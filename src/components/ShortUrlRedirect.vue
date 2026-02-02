<template>
  <div class="short-url-redirect">
    <div class="loading-container">
      <div class="spinner"></div>
      <p>{{ loadingMessage }}</p>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'ShortUrlRedirect',
  data() {
    return {
      loadingMessage: this.$t('shortUrl.loading') || '리다이렉션 중...'
    }
  },
  async mounted() {
    await this.redirectToOriginalUrl()
  },
  methods: {
    async redirectToOriginalUrl() {
      try {
        const shortCode = this.$route.params.shortCode
        
        // Django 백엔드에서 단축 URL 정보 조회
        const response = await axios.get(`http://localhost:8000/api/short-url/${shortCode}/`)
        
        const originalUrl = response.data.original_url
        
        // 원본 URL로 리다이렉션
        this.loadingMessage = this.$t('shortUrl.redirecting') || '리다이렉션 중...'
        
        // 잠시 후 리다이렉션 (사용자 경험 개선)
        setTimeout(() => {
          window.location.href = originalUrl
        }, 500)
        
      } catch (error) {
        console.error('단축 URL 처리 실패:', error)
        
        if (error.response?.status === 404) {
          this.loadingMessage = this.$t('shortUrl.notFound') || '단축 URL을 찾을 수 없습니다.'
          this.$router.push('/')
        } else if (error.response?.status === 410) {
          this.loadingMessage = this.$t('shortUrl.expired') || 'URL이 만료되었습니다.'
          this.$router.push('/')
        } else {
          this.loadingMessage = this.$t('shortUrl.error') || '오류가 발생했습니다.'
          this.$router.push('/')
        }
      }
    }
  }
}
</script>

<style scoped>
.short-url-redirect {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f8f9fa;
}

.loading-container {
  text-align: center;
  padding: 2rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

p {
  margin: 0;
  color: #666;
  font-size: 1.1rem;
}
</style>
