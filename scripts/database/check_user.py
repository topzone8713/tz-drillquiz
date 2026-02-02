#!/usr/bin/env python
import os
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

print("=== 사용자 정보 확인 ===")

try:
    user = User.objects.get(username='doohee323')
    print(f"사용자명: {user.username}")
    print(f"이메일: {user.email}")
    print(f"마지막 로그인: {user.last_login}")
    print(f"가입일: {user.date_joined}")
    
    # 비밀번호 확인 (실제로는 확인할 수 없지만 사용자 존재 여부 확인)
    print(f"사용자 존재: {user is not None}")
    
except User.DoesNotExist:
    print("사용자를 찾을 수 없습니다.")
    
    # 모든 사용자 목록 출력
    print("\n=== 모든 사용자 목록 ===")
    users = User.objects.all()
    for u in users:
        print(f"- {u.username} (ID: {u.id})") 