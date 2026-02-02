from django.contrib.auth import get_user_model
from quiz.models import UserProfile, Member
from quiz.utils.multilingual_utils import get_localized_field, BASE_LANGUAGE

User = get_user_model()


def get_user_permissions(user):
    """
    사용자의 전역 권한 정보를 반환합니다. (로그인 시 사용)
    
    Args:
        user: Django User 객체
        
    Returns:
        dict: 전역 권한 정보 딕셔너리
    """
    if not user or not user.is_authenticated:
        return {
            'is_admin': False,
            'has_study_admin_role': False,
            'is_study_admin': False,
            'is_authenticated': False
        }
    
    try:
        profile = user.profile
        user_role = profile.role
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user, role='user_role')
        user_role = profile.role
    
    # 관리자 권한 확인
    is_admin = user_role == 'admin_role'
    
    # 전역 스터디 관리자 권한 확인 (UserProfile)
    has_study_admin_role = user_role == 'study_admin_role'
    
    # 전역 스터디 관리자 권한 확인 (Member 테이블)
    is_study_admin = Member.objects.filter(
        user=user,
        is_active=True,
        role__in=['study_admin', 'study_leader']
    ).exists()
    
    return {
        'is_admin': is_admin,
        'has_study_admin_role': has_study_admin_role,
        'is_study_admin': is_study_admin,
        'is_authenticated': True,
        'user_role': user_role
    }


def get_resource_specific_permissions(user, resource):
    """
    특정 리소스에 대한 권한 정보를 반환합니다.
    
    Args:
        user: Django User 객체
        resource: 특정 리소스 (Exam, Study 등)
        
    Returns:
        dict: 리소스별 권한 정보 딕셔너리
    """
    if not user or not user.is_authenticated:
        return {
            'is_admin': False,
            'has_study_admin_role': False,
            'is_study_admin': False,
            'is_authenticated': False
        }
    
    try:
        profile = user.profile
        user_role = profile.role
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user, role='user_role')
        user_role = profile.role
    
    # 관리자 권한 확인
    is_admin = user_role == 'admin_role'
    
    # 전역 스터디 관리자 권한 확인 (UserProfile)
    has_study_admin_role = user_role == 'study_admin_role'
    
    # 특정 리소스에 대한 권한 확인
    is_study_admin = False
    
    if hasattr(resource, 'studies') and resource.studies:
        # 시험에 연결된 스터디들의 권한 확인
        is_study_admin = any(
            has_study_specific_admin_permission(user, study) 
            for study in resource.studies
        )
    elif hasattr(resource, 'study') and resource.study:
        # 단일 스터디에 대한 권한 확인
        is_study_admin = has_study_specific_admin_permission(user, resource.study)
    elif hasattr(resource, 'members'):
        # 스터디 객체인 경우
        is_study_admin = has_study_specific_admin_permission(user, resource)
    else:
        # Exam 객체인 경우 StudyTask를 통해 연결된 스터디 확인
        from quiz.models import StudyTask
        study_tasks = StudyTask.objects.filter(exam=resource)
        for task in study_tasks:
            if has_study_specific_admin_permission(user, task.study):
                is_study_admin = True
                break

        # 시험에 직접 연결된 스터디가 없는 경우, 사용자가 멤버인 모든 스터디에서 관리자 권한 확인
        # 단, 시험과 연결된 스터디에서만 확인해야 함
        if not is_study_admin:
            from quiz.models import Member
            # 시험과 연결된 스터디들만 확인
            connected_studies = [task.study for task in study_tasks]
            user_study_admin_memberships = Member.objects.filter(
                user=user,
                study__in=connected_studies,
                is_active=True,
                role__in=['study_admin', 'study_leader']
            )
            if user_study_admin_memberships.exists():
                is_study_admin = True

    return {
        'is_admin': is_admin,
        'has_study_admin_role': has_study_admin_role,
        'is_study_admin': is_study_admin,
        'is_authenticated': True,
        'user_role': user_role
    }


def has_admin_permission(user):
    """
    사용자가 관리자 권한을 가지고 있는지 확인합니다.
    
    Args:
        user: Django User 객체
        
    Returns:
        bool: 관리자 권한 여부
    """
    permissions = get_user_permissions(user)
    return permissions['is_admin']


def has_study_admin_role(user):
    """
    사용자가 전역 스터디 관리자 권한을 가지고 있는지 확인합니다.
    
    Args:
        user: Django User 객체
        
    Returns:
        bool: 전역 스터디 관리자 권한 여부
    """
    permissions = get_user_permissions(user)
    return permissions['has_study_admin_role']


def has_study_admin_permission(user):
    """
    사용자가 특정 스터디 관리자 권한을 가지고 있는지 확인합니다.
    
    Args:
        user: Django User 객체
        
    Returns:
        bool: 특정 스터디 관리자 권한 여부
    """
    permissions = get_user_permissions(user)
    return permissions['is_study_admin']


def has_any_admin_permission(user):
    """
    사용자가 관리자 또는 스터디 관리자 권한을 가지고 있는지 확인합니다.
    
    Args:
        user: Django User 객체
        
    Returns:
        bool: 관리자 또는 스터디 관리자 권한 여부
    """
    permissions = get_user_permissions(user)
    return permissions['is_admin'] or permissions['has_study_admin_role']


def has_study_specific_admin_permission(user, study=None):
    """
    사용자가 특정 스터디에 대한 관리자 권한을 가지고 있는지 확인합니다.
    
    Args:
        user: Django User 객체
        study: Study 객체 (None인 경우 모든 스터디에서 관리자 권한 확인)
        
    Returns:
        bool: 특정 스터디 관리자 권한 여부
    """
    if not user or not user.is_authenticated:
        return False
    
    # 전역 관리자 권한 확인
    permissions = get_user_permissions(user)
    if permissions['is_admin'] or permissions['has_study_admin_role']:
        return True
    
    # 특정 스터디 관리자 권한 확인
    if study:
        # 멤버십 확인 (is_active=True인 멤버만)
        is_member = study.members.filter(
            user=user,
            is_active=True
        ).exists()
        
        # 관리자 권한 확인 (study_admin 또는 study_leader 역할)
        is_admin = study.members.filter(
            user=user,
            is_active=True,
            role__in=['study_admin', 'study_leader']
        ).exists()
        
        # 디버깅 로그
        import logging
        logger = logging.getLogger(__name__)
        if is_member or is_admin:
            study_lang = study.created_language if hasattr(study, 'created_language') else BASE_LANGUAGE
            study_title = get_localized_field(study, 'title', study_lang, 'Unknown')
            logger.info(f"[PERMISSION_CHECK] 사용자 {user.username} - 스터디 {study_title} (ID: {study.id})")
            logger.info(f"  - 멤버 여부: {is_member}")
            logger.info(f"  - 관리자 권한: {is_admin}")
            if is_member:
                member_info = study.members.filter(user=user, is_active=True).values('role', 'is_active').first()
                logger.info(f"  - 멤버 정보: {member_info}")
        
        return is_admin
    else:
        return permissions['is_study_admin']


def can_edit_exam(user, exam):
    """
    사용자가 특정 시험을 편집할 수 있는 권한을 가지고 있는지 확인합니다.
    
    Args:
        user: Django User 객체
        exam: Exam 객체
        
    Returns:
        bool: 시험 편집 권한 여부
    """
    if not user or not user.is_authenticated:
        return False
    
    # 전역 관리자 권한 확인
    permissions = get_user_permissions(user)
    if permissions['is_admin'] or permissions['has_study_admin_role']:
        return True
    
    # 시험 생성자 확인
    if exam.created_by == user:
        return True
    
    # 시험이 속한 스터디의 관리자 권한 확인
    from quiz.models import StudyTask
    study_tasks = StudyTask.objects.filter(exam=exam)
    for task in study_tasks:
        if has_study_specific_admin_permission(user, task.study):
            return True
    
    return False


def can_edit_study(user, study):
    """
    사용자가 특정 스터디를 편집할 수 있는 권한을 가지고 있는지 확인합니다.
    
    Args:
        user: Django User 객체
        study: Study 객체
        
    Returns:
        bool: 스터디 편집 권한 여부
    """
    if not user or not user.is_authenticated:
        return False
    
    # 전역 관리자 권한 확인
    permissions = get_user_permissions(user)
    if permissions['is_admin'] or permissions['has_study_admin_role']:
        return True
    
    # 스터디 생성자 확인
    if study.created_by == user:
        return True
    
    # 스터디 관리자 권한 확인
    return has_study_specific_admin_permission(user, study)
