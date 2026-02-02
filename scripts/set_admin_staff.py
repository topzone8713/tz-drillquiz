#!/usr/bin/env python
"""
Admin 계정을 Django staff와 superuser로 설정하는 스크립트
"""

import os
import sys
import django

# Django 설정 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
django.setup()

from django.contrib.auth.models import User

def set_admin_staff_and_superuser():
    """admin 계정을 Django staff와 superuser로 설정"""
    try:
        # admin 사용자 찾기
        admin_user = User.objects.get(username='admin')
        print(f"✅ Admin 사용자 찾음: {admin_user.username} (ID: {admin_user.id})")
        
        # Staff 권한 설정
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()
        
        print(f"✅ Admin 사용자 권한 설정 완료")
        print(f"   - Is Staff: {admin_user.is_staff}")
        print(f"   - Is Superuser: {admin_user.is_superuser}")
        
        # 사용자 정보 출력
        print(f"\n📋 사용자 정보:")
        print(f"   - Username: {admin_user.username}")
        print(f"   - Email: {admin_user.email}")
        print(f"   - First Name: {admin_user.first_name}")
        print(f"   - Last Name: {admin_user.last_name}")
        print(f"   - Is Staff: {admin_user.is_staff}")
        print(f"   - Is Superuser: {admin_user.is_superuser}")
        
        return True
        
    except User.DoesNotExist:
        print("❌ Admin 사용자를 찾을 수 없습니다.")
        return False
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Admin 계정을 Django staff와 superuser로 설정합니다...")
    success = set_admin_staff_and_superuser()
    
    if success:
        print("\n✅ 권한 설정이 완료되었습니다!")
    else:
        print("\n❌ 권한 설정에 실패했습니다.")
        sys.exit(1)
