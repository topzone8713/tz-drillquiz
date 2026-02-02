#!/usr/bin/env python3
"""
PostgreSQL DB에서 seq 컬럼을 삭제하는 스크립트
k8s dev 환경의 DB에 포트포워딩으로 접근하여 seq 컬럼 제거
"""

import os
import sys
import django
from pathlib import Path

# Django 설정 로드
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
django.setup()

from django.db import connection

def remove_seq_column():
    """quiz_studytask 테이블에서 seq 컬럼 제거"""
    try:
        with connection.cursor() as cursor:
            # 현재 테이블 구조 확인
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'quiz_studytask' 
                AND column_name = 'seq'
            """)
            
            if cursor.fetchone():
                print("🔍 seq 컬럼이 존재합니다. 삭제를 시작합니다...")
                
                # seq 컬럼 삭제
                cursor.execute("ALTER TABLE quiz_studytask DROP COLUMN IF EXISTS seq")
                print("✅ seq 컬럼이 성공적으로 삭제되었습니다.")
                
                # 인덱스도 함께 삭제 (seq 필드가 포함된 인덱스)
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
                    print(f"✅ 인덱스 {index_name} 삭제됨")
                
                # 테이블 구조 다시 확인
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'quiz_studytask' 
                    ORDER BY ordinal_position
                """)
                
                columns = cursor.fetchall()
                print("\n📋 현재 quiz_studytask 테이블 구조:")
                for col in columns:
                    print(f"  - {col[0]}: {col[1]}")
                
            else:
                print("ℹ️ seq 컬럼이 이미 존재하지 않습니다.")
                
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False
    
    return True

def main():
    """메인 함수"""
    print("🚀 PostgreSQL DB seq 컬럼 삭제 스크립트 시작")
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
            
    except Exception as e:
        print(f"❌ DB 연결 실패: {e}")
        print("💡 포트포워딩이 올바르게 설정되었는지 확인하세요 (localhost:50350)")
        return
    
    # seq 컬럼 삭제
    if remove_seq_column():
        print("\n🎉 seq 컬럼 삭제가 완료되었습니다!")
        print("💡 이제 마이그레이션을 다시 실행할 수 있습니다.")
    else:
        print("\n❌ seq 컬럼 삭제에 실패했습니다.")

if __name__ == "__main__":
    main()
