#!/usr/bin/env python
import os
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
django.setup()

from quiz.models import Study, StudyTask, StudyTaskProgress
from django.contrib.auth import get_user_model

User = get_user_model()

print("=== 현재 진행률 확인 ===")

# 사용자 정보
try:
    user = User.objects.get(username='doohee323')
    print(f"사용자: {user.username}")
except User.DoesNotExist:
    print("사용자를 찾을 수 없습니다.")
    exit(1)

# 스터디 정보
try:
    study = Study.objects.get(id=6)
    print(f"스터디: {study.title}")
except Study.DoesNotExist:
    print("스터디를 찾을 수 없습니다.")
    exit(1)

# StudyTaskProgress 확인
print(f"\n=== StudyTaskProgress 현황 ===")
progress_records = StudyTaskProgress.objects.filter(user=user, study_task__study=study)

for record in progress_records:
            task_name = record.study_task.name_ko or record.study_task.name_en or f'Task {record.study_task.seq}'
        print(f"- {task_name}: {record.progress}%")
    print(f"  - Task ID: {record.study_task.id}")
    print(f"  - 업데이트 시간: {record.updated_at}")

# 전체 진행률 계산
if progress_records.count() > 0:
    total_progress = sum([record.progress for record in progress_records])
    overall_progress = total_progress / progress_records.count()
    print(f"\n=== 전체 진행률 계산 ===")
    print(f"총 Task 수: {progress_records.count()}")
    print(f"진행률 합계: {total_progress}%")
    print(f"평균 진행률: {overall_progress}%")
else:
    print("\n진행률 기록이 없습니다.")

# StudyTask 기본값 확인
print(f"\n=== StudyTask 기본값 확인 ===")
tasks = StudyTask.objects.filter(study=study)
for task in tasks:
            task_name = task.name_ko or task.name_en or f'Task {task.seq}'
        print(f"- {task_name}:")
    print(f"  - progress: {task.progress}%")
    print(f"  - effective_progress: {task.effective_progress}%") 