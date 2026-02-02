#!/usr/bin/env bash

# Velero 백업 스크립트
# PostgreSQL 데이터베이스와 PV를 포함한 devops 네임스페이스 백업

set -euo pipefail

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 변수 설정
NAMESPACE="devops"
BACKUP_NAME="devops-postgres-backup-$(date +%Y%m%d-%H%M%S)"
BACKUP_RETENTION_DAYS="30"
VELERO_NAMESPACE="velero"

# Velero CLI 경로 설정
VELERO_CLI="${VELERO_CLI:-velero}"

# 도움말 함수
show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Velero 백업 스크립트 - PostgreSQL 데이터베이스와 PV를 포함한 devops 네임스페이스 백업

OPTIONS:
    -n, --namespace NAME      백업할 네임스페이스 (기본값: devops)
    -b, --backup-name NAME    백업 이름 (기본값: devops-postgres-backup-TIMESTAMP)
    -r, --retention DAYS      백업 보관 기간 (일) (기본값: 30)
    -l, --list                백업 목록 조회
    -d, --describe NAME       백업 상세 정보 조회
    -s, --status NAME         백업 상태 조회
    -h, --help                이 도움말 표시

EXAMPLES:
    $0                                    # 기본 백업 실행
    $0 -n devops -b my-backup            # 특정 이름으로 백업
    $0 -r 7                              # 7일 보관 기간으로 백업
    $0 -l                                # 백업 목록 조회
    $0 -d devops-postgres-backup-20231201-120000  # 백업 상세 정보 조회
    $0 -s devops-postgres-backup-20231201-120000  # 백업 상태 조회

EOF
}

# Velero CLI 확인
check_velero() {
    log_info "Velero CLI 확인 중..."
    
    if ! command -v "$VELERO_CLI" &> /dev/null; then
        log_error "Velero CLI를 찾을 수 없습니다. PATH에 velero가 있는지 확인하세요."
        log_info "또는 VELERO_CLI 환경변수로 velero 바이너리 경로를 지정하세요."
        log_info "예: export VELERO_CLI=/path/to/velero"
        exit 1
    fi
    
    # Velero 서버 연결 확인
    if ! "$VELERO_CLI" version &> /dev/null; then
        log_error "Velero 서버에 연결할 수 없습니다."
        log_info "kubectl이 올바르게 설정되어 있는지 확인하세요."
        exit 1
    fi
    
    log_success "Velero CLI 확인 완료"
}

# 네임스페이스 존재 확인
check_namespace() {
    log_info "네임스페이스 '$NAMESPACE' 확인 중..."
    
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_error "네임스페이스 '$NAMESPACE'를 찾을 수 없습니다."
        exit 1
    fi
    
    log_success "네임스페이스 '$NAMESPACE' 확인 완료"
}

# PostgreSQL 파드 확인
check_postgres_pod() {
    log_info "PostgreSQL 파드 확인 중..."
    
    local postgres_pods
    postgres_pods=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/name=postgresql --no-headers 2>/dev/null | wc -l)
    
    if [ "$postgres_pods" -eq 0 ]; then
        log_warning "PostgreSQL 파드를 찾을 수 없습니다. 라벨을 확인하세요."
        log_info "사용 가능한 파드:"
        kubectl get pods -n "$NAMESPACE" --no-headers | head -5
    else
        log_success "PostgreSQL 파드 $postgres_pods 개 확인 완료"
    fi
}

# 백업 실행
run_backup() {
    log_info "백업 시작: $BACKUP_NAME"
    
    # 백업 명령 실행
    "$VELERO_CLI" backup create "$BACKUP_NAME" \
        --include-namespaces "$NAMESPACE" \
        --include-resources pods,persistentvolumes,persistentvolumeclaims,statefulsets,secrets,configmaps,services \
        --default-volumes-to-fs-backup=true \
        --ttl "${BACKUP_RETENTION_DAYS}h0m0s" \
        --wait
    
    if [ $? -eq 0 ]; then
        log_success "백업 완료: $BACKUP_NAME"
        
        # 백업 정보 출력
        log_info "백업 정보:"
        "$VELERO_CLI" backup describe "$BACKUP_NAME" --details
        
        # 백업 크기 정보 (가능한 경우)
        log_info "백업 크기 정보:"
        "$VELERO_CLI" backup describe "$BACKUP_NAME" | grep -E "(Total items|Items backed up|Backup Volumes)" || true
        
    else
        log_error "백업 실패: $BACKUP_NAME"
        log_info "백업 로그 확인:"
        "$VELERO_CLI" backup logs "$BACKUP_NAME" | tail -20
        exit 1
    fi
}

# 백업 목록 조회
list_backups() {
    log_info "백업 목록 조회 중..."
    "$VELERO_CLI" backup get --output table
}

# 백업 상세 정보 조회
describe_backup() {
    local backup_name="$1"
    log_info "백업 상세 정보 조회: $backup_name"
    "$VELERO_CLI" backup describe "$backup_name" --details
}

# 백업 상태 조회
get_backup_status() {
    local backup_name="$1"
    log_info "백업 상태 조회: $backup_name"
    "$VELERO_CLI" backup describe "$backup_name" | grep -E "(Phase|Started|Completed|Expiration)" || true
}

# 메인 함수
main() {
    # 인자 파싱
    while [[ $# -gt 0 ]]; do
        case $1 in
            -n|--namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            -b|--backup-name)
                BACKUP_NAME="$2"
                shift 2
                ;;
            -r|--retention)
                BACKUP_RETENTION_DAYS="$2"
                shift 2
                ;;
            -l|--list)
                list_backups
                exit 0
                ;;
            -d|--describe)
                if [ -z "${2:-}" ]; then
                    log_error "백업 이름을 지정하세요."
                    exit 1
                fi
                describe_backup "$2"
                exit 0
                ;;
            -s|--status)
                if [ -z "${2:-}" ]; then
                    log_error "백업 이름을 지정하세요."
                    exit 1
                fi
                get_backup_status "$2"
                exit 0
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "알 수 없는 옵션: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 백업 실행
    log_info "=== Velero PostgreSQL 백업 시작 ==="
    log_info "네임스페이스: $NAMESPACE"
    log_info "백업 이름: $BACKUP_NAME"
    log_info "보관 기간: $BACKUP_RETENTION_DAYS 일"
    
    check_velero
    check_namespace
    check_postgres_pod
    run_backup
    
    log_success "=== Velero PostgreSQL 백업 완료 ==="
}

# 스크립트 실행
main "$@"
