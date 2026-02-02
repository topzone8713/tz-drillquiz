# DrillQuiz E2E 테스트

이 디렉토리는 USER_SCENARIOS.md를 기반으로 한 End-to-End 테스트를 포함합니다.

## 테스트 구조

```
tests/e2e/
├── usecases/                    # 시나리오별 테스트
│   ├── scenario-01-parent-child-homework.spec.js
│   ├── scenario-02-english-vocabulary.spec.js
│   ├── scenario-03-sibling-quiz-competition.spec.js
│   ├── scenario-04-teacher-student-homework.spec.js
│   ├── scenario-05-certification-preparation.spec.js
│   └── scenario-06-korean-language-learning.spec.js
├── helpers/                     # 헬퍼 함수
│   ├── api.js                  # API 클라이언트
│   └── auth.js                 # 인증 헬퍼
└── fixtures/                    # 테스트 데이터
    └── users.json
```

## 테스트 커버리지

### 시나리오 1: 엄마와 아이의 숙제 복습 시간
- ✅ 1단계: 숙제 파일 업로드
- ✅ 2단계: 아이 수준에 맞는 문제 만들기
- ✅ 3단계: 엄마와 아이의 스터디 그룹 만들기
- ✅ 4단계: 아이가 문제 풀기
- ✅ 5단계: AI 인터뷰로 실력 확인
- ✅ 6단계: 엄마에게 결과 전송

### 시나리오 2: 중학생 딸의 영어 단어 암기
- ✅ 1단계: 단어장 파일 업로드
- ✅ 2단계: 단계별 시험 만들기
- ✅ 3단계: 학습 스터디 구성
- ✅ 4단계: 딸의 학습 진행
- ✅ 5단계: AI 음성 인터뷰로 발음 연습
- ✅ 6단계: 엄마에게 주간 리포트

### 시나리오 3: 형제가 함께하는 과학 퀴즈 대결
- ✅ 1단계: 과학 문제 파일 준비
- ✅ 2단계: 각 아이 수준에 맞는 시험 만들기
- ✅ 3단계: 가족 스터디 그룹 만들기
- ✅ 4단계: 형제의 학습 경쟁
- ✅ 5단계: 서로 도와주기
- ✅ 6단계: 주말 AI 인터뷰 시간

### 시나리오 4: 선생님과 학생들의 온라인 숙제 관리
- ✅ 1단계: 숙제 문제 파일 업로드
- ✅ 2단계: 학생별 맞춤 시험 만들기
- ✅ 3단계: 학급 스터디 그룹 만들기
- ✅ 4단계: 학생들의 숙제 수행
- ✅ 5단계: 선생님의 진행 상황 확인
- ✅ 6단계: 부진 학생 집중 관리
- ✅ 7단계: 학부모 연락

### 시나리오 5: 직장인 부부의 자격증 시험 준비
- ✅ 1단계: 기출 문제 파일 업로드
- ✅ 2단계: 과목별 시험 구성
- ✅ 3단계: 부부 스터디 그룹
- ✅ 4단계: 각자의 학습 진행
- ✅ 5단계: 서로 도와주기
- ✅ 6단계: 실전 연습 - AI 인터뷰
- ✅ 7단계: 최종 점검

### 시나리오 6: 해외 거주 가족의 한국어 학습
- ✅ 1단계: 한국어 교재 파일 준비
- ✅ 2단계: 단계별 학습 시험 만들기
- ✅ 3단계: 모국어 유지 스터디
- ✅ 4단계: 딸의 일일 학습
- ✅ 5단계: AI 음성 인터뷰로 발음 연습
- ✅ 6단계: 엄마의 주간 모니터링
- ✅ 7단계: 다국어 지원 활용

## 실행 방법

```bash
# 모든 테스트 실행
npm run test:e2e

# UI 모드 (대화형)
npm run test:e2e:ui

# 헤드 모드 (브라우저 표시)
npm run test:e2e:headed

# 디버그 모드
npm run test:e2e:debug

# 리포트 보기
npm run test:e2e:report
```

## 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `PLAYWRIGHT_BASE_URL` | 프론트엔드 URL | `http://localhost:8080` |
| `PLAYWRIGHT_API_URL` | 백엔드 API URL | `http://localhost:8000/api` |

## 테스트 결과

테스트 실행 후 결과는 다음 위치에 생성됩니다:
- **HTML 리포트**: `test-results/html-report/index.html`
- **JSON 리포트**: `test-results/results.json`
- **JUnit 리포트**: `test-results/junit.xml`
