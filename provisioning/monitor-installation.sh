#!/usr/bin/env bash

# 재설치 진행 상황 모니터링 스크립트
# reinstall-all.sh 실행 중인 상태를 실시간으로 모니터링

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 모니터링 함수
monitor_status() {
  while true; do
    clear
    echo "=========================================="
    echo -e "${CYAN}재설치 진행 상황 모니터링${NC}"
    echo "=========================================="
    echo "시간: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    # 1. 프로세스 확인
    echo -e "${BLUE}[1] 실행 중인 프로세스 확인${NC}"
    if pgrep -f "reinstall-all.sh" > /dev/null; then
      echo -e "${GREEN}✓ reinstall-all.sh 실행 중${NC}"
      PID=$(pgrep -f "reinstall-all.sh" | head -1)
      echo "  PID: $PID"
    else
      echo -e "${YELLOW}⚠ reinstall-all.sh 실행 중이지 않음${NC}"
    fi
    
    if pgrep -f "bootstrap.sh" > /dev/null; then
      echo -e "${GREEN}✓ bootstrap.sh 실행 중${NC}"
    fi
    
    if pgrep -f "vagrant" > /dev/null; then
      echo -e "${GREEN}✓ vagrant 프로세스 실행 중${NC}"
    fi
    
    if pgrep -f "install.sh" > /dev/null; then
      echo -e "${GREEN}✓ install.sh 실행 중${NC}"
    fi
    
    echo ""
    
    # 2. Vagrant VM 상태
    echo -e "${BLUE}[2] Vagrant VM 상태${NC}"
    VAGRANT_DIRS=(
      "${HOME}/workspaces/tz-k8s-vagrant"
      "${SCRIPT_DIR}/../tz-k8s-vagrant"
    )
    
    for vagrant_dir in "${VAGRANT_DIRS[@]}"; do
      if [ -d "$vagrant_dir" ] && [ -f "$vagrant_dir/Vagrantfile" ]; then
        cd "$vagrant_dir" 2>/dev/null
        if command -v vagrant > /dev/null 2>&1; then
          echo "디렉토리: $vagrant_dir"
          vagrant status 2>/dev/null | grep -E "kube-master|kube-node" || echo "  VM 정보 확인 불가"
          cd - > /dev/null
          break
        fi
      fi
    done
    
    echo ""
    
    # 3. Kubernetes 클러스터 상태 (가능한 경우)
    echo -e "${BLUE}[3] Kubernetes 클러스터 상태${NC}"
    if [ -f ~/.kube/config ]; then
      export KUBECONFIG=~/.kube/config
      if kubectl get nodes > /dev/null 2>&1; then
        echo "노드 상태:"
        kubectl get nodes 2>/dev/null || echo "  노드 정보 확인 불가"
        echo ""
        echo "Pod 상태 (일부):"
        kubectl get pods --all-namespaces 2>/dev/null | head -15 || echo "  Pod 정보 확인 불가"
      else
        echo "  Kubernetes 클러스터에 연결할 수 없음"
      fi
    else
      echo "  kubeconfig 파일 없음 (아직 생성되지 않음)"
    fi
    
    echo ""
    
    # 4. 최신 로그 확인
    echo -e "${BLUE}[4] 최신 로그 (마지막 10줄)${NC}"
    
    # cleanup.sh 로그
    if [ -f "${SCRIPT_DIR}/cleanup.log" ]; then
      echo "cleanup.log:"
      tail -3 "${SCRIPT_DIR}/cleanup.log" 2>/dev/null | sed 's/^/  /'
    fi
    
    # install.log
    if [ -f "${SCRIPT_DIR}/install.log" ]; then
      echo "install.log (마지막 5줄):"
      tail -5 "${SCRIPT_DIR}/install.log" 2>/dev/null | sed 's/^/  /'
    fi
    
    # bootstrap.sh 출력 (vagrant 로그)
    VAGRANT_LOG=$(ls -t ~/.vagrant.d/logs/* 2>/dev/null | head -1)
    if [ -n "$VAGRANT_LOG" ]; then
      echo "최신 Vagrant 로그:"
      tail -3 "$VAGRANT_LOG" 2>/dev/null | sed 's/^/  /' || echo "  로그 읽기 불가"
    fi
    
    echo ""
    echo "=========================================="
    echo "다음 업데이트까지 10초 대기..."
    echo "종료하려면 Ctrl+C"
    echo "=========================================="
    
    sleep 10
  done
}

# 실시간 로그 추적
follow_logs() {
  echo "=========================================="
  echo -e "${CYAN}실시간 로그 추적${NC}"
  echo "=========================================="
  echo ""
  
  # install.log 추적
  if [ -f "${SCRIPT_DIR}/install.log" ]; then
    echo "로그 파일 추적: ${SCRIPT_DIR}/install.log"
    echo "종료하려면 Ctrl+C"
    echo ""
    tail -f "${SCRIPT_DIR}/install.log"
  else
    echo "install.log 파일을 찾을 수 없습니다."
    echo "아직 설치가 시작되지 않았거나 로그 파일이 생성되지 않았습니다."
  fi
}

# 현재 단계 확인
check_current_step() {
  echo "=========================================="
  echo -e "${CYAN}현재 진행 단계 확인${NC}"
  echo "=========================================="
  echo ""
  
  # 1. cleanup.sh 완료 여부
  if pgrep -f "cleanup.sh" > /dev/null; then
    echo -e "${YELLOW}[진행 중] 기존 환경 정리${NC}"
  else
    echo -e "${GREEN}[완료] 기존 환경 정리${NC}"
  fi
  
  # 2. bootstrap.sh 실행 여부
  if pgrep -f "bootstrap.sh" > /dev/null; then
    echo -e "${YELLOW}[진행 중] Vagrant VM 생성 및 Kubernetes 설치${NC}"
    
    # Vagrant VM 상태 확인
    VAGRANT_DIRS=(
      "${HOME}/workspaces/tz-k8s-vagrant"
      "${SCRIPT_DIR}/../tz-k8s-vagrant"
    )
    for vagrant_dir in "${VAGRANT_DIRS[@]}"; do
      if [ -d "$vagrant_dir" ] && command -v vagrant > /dev/null 2>&1; then
        cd "$vagrant_dir" 2>/dev/null
        VM_STATUS=$(vagrant status 2>/dev/null | grep -E "kube-master|kube-node" | head -1)
        if [ -n "$VM_STATUS" ]; then
          echo "  $VM_STATUS"
        fi
        cd - > /dev/null
        break
      fi
    done
  elif [ -f ~/.kube/config ] && kubectl get nodes > /dev/null 2>&1 2>/dev/null; then
    echo -e "${GREEN}[완료] Vagrant VM 생성 및 Kubernetes 설치${NC}"
    echo "  노드: $(kubectl get nodes --no-headers 2>/dev/null | wc -l)개"
  else
    echo -e "${YELLOW}[대기] Vagrant VM 생성 및 Kubernetes 설치${NC}"
  fi
  
  # 3. install.sh 실행 여부
  if pgrep -f "provisioning.*install.sh" > /dev/null; then
    echo -e "${YELLOW}[진행 중] 프로비저닝 설치${NC}"
    
    # 어떤 컴포넌트가 설치 중인지 확인
    if [ -f "${SCRIPT_DIR}/install.log" ]; then
      CURRENT_COMPONENT=$(tail -20 "${SCRIPT_DIR}/install.log" 2>/dev/null | grep -E "\[[0-9]/8\]" | tail -1)
      if [ -n "$CURRENT_COMPONENT" ]; then
        echo "  $CURRENT_COMPONENT"
      fi
    fi
  elif [ -f ~/.kube/config ] && kubectl get pods -n jenkins > /dev/null 2>&1; then
    echo -e "${GREEN}[완료] 프로비저닝 설치${NC}"
  else
    echo -e "${YELLOW}[대기] 프로비저닝 설치${NC}"
  fi
  
  # 4. 검증
  if [ -f ~/.kube/config ] && kubectl get pods -n jenkins jenkins-0 > /dev/null 2>&1; then
    echo -e "${GREEN}[완료] 설치 검증${NC}"
  else
    echo -e "${YELLOW}[대기] 설치 검증${NC}"
  fi
  
  echo ""
}

# 메인 메뉴
case "$1" in
  "status"|"")
    monitor_status
    ;;
  "logs"|"follow")
    follow_logs
    ;;
  "step"|"steps")
    check_current_step
    ;;
  *)
    echo "사용법:"
    echo "  $0           # 실시간 상태 모니터링 (기본)"
    echo "  $0 status    # 실시간 상태 모니터링"
    echo "  $0 logs      # 실시간 로그 추적"
    echo "  $0 step      # 현재 진행 단계 확인"
    exit 1
    ;;
esac

