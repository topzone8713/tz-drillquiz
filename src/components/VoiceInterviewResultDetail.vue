<template>
  <div class="voice-interview-result-detail">
    <div class="container">
      <!-- 제목 섹션 -->
      <div class="mb-4">
        <div class="d-flex justify-content-between align-items-center">
          <h2>
            <i class="fas fa-microphone-alt text-primary me-2"></i>
            {{ $t('voiceInterview.resultDetail.title') || 'Voice Interview 결과' }}
          </h2>
          <button @click="goBack" class="btn btn-secondary">
            <i class="fas fa-arrow-left me-1"></i>
            {{ $t('voiceInterview.resultDetail.back') || '돌아가기' }}
          </button>
        </div>
      </div>

      <!-- 로딩 중 -->
      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">{{ $t('voiceInterview.resultDetail.loading') || '로딩 중...' }}</span>
        </div>
        <p class="mt-2">{{ $t('voiceInterview.resultDetail.loadingText') || '결과를 불러오는 중입니다...' }}</p>
      </div>

      <!-- 에러 메시지 -->
      <div v-else-if="error" class="alert alert-danger">
        <i class="fas fa-exclamation-triangle me-2"></i>
        {{ error }}
      </div>

      <!-- 결과 내용 -->
      <div v-else-if="result" class="result-content">
        <!-- 시험 정보 -->
        <div class="card mb-4">
          <div class="card-header">
            <h5 class="card-title mb-0">
              <i class="fas fa-info-circle me-2"></i>
              {{ $t('voiceInterview.resultDetail.examInfo') || '시험 정보' }}
            </h5>
          </div>
          <div class="card-body">
            <div class="row">
              <div class="col-md-6">
                <p><strong>{{ $t('voiceInterview.resultDetail.examTitle') || '시험 제목' }}:</strong> 
                  {{ getExamTitle(result.exam) }}
                </p>
                <p><strong>{{ $t('voiceInterview.resultDetail.completedAt') || '완료일시' }}:</strong> 
                  {{ formatDateTime(result.completed_at) }}
                </p>
              </div>
              <div class="col-md-6">
                <p><strong>{{ $t('voiceInterview.resultDetail.elapsedTime') || '소요 시간' }}:</strong> 
                  {{ formatTime(result.elapsed_seconds) }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- 결과 요약 -->
        <div class="card mb-4">
          <div class="card-header">
            <h5 class="card-title mb-0">
              <i class="fas fa-chart-bar text-primary me-2"></i>
              {{ $t('voiceInterview.resultsTitle') || '인터뷰 결과' }}
            </h5>
          </div>
          <div class="card-body">
            <div class="results-summary">
              <div class="summary-item">
                <span class="summary-label">{{ $t('voiceInterview.totalQuestions') || '전체 문제' }}</span>
                <span class="summary-value">{{ result.total_score }}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">{{ $t('voiceInterview.correctAnswers') || '정답' }}</span>
                <span class="summary-value correct">{{ result.correct_count }}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">{{ $t('voiceInterview.wrongAnswers') || '오답' }}</span>
                <span class="summary-value wrong">{{ result.wrong_count }}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">{{ $t('voiceInterview.accuracy') || '정확도' }}</span>
                <span class="summary-value" :class="{ 'high': result.accuracy >= 80, 'medium': result.accuracy >= 60 && result.accuracy < 80, 'low': result.accuracy < 60 }">
                  {{ result.accuracy.toFixed(1) }}%
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- 문제별 상세 결과 -->
        <div class="card">
          <div class="card-header">
            <h5 class="card-title mb-0">
              <i class="fas fa-list-ul me-2"></i>
              {{ $t('voiceInterview.questionDetails') || '문제별 상세 결과' }}
            </h5>
          </div>
          <div class="card-body">
            <div class="results-table-container">
              <table class="results-table">
                <thead>
                  <tr>
                    <th class="col-number">#</th>
                    <th class="col-question">{{ $t('voiceInterview.question') || '문제' }}</th>
                    <th class="col-answer">{{ $t('voiceInterview.yourAnswer') || '답변' }}</th>
                    <th class="col-evaluation">{{ $t('voiceInterview.evaluation') || '평가 내용' }}</th>
                    <th class="col-result">{{ $t('voiceInterview.result') || '결과' }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr 
                    v-for="(detail, index) in result.details" 
                    :key="detail.id"
                    :class="{ 'correct': detail.is_correct, 'wrong': !detail.is_correct }"
                  >
                    <td class="col-number">{{ index + 1 }}</td>
                    <td class="col-question" :title="getQuestionTitle(detail.question)">
                      {{ truncateText(getQuestionTitle(detail.question), 30) }}
                    </td>
                    <td class="col-answer" :title="detail.user_answer">
                      {{ truncateText(detail.user_answer, 40) }}
                    </td>
                    <td class="col-evaluation" :title="detail.evaluation">
                      <div class="evaluation-content">
                        {{ truncateText(detail.evaluation || '-', 50) }}
                      </div>
                    </td>
                    <td class="col-result">
                      <i v-if="detail.is_correct" class="fas fa-check-circle text-success"></i>
                      <i v-else class="fas fa-times-circle text-danger"></i>
                      <span>{{ detail.is_correct ? ($t('voiceInterview.correct') || '정답') : ($t('voiceInterview.wrong') || '오답') }}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../services/api'

export default {
  name: 'VoiceInterviewResultDetail',
  data() {
    return {
      result: null,
      loading: true,
      error: null
    }
  },
  mounted() {
    this.loadResult()
  },
  methods: {
    async loadResult() {
      const resultId = this.$route.params.resultId
      if (!resultId) {
        this.error = this.$t('voiceInterview.resultDetail.noResultId') || '결과 ID가 없습니다.'
        this.loading = false
        return
      }

      try {
        this.loading = true
        const response = await api.get(`/api/voice-interview-result/${resultId}/`)
        this.result = response.data
      } catch (error) {
        console.error('Voice Interview 결과 조회 실패:', error)
        this.error = error.response?.data?.error || this.$t('voiceInterview.resultDetail.loadError') || '결과를 불러오는 중 오류가 발생했습니다.'
      } finally {
        this.loading = false
      }
    },
    getExamTitle(exam) {
      if (!exam) return 'Unknown'
      return exam.title_ko || exam.title_en || exam.title || 'Unknown'
    },
    getQuestionTitle(question) {
      if (!question) return '제목 없음'
      return question.title_ko || question.title_en || question.title || '제목 없음'
    },
    formatDateTime(dateTime) {
      if (!dateTime) return '-'
      const date = new Date(dateTime)
      const currentLang = this.$i18n?.locale || 'en'
      const localeMap = {
        'ko': 'ko-KR',
        'en': 'en-US',
        'es': 'es-ES',
        'zh': 'zh-CN',
        'ja': 'ja-JP'
      }
      const locale = localeMap[currentLang] || 'en-US'
      return date.toLocaleString(locale, {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    },
    formatTime(seconds) {
      if (!seconds) {
        const currentLang = this.$i18n?.locale || 'en'
        if (currentLang === 'ko') return '0초'
        else if (currentLang === 'ja') return '0秒'
        else if (currentLang === 'zh') return '0秒'
        else if (currentLang === 'es') return '0s'
        else return '0s'
      }
      
      const currentLang = this.$i18n?.locale || 'en'
      const hours = Math.floor(seconds / 3600)
      const minutes = Math.floor((seconds % 3600) / 60)
      const secs = seconds % 60
      
      if (currentLang === 'ko') {
        if (hours > 0) {
          return `${hours}시간 ${minutes}분 ${secs}초`
        } else if (minutes > 0) {
          return `${minutes}분 ${secs}초`
        } else {
          return `${secs}초`
        }
      } else if (currentLang === 'ja') {
        if (hours > 0) {
          return `${hours}時間 ${minutes}分 ${secs}秒`
        } else if (minutes > 0) {
          return `${minutes}分 ${secs}秒`
        } else {
          return `${secs}秒`
        }
      } else if (currentLang === 'zh') {
        if (hours > 0) {
          return `${hours}小时 ${minutes}分 ${secs}秒`
        } else if (minutes > 0) {
          return `${minutes}分 ${secs}秒`
        } else {
          return `${secs}秒`
        }
      } else if (currentLang === 'es') {
        if (hours > 0) {
          return `${hours}h ${minutes}m ${secs}s`
        } else if (minutes > 0) {
          return `${minutes}m ${secs}s`
        } else {
          return `${secs}s`
        }
      } else {
        // English
        if (hours > 0) {
          return `${hours}h ${minutes}m ${secs}s`
        } else if (minutes > 0) {
          return `${minutes}m ${secs}s`
        } else {
          return `${secs}s`
        }
      }
    },
    truncateText(text, maxLength) {
      if (!text) return '-'
      if (text.length <= maxLength) return text
      return text.substring(0, maxLength) + '...'
    },
    goBack() {
      if (this.result && this.result.exam) {
        // Voice Interview 결과 목록 페이지로 이동
        this.$router.push(`/exam/${this.result.exam.id}/voice-interview-results`)
      } else {
        this.$router.go(-1)
      }
    }
  }
}
</script>

<style scoped>
.voice-interview-result-detail {
  padding: 20px 0;
  min-height: 100vh;
  background-color: #f5f5f5;
}

.result-content {
  max-width: 1200px;
  margin: 0 auto;
}

.card {
  border: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
}

.card-header {
  background-color: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
  padding: 15px 20px;
}

.card-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #333;
}

.results-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  padding: 20px 0;
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.summary-label {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 8px;
}

.summary-value {
  font-size: 1.8rem;
  font-weight: 600;
  color: #333;
}

.summary-value.correct {
  color: #28a745;
}

.summary-value.wrong {
  color: #dc3545;
}

.summary-value.high {
  color: #28a745;
}

.summary-value.medium {
  color: #ffc107;
}

.summary-value.low {
  color: #dc3545;
}

.results-table-container {
  overflow-x: auto;
}

.results-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
}

.results-table thead {
  background-color: #f8f9fa;
}

.results-table th {
  padding: 12px;
  text-align: left;
  font-weight: 600;
  border-bottom: 2px solid #dee2e6;
  color: #333;
}

.results-table td {
  padding: 12px;
  border-bottom: 1px solid #dee2e6;
}

.results-table tbody tr:hover {
  background-color: #f8f9fa;
}

.results-table tbody tr.correct {
  background-color: #d4edda;
}

.results-table tbody tr.wrong {
  background-color: #f8d7da;
}

.col-number {
  width: 50px;
  text-align: center;
}

.col-question {
  min-width: 200px;
  max-width: 300px;
}

.col-answer {
  min-width: 200px;
  max-width: 300px;
}

.col-evaluation {
  min-width: 250px;
  max-width: 400px;
}

.col-result {
  width: 100px;
  text-align: center;
}

.evaluation-content {
  max-height: 100px;
  overflow-y: auto;
}

@media (max-width: 768px) {
  .results-summary {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .results-table {
    font-size: 0.9rem;
  }
  
  .results-table th,
  .results-table td {
    padding: 8px;
  }
  
  /* Back 버튼을 원형 버튼으로 */
  .btn-secondary {
    padding: 0 !important;
    width: 40px !important;
    height: 40px !important;
    border-radius: 50% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    min-width: auto !important;
    font-size: 0 !important;
    position: relative;
  }
  
  .btn-secondary i,
  .btn-secondary > * {
    display: none !important;
  }
  
  .btn-secondary::after {
    content: '\f060'; /* Font Awesome arrow-left icon */
    font-family: 'Font Awesome 5 Free';
    font-weight: 900;
    font-size: 16px !important;
    color: #fff;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
  }
}
</style>

