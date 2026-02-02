# Calico IPIP 설정

## 개요

Kubernetes 클러스터 설치 후 Calico를 IPIP 모드로 구성하는 스크립트입니다.

## 사용 방법

### Kubernetes 설치 직후 (권장)

```bash
cd ~/workspaces/tz-drillquiz/provisioning/calico
bash setup-ipip-after-k8s-install.sh
```

- 클러스터 연결 확인 → Calico 설치 대기 → IPIP 설정 적용

### Calico가 이미 설치된 경우

```bash
cd ~/workspaces/tz-drillquiz/provisioning/calico
bash configure-ipip.sh
```

## 적용 설정

- **IPPool**: `ipipMode: Always`
- **DaemonSet**: `CALICO_IPV4POOL_IPIP: Always`
- **ConfigMap**: `calico_backend: bird`
- Calico 노드 재시작 후 적용

## 검증

```bash
kubectl get ippool default-pool -o jsonpath='{.spec.ipipMode}'   # Always
kubectl get daemonset calico-node -n kube-system -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="CALICO_IPV4POOL_IPIP")].value}'   # Always
kubectl run test-pod --image=busybox --rm -i --restart=Never -- nslookup kubernetes.default.svc.cluster.local
```
