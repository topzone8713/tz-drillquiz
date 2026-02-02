<template>
  <div class="login-modern">
    <!-- JSON-LD 구조화된 데이터 -->
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "WebPage",
      "name": "DrillQuiz 로그인",
      "description": "퀴즈 학습 플랫폼에 로그인하여 개인화된 학습 경험을 시작하세요",
      "url": "https://us.drillquiz.com/login",
      "mainEntity": {
        "@type": "WebSite",
        "name": "DrillQuiz",
        "description": "효율적인 퀴즈 학습을 위한 온라인 플랫폼",
        "url": "https://us.drillquiz.com",
        "potentialAction": {
          "@type": "LoginAction",
          "target": "https://us.drillquiz.com/login",
          "name": "로그인"
        }
      }
    }
    </script>
    
    <div class="login-container">
      <div class="login-card">
        <div class="login-header">
          <h1>{{ $t('login.title') }}</h1>
          <p class="login-subtitle">{{ $t('login.subtitle') }}</p>
        </div>
        
        <form @submit.prevent="onSubmit" class="login-form" autocomplete="off">
          <div class="form-group">
            <label for="id" class="form-label">{{ $t('login.username') }}</label>
            <div class="input-wrapper">
              <i class="fas fa-user input-icon"></i>
              <input 
                v-model="form.id" 
                type="text" 
                class="modern-input" 
                id="id" 
                required
                :placeholder="$t('login.usernamePlaceholder')"
              >
            </div>
          </div>
          
          <div class="form-group">
            <label for="password" class="form-label">{{ $t('login.password') }}</label>
            <div class="input-wrapper">
              <i class="fas fa-lock input-icon"></i>
              <input 
                v-model="form.password" 
                type="password" 
                class="modern-input" 
                id="password" 
                required
                :placeholder="$t('login.passwordPlaceholder')"
              >
            </div>
          </div>
          
          <div v-if="error" class="error-message">
            <i class="fas fa-exclamation-circle"></i>
            <span>{{ error }}</span>
          </div>
          
          <div class="form-actions">
            <button type="submit" class="login-btn">
              <i class="fas fa-sign-in-alt"></i>
              <span>{{ $t('login.login') }}</span>
            </button>
            
            <!-- 소셜 로그인 버튼 -->
            <div class="social-login">
              <!-- 구글 로그인 버튼 -->
              <button type="button" @click="googleLogin" class="google-login-btn">
                <i class="fab fa-google"></i>
                <span>{{ $t('login.googleLogin') }}</span>
              </button>
              
              <!-- Apple 로그인 버튼 (iOS에서는 네이티브 버튼 표시) -->
              <button 
                v-if="showAppleLoginButton" 
                type="button" 
                @click="appleLogin" 
                class="apple-login-btn"
                :class="{ 'apple-login-btn-native': isIOS }"
              >
                <i class="fab fa-apple"></i>
                <span>{{ $t('login.appleLogin') }}</span>
              </button>
            </div>
            
            <div class="register-link">
              <span>{{ $t('login.noAccount') }}</span>
              <router-link to="/register" class="register-btn">
                {{ $t('login.register') }}
              </router-link>
            </div>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { debugLog } from '@/utils/debugUtils'
import { authAPI } from '@/services/api'
import authService from '@/services/authService'

const isProduction = process.env.NODE_ENV === 'production'

export default {
  name: 'Login',
  metaInfo() {
    // 현재 언어에 따라 동적으로 메타 정보 생성
    const currentLang = this.$i18n?.locale || 'en'
    
    // 언어별 메타 정보 매핑
    const metaByLanguage = {
      'ko': {
        title: '로그인',
        description: 'DrillQuiz 로그인 - 퀴즈 학습 플랫폼에 로그인하여 개인화된 학습 경험을 시작하세요. 계정이 없으시다면 무료로 가입할 수 있습니다.',
        keywords: 'DrillQuiz 로그인, 퀴즈 학습 로그인, 온라인 학습 계정, Google 로그인',
        ogTitle: 'DrillQuiz 로그인 - 퀴즈 학습 플랫폼',
        ogDescription: 'DrillQuiz 로그인 - 퀴즈 학습 플랫폼에 로그인하여 개인화된 학습 경험을 시작하세요.',
        twitterTitle: 'DrillQuiz 로그인 - 퀴즈 학습 플랫폼',
        twitterDescription: 'DrillQuiz 로그인 - 퀴즈 학습 플랫폼에 로그인하여 개인화된 학습 경험을 시작하세요.'
      },
      'en': {
        title: 'Login',
        description: 'DrillQuiz Login - Sign in to the quiz learning platform and start your personalized learning experience. If you don\'t have an account, you can register for free.',
        keywords: 'DrillQuiz login, quiz learning login, online learning account, Google login',
        ogTitle: 'DrillQuiz Login - Quiz Learning Platform',
        ogDescription: 'DrillQuiz Login - Sign in to the quiz learning platform and start your personalized learning experience.',
        twitterTitle: 'DrillQuiz Login - Quiz Learning Platform',
        twitterDescription: 'DrillQuiz Login - Sign in to the quiz learning platform and start your personalized learning experience.'
      },
      'es': {
        title: 'Iniciar sesión',
        description: 'DrillQuiz Iniciar sesión - Inicia sesión en la plataforma de aprendizaje de cuestionarios y comienza tu experiencia de aprendizaje personalizada. Si no tienes una cuenta, puedes registrarte gratis.',
        keywords: 'DrillQuiz iniciar sesión, inicio de sesión de aprendizaje de cuestionarios, cuenta de aprendizaje en línea, inicio de sesión con Google',
        ogTitle: 'DrillQuiz Iniciar sesión - Plataforma de Aprendizaje',
        ogDescription: 'DrillQuiz Iniciar sesión - Inicia sesión en la plataforma de aprendizaje de cuestionarios y comienza tu experiencia de aprendizaje personalizada.',
        twitterTitle: 'DrillQuiz Iniciar sesión - Plataforma de Aprendizaje',
        twitterDescription: 'DrillQuiz Iniciar sesión - Inicia sesión en la plataforma de aprendizaje de cuestionarios y comienza tu experiencia de aprendizaje personalizada.'
      },
      'zh': {
        title: '登录',
        description: 'DrillQuiz 登录 - 登录测验学习平台，开始您的个性化学习体验。如果您没有账户，可以免费注册。',
        keywords: 'DrillQuiz 登录, 测验学习登录, 在线学习账户, Google 登录',
        ogTitle: 'DrillQuiz 登录 - 测验学习平台',
        ogDescription: 'DrillQuiz 登录 - 登录测验学习平台，开始您的个性化学习体验。',
        twitterTitle: 'DrillQuiz 登录 - 测验学习平台',
        twitterDescription: 'DrillQuiz 登录 - 登录测验学习平台，开始您的个性化学习体验。'
      },
      'ja': {
        title: 'ログイン',
        description: 'DrillQuiz ログイン - クイズ学習プラットフォームにログインして、パーソナライズされた学習体験を開始しましょう。アカウントをお持ちでない場合は、無料で登録できます。',
        keywords: 'DrillQuiz ログイン, クイズ学習ログイン, オンライン学習アカウント, Google ログイン',
        ogTitle: 'DrillQuiz ログイン - クイズ学習プラットフォーム',
        ogDescription: 'DrillQuiz ログイン - クイズ学習プラットフォームにログインして、パーソナライズされた学習体験を開始しましょう。',
        twitterTitle: 'DrillQuiz ログイン - クイズ学習プラットフォーム',
        twitterDescription: 'DrillQuiz ログイン - クイズ学習プラットフォームにログインして、パーソナライズ된学習体験を開始しましょう。'
      }
    }
    
    // 현재 언어에 맞는 메타 정보 선택, 없으면 영어 기본값
    const meta = metaByLanguage[currentLang] || metaByLanguage['en']
    
    return {
      title: meta.title,
      meta: [
        { 
          name: 'description', 
          content: meta.description
        },
        { 
          name: 'keywords', 
          content: meta.keywords
        },
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
        { property: 'og:url', content: 'https://us.drillquiz.com/login' },
        // Twitter Card
        { 
          name: 'twitter:title', 
          content: meta.twitterTitle
        },
        { 
          name: 'twitter:description', 
          content: meta.twitterDescription
        }
      ]
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
  data() {
    return {
      form: {
        id: '',
        password: ''
      },
      error: '',
      isLoading: false, // 구글 로그인 중 표시
      isAppleLoading: false // Apple 로그인 중 표시
    }
  },
  computed: {
    isIOS() {
      // iOS 기기인지 확인 (User-Agent만 사용)
      return /iPad|iPhone|iPod/.test(navigator.userAgent)
    },
    showAppleLoginButton() {
      // Apple 로그인은 iOS, macOS, 웹(모든 플랫폼)에서 지원
      // 네이티브 앱과 웹 모두에서 사용 가능
      return true
    }
  },
  methods: {
    async applyUserLanguage(user) {
      try {
        const targetLanguage = user?.language || this.$i18n.locale
        if (targetLanguage && targetLanguage !== this.$i18n.locale) {
          await this.$changeLanguage(targetLanguage)
          debugLog('언어 변경 완료:', targetLanguage)
        }
      } catch (error) {
        debugLog('로그인 후 언어 설정 적용 실패:', error, 'error')
      }
    },
    
    async clearAllCache({ preserveAuth = false } = {}) {
      try {
        if (!preserveAuth) {
          await authService.clearAuth()
        }

        const keysToRemove = []
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i)
          const shouldSkip = preserveAuth && key && key.startsWith('drillquiz.')
          if (key && !shouldSkip) {
            keysToRemove.push(key)
          }
        }
        
        keysToRemove.forEach(key => {
          localStorage.removeItem(key)
          if (!isProduction) {
            debugLog(`🗑️ 캐시 제거: ${key}`)
          }
        })
        
        // sessionStorage 완전 삭제
        sessionStorage.clear()
        if (!isProduction) {
          debugLog('🗑️ sessionStorage 완전 삭제')
        }
        
        // 강제 새로고침 플래그 설정
        localStorage.setItem('forceRefresh', Date.now().toString())
        if (!isProduction) {
          debugLog('🔄 강제 새로고침 플래그 설정')
          debugLog('✅ 로그인 시 모든 캐시가 무효화되었습니다.')
        }
      } catch (error) {
        debugLog('❌ 캐시 무효화 중 오류:', error, 'error')
      }
    },
    async onSubmit() {
      this.error = ''
      try {
        const data = await authAPI.login({
          username: this.form.id,
          password: this.form.password
        })

        if (!data?.success) {
          this.error = data?.detail || this.$t('login.messages.loginFailed')
          return
        }

        const user = data.user || await authService.getUser()

        // 기존 캐시 중 토큰은 유지하면서 사용자 데이터 제거
        await this.clearAllCache({ preserveAuth: true })

        await this.applyUserLanguage(user)

        if (this.$parent) {
          this.$parent.loginState = true
          this.$parent.currentUser = user
        }

        const returnTo = this.$route.query.returnTo
        this.$router.push(returnTo ? decodeURIComponent(returnTo) : '/')
      } catch (err) {
        this.error = err.response?.data?.detail || this.$t('login.messages.loginFailed')
      }
    },
    
    async googleLogin() {
      try {
        this.error = ''
        this.isLoading = true
        
        // 디버깅: 현재 환경 정보 로그
        console.warn('🔍 [Login.vue] Google 로그인 시작')
        console.warn('🔍 [Login.vue] window.location:', {
          origin: window.location.origin,
          hostname: window.location.hostname,
          protocol: window.location.protocol,
          href: window.location.href
        })
        console.warn('🔍 [Login.vue] User Agent:', navigator.userAgent)
        
        // Google OAuth 객체 확인
        if (!this.$googleOAuth) {
          throw new Error('Google OAuth가 초기화되지 않았습니다. 페이지를 새로고침해주세요.')
        }
        
        if (!this.$googleOAuth.signIn) {
          throw new Error('Google OAuth signIn 메서드를 찾을 수 없습니다.')
        }
        
        console.warn('🔍 [Login.vue] Google OAuth 객체 상태:', {
          exists: !!this.$googleOAuth,
          methods: Object.keys(this.$googleOAuth),
          signIn: !!this.$googleOAuth.signIn
        })
        
        // Google OAuth 로그인 (authorization code 방식)
        // 웹뷰 환경에서는 리다이렉트 방식이므로 signIn()이 Promise를 resolve하지 않을 수 있음
        try {
          const googleUser = await this.$googleOAuth.signIn()
          
          // 리다이렉트 방식인 경우 googleUser가 없을 수 있음
          // (이미 페이지가 리다이렉트되었을 수 있음)
          if (!googleUser) {
            // 리다이렉트가 시작되었으므로 여기서 종료
            // 백엔드에서 처리 후 프론트엔드로 리다이렉트됨
            return
          }
          
          const authCode = googleUser.code || googleUser.credential
          
          if (!authCode) {
            debugLog('❌ [Login.vue] [GOOGLE] authCode가 없음:', googleUser)
            this.error = 'Google 로그인에서 인증 코드를 받지 못했습니다.'
            return
          }
          
          debugLog('🔍 [Login.vue] [GOOGLE] 백엔드로 authorization code 전송 시작')
          debugLog('🔍 [Login.vue] [GOOGLE] authCode 존재 여부:', !!authCode)
          debugLog('🔍 [Login.vue] [GOOGLE] authCode 길이:', authCode ? authCode.length : 0)
          
          // 백엔드로 authorization code 전송
          const response = await axios.post('/api/google-oauth/', {
            id_token: authCode,  // 백엔드에서는 id_token 필드명을 유지하되 authorization code를 받음
            language: this.$i18n.locale
          }, {
            headers: {
              'Content-Type': 'application/json'
            }
          })
          
          debugLog('🔍 [Login.vue] [GOOGLE] 백엔드 응답:', {
            status: response.status,
            hasData: !!response.data,
            hasSuccess: !!(response.data && response.data.success),
            hasRequiresRegistration: !!(response.data && response.data.requires_registration)
          })
          
          // 신규 사용자 플래그 확인 (가입 처리 필요)
          if (response.data && typeof response.data === 'object' && response.data.requires_registration) {
            debugLog('🔍 [Login.vue] [GOOGLE] 신규 사용자 감지 - 가입 처리 페이지로 리다이렉트')
            const socialAuth = response.data.social_auth || {}
            
            // 가입 처리 페이지로 리다이렉트 (소셜 로그인 정보 포함)
            const registerParams = new URLSearchParams({
              social: socialAuth.provider || 'google',
              email: socialAuth.email || '',
              first_name: socialAuth.first_name || '',
              last_name: socialAuth.last_name || ''
            })
            
            this.$router.push(`/register?${registerParams.toString()}`)
            return
          }
          
          if (response.data && response.data.success) {
            debugLog('✅ [Login.vue] [GOOGLE] 로그인 성공, 토큰 저장 시작')
            
            // 토큰과 사용자 정보 저장 (중요!)
            if (response.data.tokens) {
              await authService.storeAuthResult({
                access: response.data.tokens.access,
                refresh: response.data.tokens.refresh,
                access_expires_in: response.data.tokens.access_expires_in,
                refresh_expires_in: response.data.tokens.refresh_expires_in,
                user: response.data.user
              })
              debugLog('✅ [Login.vue] [GOOGLE] 토큰 저장 완료')
            }
            
            // 로그인 성공
            this.$toast.success(response.data.message || 'Google 로그인에 성공했습니다.')
            
            // 사용자 정보 저장
            if (this.$store) {
              this.$store.commit('setUser', response.data.user)
            }
            
            // 인증 상태 강제 새로고침
            await authService.checkAuthStatus()
            
            // 홈으로 리다이렉트
            const returnTo = this.$route.query.returnTo
            const targetPath = returnTo ? decodeURIComponent(returnTo) : '/'
            this.$router.push(targetPath)
          } else {
            this.error = response.data?.message || 'Google 로그인에 실패했습니다.'
          }
        } catch (signInError) {
          // signIn()에서 리다이렉트가 시작되면 Promise가 resolve되지 않을 수 있음
          // 하지만 실제로는 페이지가 리다이렉트되므로 에러는 무시
          if (!isProduction) {
            debugLog('Google signIn() 호출 (리다이렉트 시작됨):', signInError, 'debug')
          }
          // 리다이렉트가 시작되었으므로 여기서 종료
          return
        }
      } catch (error) {
        debugLog('Google 로그인 오류:', error, 'error')
        
        // 리다이렉트가 시작된 경우 에러를 무시
        // (페이지가 이미 리다이렉트되었을 수 있음)
        if (error.message && (error.message.includes('리다이렉트') || error.message.includes('resolve'))) {
          return
        }
        
        // 사용자 친화적인 오류 메시지
        if (error.message.includes('건너뛰어졌습니다')) {
          this.error = this.$t('login.googleSkipped')
        } else if (error.message.includes('취소되었습니다')) {
          this.error = this.$t('login.googleCancelled')
        } else if (error.message.includes('팝업이 차단')) {
          this.error = this.$t('login.popupBlocked')
        } else if (error.message.includes('타임아웃')) {
          this.error = this.$t('login.googleTimeout')
        } else {
          this.error = this.$t('login.googleLoginFailed')
        }
      } finally {
        this.isLoading = false
      }
    },
    
    async appleLogin() {
      debugLog('🔍 [Login.vue] [APPLE_BUTTON] ========== Apple 로그인 버튼 클릭 ==========')
      try {
        debugLog('🔍 [Login.vue] [APPLE_BUTTON] 이벤트 시작 시간:', new Date().toISOString())
        
        this.error = ''
        this.isAppleLoading = true
        
        debugLog('🔍 [Login.vue] [APPLE_BUTTON] 초기 상태:', {
          error: this.error,
          isAppleLoading: this.isAppleLoading,
          isIOS: this.isIOS,
          windowLocation: {
            href: window.location.href,
            origin: window.location.origin,
            hostname: window.location.hostname,
            protocol: window.location.protocol
          }
        })
        
        // 웹 환경에서는 Apple OAuth 2.0 리다이렉트 방식 사용
        debugLog('🔍 [Login.vue] [APPLE_BUTTON] 웹 환경 - 웹 OAuth 방식 사용')
        await this.appleLoginWeb()
      } catch (error) {
        debugLog('❌ [Login.vue] Apple 로그인 오류:', error, 'error')
        
        // 사용자 친화적인 오류 메시지
        if (error.message && error.message.includes('취소')) {
          this.error = this.$t('login.appleCancelled') || 'Apple 로그인이 취소되었습니다.'
        } else if (error.message && error.message.includes('웹에서')) {
          this.error = error.message
        } else {
          this.error = this.$t('login.appleLoginFailed') || 'Apple 로그인에 실패했습니다. 다시 시도해주세요.'
        }
      } finally {
        this.isAppleLoading = false
      }
    },
    
    async appleLoginWeb() {
      try {
        debugLog('🔍 [Login.vue] 웹에서 Sign in with Apple 시작')
        debugLog('🔍 [Login.vue] [APPLE_OAUTH] ========== Apple OAuth 시작 ==========')
        
        // 웹뷰로 동작하는 경우에도 웹 방식과 동일하게 Services ID 사용
        // App ID (com.drillquiz.app)는 네이티브 iOS 앱에서 AuthenticationServices 프레임워크를 직접 사용할 때만 필요
        // Apple Client ID (설정에서 가져오기) - Services ID 사용!
        // iOS 웹뷰에서는 반드시 Services ID (com.drillquiz.web)를 사용해야 함
        let envClientId = process.env.VUE_APP_APPLE_CLIENT_ID
        let appleClientId = envClientId || 'com.drillquiz.web'
        
        debugLog('🔍 [Login.vue] [APPLE_OAUTH] Apple Client ID 설정 확인:', {
          envClientId: envClientId || '(없음)',
          appleClientId: appleClientId,
          processEnv: process.env.VUE_APP_APPLE_CLIENT_ID || '(없음)',
          isIOS: this.isIOS,
          finalClientId: appleClientId
        })
        
        // redirect_uri는 호출하는 웹앱의 도메인을 사용
        let redirectUri
        const hostname = window.location.hostname
        const currentHref = window.location.href
        
        debugLog('🔍 [Login.vue] [APPLE_OAUTH] window.location:', {
          origin: window.location.origin,
          hostname: hostname,
          protocol: window.location.protocol,
          href: currentHref,
          port: window.location.port || '(없음)'
        })
        
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
          // 개발 환경: 백엔드 포트(8000) 사용
          redirectUri = `${window.location.protocol}//${hostname}:8000/api/apple-oauth/`
          debugLog('🔍 [Login.vue] [APPLE_OAUTH] 일반 웹 환경 - localhost:8000 사용')
        } else {
          // 프로덕션: 현재 웹앱의 도메인 사용 (프론트엔드와 백엔드가 같은 도메인)
          redirectUri = `${window.location.origin}/api/apple-oauth/`
          debugLog('🔍 [Login.vue] [APPLE_OAUTH] 일반 웹 환경 - window.location.origin 사용')
        }
        
        debugLog('🔍 [Login.vue] [APPLE_OAUTH] 최종 redirect_uri:', redirectUri)
        
        // state 생성 (CSRF 방지 및 상태 관리)
        const stateData = {
          timestamp: Date.now(),
          returnUrl: window.location.href,
          language: this.$i18n.locale
        }
        const state = btoa(JSON.stringify(stateData))
        
        debugLog('🔍 [Login.vue] [APPLE_OAUTH] State 데이터:', {
          stateData: stateData,
          stateEncoded: state.substring(0, 50) + '...'
        })
        
        // Apple OAuth 2.0 authorization URL 생성
        const clientIdEncoded = encodeURIComponent(appleClientId)
        const redirectUriEncoded = encodeURIComponent(redirectUri)
        const stateEncoded = encodeURIComponent(state)
        
        debugLog('🔍 [Login.vue] [APPLE_OAUTH] URL 파라미터 인코딩:', {
          clientId: appleClientId,
          clientIdEncoded: clientIdEncoded,
          redirectUri: redirectUri,
          redirectUriEncoded: redirectUriEncoded,
          state: state.substring(0, 50) + '...',
          stateEncoded: stateEncoded.substring(0, 50) + '...'
        })
        
        // Apple OAuth는 항상 form_post를 사용해야 함 (query는 invalid_request 에러 발생)
        const responseMode = 'form_post'
        
        debugLog('🔍 [Login.vue] [APPLE_OAUTH] response_mode 결정:', {
          responseMode: responseMode,
          note: 'Apple OAuth는 항상 form_post 사용 (query는 invalid_request 발생)'
        })
        
        const authUrl = `https://appleid.apple.com/auth/authorize?` +
          `client_id=${clientIdEncoded}` +
          `&redirect_uri=${redirectUriEncoded}` +
          `&response_type=code id_token` +
          `&scope=email name` +
          `&response_mode=${responseMode}` +
          `&state=${stateEncoded}`
        
        debugLog('🔍 [Login.vue] [APPLE_OAUTH] ========== 최종 Apple OAuth URL ==========')
        debugLog('🔍 [Login.vue] [APPLE_OAUTH] 전체 URL:', authUrl)
        debugLog('🔍 [Login.vue] [APPLE_OAUTH] URL 파라미터 분석:', {
          client_id: appleClientId,
          redirect_uri: redirectUri,
          response_type: 'code id_token',
          scope: 'email name',
          response_mode: responseMode,
          state_length: state.length
        })
        debugLog('🔍 [Login.vue] [APPLE_OAUTH] ==========================================')
        
        // 웹 환경에서는 일반 리다이렉트 사용
        window.location.href = authUrl
      } catch (error) {
        debugLog('❌ [Login.vue] 웹 Apple 로그인 오류:', error, 'error')
        throw error
      }
    },
    
    async sendAppleIdentityToken(identityToken, userInfo) {
      debugLog('🔍 [Login.vue] [SEND_TOKEN] ========== sendAppleIdentityToken 메서드 진입 ==========')
      debugLog('🔍 [Login.vue] [SEND_TOKEN] 파라미터 확인:', {
        hasIdentityToken: !!identityToken,
        identityTokenType: typeof identityToken,
        identityTokenLength: identityToken ? identityToken.length : 0,
        hasUserInfo: !!userInfo,
        userInfo: userInfo,
        language: this.$i18n.locale
      })
      
      try {
        debugLog('🔍 [Login.vue] [SEND_TOKEN] Apple Identity Token 전송 시작')
        debugLog('🔍 [Login.vue] [SEND_TOKEN] 요청 데이터:', {
          hasIdentityToken: !!identityToken,
          identityTokenLength: identityToken ? identityToken.length : 0,
          userInfo: userInfo,
          language: this.$i18n.locale
        })
        
        // 백엔드로 identity token과 사용자 정보 전송
        debugLog('🔍 [Login.vue] [SEND_TOKEN] 백엔드 API 호출 시작: /api/apple-oauth/')
        const requestData = {
          identity_token: identityToken,
          user: userInfo, // 첫 로그인 시에만 제공됨 (name 등)
          language: this.$i18n.locale
        }
        debugLog('🔍 [Login.vue] [SEND_TOKEN] 요청 데이터:', requestData)
        
        const response = await axios.post('/api/apple-oauth/', requestData, {
          headers: {
            'Content-Type': 'application/json'
          }
        })
        
        debugLog('🔍 [Login.vue] [SEND_TOKEN] 백엔드 응답 받음:', {
          status: response.status,
          hasData: !!response.data,
          dataType: typeof response.data,
          isString: typeof response.data === 'string',
          dataKeys: response.data && typeof response.data === 'object' ? Object.keys(response.data) : [],
          hasRedirect: !!(response.data && typeof response.data === 'object' && response.data.redirect),
          hasSuccess: !!(response.data && typeof response.data === 'object' && response.data.success),
          hasUser: !!(response.data && typeof response.data === 'object' && response.data.user)
        })
        
        // HTML 응답인 경우 (에러 페이지 등)
        if (typeof response.data === 'string' && response.data.trim().startsWith('<!')) {
          debugLog('❌ [Login.vue] [SEND_TOKEN] 백엔드가 HTML 응답을 반환함 (에러 페이지)')
          const errorMessage = '백엔드에서 예상치 못한 응답을 받았습니다. 다시 시도해주세요.'
          this.error = errorMessage
          throw new Error(errorMessage)
        }
        
        // 백엔드에서 리다이렉트 응답을 반환하는 경우
        if (response.data && typeof response.data === 'object' && response.data.redirect) {
          debugLog('🔍 [Login.vue] [SEND_TOKEN] 리다이렉트 응답:', response.data.redirect)
          window.location.href = response.data.redirect
          return
        }
        
        // 신규 사용자 플래그 확인 (가입 처리 필요)
        if (response.data && typeof response.data === 'object' && response.data.requires_registration) {
          debugLog('🔍 [Login.vue] [SEND_TOKEN] 신규 사용자 감지 - 가입 처리 페이지로 리다이렉트')
          const socialAuth = response.data.social_auth || {}
          
          // 가입 처리 페이지로 리다이렉트 (소셜 로그인 정보 포함)
          const registerParams = new URLSearchParams({
            social: socialAuth.provider || 'apple',
            email: socialAuth.email || '',
            first_name: socialAuth.first_name || '',
            last_name: socialAuth.last_name || ''
          })
          
          this.$router.push(`/register?${registerParams.toString()}`)
          return
        }
        
        // 성공 응답 처리
        if (response.data && typeof response.data === 'object' && response.data.success) {
          debugLog('✅ [Login.vue] [SEND_TOKEN] 로그인 성공, 사용자 정보 업데이트 시작')
          
          // 토큰과 사용자 정보 저장 (중요!)
          if (response.data.tokens) {
            debugLog('🔍 [Login.vue] [SEND_TOKEN] 토큰 저장 시작')
            await authService.storeAuthResult({
              access: response.data.tokens.access,
              refresh: response.data.tokens.refresh,
              access_expires_in: response.data.tokens.access_expires_in,
              refresh_expires_in: response.data.tokens.refresh_expires_in,
              user: response.data.user
            })
            debugLog('✅ [Login.vue] [SEND_TOKEN] 토큰 저장 완료')
          } else {
            debugLog('⚠️ [Login.vue] [SEND_TOKEN] 응답에 tokens가 없음')
          }
          
          const user = response.data.user || await authService.getUser()
          debugLog('🔍 [Login.vue] [SEND_TOKEN] 사용자 정보:', {
            hasUser: !!user,
            userEmail: user?.email,
            userId: user?.id
          })
          
          // 기존 캐시 중 토큰은 유지하면서 사용자 데이터 제거
          await this.clearAllCache({ preserveAuth: true })
          debugLog('🔍 [Login.vue] [SEND_TOKEN] 캐시 정리 완료')
          
          await this.applyUserLanguage(user)
          debugLog('🔍 [Login.vue] [SEND_TOKEN] 언어 설정 완료')
          
          if (this.$parent) {
            this.$parent.loginState = true
            this.$parent.currentUser = user
            debugLog('🔍 [Login.vue] [SEND_TOKEN] 부모 컴포넌트 상태 업데이트 완료')
          }
          
          // 인증 상태 강제 새로고침
          debugLog('🔍 [Login.vue] [SEND_TOKEN] 인증 상태 새로고침 시작')
          await authService.checkAuthStatus()
          debugLog('🔍 [Login.vue] [SEND_TOKEN] 인증 상태 새로고침 완료')
          
          const returnTo = this.$route.query.returnTo
          const targetPath = returnTo ? decodeURIComponent(returnTo) : '/'
          debugLog('🔍 [Login.vue] [SEND_TOKEN] 라우터 이동:', targetPath)
          this.$router.push(targetPath)
        } else {
          debugLog('❌ [Login.vue] [SEND_TOKEN] 응답에 success가 없음:', response.data)
          const errorMessage = response.data?.message || this.$t('login.appleLoginFailed') || 'Apple 로그인에 실패했습니다.'
          this.error = errorMessage
          throw new Error(errorMessage)
        }
      } catch (error) {
        debugLog('❌ [Login.vue] [SEND_TOKEN] Apple Identity Token 전송 오류:', {
          error: error,
          message: error.message,
          response: error.response,
          status: error.response?.status,
          data: error.response?.data,
          stack: error.stack
        })
        
        // 500 에러 등 서버 에러 상세 로그
        if (error.response?.status === 500) {
          console.error('❌ [Login.vue] [SEND_TOKEN] 백엔드 500 에러:', error.response.data)
        }
        
        this.error = error.response?.data?.message || error.message || this.$t('login.appleLoginFailed') || 'Apple 로그인에 실패했습니다.'
        throw error // 상위로 에러 전파
      }
    }
  }
}
</script>

<style scoped>
/* Modern Login Styles */
.login-modern {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  position: relative;
}

.login-container {
  width: 100%;
  max-width: 450px;
}

.login-card {
  background: white;
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  animation: slideInUp 0.5s ease-out;
}

.login-header {
  padding: 40px 40px 30px;
  text-align: center;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
  border-bottom: 1px solid #e9ecef;
}

.login-header h1 {
  margin: 0 0 10px 0;
  font-size: 32px;
  font-weight: 700;
  color: #2c3e50;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-subtitle {
  margin: 0;
  color: #6c757d;
  font-size: 16px;
  font-weight: 400;
}

.login-form {
  padding: 40px;
}

.form-group {
  margin-bottom: 25px;
}

.form-label {
  display: block;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 8px;
  font-size: 14px;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 15px;
  color: #6c757d;
  font-size: 16px;
  z-index: 2;
}

.modern-input {
  width: 100%;
  padding: 15px 15px 15px 45px;
  border: 2px solid #e9ecef;
  border-radius: 12px;
  font-size: 16px;
  background: #f8f9fa;
  transition: all 0.3s ease;
  color: #2c3e50;
}

.modern-input:focus {
  outline: none;
  border-color: #667eea;
  background: white;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  transform: translateY(-1px);
}

.modern-input::placeholder {
  color: #adb5bd;
}

.error-message {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: #f8d7da;
  color: #721c24;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 14px;
  border-left: 4px solid #dc3545;
}

.error-message i {
  font-size: 16px;
  color: #dc3545;
}

.form-actions {
  margin-top: 30px;
}

.login-btn {
  width: 100%;
  padding: 15px 20px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.login-btn:active {
  transform: translateY(0);
}

.login-btn i {
  font-size: 14px;
}

.register-link {
  text-align: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e9ecef;
  color: #6c757d;
  font-size: 14px;
}

.register-btn {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
  margin-left: 5px;
  transition: all 0.3s ease;
}

.register-btn:hover {
  color: #764ba2;
  text-decoration: underline;
}

.social-login {
  margin: 20px 0;
  text-align: center;
}

.google-login-btn {
  width: 100%;
  padding: 12px 20px;
  background: #fff;
  color: #333;
  border: 2px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.google-login-btn:hover {
  background: #f8f9fa;
  border-color: #4285f4;
  box-shadow: 0 4px 12px rgba(66, 133, 244, 0.15);
}

.google-login-btn i {
  color: #4285f4;
  font-size: 18px;
}

.apple-login-btn {
  width: 100%;
  padding: 12px 20px;
  background: #000;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-top: 10px;
}

.apple-login-btn:hover {
  background: #333;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.apple-login-btn:active {
  background: #1a1a1a;
}

.apple-login-btn i {
  color: #fff;
  font-size: 18px;
}

.apple-login-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* iOS 네이티브 버튼 스타일 (필요시) */
.apple-login-btn-native {
  /* iOS 네이티브 버튼의 기본 스타일과 유사하게 */
  background: #000;
}

/* Animations */
@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Responsive Design */
@media (max-width: 768px) {
  .login-modern {
    padding: 15px;
  }
  
  .login-card {
    border-radius: 15px;
  }
  
  .login-header {
    padding: 30px 25px 20px;
  }
  
  .login-header h1 {
    font-size: 28px;
  }
  
  .login-form {
    padding: 30px 25px;
  }
  
  .modern-input {
    font-size: 16px; /* 모바일에서 자동 확대 방지 */
  }
}

@media (max-width: 480px) {
  .login-header h1 {
    font-size: 24px;
  }
  
  .login-subtitle {
    font-size: 14px;
  }
  
  .login-form {
    padding: 25px 20px;
  }
}
</style> 