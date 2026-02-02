# Celery 설정 가이드

이 문서는 DrillQuiz 프로젝트에서 Celery를 사용한 비동기 작업 처리 설정을 설명합니다.

## 개요

Celery는 Django 애플리케이션에서 시간이 오래 걸리는 작업(예: 번역 작업)을 백그라운드에서 비동기로 처리하기 위해 사용됩니다.

## 구성 요소

### 1. Celery 앱 설정
- `drillquiz/celery.py`: Celery 앱 초기화 및 설정
- `drillquiz/__init__.py`: Django 시작 시 Celery 앱 로드

### 2. Celery 태스크
- `quiz/tasks.py`: 비동기 작업 태스크 정의
  - `save_translation_results`: 단일 번역 결과 저장
  - `batch_save_translation_results`: 배치 번역 결과 저장

### 3. Django 설정
- `drillquiz/settings.py`: Celery 브로커 및 결과 백엔드 설정

## 설치

### 1. 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. Redis 확인
Celery는 Redis를 메시지 브로커로 사용합니다. Redis가 실행 중인지 확인하세요:

```bash
# 로컬 환경
redis-cli ping

# Kubernetes 환경
kubectl get pods -n devops | grep redis
```

## 실행

### 1. Celery 워커 실행

#### 로컬 개발 환경
```bash
# Django 프로젝트 루트에서 실행
celery -A drillquiz worker --loglevel=info

# 또는 백그라운드로 실행
celery -A drillquiz worker --loglevel=info --detach
```

#### 프로덕션 환경 (Kubernetes)
Celery 워커는 별도의 Deployment로 실행됩니다.

### 2. Celery Beat (주기적 작업, 선택사항)
주기적 작업이 필요한 경우:
```bash
celery -A drillquiz beat --loglevel=info
```

### 3. Celery Flower (모니터링, 선택사항)
Celery 작업 모니터링을 위한 웹 UI:
```bash
pip install flower
celery -A drillquiz flower
```

## 설정

### 환경 변수

#### 로컬 개발 환경
```bash
# .env 파일 또는 환경 변수
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

#### 프로덕션 환경 (Kubernetes)
```yaml
# ConfigMap 또는 Secret
CELERY_BROKER_URL=redis://redis-cluster-drillquiz-master.devops.svc.cluster.local:6379/0
CELERY_RESULT_BACKEND=redis://redis-cluster-drillquiz-master.devops.svc.cluster.local:6379/2
```

### Redis DB 분리
- DB 0: Celery 브로커 (메시지 큐)
- DB 1: Django 캐시
- DB 2: Celery 결과 백엔드

## 사용 방법

### 번역 작업 비동기 저장

조회 시 번역 결과는 자동으로 Celery 태스크로 전송되어 비동기로 저장됩니다:

```python
# quiz/utils/multilingual_utils.py에서 자동 처리
# skip_completion_update=True일 때 Celery 태스크로 저장
```

### 수동 태스크 호출

```python
from quiz.tasks import batch_save_translation_results

# 비동기 실행
batch_save_translation_results.delay(
    model_name='Exam',
    instance_id='123e4567-e89b-12d3-a456-426614174000',
    language_group=('ko', 'en'),
    field_names=['title', 'description'],
    translated_texts=['Title', 'Description']
)
```

## 모니터링

### 로그 확인
```bash
# Celery 워커 로그
tail -f celery.log

# Django 로그
tail -f drillquiz.log | grep CELERY
```

### 작업 상태 확인
```python
from quiz.tasks import batch_save_translation_results

# 태스크 실행
result = batch_save_translation_results.delay(...)

# 상태 확인
print(result.state)  # PENDING, SUCCESS, FAILURE 등
print(result.get())  # 결과 가져오기 (블로킹)
```

## 문제 해결

### 1. 워커가 작업을 받지 못함
- Redis 연결 확인
- `CELERY_BROKER_URL` 설정 확인
- 워커가 실행 중인지 확인

### 2. 태스크가 실행되지 않음
- 워커 로그 확인
- Redis 연결 확인
- 모델 및 필드명 확인

### 3. 성능 문제
- 워커 수 증가: `celery -A drillquiz worker --concurrency=4`
- 프리페치 설정 조정: `settings.py`의 `CELERY_WORKER_PREFETCH_MULTIPLIER`

## Kubernetes 배포

### Deployment 예시
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: drillquiz-celery-worker
  namespace: devops
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: celery-worker
        image: drillquiz-backend:latest
        command: ["celery", "-A", "drillquiz", "worker", "--loglevel=info"]
        env:
        - name: CELERY_BROKER_URL
          value: "redis://redis-cluster-drillquiz-master.devops.svc.cluster.local:6379/0"
        - name: CELERY_RESULT_BACKEND
          value: "redis://redis-cluster-drillquiz-master.devops.svc.cluster.local:6379/2"
```

## 참고 자료

- [Celery 공식 문서](https://docs.celeryproject.org/)
- [Django + Celery 가이드](https://docs.celeryproject.org/en/stable/django/first-steps-with-django.html)

