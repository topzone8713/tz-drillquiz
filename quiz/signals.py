"""
Django 모델 시그널을 통한 자동 캐시 무효화

캐시 정리 정책:
1. 스터디 모델 변경 시: StudyCacheManager를 통한 체계적인 캐시 무효화
2. 멤버 모델 변경 시: 스터디 관련 캐시 무효화
3. 폴백 메커니즘: StudyCacheManager 실패 시 기존 방식으로 캐시 무효화
4. 로깅: 모든 캐시 무효화 작업에 대한 상세 로그 기록

캐시 계층:
- Redis 환경: delete_pattern을 사용한 효율적인 패턴 매칭
- 로컬 환경: cache.clear() 또는 개별 키 삭제
"""

from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.core.cache import cache
from django.contrib.auth import get_user_model
from .models import Study, Member, StudyJoinRequest, UserProfile, Exam, ExamQuestion
from .utils.cache_utils import StudyCacheManager
from .utils.multilingual_utils import get_localized_field, BASE_LANGUAGE
import logging

logger = logging.getLogger(__name__)


def invalidate_study_cache():
    """스터디 관련 캐시를 무효화하는 헬퍼 함수"""
    try:
        # StudyCacheManager를 사용한 체계적인 캐시 무효화
        StudyCacheManager.invalidate_all_study_cache()
        logger.debug("🔄 StudyCacheManager를 통한 스터디 캐시 자동 무효화 완료")
    except Exception as e:
        logger.error(f"❌ StudyCacheManager 캐시 무효화 실패: {e}")
        # 폴백: 기존 방식으로 캐시 무효화
        try:
            # 모든 studies 관련 캐시 삭제
            cache.delete_pattern("studies_*")
            logger.info("🔄 Redis 패턴 기반 스터디 캐시 자동 무효화 완료")
        except AttributeError:
            # 다른 캐시 백엔드의 경우 개별 키 삭제
            cache.delete("studies_anonymous")
            cache.delete("studies_anonymous_true")
            cache.delete("studies_anonymous_false")
            cache.delete("studies_anonymous_all")
            # 관리자 사용자 캐시도 삭제
            cache.delete("studies_1")
            cache.delete("studies_1_true")
            cache.delete("studies_1_false")
            cache.delete("studies_1_all")
            logger.info("🔄 개별 키 기반 스터디 캐시 자동 무효화 완료")
        except Exception as e2:
            logger.error(f"❌ 폴백 캐시 무효화도 실패: {e2}")


def invalidate_study_cache_safe():
    """안전한 스터디 캐시 무효화 (세션 보존)"""
    try:
        # StudyCacheManager를 사용한 체계적인 캐시 무효화
        StudyCacheManager.invalidate_all_study_cache()
        logger.info("🔄 StudyCacheManager를 통한 스터디 캐시 안전 무효화 완료 (세션 보존)")
    except Exception as e:
        logger.error(f"❌ StudyCacheManager 캐시 무효화 실패: {e}")
        # 폴백: 기존 방식으로 캐시 무효화
        try:
            # 세션 관련 캐시는 보존하고 studies 관련 캐시만 삭제
            cache.delete_pattern("studies_*")
            logger.info("🔄 Redis 패턴 기반 스터디 캐시 안전 무효화 완료 (세션 보존)")
        except AttributeError:
            # 다른 캐시 백엔드의 경우 개별 키 삭제
            cache.delete("studies_anonymous")
            cache.delete("studies_anonymous_true")
            cache.delete("studies_anonymous_false")
            cache.delete("studies_anonymous_all")
            # 관리자 사용자 캐시도 삭제
            cache.delete("studies_1")
            cache.delete("studies_1_true")
            cache.delete("studies_1_false")
            cache.delete("studies_1_all")
            logger.info("🔄 개별 키 기반 스터디 캐시 안전 무효화 완료 (세션 보존)")
        except Exception as e2:
            logger.error(f"❌ 폴백 캐시 무효화도 실패: {e2}")


@receiver([post_save, post_delete], sender=Study)
def invalidate_cache_on_study_change(sender, instance, **kwargs):
    """스터디 모델 변경 시 캐시 무효화"""
    logger.debug(f"🔄 스터디 모델 변경 시그널: {instance.title if hasattr(instance, 'title') else instance.id}")
    invalidate_study_cache()


@receiver([post_save, post_delete], sender=Member)
def invalidate_cache_on_member_change(sender, instance, **kwargs):
    """멤버 모델 변경 시 캐시 무효화 (세션 보존)"""
    study_title = get_localized_field(instance.study, 'title', instance.study.created_language if instance.study and hasattr(instance.study, 'created_language') else BASE_LANGUAGE, 'Unknown') if instance.study else 'N/A'
    logger.info(f"🔄 멤버 변경 시그널: {instance.name} (스터디: {study_title})")
    invalidate_study_cache_safe()


@receiver([post_save, post_delete], sender=StudyJoinRequest)
def invalidate_cache_on_join_request_change(sender, instance, **kwargs):
    """스터디 가입 요청 변경 시 캐시 무효화"""
    study_title = get_localized_field(instance.study, 'title', instance.study.created_language if instance.study and hasattr(instance.study, 'created_language') else BASE_LANGUAGE, 'Unknown') if instance.study else 'N/A'
    logger.info(f"🔄 스터디 가입 요청 변경 시그널: {study_title}")
    invalidate_study_cache()


@receiver(post_save, sender=Member)
def auto_subscribe_exams_on_study_join(sender, instance, **kwargs):
    """스터디 가입 시 연결된 시험 자동 구독"""
    # 새로 생성된 멤버이고 활성 상태인 경우에만 실행
    if kwargs.get('created', False) and instance.is_active:
        try:
            from .models import ExamSubscription, StudyTask
            study_title = get_localized_field(instance.study, 'title', instance.study.created_language if hasattr(instance.study, 'created_language') else BASE_LANGUAGE, 'Unknown')
            logger.info(f"🔔 스터디 가입 시 자동 구독 시작: 사용자 {instance.user.username}, 스터디 {study_title}")
            
            # 해당 스터디에 연결된 모든 시험 조회
            study_tasks = StudyTask.objects.filter(study=instance.study)
            subscribed_count = 0
            
            for task in study_tasks:
                if task.exam:
                    # 이미 구독되어 있는지 확인
                    subscription, created = ExamSubscription.objects.get_or_create(
                        user=instance.user,
                        exam=task.exam,
                        defaults={'is_active': True}
                    )
                    if created:
                        subscribed_count += 1
                        exam_title = get_localized_field(task.exam, 'title', task.exam.created_language if hasattr(task.exam, 'created_language') else BASE_LANGUAGE, 'Unknown')
                        logger.info(f"✅ 시험 자동 구독 생성: {exam_title}")
                    else:
                        # 기존 구독이 비활성화되어 있다면 활성화
                        if not subscription.is_active:
                            subscription.is_active = True
                            subscription.save()
                            subscribed_count += 1
                            exam_title = get_localized_field(task.exam, 'title', task.exam.created_language if hasattr(task.exam, 'created_language') else BASE_LANGUAGE, 'Unknown')
                            logger.info(f"✅ 기존 구독 활성화: {exam_title}")
            
            logger.info(f"🎯 스터디 가입 시 자동 구독 완료: {subscribed_count}개 시험 구독됨")
            
        except Exception as e:
            logger.error(f"❌ 스터디 가입 시 자동 구독 실패: {e}")


@receiver(post_save, sender='quiz.StudyTask')
def auto_subscribe_existing_members_to_new_exam(sender, instance, **kwargs):
    """스터디에 새 시험이 추가될 때 기존 멤버들 자동 구독"""
    # 새로 생성된 StudyTask이고 시험이 연결된 경우에만 실행
    if kwargs.get('created', False) and instance.exam:
        try:
            from .models import ExamSubscription, Member
            study_title = get_localized_field(instance.study, 'title', instance.study.created_language if hasattr(instance.study, 'created_language') else BASE_LANGUAGE, 'Unknown')
            exam_title = get_localized_field(instance.exam, 'title', instance.exam.created_language if hasattr(instance.exam, 'created_language') else BASE_LANGUAGE, 'Unknown')
            logger.info(f"🔔 스터디에 새 시험 추가 시 자동 구독 시작: 스터디 {study_title}, 시험 {exam_title}")
            
            # 해당 스터디의 활성 멤버들 조회
            active_members = Member.objects.filter(study=instance.study, is_active=True)
            subscribed_count = 0
            
            for member in active_members:
                # 이미 구독되어 있는지 확인
                subscription, created = ExamSubscription.objects.get_or_create(
                    user=member.user,
                    exam=instance.exam,
                    defaults={'is_active': True}
                )
                if created:
                    subscribed_count += 1
                    exam_title = get_localized_field(instance.exam, 'title', instance.exam.created_language if hasattr(instance.exam, 'created_language') else BASE_LANGUAGE, 'Unknown')
                    logger.info(f"✅ 기존 멤버 자동 구독 생성: {member.user.username} -> {exam_title}")
                else:
                    # 기존 구독이 비활성화되어 있다면 활성화
                    if not subscription.is_active:
                        subscription.is_active = True
                        subscription.save()
                        subscribed_count += 1
                        exam_title = get_localized_field(instance.exam, 'title', instance.exam.created_language if hasattr(instance.exam, 'created_language') else BASE_LANGUAGE, 'Unknown')
                        logger.info(f"✅ 기존 멤버 구독 활성화: {member.user.username} -> {exam_title}")
            
            logger.info(f"🎯 스터디 새 시험 자동 구독 완료: {subscribed_count}명의 멤버가 구독됨")
            
        except Exception as e:
            logger.error(f"❌ 스터디 새 시험 자동 구독 실패: {e}")


# @receiver(post_save, sender=get_user_model())
# def create_user_profile(sender, instance, created, **kwargs):
#     """사용자 생성 시 UserProfile 자동 생성 - 비활성화됨"""
#     # auth_views.py에서 UserProfile을 직접 생성하므로 시그널 비활성화
#     pass


# @receiver(post_save, sender=get_user_model())
# def update_user_profile(sender, instance, created, **kwargs):
#     """기존 사용자에 대해 UserProfile이 없으면 생성 - 비활성화됨"""
#     # auth_views.py에서 UserProfile을 직접 생성하므로 시그널 비활성화
#     pass


@receiver(m2m_changed, sender=Exam.questions.through)
def update_exam_total_questions(sender, instance, action, pk_set, **kwargs):
    """Exam의 questions 관계가 변경될 때 total_questions 자동 업데이트"""
    if action in ["post_add", "post_remove", "post_clear"]:
        try:
            # Exam 인스턴스의 total_questions 업데이트
            if hasattr(instance, 'id'):
                exam = Exam.objects.get(id=instance.id)
                exam.total_questions = exam.questions.count()
                exam.save(update_fields=['total_questions'])
                logger.info(f"🔄 Exam {exam.id}의 total_questions 자동 업데이트: {exam.total_questions}")
        except Exception as e:
            logger.error(f"❌ Exam total_questions 자동 업데이트 실패: {e}")


@receiver([post_save, post_delete], sender=ExamQuestion)
def update_exam_total_questions_on_examquestion_change(sender, instance, **kwargs):
    """ExamQuestion 모델 변경 시 Exam의 total_questions 자동 업데이트"""
    try:
        exam = instance.exam
        exam.total_questions = exam.questions.count()
        exam.save(update_fields=['total_questions'])
        logger.info(f"🎯 Exam {exam.id}의 total_questions 자동 업데이트 (ExamQuestion 변경): {exam.total_questions}")
    except Exception as e:
        logger.error(f"❌ Exam total_questions 자동 업데이트 실패 (ExamQuestion 변경): {e}")