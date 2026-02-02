#!/usr/bin/env python3
"""
태그 삭제 스크립트
사용법: python scripts/delete_tag.py <태그명>
예시: python scripts/delete_tag.py culture1
"""

import os
import sys
import django

# Django 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
django.setup()

from quiz.models import Tag
from django.db import models

def delete_tag(tag_name):
    """태그를 삭제하는 함수"""
    try:
        # 태그 찾기 (한국어 또는 영어 이름으로 검색)
        tag = Tag.objects.filter(
            models.Q(name_ko=tag_name) | models.Q(name_en=tag_name)
        ).first()
        
        if not tag:
            print(f"❌ 태그 '{tag_name}'을(를) 찾을 수 없습니다.")
            print("\n사용 가능한 태그 목록:")
            all_tags = Tag.objects.all().order_by('name_ko')[:20]
            for t in all_tags:
                print(f"  - {t.name_ko} (ID: {t.id})")
            return False
        
        # 태그 정보 출력
        print(f"📋 태그 정보:")
        print(f"  - ID: {tag.id}")
        print(f"  - 한국어 이름: {tag.name_ko}")
        print(f"  - 영어 이름: {tag.name_en}")
        print(f"  - 생성일: {tag.created_at}")
        
        # 확인
        confirm = input(f"\n⚠️  태그 '{tag.name_ko}'을(를) 삭제하시겠습니까? (yes/no): ")
        if confirm.lower() not in ['yes', 'y']:
            print("❌ 삭제가 취소되었습니다.")
            return False
        
        # 태그 삭제
        tag.delete()
        print(f"✅ 태그 '{tag.name_ko}'이(가) 성공적으로 삭제되었습니다.")
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("사용법: python scripts/delete_tag.py <태그명>")
        print("예시: python scripts/delete_tag.py culture1")
        sys.exit(1)
    
    tag_name = sys.argv[1]
    success = delete_tag(tag_name)
    sys.exit(0 if success else 1)

