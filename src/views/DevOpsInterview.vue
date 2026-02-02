<template>
  <div class="devops-interview">
    <div class="container-fluid">
      <!-- Hero 섹션 -->
      <div class="hero-section bg-gradient-primary text-white text-center py-5 mb-5">
        <div class="container">
          <h1 class="display-3 mb-4">{{ $t('devopsInterview.hero.title') }}</h1>
          <p class="lead mb-4">{{ $t('devopsInterview.hero.subtitle') }}</p>
          <p class="h5 mb-5">{{ $t('devopsInterview.hero.description') }}</p>
          <div class="d-flex justify-content-center gap-3 flex-wrap">
            <router-link to="/study-management" class="btn btn-light btn-lg px-4 py-3">
              <i class="fas fa-play me-2"></i>{{ $t('devopsInterview.hero.startStudy') }}
            </router-link>
            <router-link to="/exam-management" class="btn btn-outline-light btn-lg px-4 py-3">
              <i class="fas fa-question-circle me-2"></i>{{ $t('devopsInterview.hero.solveProblems') }}
            </router-link>
          </div>
        </div>
      </div>

      <!-- 핵심 가치 제안 -->
      <div class="container">
        <div class="row mb-5">
          <div class="col-12 text-center mb-5">
            <h2 class="display-5 mb-4">{{ $t('devopsInterview.why.title') }}</h2>
          </div>
        </div>

        <div class="row g-4 mb-5">
          <div class="col-lg-4 col-md-6">
            <div class="card h-100 shadow-sm feature-card">
              <div class="card-body p-4 text-center">
                <div class="feature-icon bg-warning text-white rounded-circle d-inline-flex align-items-center justify-content-center mb-3" style="width: 80px; height: 80px;">
                  <i class="fas fa-redo fa-2x"></i>
                </div>
                <h4 class="card-title text-warning">{{ $t('devopsInterview.why.autoReview.title') }}</h4>
                <p class="card-text">{{ $t('devopsInterview.why.autoReview.description') }}</p>
              </div>
            </div>
          </div>

          <div class="col-lg-4 col-md-6">
            <div class="card h-100 shadow-sm feature-card">
              <div class="card-body p-4 text-center">
                <div class="feature-icon bg-info text-white rounded-circle d-inline-flex align-items-center justify-content-center mb-3" style="width: 80px; height: 80px;">
                  <i class="fas fa-comments fa-2x"></i>
                </div>
                <h4 class="card-title text-info">{{ $t('devopsInterview.why.mockInterview.title') }}</h4>
                <p class="card-text">{{ $t('devopsInterview.why.mockInterview.description') }}</p>
              </div>
            </div>
          </div>

          <div class="col-lg-4 col-md-6">
            <div class="card h-100 shadow-sm feature-card">
              <div class="card-body p-4 text-center">
                <div class="feature-icon bg-primary text-white rounded-circle d-inline-flex align-items-center justify-content-center mb-3" style="width: 80px; height: 80px;">
                  <i class="fas fa-rocket fa-2x"></i>
                </div>
                <h4 class="card-title text-primary">{{ $t('devopsInterview.why.realWorld.title') }}</h4>
                <p class="card-text">{{ $t('devopsInterview.why.realWorld.description') }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 콘텐츠 소개 -->
        <div class="row mb-5">
          <div class="col-12 text-center mb-5">
            <h2 class="display-5 mb-4">{{ $t('devopsInterview.content.title') }}</h2>
          </div>
        </div>

        <div class="row g-4 mb-5">
          <div class="col-lg-6">
            <div class="card shadow-sm h-100">
              <div class="card-header bg-primary text-white">
                <h4 class="mb-0"><i class="fas fa-database me-2"></i>{{ $t('devopsInterview.content.questionBank.title') }}</h4>
              </div>
              <div class="card-body p-4">
                <div class="row">
                  <div class="col-md-6 mb-3">
                    <h6 class="text-primary">{{ $t('devopsInterview.content.questionBank.categories') }}</h6>
                    <ul class="list-unstyled">
                      <li><i class="fas fa-check text-success me-2"></i>{{ $t('devopsInterview.content.questionBank.cicd') }}</li>
                      <li><i class="fas fa-check text-success me-2"></i>{{ $t('devopsInterview.content.questionBank.kubernetes') }}</li>
                      <li><i class="fas fa-check text-success me-2"></i>{{ $t('devopsInterview.content.questionBank.cloud') }}</li>
                      <li><i class="fas fa-check text-success me-2"></i>{{ $t('devopsInterview.content.questionBank.systemDesign') }}</li>
                      <li><i class="fas fa-check text-success me-2"></i>{{ $t('devopsInterview.content.questionBank.linux') }}</li>
                      <li><i class="fas fa-check text-success me-2"></i>{{ $t('devopsInterview.content.questionBank.sre') }}</li>
                    </ul>
                  </div>
                  <div class="col-md-6 mb-3">
                    <h6 class="text-primary">{{ $t('devopsInterview.content.questionBank.difficulty') }}</h6>
                    <div class="d-flex gap-2 flex-wrap">
                      <span class="badge bg-success">{{ $t('devopsInterview.content.questionBank.junior') }}</span>
                      <span class="badge bg-warning">{{ $t('devopsInterview.content.questionBank.mid') }}</span>
                      <span class="badge bg-danger">{{ $t('devopsInterview.content.questionBank.senior') }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="col-lg-6">
            <div class="card shadow-sm h-100">
              <div class="card-header bg-success text-white">
                <h4 class="mb-0"><i class="fas fa-book me-2"></i>{{ $t('devopsInterview.content.learningResources.title') }}</h4>
              </div>
              <div class="card-body p-4">
                <div class="row">
                  <div class="col-12 mb-3">
                    <h6 class="text-success">{{ $t('devopsInterview.content.learningResources.features') }}</h6>
                    <ul class="list-unstyled">
                      <li><i class="fas fa-lightbulb text-warning me-2"></i>{{ $t('devopsInterview.content.learningResources.qna') }}</li>
                      <li><i class="fas fa-users text-primary me-2"></i>{{ $t('devopsInterview.content.learningResources.groupStudy') }}</li>
                      <li><i class="fas fa-chart-line text-success me-2"></i>{{ $t('devopsInterview.content.learningResources.progress') }}</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 샘플 인터뷰 문제 -->
        <div class="row mb-5">
          <div class="col-12 text-center mb-4">
            <h2 class="display-5 mb-4">{{ $t('devopsInterview.sample.title') }}</h2>
          </div>
        </div>

        <div class="row g-4 mb-5">
          <div class="col-lg-4 col-md-6">
            <div class="card shadow-sm h-100">
              <div class="card-body p-4">
                <div class="d-flex align-items-center mb-3">
                  <span class="badge bg-primary me-2">{{ $t('devopsInterview.sample.question1.level') }}</span>
                  <span class="badge bg-secondary">{{ $t('devopsInterview.sample.question1.category') }}</span>
                </div>
                <h5 class="card-title">{{ $t('devopsInterview.sample.question1.title') }}</h5>
                <p class="card-text">{{ $t('devopsInterview.sample.question1.description') }}</p>
                <div class="mt-auto">
                  <small class="text-muted">{{ $t('devopsInterview.sample.question1.time') }}</small>
                </div>
              </div>
            </div>
          </div>

          <div class="col-lg-4 col-md-6">
            <div class="card shadow-sm h-100">
              <div class="card-body p-4">
                <div class="d-flex align-items-center mb-3">
                  <span class="badge bg-warning me-2">{{ $t('devopsInterview.sample.question2.level') }}</span>
                  <span class="badge bg-secondary">{{ $t('devopsInterview.sample.question2.category') }}</span>
                </div>
                <h5 class="card-title">{{ $t('devopsInterview.sample.question2.title') }}</h5>
                <p class="card-text">{{ $t('devopsInterview.sample.question2.description') }}</p>
                <div class="mt-auto">
                  <small class="text-muted">{{ $t('devopsInterview.sample.question2.time') }}</small>
                </div>
              </div>
            </div>
          </div>

          <div class="col-lg-4 col-md-6">
            <div class="card shadow-sm h-100">
              <div class="card-body p-4">
                <div class="d-flex align-items-center mb-3">
                  <span class="badge bg-danger me-2">{{ $t('devopsInterview.sample.question3.level') }}</span>
                  <span class="badge bg-secondary">{{ $t('devopsInterview.sample.question3.category') }}</span>
                </div>
                <h5 class="card-title">{{ $t('devopsInterview.sample.question3.title') }}</h5>
                <p class="card-text">{{ $t('devopsInterview.sample.question3.description') }}</p>
                <div class="mt-auto">
                  <small class="text-muted">{{ $t('devopsInterview.sample.question3.time') }}</small>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 추천 학습 경로 -->
        <div class="row mb-5">
          <div class="col-12 text-center mb-4">
            <h2 class="display-5 mb-4">{{ $t('devopsInterview.roadmap.title') }}</h2>
            <p class="lead">{{ $t('devopsInterview.roadmap.subtitle') }}</p>
          </div>
        </div>

        <div class="row g-4 mb-5">
          <div class="col-lg-3 col-md-6">
            <div class="card shadow-sm h-100 roadmap-card">
              <div class="card-header bg-success text-white text-center">
                <h5 class="mb-0">{{ $t('devopsInterview.roadmap.stage1.title') }}</h5>
              </div>
              <div class="card-body p-4">
                <div class="text-center mb-3">
                  <i class="fas fa-terminal fa-3x text-success"></i>
                </div>
                <h6 class="text-success">{{ $t('devopsInterview.roadmap.stage1.subtitle') }}</h6>
                <ul class="list-unstyled">
                  <li><i class="fas fa-check text-success me-2"></i>{{ $t('devopsInterview.roadmap.stage1.linux') }}</li>
                  <li><i class="fas fa-check text-success me-2"></i>{{ $t('devopsInterview.roadmap.stage1.shell') }}</li>
                  <li><i class="fas fa-check text-success me-2"></i>{{ $t('devopsInterview.roadmap.stage1.git') }}</li>
                </ul>
              </div>
            </div>
          </div>

          <div class="col-lg-3 col-md-6">
            <div class="card shadow-sm h-100 roadmap-card">
              <div class="card-header bg-primary text-white text-center">
                <h5 class="mb-0">{{ $t('devopsInterview.roadmap.stage2.title') }}</h5>
              </div>
              <div class="card-body p-4">
                <div class="text-center mb-3">
                  <i class="fas fa-cubes fa-3x text-primary"></i>
                </div>
                <h6 class="text-primary">{{ $t('devopsInterview.roadmap.stage2.subtitle') }}</h6>
                <ul class="list-unstyled">
                  <li><i class="fas fa-check text-primary me-2"></i>{{ $t('devopsInterview.roadmap.stage2.cicd') }}</li>
                  <li><i class="fas fa-check text-primary me-2"></i>{{ $t('devopsInterview.roadmap.stage2.docker') }}</li>
                  <li><i class="fas fa-check text-primary me-2"></i>{{ $t('devopsInterview.roadmap.stage2.kubernetes') }}</li>
                </ul>
              </div>
            </div>
          </div>

          <div class="col-lg-3 col-md-6">
            <div class="card shadow-sm h-100 roadmap-card">
              <div class="card-header bg-warning text-white text-center">
                <h5 class="mb-0">{{ $t('devopsInterview.roadmap.stage3.title') }}</h5>
              </div>
              <div class="card-body p-4">
                <div class="text-center mb-3">
                  <i class="fas fa-cloud fa-3x text-warning"></i>
                </div>
                <h6 class="text-warning">{{ $t('devopsInterview.roadmap.stage3.subtitle') }}</h6>
                <ul class="list-unstyled">
                  <li><i class="fas fa-check text-warning me-2"></i>{{ $t('devopsInterview.roadmap.stage3.cloud') }}</li>
                  <li><i class="fas fa-check text-warning me-2"></i>{{ $t('devopsInterview.roadmap.stage3.terraform') }}</li>
                  <li><i class="fas fa-check text-warning me-2"></i>{{ $t('devopsInterview.roadmap.stage3.systemDesign') }}</li>
                </ul>
              </div>
            </div>
          </div>

          <div class="col-lg-3 col-md-6">
            <div class="card shadow-sm h-100 roadmap-card">
              <div class="card-header bg-danger text-white text-center">
                <h5 class="mb-0">{{ $t('devopsInterview.roadmap.stage4.title') }}</h5>
              </div>
              <div class="card-body p-4">
                <div class="text-center mb-3">
                  <i class="fas fa-server fa-3x text-danger"></i>
                </div>
                <h6 class="text-danger">{{ $t('devopsInterview.roadmap.stage4.subtitle') }}</h6>
                <ul class="list-unstyled">
                  <li><i class="fas fa-check text-danger me-2"></i>{{ $t('devopsInterview.roadmap.stage4.distributed') }}</li>
                  <li><i class="fas fa-check text-danger me-2"></i>{{ $t('devopsInterview.roadmap.stage4.sre') }}</li>
                  <li><i class="fas fa-check text-danger me-2"></i>{{ $t('devopsInterview.roadmap.stage4.advanced') }}</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <!-- CTA 섹션 - 로그인하지 않은 사용자에게만 표시 -->
        <div v-if="!isAuthenticated" class="row mb-5">
          <div class="col-lg-8 mx-auto text-center">
            <div class="card bg-light shadow-sm">
              <div class="card-body p-5">
                <h3 class="card-title mb-4">{{ $t('devopsInterview.cta.title') }}</h3>
                <p class="card-text mb-4">{{ $t('devopsInterview.cta.description') }}</p>
                <div class="d-flex justify-content-center gap-3 flex-wrap">
                  <router-link to="/register" class="btn btn-primary btn-lg px-4 py-3">
                    <i class="fas fa-user-plus me-2"></i>{{ $t('devopsInterview.cta.register') }}
                  </router-link>
                  <router-link to="/login" class="btn btn-outline-primary btn-lg px-4 py-3">
                    <i class="fas fa-sign-in-alt me-2"></i>{{ $t('devopsInterview.cta.login') }}
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
  name: 'DevOpsInterview',
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
        title: 'DevOps 인터뷰 준비 - DrillQuiz',
        description: 'DevOps 인터뷰를 실전처럼 준비하세요. FAANG 및 실리콘밸리 빅테크에서 자주 나오는 DevOps/시스템 디자인 문제로 체계적으로 학습하세요.',
        keywords: 'DevOps 인터뷰, 시스템 디자인, Kubernetes, CI/CD, 클라우드, SRE, 실전 인터뷰 준비'
      },
      'en': {
        title: 'DevOps Interview Preparation - DrillQuiz',
        description: 'Prepare for DevOps interviews like real interviews. Learn systematically with DevOps/system design questions frequently asked at FAANG and Silicon Valley big tech companies.',
        keywords: 'DevOps interview, system design, Kubernetes, CI/CD, cloud, SRE, real interview preparation'
      },
      'es': {
        title: 'Preparación para Entrevista DevOps - DrillQuiz',
        description: 'Prepárate para entrevistas DevOps como entrevistas reales. Aprende sistemáticamente con preguntas de DevOps/diseño de sistemas frecuentemente formuladas en FAANG y grandes empresas tecnológicas de Silicon Valley.',
        keywords: 'entrevista DevOps, diseño de sistemas, Kubernetes, CI/CD, nube, SRE, preparación para entrevista real'
      },
      'zh': {
        title: 'DevOps 面试准备 - DrillQuiz',
        description: '像真实面试一样准备 DevOps 面试。系统学习 FAANG 和硅谷大型科技公司经常问到的 DevOps/系统设计问题。',
        keywords: 'DevOps 面试, 系统设计, Kubernetes, CI/CD, 云, SRE, 真实面试准备'
      },
      'ja': {
        title: 'DevOps インタビュー準備 - DrillQuiz',
        description: 'DevOpsインタビューを実戦のように準備しましょう。FAANGやシリコンバレーのビッグテックでよく出題されるDevOps/システム設計問題で体系的に学習します。',
        keywords: 'DevOpsインタビュー, システム設計, Kubernetes, CI/CD, クラウド, SRE, 実戦インタビュー準備'
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
.devops-interview {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.hero-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border-radius: 0;
}

.bg-gradient-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
}

.feature-card {
  border: none;
  border-radius: 15px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 25px rgba(0,0,0,0.1) !important;
}

.roadmap-card {
  border: none;
  border-radius: 15px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.roadmap-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 25px rgba(0,0,0,0.1) !important;
}

.card {
  border: none;
  border-radius: 15px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(0,0,0,0.1) !important;
}

.feature-icon {
  font-size: 1.5rem;
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

.badge {
  font-size: 0.75rem;
  padding: 0.5rem 0.75rem;
}

@media (max-width: 768px) {
  .hero-section {
    padding: 3rem 1rem !important;
  }
  
  .display-3 {
    font-size: 2.5rem;
  }
  
  .display-5 {
    font-size: 2rem;
  }
  
  /* Hero 섹션 버튼들을 원형 버튼으로 */
  .hero-section .btn,
  .hero-section .btn-lg {
    padding: 0 !important;
    width: 50px !important;
    height: 50px !important;
    border-radius: 50% !important;
    min-width: 50px !important;
    max-width: 50px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 0 !important;
    gap: 0 !important;
  }
  
  .hero-section .btn i {
    font-size: 20px !important;
    line-height: 1 !important;
    margin: 0 !important;
    display: block !important;
  }
  
  /* 텍스트만 숨기기 (아이콘은 유지) */
  .hero-section .btn > :not(i) {
    display: none !important;
  }
  
  /* CTA 섹션 버튼들도 원형으로 */
  .card .btn,
  .card .btn-lg {
    padding: 0 !important;
    width: 50px !important;
    height: 50px !important;
    border-radius: 50% !important;
    min-width: 50px !important;
    max-width: 50px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 0 !important;
    gap: 0 !important;
  }
  
  .card .btn i {
    font-size: 20px !important;
    line-height: 1 !important;
    margin: 0 !important;
    display: block !important;
  }
  
  /* 텍스트만 숨기기 (아이콘은 유지) */
  .card .btn > :not(i) {
    display: none !important;
  }
  
  /* 섹션 제목 margin-bottom 제거 (Why This Site?, Sample Interview Questions, Recommended Learning Path 등) */
  .row.mb-5 .col-12.text-center.mb-5,
  .row.mb-5 .col-12.text-center.mb-4 {
    margin-bottom: 0 !important;
  }
  
  /* 섹션 제목 h2의 margin-bottom도 제거 */
  .row.mb-5 .col-12.text-center.mb-5 h2.mb-4,
  .row.mb-5 .col-12.text-center.mb-4 h2.mb-4 {
    margin-bottom: 0 !important;
  }
  
  /* 섹션 제목의 p 태그 margin도 제거 */
  .row.mb-5 .col-12.text-center.mb-4 p.lead {
    margin-bottom: 0 !important;
  }
  
  /* 모바일에서 .mb-5 margin-bottom 줄이기 */
  .mb-5 {
    margin-bottom: 1rem !important;
  }
}
</style>
