# 모바일 Voice Interview 로컬 테스트 가이드

## 사전 준비사항

### 1. 필수 요구사항
- ✅ Python 3.12 이상
- ✅ Node.js 18 이상 및 npm
- ✅ OpenAI API 키 (필수)
- ✅ 마이크 권한 (브라우저에서 허용 필요)

### 2. 환경 변수 설정

#### OpenAI API 키 설정
```bash
# .env 파일 또는 환경 변수에 설정
export OPENAI_API_KEY="sk-your-openai-api-key-here"
```

또는 `env` 파일에 추가:
```bash
echo "OPENAI_API_KEY=sk-your-openai-api-key-here" >> env
```

## 로컬 서버 실행

### 방법 1: 자동 실행 스크립트 사용 (권장)

프로젝트에 제공된 스크립트를 사용하면 가장 쉽게 시작할 수 있습니다:

```bash
# 프로젝트 루트 디렉토리에서
cd /Users/dhong/workspaces/drillquiz

# 자동 실행 스크립트 실행
./scripts/deployment/start.sh
```

이 스크립트는:
- Django 서버를 `http://localhost:8000`에서 자동 시작
- Vue 개발 서버를 `http://localhost:8080`에서 자동 시작
- 백그라운드에서 실행되며 로그는 `django.log`, `vue.log`에 저장

**로그 확인:**
```bash
# Django 로그
tail -f django.log

# Vue 로그
tail -f vue.log
```

### 방법 2: 수동 실행

#### 1단계: 백엔드 서버 실행
```bash
# 프로젝트 루트 디렉토리에서
cd /Users/dhong/workspaces/drillquiz

# 가상환경 활성화
source venv/bin/activate

# Django 서버 실행
python manage.py runserver 0.0.0.0:8000
```

백엔드 서버가 `http://localhost:8000`에서 실행됩니다.

#### 2단계: 프론트엔드 서버 실행 (새 터미널)
```bash
# 새 터미널 창에서
cd /Users/dhong/workspaces/drillquiz

# Node.js 경로 설정 (필요시)
export PATH="$PATH:$HOME/.nvm/versions/node/v22.17.0/bin"

# 의존성 설치 (처음 한 번만)
npm install

# Vue 개발 서버 실행 (포트 8080)
FRONTEND_PORT=8080 npm run serve:dev
```

프론트엔드 서버가 `http://localhost:8080`에서 실행됩니다.

### 서버 재시작

서버를 재시작하려면:

```bash
# 실행 중인 서버 종료
kill $(lsof -ti:8000) 2>/dev/null  # Django
kill $(lsof -ti:8080) 2>/dev/null  # Vue

# 또는 스크립트로 재시작
./scripts/deployment/start.sh
```

## 테스트 절차

### 1. 애플리케이션 접속
브라우저에서 `http://localhost:8080` 접속

### 2. 로그인
- 기존 계정으로 로그인하거나
- 새 계정 생성

### 3. AI 모의 인터뷰 지원 시험 선택
- 시험 목록에서 `ai_mock_interview=True`인 시험 선택
- 또는 시험 관리에서 AI 모의 인터뷰 옵션 활성화

### 4. AI 모의 인터뷰 시작

#### 웹 브라우저에서:
1. 시험 상세 페이지에서 "AI 모의 인터뷰" 버튼 클릭
2. 모바일 디바이스로 감지되면 "음성 대화 모드 시작" 버튼 표시
3. 클릭하여 Voice Interview 모드 시작

#### 모바일 브라우저에서:
1. 모바일 기기에서 `http://localhost:8080` 접속 (같은 네트워크)
2. 또는 `http://[로컬IP]:8080` 접속
3. "AI 모의 인터뷰" → "음성 대화 모드 시작"

### 5. 마이크 권한 허용
브라우저에서 마이크 권한 요청 시 "허용" 클릭

### 6. 인터뷰 진행
- AI가 질문을 음성으로 제시
- 마이크에 대고 답변
- 실시간 전사 확인
- AI 피드백 수신

## 테스트 체크리스트

### 기본 기능 테스트
- [ ] 세션 생성 성공
- [ ] WebSocket 연결 성공
- [ ] 마이크 권한 획득
- [ ] 오디오 스트리밍 (송수신)
- [ ] 음성 전사 작동
- [ ] AI 응답 수신

### UI/UX 테스트
- [ ] 진행 상황 표시
- [ ] 질문 표시
- [ ] 실시간 전사 표시
- [ ] 컨트롤 버튼 작동
- [ ] 일시정지/재개 기능

### 오류 처리 테스트
- [ ] 네트워크 끊김 시 재연결
- [ ] 마이크 권한 거부 시 안내
- [ ] 세션 만료 처리

## 문제 해결

### 문제 1: OpenAI API 키 오류
```
에러: "OpenAI API 키가 설정되지 않았습니다."
```
**해결:**
```bash
# 환경 변수 확인
echo $OPENAI_API_KEY

# 설정되지 않았다면
export OPENAI_API_KEY="sk-your-key-here"
```

### 문제 2: WebSocket 연결 실패
```
에러: "WebSocket 연결에 실패했습니다."
```
**해결:**
- 브라우저 콘솔에서 오류 확인
- 네트워크 탭에서 WebSocket 연결 상태 확인
- OpenAI API 키가 올바른지 확인

### 문제 3: 마이크 권한 오류
```
에러: "마이크 권한이 필요합니다."
```
**해결:**
- 브라우저 설정에서 마이크 권한 확인
- HTTPS가 아닌 경우 일부 브라우저에서 마이크 접근 제한
- Chrome: `chrome://settings/content/microphone`

### 문제 4: CORS 오류
```
에러: "CORS policy blocked"
```
**해결:**
- `drillquiz/settings.py`에서 CORS 설정 확인
- `CORS_ALLOWED_ORIGINS`에 `http://localhost:8080` 포함 확인

### 문제 5: 세션 생성 실패
```
에러: "세션 생성에 실패했습니다."
```
**해결:**
- Django 서버 로그 확인: `tail -f django.log`
- OpenAI API 키 유효성 확인
- 네트워크 연결 확인

## 디버깅 팁

### 1. 브라우저 콘솔 확인
- F12 또는 Cmd+Option+I (Mac) / Ctrl+Shift+I (Windows)
- Console 탭에서 오류 메시지 확인
- Network 탭에서 API 요청/응답 확인

### 2. Django 서버 로그 확인
```bash
# 실시간 로그 확인
tail -f django.log

# 또는 직접 실행한 경우 터미널에서 확인
```

### 3. Vue 개발 서버 로그 확인
```bash
# 실시간 로그 확인
tail -f vue.log

# 또는 직접 실행한 경우 터미널에서 확인
```

### 4. 네트워크 요청 확인
브라우저 개발자 도구 → Network 탭:
- `/api/realtime/session/` POST 요청 확인
- WebSocket 연결 확인
- 오디오 스트림 전송 확인

## 로컬 테스트 시 주의사항

### 1. OpenAI API 비용
- Realtime API는 사용량에 따라 비용 발생
- 테스트 시 짧은 시간만 사용 권장

### 2. 마이크 품질
- 조용한 환경에서 테스트
- 마이크가 정상 작동하는지 확인

### 3. 네트워크
- 안정적인 인터넷 연결 필요
- WebSocket 연결 유지 필요

### 4. 브라우저 호환성
- Chrome/Edge 권장 (Web Audio API 지원)
- Safari는 제한적 지원
- Firefox는 기본 지원

## 모바일 디바이스에서 테스트

### 같은 네트워크에서 접속
1. 로컬 IP 확인:
   ```bash
   # Mac
   ifconfig | grep "inet " | grep -v 127.0.0.1
   
   # Linux
   ip addr show | grep "inet " | grep -v 127.0.0.1
   ```

2. 모바일 기기에서 접속:
   ```
   http://[로컬IP]:8080
   예: http://192.168.0.100:8080
   ```

3. Django 서버도 외부 접속 허용:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

### 주의사항
- 방화벽 설정 확인
- 같은 Wi-Fi 네트워크에 연결
- HTTPS가 아닌 HTTP이므로 일부 기능 제한 가능

## 빠른 테스트 스크립트

```bash
#!/bin/bash
# quick-test.sh

# 환경 변수 확인
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY가 설정되지 않았습니다."
    echo "export OPENAI_API_KEY='sk-your-key-here' 실행 후 다시 시도하세요."
    exit 1
fi

# Django 서버 시작
echo "🚀 Django 서버 시작..."
python manage.py runserver 0.0.0.0:8000 &
DJANGO_PID=$!

# 잠시 대기
sleep 3

# Vue 서버 시작
echo "🚀 Vue 개발 서버 시작..."
npm run serve:dev &
VUE_PID=$!

echo ""
echo "✅ 서버가 시작되었습니다!"
echo "   - Django: http://localhost:8000"
echo "   - Vue: http://localhost:8080"
echo ""
echo "종료하려면: kill $DJANGO_PID $VUE_PID"
```

## 다음 단계

테스트 성공 후:
1. 실제 모바일 앱에서 테스트 (Capacitor 빌드)
2. 성능 최적화
3. 추가 기능 구현 (녹화, 평가 등)

## 관련 문서

- [iOS 빌드 및 배포 가이드](./IOS_BUILD_DEPLOY_GUIDE.md) - 모바일 앱 빌드 및 배포
- [빠른 빌드 가이드](./QUICK_BUILD_GUIDE.md) - Vue 코드 변경 후 빠르게 반영하는 방법

