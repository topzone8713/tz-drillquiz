#!/usr/bin/env bash

# UC-1.2: Google OAuth 로그인 테스트
# 작성일: 2025-10-06
# 목적: Google OAuth 로그인 기능 테스트

# Load test configuration
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/test-config.sh" ]; then
    source "$SCRIPT_DIR/test-config.sh"
else
    echo "Error: test-config.sh not found"
    exit 1
fi

# 로깅 함수들
log_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

log_success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}

log_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

log_warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1"
}

# 테스트 결과 카운터
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_OPTIONAL_FAILED=0

# 간단한 테스트 실행 함수
run_simple_test() {
    local test_name="$1"
    local test_command="$2"
    
    log_info "실행 중: $test_name"
    
    if eval "$test_command" >/dev/null 2>&1; then
        log_success "통과: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "실패: $test_name"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    echo ""
}

# 선택적 테스트 실행 함수 (실패해도 전체 결과에 영향 없음)
run_optional_test() {
    local test_name="$1"
    local test_command="$2"
    
    log_info "실행 중: $test_name (선택적)"
    
    if eval "$test_command" >/dev/null 2>&1; then
        log_success "통과: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_warning "스킵: $test_name (선택적 테스트)"
        TESTS_OPTIONAL_FAILED=$((TESTS_OPTIONAL_FAILED + 1))
    fi
    echo ""
}


# 헤더 출력
echo "=========================================="
echo "  UC-1.2: Google OAuth 로그인 API 테스트"
echo "=========================================="
echo ""

# 1. 환경 확인
log_info "1. 환경 확인 시작"

# 서버 연결 확인
run_simple_test "Backend 서버 연결 확인" "curl -s $BACKEND_URL/api/health/ > /dev/null"
run_simple_test "Frontend 서버 연결 확인" "curl -s $FRONTEND_URL/ > /dev/null"

# 2. OAuth 설정 확인
log_info "2. OAuth 설정 확인"

# OAuth 엔드포인트 확인
run_simple_test "Google OAuth 시작 엔드포인트 확인" "curl -s -o /dev/null -w '%{http_code}' $BACKEND_URL/oauth/login/google/ | grep -q '200\\|302'"
run_simple_test "OAuth 콜백 엔드포인트 확인" "curl -s -o /dev/null -w '%{http_code}' $BACKEND_URL/oauth/callback/google/ | grep -q '200\\|400\\|405'"

# 3. OAuth 플로우 테스트 (시뮬레이션)
log_info "3. OAuth 플로우 시뮬레이션"

# OAuth 시작 요청 (리다이렉트 응답 확인)
run_simple_test "OAuth 시작 요청 테스트" "curl -s -I $BACKEND_URL/oauth/login/google/ | grep -q '302\\|Location'"

# 4. 인증 상태 확인 API
log_info "4. 인증 상태 확인 API 테스트"

# 비로그인 상태에서 인증 상태 확인
run_simple_test "비로그인 상태 인증 확인" "curl -s $BACKEND_URL/api/auth/status/ | grep -q 'authenticated.*false'"

# 5. CSRF 토큰 테스트
log_info "5. CSRF 토큰 테스트"

run_simple_test "CSRF 토큰 요청" "curl -s $BACKEND_URL/api/csrf-token/ | grep -q 'csrfToken'"

# 6. OAuth 관련 설정 확인
log_info "6. OAuth 관련 설정 확인"

# 기본적인 OAuth 엔드포인트 확인
run_simple_test "OAuth 엔드포인트 존재 확인" "curl -s -o /dev/null -w '%{http_code}' $BACKEND_URL/oauth/login/google/ | grep -q '200\\|302'"

# 7. 환경 변수 확인
log_info "7. 환경 변수 확인"

# Google OAuth 환경 변수가 설정되어 있는지 확인
if [ -n "$GOOGLE_OAUTH_CLIENT_ID" ] && [ -n "$GOOGLE_OAUTH_CLIENT_SECRET" ]; then
    log_success "Google OAuth 환경 변수 설정됨"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    log_warning "Google OAuth 환경 변수 누락"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# 8. 프론트엔드 OAuth 버튼 확인
log_info "8. 프론트엔드 OAuth 버튼 확인"

run_simple_test "로그인 페이지 OAuth 버튼 확인" "curl -s $FRONTEND_URL/ | grep -q 'google\\|oauth\\|login'"

# 테스트 결과 요약
echo "=========================================="
echo "  테스트 결과 요약"
echo "=========================================="
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    log_success "모든 테스트 통과 ($TESTS_PASSED 통과, $TESTS_FAILED 실패)"
else
    log_warning "일부 테스트 실패 ($TESTS_PASSED 통과, $TESTS_FAILED 실패)"
    
    echo ""
    echo "⚠️  다음 사항을 확인해주세요:"
    echo "   1. Google OAuth 클라이언트 ID/Secret 설정"
    echo "   2. OAuth 리다이렉트 URL 설정"
    echo "   3. Django OAuth 라이브러리 설치"
    echo "   4. 환경 변수 설정"
fi

echo ""
echo "=========================================="
echo "  테스트 완료"
echo "=========================================="

# 테스트 결과에 따른 종료 코드
if [ $TESTS_FAILED -eq 0 ]; then
    exit 0
else
    exit 1
fi