# SEO 체크리스트

Google 검색에서 `drillquiz.com`과 `us.drillquiz.com`이 나타나도록 하는 체크리스트입니다.

## ✅ 즉시 확인해야 할 사항

### 1. Google Search Console 등록 확인

- [ ] `https://drillquiz.com` 속성이 등록되어 있는가?
- [ ] `https://us.drillquiz.com` 속성이 등록되어 있는가?
- [ ] 각 속성의 소유권이 확인되었는가?

**확인 방법:**
1. [Google Search Console](https://search.google.com/search-console) 접속
2. 속성 목록에서 두 도메인이 모두 보이는지 확인

### 2. Sitemap 제출 확인

- [ ] `drillquiz.com` 속성에 `https://drillquiz.com/sitemap.xml` 제출되었는가?
- [ ] `us.drillquiz.com` 속성에 `https://us.drillquiz.com/sitemap.xml` 제출되었는가?
- [ ] sitemap에 오류가 없는가?

**확인 방법:**
1. 각 속성에서 **Sitemaps** 메뉴 확인
2. 제출된 sitemap이 "성공" 상태인지 확인
3. 오류가 있으면 오류 메시지 확인

### 3. Robots.txt 확인

- [ ] `https://drillquiz.com/robots.txt` 접속 가능한가?
- [ ] `https://us.drillquiz.com/robots.txt` 접속 가능한가?
- [ ] robots.txt에 `Disallow: /`가 없는가? (크롤링 차단 여부)

**확인 방법:**
```bash
curl https://drillquiz.com/robots.txt
curl https://us.drillquiz.com/robots.txt
```

**예상 결과:**
```
User-agent: *
Allow: /
...
Sitemap: https://drillquiz.com/sitemap.xml
```

### 4. Sitemap.xml 확인

- [ ] `https://drillquiz.com/sitemap.xml` 접속 가능한가?
- [ ] `https://us.drillquiz.com/sitemap.xml` 접속 가능한가?
- [ ] sitemap.xml이 올바른 XML 형식인가?
- [ ] 각 도메인에 맞는 URL이 포함되어 있는가?

**확인 방법:**
```bash
curl https://drillquiz.com/sitemap.xml
curl https://us.drillquiz.com/sitemap.xml
```

**예상 결과:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://drillquiz.com/</loc>
    ...
  </url>
</urlset>
```

### 5. 메인 페이지 접근 확인

- [ ] `https://drillquiz.com/` 접속 가능한가?
- [ ] `https://us.drillquiz.com/` 접속 가능한가?
- [ ] 페이지가 정상적으로 로드되는가?
- [ ] 404 오류가 발생하지 않는가?

**확인 방법:**
```bash
curl -I https://drillquiz.com/
curl -I https://us.drillquiz.com/
```

**예상 결과:**
```
HTTP/2 200
```

## 🔍 Google Search Console에서 확인할 사항

### 1. 인덱싱 상태

1. 각 속성에서 **인덱싱** → **페이지** 메뉴 확인
2. 인덱싱된 페이지 수 확인
   - 처음에는 0개일 수 있음 (정상)
   - sitemap 제출 후 1~2주 후부터 증가 시작

### 2. 크롤링 상태

1. **인덱싱** → **Sitemaps** 메뉴에서 크롤링 상태 확인
2. 오류가 있으면 오류 메시지 확인

### 3. URL 검사

1. **URL 검사** 메뉴에서 메인 페이지 URL 입력
2. "URL이 Google에 등록되어 있습니다" 메시지 확인
3. 인덱싱되지 않았다면 **인덱싱 요청** 클릭

## ⏰ 시간이 필요한 사항

다음 사항들은 시간이 필요합니다:

- **Sitemap 제출 후 크롤링 시작**: 1~2주
- **인덱싱 완료**: 2~4주
- **검색 결과에 나타남**: 1~2개월

## 🚨 문제 해결

### 문제 1: robots.txt가 크롤링을 차단하고 있음

**증상:**
- robots.txt에 `Disallow: /`가 있음

**해결:**
- `drillquiz/views.py`의 `robots_txt` 함수 확인
- 허용된 도메인 목록에 도메인이 포함되어 있는지 확인

### 문제 2: sitemap.xml이 404 오류

**증상:**
- `https://drillquiz.com/sitemap.xml` 접속 시 404 오류

**해결:**
- `drillquiz/urls.py`에서 `sitemap_xml` 뷰가 등록되어 있는지 확인
- 배포 후 재시작 확인

### 문제 3: Google Search Console에 등록되지 않음

**증상:**
- Search Console에 속성이 없음

**해결:**
- [Google Search Console 설정 가이드](./GOOGLE_SEARCH_CONSOLE_SETUP.md) 참고하여 등록

### 문제 4: 인덱싱이 진행되지 않음

**증상:**
- sitemap 제출 후 2주 이상 지났는데도 인덱싱이 0개

**해결:**
1. **URL 검사**에서 메인 페이지 URL 직접 입력
2. **인덱싱 요청** 클릭
3. robots.txt와 sitemap.xml이 정상인지 다시 확인
4. 서버 로그에서 Google 크롤러 접근 확인

## 📊 모니터링

### 정기적으로 확인할 사항

1. **주 1회**: Google Search Console에서 인덱싱 상태 확인
2. **주 1회**: sitemap 제출 상태 확인
3. **월 1회**: 검색 성능 확인 (노출 수, 클릭 수)

### 확인 명령어

```bash
# robots.txt 확인
curl https://drillquiz.com/robots.txt
curl https://us.drillquiz.com/robots.txt

# sitemap.xml 확인
curl https://drillquiz.com/sitemap.xml
curl https://us.drillquiz.com/sitemap.xml

# 메인 페이지 확인
curl -I https://drillquiz.com/
curl -I https://us.drillquiz.com/
```

## 📝 참고 문서

- [Google Search Console 설정 가이드](./GOOGLE_SEARCH_CONSOLE_SETUP.md)
- [SEO 문제 해결 가이드](./SEO_ISSUES_TROUBLESHOOTING.md)

