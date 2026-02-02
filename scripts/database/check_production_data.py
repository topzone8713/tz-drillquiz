#!/usr/bin/env python
"""
운영 데이터베이스 StudyTask 컬럼 데이터 상태 확인 스크립트
포트포워딩을 통해 localhost:58295로 접근
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

def check_production_data():
    """운영 데이터베이스의 StudyTask 데이터 상태를 확인합니다."""
    print("=== 운영 데이터베이스 StudyTask 데이터 상태 확인 ===")
    
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
        
        # 1. 전체 테이블 구조 확인
        print("\n--- 1. 테이블 구조 확인 ---")
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
        
        # 2. 새로 추가된 컬럼들의 데이터 상태 확인
        print("\n--- 2. 새로 추가된 컬럼 데이터 상태 ---")
        
        # seq 컬럼 확인
        cursor.execute("SELECT COUNT(*) as total, COUNT(seq) as seq_count, MIN(seq) as min_seq, MAX(seq) as max_seq FROM quiz_studytask")
        seq_stats = cursor.fetchone()
        print(f"seq 컬럼:")
        print(f"  - 총 레코드: {seq_stats['total']}")
        print(f"  - seq 값이 있는 레코드: {seq_stats['seq_count']}")
        print(f"  - seq 범위: {seq_stats['min_seq']} ~ {seq_stats['max_seq']}")
        
        # day 컬럼 확인
        cursor.execute("SELECT COUNT(*) as total, COUNT(day) as day_count FROM quiz_studytask")
        day_stats = cursor.fetchone()
        print(f"day 컬럼:")
        print(f"  - 총 레코드: {day_stats['total']}")
        print(f"  - day 값이 있는 레코드: {day_stats['day_count']}")
        
        # description 컬럼 확인
        cursor.execute("SELECT COUNT(*) as total, COUNT(description) as desc_count FROM quiz_studytask")
        desc_stats = cursor.fetchone()
        print(f"description 컬럼:")
        print(f"  - 총 레코드: {desc_stats['total']}")
        print(f"  - description 값이 있는 레코드: {desc_stats['desc_count']}")
        
        # group_id 컬럼 확인
        cursor.execute("SELECT COUNT(*) as total, COUNT(group_id) as group_count FROM quiz_studytask")
        group_stats = cursor.fetchone()
        print(f"group_id 컬럼:")
        print(f"  - 총 레코드: {group_stats['total']}")
        print(f"  - group_id 값이 있는 레코드: {group_stats['group_count']}")
        
        # 3. 실제 데이터 샘플 확인
        print("\n--- 3. 실제 데이터 샘플 (처음 5개) ---")
        cursor.execute("""
            SELECT id, name, seq, day, description, group_id
            FROM quiz_studytask 
            ORDER BY id 
            LIMIT 5
        """)
        
        samples = cursor.fetchall()
        for row in samples:
            print(f"  ID {row['id']}: {row['name']}")
            print(f"    seq: {row['seq']}")
            print(f"    day: {row['day']}")
            print(f"    description: {row['description']}")
            print(f"    group_id: {row['group_id']}")
            print()
        
        # 4. NULL이 아닌 값이 있는 컬럼 확인
        print("\n--- 4. NULL이 아닌 값이 있는 컬럼 ---")
        for col_name in ['seq', 'day', 'description', 'group_id']:
            cursor.execute(f"SELECT COUNT(*) as count FROM quiz_studytask WHERE {col_name} IS NOT NULL")
            result = cursor.fetchone()
            if result['count'] > 0:
                print(f"  {col_name}: {result['count']}개 레코드에 값이 있음")
            else:
                print(f"  {col_name}: 모든 레코드가 NULL")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_production_data()
