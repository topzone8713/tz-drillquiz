#!/usr/bin/env bash

# 공통 SSH 터널 확인 및 자동 시작 함수
# 모든 서브 컴포넌트 install.sh에서 사용

check_and_start_ssh_tunnel() {
  local kubeconfig_file="${1:-${KUBECONFIG_FILE:-~/.kube/config}}"
  local local_port="6443"
  
  if [ ! -f "$kubeconfig_file" ]; then
    return 1
  fi
  
  # server 주소 확인
  local server_addr=$(grep -E "^[[:space:]]*server:[[:space:]]*https://" "$kubeconfig_file" | head -1 | sed 's/.*server:[[:space:]]*https:\/\///' | sed 's/:.*//')
  
  # 127.0.0.1로 설정되어 있지 않으면 터널 불필요
  if [ "$server_addr" != "127.0.0.1" ] && [ "$server_addr" != "localhost" ]; then
    return 0
  fi
  
  # 포트 사용 확인 (터널이 실행 중인지 확인)
  if command -v lsof > /dev/null 2>&1; then
    if lsof -i :$local_port > /dev/null 2>&1; then
      return 0
    fi
  fi
  
  # SSH 터널이 없으면 자동 시작 시도
  echo "SSH tunnel is not active. Attempting to start it automatically..."
  
  # access-k8s-from-host.sh: provisioning 디렉터리에 있음
  local access_script=""
  local script_dir="${SCRIPT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
  local home_dir="${HOME:-~}"
  
  local possible_paths=(
    "${script_dir}/access-k8s-from-host.sh"
    "${home_dir}/workspaces/tz-drillquiz/provisioning/access-k8s-from-host.sh"
  )
  
  for path in "${possible_paths[@]}"; do
    if [ -f "$path" ]; then
      access_script="$path"
      break
    fi
  done
  
  if [ -n "$access_script" ] && [ -f "$access_script" ]; then
    echo "Found access-k8s-from-host.sh at: $access_script"
    echo "Starting SSH tunnel..."
    bash "$access_script" start > /dev/null 2>&1
    sleep 3
    
    # 다시 확인
    if command -v lsof > /dev/null 2>&1; then
      if lsof -i :$local_port > /dev/null 2>&1; then
        echo "SSH tunnel started successfully."
        return 0
      fi
    fi
    
    echo "Warning: Failed to start SSH tunnel automatically."
    echo "Please run manually: bash $access_script start"
    return 1
  else
    echo "Warning: access-k8s-from-host.sh not found."
    echo "Please start SSH tunnel manually before running this script."
    return 1
  fi
}




