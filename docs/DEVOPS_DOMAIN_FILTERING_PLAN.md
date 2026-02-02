# DevOps 도메인 필터링 구현 계획

## 개요

`devops.drillquiz.com`으로 서비스할 때 DevOps 관련 스터디와 시험만 노출되도록 필터링을 구현합니다. 로컬에서는 `devops.localhost`로 테스트할 수 있으며, `ios-devops` 앱도 `devops.drillquiz.com`을 사용합니다.

**중요**: devops 도메인에서는 다음 필터링이 적용됩니다:
1. **태그 필터링**: "IT 기술 > IT 기술" 카테고리에 속한 태그들만 사용 (현재 20개 태그, 그 중 DevOps 포함)
2. **카테고리 필터링**: "IT 기술 > IT 기술" 카테고리부터만 노출 (상위 카테고리 숨김)

## 현재 상태 분석

### 1. 기존 구현 현황

#### 프론트엔드
- ✅ `src/utils/domainUtils.js`: 도메인 감지 및 설정 관리
  - `devops` 도메인 설정 존재 (`tagName: 'DevOps'`)
  - `getCurrentDomainConfig()`, `getForcedTags()` 함수 구현됨
- ✅ `src/components/ExamManagement.vue`: 시험 목록 필터링
  - devops 도메인 감지 시 DevOps 태그 자동 적용 (line 1515-1519)
  - API 호출 시 강제 태그 파라미터 추가 (line 1871-1877)
- ✅ `src/components/StudyManagement.vue`: 스터디 목록 필터링
  - 도메인별 태그 필터링 적용 (line 1820-1853)
- ⚠️ 일부 컴포넌트에서 도메인 필터링이 누락될 수 있음

#### 백엔드
- ✅ `quiz/views/exam_views.py`: 시험 목록 API (`get_exams`)
  - `tags` 파라미터로 필터링 지원 (line 6683, 6978-6991)
- ✅ `quiz/views/study_views.py`: 스터디 목록 API (`list`)
  - `tags` 파라미터로 필터링 지원 (line 903)
- ⚠️ 백엔드에서 도메인 기반 자동 필터링 없음 (프론트엔드에 의존)

#### 인프라/설정
- ✅ `drillquiz/settings.py`: CORS 설정
  - `devops.localhost:8080`, `devops.drillquiz.com` 포함 (line 174-180)
- ✅ `ios-devops` 프로젝트 존재
- ✅ `scripts/local-ios-build.sh`: DevOps 빌드 스크립트
  - `devops.drillquiz.com` API 서버 설정 (line 47)

### 2. 문제점 및 개선 필요 사항

1. **프론트엔드 필터링 불완전**
   - 일부 컴포넌트에서 도메인 필터링이 누락될 수 있음
   - 사용자가 태그 필터를 수동으로 제거할 수 있음
   - "My Exams/Studies"에서도 필터링이 적용되어야 하는지 명확하지 않음

2. **백엔드 필터링 부재**
   - 백엔드에서 도메인을 감지하여 자동으로 필터링하지 않음
   - 프론트엔드에서 태그 파라미터를 보내지 않으면 모든 데이터가 노출됨
   - 보안 측면에서 백엔드에서도 필터링하는 것이 권장됨

3. **카테고리 필터링 부재**
   - devops 도메인에서 "IT 기술 > IT 기술" 카테고리만 노출되어야 함
   - 현재 카테고리 필터링 로직이 없음
   - 카테고리 트리 API에서 특정 카테고리만 반환하도록 필터링 필요

4. **로컬 테스트 환경**
   - `devops.localhost` 설정 확인 필요
   - 로컬 개발 환경에서 도메인 필터링 테스트 방법 명확화 필요

5. **ios-devops 앱 설정**
   - `ios-devops` 앱이 `devops.drillquiz.com`을 사용하는지 확인 필요
   - `capacitor.config.json` 설정 확인 필요

## 구현 계획

### Phase 1: 프론트엔드 필터링 강화

#### 1.1 도메인 필터링 유틸리티 개선
**파일**: `src/utils/domainUtils.js`

- [ ] `isDevOpsDomain()` 헬퍼 함수 추가
- [ ] `shouldForceDevOpsFilter()` 함수 추가 (필터링이 필요한지 판단)
- [ ] `getDevOpsCategoryId()` 함수 추가 ("IT 기술 > IT 기술" 카테고리 ID 반환)
- [ ] `getDevOpsCategoryTags()` 함수 추가 (해당 카테고리의 태그들만 반환)
- [ ] 도메인별 필터링 정책 명확화

#### 1.2 ExamManagement 컴포넌트 개선
**파일**: `src/components/ExamManagement.vue`

- [ ] devops 도메인에서 태그 필터 제거 방지
- [ ] "My Exams"에서도 devops 필터 적용 여부 결정 및 구현
- [ ] 모든 API 호출에서 devops 태그 강제 적용 확인

#### 1.3 StudyManagement 컴포넌트 개선
**파일**: `src/components/StudyManagement.vue`

- [ ] devops 도메인에서 태그 필터 제거 방지
- [ ] "My Studies"에서도 devops 필터 적용 여부 결정 및 구현
- [ ] 모든 API 호출에서 devops 태그 강제 적용 확인

#### 1.4 카테고리 필터링 구현
**파일**: `src/components/CategoryFilterModal.vue`, `src/components/TagFilterModal.vue`

- [ ] devops 도메인에서 카테고리 트리 필터링
  - "IT 기술 > IT 기술" 카테고리만 표시
  - 상위 카테고리(1단계 "IT 기술")는 숨김 처리
- [ ] 태그 필터에서도 "IT 기술 > IT 기술" 카테고리의 태그만 표시
- [ ] 카테고리 API 응답 필터링 로직 추가

#### 1.5 기타 컴포넌트 점검
- [ ] `src/views/QuestionFiles.vue`: 도메인 필터링 확인
- [ ] `src/components/StudyDetail.vue`: 관련 스터디 필터링 확인
- [ ] 홈 화면, 검색 결과 등 다른 화면에서도 필터링 적용 확인
- [ ] `src/components/TagFilter.vue`: 카테고리 필터링 확인

### Phase 2: 백엔드 필터링 추가

#### 2.1 도메인 감지 미들웨어/유틸리티
**파일**: `quiz/utils/domain_utils.py` (신규 생성)

- [ ] `get_request_domain()` 함수: 요청 도메인 추출
- [ ] `is_devops_domain()` 함수: devops 도메인 판단
- [ ] `get_domain_tag_id()` 함수: 도메인별 태그 ID 반환
- [ ] `get_devops_category_id()` 함수: "IT 기술 > IT 기술" 카테고리 ID 반환
- [ ] `get_devops_category_tag_ids()` 함수: 해당 카테고리의 모든 태그 ID 반환

#### 2.2 Exam API 필터링 강화
**파일**: `quiz/views/exam_views.py`

- [ ] `get_exams()` 함수에서 도메인 기반 자동 필터링 추가
- [ ] devops 도메인 요청 시 DevOps 태그 자동 적용
- [ ] 관리자 권한이 있어도 devops 도메인에서는 필터링 적용 (선택적)

#### 2.3 Study API 필터링 강화
**파일**: `quiz/views/study_views.py`

- [ ] `list()` 메서드에서 도메인 기반 자동 필터링 추가
- [ ] devops 도메인 요청 시 DevOps 태그 자동 적용
- [ ] 관리자 권한이 있어도 devops 도메인에서는 필터링 적용 (선택적)

#### 2.4 카테고리 API 필터링
**파일**: `quiz/views/tag_category_views.py`

- [ ] 카테고리 트리 API (`/api/tag-categories/tree/`)에서 devops 도메인 필터링
  - devops 도메인 요청 시 "IT 기술 > IT 기술" 카테고리만 반환
  - 상위 카테고리는 제외
- [ ] 태그 목록 API에서도 카테고리 필터링 적용
  - devops 도메인 요청 시 "IT 기술 > IT 기술" 카테고리의 태그만 반환

#### 2.5 기타 API 엔드포인트 점검
- [ ] 검색 API, 추천 API 등에서도 도메인 필터링 적용 확인
- [ ] 통계 API, 대시보드 API 등에서도 필터링 적용 여부 결정

### Phase 3: 로컬 테스트 환경 설정

#### 3.1 로컬 도메인 설정
- [ ] `/etc/hosts` 또는 로컬 DNS 설정 가이드 작성
  - `127.0.0.1 devops.localhost` 추가
- [ ] Vue 개발 서버에서 `devops.localhost` 접근 가능하도록 설정 확인
- [ ] Django 개발 서버에서 `devops.localhost` 허용 확인

#### 3.2 로컬 테스트 스크립트
**파일**: `scripts/test-devops-local.sh` (신규 생성)

- [ ] 로컬 환경에서 devops 도메인 테스트 스크립트 작성
- [ ] 필터링 동작 확인 테스트 케이스 포함

### Phase 4: ios-devops 앱 설정 확인

#### 4.1 capacitor.config.json 확인
**파일**: `ios-devops/App/App/capacitor.config.json`

- ✅ 현재 상태: `server.url`이 명시되어 있지 않음 (프로덕션 빌드 시 설정됨)
- [ ] 프로덕션 빌드 시 `devops.drillquiz.com` 사용 확인
- [ ] 로컬 개발 시 `devops.localhost` 사용 설정 추가 (선택적)

#### 4.2 Info.plist 확인
**파일**: `ios-devops/App/App/Info.plist`

- ✅ `NSAppTransportSecurity` 설정 확인 완료
- ✅ `devops.drillquiz.com` 도메인이 `NSExceptionDomains`에 포함됨 (line 69-75)
  - `NSExceptionAllowsInsecureHTTPLoads: true`
  - `NSIncludesSubdomains: true`

#### 4.3 빌드 스크립트 확인
**파일**: `scripts/local-ios-build.sh`

- [ ] devops 빌드 시 올바른 API 서버 URL 설정 확인
- [ ] 로컬 테스트용 설정 옵션 추가 (선택적)

### Phase 5: 문서화 및 테스트

#### 5.1 문서화
- [ ] 구현 완료 후 이 문서 업데이트
- [ ] 개발자 가이드에 devops 도메인 필터링 설명 추가
- [ ] 로컬 테스트 방법 문서화

#### 5.2 테스트
- [ ] devops.drillquiz.com에서 필터링 동작 확인
- [ ] devops.localhost에서 로컬 테스트
- [ ] ios-devops 앱에서 필터링 동작 확인
- [ ] 일반 도메인(drillquiz.com)에서 필터링이 적용되지 않는지 확인
- [ ] 관리자 권한 사용자 테스트
- [ ] 익명 사용자 테스트

## 구현 세부 사항

### 프론트엔드 필터링 정책

1. **devops 도메인 감지**
   - `window.location.hostname.includes('devops')` 사용
   - `devops.drillquiz.com`, `devops.localhost`, `devops-dev.drillquiz.com` 등 모두 포함

2. **태그 필터링 강제**
   - devops 도메인에서는 "IT 기술 > IT 기술" 카테고리에 속한 태그들만 사용 가능
   - 현재 20개의 태그가 있으며, 그 중 DevOps 태그 포함
   - 사용자가 다른 카테고리의 태그를 선택하려고 해도 제한
   - 태그 필터 UI에서 "IT 기술 > IT 기술" 카테고리의 태그만 표시

3. **카테고리 필터링 강제**
   - devops 도메인에서는 "IT 기술 > IT 기술" 카테고리부터만 노출
   - 상위 카테고리(1단계 "IT 기술")는 숨김 처리
   - 카테고리 트리에서 해당 카테고리만 표시
   - 사용자가 다른 카테고리를 선택할 수 없도록 제한

4. **"My Exams/Studies" 필터링**
   - **옵션 A**: "My Exams/Studies"에서도 devops 필터 적용 (더 엄격)
   - **옵션 B**: "My Exams/Studies"에서는 필터 미적용 (사용자 편의성)
   - **권장**: 옵션 A (일관성 유지)

### 백엔드 필터링 정책

1. **도메인 기반 자동 필터링**
   - `request.get_host()` 또는 `request.META.get('HTTP_HOST')`로 도메인 감지
   - devops 도메인 요청 시 자동으로 DevOps 태그 필터 적용
   - 프론트엔드에서 태그 파라미터를 보내지 않아도 백엔드에서 자동 적용

2. **관리자 권한 처리**
   - **옵션 A**: 관리자도 devops 도메인에서는 필터링 적용 (더 엄격)
   - **옵션 B**: 관리자는 필터링 제외 (관리 편의성)
   - **권장**: 옵션 A (보안 및 일관성)

3. **태그 ID 조회**
   - "IT 기술 > IT 기술" 카테고리의 모든 태그 ID를 조회
   - DevOps 태그가 포함되어 있는지 확인
   - 캐싱하여 성능 최적화
   - 태그가 없을 경우 빈 결과 반환 또는 경고 로그

4. **카테고리 필터링**
   - "IT 기술 > IT 기술" 카테고리 ID를 데이터베이스에서 조회
   - 해당 카테고리에 속한 태그들만 필터링에 사용
   - 카테고리 트리 API에서 해당 카테고리만 반환
   - 캐싱하여 성능 최적화

### 로컬 테스트 환경

1. **호스트 파일 설정**
   ```bash
   # /etc/hosts 파일에 추가
   127.0.0.1 devops.localhost
   ```

2. **Vue 개발 서버**
   - 기본적으로 `localhost:8080`에서 실행
   - `devops.localhost:8080`으로도 접근 가능하도록 확인

3. **Django 개발 서버**
   - `ALLOWED_HOSTS`에 `devops.localhost` 추가 확인
   - 또는 `python manage.py runserver 0.0.0.0:8000`으로 실행

## 우선순위

1. **High Priority**
   - Phase 1: 프론트엔드 필터링 강화
   - Phase 2: 백엔드 필터링 추가
   - Phase 5: 기본 테스트

2. **Medium Priority**
   - Phase 3: 로컬 테스트 환경 설정
   - Phase 4: ios-devops 앱 설정 확인

3. **Low Priority**
   - Phase 5: 상세 문서화
   - 추가 최적화 및 개선

## 참고 사항

- 기존 leetcode 도메인 필터링 로직을 참고하여 구현
- 태그 이름이 정확히 "DevOps"인지 확인 필요 (대소문자 구분)
  - 프론트엔드 코드에서 `tagName: 'DevOps'`로 설정되어 있음
  - 모든 언어 필드(`name_ko`, `name_en`, `name_es`, `name_zh`, `name_ja`)와 `localized_name`에서 일치하는 태그를 찾음
- 다국어 지원: 한국어 "DevOps", 영어 "DevOps" 등 모든 언어에서 일치하는지 확인
- 성능: 도메인 감지 및 태그 필터링이 성능에 미치는 영향 최소화
- 캐싱: 도메인별 필터링 결과 캐싱 고려
- DevOps 태그 및 카테고리 확인:
  - 데이터베이스에 "DevOps" 태그가 실제로 존재하는지 확인 필요
  - "IT 기술 > IT 기술" 카테고리가 존재하는지 확인 필요
  - DevOps 태그가 "IT 기술 > IT 기술" 카테고리에 속해 있는지 확인 필요
  - 현재 20개의 태그가 "IT 기술 > IT 기술" 카테고리에 속해 있음
  - 태그나 카테고리가 없을 경우 필터링이 작동하지 않을 수 있음
  - 태그 생성 마이그레이션 또는 관리자 페이지에서 태그 생성 필요

## 관련 파일 목록

### 프론트엔드
- `src/utils/domainUtils.js`
- `src/components/ExamManagement.vue`
- `src/components/StudyManagement.vue`
- `src/components/CategoryFilterModal.vue`
- `src/components/TagFilterModal.vue`
- `src/components/TagFilter.vue`
- `src/views/QuestionFiles.vue`
- `src/components/StudyDetail.vue`
- `src/config/apiConfig.js`

### 백엔드
- `quiz/views/exam_views.py`
- `quiz/views/study_views.py`
- `quiz/views/tag_category_views.py` (카테고리 API)
- `quiz/views/tag_views.py` (태그 API)
- `quiz/models.py` (Tag, TagCategory 모델)
- `drillquiz/settings.py`

### 설정/인프라
- `ios-devops/App/App/capacitor.config.json`
- `ios-devops/App/App/Info.plist`
- `scripts/local-ios-build.sh`
- `ci/k8s.sh` (Kubernetes 배포 설정)

