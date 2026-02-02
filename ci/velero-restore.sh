#!/usr/bin/env bash

# Velero 복원 스크립트
# PostgreSQL 데이터베이스 백업에서 복원

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
SOURCE_NAMESPACE="devops"
TARGET_NAMESPACE="devops"
RESTORE_NAME="devops-postgres-restore-$(date +%Y%m%d-%H%M%S)"
VELERO_NAMESPACE="velero"

# Velero CLI 경로 설정
VELERO_CLI="${VELERO_CLI:-velero}"

# 도움말 함수
show_help() {
    cat << EOF
Usage: $0 [OPTIONS] BACKUP_NAME

Velero 복원 스크립트 - PostgreSQL 데이터베이스 백업에서 복원

OPTIONS:
    -s, --source-namespace NAME    원본 네임스페이스 (기본값: devops)
    -t, --target-namespace NAME    대상 네임스페이스 (기본값: devops)
    -r, --restore-name NAME        복원 이름 (기본값: devops-postgres-restore-TIMESTAMP)
    -f, --force                    기존 리소스 강제 덮어쓰기
    -l, --list                     백업 목록 조회
    -h, --help                     이 도움말 표시

ARGUMENTS:
    BACKUP_NAME                    복원할 백업 이름

EXAMPLES:
    $0 devops-postgres-backup-20231201-120000              # 백업에서 복원
    $0 -t devops-restored devops-postgres-backup-20231201   # 다른 네임스페이스로 복원
    $0 -f devops-postgres-backup-20231201                   # 강제 덮어쓰기로 복원
    $0 -l                                                        # 백업 목록 조회

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

# 백업 존재 확인
check_backup() {
    local backup_name="$1"
    log_info "백업 '$backup_name' 확인 중..."
    
    if ! "$VELERO_CLI" backup describe "$backup_name" &> /dev/null; then
        log_error "백업 '$backup_name'를 찾을 수 없습니다."
        log_info "사용 가능한 백업 목록:"
        "$VELERO_CLI" backup get --output table
        exit 1
    fi
    
    # 백업 상태 확인
    local backup_phase
    backup_phase=$("$VELERO_CLI" backup describe "$backup_name" | grep "Phase:" | awk '{print $2}')
    
    if [ "$backup_phase" != "Completed" ]; then
        log_error "백업 '$backup_name'이 완료되지 않았습니다. 현재 상태: $backup_phase"
        exit 1
    fi
    
    log_success "백업 '$backup_name' 확인 완료 (상태: $backup_phase)"
}

# 대상 네임스페이스 확인
check_target_namespace() {
    log_info "대상 네임스페이스 '$TARGET_NAMESPACE' 확인 중..."
    
    if ! kubectl get namespace "$TARGET_NAMESPACE" &> /dev/null; then
        log_warning "대상 네임스페이스 '$TARGET_NAMESPACE'가 존재하지 않습니다. 생성합니다..."
        kubectl create namespace "$TARGET_NAMESPACE"
        log_success "네임스페이스 '$TARGET_NAMESPACE' 생성 완료"
    else
        log_success "네임스페이스 '$TARGET_NAMESPACE' 확인 완료"
    fi
}

# 기존 리소스 확인
check_existing_resources() {
    if [ "$TARGET_NAMESPACE" = "$SOURCE_NAMESPACE" ]; then
        log_info "기존 리소스 확인 중..."
        
        local existing_pods
        existing_pods=$(kubectl get pods -n "$TARGET_NAMESPACE" --no-headers 2>/dev/null | wc -l)
        
        if [ "$existing_pods" -gt 0 ]; then
            log_warning "대상 네임스페이스에 기존 파드가 $existing_pods 개 있습니다."
            log_info "기존 파드 목록:"
            kubectl get pods -n "$TARGET_NAMESPACE" --no-headers | head -5
            
            if [ "${FORCE_RESTORE:-false}" != "true" ]; then
                log_warning "기존 리소스를 덮어쓰려면 --force 옵션을 사용하세요."
                read -p "계속 진행하시겠습니까? (y/N): " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    log_info "복원이 취소되었습니다."
                    exit 0
                fi
            fi
        fi
    fi
}

# 복원 실행
run_restore() {
    local backup_name="$1"
    log_info "복원 시작: $RESTORE_NAME (백업: $backup_name)"
    
    # 복원 명령 구성
    local restore_cmd=("$VELERO_CLI" restore create "$RESTORE_NAME" "--from-backup" "$backup_name")
    
    # 네임스페이스 매핑 설정
    if [ "$SOURCE_NAMESPACE" != "$TARGET_NAMESPACE" ]; then
        restore_cmd+=("--namespace-mapping" "${SOURCE_NAMESPACE}:${TARGET_NAMESPACE}")
    fi
    
    # 기존 리소스 정책 설정
    if [ "${FORCE_RESTORE:-false}" = "true" ]; then
        restore_cmd+=("--existing-resource-policy" "update")
    else
        restore_cmd+=("--existing-resource-policy" "skip")
    fi
    
    # 대기 옵션 추가
    restore_cmd+=("--wait")
    
    # 복원 명령 실행
    log_info "복원 명령: ${restore_cmd[*]}"
    "${restore_cmd[@]}"
    
    if [ $? -eq 0 ]; then
        log_success "복원 완료: $RESTORE_NAME"
        
        # 복원 정보 출력
        log_info "복원 정보:"
        "$VELERO_CLI" restore describe "$RESTORE_NAME" --details
        
        # 복원된 리소스 확인
        log_info "복원된 리소스 확인:"
        kubectl get all -n "$TARGET_NAMESPACE" || true
        
    else
        log_error "복원 실패: $RESTORE_NAME"
        log_info "복원 로그 확인:"
        "$VELERO_CLI" restore logs "$RESTORE_NAME" | tail -20
        exit 1
    fi
}

# 백업 목록 조회
list_backups() {
    log_info "백업 목록 조회 중..."
    "$VELERO_CLI" backup get --output table
}

# 복원 후 검증
verify_restore() {
    log_info "복원 검증 중..."
    
    # PostgreSQL 파드 상태 확인
    log_info "PostgreSQL 파드 상태 확인:"
    kubectl get pods -n "$TARGET_NAMESPACE" -l app.kubernetes.io/name=postgresql || true
    
    # PVC 상태 확인
    log_info "PVC 상태 확인:"
    kubectl get pvc -n "$TARGET_NAMESPACE" || true
    
    # 서비스 상태 확인
    log_info "서비스 상태 확인:"
    kubectl get svc -n "$TARGET_NAMESPACE" || true
    
    log_success "복원 검증 완료"
}

# 메인 함수
main() {
    local backup_name=""
    
    # 인자 파싱
    while [[ $# -gt 0 ]]; do
        case $1 in
            -s|--source-namespace)
                SOURCE_NAMESPACE="$2"
                shift 2
                ;;
            -t|--target-namespace)
                TARGET_NAMESPACE="$2"
                shift 2
                ;;
            -r|--restore-name)
                RESTORE_NAME="$2"
                shift 2
                ;;
            -f|--force)
                FORCE_RESTORE=true
                shift
                ;;
            -l|--list)
                list_backups
                exit 0
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            -*)
                log_error "알 수 없는 옵션: $1"
                show_help
                exit 1
                ;;
            *)
                if [ -z "$backup_name" ]; then
                    backup_name="$1"
                else
                    log_error "백업 이름은 하나만 지정할 수 있습니다."
                    show_help
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    # 백업 이름 확인
    if [ -z "$backup_name" ]; then
        log_error "백업 이름을 지정하세요."
        show_help
        exit 1
    fi
    
    # 복원 실행
    log_info "=== Velero PostgreSQL 복원 시작 ==="
    log_info "원본 네임스페이스: $SOURCE_NAMESPACE"
    log_info "대상 네임스페이스: $TARGET_NAMESPACE"
    log_info "복원 이름: $RESTORE_NAME"
    log_info "백업 이름: $backup_name"
    log_info "강제 덮어쓰기: ${FORCE_RESTORE:-false}"
    
    check_velero
    check_backup "$backup_name"
    check_target_namespace
    check_existing_resources
    run_restore "$backup_name"
    verify_restore
    
    log_success "=== Velero PostgreSQL 복원 완료 ==="
}

# 스크립트 실행
main "$@"
