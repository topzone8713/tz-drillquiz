#!/bin/bash

# 환경 설정
ENVIRONMENT=${ENVIRONMENT:-development}
echo "환경: $ENVIRONMENT"

# 인자 확인
if [ "$1" = "docker" ]; then
    echo "DrillQuiz Docker (PostgreSQL) 시작 중..."
    DOCKER_MODE=true
elif [ "$1" = "prod" ]; then
    echo "DrillQuiz 프로덕션 모드 시작 중..."
    DOCKER_MODE=false
    ENVIRONMENT=production
else
    echo "DrillQuiz 로컬 (SQLite) 시작 중..."
    DOCKER_MODE=false
fi

if [ "$DOCKER_MODE" = true ]; then
    # Docker 모드 - PostgreSQL 사용
    
    # Docker가 설치되어 있는지 확인
    if ! command -v docker &> /dev/null; then
        echo "Docker가 설치되어 있지 않습니다. Docker를 먼저 설치해주세요."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        echo "Docker Compose가 설치되어 있지 않습니다. Docker Compose를 먼저 설치해주세요."
        exit 1
    fi

    # 기존 컨테이너 중지 및 제거
    echo "기존 컨테이너를 정리합니다..."
    docker-compose down

    # Docker 이미지 빌드
    echo "Docker 이미지를 빌드합니다..."
    docker-compose build

    # 컨테이너 시작
    echo "컨테이너를 시작합니다..."
    docker-compose up -d

    # 컨테이너 상태 확인
    echo "컨테이너 상태를 확인합니다..."
    docker-compose ps

    # 환경변수에서 서버 설정 가져오기
    DJANGO_HOST=${DJANGO_HOST:-localhost}
    DJANGO_PORT=${DJANGO_PORT:-8000}
    FRONTEND_HOST=${FRONTEND_HOST:-localhost}
    FRONTEND_PORT=${FRONTEND_PORT:-8080}
    
    echo ""
    echo "DrillQuiz가 성공적으로 시작되었습니다! (PostgreSQL)"
    echo ""
    echo "접속 URL:"
    echo "- 프론트엔드: http://${FRONTEND_HOST}:${FRONTEND_PORT}"
    echo "- 백엔드 API: http://${DJANGO_HOST}:${DJANGO_PORT}"
    echo "- Django 관리자: http://${DJANGO_HOST}:${DJANGO_PORT}/admin"
    echo ""
    echo "로그 확인:"
    echo "- 전체 로그: docker-compose logs -f"
    echo "- 백엔드 로그: docker-compose logs -f backend"
    echo "- 프론트엔드 로그: docker-compose logs -f frontend"
    echo "- 데이터베이스 로그: docker-compose logs -f db"
    echo ""
    echo "컨테이너 중지: ./stop.sh"
    echo "컨테이너 재시작: docker-compose restart"

else
    # 로컬 모드 - SQLite 사용
    
    echo "Python 가상환경을 확인합니다..."
    
    # Python 가상환경 확인 및 생성
    if [ ! -d "venv" ]; then
        echo "Python 가상환경을 생성합니다..."
        python3 -m venv venv
    fi

    # 가상환경 활성화
    echo "가상환경을 활성화합니다..."
    source venv/bin/activate

    # Python 의존성 설치
    echo "Python 의존성을 설치합니다..."
    pip install -r requirements.txt

    # 환경 변수 설정
    echo "환경 변수를 설정합니다..."
    export ENVIRONMENT=$ENVIRONMENT
    export USE_DOCKER=false
    export DEBUG=$([ "$ENVIRONMENT" = "production" ] && echo "False" || echo "True")
    
    # 운영 환경에서 필수 환경 변수가 설정되지 않은 경우 기본값 설정
    if [ "$ENVIRONMENT" = "production" ]; then
        echo "운영 환경 설정을 확인합니다..."
        
        # ALLOWED_HOSTS가 설정되지 않은 경우 기본값 설정
        if [ -z "$ALLOWED_HOSTS" ]; then
            export ALLOWED_HOSTS="localhost,127.0.0.1,*"
            echo "⚠️  ALLOWED_HOSTS가 설정되지 않아 기본값을 사용합니다: $ALLOWED_HOSTS"
        fi

        # CSRF_TRUSTED_ORIGINS가 설정되지 않은 경우 기본값 설정
        if [ -z "$CSRF_TRUSTED_ORIGINS" ]; then
            export CSRF_TRUSTED_ORIGINS="http://localhost:8080,http://127.0.0.1:8080,http://localhost:8000,http://127.0.0.1:8000"
            echo "⚠️  CSRF_TRUSTED_ORIGINS가 설정되지 않아 기본값을 사용합니다: $CSRF_TRUSTED_ORIGINS"
        fi

        # CORS_ALLOWED_ORIGINS가 설정되지 않은 경우 모든 도메인 허용
        if [ -z "$CORS_ALLOWED_ORIGINS" ]; then
            export CORS_ALLOW_ALL_ORIGINS="True"
            echo "⚠️  CORS_ALLOWED_ORIGINS가 설정되지 않아 모든 도메인을 허용합니다."
        fi
    fi
    
    # Django 설정을 SQLite로 변경
    echo "Django 설정을 SQLite로 변경합니다..."

    # Django 마이그레이션
    echo "Django 마이그레이션을 실행합니다..."
    python manage.py makemigrations
    python manage.py migrate

    # 번역 자동화 실행
    echo "번역 자동화를 실행합니다..."
    if [ -f "scripts/translation-extractor.py" ]; then
        python scripts/translation-extractor.py
    else
        echo "⚠️  번역 자동화 스크립트가 없습니다. 수동으로 실행해주세요."
    fi

    # Node.js 확인
    echo "Node.js를 확인합니다..."
    if ! command -v node &> /dev/null; then
        echo ""
        echo "⚠️  경고: Node.js가 설치되어 있지 않거나 PATH에 없습니다."
        echo ""
        echo "Node.js 설치 및 PATH 설정 방법:"
        echo ""
        echo "1. nvm을 사용하는 경우:"
        echo "   source ~/.nvm/nvm.sh"
        echo "   nvm use node"
        echo ""
        echo "2. Homebrew를 사용하는 경우:"
        echo "   brew install node"
        echo ""
        echo "3. 수동으로 PATH 설정하는 경우:"
        echo "   export PATH=\$PATH:/Users/dhong/.nvm/versions/node/v22.17.0/bin"
        echo ""
        echo "4. .zshrc 또는 .bashrc에 추가하는 경우:"
        echo "   echo 'export PATH=\$PATH:/Users/dhong/.nvm/versions/node/v22.17.0/bin' >> ~/.zshrc"
        echo "   source ~/.zshrc"
        echo ""
        echo "Node.js 설치 후 다시 ./start.sh를 실행해주세요."
        echo ""
        # 환경변수에서 서버 설정 가져오기
        DJANGO_HOST=${DJANGO_HOST:-localhost}
        DJANGO_PORT=${DJANGO_PORT:-8000}
        
        echo "Django 서버만 시작합니다..."
        nohup bash -c "export USE_DOCKER=false && python manage.py runserver" > django.log 2>&1 &
        echo "Django 서버가 백그라운드에서 실행 중입니다."
        echo "- Django 서버: http://${DJANGO_HOST}:${DJANGO_PORT}"
        echo "- Django 관리자: http://${DJANGO_HOST}:${DJANGO_PORT}/admin"
        echo ""
        echo "로그 확인:"
        echo "- Django 로그: tail -f django.log"
        echo ""
        echo "Vue 개발 서버는 Node.js 설치 후 수동으로 시작해주세요:"
        echo "npm install && npm run serve"
        exit 0
    fi

    if ! command -v npm &> /dev/null; then
        echo ""
        echo "⚠️  경고: npm이 설치되어 있지 않거나 PATH에 없습니다."
        echo ""
        echo "npm 설치 및 PATH 설정 방법:"
        echo ""
        echo "1. nvm을 사용하는 경우:"
        echo "   source ~/.nvm/nvm.sh"
        echo "   nvm use node"
        echo ""
        echo "2. 수동으로 PATH 설정하는 경우:"
        echo "   export PATH=\$PATH:/Users/dhong/.nvm/versions/node/v22.17.0/bin"
        echo ""
        echo "3. .zshrc 또는 .bashrc에 추가하는 경우:"
        echo "   echo 'export PATH=\$PATH:/Users/dhong/.nvm/versions/node/v22.17.0/bin' >> ~/.zshrc"
        echo "   source ~/.zshrc"
        echo ""
        echo "npm 설치 후 다시 ./start.sh를 실행해주세요."
        echo ""
        # 환경변수에서 서버 설정 가져오기
        DJANGO_HOST=${DJANGO_HOST:-localhost}
        DJANGO_PORT=${DJANGO_PORT:-8000}
        
        echo "Django 서버만 시작합니다..."
        nohup bash -c "export USE_DOCKER=false && python manage.py runserver" > django.log 2>&1 &
        echo "Django 서버가 백그라운드에서 실행 중입니다."
        echo "- Django 서버: http://${DJANGO_HOST}:${DJANGO_PORT}"
        echo "- Django 관리자: http://${DJANGO_HOST}:${DJANGO_PORT}/admin"
        echo ""
        echo "로그 확인:"
        echo "- Django 로그: tail -f django.log"
        echo ""
        echo "Vue 개발 서버는 npm 설치 후 수동으로 시작해주세요:"
        echo "npm install && npm run serve"
        exit 0
    fi

    echo "Node.js 버전: $(node --version)"
    echo "npm 버전: $(npm --version)"

    # Node.js 의존성 설치
    echo "Node.js 의존성을 설치합니다..."
    npm install

    # Vue 앱 빌드
    echo "Vue 앱을 빌드합니다..."
    if [ "$ENVIRONMENT" = "production" ]; then
        npm run build:prod
    else
        npm run build:dev
    fi

    echo ""
    echo "DrillQuiz가 성공적으로 준비되었습니다! (SQLite)"
    echo ""
    echo "서버를 시작하려면:"
    echo "- Django 서버: python manage.py runserver"
    echo "- Vue 개발 서버: npm run serve"
    echo ""
    echo "또는 Docker 모드로 실행하려면: ./start.sh docker"
    echo ""
    # 환경변수에서 서버 설정 가져오기
    DJANGO_HOST=${DJANGO_HOST:-localhost}
    DJANGO_PORT=${DJANGO_PORT:-8000}
    FRONTEND_HOST=${FRONTEND_HOST:-localhost}
    FRONTEND_PORT=${FRONTEND_PORT:-8080}
    
    echo "서버를 자동으로 시작합니다..."
    nohup bash -c "export ENVIRONMENT=$ENVIRONMENT && export USE_DOCKER=false && export DEBUG=$([ "$ENVIRONMENT" = "production" ] && echo "False" || echo "True") && export ALLOWED_HOSTS=\"$ALLOWED_HOSTS\" && export CSRF_TRUSTED_ORIGINS=\"$CSRF_TRUSTED_ORIGINS\" && export CORS_ALLOWED_ORIGINS=\"$CORS_ALLOWED_ORIGINS\" && export CORS_ALLOW_ALL_ORIGINS=\"$CORS_ALLOW_ALL_ORIGINS\" && python manage.py runserver 0.0.0.0:8000" > django.log 2>&1 &
    if [ "$ENVIRONMENT" = "production" ]; then
        # 운영 환경에서는 빌드된 파일을 nginx나 다른 웹 서버로 서빙해야 하지만,
        # 개발 편의를 위해 개발 서버를 사용하되 경고 메시지 출력
        echo "⚠️  운영 환경에서는 빌드된 파일을 웹 서버로 서빙하는 것을 권장합니다."
        nohup npm run serve:prod > vue.log 2>&1 &
    else
        nohup npm run serve:dev > vue.log 2>&1 &
    fi
    echo "서버가 백그라운드에서 실행 중입니다."
    echo "- Django 서버: http://${DJANGO_HOST}:${DJANGO_PORT}"
    echo "- Vue 개발 서버: http://${FRONTEND_HOST}:${FRONTEND_PORT}"
    echo ""
    echo "로그 확인:"
    echo "- Django 로그: tail -f django.log"
    echo "- Vue 로그: tail -f vue.log"
fi 

