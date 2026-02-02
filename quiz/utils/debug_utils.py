import os
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def log_environment_info():
    """환경 변수와 설정 값들을 로깅하는 유틸리티 함수"""
    logger.info("🔍 [DEBUG_UTILS] 환경 정보 로깅 시작")
    
    # 기본 환경 정보
    logger.info(f"  - ENVIRONMENT: {os.getenv('ENVIRONMENT', 'Not set')}")
    logger.info(f"  - CURRENT_DOMAIN: {os.getenv('CURRENT_DOMAIN', 'Not set')}")
    logger.info(f"  - USE_DOCKER: {os.getenv('USE_DOCKER', 'Not set')}")
    
    # Google OAuth 관련 설정
    logger.info("  - Google OAuth 설정:")
    logger.info(f"    * GOOGLE_OAUTH_CLIENT_ID: {getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', 'Not set')[:20]}...")
    logger.info(f"    * GOOGLE_OAUTH_CLIENT_SECRET: {'Set' if hasattr(settings, 'GOOGLE_OAUTH_CLIENT_SECRET') and settings.GOOGLE_OAUTH_CLIENT_SECRET else 'Not set'}")
    logger.info(f"    * GOOGLE_OAUTH_REDIRECT_URI: {getattr(settings, 'GOOGLE_OAUTH_REDIRECT_URI', 'Not set')}")
    
    # 프론트엔드 관련 설정
    logger.info("  - 프론트엔드 설정:")
    logger.info(f"    * VUE_APP_GOOGLE_CLIENT_ID: {os.getenv('VUE_APP_GOOGLE_CLIENT_ID', 'Not set')[:20]}...")
    logger.info(f"    * VUE_APP_GOOGLE_REDIRECT_URI: {os.getenv('VUE_APP_GOOGLE_REDIRECT_URI', 'Not set')}")
    
    # CORS 및 보안 설정
    logger.info("  - CORS 및 보안 설정:")
    logger.info(f"    * ALLOWED_HOSTS: {os.getenv('ALLOWED_HOSTS', 'Not set')}")
    logger.info(f"    * CORS_ALLOWED_ORIGINS: {os.getenv('CORS_ALLOWED_ORIGINS', 'Not set')}")
    
    # 데이터베이스 설정
    logger.info("  - 데이터베이스 설정:")
    logger.info(f"    * POSTGRES_HOST: {os.getenv('POSTGRES_HOST', 'Not set')}")
    logger.info(f"    * POSTGRES_PORT: {os.getenv('POSTGRES_PORT', 'Not set')}")
    logger.info(f"    * POSTGRES_DB: {os.getenv('POSTGRES_DB', 'Not set')}")
    
    # 미니오 설정
    logger.info("  - 미니오 설정:")
    logger.info(f"    * MINIO_ENDPOINT: {os.getenv('MINIO_ENDPOINT', 'Not set')}")
    logger.info(f"    * MINIO_BUCKET_NAME: {os.getenv('MINIO_BUCKET_NAME', 'Not set')}")
    logger.info(f"    * USE_MINIO: {os.getenv('USE_MINIO', 'Not set')}")
    
    logger.info("✅ [DEBUG_UTILS] 환경 정보 로깅 완료")

def log_request_info(request):
    """요청 정보를 로깅하는 유틸리티 함수"""
    logger.info("🔍 [DEBUG_UTILS] 요청 정보 로깅")
    logger.info(f"  - 요청 도메인: {request.get_host()}")
    logger.info(f"  - 요청 스키마: {request.scheme}")
    logger.info(f"  - 요청 URL: {request.build_absolute_uri()}")
    logger.info(f"  - 요청 메서드: {request.method}")
    logger.info(f"  - User-Agent: {request.META.get('HTTP_USER_AGENT', 'Not set')}")
    logger.info(f"  - X-Forwarded-For: {request.META.get('HTTP_X_FORWARDED_FOR', 'Not set')}")
    logger.info(f"  - X-Real-IP: {request.META.get('HTTP_X_REAL_IP', 'Not set')}")
    logger.info(f"  - Referer: {request.META.get('HTTP_REFERER', 'Not set')}")
    
    # 쿼리 파라미터
    if request.GET:
        logger.info(f"  - GET 파라미터: {dict(request.GET)}")
    
    # POST 데이터 (민감한 정보 제외)
    if request.method == 'POST' and hasattr(request, 'body'):
        try:
            import json
            data = json.loads(request.body)
            # 민감한 정보 마스킹
            safe_data = {}
            for key, value in data.items():
                if 'password' in key.lower() or 'secret' in key.lower() or 'token' in key.lower():
                    safe_data[key] = '***MASKED***'
                else:
                    safe_data[key] = value
            logger.info(f"  - POST 데이터: {safe_data}")
        except:
            logger.info(f"  - POST 데이터: {request.body[:200]}... (JSON 파싱 실패)")
    
    logger.info("✅ [DEBUG_UTILS] 요청 정보 로깅 완료")
