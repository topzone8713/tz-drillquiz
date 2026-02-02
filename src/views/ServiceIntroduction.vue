<template>
  <div class="service-introduction">
    <div class="container-fluid">
      <!-- 헤더 섹션 -->
      <div class="jumbotron bg-primary text-white text-center py-5 mb-5">
        <div class="container">
          <h1 class="display-4 mb-4">{{ $t('serviceIntro.title') }}</h1>
          <p class="lead">{{ $t('serviceIntro.subtitle') }}</p>
        </div>
      </div>

      <!-- 메인 콘텐츠 -->
      <div class="container">
        <!-- 1. 반복 학습의 새로운 방식 -->
        <div class="row mb-5">
          <div class="col-lg-8 mx-auto">
            <div class="card shadow-sm">
              <div class="card-body p-4">
                <div class="d-flex align-items-center mb-3">
                  <div class="feature-icon bg-primary text-white rounded-circle d-flex align-items-center justify-content-center me-3" style="width: 60px; height: 60px;">
                    <i class="fas fa-redo fa-lg"></i>
                  </div>
                  <h2 class="card-title mb-0">{{ $t('serviceIntro.feature1.title') }}</h2>
                </div>
                <p class="card-text mb-4">{{ $t('serviceIntro.feature1.description') }}</p>
                
                <div class="row">
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-primary">{{ $t('serviceIntro.feature1.drain.title') }}</h5>
                      <p class="text-muted">{{ $t('serviceIntro.feature1.drain.description') }}</p>
                    </div>
                  </div>
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-primary">{{ $t('serviceIntro.feature1.memory.title') }}</h5>
                      <p class="text-muted">{{ $t('serviceIntro.feature1.memory.description') }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 2. 인터뷰형 학습 지원 -->
        <div class="row mb-5">
          <div class="col-lg-8 mx-auto">
            <div class="card shadow-sm">
              <div class="card-body p-4">
                <div class="d-flex align-items-center mb-3">
                  <div class="feature-icon bg-success text-white rounded-circle d-flex align-items-center justify-content-center me-3" style="width: 60px; height: 60px;">
                    <i class="fas fa-comments fa-lg"></i>
                  </div>
                  <h2 class="card-title mb-0">{{ $t('serviceIntro.feature2.title') }}</h2>
                </div>
                <p class="card-text mb-4">{{ $t('serviceIntro.feature2.description') }}</p>
                
                <div class="row">
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-success">{{ $t('serviceIntro.feature2.interview.title') }}</h5>
                      <p class="text-muted">{{ $t('serviceIntro.feature2.interview.description') }}</p>
                    </div>
                  </div>
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-success">{{ $t('serviceIntro.feature2.followup.title') }}</h5>
                      <p class="text-muted">{{ $t('serviceIntro.feature2.followup.description') }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 3. 개인화된 오답 관리 -->
        <div class="row mb-5">
          <div class="col-lg-8 mx-auto">
            <div class="card shadow-sm">
              <div class="card-body p-4">
                <div class="d-flex align-items-center mb-3">
                  <div class="feature-icon bg-warning text-white rounded-circle d-flex align-items-center justify-content-center me-3" style="width: 60px; height: 60px;">
                    <i class="fas fa-envelope fa-lg"></i>
                  </div>
                  <h2 class="card-title mb-0">{{ $t('serviceIntro.feature3.title') }}</h2>
                </div>
                <p class="card-text mb-4">{{ $t('serviceIntro.feature3.description') }}</p>
                
                <div class="row">
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-warning">{{ $t('serviceIntro.feature3.email.title') }}</h5>
                      <p class="text-muted">{{ $t('serviceIntro.feature3.email.description') }}</p>
                    </div>
                  </div>
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-warning">{{ $t('serviceIntro.feature3.habit.title') }}</h5>
                      <p class="text-muted">{{ $t('serviceIntro.feature3.habit.description') }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 4. 학습 효과 극대화 -->
        <div class="row mb-5 mb-md-0">
          <div class="col-lg-8 mx-auto">
            <div class="card shadow-sm">
              <div class="card-body p-4">
                <div class="d-flex align-items-center mb-3">
                  <div class="feature-icon bg-info text-white rounded-circle d-flex align-items-center justify-content-center me-3" style="width: 60px; height: 60px;">
                    <i class="fas fa-chart-line fa-lg"></i>
                  </div>
                  <h2 class="card-title mb-0">{{ $t('serviceIntro.feature4.title') }}</h2>
                </div>
                <p class="card-text mb-4">{{ $t('serviceIntro.feature4.description') }}</p>
                
                <div class="row">
                  <div class="col-md-4 mb-3">
                    <div class="feature-item text-center">
                      <div class="feature-icon-small bg-primary text-white rounded-circle d-inline-flex align-items-center justify-content-center mb-2" style="width: 40px; height: 40px;">
                        <i class="fas fa-redo"></i>
                      </div>
                      <h6 class="text-primary">{{ $t('serviceIntro.feature4.drain.title') }}</h6>
                      <p class="text-muted small">{{ $t('serviceIntro.feature4.drain.description') }}</p>
                    </div>
                  </div>
                  <div class="col-md-4 mb-3">
                    <div class="feature-item text-center">
                      <div class="feature-icon-small bg-success text-white rounded-circle d-inline-flex align-items-center justify-content-center mb-2" style="width: 40px; height: 40px;">
                        <i class="fas fa-comments"></i>
                      </div>
                      <h6 class="text-success">{{ $t('serviceIntro.feature4.interview.title') }}</h6>
                      <p class="text-muted small">{{ $t('serviceIntro.feature4.interview.description') }}</p>
                    </div>
                  </div>
                  <div class="col-md-4 mb-3">
                    <div class="feature-item text-center">
                      <div class="feature-icon-small bg-warning text-white rounded-circle d-inline-flex align-items-center justify-content-center mb-2" style="width: 40px; height: 40px;">
                        <i class="fas fa-envelope"></i>
                      </div>
                      <h6 class="text-warning">{{ $t('serviceIntro.feature4.email.title') }}</h6>
                      <p class="text-muted small">{{ $t('serviceIntro.feature4.email.description') }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- CTA 섹션 - 로그인하지 않은 사용자에게만 표시 -->
        <div v-if="!isAuthenticated" class="row mb-0">
          <div class="col-lg-8 mx-auto text-center">
            <div class="card bg-light">
              <div class="card-body p-5">
                <h3 class="card-title mb-4">{{ $t('serviceIntro.cta.title') }}</h3>
                <p class="card-text mb-4">{{ $t('serviceIntro.cta.description') }}</p>
                <div class="d-flex justify-content-center gap-3 flex-wrap">
                  <router-link to="/register" class="btn btn-primary btn-lg">
                    <i class="fas fa-user-plus me-md-2"></i><span class="d-none d-md-inline">{{ $t('serviceIntro.cta.register') }}</span>
                  </router-link>
                  <router-link to="/login" class="btn btn-outline-primary btn-lg">
                    <i class="fas fa-sign-in-alt me-md-2"></i><span class="d-none d-md-inline">{{ $t('serviceIntro.cta.login') }}</span>
                  </router-link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import authService from '@/services/authService'

export default {
  name: 'ServiceIntroduction',
  computed: {
    isAuthenticated() {
      return authService.isAuthenticatedSync()
    }
  },
  metaInfo() {
    const currentLang = this.$i18n?.locale || 'en'
    
    // 언어별 메타 정보 매핑
    const metaByLanguage = {
      'ko': {
        title: '서비스 소개 - DrillQuiz',
        description: 'DrillQuiz의 혁신적인 학습 기능들을 소개합니다. 반복 학습, 인터뷰형 학습, 개인화된 오답 관리를 통해 학습 효과를 극대화하세요.',
        keywords: 'DrillQuiz, 서비스 소개, 반복 학습, 인터뷰형 학습, 오답 관리, 학습 효과'
      },
      'en': {
        title: 'Service Introduction - DrillQuiz',
        description: 'Discover DrillQuiz\'s innovative learning features. Maximize your learning effectiveness through repetitive learning, interview-style learning, and personalized error management.',
        keywords: 'DrillQuiz, service introduction, repetitive learning, interview learning, error management, learning effectiveness'
      },
      'es': {
        title: 'Introducción al Servicio - DrillQuiz',
        description: 'Descubre las funciones innovadoras de aprendizaje de DrillQuiz. Maximiza tu efectividad de aprendizaje a través del aprendizaje repetitivo, aprendizaje estilo entrevista y gestión personalizada de errores.',
        keywords: 'DrillQuiz, introducción al servicio, aprendizaje repetitivo, aprendizaje de entrevista, gestión de errores, efectividad del aprendizaje'
      },
      'zh': {
        title: '服务介绍 - DrillQuiz',
        description: '了解 DrillQuiz 的创新学习功能。通过重复学习、面试式学习和个性化错题管理，最大化您的学习效果。',
        keywords: 'DrillQuiz, 服务介绍, 重复学习, 面试学习, 错题管理, 学习效果'
      },
      'ja': {
        title: 'サービス紹介 - DrillQuiz',
        description: 'DrillQuizの革新的な学習機能をご紹介します。反復学習、インタビュー形式の学習、パーソナライズされた誤答管理を通じて学習効果を最大化します。',
        keywords: 'DrillQuiz, サービス紹介, 反復学習, インタビュー学習, 誤答管理, 学習効果'
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
        }
      ]
    }
  }
}
</script>

<style scoped>
.service-introduction {
  /* min-height 제거: App.vue의 flexbox 레이아웃이 전체 높이를 관리 */
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding-bottom: 0; /* footer와의 공백 제거 */
}

/* 마지막 섹션의 하단 마진 제거 */
.service-introduction .container > .row:last-child {
  margin-bottom: 0 !important;
}

.jumbotron {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border-radius: 0;
}

.feature-icon {
  font-size: 1.5rem;
}

.feature-icon-small {
  font-size: 1rem;
}

.card {
  border: none;
  border-radius: 15px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 25px rgba(0,0,0,0.1) !important;
}

.feature-item {
  padding: 1rem 0;
}

.btn {
  border-radius: 25px;
  padding: 12px 30px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0,0,0,0.2);
}

@media (max-width: 768px) {
  .jumbotron {
    padding: 3rem 1rem !important;
  }
  
  .display-4 {
    font-size: 2rem;
  }
  
  .lead {
    font-size: 1rem;
  }
  
  .card-body {
    padding: 1.5rem !important;
  }
  
  .feature-icon {
    width: 50px !important;
    height: 50px !important;
    font-size: 1.2rem;
  }
  
  .btn {
    padding: 10px 20px;
    font-size: 0.9rem;
  }
}
</style>
