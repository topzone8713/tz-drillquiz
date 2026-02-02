import Vue from 'vue'
import VueI18n from 'vue-i18n'
import axios from 'axios'
import { debugLog } from './utils/debugUtils'
import { apiBaseURL } from './config/apiConfig'
import { replaceDrillQuizName } from './utils/domainUtils'

if (!axios.defaults.baseURL) {
  axios.defaults.baseURL = apiBaseURL
}

axios.defaults.withCredentials = true

Vue.use(VueI18n)

// 기본 언어 설정
const defaultLanguage = 'en'

// 환경 확인
const isProduction = process.env.NODE_ENV === 'production'

// i18n 인스턴스 생성
const i18n = new VueI18n({
  locale: defaultLanguage,
  fallbackLocale: defaultLanguage,
  messages: {
    ko: {},
    en: {},
    es: {},
    zh: {},
    ja: {}
  },
  // DevOps 도메인에서 "DrillQuiz"를 "DrillQuiz DevOps"로 변환
  postTranslation: (str) => {
    return replaceDrillQuizName(str)
  }
})

function mergeFlatMessages(existingMessages, flatMessages) {
  const merged = { ...existingMessages }

  Object.entries(flatMessages || {}).forEach(([flatKey, value]) => {
    if (typeof flatKey !== 'string') {
      return
    }

    const keys = flatKey.split('.')
    if (!keys.length) {
      return
    }

    let current = merged
    keys.forEach((segment, index) => {
      if (index === keys.length - 1) {
        current[segment] = value
      } else {
        if (!current[segment] || typeof current[segment] !== 'object') {
          current[segment] = {}
        }
        current = current[segment]
      }
    })
  })

  return merged
}

// Django에서 번역 데이터를 가져오는 함수
async function loadTranslations(language) {
  try {
    if (!isProduction) {
      debugLog(`🔄 ${language} 번역 데이터 로드 시작...`)
      debugLog('🔍 loadTranslations 호출됨 - 요청 언어:', language)
    }
    const requestUrl = `/api/translations/?lang=${language}`
    debugLog(`[i18n] Fetching translations: ${requestUrl} (lang=${language})`)
    const response = await axios.get(requestUrl)
    debugLog('[i18n] Translation API response:', {
      status: response.status,
      language,
      keys: Object.keys(response.data?.translations || {}).length
    })
    if (!isProduction) {
      debugLog('🔍 번역 API 응답 - 요청 URL:', requestUrl)
    }
    const translations = response.data?.translations || {}
    
    if (!isProduction) {
      debugLog(`📦 ${language} 번역 데이터 응답:`, response.data)
    }
    
    // translations가 유효한 객체인지 확인
    if (translations && typeof translations === 'object') {
      // 기존 번역 데이터 확인
      const existingMessages = i18n.getLocaleMessage(language)

      // 평탄화된 키를 중첩 구조로 변환하면서 병합
      const mergedMessages = mergeFlatMessages(existingMessages, translations)
      i18n.setLocaleMessage(language, mergedMessages)
      
      if (!isProduction) {
        debugLog(`✅ ${language} 번역 데이터 로드 완료:`, Object.keys(mergedMessages).length, '개 키')
      }
      return mergedMessages
    } else {
      debugLog(`❌ ${language} 번역 데이터가 유효하지 않습니다:`, translations, 'error')
      return {}
    }
  } catch (error) {
    debugLog(`❌ ${language} 번역 데이터 로드 실패:`, error, 'error')
    return {}
  }
}

// 언어 변경 함수
async function changeLanguage(language) {
  try {
    if (!isProduction) {
      debugLog(`🔄 언어 변경 시작: ${language}`)
    }
    
    // 번역 데이터가 없으면 로드
    const currentMessages = i18n.getLocaleMessage(language)
    const hasTranslations = currentMessages && Object.keys(currentMessages).length > 0
    
    if (!isProduction) {
      debugLog(`📋 ${language} 번역 데이터 상태:`, hasTranslations ? '로드됨' : '로드 필요')
    }
    
    if (!hasTranslations) {
      await loadTranslations(language)
    }
    
    // 언어 변경
    i18n.locale = language
    
    // localStorage에 언어 설정 저장
    localStorage.setItem('language', language)
    
    if (!isProduction) {
      debugLog(`✅ 언어 변경 완료: ${language}`)
    }
    return true
  } catch (error) {
    debugLog(`❌ 언어 변경 실패:`, error, 'error')
    return false
  }
}

// 초기 언어 설정
async function initializeLanguage() {
  try {
    // 브라우저 언어 감지
    const browserLanguage = navigator.language || navigator.userLanguage
    let detectedLanguage = defaultLanguage

    if (browserLanguage.startsWith('ko')) {
      detectedLanguage = 'ko'
    } else if (browserLanguage.startsWith('es')) {
      detectedLanguage = 'es'
    } else if (browserLanguage.startsWith('zh')) {
      detectedLanguage = 'zh'
    } else if (browserLanguage.startsWith('ja')) {
      detectedLanguage = 'ja'
    } else {
      detectedLanguage = 'en'  // 기본값을 영어로 설정
    }

    // localStorage에서 저장된 언어 가져오기 (없으면 브라우저 언어 사용)
    const savedLanguage = localStorage.getItem('language') || detectedLanguage

    // 언어 변경
    await changeLanguage(savedLanguage)
    
    if (!isProduction) {
      debugLog('🌐 언어 설정 완료:', {
        browserLanguage,
        detectedLanguage,
        savedLanguage,
        currentLocale: i18n.locale
      })
    }
  } catch (error) {
    debugLog('초기 언어 설정 실패:', error, 'error')
    // 오류 발생 시 기본 언어로 설정
    i18n.locale = defaultLanguage
    localStorage.setItem('language', defaultLanguage)
  }
}

// 전역 함수로 등록
Vue.prototype.$changeLanguage = changeLanguage
Vue.prototype.$loadTranslations = loadTranslations

// 초기화 실행
const initializeLanguagePromise = initializeLanguage()

Vue.prototype.$waitForI18nReady = () => initializeLanguagePromise

// 번역 로딩 상태 확인 함수
function isTranslationsLoaded(language) {
  const messages = i18n.getLocaleMessage(language)
  return messages && typeof messages === 'object' && Object.keys(messages).length > 0
}

// 전역 함수로 등록
Vue.prototype.$isTranslationsLoaded = isTranslationsLoaded

export const i18nReady = initializeLanguagePromise

export default i18n 