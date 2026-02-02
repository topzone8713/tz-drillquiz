<template>
  <footer class="footer mt-auto py-1 bg-dark text-light">
    <div class="container">
      <div class="row">
        <!-- Privacy Policy -->
        <div class="col-4 col-md-4 mb-1 text-center">
          <router-link :to="privacyPolicyPath" class="text-light text-decoration-none">
            {{ $t('footer.privacyPolicy') }}
          </router-link>
        </div>

        <!-- Terms of Service -->
        <div class="col-4 col-md-4 mb-1 text-center">
          <router-link :to="termsOfServicePath" class="text-light text-decoration-none">
            {{ $t('footer.termsOfService') }}
          </router-link>
        </div>

        <!-- About this -->
        <div class="col-4 col-md-4 mb-1 text-center">
          <router-link :to="serviceIntroductionPath" class="text-light text-decoration-none">
            {{ $t('footer.aboutThis') }}
          </router-link>
        </div>
      </div>
      
      <!-- Copyright -->
      <div class="row copyright-row">
        <div class="col-12 text-center">
          <small class="text-muted">
            Copyright © 2025 drillquiz.com | All rights reserved.
          </small>
        </div>
      </div>
    </div>
  </footer>
</template>

<script>
export default {
  name: 'AppFooter',
  computed: {
    currentLanguage() {
      return this.$i18n.locale || 'en'
    },
    privacyPolicyPath() {
      const lang = this.currentLanguage
      if (lang === 'ko') {
        return '/privacy-policy_kr'
      } else if (lang === 'zh') {
        return '/privacy-policy_zh'
      } else if (lang === 'en') {
        return '/privacy-policy_en'
      } else if (lang === 'es') {
        return '/privacy-policy_es'
      } else if (lang === 'ja') {
        return '/privacy-policy_ja'
      }
      return '/privacy-policy'
    },
    termsOfServicePath() {
      const lang = this.currentLanguage
      if (lang === 'ko') {
        return '/terms-of-service_kr'
      } else if (lang === 'zh') {
        return '/terms-of-service_zh'
      } else if (lang === 'en') {
        return '/terms-of-service_en'
      } else if (lang === 'es') {
        return '/terms-of-service_es'
      } else if (lang === 'ja') {
        return '/terms-of-service_ja'
      }
      return '/terms-of-service'
    },
    serviceIntroductionPath() {
      const lang = this.currentLanguage
      if (lang === 'ko') {
        return '/service-introduction_kr'
      } else if (lang === 'zh') {
        return '/service-introduction_zh'
      } else if (lang === 'en') {
        return '/service-introduction_en'
      } else if (lang === 'es') {
        return '/service-introduction_es'
      } else if (lang === 'ja') {
        return '/service-introduction_ja'
      }
      return '/service-introduction'
    }
  }
}
</script>

<style scoped>
.footer {
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  flex-shrink: 0;
  font-size: 0.75rem;
  margin-top: auto; /* footer를 항상 하단에 위치 */
  width: 100%;
}

/* 모바일에서 Footer 하단 여백 추가 (배경색 포함) */
@media (max-width: 768px) {
  .footer {
    padding-bottom: 20px; /* 하단 홈 인디케이터 영역 고려 */
  }
}

.footer .container {
  padding-top: 0.25rem;
  padding-bottom: 0.25rem;
}

.footer a {
  transition: all 0.2s ease;
}

.footer a:hover {
  color: #ffffff !important;
  text-decoration: underline !important;
  opacity: 0.8;
}

.footer .text-muted {
  color: #adb5bd !important;
  font-size: 0.7rem;
}

.footer .mx-2 {
  color: #6c757d;
}

@media (max-width: 768px) {
  .footer .col-md-4 {
    text-align: center;
    margin-bottom: 0.5rem;
  }
  
  .footer .mx-2 {
    display: none;
  }
  
  .footer .col-md-4:not(:last-child)::after {
    content: '';
    display: block;
    height: 0.5rem;
  }
  
  .footer .copyright-row {
    margin-bottom: 5px;
  }
}
</style>
