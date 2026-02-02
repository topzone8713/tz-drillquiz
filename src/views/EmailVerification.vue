<template>
  <div class="email-verification-page">
    <div class="verification-container">
      <!-- 디버깅용 기본 텍스트 -->
      <div v-if="!loading && !success && !error" class="debug-section">
        <h2>Email Verification Page</h2>
        <p>Token: {{ token }}</p>
        <p>Loading: {{ loading }}</p>
        <p>Success: {{ success }}</p>
        <p>Error: {{ error }}</p>
      </div>
      <!-- 로딩 상태 -->
      <div v-if="loading" class="loading-section">
        <div class="loading-spinner">
          <i class="fas fa-spinner fa-spin"></i>
        </div>
        <h2>{{ $t('emailVerification.loading.title') }}</h2>
        <p>{{ $t('emailVerification.loading.description') }}</p>
      </div>

      <!-- 성공 상태 -->
      <div v-else-if="success" class="success-section">
        <div class="success-icon">
          <i class="fas fa-check-circle"></i>
        </div>
        <h2>{{ $t('emailVerification.success.title') }}</h2>
        <p>{{ $t('emailVerification.success.description') }}</p>
        <div class="action-buttons">
          <router-link to="/profile" class="btn btn-primary" @click.native="goToProfile">
            <i class="fas fa-user"></i>
            {{ $t('emailVerification.actions.profile') }}
          </router-link>
          <router-link to="/" class="btn btn-secondary">
            <i class="fas fa-home"></i>
            {{ $t('emailVerification.actions.home') }}
          </router-link>
        </div>
      </div>

      <!-- 오류 상태 -->
      <div v-else-if="error" class="error-section">
        <div class="error-icon">
          <i class="fas fa-exclamation-triangle"></i>
        </div>
        <h2>{{ $t('emailVerification.error.title') }}</h2>
        <p>{{ errorMessage }}</p>
        <div class="action-buttons">
          <router-link to="/profile" class="btn btn-primary">
            <i class="fas fa-user"></i>
            {{ $t('emailVerification.actions.profile') }}
          </router-link>
          <button @click="retryVerification" class="btn btn-secondary" v-if="canRetry">
            <i class="fas fa-redo"></i>
            {{ $t('emailVerification.actions.retry') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { debugLog } from '@/utils/debugUtils'
import authService from '@/services/authService'

export default {
  name: 'EmailVerification',
  data() {
    return {
      loading: true,
      success: false,
      error: false,
      errorMessage: '',
      canRetry: false,
      token: null
    }
  },
  mounted() {
    debugLog('EmailVerification component mounted')
    debugLog('Route params:', this.$route.params)
    this.verifyEmail()
  },
  methods: {
    async verifyEmail() {
      try {
        // URL에서 토큰 추출
        this.token = this.$route.params.token
        
        if (!this.token) {
          throw new Error(this.$t('emailVerification.error.tokenMissing'))
        }

        // API 호출
        const response = await axios.get(`/api/verify-email/${this.token}/`)
        
        if (response.data.message) {
          this.success = true
          this.error = false
          
          // 서버에서 반환된 인증 상태 확인
          if (response.data.email_verified) {
            const userData = await authService.getUser()
            if (userData) {
              await authService.storeAuthResult({
                user: {
                  ...userData,
                  email_verified: true
                }
              })
            }
          }
        } else {
          throw new Error(this.$t('emailVerification.error.general'))
        }
      } catch (error) {
        this.error = true
        this.success = false
        
        if (error.response && error.response.data && error.response.data.error) {
          this.errorMessage = error.response.data.error
        } else if (error.message) {
          this.errorMessage = error.message
        } else {
          this.errorMessage = this.$t('emailVerification.error.description')
        }
        
        // 토큰 만료 등의 경우 재시도 가능
        if (this.errorMessage.includes('만료') || this.errorMessage.includes('expired')) {
          this.canRetry = true
        }
      } finally {
        this.loading = false
      }
    },
    
    retryVerification() {
      this.loading = true
      this.error = false
      this.errorMessage = ''
      this.verifyEmail()
    },
    
    goToProfile() {
      // 프로필 페이지로 이동하기 전에 강제 새로고침을 위한 플래그 설정
      sessionStorage.setItem('refreshProfile', 'true')
    }
  }
}
</script>

<style scoped>
.email-verification-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.verification-container {
  background: white;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
  padding: 3rem;
  max-width: 500px;
  width: 100%;
  text-align: center;
}

.loading-section,
.success-section,
.error-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
}

.loading-spinner,
.success-icon,
.error-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.loading-spinner {
  color: #667eea;
}

.success-icon {
  color: #28a745;
}

.error-icon {
  color: #dc3545;
}

h2 {
  color: #2c3e50;
  font-size: 2rem;
  font-weight: 700;
  margin: 0;
}

p {
  color: #6c757d;
  font-size: 1.1rem;
  margin: 0;
  line-height: 1.6;
}

.action-buttons {
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
  flex-wrap: wrap;
  justify-content: center;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 140px;
  justify-content: center;
}

.btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  text-decoration: none;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover {
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.btn-secondary {
  background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
  color: white;
}

.btn-secondary:hover {
  color: white;
  box-shadow: 0 4px 12px rgba(108, 117, 125, 0.3);
}

/* 반응형 디자인 */
@media (max-width: 768px) {
  .verification-container {
    padding: 2rem;
    margin: 1rem;
  }
  
  h2 {
    font-size: 1.5rem;
  }
  
  p {
    font-size: 1rem;
  }
  
  .action-buttons {
    flex-direction: column;
    align-items: center;
  }
  
  .btn {
    width: 100%;
    max-width: 200px;
  }
}
</style> 