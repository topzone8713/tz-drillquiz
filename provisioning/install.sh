#!/usr/bin/env bash

source ~/.bashrc
function prop { key="${2}=" file="${HOME}/.k8s/${1}" rslt=$(grep "${3:-}" "$file" -A 10 | grep "$key" | head -n 1 | cut -d '=' -f2 | sed 's/ //g'); [[ -z "$rslt" ]] && key="${2} = " && rslt=$(grep "${3:-}" "$file" -A 10 | grep "$key" | head -n 1 | cut -d '=' -f2 | sed 's/ //g'); rslt=$(echo "$rslt" | tr -d '\n' | tr -d '\r'); echo "$rslt"; }

# 스크립트가 있는 디렉토리로 이동 (어디서 실행하든 동작하도록)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 로그 파일 설정 (append 모드로 기존 install.log에 추가)
LOG_FILE="${SCRIPT_DIR}/install.log"
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "=========================================="
echo "프로비저닝 설치 로그: ${LOG_FILE}"
echo "시작 시간: $(date)"
echo "=========================================="
echo ""

#set -x
shopt -s expand_aliases

# kubeconfig 파일 자동 감지
# 로컬 Mac 환경: my-ubuntu.config 우선 사용
# my-ubuntu 서버 환경: config 사용
if [ -f ~/.kube/my-ubuntu.config ]; then
  KUBECONFIG_FILE=~/.kube/my-ubuntu.config
elif [ -f ~/.kube/config ]; then
  KUBECONFIG_FILE=~/.kube/config
else
  echo "Error: No kubeconfig file found (~/.kube/my-ubuntu.config or ~/.kube/config)"
  exit 1
fi

echo "Using kubeconfig: ${KUBECONFIG_FILE}"
alias k="kubectl --kubeconfig ${KUBECONFIG_FILE}"
export KUBECONFIG="${KUBECONFIG_FILE}"

# 서브 스크립트에서 사용할 수 있도록 export
export KUBECONFIG_FILE


## SSH 터널링 확인 (Kubernetes API 서버 접근용)
# kubeconfig의 server가 127.0.0.1:6443이면 SSH 터널이 필요함
# 터널은 이미 실행 중이거나 별도로 설정되어 있어야 함
check_ssh_tunnel() {
  local kubeconfig_file="$1"
  local local_port="6443"
  
  if [ ! -f "$kubeconfig_file" ]; then
    return 1
  fi
  
  # server 주소 확인
  local server_addr=$(grep -E "^[[:space:]]*server:[[:space:]]*https://" "$kubeconfig_file" | head -1 | sed 's/.*server:[[:space:]]*https:\/\///' | sed 's/:.*//')
  
  # 127.0.0.1로 설정되어 있으면 터널 필요
  if [ "$server_addr" != "127.0.0.1" ] && [ "$server_addr" != "localhost" ]; then
    echo "Kubernetes API server is directly accessible: $server_addr"
    return 0
  fi
  
  # 포트 사용 확인 (터널이 실행 중인지 확인)
  if command -v lsof > /dev/null 2>&1; then
    if lsof -i :$local_port > /dev/null 2>&1; then
      echo "SSH tunnel is active (port $local_port is in use)"
      return 0
    else
      echo "Warning: SSH tunnel to port $local_port is not active. Make sure the tunnel is running."
      echo "You can start it manually using: vagrant ssh kube-master -- -L ${local_port}:127.0.0.1:6443 -N -f"
      return 1
    fi
  fi
  
  return 0
}

# SSH 터널 확인 및 자동 시작
check_ssh_tunnel "${KUBECONFIG_FILE}"
if [ $? -ne 0 ]; then
  echo "SSH tunnel is not active. Attempting to start it automatically..."
  
  # access-k8s-from-host.sh: provisioning 디렉터리에 있음
  ACCESS_SCRIPT=""
  POSSIBLE_PATHS=(
    "${SCRIPT_DIR}/access-k8s-from-host.sh"
    "${HOME}/workspaces/tz-drillquiz/provisioning/access-k8s-from-host.sh"
  )
  
  for path in "${POSSIBLE_PATHS[@]}"; do
    if [ -f "$path" ]; then
      ACCESS_SCRIPT="$path"
      break
    fi
  done
  
  if [ -n "$ACCESS_SCRIPT" ] && [ -f "$ACCESS_SCRIPT" ]; then
    echo "Found access-k8s-from-host.sh at: $ACCESS_SCRIPT"
    echo "Starting SSH tunnel..."
    bash "$ACCESS_SCRIPT" start > /dev/null 2>&1
    sleep 3
    
    # 다시 확인
    check_ssh_tunnel "${KUBECONFIG_FILE}"
    if [ $? -eq 0 ]; then
      echo "SSH tunnel started successfully."
    else
      echo "Warning: Failed to start SSH tunnel automatically."
      echo "Please run manually: bash $ACCESS_SCRIPT start"
      echo "Or check if the tunnel is already running: bash $ACCESS_SCRIPT status"
    fi
  else
    echo "Warning: access-k8s-from-host.sh not found."
    echo "Please start SSH tunnel manually before running this script."
    echo "Expected location: ${SCRIPT_DIR}/access-k8s-from-host.sh or ~/workspaces/tz-drillquiz/provisioning/access-k8s-from-host.sh"
  fi
fi


####

# 프로비저닝 순서대로 일괄 설치
# 순서: MetalLB -> Ingress NGINX -> NFS -> MinIO -> PostgreSQL -> Redis -> Velero -> Jenkins

set -e  # 에러 발생 시 중단

echo "=========================================="
echo "Kubernetes 인프라 프로비저닝 시작"
echo "=========================================="
echo ""

# 1. MetalLB 프로비저닝
echo "[1/8] MetalLB 프로비저닝 시작..."
ORIGINAL_DIR=$(pwd)
cd "$SCRIPT_DIR/metallb"
bash install.sh
cd "$ORIGINAL_DIR"
echo "[1/8] MetalLB 프로비저닝 완료"
echo ""

# 2. Ingress NGINX 프로비저닝
echo "[2/8] Ingress NGINX 프로비저닝 시작..."
ORIGINAL_DIR=$(pwd)
cd "$SCRIPT_DIR/ingress_nginx"
bash install.sh
cd "$ORIGINAL_DIR"
echo "[2/8] Ingress NGINX 프로비저닝 완료"
echo ""

# 3. NFS 프로비저닝
echo "[3/8] NFS 프로비저닝 시작..."
ORIGINAL_DIR=$(pwd)
cd "$SCRIPT_DIR/nfs"
bash install.sh
cd "$ORIGINAL_DIR"
echo "[3/8] NFS 프로비저닝 완료"
echo ""

# 4. MinIO 프로비저닝
echo "[4/8] MinIO 프로비저닝 시작..."
ORIGINAL_DIR=$(pwd)
cd "$SCRIPT_DIR/minio"
bash install.sh
cd "$ORIGINAL_DIR"
echo "[4/8] MinIO 프로비저닝 완료"
echo ""

# 5. PostgreSQL 프로비저닝
echo "[5/8] PostgreSQL 프로비저닝 시작..."
ORIGINAL_DIR=$(pwd)
cd "$SCRIPT_DIR/postgresql"
bash install.sh
cd "$ORIGINAL_DIR"
echo "[5/8] PostgreSQL 프로비저닝 완료"
echo ""

# 6. Redis 프로비저닝
echo "[6/8] Redis 프로비저닝 시작..."
ORIGINAL_DIR=$(pwd)
cd "$SCRIPT_DIR/redis"
bash install.sh
cd "$ORIGINAL_DIR"
echo "[6/8] Redis 프로비저닝 완료"
echo ""

# 7. Velero 프로비저닝
echo "[7/8] Velero 프로비저닝 시작..."
ORIGINAL_DIR=$(pwd)
cd "$SCRIPT_DIR/velero"
bash install.sh
cd "$ORIGINAL_DIR"
echo "[7/8] Velero 프로비저닝 완료"
echo ""

# 8. Jenkins 프로비저닝
echo "[8/8] Jenkins 프로비저닝 시작..."
ORIGINAL_DIR=$(pwd)
cd "$SCRIPT_DIR/jenkins/helm"
bash install.sh
cd "$ORIGINAL_DIR"
echo "[8/8] Jenkins 프로비저닝 완료"
echo ""

echo "=========================================="
echo "모든 프로비저닝이 완료되었습니다!"
echo "=========================================="

exit 0

