from django.utils import translation
from django.conf import settings
from .models import UserProfile

class UserLanguageMiddleware:
    """사용자 프로필에서 언어 설정을 가져와서 적용하는 미들웨어"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 인증된 사용자인 경우 프로필에서 언어 설정 가져오기
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                profile = request.user.profile
                from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
                if profile.language in SUPPORTED_LANGUAGES:
                    # 사용자 언어 설정을 세션에 저장
                    request.session[settings.LANGUAGE_COOKIE_NAME] = profile.language
                    # 현재 요청에 언어 설정 적용
                    translation.activate(profile.language)
                    request.LANGUAGE_CODE = profile.language
            except UserProfile.DoesNotExist:
                pass
            except Exception as e:
                print(f"언어 설정 오류: {e}")
        
        response = self.get_response(request)
        return response 