#!/usr/bin/env python3
"""
'월마트 DevOps interview Prep2' 스터디의 title_ko와 title_en 값을 확인하는 스크립트
"""

import os
import sys
import django
from pathlib import Path

# Django 설정 로드
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
django.setup()

from quiz.models import Study

def check_study_titles():
    """스터디 제목 데이터 확인"""
    print("=" * 60)
    print("스터디 제목 데이터 확인")
    print("=" * 60)
    
    # '월마트'가 포함된 스터디 찾기
    studies = Study.objects.filter(title_ko__icontains='월마트')
    
    if not studies.exists():
        print("\n'월마트'가 포함된 스터디를 찾을 수 없습니다.")
        print("\n모든 스터디의 제목 샘플 (최근 10개):")
        studies = Study.objects.all().order_by('-id')[:10]
    else:
        print(f"\n'월마트'가 포함된 스터디: {studies.count()}개")
    
    print("\n" + "-" * 60)
    for study in studies:
        print(f"\nID: {study.id}")
        print(f"  title_ko: {repr(study.title_ko)}")
        print(f"  title_en: {repr(study.title_en)}")
        print(f"  created_language: {study.created_language}")
        print(f"  is_ko_complete: {study.is_ko_complete}")
        print(f"  is_en_complete: {study.is_en_complete}")
        
        # EN 모드에서 표시될 제목 확인
        if study.title_en:
            print(f"  → EN 모드 표시: {study.title_en}")
        else:
            print(f"  → EN 모드 표시: {study.title_ko} (title_en이 비어있어서 title_ko fallback)")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    check_study_titles()

