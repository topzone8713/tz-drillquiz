# 빌드 타입 비교: dev vs prod

## 📋 개요

`./ci/mobile.sh` 스크립트에서 사용하는 빌드 타입(`dev`와 `prod`)의 차이점을 설명합니다.

---

## 🔍 주요 차이점

### 1. 환경 변수 설정

#### `build:dev` (개발 빌드)
```bash
ENVIRONMENT=development VUE_APP_ENVIRONMENT=development vue-cli-service build
```

#### `build:prod` (프로덕션 빌드)
```bash
ENVIRONMENT=production VUE_APP_ENVIRONMENT=production \
VUE_APP_API_HOST=us-dev.drillquiz.com \
VUE_APP_API_PORT=443 \
VUE_APP_API_PROTOCOL=https \
vue-cli-service build
```

---

## 📊 상세 비교표

| 항목 | `dev` (개발) | `prod` (프로덕션) |
|------|-------------|------------------|
| **환경 변수** | `VUE_APP_ENVIRONMENT=development` | `VUE_APP_ENVIRONMENT=production` |
| **API 호스트** | `localhost` (기본값) | `us-dev.drillquiz.com` |
| **API 포트** | `8000` (기본값) | `443` |
| **API 프로토콜** | `http` (기본값) | `https` |
| **코드 최적화** | 최소 (빠른 빌드) | 최대 (압축, 트리 쉐이킹) |
| **소스맵** | 포함 (디버깅 용이) | 제외 또는 최소화 |
| **디버그 로그** | ✅ 활성화 | ⚠️ 제한적 (sessionStorage.debug 필요) |
| **빌드 시간** | 빠름 | 느림 (최적화 과정) |
| **번들 크기** | 큼 | 작음 (압축됨) |
| **용도** | 로컬 개발/테스트 | 실제 배포 |

---

## 🎯 각 빌드 타입의 특징

### `dev` 빌드 (개발 환경)

**장점:**
- ✅ 빠른 빌드 시간
- ✅ 디버그 로그 활성화 (`debugLog()` 작동)
- ✅ 소스맵 포함 (디버깅 용이)
- ✅ 개발 서버와 동일한 환경

**단점:**
- ❌ 번들 크기가 큼
- ❌ 최적화되지 않음
- ❌ 프로덕션 환경과 다를 수 있음

**사용 시나리오:**
- 로컬 개발 중 테스트
- 디버깅이 필요한 경우
- 빠른 반복 개발

**예시:**
```bash
./ci/mobile.sh dev ios build
```

---

### `prod` 빌드 (프로덕션 환경)

**장점:**
- ✅ 최적화된 코드 (압축, 트리 쉐이킹)
- ✅ 작은 번들 크기
- ✅ 프로덕션 API 서버 연결 (`us-dev.drillquiz.com`)
- ✅ HTTPS 프로토콜 사용

**단점:**
- ❌ 느린 빌드 시간
- ❌ 디버그 로그 제한적 (프로덕션 모드에서 비활성화)
- ❌ 소스맵 없음 (디버깅 어려움)

**사용 시나리오:**
- 실제 배포 전 최종 테스트
- 프로덕션 환경과 동일한 설정으로 테스트
- 앱스토어 제출용 빌드

**예시:**
```bash
./ci/mobile.sh prod ios build
```

---

## 🔧 환경 변수 상세

### 개발 빌드 (`dev`)

```javascript
// src/config/apiConfig.js에서 사용
const ENVIRONMENT = 'development'
const API_HOST = 'localhost'  // 기본값
const API_PORT = '8000'      // 기본값
const API_PROTOCOL = 'http'  // 기본값
```

### 프로덕션 빌드 (`prod`)

```javascript
// src/config/apiConfig.js에서 사용
const ENVIRONMENT = 'production'
const API_HOST = 'us-dev.drillquiz.com'  // 명시적 설정
const API_PORT = '443'                    // 명시적 설정
const API_PROTOCOL = 'https'              // 명시적 설정
```

---

## 🐛 디버그 로그 동작

### `dev` 빌드
```javascript
// debugUtils.js
const isProduction = false  // process.env.NODE_ENV === 'development'

export function debugLog(message, data = null, level = 'log') {
  // 프로덕션 체크 없음 → 항상 sessionStorage.debug만 확인
  if (!isDebugMode()) return
  
  console.log(`🔍 [${timestamp}]`, message, data)
}
```

**결과:** `sessionStorage.setItem('debug', 'true')` 설정 시 모든 로그 출력

### `prod` 빌드
```javascript
// debugUtils.js
const isProduction = true  // process.env.NODE_ENV === 'production'

export function debugLog(message, data = null, level = 'log') {
  // 프로덕션 체크 제거됨 (최근 수정)
  // 하지만 여전히 sessionStorage.debug 확인 필요
  if (!isDebugMode()) return
  
  console.log(`🔍 [${timestamp}]`, message, data)
}
```

**결과:** `sessionStorage.setItem('debug', 'true')` 설정 시 로그 출력 (최근 수정으로 가능)

---

## 📦 빌드 결과물

### `dev` 빌드
```
dist/
├── js/
│   ├── app.xxxxx.js        (큼, 압축 안됨)
│   └── chunk-vendors.xxxxx.js
├── css/
│   └── app.xxxxx.css
└── index.html
```

### `prod` 빌드
```
dist/
├── js/
│   ├── app.xxxxx.js        (작음, 압축됨)
│   └── chunk-vendors.xxxxx.js
├── css/
│   └── app.xxxxx.css
└── index.html
```

---

## 🎯 언제 어떤 빌드를 사용할까?

### `dev` 빌드 사용 권장:
- ✅ 코드 변경 후 빠른 테스트
- ✅ 디버깅이 필요한 경우
- ✅ 로컬 개발 서버와 동일한 환경으로 테스트
- ✅ Voice Interview 기능 개발/테스트 중

### `prod` 빌드 사용 권장:
- ✅ 최종 배포 전 테스트
- ✅ 프로덕션 API 서버와 연결 테스트
- ✅ 앱스토어 제출용 빌드
- ✅ 성능 테스트

---

## 💡 실전 팁

### 1. 개발 중에는 `dev` 빌드 사용
```bash
# 빠른 반복 개발
./ci/mobile.sh dev ios build
```

### 2. 배포 전에는 `prod` 빌드로 최종 확인
```bash
# 프로덕션 환경 테스트
./ci/mobile.sh prod ios build
```

### 3. 디버그 로그 활성화 (둘 다 가능)
```javascript
// Safari 인스펙터 콘솔에서
sessionStorage.setItem('debug', 'true')
location.reload()
```

---

## 🔗 관련 문서

- [빠른 빌드 가이드](./QUICK_BUILD_GUIDE.md) - Vue 코드 변경 후 빠르게 반영하는 방법
- [iOS 빌드 및 배포 가이드](./IOS_BUILD_DEPLOY_GUIDE.md) - 전체 빌드 프로세스 및 Voice Interview 테스트
- [Xcode 빌드 가이드](./XCODE_BUILD_GUIDE.md) - Xcode에서 빌드 결과 파일 생성 방법
- [로컬 테스트 가이드](./LOCAL_TEST_GUIDE_VOICE_INTERVIEW.md) - Voice Interview 로컬 테스트

