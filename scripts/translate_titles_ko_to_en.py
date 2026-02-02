#!/usr/bin/env python3
"""
DrillQuiz 제목 및 설명 번역 스크립트
study, exam, quiz의 title_ko와 description_ko를 OpenAPI로 번역하여 title_en과 description_en에 업데이트합니다.

사용법:
    # 전체 실행
    python scripts/translate_titles_ko_to_en.py
    
    # 점진적 실행 (처음 50개만)
    python scripts/translate_titles_ko_to_en.py --limit 50
    
    # 특정 모델만 실행
    python scripts/translate_titles_ko_to_en.py --models study,exam
    
    # 점진적 실행 + 특정 모델
    python scripts/translate_titles_ko_to_en.py --limit 100 --models question

개발 환경 k8s DB 접속: localhost:51370
"""

import os
import sys
import django
import argparse
from pathlib import Path
import logging
from typing import List, Dict, Optional

# Django 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
django.setup()

from quiz.models import Study, Exam, Question
from quiz.utils.translation_utils import TranslationManager
from django.db import models

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ContentTranslator:
    """제목과 설명 번역을 담당하는 클래스"""
    
    def __init__(self, limit: Optional[int] = None, target_models: Optional[List[str]] = None, force_retranslate: bool = False):
        self.translation_manager = TranslationManager()
        self.limit = limit
        self.target_models = target_models or ['study', 'exam', 'question']
        self.force_retranslate = force_retranslate
        
        self.stats = {
            'study': {'total': 0, 'translated': 0, 'skipped': 0, 'failed': 0, 'cached': 0},
            'exam': {'total': 0, 'translated': 0, 'skipped': 0, 'failed': 0, 'cached': 0},
            'question': {'total': 0, 'translated': 0, 'skipped': 0, 'failed': 0, 'cached': 0}
        }
        # 번역 캐시 (한국어 내용 -> 영어 내용)
        self.translation_cache = {}
    
    def translate_study_content(self) -> None:
        """Study 모델의 title_ko와 description_ko를 번역 (중복 제거)"""
        if 'study' not in self.target_models:
            logger.info("⏭️ Study 번역 건너뜀 (--models 옵션에서 제외됨)")
            return
            
        logger.info("📚 Study 제목 및 설명 번역 시작...")
        
        # 번역이 필요한 Study들을 가져옴 (title 또는 goal 중 하나라도 번역이 필요한 경우)
        studies_needing_translation = Study.objects.filter(
            title_ko__isnull=False,
            title_ko__gt=''
        ).filter(
            models.Q(title_en__isnull=True) | models.Q(title_en='') |
            models.Q(goal_en__isnull=True) | models.Q(goal_en='')
        )
        
        # 중복 제거: 고유한 한국어 제목만 번역
        unique_ko_titles = studies_needing_translation.values_list('title_ko', flat=True).distinct()
        
        # 제한 적용
        if self.limit:
            unique_ko_titles = unique_ko_titles[:self.limit]
            logger.info(f"📊 제한 적용: 처음 {self.limit}개만 처리")
        
        self.stats['study']['total'] = studies_needing_translation.count()
        unique_count = len(unique_ko_titles)
        logger.info(f"📊 번역 대상 Study: {self.stats['study']['total']}개 (고유 제목: {unique_count}개)")
        
        # 고유한 제목들만 번역
        for unique_title in unique_ko_titles:
            try:
                # 해당 제목을 가진 첫 번째 Study를 번역
                first_study = studies_needing_translation.filter(title_ko=unique_title).first()
                if first_study and self._translate_study_content(first_study, 'study'):
                    self.stats['study']['translated'] += 1
                    logger.info(f"✅ Study 번역 완료: '{unique_title}'")
                    
                                            # 같은 제목을 가진 다른 Study들도 업데이트
                    other_studies = studies_needing_translation.filter(title_ko=unique_title).exclude(id=first_study.id)
                    if other_studies.exists():
                        for other_study in other_studies:
                            other_study.title_en = first_study.title_en
                            other_study.goal_en = first_study.goal_en
                            other_study.save()
                        logger.info(f"🔄 같은 제목 Study {other_studies.count()}개 업데이트 완료: '{unique_title}'")
                    
                else:
                    self.stats['study']['skipped'] += 1
                    logger.info(f"⏭️ Study 번역 건너뜀: '{unique_title}' (번역 실패 또는 이미 영어 내용 존재)")
            except Exception as e:
                self.stats['study']['failed'] += 1
                logger.error(f"❌ Study 번역 실패: '{unique_title}' - {str(e)}")
    
    def translate_exam_content(self) -> None:
        """Exam 모델의 title_ko와 description_ko를 번역 (중복 제거)"""
        if 'exam' not in self.target_models:
            logger.info("⏭️ Exam 번역 건너뜀 (--models 옵션에서 제외됨)")
            return
            
        logger.info("📝 Exam 제목 및 설명 번역 시작...")
        
        # 번역이 필요한 Exam들을 가져옴 (title 또는 description 중 하나라도 번역이 필요한 경우)
        exams_needing_translation = Exam.objects.filter(
            title_ko__isnull=False,
            title_ko__gt=''
        ).filter(
            models.Q(title_en__isnull=True) | models.Q(title_en='') |
            models.Q(description_en__isnull=True) | models.Q(description_en='')
        )
        
        # 중복 제거: 고유한 한국어 제목만 번역
        unique_ko_titles = exams_needing_translation.values_list('title_ko', flat=True).distinct()
        
        # 제한 적용
        if self.limit:
            unique_ko_titles = unique_ko_titles[:self.limit]
            logger.info(f"📊 제한 적용: 처음 {self.limit}개만 처리")
        
        self.stats['exam']['total'] = exams_needing_translation.count()
        unique_count = len(unique_ko_titles)
        logger.info(f"📊 번역 대상 Exam: {self.stats['exam']['total']}개 (고유 제목: {unique_count}개)")
        
        # 고유한 제목들만 번역
        for unique_title in unique_ko_titles:
            try:
                # 해당 제목을 가진 첫 번째 Exam을 번역
                first_exam = exams_needing_translation.filter(title_ko=unique_title).first()
                if first_exam and self._translate_exam_content(first_exam, 'exam'):
                    self.stats['exam']['translated'] += 1
                    logger.info(f"✅ Exam 번역 완료: '{unique_title}'")
                    
                    # 같은 제목을 가진 다른 Exam들도 업데이트
                    other_exams = exams_needing_translation.filter(title_ko=unique_title).exclude(id=first_exam.id)
                    if other_exams.exists():
                        for other_exam in other_exams:
                            other_exam.title_en = first_exam.title_en
                            other_exam.description_en = first_exam.description_en
                            other_exam.save()
                        logger.info(f"🔄 같은 제목 Exam {other_exams.count()}개 업데이트 완료: '{unique_title}'")
                    
                else:
                    self.stats['exam']['skipped'] += 1
                    logger.info(f"⏭️ Exam 번역 건너뜀: '{unique_title}' (번역 실패 또는 이미 영어 내용 존재)")
            except Exception as e:
                self.stats['exam']['failed'] += 1
                logger.error(f"❌ Exam 번역 실패: '{unique_title}' - {str(e)}")
    
    def translate_question_content(self) -> None:
        """Question 모델의 title_ko, content_ko, answer_ko를 번역 (중복 제거)"""
        if 'question' not in self.target_models:
            logger.info("⏭️ Question 번역 건너뜀 (--models 옵션에서 제외됨)")
            return
            
        logger.info("❓ Question 제목, 내용, 답변 번역 시작...")
        
        # 번역이 필요한 Question들을 가져옴 (title, content, answer 중 하나라도 번역이 필요한 경우)
        questions_needing_translation = Question.objects.filter(
            title_ko__isnull=False,
            title_ko__gt=''
        ).filter(
            models.Q(title_en__isnull=True) | models.Q(title_en='') |
            models.Q(content_en__isnull=True) | models.Q(content_en='') |
            models.Q(answer_en__isnull=True) | models.Q(answer_en='')
        )
        
        # 중복 제거: 고유한 한국어 제목만 번역
        unique_ko_titles = questions_needing_translation.values_list('title_ko', flat=True).distinct()
        
        # 제한 적용
        if self.limit:
            unique_ko_titles = unique_ko_titles[:self.limit]
            logger.info(f"📊 제한 적용: 처음 {self.limit}개만 처리")
        
        self.stats['question']['total'] = questions_needing_translation.count()
        unique_count = len(unique_ko_titles)
        logger.info(f"📊 번역 대상 Question: {self.stats['question']['total']}개 (고유 제목: {unique_count}개)")
        
        batch_size = 100
        for i in range(0, len(unique_ko_titles), batch_size):
            batch_titles = unique_ko_titles[i:i+batch_size]
            logger.info(f"🔄 Question 번역 배치 {i//batch_size + 1}/{(len(unique_ko_titles) + batch_size - 1)//batch_size} 처리 중...")
            
            for unique_title in batch_titles:
                try:
                    first_question = questions_needing_translation.filter(title_ko=unique_title).first()
                    if first_question and self._translate_question_content(first_question, 'question'):
                        self.stats['question']['translated'] += 1
                        logger.info(f"✅ Question 번역 완료: '{unique_title}'")
                        
                        other_questions = questions_needing_translation.filter(title_ko=unique_title).exclude(id=first_question.id)
                        if other_questions.exists():
                            other_questions.update(
                                title_en=first_question.title_en,
                                content_en=first_question.content_en,
                                answer_en=first_question.answer_en
                            )
                            logger.info(f"🔄 같은 제목 Question {other_questions.count()}개 업데이트 완료: '{unique_title}'")
                        
                    else:
                        self.stats['question']['skipped'] += 1
                        logger.info(f"⏭️ Question 번역 건너뜀: '{unique_title}' (번역 실패 또는 이미 영어 내용 존재)")
                except Exception as e:
                    self.stats['question']['failed'] += 1
                    logger.error(f"❌ Question 번역 실패: '{unique_title}' - {str(e)}")
    
    def _translate_study_content(self, obj, model_type: str) -> bool:
        """Study의 title과 goal을 번역 (간단하게)"""
        try:
            # 간단하게: 각 필드별로 번역
            title_translated = self._translate_single_field(obj, 'title_ko', 'title_en', model_type)
            goal_translated = self._translate_single_field(obj, 'goal_ko', 'goal_en', model_type)
            
            # 하나라도 번역되었으면 저장
            if title_translated or goal_translated:
                obj.save()
                return True
            return False
        except Exception as e:
            logger.error(f"Study 내용 번역 중 오류: {str(e)}")
            return False
    
    def _translate_exam_content(self, obj, model_type: str) -> bool:
        """Exam의 title과 description을 번역 (간단하게)"""
        try:
            # 간단하게: 각 필드별로 번역
            title_translated = self._translate_single_field(obj, 'title_ko', 'title_en', model_type)
            description_translated = self._translate_single_field(obj, 'description_ko', 'description_en', model_type)
            
            # 하나라도 번역되었으면 저장
            if title_translated or description_translated:
                obj.save()
                return True
            return False
        except Exception as e:
            logger.error(f"Exam 내용 번역 중 오류: {str(e)}")
            return False
    
    def _translate_question_content(self, obj, model_type: str) -> bool:
        """Question의 title, content, answer를 번역 (간단하게)"""
        try:
            # 간단하게: 각 필드별로 번역
            title_translated = self._translate_single_field(obj, 'title_ko', 'title_en', model_type)
            content_translated = self._translate_single_field(obj, 'content_ko', 'content_en', model_type)
            answer_translated = self._translate_single_field(obj, 'answer_ko', 'answer_en', model_type)
            
            # 하나라도 번역되었으면 저장
            if title_translated or content_translated or answer_translated:
                obj.save()
                return True
            return False
        except Exception as e:
            logger.error(f"Question 내용 번역 중 오류: {str(e)}")
            return False
    
    def _translate_single_field(self, obj, source_field: str, target_field: str, model_type: str) -> bool:
        """단일 필드 번역 (이미 번역된 필드는 스킵)"""
        source_text = getattr(obj, source_field)  # 한국어 원본 (예: title_ko)
        target_text = getattr(obj, target_field)  # 영어 번역 결과 (예: title_en)
        
        # 강력한 디버깅 로그
        logger.info(f"🔍 실제 DB 값 확인:")
        logger.info(f"   {source_field}: '{getattr(obj, source_field)}'")
        logger.info(f"   {target_field}: '{getattr(obj, target_field)}'")
        logger.info(f"   target_text: '{target_text}'")
        logger.info(f"   target_text.strip(): '{target_text.strip() if target_text else 'None'}'")
        logger.info(f"   target_text 길이: {len(target_text) if target_text else 0}")
        
        # 이미 번역된 필드는 스킵 (강제 재번역 모드가 아닌 경우)
        if target_text and target_text.strip() and not self.force_retranslate: 
            logger.info(f"⏭️ 스킵: {target_field}이 이미 번역됨 (값: '{target_text}')")
            return False
        
        # 소스 텍스트가 없으면 스킵
        if not source_text or not source_text.strip(): 
            logger.info(f"⏭️ 스킵: {source_field}이 비어있음")
            return False
        
        # 너무 짧은 텍스트는 복사 (한 글자 등)
        if len(source_text.strip()) < 2:
            logger.info(f"📋 복사: {source_field}이 너무 짧음 (길이: {len(source_text.strip())}, 내용: '{source_text}') -> {target_field}에 복사")
            setattr(obj, target_field, source_text.strip())
            return True
        
        source_text_clean = source_text.strip()
        
        # 캐시 확인
        cache_key = f"{source_field}_{source_text_clean}"
        if cache_key in self.translation_cache:
            cached_translation = self.translation_cache[cache_key]
            if cached_translation:
                setattr(obj, target_field, cached_translation)
                self.stats[model_type]['cached'] += 1
                logger.info(f"💾 캐시 사용: '{source_text_clean[:50]}...' -> '{cached_translation[:50]}...'")
                return True
        
        try:
            simple_key = "content"
            translated_dict = TranslationManager.translate_bulk_to_english({simple_key: source_text_clean})
            translated_text = translated_dict.get(simple_key, '')
            
            if translated_text and translated_text.strip():
                translated_text_clean = translated_text.strip()
                self.translation_cache[cache_key] = translated_text_clean
                setattr(obj, target_field, translated_text_clean)
                logger.info(f"✅ 번역 완료: '{source_text_clean[:50]}...' -> '{translated_text_clean[:50]}...'")
                return True
            else:
                logger.warning(f"⚠️ 번역 결과가 비어있음: '{source_text_clean[:50]}...'")
                return False
        except Exception as e:
            logger.error(f"번역 중 오류 발생: '{source_text_clean[:50]}...' - {str(e)}")
            return False
    
    def run_translation(self) -> None:
        """번역 실행"""
        logger.info("🚀 DrillQuiz 제목 및 설명 번역 스크립트 시작")
        logger.info("=" * 60)
        
        if self.limit:
            logger.info(f"📊 제한 설정: 처음 {self.limit}개 고유 제목만 처리")
        
        # 각 모델별 번역 실행
        self.translate_study_content()
        self.translate_exam_content()
        self.translate_question_content()
        
        # 통계 출력
        self._print_statistics()
        
        logger.info("\n✅ 작업이 완료되었습니다!")
    
    def _print_statistics(self) -> None:
        """번역 통계 출력"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 번역 완료 통계")
        logger.info("=" * 60)
        
        for model_type in ['study', 'exam', 'question']:
            stats = self.stats[model_type]
            logger.info(f"\n🔍 {model_type.upper()}:")
            logger.info(f"   총 대상: {stats['total']}개")
            logger.info(f"   번역 완료: {stats['translated']}개")
            logger.info(f"   캐시 사용: {stats['cached']}개")
            logger.info(f"   건너뜀: {stats['skipped']}개")
            logger.info(f"   실패: {stats['failed']}개")
        
        total_translated = sum(stats['translated'] for stats in self.stats.values())
        total_cached = sum(stats['cached'] for stats in self.stats.values())
        total_failed = sum(stats['failed'] for stats in self.stats.values())
        
        logger.info(f"\n🎯 전체 요약:")
        logger.info(f"   총 번역 완료: {total_translated}개")
        logger.info(f"   총 캐시 사용: {total_cached}개")
        logger.info(f"   총 실패: {total_failed}개")
        
        if total_failed == 0:
            logger.info("🎉 모든 번역이 성공적으로 완료되었습니다!")
        else:
            logger.info(f"⚠️ {total_failed}개 번역이 실패했습니다.")

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='DrillQuiz 제목 및 설명 번역 스크립트')
    parser.add_argument('--limit', type=int, help='처리할 고유 제목 개수 제한')
    parser.add_argument('--models', help='처리할 모델 (study,exam,question) - 쉼표로 구분')
    parser.add_argument('--dry-run', action='store_true', help='실제 번역하지 않고 번역 대상만 확인')
    parser.add_argument('--force-retranslate', action='store_true', help='이미 번역된 항목도 강제로 다시 번역')
    
    args = parser.parse_args()
    
    # 모델 리스트 파싱
    target_models = None
    if args.models:
        target_models = [model.strip() for model in args.models.split(',')]
    
    # 번역 실행
    translator = ContentTranslator(limit=args.limit, target_models=target_models, force_retranslate=args.force_retranslate)
    translator.run_translation()

if __name__ == '__main__':
    main()
