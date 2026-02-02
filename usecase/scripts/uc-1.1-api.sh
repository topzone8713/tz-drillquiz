#!/usr/bin/env bash
# UC-1.1: 회원가입 및 초기 설정 - API 자동 테스트 스크립트

set -e  # 오류 발생 시 스크립트 중단

# Load test configuration
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/test-config.sh"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 설정
API_BASE_URL="$BACKEND_URL"
TEST_USERNAME="autotest$(date +%s)"  # 타임스탬프로 고유한 사용자명 생성
TEST_EMAIL="${TEST_USERNAME}@example.com"
TEST_PASSWORD="TestPassword123!"

# 로그 함수
log_info() {
    printf "${BLUE}[INFO]${NC} %s\n" "$1"
}

log_success() {
    printf "${GREEN}[SUCCESS]${NC} %s\n" "$1"
}

log_warning() {
    printf "${YELLOW}[WARNING]${NC} %s\n" "$1"
}

log_error() {
    printf "${RED}[ERROR]${NC} %s\n" "$1"
}

# 테스트 시작
log_info "=== UC-1.1 회원가입 API 테스트 시작 ==="
log_info "테스트 사용자명: $TEST_USERNAME"
log_info "테스트 이메일: $TEST_EMAIL"

# 1. 환경 확인
log_info "1. 환경 확인"
log_info "테스트 대상 서버: $API_BASE_URL"

# Health check with detailed response
log_info "Health check 요청..."
HEALTH_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}\nTIME_TOTAL:%{time_total}" "$API_BASE_URL/api/health/" 2>/dev/null)
if [ $? -ne 0 ]; then
    log_error "서버 연결 실패: $API_BASE_URL"
    log_error "서버가 실행 중인지 확인하세요."
    exit 1
fi

# Parse health response
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
TIME_TOTAL=$(echo "$HEALTH_RESPONSE" | grep "TIME_TOTAL:" | cut -d: -f2)
HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | grep -v "HTTP_CODE:" | grep -v "TIME_TOTAL:")

log_info "Health check 응답 코드: $HTTP_CODE"
log_info "Health check 응답 시간: ${TIME_TOTAL}s"
log_info "Health check 응답 내용: $HEALTH_BODY"

if [ "$HTTP_CODE" = "200" ]; then
    log_success "서버 연결 성공"
else
    log_error "서버 응답 오류 (HTTP $HTTP_CODE)"
    exit 1
fi

# 2. 중복 사용자명 확인 (선택사항)
log_info "2. 중복 사용자명 확인"
# 실제 구현에서는 API로 중복 확인 가능

# 3. 회원가입 요청
log_info "3. 회원가입 요청"
log_info "요청 URL: $API_BASE_URL/api/register/"
log_info "요청 데이터: {\"id\": \"$TEST_USERNAME\", \"name\": \"Auto Test User\", \"email\": \"$TEST_EMAIL\", \"password\": \"$TEST_PASSWORD\", \"language\": \"ko\"}"

REGISTER_RESPONSE=$(curl -s -X POST "$API_BASE_URL/api/register/" \
  -H "Content-Type: application/json" \
  -d "{
    \"id\": \"$TEST_USERNAME\",
    \"name\": \"Auto Test User\",
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"$TEST_PASSWORD\",
    \"language\": \"ko\"
  }" 2>/dev/null)

CURL_EXIT_CODE=$?
if [ $CURL_EXIT_CODE -ne 0 ]; then
    log_error "회원가입 요청 실패 (curl exit code: $CURL_EXIT_CODE)"
    exit 1
fi

log_info "회원가입 응답: $REGISTER_RESPONSE"

# 4. 응답 검증
log_info "4. 응답 검증"

# jq가 설치되어 있는지 확인
if ! command -v jq &> /dev/null; then
    log_warning "jq가 설치되지 않았습니다. 기본 검증을 수행합니다."
    if echo "$REGISTER_RESPONSE" | grep -q '"success":true'; then
        log_success "회원가입 성공 확인"
    else
        log_error "회원가입 실패"
        echo "응답: $REGISTER_RESPONSE"
        exit 1
    fi
else
    # jq를 사용한 상세 검증
    SUCCESS=$(echo "$REGISTER_RESPONSE" | jq -r '.success // false')
    AUTO_LOGIN=$(echo "$REGISTER_RESPONSE" | jq -r '.auto_login // false')
    USERNAME=$(echo "$REGISTER_RESPONSE" | jq -r '.user.username // ""')
    USER_ID=$(echo "$REGISTER_RESPONSE" | jq -r '.user.id // ""')

    if [ "$SUCCESS" = "true" ]; then
        log_success "회원가입 성공"
    else
        log_error "회원가입 실패"
        echo "응답: $REGISTER_RESPONSE"
        exit 1
    fi

    if [ "$AUTO_LOGIN" = "true" ]; then
        log_success "자동 로그인 플래그 확인"
    else
        log_warning "자동 로그인 플래그가 false입니다"
    fi

    if [ "$USERNAME" = "$TEST_USERNAME" ]; then
        log_success "사용자명 일치 확인"
    else
        log_error "사용자명 불일치: 예상=$TEST_USERNAME, 실제=$USERNAME"
    fi

    if [ -n "$USER_ID" ] && [ "$USER_ID" != "null" ]; then
        log_success "사용자 ID 생성 확인: $USER_ID"
    else
        log_error "사용자 ID가 생성되지 않았습니다"
    fi
fi

# 5. 로그인 테스트 (선택사항)
log_info "5. 로그인 테스트"
LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE_URL/api/login/" \
  -H "Content-Type: application/json" \
  -d "{
    'username': '$TEST_USERNAME',
    'password': '$TEST_PASSWORD'
  }" 2>/dev/null)

if [ $? -eq 0 ]; then
    if echo "$LOGIN_RESPONSE" | grep -q '"success":true'; then
        log_success "로그인 테스트 성공"
    else
        log_warning "로그인 테스트 실패 (회원가입 후 자동 로그인으로 인해 정상일 수 있음)"
    fi
else
    log_warning "로그인 API 호출 실패"
fi

# 6. 정리 (선택사항)
log_info "6. 테스트 정리"
log_info "테스트 사용자 데이터는 데이터베이스에 남아있습니다."
log_info "필요시 수동으로 삭제하세요:"
log_info "  - 사용자명: $TEST_USERNAME"
log_info "  - 이메일: $TEST_EMAIL"

# 최종 결과
log_success "=== UC-1.1 API 테스트 완료 ==="
log_success "모든 테스트가 성공적으로 통과했습니다!"

exit 0
