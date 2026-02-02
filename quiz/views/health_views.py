from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from django.core.cache import cache
import logging
from rest_framework.permissions import AllowAny

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Kubernetes readinessProbe를 위한 health check 엔드포인트
    """
    try:
        # 1. 데이터베이스 연결 확인
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_healthy = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_healthy = False
    
    # 2. 캐시 연결 확인 (Redis가 설정된 경우)
    cache_healthy = True
    try:
        cache.set('health_check', 'ok', 10)
        cache_value = cache.get('health_check')
        if cache_value != 'ok':
            cache_healthy = False
    except Exception as e:
        logger.warning(f"Cache health check failed (this is normal if Redis is not configured): {e}")
        # Redis가 설정되지 않은 경우는 정상으로 처리
        cache_healthy = True
    
    # 3. 전체 상태 확인
    is_healthy = db_healthy and cache_healthy
    
    if is_healthy:
        return Response({
            'status': 'healthy',
            'database': 'ok',
            'cache': 'ok' if cache_healthy else 'not_configured'
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'status': 'unhealthy',
            'database': 'ok' if db_healthy else 'error',
            'cache': 'ok' if cache_healthy else 'error'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE) 