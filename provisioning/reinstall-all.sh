#!/usr/bin/env bash

# 전체 재설치 자동화 스크립트
# 1. 기존 환경 정리
# 2. Vagrant VM 생성 및 Kubernetes 설치
# 3. 프로비저닝 설치
# 4. 검증

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
START_TIME=$(date +%s)

# 로그 파일 설정 (모든 출력을 파일과 콘솔에 동시 기록)
LOG_FILE="${SCRIPT_DIR}/install.log"

# 기존 로그 파일 백업 (있다면)
if [ -f "${LOG_FILE}" ]; then
  mv "${LOG_FILE}" "${LOG_FILE}.old" 2>/dev/null || true
fi

# 모든 출력을 로그 파일과 콘솔에 동시 기록
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "=========================================="
echo "전체 재설치 로그 파일: ${LOG_FILE}"
echo "시작 시간: $(date)"
echo "=========================================="
echo ""

# 비대화형 모드 확인 (--auto 옵션)
AUTO_MODE=false
if [ "$1" == "--auto" ] || [ "$1" == "-y" ]; then
  AUTO_MODE=true
  echo "자동 모드로 실행합니다 (모든 확인을 자동으로 승인)"
fi

# 사용자 확인
echo "=========================================="
echo -e "${BLUE}전체 재설치 자동화 스크립트${NC}"
echo "=========================================="
echo ""
echo "이 스크립트는 다음 작업을 수행합니다:"
echo "  1. 기존 환경 완전 정리 (Kubernetes 리소스, SSH 터널, Vagrant VM)"
echo "  2. Vagrant VM 생성 및 Kubernetes 클러스터 설치"
echo "  3. 모든 프로비저닝 컴포넌트 설치"
echo "  4. 설치 검증"
echo ""
echo -e "${YELLOW}⚠️  주의: 기존 환경이 모두 삭제됩니다!${NC}"
echo ""

if [ "$AUTO_MODE" = false ]; then
  read -p "계속하시겠습니까? (yes/no): " confirm
  if [ "$confirm" != "yes" ]; then
    echo "작업이 취소되었습니다."
    exit 0
  fi
else
  echo "자동 모드: 계속 진행합니다..."
  sleep 2
fi

echo ""
echo "=========================================="
echo "[1/4] 기존 환경 완전 정리"
echo "=========================================="
echo ""

# cleanup.sh 실행 (exec로 이미 모든 출력이 로그에 기록됨)
if [ -f "${SCRIPT_DIR}/cleanup.sh" ]; then
  echo ">>> cleanup.sh 실행 시작 <<<"
  bash "${SCRIPT_DIR}/cleanup.sh"
  echo ">>> cleanup.sh 실행 완료 <<<"
else
  echo -e "${RED}Error: cleanup.sh를 찾을 수 없습니다.${NC}"
  exit 1
fi

echo ""
if [ "$AUTO_MODE" = false ]; then
  read -p "Vagrant VM 생성 및 Kubernetes 설치를 시작하시겠습니까? (yes/no): " confirm2
  if [ "$confirm2" != "yes" ]; then
    echo "작업이 중단되었습니다."
    exit 0
  fi
else
  echo "자동 모드: Vagrant VM 생성 및 Kubernetes 설치를 시작합니다..."
  sleep 2
fi

echo ""
echo "=========================================="
echo "[2/4] Vagrant VM 생성 및 Kubernetes 설치"
echo "=========================================="
echo ""

# Vagrant 디렉토리 찾기
VAGRANT_DIRS=(
  "${HOME}/workspaces/tz-k8s-vagrant"
  "${SCRIPT_DIR}/../tz-k8s-vagrant"
)

VAGRANT_DIR=""
for vagrant_dir in "${VAGRANT_DIRS[@]}"; do
  if [ -d "$vagrant_dir" ] && [ -f "$vagrant_dir/bootstrap.sh" ]; then
    VAGRANT_DIR="$vagrant_dir"
    break
  fi
done

if [ -z "$VAGRANT_DIR" ]; then
  echo -e "${RED}Error: tz-k8s-vagrant 디렉토리를 찾을 수 없습니다.${NC}"
  echo "다음 위치 중 하나에 있어야 합니다:"
  for dir in "${VAGRANT_DIRS[@]}"; do
    echo "  - $dir"
  done
  exit 1
fi

echo "Vagrant 디렉토리: $VAGRANT_DIR"
cd "$VAGRANT_DIR"

echo ""
echo "Vagrant VM 생성 및 Kubernetes 설치 중..."
echo "  (이 작업은 10-20분 정도 소요됩니다)"
echo ""

# A_ENV=M으로 설정 (Master 모드)
export A_ENV=M

# bootstrap.sh 실행 (exec로 이미 모든 출력이 로그에 기록됨)
echo ">>> bootstrap.sh 실행 시작 <<<"
bash bootstrap.sh

if [ $? -ne 0 ]; then
  echo -e "${RED}Error: Vagrant VM 생성 또는 Kubernetes 설치 실패${NC}"
  exit 1
fi
echo ">>> bootstrap.sh 실행 완료 <<<"

echo ""
echo -e "${GREEN}✓ Vagrant VM 생성 및 Kubernetes 설치 완료${NC}"

# Kubernetes 클러스터 상태 확인
echo ""
echo "Kubernetes 클러스터 상태 확인 중..."
sleep 10

if [ -f ~/.kube/config ]; then
  export KUBECONFIG=~/.kube/config
  
  # SSH 터널 시작 (필요한 경우)
  # 주의: > /dev/null 2>&1로 리다이렉션하면 로그에 기록되지 않음
  # exec가 이미 모든 출력을 캡처하므로 그냥 실행
  if [ -f "${SCRIPT_DIR}/access-k8s-from-host.sh" ]; then
    echo "SSH 터널 시작 중..."
    bash "${SCRIPT_DIR}/access-k8s-from-host.sh" start || true
    sleep 3
  fi
  
  # 노드 상태 확인
  if kubectl get nodes > /dev/null 2>&1; then
    echo "노드 상태:"
    kubectl get nodes
    echo ""
    
    # 모든 노드가 Ready인지 확인
    NOT_READY=$(kubectl get nodes --no-headers | grep -v " Ready " | wc -l)
    if [ "$NOT_READY" -gt 0 ]; then
      echo -e "${YELLOW}Warning: 일부 노드가 Ready 상태가 아닙니다.${NC}"
      kubectl get nodes
    fi
  else
    echo -e "${YELLOW}Warning: Kubernetes 클러스터에 연결할 수 없습니다.${NC}"
  fi
else
  echo -e "${YELLOW}Warning: ~/.kube/config 파일을 찾을 수 없습니다.${NC}"
fi

echo ""
if [ "$AUTO_MODE" = false ]; then
  read -p "프로비저닝 설치를 시작하시겠습니까? (yes/no): " confirm3
  if [ "$confirm3" != "yes" ]; then
    echo "작업이 중단되었습니다."
    exit 0
  fi
else
  echo "자동 모드: 프로비저닝 설치를 시작합니다..."
  sleep 2
fi

echo ""
echo "=========================================="
echo "기존 Helm 릴리스 정리 (vault, consul, harbor)"
echo "=========================================="
echo ""

# SSH 터널이 필요할 수 있으므로 확인 및 시작
if [ -f ~/.kube/config ]; then
  export KUBECONFIG=~/.kube/config
  
  # SSH 터널 시작 (필요한 경우)
  if [ -f "${SCRIPT_DIR}/access-k8s-from-host.sh" ]; then
    echo "SSH 터널 확인 중..."
    bash "${SCRIPT_DIR}/access-k8s-from-host.sh" start || true
    sleep 2
  fi
  
  # kubectl 연결 확인
  if kubectl get nodes > /dev/null 2>&1; then
    echo "Kubernetes 클러스터에 연결되었습니다."
    echo ""
    
    # Helm이 설치되어 있는지 확인
    if command -v helm > /dev/null 2>&1; then
      echo "기존 Helm 릴리스 확인 중..."
      
      # vault uninstall
      if helm list --all-namespaces 2>/dev/null | grep -q "vault"; then
        echo "vault Helm 릴리스 제거 중..."
        VAULT_NS=$(helm list --all-namespaces 2>/dev/null | grep vault | awk '{print $2}')
        if [ -n "$VAULT_NS" ]; then
          helm uninstall vault -n "$VAULT_NS" 2>/dev/null || true
          echo "vault namespace 삭제 중..."
          kubectl delete namespace "$VAULT_NS" 2>/dev/null || true
          echo -e "${GREEN}✓ vault 제거 완료${NC}"
        fi
      else
        echo "vault Helm 릴리스가 없습니다."
      fi
      
      # consul uninstall
      if helm list --all-namespaces 2>/dev/null | grep -q "consul"; then
        echo "consul Helm 릴리스 제거 중..."
        CONSUL_NS=$(helm list --all-namespaces 2>/dev/null | grep consul | awk '{print $2}')
        if [ -n "$CONSUL_NS" ]; then
          helm uninstall consul -n "$CONSUL_NS" 2>/dev/null || true
          echo "consul namespace 삭제 중..."
          kubectl delete namespace "$CONSUL_NS" 2>/dev/null || true
          echo -e "${GREEN}✓ consul 제거 완료${NC}"
        fi
      else
        echo "consul Helm 릴리스가 없습니다."
      fi
      
      # harbor uninstall
      # harbor는 여러 릴리스 이름을 가질 수 있으므로 모두 찾아서 제거
      if helm list --all-namespaces 2>/dev/null | grep -qi harbor; then
        echo "harbor Helm 릴리스 제거 중..."
        # harbor 관련 모든 릴리스 찾아서 제거
        helm list --all-namespaces 2>/dev/null | grep -i harbor | while read -r line; do
          RELEASE_NAME=$(echo "$line" | awk '{print $1}')
          NAMESPACE=$(echo "$line" | awk '{print $2}')
          if [ -n "$RELEASE_NAME" ] && [ -n "$NAMESPACE" ]; then
            echo "  - 릴리스: $RELEASE_NAME (namespace: $NAMESPACE)"
            helm uninstall "$RELEASE_NAME" -n "$NAMESPACE" 2>/dev/null || true
          fi
        done
        # harbor namespace 삭제 (일반적으로 harbor 또는 harbor-system)
        for HARBOR_NS in harbor harbor-system; do
          if kubectl get namespace "$HARBOR_NS" > /dev/null 2>&1; then
            echo "harbor namespace ($HARBOR_NS) 삭제 중..."
            kubectl delete namespace "$HARBOR_NS" 2>/dev/null || true
          fi
        done
        echo -e "${GREEN}✓ harbor 제거 완료${NC}"
      else
        echo "harbor Helm 릴리스가 없습니다."
      fi
      
      echo ""
      echo -e "${GREEN}✓ Helm 릴리스 정리 완료${NC}"
    else
      echo -e "${YELLOW}Warning: helm 명령을 찾을 수 없습니다.${NC}"
    fi
  else
    echo -e "${YELLOW}Warning: Kubernetes 클러스터에 연결할 수 없습니다.${NC}"
  fi
else
  echo -e "${YELLOW}Warning: ~/.kube/config 파일을 찾을 수 없습니다.${NC}"
fi

echo ""
echo "=========================================="
echo "[3/4] 프로비저닝 설치"
echo "=========================================="
echo ""

cd "${SCRIPT_DIR}"

echo "프로비저닝 설치 중..."
echo "  (이 작업은 20-40분 정도 소요됩니다)"
  echo "  모든 로그는 install.log 파일에 기록됩니다."
echo ""

# install.sh 실행 (exec로 이미 모든 출력이 로그에 기록됨)
# install.sh 내부에서도 exec를 하지만 같은 파일에 append하므로 문제없음
echo ">>> install.sh 실행 시작 <<<"
bash install.sh

if [ $? -ne 0 ]; then
  echo -e "${RED}Error: 프로비저닝 설치 실패${NC}"
  echo "로그를 확인하세요: install.log"
  exit 1
fi
echo ">>> install.sh 실행 완료 <<<"

echo ""
echo -e "${GREEN}✓ 프로비저닝 설치 완료${NC}"

echo ""
if [ "$AUTO_MODE" = false ]; then
  read -p "설치 검증을 시작하시겠습니까? (yes/no): " confirm4
  if [ "$confirm4" != "yes" ]; then
    echo "검증을 건너뜁니다."
    exit 0
  fi
else
  echo "자동 모드: 설치 검증을 시작합니다..."
  sleep 2
fi

echo ""
echo "=========================================="
echo "[4/4] 설치 검증"
echo "=========================================="
echo ""

cd "${SCRIPT_DIR}"

# verify_installation.sh 실행 (exec로 이미 모든 출력이 로그에 기록됨)
if [ -f "${SCRIPT_DIR}/verify_installation.sh" ]; then
  echo ">>> verify_installation.sh 실행 시작 <<<"
  bash "${SCRIPT_DIR}/verify_installation.sh"
  echo ">>> verify_installation.sh 실행 완료 <<<"
else
  echo -e "${YELLOW}Warning: verify_installation.sh를 찾을 수 없습니다.${NC}"
  echo "수동으로 검증하세요."
fi

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
MINUTES=$((ELAPSED / 60))
SECONDS=$((ELAPSED % 60))

echo ""
echo "=========================================="
echo -e "${GREEN}전체 재설치 완료!${NC}"
echo "=========================================="
echo ""
echo "종료 시간: $(date)"
echo "소요 시간: ${MINUTES}분 ${SECONDS}초"
echo ""
echo "모든 로그는 다음 파일에 기록되었습니다:"
echo "  ${LOG_FILE}"
echo ""
echo "다음 단계:"
echo "  - 웹 브라우저에서 접근:"
echo "    - Jenkins: http://jenkins.default.topzone-k8s.drillquiz.com:8080/manage/"
echo "    - MinIO: http://minio.default.topzone-k8s.drillquiz.com:8080/"
echo ""
echo "  - 로컬 PC에서 접근하려면:"
echo "    cd ${SCRIPT_DIR}"
echo "    bash access-k8s-from-mypc.sh start"
echo "    bash access-k8s-from-mypc.sh ingress start"
echo ""

