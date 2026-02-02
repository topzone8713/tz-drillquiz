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

NS=devops-dev

#k apply -f storageclass.yaml -n ${NS}

helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm uninstall devops-postgres -n ${NS}

#--reuse-values
helm upgrade --install devops-postgres bitnami/postgresql -n ${NS} -f values.yaml

sleep 240

POSTGRES_PASSWORD=$(kubectl get secret --namespace ${NS} devops-postgres-postgresql -o jsonpath="{.data.postgres-password}" | base64 --decode; echo)
echo $POSTGRES_PASSWORD

# PostgreSQL 외부 접속을 위한 NodePort Service 배포
kubectl apply -f postgres-dev.yaml -n ${NS}

#k patch svc devops-postgres-postgresql -n ${NS} -p '{"spec": {"type": "LoadBalancer", "loadBalancerSourceRanges": [ "10.20.0.0/16",  ]}}'
#kubectl -n ${NS} port-forward svc/devops-postgres-postgresql 5432:5432

exit 0

POSTGRES_HOST=$(kubectl get svc devops-postgres-postgresql -n ${NS} | tail -n 1 | awk '{print $4}')
echo ${POSTGRES_HOST}
POSTGRES_PORT=5432

sudo apt-get update && sudo apt-get install postgresql-client -y
PGPASSWORD=${POSTGRES_PASSWORD} psql -h ${POSTGRES_HOST} -p ${POSTGRES_PORT} -U postgres -d postgres -c "CREATE DATABASE test_db;"
PGPASSWORD=${POSTGRES_PASSWORD} psql -h ${POSTGRES_HOST} -p ${POSTGRES_PORT} -U postgres -d postgres -c "\l"
echo PGPASSWORD=${POSTGRES_PASSWORD} psql -h ${POSTGRES_HOST} -p ${POSTGRES_PORT} -U postgres -d postgres -c "\l"

