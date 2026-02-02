#!/usr/bin/env python3
"""
현재 데이터베이스의 통계 상태를 확인하는 스크립트
"""

import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
django.setup()

from quiz.models import ExamResult, ExamResultDetail, AccuracyAdjustmentHistory, Exam
from django.contrib.auth import get_user_model

User = get_user_model()

def check_db_status():
    """현재 데이터베이스의 통계 상태를 확인합니다."""
    print("=== 현재 데이터베이스 통계 상태 확인 ===")
    
    try:
        # 1. 전체 통계 개수 확인
        print("\n1. 전체 통계 개수:")
        result_count = ExamResult.objects.count()
        detail_count = ExamResultDetail.objects.count()
        accuracy_count = AccuracyAdjustmentHistory.objects.count()
        
        print(f"   시험 결과: {result_count}개")
        print(f"   결과 상세: {detail_count}개")
        print(f"   정확도 조정: {accuracy_count}개")
        
        # 2. 사용자별 통계 확인
        print("\n2. 사용자별 통계:")
        users = User.objects.all()
        for user in users:
            user_results = ExamResult.objects.filter(user=user).count()
            user_details = ExamResultDetail.objects.filter(result__user=user).count()
            user_accuracy = AccuracyAdjustmentHistory.objects.filter(user=user).count()
            
            if user_results > 0 or user_details > 0 or user_accuracy > 0:
                print(f"   {user.username}:")
                print(f"     - 시험 결과: {user_results}개")
                print(f"     - 결과 상세: {user_details}개")
                print(f"     - 정확도 조정: {user_accuracy}개")
        
        # 3. Public Cloud Interview 관련 시험들 확인
        print("\n3. Public Cloud Interview 관련 시험들:")
        cloud_exams = Exam.objects.filter(title__icontains="Public Cloud Interview")
        for exam in cloud_exams:
            print(f"   - {exam.title} (ID: {exam.id})")
            print(f"     원본 여부: {exam.is_original}")
            print(f"     생성자: {exam.created_by}")
            
            # 해당 시험의 결과 확인
            exam_results = ExamResult.objects.filter(exam=exam)
            print(f"     시험 결과: {exam_results.count()}개")
            
            for result in exam_results:
                print(f"       사용자: {result.user.username}, 점수: {result.score}/{result.total_score}")
        
        # 4. 최근 생성된 통계 데이터 확인
        print("\n4. 최근 생성된 통계 데이터:")
        recent_results = ExamResult.objects.order_by('-completed_at')[:5]
        if recent_results:
            print("   최근 시험 결과:")
            for result in recent_results:
                print(f"     - {result.exam.title} | {result.user.username} | {result.score}/{result.total_score} | {result.created_at}")
        else:
            print("   최근 시험 결과: 없음")
        
        recent_details = ExamResultDetail.objects.order_by('-id')[:5]
        if recent_details:
            print("   최근 결과 상세:")
            for detail in recent_details:
                print(f"     - {detail.question.title[:30]}... | {detail.result.user.username} | 정답: {detail.is_correct} | {detail.id}")
        else:
            print("   최근 결과 상세: 없음")
        
        # 5. 캐시 관련 확인
        print("\n5. 캐시 상태:")
        from django.core.cache import cache
        print(f"   Django 캐시 백엔드: {cache.__class__.__name__}")
        
        # 6. 요약
        print("\n=== 요약 ===")
        if result_count == 0 and detail_count == 0 and accuracy_count == 0:
            print("✅ 데이터베이스에 통계 데이터가 없습니다.")
            print("⚠️  프론트엔드에서 표시되는 점수는 캐시된 데이터일 가능성이 높습니다.")
        else:
            print("⚠️  데이터베이스에 통계 데이터가 남아있습니다.")
            print(f"   총 {result_count + detail_count + accuracy_count}개의 데이터가 존재합니다.")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_db_status()
