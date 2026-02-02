#!/usr/bin/env python3
"""
새로 추가된 문제들의 다국어 title 필드를 수정하는 스크립트
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

def fix_new_questions_titles():
    """새로 추가된 문제들의 다국어 title 필드를 수정"""
    try:
        # csv_id가 2, 3인 문제들 확인
        questions = Question.objects.filter(csv_id__in=['2', '3'])
        
        print(f"🔍 수정할 문제 수: {questions.count()}")
        print("=" * 50)
        
        for question in questions:
            print(f"문제 ID: {question.id}")
            print(f"CSV ID: {question.csv_id}")
            print(f"현재 title: {question.title}")
            print(f"현재 title_ko: {question.title_ko}")
            print(f"현재 title_en: {question.title_en}")
            
            # title이 있지만 title_ko나 title_en이 비어있는 경우
            if question.title and (not question.title_ko or not question.title_en):
                # title을 title_ko와 title_en에 복사
                if not question.title_ko:
                    question.title_ko = question.title
                    print("✅ title_ko 설정됨")
                
                if not question.title_en:
                    question.title_en = question.title
                    print("✅ title_en 설정됨")
                
                question.save()
                print("✅ 저장 완료")
            else:
                print("ℹ️ 수정 불필요")
            
            print("-" * 30)
        
        # 수정 후 상태 확인
        print("\n📝 수정 후 상태:")
        for question in questions:
            question.refresh_from_db()
            print(f"CSV ID {question.csv_id}:")
            print(f"  title: {question.title[:50]}...")
            print(f"  title_ko: {question.title_ko[:50] if question.title_ko else '없음'}...")
            print(f"  title_en: {question.title_en[:50] if question.title_en else '없음'}...")
            print()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_new_questions_titles()
