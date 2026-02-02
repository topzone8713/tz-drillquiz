# tz-todo-demo E2E 테스트 계획서

## 📋 개요

이 문서는 tz-todo-demo 프로젝트의 End-to-End 테스트 계획입니다.

**최종 업데이트**: 2026-01-20
**대상**: Todo 앱 사용자 유스케이스

---

## 🎯 테스트 목표

1. **핵심 기능 테스트**: 인증, Todo CRUD 등 핵심 기능 검증
2. **자동화**: Jenkins에서 테스트 스위트 실행 가능
3. **신뢰성**: 실제 사용자 시나리오 기반 테스트
4. **유지보수성**: 모듈화된 테스트 구조

---

## 📊 테스트 커버리지 매트릭스

### 인증 유스케이스

| UC | 유스케이스 | 테스트 파일 | 상태 |
|----|-----------|-----------|------|
| UC-001 | 회원가입 및 로그인 | `01-authentication.spec.js` | ✅ 완료 |

### Todo 유스케이스

| UC | 유스케이스 | 테스트 파일 | 상태 |
|----|-----------|-----------|------|
| UC-002 | Todo 생성 | `02-todo-crud.spec.js` | ⏳ 예정 |
| UC-003 | Todo 조회 | `02-todo-crud.spec.js` | ⏳ 예정 |
| UC-004 | Todo 수정 | `02-todo-crud.spec.js` | ⏳ 예정 |
| UC-005 | Todo 삭제 | `02-todo-crud.spec.js` | ⏳ 예정 |
| UC-006 | Todo 완료 표시 | `02-todo-crud.spec.js` | ⏳ 예정 |

### 알림 유스케이스

| UC | 유스케이스 | 테스트 파일 | 상태 |
|----|-----------|-----------|------|
| UC-101 | 알림 설정 | `03-notifications.spec.js` | ⏳ 예정 |
| UC-102 | 알림 수신 | `03-notifications.spec.js` | ⏳ 예정 |

---

## 🏗️ 테스트 구조

```
tests/e2e/
├── helpers/
│   ├── api.js                    # API 클라이언트
│   ├── auth.js                   # 인증 헬퍼
│   ├── data-cleanup.js           # 데이터 정리
│   └── batch-runner.js           # 배치 작업 실행
├── fixtures/
│   └── users.json                # 테스트 사용자 데이터
├── usecases/
│   └── 01-authentication.spec.js # 인증 테스트 (완료)
└── README.md
```

---

## 📝 완료된 테스트 시나리오

### UC-001: 회원가입 및 로그인 (✅ 11개 테스트 통과)

#### 로그인 페이지
1. ✅ 로그인 페이지 접근 및 UI 확인
2. ✅ 회원가입 링크 표시 확인

#### API 인증
3. ✅ 유효한 자격증명으로 로그인 성공
4. ✅ 잘못된 자격증명으로 로그인 실패
5. ✅ 인증 상태 확인
6. ✅ 프로필 조회 (인증 필요)
7. ✅ 로그아웃

#### UI 인증
8. ✅ UI를 통한 로그인 성공
9. ✅ 잘못된 자격증명으로 오류 메시지 표시

#### 보호된 라우트
10. ✅ 미인증 시 로그인 페이지로 리다이렉트
11. ✅ 인증 후 보호된 페이지 접근

---

## 🛠️ 테스트 실행 스크립트

### 로컬 개발
```bash
# 모든 테스트 실행
npm run test:e2e

# UI 모드 (대화형)
npm run test:e2e:ui

# 인증 테스트만 실행
npm run test:e2e:auth

# 리포트 보기
npm run test:e2e:report
```

### Jenkins
```bash
# Jenkins에서 실행 (E2E_TEST_YN=true 설정 필요)
npm run test:e2e:full
```

---

## 🔧 테스트 환경 설정

### 필수 사전 조건
1. 백엔드 서버 실행 (`python manage.py runserver`)
2. 프론트엔드 서버 실행 (`npm run serve`)
3. 테스트 사용자 생성 완료 (admin/password)

### 환경 변수
| 변수 | 설명 | 기본값 |
|------|------|--------|
| `PLAYWRIGHT_BASE_URL` | 프론트엔드 URL | `http://localhost:8080` |
| `PLAYWRIGHT_API_URL` | 백엔드 API URL | `http://localhost:8000/api` |
| `TEST_USERNAME` | 테스트 사용자명 | `admin` |
| `TEST_PASSWORD` | 테스트 비밀번호 | `password` |

---

## 🚀 다음 단계

### Phase 2 (예정)
- [ ] UC-002~006: Todo CRUD 테스트 구현
- [ ] Todo 헬퍼 함수 추가

### Phase 3 (예정)
- [ ] UC-101~102: 알림 테스트 구현
- [ ] 알림 헬퍼 함수 추가

---

## 📊 테스트 결과 리포트

### 위치
- **HTML 리포트**: `test-results/html-report/index.html`
- **JSON 리포트**: `test-results/results.json`
- **JUnit 리포트**: `test-results/junit.xml` (CI/CD 통합용)

---

**문서 버전**: 1.1
**최종 업데이트**: 2026-01-20
