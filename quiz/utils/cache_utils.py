"""
Redis를 활용한 고급 캐싱 전략

캐시 무효화 정책:
1. 시험 생성/삭제/수정 시: invalidate_all_exam_cache() 호출
2. 특정 시험 관련: invalidate_exam_cache(exam_id) 호출
3. 사용자별 시험: invalidate_user_exam_cache(user_id) 호출
4. 스터디 생성/삭제/수정 시: invalidate_all_study_cache() 호출
5. 특정 스터디 관련: invalidate_study_cache(study_id) 호출
6. 사용자별 스터디: invalidate_user_study_cache(user_id) 호출
7. 폴백 메커니즘: Redis 패턴 매칭 실패 시 로컬 캐시 클리어

캐시 계층:
- Redis 환경: delete_pattern을 사용한 효율적인 패턴 매칭
- 로컬 환경: cache.clear()로 전체 캐시 클리어
- 타임아웃: 기본 5분, 상세 정보는 10분
"""
import json
import hashlib
from django.core.cache import cache
from django.conf import settings
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


class StudyCacheManager:
    """스터디 데이터 캐싱을 위한 전용 매니저"""
    
    CACHE_PREFIX = "study"
    CACHE_TIMEOUT = 300  # 5분
    
    @classmethod
    def get_cache_key(cls, user_id: Union[int, str], **filters) -> str:
        """캐시 키 생성"""
        # 필터 파라미터를 정렬하여 일관된 키 생성
        filter_str = "_".join([f"{k}_{v}" for k, v in sorted(filters.items()) if v is not None])
        return f"{cls.CACHE_PREFIX}_{user_id}_{filter_str}"
    
    @classmethod
    def get_study_list_cache_key(cls, user_id: Union[int, str], study_type: str = 'all', 
                                is_public: str = 'all') -> str:
        """스터디 목록 캐시 키 생성"""
        return cls.get_cache_key(user_id, study_type=study_type, is_public=is_public)
    
    @classmethod
    def get_study_detail_cache_key(cls, study_id: int, user_id: Union[int, str]) -> str:
        """스터디 상세 정보 캐시 키 생성"""
        return f"{cls.CACHE_PREFIX}_detail_{study_id}_{user_id}"
    
    @classmethod
    def set_study_list_cache(cls, user_id: Union[int, str], data: Dict, 
                           study_type: str = 'all', is_public: str = 'all') -> bool:
        """스터디 목록 캐시 저장"""
        try:
            cache_key = cls.get_study_list_cache_key(user_id, study_type, is_public)
            cache.set(cache_key, data, cls.CACHE_TIMEOUT)
            logger.info(f"스터디 목록 캐시 저장 성공: {cache_key}")
            return True
        except Exception as e:
            logger.error(f"스터디 목록 캐시 저장 실패: {e}")
            return False
    
    @classmethod
    def get_study_list_cache(cls, user_id: Union[int, str], study_type: str = 'all', 
                           is_public: str = 'all') -> Optional[Dict]:
        """스터디 목록 캐시 조회"""
        try:
            cache_key = cls.get_study_list_cache_key(user_id, study_type, is_public)
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.info(f"스터디 목록 캐시 히트: {cache_key}")
                return cached_data
            logger.debug(f"스터디 목록 캐시 미스: {cache_key}")
            return None
        except Exception as e:
            logger.error(f"스터디 목록 캐시 조회 실패: {e}")
            return None
    
    @classmethod
    def set_study_detail_cache(cls, study_id: int, user_id: Union[int, str], data: Dict) -> bool:
        """스터디 상세 정보 캐시 저장"""
        try:
            cache_key = cls.get_study_detail_cache_key(study_id, user_id)
            cache.set(cache_key, data, cls.CACHE_TIMEOUT * 2)  # 상세 정보는 더 오래 캐시
            logger.info(f"스터디 상세 정보 캐시 저장 성공: {cache_key}")
            return True
        except Exception as e:
            logger.error(f"스터디 상세 정보 캐시 저장 실패: {e}")
            return False
    
    @classmethod
    def get_study_detail_cache(cls, study_id: int, user_id: Union[int, str]) -> Optional[Dict]:
        """스터디 상세 정보 캐시 조회"""
        try:
            cache_key = cls.get_study_detail_cache_key(study_id, user_id)
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.info(f"스터디 상세 정보 캐시 히트: {cache_key}")
                return cached_data
            logger.debug(f"스터디 상세 정보 캐시 미스: {cache_key}")
            return None
        except Exception as e:
            logger.error(f"스터디 상세 정보 캐시 조회 실패: {e}")
            return None
    
    @classmethod
    def invalidate_user_study_cache(cls, user_id: Union[int, str]) -> bool:
        """사용자의 모든 스터디 관련 캐시 무효화"""
        try:
            # Redis의 패턴 매칭을 사용하여 사용자 관련 캐시 삭제
            if hasattr(cache, 'delete_pattern'):
                pattern = f"{cls.CACHE_PREFIX}_{user_id}_*"
                cache.delete_pattern(pattern)
                logger.info(f"사용자 스터디 캐시 무효화 성공: {pattern}")
            else:
                # 로컬 캐시의 경우 전체 캐시 클리어
                cache.clear()
                logger.info(f"로컬 캐시 클리어 완료")
            return True
        except Exception as e:
            logger.error(f"사용자 스터디 캐시 무효화 실패: {e}")
            return False
    
    @classmethod
    def invalidate_study_cache(cls, study_id: int) -> bool:
        """특정 스터디 관련 캐시 무효화"""
        try:
            # Redis의 패턴 매칭을 사용하여 스터디 관련 캐시 삭제
            if hasattr(cache, 'delete_pattern'):
                # StudyViewSet에서 생성하는 캐시 키 패턴들
                patterns = [
                    "studies_*",  # StudyViewSet.list에서 생성하는 캐시
                    f"{cls.CACHE_PREFIX}_*",  # StudyCacheManager에서 생성하는 캐시
                ]
                
                for pattern in patterns:
                    cache.delete_pattern(pattern)
                    logger.info(f"스터디 캐시 무효화 성공: {pattern}")
            else:
                # 로컬 캐시의 경우 전체 캐시 클리어
                cache.clear()
                logger.info(f"로컬 캐시 클리어 완료")
            return True
        except Exception as e:
            logger.error(f"스터디 캐시 무효화 실패: {e}")
            return False
    
    @classmethod
    def invalidate_all_study_cache(cls) -> bool:
        """모든 스터디 관련 캐시 무효화"""
        try:
            # Redis의 패턴 매칭을 사용하여 모든 스터디 관련 캐시 삭제
            if hasattr(cache, 'delete_pattern'):
                # StudyViewSet에서 생성하는 캐시 키 패턴들
                patterns = [
                    "studies_*",  # StudyViewSet.list에서 생성하는 캐시
                    f"{cls.CACHE_PREFIX}_*",  # StudyCacheManager에서 생성하는 캐시
                ]
                
                for pattern in patterns:
                    cache.delete_pattern(pattern)
                    logger.debug(f"모든 스터디 캐시 무효화 성공: {pattern}")
            else:
                # 로컬 캐시의 경우 전체 캐시 클리어
                cache.clear()
                logger.info(f"로컬 캐시 클리어 완료")
            return True
        except Exception as e:
            logger.error(f"모든 스터디 캐시 무효화 실패: {e}")
            return False


class ExamCacheManager:
    """시험 데이터 캐싱을 위한 전용 매니저"""
    
    CACHE_PREFIX = "exam"
    CACHE_TIMEOUT = 300  # 5분
    
    @classmethod
    def get_cache_key(cls, user_id: Union[int, str], **filters) -> str:
        """캐시 키 생성"""
        # 필터 파라미터를 정렬하여 일관된 키 생성
        filter_str = "_".join([f"{k}_{v}" for k, v in sorted(filters.items()) if v is not None])
        return f"{cls.CACHE_PREFIX}_{user_id}_{filter_str}"
    
    @classmethod
    def get_exam_list_cache_key(cls, user_id: Union[int, str], page: int = 1, 
                               page_size: int = 20, **filters) -> str:
        """시험 목록 캐시 키 생성"""
        return cls.get_cache_key(user_id, page=page, page_size=page_size, **filters)
    
    @classmethod
    def get_exam_detail_cache_key(cls, exam_id: str, user_id: Union[int, str]) -> str:
        """시험 상세 정보 캐시 키 생성"""
        return f"{cls.CACHE_PREFIX}_detail_{exam_id}_{user_id}"
    
    @classmethod
    def set_exam_list_cache(cls, user_id: Union[int, str], data: Dict, 
                           page: int = 1, page_size: int = 20, **filters) -> bool:
        """시험 목록 캐시 저장"""
        try:
            cache_key = cls.get_exam_list_cache_key(user_id, page, page_size, **filters)
            cache.set(cache_key, data, cls.CACHE_TIMEOUT)
            logger.info(f"시험 목록 캐시 저장 성공: {cache_key}")
            return True
        except Exception as e:
            logger.error(f"시험 목록 캐시 저장 실패: {e}")
            return False
    
    @classmethod
    def get_exam_list_cache(cls, user_id: Union[int, str], page: int = 1, 
                           page_size: int = 20, **filters) -> Optional[Dict]:
        """시험 목록 캐시 조회"""
        try:
            cache_key = cls.get_exam_list_cache_key(user_id, page, page_size, **filters)
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.info(f"시험 목록 캐시 히트: {cache_key}")
                return cached_data
            logger.debug(f"시험 목록 캐시 미스: {cache_key}")
            return None
        except Exception as e:
            logger.error(f"시험 목록 캐시 조회 실패: {e}")
            return None
    
    @classmethod
    def set_exam_detail_cache(cls, exam_id: str, user_id: Union[int, str], data: Dict) -> bool:
        """시험 상세 정보 캐시 저장"""
        try:
            cache_key = cls.get_exam_detail_cache_key(exam_id, user_id)
            cache.set(cache_key, data, cls.CACHE_TIMEOUT * 2)  # 상세 정보는 더 오래 캐시
            logger.info(f"시험 상세 정보 캐시 저장 성공: {cache_key}")
            return True
        except Exception as e:
            logger.error(f"시험 상세 정보 캐시 저장 실패: {e}")
            return False
    
    @classmethod
    def get_exam_detail_cache(cls, exam_id: str, user_id: Union[int, str]) -> Optional[Dict]:
        """시험 상세 정보 캐시 조회"""
        try:
            cache_key = cls.get_exam_detail_cache_key(exam_id, user_id)
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.info(f"시험 상세 정보 캐시 히트: {cache_key}")
                return cached_data
            logger.debug(f"시험 상세 정보 캐시 미스: {cache_key}")
            return None
        except Exception as e:
            logger.error(f"시험 상세 정보 캐시 조회 실패: {e}")
            return None
    
    @classmethod
    def invalidate_user_exam_cache(cls, user_id: Union[int, str]) -> bool:
        """사용자의 모든 시험 관련 캐시 무효화"""
        try:
            # Redis의 패턴 매칭을 사용하여 사용자 관련 캐시 삭제
            if hasattr(cache, 'delete_pattern'):
                pattern = f"{cls.CACHE_PREFIX}_{user_id}_*"
                cache.delete_pattern(pattern)
                logger.info(f"사용자 시험 캐시 무효화 성공: {pattern}")
            else:
                # 로컬 캐시의 경우 전체 캐시 클리어
                cache.clear()
                logger.info(f"로컬 캐시 클리어 완료")
            return True
        except Exception as e:
            logger.error(f"사용자 시험 캐시 무효화 실패: {e}")
            return False
    
    @classmethod
    def invalidate_exam_cache(cls, exam_id: str) -> bool:
        """특정 시험 관련 캐시 무효화"""
        try:
            # Redis의 패턴 매칭을 사용하여 시험 관련 캐시 삭제
            if hasattr(cache, 'delete_pattern'):
                pattern = f"{cls.CACHE_PREFIX}_*_{exam_id}_*"
                cache.delete_pattern(pattern)
                logger.info(f"시험 캐시 무효화 성공: {pattern}")
            else:
                # 로컬 캐시의 경우 전체 캐시 클리어
                cache.clear()
                logger.info(f"로컬 캐시 클리어 완료")
            return True
        except Exception as e:
            logger.error(f"시험 캐시 무효화 실패: {e}")
            return False

    @classmethod
    def invalidate_all_exam_cache(cls) -> bool:
        """모든 시험 관련 캐시 무효화"""
        try:
            # Redis의 패턴 매칭을 사용하여 모든 시험 관련 캐시 삭제
            if hasattr(cache, 'delete_pattern'):
                pattern = f"{cls.CACHE_PREFIX}_*"
                cache.delete_pattern(pattern)
                logger.info(f"모든 시험 캐시 무효화 성공: {pattern}")
            else:
                # 로컬 캐시의 경우 전체 캐시 클리어
                cache.clear()
                logger.info(f"로컬 캐시 클리어 완료")
            return True
        except Exception as e:
            logger.error(f"모든 시험 캐시 무효화 실패: {e}")
            return False


class CacheDecorator:
    """캐싱을 위한 데코레이터"""
    
    @staticmethod
    def cache_result(timeout: int = 300, key_func=None):
        """함수 결과를 캐싱하는 데코레이터"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                # 캐시 키 생성
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    # 기본 캐시 키 생성
                    func_name = func.__name__
                    args_str = "_".join([str(arg) for arg in args])
                    kwargs_str = "_".join([f"{k}_{v}" for k, v in sorted(kwargs.items())])
                    cache_key = f"{func_name}_{args_str}_{kwargs_str}"
                
                # 캐시에서 조회
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"캐시 히트: {cache_key}")
                    return cached_result
                
                # 함수 실행
                result = func(*args, **kwargs)
                
                # 결과 캐싱
                try:
                    cache.set(cache_key, result, timeout)
                    logger.debug(f"캐시 저장: {cache_key}")
                except Exception as e:
                    logger.warning(f"캐시 저장 실패: {e}")
                
                return result
            return wrapper
        return decorator


class QueryOptimizer:
    """데이터베이스 쿼리 최적화 유틸리티"""
    
    @staticmethod
    def optimize_exam_queryset(queryset, select_fields: List[str] = None):
        """시험 쿼리셋 최적화"""
        # 기본 select_related
        queryset = queryset.select_related('original_exam', 'created_by')
        
        # tags는 항상 prefetch (ExamListSerializer에서 사용)
        # tags의 categories도 함께 prefetch하여 N+1 쿼리 방지
        queryset = queryset.prefetch_related('tags', 'tags__categories')
        
        # select_fields에 따라 prefetch_related 적용
        if not select_fields or 'questions' in select_fields:
            queryset = queryset.prefetch_related('questions')
        
        if not select_fields or 'versions' in select_fields:
            queryset = queryset.prefetch_related('versions')
        
        if not select_fields or 'studies' in select_fields:
            # StudyTask를 통해 연결된 스터디 정보는 필요시에만 조회
            # Exam 모델에는 studytask 관계가 없으므로 제거
            pass
        
        return queryset
    
    @staticmethod
    def get_optimized_exam_fields(include_detail: bool = False) -> List[str]:
        """최적화된 시험 필드 목록 반환"""
        if include_detail:
            return [
                'id', 'title', 'description', 'created_at', 'is_original', 
                'original_exam', 'version_number', 'is_public', 'created_by',
                'questions', 'versions'
            ]
        else:
            return [
                'id', 'title', 'created_at', 'is_original', 'original_exam',
                'version_number', 'is_public', 'total_questions'
            ]


def get_cache_stats() -> Dict[str, Any]:
    """캐시 통계 정보 반환"""
    try:
        if hasattr(cache, 'client'):
            # Redis 클라이언트 정보
            client_info = cache.client.info()
            return {
                'type': 'redis',
                'connected_clients': client_info.get('connected_clients', 0),
                'used_memory': client_info.get('used_memory_human', 'N/A'),
                'total_commands_processed': client_info.get('total_commands_processed', 0),
                'keyspace_hits': client_info.get('keyspace_hits', 0),
                'keyspace_misses': client_info.get('keyspace_misses', 0),
            }
        else:
            # 로컬 캐시 정보
            return {
                'type': 'local',
                'backend': str(cache),
                'note': '로컬 메모리 캐시 사용 중'
            }
    except Exception as e:
        logger.error(f"캐시 통계 조회 실패: {e}")
        return {
            'type': 'unknown',
            'error': str(e)
        }
