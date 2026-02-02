#!/bin/bash

# 운영 DB를 사용하여 로컬 Django 서버 시작 스크립트

cd /Users/dhong/workspaces/drillquiz

# 기존 서버 종료
lsof -ti:8000 | xargs kill -9 2>/dev/null

# 가상환경 활성화
source venv/bin/activate

# 운영 DB 환경 변수 설정
export USE_DOCKER=true
export POSTGRES_DB=drillquiz
export POSTGRES_USER=admin
export POSTGRES_PASSWORD='DevOps!323'
export POSTGRES_HOST=localhost
export POSTGRES_PORT=64671

# Django 서버 시작
echo "🚀 Django 서버를 운영 DB에 연결하여 시작합니다..."
echo "   Database: $POSTGRES_DB"
echo "   Host: $POSTGRES_HOST:$POSTGRES_PORT"
echo "   User: $POSTGRES_USER"
echo ""
python manage.py runserver 0.0.0.0:8000

