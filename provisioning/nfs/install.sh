#!/usr/bin/env bash

## NFS Subdir External Provisioner 설치 스크립트
##
## 사전 요구사항:
##   - 호스트 장비에 NFS 서버가 설치되어 있어야 합니다.
##   - values.yaml에 설정된 NFS 서버(10.0.0.217)가 접근 가능해야 합니다.
##   - NFS 서버 설치 가이드는 README.md를 참조하세요.

source ~/.bashrc
function prop { key="${2}=" file="${HOME}/.k8s/${1}" rslt=$(grep "${3:-}" "$file" -A 10 | grep "$key" | head -n 1 | cut -d '=' -f2 | sed 's/ //g'); [[ -z "$rslt" ]] && key="${2} = " && rslt=$(grep "${3:-}" "$file" -A 10 | grep "$key" | head -n 1 | cut -d '=' -f2 | sed 's/ //g'); rslt=$(echo "$rslt" | tr -d '\n' | tr -d '\r'); echo "$rslt"; }

# 스크립트가 있는 디렉토리로 이동 (어디서 실행하든 동작하도록)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

#set -x
shopt -s expand_aliases
# 부모 스크립트에서 KUBECONFIG_FILE이 설정되어 있으면 사용, 없으면 기본값 사용
if [ -z "$KUBECONFIG_FILE" ]; then
  if [ -f ~/.kube/my-ubuntu.config ]; then
    KUBECONFIG_FILE=~/.kube/my-ubuntu.config
  elif [ -f ~/.kube/config ]; then
    KUBECONFIG_FILE=~/.kube/config
  else
    echo "Error: No kubeconfig file found (~/.kube/my-ubuntu.config or ~/.kube/config)"
    exit 1
  fi
fi
alias k="kubectl --kubeconfig ${KUBECONFIG_FILE}"
export KUBECONFIG="${KUBECONFIG_FILE}"

NS=nfs-provisioner

# NFS Server IP 결정
# 1. 환경 변수 NFS_SERVER_IP 우선 사용
# 2. 없으면 현재 호스트 PC(스크립트를 실행하는 PC)의 IP 주소 자동 감지
# 3. 없으면 기본값 192.168.0.139 사용
if [ -z "$NFS_SERVER_IP" ]; then
  echo "NFS_SERVER_IP 환경 변수가 설정되지 않았습니다. 현재 호스트 PC의 IP 주소를 자동 감지합니다..."
  
  # 현재 호스트 PC의 IP 주소
  # 방법: hostname -I (Linux, 가장 간단)
  if command -v hostname > /dev/null 2>&1; then
    NFS_SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}' | grep -v '^$')
  fi
  
  # 모든 방법이 실패하면 기본값 사용
  if [ -z "$NFS_SERVER_IP" ]; then
    NFS_SERVER_IP="192.168.0.139"
    echo "⚠ WARNING: 현재 호스트 PC의 IP 주소를 자동 감지하지 못했습니다. 기본값 $NFS_SERVER_IP를 사용합니다."
    echo "   환경 변수로 지정하세요: export NFS_SERVER_IP=<your-ip>"
  else
    echo "✓ 현재 호스트 PC의 IP 주소 자동 감지: $NFS_SERVER_IP"
  fi
else
  echo "✓ NFS_SERVER_IP 환경 변수 사용: $NFS_SERVER_IP"
fi

echo ""
echo "=========================================="
echo "NFS Server Configuration"
echo "=========================================="
echo "NFS Server IP: $NFS_SERVER_IP"
echo "NFS Server Path: /srv/nfs"
echo ""

# values.yaml의 __NFS_SERVER_IP__ 플레이스홀더를 실제 IP로 치환
VALUES_TEMP="${SCRIPT_DIR}/values.yaml.tmp"
if [ -f "${SCRIPT_DIR}/values.yaml" ]; then
  sed "s|__NFS_SERVER_IP__|${NFS_SERVER_IP}|g" "${SCRIPT_DIR}/values.yaml" > "${VALUES_TEMP}"
  echo "✓ values.yaml에서 NFS 서버 IP 치환 완료: $NFS_SERVER_IP"
else
  echo "ERROR: values.yaml 파일을 찾을 수 없습니다: ${SCRIPT_DIR}/values.yaml"
  exit 1
fi

# NFS Subdir External Provisioner 설치
helm repo add nfs-subdir-external-provisioner https://kubernetes-sigs.github.io/nfs-subdir-external-provisioner
helm repo update
helm uninstall nfs-subdir-external-provisioner -n ${NS} 2>/dev/null || true

helm upgrade --install nfs-subdir-external-provisioner nfs-subdir-external-provisioner/nfs-subdir-external-provisioner \
  --create-namespace \
  --namespace ${NS} \
  -f "${VALUES_TEMP}"

# 임시 파일 정리
rm -f "${VALUES_TEMP}"

sleep 60

# NFS Subdir External Provisioner 상태 확인
kubectl get pods -n ${NS}
kubectl get storageclass nfs-client

## CSI NFS Driver 설치 (선택사항)
## Kubernetes CSI NFS Driver master 버전 설치
#curl -skSL https://raw.githubusercontent.com/kubernetes-csi/csi-driver-nfs/v4.9.0/deploy/install-driver.sh | bash -s v4.9.0 --
#sleep 60
#kubectl -n kube-system get pod -o wide -l app=csi-nfs-controller
#kubectl -n kube-system get pod -o wide -l app=csi-nfs-node

## CSI Driver 설치 확인
#kubectl get csinodes \
#  -o jsonpath='{range .items[*]} {.metadata.name}{": "} {range .spec.drivers[*]} {.name}{"\n"} {end}{end}'

exit 0
