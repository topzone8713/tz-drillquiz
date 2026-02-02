import axios from 'axios'
import authService from './authService'
import { apiBaseURL } from '../config/apiConfig'

const isBrowser = typeof window !== 'undefined' && typeof document !== 'undefined'

const getCookie = (name) => {
  if (!isBrowser) {
    return null
  }
  const value = document.cookie
    .split('; ')
    .find((row) => row.startsWith(`${name}=`))
  return value ? decodeURIComponent(value.split('=').slice(1).join('=')) : null
}

let activeCsrfFetch = null

const ensureCsrfToken = async () => {
  if (!isBrowser) {
    return null
  }

  const existing = getCookie('csrftoken')
  if (existing) {
    return existing
  }

  if (!activeCsrfFetch) {
    activeCsrfFetch = axios
      .get('/api/csrf-token/', {
        withCredentials: true,
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
      .then((response) => {
        activeCsrfFetch = null
        const cookieToken = getCookie('csrftoken')
        return cookieToken || response?.data?.csrfToken || null
      })
      .catch((error) => {
        activeCsrfFetch = null
        throw error
      })
  }

  return activeCsrfFetch
}

const api = axios.create({
  baseURL: apiBaseURL,
  timeout: 15000, // 기본 타임아웃 15초
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 문제 생성 API는 시간이 오래 걸릴 수 있으므로 별도 인스턴스 생성
const apiWithLongTimeout = axios.create({
  baseURL: apiBaseURL,
  timeout: 600000, // 10분 (600000ms)
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json'
  }
})

const shouldRefresh = async () => {
  const expiresAt = await authService.getAccessTokenExpiry()
  if (!expiresAt) {
    return false
  }
  const now = Date.now()
  return expiresAt - now < 5000
}

const extractAuthPayload = (data = {}) => {
  const tokens = data.tokens || {}
  const access = data.access ?? tokens.access ?? null
  const refresh = data.refresh ?? tokens.refresh ?? null
  const access_expires_in = data.expires_in ?? tokens.access_expires_in ?? null
  const refresh_expires_in = data.refresh_expires_in ?? tokens.refresh_expires_in ?? null

  if (!access && !refresh && !data.user) {
    return null
  }

  return {
    access,
    refresh,
    access_expires_in,
    refresh_expires_in,
    user: data.user ?? null
  }
}

const handleAuthResponse = async (response) => {
  const { data } = response
  const payload = extractAuthPayload(data)
  if (payload) {
    await authService.storeAuthResult(payload)
  }
  return data
}

const attachInterceptors = (client) => {
  client.interceptors.request.use(
    async (config) => {
      try {
        const isRefreshRequest = typeof config.url === 'string' && config.url.includes('/api/token/refresh/')
        if (!isRefreshRequest) {
          const method = (config.method || 'get').toLowerCase()
          if (['post', 'put', 'patch', 'delete'].includes(method)) {
            try {
              let csrfToken = getCookie('csrftoken')
              if (!csrfToken) {
                const ensuredToken = await ensureCsrfToken()
                csrfToken = ensuredToken || getCookie('csrftoken')
              }
              if (csrfToken) {
                config.headers = config.headers || {}
                config.headers['X-CSRFToken'] = csrfToken
              }
            } catch (csrfError) {
              console.warn('[auth] failed to ensure CSRF token', csrfError)
            }
          }

          let accessToken = await authService.getAccessToken()
          if (!accessToken || await shouldRefresh()) {
            try {
              accessToken = await authService.refreshAccessToken()
            } catch (refreshError) {
              await authService.clearAuth()
              accessToken = null
            }
          }

          if (accessToken) {
            config.headers = config.headers || {}
            config.headers.Authorization = `Bearer ${accessToken}`
          }
        }
      } catch (error) {
        // 토큰 로딩 중 문제가 있어도 요청은 진행
        console.warn('[auth] failed to resolve access token', error)
      }
      return config
    },
    (error) => Promise.reject(error)
  )

  client.interceptors.response.use(
    (response) => response,
    async (error) => {
      const { response, config } = error
      if (response?.status === 401 && config && !config._retry) {
        // 토큰 refresh 요청 자체가 실패한 경우는 즉시 로그인 페이지로 리다이렉트
        const isRefreshRequest = typeof config.url === 'string' && config.url.includes('/api/token/refresh/')
        if (isRefreshRequest) {
          console.warn('[auth] Refresh token failed, redirecting to login')
          await authService.clearAuth()
          if (typeof window !== 'undefined') {
            window.location.href = '/login'
          }
          return Promise.reject(error)
        }

        // 공개 API 경로 목록 (로그인하지 않은 사용자도 접근 가능)
        const publicApiPaths = [
          '/api/studies/',
          '/api/exams/',
          '/api/exam/',  // 시험 관련 API (공개 시험만) - 개별 시험 조회, 문제 목록 등 포함
          '/api/tag-categories/',  // 태그 카테고리 목록 및 트리
          '/api/question-files/',  // 문제 파일 목록
          '/api/translations/'
        ]
        
        // 요청 URL이 공개 API 경로인지 확인
        const requestUrl = config.url || ''
        const method = config.method?.toLowerCase() || ''
        const isPublicApi = publicApiPaths.some(path => requestUrl.includes(path) && method === 'get')
        
        console.log('🔍 [API Interceptor] 401 에러 처리:', {
          requestUrl,
          method,
          isPublicApi,
          publicApiPaths
        })
        
        if (isPublicApi) {
          console.log('✅ 공개 API로 인식됨:', requestUrl, '- 401 에러를 그대로 반환 (리다이렉트하지 않음)')
          // 공개 API는 401 에러를 그대로 반환 (리다이렉트하지 않음)
          return Promise.reject(error)
        }
        
        // 공개 API가 아니면 토큰 갱신 시도
        console.log('⚠️ [API Interceptor] 공개 API가 아님 - 토큰 갱신 시도:', requestUrl)
        config._retry = true
        try {
          const newToken = await authService.refreshAccessToken()
          if (newToken) {
            config.headers = config.headers || {}
            config.headers.Authorization = `Bearer ${newToken}`
            return client(config)
          }
        } catch (refreshError) {
          console.log('❌ [API Interceptor] 토큰 갱신 실패 - 로그인 페이지로 리다이렉트:', requestUrl)
          await authService.clearAuth()
          if (typeof window !== 'undefined') {
            window.location.href = '/login'
          }
        }
        // 공개 API는 401 에러를 그대로 반환 (리다이렉트하지 않음)
      }
      return Promise.reject(error)
    }
  )
}

attachInterceptors(api)
attachInterceptors(apiWithLongTimeout) // 긴 타임아웃 인스턴스에도 인터셉터 적용
attachInterceptors(axios)

// 전역 사용자 프로필 캐시 (중복 호출 방지)
let userProfileCache = null
let userProfileCachePromise = null
const USER_PROFILE_CACHE_TTL = 300000 // 5분 (밀리초)

// 인증 관련 API
export const authAPI = {
  // 사용자 등록
  register: async (userData) => {
    await ensureCsrfToken()
    const response = await api.post('/api/register/', userData)
    return handleAuthResponse(response)
  },
  
  // 사용자 로그인
  login: async (credentials) => {
    await ensureCsrfToken()
    const response = await api.post('/api/login/', credentials)
    return handleAuthResponse(response)
  },
  
  // 사용자 로그아웃
  logout: async () => {
    try {
      await ensureCsrfToken()
      await api.post('/api/logout/')
    } catch (error) {
      // 세션 기반 로그아웃 실패는 무시 (JWT 기반에서는 토큰 비우기가 중요)
      console.warn('[auth] logout request failed', error?.response?.status)
    } finally {
      await authService.clearAuth()
      // 로그아웃 시 캐시 무효화
      userProfileCache = null
      userProfileCachePromise = null
    }
  },
  
  // 이메일 인증
  verifyEmail: (token) => api.get(`/api/verify-email/${token}/`),
  
  // 비밀번호 재설정
  resetPassword: (email) => api.post('/api/reset-password/', { email }),
  
  // 사용자 프로필 조회 (전역 캐시 사용, 중복 호출 방지)
  getProfile: async (forceRefresh = false) => {
    const now = Date.now()
    
    // 강제 새로고침이 아니고 캐시가 유효한 경우
    if (!forceRefresh && userProfileCache && (now - userProfileCache.timestamp) < USER_PROFILE_CACHE_TTL) {
      return { data: userProfileCache.data }
    }
    
    // 이미 진행 중인 요청이 있으면 기다림 (중복 호출 방지)
    if (userProfileCachePromise) {
      return userProfileCachePromise
    }
    
    // 새로운 요청 시작
    userProfileCachePromise = api.get('/api/user-profile/')
      .then(response => {
        // 캐시에 저장
        userProfileCache = {
          data: response.data,
          timestamp: now
        }
        userProfileCachePromise = null
        return response
      })
      .catch(error => {
        userProfileCachePromise = null
        throw error
      })
    
    return userProfileCachePromise
  },
  
  // 사용자 프로필 캐시 무효화
  invalidateProfileCache: () => {
    userProfileCache = null
    userProfileCachePromise = null
  },
  
  // 사용자 프로필 업데이트
  updateProfile: async (profileData) => {
    const response = await api.put('/api/user-profile/', profileData)
    // 프로필 업데이트 시 캐시 무효화
    userProfileCache = null
    userProfileCachePromise = null
    return response
  },
  
  // Apple OAuth 로그인
  appleLogin: async (identityToken, userInfo, language) => {
    await ensureCsrfToken()
    const response = await api.post('/api/apple-oauth/', {
      identity_token: identityToken,
      user: userInfo,
      language: language
    })
    return handleAuthResponse(response)
  }
}

// 시험 관련 API
export const examAPI = {
  // 시험 목록 조회
  getExams: (params = {}) => api.get('/api/exams/', { params }),
  
  // 시험 상세 조회
  getExam: (id) => api.get(`/api/exams/${id}/`),
  
  // 시험 생성
  createExam: (examData) => api.post('/api/exams/', examData),
  
  // 시험 수정
  updateExam: (id, examData) => api.put(`/api/exams/${id}/`, examData),
  
  // 시험 삭제
  deleteExam: (id) => api.delete(`/api/exams/${id}/`),
  
  // 시험 제출
  submitExam: (id, answers) => api.post(`/api/exams/${id}/submit/`, { answers }),
  
  // 시험 결과 조회
  getExamResult: (id) => api.get(`/api/exam-results/${id}/`),
  
  // 시험 결과 목록
  getExamResults: (params = {}) => api.get('/api/exam-results/', { params }),
  
  // 랜덤 시험 생성
  createRandomExam: (data) => api.post('/api/create-random-exam/', data),
  
  // 추천 시험 생성
  createRecommendationExam: (data) => api.post('/api/create-random-recommendation-exam/', data)
}

// 문제 관련 API
export const questionAPI = {
  // 문제 목록 조회
  getQuestions: (params = {}) => api.get('/api/questions/', { params }),
  
  // 문제 상세 조회
  getQuestion: (id) => api.get(`/api/questions/${id}/`),
  
  // 문제 생성
  createQuestion: (questionData) => api.post('/api/questions/', questionData),
  
  // 문제 수정
  updateQuestion: (id, questionData) => api.put(`/api/questions/${id}/`, questionData),
  
  // 문제 삭제
  deleteQuestion: (id) => api.delete(`/api/questions/${id}/`),
  
  // 문제 무시
  ignoreQuestion: (id) => api.post(`/api/question/${id}/ignore/`),
  
  // 문제 무시 해제
  unignoreQuestion: (id) => api.post(`/api/question/${id}/unignore/`),
  
  // 문제 무시 확인
  checkIgnored: (id) => api.get(`/api/question/${id}/check-ignored/`)
}

// 스터디 관련 API
export const studyAPI = {
  // 스터디 목록 조회
  getStudies: (params = {}) => api.get('/api/studies/', { params }),
  
  // 스터디 상세 조회
  getStudy: (id) => api.get(`/api/studies/${id}/`),
  
  // 스터디 생성
  createStudy: (studyData) => api.post('/api/studies/', studyData),
  
  // 스터디 수정
  updateStudy: (id, studyData) => api.put(`/api/studies/${id}/`, studyData),
  
  // 스터디 삭제
  deleteStudy: (id) => api.delete(`/api/studies/${id}/`),
  
  // 스터디 가입 요청
  joinStudy: (id) => api.post('/api/study-join-request/', { study_id: id }),
  
  // 스터디 멤버 조회
  getStudyMembers: (id) => api.get(`/api/studies/${id}/members/`),
  
  // 스터디 태스크 조회
  getStudyTasks: (id) => api.get(`/api/studies/${id}/tasks/`)
}

// 파일 관련 API
export const fileAPI = {
  // 파일 업로드
  uploadFile: (file, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)
    
    return api.post('/api/upload-file/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: onProgress
    })
  },
  
  // 파일 다운로드
  downloadFile: (url) => api.get(url, { responseType: 'blob' }),
  
  // 파일 삭제
  deleteFile: (id) => api.delete(`/api/files/${id}/`)
}

// 번역 관련 API
export const translationAPI = {
  // 텍스트 번역
  translateText: (text, targetLang) => api.post('/api/translate/', {
    text,
    target_language: targetLang
  }),
  
  // 다중 텍스트 번역
  translateTexts: (texts, targetLang) => api.post('/api/translate-texts/', {
    texts,
    target_language: targetLang
  })
}

// 실시간 관련 API
export const realtimeAPI = {
  // WebRTC 세션 생성
  createSession: (data) => api.post('/api/realtime/session/', data),
  
  // WebRTC 오퍼 생성
  createOffer: (sessionId, offer) => api.post(`/api/realtime/session/${sessionId}/offer/`, { offer }),
  
  // WebRTC 답변 생성
  createAnswer: (sessionId, answer) => api.post(`/api/realtime/session/${sessionId}/answer/`, { answer }),
  
  // 실시간 함수 호출
  functionCall: (data) => api.post('/api/realtime/function-call/', data)
}

export default api
export { apiWithLongTimeout, ensureCsrfToken }
