#!/bin/bash

# 인자 확인
if [ "$1" = "docker" ]; then
    echo "DrillQuiz Docker 서비스 종료 중..."
    DOCKER_MODE=true
else
    echo "DrillQuiz 로컬 서비스 종료 중..."
    DOCKER_MODE=false
fi

if [ "$DOCKER_MODE" = true ]; then
    # Docker 모드 종료
    
    # Docker가 설치되어 있는지 확인
    if ! command -v docker &> /dev/null; then
        echo "Docker가 설치되어 있지 않습니다."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        echo "Docker Compose가 설치되어 있지 않습니다."
        exit 1
    fi

    # 실행 중인 컨테이너 확인
    echo "실행 중인 컨테이너를 확인합니다..."
    docker-compose ps

    # 컨테이너 중지
    echo "컨테이너를 중지합니다..."
    docker-compose down
    echo "컨테이너가 중지되었습니다."

    echo ""
    echo "DrillQuiz Docker 서비스가 종료되었습니다."
    echo ""
    echo "다시 시작하려면: ./start.sh docker"
    echo "또는: docker-compose up -d"

else
    # 로컬 모드 종료
    
    echo "로컬 서버 프로세스를 종료합니다..."
    
    # Django 서버 종료
    pkill -f "manage.py runserver"
    
    # Vue 개발 서버 종료
    pkill -f "npm run serve"
    
    # Node.js 프로세스 종료 (포트 8080 사용)
    lsof -ti:8080 | xargs kill -9 2>/dev/null || true
    
    # Python 프로세스 종료 (포트 8000 사용)
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    
    echo ""
    echo "DrillQuiz 로컬 서비스가 종료되었습니다."
    echo ""
    echo "다시 시작하려면: ./start.sh"
    echo "또는 Docker 모드로 시작: ./start.sh docker"
fi 