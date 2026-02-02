#!/usr/bin/env python
import os
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

print("=== 비밀번호 재설정 ===")

try:
    user = User.objects.get(username='doohee323')
    print(f"사용자: {user.username}")
    
    # 비밀번호를 'password123'으로 설정
    user.set_password('password123')
    user.save()
    
    print("✅ 비밀번호가 'password123'으로 재설정되었습니다.")
    
except User.DoesNotExist:
    print("사용자를 찾을 수 없습니다.")
except Exception as e:
    print(f"오류 발생: {e}") 