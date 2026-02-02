#!/usr/bin/env python3
"""
DrillQuiz 제목 및 설명 번역 스크립트 (간단 버전)
study, exam, quiz의 _ko 컬럼들을 distinct로 조회하여 _en으로 번역합니다.
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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleTranslator:
    def __init__(self, limit: Optional[int] = None, target_models: Optional[List[str]] = None):
        self.translation_manager = TranslationManager()
        self.limit = limit
        self.target_models = target_models or ['study', 'exam', 'question']
        self.translation_cache = {}
    
    def translate_study_content(self):
        if 'study' not in self.target_models:
            return
            
        logger.info("Study 번역 시작...")
        
        studies_needing_translation = Study.objects.filter(
            models.Q(title_ko__isnull=False) & models.Q(title_ko__gt='') |
            models.Q(goal_ko__isnull=False) & models.Q(goal_ko__gt='')
        ).filter(
            models.Q(title_en__isnull=True) | models.Q(title_en='') |
            models.Q(goal_en__isnull=True) | models.Q(goal_en='')
        )
        
        # distinct로 고유한 내용들 조회
        unique_titles = studies_needing_translation.values_list('title_ko', flat=True).distinct()
        unique_goals = studies_needing_translation.values_list('goal_ko', flat=True).distinct()
        
        if self.limit:
            unique_titles = unique_titles[:self.limit]
            unique_goals = unique_goals[:self.limit]
        
        logger.info("Study 고유 제목: {}개, 고유 목표: {}개".format(len(unique_titles), len(unique_goals)))
        
        # 고유한 제목들만 번역
        for title in unique_titles:
            if title and title.strip():
                self._translate_and_update_study_title(title)
        
        # 고유한 목표들만 번역
        for goal in unique_goals:
            if goal and goal.strip():
                self._translate_and_update_study_goal(goal)
    
    def translate_exam_content(self):
        if 'exam' not in self.target_models:
            return
            
        logger.info("Exam 번역 시작...")
        
        exams_needing_translation = Exam.objects.filter(
            models.Q(title_ko__isnull=False) & models.Q(title_ko__gt='') |
            models.Q(description_ko__isnull=False) & models.Q(description_ko__gt='')
        ).filter(
            models.Q(title_en__isnull=True) | models.Q(title_en='') |
            models.Q(description_en__isnull=True) | models.Q(description_en='')
        )
        
        unique_titles = exams_needing_translation.values_list('title_ko', flat=True).distinct()
        unique_descriptions = exams_needing_translation.values_list('description_ko', flat=True).distinct()
        
        if self.limit:
            unique_titles = unique_titles[:self.limit]
            unique_descriptions = unique_descriptions[:self.limit]
        
        logger.info("Exam 고유 제목: {}개, 고유 설명: {}개".format(len(unique_titles), len(unique_descriptions)))
        
        for title in unique_titles:
            if title and title.strip():
                self._translate_and_update_exam_title(title)
        
        for desc in unique_descriptions:
            if desc and desc.strip():
                self._translate_and_update_exam_description(desc)
    
    def translate_question_content(self):
        if 'question' not in self.target_models:
            return
            
        logger.info("Question 번역 시작...")
        
        questions_needing_translation = Question.objects.filter(
            models.Q(title_ko__isnull=False) & models.Q(title_ko__gt='') |
            models.Q(content_ko__isnull=False) & models.Q(content_ko__gt='') |
            models.Q(answer_ko__isnull=False) & models.Q(answer_ko__gt='')
        ).filter(
            models.Q(title_en__isnull=True) | models.Q(title_en='') |
            models.Q(content_en__isnull=True) | models.Q(content_en='') |
            models.Q(answer_en__isnull=True) | models.Q(answer_en='')
        )
        
        unique_titles = questions_needing_translation.values_list('title_ko', flat=True).distinct()
        unique_contents = questions_needing_translation.values_list('content_ko', flat=True).distinct()
        unique_answers = questions_needing_translation.values_list('answer_ko', flat=True).distinct()
        
        if self.limit:
            unique_titles = unique_titles[:self.limit]
            unique_contents = unique_contents[:self.limit]
            unique_answers = unique_answers[:self.limit]
        
        logger.info("Question 고유 제목: {}개, 고유 내용: {}개, 고유 답변: {}개".format(
            len(unique_titles), len(unique_contents), len(unique_answers)))
        
        for title in unique_titles:
            if title and title.strip():
                self._translate_and_update_question_title(title)
        
        for content in unique_contents:
            if content and content.strip():
                self._translate_and_update_question_content(content)
        
        for answer in unique_answers:
            if answer and answer.strip():
                self._translate_and_update_question_answer(answer)
    
    def _is_english_only(self, text: str) -> bool:
        if not text:
            return False
        
        import re
        korean_pattern = re.compile(r'[가-힣]')
        return not korean_pattern.search(text)
    
    def _translate_text(self, source_text: str) -> Optional[str]:
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
            return self.translation_cache[source_text_clean]
        
        try:
            simple_key = "content"
            translated_dict = TranslationManager.translate_bulk_to_english({simple_key: source_text_clean})
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
    
    def _translate_and_update_study_title(self, title_ko: str):
        title_en = self._translate_text(title_ko)
        if title_en:
            Study.objects.filter(title_ko=title_ko).update(title_en=title_en)
            logger.info("Study 제목 업데이트: {} -> {}".format(title_ko[:50], title_en[:50]))
    
    def _translate_and_update_study_goal(self, goal_ko: str):
        goal_en = self._translate_text(goal_ko)
        if goal_en:
            Study.objects.filter(goal_ko=goal_ko).update(goal_en=goal_en)
            logger.info("Study 목표 업데이트: {} -> {}".format(goal_ko[:50], goal_en[:50]))
    
    def _translate_and_update_exam_title(self, title_ko: str):
        title_en = self._translate_text(title_ko)
        if title_en:
            Exam.objects.filter(title_ko=title_ko).update(title_en=title_en)
            logger.info("Exam 제목 업데이트: {} -> {}".format(title_ko[:50], title_en[:50]))
    
    def _translate_and_update_exam_description(self, description_ko: str):
        description_en = self._translate_text(description_ko)
        if description_en:
            Exam.objects.filter(description_ko=description_ko).update(description_en=description_en)
            logger.info("Exam 설명 업데이트: {} -> {}".format(description_ko[:50], description_en[:50]))
    
    def _translate_and_update_question_title(self, title_ko: str):
        title_en = self._translate_text(title_ko)
        if title_en:
            Question.objects.filter(title_ko=title_ko).update(title_en=title_en)
            logger.info("Question 제목 업데이트: {} -> {}".format(title_ko[:50], title_en[:50]))
    
    def _translate_and_update_question_content(self, content_ko: str):
        content_en = self._translate_text(content_ko)
        if content_en:
            Question.objects.filter(content_ko=content_ko).update(content_en=content_en)
            logger.info("Question 내용 업데이트: {} -> {}".format(content_ko[:50], content_en[:50]))
    
    def _translate_and_update_question_answer(self, answer_ko: str):
        answer_en = self._translate_text(answer_ko)
        if answer_en:
            Question.objects.filter(answer_ko=answer_ko).update(answer_en=answer_en)
            logger.info("Question 답변 업데이트: {} -> {}".format(answer_ko[:50], answer_en[:50]))
    
    def run_translation(self):
        logger.info("DrillQuiz 번역 스크립트 시작")
        
        if self.limit:
            logger.info("제한 설정: 처음 {}개만 처리".format(self.limit))
        
        self.translate_study_content()
        self.translate_exam_content()
        self.translate_question_content()
        
        logger.info("작업 완료!")

def main():
    parser = argparse.ArgumentParser(description='DrillQuiz 번역 스크립트 (간단 버전)')
    parser.add_argument('--limit', type=int, help='처리할 고유 내용 개수 제한')
    parser.add_argument('--models', help='처리할 모델 (study,exam,question) - 쉼표로 구분')
    
    args = parser.parse_args()
    
    target_models = None
    if args.models:
        target_models = [model.strip() for model in args.models.split(',')]
    
    translator = SimpleTranslator(limit=args.limit, target_models=target_models)
    translator.run_translation()

if __name__ == '__main__':
    main()
