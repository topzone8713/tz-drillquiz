import Vue from 'vue'
import App from './App.vue'
import router from './router'
import axios from 'axios'
import BootstrapVue from 'bootstrap-vue'
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'
import '@fortawesome/fontawesome-free/css/all.min.css'
import './assets/css/mobile-buttons.css'
import { debugLog, showDebugStatus } from './utils/debugUtils'
import { getCurrentDomainConfig, replaceDrillQuizName } from './utils/domainUtils'
import VueMeta from 'vue-meta'
import i18n from './i18n'
import {
  ENVIRONMENT,
  apiBaseURL
} from './config/apiConfig'
import authService from './services/authService'
import api, { authAPI } from './services/api'


// 환경 확인 (다른 코드에서 사용되기 전에 먼저 선언)
const isProduction = process.env.NODE_ENV === 'production'

debugLog('[DrillQuiz] API base URL resolved to:', apiBaseURL)
debugLog('🔍 [main.js] [INIT] 최초 로딩 시작')
debugLog('🔍 [main.js] [INIT] 현재 환경:', {
  environment: ENVIRONMENT,
  isProduction,
  protocol: typeof window !== 'undefined' ? window.location.protocol : 'N/A',
  origin: typeof window !== 'undefined' ? window.location.origin : 'N/A',
  hostname: typeof window !== 'undefined' ? window.location.hostname : 'N/A'
})

// axios 기본 설정
axios.defaults.baseURL = apiBaseURL
axios.defaults.withCredentials = true  // 쿠키 포함

// 개발 환경에서도 console.log를 조건부로 실행 (debugLog 유틸리티 사용 권장)
// 단, 중요한 에러 로그는 유지
// 주의: 프로덕션에서 디버깅을 위해 console.log 오버라이드를 비활성화
// 대신 debugLog 유틸리티를 사용하거나, sessionStorage.debug를 설정하면 모든 로그가 보임
if (typeof window !== 'undefined' && !isProduction) {
  // 개발 환경에서만 console.log 오버라이드
  // sessionStorage debug flag 로그는 제거 (불필요한 로그)
  const originalConsoleLog = console.log
  const originalConsoleDebug = console.debug
  const originalConsoleInfo = console.info
  
  // sessionStorage에서 debug 플래그를 확인하는 함수
  const isDebugEnabled = () => {
    try {
      return sessionStorage.getItem('debug') === 'true'
    } catch (error) {
      return false
    }
  }
  
  // console.log 오버라이드 - debug 모드가 아니면 출력하지 않음 (개발 환경에서만)
  console.log = function(...args) {
    if (isDebugEnabled()) {
      originalConsoleLog.apply(console, args)
    }
  }
  
  console.debug = function(...args) {
    if (isDebugEnabled()) {
      originalConsoleDebug.apply(console, args)
    }
  }
  
  console.info = function(...args) {
    if (isDebugEnabled()) {
      originalConsoleInfo.apply(console, args)
    }
  }
  
  // console.warn과 console.error는 항상 출력되도록 유지
} else if (typeof window !== 'undefined' && isProduction) {
  // 프로덕션 환경에서는 console.log 오버라이드하지 않음 (디버깅 가능하도록)
  // 불필요한 로그는 제거
}

debugLog(`DrillQuiz ${ENVIRONMENT} 환경으로 시작됨`)
debugLog(`API Base URL: ${apiBaseURL}`)
debugLog('JWT 기반 인증 모드로 실행됩니다.')

// Bootstrap Vue 설정
Vue.use(BootstrapVue)

// Vue Meta 설정
Vue.use(VueMeta)

// DevOps 도메인에서 "DrillQuiz"를 "DrillQuiz DevOps"로 변환하는 전역 필터
Vue.filter('drillQuizName', function (value) {
  if (!value || typeof value !== 'string') {
    return value
  }
  return replaceDrillQuizName(value)
})

// Google OAuth 설정 - Google Identity Services 직접 사용 (FedCM 지원)
let googleClientId = process.env.VUE_APP_GOOGLE_CLIENT_ID
let googleRedirectUri = null

// 백엔드에서 Google OAuth 설정 가져오기
async function loadGoogleOAuthConfig() {
  try {
    debugLog('🔍 [main.js] loadGoogleOAuthConfig 호출됨')
    debugLog('🔍 [main.js] Google OAuth 설정 로드 시작...')
    // 현재 도메인을 쿼리 파라미터로 전달
    let currentDomain = window.location.hostname
    debugLog('🔍 [main.js] 최종 사용할 currentDomain:', currentDomain)
    
    // 현재 도메인을 사용하여 API 호출
    const configUrl = `${apiBaseURL}/api/google-oauth/config/?domain=${encodeURIComponent(currentDomain)}`
    debugLog('🔍 [main.js] config API 호출 URL:', configUrl)
    const response = await fetch(configUrl)
    debugLog('🔍 [main.js] config API 응답 받음:', {
      status: response.status,
      ok: response.ok
    })
    if (response.ok) {
      const responseText = await response.text()
      
      try {
        const config = JSON.parse(responseText)
        debugLog('🔍 [main.js] 백엔드에서 받은 config (파싱 완료)')
        googleClientId = config.client_id
        googleRedirectUri = config.redirect_uri
        debugLog('🔍 [main.js] 백엔드에서 받은 Google OAuth 설정:', {
          clientId: googleClientId?.substring(0, 20) + '...',
          redirectUri: googleRedirectUri
        })
      } catch (parseError) {
        console.error('❌ [main.js] JSON 파싱 실패:', parseError)
        console.error('❌ [main.js] 응답 본문:', responseText)
        throw new Error(`JSON 파싱 실패: ${parseError.message}. 응답: ${responseText.substring(0, 100)}`)
      }
    } else {
      console.warn('⚠️ [main.js] config API 응답 실패:', {
        status: response.status,
        statusText: response.statusText
      })
      console.warn('⚠️ [main.js] Google OAuth 설정을 가져올 수 없습니다, 환경 변수 사용')
      // 환경 변수 fallback
      if (!googleClientId) {
        googleClientId = process.env.VUE_APP_GOOGLE_CLIENT_ID
        if (!isProduction) {
          debugLog('🔍 [main.js] 환경 변수에서 CLIENT_ID 로드:', googleClientId?.substring(0, 20) + '...')
        }
      }
      if (!googleRedirectUri) {
        googleRedirectUri = process.env.VUE_APP_GOOGLE_REDIRECT_URI || `${window.location.origin}/api/google-oauth/`
        if (!isProduction) {
          debugLog('🔍 [main.js] 환경 변수에서 REDIRECT_URI 로드:', googleRedirectUri)
        }
      }
    }
  } catch (error) {
    console.error('❌ [main.js] Google OAuth 설정 로드 실패:', error)
    console.warn('❌ [main.js] Google OAuth 설정 로드 실패, 환경 변수 사용:', error.message || error)
    // 환경 변수 fallback
    if (!googleClientId) {
      googleClientId = process.env.VUE_APP_GOOGLE_CLIENT_ID
      if (!isProduction) {
        debugLog('🔍 [main.js] 환경 변수에서 CLIENT_ID 로드 (fallback):', googleClientId?.substring(0, 20) + '...')
      }
    }
    if (!googleRedirectUri) {
      googleRedirectUri = process.env.VUE_APP_GOOGLE_REDIRECT_URI || `${window.location.origin}/api/google-oauth/`
      if (!isProduction) {
        debugLog('🔍 [main.js] 환경 변수에서 REDIRECT_URI 로드 (fallback):', googleRedirectUri)
      }
    }
  }
  
  // 환경 변수에서도 값을 가져오지 못한 경우 하드코딩된 기본값 사용
  if (!googleClientId) {
    googleClientId = '195449497097-rf2f22ampv4imqb80fvibhr7oq5oc7km.apps.googleusercontent.com'
    if (!isProduction) {
      debugLog('🔑 하드코딩된 기본 CLIENT_ID 사용:', googleClientId?.substring(0, 20) + '...')
    }
  }
  
  if (!googleRedirectUri) {
    googleRedirectUri = 'http://localhost:8000/api/google-oauth/'
    if (!isProduction) {
      debugLog('🔗 하드코딩된 기본 REDIRECT_URI 사용:', googleRedirectUri)
    }
  }
  
  // CLIENT_SECRET도 확인 (프론트엔드에서는 사용하지 않지만 로깅용)
  const googleClientSecret = process.env.VUE_APP_GOOGLE_CLIENT_SECRET || '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'
  if (!isProduction) {
    debugLog('🔐 CLIENT_SECRET 상태:', {
      fromEnv: !!process.env.VUE_APP_GOOGLE_CLIENT_SECRET,
      value: googleClientSecret?.substring(0, 10) + '...',
      length: googleClientSecret?.length || 0
    })
  }
  
  // 설정 검증
  if (!googleClientId) {
    console.error('❌ [main.js] Google OAuth CLIENT_ID가 설정되지 않았습니다!')
    throw new Error('Google OAuth CLIENT_ID가 설정되지 않았습니다')
  }
  
  debugLog('🔗 [main.js] 최종 Google OAuth 설정:', {
    clientId: googleClientId?.substring(0, 20) + '...',
    redirectUri: googleRedirectUri
  })
}



// Google Identity Services 스크립트 로드 및 초기화
async function initializeGoogleOAuth() {
  // 백엔드에서 Google OAuth 설정 로드
  await loadGoogleOAuthConfig()
  
  return new Promise((resolve, reject) => {
    // Google Identity Services 스크립트 로드
    const script = document.createElement('script')
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.defer = true
    
    script.onload = () => {
      // Google Identity Services가 로드되었는지 확인
      if (window.google && window.google.accounts && window.google.accounts.id) {
        debugLog('🔍 [main.js] Google Identity Services 로드 성공')
        
                // Google OAuth 설정 검증
        try {
          if (!googleClientId) {
            throw new Error('Google OAuth CLIENT_ID가 설정되지 않았습니다')
          }
          
          // Google OAuth 객체 생성
          const googleAccounts = {

            
                        // 대체 로그인 방법: 리다이렉트 기반 (COOP 정책 문제 해결)
            fallbackSignIn: async function(resolve, reject) {
              try {
                if (!isProduction) {
                  debugLog('🔍 [main.js] fallbackSignIn 호출됨')
                }
                // 설정 검증
                if (!googleClientId) {
                  throw new Error('Google OAuth CLIENT_ID가 설정되지 않았습니다')
                }
                
                // 백엔드에서 가져온 리다이렉트 URI 사용
                const redirectUri = googleRedirectUri || `${window.location.origin}/api/google-oauth/`
                if (!isProduction) {
                  debugLog('🔍 [main.js] 사용할 redirectUri:', redirectUri)
                  debugLog('🔍 [main.js] googleRedirectUri 값:', googleRedirectUri)
                  debugLog('🔍 [main.js] window.location.origin:', window.location.origin)
                }
                
                // 현재 페이지 URL을 state로 저장 (복귀 시 확인용)
                const state = btoa(JSON.stringify({
                  timestamp: Date.now(),
                  returnUrl: window.location.href
                }))
                if (!isProduction) {
                  debugLog('🔍 [main.js] 생성된 state:', state)
                }
                
                // Google OAuth 리다이렉트 URL 생성 (authorization code 방식)
                const clientIdEncoded = encodeURIComponent(googleClientId)
                const redirectUriEncoded = encodeURIComponent(redirectUri)
                const stateEncoded = encodeURIComponent(state)
                const scopeEncoded = encodeURIComponent('openid email profile')
                
                const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?` +
                  `client_id=${clientIdEncoded}` +
                  `&redirect_uri=${redirectUriEncoded}` +
                  `&response_type=code` +
                  `&scope=${scopeEncoded}` +
                  `&state=${stateEncoded}` +
                  `&prompt=select_account`
                
                // 전체 URL 로깅 (중요: Google에 실제로 전송되는 요청)
                console.warn('🔍 [main.js] [OAUTH_REQUEST] 생성된 Google OAuth URL (전체, 웹환경):', authUrl)
                console.warn('🔍 [main.js] [OAUTH_REQUEST] URL 길이 (웹환경):', authUrl.length)
                
                // 모든 파라미터 상세 로깅
                console.warn('🔍 [main.js] [OAUTH_REQUEST] 파라미터 상세 분석 (웹환경):', {
                  client_id: {
                    원본: googleClientId,
                    인코딩됨: clientIdEncoded,
                    길이: googleClientId?.length || 0
                  },
                  redirect_uri: {
                    원본: redirectUri,
                    인코딩됨: redirectUriEncoded,
                    길이: redirectUri.length
                  },
                  response_type: 'code',
                  scope: {
                    원본: 'openid email profile',
                    인코딩됨: scopeEncoded
                  },
                  state: {
                    원본: state,
                    인코딩됨: stateEncoded,
                    디코딩_테스트: (() => {
                      try {
                        return JSON.parse(atob(state))
                      } catch (e) {
                        return '디코딩_실패: ' + e.message
                      }
                    })()
                  },
                  prompt: 'select_account'
                })
                
                // URL 파싱하여 각 파라미터 확인
                try {
                  const urlObj = new URL(authUrl)
                  const params = new URLSearchParams(urlObj.search)
                  console.warn('🔍 [main.js] [OAUTH_REQUEST] URL 파싱 결과 (웹환경):', {
                    baseURL: urlObj.origin + urlObj.pathname,
                    파라미터_개수: params.size,
                    client_id_값: params.get('client_id'),
                    redirect_uri_값: params.get('redirect_uri'),
                    response_type_값: params.get('response_type'),
                    scope_값: params.get('scope'),
                    state_값: params.get('state'),
                    prompt_값: params.get('prompt')
                  })
                } catch (parseError) {
                  console.error('🔍 [main.js] [OAUTH_REQUEST] URL 파싱 실패 (웹환경):', parseError)
                }
                
                if (!isProduction) {
                  debugLog('🔍 [main.js] Google OAuth로 리다이렉트 시작...')
                }
                
                window.location.href = authUrl
                
                // 리다이렉트되므로 resolve/reject는 호출되지 않음
                // 백엔드에서 처리 후 프론트엔드로 리다이렉트
              } catch (error) {
                debugLog('Google OAuth 리다이렉트 오류:', error, 'error')
                reject(new Error('Google OAuth 리다이렉트를 시작할 수 없습니다: ' + error.message))
              }
            },
            
            // 로그인 메서드 (리다이렉트 방식)
            signIn: function() {
              return new Promise((resolve, reject) => {
                this.fallbackSignIn(resolve, reject)
              })
            }
          }
          
                resolve(googleAccounts)
    } catch (error) {
      debugLog('Google OAuth 초기화 실패:', error, 'error')
      reject(error)
    }
  } else {
    reject(new Error('Google Identity Services 로드 실패'))
  }
}

script.onerror = () => {
  reject(new Error('Google Identity Services 스크립트 로드 실패'))
}

script.onabort = () => {
  reject(new Error('Google Identity Services 스크립트 로딩 중단됨'))
}

document.head.appendChild(script)
  })
}

// Google OAuth 초기화는 initializeApp()에서 처리됨


Vue.config.productionTip = false

// 디버그 모드 상태 출력
showDebugStatus()



// axios 인스턴스를 Vue 인스턴스에 추가
Vue.prototype.$http = api



// 인증 상태 확인 (Vue 앱 마운트 후 사용)
async function checkAuthStatus() {
  try {
    debugLog('🔍 [main.js] checkAuthStatus() 시작')
    
    const accessToken = await authService.getAccessToken()
    if (!accessToken) {
      debugLog('🔍 [main.js] accessToken 없음, 서버 세션 확인 시도')
      
      // 서버 세션 확인 (Google OAuth는 세션 기반)
      try {
        // 쿠키 확인
        if (typeof document !== 'undefined' && document.cookie) {
          const cookies = document.cookie.split('; ').map(c => c.split('=')[0])
          debugLog('🔍 [main.js] [checkAuthStatus] 현재 쿠키 목록:', cookies)
          const sessionCookie = document.cookie.split('; ').find(row => row.startsWith('sessionid='))
          const csrfCookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='))
          debugLog('🔍 [main.js] [checkAuthStatus] 쿠키 상태:', {
            hasSessionCookie: !!sessionCookie,
            hasCsrfCookie: !!csrfCookie
          })
        } else {
          debugLog('🔍 [main.js] [checkAuthStatus] document.cookie 없음')
        }
        
        const statusResponse = await api.get('/api/auth/status/')
        debugLog('🔍 [main.js] 서버 세션 확인 API 응답:', {
          authenticated: statusResponse.data?.authenticated || false
        })
        
        // 응답 헤더 확인
        if (statusResponse.headers) {
          debugLog('🔍 [main.js] [checkAuthStatus] 응답 헤더 확인')
        }
        if (statusResponse.data && statusResponse.data.authenticated) {
          const user = statusResponse.data.user
          await authService.storeAuthResult({ user })
          Vue.prototype.$isAuthenticated = true
          Vue.prototype.$currentUser = user
          
          if (window.vueApp) {
            window.dispatchEvent(new CustomEvent('authStatusChanged', {
              detail: {
                authenticated: true,
                user
              }
            }))
          }
          
          debugLog('✅ [main.js] 서버 세션 확인 완료 - 로그인 성공!', { email: user?.email })
          return { authenticated: true, user }
        } else {
          debugLog('⚠️ [main.js] 서버 세션 확인 결과: 인증되지 않음')
        }
      } catch (error) {
        // 400 Bad Request는 인증되지 않은 상태로 정상 처리 (조용히 무시)
        if (error.response && error.response.status === 400) {
          debugLog('서버 세션 확인: 인증되지 않은 상태 (400)', null, 'debug')
        } else {
          console.error('❌ [main.js] 서버 세션 확인 실패:', error)
        }
      }
      
      Vue.prototype.$isAuthenticated = false
      Vue.prototype.$currentUser = null
      debugLog('❌ [main.js] 인증 실패 - 로그인되지 않음')
      return { authenticated: false, user: null }
    }

    const response = await authAPI.getProfile()
    const user = response.data
    await authService.storeAuthResult({ user })

    Vue.prototype.$isAuthenticated = true
    Vue.prototype.$currentUser = user

    if (window.vueApp) {
      window.dispatchEvent(new CustomEvent('authStatusChanged', {
        detail: {
          authenticated: true,
          user
        }
      }))
    }
    
    debugLog('✅ [main.js] checkAuthStatus() 완료 - 로그인 성공!', { email: user?.email })

    return { authenticated: true, user }
  } catch (error) {
    debugLog('인증 상태 확인 실패:', error, 'error')
    await authService.clearAuth()
    Vue.prototype.$isAuthenticated = false
    Vue.prototype.$currentUser = null
  }
  return { authenticated: false, user: null }
}

// 현재 도메인에서 기본 태그 설정 (범용)
async function setupCurrentDomainDefaultTags() {
  const domainConfig = getCurrentDomainConfig()
  if (!domainConfig) {
    return
  }
  
  try {
    if (!isProduction) {
      debugLog(`🏷️ ${domainConfig.tagName} 도메인 - 로그인 후 기본 태그 설정 시작`)
    }
    
    // 서버에서 태그 정보 가져오기
    const response = await fetch('/api/tags/')
    const data = await response.json()
    
    if (data.results && Array.isArray(data.results)) {
      // 모든 지원 언어 필드를 확인하도록 수정
      const tag = data.results.find(t => {
        // 모든 지원 언어 필드 확인 (ko, en, es, zh, ja)
        const supportedLanguages = ['ko', 'en', 'es', 'zh', 'ja']
        for (const lang of supportedLanguages) {
          if (t[`name_${lang}`] === domainConfig.tagName) {
            return true
          }
        }
        // localized_name도 확인
        return t.localized_name === domainConfig.tagName
      })
      
      if (tag) {
        // sessionStorage에 태그 ID 저장
        sessionStorage.setItem(domainConfig.storageKey, tag.id.toString())
        if (!isProduction) {
          debugLog(`✅ ${domainConfig.tagName} 태그 ID 저장됨:`, tag.id)
        }
        
        // localStorage에 기본 태그 설정 플래그 저장
        localStorage.setItem(domainConfig.localStorageSetKey, 'true')
        localStorage.setItem(domainConfig.localStorageKey, JSON.stringify([tag.id]))
        
        if (!isProduction) {
          debugLog(`📊 기본 ${domainConfig.tagName} 태그 설정 완료:`, [tag.id])
        }
      } else {
        if (!isProduction) {
          debugLog(`⚠️ ${domainConfig.tagName} 태그를 찾을 수 없습니다`, null, 'warn')
        }
      }
    }
  } catch (error) {
    if (!isProduction) {
      debugLog(`❌ ${domainConfig.tagName} 기본 태그 설정 실패:`, error, 'error')
    }
  }
}

// OAuth 콜백 URL scheme 리스너 등록 (웹 환경에서는 필요 없음)
async function registerOAuthCallbackListener() {
  // 웹 환경에서는 OAuth 콜백이 URL 파라미터로 처리되므로 리스너가 필요 없음
  debugLog('🔍 [main.js] [registerOAuthCallbackListener] 웹 환경에서는 OAuth 콜백 리스너가 필요 없습니다.')
}

// Vue 앱 초기화 전에 Google OAuth 설정 로드
async function initializeApp() {
  debugLog('🔍 [main.js] [INIT] initializeApp() 함수 호출됨 - 최초 웹뷰 로딩')
  
  // OAuth 콜백 리스너 등록 (앱 초기화 시점에 한 번만)
  try {
    await registerOAuthCallbackListener()
    debugLog('🔍 [main.js] [initializeApp] registerOAuthCallbackListener() 호출 완료')
  } catch (error) {
    console.error('❌ [main.js] [initializeApp] registerOAuthCallbackListener() 호출 실패:', error)
  }
  
  try {
    // Google OAuth 초기화
    debugLog('🔍 [main.js] Google OAuth 초기화 시작')
    const googleOAuth = await initializeGoogleOAuth()
    Vue.prototype.$googleOAuth = googleOAuth
    debugLog('🔍 [main.js] Google OAuth 객체가 Vue 프로토타입에 할당됨')

    // URL 파라미터에서 로그인 상태 확인 (Fallback: App.addListener가 작동하지 않는 경우)
    const urlParams = new URLSearchParams(window.location.search)
    const loginStatus = urlParams.get('login')
    const email = urlParams.get('email')
    const errorMessage = urlParams.get('message')
    
    // URL 파라미터에서 access_token 확인
    const accessToken = urlParams.get('access_token')
    
    // URL 파라미터에서 login=success 확인
    const hasLoginSuccess = loginStatus === 'success' && email
    
    debugLog('🔍 [main.js] URL 확인:', {
      href: window.location.href.substring(0, 50) + '...',
      loginStatus,
      hasLoginSuccess,
      accessToken: !!accessToken
    })
    
    // JWT 토큰이 있으면 먼저 저장 (쿠키가 전달되지 않는 경우 대비)
    if (accessToken) {
      debugLog('🔍 [main.js] URL에서 access_token 발견 (Fallback), 저장 시작')
      
      try {
        // JWT 토큰 저장
        await authService.storeAuthResult({
          access: accessToken,
          user: email ? { email } : null
        })
        
        debugLog('✅ [main.js] access_token 저장 완료')
        
        // 인증 상태 확인 (프로필 정보 가져오기)
        await checkAuthStatus()
        debugLog('🔍 [main.js] 인증 상태 확인 완료')
        
        // URL 파라미터 정리 (OAuth 콜백 파라미터 제거)
        window.history.replaceState({}, document.title, window.location.pathname)
      } catch (error) {
        console.error('❌ [main.js] access_token 저장 실패 (Fallback):', error)
      }
    }
    
    // login=success 파라미터가 있으면 OAuth 콜백으로 처리
    if (hasLoginSuccess) {
      debugLog('🔍 [main.js] OAuth 콜백 감지, 인증 상태 확인 시작')
      
      // 인증 상태 확인
      await checkAuthStatus()
      debugLog('🔍 [main.js] 인증 상태 확인 완료')
      
      if (!isProduction) {
        debugLog('Google OAuth 로그인 성공:', email || 'OAuth callback')
      }
      
      // 현재 도메인인 경우 기본 태그 설정
      await setupCurrentDomainDefaultTags()
      
      // URL 파라미터 정리
      window.history.replaceState({}, document.title, window.location.pathname)
      
      // 로그인 성공 시 홈으로 이동
      if (router && router.currentRoute && router.currentRoute.path !== '/') {
        router.push('/')
      }
    } else if (loginStatus === 'error') {
      if (!isProduction) {
        debugLog('Google OAuth 로그인 실패:', errorMessage, 'error')
      }
      // 오류 메시지 표시 (필요시)
      // URL 파라미터 정리
      window.history.replaceState({}, document.title, window.location.pathname)
    }
    
    // Vue 앱 마운트
    debugLog('🔍 [main.js] Vue 앱 마운트 시작')
    window.vueApp = new Vue({
      router,
      i18n,
      render: h => h(App)
    }).$mount('#app')
    debugLog('🔍 [main.js] Vue 앱 마운트 완료')
    
    // Vue 앱 마운트 후 OAuth 로그인 성공 처리 및 라우팅
    if (accessToken || hasLoginSuccess) {
      debugLog('🔍 [main.js] Vue 앱 마운트 후 OAuth 로그인 처리 시작')
      // 로그인 성공 시 홈으로 이동
      if (router && router.currentRoute && router.currentRoute.path !== '/') {
        router.push('/')
      }
    } else {
      // 일반적인 경우에만 인증 상태 확인 (이미 OAuth 콜백에서 확인했으면 중복 방지)
      debugLog('🔍 [main.js] 인증 상태 확인 시작')
      await checkAuthStatus()
      debugLog('🔍 [main.js] 인증 상태 확인 완료')
    }
    
  } catch (error) {
    console.error('❌ [main.js] Google OAuth 초기화 실패:', error)
    
    // Google OAuth 초기화 실패 시에도 Vue 프로토타입에 null 할당
    Vue.prototype.$googleOAuth = null
    
    // Vue 앱 마운트 (Google OAuth 없이)
    debugLog('🔍 [main.js] Vue 앱 마운트 시작 (Google OAuth 없이)')
    window.vueApp = new Vue({
      router,
      i18n,
      render: h => h(App)
    }).$mount('#app')
    debugLog('🔍 [main.js] Vue 앱 마운트 완료 (Google OAuth 없이)')
    
    // Vue 앱 마운트 후 인증 상태 확인
    debugLog('🔍 [main.js] 인증 상태 확인 시작')
    await checkAuthStatus()
    debugLog('🔍 [main.js] 인증 상태 확인 완료')
  }
}

// 앱 초기화 시작
debugLog('🔍 [main.js] [INIT] initializeApp() 호출 시작 - 스크립트 로드 완료')
initializeApp()

// 빌드 반영 확인용 로그 (개발 환경에서만 출력)
if (process.env.NODE_ENV !== 'production') {
  console.log('🚀 [MAIN.JS] main.js 초기화 완료')
}