# DrillQuiz - 퀴즈 학습 플랫폼

## 🎯 프로젝트 소개

**DrillQuiz**는 효율적인 퀴즈 학습을 위한 온라인 플랫폼으로, 문제 풀이, 시험 관리, 학습 진도 추적을 통해 학습 효과를 극대화하는 웹 애플리케이션입니다.

### 핵심 목표
- 자주 틀리는 문제에 집중한 효율적인 학습
- 다국어 지원을 통한 글로벌 접근성
- 개인별 맞춤형 학습 경험 제공
- 스터디 그룹을 통한 협력 학습 환경 구축

---
 
## 🚀 주요 기능

### 📚 학습 관리
- **스마트 출제/풀기**: 필터된 문제들만으로 시험 출제 및 풀기
- **문제 무시 기능**: 개인별로 문제를 무시하여 틀린문제 계산에서 제외
- **즐겨찾기 시험**: 개인별 즐겨찾기 시험 생성 및 관리
- **학습 진행률 대시보드**: 시간별 진행률 추적 및 차트 시각화
- **일일 시험**: 구독한 시험에서 매일 새로운 문제 출제
- **랜덤 출제**: 설정된 문제 수만큼 랜덤 출제

### 🔧 관리 기능
- **공개/비공개 관리**: 시험, 스터디, 질문 파일의 공개 여부 설정
- **문제 그룹핑**: 문제별 그룹 ID 설정 및 일괄 관리
- **권한/역할 관리**: 관리자, 스터디 관리자, 일반 사용자 역할 구분
- **엑셀 업로드/다운로드**: 문제 및 사용자 데이터 일괄 관리

### 👥 사용자 지원
- **익명 사용자 지원**: 로그인하지 않은 사용자도 공개 시험/스터디 접근
- **Google OAuth 인증**: Google 계정을 통한 간편 로그인
- **사용자 시간대 처리**: 모든 날짜가 사용자의 로컬 시간대로 자동 변환
- **세션 관리**: 로그아웃 시 서버 세션 및 CSRF 토큰 완전 정리

### 🌐 다국어 지원
- **한국어/영어 지원**: 모든 콘텐츠의 다국어 지원
- **자동 번역**: OpenAI API를 통한 자동 번역 기능
- **실시간 언어 전환**: 사용자 인터페이스 실시간 언어 변경
- **번역 자동화**: Vue 파일에서 번역 키 자동 추출 및 Django 동기화

---

## 🚀 빠른 시작

### 1. 저장소 클론
```bash
git clone <repo-url>
cd drillquiz
```

### 2. 실행 방법

#### Docker 환경 (권장)
```bash
# PostgreSQL 모드로 시작
./start.sh docker

# 종료
./stop.sh docker
```

#### 로컬 환경
```bash
# 개발 모드로 시작 (기본값)
./start.sh

# 프로덕션 모드로 시작
./start.sh prod

# 종료
./stop.sh
```

### 3. 접속
- **프론트엔드**: http://localhost:8080 (개발) / https://us.drillquiz.com (운영)
- **백엔드 API**: http://localhost:8000 (개발) / https://us.drillquiz.com (운영)
- **Django 관리자**: http://localhost:8000/admin (admin/admin123)

---

## 🔧 Kubernetes 접근 (중요!)

**⚠️ kubectl 접근이 안 될 때 반드시 확인할 사항:**

### Kubeconfig 설정 (필수)
```bash
# Kubeconfig 파일 경로 설정
export KUBECONFIG=~/.kube/topzone.iptime.org.config

# 또는 백업 파일 사용
export KUBECONFIG=~/.kube/topzone.iptime.org.config.backup

# 설정 확인
kubectl config current-context
kubectl cluster-info
```

### 네임스페이스
- **운영 환경**: `devops`
- **개발 환경**: `devops-dev`

### 자주 사용하는 명령어
```bash
# Pod 목록 확인
kubectl get pods -n devops-dev

# 로그 확인
kubectl logs -n devops-dev -l app=drillquiz --tail=100

# 특정 API 로그 확인
kubectl logs -n devops-dev -l app=drillquiz --tail=500 | grep "/api/studies"
```

**📖 상세 가이드**: [운영 환경 디버깅 가이드](./docs/PRODUCTION_DEBUGGING_GUIDE.md)

---

## 📚 사용자 가이드

### 1. 문제 관리
1. **문제 파일 업로드**: Excel 또는 CSV 파일을 업로드하여 문제 등록
2. **문제 분류**: 난이도, 그룹 ID를 통한 문제 분류
3. **즐겨찾기**: 개인별 즐겨찾기 문제 관리
4. **무시 기능**: 개인별 문제 무시 설정

### 2. 시험 생성 및 풀이
1. **시험 생성**: 문제들을 조합하여 시험 생성
2. **스마트 출제**: 필터된 문제들만으로 시험 출제
3. **시험 풀이**: 실시간 채점 및 시간 측정
4. **재시험**: 틀린 문제만으로 재시험 생성

### 3. 스터디 그룹
1. **스터디 생성**: 다국어 제목 및 목표 설정
2. **멤버 관리**: 스터디 멤버 초대 및 역할 관리
3. **Task 기반 학습**: 시험을 Task로 연결하여 체계적 학습
4. **진행률 추적**: Task별 학습 진행률 자동 계산

### 4. 다국어 사용
1. **언어 설정**: 사용자 프로필에서 언어 설정
2. **자동 적용**: 로그인 시 설정된 언어로 자동 전환
3. **실시간 전환**: 상단 메뉴에서 언어 실시간 변경

---

## 🔧 개발자 가이드

### 기술 스택
- **Backend**: Python 3.12, Django 4.2.7, Django REST Framework 3.14.0
- **Authentication**: Google OAuth, Django REST Framework SimpleJWT (Access/Refresh 토큰 기반)
- **Frontend**: Vue.js 2.6.14, Bootstrap 5.3.2, Vue i18n 8.28.2
- **Database**: PostgreSQL 15 (운영), SQLite3 (개발)
- **Infrastructure**: Docker, Kubernetes, Jenkins CI/CD
- **Storage**: MinIO S3 호환 스토리지 (운영), 로컬 파일 시스템 (개발)
- **Cache**: Redis Cluster (운영), 로컬 메모리 캐시 (개발)

### 개발 환경 설정

#### 환경 변수
```bash
# 환경 구분
ENVIRONMENT=development  # development 또는 production

# Django 설정
DEBUG=True              # 개발 환경에서는 True, 운영에서는 False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# 서버 설정
DJANGO_HOST=localhost
DJANGO_PORT=8000
FRONTEND_HOST=localhost
FRONTEND_PORT=8080

# CORS 설정
CORS_ALLOWED_ORIGINS=http://localhost:8080,http://127.0.0.1:8080
CSRF_TRUSTED_ORIGINS=http://localhost:8080,http://127.0.0.1:8080

# MinIO Storage 설정 (Kubernetes 환경)
USE_MINIO=False
MINIO_ENDPOINT=http://minio.devops.svc.cluster.local:9000
MINIO_ACCESS_KEY=RqrGVqGHChA1dq8pg8uB
MINIO_SECRET_KEY=IqpQ6zPTYJnHjeWceCtxZG8m7hMn70JvKSL99uur
MINIO_BUCKET_NAME=drillquiz
```

### 개발 명령어
```bash
# 신규 의존성 설치 (첫 세팅 또는 requirements.txt 갱신 후)
pip install -r requirements.txt

# Django 서버
python manage.py runserver

# Vue.js 개발 서버
npm run serve:dev      # 개발 환경
npm run serve:prod     # 운영 환경

# Vue.js 빌드
npm run build:dev      # 개발 환경 빌드
npm run build:prod     # 운영 환경 빌드

# 번역 자동화
npm run i18n:extract   # Vue 파일에서 번역 키 추출
npm run i18n:compile   # Django 번역 메시지 컴파일
npm run i18n:sync      # 전체 번역 동기화 (추출 + 컴파일)
```

### 모바일 빌드
- **사전 준비**
  - Node.js 18 이상과 npm 설치
  - Capacitor CLI (`npm install @capacitor/cli --save-dev`)
  - Android SDK 및 JDK 17 (환경 변수 `ANDROID_SDK_ROOT` 설정)
  - iOS 빌드는 macOS + Xcode Command Line Tools 필요
- **Capacitor 플랫폼 동기화 및 웹 자산 빌드**
  ```bash
  ./ci/mobile-build.sh prepare
  ```
- **Android APK/AAB 생성 (Gradle 사용)**
  ```bash
  ANDROID_SDK_ROOT=/path/to/sdk ./ci/mobile-build.sh android
  # 또는 전체 파이프라인
  CAPACITOR_PLATFORMS=android ./ci/mobile-build.sh full
  ```
- **로컬 에뮬레이터에서 Django(HTTP) API 테스트**
  ```bash
  CAPACITOR_BUILD_MODE=debug \
  CAPACITOR_LOCAL_API=true \
  ./ci/mobile-build.sh full
  adb uninstall com.drillquiz.app
  adb install -r build/mobile/android/app-debug.apk
  ```
  `CAPACITOR_LOCAL_API=true` 설정 시 API 엔드포인트가 자동으로 `http://10.0.2.2:8000`에 맞춰지며, 안드로이드 네트워크 보안 설정도 허용됩니다.
- **iOS 프로젝트 패키징 (macOS)**
  ```bash
  CAPACITOR_PLATFORMS=ios ./ci/mobile-build.sh full
  # xcarchive 생성
  CAPACITOR_PLATFORMS=ios CAPACITOR_IOS_ARCHIVE=true ./ci/mobile-build.sh ios
  ```
- 생성된 산출물은 `build/mobile/` 디렉터리에 저장됩니다.

### 데이터베이스 관리

#### PostgreSQL 사용 (권장)
```bash
# Docker Compose로 PostgreSQL 실행
docker-compose up -d db
```

#### SQLite 사용 (개발용)
```bash
# settings.py에서 SQLite 설정으로 변경
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### 다국어 번역 자동화

#### 번역 시스템 구조
- **Vue.js**: `$t('key')` 함수로 번역 키 사용
- **Django**: `.po` 파일로 번역 관리
- **자동화**: Vue 파일에서 번역 키 자동 추출 및 Django 동기화

#### 번역 키 추가 방법
1. Vue 파일에서 `$t('new.key')` 형태로 번역 키 사용
2. `npm run i18n:sync` 실행하여 자동 추출
3. `locale/ko/LC_MESSAGES/django.po` 파일에서 번역 추가
4. `npm run i18n:compile` 실행하여 컴파일

### 환경 변수 우선순위

DrillQuiz는 커스텀 환경 변수 로더를 사용하여 Kubernetes 환경을 고려한 우선순위를 적용합니다:

#### 우선순위 (높음 → 낮음)
1. **Kubernetes Secret** (가장 높음)
2. **Kubernetes ConfigMap**
3. **시스템 환경 변수**
4. **.env 파일** (가장 낮음)

#### 사용법
```bash
# 로컬 개발 환경
cp env.example .env
# .env 파일 수정 후 사용

# 시스템 환경 변수로 오버라이드
export USE_MINIO=true
export MINIO_BUCKET_NAME=drillquiz-prod

# 디버깅 모드 활성화
export DEBUG_ENV_LOADER=true
```

---

## 🛠️ 유용한 명령어

### Docker 관리
```bash
# 컨테이너 상태 확인
docker-compose ps

# 컨테이너 재시작
docker-compose restart

# 컨테이너 중지
docker-compose down
```

### Django 관리
```bash
# 마이그레이션
python manage.py makemigrations
python manage.py migrate

# 관리자 계정 생성
python manage.py createsuperuser

# 통계 데이터 정리 (주의: 영구 삭제)
python clear_all_statistics.py
```

---

## 🎯 주요 사용 시나리오

### 1. 스마트 출제/풀기
1. 시험 상세 페이지에서 필터 적용 (난이도, 그룹 ID, 검색어 등)
2. "출제" 버튼 클릭 → 필터된 문제들만으로 새 시험 생성
3. "풀기" 버튼 클릭 → 필터된 문제들만으로 시험 시작
4. 시험 완료 후 원래 페이지로 자동 복귀

### 2. 익명 사용자 지원
- 로그인하지 않은 사용자도 공개 시험/스터디 접근 가능
- 공개 파일만 표시, 비공개 파일은 숨김
- 로그아웃 시 세션 완전 정리

### 3. 환경 분기
- 개발 환경: SQLite, 디버그 모드, 모든 CORS 허용
- 운영 환경: PostgreSQL, 보안 강화, 지정된 CORS만 허용

---

## 📊 통계 데이터 관리

### 통계 데이터 정리 이력
- **2025-08-13 23:16:50**: `clear_all_statistics.py` 스크립트로 모든 통계 데이터 삭제 완료
  - 시험 결과 및 상세 기록: 12개 삭제
  - 스터디 진행률 기록: 5개 삭제
  - Django 캐시 정리 및 데이터베이스 최적화 완료
  - 백업 파일: `statistics_backup_20250813_231650.txt`

### 통계 데이터 정리 스크립트
```bash
# 모든 통계 데이터 삭제 (확인 후 실행)
python clear_all_statistics.py

# 강제 삭제 (확인 없이 실행)
python clear_all_statistics.py --force
```

**주의사항**: 이 스크립트는 모든 통계 데이터를 영구적으로 삭제합니다. 실행 전 반드시 백업을 확인하세요.

---

## ✅ 최근 완료된 작업

### 2025-08-18 - 다국어 마이그레이션 완료 ✅
- **개발 환경**: 다국어 필드 정상 작동, 데이터 복구 완료
- **운영 환경**: 안전한 마이그레이션 가이드 준비 완료
- **데이터 복구**: 운영 데이터로 개발 환경 복원 후 정상 작동

### 2025-07-19 - 프로덕션 환경 설정 완료 ✅
- **프로덕션 환경 구축**: us.drillquiz.com 도메인에서 완벽 작동
- **CSRF 보안 설정**: Django 4.0 호환 CSRF_TRUSTED_ORIGINS 설정
- **네트워크 접근성**: 0.0.0.0 바인딩으로 외부 접근 지원
- **환경별 분기**: 개발/운영 환경에 따른 자동 설정 분기 완료

### 2025-07 - 환경 설정 및 하드코딩 제거 ✅
- **환경 분기 로직**: 개발/운영 환경에 따른 자동 설정 분기
- **하드코딩 제거**: localhost:8080, localhost:8000 등 하드코딩된 주소 완전 제거
- **환경 변수 관리**: Django, Vue.js 환경 변수 통합 관리
- **프로덕션 최적화**: 운영 환경에서 소스맵 비활성화 및 보안 강화

### 2025-07 - 문제 무시 기능 및 UI 개선 ✅
- **문제 무시 기능**: 개인별로 문제를 무시하여 틀린문제 계산에서 제외
- **스마트 다음문제 버튼**: 답변을 했을 때만 다음문제 버튼 활성화
- **무시 상태 토글**: 문제 풀기 화면에서 무시하기/무시해제 버튼 토글

### 2025-07 - 스마트 출제/풀기 기능 ✅
- **스마트 출제 기능**: 필터된 문제들만으로 시험 출제
- **스마트 풀기 기능**: 필터된 문제들만으로 시험 풀기
- **출제할 문제 수 자동 조정**: 화면에 표시된 문제 수에 맞춰 자동 조정

---

## 🚨 중요 알림

### 데이터베이스 마이그레이션 주의사항
**운영 환경 적용 시 주의**: 다국어 마이그레이션은 데이터 손실 위험이 있으므로 반드시 전체 데이터 백업 후 진행해야 합니다.

**상세 내용**: `TECHNICAL_SPEC.md` 파일의 운영 가이드 섹션을 참조하세요.

---

## 📞 지원 및 문의

### 문제 해결
- **FAQ**: 자주 묻는 질문 및 해결 방법
- **이슈 트래킹**: GitHub Issues를 통한 버그 리포트
- **문서**: 상세한 기술 문서는 `TECHNICAL_SPEC.md` 참조

### 기여 방법
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

**DrillQuiz**는 현대적인 웹 기술 스택을 활용하여 효율적인 퀴즈 학습 플랫폼을 제공합니다. 다국어 지원, 개인화된 학습 경험, 협력 학습 환경을 통해 사용자들의 학습 효과를 극대화하는 것을 목표로 합니다.

