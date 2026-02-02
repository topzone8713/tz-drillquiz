# SEO 문제 해결 가이드

Google Search Console에서 보고되는 SEO 문제들을 해결하는 방법입니다.

## 📋 문제 유형

### 1. Server error (5xx)
**원인**: 서버가 500, 502, 503 등의 오류를 반환
**해결**: 서버 상태 확인 및 오류 로그 분석

### 2. Blocked due to access forbidden (403)
**원인**: 인증이나 권한 문제로 접근 거부
**해결**: Google 크롤러 접근 허용

### 3. Soft 404
**원인**: 존재하지 않는 페이지가 404 대신 200을 반환
**해결**: Vue.js SPA 특성상 모든 경로를 index.html로 서빙 (정상 동작)

### 4. Blocked by robots.txt
**원인**: robots.txt에서 경로 차단
**해결**: robots.txt 설정 확인 및 수정

## 🔍 문제 진단

### 1. Google Search Console에서 확인

1. **Search Console** → **인덱싱** → **페이지** 메뉴
2. 문제가 있는 URL 목록 확인
3. 각 URL에 대해 상세 정보 확인

### 2. 직접 테스트

#### robots.txt 확인
```bash
curl https://us.drillquiz.com/robots.txt
```

#### 특정 URL 확인
```bash
# Google 크롤러 User-Agent로 시뮬레이션
curl -A "Googlebot/2.1 (+http://www.google.com/bot.html)" \
  https://us.drillquiz.com/
```

#### 헬스 체크 확인
```bash
curl https://us.drillquiz.com/api/health/
```

### 3. 서버 로그 확인

```bash
# Kubernetes 환경에서
kubectl logs -n devops deployment/drillquiz --tail=100

# 특정 pod 로그
kubectl logs -n devops <pod-name> --tail=100
```

## 🛠️ 해결 방법

### 문제 1: Server error (5xx)

#### 원인
- 데이터베이스 연결 실패
- 애플리케이션 오류
- 메모리 부족
- 타임아웃

#### 해결
1. **헬스 체크 엔드포인트 확인**
   - `/api/health/` 엔드포인트가 정상 작동하는지 확인
   - 데이터베이스 연결 상태 확인
   - Redis 캐시 연결 상태 확인

2. **서버 로그 확인**
   - 최근 에러 로그 분석
   - 스택 트레이스 확인
   - 반복되는 오류 패턴 확인

3. **리소스 확인**
   - CPU 사용률 확인
   - 메모리 사용률 확인
   - 디스크 사용률 확인

4. **데이터베이스 확인**
   - PostgreSQL 연결 상태
   - 쿼리 성능 문제
   - 데이터베이스 로그

### 문제 2: Blocked due to access forbidden (403)

#### 원인
- 인증이 필요한 경로에 Google 크롤러 접근
- CSRF 토큰 검증 실패
- 권한 체크로 인한 차단

#### 해결

**1. Google 크롤러 접근 허용**

단축 URL 리다이렉션에서 Google 크롤러는 권한 체크를 건너뛰도록 처리:
```python
# Google 크롤러 감지
user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
is_google_crawler = any(bot in user_agent for bot in [
    'googlebot', 'google-inspectiontool', 'googleother',
    'google-extended', 'apis-google', 'mediapartners-google'
])
```

**2. 공개 API 엔드포인트 확인**

- `/api/health/` - ✅ 공개
- `/api/translations/` - ✅ 공개
- `/api/exams/` - 공개 시험만 허용
- `/api/studies/` - 공개 스터디만 허용

**3. CSRF 토큰 처리**

Google 크롤러의 GET 요청은 CSRF 토큰이 필요 없으므로 문제 없음.

### 문제 3: Soft 404

#### 원인
Vue.js SPA 특성상 모든 경로가 index.html을 반환하여 Vue Router가 라우팅합니다.  
Google 크롤러는 JavaScript를 실행하지 않아서 빈 페이지로 보일 수 있습니다.

#### 해결

**1. 메타 태그 최적화**

`public/index.html`에 기본 SEO 메타 태그 추가:
- `<meta name="description">`
- `<meta name="robots" content="index, follow">`
- Open Graph 태그
- Twitter Card 태그

**2. 동적 메타 태그**

Vue Router에서 각 페이지에 대한 메타 태그 동적 설정:
- `vue-meta` 또는 `vue-head` 사용
- 각 라우트에 대한 description, title 설정

**3. Sitemap 최신화**

sitemap.xml을 최신 상태로 유지:
- 존재하는 페이지만 포함
- 최신 lastmod 날짜
- 적절한 priority 설정

**참고**: Soft 404는 Vue.js SPA의 한계입니다. 완전히 해결하려면 SSR(Server-Side Rendering)이나 Prerendering이 필요하지만, 현재는 메타 태그 최적화로 최소화할 수 있습니다.

### 문제 4: Blocked by robots.txt

#### 원인
- robots.txt에서 경로 차단
- 잘못된 robots.txt 설정
- sitemap.xml 경로 차단

#### 해결

**1. robots.txt 확인**

현재 설정:
```
User-agent: *
Allow: /
Allow: /api/health/
Allow: /api/translations/
Allow: /api/exams/
Allow: /api/studies/

# API 경로는 인증이 필요하지만 공개 엔드포인트는 허용
Allow: /api/

Disallow: /admin/
Disallow: /api/users/
Disallow: /api/user-profile/
Disallow: /api/exam-results/
```

**2. robots.txt 테스트**

[Google Search Console robots.txt 테스터](https://search.google.com/test/robots)에서 확인

**3. 주의사항**

- `Disallow: /api/`를 사용하면 모든 API 경로가 차단됨
- 공개 엔드포인트는 명시적으로 `Allow: /api/health/` 등으로 허용

## 📊 모니터링

### 1. Google Search Console

- **인덱싱** → **페이지**: 인덱싱된 페이지 확인
- **성능**: 검색 트래픽 확인
- **URL 검사**: 특정 URL 상태 확인

### 2. 서버 로그

- 403 오류 로그 모니터링
- 5xx 오류 로그 모니터링
- Google 크롤러 접근 로그 확인

### 3. 헬스 체크

```bash
# 주기적으로 헬스 체크 실행
curl https://us.drillquiz.com/api/health/
```

## ✅ 체크리스트

### 기본 설정
- [ ] robots.txt 올바르게 설정
- [ ] sitemap.xml 최신 상태
- [ ] 공개 엔드포인트 접근 가능
- [ ] 메타 태그 설정 완료

### 서버 상태
- [ ] 헬스 체크 엔드포인트 정상 작동
- [ ] 데이터베이스 연결 정상
- [ ] 서버 오류 없음
- [ ] 리소스 사용량 정상

### Google 크롤러 접근
- [ ] Google 크롤러 접근 허용
- [ ] 공개 페이지 접근 가능
- [ ] 403 오류 없음
- [ ] 5xx 오류 없음

## 🔗 관련 문서

- [Google Search Console 설정 가이드](./GOOGLE_SEARCH_CONSOLE_SETUP.md)
- [robots.txt 사양](https://www.robotstxt.org/)
- [Google 크롤러 User-Agent](https://support.google.com/webmasters/answer/1061943)

## 📝 참고사항

1. **Vue.js SPA 제한사항**: JavaScript가 필요하므로 Google 크롤러가 모든 콘텐츠를 인덱싱하지 못할 수 있습니다. 이는 정상적인 동작입니다.

2. **Soft 404**: 존재하지 않는 경로에 접근해도 Vue Router가 처리하므로 Soft 404가 발생할 수 있습니다. 중요한 페이지는 sitemap.xml에 포함시키세요.

3. **인덱싱 시간**: 수정 후 Google에 반영되기까지 **1~2주** 소요될 수 있습니다.

4. **Google 크롤러 IP 확인**: 필요시 [Google 크롤러 IP 주소](https://developers.google.com/search/apis/ipranges/googlebot.json)를 확인하여 서버 로그에서 필터링할 수 있습니다.

