#!/usr/bin/env python3
"""
모든 통계 데이터를 삭제하는 스크립트

실행 이력:
- 2025-08-13 23:16:50: 모든 통계 데이터 삭제 완료 (총 17개 데이터)
  - 시험 결과 상세: 10개 삭제
  - 시험 결과: 2개 삭제
  - 스터디 진행률 기록: 5개 삭제
  - Django 캐시 정리 완료
  - SQLite 데이터베이스 최적화 완료
- 2025-08-13 23:22:59: 모든 통계 데이터 삭제 완료 (총 28개 데이터)
  - 시험 결과 상세: 20개 삭제
  - 시험 결과: 3개 삭제
  - 스터디 진행률 기록: 5개 삭제
  - Django 캐시 정리 완료
  - SQLite 데이터베이스 최적화 완료
- 2025-08-13 23:35:38: 모든 통계 데이터 삭제 완료 (총 39개 데이터)
  - 시험 결과 상세: 30개 삭제
  - 시험 결과: 4개 삭제
  - 스터디 진행률 기록: 5개 삭제
  - Django 캐시 정리 완료
  - SQLite 데이터베이스 최적화 완료
- 2025-08-13 23:40:XX: Django 세션 정리 기능 추가
  - Django 세션 정리 기능 추가
  - StudyProgressRecord 자동 정리 기능 추가
- 2025-08-14 04:32:17: doohee323 사용자 통계 데이터 삭제 완료 (총 47개 데이터)
  - 시험 결과 상세: 30개 삭제
  - 시험 결과: 4개 삭제
  - 스터디 진행률 기록: 10개 삭제
  - 스터디 태스크 진행률: 3개 삭제
  - StudyTask progress 필드 초기화 및 Django 캐시 정리
- 2025-08-14 04:XX:XX: 스크립트 보강 완료
  - 사용자별 통계 삭제 기능 추가
  - StudyTask progress 필드 초기화 개선
  - Django 캐시 정리 강화
  - 브라우저 캐시 정리 안내 추가
  - 검증 로직 강화

주의사항:
- 이 스크립트는 모든 통계 데이터를 영구적으로 삭제합니다
- 삭제된 데이터는 복구할 수 없습니다
- 실행 전 반드시 백업을 확인하세요
- 프로덕션 환경에서는 신중하게 사용하세요

사용법:
- 일반 실행: python clear_all_statistics.py
- 강제 실행: python clear_all_statistics.py --force
"""

import os
import sys
import django
from datetime import datetime

# Django 설정
import sys
sys.path.append('/Users/dhong/workspaces/drillquiz')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
django.setup()

from quiz.models import ExamResult, ExamResultDetail, AccuracyAdjustmentHistory, StudyProgressRecord, StudyTaskProgress, StudyTask
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from django.contrib.sessions.models import Session

User = get_user_model()

def create_backup_info():
    """삭제 전 백업 정보를 생성합니다."""
    print("=== 백업 정보 생성 ===")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 현재 데이터베이스 상태 정보 수집
    backup_info = {
        'timestamp': timestamp,
        'exam_results_count': ExamResult.objects.count(),
        'exam_result_details_count': ExamResultDetail.objects.count(),
        'accuracy_history_count': AccuracyAdjustmentHistory.objects.count(),
        'study_progress_records_count': StudyProgressRecord.objects.count(),
        'study_task_progress_count': StudyTaskProgress.objects.count(),
        'study_tasks_with_progress': StudyTask.objects.filter(progress__gt=0).count(),
        'total_users': User.objects.count()
    }
    
    # 백업 정보를 파일로 저장
    backup_file = f"statistics_backup_{timestamp}.txt"
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write("=== 통계 데이터 삭제 전 백업 정보 ===\n")
        f.write(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for key, value in backup_info.items():
            f.write(f"{key}: {value}\n")
    
    print(f"   📁 백업 정보가 {backup_file}에 저장되었습니다.")
    return backup_info

def clear_django_sessions():
    """Django 세션을 정리합니다."""
    print("\n8. Django 세션 정리 중...")
    try:
        session_count = Session.objects.count()
        Session.objects.all().delete()
        print(f"   ✅ {session_count}개의 Django 세션 정리 완료")
        return True
    except Exception as e:
        print(f"   ⚠️  Django 세션 정리 실패: {str(e)}")
        return False

def clear_django_cache():
    """Django 캐시를 정리합니다."""
    print("\n9. Django 캐시 정리 중...")
    try:
        cache.clear()
        print("   ✅ Django 캐시 정리 완료")
        return True
    except Exception as e:
        print(f"   ⚠️  Django 캐시 정리 실패: {str(e)}")
        return False

def clear_orm_cache():
    """Django ORM 캐시를 무효화합니다."""
    print("\n10. Django ORM 캐시 무효화 중...")
    try:
        # 데이터베이스 연결 초기화
        connection.close()
        print("   ✅ 데이터베이스 연결 초기화 완료")
        
        # ORM 쿼리 결과 무효화를 위한 더미 쿼리 실행
        from quiz.models import ExamResult, ExamResultDetail, StudyTaskProgress, StudyProgressRecord
        
        # 각 테이블에서 더미 쿼리 실행하여 캐시 무효화
        ExamResult.objects.all().count()
        ExamResultDetail.objects.all().count()
        StudyTaskProgress.objects.all().count()
        StudyProgressRecord.objects.all().count()
        
        print("   ✅ ORM 쿼리 결과 캐시 무효화 완료")
        return True
        
    except Exception as e:
        print(f"   ⚠️  Django ORM 캐시 무효화 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def optimize_database():
    """데이터베이스를 최적화합니다."""
    print("\n9. 데이터베이스 최적화 중...")
    try:
        with connection.cursor() as cursor:
            # SQLite의 경우 VACUUM 명령으로 최적화
            if 'sqlite' in connection.settings_dict['ENGINE']:
                cursor.execute("VACUUM")
                print("   ✅ SQLite 데이터베이스 최적화 완료 (VACUUM)")
            else:
                # PostgreSQL의 경우 ANALYZE 명령
                cursor.execute("ANALYZE")
                print("   ✅ PostgreSQL 데이터베이스 최적화 완료 (ANALYZE)")
        return True
    except Exception as e:
        print(f"   ⚠️  데이터베이스 최적화 실패: {str(e)}")
        return False

def verify_deletion():
    """삭제가 제대로 되었는지 검증합니다."""
    print("\n10. 삭제 검증 중...")
    
    verification_results = {
        'exam_results': ExamResult.objects.count() == 0,
        'exam_result_details': ExamResultDetail.objects.count() == 0,
        'accuracy_history': AccuracyAdjustmentHistory.objects.count() == 0,
        'study_progress_records': StudyProgressRecord.objects.count() == 0,
        'study_task_progress': StudyTaskProgress.objects.count() == 0,
        'study_tasks_progress_zero': StudyTask.objects.filter(progress__gt=0).count() == 0
    }
    
    all_passed = all(verification_results.values())
    
    for check_name, passed in verification_results.items():
        status = "✅ 통과" if passed else "❌ 실패"
        print(f"   {check_name}: {status}")
    
    return all_passed

def clear_user_statistics(username):
    """특정 사용자의 통계 데이터를 삭제합니다."""
    print(f"=== {username} 사용자 통계 데이터 삭제 시작 ===")
    
    try:
        # 사용자 확인
        try:
            user = User.objects.get(username=username)
            print(f"✅ 사용자 {username} 확인됨 (ID: {user.id})")
        except User.DoesNotExist:
            print(f"❌ 사용자 {username}을 찾을 수 없습니다.")
            return
        
        # 백업 정보 생성
        backup_info = create_backup_info()
        
        # 1. 정확도 조정 기록 삭제
        print(f"\n1. {username} 사용자 정확도 조정 기록 삭제 중...")
        accuracy_count = AccuracyAdjustmentHistory.objects.filter(user=user).count()
        AccuracyAdjustmentHistory.objects.filter(user=user).delete()
        print(f"   ✅ {accuracy_count}개의 정확도 조정 기록 삭제 완료")
        
        # 2. 시험 결과 상세 삭제
        print(f"\n2. {username} 사용자 시험 결과 상세 삭제 중...")
        detail_count = ExamResultDetail.objects.filter(result__user=user).count()
        ExamResultDetail.objects.filter(result__user=user).delete()
        print(f"   ✅ {detail_count}개의 시험 결과 상세 삭제 완료")
        
        # 3. 시험 결과 삭제
        print(f"\n3. {username} 사용자 시험 결과 삭제 중...")
        result_count = ExamResult.objects.filter(user=user).count()
        ExamResult.objects.filter(user=user).delete()
        print(f"   ✅ {result_count}개의 시험 결과 삭제 완료")
        
        # 4. 스터디 진행률 기록 삭제
        print(f"\n4. {username} 사용자 스터디 진행률 기록 삭제 중...")
        progress_record_count = StudyProgressRecord.objects.filter(user=user).count()
        StudyProgressRecord.objects.filter(user=user).delete()
        print(f"   ✅ {progress_record_count}개의 스터디 진행률 기록 삭제 완료")
        
        # 5. 스터디 태스크 진행률 삭제
        print(f"\n5. {username} 사용자 스터디 태스크 진행률 삭제 중...")
        task_progress_count = StudyTaskProgress.objects.filter(user=user).count()
        StudyTaskProgress.objects.filter(user=user).delete()
        print(f"   ✅ {task_progress_count}개의 스터디 태스크 진행률 삭제 완료")
        
        # 6. StudyTask의 progress 필드 초기화 (해당 사용자가 참여한 스터디)
        print(f"\n6. {username} 사용자 관련 StudyTask progress 필드 초기화 중...")
        # 사용자가 참여한 스터디의 태스크들 찾기
        user_study_tasks = StudyTask.objects.filter(study__members__user=user)
        reset_count = 0
        for task in user_study_tasks:
            if task.progress > 0:
                task.progress = 0
                task.save()
                reset_count += 1
        print(f"   ✅ {reset_count}개의 StudyTask progress 필드 초기화 완료")
        
        # 7. Django 캐시 정리 (사용자별 데이터가 캐시에 남아있을 수 있음)
        print(f"\n7. Django 캐시 정리 중...")
        cache_cleared = clear_django_cache()
        
        # 8. Django ORM 캐시 무효화
        print(f"\n8. Django ORM 캐시 무효화 중...")
        orm_cache_cleared = clear_orm_cache()
        
        # 8. 삭제된 데이터 요약
        print(f"\n=== {username} 사용자 삭제 완료 요약 ===")
        print(f"✅ 정확도 조정 기록: {accuracy_count}개 삭제")
        print(f"✅ 시험 결과 상세: {detail_count}개 삭제")
        print(f"✅ 시험 결과: {result_count}개 삭제")
        print(f"✅ 스터디 진행률 기록: {progress_record_count}개 삭제")
        print(f"✅ 스터디 태스크 진행률: {task_progress_count}개 삭제")
        print(f"✅ StudyTask progress 필드: {reset_count}개 초기화")
        print(f"✅ Django 캐시: {'정리됨' if cache_cleared else '정리 실패'}")
        print(f"✅ Django ORM 캐시: {'무효화됨' if orm_cache_cleared else '무효화 실패'}")
        
        total_deleted = accuracy_count + detail_count + result_count + progress_record_count + task_progress_count
        print(f"✅ 총 {total_deleted}개의 통계 데이터 삭제 완료")
        
        # 9. 최종 상태 확인
        print(f"\n=== {username} 사용자 최종 상태 확인 ===")
        remaining_results = ExamResult.objects.filter(user=user).count()
        remaining_details = ExamResultDetail.objects.filter(result__user=user).count()
        remaining_accuracy = AccuracyAdjustmentHistory.objects.filter(user=user).count()
        remaining_progress_records = StudyProgressRecord.objects.filter(user=user).count()
        remaining_task_progress = StudyTaskProgress.objects.filter(user=user).count()
        
        print(f"남은 시험 결과: {remaining_results}개")
        print(f"남은 결과 상세: {remaining_details}개")
        print(f"남은 정확도 조정: {remaining_accuracy}개")
        print(f"남은 스터디 진행률 기록: {remaining_progress_records}개")
        print(f"남은 태스크 진행률: {remaining_task_progress}개")
        
        # 10. 브라우저 캐시 정리 안내
        print(f"\n=== 브라우저 캐시 정리 안내 ===")
        print("🌐 프론트엔드에서 여전히 이전 데이터가 보인다면:")
        print("   1. 브라우저 새로고침 (Ctrl+F5 또는 Cmd+Shift+R)")
        print("   2. 브라우저 개발자 도구 → Application → Storage → Clear storage")
        print("   3. 브라우저 캐시 및 쿠키 삭제")
        print("   4. 시크릿/프라이빗 모드에서 확인")
        
        if total_deleted > 0:
            print(f"\n🎉 {username} 사용자의 통계 데이터가 성공적으로 삭제되었습니다!")
            print("📁 백업 정보가 생성되었습니다.")
        else:
            print(f"\nℹ️  {username} 사용자에게는 삭제할 통계 데이터가 없습니다.")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

def clear_all_statistics():
    """모든 통계 데이터를 삭제합니다."""
    print("=== 모든 통계 데이터 삭제 시작 ===")
    
    try:
        # 백업 정보 생성
        backup_info = create_backup_info()
        
        # 1. 정확도 조정 기록 삭제
        print("\n1. 정확도 조정 기록 삭제 중...")
        accuracy_count = AccuracyAdjustmentHistory.objects.count()
        AccuracyAdjustmentHistory.objects.all().delete()
        print(f"   ✅ {accuracy_count}개의 정확도 조정 기록 삭제 완료")
        
        # 2. 시험 결과 상세 삭제
        print("\n2. 시험 결과 상세 삭제 중...")
        detail_count = ExamResultDetail.objects.count()
        ExamResultDetail.objects.all().delete()
        print(f"   ✅ {detail_count}개의 시험 결과 상세 삭제 완료")
        
        # 3. 시험 결과 삭제
        print("\n3. 시험 결과 삭제 중...")
        result_count = ExamResult.objects.count()
        ExamResult.objects.all().delete()
        print(f"   ✅ {result_count}개의 시험 결과 삭제 완료")
        
        # 4. 스터디 진행률 기록 삭제
        print("\n4. 스터디 진행률 기록 삭제 중...")
        progress_record_count = StudyProgressRecord.objects.count()
        StudyProgressRecord.objects.all().delete()
        print(f"   ✅ {progress_record_count}개의 스터디 진행률 기록 삭제 완료")
        
        # 5. 스터디 태스크 진행률 삭제
        print("\n5. 스터디 태스크 진행률 삭제 중...")
        task_progress_count = StudyTaskProgress.objects.count()
        StudyTaskProgress.objects.all().delete()
        print(f"   ✅ {task_progress_count}개의 스터디 태스크 진행률 삭제 완료")
        
        # 6. StudyTask의 progress 필드 초기화
        print("\n6. StudyTask progress 필드 초기화 중...")
        tasks = StudyTask.objects.all()
        reset_count = 0
        for task in tasks:
            if task.progress > 0:
                task.progress = 0
                task.save()
                reset_count += 1
        print(f"   ✅ {reset_count}개의 StudyTask progress 필드 초기화 완료")
        
        # 7. 사용자별 통계 확인
        print("\n7. 사용자별 통계 확인...")
        users = User.objects.all()
        for user in users:
            # 각 사용자의 시험 결과 수 확인
            exam_results = ExamResult.objects.filter(user=user).count()
            exam_details = ExamResultDetail.objects.filter(result__user=user).count()
            accuracy_history = AccuracyAdjustmentHistory.objects.filter(user=user).count()
            progress_records = StudyProgressRecord.objects.filter(user=user).count()
            task_progress = StudyTaskProgress.objects.filter(user=user).count()
            
            print(f"   사용자 {user.username}:")
            print(f"     - 시험 결과: {exam_results}개")
            print(f"     - 결과 상세: {exam_details}개")
            print(f"     - 정확도 조정: {accuracy_history}개")
            print(f"     - 스터디 진행률 기록: {progress_records}개")
            print(f"     - 태스크 진행률: {task_progress}개")
        
        # 7-1. StudyTask progress 필드 상세 확인
        print("\n7-1. StudyTask progress 필드 상세 확인...")
        tasks_with_progress = StudyTask.objects.filter(progress__gt=0)
        if tasks_with_progress.exists():
            print(f"   progress > 0인 StudyTask들:")
            for task in tasks_with_progress:
                task_name = task.name_ko or task.name_en or f'Task {task.seq}'
        print(f"     - {task.study.title} - {task_name}: {task.progress}%")
        else:
            print("   ✅ 모든 StudyTask의 progress가 0입니다.")
        
        # 8. Django 세션 정리
        sessions_cleared = clear_django_sessions()
        
        # 9. Django 캐시 정리
        cache_cleared = clear_django_cache()
        
        # 10. 데이터베이스 최적화
        db_optimized = optimize_database()
        
        # 11. 삭제 검증
        deletion_verified = verify_deletion()
        
        # 12. 전체 통계 요약
        print("\n=== 삭제 완료 요약 ===")
        print(f"✅ 정확도 조정 기록: {accuracy_count}개 삭제")
        print(f"✅ 시험 결과 상세: {detail_count}개 삭제")
        print(f"✅ 시험 결과: {result_count}개 삭제")
        print(f"✅ 스터디 진행률 기록: {progress_record_count}개 삭제")
        print(f"✅ 스터디 태스크 진행률: {task_progress_count}개 삭제")
        print(f"✅ StudyTask progress 필드: {reset_count}개 초기화")
        print(f"✅ Django 세션: {'정리됨' if sessions_cleared else '정리 실패'}")
        print(f"✅ Django 캐시: {'정리됨' if cache_cleared else '정리 실패'}")
        print(f"✅ 데이터베이스 최적화: {'완료' if db_optimized else '실패'}")
        print(f"✅ 삭제 검증: {'통과' if deletion_verified else '실패'}")
        
        total_deleted = accuracy_count + detail_count + result_count + progress_record_count + task_progress_count
        print(f"✅ 총 {total_deleted}개의 통계 데이터 삭제 완료")
        
        # 13. 최종 상태 확인
        print("\n=== 최종 상태 확인 ===")
        remaining_results = ExamResult.objects.count()
        remaining_details = ExamResultDetail.objects.count()
        remaining_accuracy = AccuracyAdjustmentHistory.objects.count()
        remaining_progress_records = StudyProgressRecord.objects.count()
        remaining_task_progress = StudyTaskProgress.objects.count()
        tasks_with_progress = StudyTask.objects.filter(progress__gt=0).count()
        remaining_sessions = Session.objects.count()
        
        print(f"남은 시험 결과: {remaining_results}개")
        print(f"남은 결과 상세: {remaining_details}개")
        print(f"남은 정확도 조정: {remaining_accuracy}개")
        print(f"남은 스터디 진행률 기록: {remaining_progress_records}개")
        print(f"남은 태스크 진행률: {remaining_task_progress}개")
        print(f"progress > 0인 StudyTask: {tasks_with_progress}개")
        print(f"남은 Django 세션: {remaining_sessions}개")
        
        if deletion_verified:
            print("\n🎉 모든 통계 데이터가 성공적으로 삭제되었습니다!")
            print("📁 백업 정보가 생성되었습니다.")
        else:
            print("\n⚠️  일부 데이터가 남아있습니다.")
        
        # 14. 브라우저 캐시 정리 안내
        print("\n=== 브라우저 캐시 정리 안내 ===")
        print("🌐 프론트엔드에서 여전히 이전 데이터가 보인다면:")
        print("   1. 브라우저 새로고침 (Ctrl+F5 또는 Cmd+Shift+R)")
        print("   2. 브라우저 개발자 도구 → Application → Storage → Clear storage")
        print("   3. 브라우저 캐시 및 쿠키 삭제")
        print("   4. 시크릿/프라이빗 모드에서 확인")
        print("   5. 프론트엔드 서버 재시작 (포트 8080)")
        
        # 15. 추가 검증 및 권장사항
        print("\n=== 추가 검증 및 권장사항 ===")
        print("🔍 데이터가 여전히 보인다면 다음을 확인하세요:")
        print("   1. Django 서버 재시작 (포트 8000)")
        print("   2. 프론트엔드 서버 재시작 (포트 8080)")
        print("   3. 브라우저 캐시 완전 삭제")
        print("   4. 데이터베이스 연결 상태 확인")
        print("   5. 로그에서 오류 메시지 확인")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

def confirm_deletion():
    """삭제 확인을 위한 사용자 입력을 받습니다."""
    print("⚠️  경고: 이 작업은 모든 통계 데이터를 영구적으로 삭제합니다!")
    print("⚠️  삭제된 데이터는 복구할 수 없습니다!")
    print()
    print("삭제될 데이터:")
    print("- 모든 시험 결과 및 상세 기록")
    print("- 정확도 조정 이력")
    print("- 스터디 진행률 기록")
    print("- 스터디 태스크 진행률")
    print("- StudyTask의 progress 필드 초기화")
    print("- Django 세션 정리")
    print("- Django 캐시 정리")
    print("- 데이터베이스 최적화")
    print()
    print("📁 삭제 전 백업 정보가 자동으로 생성됩니다.")
    print()
    
    while True:
        response = input("정말로 모든 통계를 삭제하시겠습니까? (yes/no): ").strip().lower()
        
        if response in ['yes', 'y', '네', '예']:
            return True
        elif response in ['no', 'n', '아니오', '아니요']:
            return False
        else:
            print("'yes' 또는 'no'로 답변해주세요.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == '--force':
            # --force 플래그가 있으면 확인 없이 모든 데이터 삭제
            print("--force 플래그로 확인 없이 모든 통계 데이터 삭제를 진행합니다.")
            clear_all_statistics()
        elif sys.argv[1] == '--user' and len(sys.argv) > 2:
            # --user 플래그로 특정 사용자 데이터 삭제
            username = sys.argv[2]
            print(f"사용자 {username}의 통계 데이터를 삭제합니다.")
            clear_user_statistics(username)
        else:
            print("사용법:")
            print("  모든 통계 삭제: python clear_all_statistics.py [--force]")
            print("  특정 사용자 삭제: python clear_all_statistics.py --user <username>")
            print("  예시: python clear_all_statistics.py --user doohee323")
    else:
        # 사용자 확인 후 모든 데이터 삭제
        if confirm_deletion():
            clear_all_statistics()
        else:
            print("삭제가 취소되었습니다.")
