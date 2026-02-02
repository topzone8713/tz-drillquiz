#!/usr/bin/env bash

# [3/4] 프로비저닝 설치와 [4/4] 설치 검증만 실행하는 스크립트
# SSH 세션이 끊어져서 중지된 경우 이 스크립트로 계속 진행

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/install.log"

# 모든 출력을 로그 파일과 콘솔에 동시 기록
exec > >(tee -a "${LOG_FILE}") 2>&1

echo ""
echo "=========================================="
echo "[3/4] 프로비저닝 설치"
echo "=========================================="
echo ""

cd "${SCRIPT_DIR}"

echo "프로비저닝 설치 중..."
echo "  (이 작업은 20-40분 정도 소요됩니다)"
echo "  모든 로그는 install.log 파일에 기록됩니다."
echo ""

# install.sh 실행
echo ">>> install.sh 실행 시작 <<<"
bash install.sh

if [ $? -ne 0 ]; then
  echo -e "${RED}Error: 프로비저닝 설치 실패${NC}"
  echo "로그를 확인하세요: install.log"
  exit 1
fi
echo ">>> install.sh 실행 완료 <<<"

echo ""
echo -e "${GREEN}✓ 프로비저닝 설치 완료${NC}"

echo ""
echo "자동 모드: 설치 검증을 시작합니다..."
sleep 2

echo ""
echo "=========================================="
echo "[4/4] 설치 검증"
echo "=========================================="
echo ""

cd "${SCRIPT_DIR}"

# verify_installation.sh 실행
if [ -f "${SCRIPT_DIR}/verify_installation.sh" ]; then
  echo ">>> verify_installation.sh 실행 시작 <<<"
  bash "${SCRIPT_DIR}/verify_installation.sh"
  echo ">>> verify_installation.sh 실행 완료 <<<"
else
  echo -e "${YELLOW}Warning: verify_installation.sh를 찾을 수 없습니다.${NC}"
  echo "수동으로 검증하세요."
fi

echo ""
echo "=========================================="
echo -e "${GREEN}프로비저닝 설치 및 검증 완료!${NC}"
echo "=========================================="
echo ""
echo "종료 시간: $(date)"
echo ""
echo "모든 로그는 다음 파일에 기록되었습니다:"
echo "  ${LOG_FILE}"
echo ""
