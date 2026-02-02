#!/usr/bin/env python3
"""
Ticktok_Algorithm.xlsx로 import된 문제들의 데이터베이스 상태 확인 스크립트
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

from quiz.models import Question, Exam, ExamQuestion

def check_ticktok_questions():
    """Ticktok_Algorithm.xlsx로 import된 문제들의 상태 확인"""
    try:
        print("🔍 Ticktok_Algorithm.xlsx 문제들 상태 확인")
        print("=" * 60)
        
        # csv_id가 Ticktok_Algorithm.xlsx인 문제들 찾기
        questions = Question.objects.filter(csv_id='Ticktok_Algorithm.xlsx')
        
        print(f"📊 총 문제 수: {questions.count()}")
        print("=" * 60)
        
        if questions.count() == 0:
            print("❌ csv_id가 'Ticktok_Algorithm.xlsx'인 문제가 없습니다.")
            return
        
        # 각 문제의 상세 정보 출력
        for i, question in enumerate(questions, 1):
            print(f"\n--- 문제 {i} ---")
            print(f"UUID: {question.id}")
            print(f"CSV ID: {question.csv_id}")
            print(f"제목 (한국어): {question.title_ko}")
            print(f"제목 (영어): {question.title_en}")
            print(f"내용 길이 (한국어): {len(question.content_ko) if question.content_ko else 0}")
            print(f"내용 길이 (영어): {len(question.content_en) if question.content_en else 0}")
            print(f"내용 미리보기 (한국어): {question.content_ko[:100] if question.content_ko else '없음'}...")
            print(f"내용 미리보기 (영어): {question.content_en[:100] if question.content_en else '없음'}...")
            print(f"정답 (한국어): {question.answer_ko}")
            print(f"정답 (영어): {question.answer_en}")
            print(f"난이도: {question.difficulty}")
            print(f"그룹 ID: {question.group_id}")
            print(f"URL: {question.url}")
            print(f"생성일: {question.created_at}")
            print(f"수정일: {question.updated_at}")
            
            # 시험 연결 상태 확인
            exam_questions = ExamQuestion.objects.filter(question=question)
            print(f"연결된 시험 수: {exam_questions.count()}")
            for eq in exam_questions:
                print(f"  - 시험: {eq.exam.title_ko or eq.exam.title_en or 'Unknown'} (ID: {eq.exam.id})")
                print(f"    순서: {eq.order}")
            
            print("-" * 40)
        
        # 중복 제목 확인
        print("\n🔍 중복 제목 확인:")
        title_counts = {}
        for question in questions:
            title = question.title_ko or question.title_en or '제목 없음'
            if title in title_counts:
                title_counts[title] += 1
            else:
                title_counts[title] = 1
        
        duplicates = {title: count for title, count in title_counts.items() if count > 1}
        if duplicates:
            print("❌ 중복 제목 발견:")
            for title, count in duplicates.items():
                print(f"  - '{title}': {count}개")
        else:
            print("✅ 중복 제목 없음")
        
        # 다른 csv_id를 가진 문제들도 확인
        print("\n🔍 다른 csv_id를 가진 문제들:")
        other_questions = Question.objects.exclude(csv_id='Ticktok_Algorithm.xlsx')
        csv_id_counts = {}
        for question in other_questions:
            csv_id = question.csv_id or 'None'
            if csv_id in csv_id_counts:
                csv_id_counts[csv_id] += 1
            else:
                csv_id_counts[csv_id] = 1
        
        # 상위 10개 csv_id 출력
        sorted_csv_ids = sorted(csv_id_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        for csv_id, count in sorted_csv_ids:
            print(f"  - {csv_id}: {count}개")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_ticktok_questions()
