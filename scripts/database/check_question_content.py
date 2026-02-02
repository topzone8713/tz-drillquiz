#!/usr/bin/env python3
"""
특정 문제의 content 확인 스크립트
"""

import os
import sys
import django
from pathlib import Path

# Django 설정 로드
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '51370'
os.environ['POSTGRES_DB'] = 'drillquiz'
os.environ['POSTGRES_USER'] = 'postgres'
os.environ['POSTGRES_PASSWORD'] = 'DevOps!323'
os.environ['USE_DOCKER'] = 'true'

django.setup()

from quiz.models import Question

def check_question_content():
    """특정 문제의 content 확인"""
    try:
        # URL에서 추출한 exam ID
        exam_id = "f31d469b-9b98-4b95-817e-8c106b1edb94"
        
        print(f"🔍 시험 ID: {exam_id}")
        print("=" * 50)
        
        # 해당 시험에 속한 문제들 확인
        from quiz.models import Exam, StudyTask
        
        try:
            exam = Exam.objects.get(id=exam_id)
            print(f"📝 시험 제목: {exam.title}")
            print(f"📝 시험 설명: {exam.description}")
            
            # 시험에 속한 문제들 확인
            study_tasks = StudyTask.objects.filter(exam=exam)
            print(f"\n📋 시험에 속한 문제 수: {study_tasks.count()}")
            
            for i, task in enumerate(study_tasks, 1):
                question = task.question
                print(f"\n--- 문제 {i} ---")
                print(f"문제 ID: {question.id}")
                print(f"CSV ID: {question.csv_id}")
                print(f"제목 (한국어): {question.title_ko}")
                print(f"제목 (영어): {question.title_en}")
                print(f"내용 길이 (한국어): {len(question.content_ko) if question.content_ko else 0}")
                print(f"내용 길이 (영어): {len(question.content_en) if question.content_en else 0}")
                print(f"내용 미리보기 (한국어): {question.content_ko[:200] if question.content_ko else '없음'}...")
                print(f"내용 미리보기 (영어): {question.content_en[:200] if question.content_en else '없음'}...")
                print(f"난이도: {question.difficulty}")
                print(f"그룹 ID: {question.group_id}")
                print(f"URL: {question.url}")
                
                if question.content_ko or question.content_en:
                    print(f"✅ Content 있음")
                else:
                    print(f"❌ Content 없음")
                    
        except Exam.DoesNotExist:
            print(f"❌ 시험을 찾을 수 없습니다: {exam_id}")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_question_content()
