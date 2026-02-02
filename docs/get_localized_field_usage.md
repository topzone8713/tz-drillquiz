# get_localized_field 함수 사용 가이드

## 개요

`get_localized_field`는 다국어 필드를 가진 객체에서 사용자 언어에 맞는 값을 반환하는 유틸리티 함수입니다.

## 위치

`quiz/utils/multilingual_utils.py`

## 함수 시그니처

```python
def get_localized_field(
    obj, 
    field_name: str, 
    user_language: str = None, 
    default_value: str = None
) -> str
```

## 파라미터

- `obj`: 다국어 필드를 가진 객체 (예: Exam, Question, Tag, Study, StudyTask 등)
- `field_name`: 필드 이름 (예: 'title', 'name', 'content', 'description')
- `user_language`: 사용자 언어 코드 ('ko', 'en', 'es', 'zh', 'ja'). None이면 `BASE_LANGUAGE` ('en') 사용
- `default_value`: 모든 언어 필드가 없을 때 반환할 기본값. None이면 필드명과 언어에 따라 자동 생성

## 반환값

사용자 언어에 맞는 필드 값 또는 fallback 값 (문자열)

## 사용 예시

### 1. Django Admin에서 사용

```python
from quiz.utils.multilingual_utils import get_localized_field
from quiz.admin import MultilingualAdminMixin

class QuestionAdmin(MultilingualAdminMixin, admin.ModelAdmin):
    def get_title(self, obj):
        """사용자 언어에 맞는 제목 반환"""
        user_language = self._get_user_language()
        return get_localized_field(obj, 'title', user_language)
    # short_description은 MultilingualAdminMixin에서 자동으로 다국어 처리됨
    # - 한국어: '제목'
    # - 영어: 'Title'
    # - 스페인어: 'Título'
    # - 중국어: '标题'
    # - 일본어: 'タイトル'
```

### 2. API View에서 사용

```python
from quiz.utils.multilingual_utils import get_localized_field, get_user_language

@api_view(['GET'])
def get_exam(request, exam_id):
    user_language = get_user_language(request)
    exam = Exam.objects.get(id=exam_id)
    
    # 제목 가져오기
    title = get_localized_field(exam, 'title', user_language)
    
    # 설명 가져오기
    description = get_localized_field(exam, 'description', user_language)
    
    return Response({
        'title': title,
        'description': description
    })
```

### 3. 커스텀 기본값 사용

```python
# 기본값을 명시적으로 지정
title = get_localized_field(exam, 'title', 'en', 'Custom Default')
```

### 4. 자동 기본값 사용 (권장)

```python
# default_value를 None으로 두면 필드명과 언어에 따라 자동 생성
# 'title' 필드의 경우:
# - 한국어: '제목 없음'
# - 영어: 'No Title'
# - 스페인어: 'Sin título'
# - 중국어: '无标题'
# - 일본어: 'タイトルなし'
title = get_localized_field(exam, 'title', user_language)
```

## 지원하는 필드명과 자동 기본값

| 필드명 | 한국어 | 영어 | 스페인어 | 중국어 | 일본어 |
|--------|--------|------|----------|--------|--------|
| `title` | 제목 없음 | No Title | Sin título | 无标题 | タイトルなし |
| `name` | 이름 없음 | No Name | Sin nombre | 无名称 | 名前なし |
| `content` | 내용 없음 | No Content | Sin contenido | 无内容 | コンテンツなし |
| `description` | 설명 없음 | No Description | Sin descripción | 无描述 | 説明なし |
| 기타 | 없음 | N/A | N/A | 无 | なし |

## Fallback 순서

각 언어별로 다음 순서로 fallback됩니다:

- **한국어 (ko)**: `field_ko` → `field_en` → `default_value`
- **영어 (en)**: `field_en` → `field_ko` → `default_value`
- **스페인어 (es)**: `field_es` → `field_en` → `field_ko` → `default_value`
- **중국어 (zh)**: `field_zh` → `field_en` → `field_ko` → `default_value`
- **일본어 (ja)**: `field_ja` → `field_en` → `field_ko` → `default_value`

## 주의사항

1. 객체는 반드시 `{field_name}_ko`, `{field_name}_en` 필드를 가져야 합니다.
2. 선택적 필드 (`{field_name}_es`, `{field_name}_zh`, `{field_name}_ja`)는 `getattr`로 안전하게 접근됩니다.
3. `user_language`가 None이면 기본값으로 'en'이 사용됩니다.
4. 모든 언어 필드가 없고 `default_value`도 None이면 필드명과 언어에 따라 자동으로 기본값이 생성됩니다.

## Django Admin search_fields 자동 생성

다국어 필드를 검색하려면 `get_multilingual_search_fields` 유틸 함수를 사용하세요:

```python
from quiz.utils.multilingual_utils import get_multilingual_search_fields

class QuestionAdmin(MultilingualAdminMixin, admin.ModelAdmin):
    search_fields = get_multilingual_search_fields(['title', 'content'])
    # 결과: ['title_ko', 'title_en', 'title_es', 'title_zh', 'title_ja', 
    #        'content_ko', 'content_en', 'content_es', 'content_zh', 'content_ja']
```

## Django Admin fieldsets fields 자동 생성

다국어 필드를 fieldsets에 포함하려면 `get_multilingual_fields` 유틸 함수를 사용하세요:

```python
from quiz.utils.multilingual_utils import get_multilingual_fields

class ExamAdmin(MultilingualAdminMixin, admin.ModelAdmin):
    fieldsets = [
        ('기본 정보', {
            'fields': get_multilingual_fields(['title', 'description'], ['total_questions'])
            # 결과: ('title_ko', 'title_en', 'title_es', 'title_zh', 'title_ja',
            #        'description_ko', 'description_en', 'description_es', 'description_zh', 'description_ja',
            #        'total_questions')
        }),
    ]
```

### get_multilingual_fields 함수

```python
def get_multilingual_fields(
    field_names: List[str], 
    other_fields: List[str] = None
) -> tuple
```

- `field_names`: 다국어 필드 이름 목록 (예: `['title', 'description']`)
- `other_fields`: 추가로 포함할 다른 필드 목록 (예: `['total_questions', 'created_by']`)
- 반환값: 모든 언어 필드와 다른 필드를 포함한 튜플

## 관련 함수

- `get_user_language(request_or_user)`: 사용자 언어 가져오기
- `get_localized_field(obj, field_name, user_language, default_value)`: 다국어 필드에서 사용자 언어에 맞는 값 반환
- `get_localized_admin_label(field_name, user_language)`: Django admin short_description을 위한 다국어 레이블 반환
- `get_multilingual_search_fields(field_names)`: Django admin search_fields 자동 생성
- `get_multilingual_fields(field_names, other_fields)`: Django admin fieldsets fields 자동 생성

## Django Admin short_description 자동 다국어 처리

`MultilingualAdminMixin`을 사용하면 `short_description`이 자동으로 사용자 언어에 맞게 설정됩니다:

```python
class QuestionAdmin(MultilingualAdminMixin, admin.ModelAdmin):
    def get_title(self, obj):
        user_language = self._get_user_language()
        return get_localized_field(obj, 'title', user_language)
    # short_description 설정 불필요 - MultilingualAdminMixin이 자동 처리
```

지원하는 메서드명과 필드명 매핑:
- `get_title` → `title`
- `get_name` → `name`
- `get_content` → `content`
- `get_description` → `description`

