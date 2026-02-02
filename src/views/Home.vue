<template>
  <div class="home-modern">
    <!-- JSON-LD 구조화된 데이터 -->
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "WebSite",
      "name": "DrillQuiz",
      "description": "효율적인 퀴즈 학습을 위한 온라인 플랫폼",
      "url": "https://us.drillquiz.com",
      "potentialAction": [
        {
          "@type": "SearchAction",
          "target": "https://us.drillquiz.com/random-practice",
          "query-input": "required",
          "name": "랜덤 연습"
        },
        {
          "@type": "ViewAction",
          "target": "https://us.drillquiz.com/getting-started",
          "name": "시작하기"
        }
      ],
      "offers": {
        "@type": "Offer",
        "price": "0",
        "priceCurrency": "KRW",
        "description": "무료 퀴즈 학습 플랫폼"
      }
    }
    </script>
    
    <!-- Toast Notifications -->
    <div v-if="showToast" class="toast-notification" :class="toastType">
      <div class="toast-content">
        <i :class="toastIcon"></i>
        <span>{{ toastMessage }}</span>
      </div>
      <button class="toast-close" @click="hideToast">
        <i class="fas fa-times"></i>
      </button>
    </div>
    
    <!-- Confirm Modal -->
    <div v-if="showConfirmModal" class="modal-overlay" @click="cancelConfirmModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h5 class="modal-title">
            <i class="fas fa-exclamation-triangle text-warning"></i>
            {{ confirmModalTitle }}
          </h5>
          <button class="modal-close" @click="cancelConfirmModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <p class="mb-0">{{ confirmModalMessage }}</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="cancelConfirmModal">
            {{ $t('common.cancel') || '취소' }}
          </button>
          <button class="btn btn-danger" @click="confirmDeleteResult">
            {{ $t('common.delete') || '삭제' }}
          </button>
        </div>
      </div>
    </div>
    
    <!-- 번역 로딩 중일 때 로딩 표시 -->
    <div v-if="!$isTranslationsLoaded($i18n.locale)" class="loading-container">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">{{ $t('common.loadingTranslations') }}</span>
      </div>
      <p class="mt-3">{{ $t('common.loadingTranslationData') }}</p>
    </div>
    
    <!-- 번역이 로드된 후에만 컨텐츠 표시 -->
    <div v-else class="home-content">
      <!-- Hero Section -->
      <div class="hero-section">
        <div class="hero-content">
          <h1 class="hero-title">{{ $t('home.title') }}</h1>
          <p class="hero-subtitle">{{ $t('home.subtitle') }}</p>
          <p class="hero-description">{{ $t('home.description') }}</p>
        </div>
      </div>

      <!-- Main Content -->
      <div class="main-container">

        <!-- 주요 기능 카드 -->
        <section class="features-section">
          <div class="section-header">
            <p class="section-subtitle">{{ $t('home.features.subtitle') || 'DrillQuiz의 핵심 기능들을 확인해보세요' }}</p>
          </div>
          <div class="features-grid">
            <div class="feature-card">
              <div class="feature-icon" @click="$router.push('/getting-started')">
                <i class="fas fa-rocket"></i>
              </div>
              <div class="feature-content">
                <h3 class="feature-title">{{ $t('home.card.gettingStarted.title') }}</h3>
                <p class="feature-description">{{ $t('home.card.gettingStarted.description') }}</p>
              </div>
            </div>
            
            <div class="feature-card exam-management-card">
              <div class="feature-icon exam-management-icon" @click="navigateToExamManagement">
                <i class="fas fa-clipboard-list"></i>
              </div>
              <div class="feature-content">
                <h3 class="feature-title">{{ $t('home.card.examManagement.title') || 'My Exams' }}</h3>
                <p class="feature-description">{{ $t('home.card.examManagement.description') || '시험을 생성하고 관리하세요' }}</p>
              </div>
            </div>
            
            <div class="feature-card">
              <div class="feature-icon" @click="$router.push('/study-management')">
                <i class="fas fa-book"></i>
              </div>
              <div class="feature-content">
                <h3 class="feature-title">{{ $t('home.card.studyManagement.title') }}</h3>
                <p class="feature-description">{{ $t('home.card.studyManagement.description') }}</p>
              </div>
            </div>
            
            <div class="feature-card">
              <div class="feature-icon" @click="goToDailyExam">
                <i class="fas fa-calendar-day"></i>
              </div>
              <div class="feature-content">
                <h3 class="feature-title">{{ $t('home.card.dailyExam.title') }}</h3>
                <p class="feature-description">{{ $t('home.card.dailyExam.description') }}</p>
              </div>
            </div>
            
            <div class="feature-card">
              <div class="feature-icon" @click="$router.push('/question-files')">
                <i class="fas fa-file-alt"></i>
              </div>
              <div class="feature-content">
                <h3 class="feature-title">{{ $t('home.card.questionManagement.title') }}</h3>
                <p class="feature-description">{{ $t('home.card.questionManagement.description') }}</p>
              </div>
            </div>
            
            <div class="feature-card">
              <div class="feature-icon" @click="goToRandomPractice">
                <i class="fas fa-random"></i>
              </div>
              <div class="feature-content">
                <h3 class="feature-title">{{ $t('home.card.randomPractice.title') }}</h3>
                <p class="feature-description">{{ $t('home.card.randomPractice.description') }}</p>
              </div>
            </div>
            
            <!-- 사용자 관리 카드: 시스템 어드민만 표시 -->
            <div class="feature-card" v-if="isAdmin">
              <div class="feature-icon" @click="$router.push('/user-management')">
                <i class="fas fa-users-cog"></i>
              </div>
              <div class="feature-content">
                <h3 class="feature-title">{{ $t('home.card.userManagement.title') }}</h3>
                <p class="feature-description">{{ $t('home.card.userManagement.description') }}</p>
              </div>
            </div>
            
            <!-- 카테고리 관리 카드: 시스템 어드민만 표시 -->
            <div class="feature-card" v-if="isAdmin">
              <div class="feature-icon" @click="$router.push('/category-management')">
                <i class="fas fa-tags"></i>
              </div>
              <div class="feature-content">
                <h3 class="feature-title">{{ $t('home.card.categoryManagement.title') }}</h3>
                <p class="feature-description">{{ $t('home.card.categoryManagement.description') }}</p>
              </div>
            </div>
          </div>
        </section>

        <!-- 로딩 중 -->
        <div v-if="loading && isAuthenticated" class="loading-section">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">{{ $t('home.loading.text') }}</span>
          </div>
          <p class="mt-2">{{ $t('home.loading.description') }}</p>
        </div>

        <!-- 스터디 진행 상황: 로그인 시에만 노출 -->
        <section v-if="isAuthenticated" class="data-section">
          <div class="section-header">
            <h2 class="section-title">{{ $t('home.studyProgress.title') }}</h2>
          </div>
          
          <div v-if="studies.length === 0" class="empty-state">
            <i class="fas fa-book-open empty-icon"></i>
          </div>
          
          <div v-else class="data-table">
            <div class="table-header">
              <div class="table-cell">Study</div>
              <div class="table-cell">Description</div>
              <div class="table-cell">Period</div>
              <div class="table-cell">Progress</div>
            </div>
            
            <div class="table-body">
              <div v-for="study in (filteredStudies || []).filter(Boolean)" :key="study.id" class="table-row">
                <div class="table-cell">
                  <router-link :to="`/study-detail/${study.id}`" class="table-link">
                    {{ getStudyTitle(study) }}
                  </router-link>
                </div>
                <div class="table-cell description-cell">
                  <div class="description-text" v-if="study.goal">{{ getStudyGoal(study) }}</div>
                  <div class="description-empty" v-else>{{ getLocalizedFallback(currentLanguage, 'description') }}</div>
                </div>
                <div class="table-cell">{{ formatDate(study.start_date) }} ~ {{ formatDate(study.end_date) }}</div>
                <div class="table-cell">
                  <router-link
                    :to="`/study-progress-dashboard/${study.id}`"
                    class="progress-link"
                    @click="recordProgress(study.id)"
                  >
                    {{ (typeof study.overall_progress === 'number' ? study.overall_progress : 0).toFixed(1) }}%
                  </router-link>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 모바일용 간단한 카드 -->
          <div class="mobile-cards">
            <div v-for="study in (filteredStudies || []).filter(Boolean).slice(0, 3)" :key="study.id" class="mobile-card">
              <div class="mobile-card-header">
                <router-link :to="`/study-detail/${study.id}`" class="mobile-card-title-link">
                  {{ getStudyTitle(study) }}
                </router-link>
                <span class="mobile-card-progress">{{ (typeof study.overall_progress === 'number' ? study.overall_progress : 0).toFixed(1) }}%</span>
              </div>
              <div class="mobile-card-info">
                <p class="mobile-card-date">{{ formatDate(study.start_date) }} ~ {{ formatDate(study.end_date) }}</p>
                <div class="mobile-card-status-container">
                  <span class="mobile-card-status" :class="getStudyStatus(study)">{{ getStudyStatusText(study) }}</span>
                  <router-link :to="`/study-progress-dashboard/${study.id}`" class="mobile-card-btn progress">Progress</router-link>
                </div>
              </div>
              <div class="mobile-card-actions">
              </div>
            </div>
          </div>
        </section>

        <!-- 최근 시험 결과: 로그인 시에만 노출 -->
        <section v-if="isAuthenticated" class="data-section">
          <div class="section-header">
            <h2 class="section-title">{{ $t('home.recentResults.title') }}</h2>
          </div>
          
          <div v-if="recentResults.length === 0" class="empty-state">
            <i class="fas fa-chart-line empty-icon"></i>
            <p>{{ $t('home.recentResults.noResults') }}</p>
          </div>
          
          <div v-else class="data-table">
            <div class="table-header">
              <div class="table-cell">{{ $t('home.recentResults.table.examTitle') }}</div>
              <div class="table-cell">{{ $t('home.recentResults.table.score') }}</div>
              <div class="table-cell">{{ $t('home.recentResults.table.correctCount') }}</div>
              <div class="table-cell">{{ $t('home.recentResults.table.wrongCount') }}</div>
              <div class="table-cell">{{ $t('home.recentResults.table.completedDate') }}</div>
              <div class="table-cell">{{ $t('home.recentResults.table.elapsedTime') }}</div>
            </div>
            
            <div class="table-body">
              <div v-for="result in recentResults" :key="result.id" class="table-row">
                <div class="table-cell">
                  <router-link :to="`/exam-detail/${result.exam.id}`" class="table-link">
                    {{ getLocalizedExamTitle(result.exam) }}
                  </router-link>
                </div>
                <div class="table-cell">
                  <span v-if="result.exam.latest_correct_count !== null && result.exam.latest_total_score">
                    {{ result.exam.latest_correct_count }}/{{ result.exam.latest_total_score }}
                  </span>
                  <span v-else>
                    {{ result.score }}/{{ result.total_score }}
                  </span>
                </div>
                <div class="table-cell">
                  <span v-if="result.exam.latest_correct_count !== null">
                    {{ result.exam.latest_correct_count }}
                  </span>
                  <span v-else>
                    {{ result.correct_count }}
                  </span>
                </div>
                <div class="table-cell">
                  <span v-if="result.exam.latest_correct_count !== null && result.exam.latest_total_score">
                    {{ result.exam.latest_total_score - result.exam.latest_correct_count }}
                  </span>
                  <span v-else>
                    {{ result.wrong_count }}
                  </span>
                </div>
                <div class="table-cell">{{ formatDate(result.completed_at) }}</div>
                <div class="table-cell">{{ formatElapsed(result.elapsed_seconds) }}</div>
              </div>
            </div>
          </div>
          
          <!-- 모바일용 간단한 카드 -->
          <div class="mobile-cards">
            <div v-for="result in recentResults.slice(0, 3)" :key="result.id" class="mobile-card">
              <div class="mobile-card-header">
                <router-link :to="`/exam-detail/${result.exam.id}`" class="mobile-card-title-link">
                  {{ getLocalizedExamTitle(result.exam) }}
                </router-link>
                <span class="mobile-card-score">
                  <span v-if="result.exam?.latest_correct_count !== null && result.exam?.latest_total_score">
                    {{ result.exam.latest_correct_count }}/{{ result.exam.latest_total_score }}
                  </span>
                  <span v-else>
                    {{ result.correct_count }}/{{ result.total_score }}
                  </span>
                </span>
              </div>
              <div class="mobile-card-info">
                <p class="mobile-card-date">{{ formatDate(result.completed_at) }}</p>
                <span class="mobile-card-time">{{ formatElapsed(result.elapsed_seconds) }}</span>
              </div>
              <div class="mobile-card-actions">
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { formatLocalDate } from '@/utils/dateUtils'
import { getLocalizedContent, getCurrentLanguage, getLocalizedFallback } from '@/utils/multilingualUtils'
import { debugLog } from '@/utils/debugUtils'
import { isAdmin, hasStudyAdminRole, getCurrentUser as getCurrentUserFromPermissions } from '@/utils/permissionUtils'

export default {
  name: 'Home',
  metaInfo() {
    // 현재 언어에 따라 동적으로 메타 정보 생성
    const currentLang = this.$i18n?.locale || 'en'
    
    // 언어별 메타 정보 매핑
    const metaByLanguage = {
      'ko': {
        title: '홈',
        description: 'DrillQuiz 홈페이지 - 효율적인 퀴즈 학습을 위한 온라인 플랫폼입니다. 문제 풀이, 시험 관리, 학습 진도 추적을 통해 학습 효과를 극대화하세요.',
        keywords: '퀴즈 학습, 온라인 시험, 문제 풀이, 학습 관리, DrillQuiz',
        ogTitle: 'DrillQuiz - 퀴즈 학습 플랫폼',
        ogDescription: 'DrillQuiz 홈페이지 - 효율적인 퀴즈 학습을 위한 온라인 플랫폼입니다.',
        twitterTitle: 'DrillQuiz - 퀴즈 학습 플랫폼',
        twitterDescription: 'DrillQuiz 홈페이지 - 효율적인 퀴즈 학습을 위한 온라인 플랫폼입니다.'
      },
      'en': {
        title: 'Home',
        description: 'DrillQuiz Homepage - An online platform for efficient quiz learning. Maximize your learning effectiveness through problem solving, exam management, and learning progress tracking.',
        keywords: 'quiz learning, online exam, problem solving, learning management, DrillQuiz',
        ogTitle: 'DrillQuiz - Quiz Learning Platform',
        ogDescription: 'DrillQuiz Homepage - An online platform for efficient quiz learning.',
        twitterTitle: 'DrillQuiz - Quiz Learning Platform',
        twitterDescription: 'DrillQuiz Homepage - An online platform for efficient quiz learning.'
      },
      'es': {
        title: 'Inicio',
        description: 'Página de inicio de DrillQuiz - Una plataforma en línea para un aprendizaje eficiente de cuestionarios. Maximice su efectividad de aprendizaje a través de la resolución de problemas, gestión de exámenes y seguimiento del progreso del aprendizaje.',
        keywords: 'aprendizaje de cuestionarios, examen en línea, resolución de problemas, gestión del aprendizaje, DrillQuiz',
        ogTitle: 'DrillQuiz - Plataforma de Aprendizaje',
        ogDescription: 'Página de inicio de DrillQuiz - Una plataforma en línea para un aprendizaje eficiente de cuestionarios.',
        twitterTitle: 'DrillQuiz - Plataforma de Aprendizaje',
        twitterDescription: 'Página de inicio de DrillQuiz - Una plataforma en línea para un aprendizaje eficiente de cuestionarios.'
      },
      'zh': {
        title: '首页',
        description: 'DrillQuiz 首页 - 高效的在线测验学习平台。通过问题解答、考试管理和学习进度跟踪，最大化您的学习效果。',
        keywords: '测验学习, 在线考试, 问题解答, 学习管理, DrillQuiz',
        ogTitle: 'DrillQuiz - 测验学习平台',
        ogDescription: 'DrillQuiz 首页 - 高效的在线测验学习平台。',
        twitterTitle: 'DrillQuiz - 测验学习平台',
        twitterDescription: 'DrillQuiz 首页 - 高效的在线测验学习平台。'
      },
      'ja': {
        title: 'ホーム',
        description: 'DrillQuiz ホームページ - 効率的なクイズ学習のためのオンラインプラットフォームです。問題解決、試験管理、学習進捗追跡を通じて学習効果を最大化します。',
        keywords: 'クイズ学習, オンライン試験, 問題解決, 学習管理, DrillQuiz',
        ogTitle: 'DrillQuiz - クイズ学習プラットフォーム',
        ogDescription: 'DrillQuiz ホームページ - 効率的なクイズ学習のためのオンラインプラットフォームです。',
        twitterTitle: 'DrillQuiz - クイズ学習プラットフォーム',
        twitterDescription: 'DrillQuiz ホームページ - 効率的なクイズ学習のためのオンラインプラットフォームです。'
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
        { property: 'og:url', content: 'https://us.drillquiz.com/' },
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
      recentResults: [],
      studies: [], // 스터디 데이터를 위한 데이터 프로퍼티 추가
      loading: true, // 로딩 상태 추가
      // 토스트 알림 관련
      showToast: false,
      toastMessage: '',
      toastType: 'success',
      toastIcon: '',
      // 확인 모달 관련
      showConfirmModal: false,
      confirmModalTitle: '',
      confirmModalMessage: '',
      pendingDeleteResult: null
    }
  },
  computed: {
    currentLanguage() {
      return getCurrentLanguage(this.$i18n);
    },
    isAdmin() {
      return isAdmin()
    },
    isStudyAdmin() {
      return hasStudyAdminRole()
    },
    isAuthenticated() {
      return Boolean(getCurrentUserFromPermissions())
    },
    filteredStudies() {
      const user = getCurrentUserFromPermissions()
      if (!user) {
        return this.studies.filter(study => study.is_public === true)
      }
      
      // admin_role 사용자는 모든 스터디에 접근 가능
      if (user.role === 'admin_role') {
        return this.studies
      }
      
      // 일반 사용자는 공개 스터디와 본인이 속한 스터디만
      const filtered = this.studies.filter(study => {
        
        // 공개 스터디는 항상 보임
        if (study.is_public === true) {
          return true
        }
        
        // 멤버인 경우도 보임
        if (study.members && Array.isArray(study.members)) {
          const isMember = study.members.some(member => {
            
            // user 필드가 있으면 user.id로 확인 (타입 변환)
            if (member.user) {
              const memberUserId = typeof member.user === 'object' ? member.user.id : member.user
              return String(memberUserId) === String(user.id)
            }
            
            // user 필드가 없으면 email로 확인
            if (member.email && user.email) {
              return member.email === user.email
            }
            
            // member_id로도 확인 (username과 비교)
            if (member.member_id && user.username) {
              return member.member_id === user.username
            }
            
            return false
          })
          
          if (isMember) {
            return true
          }
        }
        
        return false
      })
      
      // 기간이 지난 스터디 필터링 및 start_date 기준으로 정렬
      const now = new Date()
      const activeStudies = filtered.filter(study => {
        // end_date가 null이거나 end_date가 현재 날짜보다 이후인 경우만 포함
        if (!study.end_date) return true
        const endDate = new Date(study.end_date)
        return endDate >= now
      })
      
      // 사용자별 최근 진행률 기록 시간 기준으로 최신순 정렬
      return activeStudies.sort((a, b) => {
        // last_progress_recorded_at이 있으면 그것을 우선 사용 (사용자별 최근 활동 기준)
        if (a.last_progress_recorded_at && b.last_progress_recorded_at) {
          const dateA = new Date(a.last_progress_recorded_at)
          const dateB = new Date(b.last_progress_recorded_at)
          return dateB - dateA // 내림차순 (최신이 먼저)
        }
        
        // last_progress_recorded_at이 없는 경우 start_date로 fallback
        if (!a.start_date && !b.start_date) return 0
        if (!a.start_date) return 1
        if (!b.start_date) return -1
        
        const dateA = new Date(a.start_date)
        const dateB = new Date(b.start_date)
        return dateB - dateA // 내림차순 (최신이 먼저)
      })
    }
  },
  async mounted() {
    // 특정 도메인이고 비로그인 상태인 경우 해당 도메인 페이지로 리다이렉트
    const hostname = typeof window !== 'undefined' && window.location ? window.location.hostname : ''
    if (hostname.includes('devops') && !this.isAuthenticated) {
      debugLog('DevOps 도메인 + 비로그인 - devops-interview로 리다이렉트')
      this.$router.replace('/devops-interview')
      return
    }
    
    if (hostname.includes('leetcode') && !this.isAuthenticated) {
      debugLog('LeetCode 도메인 + 비로그인 - service-introduction으로 리다이렉트')
      this.$router.replace('/service-introduction')
      return
    }
    
    // 일반 도메인에서 세션이 없는 사용자이고 홈 메뉴 클릭이 아닌 경우 서비스 소개로 리다이렉트
    if (!hostname.includes('devops') && !hostname.includes('leetcode') && !this.isAuthenticated && !this.$route.query.fromHomeMenu) {
      debugLog('일반 도메인 + 세션이 없는 사용자 - 서비스 소개로 리다이렉트')
      this.$router.replace('/service-introduction')
      return
    }
    
    this.loading = true
    try {
      // 로그인한 사용자만 데이터 로드
      if (this.isAuthenticated) {
        // Random Practice를 위해 항상 최신 데이터 로드 (캐시 사용 안함)
        debugLog('Random Practice를 위해 항상 최신 데이터 로드')
        await this.loadData()
      }
      debugLog('isAdmin:', this.isAdmin)
    } finally {
      this.loading = false
    }
  },
  async beforeRouteEnter(to, from, next) {
    // 이어풀기 후 홈 화면으로 돌아올 때 데이터 새로고침
    next(async (vm) => {
      if (from.path.includes('/exam/') || from.path.includes('/take-exam/')) {
        // 캐시 무효화 후 새로고침
        vm.clearCache()
        await vm.loadData()
        vm.cacheData()
      }
    })
  },
  methods: {
    // 사용자가 언어를 변경할 때 호출되는 함수 (자동 호출 금지)
    async syncUserLanguagePreference() {
      // 로그인된 사용자인 경우 프로필에서 언어 설정 가져오기
      if (this.isAuthenticated) {
        try {
          console.log('🔍 [Home.vue] syncUserLanguagePreference 호출됨')
          console.log('🔍 [Home.vue] user-profile API 호출 시작: /api/user-profile/')
          const response = await axios.get('/api/user-profile/')
          console.log('🔍 [Home.vue] user-profile API 응답:', response.status)
          const userLanguage = response.data.language || 'en'
          
          // 도메인 기반 언어 우선순위 결정
          const hostname = typeof window !== 'undefined' && window.location ? window.location.hostname : ''
          let targetLanguage = userLanguage
          
          // 영어 도메인인 경우 영어 우선
          if (hostname.includes('us.') || hostname.includes('devops.') || hostname.includes('leetcode.')) {
            if (this.$i18n.locale === 'en') {
              // 이미 영어로 설정되어 있으면 변경하지 않음
              console.log('🔍 [Home.vue] 영어 도메인에서 이미 영어 설정됨 - 언어 변경 건너뜀')
              return
            }
            targetLanguage = 'en'
          }
          
          // 현재 언어와 다르면 변경
          if (targetLanguage !== this.$i18n.locale) {
            console.log(`🔍 [Home.vue] 언어 변경: ${this.$i18n.locale} → ${targetLanguage}`)
            await this.$changeLanguage(targetLanguage)
            debugLog(`✅ 홈 페이지에서 언어 설정 적용: ${targetLanguage}`)
          } else {
            console.log('🔍 [Home.vue] 언어 변경 불필요 - 이미 동일함')
          }
        } catch (error) {
          if (error.response && error.response.status === 401) {
            debugLog('인증되지 않은 사용자: 언어 설정 건너뜀')
          } else {
            debugLog('홈 페이지 언어 설정 적용 실패:', error, 'error')
          }
        }
      }
    },
    
    // 현재 사용자 언어에 맞는 스터디 제목 반환
    getStudyTitle(study) {
      if (!study) return '';
      
      const currentLanguage = getCurrentLanguage(this.$i18n);
      const fallbackValue = getLocalizedFallback(currentLanguage, 'title');
      return getLocalizedContent(study, 'title', currentLanguage, fallbackValue);
    },
    
    // 현재 사용자 언어에 맞는 스터디 목표 반환
    getStudyGoal(study) {
      if (!study) return '';
      
      const currentLanguage = getCurrentLanguage(this.$i18n);
      const fallbackValue = getLocalizedFallback(currentLanguage, 'description');
      return getLocalizedContent(study, 'goal', currentLanguage, fallbackValue);
    },
    
    // 현재 사용자 언어에 맞는 시험 제목 반환
    getLocalizedExamTitle(exam) {
      if (!exam) return '';
      
      const currentLanguage = getCurrentLanguage(this.$i18n);
      const fallbackValue = getLocalizedFallback(currentLanguage, 'title');
      return getLocalizedContent(exam, 'title', currentLanguage, fallbackValue);
    },
    
    async loadData(forceRefresh = false) {
      try {
        debugLog('Home.vue - loadData 시작 (forceRefresh:', forceRefresh, ')')
        debugLog('Home.vue - isAuthenticated:', this.isAuthenticated)
        
        // 강제 새로고침이거나 로그인된 사용자만 시험 결과와 스터디 데이터 로드
        if (!this.isAuthenticated) {
          debugLog('로그인되지 않은 사용자: 기본 데이터만 로드')
          // 공개 스터디만 로드
          const studiesResponse = await axios.get('/api/studies/')
          debugLog('공개 스터디 응답:', studiesResponse.data)
          this.studies = studiesResponse.data.results || studiesResponse.data || []
          this.recentResults = []
          debugLog('공개 스터디 설정 완료:', this.studies)
          return
        }

        debugLog('로그인된 사용자: 전체 데이터 로드 시작')
        
        // 시험 결과와 스터디 데이터를 병렬로 로드 (서로 독립적)
        const [examResultsResponse, studiesResponse] = await Promise.all([
          axios.get('/api/exam-results/', {
            headers: forceRefresh ? { 'Cache-Control': 'no-cache' } : {}
          }),
          axios.get('/api/studies/', {
            headers: forceRefresh ? { 'Cache-Control': 'no-cache' } : {}
          })
        ])
        
        debugLog('전체 시험 결과:', examResultsResponse.data)
        
        // 페이지네이션된 응답 처리
        const results = examResultsResponse.data.results || examResultsResponse.data || []
        debugLog('원본 시험 결과:', results)
        this.recentResults = results.slice(0, 5) // 최근 5개만 표시
        debugLog('설정된 recentResults:', this.recentResults)
        
        debugLog('스터디 응답:', studiesResponse.data)
        
        // 모든 스터디 로드
        const allStudies = studiesResponse.data.results || studiesResponse.data || []
        
        // 현재 사용자가 가입된 Study만 필터링
        if (this.isAuthenticated) {
          const user = getCurrentUserFromPermissions()
          if (user) {
            this.studies = allStudies.filter(study => {
              // 멤버 체크: 타입 변환하여 비교
              const isMember = Array.isArray(study.members) &&
                study.members.some(member => {
                  if (!member.user) return false
                  const memberUserId = typeof member.user === 'object' ? member.user.id : member.user
                  return String(memberUserId) === String(user.id)
                })
              
              // 생성자 체크: 타입 변환하여 비교
              const isCreator = study.created_by && (
                (typeof study.created_by === 'object' && String(study.created_by.id) === String(user.id)) ||
                String(study.created_by) === String(user.id)
              )
              
              return isMember || isCreator
            })
            debugLog('사용자별 Study 필터링 완료:', {
              전체: allStudies.length,
              가입된: this.studies.length,
              사용자ID: user.id
            })
          } else {
            this.studies = []
            debugLog('사용자 정보를 찾을 수 없음')
          }
        } else {
          // 로그인하지 않은 사용자는 공개 스터디만
          this.studies = allStudies.filter(study => study.is_public === true)
        }
        
        debugLog('로드된 스터디:', this.studies)
        
        // 각 스터디의 진행률 상세 로그
        this.studies.forEach((study, index) => {
          debugLog(`스터디 ${index + 1}:`, {
            id: study.id,
            title: study.title_ko || study.title_en || 'Unknown',
            overall_progress: study.overall_progress,
            overall_progress_type: typeof study.overall_progress,
            tasks_count: study.tasks ? study.tasks.length : 0
          })
        })
        
        debugLog('필터링된 스터디:', this.filteredStudies)
        
        debugLog('Home.vue - loadData 완료')
      } catch (error) {
        debugLog('Home.vue - loadData 오류:', error, 'error')
        if (error.response && error.response.status === 401) {
          debugLog('인증되지 않은 사용자: 공개 데이터만 로드')
          // 401 오류 시 공개 스터디만 로드
          try {
            const studiesResponse = await axios.get('/api/studies/')
            this.studies = studiesResponse.data.results || studiesResponse.data || []
            this.recentResults = []
          } catch (studiesError) {
            debugLog('스터디 데이터 로드 실패:', studiesError, 'error')
            this.studies = []
            this.recentResults = []
          }
        } else {
          debugLog('데이터를 불러오는데 실패했습니다:', error, 'error')
          this.recentResults = []
          this.studies = []
        }
      }
    },
    formatDate(dateString) {
      return formatLocalDate(dateString)
    },
    formatElapsed(sec) {
      if (!sec) return '0:00'
      const m = Math.floor(sec / 60)
      const s = sec % 60
      return `${m}:${s.toString().padStart(2, '0')}`
    },
    async deleteResult(result) {
      // 확인 모달 표시
      this.pendingDeleteResult = result
      this.confirmModalTitle = this.$t('confirm.deleteExamResult') || '시험 결과 삭제'
      this.confirmModalMessage = this.$t('confirm.deleteExamResultMessage') || '이 시험 결과를 삭제하시겠습니까?'
      this.showConfirmModal = true
    },
    async confirmDeleteResult() {
      if (!this.pendingDeleteResult) return
      
      const result = this.pendingDeleteResult
      this.showConfirmModal = false
      this.pendingDeleteResult = null
      
      try {
        await axios.delete(`/api/exam-result/${result.id}/`)
        // 삭제 후 목록 갱신
        this.recentResults = this.recentResults.filter(r => r.id !== result.id)
        this.$toast?.success?.(this.$t('home.alerts.deleteSuccess') || '시험 결과가 삭제되었습니다.')
      } catch (error) {
        this.$toast?.error?.(this.$t('home.alerts.deleteFailed'))
      }
    },
    cancelConfirmModal() {
      this.showConfirmModal = false
      this.pendingDeleteResult = null
    },
    async recordProgress(studyId) {
      // 인증되지 않은 사용자는 진행율 기록하지 않음
      if (!this.isAuthenticated) {
        debugLog('인증되지 않은 사용자 - 진행율 기록 건너뜀')
        return
      }
      
      try {
        await axios.post('/api/record-study-progress/', {
          study_id: studyId,
          page_type: 'home'
        })
              } catch (error) {
          debugLog('진행율 기록 실패:', error, 'error')
        }
    },
    
    // 토스트 알림 메서드들
    showToastNotification(message, type = 'success', icon = null) {
      this.toastMessage = message
      this.toastType = type
      this.toastIcon = icon || this.getToastIcon(type)
      this.showToast = true
      
      // 3초 후 자동으로 숨기기
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
    

    
    async goToRandomPractice() {
      console.log('🚀 goToRandomPractice 메서드 시작!')

      // 로그인 확인
      if (!this.isAuthenticated) {
        console.log('❌ 로그인되지 않음 - login 페이지로 이동')
        this.$router.push('/login')
        return
      }

      // 데이터가 아직 로드되지 않았으면 로드 대기
      if (this.loading) {
        console.log('데이터 로딩 중 - 잠시 대기')
        this.showToastNotification('데이터를 불러오는 중입니다. 잠시 후 다시 시도해주세요.', 'info')
        return
      }

      // 캐시 무효화 및 데이터 강제 로드
      console.log('Random Practice 클릭 - 캐시 무효화 및 데이터 강제 로드 시작')

      // 캐시된 데이터 무효화
      this.studies = []
      this.recentResults = []

      // 세션 스토리지 캐시도 무효화
      sessionStorage.removeItem('homeData')
      console.log('세션 스토리지 캐시 무효화 완료')

      // 로컬 스토리지 캐시 설정도 무효화
      localStorage.setItem('cacheDisabled', 'true')
      console.log('로컬 스토리지 캐시 비활성화 완료')

      try {
        // 캐시 무시하고 최신 데이터 로드
        this.loading = true
        await this.loadData(true) // forceRefresh = true
        this.loading = false
        console.log('데이터 강제 로드 후 studies:', this.studies)
        console.log('데이터 강제 로드 후 studies.length:', this.studies ? this.studies.length : 'undefined')
      } catch (error) {
        console.error('데이터 강제 로드 실패:', error)
        this.loading = false
      }

      // 디버깅: studies 상태 확인
      console.log('goToRandomPractice - studies:', this.studies)
      console.log('goToRandomPractice - studies.length:', this.studies ? this.studies.length : 'undefined')
      console.log('goToRandomPractice - filteredStudies:', this.filteredStudies)
      console.log('goToRandomPractice - loading:', this.loading)

      // 가입된 Study가 있는지 확인
      if (!this.studies || this.studies.length === 0) {
        console.log('Study가 없음 - study-management로 이동')
        this.showToastNotification(this.$t('home.randomPractice.noStudies') || '가입된 Study가 없습니다. Study Management에서 Study를 생성하거나 가입해주세요.', 'warning')
        // 2초 후 study-management 페이지로 이동
        setTimeout(() => {
          this.$router.push('/study-management')
        }, 2000)
        return
      }

      console.log('Study가 있음 - random-practice로 이동')
      // Study가 있으면 Random Practice 페이지로 이동
      this.$router.push('/random-practice')
  },
  
  navigateToExamManagement() {
    // 스크롤 없이 네비게이션
    this.$router.push('/exam-management').catch(() => {})
    // 네비게이션 후 스크롤 위치 유지
    this.$nextTick(() => {
      window.scrollTo(0, window.scrollY || 0)
    })
  },
  
  async goToDailyExam() {
      // 로그인 확인
      if (!this.isAuthenticated) {
        this.$router.push('/login')
        return
      }
      
      try {
        // 기존 Daily Exam API 호출 (기존 시험이 있으면 그 시험으로, 없으면 새로 생성)
        const response = await axios.get('/api/daily-exam/')
        
        if (response.data.success) {
          const examData = response.data.exam
          
          // 기존 시험이 있으면 해당 시험으로 이동, 새로 생성된 시험이면 새 시험으로 이동
          this.$router.push(`/exam-detail/${examData.id}`)
        } else {
          this.showToastNotification(this.$t('home.dailyExam.loadFailed'), 'error')
        }
      } catch (error) {
        debugLog('Daily Exam 이동 실패:', error, 'error')
        if (error.response && error.response.data && error.response.data.error) {
          let errorMessage = error.response.data.error
          
          // 백엔드에서 번역 키를 반환한 경우 번역 처리
          if (errorMessage.includes('home.dailyExam.')) {
            try {
              errorMessage = this.$t(errorMessage)
            } catch (e) {
              // 번역 키가 없으면 원본 메시지 사용
              debugLog('Translation key not found:', errorMessage, 'warn')
            }
          }
          
          // subscribed exams가 없으면 profile 페이지로 이동
          if (error.response.data.error === 'home.dailyExam.noSubscribedExams') {
            this.showToastNotification(errorMessage, 'error')
            // 2초 후 profile 페이지로 이동
            setTimeout(() => {
              this.$router.push('/profile')
            }, 2000)
            return
          }
          
          this.showToastNotification(errorMessage, 'error')
        } else {
          this.showToastNotification(this.$t('home.dailyExam.loadFailed'), 'error')
        }
      }
    },
    
    // 캐시 관련 메서드들
    getCachedData() {
      try {
        const cached = sessionStorage.getItem('homeData')
        if (cached) {
          const data = JSON.parse(cached)
          // 캐시 유효성 검사 (5분)
          const now = Date.now()
          if (now - data.timestamp < 5 * 60 * 1000) {
            return data
          }
        }
              } catch (error) {
          debugLog('캐시 데이터 파싱 오류:', error, 'error')
        }
      return null
    },
    
    cacheData() {
      // 전역 캐시 설정 확인
      const cacheEnabled = localStorage.getItem('cacheEnabled') !== 'false'
      const cacheDisabled = sessionStorage.getItem('cacheDisabled') === 'true'
      
      if (!cacheEnabled || cacheDisabled) {
        debugLog('캐시가 비활성화되어 있어 저장하지 않습니다.')
        return
      }
      
      try {
        // 캐시 저장 전에 오래된 캐시 정리
        this.cleanupOldCache()
        
        const data = {
          recentResults: this.recentResults.slice(0, 10), // 최근 10개만 캐시
          studies: this.studies,
          timestamp: Date.now()
        }
        
        const cacheString = JSON.stringify(data)
        
        // 캐시 크기 확인 (2MB 제한)
        if (cacheString.length > 2 * 1024 * 1024) {
          debugLog('홈 캐시 데이터가 너무 큽니다. 캐시를 저장하지 않습니다.', null, 'warn')
          return
        }
        
        sessionStorage.setItem('homeData', cacheString)
        debugLog('홈 데이터 캐시 저장됨 (크기:', Math.round(cacheString.length / 1024), 'KB)')
      } catch (error) {
        debugLog('캐시 저장 오류:', error, 'error')
        this.clearCache()
      }
    },
    
    shouldRefreshCache() {
      // forceRefreshHome 플래그가 true이거나 캐시가 5분 이상 지났으면 새로고침
      const forceRefresh = sessionStorage.getItem('forceRefreshHome') === 'true'
      const cacheAge = this.getCacheAge()
      const shouldRefresh = forceRefresh || cacheAge > 5 * 60 * 1000 // 5분
      
      if (forceRefresh) {
        console.log('🔄 홈페이지 강제 새로고침 플래그 감지')
        sessionStorage.removeItem('forceRefreshHome') // 플래그 제거
      }
      
      return shouldRefresh
    },
    
    clearCache() {
      sessionStorage.removeItem('homeData')
      sessionStorage.removeItem('forceRefreshHome')
      debugLog('홈 데이터 캐시 삭제됨')
    },
    
    getCacheAge() {
      try {
        const cachedData = sessionStorage.getItem('homeData')
        if (cachedData) {
          const data = JSON.parse(cachedData)
          if (data.timestamp) {
            return Date.now() - data.timestamp
          }
        }
      } catch (e) {
        // 파싱 실패 시 캐시 무효화
        return Infinity
      }
      return Infinity // 캐시가 없으면 무한대로 설정하여 새로고침 유도
    },
    
    cleanupOldCache() {
      try {
        // 모든 캐시 키 확인
        const keys = Object.keys(sessionStorage)
        const now = Date.now()
        const maxAge = 10 * 60 * 1000 // 10분
        
        keys.forEach(key => {
          if (key.includes('Cache') || key.includes('Data')) {
            try {
              const cached = sessionStorage.getItem(key)
              if (cached) {
                const data = JSON.parse(cached)
                if (data.timestamp && (now - data.timestamp > maxAge)) {
                  sessionStorage.removeItem(key)
                  debugLog('오래된 캐시 삭제:', key)
                }
              }
            } catch (e) {
              // 파싱 실패 시 삭제
              sessionStorage.removeItem(key)
              debugLog('손상된 캐시 삭제:', key)
            }
          }
        })
      } catch (error) {
        debugLog('캐시 정리 중 오류:', error, 'error')
      }
    },
    
    // 데이터 새로고침 메서드
    async refreshData() {
      this.loading = true
      try {
        this.clearCache()
        await this.loadData()
        this.cacheData()
      } finally {
        this.loading = false
      }
    },

    getStudyStatus(study) {
      if (study.overall_progress === null) {
        return 'inactive';
      } else if (study.overall_progress === 100) {
        return 'completed';
      } else {
        return 'active';
      }
    },

    getStudyStatusText(study) {
      if (study.is_completed) {
        return this.$t('home.study.status.completed');
      } else {
        return this.$t('home.study.status.inProgress');
      }
    }
  }
}
</script>

<style scoped>
/* Modern Home Styles */
.home-modern {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  color: white;
}

.home-content {
  min-height: 100vh;
}

/* Hero Section */
.hero-section {
  padding: 40px 20px 30px;
  text-align: center;
  color: white;
}

@media (max-width: 768px) {
  .hero-section {
    padding: 15px 15px 5px;
  }
}

.hero-content {
  max-width: 800px;
  margin: 0 auto;
}

.hero-title {
  font-size: 3.5rem;
  font-weight: 700;
  margin-bottom: 20px;
  background: linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 1.5rem;
  font-weight: 400;
  margin-bottom: 15px;
  opacity: 0.9;
}

.hero-description {
  font-size: 1.1rem;
  opacity: 0.8;
  line-height: 1.6;
}

/* Main Container */
.main-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px 30px;
}

@media (max-width: 768px) {
  .main-container {
    padding: 0 8px 15px;
  }
}

/* Section Headers */
.section-header {
  text-align: center;
  margin-bottom: 20px;
  color: white;
}

@media (max-width: 768px) {
  .section-header {
    margin-bottom: 10px;
  }
}

.section-title {
  font-size: 2.5rem;
  font-weight: 600;
  margin-bottom: 10px;
}

.section-subtitle {
  font-size: 1.1rem;
  opacity: 0.8;
}

/* Features Section */
.features-section {
  margin-bottom: 30px;
}

@media (max-width: 768px) {
  .features-section {
    margin-bottom: 15px;
  }
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

@media (max-width: 768px) {
  .features-grid {
    gap: 10px;
    margin-top: 5px;
  }
}

.feature-card {
  background: white;
  border-radius: 20px;
  padding: 25px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  text-align: center;
}

@media (max-width: 768px) {
  .feature-card {
    padding: 15px;
  }
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

.feature-icon {
  width: 70px;
  height: 70px;
  margin: 0 auto 15px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.8rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.feature-icon:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
  background: linear-gradient(135deg, #5a32a3 0%, #6a4c93 100%);
}

.feature-icon:active {
  transform: scale(0.98);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.6);
}

/* 시험 관리 카드 - 주황색 계열 스타일 */
.exam-management-card .exam-management-icon {
  background: linear-gradient(135deg, #ff8c42 0%, #ff6b35 100%);
}

.exam-management-card .exam-management-icon:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 20px rgba(255, 140, 66, 0.5);
  background: linear-gradient(135deg, #ff6b35 0%, #ff5722 100%);
}

.exam-management-card .exam-management-icon:active {
  transform: scale(0.98);
  box-shadow: 0 4px 15px rgba(255, 140, 66, 0.6);
}

.exam-management-card .exam-management-btn {
  background: linear-gradient(135deg, #ff8c42 0%, #ff6b35 100%);
  box-shadow: 0 4px 15px rgba(255, 140, 66, 0.3);
}

.exam-management-card .exam-management-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 140, 66, 0.4);
  background: linear-gradient(135deg, #ff6b35 0%, #ff5722 100%);
  color: white;
  text-decoration: none;
}

@media (max-width: 768px) {
  .feature-icon {
    margin: 0 auto 3px;
  }
}

.feature-title {
  font-size: 1.4rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 8px;
}

@media (max-width: 768px) {
  .feature-title {
    margin-bottom: 3px;
  }
}

.feature-description {
  color: #6c757d;
  line-height: 1.5;
  margin-bottom: 15px;
}

@media (max-width: 768px) {
  .feature-description {
    margin-bottom: 3px;
  }
}

.feature-btn {
  display: inline-block;
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  text-decoration: none;
  border-radius: 25px;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.feature-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
  color: white;
  text-decoration: none;
}

/* Loading Section */
.loading-section {
  text-align: center;
  padding: 40px;
  color: white;
}

/* Data Sections */
.data-section {
  margin-bottom: 60px;
}

@media (max-width: 768px) {
  .data-section {
    margin-bottom: 10px;
  }
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: white;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 20px;
  opacity: 0.6;
}

.empty-state p {
  font-size: 1.1rem;
  opacity: 0.8;
}

/* Data Table */
.data-table {
  background: white;
  border-radius: 15px;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.table-header {
  display: grid;
  grid-template-columns: 2fr 3fr 1.5fr 1fr;
  background: #f8f9fa;
  padding: 15px 20px;
  font-weight: 600;
  color: #2c3e50;
  border-bottom: 1px solid #e9ecef;
}

/* Recent Results Table specific styling */
.data-section:nth-child(3) .table-header,
.data-section:nth-child(3) .table-row {
  grid-template-columns: 2fr 1fr 0.8fr 0.8fr 1.2fr 1fr;
}

.table-body {
  max-height: 400px;
  overflow-y: auto;
}

.table-row {
  display: grid;
  grid-template-columns: 2fr 3fr 1.5fr 1fr;
  padding: 15px 20px;
  border-bottom: 1px solid #f1f3f4;
  transition: background-color 0.2s ease;
}

.table-row:hover {
  background-color: #f8f9fa;
}

.table-cell {
  display: flex;
  align-items: center;
  color: #2c3e50;
}

/* Period column specific styling */
.table-row .table-cell:nth-child(3) {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

/* Recent Results Table cell styling */
.data-section:nth-child(3) .table-cell {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
  font-size: 0.9rem;
}

.data-section:nth-child(3) .table-cell:first-child {
  white-space: normal;
  word-break: break-word;
}

/* Score and Elapsed column specific styling */
.data-section:nth-child(3) .table-cell:nth-child(2),
.data-section:nth-child(3) .table-cell:nth-child(5) {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

.table-link {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s ease;
}

.table-link:hover {
  color: #764ba2;
  text-decoration: underline;
}

.progress-link {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s ease;
}

.progress-link:hover {
  color: #764ba2;
  text-decoration: underline;
}

/* Description Cell Styles */
.description-cell {
  max-width: 300px;
  overflow: hidden;
}

.description-text {
  color: #6c757d;
  font-size: 0.9rem;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.description-empty {
  color: #adb5bd;
  font-style: italic;
  font-size: 0.9rem;
}

/* Action Buttons */
.action-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.retake-btn {
  background: #ffc107;
  color: #212529;
}

.retake-btn:hover {
  background: #e0a800;
  transform: translateY(-1px);
}

.continue-btn {
  background: #17a2b8;
  color: white;
}

.continue-btn:hover {
  background: #138496;
  transform: translateY(-1px);
}

.continue-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
  transform: none;
}

/* Toast Notifications - 기본 스타일은 공통 CSS (mobile-buttons.css)에 정의됨 */

/* 타입별 스타일은 공통 CSS (mobile-buttons.css)에 정의됨 */

.toast-content {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.toast-close {
  background: none;
  border: none;
  color: inherit;
  font-size: 18px;
  cursor: pointer;
  padding: 0;
  margin-left: 15px;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.toast-close:hover {
  opacity: 1;
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

/* Responsive Design */
@media (max-width: 768px) {
  .hero-title {
    font-size: 2.5rem;
  }
  
  .hero-subtitle {
    font-size: 1.2rem;
  }
  
  .section-title {
    font-size: 2rem;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  
  .feature-card {
    padding: 25px;
  }
  
  .table-header,
  .table-row {
    grid-template-columns: 1fr;
    gap: 10px;
  }
  
  .table-header {
    display: none;
  }
  
  .table-row {
    padding: 15px;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    margin-bottom: 10px;
  }
  
  .table-cell {
    padding: 5px 0;
  }
  
  .table-cell:before {
    content: attr(data-label) ": ";
    font-weight: 600;
    color: #6c757d;
  }
}

@media (max-width: 480px) {
  .hero-title {
    font-size: 2rem;
  }
  
  .hero-subtitle {
    font-size: 1rem;
  }
  
  .main-container {
    padding: 0 10px 30px;
  }
  
  .feature-card {
    padding: 20px;
  }
  
  .feature-icon {
    width: 60px;
    height: 60px;
    font-size: 1.5rem;
  }
}

/* Mobile Cards Styles */
.mobile-cards {
  display: none; /* 기본적으로 숨김 */
  grid-template-columns: 1fr;
  gap: 12px;
  margin-top: 10px;
  padding: 0 8px;
  width: 100%;
  box-sizing: border-box;
  max-width: 100vw;
  overflow-x: hidden;
}

/* 모바일에서 테이블 숨기고 카드 보이기 */
@media (max-width: 768px) {
  .data-section .data-table {
    display: none;
  }
  
  .mobile-cards {
    display: grid;
  }
  
  .data-section {
    overflow-x: hidden;
    width: 100%;
    box-sizing: border-box;
    margin-bottom: 10px;
  }
  
  .home-modern {
    overflow-x: hidden;
    width: 100%;
  }
  
  .home-content {
    overflow-x: hidden;
    width: 100%;
  }
  
  /* 전체 페이지 너비 제한 */
  body, html {
    overflow-x: hidden;
    width: 100%;
  }
}

.mobile-card {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 8px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  min-height: 100px;
}

.mobile-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
}

.mobile-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 5px;
}

.mobile-card-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #343a40;
  margin: 0;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.3;
  max-width: calc(100% - 80px);
}

.mobile-card-title-link {
  color: #007bff;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.2s ease;
  cursor: pointer;
  display: block;
  padding: 2px 0;
  border-radius: 4px;
  font-size: 1rem;
}

.mobile-card-title-link:hover {
  color: #0056b3;
  text-decoration: underline;
  background-color: rgba(0, 123, 255, 0.1);
}

.mobile-card-title-link:active {
  color: #004085;
  transform: translateY(1px);
}

/* exam title 링크 스타일 */
.mobile-card-header .mobile-card-title-link {
  color: #6f42c1;
  font-size: 0.95rem;
  font-weight: 700;
}

.mobile-card-header .mobile-card-title-link:hover {
  color: #5a32a3;
  background-color: rgba(111, 66, 193, 0.1);
}

.mobile-card-header .mobile-card-title-link:active {
  color: #4a2d8a;
}

.mobile-card-progress {
  font-size: 0.9rem;
  font-weight: 600;
  color: #6f42c1;
  background: #f8f9fa;
  padding: 4px 8px;
  border-radius: 12px;
  border: 1px solid #e9ecef;
}

.mobile-card-info {
  font-size: 0.85rem;
  color: #6c757d;
  margin-bottom: 0px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
}

.mobile-card-date {
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100%;
  margin-bottom: 5px;
}

.mobile-card-status {
  padding: 3px 8px;
  border-radius: 10px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  align-self: flex-start;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mobile-card-status.active {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.mobile-card-status.completed {
  background-color: #d1ecf1;
  color: #0c5460;
  border: 1px solid #bee5eb;
}

.mobile-card-status.inactive {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.mobile-card-status-container {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 0px;
  justify-content: space-between;
}

.mobile-card-status-container .mobile-card-btn.progress {
  padding: 4px 8px;
  font-size: 0.75rem;
  min-height: 24px;
  min-width: 60px;
  max-width: 70px;
  border-radius: 10px;
  background: #6f42c1;
  color: white;
  font-weight: 600;
  text-decoration: none;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.mobile-card-status-container .mobile-card-btn.progress:hover {
  background: #5a32a3;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(111, 66, 193, 0.3);
}

.mobile-card-actions {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-top: 0px;
  width: 100%;
}

.mobile-card-btn {
  flex: 1;
  padding: 12px 16px;
  border: none;
  border-radius: 15px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  text-align: center;
  text-decoration: none;
  transition: all 0.2s ease;
  white-space: nowrap;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1.2;
}

.mobile-card-btn.progress {
  background: #6f42c1;
  color: white;
  font-weight: 600;
}

.mobile-card-btn.progress:hover {
  background: #5a32a3;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(111, 66, 193, 0.3);
}

.mobile-card-btn.retry {
  background: #ffc107;
  color: #212529;
  font-weight: 600;
}

.mobile-card-btn.retry:hover {
  background: #e0a800;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 193, 7, 0.3);
}

.mobile-card-btn.continue {
  background: #17a2b8;
  color: white;
  font-weight: 600;
}

.mobile-card-btn.continue:hover {
  background: #138496;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(23, 162, 184, 0.3);
}

.mobile-card-btn:not(.progress):not(.retry):not(.continue) {
  background: #007bff;
  color: white;
  font-weight: 600;
}

.mobile-card-btn:not(.progress):not(.retry):not(.continue):hover {
  background: #0056b3;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3);
}

.mobile-card-btn.continue:disabled {
  background: #6c757d;
  color: #adb5bd;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}
</style>