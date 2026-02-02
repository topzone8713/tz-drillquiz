#!/usr/bin/env python
"""
시험에서 중복된 문제들을 제거하는 스크립트
각 문제당 첫 번째 것만 남기고 나머지는 제거
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

def get_duplicates_to_remove(cursor, exam_id):
    """제거해야 할 중복 문제들을 찾습니다."""
    print(f"\n=== 중복 문제 분석 (시험 ID: {exam_id}) ===")
    
    # 중복 문제들 찾기
    cursor.execute("""
        SELECT q.title_en, COUNT(*) as count, 
               ARRAY_AGG(eq.question_id ORDER BY eq.order) as question_ids,
               ARRAY_AGG(eq.order ORDER BY eq.order) as orders,
               ARRAY_AGG(eq.id ORDER BY eq.order) as exam_question_ids
        FROM quiz_examquestion eq
        JOIN quiz_question q ON eq.question_id = q.id
        WHERE eq.exam_id = %s
        GROUP BY q.title_en
        HAVING COUNT(*) > 1
        ORDER BY count DESC
    """, (exam_id,))
    
    duplicates = cursor.fetchall()
    print(f"중복된 문제 수: {len(duplicates)}개")
    
    to_remove = []
    
    for dup in duplicates:
        print(f"\n--- {dup['title_en']} ({dup['count']}개) ---")
        print(f"  Orders: {dup['orders']}")
        print(f"  Question IDs: {dup['question_ids']}")
        
        # 첫 번째 것(order가 가장 작은 것)은 유지하고 나머지는 제거 대상에 추가
        for i in range(1, len(dup['exam_question_ids'])):  # 첫 번째(인덱스 0)는 제외
            to_remove.append({
                'exam_question_id': dup['exam_question_ids'][i],
                'question_id': dup['question_ids'][i],
                'order': dup['orders'][i],
                'title': dup['title_en']
            })
            print(f"    제거 대상: Order {dup['orders'][i]} (Question ID: {dup['question_ids'][i]})")
    
    print(f"\n총 제거할 중복 항목 수: {len(to_remove)}개")
    return to_remove

def remove_duplicates(cursor, conn, exam_id):
    """중복 문제들을 제거합니다."""
    print(f"\n=== 중복 문제 제거 시작 ===")
    
    # 제거할 중복 문제들 찾기
    to_remove = get_duplicates_to_remove(cursor, exam_id)
    
    if not to_remove:
        print("제거할 중복 문제가 없습니다.")
        return 0
    
    removed_count = 0
    
    for item in to_remove:
        try:
            # quiz_examquestion에서 해당 항목 제거
            cursor.execute("""
                DELETE FROM quiz_examquestion 
                WHERE id = %s AND exam_id = %s
            """, (item['exam_question_id'], exam_id))
            
            print(f"✅ 제거: {item['title']} (Order {item['order']})")
            removed_count += 1
            
        except Exception as e:
            print(f"❌ 제거 실패: {item['title']} (Order {item['order']}) - {e}")
    
    # 변경사항 커밋
    try:
        conn.commit()
        print(f"\n✅ 총 {removed_count}개 중복 문제가 제거되었습니다.")
        return removed_count
    except Exception as e:
        print(f"\n❌ 커밋 실패: {e}")
        conn.rollback()
        return 0

def verify_cleanup(cursor, exam_id):
    """중복 제거 후 결과를 확인합니다."""
    print(f"\n=== 중복 제거 후 결과 확인 ===")
    
    # 현재 시험의 총 문제 수
    cursor.execute("""
        SELECT COUNT(*) as total_count
        FROM quiz_examquestion 
        WHERE exam_id = %s
    """, (exam_id,))
    
    total_count = cursor.fetchone()['total_count']
    print(f"현재 시험의 총 문제 수: {total_count}개")
    
    # 남은 중복 문제 확인
    cursor.execute("""
        SELECT q.title_en, COUNT(*) as count
        FROM quiz_examquestion eq
        JOIN quiz_question q ON eq.question_id = q.id
        WHERE eq.exam_id = %s
        GROUP BY q.title_en
        HAVING COUNT(*) > 1
        ORDER BY count DESC
    """, (exam_id,))
    
    remaining_duplicates = cursor.fetchall()
    
    if not remaining_duplicates:
        print("✅ 모든 중복 문제가 성공적으로 제거되었습니다!")
    else:
        print(f"⚠️  여전히 {len(remaining_duplicates)}개의 중복 문제가 남아있습니다:")
        for dup in remaining_duplicates[:5]:  # 처음 5개만 출력
            print(f"  - {dup['title_en']}: {dup['count']}개")

def main():
    """메인 함수"""
    print("=== 시험 중복 문제 제거 스크립트 ===")
    
    # 시험 ID
    exam_id = 'c3cdbfc0-893d-4616-9015-2091e48f63b2'
    print(f"대상 시험 ID: {exam_id}")
    
    # 데이터베이스 연결
    conn, cursor = connect_to_database()
    if not conn or not cursor:
        return
    
    try:
        # 중복 문제 제거
        removed_count = remove_duplicates(cursor, conn, exam_id)
        
        if removed_count > 0:
            # 결과 확인
            verify_cleanup(cursor, exam_id)
        
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











