<template>
  <div v-if="show" class="modal-overlay" @click="close">
    <div class="modal-content share-modal" @click.stop>
      <div class="modal-header">
        <h5 class="modal-title">
          <i class="fas fa-share-alt text-info"></i>
          {{ $t('examDetail.shareExam') || '시험 공유하기' }}
        </h5>
        <button class="modal-close" @click="close">
          <i class="fas fa-times"></i>
        </button>
      </div>
      <div class="modal-body">
        <!-- 이메일 입력 -->
        <div class="mb-3">
          <label class="form-label">
            <i class="fas fa-envelope me-1"></i>
            {{ $t('examDetail.shareEmailLabel') || '이메일 주소' }}
          </label>
          <input 
            v-model="email" 
            type="email" 
            class="form-control" 
            :placeholder="$t('examDetail.shareEmailPlaceholder') || '이메일을 입력하세요'"
          />
        </div>
        
        <!-- 공유 링크 표시 -->
        <div class="mb-3">
          <label class="form-label">
            <i class="fas fa-link me-1"></i>
            {{ $t('examDetail.shareLinkLabel') || '공유 링크' }}
          </label>
          <div class="input-group">
            <input 
              :value="shareUrl" 
              type="text" 
              class="form-control" 
              readonly
            />
            <button 
              class="btn btn-outline-secondary" 
              @click="copyLink"
              :disabled="!shareUrl"
            >
              <i class="fas fa-copy" :class="{ 'me-1': !isMobileDevice }"></i>
              <span v-if="!isMobileDevice">{{ $t('examDetail.copyLink') || '복사' }}</span>
            </button>
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" @click="close">
          <i class="fas fa-times" :class="{ 'me-1': !isMobileDevice }"></i>
          <span v-if="!isMobileDevice">{{ $t('examDetail.cancel') || '취소' }}</span>
        </button>
        <button 
          class="btn btn-primary" 
          @click="sendEmail"
          :disabled="!email || isSending || !isValidEmail(email)"
        >
          <i class="fas fa-paper-plane" :class="{ 'me-1': !isMobileDevice }"></i>
          <span v-if="!isMobileDevice">
            <span v-if="isSending">
              {{ $t('examDetail.sending') || '전송 중...' }}
            </span>
            <span v-else>
              {{ $t('examDetail.sendEmail') || '이메일 전송' }}
            </span>
          </span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { debugLog } from '@/utils/debugUtils'

export default {
  name: 'ShareModal',
  props: {
    show: {
      type: Boolean,
      default: false
    },
    shareUrl: {
      type: String,
      default: ''
    },
    examId: {
      type: String,
      required: false,
      default: ''
    },
    isMobileDevice: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      email: '',
      isSending: false
    }
  },
  methods: {
    close() {
      this.$emit('close')
      this.email = ''
    },
    async copyLink() {
      if (!this.shareUrl) return
      
      try {
        await navigator.clipboard.writeText(this.shareUrl)
        this.$emit('success', this.$t('examDetail.urlCopied') || '링크가 복사되었습니다.')
      } catch (error) {
        // 폴백: 기존 방식으로 복사
        this.fallbackCopyToClipboard(this.shareUrl)
      }
    },
    fallbackCopyToClipboard(text) {
      const textArea = document.createElement('textarea')
      textArea.value = text
      textArea.style.position = 'fixed'
      textArea.style.left = '-999999px'
      textArea.style.top = '-999999px'
      document.body.appendChild(textArea)
      textArea.focus()
      textArea.select()
      
      try {
        document.execCommand('copy')
        this.$emit('success', this.$t('examDetail.urlCopied') || '링크가 복사되었습니다.')
      } catch (err) {
        debugLog('Fallback 복사 실패:', err, 'error')
        this.$emit('error', this.$t('examDetail.urlCopyFailed') || '링크 복사에 실패했습니다.')
      } finally {
        document.body.removeChild(textArea)
      }
    },
    isValidEmail(email) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      return emailRegex.test(email)
    },
    async sendEmail() {
      if (!this.email || !this.isValidEmail(this.email)) {
        this.$emit('error', this.$t('examDetail.invalidEmail') || '유효한 이메일 주소를 입력하세요.')
        return
      }
      
      if (!this.shareUrl) {
        this.$emit('error', this.$t('examDetail.noShareUrl') || '공유 링크를 생성할 수 없습니다.')
        return
      }
      
      this.isSending = true
      
      if (!this.examId) {
        this.$emit('error', '시험 ID가 없습니다.')
        return
      }
      
      try {
        await axios.post('/api/exam/share/', {
          exam_id: this.examId,
          email: this.email,
          share_url: this.shareUrl
        })
        
        this.$emit('success', this.$t('examDetail.emailSent') || '이메일이 전송되었습니다.')
        this.close()
      } catch (error) {
        debugLog('이메일 전송 실패:', error, 'error')
        const errorMessage = error.response?.data?.error || 
          this.$t('examDetail.emailSendFailed') || '이메일 전송에 실패했습니다.'
        this.$emit('error', errorMessage)
      } finally {
        this.isSending = false
      }
    }
  },
  watch: {
    show(newVal) {
      if (newVal) {
        this.email = ''
      }
    }
  }
}
</script>

<style scoped>
/* 공유 모달 스타일 */
.share-modal .modal-header {
  padding: 20px;
  border-bottom: 1px solid #dee2e6;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.share-modal .modal-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.share-modal .modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #6c757d;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.share-modal .modal-close:hover {
  background-color: #f8f9fa;
  color: #495057;
}

.share-modal .modal-body {
  padding: 20px;
}

.share-modal .modal-footer {
  padding: 20px;
  border-top: 1px solid #dee2e6;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.share-modal .form-label {
  font-weight: 500;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.share-modal .input-group {
  display: flex;
}

.share-modal .input-group .form-control {
  border-top-right-radius: 0;
  border-bottom-right-radius: 0;
}

.share-modal .input-group .btn {
  border-top-left-radius: 0;
  border-bottom-left-radius: 0;
  border-left: none;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
</style>

