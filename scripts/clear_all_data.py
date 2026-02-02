#!/usr/bin/env python
"""
데이터베이스의 모든 데이터를 정리하는 스크립트
사용법: python scripts/clear_all_data.py
"""

import os
import sys
import django

# Django 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
django.setup()

from django.contrib.auth import get_user_model
from quiz.models import (
    Question, Exam, Study, StudyTask, Member,
    ExamResult, ExamResultDetail, StudyTaskProgress, 
    StudyProgressRecord, IgnoredQuestion, StudyJoinRequest,
    AccuracyAdjustmentHistory, ExamSubscription
)

def clear_all_data():
    """데이터베이스의 모든 데이터를 정리합니다."""
    
    print("=== 데이터베이스 정리 시작 ===")
    
    # 1. 통계 및 관련 데이터 삭제
    print("1. 통계 및 관련 데이터 삭제 중...")
    
    print("   - 시험 결과 상세 삭제 중...")
    ExamResultDetail.objects.all().delete()
    
    print("   - 시험 결과 삭제 중...")
    ExamResult.objects.all().delete()
    
    print("   - 태스크 진행율 삭제 중...")
    StudyTaskProgress.objects.all().delete()
    
    print("   - 스터디 진행 기록 삭제 중...")
    StudyProgressRecord.objects.all().delete()
    
    print("   - 무시된 문제 삭제 중...")
    IgnoredQuestion.objects.all().delete()
    
    print("   - 스터디 가입 요청 삭제 중...")
    StudyJoinRequest.objects.all().delete()
    
    print("   - 정확도 조정 이력 삭제 중...")
    AccuracyAdjustmentHistory.objects.all().delete()
    
    print("   - 시험 구독 삭제 중...")
    ExamSubscription.objects.all().delete()
    
    # 2. 멤버 정보 삭제
    print("2. 멤버 정보 삭제 중...")
    Member.objects.all().delete()
    
    # 3. 태스크 삭제
    print("3. 태스크 삭제 중...")
    StudyTask.objects.all().delete()
    
    # 4. 스터디 삭제
    print("4. 스터디 삭제 중...")
    Study.objects.all().delete()
    
    # 5. 시험 삭제
    print("5. 시험 삭제 중...")
    Exam.objects.all().delete()
    
    # 6. 문제 삭제
    print("6. 문제 삭제 중...")
    Question.objects.all().delete()
    
    # 7. 사용자 삭제
    print("7. 사용자 삭제 중...")
    User = get_user_model()
    User.objects.all().delete()
    
    print("✅ 모든 데이터 정리 완료!")
    
    # 8. 최종 상태 확인
    print("\n=== 최종 데이터베이스 상태 ===")
    print(f"사용자: {User.objects.count()}명")
    print(f"문제: {Question.objects.count()}개")
    print(f"시험: {Exam.objects.count()}개")
    print(f"스터디: {Study.objects.count()}개")
    print(f"태스크: {StudyTask.objects.count()}개")
    print(f"멤버: {Member.objects.count()}개")
    print(f"시험 결과: {ExamResult.objects.count()}개")
    print(f"시험 결과 상세: {ExamResultDetail.objects.count()}개")
    print(f"태스크 진행율: {StudyTaskProgress.objects.count()}개")
    print(f"스터디 진행 기록: {StudyProgressRecord.objects.count()}개")
    print(f"무시된 문제: {IgnoredQuestion.objects.count()}개")
    print(f"스터디 가입 요청: {StudyJoinRequest.objects.count()}개")
    print(f"정확도 조정 이력: {AccuracyAdjustmentHistory.objects.count()}개")
    print(f"시험 구독: {ExamSubscription.objects.count()}개")

if __name__ == "__main__":
    try:
        clear_all_data()
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        sys.exit(1)
