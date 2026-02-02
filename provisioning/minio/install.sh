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

k8s_project=$(prop 'project' 'project')
k8s_domain=$(prop 'project' 'domain')

NS=devops

kubectl create namespace ${NS}
#k apply -f storageclass.yaml -n ${NS}

# MinIO 공식 Helm chart 사용 (개발 서버와 동일)
helm repo add minio https://charts.min.io/
helm repo update
helm uninstall minio -n ${NS} 2>/dev/null || true

# MinIO 공식 Helm chart 설치
helm upgrade --install minio minio/minio --version 5.4.0 -n ${NS} -f values.yaml

sleep 60

MINIO_ROOT_USER=$(kubectl get secret --namespace ${NS} minio -o jsonpath="{.data.rootUser}" | base64 --decode; echo)
MINIO_ROOT_PASSWORD=$(kubectl get secret --namespace ${NS} minio -o jsonpath="{.data.rootPassword}" | base64 --decode; echo)
echo "MinIO Root User: ${MINIO_ROOT_USER}"
echo "MinIO Root Password: ${MINIO_ROOT_PASSWORD}"

# MinIO 외부 접속을 위한 Ingress 배포
cp -Rf minio-ingress.yaml minio-ingress.yaml_bak
sed -i "s/k8s_project/${k8s_project}/g" minio-ingress.yaml_bak
sed -i "s/k8s_domain/${k8s_domain}/g" minio-ingress.yaml_bak
k apply -f minio-ingress.yaml_bak -n ${NS}

#kubectl -n ${NS} port-forward svc/minio 9000:9000
#kubectl -n ${NS} port-forward svc/minio-console 9001:9001

exit 0
