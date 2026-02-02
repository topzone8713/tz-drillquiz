"""
답변 평가 관련 뷰
OpenAI를 통한 답변 평가 API
"""

import logging
import os
import yaml
import openai
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.utils import timezone
from quiz.utils.multilingual_utils import LANGUAGE_KO, LANGUAGE_EN, LANGUAGE_ES, LANGUAGE_ZH, LANGUAGE_JA, BASE_LANGUAGE, SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)

# 답변 평가 프롬프트 템플릿 캐시
_answer_evaluation_template_cache = None

def load_answer_evaluation_template():
    """ai/prompts/answer_evaluation_template.yaml 파일을 로드합니다."""
    global _answer_evaluation_template_cache
    if _answer_evaluation_template_cache is not None:
        return _answer_evaluation_template_cache
    
    try:
        base_dir = settings.BASE_DIR
        yaml_path = os.path.join(base_dir, 'ai', 'prompts', 'answer_evaluation_template.yaml')
        
        if not os.path.exists(yaml_path):
            logger.warning(f"⚠️ 답변 평가 프롬프트 템플릿 YAML 파일을 찾을 수 없습니다: {yaml_path}")
            _answer_evaluation_template_cache = {lang: {'prompt_template': ''} for lang in SUPPORTED_LANGUAGES}
            return _answer_evaluation_template_cache
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            templates = yaml.safe_load(f)
        
        default_templates = {lang: {'prompt_template': ''} for lang in SUPPORTED_LANGUAGES}
        _answer_evaluation_template_cache = templates or default_templates
        logger.info(f"✅ 답변 평가 프롬프트 템플릿 YAML 파일 로드 성공: {yaml_path}")
        return _answer_evaluation_template_cache
    except Exception as e:
        logger.error(f"❌ 답변 평가 프롬프트 템플릿 YAML 파일 로드 실패: {e}", exc_info=True)
        _answer_evaluation_template_cache = {lang: {'prompt_template': ''} for lang in SUPPORTED_LANGUAGES}
        return _answer_evaluation_template_cache

def get_openai_client():
    """OpenAI 클라이언트를 반환합니다."""
    if not hasattr(settings, 'OPENAI_API_KEY') or not settings.OPENAI_API_KEY:
        raise ValueError("OpenAI API 키가 설정되지 않았습니다.")
    
    return openai.OpenAI(api_key=settings.OPENAI_API_KEY)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def evaluate_answer(request):
    """OpenAI를 사용하여 답변을 평가합니다."""
    try:
        question = request.data.get('question')
        user_answer = request.data.get('user_answer')
        correct_answer = request.data.get('correct_answer')
        language = request.data.get('language', BASE_LANGUAGE)
        exam_difficulty = request.data.get('exam_difficulty', 5)  # 기본값 5
        
        if not all([question, user_answer, correct_answer]):
            return Response({
                'error': 'question, user_answer, correct_answer가 모두 필요합니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 시험 난이도 검증 및 기본값 설정
        try:
            exam_difficulty = max(1, min(10, int(exam_difficulty)))
        except (ValueError, TypeError):
            exam_difficulty = 5
            logger.warning(f"잘못된 exam_difficulty 값, 기본값 5 사용: {request.data.get('exam_difficulty')}")
        
        # 난이도에 따른 평가 가이드라인 가져오기
        from quiz.views.realtime_views import _get_evaluation_guideline
        evaluation_guideline = _get_evaluation_guideline(exam_difficulty, language)
        
        # OpenAI 사용 가능 여부 확인 (캐시 체크)
        from quiz.utils.multilingual_utils import check_openai_availability, mark_openai_unavailable
        is_openai_unavailable = not check_openai_availability()
        
        # OpenAI가 사용 불가능하면 에러 반환 (Gemini fallback은 없음)
        if is_openai_unavailable:
            logger.warning("[evaluate_answer] OpenAI가 캐시에서 사용 불가능 상태로 확인됨")
            return Response({
                'error': 'OpenAI API가 현재 사용 불가능합니다. 잠시 후 다시 시도해주세요.',
                'is_correct': False,
                'reason': 'OpenAI API 사용 불가능'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # OpenAI 클라이언트 생성
        client = get_openai_client()
        
        # YAML 파일에서 프롬프트 템플릿 로드
        templates = load_answer_evaluation_template()
        
        # 언어별 템플릿 가져오기 (언어가 지원되지 않으면 BASE_LANGUAGE 사용)
        lang_key = language if language in templates else BASE_LANGUAGE
        template_data = templates.get(lang_key, {}) or templates.get(BASE_LANGUAGE, {})
        prompt_template = template_data.get('prompt_template', '')
        
        # 템플릿이 없으면 에러 발생
        if not prompt_template:
            error_msg = f"답변 평가 프롬프트 템플릿을 로드할 수 없습니다. ai/prompts/answer_evaluation_template.yaml 파일의 '{lang_key}' 템플릿을 확인해주세요."
            logger.error(error_msg)
            return Response({'error': error_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # 템플릿에 변수 치환
        prompt = prompt_template.format(
            question=question,
            correct_answer=correct_answer,
            user_answer=user_answer,
            exam_difficulty=exam_difficulty,
            evaluation_guideline=evaluation_guideline
        )
        
        # OpenAI API 호출
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert exam evaluator. Evaluate answers based on semantic similarity, not exact word matching."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
        except Exception as e:
            # OpenAI 실패 시 캐시에 마킹
            openai_error = str(e)
            is_rate_limit = False
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                if e.response.status_code == 429:
                    is_rate_limit = True
            elif '429' in str(e) or 'insufficient_quota' in str(e) or 'RateLimitError' in str(type(e).__name__):
                is_rate_limit = True
            
            if is_rate_limit:
                logger.warning(f"[evaluate_answer] OpenAI 429/quota 초과 에러 감지: {e}, 캐시에 마킹...")
            else:
                logger.warning(f"[evaluate_answer] OpenAI API 호출 실패: {e}, 캐시에 마킹...")
            mark_openai_unavailable()
            return Response({
                'error': f'OpenAI API 호출 실패: {openai_error}',
                'is_correct': False,
                'reason': 'OpenAI API 호출 실패'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # 응답 파싱
        result_text = response.choices[0].message.content.strip()
        
        # JSON 파싱 시도
        import json
        try:
            result = json.loads(result_text)
            is_correct = result.get('is_correct', False)
            reason = result.get('reason', '')
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 텍스트에서 true/false 추출
            is_correct = 'true' in result_text.lower()
            reason = result_text
        
        # 상세한 로그 기록
        logger.info(f"답변 평가 완료:")
        logger.info(f"  - 문제: {question}")
        logger.info(f"  - 정답: {correct_answer}")
        logger.info(f"  - 사용자 답변: {user_answer}")
        logger.info(f"  - 답변 길이: {len(user_answer)} 문자")
        logger.info(f"  - 평가 결과: {is_correct}")
        logger.info(f"  - 평가 이유: {reason}")
        logger.info(f"  - 언어: {language}")
        logger.info(f"  - 시험 난이도: {exam_difficulty}")
        logger.info(f"  - 타임스탬프: {timezone.now()}")
        
        return Response({
            'is_correct': is_correct,
            'reason': reason,
            'user_answer': user_answer,
            'correct_answer': correct_answer
        })
        
    except ValueError as e:
        logger.error(f"OpenAI API 키 오류: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"답변 평가 실패: {e}")
        return Response({'error': '답변 평가 중 오류가 발생했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
