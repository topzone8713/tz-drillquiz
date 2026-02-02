#!/usr/bin/env python3
"""
기존 문제들의 source_id를 업데이트하는 스크립트
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

def update_existing_questions_source_id():
    """기존 문제들의 source_id를 업데이트"""
    try:
        print("🔧 기존 문제들의 source_id 업데이트 시작")
        print("=" * 60)
        
        # source_id가 비어있는 문제들 찾기
        questions_without_source = Question.objects.filter(source_id__isnull=True)
        print(f"📊 source_id가 없는 문제 수: {questions_without_source.count()}")
        
        if questions_without_source.count() == 0:
            print("✅ 모든 문제에 source_id가 이미 설정되어 있습니다.")
            return
        
        updated_count = 0
        
        # 각 문제에 대해 source_id 설정
        for question in questions_without_source:
            # 해당 문제가 연결된 시험 찾기
            exam_questions = ExamQuestion.objects.filter(question=question)
            
            if exam_questions.exists():
                # 첫 번째 시험의 file_name을 source_id로 사용
                exam = exam_questions.first().exam
                if exam.file_name:
                    question.source_id = exam.file_name
                    question.save()
                    updated_count += 1
                    print(f"✅ 문제 {question.id} ({question.title_ko or question.title_en or '제목 없음'}) -> source_id: {exam.file_name}")
                else:
                    # file_name이 없는 경우 csv_id를 기반으로 추정
                    if question.csv_id and question.csv_id.isdigit():
                        question.source_id = f"legacy_source_{question.csv_id}"
                    else:
                        question.source_id = "unknown_source"
                    question.save()
                    updated_count += 1
                    print(f"⚠️ 문제 {question.id} ({question.title_ko or question.title_en or '제목 없음'}) -> source_id: {question.source_id} (추정값)")
            else:
                # 시험에 연결되지 않은 문제
                if question.csv_id and question.csv_id.isdigit():
                    question.source_id = f"orphaned_{question.csv_id}"
                else:
                    question.source_id = "orphaned_unknown"
                question.save()
                updated_count += 1
                print(f"⚠️ 문제 {question.id} ({question.title_ko or question.title_en or '제목 없음'}) -> source_id: {question.source_id} (연결되지 않음)")
        
        print(f"\n📝 업데이트 완료: {updated_count}개 문제")
        
        # 업데이트 후 상태 확인
        print("\n🔍 업데이트 후 상태:")
        source_id_counts = {}
        for question in Question.objects.all():
            source_id = question.source_id or 'None'
            if source_id in source_id_counts:
                source_id_counts[source_id] += 1
            else:
                source_id_counts[source_id] = 1
        
        # 상위 10개 source_id 출력
        sorted_source_ids = sorted(source_id_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        for source_id, count in sorted_source_ids:
            print(f"  - {source_id}: {count}개")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    update_existing_questions_source_id()
