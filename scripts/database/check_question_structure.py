#!/usr/bin/env python
"""
문제 테이블의 실제 구조를 확인하는 스크립트
"""

import psycopg2
from psycopg2.extras import RealDictCursor

def check_question_structure():
    """문제 테이블의 구조와 샘플 데이터를 확인합니다."""
    db_config = {
        'host': 'localhost',
        'port': 58295,
        'database': 'drillquiz',
        'user': 'admin',
        'password': 'DevOps!323'
    }
    
    try:
        print("데이터베이스 연결 중...")
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. 테이블 구조 확인
        print("\n=== 문제 테이블 구조 확인 ===")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'quiz_question' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        for col in columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"  {col['column_name']}: {col['data_type']} {nullable}{default}")
        
        # 2. 샘플 데이터 확인 (LeetCode 관련 문제들)
        print("\n=== LeetCode 관련 문제 샘플 데이터 ===")
        cursor.execute("""
            SELECT id, title_en, csv_id, source_id
            FROM quiz_question 
            WHERE title_en LIKE '%Longest Absolute File Path%' 
               OR title_en LIKE '%Shortest Bridge%'
               OR title_en LIKE '%Continuous Subarray Sum%'
               OR title_en LIKE '%Accounts Merge%'
               OR title_en LIKE '%Subsets%'
            LIMIT 10
        """)
        
        samples = cursor.fetchall()
        print(f"총 {len(samples)}개 샘플 발견:")
        for sample in samples:
            print(f"  ID: {sample['id']}")
            print(f"  제목: {sample['title_en']}")
            print(f"  CSV_ID: {sample['csv_id']}")
            print(f"  SOURCE_ID: {sample['source_id']}")
            print("  ---")
        
        # 3. 중복 문제 확인 (csv_id 기준)
        print("\n=== CSV_ID 기준 중복 확인 ===")
        cursor.execute("""
            SELECT csv_id, COUNT(*) as count, 
                   ARRAY_AGG(title_en ORDER BY created_at) as titles
            FROM quiz_question 
            WHERE csv_id IS NOT NULL AND csv_id != ''
            GROUP BY csv_id 
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            LIMIT 5
        """)
        
        duplicates = cursor.fetchall()
        print(f"CSV_ID 기준 중복 문제: {len(duplicates)}개")
        for dup in duplicates:
            print(f"  CSV_ID {dup['csv_id']}: {dup['count']}개")
            for title in dup['titles'][:3]:  # 처음 3개만 출력
                print(f"    - {title}")
            print("  ---")
        
    except Exception as e:
        print(f"오류 발생: {e}")
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        print("데이터베이스 연결 종료")

if __name__ == "__main__":
    check_question_structure()














