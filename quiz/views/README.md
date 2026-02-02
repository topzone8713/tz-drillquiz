# Views 리팩토링 계획

## 현재 상황
- `quiz/views.py` 파일이 5,712줄로 매우 큼
- 하나의 파일에 모든 뷰가 집중되어 있어 유지보수가 어려움
- 순환 import 문제로 인해 점진적 분리가 어려움

## 리팩토링 목표
기존 `views.py` 파일을 기능별로 분리하여 관리하기 쉽게 만들기

## 분리 계획

### 1. 인증 관련 뷰 (`auth_views.py`) ✅
- `get_csrf_token`
- `test_csrf`
- `logout_view`
- `RegisterView`
- `LoginView`
- `ChangePasswordView`

### 2. 문제 관련 뷰 (`question_views.py`)
- `upload_questions`
- `get_questions`
- `get_question`
- `create_single_question_exam`
- `delete_question_results`
- `delete_question_results_global`
- `ignore_question`
- `unignore_question`
- `check_question_ignored`
- `get_ignored_questions`

### 3. 시험 관련 뷰 (`exam_views.py`)
- `create_exam`
- `get_exam`
- `get_exam_questions`
- `delete_exam`
- `update_exam`
- `submit_exam`
- `get_exam_results`
- `get_exams`
- `exam_result_detail`
- `retake_exam`
- `retake_wrong_questions`
- `save_random_practice_result`
- `continue_exam`
- `toggle_exam_original`

### 4. 스터디 관련 뷰 (`study_views.py`)
- `StudyViewSet`
- `StudyTaskViewSet`
- `MemberViewSet`
- `create_question_member_mapping`
- `get_question_member_mappings`
- `get_question_statistics`
- `record_study_progress`
- `get_study_progress_history`
- `get_study_time_statistics`

### 5. 사용자 관리 뷰 (`user_views.py`)
- `user_profile`
- `change_language`
- `UserListView`
- `UserCreateView`
- `UserUpdateView`
- `download_users_excel`
- `upload_users_excel`
- `delete_user`
- `delete_users_bulk`
- `delete_all_users`
- `search_users`
- `admin_change_user_password`
- `export_user_data`

### 6. 파일 관리 뷰 (`file_views.py`)
- `list_question_files`
- `download_question_file`
- `delete_question_file`
- `update_question_file`
- `download_exams_excel`
- `upload_exams_excel`
- `download_study_excel`
- `upload_study_excel`

### 7. 기타 뷰 (`misc_views.py`)
- `get_exam_list_for_move`
- `move_questions_to_exam`
- `move_questions`
- `copy_questions`
- `delete_questions`
- `add_question_to_exam`
- `delete_question`
- `bulk_update_question_group`
- `update_exam_questions_from_excel`
- `get_or_create_favorite_exam`
- `add_question_to_favorite`
- `get_question_original_exams`
- `fix_member_user_connections`
- `create_random_recommendation_exam`
- `get_random_recommendation_exam_questions`
- `get_random_exam_email_users`
- `get_translations`

## 구현 단계

### 1단계: 기본 구조 설정 ✅
- [x] `quiz/views/` 디렉토리 생성
- [x] `__init__.py` 파일 생성 (기존 호환성 유지)
- [x] `auth_views.py` 파일 생성 및 인증 뷰 분리

### 2단계: 점진적 분리 (현재 진행 중)
- [x] 인증 관련 뷰 분리
- [ ] 문제 관련 뷰 분리
- [ ] 시험 관련 뷰 분리
- [ ] 스터디 관련 뷰 분리
- [ ] 사용자 관리 뷰 분리
- [ ] 파일 관리 뷰 분리
- [ ] 기타 뷰 분리

### 3단계: URL 패턴 업데이트
- [ ] `urls.py`에서 새로운 뷰 구조 반영

### 4단계: 테스트 및 검증
- [ ] 모든 API 엔드포인트 정상 작동 확인
- [ ] 기존 기능 호환성 확인

## 현재 문제점
- 순환 import 문제로 인해 점진적 분리가 어려움
- `urls.py`에서 직접 import하는 뷰들이 많음

## 해결 방안 (수정됨)
1. 먼저 기존 `views.py`를 그대로 유지
2. 새로운 뷰 파일들을 생성하고 테스트
3. 모든 분리가 완료된 후 `urls.py` 업데이트
4. 마지막에 기존 `views.py` 제거

## 새로운 접근 방법
1. 기존 `views.py`를 `views_original.py`로 백업
2. 새로운 구조로 뷰들을 분리
3. 모든 테스트 완료 후 기존 파일 제거

## 주의사항
- 기존 API 호환성을 유지해야 함
- 점진적으로 분리하여 안정성 확보
- 각 파일의 크기는 500줄 이하로 유지 