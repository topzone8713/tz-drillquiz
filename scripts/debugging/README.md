# Debugging Scripts

시스템 디버깅 및 문제 해결을 위한 스크립트들입니다.

## 📁 Directory Structure

```
debugging/
├── api/          # API 관련 디버깅
├── database/     # 데이터베이스 관련 디버깅
├── system/       # 시스템 전반 디버깅
└── README.md     # 이 파일
```

## 🎯 Categories

### API Debugging (`api/`)
API 응답, 요청, 제출 등의 문제를 디버깅하는 스크립트들입니다.

**주요 스크립트:**
- `debug_api_response.py` - API 응답 디버깅
- `debug_submit.py` - 제출 과정 디버깅

### Database Debugging (`database/`)
데이터베이스 연결, 쿼리, 데이터 무결성 등을 디버깅하는 스크립트들입니다.

**주요 스크립트:**
- `debug_connection.py` - 데이터베이스 연결 디버깅
- `debug_created_by.py` - 생성자 정보 디버깅
- `debug_question_group.py` - 문제 그룹 디버깅

### System Debugging (`system/`)
시스템 전반의 성능, 정확도, 시간 등을 디버깅하는 스크립트들입니다.

**주요 스크립트:**
- `debug_dashboard.py` - 대시보드 디버깅
- `debug_exam_accuracy.py` - 시험 정확도 디버깅
- `debug_exam_list.py` - 시험 목록 디버깅
- `debug_exam_time.py` - 시험 시간 디버깅
- `debug_study_time.py` - 학습 시간 디버깅

## 🚀 Quick Start

### API 디버깅
```bash
cd scripts/debugging/api
python debug_api_response.py
```

### 데이터베이스 디버깅
```bash
cd scripts/debugging/database
python debug_connection.py
```

### 시스템 디버깅
```bash
cd scripts/debugging/system
python debug_dashboard.py
```

## ⚠️ 주의사항

- **개발 환경**: 프로덕션에서는 사용하지 마세요
- **데이터 보호**: 민감한 정보가 포함될 수 있습니다
- **일회성**: 특정 문제 해결 후 삭제를 고려하세요
- **문서화**: 디버깅 결과는 문서화하세요

## 🔄 디버깅 프로세스

1. 문제 상황 파악
2. 적절한 디버깅 스크립트 선택
3. 스크립트 실행 및 결과 분석
4. 문제 원인 파악
5. 해결책 적용
6. 결과 검증
7. 필요시 스크립트 정리

## 📝 디버깅 결과 관리

- **로그 파일**: 디버깅 결과를 로그로 저장
- **문서화**: 중요한 발견사항은 문서화
- **공유**: 팀원들과 디버깅 경험 공유
- **정리**: 해결된 문제의 디버깅 스크립트는 정리

---

**마지막 업데이트**: 2025-08-14
**버전**: 1.0.0
