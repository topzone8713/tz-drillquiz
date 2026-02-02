#!/usr/bin/env python3
"""
기존 문제들의 difficulty를 업데이트하는 스크립트
LeetCode 문제의 description에서 difficulty를 파싱하여 업데이트합니다.
"""

import os
import sys
import django
import re

# Django 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
django.setup()

from quiz.models import Question, Exam
from django.db import transaction

def normalize_difficulty(difficulty):
    """난이도를 정규화합니다."""
    if not difficulty:
        return 'unknown'
    
    diff = difficulty.lower()
    if 'easy' in diff:
        return 'easy'
    elif 'med' in diff or 'medium' in diff:
        return 'medium'
    elif 'hard' in diff:
        return 'hard'
    else:
        return 'unknown'

def parse_difficulty_from_description(description):
    """description에서 difficulty를 파싱합니다."""
    if not description:
        return None
    
    lines = description.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # LeetCode 문제 형식 파싱: "146. LRU Cache\n45.9%\nMed."
        problem_match = re.match(r'^(\d+)\.\s+(.+)$', line)
        if problem_match:
            # 다음 줄들에서 난이도 찾기
            current_index = lines.index(line)
            for i, next_line in enumerate(lines[current_index+1:current_index+4]):
                if not next_line.strip():
                    continue
                    
                # 난이도 찾기 (Easy, Med., Hard)
                difficulty_match = re.search(r'(Easy|Med\.?|Medium|Hard)', next_line, re.IGNORECASE)
                if difficulty_match:
                    return normalize_difficulty(difficulty_match.group(1))
    
    return None

def update_question_difficulties():
    """기존 문제들의 difficulty를 업데이트합니다."""
    print("🔍 기존 문제들의 difficulty 업데이트 시작...")
    
    updated_count = 0
    total_count = 0
    
    # difficulty가 'unknown'이거나 빈 문제들을 찾아서 업데이트
    questions = Question.objects.filter(
        models.Q(difficulty='unknown') | 
        models.Q(difficulty='') | 
        models.Q(difficulty__isnull=True)
    )
    
    print(f"📊 업데이트 대상 문제 수: {questions.count()}")
    
    for question in questions:
        total_count += 1
        
        # 해당 문제가 포함된 시험의 description에서 difficulty 파싱
        exam_questions = question.examquestion_set.all()
        parsed_difficulty = None
        
        for eq in exam_questions:
            exam = eq.exam
            description = exam.description_ko or exam.description_en
            if description:
                parsed_difficulty = parse_difficulty_from_description(description)
                if parsed_difficulty and parsed_difficulty != 'unknown':
                    break
        
        if parsed_difficulty and parsed_difficulty != 'unknown':
            print(f"✅ 문제 {question.id} difficulty 업데이트: {question.difficulty} -> {parsed_difficulty}")
            question.difficulty = parsed_difficulty
            question.save()
            updated_count += 1
        else:
            print(f"⏭️ 문제 {question.id} difficulty 파싱 실패: {question.title_ko or question.title_en}")
    
    print(f"🎉 업데이트 완료: {updated_count}/{total_count} 문제")

if __name__ == '__main__':
    from django.db import models
    update_question_difficulties()
