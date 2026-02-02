#!/usr/bin/env python3
"""
DrillQuiz 제목 번역 스크립트
study, exam, quiz의 title_ko를 OpenAPI로 번역하여 title_en에 업데이트합니다.

사용법:
    python translate_titles_ko_to_en.py [--dry-run] [--limit N] [--model MODEL]

옵션:
    --dry-run: 실제 데이터베이스에 저장하지 않고 번역 결과만 확인
    --limit N: 번역할 최대 개수 제한 (기본값: 100)
    --model: 번역할 모델 선택 (study, exam, quiz, all) (기본값: all)
"""

import os
import sys
import django
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any
from django.db import transaction
from django.conf import settings

# Django 설정
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
django.setup()

from quiz.models import Study, Exam, Question
from quiz.utils.translation_utils import TranslationManager

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TitleTranslator:
    """제목 번역을 담당하는 클래스"""
    
    def __init__(self, dry_run: bool = False, limit: int = 100):
        self.dry_run = dry_run
        self.limit = limit
        self.stats = {
            'total_processed': 0,
            'translated': 0,
            'skipped': 0,
            'errors': 0,
            'models': {
                'study': {'processed': 0, 'translated': 0, 'skipped': 0, 'errors': 0},
                'exam': {'processed': 0, 'translated': 0, 'skipped': 0, 'errors': 0},
                'question': {'processed': 0, 'translated': 0, 'skipped': 0, 'errors': 0}
            }
        }
    
    def translate_study_titles(self) -> None:
        """Study 모델의 title_ko를 title_en으로 번역"""
        logger.info("📚 Study 제목 번역 시작...")
        
        # title_ko는 있지만 title_en이 없는 Study 조회
        studies = Study.objects.filter(
            title_ko__isnull=False,
            title_ko__gt='',
            title_en__isnull=True
        ).exclude(title_en__gt='')[:self.limit]
        
        logger.info(f"번역 대상 Study: {studies.count()}개")
        
        for study in studies:
            try:
                self.stats['models']['study']['processed'] += 1
                self.stats['total_processed'] += 1
                
                if self.dry_run:
                    logger.info(f"[DRY-RUN] Study 번역: '{study.title_ko}' -> 번역 예정")
                    self.stats['models']['study']['skipped'] += 1
                    self.stats['skipped'] += 1
                    continue
                
                # 번역 실행
                translated_title = TranslationManager.translate_single_to_english(study.title_ko)
                
                if translated_title and translated_title != study.title_ko:
                    study.title_en = translated_title
                    study.save(update_fields=['title_en'])
                    
                    logger.info(f"✅ Study 번역 완료: '{study.title_ko}' -> '{translated_title}'")
                    self.stats['models']['study']['translated'] += 1
                    self.stats['translated'] += 1
                else:
                    logger.warning(f"⚠️ Study 번역 실패: '{study.title_ko}'")
                    self.stats['models']['study']['errors'] += 1
                    self.stats['errors'] += 1
                    
            except Exception as e:
                logger.error(f"❌ Study 번역 오류 (ID: {study.id}): {e}")
                self.stats['models']['study']['errors'] += 1
                self.stats['errors'] += 1
    
    def translate_exam_titles(self) -> None:
        """Exam 모델의 title_ko를 title_en으로 번역"""
        logger.info("📝 Exam 제목 번역 시작...")
        
        # title_ko는 있지만 title_en이 없는 Exam 조회
        exams = Exam.objects.filter(
            title_ko__isnull=False,
            title_ko__gt='',
            title_en__isnull=True
        ).exclude(title_en__gt='')[:self.limit]
        
        logger.info(f"번역 대상 Exam: {exams.count()}개")
        
        for exam in exams:
            try:
                self.stats['models']['exam']['processed'] += 1
                self.stats['total_processed'] += 1
                
                if self.dry_run:
                    logger.info(f"[DRY-RUN] Exam 번역: '{exam.title_ko}' -> 번역 예정")
                    self.stats['models']['exam']['skipped'] += 1
                    self.stats['skipped'] += 1
                    continue
                
                # 번역 실행
                translated_title = TranslationManager.translate_single_to_english(exam.title_ko)
                
                if translated_title and translated_title != exam.title_ko:
                    exam.title_en = translated_title
                    exam.save(update_fields=['title_en'])
                    
                    logger.info(f"✅ Exam 번역 완료: '{exam.title_ko}' -> '{translated_title}'")
                    self.stats['models']['exam']['translated'] += 1
                    self.stats['translated'] += 1
                else:
                    logger.warning(f"⚠️ Exam 번역 실패: '{exam.title_ko}'")
                    self.stats['models']['exam']['errors'] += 1
                    self.stats['errors'] += 1
                    
            except Exception as e:
                logger.error(f"❌ Exam 번역 오류 (ID: {exam.id}): {e}")
                self.stats['models']['exam']['errors'] += 1
                self.stats['errors'] += 1
    
    def translate_question_titles(self) -> None:
        """Question 모델의 title_ko를 title_en으로 번역"""
        logger.info("❓ Question 제목 번역 시작...")
        
        # title_ko는 있지만 title_en이 없는 Question 조회
        questions = Question.objects.filter(
            title_ko__isnull=False,
            title_ko__gt='',
            title_en__isnull=True
        ).exclude(title_en__gt='')[:self.limit]
        
        logger.info(f"번역 대상 Question: {questions.count()}개")
        
        for question in questions:
            try:
                self.stats['models']['question']['processed'] += 1
                self.stats['total_processed'] += 1
                
                if self.dry_run:
                    logger.info(f"[DRY-RUN] Question 번역: '{question.title_ko}' -> 번역 예정")
                    self.stats['models']['question']['skipped'] += 1
                    self.stats['skipped'] += 1
                    continue
                
                # 번역 실행
                translated_title = TranslationManager.translate_single_to_english(question.title_ko)
                
                if translated_title and translated_title != question.title_ko:
                    question.title_en = translated_title
                    question.save(update_fields=['title_en'])
                    
                    logger.info(f"✅ Question 번역 완료: '{question.title_ko}' -> '{translated_title}'")
                    self.stats['models']['question']['translated'] += 1
                    self.stats['translated'] += 1
                else:
                    logger.warning(f"⚠️ Question 번역 실패: '{question.title_ko}'")
                    self.stats['models']['question']['errors'] += 1
                    self.stats['errors'] += 1
                    
            except Exception as e:
                logger.error(f"❌ Question 번역 오류 (ID: {question.id}): {e}")
                self.stats['models']['question']['errors'] += 1
                self.stats['errors'] += 1
    
    def translate_all(self, models: List[str]) -> None:
        """지정된 모델들의 제목을 번역"""
        logger.info(f"🚀 제목 번역 시작 (모델: {', '.join(models)})")
        logger.info(f"드라이 런: {'예' if self.dry_run else '아니오'}")
        logger.info(f"제한 개수: {self.limit}")
        logger.info("=" * 60)
        
        start_time = django.utils.timezone.now()
        
        try:
            if 'study' in models or 'all' in models:
                self.translate_study_titles()
            
            if 'exam' in models or 'all' in models:
                self.translate_exam_titles()
            
            if 'question' in models or 'all' in models:
                self.translate_question_titles()
                
        except Exception as e:
            logger.error(f"❌ 번역 중 오류 발생: {e}")
            raise
        
        end_time = django.utils.timezone.now()
        duration = end_time - start_time
        
        self.print_summary(duration)
    
    def print_summary(self, duration) -> None:
        """번역 결과 요약 출력"""
        logger.info("=" * 60)
        logger.info("📊 번역 결과 요약")
        logger.info("=" * 60)
        logger.info(f"총 처리 시간: {duration}")
        logger.info(f"총 처리 개수: {self.stats['total_processed']}")
        logger.info(f"번역 성공: {self.stats['translated']}")
        logger.info(f"건너뜀: {self.stats['skipped']}")
        logger.info(f"오류: {self.stats['errors']}")
        logger.info("")
        
        for model_name, stats in self.stats['models'].items():
            if stats['processed'] > 0:
                logger.info(f"{model_name.title()} 모델:")
                logger.info(f"  - 처리: {stats['processed']}")
                logger.info(f"  - 번역: {stats['translated']}")
                logger.info(f"  - 건너뜀: {stats['skipped']}")
                logger.info(f"  - 오류: {stats['errors']}")
                logger.info("")
        
        if self.dry_run:
            logger.info("🔍 드라이 런 모드: 실제 데이터베이스에 저장되지 않았습니다.")
        else:
            logger.info("💾 번역 결과가 데이터베이스에 저장되었습니다.")

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='DrillQuiz 제목 번역 스크립트')
    parser.add_argument('--dry-run', action='store_true', help='실제 저장하지 않고 번역 결과만 확인')
    parser.add_argument('--limit', type=int, default=100, help='번역할 최대 개수 (기본값: 100)')
    parser.add_argument('--model', choices=['study', 'exam', 'question', 'all'], 
                       default='all', help='번역할 모델 선택 (기본값: all)')
    
    args = parser.parse_args()
    
    # 모델 리스트 생성
    if args.model == 'all':
        models = ['study', 'exam', 'question']
    else:
        models = [args.model]
    
    try:
        # 번역기 생성 및 실행
        translator = TitleTranslator(dry_run=args.dry_run, limit=args.limit)
        translator.translate_all(models)
        
        logger.info("🎉 제목 번역 작업이 완료되었습니다!")
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 치명적 오류 발생: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
