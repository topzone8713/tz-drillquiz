"""
Django settings for drillquiz project.
"""

from pathlib import Path
from datetime import timedelta
import os
from drillquiz.env_loader import get_config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# 환경 설정 (Secret > ConfigMap > 시스템 환경 변수 > .env 파일)
ENVIRONMENT = get_config('ENVIRONMENT', default='development')



# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_config('SECRET_KEY', default='django-insecure-drillquiz-secret-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = get_config('DEBUG', default='True', cast=bool)

# 환경에 따른 ALLOWED_HOSTS 설정
# DEBUG 모드에서는 모든 호스트 허용 (환경과 무관)
if DEBUG:
    ALLOWED_HOSTS = ['*', 'localhost', '127.0.0.1', 'devops.localhost', 'leetcode.localhost']
else:
    if ENVIRONMENT == 'production':
        # 환경 변수에서 ALLOWED_HOSTS 가져오기 (Jenkins에서 생성)
        ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
        # 빈 문자열 제거
        ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS if host.strip()]
        
        # 현재 배포된 도메인도 추가 (환경 변수에서)
        current_domain = os.environ.get('CURRENT_DOMAIN', '')
        if current_domain and current_domain not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(current_domain)
        
        # 와일드카드 도메인 추가
        wildcard_hosts = ['*.drillquiz.com', '.drillquiz.com']
        for host in wildcard_hosts:
            if host not in ALLOWED_HOSTS:
                ALLOWED_HOSTS.append(host)
        
        # Django에서 ALLOWED_HOSTS를 튜플로 변환 (일부 Django 버전에서 필요)
        ALLOWED_HOSTS = tuple(ALLOWED_HOSTS)
    else:
        # 개발 환경: 환경 변수에서 ALLOWED_HOSTS 가져오기
        ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
        # 빈 문자열 제거
        ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS if host.strip()]
        
        # 현재 배포된 도메인도 추가 (환경 변수에서)
        current_domain = os.environ.get('CURRENT_DOMAIN', '')
        if current_domain and current_domain not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(current_domain)
        
        # 와일드카드 도메인 추가
        wildcard_hosts = ['*.drillquiz.com', '.drillquiz.com']
        for host in wildcard_hosts:
            if host not in ALLOWED_HOSTS:
                ALLOWED_HOSTS.append(host)

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'storages',
    'channels',  # Django Channels for WebSocket support
    'quiz',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # CORS 미들웨어를 최상단에 배치
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # 언어 감지 미들웨어
    'quiz.middleware.UserLanguageMiddleware',  # 사용자 언어 설정 미들웨어
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',  # CSRF 다시 활성화
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',  # 보안 미들웨어 추가
]

# CORS 미들웨어가 모든 요청에 대해 작동하도록 설정
CORS_ORIGIN_ALLOW_ALL = False  # 보안을 위해 False

# CSRF 설정
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = False
CSRF_USE_SESSIONS = False
CSRF_COOKIE_SECURE = ENVIRONMENT == 'production'  # 프로덕션에서만 True

# OpenAI API 설정
OPENAI_API_KEY = get_config('OPENAI_API_KEY', default=None)
# 가장 저렴한 모델: gpt-3.5-turbo
# gpt-4o-mini도 저렴하지만 gpt-3.5-turbo가 더 저렴함
OPENAI_MODEL = get_config('OPENAI_MODEL', default='gpt-3.5-turbo')

# Gemini API 설정 (OpenAI 대체용)
GEMINI_API_KEY = get_config('GEMINI_API_KEY', default=None)
GEMINI_MODEL = get_config('GEMINI_MODEL', default='gemini-2.5-flash')

# CSRF 쿠키 도메인 설정 (환경에 따라 다르게)
if ENVIRONMENT == 'production':
    CSRF_COOKIE_DOMAIN = '.drillquiz.com'
else:
    CSRF_COOKIE_DOMAIN = None

CSRF_COOKIE_PATH = '/'
CSRF_COOKIE_AGE = 31449600  # 1년
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'

# 세션 쿠키 설정
SESSION_COOKIE_AGE = 1209600  # 2주 (기본값)
SESSION_COOKIE_DOMAIN = '.drillquiz.com' if ENVIRONMENT == 'production' else None
SESSION_COOKIE_SECURE = ENVIRONMENT == 'production'  # 프로덕션에서만 True
SESSION_COOKIE_HTTPONLY = True  # XSS 공격 방지
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF 공격 방지
SESSION_COOKIE_NAME = 'sessionid'
SESSION_SAVE_EVERY_REQUEST = True  # 매 요청마다 세션 저장
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8080',
    'http://127.0.0.1:8080',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://localhost',
    'http://10.0.2.2:8000',
    'http://test.iptime.org:8080',
    'https://test.iptime.org:8080',
    'http://test.iptime.org',
    'https://test.iptime.org',
    # 로컬 개발용 DevOps 도메인
    'http://devops.localhost:8080',
    'https://devops.localhost:8080',
    'http://leetcode.localhost:8080',
    'https://leetcode.localhost:8080',
    # DevOps 도메인 추가
    'https://devops.drillquiz.com',
    'http://devops.drillquiz.com',
    'https://leetcode.drillquiz.com',
    'http://leetcode.drillquiz.com',
    'https://devops-dev.drillquiz.com',
    'http://devops-dev.drillquiz.com',
    'https://leetcode-dev.drillquiz.com',
    'http://leetcode-dev.drillquiz.com',
]

# 환경 변수에서 동적 CSRF 도메인 추가
env_csrf_origins = os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')
for origin in env_csrf_origins:
    origin = origin.strip()
    if origin and origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)

# CORS 설정 (동적으로 처리) - 먼저 정의
CORS_ALLOWED_ORIGINS = [
    'http://localhost:8080',
    'http://127.0.0.1:8080',
    'http://localhost',
    'http://10.0.2.2:8000',
    # 로컬 개발용 DevOps 도메인
    'http://devops.localhost:8080',
    'https://devops.localhost:8080',
    'http://leetcode.localhost:8080',
    'https://leetcode.localhost:8080',
    # DevOps 도메인 추가
    'https://devops.drillquiz.com',
    'http://devops.drillquiz.com',
    'https://leetcode.drillquiz.com',
    'http://leetcode.drillquiz.com',
    'https://devops-dev.drillquiz.com',
    'http://devops-dev.drillquiz.com',
    'https://leetcode-dev.drillquiz.com',
    'http://leetcode-dev.drillquiz.com',
    # Capacitor/Ionic 모바일 앱 origins
    'capacitor://localhost',
    'ionic://localhost',
]

# 환경 변수에서 동적 CORS 도메인 추가
env_cors_origins = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
for origin in env_cors_origins:
    origin = origin.strip()
    if origin and origin not in CORS_ALLOWED_ORIGINS:
        CORS_ALLOWED_ORIGINS.append(origin)

# 현재 배포된 도메인도 CORS에 추가
current_domain = os.environ.get('CURRENT_DOMAIN', '')
if current_domain:
    http_origin = f'http://{current_domain}'
    https_origin = f'https://{current_domain}'
    if http_origin not in CORS_ALLOWED_ORIGINS:
        CORS_ALLOWED_ORIGINS.append(http_origin)
    if https_origin not in CORS_ALLOWED_ORIGINS:
        CORS_ALLOWED_ORIGINS.append(https_origin)

# CORS 추가 설정 - 와일드카드 도메인 허용
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://drillquiz.*\.new-nation\.church$",
    r"^http://drillquiz.*\.new-nation\.church$",
    # Capacitor/Ionic 모바일 앱 origins (모든 capacitor:// 및 ionic:// 허용)
    r"^capacitor://.*$",
    r"^ionic://.*$",
]

# CORS 미들웨어가 모든 요청에 대해 CORS 헤더를 추가하도록 설정
CORS_URLS_REGEX = r'^.*$'

# CORS 미들웨어가 preflight 요청을 처리하도록 설정
CORS_PREFLIGHT_MAX_AGE = 86400

# CORS 허용 헤더 설정
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'cache-control',
    'pragma',
    'expires',
]

# CORS 미들웨어 설정 (CORS_ALLOWED_ORIGINS 정의 후)
CORS_ORIGIN_WHITELIST = CORS_ALLOWED_ORIGINS  # 명시적으로 설정

# 현재 배포된 도메인도 CSRF에 추가
current_domain = os.environ.get('CURRENT_DOMAIN', '')
if current_domain:
    http_origin = f'http://{current_domain}'
    https_origin = f'https://{current_domain}'
    if http_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(http_origin)
    if https_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(https_origin)

# HTTPS 관련 설정
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = False  # 개발 환경에서는 False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# 프록시 설정 (Kubernetes Ingress 사용 시)
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

ROOT_URLCONF = 'drillquiz.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'public'), os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'drillquiz.wsgi.application'
ASGI_APPLICATION = 'drillquiz.asgi.application'

# Channels 설정
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',  # 개발 환경용 (프로덕션에서는 Redis 사용)
    },
}

# Database
# 환경 변수에 따라 데이터베이스 선택
USE_DOCKER = os.environ.get('USE_DOCKER', 'false').lower() == 'true'

# 기본적으로 SQLite 사용 (로컬 개발용)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(BASE_DIR / 'db.sqlite3'),
    }
}

# Docker 환경에서만 PostgreSQL 사용
if USE_DOCKER:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB', 'drillquiz'),
            'USER': os.environ.get('POSTGRES_USER', 'postgres'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'drillquiz'),
            'HOST': os.environ.get('POSTGRES_HOST', 'db'),
            'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Los_Angeles'
USE_I18N = True
USE_TZ = True

# 다국어 지원 설정
LANGUAGES = [
    ('ko', '한국어'),
    ('en', 'English'),
    ('es', 'Español'),
    ('zh', '中文'),
    ('ja', '日本語'),
]

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

# 언어 감지 미들웨어는 MIDDLEWARE 리스트에 이미 추가됨

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Static files directories (존재하는 디렉토리만 추가)
STATICFILES_DIRS = []
static_dirs = [
    os.path.join(BASE_DIR, 'static'),
    os.path.join(BASE_DIR, 'public'),
]

for static_dir in static_dirs:
    if os.path.exists(static_dir):
        STATICFILES_DIRS.append(static_dir)

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# MinIO Storage Configuration
USE_MINIO = get_config('USE_MINIO', default='False', cast=bool)

# MinIO 설정 디버깅 로그
print(f"=== MinIO 설정 디버깅 ===")
print(f"USE_MINIO: {USE_MINIO}")
print(f"MINIO_ACCESS_KEY: {get_config('MINIO_ACCESS_KEY', default='NOT_SET')}")
print(f"MINIO_SECRET_KEY: {get_config('MINIO_SECRET_KEY', default='NOT_SET')[:10]}..." if get_config('MINIO_SECRET_KEY', default='') else 'NOT_SET')
print(f"MINIO_BUCKET_NAME: {get_config('MINIO_BUCKET_NAME', default='NOT_SET')}")
print(f"MINIO_ENDPOINT: {get_config('MINIO_ENDPOINT', default='NOT_SET')}")

# 모든 환경 변수 확인 (디버깅용)
print(f"=== 모든 환경 변수 확인 ===")
for key, value in os.environ.items():
    if 'MINIO' in key:
        print(f"{key}: {value}")

if USE_MINIO:
    # MinIO S3 Storage Settings
    DEFAULT_FILE_STORAGE = 'quiz.storage.MinIOStorage'
    
    # MinIO Configuration
    AWS_ACCESS_KEY_ID = get_config('MINIO_ACCESS_KEY', default='')
    AWS_SECRET_ACCESS_KEY = get_config('MINIO_SECRET_KEY', default='')
    AWS_STORAGE_BUCKET_NAME = get_config('MINIO_BUCKET_NAME', default='drillquiz')
    # MinIO 엔드포인트 설정 - 환경 변수에서 가져오거나 기본값 사용
    minio_endpoint = get_config('MINIO_ENDPOINT', default='http://minio.devops.svc.cluster.local:9000')
    
    # ConfigMap에 설정된 MINIO_ENDPOINT를 우선 사용
    AWS_S3_ENDPOINT_URL = minio_endpoint
    print(f"MinIO ConfigMap 엔드포인트 사용: {AWS_S3_ENDPOINT_URL}")
    
    # MinIO 설정 검증
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        print(f"⚠️  MinIO 인증 정보가 누락되었습니다. 로컬 스토리지로 폴백합니다.")
        USE_MINIO = False
    else:
        print(f"✅ MinIO 설정이 완료되었습니다.")
        print(f"   - Bucket: {AWS_STORAGE_BUCKET_NAME}")
        print(f"   - Endpoint: {AWS_S3_ENDPOINT_URL}")
        print(f"   - Access Key: {AWS_ACCESS_KEY_ID[:10]}...")
    
    # S3/MinIO specific settings
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None
    AWS_S3_VERIFY = False  # MinIO에서는 SSL 인증서 검증 비활성화
    AWS_QUERYSTRING_AUTH = False
    
    # Media files will be served from MinIO
    MEDIA_URL = f'{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/'
else:
    # Local file storage (development)
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS settings
CORS_ALLOW_CREDENTIALS = True

# 추가 CORS 설정 - 와일드카드 도메인 허용
CORS_ALLOW_ALL_ORIGINS = False  # 보안을 위해 False로 설정

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
CORS_ALLOWED_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# 추가 CORS 설정
CORS_EXPOSE_HEADERS = [
    'x-csrftoken',
    'content-type',
    'content-length',
]

# Google OAuth Configuration
GOOGLE_OAUTH_CLIENT_ID = get_config('GOOGLE_OAUTH_CLIENT_ID', default='195449497097-rf2f22ampv4imqb80fvibhr7oq5oc7km.apps.googleusercontent.com')
GOOGLE_OAUTH_CLIENT_SECRET = get_config('GOOGLE_OAUTH_CLIENT_SECRET', default='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')
GOOGLE_OAUTH_REDIRECT_URI = get_config('GOOGLE_OAUTH_REDIRECT_URI', default='http://localhost:8000/api/google-oauth/')

# Apple Sign In Configuration
APPLE_CLIENT_ID = get_config('APPLE_CLIENT_ID', default=None)  # e.g., com.drillquiz.app
APPLE_TEAM_ID = get_config('APPLE_TEAM_ID', default=None)  # Apple Developer Team ID


# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'short': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'drillquiz.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'short',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': 'error.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'quiz': {
            'handlers': ['file', 'console', 'error_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'quiz.views': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'quiz.models': {
            'handlers': ['file'],
            'level': 'WARNING',  # 모델 관련 로그는 WARNING 이상만
            'propagate': False,
        },
    },
}

# Cache configuration
# 로컬 환경에서는 기본 로컬 캐시, Kubernetes 환경에서는 Redis 사용
# 
# 주의사항:
# - 2025-08-13 23:16:50에 clear_all_statistics.py로 모든 통계 데이터 삭제 완료
# - Django 캐시도 함께 정리되어 모든 캐시된 데이터가 무효화됨
# - 새로운 데이터가 쌓이면 캐시가 다시 생성됨
#
print(f"=== Redis 캐시 설정 시작 ===")
print(f"현재 환경: {ENVIRONMENT}")

# USE_DOCKER 변수로 로컬 환경 확인
USE_DOCKER = get_config('USE_DOCKER', default='false', cast=bool)
IS_LOCAL = not USE_DOCKER  # 도커를 사용하지 않으면 로컬 환경

print(f"USE_DOCKER: {USE_DOCKER}, IS_LOCAL: {IS_LOCAL}")

# 로컬 환경이면 로컬 Redis 사용, 아니면 프로덕션 Redis 사용
if IS_LOCAL:
    # 로컬 Redis 연결 확인
    local_redis_available = False
    try:
        import redis
        local_redis = redis.from_url('redis://localhost:6379/1')
        local_redis.ping()
        local_redis_available = True
    except Exception as e:
        local_redis_available = False
        print(f"⚠️  로컬 Redis 연결 실패: {e}")
    
    if local_redis_available:
        # 로컬 Redis 사용
        REDIS_ENDPOINT = os.getenv('REDIS_URL', 'redis://localhost:6379/1')
        print(f"✅ 로컬 Redis 사용 (연결 확인됨)")
        
        # 로컬 Redis 캐시 설정
        CACHES = {
            'default': {
                'BACKEND': 'quiz.cache_backend.SafeRedisCache',
                'LOCATION': REDIS_ENDPOINT,
                'OPTIONS': {
                    'CLIENT_CLASS': 'quiz.cache_backend.SafeRedisClient',
                    'CONNECTION_POOL_KWARGS': {
                        'max_connections': 50,
                        'retry_on_timeout': True,
                    },
                    'SOCKET_CONNECT_TIMEOUT': 2,  # 로컬이므로 짧은 타임아웃
                    'SOCKET_TIMEOUT': 2,  # 로컬이므로 짧은 타임아웃
                    'IGNORE_EXCEPTIONS': True,
                    'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
                    'REDIS_CLIENT_KWARGS': {
                        'decode_responses': True,
                        'socket_keepalive': True,
                    },
                    'KEY_FUNCTION': 'django_redis.util.make_key',
                },
                'KEY_PREFIX': f'drillquiz_{ENVIRONMENT}',
                'TIMEOUT': 300,
            }
        }
        
        SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
        SESSION_CACHE_ALIAS = 'default'
        
        print(f"✅ 로컬 Redis 캐시 설정 완료: {REDIS_ENDPOINT}")
    else:
        # 로컬 환경이지만 Redis가 없을 경우 폴백: 로컬 메모리 캐시
        CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'unique-snowflake',
            }
        }
        print(f"⚠️  로컬 메모리 캐시 사용 (Redis 미사용): {ENVIRONMENT} 환경")
        print(f"   Redis를 설치하고 실행하면 서버와 동일한 환경으로 테스트할 수 있습니다.")
elif ENVIRONMENT == 'production' or ENVIRONMENT == 'qa':
    # Kubernetes 환경: Redis Cluster 사용 (Docker 환경에서만)
    # 개발 환경(devops-dev 네임스페이스)은 Redis DB /3 사용, 운영/QA는 /1 사용
    # 현재 네임스페이스 확인 (환경 변수 또는 호스트명으로 판단)
    postgres_host = os.getenv('POSTGRES_HOST', '')
    if 'devops-dev' in postgres_host:
        # 개발 환경: Redis DB /3 사용 (운영과 분리)
        REDIS_ENDPOINT = os.getenv('REDIS_ENDPOINT', 'redis://redis-cluster-drillquiz-master.devops.svc.cluster.local:6379/3')
    else:
        # 운영/QA 환경: Redis DB /1 사용
        REDIS_ENDPOINT = os.getenv('REDIS_ENDPOINT', 'redis://redis-cluster-drillquiz-master.devops.svc.cluster.local:6379/1')
    CACHES = {
        'default': {
            'BACKEND': 'quiz.cache_backend.SafeRedisCache',
            'LOCATION': REDIS_ENDPOINT,
            'OPTIONS': {
                'CLIENT_CLASS': 'quiz.cache_backend.SafeRedisClient',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 50,
                    'retry_on_timeout': True,
                },
                'SOCKET_CONNECT_TIMEOUT': 5,
                'SOCKET_TIMEOUT': 5,
                # FLUSHDB 명령어 사용 방지
                'IGNORE_EXCEPTIONS': True,
                'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
                # Redis 명령어 제한 설정
                'REDIS_CLIENT_KWARGS': {
                    'decode_responses': True,
                    'socket_keepalive': True,
                },
                # 캐시 무효화 시 개별 키 삭제 사용
                'KEY_FUNCTION': 'django_redis.util.make_key',
            },
            'KEY_PREFIX': f'drillquiz_{ENVIRONMENT}',
            'TIMEOUT': 300,  # 5분 기본 타임아웃
        }
    }

    # 세션 저장소로도 Redis 사용 (선택사항)
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'

    print(f"✅ Redis 캐시 설정 활성화: {ENVIRONMENT} 환경")
    print(f"🔗 Redis Endpoint: {REDIS_ENDPOINT}")
    print(f"🔑 Key Prefix: drillquiz_{ENVIRONMENT}")
    print(f"⏱️  Cache Timeout: 300초 (5분)")
    print(f"🔗 Session Engine: Redis Cache")
else:
    # 로컬 개발 환경: 로컬 Redis 사용 (서버와 동일한 환경)
    REDIS_ENDPOINT = os.getenv('REDIS_URL', 'redis://localhost:6379/1')
    
    # Redis 연결 테스트
    try:
        import redis
        r = redis.from_url(REDIS_ENDPOINT)
        r.ping()
        redis_available = True
    except Exception as e:
        redis_available = False
        print(f"⚠️  로컬 Redis 연결 실패: {e}")
        print(f"   Redis를 설치하고 실행해주세요: brew install redis && brew services start redis")
    
    if redis_available:
        # 로컬 Redis 사용 (프로덕션과 동일한 SafeRedisCache 사용)
        CACHES = {
            'default': {
                'BACKEND': 'quiz.cache_backend.SafeRedisCache',
                'LOCATION': REDIS_ENDPOINT,
                'OPTIONS': {
                    'CLIENT_CLASS': 'quiz.cache_backend.SafeRedisClient',
                    'CONNECTION_POOL_KWARGS': {
                        'max_connections': 50,
                        'retry_on_timeout': True,
                    },
                    'SOCKET_CONNECT_TIMEOUT': 5,
                    'SOCKET_TIMEOUT': 5,
                    # FLUSHDB 명령어 사용 방지
                    'IGNORE_EXCEPTIONS': True,
                    'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
                    # Redis 명령어 제한 설정
                    'REDIS_CLIENT_KWARGS': {
                        'decode_responses': True,
                        'socket_keepalive': True,
                    },
                    # 캐시 무효화 시 개별 키 삭제 사용
                    'KEY_FUNCTION': 'django_redis.util.make_key',
                },
                'KEY_PREFIX': f'drillquiz_{ENVIRONMENT}',
                'TIMEOUT': 300,  # 5분 기본 타임아웃
            }
        }
        
        # 세션 저장소로도 Redis 사용
        SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
        SESSION_CACHE_ALIAS = 'default'
        
        print(f"✅ 로컬 Redis 캐시 설정 활성화: {ENVIRONMENT} 환경")
        print(f"🔗 Redis Endpoint: {REDIS_ENDPOINT}")
        print(f"🔑 Key Prefix: drillquiz_{ENVIRONMENT}")
        print(f"⏱️  Cache Timeout: 300초 (5분)")
        print(f"🔗 Session Engine: Redis Cache")
    else:
        # Redis가 없을 경우 폴백: 로컬 메모리 캐시
        CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'unique-snowflake',
            }
        }
        print(f"⚠️  로컬 메모리 캐시 사용 (Redis 미사용): {ENVIRONMENT} 환경")
        print(f"   Redis를 설치하고 실행하면 서버와 동일한 환경으로 테스트할 수 있습니다.")

print(f"=== Redis 캐시 설정 완료 ===")

# Celery Configuration
# Redis를 브로커와 결과 백엔드로 사용
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', None)
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', None)

# 환경 변수로 명시적으로 설정된 경우 우선 사용
if CELERY_BROKER_URL and CELERY_RESULT_BACKEND:
    # 이미 설정되어 있으면 그대로 사용
    print(f"✅ 환경 변수에서 Celery 브로커 설정 사용: {CELERY_BROKER_URL}")
elif ENVIRONMENT == 'production' or ENVIRONMENT == 'qa':
    # Kubernetes 환경: Redis Cluster 사용
    # 단, 로컬에서 실행 중인 경우(USE_DOCKER=false) 로컬 Redis 사용
    USE_DOCKER = os.environ.get('USE_DOCKER', 'false').lower() == 'true'
    
    if USE_DOCKER:
        # Docker 환경: 프로덕션 Redis 사용
        REDIS_ENDPOINT = os.getenv('REDIS_ENDPOINT', 'redis://redis-cluster-drillquiz-master.devops.svc.cluster.local:6379/1')
        if not CELERY_BROKER_URL:
            # Celery 브로커는 별도 DB 사용 (기본값: DB 0)
            CELERY_BROKER_URL = REDIS_ENDPOINT.replace('/1', '/0')
        if not CELERY_RESULT_BACKEND:
            # Celery 결과 백엔드는 별도 DB 사용 (기본값: DB 2)
            CELERY_RESULT_BACKEND = REDIS_ENDPOINT.replace('/1', '/2')
        print(f"✅ 프로덕션 Redis를 Celery 브로커로 사용: {CELERY_BROKER_URL}")
    else:
        # 로컬 실행: 로컬 Redis 사용
        local_redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
        if not CELERY_BROKER_URL:
            CELERY_BROKER_URL = f"{local_redis_url}/0"
        if not CELERY_RESULT_BACKEND:
            CELERY_RESULT_BACKEND = f"{local_redis_url}/2"
        print(f"✅ 로컬 Redis를 Celery 브로커로 사용 (로컬 실행): {CELERY_BROKER_URL}")
else:
    # 로컬 개발 환경: 로컬 Redis 사용 (항상 사용)
    local_redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    
    # 로컬 Redis 연결 확인
    redis_available = False
    try:
        import redis
        # Redis 연결 테스트
        test_redis = redis.from_url(f"{local_redis_url}/0")
        test_redis.ping()
        redis_available = True
    except Exception as e:
        redis_available = False
        print(f"⚠️  로컬 Redis 연결 실패: {e}")
        print(f"   Celery를 사용하려면 Redis를 실행해주세요: brew services start redis")
    
    # 로컬 Redis 사용 (연결 실패해도 설정은 함 - 나중에 연결될 수 있음)
    if not CELERY_BROKER_URL:
        CELERY_BROKER_URL = f"{local_redis_url}/0"
    if not CELERY_RESULT_BACKEND:
        CELERY_RESULT_BACKEND = f"{local_redis_url}/2"
    
    if redis_available:
        print(f"✅ 로컬 Redis를 Celery 브로커로 사용: {CELERY_BROKER_URL}")
    else:
        print(f"⚠️  로컬 Redis 미연결 - Celery 브로커 설정: {CELERY_BROKER_URL}")
        print(f"   Redis를 실행하면 자동으로 연결됩니다: brew services start redis")

# Celery 설정
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

# Celery 태스크 설정
CELERY_TASK_ACKS_LATE = True  # 태스크 완료 후 ACK
CELERY_TASK_REJECT_ON_WORKER_LOST = True  # 워커 손실 시 태스크 거부
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # 워커가 한 번에 가져올 태스크 수
CELERY_TASK_TRACK_STARTED = True  # 태스크 시작 추적

# Celery 결과 백엔드 설정
CELERY_RESULT_BACKEND_ALWAYS_RETRY = True
CELERY_RESULT_BACKEND_MAX_RETRIES = 10
CELERY_RESULT_EXPIRES = 3600  # 결과 만료 시간 (1시간)

# Celery 로깅
CELERY_TASK_LOG_FORMAT = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
CELERY_WORKER_LOG_FORMAT = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
CELERY_WORKER_TASK_LOG_FORMAT = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'

print(f"=== Celery 설정 완료 ===")
print(f"🔗 Broker URL: {CELERY_BROKER_URL}")
print(f"🔗 Result Backend: {CELERY_RESULT_BACKEND}")
print(f"⏱️  Timezone: {CELERY_TIMEZONE}")