#!/usr/bin/env python3
"""
quiz_study 테이블에서 created_at과 updated_at 컬럼을 삭제하는 스크립트
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
os.environ['POSTGRES_PORT'] = '51452'
os.environ['POSTGRES_DB'] = 'drillquiz'
os.environ['POSTGRES_USER'] = 'postgres'
os.environ['POSTGRES_PASSWORD'] = 'DevOps!323'
os.environ['USE_DOCKER'] = 'true'

django.setup()

from django.db import connection

def remove_study_columns():
    """quiz_study 테이블에서 created_at, updated_at 컬럼 제거"""
    try:
        with connection.cursor() as cursor:
            # 현재 테이블 구조 확인
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'quiz_study' 
                AND column_name IN ('created_at', 'updated_at')
                ORDER BY column_name
            """)
            
            existing_columns = cursor.fetchall()
            if existing_columns:
                print("🔍 다음 컬럼들이 존재합니다:")
                for col in existing_columns:
                    print(f"  - {col[0]}: {col[1]}")
                
                print("\n🗑️ 컬럼 삭제를 시작합니다...")
                
                # created_at 컬럼 삭제
                if any(col[0] == 'created_at' for col in existing_columns):
                    cursor.execute("ALTER TABLE quiz_study DROP COLUMN IF EXISTS created_at")
                    print("✅ created_at 컬럼 삭제됨")
                
                # updated_at 컬럼 삭제
                if any(col[0] == 'updated_at' for col in existing_columns):
                    cursor.execute("ALTER TABLE quiz_study DROP COLUMN IF EXISTS updated_at")
                    print("✅ updated_at 컬럼 삭제됨")
                
                # 관련 인덱스 삭제
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
                    print(f"✅ 인덱스 {index_name} 삭제됨")
                
                # 테이블 구조 다시 확인
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'quiz_study' 
                    ORDER BY ordinal_position
                """)
                
                columns = cursor.fetchall()
                print("\n📋 현재 quiz_study 테이블 구조:")
                for col in columns:
                    print(f"  - {col[0]}: {col[1]}")
                
            else:
                print("ℹ️ created_at, updated_at 컬럼이 이미 존재하지 않습니다.")
                
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False
    
    return True

def main():
    """메인 함수"""
    print("🚀 quiz_study 테이블 컬럼 삭제 스크립트 시작")
    print("=" * 50)
    
    # DB 연결 확인
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print(f"📊 PostgreSQL 버전: {version}")
            
            # 현재 DB 이름 확인
            cursor.execute("SELECT current_database()")
            db_name = cursor.fetchone()[0]
            print(f"🗄️ 현재 DB: {db_name}")
            
            # 현재 사용자 확인
            cursor.execute("SELECT current_user")
            current_user = cursor.fetchone()[0]
            print(f"👤 현재 사용자: {current_user}")
            
    except Exception as e:
        print(f"❌ DB 연결 실패: {e}")
        print("💡 포트포워딩이 올바르게 설정되었는지 확인하세요 (localhost:51452)")
        return
    
    # 컬럼 삭제
    if remove_study_columns():
        print("\n🎉 컬럼 삭제가 완료되었습니다!")
        print("💡 이제 마이그레이션을 다시 실행할 수 있습니다.")
    else:
        print("\n❌ 컬럼 삭제에 실패했습니다.")

if __name__ == "__main__":
    main()
