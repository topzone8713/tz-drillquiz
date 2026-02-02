from django.contrib import admin
from django.utils import translation
from .models import Question, Exam, ExamResult, ExamResultDetail, QuestionMemberMapping, Tag, Study, StudyTask
from quiz.utils.multilingual_utils import (
    get_user_language, 
    get_localized_field, 
    get_localized_admin_label,
    get_localized_fieldset_title,
    get_completion_fields,
    get_multilingual_search_fields,
    get_multilingual_fields
)


class MultilingualAdminMixin:
    """다국어 지원을 위한 Admin Mixin"""
    
    # short_description 매핑 (메서드명 -> 필드명)
    _admin_label_mapping = {
        'get_title': 'title',
        'get_name': 'name',
        'get_content': 'content',
        'get_description': 'description'
    }
    
    def changelist_view(self, request, extra_context=None):
        """request를 저장하고 short_description과 필드 레이블을 동적으로 설정"""
        self.request = request
        user_language = self._get_user_language()
        
        # 모든 list_display 메서드의 short_description을 동적으로 설정
        for method_name, field_name in self._admin_label_mapping.items():
            if hasattr(self, method_name):
                method = getattr(self, method_name)
                method.short_description = get_localized_admin_label(field_name, user_language)
        
        # list_display에 직접 포함된 완성도 필드의 verbose_name 동적 설정
        if hasattr(self, 'list_display') and hasattr(self, 'model'):
            completion_fields = get_completion_fields(model=self.model)
            for field_name in completion_fields:
                if field_name in self.list_display:
                    try:
                        field = self.model._meta.get_field(field_name)
                        # 원본 verbose_name을 백업하고 동적으로 설정
                        if not hasattr(field, '_original_verbose_name'):
                            field._original_verbose_name = field.verbose_name
                        field.verbose_name = get_localized_admin_label(field_name, user_language)
                    except:
                        pass
        
        return super().changelist_view(request, extra_context)
    
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """request를 저장하여 form에서 사용할 수 있도록 함"""
        self.request = request
        return super().changeform_view(request, object_id, form_url, extra_context)
    
    def get_fieldsets(self, request, obj=None):
        """fieldsets의 제목을 동적으로 다국어 처리"""
        # request를 저장하여 _get_user_language에서 사용할 수 있도록 함
        self.request = request
        user_language = get_user_language(request) if request else self._get_user_language()
        fieldsets = super().get_fieldsets(request, obj)
        
        # fieldsets의 제목을 다국어로 변환
        localized_fieldsets = []
        for title, options in fieldsets:
            # 한글 제목을 키로 변환
            title_key = None
            if title == '기본 정보':
                title_key = 'basic_info'
            elif title == '설정':
                title_key = 'settings'
            elif title == '태그':
                title_key = 'tags'
            elif title == '태그 정보':
                title_key = 'tag_info'
            elif title == '일정':
                title_key = 'schedule'
            elif title == '완성도':
                title_key = 'completion'
            elif title == '메타 정보':
                title_key = 'meta_info'
            elif title == '연결':
                title_key = 'connection'
            elif title == '진행률':
                title_key = 'progress'
            
            if title_key:
                localized_title = get_localized_fieldset_title(title_key, user_language)
            else:
                localized_title = title  # 매핑되지 않은 제목은 그대로 유지
            
            localized_fieldsets.append((localized_title, options))
        
        return localized_fieldsets
    
    def get_form(self, request, obj=None, **kwargs):
        """필드 레이블을 동적으로 설정"""
        form = super().get_form(request, obj, **kwargs)
        user_language = self._get_user_language()
        
        # 완성도 필드의 레이블 동적 설정
        completion_fields = get_completion_fields()
        for field_name in completion_fields:
            if field_name in form.base_fields:
                form.base_fields[field_name].label = get_localized_admin_label(field_name, user_language)
        
        return form
    
    def _get_user_language(self):
        """현재 사용자 언어 가져오기"""
        try:
            if hasattr(self, 'request') and self.request:
                return get_user_language(self.request)
            # Django의 translation.get_language() 사용 (미들웨어에서 설정됨)
            lang = translation.get_language()
            if lang:
                # Django 언어 코드를 프로젝트 언어 코드로 변환 (예: 'en-us' -> 'en')
                return lang.split('-')[0] if '-' in lang else lang
        except:
            pass
        return 'en'  # 기본값


@admin.register(Question)
class QuestionAdmin(MultilingualAdminMixin, admin.ModelAdmin):
    list_display = ['get_title', 'created_at', 'updated_at']
    search_fields = get_multilingual_search_fields(['title', 'content'])
    list_filter = ['created_at']
    
    def get_title(self, obj):
        """사용자 언어에 맞는 제목 반환"""
        user_language = self._get_user_language()
        return get_localized_field(obj, 'title', user_language)


@admin.register(Exam)
class ExamAdmin(MultilingualAdminMixin, admin.ModelAdmin):
    list_display = ['get_title', 'total_questions', 'voice_mode_enabled', 'created_at']
    search_fields = get_multilingual_search_fields(['title'])
    list_filter = ['voice_mode_enabled', 'created_at', 'is_public']
    filter_horizontal = ['tags']  # 태그 선택을 위한 위젯
    fieldsets = [
        ('기본 정보', {
            'fields': get_multilingual_fields(['title', 'description'], ['total_questions'])
        }),
        ('설정', {
            'fields': ('is_public', 'force_answer', 'voice_mode_enabled', 'ai_mock_interview', 'created_by')
        }),
        ('태그', {
            'fields': ('tags',)
        }),
    ]
    
    def get_title(self, obj):
        """사용자 언어에 맞는 제목 반환"""
        user_language = self._get_user_language()
        return get_localized_field(obj, 'title', user_language)


@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ['exam', 'score', 'total_score', 'correct_count', 'wrong_count', 'completed_at']
    list_filter = ['completed_at']
    search_fields = ['exam__' + field for field in get_multilingual_search_fields(['title'])]


@admin.register(ExamResultDetail)
class ExamResultDetailAdmin(admin.ModelAdmin):
    list_display = ['result', 'question', 'user_answer', 'is_correct']
    list_filter = ['is_correct']
    search_fields = ['question__' + field for field in get_multilingual_search_fields(['title'])] + ['user_answer']


@admin.register(QuestionMemberMapping)
class QuestionMemberMappingAdmin(admin.ModelAdmin):
    list_display = ['member', 'question', 'exam', 'created_at']
    list_filter = ['created_at', 'exam']
    search_fields = (
        ['member__name'] +
        ['question__' + field for field in get_multilingual_search_fields(['title'])] +
        ['exam__' + field for field in get_multilingual_search_fields(['title'])]
    )


@admin.register(Tag)
class TagAdmin(MultilingualAdminMixin, admin.ModelAdmin):
    list_display = ['get_name', 'created_language'] + get_completion_fields() + ['created_at']
    search_fields = get_multilingual_search_fields(['name'])
    list_filter = ['created_language'] + get_completion_fields() + ['created_at']
    fieldsets = [
        ('태그 정보', {
            'fields': get_multilingual_fields(['name'], ['created_language'])
        }),
        ('완성도', {
            'fields': tuple(get_completion_fields())
        }),
        ('메타 정보', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    def get_name(self, obj):
        """사용자 언어에 맞는 태그명 반환"""
        user_language = self._get_user_language()
        return get_localized_field(obj, 'name', user_language)


@admin.register(Study)
class StudyAdmin(MultilingualAdminMixin, admin.ModelAdmin):
    list_display = ['get_title', 'is_public', 'created_by', 'created_at']
    search_fields = get_multilingual_search_fields(['title', 'goal'])
    list_filter = ['is_public', 'created_language'] + get_completion_fields() + ['created_at']
    filter_horizontal = ['tags']  # 태그 선택을 위한 위젯
    fieldsets = [
        ('기본 정보', {
            'fields': get_multilingual_fields(['title', 'goal'], ['created_language'])
        }),
        ('일정', {
            'fields': ('start_date', 'end_date')
        }),
        ('설정', {
            'fields': ('is_public', 'created_by')
        }),
        ('태그', {
            'fields': ('tags',)
        }),
        ('완성도', {
            'fields': tuple(get_completion_fields()),
            'classes': ('collapse',)
        }),
    ]
    
    def get_title(self, obj):
        """사용자 언어에 맞는 제목 반환"""
        user_language = self._get_user_language()
        return get_localized_field(obj, 'title', user_language)


@admin.register(StudyTask)
class StudyTaskAdmin(MultilingualAdminMixin, admin.ModelAdmin):
    list_display = ['get_name', 'study', 'exam', 'progress', 'seq', 'is_public']
    search_fields = (
        get_multilingual_search_fields(['name']) +
        ['study__' + field for field in get_multilingual_search_fields(['title'])]
    )
    list_filter = ['is_public', 'created_language'] + get_completion_fields() + ['study']
    fieldsets = [
        ('기본 정보', {
            'fields': get_multilingual_fields(['name'], ['study', 'created_language'])
        }),
        ('연결', {
            'fields': ('exam',)
        }),
        ('진행률', {
            'fields': ('progress', 'seq')
        }),
        ('설정', {
            'fields': ('is_public',)
        }),
        ('완성도', {
            'fields': tuple(get_completion_fields()),
            'classes': ('collapse',)
        }),
    ]
    
    def get_name(self, obj):
        """사용자 언어에 맞는 태스크명 반환"""
        user_language = self._get_user_language()
        return get_localized_field(obj, 'name', user_language) 