# SEO 인덱싱 개선 가이드

## 현재 인덱싱 문제 분석

Google Search Console에서 확인된 주요 문제:

### 1. "Crawled - currently not indexed" (277개 페이지)
- **원인**: Google이 크롤링했지만 인덱싱하지 않음
- **주요 URL 패턴**:
  - `/take-exam?question_id=...&exam_id=...` (쿼리 파라미터 포함)
  - `/take-exam/:examId?returnTo=...` (리디렉션 파라미터)
  - `/register` (일반 페이지)
  - `/api/question-files/.../download/` (API 엔드포인트)

### 2. "Page with redirect" (8개 페이지)
- **원인**: 페이지가 리디렉션되고 있음
- **주요 URL**:
  - `/random-practice`
  - `/exam-detail/:examId?group_id=...&sortBy=...` (쿼리 파라미터 포함)

### 3. "Alternate page with proper canonical tag" (15개 페이지)
- **상태**: ✅ 정상 (canonical 태그가 올바르게 작동)

## 적용된 개선 사항

### 1. robots.txt 개선
쿼리 파라미터가 있는 URL과 API 엔드포인트를 차단하여 불필요한 크롤링 감소:

```
# API 다운로드 엔드포인트 차단
Disallow: /api/question-files/*/download/

# 쿼리 파라미터가 있는 동적 URL 차단
Disallow: /*?returnTo=
Disallow: /*?fromHomeMenu=
Disallow: /*?question_id=
Disallow: /*?exam_id=
Disallow: /*?group_id=
Disallow: /*?sortBy=
Disallow: /*?sortOrder=
```

### 2. Canonical URL 개선
- 쿼리 파라미터가 있는 URL에도 쿼리 파라미터를 제거한 canonical URL 설정
- `drillquiz/views.py`의 `vue_app` 함수에서 동적으로 처리

### 3. 구조화된 데이터 추가
- WebApplication, Organization, WebSite 스키마 추가
- 초기 HTML에 포함되어 Google 크롤러가 JavaScript 실행 전에 읽을 수 있음

### 4. hreflang 태그 추가
- 다국어 지원을 위한 hreflang 태그 추가
- 언어별 메타 태그 동적 설정

## 예상 효과

### 단기 (1-2주)
- 불필요한 크롤링 감소
- "Crawled - currently not indexed" 수 감소
- API 엔드포인트 크롤링 중단

### 중기 (1-2개월)
- 인덱싱된 페이지 수 증가
- 검색 결과 노출 증가
- 검색 성능 개선

## 모니터링 체크리스트

- [ ] robots.txt 업데이트 확인
- [ ] "Crawled - currently not indexed" 수 감소 확인
- [ ] "Page with redirect" 수 감소 확인
- [ ] API 엔드포인트 크롤링 중단 확인
- [ ] 인덱싱된 페이지 수 증가 확인
- [ ] 검색 성능 개선 확인

## 추가 권장 사항

### 1. 리디렉션 문제 해결
- `/random-practice` 페이지의 리디렉션 원인 확인
- 불필요한 리디렉션 제거

### 2. 중요한 페이지 인덱싱 요청
- `/register`, `/login` 등 중요한 페이지에 대해 "인덱싱 요청" 수행
- Google Search Console → URL 검사 → 인덱싱 요청

### 3. 콘텐츠 품질 개선
- 각 페이지에 고유하고 가치 있는 콘텐츠 제공
- 메타 태그 최적화
- 구조화된 데이터 추가

## 참고 자료

- [Google Search Console 설정 가이드](./GOOGLE_SEARCH_CONSOLE_SETUP.md)
- [SEO 분석 보고서](./SEO_ANALYSIS_REPORT.md)
- [SEO 체크리스트](./SEO_CHECKLIST.md)

