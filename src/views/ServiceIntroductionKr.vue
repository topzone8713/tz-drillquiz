<template>
  <div class="service-introduction">
    <div class="container-fluid">
      <!-- 헤더 섹션 -->
      <div class="jumbotron bg-primary text-white text-center py-5 mb-5">
        <div class="container">
          <h1 class="display-4 mb-4">서비스 소개</h1>
          <p class="lead">효율적인 학습을 위한 혁신적인 플랫폼</p>
        </div>
      </div>

      <!-- 메인 콘텐츠 -->
      <div class="container">
        <div class="mb-3">
          <button @click="goBack" class="btn btn-outline-secondary">
            <i class="fas fa-arrow-left"></i> 이전 페이지
          </button>
        </div>
        <!-- 1. 반복 학습의 새로운 방식 -->
        <div class="row mb-5">
          <div class="col-lg-8 mx-auto">
            <div class="card shadow-sm">
              <div class="card-body p-4">
                <div class="d-flex align-items-center mb-3">
                  <div class="feature-icon bg-primary text-white rounded-circle d-flex align-items-center justify-content-center me-3" style="width: 60px; height: 60px;">
                    <i class="fas fa-redo fa-lg"></i>
                  </div>
                  <h2 class="card-title mb-0">반복 학습의 새로운 방식</h2>
                </div>
                <p class="card-text mb-4">DrillQuiz는 망각 곡선 이론에 기반한 스마트한 반복 학습 시스템을 제공합니다. 단순한 반복이 아닌, 과학적으로 설계된 학습 패턴으로 장기 기억을 강화합니다.</p>
                
                <div class="row">
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-primary">드레인 시스템</h5>
                      <p class="text-muted">틀린 문제를 자동으로 수집하여 집중적으로 반복 학습할 수 있도록 합니다. 한 번 틀린 문제는 다시 나올 때까지 계속 반복됩니다.</p>
                    </div>
                  </div>
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-primary">장기 기억 강화</h5>
                      <p class="text-muted">시간이 지날수록 문제가 다시 나오는 간격을 늘려가며, 자연스럽게 장기 기억으로 전환되도록 돕습니다.</p>
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
                  <h2 class="card-title mb-0">인터뷰형 학습 지원</h2>
                </div>
                <p class="card-text mb-4">실제 기술 면접 환경을 시뮬레이션하여 말로 설명하는 능력을 기를 수 있습니다. 음성 인식 기술을 활용한 인터랙티브한 학습 경험을 제공합니다.</p>
                
                <div class="row">
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-success">음성 인터뷰 모드</h5>
                      <p class="text-muted">문제를 읽고 음성으로 답변을 설명하는 연습을 할 수 있습니다. 실제 면접 상황과 유사한 경험을 제공합니다.</p>
                    </div>
                  </div>
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-success">추가 질문 연습</h5>
                      <p class="text-muted">답변 후 추가 질문을 받아 더 깊이 있는 설명을 연습할 수 있습니다. 면접관의 관점에서 생각하는 능력을 기릅니다.</p>
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
                  <h2 class="card-title mb-0">개인화된 오답 관리</h2>
                </div>
                <p class="card-text mb-4">틀린 문제를 자동으로 수집하고, 정기적으로 이메일로 전송하여 언제 어디서나 복습할 수 있도록 합니다. 학습 습관을 자연스럽게 만들어줍니다.</p>
                
                <div class="row">
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-warning">자동 오답 수집</h5>
                      <p class="text-muted">틀린 문제가 자동으로 오답 노트에 추가되어 별도의 작업 없이도 체계적으로 관리됩니다.</p>
                    </div>
                  </div>
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-warning">이메일 복습</h5>
                      <p class="text-muted">설정한 주기마다 오답 문제를 이메일로 받아 일상 속에서 자연스럽게 복습할 수 있습니다.</p>
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
                  <h2 class="card-title mb-0">학습 효과 극대화</h2>
                </div>
                <p class="card-text mb-4">세 가지 핵심 기능이 유기적으로 결합되어 최적의 학습 효과를 만들어냅니다.</p>
                
                <div class="row">
                  <div class="col-md-4 mb-3">
                    <div class="feature-item text-center">
                      <div class="feature-icon-small bg-primary text-white rounded-circle d-inline-flex align-items-center justify-content-center mb-2" style="width: 40px; height: 40px;">
                        <i class="fas fa-redo"></i>
                      </div>
                      <h6 class="text-primary">드레인 시스템</h6>
                      <p class="text-muted small">틀린 문제 자동 수집 및 반복 학습</p>
                    </div>
                  </div>
                  <div class="col-md-4 mb-3">
                    <div class="feature-item text-center">
                      <div class="feature-icon-small bg-success text-white rounded-circle d-inline-flex align-items-center justify-content-center mb-2" style="width: 40px; height: 40px;">
                        <i class="fas fa-comments"></i>
                      </div>
                      <h6 class="text-success">음성 인터뷰</h6>
                      <p class="text-muted small">실제 면접 환경 시뮬레이션</p>
                    </div>
                  </div>
                  <div class="col-md-4 mb-3">
                    <div class="feature-item text-center">
                      <div class="feature-icon-small bg-warning text-white rounded-circle d-inline-flex align-items-center justify-content-center mb-2" style="width: 40px; height: 40px;">
                        <i class="fas fa-envelope"></i>
                      </div>
                      <h6 class="text-warning">이메일 복습</h6>
                      <p class="text-muted small">정기적인 오답 문제 전송</p>
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
                <h3 class="card-title mb-4">지금 시작하세요</h3>
                <p class="card-text mb-4">DrillQuiz와 함께 더 효율적인 학습을 시작해보세요. 무료로 가입하고 모든 기능을 체험해보실 수 있습니다.</p>
                <div class="d-flex justify-content-center gap-3 flex-wrap">
                  <router-link to="/register" class="btn btn-primary btn-lg">
                    <i class="fas fa-user-plus me-md-2"></i><span class="d-none d-md-inline">회원가입</span>
                  </router-link>
                  <router-link to="/login" class="btn btn-outline-primary btn-lg">
                    <i class="fas fa-sign-in-alt me-md-2"></i><span class="d-none d-md-inline">로그인</span>
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
  name: 'ServiceIntroductionKr',
  computed: {
    isAuthenticated() {
      return authService.isAuthenticatedSync()
    }
  },
  methods: {
    goBack() {
      if (window.history.length > 1) {
        this.$router.go(-1)
      } else {
        this.$router.push('/register')
      }
    }
  },
  metaInfo: {
    title: '서비스 소개 - DrillQuiz',
    meta: [
      { 
        name: 'description', 
        content: 'DrillQuiz의 혁신적인 학습 기능들을 소개합니다. 반복 학습, 인터뷰형 학습, 개인화된 오답 관리를 통해 학습 효과를 극대화하세요.' 
      },
      { 
        name: 'keywords', 
        content: 'DrillQuiz, 서비스 소개, 반복 학습, 인터뷰형 학습, 오답 관리, 학습 효과' 
      }
    ]
  }
}
</script>

<style scoped>
.service-introduction {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding-bottom: 0;
}

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

