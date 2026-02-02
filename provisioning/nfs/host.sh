#!/usr/bin/env bash

## NFS 서버 설치 스크립트 (Ubuntu/Debian)
##
## 이 스크립트는 호스트 서버에 NFS 서버를 설치하고 구성합니다.
##
## 사용법:
##   sudo bash host.sh [NFS_SERVER_IP] [NETWORK_CIDR]
##
## 예제:
##   sudo bash host.sh 192.168.0.139 192.168.0.0/16
##
## 파라미터:
##   NFS_SERVER_IP: NFS 서버의 IP 주소 (기본값: 자동 감지)
##   NETWORK_CIDR: 접근 허용 네트워크 대역 (기본값: 192.168.0.0/16)

set -e

# 기본값 설정
NFS_SERVER_IP="${1:-$(hostname -I | awk '{print $1}')}"
NETWORK_CIDR="${2:-192.168.0.0/16}"
NFS_PATH="/srv/nfs"

echo "=========================================="
echo "NFS 서버 설치 스크립트"
echo "=========================================="
echo "NFS 서버 IP: ${NFS_SERVER_IP}"
echo "네트워크 대역: ${NETWORK_CIDR}"
echo "NFS 경로: ${NFS_PATH}"
echo "=========================================="
echo ""

# root 권한 확인
if [ "$EUID" -ne 0 ]; then 
    echo "Error: 이 스크립트는 root 권한으로 실행해야 합니다."
    echo "Usage: sudo bash $0"
    exit 1
fi

# 1. NFS 서버 패키지 설치
echo "[1/5] NFS 서버 패키지 설치 중..."
apt update
apt install -y nfs-kernel-server

# 2. NFS 공유 디렉토리 생성 및 권한 설정
echo "[2/5] NFS 공유 디렉토리 생성 중..."
mkdir -p ${NFS_PATH}
chown nobody:nogroup ${NFS_PATH}
chmod 755 ${NFS_PATH}
echo "✓ 디렉토리 생성 완료: ${NFS_PATH}"

# 3. /etc/exports 파일 설정
echo "[3/5] /etc/exports 파일 설정 중..."

# 네트워크 대역을 /etc/exports 형식으로 변환 (192.168.0.0/16 -> 192.168.0.0/16)
# 이미 CIDR 형식이면 그대로 사용
NETWORK_RANGE="${NETWORK_CIDR}"

# /etc/exports 백업
if [ -f /etc/exports ]; then
    cp /etc/exports /etc/exports.backup.$(date +%Y%m%d_%H%M%S)
    echo "✓ 기존 /etc/exports 백업 완료"
fi

# 기존 설정에서 해당 경로 제거 (중복 방지)
if grep -q "^${NFS_PATH}" /etc/exports 2>/dev/null; then
    sed -i "\|^${NFS_PATH}|d" /etc/exports
    echo "✓ 기존 ${NFS_PATH} 설정 제거"
fi

# 새로운 설정 추가
EXPORT_LINE="${NFS_PATH} ${NETWORK_RANGE}(rw,sync,no_subtree_check,no_root_squash,insecure)"
echo "${EXPORT_LINE}" >> /etc/exports
echo "✓ /etc/exports에 다음 설정 추가:"
echo "  ${EXPORT_LINE}"

# 4. NFS 서버 재시작 및 활성화
echo "[4/5] NFS 서버 재시작 및 활성화 중..."
exportfs -ra 2>/dev/null || true
systemctl restart nfs-server 2>/dev/null || systemctl restart nfs-kernel-server
systemctl enable nfs-server 2>/dev/null || systemctl enable nfs-kernel-server

# NFS 서버 상태 확인 (서비스가 시작될 때까지 대기)
sleep 2
if systemctl is-active --quiet nfs-server || systemctl is-active --quiet nfs-kernel-server; then
    echo "✓ NFS 서버 실행 중"
else
    echo "⚠ NFS 서버 상태 확인 중..."
    systemctl status nfs-server 2>/dev/null || systemctl status nfs-kernel-server 2>/dev/null || true
    # exportfs가 정상이면 계속 진행 (서비스는 나중에 시작될 수 있음)
    if command -v exportfs >/dev/null 2>&1; then
        echo "✓ NFS 서비스가 시작 중입니다. 잠시 후 정상 작동할 것입니다."
    else
        echo "✗ NFS 서버 설치에 문제가 있습니다."
        exit 1
    fi
fi

# 5. 설정 확인
echo "[5/5] 설정 확인 중..."
echo ""
echo "공유 목록:"
exportfs -v | grep "${NFS_PATH}" || echo "경고: ${NFS_PATH}가 공유 목록에 없습니다."

echo ""
echo "=========================================="
echo "NFS 서버 설치 완료!"
echo "=========================================="
echo ""
echo "설정 요약:"
echo "  - NFS 서버 IP: ${NFS_SERVER_IP}"
echo "  - NFS 경로: ${NFS_PATH}"
echo "  - 접근 허용 네트워크: ${NETWORK_CIDR}"
echo ""
echo "테스트 방법:"
echo "  showmount -e localhost"
echo "  showmount -e ${NFS_SERVER_IP}"
echo ""
echo "다음 단계:"
echo "  1. Kubernetes 클러스터에서 NFS 서버 접근 가능 여부 확인"
echo "  2. provisioning/nfs/install.sh 실행하여 NFS 프로비저너 설치"
echo ""

exit 0

