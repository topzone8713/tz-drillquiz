# 운영 환경 디버깅 가이드

운영 환경에서 문제를 진단하고 해결하기 위한 종합 가이드입니다.

## 📋 목차

1. [환경 설정](#환경-설정)
2. [Kubernetes 접근](#kubernetes-접근)
3. [데이터베이스 접근](#데이터베이스-접근)
4. [Pod 접근 및 로그 확인](#pod-접근-및-로그-확인)
5. [자주 사용하는 명령어](#자주-사용하는-명령어)
6. [디버깅 시나리오](#디버깅-시나리오)
7. [환경 변수 설정](#환경-변수-설정)

---

## 환경 설정

### Kubeconfig 설정

운영 환경 Kubernetes 클러스터에 접근하기 위한 kubeconfig 파일 경로:

```bash
# Kubeconfig 파일 경로
export KUBECONFIG=~/.kube/topzone.iptime.org.config

# 또는 백업 파일 사용
export KUBECONFIG=~/.kube/topzone.iptime.org.config.backup

# 설정 확인
kubectl config current-context
kubectl cluster-info
```

### 네임스페이스

- **운영 환경**: `devops`
- **개발 환경**: `devops-dev`

---

## Kubernetes 접근

### 클러스터 연결 확인

```bash
# 클러스터 정보 확인
kubectl cluster-info

# 네임스페이스 확인
kubectl get namespaces

# 운영 환경 Pod 목록 확인
kubectl get pods -n devops

# Pod 상태 상세 확인
kubectl get pods -n devops -o wide
```

### Pod 목록 확인

```bash
# 모든 Pod 확인
kubectl get pods -n devops

# 특정 앱 Pod만 확인
kubectl get pods -n devops | grep drillquiz

# Pod 상태 필터링
kubectl get pods -n devops --field-selector status.phase=Running
```

---

## 데이터베이스 접근

### 데이터베이스 정보

#### 운영 환경 (Production)

- **네임스페이스**: `devops`
- **호스트**: `devops-postgres-postgresql.devops.svc.cluster.local`
- **데이터베이스**: `drillquiz`
- **사용자**: `admin`
- **비밀번호**: `DevOps!323`
- **포트**: `5432` (클러스터 내부)

#### 개발 환경 (Development)

- **네임스페이스**: `devops-dev`
- **호스트**: `devops-postgres-postgresql.devops-dev.svc.cluster.local`
- **데이터베이스**: `drillquiz` 또는 `drillquiz-qa`
- **사용자**: `admin`
- **비밀번호**: `DevOps!323`

### 데이터베이스 접근 방법

#### 방법 1: Pod를 통한 접근 (권장)

```bash
# PostgreSQL Pod에 접근
kubectl exec -it -n devops devops-postgres-postgresql-0 -- bash

# PostgreSQL CLI 접근
kubectl exec -it -n devops devops-postgres-postgresql-0 -- psql -U admin -d drillquiz
```

#### 방법 2: 포트 포워딩을 통한 로컬 접근

```bash
# PostgreSQL 포트 포워딩
kubectl port-forward -n devops svc/devops-postgres-postgresql 5432:5432

# 다른 터미널에서 로컬 접근
psql -h localhost -p 5432 -U admin -d drillquiz
```

#### 방법 3: Django Shell을 통한 접근

```bash
# Django Pod에 접근
kubectl exec -it -n devops <drillquiz-pod-name> -- bash

# Django Shell 실행
python manage.py shell

# 데이터베이스 쿼리 예시
from quiz.models import Exam, Study, Question
print(f"Total Exams: {Exam.objects.count()}")
print(f"Total Studies: {Study.objects.count()}")
print(f"Total Questions: {Question.objects.count()}")
```

### 데이터베이스 백업

```bash
# bastion Pod를 통한 백업
kubectl exec -it -n devops-dev bastion -- bash -c "
pg_dump -h devops-postgres-postgresql.devops.svc.cluster.local \
        -U admin \
        -d drillquiz > /data/operational_backup_\$(date +%Y%m%d_%H%M%S).sql
"

# 백업 파일 확인
kubectl exec -it -n devops-dev bastion -- ls -la /data/operational_backup_*.sql
```

---

## Pod 접근 및 로그 확인

### Pod 접근

```bash
# Pod 이름 확인
kubectl get pods -n devops

# Pod에 bash 접근
kubectl exec -it -n devops <pod-name> -- bash

# Pod에 sh 접근 (bash가 없는 경우)
kubectl exec -it -n devops <pod-name> -- sh
```

### 로그 확인

```bash
# 실시간 로그 확인
kubectl logs -n devops <pod-name> -f

# 최근 100줄 로그 확인
kubectl logs -n devops <pod-name> --tail=100

# 특정 시간 이후 로그 확인
kubectl logs -n devops <pod-name> --since=1h

# 여러 Pod의 로그 확인 (Label Selector 사용)
kubectl logs -n devops -l app=drillquiz --tail=100

# 이전 컨테이너 로그 확인 (재시작된 Pod)
kubectl logs -n devops <pod-name> --previous
```

### 로그 필터링

```bash
# 에러 로그만 확인
kubectl logs -n devops <pod-name> --tail=500 | grep -i error

# 특정 사용자 관련 로그 확인
kubectl logs -n devops <pod-name> --tail=500 | grep -i "Doohee\|doohee"

# API 요청 로그 확인
kubectl logs -n devops <pod-name> --tail=500 | grep -E "(GET|POST|PUT|DELETE).*api"

# 시험 관련 로그 확인
kubectl logs -n devops <pod-name> --tail=500 | grep -i exam
```

---

## 자주 사용하는 명령어

### Pod 관리

```bash
# Pod 재시작
kubectl rollout restart deployment/drillquiz -n devops

# Pod 상태 확인
kubectl describe pod <pod-name> -n devops

# Pod 이벤트 확인
kubectl get events -n devops --sort-by='.lastTimestamp'

# Pod 리소스 사용량 확인
kubectl top pods -n devops
```

### Deployment 관리

```bash
# Deployment 상태 확인
kubectl get deployments -n devops

# Deployment 상세 정보
kubectl describe deployment drillquiz -n devops

# Deployment 롤아웃 히스토리
kubectl rollout history deployment/drillquiz -n devops

# Deployment 롤백
kubectl rollout undo deployment/drillquiz -n devops
```

### 서비스 및 인그레스

```bash
# 서비스 확인
kubectl get svc -n devops

# 인그레스 확인
kubectl get ingress -n devops

# 인그레스 상세 정보
kubectl describe ingress drillquiz -n devops
```

### ConfigMap 및 Secret

```bash
# ConfigMap 확인
kubectl get configmap -n devops

# ConfigMap 내용 확인
kubectl get configmap <configmap-name> -n devops -o yaml

# Secret 확인
kubectl get secret -n devops

# Secret 내용 확인 (base64 디코딩 필요)
kubectl get secret <secret-name> -n devops -o jsonpath='{.data}' | jq
```

---

## 디버깅 시나리오

### 시나리오 1: 사용자 데이터 조회 문제

```bash
# 1. Pod 로그 확인
kubectl logs -n devops <drillquiz-pod-name> --tail=200 | grep -E "(Doohee|doohee|exam|GET.*exams)"

# 2. 데이터베이스에서 사용자 확인
kubectl exec -it -n devops devops-postgres-postgresql-0 -- psql -U admin -d drillquiz -c "
SELECT id, username, email, is_active 
FROM auth_user 
WHERE username = 'Doohee3231';
"

# 3. 사용자와 연관된 시험 확인
kubectl exec -it -n devops <drillquiz-pod-name> -- python manage.py shell -c "
from django.contrib.auth import get_user_model
from quiz.models import Exam, ExamResult, Member
User = get_user_model()
user = User.objects.get(username='Doohee3231')
print(f'Created Exams: {Exam.objects.filter(created_by=user).count()}')
print(f'Taken Exams: {ExamResult.objects.filter(user=user).count()}')
print(f'Study Memberships: {Member.objects.filter(user=user, is_active=True).count()}')
print(f'Public Exams: {Exam.objects.filter(is_public=True).count()}')
"
```

### 시나리오 2: API 응답 문제

```bash
# 1. API 요청 로그 확인
kubectl logs -n devops <drillquiz-pod-name> --tail=500 | grep -E "(GET|POST).*api"

# 2. 에러 로그 확인
kubectl logs -n devops <drillquiz-pod-name> --tail=500 | grep -i error

# 3. 특정 엔드포인트 로그 확인
kubectl logs -n devops <drillquiz-pod-name> --tail=500 | grep "/api/exams/"
```

### 시나리오 3: 데이터베이스 연결 문제

```bash
# 1. PostgreSQL Pod 상태 확인
kubectl get pods -n devops | grep postgres

# 2. PostgreSQL 로그 확인
kubectl logs -n devops devops-postgres-postgresql-0 --tail=100

# 3. 연결 테스트
kubectl exec -it -n devops <drillquiz-pod-name> -- python manage.py shell -c "
from django.db import connection
connection.ensure_connection()
print('Database connection successful')
"
```

### 시나리오 4: 캐시 문제

```bash
# 1. Redis Pod 상태 확인
kubectl get pods -n devops | grep redis

# 2. Redis 연결 테스트
kubectl exec -it -n devops redis-cluster-drillquiz-master-0 -- redis-cli ping

# 3. 캐시 클리어 (Django Pod에서)
kubectl exec -it -n devops <drillquiz-pod-name> -- python manage.py shell -c "
from django.core.cache import cache
cache.clear()
print('Cache cleared')
"
```

### 시나리오 5: 지원언어 필터링 문제

```bash
# 1. 시험의 supported_languages 확인
kubectl exec -it -n devops <drillquiz-pod-name> -- python manage.py shell -c "
from quiz.models import Exam
public_exams = Exam.objects.filter(is_public=True)
for exam in public_exams:
    print(f'ID: {exam.id}, Title: {exam.title_en[:50]}, Supported: {exam.supported_languages}')
"

# 2. 영어 완성도 확인
kubectl exec -it -n devops <drillquiz-pod-name> -- python manage.py shell -c "
from quiz.models import Exam
public_exams = Exam.objects.filter(is_public=True)
for exam in public_exams:
    has_title_en = bool(exam.title_en and exam.title_en.strip())
    has_desc_en = bool(exam.description_en and exam.description_en.strip())
    print(f'ID: {exam.id}, title_en: {has_title_en}, description_en: {has_desc_en}')
"
```

---

## 환경 변수 설정

### 로컬에서 Kubernetes DB 접근

```bash
# Kubeconfig 설정
export KUBECONFIG=~/.kube/topzone.iptime.org.config

# 포트 포워딩 (별도 터미널)
kubectl port-forward -n devops svc/devops-postgres-postgresql 5432:5432

# 환경 변수 설정
export USE_DOCKER=true
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=drillquiz
export POSTGRES_USER=admin
export POSTGRES_PASSWORD='DevOps!323'
```

### Django 관리 명령어 실행

```bash
# 마이그레이션 실행
kubectl exec -it -n devops <drillquiz-pod-name> -- python manage.py migrate

# 마이그레이션 상태 확인
kubectl exec -it -n devops <drillquiz-pod-name> -- python manage.py showmigrations

# Django Shell 실행
kubectl exec -it -n devops <drillquiz-pod-name> -- python manage.py shell

# 데이터베이스 쿼리 실행
kubectl exec -it -n devops <drillquiz-pod-name> -- python manage.py shell -c "
from quiz.models import Exam
print(f'Total Exams: {Exam.objects.count()}')
"
```

---

## 추가 리소스

### Redis 정보

- **호스트**: `redis-cluster-drillquiz-master.devops.svc.cluster.local`
- **포트**: `6379`
- **데이터베이스**: `1`

### MinIO 정보

- **엔드포인트**: `http://minio.devops.svc.cluster.local:9000`
- **버킷**: `drillquiz` (운영), `drillquiz-dev` (개발)

### 네임스페이스별 리소스

```bash
# 모든 리소스 확인
kubectl get all -n devops

# PVC (Persistent Volume Claim) 확인
kubectl get pvc -n devops

# ConfigMap 확인
kubectl get configmap -n devops

# Secret 확인
kubectl get secret -n devops
```

---

## 주의사항

⚠️ **운영 환경에서 작업 시 주의사항:**

1. **데이터 백업**: 데이터베이스 작업 전 반드시 백업 수행
2. **읽기 전용 작업 우선**: 가능한 한 읽기 작업만 수행
3. **변경 사항 문서화**: 모든 변경 사항을 기록
4. **롤백 계획**: 변경 전 롤백 방법 확인
5. **영향 범위 확인**: 변경이 다른 서비스에 미치는 영향 확인

---

## 빠른 참조

### 가장 자주 사용하는 명령어

```bash
# Pod 로그 확인
kubectl logs -n devops <pod-name> --tail=100

# Pod 접근
kubectl exec -it -n devops <pod-name> -- bash

# 데이터베이스 접근
kubectl exec -it -n devops devops-postgres-postgresql-0 -- psql -U admin -d drillquiz

# Django Shell 실행
kubectl exec -it -n devops <pod-name> -- python manage.py shell

# Pod 재시작
kubectl rollout restart deployment/drillquiz -n devops
```

---

**마지막 업데이트**: 2025-11-26  
**작성자**: AI Assistant  
**버전**: 1.0.0



