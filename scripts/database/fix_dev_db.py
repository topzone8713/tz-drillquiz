#!/usr/bin/env python
"""
개발 데이터베이스 StudyTask seq 필드 수정 스크립트
포트포워딩을 통해 localhost:59815로 접근
"""

import os
import sys
import django
import psycopg2
from psycopg2.extras import RealDictCursor

# Django 설정 로드
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
django.setup()

def fix_dev_database():
    """개발 데이터베이스를 수정합니다."""
    print("=== 개발 데이터베이스 수정 시작 ===")
    
    # 개발 데이터베이스 연결 정보 (포트포워딩)
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
        
        # 1. seq 필드 수정
        print("\n--- 1. seq 필드 수정 ---")
        
        # 각 스터디별로 태스크의 seq를 순차적으로 설정
        cursor.execute("""
            WITH ranked_tasks AS (
                SELECT id, study_id, ROW_NUMBER() OVER (PARTITION BY study_id ORDER BY id) as new_seq
                FROM quiz_studytask
            )
            UPDATE quiz_studytask 
            SET seq = ranked_tasks.new_seq
            FROM ranked_tasks 
            WHERE quiz_studytask.id = ranked_tasks.id
        """)
        
        updated_rows = cursor.rowcount
        print(f"✅ {updated_rows}개 레코드의 seq 필드가 수정되었습니다.")
        
        # 2. 수정 결과 확인
        print("\n--- 2. 수정 결과 확인 ---")
        
        cursor.execute("SELECT COUNT(*) as total FROM quiz_studytask")
        total_count = cursor.fetchone()['total']
        print(f"총 레코드 수: {total_count}")
        
        cursor.execute("SELECT COUNT(*) as zero_seq FROM quiz_studytask WHERE seq = 0")
        zero_seq_count = cursor.fetchone()['zero_seq']
        print(f"seq가 0인 레코드 수: {zero_seq_count}")
        
        # 3. 스터디별 seq 분포 확인
        print("\n--- 3. 스터디별 seq 분포 ---")
        cursor.execute("""
            SELECT study_id, COUNT(*) as task_count, 
                   MIN(seq) as min_seq, MAX(seq) as max_seq
            FROM quiz_studytask 
            GROUP BY study_id 
            ORDER BY study_id
        """)
        
        study_distribution = cursor.fetchall()
        for row in study_distribution:
            print(f"  스터디 {row['study_id']}: {row['task_count']}개 태스크 (seq {row['min_seq']}-{row['max_seq']})")
        
        # 4. seq 값 검증
        print("\n--- 4. seq 값 검증 ---")
        
        # 중복된 seq 확인
        cursor.execute("""
            SELECT study_id, seq, COUNT(*) as count
            FROM quiz_studytask 
            WHERE seq > 0 
            GROUP BY study_id, seq 
            HAVING COUNT(*) > 1
            ORDER BY study_id, seq
        """)
        
        duplicates = cursor.fetchall()
        if duplicates:
            print(f"⚠️  중복된 seq가 {len(duplicates)}개 있습니다:")
            for row in duplicates:
                print(f"  - 스터디 {row['study_id']}, seq {row['seq']}: {row['count']}개")
        else:
            print("✅ 중복된 seq가 없습니다.")
        
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
    print("개발 데이터베이스 수정 스크립트 (포트포워딩: localhost:59815)")
    print("=" * 60)
    print("⚠️  주의: 이 스크립트는 개발 데이터베이스를 직접 수정합니다!")
    
    response = input("\n계속 진행하시겠습니까? (y/N): ")
    if response.lower() in ['y', 'yes']:
        fix_dev_database()
    else:
        print("작업이 취소되었습니다.")
