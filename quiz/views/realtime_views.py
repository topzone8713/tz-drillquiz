"""
OpenAI Realtime API 관련 뷰
음성↔음성 실시간 통신을 위한 API 엔드포인트
"""

import logging
import os
import yaml
import openai
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication
from django.conf import settings
from django.core.cache import cache
from ..models import Exam, Question
from ..utils.multilingual_utils import get_user_language

# Gemini 지원 확인
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

logger = logging.getLogger(__name__)

# 필수 프롬프트 YAML 파일 로드
def load_mandatory_rules():
    """ai/prompts/voice_interview_mandatory_prompts.yaml 파일을 로드합니다."""
    try:
        # Django BASE_DIR 사용
        base_dir = settings.BASE_DIR
        yaml_path = os.path.join(base_dir, 'ai', 'prompts', 'voice_interview_mandatory_prompts.yaml')
        
        if not os.path.exists(yaml_path):
            logger.warning(f"⚠️ 필수 프롬프트 YAML 파일을 찾을 수 없습니다: {yaml_path}")
            return None
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            rules = yaml.safe_load(f)
        
        logger.info(f"✅ 필수 프롬프트 YAML 파일 로드 성공: {yaml_path}")
        return rules
    except Exception as e:
        logger.error(f"❌ 필수 프롬프트 YAML 파일 로드 실패: {e}", exc_info=True)
        return None

# 필수 프롬프트 캐싱 (성능 최적화)
_mandatory_rules_cache = None
_exam_context_template_cache = None
_interview_prompt_template_cache = None
_evaluation_guideline_template_cache = None

def load_exam_context_template():
    """ai/prompts/exam_context_template.yaml 파일을 로드합니다."""
    global _exam_context_template_cache
    if _exam_context_template_cache is not None:
        return _exam_context_template_cache
    
    try:
        base_dir = settings.BASE_DIR
        yaml_path = os.path.join(base_dir, 'ai', 'prompts', 'exam_context_template.yaml')
        
        if not os.path.exists(yaml_path):
            logger.warning(f"⚠️ 시험 컨텍스트 템플릿 YAML 파일을 찾을 수 없습니다: {yaml_path}")
            from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
            _exam_context_template_cache = {lang: {'template': ''} for lang in SUPPORTED_LANGUAGES}
            return _exam_context_template_cache
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            templates = yaml.safe_load(f)
        
        from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
        default_templates = {lang: {'template': ''} for lang in SUPPORTED_LANGUAGES}
        _exam_context_template_cache = templates or default_templates
        logger.info(f"✅ 시험 컨텍스트 템플릿 YAML 파일 로드 성공: {yaml_path}")
        return _exam_context_template_cache
    except Exception as e:
        logger.error(f"❌ 시험 컨텍스트 템플릿 YAML 파일 로드 실패: {e}", exc_info=True)
        from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
        _exam_context_template_cache = {lang: {'template': ''} for lang in SUPPORTED_LANGUAGES}
        return _exam_context_template_cache

def load_interview_prompt_template():
    """ai/prompts/interview_prompt_template.yaml 파일을 로드합니다."""
    global _interview_prompt_template_cache
    if _interview_prompt_template_cache is not None:
        return _interview_prompt_template_cache
    
    try:
        base_dir = settings.BASE_DIR
        yaml_path = os.path.join(base_dir, 'ai', 'prompts', 'interview_prompt_template.yaml')
        
        if not os.path.exists(yaml_path):
            logger.warning(f"⚠️ 인터뷰 프롬프트 템플릿 YAML 파일을 찾을 수 없습니다: {yaml_path}")
            _interview_prompt_template_cache = {
                'ko': {'base_template': '', 'question_restriction': '', 'mandatory_rules_marker': ''},
                'en': {'base_template': '', 'question_restriction': '', 'mandatory_rules_marker': ''},
                'es': {'base_template': '', 'question_restriction': '', 'mandatory_rules_marker': ''},
                'zh': {'base_template': '', 'question_restriction': '', 'mandatory_rules_marker': ''},
                'ja': {'base_template': '', 'question_restriction': '', 'mandatory_rules_marker': ''}
            }
            return _interview_prompt_template_cache
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            templates = yaml.safe_load(f)
        
        _interview_prompt_template_cache = templates or {
            'ko': {'base_template': '', 'question_restriction': '', 'mandatory_rules_marker': ''},
            'en': {'base_template': '', 'question_restriction': '', 'mandatory_rules_marker': ''},
            'es': {'base_template': '', 'question_restriction': '', 'mandatory_rules_marker': ''},
            'zh': {'base_template': '', 'question_restriction': '', 'mandatory_rules_marker': ''},
            'ja': {'base_template': '', 'question_restriction': '', 'mandatory_rules_marker': ''}
        }
        logger.info(f"✅ 인터뷰 프롬프트 템플릿 YAML 파일 로드 성공: {yaml_path}")
        return _interview_prompt_template_cache
    except Exception as e:
        logger.error(f"❌ 인터뷰 프롬프트 템플릿 YAML 파일 로드 실패: {e}", exc_info=True)
        _interview_prompt_template_cache = {
            'ko': {'base_template': '', 'question_restriction': '', 'mandatory_rules_marker': ''},
            'en': {'base_template': '', 'question_restriction': '', 'mandatory_rules_marker': ''},
            'es': {'base_template': '', 'question_restriction': '', 'mandatory_rules_marker': ''},
            'zh': {'base_template': '', 'question_restriction': '', 'mandatory_rules_marker': ''},
            'ja': {'base_template': '', 'question_restriction': '', 'mandatory_rules_marker': ''}
        }
        return _interview_prompt_template_cache

def get_mandatory_rules(language=None):
    from quiz.utils.multilingual_utils import BASE_LANGUAGE
    if language is None:
        language = BASE_LANGUAGE
    """언어별 필수 프롬프트를 반환합니다."""
    global _mandatory_rules_cache
    
    if _mandatory_rules_cache is None:
        _mandatory_rules_cache = load_mandatory_rules()
    
    if _mandatory_rules_cache is None:
        # YAML 파일 로드 실패 시 기본값 반환
        logger.warning("⚠️ YAML 파일 로드 실패, 기본 프롬프트 사용")
        return {
            'language_instruction': '',
            'mandatory_prompts': ''
        }
    
    from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES, LANGUAGE_EN
    lang_key = language if language in SUPPORTED_LANGUAGES else LANGUAGE_EN
    return _mandatory_rules_cache.get(lang_key, {
        'language_instruction': '',
        'mandatory_prompts': ''
    })

# OpenAI 클라이언트 초기화
def get_openai_client():
    """OpenAI 클라이언트를 반환합니다."""
    if not hasattr(settings, 'OPENAI_API_KEY') or not settings.OPENAI_API_KEY:
        raise ValueError("OpenAI API 키가 설정되지 않았습니다.")
    
    return openai.OpenAI(api_key=settings.OPENAI_API_KEY)

# Gemini 클라이언트 초기화
def get_gemini_client():
    """Gemini 클라이언트를 반환합니다."""
    if not GEMINI_AVAILABLE:
        raise ValueError("google-generativeai 패키지가 설치되지 않았습니다.")
    
    gemini_api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if not gemini_api_key:
        raise ValueError("Gemini API 키가 설정되지 않았습니다.")
    
    genai.configure(api_key=gemini_api_key)
    return genai

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_realtime_session(request):
    """OpenAI Realtime API 세션을 생성합니다."""
    from quiz.utils.multilingual_utils import LANGUAGE_KO, LANGUAGE_EN, LANGUAGE_ES, LANGUAGE_ZH, LANGUAGE_JA, BASE_LANGUAGE
    try:
        exam_id = request.data.get('exam_id')
        voice = request.data.get('voice', 'alloy')
        language = request.data.get('language', BASE_LANGUAGE)
        custom_instructions = request.data.get('instructions', '')  # textarea의 내용
        
        # 로그: 받은 데이터 확인 (항상 출력)
        print(f"[세션 생성 요청] exam_id: {exam_id}, voice: {voice}, language: {language}")
        print(f"[세션 생성 요청] custom_instructions 길이: {len(custom_instructions) if custom_instructions else 0}")
        print(f"[세션 생성 요청] request.data 전체: {request.data}")
        logger.info(f"[세션 생성 요청] exam_id: {exam_id}, voice: {voice}, language: {language}")
        logger.info(f"[세션 생성 요청] custom_instructions 길이: {len(custom_instructions) if custom_instructions else 0}")
        if custom_instructions:
            print(f"[세션 생성 요청] custom_instructions 미리보기: {custom_instructions[:200]}...")
            logger.info(f"[세션 생성 요청] custom_instructions 미리보기: {custom_instructions[:200]}...")
        else:
            print("[세션 생성 요청] ⚠️ custom_instructions가 비어있습니다!")
            logger.info("[세션 생성 요청] custom_instructions가 비어있습니다.")
        
        if not exam_id:
            return Response({'error': 'exam_id가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 시험 존재 확인
        try:
            exam = Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            return Response({'error': '시험을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        # 시험 접근 권한 확인
        user = request.user
        if not _has_exam_access(user, exam):
            return Response({'error': '이 시험에 접근할 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
        
        # OpenAI 클라이언트 생성
        client = get_openai_client()
        
        # 시험 컨텍스트 생성
        exam_context = _create_exam_context(exam, language)
        
        # 사용자가 제공한 instructions가 있으면 기존 컨텍스트와 결합
        if custom_instructions and custom_instructions.strip():
            # 사용자 지정 지침과 시험 컨텍스트만 사용 (필수 규칙 제거)
            final_instructions = f"""{custom_instructions}

=== 시험 컨텍스트 ===
{exam_context}"""
            print(f"[세션 생성] ✅ 사용자 지정 instructions 사용: {len(custom_instructions)} 문자")
            print(f"[세션 생성] 사용자 지정 instructions 미리보기: {custom_instructions[:200]}...")
            print(f"[세션 생성] final_instructions 길이: {len(final_instructions)} 문자")
            logger.info(f"[세션 생성] 사용자 지정 instructions 사용: {len(custom_instructions)} 문자")
            logger.info(f"[세션 생성] 사용자 지정 instructions 미리보기: {custom_instructions[:200]}...")
            logger.info(f"[세션 생성] final_instructions 길이: {len(final_instructions)} 문자")
        else:
            # 사용자 지정 instructions가 없으면 시험 컨텍스트만 사용
            final_instructions = exam_context
            print(f"[세션 생성] ⚠️ 기본 exam_context 사용 (사용자 지정 instructions 없음): {len(exam_context)} 문자")
            logger.info(f"[세션 생성] 기본 exam_context 사용: {len(exam_context)} 문자")
            logger.info(f"[세션 생성] exam_context 미리보기 (처음 500자): {exam_context[:500]}...")
        
        # Realtime 세션 생성
        try:
            session = client.beta.realtime.sessions.create(
                model=settings.OPENAI_MODEL,
                voice=voice,
                instructions=final_instructions,  # 사용자 지정 instructions 포함
                modalities=["audio", "text"],  # 오디오와 텍스트 모두 활성화
                input_audio_format="pcm16",
                output_audio_format="pcm16",
                input_audio_transcription={
                    "model": "whisper-1"
                },
                turn_detection={
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500
                },
                tools=[
                    {
                        "type": "function",
                        "name": "get_current_question",
                        "description": "현재 문제 정보를 가져옵니다.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "question_index": {
                                    "type": "integer",
                                    "description": "문제 인덱스 (0부터 시작)"
                                }
                            }
                        }
                    },
                    {
                        "type": "function",
                        "name": "submit_answer",
                        "description": "답안을 제출합니다.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "question_id": {
                                    "type": "string",
                                    "description": "문제 ID"
                                },
                                "answer": {
                                    "type": "string",
                                    "description": "답안"
                                }
                            },
                            "required": ["question_id", "answer"]
                        }
                    },
                    {
                        "type": "function",
                        "name": "get_question_hint",
                        "description": "문제에 대한 힌트를 제공합니다.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "question_id": {
                                    "type": "string",
                                    "description": "문제 ID"
                                }
                            },
                            "required": ["question_id"]
                        }
                    }
                ]
            )
            logger.info(f"OpenAI 세션 생성 성공: {session.id}")
        except Exception as e:
            logger.error(f"OpenAI 세션 생성 실패: {e}", exc_info=True)
            raise
        
        # client_secret 추출 (OpenAI Realtime API에서 제공하는 임시 토큰)
        # OpenAI Realtime API는 client_secret을 제공하여 모바일 앱이 직접 연결할 수 있게 함
        logger.info(f"세션 객체 타입: {type(session)}")
        logger.info(f"세션 객체 속성: {[attr for attr in dir(session) if not attr.startswith('_')]}")
        
        # 다양한 방법으로 client_secret 추출 시도
        client_secret = None
        client_secret_obj = None
        
        # 방법 1: 직접 속성 접근
        if hasattr(session, 'client_secret'):
            client_secret_obj = session.client_secret
            logger.info(f"client_secret 발견 (속성 접근): {bool(client_secret_obj)}, 타입: {type(client_secret_obj)}")
        
        # 방법 2: token 속성 확인
        if not client_secret_obj and hasattr(session, 'token'):
            client_secret_obj = session.token
            logger.info(f"token 발견 (속성 접근): {bool(client_secret_obj)}, 타입: {type(client_secret_obj)}")
        
        # 방법 3: model_dump() 사용 (Pydantic 모델인 경우)
        if not client_secret_obj:
            try:
                if hasattr(session, 'model_dump'):
                    session_dict = session.model_dump()
                    logger.info(f"model_dump() 성공, 키: {list(session_dict.keys())[:10]}")
                    client_secret_obj = session_dict.get('client_secret') or session_dict.get('token')
                elif hasattr(session, 'dict'):
                    session_dict = session.dict()
                    logger.info(f"dict() 성공, 키: {list(session_dict.keys())[:10]}")
                    client_secret_obj = session_dict.get('client_secret') or session_dict.get('token')
            except Exception as e:
                logger.warning(f"세션 객체 변환 실패: {e}")
        
        # 방법 4: getattr 사용
        if not client_secret_obj:
            client_secret_obj = getattr(session, 'client_secret', None) or getattr(session, 'token', None)
        
        # ClientSecret 객체에서 실제 문자열 값 추출
        if client_secret_obj:
            # ClientSecret 객체인 경우 value 속성 추출
            if hasattr(client_secret_obj, 'value'):
                client_secret = client_secret_obj.value
                logger.info(f"ClientSecret.value 추출 성공: {bool(client_secret)}")
            # 이미 문자열인 경우
            elif isinstance(client_secret_obj, str):
                client_secret = client_secret_obj
                logger.info(f"client_secret이 이미 문자열입니다.")
            # bytes인 경우
            elif isinstance(client_secret_obj, bytes):
                client_secret = client_secret_obj.decode('utf-8')
                logger.info(f"client_secret을 bytes에서 문자열로 변환했습니다.")
            # 다른 타입인 경우 문자열로 변환 시도
            else:
                try:
                    # ClientSecret 객체의 문자열 표현에서 값 추출 시도
                    client_secret_str = str(client_secret_obj)
                    # 만약 객체의 repr이 특정 패턴을 가지고 있다면 파싱
                    if 'value' in client_secret_str.lower():
                        # 간단한 파싱 시도 (실제 구현은 객체 구조에 따라 다를 수 있음)
                        import re
                        match = re.search(r"value[=:]\s*['\"]([^'\"]+)['\"]", client_secret_str)
                        if match:
                            client_secret = match.group(1)
                        else:
                            client_secret = client_secret_str
                    else:
                        client_secret = client_secret_str
                    logger.info(f"client_secret을 문자열로 변환했습니다: {type(client_secret_obj)} -> str")
                except Exception as e:
                    logger.error(f"client_secret 변환 실패: {e}")
                    client_secret = None
        
        if not client_secret:
            logger.error(f"client_secret을 찾을 수 없습니다. 세션 ID: {session.id}")
            logger.error(f"client_secret_obj 타입: {type(client_secret_obj)}")
            logger.error(f"client_secret_obj 값: {repr(client_secret_obj)[:500]}")
            return Response({
                'error': 'client_secret을 가져올 수 없습니다. OpenAI API 응답을 확인하세요.',
                'session_id': session.id
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # 세션 정보를 캐시에 저장
        session_key = f"realtime_session_{session.id}"
        cache.set(session_key, {
            'session_id': session.id,
            'user_id': user.id,
            'exam_id': exam_id,
            'voice': voice,
            'language': language,
            'client_secret': client_secret,  # 임시 토큰 저장
            'created_at': session.created_at.isoformat() if hasattr(session, 'created_at') else None
        }, timeout=3600)  # 1시간 후 만료
        
        logger.info(f"Realtime 세션 생성 완료: {session.id} (사용자: {user.id}, 시험: {exam_id}, client_secret 존재: {bool(client_secret)})")
        
        websocket_url = _get_websocket_url(session.id, client_secret)
        
        return Response({
            'session_id': session.id,
            'client_secret': client_secret,  # 모바일 앱에 전달 (API 키 아님!)
            'voice': voice,
            'language': language,
            'exam_title': (
                exam.title_ko if language == LANGUAGE_KO else
                (getattr(exam, 'title_es', None) or '') if language == LANGUAGE_ES else
                (getattr(exam, 'title_zh', None) or '') if language == LANGUAGE_ZH else
                exam.title_en
            ) if hasattr(exam, 'title_ko') else '',
            'websocket_url': websocket_url  # WebSocket URL 생성
        })
        
    except ValueError as e:
        logger.error(f"OpenAI API 키 오류: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"Realtime 세션 생성 실패: {e}", exc_info=True)
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return Response({
            'error': '세션 생성 중 오류가 발생했습니다.',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([])  # 임시로 인증 없이 접근 가능하도록 변경 (테스트용)
def get_mandatory_rules_api(request):
    """필수 프롬프트 YAML 내용을 반환합니다."""
    try:
        from quiz.utils.multilingual_utils import BASE_LANGUAGE
        language = request.GET.get('language', BASE_LANGUAGE)
        rules = get_mandatory_rules(language)
        
        # 로그: 받은 데이터 확인
        logger.info(f"[필수 프롬프트 API] language: {language}")
        logger.info(f"[필수 프롬프트 API] rules keys: {list(rules.keys()) if rules else 'None'}")
        logger.info(f"[필수 프롬프트 API] language_instruction 길이: {len(rules.get('language_instruction', '')) if rules else 0}")
        logger.info(f"[필수 프롬프트 API] mandatory_prompts 길이: {len(rules.get('mandatory_prompts', '')) if rules else 0}")
        
        response_data = {
            'language': language,
            'language_instruction': rules.get('language_instruction', '') if rules else '',
            'mandatory_prompts': rules.get('mandatory_prompts', '') if rules else ''
        }
        
        logger.info(f"[필수 프롬프트 API] 응답 데이터 keys: {list(response_data.keys())}")
        logger.info(f"[필수 프롬프트 API] 응답 데이터 language_instruction 길이: {len(response_data['language_instruction'])}")
        logger.info(f"[필수 프롬프트 API] 응답 데이터 mandatory_prompts 길이: {len(response_data['mandatory_prompts'])}")
        
        return Response(response_data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"필수 프롬프트 조회 실패: {e}", exc_info=True)
        return Response({
            'error': '필수 프롬프트를 불러올 수 없습니다.',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([])  # 임시로 인증 없이 접근 가능하도록 변경 (테스트용)
def get_interview_prompt_template_api(request):
    """인터뷰 프롬프트 템플릿 YAML 내용을 반환합니다."""
    try:
        from quiz.utils.multilingual_utils import BASE_LANGUAGE
        language = request.GET.get('language', BASE_LANGUAGE)
        templates = load_interview_prompt_template()
        
        # zh, es, ko, en, ja 언어 지원
        from quiz.utils.multilingual_utils import LANGUAGE_KO, LANGUAGE_ZH, LANGUAGE_ES, LANGUAGE_EN, LANGUAGE_JA
        if language == LANGUAGE_KO:
            lang_key = LANGUAGE_KO
        elif language == LANGUAGE_ZH:
            lang_key = LANGUAGE_ZH
        elif language == LANGUAGE_ES:
            lang_key = LANGUAGE_ES
        elif language == LANGUAGE_JA:
            lang_key = LANGUAGE_JA
        else:
            lang_key = LANGUAGE_EN
        template_data = templates.get(lang_key, {})
        
        response_data = {
            'language': language,
            'base_template': template_data.get('base_template', ''),
            'question_restriction': template_data.get('question_restriction', ''),
            'mandatory_rules_marker': template_data.get('mandatory_rules_marker', '')
        }
        
        logger.info(f"[인터뷰 프롬프트 템플릿 API] language: {language}, keys: {list(response_data.keys())}")
        
        return Response(response_data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"인터뷰 프롬프트 템플릿 조회 실패: {e}", exc_info=True)
        return Response({
            'error': '인터뷰 프롬프트 템플릿을 불러올 수 없습니다.',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_session_info(request, session_id):
    """Realtime 세션 정보를 조회합니다."""
    try:
        session_key = f"realtime_session_{session_id}"
        session_data = cache.get(session_key)
        
        if not session_data:
            return Response({'error': '세션을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        # 사용자 권한 확인
        if session_data['user_id'] != request.user.id:
            return Response({'error': '세션에 접근할 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
        
        # WebSocket URL 추가
        client_secret = session_data.get('client_secret')
        session_data['websocket_url'] = _get_websocket_url(session_id, client_secret)
        
        return Response(session_data)
        
    except Exception as e:
        logger.error(f"세션 정보 조회 실패: {e}")
        return Response({'error': '세션 정보 조회 중 오류가 발생했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_websocket_url(request, session_id):
    """WebSocket 연결 URL을 반환합니다."""
    try:
        session_key = f"realtime_session_{session_id}"
        session_data = cache.get(session_key)
        
        if not session_data:
            return Response({'error': '세션을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        # 사용자 권한 확인
        if session_data['user_id'] != request.user.id:
            return Response({'error': '세션에 접근할 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
        
        client_secret = session_data.get('client_secret')
        websocket_url = _get_websocket_url(session_id, client_secret)
        
        if not websocket_url:
            return Response({'error': 'WebSocket URL을 생성할 수 없습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'websocket_url': websocket_url,
            'client_secret': client_secret,
            'session_id': session_id
        })
        
    except Exception as e:
        logger.error(f"WebSocket URL 조회 실패: {e}")
        return Response({'error': 'WebSocket URL 조회 중 오류가 발생했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_realtime_session(request, session_id):
    """Realtime 세션을 삭제합니다."""
    try:
        session_key = f"realtime_session_{session_id}"
        session_data = cache.get(session_key)
        
        if not session_data:
            return Response({'error': '세션을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        # 사용자 권한 확인
        if session_data['user_id'] != request.user.id:
            return Response({'error': '세션에 접근할 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
        
        # OpenAI 세션 종료
        try:
            client = get_openai_client()
            client.beta.realtime.sessions.delete(session_id)
        except Exception as e:
            logger.warning(f"OpenAI 세션 종료 실패: {e}")
        
        # 캐시에서 세션 정보 삭제
        cache.delete(session_key)
        
        logger.info(f"Realtime 세션 삭제 완료: {session_id}")
        
        return Response({'success': True}, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"세션 삭제 실패: {e}")
        return Response({'error': '세션 삭제 중 오류가 발생했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handle_realtime_function_call(request):
    """Realtime API의 함수 호출을 처리합니다."""
    try:
        session_id = request.data.get('session_id')
        function_name = request.data.get('function_name')
        parameters = request.data.get('parameters', {})
        
        if not session_id or not function_name:
            return Response({'error': 'session_id와 function_name이 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 세션 정보 확인
        session_key = f"realtime_session_{session_id}"
        session_data = cache.get(session_key)
        
        if not session_data or session_data['user_id'] != request.user.id:
            return Response({'error': '유효하지 않은 세션입니다.'}, status=status.HTTP_403_FORBIDDEN)
        
        # 함수별 처리
        if function_name == 'get_current_question':
            return _handle_get_current_question(session_data, parameters)
        elif function_name == 'submit_answer':
            return _handle_submit_answer(session_data, parameters)
        elif function_name == 'get_question_hint':
            return _handle_get_question_hint(session_data, parameters)
        else:
            return Response({'error': f'알 수 없는 함수: {function_name}'}, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"함수 호출 처리 실패: {e}")
        return Response({'error': '함수 호출 처리 중 오류가 발생했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def _has_exam_access(user, exam):
    """사용자가 시험에 접근할 권한이 있는지 확인합니다."""
    # admin_role 사용자는 모든 시험에 접근 가능
    if hasattr(user, 'profile') and hasattr(user.profile, 'role') and user.profile.role == 'admin_role':
        return True
    
    # 시험이 공개되어 있으면 접근 가능
    if exam.is_public:
        return True
    
    # 사용자가 시험 생성자인지 확인
    if exam.created_by == user:
        return True
    
    # 사용자가 시험을 이미 풀어본 적이 있는지 확인
    from ..models import ExamResult
    return ExamResult.objects.filter(user=user, exam=exam).exists()

def _get_websocket_url(session_id, client_secret, use_proxy=True):
    """WebSocket 연결 URL을 생성합니다.
    
    Args:
        session_id: OpenAI Realtime API 세션 ID
        client_secret: OpenAI Realtime API client_secret
        use_proxy: 서버 프록시 사용 여부 (기본값: True)
                   True: ws://localhost:8000/ws/realtime/{session_id}/ (서버 프록시 사용)
                   False: wss://api.openai.com/v1/realtime?... (직접 연결, 헤더 설정 불가로 실패)
    """
    if not client_secret:
        logger.error("client_secret이 None입니다.")
        return None
    
    # 서버 프록시 사용 (모바일과 웹 모두 브라우저 WebSocket API 사용하므로 헤더 설정 불가)
    if use_proxy:
        # Django Channels WebSocket 프록시 URL
        # 프로토콜은 ws:// (로컬) 또는 wss:// (프로덕션)로 자동 결정
        from django.conf import settings
        if settings.DEBUG:
            # 개발 환경: ws://
            base_url = "ws://localhost:8000"
        else:
            # 프로덕션 환경: wss://
            current_domain = getattr(settings, 'CURRENT_DOMAIN', '')
            if current_domain:
                base_url = f"wss://{current_domain}"
            else:
                base_url = "wss://api.drillquiz.com"  # 기본값
        
        websocket_url = f"{base_url}/ws/realtime/{session_id}/"
        logger.info(f"서버 프록시 WebSocket URL 생성: {websocket_url}")
        return websocket_url
    
    # 직접 연결 (사용하지 않음 - 헤더 설정 불가로 실패)
    # OpenAI Realtime API WebSocket URL
    from urllib.parse import quote
    
    # client_secret이 bytes인 경우 문자열로 변환
    if isinstance(client_secret, bytes):
        client_secret = client_secret.decode('utf-8')
    elif not isinstance(client_secret, str):
        client_secret = str(client_secret)
    
    encoded_secret = quote(client_secret, safe='-_')
    websocket_url = f"wss://api.openai.com/v1/realtime?session_id={session_id}&client_secret={encoded_secret}&model={settings.OPENAI_MODEL}"
    
    # URL에 client_secret이 포함되어 있는지 확인
    if 'client_secret=' not in websocket_url:
        logger.error(f"❌ WebSocket URL에 client_secret이 포함되지 않음: {websocket_url[:100]}...")
    else:
        logger.info(f"✅ WebSocket URL 생성 완료: 길이={len(websocket_url)}, client_secret 포함={True}")
        # URL 파싱하여 검증
        try:
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(websocket_url)
            params = parse_qs(parsed.query)
            if 'client_secret' in params:
                logger.info(f"✅ URL 파싱 검증: client_secret 파라미터 존재, 길이={len(params['client_secret'][0])}")
            else:
                logger.error(f"❌ URL 파싱 검증 실패: client_secret 파라미터 없음")
        except Exception as e:
            logger.error(f"❌ URL 파싱 오류: {e}")
    
    return websocket_url

def load_evaluation_guideline_template():
    """ai/prompts/evaluation_guideline_template.yaml 파일을 로드합니다."""
    global _evaluation_guideline_template_cache
    if _evaluation_guideline_template_cache is not None:
        return _evaluation_guideline_template_cache
    
    try:
        base_dir = settings.BASE_DIR
        yaml_path = os.path.join(base_dir, 'ai', 'prompts', 'evaluation_guideline_template.yaml')
        
        if not os.path.exists(yaml_path):
            logger.warning(f"⚠️ 평가 가이드라인 템플릿 YAML 파일을 찾을 수 없습니다: {yaml_path}")
            from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
            _evaluation_guideline_template_cache = {lang: {'lenient': '', 'moderate': '', 'strict': ''} for lang in SUPPORTED_LANGUAGES}
            return _evaluation_guideline_template_cache
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            templates = yaml.safe_load(f)
        
        from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
        default_templates = {lang: {'lenient': '', 'moderate': '', 'strict': ''} for lang in SUPPORTED_LANGUAGES}
        _evaluation_guideline_template_cache = templates or default_templates
        logger.info(f"✅ 평가 가이드라인 템플릿 YAML 파일 로드 성공: {yaml_path}")
        return _evaluation_guideline_template_cache
    except Exception as e:
        logger.error(f"❌ 평가 가이드라인 템플릿 YAML 파일 로드 실패: {e}", exc_info=True)
        from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
        _evaluation_guideline_template_cache = {lang: {'lenient': '', 'moderate': '', 'strict': ''} for lang in SUPPORTED_LANGUAGES}
        return _evaluation_guideline_template_cache

def _get_evaluation_guideline(exam_difficulty, language):
    """
    시험 난이도에 따른 평가 가이드라인을 생성합니다.
    
    Args:
        exam_difficulty: 시험 난이도 (1~10)
        language: 언어 코드
    
    Returns:
        str: 평가 가이드라인 텍스트
    """
    from quiz.utils.multilingual_utils import BASE_LANGUAGE
    
    # 난이도 기본값 설정
    exam_difficulty = max(1, min(10, int(exam_difficulty) if exam_difficulty else 5))
    
    # YAML 파일에서 가이드라인 로드
    templates = load_evaluation_guideline_template()
    
    # 언어별 가이드라인 가져오기 (언어가 지원되지 않으면 BASE_LANGUAGE 사용)
    lang_key = language if language in templates else BASE_LANGUAGE
    lang_guidelines = templates.get(lang_key, {}) or templates.get(BASE_LANGUAGE, {})
    
    # 난이도에 따라 가이드라인 선택
    if exam_difficulty <= 3:
        guideline = lang_guidelines.get('lenient', '')
    elif exam_difficulty <= 6:
        guideline = lang_guidelines.get('moderate', '')
    else:  # 7-10
        guideline = lang_guidelines.get('strict', '')
    
    # 가이드라인이 없으면 기본값 반환
    if not guideline:
        logger.warning(f"⚠️ 평가 가이드라인을 찾을 수 없습니다. language={lang_key}, exam_difficulty={exam_difficulty}")
        return ""
    
    return guideline


def _create_exam_context(exam, language):
    """시험 컨텍스트를 생성합니다."""
    from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES, BASE_LANGUAGE
    
    # 언어가 지원되지 않으면 BASE_LANGUAGE 사용
    if language not in SUPPORTED_LANGUAGES:
        language = BASE_LANGUAGE
    
    # 동적으로 필드 가져오기
    title = getattr(exam, f'title_{language}', None) or getattr(exam, f'title_{BASE_LANGUAGE}', None) or ''
    description = getattr(exam, f'description_{language}', None) or getattr(exam, f'description_{BASE_LANGUAGE}', None) or ''
    
    # 시험 난이도 가져오기 (기본값 5)
    exam_difficulty = getattr(exam, 'exam_difficulty', 5) or 5
    
    # 시험의 문제 목록 가져오기
    questions = exam.questions.all().order_by('id')
    questions_text = ""
    for idx, question in enumerate(questions, 1):
        # 동적으로 제목 가져오기
        q_title = getattr(question, f'title_{language}', None) or getattr(question, f'title_{BASE_LANGUAGE}', None) or ''
        
        # 동적으로 답변 가져오기
        q_answer = getattr(question, f'answer_{language}', None) or getattr(question, f'answer_{BASE_LANGUAGE}', None) or getattr(question, 'answer', '')
        
        questions_text += f"\n{idx}. {q_title}\n   답변: {q_answer}\n"
    
    # 난이도에 따른 평가 가이드라인 생성
    evaluation_guideline = _get_evaluation_guideline(exam_difficulty, language)
    
    # YAML 파일에서 템플릿 로드
    templates = load_exam_context_template()
    # 언어가 지원되지 않으면 BASE_LANGUAGE 사용
    lang_key = language if language in templates else BASE_LANGUAGE
    template = templates.get(lang_key, {}).get('template', '') or templates.get(BASE_LANGUAGE, {}).get('template', '')
    
    # YAML 파일이 없으면 에러 발생
    if not template:
        error_msg = f"프롬프트 YAML 파일을 로드할 수 없습니다. ai/prompts/exam_context_template.yaml 파일의 '{lang_key}' 템플릿을 확인해주세요."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # 템플릿에 변수 치환
    context = template.format(
        title=title,
        description=description,
        question_count=questions.count(),
        questions_text=questions_text,
        exam_difficulty=exam_difficulty,
        evaluation_guideline=evaluation_guideline
    )
    
    return context

def _handle_get_current_question(session_data, parameters):
    """현재 문제 정보를 반환합니다."""
    try:
        exam_id = session_data['exam_id']
        question_index = parameters.get('question_index', 0)
        language = session_data['language']
        
        exam = Exam.objects.get(id=exam_id)
        questions = exam.questions.all().order_by('id')
        
        if question_index >= questions.count():
            return Response({'error': '문제 인덱스가 범위를 벗어났습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        question = questions[question_index]
        
        # 동적으로 필드 가져오기
        from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES, BASE_LANGUAGE
        
        # 언어가 지원되지 않으면 BASE_LANGUAGE 사용
        if language not in SUPPORTED_LANGUAGES:
            language = BASE_LANGUAGE
        
        # 동적으로 제목과 내용 가져오기
        title = getattr(question, f'title_{language}', None) or getattr(question, f'title_{BASE_LANGUAGE}', None) or ''
        content = getattr(question, f'content_{language}', None) or getattr(question, f'content_{BASE_LANGUAGE}', None) or ''
        
        question_data = {
            'id': str(question.id),
            'index': question_index,
            'title': title,
            'content': content,
            'difficulty': question.difficulty,
            'total_questions': questions.count()
        }
        
        return Response(question_data)
        
    except Exception as e:
        logger.error(f"현재 문제 조회 실패: {e}")
        return Response({'error': '문제 조회 중 오류가 발생했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def _handle_submit_answer(session_data, parameters):
    """답안을 제출합니다."""
    try:
        question_id = parameters.get('question_id')
        answer = parameters.get('answer')
        
        if not question_id or not answer:
            return Response({'error': 'question_id와 answer가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 여기서는 실제 답안 저장 로직을 구현하지 않고, 
        # 음성 인터페이스에서는 텍스트 입력으로 전환하도록 안내
        return Response({
            'message': '답안이 음성으로 제출되었습니다. 정확한 답안을 위해 텍스트 입력을 사용해주세요.',
            'question_id': question_id,
            'answer': answer
        })
        
    except Exception as e:
        logger.error(f"답안 제출 실패: {e}")
        return Response({'error': '답안 제출 중 오류가 발생했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def _handle_get_question_hint(session_data, parameters):
    """문제 힌트를 제공합니다."""
    try:
        question_id = parameters.get('question_id')
        language = session_data['language']
        
        if not question_id:
            return Response({'error': 'question_id가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        question = Question.objects.get(id=question_id)
        
        # 간단한 힌트 생성 (실제로는 더 정교한 힌트 로직 구현)
        hint = f"이 문제는 {question.difficulty} 난이도입니다. 문제를 차근차근 읽어보고 단계별로 접근해보세요."
        
        return Response({
            'hint': hint,
            'question_id': question_id
        })
        
    except Question.DoesNotExist:
        return Response({'error': '문제를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"힌트 제공 실패: {e}")
        return Response({'error': '힌트 제공 중 오류가 발생했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handle_webrtc_offer(request, session_id):
    """WebRTC Offer를 처리합니다."""
    try:
        offer = request.data.get('offer')
        if not offer:
            return Response({'error': 'offer가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 세션 정보 확인
        session_key = f"realtime_session_{session_id}"
        session_data = cache.get(session_key)
        
        if not session_data or session_data['user_id'] != request.user.id:
            return Response({'error': '유효하지 않은 세션입니다.'}, status=status.HTTP_403_FORBIDDEN)

        # TODO: 실제 OpenAI Realtime API WebRTC 연결 구현
        # 현재는 placeholder로 응답을 반환합니다.
        
        logger.info(f"WebRTC Offer 처리: session_id={session_id}, user={request.user.id}")
        
        # 임시 응답 (실제로는 OpenAI에서 받은 answer를 반환해야 함)
        answer = {
            'type': 'answer',
            'sdp': 'placeholder_sdp_answer'
        }
        
        return Response({'answer': answer})
        
    except Exception as e:
        logger.error(f"WebRTC Offer 처리 중 오류 발생: {e}", exc_info=True)
        return Response({'error': 'WebRTC Offer 처리에 실패했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handle_ice_candidate(request, session_id):
    """ICE Candidate를 처리합니다."""
    try:
        candidate = request.data.get('candidate')
        if not candidate:
            return Response({'error': 'candidate가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 세션 정보 확인
        session_key = f"realtime_session_{session_id}"
        session_data = cache.get(session_key)
        
        if not session_data or session_data['user_id'] != request.user.id:
            return Response({'error': '유효하지 않은 세션입니다.'}, status=status.HTTP_403_FORBIDDEN)

        # TODO: OpenAI Realtime API에 ICE candidate 전송
        logger.info(f"ICE Candidate 처리: session_id={session_id}, user={request.user.id}")
        
        return Response({'message': 'ICE candidate processed'})
        
    except Exception as e:
        logger.error(f"ICE Candidate 처리 중 오류 발생: {e}", exc_info=True)
        return Response({'error': 'ICE Candidate 처리에 실패했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_speech(request, session_id):
    """음성 출력을 요청합니다."""
    try:
        text = request.data.get('text')
        voice = request.data.get('voice', 'alloy')
        from quiz.utils.multilingual_utils import BASE_LANGUAGE
        language = request.data.get('language', BASE_LANGUAGE)

        if not text:
            return Response({'error': 'text가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 세션 정보 확인
        session_key = f"realtime_session_{session_id}"
        session_data = cache.get(session_key)
        
        if not session_data or session_data['user_id'] != request.user.id:
            return Response({'error': '유효하지 않은 세션입니다.'}, status=status.HTTP_403_FORBIDDEN)

        # TODO: OpenAI Realtime API에 음성 출력 요청
        # 실제 구현에서는 OpenAI Realtime API의 음성 출력 기능을 사용해야 합니다.
        
        logger.info(f"음성 출력 요청: session_id={session_id}, text={text[:50]}..., user={request.user.id}")
        
        # 임시 응답 (실제로는 OpenAI Realtime API를 통해 음성이 출력되어야 함)
        return Response({'message': 'Speech request processed'})
        
    except Exception as e:
        logger.error(f"음성 출력 요청 처리 중 오류 발생: {e}", exc_info=True)
        return Response({'error': '음성 출력 요청 처리에 실패했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stop_speech(request, session_id):
    """음성 출력을 중지합니다."""
    try:
        # 세션 정보 확인
        session_key = f"realtime_session_{session_id}"
        session_data = cache.get(session_key)
        
        if not session_data or session_data['user_id'] != request.user.id:
            return Response({'error': '유효하지 않은 세션입니다.'}, status=status.HTTP_403_FORBIDDEN)

        # TODO: OpenAI Realtime API에 음성 출력 중지 요청
        logger.info(f"음성 출력 중지 요청: session_id={session_id}, user={request.user.id}")
        
        return Response({'message': 'Speech stopped'})
        
    except Exception as e:
        logger.error(f"음성 출력 중지 요청 처리 중 오류 발생: {e}", exc_info=True)
        return Response({'error': '음성 출력 중지 요청 처리에 실패했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@authentication_classes([JWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def chat_interview(request):
    """Chat Completions API를 사용한 인터뷰 응답 생성 (TTS/STT 조합용)"""
    logger.info("=" * 80)
    logger.info("🔵 [chat_interview] API 요청 수신!")
    logger.info(f"🔵 [chat_interview] 요청 사용자: {request.user.id}")
    try:
        exam_id = request.data.get('exam_id')
        user_message = request.data.get('message', '')
        conversation_history = request.data.get('conversation_history', [])
        from quiz.utils.multilingual_utils import BASE_LANGUAGE
        language = request.data.get('language', BASE_LANGUAGE)
        instructions = request.data.get('instructions', '')
        
        logger.info(f"🔵 [chat_interview] 요청 데이터: exam_id={exam_id}, "
                   f"user_message_length={len(user_message) if user_message else 0}, "
                   f"conversation_history_count={len(conversation_history)}, "
                   f"language={language}, "
                   f"instructions_length={len(instructions) if instructions else 0}")
        
        if not exam_id:
            return Response({'error': 'exam_id가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 빈 메시지는 초기 인사말 요청으로 간주
        is_initial_greeting = not user_message or not user_message.strip()
        
        # 시험 존재 확인
        try:
            exam = Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            return Response({'error': '시험을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        # 시험 접근 권한 확인
        user = request.user
        if not _has_exam_access(user, exam):
            return Response({'error': '이 시험에 접근할 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
        
        # OpenAI 클라이언트 생성
        client = get_openai_client()
        
        # 시험 컨텍스트 생성
        exam_context = _create_exam_context(exam, language)
        
        # 필수 프롬프트 로드
        mandatory_rules = get_mandatory_rules(language)
        language_instruction = mandatory_rules.get('language_instruction', '')
        mandatory_prompts_text = mandatory_rules.get('mandatory_prompts', '')
        
        # Instructions 전달 확인 로그
        logger.info(f"Chat 인터뷰 Instructions 확인: exam_id={exam_id}, user={user.id}, "
                   f"instructions_length={len(instructions) if instructions else 0}, "
                   f"instructions_preview={instructions[:200] if instructions else '(없음)'}")
        
        # 시스템 프롬프트 구성 (언어별 중요 지침)
        important_instructions = {
            'ko': '중요: 사용자가 말하는 동안은 절대 응답하지 마세요. 사용자가 완전히 말을 끝낸 후에만 응답하세요.',
            'en': 'Important: Do not respond while the user is speaking. Only respond after the user has completely finished speaking.',
            'es': 'Importante: No responda mientras el usuario está hablando. Solo responda después de que el usuario haya terminado de hablar completamente.',
            'zh': '重要：在用户说话时不要回应。只有在用户完全说完后才回应。',
            'ja': '重要：ユーザーが話している間は絶対に応答しないでください。ユーザーが完全に話し終わった後にのみ応答してください。'
        }
        important_instruction = important_instructions.get(language, important_instructions['en'])
        
        system_prompt = f"""{exam_context}

{language_instruction}

{mandatory_prompts_text}

{instructions if instructions else ''}

{important_instruction}"""
        
        # 시스템 프롬프트 길이 로그
        logger.info(f"시스템 프롬프트 구성 완료: exam_context_length={len(exam_context)}, "
                   f"language_instruction_length={len(language_instruction)}, "
                   f"mandatory_prompts_length={len(mandatory_prompts_text)}, "
                   f"instructions_length={len(instructions) if instructions else 0}, "
                   f"total_system_prompt_length={len(system_prompt)}")
        
        # 대화 히스토리 구성
        messages = [
            {'role': 'system', 'content': system_prompt}
        ]
        
        # 기존 대화 히스토리 추가
        for msg in conversation_history:
            if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
        
        # 현재 사용자 메시지 추가 (빈 메시지인 경우 초기 인사말 요청)
        if is_initial_greeting:
            # 초기 인사말 요청 - 첫 번째 질문을 바로 시작 (언어별 메시지)
            initial_messages = {
                'ko': '첫 번째 질문을 바로 시작해주세요. 인사말이나 역할 소개 없이 질문만 제시해주세요.',
                'en': 'Please start with the first question immediately. Present only the question without greetings or role introductions.',
                'es': 'Por favor, comience con la primera pregunta de inmediato. Presente solo la pregunta sin saludos o introducciones de rol.',
                'zh': '请立即开始第一个问题。只提出问题，不要问候或角色介绍。',
                'ja': '最初の質問をすぐに始めてください。挨拶や役割の紹介なしで、質問だけを提示してください。'
            }
            initial_message = initial_messages.get(language, initial_messages['en'])
            messages.append({
                'role': 'user',
                'content': initial_message
            })
        else:
            messages.append({
                'role': 'user',
                'content': user_message
            })
        
        # Chat Completions API 호출 (OpenAI 먼저 시도)
        ai_response = None
        model_used = None
        usage_info = None
        
        # 메시지 길이 검증 및 로깅
        total_message_length = sum(len(str(msg.get('content', ''))) for msg in messages)
        logger.info(f"🔵 [chat_interview] 메시지 길이 검증: total_messages={len(messages)}, "
                   f"total_content_length={total_message_length}, "
                   f"system_prompt_length={len(system_prompt)}, "
                   f"conversation_history_count={len(conversation_history)}")
        
        # 메시지가 너무 긴 경우 경고 (OpenAI 모델별 토큰 제한 고려)
        # gpt-4o-mini의 경우 약 128K 토큰 제한, 대략 500K 문자 정도
        if total_message_length > 400000:  # 약 80% 제한
            logger.warning(f"⚠️ [chat_interview] 메시지가 매우 깁니다: {total_message_length} 문자. "
                          f"토큰 제한 초과 가능성이 있습니다.")
        
        # OpenAI 사용 가능 여부 확인 (캐시 체크)
        from quiz.utils.multilingual_utils import check_openai_availability, mark_openai_unavailable
        is_openai_unavailable = not check_openai_availability()
        
        # OpenAI가 사용 불가능하면 바로 Gemini로 전환
        if is_openai_unavailable:
            logger.info("[chat_interview] OpenAI가 캐시에서 사용 불가능 상태로 확인됨, Gemini로 바로 전환...")
            ai_response = None
            openai_error = "OpenAI가 캐시에서 사용 불가능 상태"
        else:
            # OpenAI 시도
            ai_response = None
            openai_error = None
        
        if not is_openai_unavailable:
            try:
                if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
                    logger.info("OpenAI API를 사용하여 인터뷰 응답 생성 시도...")
                    response = client.chat.completions.create(
                        model=getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini'),
                        messages=messages,
                        temperature=0.7,
                        max_tokens=1000
                    )
                    
                    ai_response = response.choices[0].message.content.strip()
                    model_used = response.model
                    usage_info = {
                        'prompt_tokens': response.usage.prompt_tokens,
                        'completion_tokens': response.usage.completion_tokens,
                        'total_tokens': response.usage.total_tokens
                    }
                    
                    logger.info(f"Chat 인터뷰 응답 생성 성공 (OpenAI): exam_id={exam_id}, user={user.id}, response_length={len(ai_response)}")
                else:
                    openai_error = "OpenAI API 키가 설정되지 않았습니다."
                    logger.warning(f"[chat_interview] OpenAI API 키 없음: {openai_error}")
                    mark_openai_unavailable()
            except Exception as e:
                # OpenAI 실패 시 캐시에 마킹
                openai_error = str(e)
                
                # OpenAI quota 초과 에러 로깅 및 즉시 캐시 마킹
                is_rate_limit = False
                if isinstance(e, openai.RateLimitError):
                    logger.error(f"[chat_interview] OpenAI API 할당량 초과 (RateLimitError): {e}, 즉시 캐시에 마킹하고 Gemini로 전환...")
                    is_rate_limit = True
                elif hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                    if e.response.status_code == 429:
                        logger.error(f"[chat_interview] OpenAI API 할당량 초과 (HTTP 429): {e}, 즉시 캐시에 마킹하고 Gemini로 전환...")
                        is_rate_limit = True
                    else:
                        logger.warning(f"[chat_interview] OpenAI API 호출 실패 (상태코드: {e.response.status_code}): {e}, 캐시에 마킹하고 Gemini로 전환...")
                elif hasattr(e, 'status_code') and e.status_code == 429:
                    logger.error(f"[chat_interview] OpenAI API 할당량 초과 (status_code 429): {e}, 즉시 캐시에 마킹하고 Gemini로 전환...")
                    is_rate_limit = True
                elif '429' in str(e) or 'insufficient_quota' in str(e):
                    logger.error(f"[chat_interview] OpenAI API 할당량 초과 (에러 메시지): {e}, 즉시 캐시에 마킹하고 Gemini로 전환...")
                    is_rate_limit = True
                else:
                    logger.warning(f"[chat_interview] OpenAI API 호출 실패: {e}, 캐시에 마킹하고 Gemini로 전환...")
                
                # 모든 에러에 대해 캐시 마킹 (429는 즉시, 다른 에러도 재시도 방지)
                mark_openai_unavailable()
        
        # OpenAI 실패했거나 사용 불가능한 경우 Gemini로 fallback
        if ai_response is None:
            
            # Gemini 시도
            try:
                if GEMINI_AVAILABLE and hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY:
                    logger.info("Gemini API를 사용하여 인터뷰 응답 생성 시도...")
                    genai_client = get_gemini_client()
                    model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-pro')
                    
                    # 모델 생성 시도 (여러 모델 이름 시도)
                    model = None
                    model_names_to_try = [
                        model_name,
                        'gemini-2.5-flash',
                        'gemini-pro',
                        'gemini-1.5-pro',
                        'gemini-1.5-pro-latest',
                        'models/gemini-pro',
                    ]
                    
                    for name in model_names_to_try:
                        try:
                            model = genai_client.GenerativeModel(name)
                            logger.info(f"Gemini 모델 '{name}' 사용")
                            break
                        except Exception as model_error:
                            logger.debug(f"모델 '{name}' 시도 실패: {model_error}")
                            continue
                    
                    if model is None:
                        raise ValueError(f"사용 가능한 Gemini 모델을 찾을 수 없습니다. 시도한 모델: {model_names_to_try}")
                    
                    # Gemini는 시스템 메시지를 별도로 처리하지 않으므로, 전체 프롬프트를 하나로 합침
                    # 언어별 레이블
                    role_labels = {
                        'ko': {'user': '사용자', 'assistant': '어시스턴트'},
                        'en': {'user': 'User', 'assistant': 'Assistant'},
                        'es': {'user': 'Usuario', 'assistant': 'Asistente'},
                        'zh': {'user': '用户', 'assistant': '助手'},
                        'ja': {'user': 'ユーザー', 'assistant': 'アシスタント'}
                    }
                    labels = role_labels.get(language, role_labels['en'])
                    
                    full_prompt = system_prompt
                    for msg in messages[1:]:  # system 메시지 제외
                        if msg['role'] == 'user':
                            full_prompt += f"\n\n{labels['user']}: {msg['content']}"
                        elif msg['role'] == 'assistant':
                            full_prompt += f"\n\n{labels['assistant']}: {msg['content']}"
                    
                    # 안전 필터 설정: 기술적 인터뷰 콘텐츠를 위해 안전 필터 민감도 낮춤
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
                                "threshold": HarmBlockThreshold.BLOCK_ONLY_HIGH  # 기술적 용어 허용을 위해 낮춤
                            }
                        ]
                        response = model.generate_content(
                            full_prompt,
                            generation_config={
                                'temperature': 0.7,
                                'max_output_tokens': 1000,
                            },
                            safety_settings=safety_settings
                        )
                    except (ImportError, AttributeError) as safety_error:
                        # enum을 사용할 수 없으면 기본 설정으로 진행
                        logger.warning(f"안전 필터 설정을 사용할 수 없습니다: {safety_error}. 기본 설정으로 진행합니다.")
                        response = model.generate_content(
                            full_prompt,
                            generation_config={
                                'temperature': 0.7,
                                'max_output_tokens': 1000,
                            }
                        )
                    
                    # 응답 검증
                    if not response.candidates or len(response.candidates) == 0:
                        raise ValueError("Gemini 응답에 후보가 없습니다.")
                    
                    candidate = response.candidates[0]
                    finish_reason = getattr(candidate, 'finish_reason', None)
                    
                    # finish_reason 확인 (0: STOP, 1: MAX_TOKENS, 2: SAFETY, 3: RECITATION, 4: OTHER)
                    if finish_reason == 2:  # SAFETY
                        logger.warning(f"Gemini 응답이 안전 필터링으로 차단됨: finish_reason={finish_reason}")
                        logger.warning(f"안전 필터링 차단 상세: candidate={candidate}, "
                                     f"safety_ratings={getattr(candidate, 'safety_ratings', None)}")
                        # 안전 필터링 차단 시에도 평가가 기록될 수 있도록 503 Service Unavailable 반환
                        # (프론트엔드에서 API 실패로 처리하여 평가 기록 로직이 실행되도록)
                        return Response({
                            'error': 'AI 응답이 안전 필터링으로 차단되었습니다. 평가는 기록됩니다.',
                            'error_type': 'safety_filter',
                            'finish_reason': finish_reason,
                            'detail': 'AI 서비스의 안전 필터링으로 인해 응답을 생성할 수 없습니다. 사용자 답변은 평가됩니다.'
                        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                    elif finish_reason == 1:  # MAX_TOKENS
                        logger.warning(f"Gemini 응답이 토큰 제한으로 잘림: finish_reason={finish_reason}")
                        # 토큰 제한으로 잘렸지만 응답은 있으므로 계속 진행
                    
                    # response.text 접근 시도 (안전하게)
                    try:
                        ai_response = response.text.strip()
                    except ValueError as text_error:
                        logger.error(f"Gemini response.text 접근 실패: {text_error}, finish_reason={finish_reason}")
                        return Response({
                            'error': f'AI 응답을 처리할 수 없습니다. finish_reason={finish_reason}',
                            'error_type': 'response_processing_error',
                            'finish_reason': finish_reason
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
                    if not ai_response:
                        raise ValueError("Gemini 응답이 비어있습니다.")
                    
                    model_used = f"gemini-{name}"
                    usage_info = {
                        'prompt_tokens': 0,  # Gemini는 토큰 정보를 직접 제공하지 않음
                        'completion_tokens': 0,
                        'total_tokens': 0
                    }
                    
                    logger.info(f"Chat 인터뷰 응답 생성 성공 (Gemini): exam_id={exam_id}, user={user.id}, response_length={len(ai_response)}, finish_reason={finish_reason}")
                else:
                    logger.error("Gemini API 키가 설정되지 않았거나 패키지가 설치되지 않았습니다.")
                    # OpenAI quota 초과이고 Gemini가 설정되지 않은 경우 명확한 에러 메시지 반환
                    if is_rate_limit:
                        error_detail = 'OpenAI API 할당량이 초과되었습니다. 나중에 다시 시도해주세요.'
                    else:
                        error_detail = 'OpenAI API 호출에 실패했습니다. 나중에 다시 시도해주세요.'
                    return Response({
                        'error': 'AI 서비스 일시 중단',
                        'detail': error_detail,
                        'error_code': 'API_QUOTA_EXCEEDED' if is_rate_limit else 'API_ERROR'
                    }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                    
            except Exception as gemini_error:
                logger.error(f"Gemini API 호출도 실패: {gemini_error}", exc_info=True)
                # 에러 타입에 따라 적절한 응답 반환
                if isinstance(gemini_error, ValueError) and 'API 키가 설정되지 않았거나' in str(gemini_error):
                    if is_rate_limit:
                        error_detail = 'OpenAI API 할당량이 초과되었습니다. 나중에 다시 시도해주세요.'
                    else:
                        error_detail = 'OpenAI API 호출에 실패했고, 대체 AI 서비스가 설정되지 않았습니다.'
                    return Response({
                        'error': 'AI 서비스 일시 중단',
                        'detail': error_detail,
                        'error_code': 'API_QUOTA_EXCEEDED' if is_rate_limit else 'API_ERROR'
                    }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                else:
                    return Response({
                        'error': 'AI 응답 생성 중 오류가 발생했습니다. OpenAI와 Gemini 모두 실패했습니다.',
                        'detail': f'OpenAI 오류: {str(e)}, Gemini 오류: {str(gemini_error)}',
                        'error_code': 'AI_SERVICE_ERROR'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if ai_response:
            return Response({
                'response': ai_response,
                'model': model_used,
                'usage': usage_info
            })
        else:
            return Response({
                'error': 'AI 응답 생성에 실패했습니다.',
                'detail': '응답을 생성할 수 없습니다.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except ValueError as e:
        logger.error(f"OpenAI API 키 오류: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"Chat 인터뷰 처리 실패: {e}", exc_info=True)
        return Response({
            'error': '인터뷰 처리 중 오류가 발생했습니다.',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
