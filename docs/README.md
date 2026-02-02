# DrillQuiz 시스템 분석 및 참조 문서

## 📋 개요

DrillQuiz는 다국어 지원 온라인 퀴즈 학습 플랫폼으로, Django REST Framework 백엔드와 Vue.js 프론트엔드로 구성된 풀스택 웹 애플리케이션입니다.

## 🔧 운영 및 디버깅

- **[운영 환경 디버깅 가이드](./PRODUCTION_DEBUGGING_GUIDE.md)** - Kubernetes 접근, 데이터베이스 접근, Pod 로그 확인 등 운영 환경 디버깅을 위한 종합 가이드

## 🏗️ 시스템 아키텍처

### 백엔드 (Backend)
- **프레임워크**: Django 4.2.7 + Django REST Framework 3.14.0
- **데이터베이스**: 
  - 개발환경: SQLite3
  - 프로덕션환경: PostgreSQL (Docker 환경)
- **캐시**: 
  - 개발환경: 로컬 메모리 캐시 (LocMemCache)
  - 프로덕션환경: Redis Cluster
- **파일 스토리지**: 
  - 개발환경: 로컬 파일 시스템
  - 프로덕션환경: MinIO (S3 호환)
- **포트**: 8000

### 프론트엔드 (Frontend)
- **프레임워크**: Vue.js 2.6.14
- **UI 라이브러리**: Bootstrap 5.3.2 + Bootstrap Vue 2.22.0
- **국제화**: Vue I18n 8.28.2
- **차트**: Chart.js 4.5.0
- **파일 처리**: SheetJS (xlsx) 0.18.5
- **음성 처리**: RecordRTC 5.6.2, WebRTC Adapter 9.0.3
- **포트**: 8080

### 외부 API 및 서비스
- **번역 서비스**: OpenAI API (GPT 기반 자동 번역)
- **OAuth 인증**: Google OAuth 2.0
- **이메일 서비스**: Django 내장 이메일 시스템
- **배포**: Kubernetes (K8s) 환경

## 🗄️ 데이터베이스 스키마 분석

### 핵심 엔티티

#### 1. Question (문제)
```python
- id: UUID (Primary Key)
- csv_id: CharField (CSV 문제 ID)
- source_id: CharField (출처 파일명)
- title_ko/title_en: CharField (다국어 제목)
- content_ko/content_en: TextField (다국어 문제 내용)
- answer_ko/answer_en: CharField (다국어 정답)
- explanation_ko/explanation_en: TextField (다국어 설명)
- difficulty: CharField (난이도: Easy/Medium/Hard)
- url: URLField (문제 URL)
- group_id: CharField (그룹 ID)
- created_language: CharField (생성 언어)
- is_ko_complete/is_en_complete: BooleanField (언어별 완성도)
- created_by: ForeignKey (생성자)
- created_at/updated_at: DateTimeField
```

#### 2. Exam (시험)
```python
- id: UUID (Primary Key)
- title_ko/title_en: CharField (다국어 제목)
- description_ko/description_en: TextField (다국어 설명)
- total_questions: IntegerField (총 문제 수)
- questions: ManyToManyField (Question, through ExamQuestion)
- is_public: BooleanField (공개 여부)
- force_answer: BooleanField (답안 입력 강제)
- voice_mode_enabled: BooleanField (음성 모드 지원)
- ai_mock_interview: BooleanField (AI 모의 인터뷰)
- original_exam: ForeignKey (원본 시험, 버전 관리)
- version_number: IntegerField (버전 번호)
- is_original: BooleanField (원본 여부)
- file_name: CharField (연결된 파일)
- created_by: ForeignKey (생성자)
- created_language: CharField (생성 언어)
- is_ko_complete/is_en_complete: BooleanField (언어별 완성도)
- created_at: DateTimeField
```

#### 3. Study (스터디)
```python
- id: AutoField (Primary Key)
- title_ko/title_en: CharField (다국어 제목)
- goal_ko/goal_en: TextField (다국어 목표)
- start_date/end_date: DateField (시작/종료일)
- is_public: BooleanField (공개 여부)
- created_by: ForeignKey (생성자)
- created_language: CharField (생성 언어)
- is_ko_complete/is_en_complete: BooleanField (언어별 완성도)
- created_at/updated_at: DateTimeField
```

#### 4. StudyTask (학습 태스크)
```python
- id: AutoField (Primary Key)
- study: ForeignKey (Study)
- name_ko/name_en: CharField (다국어 Task 이름)
- exam: ForeignKey (Exam, 연결된 시험)
- progress: FloatField (진행률 0-100%)
- seq: IntegerField (순서)
- is_public: BooleanField (공개 여부)
- created_language: CharField (생성 언어)
- is_ko_complete/is_en_complete: BooleanField (언어별 완성도)
```

#### 5. Member (멤버)
```python
- id: AutoField (Primary Key)
- study: ForeignKey (Study)
- user: ForeignKey (User, 가입된 사용자)
- name: CharField (이름)
- email: EmailField (이메일)
- member_id: CharField (사용자 정의 ID)
- affiliation: CharField (소속)
- location: CharField (위치)
- role: CharField (역할: member/study_admin/study_leader)
- is_active: BooleanField (활성화 상태)
- created_at/updated_at: DateTimeField
```

#### 6. ExamResult (시험 결과)
```python
- id: UUID (Primary Key)
- exam: ForeignKey (Exam)
- user: ForeignKey (User)
- score: IntegerField (점수)
- total_score: IntegerField (총점)
- correct_count: IntegerField (정답 수)
- wrong_count: IntegerField (오답 수)
- completed_at: DateTimeField (완료일)
- elapsed_seconds: IntegerField (소요 시간)
```

#### 7. ExamResultDetail (시험 결과 상세)
```python
- id: AutoField (Primary Key)
- result: ForeignKey (ExamResult)
- question: ForeignKey (Question)
- question_title: CharField (문제 제목, 보존용)
- question_content: TextField (문제 내용, 보존용)
- question_answer: CharField (문제 정답, 보존용)
- question_difficulty: CharField (문제 난이도, 보존용)
- user_answer: CharField (사용자 답안)
- is_correct: BooleanField (정답 여부)
- elapsed_seconds: IntegerField (문제별 소요 시간)
```

#### 8. UserProfile (사용자 프로필)
```python
- id: AutoField (Primary Key)
- user: OneToOneField (User)
- role: CharField (역할: admin_role/study_admin_role/user_role)
- random_exam_email_enabled: BooleanField (랜덤출제 이메일 발송 여부)
- random_exam_question_count: IntegerField (랜덤출제 시험당 문제 수)
- language: CharField (언어 설정: ko/en)
- email_verified: BooleanField (이메일 인증 완료)
- email_verification_token: CharField (이메일 인증 토큰)
- email_verification_sent_at: DateTimeField (이메일 인증 발송일)
- retention_cleanup_enabled: BooleanField (자동 정리 활성화)
- retention_cleanup_percentage: IntegerField (자동 정리 비율)
```

### 관계형 구조
- **Exam ↔ Question**: Many-to-Many (ExamQuestion 중간 테이블)
- **Study ↔ StudyTask**: One-to-Many
- **Study ↔ Member**: One-to-Many
- **StudyTask ↔ Exam**: Many-to-One
- **Exam ↔ ExamResult**: One-to-Many
- **ExamResult ↔ ExamResultDetail**: One-to-Many
- **User ↔ UserProfile**: One-to-One

## 🚀 주요 기능 분석

### 1. 사용자 관리
- **회원가입/로그인**: Django 기본 인증 + Google OAuth
- **프로필 관리**: 다국어 설정, 역할 관리, 이메일 인증
- **사용자 통계**: 개인별 학습 통계, 정확도 조정
- **계정 관리**: 계정 삭제, 비밀번호 변경

### 2. 문제 관리
- **문제 생성**: CSV/Excel 파일 업로드로 대량 문제 등록
- **문제 편집**: 개별 문제 수정, 삭제
- **문제 분류**: 난이도별, 그룹별 분류
- **문제 무시**: 사용자별 문제 무시 기능
- **문제 통계**: 정답률, 시도 횟수 등 통계 정보

### 3. 시험 관리
- **시험 생성**: 문제 선택, 순서 설정, 옵션 구성
- **시험 옵션**:
  - 공개/비공개 설정
  - 답안 입력 강제 모드
  - 음성 모드 지원
  - AI 모의 인터뷰 모드
- **시험 버전 관리**: 원본/복사본 관리, 재시험 지원
- **시험 결과**: 점수, 정답률, 소요시간 기록

### 4. 스터디 관리
- **스터디 생성**: 제목, 목표, 기간 설정
- **멤버 관리**: 멤버 추가/삭제, 역할 설정
- **학습 태스크**: 시험과 연결된 학습 단계 관리
- **진행률 추적**: 개인별/전체 진행률 모니터링
- **가입 요청**: 스터디 가입 요청/승인 시스템

### 5. 다국어 지원
- **자동 번역**: OpenAI API를 통한 자동 번역
- **언어별 완성도**: 한국어/영어 완성도 추적
- **사용자 언어 설정**: 프로필 기반 언어 자동 설정
- **번역 관리**: 수동 번역 수정, 번역 상태 관리

### 6. 고급 기능
- **음성 시험**: WebRTC 기반 음성 녹음/재생
- **AI 모의 인터뷰**: OpenAI API 기반 실시간 인터뷰
- **랜덤 출제**: 사용자별 맞춤 랜덤 문제 출제
- **즐겨찾기**: 개인별 문제 즐겨찾기 관리
- **구독 시스템**: 시험 구독/해제 관리

### 7. 데이터 관리
- **Excel 내보내기/가져오기**: 시험, 문제, 사용자 데이터
- **데이터 백업**: 사용자 통계 백업/복원
- **자동 정리**: 설정된 비율로 성공 기록 자동 삭제
- **캐시 관리**: Redis 기반 성능 최적화

### 8. 관리자 기능
- **사용자 관리**: 사용자 생성/수정/삭제, 역할 변경
- **데이터 관리**: 전체 데이터 내보내기/가져오기
- **통계 대시보드**: 전체 시스템 통계 조회
- **시스템 관리**: 캐시 정리, 데이터 정리

## 🔧 기술적 특징

### 1. 성능 최적화
- **데이터베이스 인덱싱**: 복합 인덱스로 쿼리 성능 최적화
- **캐시 전략**: Redis 기반 다층 캐시 시스템
- **쿼리 최적화**: select_related, prefetch_related 활용
- **페이지네이션**: 대용량 데이터 효율적 처리

### 2. 보안
- **CSRF 보호**: Django CSRF 토큰 기반 보호
- **CORS 설정**: 엄격한 CORS 정책
- **사용자 권한**: 역할 기반 접근 제어
- **데이터 검증**: 입력 데이터 유효성 검사

### 3. 확장성
- **마이크로서비스 준비**: 모듈화된 구조
- **Docker 지원**: 컨테이너화된 배포
- **Kubernetes 배포**: 클라우드 네이티브 아키텍처
- **환경별 설정**: 개발/QA/프로덕션 환경 분리

### 4. 모니터링
- **로깅 시스템**: 구조화된 로그 관리
- **에러 추적**: 상세한 에러 로그
- **성능 모니터링**: 캐시 히트율, 쿼리 성능 추적

## 📁 프로젝트 구조

```
drillquiz/
├── drillquiz/                 # Django 프로젝트 설정
│   ├── settings.py           # 환경별 설정
│   ├── urls.py              # 메인 URL 라우팅
│   └── wsgi.py              # WSGI 설정
├── quiz/                     # 메인 앱
│   ├── models.py            # 데이터 모델
│   ├── views/               # API 뷰
│   │   ├── auth_views.py    # 인증 관련
│   │   ├── exam_views.py    # 시험 관리
│   │   ├── study_views.py   # 스터디 관리
│   │   └── ...
│   ├── serializers.py       # API 직렬화
│   ├── urls.py             # API 라우팅
│   └── utils/              # 유틸리티
├── src/                     # Vue.js 프론트엔드
│   ├── components/         # Vue 컴포넌트
│   ├── views/             # Vue 페이지
│   ├── router/            # Vue 라우터
│   └── utils/             # 프론트엔드 유틸리티
├── ci/                     # CI/CD 설정
│   ├── Jenkinsfile        # Jenkins 파이프라인
│   └── k8s.yaml          # Kubernetes 배포 설정
└── scripts/               # 관리 스크립트
```

## 🚀 배포 환경

### 개발 환경
- **로컬 개발**: SQLite + 로컬 파일 시스템
- **Docker**: PostgreSQL + MinIO + Redis
- **포트**: Django 8000, Vue 8080

### 프로덕션 환경
- **Kubernetes**: 클러스터 환경
- **데이터베이스**: PostgreSQL
- **캐시**: Redis Cluster
- **스토리지**: MinIO
- **도메인**: us.drillquiz.com

## 📊 데이터 흐름

1. **사용자 인증**: Google OAuth → Django 세션
2. **문제 업로드**: CSV/Excel → 파싱 → 데이터베이스 저장
3. **시험 생성**: 문제 선택 → 시험 생성 → 캐시 업데이트
4. **시험 응시**: 문제 로드 → 답안 제출 → 결과 저장
5. **통계 계산**: 결과 집계 → 캐시 업데이트 → 프론트엔드 표시

## 🔄 캐시 전략

### Redis 캐시 키 패턴
- `drillquiz_production:exam:*` - 시험 관련 캐시
- `drillquiz_production:study:*` - 스터디 관련 캐시
- `drillquiz_production:user:*` - 사용자 관련 캐시
- `drillquiz_production:question:*` - 문제 관련 캐시

### 캐시 무효화
- **시험 변경**: ExamCacheManager를 통한 체계적 무효화
- **스터디 변경**: StudyCacheManager를 통한 무효화
- **사용자 변경**: 개별 사용자 캐시 무효화

## 🎯 새로운 버전 개발 시 고려사항

### 1. 아키텍처 개선
- **마이크로서비스 분리**: 인증, 시험, 스터디 서비스 분리
- **API Gateway**: 통합 API 관리
- **이벤트 기반 아키텍처**: 비동기 처리 개선

### 2. 기술 스택 업그레이드
- **Django 5.x**: 최신 Django 버전 적용
- **Vue 3**: Composition API 활용
- **TypeScript**: 타입 안정성 향상
- **GraphQL**: 효율적인 데이터 페칭

### 3. 성능 최적화
- **CDN 도입**: 정적 파일 최적화
- **데이터베이스 샤딩**: 대용량 데이터 처리
- **실시간 기능**: WebSocket 기반 실시간 업데이트

### 4. 보안 강화
- **JWT 토큰**: 세션 기반에서 토큰 기반으로 전환
- **API 버전 관리**: 하위 호환성 보장
- **데이터 암호화**: 민감 데이터 암호화

### 5. 모니터링 개선
- **APM 도입**: Application Performance Monitoring
- **메트릭 수집**: Prometheus + Grafana
- **알림 시스템**: 실시간 에러 알림

이 문서는 DrillQuiz 시스템의 현재 상태를 종합적으로 분석한 것으로, 새로운 버전 개발 시 참조할 수 있는 기술적 가이드입니다.
