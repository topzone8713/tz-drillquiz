<template>
  <div class="getting-started-modern">
    <!-- JSON-LD 구조화된 데이터 -->
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "HowTo",
      "name": "DrillQuiz 시작하기 가이드",
      "description": "DrillQuiz 퀴즈 학습 플랫폼 사용법을 단계별로 안내합니다",
      "url": "https://us.drillquiz.com/getting-started",
      "step": [
        {
          "@type": "HowToStep",
          "name": "문제 파일 업로드",
          "text": "파일을 업로드하여 문제를 등록합니다",
          "url": "https://us.drillquiz.com/question-files"
        },
        {
          "@type": "HowToStep",
          "name": "시험 생성",
          "text": "스터디를 기반으로 시험을 생성합니다",
          "url": "https://us.drillquiz.com/exam-management"
        },
        {
          "@type": "HowToStep",
          "name": "스터디 생성",
          "text": "업로드한 문제들로 스터디를 생성합니다",
          "url": "https://us.drillquiz.com/study-management"
        },
        {
          "@type": "HowToStep",
          "name": "학습 시작",
          "text": "생성된 시험으로 학습을 시작합니다",
          "url": "https://us.drillquiz.com/random-practice"
        }
      ]
    }
    </script>
    
    <div class="getting-started-container">
      <!-- Hero Section -->
      <div class="hero-section">
        <div class="hero-content">
          <h1 class="hero-title">{{ $t('gettingStarted.title') }}</h1>
          <p class="hero-subtitle">{{ $t('gettingStarted.subtitle') }}</p>
        </div>
      </div>

      <!-- Steps Section -->
      <div class="steps-container">
        <div class="steps-grid">
          <!-- Step 1 -->
          <div class="step-card">
            <div class="step-number">1</div>
            <div class="step-icon" @click="$router.push('/text-to-questions')">
              <i class="fas fa-upload"></i>
            </div>
            <div class="step-content">
              <h3 class="step-title">{{ $t('gettingStarted.step1.title') }}</h3>
              <p class="step-description">{{ $t('gettingStarted.step1.description') }}</p>
              <div class="step-action">
                <router-link to="/text-to-questions" class="step-btn">
                  {{ $t('gettingStarted.step1.button') }}
                </router-link>
              </div>
            </div>
          </div>

          <!-- Step 2 -->
          <div class="step-card">
            <div class="step-number">2</div>
            <div class="step-icon" @click="$router.push('/exam-management')">
              <i class="fas fa-clipboard-check"></i>
            </div>
            <div class="step-content">
              <h3 class="step-title">{{ $t('gettingStarted.step2.title') }}</h3>
              <p class="step-description">{{ $t('gettingStarted.step2.description') }}</p>
              <div class="step-action">
                <router-link to="/exam-management" class="step-btn">
                  {{ $t('gettingStarted.step2.button') }}
                </router-link>
              </div>
            </div>
          </div>

          <!-- Step 3 -->
          <div class="step-card">
            <div class="step-number">3</div>
            <div class="step-icon" @click="$router.push('/study-management')">
              <i class="fas fa-book"></i>
            </div>
            <div class="step-content">
              <h3 class="step-title">{{ $t('gettingStarted.step3.title') }}</h3>
              <p class="step-description">{{ $t('gettingStarted.step3.description') }}</p>
              <div class="step-action">
                <router-link to="/study-management" class="step-btn">
                  {{ $t('gettingStarted.step3.button') }}
                </router-link>
              </div>
            </div>
          </div>

          <!-- Step 4 -->
          <div class="step-card">
            <div class="step-number">4</div>
            <div class="step-icon" @click="$router.push('/random-practice')">
              <i class="fas fa-play-circle"></i>
            </div>
            <div class="step-content">
              <h3 class="step-title">{{ $t('gettingStarted.step4.title') }}</h3>
              <p class="step-description">{{ $t('gettingStarted.step4.description') }}</p>
              <div class="step-action">
                <router-link to="/random-practice" class="step-btn">
                  {{ $t('gettingStarted.step4.button') }}
                </router-link>
              </div>
            </div>
          </div>

          <!-- Step 5 -->
          <div class="step-card">
            <div class="step-number">5</div>
            <div class="step-icon" @click="$router.push('/profile')">
              <i class="fas fa-envelope"></i>
            </div>
            <div class="step-content">
              <h3 class="step-title">{{ $t('gettingStarted.step5.title') }}</h3>
              <p class="step-description">{{ $t('gettingStarted.step5.description') }}</p>
              <div class="step-action">
                <router-link to="/profile" class="step-btn">
                  {{ $t('gettingStarted.step5.button') }}
                </router-link>
              </div>
            </div>
          </div>

          <!-- Step 6 -->
          <div class="step-card">
            <div class="step-number">6</div>
            <div class="step-icon" @click="$router.push('/results')">
              <i class="fas fa-chart-line"></i>
            </div>
            <div class="step-content">
              <h3 class="step-title">{{ $t('gettingStarted.step6.title') }}</h3>
              <p class="step-description">{{ $t('gettingStarted.step6.description') }}</p>
              <div class="step-action">
                <router-link to="/results" class="step-btn">
                  {{ $t('gettingStarted.step6.button') }}
                </router-link>
              </div>
            </div>
          </div>
        </div>

        <!-- Back to Home Button -->
        <div class="back-home-section">
          <router-link to="/" class="back-home-btn">
            <i class="fas fa-home"></i>
            <span>{{ $t('gettingStarted.backHome') }}</span>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { isAdmin as checkIsAdmin, hasStudyAdminRole } from '@/utils/permissionUtils'

export default {
  name: 'GettingStarted',
  metaInfo() {
    return {
      title: '시작하기',
      meta: [
        { name: 'description', content: 'DrillQuiz 시작하기 - 퀴즈 학습 플랫폼 사용법을 단계별로 안내합니다. 문제 파일 업로드부터 시험 생성까지 모든 과정을 쉽게 배워보세요.' },
        { name: 'keywords', content: 'DrillQuiz 시작하기, 퀴즈 학습 가이드, 문제 파일 업로드, 스터디 생성, 시험 관리' },
        // Open Graph
        { property: 'og:title', content: 'DrillQuiz 시작하기 - 퀴즈 학습 가이드' },
        { property: 'og:description', content: 'DrillQuiz 시작하기 - 퀴즈 학습 플랫폼 사용법을 단계별로 안내합니다.' },
        { property: 'og:type', content: 'website' },
        { property: 'og:url', content: 'https://us.drillquiz.com/getting-started' },
        // Twitter Card
        { name: 'twitter:title', content: 'DrillQuiz 시작하기 - 퀴즈 학습 가이드' },
        { name: 'twitter:description', content: 'DrillQuiz 시작하기 - 퀴즈 학습 플랫폼 사용법을 단계별로 안내합니다.' }
      ]
    }
  },
  computed: {
    isAdmin() {
      return checkIsAdmin()
    },
    isStudyAdmin() {
      return hasStudyAdminRole()
    }
  }
}
</script>

<style scoped>
/* Modern Getting Started Styles */
.getting-started-modern {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.getting-started-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

/* Hero Section */
.hero-section {
  padding: 40px 20px 30px;
  text-align: center;
  color: white;
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
  opacity: 0.9;
  line-height: 1.6;
}

/* Steps Container */
.steps-container {
  padding: 0 20px 30px;
}

.steps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

/* Step Card */
.step-card {
  background: white;
  border-radius: 20px;
  padding: 25px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.step-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

.step-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* Step Number */
.step-number {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.2rem;
}

/* Step Icon */
.step-icon {
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

.step-icon:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
  background: linear-gradient(135deg, #5a32a3 0%, #6a4c93 100%);
}

.step-icon:active {
  transform: scale(0.98);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.6);
}

/* Step Content */
.step-content {
  text-align: center;
}

.step-title {
  font-size: 1.4rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 8px;
}

.step-description {
  color: #6c757d;
  line-height: 1.5;
  margin-bottom: 15px;
  font-size: 1rem;
}

/* Step Action */
.step-action {
  margin-top: 15px;
}

.step-btn {
  display: inline-block;
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  text-decoration: none;
  border-radius: 25px;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.step-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
  color: white;
  text-decoration: none;
}



/* Back to Home Section */
.back-home-section {
  text-align: center;
  margin-top: 20px;
}

.back-home-btn {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 15px 30px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  text-decoration: none;
  border-radius: 30px;
  font-weight: 500;
  transition: all 0.3s ease;
  border: 2px solid rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
}

.back-home-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
  color: white;
  text-decoration: none;
}

.back-home-btn i {
  font-size: 1.1rem;
}

/* Responsive Design */
@media (max-width: 768px) {
  .hero-title {
    font-size: 2.5rem;
  }
  
  .hero-subtitle {
    font-size: 1.2rem;
  }
  
  .steps-grid {
    grid-template-columns: 1fr;
    gap: 15px;
  }
  
  .step-card {
    padding: 20px;
  }
  
  .step-icon {
    width: 55px;
    height: 55px;
    font-size: 1.4rem;
  }
  
  .step-number {
    width: 35px;
    height: 35px;
    font-size: 1rem;
  }
}

@media (max-width: 480px) {
  .hero-title {
    font-size: 2rem;
  }
  
  .hero-subtitle {
    font-size: 1rem;
  }
  
  .getting-started-container {
    padding: 0 15px;
  }
  
  .step-card {
    padding: 18px;
  }
  
  .step-title {
    font-size: 1.2rem;
  }
  
  .step-description {
    font-size: 0.9rem;
  }
}

/* Animation for step cards */
.step-card {
  animation: fadeInUp 0.6s ease-out;
}

.step-card:nth-child(1) { animation-delay: 0.1s; }
.step-card:nth-child(2) { animation-delay: 0.2s; }
.step-card:nth-child(3) { animation-delay: 0.3s; }
.step-card:nth-child(4) { animation-delay: 0.4s; }
.step-card:nth-child(5) { animation-delay: 0.5s; }
.step-card:nth-child(6) { animation-delay: 0.6s; }

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style> 