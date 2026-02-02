#!/usr/bin/env python3
"""
DrillQuiz Question 제목 번역 스크립트
Question 테이블의 title_ko 컬럼을 읽어서 title_en으로 OpenAPI 번역하여 업데이트합니다.
devops-dev DB에 포트포워딩으로 접근합니다.
"""

import os
import sys
import django
import argparse
from pathlib import Path
import logging
from typing import List, Dict, Optional
import time

# Django 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
django.setup()

from quiz.models import Question
from quiz.utils.translation_utils import TranslationManager
from django.db import models, connection

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QuestionTitleTranslator:
    def __init__(self, limit: Optional[int] = None, batch_size: int = 50, delay: float = 1.0):
        self.translation_manager = TranslationManager()
        self.limit = limit
        self.batch_size = batch_size
        self.delay = delay  # API 호출 간 지연 시간 (초)
        self.translation_cache = {}
        self.stats = {
            'total_processed': 0,
            'translated': 0,
            'skipped': 0,
            'errors': 0
        }
    
    def get_questions_needing_translation(self):
        """번역이 필요한 Question들을 조회합니다."""
        logger.info("번역이 필요한 Question 조회 중...")
        
        # 전체 Question 상태 확인
        total_questions = Question.objects.count()
        questions_with_title_ko = Question.objects.filter(
            models.Q(title_ko__isnull=False) & models.Q(title_ko__gt='')
        ).count()
        questions_with_title_en = Question.objects.filter(
            models.Q(title_en__isnull=False) & models.Q(title_en__gt='')
        ).count()
        
        logger.info("전체 Question: {}개".format(total_questions))
        logger.info("title_ko가 있는 Question: {}개".format(questions_with_title_ko))
        logger.info("title_en이 있는 Question: {}개".format(questions_with_title_en))
        
        # 번역이 필요한 Question 조회 (더 넓은 범위로 테스트)
        questions = Question.objects.filter(
            models.Q(title_ko__isnull=False) & 
            models.Q(title_ko__gt='')
        ).values('id', 'title_ko', 'title_en')
        
        logger.info("title_ko가 있는 모든 Question: {}개".format(len(questions)))
        
        # 실제 번역이 필요한 것만 필터링
        questions_needing_translation = [
            q for q in questions 
            if not q['title_en'] or q['title_en'].strip() == ''
        ]
        
        logger.info("실제 번역이 필요한 Question: {}개".format(len(questions_needing_translation)))
        
        if self.limit:
            questions_needing_translation = questions_needing_translation[:self.limit]
        
        return questions_needing_translation
        
        if self.limit:
            questions = questions[:self.limit]
        
        logger.info("번역이 필요한 Question: {}개".format(len(questions)))
        
        # 샘플 데이터 확인 (더 자세한 정보)
        if questions:
            sample = questions[0]
            logger.info("샘플 데이터: id={}, title_ko='{}', title_en='{}'".format(
                sample['id'], sample['title_ko'][:50], sample['title_en'] or 'None'
            ))
            
            # title_en이 있지만 내용이 비어있는 경우 확인
            empty_title_en_count = Question.objects.filter(
                models.Q(title_en__isnull=False) & 
                (models.Q(title_en='') | models.Q(title_en__exact=''))
            ).count()
            
            logger.info("title_en이 있지만 내용이 비어있는 Question: {}개".format(empty_title_en_count))
            
            # title_en과 title_ko가 다른 경우 확인
            different_content_count = Question.objects.filter(
                models.Q(title_ko__isnull=False) & 
                models.Q(title_ko__gt='') &
                models.Q(title_en__isnull=False) &
                models.Q(title_en__gt='') &
                ~models.Q(title_ko=models.F('title_en'))
            ).count()
            
            logger.info("title_ko와 title_en이 다른 Question: {}개".format(different_content_count))
        
        # 실제 문제 상황 분석
        logger.info("\n=== 문제 상황 분석 ===")
        
        # 1. title_en이 비어있는 경우
        empty_title_en = Question.objects.filter(
            models.Q(title_en__isnull=True) | models.Q(title_en='')
        ).count()
        logger.info("1. title_en이 비어있는 Question: {}개".format(empty_title_en))
        
        # 2. title_en이 공백만 있는 경우
        whitespace_title_en = Question.objects.filter(
            models.Q(title_en__isnull=False) & 
            models.Q(title_en__exact='')
        ).count()
        logger.info("2. title_en이 공백만 있는 Question: {}개".format(whitespace_title_en))
        
        # 3. title_en이 'null' 문자열인 경우
        null_string_title_en = Question.objects.filter(
            models.Q(title_en__isnull=False) & 
            models.Q(title_en__exact='null')
        ).count()
        logger.info("3. title_en이 'null' 문자열인 Question: {}개".format(null_string_title_en))
        
        # 4. 실제 샘플 데이터 확인
        sample_questions = Question.objects.all()[:3]
        logger.info("\n4. 샘플 Question 데이터:")
        for i, q in enumerate(sample_questions):
            logger.info("   Question {}: id={}, title_ko='{}', title_en='{}'".format(
                i+1, q.id, q.title_ko[:30] if q.title_ko else 'None', 
                q.title_en[:30] if q.title_en else 'None'
            ))
        
        return questions
    
    def get_unique_titles(self, questions):
        """고유한 한국어 제목들을 추출합니다."""
        unique_titles = {}
        for question in questions:
            title_ko = question['title_ko'].strip()
            if title_ko and title_ko not in unique_titles:
                unique_titles[title_ko] = []
            if title_ko in unique_titles:
                unique_titles[title_ko].append(question['id'])
        
        # 중복 제거 확인 로그
        total_questions = sum(len(ids) for ids in unique_titles.values())
        logger.info("고유한 한국어 제목: {}개 (총 {}개 Question)".format(len(unique_titles), total_questions))
        
        # 중복 제거 효과 표시
        if total_questions > len(unique_titles):
            saved_translations = total_questions - len(unique_titles)
            logger.info("중복 제거로 인한 번역 작업 절약: {}개".format(saved_translations))
        
        return unique_titles
    
    def _is_english_only(self, text: str) -> bool:
        """텍스트가 영어만으로 구성되어 있는지 확인합니다."""
        if not text:
            return False
        
        import re
        korean_pattern = re.compile(r'[가-힣]')
        return not korean_pattern.search(text)
    
    def _translate_text(self, source_text: str) -> Optional[str]:
        """텍스트를 영어로 번역합니다."""
        if not source_text or not source_text.strip():
            return None
        
        source_text_clean = source_text.strip()
        
        if len(source_text_clean) < 2:
            return source_text_clean
        
        # 영어만 있는 경우 복사
        if self._is_english_only(source_text_clean):
            logger.info("영어 감지, 복사: {}".format(source_text_clean[:50]))
            return source_text_clean
        
        # 캐시 확인
        if source_text_clean in self.translation_cache:
            logger.info("캐시에서 번역 결과 사용: {}".format(source_text_clean[:50]))
            return self.translation_cache[source_text_clean]
        
        try:
            # API 호출 간 지연
            time.sleep(self.delay)
            
            simple_key = "content"
            translated_dict = self.translation_manager.translate_bulk_to_english({simple_key: source_text_clean})
            translated_text = translated_dict.get(simple_key, '')
            
            if translated_text and translated_text.strip():
                translated_text_clean = translated_text.strip()
                self.translation_cache[source_text_clean] = translated_text_clean
                logger.info("번역 완료: {} -> {}".format(source_text_clean[:50], translated_text_clean[:50]))
                return translated_text_clean
            else:
                logger.warning("번역 결과가 비어있음: {}".format(source_text_clean[:50]))
                return None
        except Exception as e:
            logger.error("번역 중 오류: {} - {}".format(source_text_clean[:50], str(e)))
            return None
    
    def translate_and_update_titles(self):
        """제목들을 번역하고 업데이트합니다."""
        questions = self.get_questions_needing_translation()
        if not questions:
            logger.info("번역이 필요한 Question이 없습니다.")
            return
        
        unique_titles = self.get_unique_titles(questions)
        
        logger.info("번역 작업 시작...")
        
        for title_ko, question_ids in unique_titles.items():
            try:
                logger.info("제목 번역 중: '{}' ({}개 Question)".format(title_ko[:50], len(question_ids)))
                
                title_en = self._translate_text(title_ko)
                
                if title_en:
                    # 해당 제목을 가진 모든 Question 업데이트
                    updated_count = Question.objects.filter(
                        id__in=question_ids
                    ).update(title_en=title_en)
                    
                    self.stats['translated'] += updated_count
                    self.stats['total_processed'] += len(question_ids)
                    
                    logger.info("✓ 제목 업데이트 완료: '{}' -> '{}' ({}개 Question)".format(
                        title_ko[:50], title_en[:50], updated_count
                    ))
                else:
                    self.stats['skipped'] += len(question_ids)
                    logger.warning("⚠ 번역 실패로 건너뜀: '{}'".format(title_ko[:50]))
                
            except Exception as e:
                self.stats['errors'] += len(question_ids)
                logger.error("✗ 제목 업데이트 중 오류: '{}' - {}".format(title_ko[:50], str(e)))
        
        self._print_stats()
    
    def _print_stats(self):
        """통계 정보를 출력합니다."""
        logger.info("=" * 60)
        logger.info("🎯 번역 작업 완료!")
        logger.info("📊 작업 통계:")
        logger.info("  • 총 처리된 Question: {}개".format(self.stats['total_processed']))
        logger.info("  • 성공적으로 번역된 Question: {}개".format(self.stats['translated']))
        logger.info("  • 건너뛴 Question: {}개".format(self.stats['skipped']))
        logger.info("  • 오류 발생 Question: {}개".format(self.stats['errors']))
        
        if self.stats['translated'] > 0:
            success_rate = (self.stats['translated'] / self.stats['total_processed']) * 100
            logger.info("  • 성공률: {:.1f}%".format(success_rate))
        
        logger.info("💡 중복 제거 효과:")
        logger.info("  • 고유한 제목만 번역하여 API 호출 최소화")
        logger.info("  • 동일한 title_kr을 가진 모든 Question의 title_en 자동 업데이트")
        logger.info("=" * 60)
    
    def run_translation(self):
        """번역 작업을 실행합니다."""
        logger.info("DrillQuiz Question 제목 번역 스크립트 시작")
        logger.info("devops-dev DB에 연결 중...")
        
        # DB 연결 확인
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM quiz_question")
                total_questions = cursor.fetchone()[0]
                logger.info("전체 Question 수: {}개".format(total_questions))
        except Exception as e:
            logger.error("DB 연결 확인 실패: {}".format(str(e)))
            return
        
        if self.limit:
            logger.info("제한 설정: 처음 {}개만 처리".format(self.limit))
        
        logger.info("배치 크기: {}개".format(self.batch_size))
        logger.info("API 호출 간 지연: {}초".format(self.delay))
        
        self.translate_and_update_titles()

def main():
    parser = argparse.ArgumentParser(
        description='DrillQuiz Question 제목 번역 스크립트',
        epilog="""
사용 예시:
  # 처음 100개만 처리
  python scripts/translate_question_titles_kr_to_en.py --limit 100
  
  # API 호출 간 지연을 2초로 설정
  python scripts/translate_question_titles_kr_to_en.py --delay 2.0
  
  # 모든 Question 처리 (기본값)
  python scripts/translate_question_titles_kr_to_en.py
        """
    )
    parser.add_argument('--limit', type=int, help='처리할 Question 개수 제한')
    parser.add_argument('--batch-size', type=int, default=50, help='배치 크기 (기본값: 50)')
    parser.add_argument('--delay', type=float, default=1.0, help='API 호출 간 지연 시간(초) (기본값: 1.0)')
    
    args = parser.parse_args()
    
    translator = QuestionTitleTranslator(
        limit=args.limit,
        batch_size=args.batch_size,
        delay=args.delay
    )
    translator.run_translation()

if __name__ == '__main__':
    main()
