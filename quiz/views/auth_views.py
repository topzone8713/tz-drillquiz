import json
import logging
import os
import requests
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import transaction
from django.conf import settings
from django.middleware.csrf import get_token
from django.http import JsonResponse, HttpResponseRedirect
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from django.utils.decorators import method_decorator
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from quiz.models import UserProfile
from quiz.message_ko import get_message as get_ko_message
from quiz.message_en import get_message as get_en_message
from quiz.utils.url_utils import get_frontend_login_url, get_frontend_url
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from quiz.utils.multilingual_utils import BASE_LANGUAGE, LANGUAGE_KO, LANGUAGE_ES, LANGUAGE_ZH, LANGUAGE_JA

logger = logging.getLogger(__name__)


def get_message_by_language(language, key, default=None):
    """언어에 따라 메시지를 반환합니다."""
    if language == LANGUAGE_KO:
        return get_ko_message(key, default or key)
    elif language == LANGUAGE_ES:
        from quiz.message_es import get_message as get_es_message
        return get_es_message(key, default or key)
    elif language == LANGUAGE_ZH:
        from quiz.message_zh import get_message as get_zh_message
        return get_zh_message(key, default or key)
    elif language == LANGUAGE_JA:
        from quiz.message_ja import get_message as get_ja_message
        return get_ja_message(key, default or key)
    else:
        return get_en_message(key, default or key)


def build_user_payload(user):
    try:
        user_profile = UserProfile.objects.get(user=user)
        language = user_profile.language
        role = getattr(user_profile, 'role', None)
        date_of_birth = getattr(user_profile, 'date_of_birth', None)
    except UserProfile.DoesNotExist:
        language = BASE_LANGUAGE
        role = None
        date_of_birth = None

    # 나이 등급 계산
    from quiz.utils.user_utils import calculate_age_rating
    age_rating = calculate_age_rating(date_of_birth)

    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'language': language,
        'is_superuser': user.is_superuser,
        'is_staff': user.is_staff,
        'role': role,
        'age_rating': age_rating,
    }


def issue_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    access_token = refresh.access_token
    access_token['username'] = user.username
    access_token['email'] = user.email
    access_token['user_id'] = user.id  # user_id도 명시적으로 추가
    
    # UserProfile의 role과 language 정보 추가
    try:
        from quiz.models import UserProfile
        profile = UserProfile.objects.get(user=user)
        access_token['role'] = profile.role if profile.role else 'user_role'
        access_token['language'] = profile.language if profile.language else BASE_LANGUAGE
    except UserProfile.DoesNotExist:
        access_token['role'] = 'user_role'
        access_token['language'] = BASE_LANGUAGE
    
    return {
        'access': str(access_token),
        'refresh': str(refresh),
        'access_expires_in': int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
        'refresh_expires_in': int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
        'token_type': 'Bearer',
    }


@api_view(['GET'])
@permission_classes([AllowAny])
def get_csrf_token(request):
    """CSRF 토큰을 반환합니다."""
    print(f"=== CSRF 토큰 요청 시작 ===")
    print(f"요청 도메인: {request.get_host()}")
    print(f"요청 경로: {request.path}")
    print(f"요청 메서드: {request.method}")
    print(f"요청 헤더: {dict(request.headers)}")
    print(f"기존 쿠키: {request.COOKIES}")

    try:
        csrf_token = get_token(request)
        logger.info(f"CSRF 토큰 생성 성공: {csrf_token[:10]}...")
        
        # 응답 생성
        response = Response({'csrfToken': csrf_token})
        
        # CORS 헤더 명시적 추가
        origin = request.META.get('HTTP_ORIGIN')
        print(f"🔍 HTTP_ORIGIN: {origin}")

        if origin:
            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Credentials"] = "true"
            response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Content-Type, X-CSRFToken, Authorization"
            print(f"✅ CORS 헤더 추가됨: {origin}")
        else:
            print(f"⚠️  HTTP_ORIGIN이 없음")
        
        # 쿠키 설정 (환경에 따라 다르게)
        from django.conf import settings
        cookie_kwargs = {
            'max_age': 31449600,  # 1년
            'samesite': 'Lax',
            'httponly': False  # JavaScript에서 읽을 수 있도록
        }
        
        # 환경에 따른 CSRF 쿠키 설정
        from django.conf import settings
        if settings.ENVIRONMENT == 'production':
            # 프로덕션 환경: 서브도메인 공유, HTTPS
            cookie_kwargs.update({
                'domain': '.drillquiz.com',
                'secure': True
            })
        else:
            # 개발 환경: localhost, HTTP 허용
            cookie_kwargs.update({
                'domain': None,  # localhost에서는 도메인 설정 안함
                'secure': False  # HTTP 허용
            })
        print(f"✅ 환경별 CSRF 쿠키 설정: {cookie_kwargs}")

        response.set_cookie('csrftoken', csrf_token, **cookie_kwargs)
        
        return response
    except Exception as e:
        logger.error(f"CSRF 토큰 생성 실패: {str(e)}")
        # 오류가 발생해도 빈 토큰 반환
        return Response({'csrfToken': ''})

@api_view(['POST'])
@permission_classes([AllowAny])
def test_csrf(request):
    """CSRF 토큰이 제대로 작동하는지 테스트합니다."""
    logger.debug("test_csrf 호출됨")
    logger.debug(f"CSRF Token in header: {request.META.get('HTTP_X_CSRFTOKEN', 'Not found')}")
    logger.debug(f"CSRF Token in cookies: {request.COOKIES.get('csrftoken', 'Not found')}")
    
    response = Response({'message': 'CSRF 토큰이 정상적으로 작동합니다.'})
    
    # CORS 헤더 명시적 추가
    origin = request.META.get('HTTP_ORIGIN')
    if origin:
        response["Access-Control-Allow-Origin"] = origin
        response["Access-Control-Allow-Credentials"] = "true"
        response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, X-CSRFToken, Authorization"
        logger.debug(f"✅ test_csrf CORS 헤더 추가됨: {origin}")
    
    return response

@api_view(['POST'])
def logout_view(request):
    """로그아웃 처리"""
    from django.contrib.auth import logout
    from django.middleware.csrf import get_token
    from django.core.cache import cache

    print(f"[logout_view] ===== 로그아웃 요청 시작 =====")
    print(f"[logout_view] 로그아웃 전 - User: {request.user}")
    print(f"[logout_view] 로그아웃 전 - Is authenticated: {request.user.is_authenticated}")
    print(f"[logout_view] 로그아웃 전 - Session ID: {request.session.session_key}")
    print(f"[logout_view] 로그아웃 전 - Cookies: {request.COOKIES}")
    
    logout(request)
    
    # 세션 완전 삭제
    request.session.flush()
    
    # 캐시 무효화는 비동기로 처리하거나 간소화 (성능 개선)
    # 개발 환경에서는 캐시 무효화를 건너뛰어 응답 속도 개선
    from django.conf import settings
    if hasattr(settings, 'ENVIRONMENT') and settings.ENVIRONMENT == 'production':
        # 프로덕션 환경에서만 캐시 무효화 수행 (비동기로 처리 가능)
        try:
            # Redis의 경우 delete_pattern 지원
            if hasattr(cache, 'delete_pattern'):
                cache.delete_pattern("exams_*")
                cache.delete_pattern("exam_results_*")
                cache.delete_pattern("questions_*")
                cache.delete_pattern("studies_*")
            else:
                # 다른 캐시 백엔드의 경우 개별 키 삭제는 스킵 (성능 향상)
                logger.info("캐시 무효화 스킵 (개별 키 삭제는 성능 저하)")
        except Exception as e:
            logger.error(f"캐시 무효화 중 오류 (무시됨): {e}")
    else:
        # 개발 환경에서는 캐시 무효화 스킵 (응답 속도 향상)
        logger.info("개발 환경 - 캐시 무효화 스킵")
    
    print(f"[logout_view] 로그아웃 후 - User: {request.user}")
    print(f"[logout_view] 로그아웃 후 - Is authenticated: {request.user.is_authenticated}")
    print(f"[logout_view] 로그아웃 후 - Session ID: {request.session.session_key}")
    print(f"[logout_view] ===== 로그아웃 완료 =====")
    
    # CSRF 토큰 재설정을 위한 응답
    response = Response({'message': '로그아웃되었습니다.'})
    
    # CSRF 토큰을 새로 생성하여 쿠키에 설정
    csrf_token = get_token(request)
    response.set_cookie('csrftoken', csrf_token, samesite='Lax', httponly=False)
    
    # 세션 쿠키 삭제 (프로덕션 환경 고려)
    from django.conf import settings
    if settings.ENVIRONMENT == 'production':
        # 프로덕션 환경: 여러 도메인에서 쿠키 삭제
        # 1. 현재 요청 도메인에서 삭제
        current_host = request.get_host()
        if current_host:
            response.delete_cookie('sessionid', domain=current_host, path='/')
            response.delete_cookie('csrftoken', domain=current_host, path='/')
        
        # 2. 서브도메인 공유를 위해 .drillquiz.com 도메인에서도 삭제
        response.delete_cookie('sessionid', domain='.drillquiz.com', path='/')
        response.delete_cookie('csrftoken', domain='.drillquiz.com', path='/')
        
        # 3. X-Forwarded-Host가 있으면 해당 도메인에서도 삭제
        forwarded_host = request.META.get('HTTP_X_FORWARDED_HOST')
        if forwarded_host:
            forwarded_domain = forwarded_host.split(',')[0].strip()
            response.delete_cookie('sessionid', domain=forwarded_domain, path='/')
            response.delete_cookie('csrftoken', domain=forwarded_domain, path='/')
        
        # 4. 추가적인 쿠키 삭제 (만료 시간을 과거로 설정)
        response.set_cookie('sessionid', '', max_age=0, domain='.drillquiz.com', path='/', secure=True, samesite='Lax')
        response.set_cookie('csrftoken', '', max_age=0, domain='.drillquiz.com', path='/', secure=True, samesite='Lax')
        
        # 5. 현재 도메인에서도 만료 시간을 과거로 설정
        if current_host:
            response.set_cookie('sessionid', '', max_age=0, domain=current_host, path='/', secure=True, samesite='Lax')
            response.set_cookie('csrftoken', '', max_age=0, domain=current_host, path='/', secure=True, samesite='Lax')
    else:
        # 개발 환경: 도메인 지정 없이 삭제
        response.delete_cookie('sessionid', path='/')
        response.delete_cookie('csrftoken', path='/')
        # 추가적인 쿠키 삭제 (만료 시간을 과거로 설정)
        response.set_cookie('sessionid', '', max_age=0, path='/', samesite='Lax')
        response.set_cookie('csrftoken', '', max_age=0, path='/', samesite='Lax')
    
    return response


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """사용자 등록 API"""
    try:
        data = request.data
        logger.info(f"사용자 등록 요청: {data.get('id', 'N/A')}")
        
        # 소셜 로그인 정보 확인 (세션 또는 요청 데이터에서)
        social_auth = request.session.get('social_auth') or {}
        social_provider = data.get('social_provider') or social_auth.get('provider')
        is_social_registration = bool(social_provider)

        # 필수 필드 검증 (소셜 로그인인 경우 비밀번호 불필요)
        if not data.get('id') or not data.get('name'):
            logger.warning(
                f"필수 필드 누락: id={data.get('id')}, name={data.get('name')}")
            return JsonResponse({
                'success': False,
                'detail': '아이디와 이름은 필수입니다.'
            }, status=400)
        
        # 소셜 로그인이 아닌 경우 비밀번호 필수
        if not is_social_registration and not data.get('password'):
            logger.warning(f"비밀번호 누락 (일반 가입): {data.get('id')}")
            return JsonResponse({
                'success': False,
                'detail': '비밀번호는 필수입니다.'
            }, status=400)

        # 사용자명 중복 확인
        if User.objects.filter(username=data['id']).exists():
            logger.warning(f"사용자명 중복: {data['id']}")
            return JsonResponse({
                'success': False,
                'detail': '이미 사용 중인 아이디입니다.'
            }, status=400)

        # 이메일 중복 확인 (이메일이 제공된 경우에만)
        email = data.get('email', '').strip()
        if not email and social_auth.get('email'):
            email = social_auth.get('email', '').strip()
        
        if email and User.objects.filter(email__iexact=email).exists():
            return JsonResponse({
                'success': False,
                'detail': '이미 사용 중인 이메일입니다.'
            }, status=400)
        
        # 소셜 로그인인 경우 이메일 검증
        if is_social_registration:
            # 세션에서 소셜 로그인 정보 확인
            if social_provider == 'apple':
                # Apple 로그인인 경우 identity_token 검증
                identity_token = social_auth.get('identity_token')
                if identity_token:
                    try:
                        apple_data = verify_apple_identity_token(identity_token)
                        if apple_data.get('email') and apple_data.get('email') != email:
                            logger.warning(f"이메일 불일치: 세션={email}, 토큰={apple_data.get('email')}")
                            email = apple_data.get('email') or email
                    except Exception as e:
                        logger.warning(f"Apple Identity Token 검증 실패 (무시): {e}")
            
            # 소셜 로그인 이메일이 없으면 에러
            if not email:
                return JsonResponse({
                    'success': False,
                    'detail': '소셜 로그인 이메일 정보가 없습니다.'
                }, status=400)

        # 사용자 생성 (소셜 로그인인 경우 비밀번호 없음)
        user = User.objects.create_user(
            username=data['id'],
            email=email if email else '',  # 이메일이 없으면 빈 문자열
            first_name=data['name'],
            password=data.get('password') if not is_social_registration else None  # 소셜 로그인은 비밀번호 없음
        )

        # UserProfile 생성
        # 언어 설정: 요청에서 전달받은 언어 또는 기본값
        from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES, BASE_LANGUAGE
        preferred_language = data.get('language', BASE_LANGUAGE)
        logger.info(f"회원가입 언어 설정: 요청된 언어={data.get('language')}, 최종 언어={preferred_language}")
        if preferred_language not in SUPPORTED_LANGUAGES:
            preferred_language = BASE_LANGUAGE  # 유효하지 않은 언어는 기본 언어로 설정
            logger.warning(f"유효하지 않은 언어 설정: {data.get('language')}, 기본값 '{BASE_LANGUAGE}' 사용")
        
        # 생년월일 처리
        date_of_birth = None
        date_of_birth_data = data.get('dateOfBirth') or data.get('date_of_birth')
        if date_of_birth_data:
            try:
                # 프론트엔드에서 year, month, day로 전송하는 경우
                if isinstance(date_of_birth_data, dict):
                    year = date_of_birth_data.get('year')
                    month = date_of_birth_data.get('month')
                    day = date_of_birth_data.get('day')
                    if year and month and day:
                        from datetime import date
                        date_of_birth = date(int(year), int(month), int(day))
                        logger.info(f"생년월일 파싱 성공: {date_of_birth}")
                # 또는 YYYY-MM-DD 형식으로 전송하는 경우
                elif isinstance(date_of_birth_data, str):
                    from datetime import datetime
                    date_of_birth = datetime.strptime(date_of_birth_data, '%Y-%m-%d').date()
                    logger.info(f"생년월일 파싱 성공 (문자열): {date_of_birth}")
            except (ValueError, TypeError, KeyError) as e:
                logger.warning(f"생년월일 파싱 실패: {e}, 데이터: {date_of_birth_data}")
            
        user_profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'language': preferred_language,  # 사용자가 선택한 언어 또는 기본값
                'email_verified': True if (is_social_registration and email) else (False if email else True),  # 소셜 로그인은 이메일 인증됨
                'retention_cleanup_enabled': True,
                'random_exam_email_enabled': True,
                'date_of_birth': date_of_birth
            }
        )
        
        # 기존 프로필이 있는 경우 date_of_birth 업데이트
        if not created and date_of_birth:
            user_profile.date_of_birth = date_of_birth
            user_profile.save(update_fields=['date_of_birth'])
            logger.info(f"기존 프로필에 생년월일 업데이트: {date_of_birth}")
        
        # 소셜 로그인인 경우 세션 정리
        if is_social_registration and 'social_auth' in request.session:
            del request.session['social_auth']
            logger.info(f"소셜 로그인 세션 정보 정리 완료: {social_provider}")
        
        # 관심 카테고리 설정 (마이그레이션 후에만 동작)
        interested_category_ids = data.get('interested_categories', [])
        if interested_category_ids:
            from ..models import TagCategory
            from django.db.utils import OperationalError
            try:
                # 유효한 카테고리 ID만 필터링
                valid_categories = TagCategory.objects.filter(
                    id__in=interested_category_ids,
                    is_active=True
                )
                user_profile.interested_categories.set(valid_categories)
                logger.info(f"관심 카테고리 설정 완료: {valid_categories.count()}개")
            except (AttributeError, OperationalError) as e:
                # interested_categories 필드가 아직 마이그레이션되지 않은 경우 무시
                logger.warning(f"관심 카테고리 설정 중 오류 (무시됨): {e}")

        logger.info(f"새 사용자 등록 성공: {data['id']} (사용자 ID: {user.id})")

        tokens = issue_tokens_for_user(user)
        user_payload = build_user_payload(user)

        return JsonResponse({
            'success': True,
            'message': '회원가입이 완료되었습니다.',
            'auto_login': True,
            'user': user_payload,
            'tokens': tokens,
            'access': tokens['access'],
            'refresh': tokens['refresh'],
            'token_type': tokens['token_type'],
            'expires_in': tokens['access_expires_in'],
        }, status=201)

    except Exception as e:
        logger.error(f"사용자 등록 중 오류: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'detail': '회원가입 중 오류가 발생했습니다.'
        }, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """사용자 로그인 API"""
    try:
        data = request.data
        username = data.get('username')
        password = data.get('password')

        logger.info(f"로그인 시도: {username}")

        if not username or not password:
            return JsonResponse({
                'success': False,
                'detail': '아이디와 비밀번호를 입력해주세요.'
            }, status=400)

        # 사용자 인증
        user = authenticate(request, username=username, password=password)

        if user is not None:
            logger.info(f"로그인 성공: {username}")
            tokens = issue_tokens_for_user(user)
            user_payload = build_user_payload(user)

            response_data = {
                'success': True,
                'message': '로그인이 완료되었습니다.',
                'user': user_payload,
                'tokens': tokens,
                'access': tokens['access'],
                'refresh': tokens['refresh'],
                'token_type': tokens['token_type'],
                'expires_in': tokens['access_expires_in'],
            }

            return JsonResponse(response_data)
        else:
            # 로그인 실패
            logger.warning(f"로그인 실패: {username} (잘못된 인증 정보)")
            return JsonResponse({
                'success': False,
                'detail': '아이디 또는 비밀번호가 올바르지 않습니다.'
            }, status=401)

    except Exception as e:
        logger.error(f"로그인 처리 중 오류: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'detail': '로그인 처리 중 오류가 발생했습니다.'
        }, status=500)

def test_redirect_response(request):
    """
    create_redirect_response 함수를 테스트하기 위한 엔드포인트
    개발 환경에서만 사용하세요.
    
    사용법:
    # JSON 응답으로 정보 확인
    curl "http://localhost:8000/api/test-redirect/?url=capacitor://localhost/login?login=success&email=test@example.com"
    
    # 실제 HTML 응답 확인 (format=html 파라미터 추가)
    curl "http://localhost:8000/api/test-redirect/?url=capacitor://localhost/login?login=success&email=test@example.com&format=html"
    
    # 일반 웹 리다이렉트 테스트
    curl -I "http://localhost:8000/api/test-redirect/?url=https://us.drillquiz.com/login?login=success"
    """
    from django.conf import settings
    
    # 프로덕션 환경에서는 비활성화
    if settings.ENVIRONMENT == 'production':
        return JsonResponse({'error': 'This endpoint is disabled in production'}, status=403)
    
    test_url = request.GET.get('url', '')
    if not test_url:
        return JsonResponse({'error': 'url parameter is required'}, status=400)
    
    # format 파라미터 확인 (url 파라미터 파싱 전에)
    format_type = request.GET.get('format', '')
    
    logger.info(f'🔍 [TEST_REDIRECT] test_url: {test_url}')
    logger.info(f'🔍 [TEST_REDIRECT] format_type: {format_type}')
    logger.info(f'🔍 [TEST_REDIRECT] all GET params: {dict(request.GET)}')
    
    # 테스트용 CSRF 토큰 (실제로는 필요 없지만 테스트용)
    csrf_token = get_token(request) if hasattr(request, 'session') else None
    
    response = create_redirect_response(test_url, csrf_token)
    
    # format=html이면 실제 응답 반환
    if format_type == 'html':
        logger.info(f'🔍 [TEST_REDIRECT] Returning HTML response')
        # HttpResponse를 직접 반환 (DRF 데코레이터 없이)
        from django.http import HttpResponse
        if hasattr(response, 'content'):
            return HttpResponse(response.content, content_type=response.get('Content-Type', 'text/html; charset=utf-8'))
        else:
            # HttpResponseRedirect인 경우
            return response
    
    # 응답 내용 확인을 위해 정보 반환 (JSON)
    if hasattr(response, 'content'):
        content_preview = response.content.decode('utf-8')[:500] if response.content else ''
        return JsonResponse({
            'test_url': test_url,
            'response_type': type(response).__name__,
            'status_code': response.status_code,
            'content_type': response.get('Content-Type', ''),
            'content_preview': content_preview,
            'is_capacitor': test_url.startswith('capacitor://') or test_url.startswith('ionic://'),
            'note': 'Add &format=html to get actual HTML response'
        })
    else:
        return JsonResponse({
            'test_url': test_url,
            'response_type': type(response).__name__,
            'status_code': response.status_code,
            'location': response.get('Location', '') if hasattr(response, 'get') else '',
            'is_capacitor': test_url.startswith('capacitor://') or test_url.startswith('ionic://'),
            'note': 'This is a redirect response. Use -I flag with curl to see headers.'
        })


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def get_translations(request):
    """번역 데이터를 반환합니다."""
    try:
        language = request.GET.get('lang', BASE_LANGUAGE)
        
        if language == LANGUAGE_KO:
            from ..message_ko import KOREAN_TRANSLATIONS
            translations = KOREAN_TRANSLATIONS
        elif language == LANGUAGE_ES:
            from ..message_es import SPANISH_TRANSLATIONS
            translations = SPANISH_TRANSLATIONS
        elif language == LANGUAGE_ZH:
            from ..message_zh import CHINESE_TRANSLATIONS
            translations = CHINESE_TRANSLATIONS
        elif language == LANGUAGE_JA:
            from ..message_ja import JAPANESE_TRANSLATIONS
            translations = JAPANESE_TRANSLATIONS
        else:
            from ..message_en import ENGLISH_TRANSLATIONS
            translations = ENGLISH_TRANSLATIONS
        
        return JsonResponse({
            'success': True,
            'translations': translations
        })
    except Exception as e:
        logger.error(f"번역 데이터 로드 실패: {e}")
        return JsonResponse({
            'success': False,
            'error': '번역 데이터를 로드할 수 없습니다.'
        }, status=500)

def add_access_token_to_url(url, access_token):
    """
    URL에 access_token 파라미터를 추가합니다.
    
    Args:
        url (str): 원본 URL
        access_token (str): JWT access token
    
    Returns:
        str: access_token이 추가된 URL
    """
    from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    params['access_token'] = [access_token]
    new_query = urlencode(params, doseq=True)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))


def create_redirect_response(url, csrf_token=None):
    """
    URL에 따라 적절한 리다이렉트 응답을 생성합니다.
    capacitor:// 또는 ionic:// 프로토콜인 경우 HTML 페이지로 리다이렉트합니다.
    
    Args:
        url (str): 리다이렉트할 URL
        csrf_token (str, optional): CSRF 토큰 (쿠키 설정용)
    
    Returns:
        HttpResponse 또는 HttpResponseRedirect
    """
    from django.http import HttpResponse, HttpResponseRedirect
    
    # 모바일 앱의 경우 capacitor:// 프로토콜이므로 직접 리다이렉트 시도
    # ASWebAuthenticationSession을 사용하는 경우 직접 리다이렉트가 작동함
    if url.startswith('capacitor://') or url.startswith('ionic://'):
        # ASWebAuthenticationSession을 사용하는 경우 직접 리다이렉트 시도
        # Django의 HttpResponseRedirect는 커스텀 스킴을 허용하지 않으므로
        # HTML 페이지를 반환하되, JavaScript로 즉시 리다이렉트
        # URL을 JavaScript에서 안전하게 사용하기 위해 이스케이프
        url_escaped = url.replace("'", "\\'").replace('"', '\\"')
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>리다이렉트 중...</title>
        </head>
        <body>
            <script>
                (function() {{
                    // 디버깅: 스크립트 실행 확인
                    console.log('🔍 [1/5] 리다이렉트 스크립트 시작 - 타임스탬프: ' + new Date().toISOString());
                    
                    // 검색 결과 기반 해결책: 단순히 capacitor:// URL로 리다이렉트만 시도
                    // 앱에서 App.addListener('appUrlOpen', ...)로 받아서 Browser.close() 호출
                    var targetUrl = '{url_escaped}';
                    
                    console.log('🔍 [2/5] targetUrl 확인: ' + targetUrl.substring(0, 80) + '...');
                    console.log('🔍 [REDIRECT] capacitor:// URL로 리다이렉트 시도:', targetUrl);
                    
                    // 여러 방법 시도 (Safari View Controller 제약 고려)
                    var methods = [
                        function() {{
                            console.log('🔍 [3/5] 방법 1 시도: window.location.href');
                            // 방법 1: location.href (가장 일반적)
                            window.location.href = targetUrl;
                        }},
                        function() {{
                            console.log('🔍 [4/5] 방법 2 시도: window.location.replace');
                            // 방법 2: location.replace
                            window.location.replace(targetUrl);
                        }},
                        function() {{
                            console.log('🔍 [5/5] 방법 3 시도: iframe');
                            // 방법 3: iframe (일부 환경에서 작동)
                            var iframe = document.createElement('iframe');
                            iframe.style.display = 'none';
                            iframe.src = targetUrl;
                            document.body.appendChild(iframe);
                            setTimeout(function() {{
                                document.body.removeChild(iframe);
                            }}, 1000);
                        }},
                        function() {{
                            console.log('⚠️ 방법 4 시도: window.open');
                            // 방법 4: window.open
                            window.open(targetUrl, '_blank');
                        }}
                    ];
                    
                    // 첫 번째 방법 시도
                    try {{
                        console.log('🔍 [3/5] 첫 번째 방법 실행 시작');
                        methods[0]();
                        console.log('✅ [4/5] 첫 번째 방법 실행 완료');
                    }} catch (e) {{
                        console.error('❌ [4/5] 첫 번째 방법 실패:', e.toString(), '- 다음 방법 시도');
                        console.error('❌ [REDIRECT] 첫 번째 방법 실패, 다음 방법 시도:', e);
                        // 첫 번째 방법이 실패하면 다음 방법 시도
                        setTimeout(function() {{
                            try {{
                                console.log('🔍 [5/5] 두 번째 방법 실행 시작');
                                methods[1]();
                                console.log('✅ 두 번째 방법 실행 완료');
                            }} catch (e2) {{
                                console.error('❌ 두 번째 방법도 실패:', e2.toString());
                                console.error('❌ [REDIRECT] 두 번째 방법도 실패:', e2);
                            }}
                        }}, 100);
                    }}
                    
                    // 최종 확인
                    setTimeout(function() {{
                        console.log('📋 [최종] 리다이렉트 시도 완료 - 만약 앱으로 이동하지 않았다면, 수동으로 Browser를 닫아주세요.');
                    }}, 500);
                }})();
            </script>
            <p>앱으로 이동 중...</p>
        </body>
        </html>
        """
        response = HttpResponse(html_content, content_type='text/html; charset=utf-8')
        
        # 캐시 방지 헤더 추가
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        # 디버깅을 위한 타임스탬프 헤더 추가
        import time
        response['X-Debug-Timestamp'] = str(int(time.time()))
        response['X-Debug-URL'] = url[:100]  # URL 일부만 표시
        
        # CSRF 토큰이 있으면 쿠키 설정
        if csrf_token:
            from django.conf import settings
            if settings.ENVIRONMENT == 'production':
                response.set_cookie('csrftoken', csrf_token, 
                                  domain='.drillquiz.com', 
                                  samesite='Lax', 
                                  httponly=False, 
                                  secure=True)
            else:
                response.set_cookie('csrftoken', csrf_token, 
                                  samesite='Lax', 
                                  httponly=False)
        
        return response
    else:
        response = HttpResponseRedirect(url)
        
        # CSRF 토큰이 있으면 쿠키 설정
        if csrf_token:
            from django.conf import settings
            if settings.ENVIRONMENT == 'production':
                response.set_cookie('csrftoken', csrf_token, 
                                  domain='.drillquiz.com', 
                                  samesite='Lax', 
                                  httponly=False, 
                                  secure=True)
            else:
                response.set_cookie('csrftoken', csrf_token, 
                                  samesite='Lax', 
                                  httponly=False)
        
        return response


@method_decorator(csrf_exempt, name='dispatch')
class GoogleOAuthView(View):
    def get(self, request, *args, **kwargs):
        """OAuth 콜백 처리 - GET 요청으로 리디렉션됨"""
        try:
            # URL 파라미터에서 authorization code 추출
            code = request.GET.get('code')
            error = request.GET.get('error')
            state = request.GET.get('state')

            # state에서 원본 도메인 및 return_url 추출
            original_domain = None
            return_url = None
            if state:
                try:
                    import base64
                    decoded_state = base64.b64decode(state).decode('utf-8')
                    state_data = json.loads(decoded_state)
                    return_url = state_data.get('returnUrl', '')
                    if return_url:
                        from urllib.parse import urlparse
                        parsed_url = urlparse(return_url)
                        original_domain = parsed_url.hostname
                        # 모바일 앱에서 capacitor://localhost인 경우 서버 도메인 사용
                        if original_domain in ['localhost', '127.0.0.1'] or parsed_url.scheme in ['capacitor', 'ionic']:
                            logger.info(f"모바일 앱 감지, 도메인을 us.drillquiz.com으로 변경 (원본: {original_domain})")
                            original_domain = 'us.drillquiz.com'
                        logger.info(f"State에서 추출한 원본 도메인: {original_domain}")
                        logger.info(f"State에서 추출한 return_url: {return_url}")
                except Exception as e:
                    logger.warning(f"State 파싱 실패: {e}")

            if error:
                logger.error(f"Google OAuth 오류: {error}")
                error_url = get_frontend_login_url(success=False, message=error, return_url=return_url)
                return create_redirect_response(error_url)

            if not code:
                logger.error("Authorization code가 없습니다")
                error_url = get_frontend_login_url(success=False, message='no_authorization_code', return_url=return_url)
                return create_redirect_response(error_url)

            # Authorization code로 액세스 토큰 교환
            try:
                # 원본 도메인이 있으면 해당 도메인의 redirect_uri 사용
                if original_domain:
                    redirect_uri = f"https://{original_domain}/api/google-oauth/"
                    logger.info(f"원본 도메인 사용한 redirect_uri: {redirect_uri}")
                else:
                    redirect_uri = settings.GOOGLE_OAUTH_REDIRECT_URI
                    logger.info(f"설정된 redirect_uri 사용: {redirect_uri}")

                token_response = requests.post('https://oauth2.googleapis.com/token', data={
                    'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
                    'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
                    'code': code,
                    'grant_type': 'authorization_code',
                    'redirect_uri': redirect_uri
                })

                if token_response.status_code != 200:
                    logger.error(f"토큰 교환 실패: {token_response.text}")
                    error_url = get_frontend_login_url(success=False, message='token_exchange_failed', original_domain=original_domain, return_url=return_url)
                    return create_redirect_response(error_url)

                token_data = token_response.json()
                access_token = token_data.get('access_token')

                if not access_token:
                    logger.error("액세스 토큰을 가져올 수 없습니다")
                    error_url = get_frontend_login_url(success=False, message='no_access_token', original_domain=original_domain, return_url=return_url)
                    return create_redirect_response(error_url)

                # 액세스 토큰으로 사용자 정보 조회
                user_info_response = requests.get(
                    'https://www.googleapis.com/oauth2/v2/userinfo',
                    headers={'Authorization': f'Bearer {access_token}'}
                )

                if user_info_response.status_code == 200:
                    user_info = user_info_response.json()
                    google_id = user_info.get('id')
                    email = user_info.get('email')
                    name = user_info.get('name', '')

                    # 이름이 없으면 이메일에서 추출
                    if not name and email:
                        name = email.split('@')[0]

                    # 사용자명 생성
                    username = name if name else email.split('@')[0]

                    # 이메일이 필수
                    if not email:
                        error_url = get_frontend_login_url(success=False, message='no_email', original_domain=original_domain, return_url=return_url)
                        return create_redirect_response(error_url)

                    with transaction.atomic():
                        # 기존 사용자 확인 (중복 사용자 처리 포함)
                        existing_users = User.objects.filter(email=email)
                        
                        if existing_users.exists():
                            # 기존 사용자가 있는 경우
                            if existing_users.count() > 1:
                                # 중복 사용자가 있는 경우, 가장 오래된 사용자를 선택
                                user = existing_users.order_by('date_joined').first()
                                logger.warning(f"중복 이메일 사용자 발견: {email}, 사용자 ID {user.id} 선택됨")
                            else:
                                user = existing_users.first()
                            
                            # 기존 사용자 로그인
                            login(request, user)
                            logger.info(f"기존 사용자 Google 로그인 성공: {email} (ID: {user.id})")
                            logger.info(f"🔍 [GOOGLE_OAUTH] 로그인 후 세션 키: {request.session.session_key}")
                            logger.info(f"🔍 [GOOGLE_OAUTH] 로그인 후 인증 여부: {request.user.is_authenticated}")

                            # JWT 토큰 생성 (쿠키가 전달되지 않는 경우를 대비)
                            tokens = issue_tokens_for_user(user)
                            access_token = tokens['access']
                            logger.info(f"🔍 [GOOGLE_OAUTH] JWT 토큰 생성 완료 (access_token 길이: {len(access_token)})")

                            # CSRF 토큰 생성 및 쿠키 설정
                            csrf_token = get_token(request)
                            success_url = get_frontend_login_url(success=True, email=email, original_domain=original_domain, return_url=return_url)
                            success_url = add_access_token_to_url(success_url, access_token)
                            
                            logger.info(f"✅ [GOOGLE_OAUTH] 기존 사용자 로그인 성공, 리다이렉트 URL: {success_url[:200]}...")
                            
                            return create_redirect_response(success_url, csrf_token)
                        else:
                            # 신규 사용자 - 가입 처리 페이지로 리다이렉트
                            logger.info(f"🔍 [GOOGLE_OAUTH] 신규 사용자 감지 (GET) - 가입 처리 페이지로 리다이렉트: {email}")
                            
                            # 소셜 로그인 정보를 세션에 임시 저장 (가입 처리 페이지에서 사용)
                            request.session['social_auth'] = {
                                'provider': 'google',
                                'email': email,
                                'first_name': given_name or '',
                                'last_name': family_name or '',
                                'google_id': google_id,
                                'language': language
                            }
                            
                            # 가입 처리 페이지로 리다이렉트
                            from urllib.parse import urlencode
                            # original_domain이 있으면 해당 도메인 사용, 없으면 기본 도메인 사용
                            if original_domain and original_domain not in ['localhost', '127.0.0.1']:
                                scheme = 'https'
                                base_url = f"{scheme}://{original_domain}"
                            else:
                                base_url = get_frontend_url('')
                            
                            query_params = urlencode({
                                'social': 'google',
                                'email': email,
                                'first_name': given_name or '',
                                'last_name': family_name or ''
                            })
                            register_url = f"{base_url}/register?{query_params}"
                            logger.info(f"🔍 [GOOGLE_OAUTH] 가입 처리 페이지로 리다이렉트 (GET): {register_url}")
                            csrf_token = get_token(request)
                            return create_redirect_response(register_url, csrf_token)

                else:
                    logger.error("사용자 정보 조회 실패")
                    error_url = get_frontend_login_url(success=False, message='user_info_failed', original_domain=original_domain, return_url=return_url)
                    return create_redirect_response(error_url)

            except Exception as e:
                logger.error(f"Google OAuth 처리 중 오류: {e}")
                error_url = get_frontend_login_url(success=False, message=str(e), original_domain=original_domain, return_url=return_url)
                return create_redirect_response(error_url)

        except Exception as e:
            logger.error(f"Google OAuth 콜백 처리 중 오류: {e}")
            error_url = get_frontend_login_url(success=False, message=str(e), original_domain=original_domain, return_url=return_url)
            return create_redirect_response(error_url)

    def post(self, request, *args, **kwargs):
        try:
            # 상세한 디버깅 로그
            logger.info(f"🔍 [GOOGLE_OAUTH] Google OAuth POST 요청 시작")
            logger.info(f"  - 요청 도메인: {request.get_host()}")
            logger.info(f"  - 요청 스키마: {request.scheme}")
            logger.info(f"  - 요청 URL: {request.build_absolute_uri()}")
            logger.info(f"  - CLIENT_ID: {settings.GOOGLE_OAUTH_CLIENT_ID[:20]}...")
            logger.info(f"  - REDIRECT_URI: {settings.GOOGLE_OAUTH_REDIRECT_URI}")
            logger.info(f"  - CURRENT_DOMAIN: {os.getenv('CURRENT_DOMAIN', 'localhost')}")
            
            data = json.loads(request.body)
            id_token = data.get('id_token')  # ID 토큰 또는 authorization code
            language = data.get('language', BASE_LANGUAGE)
            logger.info(f"  - id_token 길이: {len(id_token) if id_token else 0}")
            logger.info(f"  - language: {language}")
            logger.info(f"  - 요청 데이터: {data}")
            
            # JSON 요청인지 확인 (Content-Type 헤더 확인)
            is_json_request = request.content_type == 'application/json' or 'application/json' in request.content_type
            if not id_token:
                return JsonResponse({
                    'success': False,
                    'message': get_ko_message('google_login_failed') if language == BASE_LANGUAGE else get_en_message(
                        'google_login_failed')
                }, status=400)

            # 변수 초기화
            email = None
            username = None
            google_id = None
            given_name = None
            family_name = None

            # ID 토큰인지 authorization code인지 확인
            if len(id_token) > 100:  # ID 토큰은 일반적으로 더 길다
                # ID 토큰 직접 디코딩 시도
                try:
                    # Google의 공개키로 ID 토큰 검증
                    decoded_token = jwt.decode(
                        id_token,
                        options={"verify_signature": False}  # 개발 환경에서는 서명 검증 생략
                    )

                    email = decoded_token.get('email')
                    google_id = decoded_token.get('sub')
                    name = decoded_token.get('name', '')
                    given_name = decoded_token.get('given_name', '')
                    family_name = decoded_token.get('family_name', '')

                    if not email:
                        raise Exception('ID 토큰에서 이메일을 가져올 수 없습니다.')

                    # 이름이 없으면 이메일에서 추출
                    if not name and email:
                        name = email.split('@')[0]

                    # 사용자명 생성
                    username = name if name else email.split('@')[0]

                except Exception as e:
                    logger.error(f"ID 토큰 디코딩 실패: {e}")
                    # ID 토큰 처리 실패 시 authorization code로 처리 시도
                    pass

            # ID 토큰 처리에 실패했거나 authorization code인 경우
            if not email:
                # Authorization code로 액세스 토큰 교환
                try:
                    logger.info(f"Authorization code로 액세스 토큰 교환 시도: {id_token[:20]}...")
                    
                    # 현재 요청의 도메인을 기반으로 redirect_uri 동적 생성
                    current_scheme = request.scheme
                    current_host = request.get_host()
                    dynamic_redirect_uri = f"{current_scheme}://{current_host}/api/google-oauth/"
                    
                    logger.info(f"사용하는 리다이렉트 URI: {settings.GOOGLE_OAUTH_REDIRECT_URI}")
                    logger.info(f"동적 생성된 리다이렉트 URI: {dynamic_redirect_uri}")
                    
                    # 먼저 동적 생성된 redirect_uri로 시도
                    token_response = requests.post('https://oauth2.googleapis.com/token', data={
                        'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
                        'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
                        'code': id_token,
                        'grant_type': 'authorization_code',
                        'redirect_uri': dynamic_redirect_uri
                    })
                    
                    # 동적 redirect_uri로 실패하면 설정된 redirect_uri로 재시도
                    if token_response.status_code != 200:
                        logger.warning(f"동적 redirect_uri로 실패, 설정된 redirect_uri로 재시도: {token_response.text}")
                        token_response = requests.post('https://oauth2.googleapis.com/token', data={
                            'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
                            'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
                            'code': id_token,
                            'grant_type': 'authorization_code',
                            'redirect_uri': settings.GOOGLE_OAUTH_REDIRECT_URI
                        })

                    logger.info(f"토큰 교환 응답 상태: {token_response.status_code}")
                    logger.info(f"토큰 교환 응답 내용: {token_response.text}")

                    if token_response.status_code != 200:
                        logger.error(f"토큰 교환 실패: {token_response.text}")
                        return JsonResponse({
                            'success': False,
                            'message': get_ko_message('google_login_failed') if language == BASE_LANGUAGE else get_en_message(
                                'google_login_failed')
                        }, status=400)

                    token_data = token_response.json()
                    access_token = token_data.get('access_token')

                    if not access_token:
                        logger.error("액세스 토큰을 가져올 수 없습니다")
                        return JsonResponse({
                            'success': False,
                            'message': get_ko_message('google_login_failed') if language == BASE_LANGUAGE else get_en_message(
                                'google_login_failed')
                        }, status=400)

                    # 액세스 토큰으로 사용자 정보 조회
                    user_info_response = requests.get(
                        'https://www.googleapis.com/oauth2/v2/userinfo',
                        headers={'Authorization': f'Bearer {access_token}'}
                    )

                    if user_info_response.status_code == 200:
                        user_info = user_info_response.json()
                        google_id = user_info.get('id')
                        email = user_info.get('email')
                        name = user_info.get('name', '')
                        given_name = user_info.get('given_name', '')
                        family_name = user_info.get('family_name', '')

                        # 이름이 없으면 이메일에서 추출
                        if not name and email:
                            name = email.split('@')[0]

                        # 사용자명 생성
                        username = name if name else email.split('@')[0]

                        logger.info(f"사용자 정보 조회 성공: {email}")
                    else:
                        raise Exception('액세스 토큰으로 사용자 정보를 가져올 수 없습니다.')

                except Exception as e:
                    logger.error(f"Authorization code 처리 실패: {e}")
                    return JsonResponse({
                        'success': False,
                        'message': get_ko_message('google_login_failed') if language == BASE_LANGUAGE else get_en_message(
                            'google_login_failed')
                    }, status=400)

            # 이메일이 필수
            if not email:
                return JsonResponse({
                    'success': False,
                    'message': get_ko_message('google_login_failed') if language == BASE_LANGUAGE else get_en_message(
                        'google_login_failed')
                }, status=400)

            # 이메일 정규화 (소문자로 변환하여 대소문자 차이 문제 해결)
            normalized_email = email.lower().strip() if email else None
            logger.info(f"🔍 [GOOGLE_OAUTH] 이메일 정규화: 원본={email}, 정규화={normalized_email}")
            
            with transaction.atomic():
                # 기존 사용자 확인 (이메일로, 대소문자 무시)
                existing_users = User.objects.filter(email__iexact=normalized_email) if normalized_email else User.objects.none()
                logger.info(f"🔍 [GOOGLE_OAUTH] 이메일로 사용자 검색: {normalized_email}, 결과 수={existing_users.count()}")
                
                if existing_users.exists():
                    # 기존 사용자가 있는 경우
                    if existing_users.count() > 1:
                        # 중복 사용자가 있는 경우, 가장 오래된 사용자를 선택
                        user = existing_users.order_by('date_joined').first()
                        logger.warning(f"⚠️ [GOOGLE_OAUTH] 중복 이메일 사용자 발견: {normalized_email}, 사용자 ID {user.id} 선택됨 (총 {existing_users.count()}개)")
                    else:
                        user = existing_users.first()
                        logger.info(f"✅ [GOOGLE_OAUTH] 기존 사용자 찾음: {normalized_email}, 사용자 ID {user.id}")
                    
                    # 기존 사용자의 프로필 확인 및 생성/업데이트
                    try:
                        user_profile = user.profile
                        # 프로필이 있지만 role이 없거나 비어있는 경우 업데이트
                        if not user_profile.role or user_profile.role == '':
                            user_profile.role = 'user_role'
                            user_profile.save()
                            logger.info(f"기존 사용자 프로필의 role이 없어서 'user_role'로 설정: {normalized_email}")
                    except UserProfile.DoesNotExist:
                        # 프로필이 없는 경우 생성
                        from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES, LANGUAGE_EN
                        preferred_language = language if language in SUPPORTED_LANGUAGES else LANGUAGE_EN
                        UserProfile.objects.create(
                            user=user,
                            role='user_role',
                            language=preferred_language,
                            email_verified=True,
                            retention_cleanup_enabled=True,
                            random_exam_email_enabled=True
                        )
                        logger.info(f"기존 사용자 프로필 생성: {normalized_email}")
                    
                    # 기존 사용자 로그인
                    login(request, user)
                    logger.info(f"✅ [GOOGLE_OAUTH] 기존 사용자 로그인 성공: {normalized_email} (ID: {user.id})")

                    # JWT 토큰 생성 (프론트엔드에서 사용자 정보를 제대로 가져오기 위해 필요)
                    tokens = issue_tokens_for_user(user)
                    user_payload = build_user_payload(user)
                    access_token = tokens['access']
                    logger.info(f"🔍 [GOOGLE_OAUTH] JWT 토큰 생성 완료 (access_token 길이: {len(access_token)})")

                    # JSON 요청인 경우 JSON 응답 반환
                    if is_json_request:
                        logger.info(f"✅ [GOOGLE_OAUTH] JSON 요청 - JSON 응답 반환 (기존 사용자)")
                        return JsonResponse({
                            'success': True,
                            'user': user_payload,
                            'tokens': tokens
                        })

                    # 프론트엔드로 리다이렉트 (성공 시)
                    logger.info(f"✅ [GOOGLE_OAUTH] 기존 사용자 로그인 성공, 리다이렉트 URL 생성 중...")
                    success_url = get_frontend_login_url(success=True, email=normalized_email or email)
                    success_url = add_access_token_to_url(success_url, access_token)
                    
                    logger.info(f"  - 생성된 success_url: {success_url[:200]}...")
                    csrf_token = get_token(request)
                    return create_redirect_response(success_url, csrf_token)
                else:
                    # 신규 사용자 - 가입 처리 페이지로 리다이렉트
                    logger.info(f"🔍 [GOOGLE_OAUTH] 신규 사용자 감지 - 가입 처리 페이지로 리다이렉트: {normalized_email or email}")
                    
                    # 소셜 로그인 정보를 세션에 임시 저장 (가입 처리 페이지에서 사용)
                    request.session['social_auth'] = {
                        'provider': 'google',
                        'email': normalized_email or email,
                        'first_name': given_name or '',
                        'last_name': family_name or '',
                        'google_id': google_id,
                        'language': language
                    }
                    
                    # 가입 처리 페이지로 리다이렉트
                    from urllib.parse import urlencode
                    # original_domain이 있으면 해당 도메인 사용, 없으면 기본 도메인 사용
                    if original_domain and original_domain not in ['localhost', '127.0.0.1']:
                        scheme = 'https'
                        base_url = f"{scheme}://{original_domain}"
                    else:
                        base_url = get_frontend_url('')
                    
                    query_params = urlencode({
                        'social': 'google',
                        'email': normalized_email or email,
                        'first_name': given_name or '',
                        'last_name': family_name or ''
                    })
                    register_url = f"{base_url}/register?{query_params}"
                    logger.info(f"🔍 [GOOGLE_OAUTH] 가입 처리 페이지로 리다이렉트: {register_url}")
                    csrf_token = get_token(request)
                    return create_redirect_response(register_url, csrf_token)
                    logger.info(f"🔍 [GOOGLE_OAUTH] JWT 토큰 생성 완료 (access_token 길이: {len(access_token)})")

                    # JSON 요청인 경우 JSON 응답 반환
                    if is_json_request:
                        logger.info(f"✅ [GOOGLE_OAUTH] JSON 요청 - JSON 응답 반환 (새 사용자)")
                        return JsonResponse({
                            'success': True,
                            'user': user_payload,
                            'tokens': tokens
                        })

                    # 프론트엔드로 리다이렉트 (성공 시)
                    logger.info(f"✅ [GOOGLE_OAUTH] 새 사용자 회원가입 성공, 리다이렉트 URL 생성 중...")
                    success_url = get_frontend_login_url(success=True, email=email)
                    success_url = add_access_token_to_url(success_url, access_token)
                    
                    logger.info(f"  - 생성된 success_url: {success_url[:200]}...")
                    csrf_token = get_token(request)
                    return create_redirect_response(success_url, csrf_token)

        except json.JSONDecodeError:
            # 오류 시 프론트엔드로 리다이렉트
            logger.error(f"❌ [GOOGLE_OAUTH] JSON 디코딩 오류")
            error_url = get_frontend_login_url(success=False, message='invalid_request')
            logger.info(f"  - 생성된 error_url: {error_url}")
            return create_redirect_response(error_url)
        except Exception as e:
            logger.error(f"❌ [GOOGLE_OAUTH] Google OAuth 처리 중 오류: {e}")
            # 오류 시 프론트엔드로 리다이렉트
            error_url = get_frontend_login_url(success=False, message=str(e))
            logger.info(f"  - 생성된 error_url: {error_url}")
            return create_redirect_response(error_url)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_google_oauth_config(request):
    """Google OAuth 설정 정보 반환"""
    # 현재 요청의 도메인을 기반으로 redirect URI 동적 생성
    scheme = request.scheme
    host = request.get_host()
    
    # 프론트엔드에서 전달받은 도메인 확인
    frontend_domain = request.GET.get('domain')
    
    # 디버깅 로그
    logger.info(f"🔍 [GOOGLE_OAUTH_CONFIG] 설정 정보 요청")
    logger.info(f"  - 요청 도메인: {host}")
    logger.info(f"  - 요청 스키마: {scheme}")
    logger.info(f"  - 프론트엔드에서 전달받은 도메인: {frontend_domain}")
    logger.info(f"  - X-Forwarded-Host: {request.META.get('HTTP_X_FORWARDED_HOST', 'Not set')}")
    logger.info(f"  - X-Forwarded-Proto: {request.META.get('HTTP_X_FORWARDED_PROTO', 'Not set')}")
    logger.info(f"  - Host 헤더: {request.META.get('HTTP_HOST', 'Not set')}")
    logger.info(f"  - Referer: {request.META.get('HTTP_REFERER', 'Not set')}")
    
    # 프론트엔드에서 전달받은 도메인이 있으면 우선 사용
    if frontend_domain:
        # 모바일 앱에서 localhost나 capacitor://로 시작하는 경우 기본 도메인 사용
        if frontend_domain in ['localhost', '127.0.0.1'] or frontend_domain.startswith('capacitor://'):
            logger.info(f"  - 모바일 앱 감지, 기본 도메인 사용: us.drillquiz.com")
            host = 'us.drillquiz.com'
        else:
            logger.info(f"  - 프론트엔드 도메인 사용: {frontend_domain}")
            host = frontend_domain
        scheme = 'https'  # 프론트엔드에서 전달받은 도메인은 항상 HTTPS
    else:
        # Referer 헤더에서 원본 도메인 추출 시도
        referer = request.META.get('HTTP_REFERER', '')
        if referer:
            try:
                from urllib.parse import urlparse
                parsed_referer = urlparse(referer)
                if parsed_referer.hostname and parsed_referer.hostname != host:
                    logger.info(f"  - Referer에서 도메인 추출: {parsed_referer.hostname}")
                    host = parsed_referer.hostname
                    scheme = parsed_referer.scheme or 'https'
            except Exception as e:
                logger.warning(f"  - Referer 파싱 실패: {e}")
        
        # X-Forwarded-Host가 있으면 우선 사용 (프록시 환경에서 원본 호스트)
        if request.META.get('HTTP_X_FORWARDED_HOST'):
            forwarded_host = request.META.get('HTTP_X_FORWARDED_HOST').split(',')[0].strip()
            logger.info(f"  - X-Forwarded-Host 사용: {forwarded_host}")
            host = forwarded_host
        
        # X-Forwarded-Proto가 있으면 사용
        if request.META.get('HTTP_X_FORWARDED_PROTO'):
            scheme = request.META.get('HTTP_X_FORWARDED_PROTO')
            logger.info(f"  - X-Forwarded-Proto 사용: {scheme}")
    
    redirect_uri = f"{scheme}://{host}/api/google-oauth/"
    
    logger.info(f"  - 최종 사용된 도메인: {host}")
    logger.info(f"  - 최종 사용된 스키마: {scheme}")
    logger.info(f"  - 동적 생성된 redirect_uri: {redirect_uri}")
    logger.info(f"  - 설정된 REDIRECT_URI: {settings.GOOGLE_OAUTH_REDIRECT_URI}")
    logger.info(f"  - CLIENT_ID: {settings.GOOGLE_OAUTH_CLIENT_ID[:20]}...")
    
    return Response({
        'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
        'redirect_uri': redirect_uri
    })


def verify_apple_identity_token(identity_token):
    """
    Apple Identity Token을 검증하고 사용자 정보를 반환합니다.
    """
    try:
        # Apple의 JWKS endpoint에서 공개키 가져오기
        jwks_url = 'https://appleid.apple.com/auth/keys'
        jwks_response = requests.get(jwks_url)
        jwks_response.raise_for_status()
        jwks = jwks_response.json()
        
        # JWT 헤더에서 kid 확인 (서명 검증 없이)
        unverified_header = jwt.get_unverified_header(identity_token)
        kid = unverified_header.get('kid')
        
        if not kid:
            raise Exception('JWT 헤더에서 kid를 찾을 수 없습니다.')
        
        # JWKS에서 해당 kid의 공개키 찾기
        public_key = None
        for key in jwks.get('keys', []):
            if key.get('kid') == kid:
                # JWK를 RSA 공개키로 변환
                import base64
                from cryptography.hazmat.primitives.asymmetric import rsa
                
                # Base64 URL-safe 디코딩
                n_bytes = base64.urlsafe_b64decode(key['n'] + '==')
                e_bytes = base64.urlsafe_b64decode(key['e'] + '==')
                
                # Big-endian 정수로 변환
                n_int = int.from_bytes(n_bytes, byteorder='big')
                e_int = int.from_bytes(e_bytes, byteorder='big')
                
                # RSA 공개키 생성
                public_key_numbers = rsa.RSAPublicNumbers(e_int, n_int)
                public_key_obj = public_key_numbers.public_key(default_backend())
                
                # PEM 형식으로 변환
                pem_public_key = public_key_obj.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
                public_key = pem_public_key
                break
        
        if not public_key:
            raise Exception(f'JWKS에서 kid {kid}에 해당하는 공개키를 찾을 수 없습니다.')
        
        # Apple의 Client ID 가져오기 (설정에서)
        apple_client_id = getattr(settings, 'APPLE_CLIENT_ID', None)
        if not apple_client_id:
            # 환경 변수에서 가져오기 시도
            apple_client_id = os.getenv('APPLE_CLIENT_ID')
        
        if not apple_client_id:
            # Client ID가 없으면 검증 시 audience 체크를 건너뛰기 위해 None 사용
            # 프로덕션에서는 반드시 설정해야 함
            logger.warning("APPLE_CLIENT_ID가 설정되지 않았습니다. audience 검증을 건너뜁니다.")
        
        # JWT 검증
        # iss: https://appleid.apple.com
        # aud: Client ID (있는 경우)
        verify_kwargs = {
            'algorithms': ['RS256'],
            'issuer': 'https://appleid.apple.com',
            'options': {'verify_aud': False}  # audience는 수동으로 검증
        }
        
        decoded_token = jwt.decode(
            identity_token,
            pem_public_key,
            **verify_kwargs
        )
        
        # audience 수동 검증
        token_aud = decoded_token.get('aud')
        if apple_client_id:
            # 네이티브 Apple Sign In은 App ID를 사용하고, 웹은 Services ID를 사용함
            # com.drillquiz.web과 com.drillquiz.app은 항상 서로 허용
            valid_audiences = []
            
            # 설정된 Client ID 추가
            if apple_client_id:
                valid_audiences.append(apple_client_id)
            
            # com.drillquiz.web과 com.drillquiz.app은 항상 서로 허용
            if 'com.drillquiz.web' not in valid_audiences:
                valid_audiences.append('com.drillquiz.web')
            if 'com.drillquiz.app' not in valid_audiences:
                valid_audiences.append('com.drillquiz.app')
            
            # 설정된 Client ID와 토큰의 audience가 일치하는지 확인
            if token_aud not in valid_audiences:
                logger.warning(f"Audience 불일치: 설정값 {apple_client_id}, 토큰 {token_aud}, 허용 목록 {valid_audiences}")
                raise Exception(f'Invalid audience: expected one of {valid_audiences}, got {token_aud}')
            logger.info(f"✅ Audience 검증 성공: {token_aud} (설정값: {apple_client_id}, 허용 목록: {valid_audiences})")
        else:
            # Client ID가 설정되지 않은 경우, 토큰의 audience를 로그로 기록
            logger.warning(f"APPLE_CLIENT_ID가 설정되지 않았습니다. 토큰의 audience: {token_aud}")
        
        # 사용자 정보 추출
        apple_user_id = decoded_token.get('sub')
        email = decoded_token.get('email')
        
        # 이름 정보는 첫 로그인 시에만 제공되며, 이후에는 없을 수 있음
        # email_verified는 이메일이 제공된 경우에만 True
        
        return {
            'apple_user_id': apple_user_id,
            'email': email,
            'email_verified': decoded_token.get('email_verified', False),
            'decoded_token': decoded_token
        }
        
    except jwt.ExpiredSignatureError:
        raise Exception('Apple Identity Token이 만료되었습니다.')
    except jwt.InvalidTokenError as e:
        raise Exception(f'Apple Identity Token 검증 실패: {str(e)}')
    except Exception as e:
        logger.error(f"Apple Identity Token 검증 중 오류: {e}", exc_info=True)
        raise Exception(f'Apple Identity Token 검증 중 오류가 발생했습니다: {str(e)}')


@method_decorator(csrf_exempt, name='dispatch')
class AppleOAuthView(View):
    """Sign in with Apple OAuth 뷰 (GET/POST 모두 처리)"""
    
    def get(self, request, *args, **kwargs):
        """OAuth 콜백 처리 - GET 요청 (response_mode=query인 경우)"""
        try:
            logger.info(f"🔍 [APPLE_OAUTH] ========== Sign in with Apple GET 요청 시작 ==========")
            logger.info(f"🔍 [APPLE_OAUTH] 요청 메서드: {request.method}")
            logger.info(f"🔍 [APPLE_OAUTH] request.GET 존재 여부: {bool(request.GET)}")
            logger.info(f"🔍 [APPLE_OAUTH] request.GET 키 목록: {list(request.GET.keys()) if request.GET else '(없음)'}")
            
            # GET 요청 파라미터에서 데이터 추출 (response_mode=query인 경우)
            code = request.GET.get('code')  # authorization code (사용 안 함, id_token 사용)
            id_token = request.GET.get('id_token')  # identity token
            error = request.GET.get('error')
            error_description = request.GET.get('error_description', '')
            state = request.GET.get('state')
            user_info_json = request.GET.get('user')  # JSON 문자열
            
            # user_info 파싱
            user_info = None
            if user_info_json:
                try:
                    user_info = json.loads(user_info_json)
                except:
                    logger.warning(f"user_info JSON 파싱 실패: {user_info_json}")
            
            # state에서 language, return_url 추출
            language = BASE_LANGUAGE
            return_url = None
            original_domain = None
            if state:
                try:
                    import base64
                    decoded_state = base64.b64decode(state).decode('utf-8')
                    state_data = json.loads(decoded_state)
                    language = state_data.get('language', BASE_LANGUAGE)
                    return_url = state_data.get('returnUrl', '')
                    if return_url:
                        from urllib.parse import urlparse
                        parsed_url = urlparse(return_url)
                        original_domain = parsed_url.hostname
                        # 모바일 앱에서 capacitor://localhost인 경우 서버 도메인 사용
                        if original_domain in ['localhost', '127.0.0.1'] or parsed_url.scheme in ['capacitor', 'ionic']:
                            logger.info(f"🔍 [APPLE_OAUTH] 모바일 앱 감지, 도메인을 us.drillquiz.com으로 변경 (원본: {original_domain})")
                            original_domain = 'us.drillquiz.com'
                        logger.info(f"🔍 [APPLE_OAUTH] State에서 추출한 원본 도메인: {original_domain}")
                        logger.info(f"🔍 [APPLE_OAUTH] State에서 추출한 return_url: {return_url}")
                except Exception as e:
                    logger.warning(f"🔍 [APPLE_OAUTH] State 파싱 실패: {e}")
                    pass
            
            if error:
                logger.error(f"❌ [APPLE_OAUTH] Apple OAuth 오류: {error} - {error_description}")
                error_url = get_frontend_login_url(success=False, message=f'Apple login failed: {error}', original_domain=original_domain, return_url=return_url)
                return create_redirect_response(error_url)
            
            logger.info(f"  - id_token: {'있음' if id_token else '없음'}")
            logger.info(f"  - user_info: {'있음' if user_info else '없음'}")
            logger.info(f"  - language: {language}")
            
            if not id_token:
                logger.error("❌ [APPLE_OAUTH] id_token이 없습니다 (GET 요청)")
                error_url = get_frontend_login_url(success=False, message='Apple login failed: identity_token is required', original_domain=original_domain, return_url=return_url)
                return create_redirect_response(error_url)
            
            # Apple Identity Token 검증 및 사용자 처리 (POST 메서드와 동일한 로직 사용)
            # identity_token을 id_token으로 사용
            identity_token = id_token
            
            try:
                apple_data = verify_apple_identity_token(identity_token)
                apple_user_id = apple_data['apple_user_id']
                email = apple_data['email']
                email_verified = apple_data['email_verified']
            except Exception as e:
                logger.error(f"❌ [APPLE_OAUTH] Apple Identity Token 검증 실패: {e}")
                error_url = get_frontend_login_url(success=False, message=f'Apple Identity Token 검증 실패: {str(e)}', original_domain=original_domain, return_url=return_url)
                return create_redirect_response(error_url)
            
            # 첫 로그인 시 user_info에서 이름 정보 가져오기
            first_name = ''
            last_name = ''
            if user_info:
                name = user_info.get('name', {})
                first_name = name.get('firstName', '') if isinstance(name, dict) else ''
                last_name = name.get('lastName', '') if isinstance(name, dict) else ''
                if not email and isinstance(user_info, dict):
                    email = user_info.get('email')
            
            # 이메일이 없으면 apple_user_id를 사용
            if not email:
                email = f"{apple_user_id}@privaterelay.appleid.com"
            
            # 사용자명 생성
            base_username = email.split('@')[0] if email else f"apple_{apple_user_id[:8]}"
            
            with transaction.atomic():
                # 기존 사용자 확인
                existing_users = User.objects.filter(email=email) if email else User.objects.none()
                user = None
                if existing_users.exists():
                    user = existing_users.first()
                
                if user:
                    # 기존 사용자 로그인 (POST 메서드와 동일한 로직)
                    try:
                        user_profile = user.profile
                        if not user_profile.role or user_profile.role == '':
                            user_profile.role = 'user_role'
                            user_profile.save()
                    except UserProfile.DoesNotExist:
                        from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES, LANGUAGE_EN
                        preferred_language = language if language in SUPPORTED_LANGUAGES else LANGUAGE_EN
                        UserProfile.objects.create(
                            user=user,
                            role='user_role',
                            language=preferred_language,
                            email_verified=email_verified,
                            retention_cleanup_enabled=True,
                            random_exam_email_enabled=True
                        )
                    
                    if first_name and not user.first_name:
                        user.first_name = first_name
                    if last_name and not user.last_name:
                        user.last_name = last_name
                    if first_name or last_name:
                        user.save()
                    
                    login(request, user)
                    logger.info(f"✅ [APPLE_OAUTH] 기존 사용자 로그인 성공 (GET): {email or apple_user_id}")
                    
                    tokens = issue_tokens_for_user(user)
                    user_payload = build_user_payload(user)
                    access_token = tokens['access']
                    
                    success_url = get_frontend_login_url(success=True, email=user.email or apple_user_id, original_domain=original_domain, return_url=return_url)
                    success_url = add_access_token_to_url(success_url, access_token)
                    logger.info(f"✅ [APPLE_OAUTH] success_url capacitor:// 시작: {success_url.startswith('capacitor://')}")
                    csrf_token = get_token(request)
                    response = create_redirect_response(success_url, csrf_token)
                    logger.info(f"✅ [APPLE_OAUTH] ==========================================")
                    return response
                else:
                    # 신규 사용자 - 가입 처리 페이지로 리다이렉트 (GET 요청)
                    logger.info(f"🔍 [APPLE_OAUTH] 신규 사용자 감지 (GET) - 가입 처리 페이지로 리다이렉트: {email or apple_user_id}")
                    
                    # 이메일이 제공되지 않은 경우 에러 반환
                    if not normalized_email:
                        error_message = 'Apple 로그인 시 이메일이 제공되지 않았습니다. 이메일 공유를 허용해주세요.'
                        logger.error(f"❌ [APPLE_OAUTH] {error_message}")
                        error_url = get_frontend_login_url(
                            success=False, 
                            message=error_message, 
                            original_domain=original_domain, 
                            return_url=return_url
                        )
                        return create_redirect_response(error_url)
                    
                    # 소셜 로그인 정보를 세션에 임시 저장 (가입 처리 페이지에서 사용)
                    request.session['social_auth'] = {
                        'provider': 'apple',
                        'email': normalized_email,
                        'first_name': first_name,
                        'last_name': last_name,
                        'apple_user_id': apple_user_id,
                        'identity_token': identity_token,  # 가입 완료 시 검증용
                        'language': language
                    }
                    
                    # 가입 처리 페이지로 리다이렉트
                    from urllib.parse import urlencode
                    # original_domain이 있으면 해당 도메인 사용, 없으면 기본 도메인 사용
                    if original_domain and original_domain not in ['localhost', '127.0.0.1']:
                        scheme = 'https'
                        base_url = f"{scheme}://{original_domain}"
                    else:
                        base_url = get_frontend_url('')
                    
                    query_params = urlencode({
                        'social': 'apple',
                        'email': normalized_email,
                        'first_name': first_name,
                        'last_name': last_name
                    })
                    register_url = f"{base_url}/register?{query_params}"
                    logger.info(f"🔍 [APPLE_OAUTH] 가입 처리 페이지로 리다이렉트 (GET): {register_url}")
                    csrf_token = get_token(request)
                    return create_redirect_response(register_url, csrf_token)
                    
                    tokens = issue_tokens_for_user(user)
                    user_payload = build_user_payload(user)
                    access_token = tokens['access']
                    
                    success_url = get_frontend_login_url(success=True, email=user.email or apple_user_id, original_domain=original_domain, return_url=return_url)
                    success_url = add_access_token_to_url(success_url, access_token)
                    logger.info(f"✅ [APPLE_OAUTH] success_url capacitor:// 시작: {success_url.startswith('capacitor://')}")
                    csrf_token = get_token(request)
                    response = create_redirect_response(success_url, csrf_token)
                    logger.info(f"✅ [APPLE_OAUTH] ==========================================")
                    return response
                    
        except Exception as e:
            logger.error(f"❌ [APPLE_OAUTH] GET 요청 처리 중 오류: {e}")
            import traceback
            logger.error(traceback.format_exc())
            error_url = get_frontend_login_url(success=False, message=str(e), original_domain=original_domain if 'original_domain' in locals() else None, return_url=return_url if 'return_url' in locals() else None)
            return create_redirect_response(error_url)
    
    def post(self, request, *args, **kwargs):
        """Sign in with Apple 엔드포인트 - POST 요청"""
        # 변수 초기화 (에러 핸들러에서도 사용 가능하도록 함수 시작 부분에서 초기화)
        is_json_request = False  # 기본값: HTML 리다이렉트 응답
        original_domain = None
        return_url = None
        language = BASE_LANGUAGE
        
        try:
            logger.info(f"🔍 [APPLE_OAUTH] ========== Sign in with Apple POST 요청 시작 ==========")
            logger.info(f"🔍 [APPLE_OAUTH] 요청 메서드: {request.method}")
            logger.info(f"🔍 [APPLE_OAUTH] Content-Type: {request.content_type}")
            logger.info(f"🔍 [APPLE_OAUTH] request.POST 존재 여부: {bool(request.POST)}")
            logger.info(f"🔍 [APPLE_OAUTH] request.POST 키 목록: {list(request.POST.keys()) if request.POST else '(없음)'}")
            logger.info(f"🔍 [APPLE_OAUTH] request.body 길이: {len(request.body) if request.body else 0}")
            
            # Apple의 form_post 방식은 request.POST에 데이터가 있음
            # 또는 JSON body에 있을 수 있음 (프론트엔드에서 직접 호출하는 경우)
            if request.POST:
                # Apple이 form_post로 전송한 경우
                identity_token = request.POST.get('id_token')
                code = request.POST.get('code')  # authorization code (사용 안 함)
                user_info_json = request.POST.get('user')  # JSON 문자열
                state = request.POST.get('state')
                
                # user_info 파싱
                user_info = None
                if user_info_json:
                    try:
                        user_info = json.loads(user_info_json)
                    except:
                        logger.warning(f"user_info JSON 파싱 실패: {user_info_json}")
                
                # state에서 language, return_url 추출
                language = BASE_LANGUAGE
                return_url = None
                original_domain = None
                if state:
                    try:
                        import base64
                        decoded_state = base64.b64decode(state).decode('utf-8')
                        state_data = json.loads(decoded_state)
                        language = state_data.get('language', BASE_LANGUAGE)
                        return_url = state_data.get('returnUrl', '')
                        if return_url:
                            from urllib.parse import urlparse
                            parsed_url = urlparse(return_url)
                            original_domain = parsed_url.hostname
                            # 모바일 앱에서 capacitor://localhost인 경우 서버 도메인 사용
                            if original_domain in ['localhost', '127.0.0.1'] or parsed_url.scheme in ['capacitor', 'ionic']:
                                logger.info(f"🔍 [APPLE_OAUTH] 모바일 앱 감지, 도메인을 us.drillquiz.com으로 변경 (원본: {original_domain})")
                                original_domain = 'us.drillquiz.com'
                            logger.info(f"🔍 [APPLE_OAUTH] State에서 추출한 원본 도메인: {original_domain}")
                            logger.info(f"🔍 [APPLE_OAUTH] State에서 추출한 return_url: {return_url}")
                    except Exception as e:
                        logger.warning(f"🔍 [APPLE_OAUTH] State 파싱 실패: {e}")
                        pass
            else:
                # JSON body로 전송된 경우 (프론트엔드에서 직접 호출) - JSON 응답 반환
                is_json_request = True  # JSON 응답 반환 플래그
                logger.info(f"🔍 [APPLE_OAUTH] JSON 요청 감지 - JSON 응답 반환")
                data = {}
                try:
                    body = request.body
                    if isinstance(body, bytes):
                        body_str = body.decode('utf-8')
                        if body_str:
                            data = json.loads(body_str)
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    logger.warning(f"JSON body 파싱 실패: {e}")
                    data = {}
                
                identity_token = data.get('identity_token')
                user_info = data.get('user')  # 첫 로그인 시에만 제공됨 (name, email 등)
                language = data.get('language', BASE_LANGUAGE)
                # JSON body에서는 return_url을 state에서 추출하지 않음 (네이티브 인증에서는 불필요)
            
            logger.info(f"  - identity_token: {'있음' if identity_token else '없음'}")
            logger.info(f"  - user_info: {'있음' if user_info else '없음'}")
            logger.info(f"  - language: {language}")
            
            if not identity_token:
                logger.error("❌ [APPLE_OAUTH] identity_token이 없습니다")
                # JSON 요청인 경우 JSON 응답 반환
                if is_json_request:
                    return JsonResponse({
                        'success': False,
                        'message': 'Apple login failed: identity_token is required'
                    }, status=400)
                # HTML 리다이렉트 응답
                error_url = get_frontend_login_url(success=False, message='Apple login failed: identity_token is required', original_domain=original_domain, return_url=return_url)
                return create_redirect_response(error_url)
            
            # Apple Identity Token 검증
            try:
                apple_data = verify_apple_identity_token(identity_token)
                apple_user_id = apple_data['apple_user_id']
                email = apple_data['email']
                email_verified = apple_data['email_verified']
            except Exception as e:
                logger.error(f"❌ [APPLE_OAUTH] Apple Identity Token 검증 실패: {e}")
                # JSON 요청인 경우 JSON 응답 반환
                if is_json_request:
                    logger.info(f"🔍 [APPLE_OAUTH] JSON 요청 - JSON 에러 응답 반환")
                    return JsonResponse({
                        'success': False,
                        'message': f'Apple Identity Token 검증 실패: {str(e)}'
                    }, status=400)
                # HTML 리다이렉트 응답
                error_url = get_frontend_login_url(success=False, message=f'Apple Identity Token 검증 실패: {str(e)}', original_domain=original_domain, return_url=return_url)
                return create_redirect_response(error_url)
            
            # 첫 로그인 시 user_info에서 이름 정보 가져오기
            first_name = ''
            last_name = ''
            if user_info:
                name = user_info.get('name', {})
                first_name = name.get('firstName', '') if isinstance(name, dict) else ''
                last_name = name.get('lastName', '') if isinstance(name, dict) else ''
                # 첫 로그인 시 이메일도 user_info에 제공될 수 있음
                if not email and isinstance(user_info, dict):
                    email = user_info.get('email')
            
            # 이메일 정규화 (소문자로 변환하여 대소문자 차이 문제 해결)
            # 실제 이메일이 제공된 경우에만 정규화
            normalized_email = email.lower().strip() if email and '@' in email and not email.endswith('@privaterelay.appleid.com') else None
            
            # 이메일이 없거나 더미 이메일인 경우 None으로 설정
            if not normalized_email or normalized_email.endswith('@privaterelay.appleid.com'):
                normalized_email = None
                logger.info(f"🔍 [APPLE_OAUTH] 실제 이메일이 제공되지 않음 (Apple User ID: {apple_user_id})")
            else:
                logger.info(f"🔍 [APPLE_OAUTH] 이메일 정규화: 원본={email}, 정규화={normalized_email}")
            
            # 사용자명 생성 (이메일 또는 Apple User ID 사용)
            base_username = normalized_email.split('@')[0] if normalized_email else f"apple_{apple_user_id[:8]}"
            
            with transaction.atomic():
                # 기존 사용자 확인 (이메일로, 대소문자 무시)
                user = None
                if normalized_email:
                    # 이메일로 사용자 찾기 (대소문자 무시를 위해 __iexact 사용)
                    existing_users = User.objects.filter(email__iexact=normalized_email)
                    logger.info(f"🔍 [APPLE_OAUTH] 이메일로 사용자 검색: {normalized_email}, 결과 수={existing_users.count()}")
                    
                    if existing_users.exists():
                        # Google OAuth와 동일하게 중복 사용자 처리
                        if existing_users.count() > 1:
                            # 중복 사용자가 있는 경우, 가장 오래된 사용자를 선택
                            user = existing_users.order_by('date_joined').first()
                            logger.warning(f"⚠️ [APPLE_OAUTH] 중복 이메일 사용자 발견: {normalized_email}, 사용자 ID {user.id} 선택됨 (총 {existing_users.count()}개)")
                        else:
                            user = existing_users.first()
                            logger.info(f"✅ [APPLE_OAUTH] 기존 사용자 찾음: {normalized_email}, 사용자 ID {user.id}")
                    else:
                        logger.info(f"ℹ️ [APPLE_OAUTH] 기존 사용자 없음: {normalized_email}")
                else:
                    logger.warning(f"⚠️ [APPLE_OAUTH] 이메일이 제공되지 않음, Apple User ID로만 인식: {apple_user_id}")
                
                if user:
                    # 기존 사용자 로그인
                    try:
                        user_profile = user.profile
                        # 프로필이 있지만 role이 없거나 비어있는 경우 업데이트
                        if not user_profile.role or user_profile.role == '':
                            user_profile.role = 'user_role'
                            user_profile.save()
                    except UserProfile.DoesNotExist:
                        # 프로필이 없는 경우 생성
                        from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES, LANGUAGE_EN
                        preferred_language = language if language in SUPPORTED_LANGUAGES else LANGUAGE_EN
                        UserProfile.objects.create(
                            user=user,
                            role='user_role',
                            language=preferred_language,
                            email_verified=email_verified,
                            retention_cleanup_enabled=True,
                            random_exam_email_enabled=True
                        )
                    
                    # 이름 업데이트 (첫 로그인 시에만 제공된 경우)
                    if first_name and not user.first_name:
                        user.first_name = first_name
                    if last_name and not user.last_name:
                        user.last_name = last_name
                    if first_name or last_name:
                        user.save()
                    
                    # 기존 사용자 로그인
                    login(request, user)
                    logger.info(f"✅ [APPLE_OAUTH] 기존 사용자 로그인 성공: {email or apple_user_id}")
                    
                    tokens = issue_tokens_for_user(user)
                    user_payload = build_user_payload(user)
                    
                    # JSON 요청인 경우 JSON 응답 반환
                    if is_json_request:
                        logger.info(f"✅ [APPLE_OAUTH] JSON 요청 - JSON 응답 반환 (기존 사용자)")
                        return JsonResponse({
                            'success': True,
                            'user': user_payload,
                            'tokens': tokens
                        })
                    
                    # HTML 리다이렉트 응답 (기존 로직)
                    access_token = tokens['access']
                    success_url = get_frontend_login_url(success=True, email=user.email or apple_user_id, original_domain=original_domain, return_url=return_url)
                    success_url = add_access_token_to_url(success_url, access_token)
                    logger.info(f"✅ [APPLE_OAUTH] ========== 기존 사용자 로그인 성공 ==========")
                    logger.info(f"✅ [APPLE_OAUTH] 이메일: {user.email or apple_user_id}")
                    logger.info(f"✅ [APPLE_OAUTH] original_domain: {original_domain}")
                    logger.info(f"✅ [APPLE_OAUTH] return_url: {return_url}")
                    logger.info(f"✅ [APPLE_OAUTH] 생성된 success_url 전체: {success_url}")
                    logger.info(f"✅ [APPLE_OAUTH] success_url 길이: {len(success_url)}")
                    logger.info(f"✅ [APPLE_OAUTH] success_url에 login=success 포함: {'login=success' in success_url}")
                    logger.info(f"✅ [APPLE_OAUTH] success_url에 email 포함: {bool('email=' in success_url)}")
                    logger.info(f"✅ [APPLE_OAUTH] success_url capacitor:// 시작: {success_url.startswith('capacitor://')}")
                    csrf_token = get_token(request)
                    logger.info(f"✅ [APPLE_OAUTH] create_redirect_response 호출 시작")
                    response = create_redirect_response(success_url, csrf_token)
                    logger.info(f"✅ [APPLE_OAUTH] create_redirect_response 응답 타입: {type(response).__name__}")
                    logger.info(f"✅ [APPLE_OAUTH] create_redirect_response 응답 상태 코드: {response.status_code}")
                    if hasattr(response, 'content'):
                        logger.info(f"✅ [APPLE_OAUTH] 응답 Content-Type: {response.get('Content-Type', '(없음)')}")
                        logger.info(f"✅ [APPLE_OAUTH] 응답 content 길이: {len(response.content) if response.content else 0}")
                    logger.info(f"✅ [APPLE_OAUTH] ==========================================")
                    return response
                else:
                    # 새 사용자 - 가입 처리 페이지로 리다이렉트
                    # 이메일이 제공되지 않은 경우 에러 반환
                    if not normalized_email:
                        error_message = 'Apple 로그인 시 이메일이 제공되지 않았습니다. 이메일 공유를 허용해주세요.'
                        logger.error(f"❌ [APPLE_OAUTH] {error_message}")
                        
                        # JSON 요청인 경우 JSON 응답 반환
                        if is_json_request:
                            return JsonResponse({
                                'success': False,
                                'message': error_message
                            }, status=400)
                        
                        # HTML 리다이렉트 응답
                        error_url = get_frontend_login_url(
                            success=False, 
                            message=error_message, 
                            original_domain=original_domain, 
                            return_url=return_url
                        )
                        return create_redirect_response(error_url)
                    
                    # 이메일 중복 확인
                    if User.objects.filter(email__iexact=normalized_email).exists():
                        error_message = f'이미 존재하는 email입니다: {normalized_email}'
                        logger.error(f"❌ [APPLE_OAUTH] {error_message}")
                        
                        # JSON 요청인 경우 JSON 응답 반환
                        if is_json_request:
                            return JsonResponse({
                                'success': False,
                                'message': error_message
                            }, status=400)
                        
                        # HTML 리다이렉트 응답
                        error_url = get_frontend_login_url(
                            success=False, 
                            message=error_message, 
                            original_domain=original_domain, 
                            return_url=return_url
                        )
                        return create_redirect_response(error_url)
                    
                    # 신규 사용자 - 가입 처리 페이지로 리다이렉트
                    logger.info(f"🔍 [APPLE_OAUTH] 신규 사용자 감지 - 가입 처리 페이지로 리다이렉트: {normalized_email}")
                    
                    # 소셜 로그인 정보를 세션에 임시 저장 (가입 처리 페이지에서 사용)
                    request.session['social_auth'] = {
                        'provider': 'apple',
                        'email': normalized_email,
                        'first_name': first_name,
                        'last_name': last_name,
                        'apple_user_id': apple_user_id,
                        'identity_token': identity_token,  # 가입 완료 시 검증용
                        'language': language
                    }
                    
                    # JSON 요청인 경우 JSON 응답 반환
                    if is_json_request:
                        logger.info(f"🔍 [APPLE_OAUTH] JSON 요청 - 신규 사용자 플래그 반환")
                        # 언어에 따라 메시지 반환
                        message = get_message_by_language(language, 'register.requiresRegistration', 'Registration is required.')
                        return JsonResponse({
                            'success': False,
                            'requires_registration': True,
                            'message': message,
                            'social_auth': {
                                'provider': 'apple',
                                'email': normalized_email,
                                'first_name': first_name,
                                'last_name': last_name
                            }
                        })
                    
                    # HTML 리다이렉트 응답 - 가입 처리 페이지로 이동
                    from urllib.parse import urlencode
                    # original_domain이 있으면 해당 도메인 사용, 없으면 기본 도메인 사용
                    if original_domain and original_domain not in ['localhost', '127.0.0.1']:
                        scheme = 'https'
                        base_url = f"{scheme}://{original_domain}"
                    else:
                        base_url = get_frontend_url('')
                    
                    query_params = urlencode({
                        'social': 'apple',
                        'email': normalized_email,
                        'first_name': first_name,
                        'last_name': last_name
                    })
                    register_url = f"{base_url}/register?{query_params}"
                    logger.info(f"🔍 [APPLE_OAUTH] 가입 처리 페이지로 리다이렉트: {register_url}")
                    return create_redirect_response(register_url)
                    
        except (json.JSONDecodeError, ValueError) as decode_error:
            logger.error(f"❌ [APPLE_OAUTH] JSON 디코딩 오류: {decode_error}")
            # JSON 요청인 경우 JSON 응답 반환
            if is_json_request:
                return JsonResponse({
                    'success': False,
                    'message': 'invalid_request'
                }, status=400)
            # HTML 리다이렉트 응답
            error_url = get_frontend_login_url(success=False, message='invalid_request', original_domain=original_domain, return_url=return_url)
            return create_redirect_response(error_url)
        except Exception as e:
            logger.error(f"❌ [APPLE_OAUTH] Sign in with Apple 처리 중 오류: {e}", exc_info=True)
            # JSON 요청인 경우 JSON 응답 반환
            if is_json_request:
                return JsonResponse({
                    'success': False,
                    'message': str(e)
                }, status=500)
            # HTML 리다이렉트 응답
            error_url = get_frontend_login_url(success=False, message=str(e), original_domain=original_domain, return_url=return_url)
            return create_redirect_response(error_url)


@api_view(['GET'])
@permission_classes([AllowAny])
def check_auth_status(request):
    """사용자 인증 상태 확인"""
    logger.info(f"🔍 [AUTH_STATUS] 인증 상태 확인 요청")
    logger.info(f"🔍 [AUTH_STATUS] 사용자: {request.user}")
    logger.info(f"🔍 [AUTH_STATUS] 인증 여부: {request.user.is_authenticated}")
    logger.info(f"🔍 [AUTH_STATUS] 세션 키: {request.session.session_key}")
    logger.info(f"🔍 [AUTH_STATUS] 쿠키: {dict(request.COOKIES)}")
    
    if request.user.is_authenticated:
        logger.info(f"✅ [AUTH_STATUS] 인증된 사용자: {request.user.email}")
        
        # UserProfile에서 role과 language 가져오기
        try:
            profile = request.user.profile
            user_role = profile.role
            from quiz.utils.multilingual_utils import BASE_LANGUAGE
            language = profile.language if profile.language else BASE_LANGUAGE
        except:
            from quiz.models import UserProfile
            profile = UserProfile.objects.create(user=request.user, role='user_role')
            user_role = profile.role
            from quiz.utils.multilingual_utils import BASE_LANGUAGE
            language = profile.language if profile.language else BASE_LANGUAGE
        
        return JsonResponse({
            'authenticated': True,
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'is_staff': request.user.is_staff,
                'is_superuser': request.user.is_superuser,
                'role': user_role,  # UserProfile의 role 필드
                'language': language  # UserProfile의 language 필드
            }
        })
    else:
        logger.info(f"❌ [AUTH_STATUS] 인증되지 않은 사용자")
        return JsonResponse({
            'authenticated': False,
            'user': None
        })

