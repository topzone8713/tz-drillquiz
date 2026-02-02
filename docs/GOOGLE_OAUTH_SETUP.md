# Google OAuth 설정 가이드

## 현재 사용 중인 설정

- **Client ID**: `195449497097-rf2f22ampv4imqb80fvibhr7oq5oc7km.apps.googleusercontent.com`
- **Redirect URI**: `https://us.drillquiz.com/api/google-oauth/`

## Google Cloud Console에서 확인해야 할 사항

### 1. 리디렉션 URI 등록

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. **APIs & Services** → **Credentials** 이동
3. OAuth 2.0 Client ID 클릭 (Client ID: `195449497097-rf2f22ampv4imqb80fvibhr7oq5oc7km`)
4. **Authorized redirect URIs** 섹션 확인
5. 다음 URI가 등록되어 있는지 확인:
   ```
   https://us.drillquiz.com/api/google-oauth/
   ```
6. 없다면 **+ ADD URI** 클릭하여 추가
7. **SAVE** 클릭

### 2. OAuth 동의 화면 확인

1. **APIs & Services** → **OAuth consent screen** 이동
2. 다음 항목 확인:
   - **App name**: DrillQuiz
   - **User support email**: 지원 이메일 설정
   - **Authorized domains**: `drillquiz.com` 추가
   - **Developer contact information**: 개발자 이메일 설정

### 3. 앱 타입 확인

- Credentials에서 클라이언트 ID 타입이 **"Web application"**인지 확인
- 모바일 앱이지만 리디렉션 URI는 웹 서버를 사용하므로 "Web application"이 맞습니다.

### 4. 오래된 도메인 제거

- `t1zone.net` 관련 리디렉션 URI가 있다면 제거하거나 유지
- 사용하지 않는 도메인은 제거하는 것이 좋습니다.

## 문제 해결

### Error 400: invalid_request

이 오류는 일반적으로 다음 중 하나의 문제입니다:
1. 리디렉션 URI가 Google Cloud Console에 등록되지 않음
2. 리디렉션 URI가 정확히 일치하지 않음 (대소문자, 슬래시 등)
3. OAuth 동의 화면 설정이 완료되지 않음
4. **앱이 "In production" 상태이지만 검증(verification)이 완료되지 않음** ⚠️

### 확인 방법

1. Google Cloud Console에서 리디렉션 URI 목록 확인
2. 앱에서 사용하는 리디렉션 URI와 정확히 일치하는지 확인
3. OAuth 동의 화면이 "Testing" 또는 "In production" 상태인지 확인
4. **"In production" 상태인 경우 검증 상태 확인** ⚠️

### "In production" 상태이지만 검증이 완료되지 않은 경우

**증상:**
- Publishing status가 "In production"으로 표시됨
- 하지만 "Your app requires verification" 경고가 표시됨
- Error 400: invalid_request 오류 발생

**해결 방법:**

#### 방법 1: Testing 모드로 전환 (빠른 해결)
1. OAuth consent screen → Audience 페이지
2. "Back to testing" 버튼 클릭 → "Confirm" 클릭
3. "Test users" 섹션에서 "+ ADD USERS" 클릭
4. 테스트할 Google 계정 이메일 추가
5. 테스트 사용자로 로그인하여 확인

#### 방법 2: 검증 완료 (장기 해결)
1. "Go to verification center" 또는 "Learn more" 버튼 클릭
2. 필요한 정보 입력:
   - **App information**: 앱 이름, 로고, 지원 이메일 등
   - **Scopes**: 요청하는 권한 (openid, email, profile 등)
   - **Test instructions**: 테스트 방법 설명
   - **Privacy policy URL**: 개인정보 처리방침 URL
   - **Terms of service URL**: 이용약관 URL (선택)
3. 검증 제출
4. Google 검토 완료 대기 (며칠~몇 주 소요 가능)

**참고:**
- 앱 로고를 업데이트하면 검증이 필요할 수 있습니다
- "Needs verification" 상태에서는 일반 사용자가 로그인할 수 없습니다
- 개발/테스트 중에는 Testing 모드 사용을 권장합니다

**권장사항:**
- 개발/테스트 중에는 "Testing" 모드 사용
- 프로덕션 배포 전에 검증 완료

## 테스트를 위한 우회 방법 (합법적)

### 방법 1: Testing 모드 사용 (가장 권장) ✅

**장점:**
- 즉시 사용 가능
- 검증 없이 테스트 가능
- Test users만 추가하면 됨

**단점:**
- Test users 목록에 추가된 계정만 사용 가능
- 프로덕션에서는 사용 불가

**절차:**
1. OAuth consent screen → Audience
2. "Back to testing" 클릭 → "Confirm"
3. "Test users" 섹션에서 "+ ADD USERS"
4. 테스트할 Google 계정 이메일 추가 (여러 개 추가 가능)
5. 추가한 계정으로 로그인 테스트

### 방법 2: 별도의 개발용 OAuth 클라이언트 생성 ✅

**장점:**
- 프로덕션 클라이언트와 분리
- Testing 모드로 설정 가능
- 프로덕션에 영향 없음

**절차:**
1. Google Cloud Console → APIs & Services → Credentials
2. "+ CREATE CREDENTIALS" → "OAuth client ID"
3. Application type: "Web application" 선택
4. Name: "DrillQuiz Dev" 또는 "DrillQuiz Test"
5. Authorized redirect URIs에 개발용 URI 추가:
   - `https://us-dev.drillquiz.com/api/google-oauth/`
   - 또는 `http://localhost:8000/api/google-oauth/` (로컬 개발용)
6. 생성된 Client ID를 개발 환경에서만 사용
7. OAuth consent screen을 Testing 모드로 설정
8. Test users 추가

**환경 변수 설정:**
```bash
# 개발 환경에서만 사용
GOOGLE_OAUTH_CLIENT_ID="개발용_클라이언트_ID"
VUE_APP_GOOGLE_CLIENT_ID="개발용_클라이언트_ID"
```

### 방법 3: 로컬 개발 환경에서 테스트 ✅

**장점:**
- 인터넷 연결만 있으면 테스트 가능
- 실제 Google OAuth 플로우 테스트 가능

**절차:**
1. 로컬에서 백엔드 서버 실행 (포트 8000)
2. 로컬에서 프론트엔드 서버 실행 (포트 8080)
3. Google Cloud Console에서 Authorized redirect URIs에 추가:
   - `http://localhost:8000/api/google-oauth/`
4. OAuth consent screen을 Testing 모드로 설정
5. Test users 추가
6. 로컬에서 테스트

### 방법 4: Mock/Stub 사용 (제한적) ⚠️

**장점:**
- Google OAuth 없이도 테스트 가능
- 빠른 개발/디버깅

**단점:**
- 실제 OAuth 플로우 테스트 불가
- 프로덕션 배포 전에 실제 OAuth 테스트 필요

**사용 시나리오:**
- UI 개발/테스트
- OAuth 외 기능 테스트
- 빠른 프로토타이핑

### ⚠️ 불가능한 방법

다음 방법들은 **작동하지 않거나 Google 정책 위반**입니다:
- ❌ User-Agent 변경
- ❌ Referer 헤더 조작
- ❌ 리다이렉트 URI 우회
- ❌ 검증 상태 우회
- ❌ 다른 도메인으로 우회

### 빠른 해결 (지금 바로)

**가장 빠른 방법:**
1. OAuth consent screen → Audience
2. "Back to testing" 클릭
3. Test users에 본인 계정 추가
4. 즉시 테스트 가능 ✅

## Testing 모드에서도 Error 400이 발생하는 경우

### 확인 사항

#### 1. 로그인하는 계정이 Test users 목록에 있는지 확인 ⚠️
- **중요**: 로그인하려는 Google 계정이 반드시 Test users 목록에 있어야 합니다
- Test users 목록에 없는 계정으로는 로그인할 수 없습니다
- 현재 Test users: `doohee323@gmail.com`, `yah8713@gmail.com`
- **해결**: 로그인하려는 계정을 Test users에 추가

#### 2. 리다이렉트 URI 정확히 일치하는지 확인 ⚠️
- Google Cloud Console의 Authorized redirect URIs와 정확히 일치해야 합니다
- 대소문자, 슬래시(/) 등이 정확히 일치해야 합니다
- 현재 사용 중: `https://us.drillquiz.com/api/google-oauth/`
- **확인**: Google Cloud Console에서 정확히 일치하는지 확인

#### 3. OAuth 요청 파라미터 확인
- `client_id`가 올바른지 확인
- `redirect_uri`가 정확히 인코딩되었는지 확인
- `scope`가 올바른지 확인 (openid email profile)

#### 4. 캐시 문제
- 브라우저/앱 캐시를 지워보세요
- iOS 앱을 재시작해보세요
- 브라우저에서 시크릿 모드로 테스트해보세요

#### 5. Google 정책 위반 가능성
- 모바일 앱에서 웹뷰를 통해 OAuth를 사용하는 것이 Google 정책을 위반할 수 있습니다
- **해결**: iOS 앱 타입의 OAuth 클라이언트를 별도로 생성하는 것을 고려

### 디버깅 방법

**1. OAuth 요청 URL 확인:**
앱 로그에서 다음을 확인:
```
🔍 [main.js] 생성된 Google OAuth URL: ...
🔍 [main.js] URL 파라미터 분석: ...
```

**2. Google Cloud Console에서 확인:**
- APIs & Services → Credentials → OAuth 2.0 Client ID
- Authorized redirect URIs에 정확히 일치하는 URI가 있는지 확인
- Client ID가 올바른지 확인

**3. Test users 확인:**
- OAuth consent screen → Test users
- 로그인하려는 계정이 목록에 있는지 확인
- 없다면 "+ ADD USERS"로 추가

### 추가 해결 방법

#### 방법 A: 별도의 개발용 OAuth 클라이언트 생성
1. Google Cloud Console → Credentials
2. "+ CREATE CREDENTIALS" → "OAuth client ID"
3. Application type: "Web application"
4. Name: "DrillQuiz Test"
5. Authorized redirect URIs: `https://us.drillquiz.com/api/google-oauth/`
6. 생성된 Client ID를 사용
7. OAuth consent screen을 Testing 모드로 설정
8. Test users 추가

#### 방법 B: iOS 앱 타입 클라이언트 생성 (권장)
모바일 앱의 경우 iOS 앱 타입 클라이언트를 사용하는 것이 더 적합할 수 있습니다:
1. Google Cloud Console → Credentials
2. "+ CREATE CREDENTIALS" → "OAuth client ID"
3. Application type: **"iOS"** 선택
4. Bundle ID 입력 (iOS 앱의 Bundle ID)
5. 생성된 Client ID 사용
6. 리다이렉트 URI는 여전히 웹 서버를 사용할 수 있음





