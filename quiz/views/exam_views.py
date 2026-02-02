"""
시험 관련 API 뷰

캐시 정리 정책:
1. 시험 생성/삭제/수정 시: ExamCacheManager를 통한 체계적인 캐시 무효화
2. 시험 제출(End 버튼) 시: 시험 결과 관련 캐시 무효화
3. 폴백 메커니즘: ExamCacheManager 실패 시 기존 방식으로 캐시 무효화
4. 로깅: 모든 캐시 무효화 작업에 대한 상세 로그 기록

캐시 계층:
- Redis 환경: delete_pattern을 사용한 효율적인 패턴 매칭
- 로컬 환경: cache.clear() 또는 개별 키 삭제
- 프론트엔드: localStorage, sessionStorage 정리
"""

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from functools import wraps
import uuid
import logging
import random
import os
import pandas as pd
from django.core.cache import cache
from django.db import models
from django.db.models import Q, Count
from django.utils import timezone
from django.http import HttpResponse
from django.conf import settings
from io import BytesIO
from django.contrib.auth import get_user_model
from ..utils.cache_utils import ExamCacheManager, QueryOptimizer
from ..utils.multilingual_utils import get_user_language

User = get_user_model()
from ..models import Question, Exam, ExamQuestion, ExamResult, ExamResultDetail, Member, StudyTask, StudyTaskProgress, IgnoredQuestion, QuestionMemberMapping, Study, AccuracyAdjustmentHistory, ExamSubscription, Tag
from ..serializers import ExamSerializer, QuestionSerializer, CreateExamSerializer, ExamResultSerializer, QuestionMemberMappingSerializer, CreateQuestionMemberMappingSerializer, ExamListSerializer, TagSerializer
from quiz.utils.multilingual_utils import (
    LANGUAGE_EN, LANGUAGE_KO, LANGUAGE_ES, LANGUAGE_ZH, LANGUAGE_JA, BASE_LANGUAGE,
    get_localized_field, get_user_language
)

logger = logging.getLogger(__name__)

# 파일 경로 설정
QUESTION_FILES_DIR = os.path.join('media', 'data')




def normalize_difficulty(difficulty):
    """난이도를 정규화합니다."""
    if not difficulty:
        return 'Medium'

    difficulty = str(difficulty).lower().strip()

    if difficulty in ['easy', '쉬움', '1', '1단계']:
        return 'Easy'
    elif difficulty in ['medium', '보통', '2', '2단계', 'med', 'med.']:
        return 'Medium'
    elif difficulty in ['hard', '어려움', '3', '3단계', 'high']:
        return 'Hard'
    else:
        return 'Medium'


def format_difficulty_for_excel(difficulty):
    """엑셀 다운로드용 난이도 포맷팅"""
    if not difficulty:
        return ''
    
    difficulty = str(difficulty).lower().strip()
    
    if difficulty == 'easy':
        return 'Easy'
    elif difficulty == 'medium':
        return 'Medium'
    elif difficulty == 'hard':
        return 'Hard'
    else:
        return difficulty.capitalize()


def calculate_difficulty_distribution(exam_difficulty, question_count):
    """
    시험 난이도에 따라 문제 난이도 분배를 계산합니다.
    
    Args:
        exam_difficulty: 시험 난이도 (1~10)
        question_count: 생성할 문제 수
    
    Returns:
        dict: {'easy': count, 'medium': count, 'hard': count}
    """
    # 난이도 1: 100% easy
    if exam_difficulty == 1:
        return {'easy': question_count, 'medium': 0, 'hard': 0}
    
    # 난이도 10: 100% hard
    if exam_difficulty == 10:
        return {'easy': 0, 'medium': 0, 'hard': question_count}
    
    # 난이도 2~9: medium을 기본으로 하고, easy/hard 비율 조정
    # 난이도 5: easy 30%, medium 40%, hard 30%
    # 난이도가 낮아질수록 easy 증가, hard 감소
    # 난이도가 높아질수록 easy 감소, hard 증가
    
    # medium은 항상 40% 고정 (난이도 1, 10 제외)
    medium_ratio = 0.4
    
    # 나머지 60%를 easy와 hard로 분배
    # exam_difficulty가 1에 가까울수록 easy가 많고, 10에 가까울수록 hard가 많음
    # 난이도 5: easy 30%, hard 30% (균등)
    # 난이도 2: easy 45%, hard 15%
    # 난이도 8: easy 15%, hard 45%
    
    remaining_ratio = 1.0 - medium_ratio  # 0.6
    
    # easy와 hard의 비율 계산 (난이도 5 기준으로 50:50)
    # 난이도 1에서 easy 100%, 난이도 10에서 hard 100%
    # 난이도 5에서 easy 50%, hard 50% (나머지 60% 중에서)
    
    # easy 비율: (10 - exam_difficulty) / 9 * remaining_ratio
    # hard 비율: (exam_difficulty - 1) / 9 * remaining_ratio
    
    easy_ratio = (10 - exam_difficulty) / 9 * remaining_ratio
    hard_ratio = (exam_difficulty - 1) / 9 * remaining_ratio
    
    # 문제 수 계산 (반올림)
    easy_count = round(question_count * easy_ratio)
    hard_count = round(question_count * hard_ratio)
    medium_count = question_count - easy_count - hard_count
    
    # 음수 방지 및 총합 보정
    easy_count = max(0, easy_count)
    hard_count = max(0, hard_count)
    medium_count = max(0, medium_count)
    
    # 총합이 question_count와 다를 경우 조정
    total = easy_count + medium_count + hard_count
    if total != question_count:
        diff = question_count - total
        # medium에 차이만큼 추가/제거
        medium_count += diff
    
    return {
        'easy': max(0, easy_count),
        'medium': max(0, medium_count),
        'hard': max(0, hard_count)
    }


def auto_correct_csv_from_content(content):
    """CSV 내용을 자동으로 보정합니다."""
    try:
        print(f"auto_correct_csv_from_content 호출됨. 내용 길이: {len(content)}")

        # 먼저 전체 내용을 한 번에 파싱해서 문제가 있는 줄 찾기
        import csv
        from io import StringIO

        # 원본 내용으로 pandas 읽기 시도
        try:
            test_df = pd.read_csv(StringIO(content))
            print(f"원본 CSV 읽기 성공. 컬럼 수: {len(test_df.columns)}")
            return StringIO(content)  # 원본이 정상이면 그대로 반환
        except Exception as e:
            print(f"원본 CSV 읽기 실패: {e}")

        # 수동으로 줄 단위 처리
        lines = content.splitlines()
        print(f"분할된 행 수: {len(lines)}")

        # 빈 행 제거
        lines = [line.strip() for line in lines if line.strip()]
        print(f"빈 행 제거 후 행 수: {len(lines)}")

        if not lines:
            raise ValueError("파일이 비어있습니다.")

        # 첫 번째 행을 헤더로 사용
        header = lines[0]
        header_columns = list(csv.reader([header]))[0]
        expected_columns = len(header_columns)
        print(f"헤더 컬럼 수: {expected_columns}, 헤더: {header_columns}")

        corrected_lines = [header]
        newline_cells_count = 0  # 줄바꿈이 포함된 셀 수 추적

        for i, line in enumerate(lines[1:], 1):
            try:
                print(f"처리 중인 행 {i}: {line[:100]}...")

                # CSV reader를 사용해서 파싱 시도
                try:
                    parsed_row = list(csv.reader([line]))[0]
                    print(f"  CSV reader로 파싱 성공: {len(parsed_row)}개 컬럼")

                    # 컬럼 개수 맞추기
                    while len(parsed_row) < expected_columns:
                        parsed_row.append('')
                    if len(parsed_row) > expected_columns:
                        parsed_row = parsed_row[:expected_columns]

                    # 줄바꿈이 포함된 셀 확인 및 처리
                    corrected_row = []
                    for cell in parsed_row:
                        if '\n' in cell:
                            newline_cells_count += 1
                            # 줄바꿈을 공백으로 대체
                            cell = cell.replace('\n', ' ').replace('\r', ' ')
                        corrected_row.append(cell)

                    # 수정된 행을 CSV 형식으로 다시 작성
                    corrected_line = ','.join([f'"{cell}"' if ',' in cell or '"' in cell else cell for cell in corrected_row])
                    corrected_lines.append(corrected_line)

                except Exception as csv_error:
                    print(f"  CSV reader 파싱 실패: {csv_error}")
                    # 수동으로 처리
                    corrected_lines.append(line)

            except Exception as row_error:
                print(f"  행 {i} 처리 실패: {row_error}")
                corrected_lines.append(line)

        print(f"총 {newline_cells_count}개 셀에서 줄바꿈 제거됨")
        corrected_content = '\n'.join(corrected_lines)
        return StringIO(corrected_content)

    except Exception as e:
        print(f"auto_correct_csv_from_content 전체 실패: {e}")
        raise e


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_single_question_exam(request):
    """단일 문제 풀기를 위한 시험 데이터를 반환합니다. (인증 필요)"""
    try:
        print(f"[DEBUG] create_single_question_exam 호출됨")
        print(f"[DEBUG] request.data: {request.data}")
        print(f"[DEBUG] request.data type: {type(request.data)}")
        
        question_id = request.data.get('question_id')
        exam_id = request.data.get('exam_id')  # 현재 시험 ID
        
        print(f"[DEBUG] question_id: {question_id}")
        print(f"[DEBUG] exam_id: {exam_id}")

        if not question_id:
            print(f"[DEBUG] question_id가 없음")
            return Response({'error': '문제 ID가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            question = Question.objects.get(id=question_id)
            
            # 사용자 언어 확인 및 번역 처리
            # MultilingualContentManager의 _get_user_language 메서드와 동일한 로직 사용
            from quiz.utils.multilingual_utils import BASE_LANGUAGE, SUPPORTED_LANGUAGES
            user_language = BASE_LANGUAGE  # 기본값
            try:
                if hasattr(request.user, 'userprofile'):
                    user_language = request.user.userprofile.language
                elif hasattr(request.user, 'profile'):
                    user_language = request.user.profile.language
            except Exception:
                pass
            
            if question:
                # 사용자 언어를 우선 사용, 없으면 기본 언어('en') 사용
                question_title = None
                if hasattr(question, f'title_{user_language}'):
                    question_title = getattr(question, f'title_{user_language}', None)
                if not question_title:
                    question_title = getattr(question, f'title_{BASE_LANGUAGE}', None)
                if not question_title:
                    for lang in SUPPORTED_LANGUAGES:
                        question_title = getattr(question, f'title_{lang}', None)
                        if question_title:
                            break
                question_title = question_title or '제목 없음'
                print(f"[DEBUG] 문제 찾음: {question_title}")
            else:
                question_title = '제목 없음'
                print(f"[DEBUG] 문제 찾음: {question_title}")
            
            print(f"[DEBUG] 자동 번역 - 사용자 언어: {user_language}")
            
            # 번역이 필요한지 확인하고 자동 번역 수행
            translation_needed = False
            
            from quiz.utils.multilingual_utils import LANGUAGE_EN, LANGUAGE_KO, LANGUAGE_ES, LANGUAGE_ZH
            if user_language == LANGUAGE_EN:
                # 영어 사용자: 영어 필드가 비어있으면 번역 필요
                if question and (not question.title_en or not question.content_en or not question.answer_en or not question.explanation_en):
                    translation_needed = True
                    print(f"[DEBUG] 영어 사용자 - 영어 필드 번역 필요: title_en={bool(question.title_en if question else False)}, content_en={bool(question.content_en if question else False)}, answer_en={bool(question.answer_en if question else False)}, explanation_en={bool(question.explanation_en if question else False)})")
            elif user_language in [LANGUAGE_KO, LANGUAGE_ES, LANGUAGE_ZH]:
                # ko, es, zh 사용자: 해당 언어 필드가 비어있으면 번역 필요 (모두 en으로 번역)
                field_suffix = user_language  # 'ko', 'es', 'zh', 'ja'
                if question and (not getattr(question, f'title_{field_suffix}', None) or 
                                 not getattr(question, f'content_{field_suffix}', None) or 
                                 not getattr(question, f'answer_{field_suffix}', None) or 
                                 not getattr(question, f'explanation_{field_suffix}', None)):
                    translation_needed = True
                    print(f"[DEBUG] {user_language} 사용자 - {user_language} 필드 번역 필요")
            
            if translation_needed:
                try:
                    from ..utils.multilingual_utils import MultilingualContentManager
                    print(f"[DEBUG] 자동 번역 시작: 문제 {question.id}")
                    # 번역 처리 - Question 모델에 맞는 필드 지정
                    manager = MultilingualContentManager(question, request.user, language_fields=['title', 'content', 'answer', 'explanation'])
                    manager.handle_multilingual_update()
                    # 번역 후 문제 다시 조회
                    question.refresh_from_db()
                    print(f"[DEBUG] 자동 번역 완료: 문제 {question.id}")
                    logger.info(f"[AUTO_TRANSLATION] 문제 {question.id} 자동 번역 완료")
                except Exception as e:
                    print(f"[DEBUG] 자동 번역 실패: {str(e)}")
                    logger.warning(f"[AUTO_TRANSLATION] 문제 {question.id} 자동 번역 실패: {str(e)}")
            else:
                print(f"[DEBUG] 번역 불필요: 모든 필드가 완성됨")
            
        except Question.DoesNotExist:
            print(f"[DEBUG] 문제를 찾을 수 없음: {question_id}")
            return Response({'error': '문제를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        # 단일 문제 풀기에서는 무시 상태를 확인하지 않음
        # 무시된 문제는 랜덤 시험 생성 시에만 제외됨

        if exam_id:
            # 현재 시험을 사용
            try:
                exam = Exam.objects.get(id=exam_id)
                user_lang = get_user_language(request)
                exam_title = get_localized_field(exam, 'title', user_lang, 'Unknown')
                print(f"[DEBUG] 시험 찾음: {exam_title}")
                
                # favorite 시험인지 확인
                user_lang = get_user_language(request)
                exam_title = get_localized_field(exam, 'title', user_lang, '')
                is_favorite_exam = ("'s favorite" in exam_title) and exam.is_original
                
                # 현재 시험에 해당 문제가 있는지 확인
                exam_question = ExamQuestion.objects.filter(exam=exam, question=question).first()
                print(f"[DEBUG] ExamQuestion 조회 결과: {exam_question}")
                if not exam_question:
                    print(f"[DEBUG] 문제가 시험에 포함되지 않음: {question_id} in {exam_id}")
                    return Response({'error': '해당 문제가 시험에 포함되어 있지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)

                # 현재 시험에서 해당 문제만 필터링하여 반환
                exam_data = ExamSerializer(exam, context={'request': request}).data
                exam_data['questions'] = [QuestionSerializer(question, context={'request': request}).data]
                exam_data['total_questions'] = 1

                return Response(exam_data, status=status.HTTP_200_OK)

            except Exam.DoesNotExist:
                return Response({'error': '시험을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            # 임시 시험 생성 (기존 로직)
            exam = Exam.objects.create(
                total_questions=1,
                is_original=False
            )
            
            # 다국어 필드 설정 (모든 언어에 대해 설정)
            user_lang = get_user_language(request)
            from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
            exam.title_ko = f"단일 문제 - {question_title}"
            exam.title_en = f"Single Question - {question_title}"
            exam.title_es = f"Pregunta única - {question_title}"
            exam.title_zh = f"单一问题 - {question_title}"
            exam.title_ja = f"単一問題 - {question_title}"
            exam.save()

            # 시험에 문제 추가
            ExamQuestion.objects.create(
                exam=exam,
                question=question,
                order=1
            )

            serializer = ExamSerializer(exam, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    except Question.DoesNotExist:
        return Response({'error': '문제를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'시험 생성 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
def delete_question_results(request):
    """선택한 문제들의 풀이 결과를 삭제합니다."""
    try:
        print(f"delete_question_results 호출됨 - request.data: {request.data}")

        question_ids = request.data.get('question_ids', [])
        exam_id = request.data.get('exam_id')
        delete_all = request.data.get('delete_all', False)  # 모든 문제 결과 삭제 옵션

        print(f"question_ids: {question_ids}")
        print(f"exam_id: {exam_id}")
        print(f"delete_all: {delete_all}")

        if not exam_id:
            return Response({'error': '시험 ID가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 현재 로그인한 사용자의 결과만 필터링
        current_user = request.user
        print(f"현재 사용자: {current_user}")

        # 해당 시험의 결과들 중에서 현재 사용자의 결과만 선택
        exam_results = ExamResult.objects.filter(exam_id=exam_id, user=current_user)

        print(f"찾은 현재 사용자의 시험 결과 수: {exam_results.count()}")

        if delete_all:
            # 모든 문제 결과 삭제 (현재 사용자의 것만)
            deleted_count = 0
            for result in exam_results:
                details_to_delete = ExamResultDetail.objects.filter(result=result)
                count = details_to_delete.count()
                deleted_count += count
                print(f"시험 결과 {result.id}에서 모든 답안 삭제: {count}개")

                # 디버깅: 실제로 푼 문제들 확인
                if count > 0:
                    user_lang = get_user_language(request)
                    for detail in details_to_delete:
                        question = detail.question
                        if question:
                            question_title = get_localized_field(question, 'title', user_lang, '제목 없음')
                            print(f"  - 문제: {question_title} (ID: {question.id}) - 답안: {detail.user_answer} (정답: {detail.is_correct})")
                        else:
                            print(f"  - 문제: 제목 없음 (ID: {detail.question_id}) - 답안: {detail.user_answer} (정답: {detail.is_correct})")

                details_to_delete.delete()
                
                # ExamResult 자체도 삭제 (전체 결과 삭제 시)
                result.delete()
        else:
            # 선택된 문제들의 결과만 삭제 (현재 사용자의 것만)
            if not question_ids:
                return Response({'error': '삭제할 문제 ID가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

            # 문자열을 UUID로 변환
            question_uuids = []
            for qid in question_ids:
                try:
                    question_uuids.append(uuid.UUID(qid))
                except ValueError:
                    print(f"잘못된 UUID 형식: {qid}")

            print(f"변환된 UUID들: {question_uuids}")

            # 디버깅: 시험에 포함된 문제들 확인
            try:
                exam = Exam.objects.get(id=exam_id)
                exam_questions = Question.objects.filter(examquestion__exam=exam)
                logger.info(f"시험에 포함된 문제들: {len(exam_questions)}개")
                print(f"선택된 문제들이 시험에 포함되어 있는지 확인:")
                for qid in question_uuids:
                    is_in_exam = exam_questions.filter(id=qid).exists()
                    print(f"  문제 {qid}: {'포함됨' if is_in_exam else '포함되지 않음'}")
            except Exam.DoesNotExist:
                print(f"시험 {exam_id}를 찾을 수 없습니다.")

            deleted_count = 0
            for result in exam_results:
                # 해당 결과에서 선택된 문제들의 답안만 삭제
                details_to_delete = ExamResultDetail.objects.filter(
                    result=result,
                    question_id__in=question_uuids
                )
                count = details_to_delete.count()
                deleted_count += count
                print(f"시험 결과 {result.id}에서 삭제할 답안 수: {count}")

                # 디버깅: 이 시험 결과에 포함된 문제들 확인
                result_questions = ExamResultDetail.objects.filter(result=result).values_list('question_id', flat=True)
                logger.info(f"시험 결과 {result.id}에 포함된 문제들: {len(result_questions)}개")

                details_to_delete.delete()

        print(f"총 삭제된 답안 수: {deleted_count}")

        # ========================================
        # 🔄 REDIS 캐시 무효화 (중요!)
        # ========================================
        # 
        # 문제 풀이 결과 삭제 후 통계 데이터와 캐시 간의 불일치를 방지하기 위해
        # 관련된 모든 캐시를 무효화해야 합니다.
        #
        # 🎯 캐시 무효화가 필요한 이유:
        # 1. 문제 풀이 결과가 삭제되었지만 통계는 이전 데이터를 반환하는 문제
        # 2. 화면에 표시되는 통계와 실제 DB 데이터 간의 불일치
        # 3. 사용자가 삭제 후에도 이전 통계를 보게 되는 문제
        #
        # 🏗️ 캐시 무효화 전략:
        # 1차: ExamCacheManager를 통한 체계적인 캐시 무효화
        # 2차: Redis 패턴 매칭을 통한 포괄적인 캐시 무효화 (폴백)
        # 3차: 개별 키 기반 캐시 무효화 (최후 수단)
        #
        # 📋 무효화 대상 캐시:
        # - exams_*: 시험 관련 모든 캐시
        # - exam_results_*: 시험 결과 관련 모든 캐시
        # - question_statistics_*: 문제 통계 관련 모든 캐시
        # - statistics_*: 통계 관련 모든 캐시
        #
        # ⚠️ 주의사항:
        # - Redis 환경에서는 delete_pattern을 사용하여 효율적으로 패턴 매칭
        # - 로컬 환경에서는 개별 키를 하나씩 삭제
        # - 모든 단계에서 예외 처리를 통해 안정성 확보
        # ========================================

        # 1차: ExamCacheManager를 통한 체계적인 캐시 무효화
        try:
            from ..utils.cache_utils import ExamCacheManager
            # 문제 풀이 결과 삭제 후 관련 캐시 무효화
            ExamCacheManager.invalidate_all_exam_cache()
            if current_user.is_authenticated:
                ExamCacheManager.invalidate_user_exam_cache(current_user.id)
            logger.info(f"[DELETE_QUESTION_RESULTS] ExamCacheManager를 통한 캐시 무효화 완료: {current_user.username}")
        except Exception as e:
            logger.error(f"[DELETE_QUESTION_RESULTS] ExamCacheManager 캐시 무효화 실패: {e}")
            # 폴백: 기존 방식으로 캐시 무효화
            try:
                if hasattr(cache, 'delete_pattern'):
                    # 문제 풀이 결과 관련 캐시 무효화
                    cache.delete_pattern("exams_*")
                    cache.delete_pattern("exam_results_*")
                    cache.delete_pattern("question_statistics_*")
                    cache.delete_pattern("statistics_*")
                    logger.info("[DELETE_QUESTION_RESULTS] Redis 패턴 기반 캐시 무효화 완료")
                else:
                    # 다른 캐시 백엔드의 경우 개별 키 삭제
                    cache.delete("exams_anonymous")
                    if current_user.is_authenticated:
                        cache.delete(f"exams_{current_user.id}")
                    cache.delete("exam_results_anonymous")
                    if current_user.is_authenticated:
                        cache.delete(f"exam_results_{current_user.id}")
                    logger.info("[DELETE_QUESTION_RESULTS] 개별 키 기반 캐시 무효화 완료")
            except Exception as e2:
                logger.error(f"[DELETE_QUESTION_RESULTS] 폴백 캐시 무효화도 실패: {e2}")

        return Response({
            'message': f'{deleted_count}개의 문제 풀이 결과가 삭제되었습니다.',  # TODO: 번역 키로 변경 필요
            'deleted_count': deleted_count
        }, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"delete_question_results 오류: {str(e)}")
        import traceback
        print(f"오류 상세: {traceback.format_exc()}")
        return Response({'error': f'문제 풀이 결과 삭제 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
def delete_question_results_global(request):
    """특정 문제의 모든 풀이 결과를 삭제합니다 (어떤 시험에서 푼 것인지 상관없이)."""
    try:
        print(f"delete_question_results_global 호출됨 - request.data: {request.data}")

        question_ids = request.data.get('question_ids', [])

        print(f"question_ids: {question_ids}")

        if not question_ids:
            return Response({'error': '삭제할 문제 ID가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 현재 로그인한 사용자의 결과만 필터링
        current_user = request.user
        print(f"현재 사용자: {current_user}")

        # 문자열을 UUID로 변환
        question_uuids = []
        for qid in question_ids:
            try:
                question_uuids.append(uuid.UUID(qid))
            except ValueError:
                print(f"잘못된 UUID 형식: {qid}")

        print(f"변환된 UUID들: {question_uuids}")

        # 현재 사용자의 해당 문제들의 모든 풀이 결과 삭제
        deleted_count = 0
        for question_id in question_uuids:
            # 해당 문제의 현재 사용자 풀이 결과만 찾기
            details_to_delete = ExamResultDetail.objects.filter(
                question_id=question_id,
                result__user=current_user
            )
            count = details_to_delete.count()
            deleted_count += count

            # 디버깅: 삭제할 문제 정보 출력
            if count > 0:
                user_lang = get_user_language(request)
                question = details_to_delete.first().question
                if question:
                    question_title = get_localized_field(question, 'title', user_lang, '제목 없음')
                    print(f"문제 '{question_title}' (ID: {question_id})의 현재 사용자 풀이 결과 {count}개 삭제")
                else:
                    print(f"문제 '제목 없음' (ID: {question_id})의 현재 사용자 풀이 결과 {count}개 삭제")

                # 어떤 시험에서 푼 것인지 확인
                for detail in details_to_delete:
                    result = detail.result
                    exam_title = get_localized_field(result.exam, 'title', user_lang, 'Unknown')
                    print(f"  - 시험: {exam_title} (ID: {result.exam.id}) - 답안: {detail.user_answer} (정답: {detail.is_correct})")

            details_to_delete.delete()

        print(f"총 삭제된 답안 수: {deleted_count}")

        # ========================================
        # 🔄 REDIS 캐시 무효화 (중요!)
        # ========================================
        # 
        # 문제 풀이 결과 삭제 후 통계 데이터와 캐시 간의 불일치를 방지하기 위해
        # 관련된 모든 캐시를 무효화해야 합니다.
        #
        # 🎯 캐시 무효화가 필요한 이유:
        # 1. 문제 풀이 결과가 삭제되었지만 통계는 이전 데이터를 반환하는 문제
        # 2. 화면에 표시되는 통계와 실제 DB 데이터 간의 불일치
        # 3. 사용자가 삭제 후에도 이전 통계를 보게 되는 문제
        #
        # 🏗️ 캐시 무효화 전략:
        # 1차: ExamCacheManager를 통한 체계적인 캐시 무효화
        # 2차: Redis 패턴 매칭을 통한 포괄적인 캐시 무효화 (폴백)
        # 3차: 개별 키 기반 캐시 무효화 (최후 수단)
        #
        # 📋 무효화 대상 캐시:
        # - exams_*: 시험 관련 모든 캐시
        # - exam_results_*: 시험 결과 관련 모든 캐시
        # - question_statistics_*: 문제 통계 관련 모든 캐시
        # - statistics_*: 통계 관련 모든 캐시
        #
        # ⚠️ 주의사항:
        # - Redis 환경에서는 delete_pattern을 사용하여 효율적으로 패턴 매칭
        # - 로컬 환경에서는 개별 키를 하나씩 삭제
        # - 모든 단계에서 예외 처리를 통해 안정성 확보
        # ========================================

        # 1차: ExamCacheManager를 통한 체계적인 캐시 무효화
        try:
            from ..utils.cache_utils import ExamCacheManager
            
            # 모든 사용자의 시험 관련 캐시 무효화
            ExamCacheManager.invalidate_all_exam_cache()
            
            # 현재 사용자의 개별 캐시도 무효화 (사용자별 데이터 분리)
            if current_user.is_authenticated:
                ExamCacheManager.invalidate_user_exam_cache(current_user.id)
            
            logger.info(f"[DELETE_QUESTION_RESULTS_GLOBAL] ✅ ExamCacheManager를 통한 캐시 무효화 완료: 사용자={current_user.username}")
            
        except Exception as e:
            logger.error(f"[DELETE_QUESTION_RESULTS_GLOBAL] ❌ ExamCacheManager 캐시 무효화 실패: {e}")
            
            # 2차: 폴백 - Redis 패턴 기반 캐시 무효화
            try:
                if hasattr(cache, 'delete_pattern'):
                    # Redis 환경: 패턴 매칭을 통한 효율적인 캐시 무효화
                    logger.info("[DELETE_QUESTION_RESULTS_GLOBAL] 🔄 Redis 패턴 기반 캐시 무효화 시작")
                    
                    # 문제 풀이 결과 삭제와 관련된 모든 캐시 패턴
                    cache_patterns = [
                        "exams_*",              # 시험 관련 모든 캐시
                        "exam_results_*",       # 시험 결과 관련 모든 캐시
                        "question_statistics_*", # 문제 통계 관련 모든 캐시
                        "statistics_*"          # 통계 관련 모든 캐시
                    ]
                    
                    for pattern in cache_patterns:
                        try:
                            cache.delete_pattern(pattern)
                            logger.info(f"[DELETE_QUESTION_RESULTS_GLOBAL] ✅ 패턴 '{pattern}' 캐시 삭제 완료")
                        except Exception as pattern_error:
                            logger.warning(f"[DELETE_QUESTION_RESULTS_GLOBAL] ⚠️ 패턴 '{pattern}' 캐시 삭제 실패: {pattern_error}")
                    
                    logger.info("[DELETE_QUESTION_RESULTS_GLOBAL] ✅ Redis 패턴 기반 캐시 무효화 완료")
                    
                else:
                    # 3차: 최후 수단 - 개별 키 기반 캐시 무효화
                    logger.info("[DELETE_QUESTION_RESULTS_GLOBAL] 🔄 개별 키 기반 캐시 무효화 시작")
                    
                    # 로컬 캐시 환경에서 개별 키를 하나씩 삭제
                    cache_keys_to_delete = [
                        "exams_anonymous",                    # 익명 사용자 시험 캐시
                        f"exams_{current_user.id}" if current_user.is_authenticated else None,  # 현재 사용자 시험 캐시
                        "exam_results_anonymous",             # 익명 사용자 시험 결과 캐시
                        f"exam_results_{current_user.id}" if current_user.is_authenticated else None  # 현재 사용자 시험 결과 캐시
                    ]
                    
                    # None 값 제거 후 캐시 삭제
                    cache_keys_to_delete = [key for key in cache_keys_to_delete if key is not None]
                    
                    for key in cache_keys_to_delete:
                        try:
                            cache.delete(key)
                            logger.info(f"[DELETE_QUESTION_RESULTS_GLOBAL] ✅ 개별 키 '{key}' 캐시 삭제 완료")
                        except Exception as key_error:
                            logger.warning(f"[DELETE_QUESTION_RESULTS_GLOBAL] ⚠️ 개별 키 '{key}' 캐시 삭제 실패: {key_error}")
                    
                    logger.info("[DELETE_QUESTION_RESULTS_GLOBAL] ✅ 개별 키 기반 캐시 무효화 완료")
                    
            except Exception as e2:
                logger.error(f"[DELETE_QUESTION_RESULTS_GLOBAL] ❌ 폴백 캐시 무효화도 실패: {e2}")
                logger.error(f"[DELETE_QUESTION_RESULTS_GLOBAL] ⚠️ 캐시 무효화 실패로 인해 통계 데이터 불일치가 발생할 수 있습니다!")
                
                # 최종 경고 로그
                logger.warning(f"[DELETE_QUESTION_RESULTS_GLOBAL] 🚨 사용자 {current_user.username}의 문제 풀이 결과 삭제는 완료되었지만, 캐시 무효화에 실패했습니다.")
                logger.warning(f"[DELETE_QUESTION_RESULTS_GLOBAL] 🚨 화면에 표시되는 통계와 실제 DB 데이터가 일치하지 않을 수 있습니다.")
                logger.warning(f"[DELETE_QUESTION_RESULTS_GLOBAL] 🚨 수동으로 페이지를 새로고침하거나 캐시를 초기화해야 할 수 있습니다.")

        return Response({
            'message': f'{deleted_count}개의 문제 풀이 결과가 삭제되었습니다.',  # TODO: 번역 키로 변경 필요
            'deleted_count': deleted_count
        }, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"delete_question_results_global 오류: {str(e)}")
        import traceback
        print(f"오류 상세: {traceback.format_exc()}")
        return Response({'error': f'문제 풀이 결과 삭제 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def create_exam(request):
    """새로운 시험을 생성합니다."""
    # 캐시 무효화 (ExamCacheManager 사용)
    try:
        from ..utils.cache_utils import ExamCacheManager
        # 모든 사용자의 시험 관련 캐시 무효화
        ExamCacheManager.invalidate_all_exam_cache()
        logger.info("[CREATE_EXAM] ExamCacheManager를 통한 캐시 무효화 완료")
    except Exception as e:
        logger.error(f"[CREATE_EXAM] ExamCacheManager 캐시 무효화 실패: {e}")
        # 폴백: 기존 방식으로 캐시 무효화
        try:
            if hasattr(cache, 'delete_pattern'):
                cache.delete_pattern("exams_*")
                logger.info("[CREATE_EXAM] Redis 패턴 기반 캐시 무효화 완료")
            else:
                cache.delete("exams_anonymous")
                if request.user.is_authenticated:
                    cache.delete(f"exams_{request.user.id}")
                logger.info("[CREATE_EXAM] 개별 키 기반 캐시 무효화 완료")
        except Exception as e2:
            logger.error(f"[CREATE_EXAM] 폴백 캐시 무효화도 실패: {e2}")

    logger.info(f"[CREATE_EXAM] 요청 시작")
    logger.info(f"[CREATE_EXAM] 사용자: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
    logger.info(f"[CREATE_EXAM] 요청 데이터: {request.data}")
    logger.info(f"[CREATE_EXAM] 요청 데이터 타입: {type(request.data)}")
    logger.info(f"[CREATE_EXAM] 요청 데이터 키: {list(request.data.keys()) if hasattr(request.data, 'keys') else 'N/A'}")

    serializer = CreateExamSerializer(data=request.data)
    logger.info(f"[CREATE_EXAM] Serializer 생성 완료")

    if serializer.is_valid():
        logger.info(f"[CREATE_EXAM] Serializer 검증 성공")
        logger.info(f"[CREATE_EXAM] 검증된 데이터: {serializer.validated_data}")
        title = serializer.validated_data['title']
        description = serializer.validated_data.get('description', '')
        question_count = serializer.validated_data.get('question_count')
        wrong_questions_only = serializer.validated_data['wrong_questions_only']
        random_option = serializer.validated_data.get('random_option', 'random')
        specific_questions = serializer.validated_data.get('questions', [])
        is_original = serializer.validated_data.get('is_original', True)
        is_public = serializer.validated_data.get('is_public', False)
        file_name = request.data.get('file_name')
        creation_type = request.data.get('creation_type', 'new')  # 'new', 'copy', 'random'
        parsed_problems = serializer.validated_data.get('parsed_problems', [])
        
        # Random Exam Creation의 경우 기존에 같은 이름의 시험이 있으면 덮어쓰기
        if creation_type == 'random' and request.user.is_authenticated:
            existing_exam = Exam.objects.filter(
                Q(title_ko=title) | Q(title_en=title),  # 한국어 또는 영어 제목으로 검색
                created_by=request.user,
                is_original=False  # 복사된 시험이 아닌 원본 시험만 대상
            ).first()
            
            if existing_exam:
                logger.info(f"[CREATE_EXAM] 기존 시험 발견, 덮어쓰기: {existing_exam.id}")
                # 기존 시험 삭제
                existing_exam.delete()
                logger.info(f"[CREATE_EXAM] 기존 시험 삭제 완료")
        
        # difficulty 처리
        difficulty = serializer.validated_data.get('difficulty', '')
        normalized_difficulty = normalize_difficulty(difficulty)
        logger.info(f"[CREATE_EXAM] 원본 difficulty: {difficulty}, 정규화된 difficulty: {normalized_difficulty}")

        print(f"File name: {file_name}")
        print(f"Specific questions: {specific_questions}")
        print(f"Random option: {random_option}")
        print(f"Creation type: {creation_type}")
        print(f"Parsed problems: {len(parsed_problems) if parsed_problems else 0}")

        # selection_mode 처리
        selection_mode = request.data.get('selection_mode', 'random')
        print(f"[DEBUG] selection_mode: {selection_mode}")
        
        # parsed_problems가 있는 경우 전체 문제 번역을 피하기 위한 플래그 설정
        skip_batch_translation = bool(parsed_problems)
        if parsed_problems:
            logger.info(f"[CREATE_EXAM] parsed_problems 처리 모드: {len(parsed_problems)}개 문제")
            logger.info(f"[CREATE_EXAM] 전체 문제 번역 건너뛰기: skip_batch_translation = True")
        
        # 특정 문제 ID가 제공된 경우 (프론트엔드에서 현재 보여지고 있는 문제들)
        if specific_questions:
            try:
                print(f"[DEBUG] specific_questions 처리 시작: {len(specific_questions)}개")
                # 중복 제거
                unique_question_ids = list(set(specific_questions))
                print(f"[DEBUG] 중복 제거 후: {len(unique_question_ids)}개")
                questions = Question.objects.filter(id__in=unique_question_ids)
                print(f"[DEBUG] DB에서 찾은 문제: {len(questions)}개")
                if len(questions) != len(unique_question_ids):
                    return Response({'error': '일부 문제를 찾을 수 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)

                # 무시된 문제 제외
                if request.user.is_authenticated:
                    ignored_question_ids = IgnoredQuestion.objects.filter(user=request.user).values_list('question_id', flat=True)
                    questions = [q for q in questions if q.id not in ignored_question_ids]
                    print(f"[DEBUG] 무시된 문제 제외 후 남은 문제 수: {len(questions)}개")

                # Manual Selection 모드인 경우: 선택된 문제들만 사용
                if selection_mode == 'manual':
                    print(f"[DEBUG] Manual Selection 모드: 선택된 {len(questions)}개 문제만 사용")
                    selected_questions = list(questions)
                    question_count = len(selected_questions)
                else:
                    # Random Selection 모드: 요청된 문제 수만큼 선택
                    # 요청된 문제 수가 제공되지 않은 경우, 전체 문제 수 사용
                    if question_count is None:
                        question_count = len(questions)

                    # 문제 수가 0인 경우 빈 리스트로 설정
                    if question_count == 0:
                        selected_questions = []
                    else:
                        # 옵션별 문제 선택 로직
                        if random_option == 'wrong_only':
                            # 틀린 문제만 추출
                            wrong_questions = []
                            for question in questions:
                                # 해당 문제의 최근 시험 결과에서 틀린 횟수 확인
                                wrong_count = ExamResultDetail.objects.filter(
                                    question=question,
                                    is_correct=False
                                ).count()
                                if wrong_count > 0:
                                    wrong_questions.append(question)

                            # 틀린 문제 수가 요청한 문제 수보다 적으면 자동으로 조정
                            if len(wrong_questions) < question_count:
                                original_question_count = question_count
                                question_count = len(wrong_questions)
                                logger.info(f"[CREATE_EXAM] 틀린 문제 수({len(wrong_questions)})가 요청한 문제 수({original_question_count})보다 적어서 {question_count}개로 조정했습니다.")

                            selected_questions = random.sample(wrong_questions, question_count)

                        elif random_option == 'most_wrong':
                            # 많이 틀린 문제 추출 (시도 횟수 많고 오답률 높은 순)
                            question_scores = []
                            user = request.user

                            # 익명 사용자인 경우 빈 결과 반환
                            if not user.is_authenticated:
                                return Response({
                                    'error': '로그인이 필요한 기능입니다.'
                                }, status=status.HTTP_401_UNAUTHORIZED)

                            print(f"[most_wrong] 사용자: {user.username}")
                            print(f"[most_wrong] 총 문제 수: {len(questions)}")

                            for question in questions:
                                # 해당 문제의 총 시험 횟수 (현재 사용자만)
                                total_attempts = ExamResultDetail.objects.filter(
                                    question=question,
                                    result__user=user
                                ).count()

                                if question:
                                    question_title = get_localized_field(question, 'title', user_lang, '제목 없음')
                                    print(f"[most_wrong] 문제 {question.id} ({question_title}): 시도 횟수 = {total_attempts}")
                                else:
                                    print(f"[most_wrong] 문제 {question.id} (제목 없음): 시도 횟수 = {total_attempts}")

                                if total_attempts > 0:
                                    # 틀린 횟수 (현재 사용자만)
                                    wrong_count = ExamResultDetail.objects.filter(
                                        question=question,
                                        result__user=user,
                                        is_correct=False
                                    ).count()
                                    # 오답률 계산
                                    wrong_rate = wrong_count / total_attempts
                                    # 점수 계산: 시도 횟수 * 오답률 (시도 횟수가 많고 오답률이 높을수록 높은 점수)
                                    score = total_attempts * wrong_rate
                                    question_scores.append((question, score, total_attempts, wrong_count))
                                    print(f"[most_wrong] 문제 {question.id} 추가됨: 점수={score}, 시도={total_attempts}, 틀린={wrong_count}")
                                else:
                                    print(f"[most_wrong] 문제 {question.id} 제외됨: 시도 횟수 0")
                                    # 시도 횟수가 0인 문제는 제외

                            # 점수 높은 순으로 정렬 (시도 횟수 많고 오답률 높은 순)
                            question_scores.sort(key=lambda x: x[1], reverse=True)

                            # 상위 문제들 중에서 요청한 수만큼 선택
                            available_questions = [q for q, _, _, _ in question_scores]
                            
                            # 시도 기록이 있는 문제가 없는 경우 일반 랜덤 선택으로 fallback
                            if len(available_questions) == 0:
                                logger.info(f"[CREATE_EXAM] 시도 기록이 있는 문제가 없어서 일반 랜덤 선택으로 변경합니다.")
                                selected_questions = random.sample(list(questions), question_count)
                            else:
                                # 시도 기록이 있는 문제 수가 요청한 문제 수보다 적으면 자동으로 조정
                                if len(available_questions) < question_count:
                                    original_question_count = question_count
                                    question_count = len(available_questions)
                                    logger.info(f"[CREATE_EXAM] 시도 기록이 있는 문제 수({len(available_questions)})가 요청한 문제 수({original_question_count})보다 적어서 {question_count}개로 조정했습니다.")

                                selected_questions = available_questions[:question_count]

                        else:  # random (그냥 랜덤)
                            # 기존 로직과 동일하게 랜덤 추출
                            print(f"[DEBUG] random 옵션 선택: {len(questions)}개 중 {question_count}개 선택")
                            selected_questions = random.sample(list(questions), question_count)

            except Exception as e:
                print(f"[DEBUG] 예외 발생: {str(e)}")
                return Response({'error': f'문제 조회 오류: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        # 특정 문제 ID가 제공되지 않은 경우 (기존 로직)
        elif question_count is not None or random_option == 'most_wrong':
            if file_name:
                # MinIO 또는 로컬 파일 시스템 확인
                from django.conf import settings
                use_minio = getattr(settings, 'USE_MINIO', False)

                if use_minio:
                    # MinIO에서 파일 처리
                    import boto3
                    from botocore.exceptions import ClientError

                    try:
                        s3_client = boto3.client(
                            's3',
                            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                            verify=False
                        )

                        # MinIO에서 파일 다운로드
                        response = s3_client.get_object(
                            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                            Key=f'data/{file_name}'
                        )

                        file_content = response['Body'].read()
                        logger.info(f"[CREATE_EXAM] MinIO에서 파일 다운로드 성공: {file_name}")

                    except ClientError as e:
                        logger.error(f"[CREATE_EXAM] MinIO 파일 다운로드 실패: {e}")
                        return Response({'error': f'선택한 파일이 존재하지 않습니다: {file_name}'}, status=status.HTTP_400_BAD_REQUEST)
                    except Exception as e:
                        logger.error(f"[CREATE_EXAM] MinIO 파일 처리 오류: {e}")
                        return Response({'error': f'파일 처리 오류: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    # 로컬 파일 시스템 사용
                    file_path = os.path.join(QUESTION_FILES_DIR, file_name)
                    logger.info(f"[CREATE_EXAM] 로컬 파일 경로: {file_path}")
                    if not os.path.exists(file_path):
                        logger.error(f"[CREATE_EXAM] 로컬 파일이 존재하지 않음: {file_path}")
                        return Response({'error': f'선택한 파일이 존재하지 않습니다: {file_path}'}, status=status.HTTP_400_BAD_REQUEST)
                file_extension = os.path.splitext(file_name)[1].lower()

                try:
                    if use_minio:
                        # MinIO에서 다운로드한 파일 내용 처리
                        from io import BytesIO

                        if file_extension == '.csv':
                            # CSV 파일 처리
                            content = file_content.decode('utf-8')
                            corrected_file = auto_correct_csv_from_content(content)
                            df = pd.read_csv(corrected_file)
                            logger.info(f"[CREATE_EXAM] MinIO CSV columns: {df.columns.tolist()}")
                        else:
                            # XLS, XLSX 파일 처리
                            file_buffer = BytesIO(file_content)
                            if file_extension == '.xlsx':
                                df = pd.read_excel(file_buffer, engine='openpyxl')
                            else:  # .xls
                                df = pd.read_excel(file_buffer, engine='xlrd')
                            logger.info(f"[CREATE_EXAM] MinIO Excel columns: {df.columns.tolist()}")
                    else:
                        # 로컬 파일 시스템 처리
                        if file_extension == '.csv':
                            # CSV 파일 처리
                            with open(file_path, 'r', encoding='utf-8') as file:
                                content = file.read()
                                corrected_file = auto_correct_csv_from_content(content)
                                df = pd.read_csv(corrected_file)
                                logger.info(f"[CREATE_EXAM] 로컬 CSV columns: {df.columns.tolist()}")
                        else:
                            # XLS, XLSX 파일 처리
                            if file_extension == '.xlsx':
                                df = pd.read_excel(file_path, engine='openpyxl')
                            else:  # .xls
                                df = pd.read_excel(file_path, engine='xlrd')
                            logger.info(f"[CREATE_EXAM] 로컬 Excel columns: {df.columns.tolist()}")

                    # 컬럼명 매핑
                    csv_id_column = None
                    title_column = None
                    content_column = None
                    answer_column = None
                    difficulty_column = None
                    explanation_column = None
                    group_id_column = None
                    url_column = None
                    
                    # CSV ID 컬럼 찾기
                    if '문제id' in df.columns:
                        csv_id_column = '문제id'
                    elif '문제ID' in df.columns:
                        csv_id_column = '문제ID'
                    elif 'Question ID' in df.columns:
                        csv_id_column = 'Question ID'
                    elif 'QuestionID' in df.columns:
                        csv_id_column = 'QuestionID'
                    elif 'ID' in df.columns:
                        csv_id_column = 'ID'
                    elif 'id' in df.columns:
                        csv_id_column = 'id'
                    
                    # 제목 컬럼 찾기
                    if '제목' in df.columns:
                        title_column = '제목'
                    elif 'Title' in df.columns:
                        title_column = 'Title'
                    elif 'title' in df.columns:
                        title_column = 'title'
                    else:
                        logger.error(f"[CREATE_EXAM] 제목 컬럼을 찾을 수 없습니다. 사용 가능한 컬럼: {df.columns.tolist()}")
                        return Response({'error': '제목 컬럼을 찾을 수 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)
                    
                    # 문제 내용 컬럼 찾기
                    if '문제 내용' in df.columns:
                        content_column = '문제 내용'
                    elif 'Question Content' in df.columns:
                        content_column = 'Question Content'
                    elif 'Content' in df.columns:
                        content_column = 'Content'
                    elif '내용' in df.columns:
                        content_column = '내용'
                    
                    # 정답 컬럼 찾기
                    if '정답' in df.columns:
                        answer_column = '정답'
                    elif 'Answer' in df.columns:
                        answer_column = 'Answer'
                    elif 'answer' in df.columns:
                        answer_column = 'answer'
                    elif '답' in df.columns:
                        answer_column = '답'
                    
                    # 난이도 컬럼 찾기
                    if '난위도' in df.columns:
                        difficulty_column = '난위도'
                    elif 'Difficulty' in df.columns:
                        difficulty_column = 'Difficulty'
                    elif 'difficulty' in df.columns:
                        difficulty_column = 'difficulty'
                    elif '난이도' in df.columns:
                        difficulty_column = '난이도'
                    
                    # 설명 컬럼 찾기
                    if '설명' in df.columns:
                        explanation_column = '설명'
                    elif 'Explanation' in df.columns:
                        explanation_column = 'Explanation'
                    elif 'explanation' in df.columns:
                        explanation_column = 'explanation'
                    elif 'Description' in df.columns:
                        explanation_column = 'Description'
                    elif 'description' in df.columns:
                        explanation_column = 'description'
                    
                    # Group ID 컬럼 찾기
                    if 'Group ID' in df.columns:
                        group_id_column = 'Group ID'
                    elif 'GroupID' in df.columns:
                        group_id_column = 'GroupID'
                    elif 'group_id' in df.columns:
                        group_id_column = 'group_id'
                    elif '그룹ID' in df.columns:
                        group_id_column = '그룹ID'
                    
                    # URL 컬럼 찾기
                    if 'URL' in df.columns:
                        url_column = 'URL'
                    elif 'url' in df.columns:
                        url_column = 'url'
                    elif '링크' in df.columns:
                        url_column = '링크'
                    elif 'Link' in df.columns:
                        url_column = 'Link'
                    
                    logger.info(f"[CREATE_EXAM] 컬럼 매핑 - CSV ID: {csv_id_column}, 제목: {title_column}, 내용: {content_column}, 정답: {answer_column}, 난이도: {difficulty_column}, 설명: {explanation_column}, Group ID: {group_id_column}, URL: {url_column}")
                    
                    questions = []
                    for _, row in df.iterrows():
                        try:
                            # 변수 초기화
                            csv_id_value = ''
                            title_value = ''
                            content_value = ''
                            answer_value = ''
                            difficulty_value = None
                            explanation_value = ''
                            group_id_value = ''
                            url_value = ''
                            
                            title1 = row[title_column]
                            
                            if creation_type == 'new':
                                # 새 시험 생성: 엑셀 데이터를 사용해서 새로운 문제 생성
                                logger.info(f"[CREATE_EXAM] [DEBUG] 새 문제 생성 시작: '{title1}'")
                                
                                # 엑셀에서 모든 데이터 읽기
                                title_value = str(title1).strip()
                                
                                # 문제 내용 읽기
                                content_value = ''
                                if content_column and content_column in row and pd.notna(row[content_column]):
                                    content_value = str(row[content_column]).strip()
                                else:
                                    content_value = title_value  # 내용이 없으면 제목을 내용으로 사용
                                
                                # 정답 읽기
                                answer_value = ''
                                if answer_column and answer_column in row and pd.notna(row[answer_column]):
                                    answer_value = str(row[answer_column]).strip()
                                else:
                                    answer_value = 'Y'  # 기본값
                                
                                # 난이도 읽기
                                difficulty_value = None
                                if difficulty_column and difficulty_column in row and pd.notna(row[difficulty_column]):
                                    difficulty_value = normalize_difficulty(str(row[difficulty_column]).strip())
                                
                                # 설명 읽기
                                explanation_value = ''
                                if explanation_column and explanation_column in row and pd.notna(row[explanation_column]):
                                    explanation_value = str(row[explanation_column]).strip()
                                
                                # Group ID 읽기
                                group_id_value = ''
                                if group_id_column and group_id_column in row and pd.notna(row[group_id_column]):
                                    group_id_value = str(row[group_id_column]).strip()
                                
                                # URL 읽기
                                url_value = ''
                                if url_column and url_column in row and pd.notna(row[url_column]):
                                    excel_url = str(row[url_column]).strip()
                                    if excel_url and excel_url.lower() not in ['nan', 'none', 'null', '']:
                                        url_value = excel_url
                                        logger.info(f"[CREATE_EXAM] 엑셀에서 URL 읽음: {title1} -> {url_value}")
                                    else:
                                        logger.info(f"[CREATE_EXAM] 엑셀 URL이 비어있음: {title1}")
                                else:
                                    logger.info(f"[CREATE_EXAM] URL 컬럼 없음: {title1}")
                                
                                # CSV ID 읽기 (엑셀의 문제 순서 번호)
                                csv_id_value = ''
                                if csv_id_column and csv_id_column in row and pd.notna(row[csv_id_column]):
                                    csv_id_value = str(row[csv_id_column]).strip()
                                    logger.info(f"[CREATE_EXAM] 엑셀에서 CSV ID 읽음: {title1} -> {csv_id_value}")
                                else:
                                    # CSV ID가 없으면 제목 기반으로 해시값 생성
                                    csv_id_value = f"excel_{hash(title_value) % 1000000}"
                                    logger.info(f"[CREATE_EXAM] CSV ID 컬럼 없음, 해시값 생성: {title1} -> {csv_id_value}")
                                
                                # source_id 설정 (엑셀 파일명으로 출처 기록)
                                source_id_value = file_name
                                logger.info(f"[CREATE_EXAM] source_id 설정: {title1} -> {source_id_value}")
                                
                                # 새로운 문제 생성 (다국어 필드만 사용)
                                new_q = Question.objects.create(
                                    difficulty=difficulty_value,
                                    url=url_value,
                                    csv_id=csv_id_value,      # 엑셀의 문제 순서 번호
                                    source_id=source_id_value, # 엑셀 파일명 (출처 식별용)
                                    group_id=group_id_value,
                                    created_at=timezone.now(),
                                    updated_at=timezone.now()
                                )
                                
                                # =============================================================================
                                # 🎯 다국어 필드 설정 - 사용자 프로필 언어 기반
                                # =============================================================================
                                # 중요: 무조건 사용자의 프로필 언어를 기준으로 모든 처리가 이루어져야 함
                                # - 영어 사용자: title_en, content_en, answer_en, explanation_en 필드에 저장
                                # - 한국어 사용자: title_ko, content_ko, answer_ko, explanation_ko 필드에 저장
                                # - created_language, is_ko_complete, is_en_complete 자동 설정
                                # =============================================================================
                                
                                # 사용자 프로필 언어 확인 (기본값: BASE_LANGUAGE)
                                from quiz.utils.multilingual_utils import BASE_LANGUAGE
                                user_language = BASE_LANGUAGE
                                try:
                                    if hasattr(request.user, 'userprofile'):
                                        user_language = request.user.userprofile.language
                                    elif hasattr(request.user, 'profile'):
                                        user_language = request.user.profile.language
                                    logger.info(f"[CREATE_EXAM] 사용자 언어 감지: {request.user.username} -> {user_language}")
                                except Exception as e:
                                    logger.warning(f"[CREATE_EXAM] 사용자 언어 감지 실패: {e}, 기본값 'en' 사용")
                                
                                # 언어별 다국어 필드 설정 (모든 언어 동일하게 처리)
                                from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
                                # 사용자 언어 필드에 저장
                                setattr(new_q, f'title_{user_language}', title_value)
                                setattr(new_q, f'content_{user_language}', content_value)
                                setattr(new_q, f'answer_{user_language}', answer_value)
                                if explanation_value:
                                    setattr(new_q, f'explanation_{user_language}', explanation_value)
                                
                                # 언어별 완성도 설정 (모든 언어 동일하게 처리)
                                for lang in SUPPORTED_LANGUAGES:
                                    is_complete = (lang == user_language)
                                    setattr(new_q, f'is_{lang}_complete', is_complete)
                                
                                logger.info(f"[CREATE_EXAM] {user_language} 사용자 - {user_language} 필드에 저장: {title_value[:30]}...")
                                
                                # 생성 언어 설정 및 저장
                                new_q.created_language = user_language
                                new_q.save()
                                
                                # 번역은 나중에 배치로 처리하므로 여기서는 건너뛰기
                                logger.info(f"[CREATE_EXAM] 새 문제 생성 완료: {title1} (ID: {new_q.id}, URL: {url_value})")
                                
                                questions.append(new_q)
                                logger.info(f"[CREATE_EXAM] 새 문제 생성: {title1} (ID: {new_q.id}, group_id: {group_id_value}, URL: {url_value})")
                            else:
                                # 복제/랜덤 생성: 기존 문제 참조
                                logger.info(f"[CREATE_EXAM] [DEBUG] 복제/랜덤 모드 - 문제 검색: '{title1}'")
                                # 한국어와 영어 제목 모두에서 검색
                                from ..utils.question_utils import get_questions_by_title_both_languages
                                qs = get_questions_by_title_both_languages(title1)
                                logger.info(f"[CREATE_EXAM] [DEBUG] 복제/랜덤 모드 - 검색 결과: {qs.count()}개")
                                
                                if qs.exists():
                                    # 랜덤하게 하나 선택
                                    q = random.choice(list(qs))
                                    questions.append(q)
                                    logger.info(f"[CREATE_EXAM] 기존 문제 참조: {title1} (ID: {q.id})")
                                else:
                                    logger.warning(f"[CREATE_EXAM] Question not found: {title1}")
                                    # 더 자세한 디버깅 정보 추가
                                    logger.warning(f"[CREATE_EXAM] [DEBUG] 복제/랜덤 모드 - 전체 Question 개수: {Question.objects.count()}")
                                    logger.warning(f"[CREATE_EXAM] [DEBUG] 복제/랜덤 모드 - 부분 일치 검색 결과:")
                                    partial_matches = Question.objects.filter(
                                        models.Q(title_ko__icontains=title1[:20]) | 
                                        models.Q(title_en__icontains=title1[:20])
                                    )
                                    for pm in partial_matches[:3]:  # 처음 3개만
                                        pm_title = get_localized_field(pm, 'title', user_language, '제목 없음')
                                        logger.warning(f"[CREATE_EXAM] [DEBUG] - 부분 일치: '{pm_title}'")
                        except Exception as e:
                            logger.error(f"[CREATE_EXAM] Error finding question '{title1}': {e}")
                            continue
                    logger.info(f"[CREATE_EXAM] Found {len(questions)} questions from file")
                except Exception as e:
                    logger.error(f"[CREATE_EXAM] 파일 읽기 실패: {e}")
                    # 실패시 다른 방법 시도
                    try:
                        if use_minio:
                            # MinIO 파일 재시도
                            from io import BytesIO
                            file_buffer = BytesIO(file_content)

                            if file_extension == '.csv':
                                df = pd.read_csv(file_buffer)
                            else:
                                if file_extension == '.xlsx':
                                    df = pd.read_excel(file_buffer, engine='openpyxl')
                                else:
                                    df = pd.read_excel(file_buffer, engine='xlrd')
                            logger.info(f"[CREATE_EXAM] MinIO 원본 파일 columns: {df.columns.tolist()}")
                        else:
                            # 로컬 파일 재시도
                            if file_extension == '.csv':
                                df = pd.read_csv(file_path)
                            else:
                                if file_extension == '.xlsx':
                                    df = pd.read_excel(file_path, engine='openpyxl')
                                else:
                                    df = pd.read_excel(file_path, engine='xlrd')
                            logger.info(f"[CREATE_EXAM] 로컬 원본 파일 columns: {df.columns.tolist()}")

                        # 컬럼명 매핑 (재시도)
                        csv_id_column = None
                        title_column = None
                        content_column = None
                        answer_column = None
                        difficulty_column = None
                        explanation_column = None
                        group_id_column = None
                        url_column = None
                        
                        # CSV ID 컬럼 찾기
                        if '문제id' in df.columns:
                            csv_id_column = '문제id'
                        elif '문제ID' in df.columns:
                            csv_id_column = '문제ID'
                        elif 'ID' in df.columns:
                            csv_id_column = 'ID'
                        elif 'id' in df.columns:
                            csv_id_column = 'id'
                        
                        # 제목 컬럼 찾기
                        if '제목' in df.columns:
                            title_column = '제목'
                        elif 'Title' in df.columns:
                            title_column = 'Title'
                        else:
                            logger.error(f"[CREATE_EXAM] 제목 컬럼을 찾을 수 없습니다. 사용 가능한 컬럼: {df.columns.tolist()}")
                            return Response({'error': '제목 컬럼을 찾을 수 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)
                        
                        # 문제 내용 컬럼 찾기
                        if '문제 내용' in df.columns:
                            content_column = '문제 내용'
                        elif 'Content' in df.columns:
                            content_column = 'Content'
                        elif '내용' in df.columns:
                            content_column = '내용'
                        
                        # 정답 컬럼 찾기
                        if '정답' in df.columns:
                            answer_column = '정답'
                        elif 'Answer' in df.columns:
                            answer_column = 'Answer'
                        elif '답' in df.columns:
                            answer_column = '답'
                        
                        # 난이도 컬럼 찾기
                        if '난위도' in df.columns:
                            difficulty_column = '난위도'
                        elif 'Difficulty' in df.columns:
                            difficulty_column = 'Difficulty'
                        elif '난이도' in df.columns:
                            difficulty_column = '난이도'
                        
                        # 설명 컬럼 찾기
                        if '설명' in df.columns:
                            explanation_column = '설명'
                        elif 'Explanation' in df.columns:
                            explanation_column = 'Explanation'
                        
                        # Group ID 컬럼 찾기
                        if 'Group ID' in df.columns:
                            group_id_column = 'Group ID'
                        elif 'GroupID' in df.columns:
                            group_id_column = 'GroupID'
                        elif 'group_id' in df.columns:
                            group_id_column = 'group_id'
                        elif '그룹ID' in df.columns:
                            group_id_column = '그룹ID'
                        
                        # URL 컬럼 찾기
                        if 'URL' in df.columns:
                            url_column = 'URL'
                        elif 'url' in df.columns:
                            url_column = 'url'
                        elif '링크' in df.columns:
                            url_column = '링크'
                        elif 'Link' in df.columns:
                            url_column = 'Link'
                        
                        logger.info(f"[CREATE_EXAM] 컬럼 매핑 (재시도) - CSV ID: {csv_id_column}, 제목: {title_column}, 내용: {content_column}, 정답: {answer_column}, 난이도: {difficulty_column}, 설명: {explanation_column}, Group ID: {group_id_column}, URL: {url_column}")
                        
                        questions = []
                        for _, row in df.iterrows():
                            try:
                                # 변수 초기화
                                csv_id_value = ''
                                title_value = ''
                                content_value = ''
                                answer_value = ''
                                difficulty_value = None
                                explanation_value = ''
                                group_id_value = ''
                                url_value = ''
                                
                                title1 = row[title_column]
                                
                                if creation_type == 'new':
                                    # 새 시험 생성: 엑셀 데이터를 사용해서 새로운 문제 생성 (재시도)
                                    logger.info(f"[CREATE_EXAM] [DEBUG] 새 문제 생성 시작 (재시도): '{title1}'")
                                    
                                    # 엑셀에서 모든 데이터 읽기
                                    title_value = str(title1).strip()
                                    
                                    # 문제 내용 읽기
                                    content_value = ''
                                    if content_column and content_column in row and pd.notna(row[content_column]):
                                        content_value = str(row[content_column]).strip()
                                    else:
                                        content_value = title_value  # 내용이 없으면 제목을 내용으로 사용
                                    
                                    # 정답 읽기
                                    answer_value = ''
                                    if answer_column and answer_column in row and pd.notna(row[answer_column]):
                                        answer_value = str(row[answer_column]).strip()
                                    else:
                                        answer_value = 'Y'  # 기본값
                                    
                                    # 난이도 읽기
                                    difficulty_value = None
                                    if difficulty_column and difficulty_column in row and pd.notna(row[difficulty_column]):
                                        difficulty_value = normalize_difficulty(str(row[difficulty_column]).strip())
                                    
                                    # 설명 읽기
                                    explanation_value = ''
                                    if explanation_column and explanation_column in row and pd.notna(row[explanation_column]):
                                        explanation_value = str(row[explanation_column]).strip()
                                    
                                    # Group ID 읽기
                                    group_id_value = ''
                                    if group_id_column and group_id_column in row and pd.notna(row[group_id_column]):
                                        group_id_value = str(row[group_id_column]).strip()
                                    
                                    # URL 읽기
                                    url_value = ''
                                    if url_column and url_column in row and pd.notna(row[url_column]):
                                        excel_url = str(row[url_column]).strip()
                                        if excel_url and excel_url.lower() not in ['nan', 'none', 'null', '']:
                                            url_value = excel_url
                                            logger.info(f"[CREATE_EXAM] 엑셀에서 URL 읽음 (재시도): {title1} -> {url_value}")
                                        else:
                                            logger.info(f"[CREATE_EXAM] 엑셀 URL이 비어있음 (재시도): {title1}")
                                    else:
                                        logger.info(f"[CREATE_EXAM] URL 컬럼 없음 (재시도): {title1}")
                                    
                                    # CSV ID 읽기
                                    csv_id_value = ''
                                    if csv_id_column and csv_id_column in row and pd.notna(row[csv_id_column]):
                                        csv_id_value = str(row[csv_id_column]).strip()
                                        logger.info(f"[CREATE_EXAM] 엑셀에서 CSV ID 읽음: {title1} -> {csv_id_value}")
                                    else:
                                        # CSV ID가 없으면 제목 기반으로 해시값 생성
                                        csv_id_value = f"excel_{hash(title_value) % 1000000}"
                                        logger.info(f"[CREATE_EXAM] CSV ID 컬럼 없음, 해시값 생성: {title1} -> {csv_id_value}")
                                    
                                    # 새로운 문제 생성 (다국어 필드만 사용)
                                    new_q = Question.objects.create(
                                        difficulty=difficulty_value,
                                        url=url_value,
                                        csv_id=csv_id_value,
                                        group_id=group_id_value,
                                        created_at=timezone.now(),
                                        updated_at=timezone.now()
                                    )
                                    
                                    # 다국어 필드 설정 (한국어 사용자이므로 한국어 필드에 값 설정)
                                    new_q.title_ko = title_value
                                    new_q.content_ko = content_value
                                    new_q.answer_ko = answer_value
                                    if explanation_value:
                                        new_q.explanation_ko = explanation_value
                                    new_q.save()
                                    
                                    # 번역은 나중에 배치로 처리하므로 여기서는 건너뛰기
                                    logger.info(f"[CREATE_EXAM] 새 문제 생성 완료 (재시도): {title1} (ID: {new_q.id}, URL: {url_value})")
                                    
                                    questions.append(new_q)
                                    logger.info(f"[CREATE_EXAM] 새 문제 생성 (재시도): {title1} (ID: {new_q.id}, group_id: {group_id_value}, URL: {url_value})")
                                else:
                                    # 복제/랜덤 생성: 기존 문제 참조
                                    q = Question.objects.filter(
                                        models.Q(title_ko=title1) | models.Q(title_en=title1)
                                    ).first()
                                    if q:
                                        questions.append(q)
                                        logger.info(f"[CREATE_EXAM] 기존 문제 참조 (재시도): {title1} (ID: {q.id})")
                                    else:
                                        logger.warning(f"[CREATE_EXAM] Question not found: {title1}")
                            except Exception as e:
                                logger.error(f"[CREATE_EXAM] Error finding question '{title1}': {e}")
                                continue
                        logger.info(f"[CREATE_EXAM] Found {len(questions)} questions from original file")
                    except Exception as e2:
                        logger.error(f"[CREATE_EXAM] 파일 읽기 재시도 실패: {e2}")
                        return Response({'error': f'파일 읽기 오류: {str(e2)}'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                # difficulty 필터링 추가
                if normalized_difficulty and normalized_difficulty != 'medium':  # medium은 기본값이므로 필터링하지 않음
                    questions = list(Question.objects.filter(difficulty=normalized_difficulty))
                    logger.info(f"[CREATE_EXAM] Using questions with difficulty '{normalized_difficulty}': {len(questions)}")
                else:
                    questions = list(Question.objects.all())
                    logger.info(f"[CREATE_EXAM] Using all questions: {len(questions)}")

            # 무시된 문제 제외
            if request.user.is_authenticated:
                ignored_question_ids = IgnoredQuestion.objects.filter(user=request.user).values_list('question_id', flat=True)
                questions = [q for q in questions if q.id not in ignored_question_ids]
                logger.info(f"[CREATE_EXAM] 무시된 문제 제외 후 남은 문제 수: {len(questions)}")

            # 시험 난이도에 따른 문제 필터링 적용
            exam_difficulty = serializer.validated_data.get('exam_difficulty', 5)
            if exam_difficulty and question_count and question_count > 0:
                # 시험 난이도에 따른 문제 난이도 분배 계산
                difficulty_distribution = calculate_difficulty_distribution(exam_difficulty, question_count)
                logger.info(f"[CREATE_EXAM] 시험 난이도 {exam_difficulty}에 따른 문제 난이도 분배: {difficulty_distribution}")
                
                # 난이도별 문제 분류
                easy_questions = [q for q in questions if q.difficulty and q.difficulty.lower() == 'easy']
                medium_questions = [q for q in questions if q.difficulty and q.difficulty.lower() == 'medium']
                hard_questions = [q for q in questions if q.difficulty and q.difficulty.lower() == 'hard']
                no_difficulty_questions = [q for q in questions if not q.difficulty]
                
                logger.info(f"[CREATE_EXAM] 난이도별 문제 수 - Easy: {len(easy_questions)}, Medium: {len(medium_questions)}, Hard: {len(hard_questions)}, 난이도 없음: {len(no_difficulty_questions)}")
                
                # 각 난이도별로 필요한 문제 수만큼 선택
                selected_by_difficulty = []
                
                # Easy 문제 선택
                if difficulty_distribution['easy'] > 0:
                    if len(easy_questions) >= difficulty_distribution['easy']:
                        selected_by_difficulty.extend(random.sample(easy_questions, difficulty_distribution['easy']))
                    else:
                        selected_by_difficulty.extend(easy_questions)
                        logger.warning(f"[CREATE_EXAM] Easy 문제가 부족합니다. 요청: {difficulty_distribution['easy']}, 사용 가능: {len(easy_questions)}")
                
                # Medium 문제 선택
                if difficulty_distribution['medium'] > 0:
                    if len(medium_questions) >= difficulty_distribution['medium']:
                        selected_by_difficulty.extend(random.sample(medium_questions, difficulty_distribution['medium']))
                    else:
                        selected_by_difficulty.extend(medium_questions)
                        logger.warning(f"[CREATE_EXAM] Medium 문제가 부족합니다. 요청: {difficulty_distribution['medium']}, 사용 가능: {len(medium_questions)}")
                
                # Hard 문제 선택
                if difficulty_distribution['hard'] > 0:
                    if len(hard_questions) >= difficulty_distribution['hard']:
                        selected_by_difficulty.extend(random.sample(hard_questions, difficulty_distribution['hard']))
                    else:
                        selected_by_difficulty.extend(hard_questions)
                        logger.warning(f"[CREATE_EXAM] Hard 문제가 부족합니다. 요청: {difficulty_distribution['hard']}, 사용 가능: {len(hard_questions)}")
                
                # 선택된 문제 수가 요청한 문제 수보다 적으면 난이도 없는 문제로 채우기
                if len(selected_by_difficulty) < question_count and len(no_difficulty_questions) > 0:
                    needed = question_count - len(selected_by_difficulty)
                    selected_by_difficulty.extend(random.sample(no_difficulty_questions, min(needed, len(no_difficulty_questions))))
                
                # 선택된 문제 수가 여전히 부족하면 기존 로직으로 fallback
                if len(selected_by_difficulty) >= question_count:
                    questions = selected_by_difficulty
                    logger.info(f"[CREATE_EXAM] 시험 난이도에 따라 {len(selected_by_difficulty)}개 문제 선택 완료")
                else:
                    logger.warning(f"[CREATE_EXAM] 시험 난이도에 따른 필터링으로 문제 수 부족 ({len(selected_by_difficulty)}/{question_count}), 기존 로직으로 fallback")

            # 요청한 문제 수가 사용 가능한 문제 수보다 많으면 자동으로 조정
            if question_count > 0 and len(questions) < question_count:
                original_question_count = question_count
                question_count = len(questions)
                logger.info(f"[CREATE_EXAM] 요청한 문제 수({original_question_count})가 사용 가능한 문제 수({len(questions)})보다 많아서 {question_count}개로 조정했습니다.")

            # 0개 문제인 경우 빈 리스트로 설정
            if question_count == 0:
                selected_questions = []
            # 옵션별 문제 추출 로직
            elif random_option == 'wrong_only':
                # 틀린 문제만 추출
                wrong_questions = []
                for question in questions:
                    # 해당 문제의 최근 시험 결과에서 틀린 횟수 확인
                    wrong_count = ExamResultDetail.objects.filter(
                        question=question,
                        is_correct=False
                    ).count()
                    if wrong_count > 0:
                        wrong_questions.append(question)

                # 틀린 문제 수가 요청한 문제 수보다 적으면 자동으로 조정
                if len(wrong_questions) < question_count:
                    original_question_count = question_count
                    question_count = len(wrong_questions)
                    logger.info(f"[CREATE_EXAM] 틀린 문제 수({len(wrong_questions)})가 요청한 문제 수({original_question_count})보다 적어서 {question_count}개로 조정했습니다.")

                selected_questions = random.sample(wrong_questions, question_count)

            elif random_option == 'most_wrong':
                # 많이 틀린 문제 추출 (시도 횟수 많고 오답률 높은 순)
                question_scores = []
                user = request.user

                # 익명 사용자인 경우 빈 결과 반환
                if not user.is_authenticated:
                    return Response({
                        'error': '로그인이 필요한 기능입니다.'
                    }, status=status.HTTP_401_UNAUTHORIZED)

                print(f"[most_wrong] 사용자: {user.username}")
                print(f"[most_wrong] 총 문제 수: {len(questions)}")
                user_lang = get_user_language(request)

                for question in questions:
                    # 해당 문제의 총 시험 횟수 (현재 사용자만)
                    total_attempts = ExamResultDetail.objects.filter(
                        question=question,
                        result__user=user
                    ).count()

                    if question:
                        question_title = get_localized_field(question, 'title', user_lang, '제목 없음')
                        print(f"[most_wrong] 문제 {question.id} ({question_title}): 시도 횟수 = {total_attempts}")
                    else:
                        print(f"[most_wrong] 문제 {question.id} (제목 없음): 시도 횟수 = {total_attempts}")

                    if total_attempts > 0:
                        # 틀린 횟수 (현재 사용자만)
                        wrong_count = ExamResultDetail.objects.filter(
                            question=question,
                            result__user=user,
                            is_correct=False
                        ).count()
                        # 오답률 계산
                        wrong_rate = wrong_count / total_attempts
                        # 점수 계산: 시도 횟수 * 오답률 (시도 횟수가 많고 오답률이 높을수록 높은 점수)
                        score = total_attempts * wrong_rate
                        question_scores.append((question, score, total_attempts, wrong_count))
                        print(f"[most_wrong] 문제 {question.id} 추가됨: 점수={score}, 시도={total_attempts}, 틀린={wrong_count}")
                    else:
                        print(f"[most_wrong] 문제 {question.id} 제외됨: 시도 횟수 0")
                    # 시도 횟수가 0인 문제는 제외

                # 점수 높은 순으로 정렬 (시도 횟수 많고 오답률 높은 순)
                question_scores.sort(key=lambda x: x[1], reverse=True)

                # 상위 문제들 중에서 요청한 수만큼 선택
                available_questions = [q for q, _, _, _ in question_scores]
                
                # 시도 기록이 있는 문제가 없는 경우 일반 랜덤 선택으로 fallback
                if len(available_questions) == 0:
                    logger.info(f"[CREATE_EXAM] 시도 기록이 있는 문제가 없어서 일반 랜덤 선택으로 fallback합니다.")
                    selected_questions = random.sample(list(questions), question_count)
                else:
                    # 시도 기록이 있는 문제 수가 요청한 문제 수보다 적으면 자동으로 조정
                    if len(available_questions) < question_count:
                        original_question_count = question_count
                        question_count = len(available_questions)
                        logger.info(f"[CREATE_EXAM] 시도 기록이 있는 문제 수({len(available_questions)})가 요청한 문제 수({original_question_count})보다 적어서 {question_count}개로 조정했습니다.")

                    selected_questions = available_questions[:question_count]

            else:  # random (그냥 랜덤)
                # 기존 로직과 동일하게 랜덤 추출
                selected_questions = random.sample(list(questions), question_count)

        if not specific_questions and not file_name and question_count is None:
            return Response({'error': '문제 수 또는 특정 문제 목록이 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # selected_questions가 정의되지 않은 경우 처리
        if 'selected_questions' not in locals():
            logger.error("[CREATE_EXAM] selected_questions가 정의되지 않았습니다.")
            return Response({'error': '문제 선택에 실패했습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        print(f"[DEBUG] selected_questions 길이: {len(selected_questions) if 'selected_questions' in locals() else '정의되지 않음'}")

        # 같은 이름의 시험이 있으면 삭제 (덮어쓰기)
        # 단, "Today's Quizzes" 시험은 기존 시험을 업데이트
        existing_exam = Exam.objects.filter(
            Q(title_ko=title) | Q(title_en=title)
        ).first()
        if existing_exam and not title.startswith("Today's Quizzes"):
            # 기존 시험과 관련된 모든 데이터 삭제
            # 1. 시험 결과 상세 삭제
            exam_results = ExamResult.objects.filter(exam=existing_exam)
            for result in exam_results:
                ExamResultDetail.objects.filter(result=result).delete()

            # 2. 시험 결과 삭제
            exam_results.delete()

            # 3. 시험 문제 관계 삭제
            ExamQuestion.objects.filter(exam=existing_exam).delete()

            # 4. 기존 시험 삭제
            existing_exam.delete()
            print(f"기존 시험 '{title}' 삭제됨 (덮어쓰기)")
        elif existing_exam and title.startswith("Today's Quizzes"):
            print(f"Today's Quizzes 시험 업데이트: '{title}'")
            # 기존 시험을 업데이트 (Study Title/Goal과 동일한 다국어 처리 방식)
            exam = existing_exam
            # 다국어 처리: 사용자 언어에 맞는 필드에 저장 (Study Title/Goal과 동일한 방식)
            from ..utils.multilingual_utils import get_user_language
            user_language = get_user_language(request.user)
            if hasattr(exam, 'title_ko'):
                setattr(exam, f'title_{user_language}', title)
            if hasattr(exam, 'description_ko'):
                setattr(exam, f'description_{user_language}', description)
            exam.total_questions = question_count
            exam.is_original = is_original
            exam.is_public = is_public
            exam.file_name = file_name
            exam.created_by = request.user if request.user.is_authenticated else None
            
            # 다국어 콘텐츠 자동 처리 (Study Title/Goal과 동일한 방식)
            try:
                from ..utils.multilingual_utils import MultilingualContentManager, get_user_language
                # 먼저 현재 언어의 필드에 사용자 입력값 저장
                user_language = get_user_language(request.user)
                if hasattr(exam, 'title_ko'):
                    setattr(exam, f'title_{user_language}', title)
                if hasattr(exam, 'description_ko'):
                    setattr(exam, f'description_{user_language}', description)
                
                # 저장 후 다국어 처리
                exam.save()
                manager = MultilingualContentManager(exam, request.user, ['title', 'description'])
                manager.handle_multilingual_update()
                logger.info(f"[CREATE_EXAM] 기존 시험 다국어 콘텐츠 처리 완료: {exam.id}")
            except Exception as e:
                logger.error(f"[CREATE_EXAM] 기존 시험 다국어 콘텐츠 처리 실패: {e}")
                # 다국어 처리 실패해도 시험 업데이트는 계속 진행
            
            # 기존 문제 관계 삭제 후 새로 추가
            ExamQuestion.objects.filter(exam=exam).delete()
            
            # 시험에 문제 추가
            question_groups = request.data.get('question_groups', [])
            for i, question in enumerate(selected_questions):
                # group_id가 제공된 경우 해당 문제의 group_id 업데이트
                if i < len(question_groups) and question_groups[i]:
                    question.group_id = question_groups[i]
                    question.save()

                ExamQuestion.objects.create(
                    exam=exam,
                    question=question,
                    order=i + 1
                )
            
            # 모든 문제 추가 완료 후 배치 번역 처리
            if selected_questions:
                try:
                    from ..utils.multilingual_utils import process_large_question_batch
                    logger.info(f"[CREATE_EXAM] 기존 시험 업데이트 - {len(selected_questions)}개 문제 배치 번역 시작")
                    
                    # 배치 번역 수행
                    translation_result = process_large_question_batch(selected_questions, request.user)
                    
                    logger.info(f"[CREATE_EXAM] 기존 시험 업데이트 - 배치 번역 완료: {translation_result['successful']}/{translation_result['total_translations']} 성공")
                    
                    if translation_result['errors']:
                        logger.warning(f"[CREATE_EXAM] 기존 시험 업데이트 - 번역 중 일부 오류 발생: {len(translation_result['errors'])}개")
                        for error in translation_result['errors'][:5]:  # 처음 5개만 로그
                            logger.warning(f"[CREATE_EXAM] 번역 오류: {error}")
                            
                except Exception as e:
                    logger.error(f"[CREATE_EXAM] 기존 시험 업데이트 - 배치 번역 처리 실패: {e}")
                    # 번역 실패해도 시험 업데이트는 계속 진행
            

            
            # 캐시 무효화 강화
            try:
                # 모든 사용자의 캐시 무효화
                cache.delete_pattern("exams_*")
                logger.info("[CREATE_EXAM] 모든 시험 캐시 무효화 완료")
            except AttributeError:
                # Redis가 아닌 경우 개별 키 삭제
                cache.delete("exams_anonymous")
                if request.user.is_authenticated:
                    cache.delete(f"exams_{request.user.id}")
                logger.info("[CREATE_EXAM] 개별 시험 캐시 무효화 완료")
            except Exception as e:
                logger.error(f"[CREATE_EXAM] 캐시 무효화 실패: {e}")
            
            exam_serializer = ExamSerializer(exam)
            return Response(exam_serializer.data)

        # 시험 생성 (Study Title/Goal과 동일한 다국어 처리 방식)
        # 사용자는 title, description 필드에만 입력
        # 백엔드에서 자동으로 사용자 언어에 맞는 필드에 저장하고 번역 수행
        from ..utils.multilingual_utils import get_user_language
        user_language = get_user_language(request.user)
        
        force_answer = serializer.validated_data.get('force_answer', False)
        voice_mode_enabled = serializer.validated_data.get('voice_mode_enabled', False)
        ai_mock_interview = serializer.validated_data.get('ai_mock_interview', False)
        
        # AI 생성 문제들 처리
        generated_questions = request.data.get('generated_questions', [])
        logger.info(f"[CREATE_EXAM] AI 생성 문제 수: {len(generated_questions)}")
        
        # 시험 난이도 가져오기 (기본값 5)
        exam_difficulty = serializer.validated_data.get('exam_difficulty', 5)
        logger.info(f"[CREATE_EXAM] 시험 난이도: {exam_difficulty}")
        
        exam = Exam.objects.create(
            total_questions=question_count,
            is_original=is_original,
            is_public=is_public,
            force_answer=force_answer,
            voice_mode_enabled=voice_mode_enabled,
            ai_mock_interview=ai_mock_interview,
            file_name=file_name,
            created_by=request.user if request.user.is_authenticated else None,
            created_language=user_language,  # 명시적으로 설정
            exam_difficulty=exam_difficulty  # 시험 난이도 저장
        )
        
        # 다국어 콘텐츠 직접 처리 (Study Title/Goal과 동일한 방식)
        try:
            # 먼저 현재 언어의 필드에 사용자 입력값 저장
            if hasattr(exam, 'title_ko'):
                setattr(exam, f'title_{user_language}', title)
            if hasattr(exam, 'description_ko'):
                setattr(exam, f'description_{user_language}', description)
            
            # 기본 언어(BASE_LANGUAGE)가 아닌 언어로 입력한 경우에만 번역
            from quiz.utils.multilingual_utils import BASE_LANGUAGE, LANGUAGE_EN, LANGUAGE_KO
            # 영어 사용자가 기본 언어로 입력한 경우 → 번역하지 않음 (이미 기본 언어)
            if user_language != BASE_LANGUAGE:
                # 기본 언어가 아닌 언어로 입력한 경우 → 기본 언어로 번역
                fields_to_translate = ['title', 'description']
                
                for field_name in fields_to_translate:
                    # 현재 언어 필드
                    current_field = f"{field_name}_{user_language}"
                    # 기본 언어 필드 (번역 대상)
                    base_field = f"{field_name}_{BASE_LANGUAGE}"
                    
                    # 현재 언어 내용 가져오기
                    current_content = getattr(exam, current_field, None)
                    
                    if current_content and current_content.strip():
                        # 현재 언어 → 기본 언어 번역 수행
                        try:
                            translated_text = _translate_content(
                                current_content, 
                                user_language, 
                                BASE_LANGUAGE
                            )
                            
                            if translated_text:
                                # 번역된 텍스트를 기본 언어 필드에 저장
                                setattr(exam, base_field, translated_text)
                                logger.info(f"[CREATE_EXAM] {field_name} 번역 완료: en → ko")
                            else:
                                logger.warning(f"[CREATE_EXAM] {field_name} 번역 실패: en → ko")
                        except Exception as e:
                            logger.error(f"[CREATE_EXAM] {field_name} 번역 중 오류: {e}")
                    else:
                        logger.info(f"[CREATE_EXAM] {field_name} 건너뜀: {en_field}에 콘텐츠가 없음")
                
                # 번역된 내용이 있으면 저장
                exam.save()
                logger.info(f"[CREATE_EXAM] 다국어 콘텐츠 처리 완료: {exam.id}")
            else:
                # 한국어 사용자는 기존 MultilingualContentManager 사용
                from ..utils.multilingual_utils import MultilingualContentManager
                exam.save()
                manager = MultilingualContentManager(exam, request.user, ['title', 'description'])
                manager.handle_multilingual_update()
                logger.info(f"[CREATE_EXAM] 다국어 콘텐츠 처리 완료: {exam.id}")
                
        except Exception as e:
            logger.error(f"[CREATE_EXAM] 다국어 콘텐츠 처리 실패: {e}")
            # 다국어 처리 실패해도 시험 생성은 계속 진행
        
        # tags 필드 처리 (ManyToManyField는 별도로 처리해야 함)
        if 'tags' in request.data:
            tag_ids = request.data.get('tags', [])
            logger.info(f"[CREATE_EXAM] 태그 설정 - exam_id: {exam.id}, tag_ids: {tag_ids}")
            
            # 유효한 태그 ID만 필터링
            valid_tag_ids = []
            for tag_id in tag_ids:
                try:
                    from ..models import Tag
                    tag = Tag.objects.get(id=tag_id)
                    valid_tag_ids.append(tag_id)
                    tag_name = get_localized_field(tag, 'name', user_language, '')
                    logger.info(f"[CREATE_EXAM] 유효한 태그 ID: {tag_id} ({tag_name})")
                except Tag.DoesNotExist:
                    logger.warning(f"[CREATE_EXAM] 존재하지 않는 태그 ID: {tag_id}")
            
            # 태그는 반드시 1개 이상 필요
            if not valid_tag_ids:
                exam.delete()  # 생성된 시험 삭제
                return Response(
                    {'error': '시험에는 반드시 1개 이상의 태그가 필요합니다.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 태그 설정
            exam.tags.set(valid_tag_ids)
            logger.info(f"[CREATE_EXAM] 시험 태그 설정 완료 - 총 {len(valid_tag_ids)}개 태그")
        else:
            # 태그가 제공되지 않은 경우
            exam.delete()  # 생성된 시험 삭제
            return Response(
                {'error': '시험에는 반드시 1개 이상의 태그가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # AI 생성 문제들을 Question 객체로 생성
        ai_questions = []
        user_lang = get_user_language(request)
        if generated_questions:
            try:
                logger.info(f"[CREATE_EXAM] AI 생성 문제들을 Question 객체로 변환 시작")
                
                # 시험 난이도에 따른 문제 난이도 분배 계산
                difficulty_distribution = calculate_difficulty_distribution(exam_difficulty, len(generated_questions))
                logger.info(f"[CREATE_EXAM] 시험 난이도 {exam_difficulty}에 따른 문제 난이도 분배: {difficulty_distribution}")
                
                # 난이도별 문제 리스트 생성 (easy, medium, hard 순서)
                difficulty_order = []
                for difficulty, count in difficulty_distribution.items():
                    difficulty_order.extend([difficulty.capitalize()] * count)
                
                # 문제 수가 맞지 않으면 조정 (나머지는 medium으로)
                while len(difficulty_order) < len(generated_questions):
                    difficulty_order.append('Medium')
                difficulty_order = difficulty_order[:len(generated_questions)]
                
                # 랜덤하게 섞기 (선형 분배가 아닌 경우를 위해)
                random.shuffle(difficulty_order)
                
                for i, gen_question in enumerate(generated_questions):
                    # 시험 난이도에 따라 할당된 난이도 사용
                    assigned_difficulty = difficulty_order[i] if i < len(difficulty_order) else 'Medium'
                    
                    # Question 객체 생성
                    question = Question.objects.create(
                        title_ko=gen_question.get('title', f"AI 생성 문제 {i+1}"),
                        content_ko=gen_question.get('content', ''),
                        answer_ko=gen_question.get('answer', ''),
                        difficulty=assigned_difficulty,  # 시험 난이도에 따라 할당된 난이도 사용
                        created_by=request.user if request.user.is_authenticated else None,
                        is_original=False  # AI 생성 문제는 원본이 아님
                    )
                    
                    # 영어 번역도 생성 (간단한 번역)
                    if gen_question.get('title'):
                        question.title_en = f"AI Generated Question {i+1}: {gen_question.get('title', '')}"
                    if gen_question.get('content'):
                        question.content_en = gen_question.get('content', '')
                    if gen_question.get('answer'):
                        question.answer_en = gen_question.get('answer', '')
                    
                    question.save()
                    ai_questions.append(question)
                    
                    question_title = get_localized_field(question, 'title', user_lang, '')
                    logger.info(f"[CREATE_EXAM] AI 문제 생성 완료: {question.id} - {question_title} (난이도: {assigned_difficulty})")
                
                logger.info(f"[CREATE_EXAM] 총 {len(ai_questions)}개의 AI 문제 생성 완료")
                
                # AI 생성 문제들을 selected_questions에 추가
                selected_questions.extend(ai_questions)
                
            except Exception as e:
                logger.error(f"[CREATE_EXAM] AI 문제 생성 실패: {e}")
                # AI 문제 생성 실패 시에도 시험 생성은 계속 진행

        # 시험에 문제 추가
        question_groups = request.data.get('question_groups', [])
        for i, question in enumerate(selected_questions):
            # group_id가 제공된 경우 해당 문제의 group_id 업데이트
            if i < len(question_groups) and question_groups[i]:
                question.group_id = question_groups[i]
                question.save()

            ExamQuestion.objects.create(
                exam=exam,
                question=question,
                order=i + 1
            )
        
        # 시험 내용 분석하여 연령 등급 추정
        # 주의: create_exam은 사용자가 이미 문제를 선택한 경우이므로 난이도 조정은 하지 않음
        try:
            from ..utils.exam_utils import estimate_exam_age_rating
            # 시험에 포함된 모든 문제 가져오기
            exam_questions = [eq.question for eq in exam.examquestion_set.select_related('question').all()]
            estimated_rating = estimate_exam_age_rating(exam, exam_questions)
            exam.age_rating = estimated_rating
            exam.save(update_fields=['age_rating'])
            logger.info(f"[CREATE_EXAM] 시험 연령 등급 추정 완료: {estimated_rating} (시험 ID: {exam.id})")
        except Exception as e:
            logger.error(f"[CREATE_EXAM] 시험 연령 등급 추정 실패: {e}")
            # 추정 실패 시 기본값 17+ 유지
        
        # 모든 문제 추가 완료 후 제목만 배치 번역 처리
        if questions and not skip_batch_translation:
            try:
                from ..utils.multilingual_utils import batch_translate_question_titles
                logger.info(f"[CREATE_EXAM] {len(questions)}개 문제 제목 배치 번역 시작")
                
                # 제목만 배치 번역 수행
                translation_result = batch_translate_question_titles(questions, request.user)
                
                logger.info(f"[CREATE_EXAM] 제목 배치 번역 완료: {translation_result['translated']}/{translation_result['total']} 성공")
                
                if translation_result['errors']:
                    logger.warning(f"[CREATE_EXAM] 번역 중 일부 오류 발생: {len(translation_result['errors'])}개")
                    for error in translation_result['errors'][:5]:  # 처음 5개만 로그
                        logger.warning(f"[CREATE_EXAM] 번역 오류: {error}")
                        
            except Exception as e:
                logger.error(f"[CREATE_EXAM] 제목 배치 번역 처리 실패: {e}")
                # 번역 실패해도 시험 생성은 계속 진행
        # 시험 생성자 자동 구독
        if request.user.is_authenticated:
            try:
                from ..models import ExamSubscription
                # 이미 구독되어 있는지 확인
                subscription, created = ExamSubscription.objects.get_or_create(
                    user=request.user,
                    exam=exam,
                    defaults={'is_active': True}
                )
                if created:
                    exam_title = get_localized_field(exam, 'title', user_language, 'Unknown')
                    logger.info(f"[CREATE_EXAM] 시험 생성자 자동 구독 생성: 사용자 {request.user.username}, 시험 {exam_title}")
                else:
                    # 기존 구독이 비활성화되어 있다면 활성화
                    if not subscription.is_active:
                        subscription.is_active = True
                        subscription.save()
                        exam_title = get_localized_field(exam, 'title', get_user_language(request), 'Unknown')
                        logger.info(f"[CREATE_EXAM] 기존 구독 활성화: 사용자 {request.user.username}, 시험 {exam_title}")
            except Exception as e:
                logger.error(f"[CREATE_EXAM] 자동 구독 생성 실패: {e}")
        
        # exam 객체가 정의되지 않은 경우 처리
        if 'exam' not in locals():
            logger.error("[CREATE_EXAM] exam 객체가 정의되지 않았습니다.")
            return Response({'error': '시험 생성에 실패했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        exam_serializer = ExamSerializer(exam)
        logger.info(f"[CREATE_EXAM] 시험 생성 완료: {exam.id}")
        
        # 캐시 무효화 강화 (ExamCacheManager 사용)
        try:
            from ..utils.cache_utils import ExamCacheManager
            # 모든 사용자의 시험 관련 캐시 무효화
            ExamCacheManager.invalidate_all_exam_cache()
            logger.info("[CREATE_EXAM] ExamCacheManager를 통한 최종 캐시 무효화 완료")
        except Exception as e:
            logger.error(f"[CREATE_EXAM] ExamCacheManager 최종 캐시 무효화 실패: {e}")
            # 폴백: 기존 방식으로 캐시 무효화
            try:
                if hasattr(cache, 'delete_pattern'):
                    cache.delete_pattern("exams_*")
                    logger.info("[CREATE_EXAM] Redis 패턴 기반 폴백 캐시 무효화 완료")
                else:
                    cache.delete("exams_anonymous")
                    if request.user.is_authenticated:
                        cache.delete(f"exams_{request.user.id}")
                    logger.info("[CREATE_EXAM] 개별 키 기반 폴백 캐시 무효화 완료")
            except Exception as e2:
                logger.error(f"[CREATE_EXAM] 폴백 캐시 무효화도 실패: {e2}")
        
        return Response(exam_serializer.data, status=status.HTTP_201_CREATED)
    else:
        logger.error(f"[CREATE_EXAM] Serializer 검증 실패: {serializer.errors}")
        return Response({'error': '입력 데이터가 유효하지 않습니다.', 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_exam(request, exam_id):
    """특정 시험의 정보를 조회합니다."""
    import time
    from django.db import connection
    
    start_time = time.time()
    total_queries_before = len(connection.queries)
    
    logger.info(f"========== GET_EXAM 시작 ==========")
    logger.info(f"[GET_EXAM] 요청 정보 - exam_id: {exam_id}, user: {request.user}, is_authenticated: {request.user.is_authenticated}")
    logger.info(f"[GET_EXAM] GET 파라미터: {dict(request.GET)}")
    logger.info(f"[GET_EXAM] Headers: Accept-Language={request.headers.get('Accept-Language')}")
    
    try:
        # 쿼리 최적화: select_related와 prefetch_related 추가
        query_start = time.time()
        query_queries_before = len(connection.queries)
        
        exam = Exam.objects.select_related(
            'created_by', 'original_exam'
        ).prefetch_related(
            'questions', 'tags', 'tags__categories'
        ).get(id=exam_id)
        
        query_time = time.time() - query_start
        query_queries_after = len(connection.queries)
        logger.info(f"[GET_EXAM] DB 조회 완료 - {query_queries_after - query_queries_before}개 쿼리, {query_time:.3f}초")
        user_lang = get_user_language(request)
        exam_title = get_localized_field(exam, 'title', user_lang, 'Unknown')
        logger.info(f"[GET_EXAM] DB 조회 성공 - exam.title: {exam_title}, exam.is_public: {exam.is_public}, exam.created_by: {exam.created_by}")

        # 시험 접근 권한 확인
        user = request.user
        logger.info(f"[GET_EXAM] 권한 확인 시작 - user: {user}, is_authenticated: {user.is_authenticated}")
        logger.info(f"[GET_EXAM] 시험 정보 - exam_id: {exam_id}, exam.is_public: {exam.is_public}, exam.created_by: {exam.created_by}")
        if user.is_authenticated:
            # admin_role 사용자는 모든 시험에 접근 가능
            if hasattr(user, 'profile') and hasattr(user.profile, 'role') and user.profile.role == 'admin_role':
                pass  # 접근 허용
            else:
                # 일반 사용자는 다음 조건 중 하나를 만족해야 함:
                # 1. 시험이 공개되어 있거나
                # 2. 사용자가 해당 시험의 생성자이거나
                # 3. 사용자가 해당 시험이 포함된 스터디의 멤버이거나
                # 4. 사용자가 해당 시험을 이미 풀어본 적이 있거나

                # 시험이 공개되어 있는지 확인
                if exam.is_public:
                    pass  # 접근 허용
                else:
                    # 사용자가 해당 시험의 생성자인지 확인
                    is_creator = exam.created_by == user if exam.created_by else False

                    # 사용자가 해당 시험이 포함된 스터디의 멤버인지 확인
                    study_membership = Member.objects.filter(
                        user=user,
                        study__tasks__exam=exam,
                        is_active=True
                    ).exists()

                    # 사용자가 해당 시험을 이미 풀어본 적이 있는지 확인
                    has_taken_exam = ExamResult.objects.filter(
                        user=user,
                        exam=exam
                    ).exists()

                    if not is_creator and not study_membership and not has_taken_exam:
                        return Response({'error': '이 시험에 접근할 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
        else:
            # 익명 사용자가 비공개 시험에 접근 시도하는 경우 로그인 필요
            logger.info(f"[GET_EXAM] 익명 사용자 접근 시도 - exam.is_public: {exam.is_public}, exam_id: {exam_id}")
            if not exam.is_public:
                logger.warning(f"[GET_EXAM] 익명 사용자가 비공개 시험에 접근 시도 - exam_id: {exam_id}")
                return Response({
                    'error': '이 시험에 접근하려면 로그인이 필요합니다.',
                    'requires_login': True,
                    'exam_id': str(exam.id)
                }, status=status.HTTP_401_UNAUTHORIZED)
            else:
                logger.info(f"[GET_EXAM] ✅ 익명 사용자가 공개 시험에 접근 허용 - exam_id: {exam_id}, exam.is_public: {exam.is_public}")

        # lang 파라미터 우선 사용 (프론트엔드에서 명시적으로 전달한 언어)
        # 없으면 사용자 프로필 언어 사용
        from quiz.utils.multilingual_utils import BASE_LANGUAGE, SUPPORTED_LANGUAGES, LANGUAGE_EN
        user_language = request.GET.get('lang')
        logger.info(f"[GET_EXAM] get_exam - lang 파라미터: {user_language}")
        
        # lang 파라미터가 없으면 사용자 프로필 언어 확인
        if not user_language and request.user.is_authenticated:
            if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'language'):
                user_language = request.user.profile.language
                logger.info(f"[GET_EXAM] get_exam - 프로필 언어 사용: {user_language}")
            elif hasattr(request.user, 'userprofile') and hasattr(request.user.userprofile, 'language'):
                user_language = request.user.userprofile.language
                logger.info(f"[GET_EXAM] get_exam - userprofile 언어 사용: {user_language}")
        
        # lang 파라미터도 없고 프로필 언어도 없으면 Accept-Language 헤더 확인
        if not user_language:
            accept_language = request.headers.get('Accept-Language', 'en')
            user_language = accept_language if accept_language in SUPPORTED_LANGUAGES else LANGUAGE_EN
            logger.info(f"[GET_EXAM] get_exam - Accept-Language 헤더 사용: {accept_language}, user_language: {user_language}")
        
        # lang 파라미터도 없고 프로필 언어도 없으면 기본값 사용
        if not user_language:
            user_language = BASE_LANGUAGE
            logger.info(f"[GET_EXAM] get_exam - 기본값 사용: {user_language}")
        
        logger.info(f"[GET_EXAM] get_exam - 최종 user_language: {user_language}")
        
        # request 객체에 언어 정보 추가
        request.user_language = user_language
        
        # select 파라미터에 따라 시리얼라이저 선택
        select_fields = request.GET.get('select', '').split(',') if request.GET.get('select') else []
        logger.info(f"[GET_EXAM] select 파라미터 - select_fields: {select_fields}")
        
        # 사용자별 통계를 미리 계산 (N+1 쿼리 방지)
        user_correct_questions = None
        user_accuracy_percentage = None
        
        if request.user.is_authenticated:
            stats_start = time.time()
            stats_queries_before = len(connection.queries)
            
            # 복사된 시험인 경우 원본 시험 ID 사용
            target_exam = exam.original_exam if not exam.is_original and exam.original_exam else exam
            target_exam_id = target_exam.id
            
            # 정답 시도 수 계산
            from ..models import ExamResultDetail
            correct_count = ExamResultDetail.objects.filter(
                result__exam_id=target_exam_id,
                result__user=request.user,
                is_correct=True
            ).count()
            
            # 전체 시도 수 계산
            total_count = ExamResultDetail.objects.filter(
                result__exam_id=target_exam_id,
                result__user=request.user
            ).count()
            
            user_correct_questions = correct_count
            if total_count > 0:
                user_accuracy_percentage = (correct_count / total_count) * 100
            else:
                user_accuracy_percentage = None
            
            stats_time = time.time() - stats_start
            stats_queries_after = len(connection.queries)
            logger.info(f"[GET_EXAM] 통계 계산 완료 - {stats_queries_after - stats_queries_before}개 쿼리, {stats_time:.3f}초, correct: {user_correct_questions}, accuracy: {user_accuracy_percentage}")
        
        # 시리얼라이저 context에 user_language 및 통계 전달
        serializer_context = {
            'request': request,
            'user_language': user_language,
            'user_correct_questions': user_correct_questions,
            'user_accuracy_percentage': user_accuracy_percentage
        }
        
        if select_fields and 'questions' not in select_fields and 'content' not in select_fields and 'answer' not in select_fields and 'explanation' not in select_fields:
            # 문제 상세 내용이 필요하지 않으면 ExamDetailSerializer 사용
            from ..serializers import ExamDetailSerializer
            logger.info(f"[GET_EXAM] ExamDetailSerializer 사용")
            serializer = ExamDetailSerializer(exam, context=serializer_context)
        else:
            # 문제 상세 내용이 필요하면 ExamSerializer 사용
            logger.info(f"[GET_EXAM] ExamSerializer 사용")
            serializer = ExamSerializer(exam, context=serializer_context)
        
        # 시리얼라이저 직렬화 성능 측정
        serializer_start = time.time()
        serializer_queries_before = len(connection.queries)
        
        logger.info(f"[GET_EXAM] 시리얼라이저 데이터 변환 시작")
        data = serializer.data
        
        serializer_time = time.time() - serializer_start
        serializer_queries_after = len(connection.queries)
        serializer_query_count = serializer_queries_after - serializer_queries_before
        
        logger.info(f"[GET_EXAM] 시리얼라이저 데이터 변환 완료 - {serializer_query_count}개 쿼리, {serializer_time:.3f}초, 데이터 키: {list(data.keys())}")
        
        # 디버깅을 위한 로그 추가
        logger.info(f"Exam {exam_id} 조회 - created_by: {exam.created_by}, user: {request.user}")
        logger.info(f"Serialized data created_by: {data.get('created_by')}")
        
        # 리소스별 권한 정보 추가
        if request.user.is_authenticated:
            logger.info(f"[GET_EXAM] 권한 정보 추가 시작")
            from ..utils.permissions import get_resource_specific_permissions
            resource_permissions = get_resource_specific_permissions(request.user, exam)
            data['user_permissions'] = resource_permissions
            logger.info(f"[GET_EXAM] User permissions: {resource_permissions}")
        
        total_time = time.time() - start_time
        total_queries_after = len(connection.queries)
        total_query_count = total_queries_after - total_queries_before
        
        logger.info(f"[GET_EXAM] 응답 반환 - 데이터 크기: {len(str(data))} bytes")
        logger.info(f"[GET_EXAM] 성능 요약 - 총 시간: {total_time:.3f}초, 총 쿼리: {total_query_count}개")
        logger.info(f"========== GET_EXAM 완료 ==========")
        return Response(data)
    except Exam.DoesNotExist:
        logger.error(f"[GET_EXAM] 시험을 찾을 수 없음 - exam_id: {exam_id}")
        return Response({'error': '시험을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"[GET_EXAM] 예외 발생 - exam_id: {exam_id}, 에러: {str(e)}", exc_info=True)
        return Response({'error': f'시험 조회 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_exam_questions(request, exam_id):
    """특정 시험의 문제 목록을 조회합니다."""
    import time
    import logging
    from django.db import connection
    # get_localized_field와 SUPPORTED_LANGUAGES를 명시적으로 import하여 UnboundLocalError 방지
    from ..utils.multilingual_utils import (
        get_localized_field as get_localized_field_func,
        SUPPORTED_LANGUAGES
    )
    
    logger = logging.getLogger(__name__)
    
    start_time = time.time()
    total_queries_before = len(connection.queries)
    
    # 디버깅: 함수 호출 추적
    user_language = get_user_language(request) if request else 'unknown'
    logger.info(f"========== GET_EXAM_QUESTIONS 시작 ==========")
    logger.info(f"[GET_EXAM_QUESTIONS] API 호출 - 시험 ID: {exam_id}, 사용자: {request.user.username if request.user.is_authenticated else 'anonymous'}, 언어: {user_language}")
    
    try:
        # 쿼리 최적화: select_related 추가
        query_start = time.time()
        query_queries_before = len(connection.queries)
        
        exam = Exam.objects.select_related('created_by', 'original_exam').get(id=exam_id)
        
        query_time = time.time() - query_start
        query_queries_after = len(connection.queries)
        logger.info(f"[GET_EXAM_QUESTIONS] DB 조회 완료 - {query_queries_after - query_queries_before}개 쿼리, {query_time:.3f}초")
        logger.info(f"[GET_EXAM_QUESTIONS] 시험 정보 - exam_id: {exam_id}, is_public: {exam.is_public}")

        # 시험 접근 권한 확인
        user = request.user
        if user.is_authenticated:
            # admin_role 사용자는 모든 시험에 접근 가능
            if hasattr(user, 'profile') and hasattr(user.profile, 'role') and user.profile.role == 'admin_role':
                pass  # 접근 허용
            else:
                # 일반 사용자는 다음 조건 중 하나를 만족해야 함:
                # 1. 시험이 공개되어 있거나
                # 2. 사용자가 해당 시험의 생성자이거나
                # 3. 사용자가 해당 시험이 포함된 스터디의 멤버이거나
                # 4. 사용자가 해당 시험을 이미 풀어본 적이 있거나

                # 시험이 공개되어 있는지 확인
                if exam.is_public:
                    pass  # 접근 허용
                else:
                    # 사용자가 해당 시험의 생성자인지 확인
                    is_creator = exam.created_by == user if exam.created_by else False

                    # 사용자가 해당 시험이 포함된 스터디의 멤버인지 확인
                    study_membership = Member.objects.filter(
                        user=user,
                        study__tasks__exam=exam,
                        is_active=True
                    ).exists()

                    # 사용자가 해당 시험을 이미 풀어본 적이 있는지 확인
                    has_taken_exam = ExamResult.objects.filter(
                        user=user,
                        exam=exam
                    ).exists()

                    if not is_creator and not study_membership and not has_taken_exam:
                        return Response({'error': '이 시험에 접근할 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
        else:
            # 익명 사용자는 공개 시험만 접근 가능
            if not exam.is_public:
                logger.warning(f"[GET_EXAM_QUESTIONS] 익명 사용자가 비공개 시험에 접근 시도 (exam_id: {exam_id}) - 401 UNAUTHORIZED")
                return Response({
                    'error': '이 시험에 접근하려면 로그인이 필요합니다.',
                    'requires_login': True,
                    'exam_id': str(exam.id)
                }, status=status.HTTP_401_UNAUTHORIZED)
            else:
                logger.info(f"[GET_EXAM_QUESTIONS] 익명 사용자 공개 시험 접근 허용 (exam_id: {exam_id})")

        # favorite 시험인 경우 모든 문제를 반환, 그렇지 않으면 현재 시험의 문제들만 반환
        user_lang = get_user_language(request)
        exam_title = get_localized_field_func(exam, 'title', user_lang, '')
        is_favorite_exam = exam_title.endswith("'s favorite") if exam_title else False
        
        # 문제 조회 최적화
        questions_start = time.time()
        questions_queries_before = len(connection.queries)
        
        if is_favorite_exam:
            # favorite 시험의 경우 모든 문제를 반환
            questions = Question.objects.select_related('created_by').all()
        else:
            # 일반 시험의 경우 현재 시험의 문제들만 반환 (prefetch_related로 최적화)
            questions = Question.objects.select_related('created_by').filter(
                examquestion__exam=exam
            ).distinct().prefetch_related('examquestion_set')
        
        questions_time = time.time() - questions_start
        questions_queries_after = len(connection.queries)
        logger.info(f"[GET_EXAM_QUESTIONS] 문제 조회 완료 - {questions_queries_after - questions_queries_before}개 쿼리, {questions_time:.3f}초, 문제 수: {questions.count()}")
        
        # 태그 필터링은 시험 레벨에서 이루어지므로 여기서는 제거
        # Question 모델에는 tags 필드가 없고, 태그는 Exam 모델에서 관리됨
        
        # select 파라미터에 따라 시리얼라이저 선택
        select_fields = request.GET.get('select', '').split(',') if request.GET.get('select') else []
        
        # 사용자가 로그인한 경우 favorite과 ignored 상태 추가
        favorite_ignored_start = time.time()
        favorite_ignored_queries_before = len(connection.queries)
        
        if user.is_authenticated:
            # favorite 문제들 조회 (최적화: 한 번에 조회)
            favorite_question_ids = set()
            try:
                favorite_exams = Exam.objects.filter(
                    title_ko=f"{user.username}'s favorite",
                    is_original=True
                ).order_by('created_at')
                
                if favorite_exams.exists():
                    favorite_exam = favorite_exams.first()
                    favorite_question_ids = set(
                        ExamQuestion.objects.filter(exam=favorite_exam)
                        .values_list('question_id', flat=True)
                    )
            except Exception:
                pass
            
            # ignored 문제들 조회 (한 번에 조회)
            ignored_question_ids = set(
                IgnoredQuestion.objects.filter(user=user)
                .values_list('question_id', flat=True)
            )
        else:
            favorite_question_ids = set()
            ignored_question_ids = set()
        
        favorite_ignored_time = time.time() - favorite_ignored_start
        favorite_ignored_queries_after = len(connection.queries)
        logger.info(f"[GET_EXAM_QUESTIONS] favorite/ignored 조회 완료 - {favorite_ignored_queries_after - favorite_ignored_queries_before}개 쿼리, {favorite_ignored_time:.3f}초, favorite: {len(favorite_question_ids)}개, ignored: {len(ignored_question_ids)}개")
        
        # select 파라미터에 따라 시리얼라이저 선택
        # content, answer, explanation 관련 필드가 있는지 확인
        has_content_fields = any('content' in field for field in select_fields)
        has_answer_fields = any('answer' in field for field in select_fields)
        has_explanation_fields = any('explanation' in field for field in select_fields)
        
        if select_fields and not has_content_fields and not has_answer_fields and not has_explanation_fields:
            # 목록 표시용 최적화된 시리얼라이저 사용 (번역 불필요 - 제목만)
            logger.info(f"[GET_EXAM_QUESTIONS] QuestionListSerializer 사용 - 시험 ID: {exam_id}, 문제 수: {questions.count()}, 번역 불필요 (목록용)")
            from ..serializers import QuestionListSerializer
            
            serialize_start = time.time()
            serialize_queries_before = len(connection.queries)
            
            serializer = QuestionListSerializer(questions, many=True, context={'request': request})
            questions_data = serializer.data
            
            serialize_time = time.time() - serialize_start
            serialize_queries_after = len(connection.queries)
            serialize_query_count = serialize_queries_after - serialize_queries_before
            
            total_time = time.time() - start_time
            total_queries_after = len(connection.queries)
            total_query_count = total_queries_after - total_queries_before
            
            logger.info(f"[GET_EXAM_QUESTIONS] 직렬화 완료 - {serialize_query_count}개 쿼리, {serialize_time:.3f}초")
            logger.info(f"[GET_EXAM_QUESTIONS] 성능 요약 - 총 시간: {total_time:.3f}초, 총 쿼리: {total_query_count}개, 문제 수: {len(questions_data)}개")
            logger.info(f"========== GET_EXAM_QUESTIONS 완료 ==========")
            
            return Response(questions_data)
        else:
            # 상세 내용이 필요한 경우 기존 방식 사용 + 번역 처리
            if user.is_authenticated:
                logger.info(f"[GET_EXAM_QUESTIONS] 문제별 번역 처리 시작 - 시험 ID: {exam_id}, 문제 수: {questions.count()}")
                
                # 각 문제에 대해 번역 체크 및 백그라운드 번역 처리
                from ..utils.multilingual_utils import MultilingualContentManager
                import threading
                from django.contrib.auth import get_user_model
                User = get_user_model()
                
                user_language = get_user_language(request)
                question_multilingual_fields = ['title', 'content', 'answer', 'explanation']
            
                # 번역이 필요한 문제들을 백그라운드로 처리
                def translate_question_background(question_id, user_id, exam_id):
                    """백그라운드에서 문제 번역 처리"""
                    try:
                        question = Question.objects.get(id=question_id)
                        user = User.objects.get(id=user_id) if user_id else None
                        
                        if not user or not user.is_authenticated:
                            logger.warning(f"[GET_EXAM_QUESTIONS] 백그라운드 번역 - 사용자 인증 없음: question_id={question_id}")
                            return
                        
                        manager = MultilingualContentManager(
                            question,
                            user,
                            language_fields=question_multilingual_fields,
                            skip_completion_update=True  # 조회 시에는 완성도 상태 업데이트 건너뛰기
                        )
                        manager.handle_multilingual_update()
                        logger.info(f"[GET_EXAM_QUESTIONS] 문제 {question_id} 백그라운드 번역 완료")
                    except Question.DoesNotExist:
                        logger.error(f"[GET_EXAM_QUESTIONS] 백그라운드 번역 - 문제를 찾을 수 없음: question_id={question_id}")
                    except Exception as e:
                        logger.error(f"[GET_EXAM_QUESTIONS] 문제 {question_id} 백그라운드 번역 실패: {e}", exc_info=True)
            
                # 번역이 필요한 문제들을 확인하고 백그라운드로 처리
                for question in questions:
                    needs_translation = False
                    
                    # 소스 언어 확인: created_language가 명시적으로 설정되어 있으면 그것을 사용, 없으면 기본 언어 사용
                    # 예: created_language='ko'이면 explanation_ko가 소스, explanation_en으로 번역 가능
                    from quiz.utils.multilingual_utils import BASE_LANGUAGE
                    source_language = question.created_language or BASE_LANGUAGE
                    
                    for field_name in question_multilingual_fields:
                        current_field = f"{field_name}_{user_language}"
                        current_content = getattr(question, current_field, None)
                        
                        # 디버깅: 필드 값 확인
                        logger.info(f"[GET_EXAM_QUESTIONS] 문제 {question.id} {current_field} 확인 - 값: '{current_content[:50] if current_content else None}' (길이: {len(current_content) if current_content else 0})")
                        
                        # 현재 언어 필드가 비어있으면 소스 언어 필드 확인
                        if not current_content or not current_content.strip():
                            # 소스 언어 필드 확인
                            source_field = f"{field_name}_{source_language}"
                            source_content = getattr(question, source_field, None)
                            
                            # 소스 언어 필드가 비어있으면 번역 불가능 (소스가 없으므로)
                            if not source_content or not source_content.strip():
                                logger.warning(f"[GET_EXAM_QUESTIONS] 문제 {question.id} {field_name} 모든 언어 필드 비어있음")
                                logger.info(f"[GET_EXAM_QUESTIONS] 문제 {question.id} {field_name} 소스 언어({source_language}) 필드가 비어있어 번역 불가능 - 건너뜀")
                                continue  # 이 필드는 번역 불가능, 다음 필드 확인
                            
                            # 소스 언어 필드가 있으면 번역 필요
                            needs_translation = True
                            logger.info(f"[GET_EXAM_QUESTIONS] 문제 {question.id}의 {field_name} 번역 필요: {user_language} 필드가 비어있지만 소스 언어({source_language}) 필드 존재 - 백그라운드 처리 예약")
                            break
                    
                    # 번역이 필요한 경우 백그라운드 스레드로 처리
                    if needs_translation and user.is_authenticated:
                        logger.info(f"[GET_EXAM_QUESTIONS] 문제 {question.id} 백그라운드 번역 시작")
                        thread = threading.Thread(
                            target=translate_question_background,
                            args=(question.id, user.id, exam_id)
                        )
                        thread.daemon = True
                        thread.start()
                        # 번역 완료를 기다리지 않고 계속 진행
            
                # 번역 완료를 기다리지 않고 기존 내용을 먼저 반환
                questions_data = []
                for question in questions:
                    question_data = {
                        'id': question.id,
                        'csv_id': question.csv_id,
                        'title_ko': question.title_ko,
                        'title_en': question.title_en,
                        'title_es': getattr(question, 'title_es', None),
                        'title_zh': getattr(question, 'title_zh', None),
                        'title_ja': getattr(question, 'title_ja', None),
                        'content_ko': question.content_ko,
                        'content_en': question.content_en,
                        'content_es': getattr(question, 'content_es', None),
                        'content_zh': getattr(question, 'content_zh', None),
                        'content_ja': getattr(question, 'content_ja', None),
                        'answer_ko': question.answer_ko,
                        'answer_en': question.answer_en,
                        'answer_es': getattr(question, 'answer_es', None),
                        'answer_zh': getattr(question, 'answer_zh', None),
                        'answer_ja': getattr(question, 'answer_ja', None),
                        'explanation_ko': question.explanation_ko,
                        'explanation_en': question.explanation_en,
                        'explanation_es': getattr(question, 'explanation_es', None),
                        'explanation_zh': getattr(question, 'explanation_zh', None),
                        'explanation_ja': getattr(question, 'explanation_ja', None),
                        'difficulty': question.difficulty,
                        'url': question.url,
                        'group_id': question.group_id,
                        'created_at': question.created_at,
                        'updated_at': question.updated_at,
                        'created_language': question.created_language,
                        'is_ko_complete': question.is_ko_complete,
                        'is_en_complete': question.is_en_complete,
                        'is_es_complete': getattr(question, 'is_es_complete', False),
                        'is_zh_complete': getattr(question, 'is_zh_complete', False),
                        'is_ja_complete': getattr(question, 'is_ja_complete', False),
                        'created_by': question.created_by.id if question.created_by else None,
                        'is_favorite': question.id in favorite_question_ids,
                        'is_ignored': question.id in ignored_question_ids
                    }
                    
                    # 다국어 처리 (사용자 언어에 맞는 localized 필드 추가) - 모든 언어 동일하게 처리
                    user_language = get_user_language(request)
                    
                    question_data['localized_title'] = get_localized_field_func(question, 'title', user_language, '')
                    question_data['localized_content'] = get_localized_field_func(question, 'content', user_language, '')
                    question_data['localized_answer'] = get_localized_field_func(question, 'answer', user_language, '')
                    question_data['localized_explanation'] = get_localized_field_func(question, 'explanation', user_language, '')
                    
                    # 사용 가능한 언어 목록 (모든 언어 동일하게 처리)
                    available_languages = []
                    for lang in SUPPORTED_LANGUAGES:
                        if (getattr(question, f'title_{lang}', None) or 
                            getattr(question, f'content_{lang}', None) or 
                            getattr(question, f'answer_{lang}', None) or 
                            getattr(question, f'explanation_{lang}', None)):
                            available_languages.append(lang)
                    question_data['available_languages'] = available_languages
                    question_data['current_language'] = user_language
                    
                    questions_data.append(question_data)
                
                # favorite과 ignored 상태 추가
                for question_data in questions_data:
                    question_data['is_favorite'] = question_data['id'] in favorite_question_ids
                    question_data['is_ignored'] = question_data['id'] in ignored_question_ids
                
                return Response(questions_data)
            else:
                # 비로그인 사용자는 기본 데이터만 반환 (번역 처리 없음)
                # 비로그인 사용자는 기본 언어로 표시
                from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES, BASE_LANGUAGE
                questions_data = []
                # 쿼리셋을 리스트로 변환하여 모든 문제를 처리
                questions_list = list(questions)
                logger.info(f"[GET_EXAM_QUESTIONS] 비로그인 사용자 - questions_list 길이: {len(questions_list)}")
                
                # 비로그인 사용자는 기본 언어('en') 사용
                def get_field_value(question, field_name):
                    """기본 언어를 우선 사용, 없으면 다른 언어 중 하나 사용"""
                    value = getattr(question, f'{field_name}_{BASE_LANGUAGE}', None)
                    if value:
                        return value
                    for lang in SUPPORTED_LANGUAGES:
                        value = getattr(question, f'{field_name}_{lang}', None)
                        if value:
                            return value
                    return ''
                
                processed_count = 0
                for question in questions_list:
                    try:
                        question_data = {
                            'id': question.id,
                            'csv_id': question.csv_id,
                            'title_ko': question.title_ko,
                            'title_en': question.title_en,
                            'content_ko': question.content_ko,
                            'content_en': question.content_en,
                            'answer_ko': question.answer_ko,
                            'answer_en': question.answer_en,
                            'explanation_ko': question.explanation_ko,
                            'explanation_en': question.explanation_en,
                            'difficulty': question.difficulty,
                            'url': question.url,
                            'group_id': question.group_id,
                            'created_at': question.created_at,
                            'updated_at': question.updated_at,
                            'created_language': question.created_language,
                            'is_ko_complete': question.is_ko_complete,
                            'is_en_complete': question.is_en_complete,
                            'created_by': question.created_by.id if question.created_by else None,
                        }
                        
                        question_data['localized_title'] = get_field_value(question, 'title')
                        question_data['localized_content'] = get_field_value(question, 'content')
                        question_data['localized_answer'] = get_field_value(question, 'answer')
                        question_data['localized_explanation'] = get_field_value(question, 'explanation')
                        question_data['available_languages'] = [lang for lang in SUPPORTED_LANGUAGES 
                                                               if (getattr(question, f'title_{lang}', None) or 
                                                                   getattr(question, f'content_{lang}', None) or
                                                                   getattr(question, f'answer_{lang}', None) or
                                                                   getattr(question, f'explanation_{lang}', None))]
                        question_data['current_language'] = BASE_LANGUAGE
                        questions_data.append(question_data)
                        processed_count += 1
                    except Exception as e:
                        logger.error(f"[GET_EXAM_QUESTIONS] 비로그인 사용자 - 문제 처리 중 오류 (question_id: {question.id if question else 'unknown'}): {e}", exc_info=True)
                        continue
                
                logger.info(f"[GET_EXAM_QUESTIONS] 비로그인 사용자 - 처리 완료: {processed_count}개 처리, questions_data 길이: {len(questions_data)}")
            
            # 직렬화 성능 측정
            serialize_start = time.time()
            serialize_queries_before = len(connection.queries)
            
            response_data = questions_data
            
            serialize_time = time.time() - serialize_start
            serialize_queries_after = len(connection.queries)
            serialize_query_count = serialize_queries_after - serialize_queries_before
            
            total_time = time.time() - start_time
            total_queries_after = len(connection.queries)
            total_query_count = total_queries_after - total_queries_before
            
            logger.info(f"[GET_EXAM_QUESTIONS] 직렬화 완료 - {serialize_query_count}개 쿼리, {serialize_time:.3f}초")
            logger.info(f"[GET_EXAM_QUESTIONS] 성능 요약 - 총 시간: {total_time:.3f}초, 총 쿼리: {total_query_count}개, 문제 수: {len(response_data)}개")
            logger.info(f"========== GET_EXAM_QUESTIONS 완료 ==========")
            
            return Response(response_data)
    except Exam.DoesNotExist:
        logger.error(f"[GET_EXAM_QUESTIONS] 시험을 찾을 수 없음 - exam_id: {exam_id}")
        return Response({'error': '시험을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def translate_exam(request, exam_id):
    """시험과 문제들을 선택한 언어로 번역합니다 (강제 재번역)."""
    import threading
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"[TRANSLATE_EXAM] 번역 API 호출 시작 - exam_id: {exam_id}, 사용자: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
    logger.info(f"[TRANSLATE_EXAM] 요청 데이터: {request.data}")
    logger.info(f"[TRANSLATE_EXAM] CSRF 쿠키: {request.COOKIES.get('csrftoken', '없음')}")
    logger.info(f"[TRANSLATE_EXAM] CSRF 헤더: {request.META.get('HTTP_X_CSRFTOKEN', '없음')}")
    
    try:
        exam = Exam.objects.get(id=exam_id)
        exam_title = get_localized_field(exam, 'title', get_user_language(request), '')
        logger.info(f"[TRANSLATE_EXAM] 시험 조회 성공 - exam_id: {exam_id}, 제목: {exam_title}")
        
        # 권한 확인: admin, 스터디 관리자, 또는 시험 생성자
        user = request.user
        has_permission = False
        
        # 1. 관리자 권한 확인 (is_superuser 또는 admin_role)
        if hasattr(user, 'is_superuser') and user.is_superuser:
            has_permission = True
            logger.info(f"[TRANSLATE_EXAM] 권한 확인 - is_superuser: {user.is_superuser}")
        
        if not has_permission:
            try:
                user_profile = user.profile
                user_role = user_profile.role
                logger.info(f"[TRANSLATE_EXAM] 권한 확인 - user_role: {user_role}")
                if user_role in ['admin_role', 'study_admin_role']:
                    has_permission = True
            except Exception as e:
                user_role = None
                logger.warning(f"[TRANSLATE_EXAM] user_profile 접근 실패: {str(e)}")
        
        # 2. 스터디 관리자 권한 확인
        if not has_permission:
            is_study_admin = Member.objects.filter(
                user=user,
                is_active=True,
                role__in=['study_admin', 'study_leader']
            ).exists()
            logger.info(f"[TRANSLATE_EXAM] 권한 확인 - is_study_admin: {is_study_admin}")
            if is_study_admin:
                has_permission = True
        
        # 3. 시험 생성자 권한 확인
        if not has_permission:
            is_creator = exam.created_by == user
            logger.info(f"[TRANSLATE_EXAM] 권한 확인 - is_creator: {is_creator}, exam.created_by: {exam.created_by}, user: {user}")
            if is_creator:
                has_permission = True
        
        logger.info(f"[TRANSLATE_EXAM] 최종 권한 확인 결과 - has_permission: {has_permission}, user: {user.username}")
        
        if not has_permission:
            return Response({'error': '관리자, 스터디 관리자 또는 시험 생성자 권한이 필요합니다.'}, status=status.HTTP_403_FORBIDDEN)
        
        # 요청 데이터 확인
        target_languages = request.data.get('target_languages', [])
        if not target_languages or not isinstance(target_languages, list):
            return Response({'error': 'target_languages는 배열 형태로 제공되어야 합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 지원 언어 확인
        from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
        invalid_languages = [lang for lang in target_languages if lang not in SUPPORTED_LANGUAGES]
        if invalid_languages:
            return Response({'error': f'지원하지 않는 언어: {", ".join(invalid_languages)}'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 원본 언어 확인
        source_language = exam.created_language or 'en'
        if source_language not in SUPPORTED_LANGUAGES:
            source_language = 'en'  # 기본값
        
        # 현재 언어 제외 (프론트엔드에서 처리하지만 백엔드에서도 확인)
        target_languages = [lang for lang in target_languages if lang != source_language]
        
        if not target_languages:
            return Response({'error': '번역할 언어를 선택해주세요.'}, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"[TRANSLATE_EXAM] 번역 요청 - 시험 ID: {exam_id}, 원본 언어: {source_language}, 타겟 언어: {target_languages}, 사용자: {user.username}")
        
        # 백그라운드 번역 작업 시작
        def translate_in_background():
            try:
                logger.info(f"[TRANSLATE_EXAM] 백그라운드 번역 시작 - 시험 ID: {exam_id}")
                
                # 백그라운드 스레드에서 exam 객체 다시 로드
                exam = Exam.objects.get(id=exam_id)
                
                from quiz.utils.multilingual_utils import MultilingualContentManager, batch_translate_texts
                
                # 시험 번역
                for target_lang in target_languages:
                    try:
                        logger.info(f"[TRANSLATE_EXAM] 시험 {exam_id} {source_language} → {target_lang} 번역 시작")
                        
                        # 강제 재번역을 위해 번역 작업 직접 생성
                        translation_tasks = []
                        for field_name in ['title', 'description']:
                            source_field = f"{field_name}_{source_language}"
                            target_field = f"{field_name}_{target_lang}"
                            source_content = getattr(exam, source_field, None)
                            
                            if source_content and source_content.strip():
                                translation_tasks.append((field_name, source_language, target_lang, source_content))
                        
                        if translation_tasks:
                            # MultilingualContentManager를 사용하여 번역 실행
                            exam_manager = MultilingualContentManager(
                                exam,
                                user,
                                language_fields=['title', 'description'],
                                preserve_empty_values=False
                            )
                            exam_manager._execute_batch_translations(translation_tasks)
                            exam.refresh_from_db()
                            logger.info(f"[TRANSLATE_EXAM] 시험 {exam_id} {source_language} → {target_lang} 번역 완료")
                        
                    except Exception as e:
                        logger.error(f"[TRANSLATE_EXAM] 시험 {exam_id} {source_language} → {target_lang} 번역 실패: {str(e)}", exc_info=True)
                
                # 문제 번역
                questions = exam.questions.all()
                logger.info(f"[TRANSLATE_EXAM] 문제 번역 시작 - 문제 수: {questions.count()}")
                
                for question in questions:
                    for target_lang in target_languages:
                        try:
                            # 필드 존재 여부 확인
                            has_target_field = all(hasattr(question, f"{field_name}_{target_lang}") 
                                                  for field_name in ['title', 'content', 'answer', 'explanation'])
                            if not has_target_field:
                                logger.error(f"[TRANSLATE_EXAM] 문제 {question.id}에 {target_lang} 필드가 없습니다. 모델 마이그레이션이 필요합니다.")
                                continue
                            
                            # 강제 재번역을 위해 번역 작업 직접 생성
                            translation_tasks = []
                            for field_name in ['title', 'content', 'answer', 'explanation']:
                                source_field = f"{field_name}_{source_language}"
                                target_field = f"{field_name}_{target_lang}"
                                
                                # 필드 존재 여부 확인
                                if not hasattr(question, source_field):
                                    logger.warning(f"[TRANSLATE_EXAM] 문제 {question.id}에 {source_field} 필드가 없습니다.")
                                    continue
                                if not hasattr(question, target_field):
                                    logger.warning(f"[TRANSLATE_EXAM] 문제 {question.id}에 {target_field} 필드가 없습니다.")
                                    continue
                                
                                source_content = getattr(question, source_field, None)
                                
                                if source_content and source_content.strip():
                                    translation_tasks.append((field_name, source_language, target_lang, source_content))
                            
                            if translation_tasks:
                                question_manager = MultilingualContentManager(
                                    question,
                                    user,
                                    language_fields=['title', 'content', 'answer', 'explanation'],
                                    preserve_empty_values=False
                                )
                                question_manager._execute_batch_translations(translation_tasks)
                                question.refresh_from_db()
                            
                        except Exception as e:
                            logger.error(f"[TRANSLATE_EXAM] 문제 {question.id} {source_language} → {target_lang} 번역 실패: {str(e)}", exc_info=True)
                
                # 번역 완료 후 supported_languages 업데이트
                exam.refresh_from_db()
                
                # 모든 선택한 언어가 번역 완료되었는지 확인
                completed_languages = []
                for lang in target_languages:
                    # 시험의 title과 description이 모두 번역되었는지 확인
                    title_field = f"title_{lang}"
                    description_field = f"description_{lang}"
                    title_translated = getattr(exam, title_field, None) and getattr(exam, title_field, None).strip()
                    description_translated = getattr(exam, description_field, None) and getattr(exam, description_field, None).strip()
                    
                    if title_translated and description_translated:
                        # 문제들도 확인 (모든 문제가 번역되었는지 확인)
                        questions = exam.questions.all()
                        all_questions_translated = True
                        for q in questions:
                            for field_name in ['title', 'content', 'answer', 'explanation']:
                                field = f"{field_name}_{lang}"
                                if not getattr(q, field, None) or not getattr(q, field, None).strip():
                                    all_questions_translated = False
                                    break
                            if not all_questions_translated:
                                break
                        
                        if all_questions_translated:
                            completed_languages.append(lang.upper())
                
                # 원본 언어도 추가
                completed_languages.append(source_language.upper())
                
                # supported_languages 업데이트
                if completed_languages:
                    exam.supported_languages = ','.join(sorted(set(completed_languages)))
                    exam._skip_auto_supported_languages = True
                    exam.save(update_fields=['supported_languages'])
                    logger.info(f"[TRANSLATE_EXAM] supported_languages 업데이트: {exam.supported_languages}")
                
                # 언어별 완성도 상태 업데이트
                exam_manager = MultilingualContentManager(exam, user, ['title', 'description'])
                exam_manager._update_language_completion_status()
                
                for question in exam.questions.all():
                    question_manager = MultilingualContentManager(question, user, ['title', 'content', 'answer', 'explanation'])
                    question_manager._update_language_completion_status()
                
                logger.info(f"[TRANSLATE_EXAM] 백그라운드 번역 완료 - 시험 ID: {exam_id}")
                
            except Exception as e:
                logger.error(f"[TRANSLATE_EXAM] 백그라운드 번역 중 오류 발생: {str(e)}", exc_info=True)
        
        # 백그라운드 스레드 시작
        thread = threading.Thread(target=translate_in_background)
        thread.daemon = True
        thread.start()
        
        return Response({
            'message': '번역이 시작되었습니다.',
            'exam_id': str(exam_id),
            'source_language': source_language,
            'target_languages': target_languages
        }, status=status.HTTP_202_ACCEPTED)
        
    except Exam.DoesNotExist:
        return Response({'error': '시험을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"[TRANSLATE_EXAM] 예외 발생 - exam_id: {exam_id}, 에러: {str(e)}", exc_info=True)
        return Response({'error': f'번역 요청 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
def delete_exam(request, exam_id):
    """시험을 삭제합니다."""
    try:
        exam = Exam.objects.get(id=exam_id)

        # 권한 확인
        user = request.user
        if not user.is_authenticated:
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)

        # admin_role 사용자는 모든 시험 삭제 가능
        is_admin = False
        if hasattr(user, 'is_superuser') and user.is_superuser:
            is_admin = True
        elif hasattr(user, 'profile') and hasattr(user.profile, 'role') and user.profile.role == 'admin_role':
            is_admin = True

        if not is_admin:
            # 유틸리티 함수를 사용하여 권한 확인
            from quiz.utils.permissions import can_edit_exam
            
            # 디버깅을 위한 상세 로그 추가
            exam_title = get_localized_field(exam, 'title', get_user_language(request), 'Unknown')
            logger.info(f"[DELETE_EXAM] 권한 확인 시작: 사용자 {user.username}, 시험 {exam_title}")
            logger.info(f"[DELETE_EXAM] 시험 생성자: {exam.created_by.username if exam.created_by else 'None'}")
            logger.info(f"[DELETE_EXAM] 사용자 권한: {getattr(user.profile, 'role', 'No profile') if hasattr(user, 'profile') else 'No profile'}")
            
            can_edit = can_edit_exam(user, exam)
            logger.info(f"[DELETE_EXAM] can_edit_exam 결과: {can_edit}")
            
            if not can_edit:
                return Response({'error': '이 시험을 삭제할 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)

        # 시험과 관련된 모든 데이터 삭제
        # 1. 시험 결과 상세 처리
        exam_results = ExamResult.objects.filter(exam=exam)
        
        # Daily Exam인 경우 통계 정보 보존
        user_lang = get_user_language(request)
        exam_title = get_localized_field(exam, 'title', user_lang, '')
        is_daily_exam = "Today's Quizzes for" in exam_title if exam_title else False
        if is_daily_exam:
            exam_title = get_localized_field(exam, 'title', get_user_language(request), 'Unknown')
            logger.info(f"[DELETE_EXAM] Daily Exam '{exam_title}' - 통계 정보 보존 (ExamResultDetail 유지)")
            # Daily Exam의 경우 ExamResult만 삭제하고 ExamResultDetail은 유지
            # (통계 정보는 원본 시험에 묶여 있어야 함)
        else:
            # 일반 시험의 경우 상세 데이터 삭제
            for result in exam_results:
                ExamResultDetail.objects.filter(result=result).delete()
            # 2. 시험 결과 삭제
            exam_results.delete()
        
        # Daily Exam이 아닌 경우에만 시험 결과 삭제
        if not is_daily_exam:
            exam_results.delete()

        # 3. 시험 문제 관계 삭제 (통계 정보 보존을 위해 문제는 삭제하지 않음)
        exam_questions = ExamQuestion.objects.filter(exam=exam)
        
        # 해당 시험에 연결된 문제들의 ID 수집
        exam_question_ids = list(exam_questions.values_list('question_id', flat=True))
        
        # 추천 시험인 경우, 해당 시험에서 선택된 문제들의 group_id 초기화
        # 단, Daily Exam 생성 시 자동으로 설정된 group_id만 초기화 (사용자가 설정한 group_id는 보존)
        user_lang = get_user_language(request)
        exam_title = get_localized_field(exam, 'title', user_lang, '')
        is_recommendation_exam = "Today's Quizzes for" in exam_title if exam_title else False
        if is_recommendation_exam and exam_question_ids:
            from ..models import Question
            exam_title = get_localized_field(exam, 'title', get_user_language(request), 'Unknown')
            # 해당 시험의 제목으로 group_id가 설정된 문제들만 찾아 초기화
            # (사용자가 직접 설정한 다른 group_id는 보존)
            Question.objects.filter(
                id__in=exam_question_ids,
                group_id=exam_title
            ).update(group_id='')
            logger.info(f"[DELETE_EXAM] 추천 시험 '{exam_title}'의 문제들 group_id 초기화 완료 (Daily Exam 생성 시 자동 설정된 것만)")
        
        # 통계 정보 보존을 위해 문제는 삭제하지 않음
        # 대신 시험-문제 연결만 삭제 (ExamQuestion 관계 삭제)
        exam_title = get_localized_field(exam, 'title', get_user_language(request), 'Unknown')
        logger.info(f"[DELETE_EXAM] 시험 '{exam_title}' - 문제 연결만 삭제 (문제 유지, 통계 정보 보존)")

        exam_questions.delete()

        # 4. 시험 삭제 (삭제 전에 ID 저장)
        exam_id_str = str(exam.id)
        exam_title = get_localized_field(exam, 'title', get_user_language(request), 'Unknown')
        exam.delete()

        # 캐시 무효화 (ExamCacheManager 사용)
        try:
            from ..utils.cache_utils import ExamCacheManager
            # 시험 관련 모든 캐시 무효화
            ExamCacheManager.invalidate_exam_cache(exam_id_str)
            ExamCacheManager.invalidate_all_exam_cache()
            logger.info(f"[DELETE_EXAM] ExamCacheManager를 통한 캐시 무효화 완료: {exam_id_str}")
        except Exception as e:
            logger.error(f"[DELETE_EXAM] ExamCacheManager 캐시 무효화 실패: {e}")
            # 폴백: 기존 방식으로 캐시 무효화
            try:
                if hasattr(cache, 'delete_pattern'):
                    cache.delete_pattern("exams_*")
                    cache.delete_pattern("exam_results_*")
                    logger.info("[DELETE_EXAM] Redis 패턴 기반 폴백 캐시 무효화 완료")
                else:
                    # 다른 캐시 백엔드의 경우 개별 키 삭제
                    cache.delete("exams_anonymous")
                    cache.delete("exams_1")  # admin 사용자 ID
                    cache.delete("exams_15")  # doohee323 사용자 ID
                    cache.delete("exam_results_anonymous")
                    cache.delete("exam_results_1")
                    cache.delete("exam_results_15")
                    logger.info("[DELETE_EXAM] 개별 키 기반 폴백 캐시 무효화 완료")
            except Exception as e2:
                logger.error(f"[DELETE_EXAM] 폴백 캐시 무효화도 실패: {e2}")

        # 추가로 현재 사용자의 캐시도 명시적으로 삭제
        if user.is_authenticated:
            user_cache_key = f"exams_{user.id}"
            cache.delete(user_cache_key)
            logger.info(f"[DELETE_EXAM] 사용자별 캐시 삭제: {user_cache_key}")

        return Response({'success': True}, status=status.HTTP_200_OK)

    except Exam.DoesNotExist:
        return Response({'error': '시험을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'시험 삭제 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
def update_exam(request, exam_id):
    """시험 정보를 수정합니다."""
    try:
        logger.info(f"[UPDATE_EXAM] API 요청 시작 - exam_id: {exam_id}")
        logger.info(f"[UPDATE_EXAM] 요청 데이터: {request.data}")
        
        exam = Exam.objects.get(id=exam_id)

        # 권한 확인
        user = request.user
        if not user.is_authenticated:
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)

        # admin_role 사용자는 모든 시험 수정 가능
        is_admin = False
        if hasattr(user, 'is_superuser') and user.is_superuser:
            is_admin = True
        elif hasattr(user, 'profile') and hasattr(user.profile, 'role') and user.profile.role == 'admin_role':
            is_admin = True

        if not is_admin:
            # 유틸리티 함수를 사용하여 권한 확인
            from quiz.utils.permissions import can_edit_exam
            if not can_edit_exam(user, exam):
                return Response({'error': '이 시험을 수정할 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)

        updated = False
        if 'title' in request.data:
            # 다국어 처리: 사용자 언어에 맞는 필드에 저장 (모든 언어 동일하게 처리)
            from quiz.utils.multilingual_utils import BASE_LANGUAGE, SUPPORTED_LANGUAGES
            user_language = getattr(request.user.profile, 'language', BASE_LANGUAGE) if hasattr(request.user, 'profile') else BASE_LANGUAGE
            if user_language in SUPPORTED_LANGUAGES:
                setattr(exam, f'title_{user_language}', request.data['title'])
            else:
                setattr(exam, f'title_{BASE_LANGUAGE}', request.data['title'])  # 기본값
            updated = True
        if 'description' in request.data:
            # 다국어 처리: 사용자 언어에 맞는 필드에 저장 (모든 언어 동일하게 처리)
            from quiz.utils.multilingual_utils import BASE_LANGUAGE, SUPPORTED_LANGUAGES
            user_language = getattr(request.user.profile, 'language', BASE_LANGUAGE) if hasattr(request.user, 'profile') else BASE_LANGUAGE
            if user_language in SUPPORTED_LANGUAGES:
                setattr(exam, f'description_{user_language}', request.data['description'])
            else:
                setattr(exam, f'description_{BASE_LANGUAGE}', request.data['description'])  # 기본값
            updated = True
        if 'version_number' in request.data:
            exam.version_number = request.data['version_number']
            updated = True
        if 'created_at' in request.data:
            exam.created_at = request.data['created_at']
            updated = True
        if 'file_name' in request.data:
            exam.file_name = request.data['file_name']
            updated = True
        if 'is_public' in request.data:
            exam.is_public = request.data['is_public']
            updated = True
        if 'force_answer' in request.data:
            exam.force_answer = request.data['force_answer']
            updated = True
        if 'voice_mode_enabled' in request.data:
            exam.voice_mode_enabled = request.data['voice_mode_enabled']
            updated = True
        if 'ai_mock_interview' in request.data:
            exam.ai_mock_interview = request.data['ai_mock_interview']
            updated = True
        if 'age_rating' in request.data:
            age_rating_value = request.data.get('age_rating')
            # 연령 등급 값 검증 (4+, 9+, 12+, 17+)
            if age_rating_value and str(age_rating_value).strip() in ['4+', '9+', '12+', '17+']:
                exam.age_rating = str(age_rating_value).strip()
                updated = True
                logger.info(f"[UPDATE_EXAM] 시험 연령 등급 업데이트: {age_rating_value} -> {exam.age_rating} (exam_id: {exam_id})")
            elif age_rating_value:
                logger.warning(f"[UPDATE_EXAM] 잘못된 연령 등급 값: {age_rating_value} (4+, 9+, 12+, 17+ 중 하나여야 함)")
        if 'exam_difficulty' in request.data:
            exam_difficulty_value = request.data['exam_difficulty']
            # 난이도 값 검증 (1~10)
            if exam_difficulty_value is not None:
                exam_difficulty_value = int(exam_difficulty_value)
                if 1 <= exam_difficulty_value <= 10:
                    exam.exam_difficulty = exam_difficulty_value
                    updated = True
                    logger.info(f"[UPDATE_EXAM] 시험 난이도 업데이트: {exam_difficulty_value} (exam_id: {exam_id})")
                else:
                    logger.warning(f"[UPDATE_EXAM] 잘못된 시험 난이도 값: {exam_difficulty_value} (1~10 범위를 벗어남)")
        if 'supported_languages' in request.data:
            # admin만 supported_languages 수정 가능
            if is_admin:
                supported_languages_value = request.data.get('supported_languages', '')
                exam.supported_languages = supported_languages_value if supported_languages_value is not None else ''
                # 자동 설정을 건너뛰도록 플래그 설정
                exam._skip_auto_supported_languages = True
                logger.info(f"[UPDATE_EXAM] supported_languages 업데이트: '{supported_languages_value}' (exam_id: {exam_id})")
                updated = True
            else:
                logger.warning(f"[UPDATE_EXAM] 비관리자가 supported_languages 수정 시도: user={user.username}, exam_id={exam_id}")
        
        # tags 필드 처리 (ManyToManyField는 별도로 처리해야 함)
        if 'tags' in request.data:
            tag_ids = request.data.get('tags', [])
            logger.info(f"[UPDATE_EXAM] 태그 업데이트 - exam_id: {exam_id}, tag_ids: {tag_ids}")
            
            # 유효한 태그 ID만 필터링
            valid_tag_ids = []
            for tag_id in tag_ids:
                try:
                    from ..models import Tag
                    tag = Tag.objects.get(id=tag_id)
                    valid_tag_ids.append(tag_id)
                    tag_lang = tag.created_language if hasattr(tag, 'created_language') else BASE_LANGUAGE
                    tag_name = get_localized_field(tag, 'name', tag_lang, 'Unknown')
                    logger.info(f"[UPDATE_EXAM] 유효한 태그 ID: {tag_id} ({tag_name})")
                except Tag.DoesNotExist:
                    logger.warning(f"[UPDATE_EXAM] 존재하지 않는 태그 ID: {tag_id}")
            
            # 태그는 반드시 1개 이상 필요
            if not valid_tag_ids:
                return Response(
                    {'error': '시험에는 반드시 1개 이상의 태그가 필요합니다.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 태그 설정
            exam.tags.set(valid_tag_ids)
            logger.info(f"[UPDATE_EXAM] 시험 태그 설정 완료 - 총 {len(valid_tag_ids)}개 태그")
            updated = True
        
        # 필요시 추가 필드 처리
        if updated:
            # supported_languages를 임시로 저장 (번역 처리 후에도 유지하기 위해)
            saved_supported_languages = exam.supported_languages
            exam._saved_supported_languages = saved_supported_languages
            exam.save()
            
            # 다국어 콘텐츠 직접 처리 (Study와 동일한 방식)
            try:
                # 사용자 언어 확인
                from quiz.utils.multilingual_utils import BASE_LANGUAGE
                user_language = getattr(request.user.profile, 'language', BASE_LANGUAGE) if hasattr(request.user, 'profile') else BASE_LANGUAGE
                
                # 번역이 필요한 필드들 처리
                fields_to_translate = ['title', 'description']
                
                for field_name in fields_to_translate:
                    # 사용자 언어가 기본 언어이면 번역하지 않음
                    if user_language == BASE_LANGUAGE:
                        continue
                    
                    # 현재 언어의 필드
                    current_field = f"{field_name}_{user_language}"
                    # 대상 언어의 필드 (기본 언어로 번역)
                    target_language = BASE_LANGUAGE
                    target_field = f"{field_name}_{target_language}"
                    
                    # 현재 언어의 콘텐츠 가져오기
                    current_content = getattr(exam, current_field, None)
                    
                    if current_content and current_content.strip():
                        # Exam: 내용이 있으면 항상 번역 수행
                        try:
                            translated_text = _translate_content(
                                current_content, 
                                user_language, 
                                target_language
                            )
                            
                            if translated_text:
                                setattr(exam, target_field, translated_text)
                                logger.info(f"[UPDATE_EXAM] {field_name} 번역 완료: {user_language} → {target_language}")
                            else:
                                logger.warning(f"[UPDATE_EXAM] {field_name} 번역 실패: {user_language} → {target_language}")
                        except Exception as e:
                            logger.error(f"[UPDATE_EXAM] {field_name} 번역 중 오류: {e}")
                    else:
                        logger.info(f"[UPDATE_EXAM] {field_name} 건너뜀: {current_field}에 콘텐츠가 없음")
                
                # 번역된 내용이 있으면 저장
                # supported_languages는 번역 처리와 무관하므로 유지
                if hasattr(exam, '_saved_supported_languages'):
                    exam.supported_languages = exam._saved_supported_languages
                # _skip_auto_supported_languages 플래그가 설정되어 있으면 유지
                if hasattr(exam, '_skip_auto_supported_languages'):
                    skip_flag = exam._skip_auto_supported_languages
                    exam.save()
                    # save 후에도 플래그 재설정 (다른 곳에서 save가 호출될 수 있으므로)
                    exam._skip_auto_supported_languages = skip_flag
                else:
                    exam.save()
                logger.info(f"[UPDATE_EXAM] 다국어 콘텐츠 처리 완료: {exam.id}")
            except Exception as e:
                logger.error(f"[UPDATE_EXAM] 다국어 콘텐츠 처리 실패: {e}")
                # 다국어 처리 실패해도 시험 수정은 계속 진행
            
            # 시험 내용이 변경되었으므로 연령 등급 재계산
            # 단, 사용자가 수동으로 age_rating을 수정한 경우에는 재계산하지 않음
            if 'age_rating' not in request.data:
                try:
                    from ..utils.exam_utils import estimate_exam_age_rating
                    # 시험에 포함된 모든 문제 가져오기
                    exam_questions = [eq.question for eq in exam.examquestion_set.select_related('question').all()]
                    estimated_rating = estimate_exam_age_rating(exam, exam_questions)
                    exam.age_rating = estimated_rating
                    exam.save(update_fields=['age_rating'])
                    logger.info(f"[UPDATE_EXAM] 시험 연령 등급 재계산 완료: {estimated_rating} (시험 ID: {exam.id})")
                except Exception as e:
                    logger.error(f"[UPDATE_EXAM] 시험 연령 등급 재계산 실패: {e}")
                    # 재계산 실패 시 기존 값 유지
            else:
                logger.info(f"[UPDATE_EXAM] 사용자가 수동으로 연령 등급을 수정했으므로 자동 재계산 건너뜀: {request.data.get('age_rating')}")
            
            # 캐시 무효화 (ExamCacheManager 사용)
            try:
                from ..utils.cache_utils import ExamCacheManager
                # 수정된 시험 관련 캐시 무효화
                ExamCacheManager.invalidate_exam_cache(str(exam.id))
                ExamCacheManager.invalidate_all_exam_cache()
                logger.info(f"[UPDATE_EXAM] ExamCacheManager를 통한 캐시 무효화 완료: {exam.id}")
            except Exception as e:
                logger.error(f"[UPDATE_EXAM] ExamCacheManager 캐시 무효화 실패: {e}")
                # 폴백: 기존 방식으로 캐시 무효화
                try:
                    if hasattr(cache, 'delete_pattern'):
                        cache.delete_pattern("exams_*")
                        logger.info("[UPDATE_EXAM] Redis 패턴 기반 폴백 캐시 무효화 완료")
                    else:
                        cache.delete("exams_anonymous")
                        if user.is_authenticated:
                            cache.delete(f"exams_{user.id}")
                        logger.info("[UPDATE_EXAM] 개별 키 기반 폴백 캐시 무효화 완료")
                except Exception as e2:
                    logger.error(f"[UPDATE_EXAM] 폴백 캐시 무효화도 실패: {e2}")
                    
        serializer = ExamSerializer(exam, context={'request': request})
        return Response(serializer.data)
    except Exam.DoesNotExist:
        return Response({'error': '시험을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'시험 수정 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def update_exam_questions_from_excel(request, exam_id):
    """엑셀 파일을 통해 시험의 문제들을 업데이트합니다."""
    try:
        # 시험 존재 확인
        exam = Exam.objects.get(id=exam_id)

        if 'file' not in request.FILES:
            return Response({'error': '파일이 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES['file']
        allowed_extensions = ['.csv', '.xls', '.xlsx']
        file_extension = os.path.splitext(file.name)[1].lower()

        if file_extension not in allowed_extensions:
            return Response({'error': 'CSV, XLS, XLSX 파일만 업로드 가능합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 파일 읽기
        try:
            if file_extension == '.csv':
                file_content = file.read().decode('utf-8')
                corrected_file = auto_correct_csv_from_content(file_content)
                df = pd.read_csv(corrected_file)
            else:
                if file_extension == '.xlsx':
                    # openpyxl 엔진으로 하이퍼링크 포함하여 읽기
                    df = pd.read_excel(file, engine='openpyxl', keep_default_na=True, na_values=['', 'nan', 'None', 'NULL'])
                    logger.info(f"[UPDATE_EXAM_EXCEL] XLSX 파일을 openpyxl로 읽기 완료")
                else:  # .xls
                    df = pd.read_excel(file, engine='xlrd', keep_default_na=True, na_values=['', 'nan', 'None', 'NULL'])
                    logger.info(f"[UPDATE_EXAM_EXCEL] XLS 파일을 xlrd로 읽기 완료")
        except Exception as e:
            return Response({'error': f'파일 읽기 실패: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        # 필수 컬럼 확인
        required_columns = ['문제id', '제목', '문제 내용', '정답']
        if not all(col in df.columns for col in required_columns):
            missing_columns = [col for col in required_columns if col not in df.columns]
            logger.error(f"[UPDATE_EXAM_EXCEL] 필수 컬럼 누락: {missing_columns}")
            return Response({
                'error': f'필수 컬럼이 누락되었습니다: {", ".join(missing_columns)}',
                'available_columns': list(df.columns)
            }, status=status.HTTP_400_BAD_REQUEST)

        # 시험에 속한 문제들만 가져오기
        exam_questions = Question.objects.filter(examquestion__exam=exam)

        stats = {
            'total_rows': len(df),
            'updated': 0,
            'skipped': 0,
            'errors': 0,
            'error_details': []
        }

        for index, row in df.iterrows():
            try:
                # 컬럼명이 다를 수 있으므로 위치 기반으로도 처리
                csv_id = None
                title = None
                content = None
                answer = None
                explanation = None
                difficulty = None
                url = None
                group_id = None

                # 컬럼명으로 찾기 시도
                if '문제id' in df.columns:
                    csv_id = str(row['문제id'])
                elif '문제ID' in df.columns:
                    csv_id = str(row['문제ID'])
                elif 'ID' in df.columns:
                    csv_id = str(row['ID'])
                else:
                    # 첫 번째 컬럼을 문제 ID로 가정
                    csv_id = str(row.iloc[0])

                if '제목' in df.columns:
                    title = str(row['제목']).strip()
                elif 'Title' in df.columns:
                    title = str(row['Title']).strip()
                else:
                    # 두 번째 컬럼을 제목으로 가정
                    title = str(row.iloc[1]).strip()

                if '문제 내용' in df.columns:
                    content = str(row['문제 내용'])
                elif 'Content' in df.columns:
                    content = str(row['Content'])
                else:
                    # 세 번째 컬럼을 내용으로 가정
                    content = str(row.iloc[2])

                if '정답' in df.columns:
                    answer = str(row['정답'])
                elif 'Answer' in df.columns:
                    answer = str(row['Answer'])
                else:
                    # 네 번째 컬럼을 정답으로 가정
                    answer = str(row.iloc[3])

                # 선택적 필드들 컬럼명 기반 처리
                if '설명' in df.columns and pd.notna(row['설명']):
                    explanation = str(row['설명'])
                elif 'Explanation' in df.columns and pd.notna(row['Explanation']):
                    explanation = str(row['Explanation'])
                elif len(row) > 4 and pd.notna(row.iloc[4]):
                    explanation = str(row.iloc[4])
                
                # 난이도 처리 - Excel의 난이도가 최신 정보로 우선시됨
                difficulty = None
                if '난이도' in df.columns:
                    if pd.notna(row['난이도']):
                        difficulty = str(row['난이도']).strip()
                        # 빈 문자열이면 None으로 설정
                        if difficulty == "":
                            difficulty = None
                    # pd.notna()가 False면 이미 None이므로 그대로 유지
                elif 'Difficulty' in df.columns:
                    if pd.notna(row['Difficulty']):
                        difficulty = str(row['Difficulty']).strip()
                        if difficulty == "":
                            difficulty = None
                elif len(row) > 5:
                    if pd.notna(row.iloc[5]):
                        difficulty = str(row.iloc[5]).strip()
                        if difficulty == "":
                            difficulty = None
                
                # URL 처리 - 다양한 컬럼명과 위치 기반 처리
                url = None
                
                # 컬럼명 기반 URL 찾기 (대소문자 구분 없이)
                url_found = False
                for col in df.columns:
                    col_lower = col.lower()
                    if 'url' in col_lower or 'link' in col_lower or '링크' in col:
                        col_value = row[col]
                        if pd.notna(col_value) and str(col_value).strip():
                            url = str(col_value).strip()
                            url_found = True
                            break
                
                # 컬럼명으로 찾지 못한 경우 위치 기반으로 찾기
                if not url_found:
                    if len(row) > 5:
                        for i in range(5, min(len(row), 10)):  # 5번째부터 9번째까지 확인
                            potential_url = row.iloc[i]
                            if pd.notna(potential_url) and str(potential_url).strip():
                                potential_url_str = str(potential_url).strip()
                                # URL 패턴 확인 (http로 시작하는지)
                                if potential_url_str.startswith('http'):
                                    url = potential_url_str
                                    break
                
                # URL이 비어있거나 'nan'인 경우 None으로 설정
                if url and (url == '' or url.lower() == 'nan' or url.lower() == 'none' or url.lower() == 'null'):
                    url = None
                
                # URL이 유효한지 확인 (http 또는 https로 시작하는지)
                if url and not (url.startswith('http://') or url.startswith('https://')):
                    logger.warning(f"[UPDATE_EXAM_EXCEL] 유효하지 않은 URL 형식: {url}")
                    # URL이 유효하지 않아도 저장은 하되 경고 로그 남김
                
                # 그룹ID 처리 - 컬럼명 우선, 위치 기반 후순위
                group_id = None
                if '그룹ID' in df.columns and pd.notna(row['그룹ID']):
                    group_id = str(row['그룹ID']).strip()
                    if group_id == "":
                        group_id = None
                elif 'Group ID' in df.columns and pd.notna(row['Group ID']):
                    group_id = str(row['Group ID']).strip()
                    if group_id == "":
                        group_id = None
                elif len(row) > 7 and pd.notna(row.iloc[7]):
                    group_id = str(row.iloc[7]).strip()
                    if group_id == "":
                        group_id = None

                # 문제 ID를 기준으로 찾기 (해당 시험에 속한 문제들만)
                exam_questions = Question.objects.filter(examquestion__exam=exam, csv_id=csv_id)
                if exam_questions.exists():
                    for question in exam_questions:
                        # Excel의 정보가 최신이므로 우선시하여 업데이트
                        # 백업용 title 필드는 더 이상 사용하지 않음
                        # question.title = title  # 제거 예정
                        # 다국어 필드 사용 (기존 필드는 제거 예정)
                        question.content_ko = content
                        question.answer_ko = answer
                        # 난이도는 Excel에 있으면 무조건 업데이트 (기존 값 무시)
                        if difficulty is not None:
                            question.difficulty = normalize_difficulty(difficulty)
                        elif difficulty == "":  # 빈 문자열인 경우 명시적으로 None으로 설정
                            question.difficulty = None
                        # difficulty가 None인 경우는 업데이트하지 않음 (기존 값 유지)
                        # 설명과 URL은 Excel에 있으면 업데이트
                        if explanation:
                            question.explanation_ko = explanation
                            logger.info(f"[UPDATE_EXAM_EXCEL] 문제 {question.id}의 설명 업데이트: {explanation}")
                        
                        # URL 업데이트 전후 로깅
                        old_url = question.url
                        if url:
                            question.url = url
                            logger.info(f"[UPDATE_EXAM_EXCEL] 문제 {question.id}의 URL 업데이트: {old_url} -> {url}")
                        else:
                            logger.info(f"[UPDATE_EXAM_EXCEL] 문제 {question.id}의 URL이 비어있음 (기존: {old_url})")
                        # group_id는 항상 엑셀 값으로 강제 덮어쓰기
                        question.group_id = group_id
                        question.save()
                        
                        # 번역은 나중에 배치로 처리하므로 여기서는 건너뛰기
                        logger.info(f"[UPDATE_EXAM_EXCEL] 문제 {question.id} 업데이트 완료 (번역은 배치로 처리 예정)")
                    
                    stats['error_details'].append(f'행 {index + 2}: 시험에 속한 기존 문제 {exam_questions.count()}개를 Excel 정보로 업데이트했습니다. (ID: {csv_id}, 제목: {title})')
                else:
                    # 없으면 새로 생성 (Excel 정보를 우선시)
                    normalized_difficulty = None
                    if difficulty is not None:
                        normalized_difficulty = normalize_difficulty(difficulty)
                    elif difficulty == "":  # 빈 문자열인 경우 명시적으로 None으로 설정
                        normalized_difficulty = None
                    
                    # URL 디버깅 로그
                    logger.info(f"[UPDATE_EXAM_EXCEL] 새 문제 생성 - csv_id: {csv_id}, 제목: {title}, URL: {url}")
                    
                    question = Question.objects.create(
                        csv_id=csv_id,
                        # title, content, answer, explanation은 다국어 필드로 설정 (기존 필드는 제거 예정)
                        difficulty=normalized_difficulty,
                        url=url,
                        group_id=group_id
                    )
                    
                    # 생성된 문제의 URL 확인
                    logger.info(f"[UPDATE_EXAM_EXCEL] 새 문제 {question.id} 생성 완료 - 저장된 URL: {question.url}")
                    
                    # 다국어 필드 설정 (한국어 사용자이므로 한국어 필드에 값 설정)
                    question.title_ko = title
                    question.content_ko = content
                    question.answer_ko = answer
                    if explanation:
                        question.explanation_ko = explanation
                    question.save()
                    
                    # 번역은 나중에 배치로 처리하므로 여기서는 건너뛰기
                    logger.info(f"[UPDATE_EXAM_EXCEL] 새 문제 {question.id} 생성 완료 (번역은 배치로 처리 예정)")
                    
                    max_order = ExamQuestion.objects.filter(exam=exam).aggregate(models.Max('order'))['order__max'] or 0
                    ExamQuestion.objects.create(exam=exam, question=question, order=max_order + 1)
                    stats['error_details'].append(f'행 {index + 2}: 새로운 문제가 추가되었습니다. (ID: {csv_id}, 제목: {title})')
                stats['updated'] += 1

            except Exception as e:
                stats['errors'] += 1
                stats['error_details'].append(f'행 {index + 2}: {str(e)}')
                continue

        # 시험의 총 문제 수 업데이트
        exam.total_questions = ExamQuestion.objects.filter(exam=exam).count()
        exam.save()
        
        # 모든 문제 업데이트 완료 후 배치 번역 처리
        try:
            from ..utils.multilingual_utils import process_large_question_batch
            
            # 시험에 속한 모든 문제 가져오기
            exam_questions = Question.objects.filter(examquestion__exam=exam)
            
            if exam_questions.exists():
                logger.info(f"[UPDATE_EXAM_EXCEL] {len(exam_questions)}개 문제 배치 번역 시작")
                
                # 배치 번역 수행
                translation_result = process_large_question_batch(exam_questions, request.user)
                
                logger.info(f"[UPDATE_EXAM_EXCEL] 배치 번역 완료: {translation_result['successful']}/{translation_result['total_translations']} 성공")
                
                if translation_result['errors']:
                    logger.warning(f"[UPDATE_EXAM_EXCEL] 번역 중 일부 오류 발생: {len(translation_result['errors'])}개")
                    for error in translation_result['errors'][:5]:  # 처음 5개만 로그
                        logger.warning(f"[UPDATE_EXAM_EXCEL] 번역 오류: {error}")
                        
        except Exception as e:
            logger.error(f"[UPDATE_EXAM_EXCEL] 배치 번역 처리 실패: {e}")
            # 번역 실패해도 시험 업데이트는 계속 진행

        return Response({
            'message': f'시험 문제 업데이트 완료',
            'stats': stats
        })

    except Exam.DoesNotExist:
        return Response({'error': '시험을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'업데이트 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def import_questions_from_connected_file(request, exam_id):
    """
    연결된 파일로부터 문제를 가져와서 시험에 추가하거나 업데이트합니다.
    
    동작 방식:
    1. csv_id를 파일명으로 설정하여 파일별로 유니크하게 관리
    2. 동일한 파일(동일한 csv_id) + 동일한 제목인 경우 → 기존 문제 업데이트
    3. 새로운 문제인 경우 → 새로 추가
    
    기존 데이터:
    - 기존 csv_id는 그대로 유지 (문제 번호 형태)
    - 새로운 가져오기부터는 csv_id를 파일명으로 설정
    
    통계:
    - imported: 새로 추가된 문제 수
    - updated: 기존 문제 업데이트 수
    - skipped: 변경사항이 없는 문제 수
    - errors: 오류 발생한 문제 수
    """
    try:
        # 시험 존재 확인
        exam = Exam.objects.get(id=exam_id)

        # 연결된 파일이 있는지 확인
        if not exam.file_name:
            return Response({'error': '연결된 파일이 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # MinIO 사용 여부 확인
        use_minio = getattr(settings, 'USE_MINIO', False)
        logger.info(f"[IMPORT_FROM_CONNECTED_FILE] USE_MINIO: {use_minio}")
        logger.info(f"[IMPORT_FROM_CONNECTED_FILE] exam.file_name: {exam.file_name}")
        logger.info(f"[IMPORT_FROM_CONNECTED_FILE] settings.AWS_S3_ENDPOINT_URL: {getattr(settings, 'AWS_S3_ENDPOINT_URL', 'NOT_SET')}")
        logger.info(f"[IMPORT_FROM_CONNECTED_FILE] settings.AWS_STORAGE_BUCKET_NAME: {getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'NOT_SET')}")

        # 파일 확장자 확인
        file_extension = os.path.splitext(exam.file_name)[1].lower()
        allowed_extensions = ['.csv', '.xls', '.xlsx']

        if file_extension not in allowed_extensions:
            return Response({'error': 'CSV, XLS, XLSX 파일만 지원됩니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 파일 읽기
        try:
            if use_minio:
                # MinIO에서 파일 다운로드
                import boto3
                s3_client = boto3.client(
                    's3',
                    endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    verify=False
                )

                try:
                    logger.info(f"[IMPORT_FROM_CONNECTED_FILE] MinIO 파일 다운로드 시도: Bucket={settings.AWS_STORAGE_BUCKET_NAME}, Key=data/{exam.file_name}")
                    response = s3_client.get_object(
                        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                        Key=f'data/{exam.file_name}'
                    )
                    file_content = response['Body'].read()
                    logger.info(f"[IMPORT_FROM_CONNECTED_FILE] MinIO에서 파일 다운로드 성공: {exam.file_name}, 파일 크기: {len(file_content)} bytes")
                except Exception as e:
                    logger.error(f"[IMPORT_FROM_CONNECTED_FILE] MinIO 파일 다운로드 실패: {e}")
                    logger.error(f"[IMPORT_FROM_CONNECTED_FILE] MinIO 설정 - Endpoint: {settings.AWS_S3_ENDPOINT_URL}, Bucket: {settings.AWS_STORAGE_BUCKET_NAME}")
                    return Response({'error': '연결된 파일을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

                # 파일 내용 처리
                if file_extension == '.csv':
                    content = file_content.decode('utf-8')
                    corrected_file = auto_correct_csv_from_content(content)
                    df = pd.read_csv(corrected_file)
                else:
                    file_buffer = BytesIO(file_content)
                    if file_extension == '.xlsx':
                        df = pd.read_excel(file_buffer, engine='openpyxl')
                    else:  # .xls
                        df = pd.read_excel(file_buffer, engine='xlrd')
            else:
                # 로컬 파일 시스템 사용
                file_path = os.path.join(settings.MEDIA_ROOT, 'data', exam.file_name)

                if not os.path.exists(file_path):
                    return Response({'error': '연결된 파일을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

                if file_extension == '.csv':
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                    corrected_file = auto_correct_csv_from_content(file_content)
                    df = pd.read_csv(corrected_file)
                else:
                    if file_extension == '.xlsx':
                        df = pd.read_excel(file_path, engine='openpyxl')
                    else:  # .xls
                        df = pd.read_excel(file_path, engine='xlrd')
        except Exception as e:
            logger.error(f"[IMPORT_FROM_CONNECTED_FILE] 파일 읽기 실패: {e}")
            return Response({'error': f'파일 읽기 실패: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        # 필수 컬럼 확인 (한국어와 영어 컬럼명 모두 지원)
        required_column_pairs = [
            ('문제id', 'Question ID'),
            ('제목', 'Title'), 
            ('문제 내용', 'Question Content'),
            ('정답', 'Answer')
        ]
        
        # 각 필수 필드에 대해 한국어 또는 영어 컬럼이 하나라도 존재하는지 확인
        missing_fields = []
        for korean_col, english_col in required_column_pairs:
            if not (korean_col in df.columns or english_col in df.columns):
                missing_fields.append(f'{korean_col}/{english_col}')
        
        if missing_fields:
            return Response({
                'error': f'필수 컬럼이 누락되었습니다: {", ".join(missing_fields)}',
                'available_columns': list(df.columns),
                'note': '한국어 또는 영어 컬럼명 중 하나는 반드시 필요합니다.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 시험에 이미 존재하는 문제들의 정보 (출처 파일명 + 제목으로 매칭하여 중복 방지)
        # 재가져오기 시 동일한 출처(source_id) + 동일한 제목인 경우에만 업데이트
        existing_questions_by_source_and_title = {}
        for eq in ExamQuestion.objects.filter(exam=exam).select_related('question'):
            question = eq.question
            
            # 출처 파일명 + 제목으로 매칭 (생성 언어 기준)
            question_lang = question.created_language if hasattr(question, 'created_language') else BASE_LANGUAGE
            question_title = get_localized_field(question, 'title', question_lang, '')
            if question.source_id and question_title and question_title.strip():
                key = f"{question.source_id}:{question_title.strip()}"
                existing_questions_by_source_and_title[key] = {
                    'question': question,
                    'exam_question': eq
                }
            
            # 출처 파일명 + 영어 제목으로 매칭
            if question.source_id and question.title_en and question.title_en.strip():
                key = f"{question.source_id}:{question.title_en.strip()}"
                existing_questions_by_source_and_title[key] = {
                    'question': question,
                    'exam_question': eq
                }

        # 통계 정보 - 새로운 방식에 맞게 updated 항목 추가
        stats = {
            'total_rows': len(df),
            'imported': 0,      # 새로 추가된 문제 수
            'updated': 0,       # 기존 문제 업데이트 수 (동일 파일 + 동일 제목)
            'skipped': 0,       # 변경사항이 없는 문제 수
            'errors': 0,        # 오류 발생한 문제 수
            'error_details': []
        }

        for index, row in df.iterrows():
            try:
                # 컬럼명으로 찾기 시도
                csv_id = None
                title = None
                content = None
                answer = None
                explanation = None
                difficulty = None
                url = None
                group_id = None

                # csv_id 설정 (엑셀의 문제 순서 번호)
                problem_order = None
                if '문제id' in df.columns:
                    problem_order = str(row['문제id'])
                elif '문제ID' in df.columns:
                    problem_order = str(row['문제ID'])
                elif 'ID' in df.columns:
                    problem_order = str(row['ID'])
                elif 'Question ID' in df.columns:
                    problem_order = str(row['Question ID'])
                else:
                    # 첫 번째 컬럼을 문제 순서로 가정
                    problem_order = str(row.iloc[0])
                
                csv_id = problem_order  # 엑셀의 문제 순서 번호
                
                # source_id 설정 (엑셀 파일명으로 출처 기록)
                source_id = exam.file_name
                
                # 제목 추출 (한국어/영어) - 언어별로 처리
                title_ko = None
                title_en = None
                
                if '제목' in df.columns:
                    title_ko = str(row['제목']).strip()
                if 'Title' in df.columns:
                    title_en = str(row['Title']).strip()
                
                # null string 체크: 빈 문자열이나 공백만 있는 경우 None으로 설정
                if title_ko and not title_ko.strip():
                    title_ko = None
                if title_en and not title_en.strip():
                    title_en = None
                
                # 동일한 출처 + 동일한 제목인 기존 문제 찾기 (재가져오기 시 중복 방지)
                existing_question_info = None
                if title_ko:
                    key = f"{source_id}:{title_ko}"
                    if key in existing_questions_by_source_and_title:
                        existing_question_info = existing_questions_by_source_and_title[key]
                elif title_en:
                    key = f"{source_id}:{title_en}"
                    if key in existing_questions_by_source_and_title:
                        existing_question_info = existing_questions_by_source_and_title[key]

                if '제목' in df.columns:
                    title = str(row['제목']).strip()
                elif 'Title' in df.columns:
                    title = str(row['Title']).strip()
                else:
                    # 두 번째 컬럼을 제목으로 가정
                    title = str(row.iloc[1]).strip()

                if '문제 내용' in df.columns:
                    content = str(row['문제 내용'])
                elif 'Content' in df.columns:
                    content = str(row['Content'])
                else:
                    # 세 번째 컬럼을 내용으로 가정
                    content = str(row.iloc[2])

                if '정답' in df.columns:
                    answer = str(row['정답'])
                elif 'Answer' in df.columns:
                    answer = str(row['Answer'])
                else:
                    # 네 번째 컬럼을 정답으로 가정
                    answer = str(row.iloc[3])

                # 선택적 필드들 컬럼명 기반 처리
                if '설명' in df.columns and pd.notna(row['설명']):
                    explanation = str(row['설명'])
                elif 'Explanation' in df.columns and pd.notna(row['Explanation']):
                    explanation = str(row['Explanation'])
                elif len(row) > 4 and pd.notna(row.iloc[4]):
                    explanation = str(row.iloc[4])

                # 난이도 처리
                if '난이도' in df.columns and pd.notna(row['난이도']):
                    difficulty = str(row['난이도']).strip()
                    if difficulty == "":
                        difficulty = None
                elif 'Difficulty' in df.columns and pd.notna(row['Difficulty']):
                    difficulty = str(row['Difficulty']).strip()
                    if difficulty == "":
                        difficulty = None
                elif len(row) > 5 and pd.notna(row.iloc[5]):
                    difficulty = str(row.iloc[5]).strip()
                    if difficulty == "":
                        difficulty = None

                if 'URL' in df.columns and pd.notna(row['URL']):
                    url = str(row['URL'])
                elif len(row) > 6 and pd.notna(row.iloc[6]):
                    url = str(row.iloc[6])

                # 그룹ID 처리
                if '그룹ID' in df.columns and pd.notna(row['그룹ID']):
                    group_id = str(row['그룹ID']).strip()
                    if group_id == "":
                        group_id = None
                elif 'Group ID' in df.columns and pd.notna(row['Group ID']):
                    group_id = str(row['Group ID']).strip()
                    if group_id == "":
                        group_id = None
                elif len(row) > 7 and pd.notna(row.iloc[7]):
                    group_id = str(row.iloc[7]).strip()
                    if group_id == "":
                        group_id = None

                # 기존 문제 업데이트 또는 새 문제 생성
                if existing_question_info:
                    # 동일한 파일 + 동일한 제목인 경우 → 기존 문제 업데이트
                    question = existing_question_info['question']
                    
                    # 문제 내용 업데이트
                    if title_ko:
                        question.title_ko = title_ko
                    if title_en:
                        question.title_en = title_en
                    if content:
                        question.content_ko = content
                    if answer:
                        question.answer_ko = answer
                    if explanation:
                        question.explanation_ko = explanation
                    
                    # 난이도, URL, 그룹ID 업데이트
                    if difficulty is not None:
                        question.difficulty = normalize_difficulty(difficulty)
                    if url:
                        question.url = url
                    if group_id:
                        question.group_id = group_id
                    
                    question.save()
                    
                    logger.info(f"[IMPORT_FROM_CONNECTED_FILE] 기존 문제 업데이트 완료: {question.id} (제목: {title})")
                    stats['updated'] += 1
                    
                else:
                    # 새로운 문제인 경우 → 새로 생성
                    normalized_difficulty = None
                    if difficulty is not None:
                        normalized_difficulty = normalize_difficulty(difficulty)

                    question = Question.objects.create(
                        csv_id=csv_id,      # 엑셀의 문제 순서 번호
                        source_id=source_id, # 엑셀 파일명 (출처 식별용)
                        difficulty=normalized_difficulty,
                        url=url,
                        group_id=group_id
                    )

                    # 다국어 필드 설정 (한국어 사용자이므로 한국어 필드에 값 설정)
                    if title_ko:
                        question.title_ko = title_ko
                    if title_en:
                        question.title_en = title_en
                    if content:
                        question.content_ko = content
                    if answer:
                        question.answer_ko = answer
                    if explanation:
                        question.explanation_ko = explanation
                    
                    question.save()

                    # 번역은 나중에 배치로 처리하므로 여기서는 건너뛰기
                    logger.info(f"[IMPORT_FROM_CONNECTED_FILE] 새 문제 생성 완료: {question.id} (제목: {title}, 번역은 배치로 처리 예정)")

                    # 시험에 문제 추가
                    max_order = ExamQuestion.objects.filter(exam=exam).aggregate(models.Max('order'))['order__max'] or 0
                    ExamQuestion.objects.create(exam=exam, question=question, order=max_order + 1)

                    stats['imported'] += 1

            except Exception as e:
                stats['errors'] += 1
                stats['error_details'].append(f'행 {index + 2}: {str(e)}')
                continue

        # 시험의 총 문제 수 업데이트
        exam.total_questions = ExamQuestion.objects.filter(exam=exam).count()
        exam.save()
        
        # 번역이 필요한 문제들만 선별하여 번역 처리
        try:
            from ..utils.multilingual_utils import process_large_question_batch
            
            # 번역이 필요한 문제들만 선별
            questions_needing_translation = []
            
            # 새로 추가된 문제들 (번역 필요)
            if stats['imported'] > 0:
                new_questions = Question.objects.filter(
                    examquestion__exam=exam,
                    source_id=source_id  # 현재 파일에서 추가된 문제들
                ).order_by('-id')[:stats['imported']]
                questions_needing_translation.extend(new_questions)
                logger.info(f"[IMPORT_FROM_CONNECTED_FILE] 새로 추가된 {len(new_questions)}개 문제 번역 대상")
            
            # 업데이트된 문제들 중 번역이 필요한 경우 (내용이 변경된 경우)
            if stats['updated'] > 0:
                # 업데이트된 문제들은 이미 existing_questions에 있음
                # 여기서는 간단히 처리하고, 필요시 더 정교한 로직 추가 가능
                logger.info(f"[IMPORT_FROM_CONNECTED_FILE] 업데이트된 {stats['updated']}개 문제는 번역 상태 확인 필요")
            
            # 번역이 필요한 문제가 있는 경우에만 번역 수행
            if questions_needing_translation:
                logger.info(f"[IMPORT_FROM_CONNECTED_FILE] {len(questions_needing_translation)}개 문제 배치 번역 시작")
                
                # 배치 번역 수행
                translation_result = process_large_question_batch(questions_needing_translation, request.user)
                
                logger.info(f"[IMPORT_FROM_CONNECTED_FILE] 배치 번역 완료: {translation_result['successful']}/{translation_result['total_translations']} 성공")
                
                if translation_result['errors']:
                    logger.warning(f"[IMPORT_FROM_CONNECTED_FILE] 번역 중 일부 오류 발생: {len(translation_result['errors'])}개")
                    for error in translation_result['errors'][:5]:  # 처음 5개만 로그
                        logger.warning(f"[IMPORT_FROM_CONNECTED_FILE] 번역 오류: {error}")
            else:
                logger.info(f"[IMPORT_FROM_CONNECTED_FILE] 번역이 필요한 문제가 없습니다.")
                        
        except Exception as e:
            logger.error(f"[IMPORT_FROM_CONNECTED_FILE] 배치 번역 처리 실패: {e}")
            # 번역 실패해도 문제 가져오기는 계속 진행

        # 최종 결과 로그 및 응답
        logger.info(f"[IMPORT_FROM_CONNECTED_FILE] 가져오기 완료 - 총 {stats['total_rows']}개 행 처리")
        logger.info(f"[IMPORT_FROM_CONNECTED_FILE] 결과: 새로 추가 {stats['imported']}개, 업데이트 {stats['updated']}개, 건너뛰기 {stats['skipped']}개, 오류 {stats['errors']}개")
        
        return Response({
            'message': '연결된 파일로부터 문제 가져오기 완료',
            'stats': stats,
            'note': '동일한 출처(동일한 source_id) + 동일한 제목인 경우 기존 문제가 업데이트되었습니다.'
        })

    except Exam.DoesNotExist:
        return Response({'error': '시험을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'가져오기 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def continue_exam(request, exam_id):
    """이어풀기 - 기존 시험 결과에 추가 제출"""
    try:
        exam = Exam.objects.get(id=exam_id)
        previous_result_id = request.data.get('previous_result_id')

        if not previous_result_id:
            return Response({'error': '이전 시험 결과 ID가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            previous_result = ExamResult.objects.get(id=previous_result_id)
        except ExamResult.DoesNotExist:
            return Response({'error': '이전 시험 결과를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        # 이미 푼 문제들 확인
        answered_question_ids = set()
        for detail in previous_result.examresultdetail_set.all():
            answered_question_ids.add(detail.question.id)

        # 아직 풀지 않은 문제들 찾기 (무시된 문제 제외)
        remaining_questions = []
        ignored_question_ids = set()
        if request.user.is_authenticated:
            ignored_question_ids = set(
                IgnoredQuestion.objects.filter(user=request.user)
                .values_list('question_id', flat=True)
            )
        
        for exam_question in exam.examquestion_set.all():
            if (exam_question.question.id not in answered_question_ids and 
                exam_question.question.id not in ignored_question_ids):
                remaining_questions.append(exam_question.question)

        if not remaining_questions:
            return Response({'error': '이미 모든 문제를 풀었습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 기존 결과에 남은 문제들 추가
        new_answers = request.data.get('answers', [])
        correct_count = previous_result.correct_count
        total_score = previous_result.total_score + len(new_answers)

        # 새로운 답안들 처리
        for answer_data in new_answers:
            question_id = answer_data.get('question_id')
            user_answer = answer_data.get('answer', '')

            try:
                question = Question.objects.get(id=question_id)

                # 정답 판정 로직 개선 - 사용자 언어에 맞는 정답 필드 사용
                # 사용자의 언어 설정 확인
                from quiz.utils.multilingual_utils import BASE_LANGUAGE
                user_language = BASE_LANGUAGE  # 기본값
                if request.user.is_authenticated and hasattr(request.user, 'profile'):
                    user_language = request.user.profile.language or BASE_LANGUAGE
                
                # 언어에 맞는 정답 필드 선택
                from quiz.utils.multilingual_utils import LANGUAGE_KO, LANGUAGE_EN, LANGUAGE_ES, LANGUAGE_ZH, LANGUAGE_JA
                if user_language == LANGUAGE_KO and question.answer_ko:
                    correct_answer = question.answer_ko.lower().strip()
                elif user_language == LANGUAGE_EN and question.answer_en:
                    correct_answer = question.answer_en.lower().strip()
                elif user_language == LANGUAGE_ES and getattr(question, 'answer_es', None):
                    correct_answer = getattr(question, 'answer_es', '').lower().strip()
                elif user_language == LANGUAGE_ZH and getattr(question, 'answer_zh', None):
                    correct_answer = getattr(question, 'answer_zh', '').lower().strip()
                elif user_language == LANGUAGE_JA and getattr(question, 'answer_ja', None):
                    correct_answer = getattr(question, 'answer_ja', '').lower().strip()
                else:
                    # 폴백: 사용 가능한 언어의 정답 필드 사용
                    correct_answer = (
                        question.answer_ko or 
                        question.answer_en or 
                        getattr(question, 'answer_es', None) or 
                        getattr(question, 'answer_zh', None) or 
                        getattr(question, 'answer_ja', None) or 
                        ''
                    ).lower().strip()
                
                user_answer_clean = user_answer.lower().strip()

                # 빈 답안이지만 'Y' 또는 'N' 상태인 경우 처리
                is_correct = False
                if user_answer_clean in ['y', 'n']:
                    # 'Y'는 정답으로 처리, 'N'은 오답으로 처리
                    is_correct = (user_answer_clean == 'y')
                elif user_answer_clean == '':
                    # 빈 답안은 오답으로 처리
                    is_correct = False
                else:
                    # 여러 줄 정답 처리
                    correct_answers = [ans.strip() for ans in correct_answer.split('\n') if ans.strip()]

                    # 정확한 일치 또는 부분 일치 확인
                    if correct_answer == user_answer_clean:
                        is_correct = True
                    else:
                        # 여러 줄 정답 중 하나라도 일치하는지 확인
                        for correct_ans in correct_answers:
                            if correct_ans == user_answer_clean:
                                is_correct = True
                                break
                            # 부분 일치도 확인 (정답의 일부가 포함되어 있는지)
                            elif correct_ans in user_answer_clean or user_answer_clean in correct_ans:
                                is_correct = True
                                break

                # 디버깅 로그 추가
                if question:
                    question_title = get_localized_field(question, 'title', user_language, 'Unknown')
                    print(f"정답 판정: 문제={question_title}")
                else:
                    print(f"정답 판정: 문제=제목 없음")
                print(f"  사용자언어: {user_language}")
                print(f"  선택된정답필드: '{correct_answer}'")
                print(f"  원본정답_ko: '{question.answer_ko}'")
                print(f"  원본정답_en: '{question.answer_en}'")
                print(f"  사용자 답안: '{user_answer}'")
                print(f"  정답 여부: {is_correct}")

                if is_correct:
                    correct_count += 1

                # 결과 상세 저장
                ExamResultDetail.objects.create(
                    result=previous_result,
                    question=question,
                    user_answer=user_answer,
                    is_correct=is_correct
                )

            except Question.DoesNotExist:
                continue

        # 기존 결과 업데이트
        previous_result.correct_count = correct_count
        previous_result.total_score = total_score
        previous_result.wrong_count = total_score - correct_count
        previous_result.score = correct_count
        previous_result.completed_at = timezone.now()  # 완료 시간을 현재 시간으로 업데이트
        previous_result.save()

        # 로그인한 사용자인 경우 StudyTaskProgress 업데이트
        if request.user.is_authenticated:
            try:
                # 이 시험과 연결된 모든 StudyTask 찾기
                study_tasks = StudyTask.objects.filter(exam=exam)

                for study_task in study_tasks:
                    # 해당 사용자의 진행률 계산
                    if exam.total_questions > 0:
                        progress_percentage = (correct_count / exam.total_questions) * 100
                    else:
                        progress_percentage = 0

                    # StudyTaskProgress 업데이트 또는 생성
                    progress_obj, created = StudyTaskProgress.objects.get_or_create(
                        user=request.user,
                        study_task=study_task,
                        defaults={'progress': progress_percentage}
                    )

                    if not created:
                        # 기존 기록이 있으면 진행률 업데이트 (더 높은 값으로)
                        if progress_percentage > progress_obj.progress:
                            progress_obj.progress = progress_percentage
                            progress_obj.save()

                    print(f"StudyTaskProgress 업데이트 (continue): {request.user.username} - {study_task.name} - {progress_percentage}%")

            except Exception as e:
                print(f"StudyTaskProgress 업데이트 중 오류 (continue): {str(e)}")

        result_serializer = ExamResultSerializer(previous_result)
        return Response(result_serializer.data, status=status.HTTP_200_OK)

    except Exam.DoesNotExist:
        return Response({'error': '시험을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'이어풀기 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def retake_exam(request, exam_id):
    """시험 재응시 버전 생성"""
    try:
        original_exam = Exam.objects.get(id=exam_id)

        # 다음 버전 번호 계산
        latest_version = Exam.objects.filter(original_exam=original_exam).order_by('-version_number').first()
        next_version = (latest_version.version_number + 1) if latest_version else 1

        # 새로운 시험 생성 (동일한 문제로)
        new_exam = Exam.objects.create(
            total_questions=original_exam.total_questions,
            original_exam=original_exam,
            version_number=next_version,
            is_original=False,
            created_by=request.user if request.user.is_authenticated else None
        )
        
        # 다국어 필드 설정 (모든 언어 필드 복사)
        from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
        for lang in SUPPORTED_LANGUAGES:
            setattr(new_exam, f'title_{lang}', getattr(original_exam, f'title_{lang}', None))
            setattr(new_exam, f'description_{lang}', getattr(original_exam, f'description_{lang}', None))
        new_exam.created_language = original_exam.created_language
        new_exam.save()

        # 무시된 문제 제외하고 문제 복사
        ignored_question_ids = set()
        if request.user.is_authenticated:
            ignored_question_ids = set(
                IgnoredQuestion.objects.filter(user=request.user)
                .values_list('question_id', flat=True)
            )
        
        question_count = 0
        for exam_question in original_exam.examquestion_set.all():
            # 무시된 문제는 제외
            if exam_question.question.id not in ignored_question_ids:
                ExamQuestion.objects.create(
                    exam=new_exam,
                    question=exam_question.question,
                    order=exam_question.order
                )
                question_count += 1
        
        # 실제 문제 수로 업데이트
        new_exam.total_questions = question_count
        new_exam.save()

        serializer = ExamSerializer(new_exam, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    except Exam.DoesNotExist:
        return Response({'error': '시험을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def retake_wrong_questions(request, exam_id):
    """틀린문제만 재시험 버전 생성"""
    try:
        original_exam = Exam.objects.get(id=exam_id)

        # 모든 시험 결과에서 틀린 문제들 찾기 (누적 기준)
        all_results = ExamResult.objects.filter(exam=original_exam)
        wrong_questions = []

        # 현재 사용자가 무시한 문제들 가져오기
        ignored_question_ids = set()
        if request.user.is_authenticated:
            ignored_question_ids = set(
                IgnoredQuestion.objects.filter(user=request.user)
                .values_list('question_id', flat=True)
            )

        for result in all_results:
            for detail in result.examresultdetail_set.filter(is_correct=False):
                # 무시된 문제는 제외
                if detail.question.id not in ignored_question_ids and detail.question not in wrong_questions:
                    wrong_questions.append(detail.question)

        if not wrong_questions:
            return Response({'error': '틀린 문제가 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 다음 버전 번호 계산
        latest_version = Exam.objects.filter(original_exam=original_exam).order_by('-version_number').first()
        next_version = (latest_version.version_number + 1) if latest_version else 1

        # 새로운 시험 생성 (틀린 문제만)
        new_exam = Exam.objects.create(
            total_questions=len(wrong_questions),
            original_exam=original_exam,
            version_number=next_version,
            is_original=False,
            created_by=request.user if request.user.is_authenticated else None
        )
        
        # 다국어 필드 설정 (틀린문제만 표시, 모든 언어에 대해 설정)
        user_lang = get_user_language(request)
        from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
        # 원본 제목을 각 언어로 가져와서 접미사 추가
        title_translations = {
            'ko': '틀린문제만',
            'en': 'Wrong Questions Only',
            'es': 'Solo Preguntas Incorrectas',
            'zh': '仅错误问题',
            'ja': '間違った問題のみ'
        }
        for lang in SUPPORTED_LANGUAGES:
            original_title_lang = get_localized_field(original_exam, 'title', lang, 'Unknown')
            suffix = title_translations.get(lang, title_translations['en'])
            setattr(new_exam, f'title_{lang}', f"{original_title_lang} - {suffix}")
            # 설명은 원본 그대로 복사
            setattr(new_exam, f'description_{lang}', getattr(original_exam, f'description_{lang}', None))
        new_exam.created_language = original_exam.created_language
        new_exam.save()

        # 틀린 문제들만 복사
        for i, question in enumerate(wrong_questions):
            ExamQuestion.objects.create(
                exam=new_exam,
                question=question,
                order=i + 1
            )

        serializer = ExamSerializer(new_exam, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    except Exam.DoesNotExist:
        return Response({'error': '시험을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def submit_exam(request):
    """
    시험 제출
    
    핵심 원칙: 모든 문제 통계와 공부시간 통계는 End 버튼을 눌러 통계가 잡힐 때 처리되어야 한다
    - 화면를 열 때마다 통계를 계산하는 것은 비정상적인 접근
    - 시험 완료 시에만 통계 데이터를 생성하고 업데이트
    - StudyTaskProgress, StudyProgressRecord 등 모든 통계 테이블은 이 시점에서 처리
    """
    import traceback
    logger.info(f"[SUBMIT_EXAM] 시험 제출 시작")
    logger.info(f"[SUBMIT_EXAM] 요청 데이터: {request.data}")
    
    try:
        exam_id = request.data.get('exam_id')
        answers = request.data.get('answers', [])
        
        # answers가 문자열인 경우 JSON 파싱
        if isinstance(answers, str):
            import json
            try:
                answers = json.loads(answers)
            except json.JSONDecodeError:
                return Response({'error': '답안 데이터 형식이 올바르지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        if not exam_id:
            return Response({'error': '시험 ID가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            exam = Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            return Response({'error': '시험을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        # 정답 개수 계산
        correct_count = 0
        total_questions = len(answers)
        
        # 전체 시험 소요시간 계산
        total_elapsed_seconds = request.data.get('elapsed_seconds', 0)

        # Voice Interview 모드 여부 확인
        is_voice_interview = request.data.get('is_voice_interview', False)

        # 원본이 아닌 시험인지 확인
        is_non_original_exam = not exam.is_original
        
        # 모든 시험에 대해 ExamResult 생성 (원본이든 복사본이든)
        exam_result = ExamResult.objects.create(
            exam=exam,
            user=request.user if request.user.is_authenticated else None,
            total_score=total_questions,
            correct_count=0,
            wrong_count=0,
            score=0,
            elapsed_seconds=total_elapsed_seconds,  # 전체 시험 소요시간 저장
            completed_at=timezone.now(),
            is_voice_interview=is_voice_interview  # Voice Interview 모드 여부 저장
        )
        
        # 캐시 무효화 (ExamCacheManager 사용)
        try:
            from ..utils.cache_utils import ExamCacheManager
            # 시험 결과 관련 캐시 무효화
            ExamCacheManager.invalidate_exam_cache(str(exam.id))
            if request.user.is_authenticated:
                ExamCacheManager.invalidate_user_exam_cache(request.user.id)
            logger.info(f"[SUBMIT_EXAM] ExamCacheManager를 통한 캐시 무효화 완료: {exam.id}")
        except Exception as e:
            logger.error(f"[SUBMIT_EXAM] ExamCacheManager 캐시 무효화 실패: {e}")
            # 폴백: 기존 방식으로 캐시 무효화
            try:
                if hasattr(cache, 'delete_pattern'):
                    cache.delete_pattern("exams_*")
                    cache.delete_pattern("exam_results_*")
                    logger.info("[SUBMIT_EXAM] Redis 패턴 기반 폴백 캐시 무효화 완료")
                else:
                    cache.delete("exams_anonymous")
                    if request.user.is_authenticated:
                        cache.delete(f"exams_{request.user.id}")
                    cache.delete("exam_results_anonymous")
                    if request.user.is_authenticated:
                        cache.delete(f"exam_results_{request.user.id}")
                    logger.info("[SUBMIT_EXAM] 개별 키 기반 폴백 캐시 무효화 완료")
            except Exception as e2:
                logger.error(f"[SUBMIT_EXAM] 폴백 캐시 무효화도 실패: {e2}")

        # 각 답안 처리
        for answer_data in answers:
            question_id = answer_data.get('question_id')
            user_answer = answer_data.get('answer', '')
            elapsed_seconds = answer_data.get('elapsed_seconds', 0)  # 문제별 소요시간 추가
            evaluation = answer_data.get('evaluation', '')  # Voice Interview 평가 내용

            try:
                question = Question.objects.get(id=question_id)

                # 정답 판정 로직 개선 - 사용자 언어에 맞는 정답 필드 사용
                # 사용자의 언어 설정 확인
                from quiz.utils.multilingual_utils import BASE_LANGUAGE
                user_language = BASE_LANGUAGE  # 기본값
                if request.user.is_authenticated and hasattr(request.user, 'profile'):
                    user_language = request.user.profile.language or BASE_LANGUAGE
                
                # 언어에 맞는 정답 필드 선택 (폴백 포함) - 모든 언어 동일하게 처리
                from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
                correct_answer = None
                
                # 사용자 언어 필드 확인
                if hasattr(question, f'answer_{user_language}'):
                    answer_value = getattr(question, f'answer_{user_language}', None)
                    if answer_value:
                        correct_answer = answer_value.lower().strip()
                
                # 사용자 언어 필드가 없으면 기본 언어 필드 확인
                if not correct_answer:
                    from quiz.utils.multilingual_utils import BASE_LANGUAGE
                    if hasattr(question, f'answer_{BASE_LANGUAGE}'):
                        answer_value = getattr(question, f'answer_{BASE_LANGUAGE}', None)
                        if answer_value:
                            correct_answer = answer_value.lower().strip()
                
                # 기본 언어도 없으면 다른 언어 중 하나라도 사용
                if not correct_answer:
                    for lang in SUPPORTED_LANGUAGES:
                        if hasattr(question, f'answer_{lang}'):
                            answer_value = getattr(question, f'answer_{lang}', None)
                            if answer_value:
                                correct_answer = answer_value.lower().strip()
                                break
                
                if not correct_answer:
                    correct_answer = ''
                
                user_answer_clean = user_answer.lower().strip()

                # is_correct 변수 초기화
                is_correct = False

                # 빈 답안은 오답으로 처리
                if user_answer_clean == '':
                    is_correct = False
                else:
                    # Y/N 문제인지 확인
                    if correct_answer in ['y', 'n'] and user_answer_clean in ['y', 'n']:
                        # Y/N 문제인 경우 정답과 사용자 답안을 직접 비교
                        is_correct = (correct_answer == user_answer_clean)
                    else:
                        # 일반 문제 처리
                        # 여러 줄 정답 처리
                        correct_answers = [ans.strip() for ans in correct_answer.split('\n') if ans.strip()]

                        # 정확한 일치 또는 부분 일치 확인
                        if correct_answer == user_answer_clean:
                            is_correct = True
                        else:
                            # 여러 줄 정답 중 하나라도 일치하는지 확인
                            for correct_ans in correct_answers:
                                if correct_ans == user_answer_clean:
                                    is_correct = True
                                    break
                                # 부분 일치도 확인 (정답의 일부가 포함되어 있는지)
                                elif correct_ans in user_answer_clean or user_answer_clean in correct_ans:
                                    is_correct = True
                                    break

                # 디버깅 로그 추가 (로거 사용)
                if question:
                    question_title = get_localized_field(question, 'title', user_language, 'Unknown')
                    logger.debug(f"정답 판정: 문제={question_title}, 사용자언어={user_language}, 선택된정답필드='{correct_answer}', 원본정답_ko='{question.answer_ko}', 원본정답_en='{question.answer_en}', 사용자답안='{user_answer}', 정답여부={is_correct}, 소요시간={elapsed_seconds}초")
                else:
                    logger.debug(f"정답 판정: 문제=제목 없음, 사용자언어={user_language}, 선택된정답필드='{correct_answer}', 원본정답_ko='None', 원본정답_en='None', 사용자답안='{user_answer}', 정답여부={is_correct}, 소요시간={elapsed_seconds}초")

                if is_correct:
                    correct_count += 1

                # 원본이 아닌 시험인 경우 소스 시험에만 저장 (중복 방지)
                if not exam.is_original:
                    exam_title = get_localized_field(exam, 'title', user_language, 'Unknown')
                    logger.info(f"[SUBMIT_EXAM] 복사한 시험 '{exam_title}' - 소스 시험에도 결과 반영")
                    
                    # 해당 문제의 원본 시험 찾기
                    original_exam = None
                    
                    # 1. 복사한 시험의 경우 original_exam 필드 사용
                    if exam.original_exam:
                        original_exam = exam.original_exam
                        original_title = get_localized_field(original_exam, 'title', user_language, 'Unknown')
                        logger.info(f"[SUBMIT_EXAM] original_exam 필드로 원본 시험 찾음: {original_title}")
                    else:
                        # 2. 추천 시험인 경우 기존 로직 사용
                        if (
            (exam.title_ko and "Today's Quizzes for" in exam.title_ko) or
            (exam.title_en and "Today's Quizzes for" in exam.title_en)
        ):
                            # 문제의 group_id를 통해 원본 시험 찾기 시도
                            if question.group_id:
                                try:
                                    # "Today's Quizzes for" 시험인 경우 현재 사용자의 시험만 찾기
                                    if "Today's Quizzes for" in question.group_id:
                                        username = question.group_id.replace("Today's Quizzes for ", "")
                                        original_exam = Exam.objects.filter(
                                            title=question.group_id,
                                            created_by__username=username
                                        ).order_by('-created_at').first()
                                    else:
                                        # 일반적인 경우 - group_id가 원본 시험 제목인 경우
                                        # 예: "NeetCode 150", "LeetCode Dev", "Staff_Leadership" 등
                                        original_exam = Exam.objects.filter(
                                            title_ko=question.group_id,
                                            is_original=True
                                        ).first()
                                        
                                        if not original_exam:
                                            original_exam = Exam.objects.filter(
                                                title_en=question.group_id,
                                                is_original=True
                                            ).first()
                                    
                                    if original_exam:
                                        original_title = get_localized_field(original_exam, 'title', user_language, 'Unknown')
                                        logger.info(f"[SUBMIT_EXAM] group_id '{question.group_id}'로 원본 시험 찾음: {original_title}")
                                except Exception as e:
                                    logger.error(f"[SUBMIT_EXAM] group_id로 원본 시험 찾기 실패: {e}")
                                    pass
                            
                            # group_id로 찾지 못한 경우, 문제가 속한 다른 시험들 중에서 찾기
                            if not original_exam:
                                # 1. 원본 시험(is_original=True)을 우선 찾기
                                for exam_question in question.examquestion_set.all():
                                    if (
                                        (exam_question.exam.title_ko != exam.title_ko and exam.title_ko) or
                                        (exam_question.exam.title_en != exam.title_en and exam.title_en)
                                    ):  # 현재 시험이 아닌 다른 시험
                                        if exam_question.exam.is_original:
                                            original_exam = exam_question.exam
                                            original_title = get_localized_field(original_exam, 'title', user_language, 'Unknown')
                                            logger.info(f"[SUBMIT_EXAM] is_original=True인 원본 시험 찾음: {original_title}")
                                            break
                                
                                # 2. 원본 시험이 없으면 추천 시험이 아닌 시험 찾기
                                if not original_exam:
                                    for exam_question in question.examquestion_set.all():
                                        if (
                                            (exam_question.exam.title_ko != exam.title_ko and exam.title_ko) or
                                            (exam_question.exam.title_en != exam.title_en and exam.title_en)
                                        ):  # 현재 시험이 아닌 다른 시험
                                            if not (
            (exam_question.exam.title_ko and "Today's Quizzes for" in exam_question.exam.title_ko) or
            (exam_question.exam.title_en and "Today's Quizzes for" in exam_question.exam.title_en)
        ):
                                                original_exam = exam_question.exam
                                                original_title = get_localized_field(original_exam, 'title', user_language, 'Unknown')
                                                logger.info(f"[SUBMIT_EXAM] 추천 시험이 아닌 원본 시험 찾음: {original_title}")
                                                break
                                
                                # 3. 여전히 찾지 못한 경우, 첫 번째 다른 시험을 선택
                                if not original_exam:
                                    for exam_question in question.examquestion_set.all():
                                        if (
                                            (exam_question.exam.title_ko != exam.title_ko and exam.title_ko) or
                                            (exam_question.exam.title_en != exam.title_en and exam.title_en)
                                        ):
                                            original_exam = exam_question.exam
                                            original_title = get_localized_field(original_exam, 'title', user_language, 'Unknown')
                                            logger.info(f"[SUBMIT_EXAM] 첫 번째 다른 시험을 원본으로 선택: {original_title}")
                                            break
                    
                    if original_exam:
                        # 원본 시험의 ExamResult 찾기 (중복 방지)
                        try:
                            # 가장 최근 결과를 가져오기
                            original_result = ExamResult.objects.filter(
                                exam=original_exam,
                                user=request.user if request.user.is_authenticated else None
                            ).order_by('-completed_at').first()
                            
                            if not original_result:
                                # 결과가 없으면 새로 생성
                                original_result = ExamResult.objects.create(
                                    exam=original_exam,
                                    user=request.user if request.user.is_authenticated else None,
                                    score=0,
                                    total_score=0,
                                    correct_count=0,
                                    wrong_count=0,
                                    elapsed_seconds=0,
                                    completed_at=timezone.now()
                                )
                                original_title = get_localized_field(original_exam, 'title', user_language, 'Unknown')
                                logger.info(f"[SUBMIT_EXAM] 원본 시험 '{original_title}'에 새 결과 생성")
                            else:
                                original_title = get_localized_field(original_exam, 'title', user_language, 'Unknown')
                                logger.info(f"[SUBMIT_EXAM] 원본 시험 '{original_title}'의 기존 결과 사용: {original_result.id}")
                                
                        except Exception as e:
                            logger.error(f"[SUBMIT_EXAM] ExamResult 처리 중 오류: {str(e)}")
                            # 오류 발생 시 새로 생성
                            original_result = ExamResult.objects.create(
                                exam=original_exam,
                                user=request.user if request.user.is_authenticated else None,
                                score=0,
                                total_score=0,
                                correct_count=0,
                                wrong_count=0,
                                elapsed_seconds=0,
                                completed_at=timezone.now()
                            )
                        
                        # 원본 시험에도 동일한 결과 상세 저장
                        ExamResultDetail.objects.create(
                            result=original_result,
                            question=question,
                            user_answer=user_answer,
                            is_correct=is_correct,
                            elapsed_seconds=elapsed_seconds,  # 소요시간 추가
                            evaluation=evaluation if is_voice_interview else ''  # Voice Interview 평가 내용
                        )
                        
                        # 원본 시험의 ExamResult 요약 필드들 업데이트
                        if is_correct:
                            original_result.correct_count += 1
                        original_result.total_score += 1
                        original_result.score = original_result.correct_count
                        original_result.wrong_count = original_result.total_score - original_result.correct_count
                        original_result.save()
                        
                        if question:
                            question_title = get_localized_field(question, 'title', user_lang, '제목 없음')
                            original_title = get_localized_field(original_exam, 'title', user_lang, 'Unknown')
                            logger.info(f"[SUBMIT_EXAM] 문제 {question_title}의 결과를 원본 시험 '{original_title}'에도 반영 (요약 필드 업데이트 완료)")
                        else:
                            logger.info(f"[SUBMIT_EXAM] 문제 (제목 없음)의 결과를 원본 시험 '{original_exam.title_ko or original_exam.title_en or 'Unknown'}'에도 반영 (요약 필드 업데이트 완료)")
                    else:
                        if question:
                            question_title = get_localized_field(question, 'title', user_lang, '제목 없음')
                            logger.warning(f"[SUBMIT_EXAM] 문제 {question_title}의 원본 시험을 찾을 수 없음")
                        else:
                            logger.warning(f"[SUBMIT_EXAM] 문제 (제목 없음)의 원본 시험을 찾을 수 없음")
                        
                        # 원본 시험을 찾지 못한 경우, 문제별로 개별적으로 원본 시험 찾기 시도
                        individual_original_exam = None
                        
                        # 1. 문제의 group_id를 통해 원본 시험 찾기
                        if question.group_id:
                            try:
                                individual_original_exam = Exam.objects.filter(
                                    Q(title_ko=question.group_id) | Q(title_en=question.group_id),
                                    is_original=True
                                ).first()
                                if individual_original_exam:
                                    logger.info(f"[SUBMIT_EXAM] 문제별 group_id '{question.group_id}'로 원본 시험 찾음: {individual_original_exam.title_ko or individual_original_exam.title_en or 'Unknown'}")
                            except Exception as e:
                                logger.error(f"[SUBMIT_EXAM] 문제별 group_id로 원본 시험 찾기 실패: {e}")
                        
                        # 2. 문제가 속한 다른 원본 시험들 중에서 찾기
                        if not individual_original_exam:
                            for exam_question in question.examquestion_set.all():
                                if exam_question.exam.is_original and (
                                    (exam_question.exam.title_ko != exam.title_ko and exam.title_ko) or
                                    (exam_question.exam.title_en != exam.title_en and exam.title_en)
                                ):
                                    individual_original_exam = exam_question.exam
                                    logger.info(f"[SUBMIT_EXAM] 문제별 examquestion_set으로 원본 시험 찾음: {individual_original_exam.title_ko or individual_original_exam.title_en or 'Unknown'}")
                                    break
                        
                        # 개별 원본 시험을 찾은 경우 해당 시험에 결과 저장
                        if individual_original_exam:
                            try:
                                # 개별 원본 시험의 ExamResult 찾기 또는 생성
                                individual_result = ExamResult.objects.filter(
                                    exam=individual_original_exam,
                                    user=request.user if request.user.is_authenticated else None
                                ).order_by('-completed_at').first()
                                
                                if not individual_result:
                                    individual_result = ExamResult.objects.create(
                                        exam=individual_original_exam,
                                        user=request.user if request.user.is_authenticated else None,
                                        score=0,
                                        total_score=0,
                                        correct_count=0,
                                        wrong_count=0,
                                        elapsed_seconds=0,
                                        completed_at=timezone.now()
                                    )
                                    logger.info(f"[SUBMIT_EXAM] 개별 원본 시험 '{individual_original_exam.title_ko or individual_original_exam.title_en or 'Unknown'}'에 새 결과 생성")
                                
                                # 개별 원본 시험에 결과 상세 저장
                                ExamResultDetail.objects.create(
                                    result=individual_result,
                                    question=question,
                                    user_answer=user_answer,
                                    is_correct=is_correct,
                                    elapsed_seconds=elapsed_seconds,
                                    evaluation=evaluation if is_voice_interview else ''  # Voice Interview 평가 내용
                                )
                                
                                # 개별 원본 시험의 ExamResult 업데이트
                                if is_correct:
                                    individual_result.correct_count += 1
                                individual_result.total_score += 1
                                individual_result.score = individual_result.correct_count
                                individual_result.wrong_count = individual_result.total_score - individual_result.correct_count
                                individual_result.save()
                                
                                if question:
                                    user_lang = get_user_language(request)
                                    question_title = get_localized_field(question, 'title', user_lang, '제목 없음')
                                    original_title = get_localized_field(individual_original_exam, 'title', user_lang, 'Unknown')
                                    logger.info(f"[SUBMIT_EXAM] 문제 {question_title}의 결과를 개별 원본 시험 '{original_title}'에 반영")
                                else:
                                    logger.info(f"[SUBMIT_EXAM] 문제 (제목 없음)의 결과를 개별 원본 시험 '{individual_original_exam.title_ko or individual_original_exam.title_en or 'Unknown'}'에 반영")
                                
                            except Exception as e:
                                logger.error(f"[SUBMIT_EXAM] 개별 원본 시험 결과 저장 중 오류: {str(e)}")
                                # 오류 발생 시 현재 시험에 저장
                                if exam_result:
                                    ExamResultDetail.objects.create(
                                        result=exam_result,
                                        question=question,
                                        user_answer=user_answer,
                                        is_correct=is_correct,
                                        elapsed_seconds=elapsed_seconds,
                                        evaluation=evaluation if is_voice_interview else ''  # Voice Interview 평가 내용
                                    )
                                    logger.info(f"[SUBMIT_EXAM] 개별 원본 시험 저장 실패로 현재 시험에 저장")
                        else:
                            # 모든 방법으로 원본 시험을 찾지 못한 경우 현재 시험에 결과 저장
                            if exam_result:
                                ExamResultDetail.objects.create(
                                    result=exam_result,
                                    question=question,
                                    user_answer=user_answer,
                                    is_correct=is_correct,
                                    elapsed_seconds=elapsed_seconds,
                                    evaluation=evaluation if is_voice_interview else ''  # Voice Interview 평가 내용
                                )
                                logger.info(f"[SUBMIT_EXAM] 모든 방법으로 원본 시험을 찾지 못해 현재 시험에 저장")
                else:
                    # 일반 시험인 경우 현재 시험에만 저장
                    logger.info(f"[SUBMIT_EXAM] ExamResultDetail 생성 시작: exam_id={exam_id}, question_id={question.id if question else 'None'}, user_answer={user_answer}, is_correct={is_correct}")
                    try:
                        ExamResultDetail.objects.create(
                            result=exam_result,
                            question=question,
                            user_answer=user_answer,
                            is_correct=is_correct,
                            elapsed_seconds=elapsed_seconds,  # 소요시간 추가
                            evaluation=evaluation if is_voice_interview else ''  # Voice Interview 평가 내용
                        )
                        logger.info(f"[SUBMIT_EXAM] ExamResultDetail 생성 완료: result_id={exam_result.id}, question_id={question.id if question else 'None'}")
                    except Exception as e:
                        logger.error(f"[SUBMIT_EXAM] ExamResultDetail 생성 실패: {str(e)}")
                        logger.error(f"[SUBMIT_EXAM] 상세 오류: {traceback.format_exc()}")
                        raise

            except Question.DoesNotExist:
                continue

        # 결과 업데이트 (추천 시험이 아닌 경우에만)
        if exam_result:
            exam_result.correct_count = correct_count
            exam_result.wrong_count = total_questions - correct_count
            exam_result.score = correct_count
            exam_result.save()

        # 로그인한 사용자인 경우 StudyTaskProgress 업데이트
        # 핵심 원칙: 모든 문제 통계와 공부시간 통계는 End 버튼을 눌러 통계가 잡힐 때 처리되어야 한다
        logger.info(f"[SUBMIT_EXAM] 사용자 인증 상태: {request.user.is_authenticated}")
        logger.info(f"[SUBMIT_EXAM] 사용자: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
        
        if request.user.is_authenticated:
            try:
                logger.info(f"[SUBMIT_EXAM] StudyTaskProgress 업데이트 시작")
                # 원본 시험 찾기 - StudyTask에 연결된 시험을 우선적으로 찾기
                target_exam = exam
                
                # 1. 먼저 현재 시험이 어떤 StudyTask에 직접 연결되어 있는지 확인
                connected_study_tasks = StudyTask.objects.filter(exam=exam)
                if connected_study_tasks.exists():
                    logger.info(f"[SUBMIT_EXAM] 현재 시험이 {connected_study_tasks.count()}개의 StudyTask에 직접 연결됨")
                    # 현재 시험을 그대로 사용 (StudyTask에 연결되어 있음)
                    target_exam = exam
                elif not exam.is_original:
                    # 사본/복사 시험인 경우 원본 시험 찾기
                    if exam.original_exam:
                        target_exam = exam.original_exam
                        logger.info(f"[SUBMIT_EXAM] original_exam 필드로 원본 시험 찾음: {target_exam.title_ko or target_exam.title_en or 'Unknown'}")
                    elif (
            (exam.title_ko and "Today's Quizzes for" in exam.title_ko) or
            (exam.title_en and "Today's Quizzes for" in exam.title_en)
        ):
                        # 추천 시험인 경우 원본 시험 찾기
                        for answer_data in answers:
                            question_id = answer_data.get('question_id')
                            try:
                                question = Question.objects.get(id=question_id)
                                if question.group_id:
                                    try:
                                        target_exam = Exam.objects.get(
                                            Q(title_ko=question.group_id) | Q(title_en=question.group_id)
                                        )
                                        logger.info(f"[SUBMIT_EXAM] group_id로 원본 시험 찾음: {target_exam.title_ko or target_exam.title_en or 'Unknown'}")
                                        break
                                    except Exam.DoesNotExist:
                                        pass
                            except Question.DoesNotExist:
                                continue
                
                # 2. 만약 여전히 target_exam이 현재 시험이고, StudyTask에 연결되지 않았다면
                # 현재 사용자가 속한 스터디의 Task 중에서 해당 시험과 연결된 것 찾기
                if target_exam == exam and not connected_study_tasks.exists():
                    logger.info(f"[SUBMIT_EXAM] 현재 시험이 StudyTask에 직접 연결되지 않음. 대안 방법으로 찾기 시도")
                    
                    # 현재 사용자가 속한 스터디들 확인
                    user_studies = Study.objects.filter(members__user=request.user)
                    logger.info(f"[SUBMIT_EXAM] 사용자가 속한 스터디 수: {user_studies.count()}")
                    
                    for user_study in user_studies:
                        study_title = user_study.title_ko if user_study.title_ko else user_study.title_en or '제목 없음'
                        logger.debug(f"[SUBMIT_EXAM] 스터디 확인: {study_title} (ID: {user_study.id})")
                        for task in user_study.tasks.all():
                            logger.debug(f"[SUBMIT_EXAM]   Task: {task.name} (Exam: {task.exam.title_ko or task.exam.title_en or 'Unknown' if task.exam else 'No Exam'})")
                            if task.exam and (
            (task.exam.title_ko == exam.title_ko and exam.title_ko) or
            (task.exam.title_en == exam.title_en and exam.title_en)
        ):
                                logger.info(f"[SUBMIT_EXAM] 일치하는 Task 발견: {task.name} - {task.exam.title_ko or task.exam.title_en or 'Unknown'}")
                                target_exam = task.exam
                                break
                        if target_exam != exam:
                            break
                    
                    if target_exam != exam:
                        logger.info(f"[SUBMIT_EXAM] target_exam을 '{target_exam.title_ko or target_exam.title_en or 'Unknown'}' (ID: {target_exam.id})로 변경")
                    else:
                        logger.warning(f"[SUBMIT_EXAM] 대안 방법으로도 target_exam을 찾지 못함")
                
                # 원본 시험과 연결된 모든 StudyTask 찾기
                study_tasks = StudyTask.objects.filter(exam=target_exam)
                logger.info(f"[SUBMIT_EXAM] target_exam: {target_exam.title_ko or target_exam.title_en or 'Unknown'} (ID: {target_exam.id})")
                logger.info(f"[SUBMIT_EXAM] 연결된 StudyTask 수: {study_tasks.count()}")
                
                if study_tasks.exists():
                    for study_task in study_tasks:
                        logger.debug(f"[SUBMIT_EXAM] StudyTask: {study_task.name} (ID: {study_task.id})")
                else:
                    logger.warning(f"[SUBMIT_EXAM] target_exam '{target_exam.title_ko or target_exam.title_en or 'Unknown'}'에 연결된 StudyTask가 없습니다!")
                    # 대안: 현재 사용자가 속한 스터디의 Task 중에서 해당 시험과 연결된 것 찾기
                    user_studies = Study.objects.filter(members__user=request.user)
                    alternative_tasks = []
                    for user_study in user_studies:
                        for task in user_study.tasks.all():
                            if task.exam and (
                                (task.exam.title_ko == target_exam.title_ko and target_exam.title_ko) or
                                (task.exam.title_en == target_exam.title_en and target_exam.title_en)
                            ):
                                alternative_tasks.append(task)
                    
                    if alternative_tasks:
                        logger.info(f"[SUBMIT_EXAM] 대안 StudyTask {len(alternative_tasks)}개 발견:")
                        for task in alternative_tasks:
                            study_title = task.study.title_ko if task.study.title_ko else task.study.title_en or '제목 없음'
                            logger.debug(f"[SUBMIT_EXAM]   - {study_title} - {task.name}")
                        study_tasks = alternative_tasks
                    else:
                        logger.warning(f"[SUBMIT_EXAM] 대안 StudyTask도 찾을 수 없습니다!")

                for study_task in study_tasks:
                    # 진행률 계산
                    logger.debug(f"[SUBMIT_EXAM] 진행률 계산 시작 - exam.is_original: {exam.is_original}")
                    logger.debug(f"[SUBMIT_EXAM] correct_count: {correct_count}, total_questions: {total_questions}")
                    
                    if exam.is_original:
                        # 원본 시험인 경우 직접 계산
                        if exam.total_questions > 0:
                            progress_percentage = (correct_count / exam.total_questions) * 100
                            logger.debug(f"[SUBMIT_EXAM] 원본 시험 진행률: {correct_count}/{exam.total_questions} = {progress_percentage:.1f}%")
                        else:
                            progress_percentage = 0
                            logger.debug(f"[SUBMIT_EXAM] 원본 시험 total_questions가 0입니다")
                    else:
                        # 사본/복사 시험인 경우 원본 시험 기준으로 계산
                        logger.debug(f"[SUBMIT_EXAM] 사본 시험 - target_exam.total_questions: {target_exam.total_questions}")
                        if target_exam.total_questions > 0:
                            # 사본 시험의 정답률을 원본 시험 기준으로 변환
                            # 예: 사본에서 3/5 맞춤, 원본이 10문제면 -> (3/5) * (5/10) * 100 = 30%
                            progress_percentage = (correct_count / total_questions) * (total_questions / target_exam.total_questions) * 100
                            logger.debug(f"[SUBMIT_EXAM] 사본 시험 진행률: ({correct_count}/{total_questions}) * ({total_questions}/{target_exam.total_questions}) * 100 = {progress_percentage:.1f}%")
                        else:
                            progress_percentage = 0
                            logger.debug(f"[SUBMIT_EXAM] target_exam.total_questions가 0입니다")
                    
                    logger.debug(f"[SUBMIT_EXAM] 최종 계산된 진행률: {progress_percentage:.1f}%")

                    # StudyTaskProgress 업데이트 또는 생성
                    # 핵심 원칙: 모든 문제 통계와 공부시간 통계는 End 버튼을 눌러 통계가 잡힐 때 처리되어야 한다
                    # - 화면를 열 때마다 통계를 계산하는 것은 비정상적인 접근
                    # - 시험 완료 시에만 통계 데이터를 생성하고 업데이트
                    logger.info(f"[SUBMIT_EXAM] StudyTaskProgress 생성/업데이트 시작")
                    logger.info(f"[SUBMIT_EXAM] 사용자: {request.user.username}, Task: {study_task.name}, 진행률: {progress_percentage:.1f}%")
                    
                    try:
                        progress_obj, created = StudyTaskProgress.objects.get_or_create(
                            user=request.user,
                            study_task=study_task,
                            defaults={'progress': progress_percentage}
                        )
                        
                        if created:
                            logger.info(f"[SUBMIT_EXAM] StudyTaskProgress 새로 생성됨: {progress_percentage:.1f}%")
                        else:
                            logger.debug(f"[SUBMIT_EXAM] 기존 StudyTaskProgress 발견: {progress_obj.progress:.1f}%")
                            # 기존 기록이 있으면 진행률 업데이트 (더 높은 값으로)
                            if progress_percentage > progress_obj.progress:
                                progress_obj.progress = progress_percentage
                                progress_obj.save()
                                logger.info(f"[SUBMIT_EXAM] StudyTaskProgress 업데이트됨: {progress_percentage:.1f}%")
                            else:
                                logger.debug(f"[SUBMIT_EXAM] 기존 진행률이 더 높아서 업데이트하지 않음")
                        
                        logger.debug(f"[SUBMIT_EXAM] StudyTaskProgress 최종 상태: {progress_obj.progress:.1f}%")
                        
                    except Exception as e:
                        logger.error(f"[SUBMIT_EXAM] StudyTaskProgress 생성/업데이트 실패: {str(e)}")
                        import traceback
                        traceback.print_exc()
                    
                    # StudyTask의 전체 진행률도 업데이트 (사용자별 진행률의 평균)
                    try:
                        # 해당 Task의 모든 사용자 진행률 평균 계산
                        all_user_progress = StudyTaskProgress.objects.filter(study_task=study_task)
                        if all_user_progress.exists():
                            avg_progress = sum([p.progress for p in all_user_progress]) / all_user_progress.count()
                            study_task.progress = avg_progress
                            study_task.save()
                            logger.debug(f"StudyTask 전체 진행률 업데이트: {study_task.name} - {avg_progress:.1f}%")
                    except Exception as e:
                        logger.error(f"StudyTask 전체 진행률 업데이트 중 오류: {str(e)}")

            except Exception as e:
                logger.error(f"StudyTaskProgress 업데이트 중 오류 (submit): {str(e)}")

        # StudyProgressRecord 생성 - Task별 진행률을 포함한 기록 저장
        # 핵심 원칙: 모든 문제 통계와 공부시간 통계는 End 버튼을 눌러 통계가 잡힐 때 처리되어야 한다
        try:
            from quiz.models import StudyProgressRecord
            
            # 현재 사용자가 속한 스터디들 중에서 target_exam과 연결된 Task가 있는 스터디 찾기
            user_studies = Study.objects.filter(members__user=request.user)
            target_study = None
            
            for user_study in user_studies:
                for task in user_study.tasks.all():
                    if task.exam and task.exam.id == target_exam.id:
                        target_study = user_study
                        study_title = target_study.title_ko if target_study.title_ko else target_study.title_en or '제목 없음'
                        print(f"[SUBMIT_EXAM] StudyProgressRecord용 스터디 발견: {study_title}")
                        break
                if target_study:
                    break
            
            if target_study:
                # 현재 사용자의 모든 Task 진행률 수집
                task_progresses = {}
                overall_progress = 0
                total_tasks = 0
                
                for study_task in target_study.tasks.all():
                    try:
                        progress_obj = StudyTaskProgress.objects.get(user=request.user, study_task=study_task)
                        task_progress = progress_obj.progress
                    except StudyTaskProgress.DoesNotExist:
                        task_progress = 0
                    
                    task_progresses[str(study_task.id)] = task_progress
                    overall_progress += task_progress
                    total_tasks += 1
                
                # 전체 진행률 계산 (평균)
                if total_tasks > 0:
                    overall_progress = overall_progress / total_tasks
                
                # StudyProgressRecord 생성
                StudyProgressRecord.objects.create(
                    user=request.user,
                    study=target_study,
                    overall_progress=overall_progress,
                    task_progresses=task_progresses,
                    page_type='exam-completion'  # 시험 완료로 기록
                )
                
                study_title = target_study.title_ko if target_study.title_ko else target_study.title_en or '제목 없음'
                logger.info(f"StudyProgressRecord 생성 완료: {request.user.username} - {study_title} - 전체 진행률: {overall_progress:.1f}%")
            else:
                logger.warning(f"[SUBMIT_EXAM] StudyProgressRecord 생성 실패: target_exam과 연결된 스터디를 찾을 수 없음")
            
        except Exception as e:
            logger.error(f"StudyProgressRecord 생성 중 오류 (submit): {str(e)}")
            import traceback
            traceback.print_exc()

        # 시험 결과 관련 캐시 무효화
        try:
            from django.core.cache import cache
            # 모든 exams 관련 캐시 삭제 (통계가 변경되었으므로)
            cache.delete_pattern("exams_*")
        except AttributeError:
            # 다른 캐시 백엔드의 경우 개별 키 삭제
            cache.delete("exams_anonymous")
            cache.delete("exams_anonymous_true")
            cache.delete("exams_anonymous_false")
            cache.delete("exams_anonymous_all")
            # 관리자 사용자 캐시도 삭제
            cache.delete("exams_1")
            cache.delete("exams_1_true")
            cache.delete("exams_1_false")
            cache.delete("exams_1_all")
            logger.info("시험 제출 후 캐시 무효화 완료 (개별 키 삭제)")
        except Exception as e:
            logger.error(f"시험 제출 후 캐시 무효화 중 오류: {e}")

        # 프론트엔드 캐시 무효화를 위한 응답 헤더 추가
        response_data = {
            'message': '시험 제출 완료',
            'cache_invalidation': {
                'studies': True,  # 스터디 목록 캐시 무효화
                'study_progress': True,  # 스터디 진행률 캐시 무효화
                'exam_results': True,  # 시험 결과 캐시 무효화
                'timestamp': timezone.now().isoformat()  # 캐시 무효화 타임스탬프
            }
        }
        
        # ========================================
        # 🔄 최종 캐시 무효화 (중요!)
        # ========================================
        # 
        # 모든 문제 풀이 결과 저장 완료 후 최종 캐시 무효화
        # 이 시점에서 캐시를 무효화해야 실제 저장된 데이터에 대한 캐시가 정리됩니다.
        #
        # 🎯 최종 캐시 무효화가 필요한 이유:
        # 1. 문제 풀이 결과가 실제로 DB에 저장된 후
        # 2. 통계 데이터가 업데이트된 후
        # 3. 사용자가 다음 조회 시 최신 데이터를 볼 수 있도록
        #
        # 📋 무효화 대상:
        # - 시험 결과 관련 캐시
        # - 문제 통계 관련 캐시
        # - 사용자별 시험 캐시
        # ========================================
        
        # 최종 캐시 무효화 (ExamCacheManager 사용)
        try:
            from ..utils.cache_utils import ExamCacheManager
            
            # 시험 결과 저장 완료 후 관련 캐시 무효화
            ExamCacheManager.invalidate_exam_cache(str(exam.id))
            if request.user.is_authenticated:
                ExamCacheManager.invalidate_user_exam_cache(request.user.id)
            
            logger.info(f"[SUBMIT_EXAM] ✅ 최종 캐시 무효화 완료: 시험={exam.id}, 사용자={request.user.username if request.user.is_authenticated else 'Anonymous'}")
            
        except Exception as e:
            logger.error(f"[SUBMIT_EXAM] ❌ 최종 캐시 무효화 실패: {e}")
            
            # 폴백: Redis 패턴 기반 캐시 무효화
            try:
                if hasattr(cache, 'delete_pattern'):
                    # 시험 결과 저장 완료 후 관련 캐시 무효화
                    cache.delete_pattern("exams_*")
                    cache.delete_pattern("exam_results_*")
                    cache.delete_pattern("question_statistics_*")
                    cache.delete_pattern("statistics_*")
                    logger.info("[SUBMIT_EXAM] ✅ Redis 패턴 기반 최종 캐시 무효화 완료")
                else:
                    # 로컬 캐시 환경에서 개별 키 삭제
                    cache.delete("exams_anonymous")
                    if request.user.is_authenticated:
                        cache.delete(f"exams_{request.user.id}")
                    cache.delete("exam_results_anonymous")
                    if request.user.is_authenticated:
                        cache.delete(f"exam_results_{request.user.id}")
                    logger.info("[SUBMIT_EXAM] ✅ 개별 키 기반 최종 캐시 무효화 완료")
                    
            except Exception as e2:
                logger.error(f"[SUBMIT_EXAM] ❌ 폴백 최종 캐시 무효화도 실패: {e2}")
                logger.warning(f"[SUBMIT_EXAM] 🚨 시험 제출은 완료되었지만 캐시 무효화에 실패했습니다!")
                logger.warning(f"[SUBMIT_EXAM] 🚨 사용자가 다음 조회 시 이전 데이터를 볼 수 있습니다!")

        # 원본이 아닌 시험인 경우 빈 응답, 원본 시험인 경우 결과 반환
        if is_non_original_exam:
            response_data['message'] = '복사한 시험 결과가 소스 시험에 반영되었습니다.'
            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            response_data['exam_result'] = ExamResultSerializer(exam_result).data
            return Response(response_data, status=status.HTTP_201_CREATED)

    except Exception as e:
        error_msg = f'시험 제출 중 오류가 발생했습니다: {str(e)}'
        logger.error(f"[SUBMIT_EXAM] 오류: {error_msg}")
        logger.error(f"[SUBMIT_EXAM] 스택 트레이스: {traceback.format_exc()}")
        return Response({'error': error_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _apply_pagination(results, page, page_size):
    """페이지네이션 적용 공통 함수"""
    try:
        page = int(page)
        page_size = int(page_size)
    except ValueError:
        page = 1
        page_size = page_size if isinstance(page_size, int) else 10

    start = (page - 1) * page_size
    end = start + page_size

    paginated_results = results[start:end]
    
    return paginated_results, page, page_size, results.count()


@api_view(['GET'])
def get_exam_results(request):
    """사용자의 시험 결과 목록 조회 (전체 정보)"""
    import time
    from django.db import connection
    
    try:
        if not request.user.is_authenticated:
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)

        start_time = time.time()
        queries_before = len(connection.queries)
        
        # exam_id 파라미터 처리
        exam_id = request.GET.get('exam_id')
        latest_only = request.GET.get('latest', 'false').lower() == 'true'
        
        # 기본 쿼리셋 최적화
        query_start = time.time()
        results = ExamResult.objects.filter(user=request.user).select_related('exam').only(
            'id', 'exam__id', 'exam__title_ko', 'exam__title_en', 'exam__is_public', 'exam__is_original',
            'score', 'total_score', 'correct_count', 'wrong_count', 
            'completed_at', 'elapsed_seconds'
        )
        
        # exam_id가 있으면 해당 시험의 결과만 필터링
        if exam_id:
            results = results.filter(exam_id=exam_id)
        
        # latest=true이면 가장 최근 결과만 반환
        if latest_only:
            results = results.order_by('-completed_at')[:1]
        else:
            results = results.order_by('-completed_at')
        
        query_time = time.time() - query_start
        queries_after_query = len(connection.queries)
        logger.info(f"[GET_EXAM_RESULTS] 쿼리셋 생성: {queries_after_query - queries_before}개 쿼리, {query_time:.3f}초")

        # latest=true일 때는 페이지네이션 적용하지 않음
        if latest_only:
            # 결과 조회
            fetch_start = time.time()
            results_list = list(results)
            fetch_time = time.time() - fetch_start
            queries_after_fetch = len(connection.queries)
            logger.info(f"[GET_EXAM_RESULTS] 결과 조회: {queries_after_fetch - queries_after_query}개 쿼리, {fetch_time:.3f}초, 결과 수: {len(results_list)}")
            
            # 최적화된 직렬화 (details, wrong_questions 제외)
            serialize_start = time.time()
            data = [{
                'id': str(result.id),
                'exam': {
                    'id': str(result.exam.id),
                    'title': result.exam.title_ko or result.exam.title_en or 'Unknown',
                    'title_ko': result.exam.title_ko,
                    'title_en': result.exam.title_en,
                    'is_public': result.exam.is_public,
                    'is_original': result.exam.is_original,
                    'latest_correct_count': result.correct_count,
                    'latest_total_score': result.total_score
                },
                'score': result.score,
                'total_score': result.total_score,
                'correct_count': result.correct_count,
                'wrong_count': result.wrong_count,
                'completed_at': result.completed_at,
                'elapsed_seconds': result.elapsed_seconds
            } for result in results_list]
            serialize_time = time.time() - serialize_start
            queries_after_serialize = len(connection.queries)
            logger.info(f"[GET_EXAM_RESULTS] 직렬화: {queries_after_serialize - queries_after_fetch}개 쿼리, {serialize_time:.3f}초")
            
            total_time = time.time() - start_time
            total_queries = queries_after_serialize - queries_before
            logger.info(f"[GET_EXAM_RESULTS] 총 시간: {total_time:.3f}초, 총 쿼리: {total_queries}개")

            return Response({
                'results': data,
                'total_count': len(data),
                'page': 1,
                'page_size': len(data),
                'total_pages': 1
            })
        else:
            # 페이지네이션 적용
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
            
            # count 쿼리 최적화 (페이지네이션 전에 먼저 계산)
            count_start = time.time()
            total_count = results.count()
            count_time = time.time() - count_start
            queries_after_count = len(connection.queries)
            logger.info(f"[GET_EXAM_RESULTS] count 쿼리: {queries_after_count - queries_after_query}개 쿼리, {count_time:.3f}초, total_count: {total_count}")
            
            # 페이지네이션 적용
            pagination_start = time.time()
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            paginated_results = list(results[start_index:end_index])
            pagination_time = time.time() - pagination_start
            queries_after_pagination = len(connection.queries)
            logger.info(f"[GET_EXAM_RESULTS] 페이지네이션 조회: {queries_after_pagination - queries_after_count}개 쿼리, {pagination_time:.3f}초, 결과 수: {len(paginated_results)}")

            # 최적화된 직렬화 (details, wrong_questions 제외)
            serialize_start = time.time()
            data = [{
                'id': str(result.id),
                'exam': {
                    'id': str(result.exam.id),
                    'title': result.exam.title_ko or result.exam.title_en or 'Unknown',
                    'title_ko': result.exam.title_ko,
                    'title_en': result.exam.title_en,
                    'is_public': result.exam.is_public,
                    'is_original': result.exam.is_original,
                    'latest_correct_count': result.correct_count,
                    'latest_total_score': result.total_score
                },
                'score': result.score,
                'total_score': result.total_score,
                'correct_count': result.correct_count,
                'wrong_count': result.wrong_count,
                'completed_at': result.completed_at,
                'elapsed_seconds': result.elapsed_seconds
            } for result in paginated_results]
            serialize_time = time.time() - serialize_start
            queries_after_serialize = len(connection.queries)
            logger.info(f"[GET_EXAM_RESULTS] 직렬화: {queries_after_serialize - queries_after_pagination}개 쿼리, {serialize_time:.3f}초")
            
            total_time = time.time() - start_time
            total_queries = queries_after_serialize - queries_before
            logger.info(f"[GET_EXAM_RESULTS] 총 시간: {total_time:.3f}초, 총 쿼리: {total_queries}개, page: {page}, page_size: {page_size}")

            return Response({
                'results': data,
                'total_count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size
            })

    except Exception as e:
        logger.error(f"[GET_EXAM_RESULTS] 오류 발생: {str(e)}", exc_info=True)
        return Response({'error': f'시험 결과 조회 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_exam_results_summary(request):
    """시험 결과 요약 정보만 조회 (점수 계산용) - 최적화된 버전"""
    try:
        if not request.user.is_authenticated:
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)

        # 필요한 필드만 조회 (점수 계산에 필요한 최소 데이터)
        results = ExamResult.objects.filter(user=request.user).select_related('exam').only(
            'id', 'exam__id', 'exam__title_ko', 'exam__title_en', 'score', 'total_score', 'completed_at'
        ).order_by('-completed_at')

        # 페이지네이션 적용
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 100)  # 기본값을 100으로 설정
        paginated_results, page, page_size, total_count = _apply_pagination(results, page, page_size)

        # 간소화된 데이터 구조 (직렬화 오버헤드 최소화)
        data = [{
            'id': str(result.id),
            'exam': {
                'id': str(result.exam.id),
                'title': result.exam.title_ko or result.exam.title_en or 'Unknown',
                'title_ko': result.exam.title_ko,
                'title_en': result.exam.title_en
            },
            'score': result.score,
            'total_score': result.total_score,
            'completed_at': result.completed_at
        } for result in paginated_results]

        return Response({
            'results': data,
            'total_count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size
        })

    except Exception as e:
        return Response({'error': f'시험 결과 요약 조회 중 오류가 발생했습니다: {str(e)}'}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def exam_result_detail(request, result_id):
    """특정 시험 결과 상세 조회"""
    try:
        if not request.user.is_authenticated:
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            result = ExamResult.objects.get(id=result_id, user=request.user)
        except ExamResult.DoesNotExist:
            return Response({'error': '시험 결과를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ExamResultSerializer(result)
        return Response(serializer.data)

    except Exception as e:
        return Response({'error': f'시험 결과 상세 조회 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_voice_interview_results(request, exam_id):
    """특정 시험의 Voice Interview 결과 목록 조회"""
    try:
        if not request.user.is_authenticated:
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            exam = Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            return Response({'error': '시험을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        # 접근 권한 확인
        from ..utils.permissions import get_user_permissions, can_edit_exam
        from ..models import Member
        
        permissions = get_user_permissions(request.user)
        is_admin = permissions['is_admin'] or permissions['has_study_admin_role']
        is_creator = exam.created_by == request.user if exam.created_by else False
        
        # 시험이 포함된 스터디의 멤버인지 확인
        is_study_member = Member.objects.filter(
            user=request.user,
            study__tasks__exam=exam,
            is_active=True
        ).exists()
        
        # 시험을 본 적이 있는지 확인
        has_taken_exam = ExamResult.objects.filter(
            user=request.user,
            exam=exam
        ).exists()
        
        # 권한이 있는 사용자: admin, 생성자, 스터디 멤버는 모든 결과 조회 가능
        # 권한이 없는 사용자: 자신의 결과만 조회 가능
        if is_admin or is_creator or is_study_member:
            # 모든 Voice Interview 결과 조회
            results = ExamResult.objects.filter(
                exam=exam,
                is_voice_interview=True
            ).order_by('-completed_at')
        elif has_taken_exam:
            # 자신의 결과만 조회
            results = ExamResult.objects.filter(
                exam=exam,
                user=request.user,
                is_voice_interview=True
            ).order_by('-completed_at')
        else:
            # 사용자 언어에 맞는 에러 메시지 반환
            user_language = get_user_language(request.user)
            if user_language == LANGUAGE_KO:
                error_msg = '이 시험의 Voice Interview 결과에 접근할 권한이 없습니다.'
            elif user_language == LANGUAGE_EN:
                error_msg = 'You do not have permission to access Voice Interview results for this exam.'
            elif user_language == LANGUAGE_ZH:
                error_msg = '您没有权限访问此考试的语音面试结果。'
            elif user_language == LANGUAGE_ES:
                error_msg = 'No tiene permiso para acceder a los resultados de entrevista por voz de este examen.'
            elif user_language == LANGUAGE_JA:
                error_msg = 'この試験の音声面接結果にアクセスする権限がありません。'
            else:
                error_msg = 'You do not have permission to access Voice Interview results for this exam.'
            return Response({'error': error_msg}, status=status.HTTP_403_FORBIDDEN)

        # 페이지네이션
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        start = (page - 1) * page_size
        end = start + page_size
        paginated_results = results[start:end]

        data = [{
            'id': str(result.id),
            'exam': {
                'id': str(result.exam.id),
                'title': result.exam.title_ko or result.exam.title_en or 'Unknown',
                'title_ko': result.exam.title_ko,
                'title_en': result.exam.title_en,
            },
            'user': {
                'id': str(result.user.id) if result.user else None,
                'username': result.user.username if result.user else 'Anonymous',
                'email': result.user.email if result.user else None,
            },
            'score': result.score,
            'total_score': result.total_score,
            'correct_count': result.correct_count,
            'wrong_count': result.wrong_count,
            'completed_at': result.completed_at,
            'elapsed_seconds': result.elapsed_seconds,
            'accuracy': (result.correct_count / result.total_score * 100) if result.total_score > 0 else 0
        } for result in paginated_results]

        return Response({
            'results': data,
            'total_count': results.count(),
            'page': page,
            'page_size': page_size,
            'total_pages': (results.count() + page_size - 1) // page_size
        })

    except Exception as e:
        return Response({'error': f'Voice Interview 결과 조회 중 오류가 발생했습니다: {str(e)}'}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_voice_interview_result_detail(request, result_id):
    """특정 Voice Interview 결과 상세 조회 (평가 내용 포함)"""
    try:
        if not request.user.is_authenticated:
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            result = ExamResult.objects.get(id=result_id, is_voice_interview=True)
        except ExamResult.DoesNotExist:
            # 사용자 언어에 맞는 에러 메시지 반환
            user_language = get_user_language(request.user)
            if user_language == LANGUAGE_KO:
                error_msg = 'Voice Interview 결과를 찾을 수 없습니다.'
            elif user_language == LANGUAGE_EN:
                error_msg = 'Voice Interview result not found.'
            elif user_language == LANGUAGE_ZH:
                error_msg = '找不到语音面试结果。'
            elif user_language == LANGUAGE_ES:
                error_msg = 'No se encontró el resultado de entrevista por voz.'
            elif user_language == LANGUAGE_JA:
                error_msg = '音声面接結果が見つかりませんでした。'
            else:
                error_msg = 'Voice Interview result not found.'
            return Response({'error': error_msg}, status=status.HTTP_404_NOT_FOUND)

        # 접근 권한 확인
        from ..utils.permissions import get_user_permissions
        from ..models import Member
        
        permissions = get_user_permissions(request.user)
        is_admin = permissions['is_admin'] or permissions['has_study_admin_role']
        is_creator = result.exam.created_by == request.user if result.exam.created_by else False
        is_result_owner = result.user == request.user if result.user else False
        
        # 시험이 포함된 스터디의 멤버인지 확인
        is_study_member = Member.objects.filter(
            user=request.user,
            study__tasks__exam=result.exam,
            is_active=True
        ).exists()
        
        # 권한이 있는 사용자만 접근 가능
        if not (is_admin or is_creator or is_study_member or is_result_owner):
            # 사용자 언어에 맞는 에러 메시지 반환
            user_language = get_user_language(request.user)
            if user_language == LANGUAGE_KO:
                error_msg = '이 Voice Interview 결과에 접근할 권한이 없습니다.'
            elif user_language == LANGUAGE_EN:
                error_msg = 'You do not have permission to access this Voice Interview result.'
            elif user_language == LANGUAGE_ZH:
                error_msg = '您没有权限访问此语音面试结果。'
            elif user_language == LANGUAGE_ES:
                error_msg = 'No tiene permiso para acceder a este resultado de entrevista por voz.'
            elif user_language == LANGUAGE_JA:
                error_msg = 'この音声面接結果にアクセスする権限がありません。'
            else:
                error_msg = 'You do not have permission to access this Voice Interview result.'
            return Response({'error': error_msg}, status=status.HTTP_403_FORBIDDEN)

        # 결과 상세 정보 조회
        details = result.examresultdetail_set.all().order_by('id')
        
        # 정확도 계산
        accuracy = (result.correct_count / result.total_score * 100) if result.total_score > 0 else 0

        result_data = {
            'id': str(result.id),
            'exam': {
                'id': str(result.exam.id),
                'title': result.exam.title_ko or result.exam.title_en or 'Unknown',
                'title_ko': result.exam.title_ko,
                'title_en': result.exam.title_en,
            },
            'score': result.score,
            'total_score': result.total_score,
            'correct_count': result.correct_count,
            'wrong_count': result.wrong_count,
            'completed_at': result.completed_at,
            'elapsed_seconds': result.elapsed_seconds,
            'accuracy': accuracy,
            'details': [{
                'id': str(detail.id),
                'question': {
                    'id': str(detail.question.id) if detail.question else None,
                    'title': detail.question_title or (detail.question.title_ko if detail.question else None) or (detail.question.title_en if detail.question else None) or '제목 없음',
                    'title_ko': detail.question.title_ko if detail.question else None,
                    'title_en': detail.question.title_en if detail.question else None,
                },
                'user_answer': detail.user_answer,
                'is_correct': detail.is_correct,
                'evaluation': detail.evaluation or '',
                'accuracy': detail.result.score / detail.result.total_score * 100 if detail.result.total_score > 0 else 0,
                'elapsed_seconds': detail.elapsed_seconds
            } for detail in details]
        }

        return Response(result_data)

    except Exception as e:
        return Response({'error': f'Voice Interview 결과 상세 조회 중 오류가 발생했습니다: {str(e)}'}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def share_voice_interview_result(request):
    """Voice Interview 결과를 이메일로 공유"""
    try:
        if not request.user.is_authenticated:
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)

        result_id = request.data.get('result_id')
        study_id = request.data.get('study_id')
        member_ids = request.data.get('member_ids', [])

        if not result_id or not study_id or not member_ids:
            return Response({'error': '필수 파라미터가 누락되었습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # study_id를 정수로 변환 (문자열로 전달될 수 있음)
        try:
            study_id = int(study_id) if isinstance(study_id, str) else study_id
        except (ValueError, TypeError):
            return Response({'error': '유효하지 않은 스터디 ID입니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # member_ids가 리스트인지 확인
        if not isinstance(member_ids, list):
            return Response({'error': '멤버 ID는 리스트 형식이어야 합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # member_ids를 정수 리스트로 변환
        try:
            member_ids = [int(mid) if isinstance(mid, str) else mid for mid in member_ids]
        except (ValueError, TypeError):
            return Response({'error': '유효하지 않은 멤버 ID입니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 결과 확인 (exam 관계도 함께 로드)
        try:
            result = ExamResult.objects.select_related('exam').get(id=result_id, is_voice_interview=True)
        except ExamResult.DoesNotExist:
            return Response({'error': 'Voice Interview 결과를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        # exam이 없으면 에러 반환
        if not result.exam:
            return Response({'error': '시험 정보를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        # 스터디 확인
        try:
            study = Study.objects.get(id=study_id)
        except Study.DoesNotExist:
            return Response({'error': '스터디를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        # 멤버 확인 및 이메일 전송
        from ..models import Member
        from ..email_utils import get_email_config
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from django.conf import settings
        import os

        members = Member.objects.filter(
            id__in=member_ids,
            study=study,
            is_active=True
        )

        if not members.exists():
            return Response({'error': '선택한 멤버를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        # 결과 링크 생성
        frontend_host = os.getenv('CURRENT_DOMAIN', 'localhost')
        scheme = 'http' if frontend_host == 'localhost' else 'https'
        result_url = f"{scheme}://{frontend_host}/voice-interview-result/{result_id}"

        # 이메일 설정 (get_email_config()가 이미 환경 변수에서 올바른 값을 가져옴)
        email_config = get_email_config()
        
        # 사용자 언어 설정
        from ..utils.multilingual_utils import (
            get_user_language, SUPPORTED_LANGUAGES,
            LANGUAGE_KO, LANGUAGE_EN, LANGUAGE_ES, LANGUAGE_ZH, LANGUAGE_JA, BASE_LANGUAGE
        )
        user_language = get_user_language(request.user)
        
        # 동적으로 exam 제목 가져오기 (사용자 언어 우선, 폴백 순서 적용)
        exam_title = None
        # 사용자 언어 필드 확인
        if hasattr(result.exam, f'title_{user_language}'):
            exam_title = getattr(result.exam, f'title_{user_language}', None)
        # 사용자 언어 필드가 없으면 기본 언어 필드 확인
        if not exam_title:
            if hasattr(result.exam, f'title_{BASE_LANGUAGE}'):
                exam_title = getattr(result.exam, f'title_{BASE_LANGUAGE}', None)
        # 기본 언어도 없으면 다른 언어 중 하나라도 사용
        if not exam_title:
            for lang in SUPPORTED_LANGUAGES:
                if hasattr(result.exam, f'title_{lang}'):
                    exam_title = getattr(result.exam, f'title_{lang}', None)
                    if exam_title:
                        break
        # 모든 언어 필드가 없으면 기본값 사용
        if not exam_title:
            exam_title = 'Exam' if user_language == BASE_LANGUAGE else '시험'

        # 이메일 제목 설정 (동적 처리)
        subject_templates = {
            LANGUAGE_KO: f"Voice Interview 결과 공유 - {exam_title}",
            LANGUAGE_ZH: f"语音面试结果分享 - {exam_title}",
            LANGUAGE_ES: f"Compartir Resultado de Entrevista por Voz - {exam_title}",
            LANGUAGE_JA: f"音声面接結果の共有 - {exam_title}",
        }
        subject = subject_templates.get(user_language, f"Voice Interview Result Shared - {exam_title}")
        
        # 템플릿 이름 설정 (동적 처리)
        template_names = {
            LANGUAGE_KO: 'share_voice_interview_result_ko.html',
            LANGUAGE_ZH: 'share_voice_interview_result_zh.html',
            LANGUAGE_ES: 'share_voice_interview_result_es.html',
            LANGUAGE_JA: 'share_voice_interview_result_ja.html',
        }
        template_name = template_names.get(user_language, 'share_voice_interview_result_en.html')

        # 템플릿 컨텍스트
        from django.template.loader import render_to_string
        # 정확도 계산 (안전하게 처리)
        correct_count = getattr(result, 'correct_count', None) or 0
        total_score = result.total_score or 0
        accuracy = (correct_count / total_score * 100) if total_score > 0 else 0.0
        
        context = {
            'sharer_name': request.user.username,
            'exam_title': exam_title,
            'completed_at': result.completed_at.strftime('%Y-%m-%d %H:%M:%S') if result.completed_at else '-',
            'score': result.score or 0,
            'total_score': total_score,
            'accuracy': f"{accuracy:.1f}",
            'result_url': result_url
        }

        # HTML 이메일 템플릿 렌더링
        try:
            html_content = render_to_string(template_name, context)
        except Exception as e:
            logger.error(f"템플릿 렌더링 실패: {str(e)}")
            # 템플릿이 없으면 기본 영어 템플릿 사용
            html_content = render_to_string('share_voice_interview_result_en.html', context)

        # 텍스트 버전 (간단한 버전)
        if user_language == LANGUAGE_KO:
            text_content = f"""
안녕하세요,

{request.user.username}님이 Voice Interview 결과를 공유했습니다.

시험: {context['exam_title']}
완료일시: {context['completed_at']}
점수: {context['score']}/{context['total_score']}
정확도: {context['accuracy']}%

결과를 확인하려면 아래 링크를 클릭하세요:
{result_url}

© 2024 DrillQuiz. All rights reserved.
"""
        elif user_language == LANGUAGE_ZH:
            text_content = f"""
您好，

{request.user.username}分享了语音面试结果。

考试: {context['exam_title']}
完成时间: {context['completed_at']}
分数: {context['score']}/{context['total_score']}
准确率: {context['accuracy']}%

请点击下面的链接查看结果：
{result_url}

© 2024 DrillQuiz. 保留所有权利。
"""
        elif user_language == LANGUAGE_ES:
            text_content = f"""
Hola,

{request.user.username} ha compartido un resultado de entrevista por voz.

Examen: {context['exam_title']}
Completado: {context['completed_at']}
Puntuación: {context['score']}/{context['total_score']}
Precisión: {context['accuracy']}%

Haga clic en el enlace a continuación para ver el resultado:
{result_url}

© 2024 DrillQuiz. Todos los derechos reservados.
"""
        elif user_language == LANGUAGE_JA:
            text_content = f"""
こんにちは、

{request.user.username}が音声面接結果を共有しました。

試験: {context['exam_title']}
完了日時: {context['completed_at']}
スコア: {context['score']}/{context['total_score']}
精度: {context['accuracy']}%

結果を確認するには、以下のリンクをクリックしてください：
{result_url}

© 2024 DrillQuiz. All rights reserved.
"""
        else:
            text_content = f"""
Hello,

{request.user.username} has shared a Voice Interview result.

Exam: {context['exam_title']}
Completed: {context['completed_at']}
Score: {context['score']}/{context['total_score']}
Accuracy: {context['accuracy']}%

Click the link below to view the result:
{result_url}

© 2024 DrillQuiz. All rights reserved.
"""

        # 이메일 전송
        sent_count = 0
        failed_count = 0
        failed_emails = []

        try:
            server = smtplib.SMTP(email_config['SMTPHost'], email_config['SMTPPort'])
            server.starttls()
            server.login(email_config['Username'], email_config['Password'])

            for member in members:
                if not member.email or not member.email.strip():
                    failed_count += 1
                    failed_emails.append(member.name or 'Unknown')
                    continue

                try:
                    msg = MIMEMultipart('alternative')
                    msg['From'] = email_config['FromEmail']
                    msg['To'] = member.email
                    msg['Subject'] = subject

                    # HTML과 텍스트 버전 모두 추가
                    text_part = MIMEText(text_content, 'plain', 'utf-8')
                    html_part = MIMEText(html_content, 'html', 'utf-8')
                    
                    msg.attach(text_part)
                    msg.attach(html_part)

                    server.send_message(msg)
                    sent_count += 1
                except Exception as e:
                    logger.error(f"이메일 전송 실패 ({member.email}): {str(e)}")
                    failed_count += 1
                    failed_emails.append(member.name or member.email or 'Unknown')

            server.quit()

            return Response({
                'success': True,
                'sent_count': sent_count,
                'failed_count': failed_count,
                'failed_emails': failed_emails
            })

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP 인증 실패: {str(e)}")
            error_message = '이메일 서버 인증에 실패했습니다. SMTP 설정을 확인해주세요.'
            if 'Username and Password not accepted' in str(e):
                error_message = '이메일 서버 인증에 실패했습니다. SMTP 사용자명과 비밀번호를 확인해주세요.'
            return Response({'error': error_message}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except smtplib.SMTPException as e:
            logger.error(f"SMTP 오류: {str(e)}")
            return Response({'error': f'이메일 서버 오류가 발생했습니다: {str(e)}'}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            import traceback
            logger.error(f"이메일 서버 연결 실패: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            error_message = f'이메일 전송 중 오류가 발생했습니다: {str(e)}'
            # 개발 환경에서는 더 자세한 정보 제공
            if settings.DEBUG:
                error_message += f'\n상세 정보: {traceback.format_exc()}'
            return Response({'error': error_message}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        import traceback
        logger.error(f"Voice Interview 결과 공유 중 오류: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return Response({'error': f'결과 공유 중 오류가 발생했습니다: {str(e)}'}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def share_exam(request):
    """시험을 이메일로 공유"""
    try:
        if not request.user.is_authenticated:
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)

        exam_id = request.data.get('exam_id')
        email = request.data.get('email')
        share_url = request.data.get('share_url')

        if not exam_id or not email or not share_url:
            return Response({'error': '필수 파라미터가 누락되었습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 이메일 유효성 검사
        import re
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_pattern, email):
            return Response({'error': '유효하지 않은 이메일 주소입니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 시험 확인
        try:
            exam = Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            return Response({'error': '시험을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        # 이메일 전송
        from ..email_utils import get_email_config
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from django.conf import settings
        import os

        # 이메일 설정
        email_config = get_email_config()
        
        # 사용자 언어 설정
        from ..utils.multilingual_utils import (
            get_user_language, SUPPORTED_LANGUAGES,
            LANGUAGE_KO, LANGUAGE_EN, LANGUAGE_ES, LANGUAGE_ZH, LANGUAGE_JA, BASE_LANGUAGE
        )
        user_language = get_user_language(request.user)
        
        # 동적으로 exam 제목 가져오기
        exam_title = None
        if hasattr(exam, f'title_{user_language}'):
            exam_title = getattr(exam, f'title_{user_language}', None)
        if not exam_title:
            if hasattr(exam, f'title_{BASE_LANGUAGE}'):
                exam_title = getattr(exam, f'title_{BASE_LANGUAGE}', None)
        if not exam_title:
            for lang in SUPPORTED_LANGUAGES:
                if hasattr(exam, f'title_{lang}'):
                    exam_title = getattr(exam, f'title_{lang}', None)
                    if exam_title:
                        break
        if not exam_title:
            exam_title = 'Exam' if user_language == BASE_LANGUAGE else '시험'

        # 이메일 제목 설정
        subject_templates = {
            LANGUAGE_KO: f"시험 공유 - {exam_title}",
            LANGUAGE_ZH: f"考试分享 - {exam_title}",
            LANGUAGE_ES: f"Compartir Examen - {exam_title}",
            LANGUAGE_JA: f"試験の共有 - {exam_title}",
        }
        subject = subject_templates.get(user_language, f"Exam Shared - {exam_title}")

        # 템플릿 이름 설정
        template_names = {
            LANGUAGE_KO: 'share_exam_ko.html',
            LANGUAGE_ZH: 'share_exam_zh.html',
            LANGUAGE_ES: 'share_exam_es.html',
            LANGUAGE_JA: 'share_exam_ja.html',
        }
        template_name = template_names.get(user_language, 'share_exam_en.html')

        # 템플릿 컨텍스트
        from django.template.loader import render_to_string
        context = {
            'sharer_name': request.user.username,
            'exam_title': exam_title,
            'share_url': share_url
        }

        # HTML 이메일 템플릿 렌더링
        try:
            html_content = render_to_string(template_name, context)
        except Exception as e:
            logger.error(f"템플릿 렌더링 실패: {str(e)}")
            # 템플릿이 없으면 기본 영어 템플릿 사용
            html_content = render_to_string('share_exam_en.html', context)

        # 이메일 본문 생성 (텍스트 버전)
        if user_language == LANGUAGE_KO:
            text_content = f"""
안녕하세요,

{request.user.username}님이 시험을 공유했습니다.

시험: {exam_title}
공유 링크: {share_url}

시험을 확인하려면 위 링크를 클릭하세요.

© 2024 DrillQuiz. All rights reserved.
"""
        elif user_language == LANGUAGE_ZH:
            text_content = f"""
您好，

{request.user.username}分享了考试。

考试: {exam_title}
分享链接: {share_url}

请点击上面的链接查看考试。

© 2024 DrillQuiz. 保留所有权利。
"""
        elif user_language == LANGUAGE_ES:
            text_content = f"""
Hola,

{request.user.username} ha compartido un examen.

Examen: {exam_title}
Enlace compartido: {share_url}

Haga clic en el enlace de arriba para ver el examen.

© 2024 DrillQuiz. Todos los derechos reservados.
"""
        elif user_language == LANGUAGE_JA:
            text_content = f"""
こんにちは、

{request.user.username}さんが試験を共有しました。

試験: {exam_title}
共有リンク: {share_url}

試験を確認するには、上記のリンクをクリックしてください。

© 2024 DrillQuiz. 全著作権所有。
"""
        else:
            text_content = f"""
Hello,

{request.user.username} has shared an exam.

Exam: {exam_title}
Share Link: {share_url}

Click the link above to view the exam.

© 2024 DrillQuiz. All rights reserved.
"""

        # 이메일 전송
        try:
            server = smtplib.SMTP(email_config['SMTPHost'], email_config['SMTPPort'])
            server.starttls()
            server.login(email_config['Username'], email_config['Password'])

            msg = MIMEMultipart('alternative')
            msg['From'] = email_config['FromEmail']
            msg['To'] = email
            msg['Subject'] = subject

            # 텍스트 버전 추가
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # HTML 버전 추가
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            server.send_message(msg)
            server.quit()

            return Response({
                'success': True,
                'message': '이메일이 전송되었습니다.'
            })

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP 인증 실패: {str(e)}")
            error_message = '이메일 서버 인증에 실패했습니다. SMTP 설정을 확인해주세요.'
            return Response({'error': error_message}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except smtplib.SMTPException as e:
            logger.error(f"SMTP 오류: {str(e)}")
            return Response({'error': f'이메일 서버 오류가 발생했습니다: {str(e)}'}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            import traceback
            logger.error(f"이메일 전송 실패: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            error_message = f'이메일 전송 중 오류가 발생했습니다: {str(e)}'
            if settings.DEBUG:
                error_message += f'\n상세 정보: {traceback.format_exc()}'
            return Response({'error': error_message}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        import traceback
        logger.error(f"시험 공유 중 오류: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return Response({'error': f'시험 공유 중 오류가 발생했습니다: {str(e)}'}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_voice_interview_results(request):
    """Voice Interview 결과 삭제 (복수 선택 가능)"""
    try:
        if not request.user.is_authenticated:
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)

        result_ids = request.data.get('result_ids', [])
        exam_id = request.data.get('exam_id')

        if not result_ids or not isinstance(result_ids, list):
            return Response({'error': '삭제할 결과 ID가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 결과 확인 및 권한 검사
        results = ExamResult.objects.filter(
            id__in=result_ids,
            is_voice_interview=True
        ).select_related('exam', 'user')

        if not results.exists():
            return Response({'error': '삭제할 결과를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        # 권한 확인: admin, exam creator, study member, 또는 결과 소유자만 삭제 가능
        from ..models import Member
        
        deleted_count = 0
        failed_results = []

        for result in results:
            can_delete = False

            # Admin은 모든 결과 삭제 가능
            is_admin = (hasattr(request.user, 'is_superuser') and request.user.is_superuser) or \
                      (hasattr(request.user, 'is_staff') and request.user.is_staff)
            if is_admin:
                can_delete = True
            # Exam 생성자는 해당 exam의 모든 결과 삭제 가능
            elif result.exam and result.exam.created_by == request.user:
                can_delete = True
            # 결과 소유자는 자신의 결과 삭제 가능
            elif result.user == request.user:
                can_delete = True
            # Study 멤버는 해당 exam이 포함된 study의 멤버인 경우 삭제 가능
            elif exam_id and result.exam:
                study_members = Member.objects.filter(
                    user=request.user,
                    study__tasks__exam=result.exam,
                    is_active=True
                )
                if study_members.exists():
                    can_delete = True

            if can_delete:
                result.delete()
                deleted_count += 1
            else:
                failed_results.append(str(result.id))

        if failed_results:
            return Response({
                'success': True,
                'deleted_count': deleted_count,
                'failed_count': len(failed_results),
                'failed_results': failed_results,
                'message': f'{deleted_count}개의 결과가 삭제되었습니다. {len(failed_results)}개의 결과는 권한이 없어 삭제되지 않았습니다.'
            }, status=status.HTTP_200_OK)

        return Response({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'{deleted_count}개의 결과가 삭제되었습니다.'
        })

    except Exception as e:
        import traceback
        logger.error(f"Voice Interview 결과 삭제 중 오류: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return Response({'error': f'결과 삭제 중 오류가 발생했습니다: {str(e)}'}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def toggle_exam_original(request, exam_id):
    """시험의 is_original 필드를 토글합니다."""
    try:
        exam = Exam.objects.get(id=exam_id)
        exam.is_original = not exam.is_original
        exam.save()
        serializer = ExamSerializer(exam, context={'request': request})
        return Response(serializer.data)
    except Exam.DoesNotExist:
        return Response({'error': '시험을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def add_question_to_exam(request, exam_id):
    """시험에 새 문제를 추가합니다."""
    try:
        # 관리자 권한 확인
        if not request.user.is_authenticated:
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)

        # 권한 확인: can_edit_exam 유틸 함수 사용
        from ..utils.permissions import can_edit_exam

        # 시험 존재 확인
        exam = Exam.objects.get(id=exam_id)

        # 권한 확인
        if not can_edit_exam(request.user, exam):
            return Response({'error': '시험에 문제를 추가할 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)

        # 요청 데이터 가져오기
        csv_id = request.data.get('csv_id')
        title = request.data.get('title')
        content = request.data.get('content')
        answer = request.data.get('answer')
        explanation = request.data.get('explanation', '')
        difficulty = request.data.get('difficulty', '')
        url = request.data.get('url', '')
        group_id = request.data.get('group_id', '')

        # 필수 필드 검증
        if not all([csv_id, title, content, answer]):
            return Response({
                'error': '문제 ID, 제목, 문제 내용, 정답은 필수 입력 항목입니다.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 사용자 언어 확인
        from quiz.utils.multilingual_utils import BASE_LANGUAGE
        user_language = BASE_LANGUAGE  # 기본값
        try:
            if hasattr(request.user, 'userprofile'):
                user_language = request.user.userprofile.language
            elif hasattr(request.user, 'profile'):
                user_language = request.user.profile.language
        except Exception:
            pass
        
        # 기존 문제 확인 (동일한 제목의 문제가 있는지 체크)
        from ..utils.question_utils import get_questions_by_title
        existing_questions = get_questions_by_title(title, user_language)
        existing_question = existing_questions.first() if existing_questions.exists() else None
        
        if existing_question:
            # 기존 문제가 있으면 재사용하되, difficulty가 업데이트되어야 하는 경우 업데이트
            question = existing_question
            
            # difficulty가 제공되고 기존 difficulty와 다른 경우 업데이트
            if difficulty and question.difficulty != difficulty:
                print(f"[ADD_QUESTION_TO_EXAM] 기존 문제 difficulty 업데이트: {title} (ID: {question.id}) - {question.difficulty} -> {difficulty}")
                question.difficulty = difficulty
                question.save()
            
            print(f"[ADD_QUESTION_TO_EXAM] 기존 문제 재사용: {title} (ID: {question.id})")
        else:
            # 새 문제 생성 (다국어 필드만 사용)
            question = Question.objects.create(
                csv_id=csv_id,
                difficulty=difficulty,
                url=url,
                group_id=group_id,
                created_by=request.user,
                created_language=user_language
            )
            
            # 다국어 필드에 데이터 저장
            setattr(question, f'title_{user_language}', title)
            setattr(question, f'content_{user_language}', content)
            setattr(question, f'answer_{user_language}', answer)
            if explanation:
                setattr(question, f'explanation_{user_language}', explanation)
            
            # 다국어 필드 설정 후 저장
            question.save()
            print(f"[ADD_QUESTION_TO_EXAM] 새 문제 생성: {title} (ID: {question.id})")
        
        # 번역은 나중에 배치로 처리하므로 여기서는 건너뛰기
        print(f"[ADD_QUESTION_TO_EXAM] 문제 {question.id} 생성 완료 (번역은 배치로 처리 예정)")

        # 시험에 문제 추가 (중복 체크)
        existing_exam_question = ExamQuestion.objects.filter(
            exam=exam,
            question=question
        ).first()
        
        if existing_exam_question:
            print(f"[ADD_QUESTION_TO_EXAM] 문제가 이미 시험에 추가되어 있음: {title} (ID: {question.id})")
        else:
            # 시험에 문제 추가 (가장 마지막 순서로)
            max_order = ExamQuestion.objects.filter(exam=exam).aggregate(
                models.Max('order')
            )['order__max'] or 0

            ExamQuestion.objects.create(
                exam=exam,
                question=question,
                order=max_order + 1
            )
            print(f"[ADD_QUESTION_TO_EXAM] 시험에 문제 추가 완료: {title} (ID: {question.id})")
        
        # 문제 추가 완료 후 배치 번역 처리
        try:
            from ..utils.multilingual_utils import process_large_question_batch
            
            # 시험에 속한 모든 문제 가져오기
            exam_questions = Question.objects.filter(examquestion__exam=exam)
            
            if exam_questions.exists():
                print(f"[ADD_QUESTION_TO_EXAM] {len(exam_questions)}개 문제 배치 번역 시작")
                
                # 배치 번역 수행
                translation_result = process_large_question_batch(exam_questions, request.user)
                
                print(f"[ADD_QUESTION_TO_EXAM] 배치 번역 완료: {translation_result['successful']}/{translation_result['total_translations']} 성공")
                
                if translation_result['errors']:
                    print(f"[ADD_QUESTION_TO_EXAM] 번역 중 일부 오류 발생: {len(translation_result['errors'])}개")
                    for error in translation_result['errors'][:3]:  # 처음 3개만 로그
                        print(f"[ADD_QUESTION_TO_EXAM] 번역 오류: {error}")
                        
        except Exception as e:
            print(f"[ADD_QUESTION_TO_EXAM] 배치 번역 처리 실패: {e}")
            # 번역 실패해도 문제 추가는 계속 진행

        return Response({
            'message': '새 문제가 성공적으로 추가되었습니다.',
            'question_id': question.id
        }, status=status.HTTP_201_CREATED)

    except Exam.DoesNotExist:
        return Response({'error': '시험을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'문제 추가 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_question_member_mappings(request, exam_id):
    """시험의 문제-멤버 매핑을 조회합니다. (인증 필요)"""
    try:
        exam = Exam.objects.get(id=exam_id)
        mappings = QuestionMemberMapping.objects.filter(exam=exam)
        serializer = QuestionMemberMappingSerializer(mappings, many=True)
        return Response(serializer.data)
    except Exam.DoesNotExist:
        return Response({'error': '시험을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_question_statistics(request, exam_id):
    """시험의 문제별 정답 통계를 조회합니다. (공개 API - 인증 불필요)"""
    logger.info(f"[QUESTION_STATS] API 호출 시작 - exam_id: {exam_id}")
    logger.info(f"[QUESTION_STATS] 사용자 인증 상태: {request.user.is_authenticated}")
    logger.info(f"[QUESTION_STATS] 사용자 ID: {request.user.id if request.user.is_authenticated else 'Anonymous'}")
    logger.info(f"[QUESTION_STATS] 사용자명: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
    
    try:
        exam = Exam.objects.get(id=exam_id)
        logger.info(f"[QUESTION_STATS] 시험 정보 - exam_id: {exam_id}, is_public: {exam.is_public}")
        
        # 시험 접근 권한 확인
        user = request.user
        if not user.is_authenticated:
            # 익명 사용자는 공개 시험만 접근 가능
            if not exam.is_public:
                logger.warning(f"[QUESTION_STATS] 익명 사용자가 비공개 시험에 접근 시도 (exam_id: {exam_id}) - 401 UNAUTHORIZED")
                return Response({
                    'error': '이 시험에 접근하려면 로그인이 필요합니다.',
                    'requires_login': True,
                    'exam_id': str(exam.id)
                }, status=status.HTTP_401_UNAUTHORIZED)
            else:
                logger.info(f"[QUESTION_STATS] 익명 사용자 공개 시험 접근 허용 (exam_id: {exam_id})")
        elif user.is_authenticated:
            # 인증된 사용자는 추가 권한 체크
            if hasattr(user, 'profile') and hasattr(user.profile, 'role') and user.profile.role == 'admin_role':
                pass  # admin은 모든 시험 접근 가능
            elif not exam.is_public:
                # 비공개 시험인 경우 생성자, 스터디 멤버, 시험을 풀어본 사용자만 접근 가능
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
                    logger.warning(f"[QUESTION_STATS] 인증된 사용자가 비공개 시험에 접근 시도 (exam_id: {exam_id}) - 403 FORBIDDEN")
                    return Response({'error': '이 시험에 접근할 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
        
        exam_questions = Question.objects.filter(examquestion__exam=exam).select_related()

        logger.info(f"[QUESTION_STATS] 시험 정보: {exam.title_ko or exam.title_en or 'Unknown'} (ID: {exam.id})")
        logger.info(f"[QUESTION_STATS] 시험에 포함된 문제 수: {exam_questions.count()}")

        # 사용자 ID 또는 username 쿼리 파라미터 확인
        user_id_param = request.GET.get('user_id')
        username_param = request.GET.get('username')
        
        logger.info(f"[QUESTION_STATS] 쿼리 파라미터 - user_id: {user_id_param}, username: {username_param}")

        # 성능 최적화: 같은 제목의 문제들을 그룹화하여 통계 계산
        statistics = []
        
        # 문제들을 제목별로 그룹화 (시험에 포함된 문제들의 제목을 기준으로)
        from ..utils.question_utils import group_questions_by_title, get_all_questions_by_title_group
        title_groups = group_questions_by_title(exam_questions)
        
        logger.info(f"[QUESTION_STATS] 제목별 그룹 수: {len(title_groups)}")
        
        # 각 제목 그룹별로 통계 계산
        for title_key, questions_in_group in title_groups.items():
            # 시험에 포함된 문제들의 ID
            exam_question_ids = [q.id for q in questions_in_group]
            
            # 동일한 제목의 모든 문제를 찾아서 통합 통계 계산
            all_questions = get_all_questions_by_title_group(title_key)
            all_question_ids = [q.id for q in all_questions]
            logger.info(f"[QUESTION_STATS] 그룹 {title_key}: 시험 문제 {len(exam_question_ids)}개, 전체 문제 {len(all_question_ids)}개")
            
            # 인증된 사용자인 경우
            if user.is_authenticated:
                # admin 사용자는 모든 사용자의 통계를 볼 수 있음
                if hasattr(user, 'profile') and user.profile.role == 'admin_role':
                    logger.info(f"[QUESTION_STATS] Admin 사용자 처리 - 그룹: {title_key}")
                    
                    # 전체 시도 횟수 조회 (동일한 제목의 모든 문제)
                    total_attempts_data = ExamResultDetail.objects.filter(
                        question_id__in=all_question_ids
                    ).values('question_id').annotate(
                        total_attempts=Count('id')
                    )
                    
                    # 정답 횟수 조회 (동일한 제목의 모든 문제)
                    correct_attempts_data = ExamResultDetail.objects.filter(
                        question_id__in=all_question_ids,
                        is_correct=True
                    ).values('question_id').annotate(
                        correct_attempts=Count('id')
                    )
                    
                    # 그룹 내 최대값 계산
                    total_attempts = max([item['total_attempts'] for item in total_attempts_data], default=0)
                    correct_attempts = max([item['correct_attempts'] for item in correct_attempts_data], default=0)
                    
                else:
                    logger.info(f"[QUESTION_STATS] 일반 사용자 처리 - 그룹: {title_key}")
                    
                    # 사용자의 전체 시도 횟수 조회 (동일한 제목의 모든 문제)
                    total_attempts_data = ExamResultDetail.objects.filter(
                        question_id__in=all_question_ids,
                        result__user_id=user.id
                    ).values('question_id').annotate(
                        total_attempts=Count('id')
                    )
                    
                    # 사용자의 정답 횟수 조회 (동일한 제목의 모든 문제)
                    correct_attempts_data = ExamResultDetail.objects.filter(
                        question_id__in=all_question_ids,
                        result__user_id=user.id,
                        is_correct=True
                    ).values('question_id').annotate(
                        correct_attempts=Count('id')
                    )
                    
                    # 그룹 내 최대값 계산
                    total_attempts = max([item['total_attempts'] for item in total_attempts_data], default=0)
                    correct_attempts = max([item['correct_attempts'] for item in correct_attempts_data], default=0)
                    
            else:
                logger.info(f"[QUESTION_STATS] 익명 사용자 처리 - 그룹: {title_key}")
                # 익명 사용자의 경우
                if user_id_param:
                    logger.info(f"[QUESTION_STATS] user_id 파라미터로 처리: {user_id_param}")
                    try:
                        user_id = int(user_id_param)
                        
                        # question_ids는 이전에 정의되어 있어야 함
                        # 지정된 사용자의 전체 시도 횟수 조회
                        all_question_ids = list(Question.objects.filter(
                            title_ko__icontains=title_key
                        ).values_list('id', flat=True))
                        total_attempts_data = ExamResultDetail.objects.filter(
                            question_id__in=all_question_ids,
                            result__user_id=user_id
                        ).values('question_id').annotate(
                            total_attempts=Count('id')
                        )
                        
                        # 지정된 사용자의 정답 횟수 조회
                        correct_attempts_data = ExamResultDetail.objects.filter(
                            question_id__in=all_question_ids,
                            result__user_id=user_id,
                            is_correct=True
                        ).values('question_id').annotate(
                            correct_attempts=Count('id')
                        )
                        
                        # 그룹 내 최대값 계산
                        total_attempts = max([item['total_attempts'] for item in total_attempts_data], default=0)
                        correct_attempts = max([item['correct_attempts'] for item in correct_attempts_data], default=0)
                        
                    except ValueError:
                        logger.error(f"[QUESTION_STATS] 잘못된 user_id 파라미터: {user_id_param}")
                        return Response({'error': '잘못된 user_id 파라미터입니다.'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    logger.info(f"[QUESTION_STATS] 익명 사용자 - 기본 통계 (0으로 설정)")
                    total_attempts = 0
                    correct_attempts = 0
            
            # 그룹 내 모든 문제에 동일한 통계 적용
            for question in questions_in_group:
                statistics.append({
                    'question_id': question.id,
                    'total_attempts': total_attempts,
                    'correct_attempts': correct_attempts
                })
        
        logger.info(f"[QUESTION_STATS] 전체 통계 생성 완료 - 문제 수: {len(statistics)}")
        logger.info(f"[QUESTION_STATS] 통계 데이터: {statistics}")
        
        response = Response(statistics)
        
        # 캐시 무효화 헤더 설정
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        logger.info(f"[QUESTION_STATS] API 응답 완료 - 상태코드: 200, 응답크기: {len(str(statistics))}")
        return response
    except Exam.DoesNotExist:
        logger.error(f"[QUESTION_STATS] 시험을 찾을 수 없음: {exam_id}")
        return Response({'error': '시험을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def get_exam_list_for_move(request):
    """문제 이동을 위한 시험 목록을 조회합니다."""
    try:
        # 현재 시험 ID를 제외한 모든 시험 조회
        current_exam_id = request.GET.get('current_exam_id')
        exams = Exam.objects.all().order_by('-created_at')

        exam_list = []
        for exam in exams:
            # 현재 시험은 제외
            if str(exam.id) == current_exam_id:
                continue

            exam_list.append({
                'id': exam.id,
                'title': exam.title_ko or exam.title_en or 'Unknown',
                'total_questions': exam.total_questions,
                'created_at': exam.created_at,
                'is_original': exam.is_original
            })

        return Response(exam_list, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': f'시험 목록 조회 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def move_questions_to_exam(request):
    """선택된 문제들을 다른 시험으로 이동합니다."""
    try:
        source_exam_id = request.data.get('source_exam_id')
        target_exam_id = request.data.get('target_exam_id')
        question_ids = request.data.get('question_ids', [])

        if not source_exam_id or not target_exam_id or not question_ids:
            return Response({'error': '필수 파라미터가 누락되었습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 소스 시험과 타겟 시험 조회
        try:
            source_exam = Exam.objects.get(id=source_exam_id)
            target_exam = Exam.objects.get(id=target_exam_id)
        except Exam.DoesNotExist:
            return Response({'error': '시험을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        # 문제들이 소스 시험에 실제로 존재하는지 확인
        source_exam_questions = ExamQuestion.objects.filter(
            exam=source_exam,
            question_id__in=question_ids
        )

        if len(source_exam_questions) != len(question_ids):
            return Response({'error': '일부 문제가 소스 시험에 존재하지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 타겟 시험에 이미 존재하는 문제들 확인
        existing_questions = ExamQuestion.objects.filter(
            exam=target_exam,
            question_id__in=question_ids
        )

        if existing_questions.exists():
            return Response({'error': '일부 문제가 이미 타겟 시험에 존재합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 문제들을 타겟 시험으로 이동
        moved_count = 0
        for exam_question in source_exam_questions:
            # 타겟 시험에 추가
            ExamQuestion.objects.create(
                exam=target_exam,
                question=exam_question.question,
                order=target_exam.examquestion_set.count() + 1
            )

            # 소스 시험에서 제거
            exam_question.delete()
            moved_count += 1

        # 시험의 총 문제 수 업데이트
        source_exam.total_questions = source_exam.examquestion_set.count()
        target_exam.total_questions = target_exam.examquestion_set.count()
        source_exam.save()
        target_exam.save()

        return Response({
            'message': f'{moved_count}개의 문제가 성공적으로 이동되었습니다.',
            'moved_count': moved_count,
            'source_exam_total': source_exam.total_questions,
            'target_exam_total': target_exam.total_questions
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': f'문제 이동 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def create_question_member_mapping(request):
    """시험의 문제들을 스터디 멤버들에게 랜덤하게 매핑합니다."""
    serializer = CreateQuestionMemberMappingSerializer(data=request.data)
    if serializer.is_valid():
        exam_id = serializer.validated_data['exam_id']
        study_id = serializer.validated_data['study_id']
        question_ids = request.data.get('question_ids', [])  # 필터된 문제 ID들

        try:
            exam = Exam.objects.get(id=exam_id)
            study = Study.objects.get(id=study_id)

            # 기존 매핑 삭제
            QuestionMemberMapping.objects.filter(exam=exam).delete()

            # 문제들 가져오기 (필터된 문제 ID가 있으면 해당 문제들만, 없으면 전체)
            if question_ids:
                exam_questions = Question.objects.filter(id__in=question_ids, examquestion__exam=exam).order_by('examquestion__order')
            else:
                exam_questions = Question.objects.filter(examquestion__exam=exam).order_by('examquestion__order')

            # 스터디 멤버들 가져오기 (활성화된 멤버만)
            members = Member.objects.filter(study=study, is_active=True)

            if not exam_questions.exists():
                return Response({'error': '시험에 문제가 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)

            if not members.exists():
                return Response({'error': '스터디에 멤버가 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)

            # 문제와 멤버를 랜덤하게 매핑
            questions_list = list(exam_questions)
            members_list = list(members)

            # 문제 수와 멤버 수 중 작은 값만큼 매핑
            mapping_count = min(len(questions_list), len(members_list))

            # 랜덤 셔플
            import random
            random.shuffle(questions_list)
            random.shuffle(members_list)

            # 매핑 생성
            mappings = []
            for i in range(mapping_count):
                mapping = QuestionMemberMapping.objects.create(
                    question=questions_list[i],
                    member=members_list[i],
                    exam=exam
                )
                mappings.append(mapping)

            # 결과 반환
            result_serializer = QuestionMemberMappingSerializer(mappings, many=True)
            return Response({
                'message': f'{mapping_count}개의 문제-멤버 매핑이 생성되었습니다.',
                'mappings': result_serializer.data
            })

        except Exam.DoesNotExist:
            return Response({'error': '시험을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        except Study.DoesNotExist:
            return Response({'error': '스터디를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'매핑 생성 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_exams(request):
    """최적화된 시험 목록 조회 API (페이지네이션, 캐싱, 필드 선택 지원)"""
    import time
    from django.db import connection
    
    # 성능 측정 시작
    start_time = time.time()
    initial_queries = len(connection.queries)
    
    # 페이지네이션 파라미터
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    
    # 필요한 필드만 선택적으로 반환 (select 파라미터)
    select_fields_raw = request.GET.get('select', '').strip()
    if select_fields_raw:
        select_fields = [f.strip() for f in select_fields_raw.split(',') if f.strip()]
    else:
        select_fields = []
    logger.debug(f"[GET_EXAMS] select 파라미터 파싱 - 원본: '{select_fields_raw}', 파싱 결과: {select_fields}")
    
    # 필터링 파라미터
    is_public_param = request.GET.get('is_public')
    is_original_param = request.GET.get('is_original')
    my_exams_param = request.GET.get('my_exams')
    my_exams_public_param = request.GET.get('my_exams_public')  # 내가 생성한 시험 + 공개 시험
    search_title = request.GET.get('search_title', '').strip()
    tag_ids = request.GET.getlist('tags')  # 태그 필터링
    age_rating = request.GET.get('age_rating')  # 연령 등급 필터링
    
    # DevOps 도메인 필터링: devops 도메인인 경우 자동으로 카테고리 태그 필터 적용
    from quiz.utils.domain_utils import is_devops_domain, get_devops_category_tag_ids
    if is_devops_domain(request):
        devops_tag_ids = get_devops_category_tag_ids()
        if devops_tag_ids:
            # 기존 tag_ids와 병합 (중복 제거)
            existing_tag_ids = [int(tid) for tid in tag_ids if str(tid).isdigit()]
            # devops 태그 ID와 교집합만 유지 (둘 다 만족해야 함)
            if existing_tag_ids:
                # devops 태그 중에서 기존 태그와 일치하는 것만 사용
                tag_ids = [str(tid) for tid in existing_tag_ids if tid in devops_tag_ids]
            else:
                # 기존 태그가 없으면 devops 태그만 사용
                tag_ids = [str(tid) for tid in devops_tag_ids]
            logger.info(f"[GET_EXAMS] DevOps 도메인 필터링 적용: {len(tag_ids)}개 태그")
    
    # 사용자 ID
    user_id = request.user.id if request.user.is_authenticated else 'anonymous'
    
    # lang 파라미터 우선 사용 (프론트엔드에서 명시적으로 전달한 언어)
    # 없으면 사용자 프로필 언어 사용
    from quiz.utils.multilingual_utils import BASE_LANGUAGE
    user_language = request.GET.get('lang')
    logger.info(f"[GET_EXAMS] get_exams - lang 파라미터: {user_language}")
    
    # lang 파라미터가 없으면 사용자 프로필 언어 확인
    if not user_language and request.user.is_authenticated:
        if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'language'):
            user_language = request.user.profile.language
            logger.info(f"[GET_EXAMS] get_exams - 프로필 언어 사용: {user_language}")
        elif hasattr(request.user, 'userprofile') and hasattr(request.user.userprofile, 'language'):
            user_language = request.user.userprofile.language
            logger.info(f"[GET_EXAMS] get_exams - userprofile 언어 사용: {user_language}")
    
    # lang 파라미터도 없고 프로필 언어도 없으면 기본값 사용
    if not user_language:
        user_language = BASE_LANGUAGE
        logger.info(f"[GET_EXAMS] get_exams - 기본값 사용: {user_language}")
    
    logger.info(f"[GET_EXAMS] get_exams - 최종 user_language: {user_language}")
    
    # 강제 새로고침 파라미터 확인
    force_refresh = request.GET.get('force')
    cache_param = request.GET.get('cache')
    refresh_param = request.GET.get('refresh')
    
    # 강제 새로고침이 요청된 경우 캐시 무효화
    if force_refresh or cache_param or refresh_param:
        try:
            # 모든 시험 캐시 무효화
            ExamCacheManager.invalidate_all_exam_cache()
            if request.user.is_authenticated:
                ExamCacheManager.invalidate_user_exam_cache(request.user.id)
            logger.info(f"[GET_EXAMS] 강제 새로고침으로 인한 캐시 무효화 완료: 사용자={user_id}")
        except Exception as e:
            logger.error(f"[GET_EXAMS] 강제 새로고침 캐시 무효화 실패: {e}")
    
    # 캐시 키 생성
    cache_key_params = {
        'page': page,
        'page_size': page_size,
        'is_public': is_public_param,
        'is_original': is_original_param,
        'my_exams': my_exams_param,
        'my_exams_public': my_exams_public_param,  # 내가 생성한 시험 + 공개 시험
        'search_title': search_title,
        'select_fields': ','.join(select_fields) if select_fields else 'all',
        'tags': ','.join(tag_ids) if tag_ids else 'all',
        'age_rating': age_rating if age_rating else 'all'
    }
    
    # 강제 새로고침이 아닌 경우에만 캐시에서 조회
    if not (force_refresh or cache_param or refresh_param):
        cached_data = ExamCacheManager.get_exam_list_cache(user_id, **cache_key_params)
        if cached_data:
            return Response(cached_data)
    
    # 쿼리셋 최적화
    base_queryset = QueryOptimizer.optimize_exam_queryset(
        Exam.objects.select_related('original_exam', 'created_by'),
        select_fields
    )
    
    # 필터링 적용
    if is_public_param == 'true':
        base_queryset = base_queryset.filter(is_public=True)
    elif is_public_param == 'false':
        base_queryset = base_queryset.filter(is_public=False)
    
    # is_original 필터링 적용
    if is_original_param == 'true':
        base_queryset = base_queryset.filter(is_original=True)
    elif is_original_param == 'false':
        base_queryset = base_queryset.filter(is_original=False)
    
    # age_rating 필터링 적용
    if age_rating and age_rating in ['4+', '9+', '12+', '17+']:
        base_queryset = base_queryset.filter(age_rating=age_rating)
        logger.info(f"[GET_EXAMS] 연령 등급 필터링 적용: {age_rating}")
    
    # my_exams 파라미터 처리
    if my_exams_param == 'true' and request.user.is_authenticated:
        my_exams_start = time.time()
        my_exams_queries_before = len(connection.queries)
        
        # 내 시험만 조회 (내가 생성한 것 + 내가 참여한 스터디의 것 + 내가 응시한 것 + Today's Quizzes)
        # 최적화: 하나의 Q 객체로 통합하여 단일 쿼리로 처리
        user = request.user
        username = user.username
        
        # StudyTask를 통해 연결된 시험들 조회
        study_exams = Exam.objects.filter(
            studytask__study__members__user=user,
            studytask__study__members__is_active=True
        ).distinct()
        
        # 내가 응시한 시험들 조회
        taken_exams = Exam.objects.filter(
            examresult__user=user,
            examresult__examresultdetail__isnull=False
        ).distinct()
        
        # 내가 생성한 시험들 조회
        created_exams = Exam.objects.filter(created_by=user).distinct()
        
        # "Today's Quizzes for" 시험들 조회 (사용자별)
        today_quizzes = Exam.objects.filter(
            Q(title_ko__startswith=f"Today's Quizzes for {username}") |
            Q(title_en__startswith=f"Today's Quizzes for {username}")
        ).distinct()
        
        # 모든 시험을 합치고 중복 제거 (공개 시험 제외)
        base_exams = (study_exams | taken_exams | created_exams | today_quizzes).distinct()
        
        # copied_exams는 서브쿼리로 최적화 (별도 쿼리 실행 방지)
        base_exam_ids = base_exams.values_list('id', flat=True)
        copied_exams = Exam.objects.filter(original_exam_id__in=base_exam_ids).distinct()
        
        base_queryset = (base_exams | copied_exams).select_related('original_exam', 'created_by')
        
        my_exams_queries_after = len(connection.queries)
        my_exams_time = time.time() - my_exams_start
        logger.debug(f"[GET_EXAMS] my_exams 쿼리 구성 완료: {my_exams_queries_after - my_exams_queries_before}개 쿼리, {my_exams_time:.3f}초")
        
        # my_exams에 태그 필터 적용
        if tag_ids:
            try:
                # tag_ids가 문자열 리스트인 경우 정수로 변환, 이미 정수인 경우 그대로 사용
                tag_ids_int = []
                for tag_id in tag_ids:
                    if isinstance(tag_id, str) and tag_id.isdigit():
                        tag_ids_int.append(int(tag_id))
                    elif isinstance(tag_id, int):
                        tag_ids_int.append(tag_id)
                
                if tag_ids_int:
                    base_queryset = base_queryset.filter(tags__id__in=tag_ids_int).distinct()
                    logger.info(f"[GET_EXAMS] my_exams 태그 필터링 적용: tag_ids={tag_ids_int}")
            except (ValueError, AttributeError):
                pass
        
        # select_fields에 questions가 명시적으로 포함된 경우에만 prefetch
        if select_fields and 'questions' in select_fields:
            base_queryset = base_queryset.prefetch_related('questions')
        elif not select_fields:
            # select_fields가 없으면 기본적으로 questions prefetch (하위 호환성)
            base_queryset = base_queryset.prefetch_related('questions')
        # select_fields에 versions가 명시적으로 포함된 경우에만 prefetch
        if select_fields and 'versions' in select_fields:
            base_queryset = base_queryset.prefetch_related('versions')
        elif not select_fields:
            # select_fields가 없으면 기본적으로 versions prefetch (하위 호환성)
            base_queryset = base_queryset.prefetch_related('versions')
    
    # my_exams_public 파라미터 처리 (내가 생성한 시험 + 공개 시험)
    if my_exams_public_param == 'true' and request.user.is_authenticated:
        # 내가 생성한 시험들 조회
        created_exams = Exam.objects.filter(created_by=request.user).distinct()
        
        # 공개 시험들 조회
        public_exams = Exam.objects.filter(is_public=True).distinct()
        
        # 모든 시험을 합치고 중복 제거
        base_exams = (created_exams | public_exams).distinct()
        
        # copied_exams는 서브쿼리로 최적화 (별도 쿼리 실행 방지)
        base_exam_ids = base_exams.values_list('id', flat=True)
        copied_exams = Exam.objects.filter(original_exam_id__in=base_exam_ids).distinct()
        
        base_queryset = (base_exams | copied_exams).select_related('original_exam', 'created_by')
        
        # my_exams_public에 태그 필터 적용
        if tag_ids:
            try:
                tag_ids_int = []
                for tag_id in tag_ids:
                    if isinstance(tag_id, str) and tag_id.isdigit():
                        tag_ids_int.append(int(tag_id))
                    elif isinstance(tag_id, int):
                        tag_ids_int.append(tag_id)
                
                if tag_ids_int:
                    base_queryset = base_queryset.filter(tags__id__in=tag_ids_int).distinct()
                    logger.info(f"[GET_EXAMS] my_exams_public 태그 필터링 적용: tag_ids={tag_ids_int}")
            except (ValueError, AttributeError):
                pass
        
        # select_fields에 questions가 명시적으로 포함된 경우에만 prefetch
        if select_fields and 'questions' in select_fields:
            base_queryset = base_queryset.prefetch_related('questions')
        elif not select_fields:
            # select_fields가 없으면 기본적으로 questions prefetch (하위 호환성)
            base_queryset = base_queryset.prefetch_related('questions')
        # select_fields에 versions가 명시적으로 포함된 경우에만 prefetch
        if select_fields and 'versions' in select_fields:
            base_queryset = base_queryset.prefetch_related('versions')
        elif not select_fields:
            # select_fields가 없으면 기본적으로 versions prefetch (하위 호환성)
            base_queryset = base_queryset.prefetch_related('versions')
    
    elif not request.user.is_authenticated:
        base_queryset = base_queryset.filter(is_public=True)
        # 익명 사용자에 태그 필터 적용
        if tag_ids:
            try:
                tag_ids_int = []
                for tag_id in tag_ids:
                    if isinstance(tag_id, str) and tag_id.isdigit():
                        tag_ids_int.append(int(tag_id))
                    elif isinstance(tag_id, int):
                        tag_ids_int.append(tag_id)
                
                if tag_ids_int:
                    base_queryset = base_queryset.filter(tags__id__in=tag_ids_int).distinct()
                    logger.info(f"[GET_EXAMS] 익명 사용자 태그 필터링 적용: tag_ids={tag_ids_int}")
            except (ValueError, AttributeError):
                pass
    else:
        # 관리자 또는 일반 사용자
        if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'role') and request.user.profile.role == 'admin_role':
            # 관리자에 태그 필터 적용
            if tag_ids:
                try:
                    tag_ids_int = []
                    for tag_id in tag_ids:
                        if isinstance(tag_id, str) and tag_id.isdigit():
                            tag_ids_int.append(int(tag_id))
                        elif isinstance(tag_id, int):
                            tag_ids_int.append(tag_id)
                    
                    if tag_ids_int:
                        base_queryset = base_queryset.filter(tags__id__in=tag_ids_int).distinct()
                        logger.info(f"[GET_EXAMS] 관리자 태그 필터링 적용: tag_ids={tag_ids_int}")
                except (ValueError, AttributeError):
                    pass
        else:
            # is_public 파라미터가 있으면 해당 필터만 적용하고 사용자 연관성 체크하지 않음
            if is_public_param:
                # is_public 필터에 태그 필터 적용
                if tag_ids:
                    try:
                        tag_ids_int = []
                        for tag_id in tag_ids:
                            if isinstance(tag_id, str) and tag_id.isdigit():
                                tag_ids_int.append(int(tag_id))
                            elif isinstance(tag_id, int):
                                tag_ids_int.append(tag_id)
                        
                        if tag_ids_int:
                            base_queryset = base_queryset.filter(tags__id__in=tag_ids_int)
                            logger.info(f"[GET_EXAMS] is_public 필터에 태그 필터링 적용: tag_ids={tag_ids_int}")
                    except (ValueError, AttributeError):
                        pass
            else:
                # 내 시험만 조회 (is_public 파라미터가 없을 때만)
                user = request.user
                username = user.username
                
                # StudyTask를 통해 연결된 시험들 조회
                study_exams = Exam.objects.filter(
                    studytask__study__members__user=user,
                    studytask__study__members__is_active=True
                ).distinct()
                
                # 내가 응시한 시험들 조회
                taken_exams = Exam.objects.filter(
                    examresult__user=user,
                    examresult__examresultdetail__isnull=False
                ).distinct()
                
                # 내가 생성한 시험들 조회
                created_exams = Exam.objects.filter(created_by=user).distinct()
                
                # "Today's Quizzes for" 시험들 조회 (사용자별)
                today_quizzes = Exam.objects.filter(
                    Q(title_ko__startswith=f"Today's Quizzes for {username}") |
                    Q(title_en__startswith=f"Today's Quizzes for {username}")
                ).distinct()
                
                base_exams = (study_exams | taken_exams | created_exams | today_quizzes).distinct()
                
                # copied_exams는 서브쿼리로 최적화 (별도 쿼리 실행 방지)
                base_exam_ids = base_exams.values_list('id', flat=True)
                copied_exams = Exam.objects.filter(original_exam_id__in=base_exam_ids).distinct()
                
                base_queryset = (base_exams | copied_exams).select_related('original_exam', 'created_by')
                
                # 일반 사용자에 태그 필터 적용
                if tag_ids:
                    try:
                        tag_ids_int = []
                        for tag_id in tag_ids:
                            if isinstance(tag_id, str) and tag_id.isdigit():
                                tag_ids_int.append(int(tag_id))
                            elif isinstance(tag_id, int):
                                tag_ids_int.append(tag_id)
                        
                        if tag_ids_int:
                            base_queryset = base_queryset.filter(tags__id__in=tag_ids_int).distinct()
                            logger.info(f"[GET_EXAMS] 일반 사용자 태그 필터링 적용: tag_ids={tag_ids_int}")
                    except (ValueError, AttributeError):
                        pass
            
            # select_fields에 questions가 명시적으로 포함된 경우에만 prefetch
            if select_fields and 'questions' in select_fields:
                base_queryset = base_queryset.prefetch_related('questions')
            elif not select_fields:
                # select_fields가 없으면 기본적으로 questions prefetch (하위 호환성)
                base_queryset = base_queryset.prefetch_related('questions')
            # select_fields에 versions가 명시적으로 포함된 경우에만 prefetch
            if select_fields and 'versions' in select_fields:
                base_queryset = base_queryset.prefetch_related('versions')
            elif not select_fields:
                # select_fields가 없으면 기본적으로 versions prefetch (하위 호환성)
                base_queryset = base_queryset.prefetch_related('versions')
    
    # 제목 검색 필터
    if search_title:
        base_queryset = base_queryset.filter(
            Q(title_ko__icontains=search_title) |
            Q(title_en__icontains=search_title)
        )
    
    # 태그 필터링은 각 필터링 로직 내부에서 이미 적용됨
    
    # 지원 언어 필터링 추가
    # admin 권한이고 모든 시험을 조회할 때(my_exams나 is_public 파라미터가 없을 때)는 지원언어 필터를 적용하지 않음
    # supported_languages에 사용자 언어가 포함되어 있어야 조회됨
    # Exam.save() 메서드에서 항상 supported_languages를 설정하므로 빈 문자열은 거의 없음
    # 성능 최적화: 단일 __contains 조건 사용 (인덱스는 부분적으로 활용)
    is_admin = False
    if request.user.is_authenticated:
        if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'role') and request.user.profile.role == 'admin_role':
            is_admin = True
        elif hasattr(request.user, 'is_superuser') and request.user.is_superuser:
            is_admin = True
    
    if not (is_admin and not my_exams_param and not my_exams_public_param and not is_public_param):
        # admin이 모든 시험을 조회할 때가 아니면 지원언어 필터 적용
        # 생성자가 만든 시험은 지원언어 필터를 건너뛰어야 함 (자신이 만든 시험은 항상 볼 수 있어야 함)
        if request.user.is_authenticated:
            base_queryset = base_queryset.filter(
                Q(supported_languages__contains=user_language) | Q(created_by=request.user)
            )
        else:
            base_queryset = base_queryset.filter(
                Q(supported_languages__contains=user_language)
            )
    
    # 태그 필터가 적용된 경우 distinct() 적용 (ManyToMany 관계로 인한 중복 제거)
    # 정렬 전에 distinct()를 적용하여 페이지네이션 문제 방지
    if tag_ids:
        base_queryset = base_queryset.distinct()
        logger.info(f"[GET_EXAMS] 태그 필터 적용 후 distinct() 호출, 쿼리셋 개수: {base_queryset.count()}")
    
    # 정렬
    base_queryset = base_queryset.order_by('-created_at')
    logger.info(f"[GET_EXAMS] 정렬 적용 후 쿼리셋 개수: {base_queryset.count()}")
    
    # 전체 개수 계산 (annotate() 전에 수행하여 distinct()가 제대로 작동하도록 함)
    # distinct()가 적용되었는지 확인
    has_distinct = hasattr(base_queryset.query, 'distinct_fields') and base_queryset.query.distinct_fields
    logger.info(f"[GET_EXAMS] total_count 계산 전 상태: distinct 적용 여부={has_distinct}, tag_ids={tag_ids}")
    
    count_start = time.time()
    count_queries_before = len(connection.queries)
    # annotate() 전에 total_count 계산 (distinct()가 제대로 작동하도록)
    total_count = base_queryset.count()
    count_time = time.time() - count_start
    count_queries_after = len(connection.queries)
    logger.info(f"[GET_EXAMS] total_count 계산: {count_queries_after - count_queries_before}개 쿼리, {count_time:.3f}초, 결과: {total_count}개, page: {page}, page_size: {page_size}, distinct 적용: {has_distinct}")
    
    # ExamListSerializer를 사용하는 경우 최적화 적용
    # 모든 권한에 대해 일관되게 적용
    if select_fields and 'questions' not in select_fields and 'versions' not in select_fields:
        from django.db.models import Count
        # questions 개수를 annotate로 미리 계산
        base_queryset = base_queryset.annotate(
            total_questions_count=Count('questions', distinct=True)
        )
        # tags를 prefetch_related로 미리 로드 (N+1 쿼리 방지)
        # 권한별로 이미 prefetch가 적용된 경우를 확인하여 중복 방지
        if not hasattr(base_queryset, '_prefetch_related_lookups') or 'tags' not in base_queryset._prefetch_related_lookups:
            base_queryset = base_queryset.prefetch_related('tags', 'tags__categories')
    
    # 페이지네이션 적용
    # annotate() 후에 distinct()가 무효화될 수 있으므로, 태그 필터가 있는 경우 다시 적용
    if tag_ids:
        # annotate() 후 distinct() 재적용 (ManyToMany 관계로 인한 중복 방지)
        base_queryset = base_queryset.distinct()
        logger.info(f"[GET_EXAMS] 페이지네이션 전 distinct() 재적용 (태그 필터 있음)")
    
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    logger.info(f"[GET_EXAMS] 페이지네이션 범위: start_index={start_index}, end_index={end_index}, total_count={total_count}")
    pagination_start = time.time()
    pagination_queries_before = len(connection.queries)
    paginated_exams = base_queryset[start_index:end_index]
    pagination_time = time.time() - pagination_start
    pagination_queries_after = len(connection.queries)
    paginated_count = len(list(paginated_exams))
    logger.info(f"[GET_EXAMS] 페이지네이션 쿼리: {pagination_queries_after - pagination_queries_before}개 쿼리, {pagination_time:.3f}초, 결과 개수: {paginated_count}")
    
    # ExamListSerializer를 사용하는 경우 사용자별 최신 결과 및 통계를 미리 조회
    user_latest_results_dict = {}
    user_correct_questions_dict = {}
    user_accuracy_percentage_dict = {}
    # 권한별 로그 추가
    user_role = 'anonymous'
    if request.user.is_authenticated:
        if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'role') and request.user.profile.role == 'admin_role':
            user_role = 'admin'
        elif hasattr(request.user, 'is_superuser') and request.user.is_superuser:
            user_role = 'superuser'
        else:
            user_role = 'user'
    logger.debug(f"[GET_EXAMS] 사용자 권한: {user_role}, 인증 여부: {request.user.is_authenticated}, my_exams: {my_exams_param}, is_public: {is_public_param}")
    
    if select_fields and 'questions' not in select_fields and 'versions' not in select_fields and request.user.is_authenticated:
        # 페이지네이션된 시험 ID를 가져와서 한 번에 조회
        exam_ids = [str(exam.id) for exam in paginated_exams]
        # 원본 시험 ID도 포함
        original_exam_ids = [str(exam.original_exam_id) for exam in paginated_exams if not exam.is_original and exam.original_exam_id]
        all_exam_ids = list(set([uuid.UUID(eid) for eid in exam_ids] + [uuid.UUID(eid) for eid in original_exam_ids if eid]))
        
        if all_exam_ids:
            # 각 시험의 최신 결과를 한 번에 조회
            # UUID 타입에는 Max()를 사용할 수 없으므로 completed_at 기준으로 정렬하여 최신 결과 선택
            from django.db.models import Max
            # completed_at이 최대인 결과를 찾기 위해 서브쿼리 사용
            latest_completed_at_dict = {}
            latest_completed_at_queryset = ExamResult.objects.filter(
                exam_id__in=all_exam_ids,
                user=request.user
            ).values('exam_id').annotate(
                latest_completed_at=Max('completed_at')
            )
            
            # exam_id -> latest_completed_at 딕셔너리 생성
            for item in latest_completed_at_queryset:
                latest_completed_at_dict[item['exam_id']] = item['latest_completed_at']
            
            # 각 exam_id별로 최신 completed_at에 해당하는 결과를 한 번에 조회
            # 여러 결과가 같은 completed_at을 가질 수 있으므로, 추가로 id를 기준으로 정렬
            latest_results = ExamResult.objects.none()  # 빈 queryset으로 초기화
            if latest_completed_at_dict:
                # Q 객체를 사용하여 모든 조건을 OR로 연결 (Q는 파일 상단에서 이미 import됨)
                q_objects = Q()
                for exam_id, latest_at in latest_completed_at_dict.items():
                    q_objects |= Q(exam_id=exam_id, completed_at=latest_at)
                
                # 모든 최신 결과를 한 번에 가져오기 (completed_at 내림차순, id 내림차순)
                latest_results = ExamResult.objects.filter(
                    q_objects,
                    user=request.user
                ).select_related('exam').order_by('-completed_at', '-id')
            
            # 딕셔너리로 변환 (exam_id -> result, UUID를 문자열로 변환)
            # 같은 exam_id에 대해 여러 결과가 있을 수 있으므로, completed_at이 최신인 것만 선택
            for result in latest_results:
                exam_id = str(result.exam_id)
                # 같은 시험에 여러 결과가 있으면 가장 최신 것만 사용
                if exam_id not in user_latest_results_dict:
                    user_latest_results_dict[exam_id] = result
                elif result.completed_at > user_latest_results_dict[exam_id].completed_at:
                    user_latest_results_dict[exam_id] = result
                elif result.completed_at == user_latest_results_dict[exam_id].completed_at:
                    # completed_at이 같으면 id가 더 큰(최신) 것을 선택
                    if result.id > user_latest_results_dict[exam_id].id:
                        user_latest_results_dict[exam_id] = result
            
            # 페이지네이션된 모든 시험 ID를 딕셔너리에 추가 (결과가 없는 경우 None으로 표시)
            # 이렇게 하면 fallback 쿼리를 방지할 수 있음
            for exam in paginated_exams:
                exam_id_str = str(exam.id)
                if exam_id_str not in user_latest_results_dict:
                    # 결과가 없는 시험도 딕셔너리에 추가 (None으로)
                    user_latest_results_dict[exam_id_str] = None
                # 복사된 시험의 경우 원본 시험 ID도 확인
                if not exam.is_original and exam.original_exam_id:
                    original_exam_id_str = str(exam.original_exam_id)
                    if original_exam_id_str in user_latest_results_dict and exam_id_str not in user_latest_results_dict:
                        # 원본 시험의 결과를 복사된 시험 ID로도 매핑
                        user_latest_results_dict[exam_id_str] = user_latest_results_dict[original_exam_id_str]
            
            logger.debug(f"[GET_EXAMS] user_latest_results_dict 크기: {len(user_latest_results_dict)}개, exam_ids: {list(user_latest_results_dict.keys())[:5]}...")
            
            # 모든 시험의 통계를 한 번에 조회 (N+1 쿼리 방지)
            # Count는 이미 상단에서 import됨
            from ..models import ExamResultDetail
            
            # 각 시험별 정답 시도 수 계산
            correct_counts = ExamResultDetail.objects.filter(
                result__exam_id__in=all_exam_ids,
                result__user=request.user,
                is_correct=True
            ).values('result__exam_id').annotate(
                correct_count=Count('id')
            )
            
            # 각 시험별 전체 시도 수 계산
            total_counts = ExamResultDetail.objects.filter(
                result__exam_id__in=all_exam_ids,
                result__user=request.user
            ).values('result__exam_id').annotate(
                total_count=Count('id')
            )
            
            # 딕셔너리로 변환
            correct_counts_dict = {str(item['result__exam_id']): item['correct_count'] for item in correct_counts}
            total_counts_dict = {str(item['result__exam_id']): item['total_count'] for item in total_counts}
            
            # 원본 시험 ID 매핑 생성 (복사된 시험 -> 원본 시험)
            # 이미 가져온 exam_ids를 활용하여 매핑 생성 (추가 쿼리 방지)
            exam_to_original = {}
            copied_exams_for_mapping = base_queryset.filter(
                is_original=False, 
                original_exam_id__isnull=False
            ).values_list('id', 'original_exam_id')
            for exam_id, original_exam_id in copied_exams_for_mapping:
                exam_to_original[str(exam_id)] = str(original_exam_id)
            
            # 각 시험의 통계 계산 (원본 시험 우선)
            # ⚠️ 주의: total_count 변수명을 exam_total_count로 변경하여 페이지네이션의 total_count와 충돌 방지
            for exam_id in all_exam_ids:
                exam_id_str = str(exam_id)
                # 복사된 시험인 경우 원본 시험 ID 사용
                target_exam_id_str = exam_to_original.get(exam_id_str, exam_id_str)
                
                correct_count = correct_counts_dict.get(target_exam_id_str, 0)
                exam_total_count = total_counts_dict.get(target_exam_id_str, 0)  # 변수명 변경: total_count -> exam_total_count
                
                user_correct_questions_dict[exam_id_str] = correct_count
                
                if exam_total_count > 0:
                    user_accuracy_percentage_dict[exam_id_str] = (correct_count / exam_total_count) * 100
                else:
                    user_accuracy_percentage_dict[exam_id_str] = None
    
    # 시리얼라이저 선택 및 직렬화 (성능 측정)
    serializer_start = time.time()
    serializer_queries_before = len(connection.queries)
    
    serializer_context = {
        'request': request,
        'user_language': user_language,
        'user_latest_results_dict': user_latest_results_dict,
        'user_correct_questions_dict': user_correct_questions_dict,
        'user_accuracy_percentage_dict': user_accuracy_percentage_dict
    }
    
    # 시리얼라이저 선택 로직 디버깅
    logger.debug(f"[GET_EXAMS] select_fields: {select_fields}, type: {type(select_fields)}, len: {len(select_fields) if select_fields else 0}")
    has_questions = 'questions' in select_fields if select_fields else False
    has_versions = 'versions' in select_fields if select_fields else False
    logger.debug(f"[GET_EXAMS] 'questions' in select_fields: {has_questions}, 'versions' in select_fields: {has_versions}")
    
    # select_fields가 비어있거나, questions와 versions가 없으면 ExamListSerializer 사용
    use_list_serializer = (not select_fields) or (select_fields and 'questions' not in select_fields and 'versions' not in select_fields)
    logger.debug(f"[GET_EXAMS] use_list_serializer: {use_list_serializer}")
    
    if use_list_serializer:
        serializer = ExamListSerializer(paginated_exams, many=True, context=serializer_context)
        logger.debug(f"[GET_EXAMS] ✅ ExamListSerializer 사용 (최적화됨)")
    else:
        serializer = ExamSerializer(paginated_exams, many=True, context=serializer_context)
        logger.info(f"[GET_EXAMS] ⚠️ ExamSerializer 사용 (questions 또는 versions 포함)")
    
    # 직렬화 실행
    serializer_data = serializer.data
    
    serializer_time = time.time() - serializer_start
    serializer_queries_after = len(connection.queries)
    query_count = serializer_queries_after - serializer_queries_before
    
    # 쿼리 상세 로깅 (처음 10개와 마지막 10개만)
    if query_count > 20:
        logger.warning(f"[GET_EXAMS] 시리얼라이저 직렬화: {query_count}개 쿼리, {serializer_time:.3f}초 (쿼리 수가 많음)")
        logger.debug(f"[GET_EXAMS] 처음 10개 쿼리:")
        for i, q in enumerate(connection.queries[serializer_queries_before:serializer_queries_before+10]):
            logger.debug(f"  {i+1}. {q['sql'][:100]}...")
        logger.debug(f"[GET_EXAMS] 마지막 10개 쿼리:")
        for i, q in enumerate(connection.queries[serializer_queries_after-10:serializer_queries_after]):
            logger.debug(f"  {query_count-9+i}. {q['sql'][:100]}...")
    else:
        logger.debug(f"[GET_EXAMS] 시리얼라이저 직렬화: {query_count}개 쿼리, {serializer_time:.3f}초")
        for i, q in enumerate(connection.queries[serializer_queries_before:serializer_queries_after]):
            logger.debug(f"  {i+1}. {q['sql'][:100]}...")
    
    # 구독 정보 추가 (성능 측정)
    if request.user.is_authenticated:
        subscription_start = time.time()
        subscription_queries_before = len(connection.queries)
        
        exam_ids = [str(exam.id) for exam in paginated_exams]
        
        user_subscriptions = ExamSubscription.objects.filter(
            user=request.user,
            exam_id__in=exam_ids,
            is_active=True
        ).values_list('exam_id', flat=True)
        
        # UUID를 문자열로 변환하여 비교
        user_subscription_ids = set(str(sub_id) for sub_id in user_subscriptions)
        
        # 각 시험에 구독 상태 추가 (set을 사용하여 O(1) 조회)
        for exam_data in serializer_data:
            exam_data['is_subscribed'] = str(exam_data['id']) in user_subscription_ids
        
        subscription_time = time.time() - subscription_start
        subscription_queries_after = len(connection.queries)
        logger.debug(f"[GET_EXAMS] 구독 정보 조회: {subscription_queries_after - subscription_queries_before}개 쿼리, {subscription_time:.3f}초, {len(exam_ids)}개 시험")
    else:
        logger.debug("[GET_EXAMS] 익명 사용자이므로 구독 정보 추가하지 않음")
    
    # total_pages 계산 (올림 처리)
    # total_count가 0이면 total_pages도 0이어야 함
    if total_count == 0:
        total_pages = 0
    else:
        total_pages = (total_count + page_size - 1) // page_size
    has_next = end_index < total_count
    has_previous = page > 1
    
    logger.info(f"[GET_EXAMS] 페이지네이션 최종 정보: page={page}, total_count={total_count}, page_size={page_size}, total_pages={total_pages}, has_next={has_next}, has_previous={has_previous}, results_count={len(serializer_data)}")
    
    response_data = {
        'results': serializer_data,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total_count': total_count,
            'total_pages': total_pages,
            'has_next': has_next,
            'has_previous': has_previous
        },
        'filters': {
            'is_public': is_public_param,
            'my_exams': my_exams_param,
            'search_title': search_title,
            'select_fields': select_fields,
            'tags': tag_ids
        }
    }
    
    # 캐시에 저장 (비동기 처리로 성능 개선)
    cache_start = time.time()
    try:
        # Celery 태스크로 비동기 저장
        from quiz.tasks import save_exam_list_cache
        # cache_key_params에 이미 page와 page_size가 포함되어 있으므로 별도로 전달하지 않음
        save_exam_list_cache.delay(user_id, response_data, **cache_key_params)
        cache_time = time.time() - cache_start
        logger.info(f"[GET_EXAMS] 캐시 저장 Celery 태스크 전송 완료 ({cache_time:.3f}초)")
    except Exception as e:
        # Celery 태스크 전송 실패 시 동기 저장으로 폴백
        logger.warning(f"[GET_EXAMS] Celery 태스크 전송 실패, 동기 저장으로 폴백: {str(e)}")
        ExamCacheManager.set_exam_list_cache(user_id, response_data, **cache_key_params)
        cache_time = time.time() - cache_start
        logger.info(f"[GET_EXAMS] 캐시 저장 완료 (동기 저장, {cache_time:.3f}초)")
    
    # 전체 성능 측정 결과
    total_time = time.time() - start_time
    total_queries = len(connection.queries) - initial_queries
    
    logger.info(f"[GET_EXAMS] ⚡ 성능 요약 - 총 시간: {total_time:.3f}초, 총 쿼리: {total_queries}개")
    logger.info(f"[GET_EXAMS]   - 캐시 저장: {cache_time:.3f}초")
    logger.info(f"[GET_EXAMS]   - 결과 수: {len(serializer.data)}개, 전체: {total_count}개")
    
    # 쿼리 상세 로깅 (DEBUG 레벨)
    if logger.isEnabledFor(logging.DEBUG):
        for i, query in enumerate(connection.queries[initial_queries:], 1):
            logger.debug(f"[GET_EXAMS] 쿼리 {i}: {query['time']}초 - {query['sql'][:200]}")
    
    return Response(response_data)


@api_view(['POST'])
def save_random_practice_result(request):
    """랜덤 연습 결과를 저장합니다."""
    try:
        study_id = request.data.get('study_id')
        correct_count = request.data.get('correct_count', 0)
        total_questions = request.data.get('total_questions', 0)
        elapsed_seconds = request.data.get('elapsed_seconds', 0)

        if not study_id:
            return Response({'error': '스터디 ID가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            study = Study.objects.get(id=study_id)
        except Study.DoesNotExist:
            return Response({'error': '스터디를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        # 기존 랜덤 연습 시험 찾기 (다국어 필드 사용)
        study_title = study.title_ko if study.title_ko else study.title_en or '제목 없음'
        existing_exam = Exam.objects.filter(
            models.Q(title_ko__startswith=f"{study_title} - 랜덤 연습") | 
            models.Q(title_en__startswith=f"{study_title} - 랜덤 연습"),
            is_original=True
        ).first()

        if existing_exam:
            # 기존 시험이 있으면 버전 생성
            latest_version = Exam.objects.filter(original_exam=existing_exam).order_by('-version_number').first()
            next_version = (latest_version.version_number + 1) if latest_version else 1

            exam = Exam.objects.create(
                total_questions=total_questions,
                original_exam=existing_exam,
                version_number=next_version,
                is_original=False
            )
            
            # 다국어 필드 설정
            exam.title_ko = f"{study_title} - 랜덤 연습"
            exam.title_en = f"{study_title} - Random Practice"
            exam.save()
        else:
            # 첫 번째 랜덤 연습이면 원본 시험 생성
            exam = Exam.objects.create(
                total_questions=total_questions,
                is_original=True
            )
            
            # 다국어 필드 설정
            exam.title_ko = f"{study_title} - 랜덤 연습"
            exam.title_en = f"{study_title} - Random Practice"
            exam.save()

        # 시험 결과 생성
        result = ExamResult.objects.create(
            exam=exam,
            user=request.user,
            score=correct_count,
            total_score=total_questions,
            correct_count=correct_count,
            wrong_count=total_questions - correct_count,
            elapsed_seconds=elapsed_seconds
        )

        # 랜덤 연습 결과에 대한 StudyTaskProgress 업데이트
        if request.user.is_authenticated:
            try:
                # 스터디의 모든 Task에 대해 진행율 업데이트
                study_tasks = StudyTask.objects.filter(study=study)
                
                for study_task in study_tasks:
                    # 랜덤 연습은 전체 스터디 진행율에 기여하므로 작은 비율로 계산
                    # 예: 3문제 중 2문제 맞춤 = 약 2% 기여 (전체 스터디 기준)
                    if total_questions > 0:
                        # 랜덤 연습의 기여도를 전체 스터디 기준으로 계산
                        # 전체 스터디 문제 수를 고려하여 비율 조정
                        total_study_questions = sum(task.exam.total_questions for task in study_tasks if task.exam)
                        if total_study_questions > 0:
                            # 랜덤 연습 기여도 = (맞춘 문제 수 / 전체 스터디 문제 수) * 100
                            progress_contribution = (correct_count / total_study_questions) * 100
                        else:
                            progress_contribution = 0
                    else:
                        progress_contribution = 0

                    # StudyTaskProgress 업데이트 또는 생성
                    progress_obj, created = StudyTaskProgress.objects.get_or_create(
                        user=request.user,
                        study_task=study_task,
                        defaults={'progress': progress_contribution}
                    )

                    if not created:
                        # 기존 기록이 있으면 진행률 업데이트 (더 높은 값으로)
                        if progress_contribution > progress_obj.progress:
                            progress_obj.progress = progress_contribution
                            progress_obj.save()

                    print(f"StudyTaskProgress 업데이트 (랜덤 연습): {request.user.username} - {study_task.name} - {progress_contribution}%")

            except Exception as e:
                print(f"랜덤 연습 StudyTaskProgress 업데이트 중 오류: {str(e)}")

        result_serializer = ExamResultSerializer(result)
        return Response(result_serializer.data, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': f'랜덤 연습 결과 저장 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_answer(request):
    """AI를 사용하여 사용자 답안이 정답과 의미적으로 일치하는지 판단합니다."""
    try:
        user_answer = request.data.get('user_answer', '').strip()
        correct_answer = request.data.get('correct_answer', '').strip()
        language = request.data.get('language', 'en')
        
        if not user_answer or not correct_answer:
            return Response({
                'error': '사용자 답안과 정답이 필요합니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        from quiz.utils.multilingual_utils import check_answer_with_ai
        result = check_answer_with_ai(user_answer, correct_answer, language)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"[CHECK_ANSWER_API] 답안 판단 중 오류: {e}")
        return Response({
            'error': f'답안 판단 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def download_exams_excel(request):
    """시험 정보를 Excel 파일로 다운로드합니다."""
    try:
        user_lang = get_user_language(request)
        # 모든 시험 정보 조회
        exams = Exam.objects.all().order_by('-created_at')

        # Excel 파일 생성
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 시험 기본 정보
            exam_data = []
            for exam in exams:
                exam_data.append({
                    '시험ID': exam.id,
                    '시험제목': get_localized_field(exam, 'title', user_lang, 'Unknown'),
                    '문제수': ExamQuestion.objects.filter(exam=exam).count(),
                    '연결된파일': exam.file_name or '',
                    '생성일': exam.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    '원본여부': '예' if exam.is_original else '아니오'
                })

            exam_df = pd.DataFrame(exam_data)
            exam_df.to_excel(writer, sheet_name='시험목록', index=False)

            # 시험별 문제 상세 정보
            for exam in exams:
                exam_questions = ExamQuestion.objects.filter(exam=exam).select_related('question').order_by('order')

                question_data = []
                for eq in exam_questions:
                    question = eq.question
                    question_title = get_localized_field(question, 'title', user_lang, '제목 없음')
                    question_data.append({
                        '문제ID': question.id,
                        '문제제목': question_title,
                                        '문제내용': question.content_ko or question.content_en or '',
                '정답': question.answer_ko or question.answer_en or '',
                '설명': question.explanation_ko or question.explanation_en or '',
                        '난이도': format_difficulty_for_excel(question.difficulty),
                        'URL': question.url or '',
                        '순서': eq.order
                    })

                if question_data:
                    question_df = pd.DataFrame(question_data)
                    # 시트명 생성 (안전한 방식)
                    title = exam.title_ko or exam.title_en or "Unknown"
                    sheet_name = f'시험{exam.id}_{title[:20]}'  # 시트명 길이 제한
                    question_df.to_excel(writer, sheet_name=sheet_name, index=False)

        output.seek(0)

        # 파일명 생성
        filename = 'exams.xlsx'

        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    except Exception as e:
        import traceback; traceback.print_exc()
        return Response({'detail': f'Excel 다운로드 중 오류가 발생했습니다: {str(e)}'}, status=500)


@api_view(['POST'])
def upload_exams_excel(request):
    """Excel 파일로 시험 정보를 업로드합니다."""
    try:
        if 'file' not in request.FILES:
            return Response({'detail': '파일이 업로드되지 않았습니다.'}, status=400)

        file = request.FILES['file']

        # 파일 확장자 확인
        if not file.name.endswith(('.xlsx', '.xls')):
            return Response({'detail': 'Excel 파일(.xlsx, .xls)만 업로드 가능합니다.'}, status=400)

        # Excel 파일 읽기
        try:
            excel_file = pd.ExcelFile(file)
        except Exception as e:
            return Response({'detail': f'Excel 파일 읽기 실패: {str(e)}'}, status=400)

        stats = {
            'total_exams': 0,
            'created': 0,
            'skipped': 0,
            'errors': 0,
            'error_details': []
        }

        # 시험 목록 시트 처리
        if '시험목록' in excel_file.sheet_names:
            try:
                exam_list_df = pd.read_excel(file, sheet_name='시험목록')

                for index, row in exam_list_df.iterrows():
                    try:
                        exam_title = row.get('시험제목')
                        file_name = row.get('연결된파일')
                        total_questions = row.get('문제수')

                        if pd.isna(exam_title) or not exam_title:
                            stats['errors'] += 1
                            stats['error_details'].append(f'행 {index + 2}: 시험제목이 비어있습니다.')
                            continue

                        # 기존 시험 확인 (제목으로)
                        existing_exam = Exam.objects.filter(title=exam_title).first()
                        if existing_exam:
                            stats['skipped'] += 1
                            continue

                        # 새 시험 생성
                        exam = Exam.objects.create(
                            title=exam_title,
                            is_original=True,
                            file_name=file_name,
                            total_questions=total_questions
                        )
                        stats['created'] += 1
                        stats['total_exams'] += 1

                        # 연결된 파일에서 문제 읽어와 시험에 연결
                        if file_name and not pd.isna(file_name):
                            try:
                                file_path = os.path.join(QUESTION_FILES_DIR, file_name)
                                if os.path.exists(file_path):
                                    file_extension = os.path.splitext(file_name)[1].lower()

                                    # 파일에서 문제 읽기
                                    if file_extension == '.csv':
                                        with open(file_path, 'r', encoding='utf-8') as f:
                                            content = f.read()
                                            corrected_file = auto_correct_csv_from_content(content)
                                            df = pd.read_csv(corrected_file)
                                    else:  # .xlsx, .xls
                                        if file_extension == '.xlsx':
                                            df = pd.read_excel(file_path, engine='openpyxl')
                                        else:
                                            df = pd.read_excel(file_path, engine='xlrd')

                                    # 문제 수만큼 문제 찾아서 시험에 연결
                                    questions_to_add = []
                                    for _, q_row in df.iterrows():
                                        try:
                                            question_title = q_row.get('제목')
                                            if pd.isna(question_title) or not question_title:
                                                continue

                                            # 기존 문제 확인 (한국어와 영어 제목 모두에서 검색)
                                            question = Question.objects.filter(
                                                models.Q(title_ko=question_title) | models.Q(title_en=question_title)
                                            ).first()
                                            if question:
                                                questions_to_add.append(question)

                                                # 문제 수에 도달하면 중단
                                                if len(questions_to_add) >= total_questions:
                                                    break

                                        except Exception as e:
                                            continue

                                    # 시험에 문제 추가
                                    for i, question in enumerate(questions_to_add):
                                        if not ExamQuestion.objects.filter(exam=exam, question=question).exists():
                                            ExamQuestion.objects.create(
                                                exam=exam,
                                                question=question,
                                                order=i + 1
                                            )

                                    # 실제 연결된 문제 수로 total_questions 업데이트
                                    actual_count = ExamQuestion.objects.filter(exam=exam).count()
                                    exam.total_questions = actual_count
                                    exam.save()

                                else:
                                    stats['errors'] += 1
                                    stats['error_details'].append(f'행 {index + 2}: 연결된 파일을 찾을 수 없습니다: {file_name}')

                            except Exception as e:
                                stats['errors'] += 1
                                stats['error_details'].append(f'행 {index + 2}: 연결된 파일 처리 오류: {str(e)}')

                    except Exception as e:
                        stats['errors'] += 1
                        stats['error_details'].append(f'행 {index + 2}: {str(e)}')
                        continue

            except Exception as e:
                stats['errors'] += 1
                stats['error_details'].append(f'시험목록 시트 처리 오류: {str(e)}')

        return Response({
            'message': f'Excel 파일 업로드가 완료되었습니다.',
            'stats': stats
        }, status=200)

    except Exception as e:
        return Response({'detail': f'Excel 업로드 중 오류가 발생했습니다: {str(e)}'}, status=500)


@api_view(['POST'])
def move_questions(request):
    """문제를 한 시험에서 다른 시험으로 이동합니다."""
    if not request.user.is_authenticated:
        return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)
    
    # 권한 확인: 관리자, 스터디 관리자, 또는 생성자
    has_permission = False
    
    # 1. 관리자 권한 확인
    try:
        user_profile = request.user.profile
        user_role = user_profile.role
        if user_role in ['admin_role', 'study_admin_role']:
            has_permission = True
    except:
        user_role = None
    
    # 2. 스터디 관리자 권한 확인 (Member 테이블에서)
    if not has_permission:
        from quiz.models import Member
        is_study_admin = Member.objects.filter(
            user=request.user,
            is_active=True,
            role__in=['study_admin', 'study_leader']
        ).exists()
        if is_study_admin:
            has_permission = True
    
    # 3. 생성자 권한 확인 (from_exam의 생성자인지)
    if not has_permission:
        from_exam_id = request.data.get('from_exam_id')
        if from_exam_id:
            try:
                from_exam = Exam.objects.get(id=from_exam_id, created_by=request.user)
                has_permission = True
            except Exam.DoesNotExist:
                pass
    
    if not has_permission:
        return Response({'error': '관리자, 스터디 관리자 또는 생성자 권한이 필요합니다.'}, status=status.HTTP_403_FORBIDDEN)
    
    from_exam_id = request.data.get('from_exam_id')
    to_exam_id = request.data.get('to_exam_id')
    question_ids = request.data.get('question_ids', [])

    print(f"move_questions 호출됨:")
    print(f"from_exam_id: {from_exam_id}")
    print(f"to_exam_id: {to_exam_id}")
    print(f"question_ids: {question_ids}")

    if not from_exam_id or not to_exam_id or not question_ids:
        return Response({'error': '필수 파라미터 누락'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        from_exam = Exam.objects.get(id=from_exam_id)
        to_exam = Exam.objects.get(id=to_exam_id)

        print(f"from_exam: {from_exam.title_ko or from_exam.title_en or 'Unknown'}")
        print(f"to_exam: {to_exam.title_ko or to_exam.title_en or 'Unknown'}")

        # 문제들이 from_exam에 실제로 존재하는지 확인
        existing_questions = ExamQuestion.objects.filter(
            exam=from_exam,
            question_id__in=question_ids
        )

        print(f"from_exam에 존재하는 문제 수: {len(existing_questions)}")
        print(f"요청된 문제 수: {len(question_ids)}")

        if len(existing_questions) != len(question_ids):
            return Response({'error': '일부 문제가 소스 시험에 존재하지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # to_exam에 이미 존재하는 문제들 삭제 (덮어쓰기)
        target_existing = ExamQuestion.objects.filter(
            exam=to_exam,
            question_id__in=question_ids
        )

        print(f"to_exam에 이미 존재하는 문제 수: {len(target_existing)}")

        # 기존 문제들을 삭제 (덮어쓰기)
        target_existing.delete()

        # from_exam에서 제거
        ExamQuestion.objects.filter(exam=from_exam, question_id__in=question_ids).delete()

        # to_exam에 추가 (order는 마지막+1로)
        current_count = ExamQuestion.objects.filter(exam=to_exam).count()
        for idx, qid in enumerate(question_ids):
            ExamQuestion.objects.create(
                exam=to_exam,
                question_id=qid,
                order=current_count + idx + 1
            )

        # 시험의 총 문제 수 업데이트
        from_exam.total_questions = ExamQuestion.objects.filter(exam=from_exam).count()
        to_exam.total_questions = ExamQuestion.objects.filter(exam=to_exam).count()
        from_exam.save()
        to_exam.save()

        return Response({'success': True}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def copy_questions(request):
    """문제를 한 시험에서 다른 시험으로 복사합니다."""
    if not request.user.is_authenticated:
        return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)
    
    # 권한 확인: 관리자, 스터디 관리자, 또는 생성자
    has_permission = False
    
    # 1. 관리자 권한 확인
    try:
        user_profile = request.user.profile
        user_role = user_profile.role
        if user_role in ['admin_role', 'study_admin_role']:
            has_permission = True
    except:
        user_role = None
    
    # 2. 스터디 관리자 권한 확인 (Member 테이블에서)
    if not has_permission:
        from quiz.models import Member
        is_study_admin = Member.objects.filter(
            user=request.user,
            is_active=True,
            role__in=['study_admin', 'study_leader']
        ).exists()
        if is_study_admin:
            has_permission = True
    
    # 3. 생성자 권한 확인 (from_exam의 생성자인지)
    if not has_permission:
        from_exam_id = request.data.get('from_exam_id')
        if from_exam_id:
            try:
                from_exam = Exam.objects.get(id=from_exam_id, created_by=request.user)
                has_permission = True
            except Exam.DoesNotExist:
                pass
    
    if not has_permission:
        return Response({'error': '관리자, 스터디 관리자 또는 생성자 권한이 필요합니다.'}, status=status.HTTP_403_FORBIDDEN)
    
    from_exam_id = request.data.get('from_exam_id')
    to_exam_id = request.data.get('to_exam_id')
    question_ids = request.data.get('question_ids', [])
    if not from_exam_id or not to_exam_id or not question_ids:
        return Response({'error': '필수 파라미터 누락'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        to_exam = Exam.objects.get(id=to_exam_id)

        # to_exam에 이미 존재하는 문제들 확인
        existing_questions = ExamQuestion.objects.filter(
            exam=to_exam,
            question_id__in=question_ids
        )

        if existing_questions.exists():
            return Response({'error': '일부 문제가 이미 타겟 시험에 존재합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # to_exam에 추가 (order는 마지막+1로)
        current_count = ExamQuestion.objects.filter(exam=to_exam).count()
        for idx, qid in enumerate(question_ids):
            ExamQuestion.objects.create(
                exam=to_exam,
                question_id=qid,
                order=current_count + idx + 1
            )

        # 시험의 총 문제 수 업데이트
        to_exam.total_questions = ExamQuestion.objects.filter(exam=to_exam).count()
        to_exam.save()

        return Response({'success': True}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def delete_questions(request):
    """선택된 문제들을 삭제합니다."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)

        question_ids = request.data.get('question_ids', [])
        exam_id = request.data.get('exam_id')  # 시험 ID 추가
        if not question_ids:
            return Response({'error': '삭제할 문제 ID가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # admin_role 사용자는 모든 문제 삭제 가능
        is_admin = False
        if hasattr(user, 'is_superuser') and user.is_superuser:
            is_admin = True
        elif hasattr(user, 'profile') and hasattr(user.profile, 'role') and user.profile.role == 'admin_role':
            is_admin = True

        # 시험 정보 확인 (복사본 여부 판단용)
        current_exam = None
        is_copy_exam = False
        if exam_id:
            try:
                current_exam = Exam.objects.get(id=exam_id)
                is_copy_exam = not current_exam.is_original
                print(f"[DELETE_QUESTIONS] 현재 시험: {current_exam.title_ko or current_exam.title_en or 'Unknown'} (ID: {current_exam.id})")
                print(f"[DELETE_QUESTIONS] 복사본 시험 여부: {is_copy_exam}")
            except Exam.DoesNotExist:
                print(f"[DELETE_QUESTIONS] 시험 {exam_id}를 찾을 수 없습니다.")

        if not is_admin:
            # 문제가 속한 시험들을 확인하여 권한 검증
            questions = Question.objects.filter(id__in=question_ids).prefetch_related('examquestion_set__exam')
            
            # 사용자가 관리자인 스터디 목록 가져오기
            user_admin_studies = Study.objects.filter(
                members__user=user,
                members__is_active=True,
                members__role__in=['study_admin', 'study_leader']
            ).values_list('id', flat=True)
            
            print(f"[DELETE_QUESTIONS] 사용자가 관리자인 스터디: {list(user_admin_studies)}")
            
            for question in questions:
                # 각 문제가 속한 시험들을 확인
                for exam_question in question.examquestion_set.all():
                    exam = exam_question.exam
                    
                    # 시험 생성자 또는 스터디 관리자인지 확인
                    is_creator = exam.created_by == user
                    is_study_admin = False
                    
                    # StudyTask를 통해 연결된 스터디 확인
                    study_task = StudyTask.objects.filter(exam=exam).first()
                    if study_task and study_task.study:
                        is_study_admin = study_task.study.id in user_admin_studies
                    
                    print(f"[DELETE_QUESTIONS] 사용자: {user.username} (ID: {user.id})")
                    print(f"[DELETE_QUESTIONS] 시험: {exam.title_ko or exam.title_en or 'Unknown'} (ID: {exam.id})")
                    print(f"[DELETE_QUESTIONS] 시험 생성자: {exam.created_by.username if exam.created_by else 'None'}")
                    print(f"[DELETE_QUESTIONS] is_creator: {is_creator}")
                    print(f"[DELETE_QUESTIONS] study_task: {study_task}")
                    if study_task:
                        study_title = study_task.study.title_ko if study_task.study.title_ko else study_task.study.title_en or '제목 없음' if study_task.study else 'None'
                        print(f"[DELETE_QUESTIONS] study: {study_title}")
                        print(f"[DELETE_QUESTIONS] is_study_admin: {is_study_admin}")
                    
                    if not (is_creator or is_study_admin):
                        return Response({'error': f'문제 {question.id}를 삭제할 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)

        # 복사본 시험인 경우: 문제를 실제로 삭제하지 않고 시험-문제 연결만 제거
        if is_copy_exam and current_exam:
            print(f"[DELETE_QUESTIONS] 복사본 시험에서 문제 제거: 시험-문제 연결만 삭제")
            
            # 현재 시험에서 선택된 문제들의 연결만 제거
            removed_count = ExamQuestion.objects.filter(
                exam=current_exam,
                question_id__in=question_ids
            ).delete()[0]
            
            # 시험의 총 문제 수 업데이트
            current_exam.total_questions = ExamQuestion.objects.filter(exam=current_exam).count()
            current_exam.save()
            
            print(f"[DELETE_QUESTIONS] 복사본 시험에서 {removed_count}개 문제 연결 제거 완료")
            
            return Response({
                'message': f'복사본 시험에서 {removed_count}개의 문제가 제거되었습니다. (원본 문제는 유지됨)',
                'deleted_count': removed_count,
                'is_copy_exam': True
            }, status=status.HTTP_200_OK)
        else:
            # 원본 시험이거나 시험 ID가 없는 경우: 문제를 실제로 삭제
            print(f"[DELETE_QUESTIONS] 원본 시험에서 문제 삭제: 문제 자체를 삭제")
            deleted_count = Question.objects.filter(id__in=question_ids).delete()[0]
            
            return Response({
                'message': f'{deleted_count}개의 문제가 삭제되었습니다.',
                'deleted_count': deleted_count,
                'is_copy_exam': False
            }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': f'문제 삭제 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_or_create_favorite_exam(request):
    """사용자의 favorite 시험을 조회하거나 생성합니다."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)

        # 사용자의 favorite 시험 찾기 (가장 오래된 것을 우선)
        favorite_exams = Exam.objects.filter(
            title_ko=f"{user.username}'s favorite",
            is_original=True
        ).order_by('created_at')
        
        if favorite_exams.exists():
            # 기존 favorite 시험이 있으면 첫 번째 것을 사용
            favorite_exam = favorite_exams.first()
            
            # 중복된 favorite 시험이 있으면 나머지는 삭제
            if favorite_exams.count() > 1:
                for duplicate_exam in favorite_exams[1:]:
                    # 중복 시험의 문제들을 첫 번째 시험으로 이동
                    duplicate_questions = ExamQuestion.objects.filter(exam=duplicate_exam)
                    for eq in duplicate_questions:
                        # 이미 첫 번째 시험에 같은 문제가 있는지 확인
                        existing = ExamQuestion.objects.filter(
                            exam=favorite_exam,
                            question=eq.question
                        ).first()
                        if not existing:
                            eq.exam = favorite_exam
                            eq.save()
                    
                    # 중복 시험 삭제
                    duplicate_exam.delete()
                
                # 첫 번째 시험의 총 문제 수 업데이트
                favorite_exam.total_questions = ExamQuestion.objects.filter(exam=favorite_exam).count()
                favorite_exam.save()
        else:
            # favorite 시험이 없으면 생성 (비공개로 설정)
            favorite_exam = Exam.objects.create(
                title_ko=f"{user.username}'s favorite",
                total_questions=0,
                is_original=True,
                is_public=False  # 비공개로 설정
            )

        serializer = ExamSerializer(favorite_exam, context={'request': request})
        return Response(serializer.data)

    except Exception as e:
        return Response({'error': f'favorite 시험 조회 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def add_question_to_favorite(request):
    """문제를 favorite 시험에 추가합니다."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)

        # 캐시 무효화
        try:
            from django.core.cache import cache
            cache.delete_pattern("favorites_*")
            print(f"[add_question_to_favorite] 캐시 삭제 완료")
        except Exception as e:
            print(f"[add_question_to_favorite] 캐시 삭제 실패: {e}")

        question_id = request.data.get('question_id')
        if not question_id:
            return Response({'error': '문제 ID가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 문제 존재 확인
        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return Response({'error': '문제를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        # 무시된 문제인지 확인 (자동 해제하지 않음)
        ignored_question = IgnoredQuestion.objects.filter(user=user, question=question).first()
        is_ignored = ignored_question is not None

        # 사용자의 favorite 시험 찾기 또는 생성 (가장 오래된 것을 우선)
        favorite_exams = Exam.objects.filter(
            title_ko=f"{user.username}'s favorite",
            is_original=True
        ).order_by('created_at')
        
        if favorite_exams.exists():
            # 기존 favorite 시험이 있으면 첫 번째 것을 사용
            favorite_exam = favorite_exams.first()
            
            # 중복된 favorite 시험이 있으면 나머지는 삭제
            if favorite_exams.count() > 1:
                for duplicate_exam in favorite_exams[1:]:
                    # 중복 시험의 문제들을 첫 번째 시험으로 이동
                    duplicate_questions = ExamQuestion.objects.filter(exam=duplicate_exam)
                    for eq in duplicate_questions:
                        # 이미 첫 번째 시험에 같은 문제가 있는지 확인
                        existing = ExamQuestion.objects.filter(
                            exam=favorite_exam,
                            question=eq.question
                        ).first()
                        if not existing:
                            eq.exam = favorite_exam
                            eq.save()
                    
                    # 중복 시험 삭제
                    duplicate_exam.delete()
                
                # 첫 번째 시험의 총 문제 수 업데이트
                favorite_exam.total_questions = ExamQuestion.objects.filter(exam=favorite_exam).count()
                favorite_exam.save()
        else:
            favorite_exam = Exam.objects.create(
                title_ko=f"{user.username}'s favorite",
                total_questions=0,
                is_original=True,
                is_public=False  # 비공개로 설정
            )

        # 이미 favorite에 추가되어 있는지 확인
        existing_question = ExamQuestion.objects.filter(
            exam=favorite_exam,
            question=question
        ).first()

        if existing_question:
            # 이미 favorite에 있는 경우 제거
            existing_question.delete()
            
            # 시험의 총 문제 수 업데이트
            favorite_exam.total_questions = ExamQuestion.objects.filter(exam=favorite_exam).count()
            favorite_exam.save()
            
            return Response({
                'message': '문제가 favorite에서 제거되었습니다.',
                'favorite_exam_id': favorite_exam.id,
                'is_favorite': False
            }, status=status.HTTP_200_OK)
        else:
            # favorite에 없는 경우 추가
            max_order = ExamQuestion.objects.filter(exam=favorite_exam).aggregate(
                models.Max('order')
            )['order__max'] or 0

            ExamQuestion.objects.create(
                exam=favorite_exam,
                question=question,
                order=max_order + 1
            )

            # 자동 번역 로직: 어떤 언어든 콘텐츠가 있지만 영어 콘텐츠가 없는 경우
            try:
                if not question.content_en:
                    from quiz.utils.multilingual_utils import (
                        batch_translate_texts, 
                        is_auto_translation_enabled,
                        LANGUAGE_KO, LANGUAGE_EN, LANGUAGE_ES, LANGUAGE_ZH, LANGUAGE_JA
                    )
                    
                    if is_auto_translation_enabled(request.user):
                        # 우선순위: ko → es → zh → ja 순서로 번역 시도
                        source_content = None
                        source_language = None
                        
                        if question.content_ko:
                            source_content = question.content_ko
                            source_language = LANGUAGE_KO
                        elif getattr(question, 'content_es', None):
                            source_content = getattr(question, 'content_es', '')
                            source_language = LANGUAGE_ES
                        elif getattr(question, 'content_zh', None):
                            source_content = getattr(question, 'content_zh', '')
                            source_language = LANGUAGE_ZH
                        elif getattr(question, 'content_ja', None):
                            source_content = getattr(question, 'content_ja', '')
                            source_language = LANGUAGE_JA
                        
                        if source_content and source_language:
                            # 해당 언어 → 영어 번역
                            translated_texts = batch_translate_texts([source_content], source_language, LANGUAGE_EN)
                            if translated_texts and translated_texts[0]:
                                question.content_en = translated_texts[0]
                                question.save()
                                print(f"[add_question_to_favorite] 문제 {question.id} {source_language} → 영어 번역 완료")
                            else:
                                print(f"[add_question_to_favorite] 문제 {question.id} {source_language} → 영어 번역 실패")
                    else:
                        print(f"[add_question_to_favorite] 사용자 설정으로 자동 번역이 비활성화되어 번역을 건너뜀 (question_id={question.id})")
                        
            except Exception as e:
                print(f"[add_question_to_favorite] 자동 번역 중 오류: {e}")

            # 시험의 총 문제 수 업데이트
            favorite_exam.total_questions = ExamQuestion.objects.filter(exam=favorite_exam).count()
            favorite_exam.save()

            return Response({
                'message': '문제가 favorite에 추가되었습니다.',
                'favorite_exam_id': favorite_exam.id,
                'is_favorite': True
            }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': f'favorite 추가 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_favorite_exam_questions(request):
    """사용자의 favorite 시험 문제들을 조회합니다 (캐싱 지원)."""
    import time
    start_time = time.time()
    
    logger.info(f"[FAVORITE_API] API 호출 시작 - 사용자: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
    logger.info(f"[FAVORITE_API] 요청 파라미터: {dict(request.GET)}")
    logger.info(f"[FAVORITE_API] 요청 헤더 User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}")
    
    try:
        user = request.user
        if not user.is_authenticated:
            logger.warning(f"[FAVORITE_API] 인증되지 않은 사용자 접근")
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)

        from django.core.cache import cache
        
        # 캐시 키 생성
        cache_key = f"favorites_{user.id}"
        
        # 강제 새로고침 파라미터 확인
        force_refresh = request.GET.get('t')
        if force_refresh:
            logger.info(f"[FAVORITE_API] 강제 새로고침 요청됨")
            try:
                if hasattr(cache, 'delete_pattern'):
                    cache.delete_pattern("favorites_*")
                    logger.info(f"[FAVORITE_API] 캐시 삭제 완료")
                else:
                    cache.delete(cache_key)
                    logger.info(f"[FAVORITE_API] 캐시 삭제 완료 (로컬 캐시)")
            except Exception as e:
                logger.warning(f"[FAVORITE_API] 캐시 삭제 실패: {e}")

        # 캐시에서 데이터 확인 (강제 새로고침이 아닌 경우에만)
        if not force_refresh:
            cache_start = time.time()
            cached_data = cache.get(cache_key)
            cache_time = time.time() - cache_start
            if cached_data:
                total_time = time.time() - start_time
                logger.info(f"[FAVORITE_API] 캐시 히트: user_id={user.id}, 캐시 조회 시간={cache_time*1000:.2f}ms, 총 시간={total_time*1000:.2f}ms")
                return Response(cached_data)

        # 사용자의 favorite 시험 찾기 (가장 오래된 것을 우선)
        db_start = time.time()
        favorite_exams = Exam.objects.filter(
            models.Q(title_ko=f"{user.username}'s favorite") | models.Q(title_en=f"{user.username}'s favorite"),
            is_original=True
        ).order_by('created_at')
        
        if not favorite_exams.exists():
            response_data = {'questions': [], 'exam': None}
            # 빈 결과도 캐시에 저장
            cache.set(cache_key, response_data, 300)
            return Response(response_data, status=status.HTTP_200_OK)
        
        # 첫 번째 favorite 시험 사용
        favorite_exam = favorite_exams.first()
        
        # 중복된 favorite 시험이 있으면 Celery로 비동기 정리 (응답 시간 단축)
        if favorite_exams.count() > 1:
            try:
                from quiz.tasks import cleanup_duplicate_favorite_exams
                cleanup_duplicate_favorite_exams.delay(user.id, favorite_exam.id, [exam.id for exam in favorite_exams[1:]])
                logger.info(f"[FAVORITE_API] 중복 시험 정리 Celery 태스크 전송 완료: user_id={user.id}")
            except Exception as e:
                # Celery 태스크 전송 실패 시 동기 처리로 폴백 (느리지만 정확함)
                logger.warning(f"[FAVORITE_API] Celery 태스크 전송 실패, 동기 처리로 폴백: {str(e)}")
                for duplicate_exam in favorite_exams[1:]:
                    duplicate_questions = ExamQuestion.objects.filter(exam=duplicate_exam)
                    for eq in duplicate_questions:
                        existing = ExamQuestion.objects.filter(
                            exam=favorite_exam,
                            question=eq.question
                        ).first()
                        if not existing:
                            eq.exam = favorite_exam
                            eq.save()
                    duplicate_exam.delete()
                favorite_exam.total_questions = ExamQuestion.objects.filter(exam=favorite_exam).count()
                favorite_exam.save()
        
        db_time = time.time() - db_start

        # Favorites 페이지에서는 favorite이거나 ignored된 문제들만 반환
        query_start = time.time()
        favorite_question_ids = set(
            ExamQuestion.objects.filter(exam=favorite_exam)
            .values_list('question_id', flat=True)
        )
        
        ignored_question_ids = set(
            IgnoredQuestion.objects.filter(user=user)
            .values_list('question_id', flat=True)
        )
        
        # favorite이거나 ignored된 문제들만 조회 (최적화: select_related 추가)
        all_relevant_ids = favorite_question_ids.union(ignored_question_ids)
        questions = Question.objects.filter(id__in=all_relevant_ids).select_related('created_by')

        logger.info(f"[FAVORITE_API] Found {len(favorite_question_ids)} favorite questions for user {user.username}")
        logger.info(f"[FAVORITE_API] Found {len(ignored_question_ids)} ignored questions for user {user.username}")
        logger.info(f"[FAVORITE_API] Total relevant questions: {len(all_relevant_ids)}")
        
        # 사용자별 문제 통계를 미리 계산 (N+1 쿼리 방지)
        from ..models import ExamResultDetail
        from django.db.models import Count, Q
        
        # 모든 문제의 시도 횟수와 정답 횟수를 한 번에 조회
        question_stats = ExamResultDetail.objects.filter(
            question_id__in=all_relevant_ids,
            result__user=user
        ).values('question_id').annotate(
            attempt_count=Count('id'),
            correct_count=Count('id', filter=Q(is_correct=True))
        )
        
        # 딕셔너리로 변환 (question_id -> {attempt_count, correct_count})
        question_stats_dict = {}
        for stat in question_stats:
            question_id = stat['question_id']
            question_stats_dict[question_id] = {
                'attempt_count': stat['attempt_count'],
                'correct_count': stat['correct_count'],
                'correct_rate': (stat['correct_count'] / stat['attempt_count'] * 100) if stat['attempt_count'] > 0 else 0
            }
        
        # favorite과 ignored 상태를 문자열로 변환하여 빠른 조회 (O(1))
        favorite_question_ids_str = {str(fav_id) for fav_id in favorite_question_ids}
        ignored_question_ids_str = {str(ignored_id) for ignored_id in ignored_question_ids}
        
        # 시리얼라이저 컨텍스트에 미리 계산된 통계 추가
        serializer_context = {'request': request, 'question_stats_dict': question_stats_dict}
        
        # 시리얼라이저를 한 번에 사용하여 N+1 쿼리 방지
        serializer_start = time.time()
        questions_serializer = QuestionSerializer(questions, many=True, context=serializer_context)
        questions_data = questions_serializer.data
        serializer_time = time.time() - serializer_start
        
        # 각 문제에 favorite과 ignored 상태 추가 (O(1) 조회)
        for question_data in questions_data:
            question_id_str = str(question_data['id'])
            question_data['is_favorite'] = question_id_str in favorite_question_ids_str
            question_data['is_ignored'] = question_id_str in ignored_question_ids_str
        
        # 디버깅: ignored 상태 설정 확인
        ignored_count = sum(1 for q in questions_data if q['is_ignored'])
        logger.debug(f"[FAVORITE_API] Set is_ignored=True for {ignored_count} questions out of {len(questions_data)}")
        
        exam_serializer = ExamSerializer(favorite_exam, context={'request': request})
        query_time = time.time() - query_start

        response_data = {
            'questions': questions_data,
            'exam': exam_serializer.data
        }
        
        # 캐시에 저장 (300초 TTL, Celery로 비동기 처리)
        cache_save_start = time.time()
        try:
            from quiz.tasks import save_favorite_exam_questions_cache
            save_favorite_exam_questions_cache.delay(user.id, response_data, timeout=300)
            logger.debug(f"[FAVORITE_API] 캐시 저장 Celery 태스크 전송 완료: user_id={user.id}")
        except Exception as e:
            # Celery 태스크 전송 실패 시 동기 저장으로 폴백
            logger.warning(f"[FAVORITE_API] Celery 태스크 전송 실패, 동기 저장으로 폴백: {str(e)}")
            try:
                cache.set(cache_key, response_data, 300)
                logger.debug(f"[FAVORITE_API] 동기 캐시 저장 완료: user_id={user.id}")
            except Exception as cache_error:
                logger.error(f"[FAVORITE_API] 캐시 저장 실패: {cache_error}")
        cache_save_time = time.time() - cache_save_start
        
        total_time = time.time() - start_time
        logger.info(f"[FAVORITE_API] 캐시 미스: user_id={user.id}, DB 조회={db_time*1000:.2f}ms, 쿼리/시리얼라이저={query_time*1000:.2f}ms (시리얼라이저={serializer_time*1000:.2f}ms), 캐시 저장 태스크 전송={cache_save_time*1000:.2f}ms, 총 시간={total_time*1000:.2f}ms")

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': f'favorite 문제 조회 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE', 'POST'])
def remove_question_from_favorite(request):
    """favorite에서 문제를 제거합니다."""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)

        # 캐시 무효화
        try:
            from django.core.cache import cache
            cache.delete_pattern("favorites_*")
            print(f"[remove_question_from_favorite] 캐시 삭제 완료")
        except Exception as e:
            print(f"[remove_question_from_favorite] 캐시 삭제 실패: {e}")

        question_id = request.data.get('question_id')
        if not question_id:
            return Response({'error': '문제 ID가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        print(f"DEBUG: Removing question {question_id} from favorite for user {user.username}")

        # 문제 존재 확인
        try:
            question = Question.objects.get(id=question_id)
            print(f"DEBUG: Question found: {question.id}")
        except Question.DoesNotExist:
            print(f"DEBUG: Question {question_id} not found")
            return Response({'error': '문제를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        # 사용자의 favorite 시험 찾기 (가장 오래된 것을 우선)
        favorite_exams = Exam.objects.filter(
            title_ko=f"{user.username}'s favorite",
            is_original=True
        ).order_by('created_at')
        
        print(f"DEBUG: Found {favorite_exams.count()} favorite exams for user {user.username}")
        
        if not favorite_exams.exists():
            print(f"DEBUG: No favorite exam found for user {user.username}")
            return Response({'error': 'favorite 시험을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        # 첫 번째 favorite 시험 사용
        favorite_exam = favorite_exams.first()
        
        # 중복된 favorite 시험이 있으면 정리
        if favorite_exams.count() > 1:
            for duplicate_exam in favorite_exams[1:]:
                # 중복 시험의 문제들을 첫 번째 시험으로 이동
                duplicate_questions = ExamQuestion.objects.filter(exam=duplicate_exam)
                for eq in duplicate_questions:
                    # 이미 첫 번째 시험에 같은 문제가 있는지 확인
                    existing = ExamQuestion.objects.filter(
                        exam=favorite_exam,
                        question=eq.question
                    ).first()
                    if not existing:
                        eq.exam = favorite_exam
                        eq.save()
                
                # 중복 시험 삭제
                duplicate_exam.delete()
            
            # 첫 번째 시험의 총 문제 수 업데이트
            favorite_exam.total_questions = ExamQuestion.objects.filter(exam=favorite_exam).count()
            favorite_exam.save()

        # favorite에서 문제 제거
        exam_question = ExamQuestion.objects.filter(
            exam=favorite_exam,
            question=question
        ).first()

        print(f"DEBUG: Looking for question {question.id} in exam {favorite_exam.id}")
        print(f"DEBUG: Found exam_question: {exam_question}")
        
        # 현재 favorite 시험의 모든 문제 확인
        all_exam_questions = ExamQuestion.objects.filter(exam=favorite_exam)
        print(f"DEBUG: Total questions in favorite exam: {all_exam_questions.count()}")
        for eq in all_exam_questions[:5]:  # 처음 5개만 출력
            print(f"DEBUG: ExamQuestion {eq.id}: question_id={eq.question.id}")

        if not exam_question:
            print(f"DEBUG: Question {question.id} not found in favorite exam {favorite_exam.id}")
            # 문제가 없어도 성공으로 처리 (이미 삭제된 것으로 간주)
            return Response({
                'message': 'favorite에서 제거되었습니다. (이미 제거됨)',
                'removed_question_id': question_id,
                'already_removed': True
            }, status=status.HTTP_200_OK)

        exam_question.delete()

        # 시험의 총 문제 수 업데이트
        favorite_exam.total_questions = ExamQuestion.objects.filter(exam=favorite_exam).count()
        favorite_exam.save()

        return Response({
            'message': 'favorite에서 제거되었습니다.',
            'removed_question_id': question_id
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': f'favorite에서 제거 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_or_create_daily_exam(request):
    """사용자의 'Today's Quizzes for username' 시험이 있는지 확인하고, 있으면 해당 시험으로 이동하고, 없으면 새로 생성합니다."""
    try:
        # 로그인 확인
        if not request.user.is_authenticated:
            return Response({'error': 'home.dailyExam.loginRequired'}, status=status.HTTP_401_UNAUTHORIZED)
        
        user = request.user
        daily_exam_title = f"Today's Quizzes for {user.username}"
        
        # 기존 Daily Exam이 있는지 확인
        existing_exam = Exam.objects.filter(
            title_ko=daily_exam_title,
            created_by=user
        ).first()
        
        if existing_exam:
            # 기존 시험이 있으면 해당 시험 정보 반환
            from ..serializers import ExamSerializer
            exam_serializer = ExamSerializer(existing_exam)
            return Response({
                'success': True,
                'exam': exam_serializer.data,
                'is_new': False,
                'message': '기존 Daily Exam을 찾았습니다.'
            }, status=status.HTTP_200_OK)
        else:
            # 기존 시험이 없으면 새로 생성
            # create_random_recommendation_exam 함수의 로직을 직접 사용
            try:
                from ..models import UserProfile, Study, Member, StudyTask, IgnoredQuestion, ExamResultDetail
                from django.db import models
                
                # 사용자 프로필에서 문제 수 가져오기 (최신 데이터)
                try:
                    # 강제로 데이터베이스에서 최신 데이터 가져오기
                    from django.db import connection
                    cursor = connection.cursor()
                    cursor.execute("SELECT random_exam_question_count FROM quiz_userprofile WHERE user_id = %s", [user.id])
                    result = cursor.fetchone()
                    
                    if result:
                        questions_per_exam = result[0]
                        print(f"[Daily Exam] Raw SQL로 사용자 프로필에서 문제 수 가져옴: {questions_per_exam}")
                    else:
                        # Raw SQL로 가져올 수 없는 경우 ORM 사용
                        user_profile = UserProfile.objects.get(user=user)
                        questions_per_exam = user_profile.random_exam_question_count
                        print(f"[Daily Exam] ORM으로 사용자 프로필에서 문제 수 가져옴: {questions_per_exam}")
                        
                except Exception as e:
                    print(f"[Daily Exam] 사용자 프로필 조회 중 오류: {str(e)}")
                    questions_per_exam = 3  # 기본값
                    print(f"[Daily Exam] 기본값 사용: {questions_per_exam}")
                
                # user_profile 변수가 정의되지 않았을 수 있으므로 안전하게 처리
                user_profile = None
                try:
                    user_profile = UserProfile.objects.get(user=user)
                except UserProfile.DoesNotExist:
                    print(f"[Daily Exam] 사용자 프로필을 찾을 수 없음: {user.username}")
                except Exception as e:
                    print(f"[Daily Exam] 사용자 프로필 조회 중 오류: {str(e)}")
                
                # 제목 생성
                title = f"Today's Quizzes for {user.username}"
                
                # 사용자가 구독한 시험들에서 문제 추출 (Subscribed Exams)
                from ..models import ExamSubscription
                
                # 사용자가 구독한 시험들 조회
                subscribed_exams = Exam.objects.filter(
                    examsubscription__user=user,
                    examsubscription__is_active=True,
                    examquestion__isnull=False
                ).distinct()
                
                # 구독한 시험이 없으면 오류 반환 (스터디 기반 폴백 제거)
                if not subscribed_exams.exists():
                    return Response({
                        'error': 'home.dailyExam.noSubscribedExams'
                    }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    # 구독한 시험들을 사용
                    accessible_exams = subscribed_exams
                
                # 접근 가능한 시험이 없으면 오류 반환
                if not accessible_exams.exists():
                    if 'subscribed_exams' in locals() and subscribed_exams.exists():
                        return Response({
                            'error': 'home.dailyExam.noQuestionsInSubscribedExams'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return Response({
                            'error': 'home.dailyExam.noAccessibleExams'
                        }, status=status.HTTP_400_BAD_REQUEST)
                
                # 모든 시험에서 문제 수집
                all_exam_questions = []
                
                for exam in accessible_exams:
                    # 시험의 문제들 조회 (무시된 문제 제외)
                    exam_questions = Question.objects.filter(
                        examquestion__exam=exam
                    ).distinct()
                    
                    # 무시된 문제 제외
                    ignored_question_ids = set(
                        IgnoredQuestion.objects.filter(user=user)
                        .values_list('question_id', flat=True)
                    )
                    exam_questions = [q for q in exam_questions if q.id not in ignored_question_ids]
                    
                    if not exam_questions:
                        continue
                    
                    # 문제 통계 조회
                    for question in exam_questions:
                        total_attempts = ExamResultDetail.objects.filter(
                            question=question,
                            result__user=user
                        ).count()
                        
                        if total_attempts > 0:
                            wrong_count = ExamResultDetail.objects.filter(
                                question=question,
                                result__user=user,
                                is_correct=False
                            ).count()
                            wrong_rate = wrong_count / total_attempts
                            score = wrong_rate + (1.0 / total_attempts)
                        else:
                            score = 1.0
                        
                        all_exam_questions.append({
                            'question': question,
                            'exam': exam,
                            'score': score,
                            'attempts': total_attempts,
                            'wrong_count': wrong_count if total_attempts > 0 else 0
                        })
                
                # 시험별로 그룹화
                exam_questions_map = {}
                for item in all_exam_questions:
                    exam_title = item['exam'].title
                    if exam_title not in exam_questions_map:
                        exam_questions_map[exam_title] = []
                    exam_questions_map[exam_title].append(item)
                
                # 각 시험에서 questions_per_exam 개수만큼 문제 선택 (부족하면 있는 만큼만)
                all_questions = []
                
                # 시험별로 문제를 그룹화
                exam_questions_map = {}
                for item in all_exam_questions:
                    exam_title = item['exam'].title
                    if exam_title not in exam_questions_map:
                        exam_questions_map[exam_title] = []
                    exam_questions_map[exam_title].append(item)
                
                # 각 시험에서 상위 questions_per_exam 개수만큼 선택
                total_selected = 0
                for exam_title, exam_questions in exam_questions_map.items():
                    # 해당 시험의 문제들을 점수 순으로 정렬
                    sorted_exam_questions = sorted(exam_questions, key=lambda x: x['score'], reverse=True)
                    
                    # 상위 questions_per_exam 개수만큼 선택 (부족하면 있는 만큼만)
                    available_count = min(questions_per_exam, len(sorted_exam_questions))
                    selected_from_exam = sorted_exam_questions[:available_count]
                    
                    print(f"[DAILY_EXAM] 시험 '{exam_title}'에서 {len(selected_from_exam)}개 문제 선택 (요청: {questions_per_exam}개, 가용: {len(sorted_exam_questions)}개)")
                    
                    user_lang = get_user_language(request)
                    for item in selected_from_exam:
                        question = item['question']
                        exam = item['exam']
                        
                        # group_id에 소스 시험 이름 설정
                        # 단, 사용자가 이미 설정한 group_id가 있으면 보존 (빈 문자열이 아닌 경우)
                        if not question.group_id or question.group_id.strip() == '':
                            question.group_id = get_localized_field(exam, 'title', user_lang, 'Unknown')
                            question.save()
                        
                        question_title = get_localized_field(question, 'title', user_lang, '제목 없음')
                        exam_title = get_localized_field(exam, 'title', user_lang, 'Unknown')
                        all_questions.append({
                            'id': question.id,
                            'title': question_title,
                            'source_exam': exam_title,
                            'group_id': exam_title,
                            'score': item['score'],
                            'attempts': item['attempts'],
                            'wrong_count': item['wrong_count']
                        })
                    
                    total_selected += len(selected_from_exam)
                
                print(f"[DAILY_EXAM] 총 {total_selected}개 문제 선택 완료")
                
                # 중복 제거
                unique_questions = []
                seen_ids = set()
                
                for question_data in all_questions:
                    if question_data['id'] not in seen_ids:
                        unique_questions.append(question_data)
                        seen_ids.add(question_data['id'])
                
                if not unique_questions:
                    return Response({
                        'error': 'home.dailyExam.noQuestionsAvailable'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # 같은 이름의 시험이 있으면 재사용
                existing_exam = Exam.objects.filter(title_ko=title, created_by=user).first()
                if existing_exam:
                    print(f"[DAILY_EXAM] 기존 시험 '{existing_exam.title_ko or existing_exam.title_en or 'Unknown'}' 발견 - 재사용")
                    
                    # 기존 시험의 문제들을 반환
                    existing_questions = existing_exam.questions.all()
                    selected_questions = []
                    user_lang = get_user_language(request)
                    
                    for question in existing_questions:
                        # 문제 통계 정보 가져오기
                        from ..views.user_data_views import get_question_statistics_for_user
                        question_stats = get_question_statistics_for_user(question, user)
                        question_title = get_localized_field(question, 'title', user_lang, '제목 없음')
                        selected_questions.append({
                            'id': question.id,
                            'title': question_title,
                            'source_exam': question.group_id,
                            'group_id': question.group_id,
                            'score': question_stats['score'],
                            'attempts': question_stats['attempts'],
                            'wrong_count': question_stats['wrong_count']
                        })
                    
                    # 응답 데이터 구성
                    response_data = {
                        'success': True,
                        'exam': ExamSerializer(existing_exam, context={'request': request}).data,
                        'is_new': False,
                        'message': '기존 Daily Exam을 재사용합니다.',
                        'selected_questions': selected_questions
                    }
                    
                    response = Response(response_data, status=status.HTTP_200_OK)
                    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                    response['Pragma'] = 'no-cache'
                    response['Expires'] = '0'
                    
                    return response
                
                # 새 시험 생성
                print(f"[DAILY_EXAM] 시험 생성 시작: title={title}, questions={len(unique_questions)}, user={user.username}")
                exam = Exam.objects.create(
                    title_ko=title,
                    total_questions=len(unique_questions),
                    is_original=False,
                    is_public=False,
                    created_by=user
                )
                print(f"[DAILY_EXAM] 시험 생성 완료: id={exam.id}, created_by={exam.created_by}, created_at={exam.created_at}")
                
                # 시험에 문제 추가
                for i, question_data in enumerate(unique_questions):
                    question = Question.objects.get(id=question_data['id'])
                    ExamQuestion.objects.create(
                        exam=exam,
                        question=question,
                        order=i + 1
                    )
                
                # 시험 관련 캐시 무효화
                try:
                    from django.core.cache import cache
                    
                    # 1. ExamCacheManager 캐시 무효화
                    try:
                        from ..utils.cache_utils import ExamCacheManager
                        # 모든 시험 캐시 무효화
                        ExamCacheManager.invalidate_all_exam_cache()
                        # 사용자별 시험 캐시 무효화
                        ExamCacheManager.invalidate_user_exam_cache(user.id)
                        print("[DAILY_EXAM] ExamCacheManager 캐시 삭제 완료")
                    except Exception as e:
                        print(f"[DAILY_EXAM] ExamCacheManager 캐시 삭제 실패: {e}")
                    
                    # 2. Django 캐시 무효화
                    try:
                        cache.delete_pattern("exams_*")
                        print("[DAILY_EXAM] Django 패턴 기반 캐시 삭제 완료")
                    except AttributeError:
                        # 3. 개별 키 기반 캐시 삭제 (로컬 캐시 등)
                        cache_keys_to_delete = [
                            "exams_anonymous",
                            "exams_anonymous_true", 
                            "exams_anonymous_false",
                            "exams_anonymous_all",
                            "exams_1",
                            "exams_1_true",
                            "exams_1_false", 
                            "exams_1_all"
                        ]
                        
                        # 4. 사용자별 캐시 키 추가
                        if user:
                            user_id = user.id
                            cache_keys_to_delete.extend([
                                f"exams_{user_id}",
                                f"exams_{user_id}_true",
                                f"exams_{user_id}_false",
                                f"exams_{user_id}_all"
                            ])
                        
                        # 5. 모든 캐시 키 삭제
                        for key in cache_keys_to_delete:
                            cache.delete(key)
                        
                        print(f"[DAILY_EXAM] Django 개별 키 기반 캐시 삭제 완료 ({len(cache_keys_to_delete)}개 키)")
                        
                except Exception as e:
                    print(f"[DAILY_EXAM] 시험 캐시 무효화 중 오류: {e}")
                
                # 시험 정보 반환
                exam_serializer = ExamSerializer(exam)
                
                # 프론트엔드 캐시 무효화를 위한 응답 헤더 추가
                response = Response({
                    'success': True,
                    'exam': exam_serializer.data,
                    'is_new': True,
                    'message': '새로운 Daily Exam이 생성되었습니다.'
                }, status=status.HTTP_201_CREATED)
                
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                
                return response
                
            except Exception as e:
                logger.error(f'Daily Exam 생성 중 오류: {str(e)}')
                return Response({
                    'error': f'home.dailyExam.creationError: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
    except Exception as e:
        logger.error(f'Daily Exam 조회/생성 중 오류: {str(e)}')
        return Response({
            'error': f'home.dailyExam.processingError: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def adjust_question_accuracy(request):
    """문제의 정확도를 조정합니다. 최신 시도의 is_correct 값만 변경합니다."""
    try:
        if not request.user.is_authenticated:
            return Response({'error': '인증이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        question_id = request.data.get('question_id')
        exam_id = request.data.get('exam_id')
        adjustment_type = request.data.get('adjustment_type')  # 'clear' 또는 'ambiguous'
        
        if not question_id or not exam_id or not adjustment_type:
            return Response({'error': '필수 파라미터가 누락되었습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 문제와 시험 확인
        try:
            question = Question.objects.get(id=question_id)
            exam = Exam.objects.get(id=exam_id)
        except (Question.DoesNotExist, Exam.DoesNotExist):
            return Response({'error': '문제 또는 시험을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        # 해당 시험에서의 문제 통계 조회
        exam_results = ExamResult.objects.filter(exam=exam)
        total_attempts = 0
        correct_attempts = 0
        
        for result in exam_results:
            details = ExamResultDetail.objects.filter(result=result, question=question)
            for detail in details:
                total_attempts += 1
                if detail.is_correct:
                    correct_attempts += 1
        
        # 최신 ExamResultDetail 찾기 (가장 최근 시도)
        latest_detail = ExamResultDetail.objects.filter(
            question=question,
            result__exam=exam
        ).order_by('-id').first()
        
        if not latest_detail:
            return Response({'error': '해당 문제의 시험 결과를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        # 조정 적용
        if adjustment_type == 'clear':
            # 명확: 틀린 문제 중 가장 최근 것을 맞은 것으로 변경
            wrong_attempts = total_attempts - correct_attempts
            
            if wrong_attempts > 0:
                # 틀린 문제 중 가장 최근 것을 찾아서 맞은 것으로 변경
                latest_wrong_detail = ExamResultDetail.objects.filter(
                    question=question,
                    result__exam=exam,
                    is_correct=False
                ).order_by('-id').first()
                
                if latest_wrong_detail:
                    latest_wrong_detail.is_correct = True
                    latest_wrong_detail.save()
                    
        elif adjustment_type == 'ambiguous':
            # 모호: 맞은 문제 중 가장 최근 것을 틀린 것으로 변경
            if correct_attempts > 0:
                # 맞은 문제 중 가장 최근 것을 찾아서 틀린 것으로 변경
                latest_correct_detail = ExamResultDetail.objects.filter(
                    question=question,
                    result__exam=exam,
                    is_correct=True
                ).order_by('-id').first()
                
                if latest_correct_detail:
                    latest_correct_detail.is_correct = False
                    latest_correct_detail.save()
        else:
            return Response({'error': '잘못된 조정 타입입니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 변경 후 다시 통계 계산
        updated_total_attempts = 0
        updated_correct_attempts = 0
        
        for result in exam_results:
            details = ExamResultDetail.objects.filter(result=result, question=question)
            for detail in details:
                updated_total_attempts += 1
                if detail.is_correct:
                    updated_correct_attempts += 1
        
        updated_accuracy = (updated_correct_attempts / updated_total_attempts * 100) if updated_total_attempts > 0 else 0
        
        # 캐시 무효화 (Redis가 아닌 경우를 대비해 안전하게 처리)
        try:
            # 시험 관련 캐시 키들 무효화
            cache_keys_to_delete = [
                f'exam_{exam_id}_questions',
                f'exam_{exam_id}_statistics',
                f'exam_{exam_id}_question_statistics',
                f'question_statistics_{question_id}',
                f'exam_{exam_id}_question_member_mappings',
                # 더 포괄적인 캐시 무효화
                f'exam_{exam_id}_*',
                f'question_{question_id}_*',
                f'statistics_*',
                f'question_statistics_*',
            ]
            
            for key in cache_keys_to_delete:
                cache.delete(key)
            
            # 패턴 매칭으로 캐시 키 삭제 (Redis의 경우)
            try:
                import re
                all_keys = cache.keys('*')
                pattern_keys = [
                    f'exam_{exam_id}_*',
                    f'question_{question_id}_*',
                    f'*statistics*',
                ]
                
                for pattern in pattern_keys:
                    regex = re.compile(pattern.replace('*', '.*'))
                    for key in all_keys:
                        if regex.match(key):
                            cache.delete(key)
            except Exception as pattern_error:
                logger.warning(f'패턴 캐시 삭제 중 오류 (무시됨): {str(pattern_error)}')
            
            logger.info(f'정확도 조정 후 캐시 무효화 완료: {exam_id}')
        except Exception as cache_error:
            logger.warning(f'캐시 무효화 중 오류 (무시됨): {str(cache_error)}')
        
        return Response({
            'success': True,
            'message': 'accuracy_adjustment.success',
            'updated_stats': {
                'total_attempts': updated_total_attempts,
                'correct_attempts': updated_correct_attempts,
                'accuracy': round(updated_accuracy, 1)
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'정확도 조정 중 오류: {str(e)}')
        return Response({'error': f'정확도 조정 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def bulk_adjust_user_accuracy(request):
    """특정 사용자의 문제 목록에서 정확도를 일괄적으로 조정하는 API"""
    try:
        # 요청 데이터에서 인증 정보 가져오기
        username = request.data.get('username')
        password = request.data.get('password')
        target_username = request.data.get('target_username')
        
        # username/password 인증 방식 사용 (curl 호출 시)
        if username and password:
            from django.contrib.auth import authenticate
            
            # 사용자 존재 확인
            user = User.objects.filter(username=username).first()
            if not user:
                return Response({
                    'error': '존재하지 않는 사용자입니다.'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # 비밀번호 확인
            authenticated_user = authenticate(username=username, password=password)
            if not authenticated_user:
                return Response({
                    'error': '비밀번호가 일치하지 않습니다.'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # admin 권한 확인
            if not user.is_staff:
                return Response({
                    'error': 'admin 권한이 필요합니다.'
                }, status=status.HTTP_403_FORBIDDEN)
        else:
            # 기존 토큰 기반 인증 방식 (화면에서 호출 시)
            if not request.user.is_authenticated:
                return Response({'error': '인증이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)
            
            # 토큰 기반 인증의 경우 현재 사용자를 target_username으로 사용
            if not target_username:
                target_username = request.user.username
        
        # 요청 데이터 파싱
        exam_id = request.data.get('exam_id')  # 선택적 파라미터
        question_ids = request.data.get('question_ids', [])  # 선택된 문제 ID 목록
        adjustment_percentage = request.data.get('adjustment_percentage', 10.0)  # 사용자가 슬라이더에서 선택한 값
        adjustment_type = request.data.get('adjustment_type', 'decrease')  # 'increase' 또는 'decrease'
        
        if not target_username:
            return Response({'error': 'target_username 파라미터가 누락되었습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 조정 타입 유효성 검사
        if adjustment_type not in ['increase', 'decrease']:
            return Response({'error': '조정 타입은 "increase" 또는 "decrease"여야 합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 조정 퍼센트 유효성 검사
        try:
            adjustment_percentage = float(adjustment_percentage)
            if adjustment_percentage < 0 or adjustment_percentage > 100:
                return Response({'error': '조정 퍼센트는 0-100 사이의 값이어야 합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({'error': '조정 퍼센트는 숫자여야 합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 대상 사용자 확인
        try:
            target_user = User.objects.get(username=target_username)
        except User.DoesNotExist:
            return Response({'error': '대상 사용자를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        # exam_id가 있으면 특정 시험의 문제들, 없으면 사용자가 시도한 모든 문제들 조회
        if exam_id:
            try:
                exam = Exam.objects.get(id=exam_id)
                if question_ids and len(question_ids) > 0:
                    # 선택된 문제들만 조회
                    questions = exam.questions.filter(id__in=question_ids)
                else:
                    # 모든 문제 조회 (기존 동작)
                    questions = exam.questions.all()
            except Exam.DoesNotExist:
                return Response({'error': '시험을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            # 사용자가 시도한 모든 문제들 조회
            if question_ids and len(question_ids) > 0:
                # 선택된 문제들만 조회
                questions = Question.objects.filter(
                    id__in=question_ids,
                    examresultdetail__result__user=target_user
                ).distinct()
            else:
                # 모든 문제 조회 (기존 동작)
                questions = Question.objects.filter(
                    examresultdetail__result__user=target_user
                ).distinct()
        adjusted_questions = []
        user_lang = get_user_language(request)
        
        for question in questions:
            # 해당 사용자의 문제 통계 조회
            if exam_id:
                # 특정 시험의 문제 통계
                exam_results = ExamResult.objects.filter(exam=exam, user=target_user)
            else:
                # 모든 시험의 문제 통계
                exam_results = ExamResult.objects.filter(user=target_user)
            
            total_attempts = 0
            correct_attempts = 0
            
            for result in exam_results:
                details = ExamResultDetail.objects.filter(result=result, question=question)
                for detail in details:
                    total_attempts += 1
                    if detail.is_correct:
                        correct_attempts += 1
            
            # 시도한 문제만 처리
            if total_attempts > 0:
                current_accuracy = (correct_attempts / total_attempts) * 100
                
                # 조정할 정답 개수 계산 (조정 퍼센트 기반)
                adjustment_count = max(1, int((adjustment_percentage / 100) * total_attempts))
                
                # 조정 타입에 따른 로직
                if adjustment_type == 'decrease':
                    # 정확도를 낮추는 경우: 맞은 문제 중 최신 것들을 틀린 것으로 변경
                    if correct_attempts > 0:
                        # 맞은 문제 중 가장 최근 것들을 찾아서 틀린 것으로 변경
                        if exam_id:
                            latest_correct_details = ExamResultDetail.objects.filter(
                                question=question,
                                result__exam=exam,
                                result__user=target_user,
                                is_correct=True
                            ).order_by('-id')[:adjustment_count]
                        else:
                            latest_correct_details = ExamResultDetail.objects.filter(
                                question=question,
                                result__user=target_user,
                                is_correct=True
                            ).order_by('-id')[:adjustment_count]
                        
                        if latest_correct_details.count() > 0:
                            actual_flipped_count = latest_correct_details.count()
                            for detail in latest_correct_details:
                                detail.is_correct = False
                                detail.save()
                            
                            # 새로운 정확도 계산
                            new_correct_attempts = correct_attempts - actual_flipped_count
                            new_total_attempts = total_attempts
                            new_accuracy = (new_correct_attempts / new_total_attempts) * 100
                            
                            question_title = get_localized_field(question, 'title', user_lang, '제목 없음')
                            adjusted_questions.append({
                                'question_id': question.id,
                                'question_title': question_title,
                                'previous_accuracy': current_accuracy,
                                'new_accuracy': new_accuracy,
                                'adjustment_applied': True,
                                'adjustment_type': 'decrease',
                                'flipped_count': actual_flipped_count
                            })
                        else:
                            question_title = get_localized_field(question, 'title', user_lang, '제목 없음')
                            adjusted_questions.append({
                                'question_id': question.id,
                                'question_title': question_title,
                                'previous_accuracy': current_accuracy,
                                'new_accuracy': current_accuracy,
                                'adjustment_applied': False,
                                'reason': '조정할 수 있는 정답 기록이 없습니다.',
                                'adjustment_type': 'decrease'
                            })
                    else:
                        question_title = get_localized_field(question, 'title', user_lang, '제목 없음')
                        adjusted_questions.append({
                            'question_id': question.id,
                            'question_title': question_title,
                            'previous_accuracy': current_accuracy,
                            'new_accuracy': current_accuracy,
                            'adjustment_applied': False,
                            'reason': '정답 기록이 없습니다.',
                            'adjustment_type': 'decrease'
                        })
                else:  # adjustment_type == 'increase'
                    # 정확도를 높이는 경우: 틀린 문제 중 최신 것들을 맞은 것으로 변경
                    wrong_attempts = total_attempts - correct_attempts
                    
                    if wrong_attempts > 0:
                        # 틀린 문제 중 가장 최근 것들을 찾아서 맞은 것으로 변경
                        if exam_id:
                            latest_wrong_details = ExamResultDetail.objects.filter(
                                question=question,
                                result__exam=exam,
                                result__user=target_user,
                                is_correct=False
                            ).order_by('-id')[:adjustment_count]
                        else:
                            latest_wrong_details = ExamResultDetail.objects.filter(
                                question=question,
                                result__user=target_user,
                                is_correct=False
                            ).order_by('-id')[:adjustment_count]
                        
                        if latest_wrong_details.count() > 0:
                            actual_flipped_count = latest_wrong_details.count()
                            for detail in latest_wrong_details:
                                detail.is_correct = True
                                detail.save()
                            
                            # 새로운 정확도 계산
                            new_correct_attempts = correct_attempts + actual_flipped_count
                            new_total_attempts = total_attempts
                            new_accuracy = (new_correct_attempts / new_total_attempts) * 100
                            
                            question_title = get_localized_field(question, 'title', user_lang, '제목 없음')
                            adjusted_questions.append({
                                'question_id': question.id,
                                'question_title': question_title,
                                'previous_accuracy': current_accuracy,
                                'new_accuracy': new_accuracy,
                                'adjustment_applied': True,
                                'adjustment_type': 'increase',
                                'flipped_count': actual_flipped_count
                            })
                        else:
                            question_title = get_localized_field(question, 'title', user_lang, '제목 없음')
                            adjusted_questions.append({
                                'question_id': question.id,
                                'question_title': question_title,
                                'previous_accuracy': current_accuracy,
                                'new_accuracy': current_accuracy,
                                'adjustment_applied': False,
                                'reason': '조정할 수 있는 오답 기록이 없습니다.',
                                'adjustment_type': 'increase'
                            })
                    else:
                        question_title = get_localized_field(question, 'title', user_lang, '제목 없음')
                        adjusted_questions.append({
                            'question_id': question.id,
                            'question_title': question_title,
                            'previous_accuracy': current_accuracy,
                            'new_accuracy': current_accuracy,
                            'adjustment_applied': False,
                            'reason': '오답 기록이 없습니다.',
                            'adjustment_type': 'increase'
                        })
            else:
                user_lang = get_user_language(request)
                question_title = get_localized_field(question, 'title', user_lang, '제목 없음')
                adjusted_questions.append({
                    'question_id': question.id,
                    'question_title': question_title,
                    'previous_accuracy': 0,
                    'new_accuracy': 0,
                    'adjustment_applied': False,
                    'reason': '시도한 기록이 없습니다.'
                })
        
        adjustment_type_text = "낮추기" if adjustment_type == 'decrease' else "높이기"
        return Response({
            'success': True,
            'message': f'정확도 {adjustment_type_text}가 완료되었습니다. (조정 퍼센트: {adjustment_percentage}%)',
            'adjusted_questions': adjusted_questions,
            'total_questions': len(questions),
            'adjusted_count': len([q for q in adjusted_questions if q['adjustment_applied']]),
            'adjustment_type': adjustment_type
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'일괄 정확도 조정 중 오류: {str(e)}')
        return Response({'error': f'일괄 정확도 조정 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def adjust_single_question_accuracy(request):
    """특정 사용자의 특정 문제에 대한 정확도를 조정하는 API"""
    try:
        if not request.user.is_authenticated:
            return Response({'error': '인증이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # 요청 데이터 파싱
        target_user_id = request.data.get('target_user_id')
        exam_id = request.data.get('exam_id')
        question_id = request.data.get('question_id')
        adjustment_percentage = request.data.get('adjustment_percentage', 10.0)  # 기본값 10%
        adjustment_type = request.data.get('adjustment_type', 'decrease')  # 'increase' 또는 'decrease'
        
        if not target_user_id or not exam_id or not question_id:
            return Response({'error': '필수 파라미터가 누락되었습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 조정 타입 유효성 검사
        if adjustment_type not in ['increase', 'decrease']:
            return Response({'error': '조정 타입은 "increase" 또는 "decrease"여야 합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 조정 퍼센트 유효성 검사
        try:
            adjustment_percentage = float(adjustment_percentage)
            if adjustment_percentage < 0 or adjustment_percentage > 100:
                return Response({'error': '조정 퍼센트는 0-100 사이의 값이어야 합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({'error': '조정 퍼센트는 숫자여야 합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 시험 확인
        try:
            exam = Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            return Response({'error': '시험을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        # 문제 확인
        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return Response({'error': '문제를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        # 대상 사용자 확인
        try:
            target_user = User.objects.get(id=target_user_id)
        except User.DoesNotExist:
            return Response({'error': '대상 사용자를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        # 해당 사용자의 문제 통계 조회
        exam_results = ExamResult.objects.filter(exam=exam, user=target_user)
        total_attempts = 0
        correct_attempts = 0
        
        for result in exam_results:
            details = ExamResultDetail.objects.filter(result=result, question=question)
            for detail in details:
                total_attempts += 1
                if detail.is_correct:
                    correct_attempts += 1
        
        # 시도한 문제만 처리
        if total_attempts > 0:
            current_accuracy = (correct_attempts / total_attempts) * 100
            
            # 정확도 조정 이력 조회 또는 생성
            history, created = AccuracyAdjustmentHistory.objects.get_or_create(
                user=target_user,
                question=question,
                exam=exam,
                defaults={
                    'adjustment_count': 1,
                    'total_adjustment_percentage': adjustment_percentage
                }
            )
            
            if not created:
                # 기존 이력이 있으면 누적
                history.adjustment_count += 1
                history.total_adjustment_percentage += adjustment_percentage
                history.save()
            
            # 조정 타입에 따른 로직
            if adjustment_type == 'decrease':
                # 정확도를 낮추는 경우
                # 누적 조정 퍼센트가 현재 정확도를 초과하면 정확도를 0으로 만들기
                if history.total_adjustment_percentage >= current_accuracy:
                    # 맞은 문제 중 가장 최근 것을 틀린 것으로 변경
                    latest_correct_detail = ExamResultDetail.objects.filter(
                        question=question,
                        result__exam=exam,
                        result__user=target_user,
                        is_correct=True
                    ).order_by('-id').first()
                    
                    if latest_correct_detail:
                        latest_correct_detail.is_correct = False
                        latest_correct_detail.save()
                        
                        question_title = get_localized_field(question, 'title', user_lang, '제목 없음')
                        return Response({
                            'success': True,
                            'message': 'accuracy_adjustment.to_zero',
                            'message_params': {'adjustment_percentage': adjustment_percentage},
                            'question_id': question.id,
                            'question_title': question_title,
                            'previous_accuracy': current_accuracy,
                            'new_accuracy': 0,
                            'adjustment_applied': True,
                            'adjustment_type': 'decrease'
                        }, status=status.HTTP_200_OK)
                    else:
                        question_title = get_localized_field(question, 'title', user_lang, '제목 없음')
                        return Response({
                            'success': False,
                            'message': '조정할 수 있는 정답 기록이 없습니다.',
                            'question_id': question.id,
                            'question_title': question_title,
                            'previous_accuracy': current_accuracy,
                            'new_accuracy': current_accuracy,
                            'adjustment_applied': False,
                            'adjustment_type': 'decrease'
                        }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    question_title = get_localized_field(question, 'title', user_lang, '제목 없음')
                    return Response({
                        'success': False,
                        'message': f'누적 조정 퍼센트({history.total_adjustment_percentage}%)가 현재 정확도({current_accuracy}%)보다 낮습니다.',
                        'question_id': question.id,
                        'question_title': question_title,
                        'previous_accuracy': current_accuracy,
                        'new_accuracy': current_accuracy,
                        'adjustment_applied': False,
                        'adjustment_type': 'decrease'
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:  # adjustment_type == 'increase'
                # 정확도를 높이는 경우
                # 누적 조정 퍼센트가 (100 - 현재 정확도)를 초과하면 정확도를 100%로 만들기
                max_increase_needed = 100 - current_accuracy
                if history.total_adjustment_percentage >= max_increase_needed:
                    # 틀린 문제 중 가장 최근 것을 맞은 것으로 변경
                    latest_wrong_detail = ExamResultDetail.objects.filter(
                        question=question,
                        result__exam=exam,
                        result__user=target_user,
                        is_correct=False
                    ).order_by('-id').first()
                    
                    if latest_wrong_detail:
                        latest_wrong_detail.is_correct = True
                        latest_wrong_detail.save()
                        
                        question_title = get_localized_field(question, 'title', user_lang, '제목 없음')
                        return Response({
                            'success': True,
                            'message': 'accuracy_adjustment.to_hundred',
                            'message_params': {'adjustment_percentage': adjustment_percentage},
                            'question_id': question.id,
                            'question_title': question_title,
                            'previous_accuracy': current_accuracy,
                            'new_accuracy': 100,
                            'adjustment_applied': True,
                            'adjustment_type': 'increase'
                        }, status=status.HTTP_200_OK)
                    else:
                        question_title = get_localized_field(question, 'title', user_lang, '제목 없음')
                        return Response({
                            'success': False,
                            'message': '조정할 수 있는 오답 기록이 없습니다.',
                            'question_id': question.id,
                            'question_title': question_title,
                            'previous_accuracy': current_accuracy,
                            'new_accuracy': current_accuracy,
                            'adjustment_applied': False,
                            'adjustment_type': 'increase'
                        }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    question_title = get_localized_field(question, 'title', user_lang, '제목 없음')
                    return Response({
                        'success': False,
                        'message': f'누적 조정 퍼센트({history.total_adjustment_percentage}%)가 필요한 증가량({max_increase_needed}%)보다 낮습니다.',
                        'question_id': question.id,
                        'question_title': question_title,
                        'previous_accuracy': current_accuracy,
                        'new_accuracy': current_accuracy,
                        'adjustment_applied': False,
                        'adjustment_type': 'increase'
                    }, status=status.HTTP_400_BAD_REQUEST)
        else:
            user_lang = get_user_language(request)
            question_title = get_localized_field(question, 'title', user_lang, '제목 없음')
            return Response({
                'success': False,
                'message': '시도한 기록이 없습니다.',
                'question_id': question.id,
                'question_title': question_title,
                'previous_accuracy': 0,
                'new_accuracy': 0,
                'adjustment_applied': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f'단일 문제 정확도 조정 중 오류: {str(e)}')
        return Response({'error': f'단일 문제 정확도 조정 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def toggle_exam_subscription(request):
    """시험 구독/구독해제 토글"""
    try:
        exam_id = request.data.get('exam_id')
        if not exam_id:
            return Response({'error': '시험 ID가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            exam = Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            return Response({'error': '시험을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        user = request.user
        if not user.is_authenticated:
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        logger.info(f"[TOGGLE_SUBSCRIPTION] 시험 {exam.title_ko or exam.title_en or 'Unknown'} (ID: {exam.id}) 구독 상태 변경 시작")
        
        # 기존 구독 확인
        subscription, created = ExamSubscription.objects.get_or_create(
            user=user,
            exam=exam,
            defaults={'is_active': True}
        )
        
        logger.info(f"[TOGGLE_SUBSCRIPTION] 구독 객체 상태: created={created}, is_active={subscription.is_active}, exam_id={subscription.exam_id}")
        
        if created:
            # 새로 구독
            is_subscribed = True
            message = '시험이 구독되었습니다.'
            logger.info(f"[TOGGLE_SUBSCRIPTION] 새 구독 생성: 사용자 {user.username}, 시험 {exam.title_ko or exam.title_en or 'Unknown'}")
        else:
            # 기존 구독 상태 토글
            old_status = subscription.is_active
            subscription.is_active = not subscription.is_active
            subscription.save()
            is_subscribed = subscription.is_active
            message = '시험이 구독되었습니다.' if is_subscribed else '시험 구독이 해제되었습니다.'
            logger.info(f"[TOGGLE_SUBSCRIPTION] 구독 상태 토글: {old_status} → {is_subscribed}, 사용자 {user.username}, 시험 {exam.title_ko or exam.title_en or 'Unknown'}")
        
        # 캐시 무효화
        try:
            from ..utils.cache_utils import ExamCacheManager
            ExamCacheManager.invalidate_user_exam_cache(user.id)
            logger.info(f"[TOGGLE_SUBSCRIPTION] 사용자 {user.id}의 시험 캐시 무효화 완료")
        except Exception as e:
            logger.error(f"[TOGGLE_SUBSCRIPTION] 캐시 무효화 실패: {e}")
        
        return Response({
            'success': True,
            'is_subscribed': is_subscribed,
            'message': message,
            'exam_id': str(exam.id),
            'exam_title': exam.title_ko or exam.title_en or 'Unknown'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'시험 구독 토글 중 오류: {str(e)}')
        return Response({'error': f'시험 구독 토글 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def bulk_toggle_exam_subscriptions(request):
    """여러 시험 일괄 구독/구독해제"""
    try:
        exam_ids = request.data.get('exam_ids', [])
        action = request.data.get('action')  # 'subscribe' 또는 'unsubscribe'
        
        if not exam_ids:
            return Response({'error': '시험 ID 목록이 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if action not in ['subscribe', 'unsubscribe']:
            return Response({'error': '유효하지 않은 액션입니다. (subscribe 또는 unsubscribe)'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        if not user.is_authenticated:
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # 시험 존재 여부 확인
        exams = Exam.objects.filter(id__in=exam_ids)
        if len(exams) != len(exam_ids):
            return Response({'error': '일부 시험을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        logger.info(f"[BULK_SUBSCRIPTION] 사용자 {user.username}의 일괄 구독 처리 시작. 액션: {action}, 시험 수: {len(exam_ids)}")
        
        # 일괄 처리
        if action == 'subscribe':
            # 구독 생성 또는 활성화
            for exam in exams:
                subscription, created = ExamSubscription.objects.get_or_create(
                    user=user,
                    exam=exam,
                    defaults={'is_active': True}
                )
                if created:
                    logger.info(f"[BULK_SUBSCRIPTION] 새 구독 생성: 시험 {exam.title_ko or exam.title_en or 'Unknown'}")
                else:
                    logger.info(f"[BULK_SUBSCRIPTION] 기존 구독 발견: 시험 {exam.title_ko or exam.title_en or 'Unknown'}")
            
            # 기존 구독이 비활성화된 경우 활성화
            updated_count = ExamSubscription.objects.filter(
                user=user,
                exam__in=exams,
                is_active=False
            ).update(is_active=True)
            
            logger.info(f"[BULK_SUBSCRIPTION] 비활성 구독 {updated_count}개 활성화됨")
            message = f'{len(exam_ids)}개 시험이 구독되었습니다.'
        else:
            # 구독 해제 (비활성화)
            updated_count = ExamSubscription.objects.filter(
                user=user,
                exam__in=exams
            ).update(is_active=False)
            
            logger.info(f"[BULK_SUBSCRIPTION] {updated_count}개 구독 비활성화됨")
            message = f'{len(exam_ids)}개 시험 구독이 해제되었습니다.'
        
        # 캐시 무효화
        try:
            from ..utils.cache_utils import ExamCacheManager
            ExamCacheManager.invalidate_user_exam_cache(user.id)
            logger.info(f"[BULK_SUBSCRIPTION] 사용자 {user.id}의 시험 캐시 무효화 완료")
        except Exception as e:
            logger.error(f"[BULK_SUBSCRIPTION] 캐시 무효화 실패: {e}")
        
        return Response({
            'success': True,
            'message': message,
            'action': action,
            'processed_count': len(exam_ids)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'일괄 시험 구독 처리 중 오류: {str(e)}')
        return Response({'error': f'일괄 시험 구독 처리 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_user_exam_subscriptions(request):
    """사용자의 시험 구독 목록 조회"""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # 활성 구독만 조회
        subscriptions = ExamSubscription.objects.filter(
            user=user,
            is_active=True
        ).select_related('exam').order_by('-subscribed_at')
        
        subscription_data = []
        for subscription in subscriptions:
            subscription_data.append({
                'id': str(subscription.id),
                'exam_id': str(subscription.exam.id),
                'exam_title': subscription.exam.title_ko or subscription.exam.title_en or 'Unknown',
                'subscribed_at': subscription.subscribed_at.isoformat(),
                'is_active': subscription.is_active
            })
        
        return Response({
            'success': True,
            'subscriptions': subscription_data,
            'total_count': len(subscription_data)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'사용자 시험 구독 목록 조회 중 오류: {str(e)}')
        return Response({'error': f'사용자 시험 구독 목록 조회 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_user_my_exams(request):
    """사용자가 생성한 시험 목록 조회"""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # 사용자 프로필 언어 가져오기
        user_language = get_user_language(request)
        logger.debug(f"[GET_USER_MY_EXAMS] user_language: {user_language}, user: {user.username if user.is_authenticated else 'anonymous'}")
        
        # 사용자가 생성한 시험 목록 조회 (Daily Exam 제외)
        my_exams = Exam.objects.filter(
            created_by=user
        ).exclude(
            Q(title_ko__startswith="Today's Quizzes for") |
            Q(title_en__startswith="Today's Quizzes for")
        ).order_by('-created_at')
        
        exam_data = []
        for exam in my_exams:
            # 사용자 언어에 맞는 제목 선택
            if user_language == 'ko':
                title = exam.title_ko or exam.title_en or 'Unknown'
            elif user_language == 'en':
                title = exam.title_en or exam.title_ko or 'Unknown'
            elif user_language == 'es':
                title = getattr(exam, 'title_es', None) or exam.title_en or exam.title_ko or 'Unknown'
            elif user_language == 'zh':
                title = getattr(exam, 'title_zh', None) or exam.title_en or exam.title_ko or 'Unknown'
            elif user_language == 'ja':
                title = getattr(exam, 'title_ja', None) or exam.title_en or exam.title_ko or 'Unknown'
            else:
                # 기본값: 영어 우선
                title = exam.title_en or exam.title_ko or 'Unknown'
            
            logger.debug(f"[GET_USER_MY_EXAMS] exam_id: {exam.id}, user_language: {user_language}, title: {title}, title_ko: {exam.title_ko}, title_en: {exam.title_en}")
            
            exam_data.append({
                'id': str(exam.id),
                'title': title,
                'created_at': exam.created_at.isoformat(),
                'is_public': exam.is_public,
                'is_original': exam.is_original
            })
        
        return Response({
            'success': True,
            'exams': exam_data,
            'total_count': len(exam_data)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'사용자 My Exams 조회 중 오류: {str(e)}')
        return Response({'error': f'사용자 My Exams 조회 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_exam_tags(request):
    """사용 가능한 태그 목록 조회"""
    try:
        tags = Tag.objects.all().order_by('name_ko')
        serializer = TagSerializer(tags, many=True, context={'request': request})
        return Response(serializer.data)
    except Exception as e:
        logger.error(f"태그 목록 조회 중 오류 발생: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_user_subscribed_exams(request):
    """사용자가 구독한 시험 목록 조회"""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # 사용자 프로필 언어 가져오기
        user_language = get_user_language(request)
        logger.debug(f"[GET_USER_SUBSCRIBED_EXAMS] user_language: {user_language}, user: {user.username if user.is_authenticated else 'anonymous'}")
        
        # 사용자가 구독한 시험 목록 조회
        subscriptions = ExamSubscription.objects.filter(
            user=user,
            is_active=True
        ).select_related('exam').order_by('-subscribed_at')
        
        exam_data = []
        for subscription in subscriptions:
            # 사용자 언어에 맞는 제목 선택
            if user_language == 'ko':
                title = subscription.exam.title_ko or subscription.exam.title_en or 'Unknown'
            elif user_language == 'en':
                title = subscription.exam.title_en or subscription.exam.title_ko or 'Unknown'
            elif user_language == 'es':
                title = getattr(subscription.exam, 'title_es', None) or subscription.exam.title_en or subscription.exam.title_ko or 'Unknown'
            elif user_language == 'zh':
                title = getattr(subscription.exam, 'title_zh', None) or subscription.exam.title_en or subscription.exam.title_ko or 'Unknown'
            elif user_language == 'ja':
                title = getattr(subscription.exam, 'title_ja', None) or subscription.exam.title_en or subscription.exam.title_ko or 'Unknown'
            else:
                # 기본값: 영어 우선
                title = subscription.exam.title_en or subscription.exam.title_ko or 'Unknown'
            
            logger.debug(f"[GET_USER_SUBSCRIBED_EXAMS] exam_id: {subscription.exam.id}, user_language: {user_language}, title: {title}, title_ko: {subscription.exam.title_ko}, title_en: {subscription.exam.title_en}")
            
            exam_data.append({
                'id': str(subscription.exam.id),
                'title': title,
                'subscribed_at': subscription.subscribed_at.isoformat(),
                'is_public': subscription.exam.is_original,
                'is_original': subscription.exam.is_original
            })
        
        return Response({
            'success': True,
            'exams': exam_data,
            'total_count': len(exam_data)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'사용자 Subscribed Exams 조회 중 오류: {str(e)}')
        return Response({'error': f'사용자 Subscribed Exams 조회 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def move_exams_to_subscribed(request):
    """My Exams에서 Subscribed Exams로 시험 이동"""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        exam_ids = request.data.get('exam_ids', [])
        if not exam_ids:
            return Response({'error': '시험 ID 목록이 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 시험 존재 여부 및 소유권 확인 (Daily Exam 제외)
        exams = Exam.objects.filter(
            id__in=exam_ids,
            created_by=user
        ).exclude(
            Q(title_ko__startswith="Today's Quizzes for") |
            Q(title_en__startswith="Today's Quizzes for")
        )
        
        if len(exams) != len(exam_ids):
            return Response({'error': '일부 시험을 찾을 수 없거나 접근 권한이 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        # 구독 생성 또는 활성화
        for exam in exams:
            subscription, created = ExamSubscription.objects.get_or_create(
                user=user,
                exam=exam,
                defaults={'is_active': True}
            )
            if not created and not subscription.is_active:
                subscription.is_active = True
                subscription.save()
        
        # 업데이트된 My Exams 목록 반환
        updated_my_exams = Exam.objects.filter(
            created_by=user
        ).order_by('-created_at')
        
        exam_data = []
        for exam in updated_my_exams:
            exam_data.append({
                'id': str(exam.id),
                'title': exam.title_ko or exam.title_en or 'Unknown',
                'created_at': exam.created_at.isoformat(),
                'is_public': exam.is_public,
                'is_original': exam.is_original
            })
        
        return Response({
            'success': True,
            'message': f'{len(exam_ids)}개 시험이 Subscribed Exams로 이동되었습니다.',
            'exams': exam_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'시험을 Subscribed Exams로 이동 중 오류: {str(e)}')
        return Response({'error': f'시험을 Subscribed Exams로 이동 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def move_exams_to_my_exams(request):
    """Subscribed Exams에서 My Exams로 시험 이동 (구독 해제)"""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        exam_ids = request.data.get('exam_ids', [])
        if not exam_ids:
            return Response({'error': '시험 ID 목록이 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 구독 해제 (비활성화)
        updated_count = ExamSubscription.objects.filter(
            user=user,
            exam_id__in=exam_ids,
            is_active=True
        ).update(is_active=False)
        
        # 업데이트된 Subscribed Exams 목록 반환
        updated_subscriptions = ExamSubscription.objects.filter(
            user=user,
            is_active=True
        ).select_related('exam').order_by('-subscribed_at')
        
        exam_data = []
        for subscription in updated_subscriptions:
            exam_data.append({
                'id': str(subscription.exam.id),
                'title': subscription.exam.title_ko or subscription.exam.title_en or 'Unknown',
                'subscribed_at': subscription.subscribed_at.isoformat(),
                'is_public': subscription.exam.is_public,
                'is_original': subscription.exam.is_original
            })
        
        return Response({
            'success': True,
            'message': f'{updated_count}개 시험 구독이 해제되었습니다.',
            'exams': exam_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'시험을 My Exams로 이동 중 오류: {str(e)}')
        return Response({'error': f'시험을 My Exams로 이동 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def shuffle_subscribed_exams(request):
    """Subscribed Exams 목록을 셔플"""
    try:
        user = request.user
        if not user.is_authenticated:
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        exam_ids = request.data.get('exam_ids', [])
        if not exam_ids:
            return Response({'error': '시험 ID 목록이 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 구독된 시험 목록 조회
        subscriptions = ExamSubscription.objects.filter(
            user=user,
            exam_id__in=exam_ids,
            is_active=True
        ).select_related('exam')
        
        if len(subscriptions) != len(exam_ids):
            return Response({'error': '일부 시험을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        # 시험 목록을 셔플
        exam_list = list(subscriptions)
        random.shuffle(exam_list)
        
        # 셔플된 시험 목록 반환
        exam_data = []
        for subscription in exam_list:
            exam_data.append({
                'id': str(subscription.exam.id),
                'title': subscription.exam.title_ko or subscription.exam.title_en or 'Unknown',
                'subscribed_at': subscription.subscribed_at.isoformat(),
                'is_public': subscription.exam.is_public,
                'is_original': subscription.exam.is_original
            })
        
        return Response({
            'success': True,
            'message': f'{len(exam_ids)}개 시험이 셔플되었습니다.',
            'exams': exam_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'Subscribed Exams 셔플 중 오류: {str(e)}')
        return Response({'error': f'Subscribed Exams 셔플 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_exam_connected_studies(request, exam_id):
    """시험에 연결된 스터디(프로젝트) 목록을 조회합니다."""
    import time
    from django.db import connection
    import logging
    logger = logging.getLogger(__name__)
    
    start_time = time.time()
    total_queries_before = len(connection.queries)
    
    logger.info(f"========== GET_EXAM_CONNECTED_STUDIES 시작 ==========")
    logger.info(f"[GET_EXAM_CONNECTED_STUDIES] API 호출 - 시험 ID: {exam_id}, 사용자: {request.user.username if request.user.is_authenticated else 'anonymous'}")
    
    try:
        # 쿼리 최적화: select_related 추가
        query_start = time.time()
        query_queries_before = len(connection.queries)
        
        exam = Exam.objects.select_related('created_by', 'original_exam').get(id=exam_id)
        
        query_time = time.time() - query_start
        query_queries_after = len(connection.queries)
        logger.info(f"[GET_EXAM_CONNECTED_STUDIES] DB 조회 완료 - {query_queries_after - query_queries_before}개 쿼리, {query_time:.3f}초")
        
        # 시험 접근 권한 확인
        user = request.user
        if user.is_authenticated:
            # admin_role 사용자는 모든 시험에 접근 가능
            if hasattr(user, 'profile') and hasattr(user.profile, 'role') and user.profile.role == 'admin_role':
                pass  # 접근 허용
            else:
                # 일반 사용자는 다음 조건 중 하나를 만족해야 함:
                # 1. 시험이 공개되어 있거나
                # 2. 사용자가 해당 시험의 생성자이거나
                # 3. 사용자가 해당 시험이 포함된 스터디의 멤버이거나
                # 4. 사용자가 해당 시험을 이미 풀어본 적이 있거나

                # 시험이 공개되어 있는지 확인
                if exam.is_public:
                    pass  # 접근 허용
                else:
                    # 사용자가 해당 시험의 생성자인지 확인
                    is_creator = exam.created_by == user if exam.created_by else False

                    # 사용자가 해당 시험이 포함된 스터디의 멤버인지 확인
                    study_membership = Member.objects.filter(
                        user=user,
                        study__tasks__exam=exam,
                        is_active=True
                    ).exists()

                    # 사용자가 해당 시험을 이미 풀어본 적이 있는지 확인
                    has_taken_exam = ExamResult.objects.filter(
                        user=user,
                        exam=exam
                    ).exists()

                    if not is_creator and not study_membership and not has_taken_exam:
                        # 권한이 없어도 연결된 스터디 정보는 반환 (가입 요청 생성을 위해)
                        # 하지만 에러 플래그를 포함하여 권한 없음을 알림
                        pass  # 아래에서 연결된 스터디 정보 반환
        else:
            # 익명 사용자는 공개 시험만 접근 가능하지만, 연결된 프로젝트 정보는 제공하지 않음
            if not exam.is_public:
                return Response({'error': '이 시험에 접근할 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
            
            # 익명 사용자에게는 빈 연결된 프로젝트 목록 반환
            return Response({
                'success': True,
                'connected_studies': [],
                'total_count': 0
            }, status=status.HTTP_200_OK)

        # 시험에 연결된 StudyTask들을 조회 (최적화)
        study_tasks_start = time.time()
        study_tasks_queries_before = len(connection.queries)
        
        study_tasks = StudyTask.objects.filter(exam=exam).select_related('study', 'exam')
        
        study_tasks_time = time.time() - study_tasks_start
        study_tasks_queries_after = len(connection.queries)
        logger.info(f"[GET_EXAM_CONNECTED_STUDIES] StudyTask 조회 완료 - {study_tasks_queries_after - study_tasks_queries_before}개 쿼리, {study_tasks_time:.3f}초, 스터디 수: {study_tasks.count()}")
        
        # 연결된 스터디 정보 수집
        connected_studies = []
        for task in study_tasks:
            study = task.study
            
            # 사용자 언어에 맞는 스터디 제목 결정
            from quiz.utils.multilingual_utils import (
                BASE_LANGUAGE, LANGUAGE_KO, LANGUAGE_EN, LANGUAGE_ES, LANGUAGE_ZH, LANGUAGE_JA
            )
            user_language = BASE_LANGUAGE  # 기본값
            if user.is_authenticated and hasattr(user, 'profile') and hasattr(user.profile, 'language'):
                user_language = user.profile.language or BASE_LANGUAGE
            
            # 다국어 제목 선택 (사용자 언어 우선, 폴백 순서 적용) - 모든 언어 동일하게 처리
            from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
            study_title = None
            
            # 사용자 언어 필드 확인
            if hasattr(study, f'title_{user_language}'):
                study_title = getattr(study, f'title_{user_language}', None)
            
            # 사용자 언어 필드가 없으면 기본 언어 필드 확인
            if not study_title:
                if hasattr(study, f'title_{BASE_LANGUAGE}'):
                    study_title = getattr(study, f'title_{BASE_LANGUAGE}', None)
            
            # 기본 언어도 없으면 다른 언어 중 하나라도 사용
            if not study_title:
                for lang in SUPPORTED_LANGUAGES:
                    if hasattr(study, f'title_{lang}'):
                        study_title = getattr(study, f'title_{lang}', None)
                        if study_title:
                            break
            
            if not study_title:
                study_title = '제목 없음'  # 기본값
            
            # 사용자 언어에 맞는 Task 이름 결정 (모든 지원 언어 확인)
            from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
            task_name = get_localized_field(task, 'name', user_language, '이름 없음')
            if not task_name:
                task_name = '이름 없음'  # 기본값
            elif user_language == LANGUAGE_ES:
                task_name = (
                    getattr(task, 'name_es', None) or 
                    task.name_en or 
                    task.name_ko or 
                    getattr(task, 'name_zh', None) or 
                    getattr(task, 'name_ja', None) or 
                    'Sin nombre'
                )
            elif user_language == LANGUAGE_ZH:
                task_name = (
                    getattr(task, 'name_zh', None) or 
                    task.name_en or 
                    task.name_ko or 
                    getattr(task, 'name_es', None) or 
                    getattr(task, 'name_ja', None) or 
                    '无名称'
                )
            elif user_language == LANGUAGE_JA:
                task_name = (
                    getattr(task, 'name_ja', None) or 
                    task.name_en or 
                    task.name_ko or 
                    getattr(task, 'name_es', None) or 
                    getattr(task, 'name_zh', None) or 
                    '名前なし'
                )
            else:
                task_name = task.name_en or task.name_ko or 'No Name'
            
            connected_studies.append({
                'study_id': study.id,
                'study_title': study_title,  # Localized title for backward compatibility
                'title_ko': getattr(study, 'title_ko', None) or '',
                'title_en': getattr(study, 'title_en', None) or '',
                'title_es': getattr(study, 'title_es', None) or '',
                'title_zh': getattr(study, 'title_zh', None) or '',
                'title_ja': getattr(study, 'title_ja', None) or '',
                'task_id': task.id,
                'task_name': task_name,  # Localized task name for backward compatibility
                'task_name_ko': getattr(task, 'name_ko', None) or '',
                'task_name_en': getattr(task, 'name_en', None) or '',
                'task_name_es': getattr(task, 'name_es', None) or '',
                'task_name_zh': getattr(task, 'name_zh', None) or '',
                'task_name_ja': getattr(task, 'name_ja', None) or '',
                'study_url': f'/study-detail/{study.id}',
                'is_public': study.is_public
            })
        
        total_time = time.time() - start_time
        total_queries_after = len(connection.queries)
        total_query_count = total_queries_after - total_queries_before
        
        logger.info(f"[GET_EXAM_CONNECTED_STUDIES] 성능 요약 - 총 시간: {total_time:.3f}초, 총 쿼리: {total_query_count}개, 스터디 수: {len(connected_studies)}개")
        logger.info(f"========== GET_EXAM_CONNECTED_STUDIES 완료 ==========")
        
        return Response({
            'success': True,
            'connected_studies': connected_studies,
            'total_count': len(connected_studies)
        }, status=status.HTTP_200_OK)
        
    except Exam.DoesNotExist:
        logger.error(f"[GET_EXAM_CONNECTED_STUDIES] 시험을 찾을 수 없음 - exam_id: {exam_id}")
        return Response({'error': '시험을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f'시험 연결 스터디 조회 중 오류: {str(e)}')
        return Response({'error': f'시험 연결 스터디 조회 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _translate_content(text, from_language, to_language):
    """
    텍스트를 지정된 언어로 번역하는 함수 (Gemini 폴백 지원)
    
    Args:
        text: 번역할 텍스트
        from_language: 원본 언어 ('ko', 'en', 'es', 'zh', 'ja')
        to_language: 대상 언어 ('ko', 'en', 'es', 'zh', 'ja')
    
    Returns:
        str: 번역된 텍스트 또는 None (번역 실패 시)
    """
    if not text or not text.strip():
        return None
    
    # batch_translate_texts를 사용하여 Gemini 폴백 지원
    from quiz.utils.multilingual_utils import batch_translate_texts
    
    try:
        translated_results = batch_translate_texts([text], from_language, to_language)
        if translated_results and len(translated_results) > 0 and translated_results[0]:
            translated_text = translated_results[0]
            logger.info(f"[TRANSLATE] 번역 성공: '{text}' → '{translated_text}' ({from_language} → {to_language})")
            return translated_text
        else:
            logger.warning(f"[TRANSLATE] 번역 실패: {from_language} → {to_language}")
            return None
    except Exception as e:
        logger.warning(f"[TRANSLATE] 번역 중 예상치 못한 오류: {str(e)} - {from_language} → {to_language}")
        return None