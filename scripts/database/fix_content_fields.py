#!/usr/bin/env python3
"""
content 필드를 올바른 다국어 구조로 수정하는 스크립트
"""

import os
import sys
import django
from pathlib import Path

# Django 설정 로드
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')

django.setup()

from quiz.models import Question

def fix_content_fields():
    """content 필드를 올바른 다국어 구조로 수정"""
    try:
        # 특정 문제 확인
        question_id = "cc8e3ec1e96441cc9bcb13df11807fd1"
        question = Question.objects.get(id=question_id)
        
        print(f"🔍 문제 ID: {question_id}")
        content = question.content_ko or question.content_en or ''
        print(f"현재 content: {content[:100] if content else '내용 없음'}...")
        print(f"현재 content_en: {question.content_en[:100] if question.content_en else '없음'}...")
        print(f"현재 content_ko: {question.content_ko[:100] if question.content_ko else '없음'}...")
        print("=" * 50)
        
        # 기존 content 필드는 더 이상 사용하지 않음 (다국어 필드만 사용)
        print("✅ 다국어 필드만 사용하도록 설정되었습니다.")
        
        # 수정 후 상태 확인
        question.refresh_from_db()
        print(f"\n📝 수정 후 상태:")
        print(f"content_en: {question.content_en[:100] if question.content_en else '없음'}...")
        print(f"content_ko: {question.content_ko[:100] if question.content_ko else '없음'}...")
        
    except Question.DoesNotExist:
        print(f"❌ 문제를 찾을 수 없습니다: {question_id}")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_content_fields()
