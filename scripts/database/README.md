# Database Management Scripts

데이터베이스 관리 및 유지보수를 위한 스크립트들입니다.

## 📁 Scripts

### `clear_all_statistics.py`
- **목적**: 통계 데이터 초기화
- **사용법**: 
  - 모든 통계 삭제: `python clear_all_statistics.py [--force]`
  - 특정 사용자 삭제: `python clear_all_statistics.py --user <username>`
- **기능**: 
  - 시험 결과, 진행률 기록, 정확도 조정 이력 삭제
  - StudyTask progress 필드 초기화
  - Django 캐시 및 세션 정리
  - 자동 백업 생성

### `check_user_progress.py`
- **목적**: 사용자 진행률 데이터 확인
- **사용법**: `python check_user_progress.py [username]`
- **기능**: 
  - 사용자별 스터디 참여 현황
  - StudyTask progress 필드 상태
  - StudyTaskProgress 레코드 확인

### `check_db_status.py`
- **목적**: 데이터베이스 상태 확인
- **사용법**: `python check_db_status.py`
- **기능**: 
  - 데이터베이스 연결 상태
  - 테이블별 레코드 수
  - 시스템 상태 점검

### `check_progress.py`
- **목적**: 진행률 데이터 확인
- **사용법**: `python check_progress.py`
- **기능**: 
  - 전체 진행률 현황
  - 사용자별 진행률 요약

### `check_user.py`
- **목적**: 사용자 데이터 확인
- **사용법**: `python check_user.py [username]`
- **기능**: 
  - 사용자 정보 및 권한
  - 관련 데이터 현황

### `test_translation_manager.py`
- **목적**: 번역 기능 테스트
- **사용법**: `python test_translation_manager.py`
- **기능**: 
  - TranslationManager 기능 검증
  - 다국어 필드 번역 테스트

### `test_translation_manager_debug.py`
- **목적**: 번역 기능 디버깅 테스트
- **사용법**: `python test_translation_manager_debug.py`
- **기능**: 
  - 번역 기능 상세 디버깅 정보 확인
  - 번역 과정 로깅

### `test_favorite_api.py`
- **목적**: 즐겨찾기 API 테스트
- **사용법**: `python test_favorite_api.py`
- **기능**: 
  - 즐겨찾기 API 동작 검증

### `test_correct_count.py`
- **목적**: 정답 개수 계산 테스트
- **사용법**: `python test_correct_count.py`
- **기능**: 
  - 정답 개수 계산 로직 검증

### `test_submit_api.py`
- **목적**: 시험 제출 API 테스트
- **사용법**: `python test_submit_api.py`
- **기능**: 
  - 시험 제출 API 동작 검증

### `fix_exam_result_summaries.py`
- **목적**: ExamResult 요약 필드 수정
- **사용법**: `python fix_exam_result_summaries.py`
- **기능**: 
  - ExamResultDetail 기반으로 요약 필드 재계산
  - 정답 개수, 총점, 오답 개수 수정
  - 데이터 무결성 복구

### `delete_estimated_records.py`
- **목적**: 추정된 기록 삭제
- **사용법**: `python delete_estimated_records.py`
- **기능**: 
  - elapsed_seconds가 0인 추정 기록 삭제
  - 데이터 품질 개선
  - 사용자 확인 후 삭제 실행

### `create_paypal_questions.py`
- **목적**: PayPal 알고리즘 문제 생성
- **사용법**: `python create_paypal_questions.py`
- **기능**: 
  - 엑셀 파일에서 문제 데이터 읽기
  - Question 모델에 문제 생성
  - Exam에 문제 연결
  - 대량 데이터 초기화

### `fix_seq_column.py`
- **목적**: quiz_studytask 테이블의 seq 컬럼 삭제
- **사용법**: `python fix_seq_column.py`
- **기능**: 
  - PostgreSQL DB에서 seq 컬럼 제거
  - 관련 인덱스 정리
  - 마이그레이션 오류 해결

### `fix_study_columns.py`
- **목적**: quiz_study 테이블의 created_at, updated_at 컬럼 삭제
- **사용법**: `python fix_study_columns.py`
- **기능**: 
  - 개발 환경 DB에서 컬럼 제거
  - 마이그레이션 오류 해결
  - 테이블 구조 정리

### `fix_study_columns_prod.py`
- **목적**: 운영 환경 quiz_study 테이블의 created_at, updated_at 컬럼 삭제
- **사용법**: `python fix_study_columns_prod.py`
- **기능**: 
  - 운영 환경 DB에서 컬럼 제거
  - 마이그레이션 오류 해결
  - 테이블 구조 정리

### `check_dev_final.py`
- **목적**: 개발 환경 최종 상태 확인
- **사용법**: `python check_dev_final.py`
- **기능**: 
  - 개발 환경 DB 상태 점검
  - 마이그레이션 상태 확인

### `fix_dev_db.py`
- **목적**: 개발 환경 DB 문제 수정
- **사용법**: `python fix_dev_db.py`
- **기능**: 
  - 개발 환경 DB 오류 수정
  - 데이터 무결성 복구

### `check_dev_model.py`
- **목적**: 개발 환경 모델 상태 확인
- **사용법**: `python check_dev_model.py`
- **기능**: 
  - 개발 환경 모델 상태 점검
  - 데이터베이스 스키마 확인

### `check_production_data.py`
- **목적**: 운영 환경 데이터 상태 확인
- **사용법**: `python check_production_data.py`
- **기능**: 
  - 운영 환경 데이터 품질 점검
  - 데이터 무결성 확인

### `check_production_migrations.py`
- **목적**: 운영 환경 마이그레이션 상태 확인
- **사용법**: `python check_production_migrations.py`
- **기능**: 
  - 운영 환경 마이그레이션 상태 점검
  - 적용된 마이그레이션 목록 확인

### `check_progress_debug.py`
- **목적**: 진행률 디버깅 정보 확인
- **사용법**: `python check_progress_debug.py`
- **기능**: 
  - 진행률 관련 디버깅 정보 출력
  - 문제 진단을 위한 상세 정보 제공

### `fix_dev_sqlite.py`
- **목적**: 개발 환경 SQLite DB 문제 수정
- **사용법**: `python fix_dev_sqlite.py`
- **기능**: 
  - 개발 환경 SQLite DB 오류 수정
  - 데이터 무결성 복구

### `fix_production_migrations.py`
- **목적**: 운영 환경 마이그레이션 문제 수정
- **사용법**: `python fix_production_migrations.py`
- **기능**: 
  - 운영 환경 마이그레이션 오류 수정
  - 마이그레이션 상태 복구

### `fix_seq_column_direct.py`
- **목적**: Django dbshell을 사용한 seq 컬럼 삭제
- **사용법**: `python fix_seq_column_direct.py`
- **기능**: 
  - Django dbshell을 통한 seq 컬럼 제거
  - 마이그레이션 오류 해결

### `fix_seq_column_shell.py`
- **목적**: Django shell을 사용한 seq 컬럼 삭제
- **사용법**: `python fix_seq_column_shell.py`
- **기능**: 
  - Django shell을 통한 seq 컬럼 제거
  - PostgreSQL DB 직접 접근

### `debug_permissions.py`
- **목적**: 권한 관련 디버깅 정보 확인
- **사용법**: `python debug_permissions.py`
- **기능**: 
  - 사용자 권한 상태 디버깅
  - 권한 관련 문제 진단

### `debug_doohee323_data.py`
- **목적**: 특정 사용자(doohee323) 데이터 디버깅
- **사용법**: `python debug_doohee323_data.py`
- **기능**: 
  - 특정 사용자 데이터 상태 확인
  - 사용자별 문제 진단

### `debug_api_data.py`
- **목적**: API 데이터 디버깅 정보 확인
- **사용법**: `python debug_api_data.py`
- **기능**: 
  - API 응답 데이터 상태 확인
  - API 관련 문제 진단

### `debug_algorithm_progress.py`
- **목적**: 알고리즘 진행률 디버깅 정보 확인
- **사용법**: `python debug_algorithm_progress.py`
- **기능**: 
  - 알고리즘 문제 진행률 상태 확인
  - 진행률 관련 문제 진단

### `clean_dev_db.py`
- **목적**: 개발 환경 데이터베이스 정리
- **사용법**: `python clean_dev_db.py`
- **기능**: 
  - 개발 환경 DB 데이터 정리
  - 테스트 데이터 초기화

### `clean_production_db.py`
- **목적**: 운영 환경 데이터베이스 정리
- **사용법**: `python clean_production_db.py`
- **기능**: 
  - 운영 환경 DB 데이터 정리
  - 불필요한 데이터 제거

### `rollback_migrations.py`
- **목적**: 문제가 되는 마이그레이션들 롤백
- **사용법**: `python rollback_migrations.py`
- **기능**: 
  - 0041, 0042 마이그레이션 롤백
  - created_at, updated_at, seq 컬럼 제거
  - django_migrations 테이블 정리
  - 마이그레이션 오류 해결

### `check_dev_db_status.py`
- **목적**: 개발 환경 PostgreSQL DB 상태 확인
- **사용법**: `python check_dev_db_status.py`
- **기능**: 
  - DB 연결 상태 확인
  - 테이블 구조 및 레코드 수 확인
  - 마이그레이션 상태 점검
  - 전체 DB 상태 진단

### `fix_study_columns_prod.py`
- **목적**: 운영 환경 quiz_study 테이블의 created_at, updated_at 컬럼 삭제
- **사용법**: `python fix_study_columns_prod.py`
- **기능**: 
  - 운영 환경 DB에서 컬럼 제거
  - 마이그레이션 오류 해결
  - 테이블 구조 정리

## ⚠️ 주의사항

- **백업**: 실행 전 반드시 백업을 확인하세요
- **권한**: 프로덕션 환경에서는 신중하게 사용하세요
- **테스트**: 개발 환경에서 먼저 테스트하세요

## 🔄 실행 순서

1. 백업 확인
2. 스크립트 실행
3. 결과 검증
4. 필요시 롤백
