#!/usr/bin/env python3
"""
개발 환경 PostgreSQL DB 상태 확인 스크립트
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
os.environ['POSTGRES_PORT'] = '51370'
os.environ['POSTGRES_DB'] = 'drillquiz'
os.environ['POSTGRES_USER'] = 'postgres'
os.environ['POSTGRES_PASSWORD'] = 'DevOps!323'
os.environ['USE_DOCKER'] = 'true'

django.setup()

from django.db import connection

def check_db_status():
    """데이터베이스 상태 확인"""
    try:
        with connection.cursor() as cursor:
            # 1. PostgreSQL 버전 및 연결 정보
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print(f"📊 PostgreSQL 버전: {version}")
            
            cursor.execute("SELECT current_database()")
            db_name = cursor.fetchone()[0]
            print(f"🗄️ 현재 DB: {db_name}")
            
            cursor.execute("SELECT current_user")
            current_user = cursor.fetchone()[0]
            print(f"👤 현재 사용자: {current_user}")
            
            # 2. 테이블 목록 확인
            cursor.execute("""
                SELECT table_name, table_type 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)
            
            tables = cursor.fetchall()
            print(f"\n📋 테이블 목록 (총 {len(tables)}개):")
            for table in tables:
                print(f"  - {table[0]} ({table[1]})")
            
            # 3. quiz_study 테이블 구조 확인
            print(f"\n🔍 quiz_study 테이블 구조:")
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'quiz_study' 
                ORDER BY ordinal_position
            """)
            
            columns = cursor.fetchall()
            for col in columns:
                nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                default = f"DEFAULT {col[3]}" if col[3] else ""
                print(f"  - {col[0]}: {col[1]} {nullable} {default}")
            
            # 4. quiz_studytask 테이블 구조 확인
            print(f"\n🔍 quiz_studytask 테이블 구조:")
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'quiz_studytask' 
                ORDER BY ordinal_position
            """)
            
            columns = cursor.fetchall()
            for col in columns:
                nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                default = f"DEFAULT {col[3]}" if col[3] else ""
                print(f"  - {col[0]}: {col[1]} {nullable} {default}")
            
            # 5. 마이그레이션 상태 확인
            print(f"\n🔍 Django 마이그레이션 상태:")
            cursor.execute("""
                SELECT app, name, applied 
                FROM django_migrations 
                WHERE app = 'quiz' 
                ORDER BY applied DESC 
                LIMIT 10
            """)
            
            migrations = cursor.fetchall()
            for mig in migrations:
                status = "✅" if mig[2] else "❌"
                print(f"  {status} {mig[0]}.{mig[1]}")
            
            # 6. 테이블별 레코드 수 확인
            print(f"\n📊 테이블별 레코드 수:")
            for table in tables:
                if table[1] == 'BASE TABLE':
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                        count = cursor.fetchone()[0]
                        print(f"  - {table[0]}: {count:,}개")
                    except Exception as e:
                        print(f"  - {table[0]}: 확인 실패 ({e})")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False
    
    return True

def main():
    """메인 함수"""
    print("🚀 개발 환경 PostgreSQL DB 상태 확인 스크립트 시작")
    print("=" * 60)
    
    # DB 연결 확인
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ DB 연결 성공!")
            
    except Exception as e:
        print(f"❌ DB 연결 실패: {e}")
        print("💡 포트포워딩이 올바르게 설정되었는지 확인하세요 (localhost:59164)")
        return
    
    # DB 상태 확인
    if check_db_status():
        print("\n🎉 DB 상태 확인이 완료되었습니다!")
    else:
        print("\n❌ DB 상태 확인에 실패했습니다.")

if __name__ == "__main__":
    main()
