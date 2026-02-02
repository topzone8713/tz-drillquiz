#!/usr/bin/env python3
"""
DrillQuiz 번역 유틸리티 모듈
Bulk 번역 기능을 제공하여 API 호출을 최소화하고 비용을 절약합니다.
"""

import logging
import requests
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

class TranslationManager:
    """
    번역 관리를 위한 중앙화된 클래스
    Bulk 번역을 통해 API 호출을 최소화하고 캐싱을 활용합니다.
    """
    
    CACHE_PREFIX = "translation"
    CACHE_TIMEOUT = 86400 * 30  # 30일
    
    @classmethod
    def translate_bulk_to_english(cls, texts_dict: Dict[str, str]) -> Dict[str, str]:
        """
        한국어 텍스트들을 영어로 벌크 번역합니다.
        
        Args:
            texts_dict: 번역할 텍스트들의 딕셔너리
                예: {'title': '한국어 제목', 'goal': '한국어 목표'}
        
        Returns:
            번역된 텍스트들의 딕셔너리
        """
        if not texts_dict or not any(texts_dict.values()):
            logger.info("번역할 텍스트가 없습니다.")
            return {}
        
        # 캐시에서 먼저 확인
        cached_results = cls._get_cached_translations(texts_dict, 'ko_to_en')
        if cached_results:
            logger.info(f"[BULK_TRANSLATION] 캐시에서 {len(cached_results)}개 번역 결과 로드")
            return cached_results
        
        # 번역이 필요한 텍스트만 필터링
        texts_to_translate = {k: v for k, v in texts_dict.items() if v and k not in cached_results}
        
        if not texts_to_translate:
            return cached_results
        
        try:
            translated_dict = cls._call_openai_api(texts_to_translate, 'ko_to_en')
            
            # 캐시에 저장
            cls._cache_translations(texts_to_translate, translated_dict, 'ko_to_en')
            
            # 기존 캐시 결과와 병합
            result = {**cached_results, **translated_dict}
            logger.info(f"[BULK_TRANSLATION] 한국어->영어 벌크 번역 완료: {list(texts_dict.keys())} -> {list(result.keys())}")
            return result
            
        except Exception as e:
            logger.error(f'벌크 번역 중 오류: {str(e)}')
            return cached_results
    
    @classmethod
    def translate_bulk_to_korean(cls, texts_dict: Dict[str, str]) -> Dict[str, str]:
        """
        영어 텍스트들을 한국어로 벌크 번역합니다.
        
        Args:
            texts_dict: 번역할 텍스트들의 딕셔너리
                예: {'title': 'English Title', 'goal': 'English Goal'}
        
        Returns:
            번역된 텍스트들의 딕셔너리
        """
        if not texts_dict or not any(texts_dict.values()):
            logger.info("번역할 텍스트가 없습니다.")
            return {}
        
        # 캐시에서 먼저 확인
        cached_results = cls._get_cached_translations(texts_dict, 'en_to_ko')
        if cached_results:
            logger.info(f"[BULK_TRANSLATION] 캐시에서 {len(cached_results)}개 번역 결과 로드")
            return cached_results
        
        # 번역이 필요한 텍스트만 필터링
        texts_to_translate = {k: v for k, v in texts_dict.items() if v and k not in cached_results}
        
        if not texts_to_translate:
            return cached_results
        
        try:
            translated_dict = cls._call_openai_api(texts_to_translate, 'en_to_ko')
            
            # 캐시에 저장
            cls._cache_translations(texts_to_translate, translated_dict, 'en_to_ko')
            
            # 기존 캐시 결과와 병합
            result = {**cached_results, **translated_dict}
            logger.info(f"[BULK_TRANSLATION] 영어->한국어 벌크 번역 완료: {list(texts_dict.keys())} -> {list(result.keys())}")
            return result
            
        except Exception as e:
            logger.error(f'벌크 번역 중 오류: {str(e)}')
            return cached_results
    
    @classmethod
    def translate_single_to_english(cls, text: str) -> str:
        """
        단일 한국어 텍스트를 영어로 번역합니다. (호환성을 위해 유지)
        내부적으로 벌크 번역을 사용하여 효율성을 높입니다.
        """
        if not text:
            return ""
        
        translated_dict = cls.translate_bulk_to_english({'text': text})
        return translated_dict.get('text', '')
    
    @classmethod
    def translate_single_to_korean(cls, text: str) -> str:
        """
        단일 영어 텍스트를 한국어로 번역합니다. (호환성을 위해 유지)
        내부적으로 벌크 번역을 사용하여 효율성을 높입니다.
        """
        if not text:
            return ""
        
        translated_dict = cls.translate_bulk_to_korean({'text': text})
        return translated_dict.get('text', '')
    
    @classmethod
    def translate_bulk_to_spanish(cls, texts_dict: Dict[str, str]) -> Dict[str, str]:
        """
        한국어 또는 영어 텍스트들을 스페인어로 벌크 번역합니다.
        
        Args:
            texts_dict: 번역할 텍스트들의 딕셔너리
        
        Returns:
            번역된 텍스트들의 딕셔너리
        """
        if not texts_dict or not any(texts_dict.values()):
            logger.info("번역할 텍스트가 없습니다.")
            return {}
        
        # Try ko_to_es first, then en_to_es
        cached_results = cls._get_cached_translations(texts_dict, 'ko_to_es')
        if not cached_results:
            cached_results = cls._get_cached_translations(texts_dict, 'en_to_es')
        
        if cached_results:
            logger.info(f"[BULK_TRANSLATION] 캐시에서 {len(cached_results)}개 번역 결과 로드")
            return cached_results
        
        # 번역이 필요한 텍스트만 필터링
        texts_to_translate = {k: v for k, v in texts_dict.items() if v and k not in cached_results}
        
        if not texts_to_translate:
            return cached_results
        
        try:
            # Try ko_to_es first
            translated_dict = cls._call_openai_api(texts_to_translate, 'ko_to_es')
            
            # If that fails, try en_to_es
            if not translated_dict:
                translated_dict = cls._call_openai_api(texts_to_translate, 'en_to_es')
            
            if translated_dict:
                # 캐시에 저장
                cls._cache_translations(texts_to_translate, translated_dict, 'ko_to_es')
                
                # 기존 캐시 결과와 병합
                result = {**cached_results, **translated_dict}
                logger.info(f"[BULK_TRANSLATION] 스페인어 벌크 번역 완료: {list(texts_dict.keys())} -> {list(result.keys())}")
                return result
            else:
                return cached_results
                
        except Exception as e:
            logger.error(f'벌크 번역 중 오류: {str(e)}')
            return cached_results
    
    @classmethod
    def translate_single_to_spanish(cls, text: str) -> str:
        """
        단일 텍스트를 스페인어로 번역합니다. (호환성을 위해 유지)
        내부적으로 벌크 번역을 사용하여 효율성을 높입니다.
        """
        if not text:
            return ""
        
        translated_dict = cls.translate_bulk_to_spanish({'text': text})
        return translated_dict.get('text', '')
    
    @classmethod
    def translate_bulk_to_japanese(cls, texts_dict: Dict[str, str]) -> Dict[str, str]:
        """
        한국어 또는 영어 텍스트들을 일본어로 벌크 번역합니다.
        
        Args:
            texts_dict: 번역할 텍스트들의 딕셔너리
        
        Returns:
            번역된 텍스트들의 딕셔너리
        """
        if not texts_dict or not any(texts_dict.values()):
            logger.info("번역할 텍스트가 없습니다.")
            return {}
        
        # Try ko_to_ja first, then en_to_ja
        cached_results = cls._get_cached_translations(texts_dict, 'ko_to_ja')
        if not cached_results:
            cached_results = cls._get_cached_translations(texts_dict, 'en_to_ja')
        
        if cached_results:
            logger.info(f"[BULK_TRANSLATION] 캐시에서 {len(cached_results)}개 번역 결과 로드")
            return cached_results
        
        # 번역이 필요한 텍스트만 필터링
        texts_to_translate = {k: v for k, v in texts_dict.items() if v and k not in cached_results}
        
        if not texts_to_translate:
            return cached_results
        
        try:
            # Try ko_to_ja first
            translated_dict = cls._call_openai_api(texts_to_translate, 'ko_to_ja')
            
            # If that fails, try en_to_ja
            if not translated_dict:
                translated_dict = cls._call_openai_api(texts_to_translate, 'en_to_ja')
            
            if translated_dict:
                # 캐시에 저장
                cls._cache_translations(texts_to_translate, translated_dict, 'ko_to_ja')
                
                # 기존 캐시 결과와 병합
                result = {**cached_results, **translated_dict}
                logger.info(f"[BULK_TRANSLATION] 일본어 벌크 번역 완료: {list(texts_dict.keys())} -> {list(result.keys())}")
                return result
            else:
                return cached_results
                
        except Exception as e:
            logger.error(f'벌크 번역 중 오류: {str(e)}')
            return cached_results
    
    @classmethod
    def translate_single_to_japanese(cls, text: str) -> str:
        """
        단일 텍스트를 일본어로 번역합니다. (호환성을 위해 유지)
        내부적으로 벌크 번역을 사용하여 효율성을 높입니다.
        """
        if not text:
            return ""
        
        translated_dict = cls.translate_bulk_to_japanese({'text': text})
        return translated_dict.get('text', '')
    
    @classmethod
    def translate_bulk_to_chinese(cls, texts_dict: Dict[str, str]) -> Dict[str, str]:
        """
        한국어 또는 영어 텍스트들을 중국어로 벌크 번역합니다.
        
        Args:
            texts_dict: 번역할 텍스트들의 딕셔너리
        
        Returns:
            번역된 텍스트들의 딕셔너리
        """
        if not texts_dict or not any(texts_dict.values()):
            logger.info("번역할 텍스트가 없습니다.")
            return {}
        
        # Try ko_to_zh first, then en_to_zh
        cached_results = cls._get_cached_translations(texts_dict, 'ko_to_zh')
        if not cached_results:
            cached_results = cls._get_cached_translations(texts_dict, 'en_to_zh')
        
        if cached_results:
            logger.info(f"[BULK_TRANSLATION] 캐시에서 {len(cached_results)}개 번역 결과 로드")
            return cached_results
        
        # 번역이 필요한 텍스트만 필터링
        texts_to_translate = {k: v for k, v in texts_dict.items() if v and k not in cached_results}
        
        if not texts_to_translate:
            return cached_results
        
        try:
            # Try ko_to_zh first
            translated_dict = cls._call_openai_api(texts_to_translate, 'ko_to_zh')
            
            # If that fails, try en_to_zh
            if not translated_dict:
                translated_dict = cls._call_openai_api(texts_to_translate, 'en_to_zh')
            
            if translated_dict:
                # 캐시에 저장
                cls._cache_translations(texts_to_translate, translated_dict, 'ko_to_zh')
                
                # 기존 캐시 결과와 병합
                result = {**cached_results, **translated_dict}
                logger.info(f"[BULK_TRANSLATION] 중국어 벌크 번역 완료: {list(texts_dict.keys())} -> {list(result.keys())}")
                return result
            else:
                return cached_results
                
        except Exception as e:
            logger.error(f'벌크 번역 중 오류: {str(e)}')
            return cached_results
    
    @classmethod
    def translate_single_to_chinese(cls, text: str) -> str:
        """
        단일 텍스트를 중국어로 번역합니다. (호환성을 위해 유지)
        내부적으로 벌크 번역을 사용하여 효율성을 높입니다.
        """
        if not text:
            return ""
        
        translated_dict = cls.translate_bulk_to_chinese({'text': text})
        return translated_dict.get('text', '')
    
    @classmethod
    def _call_openai_api(cls, texts_dict: Dict[str, str], direction: str) -> Dict[str, str]:
        """
        OpenAI API를 호출하여 번역을 수행합니다.
        """
        # OpenAI 사용 가능 여부 확인 (캐시 체크)
        from quiz.utils.multilingual_utils import check_openai_availability, mark_openai_unavailable
        is_openai_unavailable = not check_openai_availability()
        
        # OpenAI가 사용 불가능하면 빈 딕셔너리 반환
        if is_openai_unavailable:
            logger.warning(f"[TranslationManager._call_openai_api] OpenAI가 캐시에서 사용 불가능 상태로 확인됨, 번역 건너뜀 ({direction})")
            return {}
        
        openai_api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not openai_api_key:
            logger.warning("OpenAI API 키가 설정되지 않았습니다.")
            mark_openai_unavailable()
            return {}
        
        # 번역 방향에 따른 프롬프트 설정 (더 명확하고 일관된 응답을 위해)
        if direction == 'ko_to_en':
            system_content = 'You are a helpful assistant that translates Korean text to English. Always respond with the format "ITEM_key: translated_text" for each item, one per line.'
            user_prompt = "다음 한국어 텍스트들을 영어로 번역해주세요. 반드시 'ITEM_key: 번역결과' 형식으로 응답해주세요:\n\n"
        elif direction == 'en_to_ko':
            system_content = 'You are a helpful assistant that translates English text to Korean. Always respond with the format "ITEM_key: translated_text" for each item, one per line.'
            user_prompt = "다음 영어 텍스트들을 한국어로 번역해주세요. 반드시 'ITEM_key: 번역결과' 형식으로 응답해주세요:\n\n"
        elif direction == 'ko_to_es':
            system_content = 'You are a helpful assistant that translates Korean text to Spanish. Always respond with the format "ITEM_key: translated_text" for each item, one per line.'
            user_prompt = "다음 한국어 텍스트들을 스페인어로 번역해주세요. 반드시 'ITEM_key: 번역결과' 형식으로 응답해주세요:\n\n"
        elif direction == 'en_to_es':
            system_content = 'You are a helpful assistant that translates English text to Spanish. Always respond with the format "ITEM_key: translated_text" for each item, one per line.'
            user_prompt = "다음 영어 텍스트들을 스페인어로 번역해주세요. 반드시 'ITEM_key: 번역결과' 형식으로 응답해주세요:\n\n"
        elif direction == 'es_to_ko':
            system_content = 'You are a helpful assistant that translates Spanish text to Korean. Always respond with the format "ITEM_key: translated_text" for each item, one per line.'
            user_prompt = "다음 스페인어 텍스트들을 한국어로 번역해주세요. 반드시 'ITEM_key: 번역결과' 형식으로 응답해주세요:\n\n"
        elif direction == 'es_to_en':
            system_content = 'You are a helpful assistant that translates Spanish text to English. Always respond with the format "ITEM_key: translated_text" for each item, one per line.'
            user_prompt = "다음 스페인어 텍스트들을 영어로 번역해주세요. 반드시 'ITEM_key: 번역결과' 형식으로 응답해주세요:\n\n"
        elif direction == 'ko_to_ja':
            system_content = 'You are a helpful assistant that translates Korean text to Japanese. Always respond with the format "ITEM_key: translated_text" for each item, one per line.'
            user_prompt = "다음 한국어 텍스트들을 일본어로 번역해주세요. 반드시 'ITEM_key: 번역결과' 형식으로 응답해주세요:\n\n"
        elif direction == 'en_to_ja':
            system_content = 'You are a helpful assistant that translates English text to Japanese. Always respond with the format "ITEM_key: translated_text" for each item, one per line.'
            user_prompt = "다음 영어 텍스트들을 일본어로 번역해주세요. 반드시 'ITEM_key: 번역결과' 형식으로 응답해주세요:\n\n"
        elif direction == 'ja_to_ko':
            system_content = 'You are a helpful assistant that translates Japanese text to Korean. Always respond with the format "ITEM_key: translated_text" for each item, one per line.'
            user_prompt = "다음 일본어 텍스트들을 한국어로 번역해주세요. 반드시 'ITEM_key: 번역결과' 형식으로 응답해주세요:\n\n"
        elif direction == 'ja_to_en':
            system_content = 'You are a helpful assistant that translates Japanese text to English. Always respond with the format "ITEM_key: translated_text" for each item, one per line.'
            user_prompt = "다음 일본어 텍스트들을 영어로 번역해주세요. 반드시 'ITEM_key: 번역결과' 형식으로 응답해주세요:\n\n"
        elif direction == 'ko_to_zh':
            system_content = 'You are a helpful assistant that translates Korean text to Chinese (Simplified). Always respond with the format "ITEM_key: translated_text" for each item, one per line.'
            user_prompt = "다음 한국어 텍스트들을 중국어(간체)로 번역해주세요. 반드시 'ITEM_key: 번역결과' 형식으로 응답해주세요:\n\n"
        elif direction == 'en_to_zh':
            system_content = 'You are a helpful assistant that translates English text to Chinese (Simplified). Always respond with the format "ITEM_key: translated_text" for each item, one per line.'
            user_prompt = "다음 영어 텍스트들을 중국어(간체)로 번역해주세요. 반드시 'ITEM_key: 번역결과' 형식으로 응답해주세요:\n\n"
        elif direction == 'zh_to_ko':
            system_content = 'You are a helpful assistant that translates Chinese (Simplified) text to Korean. Always respond with the format "ITEM_key: translated_text" for each item, one per line.'
            user_prompt = "다음 중국어(간체) 텍스트들을 한국어로 번역해주세요. 반드시 'ITEM_key: 번역결과' 형식으로 응답해주세요:\n\n"
        elif direction == 'zh_to_en':
            system_content = 'You are a helpful assistant that translates Chinese (Simplified) text to English. Always respond with the format "ITEM_key: translated_text" for each item, one per line.'
            user_prompt = "다음 중국어(간체) 텍스트들을 영어로 번역해주세요. 반드시 'ITEM_key: 번역결과' 형식으로 응답해주세요:\n\n"
        else:
            logger.warning(f"지원하지 않는 번역 방향: {direction}")
            return {}
        
        # 번역 요청을 위한 프롬프트 구성 (더 명확한 키 사용)
        for key, text in texts_dict.items():
            if text:  # 빈 문자열이 아닌 경우만
                user_prompt += f"ITEM_{key}: {text}\n"
        
        # OpenAI API 호출
        headers = {
            'Authorization': f'Bearer {openai_api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'gpt-3.5-turbo',
            'messages': [
                {
                    'role': 'system',
                    'content': system_content
                },
                {
                    'role': 'user',
                    'content': user_prompt
                }
            ],
            'max_tokens': 500,  # 더 긴 응답을 위해 증가
            'temperature': 0.3
        }
        
        try:
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=30
            )
        except Exception as e:
            logger.error(f"[TranslationManager._call_openai_api] OpenAI API 요청 실패: {e}")
            mark_openai_unavailable()
            return {}
        
        if response.status_code == 200:
            result = response.json()
            translated_content = result['choices'][0]['message']['content'].strip()
            
            # 디버깅: API 응답 내용 로깅
            logger.debug(f"OpenAI API 응답 원본: {translated_content}")
            
            # 번역 결과를 파싱하여 딕셔너리로 변환 (개선된 파싱)
            translated_dict = {}
            lines = translated_content.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                logger.debug(f"파싱 시도: '{line}'")
                
                # ITEM_key: value 형식 파싱
                if line.startswith('ITEM_'):
                    try:
                        key_part, value = line.split(':', 1)
                        key = key_part.replace('ITEM_', '').strip()
                        value = value.strip()
                        
                        # 원본 키와 매칭
                        if key in texts_dict.keys():
                            # ITEM_key: 다음에 오는 모든 내용을 수집
                            full_value = [value]  # 첫 줄 값
                            
                            # 다음 줄들을 확인하여 ITEM_으로 시작하지 않는 내용을 수집
                            i = lines.index(line) + 1
                            while i < len(lines) and not lines[i].startswith('ITEM_') and lines[i].strip():
                                full_value.append(lines[i].strip())
                                i += 1
                            
                            # 모든 내용을 하나로 합침
                            final_value = '\n'.join(full_value)
                            translated_dict[key] = final_value
                            logger.debug(f"번역 결과 파싱 성공: {key} -> {final_value[:100]}...")
                    except ValueError:
                        logger.warning(f"번역 결과 파싱 실패: {line}")
                        continue
                
                # 일반적인 key: value 형식도 지원
                elif ':' in line:
                    try:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # 원본 키와 매칭 (대소문자 무시)
                        for original_key in texts_dict.keys():
                            if key.lower() == original_key.lower():
                                translated_dict[original_key] = value
                                logger.debug(f"번역 결과 파싱 성공: {original_key} -> {value}")
                                break
                    except ValueError:
                        logger.warning(f"번역 결과 파싱 실패: {line}")
                        continue
            
            # 파싱 결과 로깅
            logger.info(f"번역 결과 파싱: {len(texts_dict)}개 요청 -> {len(translated_dict)}개 성공")
            if len(translated_dict) != len(texts_dict):
                logger.warning(f"일부 번역 결과 파싱 실패: {set(texts_dict.keys()) - set(translated_dict.keys())}")
                logger.debug(f"요청된 키: {list(texts_dict.keys())}")
                logger.debug(f"파싱된 키: {list(translated_dict.keys())}")
            
            return translated_dict
        else:
            # 429 에러(quota 초과) 또는 insufficient_quota 에러는 즉시 캐시에 마킹
            error_detail = None
            try:
                error_detail = response.json()
            except:
                pass
            
            if response.status_code == 429:
                logger.error(f'[TranslationManager._call_openai_api] OpenAI 429/quota 초과 에러: {response.status_code} - {response.text[:200]}')
                if error_detail and 'error' in error_detail:
                    error_code = error_detail['error'].get('code', '')
                    if error_code == 'insufficient_quota':
                        logger.warning(f"[TranslationManager._call_openai_api] OpenAI 429/quota 초과 에러 감지, 즉시 캐시에 마킹...")
                        mark_openai_unavailable()
                else:
                    mark_openai_unavailable()
            else:
                logger.error(f'[TranslationManager._call_openai_api] OpenAI API 오류: {response.status_code} - {response.text[:200]}')
                # 다른 에러도 재시도 방지를 위해 마킹
                mark_openai_unavailable()
            return {}
    
    @classmethod
    def _get_cache_key(cls, text: str, direction: str) -> str:
        """캐시 키를 생성합니다."""
        import hashlib
        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        return f"{cls.CACHE_PREFIX}:{direction}:{text_hash}"
    
    @classmethod
    def _get_cached_translations(cls, texts_dict: Dict[str, str], direction: str) -> Dict[str, str]:
        """캐시된 번역 결과를 가져옵니다."""
        cached_results = {}
        
        for key, text in texts_dict.items():
            if text:
                cache_key = cls._get_cache_key(text, direction)
                cached_text = cache.get(cache_key)
                if cached_text:
                    cached_results[key] = cached_text
        
        return cached_results
    
    @classmethod
    def _cache_translations(cls, original_dict: Dict[str, str], translated_dict: Dict[str, str], direction: str):
        """번역 결과를 캐시에 저장합니다."""
        for key, original_text in original_dict.items():
            if key in translated_dict and translated_dict[key]:
                cache_key = cls._get_cache_key(original_text, direction)
                cache.set(cache_key, translated_dict[key], cls.CACHE_TIMEOUT)
    
    @classmethod
    def clear_cache(cls, direction: Optional[str] = None):
        """
        번역 캐시를 정리합니다.
        
        Args:
            direction: 정리할 번역 방향 ('ko_to_en', 'en_to_ko', None=전체)
        """
        if direction:
            # 특정 방향의 캐시만 정리
            pattern = f"{cls.CACHE_PREFIX}:{direction}:*"
            # Django의 cache.delete_pattern은 지원하지 않으므로 개별 삭제
            logger.info(f"번역 캐시 정리: {direction}")
        else:
            # 전체 번역 캐시 정리
            logger.info("전체 번역 캐시 정리")
        
        # 실제 구현에서는 더 정교한 캐시 정리 로직이 필요할 수 있음
        # 현재는 로그만 출력

class BulkTranslationMixin:
    """
    Bulk 번역 기능을 제공하는 Mixin 클래스
    ViewSet이나 다른 클래스에서 상속받아 사용할 수 있습니다.
    """
    
    def translate_study_fields(self, study, fields_to_translate: Dict[str, str], target_language: str):
        """
        스터디 필드들을 벌크로 번역합니다.
        
        Args:
            study: 번역할 스터디 객체
            fields_to_translate: 번역할 필드들의 딕셔너리
            target_language: 목표 언어
        """
        from quiz.utils.multilingual_utils import LANGUAGE_EN
        if target_language == LANGUAGE_EN:
            translated_dict = TranslationManager.translate_bulk_to_english(fields_to_translate)
        else:
            translated_dict = TranslationManager.translate_bulk_to_korean(fields_to_translate)
        
        # 번역 결과 적용
        update_fields = []
        for field_name, translated_value in translated_dict.items():
            if translated_value:
                setattr(study, f"{field_name}_{target_language}", translated_value)
                update_fields.append(f"{field_name}_{target_language}")
        
        # 변경된 필드들 저장
        if update_fields:
            study.save(update_fields=update_fields)
            logger.info(f"[BULK_TRANSLATION] 스터디 필드 번역 완료: {update_fields}")
        
        return translated_dict
