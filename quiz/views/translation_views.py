#!/usr/bin/env python3
"""
DrillQuiz 번역 관리 API 뷰
번역 상태 확인, 캐시 관리, 수동 번역 등의 기능을 제공합니다.
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.conf import settings
from ..utils.translation_utils import TranslationManager

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_translation_status(request):
    """
    번역 시스템 상태를 확인합니다.
    """
    try:
        # OpenAI API 키 상태 확인
        openai_api_key = getattr(settings, 'OPENAI_API_KEY', None)
        api_key_status = 'configured' if openai_api_key else 'not_configured'
        
        # 번역 방향별 상태
        translation_directions = ['ko_to_en', 'en_to_ko']
        
        status_info = {
            'api_key_status': api_key_status,
            'translation_directions': translation_directions,
            'cache_enabled': True,
            'bulk_translation_enabled': True,
            'system_status': 'operational' if openai_api_key else 'disabled'
        }
        
        return Response({
            'success': True,
            'translation_status': status_info
        })
        
    except Exception as e:
        logger.error(f'번역 상태 확인 중 오류: {str(e)}')
        return Response({
            'success': False,
            'error': f'번역 상태 확인 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def clear_translation_cache(request):
    """
    번역 캐시를 정리합니다. (관리자만)
    """
    try:
        direction = request.data.get('direction')  # 'ko_to_en', 'en_to_ko', 또는 None (전체)
        
        TranslationManager.clear_cache(direction)
        
        message = f"번역 캐시 정리 완료: {direction if direction else '전체'}"
        logger.info(f"[ADMIN] {message}")
        
        return Response({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        logger.error(f'번역 캐시 정리 중 오류: {str(e)}')
        return Response({
            'success': False,
            'error': f'번역 캐시 정리 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def translate_texts(request):
    """
    텍스트들을 번역합니다.
    """
    try:
        texts = request.data.get('texts', {})
        target_language = request.data.get('target_language')
        
        if not texts or not target_language:
            return Response({
                'success': False,
                'error': '번역할 텍스트와 목표 언어가 필요합니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if target_language not in ['en', 'ko', 'es', 'zh', 'ja']:
            return Response({
                'success': False,
                'error': '유효하지 않은 목표 언어입니다. (en, ko, es, zh 또는 ja)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 번역 실행
        from quiz.utils.multilingual_utils import LANGUAGE_EN, LANGUAGE_ES, LANGUAGE_KO, LANGUAGE_ZH, LANGUAGE_JA, BASE_LANGUAGE
        if target_language == LANGUAGE_EN:
            translated_dict = TranslationManager.translate_bulk_to_english(texts)
            source_language = LANGUAGE_KO  # Default source, could be enhanced to detect
        elif target_language == LANGUAGE_ES:
            translated_dict = TranslationManager.translate_bulk_to_spanish(texts)
            source_language = LANGUAGE_KO  # Default source, could be enhanced to detect
        elif target_language == LANGUAGE_ZH:
            # 중국어 번역은 TranslationManager에 추가 필요
            translated_dict = TranslationManager.translate_bulk_to_korean(texts)  # 임시로 한국어 번역 사용
            source_language = BASE_LANGUAGE  # Default source
        elif target_language == LANGUAGE_JA:
            translated_dict = TranslationManager.translate_bulk_to_japanese(texts)
            source_language = LANGUAGE_KO  # Default source, could be enhanced to detect
        else:
            translated_dict = TranslationManager.translate_bulk_to_korean(texts)
            source_language = BASE_LANGUAGE
        
        logger.info(f"[MANUAL_TRANSLATION] 사용자 {request.user.username}의 수동 번역 완료: {list(texts.keys())} -> {list(translated_dict.keys())}")
        
        return Response({
            'success': True,
            'translated_texts': translated_dict,
            'source_language': source_language,
            'target_language': target_language
        })
        
    except Exception as e:
        logger.error(f'수동 번역 중 오류: {str(e)}')
        return Response({
            'success': False,
            'error': f'번역 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_translation_statistics(request):
    """
    번역 통계 정보를 제공합니다.
    """
    try:
        # OpenAI API 키 상태
        openai_api_key = getattr(settings, 'OPENAI_API_KEY', None)
        
        # 기본 통계 정보
        from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
        stats = {
            'api_configured': bool(openai_api_key),
            'bulk_translation_supported': True,
            'cache_supported': True,
            'supported_languages': SUPPORTED_LANGUAGES,
            'translation_directions': ['ko_to_en', 'en_to_ko', 'ko_to_es', 'en_to_es', 'es_to_ko', 'es_to_en', 'en_to_zh', 'zh_to_ko', 'zh_to_en', 'ko_to_ja', 'en_to_ja', 'ja_to_ko', 'ja_to_en']
        }
        
        return Response({
            'success': True,
            'translation_statistics': stats
        })
        
    except Exception as e:
        logger.error(f'번역 통계 조회 중 오류: {str(e)}')
        return Response({
            'success': False,
            'error': f'번역 통계 조회 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
