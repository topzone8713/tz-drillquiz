#!/usr/bin/env python
"""
StudyTask의 seq 필드 수정 스크립트

이 스크립트는 기존 StudyTask 데이터에 대해 seq 값을 설정합니다.
프로덕션 환경에서 실행하기 전에 반드시 백업을 수행하세요.
"""

import os
import sys
import django

# Django 설정 로드
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
django.setup()

from django.db import connection, transaction
from quiz.models import StudyTask, Study


def fix_studytask_seq():
    """StudyTask의 seq 필드를 수정합니다."""
    print("=== StudyTask seq 필드 수정 시작 ===")
    
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


def verify_studytask_seq():
    """StudyTask의 seq 필드 상태를 확인합니다."""
    print("\n=== StudyTask seq 필드 상태 확인 ===")
    
    try:
        # seq가 0인 태스크 확인
        tasks_with_zero_seq = StudyTask.objects.filter(seq=0)
        if tasks_with_zero_seq.exists():
            print(f"⚠️  seq가 0인 태스크가 {tasks_with_zero_seq.count()}개 있습니다:")
            for task in tasks_with_zero_seq[:10]:  # 처음 10개만 표시
                task_name = task.name_ko or task.name_en or f'Task {task.seq}'
        print(f"  - {task.study.title} > {task_name} (ID: {task.id})")
            if tasks_with_zero_seq.count() > 10:
                print(f"  ... 및 {tasks_with_zero_seq.count() - 10}개 더")
        else:
            print("✅ 모든 태스크의 seq가 0보다 큽니다.")
        
        # 중복된 seq 확인
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT study_id, seq, COUNT(*) as count
                FROM quiz_studytask 
                WHERE seq > 0 
                GROUP BY study_id, seq 
                HAVING COUNT(*) > 1
                ORDER BY study_id, seq
            """)
            
            duplicates = cursor.fetchall()
            if duplicates:
                print(f"⚠️  중복된 seq가 {len(duplicates)}개 있습니다:")
                for study_id, seq, count in duplicates:
                    print(f"  - 스터디 ID {study_id}, seq {seq}: {count}개")
            else:
                print("✅ 중복된 seq가 없습니다.")
                
    except Exception as e:
        print(f"❌ 확인 중 오류 발생: {str(e)}")


if __name__ == "__main__":
    print("StudyTask seq 필드 수정 스크립트")
    print("=" * 50)
    
    # 현재 상태 확인
    verify_studytask_seq()
    
    # 사용자 확인
    response = input("\n계속 진행하시겠습니까? (y/N): ")
    if response.lower() in ['y', 'yes']:
        fix_studytask_seq()
        print("\n수정 후 상태 확인:")
        verify_studytask_seq()
    else:
        print("작업이 취소되었습니다.")
