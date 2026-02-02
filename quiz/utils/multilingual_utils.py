#!/usr/bin/env python3
"""
다국어 처리를 위한 공통 유틸리티 모듈

이 모듈은 Django 모델의 다국어 필드를 효율적으로 처리하기 위한
공통 기능들을 제공합니다.

주요 기능:
1. 다국어 콘텐츠 변경 감지
2. 자동 번역 처리 (배치 번역 지원) - 사용자 프로필의 번역 활성화 여부에 따라 수행
3. 언어별 완성도 상태 관리
4. 다국어 응답 데이터 생성
5. 대량 문제 배치 번역 최적화

중요: 번역 처리 규칙
- 사용자의 프로필에 번역이 활성화되어 있을 경우에만 번역을 수행합니다.
- 번역이 비활성화된 사용자가 시험을 생성할 경우에는 번역 처리를 수행하지 않습니다.
- en 모드가 아닌 언어(예: ko, es, zh, ja)로 생성된 시험은 en으로 번역되어야 하며,
  supported_language에 en도 포함되어야 합니다 (예: ko,en).
- 시험이 생성되는 시점 (매뉴얼 생성, 자동생성)과 en 모드로 시험을 로딩하는 시점에
  번역이 필요한지 확인하고 번역을 수행합니다.

사용 예시:
```python
from quiz.utils.multilingual_utils import MultilingualContentManager

class StudyViewSet(viewsets.ModelViewSet):
    def perform_update(self, serializer):
        study = serializer.save()
        
        # 다국어 콘텐츠 자동 처리 (사용자의 번역 활성화 여부에 따라 자동으로 처리됨)
        manager = MultilingualContentManager(study, self.request.user)
        manager.handle_multilingual_update()
```

작성일: 2025-08-17
작성자: AI Assistant
"""

import logging
from typing import Dict, List, Tuple, Optional, Any
from django.conf import settings
from django.core.cache import cache
import requests
import json
import time
import gc
import re
import os
import yaml

logger = logging.getLogger(__name__)

# ============================================================================
# 다국어 지원 언어 상수
# ============================================================================
# 지원하는 모든 언어 코드
SUPPORTED_LANGUAGES = ['ko', 'en', 'es', 'zh', 'ja']

# 개별 언어 코드 상수 (타입 체크 및 오타 방지)
LANGUAGE_KO = 'ko'
LANGUAGE_EN = 'en'
LANGUAGE_ES = 'es'
LANGUAGE_ZH = 'zh'
LANGUAGE_JA = 'ja'

# 기본 언어 (영어를 기본 언어로 사용)
BASE_LANGUAGE = LANGUAGE_EN

# OpenAI 실패 상태 관리 (Django 캐시 사용 - 앱 전체에서 공유)
OPENAI_UNAVAILABLE_CACHE_TTL = 3600  # 1시간 (초)
OPENAI_UNAVAILABLE_CACHE_KEY = 'openai_unavailable_status'  # 캐시 키
_openai_unavailable_status = False  # OpenAI 사용 불가능 여부 (하위 호환성 유지)
_openai_unavailable_timestamp = 0  # 마지막으로 사용 불가능으로 마킹된 시간 (하위 호환성 유지)

__all__ = [
    'SUPPORTED_LANGUAGES',
    'LANGUAGE_KO',
    'LANGUAGE_EN',
    'LANGUAGE_ES',
    'LANGUAGE_ZH',
    'LANGUAGE_JA',
    'BASE_LANGUAGE',
    'MultilingualContentManager', 
    'get_user_language',
    'get_localized_field',
    'get_localized_admin_label',
    'get_localized_fieldset_title',
    'get_completion_fields',
    'get_multilingual_search_fields',
    'get_multilingual_fields',
    'batch_translate_texts',
    'batch_translate_questions',
    'process_large_question_batch',
    'smart_translate_content',
    'is_choice_format',
    'translate_choices_with_format',
    'is_auto_translation_enabled',
    'check_answer_with_ai'
]

# 배치 번역 설정
BATCH_SIZE = 50  # OpenAI API 한 번에 처리할 수 있는 적절한 크기
MAX_RETRIES = 3  # 최대 재시도 횟수
RETRY_DELAY = 2  # 재시도 간격 (초)

def check_openai_availability() -> bool:
    """
    OpenAI API 사용 가능 여부를 Django 캐시와 전역 변수에서 확인합니다.
    캐시가 없으면 전역 변수를 확인하고, 둘 다 없으면 사용 가능한 것으로 간주합니다.
    
    Returns:
        bool: OpenAI가 사용 가능하면 True, 사용 불가능하면 False
    """
    # 1. Django 캐시에서 확인 (TTL이 자동으로 관리됨)
    try:
        cached_status = cache.get(OPENAI_UNAVAILABLE_CACHE_KEY)
        if cached_status is not None:
            logger.warning(f"[OPENAI_CACHE] ⚠️ OpenAI 사용 불가능 상태 확인됨 (Django 캐시, 값: {cached_status}) - Gemini로 전환해야 함")
            return False
    except Exception as e:
        logger.warning(f"[OPENAI_CACHE] ⚠️ Django 캐시 확인 중 예외 발생: {e}, 전역 변수로 fallback")
    
    # 2. 전역 변수 확인 (캐시 실패 시 fallback)
    global _openai_unavailable_status, _openai_unavailable_timestamp
    if _openai_unavailable_status:
        # TTL 확인 (1시간 = 3600초)
        elapsed_time = time.time() - _openai_unavailable_timestamp
        if elapsed_time < OPENAI_UNAVAILABLE_CACHE_TTL:
            remaining_time = int(OPENAI_UNAVAILABLE_CACHE_TTL - elapsed_time)
            logger.warning(f"[OPENAI_CACHE] ⚠️ OpenAI 사용 불가능 상태 확인됨 (전역 변수, 남은 시간: {remaining_time}초) - Gemini로 전환해야 함")
            return False
        else:
            # TTL이 지났으면 사용 가능 상태로 복구
            logger.info(f"[OPENAI_CACHE] ✅ OpenAI TTL 만료, 사용 가능 상태로 복구 (경과 시간: {int(elapsed_time)}초)")
            _openai_unavailable_status = False
            _openai_unavailable_timestamp = 0
    
    # 캐시와 전역 변수 모두 없거나 TTL이 지났으면 사용 가능
    logger.info(f"[OPENAI_CACHE] ✅ OpenAI 사용 가능 상태 (캐시/전역 변수 모두 없음 또는 TTL 만료)")
    return True


def mark_openai_unavailable(ttl: int = OPENAI_UNAVAILABLE_CACHE_TTL) -> None:
    """
    OpenAI API를 사용 불가능 상태로 Django 캐시에 마킹합니다.
    
    Args:
        ttl: TTL (초 단위), 기본값 1시간
    """
    # 하위 호환성을 위해 전역 변수 먼저 업데이트 (캐시 실패 시에도 작동)
    global _openai_unavailable_status, _openai_unavailable_timestamp
    _openai_unavailable_status = True
    _openai_unavailable_timestamp = time.time()
    
    # Django 캐시에 저장 시도 (TTL 자동 관리)
    try:
        # 캐시 백엔드 정보 로깅 (디버깅용)
        from django.conf import settings
        cache_backend = settings.CACHES.get('default', {}).get('BACKEND', 'unknown')
        logger.info(f"[OPENAI_CACHE] 🔧 캐시 백엔드: {cache_backend}")
        logger.info(f"[OPENAI_CACHE] 🔧 캐시 키: {OPENAI_UNAVAILABLE_CACHE_KEY}, TTL: {ttl}초")
        
        # 캐시 저장 시도
        cache.set(OPENAI_UNAVAILABLE_CACHE_KEY, True, timeout=ttl)
        logger.debug(f"[OPENAI_CACHE] cache.set() 호출 완료")
        
        # 캐시 설정 후 즉시 확인하여 제대로 설정되었는지 검증
        verify_status = cache.get(OPENAI_UNAVAILABLE_CACHE_KEY)
        logger.debug(f"[OPENAI_CACHE] cache.get() 결과: {verify_status}")
        
        if verify_status is not None:
            logger.warning(f"[OPENAI_CACHE] ✅ OpenAI를 {ttl}초(1시간)간 사용 불가능 상태로 마킹 완료 (Django 캐시, 검증: {verify_status})")
        else:
            # 캐시 저장 실패 - 전역 변수로 fallback
            logger.error(f"[OPENAI_CACHE] ⚠️ Django 캐시 저장 실패 (cache.get()이 None 반환), 전역 변수로 fallback")
            logger.error(f"[OPENAI_CACHE] 🔍 캐시 백엔드: {cache_backend}")
            logger.error(f"[OPENAI_CACHE] 🔍 캐시 키: {OPENAI_UNAVAILABLE_CACHE_KEY}")
            logger.warning(f"[OPENAI_CACHE] ✅ 전역 변수로 OpenAI 사용 불가능 상태 마킹 완료 (TTL: {ttl}초)")
            
            # 추가 디버깅: 다른 키로 테스트
            try:
                test_key = 'openai_cache_test'
                cache.set(test_key, 'test_value', 10)
                test_result = cache.get(test_key)
                if test_result == 'test_value':
                    logger.warning(f"[OPENAI_CACHE] 🔍 다른 키로 캐시 테스트 성공 - 특정 키 문제일 수 있음")
                else:
                    logger.error(f"[OPENAI_CACHE] 🔍 다른 키로 캐시 테스트 실패 - 캐시 백엔드 문제 가능성")
                cache.delete(test_key)
            except Exception as test_e:
                logger.error(f"[OPENAI_CACHE] 🔍 캐시 테스트 중 예외: {test_e}")
                
    except Exception as e:
        logger.error(f"[OPENAI_CACHE] ❌ Django 캐시 저장 중 예외 발생: {e}", exc_info=True)
        logger.warning(f"[OPENAI_CACHE] ✅ 전역 변수로 OpenAI 사용 불가능 상태 마킹 완료 (TTL: {ttl}초)")


def get_user_language(request_or_user) -> str:
    """
    사용자의 언어 설정을 가져오는 공유 유틸 함수
    
    Args:
        request_or_user: Django request 객체 또는 user 인스턴스
    
    Returns:
        str: 사용자 언어, 기본값은 'en'
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # request 객체인 경우 user 추출
        if hasattr(request_or_user, 'user'):
            user = request_or_user.user
        else:
            user = request_or_user
        
        # 익명 사용자 체크
        if not user or user.is_anonymous:
            logger.debug(f"[GET_USER_LANGUAGE] 익명 사용자, 기본값 반환: {BASE_LANGUAGE}")
            return BASE_LANGUAGE
        
        # 사용자 프로필에서 언어 설정 가져오기
        if hasattr(user, 'userprofile'):
            language = user.userprofile.language
            logger.debug(f"[GET_USER_LANGUAGE] userprofile에서 언어 가져옴: {language}, user: {user.username}")
            return language
        elif hasattr(user, 'profile'):
            language = user.profile.language
            logger.debug(f"[GET_USER_LANGUAGE] profile에서 언어 가져옴: {language}, user: {user.username}")
            return language
        else:
            logger.debug(f"[GET_USER_LANGUAGE] 프로필 없음, 기본값 반환: {BASE_LANGUAGE}, user: {user.username}")
    except Exception as e:
        logger.debug(f"[GET_USER_LANGUAGE] 예외 발생: {str(e)}, 기본값 반환: {BASE_LANGUAGE}")
        pass
    return BASE_LANGUAGE


def get_localized_field(obj, field_name: str, user_language: str = None, default_value: str = None) -> str:
    """
    객체의 다국어 필드에서 사용자 언어에 맞는 값을 반환합니다.
    
    Args:
        obj: 다국어 필드를 가진 객체 (예: Exam, Question, Tag, Study 등)
        field_name: 필드 이름 (예: 'title', 'name', 'content', 'description')
        user_language: 사용자 언어 코드. None이면 BASE_LANGUAGE 사용
        default_value: 모든 언어 필드가 없을 때 반환할 기본값. None이면 언어별 기본값 사용
    
    Returns:
        str: 사용자 언어에 맞는 필드 값 또는 fallback 값
    
    사용 예시:
        # Exam 객체의 제목 가져오기 (언어별 기본값 자동 사용)
        title = get_localized_field(exam, 'title', 'en')
        
        # Tag 객체의 이름 가져오기 (커스텀 기본값 사용)
        name = get_localized_field(tag, 'name', 'ko', '태그명 없음')
    """
    if user_language is None:
        user_language = BASE_LANGUAGE
    
    # 필드명에 언어 코드를 붙여서 접근
    field_ko = getattr(obj, f'{field_name}_ko', None)
    field_en = getattr(obj, f'{field_name}_en', None)
    field_es = getattr(obj, f'{field_name}_es', None)
    field_zh = getattr(obj, f'{field_name}_zh', None)
    field_ja = getattr(obj, f'{field_name}_ja', None)
    
    # 기본값이 없으면 언어별 기본값 생성
    if default_value is None:
        # 필드명에 따른 언어별 기본값
        if field_name == 'title':
            default_values = {
                LANGUAGE_KO: '제목 없음',
                LANGUAGE_EN: 'No Title',
                LANGUAGE_ES: 'Sin título',
                LANGUAGE_ZH: '无标题',
                LANGUAGE_JA: 'タイトルなし'
            }
        elif field_name == 'name':
            default_values = {
                LANGUAGE_KO: '이름 없음',
                LANGUAGE_EN: 'No Name',
                LANGUAGE_ES: 'Sin nombre',
                LANGUAGE_ZH: '无名称',
                LANGUAGE_JA: '名前なし'
            }
        elif field_name == 'content':
            default_values = {
                LANGUAGE_KO: '내용 없음',
                LANGUAGE_EN: 'No Content',
                LANGUAGE_ES: 'Sin contenido',
                LANGUAGE_ZH: '无内容',
                LANGUAGE_JA: 'コンテンツなし'
            }
        elif field_name == 'description':
            default_values = {
                LANGUAGE_KO: '설명 없음',
                LANGUAGE_EN: 'No Description',
                LANGUAGE_ES: 'Sin descripción',
                LANGUAGE_ZH: '无描述',
                LANGUAGE_JA: '説明なし'
            }
        else:
            # 알 수 없는 필드명인 경우 영어 기본값 사용
            default_values = {
                LANGUAGE_KO: '없음',
                LANGUAGE_EN: 'N/A',
                LANGUAGE_ES: 'N/A',
                LANGUAGE_ZH: '无',
                LANGUAGE_JA: 'なし'
            }
        default_value = default_values.get(user_language, default_values[BASE_LANGUAGE])
    
    # 사용자 언어에 맞는 필드 선택 (fallback 순서 포함)
    if user_language == LANGUAGE_KO:
        return field_ko or field_en or default_value
    elif user_language == LANGUAGE_EN:
        return field_en or field_ko or default_value
    elif user_language == LANGUAGE_ES:
        return field_es or field_en or field_ko or default_value
    elif user_language == LANGUAGE_ZH:
        return field_zh or field_en or field_ko or default_value
    elif user_language == LANGUAGE_JA:
        return field_ja or field_en or field_ko or default_value
    else:
        # 기본값: 영어 우선
        return field_en or field_ko or default_value


def get_multilingual_search_fields(field_names: List[str]) -> List[str]:
    """
    Django admin의 search_fields를 위한 다국어 필드 목록을 자동 생성합니다.
    
    Args:
        field_names: 필드 이름 목록 (예: ['title', 'content'])
    
    Returns:
        List[str]: 모든 언어 필드 목록 (예: ['title_ko', 'title_en', 'title_es', 'title_zh', 'title_ja', ...])
    
    사용 예시:
        # Django admin에서 사용
        class QuestionAdmin(admin.ModelAdmin):
            search_fields = get_multilingual_search_fields(['title', 'content'])
            # 결과: ['title_ko', 'title_en', 'title_es', 'title_zh', 'title_ja',
            #        'content_ko', 'content_en', 'content_es', 'content_zh', 'content_ja']
    """
    search_fields = []
    for field_name in field_names:
        for lang in SUPPORTED_LANGUAGES:
            search_fields.append(f'{field_name}_{lang}')
    return search_fields


def get_localized_admin_label(field_name: str, user_language: str = None) -> str:
    """
    Django admin의 short_description을 위한 다국어 레이블을 반환합니다.
    
    Args:
        field_name: 필드 이름 (예: 'title', 'name', 'is_ko_complete')
        user_language: 사용자 언어 코드. None이면 BASE_LANGUAGE 사용
    
    Returns:
        str: 사용자 언어에 맞는 레이블
    
    사용 예시:
        # Django admin에서 사용
        class QuestionAdmin(MultilingualAdminMixin, admin.ModelAdmin):
            def changelist_view(self, request, extra_context=None):
                self.request = request
                user_language = self._get_user_language()
                self.get_title.short_description = get_localized_admin_label('title', user_language)
                return super().changelist_view(request, extra_context)
    """
    if user_language is None:
        user_language = BASE_LANGUAGE
    
    # 필드명에 따른 언어별 레이블
    labels = {
        'title': {
            LANGUAGE_KO: '제목',
            LANGUAGE_EN: 'Title',
            LANGUAGE_ES: 'Título',
            LANGUAGE_ZH: '标题',
            LANGUAGE_JA: 'タイトル'
        },
        'name': {
            LANGUAGE_KO: '이름',
            LANGUAGE_EN: 'Name',
            LANGUAGE_ES: 'Nombre',
            LANGUAGE_ZH: '名称',
            LANGUAGE_JA: '名前'
        },
        'content': {
            LANGUAGE_KO: '내용',
            LANGUAGE_EN: 'Content',
            LANGUAGE_ES: 'Contenido',
            LANGUAGE_ZH: '内容',
            LANGUAGE_JA: 'コンテンツ'
        },
        'description': {
            LANGUAGE_KO: '설명',
            LANGUAGE_EN: 'Description',
            LANGUAGE_ES: 'Descripción',
            LANGUAGE_ZH: '描述',
            LANGUAGE_JA: '説明'
        },
        'is_ko_complete': {
            LANGUAGE_KO: '한국어 완성',
            LANGUAGE_EN: 'Korean Complete',
            LANGUAGE_ES: 'Coreano Completo',
            LANGUAGE_ZH: '韩语完成',
            LANGUAGE_JA: '韓国語完了'
        },
        'is_en_complete': {
            LANGUAGE_KO: '영어 완성',
            LANGUAGE_EN: 'English Complete',
            LANGUAGE_ES: 'Inglés Completo',
            LANGUAGE_ZH: '英语完成',
            LANGUAGE_JA: '英語完了'
        },
        'is_es_complete': {
            LANGUAGE_KO: '스페인어 완성',
            LANGUAGE_EN: 'Spanish Complete',
            LANGUAGE_ES: 'Español Completo',
            LANGUAGE_ZH: '西班牙语完成',
            LANGUAGE_JA: 'スペイン語完了'
        },
        'is_zh_complete': {
            LANGUAGE_KO: '중국어 완성',
            LANGUAGE_EN: 'Chinese Complete',
            LANGUAGE_ES: 'Chino Completo',
            LANGUAGE_ZH: '中文完成',
            LANGUAGE_JA: '中国語完了'
        },
        'is_ja_complete': {
            LANGUAGE_KO: '일본어 완성',
            LANGUAGE_EN: 'Japanese Complete',
            LANGUAGE_ES: 'Japonés Completo',
            LANGUAGE_ZH: '日语完成',
            LANGUAGE_JA: '日本語完了'
        }
    }
    
    field_labels = labels.get(field_name, {
        LANGUAGE_KO: '필드',
        LANGUAGE_EN: 'Field',
        LANGUAGE_ES: 'Campo',
        LANGUAGE_ZH: '字段',
        LANGUAGE_JA: 'フィールド'
    })
    
    return field_labels.get(user_language, field_labels[BASE_LANGUAGE])


def get_completion_fields(languages: List[str] = None, model=None) -> List[str]:
    """
    완성도 필드 목록을 자동 생성합니다.
    모델이 제공되면 실제로 존재하는 필드만 반환합니다.
    
    Args:
        languages: 포함할 언어 목록. None이면 모든 지원 언어 사용
        model: Django 모델 클래스. 제공되면 실제로 존재하는 필드만 반환
    
    Returns:
        List[str]: 완성도 필드 목록 (예: ['is_ko_complete', 'is_en_complete', ...])
    
    사용 예시:
        # 모든 언어의 완성도 필드
        completion_fields = get_completion_fields()
        # 결과: ['is_ko_complete', 'is_en_complete', 'is_es_complete', 'is_zh_complete', 'is_ja_complete']
        
        # 특정 언어만
        completion_fields = get_completion_fields(['ko', 'en'])
        # 결과: ['is_ko_complete', 'is_en_complete']
        
        # 특정 모델에 맞는 언어만 (필요한 경우)
        # completion_fields = get_completion_fields(['ko', 'en'])
        # 결과: ['is_ko_complete', 'is_en_complete']
    """
    if languages is None:
        languages = SUPPORTED_LANGUAGES
    
    completion_fields = [f'is_{lang}_complete' for lang in languages]
    
    # 모델이 제공되면 실제로 존재하는 필드만 필터링
    if model:
        existing_fields = set(field.name for field in model._meta.get_fields())
        completion_fields = [field for field in completion_fields if field in existing_fields]
    
    return completion_fields


def get_localized_fieldset_title(title_key: str, user_language: str = None) -> str:
    """
    Django admin fieldsets의 제목을 위한 다국어 레이블을 반환합니다.
    
    Args:
        title_key: 필드셋 제목 키 (예: 'basic_info', 'settings', 'completion')
        user_language: 사용자 언어 코드. None이면 BASE_LANGUAGE 사용
    
    Returns:
        str: 사용자 언어에 맞는 필드셋 제목
    
    사용 예시:
        # Django admin fieldsets에서 사용
        class ExamAdmin(MultilingualAdminMixin, admin.ModelAdmin):
            def get_fieldsets(self, request, obj=None):
                user_language = self._get_user_language()
                return [
                    (get_localized_fieldset_title('basic_info', user_language), {
                        'fields': get_multilingual_fields(['title', 'description'])
                    }),
                ]
    """
    if user_language is None:
        user_language = BASE_LANGUAGE
    
    # 필드셋 제목 키에 따른 언어별 레이블
    titles = {
        'basic_info': {
            LANGUAGE_KO: '기본 정보',
            LANGUAGE_EN: 'Basic Information',
            LANGUAGE_ES: 'Información Básica',
            LANGUAGE_ZH: '基本信息',
            LANGUAGE_JA: '基本情報'
        },
        'settings': {
            LANGUAGE_KO: '설정',
            LANGUAGE_EN: 'Settings',
            LANGUAGE_ES: 'Configuración',
            LANGUAGE_ZH: '设置',
            LANGUAGE_JA: '設定'
        },
        'tags': {
            LANGUAGE_KO: '태그',
            LANGUAGE_EN: 'Tags',
            LANGUAGE_ES: 'Etiquetas',
            LANGUAGE_ZH: '标签',
            LANGUAGE_JA: 'タグ'
        },
        'tag_info': {
            LANGUAGE_KO: '태그 정보',
            LANGUAGE_EN: 'Tag Information',
            LANGUAGE_ES: 'Información de Etiqueta',
            LANGUAGE_ZH: '标签信息',
            LANGUAGE_JA: 'タグ情報'
        },
        'schedule': {
            LANGUAGE_KO: '일정',
            LANGUAGE_EN: 'Schedule',
            LANGUAGE_ES: 'Calendario',
            LANGUAGE_ZH: '日程',
            LANGUAGE_JA: 'スケジュール'
        },
        'completion': {
            LANGUAGE_KO: '완성도',
            LANGUAGE_EN: 'Completion',
            LANGUAGE_ES: 'Finalización',
            LANGUAGE_ZH: '完成度',
            LANGUAGE_JA: '完了度'
        },
        'meta_info': {
            LANGUAGE_KO: '메타 정보',
            LANGUAGE_EN: 'Meta Information',
            LANGUAGE_ES: 'Información Meta',
            LANGUAGE_ZH: '元信息',
            LANGUAGE_JA: 'メタ情報'
        },
        'connection': {
            LANGUAGE_KO: '연결',
            LANGUAGE_EN: 'Connection',
            LANGUAGE_ES: 'Conexión',
            LANGUAGE_ZH: '连接',
            LANGUAGE_JA: '接続'
        },
        'progress': {
            LANGUAGE_KO: '진행률',
            LANGUAGE_EN: 'Progress',
            LANGUAGE_ES: 'Progreso',
            LANGUAGE_ZH: '进度',
            LANGUAGE_JA: '進捗'
        }
    }
    
    fieldset_titles = titles.get(title_key, {
        LANGUAGE_KO: '필드셋',
        LANGUAGE_EN: 'Fieldset',
        LANGUAGE_ES: 'Conjunto de Campos',
        LANGUAGE_ZH: '字段集',
        LANGUAGE_JA: 'フィールドセット'
    })
    
    return fieldset_titles.get(user_language, fieldset_titles[BASE_LANGUAGE])


def get_multilingual_fields(field_names: List[str], other_fields: List[str] = None) -> tuple:
    """
    Django admin의 fieldsets fields를 위한 다국어 필드 목록을 자동 생성합니다.
    
    Args:
        field_names: 다국어 필드 이름 목록 (예: ['title', 'description'])
        other_fields: 추가로 포함할 다른 필드 목록 (예: ['total_questions', 'created_by'])
    
    Returns:
        tuple: 모든 언어 필드와 다른 필드를 포함한 튜플
              (예: ('title_ko', 'title_en', 'title_es', 'title_zh', 'title_ja',
                    'description_ko', 'description_en', 'description_es', 'description_zh', 'description_ja',
                    'total_questions', 'created_by'))
    
    사용 예시:
        # Django admin fieldsets에서 사용
        class ExamAdmin(admin.ModelAdmin):
            fieldsets = [
                ('기본 정보', {
                    'fields': get_multilingual_fields(['title', 'description'], ['total_questions'])
                }),
            ]
    """
    multilingual_fields = []
    for field_name in field_names:
        for lang in SUPPORTED_LANGUAGES:
            multilingual_fields.append(f'{field_name}_{lang}')
    
    if other_fields:
        multilingual_fields.extend(other_fields)
    
    return tuple(multilingual_fields)


def is_auto_translation_enabled(user) -> bool:
    """
    사용자의 자동 번역 설정 여부를 확인합니다.

    Args:
        user: Django User 인스턴스 또는 Request.user

    Returns:
        bool: 자동 번역이 활성화되어 있으면 True, 비활성화되어 있으면 False
    """
    try:
        if not user or getattr(user, 'is_anonymous', False):
            return True

        profile = None
        # UserProfile 접근 (프로젝트에 따라 profile 또는 userprofile 속성을 사용할 수 있음)
        if hasattr(user, 'profile') and user.profile:
            profile = user.profile
        elif hasattr(user, 'userprofile') and user.userprofile:
            profile = user.userprofile

        if profile and hasattr(profile, 'auto_translation_enabled'):
            return bool(profile.auto_translation_enabled)
    except Exception as e:
        logger.warning(f"[AUTO_TRANSLATION] 사용자 번역 설정 확인 중 오류: {e}")

    # 예외 상황에서는 기본값(True)로 동작하여 기존 동작을 유지
    return True

def translate_long_text_in_chunks(text: str, from_lang: str, to_lang: str, chunk_size: int = 2000) -> Optional[str]:
    """
    긴 텍스트를 섹션별로 분할하여 번역합니다.
    
    Args:
        text: 번역할 긴 텍스트
        from_lang: 원본 언어
        to_lang: 대상 언어
        chunk_size: 분할 기준 크기 (기본 2000자)
    
    Returns:
        str: 번역된 전체 텍스트, 실패 시 None
    """
    try:
        # 섹션 기반 분할 (# 0), # 1), # 2) 등)
        import re
        sections = re.split(r'(\n#\s+\d+\))', text)
        
        # 분할된 섹션이 없으면 단순 길이 기반 분할
        if len(sections) <= 1:
            logger.info(f"[CHUNK_TRANSLATE] 섹션 감지 실패 → 길이 기반 분할 ({chunk_size}자 단위)")
            chunks = []
            for i in range(0, len(text), chunk_size):
                chunks.append(text[i:i+chunk_size])
        else:
            logger.info(f"[CHUNK_TRANSLATE] 섹션 감지 성공 → {len(sections)//2}개 섹션 분할")
            chunks = []
            current_chunk = ""
            for i, section in enumerate(sections):
                # 섹션 구분자와 내용을 합침
                current_chunk += section
                # 청크 크기 초과 또는 마지막 섹션이면 저장
                if len(current_chunk) >= chunk_size or i == len(sections) - 1:
                    if current_chunk.strip():
                        chunks.append(current_chunk)
                    current_chunk = ""
        
        logger.info(f"[CHUNK_TRANSLATE] 총 {len(chunks)}개 청크로 분할 (크기: {[len(c) for c in chunks]})")
        
        # 각 청크를 개별적으로 번역
        translated_chunks = []
        for i, chunk in enumerate(chunks):
            logger.info(f"[CHUNK_TRANSLATE] 청크 {i+1}/{len(chunks)} 번역 중... ({len(chunk)}자)")
            result = batch_translate_texts([chunk], from_lang, to_lang)
            if result and result[0]:
                translated_chunks.append(result[0])
                logger.info(f"[CHUNK_TRANSLATE] 청크 {i+1} 번역 완료")
            else:
                logger.error(f"[CHUNK_TRANSLATE] 청크 {i+1} 번역 실패")
                return None  # 하나라도 실패하면 전체 실패
        
        # 번역된 청크들을 합침
        final_text = ''.join(translated_chunks)
        logger.info(f"[CHUNK_TRANSLATE] 전체 번역 완료: {len(chunks)}개 청크 → {len(final_text)}자")
        return final_text
        
    except Exception as e:
        logger.error(f"[CHUNK_TRANSLATE] 분할 번역 중 오류: {e}")
        return None


def batch_translate_texts(texts: List[str], from_language: str, to_language: str) -> List[Optional[str]]:
    """
    여러 텍스트를 한 번의 API 호출로 번역합니다.
    OpenAI를 먼저 시도하고, 실패하면 Gemini로 fallback합니다.
    OpenAI 실패 시 1시간간 캐시에 저장하여 이후 요청은 바로 Gemini를 사용합니다.
    
    Args:
        texts: 번역할 텍스트 리스트
        from_language: 원본 언어
        to_language: 대상 언어
    
    Returns:
        List[Optional[str]]: 번역된 텍스트 리스트, 실패 시 None
    """
    if not texts:
        return []
    
    if from_language not in SUPPORTED_LANGUAGES or to_language not in SUPPORTED_LANGUAGES:
        logger.warning(f"[BATCH_TRANSLATE] 지원하지 않는 번역 방향: {from_language} → {to_language}")
        return [None] * len(texts)
    
    # OpenAI 사용 가능 여부 확인 (캐시 체크) - 함수 시작 시점에 먼저 체크
    openai_error = None
    logger.info(f"[BATCH_TRANSLATE] 🔍 캐시 확인 시작... ({from_language} → {to_language})")
    is_openai_unavailable = not check_openai_availability()
    
    if is_openai_unavailable:
        logger.warning(f"[BATCH_TRANSLATE] ⚠️ OpenAI가 캐시에서 사용 불가능 상태로 확인됨, Gemini로 바로 전환... ({from_language} → {to_language})")
        openai_error = "OpenAI가 캐시에서 사용 불가능 상태"
    else:
        # 캐시 확인 로그 추가 (디버깅용)
        logger.info(f"[BATCH_TRANSLATE] ✅ OpenAI 캐시 확인: 사용 가능 상태, OpenAI API 호출 시도... ({from_language} → {to_language})")
        # OpenAI API 시도
        try:
            # OpenAI API 키 확인
            openai_api_key = getattr(settings, 'OPENAI_API_KEY', None)
            if not openai_api_key:
                logger.warning(f"[BATCH_TRANSLATE] OpenAI API 키가 설정되지 않음 - {from_language} → {to_language}")
                openai_error = "OpenAI API 키가 설정되지 않음"
                mark_openai_unavailable()
            else:
                # 언어 이름 매핑
                language_names = {
                    LANGUAGE_KO: 'Korean',
                    LANGUAGE_EN: 'English',
                    LANGUAGE_ES: 'Spanish',
                    LANGUAGE_ZH: 'Chinese (Simplified)',
                    LANGUAGE_JA: 'Japanese'
                }
                
                from_lang_name = language_names.get(from_language, from_language)
                to_lang_name = language_names.get(to_language, to_language)
                
                # 일반적인 번역 프롬프트 (모든 언어 방향에 적용)
                system_prompt = '''You are a professional translator. Translate text accurately while preserving meaning, tone, and formatting.
CRITICAL: Your response must be a VALID JSON array that can be parsed by json.loads() in Python.
RULES:
1. Return format: ["translation1", "translation2", ...]
2. Use double quotes (") for strings, escape them as \" inside text
3. Escape backslashes as \\
4. Escape newlines as \\n (they should already be in the input)
5. NO extra text, NO markdown, NO code blocks, NO explanations
6. Exact same number of elements as input texts
7. Preserve formatting (newlines, bullets, numbering) in the translation'''
                
                user_prompt = f'Translate these {len(texts)} {from_lang_name} text(s) to {to_lang_name}. Return ONLY a valid JSON array with exactly {len(texts)} translation(s):\n{json.dumps(texts, ensure_ascii=False)}'
                
                if not openai_error and system_prompt and user_prompt:
                    # API 호출 전에 다시 한 번 캐시 확인 (동시성 문제 방지)
                    logger.info(f"[BATCH_TRANSLATE] 🔍 API 호출 직전 캐시 재확인... ({from_language} → {to_language})")
                    if not check_openai_availability():
                        logger.warning(f"[BATCH_TRANSLATE] ⚠️ API 호출 직전 캐시 재확인: OpenAI 사용 불가능 상태로 변경됨, Gemini로 전환... ({from_language} → {to_language})")
                        openai_error = "OpenAI가 캐시에서 사용 불가능 상태 (재확인)"
                    else:
                        logger.info(f"[BATCH_TRANSLATE] ✅ API 호출 직전 캐시 재확인: OpenAI 사용 가능, API 호출 진행... ({from_language} → {to_language})")
                        # OpenAI API 호출
                        headers = {
                            'Authorization': f'Bearer {openai_api_key}',
                            'Content-Type': 'application/json'
                        }
                        
                        # 배치 크기와 텍스트 길이에 따라 토큰 수 조정
                        total_input_length = sum(len(t) for t in texts)
                        # 한국어→영어는 평균 2배, 프롬프트 오버헤드 500 토큰
                        estimated_output_tokens = int(total_input_length * 2.0) + 500
                        model = 'gpt-3.5-turbo'
                        # gpt-3.5-turbo의 출력 토큰 제한: 최대 4096
                        max_tokens = min(estimated_output_tokens, 4096)
                        
                        logger.info(f"[BATCH_TRANSLATE] 토큰 계산: 입력 길이={total_input_length}, 예상 출력 토큰={estimated_output_tokens}, 실제 할당={max_tokens}, 모델={model}")
                        
                        payload = {
                            'model': model,
                            'messages': [
                                {
                                    'role': 'system',
                                    'content': system_prompt
                                },
                                {
                                    'role': 'user',
                                    'content': user_prompt
                                }
                            ],
                            'max_tokens': max_tokens,
                            'temperature': 0.3
                        }
                        
                        logger.info(f"[BATCH_TRANSLATE] OpenAI API 호출 시작 - 텍스트 수: {len(texts)}, max_tokens: {max_tokens}")
                        logger.debug(f"[BATCH_TRANSLATE] 요청 텍스트들: {[t[:100] + '...' if len(t) > 100 else t for t in texts]}")
                        
                        response = requests.post(
                            'https://api.openai.com/v1/chat/completions',
                            headers=headers,
                            json=payload,
                            timeout=60  # 배치 번역이므로 타임아웃 증가
                        )
                        
                        logger.info(f"[BATCH_TRANSLATE] OpenAI API 응답 상태: {response.status_code}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        response_content = result['choices'][0]['message']['content'].strip()
                        
                        logger.info(f"[BATCH_TRANSLATE] 원본 응답 길이: {len(response_content)}자")
                        logger.debug(f"[BATCH_TRANSLATE] 원본 응답 전체:\n{response_content}")
                        
                        try:
                            # JSON 응답 파싱 시도 1: JSON 객체에서 translations 키 추출
                            response_obj = json.loads(response_content)
                            
                            # response_format=json_object 사용 시 {"translations": [...]} 형태
                            if isinstance(response_obj, dict) and 'translations' in response_obj:
                                translated_texts = response_obj['translations']
                                if isinstance(translated_texts, list) and len(translated_texts) == len(texts):
                                    logger.info(f"[BATCH_TRANSLATE] 배치 번역 성공 (json_object): {len(texts)}개 텍스트 ({from_language} → {to_language})")
                                    return translated_texts
                                else:
                                    logger.warning(f"[BATCH_TRANSLATE] 응답 배열 크기 오류: 예상 {len(texts)}개, 실제 {len(translated_texts) if isinstance(translated_texts, list) else 'N/A'}")
                                    return [None] * len(texts)
                            # 이전 형식 (배열 직접 반환) 호환성 유지
                            elif isinstance(response_obj, list) and len(response_obj) == len(texts):
                                logger.info(f"[BATCH_TRANSLATE] 배치 번역 성공 (array): {len(texts)}개 텍스트 ({from_language} → {to_language})")
                                return response_obj
                            else:
                                logger.warning(f"[BATCH_TRANSLATE] 응답 형식 오류: {type(response_obj)}, 내용: {str(response_obj)[:200]}")
                                return [None] * len(texts)
                        except json.JSONDecodeError as e:
                            logger.error(f"[BATCH_TRANSLATE] JSON 파싱 실패 (1차 시도): {e}")
                            logger.error(f"[BATCH_TRANSLATE] 에러 위치: line {e.lineno}, column {e.colno}, position {e.pos}")
                            logger.error(f"[BATCH_TRANSLATE] 에러 발생 위치 주변 텍스트 (pos-50 ~ pos+50):")
                            error_start = max(0, e.pos - 50)
                            error_end = min(len(response_content), e.pos + 50)
                            logger.error(f"[BATCH_TRANSLATE] ...{response_content[error_start:error_end]}...")
                            logger.error(f"[BATCH_TRANSLATE] 전체 응답 내용:")
                            logger.error(response_content)
                            
                            # JSON 응답 파싱 시도 2: 여러 정제 방법 시도
                            try:
                                # 방법 1: 마크다운 코드 블록 제거
                                cleaned_content = re.sub(r'^```(?:json)?\s*\n?', '', response_content)
                                cleaned_content = re.sub(r'\n?```\s*$', '', cleaned_content)
                                cleaned_content = cleaned_content.strip()
                                
                                # 방법 2: 배열 추출 (대괄호 안의 내용만)
                                # 응답에 설명 텍스트가 배열 밖에 있을 수 있음
                                array_match = re.search(r'(\[.*\])', cleaned_content, re.DOTALL)
                                if array_match:
                                    cleaned_content = array_match.group(1)
                                    logger.info(f"[BATCH_TRANSLATE] 2차 시도: 배열 부분만 추출 ({len(cleaned_content)}자)")
                                else:
                                    logger.info(f"[BATCH_TRANSLATE] 2차 시도: 코드 블록 제거 후 파싱")
                                
                                logger.debug(f"[BATCH_TRANSLATE] 정제된 내용:\n{cleaned_content[:500]}")
                                
                                response_obj = json.loads(cleaned_content)
                                
                                # response_format=json_object 사용 시 {"translations": [...]} 형태
                                if isinstance(response_obj, dict) and 'translations' in response_obj:
                                    translated_texts = response_obj['translations']
                                    if isinstance(translated_texts, list) and len(translated_texts) == len(texts):
                                        logger.info(f"[BATCH_TRANSLATE] 배치 번역 성공 (2차 시도, json_object): {len(texts)}개 텍스트 ({from_language} → {to_language})")
                                        return translated_texts
                                    else:
                                        logger.warning(f"[BATCH_TRANSLATE] 응답 배열 크기 오류 (2차 시도): 예상 {len(texts)}개, 실제 {len(translated_texts) if isinstance(translated_texts, list) else 'N/A'}")
                                        return [None] * len(texts)
                                # 이전 형식 호환성
                                elif isinstance(response_obj, list) and len(response_obj) == len(texts):
                                    logger.info(f"[BATCH_TRANSLATE] 배치 번역 성공 (2차 시도, array): {len(texts)}개 텍스트 ({from_language} → {to_language})")
                                    return response_obj
                                else:
                                    logger.warning(f"[BATCH_TRANSLATE] 응답 형식 오류 (2차 시도): {type(response_obj)}, 내용: {str(response_obj)[:200]}")
                                    return [None] * len(texts)
                            except json.JSONDecodeError as e2:
                                logger.error(f"[BATCH_TRANSLATE] JSON 파싱 실패 (2차 시도): {e2}")
                                logger.error(f"[BATCH_TRANSLATE] 에러 위치: line {e2.lineno}, column {e2.colno}, position {e2.pos}")
                                logger.error(f"[BATCH_TRANSLATE] 에러 발생 위치 주변 텍스트:")
                                error_start = max(0, e2.pos - 100)
                                error_end = min(len(cleaned_content), e2.pos + 100)
                                logger.error(f"[BATCH_TRANSLATE] ...{cleaned_content[error_start:error_end]}...")
                                
                                # 3차 시도: 단일 요소 배열에서 텍스트만 추출
                                logger.info(f"[BATCH_TRANSLATE] 3차 시도: 수동 텍스트 추출")
                                try:
                                    # ["텍스트"] 형태에서 대괄호와 양쪽 따옴표 제거
                                    if cleaned_content.startswith('["') and cleaned_content.endswith('"]'):
                                        extracted = cleaned_content[2:-2]  # [" 와 "] 제거
                                        # 이스케이프 시퀀스 처리
                                        extracted = extracted.replace('\\n', '\n')
                                        extracted = extracted.replace('\\t', '\t')
                                        extracted = extracted.replace('\\r', '\r')
                                        extracted = extracted.replace('\\"', '"')
                                        extracted = extracted.replace('\\\\', '\\')
                                        
                                        logger.info(f"[BATCH_TRANSLATE] 3차 시도 성공: 수동 추출 ({len(extracted)}자)")
                                        return [extracted]
                                    else:
                                        logger.error(f"[BATCH_TRANSLATE] 3차 시도 실패: 예상 형식 아님")
                                        logger.error(f"[BATCH_TRANSLATE] 응답 전체 길이: {len(response_content)}자")
                                        return [None] * len(texts)
                                except Exception as e3:
                                    logger.error(f"[BATCH_TRANSLATE] 3차 시도 중 예외: {e3}")
                                    return [None] * len(texts)
                            except Exception as e3:
                                logger.error(f"[BATCH_TRANSLATE] 2차 시도 중 예외 발생: {e3}", exc_info=True)
                                return [None] * len(texts)
                    else:
                        openai_error = f"OpenAI API 오류: {response.status_code}"
                        try:
                            error_detail = response.json()
                            logger.error(f"[BATCH_TRANSLATE] 에러 상세: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
                            if 'error' in error_detail:
                                error_code = error_detail['error'].get('code', '')
                                error_message = error_detail['error'].get('message', openai_error)
                                openai_error = f"OpenAI: {error_message}"
                                # 429 에러(quota 초과) 또는 insufficient_quota 에러는 즉시 캐시에 마킹
                                if response.status_code == 429 or error_code == 'insufficient_quota':
                                    logger.warning(f"[BATCH_TRANSLATE] OpenAI 429/quota 초과 에러 감지, 즉시 캐시에 마킹하고 Gemini로 전환...")
                                    mark_openai_unavailable()
                        except:
                            logger.error(f"[BATCH_TRANSLATE] 에러 응답: {response.text[:500]}")
                            # 429 에러는 상태 코드로도 확인 가능
                            if response.status_code == 429:
                                logger.warning(f"[BATCH_TRANSLATE] OpenAI 429 에러 감지, 즉시 캐시에 마킹하고 Gemini로 전환...")
                                mark_openai_unavailable()
                        logger.warning(f"[BATCH_TRANSLATE] {openai_error}, Gemini로 전환 시도...")
                        # 429가 아닌 다른 에러도 마킹 (재시도 방지)
                        if response.status_code != 429:
                            mark_openai_unavailable()
            
        except requests.exceptions.Timeout:
            openai_error = "OpenAI API 요청 시간 초과"
            logger.warning(f"[BATCH_TRANSLATE] {openai_error}, Gemini로 전환 시도...")
            mark_openai_unavailable()
        except requests.exceptions.RequestException as e:
            openai_error = f"OpenAI API 요청 오류: {str(e)}"
            logger.warning(f"[BATCH_TRANSLATE] {openai_error}, Gemini로 전환 시도...")
            mark_openai_unavailable()
        except Exception as e:
            openai_error = f"OpenAI 번역 중 예상치 못한 오류: {str(e)}"
            logger.warning(f"[BATCH_TRANSLATE] {openai_error}, Gemini로 전환 시도...", exc_info=True)
            mark_openai_unavailable()
    
    # OpenAI가 실패했거나 캐시에서 사용 불가능한 경우에만 Gemini fallback 시도
    # openai_error가 None이면 OpenAI가 성공한 것이므로 Gemini fallback 불필요
    if openai_error is None:
        # OpenAI가 성공했는데 여기까지 왔다면 이상한 상황
        logger.warning(f"[BATCH_TRANSLATE] OpenAI 성공했는데 Gemini fallback 블록에 도달함 - 이는 정상적인 상황이 아닙니다")
        return [None] * len(texts)
    
    # Gemini fallback 시도
    try:
        try:
            import google.generativeai as genai
        except ImportError:
            logger.warning("[BATCH_TRANSLATE] google-generativeai 패키지가 설치되지 않음, Gemini fallback 불가")
            return [None] * len(texts)
        
        gemini_api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not gemini_api_key:
            logger.warning("[BATCH_TRANSLATE] Gemini API 키가 설정되지 않음, Gemini fallback 불가")
            return [None] * len(texts)
        
        logger.info(f"[BATCH_TRANSLATE] Gemini API를 사용하여 번역 시도... ({from_language} → {to_language})")
        genai.configure(api_key=gemini_api_key)
        
        # 모델 생성 시도 (여러 모델 이름 시도)
        model = None
        model_names_to_try = [
            getattr(settings, 'GEMINI_MODEL', 'gemini-pro'),
            'gemini-2.5-flash',
            'gemini-pro',
            'gemini-1.5-pro',
            'gemini-1.5-pro-latest',
            'models/gemini-pro',
        ]
        
        for name in model_names_to_try:
            try:
                model = genai.GenerativeModel(name)
                logger.info(f"[BATCH_TRANSLATE] Gemini 모델 '{name}' 사용")
                break
            except Exception as model_error:
                logger.debug(f"[BATCH_TRANSLATE] 모델 '{name}' 시도 실패: {model_error}")
                continue
        
        if model is None:
            raise ValueError(f"사용 가능한 Gemini 모델을 찾을 수 없습니다. 시도한 모델: {model_names_to_try}")
        
        # 언어 이름 매핑 (Gemini용)
        language_names = {
            LANGUAGE_KO: 'Korean',
            LANGUAGE_EN: 'English',
            LANGUAGE_ES: 'Spanish',
            LANGUAGE_ZH: 'Chinese (Simplified)',
            LANGUAGE_JA: 'Japanese'
        }
        
        from_lang_name = language_names.get(from_language, from_language)
        to_lang_name = language_names.get(to_language, to_language)
        
        # 일반적인 번역 프롬프트 (모든 언어 방향에 적용)
        gemini_prompt = f'''You are a professional translator. Translate the following {from_lang_name} texts to {to_lang_name}.
CRITICAL: Your response must be a VALID JSON array that can be parsed by json.loads() in Python.
RULES:
1. Return format: ["translation1", "translation2", ...]
2. Use double quotes (") for strings, escape them as \\" inside text
3. Escape backslashes as \\\\
4. Escape newlines as \\n
5. NO extra text, NO markdown, NO code blocks, NO explanations
6. Exact same number of elements as input
7. Preserve formatting (newlines, bullets, numbering) in the translation

Translate these {len(texts)} {from_lang_name} text(s) to {to_lang_name}. Return ONLY a JSON array:
{json.dumps(texts, ensure_ascii=False)}'''
        
        # Gemini API 호출
        # estimated_output_tokens가 정의되지 않았을 경우를 대비
        total_input_length = sum(len(t) for t in texts)
        estimated_output_tokens = int(total_input_length * 2.0) + 500
        gemini_max_tokens = max(estimated_output_tokens, 2000)
        # 안전 필터 설정: 번역 콘텐츠를 위해 안전 필터 민감도 낮춤
        try:
            # Google Generative AI SDK에서 제공하는 enum 사용 시도
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            safety_settings = [
                {
                    "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
                    "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    "threshold": HarmBlockThreshold.BLOCK_ONLY_HIGH  # 번역 콘텐츠 허용을 위해 낮춤
                }
            ]
            response = model.generate_content(
                gemini_prompt,
                generation_config={
                    'temperature': 0.3,
                    'max_output_tokens': gemini_max_tokens,
                },
                safety_settings=safety_settings
            )
        except (ImportError, AttributeError, TypeError) as e:
            # safety_settings 설정 실패 시 기본 설정으로 fallback
            logger.debug(f"[BATCH_TRANSLATE] Gemini 안전 필터 설정 실패, 기본 설정 사용: {e}")
            response = model.generate_content(
                gemini_prompt,
                generation_config={
                    'temperature': 0.3,
                    'max_output_tokens': gemini_max_tokens,
                }
            )
        
        # 응답 확인
        if not response or not response.candidates:
            raise ValueError("Gemini API 응답이 비어있습니다.")
        
        ai_response = response.text.strip()
        logger.info(f"[BATCH_TRANSLATE] Gemini 응답 받음 (길이: {len(ai_response)}자)")
        
        # JSON 파싱 (OpenAI와 동일한 로직)
        try:
            # 마크다운 코드 블록 제거 및 배열 추출
            cleaned_content = re.sub(r'^```(?:json)?\s*\n?', '', ai_response)
            cleaned_content = re.sub(r'\n?```\s*$', '', cleaned_content)
            cleaned_content = cleaned_content.strip()
            
            array_match = re.search(r'(\[.*\])', cleaned_content, re.DOTALL)
            if array_match:
                cleaned_content = array_match.group(1)
            
            response_obj = json.loads(cleaned_content)
            
            # JSON 배열 확인
            if isinstance(response_obj, list) and len(response_obj) == len(texts):
                logger.info(f"[BATCH_TRANSLATE] Gemini 배치 번역 성공: {len(texts)}개 텍스트 ({from_language} → {to_language})")
                return response_obj
            elif isinstance(response_obj, dict) and 'translations' in response_obj:
                translated_texts = response_obj['translations']
                if isinstance(translated_texts, list) and len(translated_texts) == len(texts):
                    logger.info(f"[BATCH_TRANSLATE] Gemini 배치 번역 성공 (json_object): {len(texts)}개 텍스트 ({from_language} → {to_language})")
                    return translated_texts
                else:
                    logger.warning(f"[BATCH_TRANSLATE] Gemini 응답 배열 크기 오류: 예상 {len(texts)}개, 실제 {len(translated_texts) if isinstance(translated_texts, list) else 'N/A'}")
                    return [None] * len(texts)
            else:
                logger.warning(f"[BATCH_TRANSLATE] Gemini 응답 형식 오류: {type(response_obj)}, 내용: {str(response_obj)[:200]}")
                return [None] * len(texts)
        except json.JSONDecodeError as e:
            logger.error(f"[BATCH_TRANSLATE] Gemini JSON 파싱 실패: {e}")
            logger.error(f"[BATCH_TRANSLATE] Gemini 응답 내용: {ai_response[:500]}")
            return [None] * len(texts)
        except Exception as e:
            logger.error(f"[BATCH_TRANSLATE] Gemini 응답 처리 중 오류: {e}")
            return [None] * len(texts)
            
    except Exception as gemini_error:
        logger.error(f"[BATCH_TRANSLATE] Gemini API 호출도 실패: {gemini_error}")
        error_msg = f"번역 실패: OpenAI와 Gemini 모두 실패했습니다. "
        if 'openai_error' in locals():
            error_msg += f"OpenAI: {openai_error}. "
        error_msg += f"Gemini: {str(gemini_error)}"
        logger.error(f"[BATCH_TRANSLATE] {error_msg}")
        return [None] * len(texts)

def batch_translate_questions(questions: List, user, max_retries: int = MAX_RETRIES) -> Dict[str, Any]:
    """
    여러 문제를 배치로 번역 처리합니다.
    
    Args:
        questions: 번역할 문제 리스트
        user: 현재 사용자
        max_retries: 최대 재시도 횟수
    
    Returns:
        Dict: 번역 결과 통계
    """
    if not questions:
        return {'total': 0, 'translated': 0, 'failed': 0, 'errors': []}

    if not is_auto_translation_enabled(user):
        logger.info("[BATCH_QUESTION_TRANSLATE] 사용자 설정으로 인해 자동 번역이 비활성화되어 배치 번역을 건너뜁니다.")
        return {'total': 0, 'translated': 0, 'failed': 0, 'errors': [], 'skipped': True}
    
    logger.info(f"[BATCH_QUESTION_TRANSLATE] {len(questions)}개 문제 배치 번역 시작")
    
    # 번역할 텍스트들을 언어별로 그룹화
    ko_texts = []  # 한국어 → 영어 번역 대상
    en_texts = []  # 영어 → 한국어 번역 대상
    
    for question in questions:
        # 제목 번역
        if hasattr(question, 'title_ko') and question.title_ko and not getattr(question, 'title_en', None):
            ko_texts.append(('title', question.id, question.title_ko))
        elif hasattr(question, 'title_en') and question.title_en and not getattr(question, 'title_ko', None):
            en_texts.append(('title', question.id, question.title_en))
        
        # 내용 번역
        if hasattr(question, 'content_ko') and question.content_ko and not getattr(question, 'content_en', None):
            ko_texts.append(('content', question.id, question.content_ko))
        elif hasattr(question, 'content_en') and question.content_en and not getattr(question, 'content_ko', None):
            en_texts.append(('content', question.id, question.content_en))
        
        # 정답 번역
        if hasattr(question, 'answer_ko') and question.answer_ko and not getattr(question, 'answer_en', None):
            ko_texts.append(('answer', question.id, question.answer_ko))
        elif hasattr(question, 'answer_en') and question.answer_en and not getattr(question, 'answer_ko', None):
            en_texts.append(('answer', question.id, question.answer_en))
        
        # 설명 번역
        if hasattr(question, 'explanation_ko') and question.explanation_ko and not getattr(question, 'explanation_en', None):
            ko_texts.append(('explanation', question.id, question.explanation_ko))
        elif hasattr(question, 'explanation_en') and question.explanation_en and not getattr(question, 'explanation_ko', None):
            en_texts.append(('explanation', question.id, question.explanation_en))
    
    total_translations = len(ko_texts) + len(en_texts)
    translated_count = 0
    failed_count = 0
    errors = []
    
    # 한국어 → 영어 배치 번역
    if ko_texts:
        try:
            texts_to_translate = [text for _, _, text in ko_texts]
            translated_texts = batch_translate_texts(texts_to_translate, 'ko', 'en')
            
            # 번역 결과를 각 문제에 적용
            for i, (field_type, question_id, _) in enumerate(ko_texts):
                if translated_texts[i]:
                    question = next(q for q in questions if q.id == question_id)
                    setattr(question, f'{field_type}_en', translated_texts[i])
                    question.save(update_fields=[f'{field_type}_en'])
                    translated_count += 1
                else:
                    failed_count += 1
                    errors.append(f"문제 {question_id}의 {field_type} 번역 실패")
                    
        except Exception as e:
            logger.error(f"[BATCH_QUESTION_TRANSLATE] 한국어→영어 번역 실패: {e}")
            failed_count += len(ko_texts)
            errors.append(f"한국어→영어 배치 번역 실패: {str(e)}")
    
    # 영어 → 한국어 배치 번역
    if en_texts:
        try:
            texts_to_translate = [text for _, _, text in en_texts]
            translated_texts = batch_translate_texts(texts_to_translate, 'en', 'ko')
            
            # 번역 결과를 각 문제에 적용
            for i, (field_type, question_id, _) in enumerate(en_texts):
                if translated_texts[i]:
                    question = next(q for q in questions if q.id == question_id)
                    setattr(question, f'{field_type}_ko', translated_texts[i])
                    question.save(update_fields=[f'{field_type}_ko'])
                    translated_count += 1
                else:
                    failed_count += 1
                    errors.append(f"문제 {question_id}의 {field_type} 번역 실패")
                    
        except Exception as e:
            logger.error(f"[BATCH_QUESTION_TRANSLATE] 영어→한국어 번역 실패: {e}")
            failed_count += len(en_texts)
            errors.append(f"영어→한국어 배치 번역 실패: {str(e)}")
    
    logger.info(f"[BATCH_QUESTION_TRANSLATE] 배치 번역 완료: {translated_count}/{total_translations} 성공, {failed_count} 실패")
    
    return {
        'total': total_translations,
        'translated': translated_count,
        'failed': failed_count,
        'errors': errors
    }

def batch_translate_question_titles(questions: List, user, max_retries: int = MAX_RETRIES) -> Dict[str, Any]:
    """
    여러 문제의 제목만 배치로 번역 처리합니다.
    
    Args:
        questions: 번역할 문제 리스트
        user: 현재 사용자
        max_retries: 최대 재시도 횟수
    
    Returns:
        Dict: 번역 결과 통계
    """
    if not questions:
        return {'total': 0, 'translated': 0, 'failed': 0, 'errors': []}
    
    logger.info(f"[BATCH_QUESTION_TITLE_TRANSLATE] {len(questions)}개 문제 제목 배치 번역 시작")
    
    # 번역할 텍스트들을 언어별로 그룹화 (제목만)
    ko_texts = []  # 한국어 → 영어 번역 대상
    en_texts = []  # 영어 → 한국어 번역 대상
    
    for question in questions:
        # 제목만 번역 (내용, 정답, 설명은 제외)
        if hasattr(question, 'title_ko') and question.title_ko and not getattr(question, 'title_en', None):
            ko_texts.append(('title', question.id, question.title_ko))
        elif hasattr(question, 'title_en') and question.title_en and not getattr(question, 'title_ko', None):
            en_texts.append(('title', question.id, question.title_en))
    
    total_translations = len(ko_texts) + len(en_texts)
    translated_count = 0
    failed_count = 0
    errors = []
    
    # 한국어 → 영어 배치 번역
    if ko_texts:
        try:
            texts_to_translate = [text for _, _, text in ko_texts]
            translated_texts = batch_translate_texts(texts_to_translate, 'ko', 'en')
            
            # 번역 결과를 각 문제에 적용
            for i, (field_type, question_id, _) in enumerate(ko_texts):
                if translated_texts[i]:
                    question = next(q for q in questions if q.id == question_id)
                    setattr(question, f'{field_type}_en', translated_texts[i])
                    question.save(update_fields=[f'{field_type}_en'])
                    translated_count += 1
                else:
                    failed_count += 1
                    errors.append(f"문제 {question_id}의 {field_type} 번역 실패")
                    
        except Exception as e:
            logger.error(f"[BATCH_QUESTION_TITLE_TRANSLATE] 한국어→영어 번역 실패: {e}")
            failed_count += len(ko_texts)
            errors.append(f"한국어→영어 배치 번역 실패: {str(e)}")
    
    # 영어 → 한국어 배치 번역
    if en_texts:
        try:
            texts_to_translate = [text for _, _, text in en_texts]
            translated_texts = batch_translate_texts(texts_to_translate, 'en', 'ko')
            
            # 번역 결과를 각 문제에 적용
            for i, (field_type, question_id, _) in enumerate(en_texts):
                if translated_texts[i]:
                    question = next(q for q in questions if q.id == question_id)
                    setattr(question, f'{field_type}_ko', translated_texts[i])
                    question.save(update_fields=[f'{field_type}_ko'])
                    translated_count += 1
                else:
                    failed_count += 1
                    errors.append(f"문제 {question_id}의 {field_type} 번역 실패")
                    
        except Exception as e:
            logger.error(f"[BATCH_QUESTION_TITLE_TRANSLATE] 영어→한국어 번역 실패: {e}")
            failed_count += len(en_texts)
            errors.append(f"영어→한국어 배치 번역 실패: {str(e)}")
    
    logger.info(f"[BATCH_QUESTION_TITLE_TRANSLATE] 제목 배치 번역 완료: {translated_count}/{total_translations} 성공, {failed_count} 실패")
    
    return {
        'total': total_translations,
        'translated': translated_count,
        'failed': failed_count,
        'errors': errors
    }

def process_large_question_batch(questions: List, user, batch_size: int = BATCH_SIZE) -> Dict[str, Any]:
    """
    대량의 문제를 배치로 나누어 번역 처리합니다.
    
    Args:
        questions: 번역할 문제 리스트
        user: 현재 사용자
        batch_size: 배치 크기
    
    Returns:
        Dict: 전체 번역 결과 통계
    """
    if not questions:
        return {'total_questions': 0, 'total_translations': 0, 'successful': 0, 'failed': 0, 'errors': []}

    if not is_auto_translation_enabled(user):
        logger.info("[LARGE_BATCH_TRANSLATE] 사용자 설정으로 인해 자동 번역이 비활성화되어 대량 번역을 건너뜁니다.")
        return {
            'total_questions': len(questions),
            'total_translations': 0,
            'successful': 0,
            'failed': 0,
            'errors': [],
            'skipped': True
        }
    
    total_questions = len(questions)
    batches = []
    
    # 배치로 분할
    for i in range(0, total_questions, batch_size):
        batch = questions[i:i + batch_size]
        batches.append(batch)
    
    logger.info(f"[LARGE_BATCH_TRANSLATE] 총 {total_questions}개 문제를 {len(batches)}개 배치로 분할 (배치 크기: {batch_size})")
    
    total_translations = 0
    total_successful = 0
    total_failed = 0
    all_errors = []
    
    # 각 배치별로 번역 처리
    for i, batch in enumerate(batches):
        try:
            logger.info(f"[LARGE_BATCH_TRANSLATE] 배치 {i+1}/{len(batches)} 처리 중 ({len(batch)}개 문제)")
            
            # 배치 번역 수행
            result = batch_translate_questions(batch, user)
            
            total_translations += result['total']
            total_successful += result['translated']
            total_failed += result['failed']
            all_errors.extend(result['errors'])
            
            # 진행률 표시
            progress = ((i + 1) / len(batches)) * 100
            logger.info(f"[LARGE_BATCH_TRANSLATE] 진행률: {progress:.1f}% ({i+1}/{len(batches)})")
            
            # 메모리 정리
            gc.collect()
            
            # API 호출 간격 조절 (Rate Limiting 방지)
            if i < len(batches) - 1:  # 마지막 배치가 아닌 경우
                time.sleep(0.5)  # 0.5초 대기
            
        except Exception as e:
            logger.error(f"[LARGE_BATCH_TRANSLATE] 배치 {i+1} 처리 실패: {e}")
            all_errors.append(f"배치 {i+1} 처리 실패: {str(e)}")
            # 실패한 배치는 건너뛰고 계속 진행
            continue
    
    logger.info(f"[LARGE_BATCH_TRANSLATE] 전체 배치 번역 완료: {total_successful}/{total_translations} 성공, {total_failed} 실패")
    
    return {
        'total_questions': total_questions,
        'total_translations': total_translations,
        'successful': total_successful,
        'failed': total_failed,
        'errors': all_errors
    }


class MultilingualContentManager:
    """
    다국어 콘텐츠를 관리하는 공통 클래스
    
    이 클래스는 Django 모델의 다국어 필드를 효율적으로 처리하기 위한
    공통 기능들을 제공합니다.
    
    지원하는 다국어 필드 패턴:
    - title_ko, title_en
    - goal_ko, goal_en
    - description_ko, description_en
    - content_ko, content_en
    
    사용 예시:
    ```python
    # 스터디 모델에서 사용
    manager = MultilingualContentManager(study_instance, request.user)
    manager.handle_multilingual_update()
    
    # 다른 모델에서도 사용 가능
    manager = MultilingualContentManager(exam_instance, request.user)
    manager.handle_multilingual_update()
    ```
    """
    
    def __init__(self, instance, user, language_fields=None, preserve_empty_values=False, skip_completion_update=False):
        """
        MultilingualContentManager 초기화
        
        Args:
            instance: Django 모델 인스턴스
            user: 현재 사용자
            language_fields: 다국어 필드 정의 (기본값: title, goal)
            preserve_empty_values: 빈 값이 명시적으로 설정된 경우 보존 여부
            skip_completion_update: 완성도 상태 업데이트를 건너뛸지 여부 (조회 시 True)
        """
        self.instance = instance
        self.user = user
        self.current_language = self._get_user_language()
        self.preserve_empty_values = preserve_empty_values
        self.auto_translation_enabled = is_auto_translation_enabled(user)
        self.skip_completion_update = skip_completion_update
        
        # 기본 다국어 필드 설정
        if language_fields is None:
            self.language_fields = ['title', 'goal']
        else:
            self.language_fields = language_fields
        
        # 지원 언어
        self.supported_languages = SUPPORTED_LANGUAGES
        
        # 초기화 로그는 debug 레벨로만 출력 (너무 많은 로그 방지)
        # logger.debug(f"[MULTILINGUAL] 매니저 초기화: 모델={instance.__class__.__name__}, 언어={self.current_language}")
    
    def _get_user_language(self) -> str:
        """사용자의 언어 설정을 가져옵니다."""
        return get_user_language(self.user)
    
    def handle_multilingual_update(self) -> None:
        """
        다국어 콘텐츠 업데이트를 처리합니다.
        
        중요: 사용자의 프로필에 번역이 활성화되어 있을 경우에만 번역을 수행합니다.
        번역이 비활성화된 사용자의 경우 번역을 수행하지 않습니다.
        
        이 메서드는 다음 작업을 수행합니다:
        1. 사용자의 번역 활성화 여부 확인 (auto_translation_enabled)
        2. 번역이 활성화된 경우에만:
           - 각 다국어 필드에 대해 변경 감지
           - 필요한 경우 배치 번역 수행
        3. 언어별 완성도 상태 업데이트 (번역 활성화 여부와 무관하게 수행)
        """
        # logger.info(f"[MULTILINGUAL] 다국어 콘텐츠 업데이트 시작")
        # logger.info(f"[MULTILINGUAL_DEBUG] 인스턴스: {self.instance}")
        # logger.info(f"[MULTILINGUAL_DEBUG] 사용자: {self.user}")
        # logger.info(f"[MULTILINGUAL_DEBUG] 현재 언어: {self.current_language}")
        # logger.info(f"[MULTILINGUAL_DEBUG] 언어 필드들: {self.language_fields}")
        
        translation_tasks = []
        has_translation = False

        if self.auto_translation_enabled:
        #     logger.info(f"[MULTILINGUAL] 자동 번역 비활성화 설정으로 인해 번역을 건너뜁니다.")
        # else:
            # 번역이 필요한 콘텐츠 목록 생성
            translation_tasks = self._identify_translation_tasks()
            
            # 번역 작업 실행
            if translation_tasks:
                # 배치 번역 작업 실행
                self._execute_batch_translations(translation_tasks)
                has_translation = True
        
        # 언어별 완성도 상태 업데이트 (조회 시에는 건너뛰기)
        if not self.skip_completion_update:
            self._update_language_completion_status()
        
        # 실제 번역이 실행된 경우에만 로그 출력
        if has_translation:
            logger.info(f"[MULTILINGUAL] 다국어 콘텐츠 업데이트 완료 (번역 작업 {len(translation_tasks)}개 실행)")
    
    def _identify_translation_tasks(self) -> List[Tuple[str, str, str, str]]:
        """
        번역이 필요한 콘텐츠를 식별합니다.
        
        영어를 기본 언어(base language)로 하여:
        - 한국어로 생성하면 → 영어로 번역
        - 중국어로 생성하면 → 영어로 번역
        - 스페인어로 생성하면 → 영어로 번역
        - 일본어로 생성하면 → 영어로 번역
        - 영어로 생성하면 → 번역하지 않음 (영어가 기본 언어)
        
        중요: 사용자의 프로필에 번역이 활성화되어 있을 경우,
        en 모드가 아닌 언어로 생성된 시험은 항상 en으로 번역되어야 하며,
        supported_language에 en도 포함되어야 함.
        
        Returns:
            List[Tuple]: (필드명, 원본언어, 대상언어, 콘텐츠) 튜플의 리스트
        """
        translation_tasks = []
        
        # 🔍 디버깅: 인스턴스 정보 로깅
        # logger.info(f"[MULTILINGUAL_DEBUG] _identify_translation_tasks 시작")
        # logger.info(f"[MULTILINGUAL_DEBUG] 인스턴스 타입: {type(self.instance)}")
        # logger.info(f"[MULTILINGUAL_DEBUG] 인스턴스 ID: {getattr(self.instance, 'id', 'N/A')}")
        # logger.info(f"[MULTILINGUAL_DEBUG] 현재 언어: {self.current_language}")
        # logger.info(f"[MULTILINGUAL_DEBUG] 언어 필드들: {self.language_fields}")
        
        for field_name in self.language_fields:
            # 영어를 기본 언어로 하여, 다른 언어는 항상 영어로 번역
            # 사용자 언어가 기본 언어(BASE_LANGUAGE)와 같으면 번역하지 않음
            # 단, en 모드로 로딩하는 경우 created_language로 임시 변경된 경우를 고려해야 함
            
            # 변수 초기화
            source_field = None
            target_field = None
            from_lang = None
            to_lang = None
            
            if self.current_language == BASE_LANGUAGE:
                # 기본 언어로 생성한 경우 → 번역하지 않음 (이미 기본 언어)
                # 하지만 en 모드로 로딩할 때 created_language로 임시 변경된 경우는 제외
                # created_language를 확인하여 실제 생성 언어가 BASE_LANGUAGE가 아닌 경우 번역 필요
                created_language = getattr(self.instance, 'created_language', None) or BASE_LANGUAGE
                if created_language == BASE_LANGUAGE:
                    # 실제로 en으로 생성된 경우 → 번역하지 않음
                    continue
                else:
                    # en 모드로 로딩하지만 실제로는 다른 언어로 생성된 경우 → 번역 필요
                    # created_language를 사용하여 번역 작업 식별
                    source_field = f"{field_name}_{created_language}"  # 생성 언어 필드 (번역할 원본)
                    target_field = f"{field_name}_{BASE_LANGUAGE}"      # 영어 필드 (번역할 대상)
                    from_lang = created_language
                    to_lang = BASE_LANGUAGE
            else:
                # 한국어, 중국어 등 다른 언어로 생성한 경우 → 영어로 번역
                source_field = f"{field_name}_{self.current_language}"  # 현재 언어 필드 (번역할 원본)
                target_field = f"{field_name}_{BASE_LANGUAGE}"         # 영어 필드 (번역할 대상)
                from_lang = self.current_language
                to_lang = BASE_LANGUAGE
            
            # 🔍 디버깅: 필드별 상세 정보 로깅
            # logger.info(f"[MULTILINGUAL_DEBUG] 필드 '{field_name}' 처리 중:")
            # logger.info(f"[MULTILINGUAL_DEBUG]   - 원본 언어 필드: {source_field}")
            # logger.info(f"[MULTILINGUAL_DEBUG]   - 대상 언어 필드: {target_field}")
            
            # 원본 언어의 콘텐츠 가져오기 (번역할 원본)
            source_content = getattr(self.instance, source_field, None)
            # logger.info(f"[MULTILINGUAL_DEBUG]   - 원본 언어 콘텐츠: {source_content[:100] if source_content else 'None'}...")
            
            # 대상 언어의 콘텐츠 확인 (이미 번역되어 있는지)
            target_content = getattr(self.instance, target_field, None)
            # logger.info(f"[MULTILINGUAL_DEBUG]   - 대상 언어 콘텐츠: {target_content[:100] if target_content else 'None'}...")
            
            # 빈 값 보존 모드에서 현재 언어 필드가 빈 값인 경우, 대상 언어 필드도 빈 값으로 설정
            if self.preserve_empty_values and (not source_content or (isinstance(source_content, str) and not source_content.strip())):
                setattr(self.instance, target_field, '')
                continue
            
            # 빈 값이나 공백만 있는 경우 번역 건너뜀
            if not source_content or (isinstance(source_content, str) and not source_content.strip()):
                continue
            
            # 빈 값 보존 모드에서 현재 언어 필드가 빈 값이 아닌 경우, 대상 언어 필드가 비어있으면 번역 수행
            if self.preserve_empty_values and source_content and not target_content:
                translation_tasks.append((field_name, from_lang, to_lang, source_content))
                logger.debug(f"[MULTILINGUAL] 번역 작업 추가: {field_name} ({from_lang} → {to_lang}) - 빈 값 보존 모드")
                continue
            
            # 현재 언어 필드에 내용이 있고 영어 필드가 비어있으면 번역 수행
            current_content = getattr(self.instance, source_field, None)
            if current_content and not target_content:
                translation_tasks.append((field_name, from_lang, to_lang, current_content))
                logger.debug(f"[MULTILINGUAL] 번역 작업 추가: {field_name} ({from_lang} → {to_lang}) - 대상 언어 필드 비어있음")
                continue
            
            if not target_content:
                # 영어 필드가 비어있음 → 번역 필요
                translation_tasks.append((field_name, from_lang, to_lang, source_content))
                logger.debug(f"[MULTILINGUAL] 번역 작업 추가: {field_name} ({from_lang} → {to_lang}) - 대상 언어 필드 비어있음")
            else:
                # 영어 필드가 이미 있음 → 원본 언어 필드가 변경되었는지 확인
                source_content = getattr(self.instance, source_field, None)
                
                # 원본 언어 필드의 내용이 변경되었으면 재번역 수행
                if self._is_content_changed(source_field, source_content):
                    translation_tasks.append((field_name, from_lang, to_lang, source_content))
                    logger.debug(f"[MULTILINGUAL] 번역 작업 추가: {field_name} ({from_lang} → {to_lang}) - 원본 언어 필드 변경 감지")
        
        # 실제 번역 작업이 있는 경우에만 로깅
        if translation_tasks:
            logger.info(f"[MULTILINGUAL] 번역 작업 {len(translation_tasks)}개 식별 완료")
        
        return translation_tasks
    
    def _is_content_changed(self, field_name: str, new_content: str) -> bool:
        """
        특정 필드의 내용이 실제로 변경되었는지 확인합니다.
        
        Args:
            field_name: 확인할 필드명
            new_content: 새로운 콘텐츠
        
        Returns:
            bool: 변경되었으면 True, 변경되지 않았으면 False
        """
        try:
            # Django 모델의 _state를 활용하여 변경 감지
            if hasattr(self.instance, '_state') and self.instance._state.adding:
                # 새로 생성된 인스턴스인 경우
                return True
            
            # Study 모델의 변경 플래그 확인
            if hasattr(self.instance, f'_{field_name}_changed'):
                is_changed = getattr(self.instance, f'_{field_name}_changed', False)
                if is_changed:
                    return True
            
            # 현재 인스턴스에서 기존 값 가져오기
            old_content = getattr(self.instance, field_name, None)
            
            # 인스턴스 ID 로깅 (디버깅용)
            instance_id = getattr(self.instance, 'id', 'N/A')
            instance_type = self.instance.__class__.__name__
            
            # 내용 비교 (공백 제거 후 비교)
            if old_content and new_content:
                old_clean = old_content.strip()
                new_clean = new_content.strip()
                
                if old_clean != new_clean:
                    return True
                else:
                    return False
            elif not old_content and new_content:
                # 기존 값이 없고 새로운 값이 있는 경우 (최초 입력)
                return True
            elif old_content and not new_content:
                # 기존 값이 있고 새로운 값이 없는 경우 (삭제)
                return True
            else:
                # 둘 다 비어있는 경우
                return False
                
        except Exception as e:
            logger.error(f"[CHANGE_DETECT] {field_name} 변경 감지 중 오류: {e}")
            # 오류 발생 시 기본적으로 변경된 것으로 간주 (안전장치)
            return True
    
    def _execute_batch_translations(self, translation_tasks: List[Tuple[str, str, str, str]]) -> None:
        """
        배치 번역 작업을 실행합니다.
        
        Args:
            translation_tasks: 번역할 작업 목록
        """
        if not translation_tasks:
            return
        
        # 언어별로 그룹화
        language_groups = {}
        for field_name, from_lang, to_lang, content in translation_tasks:
            key = (from_lang, to_lang)
            if key not in language_groups:
                language_groups[key] = []
            language_groups[key].append((field_name, content))
        
        # 각 언어 그룹별로 배치 번역 수행
        for (from_lang, to_lang), tasks in language_groups.items():
            try:
                # 번역할 텍스트들 추출
                texts = [content for _, content in tasks]
                field_names = [field_name for field_name, _ in tasks]
                
                logger.info(f"[MULTILINGUAL] 배치 번역 시작: {len(texts)}개 텍스트 ({from_lang} → {to_lang})")
                
                # 스마트 번역 수행 (선택지 형식 보존)
                translated_texts = []
                for i, content in enumerate(texts):
                    try:
                        # 스마트 번역으로 선택지 형식 보존 (원본 언어 정보 전달)
                        translated_content = smart_translate_content(content, to_lang, from_lang)
                        translated_texts.append(translated_content)
                        logger.info(f"[MULTILINGUAL] 스마트 번역 완료: {field_names[i]} - 선택지 형식 보존")
                    except Exception as e:
                        logger.warning(f"[MULTILINGUAL] 스마트 번역 실패, 기존 방식으로 폴백: {e}")
                        # 스마트 번역 실패 시 기존 배치 번역으로 폴백
                        fallback_result = batch_translate_texts([content], from_lang, to_lang)
                        translated_texts.append(fallback_result[0] if fallback_result else None)
                
                # 번역 결과 저장
                logger.info(f"[MULTILINGUAL_SAVE] 번역 결과 저장 시작 - 인스턴스 ID: {self.instance.id}, skip_completion_update: {self.skip_completion_update}")
                for i, (field_name, translated_content) in enumerate(zip(field_names, translated_texts)):
                    if translated_content:
                        target_field = f"{field_name}_{to_lang}"
                        
                        # 저장 전 필드 값 확인
                        old_value = getattr(self.instance, target_field, None)
                        old_display = old_value[:100] if old_value else '(비어있음)'
                        logger.debug(f"[MULTILINGUAL_SAVE] {field_name} 저장 전 - {target_field}: {old_display}...")
                        
                        setattr(self.instance, target_field, translated_content)
                        
                        # 저장 후 메모리 상 값 확인
                        new_value = getattr(self.instance, target_field, None)
                        logger.debug(f"[MULTILINGUAL_SAVE] {field_name} setattr 후 - {target_field}: {new_value[:100]}...")
                        logger.info(f"[MULTILINGUAL] {field_name} 번역 완료: '{texts[i][:50]}...' → '{translated_content[:50]}...'")
                    else:
                        logger.warning(f"[MULTILINGUAL] {field_name} 번역 실패")
                
                # 조회 시(skip_completion_update=True)에는 Celery 태스크로 비동기 저장 (성능 최적화)
                # 저장/업데이트 시에는 동기 저장
                if self.skip_completion_update:
                    # Celery 태스크로 비동기 저장
                    try:
                        from quiz.tasks import batch_save_translation_results
                        model_name = self.instance.__class__.__name__
                        instance_id = str(self.instance.id)
                        language_group = (from_lang, to_lang)
                        
                        # 번역 결과를 Celery 태스크로 전송
                        batch_save_translation_results.delay(
                            model_name=model_name,
                            instance_id=instance_id,
                            language_group=language_group,
                            field_names=field_names,
                            translated_texts=translated_texts
                        )
                        logger.info(f"[MULTILINGUAL_SAVE] Celery 태스크로 비동기 저장 요청 - {model_name}({instance_id}): {len(field_names)}개 필드")
                    except Exception as e:
                        logger.warning(f"[MULTILINGUAL_SAVE] Celery 태스크 전송 실패, 동기 저장으로 폴백: {str(e)}")
                        # 폴백: 동기 저장
                        update_fields = [f"{field_name}_{to_lang}" for field_name in field_names]
                        self.instance.save(update_fields=update_fields)
                        logger.info(f"[MULTILINGUAL_SAVE] 동기 저장 완료 (폴백)")
                else:
                    # 저장/업데이트 시에는 동기 저장
                    update_fields = [f"{field_name}_{to_lang}" for field_name in field_names]
                    logger.info(f"[MULTILINGUAL_SAVE] DB 저장 시작 - update_fields: {update_fields}")
                    self.instance.save(update_fields=update_fields)
                    logger.info(f"[MULTILINGUAL_SAVE] DB 저장 완료")
                    
                    # DB에서 다시 읽어서 확인
                    self.instance.refresh_from_db()
                    logger.debug(f"[MULTILINGUAL_SAVE] DB 저장 후 재확인:")
                    for field_name in field_names:
                        target_field = f"{field_name}_{to_lang}"
                        db_value = getattr(self.instance, target_field, None)
                        empty_marker = "(비어있음)"
                        display_value = db_value[:100] if db_value else empty_marker
                        logger.debug(f"[MULTILINGUAL_SAVE]   {target_field}: {display_value}...")
                
                logger.info(f"[MULTILINGUAL] 배치 번역 완료: {len(texts)}개 텍스트 ({from_lang} → {to_lang})")
                    
            except Exception as e:
                logger.error(f"[MULTILINGUAL] 배치 번역 실패 ({from_lang} → {to_lang}): {e}")
    
    def _execute_translations(self, translation_tasks: List[Tuple[str, str, str, str]]) -> None:
        """
        개별 번역 작업을 실행합니다. (하위 호환성을 위해 유지)
        
        Args:
            translation_tasks: 번역할 작업 목록
        """
        # 배치 번역으로 대체
        self._execute_batch_translations(translation_tasks)
    
    def _translate_content(self, text: str, from_language: str, to_language: str) -> Optional[str]:
        """
        단일 텍스트를 번역합니다. (하위 호환성을 위해 유지)
        
        Args:
            text: 번역할 텍스트
            from_language: 원본 언어
            to_language: 대상 언어
        
        Returns:
            str: 번역된 텍스트, 실패 시 None
        """
        # 배치 번역을 사용하여 단일 텍스트 번역
        result = batch_translate_texts([text], from_language, to_language)
        return result[0] if result else None
    
    def _update_language_completion_status(self) -> None:
        """언어별 완성도 상태를 업데이트합니다."""
        try:
            update_fields = []
            
            # 각 언어별 완성도 체크
            for language in self.supported_languages:
                completion_field = f"is_{language}_complete"
                
                # 해당 언어의 모든 필드가 완성되었는지 확인
                is_complete = all(
                    getattr(self.instance, f"{field_name}_{language}", None)
                    for field_name in self.language_fields
                )
                
                # 현재 완성도 상태와 비교
                current_status = getattr(self.instance, completion_field, False)
                if is_complete != current_status:
                    setattr(self.instance, completion_field, is_complete)
                    update_fields.append(completion_field)
            
            # 지원 언어 업데이트 (자동 설정을 건너뛰는 플래그가 없을 때만)
            # 완성도 상태를 먼저 확인한 후 supported_languages를 업데이트
            if hasattr(self.instance, 'supported_languages'):
                # _skip_auto_supported_languages 플래그가 설정되어 있으면 자동 업데이트 건너뛰기
                skip_auto = getattr(self.instance, '_skip_auto_supported_languages', False)
                if not skip_auto:
                    # 플래그가 없으면 완성도에 따라 supported_languages 자동 업데이트 (모든 언어 동일하게 처리)
                    supported = []
                    for language in self.supported_languages:
                        completion_field = f"is_{language}_complete"
                        if hasattr(self.instance, completion_field):
                            is_complete = getattr(self.instance, completion_field, False)
                            if is_complete:
                                supported.append(language)
                    
                    # en으로 번역된 경우 en도 포함되어야 함
                    # 사용자의 프로필에 번역이 활성화되어 있을 경우,
                    # en 모드가 아닌 언어로 생성된 시험은 en으로 번역되어야 하며,
                    # supported_language에 en도 포함되어야 함
                    created_lang = getattr(self.instance, 'created_language', BASE_LANGUAGE)
                    if created_lang != BASE_LANGUAGE:
                        # en 모드가 아닌 언어로 생성된 시험인 경우
                        # en 필드가 완성되었으면 en도 포함
                        en_completion_field = f"is_{BASE_LANGUAGE}_complete"
                        if hasattr(self.instance, en_completion_field):
                            is_en_complete = getattr(self.instance, en_completion_field, False)
                            if is_en_complete and BASE_LANGUAGE not in supported:
                                supported.append(BASE_LANGUAGE)
                                logger.info(f"[MULTILINGUAL] en으로 번역된 경우 en을 supported_languages에 추가")
                    
                    # 둘 다 완성되지 않았으면 생성 언어만 포함
                    if not supported:
                        supported.append(created_lang)
                    
                    # supported_languages 설정
                    new_supported = ','.join(supported)
                    current_supported = getattr(self.instance, 'supported_languages', '') or ''
                    
                    # 완성도가 변경되어 supported_languages가 업데이트되어야 하는 경우
                    if new_supported != current_supported:
                        self.instance.supported_languages = new_supported
                        if 'supported_languages' not in update_fields:
                            update_fields.append('supported_languages')
                        # 객체 정보 추가 (모델명과 ID)
                        instance_type = self.instance.__class__.__name__
                        instance_id = getattr(self.instance, 'id', 'N/A')
                        logger.info(f"[MULTILINGUAL] 지원 언어 자동 업데이트 [{instance_type}({instance_id})]: {current_supported} → {new_supported}")
                    # 변경이 없을 때는 로깅하지 않음 (너무 많은 로그 방지)
                else:
                    logger.debug(f"[MULTILINGUAL] 지원 언어 자동 업데이트 건너뛰기 (플래그 설정됨)")
            
            # 변경사항이 있으면 저장 (완성도 상태와 supported_languages를 함께 저장)
            if update_fields:
                instance_type = self.instance.__class__.__name__
                instance_id = getattr(self.instance, 'id', 'N/A')
                self.instance.save(update_fields=update_fields)
                logger.info(f"[MULTILINGUAL] DB 저장 완료 [{instance_type}({instance_id})]: {update_fields}")
                
        except Exception as e:
            logger.error(f"[MULTILINGUAL] 언어별 완성도 상태 업데이트 실패: {e}")
    
    def get_localized_content(self, field_name: str) -> Dict[str, Any]:
        """
        특정 필드의 다국어 콘텐츠를 현재 사용자 언어에 맞게 반환합니다.
        
        Args:
            field_name: 필드명 (예: 'title', 'goal')
        
        Returns:
            Dict: 다국어 콘텐츠 정보
        """
        try:
            # 현재 언어와 대상 언어의 콘텐츠 가져오기
            current_field = f"{field_name}_{self.current_language}"
            # 번역 대상 언어 결정: ko, es, zh, ja는 모두 en으로 번역
            if self.current_language in [LANGUAGE_KO, LANGUAGE_ES, LANGUAGE_ZH, LANGUAGE_JA]:
                target_language = BASE_LANGUAGE  # ko, es, zh, ja는 모두 en으로 번역
            else:
                target_language = BASE_LANGUAGE  # 기본값 (en)
            target_field = f"{field_name}_{target_language}"
            
            current_content = getattr(self.instance, current_field, None)
            target_content = getattr(self.instance, target_field, None)
            
            # 사용 가능한 언어 목록 생성
            available_languages = []
            ko_content = getattr(self.instance, f"{field_name}_ko", None)
            en_content = getattr(self.instance, f"{field_name}_en", None)
            es_content = getattr(self.instance, f"{field_name}_es", None)
            zh_content = getattr(self.instance, f"{field_name}_zh", None)
            ja_content = getattr(self.instance, f"{field_name}_ja", None)
            
            if ko_content and ko_content.strip():
                available_languages.append('ko')
            if en_content and en_content.strip():
                available_languages.append('en')
            if es_content and es_content.strip():
                available_languages.append('es')
            if zh_content and zh_content.strip():
                available_languages.append('zh')
            if ja_content and ja_content.strip():
                available_languages.append('ja')
            
            # 현재 언어 우선, 폴백 순서로 콘텐츠 설정
            # 빈 값 보존 모드에서는 현재 언어의 콘텐츠를 그대로 사용 (빈 값도 포함)
            if self.preserve_empty_values:
                content = current_content or ''
            else:
                # 모든 언어(ko, es, zh, ja)는 en으로 번역되므로 동일하게 처리
                # 현재 언어의 content가 있으면 우선 사용, 없으면 en (target_content) 사용
                content = current_content or target_content or ''
            
            return {
                'content': content,
                'current_language': self.current_language,
                'available_languages': available_languages,
                'is_complete': bool(current_content and current_content.strip() and target_content and target_content.strip())
            }
            
        except Exception as e:
            logger.error(f"[MULTILINGUAL] 다국어 콘텐츠 조회 실패: {e}")
            return {
                'content': '',
                'current_language': self.current_language,
                'available_languages': [],
                'is_complete': False
            }
    
    def get_all_localized_content(self) -> Dict[str, Any]:
        """
        모든 다국어 필드의 콘텐츠를 반환합니다.
        
        Returns:
            Dict: 모든 다국어 필드의 콘텐츠 정보와 메타데이터
        """
        try:
            result = {
                'fields': {},
                'current_language': self.current_language,
                'available_languages': []
            }
            
            # 사용 가능한 언어 목록 생성
            for language in self.supported_languages:
                has_content = any(
                    getattr(self.instance, f"{field_name}_{language}", None) and 
                    getattr(self.instance, f"{field_name}_{language}", None).strip()
                    for field_name in self.language_fields
                )
                if has_content:
                    result['available_languages'].append(language)
            
            # 각 필드별 다국어 콘텐츠
            for field_name in self.language_fields:
                result['fields'][field_name] = self.get_localized_content(field_name)
            
            return result
        except Exception as e:
            logger.error(f"[MULTILINGUAL] 전체 다국어 콘텐츠 조회 실패: {e}")
            return {
                'fields': {},
                'current_language': self.current_language,
                'available_languages': []
            }


class MultilingualSerializerMixin:
    """
    Django REST Framework 시리얼라이저에 다국어 처리를 추가하는 믹스인
    
    사용 예시:
    ```python
    class StudySerializer(MultilingualSerializerMixin, serializers.ModelSerializer):
        class Meta:
            model = Study
            fields = ['id', 'title_ko', 'title_en', 'goal_ko', 'goal_en']
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.multilingual_fields = ['title', 'goal']  # 다국어 필드 지정
    ```
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.multilingual_fields = getattr(self, 'multilingual_fields', ['title', 'goal'])
    
    def to_representation(self, instance):
        """응답 데이터 변환 시 다국어 콘텐츠 최적화 및 자동 번역"""
        data = super().to_representation(instance)
        
        # 다국어 콘텐츠 처리
        if hasattr(self, 'context') and 'request' in self.context:
            request = self.context['request']
            
            if hasattr(request, 'user'):
                # 자동 번역 설정 확인
                auto_translation_enabled = is_auto_translation_enabled(request.user)
                
                if auto_translation_enabled:
                    # MultilingualContentManager가 내부에서 번역 필요성을 올바르게 판단합니다.
                    # - en 모드로 로딩할 때 created_language를 확인하여 번역 수행
                    # - 다른 언어로 로딩할 때도 적절히 처리
                    # 조회 시에는 완성도 상태 업데이트를 건너뛰기 (skip_completion_update=True)
                    manager = MultilingualContentManager(instance, request.user, self.multilingual_fields, preserve_empty_values=True, skip_completion_update=True)
                    manager.handle_multilingual_update()
                    localized_data = manager.get_all_localized_content()
                else:
                    # 자동 번역이 비활성화된 경우: 번역 없이 다국어 콘텐츠만 조회 (로그 없음)
                    current_language = get_user_language(request.user)
                    localized_data = {
                        'fields': {},
                        'current_language': current_language,
                        'available_languages': []
                    }
                    
                    # 사용 가능한 언어 목록 생성
                    for language in SUPPORTED_LANGUAGES:
                        has_content = any(
                            getattr(instance, f"{field_name}_{language}", None) and 
                            getattr(instance, f"{field_name}_{language}", None).strip()
                            for field_name in self.multilingual_fields
                        )
                        if has_content:
                            localized_data['available_languages'].append(language)
                    
                    # 각 필드별 다국어 콘텐츠 (번역 없이 현재 값만 반환)
                    for field_name in self.multilingual_fields:
                        current_field = f"{field_name}_{current_language}"
                        # 번역 대상 언어 결정: ko, es, zh, ja는 모두 en으로 번역
                        if current_language in [LANGUAGE_KO, LANGUAGE_ES, LANGUAGE_ZH, LANGUAGE_JA]:
                            target_language = BASE_LANGUAGE  # ko, es, zh, ja는 모두 en으로 번역
                        else:
                            target_language = BASE_LANGUAGE  # 기본값 (en)
                        target_field = f"{field_name}_{target_language}"
                        
                        current_content = getattr(instance, current_field, None)
                        target_content = getattr(instance, target_field, None)
                        
                        # 사용 가능한 언어 목록
                        available_languages = []
                        ko_content = getattr(instance, f"{field_name}_ko", None)
                        en_content = getattr(instance, f"{field_name}_en", None)
                        es_content = getattr(instance, f"{field_name}_es", None)
                        zh_content = getattr(instance, f"{field_name}_zh", None)
                        ja_content = getattr(instance, f"{field_name}_ja", None)
                        if ko_content and ko_content.strip():
                            available_languages.append('ko')
                        if en_content and en_content.strip():
                            available_languages.append('en')
                        if es_content and es_content.strip():
                            available_languages.append('es')
                        if zh_content and zh_content.strip():
                            available_languages.append('zh')
                        if ja_content and ja_content.strip():
                            available_languages.append('ja')
                        
                        # 현재 언어 우선, 폴백 순서로 콘텐츠 설정
                        # 모든 언어(ko, es, zh, ja)는 en으로 번역되므로 동일하게 처리
                        # 현재 언어의 content가 있으면 우선 사용, 없으면 en (target_content) 사용
                        content = current_content or target_content or ''
                        
                        localized_data['fields'][field_name] = {
                            'content': content,
                            'current_language': current_language,
                            'available_languages': available_languages,
                            'is_complete': bool(current_content and current_content.strip() and target_content and target_content.strip())
                        }
                
                # 각 필드에 현재 언어에 맞는 콘텐츠 추가
                for field_name in self.multilingual_fields:
                    field_data = localized_data['fields'].get(field_name, {})
                    data[f'{field_name}_localized'] = field_data
                
                # 메타데이터 추가
                data['current_language'] = localized_data['current_language']
                data['available_language'] = localized_data['available_languages']
        
        return data


# =============================================================================
# 🎯 선택지 형식 보존 스마트 번역 시스템
# =============================================================================
# 중요: ABCD 선택지 형식을 감지하여 개별 번역으로 형식을 보존
# - 일반 텍스트: 기존 방식대로 전체 번역
# - 선택지 형식: 각 선택지를 개별 번역하여 ABCD 형식 유지
# =============================================================================

def is_choice_format(content: str) -> bool:
    """
    내용이 ABCD 선택지 형식인지 판단합니다.
    
    Args:
        content: 검사할 텍스트 내용
    
    Returns:
        bool: 선택지 형식이면 True, 일반 텍스트면 False
    """
    if not content or not isinstance(content, str):
        return False
    
    import re
    
    # 선택지 패턴: a., b., c., d. 또는 A., B., C., D. 또는 1., 2., 3., 4.
    choice_patterns = [
        r'^[a-d]\.\s+.+$',      # a. 내용, b. 내용...
        r'^[A-D]\.\s+.+$',      # A. 내용, B. 내용...
        r'^[1-4]\.\s+.+$',      # 1. 내용, 2. 내용...
        r'^\([a-d]\)\s+.+$',    # (a) 내용, (b) 내용...
        r'^\([A-D]\)\s+.+$',    # (A) 내용, (B) 내용...
    ]
    
    lines = content.strip().split('\n')
    if len(lines) < 2:  # 최소 2개 선택지가 있어야 함
        return False
    
    choice_count = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        for pattern in choice_patterns:
            if re.match(pattern, line):
                choice_count += 1
                break
    
    # 2개 이상의 선택지가 감지되면 선택지 형식으로 판단
    is_choice = choice_count >= 2
    logger.info(f"[CHOICE_DETECT] 선택지 형식 감지: {is_choice} (감지된 선택지 수: {choice_count})")
    return is_choice


def translate_choices_with_format(content: str, target_lang: str = 'en', from_lang: str = None) -> str:
    """
    ABCD 선택지 형식을 유지하면서 번역합니다.
    
    Args:
        content: 번역할 선택지 내용
        target_lang: 대상 언어
        from_lang: 원본 언어 (지정하지 않으면 자동 감지)
    
    Returns:
        str: 번역된 선택지 내용 (ABCD 형식 유지)
    """
    if not content or not isinstance(content, str):
        return content
    
    import re
    
    # 선택지 패턴 감지 (a., b., c., d. 또는 A., B., C., D. 또는 1., 2., 3., 4.)
    choice_patterns = [
        (r'^([a-d])\.\s*(.+)$', r'\1.'),
        (r'^([A-D])\.\s*(.+)$', r'\1.'),
        (r'^([1-4])\.\s*(.+)$', r'\1.'),
        (r'^\(([a-d])\)\s*(.+)$', r'(\1)'),
        (r'^\(([A-D])\)\s*(.+)$', r'(\1)'),
    ]
    
    lines = content.split('\n')
    translated_lines = []
    
    logger.info(f"[CHOICE_TRANSLATE] 선택지 개별 번역 시작: {len(lines)}개 라인")
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            translated_lines.append('')
            continue
            
        choice_detected = False
        for pattern, replacement in choice_patterns:
            match = re.match(pattern, line)
            if match:
                # 선택지 형식 감지됨
                choice_marker = re.sub(pattern, replacement, line, count=1)
                choice_text = match.group(2)  # 선택지 내용
                
                logger.info(f"[CHOICE_TRANSLATE] 선택지 {i+1} 감지: {choice_marker} - {choice_text[:50]}...")
                
                # 개별 선택지 번역
                try:
                    translated_text = translate_text(choice_text, target_lang, from_lang)
                    translated_lines.append(f"{choice_marker} {translated_text}")
                    logger.info(f"[CHOICE_TRANSLATE] 선택지 {i+1} 번역 완료: {choice_marker} - {translated_text[:50]}...")
                except Exception as e:
                    logger.warning(f"[CHOICE_TRANSLATE] 선택지 {i+1} 번역 실패: {e}, 원본 유지")
                    translated_lines.append(line)  # 번역 실패 시 원본 유지
                
                choice_detected = True
                break
        
        if not choice_detected:
            # 일반 텍스트는 그대로 번역
            try:
                translated_text = translate_text(line, target_lang, from_lang)
                translated_lines.append(translated_text)
                logger.info(f"[CHOICE_TRANSLATE] 일반 텍스트 {i+1} 번역 완료: {translated_text[:50]}...")
            except Exception as e:
                logger.warning(f"[CHOICE_TRANSLATE] 일반 텍스트 {i+1} 번역 실패: {e}, 원본 유지")
                translated_lines.append(line)  # 번역 실패 시 원본 유지
    
    result = '\n'.join(translated_lines)
    logger.info(f"[CHOICE_TRANSLATE] 선택지 형식 번역 완료: {len(lines)}개 라인")
    return result


def translate_text(text: str, target_lang: str = None, from_lang: str = None) -> str:
    if target_lang is None:
        target_lang = LANGUAGE_KO
    """
    단일 텍스트를 번역합니다. 긴 텍스트는 자동으로 분할하여 번역합니다.
    
    Args:
        text: 번역할 텍스트
        target_lang: 대상 언어
        from_lang: 원본 언어 (지정하지 않으면 자동 감지)
    
    Returns:
        str: 번역된 텍스트
    """
    if not text or not isinstance(text, str):
        return text
    
    # 원본 언어가 지정되지 않은 경우에만 자동 감지
    if from_lang is None:
        from_lang = 'en' if any(ord(c) < 128 for c in text[:100]) else 'en'
    
    # 긴 텍스트 분할 번역 (700자 이상 시)
    # 한국어→영어 번역 시 토큰이 약 2배 증가, 안전하게 700자에서 분할
    # 700자 * 2 = 1400 토큰 + 오버헤드 500 = ~1900 토큰 (4096 이하 안전)
    # JSON 이스케이프 문제를 줄이기 위해 청크를 작게 유지
    if len(text) > 700:
        logger.info(f"[TRANSLATE_TEXT] 긴 텍스트 감지({len(text)}자) → 분할 번역 시작")
        result = translate_long_text_in_chunks(text, from_lang, target_lang, chunk_size=700)
        if result:
            return result
        else:
            logger.warning(f"[TRANSLATE_TEXT] 분할 번역 실패 → 원본 그대로 단일 번역 시도")
            # 분할 번역 실패 시 원본 그대로 시도 (fallback)
    
    # 단일 텍스트를 리스트로 변환하여 배치 번역 함수 사용
    translated_list = batch_translate_texts([text], from_lang, target_lang)
    
    # 번역 실패 시 원본을 반환하지 말고 None 반환 (잘못된 언어 데이터 저장 방지)
    if translated_list and translated_list[0]:
        return translated_list[0]
    else:
        logger.error(f"[TRANSLATE_TEXT] 번역 실패 - 원본 반환하지 않음: {text[:100]}...")
        return None  # 번역 실패 시 None 반환하여 잘못된 데이터 저장 방지


def smart_translate_content(content: str, target_lang: str = None, from_lang: str = None) -> str:
    if target_lang is None:
        target_lang = LANGUAGE_KO
    """
    스마트 번역: 선택지 형식일 때만 개별 번역, 일반 텍스트는 전체 번역
    
    Args:
        content: 번역할 텍스트 내용
        target_lang: 대상 언어
        from_lang: 원본 언어 (지정하지 않으면 자동 감지)
    
    Returns:
        str: 번역된 텍스트 (선택지 형식 보존)
    """
    if not content or not isinstance(content, str):
        return content
    
    logger.info(f"[SMART_TRANSLATE] 스마트 번역 시작: {len(content)}자, 대상 언어: {target_lang}, 원본 언어: {from_lang or '자동감지'}")
    
    if is_choice_format(content):
        # 선택지 형식 감지됨 → 개별 번역으로 형식 보존
        logger.info(f"[SMART_TRANSLATE] 선택지 형식 감지됨 → 개별 번역 적용")
        return translate_choices_with_format(content, target_lang, from_lang)
    else:
        # 일반 텍스트 → 기존 방식대로 전체 번역
        logger.info(f"[SMART_TRANSLATE] 일반 텍스트 감지됨 → 전체 번역 적용")
        return translate_text(content, target_lang, from_lang)


# 답안 판단 프롬프트 템플릿 캐시
_answer_check_template_cache = None

def load_answer_check_template():
    """ai/prompts/answer_check_template.yaml 파일을 로드합니다."""
    global _answer_check_template_cache
    if _answer_check_template_cache is not None:
        return _answer_check_template_cache
    
    try:
        base_dir = settings.BASE_DIR
        yaml_path = os.path.join(base_dir, 'ai', 'prompts', 'answer_check_template.yaml')
        
        if not os.path.exists(yaml_path):
            logger.warning(f"⚠️ 답안 판단 프롬프트 템플릿 YAML 파일을 찾을 수 없습니다: {yaml_path}")
            _answer_check_template_cache = {lang: {'system_prompt': '', 'user_prompt_template': ''} for lang in SUPPORTED_LANGUAGES}
            return _answer_check_template_cache
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            templates = yaml.safe_load(f)
        
        default_templates = {lang: {'system_prompt': '', 'user_prompt_template': ''} for lang in SUPPORTED_LANGUAGES}
        _answer_check_template_cache = templates or default_templates
        logger.info(f"✅ 답안 판단 프롬프트 템플릿 YAML 파일 로드 성공: {yaml_path}")
        return _answer_check_template_cache
    except Exception as e:
        logger.error(f"❌ 답안 판단 프롬프트 템플릿 YAML 파일 로드 실패: {e}", exc_info=True)
        _answer_check_template_cache = {lang: {'system_prompt': '', 'user_prompt_template': ''} for lang in SUPPORTED_LANGUAGES}
        return _answer_check_template_cache


def check_answer_with_ai(user_answer: str, correct_answer: str, language: str = 'en') -> Dict[str, Any]:
    """
    AI를 사용하여 사용자 답안이 정답과 의미적으로 일치하는지 판단합니다.
    OpenAI를 먼저 시도하고, 실패하면 Gemini로 fallback합니다.
    
    Args:
        user_answer: 사용자가 입력한 답안
        correct_answer: 정답
        language: 답안의 언어 (기본값: 'en')
    
    Returns:
        Dict: {
            'is_correct': bool,  # 정답 여부
            'confidence': float,  # 신뢰도 (0.0 ~ 1.0)
            'reason': str,  # 판단 이유
            'provider': str  # 사용한 AI 제공자 ('openai' 또는 'gemini')
        }
    """
    if not user_answer or not correct_answer:
        return {
            'is_correct': False,
            'confidence': 0.0,
            'reason': '답안이 비어있습니다.',
            'provider': None
        }
    
    # 단순 문자열 비교로 정확히 일치하면 바로 반환 (AI 호출 불필요)
    if user_answer.strip().lower() == correct_answer.strip().lower():
        return {
            'is_correct': True,
            'confidence': 1.0,
            'reason': '답안이 정확히 일치합니다.',
            'provider': 'exact_match'
        }
    
    # OpenAI 사용 가능 여부 확인
    openai_error = None
    is_openai_unavailable = not check_openai_availability()
    
    if not is_openai_unavailable:
        # OpenAI API 시도
        try:
            openai_api_key = getattr(settings, 'OPENAI_API_KEY', None)
            if not openai_api_key:
                openai_error = "OpenAI API 키가 설정되지 않음"
                mark_openai_unavailable()
            else:
                # 프롬프트 템플릿 로드
                templates = load_answer_check_template()
                lang_key = language if language in SUPPORTED_LANGUAGES else BASE_LANGUAGE
                template = templates.get(lang_key, templates.get(BASE_LANGUAGE, {}))
                
                system_prompt = template.get('system_prompt', '')
                user_prompt_template = template.get('user_prompt_template', '')
                
                # 템플릿이 없으면 기본 프롬프트 사용
                if not system_prompt or not user_prompt_template:
                    logger.warning(f"[CHECK_ANSWER] 프롬프트 템플릿이 비어있습니다. 기본 프롬프트 사용 (language: {language})")
                    # 언어 이름 매핑
                    language_names = {
                        LANGUAGE_KO: 'Korean',
                        LANGUAGE_EN: 'English',
                        LANGUAGE_ES: 'Spanish',
                        LANGUAGE_ZH: 'Chinese (Simplified)',
                        LANGUAGE_JA: 'Japanese'
                    }
                    lang_name = language_names.get(language, 'English')
                    
                    system_prompt = f'''You are an expert evaluator for educational assessments. Your task is to determine if a student's answer is semantically equivalent to the correct answer.

Rules:
1. Consider synonyms, paraphrasing, and different phrasings that convey the same meaning
2. Ignore minor spelling mistakes, capitalization, and punctuation differences
3. For technical terms, be strict but allow common abbreviations
4. Return ONLY a valid JSON object with this exact format:
{{"is_correct": true/false, "confidence": 0.0-1.0, "reason": "brief explanation"}}

Examples:
- Correct: "Paris" vs "paris" → is_correct: true
- Correct: "The capital of France" vs "Paris" → is_correct: true (if context allows)
- Incorrect: "London" vs "Paris" → is_correct: false
'''
                    
                    user_prompt_template = '''Evaluate if the student's answer is correct:

Correct Answer: {correct_answer}
Student Answer: {user_answer}
Language: {language_name}

Return ONLY the JSON object, no other text.'''
                
                # 언어 이름 매핑
                language_names = {
                    LANGUAGE_KO: 'Korean',
                    LANGUAGE_EN: 'English',
                    LANGUAGE_ES: 'Spanish',
                    LANGUAGE_ZH: 'Chinese (Simplified)',
                    LANGUAGE_JA: 'Japanese'
                }
                lang_name = language_names.get(language, 'English')
                
                # 템플릿 변수 치환
                user_prompt = user_prompt_template.format(
                    correct_answer=correct_answer,
                    user_answer=user_answer,
                    language_name=lang_name
                )
                
                headers = {
                    'Authorization': f'Bearer {openai_api_key}',
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    'model': 'gpt-3.5-turbo',
                    'messages': [
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': user_prompt}
                    ],
                    'max_tokens': 200,
                    'temperature': 0.1
                }
                
                response = requests.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers=headers,
                    json=payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    response_content = result['choices'][0]['message']['content'].strip()
                    
                    # JSON 파싱
                    try:
                        # 마크다운 코드 블록 제거
                        cleaned_content = re.sub(r'^```(?:json)?\s*\n?', '', response_content)
                        cleaned_content = re.sub(r'\n?```\s*$', '', cleaned_content)
                        cleaned_content = cleaned_content.strip()
                        
                        response_obj = json.loads(cleaned_content)
                        
                        if isinstance(response_obj, dict) and 'is_correct' in response_obj:
                            return {
                                'is_correct': bool(response_obj.get('is_correct', False)),
                                'confidence': float(response_obj.get('confidence', 0.5)),
                                'reason': str(response_obj.get('reason', '')),
                                'provider': 'openai'
                            }
                    except json.JSONDecodeError as e:
                        logger.error(f"[CHECK_ANSWER] OpenAI JSON 파싱 실패: {e}, 응답: {response_content[:200]}")
                        openai_error = f"JSON 파싱 실패: {e}"
                else:
                    openai_error = f"OpenAI API 오류: {response.status_code}"
                    if response.status_code == 429:
                        mark_openai_unavailable()
        except Exception as e:
            openai_error = f"OpenAI API 호출 실패: {str(e)}"
            logger.error(f"[CHECK_ANSWER] OpenAI 오류: {e}")
            if '429' in str(e) or 'quota' in str(e).lower():
                mark_openai_unavailable()
    
    # Gemini fallback
    try:
        try:
            import google.generativeai as genai
        except ImportError:
            logger.warning("[CHECK_ANSWER] google-generativeai 패키지가 설치되지 않음")
            return {
                'is_correct': False,
                'confidence': 0.0,
                'reason': 'AI 서비스를 사용할 수 없습니다.',
                'provider': None
            }
        
        gemini_api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not gemini_api_key:
            logger.warning("[CHECK_ANSWER] Gemini API 키가 설정되지 않음")
            return {
                'is_correct': False,
                'confidence': 0.0,
                'reason': 'AI 서비스를 사용할 수 없습니다.',
                'provider': None
            }
        
        genai.configure(api_key=gemini_api_key)
        
        # 모델 생성
        model_names_to_try = [
            getattr(settings, 'GEMINI_MODEL', 'gemini-pro'),
            'gemini-2.5-flash',
            'gemini-pro',
            'gemini-1.5-pro',
        ]
        
        model = None
        for name in model_names_to_try:
            try:
                model = genai.GenerativeModel(name)
                break
            except:
                continue
        
        if not model:
            raise ValueError("사용 가능한 Gemini 모델을 찾을 수 없습니다")
        
        # 프롬프트 템플릿 로드
        templates = load_answer_check_template()
        lang_key = language if language in SUPPORTED_LANGUAGES else BASE_LANGUAGE
        template = templates.get(lang_key, templates.get(BASE_LANGUAGE, {}))
        
        system_prompt = template.get('system_prompt', '')
        user_prompt_template = template.get('user_prompt_template', '')
        
        # 템플릿이 없으면 기본 프롬프트 사용
        if not system_prompt or not user_prompt_template:
            logger.warning(f"[CHECK_ANSWER] 프롬프트 템플릿이 비어있습니다. 기본 프롬프트 사용 (language: {language})")
            # 언어 이름 매핑
            language_names = {
                LANGUAGE_KO: 'Korean',
                LANGUAGE_EN: 'English',
                LANGUAGE_ES: 'Spanish',
                LANGUAGE_ZH: 'Chinese (Simplified)',
                LANGUAGE_JA: 'Japanese'
            }
            lang_name = language_names.get(language, 'English')
            
            gemini_prompt = f'''You are an expert evaluator for educational assessments. Determine if the student's answer is semantically equivalent to the correct answer.

Rules:
1. Consider synonyms, paraphrasing, and different phrasings that convey the same meaning
2. Ignore minor spelling mistakes, capitalization, and punctuation differences
3. For technical terms, be strict but allow common abbreviations
4. Return ONLY a valid JSON object with this exact format:
{{"is_correct": true/false, "confidence": 0.0-1.0, "reason": "brief explanation"}}

Correct Answer: {correct_answer}
Student Answer: {user_answer}
Language: {lang_name}

Return ONLY the JSON object, no other text.'''
        else:
            # 언어 이름 매핑
            language_names = {
                LANGUAGE_KO: 'Korean',
                LANGUAGE_EN: 'English',
                LANGUAGE_ES: 'Spanish',
                LANGUAGE_ZH: 'Chinese (Simplified)',
                LANGUAGE_JA: 'Japanese'
            }
            lang_name = language_names.get(language, 'English')
            
            # 템플릿 변수 치환 (Gemini는 system/user 구분 없이 하나의 프롬프트로)
            gemini_prompt = f"{system_prompt}\n\n{user_prompt_template.format(correct_answer=correct_answer, user_answer=user_answer, language_name=lang_name)}"
        
        response = model.generate_content(
            gemini_prompt,
            generation_config={
                'temperature': 0.1,
                'max_output_tokens': 200,
            }
        )
        
        if not response or not response.candidates:
            raise ValueError("Gemini API 응답이 비어있습니다")
        
        ai_response = response.text.strip()
        
        # JSON 파싱
        try:
            cleaned_content = re.sub(r'^```(?:json)?\s*\n?', '', ai_response)
            cleaned_content = re.sub(r'\n?```\s*$', '', cleaned_content)
            cleaned_content = cleaned_content.strip()
            
            response_obj = json.loads(cleaned_content)
            
            if isinstance(response_obj, dict) and 'is_correct' in response_obj:
                return {
                    'is_correct': bool(response_obj.get('is_correct', False)),
                    'confidence': float(response_obj.get('confidence', 0.5)),
                    'reason': str(response_obj.get('reason', '')),
                    'provider': 'gemini'
                }
        except json.JSONDecodeError as e:
            logger.error(f"[CHECK_ANSWER] Gemini JSON 파싱 실패: {e}, 응답: {ai_response[:200]}")
    
    except Exception as gemini_error:
        logger.error(f"[CHECK_ANSWER] Gemini API 호출 실패: {gemini_error}")
    
    # 모든 AI 서비스 실패 시 기본값 반환 (단순 비교)
    return {
        'is_correct': False,
        'confidence': 0.0,
        'reason': 'AI 서비스를 사용할 수 없어 정확한 판단을 할 수 없습니다.',
        'provider': None
    }
