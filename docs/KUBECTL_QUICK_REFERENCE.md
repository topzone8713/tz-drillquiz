# kubectl 빠른 참조 가이드

**⚠️ kubectl 접근이 안 될 때 반드시 확인할 사항**

## 1. Kubeconfig 설정 (필수!)

kubectl을 사용하기 전에 **반드시** KUBECONFIG 환경 변수를 설정해야 합니다.

```bash
# Kubeconfig 파일 경로 설정
export KUBECONFIG=~/.kube/topzone.iptime.org.config

# 또는 백업 파일 사용
export KUBECONFIG=~/.kube/topzone.iptime.org.config.backup

# 설정 확인
kubectl config current-context
# 정상 출력: kubernetes-admin@cluster.local

kubectl cluster-info
```

## 2. 네임스페이스

- **운영 환경**: `devops`
- **개발 환경**: `devops-dev`

## 3. 자주 사용하는 명령어

### Pod 확인
```bash
# 모든 Pod 확인
kubectl get pods -n devops-dev

# 특정 앱 Pod만 확인
kubectl get pods -n devops-dev | grep drillquiz

# Pod 상태 상세 확인
kubectl get pods -n devops-dev -o wide
```

### 로그 확인
```bash
# 실시간 로그 확인
kubectl logs -n devops-dev -l app=drillquiz -f

# 최근 100줄 로그 확인
kubectl logs -n devops-dev -l app=drillquiz --tail=100

# 최근 1시간 로그 확인
kubectl logs -n devops-dev -l app=drillquiz --since=1h

# 특정 API 로그 확인
kubectl logs -n devops-dev -l app=drillquiz --tail=500 | grep "/api/studies"

# 에러 로그만 확인
kubectl logs -n devops-dev -l app=drillquiz --tail=500 | grep -i error
```

### Pod 접근
```bash
# Pod 이름 확인
kubectl get pods -n devops-dev

# Pod에 bash 접근
kubectl exec -it -n devops-dev <pod-name> -- bash

# Django Shell 실행
kubectl exec -it -n devops-dev <pod-name> -- python manage.py shell
```

## 4. 문제 해결

### kubectl 접근이 안 될 때
1. **KUBECONFIG 환경 변수 확인**
   ```bash
   echo $KUBECONFIG
   # 출력이 없으면 설정 필요
   export KUBECONFIG=~/.kube/topzone.iptime.org.config
   ```

2. **네임스페이스 확인**
   ```bash
   kubectl get namespaces
   # devops, devops-dev가 있는지 확인
   ```

3. **Pod가 없는 경우**
   ```bash
   kubectl get pods -n devops-dev
   # Pod가 없으면 Deployment 확인
   kubectl get deployments -n devops-dev
   ```

### 자주 발생하는 에러

#### 에러: `error: error executing jsonpath`
- **원인**: Pod가 없거나 Label Selector가 잘못됨
- **해결**: `kubectl get pods -n devops-dev`로 Pod 확인 후 정확한 이름 사용

#### 에러: `The connection to the server ... was refused`
- **원인**: KUBECONFIG가 설정되지 않았거나 잘못된 경로
- **해결**: `export KUBECONFIG=~/.kube/topzone.iptime.org.config` 실행

## 5. 상세 가이드

더 자세한 내용은 [운영 환경 디버깅 가이드](./PRODUCTION_DEBUGGING_GUIDE.md)를 참고하세요.

---

**마지막 업데이트**: 2025-11-28  
**작성자**: AI Assistant

