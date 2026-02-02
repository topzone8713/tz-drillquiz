#!/usr/bin/env python3
import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
django.setup()

import pandas as pd
from quiz.models import Question, Exam, ExamQuestion

def create_paypal_questions():
    # 엑셀 파일 읽기
    df = pd.read_excel('/tmp/Paypal_Algorithm.xlsx')
    print(f'엑셀에서 읽은 문제 수: {len(df)}')
    
    # 시험 가져오기
    exam = Exam.objects.get(id='06ce4c24-2837-451e-8a36-16d79f5987ea')
    print(f'시험: {exam.title}')
    
    created_questions = []
    
    # 각 행을 순회하며 문제 생성
    for idx, row in df.iterrows():
        try:
            # 문제 생성
            question = Question.objects.create(
                title=row['제목'],
                content=row['문제 내용'],
                answer=row['정답'],
                explanation=row['설명'],
                difficulty=row['난이도'],
                url=row['URL'],
                csv_id=str(row['문제id'])
            )
            created_questions.append(question)
            print(f'생성됨: {question.title} - 난이도: {question.difficulty}')
        except Exception as e:
            print(f'오류 발생: {row["제목"]} - {e}')
    
    print(f'총 {len(created_questions)}개 문제 생성 완료')
    
    # 시험에 문제 연결
    for i, question in enumerate(created_questions):
        ExamQuestion.objects.create(
            exam=exam,
            question=question,
            order=i + 1
        )
        print(f'시험에 연결됨: {question.title}')
    
    print('모든 문제가 시험에 연결되었습니다.')

if __name__ == '__main__':
    create_paypal_questions() 