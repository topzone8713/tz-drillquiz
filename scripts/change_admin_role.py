#!/usr/bin/env python
"""
Admin 계정을 시스템 어드민 권한으로 변경하는 스크립트
"""

import os
import sys
import django

# Django 설정 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
django.setup()

from django.contrib.auth.models import User
from quiz.models import UserProfile
from quiz.utils.multilingual_utils import BASE_LANGUAGE

def change_admin_to_system_admin():
    """admin 계정을 시스템 어드민 권한으로 변경"""
    try:
        # admin 사용자 찾기
        admin_user = User.objects.get(username='admin')
        print(f"✅ Admin 사용자 찾음: {admin_user.username} (ID: {admin_user.id})")
        
        # UserProfile 가져오기 (없으면 생성)
        user_profile, created = UserProfile.objects.get_or_create(
            user=admin_user,
            defaults={
                'role': 'admin_role',
                'language': BASE_LANGUAGE,  # 기본 언어는 'en'
                'email_verification_sent_at': None,
                'email_verified': False,
                'random_exam_email_enabled': False,
                'retention_cleanup_enabled': False
            }
        )
        
        if created:
            print(f"✅ UserProfile 생성됨")
        else:
            print(f"✅ UserProfile 찾음: {user_profile.role}")
        
        # 시스템 어드민 권한으로 변경
        user_profile.role = 'admin_role'
        user_profile.save()
        
        print(f"✅ Admin 사용자 권한 변경 완료: {user_profile.role}")
        
        # 사용자 정보 출력
        print(f"\n📋 사용자 정보:")
        print(f"   - Username: {admin_user.username}")
        print(f"   - Email: {admin_user.email}")
        print(f"   - First Name: {admin_user.first_name}")
        print(f"   - Last Name: {admin_user.last_name}")
        print(f"   - Is Staff: {admin_user.is_staff}")
        print(f"   - Is Superuser: {admin_user.is_superuser}")
        print(f"   - Role: {user_profile.role}")
        print(f"   - Language: {user_profile.language}")
        
        return True
        
    except User.DoesNotExist:
        print("❌ Admin 사용자를 찾을 수 없습니다.")
        return False
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Admin 계정을 시스템 어드민 권한으로 변경합니다...")
    success = change_admin_to_system_admin()
    
    if success:
        print("\n✅ 권한 변경이 완료되었습니다!")
    else:
        print("\n❌ 권한 변경에 실패했습니다.")
        sys.exit(1)
