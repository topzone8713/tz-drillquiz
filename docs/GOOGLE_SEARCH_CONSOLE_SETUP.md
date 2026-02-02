# Google Search Console 설정 가이드

Google에서 "drillquiz"로 검색했을 때 사이트가 나타나도록 설정하는 방법입니다.

## ⚠️ 중요: 반드시 등록해야 합니다!

현재 `drillquiz.com`과 `us.drillquiz.com`이 Google 검색에서 나타나지 않는 이유는 **Google Search Console에 등록되지 않았기 때문**입니다. 아래 단계를 따라 반드시 등록해야 합니다.

## 📋 개요

Google Search Console에 사이트를 등록하고 sitemap을 제출하면 Google이 사이트를 크롤링하고 검색 결과에 포함시킵니다.

**두 개의 속성을 모두 등록해야 합니다:**
1. `https://drillquiz.com` (또는 도메인 방식으로 `drillquiz.com`)
2. `https://us.drillquiz.com`

## 1단계: Google Search Console 접속

1. [Google Search Console](https://search.google.com/search-console) 접속
2. Google 계정으로 로그인
3. **속성 추가** 클릭

## 2단계: 속성(Property) 추가 - 첫 번째: drillquiz.com

### 방법 1: URL 접두어 방식 (권장)

1. **URL 접두어** 선택
2. 사이트 URL 입력:
   ```
   https://drillquiz.com
   ```
3. **계속** 클릭

### 방법 2: 도메인 방식 (더 포괄적)

1. **도메인** 선택
2. 도메인 입력:
   ```
   drillquiz.com
   ```
3. **계속** 클릭
   
   **참고**: 도메인 방식을 사용하면 `drillquiz.com`, `www.drillquiz.com`, `us.drillquiz.com` 등 모든 서브도메인이 포함됩니다.

## 2-2단계: 속성(Property) 추가 - 두 번째: us.drillquiz.com

첫 번째 속성 등록 후, 다시 **속성 추가**를 클릭하여 두 번째 속성을 추가합니다.

1. **URL 접두어** 선택
2. 사이트 URL 입력:
   ```
   https://us.drillquiz.com
   ```
3. **계속** 클릭

## 3단계: 소유권 확인

Google Search Console에서 사이트 소유권을 확인해야 합니다.

### 방법 1: HTML 파일 업로드 (가장 간단)

**이 파일은 무엇인가요?**
- Google Search Console에서 사이트 소유권을 확인하기 위해 제공하는 HTML 파일입니다
- 파일 이름은 `google`로 시작하고 랜덤한 문자열이 포함됩니다 (예: `google1234567890abcdef.html`)
- 파일 내용은 매우 간단한 HTML이며, Google이 이 파일에 접근할 수 있으면 사이트 소유권을 확인합니다

**어디서 얻을 수 있나요?**
1. Google Search Console에서 속성을 추가할 때 소유권 확인 단계에서 제공됩니다
2. **HTML 파일** 방식 선택
3. Google이 자동으로 생성한 파일을 다운로드할 수 있는 링크가 표시됩니다
4. 파일 이름은 `google`로 시작하는 랜덤한 문자열입니다 (예: `google1234567890abcdef.html`)

**사용 방법:**
1. Google Search Console에서 **HTML 파일** 방식 선택
2. 제공된 HTML 파일 다운로드 버튼 클릭 (파일 이름은 `google`로 시작)
3. 다운로드한 파일을 프로젝트의 `public/` 디렉토리에 복사
   ```bash
   # 예시
   cp ~/Downloads/google1234567890abcdef.html /Users/dhong/workspaces/drillquiz/public/
   ```
4. 파일을 커밋하고 배포
5. 배포 후 `https://us.drillquiz.com/google1234567890abcdef.html` 접속하여 파일이 보이는지 확인
   - 파일 내용이 표시되면 정상입니다
6. Google Search Console에서 **확인** 버튼 클릭

**참고:**
- 파일 이름의 `1234567890abcdef` 부분은 Google이 생성한 고유한 문자열입니다
- 실제 파일 이름은 Google Search Console에서 제공하는 이름을 그대로 사용해야 합니다

### 방법 2: HTML 태그 방식

1. **HTML 태그** 방식 선택
2. 제공된 메타 태그 복사 (예: `<meta name="google-site-verification" content="abc123..."/>`)
3. `public/index.html` 파일의 `<head>` 섹션에 추가:
   ```html
   <head>
     <!-- 기존 메타 태그들 -->
     <meta name="google-site-verification" content="abc123..." />
   </head>
   ```
4. 변경사항 커밋 및 배포
5. Search Console에서 **확인** 클릭

### 방법 3: Google Analytics 방식 (이미 GA 사용 중인 경우)

1. **Google Analytics** 방식 선택
2. Google Analytics 계정이 이미 연결되어 있으면 자동으로 확인됨
3. **확인** 클릭

### 방법 4: DNS 레코드 방식

1. **도메인 이름 제공업체** 방식 선택
2. 제공된 TXT 레코드를 DNS에 추가:
   ```
   Type: TXT
   Name: @
   Value: google-site-verification=abc123...
   ```
3. DNS 전파 대기 (몇 분~몇 시간 소요)
4. Search Console에서 **확인** 클릭

**권장**: HTML 파일 업로드 방식이 가장 간단하고 빠릅니다.

## 4단계: Sitemap 제출

소유권 확인 후 각 속성에 대해 sitemap을 제출합니다.

### drillquiz.com 속성에 sitemap 제출

1. `drillquiz.com` 속성에서 좌측 메뉴 → **Sitemaps** 선택
2. **새 sitemap 추가** 클릭
3. Sitemap URL 입력:
   ```
   https://drillquiz.com/sitemap.xml
   ```
4. **제출** 클릭

### us.drillquiz.com 속성에 sitemap 제출

1. `us.drillquiz.com` 속성으로 전환
2. 좌측 메뉴 → **Sitemaps** 선택
3. **새 sitemap 추가** 클릭
4. Sitemap URL 입력:
   ```
   https://us.drillquiz.com/sitemap.xml
   ```
5. **제출** 클릭

**참고**: sitemap.xml은 이제 동적으로 생성되므로 각 도메인에 맞게 자동으로 생성됩니다.

## 5단계: 인덱싱 요청 (강력 권장)

특정 페이지를 빠르게 인덱싱하고 싶은 경우:

### drillquiz.com 인덱싱 요청

1. `drillquiz.com` 속성에서 좌측 메뉴 → **URL 검사** 선택
2. 인덱싱하려는 URL 입력:
   ```
   https://drillquiz.com/
   ```
3. **인덱싱 요청** 클릭
4. Google이 크롤링하고 인덱싱함 (보통 몇 시간~며칠 소요)

### us.drillquiz.com 인덱싱 요청

1. `us.drillquiz.com` 속성으로 전환
2. 좌측 메뉴 → **URL 검사** 선택
3. 인덱싱하려는 URL 입력:
   ```
   https://us.drillquiz.com/
   ```
4. **인덱싱 요청** 클릭

## 6단계: 확인 및 모니터링

### 인덱싱 확인

1. **인덱싱** → **페이지** 메뉴에서 인덱싱된 페이지 확인
2. 인덱싱 상태 모니터링

### 검색 성능 확인

1. **성능** 메뉴에서 검색 트래픽 확인
2. 노출 수, 클릭 수, 평균 순위 등 확인

### 문제 확인

1. **보안 문제** 메뉴에서 보안 문제 확인
2. **수동 조치** 메뉴에서 Google의 수동 조치 확인
3. **핵심 웹 바이탈** 메뉴에서 사이트 성능 확인

## 자주 묻는 질문

### Q: 사이트를 등록한 후 언제 검색 결과에 나타나나요?

**A:** 
- 일반적으로 **1~2주** 소요
- sitemap 제출 후 **몇 일~몇 주** 내에 크롤링 시작
- 페이지 인덱싱은 **몇 주~몇 달** 걸릴 수 있음
- 새 사이트는 더 오래 걸릴 수 있음

### Q: "drillquiz"로 검색했는데 여전히 나타나지 않아요

**A:** 
1. **사이트 등록 확인**: Search Console에서 `drillquiz.com`과 `us.drillquiz.com` 모두 등록되어 있는지 확인
2. **Sitemap 제출 확인**: 각 속성에 대해 sitemap이 제출되어 있고 오류가 없는지 확인
3. **인덱싱 확인**: "인덱싱" 메뉴에서 페이지가 인덱싱되었는지 확인 (보통 처음에는 0개로 표시됨)
4. **시간 대기**: 
   - sitemap 제출 후 크롤링 시작까지: **1~2주**
   - 인덱싱 완료까지: **2~4주**
   - 검색 결과에 나타나기까지: **1~2개월**
5. **키워드 경쟁**: "drillquiz"라는 키워드로 경쟁하는 다른 사이트가 있을 수 있음
6. **robots.txt 확인**: `https://drillquiz.com/robots.txt`와 `https://us.drillquiz.com/robots.txt`가 크롤링을 허용하는지 확인

### Q: 특정 URL만 인덱싱하고 싶어요

**A:**
1. Search Console → **URL 검사** 메뉴
2. 인덱싱하려는 URL 입력
3. **인덱싱 요청** 클릭

### Q: robots.txt가 사이트 크롤링을 차단하고 있어요

**A:**
1. `public/robots.txt` 파일 확인
2. `Disallow: /` 또는 잘못된 설정이 있는지 확인
3. 현재 설정:
   ```
   User-agent: *
   Allow: /
   ```
   이 설정은 모든 크롤러가 모든 페이지를 크롤링할 수 있도록 허용합니다.

### Q: sitemap.xml이 업데이트되지 않아요

**A:**
1. `public/sitemap.xml` 파일이 최신인지 확인
2. 빌드 후 `dist/sitemap.xml`에 포함되는지 확인
3. `https://us.drillquiz.com/sitemap.xml` 접속하여 파일이 보이는지 확인
4. Search Console에서 sitemap을 다시 제출

### Q: google1234567890abcdef.html 파일은 무엇인가요? 어디서 얻을 수 있나요?

**A:**
- 이 파일은 Google Search Console에서 사이트 소유권을 확인하기 위해 제공하는 HTML 파일입니다
- **어디서 얻나요?**
  1. Google Search Console에서 속성을 추가할 때 소유권 확인 단계로 진행
  2. **HTML 파일** 방식 선택
  3. Google이 자동으로 생성한 파일을 다운로드할 수 있는 링크가 표시됨
  4. 파일 이름은 `google`로 시작하는 랜덤한 문자열입니다 (예: `google1234567890abcdef.html`)
- **사용 방법:**
  1. 다운로드한 파일을 `public/` 디렉토리에 복사
  2. 파일을 커밋하고 배포
  3. 배포 후 `https://your-domain.com/google1234567890abcdef.html` 접속하여 파일이 보이는지 확인
  4. Google Search Console에서 **확인** 버튼 클릭
- **참고:** 파일 이름의 랜덤한 부분은 Google이 생성한 고유한 문자열이므로, Google Search Console에서 제공하는 이름을 그대로 사용해야 합니다

## 추가 최적화 팁

### 1. 구조화된 데이터(Schema.org) 추가

페이지에 구조화된 데이터를 추가하면 검색 결과에 풍부한 결과(Rich Results)를 표시할 수 있습니다.

예시 (JSON-LD):
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "DrillQuiz",
  "description": "Online quiz learning platform",
  "url": "https://us.drillquiz.com",
  "applicationCategory": "EducationalApplication",
  "operatingSystem": "Web"
}
</script>
```

### 2. 콘텐츠 최적화

- **제목 태그**: 각 페이지에 고유하고 설명적인 제목 태그 사용
- **메타 설명**: 각 페이지에 고유하고 매력적인 메타 설명 추가
- **키워드**: "drillquiz" 키워드를 페이지 내용에 자연스럽게 포함

### 3. 백링크 구축

다른 웹사이트에서 사이트로 링크를 걸면 검색 순위가 향상됩니다.

- 소셜 미디어 공유
- 블로그 포스트 작성
- 커뮤니티 참여
- 파트너십 링크

### 4. 로컬 SEO (선택사항)

지역 기반 서비스라면:
- Google My Business 등록
- 지역 키워드 최적화
- 지역 디렉토리에 등록

## 문제 해결

### 문제 1: 소유권 확인 실패

**해결:**
- HTML 파일이 올바른 위치에 있는지 확인
- HTML 태그가 `<head>` 섹션에 있는지 확인
- DNS 레코드가 올바르게 설정되었는지 확인
- 파일 접근이 가능한지 확인 (https://us.drillquiz.com/verification-file.html)

### 문제 2: Sitemap 오류

**해결:**
- sitemap.xml 형식이 올바른지 확인
- 모든 URL이 https://로 시작하는지 확인
- sitemap.xml 파일이 접근 가능한지 확인
- Search Console의 **Sitemaps** 메뉴에서 오류 메시지 확인

### 문제 3: 인덱싱되지 않음

**해결:**
- robots.txt가 크롤링을 차단하지 않는지 확인
- 페이지가 공개적으로 접근 가능한지 확인
- 메타 태그에 `noindex`가 없는지 확인
- 페이지가 404 오류를 반환하지 않는지 확인

## 참고 자료

- [Google Search Console 도움말](https://support.google.com/webmasters/)
- [Sitemap 생성 가이드](https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview)
- [검색 엔진 최적화(SEO) 가이드](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)

## 다음 단계

1. ✅ Google Search Console에 사이트 등록
2. ✅ Sitemap 제출
3. ✅ 인덱싱 대기 (1~2주)
4. ✅ 검색 성능 모니터링
5. ✅ 콘텐츠 최적화 지속

