from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.conf import settings

# 다국어 지원 언어 상수
from quiz.utils.multilingual_utils import (
    SUPPORTED_LANGUAGES, LANGUAGE_KO, LANGUAGE_EN, LANGUAGE_ES, LANGUAGE_ZH, LANGUAGE_JA, BASE_LANGUAGE,
    get_localized_field
)

# Django choices를 위한 언어 튜플 리스트
LANGUAGE_CHOICES = [
    (LANGUAGE_KO, '한국어'),
    (LANGUAGE_EN, 'English'),
    (LANGUAGE_ES, 'Español'),
    (LANGUAGE_ZH, '中文'),
    (LANGUAGE_JA, '日本語'),
]


class Question(models.Model):
    """문제 모델 - 다국어 지원"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    csv_id = models.CharField(max_length=50, verbose_name="CSV 문제 ID", blank=True, null=True)
    source_id = models.CharField(max_length=200, verbose_name="출처 파일명", blank=True, null=True, help_text="엑셀 파일명 또는 문제 출처를 나타내는 식별자")
    
    # 다국어 제목
    title_ko = models.CharField(max_length=200, verbose_name="한국어 제목", blank=True)
    title_en = models.CharField(max_length=200, verbose_name="영어 제목", blank=True)
    title_es = models.CharField(max_length=200, verbose_name="스페인어 제목", blank=True)
    title_zh = models.CharField(max_length=200, verbose_name="중국어 제목", blank=True)
    title_ja = models.CharField(max_length=200, verbose_name="일본어 제목", blank=True)
    
    # 다국어 문제 내용
    content_ko = models.TextField(verbose_name="한국어 문제 내용", blank=True)
    content_en = models.TextField(verbose_name="영어 문제 내용", blank=True)
    content_es = models.TextField(verbose_name="스페인어 문제 내용", blank=True)
    content_zh = models.TextField(verbose_name="중국어 문제 내용", blank=True)
    content_ja = models.TextField(verbose_name="일본어 문제 내용", blank=True)
    
    # 다국어 정답
    answer_ko = models.TextField(verbose_name="한국어 정답", blank=True)
    answer_en = models.TextField(verbose_name="영어 정답", blank=True)
    answer_es = models.TextField(verbose_name="스페인어 정답", blank=True)
    answer_zh = models.TextField(verbose_name="중국어 정답", blank=True)
    answer_ja = models.TextField(verbose_name="일본어 정답", blank=True)
    
    # 다국어 설명
    explanation_ko = models.TextField(verbose_name="한국어 설명", blank=True, null=True)
    explanation_en = models.TextField(verbose_name="영어 설명", blank=True, null=True)
    explanation_es = models.TextField(verbose_name="스페인어 설명", blank=True, null=True)
    explanation_zh = models.TextField(verbose_name="중국어 설명", blank=True, null=True)
    explanation_ja = models.TextField(verbose_name="일본어 설명", blank=True, null=True)
    
    difficulty = models.CharField(max_length=20, verbose_name="난이도", blank=True, null=True)
    url = models.URLField(verbose_name="문제 URL", blank=True, null=True)
    group_id = models.CharField(max_length=50, verbose_name="그룹 ID", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")
    
    # 생성 시 사용자의 프로필 언어 (자동 설정)
    created_language = models.CharField(
        max_length=2, 
        choices=LANGUAGE_CHOICES,
        verbose_name='생성 언어',
        default=BASE_LANGUAGE
    )
    
    # 언어별 완성도 추적
    is_ko_complete = models.BooleanField(default=False, verbose_name='한국어 완성')
    is_en_complete = models.BooleanField(default=False, verbose_name='영어 완성')
    is_es_complete = models.BooleanField(default=False, verbose_name='스페인어 완성')
    is_zh_complete = models.BooleanField(default=False, verbose_name='중국어 완성')
    is_ja_complete = models.BooleanField(default=False, verbose_name='일본어 완성')
    
    # 문제 생성자 (권한 확인용)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="생성자")

    class Meta:
        verbose_name = "문제"
        verbose_name_plural = "문제들"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title_ko']),
            models.Index(fields=['title_en']),
            models.Index(fields=['title_ja']),
            models.Index(fields=['content_ko']),
            models.Index(fields=['content_en']),
            models.Index(fields=['content_ja']),
            models.Index(fields=['created_language']),
            models.Index(fields=['is_ko_complete']),
            models.Index(fields=['is_en_complete']),
            models.Index(fields=['is_ja_complete']),
            # 성능 개선을 위한 추가 인덱스
            models.Index(fields=['difficulty']),  # 난이도별 필터링
            models.Index(fields=['group_id']),    # 그룹별 필터링
            models.Index(fields=['csv_id']),      # CSV ID 검색
            models.Index(fields=['source_id']),   # 출처 파일명 검색 (중복 방지용)
            models.Index(fields=['created_at']),  # 생성일 정렬
            models.Index(fields=['updated_at']),  # 수정일 정렬
            # 복합 인덱스 (자주 함께 사용되는 필드들)
            models.Index(fields=['created_language', 'is_ko_complete']),
            models.Index(fields=['created_language', 'is_en_complete']),
            models.Index(fields=['created_language', 'is_ja_complete']),
            models.Index(fields=['difficulty', 'created_language']),
            models.Index(fields=['group_id', 'created_language']),
            # 중복 방지를 위한 복합 인덱스
            models.Index(fields=['source_id', 'title_ko']),  # 출처 + 한국어 제목
            models.Index(fields=['source_id', 'title_en']),  # 출처 + 영어 제목
            models.Index(fields=['source_id', 'title_ja']),  # 출처 + 일본어 제목
        ]

    def __str__(self):
        """생성 언어 기준으로 제목 반환"""
        language = self.created_language if hasattr(self, 'created_language') else BASE_LANGUAGE
        return get_localized_field(self, 'title', language)
    
    def save(self, *args, **kwargs):
        """
        저장 시 언어별 완성도 자동 업데이트 및 생성 언어 설정
        
        다국어 처리 방식 (Exam과 동일):
        1. 사용자가 title, content, answer, explanation 필드에 입력한 내용을
           현재 사용자 언어에 맞는 필드에 자동 저장
        2. MultilingualContentManager가 자동으로 번역 수행 (뷰에서 처리)
        3. 언어별 완성도 상태 자동 업데이트
        """
        # 생성 시에만 언어 자동 설정
        if not self.pk and not self.created_language:
            # 현재 사용자 언어 설정 (뷰에서 처리)
            from quiz.utils.multilingual_utils import LANGUAGE_KO
            self.created_language = BASE_LANGUAGE  # 기본값
        
        # 언어별 완성도 자동 업데이트
        self.is_ko_complete = bool(self.title_ko and self.content_ko and self.answer_ko)
        self.is_en_complete = bool(self.title_en and self.content_en and self.answer_en)
        self.is_es_complete = bool(self.title_es and self.content_es and self.answer_es)
        self.is_zh_complete = bool(self.title_zh and self.content_zh and self.answer_zh)
        self.is_ja_complete = bool(self.title_ja and self.content_ja and self.answer_ja)
        
        super().save(*args, **kwargs)


class TagCategory(models.Model):
    """
    태그 카테고리 모델 - 계층 구조 지원 (최대 3단계)
    
    태그를 카테고리별로 분류하여 관리할 수 있습니다.
    계층 구조를 통해 대분류 > 중분류 > 소분류 형태로 구성됩니다.
    """
    # 계층 구조를 위한 self-referential ForeignKey
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='상위 카테고리',
        db_index=True
    )
    
    # 다국어 카테고리 이름
    name_ko = models.CharField(max_length=100, verbose_name='한국어 카테고리명')
    name_en = models.CharField(max_length=100, verbose_name='영어 카테고리명', blank=True)
    name_es = models.CharField(max_length=100, verbose_name='스페인어 카테고리명', blank=True)
    name_zh = models.CharField(max_length=100, verbose_name='중국어 카테고리명', blank=True)
    name_ja = models.CharField(max_length=100, verbose_name='일본어 카테고리명', blank=True)
    
    # 계층 깊이 (1, 2, 3)
    level = models.IntegerField(
        verbose_name='레벨',
        choices=[(1, '1단계'), (2, '2단계'), (3, '3단계')],
        default=1,
        db_index=True
    )
    
    # 같은 레벨 내 정렬 순서
    order = models.IntegerField(default=0, verbose_name='정렬 순서', db_index=True)
    
    # UI에서 사용할 색상 코드 (선택)
    color = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='색상 코드',
        help_text='UI에서 사용할 색상 코드 (예: 🟩, 🟦, 🟨)'
    )
    
    # 언어별 완성도 추적
    is_ko_complete = models.BooleanField(default=False, verbose_name='한국어 완성')
    is_en_complete = models.BooleanField(default=False, verbose_name='영어 완성')
    is_es_complete = models.BooleanField(default=False, verbose_name='스페인어 완성')
    is_zh_complete = models.BooleanField(default=False, verbose_name='중국어 완성')
    is_ja_complete = models.BooleanField(default=False, verbose_name='일본어 완성')
    
    # 활성화/비활성화
    is_active = models.BooleanField(
        default=True,
        verbose_name='활성화',
        help_text='비활성화된 카테고리는 UI에서 숨겨집니다.',
        db_index=True
    )
    
    # 생성 시 사용자의 프로필 언어 (자동 설정)
    created_language = models.CharField(
        max_length=2,
        choices=LANGUAGE_CHOICES,
        verbose_name='생성 언어',
        default=BASE_LANGUAGE
    )
    
    # 메타 정보
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="생성자",
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")
    
    class Meta:
        verbose_name = "태그 카테고리"
        verbose_name_plural = "태그 카테고리들"
        ordering = ['level', 'order', 'name_ko']
        indexes = [
            models.Index(fields=['parent', 'level']),
            models.Index(fields=['level', 'order']),
            models.Index(fields=['name_ko']),
            models.Index(fields=['name_en']),
            models.Index(fields=['name_es']),
            models.Index(fields=['name_zh']),
            models.Index(fields=['name_ja']),
        ]
    
    def __str__(self):
        """생성 언어 기준으로 이름 반환"""
        language = self.created_language if hasattr(self, 'created_language') else BASE_LANGUAGE
        return get_localized_field(self, 'name', language)
    
    def get_full_path(self, language=None):
        """
        전체 카테고리 경로 반환 (예: "1. 취미 · 라이프스타일 > 1.1 요리 · 베이킹")
        
        Args:
            language (str): 언어 코드. None이면 created_language 사용
        
        Returns:
            str: 전체 경로 문자열
        """
        if language is None:
            language = self.created_language
        
        path_parts = []
        current = self
        
        # 루트까지 올라가면서 경로 구성
        while current:
            name = get_localized_field(current, 'name', language)
            path_parts.insert(0, name)
            current = current.parent
        
        return ' > '.join(path_parts)
    
    def get_localized_name(self, language=None):
        """지정된 언어에 맞는 카테고리명 반환"""
        if language is None:
            language = self.created_language if hasattr(self, 'created_language') else BASE_LANGUAGE
        return get_localized_field(self, 'name', language)
    
    def save(self, *args, **kwargs):
        """저장 시 level 자동 계산 및 검증"""
        # parent가 있으면 level 계산
        if self.parent:
            parent_level = self.parent.level
            if parent_level >= 3:
                raise ValueError("카테고리 깊이는 최대 3단계까지 가능합니다.")
            self.level = parent_level + 1
        else:
            self.level = 1
        
        # 언어별 완성도 자동 업데이트
        self.is_ko_complete = bool(self.name_ko)
        self.is_en_complete = bool(self.name_en)
        self.is_es_complete = bool(self.name_es)
        self.is_zh_complete = bool(self.name_zh)
        self.is_ja_complete = bool(self.name_ja)
        
        super().save(*args, **kwargs)


class Tag(models.Model):
    """
    태그 모델 - 다국어 지원
    
    스터디와 시험에 복수 태그를 할당할 수 있으며,
    알파벳 순서로 자동 정렬됩니다.
    """
    # 다국어 태그 이름
    name_ko = models.CharField(max_length=50, verbose_name='한국어 태그명', unique=True)
    name_en = models.CharField(max_length=50, verbose_name='영어 태그명', unique=True)
    name_es = models.CharField(max_length=50, verbose_name='스페인어 태그명', blank=True, null=True)
    name_zh = models.CharField(max_length=50, verbose_name='중국어 태그명', blank=True, null=True)
    name_ja = models.CharField(max_length=50, verbose_name='일본어 태그명', blank=True, null=True)
    
    # 언어별 완성도 추적
    is_ko_complete = models.BooleanField(default=False, verbose_name='한국어 완성')
    is_en_complete = models.BooleanField(default=False, verbose_name='영어 완성')
    is_es_complete = models.BooleanField(default=False, verbose_name='스페인어 완성')
    is_zh_complete = models.BooleanField(default=False, verbose_name='중국어 완성')
    is_ja_complete = models.BooleanField(default=False, verbose_name='일본어 완성')
    
    # 생성 시 사용자의 프로필 언어 (자동 설정)
    created_language = models.CharField(
        max_length=2, 
        choices=LANGUAGE_CHOICES,
        verbose_name='생성 언어',
        default=BASE_LANGUAGE
    )
    
    # 메타 정보
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="생성자", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")
    
    # 카테고리 관계 (ManyToMany - 태그는 여러 카테고리에 속할 수 있음)
    categories = models.ManyToManyField(
        TagCategory,
        blank=True,
        verbose_name="카테고리들",
        related_name="tags"
    )
    
    class Meta:
        verbose_name = "태그"
        verbose_name_plural = "태그들"
        ordering = ['name_ko']  # 알파벳 순서로 정렬
        indexes = [
            models.Index(fields=['name_ko']),
            models.Index(fields=['name_en']),
            models.Index(fields=['name_es']),
            models.Index(fields=['name_zh']),
            models.Index(fields=['name_ja']),
            models.Index(fields=['created_language']),
            models.Index(fields=['is_ko_complete']),
            models.Index(fields=['is_en_complete']),
            models.Index(fields=['is_es_complete']),
            models.Index(fields=['is_zh_complete']),
            models.Index(fields=['is_ja_complete']),
        ]
    
    def __str__(self):
        """생성 언어 기준으로 이름 반환"""
        language = self.created_language if hasattr(self, 'created_language') else BASE_LANGUAGE
        return get_localized_field(self, 'name', language)
    
    @property
    def name(self):
        """현재 활성 언어의 태그명 반환 (기존 코드 호환성)"""
        language = self.created_language if hasattr(self, 'created_language') else BASE_LANGUAGE
        return get_localized_field(self, 'name', language, '')
    
    @property
    def has_any_name(self):
        """어떤 언어든 이름이 있는지 확인"""
        from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
        for lang in SUPPORTED_LANGUAGES:
            field_name = f'name_{lang}'
            if hasattr(self, field_name) and getattr(self, field_name, None):
                return True
        return False
    
    @property
    def available_languages(self):
        """사용 가능한 언어 목록"""
        from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
        languages = []
        for lang in SUPPORTED_LANGUAGES:
            field_name = f'name_{lang}'
            if hasattr(self, field_name) and getattr(self, field_name, None):
                languages.append(lang)
        return languages
    
    def getLocalizedName(self, language=None):
        """
        지정된 언어에 맞는 태그명 반환
        
        Args:
            language (str): 언어 코드. None이면 created_language 사용
        
        Returns:
            str: 해당 언어의 태그명 또는 fallback 태그명
        """
        if language is None:
            language = self.created_language if hasattr(self, 'created_language') else BASE_LANGUAGE
        return get_localized_field(self, 'name', language)
    
    def save(self, *args, **kwargs):
        """
        저장 시 언어별 완성도 자동 업데이트 및 생성 언어 설정
        """
        # 생성 시에만 언어 자동 설정
        if not self.pk and not self.created_language:
            if self.created_by and hasattr(self.created_by, 'userprofile'):
                self.created_language = self.created_by.userprofile.language
            else:
                self.created_language = BASE_LANGUAGE  # 기본값
        
        # 언어별 완성도 자동 업데이트
        self.is_ko_complete = bool(self.name_ko)
        self.is_en_complete = bool(self.name_en)
        self.is_es_complete = bool(self.name_es)
        self.is_zh_complete = bool(self.name_zh)
        self.is_ja_complete = bool(self.name_ja)
        
        super().save(*args, **kwargs)


class Exam(models.Model):
    """
    시험 모델 - 다국어 제목/설명 지원
    
    다국어 처리 방식 (Study Title/Goal과 동일):
    1. 사용자는 title, description 필드에만 입력 (현재 언어로)
    2. 백엔드에서 자동으로 사용자 언어에 맞는 필드에 저장
    3. MultilingualContentManager가 자동으로 번역 수행
    4. 프론트엔드에서는 getLocalizedTitle() 메서드로 현재 언어에 맞는 제목 표시
    
    ⚠️  운영 환경 마이그레이션 주의사항:
    1. 기존 title, description 필드가 title_ko, description_ko로 마이그레이션됨
    2. 마이그레이션 시 데이터 손실 방지를 위해 단계별 실행 필요
    3. 롤백이 불가능하므로 충분한 테스트 후 적용
    
    마이그레이션 순서:
    1. 마이그레이션 파일 생성 (데이터 복사)
    2. 기존 필드 제거 마이그레이션
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # 다국어 제목 (기존 title 필드 대체)
    title_ko = models.CharField(max_length=200, verbose_name='한국어 제목', blank=True)
    title_en = models.CharField(max_length=200, verbose_name='영어 제목', blank=True)
    title_es = models.CharField(max_length=200, verbose_name='스페인어 제목', blank=True)
    title_zh = models.CharField(max_length=200, verbose_name='중국어 제목', blank=True)
    title_ja = models.CharField(max_length=200, verbose_name='일본어 제목', blank=True)
    
    # 다국어 설명 (기존 description 필드 대체)
    description_ko = models.TextField(verbose_name='한국어 설명', blank=True, null=True)
    description_en = models.TextField(verbose_name='영어 설명', blank=True, null=True)
    description_es = models.TextField(verbose_name='스페인어 설명', blank=True, null=True)
    description_zh = models.TextField(verbose_name='중국어 설명', blank=True, null=True)
    description_ja = models.TextField(verbose_name='일본어 설명', blank=True, null=True)
    
    # 언어별 완성도 추적
    is_ko_complete = models.BooleanField(default=False, verbose_name='한국어 완성')
    is_en_complete = models.BooleanField(default=False, verbose_name='영어 완성')
    is_es_complete = models.BooleanField(default=False, verbose_name='스페인어 완성')
    is_zh_complete = models.BooleanField(default=False, verbose_name='중국어 완성')
    is_ja_complete = models.BooleanField(default=False, verbose_name='일본어 완성')
    
    # 생성 시 사용자의 프로필 언어 (자동 설정)
    created_language = models.CharField(
        max_length=2, 
        choices=LANGUAGE_CHOICES,
        verbose_name='생성 언어',
        default=BASE_LANGUAGE
    )
    
    # 기존 필드들
    questions = models.ManyToManyField(Question, through='ExamQuestion', verbose_name="문제들")
    total_questions = models.IntegerField(verbose_name="총 문제 수")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일", db_index=True)
    # 버전 관리 필드
    original_exam = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='versions', verbose_name="원본 시험", db_index=True)
    version_number = models.IntegerField(default=0, verbose_name="버전 번호")
    is_original = models.BooleanField(default=True, verbose_name="원본 여부", db_index=True)
    file_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="연결된 파일")
    is_public = models.BooleanField(default=True, verbose_name="공개 여부", db_index=True)
    force_answer = models.BooleanField(default=False, verbose_name="답안 입력 강제", help_text="체크하면 Pass/Fail 버튼 대신 Submit 버튼으로 답안을 검증합니다")
    voice_mode_enabled = models.BooleanField(default=False, verbose_name="음성 모드 지원", help_text="체크하면 음성으로 시험을 볼 수 있습니다")
    ai_mock_interview = models.BooleanField(default=False, verbose_name="AI 모의 인터뷰", help_text="체크하면 AI와 함께 모의 인터뷰를 진행할 수 있습니다")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="생성자", db_index=True)
    
    # 태그 관계 추가
    tags = models.ManyToManyField(Tag, blank=True, verbose_name="태그들", related_name="exams")
    
    # 지원 언어 필드 (콤마로 구분된 언어 코드, 예: "ko,en")
    supported_languages = models.CharField(
        max_length=20,
        default='',
        blank=True,
        verbose_name='지원 언어',
        help_text='콤마로 구분된 언어 코드 (예: "ko,en")',
        db_index=True
    )
    
    # 시험 난이도 (1~10 단계)
    exam_difficulty = models.IntegerField(
        default=5,
        verbose_name='시험 난이도',
        help_text='시험의 난이도 (1: 쉬운 문제만, 10: 어려운 문제만, 5: 적절히 섞임)',
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        db_index=True
    )
    
    # 연령 등급 (4+, 9+, 12+, 17+)
    age_rating = models.CharField(
        max_length=10,
        choices=[
            ('4+', '4+'),
            ('9+', '9+'),
            ('12+', '12+'),
            ('17+', '17+'),
        ],
        default='17+',
        verbose_name='연령 등급',
        help_text='시험 내용을 분석하여 추정된 연령 등급',
        db_index=True
    )

    class Meta:
        verbose_name = "시험"
        verbose_name_plural = "시험들"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_public', '-created_at']),
            models.Index(fields=['is_original', '-created_at']),
            models.Index(fields=['original_exam', 'version_number']),
            models.Index(fields=['title_ko']),  # 한국어 제목 검색 최적화
            models.Index(fields=['title_en']),  # 영어 제목 검색 최적화
            models.Index(fields=['title_es']),  # 스페인어 제목 검색 최적화
            models.Index(fields=['title_zh']),  # 중국어 제목 검색 최적화
            models.Index(fields=['title_ja']),  # 일본어 제목 검색 최적화
            models.Index(fields=['created_by', '-created_at']),  # 생성자별 시험 조회 최적화
            models.Index(fields=['is_public', 'is_original', '-created_at']),  # 복합 인덱스
            models.Index(fields=['created_language']),  # 생성 언어별 조회 최적화
            models.Index(fields=['is_ko_complete']),  # 한국어 완성도별 조회 최적화
            models.Index(fields=['is_en_complete']),  # 영어 완성도별 조회 최적화
            models.Index(fields=['is_es_complete']),  # 스페인어 완성도별 조회 최적화
            models.Index(fields=['is_zh_complete']),  # 중국어 완성도별 조회 최적화
        ]

    def __str__(self):
        """
        문자열 표현 (Study Title/Goal과 동일한 다국어 처리 방식)
        생성 언어 기준으로 제목 반환
        """
        language = self.created_language if hasattr(self, 'created_language') else BASE_LANGUAGE
        title = get_localized_field(self, 'title', language)
        
        if self.is_original:
            return title
        else:
            return f"{title} (Retake v{self.version_number})"
    
    @property
    def title(self):
        """
        현재 활성 언어의 제목 반환 (기존 코드 호환성)
        
        다국어 처리 방식:
        1. 사용자가 입력한 title 필드는 현재 사용자 언어에 맞는 필드에 저장됨
        2. 이 속성은 해당 언어 필드의 값을 반환
        3. 프론트엔드에서는 getLocalizedTitle() 메서드 사용 권장
        """
        language = self.created_language if hasattr(self, 'created_language') else BASE_LANGUAGE
        return get_localized_field(self, 'title', language, '')
    
    @property
    def description(self):
        """
        현재 활성 언어의 설명 반환 (기존 코드 호환성)
        
        다국어 처리 방식:
        1. 사용자가 입력한 description 필드는 현재 사용자 언어에 맞는 필드에 저장됨
        2. 이 속성은 해당 언어 필드의 값을 반환
        3. 프론트엔드에서는 getLocalizedDescription() 메서드 사용 권장
        """
        language = self.created_language if hasattr(self, 'created_language') else BASE_LANGUAGE
        return get_localized_field(self, 'description', language, '')
    
    @property
    def has_any_title(self):
        """어떤 언어든 제목이 있는지 확인"""
        from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
        for lang in SUPPORTED_LANGUAGES:
            field_name = f'title_{lang}'
            if hasattr(self, field_name) and getattr(self, field_name, None):
                return True
        return False
    
    @property
    def has_any_description(self):
        """어떤 언어든 설명이 있는지 확인"""
        from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
        for lang in SUPPORTED_LANGUAGES:
            field_name = f'description_{lang}'
            if hasattr(self, field_name) and getattr(self, field_name, None):
                return True
        return False
    
    @property
    def available_languages(self):
        """사용 가능한 언어 목록"""
        from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
        languages = []
        for lang in SUPPORTED_LANGUAGES:
            title_field = f'title_{lang}'
            desc_field = f'description_{lang}'
            if (hasattr(self, title_field) and getattr(self, title_field, None) and
                hasattr(self, desc_field) and getattr(self, desc_field, None)):
                languages.append(lang)
        return languages
    
    @property
    def latest_score_percentage(self):
        """최신 시험 결과의 백분율 점수"""
        result = self.latest_result
        if result and result.total_score:
            return (result.score / result.total_score) * 100
        return None
    
    @property
    def display_title(self):
        """표시용 제목"""
        language = self.created_language if hasattr(self, 'created_language') else BASE_LANGUAGE
        title = get_localized_field(self, 'title', language)
        if self.is_original:
            return title
        else:
            return f"{title} (Retake)"
    
    def getLocalizedTitle(self, language=None):
        """
        지정된 언어에 맞는 제목 반환
        
        Args:
            language (str): 언어 코드. None이면 created_language 사용
        
        Returns:
            str: 해당 언어의 제목 또는 fallback 제목
        """
        if language is None:
            language = self.created_language if hasattr(self, 'created_language') else BASE_LANGUAGE
        return get_localized_field(self, 'title', language)

    @property
    def latest_result(self):
        # 현재 요청의 사용자 정보를 가져오기 위해 serializer context에서 확인
        # 이 속성은 serializer에서만 사용되므로 context를 통해 사용자 정보를 전달받아야 함
        # 기본적으로는 모든 사용자의 결과를 반환하되, serializer에서 필터링
        if self.is_original:
            all_exam_ids = [self.id] + list(self.versions.values_list('id', flat=True))
            return ExamResult.objects.filter(exam_id__in=all_exam_ids).order_by('-completed_at').first()
        else:
            return ExamResult.objects.filter(exam=self).order_by('-completed_at').first()

    @property
    def latest_correct_count(self):
        result = self.latest_result
        return result.correct_count if result else None

    @property
    def latest_total_score(self):
        result = self.latest_result
        return result.total_score if result else None

    @property
    def total_correct_questions(self):
        """
        전체 시험에서 맞춘 문제 수 (각 문제별 통계 합산) - 모든 사용자 기준
        
        ⚠️  주의: 이 프로퍼티는 모든 사용자의 통계를 통합하여 반환합니다
        - 개인 정보 보호를 위해 개별 사용자 화면에서는 사용하지 않아야 함
        - 관리자 대시보드나 전체 통계에서만 사용
        
        개인 통계가 필요한 경우: get_total_correct_questions_for_user(user) 메서드 사용
        """
        total_correct = 0
        
        for question in self.questions.all():
            # 해당 문제의 정답 시도가 있는지 확인 (모든 시험에서)
            correct_attempts = ExamResultDetail.objects.filter(
                question=question,
                is_correct=True
            ).count()
            
            if correct_attempts > 0:
                total_correct += 1
        
        return total_correct

    def get_total_correct_questions_for_user(self, user):
        """
        특정 사용자의 맞춘 시도 수 계산 (문제별이 아닌 시도별)
        
        핵심 원칙: 모든 통계 정보는 개인 통계만 반환한다
        - 특정 사용자의 개인 통계만 반환 (다른 사용자 정보 노출 금지)
        - 모든 통계는 원본 시험에만 남김 - 복사된 시험인 경우 원본 시험의 결과 반환
        - 개인정보 보호 및 보안 강화
        """
        # 추천 시험인 경우 각 문제별로 개별 원본 시험에서 푼 점수를 합산
        if ("Today's Quizzes for" in (self.title_ko or '')) or ("Today's Quizzes for" in (self.title_en or '')):
            total_correct = 0
            
            for question in self.questions.all():
                # 문제의 group_id를 통해 원본 시험 찾기
                if question.group_id:
                    try:
                        # group_id가 원본 시험 제목인 경우
                        original_exam = Exam.objects.filter(
                            title_ko=question.group_id,
                            is_original=True
                        ).first()
                        
                        if not original_exam:
                            original_exam = Exam.objects.filter(
                                title_en=question.group_id,
                                is_original=True
                            ).first()
                        
                        if original_exam:
                            # 해당 원본 시험에서 이 문제를 정답으로 맞춘 시도 수 계산
                            correct_attempts = ExamResultDetail.objects.filter(
                                result__exam=original_exam,
                                result__user=user,
                                question=question,
                                is_correct=True
                            ).count()
                            
                            total_correct += correct_attempts
                    except Exception:
                        pass
            
            return total_correct
        
        # 복사된 시험인 경우 원본 시험의 결과를 참조
        if not self.is_original and self.original_exam:
            # 원본 시험에서 해당 사용자의 정답 시도 수 계산
            total_correct = ExamResultDetail.objects.filter(
                result__exam=self.original_exam,
                result__user=user,
                is_correct=True
            ).count()
            return total_correct
        
        # 일반적인 경우: 현재 시험의 결과 반환
        total_correct = ExamResultDetail.objects.filter(
            result__exam=self,
            result__user=user,
            is_correct=True
        ).count()
        
        return total_correct

    def get_total_attempted_questions_for_user(self, user):
        """특정 사용자가 해당 시험에서 시도한 문제 수를 반환합니다."""
        if not user.is_authenticated:
            return 0
        
        # 추천 시험인 경우 각 문제별로 개별 원본 시험에서 푼 점수를 합산
        if ("Today's Quizzes for" in (self.title_ko or '')) or ("Today's Quizzes for" in (self.title_en or '')):
            total_attempts = 0
            
            for question in self.questions.all():
                # 문제의 group_id를 통해 원본 시험 찾기
                if question.group_id:
                    try:
                        # group_id가 원본 시험 제목인 경우
                        original_exam = Exam.objects.filter(
                            title_ko=question.group_id,
                            is_original=True
                        ).first()
                        
                        if not original_exam:
                            original_exam = Exam.objects.filter(
                                title_en=question.group_id,
                                is_original=True
                            ).first()
                        
                        if original_exam:
                            # 해당 원본 시험에서 이 문제를 시도했는지 확인
                            has_attempted = ExamResultDetail.objects.filter(
                                result__exam=original_exam,
                                result__user=user,
                                question=question
                            ).exists()
                            
                            if has_attempted:
                                total_attempts += 1
                    except Exception:
                        pass
            
            return total_attempts
        
        # 복사된 시험인 경우 원본 시험의 결과를 참조
        if not self.is_original and self.original_exam:
            # 원본 시험에서 해당 사용자의 시도 수 계산
            total_attempts = ExamResultDetail.objects.filter(
                result__exam=self.original_exam,
                result__user=user
            ).count()
            return total_attempts
        
        # 일반적인 경우: 현재 시험의 결과 반환
        total_attempts = ExamResultDetail.objects.filter(
            result__exam=self,
            result__user=user
        ).count()
        
        return total_attempts

    def get_accuracy_percentage_for_user(self, user):
        """
        특정 사용자의 합격률 계산 (exam-detail과 동일한 로직)
        
        계산 방식:
        1. 전체 시도 횟수 중 정답 횟수의 비율
        2. ExamResultDetail에서 해당 사용자의 모든 시도 기록을 기반으로 계산
        """
        if not user.is_authenticated:
            return None
        
        # 추천 시험인 경우 각 문제별로 개별 원본 시험에서 푼 점수를 합산
        if ("Today's Quizzes for" in (self.title_ko or '')) or ("Today's Quizzes for" in (self.title_en or '')):
            total_correct = 0
            total_attempts = 0
            
            for question in self.questions.all():
                # 문제의 group_id를 통해 원본 시험 찾기
                if question.group_id:
                    try:
                        # group_id가 원본 시험 제목인 경우
                        original_exam = Exam.objects.filter(
                            title_ko=question.group_id,
                            is_original=True
                        ).first()
                        
                        if not original_exam:
                            original_exam = Exam.objects.filter(
                                title_en=question.group_id,
                                is_original=True
                            ).first()
                        
                        if original_exam:
                            # 해당 원본 시험에서 이 문제를 시도했는지 확인
                            has_attempted = ExamResultDetail.objects.filter(
                                result__exam=original_exam,
                                result__user=user,
                                question=question
                            ).exists()
                            
                            if has_attempted:
                                total_attempts += 1
                                # 정답인지 확인
                                is_correct = ExamResultDetail.objects.filter(
                                    result__exam=original_exam,
                                    result__user=user,
                                    question=question,
                                    is_correct=True
                                ).exists()
                                
                                if is_correct:
                                    total_correct += 1
                    except Exception:
                        pass
            
            if total_attempts > 0:
                return (total_correct / total_attempts) * 100
            return None
        
        # 일반적인 경우: 원본 시험이 있으면 원본 시험의 결과 반환
        target_exam = self.original_exam if not self.is_original and self.original_exam else self
        
        # 원본 시험의 모든 시도 중 정답 비율 계산
        total_attempts = ExamResultDetail.objects.filter(
            result__exam=target_exam,
            result__user=user
        ).count()
        
        if total_attempts == 0:
            return None
        
        total_correct = ExamResultDetail.objects.filter(
            result__exam=target_exam,
            result__user=user,
            is_correct=True
        ).count()
        
        return (total_correct / total_attempts) * 100

    @property
    def total_questions_attempted(self):
        """
        전체 시험에서 시도한 문제 수 (각 문제별 통계 합산) - 모든 사용자 기준
        
        ⚠️  주의: 이 프로퍼티는 모든 사용자의 통계를 통합하여 반환합니다
        - 개인 정보 보호를 위해 개별 사용자 화면에서는 사용하지 않아야 함
        - 관리자 대시보드나 전체 통계에서만 사용
        
        개인 통계가 필요한 경우: get_total_correct_questions_for_user(user) 메서드 사용
        """
        total_attempted = 0
        
        for question in self.questions.all():
            # 해당 문제의 시도가 있는지 확인 (모든 시험에서)
            attempts = ExamResultDetail.objects.filter(
                question=question
            ).count()
            
            if attempts > 0:
                total_attempted += 1
        
        return total_attempted

    @property
    def has_results(self):
        """시험 결과가 있는지 확인"""
        return ExamResult.objects.filter(exam=self).exists()

    def delete(self, *args, **kwargs):
        """시험 삭제 시 통계 정보 보존을 위해 문제는 삭제하지 않고 연결만 삭제"""
        # 해당 시험에 연결된 문제들의 ID 수집
        exam_question_ids = list(self.questions.values_list('id', flat=True))
        
        # 추천 시험인 경우, 해당 시험에서 선택된 문제들의 group_id 초기화
        # 단, Daily Exam 생성 시 자동으로 설정된 group_id만 초기화 (사용자가 설정한 group_id는 보존)
        is_recommendation_exam = "Today's Quizzes for" in self.title
        if is_recommendation_exam and exam_question_ids:
            # 해당 시험의 제목으로 group_id가 설정된 문제들만 찾아 초기화
            # (사용자가 직접 설정한 다른 group_id는 보존)
            Question.objects.filter(
                id__in=exam_question_ids,
                group_id=self.title
            ).update(group_id='')
            print(f"[DELETE_EXAM] 추천 시험 '{self.title}'의 문제들 group_id 초기화 완료 (Daily Exam 생성 시 자동 설정된 것만)")
        
        # 통계 정보 보존을 위해 문제는 삭제하지 않음
        # 대신 시험-문제 연결만 삭제 (ExamQuestion 관계 삭제)
        print(f"[DELETE_EXAM] 시험 '{self.title}' - 문제 연결만 삭제 (문제 유지, 통계 정보 보존)")
        
        # 부모 클래스의 delete 메서드 호출
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        """
        저장 시 언어별 완성도 자동 업데이트 및 생성 언어 설정
        
        다국어 처리 방식 (Study Title/Goal과 동일):
        1. 사용자가 title, description 필드에 입력한 내용을
           현재 사용자 언어에 맞는 필드(title_ko/description_ko 또는 title_en/description_en)에 자동 저장
        2. MultilingualContentManager가 자동으로 번역 수행 (뷰에서 처리)
        3. 언어별 완성도 상태 자동 업데이트
        4. 지원 언어는 생성자 프로필의 auto_translation_enabled 설정에 따라 결정
        """
        # 생성 시에만 언어 자동 설정
        if not self.pk and not self.created_language:
            if self.created_by and hasattr(self.created_by, 'userprofile'):
                self.created_language = self.created_by.userprofile.language
            else:
                self.created_language = BASE_LANGUAGE  # 기본값
        
        # 언어별 완성도 자동 업데이트
        self.is_ko_complete = bool(self.title_ko and self.description_ko)
        self.is_en_complete = bool(self.title_en and self.description_en)
        self.is_es_complete = bool(self.title_es and self.description_es)
        self.is_zh_complete = bool(self.title_zh and self.description_zh)
        self.is_ja_complete = bool(self.title_ja and self.description_ja)
        
        # 지원 언어 업데이트: 생성자 프로필의 auto_translation_enabled 설정 기반
        # 단, _skip_auto_supported_languages 플래그가 설정되어 있으면 자동 설정을 건너뜀
        # 번역이 완료되어 완성도가 변경되면 supported_languages도 자동으로 업데이트
        if not (hasattr(self, '_skip_auto_supported_languages') and self._skip_auto_supported_languages):
            supported = []
            if self.created_by and hasattr(self.created_by, 'profile'):
                profile = self.created_by.profile
                if hasattr(profile, 'auto_translation_enabled') and profile.auto_translation_enabled:
                    # 자동 번역이 활성화되어 있으면 완성된 언어만 지원
                    if self.is_ko_complete:
                        supported.append(LANGUAGE_KO)
                    if self.is_en_complete:
                        supported.append(LANGUAGE_EN)
                    if self.is_es_complete:
                        supported.append(LANGUAGE_ES)
                    if self.is_zh_complete:
                        supported.append(LANGUAGE_ZH)
                    if self.is_ja_complete:
                        supported.append(LANGUAGE_JA)
                    # 둘 다 완성되지 않았으면 생성 언어만 포함
                    if not supported:
                        supported.append(self.created_language)
                else:
                    # 자동 번역이 비활성화되어 있으면 생성 언어만 지원
                    supported.append(self.created_language)
            else:
                # 생성자가 없거나 프로필이 없으면 생성 언어만 지원
                supported.append(self.created_language)
            
            new_supported = ','.join(supported)
            # supported_languages가 비어있거나 변경된 경우에만 업데이트
            if not self.supported_languages or new_supported != self.supported_languages:
                self.supported_languages = new_supported
        
        super().save(*args, **kwargs)


class ExamQuestion(models.Model):
    """시험-문제 연결 모델"""
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, verbose_name="시험")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="문제")
    order = models.IntegerField(verbose_name="순서")

    class Meta:
        verbose_name = "시험 문제"
        verbose_name_plural = "시험 문제들"
        ordering = ['order']
    



class ExamResult(models.Model):
    """시험 결과 모델"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, verbose_name="시험", db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="사용자", db_index=True)
    score = models.IntegerField(verbose_name="점수")
    total_score = models.IntegerField(verbose_name="총점")
    correct_count = models.IntegerField(verbose_name="정답 수")
    wrong_count = models.IntegerField(verbose_name="오답 수")
    completed_at = models.DateTimeField(default=timezone.now, verbose_name="완료일", db_index=True)
    elapsed_seconds = models.IntegerField(default=0, verbose_name="소요 시간(초)")
    is_voice_interview = models.BooleanField(default=False, verbose_name="음성 인터뷰 결과", db_index=True, help_text="Voice Interview 모드로 진행된 시험 결과인지 여부")

    class Meta:
        verbose_name = "시험 결과"
        verbose_name_plural = "시험 결과들"
        ordering = ['-completed_at']
        indexes = [
            models.Index(fields=['user', '-completed_at']),
            models.Index(fields=['exam', '-completed_at']),
            models.Index(fields=['user', 'exam']),
            models.Index(fields=['exam', 'is_voice_interview', '-completed_at']),
        ]

    def __str__(self):
        exam_language = self.exam.created_language if hasattr(self.exam, 'created_language') else BASE_LANGUAGE
        exam_title = get_localized_field(self.exam, 'title', exam_language)
        return f"{exam_title} - {self.score}/{self.total_score}"


class ExamResultDetail(models.Model):
    """시험 결과 상세 모델"""
    result = models.ForeignKey(ExamResult, on_delete=models.CASCADE, verbose_name="시험 결과", db_index=True)
    question = models.ForeignKey(Question, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="문제", db_index=True)
    # 문제 삭제 후에도 통계 정보를 보존하기 위한 필드들
    question_title = models.CharField(max_length=200, verbose_name="문제 제목", blank=True, null=True)
    question_content = models.TextField(verbose_name="문제 내용", blank=True, null=True)
    question_answer = models.TextField(verbose_name="문제 정답", blank=True, null=True)
    question_difficulty = models.CharField(max_length=20, verbose_name="문제 난이도", blank=True, null=True)
    user_answer = models.TextField(verbose_name="사용자 답안")
    is_correct = models.BooleanField(verbose_name="정답 여부", db_index=True)
    elapsed_seconds = models.IntegerField(default=0, verbose_name="문제별 소요 시간(초)")
    evaluation = models.TextField(verbose_name="AI 평가 내용", blank=True, null=True, help_text="Voice Interview 모드에서 AI가 제공한 평가 내용")

    class Meta:
        verbose_name = "시험 결과 상세"
        verbose_name_plural = "시험 결과 상세들"
        indexes = [
            models.Index(fields=['result', 'is_correct']),
            models.Index(fields=['question', 'is_correct']),
        ]

    def save(self, *args, **kwargs):
        """저장 시 문제 정보를 보존"""
        if self.question and not self.question_title:
            # 다국어 제목 필드 사용
            question_language = self.question.created_language if hasattr(self.question, 'created_language') else BASE_LANGUAGE
            self.question_title = get_localized_field(self.question, 'title', question_language)
            self.question_content = get_localized_field(self.question, 'content', question_language)
            self.question_answer = get_localized_field(self.question, 'answer', question_language)
            self.question_difficulty = self.question.difficulty
        super().save(*args, **kwargs)


class Study(models.Model):
    """
    스터디 모델 - 다국어 제목/목표 지원
    
    ⚠️  운영 환경 마이그레이션 주의사항:
    1. 기존 title, goal 필드가 title_ko, goal_ko로 마이그레이션됨
    2. 마이그레이션 시 데이터 손실 방지를 위해 단계별 실행 필요
    3. 롤백이 불가능하므로 충분한 테스트 후 적용
    
    마이그레이션 순서:
    1. 0044_migrate_existing_study_data.py (데이터 복사)
    2. 0043_remove_study_goal_remove_study_title_and_more.py (필드 제거)
    
    롤백 방법:
    - 마이그레이션 전: python manage.py migrate quiz 0042
    - 데이터 복원: 백업 파일에서 loaddata
    """
    # 다국어 제목 (기존 title 필드 대체)
    title_ko = models.CharField(max_length=200, verbose_name='한국어 제목', blank=True)
    title_en = models.CharField(max_length=200, verbose_name='영어 제목', blank=True)
    title_es = models.CharField(max_length=200, verbose_name='스페인어 제목', blank=True)
    title_zh = models.CharField(max_length=200, verbose_name='중국어 제목', blank=True)
    title_ja = models.CharField(max_length=200, verbose_name='일본어 제목', blank=True)
    
    # 다국어 목표/설명 (기존 goal 필드 대체)
    goal_ko = models.TextField(verbose_name='한국어 목표', blank=True)
    goal_en = models.TextField(verbose_name='영어 목표', blank=True)
    goal_es = models.TextField(verbose_name='스페인어 목표', blank=True)
    goal_zh = models.TextField(verbose_name='중국어 목표', blank=True)
    goal_ja = models.TextField(verbose_name='일본어 목표', blank=True)
    
    # 언어별 완성도 추적
    is_ko_complete = models.BooleanField(default=False, verbose_name='한국어 완성')
    is_en_complete = models.BooleanField(default=False, verbose_name='영어 완성')
    is_es_complete = models.BooleanField(default=False, verbose_name='스페인어 완성')
    is_zh_complete = models.BooleanField(default=False, verbose_name='중국어 완성')
    is_ja_complete = models.BooleanField(default=False, verbose_name='일본어 완성')
    
    # 생성 시 사용자의 프로필 언어 (자동 설정)
    created_language = models.CharField(
        max_length=2, 
        choices=LANGUAGE_CHOICES,
        verbose_name='생성 언어',
        default=BASE_LANGUAGE
    )
    
    # 기존 필드들
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_public = models.BooleanField(default=True, verbose_name="공개 여부", db_index=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="생성자", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")
    
    # 태그 관계 추가
    tags = models.ManyToManyField(Tag, blank=True, verbose_name="태그들", related_name="studies")
    
    # 지원 언어 필드 (콤마로 구분된 언어 코드, 예: "ko,en")
    supported_languages = models.CharField(
        max_length=20,
        default='',
        blank=True,
        verbose_name='지원 언어',
        help_text='콤마로 구분된 언어 코드 (예: "ko,en")',
        db_index=True
    )

    class Meta:
        indexes = [
            models.Index(fields=['is_public']),
            models.Index(fields=['created_at']),
            models.Index(fields=['created_language']),
            models.Index(fields=['is_ko_complete']),
            models.Index(fields=['is_en_complete']),
            models.Index(fields=['is_es_complete']),
            models.Index(fields=['is_zh_complete']),
            models.Index(fields=['is_ja_complete']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        """생성 언어 기준으로 제목 반환"""
        language = self.created_language if hasattr(self, 'created_language') else BASE_LANGUAGE
        return get_localized_field(self, 'title', language)
    
    @property
    def title(self):
        """현재 활성 언어의 제목 반환 (기존 코드 호환성) - 나중에 제거 예정"""
        language = self.created_language if hasattr(self, 'created_language') else BASE_LANGUAGE
        return get_localized_field(self, 'title', language, '')
    
    @property
    def goal(self):
        """현재 활성 언어의 목표 반환 (기존 코드 호환성) - 나중에 제거 예정"""
        language = self.created_language if hasattr(self, 'created_language') else BASE_LANGUAGE
        return get_localized_field(self, 'goal', language, '')
    
    @property
    def has_any_title(self):
        """어떤 언어든 제목이 있는지 확인"""
        return bool(self.title_ko or self.title_en or self.title_es or self.title_zh or self.title_ja)
    
    @property
    def has_any_goal(self):
        """어떤 언어든 목표가 있는지 확인"""
        return bool(self.goal_ko or self.goal_en or self.goal_es or self.goal_zh or self.goal_ja)
    
    @property
    def available_languages(self):
        """사용 가능한 언어 목록"""
        from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
        languages = []
        for lang in SUPPORTED_LANGUAGES:
            title_field = f'title_{lang}'
            goal_field = f'goal_{lang}'
            if (hasattr(self, title_field) and getattr(self, title_field, None) and
                hasattr(self, goal_field) and getattr(self, goal_field, None)):
                languages.append(lang)
        return languages
    
    def save(self, *args, **kwargs):
        # 생성 시에만 언어 자동 설정
        if not self.pk and not self.created_language:
            if self.created_by and hasattr(self.created_by, 'userprofile'):
                self.created_language = self.created_by.userprofile.language
            self.created_language = BASE_LANGUAGE  # 기본값
        
        # start_date가 null이면 오늘 날짜로 자동 설정
        # 랜덤으로 생성되거나 파일로부터 생성되는 시험의 경우 자동으로 오늘부터 시작
        from django.utils import timezone
        if not self.start_date:
            self.start_date = timezone.now().date()
        
        # 언어별 완성도 자동 업데이트
        self.is_ko_complete = bool(self.title_ko and self.goal_ko)
        self.is_en_complete = bool(self.title_en and self.goal_en)
        self.is_es_complete = bool(self.title_es and self.goal_es)
        self.is_zh_complete = bool(self.title_zh and self.goal_zh)
        self.is_ja_complete = bool(self.title_ja and self.goal_ja)
        
        # 지원 언어 업데이트: 생성자 프로필의 auto_translation_enabled 설정 기반
        # 단, _skip_auto_supported_languages 플래그가 설정되어 있으면 자동 설정을 건너뜀
        # 번역이 완료되어 완성도가 변경되면 supported_languages도 자동으로 업데이트
        if not (hasattr(self, '_skip_auto_supported_languages') and self._skip_auto_supported_languages):
            supported = []
            if self.created_by and hasattr(self.created_by, 'profile'):
                profile = self.created_by.profile
                if hasattr(profile, 'auto_translation_enabled') and profile.auto_translation_enabled:
                    # 자동 번역이 활성화되어 있으면 완성된 언어만 지원
                    if self.is_ko_complete:
                        supported.append(LANGUAGE_KO)
                    if self.is_en_complete:
                        supported.append(LANGUAGE_EN)
                    if self.is_es_complete:
                        supported.append(LANGUAGE_ES)
                    if self.is_zh_complete:
                        supported.append(LANGUAGE_ZH)
                    if self.is_ja_complete:
                        supported.append(LANGUAGE_JA)
                    # 둘 다 완성되지 않았으면 생성 언어만 포함
                    if not supported:
                        supported.append(self.created_language)
                else:
                    # 자동 번역이 비활성화되어 있으면 생성 언어만 지원
                    supported.append(self.created_language)
            else:
                # 생성자가 없거나 프로필이 없으면 생성 언어만 지원
                supported.append(self.created_language)
            
            new_supported = ','.join(supported)
            # supported_languages가 비어있거나 변경된 경우에만 업데이트
            if not self.supported_languages or new_supported != self.supported_languages:
                self.supported_languages = new_supported
        
        super().save(*args, **kwargs)

class StudyTask(models.Model):
    study = models.ForeignKey(Study, on_delete=models.CASCADE, related_name='tasks', db_index=True)
    
    # 다국어 Task 이름
    name_ko = models.CharField(max_length=200, verbose_name='한국어 Task 이름', blank=True)
    name_en = models.CharField(max_length=200, verbose_name='영어 Task 이름', blank=True)
    name_es = models.CharField(max_length=200, verbose_name='스페인어 Task 이름', blank=True)
    name_zh = models.CharField(max_length=200, verbose_name='중국어 Task 이름', blank=True)
    name_ja = models.CharField(max_length=200, verbose_name='일본어 Task 이름', blank=True)
    
    exam = models.ForeignKey(Exam, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    progress = models.FloatField(default=0)  # 0-100%
    seq = models.IntegerField(default=0, verbose_name="순서")  # 데이터베이스의 seq 컬럼과 일치
    # 주의: 이 필드는 clear_all_statistics.py 스크립트로 초기화됨
    # 2025-08-13 23:16:50에 모든 통계 데이터 삭제 완료
    # 새로운 학습 활동을 시작하면 이 값이 업데이트됨
    is_public = models.BooleanField(default=True, verbose_name="공개 여부")
    
    # 언어별 완성도 추적
    is_ko_complete = models.BooleanField(default=False, verbose_name='한국어 완성')
    is_en_complete = models.BooleanField(default=False, verbose_name='영어 완성')
    is_es_complete = models.BooleanField(default=False, verbose_name='스페인어 완성')
    is_zh_complete = models.BooleanField(default=False, verbose_name='중국어 완성')
    is_ja_complete = models.BooleanField(default=False, verbose_name='일본어 완성')
    
    # 생성 시 사용자의 프로필 언어 (자동 설정)
    created_language = models.CharField(
        max_length=2, 
        choices=LANGUAGE_CHOICES,
        verbose_name='생성 언어',
        default=BASE_LANGUAGE
    )
    
    # 지원 언어 필드 (콤마로 구분된 언어 코드, 예: "ko,en")
    supported_languages = models.CharField(
        max_length=20,
        default='',
        blank=True,
        verbose_name='지원 언어',
        help_text='콤마로 구분된 언어 코드 (예: "ko,en")',
        db_index=True
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['study', 'exam']),
            models.Index(fields=['study', 'seq']),  # 순서별 정렬을 위한 인덱스
            models.Index(fields=['created_language']),
            models.Index(fields=['is_ko_complete']),
            models.Index(fields=['is_en_complete']),
            models.Index(fields=['is_es_complete']),
            models.Index(fields=['is_zh_complete']),
            models.Index(fields=['is_ja_complete']),
        ]
        ordering = ['study', 'seq']  # 기본 정렬 순서 (이제 seq 필드가 Django 모델에 있음)
        verbose_name = "학습 태스크"
        verbose_name_plural = "학습 태스크들"
    
    def __str__(self):
        """생성 언어 기준으로 이름 반환"""
        study_language = self.study.created_language if hasattr(self.study, 'created_language') else BASE_LANGUAGE
        study_title = get_localized_field(self.study, 'title', study_language)
        task_language = self.created_language if hasattr(self, 'created_language') else BASE_LANGUAGE
        task_name = get_localized_field(self, 'name', task_language)
        return f"{study_title} - {task_name}"
    
    @property
    def task_name(self):
        """현재 활성 언어의 Task 이름 반환 (기존 코드 호환성)"""
        language = self.created_language if hasattr(self, 'created_language') else BASE_LANGUAGE
        return get_localized_field(self, 'name', language, '')
    
    @property
    def has_any_name(self):
        """어떤 언어든 이름이 있는지 확인"""
        from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
        for lang in SUPPORTED_LANGUAGES:
            field_name = f'name_{lang}'
            if hasattr(self, field_name) and getattr(self, field_name, None):
                return True
        return False
    
    @property
    def available_languages(self):
        """사용 가능한 언어 목록"""
        from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
        languages = []
        for lang in SUPPORTED_LANGUAGES:
            field_name = f'name_{lang}'
            if hasattr(self, field_name) and getattr(self, field_name, None):
                languages.append(lang)
        return languages
    
    def save(self, *args, **kwargs):
        # 생성 시에만 언어 자동 설정
        if not self.pk and not self.created_language:
            if self.study and self.study.created_by and hasattr(self.study.created_by, 'userprofile'):
                self.created_language = self.study.created_by.userprofile.language
            else:
                self.created_language = BASE_LANGUAGE  # 기본값
        
        # 언어별 완성도 자동 업데이트
        self.is_ko_complete = bool(self.name_ko)
        self.is_en_complete = bool(self.name_en)
        self.is_es_complete = bool(self.name_es)
        self.is_zh_complete = bool(self.name_zh)
        self.is_ja_complete = bool(self.name_ja)
        
        # 지원 언어 업데이트: 생성자 프로필의 auto_translation_enabled 설정 기반
        supported = []
        if self.study and self.study.created_by and hasattr(self.study.created_by, 'profile'):
            profile = self.study.created_by.profile
            if hasattr(profile, 'auto_translation_enabled') and profile.auto_translation_enabled:
                if self.is_ko_complete:
                    supported.append(LANGUAGE_KO)
                if self.is_en_complete:
                    supported.append(LANGUAGE_EN)
                if self.is_es_complete:
                    supported.append(LANGUAGE_ES)
                if self.is_zh_complete:
                    supported.append(LANGUAGE_ZH)
                if self.is_ja_complete:
                    supported.append(LANGUAGE_JA)
                if not supported:
                    supported.append(self.created_language)
            else:
                # 자동 번역이 비활성화되어 있으면 생성 언어만 지원
                supported.append(self.created_language)
        else:
            # 생성자가 없거나 프로필이 없으면 생성 언어만 지원
            supported.append(self.created_language)
        
        self.supported_languages = ','.join(supported)
        
        # seq가 설정되지 않은 경우 자동으로 설정
        if self.seq == 0 and self.study_id:
            # 같은 스터디 내에서 가장 큰 seq 값 + 1
            max_seq = StudyTask.objects.filter(study_id=self.study_id).aggregate(
                models.Max('seq')
            )['seq__max'] or 0
            self.seq = max_seq + 1
        
        # 진행률 자동 계산 및 업데이트 (exam이 연결된 경우)
        if self.exam and self.study_id:
            try:
                # 스터디의 모든 멤버에 대해 진행률 계산
                from django.contrib.auth.models import User
                # study_id를 사용하여 study 객체 가져오기
                from quiz.models import Study
                study = Study.objects.get(id=self.study_id)
                for member in study.members.all():
                    if member.user:
                        user = member.user
                        # 새로운 계산 로직 사용
                        correct_attempts = self.exam.get_total_correct_questions_for_user(user)
                        total_attempts = self.exam.get_total_attempted_questions_for_user(user)
                        if total_attempts > 0:
                            calculated_progress = (correct_attempts / total_attempts) * 100
                            # 현재 사용자가 스터디 생성자인 경우 progress 필드 업데이트
                            if user == study.created_by:
                                self.progress = calculated_progress
                            break  # 첫 번째 사용자(생성자)만 처리
            except Exception as e:
                # 진행률 계산 실패 시 기존 값 유지
                pass
        
        super().save(*args, **kwargs)
    
    @property
    def effective_progress(self):
        """
        진행률 계산 - StudyTask의 progress 필드를 우선 사용
        
        핵심 원칙: 모든 통계 정보는 개인 통계만 반환한다
        - StudyTask의 progress 필드가 설정되어 있으면 그것을 사용
        - progress가 0이면 현재 사용자의 개인 시험 결과 기반으로 계산
        - 모든 사용자의 통계를 통합하지 않음 (보안 및 개인정보 보호)
        """
        # StudyTask의 progress 필드가 설정되어 있으면 그것을 사용
        if self.progress > 0:
            return self.progress
        
        # progress가 0이면 개인 시험 결과 기반으로 계산
        # 주의: 이 프로퍼티는 현재 사용자 컨텍스트가 없으므로 0 반환
        # 실제 개인 진행률은 StudySerializer에서 사용자별로 계산됨
        if self.exam:
            # ❌ 이전 설계: 모든 사용자의 통계를 통합하여 진행률 계산
            # total_correct = self.exam.total_correct_questions  # 모든 사용자 기준 (잘못된 설계)
            
            # ✅ 새로운 설계: 개인 통계만 반환 (현재 컨텍스트에서는 0 반환)
            # 실제 개인 진행률은 StudySerializer.get_overall_progress()에서 계산됨
            return 0
        return 0


class Member(models.Model):
    ROLE_CHOICES = [
        ('member', '멤버'),
        ('study_admin', '스터디 관리자'),
        ('study_leader', '스터디 리더'),
    ]
    
    study = models.ForeignKey(Study, on_delete=models.CASCADE, related_name='members', db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="가입된 사용자", db_index=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    member_id = models.CharField(max_length=50, blank=True, null=True)  # 사용자 정의 ID
    affiliation = models.CharField(max_length=200, blank=True, null=True)  # 소속
    location = models.CharField(max_length=200, blank=True, null=True)  # 위치
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='member',
        verbose_name="스터디 내 역할"
    )
    is_active = models.BooleanField(default=True, verbose_name="활성화 상태", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        study_title = self.study.title_ko if self.study.title_ko else self.study.title_en or '제목 없음'
        if self.user:
            return f"{study_title} - {self.user.username} ({self.name}) - {self.get_role_display()}"
        return f"{study_title} - {self.name} - {self.get_role_display()}"
    
    class Meta:
        unique_together = ['study', 'user']  # 같은 스터디 내에서 같은 사용자 중복 방지
        indexes = [
            models.Index(fields=['study', 'is_active']),
            models.Index(fields=['user', 'is_active']),
        ]


class QuestionMemberMapping(models.Model):
    """문제와 멤버 매핑 모델"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='member_mappings')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='question_mappings')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='question_member_mappings')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['question', 'member', 'exam']
        verbose_name = '문제-멤버 매핑'
        verbose_name_plural = '문제-멤버 매핑들'

    def __str__(self):
        question_title = self.question.title_ko if self.question.title_ko else self.question.title_en or '제목 없음'
        return f"{self.member.name} - {question_title} ({self.exam.title_ko or self.exam.title_en or 'Unknown'})" 


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin_role', '관리자'),
        ('study_admin_role', '스터디 관리자'),
        ('user_role', '일반 사용자'),
    ]
    
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='user_role',
        verbose_name="역할"
    )
    random_exam_email_enabled = models.BooleanField(
        default=False,
        verbose_name="랜덤출제 이메일 발송 여부"
    )
    random_exam_question_count = models.IntegerField(
        default=3,
        verbose_name="랜덤출제 시험당 문제 수"
    )
    language = models.CharField(
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default='en',
        verbose_name="언어 설정"
    )
    email_verified = models.BooleanField(
        default=False,
        verbose_name="이메일 인증 완료"
    )
    email_verification_token = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="이메일 인증 토큰"
    )
    email_verification_sent_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="이메일 인증 발송일"
    )
    auto_translation_enabled = models.BooleanField(
        default=True,
        verbose_name="자동 번역 지원 사용",
        help_text="자동 번역 기능을 사용할지 여부"
    )
    retention_cleanup_enabled = models.BooleanField(
        default=False,
        verbose_name="자동 정리 활성화"
    )
    retention_cleanup_percentage = models.IntegerField(
        default=0,
        verbose_name="자동 정리 비율",
        help_text="매일 성공한 기록 중 삭제할 비율 (0-100%)"
    )
    interested_categories = models.ManyToManyField(
        'TagCategory',
        blank=True,
        verbose_name="관심 카테고리",
        related_name="interested_users",
        help_text="사용자가 관심있는 카테고리 목록"
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        verbose_name="생년월일",
        help_text="사용자의 생년월일 (나이 확인 목적)"
    )
    
    class Meta:
        verbose_name = "사용자 프로필"
        verbose_name_plural = "사용자 프로필들"
    
    def __str__(self):
        return f"{self.user.username}의 프로필" 


class StudyTaskProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="사용자")
    study_task = models.ForeignKey('StudyTask', on_delete=models.CASCADE, verbose_name="스터디 Task")
    progress = models.FloatField(default=0, verbose_name="진행율")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="업데이트 일시")

    class Meta:
        unique_together = ('user', 'study_task')
        verbose_name = "스터디 Task 진행율"
        verbose_name_plural = "스터디 Task 진행율들"

    def __str__(self):
        return f"{self.user} - {self.study_task} - {self.progress}%" 


class StudyProgressRecord(models.Model):
    """스터디 진행율 기록 모델"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="사용자")
    study = models.ForeignKey(Study, on_delete=models.CASCADE, verbose_name="스터디")
    overall_progress = models.FloatField(default=0, verbose_name="전체 진행율")
    task_progresses = models.JSONField(default=dict, verbose_name="Task별 진행율")
    recorded_at = models.DateTimeField(auto_now_add=True, verbose_name="기록 일시")
    page_type = models.CharField(max_length=50, verbose_name="페이지 타입")  # study-management, study-detail

    class Meta:
        verbose_name = "스터디 진행율 기록"
        verbose_name_plural = "스터디 진행율 기록들"
        ordering = ['-recorded_at']

    def __str__(self):
        study_title = self.study.title_ko if self.study.title_ko else self.study.title_en or '제목 없음'
        return f"{self.user.username} - {study_title} - {self.overall_progress}% ({self.recorded_at.strftime('%Y-%m-%d %H:%M')})" 


class IgnoredQuestion(models.Model):
    """무시된 문제 모델"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="사용자")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="문제")
    ignored_at = models.DateTimeField(auto_now_add=True, verbose_name="무시한 일시")

    class Meta:
        verbose_name = "무시된 문제"
        verbose_name_plural = "무시된 문제들"
        unique_together = ['user', 'question']  # 같은 사용자가 같은 문제를 중복 무시하지 않도록
        ordering = ['-ignored_at']

    def __str__(self):
        question_title = self.question.title_ko if self.question.title_ko else self.question.title_en or '제목 없음'
        return f"{self.user.username} - {question_title}"


class StudyJoinRequest(models.Model):
    """스터디 가입 요청 모델"""
    STATUS_CHOICES = [
        ('pending', '대기중'),
        ('approved', '승인됨'),
        ('rejected', '거절됨'),
    ]
    
    study = models.ForeignKey(Study, on_delete=models.CASCADE, related_name='join_requests', verbose_name="스터디")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="요청자")
    message = models.TextField(blank=True, null=True, verbose_name="요청 메시지")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="상태"
    )
    requested_at = models.DateTimeField(auto_now_add=True, verbose_name="요청일")
    responded_at = models.DateTimeField(null=True, blank=True, verbose_name="응답일")
    responded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='responded_join_requests',
        verbose_name="응답자"
    )
    
    class Meta:
        verbose_name = "스터디 가입 요청"
        verbose_name_plural = "스터디 가입 요청들"
        unique_together = ['study', 'user']  # 같은 스터디에 같은 사용자가 중복 요청하지 않도록
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['study', 'status']),
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        study_title = self.study.title_ko if self.study.title_ko else self.study.title_en or '제목 없음'
        return f"{self.user.username} - {study_title} ({self.get_status_display()})"


class AccuracyAdjustmentHistory(models.Model):
    """정확도 조정 이력 모델"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="사용자", db_index=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="문제", db_index=True)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, verbose_name="시험", db_index=True)
    adjustment_count = models.IntegerField(default=1, verbose_name="조정 횟수")
    total_adjustment_percentage = models.FloatField(default=10.0, verbose_name="총 조정 퍼센트")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")
    
    class Meta:
        verbose_name = "정확도 조정 이력"
        verbose_name_plural = "정확도 조정 이력들"
        unique_together = ['user', 'question', 'exam']  # 같은 사용자의 같은 문제-시험 조합에 대해 하나의 이력만 유지
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'question']),
            models.Index(fields=['user', 'exam']),
        ]
    
    def __str__(self):
        question_title = self.question.title_ko if self.question.title_ko else self.question.title_en or '제목 없음'
        return f"{self.user.username} - {question_title} - {self.total_adjustment_percentage}% 조정"


class ExamSubscription(models.Model):
    """시험 구독 모델"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="사용자", db_index=True)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, verbose_name="시험", db_index=True)
    subscribed_at = models.DateTimeField(auto_now_add=True, verbose_name="구독일")
    is_active = models.BooleanField(default=True, verbose_name="활성 상태")

    class Meta:
        verbose_name = "시험 구독"
        verbose_name_plural = "시험 구독들"
        unique_together = ['user', 'exam']
        ordering = ['-subscribed_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['exam', 'is_active']),
            models.Index(fields=['user', 'exam']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.exam.title_ko or self.exam.title_en or 'Unknown'}"


class ShortUrl(models.Model):
    """URL 단축 모델"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    short_code = models.CharField(max_length=10, unique=True, verbose_name="단축 코드", db_index=True)
    original_url = models.URLField(max_length=2000, verbose_name="원본 URL")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="생성자", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="만료일", help_text="만료일이 설정되면 해당 시간 이후 URL이 무효화됩니다")
    access_count = models.IntegerField(default=0, verbose_name="접근 횟수")
    last_accessed_at = models.DateTimeField(null=True, blank=True, verbose_name="마지막 접근일")

    class Meta:
        verbose_name = "단축 URL"
        verbose_name_plural = "단축 URL들"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['short_code']),
            models.Index(fields=['created_by', '-created_at']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.short_code} -> {self.original_url[:50]}..."

    def is_expired(self):
        """URL이 만료되었는지 확인"""
        if self.expires_at is None:
            return False
        from django.utils import timezone
        return timezone.now() > self.expires_at

    def increment_access_count(self):
        """접근 횟수 증가"""
        from django.utils import timezone
        self.access_count += 1
        self.last_accessed_at = timezone.now()
        self.save(update_fields=['access_count', 'last_accessed_at'])