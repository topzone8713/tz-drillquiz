<template>
  <div class="random-practice-modern">
    <div class="random-practice-container">
      <!-- Study Selection Section -->
      <div class="study-selection-section" v-if="!selectedStudy">
        <div class="section-header">
          <h1 class="page-title">{{ $t('randomPractice.title') }}</h1>
        </div>
        

        
        <div class="study-selection-card">
          <div class="card-header">
            <h2 class="card-title">{{ $t('randomPractice.studySelection.title') }}</h2>
          </div>
          
          <div class="card-content">
            <div v-if="loading" class="loading-container">
              <div class="loading-spinner">
                <i class="fas fa-spinner fa-spin"></i>
              </div>
              <p>Loading...</p>
            </div>
            
            <div v-else-if="myStudies && myStudies.length === 0" class="empty-state">
              <i class="fas fa-book-open empty-icon"></i>
              <p>{{ $t('randomPractice.studySelection.noStudies') }}</p>
            </div>
            
            <div v-else class="studies-grid">
              <div class="study-card" v-for="study in filteredStudies" :key="study.id">
                <div class="study-header">
                  <h3 class="study-title">{{ getStudyTitle(study) }}</h3>
                  <p class="study-goal">{{ study.goal }}</p>
                </div>
                
                <div class="study-info">
                  <div class="info-item">
                    <i class="fas fa-calendar-alt info-icon"></i>
                    <span v-if="study.start_date || study.end_date">
                      {{ formatDate(study.start_date) }} ~ {{ formatDate(study.end_date) }}
                    </span>
                    <span v-else class="text-muted">{{ $t('randomPractice.studySelection.noDateRange') }}</span>
                  </div>
                </div>
                
                <div class="study-progress">
                  <div class="progress-item">
                    <i class="fas fa-chart-line progress-icon"></i>
                    <span>{{ $t('randomPractice.studySelection.progress', { progress: (study.overall_progress || 0).toFixed(1) }) }}</span>
                  </div>
                </div>
                
                <div class="study-actions">
                  <button 
                    @click="selectStudy(study)" 
                    class="select-study-btn"
                    :disabled="!study.tasks || study.tasks.length === 0"
                  >
                    <i class="fas fa-play"></i>
                    {{ $t('randomPractice.studySelection.selectStudy') }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Practice Settings Section -->
      <div class="practice-settings-section" v-if="selectedStudy && !currentQuestion">
        <div class="practice-settings-card">
          <div class="card-header">
            <h2 class="card-title">{{ getStudyTitle(selectedStudy) }} - {{ $t('randomPractice.practiceSettings.title') }}</h2>
          </div>
          
          <div class="card-content">
            <div class="settings-grid">
              <div class="study-info-section">
                <h3 class="section-title">{{ $t('randomPractice.practiceSettings.studyInfo') }}</h3>
                <div class="info-list">
                  <div class="info-item">
                    <i class="fas fa-bullseye info-icon"></i>
                    <div class="info-content">
                      <strong>{{ $t('randomPractice.practiceSettings.goal') }}:</strong>
                      <span>{{ selectedStudy.goal }}</span>
                    </div>
                  </div>
                  <div class="info-item">
                    <i class="fas fa-calendar-alt info-icon"></i>
                    <div class="info-content">
                      <strong>{{ $t('randomPractice.practiceSettings.period') }}:</strong>
                      <span v-if="selectedStudy.start_date || selectedStudy.end_date">
                        {{ formatDate(selectedStudy.start_date) }} ~ {{ formatDate(selectedStudy.end_date) }}
                      </span>
                      <span v-else class="text-muted">{{ $t('randomPractice.practiceSettings.noDateRange') }}</span>
                    </div>
                  </div>
                </div>
                
                <div class="study-progress-section">
                  <div class="progress-item">
                    <i class="fas fa-chart-line progress-icon"></i>
                    <div class="progress-content">
                      <strong>{{ $t('randomPractice.practiceSettings.overallProgress') }}:</strong>
                      <span>{{ (selectedStudy.overall_progress || 0).toFixed(1) }}%</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div class="settings-form-section">
                <h3 class="section-title">{{ $t('randomPractice.practiceSettings.practiceSettings') }}</h3>
                <div class="settings-form">
                  <div class="form-group">
                    <label for="questionCount" class="form-label">{{ $t('randomPractice.practiceSettings.questionCount') }}</label>
                    <input 
                      type="number" 
                      class="modern-input" 
                      id="questionCount" 
                      v-model.number="questionCount"
                      min="1" 
                      :max="maxQuestions"
                      required
                    >
                    <div class="form-help">{{ $t('randomPractice.practiceSettings.maxQuestionsNote', { count: maxQuestions }) }}</div>
                  </div>
                  
                  <div class="form-actions">
                    <button @click="startPractice" class="start-practice-btn" :disabled="questionCount < 1">
                      <i class="fas fa-play"></i>
                      <span>{{ $t('randomPractice.practiceSettings.startPractice') }}</span>
                    </button>
                    <button @click="backToStudySelection" class="back-btn">
                      <i class="fas fa-arrow-left"></i>
                      <span>{{ $t('randomPractice.practiceSettings.selectOtherStudy') }}</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Question Practice Section -->
      <div class="question-practice-section" v-if="currentQuestion">
        <div class="question-practice-card">
          <div class="question-header">
            <div class="question-info">
              <h2 class="question-title">{{ $t('randomPractice.question.title', { current: currentQuestionIndex + 1, total: questions.length }) }}</h2>
              <h3 class="question-subtitle">{{ getQuestionTitle(currentQuestion) }}</h3>
            </div>
            <div class="question-controls">
              <div class="timer">
                <i class="fas fa-clock timer-icon"></i>
                <span>{{ $t('randomPractice.question.elapsedTime', { time: formatElapsed(elapsedSeconds) }) }}</span>
              </div>
              <button @click="showAnswer = !showAnswer" class="toggle-answer-btn">
                <i class="fas fa-eye"></i>
                {{ showAnswer ? $t('randomPractice.question.hideAnswer') : $t('randomPractice.question.showAnswer') }}
              </button>
              <button @click="endPractice" class="end-practice-btn">
                <i class="fas fa-stop"></i>
                {{ $t('randomPractice.question.end') }}
              </button>
            </div>
          </div>

          <div class="question-content">
            <div class="question-details">
              <div class="detail-item">
                <i class="fas fa-hashtag detail-icon"></i>
                <div class="detail-content">
                  <strong>{{ $t('randomPractice.question.questionId') }}:</strong>
                  <span>{{ currentQuestion.csv_id }}</span>
                </div>
              </div>
              
              <div class="detail-item">
                <i class="fas fa-tag detail-icon"></i>
                <div class="detail-content">
                  <strong>{{ $t('randomPractice.question.titleLabel') }}:</strong>
                  <span>{{ getQuestionTitle(currentQuestion) }}</span>
                </div>
              </div>
              
              <div class="detail-item">
                <i class="fas fa-question-circle detail-icon"></i>
                <div class="detail-content">
                  <strong>{{ $t('randomPractice.question.content') }}:</strong>
                  <div class="content-box">{{ getQuestionContent(currentQuestion) }}</div>
                </div>
              </div>
              
              <div class="detail-item">
                <i class="fas fa-signal detail-icon"></i>
                <div class="detail-content">
                  <strong>{{ $t('randomPractice.question.difficulty') }}:</strong>
                  <span class="difficulty-badge" :class="getDifficultyClass(currentQuestion.difficulty)">
                    {{ currentQuestion.difficulty }}
                  </span>
                </div>
              </div>
              
              <div class="detail-item" v-if="currentQuestion.url">
                <i class="fas fa-link detail-icon"></i>
                <div class="detail-content">
                  <strong>URL:</strong>
                  <a :href="currentQuestion.url" target="_blank" class="url-link">
                    <i class="fas fa-external-link-alt"></i>
                    {{ currentQuestion.url }}
                  </a>
                </div>
              </div>
              
              <div class="detail-item" v-if="showAnswer">
                <i class="fas fa-lightbulb detail-icon"></i>
                <div class="detail-content">
                  <strong>{{ $t('randomPractice.question.answer') }}:</strong>
                  <div class="answer-box">{{ getQuestionAnswer(currentQuestion) }}</div>
                </div>
              </div>
            </div>

            <div class="answer-section">
              <div class="answer-input-group">
                <label for="answerInput" class="answer-label">{{ $t('randomPractice.question.enterAnswer') }}</label>
                <input 
                  type="text" 
                  class="modern-input" 
                  id="answerInput" 
                  v-model="userAnswer"
                  @keyup.enter="submitAnswer"
                  :placeholder="$t('randomPractice.question.answerPlaceholder')"
                  ref="answerInput"
                >
              </div>

              <div class="answer-actions">
                <button @click="submitAnswer" class="submit-answer-btn">
                  <i class="fas fa-check"></i>
                  {{ $t('randomPractice.question.submitAnswer') }}
                </button>
                <button @click="skipQuestion" class="skip-question-btn">
                  <i class="fas fa-forward"></i>
                  {{ $t('randomPractice.question.skipQuestion') }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Result Modal -->
      <div class="modal fade" id="resultModal" tabindex="-1" ref="resultModal">
        <div class="modal-dialog modal-xl">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">{{ $t('randomPractice.result.title') }}</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
              <div class="result-content">
                <div class="result-icon">
                  <i class="fas fa-trophy"></i>
                </div>
                <h4 class="result-message">{{ resultMessage }}</h4>
                <div class="result-stats">
                  <div class="stat-item">
                    <i class="fas fa-check-circle stat-icon correct"></i>
                    <span>{{ $t('randomPractice.result.correct', { correct: correctCount, total: totalQuestions }) }}</span>
                  </div>
                  <div class="stat-item">
                    <i class="fas fa-percentage stat-icon"></i>
                    <span>{{ $t('randomPractice.result.accuracy', { accuracy: ((correctCount / totalQuestions) * 100).toFixed(1) }) }}</span>
                  </div>
                  <div class="stat-item">
                    <i class="fas fa-clock stat-icon"></i>
                    <span>{{ $t('randomPractice.result.elapsedTime', { time: formatElapsed(elapsedSeconds) }) }}</span>
                  </div>
                </div>
                
                <!-- 문제별 상세 결과 테이블 -->
                <div class="question-results-table" v-if="questionResults.length > 0">
                  <h5 class="table-title">{{ $t('randomPractice.result.questionDetails') }}</h5>
                  <div class="table-container">
                    <table class="results-table">
                      <thead>
                        <tr>
                          <th>{{ $t('randomPractice.result.table.questionNumber') }}</th>
                          <th>{{ $t('randomPractice.result.table.questionTitle') }}</th>
                          <th>{{ $t('randomPractice.result.table.userAnswer') }}</th>
                          <th>{{ $t('randomPractice.result.table.correctAnswer') }}</th>
                          <th>{{ $t('randomPractice.result.table.result') }}</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="(result, index) in questionResults" :key="index" :class="{ 'correct-row': result.isCorrect, 'wrong-row': !result.isCorrect }">
                          <td>{{ result.questionIndex }}</td>
                          <td class="question-title-cell">{{ result.questionTitle }}</td>
                          <td>{{ result.userAnswer || $t('randomPractice.result.table.skipped') }}</td>
                          <td>{{ result.correctAnswer }}</td>
                          <td>
                            <span v-if="result.isCorrect" class="result-badge correct-badge">
                              <i class="fas fa-check"></i> {{ $t('randomPractice.result.table.correct') }}
                            </span>
                            <span v-else class="result-badge wrong-badge">
                              <i class="fas fa-times"></i> {{ $t('randomPractice.result.table.wrong') }}
                            </span>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="close-result-btn" @click="closeResultModal">
                <i class="fas fa-times"></i>
                {{ $t('randomPractice.result.close') }}
              </button>
              <button type="button" class="restart-practice-btn" @click="restartPractice">
                <i class="fas fa-redo"></i>
                {{ $t('randomPractice.result.restart') }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { debugLog } from '@/utils/debugUtils'
import { Modal } from 'bootstrap'
import authService from '@/services/authService'
import { SUPPORTED_LANGUAGES } from '@/utils/multilingualUtils'
import { getLocalizedContentWithI18n } from '@/utils/multilingualUtils'

export default {
  name: 'RandomPractice',
  data() {
    return {
      loading: true,
      studies: [],
      selectedStudy: null,
      questionCount: 10,
      questions: [],
      currentQuestionIndex: 0,
      currentQuestion: null,
      userAnswer: '',
      showAnswer: false,
      elapsedSeconds: 0,
      timer: null,
      correctCount: 0,
      totalQuestions: 0,
      resultModal: null,
      resultMessage: '',
      userProfileLanguage: null,
      questionResults: [], // 문제별 답안 결과 저장
    }
  },
  computed: {
    isAuthenticated() {
      return authService.isAuthenticatedSync()
    },
    filteredStudies() {
      const user = authService.getUserSync()
      if (!user) return []
      
      // admin_role 사용자는 모든 스터디에 접근 가능
      if (user.role === 'admin_role') {
        return this.studies || []
      }
      
      // 일반 사용자는 멤버인 스터디만 필터링
      return (this.studies || []).filter(study =>
        Array.isArray(study.members) &&
        study.members.some(member => member.user === user.id)
      )
    },
    maxQuestions() {
      if (!this.selectedStudy || !this.selectedStudy.tasks) return 0
      return this.selectedStudy.tasks.reduce((total, task) => {
        return total + (task.exam && task.exam.total_questions ? task.exam.total_questions : 0)
      }, 0)
    },
    myStudies() {
      return this.studies || [];
    }
  },
  async mounted() {
    // 로그인하지 않은 사용자인 경우 로그인 화면으로 이동
    if (!this.isAuthenticated) {
      this.$router.push('/login')
      return
    }
    
    this.loading = true
    try {
      await this.getUserProfileLanguage()
      await this.loadStudies()
      this.resultModal = new Modal(this.$refs.resultModal)
    } finally {
      this.loading = false
    }
  },
  beforeUnmount() {
    this.stopTimer()
  },
  methods: {
    // 사용자 프로필 언어 가져오기
    async getUserProfileLanguage() {
      // 컴포넌트 레벨 캐시에 있으면 반환
      if (this.userProfileLanguage) {
        return this.userProfileLanguage
      }
      
      try {
        if (this.isAuthenticated) {
          const { authAPI } = await import('@/services/api')
          const response = await authAPI.getProfile()
          const language = response.data.language || 'en'
          // 컴포넌트 레벨 캐시에 저장
          this.userProfileLanguage = language
          return language
        }
        this.userProfileLanguage = 'en'
        return 'en' // 기본값
      } catch (error) {
        console.error('사용자 프로필 언어 가져오기 실패:', error)
        this.userProfileLanguage = 'en'
        return 'en'
      }
    },
    async loadStudies() {
      try {
        const response = await axios.get('/api/studies/')
        this.studies = response.data.results || response.data || []
      } catch (error) {
        debugLog('스터디 목록 로드 실패:', error, 'error')
      }
    },
    formatDate(dateString) {
      if (!dateString) {
        return '-'
      }
      try {
        const date = new Date(dateString)
        // 유효하지 않은 날짜 체크 (NaN이거나 1970년 이전인 경우)
        if (isNaN(date.getTime()) || date.getFullYear() < 1970) {
          return '-'
        }
        return date.toLocaleDateString('ko-KR')
      } catch (error) {
        return '-'
      }
    },
    formatElapsed(sec) {
      if (!sec) return '0:00'
      const m = Math.floor(sec / 60)
      const s = sec % 60
      return `${m}:${s.toString().padStart(2, '0')}`
    },
    selectStudy(study) {
      this.selectedStudy = study
      this.questionCount = Math.min(10, this.maxQuestions)
    },
    backToStudySelection() {
      this.selectedStudy = null
      this.questionCount = 10
    },
    async startPractice() {
      try {
        // 스터디의 모든 태스크에서 문제 수집
        const allQuestions = []
        for (const task of this.selectedStudy.tasks) {
          if (task.exam && task.exam.questions) {
            allQuestions.push(...task.exam.questions)
          }
        }
        
        if (allQuestions.length === 0) {
          this.$toast?.error?.(this.$t('randomPractice.messages.noQuestions'))
          return
        }
        
        // 랜덤하게 문제 선택
        this.questions = this.shuffleArray(allQuestions).slice(0, this.questionCount)
        this.currentQuestionIndex = 0
        this.currentQuestion = this.questions[0]
        this.correctCount = 0
        this.totalQuestions = this.questions.length
        this.elapsedSeconds = 0
        this.startTimer()
        
        this.$nextTick(() => {
          this.$refs.answerInput?.focus()
        })
      } catch (error) {
        debugLog('문제 풀기 시작 실패:', error, 'error')
        this.$toast?.error?.(this.$t('randomPractice.messages.startFailed'))
      }
    },
    shuffleArray(array) {
      const shuffled = [...array]
      for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1))
        ;[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
      }
      return shuffled
    },
    startTimer() {
      this.timer = setInterval(() => {
        this.elapsedSeconds++
      }, 1000)
    },
    stopTimer() {
      if (this.timer) {
        clearInterval(this.timer)
        this.timer = null
      }
    },
    async submitAnswer() {
      if (!this.userAnswer.trim()) return
      
      // 다국어 답안 필드에서 현재 언어에 맞는 답안 가져오기
      const correctAnswer = this.getQuestionAnswer(this.currentQuestion)
      
      // 사지선다 여부 판단 (정답이 a, b, c, d 또는 1-2글자인 경우)
      const isMultipleChoice = this.isMultipleChoiceAnswer(correctAnswer)
      
      let isCorrect = false
      
      if (isMultipleChoice) {
        // 사지선다: 단순 비교
        isCorrect = correctAnswer.toLowerCase().trim() === 
                   this.userAnswer.toLowerCase().trim()
      } else {
        // 주관식: AI로 의미 판단
        try {
          const userLang = this.userProfileLanguage || this.$i18n?.locale || 'en'
          const response = await axios.post('/api/check-answer/', {
            user_answer: this.userAnswer,
            correct_answer: correctAnswer,
            language: userLang
          })
          
          isCorrect = response.data.is_correct || false
          
          // 디버그 로그
          if (isCorrect) {
            debugLog(`✅ AI 판단: 정답 (신뢰도: ${response.data.confidence}, 제공자: ${response.data.provider})`)
          } else {
            debugLog(`❌ AI 판단: 오답 (신뢰도: ${response.data.confidence}, 이유: ${response.data.reason})`)
          }
        } catch (error) {
          // AI API 실패 시 단순 비교로 폴백
          debugLog('AI 답안 판단 실패, 단순 비교로 폴백:', error)
          isCorrect = correctAnswer.toLowerCase().trim() === 
                     this.userAnswer.toLowerCase().trim()
        }
      }
      
      if (isCorrect) {
        this.correctCount++
      }
      
      // 문제별 결과 저장
      this.questionResults.push({
        questionIndex: this.currentQuestionIndex + 1,
        questionTitle: this.getQuestionTitle(this.currentQuestion),
        userAnswer: this.userAnswer,
        correctAnswer: correctAnswer,
        isCorrect: isCorrect
      })
      
      this.nextQuestion()
    },
    
    isMultipleChoiceAnswer(answer) {
      if (!answer) return false
      
      const trimmed = answer.trim().toLowerCase()
      
      // a, b, c, d 또는 A, B, C, D
      if (/^[a-d]$/i.test(trimmed)) {
        return true
      }
      
      // 1-2글자이고 숫자 또는 단일 문자인 경우
      if (trimmed.length <= 2 && /^[a-z0-9]$/i.test(trimmed)) {
        return true
      }
      
      return false
    },
    skipQuestion() {
      // 건너뛴 문제도 결과에 저장 (오답 처리)
      const correctAnswer = this.getQuestionAnswer(this.currentQuestion)
      this.questionResults.push({
        questionIndex: this.currentQuestionIndex + 1,
        questionTitle: this.getQuestionTitle(this.currentQuestion),
        userAnswer: '',
        correctAnswer: correctAnswer,
        isCorrect: false
      })
      
      this.nextQuestion()
    },
    nextQuestion() {
      this.userAnswer = ''
      
      if (this.currentQuestionIndex < this.questions.length - 1) {
        this.currentQuestionIndex++
        this.currentQuestion = this.questions[this.currentQuestionIndex]
        this.$nextTick(() => {
          this.$refs.answerInput?.focus()
        })
      } else {
        this.endPractice()
      }
    },
    async endPractice() {
      this.stopTimer()
      this.resultMessage = this.$t('randomPractice.result.correct', { correct: this.correctCount, total: this.totalQuestions })
      
      // 랜덤 연습 결과를 백엔드에 저장
      try {
        await axios.post('/api/save-random-practice-result/', {
          study_id: this.selectedStudy.id,
          correct_count: this.correctCount,
          total_questions: this.totalQuestions,
          elapsed_seconds: this.elapsedSeconds
        })
        debugLog(this.$t('randomPractice.messages.resultSaved'))
      } catch (error) {
        debugLog(this.$t('randomPractice.messages.resultSaveFailed'), error, 'error')
        // 저장 실패해도 결과는 표시
      }
      
      this.resultModal.show()
    },
    closeResultModal() {
      this.resultModal.hide()
      this.resetPractice()
    },
    restartPractice() {
      this.resultModal.hide()
      this.resetPractice()
      this.startPractice()
    },
    resetPractice() {
      this.questions = []
      this.currentQuestionIndex = 0
      this.currentQuestion = null
      this.userAnswer = ''
      this.showAnswer = false
      this.elapsedSeconds = 0
      this.correctCount = 0
      this.totalQuestions = 0
      this.questionResults = []
    },
    getDifficultyClass(difficulty) {
      if (!difficulty) return ''
      const lowerDifficulty = difficulty.toLowerCase()
      if (lowerDifficulty === 'easy' || lowerDifficulty === '쉬움') return 'easy'
      if (lowerDifficulty === 'medium' || lowerDifficulty === '보통') return 'medium'
      if (lowerDifficulty === 'hard' || lowerDifficulty === '어려움') return 'hard'
      return ''
    },
    
    // 다국어 제목 처리 메서드들
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
    
    getQuestionTitle(question) {
      if (!question) return '';
      
      // 사용자 프로필 언어 우선, 없으면 i18n locale, 기본값은 'en'
      const userLang = this.userProfileLanguage || this.$i18n?.locale || 'en'
      
      // 모든 지원 언어 필드를 확인하여 사용자 언어에 맞는 값 반환
      const supportedLanguages = SUPPORTED_LANGUAGES
      
      // 사용자 언어 우선
      if (question[`title_${userLang}`]) {
        return question[`title_${userLang}`]
      }
      
      // 영어 폴백 (기본 언어)
      if (question.title_en) {
        return question.title_en
      }
      
      // 다른 지원 언어 확인
      for (const lang of supportedLanguages) {
        if (question[`title_${lang}`]) {
          return question[`title_${lang}`]
        }
      }
      
      // 기본 title 필드 폴백
      if (question.title) {
        return question.title
      }
      
      // 최종 폴백
      return userLang === 'ko' ? '제목 없음' : 'No Title'
    },
    
    getQuestionContent(question) {
      if (!question) return '';
      
      // getLocalizedContentWithI18n 사용
      const userLang = this.userProfileLanguage || this.$i18n?.locale || 'en'
      const fallbackValue = userLang === 'ko' ? '내용 없음' : 'No Content'
      return getLocalizedContentWithI18n(question, 'content', this.$i18n, this.userProfileLanguage, fallbackValue)
    },
    
    getQuestionAnswer(question) {
      if (!question) return '';
      
      // getLocalizedContentWithI18n 사용
      const userLang = this.userProfileLanguage || this.$i18n?.locale || 'en'
      const fallbackValue = userLang === 'ko' ? '답안 없음' : 'No Answer'
      return getLocalizedContentWithI18n(question, 'answer', this.$i18n, this.userProfileLanguage, fallbackValue)
    }
  }
}
</script>

<style scoped>
.random-practice-modern {
  padding-top: 10px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

.random-practice-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.section-header {
  text-align: center;
  margin-bottom: 30px;
}

/* Page Title */
.page-title {
  padding: 20px 30px 20px;
  background: white;
  margin: 0;
  font-size: 2.5rem;
  font-weight: 700;
  color: #2c3e50;
  text-align: center;
}

.study-selection-section,
.practice-settings-section,
.question-practice-section {
  background-color: rgba(255, 255, 255, 0.95);
  border-radius: 15px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
  margin-bottom: 20px;
  overflow: hidden;
  backdrop-filter: blur(10px);
}

.study-selection-card,
.practice-settings-card,
.question-practice-card {
  padding: 15px 20px;
}

.card-header {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  padding: 15px 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.card-title {
  font-size: 1.8rem;
  color: #4a4a4a;
  margin-bottom: 10px;
}

.section-title {
  font-size: 1.5rem;
  color: #333;
  margin-bottom: 15px;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #555;
  font-size: 0.95rem;
}

.info-icon {
  color: #007bff;
  font-size: 1.1rem;
}

.info-content strong {
  color: #333;
}

.settings-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-label {
  font-size: 1rem;
  color: #555;
  margin-bottom: 5px;
  display: block;
}

.modern-input {
  width: 100%;
  padding: 10px 15px;
  border: 1px solid #ccc;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.3s ease;
}

.modern-input:focus {
  border-color: #007bff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
  outline: none;
}

.form-help {
  font-size: 0.8rem;
  color: #666;
  margin-top: 5px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.start-practice-btn,
.back-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.start-practice-btn {
  background-color: #28a745;
  color: white;
}

.start-practice-btn:hover {
  background-color: #218838;
}

.back-btn {
  background-color: #6c757d;
  color: white;
}

.back-btn:hover {
  background-color: #5a6268;
}

.studies-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.study-card {
  background-color: #fdfdfd;
  border: 1px solid #eee;
  border-radius: 10px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  box-sizing: border-box;
  max-width: 100%;
  min-width: 0;
}

.study-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
}

.study-header {
  margin-bottom: 10px;
}

.study-title {
  font-size: 1.3rem;
  color: #333;
  margin-bottom: 5px;
}

.study-goal {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 10px;
}

.study-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
  font-size: 0.9rem;
  color: #555;
}

.study-progress {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  font-size: 0.9rem;
  color: #555;
}

.study-progress-section {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #eee;
}

.progress-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-icon {
  color: #007bff;
  font-size: 1rem;
}

.study-actions {
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
}

.select-study-btn {
  width: 100%;
  padding: 10px 15px;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
  background-color: #007bff;
  color: white;
  transition: background-color 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.select-study-btn:hover {
  background-color: #0056b3;
}

.select-study-btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
  color: #888;
}

.empty-state {
  text-align: center;
  padding: 50px 20px;
  color: #888;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 15px;
  color: #e0e0e0;
}

.question-practice-section {
  padding-top: 0; /* Remove top padding for the last section */
}

.question-practice-card {
  padding: 25px;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.question-info {
  flex-grow: 1;
}

.question-title {
  font-size: 1.8rem;
  color: #333;
  margin-bottom: 5px;
}

.question-subtitle {
  font-size: 1.1rem;
  color: #555;
  margin-bottom: 10px;
}

.question-controls {
  display: flex;
  align-items: center;
  gap: 15px;
}

.timer {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #666;
  font-size: 1rem;
}

.timer-icon {
  color: #007bff;
  font-size: 1.1rem;
}

.toggle-answer-btn {
  padding: 8px 12px;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: bold;
  cursor: pointer;
  background-color: #e0e0e0;
  color: #333;
  transition: background-color 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.toggle-answer-btn:hover {
  background-color: #d0d0d0;
}

.end-practice-btn {
  padding: 8px 12px;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: bold;
  cursor: pointer;
  background-color: #dc3545;
  color: white;
  transition: background-color 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.end-practice-btn:hover {
  background-color: #c82333;
}

.question-content {
  margin-top: 20px;
}

.question-details {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #555;
  font-size: 0.95rem;
}

.detail-icon {
  color: #007bff;
  font-size: 1.1rem;
}

.detail-content strong {
  color: #333;
  margin-right: 8px;
}

.content-box {
  background-color: #f9f9f9;
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 15px;
  font-size: 0.95rem;
  color: #444;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.difficulty-badge {
  display: inline-block;
  padding: 5px 10px;
  border-radius: 15px;
  font-size: 0.8rem;
  font-weight: bold;
  color: white;
}

.difficulty-badge.easy {
  background-color: #28a745; /* Green */
}

.difficulty-badge.medium {
  background-color: #ffc107; /* Yellow */
}

.difficulty-badge.hard {
  background-color: #dc3545; /* Red */
}

.url-link {
  color: #007bff;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 5px;
}

.url-link:hover {
  text-decoration: underline;
}

.answer-section {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #eee;
}

.answer-input-group {
  margin-bottom: 15px;
}

.answer-label {
  font-size: 1rem;
  color: #555;
  margin-bottom: 5px;
  display: block;
}

.answer-input {
  width: 100%;
  padding: 10px 15px;
  border: 1px solid #ccc;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.3s ease;
}

.answer-input:focus {
  border-color: #007bff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
  outline: none;
}

.answer-actions {
  display: flex;
  justify-content: space-between;
}

.submit-answer-btn,
.skip-question-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.submit-answer-btn {
  background-color: #007bff;
  color: white;
}

.submit-answer-btn:hover {
  background-color: #0056b3;
}

.skip-question-btn {
  background-color: #6c757d;
  color: white;
}

.skip-question-btn:hover {
  background-color: #5a6268;
}

/* Result Modal 스타일 */
#resultModal .modal-dialog {
  max-width: 80%;
  width: 80%;
  margin: 1.75rem auto;
}

@media (max-width: 768px) {
  #resultModal .modal-dialog {
    max-width: 95%;
    width: 95%;
    margin: 0.5rem auto;
    display: flex;
    align-items: center;
    min-height: calc(100% - 1rem);
  }
  
  #resultModal .modal-content {
    margin: auto;
  }
}

.modal-body {
  text-align: center;
  max-height: 80vh;
  overflow-y: auto;
}

.result-content {
  margin-top: 20px;
}

.result-icon {
  font-size: 5rem;
  color: #ffd700; /* Gold color for trophy */
  margin-bottom: 15px;
}

.result-message {
  font-size: 2rem;
  color: #333;
  margin-bottom: 10px;
}

.result-stats {
  display: flex;
  justify-content: center;
  gap: 20px;
  font-size: 1.1rem;
  color: #555;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.stat-icon {
  font-size: 1.2rem;
}

.stat-icon.correct {
  color: #28a745; /* Green for correct */
}

.stat-icon.percentage {
  color: #007bff; /* Blue for accuracy */
}

.stat-icon.clock {
  color: #6c757d; /* Gray for elapsed time */
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.close-result-btn,
.restart-practice-btn {
  padding: 10px 25px;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.close-result-btn {
  background-color: #6c757d;
  color: white;
}

.close-result-btn:hover {
  background-color: #5a6268;
}

.restart-practice-btn {
  background-color: #28a745;
  color: white;
}

.restart-practice-btn:hover {
  background-color: #218838;
}

.modal-footer button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
  color: #888;
}

.loading-container {
  text-align: center;
  padding: 50px 20px;
}

.loading-spinner {
  font-size: 3rem;
  color: #007bff;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

 .empty-state p {
   color: #888;
   font-size: 1.1rem;
 }

 /* Responsive Design */
 @media (max-width: 768px) {
   .random-practice-container {
     padding: 0 15px;
   }

   .page-title {
     font-size: 2rem;
   }

   .card-title {
     font-size: 1.5rem;
   }

   .study-selection-section,
   .practice-settings-section {
     padding: 10px;
   }

   .settings-grid {
     grid-template-columns: 1fr;
     gap: 15px;
   }

   .studies-grid {
     grid-template-columns: 1fr;
     min-width: 0;
     overflow: hidden;
   }
   
   .study-card {
     min-width: 0;
     max-width: 100%;
   }
   
   /* 원형 버튼 스타일 */
   .start-practice-btn,
   .back-btn {
     padding: 0 !important;
     width: 40px !important;
     height: 40px !important;
     border-radius: 50% !important;
     display: flex !important;
     align-items: center !important;
     justify-content: center !important;
     font-size: 0 !important;
     gap: 0 !important;
     min-width: auto !important;
   }
   
   .start-practice-btn i,
   .back-btn i {
     font-size: 14px !important;
     line-height: 1 !important;
   }
   
   .start-practice-btn span,
   .back-btn span {
     display: none !important;
   }

   .question-header {
     flex-direction: column;
     align-items: flex-start;
     gap: 15px;
   }

   .question-controls {
     width: 100%;
     justify-content: space-between;
     flex-direction: row;
     align-items: center;
   }
   
   .question-controls .timer {
     flex: 0 0 auto;
   }
   
   /* 답안 보기와 연습 종료 버튼을 우측에 그룹화 */
   .question-controls .toggle-answer-btn,
   .question-controls .end-practice-btn {
     margin-left: 0;
   }
   
   /* 버튼들 사이 간격 최소화 */
   .question-controls .toggle-answer-btn {
     margin-right: 4px;
   }
   
   /* 버튼들을 그룹으로 묶어서 우측 정렬 */
   .question-controls {
     gap: 0;
   }
   
   .question-controls .timer {
     margin-right: auto;
   }

   .answer-actions {
     flex-direction: row;
     justify-content: flex-end;
     gap: 4px;
   }
   
   /* 모바일에서 답안 제출/건너뛰기 버튼 원형으로 */
   .submit-answer-btn,
   .skip-question-btn {
     padding: 0 !important;
     width: 50px !important;
     height: 50px !important;
     border-radius: 50% !important;
     display: flex !important;
     align-items: center !important;
     justify-content: center !important;
     font-size: 0 !important;
     gap: 0 !important;
     min-width: auto !important;
   }
   
   .submit-answer-btn i,
   .skip-question-btn i {
     font-size: 18px !important;
     line-height: 1 !important;
   }
   
   .submit-answer-btn > *:not(i),
   .skip-question-btn > *:not(i) {
     display: none !important;
   }
   
   /* 모바일에서 스터디 선택 버튼 원형으로 */
   .select-study-btn,
   .select-study-btn:disabled {
     padding: 0 !important;
     width: 50px !important;
     height: 50px !important;
     border-radius: 50% !important;
     display: flex !important;
     align-items: center !important;
     justify-content: center !important;
     font-size: 0 !important;
     gap: 0 !important;
     min-width: auto !important;
   }
   
   .select-study-btn i,
   .select-study-btn:disabled i {
     font-size: 18px !important;
     line-height: 1 !important;
   }
   
   .select-study-btn > *:not(i),
   .select-study-btn:disabled > *:not(i) {
     display: none !important;
   }

   .result-stats {
     flex-direction: column;
     gap: 10px;
   }

   .modal-footer {
     flex-direction: row;
     justify-content: center;
     gap: 10px;
   }
   
   /* 모바일에서 결과 모달 버튼 원형으로 */
   .close-result-btn,
   .restart-practice-btn {
     padding: 0 !important;
     width: 50px !important;
     height: 50px !important;
     border-radius: 50% !important;
     display: flex !important;
     align-items: center !important;
     justify-content: center !important;
     font-size: 0 !important;
     gap: 0 !important;
     min-width: auto !important;
   }
   
   .close-result-btn i,
   .restart-practice-btn i {
     font-size: 18px !important;
     line-height: 1 !important;
   }
   
   .close-result-btn,
   .restart-practice-btn {
     font-size: 0 !important;
     line-height: 0 !important;
   }
   
   .close-result-btn::after,
   .restart-practice-btn::after {
     content: '';
   }
   
   /* 버튼 내 텍스트 노드 숨기기 */
   .close-result-btn > i,
   .restart-practice-btn > i {
     font-size: 18px !important;
     line-height: 1 !important;
     display: inline-block !important;
   }
 }

 @media (max-width: 576px) {
   .random-practice-container {
     padding: 0 10px;
   }

   .page-title {
     font-size: 1.8rem;
   }

   .card-title {
     font-size: 1.3rem;
   }

   .study-selection-card,
   .practice-settings-card,
   .question-practice-card {
     padding: 15px;
   }
   
   .start-practice-btn,
   .back-btn {
     width: 36px !important;
     height: 36px !important;
   }
   
   .start-practice-btn i,
   .back-btn i {
     font-size: 12px !important;
   }

   .question-title {
     font-size: 1.5rem;
   }

   .question-subtitle {
     font-size: 1rem;
   }

   .question-controls {
     flex-direction: row;
     justify-content: space-between;
     align-items: center;
     gap: 0;
   }
   
   .question-controls .timer {
     flex: 0 0 auto;
     margin-right: auto;
   }
   
   /* 답안 보기와 연습 종료 버튼을 우측에 그룹화 */
   .question-controls .toggle-answer-btn,
   .question-controls .end-practice-btn {
     margin-left: 0;
   }
   
   /* 버튼들 사이 간격 최소화 */
   .question-controls .toggle-answer-btn {
     margin-right: 3px;
   }

   .timer {
     justify-content: center;
   }

   /* 모바일에서 답안 보기/연습 종료 버튼 원형으로 */
   .toggle-answer-btn,
   .end-practice-btn {
     padding: 0 !important;
     width: 45px !important;
     height: 45px !important;
     border-radius: 50% !important;
     display: flex !important;
     align-items: center !important;
     justify-content: center !important;
     font-size: 0 !important;
     gap: 0 !important;
     min-width: auto !important;
   }
   
   .toggle-answer-btn i,
   .end-practice-btn i {
     font-size: 16px !important;
     line-height: 1 !important;
   }
   
   .toggle-answer-btn > *:not(i),
   .end-practice-btn > *:not(i) {
     display: none !important;
   }
   
   /* 모바일에서 답안 제출/건너뛰기 버튼 원형으로 (작은 화면) */
   .submit-answer-btn,
   .skip-question-btn {
     width: 45px !important;
     height: 45px !important;
   }
   
   .submit-answer-btn i,
   .skip-question-btn i {
     font-size: 16px !important;
   }
   
   /* 모바일에서 스터디 선택 버튼 원형으로 (작은 화면) */
   .select-study-btn,
   .select-study-btn:disabled {
     width: 45px !important;
     height: 45px !important;
   }
   
   .select-study-btn i,
   .select-study-btn:disabled i {
     font-size: 16px !important;
   }
   
   /* 모바일에서 결과 모달 버튼 원형으로 (작은 화면) */
   .close-result-btn,
   .restart-practice-btn {
     width: 45px !important;
     height: 45px !important;
   }
   
   .close-result-btn i,
   .restart-practice-btn i {
     font-size: 16px !important;
   }
 }

.answer-box {
  background-color: #fff3cd; /* Light yellow for answer */
  border: 1px solid #ffeeba;
  border-radius: 8px;
  padding: 15px;
  font-size: 0.95rem;
  color: #856404;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* 문제별 결과 테이블 스타일 */
.question-results-table {
  margin-top: 30px;
  padding-top: 30px;
  border-top: 2px solid #eee;
}

.table-title {
  font-size: 1.3rem;
  color: #333;
  margin-bottom: 15px;
  font-weight: 600;
}

.table-container {
  overflow-x: auto;
  max-height: 400px;
  overflow-y: auto;
}

.results-table {
  width: 100%;
  border-collapse: collapse;
  background-color: white;
  font-size: 0.9rem;
}

.results-table thead {
  background-color: #f8f9fa;
  position: sticky;
  top: 0;
  z-index: 10;
}

.results-table th {
  padding: 12px 12px;
  text-align: left;
  font-weight: 600;
  color: #333;
  border-bottom: 2px solid #dee2e6;
  white-space: nowrap;
  min-width: 80px;
}

.results-table th:nth-child(1) {
  width: 60px;
  text-align: center;
}

.results-table th:nth-child(2) {
  width: 250px;
  min-width: 200px;
}

.results-table th:nth-child(3) {
  width: 200px;
  min-width: 150px;
}

.results-table th:nth-child(4) {
  width: 300px;
  min-width: 200px;
}

.results-table th:nth-child(5) {
  width: 100px;
  text-align: center;
}

.results-table td {
  padding: 12px 12px;
  border-bottom: 1px solid #dee2e6;
  vertical-align: top;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.results-table td:nth-child(1) {
  text-align: center;
  font-weight: 600;
}

.results-table td:nth-child(5) {
  text-align: center;
}

.results-table tbody tr:hover {
  background-color: #f8f9fa;
}

.results-table tbody tr.correct-row {
  background-color: #d4edda;
}

.results-table tbody tr.correct-row:hover {
  background-color: #c3e6cb;
}

.results-table tbody tr.wrong-row {
  background-color: #f8d7da;
}

.results-table tbody tr.wrong-row:hover {
  background-color: #f5c6cb;
}

.question-title-cell {
  max-width: 250px;
  word-wrap: break-word;
  overflow-wrap: break-word;
  line-height: 1.4;
}

.result-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
}

.result-badge.correct-badge {
  background-color: #28a745;
  color: white;
}

.result-badge.wrong-badge {
  background-color: #dc3545;
  color: white;
}

/* 모바일 반응형 */
@media (max-width: 768px) {
  .question-results-table {
    margin-top: 20px;
    padding-top: 20px;
  }
  
  .table-title {
    font-size: 1.1rem;
  }
  
  .results-table {
    font-size: 0.8rem;
  }
  
  .results-table th,
  .results-table td {
    padding: 8px 4px;
  }
  
  .question-title-cell {
    max-width: 120px;
  }
}
</style> 