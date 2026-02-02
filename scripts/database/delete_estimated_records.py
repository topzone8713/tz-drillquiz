#!/usr/bin/env python
import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
django.setup()

from quiz.models import ExamResult, ExamResultDetail
from django.db import transaction

def delete_estimated_records():
    """elapsed_seconds가 0인 추정된 기록들을 삭제합니다."""
    
    # elapsed_seconds가 0인 ExamResultDetail 찾기
    zero_time_details = ExamResultDetail.objects.filter(elapsed_seconds=0)
    print(f"elapsed_seconds가 0인 상세 기록: {zero_time_details.count()}개")
    
    # 해당 ExamResult들 찾기
    result_ids = zero_time_details.values_list('result_id', flat=True).distinct()
    zero_time_results = ExamResult.objects.filter(id__in=result_ids)
    print(f"관련된 시험 결과: {zero_time_results.count()}개")
    
    # 삭제할 데이터 미리보기
    for result in zero_time_results[:5]:
        details = result.examresultdetail_set.all()
        zero_count = details.filter(elapsed_seconds=0).count()
        total_count = details.count()
        print(f"  시험 결과 {result.id}: {total_count}개 중 {zero_count}개가 0초")
    
    # 사용자 확인
    confirm = input("\n이 기록들을 삭제하시겠습니까? (y/N): ")
    if confirm.lower() != 'y':
        print("삭제가 취소되었습니다.")
        return
    
    # 삭제 실행
    with transaction.atomic():
        deleted_results = zero_time_results.delete()
        print(f"\n삭제 완료:")
        print(f"  ExamResult: {deleted_results[0]}개")
        print(f"  ExamResultDetail: {deleted_results[1].get('quiz.ExamResultDetail', 0)}개")
        
        # 남은 데이터 확인
        remaining_results = ExamResult.objects.count()
        remaining_details = ExamResultDetail.objects.count()
        print(f"\n남은 데이터:")
        print(f"  ExamResult: {remaining_results}개")
        print(f"  ExamResultDetail: {remaining_details}개")

if __name__ == "__main__":
    delete_estimated_records() 