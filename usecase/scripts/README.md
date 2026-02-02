# Use Case 자동화 테스트 스크립트

이 폴더는 DrillQuiz Use Case를 자동화하여 테스트하기 위한 스크립트들을 포함합니다.

## 🚀 환경 변수 지원

모든 테스트 스크립트는 이제 환경 변수를 지원하여 다양한 환경에서 실행할 수 있습니다:

### 환경 변수
- `BACKEND_URL` - 백엔드 서버 URL (기본값: http://localhost:8000)
- `FRONTEND_URL` - 프론트엔드 서버 URL (기본값: http://localhost:8080)
- `PROJECT_ROOT` - 프로젝트 루트 디렉토리 (기본값: /Users/dhong/workspaces/drillquiz)

### 사용법

#### 1. 로컬 개발 환경
```bash
./uc-all.sh
```

#### 2. Kubernetes 환경
```bash
# 개발 환경
./run-tests-jenkins.sh k8s-dev

# QA 환경
./run-tests-jenkins.sh k8s-qa

# 운영 환경
./run-tests-jenkins.sh k8s-prod
```

#### 3. 커스텀 환경
```bash
BACKEND_URL=http://my-backend:8080 FRONTEND_URL=http://my-frontend:3000 ./uc-all.sh
```

#### 4. Jenkins 파이프라인
```bash
# 환경별 실행
./run-tests-jenkins.sh local
./run-tests-jenkins.sh k8s-dev
./run-tests-jenkins.sh k8s-qa
./run-tests-jenkins.sh k8s-prod
./run-tests-jenkins.sh custom
```

자세한 내용은 `jenkins-example.sh`를 참조하세요.

## 스크립트 목록

### UC-1.1: 회원가입 및 초기 설정
- **파일**: `uc-1.1-api-test.sh`
- **설명**: 회원가입 API 자동 테스트
- **실행 방법**: `./uc-1.1-api-test.sh`

### UC-1.2: Google OAuth 로그인
- **파일**: `uc-1.2-oauth.sh`
- **설명**: Google OAuth 로그인 API 테스트
- **실행 방법**: `./uc-1.2-oauth.sh`

### UC-1.3: 프로필 관리
- **파일**: `uc-1.3-profile.sh`
- **설명**: 프로필 조회 및 수정 API 테스트
- **실행 방법**: `./uc-1.3-profile.sh`

### UC-1.4: 비밀번호 변경
- **파일**: `uc-1.4-password.sh`
- **설명**: 비밀번호 변경 API 테스트
- **실행 방법**: `./uc-1.4-password.sh`

### UC-1.5: 개인 정보 초기화
- **파일**: `uc-1.5-data-reset.sh`
- **설명**: 개인 학습 데이터 초기화 API 테스트
- **실행 방법**: `./uc-1.5-data-reset.sh`

### UC-1.6: 회원 탈퇴
- **파일**: `uc-1.6-withdrawal.sh`
- **설명**: 회원 탈퇴 API 테스트
- **실행 방법**: `./uc-1.6-withdrawal.sh`

### UC-2.1: 문제 파일 업로드
- **파일**: `uc-2.1-file-upload.sh`
- **설명**: CSV/Excel 파일 업로드 API 테스트
- **실행 방법**: `./uc-2.1-file-upload.sh`

### UC-2.2: 문제 파일 다운로드
- **파일**: `uc-2.2-file-download.sh`
- **설명**: 문제 파일 다운로드 API 테스트
- **실행 방법**: `./uc-2.2-file-download.sh`

### UC-3.1: 시험 생성
- **파일**: `uc-3.1-exam-creation.sh`
- **설명**: 시험 생성 API 테스트
- **실행 방법**: `./uc-3.1-exam-creation.sh`

### UC-3.2: 시험 풀기
- **파일**: `uc-3.2-exam-taking.sh`
- **설명**: 시험 풀기 API 테스트
- **실행 방법**: `./uc-3.2-exam-taking.sh`

### UC-3.3: 시험 결과 확인
- **파일**: `uc-3.3-exam-results.sh`
- **설명**: 시험 결과 조회 및 통계 API 테스트
- **실행 방법**: `./uc-3.3-exam-results.sh`

### UC-3.4: 오답 노트
- **파일**: `uc-3.4-wrong-notes.sh`
- **설명**: 오답 노트 관리 API 테스트
- **실행 방법**: `./uc-3.4-wrong-notes.sh`

### UC-4.1: 스터디 생성
- **파일**: `uc-4.1-study-creation.sh`
- **설명**: 스터디 그룹 생성 API 테스트
- **실행 방법**: `./uc-4.1-study-creation.sh`

### UC-4.2: 스터디 멤버 관리
- **파일**: `uc-4.2-study-members.sh`
- **설명**: 스터디 멤버 관리 API 테스트
- **실행 방법**: `./uc-4.2-study-members.sh`

### UC-4.3: 스터디 Task 관리
- **파일**: `uc-4.3-study-tasks.sh`
- **설명**: 스터디 Task 관리 API 테스트
- **실행 방법**: `./uc-4.3-study-tasks.sh`

### UC-5.1: Voice Mode 시험
- **파일**: `uc-5.1-voice-mode.sh`
- **설명**: Voice Mode 시험 API 테스트
- **실행 방법**: `./uc-5.1-voice-mode.sh`

### UC-5.2: AI Mock Interview
- **파일**: `uc-5.2-ai-mock-interview.sh`
- **설명**: AI Mock Interview API 테스트
- **실행 방법**: `./uc-5.2-ai-mock-interview.sh`

### UC-ALL: 전체 테스트 실행
- **파일**: `uc-all.sh`
- **설명**: 모든 Use Case 테스트를 순차적으로 실행
- **실행 방법**: `./uc-all.sh`
- **특징**: 
  - 모든 Use Case를 자동으로 순차 실행
  - 테스트 통과/실패 통계 제공
  - 실패한 테스트 목록 표시

## 실행 방법

### 사전 요구사항
1. **서버 실행**: Django 백엔드 서버가 `http://localhost:8000`에서 실행 중이어야 합니다.
2. **curl 설치**: HTTP 요청을 위해 curl이 필요합니다.
3. **jq 설치** (선택사항): JSON 응답 파싱을 위해 jq를 권장합니다.

```bash
# Ubuntu/Debian
sudo apt-get install curl jq

# macOS
brew install curl jq

# CentOS/RHEL
sudo yum install curl jq
```

### 스크립트 실행
```bash
# usecase/scripts 폴더로 이동
cd usecase/scripts

# UC-1.1 테스트 실행
./uc-1.1-api-test.sh
```

## 스크립트 기능

### UC-1.1 API 테스트 스크립트
- ✅ **환경 확인**: 서버 연결 상태 확인
- ✅ **회원가입 테스트**: 새로운 사용자 생성
- ✅ **응답 검증**: 성공/실패 및 데이터 검증
- ✅ **자동 로그인 확인**: auto_login 플래그 검증
- ✅ **로그인 테스트**: 생성된 계정으로 로그인 테스트
- ✅ **결과 보고**: 상세한 테스트 결과 출력

### 출력 예시
```
[INFO] === UC-1.1 회원가입 API 테스트 시작 ===
[INFO] 테스트 사용자명: autotest1696492800
[INFO] 테스트 이메일: autotest1696492800@example.com
[INFO] 1. 환경 확인
[SUCCESS] 서버 연결 성공
[INFO] 2. 중복 사용자명 확인
[INFO] 3. 회원가입 요청
[INFO] 회원가입 응답: {"success":true,"message":"회원가입이 완료되었습니다.","auto_login":true,"user":{"id":126,"username":"autotest1696492800",...}}
[INFO] 4. 응답 검증
[SUCCESS] 회원가입 성공
[SUCCESS] 자동 로그인 플래그 확인
[SUCCESS] 사용자명 일치 확인
[SUCCESS] 사용자 ID 생성 확인: 126
[INFO] 5. 로그인 테스트
[SUCCESS] 로그인 테스트 성공
[INFO] 6. 테스트 정리
[INFO] 테스트 사용자 데이터는 데이터베이스에 남아있습니다.
[SUCCESS] === UC-1.1 API 테스트 완료 ===
[SUCCESS] 모든 테스트가 성공적으로 통과했습니다!
```

## CI/CD 통합
### Jenkins Pipeline 예시
```groovy
pipeline {
    agent any
    stages {
        stage('Setup') {
            steps {
                sh 'pip install -r requirements.txt'
            }
        }
        stage('Start Server') {
            steps {
                sh 'python manage.py runserver &'
                sh 'sleep 10'
            }
        }
        stage('Run Tests') {
            steps {
                sh 'chmod +x usecase/scripts/*.sh'
                sh './usecase/scripts/uc-1.1-api-test.sh'
            }
        }
    }
}
```

## 새로운 스크립트 추가

새로운 Use Case 테스트 스크립트를 추가할 때는 다음 템플릿을 사용하세요:

```bash
#!/bin/bash
# UC-{번호}: {제목} - API 자동 테스트 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 설정
API_BASE_URL="http://localhost:8000"

# 로그 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 테스트 시작
log_info "=== UC-{번호} 테스트 시작 ==="

# 테스트 로직 구현

log_success "=== UC-{번호} 테스트 완료 ==="
```

## 문제 해결

### 일반적인 문제
1. **서버 연결 실패**: Django 서버가 실행 중인지 확인
2. **jq 명령어 없음**: jq를 설치하거나 스크립트에서 제거
3. **권한 오류**: `chmod +x` 명령으로 실행 권한 부여

### 디버깅
```bash
# 상세 출력으로 실행
bash -x ./uc-1.1-api-test.sh

# 특정 단계만 실행
curl -v http://localhost:8000/api/health/
```
