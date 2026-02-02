import axios from 'axios'
import { debugLog } from '@/utils/debugUtils'
import authService from '@/services/authService'
import { examAPI } from '@/services/api'

/**
 * 연령 등급에 따른 기본 시험 난이도를 반환합니다.
 * 
 * @param {string} ageRating - 연령 등급 ('4+', '9+', '12+', '17+')
 * @returns {number} 기본 시험 난이도 (1~10)
 */
export function getDefaultDifficultyByAgeRating(ageRating) {
  if (!ageRating) {
    return 5 // 기본값
  }
  
  switch (ageRating) {
    case '4+':
      return 3 // 낮은 난이도
    case '9+':
      return 4 // 낮은 난이도
    case '12+':
      return 5 // 중간 난이도
    case '17+':
      return 7 // 높은 난이도
    default:
      return 5 // 기본값
  }
}

/**
 * Daily Exam 생성 기능을 공유하는 유틸리티 함수들
 */

/**
 * Daily Exam 생성 확인 모달을 표시하고 실행합니다.
 * @param {Object} context - Vue 컴포넌트 컨텍스트 (this)
 * @param {Function} onSuccess - 성공 시 콜백 함수
 */
export async function createDailyExam(context, onSuccess = null) {
  context.showConfirmModal(
    context.$t('examManagement.messages.randomExamConfirm'),
    context.$t('examManagement.messages.randomExamConfirm'),
    'Confirm',
    'Cancel',
    'btn-success',
    'fas fa-random',
    () => executeCreateDailyExam(context, onSuccess)
  )
}

/**
 * Daily Exam 생성을 실제로 실행합니다.
 * @param {Object} context - Vue 컴포넌트 컨텍스트 (this)
 * @param {Function} onSuccess - 성공 시 콜백 함수
 */
async function executeCreateDailyExam(context, onSuccess = null) {
  try {
    // 현재 사용자 정보 가져오기
    const user = authService.getUserSync()
    if (!user) {
      context.showToastNotification('로그인이 필요합니다.', 'error')
      return
    }

    // 사용자 프로필 강제 새로고침을 위한 타임스탬프 추가
    const timestamp = Date.now()
    
    // create_random_recommendation_exam API 호출
    const response = await axios.post('/api/create-random-recommendation-exam/', {
      target_username: user.username, // 현재 사용자를 대상으로 설정
      title: '', // 자동 생성되도록 빈 문자열
      questions_per_exam: null, // 사용자 프로필에서 가져오도록 null
      is_public: false, // 비공개로 설정
      _t: timestamp // 캐시 무효화를 위한 타임스탬프
    })

    if (response.data.success) {
      const examData = response.data.exam
      
      // 성공 메시지 표시
      context.showToastNotification(context.$t('examManagement.messages.randomExamSuccess'), 'success')
      
      // 캐시 강제 새로고침 플래그 설정
      sessionStorage.setItem('forceRefreshExamManagement', 'true')
      sessionStorage.setItem('forceRefreshProfile', 'true')
      
      // 성공 콜백이 있으면 실행
      if (onSuccess) {
        onSuccess(examData)
      } else {
        // 기본 동작: 생성된 시험으로 바로 이동
        context.$router.push(`/take-exam/${examData.id}?returnTo=exam-management`)
      }
    } else {
      context.showToastNotification('Daily Exam 생성에 실패했습니다.', 'error')
    }

  } catch (error) {
    debugLog('Daily Exam 생성 실패:', error, 'error')
    if (error.response && error.response.data && error.response.data.error) {
      const errorKey = error.response.data.error
      let errorMessage = 'Daily Exam 생성에 실패했습니다.'
      
      // 번역 키에 따른 오류 메시지 처리
      if (errorKey === 'home.dailyExam.noSubscribedExams') {
        errorMessage = context.$t('home.dailyExam.noSubscribedExams')
      } else if (errorKey === 'home.dailyExam.noQuestionsInSubscribedExams') {
        errorMessage = context.$t('home.dailyExam.noQuestionsInSubscribedExams')
      } else if (errorKey === 'home.dailyExam.noAccessibleExams') {
        errorMessage = context.$t('home.dailyExam.noAccessibleExams')
      } else if (errorKey === 'home.dailyExam.noQuestionsAvailable') {
        errorMessage = context.$t('home.dailyExam.noQuestionsAvailable')
      } else if (errorKey.startsWith('home.dailyExam.')) {
        // 번역 키가 있으면 번역된 메시지 사용
        errorMessage = context.$t(errorKey)
      } else {
        // 일반 오류 메시지
        errorMessage = `Daily Exam 생성 실패: ${errorKey}`
      }
      
      context.showToastNotification(errorMessage, 'error')
    } else {
      context.showToastNotification(context.$t('examManagement.messages.randomExamFailed'), 'error')
    }
  }
}

/**
 * 시험 제목 중복 체크 (API 호출)
 * @param {string} title - 체크할 시험 제목
 * @param {boolean} checkMyExamsOnly - 내 시험만 체크할지 여부 (기본값: true)
 * @returns {Promise<boolean>} 중복이면 true, 아니면 false
 */
export async function checkTitleDuplicate(title, checkMyExamsOnly = true) {
  if (!title || !title.trim()) {
    return false
  }
  
  try {
    const params = {
      search_title: title.trim(),
      page_size: 1
    }
    
    if (checkMyExamsOnly) {
      params.my_exams = true
    }
    
    const response = await examAPI.getExams(params)
    
    if (response.data && response.data.results && response.data.results.length > 0) {
      // 정확히 일치하는지 확인 (대소문자 구분 없이)
      const existingExam = response.data.results[0]
      const existingTitle = existingExam.display_title || existingExam.title_ko || existingExam.title_en || ''
      return existingTitle.toLowerCase() === title.trim().toLowerCase()
    }
    
    return false
  } catch (error) {
    debugLog('시험 제목 중복 체크 오류:', error, 'error')
    // 오류 발생 시 중복이 아니라고 가정 (네트워크 오류 등)
    return false
  }
}

/**
 * 고유한 시험 제목 자동 생성
 * @param {string} baseTitle - 기본 제목
 * @param {boolean} checkMyExamsOnly - 내 시험만 체크할지 여부 (기본값: true)
 * @returns {Promise<string>} 고유한 제목
 */
export async function generateUniqueTitle(baseTitle, checkMyExamsOnly = true) {
  if (!baseTitle || !baseTitle.trim()) {
    return ''
  }
  
  let candidateTitle = baseTitle.trim()
  let attempt = 0
  const maxAttempts = 100 // 최대 100번 시도
  
  while (attempt < maxAttempts) {
    // 중복 체크
    const isDuplicate = await checkTitleDuplicate(candidateTitle, checkMyExamsOnly)
    
    if (!isDuplicate) {
      // 중복이 아니면 사용
      return candidateTitle
    }
    
    // 중복이면 번호를 추가하여 다시 시도
    attempt++
    candidateTitle = `${baseTitle.trim()} (${attempt})`
  }
  
  // 최대 시도 횟수 초과 시 타임스탬프 추가
  const timestamp = new Date().getTime()
  return `${baseTitle.trim()} (${timestamp})`
}
