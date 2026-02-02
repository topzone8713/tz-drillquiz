<template>
  <div class="results-modern">
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
    
    <!-- Modal Confirm -->
    <div v-if="showModal" class="modal-overlay" @click="cancelModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h5 class="modal-title">
            <i :class="modalIcon"></i>
            {{ modalTitle }}
          </h5>
          <button class="modal-close" @click="cancelModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <p class="mb-0">{{ modalMessage }}</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="cancelModal">
            {{ modalCancelText }}
          </button>
          <button class="btn" :class="modalConfirmButtonClass" @click="confirmModal">
            <i class="fas fa-check me-1"></i>
            {{ modalConfirmText }}
          </button>
        </div>
      </div>
    </div>
    
    <div class="results-container">
      <!-- Top Header -->
      <div class="top-header">
        <div class="header-actions">

          <router-link v-if="examId" to="/results" class="action-btn action-btn-secondary">
            <i class="fas fa-list"></i>
            <span class="action-label">{{ $t('results.allResults') }}</span>
          </router-link>

        </div>
      </div>

      <!-- Page Title -->
      <div class="page-title">
        <h1>{{ pageTitle }}</h1>
      </div>

      <!-- Results List -->
      <div class="card-modern results-list-card">
        <div class="card-header-modern">
          <h3>{{ examId ? $t('results.examResults') : $t('results.allExamResults') }}</h3>
          <div class="card-actions">
            <button @click="refreshResults" class="action-btn action-btn-info">
              <i class="fas fa-sync-alt"></i>
              <span class="action-label">{{ $t('results.refresh') }}</span>
            </button>
          </div>
        </div>

        <!-- 로딩 중 -->
        <div v-if="loading" class="text-center py-4">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">{{ $t('results.loading') }}</span>
          </div>
          <p class="mt-2">{{ $t('results.loadingText') }}</p>
        </div>

        <!-- 결과 없음 -->
        <div v-else-if="filteredResults.length === 0" class="empty-state">
          <i class="fas fa-chart-line empty-icon"></i>
          <p>{{ examId ? $t('results.noExamResults') : $t('results.noResults') }}</p>
        </div>

        <!-- 결과 테이블 -->
        <div v-else class="results-table">
          <div class="table-header">
            <div class="table-cell">{{ $t('results.table.examTitle') }}</div>
            <div class="table-cell">{{ $t('results.table.study') }}</div>
            <div class="table-cell">{{ $t('results.table.score') }}</div>
            <div class="table-cell">{{ $t('results.table.correctCount') }}</div>
            <div class="table-cell">{{ $t('results.table.wrongCount') }}</div>
            <div class="table-cell">{{ $t('results.table.elapsedTime') }}</div>
            <div class="table-cell" v-if="isAdmin">{{ $t('results.table.management') }}</div>
          </div>
          
          <div class="table-body">
                         <div v-for="result in paginatedResults" :key="result.id" class="table-row">
               <div class="table-cell">
                 <router-link v-if="result.exam && result.exam.id" :to="`/exam-detail/${result.exam.id}`" class="result-link">
                   {{ getExamTitle(result.exam) }}
                   <small class="text-muted d-block">{{ formatDate(result.completed_at) }} {{ formatTime(result.completed_at) }}</small>
                 </router-link>
                 <span v-else class="result-link text-muted">시험 정보 없음</span>
               </div>
                                            <div class="table-cell">
                 <span class="study-name" v-if="result.exam && result.exam.study && result.exam.study.title_ko">{{ getStudyTitle(result.exam.study) }}</span>
                 <span class="text-muted" v-else>-</span>
               </div>
               <div class="table-cell">
                 <span class="score-badge" v-if="result.score !== null && result.total_score !== null">
                   {{ result.score }}/{{ result.total_score }}
                 </span>
                 <span class="text-muted" v-else>-</span>
               </div>
               <div class="table-cell">
                 <span class="correct-count">{{ result.correct_count }}</span>
               </div>
               <div class="table-cell">
                 <span class="wrong-count">{{ result.wrong_count }}</span>
               </div>
                              <div class="table-cell">{{ formatElapsed(result.elapsed_seconds) }}</div>
              <div class="table-cell" v-if="isAdmin">
                <div class="action-buttons">
                  <router-link
                    v-if="result.exam && result.exam.id"
                    :to="`/take-exam/${result.exam.id}?returnTo=results`"
                    class="action-btn action-btn-warning btn-sm"
                  >
                    <i class="fas fa-redo"></i>
                    <span class="action-label">다시풀기</span>
                  </router-link>
                  <router-link
                    v-if="result.exam && result.exam.id"
                    :to="`/take-exam/${result.exam.id}?continue=true&result_id=${result.id}&returnTo=results`"
                    class="action-btn action-btn-info btn-sm"
                  >
                    <i class="fas fa-play"></i>
                    <span class="action-label">이어풀기</span>
                  </router-link>
                  <button 
                    class="action-btn action-btn-danger btn-sm" 
                    @click="deleteResult(result)"
                  >
                    <i class="fas fa-trash"></i>
                    <span class="action-label">삭제</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 페이지네이션 -->
        <div v-if="totalPages > 1" class="pagination-container">
          <div class="pagination">
            <button 
              @click="goToFirstPage" 
              :disabled="currentPage === 1"
              class="pagination-btn"
              title="첫 페이지"
            >
              <i class="fas fa-angle-double-left"></i>
            </button>
            
            <button 
              @click="goToPreviousPage" 
              :disabled="currentPage === 1"
              class="pagination-btn"
              title="이전 페이지"
            >
              <i class="fas fa-angle-left"></i>
            </button>
            
            <button 
              v-for="page in pageNumbers" 
              :key="page"
              @click="goToPage(page)"
              :class="['pagination-btn', { active: currentPage === page }]"
            >
              {{ page }}
            </button>
            
            <button 
              @click="goToNextPage" 
              :disabled="currentPage === totalPages"
              class="pagination-btn"
              title="다음 페이지"
            >
              <i class="fas fa-angle-right"></i>
            </button>
            
            <button 
              @click="goToLastPage" 
              :disabled="currentPage === totalPages"
              class="pagination-btn"
              title="마지막 페이지"
            >
              <i class="fas fa-angle-double-right"></i>
            </button>
          </div>
          
          <div class="pagination-info">
            {{ (currentPage - 1) * itemsPerPage + 1 }}-{{ Math.min(currentPage * itemsPerPage, filteredResults.length) }} / {{ filteredResults.length }}개
          </div>
        </div>
      </div>


    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { formatLocalDate } from '@/utils/dateUtils'
import { debugLog } from '@/utils/debugUtils'
import { isAdmin, hasStudyAdminRole, getCurrentUser as getCurrentUserFromPermissions } from '@/utils/permissionUtils'
import { SUPPORTED_LANGUAGES } from '@/utils/multilingualUtils'

export default {
  name: 'Results',
  data() {
    return {
      allResults: [],
      examId: null,
      examTitle: '',
      loading: true,
      // Toast 알림 설정
      showToast: false,
      toastMessage: '',
      toastType: 'success',
      toastIcon: 'fas fa-check',
      // 모달 설정
      showModal: false,
      modalTitle: '',
      modalMessage: '',
      modalConfirmText: '',
      modalCancelText: '',
      modalConfirmButtonClass: 'btn-success',
      modalIcon: 'fas fa-question',
      modalCallback: null,
      // 페이지네이션 설정
      currentPage: 1,
      itemsPerPage: 10
    }
  },
  computed: {
    pageTitle() {
      if (this.examId && this.examTitle) {
        return `${this.examTitle} - ${this.$t('results.examResults')}`
      }
      return this.$t('results.examResults')
    },
    filteredResults() {
      if (this.examId) {
        return this.allResults.filter(result => result.exam && result.exam.id === this.examId)
      }
      return this.allResults
    },
    isAuthenticated() {
      return Boolean(getCurrentUserFromPermissions())
    },
    isAdmin() {
      return isAdmin()
    },
    isStudyAdmin() {
      return hasStudyAdminRole()
    },
    // 페이지네이션 관련 computed 속성들
    totalPages() {
      return Math.ceil(this.filteredResults.length / this.itemsPerPage)
    },
    paginatedResults() {
      const start = (this.currentPage - 1) * this.itemsPerPage
      const end = start + this.itemsPerPage
      return this.filteredResults.slice(start, end)
    },
    pageNumbers() {
      const pages = []
      const maxVisiblePages = 5
      const startPage = Math.max(1, this.currentPage - Math.floor(maxVisiblePages / 2))
      const endPage = Math.min(this.totalPages, startPage + maxVisiblePages - 1)
      
      for (let i = startPage; i <= endPage; i++) {
        pages.push(i)
      }
      return pages
    }
  },
  async mounted() {
    // 로그인하지 않은 사용자인 경우 로그인 화면으로 이동
    if (!this.isAuthenticated) {
      this.$router.push('/login')
      return
    }
    
    this.examId = this.$route.query.exam_id
    await this.loadResults()
  },
  methods: {
    // 다국어 제목 처리 메서드들
    getExamTitle(exam) {
      if (!exam) return '';
      
      // 사용자 프로필 언어 우선, 없으면 i18n locale, 기본값은 'en'
      const userLang = this.userProfileLanguage || this.$i18n?.locale || 'en'
      
      // 모든 지원 언어 필드를 확인하여 사용자 언어에 맞는 값 반환
      const supportedLanguages = SUPPORTED_LANGUAGES
      
      // 사용자 언어 우선
      if (exam[`title_${userLang}`]) {
        return exam[`title_${userLang}`]
      }
      
      // 영어 폴백 (기본 언어)
      if (exam.title_en) {
        return exam.title_en
      }
      
      // 다른 지원 언어 확인
      for (const lang of supportedLanguages) {
        if (exam[`title_${lang}`]) {
          return exam[`title_${lang}`]
        }
      }
      
      // 기본 title 필드 폴백
      if (exam.title) {
        return exam.title
      }
      
      // 최종 폴백
      return userLang === 'ko' ? '제목 없음' : 'No Title'
    },
    
    getStudyTitle(study) {
      if (!study) return '';
      
      // 사용자 프로필 언어 우선, 없으면 i18n locale, 기본값은 'en'
      const userLang = this.userProfileLanguage || this.$i18n?.locale || 'en'
      
      // 모든 지원 언어 필드를 확인하여 사용자 언어에 맞는 값 반환
      const supportedLanguages = SUPPORTED_LANGUAGES
      
      // 사용자 언어 우선
      if (study[`title_${userLang}`]) {
        return study[`title_${userLang}`]
      }
      
      // 영어 폴백 (기본 언어)
      if (study.title_en) {
        return study.title_en
      }
      
      // 다른 지원 언어 확인
      for (const lang of supportedLanguages) {
        if (study[`title_${lang}`]) {
          return study[`title_${lang}`]
        }
      }
      
      // 기본 title 필드 폴백
      if (study.title) {
        return study.title
      }
      
      // 최종 폴백
      return userLang === 'ko' ? '제목 없음' : 'No Title'
    },
    
    // 토스트 알림 메서드들
    showToastNotification(message, type = 'success', icon = null) {
      this.toastMessage = message
      this.toastType = type
      this.toastIcon = icon || this.getToastIcon(type)
      this.showToast = true
      
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
    
    // 모달 메서드들
    showConfirmModal(title, message, confirmText = '확인', cancelText = '취소', confirmButtonClass = 'btn-success', icon = 'fas fa-question', callback = null) {
      this.modalTitle = title
      this.modalMessage = message
      this.modalConfirmText = confirmText
      this.modalCancelText = cancelText
      this.modalConfirmButtonClass = confirmButtonClass
      this.modalIcon = icon
      this.modalCallback = callback
      this.showModal = true
    },
    
    confirmModal() {
      if (this.modalCallback) {
        this.modalCallback()
      }
      this.hideModal()
    },
    
    cancelModal() {
      this.hideModal()
    },
    
    hideModal() {
      this.showModal = false
      this.modalCallback = null
    },
    
    // 페이지네이션 메서드들
    goToPage(page) {
      if (page >= 1 && page <= this.totalPages) {
        this.currentPage = page
      }
    },
    
    goToFirstPage() {
      this.currentPage = 1
    },
    
    goToLastPage() {
      this.currentPage = this.totalPages
    },
    
    goToPreviousPage() {
      if (this.currentPage > 1) {
        this.currentPage--
      }
    },
    
    goToNextPage() {
      if (this.currentPage < this.totalPages) {
        this.currentPage++
      }
    },

    async loadResults() {
      this.loading = true
      try {
        debugLog('시험 결과 로드 시작...')
        const response = await axios.get('/api/exam-results/')
        debugLog('API 응답:', response.data)
        debugLog('API 응답 첫 번째 항목:', response.data[0])
        
        // 응답 데이터 구조 확인
        let resultsData = response.data
        if (response.data && response.data.results) {
          // 페이지네이션 응답 형식
          resultsData = response.data.results
          debugLog('페이지네이션 응답에서 results 추출:', resultsData)
        }
        
        if (!Array.isArray(resultsData)) {
          debugLog('응답이 배열이 아님:', resultsData)
          resultsData = []
        }
        
        // exam 필드가 있는 결과만 필터링
        const validResults = resultsData.filter(result => {
          const isValid = result && result.exam && result.exam.id
          if (!isValid) {
            debugLog('유효하지 않은 결과 제외:', result)
          }
          return isValid
        })
        
        // 스터디 정보가 있는 경우 로그
        validResults.forEach(result => {
          debugLog('결과 정보:', {
            id: result.id,
            exam: this.getExamTitle(result.exam),
            study: result.study ? this.getStudyTitle(result.study) : null,
            score: result.score,
            total_score: result.total_score
          })
        })
        
        this.allResults = validResults
        
        if (this.examId) {
          const examResults = this.allResults.filter(result => result.exam && result.exam.id === this.examId)
          if (examResults.length > 0) {
            this.examTitle = this.getExamTitle(examResults[0].exam)
          }
        }
        
        debugLog('로드된 결과 수:', this.allResults.length)
        debugLog('유효한 결과 샘플:', this.allResults.slice(0, 2))
        
        if (this.allResults.length === 0) {
          this.showToastNotification('표시할 시험 결과가 없습니다.', 'info')
        }
      } catch (error) {
        debugLog('시험 결과를 불러오는데 실패했습니다:', error, 'error')
        debugLog('오류 상세:', error.response?.data)
        debugLog('오류 상태:', error.response?.status)
        
        let errorMessage = this.$t('results.errors.loadFailed')
        if (error.response?.status === 401) {
          errorMessage = this.$t('results.errors.loginRequired')
        } else if (error.response?.status === 403) {
          errorMessage = this.$t('results.errors.accessDenied')
        } else if (error.response?.status === 404) {
          errorMessage = this.$t('results.errors.notFound')
        }
        
        this.showToastNotification(errorMessage, 'error')
        this.allResults = []
      } finally {
        this.loading = false
      }
    },

    async refreshResults() {
      await this.loadResults()
      this.showToastNotification(this.$t('results.refreshSuccess'), 'success')
    },

    formatDate(dateString) {
      return formatLocalDate(dateString)
    },

    formatTime(dateString) {
      if (!dateString) return ''
      const date = new Date(dateString)
      const hours = date.getHours().toString().padStart(2, '0')
      const minutes = date.getMinutes().toString().padStart(2, '0')
      return `${hours}:${minutes}`
    },

    formatElapsed(sec) {
      if (!sec) return '0:00'
      const m = Math.floor(sec / 60)
      const s = sec % 60
      return `${m}:${s.toString().padStart(2, '0')}`
    },

    async deleteResult(result) {
      this.showConfirmModal(
        this.$t('results.delete.title'),
        this.$t('results.delete.confirm'),
        this.$t('results.delete.confirmButton'),
        this.$t('results.delete.cancelButton'),
        'btn-danger',
        'fas fa-trash',
        () => this.executeDeleteResult(result)
      )
    },

    async executeDeleteResult(result) {
      try {
        await axios.delete(`/api/exam-result/${result.id}/`)
        this.allResults = this.allResults.filter(r => r.id !== result.id)
        this.recentResults = this.recentResults.filter(r => r.id !== result.id)
        this.showToastNotification(this.$t('results.delete.success'), 'success')
      } catch (error) {
        debugLog('결과 삭제 실패:', error, 'error')
        this.showToastNotification(this.$t('results.delete.failed'), 'error')
      }
    }
  }
}
</script>

<style scoped>
/* Modern Results Styles */
.results-modern {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.results-container {
  max-width: 1400px;
  margin: 0 auto;
  background: white;
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

/* Top Header */
.top-header {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 20px 30px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: flex-end;
}

/* Action Button Styles */
.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: 2px solid #e9ecef;
  border-radius: 25px;
  background: white;
  color: #6c757d;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  text-decoration: none;
}

.action-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn-primary {
  border-color: #007bff;
  background: #007bff;
  color: white;
}

.action-btn-primary:hover:not(:disabled) {
  background: #0056b3;
  border-color: #0056b3;
}

.action-btn-secondary {
  border-color: #6c757d;
  background: white;
  color: #6c757d;
}

.action-btn-secondary:hover:not(:disabled) {
  background: #6c757d;
  border-color: #6c757d;
  color: white;
}

.action-btn-success {
  border-color: #28a745;
  background: #28a745;
  color: white;
}

.action-btn-success:hover:not(:disabled) {
  background: #218838;
  border-color: #1e7e34;
}

.action-btn-info {
  border-color: #17a2b8;
  background: #17a2b8;
  color: white;
}

.action-btn-info:hover:not(:disabled) {
  background: #138496;
  border-color: #117a8b;
}

.action-btn-warning {
  border-color: #ffc107;
  background: #ffc107;
  color: #212529;
}

.action-btn-warning:hover:not(:disabled) {
  background: #e0a800;
  border-color: #d39e00;
}

.action-btn-danger {
  border-color: #dc3545;
  background: #dc3545;
  color: white;
}

.action-btn-danger:hover:not(:disabled) {
  background: #c82333;
  border-color: #bd2130;
}

.action-label {
  font-size: 12px;
  font-weight: 500;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

/* Page Title */
.page-title {
  padding: 30px;
  background: white;
  border-bottom: 1px solid #e9ecef;
}

.page-title h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  color: #2c3e50;
}

/* Card Styles */
.card-modern {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  padding: 30px;
  margin: 20px 30px;
  border: 1px solid #e9ecef;
}

.card-header-modern {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e9ecef;
}

.card-header-modern h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
}

.card-actions {
  display: flex;
  gap: 10px;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #6c757d;
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

/* Results Table */
.results-table,
.recent-results-table {
  background: white;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.table-header {
  display: grid;
  grid-template-columns: 2fr 1.5fr 1fr 0.8fr 0.8fr 1fr 1.5fr;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-weight: 600;
  font-size: 14px;
  padding: 16px 20px;
}

.table-body {
  max-height: 400px;
  overflow-y: auto;
}

.table-row {
  display: grid;
  grid-template-columns: 2fr 1.5fr 1fr 0.8fr 0.8fr 1fr 1.5fr;
  padding: 16px 20px;
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
  font-size: 14px;
}

.result-link {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s ease;
}

.result-link:hover {
  color: #764ba2;
  text-decoration: underline;
}

.text-muted {
  color: #6c757d !important;
  opacity: 0.7;
}

.score-badge {
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.correct-count {
  color: #28a745;
  font-weight: 600;
}

.wrong-count {
  color: #dc3545;
  font-weight: 600;
}

.study-name {
  color: #17a2b8;
  font-weight: 500;
  font-size: 0.9rem;
}

.action-buttons {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

/* Toast Notifications - 모든 스타일은 공통 CSS (mobile-buttons.css)에 정의됨 */

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

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000; /* 모달 오버레이 */
  animation: fadeIn 0.3s ease-out;
}

.modal-content {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow: hidden;
  animation: slideInUp 0.3s ease-out;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #e9ecef;
  background: #f8f9fa;
}

.modal-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 10px;
}

.modal-close {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #6c757d;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s;
}

.modal-close:hover {
  background: #e9ecef;
  color: #495057;
}

.modal-body {
  padding: 24px;
}

.modal-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding: 20px 24px;
  border-top: 1px solid #e9ecef;
  background: #f8f9fa;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideInUp {
  from {
    transform: translateY(50px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

/* Responsive Design */
@media (max-width: 768px) {
  .results-container {
    margin: 0;
    border-radius: 0;
  }
  
  .card-modern {
    margin: 10px;
    padding: 20px;
  }
  
  .page-title h1 {
    font-size: 2rem;
  }
  
  .card-header-modern {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }
  
  .card-actions {
    width: 100%;
    justify-content: flex-end;
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
  
  /* 페이지네이션 스타일 */
  .pagination-container {
    margin-top: 2rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
  }
  
  .pagination {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: white;
    padding: 1rem;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  }
  
  .pagination-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border: 1px solid #e1e5e9;
    background: white;
    color: #495057;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
    font-weight: 500;
  }
  
  .pagination-btn:hover:not(:disabled) {
    background: #667eea;
    color: white;
    border-color: #667eea;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  }
  
  .pagination-btn.active {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-color: #667eea;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  }
  
  .pagination-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    background: #f8f9fa;
    color: #adb5bd;
  }
  
  .pagination-info {
    color: #6c757d;
    font-size: 0.9rem;
    font-weight: 500;
  }
  
  @media (max-width: 768px) {
    .pagination {
      gap: 0.25rem;
      padding: 0.75rem;
    }
    
    .pagination-btn {
      width: 36px;
      height: 36px;
      font-size: 0.875rem;
    }
  }
}
</style> 