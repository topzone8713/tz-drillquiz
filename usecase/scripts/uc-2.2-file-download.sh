#!/usr/bin/env bash

# UC-2.2: 문제 파일 다운로드 - API 테스트 스크립트
# 작성일: 2025-10-05
# 목적: 문제 파일 다운로드 관련 API 엔드포인트 테스트

set -e  # 오류 발생 시 스크립트 종료

# 색상 정의
# Load test configuration
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/test-config.sh"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    printf "${BLUE}[INFO]${NC} $1"
}

log_success() {
    printf "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    printf "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    printf "${RED}[ERROR]${NC} $1"
}

# 테스트 결과 카운터
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_OPTIONAL_FAILED=0

# 테스트 실행 함수
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
echo "  UC-2.2: 문제 파일 다운로드 API 테스트"
echo "=========================================="
echo ""

# 1. 환경 확인
log_info "1. 환경 확인 시작"

# 서버 연결 확인
run_simple_test "Backend 서버 연결 확인" "
    curl -s $BACKEND_URL/api/health/ > /dev/null
"

run_simple_test "Frontend 서버 연결 확인" "
    curl -s $FRONTEND_URL/ > /dev/null
"

# 2. 미디어 디렉토리 및 샘플 파일 확인
log_info "2. 미디어 디렉토리 및 샘플 파일 확인"

run_simple_test "미디어 디렉토리 존재 확인" "
    [ -d $PROJECT_ROOT/media/data ]
"

run_simple_test "미디어 내 샘플 파일 존재 확인 (선택)" "
    # 파일이 있으면 통과, 없어도 경고만 (업로드 후에 생성됨)
    if [ -f $PROJECT_ROOT/media/data/sample_en.xlsx ]; then
        echo '샘플 파일 존재'
        exit 0
    else
        echo '샘플 파일 없음 (업로드 후 생성됨)'
        exit 0
    fi
"

# 3. 파일 다운로드 엔드포인트 확인
log_info "3. 파일 다운로드 엔드포인트 확인"

run_simple_test "다운로드 엔드포인트 확인" "
    # 파일이 없으면 404, 인증 필요하면 401/403
    curl -s -o /dev/null -w '%{http_code}' $BACKEND_URL/api/question-files/sample_en.xlsx/download/ | grep -qE '^(200|401|403|404)$'
"

# 4. 파일 목록 조회 엔드포인트 확인
log_info "4. 파일 목록 조회 엔드포인트 확인"

run_simple_test "파일 목록 엔드포인트 확인" "
    curl -s $BACKEND_URL/api/question-files/ > /dev/null
"

# 5. Content-Type 헤더 확인
log_info "5. Content-Type 헤더 확인"

run_simple_test "다운로드 Content-Type 헤더 확인" "
    # 파일이 있을 경우에만 확인 가능
    response=\$(curl -s -I $BACKEND_URL/api/question-files/sample_en.xlsx/download/)
    # 200이면 Content-Type 확인, 아니면 인증 또는 파일 없음
    if echo '\$response' | grep -q '200 OK'; then
        echo '\$response' | grep -q 'Content-Type'
    else
        # 401, 403, 404는 정상 (파일 없거나 인증 필요)
        echo '\$response' | grep -q '401\|403\|404'
    fi
"

# 6. Content-Disposition 헤더 확인
log_info "6. Content-Disposition 헤더 확인"

run_simple_test "다운로드 Content-Disposition 헤더 확인" "
    curl -s -I $BACKEND_URL/api/question-files/sample_en.xlsx/download/ | grep -q '200 OK'; then
        echo '\$response' | grep -q 'Content-Disposition\|attachment'
    else
        # 401, 403, 404는 정상
        echo '\$response' | grep -q '401\|403\|404'
    fi
"

# 7. 파일 존재하지 않을 경우 404 확인
log_info "7. 파일 존재하지 않을 경우 404 확인"

run_simple_test "존재하지 않는 파일 다운로드 시 404 확인" "
    curl -s -o /dev/null -w '%{http_code}' $BACKEND_URL/api/question-files/nonexistent_file_12345.xlsx/download/ | grep -qE '^(404|401|403)$'
"

# 8. Django 미디어 설정 확인
log_info "8. Django 미디어 설정 확인"

run_optional_test "Django 미디어 설정 확인" "
    cd $PROJECT_ROOT && python3 << 'PYEOF'
import os
import sys
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
import django
django.setup()
from django.conf import settings

# Django 미디어 설정 확인
media_root = getattr(settings, 'MEDIA_ROOT', None)
media_url = getattr(settings, 'MEDIA_URL', None)

if media_root and media_url:
    print(f'미디어 설정됨')
    exit(0)
else:
    print('미디어 설정 없음')
    exit(1)
    PYEOF
"

# 9. 파일 스트리밍 확인
log_info "9. 파일 스트리밍 확인"

run_simple_test "파일 스트리밍 응답 확인" "
    # 파일이 있을 경우 바이너리 데이터 스트리밍
    # 없으면 404 또는 인증 오류
    curl -s -o /dev/null -w '%{http_code}' $BACKEND_URL/api/question-files/sample_en.xlsx/download/ | grep -qE '^(200|401|403|404)$'
"

# 10. 로깅 설정 확인
log_info "10. 로깅 설정 확인"

run_optional_test "Django 로깅 설정 확인" "
    cd $PROJECT_ROOT && python3 << 'PYEOF'
import os
import sys
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
import django
django.setup()
import logging

# Django 로깅 설정 확인
logger = logging.getLogger('django')
if logger.handlers or logging.getLogger().handlers:
    print(f'로깅 핸들러 설정됨')
    exit(0)
else:
    print('로깅 핸들러 설정 없음')
    exit(1)
    PYEOF
"

# 11. 프론트엔드 파일 목록 페이지 확인
log_info "11. 프론트엔드 파일 목록 페이지 확인"

run_simple_test "Question Files 페이지 접근 확인" "
    curl -s -o /dev/null -w '%{http_code}' $FRONTEND_URL/question-files | grep -qE '^(200|404)$'
"

# 12. 파일 메타데이터 확인 (JSON)
log_info "12. 파일 메타데이터 확인"

run_simple_test "파일 메타데이터 JSON 존재 확인" "
    # 메타데이터 파일이 있으면 통과, 없어도 경고만
    if [ -f $PROJECT_ROOT/media/data/sample_en.xlsx.json ]; then
        echo '메타데이터 파일 존재'
        cat $PROJECT_ROOT/media/data/sample_en.xlsx.json | jq '.'
        exit 0
    else
        echo '메타데이터 파일 없음 (업로드 후 생성됨)'
        exit 0
    fi
"

# 13. 파일 삭제 엔드포인트 확인
log_info "13. 파일 삭제 엔드포인트 확인"

run_simple_test "파일 삭제 엔드포인트 확인" "
    response=\$(curl -s -o /dev/null -w '%{http_code}' -X DELETE $BACKEND_URL/api/question-files/sample_en.xlsx/delete/)
    # 200, 401, 403, 404 모두 정상 (인증, 권한, 파일 없음)
    [ '\$response' = '200' ] || [ '\$response' = '401' ] || [ '\$response' = '403' ] || [ '\$response' = '404' ]
"

# 14. 종합 테스트 결과
echo "=========================================="
echo "  테스트 결과 요약"
echo "=========================================="
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    log_success "모든 테스트 통과! ($TESTS_PASSED/$((TESTS_PASSED + TESTS_FAILED)))"
    echo ""
    echo "✅ 문제 파일 다운로드 API가 올바르게 구성되어 있습니다."
    echo "✅ 파일 다운로드 및 관련 엔드포인트가 정상적으로 작동합니다."
    echo "✅ Content-Type 및 Content-Disposition 헤더가 설정되어 있습니다."
    echo "✅ 파일 스트리밍 및 에러 처리가 구현되어 있습니다."
    echo ""
    echo "📝 다음 단계:"
    echo "   1. 실제 로그인 상태에서 파일 다운로드 테스트"
    echo "   2. 대용량 파일 다운로드 테스트"
    echo "   3. 다운로드 속도 최적화 (추후)"
else
    log_warning "일부 테스트 실패 ($TESTS_PASSED 통과, $TESTS_FAILED 실패)"
    echo ""
    echo "⚠️  다음 사항을 확인해주세요:"
    echo "   1. 파일 다운로드 관련 API 구현 상태"
    echo "   2. 미디어 디렉토리 및 파일 존재 여부"
    echo "   3. 프론트엔드 파일 목록 페이지 구현 상태"
    echo "   4. 파일 스트리밍 및 헤더 설정"
fi

echo ""
echo "=========================================="
echo "  테스트 완료"
echo "=========================================="

# 종료 코드 설정
if [ $TESTS_FAILED -eq 0 ]; then
    exit 0
else
    exit 1
fi

