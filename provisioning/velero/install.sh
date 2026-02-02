#!/usr/bin/env bash

# https://guide.ncloud-docs.com/docs/k8s-k8suse-velero#3velero%EC%84%9C%EB%B2%84%EC%84%A4%EC%B9%98
# https://guide.ncloud-docs.com/docs/k8s-k8sexamples-velero

source ~/.bashrc

# 스크립트가 있는 디렉토리로 이동 (어디서 실행하든 동작하도록)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

#set -x
shopt -s expand_aliases

# 부모 스크립트에서 KUBECONFIG_FILE이 설정되어 있으면 사용, 없으면 기본값 사용
if [ -z "$KUBECONFIG_FILE" ]; then
  if [ -f ~/.kube/my-ubuntu.config ]; then
    KUBECONFIG_FILE=~/.kube/my-ubuntu.config
  else
    KUBECONFIG_FILE=~/.kube/config
  fi
fi
alias k="kubectl --kubeconfig ${KUBECONFIG_FILE} -n consul"
export KUBECONFIG="${KUBECONFIG_FILE}"

# SSH 터널 확인 및 자동 시작 (공통 함수 사용)
if [ -f "${SCRIPT_DIR}/../common-ssh-tunnel.sh" ]; then
  source "${SCRIPT_DIR}/../common-ssh-tunnel.sh"
  check_and_start_ssh_tunnel "${KUBECONFIG_FILE}"
fi

NS=velero

# Velero namespace 생성
kubectl create namespace ${NS} --dry-run=client -o yaml | kubectl apply -f -

# Helm repository 추가
helm repo add vmware-tanzu https://vmware-tanzu.github.io/helm-charts
helm repo update

# 기존 설치 제거
helm uninstall velero -n ${NS} 2>/dev/null || true

# MinIO credentials 가져오기 (MinIO가 설치되어 있어야 함)
MINIO_ROOT_USER=$(kubectl get secret minio -n devops -o jsonpath='{.data.rootUser}' 2>/dev/null | base64 -d || echo "topzone-k8s")
MINIO_ROOT_PASSWORD=$(kubectl get secret minio -n devops -o jsonpath='{.data.rootPassword}' 2>/dev/null | base64 -d || echo "DevOps!323")

# Velero credentials secret 생성
kubectl create secret generic credentials-velero \
  --from-literal=cloud="[default]
aws_access_key_id=${MINIO_ROOT_USER}
aws_secret_access_key=${MINIO_ROOT_PASSWORD}" \
  -n ${NS} \
  --dry-run=client -o yaml | kubectl apply -f -

# Velero CRD 설치 (Helm chart의 upgradeCRDs가 제대로 작동하지 않을 수 있으므로 수동 설치)
echo "Velero CRD 설치 중..."
VELERO_VERSION="v1.16.1"
VELERO_DIR="velero-${VELERO_VERSION}-linux-amd64"

if [ ! -d "${VELERO_DIR}" ]; then
  wget -q https://github.com/vmware-tanzu/velero/releases/download/${VELERO_VERSION}/velero-${VELERO_VERSION}-linux-amd64.tar.gz
  tar -xzf velero-${VELERO_VERSION}-linux-amd64.tar.gz
fi

# v1 CRD 설치
if [ -d "${VELERO_DIR}/config/crd/bases" ]; then
  kubectl apply -f ${VELERO_DIR}/config/crd/bases/
  echo "v1 CRD 설치 완료"
fi

# v2alpha1 CRD 설치 (CSI 기능용)
if ! kubectl get crd datadownloads.velero.io > /dev/null 2>&1; then
  echo "v2alpha1 CRD 설치 중..."
  # GitHub에서 직접 설치 (Velero v1.16.1 릴리스에 포함되지 않을 수 있음)
  kubectl apply -f https://raw.githubusercontent.com/vmware-tanzu/velero/main/config/crd/v2alpha1/bases/velero.io_datadownloads.yaml 2>/dev/null || true
  kubectl apply -f https://raw.githubusercontent.com/vmware-tanzu/velero/main/config/crd/v2alpha1/bases/velero.io_datauploads.yaml 2>/dev/null || true
  
  # 또는 로컬 파일에서 설치 시도
  if [ -d "${VELERO_DIR}/config/crd/v2alpha1" ]; then
    kubectl apply -f ${VELERO_DIR}/config/crd/v2alpha1/ 2>/dev/null || true
  elif [ -f "${VELERO_DIR}/config/crd/bases/velero.io_datadownloads.yaml" ]; then
    kubectl apply -f ${VELERO_DIR}/config/crd/bases/velero.io_datadownloads.yaml 2>/dev/null || true
    kubectl apply -f ${VELERO_DIR}/config/crd/bases/velero.io_datauploads.yaml 2>/dev/null || true
  fi
  
  if kubectl get crd datadownloads.velero.io > /dev/null 2>&1; then
    echo "v2alpha1 CRD 설치 완료"
  else
    echo "Warning: v2alpha1 CRD 설치 실패. CSI 기능이 비활성화되어 있으므로 문제없을 수 있습니다."
  fi
else
  echo "v2alpha1 CRD가 이미 설치되어 있습니다."
fi

# Velero values.yaml 생성 (MinIO URL 업데이트)
cp -f values.yaml values.yaml_bak
sed -i "s|s3Url: http://minio-svc.devops.svc.cluster.local:9000|s3Url: http://minio-svc.devops.svc.cluster.local:9000|g" values.yaml_bak
sed -i "s|bucket: devops-velero|bucket: velero|g" values.yaml_bak
sed -i "s|region: minio|region: minio-default|g" values.yaml_bak

# tz-registrykey secret이 velero namespace에 있는지 확인하고 없으면 복사
if ! kubectl get secret tz-registrykey -n ${NS} > /dev/null 2>&1; then
  if kubectl get secret tz-registrykey -n devops > /dev/null 2>&1; then
    echo "tz-registrykey secret을 velero namespace로 복사 중..."
    kubectl get secret tz-registrykey -n devops -o yaml | sed "s/namespace: devops/namespace: ${NS}/" | kubectl apply -f -
  fi
fi

# Velero 설치 (values.yaml 사용)
helm install velero vmware-tanzu/velero \
  --namespace ${NS} \
  --version 3.1.2 \
  -f values.yaml_bak \
  --set configuration.backupStorageLocation.config.s3Url=http://minio-svc.devops.svc.cluster.local:9000 \
  --set credentials.existingSecret=credentials-velero \
  --set kubectl.image.repository="" \
  --set upgradeCRDs=false \
  --set metrics.prometheusRule.enabled=false

echo "Velero 설치 완료. Pod 상태 확인 중..."
sleep 10
kubectl get pods -n ${NS}

# Velero Pod가 정상적으로 실행되는지 확인
echo ""
echo "Velero 설치 상태:"
kubectl get deployment velero -n ${NS} 2>/dev/null || echo "Velero deployment를 확인할 수 없습니다."

# 일별 백업 스케줄 적용 (provisioning/install.sh 모듈 대상)
echo ""
echo "일별 백업 스케줄 적용 중..."
if [ -f "${SCRIPT_DIR}/schedule-daily.yaml" ]; then
  kubectl apply -f "${SCRIPT_DIR}/schedule-daily.yaml"
  echo "Schedule daily-provisioning-backup 적용 완료 (매일 02:00 UTC, 보관 7일)"
  kubectl get schedule -n ${NS}
else
  echo "Warning: schedule-daily.yaml not found at ${SCRIPT_DIR}/schedule-daily.yaml"
fi

exit 0
