#!/usr/bin/env python3
"""
원본 컬럼의 값을 한국어 필드로 복사하는 스크립트
"""

import os
import sys
import django
from pathlib import Path

# Django 설정 로드
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
os.environ['USE_DOCKER'] = 'true'
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '51370'
os.environ['POSTGRES_DB'] = 'drillquiz'
os.environ['POSTGRES_USER'] = 'postgres'
os.environ['POSTGRES_PASSWORD'] = 'DevOps!323'

django.setup()

from django.db import connection

def copy_original_to_korean():
    """원본 컬럼의 값을 한국어 필드로 복사"""
    try:
        with connection.cursor() as cursor:
            print("🚀 원본 컬럼을 한국어 필드로 복사 시작")
            print("=" * 60)
            
            # 1. quiz_study 테이블 - 원본 title, goal에서 _ko로 복사
            print("📚 quiz_study 테이블 처리 중...")
            cursor.execute("""
                UPDATE quiz_study 
                SET title_ko = title, goal_ko = goal
            """)
            study_updated = cursor.rowcount
            print(f"  ✅ quiz_study 업데이트 완료: {study_updated}개 행")
            
            # 2. quiz_exam 테이블 - 원본 title, description에서 _ko로 복사
            print("📝 quiz_exam 테이블 처리 중...")
            cursor.execute("""
                UPDATE quiz_exam 
                SET title_ko = title, description_ko = description
            """)
            exam_updated = cursor.rowcount
            print(f"  ✅ quiz_exam 업데이트 완료: {exam_updated}개 행")
            
            # 3. quiz_question 테이블 - 원본 title, content, answer, explanation에서 _ko로 복사
            print("❓ quiz_question 테이블 처리 중...")
            cursor.execute("""
                UPDATE quiz_question 
                SET title_ko = title, content_ko = content, 
                    answer_ko = answer, explanation_ko = explanation
            """)
            question_updated = cursor.rowcount
            print(f"  ✅ quiz_question 업데이트 완료: {question_updated}개 행")
            
            # 4. quiz_studytask 테이블 - 원본 name에서 name_ko로 복사
            print("📋 quiz_studytask 테이블 처리 중...")
            cursor.execute("""
                UPDATE quiz_studytask 
                SET name_ko = name
            """)
            task_updated = cursor.rowcount
            print(f"  ✅ quiz_studytask 업데이트 완료: {task_updated}개 행")
            
            # 변경사항 커밋
            connection.commit()
            
            print("\n🎉 모든 테이블 업데이트 완료!")
            print(f"📊 총 업데이트된 행 수:")
            print(f"  - quiz_study: {study_updated}개")
            print(f"  - quiz_exam: {exam_updated}개")
            print(f"  - quiz_question: {question_updated}개")
            print(f"  - quiz_studytask: {task_updated}개")
            
            return True
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        connection.rollback()
        return False

def verify_copy_results():
    """복사 결과 확인"""
    try:
        with connection.cursor() as cursor:
            print("\n🔍 복사 결과 확인 중...")
            print("=" * 60)
            
            # quiz_study 확인
            cursor.execute("SELECT COUNT(*) FROM quiz_study WHERE title_ko IS NOT NULL AND title_ko != ''")
            study_count = cursor.fetchone()[0]
            print(f"  📚 quiz_study (title_ko): {study_count}개")
            
            # quiz_exam 확인
            cursor.execute("SELECT COUNT(*) FROM quiz_exam WHERE title_ko IS NOT NULL AND title_ko != ''")
            exam_count = cursor.fetchone()[0]
            print(f"  📝 quiz_exam (title_ko): {exam_count}개")
            
            # quiz_question 확인
            cursor.execute("SELECT COUNT(*) FROM quiz_question WHERE title_ko IS NOT NULL AND title_ko != ''")
            question_title_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM quiz_question WHERE content_ko IS NOT NULL AND content_ko != ''")
            question_content_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM quiz_question WHERE answer_ko IS NOT NULL AND answer_ko != ''")
            question_answer_count = cursor.fetchone()[0]
            print(f"  ❓ quiz_question (title_ko): {question_title_count}개")
            print(f"  ❓ quiz_question (content_ko): {question_content_count}개")
            print(f"  ❓ quiz_question (answer_ko): {question_answer_count}개")
            
            # quiz_studytask 확인
            cursor.execute("SELECT COUNT(*) FROM quiz_studytask WHERE name_ko IS NOT NULL AND name_ko != ''")
            task_count = cursor.fetchone()[0]
            print(f"  📋 quiz_studytask (name_ko): {task_count}개")
            
            return True
            
    except Exception as e:
        print(f"❌ 확인 중 오류 발생: {e}")
        return False

def main():
    """메인 함수"""
    print("🚀 원본 컬럼을 한국어 필드로 복사하는 스크립트 시작")
    print("=" * 60)
    
    # DB 연결 확인
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ DB 연결 성공!")
            
    except Exception as e:
        print(f"❌ DB 연결 실패: {e}")
        print("💡 포트포워딩이 올바르게 설정되었는지 확인하세요 (localhost:51370)")
        return
    
    # 원본 컬럼을 한국어 필드로 복사
    if copy_original_to_korean():
        print("\n✅ 복사 작업이 성공적으로 완료되었습니다!")
        
        # 결과 확인
        verify_copy_results()
        
    else:
        print("\n❌ 복사 작업에 실패했습니다.")

if __name__ == "__main__":
    main()
