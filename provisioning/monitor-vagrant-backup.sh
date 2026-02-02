#!/bin/bash

# Vagrant 및 백업 모니터링 스크립트
# my-mac2에서 실행

echo "=========================================="
echo "Vagrant & Backup Monitoring on my-mac2"
echo "=========================================="
echo ""

# 1. LaunchAgent 서비스 상태
echo "1. LaunchAgent Service Status:"
echo "----------------------------------------"
launchctl list | grep com.vagrant.autostart || echo "Service not found"
echo ""

# 2. Vagrant VM 상태
echo "2. Vagrant VM Status:"
echo "----------------------------------------"
cd ~/workspaces/tz-k8s-vagrant 2>/dev/null && vagrant status 2>&1 || echo "Cannot access vagrant or directory"
echo ""

# 3. VirtualBox 실행 중인 VM
echo "3. VirtualBox Running VMs:"
echo "----------------------------------------"
VBoxManage list runningvms 2>/dev/null || echo "VBoxManage not found or no VMs running"
echo ""

# 4. 백업 프로세스 확인
echo "4. Backup Process Status:"
echo "----------------------------------------"
ps aux | grep -E "[b]ackup-vms.sh|[v]agrant.*backup" | head -5 || echo "No backup process running"
echo ""

# 5. 최근 LaunchAgent 로그
echo "5. Recent LaunchAgent Log (last 30 lines):"
echo "----------------------------------------"
tail -n 30 ~/workspaces/tz-drillquiz/provisioning/logs/vagrant-autostart.log 2>/dev/null || echo "Log file not found"
echo ""

# 6. LaunchAgent 에러 로그
echo "6. LaunchAgent Error Log (last 20 lines):"
echo "----------------------------------------"
tail -n 20 ~/workspaces/tz-drillquiz/provisioning/logs/vagrant-autostart.error.log 2>/dev/null || echo "Error log not found or empty"
echo ""

# 7. 백업 로그
echo "7. Backup Log (last 30 lines):"
echo "----------------------------------------"
tail -n 30 /tmp/vagrant-auto-backup.log 2>/dev/null || echo "Backup log not found or empty"
echo ""

# 8. 최근 백업 디렉토리
echo "8. Recent Backup Directories:"
echo "----------------------------------------"
ls -lht ~/vagrant-backups/ 2>/dev/null | head -10 || echo "Backup directory not found"
echo ""

# 9. 디스크 사용량 (백업 디렉토리)
echo "9. Backup Directory Disk Usage:"
echo "----------------------------------------"
du -sh ~/vagrant-backups/ 2>/dev/null || echo "Backup directory not found"
echo ""

echo "=========================================="
echo "Monitoring Complete"
echo "=========================================="
