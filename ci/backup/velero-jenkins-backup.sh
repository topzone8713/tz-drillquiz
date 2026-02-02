#!/usr/bin/env bash

# Velero Jenkins 백업 스크립트
# Jenkins 네임스페이스와 PV를 포함한 백업

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
NAMESPACE="jenkins"
BACKUP_NAME="jenkins-backup-$(date +%Y%m%d-%H%M%S)"
BACKUP_RETENTION_DAYS="30"
VELERO_NAMESPACE="velero"

# Velero CLI 경로 설정
VELERO_CLI="${VELERO_CLI:-velero}"

# 도움말 함수
show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Velero 백업 스크립트 - Jenkins 네임스페이스와 PV를 포함한 백업

OPTIONS:
    -n, --namespace NAME      백업할 네임스페이스 (기본값: jenkins)
    -b, --backup-name NAME    백업 이름 (기본값: jenkins-backup-TIMESTAMP)
    -r, --retention DAYS      백업 보관 기간 (일) (기본값: 30)
    -l, --list                백업 목록 조회
    -d, --describe NAME       백업 상세 정보 조회
    -s, --status NAME         백업 상태 조회
    -h, --help                이 도움말 표시

EXAMPLES:
    $0                                    # 기본 백업 실행
    $0 -n jenkins -b my-backup            # 특정 이름으로 백업
    $0 -r 7                              # 7일 보관 기간으로 백업
    $0 -l                                # 백업 목록 조회
    $0 -d jenkins-backup-20231201-120000  # 백업 상세 정보 조회
    $0 -s jenkins-backup-20231201-120000  # 백업 상태 조회

EOF
}

# Velero CLI 확인 및 설치
check_velero() {
    log_info "Velero CLI 확인 중..."
    
    # 먼저 PATH에서 확인
    if command -v "$VELERO_CLI" &> /dev/null; then
        log_success "Velero CLI 확인 완료: $(command -v $VELERO_CLI)"
        return 0
    fi
    
    # 현재 디렉토리의 velero 파일 확인
    if [ -f "./velero" ] && [ -x "./velero" ]; then
        VELERO_CLI="./velero"
        log_success "현재 디렉토리의 Velero CLI 발견: ./velero"
    # 스크립트 디렉토리의 velero 파일 확인
    elif [ -f "$(dirname "$0")/velero" ] && [ -x "$(dirname "$0")/velero" ]; then
        VELERO_CLI="$(dirname "$0")/velero"
        log_success "스크립트 디렉토리의 Velero CLI 발견: $VELERO_CLI"
    # 프로젝트 루트의 velero 파일 확인
    elif [ -f "$(pwd)/velero" ] && [ -x "$(pwd)/velero" ]; then
        VELERO_CLI="$(pwd)/velero"
        log_success "프로젝트 루트의 Velero CLI 발견: $VELERO_CLI"
    else
        log_warning "Velero CLI를 찾을 수 없습니다."
        log_info "Velero CLI를 자동으로 설치하시겠습니까? (y/n)"
        read -r response
        
        if [[ "$response" =~ ^[Yy]$ ]]; then
            install_velero_cli
        else
            log_error "Velero CLI가 필요합니다."
            log_info "수동 설치 방법:"
            log_info "  macOS: brew install velero"
            log_info "  또는: https://velero.io/docs/main/basic-install/#install-the-cli"
            log_info "또는 VELERO_CLI 환경변수로 velero 바이너리 경로를 지정하세요."
            log_info "예: export VELERO_CLI=/path/to/velero"
            exit 1
        fi
    fi
    
    # Velero 서버 연결 확인
    if ! "$VELERO_CLI" version &> /dev/null; then
        log_error "Velero 서버에 연결할 수 없습니다."
        log_info "kubectl이 올바르게 설정되어 있는지 확인하세요."
        exit 1
    fi
    
    log_success "Velero CLI 확인 완료: $VELERO_CLI"
}

# Velero CLI 설치
install_velero_cli() {
    log_info "Velero CLI 설치 중..."
    
    local os_type
    os_type=$(uname -s | tr '[:upper:]' '[:lower:]')
    local arch_type
    arch_type=$(uname -m)
    
    # macOS의 경우 arm64 또는 amd64
    if [ "$os_type" = "darwin" ]; then
        if [ "$arch_type" = "arm64" ]; then
            arch_type="arm64"
        else
            arch_type="amd64"
        fi
    fi
    
    local velero_version="v1.13.0"
    local download_url="https://github.com/vmware-tanzu/velero/releases/download/${velero_version}/velero-${velero_version}-${os_type}-${arch_type}.tar.gz"
    local temp_dir
    temp_dir=$(mktemp -d)
    
    log_info "다운로드 URL: $download_url"
    
    # 다운로드 및 설치
    if curl -fsSL -o "${temp_dir}/velero.tar.gz" "$download_url"; then
        tar -xzf "${temp_dir}/velero.tar.gz" -C "${temp_dir}"
        chmod +x "${temp_dir}/velero-${velero_version}-${os_type}-${arch_type}/velero"
        
        # /usr/local/bin에 설치 시도, 실패하면 현재 디렉토리
        if mv "${temp_dir}/velero-${velero_version}-${os_type}-${arch_type}/velero" /usr/local/bin/velero 2>/dev/null; then
            log_success "Velero CLI가 /usr/local/bin/velero에 설치되었습니다."
            VELERO_CLI="velero"
        else
            log_warning "권한이 없어 /usr/local/bin에 설치할 수 없습니다."
            log_info "현재 디렉토리에 velero를 설치합니다."
            mv "${temp_dir}/velero-${velero_version}-${os_type}-${arch_type}/velero" ./velero
            chmod +x ./velero
            VELERO_CLI="./velero"
            log_success "Velero CLI가 ./velero에 설치되었습니다."
        fi
        
        rm -rf "${temp_dir}"
    else
        log_error "Velero CLI 다운로드 실패"
        log_info "수동 설치 방법:"
        log_info "  macOS: brew install velero"
        log_info "  또는: https://velero.io/docs/main/basic-install/#install-the-cli"
        exit 1
    fi
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

# Jenkins 리소스 확인
check_jenkins_resources() {
    log_info "Jenkins 리소스 확인 중..."
    
    # Jenkins Deployment 확인
    local jenkins_deployments
    jenkins_deployments=$(kubectl get deployments -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l)
    
    if [ "$jenkins_deployments" -eq 0 ]; then
        log_warning "Jenkins Deployment를 찾을 수 없습니다."
    else
        log_success "Jenkins Deployment $jenkins_deployments 개 확인 완료"
    fi
    
    # Jenkins PVC 확인
    local jenkins_pvcs
    jenkins_pvcs=$(kubectl get pvc -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l)
    
    if [ "$jenkins_pvcs" -eq 0 ]; then
        log_warning "Jenkins PVC를 찾을 수 없습니다."
    else
        log_success "Jenkins PVC $jenkins_pvcs 개 확인 완료"
        log_info "PVC 목록:"
        kubectl get pvc -n "$NAMESPACE" --no-headers | awk '{print "  - " $1}'
    fi
}

# 백업 실행
run_backup() {
    log_info "백업 시작: $BACKUP_NAME"
    
    # Velero CLI가 없으면 kubectl을 통해 YAML로 백업 생성
    if ! command -v "$VELERO_CLI" &> /dev/null && [ ! -f "$VELERO_CLI" ]; then
        log_warning "Velero CLI를 사용할 수 없습니다. kubectl을 통해 백업을 생성합니다."
        create_backup_via_kubectl
        return
    fi
    
    # 백업 명령 실행
    "$VELERO_CLI" backup create "$BACKUP_NAME" \
        --include-namespaces "$NAMESPACE" \
        --include-resources deployments,statefulsets,services,configmaps,secrets,persistentvolumes,persistentvolumeclaims,pods,replicasets \
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

# kubectl을 통해 백업 생성
create_backup_via_kubectl() {
    log_info "kubectl을 통해 백업 생성 중..."
    
    # 백업 YAML 생성
    local backup_yaml
    backup_yaml=$(cat <<EOF
apiVersion: velero.io/v1
kind: Backup
metadata:
  name: ${BACKUP_NAME}
  namespace: ${VELERO_NAMESPACE}
  labels:
    app: jenkins
    component: ci-cd
    created-by: velero-jenkins-backup-script
spec:
  includedNamespaces:
  - ${NAMESPACE}
  includedResources:
  - deployments
  - statefulsets
  - services
  - configmaps
  - secrets
  - persistentvolumes
  - persistentvolumeclaims
  - pods
  - replicasets
  - serviceaccounts
  - roles
  - rolebindings
  includeClusterResources: auto
  defaultVolumesToFsBackup: true
  snapshotVolumes: true
  storageLocation: default
  ttl: ${BACKUP_RETENTION_DAYS}h0m0s
  csiSnapshotTimeout: 10m0s
  itemOperationTimeout: 4h0m0s
EOF
)
    
    # YAML을 임시 파일로 저장하고 적용
    local temp_file
    temp_file=$(mktemp)
    echo "$backup_yaml" > "$temp_file"
    
    log_info "백업 리소스 생성 중..."
    if kubectl apply -f "$temp_file"; then
        log_success "백업 리소스 생성 완료: $BACKUP_NAME"
        log_info "백업 상태 확인:"
        kubectl get backup "$BACKUP_NAME" -n "$VELERO_NAMESPACE"
        
        # 백업 완료 대기 및 상태 확인
        log_info "백업 진행 상황 모니터링 중..."
        local max_wait=300  # 최대 5분 대기
        local waited=0
        while [ $waited -lt $max_wait ]; do
            local phase
            phase=$(kubectl get backup "$BACKUP_NAME" -n "$VELERO_NAMESPACE" -o jsonpath='{.status.phase}' 2>/dev/null)
            
            if [ "$phase" = "Completed" ]; then
                log_success "백업 완료: $BACKUP_NAME"
                break
            elif [ "$phase" = "PartiallyFailed" ] || [ "$phase" = "Failed" ]; then
                log_warning "백업 상태: $phase"
                log_info "PodVolumeBackup 상태 확인:"
                kubectl get podvolumebackups -n "$VELERO_NAMESPACE" -l velero.io/backup-name="$BACKUP_NAME" -o wide
                
                # Kopia 리포지토리 초기화 실패 확인
                local pvb_errors
                pvb_errors=$(kubectl get podvolumebackups -n "$VELERO_NAMESPACE" -l velero.io/backup-name="$BACKUP_NAME" -o jsonpath='{range .items[*]}{.status.message}{"\n"}{end}' 2>/dev/null | grep -i "repository not initialized" | head -1)
                
                if [ -n "$pvb_errors" ]; then
                    log_warning "Kopia 리포지토리 초기화 실패가 감지되었습니다."
                    log_info "해결 방법:"
                    log_info "  1. MinIO 연결 확인: kubectl get svc -n devops | grep minio"
                    log_info "  2. Velero node-agent 재시작: kubectl rollout restart daemonset/node-agent -n velero"
                    log_info "  3. 새로운 백업 시도 (첫 백업 시 Kopia 리포지토리가 자동 초기화됨)"
                fi
                break
            fi
            
            sleep 5
            waited=$((waited + 5))
            echo -n "."
        done
        echo
        
        log_info "백업 진행 상황을 계속 확인하려면 다음 명령을 실행하세요:"
        log_info "  kubectl get backup $BACKUP_NAME -n $VELERO_NAMESPACE -w"
        log_info "  kubectl get podvolumebackups -n $VELERO_NAMESPACE -l velero.io/backup-name=$BACKUP_NAME"
        log_info "또는 Velero CLI를 설치한 후:"
        log_info "  velero backup describe $BACKUP_NAME"
    else
        log_error "백업 리소스 생성 실패"
        rm -f "$temp_file"
        exit 1
    fi
    
    rm -f "$temp_file"
}

# 백업 목록 조회
list_backups() {
    log_info "백업 목록 조회 중..."
    
    if command -v "$VELERO_CLI" &> /dev/null || [ -f "$VELERO_CLI" ]; then
        "$VELERO_CLI" backup get --output table
    else
        log_info "kubectl을 통해 백업 목록 조회 중..."
        kubectl get backups -n "$VELERO_NAMESPACE" -o wide
    fi
}

# 백업 상세 정보 조회
describe_backup() {
    local backup_name="$1"
    log_info "백업 상세 정보 조회: $backup_name"
    
    if command -v "$VELERO_CLI" &> /dev/null || [ -f "$VELERO_CLI" ]; then
        "$VELERO_CLI" backup describe "$backup_name" --details
    else
        log_info "kubectl을 통해 백업 정보 조회 중..."
        kubectl describe backup "$backup_name" -n "$VELERO_NAMESPACE"
    fi
}

# 백업 상태 조회
get_backup_status() {
    local backup_name="$1"
    log_info "백업 상태 조회: $backup_name"
    
    if command -v "$VELERO_CLI" &> /dev/null || [ -f "$VELERO_CLI" ]; then
        "$VELERO_CLI" backup describe "$backup_name" | grep -E "(Phase|Started|Completed|Expiration)" || true
    else
        log_info "kubectl을 통해 백업 상태 조회 중..."
        kubectl get backup "$backup_name" -n "$VELERO_NAMESPACE" -o jsonpath='{.status.phase}' && echo
        kubectl get backup "$backup_name" -n "$VELERO_NAMESPACE" -o jsonpath='{.status.startTimestamp}' && echo
        kubectl get backup "$backup_name" -n "$VELERO_NAMESPACE" -o jsonpath='{.status.completionTimestamp}' && echo
    fi
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
    log_info "=== Velero Jenkins 백업 시작 ==="
    log_info "네임스페이스: $NAMESPACE"
    log_info "백업 이름: $BACKUP_NAME"
    log_info "보관 기간: $BACKUP_RETENTION_DAYS 일"
    
    check_velero
    check_namespace
    check_jenkins_resources
    run_backup
    
    log_success "=== Velero Jenkins 백업 완료 ==="
}

# 스크립트 실행
main "$@"

