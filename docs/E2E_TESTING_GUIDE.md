# E2E 테스트 가이드

Playwright를 사용한 E2E 테스트 환경이 구축되었습니다.

## 변경 사항

### 제거된 항목
- ❌ Cypress (`cypress`, `@vue/cli-plugin-e2e-cypress`)
- ❌ 기존 Cypress 테스트 파일들

### 추가된 항목
- ✅ Playwright (`@playwright/test`)
- ✅ E2E 테스트 구조 (`tests/e2e/`)
- ✅ 인증 테스트 케이스
- ✅ Jenkins 통합

## 설치

```bash
# Playwright 설치
npm install -D @playwright/test

# 브라우저 설치 (로컬 개발)
npx playwright install

# 브라우저 의존성 포함 설치 (CI/CD)
npx playwright install --with-deps chromium
```

## 테스트 실행

### 로컬 개발

```bash
# 모든 E2E 테스트 실행
npm run test:e2e

# UI 모드 (대화형)
npm run test:e2e:ui

# 헤드 모드 (브라우저 표시)
npm run test:e2e:headed

# 디버그 모드
npm run test:e2e:debug

# 인증 테스트만 실행
npm run test:e2e:auth

# 리포트 보기
npm run test:e2e:report
```

### Jenkins에서 실행

1. Jenkins 파이프라인에서 `E2E_TEST_YN=true` 환경 변수 설정
2. 파이프라인 실행 시 "Run E2E Tests" 스테이지가 자동 실행됨
3. 테스트 리포트는 Jenkins 아티팩트로 저장됨

## 테스트 구조

```
tests/e2e/
├── usecases/                    # 유스케이스별 테스트
│   └── 01-authentication.spec.js
├── helpers/                     # 헬퍼 함수
│   ├── api.js                  # API 클라이언트
│   ├── auth.js                 # 인증 헬퍼
│   ├── data-cleanup.js         # 데이터 정리
│   └── batch-runner.js         # 배치 실행
├── fixtures/                    # 테스트 데이터
│   └── users.json
└── README.md
```

## 인증 테스트

인증 테스트는 다음 시나리오를 포함합니다:

1. ✅ 로그인 페이지 접근 및 UI 확인
2. ✅ 유효한 자격증명으로 로그인 성공 (API)
3. ✅ UI를 통한 로그인 성공
4. ✅ 잘못된 자격증명으로 로그인 실패
5. ✅ API를 통한 로그아웃
6. ✅ 인증 상태 확인
7. ✅ 프로필 조회 (인증 필요)
8. ✅ 보호된 페이지 접근 시 리다이렉트

## 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `PLAYWRIGHT_BASE_URL` | 프론트엔드 URL | `http://localhost:8080` |
| `PLAYWRIGHT_API_URL` | 백엔드 API URL | `http://localhost:8000/api` |
| `TEST_USERNAME` | 테스트 사용자명 | `admin` |
| `TEST_PASSWORD` | 테스트 비밀번호 | `password` |
| `E2E_TEST_YN` | Jenkins에서 E2E 테스트 실행 여부 | `false` |

## 테스트 사용자 생성

테스트 실행 전 테스트 사용자가 필요합니다:

```bash
cd backend && source venv/bin/activate
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_user('admin', 'admin@example.com', 'password')
    print('Created admin user')
"
```

## API 엔드포인트

테스트에서 사용하는 주요 API 엔드포인트:

| 엔드포인트 | 설명 |
|-----------|------|
| `/api/auth/login/` | 로그인 |
| `/api/auth/register/` | 회원가입 |
| `/api/auth/logout/` | 로그아웃 |
| `/api/auth/profile/` | 프로필 조회 |
| `/api/auth/token/refresh/` | 토큰 갱신 |
| `/api/todos/` | Todo CRUD |

## 헬퍼 함수 사용법

### API 클라이언트

```javascript
const { ApiClient } = require('../helpers/api');

const apiClient = new ApiClient(process.env.PLAYWRIGHT_API_URL);
const response = await apiClient.get('/endpoint/');
const data = await response.json();
```

### 인증

```javascript
const { login, logout } = require('../helpers/auth');

// 로그인
await login(page, apiClient, 'username', 'password');

// 로그아웃
await logout(page, apiClient);
```

### 데이터 정리

```javascript
const { cleanupTestData, resetTestEnvironment } = require('../helpers/data-cleanup');

// 테스트 환경 초기화
await resetTestEnvironment();

// 특정 데이터 정리
await cleanupTestData('user', [userId]);
```

### 배치 실행

```javascript
const { runBatch } = require('../helpers/batch-runner');

// 배치 실행
await runBatch('check_recommendation_achievements', {
  timeout: 120000,
});
```

## 새로운 테스트 추가

### 1. 테스트 파일 생성

```javascript
// tests/e2e/usecases/02-my-usecase.spec.js
const { test, expect } = require('@playwright/test');
const { ApiClient } = require('../helpers/api');
const { login } = require('../helpers/auth');

test.describe('My Use Case', () => {
  let apiClient;

  test.beforeEach(async ({ page }) => {
    apiClient = new ApiClient(process.env.PLAYWRIGHT_API_URL);
    await login(page, apiClient, 'admin', 'password');
  });

  test('should do something', async ({ page }) => {
    await page.goto('/my-page');
    // 테스트 코드
  });

  test.afterEach(async () => {
    await apiClient.dispose();
  });
});
```

### 2. package.json에 스크립트 추가 (선택사항)

```json
{
  "scripts": {
    "test:e2e:my-usecase": "playwright test tests/e2e/usecases/02-my-usecase.spec.js"
  }
}
```

## 리포트

테스트 실행 후 리포트는 다음 위치에 생성됩니다:

- **HTML 리포트**: `test-results/html-report/index.html`
- **JSON 리포트**: `test-results/results.json`
- **JUnit 리포트**: `test-results/junit.xml` (CI/CD 통합용)

Jenkins에서는 자동으로 HTML 리포트가 퍼블리시됩니다.

## 문제 해결

### 브라우저 설치 실패

```bash
# 의존성 포함 설치
npx playwright install --with-deps chromium
```

### 테스트 실패

1. 서버가 실행 중인지 확인
   ```bash
   # 프론트엔드
   npm run serve

   # 백엔드 (backend 디렉토리에서)
   cd backend && source venv/bin/activate && python manage.py runserver
   ```

2. 환경 변수 확인
   ```bash
   echo $PLAYWRIGHT_BASE_URL
   echo $PLAYWRIGHT_API_URL
   ```

3. 테스트 로그 확인
   - `test-results/` 디렉토리 확인
   - 스크린샷 및 비디오 확인

### Jenkins에서 실패

1. Node.js 버전 확인 (18 이상 권장)
2. 브라우저 의존성 설치 확인
3. 서버 접근 가능 여부 확인 (Kubernetes 내부 네트워크)

## 다음 단계

다음 유스케이스 테스트를 추가할 수 있습니다:

- [ ] Todo CRUD 테스트 (생성, 조회, 수정, 삭제, 완료 표시)
- [ ] 알림 설정 테스트
- [ ] 사용자 프로필 테스트

## 참고 자료

- [Playwright 공식 문서](https://playwright.dev/)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [테스트 작성 가이드](tests/e2e/README.md)












