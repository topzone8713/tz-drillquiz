#!/usr/bin/env python
"""
개발 데이터베이스 불필요한 컬럼 제거 스크립트
포트포워딩을 통해 localhost:59815로 접근
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

def clean_dev_database():
    """개발 데이터베이스에서 불필요한 컬럼들을 제거합니다."""
    print("=== 개발 데이터베이스 불필요한 컬럼 제거 시작 ===")
    
    # 개발 데이터베이스 연결 정보
    db_config = {
        'host': 'localhost',
        'port': 59815,
        'database': 'drillquiz',
        'user': 'admin',
        'password': 'DevOps!323'
    }
    
    try:
        print(f"데이터베이스 연결: {db_config['host']}:{db_config['port']}")
        
        # 데이터베이스 연결
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. 제거할 컬럼들 확인
        print("\n--- 1. 제거할 컬럼들 확인 ---")
        columns_to_remove = ['day', 'description', 'group_id']
        
        for col_name in columns_to_remove:
            cursor.execute(f"SELECT COUNT(*) as count FROM quiz_studytask WHERE {col_name} IS NOT NULL")
            result = cursor.fetchone()
            if result['count'] > 0:
                print(f"  ⚠️  {col_name}: {result['count']}개 레코드에 값이 있음")
            else:
                print(f"  ✅ {col_name}: 모든 레코드가 NULL (안전하게 제거 가능)")
        
        # 2. 컬럼 제거
        print("\n--- 2. 불필요한 컬럼들 제거 ---")
        
        for col_name in columns_to_remove:
            try:
                cursor.execute(f"ALTER TABLE quiz_studytask DROP COLUMN IF EXISTS {col_name}")
                print(f"  ✅ {col_name} 컬럼 제거 완료")
            except Exception as e:
                print(f"  ❌ {col_name} 컬럼 제거 실패: {str(e)}")
        
        # 3. 제거 후 테이블 구조 확인
        print("\n--- 3. 제거 후 테이블 구조 확인 ---")
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
        
        # 4. seq 컬럼 상태 확인 (유지할 컬럼)
        print("\n--- 4. seq 컬럼 상태 확인 (유지) ---")
        cursor.execute("SELECT COUNT(*) as total, MIN(seq) as min_seq, MAX(seq) as max_seq FROM quiz_studytask")
        seq_stats = cursor.fetchone()
        print(f"seq 컬럼:")
        print(f"  - 총 레코드: {seq_stats['total']}")
        print(f"  - seq 범위: {seq_stats['min_seq']} ~ {seq_stats['max_seq']}")
        
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
    print("개발 데이터베이스 불필요한 컬럼 제거 스크립트")
    print("=" * 60)
    print("⚠️  주의: 이 스크립트는 개발 데이터베이스를 직접 수정합니다!")
    print("제거할 컬럼들: day, description, group_id (모두 NULL 값만 있음)")
    print("유지할 컬럼: seq (실제 데이터가 있음)")
    
    response = input("\n계속 진행하시겠습니까? (y/N): ")
    if response.lower() in ['y', 'yes']:
        clean_dev_database()
    else:
        print("작업이 취소되었습니다.")
