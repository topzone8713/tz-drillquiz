"""
문제 관련 공통 유틸리티 함수들
"""
from django.db import models
from quiz.models import Question


def get_questions_by_title(title, language='en'):
    """
    제목으로 문제들을 조회합니다.
    
    Args:
        title (str): 문제 제목
        language (str): 언어
    
    Returns:
        QuerySet: 해당 제목의 모든 문제들
    """
    from quiz.utils.multilingual_utils import LANGUAGE_KO, LANGUAGE_EN, LANGUAGE_ES, LANGUAGE_ZH
    if language == LANGUAGE_KO:
        return Question.objects.filter(title_ko=title)
    elif language == LANGUAGE_ES:
        return Question.objects.filter(title_es=title)
    elif language == LANGUAGE_ZH:
        return Question.objects.filter(title_zh=title)
    else:
        # LANGUAGE_EN 또는 기본값
        return Question.objects.filter(title_en=title)


def get_questions_by_title_both_languages(title):
    """
    한국어 또는 영어 제목으로 문제들을 조회합니다.
    
    Args:
        title (str): 문제 제목
    
    Returns:
        QuerySet: 해당 제목의 모든 문제들 (한국어 또는 영어)
    """
    return Question.objects.filter(
        models.Q(title_ko=title) | models.Q(title_en=title)
    )


def group_questions_by_title(questions):
    """
    문제들을 제목별로 그룹화합니다.
    
    Args:
        questions (QuerySet): 그룹화할 문제들
    
    Returns:
        dict: {title_key: [question1, question2, ...]} 형태의 딕셔너리
    """
    title_groups = {}
    
    for question in questions:
        # 제목 결정 (title_en 우선, 없으면 title_ko)
        title_key = None
        if question.title_en and question.title_en.strip():
            title_key = f"en:{question.title_en}"
        elif question.title_ko and question.title_ko.strip():
            title_key = f"ko:{question.title_ko}"
        else:
            title_key = f"id:{question.id}"  # 제목이 없으면 ID로 그룹화
        
        if title_key not in title_groups:
            title_groups[title_key] = []
        title_groups[title_key].append(question)
    
    return title_groups


def get_all_questions_by_title_group(title_key):
    """
    제목 그룹 키를 기반으로 동일한 제목의 모든 문제를 조회합니다.
    
    Args:
        title_key (str): 'en:title' 또는 'ko:title' 형태의 키
    
    Returns:
        QuerySet: 동일한 제목의 모든 문제들
    """
    if title_key.startswith('en:'):
        title = title_key[3:]  # 'en:' 제거
        return Question.objects.filter(title_en=title)
    elif title_key.startswith('ko:'):
        title = title_key[3:]  # 'ko:' 제거
        return Question.objects.filter(title_ko=title)
    else:
        # ID로 그룹화된 경우는 해당 문제만
        question_id = title_key[3:]  # 'id:' 제거
        return Question.objects.filter(id=question_id)
