"""
커스텀 Redis 캐시 백엔드
FLUSHDB 명령어를 사용하지 않고 개별 키 삭제를 사용
"""

from django_redis.cache import RedisCache
from django_redis.client import DefaultClient
from django.core.cache.backends.base import InvalidCacheBackendError
import logging

logger = logging.getLogger(__name__)


class SafeRedisClient(DefaultClient):
    """
    FLUSHDB 명령어를 사용하지 않는 안전한 Redis 클라이언트
    """
    
    def clear(self, version=None):
        """
        FLUSHDB 대신 개별 키 삭제를 사용하여 캐시를 정리
        """
        try:
            # 키 패턴을 사용하여 개별 키 삭제
            pattern = self.make_key('*', version=version)
            keys = self.connection.keys(pattern)
            
            if keys:
                # 개별 키 삭제
                deleted_count = 0
                for key in keys:
                    try:
                        if self.connection.delete(key):
                            deleted_count += 1
                    except Exception as e:
                        logger.warning(f"키 삭제 실패: {key}, 에러: {e}")
                        continue
                
                logger.info(f"캐시 정리 완료: {deleted_count}개 키 삭제됨")
                return deleted_count
            else:
                logger.info("삭제할 캐시 키가 없습니다.")
                return 0
                
        except Exception as e:
            logger.error(f"캐시 정리 중 오류 발생: {e}")
            # 오류가 발생해도 애플리케이션이 중단되지 않도록 함
            return 0


class SafeRedisCache(RedisCache):
    """
    안전한 Redis 캐시 백엔드
    """
    
    def __init__(self, server, params):
        super().__init__(server, params)
        # 커스텀 클라이언트 클래스 사용
        self._client_class = SafeRedisClient


# Django 캐시 백엔드로 등록
CACHE_BACKEND = 'quiz.cache_backend.SafeRedisCache'
