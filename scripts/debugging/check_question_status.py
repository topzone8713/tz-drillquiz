#!/usr/bin/env python
import os
import sys
import django

# Django 설정을 위해 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Django 환경 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
django.setup()

from quiz.models import Question, IgnoredQuestion, Exam, ExamQuestion
from django.contrib.auth.models import User
from django.db import models

def check_question_status():
    """문제의 Favorite과 Ignored 상태를 확인합니다."""
    
    print("🔍 문제 상태 확인 시작...")
    print("=" * 50)
    
    # "하이브리드 클라우드 구성" 문제 찾기
    questions = Question.objects.filter(
        models.Q(title_ko__icontains="하이브리드 클라우드 구성") | 
        models.Q(title_en__icontains="하이브리드 클라우드 구성")
    )
    
    if not questions.exists():
        print("❌ '하이브리드 클라우드 구성' 문제를 찾을 수 없습니다.")
        return
    
    print(f"✅ '하이브리드 클라우드 구성' 문제 {questions.count()}개 발견:")
    
    for question in questions:
        question_title = question.title_ko if question.title_ko else question.title_en or '제목 없음'
        print(f"\n📝 문제 ID: {question.id}")
        print(f"📝 제목: {question_title}")
        content = question.content_ko or question.content_en or ''
        print(f"📝 내용: {content[:100] if content else '내용 없음'}...")
        
        # Favorite 상태 확인 (ExamQuestion을 통해)
        favorite_count = 0
        favorite_users = []
        
        # 모든 사용자의 favorite 시험에서 이 문제가 있는지 확인
        users = User.objects.filter(is_active=True)
        for user in users:
            favorite_exams = Exam.objects.filter(
                title=f"{user.username}'s favorite",
                is_original=True
            )
            
            for exam in favorite_exams:
                if ExamQuestion.objects.filter(exam=exam, question=question).exists():
                    favorite_count += 1
                    favorite_users.append(user.username)
                    break
        
        print(f"❤️  Favorite 상태: {favorite_count}개")
        if favorite_users:
            print(f"   - 사용자: {', '.join(favorite_users)}")
        
        # Ignored 상태 확인
        ignored_count = IgnoredQuestion.objects.filter(question=question).count()
        print(f"🚫 Ignored 상태: {ignored_count}개")
        
        if ignored_count > 0:
            ignoreds = IgnoredQuestion.objects.filter(question=question)
            for ign in ignoreds:
                print(f"   - 사용자: {ign.user.username} (ID: {ign.user.id})")
                print(f"   - 생성일: {ign.ignored_at}")
        
        print("-" * 30)
    
    # 전체 통계
    print("\n📊 전체 통계:")
    
    # 전체 Favorite 문제 수 (모든 사용자의 favorite 시험에 있는 문제들)
    total_favorites = 0
    for user in users:
        favorite_exams = Exam.objects.filter(
            title=f"{user.username}'s favorite",
            is_original=True
        )
        for exam in favorite_exams:
            total_favorites += ExamQuestion.objects.filter(exam=exam).count()
    
    print(f"❤️  전체 Favorite 문제 수: {total_favorites}개")
    print(f"🚫 전체 Ignored 문제 수: {IgnoredQuestion.objects.count()}개")
    
    # 사용자별 상태
    print("\n👥 사용자별 상태:")
    for user in users:
        # Favorite 문제 수
        favorite_count = 0
        favorite_exams = Exam.objects.filter(
            title=f"{user.username}'s favorite",
            is_original=True
        )
        for exam in favorite_exams:
            favorite_count += ExamQuestion.objects.filter(exam=exam).count()
        
        # Ignored 문제 수
        ignored_count = IgnoredQuestion.objects.filter(user=user).count()
        
        if favorite_count > 0 or ignored_count > 0:
            print(f"   {user.username}: Favorite {favorite_count}개, Ignored {ignored_count}개")

if __name__ == "__main__":
    check_question_status()
