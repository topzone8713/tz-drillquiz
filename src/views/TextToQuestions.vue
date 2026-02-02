<template>
  <div class="text-to-questions-modern">
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
    
    <!-- 번역 로딩 중일 때 로딩 표시 -->
    <div v-if="!translationsLoaded" class="loading-container">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <p class="mt-3">Loading translation data...</p>
    </div>
    
    <!-- 번역이 로드된 후에만 컨텐츠 표시 -->
    <div v-else class="files-container">
      <!-- Top Header -->
      <div class="top-header">
        <div class="header-actions">
          <router-link to="/question-files" class="action-btn action-btn-primary">
            <i class="fas fa-file-alt"></i>
            <span class="action-label">{{ translations.backToFiles }}</span>
          </router-link>
          <router-link to="/exam-management" class="action-btn action-btn-success">
            <i class="fas fa-clipboard-list"></i>
            <span class="action-label">{{ translations.examManagement }}</span>
          </router-link>
        </div>
      </div>

      <!-- Page Title -->
      <div class="page-title">
        <h1>{{ translations.pageTitle }}</h1>
      </div>

      <!-- File Upload Section -->
      <div class="upload-section">
        <div class="upload-card">
          <div class="card-header-modern">
            <h3>{{ translations.uploadTitle }}</h3>
          </div>
          
          <div class="upload-content">
            <!-- Input Mode Selection -->
            <div class="input-mode-selector">
              <div class="btn-group" role="group">
                <button 
                  type="button" 
                  class="btn" 
                  :class="inputMode === 'file' ? 'btn-primary' : 'btn-outline-primary'"
                  @click="inputMode = 'file'"
                  :disabled="isProcessing"
                >
                  <i class="fas fa-file"></i>
                  {{ translations.fileMode }}
                </button>
                <button 
                  type="button" 
                  class="btn" 
                  :class="inputMode === 'url' ? 'btn-primary' : 'btn-outline-primary'"
                  @click="inputMode = 'url'"
                  :disabled="isProcessing"
                >
                  <i class="fas fa-link"></i>
                  {{ translations.urlMode }}
                </button>
              </div>
            </div>
            
            <div class="upload-form">
              <!-- File Input Mode -->
              <div v-if="inputMode === 'file'" class="upload-input-group">
                <div class="upload-input">
                  <label class="form-label">{{ translations.fileLabel || 'File' }}</label>
                  <input 
                    type="file" 
                    class="form-control" 
                    @change="handleFileSelect" 
                    accept=".txt"
                    ref="fileInput"
                    :disabled="isProcessing"
                  >
                  <small class="form-text text-muted mt-2">
                    {{ translations.fileFormatNote }}
                  </small>
                </div>
                <div class="upload-input">
                  <label class="form-label">{{ translations.titleLabel }}</label>
                  <input 
                    type="text" 
                    class="form-control" 
                    :class="{ 'is-invalid': titleValidationError }"
                    v-model="inputTitle"
                    @input="handleTitleInput"
                    :placeholder="translations.titlePlaceholder"
                    :disabled="isProcessing"
                  >
                  <div v-if="titleValidationError" class="invalid-feedback d-block">
                    {{ titleValidationError }}
                  </div>
                  <small v-else class="form-text text-muted mt-2">
                    {{ translations.titleNote }}
                  </small>
                </div>
              </div>
              
              <!-- URL Input Mode -->
              <div v-else class="upload-input-group">
                <div class="upload-input">
                  <label class="form-label">{{ translations.urlLabel }}</label>
                  <input 
                    type="url" 
                    class="form-control" 
                    v-model="inputUrl"
                    @input="handleUrlInput"
                    :placeholder="translations.urlPlaceholder"
                    :disabled="isProcessing"
                    ref="urlInput"
                  >
                  <small class="form-text text-muted mt-2">
                    {{ translations.urlFormatNote }}
                  </small>
                </div>
                <div class="upload-input">
                  <label class="form-label">{{ translations.titleLabel }}</label>
                  <input 
                    type="text" 
                    class="form-control" 
                    :class="{ 'is-invalid': titleValidationError }"
                    v-model="inputTitle"
                    @input="handleTitleInput"
                    :placeholder="translations.titlePlaceholder"
                    :disabled="isProcessing"
                  >
                  <div v-if="titleValidationError" class="invalid-feedback d-block">
                    {{ titleValidationError }}
                  </div>
                  <small v-else class="form-text text-muted mt-2">
                    {{ translations.titleNote }}
                  </small>
                </div>
              </div>
              
              <!-- Question Count Input (공통) -->
              <div class="upload-input upload-input-number">
                <label class="form-label">{{ translations.questionCountLabel }}</label>
                <div class="input-wrapper">
                  <input 
                    type="number" 
                    class="form-control" 
                    v-model.number="questionCount"
                    :min="1"
                    :max="50"
                    :disabled="isProcessing"
                  >
                  <small class="form-text text-muted mt-2">
                    {{ translations.questionCountNote }}
                  </small>
                </div>
              </div>
              
              <!-- Exam Difficulty Input (공통) -->
              <div class="upload-input upload-input-difficulty">
                <label class="form-label">{{ $t('examDetail.examDifficultyLabel') || '시험 난이도' }}</label>
                <input 
                  type="range" 
                  class="form-control" 
                  v-model.number="examDifficulty"
                  :min="1"
                  :max="10"
                  :disabled="isProcessing"
                  style="width: 100%;"
                >
              </div>
              
              <!-- Public 설정 및 AI 모의 인터뷰 -->
              <div class="upload-options">
                <div class="form-check">
                  <input 
                    class="form-check-input" 
                    type="checkbox" 
                    id="isPublic" 
                    v-model="isPublic"
                    :disabled="isProcessing"
                  >
                  <label class="form-check-label" for="isPublic">
                    {{ translations.publicFile }}
                  </label>
                </div>
                <div class="form-check">
                  <input 
                    class="form-check-input" 
                    type="checkbox" 
                    id="aiMockInterview" 
                    v-model="aiMockInterview"
                    :disabled="isProcessing"
                  >
                  <label class="form-check-label" for="aiMockInterview">
                    {{ translations.aiMockInterview }}
                  </label>
                </div>
              </div>
              
              <!-- Tags Section -->
              <div class="upload-input" style="flex: 1; min-width: 100%;">
                <label class="form-label">{{ $t('studyDetail.tagManagement') || '태그 관리' }}</label>
                <div class="d-flex align-items-center justify-content-end gap-2 flex-wrap">
                  <!-- Selected Tags Display -->
                  <div v-if="newExamTags.length > 0" class="d-flex align-items-center flex-wrap gap-2">
                    <span 
                      v-for="tagId in newExamTags" 
                      :key="tagId"
                      class="badge bg-primary"
                    >
                      {{ getSelectedTagName(tagId) }}
                      <button 
                        @click="removeExamTag(tagId)" 
                        class="btn-close btn-close-white ms-1" 
                        style="font-size: 0.7em;"
                      ></button>
                    </span>
                  </div>
                  <button 
                    @click="openTagModal" 
                    type="button"
                    class="btn btn-outline-primary btn-sm tag-search-btn"
                    :disabled="isProcessing"
                  >
                    <i class="fas fa-tags"></i>
                    <span class="tag-search-text">{{ $t('tagFilterModal.title') || '태그로 검색' }}</span>
                    <span v-if="newExamTags.length > 0" class="badge bg-primary ms-2">{{ newExamTags.length }}</span>
                  </button>
                </div>
              </div>
              
              <div class="upload-actions">
                <button 
                  @click="processTextFile" 
                  class="action-btn action-btn-success"
                  :disabled="!canProcess || isProcessing"
                >
                  <i v-if="isProcessing" class="fas fa-spinner fa-spin"></i>
                  <i v-else class="fas fa-magic"></i>
                  <span class="action-label">{{ isProcessing ? translations.processing : translations.generateQuestions }}</span>
                </button>
                <button 
                  @click="resetForm" 
                  class="action-btn action-btn-secondary"
                  :disabled="isProcessing"
                >
                  <i class="fas fa-times"></i>
                  <span class="action-label">{{ translations.reset }}</span>
                </button>
              </div>
            </div>
            
            <div v-if="uploadMessage" class="upload-message" :class="uploadMessageType">
              {{ uploadMessage }}
            </div>
            
            <!-- Processing Status -->
            <div v-if="isProcessing" class="processing-status">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Processing...</span>
              </div>
              <p class="mt-3">{{ translations.processingMessage }}</p>
              <div class="progress-info" v-if="processingStep">
                <small>{{ processingStep }}</small>
              </div>
            </div>
            
            <!-- Info Section -->
            <div class="info-section">
              <div class="info-alert">
                <i class="fas fa-info-circle"></i>
                <strong>{{ translations.howItWorks }}</strong>
              </div>
              <ol class="info-steps">
                <li>{{ translations.step1 }}</li>
                <li>{{ translations.step2 }}</li>
                <li>{{ translations.step3 }}</li>
                <li>{{ translations.step4 }}</li>
              </ol>
              
              <div class="info-alert mt-3">
                <i class="fas fa-lightbulb"></i>
                <strong>{{ translations.tipsTitle }}</strong>
              </div>
              <ul class="info-tips">
                <li>{{ translations.tip1 }}</li>
                <li>{{ translations.tip2 }}</li>
                <li>{{ translations.tip3 }}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Tag Filter Modal -->
    <TagFilterModal
      :show="showTagModal"
      :selectedTags="newExamTags"
      @update:show="showTagModal = $event"
      @update:selectedTags="handleTagUpdate"
      @apply="handleTagApply"
      @error="handleTagError"
      @tag-created="handleTagCreated"
    />
  </div>
</template>

<script>
import { apiWithLongTimeout } from '@/services/api'
import { debugLog } from '@/utils/debugUtils'
import TagFilterModal from '@/components/TagFilterModal.vue'
import axios from 'axios'
import authService from '@/services/authService'
import { getDefaultDifficultyByAgeRating, checkTitleDuplicate, generateUniqueTitle } from '@/utils/examUtils'
import { getLocalizedContent } from '@/utils/multilingualUtils'

export default {
  name: 'TextToQuestions',
  components: {
    TagFilterModal
  },
  data() {
    return {
      selectedFile: null,
      inputUrl: '',
      inputTitle: '',
      questionCount: 10,
      inputMode: 'file', // 'file' or 'url'
      uploadMessage: '',
      uploadMessageType: 'alert-info',
      isProcessing: false,
      processingStep: '',
      isPublic: false,
      aiMockInterview: true,
      examDifficulty: 5, // 시험 난이도 (1~10)
      translationsLoaded: false,
      // Toast Notifications
      showToast: false,
      toastMessage: '',
      toastType: 'alert-info',
      toastIcon: 'fas fa-info-circle',
      translations: {},
      // Tag Selection
      newExamTags: [],
      showTagModal: false,
      availableTags: [],
      // Title Validation
      titleValidationError: '',
      titleValidationTimer: null
    }
  },
  computed: {
    isAuthenticated() {
      return authService.isAuthenticatedSync()
    },
    canProcess() {
      // 태그는 반드시 1개 이상 선택되어야 함
      if (!this.newExamTags || this.newExamTags.length === 0) {
        return false
      }
      
      // 시험 제목 중복 오류가 있으면 처리 불가
      if (this.titleValidationError) {
        return false
      }
      
      if (this.inputMode === 'file') {
        return this.selectedFile !== null
      } else {
        return this.inputUrl.trim().length > 0 && this.isValidUrl(this.inputUrl)
      }
    }
  },
  async mounted() {
    await this.loadTranslations()
    await this.loadTags()
    await this.loadDefaultDifficulty()
  },
  methods: {
    async loadTranslations() {
      try {
        // 기본 번역 설정
        const isLoaded = this.$i18n.locale !== undefined
        
        this.translations = {
          pageTitle: isLoaded ? (this.$t('textToQuestions.title') || '텍스트에서 문제 생성') : '텍스트에서 문제 생성',
          pageDescription: isLoaded ? (this.$t('textToQuestions.description') || '텍스트 파일을 업로드하면 AI가 자동으로 퀴즈 문제를 생성합니다.') : '텍스트 파일을 업로드하면 AI가 자동으로 퀴즈 문제를 생성합니다.',
          backToFiles: isLoaded ? (this.$t('textToQuestions.backToFiles') || '문제 파일 목록') : '문제 파일 목록',
          examManagement: isLoaded ? (this.$t('questionFiles.examManagement') || '시험 관리') : '시험 관리',
          uploadTitle: isLoaded ? (this.$t('textToQuestions.uploadTitle') || '텍스트 파일 업로드') : '텍스트 파일 업로드',
          fileLabel: isLoaded ? (this.$t('textToQuestions.fileLabel') || '파일') : '파일',
          fileFormatNote: isLoaded ? (this.$t('textToQuestions.fileFormatNote') || '텍스트 파일(.txt)만 업로드 가능합니다.') : '텍스트 파일(.txt)만 업로드 가능합니다.',
          fileMode: isLoaded ? (this.$t('textToQuestions.fileMode') || '파일 업로드') : '파일 업로드',
          urlMode: isLoaded ? (this.$t('textToQuestions.urlMode') || 'URL 입력') : 'URL 입력',
          urlLabel: isLoaded ? (this.$t('textToQuestions.urlLabel') || 'URL') : 'URL',
          urlPlaceholder: isLoaded ? (this.$t('textToQuestions.urlPlaceholder') || 'https://example.com/article') : 'https://example.com/article',
          urlFormatNote: isLoaded ? (this.$t('textToQuestions.urlFormatNote') || '웹페이지 URL을 입력하면 해당 페이지의 컨텐츠를 자동으로 파싱합니다.') : '웹페이지 URL을 입력하면 해당 페이지의 컨텐츠를 자동으로 파싱합니다.',
          titleLabel: isLoaded ? (this.$t('textToQuestions.titleLabel') || '제목') : '제목',
          titlePlaceholder: isLoaded ? (this.$t('textToQuestions.titlePlaceholder') || '시험 제목을 입력하세요 (선택사항)') : '시험 제목을 입력하세요 (선택사항)',
          titleNote: isLoaded ? (this.$t('textToQuestions.titleNote') || '입력하지 않으면 파일명 또는 URL 도메인명이 사용됩니다.') : '입력하지 않으면 파일명 또는 URL 도메인명이 사용됩니다.',
          duplicateTitleError: (() => {
            // examManagement.messages.duplicateTitle 사용 (다국어 지원)
            if (!isLoaded) {
              return '동일한 이름의 시험이 이미 존재합니다.'
            }
            try {
              const translated = this.$t('examManagement.messages.duplicateTitle')
              // 번역 키가 그대로 반환되면 번역이 없는 것이므로 현재 언어에 맞는 fallback 사용
              if (translated === 'examManagement.messages.duplicateTitle' || !translated) {
                const currentLang = this.$i18n.locale || 'en'
                const fallbackMessages = {
                  'ko': '이미 같은 이름의 시험이 존재합니다',
                  'en': 'An exam with this title already exists',
                  'es': 'Ya existe un examen con este título',
                  'zh': '已存在相同标题的考试',
                  'ja': 'このタイトルの試験が既に存在します'
                }
                return fallbackMessages[currentLang] || fallbackMessages['en']
              }
              return translated
            } catch (e) {
              return '동일한 이름의 시험이 이미 존재합니다.'
            }
          })(),
          questionCountLabel: isLoaded ? (this.$t('textToQuestions.questionCountLabel') || '생성할 문제 개수') : '생성할 문제 개수',
          questionCountNote: isLoaded ? (this.$t('textToQuestions.questionCountNote') || '1~50 사이의 숫자를 입력하세요. 기본값: 10') : '1~50 사이의 숫자를 입력하세요. 기본값: 10',
          publicFile: isLoaded ? (this.$t('textToQuestions.publicFile') || '공개') : '공개',
          aiMockInterview: isLoaded ? (this.$t('examManagement.createForm.aiMockInterview') || 'AI 모의 인터뷰') : 'AI 모의 인터뷰',
          generateQuestions: isLoaded ? (this.$t('textToQuestions.generateQuestions') || 'Generate') : 'Generate',
          processing: isLoaded ? (this.$t('textToQuestions.processing') || '처리 중...') : '처리 중...',
          reset: isLoaded ? (this.$t('textToQuestions.reset') || '초기화') : '초기화',
          processingMessage: isLoaded ? (this.$t('textToQuestions.processingMessage') || 'AI가 텍스트를 분석하여 문제를 생성하고 있습니다. 잠시만 기다려주세요...') : 'AI가 텍스트를 분석하여 문제를 생성하고 있습니다. 잠시만 기다려주세요...',
          howItWorks: isLoaded ? (this.$t('textToQuestions.howItWorks') || '작동 방식') : '작동 방식',
          step1: isLoaded ? (this.$t('textToQuestions.step1') || '텍스트 파일을 선택합니다.') : '텍스트 파일을 선택합니다.',
          step2: isLoaded ? (this.$t('textToQuestions.step2') || 'AI가 텍스트 내용을 분석합니다.') : 'AI가 텍스트 내용을 분석합니다.',
          step3: isLoaded ? (this.$t('textToQuestions.step3') || '텍스트에서 주요 개념과 내용을 추출하여 문제를 생성합니다.') : '텍스트에서 주요 개념과 내용을 추출하여 문제를 생성합니다.',
          step4: isLoaded ? (this.$t('textToQuestions.step4') || '생성된 문제를 엑셀 파일 형식으로 저장합니다.') : '생성된 문제를 엑셀 파일 형식으로 저장합니다.',
          tipsTitle: isLoaded ? (this.$t('textToQuestions.tipsTitle') || '팁') : '팁',
          tip1: isLoaded ? (this.$t('textToQuestions.tip1') || '명확하고 구조화된 텍스트일수록 더 좋은 문제가 생성됩니다.') : '명확하고 구조화된 텍스트일수록 더 좋은 문제가 생성됩니다.',
          tip2: isLoaded ? (this.$t('textToQuestions.tip2') || '텍스트가 너무 길면 처음 5000자만 사용됩니다.') : '텍스트가 너무 길면 처음 5000자만 사용됩니다.',
          tip3: isLoaded ? (this.$t('textToQuestions.tip3') || '생성된 엑셀 파일은 문제 파일 목록에서 확인할 수 있습니다.') : '생성된 엑셀 파일은 문제 파일 목록에서 확인할 수 있습니다.'
        }
        
        this.translationsLoaded = true
      } catch (error) {
        console.error('번역 로드 실패:', error)
        this.translationsLoaded = true // 에러가 나도 화면은 표시
      }
    },
    async handleFileSelect(event) {
      this.selectedFile = event.target.files[0]
      this.uploadMessage = ''
      
      if (this.selectedFile) {
        const fileExtension = this.selectedFile.name.split('.').pop().toLowerCase()
        if (fileExtension !== 'txt') {
          this.uploadMessage = this.$t('textToQuestions.fileFormatNote')
          this.uploadMessageType = 'alert-warning'
          this.selectedFile = null
          this.$refs.fileInput.value = ''
          return
        }
        
        // 파일 크기 확인 (10MB 제한)
        if (this.selectedFile.size > 10 * 1024 * 1024) {
          this.uploadMessage = this.$t('textToQuestions.fileSizeLimit')
          this.uploadMessageType = 'alert-warning'
          this.selectedFile = null
          this.$refs.fileInput.value = ''
          return
        }
        
        // 파일명을 기본 제목으로 설정 (제목이 비어있을 때만)
        if (!this.inputTitle.trim()) {
          const fileNameWithoutExt = this.selectedFile.name.replace(/\.[^/.]+$/, '')
          // 중복 체크 후 자동으로 고유한 제목 생성
          await this.setUniqueTitle(fileNameWithoutExt)
        }
        
        this.uploadMessage = this.$t('textToQuestions.fileSelected', {
          fileName: this.selectedFile.name,
          fileSize: this.formatSize(this.selectedFile.size)
        })
        this.uploadMessageType = 'alert-info'
      }
    },
    isValidUrl(string) {
      try {
        const url = new URL(string)
        return url.protocol === 'http:' || url.protocol === 'https:'
      } catch (_) {
        return false
      }
    },
    extractDomainFromUrl(urlString) {
      try {
        const url = new URL(urlString)
        return url.hostname.replace(/^www\./, '') // www. 제거
      } catch (_) {
        return ''
      }
    },
    async setUniqueTitle(baseTitle) {
      if (!baseTitle || !baseTitle.trim()) {
        this.inputTitle = ''
        this.titleValidationError = ''
        return
      }
      
      // 공통 함수 사용
      const uniqueTitle = await generateUniqueTitle(baseTitle, true)
      this.inputTitle = uniqueTitle
      this.titleValidationError = ''
    },
    async processTextFile() {
      if (this.inputMode === 'file' && !this.selectedFile) {
        this.showToastMessage(this.$t('textToQuestions.fileRequired'), 'alert-warning', 'fas fa-exclamation-triangle')
        return
      }
      
      if (this.inputMode === 'url' && (!this.inputUrl.trim() || !this.isValidUrl(this.inputUrl))) {
        this.showToastMessage(this.$t('textToQuestions.urlRequired'), 'alert-warning', 'fas fa-exclamation-triangle')
        return
      }
      
      if (!this.questionCount || this.questionCount < 1 || this.questionCount > 50) {
        this.showToastMessage(this.$t('textToQuestions.questionCountInvalid'), 'alert-warning', 'fas fa-exclamation-triangle')
        return
      }
      
      // 태그는 반드시 1개 이상 선택되어야 함
      if (!this.newExamTags || this.newExamTags.length === 0) {
        this.showToastMessage(this.$t('textToQuestions.tagRequired'), 'alert-warning', 'fas fa-exclamation-triangle')
        return
      }
      
      // 시험 제목 중복 확인
      if (this.inputTitle && this.inputTitle.trim()) {
        await this.validateTitle()
        if (this.titleValidationError) {
          this.showToastMessage(this.titleValidationError, 'alert-warning', 'fas fa-exclamation-triangle')
          return
        }
      }

      this.isProcessing = true
      this.uploadMessage = ''
      this.processingStep = this.inputMode === 'file' 
        ? this.$t('textToQuestions.processingStep.readingFile')
        : this.$t('textToQuestions.processingStep.fetchingUrl')
      
      try {
        const formData = new FormData()
        
        if (this.inputMode === 'file') {
          formData.append('file', this.selectedFile)
          // 제목이 없으면 파일명 사용
          const title = this.inputTitle.trim() || this.selectedFile.name.replace(/\.[^/.]+$/, '')
          formData.append('title', title)
        } else {
          formData.append('url', this.inputUrl.trim())
          formData.append('title', this.inputTitle.trim() || '')
        }
        
        formData.append('question_count', this.questionCount)
        formData.append('is_public', this.isPublic)
        formData.append('ai_mock_interview', this.aiMockInterview)
        formData.append('exam_difficulty', this.examDifficulty || 5)
        
        // 태그 추가
        if (this.newExamTags && this.newExamTags.length > 0) {
          // FormData에서 배열을 보낼 때는 같은 키로 여러 번 append
          this.newExamTags.forEach((tagId) => {
            formData.append('tags', tagId)
          })
        }

        this.processingStep = this.$t('textToQuestions.processingStep.analyzingText')
        
              // 문제 생성은 시간이 오래 걸릴 수 있으므로 긴 타임아웃 인스턴스 사용
              const response = await apiWithLongTimeout.post('/api/text-to-questions/', formData, {
                headers: {
                  'Content-Type': 'multipart/form-data'
                }
              })
        
        this.processingStep = this.$t('textToQuestions.processingStep.creatingExcel')
        
        if (response.data && response.data.success) {
          const successMsg = response.data.message || this.$t('textToQuestions.successMessage')
          this.uploadMessage = successMsg
          this.uploadMessageType = 'alert-success'
          this.showToastMessage(successMsg, 'alert-success', 'fas fa-check-circle')
          
          // 성공 후 exam_id가 있으면 시험 상세 페이지로 이동, 없으면 파일 목록 페이지로 이동
          setTimeout(() => {
            if (response.data.exam_id) {
              const timestamp = Date.now()
              this.$router.push(`/exam-detail/${response.data.exam_id}?t=${timestamp}`)
            } else {
              this.$router.push('/question-files')
            }
          }, 2000)
        } else {
          const failureMsg = response.data?.error || this.$t('textToQuestions.failureMessage')
          throw new Error(failureMsg)
        }
      } catch (error) {
        debugLog('텍스트 파일 처리 오류:', error, 'error')
        this.uploadMessageType = 'alert-danger'
        const errorMsg = error.response?.data?.error || error.message || this.$t('textToQuestions.processingError')
        this.uploadMessage = errorMsg
        this.showToastMessage(errorMsg, 'alert-danger', 'fas fa-exclamation-circle')
      } finally {
        this.isProcessing = false
        this.processingStep = ''
      }
    },
    async resetForm() {
      this.selectedFile = null
      this.inputUrl = ''
      this.inputTitle = ''
      this.questionCount = 10
      this.uploadMessage = ''
      this.uploadMessageType = 'alert-info'
      this.isPublic = false
      this.aiMockInterview = false
      // resetForm 시에도 프로필 기반 기본값으로 재설정
      await this.loadDefaultDifficulty()
      this.newExamTags = [] // 태그 초기화
      this.titleValidationError = '' // 제목 검증 오류 초기화
      if (this.titleValidationTimer) {
        clearTimeout(this.titleValidationTimer)
        this.titleValidationTimer = null
      }
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = ''
      }
    },
    formatSize(bytes) {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
    },
    showToastMessage(message, type, icon) {
      this.toastMessage = message
      this.toastType = type
      this.toastIcon = icon
      this.showToast = true
      setTimeout(() => {
        this.hideToast()
      }, 5000)
    },
    hideToast() {
      this.showToast = false
    },
    // URL Input Handler
    async handleUrlInput() {
      // URL이 유효하고 제목이 비어있을 때만 도메인명으로 자동 설정
      if (this.inputUrl && this.inputUrl.trim() && this.isValidUrl(this.inputUrl)) {
        if (!this.inputTitle || !this.inputTitle.trim()) {
          const domain = this.extractDomainFromUrl(this.inputUrl)
          if (domain) {
            // 중복 체크 후 자동으로 고유한 제목 생성
            await this.setUniqueTitle(domain)
          }
        }
      }
    },
    // Title Validation
    handleTitleInput() {
      // 기존 타이머가 있으면 취소
      if (this.titleValidationTimer) {
        clearTimeout(this.titleValidationTimer)
      }
      
      // 입력이 비어있으면 검증 오류 제거
      if (!this.inputTitle || !this.inputTitle.trim()) {
        this.titleValidationError = ''
        return
      }
      
      // debounce: 500ms 후에 검증 실행
      this.titleValidationTimer = setTimeout(() => {
        this.validateTitle()
      }, 500)
    },
    async validateTitle() {
      if (!this.inputTitle || !this.inputTitle.trim()) {
        this.titleValidationError = ''
        return
      }
      
      try {
        const title = this.inputTitle.trim()
        // 공통 함수 사용하여 중복 체크
        const isDuplicate = await checkTitleDuplicate(title, true)
        
        if (isDuplicate) {
          // 번역이 로드되지 않았을 수 있으므로 안전하게 처리
          const translation = this.$t('examManagement.messages.duplicateTitle')
          // 번역 키가 그대로 반환되면 번역이 없는 것이므로 현재 언어에 맞는 fallback 사용
          if (translation === 'examManagement.messages.duplicateTitle' || !translation) {
            const currentLang = this.$i18n.locale || 'en'
            const fallbackMessages = {
              'ko': '이미 같은 이름의 시험이 존재합니다',
              'en': 'An exam with this title already exists',
              'es': 'Ya existe un examen con este título',
              'zh': '已存在相同标题的考试',
              'ja': 'このタイトルの試験が既に存在します'
            }
            this.titleValidationError = fallbackMessages[currentLang] || fallbackMessages['en']
          } else {
            this.titleValidationError = translation
          }
          return
        }
        
        // 중복 없음
        this.titleValidationError = ''
      } catch (error) {
        debugLog('시험 제목 검증 오류:', error, 'error')
        // 검증 오류가 발생해도 입력을 막지 않음 (네트워크 오류 등)
        this.titleValidationError = ''
      }
    },
    // Tag Management
    async loadTags() {
      try {
        const response = await axios.get('/api/studies/tags/')
        this.availableTags = response.data || []
      } catch (error) {
        console.error('태그 목록 로드 실패:', error)
      }
    },
    openTagModal() {
      this.showTagModal = true
    },
    handleTagUpdate(selectedTags) {
      this.newExamTags = selectedTags
    },
    handleTagApply(selectedTags) {
      this.newExamTags = selectedTags
      this.showTagModal = false
    },
    removeExamTag(tagId) {
      const index = this.newExamTags.indexOf(tagId)
      if (index > -1) {
        this.newExamTags.splice(index, 1)
      }
    },
    getSelectedTagName(tagId) {
      const tag = this.availableTags.find(t => t.id === tagId)
      if (!tag) {
        return this.$t('textToQuestions.loading')
      }
      // 사용자 프로필 언어 우선, 없으면 i18n locale, 기본값은 'en'
      const userLang = this.userProfileLanguage || this.$i18n?.locale || 'en'
      
      // 모든 지원 언어 필드를 확인하여 사용자 언어에 맞는 값 반환
      return getLocalizedContent(tag, 'name', userLang) || tag.localized_name || (userLang === 'ko' ? '태그 없음' : 'No Tag')
    },
    handleTagCreated(tag) {
      // 새로 생성된 태그를 availableTags에 추가
      if (!this.availableTags.find(t => t.id === tag.id)) {
        this.availableTags.push(tag)
        console.log('✅ 새 태그가 availableTags에 추가됨:', tag)
      }
    },
    handleTagError(error) {
      console.error('태그 에러:', error)
      this.showToastMessage(this.$t('textToQuestions.tagError'), 'alert-danger', 'fas fa-exclamation-circle')
    },
    async loadDefaultDifficulty() {
      // 프로필의 age_rating에 따라 기본 난이도 설정
      try {
        if (!this.isAuthenticated) {
          debugLog('[loadDefaultDifficulty] 로그인하지 않음, 기본값 5 사용')
          this.examDifficulty = 5 // 로그인하지 않은 경우 기본값 5
          return
        }
        
        // 먼저 캐시된 사용자 정보 확인
        const cachedUser = authService.getUserSync()
        debugLog('[loadDefaultDifficulty] 캐시된 사용자 정보:', cachedUser)
        if (cachedUser && cachedUser.age_rating) {
          const defaultDifficulty = getDefaultDifficultyByAgeRating(cachedUser.age_rating)
          debugLog(`[loadDefaultDifficulty] 캐시에서 age_rating 발견: ${cachedUser.age_rating} → 난이도: ${defaultDifficulty}`)
          this.examDifficulty = defaultDifficulty
          return
        }
        
        // 캐시에 없으면 API 호출
        debugLog('[loadDefaultDifficulty] API 호출하여 프로필 정보 가져오기')
        const response = await axios.get('/api/user-profile/get/')
        debugLog('[loadDefaultDifficulty] API 응답:', response.data)
        if (response.data && response.data.age_rating) {
          const defaultDifficulty = getDefaultDifficultyByAgeRating(response.data.age_rating)
          debugLog(`[loadDefaultDifficulty] API에서 age_rating 발견: ${response.data.age_rating} → 난이도: ${defaultDifficulty}`)
          this.examDifficulty = defaultDifficulty
          
          // 사용자 정보 업데이트 (다음번에는 캐시에서 가져올 수 있도록)
          if (cachedUser) {
            const updatedUser = { ...cachedUser, age_rating: response.data.age_rating }
            await authService.storeAuthResult({ user: updatedUser })
          }
        } else {
          debugLog('[loadDefaultDifficulty] API 응답에 age_rating 없음, 기본값 5 사용')
          this.examDifficulty = 5 // age_rating이 없으면 기본값 5
        }
      } catch (error) {
        debugLog('프로필 로드 실패, 기본 난이도 사용:', error)
        this.examDifficulty = 5 // 에러 시 기본값 5
      }
    }
  }
}
</script>

<style scoped>
/* QuestionFiles.vue와 동일한 스타일 사용 */
.text-to-questions-modern {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  color: white;
}

.files-container {
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
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
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

.action-btn-success {
  border-color: #28a745;
  background: #28a745;
  color: white;
}

.action-btn-success:hover:not(:disabled) {
  background: #218838;
  border-color: #218838;
}

.action-btn-secondary {
  border-color: #6c757d;
  background: #6c757d;
  color: white;
}

.action-btn-secondary:hover:not(:disabled) {
  background: #5a6268;
  border-color: #5a6268;
}

.action-label {
  font-size: 12px;
  font-weight: 500;
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

.page-description {
  font-size: 18px;
  opacity: 0.9;
  color: #666;
  margin-top: 10px;
}

.upload-section {
  padding: 30px;
  background: white;
  border-top: 1px solid #e9ecef;
}

.upload-card {
  background: white;
  border-radius: 15px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid #e9ecef;
  overflow: hidden;
}

.card-header-modern {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 20px 25px;
  border-bottom: 1px solid #e9ecef;
  background: #f8f9fa;
}

.card-header-modern h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
}

.upload-content {
  padding: 25px;
}

.input-mode-selector {
  margin-bottom: 20px;
  display: flex;
  justify-content: center;
}

.input-mode-selector .btn-group {
  display: flex;
  gap: 0;
}

.input-mode-selector .btn {
  padding: 10px 20px;
  border-radius: 0;
}

.input-mode-selector .btn:first-child {
  border-top-left-radius: 8px;
  border-bottom-left-radius: 8px;
}

.input-mode-selector .btn:last-child {
  border-top-right-radius: 8px;
  border-bottom-right-radius: 8px;
}

.upload-form {
  display: flex;
  gap: 15px;
  align-items: end;
  flex-wrap: wrap;
  margin-bottom: 20px;
}

.upload-input-group {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
  flex: 1;
  min-width: 100%;
}

.upload-input {
  flex: 1;
  min-width: 300px;
  display: flex;
  flex-direction: column;
}

.upload-input.upload-input-number {
  flex: 0 0 auto;
  min-width: 150px;
  width: auto;
  display: flex;
  flex-direction: column;
  position: relative;
}

.upload-input.upload-input-difficulty {
  flex: 0 0 auto;
  max-width: 45%;
  min-width: 200px;
  width: auto;
  display: flex;
  flex-direction: column;
}

.upload-input.upload-input-number .form-label {
  margin-bottom: 5px;
}

.upload-input.upload-input-number .input-wrapper {
  display: flex;
  flex-direction: column;
  margin-top: auto;
  position: relative;
}

.upload-input.upload-input-number .form-control {
  margin-bottom: 0;
}

.upload-input.upload-input-number .form-text {
  white-space: nowrap;
  margin-top: 5px;
  margin-bottom: 0;
  position: relative;
  display: block;
  width: 100%;
}

.upload-input .form-label {
  font-weight: 500;
  margin-bottom: 5px;
  color: #333;
}

.upload-input .input-wrapper {
  display: flex;
  flex-direction: column;
}

.upload-input .form-control {
  flex-shrink: 0;
  margin-bottom: 0;
}

/* Range Input 스타일 - 그라데이션 배경 */
.upload-input input[type="range"].form-control {
  -webkit-appearance: none;
  appearance: none;
  height: 8px;
  background: transparent;
  padding: 0;
  margin-top: 18px;
}

/* Webkit 브라우저 (Chrome, Safari, Edge) */
.upload-input input[type="range"].form-control::-webkit-slider-runnable-track {
  width: 100%;
  height: 8px;
  background: linear-gradient(to right, #ffffff 0%, #ff0000 100%);
  border-radius: 4px;
  cursor: pointer;
}

.upload-input input[type="range"].form-control::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  background: #007bff;
  border-radius: 50%;
  cursor: pointer;
  margin-top: -6px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  transition: all 0.2s ease;
}

.upload-input input[type="range"].form-control::-webkit-slider-thumb:hover {
  transform: scale(1.1);
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3);
}

/* Firefox */
.upload-input input[type="range"].form-control::-moz-range-track {
  width: 100%;
  height: 8px;
  background: linear-gradient(to right, #ffffff 0%, #ff0000 100%);
  border-radius: 4px;
  cursor: pointer;
  border: none;
}

.upload-input input[type="range"].form-control::-moz-range-thumb {
  width: 20px;
  height: 20px;
  background: #007bff;
  border-radius: 50%;
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  transition: all 0.2s ease;
}

.upload-input input[type="range"].form-control::-moz-range-thumb:hover {
  transform: scale(1.1);
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3);
}

/* IE/Edge */
.upload-input input[type="range"].form-control::-ms-track {
  width: 100%;
  height: 8px;
  background: transparent;
  border-color: transparent;
  color: transparent;
  cursor: pointer;
}

.upload-input input[type="range"].form-control::-ms-fill-lower {
  background: linear-gradient(to right, #ffffff 0%, #ff0000 100%);
  border-radius: 4px;
}

.upload-input input[type="range"].form-control::-ms-fill-upper {
  background: linear-gradient(to right, #ffffff 0%, #ff0000 100%);
  border-radius: 4px;
}

.upload-input input[type="range"].form-control::-ms-thumb {
  width: 20px;
  height: 20px;
  background: #007bff;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.upload-input .form-text {
  margin-top: 5px;
  flex-shrink: 0;
  margin-bottom: 0;
}

.upload-options {
  display: flex;
  align-items: center;
  align-self: flex-end;
  margin-bottom: 0;
  margin-top: 20px;
}

.upload-options .form-check {
  margin-bottom: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  position: relative;
  z-index: 1;
}

.upload-options .form-check-input {
  margin: 0;
  cursor: pointer;
  pointer-events: auto;
  position: relative;
  z-index: 2;
}

.upload-options .form-check-label {
  margin: 0;
  cursor: pointer;
  pointer-events: auto;
  user-select: none;
}

.upload-actions {
  display: flex;
  gap: 10px;
  align-self: flex-end;
  margin-left: auto;
  margin-top: 25px;
}

.upload-message {
  margin-top: 15px;
  padding: 12px 16px;
  border-radius: 8px;
  font-weight: 500;
}

.upload-message.alert-success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.upload-message.alert-danger {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.upload-message.alert-warning {
  background: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
}

.upload-message.alert-info {
  background: #d1ecf1;
  color: #0c5460;
  border: 1px solid #bee5eb;
  margin-top: 40px;
}

.processing-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  margin-top: 20px;
}

.progress-info {
  margin-top: 15px;
  color: #6c757d;
}

.info-section {
  margin-top: 30px;
}

.info-alert {
  background: #e3f2fd;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 15px;
  margin-top: 40px;
  border: 1px solid #bbdefb;
  color: #1976d2;
}

.info-alert i {
  margin-right: 8px;
}

.info-steps,
.info-tips {
  padding-left: 20px;
  margin-bottom: 15px;
}

.info-steps li,
.info-tips li {
  margin-bottom: 8px;
  line-height: 1.6;
}

/* Toast Notifications - 기본 스타일은 공통 CSS (mobile-buttons.css)에 정의됨 */

.toast-content {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.toast-close {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  margin-left: 15px;
  opacity: 0.7;
}

.toast-close:hover {
  opacity: 1;
}

/* 타입별 스타일은 공통 CSS (mobile-buttons.css)에 정의됨 */

@media (max-width: 768px) {
  .text-to-questions-modern {
    padding: 10px;
  }
  
  .upload-section {
    padding: 10px;
  }
  
  /* 원형 버튼 스타일은 공통 CSS (mobile-buttons.css)에서 처리됨 */
  
  .upload-options .form-check-input {
    flex-shrink: 0;
    width: 20px !important;
    height: 20px !important;
    min-width: 20px !important;
    min-height: 20px !important;
    vertical-align: middle;
    cursor: pointer;
    pointer-events: auto;
    z-index: 1;
    position: relative;
    display: block !important;
    opacity: 1 !important;
    visibility: visible !important;
  }
  
  .upload-options .form-check-label {
    display: flex;
    align-items: center;
    line-height: 1.5;
    cursor: pointer;
    pointer-events: auto;
    user-select: none;
  }
  
  .upload-options .form-check {
    cursor: pointer;
    pointer-events: auto;
  }
  
  /* 모바일에서 태그 검색 버튼 텍스트 숨기기 */
  .tag-search-btn .tag-search-text {
    display: none;
  }
  
  .tag-search-btn {
    padding: 6px 12px !important;
  }
}
</style>

