/**
 * 디버그 유틸리티 함수들
 */

// 환경 확인
const isProduction = process.env.NODE_ENV === 'production'

/**
 * 디버그 모드가 활성화되어 있는지 확인
 * @returns {boolean} 디버그 모드 여부
 */
export function isDebugMode() {
  try {
    return sessionStorage.getItem('debug') === 'true'
  } catch (error) {
    return false
  }
}

/**
 * 디버그 로그 출력 (디버그 모드일 때만)
 * @param {string} message - 로그 메시지
 * @param {any} data - 출력할 데이터 (선택사항)
 * @param {string} level - 로그 레벨 ('log', 'warn', 'error', 'info')
 */
export function debugLog(message, data = null, level = 'log') {
  // 디버그 모드가 활성화되어 있지 않으면 조용히 반환 (아무것도 출력하지 않음)
  if (!isDebugMode()) {
    return
  }
  
  // 프로덕션 환경에서도 디버그 플래그가 있으면 출력 (디버깅 목적)
  const timestamp = new Date().toLocaleTimeString()
  const prefix = `🔍 [${timestamp}]`
  
  switch (level) {
    case 'warn':
      console.warn(prefix, message, data)
      break
    case 'error':
      console.error(prefix, message, data)
      break
    case 'info':
      console.info(prefix, message, data)
      break
    default:
      console.log(prefix, message, data)
  }
}

/**
 * 디버그 모드를 토글
 */
export function toggleDebugMode() {
  try {
    const currentDebug = sessionStorage.getItem('debug') === 'true'
    sessionStorage.setItem('debug', (!currentDebug).toString())
    if (!isProduction) {
      console.log(`🔧 디버그 모드가 ${!currentDebug ? '활성화' : '비활성화'}되었습니다.`)
    }
    return !currentDebug
  } catch (error) {
    console.error('디버그 모드 토글 실패:', error)
    return false
  }
}

/**
 * 디버그 모드를 활성화
 */
export function enableDebugMode() {
  try {
    sessionStorage.setItem('debug', 'true')
    if (!isProduction) {
      console.log('🔧 디버그 모드가 활성화되었습니다.')
    }
    return true
  } catch (error) {
    console.error('디버그 모드 활성화 실패:', error)
    return false
  }
}

/**
 * 디버그 모드를 비활성화
 */
export function disableDebugMode() {
  try {
    sessionStorage.setItem('debug', 'false')
    if (!isProduction) {
      console.log('🔧 디버그 모드가 비활성화되었습니다.')
    }
    return true
  } catch (error) {
    console.error('디버그 모드 비활성화 실패:', error)
    return false
  }
}

/**
 * 디버그 로그 출력 (디버그 모드일 때만 출력)
 * @param {string} message - 로그 메시지
 * @param {any} data - 출력할 데이터 (선택사항)
 * @param {string} level - 로그 레벨 ('log', 'warn', 'error', 'info')
 */
export function forceDebugLog(message, data = null, level = 'log') {
  // 디버그 모드가 활성화되어 있지 않으면 조용히 반환 (아무것도 출력하지 않음)
  if (!isDebugMode()) {
    return
  }
  
  const timestamp = new Date().toLocaleTimeString()
  const prefix = `🔍 [FORCE] [${timestamp}]`
  
  switch (level) {
    case 'warn':
      console.warn(prefix, message, data)
      break
    case 'error':
      console.error(prefix, message, data)
      break
    case 'info':
      console.info(prefix, '[INFO]', message, data)
      break
    default:
      console.log(prefix, message, data)
  }
}

/**
 * 함수 실행 시간 측정 (디버그 모드일 때만)
 * @param {string} name - 함수명
 * @param {Function} fn - 실행할 함수
 * @returns {any} 함수 실행 결과
 */
export async function debugTime(name, fn) {
  // 운영 환경에서는 디버그 로그를 출력하지 않음
  if (isProduction) {
    return await fn()
  }
  
  if (!isDebugMode()) {
    return await fn()
  }

  const start = performance.now()
  try {
    const result = await fn()
    const end = performance.now()
    debugLog(`⏱️ ${name} 실행 시간: ${(end - start).toFixed(2)}ms`)
    return result
  } catch (error) {
    const end = performance.now()
    debugLog(`⏱️ ${name} 실행 시간 (에러): ${(end - start).toFixed(2)}ms`, error, 'error')
    throw error
  }
}

/**
 * 객체 상태 로깅 (디버그 모드일 때만)
 * @param {string} name - 객체명
 * @param {any} obj - 로깅할 객체
 */
export function debugObject(name, obj) {
  // 운영 환경에서는 디버그 로그를 출력하지 않음
  if (isProduction) return
  
  if (!isDebugMode()) return
  
  debugLog(`📊 ${name} 상태:`, obj)
}

/**
 * API 요청/응답 로깅 (디버그 모드일 때만)
 * @param {string} method - HTTP 메서드
 * @param {string} url - 요청 URL
 * @param {any} requestData - 요청 데이터
 * @param {any} responseData - 응답 데이터
 * @param {number} status - HTTP 상태 코드
 */
export function debugApi(method, url, requestData = null, responseData = null, status = null) {
  // 운영 환경에서는 디버그 로그를 출력하지 않음
  if (isProduction) return
  
  if (!isDebugMode()) return

  const timestamp = new Date().toLocaleTimeString()
  const prefix = `🌐 [${timestamp}] ${method.toUpperCase()} ${url}`
  
  if (requestData) {
    debugLog(`${prefix} 요청:`, requestData)
  }
  
  if (responseData !== null) {
    const statusText = status ? ` (${status})` : ''
    debugLog(`${prefix} 응답${statusText}:`, responseData)
  }
}

/**
 * 컴포넌트 라이프사이클 로깅 (디버그 모드일 때만)
 * @param {string} componentName - 컴포넌트명
 * @param {string} lifecycle - 라이프사이클 메서드명
 * @param {any} data - 추가 데이터
 */
export function debugLifecycle(componentName, lifecycle, data = null) {
  // 운영 환경에서는 디버그 로그를 출력하지 않음
  if (isProduction) return
  
  if (!isDebugMode()) return
  
  debugLog(`🔄 ${componentName} ${lifecycle}`, data)
}

/**
 * 이벤트 로깅 (디버그 모드일 때만)
 * @param {string} eventName - 이벤트명
 * @param {any} eventData - 이벤트 데이터
 */
export function debugEvent(eventName, eventData = null) {
  // 운영 환경에서는 디버그 로그를 출력하지 않음
  if (isProduction) return
  
  if (!isDebugMode()) return
  
  debugLog(`🎯 이벤트: ${eventName}`, eventData)
}

/**
 * 상태 변경 로깅 (디버그 모드일 때만)
 * @param {string} componentName - 컴포넌트명
 * @param {string} propertyName - 속성명
 * @param {any} oldValue - 이전 값
 * @param {any} newValue - 새로운 값
 */
export function debugStateChange(componentName, propertyName, oldValue, newValue) {
  // 운영 환경에서는 디버그 로그를 출력하지 않음
  if (isProduction) return
  
  if (!isDebugMode()) return
  
  debugLog(`🔄 ${componentName}.${propertyName} 변경:`, {
    old: oldValue,
    new: newValue
  })
}

/**
 * 디버그 모드 상태를 콘솔에 출력
 */
export function showDebugStatus() {
  // 운영 환경에서는 디버그 로그를 출력하지 않음
  if (isProduction) return
  
  const isDebug = isDebugMode()
  
  if (!isProduction) {
    debugLog(`🔧 디버그 모드: ${isDebug ? '활성화' : '비활성화'}`)
    
    if (isDebug) {
      debugLog('💡 디버그 모드가 활성화되어 있습니다.')
      debugLog('💡 디버그 모드를 비활성화하려면: disableDebugMode()')
      debugLog('💡 디버그 모드를 토글하려면: toggleDebugMode()')
    } else {
      debugLog('💡 디버그 모드를 활성화하려면: enableDebugMode()')
      debugLog('💡 디버그 모드를 토글하려면: toggleDebugMode()')
    }
  }
}

// 전역 함수로 등록 (항상 등록 - 프로덕션에서도 디버깅 가능하도록)
if (typeof window !== 'undefined') {
  window.enableDebugMode = enableDebugMode
  window.disableDebugMode = disableDebugMode
  window.toggleDebugMode = toggleDebugMode
  window.showDebugStatus = showDebugStatus
  window.debugLog = debugLog
  window.forceDebugLog = forceDebugLog
  window.isDebugMode = isDebugMode
  
  // 빌드 반영 확인용 로그는 제거 (불필요한 로그)
} 