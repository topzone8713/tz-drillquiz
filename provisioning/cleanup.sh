#!/usr/bin/env bash

# 기존 환경 완전 정리 스크립트
# 재설치 전에 모든 리소스를 깨끗하게 정리

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "기존 환경 완전 정리 시작"
echo "=========================================="
echo ""
echo -e "${YELLOW}참고: Vagrant VM을 제거하면 Kubernetes 클러스터가 사라지므로${NC}"
echo -e "${YELLOW}      Kubernetes 리소스 정리는 불필요합니다.${NC}"
echo ""

echo -e "${YELLOW}[1/3] SSH 터널 정리...${NC}"

# SSH 터널 프로세스 종료
if command -v lsof > /dev/null 2>&1; then
  echo "  - 포트 6443 사용 프로세스 종료 중..."
  pids=$(lsof -ti :6443 2>/dev/null || echo "")
  if [ -n "$pids" ]; then
    echo "$pids" | while read pid; do
      [ -n "$pid" ] && kill -9 "$pid" 2>/dev/null || true
    done
    echo "    SSH 터널 프로세스 종료됨"
  else
    echo "    실행 중인 SSH 터널 없음"
  fi
else
  echo "    lsof 명령어 없음, SSH 터널 정리 건너뜀"
fi

# access-k8s-from-host.sh stop
if [ -f "${SCRIPT_DIR}/access-k8s-from-host.sh" ]; then
  echo "  - access-k8s-from-host.sh 정리 중..."
  bash "${SCRIPT_DIR}/access-k8s-from-host.sh" stop > /dev/null 2>&1 || true
fi

# access-k8s-from-mypc.sh stop (로컬에서 실행 중인 경우)
if [ -f "${SCRIPT_DIR}/access-k8s-from-mypc.sh" ]; then
  echo "  - access-k8s-from-mypc.sh 정리 중..."
  bash "${SCRIPT_DIR}/access-k8s-from-mypc.sh" stop > /dev/null 2>&1 || true
fi

# access-k8s-from-mypc.sh ingress stop (통합된 스크립트 사용)
if [ -f "${SCRIPT_DIR}/access-k8s-from-mypc.sh" ]; then
  echo "  - Ingress port-forward 정리 중..."
  bash "${SCRIPT_DIR}/access-k8s-from-mypc.sh" ingress stop > /dev/null 2>&1 || true
fi

echo -e "${GREEN}  ✓ SSH 터널 정리 완료${NC}"

echo ""
echo -e "${YELLOW}[2/3] Vagrant VM 정리...${NC}"

# Vagrant VM 상태 확인 및 제거
VAGRANT_DIRS=(
  "${HOME}/workspaces/tz-k8s-vagrant"
  "${SCRIPT_DIR}/../tz-k8s-vagrant"
)

VAGRANT_FOUND=false
for vagrant_dir in "${VAGRANT_DIRS[@]}"; do
  if [ -d "$vagrant_dir" ] && [ -f "$vagrant_dir/Vagrantfile" ]; then
    echo "  - Vagrant 디렉토리 발견: $vagrant_dir"
    cd "$vagrant_dir"
    
    if command -v vagrant > /dev/null 2>&1; then
      echo "    Vagrant VM 상태 확인 중..."
      if vagrant status 2>/dev/null | grep -q "running\|saved"; then
        echo "    Vagrant VM 제거 중..."
        if [ -f "$vagrant_dir/bootstrap.sh" ]; then
          bash "$vagrant_dir/bootstrap.sh" remove > /dev/null 2>&1 || vagrant destroy -f > /dev/null 2>&1 || true
        else
          vagrant destroy -f > /dev/null 2>&1 || true
        fi
        echo "    Vagrant VM 제거 완료"
      else
        echo "    실행 중인 Vagrant VM 없음"
      fi
      VAGRANT_FOUND=true
      break
    else
      echo "    vagrant 명령어 없음"
    fi
  fi
done

if [ "$VAGRANT_FOUND" = false ]; then
  echo -e "${YELLOW}    Vagrant 디렉토리를 찾을 수 없음 (수동으로 정리 필요)${NC}"
fi

echo -e "${GREEN}  ✓ Vagrant VM 정리 완료${NC}"

echo ""
echo -e "${YELLOW}[3/3] 임시 파일 정리...${NC}"

# install.log 파일들 정리
echo "  - install.log 파일 정리 중..."
find "${SCRIPT_DIR}" -name "install*.log" -type f -mtime +7 -delete 2>/dev/null || true

# _bak 파일들 정리
echo "  - _bak 파일 정리 중..."
find "${SCRIPT_DIR}" -name "*_bak" -type f -delete 2>/dev/null || true
find "${SCRIPT_DIR}" -name "*.bak" -type f -delete 2>/dev/null || true

echo -e "${GREEN}  ✓ 임시 파일 정리 완료${NC}"


echo ""
echo "=========================================="
echo -e "${GREEN}기존 환경 정리 완료!${NC}"
echo "=========================================="
echo ""
echo "다음 단계:"
echo "  1. Vagrant VM 생성 및 Kubernetes 설치:"
echo "     cd ~/workspaces/tz-k8s-vagrant && bash bootstrap.sh"
echo "  2. 프로비저닝 설치:"
echo "     cd ~/workspaces/tz-drillquiz/provisioning && bash install.sh"
echo "  3. 검증:"
echo "     cd ~/workspaces/tz-drillquiz/provisioning && bash verify_installation.sh"
echo ""

