<template>
  <div class="service-introduction">
    <div class="container-fluid">
      <!-- 헤더 섹션 -->
      <div class="jumbotron bg-primary text-white text-center py-5 mb-5">
        <div class="container">
          <h1 class="display-4 mb-4">服务介绍</h1>
          <p class="lead">高效学习的创新平台</p>
        </div>
      </div>

      <!-- 메인 콘텐츠 -->
      <div class="container">
        <div class="mb-3">
          <button @click="goBack" class="btn btn-outline-secondary">
            <i class="fas fa-arrow-left"></i> 返回
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
                  <h2 class="card-title mb-0">重复学习的新方式</h2>
                </div>
                <p class="card-text mb-4">DrillQuiz提供基于遗忘曲线理论的智能重复学习系统。不是简单的重复，而是科学设计的学习模式，强化长期记忆。</p>
                
                <div class="row">
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-primary">排水系统</h5>
                      <p class="text-muted">自动收集错误题目，让您能够集中重复学习。一旦答错的题目会持续重复，直到再次出现。</p>
                    </div>
                  </div>
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-primary">长期记忆强化</h5>
                      <p class="text-muted">随着时间的推移，题目再次出现的间隔逐渐增加，自然帮助转化为长期记忆。</p>
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
                  <h2 class="card-title mb-0">面试式学习支持</h2>
                </div>
                <p class="card-text mb-4">模拟真实技术面试环境，培养用语言解释的能力。提供基于语音识别技术的互动学习体验。</p>
                
                <div class="row">
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-success">语音面试模式</h5>
                      <p class="text-muted">可以阅读题目并用语音解释答案进行练习。提供与真实面试情况相似的体验。</p>
                    </div>
                  </div>
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-success">追加问题练习</h5>
                      <p class="text-muted">回答后可以接受追加问题，练习更深入的说明。培养从面试官角度思考的能力。</p>
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
                  <h2 class="card-title mb-0">个性化错题管理</h2>
                </div>
                <p class="card-text mb-4">自动收集错误题目，定期通过电子邮件发送，让您随时随地复习。自然地培养学习习惯。</p>
                
                <div class="row">
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-warning">自动错题收集</h5>
                      <p class="text-muted">错误题目自动添加到错题本，无需额外操作即可系统管理。</p>
                    </div>
                  </div>
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-warning">电子邮件复习</h5>
                      <p class="text-muted">按设定的周期接收错题邮件，在日常生活中自然复习。</p>
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
                  <h2 class="card-title mb-0">最大化学习效果</h2>
                </div>
                <p class="card-text mb-4">三个核心功能有机结合，创造最佳学习效果。</p>
                
                <div class="row">
                  <div class="col-md-4 mb-3">
                    <div class="feature-item text-center">
                      <div class="feature-icon-small bg-primary text-white rounded-circle d-inline-flex align-items-center justify-content-center mb-2" style="width: 40px; height: 40px;">
                        <i class="fas fa-redo"></i>
                      </div>
                      <h6 class="text-primary">排水系统</h6>
                      <p class="text-muted small">自动收集错题并重复学习</p>
                    </div>
                  </div>
                  <div class="col-md-4 mb-3">
                    <div class="feature-item text-center">
                      <div class="feature-icon-small bg-success text-white rounded-circle d-inline-flex align-items-center justify-content-center mb-2" style="width: 40px; height: 40px;">
                        <i class="fas fa-comments"></i>
                      </div>
                      <h6 class="text-success">语音面试</h6>
                      <p class="text-muted small">真实面试环境模拟</p>
                    </div>
                  </div>
                  <div class="col-md-4 mb-3">
                    <div class="feature-item text-center">
                      <div class="feature-icon-small bg-warning text-white rounded-circle d-inline-flex align-items-center justify-content-center mb-2" style="width: 40px; height: 40px;">
                        <i class="fas fa-envelope"></i>
                      </div>
                      <h6 class="text-warning">电子邮件复习</h6>
                      <p class="text-muted small">定期发送错题</p>
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
                <h3 class="card-title mb-4">立即开始</h3>
                <p class="card-text mb-4">立即开始使用DrillQuiz进行更高效的学习。免费注册并体验所有功能。</p>
                <div class="d-flex justify-content-center gap-3 flex-wrap">
                  <router-link to="/register" class="btn btn-primary btn-lg">
                    <i class="fas fa-user-plus me-md-2"></i><span class="d-none d-md-inline">注册</span>
                  </router-link>
                  <router-link to="/login" class="btn btn-outline-primary btn-lg">
                    <i class="fas fa-sign-in-alt me-md-2"></i><span class="d-none d-md-inline">登录</span>
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
  name: 'ServiceIntroductionZh',
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
    title: '服务介绍 - DrillQuiz',
    meta: [
      { 
        name: 'description', 
        content: '介绍DrillQuiz的创新学习功能。通过重复学习、面试式学习、个性化错题管理最大化学习效果。' 
      },
      { 
        name: 'keywords', 
        content: 'DrillQuiz, 服务介绍, 重复学习, 面试式学习, 错题管理, 学习效果' 
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

