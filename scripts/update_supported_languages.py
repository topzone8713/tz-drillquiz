#!/usr/bin/env python3
"""
기존 데이터의 supported_languages 필드를 업데이트하는 스크립트

사용법:
    python manage.py shell < scripts/update_supported_languages.py
    또는
    python scripts/update_supported_languages.py
"""

import os
import sys
import django

# Django 설정 로드
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
django.setup()

from quiz.models import Exam, Study, StudyTask
from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES

def update_supported_languages():
    """기존 데이터의 supported_languages 필드를 업데이트합니다."""
    
    print("=" * 60)
    print("지원 언어 필드 업데이트 시작")
    print("=" * 60)
    
    # Exam 업데이트
    print("\n[Exam] 지원 언어 업데이트 중...")
    exam_count = 0
    for exam in Exam.objects.all():
        supported = []
        # 모든 지원 언어의 완성도 필드를 동적으로 확인
        for lang in SUPPORTED_LANGUAGES:
            completion_field = f'is_{lang}_complete'
            if hasattr(exam, completion_field) and getattr(exam, completion_field, False):
                supported.append(lang)
        if not supported:
            supported.append(exam.created_language)
        
        new_supported = ','.join(supported)
        if exam.supported_languages != new_supported:
            exam.supported_languages = new_supported
            exam.save(update_fields=['supported_languages'])
            exam_count += 1
            if exam_count <= 5:  # 처음 5개만 출력
                print(f"  - {exam.title_ko or exam.title_en or '제목 없음'}: {exam.supported_languages}")
    print(f"✅ Exam {exam_count}개 업데이트 완료")
    
    # Study 업데이트
    print("\n[Study] 지원 언어 업데이트 중...")
    study_count = 0
    for study in Study.objects.all():
        supported = []
        # 모든 지원 언어의 완성도 필드를 동적으로 확인
        for lang in SUPPORTED_LANGUAGES:
            completion_field = f'is_{lang}_complete'
            if hasattr(study, completion_field) and getattr(study, completion_field, False):
                supported.append(lang)
        if not supported:
            supported.append(study.created_language)
        
        new_supported = ','.join(supported)
        if study.supported_languages != new_supported:
            study.supported_languages = new_supported
            study.save(update_fields=['supported_languages'])
            study_count += 1
            if study_count <= 5:  # 처음 5개만 출력
                print(f"  - {study.title_ko or study.title_en or '제목 없음'}: {study.supported_languages}")
    print(f"✅ Study {study_count}개 업데이트 완료")
    
    # StudyTask 업데이트
    print("\n[StudyTask] 지원 언어 업데이트 중...")
    task_count = 0
    for task in StudyTask.objects.all():
        supported = []
        # StudyTask는 name_ko와 name_en만 지원하므로, 해당 완성도 필드만 확인
        # 모든 지원 언어를 확인하되, 실제로 존재하는 필드만 처리
        for lang in SUPPORTED_LANGUAGES:
            completion_field = f'is_{lang}_complete'
            if hasattr(task, completion_field) and getattr(task, completion_field, False):
                supported.append(lang)
        if not supported:
            supported.append(task.created_language)
        
        new_supported = ','.join(supported)
        if task.supported_languages != new_supported:
            task.supported_languages = new_supported
            task.save(update_fields=['supported_languages'])
            task_count += 1
            if task_count <= 5:  # 처음 5개만 출력
                print(f"  - {task.name_ko or task.name_en or '이름 없음'}: {task.supported_languages}")
    print(f"✅ StudyTask {task_count}개 업데이트 완료")
    
    print("\n" + "=" * 60)
    print("지원 언어 필드 업데이트 완료")
    print("=" * 60)
    print(f"\n총 업데이트:")
    print(f"  - Exam: {exam_count}개")
    print(f"  - Study: {study_count}개")
    print(f"  - StudyTask: {task_count}개")

if __name__ == '__main__':
    update_supported_languages()







