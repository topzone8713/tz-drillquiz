# 로컬 Redis 설정 가이드

로컬 개발 환경에서도 서버와 동일하게 Redis를 사용하도록 설정하는 방법입니다.

## Redis 설치

### macOS (Homebrew)
```bash
# Redis 설치
brew install redis

# Redis 서비스 시작 (부팅 시 자동 시작)
brew services start redis

# 또는 수동으로 시작
redis-server
```

### Linux (Ubuntu/Debian)
```bash
# Redis 설치
sudo apt-get update
sudo apt-get install redis-server

# Redis 서비스 시작
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### Docker
```bash
# Redis 컨테이너 실행
docker run -d -p 6379:6379 --name redis redis:latest
```

## Redis 확인

### 연결 테스트
```bash
# Redis CLI로 연결 테스트
redis-cli ping
# 응답: PONG
```

### Redis 상태 확인
```bash
# Redis 서비스 상태 확인 (macOS)
brew services list | grep redis

# Redis 프로세스 확인
ps aux | grep redis
```

## Django 설정

### 환경 변수 (선택사항)
`.env` 파일에 Redis URL을 명시적으로 설정할 수 있습니다:

```bash
REDIS_URL=redis://localhost:6379/1
```

### 자동 감지
Django는 시작 시 자동으로 로컬 Redis 연결을 시도합니다:
- Redis가 사용 가능하면: Redis 캐시 사용
- Redis가 없으면: 로컬 메모리 캐시로 폴백

## Redis DB 분리

로컬 환경에서도 서버와 동일하게 Redis DB를 분리하여 사용합니다:

- **DB 0**: Celery 브로커 (메시지 큐)
- **DB 1**: Django 캐시
- **DB 2**: Celery 결과 백엔드

## 캐시 확인

### Django에서 캐시 테스트
```python
# Django shell에서
python manage.py shell

from django.core.cache import cache
cache.set('test_key', 'test_value', 60)
cache.get('test_key')
```

### Redis에서 직접 확인
```bash
# Redis CLI 접속
redis-cli

# DB 1 선택 (Django 캐시)
SELECT 1

# 모든 키 확인
KEYS *

# 특정 키 확인
GET drillquiz_development:test_key
```

## 문제 해결

### 1. Redis 연결 실패
```
⚠️  로컬 Redis 연결 실패: [Errno 61] Connection refused
```

**해결 방법:**
- Redis 서비스가 실행 중인지 확인
- `brew services start redis` (macOS)
- `sudo systemctl start redis-server` (Linux)

### 2. 포트 충돌
기본 포트 6379가 사용 중인 경우:
```bash
# 다른 포트로 Redis 실행
redis-server --port 6380
```

환경 변수 설정:
```bash
REDIS_URL=redis://localhost:6380/1
```

### 3. 권한 문제
```bash
# Redis 데이터 디렉토리 권한 확인
sudo chown -R $(whoami) /usr/local/var/db/redis
```

## Celery와 함께 사용

로컬에서 Celery 워커를 실행할 때도 Redis를 사용합니다:

```bash
# Celery 워커 실행
celery -A drillquiz worker --loglevel=info
```

Celery는 자동으로 `redis://localhost:6379/0` (DB 0)을 브로커로 사용합니다.

## 성능 비교

### 로컬 메모리 캐시 (LocMemCache)
- ✅ 빠른 속도
- ❌ 프로세스 간 공유 불가
- ❌ 서버 환경과 다름

### Redis 캐시
- ✅ 서버 환경과 동일
- ✅ 프로세스 간 공유 가능
- ✅ Celery와 통합 가능
- ⚠️ Redis 설치 필요

## 참고 자료

- [Redis 공식 문서](https://redis.io/documentation)
- [Django Redis 캐시](https://django-redis.readthedocs.io/)

