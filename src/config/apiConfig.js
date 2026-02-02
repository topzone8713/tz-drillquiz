const ENVIRONMENT = process.env.VUE_APP_ENVIRONMENT || 'development'

const API_HOST = process.env.VUE_APP_API_HOST || 'localhost'
const API_PORT = process.env.VUE_APP_API_PORT || '8000'
const API_PROTOCOL = process.env.VUE_APP_API_PROTOCOL || 'http'
const API_BASE_URL = process.env.VUE_APP_API_BASE_URL || ''

const buildBaseUrl = (protocol, host, port) => {
  if (!host) return ''
  const normalizedPort = port && `${port}` !== '' ? `:${port}` : ''
  return `${protocol}://${host}${normalizedPort}`
}

const resolveApiBaseUrl = () => {
  // If VUE_APP_API_BASE_URL is explicitly set, use it (highest priority)
  if (API_BASE_URL) {
    return API_BASE_URL
  }

  let protocol = API_PROTOCOL
  let host = API_HOST
  let port = API_PORT

  if (ENVIRONMENT === 'production') {
    // For web production, use window.location.origin
    if (typeof window !== 'undefined') {
      return window.location.origin
    }
    return buildBaseUrl(protocol, host, port)
  }

  // Development mode
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname
    const isLocalHost = ['localhost', '127.0.0.1'].includes(hostname)

    // Web 개발 환경에서 Vue dev server가 실행 중이면 proxy 사용 (빈 문자열)
    // proxy를 사용하면 쿠키가 제대로 전달됨
    if (isLocalHost) {
      // Vue dev server의 proxy 사용 (쿠키 전달을 위해 필요)
      return ''
    }
  }

  return buildBaseUrl(protocol, host, port)
}

const apiBaseURL = resolveApiBaseUrl()

// 디버그용: 콘솔에서 API 설정 확인 가능하도록 전역 노출
if (typeof window !== 'undefined') {
  window.__API_CONFIG__ = {
    apiBaseURL,
    ENVIRONMENT,
    API_HOST,
    API_PORT,
    API_PROTOCOL,
    location: {
      protocol: window.location?.protocol,
      hostname: window.location?.hostname
    }
  }
  
  // 개발 환경에서는 자동으로 로그 출력
  if (ENVIRONMENT === 'development') {
    console.log('🔍 [API Config] API Base URL:', apiBaseURL)
    console.log('🔍 [API Config] Environment:', ENVIRONMENT)
  }
}

export {
  ENVIRONMENT,
  API_HOST,
  API_PORT,
  API_PROTOCOL,
  apiBaseURL
}


