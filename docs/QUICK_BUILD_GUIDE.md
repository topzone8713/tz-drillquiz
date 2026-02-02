# 빠른 빌드 가이드 (코드 변경 반영)

> **이 문서는**: Vue 코드를 수정한 후 iOS 앱에 빠르게 반영하는 방법을 설명합니다.  
> **전체 프로세스**: 처음부터 전체 빌드 프로세스를 확인하려면 [iOS 빌드 및 배포 가이드](./IOS_BUILD_DEPLOY_GUIDE.md)를 참고하세요.

Vue 코드를 수정한 후 iOS 앱에 반영하는 방법입니다.

## ⚠️ 중요: 코드 변경 반영 프로세스

Vue 코드를 수정했다면 **반드시 다음 순서로 빌드해야 합니다**:

1. ✅ **Vue 앱 빌드** (`npm run build`)
2. ✅ **Capacitor 동기화** (`npx cap sync ios`)
3. ✅ **Xcode에서 빌드 및 재설치**

단순히 Xcode에서 빌드만 하면 **이전 빌드된 파일이 그대로 사용**됩니다!

---

## 🚀 빠른 빌드 명령어

### 전체 프로세스 (한 번에 실행)

```bash
cd /Users/dhong/workspaces/drillquiz

# Node.js 경로 설정 (필요시)
export PATH="$PATH:$HOME/.nvm/versions/node/v22.17.0/bin"

# 1. Vue 앱 빌드
echo "📦 Vue 앱 빌드 중..."
npm run build:dev  # 개발 환경 (디버그 로그 포함)
# 또는
npm run build:prod  # 프로덕션 환경

# 2. Capacitor 동기화
echo "🔄 Capacitor 동기화 중..."
npx cap sync ios

# 3. Xcode 열기
echo "🚀 Xcode 열기..."
open ios/App/App.xcworkspace
```

### 단계별 설명

#### 1단계: Vue 앱 빌드

```bash
# 개발 환경 빌드 (디버그 로그 포함, sessionStorage.debug 지원)
npm run build:dev

# 또는 프로덕션 빌드
npm run build:prod
```

**빌드 결과물**: `dist/` 디렉토리에 생성됩니다.

**차이점**:
- `build:dev`: 개발 환경 설정, 디버그 로그 활성화
- `build:prod`: 프로덕션 환경 설정, 최적화된 빌드

#### 2단계: Capacitor 동기화

```bash
npx cap sync ios
```

이 명령은:
- `dist/` 디렉토리의 빌드 파일을 `ios/App/App/public/`로 복사
- 네이티브 플러그인 동기화
- iOS 프로젝트 설정 업데이트

**⚠️ 중요**: 이 단계를 건너뛰면 Xcode에서 이전 빌드 파일을 사용합니다!

#### 3단계: Xcode에서 빌드

1. Xcode에서 프로젝트 열기:
   ```bash
   open ios/App/App.xcworkspace
   ```
   ⚠️ **주의**: `.xcodeproj`가 아닌 `.xcworkspace`를 열어야 합니다!

2. Xcode에서:
   - 상단 툴바에서 **디바이스 선택** (시뮬레이터 또는 연결된 기기)
   - **Product** → **Clean Build Folder** (⌘⇧K) - 선택사항이지만 권장
   - **Product** → **Run** (⌘R) 또는 재생 버튼 클릭

---

## 🔍 디버그 모드 활성화

빌드 후 Safari 인스펙터에서:

```javascript
// 디버그 모드 활성화
sessionStorage.setItem('debug', 'true')

// 페이지 새로고침
location.reload()
```

이제 `debugLog()`로 출력한 모든 로그가 콘솔에 표시됩니다.

---

## 📝 빌드 스크립트 (자동화)

빠른 빌드를 위한 스크립트:

```bash
#!/bin/bash
# quick-build.sh

cd /Users/dhong/workspaces/drillquiz

# Node.js 경로 설정
export PATH="$PATH:$HOME/.nvm/versions/node/v22.17.0/bin"

# 빌드 타입 선택 (기본: dev)
BUILD_TYPE=${1:-dev}

echo "📦 Vue 앱 빌드 중... (타입: $BUILD_TYPE)"
if [ "$BUILD_TYPE" = "prod" ]; then
  npm run build:prod
else
  npm run build:dev
fi

if [ $? -ne 0 ]; then
  echo "❌ 빌드 실패!"
  exit 1
fi

echo "🔄 Capacitor 동기화 중..."
npx cap sync ios

if [ $? -ne 0 ]; then
  echo "❌ Capacitor 동기화 실패!"
  exit 1
fi

echo "🚀 Xcode 열기..."
open ios/App/App.xcworkspace

echo "✅ 완료! Xcode에서 빌드 및 실행하세요."
```

사용법:
```bash
# 개발 환경 빌드
./quick-build.sh dev

# 프로덕션 빌드
./quick-build.sh prod
```

---

## ❓ 자주 묻는 질문

### Q: Vue 코드만 수정했는데 Xcode에서 빌드만 하면 안 되나요?

**A: 안 됩니다!** 

Vue 코드는 JavaScript로 작성되어 있지만, iOS 앱에 포함되려면:
1. Vue 앱을 빌드해서 `dist/` 디렉토리에 번들 파일 생성
2. Capacitor가 `dist/` 파일을 iOS 프로젝트로 복사
3. Xcode가 복사된 파일을 앱 번들에 포함

이 과정을 거쳐야 합니다.

### Q: `npm run build:dev`와 `build:prod`의 차이는?

**A:**
- **`build:dev`**: 개발 환경 설정
  - 디버그 로그 활성화
  - 소스맵 포함
  - 최적화 최소화 (빠른 빌드)
  
- **`build:prod`**: 프로덕션 환경 설정
  - 코드 최적화 및 압축
  - 소스맵 제외 (선택사항)
  - 환경 변수: `VUE_APP_API_HOST=us-dev.drillquiz.com`

### Q: 빌드 시간이 너무 오래 걸려요

**A:** 개발 중에는 `build:dev`를 사용하세요. 프로덕션 빌드보다 빠릅니다.

### Q: 빌드 후에도 변경사항이 반영되지 않아요

**A:** 다음을 확인하세요:
1. ✅ `npm run build`가 성공했는지 확인
2. ✅ `npx cap sync ios`가 성공했는지 확인
3. ✅ Xcode에서 **Clean Build Folder** (⌘⇧K) 실행
4. ✅ 앱을 완전히 종료하고 재설치

### Q: 디버그 로그가 안 보여요

**A:**
1. ✅ `build:dev`로 빌드했는지 확인
2. ✅ Safari 인스펙터에서 `sessionStorage.setItem('debug', 'true')` 설정
3. ✅ 페이지 새로고침
4. ✅ Safari 인스펙터 콘솔 필터 확인 (Warning/Log 레벨)

---

## 🔗 관련 문서

- [iOS 빌드 및 배포 가이드](./IOS_BUILD_DEPLOY_GUIDE.md) - 전체 빌드 프로세스 및 Voice Interview 테스트
- [Xcode 빌드 가이드](./XCODE_BUILD_GUIDE.md) - Xcode에서 빌드 결과 파일 생성 방법
- [IPA 설치 가이드](./IPA_INSTALL_GUIDE.md) - .ipa 파일을 다른 기기에 설치하는 방법
- [빌드 타입 비교](./BUILD_TYPES_COMPARISON.md) - dev vs prod 빌드 차이점
- [Safari 웹 인스펙터 가이드](./IOS_WEB_INSPECTOR_GUIDE.md) - 디버깅 가이드
- [로컬 테스트 가이드](./LOCAL_TEST_GUIDE_VOICE_INTERVIEW.md) - Voice Interview 로컬 테스트

