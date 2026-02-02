#!/usr/bin/env bash

# Ubuntu 계정에 sudo 권한 추가 스크립트
# 사용법: ./add-ubuntu-sudo.sh

set -e

echo "=========================================="
echo "Ubuntu 계정 sudo 권한 추가"
echo "=========================================="
echo ""

# SSH로 my-ubuntu에 접속하여 ubuntu 계정에 sudo 권한 추가
echo "my-ubuntu 서버에 접속하여 ubuntu 계정에 sudo 권한을 추가합니다..."

ssh my-ubuntu "echo 'hdh971097' | sudo -S bash -c '
    # ubuntu 계정을 sudo 그룹에 추가 (이미 있을 수 있음)
    usermod -aG sudo ubuntu
    
    # 비밀번호 없이 sudo 사용 가능하도록 설정
    echo \"ubuntu ALL=(ALL) NOPASSWD:ALL\" > /etc/sudoers.d/ubuntu-nopasswd
    chmod 0440 /etc/sudoers.d/ubuntu-nopasswd
    
    # sudoers 파일 문법 검증
    visudo -c
    
    echo \"✅ Ubuntu 계정 sudo 권한 설정 완료\"
    echo \"✅ Ubuntu 계정은 이제 비밀번호 없이 sudo 명령을 사용할 수 있습니다.\"
'"

echo ""
echo "=========================================="
echo "완료!"
echo "=========================================="
echo ""
echo "확인: ssh my-ubuntu로 접속 후 다음 명령으로 확인하세요:"
echo "  groups ubuntu"
echo "  sudo whoami"
