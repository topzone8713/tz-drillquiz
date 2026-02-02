#!/usr/bin/env python
import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
django.setup()

from quiz.models import Study, Exam, ExamResult, ExamResultDetail
from django.contrib.auth.models import User

def check_study_progress():
    """스터디 진행률 확인"""
    print("=== 스터디 진행률 디버깅 ===")
    
    # 스터디 ID 20 확인
    try:
        study = Study.objects.get(id=20)
        print(f"스터디: {study.title}")
        print(f"태스크 수: {study.tasks.count()}")
        
        for task in study.tasks.all():
            task_name = task.name_ko or task.name_en or f'Task {task.seq}'
        print(f"\n태스크: {task_name}")
            if task.exam:
                print(f"  연결된 시험: {task.exam.title}")
                print(f"  시험 문제 수: {task.exam.total_questions}")
                
                # 사용자 확인 (첫 번째 사용자 사용)
                user = User.objects.first()
                if user:
                    print(f"  사용자: {user.username}")
                    
                    # 맞춘 문제 수
                    correct_count = task.exam.get_total_correct_questions_for_user(user)
                    print(f"  맞춘 문제 수: {correct_count}")
                    
                    # 시도한 문제 수
                    attempted_count = task.exam.get_total_attempted_questions_for_user(user)
                    print(f"  시도한 문제 수: {attempted_count}")
                    
                    # 진행률 계산
                    if task.exam.total_questions > 0:
                        correct_progress = (correct_count / task.exam.total_questions) * 100
                        attempted_progress = (attempted_count / task.exam.total_questions) * 100
                        print(f"  맞춘 진행률: {correct_progress:.1f}%")
                        print(f"  시도한 진행률: {attempted_progress:.1f}%")
            else:
                print("  연결된 시험 없음")
        
        # 전체 진행률 계산
        total_correct = 0
        total_attempted = 0
        total_questions = 0
        
        for task in study.tasks.all():
            if task.exam:
                user = User.objects.first()
                if user:
                    correct_count = task.exam.get_total_correct_questions_for_user(user)
                    attempted_count = task.exam.get_total_attempted_questions_for_user(user)
                    question_count = task.exam.total_questions
                    
                    total_correct += correct_count
                    total_attempted += attempted_count
                    total_questions += question_count
        
        if total_questions > 0:
            overall_correct = (total_correct / total_questions) * 100
            overall_attempted = (total_attempted / total_questions) * 100
            print(f"\n=== 전체 진행률 ===")
            print(f"맞춘 진행률: {overall_correct:.1f}%")
            print(f"시도한 진행률: {overall_attempted:.1f}%")
        
    except Study.DoesNotExist:
        print("스터디 ID 20을 찾을 수 없습니다.")
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    check_study_progress()
