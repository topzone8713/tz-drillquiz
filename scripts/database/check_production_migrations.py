#!/usr/bin/env python
"""
운영 환경 마이그레이션 상태 확인 스크립트
포트포워딩을 통해 localhost:58295로 접근
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

def check_production_migrations():
    """운영 환경의 마이그레이션 상태를 확인합니다."""
    print("=== 운영 환경 마이그레이션 상태 확인 ===")
    
    # 운영 데이터베이스 연결 정보
    db_config = {
        'host': 'localhost',
        'port': 58295,
        'database': 'drillquiz',
        'user': 'admin',
        'password': 'DevOps!323'
    }
    
    try:
        print(f"데이터베이스 연결: {db_config['host']}:{db_config['port']}")
        
        # 데이터베이스 연결
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. django_migrations 테이블 확인
        print("\n--- 1. Django 마이그레이션 테이블 확인 ---")
        cursor.execute("""
            SELECT app, name, applied 
            FROM django_migrations 
            WHERE app = 'quiz' 
            ORDER BY applied
        """)
        
        migrations = cursor.fetchall()
        print(f"총 마이그레이션 수: {len(migrations)}")
        
        for migration in migrations:
            print(f"  {migration['app']}.{migration['name']} - {migration['applied']}")
        
        # 2. quiz_studytask 테이블 구조 확인
        print("\n--- 2. quiz_studytask 테이블 구조 확인 ---")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'quiz_studytask' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        for col in columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"  {col['column_name']}: {col['data_type']} {nullable}{default}")
        
        # 3. 문제가 되는 마이그레이션 확인
        print("\n--- 3. 문제가 되는 마이그레이션 확인 ---")
        problem_migrations = [
            '0041_add_seq_field_to_studytask',
            '0042_add_missing_fields_to_studytask'
        ]
        
        for migration_name in problem_migrations:
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM django_migrations 
                WHERE app = 'quiz' AND name = %s
            """, (migration_name,))
            
            result = cursor.fetchone()
            if result['count'] > 0:
                print(f"  ⚠️  {migration_name}: 운영 환경에 존재함")
            else:
                print(f"  ✅ {migration_name}: 운영 환경에 없음")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_production_migrations()
