#!/usr/bin/env python3
"""
DrillQuiz 콘텐츠 일괄 번역 관리 명령어
백엔드에서 스터디, 시험 등의 콘텐츠를 일괄적으로 번역합니다.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings
from quiz.models import Study, Exam, Question
from quiz.utils.translation_utils import TranslationManager
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'DrillQuiz 콘텐츠를 일괄적으로 번역합니다.'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--content-type',
            type=str,
            choices=['study', 'exam', 'question', 'all'],
            default='all',
            help='번역할 콘텐츠 타입 (study, exam, question, all)'
        )
        parser.add_argument(
            '--direction',
            type=str,
            choices=['ko_to_en', 'en_to_ko', 'both', 'all'],
            default='all',
            help='번역 방향 (ko_to_en, en_to_ko, both, all) - all은 모든 언어 쌍에 대해 번역'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제 번역 없이 번역이 필요한 콘텐츠만 확인'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='번역할 최대 콘텐츠 수'
        )
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='번역 캐시를 정리한 후 번역 실행'
        )
    
    def handle(self, *args, **options):
        content_type = options['content_type']
        direction = options['direction']
        dry_run = options['dry_run']
        limit = options['limit']
        clear_cache = options['clear_cache']
        
        # OpenAI API 키 확인
        if not getattr(settings, 'OPENAI_API_KEY', None):
            raise CommandError('OpenAI API 키가 설정되지 않았습니다. settings.py에 OPENAI_API_KEY를 설정해주세요.')
        
        if clear_cache:
            self.stdout.write('🗑️ 번역 캐시 정리 중...')
            TranslationManager.clear_cache()
            self.stdout.write(self.style.SUCCESS('✅ 번역 캐시 정리 완료'))
        
        if dry_run:
            self.stdout.write('🔍 번역이 필요한 콘텐츠 확인 중... (실제 번역 없음)')
        
        try:
            if content_type in ['study', 'all']:
                self.translate_studies(direction, dry_run, limit)
            
            if content_type in ['exam', 'all']:
                self.translate_exams(direction, dry_run, limit)
            
            if content_type in ['question', 'all']:
                self.translate_questions(direction, dry_run, limit)
            
            self.stdout.write(self.style.SUCCESS('🎉 일괄 번역 완료!'))
            
        except Exception as e:
            logger.error(f'일괄 번역 중 오류: {str(e)}')
            raise CommandError(f'번역 중 오류가 발생했습니다: {str(e)}')
    
    def translate_studies(self, direction, dry_run, limit):
        """스터디 콘텐츠 번역"""
        from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES, BASE_LANGUAGE
        
        self.stdout.write('📚 스터디 번역 시작...')
        
        # 번역이 필요한 스터디 조회
        studies_to_translate = []
        
        if direction == 'all':
            # 모든 언어 쌍에 대해 번역 (기본 언어를 기준으로 다른 언어로 번역)
            for source_lang in SUPPORTED_LANGUAGES:
                for target_lang in SUPPORTED_LANGUAGES:
                    if source_lang == target_lang:
                        continue
                    
                    source_title_field = f'title_{source_lang}'
                    source_goal_field = f'goal_{source_lang}'
                    target_title_field = f'title_{target_lang}'
                    
                    if not hasattr(Study, source_title_field) or not hasattr(Study, target_title_field):
                        continue
                    
                    studies = Study.objects.filter(
                        **{f'{source_title_field}__isnull': False, f'{source_title_field}__gt': ''}
                    ).filter(
                        **{f'{target_title_field}__isnull': True}
                    ).exclude(**{f'{target_title_field}__gt': ''})
                    
                    for study in studies:
                        studies_to_translate.append({
                            'study': study,
                            'fields': {
                                'title': getattr(study, source_title_field, ''),
                                'goal': getattr(study, source_goal_field, '') or ''
                            },
                            'source_lang': source_lang,
                            'target_lang': target_lang
                        })
        else:
            # 기존 방식 유지 (하위 호환성)
            if direction in ['ko_to_en', 'both']:
                ko_studies = Study.objects.filter(
                    title_ko__isnull=False,
                    title_ko__gt='',
                    title_en__isnull=True
                ).exclude(title_en__gt='')
                
                for study in ko_studies:
                    studies_to_translate.append({
                        'study': study,
                        'fields': {'title': study.title_ko, 'goal': study.goal_ko or ''},
                        'source_lang': 'ko',
                        'target_lang': 'en'
                    })
            
            if direction in ['en_to_ko', 'both']:
                en_studies = Study.objects.filter(
                    title_en__isnull=False,
                    title_en__gt='',
                    title_ko__isnull=True
                ).exclude(title_ko__gt='')
                
                for study in en_studies:
                    studies_to_translate.append({
                        'study': study,
                        'fields': {'title': study.title_en, 'goal': study.goal_en or ''},
                        'source_lang': 'en',
                        'target_lang': 'ko'
                    })
        
        if limit:
            studies_to_translate = studies_to_translate[:limit]
        
        self.stdout.write(f'📊 번역이 필요한 스터디: {len(studies_to_translate)}개')
        
        if dry_run:
            for item in studies_to_translate:
                study = item['study']
                self.stdout.write(f'  - 스터디 {study.id}: {study.title_ko or study.title_en}')
            return
        
        # 실제 번역 실행
        translated_count = 0
        for item in studies_to_translate:
            try:
                study = item['study']
                fields = item['fields']
                source_lang = item.get('source_lang', 'ko')
                target_lang = item.get('target_lang', 'en')
                
                # target_lang에 따라 적절한 번역 메서드 선택
                if target_lang == 'en':
                    translated_dict = TranslationManager.translate_bulk_to_english(fields)
                elif target_lang == 'ko':
                    translated_dict = TranslationManager.translate_bulk_to_korean(fields)
                elif target_lang == 'es':
                    translated_dict = TranslationManager.translate_bulk_to_spanish(fields)
                elif target_lang == 'zh':
                    translated_dict = TranslationManager.translate_bulk_to_chinese(fields)
                elif target_lang == 'ja':
                    translated_dict = TranslationManager.translate_bulk_to_japanese(fields)
                else:
                    # 기본적으로 영어로 번역
                    translated_dict = TranslationManager.translate_bulk_to_english(fields)
                
                target_title_field = f'title_{target_lang}'
                target_goal_field = f'goal_{target_lang}'
                
                if 'title' in translated_dict and hasattr(study, target_title_field):
                    setattr(study, target_title_field, translated_dict['title'])
                if 'goal' in translated_dict and hasattr(study, target_goal_field):
                    setattr(study, target_goal_field, translated_dict['goal'])
                
                study.save()
                translated_count += 1
                self.stdout.write(f'  ✅ 스터디 {study.id} 번역 완료 ({source_lang} → {target_lang})')
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ 스터디 {item["study"].id} 번역 실패: {str(e)}'))
        
        self.stdout.write(f'📚 스터디 번역 완료: {translated_count}/{len(studies_to_translate)}개')
    
    def translate_exams(self, direction, dry_run, limit):
        """시험 콘텐츠 번역"""
        from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES, BASE_LANGUAGE
        
        self.stdout.write('📝 시험 번역 시작...')
        
        # 번역이 필요한 시험 조회
        exams_to_translate = []
        
        if direction == 'all':
            # 모든 언어 쌍에 대해 번역
            for source_lang in SUPPORTED_LANGUAGES:
                for target_lang in SUPPORTED_LANGUAGES:
                    if source_lang == target_lang:
                        continue
                    
                    source_title_field = f'title_{source_lang}'
                    source_description_field = f'description_{source_lang}'
                    target_title_field = f'title_{target_lang}'
                    
                    if not hasattr(Exam, source_title_field) or not hasattr(Exam, target_title_field):
                        continue
                    
                    exams = Exam.objects.filter(
                        **{f'{source_title_field}__isnull': False, f'{source_title_field}__gt': ''}
                    ).filter(
                        **{f'{target_title_field}__isnull': True}
                    ).exclude(**{f'{target_title_field}__gt': ''})
                    
                    for exam in exams:
                        exams_to_translate.append({
                            'exam': exam,
                            'fields': {
                                'title': getattr(exam, source_title_field, ''),
                                'description': getattr(exam, source_description_field, '') or ''
                            },
                            'source_lang': source_lang,
                            'target_lang': target_lang
                        })
        else:
            # 기존 방식 유지 (하위 호환성)
            if direction in ['ko_to_en', 'both']:
                ko_exams = Exam.objects.filter(
                    title_ko__isnull=False,
                    title_ko__gt='',
                    title_en__isnull=True
                ).exclude(title_en__gt='')
                
                for exam in ko_exams:
                    exams_to_translate.append({
                        'exam': exam,
                        'fields': {'title': exam.title_ko, 'description': exam.description_ko or ''},
                        'source_lang': 'ko',
                        'target_lang': 'en'
                    })
            
            if direction in ['en_to_ko', 'both']:
                en_exams = Exam.objects.filter(
                    title_en__isnull=False,
                    title_en__gt='',
                    title_ko__isnull=True
                ).exclude(title_ko__gt='')
                
                for exam in en_exams:
                    exams_to_translate.append({
                        'exam': exam,
                        'fields': {'title': exam.title_en, 'description': exam.description_en or ''},
                        'source_lang': 'en',
                        'target_lang': 'ko'
                    })
        
        if limit:
            exams_to_translate = exams_to_translate[:limit]
        
        self.stdout.write(f'📊 번역이 필요한 시험: {len(exams_to_translate)}개')
        
        if dry_run:
            for item in exams_to_translate:
                exam = item['exam']
                self.stdout.write(f'  - 시험 {exam.id}: {exam.title_ko or exam.title_en}')
            return
        
        # 실제 번역 실행
        translated_count = 0
        for item in exams_to_translate:
            try:
                exam = item['exam']
                fields = item['fields']
                source_lang = item.get('source_lang', 'ko')
                target_lang = item.get('target_lang', 'en')
                
                # target_lang에 따라 적절한 번역 메서드 선택
                if target_lang == 'en':
                    translated_dict = TranslationManager.translate_bulk_to_english(fields)
                elif target_lang == 'ko':
                    translated_dict = TranslationManager.translate_bulk_to_korean(fields)
                elif target_lang == 'es':
                    translated_dict = TranslationManager.translate_bulk_to_spanish(fields)
                elif target_lang == 'zh':
                    translated_dict = TranslationManager.translate_bulk_to_chinese(fields)
                elif target_lang == 'ja':
                    translated_dict = TranslationManager.translate_bulk_to_japanese(fields)
                else:
                    translated_dict = TranslationManager.translate_bulk_to_english(fields)
                
                target_title_field = f'title_{target_lang}'
                target_description_field = f'description_{target_lang}'
                
                if 'title' in translated_dict and hasattr(exam, target_title_field):
                    setattr(exam, target_title_field, translated_dict['title'])
                if 'description' in translated_dict and hasattr(exam, target_description_field):
                    setattr(exam, target_description_field, translated_dict['description'])
                
                exam.save()
                translated_count += 1
                self.stdout.write(f'  ✅ 시험 {exam.id} 번역 완료 ({source_lang} → {target_lang})')
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ 시험 {item["exam"].id} 번역 실패: {str(e)}'))
        
        self.stdout.write(f'📝 시험 번역 완료: {translated_count}/{len(exams_to_translate)}개')
    
    def translate_questions(self, direction, dry_run, limit):
        """문제 콘텐츠 번역"""
        from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES, BASE_LANGUAGE
        
        self.stdout.write('❓ 문제 번역 시작...')
        
        # 번역이 필요한 문제 조회
        questions_to_translate = []
        
        if direction == 'all':
            # 모든 언어 쌍에 대해 번역
            for source_lang in SUPPORTED_LANGUAGES:
                for target_lang in SUPPORTED_LANGUAGES:
                    if source_lang == target_lang:
                        continue
                    
                    source_title_field = f'title_{source_lang}'
                    source_explanation_field = f'explanation_{source_lang}'
                    target_title_field = f'title_{target_lang}'
                    
                    if not hasattr(Question, source_title_field) or not hasattr(Question, target_title_field):
                        continue
                    
                    questions = Question.objects.filter(
                        **{f'{source_title_field}__isnull': False, f'{source_title_field}__gt': ''}
                    ).filter(
                        **{f'{target_title_field}__isnull': True}
                    ).exclude(**{f'{target_title_field}__gt': ''})
                    
                    for question in questions:
                        questions_to_translate.append({
                            'question': question,
                            'fields': {
                                'title': getattr(question, source_title_field, ''),
                                'explanation': getattr(question, source_explanation_field, '') or ''
                            },
                            'source_lang': source_lang,
                            'target_lang': target_lang
                        })
        else:
            # 기존 방식 유지 (하위 호환성)
            if direction in ['ko_to_en', 'both']:
                ko_questions = Question.objects.filter(
                    title_ko__isnull=False,
                    title_ko__gt='',
                    title_en__isnull=True
                ).exclude(title_en__gt='')
                
                for question in ko_questions:
                    questions_to_translate.append({
                        'question': question,
                        'fields': {'title': question.title_ko, 'explanation': question.explanation_ko or ''},
                        'source_lang': 'ko',
                        'target_lang': 'en'
                    })
            
            if direction in ['en_to_ko', 'both']:
                en_questions = Question.objects.filter(
                    title_en__isnull=False,
                    title_en__gt='',
                    title_ko__isnull=True
                ).exclude(title_ko__gt='')
                
                for question in en_questions:
                    questions_to_translate.append({
                        'question': question,
                        'fields': {'title': question.title_en, 'explanation': question.explanation_en or ''},
                        'source_lang': 'en',
                        'target_lang': 'ko'
                    })
        
        if limit:
            questions_to_translate = questions_to_translate[:limit]
        
        self.stdout.write(f'📊 번역이 필요한 문제: {len(questions_to_translate)}개')
        
        if dry_run:
            for item in questions_to_translate:
                question = item['question']
                self.stdout.write(f'  - 문제 {question.id}: {question.title_ko or question.title_en}')
            return
        
        # 실제 번역 실행
        translated_count = 0
        for item in questions_to_translate:
            try:
                question = item['question']
                fields = item['fields']
                source_lang = item.get('source_lang', 'ko')
                target_lang = item.get('target_lang', 'en')
                
                # target_lang에 따라 적절한 번역 메서드 선택
                if target_lang == 'en':
                    translated_dict = TranslationManager.translate_bulk_to_english(fields)
                elif target_lang == 'ko':
                    translated_dict = TranslationManager.translate_bulk_to_korean(fields)
                elif target_lang == 'es':
                    translated_dict = TranslationManager.translate_bulk_to_spanish(fields)
                elif target_lang == 'zh':
                    translated_dict = TranslationManager.translate_bulk_to_chinese(fields)
                elif target_lang == 'ja':
                    translated_dict = TranslationManager.translate_bulk_to_japanese(fields)
                else:
                    translated_dict = TranslationManager.translate_bulk_to_english(fields)
                
                target_title_field = f'title_{target_lang}'
                target_explanation_field = f'explanation_{target_lang}'
                
                if 'title' in translated_dict and hasattr(question, target_title_field):
                    setattr(question, target_title_field, translated_dict['title'])
                if 'explanation' in translated_dict and hasattr(question, target_explanation_field):
                    setattr(question, target_explanation_field, translated_dict['explanation'])
                
                question.save()
                translated_count += 1
                self.stdout.write(f'  ✅ 문제 {question.id} 번역 완료 ({source_lang} → {target_lang})')
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ 문제 {item["question"].id} 번역 실패: {str(e)}'))
        
        self.stdout.write(f'❓ 문제 번역 완료: {translated_count}/{len(questions_to_translate)}개')
