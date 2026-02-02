# 카테고리 다국어 번역 실행 가이드

## 방법 1: Django 관리 명령어 사용

터미널에서 다음 명령어를 실행합니다:

```bash
# 가상환경 활성화 (필요한 경우)
source venv/bin/activate  # 또는 사용하는 가상환경 경로

# 모든 카테고리 번역 실행
python manage.py translate_all_categories

# DRY RUN 모드 (실제 저장 없이 확인만)
python manage.py translate_all_categories --dry-run

# 기존 번역 덮어쓰기 (force 모드)
python manage.py translate_all_categories --force
```

## 방법 2: API 엔드포인트 사용

### API 호출

```bash
# 관리자 계정으로 로그인 후
curl -X POST http://localhost:8000/api/tag-categories/translate-all/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

### 또는 프론트엔드에서

```javascript
// Vue 컴포넌트에서
async translateAllCategories() {
  try {
    const response = await axios.post('/api/tag-categories/translate-all/');
    console.log('번역 완료:', response.data);
    alert(`번역 완료: ${response.data.translated}개 카테고리`);
  } catch (error) {
    console.error('번역 실패:', error);
  }
}
```

## 번역 로직

1. **영어 이름 기준**: `name_en` 필드에 값이 있으면 이를 기준으로 번역
2. **영어가 없는 경우**: `name_ko`가 있으면 한국어를 영어로 먼저 번역
3. **번역 대상 언어**: 
   - 스페인어 (`name_es`)
   - 중국어 (`name_zh`)
   - 일본어 (`name_ja`)
4. **기존 번역 보존**: 이미 번역이 있는 언어는 건너뜀 (force 모드 제외)

## 결과

번역 완료 후 다음과 같은 정보를 반환합니다:

- `total`: 총 카테고리 수
- `translated`: 번역이 완료된 카테고리 수
- `skipped`: 이미 번역이 완료되어 건너뛴 카테고리 수
- `errors`: 오류 발생 수
- `error_details`: 오류 상세 정보

