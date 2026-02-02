"""
API 엔드포인트 로깅 미들웨어
테스트 환경에서 API 호출을 추적하고 로깅합니다.
"""

import logging
import time
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger(__name__)

class APILoggingMiddleware(MiddlewareMixin):
    """
    API 엔드포인트 호출을 로깅하는 미들웨어
    """
    
    def process_request(self, request):
        """요청 처리 전 로깅"""
        if self._should_log_request(request):
            request._api_start_time = time.time()
            logger.info(f"🌐 API Request: {request.method} {request.path}")
            logger.info(f"   Headers: {dict(request.headers)}")
            if hasattr(request, 'data') and request.data:
                logger.info(f"   Data: {request.data}")
    
    def process_response(self, request, response):
        """응답 처리 후 로깅"""
        if self._should_log_request(request):
            duration = getattr(request, '_api_start_time', None)
            if duration:
                duration = time.time() - duration
                logger.info(f"🌐 API Response: {request.method} {request.path} -> {response.status_code} ({duration:.3f}s)")
            else:
                logger.info(f"🌐 API Response: {request.method} {request.path} -> {response.status_code}")
            
            # 에러 응답의 경우 상세 로깅
            if response.status_code >= 400:
                logger.error(f"   Error Response: {response.content.decode('utf-8', errors='ignore')[:500]}")
        
        return response
    
    def _should_log_request(self, request):
        """로깅할 요청인지 확인"""
        # API 엔드포인트만 로깅
        if not request.path.startswith('/api/'):
            return False
        
        # 테스트 환경에서만 로깅
        if not (settings.DEBUG or getattr(settings, 'TESTING', False)):
            return False
        
        # 특정 경로 제외 (너무 많은 로그 방지)
        exclude_paths = ['/api/health/', '/api/status/']
        if any(request.path.startswith(path) for path in exclude_paths):
            return False
        
        return True
