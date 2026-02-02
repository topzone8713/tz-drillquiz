# 카테고리 다국어 지원 계획

## 목표
TagCategory 모델에 스페인어(es)와 중국어(zh) 지원을 추가하여 4개 언어(ko, en, es, zh)를 모두 지원하도록 합니다.

## 현재 상태 분석

### 1. 모델 (TagCategory)
- ✅ `name_ko`, `name_en` 필드 존재
- ❌ `name_es`, `name_zh` 필드 없음
- ✅ `is_ko_complete`, `is_en_complete` 필드 존재
- ❌ `is_es_complete`, `is_zh_complete` 필드 없음
- ✅ `created_language` 필드 존재
- ⚠️ `__str__()`, `get_localized_name()`, `get_full_path()` 메서드에서 `name_es`, `name_zh`를 `hasattr()`로 체크하지만 실제 필드는 없음

### 2. 시리얼라이저 (TagCategorySerializer)
- ✅ `MultilingualSerializerMixin` 사용 중
- ✅ `multilingual_fields = ['name']` 설정됨
- ❌ `name_es`, `name_zh` 필드가 Meta.fields에 없음
- ❌ `is_es_complete`, `is_zh_complete` 필드가 Meta.fields에 없음
- ⚠️ `get_available_languages()` 메서드에서 es, zh를 체크하지 않음

### 3. 뷰 (TagCategoryViewSet)
- ❌ `perform_create()`, `perform_update()`에서 `MultilingualContentManager` 사용 안 함
- ⚠️ 자동 번역 기능이 작동하지 않음

## 구현 계획

### 단계 1: 모델 필드 추가
**파일**: `quiz/models.py`

1. **필드 추가**:
   ```python
   name_es = models.CharField(max_length=100, verbose_name='스페인어 카테고리명', blank=True)
   name_zh = models.CharField(max_length=100, verbose_name='중국어 카테고리명', blank=True)
   is_es_complete = models.BooleanField(default=False, verbose_name='스페인어 완성')
   is_zh_complete = models.BooleanField(default=False, verbose_name='중국어 완성')
   ```

2. **인덱스 추가** (Meta 클래스):
   ```python
   models.Index(fields=['name_es']),
   models.Index(fields=['name_zh']),
   ```

3. **save() 메서드 업데이트**:
   - `is_es_complete`, `is_zh_complete` 자동 업데이트 로직 추가

### 단계 2: 마이그레이션 파일 생성
**새 파일**: `quiz/migrations/XXXX_add_multilingual_fields_to_tagcategory.py`

1. 필드 추가 마이그레이션 생성
2. 기존 데이터의 기본값 설정 (빈 문자열)

### 단계 3: 시리얼라이저 업데이트
**파일**: `quiz/serializers.py`

1. **Meta.fields에 필드 추가**:
   ```python
   'name_es', 'name_zh', 'is_es_complete', 'is_zh_complete'
   ```

2. **get_available_languages() 메서드 업데이트**:
   ```python
   if obj.name_es:
       languages.append('es')
   if obj.name_zh:
       languages.append('zh')
   ```

### 단계 4: 뷰에 다국어 매니저 적용
**파일**: `quiz/views/tag_category_views.py`

1. **perform_create() 메서드 업데이트**:
   ```python
   from quiz.utils.multilingual_utils import MultilingualContentManager
   
   def perform_create(self, serializer):
       instance = serializer.save(created_by=self.request.user)
       
       # 다국어 콘텐츠 자동 처리
       manager = MultilingualContentManager(
           instance, 
           self.request.user,
           language_fields=['name']
       )
       manager.handle_multilingual_update()
       
       # 캐시 무효화
       self._invalidate_category_cache(instance)
   ```

2. **perform_update() 메서드 업데이트**:
   ```python
   def perform_update(self, serializer):
       instance = serializer.save()
       
       # 다국어 콘텐츠 자동 처리
       manager = MultilingualContentManager(
           instance,
           self.request.user,
           language_fields=['name']
       )
       manager.handle_multilingual_update()
       
       # 캐시 무효화
       self._invalidate_category_cache(instance)
   ```

### 단계 5: 모델 메서드 업데이트 (선택사항)
**파일**: `quiz/models.py`

- `__str__()`, `get_localized_name()`, `get_full_path()` 메서드는 이미 `hasattr()` 체크로 되어 있어서 필드만 추가하면 작동함
- 하지만 명시적으로 필드 존재 여부를 확인하도록 개선 가능

## 구현 순서

1. ✅ 모델 필드 추가 (`quiz/models.py`)
2. ✅ 마이그레이션 파일 생성
3. ✅ 시리얼라이저 업데이트 (`quiz/serializers.py`)
4. ✅ 뷰 업데이트 (`quiz/views/tag_category_views.py`)
5. ✅ 테스트 (로컬 환경)

## 검증 체크리스트

- [ ] 모델에 `name_es`, `name_zh`, `is_es_complete`, `is_zh_complete` 필드 추가됨
- [ ] 마이그레이션 파일 생성 및 실행 성공
- [ ] 시리얼라이저에서 새 필드들이 노출됨
- [ ] 카테고리 생성 시 자동 번역 작동 (ko → en, es, zh)
- [ ] 카테고리 수정 시 자동 번역 작동
- [ ] `get_localized_name()` 메서드가 es, zh 반환 가능
- [ ] `get_full_path()` 메서드가 es, zh 경로 반환 가능
- [ ] 기존 카테고리 데이터에 영향 없음

## 참고사항

1. **기존 코드 호환성**: 
   - `hasattr()` 체크를 사용하는 메서드들은 필드만 추가하면 자동으로 작동
   - 빈 문자열 기본값으로 기존 데이터에 영향 없음

2. **자동 번역 전략**:
   - 다른 모델들(Exam, Study)과 동일하게 BASE_LANGUAGE(영어) 기준
   - ko, es, zh로 생성 시 → en으로 자동 번역
   - en으로 생성 시 → 번역하지 않음

3. **완성도 체크**:
   - `is_es_complete`, `is_zh_complete`는 `name_es`, `name_zh` 필드가 비어있지 않으면 True
   - `save()` 메서드에서 자동 업데이트

