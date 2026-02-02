#!/usr/bin/env python
"""
사용자 프로필의 role이 없거나 비어있는 경우 수정하는 스크립트
"""

import os
import sys
import django

# Django 설정
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
django.setup()

from django.contrib.auth import get_user_model
from quiz.models import UserProfile
from quiz.utils.multilingual_utils import BASE_LANGUAGE

User = get_user_model()

def fix_user_profile_roles():
    """프로필의 role이 없거나 비어있는 사용자를 수정"""
    users = User.objects.all()
    fixed_count = 0
    created_count = 0
    
    print("=" * 60)
    print("사용자 프로필 role 수정 시작")
    print("=" * 60)
    
    for user in users:
        try:
            profile = user.profile
            # role이 없거나 비어있는 경우
            if not profile.role or profile.role == '':
                profile.role = 'user_role'
                profile.save()
                print(f"✅ {user.username} (ID: {user.id}): role을 'user_role'로 설정")
                fixed_count += 1
            else:
                print(f"✓ {user.username} (ID: {user.id}): role = {profile.role} (변경 불필요)")
        except UserProfile.DoesNotExist:
            # 프로필이 없는 경우 생성
            UserProfile.objects.create(
                user=user,
                role='user_role',
                language=BASE_LANGUAGE,  # 기본 언어는 'en'
                email_verified=False,
                retention_cleanup_enabled=True,
                random_exam_email_enabled=True
            )
            print(f"✅ {user.username} (ID: {user.id}): 프로필 생성 (role='user_role')")
            created_count += 1
    
    print("=" * 60)
    print(f"완료: {fixed_count}개 프로필 수정, {created_count}개 프로필 생성")
    print("=" * 60)

if __name__ == "__main__":
    fix_user_profile_roles()

