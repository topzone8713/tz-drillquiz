#!/usr/bin/env python
"""
개발 환경 StudyTask 모델 상태 확인 스크립트
"""

import os
import sys
import django

# Django 설정 로드
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
django.setup()

from quiz.models import StudyTask

def check_dev_model():
    """개발 환경의 StudyTask 모델 상태를 확인합니다."""
    print("=== 개발 환경 StudyTask 확인 ===")
    
    # 모델 필드 확인
    model_fields = [f.name for f in StudyTask._meta.get_fields() if hasattr(f, 'name')]
    print(f"모델 필드: {model_fields}")
    
    # 데이터 상태 확인
    total_count = StudyTask.objects.count()
    zero_seq_count = StudyTask.objects.filter(seq=0).count()
    
    print(f"총 레코드 수: {total_count}")
    print(f"seq가 0인 레코드 수: {zero_seq_count}")
    
    if zero_seq_count == 0:
        print("✅ 모든 태스크의 seq가 올바르게 설정되었습니다.")
    else:
        print(f"⚠️  {zero_seq_count}개 태스크의 seq가 0입니다.")
    
    # seq 값 분포 확인
    print("\nseq 값 분포:")
    for task in StudyTask.objects.all()[:5]:
        task_name = task.name_ko or task.name_en or f'Task {task.seq}'
        print(f"  - {task.study.title} > {task_name}: seq {task.seq}")
    
    if total_count > 5:
        print(f"  ... 및 {total_count - 5}개 더")

if __name__ == "__main__":
    check_dev_model()
