#!/usr/bin/env python
"""
운영 환경 마이그레이션 정리 스크립트
포트포워딩을 통해 localhost:58295로 접근
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

def fix_production_migrations():
    """운영 환경에서 문제가 되는 마이그레이션들을 제거합니다."""
    print("=== 운영 환경 마이그레이션 정리 시작 ===")
    
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
        
        # 1. 제거할 마이그레이션들 확인
        print("\n--- 1. 제거할 마이그레이션들 확인 ---")
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
                print(f"  ⚠️  {migration_name}: 운영 환경에 존재함 (제거 예정)")
            else:
                print(f"  ✅ {migration_name}: 운영 환경에 없음")
        
        # 2. 문제가 되는 마이그레이션들 제거
        print("\n--- 2. 문제가 되는 마이그레이션들 제거 ---")
        
        for migration_name in problem_migrations:
            try:
                cursor.execute("""
                    DELETE FROM django_migrations 
                    WHERE app = 'quiz' AND name = %s
                """, (migration_name,))
                
                deleted_count = cursor.rowcount
                if deleted_count > 0:
                    print(f"  ✅ {migration_name}: 제거 완료")
                else:
                    print(f"  ℹ️  {migration_name}: 이미 제거됨")
                    
            except Exception as e:
                print(f"  ❌ {migration_name}: 제거 실패 - {str(e)}")
        
        # 3. 제거 후 마이그레이션 상태 확인
        print("\n--- 3. 제거 후 마이그레이션 상태 확인 ---")
        cursor.execute("""
            SELECT app, name, applied 
            FROM django_migrations 
            WHERE app = 'quiz' 
            ORDER BY applied
        """)
        
        migrations = cursor.fetchall()
        print(f"총 마이그레이션 수: {len(migrations)}")
        
        # 최근 마이그레이션들만 표시
        recent_migrations = migrations[-5:] if len(migrations) > 5 else migrations
        for migration in recent_migrations:
            print(f"  {migration['app']}.{migration['name']} - {migration['applied']}")
        
        if len(migrations) > 5:
            print(f"  ... 및 {len(migrations) - 5}개 더")
        
        # 4. quiz_studytask 테이블 구조 확인
        print("\n--- 4. quiz_studytask 테이블 구조 확인 ---")
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
        
        # 변경사항 커밋
        conn.commit()
        print("\n✅ 모든 변경사항이 커밋되었습니다.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 오류 발생 시 롤백
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    print("운영 환경 마이그레이션 정리 스크립트")
    print("=" * 60)
    print("⚠️  주의: 이 스크립트는 운영 환경의 마이그레이션 기록을 수정합니다!")
    print("제거할 마이그레이션들:")
    print("  - 0041_add_seq_field_to_studytask")
    print("  - 0042_add_missing_fields_to_studytask")
    print("\n이 마이그레이션들은 이미 데이터베이스에 적용되었지만")
    print("Django 마이그레이션 시스템과 충돌을 일으키고 있습니다.")
    
    response = input("\n계속 진행하시겠습니까? (y/N): ")
    if response.lower() in ['y', 'yes']:
        fix_production_migrations()
    else:
        print("작업이 취소되었습니다.")
