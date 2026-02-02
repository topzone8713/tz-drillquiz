"""
Celery tasks for quiz application.

This module contains asynchronous tasks that can be executed in the background
using Celery workers.
"""

import logging
from celery import shared_task
from django.apps import apps
from quiz.utils.multilingual_utils import get_localized_field, BASE_LANGUAGE

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def save_translation_results(self, model_name, instance_id, update_fields_dict):
    """
    번역 결과를 비동기로 DB에 저장하는 Celery 태스크.
    
    Args:
        model_name: 모델 이름 (예: 'Exam', 'Question', 'Study')
        instance_id: 인스턴스 ID
        update_fields_dict: 업데이트할 필드 딕셔너리 {field_name: value}
    
    Returns:
        bool: 저장 성공 여부
    """
    try:
        # 모델 가져오기
        Model = apps.get_model('quiz', model_name)
        
        # 인스턴스 조회
        instance = Model.objects.get(id=instance_id)
        
        # 필드 업데이트
        for field_name, value in update_fields_dict.items():
            setattr(instance, field_name, value)
        
        # DB 저장
        update_fields = list(update_fields_dict.keys())
        instance.save(update_fields=update_fields)
        
        logger.info(f"[CELERY_TASK] 번역 결과 저장 완료 - {model_name}({instance_id}): {update_fields}")
        return True
        
    except Model.DoesNotExist:
        logger.error(f"[CELERY_TASK] 인스턴스를 찾을 수 없음 - {model_name}({instance_id})")
        return False
    except Exception as e:
        logger.error(f"[CELERY_TASK] 번역 결과 저장 실패 - {model_name}({instance_id}): {str(e)}")
        # 재시도
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def batch_save_translation_results(self, model_name, instance_id, language_group, field_names, translated_texts):
    """
    배치 번역 결과를 비동기로 DB에 저장하는 Celery 태스크.
    
    Args:
        model_name: 모델 이름 (예: 'Exam', 'Question', 'Study')
        instance_id: 인스턴스 ID
        language_group: 언어 그룹 튜플 (from_lang, to_lang)
        field_names: 필드 이름 리스트
        translated_texts: 번역된 텍스트 리스트
    
    Returns:
        bool: 저장 성공 여부
    """
    try:
        from_lang, to_lang = language_group
        
        # 모델 가져오기
        Model = apps.get_model('quiz', model_name)
        
        # 인스턴스 조회
        instance = Model.objects.get(id=instance_id)
        
        # 번역 결과를 필드에 설정
        update_fields_dict = {}
        for field_name, translated_content in zip(field_names, translated_texts):
            if translated_content:
                target_field = f"{field_name}_{to_lang}"
                setattr(instance, target_field, translated_content)
                update_fields_dict[target_field] = translated_content
        
        # DB 저장
        if update_fields_dict:
            update_fields = list(update_fields_dict.keys())
            instance.save(update_fields=update_fields)
            logger.info(f"[CELERY_TASK] 배치 번역 결과 저장 완료 - {model_name}({instance_id}): {len(update_fields)}개 필드 ({from_lang} → {to_lang})")
            return True
        else:
            logger.warning(f"[CELERY_TASK] 저장할 번역 결과 없음 - {model_name}({instance_id})")
            return False
        
    except Model.DoesNotExist:
        logger.error(f"[CELERY_TASK] 인스턴스를 찾을 수 없음 - {model_name}({instance_id})")
        return False
    except Exception as e:
        logger.error(f"[CELERY_TASK] 배치 번역 결과 저장 실패 - {model_name}({instance_id}): {str(e)}")
        # 재시도
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=2, default_retry_delay=30, ignore_result=True)
def save_exam_list_cache(self, user_id, data, **cache_params):
    """
    시험 목록 캐시를 비동기로 저장하는 Celery 태스크.
    
    Args:
        user_id: 사용자 ID
        data: 캐시할 데이터
        **cache_params: 캐시 파라미터 (page, page_size, filters 등)
    
    Returns:
        bool: 저장 성공 여부
    """
    try:
        from quiz.utils.cache_utils import ExamCacheManager
        
        # 캐시 저장 (cache_params에 모든 파라미터 포함)
        result = ExamCacheManager.set_exam_list_cache(user_id, data, **cache_params)
        
        page = cache_params.get('page', 'N/A')
        if result:
            logger.info(f"[CELERY_TASK] 시험 목록 캐시 저장 완료 - user_id: {user_id}, page: {page}")
        else:
            logger.warning(f"[CELERY_TASK] 시험 목록 캐시 저장 실패 - user_id: {user_id}, page: {page}")
        
        return result
        
    except Exception as e:
        page = cache_params.get('page', 'N/A')
        logger.error(f"[CELERY_TASK] 시험 목록 캐시 저장 중 오류 - user_id: {user_id}, page: {page}, error: {str(e)}")
        # 재시도
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=2, default_retry_delay=30, ignore_result=True)
def save_user_profile_cache(self, user_id, data, timeout=300):
    """
    사용자 프로필 캐시를 비동기로 저장하는 Celery 태스크.
    
    Args:
        user_id: 사용자 ID
        data: 캐시할 데이터
        timeout: 캐시 만료 시간 (초, 기본값: 300)
    
    Returns:
        bool: 저장 성공 여부
    """
    try:
        from django.core.cache import cache
        
        cache_key = f"user_profile_{user_id}"
        cache.set(cache_key, data, timeout)
        
        logger.info(f"[CELERY_TASK] 사용자 프로필 캐시 저장 완료 - user_id: {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"[CELERY_TASK] 사용자 프로필 캐시 저장 중 오류 - user_id: {user_id}, error: {str(e)}")
        # 재시도
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60, ignore_result=True)
def cleanup_duplicate_favorite_exams(self, user_id, main_exam_id, duplicate_exam_ids):
    """
    중복된 favorite 시험을 정리하는 Celery 태스크.
    
    Args:
        user_id: 사용자 ID
        main_exam_id: 메인 시험 ID (유지할 시험)
        duplicate_exam_ids: 중복 시험 ID 목록 (삭제할 시험들)
    
    Returns:
        bool: 정리 성공 여부
    """
    try:
        from django.contrib.auth import get_user_model
        from quiz.models import Exam, ExamQuestion
        
        User = get_user_model()
        user = User.objects.get(id=user_id)
        main_exam = Exam.objects.get(id=main_exam_id)
        
        for duplicate_exam_id in duplicate_exam_ids:
            try:
                duplicate_exam = Exam.objects.get(id=duplicate_exam_id)
                
                # 중복 시험의 문제들을 메인 시험으로 이동
                duplicate_questions = ExamQuestion.objects.filter(exam=duplicate_exam)
                for eq in duplicate_questions:
                    existing = ExamQuestion.objects.filter(
                        exam=main_exam,
                        question=eq.question
                    ).first()
                    if not existing:
                        eq.exam = main_exam
                        eq.save()
                
                # 중복 시험 삭제
                duplicate_exam.delete()
            except Exam.DoesNotExist:
                continue
            except Exception as e:
                logger.error(f"[CELERY_TASK] 중복 시험 {duplicate_exam_id} 정리 실패: {str(e)}")
                continue
        
        # 메인 시험의 총 문제 수 업데이트
        main_exam.total_questions = ExamQuestion.objects.filter(exam=main_exam).count()
        main_exam.save()
        
        logger.info(f"[CELERY_TASK] 중복 favorite 시험 정리 완료 - user_id: {user_id}, 메인 시험: {main_exam_id}, 정리된 시험: {len(duplicate_exam_ids)}개")
        return True
        
    except Exception as e:
        logger.error(f"[CELERY_TASK] 중복 favorite 시험 정리 중 오류 - user_id: {user_id}, error: {str(e)}")
        # 재시도
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=2, default_retry_delay=30, ignore_result=True)
def save_favorite_exam_questions_cache(self, user_id, data, timeout=300):
    """
    즐겨찾기 시험 문제 캐시를 비동기로 저장하는 Celery 태스크.
    
    Args:
        user_id: 사용자 ID
        data: 캐시할 데이터
        timeout: 캐시 만료 시간 (초, 기본값: 300)
    
    Returns:
        bool: 저장 성공 여부
    """
    try:
        from django.core.cache import cache
        
        cache_key = f"favorites_{user_id}"
        cache.set(cache_key, data, timeout)
        
        logger.info(f"[CELERY_TASK] 즐겨찾기 시험 문제 캐시 저장 완료 - user_id: {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"[CELERY_TASK] 즐겨찾기 시험 문제 캐시 저장 중 오류 - user_id: {user_id}, error: {str(e)}")
        # 재시도
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=2, default_retry_delay=30, ignore_result=True)
def save_study_list_cache(self, cache_key, data, timeout=300):
    """
    스터디 목록 캐시를 비동기로 저장하는 Celery 태스크.
    
    Args:
        cache_key: 캐시 키
        data: 캐시할 데이터
        timeout: 캐시 만료 시간 (초, 기본값: 300)
    
    Returns:
        bool: 저장 성공 여부
    """
    try:
        from django.core.cache import cache
        
        cache.set(cache_key, data, timeout)
        
        logger.info(f"[CELERY_TASK] 스터디 목록 캐시 저장 완료 - cache_key: {cache_key}")
        return True
        
    except Exception as e:
        logger.error(f"[CELERY_TASK] 스터디 목록 캐시 저장 중 오류 - cache_key: {cache_key}, error: {str(e)}")
        # 재시도
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60, ignore_result=True)
def record_study_progress_task(self, user_id, study_ids, page_type):
    """
    스터디 진행율을 비동기로 기록하는 Celery 태스크.
    
    Args:
        user_id: 사용자 ID
        study_ids: 스터디 ID 목록
        page_type: 페이지 타입 (예: 'study-management')
    
    Returns:
        bool: 기록 성공 여부
    """
    try:
        from django.contrib.auth import get_user_model
        from quiz.models import Study, StudyProgressRecord
        
        User = get_user_model()
        user = User.objects.get(id=user_id)
        
        records_created = []
        
        for study_id in study_ids:
            try:
                study = Study.objects.get(id=study_id)
                
                # 현재 진행율 계산 (StudyTaskProgress의 실제 진행률 사용)
                tasks = study.tasks.all()
                task_progresses = {}
                total_progress = 0
                
                for task in tasks:
                    # StudyTaskSerializer와 동일한 로직으로 진행률 계산
                    if task.exam:
                        correct_attempts = task.exam.get_total_correct_questions_for_user(user)
                        total_attempts = task.exam.get_total_attempted_questions_for_user(user)
                        if total_attempts > 0:
                            task_progress = (correct_attempts / total_attempts) * 100
                        else:
                            task_progress = 0
                    else:
                        task_progress = 0
                    
                    task_progresses[task.id] = task_progress
                    total_progress += task_progress
                
                overall_progress = total_progress / len(tasks) if tasks else 0
                
                # 기록 생성
                record = StudyProgressRecord.objects.create(
                    user=user,
                    study=study,
                    overall_progress=overall_progress,
                    task_progresses=task_progresses,
                    page_type=page_type
                )
                
                records_created.append({
                    'study_id': study_id,
                    'study_title': get_localized_field(study, 'title', study.created_language if hasattr(study, 'created_language') else BASE_LANGUAGE, 'Unknown'),
                    'overall_progress': overall_progress,
                    'record_id': record.id
                })
                
            except Study.DoesNotExist:
                continue
            except Exception as e:
                logger.error(f"[CELERY_TASK] 스터디 {study_id} 진행율 기록 실패: {str(e)}")
                continue
        
        logger.info(f"[CELERY_TASK] 스터디 진행율 기록 완료 - user_id: {user_id}, study_ids: {len(study_ids)}개, 기록됨: {len(records_created)}개")
        return True
        
    except Exception as e:
        logger.error(f"[CELERY_TASK] 스터디 진행율 기록 중 오류 - user_id: {user_id}, error: {str(e)}")
        # 재시도
        raise self.retry(exc=e)

