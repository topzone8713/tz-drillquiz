import { debugLog } from './debugUtils.js'

/**
 * 캐시 설정 및 제어 유틸리티
 * 
 * Profile.vue의 기존 캐시 설정을 활용하여 모든 캐시 영역의 동작을 제어합니다.
 * - localStorage의 'cacheEnabled' 설정을 확인 (Profile.vue에서 설정)
 * - sessionStorage의 'cacheDisabled' 플래그를 확인 (Profile.vue에서 설정)
 * - 캐시가 비활성화된 경우 모든 캐시 작업을 건너뜀
 */

/**
 * Profile.vue의 캐시 설정을 확인하여 캐시가 활성화되어 있는지 확인
 * @returns {boolean} 캐시 활성화 여부
 */
export function isCacheEnabled() {
  try {
    // Profile.vue에서 설정한 localStorage의 캐시 설정 확인
    const cacheEnabled = localStorage.getItem('cacheEnabled')
    
    // Profile.vue에서 설정한 sessionStorage의 캐시 비활성화 플래그 확인
    const cacheDisabled = sessionStorage.getItem('cacheDisabled')
    
    // 캐시가 명시적으로 비활성화되었거나, 비활성화 플래그가 설정된 경우
    if (cacheEnabled === 'false' || cacheDisabled === 'true') {
      return false
    }
    
    // 기본값은 활성화 (설정이 없는 경우)
    return cacheEnabled !== 'false'
  } catch (error) {
    debugLog('캐시 설정 확인 중 오류:', error, 'error')
    // 오류 발생 시 기본적으로 캐시 활성화
    return true
  }
}

/**
 * 캐시가 활성화된 경우에만 콜백 함수 실행
 * @param {Function} callback - 캐시가 활성화된 경우 실행할 함수
 * @param {*} defaultValue - 캐시가 비활성화된 경우 반환할 기본값
 * @returns {*} 콜백 함수의 결과 또는 기본값
 */
export function withCache(callback, defaultValue = null) {
  if (isCacheEnabled()) {
    try {
      return callback()
    } catch (error) {
      debugLog('캐시 작업 중 오류:', error, 'error')
      return defaultValue
    }
  }
  return defaultValue
}

/**
 * Profile.vue의 캐시 설정에 따라 sessionStorage에 저장
 * @param {string} key - 저장할 키
 * @param {*} value - 저장할 값
 * @returns {boolean} 저장 성공 여부
 */
export function setSessionCache(key, value) {
  return withCache(() => {
    sessionStorage.setItem(key, JSON.stringify(value))
    return true
  }, false)
}

/**
 * Profile.vue의 캐시 설정에 따라 sessionStorage에서 조회
 * @param {string} key - 조회할 키
 * @param {*} defaultValue - 캐시가 비활성화되거나 실패 시 반환할 기본값
 * @returns {*} 저장된 값 또는 기본값
 */
export function getSessionCache(key, defaultValue = null) {
  return withCache(() => {
    const cached = sessionStorage.getItem(key)
    return cached ? JSON.parse(cached) : defaultValue
  }, defaultValue)
}

/**
 * Profile.vue의 캐시 설정에 따라 sessionStorage에서 삭제
 * @param {string} key - 삭제할 키
 * @returns {boolean} 삭제 성공 여부
 */
export function removeSessionCache(key) {
  return withCache(() => {
    sessionStorage.removeItem(key)
    return true
  }, false)
}

/**
 * Profile.vue의 캐시 설정에 따라 localStorage에 저장
 * @param {string} key - 저장할 키
 * @param {*} value - 저장할 값
 * @returns {boolean} 저장 성공 여부
 */
export function setLocalCache(key, value) {
  return withCache(() => {
    localStorage.setItem(key, JSON.stringify(value))
    return true
  }, false)
}

/**
 * Profile.vue의 캐시 설정에 따라 localStorage에서 조회
 * @param {string} key - 조회할 키
 * @param {*} defaultValue - 캐시가 비활성화되거나 실패 시 반환할 기본값
 * @returns {*} 저장된 값 또는 기본값
 */
export function getLocalCache(key, defaultValue = null) {
  return withCache(() => {
    const cached = localStorage.getItem(key)
    return cached ? JSON.parse(cached) : defaultValue
  }, defaultValue)
}

/**
 * Profile.vue의 캐시 설정에 따라 localStorage에서 삭제
 * @param {string} key - 삭제할 키
 * @returns {boolean} 삭제 성공 여부
 */
export function removeLocalCache(key) {
  return withCache(() => {
    localStorage.removeItem(key)
    return true
  }, false)
}

/**
 * Profile.vue의 캐시 설정에 따라 패턴에 맞는 키들을 삭제
 * @param {string} pattern - 삭제할 키 패턴 (정규식 또는 문자열)
 * @param {Storage} storage - 대상 스토리지 (sessionStorage 또는 localStorage)
 * @returns {number} 삭제된 키의 개수
 */
export function removeCacheByPattern(pattern, storage = sessionStorage) {
  return withCache(() => {
    let deletedCount = 0
    const keys = Object.keys(storage)
    
    keys.forEach(key => {
      if (typeof pattern === 'string') {
        if (key.includes(pattern)) {
          storage.removeItem(key)
          deletedCount++
        }
      } else if (pattern.test(key)) {
        storage.removeItem(key)
        deletedCount++
      }
    })
    
    return deletedCount
  }, 0)
}

/**
 * Profile.vue의 캐시 설정에 따라 모든 캐시 클리어
 * @param {Storage} storage - 대상 스토리지 (sessionStorage 또는 localStorage)
 * @returns {boolean} 클리어 성공 여부
 */
export function clearAllCache(storage = sessionStorage) {
  return withCache(() => {
    storage.clear()
    return true
  }, false)
}

/**
 * Profile.vue의 캐시 설정 상태를 콘솔에 출력 (디버깅용)
 */
export function logCacheStatus() {
  const enabled = isCacheEnabled()
  debugLog(`🔍 Profile.vue 캐시 설정 상태: ${enabled ? '활성화' : '비활성화'}`)
  
  if (enabled) {
    debugLog('📊 sessionStorage 항목 수:', sessionStorage.length)
    debugLog('📊 localStorage 항목 수:', localStorage.length)
  }
  
  return enabled
}

/**
 * Profile.vue의 캐시 설정을 확인하는 헬퍼 함수
 * @returns {Object} 캐시 설정 정보
 */
export function getCacheSettings() {
  return {
    enabled: isCacheEnabled(),
    localStorageSetting: localStorage.getItem('cacheEnabled'),
    sessionStorageFlag: sessionStorage.getItem('cacheDisabled')
  }
}

/**
 * 프론트엔드 캐시 관리 유틸리티
 */

/**
 * 로컬 스토리지에서 특정 키의 데이터를 삭제합니다.
 * @param {string} key - 삭제할 키
 */
export function clearLocalStorageItem(key) {
  try {
    localStorage.removeItem(key)
    debugLog(`캐시 무효화: ${key} 삭제됨`)
  } catch (e) {
    debugLog(`캐시 무효화 실패 (${key}):`, e, 'error')
  }
}

/**
 * 세션 스토리지에서 특정 키의 데이터를 삭제합니다.
 * @param {string} key - 삭제할 키
 */
export function clearSessionStorageItem(key) {
  try {
    sessionStorage.removeItem(key)
    debugLog(`세션 캐시 무효화: ${key} 삭제됨`)
  } catch (e) {
    debugLog(`세션 캐시 무효화 실패 (${key}):`, e, 'error')
  }
}

/**
 * 스터디 관련 캐시를 무효화합니다.
 */
export function invalidateStudyCache() {
  debugLog('스터디 캐시 무효화 시작')
  
  // 스터디 목록 관련 캐시
  clearLocalStorageItem('studies')
  clearLocalStorageItem('study_list')
  clearLocalStorageItem('study_cache')
  
  // 스터디 진행률 관련 캐시
  clearLocalStorageItem('study_progress')
  clearLocalStorageItem('study_progress_cache')
  
  // 시험 결과 관련 캐시
  clearLocalStorageItem('exam_results')
  clearLocalStorageItem('exam_results_cache')
  
  debugLog('스터디 캐시 무효화 완료')
}

/**
 * 특정 스터디의 캐시를 무효화합니다.
 * @param {number|string} studyId - 스터디 ID
 */
export function invalidateStudySpecificCache(studyId) {
  debugLog(`스터디 ${studyId} 캐시 무효화 시작`)
  
  // 특정 스터디 관련 캐시
  clearLocalStorageItem(`study_${studyId}`)
  clearLocalStorageItem(`study_${studyId}_progress`)
  clearLocalStorageItem(`study_${studyId}_tasks`)
  clearLocalStorageItem(`study_${studyId}_members`)
  
  debugLog(`스터디 ${studyId} 캐시 무효화 완료`)
}

/**
 * 모든 관련 캐시를 무효화합니다.
 */
export function invalidateAllCache() {
  debugLog('전체 캐시 무효화 시작')
  
  // 로컬 스토리지 전체 삭제
  try {
    localStorage.clear()
    debugLog('로컬 스토리지 전체 삭제 완료')
  } catch (e) {
    debugLog('로컬 스토리지 삭제 실패:', e, 'error')
  }
  
  // 세션 스토리지 전체 삭제
  try {
    sessionStorage.clear()
    debugLog('세션 스토리지 전체 삭제 완료')
  } catch (e) {
    debugLog('세션 스토리지 삭제 실패:', e, 'error')
  }
  
  debugLog('전체 캐시 무효화 완료')
}

/**
 * 백엔드에서 받은 캐시 무효화 신호를 처리합니다.
 * @param {Object} cacheInvalidation - 백엔드에서 받은 캐시 무효화 정보
 */
export function handleBackendCacheInvalidation(cacheInvalidation) {
  if (!cacheInvalidation) return
  
  debugLog('백엔드 캐시 무효화 신호 처리:', cacheInvalidation)
  
  if (cacheInvalidation.studies) {
    invalidateStudyCache()
  }
  
  if (cacheInvalidation.study_progress) {
    clearLocalStorageItem('study_progress')
    clearLocalStorageItem('study_progress_cache')
  }
  
  if (cacheInvalidation.exam_results) {
    clearLocalStorageItem('exam_results')
    clearLocalStorageItem('exam_results_cache')
  }
  
  // 타임스탬프 저장 (마지막 캐시 무효화 시간)
  if (cacheInvalidation.timestamp) {
    localStorage.setItem('last_cache_invalidation', cacheInvalidation.timestamp)
  }
  
  debugLog('백엔드 캐시 무효화 신호 처리 완료')
}

/**
 * 캐시 무효화 후 페이지 새로고침을 트리거합니다.
 * @param {boolean} forceReload - 강제 새로고침 여부
 */
export function triggerPageRefresh(forceReload = false) {
  if (forceReload) {
    // 강제 새로고침
    window.location.reload(true)
  } else {
    // 일반 새로고침
    window.location.reload()
  }
}

/**
 * Vue 컴포넌트의 데이터를 강제로 새로고침합니다.
 * @param {Object} component - Vue 컴포넌트 인스턴스
 * @param {string} methodName - 새로고침할 메서드 이름
 */
export function refreshComponentData(component, methodName) {
  if (component && typeof component[methodName] === 'function') {
    debugLog(`컴포넌트 데이터 새로고침: ${methodName}`)
    component[methodName]()
  } else {
    debugLog(`컴포넌트 메서드를 찾을 수 없음: ${methodName}`, null, 'warn')
  }
}
