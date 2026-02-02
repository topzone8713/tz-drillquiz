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
  else
    KUBECONFIG_FILE=~/.kube/config
  fi
fi
alias k="kubectl --kubeconfig ${KUBECONFIG_FILE}"
export KUBECONFIG="${KUBECONFIG_FILE}"

# SSH 터널 확인 및 자동 시작 (공통 함수 사용)
if [ -f "${SCRIPT_DIR}/../../common-ssh-tunnel.sh" ]; then
  source "${SCRIPT_DIR}/../../common-ssh-tunnel.sh"
  check_and_start_ssh_tunnel "${KUBECONFIG_FILE}"
elif [ -f "${SCRIPT_DIR}/../common-ssh-tunnel.sh" ]; then
  source "${SCRIPT_DIR}/../common-ssh-tunnel.sh"
  check_and_start_ssh_tunnel "${KUBECONFIG_FILE}"
fi

k8s_project=$(prop 'project' 'project')
k8s_domain=$(prop 'project' 'domain')

helm repo add jenkins https://charts.jenkins.io
helm search repo jenkins

helm list --all-namespaces -a

# 기존 Helm release가 있으면 삭제
if helm list -n jenkins | grep -q jenkins; then
  echo "Existing Jenkins Helm release found. Deleting..."
  helm delete jenkins -n jenkins
  sleep 5
fi

# 기존 수동으로 생성된 리소스들 정리 (Helm이 관리하도록)
echo "Cleaning up manually created resources..."
k delete serviceaccount jenkins -n jenkins --ignore-not-found=true
k delete role jenkins -n jenkins --ignore-not-found=true
k delete rolebinding jenkins -n jenkins --ignore-not-found=true
k delete clusterrolebinding jenkins-crb --ignore-not-found=true
k delete clusterrole jenkinsclusterrole --ignore-not-found=true
# clusterRole.yaml의 리소스들도 정리 (이름이 다를 수 있음)
k delete clusterrole jenkins --ignore-not-found=true
k delete clusterrolebinding jenkins --ignore-not-found=true

k create namespace jenkins --dry-run=client -o yaml | k apply -f -

# jenkins.yaml은 더 이상 사용하지 않음 (Helm이 모든 리소스를 관리)
# k apply -f jenkins.yaml

APP_VERSION=5.8.116
# helm show values로 최신 기본 values.yaml 가져오기 (참고용)
echo "Fetching default values from Helm chart for reference..."
helm repo update
# helm show values jenkins/jenkins --version "${APP_VERSION}" > values.yaml 2>/dev/null || true

# 기존 values.yaml 사용 (helm show values는 참고용으로만)
# values.yaml을 복사하고 필요한 부분만 sed로 수정
cp -Rf values.yaml values.yaml_bak
sed -i "s|k8s_project|${k8s_project}|g" values.yaml_bak
sed -i "s|tz-registrykey|tz-registrykey|g" values.yaml_bak

# 최신 안정 버전으로 설치 (Jenkins 2.528.3-jdk21)
helm upgrade --install jenkins jenkins/jenkins \
  --namespace jenkins \
  --version "${APP_VERSION}" \
  -f values.yaml_bak

if [ $? -ne 0 ]; then
  echo "ERROR: Helm install failed!"
  exit 1
fi
#k patch svc jenkins --type='json' -p '[{"op":"replace","path":"/spec/type","value":"NodePort"},{"op":"replace","path":"/spec/ports/0/nodePort","value":31000}]' -n jenkins
#k patch svc jenkins -p '{"spec": {"ports": [{"port": 8080,"targetPort": 8080, "name": "http"}], "type": "ClusterIP"}}' -n jenkins --force

#kubectl cp plugin.txt jenkins/jenkins-0:/tmp/plugin.txt
#kubectl -n jenkins exec -it jenkins-0 /bin/bash
#jenkins-plugin-cli --plugin-file /tmp/plugin.txt --plugins delivery-pipeline-plugin:1.3.2 deployit-plugin

cp -Rf jenkins-ingress.yaml jenkins-ingress.yaml_bak
sed -i "s/k8s_project/${k8s_project}/g" jenkins-ingress.yaml_bak
sed -i "s/k8s_domain/${k8s_domain}/g" jenkins-ingress.yaml_bak
k apply -f jenkins-ingress.yaml_bak -n jenkins

# clusterRole.yaml 적용 (필요한 경우 추가 RBAC 권한 부여)
# 주의: Helm chart가 자동으로 생성하는 RBAC와 함께 사용됨
if [ -f clusterRole.yaml ]; then
  echo "Applying clusterRole.yaml..."
  k apply -f clusterRole.yaml
fi

echo "waiting for starting a jenkins server!"
sleep 60

mkdir -p /${HOME}/.docker

# docker-config ConfigMap 적용
# dockerConfig.yml 파일이 있으면 사용하고, 없으면 provisioning/resources/config.json 사용
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
if [ -f dockerConfig.yml ]; then
  echo "Applying dockerConfig.yml..."
  k apply -f dockerConfig.yml -n jenkins
else
  # 기존 방식: provisioning/resources/config.json 사용
  echo "Creating docker-config from provisioning/resources/config.json..."
  cp -Rf "$PROJECT_ROOT/provisioning/resources/config.json" /${HOME}/.docker/config2.json
  k delete configmap docker-config -n jenkins --ignore-not-found=true
  k create configmap docker-config --from-file=/${HOME}/.docker/config2.json -n jenkins
fi

#kubectl cp plugin.txt jenkins/jenkins-0:/tmp/plugin.txt
#kubectl -n jenkins exec -it jenkins-0 /bin/bash
# jenkins-plugin-cli --list
#jenkins-plugin-cli --plugin-file /tmp/plugin.txt --plugins delivery-pipeline-plugin:1.3.2 deployit-plugin

sleep 240

# info 파일 경로: Vagrant VM 내부에서는 /vagrant/info, 호스트에서는 tz-k8s-vagrant/info 또는 tz-drillquiz/info
INFO_FILE="${INFO_FILE:-}"
if [ -z "$INFO_FILE" ]; then
  if [ -d /vagrant ]; then
    INFO_FILE="/vagrant/info"
  elif [ -f "$HOME/workspaces/tz-k8s-vagrant/info" ] || [ -d "$HOME/workspaces/tz-k8s-vagrant" ]; then
    INFO_FILE="$HOME/workspaces/tz-k8s-vagrant/info"
  elif [ -d "$SCRIPT_DIR/../../.." ]; then
    INFO_FILE="$(cd "$SCRIPT_DIR/../../.." && pwd)/info"
  else
    INFO_FILE="/tmp/provisioning-info"
  fi
fi
mkdir -p "$(dirname "$INFO_FILE")" 2>/dev/null || true

JENKINS_INFO="
##[ Jenkins ]##########################################################
#  - URL: https://jenkins.default.${k8s_project}.${k8s_domain}
#
#  - ID: admin
#  - Password:
#    kubectl -n jenkins exec -it svc/jenkins -c jenkins -- /bin/cat /run/secrets/chart-admin-password && echo
#######################################################################
"
echo "$JENKINS_INFO" >> "$INFO_FILE"
cat "$INFO_FILE"

exit 0

