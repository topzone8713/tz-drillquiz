# DrillQuiz Frontend API 함수 명세서

## 📋 개요

DrillQuiz 프론트엔드에서 사용하는 API 함수들을 Vue.js 컴포넌트별로 정리한 명세서입니다. 이 문서는 프론트엔드 개발 시 API 호출 패턴과 사용법을 참조할 수 있는 가이드입니다.

**기술 스택**: Vue.js 2.6.14, Axios, Vue I18n  
**HTTP 클라이언트**: Axios (기본), $http (Vue 인스턴스)

## 🔧 공통 설정

### Axios 기본 설정
```javascript
// main.js
axios.defaults.baseURL = apiBaseURL
axios.defaults.withCredentials = true  // 쿠키 포함
```

### CSRF 토큰 처리
```javascript
// 모든 요청에 CSRF 토큰 자동 추가
axios.interceptors.request.use(function (config) {
  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value
  if (csrfToken) {
    config.headers['X-CSRFToken'] = csrfToken
  }
  return config
})
```

## 📚 API 함수 카테고리

## 1. 🔐 인증 및 사용자 관리 (Authentication & User Management)

### 1.1 App.vue - 메인 애플리케이션
| 함수명 | HTTP Method | Endpoint | Description | Parameters |
|--------|-------------|----------|-------------|------------|
| `getCsrfToken()` | GET | `/api/csrf-token/` | CSRF 토큰 발급 | - |
| `checkAuthStatus()` | GET | `/api/auth/status/` | 인증 상태 확인 | - |
| `getUserProfile()` | GET | `/api/user-profile/` | 사용자 프로필 조회 | - |
| `changeLanguage()` | POST | `/api/change-language/` | 사용자 언어 변경 | `{ language: string }` |
| `logout()` | POST | `/api/logout/` | 사용자 로그아웃 | - |

### 1.2 Profile.vue - 사용자 프로필 관리
| 함수명 | HTTP Method | Endpoint | Description | Parameters |
|--------|-------------|----------|-------------|------------|
| `getUserProfile()` | GET | `/api/user-profile/get/` | 사용자 프로필 상세 조회 | - |
| `updateProfile()` | PATCH | `/api/user-profile/update/` | 사용자 프로필 수정 | `{ name, email, language, ... }` |
| `updateProfileBasic()` | PATCH | `/api/user-profile/` | 기본 프로필 수정 | `{ name, email }` |
| `manualRetentionCleanup()` | POST | `/api/retention-cleanup/manual/` | 수동 데이터 정리 | - |
| `exportUserData()` | GET | `/api/export-user-data/` | 사용자 데이터 내보내기 | `{ responseType: 'blob' }` |
| `resetUserStatistics()` | POST | `/api/user-statistics/reset/` | 사용자 통계 초기화 | - |
| `changePassword()` | POST | `/api/user/{id}/change-password/` | 비밀번호 변경 | `{ new_password, confirm_password }` |
| `loginAfterPasswordChange()` | POST | `/api/login/` | 비밀번호 변경 후 재로그인 | `{ username, password }` |
| `sendEmailVerification()` | POST | `/api/send-email-verification/` | 이메일 인증 요청 | - |
| `getMyExams()` | GET | `/api/exams/` | 내 시험 목록 조회 | `{ my_exams: true, page_size: 100 }` |
| `getSubscribedExams()` | GET | `/api/user-exams/subscribed-exams/` | 구독한 시험 목록 | - |
| `moveExamsToSubscribed()` | POST | `/api/user-exams/move-to-subscribed/` | 시험을 구독으로 이동 | `{ exam_ids: [] }` |
| `moveExamsToMyExams()` | POST | `/api/user-exams/move-to-my-exams/` | 시험을 내 시험으로 이동 | `{ exam_ids: [] }` |
| `deleteMyAccount()` | DELETE | `/api/delete-my-account/` | 내 계정 삭제 | - |

## 2. 📝 시험 관리 (Exam Management)

### 2.1 TakeExam.vue - 시험 응시
| 함수명 | HTTP Method | Endpoint | Description | Parameters |
|--------|-------------|----------|-------------|------------|
| `loadExam()` | GET | `/api/exam/{examId}/` | 시험 정보 로드 | `{ examId: string }` |
| `getConnectedStudies()` | GET | `/api/exam/{examId}/connected-studies/` | 연결된 스터디 조회 | `{ examId: string }` |
| `createSingleQuestionExam()` | POST | `/api/create-single-question-exam/` | 단일 문제 시험 생성 | `{ question_id, exam_id }` |
| `createExam()` | POST | `/api/create-exam/` | 새 시험 생성 | `{ title, description, questions: [] }` |
| `getExamResult()` | GET | `/api/exam-result/{resultId}/` | 시험 결과 조회 | `{ resultId: string }` |
| `continueExam()` | POST | `/api/exam/{examId}/continue/` | 시험 계속하기 | `{ examId: string }` |
| `submitExam()` | POST | `/api/submit-exam/` | 시험 제출 | `{ exam_id, answers: [] }` |
| `updateQuestion()` | PATCH | `/api/questions/{questionId}/update/` | 문제 수정 | `{ questionId: string, data: {} }` |
| `addQuestionToExam()` | POST | `/api/exam/{examId}/add-question/` | 시험에 문제 추가 | `{ examId: string, question_id }` |
| `deleteQuestion()` | DELETE | `/api/questions/{questionId}/` | 문제 삭제 | `{ questionId: string }` |
| `getQuestionStatistics()` | GET | `/api/exam/{examId}/question-statistics/` | 문제 통계 조회 | `{ examId: string }` |
| `addToFavorite()` | POST | `/api/add-question-to-favorite/` | 즐겨찾기에 추가 | `{ question_id }` |
| `ignoreQuestion()` | POST | `/api/question/{questionId}/ignore/` | 문제 무시 | `{ questionId: string }` |
| `getFavoriteQuestions()` | GET | `/api/favorite-exam-questions/` | 즐겨찾기 문제 목록 | - |
| `getIgnoredQuestions()` | GET | `/api/questions/ignored/` | 무시된 문제 목록 | - |
| `adjustQuestionAccuracy()` | POST | `/api/adjust-question-accuracy/` | 문제 정확도 조정 | `{ question_id, adjustment_percentage }` |

### 2.2 ExamDetail.vue - 시험 상세 관리
| 함수명 | HTTP Method | Endpoint | Description | Parameters |
|--------|-------------|----------|-------------|------------|
| `createRandomRecommendationExam()` | POST | `/api/create-random-recommendation-exam/` | 랜덤 추천 시험 생성 | `{ target_username, title, questions_per_exam, is_public }` |
| `loadExam()` | GET | `/api/exam/{examId}/` | 시험 정보 로드 | `{ examId: string }` |
| `getConnectedStudies()` | GET | `/api/exam/{examId}/connected-studies/` | 연결된 스터디 조회 | `{ examId: string }` |
| `getFavoriteQuestions()` | GET | `/api/favorite-exam-questions/` | 즐겨찾기 문제 목록 | - |
| `getExamQuestions()` | GET | `/api/exam/{examId}/questions/` | 시험 문제 목록 | `{ examId: string }` |
| `createExam()` | POST | `/api/create-exam/` | 새 시험 생성 | `{ title, description, questions: [] }` |
| `getStudies()` | GET | `/api/studies/` | 스터디 목록 조회 | - |
| `getStudyMembers()` | GET | `/api/studies/{studyId}/members/` | 스터디 멤버 목록 | `{ studyId: number }` |
| `createQuestionMemberMapping()` | POST | `/api/create-question-member-mapping/` | 문제-멤버 매핑 생성 | `{ question_id, member_id, exam_id }` |
| `getQuestionMemberMappings()` | GET | `/api/exam/{examId}/question-member-mappings/` | 문제-멤버 매핑 조회 | `{ examId: string }` |
| `getExamResults()` | GET | `/api/exam-results/` | 시험 결과 조회 | `{ exam_id, latest: true }` |
| `getQuestionStatistics()` | GET | `/api/exam/{examId}/question-statistics/` | 문제 통계 조회 | `{ examId: string }` |
| `updateExam()` | PATCH | `/api/exam/{examId}/update/` | 시험 수정 | `{ examId: string, data: {} }` |
| `importFromConnectedFile()` | POST | `/api/exam/{examId}/import-from-connected-file/` | 연결된 파일에서 문제 가져오기 | `{ examId: string }` |
| `deleteQuestionResultsGlobal()` | DELETE | `/api/delete-question-results-global/` | 전체 문제 결과 삭제 | - |
| `deleteQuestionResults()` | DELETE | `/api/delete-question-results/` | 문제 결과 삭제 | `{ question_ids: [] }` |
| `deleteExam()` | DELETE | `/api/exam/{examId}/` | 시험 삭제 | `{ examId: string }` |
| `deleteQuestions()` | POST | `/api/delete-questions/` | 문제 일괄 삭제 | `{ question_ids: [] }` |
| `moveQuestions()` | POST | `/api/move-questions/` | 문제 이동 | `{ question_ids: [], target_exam_id }` |
| `copyQuestions()` | POST | `/api/copy-questions/` | 문제 복사 | `{ question_ids: [], target_exam_id }` |
| `bulkUpdateQuestionGroup()` | PATCH | `/api/questions/bulk-update-group/` | 문제 그룹 일괄 업데이트 | `{ question_ids: [], group_id }` |
| `addToFavorite()` | POST | `/api/add-question-to-favorite/` | 즐겨찾기에 추가 | `{ question_id }` |
| `ignoreQuestion()` | POST | `/api/question/{questionId}/ignore/` | 문제 무시 | `{ questionId: string }` |
| `unignoreQuestion()` | POST | `/api/question/{questionId}/unignore/` | 문제 무시 해제 | `{ questionId: string }` |
| `updateQuestionsFromExcel()` | POST | `/api/exam/{examId}/update-questions-from-excel/` | Excel에서 문제 업데이트 | `{ examId: string, file: FormData }` |
| `bulkAdjustUserAccuracy()` | POST | `/api/bulk-adjust-user-accuracy/` | 사용자 정확도 일괄 조정 | `{ user_id, adjustment_percentage }` |

### 2.3 ExamManagement.vue - 시험 관리
| 함수명 | HTTP Method | Endpoint | Description | Parameters |
|--------|-------------|----------|-------------|------------|
| `createRandomRecommendationExams()` | POST | `/api/create-random-recommendation-exam/` | 랜덤 추천 시험 생성 | `{ target_username, title, questions_per_exam, is_public }` |

## 3. 📚 스터디 관리 (Study Management)

### 3.1 StudyManagement.vue - 스터디 관리
| 함수명 | HTTP Method | Endpoint | Description | Parameters |
|--------|-------------|----------|-------------|------------|
| `loadStudies()` | GET | `/api/studies/` | 스터디 목록 조회 | `{ is_public, my_studies, select }` |
| `createStudy()` | POST | `/api/studies/` | 스터디 생성 | `{ title_ko, title_en, goal_ko, goal_en, start_date, end_date, is_public }` |
| `updateStudy()` | PUT | `/api/studies/{id}/` | 스터디 수정 | `{ id: number, data: {} }` |
| `deleteStudy()` | DELETE | `/api/studies/{id}/` | 스터디 삭제 | `{ id: number }` |
| `recordProgress()` | POST | `/api/record-study-progress/` | 스터디 진행률 기록 | `{ study_id, overall_progress, task_progresses, page_type }` |

### 3.2 StudyDetail.vue - 스터디 상세
| 함수명 | HTTP Method | Endpoint | Description | Parameters |
|--------|-------------|----------|-------------|------------|
| `loadStudy()` | GET | `/api/studies/{id}/` | 스터디 상세 조회 | `{ id: number }` |
| `loadStudyTasks()` | GET | `/api/study-tasks/` | 스터디 태스크 목록 | `{ study: studyId }` |
| `createStudyTask()` | POST | `/api/study-tasks/` | 스터디 태스크 생성 | `{ study, name_ko, name_en, exam, seq, is_public }` |
| `updateStudyTask()` | PUT | `/api/study-tasks/{id}/` | 스터디 태스크 수정 | `{ id: number, data: {} }` |
| `deleteStudyTask()` | DELETE | `/api/study-tasks/{id}/` | 스터디 태스크 삭제 | `{ id: number }` |
| `loadMembers()` | GET | `/api/members/` | 멤버 목록 조회 | `{ study: studyId }` |
| `createMember()` | POST | `/api/members/` | 멤버 추가 | `{ study, name, email, member_id, affiliation, location, role }` |
| `updateMember()` | PUT | `/api/members/{id}/` | 멤버 정보 수정 | `{ id: number, data: {} }` |
| `deleteMember()` | DELETE | `/api/members/{id}/` | 멤버 삭제 | `{ id: number }` |

## 4. 🎤 실시간 기능 (Realtime Features)

### 4.1 VoiceExamInterface.vue - 음성 시험 인터페이스
| 함수명 | HTTP Method | Endpoint | Description | Parameters |
|--------|-------------|----------|-------------|------------|
| `createRealtimeSession()` | POST | `/api/realtime/session/` | 실시간 세션 생성 | `{ exam_id, user_id }` |
| `handleWebRTCOffer()` | POST | `/api/realtime/session/{sessionId}/offer/` | WebRTC Offer 처리 | `{ sessionId: string, offer: RTCSessionDescription }` |
| `handleIceCandidate()` | POST | `/api/realtime/session/{sessionId}/ice-candidate/` | ICE Candidate 처리 | `{ sessionId: string, candidate: RTCIceCandidate }` |
| `getUserProfile()` | GET | `/api/user-profile/` | 사용자 프로필 조회 | - |
| `evaluateAnswer()` | POST | `/api/evaluate-answer/` | AI 답변 평가 | `{ question, answer, session_id }` |
| `requestSpeech()` | POST | `/api/realtime/session/{sessionId}/speak/` | 음성 녹음 시작 | `{ sessionId: string, speechRequest: {} }` |
| `stopSpeech()` | POST | `/api/realtime/session/{sessionId}/stop-speak/` | 음성 녹음 중지 | `{ sessionId: string }` |
| `deleteRealtimeSession()` | DELETE | `/api/realtime/session/{sessionId}/delete/` | 실시간 세션 삭제 | `{ sessionId: string }` |

## 5. 🌐 다국어 지원 (Multilingual Support)

### 5.1 다국어 유틸리티 함수 (multilingualUtils.js)
| 함수명 | Description | Parameters | Return Type |
|--------|-------------|------------|-------------|
| `getCurrentLanguage(i18n)` | 현재 사용자 언어 조회 | `i18n: Object` | `string` |
| `getLocalizedContent(item, fieldName, currentLanguage, fallbackValue)` | 다국어 필드에서 현재 언어에 맞는 값 추출 | `item: Object, fieldName: string, currentLanguage: string, fallbackValue: string` | `string` |
| `getAvailableLanguages(item, fieldName)` | 사용 가능한 언어 목록 생성 | `item: Object, fieldName: string` | `Array<string>` |
| `validateMultilingualFields(item, fieldName)` | 다국어 필드 유효성 검사 | `item: Object, fieldName: string` | `boolean` |
| `getMultilingualCompletion(item, fieldName)` | 언어별 완성도 상태 확인 | `item: Object, fieldName: string` | `Object` |
| `getMultilingualMetadata(item, fieldName, currentLanguage)` | 다국어 콘텐츠 메타데이터 생성 | `item: Object, fieldName: string, currentLanguage: string` | `Object` |
| `createMultilingualEditData(item, fieldName, currentLanguage)` | 다국어 필드 편집용 초기 데이터 생성 | `item: Object, fieldName: string, currentLanguage: string` | `Object` |
| `detectMultilingualChanges(original, updated, fieldName)` | 다국어 필드 변경 사항 감지 | `original: Object, updated: Object, fieldName: string` | `boolean` |
| `getMultilingualSummary(item, fieldNames, currentLanguage)` | 다국어 필드 요약 정보 생성 | `item: Object, fieldNames: Array<string>, currentLanguage: string` | `Object` |

## 6. 💾 캐시 관리 (Cache Management)

### 6.1 캐시 유틸리티 함수 (cacheUtils.js)
| 함수명 | Description | Parameters | Return Type |
|--------|-------------|------------|-------------|
| `isCacheEnabled()` | 캐시 활성화 여부 확인 | - | `boolean` |
| `withCache(callback, defaultValue)` | 캐시 활성화 시에만 콜백 실행 | `callback: Function, defaultValue: any` | `any` |
| `setSessionCache(key, value)` | sessionStorage에 저장 | `key: string, value: any` | `boolean` |
| `getSessionCache(key, defaultValue)` | sessionStorage에서 조회 | `key: string, defaultValue: any` | `any` |
| `removeSessionCache(key)` | sessionStorage에서 삭제 | `key: string` | `boolean` |
| `setLocalCache(key, value)` | localStorage에 저장 | `key: string, value: any` | `boolean` |
| `getLocalCache(key, defaultValue)` | localStorage에서 조회 | `key: string, defaultValue: any` | `any` |
| `removeLocalCache(key)` | localStorage에서 삭제 | `key: string` | `boolean` |
| `removeCacheByPattern(pattern, storage)` | 패턴에 맞는 키들 삭제 | `pattern: string|RegExp, storage: Storage` | `number` |
| `clearAllCache(storage)` | 모든 캐시 클리어 | `storage: Storage` | `boolean` |
| `invalidateStudyCache()` | 스터디 관련 캐시 무효화 | - | `void` |
| `invalidateStudySpecificCache(studyId)` | 특정 스터디 캐시 무효화 | `studyId: number|string` | `void` |
| `invalidateAllCache()` | 모든 관련 캐시 무효화 | - | `void` |
| `handleBackendCacheInvalidation(cacheInvalidation)` | 백엔드 캐시 무효화 신호 처리 | `cacheInvalidation: Object` | `void` |
| `triggerPageRefresh(forceReload)` | 페이지 새로고침 트리거 | `forceReload: boolean` | `void` |
| `refreshComponentData(component, methodName)` | Vue 컴포넌트 데이터 새로고침 | `component: Object, methodName: string` | `void` |

## 7. 🎯 고급 기능 (Advanced Features)

### 7.1 시험 유틸리티 함수 (examUtils.js)
| 함수명 | Description | Parameters | Return Type |
|--------|-------------|------------|-------------|
| `createDailyExam(context, onSuccess)` | Daily Exam 생성 확인 모달 표시 및 실행 | `context: Object, onSuccess: Function` | `Promise<void>` |
| `executeCreateDailyExam(context, onSuccess)` | Daily Exam 생성 실제 실행 | `context: Object, onSuccess: Function` | `Promise<void>` |

## 📊 공통 패턴 및 사용법

### 1. API 호출 패턴
```javascript
// 기본 패턴
async function apiCall() {
  try {
    const response = await axios.get('/api/endpoint/')
    if (response.data.success) {
      // 성공 처리
      return response.data
    } else {
      // 에러 처리
      throw new Error(response.data.error)
    }
  } catch (error) {
    console.error('API 호출 실패:', error)
    throw error
  }
}
```

### 2. 다국어 처리 패턴
```javascript
// 다국어 필드 처리
import { getLocalizedContent, getCurrentLanguage } from '@/utils/multilingualUtils'

const title = getLocalizedContent(study, 'title', getCurrentLanguage(this.$i18n))
```

### 3. 캐시 처리 패턴
```javascript
// 캐시를 고려한 데이터 로딩
import { getSessionCache, setSessionCache } from '@/utils/cacheUtils'

const cachedData = getSessionCache('key')
if (cachedData) {
  return cachedData
}

const data = await apiCall()
setSessionCache('key', data)
return data
```

### 4. 에러 처리 패턴
```javascript
// 통일된 에러 처리
try {
  const response = await axios.post('/api/endpoint/', data)
  this.showToastNotification('성공했습니다.', 'success')
} catch (error) {
  const errorMessage = error.response?.data?.error || '오류가 발생했습니다.'
  this.showToastNotification(errorMessage, 'error')
}
```

## 🔧 설정 및 초기화

### 1. Axios 인터셉터 설정
```javascript
// 요청 인터셉터
axios.interceptors.request.use(function (config) {
  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value
  if (csrfToken) {
    config.headers['X-CSRFToken'] = csrfToken
  }
  return config
})

// 응답 인터셉터
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // 인증 오류 처리
      this.$router.push('/login')
    }
    return Promise.reject(error)
  }
)
```

### 2. CSRF 토큰 초기화
```javascript
// 앱 시작 시 CSRF 토큰 발급
async function initializeApp() {
  try {
    await axios.get('/api/csrf-token/')
    console.log('CSRF 토큰 발급 완료')
  } catch (error) {
    console.error('CSRF 토큰 발급 실패:', error)
  }
}
```

## 🚀 새로운 버전 개발 시 고려사항

### 1. API 클라이언트 개선
- **Vue 3 Composition API**: setup() 함수에서 API 호출 관리
- **TypeScript**: API 응답 타입 정의 및 타입 안정성 향상
- **Pinia**: 상태 관리 라이브러리로 API 상태 중앙화

### 2. 에러 처리 개선
- **전역 에러 핸들러**: 중앙화된 에러 처리 시스템
- **재시도 로직**: 네트워크 오류 시 자동 재시도
- **오프라인 지원**: 서비스 워커를 통한 오프라인 기능

### 3. 성능 최적화
- **요청 취소**: AbortController를 통한 불필요한 요청 취소
- **요청 디바운싱**: 중복 요청 방지
- **응답 캐싱**: HTTP 캐시 헤더 활용

### 4. 개발자 경험 개선
- **API 문서 자동 생성**: OpenAPI 스펙 기반 문서 생성
- **모킹 시스템**: 개발 환경에서 API 모킹
- **테스트 유틸리티**: API 테스트를 위한 헬퍼 함수

이 프론트엔드 API 명세서는 DrillQuiz의 현재 프론트엔드 구조를 종합적으로 정리한 것으로, 새로운 버전 개발 시 참조할 수 있는 기술적 가이드입니다.
