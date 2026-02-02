# DrillQuiz API 명세서

## 📋 개요

DrillQuiz API는 Django REST Framework 기반의 RESTful API로, 퀴즈 학습 플랫폼의 모든 기능을 제공합니다.

**Base URL**: `https://us.drillquiz.com/api/` (프로덕션)  
**개발 URL**: `http://localhost:8000/api/` (개발)

## 🔐 인증

### CSRF 토큰
- **GET** `/csrf-token/` - CSRF 토큰 발급
- **POST** `/test-csrf/` - CSRF 토큰 테스트

### 세션 인증
- Django 세션 기반 인증
- Google OAuth 2.0 지원

## 📚 API 카테고리

## 1. 🔐 인증 및 사용자 관리 (Authentication & User Management)

### 1.1 사용자 인증
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/register/` | 사용자 회원가입 | ❌ |
| POST | `/login/` | 사용자 로그인 | ❌ |
| POST | `/logout/` | 사용자 로그아웃 | ✅ |
| GET | `/auth/status/` | 인증 상태 확인 | ❌ |

### 1.2 Google OAuth
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/google-oauth/` | Google OAuth 로그인 | ❌ |
| GET | `/google-oauth/config/` | Google OAuth 설정 조회 | ❌ |

### 1.3 사용자 프로필
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/user-profile/get/` | 사용자 프로필 조회 | ✅ |
| POST | `/user-profile/update/` | 사용자 프로필 수정 | ✅ |
| POST | `/change-language/` | 사용자 언어 변경 | ✅ |
| POST | `/update-user-language/` | 사용자 언어 업데이트 | ✅ |

### 1.4 이메일 인증
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/send-email-verification/` | 이메일 인증 요청 | ✅ |
| GET | `/verify-email/<token>/` | 이메일 인증 확인 | ❌ |

### 1.5 사용자 관리 (관리자)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/users/` | 사용자 목록 조회 | ✅ (Admin) |
| POST | `/users/create/` | 사용자 생성 | ✅ (Admin) |
| PUT | `/users/<user_id>/` | 사용자 정보 수정 | ✅ (Admin) |
| DELETE | `/users/<user_id>/delete/` | 사용자 삭제 | ✅ (Admin) |
| POST | `/users/delete-bulk/` | 사용자 일괄 삭제 | ✅ (Admin) |
| POST | `/users/delete-all/` | 모든 사용자 삭제 | ✅ (Admin) |
| GET | `/search-users/` | 사용자 검색 | ✅ (Admin) |
| POST | `/user/<user_id>/change-password/` | 사용자 비밀번호 변경 | ✅ (Admin) |

### 1.6 사용자 데이터 관리
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/export-user-data/` | 사용자 데이터 내보내기 | ✅ |
| POST | `/delete-my-account/` | 내 계정 삭제 | ✅ |
| GET | `/user-statistics/summary/` | 사용자 통계 요약 | ✅ |
| POST | `/user-statistics/reset/` | 사용자 통계 초기화 | ✅ |
| POST | `/user-statistics/backup/` | 사용자 통계 백업 | ✅ |

## 2. 📝 문제 관리 (Question Management)

### 2.1 문제 CRUD
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/upload-questions/` | 문제 파일 업로드 (CSV/Excel) | ✅ |
| GET | `/questions/` | 문제 목록 조회 | ✅ |
| GET | `/questions/<question_id>/` | 특정 문제 조회 | ✅ |
| PUT | `/questions/<question_id>/update/` | 문제 수정 | ✅ |
| DELETE | `/questions/<question_id>/delete/` | 문제 삭제 | ✅ |

### 2.2 문제 통계 및 분석
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/questions/statistics-by-title/<title>/` | 제목별 문제 통계 | ✅ |
| GET | `/questions/<question_id>/original-exams/` | 문제가 포함된 시험 목록 | ✅ |
| POST | `/adjust-question-accuracy/` | 문제 정확도 조정 | ✅ |
| POST | `/adjust-single-question-accuracy/` | 단일 문제 정확도 조정 | ✅ |

### 2.3 문제 그룹 관리
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/questions/bulk-update-group/` | 문제 그룹 일괄 업데이트 | ✅ |
| POST | `/move-questions-to-exam/` | 문제를 시험으로 이동 | ✅ |
| POST | `/move-questions/` | 문제 이동 | ✅ |
| POST | `/copy-questions/` | 문제 복사 | ✅ |
| POST | `/delete-questions/` | 문제 일괄 삭제 | ✅ |

### 2.4 문제 무시 기능
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/questions/ignored/` | 무시된 문제 목록 | ✅ |
| POST | `/question/<question_id>/ignore/` | 문제 무시 | ✅ |
| POST | `/question/<question_id>/unignore/` | 문제 무시 해제 | ✅ |
| GET | `/question/<question_id>/check-ignored/` | 문제 무시 상태 확인 | ✅ |

### 2.5 문제 파일 관리
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/question-files/` | 문제 파일 목록 | ✅ |
| GET | `/question-files/check-existing/<filename>/` | 파일 존재 확인 | ✅ |
| GET | `/question-files/<filename>/download/` | 문제 파일 다운로드 | ✅ |
| DELETE | `/question-files/<filename>/delete/` | 문제 파일 삭제 | ✅ |
| PUT | `/question-files/<filename>/` | 문제 파일 수정 | ✅ |

## 3. 📋 시험 관리 (Exam Management)

### 3.1 시험 CRUD
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/create-exam/` | 시험 생성 | ✅ |
| GET | `/exam/<exam_id>/` | 시험 상세 조회 | ✅ |
| PUT | `/exam/<exam_id>/update/` | 시험 수정 | ✅ |
| DELETE | `/exam/<exam_id>/delete/` | 시험 삭제 | ✅ |
| GET | `/exams/` | 시험 목록 조회 | ✅ |

### 3.2 시험 문제 관리
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/exam/<exam_id>/questions/` | 시험 문제 목록 | ✅ |
| POST | `/exam/<exam_id>/add-question/` | 시험에 문제 추가 | ✅ |
| POST | `/exam/<exam_id>/update-questions-from-excel/` | Excel에서 문제 업데이트 | ✅ |
| POST | `/exam/<exam_id>/import-from-connected-file/` | 연결된 파일에서 문제 가져오기 | ✅ |

### 3.3 시험 실행
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/create-single-question-exam/` | 단일 문제 시험 생성 | ✅ |
| POST | `/exam/<exam_id>/continue/` | 시험 계속하기 | ✅ |
| POST | `/exam/<exam_id>/retake/` | 시험 재시도 | ✅ |
| POST | `/exam/<exam_id>/wrong-questions/` | 틀린 문제만 재시험 | ✅ |
| POST | `/submit-exam/` | 시험 제출 | ✅ |

### 3.4 시험 결과
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/exam-results/` | 시험 결과 목록 | ✅ |
| GET | `/exam-results/summary/` | 시험 결과 요약 | ✅ |
| GET | `/exam-result/<result_id>/` | 시험 결과 상세 | ✅ |
| POST | `/save-random-practice-result/` | 랜덤 연습 결과 저장 | ✅ |

### 3.5 시험 설정
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/exam/<exam_id>/toggle-original/` | 시험 원본/복사본 토글 | ✅ |
| GET | `/exam-list-for-move/` | 이동 가능한 시험 목록 | ✅ |

### 3.6 시험 통계
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/exam/<exam_id>/question-statistics/` | 시험 문제 통계 | ✅ |
| GET | `/exam/<exam_id>/question-member-mappings/` | 문제-멤버 매핑 | ✅ |
| GET | `/exam/<exam_id>/connected-studies/` | 연결된 스터디 목록 | ✅ |

### 3.7 시험 구독 관리
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/exam-subscription/toggle/` | 시험 구독 토글 | ✅ |
| POST | `/exam-subscription/bulk-toggle/` | 시험 구독 일괄 토글 | ✅ |
| GET | `/exam-subscription/user/` | 사용자 시험 구독 목록 | ✅ |

### 3.8 사용자 시험 관리
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/user-exams/my-exams/` | 내 시험 목록 | ✅ |
| GET | `/user-exams/subscribed-exams/` | 구독한 시험 목록 | ✅ |
| POST | `/user-exams/move-to-subscribed/` | 시험을 구독으로 이동 | ✅ |
| POST | `/user-exams/move-to-my-exams/` | 시험을 내 시험으로 이동 | ✅ |
| POST | `/user-exams/shuffle/` | 구독 시험 순서 섞기 | ✅ |

### 3.9 시험 데이터 관리
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/exams/download-excel/` | 시험 Excel 다운로드 | ✅ |
| POST | `/exams/upload-excel/` | 시험 Excel 업로드 | ✅ |
| POST | `/delete-question-results/` | 문제 결과 삭제 | ✅ |
| POST | `/delete-question-results-global/` | 전체 문제 결과 삭제 | ✅ |

## 4. 📚 스터디 관리 (Study Management)

### 4.1 스터디 CRUD (ViewSet)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/studies/` | 스터디 목록 조회 | ✅ |
| POST | `/studies/` | 스터디 생성 | ✅ |
| GET | `/studies/<id>/` | 스터디 상세 조회 | ✅ |
| PUT | `/studies/<id>/` | 스터디 수정 | ✅ |
| DELETE | `/studies/<id>/` | 스터디 삭제 | ✅ |

### 4.2 스터디 태스크 관리 (ViewSet)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/study-tasks/` | 스터디 태스크 목록 | ✅ |
| POST | `/study-tasks/` | 스터디 태스크 생성 | ✅ |
| GET | `/study-tasks/<id>/` | 스터디 태스크 상세 | ✅ |
| PUT | `/study-tasks/<id>/` | 스터디 태스크 수정 | ✅ |
| DELETE | `/study-tasks/<id>/` | 스터디 태스크 삭제 | ✅ |

### 4.3 멤버 관리 (ViewSet)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/members/` | 멤버 목록 조회 | ✅ |
| POST | `/members/` | 멤버 추가 | ✅ |
| GET | `/members/<id>/` | 멤버 상세 조회 | ✅ |
| PUT | `/members/<id>/` | 멤버 정보 수정 | ✅ |
| DELETE | `/members/<id>/` | 멤버 삭제 | ✅ |
| GET | `/studies/<id>/members/` | 스터디 멤버 목록 | ✅ |

### 4.4 스터디 가입 요청
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/study-join-request/` | 스터디 가입 요청 | ✅ |
| GET | `/study-join-request/user/` | 사용자 가입 요청 목록 | ✅ |
| GET | `/studies/<study_id>/join-requests/` | 스터디 가입 요청 목록 | ✅ |
| POST | `/study-join-request/<request_id>/respond/` | 가입 요청 응답 | ✅ |
| POST | `/study-join-request/<request_id>/cancel/` | 가입 요청 취소 | ✅ |
| DELETE | `/study-join-request/user/<study_id>/` | 사용자 가입 요청 삭제 | ✅ |

### 4.5 스터디 진행률 관리
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/record-study-progress/` | 스터디 진행률 기록 | ✅ |
| GET | `/study-progress-history/<study_id>/` | 스터디 진행률 이력 | ✅ |
| GET | `/study-time-statistics/<study_id>/` | 스터디 시간 통계 | ✅ |

### 4.6 스터디 데이터 관리
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/studies/<study_id>/download-excel/` | 스터디 Excel 다운로드 | ✅ |
| POST | `/studies/upload-excel/` | 스터디 Excel 업로드 | ✅ |

## 5. 🎯 고급 기능 (Advanced Features)

### 5.1 즐겨찾기 관리
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/favorite-exam/` | 즐겨찾기 시험 조회/생성 | ✅ |
| GET | `/favorite-exam-questions/` | 즐겨찾기 문제 목록 | ✅ |
| POST | `/add-question-to-favorite/` | 문제를 즐겨찾기에 추가 | ✅ |
| POST | `/remove-question-from-favorite/` | 즐겨찾기에서 문제 제거 | ✅ |

### 5.2 랜덤 출제
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/create-random-recommendation-exam/` | 랜덤 추천 시험 생성 | ✅ |
| GET | `/random-recommendation-exam-questions/` | 랜덤 추천 시험 문제 | ✅ |
| GET | `/random-exam-email-users/` | 랜덤 시험 이메일 사용자 | ✅ |
| GET | `/daily-exam/` | 일일 시험 조회/생성 | ✅ |

### 5.3 정확도 조정
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/bulk-adjust-user-accuracy/` | 사용자 정확도 일괄 조정 | ✅ |

### 5.4 데이터 정리
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/retention-cleanup/manual/` | 수동 데이터 정리 | ✅ |

## 6. 🎤 실시간 기능 (Realtime Features)

### 6.1 실시간 세션 관리
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/realtime/session/` | 실시간 세션 생성 | ✅ |
| GET | `/realtime/session/<session_id>/` | 실시간 세션 정보 | ✅ |
| DELETE | `/realtime/session/<session_id>/delete/` | 실시간 세션 삭제 | ✅ |
| POST | `/realtime/function-call/` | 실시간 함수 호출 | ✅ |

### 6.2 WebRTC 음성 처리
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/realtime/session/<session_id>/offer/` | WebRTC Offer 처리 | ✅ |
| POST | `/realtime/session/<session_id>/ice-candidate/` | ICE Candidate 처리 | ✅ |
| POST | `/realtime/session/<session_id>/speak/` | 음성 녹음 시작 | ✅ |
| POST | `/realtime/session/<session_id>/stop-speak/` | 음성 녹음 중지 | ✅ |

## 7. 🤖 AI 기능 (AI Features)

### 7.1 답변 평가
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/evaluate-answer/` | AI 답변 평가 | ✅ |

## 8. 🌐 다국어 지원 (Multilingual Support)

### 8.1 번역 관리
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/translations/` | 번역 데이터 조회 | ❌ |
| POST | `/translate/` | 텍스트 번역 | ✅ |

## 9. 🔧 시스템 관리 (System Management)

### 9.1 시스템 상태
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/health/` | 시스템 상태 확인 | ❌ |

### 9.2 캐시 관리
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/clear-all-cache/` | 전체 캐시 정리 | ✅ (Admin) |
| POST | `/clear-study-cache/` | 스터디 캐시 정리 | ✅ (Admin) |

### 9.3 데이터 관리
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/users/download-excel/` | 사용자 Excel 다운로드 | ✅ (Admin) |
| POST | `/users/upload-excel/` | 사용자 Excel 업로드 | ✅ (Admin) |
| POST | `/fix-member-connections/` | 멤버 연결 수정 | ✅ (Admin) |

## 📊 응답 형식

### 성공 응답
```json
{
  "status": "success",
  "data": { ... },
  "message": "요청이 성공적으로 처리되었습니다."
}
```

### 에러 응답
```json
{
  "status": "error",
  "error": "에러 메시지",
  "details": { ... }
}
```

### 페이지네이션 응답
```json
{
  "count": 100,
  "next": "http://api.example.com/items/?page=2",
  "previous": null,
  "results": [ ... ]
}
```

## 🔒 인증 헤더

### CSRF 토큰
```
X-CSRFToken: <csrf_token>
```

### 세션 쿠키
```
Cookie: sessionid=<session_id>; csrftoken=<csrf_token>
```

## 📝 요청 예시

### 문제 업로드
```bash
curl -X POST \
  http://localhost:8000/api/upload-questions/ \
  -H 'X-CSRFToken: <csrf_token>' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@questions.csv'
```

### 시험 생성
```bash
curl -X POST \
  http://localhost:8000/api/create-exam/ \
  -H 'X-CSRFToken: <csrf_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "새로운 시험",
    "description": "시험 설명",
    "questions": ["question_id_1", "question_id_2"]
  }'
```

### 시험 제출
```bash
curl -X POST \
  http://localhost:8000/api/submit-exam/ \
  -H 'X-CSRFToken: <csrf_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "exam_id": "exam_uuid",
    "answers": [
      {"question_id": "q1", "answer": "답안1"},
      {"question_id": "q2", "answer": "답안2"}
    ]
  }'
```

## 🚀 새로운 버전 개발 시 고려사항

### 1. API 버전 관리
- URL 버전 관리: `/api/v2/`
- 하위 호환성 보장
- 점진적 마이그레이션

### 2. 인증 방식 개선
- JWT 토큰 도입
- OAuth 2.0 확장
- API 키 인증

### 3. 응답 형식 표준화
- OpenAPI 3.0 스펙 준수
- 일관된 에러 코드
- 상세한 API 문서

### 4. 성능 최적화
- GraphQL 도입 검토
- 캐싱 전략 개선
- 배치 처리 API

### 5. 실시간 기능 확장
- WebSocket 지원
- Server-Sent Events
- 실시간 알림

이 API 명세서는 DrillQuiz의 현재 API 구조를 종합적으로 정리한 것으로, 새로운 버전 개발 시 참조할 수 있는 기술적 가이드입니다.
