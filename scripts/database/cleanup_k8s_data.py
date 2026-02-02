#!/usr/bin/env python3
"""
k8s 환경의 PostgreSQL 데이터를 정리하는 스크립트
"""

import psycopg2
import psycopg2.extras
from psycopg2.extras import RealDictCursor
import sys

def connect_to_k8s_postgres():
    """k8s PostgreSQL에 연결"""
    try:
        connection = psycopg2.connect(
            host="localhost",
            port=54635,
            database="drillquiz",
            user="postgres",
            password="postgres"  # 실제 비밀번호로 변경 필요
        )
        return connection
    except Exception as e:
        print(f"❌ PostgreSQL 연결 실패: {e}")
        return None

def cleanup_k8s_data():
    """k8s 환경의 데이터 정리"""
    print("🧹 k8s 환경 데이터 정리 시작")
    print("=" * 60)
    
    # PostgreSQL 연결
    conn = connect_to_k8s_postgres()
    if not conn:
        return
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            
            # 1. 현재 상태 확인
            print("🔍 현재 상태 확인 중...")
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_questions,
                    COUNT(CASE WHEN source_id IS NOT NULL THEN 1 END) as with_source_id,
                    COUNT(CASE WHEN source_id IS NULL THEN 1 END) as without_source_id
                FROM quiz_question
            """)
            stats = cursor.fetchone()
            print(f"📊 총 문제 수: {stats['total_questions']}")
            print(f"📊 source_id 있음: {stats['with_source_id']}")
            print(f"📊 source_id 없음: {stats['without_source_id']}")
            
            # 2. csv_id 분포 확인
            print(f"\n🔍 csv_id 분포 확인 중...")
            cursor.execute("""
                SELECT csv_id, COUNT(*) as count 
                FROM quiz_question 
                WHERE csv_id IS NOT NULL 
                GROUP BY csv_id 
                ORDER BY count DESC 
                LIMIT 10
            """)
            csv_id_stats = cursor.fetchall()
            for row in csv_id_stats:
                print(f"  - {row['csv_id']}: {row['count']}개")
            
            # 3. 기존 문제들의 source_id 업데이트
            print(f"\n🔧 기존 문제들의 source_id 업데이트 중...")
            
            # 연결된 시험이 있는 문제들 찾기
            cursor.execute("""
                SELECT DISTINCT q.id, q.csv_id, q.title_ko, q.title_en, e.file_name
                FROM quiz_question q
                JOIN quiz_examquestion eq ON q.id = eq.question_id
                JOIN quiz_exam e ON eq.exam_id = e.id
                WHERE q.source_id IS NULL
                ORDER BY e.file_name
            """)
            
            connected_questions = cursor.fetchall()
            print(f"📊 연결된 시험이 있는 문제: {len(connected_questions)}개")
            
            # source_id 업데이트
            updated_count = 0
            for question in connected_questions:
                if question['file_name']:
                    cursor.execute("""
                        UPDATE quiz_question 
                        SET source_id = %s 
                        WHERE id = %s
                    """, (question['file_name'], question['id']))
                    updated_count += 1
                    print(f"  ✅ {question['title_ko'] or question['title_en']} -> {question['file_name']}")
            
            print(f"📝 source_id 업데이트 완료: {updated_count}개")
            
            # 4. 테스트 데이터 정리
            print(f"\n🧹 테스트 데이터 정리 중...")
            
            # 삭제할 source_id 목록
            sources_to_delete = [
                'LeetCode Dev.xlsx',
                'neetcode_150 (1).xlsx', 
                'Apple N_W LeetCode.xlsx',
                'Staff_Leadership.xlsx'
            ]
            
            total_deleted = 0
            
            for source_id in sources_to_delete:
                print(f"🔍 {source_id} 확인 중...")
                
                # 해당 source_id를 가진 문제들 찾기
                cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM quiz_question 
                    WHERE source_id = %s
                """, (source_id,))
                
                count_result = cursor.fetchone()
                count = count_result['count'] if count_result else 0
                
                if count == 0:
                    print(f"  ✅ {source_id}: 문제 없음")
                    continue
                
                print(f"  📊 {source_id}: {count}개 문제 발견")
                
                # 연결 상태 확인
                cursor.execute("""
                    SELECT COUNT(*) as connected_count
                    FROM quiz_question q
                    JOIN quiz_examquestion eq ON q.id = eq.question_id
                    WHERE q.source_id = %s
                """, (source_id,))
                
                connected_result = cursor.fetchone()
                connected_count = connected_result['connected_count'] if connected_result else 0
                
                if connected_count > 0:
                    print(f"    ⚠️ {connected_count}개 문제가 시험에 연결됨 - 건너뜀")
                    continue
                
                # 연결되지 않은 문제들 삭제
                cursor.execute("""
                    DELETE FROM quiz_question 
                    WHERE source_id = %s
                """, (source_id,))
                
                deleted_count = cursor.rowcount
                total_deleted += deleted_count
                print(f"  ✅ {source_id}: {deleted_count}개 문제 삭제 완료")
            
            # 5. orphaned 문제들 정리
            print(f"\n🔍 orphaned 문제들 정리 중...")
            
            # 연결되지 않은 문제들 찾기
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM quiz_question q
                LEFT JOIN quiz_examquestion eq ON q.id = eq.question_id
                WHERE eq.question_id IS NULL
            """)
            
            orphaned_result = cursor.fetchone()
            orphaned_count = orphaned_result['count'] if orphaned_result else 0
            
            if orphaned_count > 0:
                print(f"📊 연결되지 않은 문제: {orphaned_count}개")
                
                # csv_id가 숫자인 경우 legacy_source로 설정
                cursor.execute("""
                    UPDATE quiz_question 
                    SET source_id = 'legacy_source_' || csv_id
                    WHERE id IN (
                        SELECT q.id
                        FROM quiz_question q
                        LEFT JOIN quiz_examquestion eq ON q.id = eq.question_id
                        WHERE eq.question_id IS NULL 
                        AND q.csv_id ~ '^[0-9]+$'
                        AND q.source_id IS NULL
                    )
                """)
                
                legacy_updated = cursor.rowcount
                print(f"✅ legacy_source로 업데이트: {legacy_updated}개")
                
                # 나머지는 orphaned_unknown으로 설정
                cursor.execute("""
                    UPDATE quiz_question 
                    SET source_id = 'orphaned_unknown'
                    WHERE source_id IS NULL
                """)
                
                unknown_updated = cursor.rowcount
                print(f"✅ orphaned_unknown으로 업데이트: {unknown_updated}개")
            
            # 6. 최종 상태 확인
            print(f"\n🔍 정리 후 상태:")
            cursor.execute("""
                SELECT source_id, COUNT(*) as count 
                FROM quiz_question 
                GROUP BY source_id 
                ORDER BY count DESC 
                LIMIT 10
            """)
            
            final_stats = cursor.fetchall()
            for row in final_stats:
                print(f"  - {row['source_id'] or 'None'}: {row['count']}개")
            
            # 변경사항 커밋
            conn.commit()
            print(f"\n✅ 모든 변경사항이 커밋되었습니다!")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()

if __name__ == "__main__":
    cleanup_k8s_data()

