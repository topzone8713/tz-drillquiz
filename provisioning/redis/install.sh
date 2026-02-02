#!/usr/bin/env bash

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

# SSH 터널 확인 및 자동 시작 (공통 함수 사용)
if [ -f "${SCRIPT_DIR}/../common-ssh-tunnel.sh" ]; then
  source "${SCRIPT_DIR}/../common-ssh-tunnel.sh"
  check_and_start_ssh_tunnel "${KUBECONFIG_FILE}"
fi

NS=devops

# local-path StorageClass가 없으면 생성
if ! kubectl get storageclass local-path > /dev/null 2>&1; then
  echo "local-path StorageClass가 없습니다. 생성 중..."
  
  # local-path-provisioner 설치
  helm repo add rancher-latest https://releases.rancher.com/helm-charts/latest
  helm repo update
  
  # local-path-provisioner가 이미 설치되어 있는지 확인
  if ! helm list -n local-path-storage | grep -q local-path-provisioner; then
    helm upgrade --install local-path-provisioner rancher-latest/local-path-provisioner \
      --namespace local-path-storage \
      --create-namespace \
      --wait
    echo "local-path-provisioner 설치 완료"
  else
    echo "local-path-provisioner가 이미 설치되어 있습니다."
  fi
  
  # StorageClass 생성 확인
  sleep 5
  if kubectl get storageclass local-path > /dev/null 2>&1; then
    echo "local-path StorageClass 생성 완료"
  else
    echo "Warning: local-path StorageClass가 생성되지 않았습니다. 수동으로 확인이 필요합니다."
  fi
else
  echo "local-path StorageClass가 이미 존재합니다."
fi

helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm uninstall redis-cluster-drillquiz -n ${NS}

helm upgrade --install redis-cluster-drillquiz bitnami/redis -n ${NS} -f values.yaml

sleep 60

# Redis 상태 확인
kubectl get pods -n ${NS} | grep redis-cluster-drillquiz

exit 0
