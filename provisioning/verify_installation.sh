#!/usr/bin/env bash

# Kubernetes 인프라 설치 검증 스크립트
# 모든 컴포넌트가 정상 동작하는지 확인

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# kubeconfig 파일 자동 감지
if [ -f ~/.kube/my-ubuntu.config ]; then
  KUBECONFIG_FILE=~/.kube/my-ubuntu.config
elif [ -f ~/.kube/config ]; then
  KUBECONFIG_FILE=~/.kube/config
else
  echo -e "${RED}Error: No kubeconfig file found${NC}"
  exit 1
fi

export KUBECONFIG="${KUBECONFIG_FILE}"

echo "=========================================="
echo "Kubernetes 인프라 설치 검증 시작"
echo "Using kubeconfig: ${KUBECONFIG_FILE}"
echo "=========================================="
echo ""

ERROR_COUNT=0
WARNING_COUNT=0

# 함수: Pod 상태 확인
check_pods() {
  local namespace=$1
  local label_selector=$2
  local component=$3
  
  echo -n "[검증] ${component} Pod 상태 확인... "
  
  if [ -n "${label_selector}" ]; then
    pods=$(kubectl get pods -n ${namespace} -l ${label_selector} --no-headers 2>/dev/null || echo "")
  else
    pods=$(kubectl get pods -n ${namespace} --no-headers 2>/dev/null || echo "")
  fi
  
  if [ -z "${pods}" ]; then
    echo -e "${RED}FAIL${NC} - Pod를 찾을 수 없음"
    ((ERROR_COUNT++))
    return 1
  fi
  
  not_running=$(echo "${pods}" | grep -v "Running" | grep -v "Completed" || true)
  
  if [ -n "${not_running}" ]; then
    echo -e "${YELLOW}WARNING${NC}"
    echo "${not_running}" | while read line; do
      echo "  - ${line}"
    done
    ((WARNING_COUNT++))
  else
    echo -e "${GREEN}OK${NC}"
  fi
}

# 함수: Service 확인
check_service() {
  local namespace=$1
  local service_name=$2
  local component=$3
  
  echo -n "[검증] ${component} Service 확인... "
  
  service=$(kubectl get svc ${service_name} -n ${namespace} --no-headers 2>/dev/null || echo "")
  
  if [ -z "${service}" ]; then
    echo -e "${RED}FAIL${NC} - Service를 찾을 수 없음"
    ((ERROR_COUNT++))
    return 1
  fi
  
  echo -e "${GREEN}OK${NC}"
  echo "  ${service}"
}

# 함수: StorageClass 확인
check_storageclass() {
  local storageclass_name=$1
  local component=$2
  
  echo -n "[검증] ${component} StorageClass 확인... "
  
  sc=$(kubectl get storageclass ${storageclass_name} --no-headers 2>/dev/null || echo "")
  
  if [ -z "${sc}" ]; then
    echo -e "${RED}FAIL${NC} - StorageClass를 찾을 수 없음"
    ((ERROR_COUNT++))
    return 1
  fi
  
  echo -e "${GREEN}OK${NC}"
}

# 1. 노드 상태 확인
echo "=== 노드 상태 ==="
nodes=$(kubectl get nodes --no-headers 2>/dev/null)
if [ -z "${nodes}" ]; then
  echo -e "${RED}ERROR: 노드를 찾을 수 없습니다${NC}"
  exit 1
fi

echo "${nodes}" | while read line; do
  status=$(echo "${line}" | awk '{print $2}')
  if [ "${status}" == "Ready" ]; then
    echo -e "${GREEN}✓${NC} ${line}"
  else
    echo -e "${RED}✗${NC} ${line}"
    ((ERROR_COUNT++))
  fi
done
echo ""

# 2. MetalLB
echo "=== MetalLB ==="
check_pods "metallb-system" "" "MetalLB"
echo ""

# 3. Ingress NGINX
echo "=== Ingress NGINX ==="
check_pods "default" "app.kubernetes.io/component=controller" "Ingress NGINX Controller"
check_service "default" "ingress-nginx-controller" "Ingress NGINX"
echo ""

# 4. Cert-Manager
echo "=== Cert-Manager ==="
check_pods "cert-manager" "app.kubernetes.io/instance=cert-manager" "Cert-Manager"
echo ""

# 5. NFS StorageClass
echo "=== NFS StorageClass ==="
check_storageclass "nfs-client" "NFS"
check_pods "nfs-provisioner" "app=nfs-subdir-external-provisioner" "NFS Provisioner"
echo ""

# 6. MinIO
echo "=== MinIO ==="
check_pods "devops" "app=minio" "MinIO"
check_service "devops" "minio-svc" "MinIO"
echo ""

# 7. PostgreSQL
echo "=== PostgreSQL ==="
check_pods "devops-dev" "app.kubernetes.io/name=postgresql" "PostgreSQL"
echo ""

# 8. Redis
echo "=== Redis ==="
check_pods "devops" "app.kubernetes.io/name=redis" "Redis"
echo ""

# 9. Velero
echo "=== Velero ==="
check_pods "velero" "app.kubernetes.io/name=velero" "Velero"
bsl=$(kubectl get backupstoragelocation -n velero --no-headers 2>/dev/null || echo "")
if [ -n "${bsl}" ]; then
  echo -e "${GREEN}[검증] Velero BackupStorageLocation${NC}"
else
  echo -e "${YELLOW}[검증] Velero BackupStorageLocation - 없음${NC}"
  ((WARNING_COUNT++))
fi
echo ""

# 10. Jenkins
echo "=== Jenkins ==="
check_pods "jenkins" "app.kubernetes.io/component=jenkins-controller" "Jenkins"
jenkins_status=$(kubectl get pod jenkins-0 -n jenkins -o jsonpath='{.status.phase}' 2>/dev/null || echo "")
if [ "${jenkins_status}" == "Running" ]; then
  echo -n "[검증] Jenkins 로그 확인... "
  if kubectl logs jenkins-0 -n jenkins --tail=10 2>/dev/null | grep -q "fully up and running"; then
    echo -e "${GREEN}OK${NC}"
  else
    echo -e "${YELLOW}WARNING${NC} - 'fully up and running' 메시지 없음"
    ((WARNING_COUNT++))
  fi
fi
echo ""

# 11. 전체 Pod 상태 요약
echo "=== 전체 Pod 상태 요약 ==="
echo -n "[검증] Pending/Error/CrashLoopBackOff Pod 확인... "
problematic_pods=$(kubectl get pods --all-namespaces --no-headers 2>/dev/null | grep -E "Pending|Error|CrashLoopBackOff" || true)
if [ -z "${problematic_pods}" ]; then
  echo -e "${GREEN}OK${NC}"
else
  echo -e "${RED}FAIL${NC}"
  echo "${problematic_pods}"
  ((ERROR_COUNT++))
fi
echo ""

# 12. PVC 상태
echo "=== PVC 상태 ==="
pending_pvcs=$(kubectl get pvc --all-namespaces --no-headers 2>/dev/null | grep -v "Bound" || true)
if [ -z "${pending_pvcs}" ]; then
  echo -e "${GREEN}[검증] 모든 PVC가 Bound 상태${NC}"
else
  echo -e "${YELLOW}[검증] Bound가 아닌 PVC:${NC}"
  echo "${pending_pvcs}"
  ((WARNING_COUNT++))
fi
echo ""

# 최종 결과
echo "=========================================="
echo "검증 완료"
echo "=========================================="
if [ ${ERROR_COUNT} -eq 0 ] && [ ${WARNING_COUNT} -eq 0 ]; then
  echo -e "${GREEN}✓ 모든 검증 통과${NC}"
  exit 0
elif [ ${ERROR_COUNT} -eq 0 ]; then
  echo -e "${YELLOW}⚠ 경고 ${WARNING_COUNT}개 (정상 동작 가능)${NC}"
  exit 0
else
  echo -e "${RED}✗ 오류 ${ERROR_COUNT}개 발견${NC}"
  if [ ${WARNING_COUNT} -gt 0 ]; then
    echo -e "${YELLOW}⚠ 경고 ${WARNING_COUNT}개${NC}"
  fi
  exit 1
fi

