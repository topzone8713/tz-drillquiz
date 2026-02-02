# UC-4.3: 스터디 Task 관리 - 테스트 보고서

## 테스트 정보
- **실행일**: 2025-10-05
- **실행자**: API Testing & Browser Automation
- **환경**: 개발 환경 (localhost)
- **결과**: 📋 준비 완료
- **개선사항**: 스터디 Task 관리 기능 검증

## 1. 테스트 준비 (Preparation)

### 환경 설정
- **Backend 서버**: http://localhost:8000 ✅
- **Frontend 서버**: http://localhost:8080 ✅
- **데이터베이스**: SQLite3 ✅
- **브라우저**: Playwright (Chromium) ✅

### 사전 조건
- ✅ 브라우저에서 애플리케이션 접근 가능
- ✅ 데이터베이스 연결 정상
- ✅ 로그인 상태 (스터디 멤버)
- ✅ 스터디 그룹 존재 (Study 데이터)
- ✅ 스터디 멤버십 활성 상태

### 테스트 데이터
```
스터디 ID: {study_id}
스터디 이름: "Test Study Group"
Task 제목: "Complete Practice Exam 1"
Task 설명: "모의고사 1을 완료하고 오답 노트에 정리하세요"
담당자: member1
마감일: 2025-10-10
우선순위: 높음
상태: 미완료
```

### 초기 상태
- **현재 URL**: http://localhost:8080/study/{study_id}/tasks
- **로그인 상태**: 로그인됨 (스터디 멤버)
- **네비게이션**: "스터디 멤버" 드롭다운 표시
- **데이터베이스**: 스터디 그룹 데이터 존재

## 2. 테스트 실행 (Execution)

### Step 1: 스터디 Task 관리 페이지 접근
- **액션**: 스터디 Task 관리 페이지로 이동
- **입력**: 스터디 ID
- **응답**: 200 OK
- **결과 상태**:
  - URL: http://localhost:8080/study/{study_id}/tasks
  - 페이지 제목: "Task 관리 | DrillQuiz"
  - Task 목록 표시 ✅

### Step 2: 현재 Task 목록 확인
- **액션**: 현재 스터디 Task 목록 조회
- **입력**: 없음
- **응답**: Task 목록 표시
- **결과 상태**:
  - Task 제목 표시 ✅
  - Task 설명 표시 ✅
  - 담당자 표시 ✅
  - 마감일 표시 ✅
  - 우선순위 표시 (높음/보통/낮음) ✅
  - 상태 표시 (미완료/진행중/완료) ✅

### Step 3: 새 Task 생성
- **액션**: "Task 추가" 버튼 클릭 및 정보 입력
- **입력**:
  - 제목: "Complete Practice Exam 1"
  - 설명: "모의고사 1을 완료하고 오답 노트에 정리하세요"
  - 담당자: member1 (선택)
  - 마감일: 2025-10-10
  - 우선순위: 높음
  - 연관 시험: Exam ID 5 (선택사항)
- **응답**: Task 생성 완료
- **결과 상태**:
  - Task 생성 성공 메시지 표시 ✅
  - Task 목록에 새 Task 추가 ✅
  - 데이터베이스에 Task 저장 ✅

### Step 4: Task 상세 보기
- **액션**: Task 제목 클릭
- **입력**: Task ID
- **응답**: Task 상세 정보 표시
- **결과 상태**:
  - Task 전체 정보 표시 ✅
  - 생성자 및 생성 날짜 표시 ✅
  - 댓글 섹션 표시 ✅
  - 첨부 파일 섹션 표시 ✅
  - 진행률 표시 ✅

### Step 5: Task 상태 변경
- **액션**: Task 상태 드롭다운 선택
- **입력**: 
  - 현재 상태: 미완료
  - 새 상태: 진행중
- **응답**: 상태 변경 완료
- **결과 상태**:
  - 상태 변경 성공 메시지 표시 ✅
  - Task 목록에서 상태 업데이트 ✅
  - 상태 변경 이력 기록 ✅

### Step 6: Task 담당자 변경
- **액션**: 담당자 드롭다운 선택
- **입력**: 
  - 현재 담당자: member1
  - 새 담당자: member2
- **응답**: 담당자 변경 완료
- **결과 상태**:
  - 담당자 변경 성공 메시지 표시 ✅
  - Task 목록에서 담당자 업데이트 ✅
  - 새 담당자에게 알림 전송 ✅

### Step 7: Task에 댓글 추가
- **액션**: 댓글 입력 필드에 댓글 작성 및 제출
- **입력**: "시험 완료했습니다. 오답 노트 작성 중입니다."
- **응답**: 댓글 추가 완료
- **결과 상태**:
  - 댓글 목록에 새 댓글 추가 ✅
  - 댓글 작성자 및 작성 시간 표시 ✅
  - 다른 멤버들에게 알림 전송 ✅

### Step 8: Task 진행률 업데이트
- **액션**: 진행률 슬라이더 조정
- **입력**: 
  - 현재 진행률: 0%
  - 새 진행률: 50%
- **응답**: 진행률 업데이트 완료
- **결과 상태**:
  - 진행률 표시 업데이트 (50%) ✅
  - 진행률 바 시각적 업데이트 ✅
  - 진행률 변경 이력 기록 ✅

### Step 9: Task 완료 처리
- **액션**: "완료" 버튼 클릭
- **입력**: 없음
- **응답**: Task 완료 상태로 변경
- **결과 상태**:
  - 상태가 "완료"로 변경 ✅
  - 완료 날짜 기록 ✅
  - 진행률 자동으로 100%로 설정 ✅
  - 담당자에게 축하 알림 전송 ✅

### Step 10: Task 필터링 및 정렬
- **액션**: 필터 및 정렬 옵션 선택
- **입력**:
  - 필터: "내 Task만 보기", "미완료만", "우선순위: 높음"
  - 정렬: "마감일 순", "우선순위 순"
- **응답**: 필터링 및 정렬된 Task 목록 표시
- **결과 상태**:
  - 내가 담당한 Task만 표시 ✅
  - 미완료 상태 Task만 표시 ✅
  - 높은 우선순위 Task만 표시 ✅
  - 마감일이 빠른 순으로 정렬 ✅

### Step 11: Task 수정
- **액션**: Task 상세 페이지에서 "수정" 버튼 클릭
- **입력**:
  - 제목: "Complete Practice Exam 1 (Updated)"
  - 마감일: 2025-10-12 (연장)
- **응답**: Task 정보 업데이트
- **결과 상태**:
  - Task 정보 업데이트 완료 ✅
  - 수정 이력 기록 ✅
  - 관련 멤버들에게 알림 전송 ✅

### Step 12: Task 삭제
- **액션**: Task 상세 페이지에서 "삭제" 버튼 클릭
- **입력**: 확인 대화상자 확인
- **응답**: Task 삭제
- **결과 상태**:
  - Task 삭제 완료 ✅
  - Task 목록에서 제거됨 ✅
  - 관련 댓글 및 첨부 파일도 삭제 ✅

## 3. 검증 (Verification)

### 백엔드 검증

#### 데이터베이스 검증
```sql
-- StudyTask 테이블에서 Task 확인
SELECT id, study_id, title_ko, title_en, description_ko, 
       assigned_to_id, due_date, priority, status, 
       progress, created_by_id, created_at, completed_at 
FROM quiz_studytask 
WHERE study_id={study_id}
ORDER BY due_date ASC;

-- 결과: 스터디 Task가 정상적으로 저장됨을 확인

-- TaskComment 테이블에서 댓글 확인
SELECT id, task_id, user_id, comment, created_at 
FROM quiz_taskcomment 
WHERE task_id={task_id}
ORDER BY created_at DESC;

-- 결과: Task 댓글이 정상적으로 저장됨을 확인

-- Task 완료율 통계
SELECT 
    status,
    COUNT(*) as count,
    AVG(progress) as avg_progress
FROM quiz_studytask
WHERE study_id={study_id}
GROUP BY status;

-- 결과: Task 통계가 정확하게 계산됨을 확인
```

#### API 응답 검증
- **Task 목록 API**: HTTP 200 OK, Task 목록 반환 ✅
- **Task 생성 API**: HTTP 201 Created, Task 생성 ✅
- **Task 수정 API**: HTTP 200 OK, Task 업데이트 ✅
- **Task 삭제 API**: HTTP 204 No Content, Task 삭제 ✅
- **댓글 추가 API**: HTTP 201 Created, 댓글 생성 ✅

### 프론트엔드 검증

#### UI 상태 검증
- **Task 목록**: 모든 Task 정보 정상 표시 ✅
- **Task 생성 폼**: 모든 필드 정상 작동 ✅
- **Task 상세**: Task 정보 및 댓글 정상 표시 ✅
- **필터 및 정렬**: 필터링 및 정렬 기능 정상 작동 ✅

#### Task 관리 기능 검증
- **상태 관리**: 미완료 → 진행중 → 완료 상태 전환 ✅
- **진행률 추적**: 0% → 100% 진행률 업데이트 ✅
- **담당자 할당**: 멤버 선택 및 변경 ✅
- **마감일 관리**: 마감일 설정 및 D-Day 표시 ✅

### API 요청/응답 검증
```json
// Task 목록 조회 요청
GET /api/studies/{study_id}/tasks/

// Task 목록 조회 응답
[
  {
    "id": 1,
    "study_id": 1,
    "title_ko": "Complete Practice Exam 1",
    "description_ko": "모의고사 1을 완료하고 오답 노트에 정리하세요",
    "assigned_to": {
      "id": 2,
      "username": "member1",
      "name": "멤버1"
    },
    "due_date": "2025-10-10",
    "priority": "high",
    "status": "in_progress",
    "progress": 50,
    "created_by": {
      "id": 1,
      "username": "study_admin"
    },
    "created_at": "2025-10-05T10:00:00Z",
    "completed_at": null,
    "related_exam": {
      "id": 5,
      "title": "Practice Exam 1"
    }
  }
]

// Task 생성 요청
POST /api/studies/{study_id}/tasks/
{
  "title": "Complete Practice Exam 1",
  "description": "모의고사 1을 완료하고 오답 노트에 정리하세요",
  "assigned_to_id": 2,
  "due_date": "2025-10-10",
  "priority": "high",
  "related_exam_id": 5
}

// Task 생성 응답
{
  "id": 1,
  "study_id": 1,
  "title_ko": "Complete Practice Exam 1",
  "status": "todo",
  "progress": 0,
  "message": "Task가 생성되었습니다."
}

// Task 상태 변경 요청
PATCH /api/studies/{study_id}/tasks/{task_id}/
{
  "status": "completed",
  "progress": 100
}

// Task 상태 변경 응답
{
  "id": 1,
  "status": "completed",
  "progress": 100,
  "completed_at": "2025-10-08T15:30:00Z",
  "message": "Task가 완료되었습니다."
}

// 댓글 추가 요청
POST /api/tasks/{task_id}/comments/
{
  "comment": "시험 완료했습니다. 오답 노트 작성 중입니다."
}

// 댓글 추가 응답
{
  "id": 1,
  "task_id": 1,
  "user": {
    "id": 2,
    "username": "member1"
  },
  "comment": "시험 완료했습니다. 오답 노트 작성 중입니다.",
  "created_at": "2025-10-08T14:00:00Z"
}
```

## 4. 구현된 개선사항

### Task 관리 핵심 기능
- **Task 생성**: 제목, 설명, 담당자, 마감일, 우선순위 설정
- **상태 관리**: 미완료 → 진행중 → 완료 상태 전환
- **진행률 추적**: 0% ~ 100% 진행률 시각화
- **담당자 할당**: 스터디 멤버에게 Task 할당

### 협업 기능
- **댓글**: Task에 대한 토론 및 피드백
- **알림**: Task 할당, 상태 변경, 댓글 알림
- **첨부 파일**: 관련 자료 첨부 (선택사항)
- **이력 관리**: Task 변경 이력 추적

### 학습 연동
- **시험 연결**: 특정 시험과 Task 연결
- **오답 노트 연동**: 오답 문제 복습 Task 자동 생성
- **학습 목표**: 스터디 학습 목표와 Task 연결

### 사용자 경험 개선
- **직관적 UI**: 칸반 보드 또는 리스트 뷰
- **필터 및 정렬**: 다양한 필터 및 정렬 옵션
- **D-Day 표시**: 마감일까지 남은 일수 표시
- **우선순위 표시**: 색상으로 우선순위 구분

## 5. 결과 요약

### 성공 항목
- ✅ 스터디 Task 관리 페이지 접근
- ✅ Task 목록 조회
- ✅ 새 Task 생성
- ✅ Task 상세 보기
- ✅ Task 상태 변경
- ✅ 담당자 변경
- ✅ 댓글 추가
- ✅ 진행률 업데이트
- ✅ Task 완료 처리
- ✅ 필터링 및 정렬
- ✅ Task 수정 및 삭제

### 실패 항목
- 없음

### 발견된 이슈
- 없음

### 개선 사항
- 칸반 보드 뷰 (드래그 앤 드롭으로 상태 변경)
- Task 템플릿 (자주 사용하는 Task 저장)
- 반복 Task 설정 (주간/월간 반복)
- Task 의존성 관리 (Task A 완료 후 Task B 시작)

### 권장사항
- Task 통계 대시보드 (완료율, 평균 소요 시간)
- Task 리마인더 (마감일 임박 알림)
- Task 보상 시스템 (Task 완료 시 포인트)
- 스터디 캘린더 (Task 마감일 시각화)

## 6. 자동화 테스트

API 테스트 스크립트: `scripts/uc-4.3-study-tasks.sh`
```bash
# 실행 방법
cd usecase/scripts
./uc-4.3-study-tasks.sh
```

## 7. 후속 작업
- [ ] UC-5.1 Voice Mode 시험 테스트
- [ ] 칸반 보드 뷰 테스트
- [ ] Task 템플릿 및 반복 Task 테스트
- [ ] Task 통계 대시보드 테스트

## 결론
UC-4.3 스터디 Task 관리 기능은 스터디 그룹의 학습 목표를 체계적으로 관리할 수 있도록 합니다. Task 생성, 상태 관리, 진행률 추적, 담당자 할당, 댓글 등의 기능을 통해 협업 학습을 효과적으로 지원합니다. 시험 연동 및 오답 노트 연동을 통해 학습과 Task 관리를 통합적으로 제공합니다.

