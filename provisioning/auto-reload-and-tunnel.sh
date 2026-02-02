#!/bin/bash

# Workspace base directory
WORKSPACE_BASE="${WORKSPACE_BASE:-$HOME/workspaces}"

VAGRANT_DIR="${WORKSPACE_BASE}/tz-k8s-vagrant"
TUNNEL_SCRIPT="${WORKSPACE_BASE}/tz-drillquiz/provisioning/access-k8s-from-host.sh"

cd "$VAGRANT_DIR" || exit 1

echo "=========================================="
echo "Checking Vagrant VM status..."
echo "=========================================="

# VM 상태 확인 (출력 파싱 개선)
VAGRANT_STATUS=$(vagrant status 2>/dev/null)
POWEROFF_COUNT=$(echo "$VAGRANT_STATUS" | grep -c "poweroff (virtualbox)" || echo "0")
RUNNING_COUNT=$(echo "$VAGRANT_STATUS" | grep -c "running (virtualbox)" || echo "0")
ABORTED_COUNT=$(echo "$VAGRANT_STATUS" | grep -c "aborted (virtualbox)" || echo "0")
# TOTAL_COUNT는 kube-master 또는 kube-node로 시작하는 모든 VM 개수
TOTAL_COUNT=$(echo "$VAGRANT_STATUS" | grep -E "^[[:space:]]*kube-(master|node)" | wc -l | tr -d ' \n\r')

echo "VM Status: $RUNNING_COUNT running, $POWEROFF_COUNT poweroff, $ABORTED_COUNT aborted, $TOTAL_COUNT total"

# 숫자 변수 검증 (줄바꿈 제거)
POWEROFF_COUNT=$(echo "${POWEROFF_COUNT:-0}" | tr -d ' \n\r')
RUNNING_COUNT=$(echo "${RUNNING_COUNT:-0}" | tr -d ' \n\r')
ABORTED_COUNT=$(echo "${ABORTED_COUNT:-0}" | tr -d ' \n\r')
TOTAL_COUNT=$(echo "${TOTAL_COUNT:-0}" | tr -d ' \n\r')

# VM이 실행 중이 아니면 시작 (aborted 상태도 vagrant up으로 복구 가능)
if [ "$POWEROFF_COUNT" -gt 0 ] || [ "$RUNNING_COUNT" -eq 0 ] || [ "$ABORTED_COUNT" -gt 0 ]; then
    echo ""
    echo "=========================================="
    echo "Starting Vagrant VMs (vagrant up)..."
    echo "=========================================="
    
    # VM 시작 (aborted 상태도 vagrant up으로 복구됨)
    vagrant up || echo "Warning: vagrant up had some issues, but continuing..."
else
    echo ""
    echo "=========================================="
    echo "All VMs are already running. Skipping vagrant up/reload."
    echo "=========================================="
fi

echo ""
echo "=========================================="
echo "Waiting for VMs to be ready..."
echo "=========================================="

# VM이 모두 running 상태가 될 때까지 대기 (최대 5분)
MAX_WAIT=300
WAIT_INTERVAL=10
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
    # 모든 VM이 running 상태인지 확인
    VAGRANT_STATUS=$(vagrant status 2>/dev/null)
    RUNNING_COUNT=$(echo "$VAGRANT_STATUS" | grep -c "running (virtualbox)" || echo "0")
    # TOTAL_COUNT는 kube-master 또는 kube-node로 시작하는 모든 VM 개수
    TOTAL_COUNT=$(echo "$VAGRANT_STATUS" | grep -E "^[[:space:]]*kube-(master|node)" | wc -l | tr -d ' \n\r')
    
    # 숫자 변수 검증 (줄바꿈 제거)
    RUNNING_COUNT=$(echo "${RUNNING_COUNT:-0}" | tr -d ' \n\r')
    TOTAL_COUNT=$(echo "${TOTAL_COUNT:-0}" | tr -d ' \n\r')
    
    if [ "$RUNNING_COUNT" -eq "$TOTAL_COUNT" ] && [ "$TOTAL_COUNT" -gt 0 ]; then
        echo "All VMs are running! ($RUNNING_COUNT/$TOTAL_COUNT)"
        break
    fi
    
    echo "Waiting for VMs... ($RUNNING_COUNT/$TOTAL_COUNT running, elapsed: ${ELAPSED}s)"
    sleep $WAIT_INTERVAL
    ELAPSED=$((ELAPSED + WAIT_INTERVAL))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo "Warning: Timeout waiting for all VMs to be ready"
    vagrant status
    echo "VM will remain in current state. Exiting without starting SSH tunnel."
    exit 0
fi

echo ""
echo "=========================================="
echo "Verifying VM SSH connectivity (safe method)..."
echo "=========================================="

# VM이 실제로 SSH 연결이 가능한지 확인 (최대 2분)
# vagrant ssh를 직접 사용하지 않고, VirtualBox 상태만 확인
SSH_WAIT=120
SSH_INTERVAL=5
SSH_ELAPSED=0
SSH_READY=false

# VirtualBox에서 VM이 실제로 실행 중인지 확인
while [ $SSH_ELAPSED -lt $SSH_WAIT ]; do
    # VirtualBox에서 실행 중인 VM 수 확인
    VBOX_RUNNING=$(VBoxManage list runningvms 2>/dev/null | wc -l)
    VBOX_RUNNING=${VBOX_RUNNING:-0}
    
    if [ "$VBOX_RUNNING" -ge "$TOTAL_COUNT" ] && [ "$TOTAL_COUNT" -gt 0 ]; then
        # 추가로 VM이 안정적으로 실행 중인지 확인 (최소 10초 대기)
        sleep 10
        echo "VM SSH connectivity verified via VirtualBox status!"
        SSH_READY=true
        break
    fi
    
    echo "Waiting for VM to be ready in VirtualBox... (running: $VBOX_RUNNING/$TOTAL_COUNT, elapsed: ${SSH_ELAPSED}s)"
    sleep $SSH_INTERVAL
    SSH_ELAPSED=$((SSH_ELAPSED + SSH_INTERVAL))
done

if [ "$SSH_READY" = false ]; then
    echo "Warning: VM not ready in VirtualBox. Skipping SSH tunnel setup."
    echo "VM will remain running, but SSH tunnel will not be started."
    exit 0
fi

echo ""
echo "=========================================="
echo "SSH Tunnel (skipped - not needed for local VMs)..."
echo "=========================================="

# SSH 터널은 로컬 VM에서는 불필요함
# my-mac, my-mac2는 로컬 Vagrant VM이므로 SSH 터널이 필요 없음
# my-ubuntu 등 원격 서버에서만 필요하지만, 여기서는 스킵
echo "Skipping SSH tunnel setup (not needed for local Vagrant VMs)"
echo "Note: SSH tunnel is only needed for remote server access, not for local VMs"

echo ""
echo "=========================================="
echo "Checking if backup is needed..."
echo "=========================================="

# 백업 스크립트 경로
BACKUP_SCRIPT="${VAGRANT_DIR}/scripts/backup-vms.sh"

# 백업 활성화 여부 확인 (환경 변수로 제어 가능)
AUTO_BACKUP_ENABLED="${AUTO_BACKUP_ENABLED:-true}"

if [ "$AUTO_BACKUP_ENABLED" != "true" ]; then
    echo "Auto-backup is disabled (AUTO_BACKUP_ENABLED=false)"
    echo "Skipping backup..."
else
    if [ -f "$BACKUP_SCRIPT" ]; then
        # 재부팅 후 자동 실행인 경우 무조건 백업
        # 시스템 부팅 시간 확인 (재부팅 후 1시간 이내면 재부팅으로 간주)
        CURRENT_TIME=$(date +%s)
        if [ "$(uname)" = "Darwin" ]; then
            # macOS: sysctl로 부팅 시간 확인
            BOOT_TIME=$(sysctl -n kern.boottime 2>/dev/null | awk '{print $4}' | tr -d ',' || echo "0")
            if [ "$BOOT_TIME" != "0" ]; then
                UPTIME_SECONDS=$((CURRENT_TIME - BOOT_TIME))
            else
                # 대체 방법: uptime 사용
                UPTIME_SECONDS=$(uptime | awk -F'up ' '{print $2}' | awk -F',' '{print $1}' | awk '{if ($2=="min") print $1*60; else if ($2=="sec") print $1; else print $1*3600}' || echo "0")
            fi
        else
            # Linux: /proc/uptime 사용
            UPTIME_SECONDS=$(awk '{print int($1)}' /proc/uptime 2>/dev/null || echo "0")
        fi
        
        # 재부팅 후 1시간 이내면 재부팅으로 간주하고 백업 수행
        # 재부팅 후 VM이 정상적으로 기동되면 백업하는 것이 합리적
        REBOOT_THRESHOLD=3600  # 1시간 (초)
        if [ "$UPTIME_SECONDS" -lt "$REBOOT_THRESHOLD" ] && [ "$UPTIME_SECONDS" -gt 0 ]; then
            UPTIME_MINUTES=$((UPTIME_SECONDS / 60))
            echo "System was recently rebooted (uptime: ${UPTIME_MINUTES} minutes)"
            echo "Starting automatic backup after reboot..."
            
            # 백업 실행 (백그라운드로 실행하여 VM 시작을 지연시키지 않음)
            export PATH="/usr/local/bin:/Applications/VirtualBox.app/Contents/MacOS:${PATH}"
            cd "$VAGRANT_DIR"
            bash "$BACKUP_SCRIPT" > /tmp/vagrant-auto-backup.log 2>&1 &
            BACKUP_PID=$!
            
            echo "Backup started in background (PID: $BACKUP_PID)"
            echo "Backup log: /tmp/vagrant-auto-backup.log"
            echo "Note: Backup runs in background and won't delay VM startup"
        else
            # 재부팅이 아닌 경우, 마지막 백업 시간 확인 (24시간 이내면 스킵)
            BACKUP_BASE_DIR="${HOME}/vagrant-backups"
            BACKUP_INTERVAL=86400  # 24시간 (초)
            
            if [ "$(uname)" = "Darwin" ]; then
                LAST_BACKUP_DIR=$(ls -td "${BACKUP_BASE_DIR}"/vagrant-vms-* 2>/dev/null | head -1 || echo "")
                if [ -n "$LAST_BACKUP_DIR" ] && [ -d "$LAST_BACKUP_DIR" ]; then
                    LAST_BACKUP_TIME=$(stat -f %m "$LAST_BACKUP_DIR" 2>/dev/null || echo "0")
                    TIME_DIFF=$((CURRENT_TIME - LAST_BACKUP_TIME))
                else
                    TIME_DIFF=$((BACKUP_INTERVAL + 1))  # 백업이 없으면 백업 수행
                fi
            else
                LAST_BACKUP=$(find "${BACKUP_BASE_DIR}" -maxdepth 1 -type d -name "vagrant-vms-*" -not -name "latest" -printf "%T@\n" 2>/dev/null | sort -n | tail -1 || echo "0")
                TIME_DIFF=$((CURRENT_TIME - LAST_BACKUP))
            fi
            
            if [ $TIME_DIFF -lt $BACKUP_INTERVAL ] && [ -n "$LAST_BACKUP_DIR" ]; then
                HOURS_AGO=$((TIME_DIFF / 3600))
                echo "Last backup was ${HOURS_AGO} hours ago (less than 24 hours)"
                echo "Skipping backup to save disk space..."
            else
                echo "Starting automatic backup..."
                echo "  (Last backup: ${TIME_DIFF}s ago, interval: ${BACKUP_INTERVAL}s)"
                
                # 백업 실행 (백그라운드로 실행하여 VM 시작을 지연시키지 않음)
                export PATH="/usr/local/bin:/Applications/VirtualBox.app/Contents/MacOS:${PATH}"
                cd "$VAGRANT_DIR"
                bash "$BACKUP_SCRIPT" > /tmp/vagrant-auto-backup.log 2>&1 &
                BACKUP_PID=$!
                
                echo "Backup started in background (PID: $BACKUP_PID)"
                echo "Backup log: /tmp/vagrant-auto-backup.log"
                echo "Note: Backup runs in background and won't delay VM startup"
            fi
        fi
    else
        echo "Warning: Backup script not found: $BACKUP_SCRIPT"
        echo "Skipping backup..."
    fi
fi

echo ""
echo "=========================================="
echo "Done!"
echo "=========================================="
