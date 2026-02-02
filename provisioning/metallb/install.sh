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

NS=metallb-system
METALLB_VERSION="v0.12.1"

# kube-proxy strictARP 설정 (MetalLB 필수)
kubectl get configmap kube-proxy -n kube-system -o yaml | \
sed -e "s/strictARP: false/strictARP: true/" | \
kubectl apply -f - -n kube-system

# MetalLB 네임스페이스 생성
kubectl create namespace ${NS} --dry-run=client -o yaml | kubectl apply -f -

# MetalLB 설치 (GitHub에서 직접 다운로드)
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/${METALLB_VERSION}/manifests/namespace.yaml
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/${METALLB_VERSION}/manifests/metallb.yaml -n ${NS}

sleep 60

# Memberlist secret 생성 (첫 설치 시에만 필요)
# 기존 secret이 있으면 생성하지 않음
if ! kubectl get secret memberlist -n ${NS} &> /dev/null; then
    kubectl create secret generic memberlist -n ${NS} --from-literal=secretkey="$(openssl rand -base64 128)"
fi

# Layer2 IP 주소 풀 설정
kubectl apply -f layer2-config.yaml -n ${NS}

# Pod 상태 확인
kubectl get pods -n ${NS}

#kubectl logs -l component=speaker -n ${NS}

exit 0