<template>
  <div id="app">
    <!-- JSON-LD 구조화된 데이터 -->
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "Organization",
      "name": "DrillQuiz",
      "description": "효율적인 퀴즈 학습을 위한 온라인 플랫폼",
      "url": "https://us.drillquiz.com",
      "logo": "https://us.drillquiz.com/favicon.ico",
      "sameAs": [
        "https://us.drillquiz.com"
      ],
      "contactPoint": {
        "@type": "ContactPoint",
        "contactType": "customer service",
        "url": "https://us.drillquiz.com"
      }
    }
    </script>
    
    <!-- 번역 로딩 중일 때 로딩 표시 -->
    <div v-if="!translationsReady" class="translation-loading-container">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading translations...</span>
      </div>
      <p class="mt-3">Loading translation data...</p>
    </div>
    
    <!-- 번역이 로드된 후에만 컨텐츠 표시 -->
    <div v-else>
      <nav class="navbar navbar-expand navbar-light bg-light px-3">
      <div class="navbar-nav me-auto">
        <router-link v-if="!isLoggedIn" :to="getServiceIntroLink()" class="nav-link service-intro-link">{{ $t('menu.serviceIntro') }}</router-link>
        <router-link v-if="isLoggedIn || !isSpecificDomain" to="/?fromHomeMenu=true" class="nav-link">{{ $t('menu.home') }}</router-link>
        <router-link to="/exam-management" class="nav-link">{{ $t('menu.exam') }}</router-link>
        <router-link v-if="showStudyMenu" to="/study-management" class="nav-link">{{ $t('menu.study') }}</router-link>
      </div>
      <div class="navbar-nav ms-auto">
        <!-- 언어 변경 드롭다운 -->
        <div class="nav-item dropdown" ref="languageDropdownContainer" @mouseenter="handleLanguageDropdownMouseEnter" @mouseleave="handleLanguageDropdownMouseLeave">
          <button 
            @click.prevent="toggleLanguageDropdown" 
            class="nav-link language-switcher-btn dropdown-toggle"
            :title="$t('common.languageSwitch')"
          >
            {{ currentLanguage === 'ko' ? 'KR' : currentLanguage === 'en' ? 'EN' : currentLanguage === 'es' ? 'ES' : currentLanguage === 'zh' ? 'ZH' : 'JA' }}
          </button>
          <ul class="dropdown-menu language-dropdown-menu" :class="{ show: showLanguageDropdown }" @click.stop @mouseenter="handleLanguageDropdownMouseEnter" @mouseleave="handleLanguageDropdownMouseLeave">
            <li>
              <a class="dropdown-item" href="#" @click.prevent="changeLanguage('en')" :class="{ active: currentLanguage === 'en' }">
                English (EN)
              </a>
            </li>
            <li>
              <a class="dropdown-item" href="#" @click.prevent="changeLanguage('es')" :class="{ active: currentLanguage === 'es' }">
                Español (ES)
              </a>
            </li>
            <li>
              <a class="dropdown-item" href="#" @click.prevent="changeLanguage('ko')" :class="{ active: currentLanguage === 'ko' }">
                한국어 (KR)
              </a>
            </li>
            <li>
              <a class="dropdown-item" href="#" @click.prevent="changeLanguage('zh')" :class="{ active: currentLanguage === 'zh' }">
                中文 (ZH)
              </a>
            </li>
            <li>
              <a class="dropdown-item" href="#" @click.prevent="changeLanguage('ja')" :class="{ active: currentLanguage === 'ja' }">
                日本語 (JA)
              </a>
            </li>
          </ul>
        </div>
        
        <router-link v-if="!isLoggedIn" to="/login" class="nav-link">{{ $t('menu.login') }}</router-link>
        
        <!-- 로그인된 사용자를 위한 드롭다운 메뉴 -->
        <div v-if="isLoggedIn" class="nav-item dropdown" ref="dropdownContainer" @mouseenter="handleDropdownMouseEnter" @mouseleave="handleDropdownMouseLeave">
          <a class="nav-link dropdown-toggle" href="#" role="button" @click.prevent="toggleDropdown">
            {{ userName }}
          </a>
          <ul class="dropdown-menu" :class="{ show: showDropdown }" @click.stop @mouseenter="handleDropdownMouseEnter" @mouseleave="handleDropdownMouseLeave">
            <li><router-link class="dropdown-item" to="/profile" @click="hideDropdown">{{ $t('menu.profile') }}</router-link></li>
            <li><router-link class="dropdown-item" to="/favorites" @click="hideDropdown">{{ $t('menu.favorite') }}</router-link></li>
            <li><hr class="dropdown-divider"></li>
            <li><a class="dropdown-item" href="#" @click.prevent="logout">{{ $t('menu.logout') }}</a></li>
          </ul>
        </div>
      </div>
    </nav>
    <div class="router-view-container">
      <!-- 모바일 웹일 때만 iOS 앱 설치 메시지 표시 -->
      <div v-if="showMobileAppInstallBanner" class="mobile-app-install-banner">
        <div class="mobile-app-install-content">
          <span class="mobile-app-install-text">{{ $t('menu.installApp') }}</span>
          <a 
            href="https://apps.apple.com/us/app/drillquiz/id6755402441" 
            target="_blank" 
            rel="noopener noreferrer"
            class="mobile-app-install-link"
          >
            <i class="fab fa-apple"></i>
          </a>
        </div>
      </div>
      <router-view/>
    </div>
    <AppFooter />
    <ChatWidget />
    </div>
  </div>
</template>

<script>
// TODO: console.log를 debugLog로 변경할 수 있는지 반드시 검토해야 함
// - 운영 환경에서 브라우저 콘솔에 로그가 보이면 안 됨
// - debugLog는 운영 환경에서 자동으로 비활성화됨
import { debugLog } from '@/utils/debugUtils'
import { isAdmin, hasStudyAdminRole } from '@/utils/permissionUtils'
import AppFooter from '@/components/Footer.vue'
import ChatWidget from '@/components/ChatWidget.vue'
import authService from '@/services/authService'
import { authAPI } from '@/services/api'

export default {
  components: {
    AppFooter,
    ChatWidget
  },
  metaInfo() {
    // 현재 언어에 따라 동적으로 메타 정보 생성
    const currentLang = this.$i18n?.locale || 'en'
    
    // 언어별 메타 정보 매핑
    const metaByLanguage = {
      'ko': {
        title: 'DrillQuiz - 퀴즈 학습 플랫폼',
        description: 'DrillQuiz는 효율적인 퀴즈 학습을 위한 온라인 플랫폼입니다. 문제 풀이, 시험 관리, 학습 진도 추적을 통해 학습 효과를 극대화하세요.',
        keywords: '퀴즈, 학습, 시험, 문제 풀이, 온라인 학습, DrillQuiz',
        ogTitle: 'DrillQuiz - 퀴즈 학습 플랫폼',
        ogDescription: 'DrillQuiz는 효율적인 퀴즈 학습을 위한 온라인 플랫폼입니다.',
        twitterTitle: 'DrillQuiz - 퀴즈 학습 플랫폼',
        twitterDescription: 'DrillQuiz는 효율적인 퀴즈 학습을 위한 온라인 플랫폼입니다.'
      },
      'en': {
        title: 'DrillQuiz - Drill, Quiz, Drill',
        description: 'DrillQuiz is an online platform for efficient quiz learning. Maximize your learning effectiveness through problem solving, exam management, and learning progress tracking.',
        keywords: 'quiz, learning, exam, problem solving, online learning, DrillQuiz',
        ogTitle: 'DrillQuiz - Quiz Learning Platform',
        ogDescription: 'DrillQuiz is an online platform for efficient quiz learning.',
        twitterTitle: 'DrillQuiz - Quiz Learning Platform',
        twitterDescription: 'DrillQuiz is an online platform for efficient quiz learning.'
      },
      'es': {
        title: 'DrillQuiz - Plataforma de Aprendizaje',
        description: 'DrillQuiz es una plataforma en línea para un aprendizaje eficiente de cuestionarios. Maximice su efectividad de aprendizaje a través de la resolución de problemas, gestión de exámenes y seguimiento del progreso del aprendizaje.',
        keywords: 'cuestionario, aprendizaje, examen, resolución de problemas, aprendizaje en línea, DrillQuiz',
        ogTitle: 'DrillQuiz - Plataforma de Aprendizaje',
        ogDescription: 'DrillQuiz es una plataforma en línea para un aprendizaje eficiente de cuestionarios.',
        twitterTitle: 'DrillQuiz - Plataforma de Aprendizaje',
        twitterDescription: 'DrillQuiz es una plataforma en línea para un aprendizaje eficiente de cuestionarios.'
      },
      'zh': {
        title: 'DrillQuiz - 测验学习平台',
        description: 'DrillQuiz是一个高效的在线测验学习平台。通过问题解答、考试管理和学习进度跟踪，最大化您的学习效果。',
        keywords: '测验, 学习, 考试, 问题解答, 在线学习, DrillQuiz',
        ogTitle: 'DrillQuiz - 测验学习平台',
        ogDescription: 'DrillQuiz是一个高效的在线测验学习平台。',
        twitterTitle: 'DrillQuiz - 测验学习平台',
        twitterDescription: 'DrillQuiz是一个高效的在线测验学习平台。'
      },
      'ja': {
        title: 'DrillQuiz - クイズ学習プラットフォーム',
        description: 'DrillQuizは効率的なクイズ学習のためのオンラインプラットフォームです。問題解決、試験管理、学習進捗追跡を通じて学習効果を最大化します。',
        keywords: 'クイズ, 学習, 試験, 問題解決, オンライン学習, DrillQuiz',
        ogTitle: 'DrillQuiz - クイズ学習プラットフォーム',
        ogDescription: 'DrillQuizは効率的なクイズ学習のためのオンラインプラットフォームです。',
        twitterTitle: 'DrillQuiz - クイズ学習プラットフォーム',
        twitterDescription: 'DrillQuizは効率的なクイズ学習のためのオンラインプラットフォームです。'
      }
    }
    
    // 현재 언어에 맞는 메타 정보 선택, 없으면 영어 기본값
    const meta = metaByLanguage[currentLang] || metaByLanguage['en']
    
    return {
      title: meta.title,
      titleTemplate: '%s | DrillQuiz',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no' },
        { 
          name: 'description', 
          content: meta.description
        },
        { 
          name: 'keywords', 
          content: meta.keywords
        },
        { name: 'author', content: 'DrillQuiz Team' },
        { name: 'robots', content: 'index, follow' },
        // Open Graph
        { 
          property: 'og:title', 
          content: meta.ogTitle
        },
        { 
          property: 'og:description', 
          content: meta.ogDescription
        },
        { property: 'og:type', content: 'website' },
        { property: 'og:url', content: 'https://us.drillquiz.com' },
        { property: 'og:image', content: '/favicon.ico' },
        { property: 'og:site_name', content: 'DrillQuiz' },
        // Twitter Card
        { name: 'twitter:card', content: 'summary' },
        { 
          name: 'twitter:title', 
          content: meta.twitterTitle
        },
        { 
          name: 'twitter:description', 
          content: meta.twitterDescription
        },
        { name: 'twitter:image', content: '/favicon.ico' }
      ],
      link: [
        { rel: 'canonical', href: this.getCanonicalUrl() }
      ]
    }
  },
  data() {
    return {
      loginState: false,
      showDropdown: false,
      showLanguageDropdown: false,
      currentUser: null,
      translationsReady: false,
      unsubscribeAuth: null,
      dropdownCloseTimer: null,
      languageDropdownCloseTimer: null
    }
  },
  computed: {
    isLoggedIn() {
      return this.loginState
    },
    isAdmin() {
      return this.loginState && isAdmin()
    },
    isStudyAdmin() {
      return this.loginState && hasStudyAdminRole()
    },
    userName() {
      // loginState가 false이면 사용자 정보를 반환하지 않음
      if (!this.loginState) {
        return this.$t('menu.user')
      }
      const cachedUser = this.currentUser || authService.getUserSync()
      if (cachedUser && cachedUser.username) {
        console.log('[App.vue] userName resolved from cached user:', cachedUser.username)
        return cachedUser.username
      }
      console.log('[App.vue] userName fallback to default label')
      return this.$t('menu.user')
    },
    currentLanguage() {
      return this.$i18n.locale || 'en'
    },
    isDevOpsDomain() {
      return typeof window !== 'undefined' && window.location && window.location.hostname && window.location.hostname.includes('devops')
    },
    isLeetCodeDomain() {
      return typeof window !== 'undefined' && window.location && window.location.hostname && window.location.hostname.includes('leetcode')
    },
    isSpecificDomain() {
      return this.isDevOpsDomain || this.isLeetCodeDomain
    },
    showStudyMenu() {
      // 세션이 없을 때는 기본적으로 표시
      if (!this.loginState) {
        return true
      }
      // 세션이 있을 때 17+ 미만이면 숨김
      const cachedUser = this.currentUser || authService.getUserSync()
      if (cachedUser && cachedUser.age_rating) {
        return cachedUser.age_rating === '17+'
      }
      // age_rating이 없으면 기본적으로 표시 (기존 사용자 호환성)
      return true
    },
    showMobileAppInstallBanner() {
      // Apple 기기(iPhone, iPad, macOS)일 때 표시
      return this.isAppleDevice()
    }
      },
    watch: {
      // 언어 변경 감지하여 메타 정보 업데이트
      '$i18n.locale': {
        handler() {
          // vue-meta가 자동으로 메타 정보를 업데이트함
          this.$meta().refresh()
        },
        immediate: true
      }
  },
  async mounted() {
    try {
      await this.$waitForI18nReady()
      this.translationsReady = true
    } catch (error) {
      debugLog('번역 초기화 대기 중 오류:', error, 'error')
      this.translationsReady = true
    }

    window.addEventListener('authStatusChanged', this.handleAuthStatusChange)
    this.unsubscribeAuth = authService.subscribe((snapshot) => {
      console.log('[App.vue] authService.subscribe snapshot', snapshot)
      this.refreshUserState(snapshot)
    })

    await this.initializeAuthState()
    await this.checkOAuthLoginSuccess()

    // 라우터 네비게이션 후 세션 확인을 위한 변수
    let lastAuthCheckTime = 0
    const AUTH_CHECK_INTERVAL = 10000 // 10초 간격으로만 확인
    let isFirstNavigation = true // 첫 번째 네비게이션 플래그
    
    this.$router.afterEach(async (to, from) => {
      this.updateFavicon()
      // 자동 스크롤 비활성화
      // this.$nextTick(() => {
      //   this.adjustScrollToNavbarBottom()
      // })
      
      // 첫 번째 네비게이션은 스킵 (초기 로드는 이미 initializeAuthState에서 처리됨)
      if (isFirstNavigation) {
        isFirstNavigation = false
        return
      }
      
      // 같은 경로로의 네비게이션은 스킵
      if (to.path === from.path) {
        return
      }
      
      // 사용자 정보가 이미 있으면 세션 확인 불필요
      if (this.loginState && this.currentUser) {
        return
      }
      
      // 너무 자주 호출되지 않도록 debounce (10초 간격)
      const now = Date.now()
      if (now - lastAuthCheckTime < AUTH_CHECK_INTERVAL) {
        return
      }
      lastAuthCheckTime = now
      
      // 라우터 네비게이션 후 인증 상태 확인 (세션 기반 인증 유지)
      // loginState가 false이거나 사용자 정보가 없을 때만 세션 상태 확인
      if (!this.loginState || !this.currentUser) {
        try {
          await this.checkAuthStatus()
        } catch (error) {
          // 에러는 무시 (인증되지 않은 상태로 유지)
          debugLog('라우터 네비게이션 후 인증 상태 확인 실패:', error, 'debug')
        }
      }
    })

    this.updateFavicon()

    // 자동 스크롤 비활성화
    // this.$nextTick(() => {
    //   this.adjustScrollToNavbarBottom()
    // })
    
    // 외부 클릭 감지를 위한 이벤트 리스너 추가
    document.addEventListener('click', this.handleOutsideClick)
    
    // iPad 감지
    debugLog('[mounted] checkIsiPad 호출 전', null, 'debug')
    this.checkIsiPad()
    debugLog('[mounted] checkIsiPad 호출 후 - body 클래스', document.body.className, 'debug')
    
    // CSS 적용 확인 (디버그 모드에서만)
    this.$nextTick(() => {
      const navbar = document.querySelector('.navbar')
      if (navbar) {
        const styles = window.getComputedStyle(navbar)
        debugLog('[mounted] navbar computed styles', {
          marginTop: styles.marginTop,
          paddingTop: styles.paddingTop,
          minHeight: styles.minHeight,
          windowInnerWidth: window.innerWidth,
          bodyClasses: document.body.className
        }, 'debug')
      }
    })
  },
  beforeDestroy() {
    // 이벤트 리스너 제거
    window.removeEventListener('authStatusChanged', this.handleAuthStatusChange)
    document.removeEventListener('click', this.handleOutsideClick)
    if (typeof this.unsubscribeAuth === 'function') {
      this.unsubscribeAuth()
    }
    // 타이머 정리
    if (this.dropdownCloseTimer) {
      clearTimeout(this.dropdownCloseTimer)
      this.dropdownCloseTimer = null
    }
    if (this.languageDropdownCloseTimer) {
      clearTimeout(this.languageDropdownCloseTimer)
      this.languageDropdownCloseTimer = null
    }
  },
  methods: {
    getCanonicalUrl() {
      // 현재 경로에 따라 canonical URL 생성
      if (typeof window === 'undefined') {
        return 'https://us.drillquiz.com'
      }
      const baseUrl = 'https://us.drillquiz.com'
      const path = this.$route ? this.$route.path : (window.location ? window.location.pathname : '/')
      // 쿼리 파라미터 제거 (canonical URL은 쿼리 파라미터 없음)
      const cleanPath = path.split('?')[0]
      // 해시 제거
      const cleanPathNoHash = cleanPath.split('#')[0]
      // 루트 경로는 기본 URL만 반환
      if (cleanPathNoHash === '/' || !cleanPathNoHash) {
        return baseUrl
      }
      return `${baseUrl}${cleanPathNoHash}`
    },
    refreshUserState(snapshot) {
      console.log('[App.vue] refreshUserState invoked with snapshot:', snapshot)
      const authSnapshot = snapshot || authService.getAuthSnapshot()
      console.log('[App.vue] resolved authSnapshot:', authSnapshot)
      
      // 사용자 정보가 있으면 설정
      if (authSnapshot?.user) {
        this.currentUser = authSnapshot.user
        this.loginState = true
        return
      }
      
      // 사용자 정보가 없지만 현재 사용자 정보가 이미 있으면 유지
      // (세션 기반 인증에서는 authService가 accessToken 기반으로만 확인하므로
      //  사용자 정보가 없을 수 있지만 실제로는 세션이 유효할 수 있음)
      if (!authSnapshot?.isAuthenticated && this.currentUser && this.loginState) {
        // 기존 사용자 정보 유지 (세션 기반 인증)
        return
      }
      
      // 인증 상태가 false이고 사용자 정보도 없으면 초기화
      if (!authSnapshot?.isAuthenticated) {
        this.loginState = false
        this.currentUser = null
      } else {
        this.loginState = true
      }
    },
    async initializeAuthState() {
      try {
        const snapshot = authService.getAuthSnapshot()
        if (snapshot) {
          this.refreshUserState(snapshot)
        }

        const accessToken = await authService.getAccessToken()
        this.loginState = !!accessToken

        // accessToken이 없어도 세션 기반 인증을 확인 (구글 인증 등)
        if (!this.loginState) {
          try {
            const statusResponse = await this.$http.get('/api/auth/status/')
            if (statusResponse.data.authenticated) {
              this.loginState = true
              const mergedUser = {
                ...(this.currentUser || {}),
                ...(statusResponse.data.user || {})
              }
              this.currentUser = mergedUser
              await authService.storeAuthResult({ user: mergedUser })
              return
            }
          } catch (error) {
            // 세션 확인 실패는 무시 (인증되지 않은 상태로 처리)
            // 400 Bad Request는 정상적인 경우 (인증되지 않은 상태)
            if (error.response && error.response.status === 400) {
              // 조용히 무시
            } else {
              debugLog('세션 기반 인증 확인 실패:', error, 'debug')
            }
          }
          
          this.currentUser = null
          return
        }

        const cachedUser = authService.getUserSync()
        if (cachedUser) {
          this.currentUser = cachedUser
          return
        }

        const storedUser = await authService.getUser()
        if (storedUser) {
          this.currentUser = storedUser
          return
        }

        const baseUser = this.currentUser || cachedUser
        const response = await authAPI.getProfile()
        const mergedUser = {
          ...(baseUser || {}),
          ...(response.data || {})
        }
        this.currentUser = mergedUser
        await authService.storeAuthResult({ user: mergedUser })
      } catch (error) {
        debugLog('초기 사용자 정보 로딩 실패:', error, 'error')
        this.loginState = false
        this.currentUser = null
      }
    },
    
    async checkOAuthLoginSuccess() {
      // URL에서 OAuth 로그인 성공 파라미터 확인
      const urlParams = new URLSearchParams(window.location.search)
      const loginSuccess = urlParams.get('login')
      const email = urlParams.get('email')
      
      if (loginSuccess === 'success' && email) {
        try {
          // 구글 인증은 세션 기반이므로 세션 상태를 확인해야 함
          await this.checkAuthStatus()
          const newUrl = window.location.pathname
          window.history.replaceState({}, '', newUrl)
        } catch (error) {
          debugLog('OAuth 로그인 성공 후 인증 상태 확인 실패:', error, 'error')
        }
      }
    },
    
    async checkAuthStatus() {
      try {
        console.log('🔍 [App.vue] checkAuthStatus 호출됨')
        console.log('🔍 [App.vue] status API 호출 시작: /api/auth/status/')
        const response = await this.$http.get('/api/auth/status/')
        console.log('🔍 [App.vue] status API 응답:', response.status)
        
        this.loginState = response.data.authenticated
        const mergedUser = {
          ...(this.currentUser || {}),
          ...(response.data.user || {})
        }
        this.currentUser = mergedUser
        if (response.data.authenticated && response.data.user) {
          await authService.storeAuthResult({ user: mergedUser })
        }
        return response.data
      } catch (error) {
        // 400 Bad Request는 인증되지 않은 상태로 정상 처리
        if (error.response && error.response.status === 400) {
          debugLog('인증 상태 확인: 인증되지 않은 상태 (400)', null, 'debug')
        } else {
          debugLog('인증 상태 확인 실패:', error, 'error')
        }
      }
      return { authenticated: false, user: null }
    },
    
    async handleAuthStatusChange(event) {
      const { authenticated, user } = event.detail
      this.loginState = authenticated
      const mergedUser = {
        ...(this.currentUser || {}),
        ...(user || {})
      }
      this.currentUser = mergedUser
      console.log('[App.vue] handleAuthStatusChange', { authenticated, user, mergedUser })
      
      if (authenticated && user) {
        await authService.storeAuthResult({ user: mergedUser })
      } else {
        await authService.clearAuth()
      }
    },
    
    async applyUserLanguage() {
      // 로그인된 사용자인 경우 프로필에서 언어 설정 가져오기
      if (this.loginState) {
        try {
          console.log('🔍 [App.vue] applyUserLanguage 시작 - 현재 언어:', this.$i18n.locale)
          // 전역 캐시를 사용하는 authAPI.getProfile 사용 (중복 호출 방지)
          const { authAPI } = await import('@/services/api')
          console.log('🔍 [App.vue] user-profile API 호출 시작: /api/user-profile/ (전역 캐시 사용)')
          const response = await authAPI.getProfile()
          console.log('🔍 [App.vue] user-profile API 응답:', response.status || 'cached')
          const userLanguage = response.data.language || 'en'
          console.log('🔍 사용자 프로필 언어:', userLanguage, '현재 언어:', this.$i18n.locale)
          
          // 현재 언어와 다르면 변경
          if (userLanguage !== this.$i18n.locale) {
            console.log('🔍 언어 변경 시작:', this.$i18n.locale, '→', userLanguage)
            await this.$changeLanguage(userLanguage)
            console.log('🔍 언어 변경 완료:', this.$i18n.locale)
          } else {
            console.log('🔍 언어 변경 불필요 - 이미 동일함')
          }
        } catch (error) {
          console.error('🔍 applyUserLanguage 오류:', error)
        }
      }
    },
    toggleDropdown() {
      this.showDropdown = !this.showDropdown
    },
    toggleLanguageDropdown() {
      this.showLanguageDropdown = !this.showLanguageDropdown
    },
    hideLanguageDropdown() {
      // 타이머 정리
      if (this.languageDropdownCloseTimer) {
        clearTimeout(this.languageDropdownCloseTimer)
        this.languageDropdownCloseTimer = null
      }
      this.showLanguageDropdown = false
    },
    async changeLanguage(newLanguage) {
      // 이미 선택된 언어면 변경하지 않음
      if (newLanguage === this.currentLanguage) {
        this.hideLanguageDropdown()
        return
      }
      
      try {
        // 로그인된 사용자인 경우에만 DB에 저장 및 새로운 토큰 받기
        if (this.isLoggedIn) {
          const response = await this.$http.post('/api/change-language/', {
            language: newLanguage
          })
          
          // 새로운 JWT 토큰이 있으면 저장 (언어 정보 반영)
          if (response.data && response.data.tokens) {
            await authService.storeAuthResult({
              access: response.data.tokens.access,
              refresh: response.data.tokens.refresh,
              access_expires_in: response.data.tokens.access_expires_in,
              refresh_expires_in: response.data.tokens.refresh_expires_in
            })
            debugLog('✅ 언어 변경 후 새로운 토큰 저장 완료')
          }
        }
        
        this.translationsReady = false
        // Vue i18n 언어 변경
        await this.$changeLanguage(newLanguage)
        this.translationsReady = true
        
        // 메타 정보 업데이트 (vue-meta가 자동으로 처리)
        // 각 페이지의 watcher가 이미 $meta().refresh()를 호출하므로 중복 호출 방지
        // 단, watcher가 없는 페이지를 위해 안전하게 호출
        this.$nextTick(() => {
          this.$meta().refresh()
        })
        
        // 언어 드롭다운 닫기
        this.hideLanguageDropdown()
        
        // 리프레시 없이 언어 변경 완료
        // Vue의 반응성 시스템을 통해 $t() 함수가 자동으로 업데이트됨
        // 필요한 컴포넌트들은 $i18n.locale watcher를 통해 데이터를 다시 로드함
        debugLog('✅ 언어 변경 완료 (리프레시 없음):', newLanguage)
      } catch (error) {
        debugLog('언어 변경 실패:', error, 'error')
        // DB 저장 실패해도 프론트엔드 언어는 변경
        await this.$changeLanguage(newLanguage)
        this.translationsReady = true
        
        this.$nextTick(() => {
          this.$meta().refresh()
        })
        
        this.hideLanguageDropdown()
        
        debugLog('✅ 언어 변경 완료 (리프레시 없음, 에러 처리):', newLanguage)
      }
    },
    hideDropdown() {
      // 타이머 정리
      if (this.dropdownCloseTimer) {
        clearTimeout(this.dropdownCloseTimer)
        this.dropdownCloseTimer = null
      }
      this.showDropdown = false
    },
    handleDropdownMouseEnter() {
      // 마우스가 드롭다운 영역으로 들어오면 타이머 취소
      if (this.dropdownCloseTimer) {
        clearTimeout(this.dropdownCloseTimer)
        this.dropdownCloseTimer = null
      }
    },
    handleDropdownMouseLeave(event) {
      // 드롭다운이 열려있지 않으면 무시
      if (!this.showDropdown) {
        return
      }
      
      // relatedTarget이 드롭다운 컨테이너나 메뉴 내부인지 확인
      const dropdownContainer = this.$refs.dropdownContainer
      if (dropdownContainer && event.relatedTarget) {
        // 드롭다운 컨테이너나 그 하위 요소로 이동하는 경우 무시
        if (dropdownContainer.contains(event.relatedTarget)) {
          return
        }
      }
      
      // 드롭다운 컨테이너 밖으로 나가는 경우 약간의 지연 후 닫기
      this.dropdownCloseTimer = setTimeout(() => {
        this.showDropdown = false
        this.dropdownCloseTimer = null
      }, 200) // 200ms 지연으로 드롭다운 메뉴로 이동할 시간 제공
    },
    handleLanguageDropdownMouseEnter() {
      // 마우스가 언어 드롭다운 영역으로 들어오면 타이머 취소
      if (this.languageDropdownCloseTimer) {
        clearTimeout(this.languageDropdownCloseTimer)
        this.languageDropdownCloseTimer = null
      }
    },
    handleLanguageDropdownMouseLeave(event) {
      // 언어 드롭다운이 열려있지 않으면 무시
      if (!this.showLanguageDropdown) {
        return
      }
      
      // relatedTarget이 언어 드롭다운 컨테이너나 메뉴 내부인지 확인
      const languageDropdownContainer = this.$refs.languageDropdownContainer
      if (languageDropdownContainer && event.relatedTarget) {
        // 언어 드롭다운 컨테이너나 그 하위 요소로 이동하는 경우 무시
        if (languageDropdownContainer.contains(event.relatedTarget)) {
          return
        }
      }
      
      // 언어 드롭다운 컨테이너 밖으로 나가는 경우 약간의 지연 후 닫기
      this.languageDropdownCloseTimer = setTimeout(() => {
        this.showLanguageDropdown = false
        this.languageDropdownCloseTimer = null
      }, 200) // 200ms 지연으로 드롭다운 메뉴로 이동할 시간 제공
    },
    
    getServiceIntroLink() {
      // 특정 도메인인 경우 해당 도메인 페이지, 그 외에는 service-introduction
      if (this.isDevOpsDomain) {
        return '/devops-interview'
      } else {
        return '/service-introduction'
      }
    },
    handleOutsideClick(event) {
      // 드롭다운 컨테이너나 드롭다운 메뉴 내부 클릭인지 확인
      const dropdownContainer = this.$refs.dropdownContainer
      if (dropdownContainer && dropdownContainer.contains(event.target)) {
        return
      }
      
      // 언어 드롭다운 컨테이너 확인
      const languageDropdownContainer = this.$refs.languageDropdownContainer
      if (languageDropdownContainer && languageDropdownContainer.contains(event.target)) {
        return
      }
      
      // 외부 클릭이면 드롭다운 닫기
      if (this.showDropdown) {
        this.showDropdown = false
      }
      if (this.showLanguageDropdown) {
        this.showLanguageDropdown = false
      }
    },
    async logout() {
      // 즉시 UI 업데이트 (백엔드 응답을 기다리지 않음)
      this.loginState = false
      this.currentUser = null
      
      // authService의 인증 정보 즉시 초기화
      await authService.clearAuth()
      
      sessionStorage.clear()
      
      this.$root.$emit('clearAllFilters');

      // 백엔드 로그아웃 요청은 백그라운드에서 실행 (응답 기다리지 않음)
      authAPI.logout().catch(error => {
        debugLog('로그아웃 요청 실패 (무시됨):', error, 'warn')
      })
      
      // 즉시 로그인 페이지로 이동
      this.$router.push('/login').catch(err => {
        if (err.name !== 'NavigationDuplicated') {
          // NavigationDuplicated가 아닌 다른 오류는 다시 던짐
          throw err
        }
        // 중복 네비게이션 오류는 무시하고 페이지 새로고침
        window.location.reload()
      })
    },
    updateFavicon() {
      // 웹 환경에서는 항상 favicon 업데이트

      const currentPath = this.$route.path
      const isFavoritesPage = currentPath.includes('/favorites')
      const timestamp = new Date().getTime() // 캐시 방지
      
      // 기존 favicon 링크들 제거
      const existingLinks = document.querySelectorAll("link[rel*='icon']")
      existingLinks.forEach(link => link.remove())
      
      // 새로운 favicon 링크 생성
      const link = document.createElement('link')
      link.type = 'image/x-icon'
      link.rel = 'shortcut icon'
      
      if (isFavoritesPage) {
        link.href = `/favicon-favorite.ico?t=${timestamp}`
      } else {
        link.href = `/favicon.ico?t=${timestamp}`
      }
      
      document.head.appendChild(link)
    },
    
    adjustScrollToNavbarBottom() {
      // 모바일 디바이스에서만 실행
      if (!this.isMobileDevice()) {
        return
      }
      
      // navbar 요소 찾기
      const navbar = document.querySelector('.navbar')
      if (!navbar) {
        return
      }
      
      // navbar의 bottom 위치 계산
      const navbarRect = navbar.getBoundingClientRect()
      const navbarBottom = navbarRect.bottom
      
      // 현재 스크롤 위치에서 navbar bottom이 화면 top에 오도록 조정
      const currentScrollTop = window.pageYOffset || document.documentElement.scrollTop
      const targetScrollTop = currentScrollTop + navbarBottom
      
      // 부드러운 스크롤로 이동
      window.scrollTo({
        top: targetScrollTop,
        behavior: 'smooth'
      })
      

    },
    
    isMobileDevice() {
      // 모바일 디바이스 감지
      const userAgent = navigator.userAgent || navigator.vendor || window.opera
      const isMobile = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent.toLowerCase())
      
      // 화면 크기로도 모바일 판단 (768px 이하)
      const isSmallScreen = window.innerWidth <= 768
      
      return isMobile || isSmallScreen
    },
    isAppleDevice() {
      // Apple 기기 감지 (iPhone, iPad, macOS)
      if (typeof navigator === 'undefined') {
        return false
      }
      const userAgent = navigator.userAgent || navigator.vendor || window.opera || ''
      const platform = navigator.platform || ''
      
      // macOS 감지
      const isMacOS = /Mac|MacIntel|MacPPC|Mac68K/i.test(platform) || /Mac OS X/i.test(userAgent)
      
      // iOS 감지 (iPhone, iPad, iPod)
      const isIOS = /iPhone|iPad|iPod/i.test(userAgent) || /iPhone|iPad|iPod/i.test(platform)
      
      return isMacOS || isIOS
    },
    
    
    checkIsiPad() {
      debugLog('[checkIsiPad] 시작', null, 'debug')
      // iPad 감지
      if (typeof navigator !== 'undefined') {
        const userAgent = navigator.userAgent || ''
        const platform = navigator.platform || ''
        const maxTouchPoints = navigator.maxTouchPoints || 0
        
        debugLog('[checkIsiPad] userAgent', userAgent, 'debug')
        debugLog('[checkIsiPad] platform', platform, 'debug')
        debugLog('[checkIsiPad] maxTouchPoints', maxTouchPoints, 'debug')
        
        const isiPadByUA = /iPad/i.test(userAgent)
        const isiPadByPlatform = platform === 'MacIntel' && maxTouchPoints > 1
        const isiPad = isiPadByUA || isiPadByPlatform
        
        debugLog('[checkIsiPad] isiPadByUA', isiPadByUA, 'debug')
        debugLog('[checkIsiPad] isiPadByPlatform', { isiPadByPlatform, platform: platform === 'MacIntel', maxTouchPoints: maxTouchPoints > 1 }, 'debug')
        debugLog('[checkIsiPad] 최종 isiPad', isiPad, 'debug')
        
        if (isiPad) {
          document.body.classList.add('is-ipad')
          debugLog('[checkIsiPad] is-ipad 클래스 추가됨', null, 'debug')
        } else {
          document.body.classList.remove('is-ipad')
          debugLog('[checkIsiPad] is-ipad 클래스 제거됨', null, 'debug')
        }
        
        debugLog('[checkIsiPad] 최종 body 클래스', document.body.className, 'debug')
      } else {
        debugLog('[checkIsiPad] navigator 객체 없음', null, 'debug')
      }
    }
  }
}
</script>

<style>
/* 모바일 및 태블릿 디바이스에서 상단 여백 추가 - Safe Area 기반 */
/* iPhone 처리 (768px 이하) */
@media (max-width: 768px) {
  #app {
    padding-top: 0; /* navbar에 직접 적용하므로 제거 */
    padding-bottom: 0; /* 하단 여백은 footer에서 처리 */
  }
  
  /* 모바일에서 navbar 상단 고정 */
  nav.navbar,
  .navbar.navbar-expand,
  .navbar.navbar-light {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    width: 100% !important;
    z-index: 1030 !important; /* Bootstrap navbar 기본 z-index */
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important; /* 고정 시 그림자 추가 */
    background-color: #f8f9fa !important; /* Bootstrap bg-light 색상 */
  }
  
  /* navbar가 fixed이므로 콘텐츠 영역에 상단 여백 추가 */
  .router-view-container {
    /* 기본값: navbar 높이만큼 (5px 여유 공간 제거) */
    padding-top: 51px !important;
    margin-top: 0 !important;
  }
  
  /* navbar 아래 첫 번째 요소에도 여백 추가 (이중 보험) */
  .router-view-container > *:first-child {
    margin-top: 0 !important;
  }
  
  /* Capacitor 네이티브 앱 환경 - iPhone */
  body.capacitor-native:not(.is-ipad) .navbar {
    min-height: 56px;
    padding-top: 44px !important; /* iPhone Safe area 고려한 상단 여백 */
  }
  
  /* Capacitor 네이티브 앱 환경 - iPhone의 router-view-container */
  /* navbar 높이(56px) + safe area(44px) - 5px = 95px */
  body.capacitor-native:not(.is-ipad) .router-view-container {
    padding-top: 95px !important; /* navbar 높이 + safe area - 5px */
  }
  
  /* 웹 환경에서는 작은 여백만 적용 */
  body:not(.capacitor-native) .navbar {
    padding-top: 7px !important;
  }
  
  /* 웹 환경(비 iOS 앱)에서 router-view-container */
  body:not(.capacitor-native) .router-view-container {
    padding-top: 56px !important;
    margin-top: 0 !important;
  }
  
  /* 모바일에서 서비스 소개 링크 숨김 */
  .service-intro-link {
    display: none !important;
  }
}

/* iPad 처리 (769px 이상, 태블릿 크기) */
/* iPad는 다양한 크기를 가지므로 1024px 제한 제거 */
@media (min-width: 769px) and (max-width: 1024px) {
  #app {
    padding-top: 0;
    padding-bottom: 0;
  }
  
  /* iPad에서 navbar 상단 고정 */
  nav.navbar,
  .navbar.navbar-expand,
  .navbar.navbar-light {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    width: 100% !important;
    z-index: 1030 !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
    background-color: #f8f9fa !important;
  }
  
  /* navbar가 fixed이므로 콘텐츠 영역에 상단 여백 추가 */
  .router-view-container {
    padding-top: 51px !important;
    margin-top: 0 !important;
  }
  
  /* Capacitor 네이티브 앱 환경 - iPad */
  body.capacitor-native.is-ipad .navbar {
    min-height: 56px;
    padding-top: 32px !important; /* iPad Safe area 고려한 상단 여백 (27px + 5px) */
  }
  
  /* 웹 환경 - iPad (웹뷰 포함) */
  body:not(.capacitor-native).is-ipad .navbar {
    min-height: 56px;
    padding-top: 32px !important; /* iPad 웹뷰에서도 동일한 여백 적용 (27px + 5px) */
  }
}

/* 데스크톱 CSS는 위의 iPad 미디어 쿼리와 중복되므로 제거됨 */

.navbar .navbar-nav .nav-item .language-switcher-btn {
  background: rgba(102, 126, 234, 0.3) !important;
  border: none;
  width: 40px;
  height: 40px;
  padding: 0;
  color: #6c757d;
  font-weight: 500;
  font-size: 70% !important;
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.navbar .navbar-nav .nav-item .language-switcher-btn.dropdown-toggle::after {
  display: none;
}

.language-dropdown-menu {
  position: absolute !important;
  top: 100% !important;
  right: 0 !important;
  z-index: 2200 !important; /* 최상위 레이어 (예: 로딩 오버레이) */
  display: none;
  min-width: 10rem;
  padding: 0.5rem 0;
  margin: 0.125rem 0 0;
  font-size: 1rem;
  color: #212529;
  text-align: left;
  list-style: none;
  background-color: #fff;
  background-clip: padding-box;
  border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 0.375rem;
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
}

.language-dropdown-menu.show {
  display: block !important;
}

.language-dropdown-menu .dropdown-item {
  display: block;
  width: 100%;
  padding: 0.5rem 1rem;
  clear: both;
  font-weight: 400;
  color: #212529;
  text-align: inherit;
  text-decoration: none;
  white-space: nowrap;
  background-color: transparent;
  border: 0;
  cursor: pointer;
}

.language-dropdown-menu .dropdown-item:hover {
  color: #1e2125;
  background-color: #e9ecef;
}

.language-dropdown-menu .dropdown-item.active {
  color: #fff;
  background-color: #667eea;
}

.navbar .navbar-nav .nav-item:has(.language-switcher-btn) {
  display: flex;
  align-items: center;
}

.navbar .navbar-nav .nav-item .language-switcher-btn:hover {
  color: #495057;
  background-color: rgba(102, 126, 234, 0.4) !important;
}

.navbar .navbar-nav .nav-item .language-switcher-btn:focus {
  outline: none;
  box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
}

.dropdown-menu.show {
  display: block !important;
  z-index: 2200 !important; /* 최상위 레이어 (예: 로딩 오버레이) */
}

.dropdown-menu {
  position: absolute !important;
  top: 100% !important;
  right: 0 !important;
  z-index: 2200 !important; /* 최상위 레이어 (예: 로딩 오버레이) */
  display: none;
  min-width: 10rem;
  padding: 0.5rem 0;
  margin: 0.125rem 0 0;
  font-size: 1rem;
  color: #212529;
  text-align: left;
  list-style: none;
  background-color: #fff;
  background-clip: padding-box;
  border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 0.375rem;
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
}

.dropdown-item {
  display: block;
  width: 100%;
  padding: 0.25rem 1rem;
  clear: both;
  font-weight: 400;
  color: #212529;
  text-align: inherit;
  text-decoration: none;
  white-space: nowrap;
  background-color: transparent;
  border: 0;
}

.dropdown-item:hover {
  color: #1e2125;
  background-color: #e9ecef;
}

.dropdown-divider {
  height: 0;
  margin: 0.5rem 0;
  overflow: hidden;
  border-top: 1px solid rgba(0, 0, 0, 0.15);
}

/* 전역 문제 수 정보 스타일 */
.question-count-info .count-label {
  color: #6c757d !important;
  font-weight: 500 !important;
}

.question-count-info .count-value {
  color: #495057 !important;
  font-weight: 600 !important;
  min-width: 20px !important;
  text-align: center !important;
}

.question-count-info .count-value.selected {
  color: #007bff !important;
  font-weight: 700 !important;
}

.question-count-info .count-separator {
  color: #dee2e6 !important;
  font-weight: 300 !important;
  margin: 0 4px !important;
}

@media (max-width: 576px) {
  .container-fluid {
    padding-left: 0px !important;
    padding-right: 0px !important;
  }
  
  .card, .table-responsive, .study-management-wrapper {
    margin-left: 0 !important;
    margin-right: 0 !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    max-width: 100% !important;
  }
  
  .card {
    padding: 8px !important;
    margin-bottom: 10px !important;
  }
  
  .card-body {
    padding: 12px !important;
  }
  
  .table {
    font-size: 0.9rem;
  }
  
  .table td, .table th {
    padding: 8px 4px !important;
  }
  
  .btn-group .btn {
    min-width: 60px;
    white-space: nowrap;
    font-size: 0.8rem;
    padding: 4px 8px;
  }
  
  .btn {
    white-space: nowrap;
    min-width: 50px;
  }
  
  .form-control, .form-select {
    font-size: 0.9rem;
  }
  
  .alert {
    padding: 8px 12px;
    margin-bottom: 10px;
  }
  
  .jumbotron {
    padding: 1rem !important;
  }
  
  .display-4 {
    font-size: 2rem;
  }
  
  .lead {
    font-size: 1rem;
  }
}

/* 일반적인 여백 조정 */
.card {
  margin-bottom: 1rem;
}

.table-responsive {
  margin-bottom: 1rem;
}

.btn-group {
  margin-bottom: 0.5rem;
}

.form-group {
  margin-bottom: 1rem;
}

.alert {
  margin-bottom: 1rem;
}
#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.router-view-container {
  flex: 1;
  min-height: 0; /* flexbox에서 중요한 설정 */
}

/* 번역 로딩 컨테이너 - 화면 중앙에 배치 */
.translation-loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  text-align: center;
  padding: 2rem;
  /* navbar가 fixed이므로 상단 패딩 추가 (모바일 대응) */
  padding-top: calc(51px + 2rem);
}

@media (min-width: 769px) {
  .translation-loading-container {
    padding-top: calc(51px + 2rem);
  }
}

.translation-loading-container .spinner-border {
  width: 3rem;
  height: 3rem;
}

.translation-loading-container p {
  margin-top: 1rem;
  font-size: 1.1rem;
  color: #495057;
}

/* 모바일에서 router-view-container에 상단 여백 추가 - navbar가 fixed이므로 여백 필요 */
/* 위의 @media (max-width: 768px) 블록에서 이미 padding-top: 70px이 설정되어 있음 */

/* 모바일 앱 설치 배너 스타일 */
.mobile-app-install-banner {
  background-color: lightgray;
  border-bottom: 1px solid #dee2e6;
  padding-top: 3px;
  padding-bottom: 2px;
  padding-left: 16px;
  padding-right: 16px;
  text-align: center;
  width: 100%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.mobile-app-install-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
  padding: 0 4px;
}

.mobile-app-install-text {
  color: #495057;
  font-size: 13px;
  font-weight: 500;
  line-height: 1.4;
  text-align: center;
}

.mobile-app-install-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px 10px;
  background-color: #007bff;
  color: #ffffff;
  text-decoration: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  transition: background-color 0.2s ease;
  min-width: 36px;
  flex-shrink: 0;
}

.mobile-app-install-link:hover {
  background-color: #0056b3;
  color: #ffffff;
  text-decoration: none;
}

.mobile-app-install-link i {
  font-size: 16px;
}

/* 작은 화면에서 텍스트 크기 조절 */
@media (max-width: 360px) {
  .mobile-app-install-text {
    font-size: 12px;
  }
  
  .mobile-app-install-content {
    gap: 6px;
    padding: 0 2px;
  }
  
  .mobile-app-install-link {
    padding: 5px 8px;
    min-width: 32px;
  }
  
  .mobile-app-install-link i {
    font-size: 14px;
  }
}

/* Apple 기기가 아닌 데스크톱에서는 숨김 (CSS로는 Apple 기기 감지 불가하므로 JavaScript에서 처리) */

/* Footer가 정확히 하단에 붙도록 설정 */
.footer {
  margin-top: auto;
}

/* 기본 마진과 패딩 제거 */
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
}

/* iOS 웹뷰 확대 방지 */
html {
  -webkit-text-size-adjust: 100%;
  text-size-adjust: 100%;
}

/* iOS 입력 필드 자동 확대 방지 - 모든 입력 필드는 최소 16px */
input[type="text"],
input[type="email"],
input[type="password"],
input[type="number"],
input[type="tel"],
input[type="url"],
input[type="search"],
input[type="date"],
input[type="time"],
input[type="datetime-local"],
textarea,
select {
  font-size: 16px !important;
}

@media (max-width: 768px) {
  input[type="text"],
  input[type="email"],
  input[type="password"],
  input[type="number"],
  input[type="tel"],
  input[type="url"],
  input[type="search"],
  input[type="date"],
  input[type="time"],
  input[type="datetime-local"],
  textarea,
  select {
    font-size: 16px !important;
  }
}
</style> 