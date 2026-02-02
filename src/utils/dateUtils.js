/**
 * 날짜 유틸리티 함수들
 * 모든 날짜는 사용자의 로컬 시간대를 기준으로 처리됩니다.
 */

/**
 * 서버에서 받은 UTC 날짜를 사용자의 로컬 시간대로 변환하여 포맷팅
 * @param {string|Date} dateString - 서버에서 받은 날짜 문자열 또는 Date 객체
 * @param {Object} options - 포맷팅 옵션
 * @returns {string} 포맷팅된 날짜 문자열
 */
export function formatLocalDate(dateString, options = {}) {
  if (!dateString) return ''
  
  const date = new Date(dateString)
  
  // 사용자의 로컬 시간대로 자동 변환
  const localDate = new Date(date.getTime())
  
  const defaultOptions = {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }
  
  return localDate.toLocaleDateString('ko-KR', { ...defaultOptions, ...options })
}

/**
 * 서버에서 받은 UTC 날짜를 사용자의 로컬 시간대로 변환하여 시간 포맷팅
 * @param {string|Date} dateString - 서버에서 받은 날짜 문자열 또는 Date 객체
 * @param {Object} options - 포맷팅 옵션
 * @returns {string} 포맷팅된 시간 문자열
 */
export function formatLocalTime(dateString, options = {}) {
  if (!dateString) return ''
  
  const date = new Date(dateString)
  
  // 사용자의 로컬 시간대로 자동 변환
  const localDate = new Date(date.getTime())
  
  const defaultOptions = {
    hour: '2-digit',
    minute: '2-digit'
  }
  
  return localDate.toLocaleTimeString('ko-KR', { ...defaultOptions, ...options })
}

/**
 * 서버에서 받은 UTC 날짜를 사용자의 로컬 시간대로 변환하여 날짜+시간 포맷팅
 * @param {string|Date} dateString - 서버에서 받은 날짜 문자열 또는 Date 객체
 * @returns {string} 포맷팅된 날짜+시간 문자열
 */
export function formatLocalDateTime(dateString) {
  if (!dateString) return ''
  
  const date = new Date(dateString)
  
  // 사용자의 로컬 시간대로 자동 변환
  const localDate = new Date(date.getTime())
  
  return localDate.toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * 서버에서 받은 UTC 날짜를 사용자의 로컬 시간대로 변환하여 YYYY-MM-DD 형식으로 반환
 * @param {string|Date} dateString - 서버에서 받은 날짜 문자열 또는 Date 객체
 * @returns {string} YYYY-MM-DD 형식의 날짜 문자열
 */
export function formatLocalDateISO(dateString) {
  if (!dateString) return ''
  
  const date = new Date(dateString)
  
  // 사용자의 로컬 시간대로 자동 변환
  const localDate = new Date(date.getTime())
  
  return localDate.toISOString().split('T')[0]
}

/**
 * 두 날짜를 사용자의 로컬 시간대 기준으로 비교
 * @param {string|Date} dateA - 첫 번째 날짜
 * @param {string|Date} dateB - 두 번째 날짜
 * @returns {number} 비교 결과 (-1, 0, 1)
 */
export function compareLocalDates(dateA, dateB) {
  const localDateA = new Date(dateA)
  const localDateB = new Date(dateB)
  
  return localDateA.getTime() - localDateB.getTime()
} 