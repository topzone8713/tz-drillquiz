#!/usr/bin/env python
"""
간단한 LeetCode ID 수정 스크립트 - 배치 처리
"""

import psycopg2
from psycopg2.extras import RealDictCursor

def connect_to_database():
    """데이터베이스에 연결합니다."""
    db_config = {
        'host': 'localhost',
        'port': 58295,
        'database': 'drillquiz',
        'user': 'admin',
        'password': 'DevOps!323'
    }
    
    try:
        print(f"데이터베이스 연결: {db_config['host']}:{db_config['port']}")
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        return conn, cursor
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return None, None

def get_wrong_id_mappings():
    """수정해야 할 잘못된 ID 매핑을 반환합니다."""
    return [
        # (현재 잘못된 ID, 올바른 ID, 문제 제목)
        ("68", "78", "Subsets"),
        ("20", "20", "Valid Parentheses"),  # 이미 올바른 경우도 있지만 확인용
    ]

def fix_specific_ids(cursor, conn):
    """특정 잘못된 ID들을 수정합니다."""
    print("\n=== 특정 ID 수정 시작 ===")
    
    wrong_mappings = get_wrong_id_mappings()
    updated_count = 0
    
    for wrong_id, correct_id, title in wrong_mappings:
        print(f"\n--- {title} 수정 중 ---")
        
        # 현재 잘못된 ID를 가진 문제들 확인
        cursor.execute("""
            SELECT id, title_en, csv_id 
            FROM quiz_question 
            WHERE title_en = %s AND csv_id = %s
            LIMIT 5
        """, (title, wrong_id))
        
        wrong_questions = cursor.fetchall()
        print(f"  잘못된 ID {wrong_id}를 가진 {title} 문제: {len(wrong_questions)}개")
        
        # 올바른 ID로 수정
        cursor.execute("""
            UPDATE quiz_question 
            SET csv_id = %s, updated_at = NOW()
            WHERE title_en = %s AND csv_id = %s
        """, (correct_id, title, wrong_id))
        
        affected_rows = cursor.rowcount
        print(f"  ✅ {affected_rows}개 문제를 {wrong_id} → {correct_id}로 수정")
        updated_count += affected_rows
        
        # 중간 커밋
        conn.commit()
    
    print(f"\n✅ 총 {updated_count}개 문제의 ID가 수정되었습니다.")
    return updated_count

def verify_specific_fixes(cursor):
    """특정 수정 결과를 확인합니다."""
    print("\n=== 수정 결과 확인 ===")
    
    wrong_mappings = get_wrong_id_mappings()
    
    for wrong_id, correct_id, title in wrong_mappings:
        # 수정 후 잘못된 ID가 남아있는지 확인
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM quiz_question 
            WHERE title_en = %s AND csv_id = %s
        """, (title, wrong_id))
        
        remaining_wrong = cursor.fetchone()['count']
        
        # 올바른 ID로 수정된 문제 수 확인
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM quiz_question 
            WHERE title_en = %s AND csv_id = %s
        """, (title, correct_id))
        
        correct_count = cursor.fetchone()['count']
        
        print(f"  {title}:")
        print(f"    - 잘못된 ID {wrong_id} 남은 개수: {remaining_wrong}")
        print(f"    - 올바른 ID {correct_id} 개수: {correct_count}")

def main():
    """메인 함수"""
    print("=== 간단한 LeetCode ID 수정 스크립트 ===")
    
    # 데이터베이스 연결
    conn, cursor = connect_to_database()
    if not conn or not cursor:
        return
    
    try:
        # 특정 ID 수정
        updated_count = fix_specific_ids(cursor, conn)
        
        if updated_count > 0:
            # 수정 결과 확인
            verify_specific_fixes(cursor)
        
        print("\n=== 작업 완료 ===")
        
    except Exception as e:
        print(f"\n❌ 작업 중 오류 발생: {e}")
        conn.rollback()
    
    finally:
        cursor.close()
        conn.close()
        print("데이터베이스 연결을 종료했습니다.")

if __name__ == "__main__":
    main()











