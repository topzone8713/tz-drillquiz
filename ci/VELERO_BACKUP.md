# 🔄 Velero 백업 가이드

이 문서는 Velero를 사용하여 PostgreSQL 데이터베이스와 PV(Persistent Volume)를 포함한 Kubernetes 리소스를 백업하고 복원하는 방법을 설명합니다.

## 📋 목차

- [개요](#개요)
- [전제 조건](#전제-조건)
- [파일 구조](#파일-구조)
- [백업 실행](#백업-실행)
- [복원 실행](#복원-실행)
- [자동화된 백업](#자동화된-백업)
- [문제 해결](#문제-해결)
- [참고 자료](#참고-자료)

## 🎯 개요

Velero는 Kubernetes 클러스터의 리소스와 영구 볼륨을 백업하고 복원하는 도구입니다. 이 설정은 다음과 같은 기능을 제공합니다:

- **PostgreSQL 데이터베이스 백업**: devops 네임스페이스의 PostgreSQL 데이터베이스와 관련 리소스
- **PV 백업**: 영구 볼륨의 데이터까지 포함한 완전한 백업
- **자동화된 스케줄**: 일일/주간 자동 백업
- **복원 기능**: 백업에서 완전한 복원
- **스크립트 기반**: 쉬운 백업/복원 작업

## ⚙️ 전제 조건

### 1. Velero 설치 확인

```bash
# Velero 파드 상태 확인
kubectl get pods -n velero

# Velero CLI 설치 (macOS)
curl -fsSL -o velero-v1.13.0-darwin-amd64.tar.gz \
  https://github.com/vmware-tanzu/velero/releases/download/v1.13.0/velero-v1.13.0-darwin-amd64.tar.gz
tar -xzf velero-v1.13.0-darwin-amd64.tar.gz
chmod +x velero-v1.13.0-darwin-amd64/velero
```

### 2. 백업 스토리지 위치 확인

```bash
# 백업 스토리지 위치 확인
kubectl get backupstoragelocation -n velero

# MinIO 서비스 확인 (백업 스토리지)
kubectl get svc -n devops | grep minio
```

### 3. 대상 리소스 확인

```bash
# devops 네임스페이스 확인
kubectl get ns devops

# PostgreSQL 파드 확인
kubectl get pods -n devops | grep postgres

# PVC 확인
kubectl get pvc -n devops | grep postgres
```

## 📁 파일 구조

```
ci/
├── BACKUP.md                    # 이 문서
├── velero-backup.yaml          # 백업 설정 YAML
├── velero-restore.yaml         # 복원 설정 YAML
├── velero-schedule.yaml        # 자동 백업 스케줄 YAML
├── velero-backup.sh            # 백업 실행 스크립트
└── velero-restore.sh           # 복원 실행 스크립트
```

### 파일 설명

| 파일 | 용도 | 설명 |
|------|------|------|
| `velero-backup.yaml` | 수동 백업 | PostgreSQL과 PV를 포함한 수동 백업 설정 |
| `velero-restore.yaml` | 복원 설정 | 백업에서 리소스 복원 설정 |
| `velero-schedule.yaml` | 자동 백업 | 일일/주간 자동 백업 스케줄 |
| `velero-backup.sh` | 백업 스크립트 | 백업 실행 및 관리 스크립트 |
| `velero-restore.sh` | 복원 스크립트 | 복원 실행 및 관리 스크립트 |

## 🚀 백업 실행

### 1. 스크립트를 사용한 백업

```bash
# 기본 백업 실행
./ci/velero-backup.sh

# 특정 이름으로 백업
./ci/velero-backup.sh -b my-postgres-backup

# 7일 보관 기간으로 백업
./ci/velero-backup.sh -r 7

# 백업 목록 조회
./ci/velero-backup.sh -l

# 백업 상세 정보 조회
./ci/velero-backup.sh -d devops-postgres-backup-20231201-120000
```

### 2. Velero CLI를 사용한 백업

```bash
# 직접 백업 실행
velero backup create devops-postgres-backup \
  --include-namespaces devops \
  --include-resources pods,persistentvolumes,persistentvolumeclaims,statefulsets,secrets,configmaps,services \
  --default-volumes-to-fs-backup=true \
  --ttl 720h0m0s \
  --wait
```

### 3. YAML 파일을 사용한 백업

```bash
# YAML 파일로 백업 생성
kubectl apply -f ci/velero-backup.yaml

# 백업 상태 확인
velero backup describe devops-postgres-backup
```

## 🔄 복원 실행

### 1. 스크립트를 사용한 복원

```bash
# 백업에서 복원
./ci/velero-restore.sh devops-postgres-backup-20231201-120000

# 다른 네임스페이스로 복원
./ci/velero-restore.sh -t devops-restored devops-postgres-backup-20231201

# 강제 덮어쓰기로 복원
./ci/velero-restore.sh -f devops-postgres-backup-20231201

# 백업 목록 조회
./ci/velero-restore.sh -l
```

### 2. Velero CLI를 사용한 복원

```bash
# 직접 복원 실행
velero restore create devops-postgres-restore \
  --from-backup devops-postgres-backup-20231201-120000 \
  --wait

# 복원 상태 확인
velero restore describe devops-postgres-restore
```

### 3. YAML 파일을 사용한 복원

```bash
# YAML 파일로 복원 생성
kubectl apply -f ci/velero-restore.yaml

# 복원 상태 확인
velero restore describe devops-postgres-restore
```

## ⏰ 자동화된 백업

### 1. 스케줄 백업 설정

```bash
# 스케줄 백업 생성
kubectl apply -f ci/velero-schedule.yaml

# 스케줄 확인
velero schedule get

# 스케줄 상세 정보
velero schedule describe devops-postgres-daily-backup
```

### 2. 스케줄 설정

| 스케줄 | 빈도 | 보관 기간 | 설명 |
|--------|------|-----------|------|
| `devops-postgres-daily-backup` | 매일 2:00 AM | 7일 | 일일 백업 |
| `devops-postgres-weekly-backup` | 매주 일요일 3:00 AM | 30일 | 주간 백업 |

### 3. 스케줄 관리

```bash
# 스케줄 일시정지
velero schedule pause devops-postgres-daily-backup

# 스케줄 재개
velero schedule unpause devops-postgres-daily-backup

# 스케줄 삭제
velero schedule delete devops-postgres-daily-backup
```

## 🏭 운영 환경 PostgreSQL 백업/복원 스크립트

### 1. 운영 PostgreSQL 백업 스크립트

```bash
#!/bin/bash
# 운영 PostgreSQL 백업 스크립트 (production-postgres-backup.sh)

set -euo pipefail

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 로그 함수
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 변수 설정
NAMESPACE="devops"
BACKUP_NAME="prod-postgres-backup-$(date +%Y%m%d-%H%M%S)"
BACKUP_RETENTION_DAYS="30"
POSTGRES_POD="devops-postgres-postgresql-0"
VELERO_CLI="${VELERO_CLI:-velero}"

# 사전 백업 체크
pre_backup_check() {
    log_info "운영 PostgreSQL 백업 사전 체크 시작..."
    
    # PostgreSQL 파드 상태 확인
    if ! kubectl get pod "$POSTGRES_POD" -n "$NAMESPACE" &>/dev/null; then
        log_error "PostgreSQL 파드를 찾을 수 없습니다: $POSTGRES_POD"
        exit 1
    fi
    
    # 파드 상태 확인
    local pod_status
    pod_status=$(kubectl get pod "$POSTGRES_POD" -n "$NAMESPACE" -o jsonpath='{.status.phase}')
    if [ "$pod_status" != "Running" ]; then
        log_error "PostgreSQL 파드가 실행 중이 아닙니다. 상태: $pod_status"
        exit 1
    fi
    
    # 데이터베이스 연결 테스트
    if ! kubectl exec "$POSTGRES_POD" -n "$NAMESPACE" -- psql -U postgres -c "SELECT 1;" &>/dev/null; then
        log_error "PostgreSQL 데이터베이스에 연결할 수 없습니다"
        exit 1
    fi
    
    log_success "사전 체크 완료"
}

# 백업 전 데이터베이스 정리
prepare_database() {
    log_info "PostgreSQL 백업 준비 중..."
    
    # 활성 연결 종료 (백업을 위한 안전한 상태로 전환)
    kubectl exec "$POSTGRES_POD" -n "$NAMESPACE" -- psql -U postgres -c "
        SELECT pg_terminate_backend(pid) 
        FROM pg_stat_activity 
        WHERE datname NOT IN ('postgres', 'template0', 'template1') 
        AND pid <> pg_backend_pid();
    " || log_warning "일부 연결 종료 실패 (정상적일 수 있음)"
    
    # 체크포인트 강제 실행
    kubectl exec "$POSTGRES_POD" -n "$NAMESPACE" -- psql -U postgres -c "CHECKPOINT;" || {
        log_error "체크포인트 실행 실패"
        exit 1
    }
    
    log_success "데이터베이스 백업 준비 완료"
}

# Velero 백업 실행
run_velero_backup() {
    log_info "Velero 백업 실행: $BACKUP_NAME"
    
    "$VELERO_CLI" backup create "$BACKUP_NAME" \
        --include-namespaces "$NAMESPACE" \
        --include-resources pods,persistentvolumes,persistentvolumeclaims,statefulsets,secrets,configmaps,services \
        --selector "app.kubernetes.io/name=postgresql" \
        --default-volumes-to-fs-backup=true \
        --ttl "${BACKUP_RETENTION_DAYS}h0m0s" \
        --wait
    
    if [ $? -eq 0 ]; then
        log_success "Velero 백업 완료: $BACKUP_NAME"
    else
        log_error "Velero 백업 실패"
        exit 1
    fi
}

# 백업 검증
verify_backup() {
    log_info "백업 검증 중..."
    
    # 백업 상태 확인
    local backup_phase
    backup_phase=$("$VELERO_CLI" backup describe "$BACKUP_NAME" | grep "Phase:" | awk '{print $2}')
    
    if [ "$backup_phase" = "Completed" ]; then
        log_success "백업 검증 성공 (상태: $backup_phase)"
    elif [ "$backup_phase" = "PartiallyFailed" ]; then
        log_warning "백업이 부분적으로 실패했지만 계속 진행합니다 (상태: $backup_phase)"
    else
        log_error "백업 검증 실패 (상태: $backup_phase)"
        exit 1
    fi
    
    # 백업된 항목 수 확인
    local items_backed_up
    items_backed_up=$("$VELERO_CLI" backup describe "$BACKUP_NAME" | grep "Items backed up:" | awk '{print $4}')
    log_info "백업된 항목 수: $items_backed_up"
}

# 메인 실행
main() {
    log_info "=== 운영 PostgreSQL 백업 시작 ==="
    log_info "백업 이름: $BACKUP_NAME"
    log_info "네임스페이스: $NAMESPACE"
    log_info "보관 기간: $BACKUP_RETENTION_DAYS 일"
    
    pre_backup_check
    prepare_database
    run_velero_backup
    verify_backup
    
    log_success "=== 운영 PostgreSQL 백업 완료 ==="
    log_info "백업 이름: $BACKUP_NAME"
}

main "$@"
```

### 2. 운영 PostgreSQL 복원 스크립트

```bash
#!/bin/bash
# 운영 PostgreSQL 복원 스크립트 (production-postgres-restore.sh)

set -euo pipefail

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 로그 함수
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 변수 설정
SOURCE_NAMESPACE="devops"
TARGET_NAMESPACE="devops"
RESTORE_NAME="prod-postgres-restore-$(date +%Y%M%d-%H%M%S)"
POSTGRES_POD="devops-postgres-postgresql-0"
VELERO_CLI="${VELERO_CLI:-velero}"

# 사용법 표시
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS] BACKUP_NAME

운영 PostgreSQL 복원 스크립트

OPTIONS:
    -t, --target-namespace NAME    대상 네임스페이스 (기본값: devops)
    -r, --restore-name NAME       복원 이름 (기본값: prod-postgres-restore-TIMESTAMP)
    -f, --force                   기존 리소스 강제 덮어쓰기
    -d, --dry-run                 실제 복원 없이 시뮬레이션만 실행
    -h, --help                    이 도움말 표시

ARGUMENTS:
    BACKUP_NAME                   복원할 백업 이름

EXAMPLES:
    $0 prod-postgres-backup-20231201-120000
    $0 -t devops-restored prod-postgres-backup-20231201
    $0 -f -d prod-postgres-backup-20231201
EOF
}

# 백업 존재 및 유효성 확인
check_backup() {
    local backup_name="$1"
    log_info "백업 확인: $backup_name"
    
    if ! "$VELERO_CLI" backup describe "$backup_name" &>/dev/null; then
        log_error "백업을 찾을 수 없습니다: $backup_name"
        log_info "사용 가능한 백업 목록:"
        "$VELERO_CLI" backup get --output table | head -10
        exit 1
    fi
    
    local backup_phase
    backup_phase=$("$VELERO_CLI" backup describe "$backup_name" | grep "Phase:" | awk '{print $2}')
    
    if [ "$backup_phase" != "Completed" ] && [ "$backup_phase" != "PartiallyFailed" ]; then
        log_error "백업이 완료되지 않았습니다. 상태: $backup_phase"
        exit 1
    fi
    
    log_success "백업 확인 완료 (상태: $backup_phase)"
}

# 복원 전 안전성 체크
safety_check() {
    log_info "복원 전 안전성 체크..."
    
    # 현재 PostgreSQL 파드 상태 확인
    if kubectl get pod "$POSTGRES_POD" -n "$TARGET_NAMESPACE" &>/dev/null; then
        local pod_status
        pod_status=$(kubectl get pod "$POSTGRES_POD" -n "$TARGET_NAMESPACE" -o jsonpath='{.status.phase}')
        
        if [ "$pod_status" = "Running" ]; then
            log_warning "PostgreSQL 파드가 실행 중입니다: $POSTGRES_POD"
            log_warning "복원 시 서비스 중단이 발생할 수 있습니다."
            
            if [ "${FORCE_RESTORE:-false}" != "true" ]; then
                read -p "계속 진행하시겠습니까? (y/N): " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    log_info "복원이 취소되었습니다."
                    exit 0
                fi
            fi
        fi
    fi
    
    # 현재 백업 생성 (복원 전 백업)
    log_info "복원 전 현재 상태 백업 생성..."
    local pre_restore_backup
    pre_restore_backup="pre-restore-backup-$(date +%Y%m%d-%H%M%S)"
    
    "$VELERO_CLI" backup create "$pre_restore_backup" \
        --include-namespaces "$TARGET_NAMESPACE" \
        --include-resources pods,persistentvolumes,persistentvolumeclaims,statefulsets,secrets,configmaps,services \
        --selector "app.kubernetes.io/name=postgresql" \
        --ttl 24h0m0s
    
    log_success "복원 전 백업 생성 완료: $pre_restore_backup"
}

# PostgreSQL 서비스 중단
stop_postgres_service() {
    log_info "PostgreSQL 서비스 중단 중..."
    
    # StatefulSet 스케일링 다운
    kubectl scale statefulset devops-postgres-postgresql -n "$TARGET_NAMESPACE" --replicas=0
    
    # 파드 완전 종료 대기
    log_info "PostgreSQL 파드 종료 대기 중..."
    kubectl wait --for=delete pod/"$POSTGRES_POD" -n "$TARGET_NAMESPACE" --timeout=300s || {
        log_warning "파드 종료 타임아웃, 강제 삭제 시도"
        kubectl delete pod "$POSTGRES_POD" -n "$TARGET_NAMESPACE" --force --grace-period=0
    }
    
    log_success "PostgreSQL 서비스 중단 완료"
}

# Velero 복원 실행
run_velero_restore() {
    local backup_name="$1"
    log_info "Velero 복원 실행: $RESTORE_NAME (백업: $backup_name)"
    
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
    
    # 드라이 런 모드
    if [ "${DRY_RUN:-false}" = "true" ]; then
        restore_cmd+=("--dry-run")
        log_info "드라이 런 모드로 실행됩니다."
    fi
    
    # 대기 옵션 추가
    restore_cmd+=("--wait")
    
    log_info "복원 명령: ${restore_cmd[*]}"
    "${restore_cmd[@]}"
    
    if [ $? -eq 0 ]; then
        log_success "Velero 복원 완료: $RESTORE_NAME"
    else
        log_error "Velero 복원 실패"
        exit 1
    fi
}

# PostgreSQL 서비스 재시작
start_postgres_service() {
    log_info "PostgreSQL 서비스 재시작 중..."
    
    # StatefulSet 스케일링 업
    kubectl scale statefulset devops-postgres-postgresql -n "$TARGET_NAMESPACE" --replicas=1
    
    # 파드 실행 대기
    log_info "PostgreSQL 파드 실행 대기 중..."
    kubectl wait --for=condition=ready pod/"$POSTGRES_POD" -n "$TARGET_NAMESPACE" --timeout=300s || {
        log_error "PostgreSQL 파드 실행 실패"
        log_info "파드 로그 확인:"
        kubectl logs "$POSTGRES_POD" -n "$TARGET_NAMESPACE" --tail=50
        exit 1
    }
    
    log_success "PostgreSQL 서비스 재시작 완료"
}

# 복원 검증
verify_restore() {
    log_info "복원 검증 중..."
    
    # 복원 상태 확인
    local restore_phase
    restore_phase=$("$VELERO_CLI" restore describe "$RESTORE_NAME" | grep "Phase:" | awk '{print $2}')
    
    if [ "$restore_phase" = "Completed" ]; then
        log_success "복원 검증 성공 (상태: $restore_phase)"
    else
        log_warning "복원이 부분적으로 실패했습니다 (상태: $restore_phase)"
    fi
    
    # PostgreSQL 연결 테스트
    log_info "PostgreSQL 연결 테스트..."
    sleep 10  # 서비스 완전 시작 대기
    
    if kubectl exec "$POSTGRES_POD" -n "$TARGET_NAMESPACE" -- psql -U postgres -c "SELECT 1;" &>/dev/null; then
        log_success "PostgreSQL 연결 테스트 성공"
    else
        log_warning "PostgreSQL 연결 테스트 실패"
    fi
    
    # 복원된 리소스 확인
    log_info "복원된 리소스 확인:"
    kubectl get all -n "$TARGET_NAMESPACE" | grep postgres || true
    kubectl get pvc -n "$TARGET_NAMESPACE" | grep postgres || true
}

# 메인 함수
main() {
    local backup_name=""
    local dry_run=false
    
    # 인자 파싱
    while [[ $# -gt 0 ]]; do
        case $1 in
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
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            -*)
                log_error "알 수 없는 옵션: $1"
                show_usage
                exit 1
                ;;
            *)
                if [ -z "$backup_name" ]; then
                    backup_name="$1"
                else
                    log_error "백업 이름은 하나만 지정할 수 있습니다."
                    show_usage
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    # 백업 이름 확인
    if [ -z "$backup_name" ]; then
        log_error "백업 이름을 지정하세요."
        show_usage
        exit 1
    fi
    
    # 드라이 런 모드가 아닌 경우에만 실제 복원 수행
    if [ "$DRY_RUN" = "false" ]; then
        log_info "=== 운영 PostgreSQL 복원 시작 ==="
        log_info "원본 네임스페이스: $SOURCE_NAMESPACE"
        log_info "대상 네임스페이스: $TARGET_NAMESPACE"
        log_info "복원 이름: $RESTORE_NAME"
        log_info "백업 이름: $backup_name"
        log_info "강제 덮어쓰기: ${FORCE_RESTORE:-false}"
        
        check_backup "$backup_name"
        safety_check
        stop_postgres_service
        run_velero_restore "$backup_name"
        start_postgres_service
        verify_restore
        
        log_success "=== 운영 PostgreSQL 복원 완료 ==="
    else
        log_info "=== 드라이 런 모드 ==="
        log_info "실제 복원은 수행되지 않습니다."
        check_backup "$backup_name"
        log_info "드라이 런 완료"
    fi
}

main "$@"
```

### 3. 운영 환경 백업/복원 실행 예시

```bash
# 1. 운영 PostgreSQL 백업 실행
./ci/velero-backup.sh -b prod-postgres-backup-$(date +%Y%m%d)

# 2. 백업 상태 확인
./ci/velero-backup.sh -d prod-postgres-backup-20231201-120000

# 3. 운영 PostgreSQL 복원 (드라이 런)
./ci/velero-restore.sh -d prod-postgres-backup-20231201-120000

# 4. 운영 PostgreSQL 복원 (실제 실행)
./ci/velero-restore.sh -f prod-postgres-backup-20231201-120000

# 5. 복원 후 검증
kubectl get pods -n devops | grep postgres
kubectl exec -n devops devops-postgres-postgresql-0 -- psql -U postgres -c "SELECT version();"
```

## 🔧 문제 해결

### 1. 일반적인 문제

#### 백업 실패
```bash
# 백업 로그 확인
velero backup logs devops-postgres-backup

# 백업 상세 정보 확인
velero backup describe devops-postgres-backup --details
```

#### MinIO 연결 문제
```bash
# MinIO 서비스 상태 확인
kubectl get svc -n devops | grep minio

# MinIO 파드 상태 확인
kubectl get pods -n devops | grep minio

# MinIO 서비스 재시작
kubectl rollout restart deployment/minio -n devops
```

#### PVC 백업 실패
```bash
# PVC 상태 확인
kubectl get pvc -n devops

# 스토리지 클래스 확인
kubectl get storageclass

# 볼륨 스냅샷 기능 확인
kubectl get volumesnapshotclass
```

### 2. 백업 검증

```bash
# 백업 목록 확인
velero backup get

# 백업 상세 정보 확인
velero backup describe <backup-name>

# 백업 로그 확인
velero backup logs <backup-name>
```

### 3. 복원 검증

```bash
# 복원 목록 확인
velero restore get

# 복원 상세 정보 확인
velero restore describe <restore-name>

# 복원된 리소스 확인
kubectl get all -n devops
kubectl get pvc -n devops
```

## 📊 모니터링

### 1. 백업 상태 모니터링

```bash
# 백업 상태 확인
watch "velero backup get"

# 실시간 백업 로그
velero backup logs -f <backup-name>
```

### 2. 복원 상태 모니터링

```bash
# 복원 상태 확인
watch "velero restore get"

# 복원된 파드 상태 확인
watch "kubectl get pods -n devops"
```

### 3. 스토리지 사용량 확인

```bash
# MinIO 스토리지 사용량 확인
kubectl exec -n devops deployment/minio -- mc du /data

# 백업 크기 확인
velero backup describe <backup-name> | grep -E "(Total items|Items backed up)"
```

## 🔒 보안 고려사항

### 1. 백업 암호화

- Velero는 기본적으로 백업을 암호화하지 않습니다
- 민감한 데이터의 경우 백업 전 암호화를 고려하세요

### 2. 접근 권한

```bash
# Velero RBAC 확인
kubectl get clusterrolebinding | grep velero

# 백업 스토리지 접근 권한 확인
kubectl get secret -n velero | grep cloud-credentials
```

### 3. 백업 보관 정책

- 백업 TTL 설정으로 자동 삭제 관리
- 중요 백업은 별도 저장소에 장기 보관
- 정기적인 백업 테스트 수행

## 📚 참고 자료

### Velero 공식 문서
- [Velero Documentation](https://velero.io/docs/)
- [Velero GitHub Repository](https://github.com/vmware-tanzu/velero)
- [Velero CLI Reference](https://velero.io/docs/main/basic-install/)

### Kubernetes 백업 관련
- [Kubernetes Backup Best Practices](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#backup)
- [Volume Snapshots](https://kubernetes.io/docs/concepts/storage/volume-snapshots/)

### PostgreSQL 백업 관련
- [PostgreSQL Backup Documentation](https://www.postgresql.org/docs/current/backup.html)
- [PostgreSQL in Kubernetes](https://kubernetes.io/docs/tutorials/stateful-application/basic-stateful-set/)

## 🆘 지원

문제가 발생하거나 추가 도움이 필요한 경우:

1. **백업 로그 확인**: `velero backup logs <backup-name>`
2. **복원 로그 확인**: `velero restore logs <restore-name>`
3. **Velero 상태 확인**: `kubectl get pods -n velero`
4. **스토리지 상태 확인**: `kubectl get backupstoragelocation -n velero`

---

**마지막 업데이트**: 2025년 9월 20일  
**작성자**: DevOps Team  
**버전**: 1.0.0
