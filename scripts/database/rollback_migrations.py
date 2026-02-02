#!/usr/bin/env python3
"""
문제가 되는 마이그레이션들을 롤백하는 스크립트
"""

import os
import sys
import django
from pathlib import Path

# Django 설정 로드
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '59164'
os.environ['POSTGRES_DB'] = 'drillquiz'
os.environ['POSTGRES_USER'] = 'postgres'
os.environ['POSTGRES_PASSWORD'] = 'DevOps!323'
os.environ['USE_DOCKER'] = 'true'

django.setup()

from django.db import connection

def check_migration_status():
    """마이그레이션 상태 확인"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT app, name, applied 
                FROM django_migrations 
                WHERE app = 'quiz' 
                ORDER BY applied DESC
            """)
            
            migrations = cursor.fetchall()
            print("📋 현재 마이그레이션 상태:")
            for mig in migrations:
                status = "✅" if mig[2] else "❌"
                print(f"  {status} {mig[0]}.{mig[1]}")
            
            return migrations
            
    except Exception as e:
        print(f"❌ 마이그레이션 상태 확인 실패: {e}")
        return []

def rollback_migrations():
    """문제가 되는 마이그레이션들 롤백"""
    try:
        with connection.cursor() as cursor:
            print("\n🔄 마이그레이션 롤백 시작...")
            
            # 1. 0042 마이그레이션 롤백 (created_at, updated_at 컬럼 제거)
            print("\n🗑️ 0042 마이그레이션 롤백 중...")
            
            # created_at 컬럼 제거
            cursor.execute("ALTER TABLE quiz_study DROP COLUMN IF EXISTS created_at")
            print("✅ created_at 컬럼 제거됨")
            
            # updated_at 컬럼 제거
            cursor.execute("ALTER TABLE quiz_study DROP COLUMN IF EXISTS updated_at")
            print("✅ updated_at 컬럼 제거됨")
            
            # 관련 인덱스 제거
            cursor.execute("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'quiz_study' 
                AND (indexdef LIKE '%created_at%' OR indexdef LIKE '%updated_at%')
            """)
            
            indexes = cursor.fetchall()
            for index in indexes:
                index_name = index[0]
                cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
                print(f"✅ 인덱스 {index_name} 제거됨")
            
            # 2. 0041 마이그레이션 롤백 (seq 컬럼 제거)
            print("\n🗑️ 0041 마이그레이션 롤백 중...")
            
            # seq 컬럼 제거
            cursor.execute("ALTER TABLE quiz_studytask DROP COLUMN IF EXISTS seq")
            print("✅ seq 컬럼 제거됨")
            
            # 관련 인덱스 제거
            cursor.execute("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'quiz_studytask' 
                AND indexdef LIKE '%seq%'
            """)
            
            indexes = cursor.fetchall()
            for index in indexes:
                index_name = index[0]
                cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
                print(f"✅ 인덱스 {index_name} 제거됨")
            
            # 3. django_migrations 테이블에서 해당 마이그레이션들 제거
            print("\n🗑️ django_migrations 테이블 정리 중...")
            
            cursor.execute("DELETE FROM django_migrations WHERE app = 'quiz' AND name IN ('0041_add_seq_field_to_studytask_clean', '0042_alter_study_options_study_created_at_and_more')")
            deleted_count = cursor.rowcount
            print(f"✅ {deleted_count}개 마이그레이션 기록 제거됨")
            
            # 4. 테이블 구조 재확인
            print("\n📋 롤백 후 테이블 구조:")
            
            # quiz_study 테이블
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'quiz_study' 
                ORDER BY ordinal_position
            """)
            
            columns = cursor.fetchall()
            print("\n🔍 quiz_study 테이블:")
            for col in columns:
                print(f"  - {col[0]}: {col[1]}")
            
            # quiz_studytask 테이블
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'quiz_studytask' 
                ORDER BY ordinal_position
            """)
            
            columns = cursor.fetchall()
            print("\n🔍 quiz_studytask 테이블:")
            for col in columns:
                print(f"  - {col[0]}: {col[1]}")
            
    except Exception as e:
        print(f"❌ 롤백 중 오류 발생: {e}")
        return False
    
    return True

def main():
    """메인 함수"""
    print("🚀 마이그레이션 롤백 스크립트 시작")
    print("=" * 50)
    
    # DB 연결 확인
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ DB 연결 성공!")
            
    except Exception as e:
        print(f"❌ DB 연결 실패: {e}")
        return
    
    # 마이그레이션 상태 확인
    migrations = check_migration_status()
    if not migrations:
        return
    
    # 롤백 실행
    if rollback_migrations():
        print("\n🎉 마이그레이션 롤백이 완료되었습니다!")
        print("💡 이제 마이그레이션을 다시 실행할 수 있습니다.")
    else:
        print("\n❌ 마이그레이션 롤백에 실패했습니다.")

if __name__ == "__main__":
    main()
