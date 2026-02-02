# 도메인 확장 가이드

이 문서는 새로운 도메인을 추가하는 방법을 설명합니다.

## 개요

현재 시스템은 `devops.drillquiz.com`과 `leetcode.drillquiz.com` 도메인을 지원합니다. 새로운 도메인을 추가하려면 다음 단계를 따르세요.

## 1. 도메인 설정 추가

`src/utils/domainUtils.js` 파일의 `DOMAIN_CONFIGS` 객체에 새로운 도메인 설정을 추가합니다:

```javascript
const DOMAIN_CONFIGS = {
  devops: {
    keyword: 'devops',
    tagName: 'DevOps',
    storageKey: 'devops_tag_id',
    localStorageKey: 'devops_default_tags',
    localStorageSetKey: 'devops_default_tags_set'
  },
  leetcode: {
    keyword: 'leetcode',
    tagName: 'LeetCode',
    storageKey: 'leetcode_tag_id',
    localStorageKey: 'leetcode_default_tags',
    localStorageSetKey: 'leetcode_default_tags_set'
  },
  // 새로운 도메인 추가
  python: {
    keyword: 'python',
    tagName: 'Python',
    storageKey: 'python_tag_id',
    localStorageKey: 'python_default_tags',
    localStorageSetKey: 'python_default_tags_set'
  }
}
```

### 설정 항목 설명

- `keyword`: 도메인에서 검색할 키워드 (예: 'python')
- `tagName`: 태그 이름 (예: 'Python')
- `storageKey`: sessionStorage에 저장할 키 (예: 'python_tag_id')
- `localStorageKey`: localStorage에 저장할 키 (예: 'python_default_tags')
- `localStorageSetKey`: localStorage 설정 플래그 키 (예: 'python_default_tags_set')

## 2. 백엔드 설정

### 2.1 Kubernetes 설정

`ci/k8s.yaml` 파일에 새로운 도메인을 추가합니다:

```yaml
ALLOWED_HOSTS: "localhost,127.0.0.1,devops.drillquiz.com,leetcode.drillquiz.com,python.drillquiz.com,DOMAIN_PLACEHOLDER"
CORS_ALLOWED_ORIGINS: "http://localhost:8080,https://devops.drillquiz.com,https://leetcode.drillquiz.com,https://python.drillquiz.com,https://DOMAIN_PLACEHOLDER"
```

### 2.2 OAuth2 설정

Google OAuth2 콜솔에서 새로운 도메인의 리다이렉트 URI를 추가합니다:

```
https://python.drillquiz.com/api/google-oauth/
```

## 3. 태그 생성

백엔드에서 새로운 태그를 생성합니다:

```python
# Django 관리자 또는 API를 통해 태그 생성
Tag.objects.create(
    name_ko='Python',
    name_en='Python',
    localized_name='Python'
)
```

## 4. DNS 설정

DNS에서 새로운 서브도메인을 설정합니다:

```
python.drillquiz.com -> 서버 IP
```

## 5. 테스트

### 5.1 도메인 감지 테스트

```javascript
// 브라우저 콘솔에서 테스트
import { getCurrentDomainTagInfo } from '@/utils/domainUtils'
console.log(getCurrentDomainTagInfo())
```

### 5.2 태그 필터링 테스트

1. `python.drillquiz.com`에 접속
2. 스터디 관리 페이지에서 Python 태그가 자동으로 적용되는지 확인
3. Python 태그가 제거되지 않는지 확인

## 6. 자동화된 처리

새로운 도메인이 추가되면 다음이 자동으로 처리됩니다:

- ✅ 도메인 감지
- ✅ 기본 태그 자동 적용
- ✅ 태그 필터링
- ✅ OAuth2 리다이렉트
- ✅ API 파라미터 자동 추가
- ✅ URL 쿼리 자동 추가

## 7. 범용 함수 사용

새로운 도메인을 추가한 후에는 범용 함수를 사용할 수 있습니다:

```javascript
import { 
  getCurrentDomainTagInfo,
  applyCurrentDomainTagFilter,
  addCurrentDomainTagParams,
  addCurrentDomainTagQuery
} from '@/utils/domainUtils'

// 현재 도메인 정보 가져오기
const domainInfo = getCurrentDomainTagInfo(availableTags)

// 태그 필터 적용
const filteredTags = applyCurrentDomainTagFilter(userSelectedTags, availableTags)

// API 파라미터에 태그 추가
const params = addCurrentDomainTagParams(new URLSearchParams(), userSelectedTags, availableTags)

// URL 쿼리에 태그 추가
const url = addCurrentDomainTagQuery('/api/studies/', userSelectedTags, availableTags)
```

## 8. 주의사항

1. **태그 이름 일관성**: `tagName`은 백엔드의 태그 이름과 정확히 일치해야 합니다.
2. **키워드 고유성**: `keyword`는 다른 도메인과 중복되지 않아야 합니다.
3. **Storage 키 고유성**: `storageKey`는 다른 도메인과 중복되지 않아야 합니다.
4. **테스트**: 새로운 도메인 추가 후 반드시 테스트를 수행하세요.

## 9. 예시: React 도메인 추가

```javascript
// 1. DOMAIN_CONFIGS에 추가
react: {
  keyword: 'react',
  tagName: 'React',
  storageKey: 'react_tag_id',
  localStorageKey: 'react_default_tags',
  localStorageSetKey: 'react_default_tags_set'
}

// 2. k8s.yaml에 추가
ALLOWED_HOSTS: "...,react.drillquiz.com,..."
CORS_ALLOWED_ORIGINS: "...,https://react.drillquiz.com,..."

// 3. 백엔드에서 React 태그 생성
// 4. DNS 설정: react.drillquiz.com
// 5. 테스트 완료
```

이제 `react.drillquiz.com`에 접속하면 자동으로 React 태그가 적용됩니다!
