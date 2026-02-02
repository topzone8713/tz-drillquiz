#!/usr/bin/env python3
"""
사용자 진행률 데이터 확인 스크립트
"""

import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
django.setup()

from quiz.models import StudyTask, Study, StudyTaskProgress
from django.contrib.auth import get_user_model

User = get_user_model()

def check_user_progress(username):
    """사용자의 진행률 데이터를 확인합니다."""
    print(f"=== {username} 사용자 진행률 데이터 확인 ===")
    
    try:
        user = User.objects.get(username=username)
        print(f"✅ 사용자 {username} 확인됨 (ID: {user.id})")
    except User.DoesNotExist:
        print(f"❌ 사용자 {username}을 찾을 수 없습니다.")
        return
    
    # 참여한 스터디 확인
    studies = Study.objects.filter(members__user=user)
    print(f"\n참여한 스터디 수: {studies.count()}개")
    
    total_progress = 0
    for study in studies:
        print(f"\n스터디: {study.title}")
        tasks = StudyTask.objects.filter(study=study)
        study_progress = 0
        
        for task in tasks:
            task_name = task.name_ko or task.name_en or f'Task {task.seq}'
        print(f"  - 태스크: {task_name}, progress: {task.progress}")
            study_progress += task.progress
        
        print(f"  스터디 총 progress: {study_progress}")
        total_progress += study_progress
    
    print(f"\n=== 전체 요약 ===")
    print(f"전체 총 progress: {total_progress}")
    
    # StudyTaskProgress 확인
    task_progress_records = StudyTaskProgress.objects.filter(user=user)
    print(f"StudyTaskProgress 레코드 수: {task_progress_records.count()}개")
    
    if task_progress_records.exists():
        print("StudyTaskProgress 상세:")
        for record in task_progress_records:
            print(f"  - {record.study_task.title}: {record.progress}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        username = "doohee323"
    
    check_user_progress(username)
