"""
도메인 관련 유틸리티 함수들
"""
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)

# 캐시 키
DEVOPS_CATEGORY_CACHE_KEY = 'devops_category_id'
DEVOPS_CATEGORY_TAG_IDS_CACHE_KEY = 'devops_category_tag_ids'
DEVOPS_TAG_ID_CACHE_KEY = 'devops_tag_id'
CACHE_TIMEOUT = 3600  # 1시간


def get_request_domain(request):
    """
    요청에서 도메인 추출
    :param request: Django request 객체
    :return: str 도메인 이름
    """
    host = request.get_host().lower()
    # 포트 제거
    if ':' in host:
        host = host.split(':')[0]
    return host


def is_devops_domain(request):
    """
    요청이 DevOps 도메인에서 온 것인지 확인
    :param request: Django request 객체
    :return: bool DevOps 도메인 여부
    """
    domain = get_request_domain(request)
    return 'devops' in domain


def get_devops_category_id():
    """
    "IT 기술 > IT 기술" 카테고리 ID 반환 (캐싱)
    :return: int|None 카테고리 ID
    """
    # 캐시에서 확인
    category_id = cache.get(DEVOPS_CATEGORY_CACHE_KEY)
    if category_id:
        return category_id
    
    try:
        from quiz.models import TagCategory
        
        # 1단계 "IT 기술" 카테고리 찾기
        it_category_level1 = TagCategory.objects.filter(
            level=1,
            name_ko='IT 기술'
        ).first()
        
        if not it_category_level1:
            logger.warning("⚠️ 1단계 'IT 기술' 카테고리를 찾을 수 없습니다.")
            return None
        
        # 2단계 "IT 기술" 카테고리 찾기 (IT 기술 > IT 기술)
        it_tech_category = TagCategory.objects.filter(
            parent=it_category_level1,
            level=2,
            name_ko='IT 기술',
            order=6
        ).first()
        
        if it_tech_category:
            # 캐시에 저장
            cache.set(DEVOPS_CATEGORY_CACHE_KEY, it_tech_category.id, CACHE_TIMEOUT)
            return it_tech_category.id
        else:
            logger.warning("⚠️ 2단계 'IT 기술' 카테고리를 찾을 수 없습니다.")
            return None
            
    except Exception as e:
        logger.error(f"❌ DevOps 카테고리 ID 조회 중 오류: {str(e)}")
        return None


def get_devops_category_tag_ids():
    """
    "IT 기술 > IT 기술" 카테고리에 속한 모든 태그 ID 반환 (캐싱)
    :return: list[int] 태그 ID 목록
    """
    # 캐시에서 확인
    tag_ids = cache.get(DEVOPS_CATEGORY_TAG_IDS_CACHE_KEY)
    if tag_ids:
        return tag_ids
    
    category_id = get_devops_category_id()
    if not category_id:
        return []
    
    try:
        from quiz.models import Tag
        
        # 해당 카테고리에 속한 태그들 조회
        tags = Tag.objects.filter(categories__id=category_id).distinct()
        tag_ids = list(tags.values_list('id', flat=True))
        
        # 캐시에 저장
        cache.set(DEVOPS_CATEGORY_TAG_IDS_CACHE_KEY, tag_ids, CACHE_TIMEOUT)
        
        logger.info(f"✅ DevOps 카테고리 태그 ID 조회 완료: {len(tag_ids)}개")
        return tag_ids
        
    except Exception as e:
        logger.error(f"❌ DevOps 카테고리 태그 ID 조회 중 오류: {str(e)}")
        return []


def get_domain_tag_id(request, tag_name='DevOps'):
    """
    도메인별 태그 ID 반환 (캐싱)
    :param request: Django request 객체
    :param tag_name: 태그 이름 (기본값: 'DevOps')
    :return: int|None 태그 ID
    """
    if not is_devops_domain(request):
        return None
    
    # 캐시 키는 태그 이름별로 구분
    cache_key = f"{DEVOPS_TAG_ID_CACHE_KEY}_{tag_name}"
    
    # 캐시에서 확인
    tag_id = cache.get(cache_key)
    if tag_id:
        return tag_id
    
    try:
        from quiz.models import Tag
        
        # 모든 언어 필드에서 태그 찾기
        tag = Tag.objects.filter(
            name_ko=tag_name
        ).first()
        
        if not tag:
            # 영어로도 시도
            tag = Tag.objects.filter(
                name_en=tag_name
            ).first()
        
        if tag:
            # 캐시에 저장
            cache.set(cache_key, tag.id, CACHE_TIMEOUT)
            return tag.id
        else:
            logger.warning(f"⚠️ '{tag_name}' 태그를 찾을 수 없습니다.")
            return None
            
    except Exception as e:
        logger.error(f"❌ 태그 ID 조회 중 오류: {str(e)}")
        return None


def clear_domain_cache():
    """
    도메인 관련 캐시 모두 삭제
    """
    cache.delete(DEVOPS_CATEGORY_CACHE_KEY)
    cache.delete(DEVOPS_CATEGORY_TAG_IDS_CACHE_KEY)
    cache.delete_many([key for key in cache.keys() if key.startswith(DEVOPS_TAG_ID_CACHE_KEY)])

