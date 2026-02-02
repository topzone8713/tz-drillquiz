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

NS=default

# Ingress NGINX 설치
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

APP_VERSION=4.0.13
helm uninstall ingress-nginx -n ${NS} 2>/dev/null || true

helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
  -f values.yaml \
  --version ${APP_VERSION} \
  -n ${NS}

# ValidatingWebhookConfiguration 삭제 (필요시)
kubectl delete ValidatingWebhookConfiguration ingress-nginx-admission 2>/dev/null || true

sleep 60

# Ingress NGINX 상태 확인
kubectl get pods -n ${NS}
kubectl get service ingress-nginx-controller -n ${NS}

#### cert-manager 설치 ####
helm repo add jetstack https://charts.jetstack.io
helm repo update

helm uninstall cert-manager -n cert-manager 2>/dev/null || true

# cert-manager 네임스페이스 생성
kubectl create namespace cert-manager --dry-run=client -o yaml | kubectl apply -f -

# cert-manager CRDs 설치
kubectl apply --validate=false -f https://github.com/cert-manager/cert-manager/releases/download/v1.10.0/cert-manager.crds.yaml

# cert-manager 설치
helm upgrade --install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=false \
  --version v1.10.0

sleep 60

# cert-manager 상태 확인
kubectl get pods -n cert-manager

# Let's Encrypt ClusterIssuer 적용
kubectl apply -f letsencrypt-prod.yaml

# ClusterIssuer 상태 확인
kubectl get clusterissuer letsencrypt-prod

exit 0
