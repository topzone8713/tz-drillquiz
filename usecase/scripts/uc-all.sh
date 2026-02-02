#!/usr/bin/env bash

# UC-ALL: 모든 Use Case 테스트 실행 스크립트
# 작성일: 2025-10-05
# 목적: 모든 Use Case 테스트를 순차적으로 실행

# set -e  # 오류 발생 시 스크립트 종료 (선택적) - 주석 처리
# 테스트 실행 모드 설정
STOP_ON_FIRST_FAILURE=${STOP_ON_FIRST_FAILURE:-false}  # 첫 번째 실패 시 중단 여부

# Load test configuration
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/test-config.sh" ]; then
    source "$SCRIPT_DIR/test-config.sh"
elif [ -f "./usecase/scripts/test-config.sh" ]; then
    source "./usecase/scripts/test-config.sh"
elif [ -f "test-config.sh" ]; then
    source "test-config.sh"
else
    echo "Warning: test-config.sh not found, using defaults"
    export BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
    export FRONTEND_URL="${FRONTEND_URL:-http://localhost:8080}"
    export PROJECT_ROOT="${PROJECT_ROOT:-/Users/dhong/workspaces/drillquiz}"
fi

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

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

log_header() {
    echo ""
    printf "${CYAN}==========================================\n"
    printf "  %s\n" "$1"
    printf "==========================================${NC}\n"
    echo ""
}

# 테스트 결과 추적
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
FAILED_TEST_NAMES=""  # POSIX sh에서는 문자열로 관리

# 스크립트 디렉토리로 이동
cd "$(dirname "$0")"

# 헤더 출력
log_header "DrillQuiz - 모든 Use Case 테스트 실행"

log_info "시작 시간: $(date '+%Y-%m-%d %H:%M:%S')"

# 실행 모드 정보 출력 (Build #9 테스트)
if [ "$STOP_ON_FIRST_FAILURE" = "true" ]; then
    log_info "🛑 실행 모드: 첫 번째 실패 시 중단"
else
    log_info "🔄 실행 모드: 모든 테스트 계속 실행"
fi

echo ""

# 테스트 실행 함수
run_use_case_test() {
    test_name="$1"
    test_script="$2"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    log_header "$test_name"
    
    if [ -f "$test_script" ]; then
        # OAuth 테스트는 외부 연동이므로 실패해도 중단하지 않음
        is_oauth_test=false
        if [[ "$test_name" == *"OAuth"* ]] || [[ "$test_script" == *"oauth"* ]]; then
            is_oauth_test=true
            log_info "🔗 OAuth 테스트 (외부 연동): 실패해도 중단하지 않음"
        fi
        
        # Use bash if available, otherwise fallback to sh
        if command -v bash >/dev/null 2>&1; then
            if bash "$test_script"; then
                log_success "✅ $test_name 테스트 통과"
                PASSED_TESTS=$((PASSED_TESTS + 1))
            else
                if [ "$is_oauth_test" = true ]; then
                    log_warning "⚠️  $test_name 테스트 실패 (OAuth 외부 연동 - 계속 진행)"
                    FAILED_TESTS=$((FAILED_TESTS + 1))
                    FAILED_TEST_NAMES="$FAILED_TEST_NAMES$test_name (OAuth 외부 연동) "
                else
                    log_error "❌ $test_name 테스트 실패"
                    FAILED_TESTS=$((FAILED_TESTS + 1))
                    FAILED_TEST_NAMES="$FAILED_TEST_NAMES$test_name "
                    
                    # 첫 번째 실패 시 중단 모드인 경우 전체 테스트 중단 (OAuth 제외)
                    if [ "$STOP_ON_FIRST_FAILURE" = "true" ]; then
                        log_error "🛑 첫 번째 실패 시 중단 모드: 전체 테스트 중단"
                        exit 1
                    fi
                fi
            fi
        else
            if sh "$test_script"; then
                log_success "✅ $test_name 테스트 통과"
                PASSED_TESTS=$((PASSED_TESTS + 1))
            else
                if [ "$is_oauth_test" = true ]; then
                    log_warning "⚠️  $test_name 테스트 실패 (OAuth 외부 연동 - 계속 진행)"
                    FAILED_TESTS=$((FAILED_TESTS + 1))
                    FAILED_TEST_NAMES="$FAILED_TEST_NAMES$test_name (OAuth 외부 연동) "
                else
                    log_error "❌ $test_name 테스트 실패"
                    FAILED_TESTS=$((FAILED_TESTS + 1))
                    FAILED_TEST_NAMES="$FAILED_TEST_NAMES$test_name "
                    
                    # 첫 번째 실패 시 중단 모드인 경우 전체 테스트 중단 (OAuth 제외)
                    if [ "$STOP_ON_FIRST_FAILURE" = "true" ]; then
                        log_error "🛑 첫 번째 실패 시 중단 모드: 전체 테스트 중단"
                        exit 1
                    fi
                fi
            fi
        fi
    else
        log_warning "⚠️  $test_name 스크립트 없음: $test_script"
        ((FAILED_TESTS++))
        FAILED_TEST_NAMES="$FAILED_TEST_NAMES$test_name (스크립트 없음) "
    fi
    
    echo ""
    sleep 2  # 각 테스트 사이에 2초 대기
}

# UC-1: 사용자 관리
log_info "🔹 UC-1: 사용자 관리 테스트 시작"
run_use_case_test "UC-1.1: 회원가입 및 초기 설정" "./uc-1.1-api.sh"
run_use_case_test "UC-1.2: Google OAuth 로그인" "./uc-1.2-oauth.sh"
run_use_case_test "UC-1.3: 프로필 관리" "./uc-1.3-profile.sh"
run_use_case_test "UC-1.4: 비밀번호 변경" "./uc-1.4-password.sh"
run_use_case_test "UC-1.5: 개인 정보 초기화" "./uc-1.5-data-reset.sh"
run_use_case_test "UC-1.6: 회원 탈퇴" "./uc-1.6-withdrawal.sh"

# UC-2: 문제 관리
log_info "🔹 UC-2: 문제 관리 테스트 시작"
run_use_case_test "UC-2.1: 문제 파일 업로드" "./uc-2.1-file-upload.sh"
run_use_case_test "UC-2.2: 문제 파일 다운로드" "./uc-2.2-file-download.sh"

# UC-3: 시험 기능
log_info "🔹 UC-3: 시험 기능 테스트 시작"
run_use_case_test "UC-3.1: 시험 생성" "./uc-3.1-exam-creation.sh"
run_use_case_test "UC-3.2: 시험 풀기" "./uc-3.2-exam-taking.sh"
run_use_case_test "UC-3.3: 시험 결과 확인" "./uc-3.3-exam-results.sh"
run_use_case_test "UC-3.4: 오답 노트" "./uc-3.4-wrong-notes.sh"

# UC-4: 스터디 기능
log_info "🔹 UC-4: 스터디 기능 테스트 시작"
run_use_case_test "UC-4.1: 스터디 생성" "./uc-4.1-study-creation.sh"
run_use_case_test "UC-4.2: 스터디 멤버 관리" "./uc-4.2-study-members.sh"
run_use_case_test "UC-4.3: 스터디 Task 관리" "./uc-4.3-study-tasks.sh"

# UC-5: 고급 기능
log_info "🔹 UC-5: 고급 기능 테스트 시작"
run_use_case_test "UC-5.1: Voice Mode 시험" "./uc-5.1-voice-mode.sh"
run_use_case_test "UC-5.2: AI Mock Interview" "./uc-5.2-ai-mock-interview.sh"

# 종합 결과
log_header "종합 테스트 결과"

log_info "종료 시간: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    log_success "🎉 모든 테스트 통과! ($PASSED_TESTS/$TOTAL_TESTS)"
    echo ""
    echo "✅ DrillQuiz 시스템이 올바르게 작동하고 있습니다."
    echo "✅ 모든 Use Case가 성공적으로 검증되었습니다."
else
    log_warning "⚠️  일부 테스트 실패 ($PASSED_TESTS 통과, $FAILED_TESTS 실패 / 총 $TOTAL_TESTS)"
    echo ""
    echo "❌ 실패한 테스트:"
    # 실패한 테스트들을 출력 (세미콜론으로 구분)
    if [ -n "$FAILED_TEST_NAMES" ]; then
        echo "$FAILED_TEST_NAMES" | tr ' ' '\n' | while read -r failed_test; do
            if [ -n "$failed_test" ]; then
                echo "   - $failed_test"
            fi
        done
    fi
    echo ""
    echo "💡 다음 사항을 확인해주세요:"
    echo "   1. 서버가 실행 중인지 확인 (Backend: :8000, Frontend: :8080)"
    echo "   2. 데이터베이스 마이그레이션 상태 확인"
    echo "   3. 필요한 환경 변수 설정 확인"
    echo "   4. 개별 테스트 로그 확인"
    echo ""
    echo "❌ 테스트 실패로 인해 스크립트를 중단합니다."
fi

echo ""
log_header "테스트 완료"

# 종료 코드 설정
# OAuth 실패만 있는 경우는 정상으로 처리
if [ $FAILED_TESTS -eq 0 ]; then
    exit 0
elif [ $FAILED_TESTS -eq 1 ] && echo "$FAILED_TEST_NAMES" | grep -q "UC-1.2"; then
    log_info "OAuth 외부 연동 테스트만 실패 - 정상 처리"
    exit 0
else
    exit 1
fi
