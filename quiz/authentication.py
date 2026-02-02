from rest_framework import authentication
from rest_framework import exceptions
from django.conf import settings
import os


class APIKeyAuthentication(authentication.BaseAuthentication):
    """
    API Key 인증 클래스
    Authorization 헤더에서 API Key를 확인합니다.
    """
    
    def authenticate(self, request):
        # Authorization 헤더에서 API Key 추출
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return None
            
        api_key = auth_header.split(' ')[1]
        
        # 환경 변수에서 API Key 확인
        expected_api_key = os.environ.get('API_KEY', 'drillquiz-api-key-2024')
        
        if api_key == expected_api_key:
            # 인증 성공 시 AnonymousUser 반환 (API Key만으로는 특정 사용자 식별 불가)
            from django.contrib.auth.models import AnonymousUser
            return (AnonymousUser(), None)
        else:
            raise exceptions.AuthenticationFailed('Invalid API Key')
    
    def authenticate_header(self, request):
        return 'Bearer realm="API"' 