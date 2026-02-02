#!/usr/bin/env python
"""
Study 권한 문제 진단 스크립트
study-detail/24에서 doohee323@gmail.com 사용자의 권한을 확인합니다.
"""
import os
import sys
import django

# Django 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
django.setup()

from django.contrib.auth import get_user_model
from quiz.models import Study, Member
from quiz.utils.permissions import has_study_specific_admin_permission, get_user_permissions

User = get_user_model()

def check_study_permission():
    email = 'doohee323@gmail.com'
    study_id = 24
    
    print(f"=" * 60)
    print(f"Study 권한 진단: Study ID {study_id}")
    print(f"사용자 이메일: {email}")
    print(f"=" * 60)
    
    # 1. 사용자 찾기
    try:
        user = User.objects.get(email=email)
        print(f"\n[1] 사용자 정보:")
        print(f"  - ID: {user.id}")
        print(f"  - Username: {user.username}")
        print(f"  - Email: {user.email}")
        print(f"  - Is Superuser: {user.is_superuser}")
        if hasattr(user, 'profile'):
            print(f"  - Profile Role: {user.profile.role}")
        else:
            print(f"  - Profile: 없음")
    except User.DoesNotExist:
        print(f"\n[오류] 사용자를 찾을 수 없습니다: {email}")
        return
    except User.MultipleObjectsReturned:
        users = User.objects.filter(email=email)
        print(f"\n[경고] 동일한 이메일의 사용자가 {users.count()}명 있습니다:")
        for u in users:
            print(f"  - ID: {u.id}, Username: {u.username}")
        user = users.first()
        print(f"\n첫 번째 사용자를 사용합니다: ID {user.id}")
    
    # 2. 사용자 권한 확인
    print(f"\n[2] 전역 권한 확인:")
    permissions = get_user_permissions(user)
    print(f"  - is_admin: {permissions.get('is_admin')}")
    print(f"  - has_study_admin_role: {permissions.get('has_study_admin_role')}")
    print(f"  - user_role: {permissions.get('user_role')}")
    
    # 3. Study 찾기
    try:
        study = Study.objects.get(id=study_id)
        print(f"\n[3] Study 정보:")
        print(f"  - ID: {study.id}")
        print(f"  - Title KO: {study.title_ko}")
        print(f"  - Title EN: {study.title_en}")
        print(f"  - Is Public: {study.is_public}")
        
        # created_by 확인
        if study.created_by:
            created_by_id = study.created_by.id if hasattr(study.created_by, 'id') else study.created_by
            created_by_user = User.objects.get(id=created_by_id) if isinstance(created_by_id, int) else None
            print(f"  - Created By ID: {created_by_id}")
            if created_by_user:
                print(f"  - Created By Username: {created_by_user.username}")
                print(f"  - Created By Email: {created_by_user.email}")
                print(f"  - 현재 사용자가 생성자인가? {created_by_id == user.id}")
        else:
            print(f"  - Created By: None")
    except Study.DoesNotExist:
        print(f"\n[오류] Study를 찾을 수 없습니다: ID {study_id}")
        return
    
    # 4. Member 관계 확인
    print(f"\n[4] Member 관계 확인:")
    members = Member.objects.filter(study=study, user=user)
    print(f"  - Member 레코드 수: {members.count()}")
    
    if members.exists():
        for member in members:
            print(f"\n  Member ID: {member.id}")
            print(f"    - User ID: {member.user.id}")
            print(f"    - Role: {member.role}")
            print(f"    - Is Active: {member.is_active}")
            print(f"    - Joined At: {member.joined_at}")
            
            # 역할별 권한 확인
            is_study_admin = member.is_active and member.role in ['study_admin', 'study_leader']
            print(f"    - 관리자 권한 있는가? {is_study_admin}")
    else:
        print(f"  - 해당 사용자는 이 Study의 멤버가 아닙니다.")
    
    # 5. 전체 멤버 목록 (참고용)
    all_members = Member.objects.filter(study=study).select_related('user')
    print(f"\n[5] 전체 멤버 목록 (Study ID {study_id}):")
    print(f"  총 {all_members.count()}명")
    for member in all_members[:10]:  # 최대 10명만 표시
        user_email = member.user.email if hasattr(member.user, 'email') else 'N/A'
        print(f"    - {member.user.username} ({user_email}) - Role: {member.role}, Active: {member.is_active}")
    if all_members.count() > 10:
        print(f"    ... 외 {all_members.count() - 10}명")
    
    # 6. 권한 체크 함수 테스트
    print(f"\n[6] 권한 체크 함수 테스트:")
    has_admin = has_study_specific_admin_permission(user, study)
    print(f"  - has_study_specific_admin_permission(): {has_admin}")
    
    # 7. isStudyCreator 확인
    print(f"\n[7] isStudyCreator 확인:")
    if study.created_by:
        created_by_id = study.created_by.id if hasattr(study.created_by, 'id') else study.created_by
        is_creator = created_by_id == user.id
        print(f"  - Created By ID: {created_by_id}")
        print(f"  - Current User ID: {user.id}")
        print(f"  - Is Creator: {is_creator}")
    else:
        print(f"  - Created By가 없음")
    
    # 8. 권한 요약
    print(f"\n" + "=" * 60)
    print(f"[권한 요약]")
    print(f"=" * 60)
    is_admin = permissions.get('is_admin') or permissions.get('has_study_admin_role')
    is_creator = study.created_by and (
        (hasattr(study.created_by, 'id') and study.created_by.id == user.id) or
        (not hasattr(study.created_by, 'id') and study.created_by == user.id)
    )
    is_study_admin = has_study_specific_admin_permission(user, study)
    
    print(f"  - 전역 관리자: {is_admin}")
    print(f"  - Study 생성자: {is_creator}")
    print(f"  - Study 관리자: {is_study_admin}")
    print(f"  - 편집 가능: {is_admin or is_creator or is_study_admin}")
    
    if not (is_admin or is_creator or is_study_admin):
        print(f"\n[문제 진단]")
        print(f"  편집 권한이 없는 이유:")
        if not is_admin:
            print(f"    - 전역 관리자 권한 없음")
        if not is_creator:
            print(f"    - Study 생성자가 아님 (생성자 ID: {created_by_id if study.created_by else 'None'})")
        if not is_study_admin:
            print(f"    - Study 관리자 권한 없음")
            if members.exists():
                for member in members:
                    if not member.is_active:
                        print(f"      - 멤버십이 비활성화됨 (Member ID: {member.id})")
                    if member.role not in ['study_admin', 'study_leader']:
                        print(f"      - 역할이 관리자가 아님 (현재 역할: {member.role})")
            else:
                print(f"      - 멤버가 아님")

if __name__ == '__main__':
    check_study_permission()


