#!/usr/bin/env python
"""
로컬 SQLite StudyTask seq 필드 수정 스크립트
"""

import os
import sys
import django

# Django 설정 로드
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
django.setup()

from django.db import connection, transaction
from quiz.models import StudyTask, Study


def fix_dev_sqlite_seq():
    """로컬 SQLite의 StudyTask seq 필드를 수정합니다."""
    print("=== 로컬 SQLite StudyTask seq 필드 수정 시작 ===")
    
    try:
        with transaction.atomic():
            # 모든 스터디를 가져옴
            studies = Study.objects.all()
            
            for study in studies:
                print(f"스터디 '{study.title}' (ID: {study.id}) 처리 중...")
                
                # 해당 스터디의 모든 태스크를 가져와서 seq 순서대로 정렬
                tasks = StudyTask.objects.filter(study=study).order_by('id')
                
                for index, task in enumerate(tasks, 1):
                    old_seq = task.seq
                    task.seq = index
                    task.save(update_fields=['seq'])
                    task_name = task.name_ko or task.name_en or f'Task {task.seq}'
                    print(f"  - 태스크 '{task_name}' (ID: {task.id}): seq {old_seq} -> {index}")
                
                print(f"  ✅ 스터디 '{study.title}' 완료: {tasks.count()}개 태스크 처리")
            
            print("\n=== 모든 스터디 처리 완료 ===")
            
            # 결과 확인
            total_tasks = StudyTask.objects.count()
            tasks_with_seq = StudyTask.objects.filter(seq__gt=0).count()
            print(f"총 태스크 수: {total_tasks}")
            print(f"seq가 설정된 태스크 수: {tasks_with_seq}")
            
            if total_tasks == tasks_with_seq:
                print("✅ 모든 태스크의 seq가 올바르게 설정되었습니다.")
            else:
                print("⚠️  일부 태스크의 seq가 설정되지 않았습니다.")
                
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        raise


if __name__ == "__main__":
    print("로컬 SQLite StudyTask seq 필드 수정 스크립트")
    print("=" * 50)
    
    # 현재 상태 확인
    from quiz.models import StudyTask
    total_count = StudyTask.objects.count()
    zero_seq_count = StudyTask.objects.filter(seq=0).count()
    
    print(f"현재 상태:")
    print(f"  총 태스크 수: {total_count}")
    print(f"  seq가 0인 태스크 수: {zero_seq_count}")
    
    if zero_seq_count == 0:
        print("✅ 이미 모든 태스크의 seq가 설정되어 있습니다.")
    else:
        # 사용자 확인
        response = input(f"\n{zero_seq_count}개 태스크의 seq를 수정하시겠습니까? (y/N): ")
        if response.lower() in ['y', 'yes']:
            fix_dev_sqlite_seq()
        else:
            print("작업이 취소되었습니다.")
