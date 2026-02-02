#!/usr/bin/env python
"""
기존 ExamResult의 요약 필드들을 ExamResultDetail을 기반으로 재계산하는 스크립트

이 스크립트는 submit_exam 함수의 버그로 인해 요약 필드들이 제대로 업데이트되지 않은
ExamResult들을 수정합니다.
"""

import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
django.setup()

from quiz.models import ExamResult, ExamResultDetail
from django.db import transaction

def fix_exam_result_summaries():
    """모든 ExamResult의 요약 필드들을 ExamResultDetail을 기반으로 재계산"""
    
    print("🔧 ExamResult 요약 필드 수정 시작...")
    
    # 모든 ExamResult 조회
    exam_results = ExamResult.objects.all()
    fixed_count = 0
    
    for result in exam_results:
        try:
            # 해당 결과의 모든 ExamResultDetail 조회
            details = ExamResultDetail.objects.filter(result=result)
            
            if details.exists():
                # 요약 필드들 재계산
                correct_count = details.filter(is_correct=True).count()
                total_score = details.count()
                wrong_count = total_score - correct_count
                score = correct_count
                
                # 기존 값과 다른 경우에만 업데이트
                if (result.correct_count != correct_count or 
                    result.total_score != total_score or 
                    result.wrong_count != wrong_count or 
                    result.score != score):
                    
                    print(f"📝 수정: {result.exam.title} (사용자: {result.user.username if result.user else 'Anonymous'})")
                    print(f"   기존: 정답 {result.correct_count}/{result.total_score}, 점수 {result.score}")
                    print(f"   수정: 정답 {correct_count}/{total_score}, 점수 {score}")
                    
                    # 요약 필드들 업데이트
                    result.correct_count = correct_count
                    result.total_score = total_score
                    result.wrong_count = wrong_count
                    result.score = score
                    result.save()
                    
                    fixed_count += 1
                    
        except Exception as e:
            print(f"❌ 오류 발생 (ExamResult ID: {result.id}): {str(e)}")
            continue
    
    print(f"\n✅ 수정 완료: {fixed_count}개의 ExamResult 요약 필드 수정됨")
    
    # 수정된 결과 확인
    print("\n📊 수정된 결과 확인:")
    for result in ExamResult.objects.all():
        details = ExamResultDetail.objects.filter(result=result)
        if details.exists():
            correct_count = details.filter(is_correct=True).count()
            total_score = details.count()
            print(f"  {result.exam.title} (사용자: {result.user.username if result.user else 'Anonymous'}): "
                  f"정답 {correct_count}/{total_score}, 점수 {result.score}")

if __name__ == "__main__":
    try:
        with transaction.atomic():
            fix_exam_result_summaries()
        print("\n🎉 모든 수정이 성공적으로 완료되었습니다!")
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        sys.exit(1)

