<template>
  <div class="register-modern">
    <!-- JSON-LD 구조화된 데이터 -->
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "WebPage",
      "name": "DrillQuiz 회원가입",
      "description": "퀴즈 학습 플랫폼에 새로운 계정을 만들어 개인화된 학습 경험을 시작하세요",
      "url": "https://us.drillquiz.com/register",
      "mainEntity": {
        "@type": "WebSite",
        "name": "DrillQuiz",
        "description": "효율적인 퀴즈 학습을 위한 온라인 플랫폼",
        "url": "https://us.drillquiz.com",
        "potentialAction": {
          "@type": "RegisterAction",
          "target": "https://us.drillquiz.com/register",
          "name": "회원가입"
        }
      }
    }
    </script>
    
    <div class="register-container">
      <div class="register-card">
        <div class="register-header">
          <h1>{{ $t('register.title') }}</h1>
          <p class="register-subtitle">{{ $t('register.subtitle') }}</p>
        </div>
        
        <!-- 회원가입 폼 -->
        <form @submit.prevent="onSubmit" class="register-form" autocomplete="off">
          <div class="form-row">
            <div class="form-group">
              <label for="id" class="form-label">{{ $t('register.username') }}</label>
              <div class="input-wrapper">
                <i class="fas fa-user input-icon"></i>
                <input 
                  v-model="form.id" 
                  type="text" 
                  class="modern-input" 
                  id="id" 
                  required
                  :placeholder="$t('register.usernamePlaceholder')"
                >
              </div>
            </div>
            
            <div class="form-group">
              <label for="name" class="form-label">{{ $t('register.name') }}</label>
              <div class="input-wrapper">
                <i class="fas fa-user-circle input-icon"></i>
                <input 
                  v-model="form.name" 
                  type="text" 
                  class="modern-input" 
                  id="name" 
                  required
                  :placeholder="$t('register.namePlaceholder')"
                >
              </div>
            </div>
          </div>
          
          <div class="form-group">
            <label for="email" class="form-label">{{ $t('register.email') }}</label>
            <div class="input-wrapper">
              <i class="fas fa-envelope input-icon"></i>
              <input 
                v-model="form.email" 
                type="email" 
                class="modern-input" 
                id="email" 
                :readonly="isSocialRegistration"
                :placeholder="$t('register.emailPlaceholder')"
              >
              <span v-if="isSocialRegistration" class="social-badge">
                <i class="fab" :class="socialProvider === 'google' ? 'fa-google' : 'fa-apple'"></i>
                {{ socialProvider === 'google' ? $t('register.googleLogin') : $t('register.appleLogin') }}
              </span>
            </div>
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label for="affiliation" class="form-label">{{ $t('register.affiliation') }}</label>
              <div class="input-wrapper">
                <i class="fas fa-building input-icon"></i>
                <input 
                  v-model="form.affiliation" 
                  type="text" 
                  class="modern-input" 
                  id="affiliation"
                  :placeholder="$t('register.affiliationPlaceholder')"
                >
              </div>
            </div>
            
            <div class="form-group">
              <label for="location" class="form-label">{{ $t('register.location') }}</label>
              <div class="input-wrapper">
                <i class="fas fa-map-marker-alt input-icon"></i>
                <input 
                  v-model="form.location" 
                  type="text" 
                  class="modern-input" 
                  id="location"
                  :placeholder="$t('register.locationPlaceholder')"
                >
              </div>
            </div>
            

          </div>
          
          <!-- 소셜 로그인이 아닌 경우에만 비밀번호 필드 표시 -->
          <div v-if="!isSocialRegistration" class="form-row">
            <div class="form-group">
              <label for="password" class="form-label">{{ $t('register.password') }}</label>
              <div class="input-wrapper">
                <i class="fas fa-lock input-icon"></i>
                <input 
                  v-model="form.password" 
                  type="password" 
                  class="modern-input" 
                  id="password" 
                  required
                  :placeholder="$t('register.passwordPlaceholder')"
                >
              </div>
            </div>
            
            <div class="form-group">
              <label for="password2" class="form-label">{{ $t('register.passwordConfirm') }}</label>
              <div class="input-wrapper">
                <i class="fas fa-lock input-icon"></i>
                <input 
                  v-model="form.password2" 
                  type="password" 
                  class="modern-input" 
                  id="password2" 
                  required
                  :placeholder="$t('register.passwordConfirmPlaceholder')"
                >
              </div>
            </div>
          </div>
          
          <!-- 생년월일 입력 섹션 -->
          <div class="form-group dob-section">
            <label class="form-label">{{ $t('register.dateOfBirth.label') }} <span class="required">*</span></label>
            <div class="dob-pickers">
              <select v-model="form.dateOfBirth.year" class="dob-picker" @change="validateDateOfBirth">
                <option value="">{{ $t('register.dateOfBirth.year') }}</option>
                <option v-for="year in availableYears" :key="year" :value="year">{{ year }}</option>
              </select>
              <select v-model="form.dateOfBirth.month" class="dob-picker" @change="validateDateOfBirth">
                <option value="">{{ $t('register.dateOfBirth.month') }}</option>
                <option v-for="month in availableMonths" :key="month.value" :value="month.value">{{ month.label }}</option>
              </select>
              <select v-model="form.dateOfBirth.day" class="dob-picker" @change="validateDateOfBirth">
                <option value="">{{ $t('register.dateOfBirth.day') }}</option>
                <option v-for="day in availableDays" :key="day" :value="day">{{ day }}</option>
              </select>
            </div>
            <div v-if="dateOfBirthError" class="dob-error">
              <i class="fas fa-exclamation-circle"></i>
              <span>{{ dateOfBirthError }}</span>
            </div>
            <small class="form-text dob-privacy-note">
              {{ $t('register.dateOfBirth.privacyNote') }}
              <router-link :to="getPrivacyPolicyLink()" class="dob-privacy-link">
                {{ $t('register.dateOfBirth.privacyPolicyLink') }}
              </router-link>
            </small>
          </div>
          
          <!-- 관심 카테고리 선택 -->
          <div class="form-group">
            <label class="form-label">
              <i class="fas fa-tags"></i>
              {{ $t('profile.interestedCategories.title') }}
            </label>
            <div class="category-selection-container">
              <div class="d-flex align-items-center justify-content-between gap-2 flex-wrap">
                <!-- Selected Categories Display -->
                <div v-if="selectedCategoriesDisplay.length > 0" class="d-flex align-items-center flex-wrap gap-2 flex-grow-1">
                  <span 
                    v-for="category in selectedCategoriesDisplay" 
                    :key="category.id"
                    class="badge bg-primary"
                  >
                    {{ getCategoryDisplayName(category) }}
                    <button 
                      @click="removeCategory(category.id)" 
                      class="btn-close btn-close-white ms-1" 
                      style="font-size: 0.7em;"
                    ></button>
                  </span>
                </div>
                <!-- Category Filter Button -->
                <button 
                  @click="openCategoryFilterModal" 
                  class="btn btn-outline-primary tag-filter-btn"
                >
                  <i class="fas fa-tags"></i>
                  {{ $t('categoryFilterModal.title') }}
                  <span v-if="form.interested_categories.length > 0" class="badge bg-primary ms-2">{{ form.interested_categories.length }}</span>
                </button>
              </div>
            </div>
            <small class="form-text">{{ $t('profile.interestedCategories.hint') }}</small>
          </div>
          
          <!-- Category Filter Modal -->
          <CategoryFilterModal
            :show="showCategoryFilterModal"
            :selectedCategories="form.interested_categories"
            @update:show="showCategoryFilterModal = $event"
            @update:selectedCategories="handleSelectedCategoriesUpdate"
            @apply="handleCategoryFilterApply"
            @error="handleCategoryFilterError"
          />
          
          <div v-if="error" class="error-message">
            <i class="fas fa-exclamation-circle"></i>
            <span>{{ error }}</span>
          </div>
          
          <div class="form-actions">
            <button type="submit" class="register-btn" :disabled="!isDateOfBirthValid">
              <i class="fas fa-user-plus"></i>
              <span>{{ $t('register.register') }}</span>
            </button>
            
            <!-- 소셜 로그인 버튼 -->
            <div class="social-login">
              <!-- Google 회원가입 버튼 -->
              <button type="button" @click="googleLogin" class="google-login-btn">
                <i class="fab fa-google"></i>
                <span>{{ $t('register.googleSignup') }}</span>
              </button>
              
              <!-- Apple 회원가입 버튼 (iOS에서는 네이티브 버튼 표시) -->
              <button 
                v-if="showAppleLoginButton" 
                type="button" 
                @click="appleLogin" 
                class="apple-login-btn"
                :class="{ 'apple-login-btn-native': isIOS }"
              >
                <i class="fab fa-apple"></i>
                <span>{{ $t('register.appleSignup') }}</span>
              </button>
            </div>
            
            <div class="login-link">
              <span>{{ $t('register.haveAccount') }}</span>
              <router-link to="/login" class="login-btn">
                {{ $t('register.login') }}
              </router-link>
            </div>
          </div>
        </form>
      </div>
    </div>

    <!-- 토스트 알림 -->
    <div v-if="showToast" class="toast-notification" :class="toastType">
      <div class="toast-content">
        <i :class="toastIcon"></i>
        <span>{{ toastMessage }}</span>
      </div>
      <button @click="hideToast" class="toast-close">
        <i class="fas fa-times"></i>
      </button>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { debugLog } from '@/utils/debugUtils'
import { authAPI } from '@/services/api'
import authService from '@/services/authService'
import CategoryFilterModal from '@/components/CategoryFilterModal.vue'
import { getLocalizedContent } from '@/utils/multilingualUtils'

export default {
  name: 'Register',
  components: {
    CategoryFilterModal
  },
  metaInfo() {
    // 현재 언어에 따라 동적으로 메타 정보 생성
    const currentLang = this.$i18n?.locale || 'en'
    
    // 언어별 메타 정보 매핑
    const metaByLanguage = {
      'ko': {
        title: '회원가입',
        description: 'DrillQuiz 회원가입 - 퀴즈 학습 플랫폼에 새로운 계정을 만들어 개인화된 학습 경험을 시작하세요. 무료로 가입하고 다양한 학습 기능을 이용해보세요.',
        keywords: 'DrillQuiz 회원가입, 퀴즈 학습 가입, 온라인 학습 계정 생성, 무료 회원가입',
        ogTitle: 'DrillQuiz 회원가입 - 퀴즈 학습 플랫폼',
        ogDescription: 'DrillQuiz 회원가입 - 퀴즈 학습 플랫폼에 새로운 계정을 만들어 개인화된 학습 경험을 시작하세요.',
        twitterTitle: 'DrillQuiz 회원가입 - 퀴즈 학습 플랫폼',
        twitterDescription: 'DrillQuiz 회원가입 - 퀴즈 학습 플랫폼에 새로운 계정을 만들어 개인화된 학습 경험을 시작하세요.'
      },
      'en': {
        title: 'Register',
        description: 'DrillQuiz Registration - Create a new account on the quiz learning platform and start your personalized learning experience. Sign up for free and explore various learning features.',
        keywords: 'DrillQuiz registration, quiz learning signup, online learning account creation, free registration',
        ogTitle: 'DrillQuiz Registration - Quiz Learning Platform',
        ogDescription: 'DrillQuiz Registration - Create a new account on the quiz learning platform and start your personalized learning experience.',
        twitterTitle: 'DrillQuiz Registration - Quiz Learning Platform',
        twitterDescription: 'DrillQuiz Registration - Create a new account on the quiz learning platform and start your personalized learning experience.'
      },
      'es': {
        title: 'Registrarse',
        description: 'Registro de DrillQuiz - Crea una nueva cuenta en la plataforma de aprendizaje de cuestionarios y comienza tu experiencia de aprendizaje personalizada. Regístrate gratis y explora varias funciones de aprendizaje.',
        keywords: 'registro DrillQuiz, inscripción en aprendizaje de cuestionarios, creación de cuenta de aprendizaje en línea, registro gratuito',
        ogTitle: 'Registro de DrillQuiz - Plataforma de Aprendizaje',
        ogDescription: 'Registro de DrillQuiz - Crea una nueva cuenta en la plataforma de aprendizaje de cuestionarios y comienza tu experiencia de aprendizaje personalizada.',
        twitterTitle: 'Registro de DrillQuiz - Plataforma de Aprendizaje',
        twitterDescription: 'Registro de DrillQuiz - Crea una nueva cuenta en la plataforma de aprendizaje de cuestionarios y comienza tu experiencia de aprendizaje personalizada.'
      },
      'zh': {
        title: '注册',
        description: 'DrillQuiz 注册 - 在测验学习平台上创建新账户，开始您的个性化学习体验。免费注册并探索各种学习功能。',
        keywords: 'DrillQuiz 注册, 测验学习注册, 在线学习账户创建, 免费注册',
        ogTitle: 'DrillQuiz 注册 - 测验学习平台',
        ogDescription: 'DrillQuiz 注册 - 在测验学习平台上创建新账户，开始您的个性化学习体验。',
        twitterTitle: 'DrillQuiz 注册 - 测验学习平台',
        twitterDescription: 'DrillQuiz 注册 - 在测验学习平台上创建新账户，开始您的个性化学习体验。'
      },
      'ja': {
        title: '登録',
        description: 'DrillQuiz 登録 - クイズ学習プラットフォームで新しいアカウントを作成し、パーソナライズされた学習体験を始めましょう。無料で登録して、さまざまな学習機能を探索してください。',
        keywords: 'DrillQuiz 登録, クイズ学習登録, オンライン学習アカウント作成, 無料登録',
        ogTitle: 'DrillQuiz 登録 - クイズ学習プラットフォーム',
        ogDescription: 'DrillQuiz 登録 - クイズ学習プラットフォームで新しいアカウントを作成し、パーソナライズされた学習体験を始めましょう。',
        twitterTitle: 'DrillQuiz 登録 - クイズ学習プラットフォーム',
        twitterDescription: 'DrillQuiz 登録 - クイズ学習プラットフォームで新しいアカウントを作成し、パーソナライズされた学習体験を始めましょう。'
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
        { property: 'og:url', content: 'https://us.drillquiz.com/register' },
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
  computed: {
    isIOS() {
      // iOS 기기인지 확인 (User-Agent만 사용)
      return /iPad|iPhone|iPod/.test(navigator.userAgent)
    },
    showAppleLoginButton() {
      // iOS 또는 웹에서는 Apple 로그인 버튼 표시
      return this.isIOS || true // 일단 항상 표시 (나중에 조건 수정 가능)
    },
    selectedCategoriesDisplay() {
      // form.interested_categories ID 배열을 기반으로 카테고리 객체 반환
      if (!this.availableCategories || this.availableCategories.length === 0) {
        return []
      }
      return this.availableCategories.filter(cat => 
        this.form.interested_categories.includes(cat.id)
      )
    },
    isSocialRegistration() {
      // URL 파라미터 또는 세션에서 소셜 로그인 정보 확인
      return Boolean(this.$route.query.social || sessionStorage.getItem('social_auth_provider'))
    },
    socialProvider() {
      // 소셜 로그인 제공자 확인
      return this.$route.query.social || sessionStorage.getItem('social_auth_provider') || null
    },
    availableYears() {
      const currentYear = new Date().getFullYear()
      const years = []
      // 1900년부터 현재 연도까지
      for (let year = currentYear; year >= 1900; year--) {
        years.push(year)
      }
      return years
    },
    availableMonths() {
      const months = []
      for (let i = 1; i <= 12; i++) {
        months.push({
          value: i,
          label: i < 10 ? `0${i}` : `${i}`
        })
      }
      return months
    },
    availableDays() {
      if (!this.form.dateOfBirth.year || !this.form.dateOfBirth.month) {
        return Array.from({ length: 31 }, (_, i) => i + 1)
      }
      
      const year = parseInt(this.form.dateOfBirth.year)
      const month = parseInt(this.form.dateOfBirth.month)
      const daysInMonth = new Date(year, month, 0).getDate()
      return Array.from({ length: daysInMonth }, (_, i) => i + 1)
    },
    isDateOfBirthValid() {
      return this.form.dateOfBirth.year && 
             this.form.dateOfBirth.month && 
             this.form.dateOfBirth.day &&
             !this.dateOfBirthError
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
        name: '',
        email: '',
        affiliation: '',
        location: '',
        language: this.$i18n.locale || 'en',  // 현재 언어 설정을 기본값으로
        password: '',
        password2: '',
        interested_categories: [],
        dateOfBirth: {
          year: '',
          month: '',
          day: ''
        }
      },
      dateOfBirthError: '',
      userAge: null,
      isChildMode: false,
      error: '',
      isLoading: false,
      isAppleLoading: false, // Apple 로그인 중 표시
      // 토스트 알림 설정
      showToast: false,
      toastMessage: '',
      toastType: 'success',
      toastIcon: 'fas fa-check',
      // 관심 카테고리 관련
      availableCategories: [],
      categoryTree: [], // 트리 구조 (경로 생성용)
      loadingCategories: false,
      showCategoryFilterModal: false
    }
  },
  async mounted() {
    await this.loadCategories()
    
    // URL 파라미터에서 소셜 로그인 정보 확인
    const query = this.$route.query
    if (query.social && (query.social === 'apple' || query.social === 'google')) {
      debugLog('🔍 [Register.vue] 소셜 로그인 정보 감지:', query)
      
      // 소셜 로그인 정보를 폼에 미리 채우기
      if (query.email) {
        this.form.email = query.email
      }
      if (query.first_name) {
        this.form.name = query.first_name
      }
      if (query.last_name && this.form.name) {
        this.form.name = `${this.form.name} ${query.last_name}`.trim()
      } else if (query.last_name) {
        this.form.name = query.last_name
      }
      
      // 소셜 로그인 정보를 세션에 저장 (가입 완료 시 사용)
      if (window.sessionStorage) {
        sessionStorage.setItem('social_auth_provider', query.social)
        if (query.email) {
          sessionStorage.setItem('social_auth_email', query.email)
        }
      }
      
      debugLog('🔍 [Register.vue] 소셜 로그인 정보 폼에 적용 완료:', {
        email: this.form.email,
        name: this.form.name
      })
    }
  },
  methods: {
    validateDateOfBirth() {
      this.dateOfBirthError = ''
      
      if (!this.form.dateOfBirth.year || !this.form.dateOfBirth.month || !this.form.dateOfBirth.day) {
        return
      }
      
      const year = parseInt(this.form.dateOfBirth.year)
      const month = parseInt(this.form.dateOfBirth.month)
      const day = parseInt(this.form.dateOfBirth.day)
      
      // 미래 날짜 확인
      const today = new Date()
      const selectedDate = new Date(year, month - 1, day)
      
      if (selectedDate > today) {
        this.dateOfBirthError = this.$t('register.dateOfBirth.errors.futureDate')
        return
      }
      
      // 유효한 날짜인지 확인
      if (selectedDate.getFullYear() !== year || 
          selectedDate.getMonth() !== month - 1 || 
          selectedDate.getDate() !== day) {
        this.dateOfBirthError = this.$t('register.dateOfBirth.errors.invalidDate')
        return
      }
      
      // 나이 계산
      const age = this.calculateAge(selectedDate)
      this.userAge = age
      this.isChildMode = age < 13
    },
    
    calculateAge(birthDate) {
      const today = new Date()
      let age = today.getFullYear() - birthDate.getFullYear()
      const monthDiff = today.getMonth() - birthDate.getMonth()
      
      if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        age--
      }
      
      return age
    },
    
    
    getPrivacyPolicyLink() {
      const lang = this.$i18n.locale || 'en'
      const langMap = {
        'ko': '/privacy-policy_kr',
        'en': '/privacy-policy_en',
        'es': '/privacy-policy_es',
        'zh': '/privacy-policy_zh',
        'ja': '/privacy-policy_ja'
      }
      return langMap[lang] || '/privacy-policy_en'
    },
    
    async onSubmit() {
      this.error = ''
      
      // 생년월일 검증
      if (!this.isDateOfBirthValid) {
        if (!this.form.dateOfBirth.year || !this.form.dateOfBirth.month || !this.form.dateOfBirth.day) {
          this.dateOfBirthError = this.$t('register.dateOfBirth.errors.allRequired')
        }
        return
      }
      
      // 나이 확인 후 분기 (현재는 라우트가 없으므로 주석 처리)
      // TODO: 나이 확인 결과 화면 컴포넌트 생성 후 라우트 추가 필요
      // if (this.isChildMode) {
      //   // 어린이 모드 안내 화면으로 이동
      //   this.$router.push({
      //     name: 'AgeVerificationResult',
      //     query: {
      //       age: this.userAge,
      //       isChild: true,
      //       year: this.form.dateOfBirth.year,
      //       month: this.form.dateOfBirth.month,
      //       day: this.form.dateOfBirth.day,
      //       ...this.$route.query // 기존 쿼리 파라미터 유지 (소셜 로그인 정보 등)
      //     }
      //   })
      //   return
      // }
      
      // 소셜 로그인이 아닌 경우에만 비밀번호 검증
      if (!this.isSocialRegistration) {
        if (this.form.password !== this.form.password2) {
          const errorMessage = this.$t('register.errors.passwordMismatch')
          this.showToastNotification(errorMessage, 'error')
          this.error = errorMessage
          return
        }
      }
      try {
        // 소셜 로그인 정보 확인
        const socialProvider = this.$route.query.social || (sessionStorage.getItem('social_auth_provider') || null)
        const isSocialRegistration = Boolean(socialProvider)
        
        // 생년월일을 YYYY-MM-DD 형식으로 변환
        const dateOfBirth = `${this.form.dateOfBirth.year}-${String(this.form.dateOfBirth.month).padStart(2, '0')}-${String(this.form.dateOfBirth.day).padStart(2, '0')}`
        
        const requestData = {
          id: this.form.id,
          name: this.form.name,
          email: this.form.email,
          affiliation: this.form.affiliation,
          location: this.form.location,
          password: this.form.password,
          language: this.$i18n.locale || 'en',  // 현재 언어 설정 전달
          interested_categories: this.form.interested_categories || [],
          date_of_birth: dateOfBirth
        }
        
        // 소셜 로그인인 경우 provider 정보 추가
        if (isSocialRegistration) {
          requestData.social_provider = socialProvider
          debugLog('🔍 [Register.vue] 소셜 로그인 가입:', socialProvider)
        }
        
        console.log('회원가입 요청 데이터:', requestData)
        console.log('현재 언어 설정:', this.$i18n.locale)
        
        const data = await authAPI.register(requestData)
        
        // 소셜 로그인 세션 정보 정리
        if (isSocialRegistration) {
          sessionStorage.removeItem('social_auth_provider')
          sessionStorage.removeItem('social_auth_email')
        }

        if (!data?.success) {
          const errorMessage = data?.detail || this.$t('register.errors.registrationFailed')
          this.showToastNotification(errorMessage, 'error')
          this.error = errorMessage
          return
        }

        await this.handleAuthSuccess(data)

        this.showToastNotification(
          this.$t('register.alerts.registrationComplete'), 
          'success'
        )

        setTimeout(() => {
          this.$router.push('/')
        }, 1500)
      } catch (err) {
        const errorMessage = err.response?.data?.detail || this.$t('register.errors.registrationFailed')
        this.showToastNotification(errorMessage, 'error')
        this.error = errorMessage
      }
    },
    
    async loadCategories() {
      this.loadingCategories = true
      try {
        const response = await axios.get('/api/tag-categories/tree/', {
          params: {
            is_active: true
          }
        }).catch(() => {
          // tree API가 없으면 일반 API 사용
          return axios.get('/api/tag-categories/', {
            params: {
              is_active: true
            }
          })
        })
        
        // 트리 구조를 평면화 (표시용) + 트리 구조 유지 (경로 생성용)
        const flattenCategories = (categories) => {
          let result = []
          categories.forEach(cat => {
            if (cat && cat.is_active !== false) {
              result.push(cat)
              if (cat.children && cat.children.length > 0) {
                result = result.concat(flattenCategories(cat.children))
              }
            }
          })
          return result
        }
        
        const categories = response.data || []
        if (Array.isArray(categories) && categories.length > 0 && categories[0].children) {
          // 트리 구조인 경우
          this.availableCategories = flattenCategories(categories)
          // 트리 구조도 유지 (경로 생성용)
          this.categoryTree = categories.filter(cat => cat && cat.is_active !== false)
        } else {
          // 평면 구조인 경우 그대로 사용
          this.availableCategories = (categories || []).filter(cat => cat && cat.is_active !== false)
          this.categoryTree = (categories || []).filter(cat => cat && cat.is_active !== false)
        }
      } catch (error) {
        debugLog('카테고리 로드 실패:', error, 'error')
        this.availableCategories = []
        this.categoryTree = []
      } finally {
        this.loadingCategories = false
      }
    },
    getCategoryDisplayName(category) {
      const locale = this.$i18n.locale || 'en'
      
      // 현재 언어에 맞는 카테고리 이름 우선 사용
      // full_path는 사용자 프로필 언어로 생성될 수 있어서 신뢰하지 않음
      // 카테고리 트리에서 부모 경로 찾아서 경로 생성
      return this.buildCategoryPath(category, locale)
    },
    buildCategoryPath(category, locale) {
      // 카테고리 트리에서 부모 경로 찾기
      if (!this.categoryTree || this.categoryTree.length === 0) {
        // 트리가 없으면 현재 언어에 맞는 이름만 반환
        return getLocalizedContent(category, 'name', locale) || category.full_path || `Category ${category.id}`
      }
      
      // 카테고리 트리에서 현재 카테고리와 부모 찾기
      const findCategoryInTree = (catId, tree, path = []) => {
        for (const cat of tree) {
          const currentPath = [...path]
          // 현재 언어에 맞는 이름 추가
          const name = getLocalizedContent(cat, 'name', locale) || ''
          
          if (name) {
            currentPath.push(name)
          }
          
          // 찾는 카테고리인 경우 경로 반환
          if (cat.id === catId) {
            return currentPath
          }
          
          // 자식 카테고리 탐색
          if (cat.children && cat.children.length > 0) {
            const childPath = findCategoryInTree(catId, cat.children, currentPath)
            if (childPath) {
              return childPath
            }
          }
        }
        return null
      }
      
      const path = findCategoryInTree(category.id, this.categoryTree)
      if (path && path.length > 0) {
        return path.join(' > ')
      }
      
      // 경로를 찾지 못한 경우 현재 언어에 맞는 이름만 반환
      return getLocalizedContent(category, 'name', locale) || category.full_path || `Category ${category.id}`
    },
    openCategoryFilterModal() {
      this.showCategoryFilterModal = true
    },
    handleSelectedCategoriesUpdate(selectedCategoryIds) {
      this.form.interested_categories = selectedCategoryIds
    },
    handleCategoryFilterApply(selectedCategoryIds) {
      console.log('🔄 Register handleCategoryFilterApply 호출됨, selectedCategoryIds:', selectedCategoryIds)
      
      // 선택된 카테고리 ID를 form.interested_categories에 직접 저장
      this.form.interested_categories = selectedCategoryIds || []
    },
    handleCategoryFilterError(error) {
      debugLog('카테고리 필터 오류:', error, 'error')
      this.showToastNotification(
        this.$t('profile.interestedCategories.updateFailed'),
        'error'
      )
    },
    removeCategory(categoryId) {
      const index = this.form.interested_categories.indexOf(categoryId)
      if (index > -1) {
        this.form.interested_categories.splice(index, 1)
      }
    },
    async googleLogin() {
      try {
        this.error = ''
        this.isLoading = true
        
        // Google OAuth 로그인 (Google Identity Services 직접 사용)
        const googleUser = await this.$googleOAuth.signIn()
        const idToken = googleUser.credential
        
        // 백엔드로 ID 토큰 전송
        const response = await axios.post('/api/google-oauth/', {
          id_token: idToken,
          language: this.$i18n.locale
        })
        
        // 신규 사용자 - 가입 처리가 필요한 경우
        if (response.data.requires_registration) {
          debugLog('🔍 [Register.vue] Google 신규 사용자 감지 - 회원가입 폼에 정보 채우기')
          
          const socialAuth = response.data.social_auth || {}
          
          // 소셜 로그인 정보를 세션에 저장
          if (window.sessionStorage) {
            sessionStorage.setItem('social_auth_provider', 'google')
            if (socialAuth.email) {
              sessionStorage.setItem('social_auth_email', socialAuth.email)
            }
          }
          
          // 폼에 정보 채우기
          if (socialAuth.email) {
            this.form.email = socialAuth.email
          }
          
          // 이름 정보 채우기
          if (socialAuth.first_name || socialAuth.last_name) {
            const firstName = socialAuth.first_name || ''
            const lastName = socialAuth.last_name || ''
            this.form.name = `${firstName} ${lastName}`.trim() || ''
          }
          
          // 소셜 로그인 정보를 URL 파라미터로도 설정 (회원가입 완료 시 사용)
          const query = this.$route.query
          if (!query.social) {
            // 현재 페이지에 소셜 로그인 정보 추가
            const newQuery = {
              ...query,
              social: 'google',
              email: socialAuth.email || '',
              first_name: socialAuth.first_name || '',
              last_name: socialAuth.last_name || ''
            }
            // URL 업데이트 (페이지 리로드 없이)
            this.$router.replace({ query: newQuery })
          }
          
          this.isLoading = false
          
          // 생년월일은 이미 폼에 포함되어 있으므로 추가 작업 불필요
          
          return
        }
        
        if (response.data.success) {
          // 회원가입 성공
          this.$toast.success(response.data.message)
          
          // 사용자 정보 저장
          this.$store.commit('setUser', response.data.user)
          
          // 홈으로 리다이렉트
          this.$router.push('/')
        } else {
          this.error = response.data.message
        }
      } catch (error) {
        debugLog('Google 로그인 오류:', error, 'error')
        
        // 신규 사용자 응답이 에러로 처리된 경우
        if (error.response?.data?.requires_registration) {
          const socialAuth = error.response.data.social_auth || {}
          
          // 소셜 로그인 정보를 세션에 저장
          if (window.sessionStorage) {
            sessionStorage.setItem('social_auth_provider', 'google')
            if (socialAuth.email) {
              sessionStorage.setItem('social_auth_email', socialAuth.email)
            }
          }
          
          // 폼에 정보 채우기
          if (socialAuth.email) {
            this.form.email = socialAuth.email
          }
          
          if (socialAuth.first_name || socialAuth.last_name) {
            const firstName = socialAuth.first_name || ''
            const lastName = socialAuth.last_name || ''
            this.form.name = `${firstName} ${lastName}`.trim() || ''
          }
          
          this.isLoading = false
          
          // 생년월일은 이미 폼에 포함되어 있으므로 추가 작업 불필요
          
          return
        }
        
        // 사용자 친화적인 오류 메시지
        if (error.message.includes('건너뛰어졌습니다')) {
          this.error = this.$t('register.googleSkipped')
        } else if (error.message.includes('취소되었습니다')) {
          this.error = this.$t('register.googleCancelled')
        } else if (error.message.includes('팝업이 차단')) {
          this.error = this.$t('register.popupBlocked')
        } else if (error.message.includes('타임아웃')) {
          this.error = this.$t('register.googleTimeout')
        } else {
          this.error = this.$t('register.googleSignupFailed')
        }
      } finally {
        this.isLoading = false
      }
    },
    
    async appleLogin() {
      try {
        debugLog('🔍 [Register.vue] [APPLE_BUTTON] ========== Apple 회원가입 버튼 클릭 ==========')
        debugLog('🔍 [Register.vue] [APPLE_BUTTON] 이벤트 시작 시간:', new Date().toISOString())
        
        this.error = ''
        this.isAppleLoading = true
        
        debugLog('🔍 [Register.vue] [APPLE_BUTTON] 초기 상태:', {
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
        debugLog('🔍 [Register.vue] [APPLE_BUTTON] 웹 환경 - 웹 OAuth 방식 사용')
        await this.appleLoginWeb()
      } catch (error) {
        debugLog('❌ [Register.vue] Apple 로그인 오류:', error, 'error')
        
        // 사용자 친화적인 오류 메시지
        if (error.message && error.message.includes('취소')) {
          this.error = this.$t('register.appleCancelled')
        } else if (error.message && error.message.includes('웹에서')) {
          this.error = error.message
        } else {
          this.error = this.$t('register.appleSignupFailed')
        }
      } finally {
        this.isAppleLoading = false
      }
    },
    
    async appleLoginWeb() {
      try {
        debugLog('🔍 [Register.vue] 웹에서 Sign in with Apple 시작')
        debugLog('🔍 [Register.vue] [APPLE_OAUTH] ========== Apple OAuth 시작 ==========')
        
        // 웹뷰로 동작하는 경우에도 웹 방식과 동일하게 Services ID 사용
        // App ID (com.drillquiz.app)는 네이티브 iOS 앱에서 AuthenticationServices 프레임워크를 직접 사용할 때만 필요
        // Apple Client ID (설정에서 가져오기) - Services ID 사용!
        // iOS 웹뷰에서는 반드시 Services ID (com.drillquiz.web)를 사용해야 함
        let envClientId = process.env.VUE_APP_APPLE_CLIENT_ID
        let appleClientId = envClientId || 'com.drillquiz.web'
        
        debugLog('🔍 [Register.vue] [APPLE_OAUTH] Apple Client ID 설정 확인:', {
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
        
        debugLog('🔍 [Register.vue] [APPLE_OAUTH] window.location:', {
          origin: window.location.origin,
          hostname: hostname,
          protocol: window.location.protocol,
          href: currentHref,
          port: window.location.port || '(없음)'
        })
        
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
          // 개발 환경: 백엔드 포트(8000) 사용
          redirectUri = `${window.location.protocol}//${hostname}:8000/api/apple-oauth/`
          debugLog('🔍 [Register.vue] [APPLE_OAUTH] 일반 웹 환경 - localhost:8000 사용')
        } else {
          // 프로덕션: 현재 웹앱의 도메인 사용 (프론트엔드와 백엔드가 같은 도메인)
          redirectUri = `${window.location.origin}/api/apple-oauth/`
          debugLog('🔍 [Register.vue] [APPLE_OAUTH] 일반 웹 환경 - window.location.origin 사용')
        }
        
        debugLog('🔍 [Register.vue] [APPLE_OAUTH] 최종 redirect_uri:', redirectUri)
        
        // state 생성 (CSRF 방지 및 상태 관리)
        const stateData = {
          timestamp: Date.now(),
          returnUrl: window.location.href,
          language: this.$i18n.locale
        }
        const state = btoa(JSON.stringify(stateData))
        
        debugLog('🔍 [Register.vue] [APPLE_OAUTH] State 데이터:', {
          stateData: stateData,
          stateEncoded: state.substring(0, 50) + '...'
        })
        
        // Apple OAuth 2.0 authorization URL 생성
        const clientIdEncoded = encodeURIComponent(appleClientId)
        const redirectUriEncoded = encodeURIComponent(redirectUri)
        const stateEncoded = encodeURIComponent(state)
        
        debugLog('🔍 [Register.vue] [APPLE_OAUTH] URL 파라미터 인코딩:', {
          clientId: appleClientId,
          clientIdEncoded: clientIdEncoded,
          redirectUri: redirectUri,
          redirectUriEncoded: redirectUriEncoded,
          state: state.substring(0, 50) + '...',
          stateEncoded: stateEncoded.substring(0, 50) + '...'
        })
        
        // Apple OAuth는 항상 form_post를 사용해야 함 (query는 invalid_request 에러 발생)
        const responseMode = 'form_post'
        
        debugLog('🔍 [Register.vue] [APPLE_OAUTH] response_mode 결정:', {
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
        
        debugLog('🔍 [Register.vue] [APPLE_OAUTH] ========== 최종 Apple OAuth URL ==========')
        debugLog('🔍 [Register.vue] [APPLE_OAUTH] 전체 URL:', authUrl)
        debugLog('🔍 [Register.vue] [APPLE_OAUTH] URL 파라미터 분석:', {
          client_id: appleClientId,
          redirect_uri: redirectUri,
          response_type: 'code id_token',
          scope: 'email name',
          response_mode: responseMode,
          state_length: state.length
        })
        debugLog('🔍 [Register.vue] [APPLE_OAUTH] ==========================================')
        
        // 웹 환경에서는 일반 리다이렉트 사용
        debugLog('🔍 [Register.vue] [APPLE_OAUTH] ========== 웹 환경 ==========')
        debugLog('🔍 [Register.vue] [APPLE_OAUTH] 환경 정보:', {
          isIOS: this.isIOS,
          userAgent: window.navigator?.userAgent || '(없음)'
        })
        debugLog('🔍 [Register.vue] [APPLE_OAUTH] ✅ 웹 환경 - 일반 리다이렉트 사용')
        debugLog('🔍 [Register.vue] [APPLE_OAUTH] window.location.href 호출 전')
        window.location.href = authUrl
        debugLog('🔍 [Register.vue] [APPLE_OAUTH] window.location.href 호출 완료 (리다이렉트 중)')
      } catch (error) {
        debugLog('❌ [Register.vue] 웹 Apple 로그인 오류:', error, 'error')
        throw error
      }
    },
    
    async sendAppleIdentityToken(identityToken, userInfo) {
      try {
        debugLog('🔍 [Register.vue] Apple Identity Token 전송 시작')
        
        // 백엔드로 identity token과 사용자 정보 전송
        const response = await axios.post('/api/apple-oauth/', {
          identity_token: identityToken,
          user: userInfo, // 첫 로그인 시에만 제공됨 (name 등)
          language: this.$i18n.locale
        })
        
        debugLog('🔍 [Register.vue] Apple OAuth 응답:', response.data)
        
        // 백엔드에서 리다이렉트 응답을 반환하는 경우
        if (response.data && response.data.redirect) {
          window.location.href = response.data.redirect
          return
        }
        
        // 신규 사용자 - 가입 처리가 필요한 경우
        if (response.data.requires_registration) {
          debugLog('🔍 [Register.vue] 신규 사용자 감지 - 회원가입 폼에 정보 채우기')
          
          const socialAuth = response.data.social_auth || {}
          
          // 소셜 로그인 정보를 세션에 저장
          if (window.sessionStorage) {
            sessionStorage.setItem('social_auth_provider', 'apple')
            if (socialAuth.email) {
              sessionStorage.setItem('social_auth_email', socialAuth.email)
            }
          }
          
          // 폼에 정보 채우기
          if (socialAuth.email) {
            this.form.email = socialAuth.email
          }
          
          // 이름 정보 채우기
          if (socialAuth.first_name || socialAuth.last_name) {
            const firstName = socialAuth.first_name || ''
            const lastName = socialAuth.last_name || ''
            this.form.name = `${firstName} ${lastName}`.trim() || ''
          }
          
          // 소셜 로그인 정보를 URL 파라미터로도 설정 (회원가입 완료 시 사용)
          const query = this.$route.query
          if (!query.social) {
            // 현재 페이지에 소셜 로그인 정보 추가
            const newQuery = {
              ...query,
              social: 'apple',
              email: socialAuth.email || '',
              first_name: socialAuth.first_name || '',
              last_name: socialAuth.last_name || ''
            }
            // URL 업데이트 (페이지 리로드 없이)
            this.$router.replace({ query: newQuery })
          }
          
          this.isAppleLoading = false
          
          // 생년월일은 이미 폼에 포함되어 있으므로 추가 작업 불필요
          
          return
        }
        
        // 성공 응답 처리
        if (response.data.success) {
          const user = response.data.user || await authService.getUser()
          
          await this.handleAuthSuccess({ user })
          
          this.showToastNotification(
            this.$t('register.alerts.registrationComplete'),
            'success'
          )
          
          setTimeout(() => {
            this.$router.push('/')
          }, 1500)
        } else {
          this.error = response.data.message || this.$t('register.appleSignupFailed')
        }
      } catch (error) {
        debugLog('❌ [Register.vue] Apple Identity Token 전송 오류:', error, 'error')
        
        // 신규 사용자 응답이 에러로 처리된 경우
        if (error.response?.data?.requires_registration) {
          const socialAuth = error.response.data.social_auth || {}
          
          // 소셜 로그인 정보를 세션에 저장
          if (window.sessionStorage) {
            sessionStorage.setItem('social_auth_provider', 'apple')
            if (socialAuth.email) {
              sessionStorage.setItem('social_auth_email', socialAuth.email)
            }
          }
          
          // 폼에 정보 채우기
          if (socialAuth.email) {
            this.form.email = socialAuth.email
          }
          
          if (socialAuth.first_name || socialAuth.last_name) {
            const firstName = socialAuth.first_name || ''
            const lastName = socialAuth.last_name || ''
            this.form.name = `${firstName} ${lastName}`.trim() || ''
          }
          
          this.isAppleLoading = false
          
          // 생년월일은 이미 폼에 포함되어 있으므로 추가 작업 불필요
          
          return
        }
        
        this.error = error.response?.data?.message || this.$t('register.appleSignupFailed')
      }
    },
    
    // 토스트 알림 메서드들
    showToastNotification(message, type = 'success', icon = null) {
      this.toastMessage = message
      this.toastType = type
      this.toastIcon = icon || this.getToastIcon(type)
      this.showToast = true
      
      setTimeout(() => {
        this.hideToast()
      }, 3000)
    },
    
    hideToast() {
      this.showToast = false
    },
    
    getToastIcon(type) {
      switch (type) {
        case 'success':
          return 'fas fa-check'
        case 'error':
          return 'fas fa-exclamation-triangle'
        case 'warning':
          return 'fas fa-exclamation-circle'
        case 'info':
          return 'fas fa-info-circle'
        default:
          return 'fas fa-info-circle'
      }
    },

    async handleAuthSuccess(data) {
      const user = data.user || await authService.getUser()
      await this.applyUserLanguage(user)

      window.dispatchEvent(new CustomEvent('authStatusChanged', {
        detail: {
          authenticated: true,
          user
        }
      }))

      if (window.vueApp && window.vueApp.$children[0]) {
        window.vueApp.$children[0].loginState = true
        window.vueApp.$children[0].currentUser = user
        window.vueApp.$children[0].$forceUpdate()
      }
    },

    async applyUserLanguage(user) {
      try {
        const targetLanguage = user?.language || this.$i18n.locale
        if (targetLanguage && targetLanguage !== this.$i18n.locale) {
          await this.$changeLanguage(targetLanguage)
          debugLog('회원가입 후 언어 변경:', targetLanguage)
        }
      } catch (error) {
        debugLog('회원가입 후 언어 설정 적용 실패:', error, 'error')
      }
    }
  }
}
</script>

<style scoped>
/* Modern Register Styles */
.register-modern {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.register-container {
  width: 100%;
  max-width: 600px;
}

.register-card {
  background: white;
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  animation: slideInUp 0.5s ease-out;
}

.register-header {
  padding: 40px 40px 30px;
  text-align: center;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
  border-bottom: 1px solid #e9ecef;
}

.register-header h1 {
  margin: 0 0 10px 0;
  font-size: 32px;
  font-weight: 700;
  color: #2c3e50;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.register-subtitle {
  margin: 0;
  color: #6c757d;
  font-size: 16px;
  font-weight: 400;
}

/* Date of Birth Section Styles */
.dob-section {
  margin-bottom: 25px;
}

.dob-label {
  font-weight: 600;
  color: #2c3e50;
  font-size: 14px;
  margin-bottom: 10px;
}

.dob-pickers {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.dob-picker {
  flex: 1;
  min-width: 100px;
  padding: 15px;
  border: 2px solid #e9ecef;
  border-radius: 12px;
  font-size: 16px;
  background: white;
  color: #2c3e50;
  cursor: pointer;
  transition: all 0.3s ease;
}

.dob-picker:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.dob-picker:hover {
  border-color: #667eea;
}

.dob-error {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: #f8d7da;
  color: #721c24;
  border-radius: 8px;
  font-size: 14px;
  border-left: 4px solid #dc3545;
}

.dob-error i {
  font-size: 16px;
  color: #dc3545;
}

.dob-privacy-note {
  font-size: 12px;
  color: #6c757d;
  line-height: 1.5;
  margin-top: 10px;
  display: block;
}

.dob-privacy-link {
  color: #667eea;
  text-decoration: none;
  font-size: 12px;
  font-weight: 500;
  transition: color 0.3s ease;
}

.dob-privacy-link:hover {
  color: #764ba2;
  text-decoration: underline;
}

.form-divider {
  margin: 30px 0;
  border: none;
  border-top: 1px solid #e9ecef;
}

.register-form {
  padding: 40px;
}

.form-row {
  display: flex;
  gap: 20px;
  margin-bottom: 25px;
}

.form-row .form-group {
  flex: 1;
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

.form-label .required {
  color: #dc3545;
  margin-left: 4px;
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
}

.input-wrapper {
  position: relative;
}

.social-badge {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 8px;
  background: #f8f9fa;
  border-radius: 6px;
  font-size: 12px;
  color: #6c757d;
  font-weight: 500;
}

.social-badge i {
  font-size: 14px;
}

.modern-input[readonly] {
  background-color: #f8f9fa;
  cursor: not-allowed;
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

.register-btn {
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

.register-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.register-btn:active {
  transform: translateY(0);
}

.register-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.register-btn i {
  font-size: 14px;
}

.login-link {
  text-align: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e9ecef;
  color: #6c757d;
  font-size: 14px;
}

.login-btn-link {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
  margin-left: 5px;
  transition: all 0.3s ease;
}

.login-btn-link:hover {
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
  .register-modern {
    padding: 10px;
  }
  
  .register-card {
    border-radius: 15px;
  }
  
  .register-header {
    padding: 30px 25px 20px;
  }
  
  .register-header h1 {
    font-size: 28px;
  }
  
  .register-form {
    padding: 30px 25px;
  }
  
  .form-row {
    flex-direction: column;
    gap: 0;
  }
  
  .modern-input {
    font-size: 16px; /* 모바일에서 자동 확대 방지 */
  }
}

@media (max-width: 480px) {
  .register-header h1 {
    font-size: 24px;
  }
  
  .register-subtitle {
    font-size: 14px;
  }
  
  .register-form {
    padding: 25px 20px;
  }
}

/* 토스트 알림 스타일 - 기본 스타일은 공통 CSS (mobile-buttons.css)에 정의됨 */

/* 타입별 스타일은 공통 CSS (mobile-buttons.css)에 정의됨 */

.toast-close {
  background: none;
  border: none;
  color: #6c757d;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.toast-close:hover {
  background: #f8f9fa;
  color: #495057;
}

@keyframes slideInRight {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* 모바일에서 토스트 위치 조정 */
@media (max-width: 768px) {
  .toast-notification {
    right: 10px;
    left: 10px;
    max-width: none;
  }
}
</style> 