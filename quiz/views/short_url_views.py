import hashlib
import string
import random
from django.shortcuts import redirect
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from ..models import ShortUrl
import logging

logger = logging.getLogger(__name__)


def generate_short_code(length=8):
    """단축 코드 생성"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def create_short_url(original_url, user=None, expires_days=None):
    """단축 URL 생성"""
    # 기존에 같은 URL이 있는지 확인
    existing_short_url = ShortUrl.objects.filter(original_url=original_url).first()
    if existing_short_url and not existing_short_url.is_expired():
        return existing_short_url
    
    # 고유한 short_code 생성
    while True:
        short_code = generate_short_code()
        if not ShortUrl.objects.filter(short_code=short_code).exists():
            break
    
    # 만료일 설정
    expires_at = None
    if expires_days:
        expires_at = timezone.now() + timezone.timedelta(days=expires_days)
    
    # 단축 URL 생성
    short_url = ShortUrl.objects.create(
        short_code=short_code,
        original_url=original_url,
        created_by=user,
        expires_at=expires_at
    )
    
    return short_url


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_short_url_api(request):
    """단축 URL 생성 API"""
    try:
        original_url = request.data.get('url')
        if not original_url:
            return Response(
                {'error': 'URL이 필요합니다.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 기본 만료일: 30일
        expires_days = request.data.get('expires_days', 30)
        
        # 단축 URL 생성
        short_url = create_short_url(
            original_url=original_url,
            user=request.user,
            expires_days=expires_days
        )
        
        # 단축 URL 생성
        base_url = request.build_absolute_uri('/')
        short_url_full = f"{base_url}s/{short_url.short_code}"
        
        return Response({
            'short_code': short_url.short_code,
            'short_url': short_url_full,
            'original_url': short_url.original_url,
            'created_at': short_url.created_at,
            'expires_at': short_url.expires_at
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"단축 URL 생성 실패: {str(e)}")
        return Response(
            {'error': '단축 URL 생성에 실패했습니다.'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_short_url_info(request, short_code):
    """단축 URL 정보 조회 API"""
    try:
        short_url = ShortUrl.objects.get(short_code=short_code)
        
        # 만료된 URL인지 확인
        if short_url.is_expired():
            return Response(
                {'error': '만료된 URL입니다.'}, 
                status=status.HTTP_410_GONE
            )
        
        base_url = request.build_absolute_uri('/')
        short_url_full = f"{base_url}s/{short_url.short_code}"
        
        return Response({
            'short_code': short_url.short_code,
            'short_url': short_url_full,
            'original_url': short_url.original_url,
            'created_at': short_url.created_at,
            'expires_at': short_url.expires_at,
            'access_count': short_url.access_count,
            'last_accessed_at': short_url.last_accessed_at
        })
        
    except ShortUrl.DoesNotExist:
        return Response(
            {'error': '단축 URL을 찾을 수 없습니다.'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"단축 URL 정보 조회 실패: {str(e)}")
        return Response(
            {'error': '단축 URL 정보 조회에 실패했습니다.'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_short_urls(request):
    """사용자의 단축 URL 목록 조회 API"""
    try:
        short_urls = ShortUrl.objects.filter(created_by=request.user).order_by('-created_at')
        
        base_url = request.build_absolute_uri('/')
        results = []
        
        for short_url in short_urls:
            results.append({
                'short_code': short_url.short_code,
                'short_url': f"{base_url}s/{short_url.short_code}",
                'original_url': short_url.original_url,
                'created_at': short_url.created_at,
                'expires_at': short_url.expires_at,
                'access_count': short_url.access_count,
                'last_accessed_at': short_url.last_accessed_at,
                'is_expired': short_url.is_expired()
            })
        
        return Response(results)
        
    except Exception as e:
        logger.error(f"사용자 단축 URL 목록 조회 실패: {str(e)}")
        return Response(
            {'error': '단축 URL 목록 조회에 실패했습니다.'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_short_url(request, short_code):
    """단축 URL 삭제 API"""
    try:
        short_url = ShortUrl.objects.get(short_code=short_code, created_by=request.user)
        short_url.delete()
        
        return Response(
            {'message': '단축 URL이 삭제되었습니다.'}, 
            status=status.HTTP_204_NO_CONTENT
        )
        
    except ShortUrl.DoesNotExist:
        return Response(
            {'error': '단축 URL을 찾을 수 없습니다.'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"단축 URL 삭제 실패: {str(e)}")
        return Response(
            {'error': '단축 URL 삭제에 실패했습니다.'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def redirect_short_url(request, short_code):
    """단축 URL 리다이렉션 뷰"""
    print(f"🔗 단축 URL 뷰 호출됨: {short_code}")
    logger.info(f"단축 URL 접근: {short_code}")
    try:
        short_url = ShortUrl.objects.get(short_code=short_code)
        logger.info(f"단축 URL 찾음: {short_url.original_url}")
        
        # 만료된 URL인지 확인
        if short_url.is_expired():
            logger.warning(f"만료된 URL: {short_code}")
            from django.http import HttpResponse
            return HttpResponse("URL이 만료되었습니다.", status=410)
        
        # Google 크롤러 감지 (403 오류 방지)
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        is_google_crawler = any(bot in user_agent for bot in [
            'googlebot', 'google-inspectiontool', 'googleother', 
            'google-extended', 'apis-google', 'mediapartners-google'
        ])
        
        # 원본 URL에서 시험 ID 추출 및 권한 확인
        import re
        from urllib.parse import urlparse, parse_qs
        from ..models import Exam, Member, ExamResult
        
        original_url = short_url.original_url
        parsed_url = urlparse(original_url)
        
        # URL에서 시험 ID 추출
        exam_id = None
        # /take-exam/{exam_id} 패턴
        take_exam_match = re.search(r'/take-exam/([a-f0-9-]+)', original_url)
        if take_exam_match:
            exam_id = take_exam_match.group(1)
        else:
            # /take-exam?exam_id={exam_id} 패턴
            query_params = parse_qs(parsed_url.query)
            if 'exam_id' in query_params:
                exam_id = query_params['exam_id'][0]
            elif 'examId' in query_params:
                exam_id = query_params['examId'][0]
        
        # 시험 ID가 있으면 권한 확인 (Google 크롤러는 제외)
        if exam_id and not is_google_crawler:
            try:
                exam = Exam.objects.get(id=exam_id)
                user = request.user
                
                # 비공개 시험인 경우 권한 확인
                if not exam.is_public:
                    if not user.is_authenticated:
                        # 익명 사용자는 로그인 페이지로 리다이렉트
                        from django.http import HttpResponseRedirect
                        login_url = f"/login?returnTo={original_url}"
                        return HttpResponseRedirect(login_url)
                    
                    # admin_role 사용자는 모든 시험에 접근 가능
                    is_admin = hasattr(user, 'profile') and hasattr(user.profile, 'role') and user.profile.role == 'admin_role'
                    if not is_admin:
                        # 일반 사용자는 다음 조건 중 하나를 만족해야 함:
                        # 1. 시험 생성자
                        # 2. 스터디 멤버
                        # 3. 시험을 풀어본 적이 있음
                        
                        is_creator = exam.created_by == user if exam.created_by else False
                        study_membership = Member.objects.filter(
                            user=user,
                            study__tasks__exam=exam,
                            is_active=True
                        ).exists()
                        has_taken_exam = ExamResult.objects.filter(
                            user=user,
                            exam=exam
                        ).exists()
                        
                        if not is_creator and not study_membership and not has_taken_exam:
                            # 권한 없음 - 403 에러 페이지로 리다이렉트
                            from django.http import HttpResponse
                            return HttpResponse("이 시험에 접근할 권한이 없습니다.", status=403)
            except Exam.DoesNotExist:
                # 시험을 찾을 수 없으면 그냥 리다이렉트 (404는 나중에 처리됨)
                pass
            except Exception as e:
                logger.error(f"권한 확인 중 오류: {str(e)}")
                # 오류 발생 시 그냥 리다이렉트 (보안상 안전한 쪽으로)
                pass
        
        # 접근 횟수 증가
        short_url.increment_access_count()
        logger.info(f"리다이렉션: {short_url.original_url}")
        
        # 원본 URL로 리다이렉션
        return redirect(short_url.original_url)
        
    except ShortUrl.DoesNotExist:
        logger.error(f"단축 URL을 찾을 수 없음: {short_code}")
        from django.http import HttpResponse
        return HttpResponse("단축 URL을 찾을 수 없습니다.", status=404)
    except Exception as e:
        logger.error(f"단축 URL 리다이렉션 실패: {str(e)}")
        from django.http import HttpResponse
        return HttpResponse("단축 URL 처리에 실패했습니다.", status=500)
