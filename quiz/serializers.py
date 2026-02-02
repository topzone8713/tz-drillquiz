import logging
from rest_framework import serializers
from .models import Study, StudyTask, Member, StudyTaskProgress, ExamResult, ExamResultDetail, Exam, Question, QuestionMemberMapping, StudyJoinRequest, UserProfile, Tag, TagCategory
from .utils.multilingual_utils import (
    MultilingualSerializerMixin, 
    get_user_language, 
    is_auto_translation_enabled, 
    get_completion_fields,
    get_localized_field
)
from django.contrib.auth import get_user_model


class TagSerializer(serializers.ModelSerializer):
    """
    태그 모델용 다국어 시리얼라이저 (읽기 전용 최적화)
    """
    # 다국어 필드를 위한 SerializerMethodField
    localized_name = serializers.SerializerMethodField()
    available_languages = serializers.SerializerMethodField()
    usage_count = serializers.IntegerField(read_only=True, default=0)
    categories = serializers.SerializerMethodField()
    category_paths = serializers.SerializerMethodField()
    
    class Meta:
        model = Tag
        fields = [
            'id', 'name_ko', 'name_en', 'created_language'
        ] + get_completion_fields() + [
            'localized_name', 
            'available_languages', 'usage_count', 'categories',
            'category_paths', 'created_at', 'updated_at'
        ]
    
    def get_localized_name(self, obj):
        """현재 사용자 언어에 맞는 태그명 반환"""
        request = self.context.get('request')
        user_language = get_user_language(request)
        return get_localized_field(obj, 'name', user_language, '')
    
    def get_available_languages(self, obj):
        """사용 가능한 언어 목록 반환"""
        return obj.available_languages
    
    def get_categories(self, obj):
        """태그가 속한 카테고리 목록 반환"""
        from quiz.utils.multilingual_utils import BASE_LANGUAGE
        
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user and hasattr(request.user, 'is_anonymous') and not request.user.is_anonymous:
            try:
                user_profile = request.user.profile
                user_language = user_profile.language
            except:
                user_language = BASE_LANGUAGE
        else:
            user_language = BASE_LANGUAGE
        
        # prefetch된 categories 사용 (N+1 쿼리 방지)
        if hasattr(obj, '_prefetched_objects_cache') and 'categories' in obj._prefetched_objects_cache:
            categories = obj._prefetched_objects_cache['categories']
        else:
            categories = obj.categories.all()
        return [
            {
                'id': cat.id,
                'name': cat.get_localized_name(user_language),
                'full_path': cat.get_full_path(user_language),
                'level': cat.level,
                'color': cat.color
            }
            for cat in categories
        ]
    
    def get_category_paths(self, obj):
        """태그가 속한 모든 카테고리의 전체 경로 목록 반환"""
        from quiz.utils.multilingual_utils import BASE_LANGUAGE
        
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user and hasattr(request.user, 'is_anonymous') and not request.user.is_anonymous:
            try:
                user_profile = request.user.profile
                user_language = user_profile.language
            except:
                user_language = BASE_LANGUAGE
        else:
            user_language = BASE_LANGUAGE
        
        # prefetch된 categories 사용 (N+1 쿼리 방지)
        if hasattr(obj, '_prefetched_objects_cache') and 'categories' in obj._prefetched_objects_cache:
            categories = obj._prefetched_objects_cache['categories']
        else:
            categories = obj.categories.all()
        return [cat.get_full_path(user_language) for cat in categories]


class TagCategorySerializer(MultilingualSerializerMixin, serializers.ModelSerializer):
    """
    태그 카테고리 모델용 다국어 시리얼라이저
    """
    # 다국어 필드를 위한 SerializerMethodField
    localized_name = serializers.SerializerMethodField()
    full_path = serializers.SerializerMethodField()
    available_languages = serializers.SerializerMethodField()
    children_count = serializers.SerializerMethodField()
    tags_count = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()
    
    class Meta:
        model = TagCategory
        fields = [
            'id', 'name_ko', 'name_en', 'name_es', 'name_zh', 'name_ja', 'created_language',
            'is_ko_complete', 'is_en_complete', 'is_es_complete', 'is_zh_complete', 'is_ja_complete', 
            'is_active', 'localized_name', 'available_languages', 'full_path', 
            'level', 'order', 'color', 'parent', 'parent_name', 'children_count',
            'tags_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['level', 'created_at', 'updated_at']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 다국어 필드 지정
        self.multilingual_fields = ['name']
    
    def get_localized_name(self, obj):
        """현재 사용자 언어에 맞는 카테고리명 반환"""
        request = self.context.get('request')
        user_language = get_user_language(request)
        return get_localized_field(obj, 'name', user_language, '')
    
    def get_full_path(self, obj):
        """전체 카테고리 경로 반환"""
        from quiz.utils.multilingual_utils import BASE_LANGUAGE, LANGUAGE_KO, LANGUAGE_EN, LANGUAGE_ES, LANGUAGE_ZH
        
        request = self.context.get('request')
        user_language = BASE_LANGUAGE  # 기본값
        
        # 1. 요청 헤더에서 언어 확인 (Accept-Language 또는 X-Language 헤더)
        if request:
            # X-Language 헤더 확인 (프론트엔드에서 명시적으로 보낸 경우)
            language_header = request.META.get('HTTP_X_LANGUAGE') or request.META.get('X-Language')
            if language_header and language_header in [LANGUAGE_KO, LANGUAGE_EN, LANGUAGE_ES, LANGUAGE_ZH]:
                user_language = language_header
            else:
                # Accept-Language 헤더 확인
                accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
                if accept_language:
                    # Accept-Language 파싱 (예: "zh-CN,zh;q=0.9,en;q=0.8")
                    for lang_code in accept_language.split(','):
                        lang = lang_code.split(';')[0].strip().lower()[:2]
                        if lang in [LANGUAGE_KO, LANGUAGE_EN, LANGUAGE_ES, LANGUAGE_ZH]:
                            user_language = lang
                            break
            
            # 2. 사용자 프로필 언어 확인 (헤더가 없을 때만)
            if user_language == BASE_LANGUAGE and hasattr(request, 'user') and request.user and hasattr(request.user, 'is_anonymous') and not request.user.is_anonymous:
                try:
                    user_profile = request.user.profile
                    user_language = user_profile.language
                except:
                    pass
        
        return obj.get_full_path(user_language)
    
    def get_available_languages(self, obj):
        """사용 가능한 언어 목록 반환"""
        languages = []
        if obj.name_ko:
            languages.append('ko')
        if obj.name_en:
            languages.append('en')
        if obj.name_es:
            languages.append('es')
        if obj.name_zh:
            languages.append('zh')
        if obj.name_ja:
            languages.append('ja')
        return languages
    
    def get_children_count(self, obj):
        """하위 카테고리 개수 반환"""
        return obj.children.count()
    
    def get_tags_count(self, obj):
        """해당 카테고리에 속한 태그 개수 반환"""
        return obj.tags.count()
    
    def get_parent_name(self, obj):
        """상위 카테고리 이름 반환"""
        from quiz.utils.multilingual_utils import BASE_LANGUAGE
        
        if obj.parent:
            request = self.context.get('request')
            if request and hasattr(request, 'user') and request.user and hasattr(request.user, 'is_anonymous') and not request.user.is_anonymous:
                try:
                    user_profile = request.user.profile
                    user_language = user_profile.language
                except:
                    user_language = BASE_LANGUAGE
            else:
                user_language = BASE_LANGUAGE
            return obj.parent.get_localized_name(user_language)
        return None


class QuestionListSerializer(serializers.ModelSerializer):
    """문제 목록 조회용 최적화된 시리얼라이저 - 목록 표시에 필요한 필드만 반환"""
    localized_title = serializers.SerializerMethodField()
    available_languages = serializers.SerializerMethodField()
    current_language = serializers.SerializerMethodField()
    
    class Meta:
        model = Question
        fields = [
            'id', 'csv_id', 'title_ko', 'title_en', 'difficulty', 'url', 'group_id', 
            'created_at', 'updated_at', 'created_language'
        ] + get_completion_fields() + [
            'created_by', 'localized_title', 'available_languages', 'current_language'
        ]
    
    def get_localized_title(self, obj):
        """현재 사용자 언어에 맞는 제목 반환"""
        request = self.context.get('request')
        user_language = get_user_language(request)
        return get_localized_field(obj, 'title', user_language, '')
    
    def get_available_languages(self, obj):
        """사용 가능한 언어 목록"""
        from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
        languages = []
        for lang in SUPPORTED_LANGUAGES:
            if hasattr(obj, f'title_{lang}') and getattr(obj, f'title_{lang}', None):
                languages.append(lang)
        return languages
    
    def get_current_language(self, obj):
        """현재 사용자 언어"""
        request = self.context.get('request')
        return get_user_language(request)


class QuestionSerializer(MultilingualSerializerMixin, serializers.ModelSerializer):
    """
    문제 모델용 다국어 시리얼라이저
    
    주의: 다국어 처리 때문에 title, content, answer, explanation 필드는 직접 사용하지 않습니다.
    대신 title_ko/title_en, content_ko/content_en, answer_ko/answer_en, explanation_ko/explanation_en을 사용합니다.
    
    다국어 필드:
    - title_ko, title_en (문제 제목)
    - content_ko, content_en (문제 내용)
    - answer_ko, answer_en (문제 정답)
    - explanation_ko, explanation_en (문제 설명)
    
    중요: localized_* 필드들은 사용자 언어 설정에 따라 하나의 언어만 반환합니다.
    - 한국어 사용자: title_ko, content_ko, answer_ko, explanation_ko만 반환
    - 영어 사용자: title_en, content_en, answer_en, explanation_en만 반환
    - 폴백 로직 없음: 사용자 언어에 맞는 콘텐츠가 없으면 빈 문자열 반환
    
    프론트엔드에서는 localized_title, localized_content, localized_answer, localized_explanation을 사용해야 합니다.
    """
    attempt_count = serializers.SerializerMethodField()
    correct_count = serializers.SerializerMethodField()
    correct_rate = serializers.SerializerMethodField()
    
    # 다국어 필드를 위한 SerializerMethodField
    # 주의: title, content, answer, explanation 필드는 직접 사용하지 않음
    # 다국어 처리 때문에 title_ko/title_en, content_ko/content_en 등을 사용
    localized_title = serializers.SerializerMethodField()
    localized_content = serializers.SerializerMethodField()
    localized_answer = serializers.SerializerMethodField()
    localized_explanation = serializers.SerializerMethodField()
    available_languages = serializers.SerializerMethodField()
    
    class Meta:
        model = Question
        fields = [
            'id', 'csv_id', 'title_ko', 'title_en', 'content_ko', 'content_en', 'answer_ko', 'answer_en', 'explanation_ko', 'explanation_en',
            'difficulty', 'url', 'group_id', 'created_at', 'updated_at', 'attempt_count', 'correct_count', 'correct_rate',
            'created_language'
        ] + get_completion_fields() + [
            'created_by', 'localized_title', 'localized_content', 'localized_answer', 'localized_explanation', 'available_languages'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 다국어 필드 지정 (공통 모듈에서 사용)
        # 주의: title, content, answer, explanation은 직접 필드가 아님
        # title_ko/title_en, content_ko/content_en 등을 의미
        self.multilingual_fields = ['title', 'content', 'answer', 'explanation']
    
    def get_localized_title(self, obj):
        """현재 사용자 언어에 맞는 제목 반환"""
        request = self.context.get('request')
        user_language = get_user_language(request)
        return get_localized_field(obj, 'title', user_language, '')
    
    def get_localized_content(self, obj):
        """현재 사용자 언어에 맞는 문제 내용 반환"""
        request = self.context.get('request')
        user_language = get_user_language(request)
        return get_localized_field(obj, 'content', user_language, '')
    
    def get_localized_answer(self, obj):
        """현재 사용자 언어에 맞는 정답 반환"""
        request = self.context.get('request')
        user_language = get_user_language(request)
        return get_localized_field(obj, 'answer', user_language, '')
    
    def get_localized_explanation(self, obj):
        """현재 사용자 언어에 맞는 설명 반환"""
        request = self.context.get('request')
        user_language = get_user_language(request)
        return get_localized_field(obj, 'explanation', user_language, '')
    

    
    def get_available_languages(self, obj):
        """사용 가능한 언어 목록"""
        from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
        languages = []
        for lang in SUPPORTED_LANGUAGES:
            # Question 모델은 title, content, answer 필드가 모두 있어야 완전한 것으로 간주
            title_field = f'title_{lang}'
            content_field = f'content_{lang}'
            answer_field = f'answer_{lang}'
            if (hasattr(obj, title_field) and getattr(obj, title_field, None) and
                hasattr(obj, content_field) and getattr(obj, content_field, None) and
                hasattr(obj, answer_field) and getattr(obj, answer_field, None)):
                languages.append(lang)
        return languages
    
    def get_attempt_count(self, obj):
        """현재 사용자의 해당 문제 시도횟수 (최적화: 컨텍스트에서 미리 계산된 데이터 사용)"""
        # 컨텍스트에서 미리 계산된 통계 사용
        question_stats_dict = self.context.get('question_stats_dict', {})
        if question_stats_dict:
            stats = question_stats_dict.get(obj.id)
            if stats:
                return stats.get('attempt_count', 0)
        
        # 폴백: 기존 방식 (컨텍스트에 통계가 없는 경우)
        request = self.context.get('request')
        if not request or not request.user or not hasattr(request.user, 'is_authenticated') or not request.user.is_authenticated:
            return 0
        
        return ExamResultDetail.objects.filter(
            question=obj,
            result__user=request.user
        ).count()
    
    def get_correct_count(self, obj):
        """현재 사용자의 해당 문제 정답 횟수 (최적화: 컨텍스트에서 미리 계산된 데이터 사용)"""
        # 컨텍스트에서 미리 계산된 통계 사용
        question_stats_dict = self.context.get('question_stats_dict', {})
        if question_stats_dict:
            stats = question_stats_dict.get(obj.id)
            if stats:
                return stats.get('correct_count', 0)
        
        # 폴백: 기존 방식 (컨텍스트에 통계가 없는 경우)
        request = self.context.get('request')
        if not request or not request.user or not hasattr(request.user, 'is_authenticated') or not request.user.is_authenticated:
            return 0
        
        return ExamResultDetail.objects.filter(
            question=obj,
            result__user=request.user,
            is_correct=True
        ).count()

    def get_correct_rate(self, obj):
        """현재 사용자의 해당 문제 정답률 (최적화: 컨텍스트에서 미리 계산된 데이터 사용)"""
        # 컨텍스트에서 미리 계산된 통계 사용
        question_stats_dict = self.context.get('question_stats_dict', {})
        if question_stats_dict:
            stats = question_stats_dict.get(obj.id)
            if stats:
                return stats.get('correct_rate', 0)
        
        # 폴백: 기존 방식 (컨텍스트에 통계가 없는 경우)
        request = self.context.get('request')
        if not request or not request.user or not hasattr(request.user, 'is_authenticated') or not request.user.is_authenticated:
            return 0
        
        attempt_count = self.get_attempt_count(obj)
        correct_count = self.get_correct_count(obj)
        
        if attempt_count == 0:
            return 0
        return (correct_count / attempt_count) * 100


class ExamDetailSerializer(serializers.ModelSerializer):
    """시험 상세 화면용 최적화된 시리얼라이저 - 문제 목록 관리용"""
    display_title = serializers.SerializerMethodField()
    display_description = serializers.SerializerMethodField()
    total_questions = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    questions = serializers.SerializerMethodField()
    
    # 태그를 객체 배열로 반환
    tags = TagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Exam
        fields = [
            'id', 'title_ko', 'title_en', 'description_ko', 'description_en', 'display_title', 'display_description',
            'is_public', 'is_original', 'created_at', 'total_questions', 'created_by', 'questions',
            'created_language'
        ] + get_completion_fields() + [
            'file_name', 'force_answer', 'voice_mode_enabled',
            'tags', 'age_rating', 'exam_difficulty', 'ai_mock_interview', 'version_number'
        ]
    
    def get_display_title(self, obj):
        """사용자 언어에 맞는 제목 반환"""
        # 1. 컨텍스트에서 명시적으로 전달된 언어 정보 우선 사용
        context_language = self.context.get('user_language')
        if context_language:
            return get_localized_field(obj, 'title', context_language, '')
        
        # 2. fallback: request에서 사용자 언어 확인
        request = self.context.get('request')
        user_language = get_user_language(request)
        return get_localized_field(obj, 'title', user_language, '')
    
    def get_display_description(self, obj):
        """사용자 언어에 맞는 설명 반환"""
        # 1. 컨텍스트에서 명시적으로 전달된 언어 정보 우선 사용
        context_language = self.context.get('user_language')
        if context_language:
            return get_localized_field(obj, 'description', context_language, '')
        
        # 2. fallback: request에서 사용자 언어 확인
        request = self.context.get('request')
        user_language = get_user_language(request)
        return get_localized_field(obj, 'description', user_language, '')
    
    def get_total_questions(self, obj):
        """실제 문제 수를 동적으로 계산"""
        # annotate로 계산된 total_questions_count가 있으면 사용
        if hasattr(obj, 'total_questions_count'):
            return obj.total_questions_count
        # total_questions 필드가 있으면 사용
        if hasattr(obj, 'total_questions') and obj.total_questions is not None:
            return obj.total_questions
        # prefetch된 경우 len 사용
        if hasattr(obj, '_prefetched_objects_cache') and 'questions' in obj._prefetched_objects_cache:
            return len(obj.questions.all())
        # 마지막 수단: count() 사용
        return obj.questions.count()
    
    def get_created_by(self, obj):
        """시험 생성자 정보 반환"""
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'username': obj.created_by.username,
                'email': obj.created_by.email
            }
        return None
    
    def get_questions(self, obj):
        """문제 목록 반환 (목록 관리용 - 상세 내용 제외)"""
        questions = obj.questions.all()
        return [
            {
                'id': q.id,
                'title_ko': q.title_ko,
                'title_en': q.title_en,
                'difficulty': q.difficulty,
                'url': q.url,
                'group_id': q.group_id,
                'created_at': q.created_at,
                'updated_at': q.updated_at,
                'csv_id': q.csv_id,
                'created_language': q.created_language,
                'is_ko_complete': q.is_ko_complete,
                'is_en_complete': q.is_en_complete,
                'created_by': q.created_by.id if q.created_by else None
            }
            for q in questions
        ]


class ExamListSerializer(serializers.ModelSerializer):
    """시험 목록 조회용 최적화된 시리얼라이저 - 필요한 필드만 반환"""
    display_title = serializers.SerializerMethodField()
    total_questions = serializers.SerializerMethodField()
    has_results = serializers.SerializerMethodField()
    latest_score_percentage = serializers.SerializerMethodField()
    latest_correct_count = serializers.SerializerMethodField()
    latest_total_score = serializers.SerializerMethodField()
    user_correct_questions = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    
    # 사용자별 합격률 필드 추가 (exam-detail과 동일한 로직)
    accuracy_percentage = serializers.SerializerMethodField()
    
    # 태그를 객체 배열로 반환
    tags = TagSerializer(many=True, read_only=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 같은 시험에 대해 _get_latest_result 결과를 캐싱
        self._latest_result_cache = {}
    
    class Meta:
        model = Exam
        fields = [
            'id', 'title_ko', 'title_en', 'display_title', 'is_original', 'original_exam',
            'version_number', 'is_public', 'created_at', 'total_questions', 'has_results',
            'latest_score_percentage', 'latest_correct_count', 'latest_total_score', 'user_correct_questions',
            'created_by', 'accuracy_percentage', 'tags', 'ai_mock_interview'
        ]
    
    def get_display_title(self, obj):
        """사용자 언어에 맞는 제목 반환"""
        # 1. 컨텍스트에서 명시적으로 전달된 언어 정보 우선 사용
        context_language = self.context.get('user_language')
        if context_language:
            return get_localized_field(obj, 'title', context_language, '')
        
        # 2. fallback: request에서 사용자 언어 확인
        request = self.context.get('request')
        user_language = get_user_language(request)
        return get_localized_field(obj, 'title', user_language, '')
    
    def get_total_questions(self, obj):
        """실제 문제 수를 동적으로 계산"""
        # annotate로 계산된 total_questions_count가 있으면 사용
        if hasattr(obj, 'total_questions_count'):
            return obj.total_questions_count
        # total_questions 필드가 있으면 사용
        if hasattr(obj, 'total_questions') and obj.total_questions is not None:
            return obj.total_questions
        # prefetch된 경우 len 사용
        if hasattr(obj, '_prefetched_objects_cache') and 'questions' in obj._prefetched_objects_cache:
            return len(obj.questions.all())
        # 마지막 수단: count() 사용
        return obj.questions.count()
    
    def _get_latest_result(self, obj):
        """prefetch된 최신 결과를 가져오는 헬퍼 메서드 (캐싱 지원)"""
        request = self.context.get('request')
        if not request or not request.user or not hasattr(request.user, 'is_authenticated') or not request.user.is_authenticated:
            return None
        
        # 캐시 확인 (같은 시험에 대해 여러 번 호출되는 것을 방지)
        exam_id_str = str(obj.id)
        if hasattr(self, '_latest_result_cache') and exam_id_str in self._latest_result_cache:
            return self._latest_result_cache[exam_id_str]
        
        # context에서 prefetch된 결과 딕셔너리 가져오기
        user_latest_results_dict = self.context.get('user_latest_results_dict', {})
        
        # 현재 시험 ID로 먼저 확인
        if exam_id_str in user_latest_results_dict:
            result = user_latest_results_dict[exam_id_str]
            # 캐시에 저장
            if hasattr(self, '_latest_result_cache'):
                self._latest_result_cache[exam_id_str] = result
            return result
        
        # 복사된 시험인 경우 원본 시험의 결과를 찾기
        if not obj.is_original and obj.original_exam:
            original_exam_id_str = str(obj.original_exam.id)
            if original_exam_id_str in user_latest_results_dict:
                result = user_latest_results_dict[original_exam_id_str]
                # 캐시에 저장 (현재 시험 ID로도 저장)
                if hasattr(self, '_latest_result_cache'):
                    self._latest_result_cache[exam_id_str] = result
                    self._latest_result_cache[original_exam_id_str] = result
                return result
        
        # user_latest_results_dict에 없는 경우 None으로 처리 (fallback 쿼리 방지)
        # 이는 해당 시험에 결과가 없다는 의미이므로 None 반환
        if hasattr(self, '_latest_result_cache'):
            self._latest_result_cache[exam_id_str] = None
        return None
    
    def get_has_results(self, obj):
        """현재 사용자의 시험 결과 존재 여부"""
        latest_result = self._get_latest_result(obj)
        return latest_result is not None
    
    def get_latest_score_percentage(self, obj):
        """현재 사용자의 최신 시험 결과 백분율"""
        latest_result = self._get_latest_result(obj)
        if latest_result and latest_result.total_score:
            return (latest_result.score / latest_result.total_score) * 100
        return None
    
    def get_latest_correct_count(self, obj):
        """현재 사용자의 최신 시험 결과 정답 수"""
        latest_result = self._get_latest_result(obj)
        return latest_result.correct_count if latest_result else None
    
    def get_latest_total_score(self, obj):
        """현재 사용자의 최신 시험 결과 총점"""
        latest_result = self._get_latest_result(obj)
        return latest_result.total_score if latest_result else None
    
    def get_user_correct_questions(self, obj):
        """현재 사용자의 맞춘 문제 수 계산"""
        request = self.context.get('request')
        if not request or not request.user or not hasattr(request.user, 'is_authenticated') or not request.user.is_authenticated:
            return None
        
        # context에서 prefetch된 통계 딕셔너리 가져오기
        user_correct_questions_dict = self.context.get('user_correct_questions_dict', {})
        exam_id_str = str(obj.id)
        
        if exam_id_str in user_correct_questions_dict:
            return user_correct_questions_dict[exam_id_str]
        
        # 복사된 시험인 경우 원본 시험의 통계 확인
        if not obj.is_original and obj.original_exam:
            original_exam_id_str = str(obj.original_exam.id)
            if original_exam_id_str in user_correct_questions_dict:
                return user_correct_questions_dict[original_exam_id_str]
        
        # prefetch되지 않은 경우에만 쿼리 실행 (fallback)
        target_exam = obj.original_exam if not obj.is_original and obj.original_exam else obj
        return target_exam.get_total_correct_questions_for_user(request.user)

    def get_accuracy_percentage(self, obj):
        """현재 사용자의 합격률 계산 (exam-detail과 동일한 로직)"""
        request = self.context.get('request')
        if not request or not request.user or not hasattr(request.user, 'is_authenticated') or not request.user.is_authenticated:
            return None
        
        # context에서 prefetch된 통계 딕셔너리 가져오기
        user_accuracy_percentage_dict = self.context.get('user_accuracy_percentage_dict', {})
        exam_id_str = str(obj.id)
        
        if exam_id_str in user_accuracy_percentage_dict:
            return user_accuracy_percentage_dict[exam_id_str]
        
        # 복사된 시험인 경우 원본 시험의 통계 확인
        if not obj.is_original and obj.original_exam:
            original_exam_id_str = str(obj.original_exam.id)
            if original_exam_id_str in user_accuracy_percentage_dict:
                return user_accuracy_percentage_dict[original_exam_id_str]
        
        # prefetch되지 않은 경우에만 쿼리 실행 (fallback)
        target_exam = obj.original_exam if not obj.is_original and obj.original_exam else obj
        return target_exam.get_accuracy_percentage_for_user(request.user)

    def get_created_by(self, obj):
        """시험 생성자 정보 반환"""
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'username': obj.created_by.username,
                'email': obj.created_by.email
            }
        return None
    
    def get_display_description(self, obj):
        """사용자 언어에 맞는 설명 반환"""
        # 1. 컨텍스트에서 명시적으로 전달된 언어 정보 우선 사용
        context_language = self.context.get('user_language')
        if context_language:
            from quiz.utils.multilingual_utils import LANGUAGE_KO, LANGUAGE_EN, LANGUAGE_ES, LANGUAGE_ZH, LANGUAGE_JA
            # 타입 안전성을 위해 문자열로 변환하여 비교
            context_language_str = str(context_language).strip() if context_language else None
            if context_language_str == LANGUAGE_KO:
                return obj.description_ko or obj.description_en or (getattr(obj, 'description_es', None) or '') or (getattr(obj, 'description_zh', None) or '') or ''
            elif context_language_str == LANGUAGE_EN:
                return obj.description_en or obj.description_ko or (getattr(obj, 'description_es', None) or '') or (getattr(obj, 'description_zh', None) or '') or ''
            elif context_language_str == LANGUAGE_ES:
                return (getattr(obj, 'description_es', None) or '') or obj.description_en or obj.description_ko or (getattr(obj, 'description_zh', None) or '') or ''
            elif context_language_str == LANGUAGE_ZH:
                return (getattr(obj, 'description_zh', None) or '') or obj.description_en or obj.description_ko or (getattr(obj, 'description_es', None) or '') or (getattr(obj, 'description_ja', None) or '') or ''
            elif context_language_str == LANGUAGE_JA:
                return (getattr(obj, 'description_ja', None) or '') or obj.description_en or obj.description_ko or (getattr(obj, 'description_es', None) or '') or (getattr(obj, 'description_zh', None) or '') or ''
            else:
                return obj.description_en or obj.description_ko or (getattr(obj, 'description_es', None) or '') or (getattr(obj, 'description_zh', None) or '') or (getattr(obj, 'description_ja', None) or '') or ''
        
        # 2. fallback: request에서 사용자 언어 확인
        request = self.context.get('request')
        if not request:
            return obj.description_ko or obj.description_en or (getattr(obj, 'description_es', None) or '') or (getattr(obj, 'description_zh', None) or '') or ''
        
        from quiz.utils.multilingual_utils import BASE_LANGUAGE
        user_language = BASE_LANGUAGE  # 기본값
        if hasattr(request, 'user') and request.user and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated:
            if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'language'):
                user_language = request.user.profile.language
            elif hasattr(request.user, 'userprofile') and hasattr(request.user.userprofile, 'language'):
                user_language = request.user.userprofile.language
        
        from quiz.utils.multilingual_utils import LANGUAGE_KO, LANGUAGE_EN, LANGUAGE_ES, LANGUAGE_ZH, LANGUAGE_JA
        if user_language == LANGUAGE_KO:
            return obj.description_ko or obj.description_en or (getattr(obj, 'description_es', None) or '') or (getattr(obj, 'description_zh', None) or '') or ''
        elif user_language == LANGUAGE_EN:
            return obj.description_en or obj.description_ko or (getattr(obj, 'description_es', None) or '') or (getattr(obj, 'description_zh', None) or '') or ''
        elif user_language == LANGUAGE_ES:
            return (getattr(obj, 'description_es', None) or '') or obj.description_en or obj.description_ko or (getattr(obj, 'description_zh', None) or '') or ''
        elif user_language == LANGUAGE_ZH:
            return (getattr(obj, 'description_zh', None) or '') or obj.description_en or obj.description_ko or (getattr(obj, 'description_es', None) or '') or (getattr(obj, 'description_ja', None) or '') or ''
        elif user_language == LANGUAGE_JA:
            return (getattr(obj, 'description_ja', None) or '') or obj.description_en or obj.description_ko or (getattr(obj, 'description_es', None) or '') or (getattr(obj, 'description_zh', None) or '') or ''
        else:
            return obj.description_en or obj.description_ko or (getattr(obj, 'description_es', None) or '') or (getattr(obj, 'description_zh', None) or '') or (getattr(obj, 'description_ja', None) or '') or ''


class ExamSerializer(MultilingualSerializerMixin, serializers.ModelSerializer):
    """
    시험 모델용 다국어 시리얼라이저 (예시)
    
    다국어 필드:
    - title_ko, title_en (시험 제목)
    - description_ko, description_en (시험 설명)
    """
    
    # 문제 목록 필드 (성능 최적화 적용)
    questions = serializers.SerializerMethodField()
    
    # 다국어 필드를 위한 SerializerMethodField
    localized_title = serializers.SerializerMethodField()
    localized_description = serializers.SerializerMethodField()
    available_languages = serializers.SerializerMethodField()
    
    # display_title 필드 추가 (사용자 언어에 맞는 제목)
    display_title = serializers.SerializerMethodField()
    display_description = serializers.SerializerMethodField()
    
    # created_by 필드를 SerializerMethodField로 변경
    created_by = serializers.SerializerMethodField()
    
    # 사용자별 정답 개수 필드 추가
    user_correct_questions = serializers.SerializerMethodField()
    
    # 사용자별 합격률 필드 추가 (exam-detail과 동일한 로직)
    accuracy_percentage = serializers.SerializerMethodField()
    
    # 태그를 객체 배열로 반환
    tags = TagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Exam
        fields = [
            'id', 'title_ko', 'title_en', 'title_zh', 'title_es', 'title_ja', 'description_ko', 'description_en', 'description_zh', 'description_es', 'description_ja',
            'questions', 'is_public', 'is_original', 'created_at',
            'created_language'
        ] + get_completion_fields() + [
            'created_by', 'total_questions', 'file_name', 'force_answer',
            'voice_mode_enabled', 'ai_mock_interview', 'localized_title', 'localized_description', 'available_languages',
            'display_title', 'display_description',
            'user_correct_questions', 'accuracy_percentage', 'tags', 'supported_languages', 'exam_difficulty', 'age_rating'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 다국어 필드 지정 (공통 모듈에서 사용)
        self.multilingual_fields = ['title', 'description']

    def get_versions(self, obj):
        """원본 시험의 경우 버전 목록 반환"""
        if obj.is_original:
            versions = Exam.objects.filter(original_exam=obj).order_by('version_number')
            return ExamSerializer(versions, many=True).data
        return []

    def get_total_questions(self, obj):
        """실제 문제 수를 동적으로 계산"""
        # annotate로 계산된 total_questions_count가 있으면 사용
        if hasattr(obj, 'total_questions_count'):
            return obj.total_questions_count
        # total_questions 필드가 있으면 사용
        if hasattr(obj, 'total_questions') and obj.total_questions is not None:
            return obj.total_questions
        # prefetch된 경우 len 사용
        if hasattr(obj, '_prefetched_objects_cache') and 'questions' in obj._prefetched_objects_cache:
            return len(obj.questions.all())
        # 마지막 수단: count() 사용
        return obj.questions.count()

    def get_user_correct_questions(self, obj):
        """현재 사용자의 맞춘 문제 수 계산"""
        request = self.context.get('request')
        if not request or not request.user or not hasattr(request.user, 'is_authenticated') or not request.user.is_authenticated:
            return 0
        
        # context에서 prefetch된 통계 값 사용 (N+1 쿼리 방지)
        user_correct_questions = self.context.get('user_correct_questions')
        if user_correct_questions is not None:
            return user_correct_questions
        
        # Fallback: prefetch되지 않은 경우에만 쿼리 실행
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"[EXAM_SERIALIZER] get_user_correct_questions fallback 쿼리 실행 - exam_id: {obj.id}")
        return obj.get_total_correct_questions_for_user(request.user)
    
    def get_accuracy_percentage(self, obj):
        """현재 사용자의 합격률 계산 (exam-detail과 동일한 로직)"""
        request = self.context.get('request')
        if not request or not request.user or not hasattr(request.user, 'is_authenticated') or not request.user.is_authenticated:
            return None
        
        # context에서 prefetch된 통계 값 사용 (N+1 쿼리 방지)
        user_accuracy_percentage = self.context.get('user_accuracy_percentage')
        if user_accuracy_percentage is not None:
            return user_accuracy_percentage
        
        # Fallback: prefetch되지 않은 경우에만 쿼리 실행
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"[EXAM_SERIALIZER] get_accuracy_percentage fallback 쿼리 실행 - exam_id: {obj.id}")
        return obj.get_accuracy_percentage_for_user(request.user)
    
    def get_created_by(self, obj):
        """시험 생성자 정보 반환"""
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'username': obj.created_by.username,
                'email': obj.created_by.email
            }
        return None
    
    def get_display_title(self, obj):
        """사용자 언어에 맞는 제목 반환"""
        # 1. 컨텍스트에서 명시적으로 전달된 언어 정보 우선 사용
        context_language = self.context.get('user_language')
        if context_language:
            return get_localized_field(obj, 'title', context_language, '')
        
        # 2. fallback: request에서 사용자 언어 확인
        request = self.context.get('request')
        user_language = get_user_language(request)
        return get_localized_field(obj, 'title', user_language, '')
    
    def get_display_description(self, obj):
        """사용자 언어에 맞는 설명 반환"""
        # 1. 컨텍스트에서 명시적으로 전달된 언어 정보 우선 사용
        context_language = self.context.get('user_language')
        if context_language:
            from quiz.utils.multilingual_utils import LANGUAGE_KO, LANGUAGE_EN, LANGUAGE_ES, LANGUAGE_ZH, LANGUAGE_JA
            # 타입 안전성을 위해 문자열로 변환하여 비교
            context_language_str = str(context_language).strip() if context_language else None
            if context_language_str == LANGUAGE_KO:
                return obj.description_ko or obj.description_en or (getattr(obj, 'description_es', None) or '') or (getattr(obj, 'description_zh', None) or '') or ''
            elif context_language_str == LANGUAGE_EN:
                return obj.description_en or obj.description_ko or (getattr(obj, 'description_es', None) or '') or (getattr(obj, 'description_zh', None) or '') or ''
            elif context_language_str == LANGUAGE_ES:
                return (getattr(obj, 'description_es', None) or '') or obj.description_en or obj.description_ko or (getattr(obj, 'description_zh', None) or '') or ''
            elif context_language_str == LANGUAGE_ZH:
                return (getattr(obj, 'description_zh', None) or '') or obj.description_en or obj.description_ko or (getattr(obj, 'description_es', None) or '') or (getattr(obj, 'description_ja', None) or '') or ''
            elif context_language_str == LANGUAGE_JA:
                return (getattr(obj, 'description_ja', None) or '') or obj.description_en or obj.description_ko or (getattr(obj, 'description_es', None) or '') or (getattr(obj, 'description_zh', None) or '') or ''
            else:
                return obj.description_en or obj.description_ko or (getattr(obj, 'description_es', None) or '') or (getattr(obj, 'description_zh', None) or '') or (getattr(obj, 'description_ja', None) or '') or ''
        
        # 2. fallback: request에서 사용자 언어 확인
        request = self.context.get('request')
        if not request:
            return obj.description_ko or obj.description_en or (getattr(obj, 'description_es', None) or '') or (getattr(obj, 'description_zh', None) or '') or ''
        
        from quiz.utils.multilingual_utils import BASE_LANGUAGE
        user_language = BASE_LANGUAGE  # 기본값
        if hasattr(request, 'user') and request.user and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated:
            if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'language'):
                user_language = request.user.profile.language
            elif hasattr(request.user, 'userprofile') and hasattr(request.user.userprofile, 'language'):
                user_language = request.user.userprofile.language
        
        from quiz.utils.multilingual_utils import LANGUAGE_KO, LANGUAGE_EN, LANGUAGE_ES, LANGUAGE_ZH, LANGUAGE_JA
        if user_language == LANGUAGE_KO:
            return obj.description_ko or obj.description_en or (getattr(obj, 'description_es', None) or '') or (getattr(obj, 'description_zh', None) or '') or ''
        elif user_language == LANGUAGE_EN:
            return obj.description_en or obj.description_ko or (getattr(obj, 'description_es', None) or '') or (getattr(obj, 'description_zh', None) or '') or ''
        elif user_language == LANGUAGE_ES:
            return (getattr(obj, 'description_es', None) or '') or obj.description_en or obj.description_ko or (getattr(obj, 'description_zh', None) or '') or ''
        elif user_language == LANGUAGE_ZH:
            return (getattr(obj, 'description_zh', None) or '') or obj.description_en or obj.description_ko or (getattr(obj, 'description_es', None) or '') or (getattr(obj, 'description_ja', None) or '') or ''
        elif user_language == LANGUAGE_JA:
            return (getattr(obj, 'description_ja', None) or '') or obj.description_en or obj.description_ko or (getattr(obj, 'description_es', None) or '') or (getattr(obj, 'description_zh', None) or '') or ''
        else:
            return obj.description_en or obj.description_ko or (getattr(obj, 'description_es', None) or '') or (getattr(obj, 'description_zh', None) or '') or (getattr(obj, 'description_ja', None) or '') or ''
    
    def get_localized_title(self, obj):
        """현재 사용자 언어에 맞는 제목 반환"""
        request = self.context.get('request')
        user_language = get_user_language(request)
        return get_localized_field(obj, 'title', user_language, '')
    
    def get_localized_description(self, obj):
        """현재 사용자 언어에 맞는 설명 반환"""
        request = self.context.get('request')
        user_language = get_user_language(request)
        return get_localized_field(obj, 'description', user_language, '')
    

    
    def get_questions(self, obj):
        """성능 최적화된 문제 목록 반환 (필요한 필드만) + 개별 번역 처리"""
        import logging
        logger = logging.getLogger(__name__)
        
        # prefetch_related로 이미 가져온 questions 사용 (추가 쿼리 방지)
        if hasattr(obj, '_prefetched_objects_cache') and 'questions' in obj._prefetched_objects_cache:
            questions = obj._prefetched_objects_cache['questions']
        else:
            # prefetch되지 않은 경우에만 쿼리 실행 (fallback)
            logger.debug(f"[EXAM_SERIALIZER] get_questions fallback 쿼리 실행 - exam_id: {obj.id}")
            # 문제 목록을 가져오되, 다국어 필드만 포함하여 번역 부담 최소화
            # 마이그레이션이 적용되지 않은 환경을 위해 필요한 필드만 선택
            from quiz.utils.multilingual_utils import get_completion_fields
            completion_fields = get_completion_fields()
            questions = obj.questions.all().only(
                'id', 'title_ko', 'title_en', 'content_ko', 'content_en',
                'answer_ko', 'answer_en', 'explanation_ko', 'explanation_en',
                'difficulty', 'url', 'group_id', 'created_at', 'updated_at',
                'csv_id', 'created_language', 'created_by',
                *completion_fields
            )
        
        # 자동 번역이 활성화된 경우에만 번역 처리
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            auto_translation_enabled = is_auto_translation_enabled(request.user)
            
            if auto_translation_enabled:
                # 각 문제에 대해 개별 번역 처리
                # MultilingualContentManager가 내부에서 번역 필요성을 올바르게 판단하므로
                # 여기서는 직접 확인하지 않고 항상 MultilingualContentManager를 호출합니다.
                for question in questions:
                    try:
                        from quiz.utils.multilingual_utils import MultilingualContentManager
                        
                        # Question 모델용 다국어 필드 지정
                        question_multilingual_fields = ['title', 'content', 'answer', 'explanation']
                        
                        # MultilingualContentManager로 개별 번역 처리
                        # MultilingualContentManager가 내부에서 번역 필요성을 올바르게 판단합니다.
                        # - user_language가 'en'이고 created_language가 'ko'인 경우
                        #   → title_ko를 확인하고 title_en이 비어있으면 ko → en 번역
                        # - user_language가 'ko'인 경우
                        #   → title_ko를 확인하고 title_en이 비어있으면 ko → en 번역
                        # 조회 시에는 완성도 상태 업데이트를 건너뛰기 (skip_completion_update=True)
                        manager = MultilingualContentManager(question, request.user, question_multilingual_fields, skip_completion_update=True)
                        manager.handle_multilingual_update()
                        
                        # 번역 후 데이터베이스에서 최신 정보 가져오기
                        question.refresh_from_db()
                        
                    except Exception as e:
                        logger.warning(f"[EXAM_SERIALIZER] 문제 {question.id} 번역 처리 실패: {str(e)}")
        
        return [
            {
                'id': q.id,
                'title_ko': q.title_ko,
                'title_en': q.title_en,
                'title_es': getattr(q, 'title_es', None),
                'title_zh': getattr(q, 'title_zh', None),
                'title_ja': getattr(q, 'title_ja', None),
                'content_ko': q.content_ko,
                'content_en': q.content_en,
                'content_es': getattr(q, 'content_es', None),
                'content_zh': getattr(q, 'content_zh', None),
                'content_ja': getattr(q, 'content_ja', None),
                'answer_ko': q.answer_ko,
                'answer_en': q.answer_en,
                'answer_es': getattr(q, 'answer_es', None),
                'answer_zh': getattr(q, 'answer_zh', None),
                'answer_ja': getattr(q, 'answer_ja', None),
                'explanation_ko': q.explanation_ko,
                'explanation_en': q.explanation_en,
                'explanation_es': getattr(q, 'explanation_es', None),
                'explanation_zh': getattr(q, 'explanation_zh', None),
                'explanation_ja': getattr(q, 'explanation_ja', None),
                'difficulty': q.difficulty,
                'url': q.url,
                'group_id': q.group_id,
                'created_at': q.created_at,
                'updated_at': q.updated_at,
                'csv_id': q.csv_id,
                'created_language': q.created_language,
                'is_ko_complete': q.is_ko_complete,
                'is_en_complete': q.is_en_complete,
                'is_es_complete': getattr(q, 'is_es_complete', False),
                'is_zh_complete': getattr(q, 'is_zh_complete', False),
                'is_ja_complete': getattr(q, 'is_ja_complete', False),
                'created_by': q.created_by.id if q.created_by else None
            }
            for q in questions
        ]
    
    def get_available_languages(self, obj):
        """사용 가능한 언어 목록"""
        from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
        languages = []
        for lang in SUPPORTED_LANGUAGES:
            # Exam 모델은 title과 description 필드가 모두 있어야 완전한 것으로 간주
            title_field = f'title_{lang}'
            description_field = f'description_{lang}'
            if (hasattr(obj, title_field) and getattr(obj, title_field, None) and
                hasattr(obj, description_field) and getattr(obj, description_field, None)):
                languages.append(lang)
        return languages


class ExamResultDetailSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)
    
    class Meta:
        model = ExamResultDetail
        fields = ['id', 'question', 'user_answer', 'is_correct']


class ExamResultSerializer(serializers.ModelSerializer):
    exam = ExamSerializer(read_only=True)
    details = serializers.SerializerMethodField()
    wrong_questions = serializers.SerializerMethodField()

    class Meta:
        model = ExamResult
        fields = ['id', 'exam', 'score', 'total_score', 'correct_count', 'wrong_count', 'completed_at', 'details', 'elapsed_seconds', 'wrong_questions']

    def get_details(self, obj):
        details_qs = obj.examresultdetail_set.all()
        return ExamResultDetailSerializer(details_qs, many=True).data

    def get_wrong_questions(self, obj):
        """틀린 문제들의 ID 목록 반환"""
        wrong_details = obj.examresultdetail_set.filter(is_correct=False)
        return [detail.question.id for detail in wrong_details]


class CreateExamSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    question_count = serializers.IntegerField(min_value=0, max_value=1000, required=False)
    wrong_questions_only = serializers.BooleanField(default=False)
    random_option = serializers.ChoiceField(
        choices=[('random', '그냥 랜덤'), ('wrong_only', '틀린 문제만'), ('most_wrong', '많이 틀린 문제')],
        default='random',
        required=False
    )
    questions = serializers.ListField(
        child=serializers.UUIDField(),
        required=False
    )
    is_original = serializers.BooleanField(default=True)
    is_public = serializers.BooleanField(default=True)
    force_answer = serializers.BooleanField(default=False)
    difficulty = serializers.CharField(required=False, allow_blank=True)
    exam_difficulty = serializers.IntegerField(min_value=1, max_value=10, required=False, default=5)
    parsed_problems = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True
    )


class SubmitExamSerializer(serializers.Serializer):
    exam_id = serializers.UUIDField()
    answers = serializers.ListField(
        child=serializers.DictField()
    ) 


class StudyTaskSerializer(MultilingualSerializerMixin, serializers.ModelSerializer):
    exam_title = serializers.SerializerMethodField()
    effective_progress = serializers.FloatField(read_only=True)
    exam = ExamSerializer(read_only=True)
    study = serializers.SerializerMethodField()  # study 정보를 메서드로 반환
    user_progress = serializers.SerializerMethodField()
    attempted_progress = serializers.SerializerMethodField()
    correct_progress = serializers.SerializerMethodField()
    
    # 사용자별 합격률 필드 추가 (exam-management과 동일한 로직)
    accuracy_percentage = serializers.SerializerMethodField()
    
    # 정확도 계산 근거를 위한 필드 추가
    correct_attempts = serializers.SerializerMethodField()
    total_attempts = serializers.SerializerMethodField()
    
    # 다국어 필드들
    name_ko = serializers.CharField(required=False, allow_blank=True)
    name_en = serializers.CharField(required=False, allow_blank=True)
    
    # 언어별 완성도
    is_ko_complete = serializers.BooleanField(read_only=True)
    is_en_complete = serializers.BooleanField(read_only=True)
    created_language = serializers.CharField(read_only=True)
    
    class Meta:
        model = StudyTask
        fields = [
            'id', 'study', 'name_ko', 'name_en', 'progress', 'exam', 'exam_title', 
            'effective_progress', 'user_progress', 'attempted_progress', 'correct_progress', 
            'accuracy_percentage', 'correct_attempts', 'total_attempts', 'is_public', 'seq', 'is_ko_complete', 'is_en_complete', 'created_language'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 다국어 필드 지정 (MultilingualSerializerMixin에서 사용)
        self.multilingual_fields = ['name']
    
    def to_representation(self, instance):
        """응답 데이터 변환 시 다국어 콘텐츠 최적화 및 권한 확인"""
        data = super().to_representation(instance)
        
        # exam 필드 권한 확인
        if instance.exam and 'exam' in data and data['exam']:
            exam = instance.exam
            request = self.context.get('request')
            user = request.user if request else None
            study = instance.study
            
            # 비공개 시험인 경우 권한 확인
            if not exam.is_public:
                has_permission = False
                
                # 관리자는 모든 시험 접근 가능
                if user and user.is_authenticated:
                    if hasattr(user, 'profile') and hasattr(user.profile, 'role') and user.profile.role == 'admin_role':
                        has_permission = True
                    else:
                        # 사용자가 시험 생성자인지 확인
                        is_creator = exam.created_by == user if exam.created_by else False
                        
                        # 사용자가 스터디 멤버인지 확인
                        is_study_member = False
                        if study:
                            is_study_member = Member.objects.filter(
                                user=user,
                                study=study,
                                is_active=True
                            ).exists()
                        
                        # 사용자가 시험을 이미 풀어본 적이 있는지 확인
                        has_taken_exam = ExamResult.objects.filter(
                            user=user,
                            exam=exam
                        ).exists()
                        
                        has_permission = is_creator or is_study_member or has_taken_exam
                
                # 권한이 없으면 exam 필드를 None으로 설정
                if not has_permission:
                    data['exam'] = None
                    data['exam_title'] = None
        
        # 기존 API 호환성을 위해 name 필드를 계산된 값으로 제공
        # 현재 사용자 언어에 맞는 이름 설정
        from quiz.utils.multilingual_utils import BASE_LANGUAGE
        if hasattr(self, 'context') and 'request' in self.context:
            request = self.context['request']
            if hasattr(request, 'user') and request.user and hasattr(request.user, 'is_anonymous') and not request.user.is_anonymous:
                try:
                    user_profile = request.user.profile
                    user_language = user_profile.language
                except:
                    user_language = BASE_LANGUAGE  # 기본값
            else:
                user_language = BASE_LANGUAGE  # 기본값
            
            # 언어에 맞는 이름 설정
            from quiz.utils.multilingual_utils import LANGUAGE_KO, LANGUAGE_EN, LANGUAGE_ES, LANGUAGE_ZH, LANGUAGE_JA
            if user_language == LANGUAGE_KO:
                data['name'] = instance.name_ko or instance.name_en or (getattr(instance, 'name_es', None) or '') or (getattr(instance, 'name_zh', None) or '') or ''
            elif user_language == LANGUAGE_EN:
                data['name'] = instance.name_en or instance.name_ko or (getattr(instance, 'name_es', None) or '') or (getattr(instance, 'name_zh', None) or '') or ''
            elif user_language == LANGUAGE_ES:
                data['name'] = (getattr(instance, 'name_es', None) or '') or instance.name_en or instance.name_ko or (getattr(instance, 'name_zh', None) or '') or ''
            elif user_language == LANGUAGE_ZH:
                data['name'] = (getattr(instance, 'name_zh', None) or '') or instance.name_en or instance.name_ko or (getattr(instance, 'name_es', None) or '') or ''
            else:
                data['name'] = instance.name_en or instance.name_ko or (getattr(instance, 'name_es', None) or '') or (getattr(instance, 'name_zh', None) or '') or ''
        else:
            # context가 없는 경우 기본값 사용
            data['name'] = instance.name_ko or instance.name_en or (getattr(instance, 'name_es', None) or '') or (getattr(instance, 'name_zh', None) or '') or ''
        
        return data

    def get_study(self, obj):
        """스터디 정보를 완전한 객체로 반환"""
        if obj.study:
            # prefetch된 members 사용 (N+1 쿼리 방지)
            if hasattr(obj.study, '_prefetched_objects_cache') and 'members' in obj.study._prefetched_objects_cache:
                members = obj.study._prefetched_objects_cache['members']
            else:
                members = obj.study.members.all()
            
            return {
                'id': obj.study.id,
                'title': obj.study.title_ko or obj.study.title_en or 'Unknown',
                'members': [
                    {
                        'id': member.id,
                        'user': member.user.id if member.user else None,
                        'user_username': member.user.username if member.user else None,
                        'user_email': member.user.email if member.user else None,
                        'name': member.name,
                        'email': member.email,
                        'member_id': member.member_id,
                        'affiliation': member.affiliation,
                        'location': member.location,
                        'role': member.role,
                        'is_active': member.is_active,
                        'created_at': member.created_at,
                        'updated_at': member.updated_at
                    }
                    for member in members
                ]
            }
        return None

    def get_exam_title(self, obj):
        """시험 제목을 현재 사용자 언어에 맞게 반환"""
        from quiz.utils.multilingual_utils import BASE_LANGUAGE
        
        if not obj.exam:
            return ''
        
        # 현재 사용자 언어 확인
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user and hasattr(request.user, 'is_anonymous') and not request.user.is_anonymous:
            try:
                user_profile = request.user.profile
                user_language = user_profile.language
            except:
                user_language = BASE_LANGUAGE  # 기본값
        else:
            user_language = BASE_LANGUAGE  # 기본값
        
        # 언어에 맞는 제목 반환
        from quiz.utils.multilingual_utils import LANGUAGE_KO, LANGUAGE_EN, LANGUAGE_ES, LANGUAGE_ZH, LANGUAGE_JA
        if user_language == LANGUAGE_KO:
            return obj.exam.title_ko or obj.exam.title_en or (getattr(obj.exam, 'title_es', None) or '') or (getattr(obj.exam, 'title_zh', None) or '') or ''
        elif user_language == LANGUAGE_EN:
            return obj.exam.title_en or obj.exam.title_ko or (getattr(obj.exam, 'title_es', None) or '') or (getattr(obj.exam, 'title_zh', None) or '') or ''
        elif user_language == LANGUAGE_ES:
            return (getattr(obj.exam, 'title_es', None) or '') or obj.exam.title_en or obj.exam.title_ko or (getattr(obj.exam, 'title_zh', None) or '') or ''
        elif user_language == LANGUAGE_ZH:
            return (getattr(obj.exam, 'title_zh', None) or '') or obj.exam.title_en or obj.exam.title_ko or (getattr(obj.exam, 'title_es', None) or '') or (getattr(obj.exam, 'title_ja', None) or '') or ''
        elif user_language == LANGUAGE_JA:
            return (getattr(obj.exam, 'title_ja', None) or '') or obj.exam.title_en or obj.exam.title_ko or (getattr(obj.exam, 'title_es', None) or '') or (getattr(obj.exam, 'title_zh', None) or '') or ''
        else:
            return obj.exam.title_en or obj.exam.title_ko or (getattr(obj.exam, 'title_es', None) or '') or (getattr(obj.exam, 'title_zh', None) or '') or (getattr(obj.exam, 'title_ja', None) or '') or ''
    
    def get_user_progress(self, obj):
        """사용자 진행률 반환 (context의 user_progress_dict 사용하여 N+1 쿼리 방지)"""
        user = self.context.get('request').user if self.context.get('request') else None
        if not user or user.is_anonymous:
            return 0
        
        # context에 미리 로드된 user_progress_dict 사용
        user_progress_dict = self.context.get('user_progress_dict', {})
        if obj.id in user_progress_dict:
            return user_progress_dict[obj.id]
        
        # 폴백: context에 없으면 쿼리 실행 (하지만 가능한 한 피해야 함)
        from .models import StudyTaskProgress
        progress_obj = StudyTaskProgress.objects.filter(user=user, study_task=obj).first()
        return progress_obj.progress if progress_obj else 0

    def get_attempted_progress(self, obj):
        """해당 태스크에서 시도한 문제의 진행률을 계산합니다 (고유하게 시도한 문제 수/전체 문제 수, 최대 100%)."""
        try:
            user = self.context.get('request').user if self.context.get('request') else None
            if not user or user.is_anonymous:
                return 0
            
            if not obj.exam:
                return 0
            
            # 해당 사용자가 해당 시험에서 시도한 문제 수와 전체 문제 수 계산
            total_attempts = obj.exam.get_total_attempted_questions_for_user(user)
            total_questions = obj.exam.questions.count()
            
            if total_questions > 0:
                # 진행률: 고유하게 시도한 문제 수 / 전체 문제 수 (최대 100%)
                # total_attempts가 total_questions를 넘을 수 있으므로 제한
                unique_attempted_questions = min(total_attempts, total_questions)
                return (unique_attempted_questions / total_questions) * 100
            else:
                return 0
        except Exception as e:
            print(f"❌ Error calculating attempted progress for task {obj.id}: {str(e)}")
            return 0

    def get_correct_progress(self, obj):
        """해당 태스크에서 맞춘 시도의 정확도를 계산합니다 (맞춘 시도 수/전체 시도 수)."""
        try:
            user = self.context.get('request').user if self.context.get('request') else None
            if not user or user.is_anonymous:
                return 0
            
            if not obj.exam:
                return 0
            
            # 해당 사용자가 해당 시험에서 맞춘 시도 수와 전체 시도 수 계산
            correct_attempts = obj.exam.get_total_correct_questions_for_user(user)
            total_attempts = obj.exam.get_total_attempted_questions_for_user(user)
            
            if total_attempts > 0:
                # 정확도: 맞춘 시도 수 / 전체 시도 수
                return (correct_attempts / total_attempts) * 100
            else:
                return 0
        except Exception as e:
            print(f"❌ Error calculating correct progress for task {obj.id}: {str(e)}")
            return 0

    def get_accuracy_percentage(self, obj):
        """현재 사용자의 합격률 계산 (exam-management과 동일한 로직)"""
        try:
            user = self.context.get('request').user if self.context.get('request') else None
            if not user or user.is_anonymous:
                return None
            
            if not obj.exam:
                return None
            
            # exam-management과 동일한 로직 사용
            return obj.exam.get_accuracy_percentage_for_user(user)
        except Exception as e:
            print(f"❌ Error calculating accuracy percentage for task {obj.id}: {str(e)}")
            return None

    def get_correct_attempts(self, obj):
        """현재 사용자가 해당 태스크에서 맞춘 문제 수를 반환합니다."""
        user = self.context.get('request').user if self.context.get('request') else None
        if not user or user.is_anonymous:
            return 0
        
        if not obj.exam:
            return 0
            
        return obj.exam.get_total_correct_questions_for_user(user)

    def get_total_attempts(self, obj):
        """현재 사용자가 해당 태스크에서 시도한 문제 수를 반환합니다."""
        user = self.context.get('request').user if self.context.get('request') else None
        if not user or user.is_anonymous:
            return 0
        
        if not obj.exam:
            return 0
            
        return obj.exam.get_total_attempted_questions_for_user(user)


class StudyTaskUpdateSerializer(MultilingualSerializerMixin, serializers.ModelSerializer):
    """StudyTask 업데이트용 serializer - exam 필드를 writable하게 만듦"""
    
    # 다국어 필드들
    name_ko = serializers.CharField(required=False, allow_blank=True)
    name_en = serializers.CharField(required=False, allow_blank=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 다국어 필드 지정 (MultilingualSerializerMixin에서 사용)
        self.multilingual_fields = ['name']
    
    class Meta:
        model = StudyTask
        fields = ['id', 'study', 'name_ko', 'name_en', 'progress', 'exam', 'is_public', 'seq']
    
    def validate_study(self, value):
        """study 필드 검증"""
        if not value:
            raise serializers.ValidationError("study 필드가 필요합니다.")
        return value


class StudyTaskListSerializer(MultilingualSerializerMixin, serializers.ModelSerializer):
    """스터디 태스크 목록용 최적화된 시리얼라이저 - 불필요한 상세 정보 제외"""
    display_name = serializers.SerializerMethodField()
    exam_summary = serializers.SerializerMethodField()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 다국어 필드 지정 (MultilingualSerializerMixin에서 사용)
        self.multilingual_fields = ['name']
    
    class Meta:
        model = StudyTask
        fields = [
            'id', 'name_ko', 'name_en', 'display_name', 'progress', 'exam_summary',
            'is_public', 'seq', 'is_ko_complete', 'is_en_complete', 'created_language'
        ]
    
    def get_display_name(self, obj):
        """사용자 언어에 맞는 태스크 이름 반환"""
        request = self.context.get('request')
        if not request:
            return obj.name_ko or obj.name_en or (getattr(obj, 'name_es', None) or '') or (getattr(obj, 'name_zh', None) or '') or ''
        
        from quiz.utils.multilingual_utils import BASE_LANGUAGE
        user_language = BASE_LANGUAGE  # 기본값
        if hasattr(request, 'user') and request.user and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated:
            if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'language'):
                user_language = request.user.profile.language
        
        from quiz.utils.multilingual_utils import LANGUAGE_KO, LANGUAGE_EN, LANGUAGE_ES, LANGUAGE_ZH, LANGUAGE_JA
        if user_language == LANGUAGE_KO:
            return obj.name_ko or obj.name_en or (getattr(obj, 'name_es', None) or '') or (getattr(obj, 'name_zh', None) or '') or ''
        elif user_language == LANGUAGE_EN:
            return obj.name_en or obj.name_ko or (getattr(obj, 'name_es', None) or '') or (getattr(obj, 'name_zh', None) or '') or ''
        elif user_language == LANGUAGE_ES:
            return (getattr(obj, 'name_es', None) or '') or obj.name_en or obj.name_ko or (getattr(obj, 'name_zh', None) or '') or ''
        elif user_language == LANGUAGE_ZH:
            return (getattr(obj, 'name_zh', None) or '') or obj.name_en or obj.name_ko or (getattr(obj, 'name_es', None) or '') or (getattr(obj, 'name_ja', None) or '') or ''
        elif user_language == LANGUAGE_JA:
            return (getattr(obj, 'name_ja', None) or '') or obj.name_en or obj.name_ko or (getattr(obj, 'name_es', None) or '') or (getattr(obj, 'name_zh', None) or '') or ''
        else:
            return obj.name_en or obj.name_ko or (getattr(obj, 'name_es', None) or '') or (getattr(obj, 'name_zh', None) or '') or (getattr(obj, 'name_ja', None) or '') or ''
    
    def to_representation(self, instance):
        """기존 API 호환성을 위해 name 필드도 제공"""
        data = super().to_representation(instance)
        
        # name 필드를 display_name과 동일한 값으로 설정
        data['name'] = data['display_name']
        
        return data
    
    def get_exam_summary(self, obj):
        """시험 요약 정보만 반환 (상세 내용 제외) - 권한 확인 포함"""
        if not obj.exam:
            return None
        
        try:
            # 권한 확인
            request = self.context.get('request')
            user = request.user if request else None
            exam = obj.exam
            study = getattr(obj, 'study', None)
            
            # 관리자는 모든 시험 접근 가능
            if user and user.is_authenticated:
                if hasattr(user, 'profile') and hasattr(user.profile, 'role') and user.profile.role == 'admin_role':
                    # 관리자는 모든 시험 정보 반환
                    return {
                        'id': str(exam.id),
                        'title_ko': exam.title_ko,
                        'title_en': exam.title_en,
                        'is_public': exam.is_public,
                        'total_questions': exam.total_questions if hasattr(exam, 'total_questions') else (exam.questions.count() if hasattr(exam, 'questions') else 0)
                    }
            
            # 시험이 공개되어 있으면 정보 반환
            if exam.is_public:
                return {
                    'id': str(exam.id),
                    'title_ko': exam.title_ko,
                    'title_en': exam.title_en,
                    'is_public': exam.is_public,
                    'total_questions': exam.total_questions if hasattr(exam, 'total_questions') else (exam.questions.count() if hasattr(exam, 'questions') else 0)
                }
            
            # 비공개 시험인 경우 권한 확인
            if user and user.is_authenticated:
                # 사용자가 시험 생성자인지 확인
                is_creator = exam.created_by == user if exam.created_by else False
                
                # 사용자가 스터디 멤버인지 확인
                is_study_member = False
                if study:
                    try:
                        is_study_member = Member.objects.filter(
                            user=user,
                            study=study,
                            is_active=True
                        ).exists()
                    except Exception:
                        is_study_member = False
                
                # 사용자가 시험을 이미 풀어본 적이 있는지 확인
                has_taken_exam = False
                try:
                    has_taken_exam = ExamResult.objects.filter(
                        user=user,
                        exam=exam
                    ).exists()
                except Exception:
                    has_taken_exam = False
                
                # 권한이 있으면 정보 반환
                if is_creator or is_study_member or has_taken_exam:
                    return {
                        'id': str(exam.id),
                        'title_ko': exam.title_ko,
                        'title_en': exam.title_en,
                        'is_public': exam.is_public,
                        'total_questions': exam.total_questions if hasattr(exam, 'total_questions') else (exam.questions.count() if hasattr(exam, 'questions') else 0)
                    }
            
            # 권한이 없으면 None 반환 (비공개 시험 정보 숨김)
            return None
        except Exception as e:
            # 에러 발생 시 None 반환 (에러 로그는 남기지 않음 - 너무 많은 로그 방지)
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"get_exam_summary 에러: {e}")
            return None


class StudyListSerializer(serializers.ModelSerializer):
    """스터디 목록 조회용 최적화된 시리얼라이저 - 필요한 필드만 반환"""
    display_title = serializers.SerializerMethodField()
    display_goal = serializers.SerializerMethodField()
    total_tasks = serializers.SerializerMethodField()
    total_members = serializers.SerializerMethodField()
    overall_progress = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()
    tasks = serializers.SerializerMethodField()
    last_progress_recorded_at = serializers.SerializerMethodField()  # 사용자별 최근 진행률 기록 시간
    
    class Meta:
        model = Study
        fields = [
            'id', 'title_ko', 'title_en', 'title_es', 'title_zh',
            'goal_ko', 'goal_en', 'goal_es', 'goal_zh',
            'display_title', 'display_goal',
            'is_ko_complete', 'is_en_complete', 'is_es_complete', 'is_zh_complete', 'is_ja_complete',
            'created_language', 'start_date', 'end_date',
            'total_tasks', 'total_members', 'overall_progress', 'is_public', 'created_by', 'members', 'tasks',
            'created_at', 'updated_at', 'last_progress_recorded_at', 'tags'
        ]
    
    def get_display_title(self, obj):
        """사용자 언어에 맞는 제목 반환"""
        # 1. 컨텍스트에서 명시적으로 전달된 언어 정보 우선 사용
        context_language = self.context.get('user_language')
        if context_language:
            return get_localized_field(obj, 'title', context_language, '')
        
        # 2. fallback: request에서 사용자 언어 확인
        request = self.context.get('request')
        user_language = get_user_language(request)
        return get_localized_field(obj, 'title', user_language, '')
    
    def get_display_goal(self, obj):
        """사용자 언어에 맞는 목표 반환"""
        # 1. 컨텍스트에서 명시적으로 전달된 언어 정보 우선 사용
        context_language = self.context.get('user_language')
        if context_language:
            return get_localized_field(obj, 'goal', context_language, '')
        
        # 2. fallback: request에서 사용자 언어 확인
        request = self.context.get('request')
        user_language = get_user_language(request)
        return get_localized_field(obj, 'goal', user_language, '')
    
    def get_total_tasks(self, obj):
        """태스크 수 반환 (최적화: prefetch된 tasks 사용)"""
        # prefetch된 tasks를 사용하여 추가 쿼리 방지
        if hasattr(obj, '_prefetched_objects_cache') and 'tasks' in obj._prefetched_objects_cache:
            return len(obj._prefetched_objects_cache['tasks'])
        return obj.tasks.count()
    
    def get_total_members(self, obj):
        """활성 멤버 수 반환 (최적화: prefetch된 members 사용)"""
        # prefetch된 members를 사용하여 추가 쿼리 방지
        if hasattr(obj, '_prefetched_objects_cache') and 'members' in obj._prefetched_objects_cache:
            return len([m for m in obj._prefetched_objects_cache['members'] if m.is_active])
        return obj.members.filter(is_active=True).count()
    
    def get_overall_progress(self, obj):
        """전체 진행률 계산 (최적화: 컨텍스트에서 미리 계산된 데이터 사용)"""
        try:
            user = self.context.get('request').user if self.context.get('request') else None
            if not user or user.is_anonymous:
                return 0
            
            # 컨텍스트에서 미리 계산된 진행률 데이터 사용
            user_progress_dict = self.context.get('user_progress_dict', {})
            user_exam_result_dict = self.context.get('user_exam_result_dict', {})
            
            tasks = obj.tasks.all()
            if not tasks:
                return 0
            
            total_progress = 0
            task_count = 0
            
            # 미리 계산된 데이터 사용
            study_progresses = user_progress_dict.get(obj.id, [])
            study_exam_results = user_exam_result_dict.get(obj.id, {})
            
            for task in tasks:
                task_progress = 0
                
                # 미리 로드된 진행률 데이터에서 찾기
                progress_obj = None
                for progress in study_progresses:
                    if progress.study_task_id == task.id:
                        progress_obj = progress
                        break
                
                if progress_obj:
                    task_progress = progress_obj.progress
                else:
                    # 시험 결과 기반으로 계산 (미리 로드된 데이터 사용)
                    if task.exam_id:
                        result = study_exam_results.get(task.exam_id)
                        if result and hasattr(result, 'total_score') and result.total_score:
                            task_progress = (result.score / result.total_score) * 100
                        else:
                            task_progress = 0
                    else:
                        task_progress = 0
                
                total_progress += task_progress
                task_count += 1
            
            return round(total_progress / task_count, 1) if task_count > 0 else 0
            
        except Exception as e:
            print(f"진행률 계산 오류: {e}")
            return 0
    
    def get_created_by(self, obj):
        """스터디 생성자 정보 반환"""
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'username': obj.created_by.username,
                'email': obj.created_by.email
            }
        return None

    def get_members(self, obj):
        """스터디 멤버 목록 반환 (최적화된 버전)"""
        members = obj.members.filter(is_active=True)
        return [
            {
                'id': member.id,
                'user': member.user.id if member.user else None,
                'name': member.name,
                'email': member.email,
                'role': member.role,
                'is_active': member.is_active
            }
            for member in members
        ]

    def get_tasks(self, obj):
        """스터디 태스크 목록 반환 (최적화된 버전)"""
        tasks = obj.tasks.all()
        return StudyTaskListSerializer(tasks, many=True, context=self.context).data
    
    def get_last_progress_recorded_at(self, obj):
        """사용자별 최근 진행률 기록 시간 반환 (최적화: 컨텍스트에서 미리 계산된 데이터 사용)"""
        try:
            user = self.context.get('request').user if self.context.get('request') else None
            
            if not user or user.is_anonymous:
                return None
            
            # 컨텍스트에서 미리 계산된 최근 진행률 기록 사용
            user_last_progress_dict = self.context.get('user_last_progress_dict', {})
            result = user_last_progress_dict.get(obj.id)
            
            return result
            
        except Exception as e:
            print(f"❌ 최근 진행률 기록 시간 조회 오류: {e}")
            return None


class StudySerializer(MultilingualSerializerMixin, serializers.ModelSerializer):
    tasks = StudyTaskSerializer(many=True, read_only=True)
    members = serializers.SerializerMethodField()
    overall_progress = serializers.SerializerMethodField()
    correct_progress = serializers.SerializerMethodField()
    attempted_progress = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    
    # 사용자별 합격률 필드 추가 (exam-management과 동일한 로직)
    accuracy_percentage = serializers.SerializerMethodField()
    
    # 사용자별 최근 진행률 기록 시간
    last_progress_recorded_at = serializers.SerializerMethodField()
    
    # 태그 정보를 전체 객체로 반환
    tags = TagSerializer(many=True, read_only=True)
    
    # 다국어 필드들
    title_ko = serializers.CharField(required=False, allow_blank=True)
    title_en = serializers.CharField(required=False, allow_blank=True)
    title_zh = serializers.CharField(required=False, allow_blank=True)
    title_es = serializers.CharField(required=False, allow_blank=True)
    goal_ko = serializers.CharField(required=False, allow_blank=True)
    goal_en = serializers.CharField(required=False, allow_blank=True)
    goal_zh = serializers.CharField(required=False, allow_blank=True)
    goal_es = serializers.CharField(required=False, allow_blank=True)
    
    # 언어별 완성도 (모든 언어 자동 포함)
    created_language = serializers.CharField(read_only=True)
    
    class Meta:
        model = Study
        fields = [
            'id', 'title_ko', 'title_en', 'title_zh', 'title_es',
            'goal_ko', 'goal_en', 'goal_zh', 'goal_es',
            'created_language'
        ] + get_completion_fields() + [
            'start_date', 'end_date', 'tasks', 'members', 
            'overall_progress', 'correct_progress', 'attempted_progress', 
            'accuracy_percentage', 'is_public', 'created_by', 'last_progress_recorded_at', 'tags',
            'supported_languages'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 다국어 필드 지정 (공통 모듈에서 사용)
        self.multilingual_fields = ['title', 'goal']
    
    def get_created_by(self, obj):
        """스터디 생성자 정보 반환"""
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'username': obj.created_by.username,
                'email': obj.created_by.email
            }
        return None

    def get_members(self, obj):
        """스터디 멤버 목록 반환"""
        members = obj.members.all()
        return MemberSerializer(members, many=True, context=self.context).data

    def get_overall_progress(self, obj):
        """
        스터디의 전체 진행률을 계산합니다.
        
        주의사항:
        - 2025-08-13 23:16:50에 clear_all_statistics.py로 모든 통계 데이터 삭제 완료
        - 이제 모든 진행률이 0%에서 시작됨
        - 새로운 시험 결과가 쌓이면 진행률이 업데이트됨
        
        계산 로직:
        1. context의 study_progress_dict에서 미리 계산된 값 사용 (우선순위, N+1 쿼리 방지)
        2. context에 없으면 시험 결과 기반으로 실제 진행률 계산
        3. StudyTaskProgress에서 사용자별 진행률 확인 (fallback)
        4. 모든 태스크의 평균 진행률 반환
        """
        # context에 미리 계산된 진행률이 있으면 사용 (N+1 쿼리 방지)
        study_progress_dict = self.context.get('study_progress_dict', {})
        if obj.id in study_progress_dict:
            return study_progress_dict[obj.id]
        
        # 폴백: context에 없으면 기존 로직 사용
        try:
            
            # 현재 로그인한 사용자 가져오기
            user = self.context.get('request').user if self.context.get('request') else None
            print(f"🔍 context 확인: {self.context}")
            print(f"🔍 user 정보: {user}")
            
            if not user or user.is_anonymous:
                print(f"�� 사용자 정보 없음 또는 익명 사용자")
                return 0
            
            tasks = obj.tasks.all()
            print(f"🔍 tasks 개수: {tasks.count()}")
            
            if not tasks:
                print(f"🔍 태스크가 없음")
                return 0
            
            # 사용자별 개별 진행률 계산
            total_progress = 0
            task_count = 0
            
            for task in tasks:
                task_progress = 0
                
                if task.exam:
                    attempted_count = task.exam.get_total_attempted_questions_for_user(user)
                    total_questions = task.exam.questions.count()
                    
                    if total_questions > 0:
                        task_progress = (attempted_count / total_questions) * 100
                
                if task_progress == 0:
                    from .models import StudyTaskProgress
                    progress_obj = StudyTaskProgress.objects.filter(user=user, study_task=task).first()
                    if progress_obj and progress_obj.progress > 0:
                        task_progress = progress_obj.progress
                
                total_progress += task_progress
                task_count += 1
            
            if task_count == 0:
                return 0
            
            return total_progress / task_count
        except Exception as e:
            return 0

    def get_correct_progress(self, obj):
        """
        스터디의 맞춘 문제 기반 진행률을 계산합니다.
        context의 study_correct_progress_dict에서 미리 계산된 값을 사용하여 N+1 쿼리 방지
        """
        # context에 미리 계산된 진행률이 있으면 사용
        study_correct_progress_dict = self.context.get('study_correct_progress_dict', {})
        if obj.id in study_correct_progress_dict:
            return study_correct_progress_dict[obj.id]
        
        # 폴백: context에 없으면 기존 로직 사용
        try:
            user = self.context.get('request').user if self.context.get('request') else None
            if not user or user.is_anonymous:
                return 0
            
            tasks = obj.tasks.all()
            if not tasks:
                return 0
            
            total_correct = 0
            total_questions = 0
            
            for task in tasks:
                if task.exam:
                    correct_count = task.exam.get_total_correct_questions_for_user(user)
                    question_count = task.exam.questions.count()
                    total_correct += correct_count
                    total_questions += question_count
            
            if total_questions == 0:
                return 0
            
            return (total_correct / total_questions) * 100
        except Exception as e:
            return 0

    def get_attempted_progress(self, obj):
        """
        스터디의 시도한 문제 기반 진행률을 계산합니다.
        context의 study_attempted_progress_dict에서 미리 계산된 값을 사용하여 N+1 쿼리 방지
        """
        # context에 미리 계산된 진행률이 있으면 사용
        study_attempted_progress_dict = self.context.get('study_attempted_progress_dict', {})
        if obj.id in study_attempted_progress_dict:
            return study_attempted_progress_dict[obj.id]
        
        # 폴백: context에 없으면 기존 로직 사용
        try:
            user = self.context.get('request').user if self.context.get('request') else None
            if not user or user.is_anonymous:
                return 0
            
            tasks = obj.tasks.all()
            if not tasks:
                return 0
            
            total_attempted = 0
            total_questions = 0
            
            for task in tasks:
                if task.exam:
                    attempted_count = task.exam.get_total_attempted_questions_for_user(user)
                    question_count = task.exam.questions.count()
                    total_attempted += attempted_count
                    total_questions += question_count
            
            if total_questions == 0:
                return 0
            
            return (total_attempted / total_questions) * 100
        except Exception as e:
            return 0

    def get_accuracy_percentage(self, obj):
        """
        현재 사용자의 합격률 계산 (exam-management과 동일한 로직)
        context의 study_accuracy_dict에서 미리 계산된 값을 사용하여 N+1 쿼리 방지
        """
        # context에 미리 계산된 합격률이 있으면 사용
        study_accuracy_dict = self.context.get('study_accuracy_dict', {})
        if obj.id in study_accuracy_dict:
            return study_accuracy_dict[obj.id]
        
        # 폴백: context에 없으면 기존 로직 사용
        try:
            user = self.context.get('request').user if self.context.get('request') else None
            if not user or user.is_anonymous:
                return None
            
            tasks = obj.tasks.all()
            if not tasks:
                return None
            
            total_accuracy = 0
            task_count = 0
            
            for task in tasks:
                if task.exam:
                    accuracy = task.exam.get_accuracy_percentage_for_user(user)
                    if accuracy is not None:
                        total_accuracy += accuracy
                        task_count += 1
            
            if task_count == 0:
                return None
            
            return total_accuracy / task_count
        except Exception as e:
            return None

    def get_last_progress_recorded_at(self, obj):
        """사용자별 최근 진행률 기록 시간 반환"""
        try:
            user = self.context.get('request').user if self.context.get('request') else None
            print(f"🔍 StudySerializer get_last_progress_recorded_at 호출됨 - 스터디: {obj.title_ko or obj.title_en}, 사용자: {user.username if user else 'None'}")
            
            if not user or user.is_anonymous:
                print(f"❌ 사용자가 없거나 익명 사용자: {user}")
                return None
            
            from .models import StudyProgressRecord
            last_record = StudyProgressRecord.objects.filter(
                user=user,
                study=obj
            ).order_by('-recorded_at').first()
            
            result = last_record.recorded_at if last_record else None
            print(f"✅ StudySerializer 결과: {result}")
            return result
            
        except Exception as e:
            print(f"❌ StudySerializer 최근 진행률 기록 시간 조회 오류: {e}")
            import traceback
            traceback.print_exc()
            return None


class MemberSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Member
        fields = ['id', 'study', 'user', 'user_username', 'user_email', 'name', 'email', 'member_id', 'affiliation', 'location', 'role', 'is_active', 'created_at', 'updated_at']
    
    def to_internal_value(self, data):
        """입력 데이터 처리 시에만 user 필드를 제외하고 처리"""
        if 'user' not in data:
            data = data.copy()
            data['user'] = None
        return super().to_internal_value(data)
    
    def to_representation(self, instance):
        """출력 시 user 필드가 제대로 포함되도록 보장"""
        data = super().to_representation(instance)
        if instance.user:
            data['user'] = instance.user.id
        return data
    
    def create(self, validated_data):
        """user 필드가 None이면 제거"""
        if validated_data.get('user') is None:
            validated_data.pop('user', None)
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """user 필드가 None이면 제거"""
        if validated_data.get('user') is None:
            validated_data.pop('user', None)
        return super().update(instance, validated_data)


class QuestionMemberMappingSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)
    member = MemberSerializer(read_only=True)
    exam = ExamSerializer(read_only=True)
    
    class Meta:
        model = QuestionMemberMapping
        fields = ['id', 'question', 'member', 'exam', 'created_at', 'updated_at']


class StudyJoinRequestSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    study_title = serializers.SerializerMethodField()
    responded_by_username = serializers.CharField(source='responded_by.username', read_only=True)
    
    class Meta:
        model = StudyJoinRequest
        fields = [
            'id', 'study', 'study_title', 'user', 'user_username', 'user_email', 
            'message', 'status', 'requested_at', 'responded_at', 'responded_by', 
            'responded_by_username'
        ]
        read_only_fields = ['user', 'requested_at', 'responded_at', 'responded_by']
    
    def get_study_title(self, obj):
        """스터디 제목을 현재 사용자 언어에 맞게 반환"""
        if not obj.study:
            return ''
        
        # 현재 사용자 언어 확인
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user and hasattr(request.user, 'is_anonymous') and not request.user.is_anonymous:
            try:
                user_profile = request.user.profile
                user_language = user_profile.language
            except:
                from quiz.utils.multilingual_utils import BASE_LANGUAGE
                user_language = BASE_LANGUAGE  # 기본값
        else:
            from quiz.utils.multilingual_utils import BASE_LANGUAGE
            user_language = BASE_LANGUAGE  # 기본값
        
        # 언어에 맞는 제목 반환
        from quiz.utils.multilingual_utils import LANGUAGE_KO, LANGUAGE_EN, LANGUAGE_ES, LANGUAGE_ZH, LANGUAGE_JA
        if user_language == LANGUAGE_KO:
            return obj.study.title_ko or obj.study.title_en or (getattr(obj.study, 'title_es', None) or '') or (getattr(obj.study, 'title_zh', None) or '') or ''
        elif user_language == LANGUAGE_EN:
            return obj.study.title_en or obj.study.title_ko or (getattr(obj.study, 'title_es', None) or '') or (getattr(obj.study, 'title_zh', None) or '') or ''
        elif user_language == LANGUAGE_ES:
            return (getattr(obj.study, 'title_es', None) or '') or obj.study.title_en or obj.study.title_ko or (getattr(obj.study, 'title_zh', None) or '') or ''
        elif user_language == LANGUAGE_ZH:
            return (getattr(obj.study, 'title_zh', None) or '') or obj.study.title_en or obj.study.title_ko or (getattr(obj.study, 'title_es', None) or '') or ''
        else:
            return obj.study.title_en or obj.study.title_ko or (getattr(obj.study, 'title_es', None) or '') or (getattr(obj.study, 'title_zh', None) or '') or ''


class CreateStudyJoinRequestSerializer(serializers.Serializer):
    study_id = serializers.IntegerField()
    message = serializers.CharField(required=False, allow_blank=True)


class UpdateStudyJoinRequestSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['approved', 'rejected'])
    message = serializers.CharField(required=False, allow_blank=True)


class CreateQuestionMemberMappingSerializer(serializers.Serializer):
    exam_id = serializers.UUIDField()
    study_id = serializers.IntegerField() 