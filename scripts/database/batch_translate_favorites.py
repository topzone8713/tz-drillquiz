#!/usr/bin/env python
import os
import django
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
django.setup()

from django.contrib.auth import get_user_model
from quiz.models import Exam, ExamQuestion, Question, IgnoredQuestion
from quiz.utils.multilingual_utils import batch_translate_texts

User = get_user_model()

print("=== 즐겨찾기 문제 일괄 번역 ===")

def translate_favorite_questions():
    """즐겨찾기된 문제들 중 영어 콘텐츠가 없는 문제들을 번역합니다."""
    
    # 모든 사용자의 favorite 시험 찾기
    favorite_exams = Exam.objects.filter(
        title_ko__endswith="'s favorite",
        is_original=True
    )
    
    print(f"총 {favorite_exams.count()}개의 favorite 시험을 찾았습니다.")
    
    total_translated = 0
    total_failed = 0
    
    for exam in favorite_exams:
        username = exam.title_ko.replace("'s favorite", "")
        print(f"\n=== {username}의 favorite 시험 ===")
        print(f"시험 ID: {exam.id}")
        
        # 해당 시험의 문제들 조회
        exam_questions = ExamQuestion.objects.filter(exam=exam)
        print(f"문제 수: {exam_questions.count()}")
        
        # 번역이 필요한 문제들 찾기 (어떤 언어에 콘텐츠가 있지만 BASE_LANGUAGE('en')에 콘텐츠가 없는 문제)
        from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES, BASE_LANGUAGE
        questions_to_translate = []
        for eq in exam_questions:
            question = eq.question
            # BASE_LANGUAGE('en')에 콘텐츠가 없고, 다른 언어에 콘텐츠가 있는 경우
            base_content = getattr(question, f'content_{BASE_LANGUAGE}', None)
            if not base_content:
                # 다른 언어 중 하나라도 콘텐츠가 있는지 확인
                has_other_language_content = False
                source_language = None
                for lang in SUPPORTED_LANGUAGES:
                    if lang != BASE_LANGUAGE:
                        content = getattr(question, f'content_{lang}', None)
                        if content:
                            has_other_language_content = True
                            source_language = lang
                            break
                if has_other_language_content:
                    questions_to_translate.append((question, source_language))
        
        if not questions_to_translate:
            print("번역이 필요한 문제가 없습니다.")
            continue
        
        print(f"번역이 필요한 문제 수: {len(questions_to_translate)}")
        
        # 소스 언어별로 그룹화하여 번역
        from collections import defaultdict
        questions_by_source_lang = defaultdict(list)
        for question, source_lang in questions_to_translate:
            questions_by_source_lang[source_lang].append(question)
        
        try:
            # 각 소스 언어별로 번역 수행
            for source_lang, questions in questions_by_source_lang.items():
                print(f"{source_lang} → {BASE_LANGUAGE} 번역 시작...")
                # 소스 언어 콘텐츠들을 수집
                source_contents = [getattr(q, f'content_{source_lang}') for q in questions]
                translated_texts = batch_translate_texts(source_contents, source_lang, BASE_LANGUAGE)
                
                # 번역 결과를 각 문제에 저장
                for i, question in enumerate(questions):
                    if translated_texts and i < len(translated_texts) and translated_texts[i]:
                        setattr(question, f'content_{BASE_LANGUAGE}', translated_texts[i])
                        question.save()
                    print(f"✅ 문제 {question.id} 번역 완료")
                    total_translated += 1
                else:
                    print(f"❌ 문제 {question.id} 번역 실패")
                    total_failed += 1
                    
        except Exception as e:
            print(f"번역 중 오류 발생: {e}")
            total_failed += len(questions_to_translate)
    
    print(f"\n=== 번역 완료 ===")
    print(f"성공: {total_translated}개")
    print(f"실패: {total_failed}개")
    print(f"총 처리: {total_translated + total_failed}개")

def translate_ignored_questions():
    """무시된 문제들 중 영어 콘텐츠가 없는 문제들을 번역합니다."""
    
    print(f"\n=== 무시된 문제 일괄 번역 ===")
    
    # 무시된 문제들 중 번역이 필요한 문제들 찾기
    from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES, BASE_LANGUAGE
    ignored_questions = IgnoredQuestion.objects.select_related('question').all()
    
    questions_to_translate = []
    for ignored in ignored_questions:
        question = ignored.question
        # BASE_LANGUAGE('en')에 콘텐츠가 없고, 다른 언어에 콘텐츠가 있는 경우
        base_content = getattr(question, f'content_{BASE_LANGUAGE}', None)
        if not base_content:
            # 다른 언어 중 하나라도 콘텐츠가 있는지 확인
            has_other_language_content = False
            source_language = None
            for lang in SUPPORTED_LANGUAGES:
                if lang != BASE_LANGUAGE:
                    content = getattr(question, f'content_{lang}', None)
                    if content:
                        has_other_language_content = True
                        source_language = lang
                        break
            if has_other_language_content:
                questions_to_translate.append((question, source_language))
    
    if not questions_to_translate:
        print("번역이 필요한 무시된 문제가 없습니다.")
        return
    
    print(f"번역이 필요한 무시된 문제 수: {len(questions_to_translate)}")
    
    # 소스 언어별로 그룹화하여 번역
    from collections import defaultdict
    questions_by_source_lang = defaultdict(list)
    for question, source_lang in questions_to_translate:
        questions_by_source_lang[source_lang].append(question)
    
    try:
        total_translated = 0
        total_failed = 0
        
        # 각 소스 언어별로 번역 수행
        for source_lang, questions in questions_by_source_lang.items():
            print(f"{source_lang} → {BASE_LANGUAGE} 번역 시작...")
            # 소스 언어 콘텐츠들을 수집
            source_contents = [getattr(q, f'content_{source_lang}') for q in questions]
            translated_texts = batch_translate_texts(source_contents, source_lang, BASE_LANGUAGE)
            
            # 번역 결과를 각 문제에 저장
            for i, question in enumerate(questions):
                if translated_texts and i < len(translated_texts) and translated_texts[i]:
                    setattr(question, f'content_{BASE_LANGUAGE}', translated_texts[i])
                    question.save()
                print(f"✅ 문제 {question.id} 번역 완료")
                total_translated += 1
            else:
                print(f"❌ 문제 {question.id} 번역 실패")
                total_failed += 1
        
        print(f"무시된 문제 번역 완료 - 성공: {total_translated}개, 실패: {total_failed}개")
        
    except Exception as e:
        print(f"번역 중 오류 발생: {e}")

if __name__ == "__main__":
    try:
        # 즐겨찾기 문제 번역
        translate_favorite_questions()
        
        # 무시된 문제 번역
        translate_ignored_questions()
        
        print("\n🎉 모든 번역 작업이 완료되었습니다!")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
