#!/usr/bin/env python
"""
Study 권한 문제 진단 스크립트 (DB 직접 연결)
study-detail/24에서 doohee323@gmail.com 사용자의 권한을 확인합니다.
"""
import psycopg2
from psycopg2.extras import RealDictCursor

# DB 연결 정보
DB_HOST = 'localhost'
DB_PORT = 54486
DB_NAME = 'drillquiz'
DB_USER = 'postgres'
DB_PASSWORD = 'DevOps!323'

def check_study_permission():
    email = 'doohee323@gmail.com'
    study_id = 24
    
    print(f"=" * 60)
    print(f"Study 권한 진단: Study ID {study_id}")
    print(f"사용자 이메일: {email}")
    print(f"=" * 60)
    
    try:
        # DB 연결
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. 사용자 찾기
        print(f"\n[1] 사용자 정보:")
        cur.execute("""
            SELECT id, username, email, is_superuser, is_staff
            FROM quiz_user
            WHERE email = %s
        """, (email,))
        users = cur.fetchall()
        
        if not users:
            print(f"  [오류] 사용자를 찾을 수 없습니다: {email}")
            return
        
        if len(users) > 1:
            print(f"  [경고] 동일한 이메일의 사용자가 {len(users)}명 있습니다:")
            for u in users:
                print(f"    - ID: {u['id']}, Username: {u['username']}")
        
        user = users[0]
        user_id = user['id']
        print(f"  - ID: {user_id}")
        print(f"  - Username: {user['username']}")
        print(f"  - Email: {user['email']}")
        print(f"  - Is Superuser: {user['is_superuser']}")
        print(f"  - Is Staff: {user['is_staff']}")
        
        # 2. UserProfile 확인
        cur.execute("""
            SELECT role
            FROM quiz_userprofile
            WHERE user_id = %s
        """, (user_id,))
        profile = cur.fetchone()
        if profile:
            print(f"  - Profile Role: {profile['role']}")
        else:
            print(f"  - Profile: 없음")
        
        # 3. Study 찾기
        print(f"\n[2] Study 정보:")
        cur.execute("""
            SELECT id, title_ko, title_en, is_public, created_by_id
            FROM quiz_study
            WHERE id = %s
        """, (study_id,))
        study = cur.fetchone()
        
        if not study:
            print(f"  [오류] Study를 찾을 수 없습니다: ID {study_id}")
            return
        
        print(f"  - ID: {study['id']}")
        print(f"  - Title KO: {study['title_ko']}")
        print(f"  - Title EN: {study['title_en']}")
        print(f"  - Is Public: {study['is_public']}")
        print(f"  - Created By ID: {study['created_by_id']}")
        
        if study['created_by_id']:
            cur.execute("""
                SELECT id, username, email
                FROM quiz_user
                WHERE id = %s
            """, (study['created_by_id'],))
            creator = cur.fetchone()
            if creator:
                print(f"  - Created By Username: {creator['username']}")
                print(f"  - Created By Email: {creator['email']}")
                print(f"  - 현재 사용자가 생성자인가? {study['created_by_id'] == user_id}")
        
        # 4. Member 관계 확인
        print(f"\n[3] Member 관계 확인:")
        cur.execute("""
            SELECT id, user_id, role, is_active, joined_at
            FROM quiz_member
            WHERE study_id = %s AND user_id = %s
        """, (study_id, user_id))
        members = cur.fetchall()
        
        print(f"  - Member 레코드 수: {len(members)}")
        
        if members:
            for member in members:
                print(f"\n  Member ID: {member['id']}")
                print(f"    - User ID: {member['user_id']}")
                print(f"    - Role: {member['role']}")
                print(f"    - Is Active: {member['is_active']}")
                print(f"    - Joined At: {member['joined_at']}")
                
                is_study_admin = member['is_active'] and member['role'] in ['study_admin', 'study_leader']
                print(f"    - 관리자 권한 있는가? {is_study_admin}")
        else:
            print(f"  - 해당 사용자는 이 Study의 멤버가 아닙니다.")
        
        # 5. 전체 멤버 목록 (참고용)
        cur.execute("""
            SELECT m.id, m.user_id, m.role, m.is_active, u.username, u.email
            FROM quiz_member m
            JOIN quiz_user u ON m.user_id = u.id
            WHERE m.study_id = %s
            ORDER BY m.joined_at
            LIMIT 10
        """, (study_id,))
        all_members = cur.fetchall()
        
        cur.execute("SELECT COUNT(*) as total FROM quiz_member WHERE study_id = %s", (study_id,))
        total_members = cur.fetchone()['total']
        
        print(f"\n[4] 전체 멤버 목록 (Study ID {study_id}):")
        print(f"  총 {total_members}명")
        for member in all_members:
            print(f"    - {member['username']} ({member['email']}) - Role: {member['role']}, Active: {member['is_active']}")
        if total_members > 10:
            print(f"    ... 외 {total_members - 10}명")
        
        # 6. 권한 요약
        print(f"\n" + "=" * 60)
        print(f"[권한 요약]")
        print(f"=" * 60)
        
        # 전역 관리자 확인
        is_admin = user['is_superuser'] or (profile and profile['role'] == 'admin_role')
        
        # Study 생성자 확인
        is_creator = study['created_by_id'] == user_id
        
        # Study 관리자 확인
        is_study_admin = False
        if members:
            for member in members:
                if member['is_active'] and member['role'] in ['study_admin', 'study_leader']:
                    is_study_admin = True
                    break
        
        print(f"  - 전역 관리자: {is_admin}")
        print(f"  - Study 생성자: {is_creator}")
        print(f"  - Study 관리자: {is_study_admin}")
        print(f"  - 편집 가능: {is_admin or is_creator or is_study_admin}")
        
        if not (is_admin or is_creator or is_study_admin):
            print(f"\n[문제 진단]")
            print(f"  편집 권한이 없는 이유:")
            if not is_admin:
                print(f"    - 전역 관리자 권한 없음 (is_superuser={user['is_superuser']}, role={profile['role'] if profile else 'None'})")
            if not is_creator:
                print(f"    - Study 생성자가 아님 (생성자 ID: {study['created_by_id']}, 현재 사용자 ID: {user_id})")
            if not is_study_admin:
                print(f"    - Study 관리자 권한 없음")
                if members:
                    for member in members:
                        if not member['is_active']:
                            print(f"      - 멤버십이 비활성화됨 (Member ID: {member['id']})")
                        if member['role'] not in ['study_admin', 'study_leader']:
                            print(f"      - 역할이 관리자가 아님 (현재 역할: {member['role']})")
                else:
                    print(f"      - 멤버가 아님")
        
        # 7. 해결 방안
        print(f"\n" + "=" * 60)
        print(f"[해결 방안]")
        print(f"=" * 60)
        if not is_creator and not is_study_admin:
            print(f"권한을 부여하려면 다음 중 하나를 수행하세요:")
            print(f"\n1. Study 생성자로 변경:")
            print(f"   UPDATE quiz_study SET created_by_id = {user_id} WHERE id = {study_id};")
            print(f"\n2. Study 관리자로 추가 (또는 역할 변경):")
            if members:
                print(f"   UPDATE quiz_member SET role = 'study_admin', is_active = true WHERE id = {members[0]['id']};")
            else:
                print(f"   INSERT INTO quiz_member (study_id, user_id, role, is_active, joined_at)")
                print(f"   VALUES ({study_id}, {user_id}, 'study_admin', true, NOW());")
            print(f"\n3. 전역 관리자로 변경:")
            print(f"   UPDATE quiz_user SET is_superuser = true WHERE id = {user_id};")
            print(f"   또는")
            if profile:
                print(f"   UPDATE quiz_userprofile SET role = 'admin_role' WHERE user_id = {user_id};")
            else:
                print(f"   INSERT INTO quiz_userprofile (user_id, role) VALUES ({user_id}, 'admin_role');")
        
        cur.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"\n[DB 오류] {e}")
    except Exception as e:
        print(f"\n[오류] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_study_permission()


