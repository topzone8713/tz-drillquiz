/* eslint-disable */
// TODO: console.log를 debugLog로 변경할 수 있는지 반드시 검토해야 함
// - 운영 환경에서 브라우저 콘솔에 로그가 보이면 안 됨
// - debugLog는 운영 환경에서 자동으로 비활성화됨
import EntityTagManager from '@/components/EntityTagManager.vue'
import axios from 'axios'
import { debugLog } from '@/utils/debugUtils'
import { getLocalizedContentWithI18n } from '@/utils/multilingualUtils'
import authService from '@/services/authService'



<template>
  <div class="exam-detail-modern">
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
    
    <!-- Share Modal -->
    <ShareModal
      :show="showShareModal"
      :share-url="shareUrl"
      :exam-id="exam?.id"
      :is-mobile-device="isMobileDevice"
      @close="closeShareModal"
      @success="showSuccessToast"
      @error="showErrorToast"
    />
    
    <!-- AI Mock Interview Detail Modal -->
    <div v-if="showAIMockInterviewModal" class="modal-overlay" @click="hideAIMockInterviewModal">
      <!-- Voice Interview 모드 (모바일 및 웹 환경 모두 지원) -->
      <div v-if="showVoiceInterview" class="mobile-voice-interview-container" @click.stop>
        <MobileVoiceInterview
          :exam-id="selectedQuestionForAI?.id"
          :exam-title="selectedQuestionForAI?.localized_title || selectedQuestionForAI?.title"
          :language="currentLanguage"
          :voice="'alloy'"
          :instructions="interviewPromptText"
          :questions="questions"
          @interview-ended="handleInterviewEnded"
          @session-created="handleSessionCreated"
        />
      </div>
      
      <!-- 웹 환경: 클립보드 복사 모드 -->
      <div v-else class="modal-content" @click.stop>
        <div class="modal-header">
          <h5 class="modal-title">
            <i class="fas fa-robot"></i>
            {{ $t('examDetail.aiMockInterviewSupport') || 'AI 모의 인터뷰 지원' }}
          </h5>
          <button class="modal-close" @click="hideAIMockInterviewModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <div class="ai-mock-interview-detail">
            <div class="exam-info">
              <p><strong>{{ $t('examDetail.examTitle') || '제목' }}:</strong> {{ selectedQuestionForAI?.localized_title || selectedQuestionForAI?.title }}</p>
              <p><strong>{{ $t('examDetail.totalQuestions') || '총 문제 수' }}:</strong> {{ selectedQuestionForAI?.total_questions || 0 }}{{ $t('examDetail.questionsUnit') || '개' }}</p>
            </div>
            
            <!-- 음성 대화 모드 옵션 (모바일 및 웹 환경 모두 지원) -->
            <div class="mobile-options">
              <button @click.stop="startVoiceInterview" class="btn btn-primary voice-interview-btn">
                <i class="fas fa-microphone"></i>
                {{ $t('examDetail.startVoiceInterview') || '음성 대화 모드 시작' }}
              </button>
              <p class="option-description">
                {{ $t('examDetail.voiceInterviewDescription') || 'ChatGPT Voice Conversation Mode와 유사한 실시간 음성 대화로 인터뷰를 진행합니다.' }}
              </p>
            </div>
            
            <!-- 클립보드 복사 섹션 -->
            <div class="clipboard-section">
              <div class="clipboard-content">
                  <div class="interview-prompt">
                    <textarea 
                      v-model="interviewPromptText" 
                      class="prompt-textarea" 
                      ref="interviewPrompt"
                      rows="15"
                    ></textarea>
                  </div>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
            <button @click="resetPrompt" class="reset-btn">
              <i class="fas fa-undo"></i>
              {{ $t('examDetail.reset') || '초기화' }}
            </button>
            <button @click="copyToClipboard" class="copy-btn">
              <i class="fas fa-copy"></i>
              {{ $t('examDetail.copyToClipboard') || '클립보드에 복사' }}
            </button>
            <button class="btn btn-secondary" @click="hideAIMockInterviewModal">
              {{ $t('examDetail.close') || '닫기' }}
            </button>
        </div>
      </div>
    </div>

    <!-- Translation Modal -->
    <div v-if="showTranslateModal" class="modal-overlay" @click="showTranslateModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h5 class="modal-title">
            <i class="fas fa-language"></i>
            {{ $t('examDetail.translateModalTitle') || 'Select Translation Languages' }}
          </h5>
          <button class="modal-close" @click="showTranslateModal = false">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <p>{{ $t('examDetail.translateModalDescription') || 'Select the languages to translate to.' }}</p>
          <div class="translation-languages">
            <div class="language-actions mb-2">
              <button @click="selectAllLanguages" class="btn btn-sm btn-secondary me-2">
                <i class="fas fa-check-square"></i>
                <span v-if="!isMobileDevice">{{ $t('examDetail.selectAll') || 'Select All' }}</span>
              </button>
              <button @click="deselectAllLanguages" class="btn btn-sm btn-secondary">
                <i class="fas fa-square"></i>
                <span v-if="!isMobileDevice">{{ $t('examDetail.deselectAll') || 'Deselect All' }}</span>
              </button>
            </div>
            <div v-for="lang in availableLanguages" :key="lang.code" class="form-check">
              <input 
                class="form-check-input" 
                type="checkbox" 
                :id="`lang-${lang.code}`"
                :value="lang.code"
                v-model="selectedLanguages"
              >
              <label class="form-check-label" :for="`lang-${lang.code}`">
                {{ lang.name }}
              </label>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showTranslateModal = false">
            <i class="fas fa-times"></i>
            <span v-if="!isMobileDevice">{{ $t('modal.cancel') || '취소' }}</span>
          </button>
          <button class="btn btn-primary" @click="handleTranslateExam" :disabled="selectedLanguages.length === 0">
            <i class="fas fa-check"></i>
            <span v-if="!isMobileDevice">{{ $t('examDetail.apply') || '적용' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Options Modal -->
    <div v-if="showOptionsModal" class="modal-overlay" @click="hideOptionsModal">
      <div class="modal-content options-modal" @click.stop>
        <div class="modal-header">
          <h5 class="modal-title">
            <i class="fas fa-cog"></i>
            {{ $t('examDetail.options') }}
          </h5>
          <button class="modal-close" @click="hideOptionsModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <div class="options-content">
            <!-- Random Exam Controls -->
            <div class="options-section" v-if="filteredQuestions.length > 0">
              <h6>{{ $t('examDetail.randomExamControls') }}</h6>
              <div class="options-grid">
                <div class="option-group">
                  <label>{{ $t('examDetail.examTitleOptional') }}</label>
                  <input 
                    v-model="customExamTitle" 
                    type="text" 
                    class="form-control" 
                    :placeholder="$t('examDetail.examTitlePlaceholder')"
                  >
                </div>
                <div class="option-group">
                  <label>{{ $t('examDetail.questionCountToUse') }}</label>
                  <input 
                    v-model.number="selectedQuestionCount" 
                    type="number" 
                    class="form-control" 
                    :min="1" 
                    :max="Math.min(filteredQuestions.length, 10)"
                    :disabled="selectedQuestions.length > 0"
                  >
                </div>

                <div class="option-group">
                  <label>{{ $t('examDetail.randomOptionLabel') }}</label>
                  <select v-model="randomOption" class="form-control" :disabled="selectedQuestions.length > 0">
                    <option value="wrong_only">{{ $t('examDetail.wrongQuestions') }}</option>
                    <option value="most_wrong">{{ $t('examDetail.mostWrongQuestions') }}</option>
                    <option value="random">{{ $t('examDetail.justRandom') }}</option>
                  </select>
                </div>
              </div>
              <div class="options-actions">
                <button @click="clearSelection" class="action-btn action-btn-secondary">
                  <i class="fas fa-times"></i>
                  <span>{{ $t('examDetail.clearSelection') }}</span>
                </button>
                <button 
                  @click="createRandomExam" 
                  class="action-btn action-btn-success"
                  :disabled="filteredQuestions.length === 0"
                >
                  <i class="fas fa-plus"></i>
                  <span>{{ $t('examDetail.createExam') }}</span>
                </button>
              </div>
            </div>
            
            <!-- Question Management Controls -->
            <div class="options-section" v-if="exam && selectedQuestions.length > 0">
              <h6>{{ $t('examDetail.questionManagement') }}</h6>
              <div class="options-grid">
                <div class="option-group">
                  <label>{{ $t('examDetail.selectExamLabel') }}</label>
                  <select v-model="selectedTargetExamId" class="form-control">
                    <option value="">{{ $t('examDetail.selectExam') }}</option>
                    <option v-for="targetExam in availableExams" :key="targetExam.id" :value="targetExam.id">
                      {{ getLocalizedTitle(targetExam) }} ({{ targetExam.total_questions }} {{ $t('examDetail.questions') }})
                    </option>
                  </select>
                </div>
                <div class="option-group">
                  <label>{{ $t('examDetail.selectedQuestionsLabel') }}</label>
                  <span class="selected-count">{{ selectedQuestions.length }}</span>
                </div>
              </div>
              <div class="options-actions">
                <!-- Move Questions (즐겨찾기 모드에서는 숨김) -->
                <button 
                  v-if="!isFavoriteMode"
                  @click="moveQuestionsToExam" 
                  class="action-btn action-btn-warning"
                  :disabled="!selectedTargetExamId"
                >
                  <i class="fas fa-arrow-right"></i>
                  <span>{{ $t('examDetail.moveQuestions') }}</span>
                </button>
                <!-- Copy Questions (항상 표시) -->
                <button 
                  @click="copyQuestionsToExam" 
                  class="action-btn action-btn-info"
                  :disabled="!selectedTargetExamId"
                >
                  <i class="fas fa-copy"></i>
                  <span>{{ $t('examDetail.copyQuestions') }}</span>
                </button>
              </div>
            </div>
            
            <!-- Group ID Controls (즐겨찾기 모드에서는 숨김) -->
            <div class="options-section" v-if="!isFavoriteMode && selectedQuestions.length > 0">
              <h6>{{ $t('examDetail.groupManagement') }}</h6>
              <div class="options-grid">
                <div class="option-group">
                  <label>{{ $t('examDetail.enterGroupIdLabel') }}</label>
                  <input v-model="groupIdInput" class="form-control" :placeholder="$t('examDetail.groupIdPlaceholder')">
                </div>
                <div class="option-group">
                  <label>{{ $t('examDetail.selectedQuestionsLabel') }}</label>
                  <span class="selected-count">{{ selectedQuestions.length }}</span>
                </div>
              </div>
              <div class="options-actions">
                <button @click="applyGroupIdToSelected" class="action-btn action-btn-success" :disabled="!groupIdInput">
                  <i class="fas fa-tags"></i>
                  <span>{{ $t('examDetail.applyGroup') }}</span>
                </button>
              </div>
            </div>
            
            <!-- Member Mapping Controls (즐겨찾기 모드에서는 숨김) -->
            <div class="options-section" v-if="!isFavoriteMode && exam && selectedQuestions.length > 0">
              <h6>{{ $t('examDetail.memberManagement') }}</h6>
              <div class="options-grid">
                <div class="option-group">
                  <label>{{ $t('examDetail.selectStudyLabel') }}</label>
                  <select v-model="selectedStudyId" class="form-control" @change="loadStudyMembers">
                    <option value="">{{ $t('examDetail.selectStudy') }}</option>
                    <option v-for="study in validStudies" :key="study.id" :value="study.id">
                      {{ localizedStudyTitle(study) }}
                    </option>
                  </select>
                </div>
                <div class="option-group">
                  <label>{{ $t('examDetail.memberCountLabel') }}</label>
                  <span class="selected-count">{{ $t('examDetail.person', { count: studyMembers.length }) }}</span>
                </div>
              </div>
              <div class="options-actions">
                <button 
                  @click="goToMemberManagement" 
                  class="action-btn action-btn-warning"
                  :disabled="!selectedStudyId"
                  v-if="isAdmin"
                >
                  <i class="fas fa-users"></i>
                  <span>{{ $t('examDetail.memberManagement') }}</span>
                </button>
                <button 
                  @click="createMemberMapping" 
                  class="action-btn action-btn-info"
                  :disabled="!selectedStudyId || studyMembers.length === 0"
                >
                  <i class="fas fa-link"></i>
                  <span>{{ $t('examDetail.memberQuestionMapping') }}</span>
                </button>
                <button 
                  @click="loadMappings" 
                  class="action-btn action-btn-secondary"
                  :disabled="!exam"
                >
                  <i class="fas fa-eye"></i>
                  <span>{{ $t('examDetail.viewMappings') }}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    

    
    <!-- 번역 로딩 중일 때 로딩 표시 -->
    <div v-if="!translationsLoaded" class="loading-container">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">{{ $t('common.loadingTranslations') }}</span>
      </div>
      <p class="mt-3">{{ $t('common.loadingTranslationData') }}</p>
    </div>
    
    <!-- 번역이 로드된 후에만 컨텐츠 표시 -->
    <div v-else class="exam-container">
      <!-- Top Header -->
      <div class="top-header">
        <div class="header-actions">
          
          <!-- Share 버튼 (17+ 등급만 표시) -->
          <button 
            v-if="showShareButton"
            @click="openShareModal" 
            class="action-btn action-btn-info"
            :title="$t('examDetail.shareTooltip')"
          >
            <i class="fas fa-link"></i>
            <span class="action-label">{{ $t('examDetail.share') }}</span>
          </button>

          <!-- Daily Exam 버튼 -->
          <button 
            @click="createRandomRecommendationExams" 
            class="action-btn action-btn-warning"
            v-if="isAuthenticated && isCurrentUserDailyExam"
          >
            <i class="fas fa-random"></i>
            <span class="action-label">{{ $t('examManagement.randomExam') }}</span>
          </button>
          
          <!-- My Exam 버튼 -->
          <button 
            v-if="isAdmin || isStudyAdmin"
            @click="goToExamManagement" 
            class="action-btn action-btn-success"
          >
            <i class="fas fa-cog"></i>
            <span class="action-label">{{ $t('examDetail.myExam') }}</span>
          </button>
          
          <!-- 관리자 드롭다운 메뉴 -->
          <div class="admin-dropdown-container" v-if="isAuthenticated">
            <button 
              class="action-btn action-btn-modern admin-dropdown-toggle" 
              @click.stop="toggleAdminDropdownMenu"
              :class="{ 'active': showAdminDropdownMenu }"
              type="button"
            >
              <i class="fa-solid fa-ellipsis-vertical"></i>
            </button>
            
            <div v-if="showAdminDropdownMenu" class="admin-dropdown-menu" @click.stop>
              <button 
                v-if="canDeleteQuestions"
                @click="handleAdminDropdownAction('deleteSelectedQuestions')" 
                class="admin-dropdown-item"
                :disabled="selectedQuestions.length === 0"
              >
                <i class="fas fa-trash"></i>
                <span>{{ safeTranslate('examDetail.deleteQuestions', '문제 삭제') }}</span>
              </button>
              <button 
                @click="handleAdminDropdownAction('deleteSelectedQuestionResultsGlobal')" 
                class="admin-dropdown-item"
                :disabled="selectedQuestions.length === 0"
              >
                <i class="fas fa-exclamation-triangle"></i>
                <span>{{ safeTranslate('examDetail.forceDelete', '강제삭제') }}</span>
              </button>
              <button 
                v-if="isAdmin || isStudyAdmin"
                @click="handleAdminDropdownAction('deleteAllQuestionResults')" 
                class="admin-dropdown-item"
              >
                <i class="fas fa-trash-alt"></i>
                <span>{{ safeTranslate('examDetail.deleteAllResults', '전체 결과 삭제') }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Page Title -->
      <div class="page-title">
        <h1 v-if="isFavoriteMode">
          {{ localizedExamTitle }}
        </h1>
        <h1 v-else>{{ localizedExamTitle }}</h1>
      </div>
      
      <!-- Exam Info Card -->
      <div class="exam-info-card" v-if="exam">
        <div class="card-header-modern">
          <h3>{{ safeTranslate('examDetail.examInfo', '시험 정보') }}</h3>
          <div class="card-actions">
            <button v-if="exam && exam.ai_mock_interview && !isMobileDevice" @click="showAIMockInterviewDetail(exam)" class="action-btn action-btn-info action-btn-large ai-mock-interview-btn">
              <i class="fas fa-robot"></i>
              <span class="action-label">{{ $t('examDetail.aiMockInterview') || 'AI 모의 인터뷰' }}</span>
            </button>
            <div class="accuracy-adjustment-controls">
              <button @click="decreaseAccuracy" class="accuracy-btn accuracy-btn-decrease" title="정확도 낮추기">
                <i class="fas fa-arrow-down"></i>
              </button>
              <div class="accuracy-slider-container">
                              <input 
                v-model.number="accuracyAdjustmentPercentage" 
                type="range" 
                class="accuracy-slider" 
                :min="0" 
                :max="100"
                step="1"
                @input="onAccuracySliderChange"
                @mouseup="onAccuracySliderMouseUp"
              >
                <span class="accuracy-percentage">{{ accuracyAdjustmentPercentage }}%</span>
              </div>
              <button @click="increaseAccuracy" class="accuracy-btn accuracy-btn-increase" title="정확도 높이기">
                <i class="fas fa-arrow-up"></i>
              </button>
            </div>
            <button @click="toggleExamInfo" class="card-action-btn">
              <i class="fas fa-info-circle"></i>
              <span class="action-label">{{ safeTranslate('examDetail.detail', 'Detail') }}</span>
            </button>
            <button v-if="exam && exam.ai_mock_interview && isMobileDevice" @click="showAIMockInterviewDetail(exam)" class="action-btn action-btn-info action-btn-large ai-mock-interview-btn">
              <i class="fas fa-robot"></i>
              <span class="action-label">{{ $t('examDetail.aiMockInterview') || 'AI 모의 인터뷰' }}</span>
            </button>
            <button v-if="showExamInfo && !isFavoriteMode && (isAdmin || isStudyAdmin || isExamCreator)" @click="toggleEditInfo" class="card-action-btn">
              <i class="fas fa-edit"></i>
              <span class="action-label">{{ safeTranslate('examDetail.edit', 'Edit') }}</span>
            </button>
          </div>
        </div>
        
        <div class="exam-info-content" v-if="!isEditingInfo && showExamInfo">
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">{{ safeTranslate('examDetail.totalQuestions', '총 문제 수') }}:</span>
              <span class="info-value">{{ exam.total_questions || questions.length || 0 }}</span>
            </div>

            <div class="info-item" v-if="examTotalCorrect !== undefined && examTotalQuestions !== undefined">
              <span class="info-label">{{ safeTranslate('examDetail.correctQuestions', '맞춘 문제횟수') }}:</span>
              <span class="info-value">{{ examTotalCorrect }} / {{ examTotalQuestions }}</span>
            </div>
            <div class="info-item" v-if="latestScorePercentage !== undefined">
              <span class="info-label">{{ safeTranslate('examDetail.latestScore', '최신 점수') }}:</span>
              <span class="info-value score-value">{{ latestScorePercentage }}%</span>
            </div>
            <div class="info-item">
              <span class="info-label">{{ safeTranslate('examDetail.version', '버전') }}:</span>
              <span class="info-value">{{ exam.version_number || 1 }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">{{ safeTranslate('examDetail.originalExam', '원본 시험') }}:</span>
              <span class="info-value">{{ exam.is_original ? safeTranslate('examDetail.original', '원본') : safeTranslate('examDetail.retake', '재시험') }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">{{ safeTranslate('examDetail.publicStatus', '공개 여부') }}:</span>
              <span class="status-badge" :class="exam.is_public ? 'status-public' : 'status-private'">
                {{ exam.is_public ? safeTranslate('examDetail.public', '공개') : safeTranslate('examDetail.private', '비공개') }}
              </span>
            </div>
            <div class="info-item">
              <span class="info-label">{{ safeTranslate('examDetail.forceAnswer', '답안 입력 강제') }}:</span>
              <span class="status-badge" :class="exam.force_answer ? 'status-enabled' : 'status-disabled'">
                {{ exam.force_answer ? safeTranslate('examDetail.enabled', '활성화') : safeTranslate('examDetail.disabled', '비활성화') }}
              </span>
            </div>
            <div class="info-item" v-if="exam.age_rating !== undefined && exam.age_rating !== null">
              <span class="info-label">{{ $t('examDetail.ageRating') }}:</span>
              <span class="info-value">{{ exam.age_rating || '17+' }}</span>
            </div>
            <div class="info-item" v-if="exam.exam_difficulty !== undefined">
              <span class="info-label">{{ safeTranslate('examDetail.examDifficulty', '시험 난이도') }}:</span>
              <span class="info-value">{{ exam.exam_difficulty || 5 }} / 10</span>
            </div>
            <div class="info-item">
              <span class="info-label">{{ safeTranslate('examDetail.voiceMode', '음성 모드 지원') }}:</span>
              <span class="status-badge" :class="exam.voice_mode_enabled ? 'status-enabled' : 'status-disabled'">
                {{ exam.voice_mode_enabled ? safeTranslate('examDetail.enabled', '활성화') : safeTranslate('examDetail.disabled', '비활성화') }}
              </span>
            </div>
            <div class="info-item" v-if="exam.ai_mock_interview && isAuthenticated && hasVoiceInterviewResults">
              <span class="info-label">{{ safeTranslate('examDetail.voiceInterviewResults', '음성 인터뷰 결과') }}:</span>
              <router-link 
                :to="`/exam/${exam.id}/voice-interview-results`" 
                class="progress-button"
              >
                <i class="fas fa-chart-bar me-1"></i>
                {{ safeTranslate('examDetail.viewVoiceInterviewResults', '결과 보기') }}
              </router-link>
            </div>
            <div class="info-item" v-if="exam.file_name && isAuthenticated">
              <a 
                :href="`/api/question-files/${exam.file_name}/download/`" 
                class="file-link"
                :download="exam.file_name"
                :title="safeTranslate('examDetail.connectedFileDownload', '연결된 파일 다운로드')"
              >
                <i class="fas fa-download"></i>
                {{ exam.file_name }}
              </a>
            </div>
            <div class="info-item" v-if="(isAdmin || isStudyAdmin || isExamCreator) && exam">
              <span class="info-label">{{ $t('examDetail.supportedLanguagesLabel') || 'Supported Languages' }}:</span>
              <span class="info-value">{{ exam.supported_languages || '' }}</span>
              <button 
                v-if="isAdmin || isStudyAdmin || isExamCreator"
                @click="showTranslateModal = true"
                class="btn btn-sm btn-primary ms-2"
                style="margin-left: 10px;"
              >
                <i class="fas fa-language"></i>
                <span v-if="!isMobileDevice">{{ $t('examDetail.translateButton') || '번역' }}</span>
              </button>
            </div>
            <div class="info-item" v-if="connectedStudies.length > 0">
              <span class="info-label">{{ safeTranslate('examDetail.connectedProjects.label', '연결된 프로젝트:') }}</span>
              <div class="connected-projects">
                <div v-if="connectedStudies.length === 1" class="single-project">
                  <a 
                    :href="connectedStudies[0].study_url" 
                    class="project-link"
                    :title="connectedStudies[0].study_title"
                  >
                    <i class="fas fa-external-link-alt"></i>
                    {{ connectedStudies[0].study_title }}
                  </a>
                </div>
                <div v-else class="multiple-projects">
                  <div class="project-selector">
                    <button 
                      @click="showProjectSelector = !showProjectSelector"
                      class="btn btn-outline-primary btn-sm"
                      :title="safeTranslate('examDetail.connectedProjects.multiple', '프로젝트 선택')"
                    >
                      <i class="fas fa-list"></i>
                      {{ safeTranslate('examDetail.connectedProjects.multiple', '프로젝트 선택') }}
                    </button>
                    <div v-if="showProjectSelector" class="project-dropdown">
                      <div 
                        v-for="study in connectedStudies" 
                        :key="study.study_id"
                        class="project-item"
                      >
                        <a 
                          :href="study.study_url" 
                          class="project-link"
                          :title="study.study_title"
                        >
                          <i class="fas fa-external-link-alt"></i>
                          {{ study.study_title }}
                        </a>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
          </div>
          
          <div class="description-section" v-if="localizedExamDescription">
            <h4>{{ safeTranslate('examDetail.description', '설명') }}:</h4>
            <div class="description-content" v-html="formatDescription(localizedExamDescription)"></div>
          </div>
          
          <!-- Tags Management Section -->
          <div class="card-modern tag-management-card" v-if="exam && (isAdmin || isStudyAdmin || isExamCreator)">
            <div class="card-header-modern">
              <h3>{{ safeTranslate('examDetail.tagManagement', '태그 관리') }}</h3>
            </div>
            
            <EntityTagManager
              entityType="exam"
              :entityId="exam.id"
              :tags="exam.tags || []"
              :canEdit="isAdmin || isStudyAdmin || isExamCreator"
              @tags-updated="handleTagsUpdated"
              @success="handleTagSuccess"
              @error="handleTagError"
            />
          </div>
        </div>
        
        <!-- Edit Form -->
        <div class="edit-form" v-if="isEditingInfo && showExamInfo">
          <div class="form-grid">
            <div class="form-group">
              <label>{{ $t('examDetail.titleLabel') }}:</label>
              <input v-model="editingTitle" class="form-control" />
            </div>
            <div class="form-group">
              <label>{{ $t('examDetail.createdAtLabel') }}:</label>
              <input v-model="editingCreatedAt" type="datetime-local" class="form-control" />
            </div>
            <div class="form-group">
              <label>{{ $t('examDetail.versionLabel') }}:</label>
              <input v-model.number="editingVersion" type="number" min="1" class="form-control" />
            </div>
            <div class="form-group">
              <label>{{ $t('examDetail.ageRatingLabel') }}:</label>
              <select 
                v-model="editingAgeRating" 
                class="form-control"
              >
                <option 
                  v-for="rating in availableAgeRatings" 
                  :key="rating" 
                  :value="rating"
                >
                  {{ rating }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>{{ safeTranslate('examDetail.examDifficultyLabel', '시험 난이도') }}:</label>
              <input 
                v-model.number="editingExamDifficulty" 
                type="range" 
                min="1" 
                max="10" 
                class="form-control" 
                style="width: 100%;"
              />
            </div>
            <div class="form-group">
              <label>&nbsp;</label>
              <div class="checkbox-group">
                <input 
                  v-model="editingIsPublic" 
                  type="checkbox" 
                  class="form-check-input" 
                  id="editingIsPublic"
                >
                <label class="form-check-label" for="editingIsPublic">
                  {{ $t('examDetail.publicStatus') }}
                </label>
              </div>
            </div>
            <div class="form-group">
              <label>&nbsp;</label>
              <div class="checkbox-group">
                <input 
                  v-model="editingForceAnswer" 
                  type="checkbox" 
                  class="form-check-input" 
                  id="editingForceAnswer"
                >
                <label class="form-check-label" for="editingForceAnswer">
                  {{ $t('examDetail.forceAnswer') }}
                </label>
              </div>
            </div>
            <div class="form-group">
              <label>&nbsp;</label>
              <div class="checkbox-group">
                <input 
                  v-model="editingVoiceModeEnabled" 
                  type="checkbox" 
                  class="form-check-input" 
                  id="editingVoiceModeEnabled"
                >
                <label class="form-check-label" for="editingVoiceModeEnabled">
                  {{ $t('examDetail.voiceMode') }}
                </label>
              </div>
            </div>
            <div class="form-group">
              <label>&nbsp;</label>
              <div class="checkbox-group">
                <input 
                  v-model="editingAIMockInterview" 
                  type="checkbox" 
                  class="form-check-input" 
                  id="editingAIMockInterview"
                >
                <label class="form-check-label" for="editingAIMockInterview">
                  {{ $t('examDetail.aiMockInterview') || 'AI 모의 인터뷰' }}
                </label>
              </div>
            </div>
            <!-- Supported Languages (Admin only) -->
            <div v-if="isAdmin" class="form-group">
              <label>{{ $t('examDetail.supportedLanguagesLabel') || 'Supported Languages' }}:</label>
              <input 
                v-model="editingSupportedLanguages" 
                type="text" 
                class="form-control" 
                :placeholder="$t('examDetail.supportedLanguagesPlaceholder') || '예: ko,en'"
              />
              <small class="form-text text-muted">
                {{ $t('examDetail.supportedLanguagesHelp') || '콤마로 구분된 언어 코드 (예: ko,en)' }}
              </small>
            </div>
            <!-- 문제 붙여넣기 체크박스 (localhost에서만 표시) -->
            <div v-if="showPasteProblemCheckbox" class="form-group">
              <label>&nbsp;</label>
              <div class="checkbox-group">
                <input 
                  v-model="pasteProblemMode" 
                  type="checkbox" 
                  class="form-check-input" 
                  id="pasteProblemCheck"
                  @change="onPasteProblemChange"
                >
                <label class="form-check-label" for="pasteProblemCheck">
                  {{ $t('examManagement.createForm.aiGenerateQuestions') }}
                </label>
              </div>
            </div>
          </div>
          
          <!-- AI 문제 생성기 (localhost에서만 표시) -->
          <div v-if="showPasteProblemCheckbox && pasteProblemMode" class="ai-question-generator">
            <div class="card-modern ai-generator-card">
              <div class="card-header-modern"></div>
              <div class="card-body">
                <div class="form-group">
                  <div class="textarea-container">
                    <textarea 
                      v-model="leetcodeProblems" 
                      @input="parseProblems"
                      rows="8" 
                      placeholder="문제 목록을 붙여넣으세요..." 
                      class="form-control"
                    ></textarea>
                    <button title="클립보드에 복사" class="copy-btn" @click="copyToClipboard">
                      <i class="fas fa-copy"></i>
                    </button>
                  </div>
                  <div class="form-text">{{ $t('examManagement.createForm.leetcodeProblemsHelp') }}</div>
                </div>
                
                <!-- 파싱된 문제 목록 표시 -->
                <div v-if="parsedProblems.length > 0" class="parsed-problems">
                  <h6>{{ $t('examManagement.createForm.parsedProblems') }} ({{ parsedProblems.length }})</h6>
                  <div class="problem-list">
                    <div 
                      v-for="(problem, index) in parsedProblems" 
                      :key="index"
                      class="problem-item"
                      :class="{ 'problem-error': problem.error }"
                    >
                      <div class="problem-info">
                        <span class="problem-number">{{ problem.id }}</span>
                        <span class="problem-title">{{ problem.title }}</span>
                        <span class="problem-difficulty" :class="`difficulty-${problem.difficulty}`"> {{ problem.difficulty }} </span>
                        <span class="problem-url">
                          <a :href="problem.url" target="_blank" class="url-link">
                            <i class="fas fa-external-link-alt"></i>
                          </a>
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="generator-actions">
                  <button @click="clearProblems" class="btn btn-secondary">
                    <i class="fas fa-trash me-1"></i> {{ $t('examManagement.createForm.clearProblems') }}
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div class="form-group">
            <label>{{ $t('examDetail.descriptionLabel') }}:</label>
            <textarea 
              v-model="editingDescription" 
              class="form-control" 
              rows="4"
              :placeholder="$t('examDetail.descriptionPlaceholder')"
            ></textarea>
          </div>
          <div class="form-actions">
            <button 
              @click="saveInfo" 
              class="action-btn action-btn-success"
              :disabled="isSaving"
            >
              <i :class="isSaving ? 'fas fa-spinner fa-spin' : 'fas fa-save'"></i>
              <span class="action-label">
                {{ isSaving ? $t('examManagement.createForm.saving') : $t('examDetail.save') }}
              </span>
            </button>
            <button 
              v-if="!isFavoriteMode && exam && exam.file_name && isAuthenticated" 
              @click="importFromConnectedFile" 
              class="action-btn action-btn-info"
              :disabled="isImporting"
            >
              <i class="fas fa-download"></i>
              <span class="action-label">{{ safeTranslate('examDetail.import', '가져오기') }}</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Questions List -->
      <div class="questions-section">


        <!-- Excel Upload Section (즐겨찾기 모드에서는 숨김) -->
        <div class="control-card" v-if="!isFavoriteMode && exam && (isAdmin || isStudyAdmin) && showExcelUpload && (!exam.file_name)">
          <div class="card-header-modern">
            <h3>{{ safeTranslate('examDetail.dataUpload', 'Data Upload') }}</h3>
          </div>
          <div class="control-content">
            <div class="upload-info">
              <h6><i class="fas fa-info-circle"></i>{{ $t('examDetail.excelFormatGuide', '엑셀 형식 가이드') }}</h6>
              <p><strong>{{ $t('examDetail.requiredColumns', '필수 컬럼') }}:</strong> {{ $t('examDetail.questionId') }}, {{ $t('examDetail.title') }}, {{ $t('examDetail.questionContent') }}, {{ $t('examDetail.answer') }}</p>
              <p><strong>{{ $t('examDetail.optionalColumns', '선택 컬럼') }}:</strong> {{ $t('examDetail.description') }}, {{ $t('examDetail.difficulty') }}, {{ $t('examDetail.url') }}, {{ $t('examDetail.groupId') }}</p>
              <p><strong>✅ {{ $t('examDetail.features', '기능') }}:</strong> {{ safeTranslate('examDetail.featuresDescription', '기존 문제 업데이트 + 새로운 문제 추가') }}</p>
              <p><strong>⚠️ {{ $t('examDetail.warnings', '주의사항') }}:</strong> {{ safeTranslate('examDetail.warningsDescription', '그룹ID 컬럼이 있으면 기존 그룹ID를 덮어씁니다') }}</p>
              <p><strong>{{ $t('examDetail.supportedFormats', '지원 형식') }}:</strong> CSV, XLS, XLSX</p>
            </div>
            <div class="upload-form">
              <div class="upload-input">
                <input 
                  type="file" 
                  class="form-control" 
                  @change="handleExcelFileSelect" 
                  accept=".xlsx,.xls,.csv"
                  ref="excelFileInput"
                >
              </div>
              <div class="upload-actions">
                <button 
                  @click="uploadExcelFile" 
                  class="action-btn action-btn-success"
                  :disabled="!selectedExcelFile"
                >
                  <i class="fas fa-upload"></i>
                  <span class="action-label">{{ $t('examDetail.upload') }}</span>
                </button>
                <button 
                  @click="cancelExcelUpload" 
                  class="action-btn action-btn-secondary"
                >
                  <i class="fas fa-times"></i>
                  <span class="action-label">{{ $t('examDetail.cancel') }}</span>
                </button>
              </div>
            </div>
            <div v-if="uploadMessage" class="upload-message" :class="uploadMessageType">
              {{ uploadMessage }}
            </div>
          </div>
        </div>

        <!-- Filter Controls -->
        <div class="filter-card">
          <div class="filter-content">
            <div class="filter-row" :class="{ 'mobile-hidden': !showFilterRow }">
              <div class="filter-group">
                <input
                  v-model="searchTerm"
                  type="text"
                  class="form-control"
                  :placeholder="$t('examDetail.searchPlaceholder')"
                >
              </div>
              <div class="filter-group">
                <select v-model="difficultyFilter" class="form-control">
                  <option value="">{{ $t('examDetail.allDifficulties') }}</option>
                  <option value="Easy">Easy</option>
                  <option value="Medium">Medium</option>
                  <option value="Hard">Hard</option>
                </select>
              </div>
              <div class="filter-group">
                <select v-model="answerFilter" class="form-control">
                  <option value="">{{ $t('examDetail.allAccuracy') }}</option>
                  <option value="high">{{ $t('examDetail.highAccuracy') }}</option>
                  <option value="low">{{ $t('examDetail.lowAccuracy') }}</option>
                </select>
              </div>
              <div class="filter-group">
                <select v-model="favoriteFilter" class="form-control">
                  <option value="">{{ $t('examDetail.allFavorites') }}</option>
                  <option value="favorite">{{ $t('examDetail.favorite') }}</option>
                  <option value="not_favorite">{{ $t('examDetail.notFavorite') }}</option>
                </select>
              </div>
              <div class="filter-group">
                <select v-model="ignoreFilter" class="form-control">
                  <option value="">{{ $t('examDetail.allIgnores') }}</option>
                  <option value="ignored">{{ $t('examDetail.ignored') }}</option>
                  <option value="not_ignored">{{ $t('examDetail.notIgnored') }}</option>
                </select>
              </div>
              <div class="filter-group">
                <input
                  v-model="groupIdFilter"
                  type="text"
                  class="form-control group-id-filter"
                  :placeholder="$t('examDetail.groupIdFilterPlaceholder')"
                  @input="debugGroupIdFilter"
                >
              </div>
              <div class="filter-group" v-if="isFavoriteExam">
                <select v-model="originalExamFilter" class="form-control">
                  <option value="">{{ $t('examDetail.allOriginalExams') }}</option>
                  <option v-for="exam in availableOriginalExams" :key="exam.id" :value="exam.id">
                    {{ getLocalizedTitle(exam) }}
                  </option>
                </select>
              </div>
                    <!-- Tag Filter 제거: 시험 목록에서만 사용 -->
              <button @click="resetFilters" class="action-btn action-btn-secondary reset-filter-btn">
                <i class="fas fa-undo"></i>
                <span class="action-label">{{ $t('examDetail.resetFilters') }}</span>
              </button>
            </div>
            <div class="filter-actions">
              <!-- 문제 수 정보 표시 -->
              <div class="question-count-info" v-if="exam">
                <span class="count-label">{{ safeTranslate('examDetail.totalQuestions', '총 문제 수') }}:</span>
                <span class="count-value">{{ questions.length || 0 }}</span>
                <span class="count-separator">|</span>
                <span class="count-label">{{ safeTranslate('examDetail.seenQuestions', '보이는 문제') }}:</span>
                <span class="count-value">{{ filteredQuestions.length || 0 }}</span>
                <span v-if="selectedQuestions.length > 0" class="count-separator">|</span>
                <span v-if="selectedQuestions.length > 0" class="count-label">{{ safeTranslate('examDetail.selectedQuestions', '선택된 문제') }}:</span>
                <span v-if="selectedQuestions.length > 0" class="count-value selected">{{ selectedQuestions.length }}</span>
              </div>
              
              <!-- 기본 버튼들 -->
              <button @click="toggleFilterRow" class="action-btn action-btn-info mobile-filter-toggle">
                <i class="fas fa-filter"></i>
                <span class="action-label">{{ $t('examDetail.filter') || 'Filter' }}</span>
              </button>
              <button v-if="exam" @click="startExam" class="action-btn action-btn-success">
                <i class="fas fa-play"></i>
                <span class="action-label">{{ $t('examDetail.startExam') }}</span>
              </button>
              <button 
                class="action-btn action-btn-danger" 
                @click="deleteSelectedQuestions" 
                :disabled="selectedQuestions.length === 0"
                v-if="canDeleteQuestions"
              >
                <i class="fas fa-trash"></i>
                <span class="action-label">{{ safeTranslate('examDetail.deleteQuestions', '삭제') }}</span>
              </button>
              
              <!-- Options 버튼 (즐겨찾기 모드 또는 권한이 있는 경우 표시) -->
              <button 
                v-if="isFavoriteMode || isAdmin || isStudyAdmin || isExamCreator"
                @click="openOptionsModal" 
                class="action-btn action-btn-info"
              >
                <i class="fas fa-cog"></i>
                <span class="action-label">{{ $t('examDetail.options') }}</span>
              </button>
              
              <!-- 드롭다운 메뉴 -->
              <div class="dropdown-menu-container">
                <button 
                  class="action-btn action-btn-modern dropdown-toggle" 
                  @click.stop="toggleDropdownMenu"
                  :class="{ 'active': showDropdownMenu }"
                  type="button"
                >
                  <i class="fa-solid fa-ellipsis-vertical"></i>
                </button>
                
                <div v-if="showDropdownMenu" class="dropdown-menu" @click.stop>
                  <button v-if="(isAdmin || isStudyAdmin || isExamCreator) && exam" @click="handleDropdownAction('goToAddQuestion')" class="dropdown-item">
                    <i class="fas fa-plus"></i>
                    <span>{{ $t('examDetail.add') }}</span>
                  </button>
                  <button @click="handleDropdownAction('downloadExcel')" class="dropdown-item" :disabled="!questions.length" v-if="isAuthenticated">
                    <i class="fas fa-download"></i>
                    <span>{{ $t('examDetail.download') }}</span>
                  </button>
                  <button @click="handleDropdownAction('toggleExcelUpload')" class="dropdown-item" v-if="isAdmin || isStudyAdmin && (!exam || !exam.file_name)">
                    <i class="fas fa-upload"></i>
                    <span>{{ $t('examDetail.upload') }}</span>
                  </button>
                  <button @click="handleDropdownAction('addAllToFavorite')" class="dropdown-item" :disabled="selectedQuestions.length === 0">
                    <i class="fas fa-star"></i>
                    <span>{{ $t('examDetail.addAllToFavorite') }}</span>
                  </button>
                  <button @click="handleDropdownAction('ignoreAllQuestions')" class="dropdown-item" :disabled="selectedQuestions.length === 0">
                    <i class="fas fa-ban"></i>
                    <span>{{ $t('examDetail.ignoreAll') }}</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Questions Table -->
        <div class="questions-table">
          <div class="table-header">
            <div class="table-select-all">
              <input 
                type="checkbox" 
                @change="toggleAllQuestions"
                :checked="isAllSelected"
                :indeterminate="isPartiallySelected"
              >
            </div>
            <div class="table-column" @click="setSort('order')">
              {{ $t('examDetail.number') }}
              <i :class="getSortIcon('order')" class="sort-icon"></i>
            </div>
            <div class="table-column" @click="setSort('csv_id')">
              {{ $t('examDetail.id') }}
              <i :class="getSortIcon('csv_id')" class="sort-icon"></i>
            </div>
            <div class="table-column" @click="setSort('title')">
              {{ $t('examDetail.title') }}
              <i :class="getSortIcon('title')" class="sort-icon"></i>
            </div>
            <div class="table-column" @click="setSort('group_id')">
              {{ $t('examDetail.group') }}
              <i :class="getSortIcon('group_id')" class="sort-icon"></i>
            </div>
            <div class="table-column" @click="setSort('difficulty')">
              {{ $t('examDetail.difficulty') }}
              <i :class="getSortIcon('difficulty')" class="sort-icon"></i>
            </div>
            <div class="table-column" @click="setSort('answer')">
              {{ $t('examDetail.correctCount') }}
              <i :class="getSortIcon('answer')" class="sort-icon"></i>
            </div>
            <div class="table-column" @click="setSort('total_attempts')">
              {{ $t('examDetail.attemptCount') }}
              <i :class="getSortIcon('total_attempts')" class="sort-icon"></i>
            </div>
            <div class="table-column" v-if="showMemberMapping">
              {{ $t('examDetail.memberMapping', 'Member Mapping') }}
            </div>
            <div class="table-column" v-if="isFavoriteExam">{{ $t('examDetail.originalExamName') }}</div>
            <div class="table-column">{{ $t('examDetail.status') }}</div>
          </div>
          
          <div class="table-body">
            <!-- 로딩 중 -->
            <div v-if="questionsLoading || (exam && !questionsLoaded)" class="loading-questions">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">{{ $t('examDetail.loadingQuestions') }}</span>
              </div>
              <p class="mt-3">{{ $t('examDetail.loadingQuestionsText') }}</p>
            </div>
            
            <!-- 문제 없음 (로딩이 완료되고 문제가 없을 때만 표시) -->
            <div v-else-if="!questionsLoading && questionsLoaded && filteredQuestions.length === 0" class="no-questions">
              <i class="fas fa-search"></i>
              <p>{{ $t('examDetail.noQuestionsFound') }}</p>
              <small>{{ $t('examDetail.adjustFilters') }}</small>
            </div>
            
            <div v-for="(question, index) in filteredQuestions" :key="question.id" 
                 class="table-row" :class="{ 'selected': isQuestionSelected(question.id) }">
              <div class="table-cell">
                <input 
                  type="checkbox" 
                  :value="question.id"
                  v-model="selectedQuestions"
                  @click="(e) => handleCheckboxClick(e, index, question.id)"
                >
              </div>
              <div class="table-cell">{{ index + 1 }}</div>
              <div class="table-cell">{{ question.csv_id }}</div>
              <div class="table-cell">
                <router-link :to="getSingleQuestionUrl(question)" class="question-link">
                  <strong>{{ question.localized_title || question.title }}</strong>
                </router-link>
              </div>
              <div class="table-cell">
                <span v-if="question.group_id" class="group-id" :title="question.group_id">{{ question.group_id }}</span>
                <span v-else class="no-group">-</span>
              </div>
              <div class="table-cell">
                <span class="difficulty-badge" :class="getDifficultyBadgeClass(question.difficulty)">
                  {{ question.difficulty }}
                </span>
              </div>
              <div class="table-cell">
                <span v-if="getQuestionStatistics(question.id)" class="correct-count">
                  {{ getQuestionStatistics(question.id).correct_attempts }}
                </span>
                <span v-else class="no-stats">0</span>
              </div>
              <div class="table-cell">
                <span v-if="getQuestionStatistics(question.id)" class="attempt-count">
                  {{ getQuestionStatistics(question.id).total_attempts }}
                </span>
                <span v-else class="no-stats">0</span>
              </div>
              <div class="table-cell" v-if="showMemberMapping">
                <div class="member-mapping-info">
                  <div v-for="mapping in getQuestionMemberMappings(question.id)" :key="mapping.id" class="member-mapping">
                    <span class="member-name">{{ mapping.member.name || mapping.member.user_username }}</span>
                  </div>
                  <div v-if="getQuestionMemberMappings(question.id).length === 0" class="no-mapping">
                    -
                  </div>
                </div>
              </div>
              <div class="table-cell" v-if="isFavoriteExam">
                <div v-for="originalExam in question.original_exams" :key="originalExam.id" class="original-exam">
                  <router-link :to="`/exam-detail/${originalExam.id}`" class="exam-link">
                    {{ getLocalizedTitle(originalExam) }}
                  </router-link>
                </div>
              </div>
              <div class="table-cell">
                <div class="status-badges">
                  <!-- 즐겨찾기 모드가 아닐 때만 토글 버튼 표시 -->
                  <template v-if="!isFavoriteMode">
                    <!-- 즐겨찾기 토글 버튼 (상태가 있을 때만) -->
                    <button 
                      v-if="isQuestionFavorite(question.id)"
                      @click="toggleFavorite(question.id)" 
                      class="status-badge status-favorite-toggle status-favorite"
                      title="즐겨찾기 해제"
                    >
                      <i class="fas fa-star"></i>{{ $t('examDetail.favorite') }}
                    </button>
                    
                    <!-- 무시하기 토글 버튼 (상태가 있을 때만) -->
                    <button 
                      v-if="isQuestionIgnored(question.id)"
                      @click="toggleIgnore(question.id)" 
                      class="status-badge status-ignore-toggle status-ignored"
                      title="무시 해제"
                    >
                      <i class="fas fa-ban"></i>{{ $t('examDetail.ignored') }}
                    </button>
                  </template>
                  
                  <!-- 즐겨찾기 모드일 때는 상태만 표시 -->
                  <template v-else>
                    <span v-if="isQuestionFavorite(question.id)" class="status-badge status-favorite">
                      <i class="fas fa-star"></i>{{ $t('examDetail.favorite') }}
                    </span>
                    <span v-if="isQuestionIgnored(question.id)" class="status-badge status-ignored">
                      <i class="fas fa-ban"></i>{{ $t('examDetail.ignored') }}
                    </span>
                  </template>
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
import axios from 'axios'
import * as XLSX from 'xlsx'
import { saveAs } from 'file-saver'
import { debugLog, debugLifecycle, debugApi, debugObject, forceDebugLog } from '@/utils/debugUtils'
import { formatTextWithLinks } from '@/utils/textUtils'
import { isAdmin, getCurrentUser, getCurrentUser as getCurrentUserFromPermissions, hasStudyAdminRole, canEditExam } from '@/utils/permissionUtils'
import { parseLeetCodeProblems, convertToQuestionData } from '@/utils/problemParser'
import { loadMandatoryRules, loadInterviewPromptTemplate, buildInterviewPrompt } from '@/utils/voiceInterviewUtils'
import { getLocalizedContentWithI18n } from '@/utils/multilingualUtils'
import authService from '@/services/authService'

// axios 인터셉터를 통한 전역 캐시 무효화
axios.interceptors.request.use(config => {
  // 캐시 무효화가 필요한 경우
  if (config.params && (config.params._refresh || config.params._nocache)) {
    config.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    config.headers['Pragma'] = 'no-cache'
  }
  
  return config
})

export default {
  name: 'ExamDetail',
  
  components: {
    'EntityTagManager': () => import('@/components/EntityTagManager.vue'),
    'ShareModal': () => import('@/components/ShareModal.vue'),
    'MobileVoiceInterview': () => import('@/components/MobileVoiceInterview.vue')
  },
  
  props: {
    favoriteMode: {
      type: Boolean,
      default: false
    },
    examId: {
      type: String,
      default: null
    }
  },


  data() {
    return {
      exam: null,
      questions: [],
      searchTerm: this.getStoredFilter('searchTerm', ''),
      difficultyFilter: this.getStoredFilter('difficultyFilter', ''),
      sortBy: this.getStoredFilter('sortBy', 'priority'),
      sortOrder: this.getStoredFilter('sortOrder', 'asc'),
      selectedQuestions: [],
      customExamTitle: '', // 사용자 정의 시험 제목
      lastCheckedIndex: null,
      studies: [], // 스터디 목록
      studyMembers: [], // 선택된 스터디의 멤버 목록
      selectedStudyId: '', // 선택된 스터디 ID
      mappings: [], // 매핑 목록
      
      editingDescription: '',
      editingTitle: '',
      // 추가
      isEditingInfo: false,
      showExamInfo: false, // Exam Information 영역 표시 여부 (기본값: 숨김)
      editingVersion: 1,
      editingCreatedAt: '',
              editingIsPublic: false,
        editingForceAnswer: false,
      editingVoiceModeEnabled: false,
      editingAIMockInterview: false,
      editingAgeRating: '17+', // 연령 등급
      editingExamDifficulty: 5, // 시험 난이도 (1~10)
      editingSupportedLanguages: '', // admin일 때 supported_languages 수정용
      // 번역 모달 관련
      showTranslateModal: false,
      selectedLanguages: [],
      randomOption: 'most_wrong',
      // 모바일 Voice Interview 관련
      isMobileDevice: false,
      showVoiceInterview: false,
      latestResult: null,
      resultDetails: [],
      answerFilter: this.getStoredFilter('answerFilter', ''),
      favoriteFilter: this.getStoredFilter('favoriteFilter', ''),
      ignoreFilter: this.getStoredFilter('ignoreFilter', 'not_ignored'),
      questionStatistics: [], // 문제별 정답 통계
      memberMappings: [], // Member-Question Mapping 데이터
      // 문제 이동 관련
      availableExams: [], // 이동 가능한 시험 목록
      selectedTargetExamId: '', // 선택된 타겟 시험 ID
      // 그룹 ID 입력
      groupIdInput: '',
      groupIdFilter: this.getStoredFilter('groupIdFilter', ''), // 그룹 필터 (시험별로 관리)
      // 원본 시험 필터
      originalExamFilter: this.getStoredFilter('originalExamFilter', ''),
      // 필터 행 표시 여부 (모바일에서 기본 숨김)
      showFilterRow: false,
      // 엑셀 업로드 관련
      showExcelUpload: false,
      selectedExcelFile: null,
      uploadMessage: '',
      uploadMessageType: 'alert-info',
      // 연결된 파일 가져오기 관련
      isImporting: false,
        // 문제 붙여넣기 관련
        showPasteProblemCheckbox: false, // 문제 붙여넣기 체크박스 표시 여부
        pasteProblemMode: false, // 문제 붙여넣기 모드 활성화 여부
        parsedProblems: [], // 파싱된 문제 목록
        leetcodeProblems: '146. LRU Cache\nMed.\n\n1. Two Sum\nEasy', // LeetCode 문제 목록 텍스트
        isSaving: false, // 저장 중 상태
          // 번역 로딩 상태
      // AI 모의 인터뷰 관련
      showAIMockInterviewModal: false,
      selectedQuestionForAI: null,
      interviewPromptText: '',
      isInitializingPrompt: false, // initializePromptText 실행 중 플래그
      translationsLoaded: false,
      // 문제 목록 로딩 상태
      questionsLoading: true, // 초기 로딩 상태로 설정
      // favorite과 무시 관련 상태
      favoriteQuestions: new Set(),
      ignoredQuestions: new Set(),
      // 연결된 프로젝트 관련
      connectedStudies: [],
      toastMessageQueue: [], // 토스트 메시지 큐
      isShowingToast: false, // 현재 토스트 메시지를 표시 중인지 여부
      showProjectSelector: false,
      
      // Notification 관련 데이터
      showToast: false,
      toastMessage: '',
      toastType: 'success',
      toastIcon: 'fas fa-check-circle',
      showModal: false,
      modalTitle: '',
      modalMessage: '',
      modalType: 'info',

      modalCallback: null,
      showDropdownMenu: false,
      showAdminDropdownMenu: false,
      showOptionsModal: false,
      shouldReopenOptionsModal: false,
      
      // 정확도 조정 관련
      accuracyAdjustmentPercentage: 0,
      
      // 즐겨찾기 모드 관련
      isFavoriteMode: false,
      favoriteModeTitle: '',
      
      // 무한 루프 방지를 위한 수동 계산 값들
      examTotalQuestions: 0,
      latestScorePercentage: 0,
      
      // 사용자 프로필 언어 (캐시)
      userProfileLanguage: null,
      
      // Voice Interview 결과 개수
      voiceInterviewResultsCount: 0,
      
      // 공유 모달 관련
      showShareModal: false,
      shareUrl: '',
    }
  },
  computed: {
    hasVoiceInterviewResults() {
      return this.voiceInterviewResultsCount > 0
    },
    // 선택된 문제 수 (자동 계산)
    selectedQuestionCount() {
      return this.selectedQuestions.length > 0 ? this.selectedQuestions.length : 10;
    },
    
    // 현재 사용자 언어
    currentLanguage() {
      return this.$i18n.locale || 'en';
    },
    // 공유 버튼 표시 여부 (17+ 등급만 표시)
    showShareButton() {
      // 세션이 없을 때는 기본적으로 표시
      if (!this.isAuthenticated) {
        return true
      }
      // 세션이 있을 때 17+ 미만이면 숨김
      const user = authService.getUserSync()
      if (user && user.age_rating) {
        return user.age_rating === '17+'
      }
      // age_rating이 없으면 기본적으로 표시 (기존 사용자 호환성)
      return true
    },
    // 사용자의 연령 등급 이하만 선택 가능한 등급 목록
    availableAgeRatings() {
      const allRatings = ['4+', '9+', '12+', '17+']
      const user = authService.getUserSync()
      
      // 로그인하지 않았거나 age_rating이 없으면 모든 등급 선택 가능
      if (!user || !user.age_rating) {
        return allRatings
      }
      
      const userRating = user.age_rating
      const ratingOrder = { '4+': 1, '9+': 2, '12+': 3, '17+': 4 }
      const userRatingOrder = ratingOrder[userRating] || 4
      
      // 사용자 등급 이하만 반환
      return allRatings.filter(rating => {
        const ratingOrderValue = ratingOrder[rating] || 4
        return ratingOrderValue <= userRatingOrder
      })
    },
    // 사용자의 최대 연령 등급
    maxUserAgeRating() {
      const user = authService.getUserSync()
      return user && user.age_rating ? user.age_rating : null
    },
    
    // 현재 시험의 다국어 제목 (반응형)
    localizedExamTitle() {
      if (!this.exam) return '';
      
      // 즐겨찾기 모드에서 display_title이 있으면 우선 사용
      if (this.isFavoriteMode && this.exam.display_title) {
        return this.exam.display_title;
      }
      
      // 사용자 프로필 언어 가져오기 (동기적으로, 캐시 우선)
      let userLang = this.userProfileLanguage
      
      // userProfileLanguage가 없으면 동적으로 가져오기 (동기적으로는 불가능하므로 기본값 사용)
      if (!userLang) {
        console.warn('[ExamDetail] userProfileLanguage가 null입니다. 기본값 "en" 사용')
        userLang = 'en'
      }
      
      // display_title 사용 (백엔드에서 올바르게 처리된 경우)
      if (this.exam.display_title && this.exam.display_title.trim()) {
        forceDebugLog(`✅ [ExamDetail] localizedExamTitle - display_title 사용: "${this.exam.display_title}"`)
        return this.exam.display_title
      }
      
      // display_title도 없으면 폴백 로직 사용
      return getLocalizedContentWithI18n(this.exam, 'title', this.$i18n, this.userProfileLanguage, '') || this.exam.title || ''
    },
    
    // 현재 시험의 다국어 설명 (반응형)
    localizedExamDescription() {
      if (!this.exam) return '';
      
      // 사용자 프로필 언어 가져오기 (동기적으로, 캐시 우선)
      let userLang = this.userProfileLanguage
      
      // userProfileLanguage가 없으면 동적으로 가져오기 (동기적으로는 불가능하므로 기본값 사용)
      if (!userLang) {
        console.warn('[ExamDetail] userProfileLanguage가 null입니다. 기본값 "en" 사용')
        userLang = 'en'
      }
      
      // 사용자 언어에 맞는 언어별 필드가 있으면 우선 사용
      // 백엔드 display_description이 예상과 다를 경우를 대비한 방어적 로직
      if (userLang === 'zh' && this.exam.description_zh && this.exam.description_zh.trim()) {
        // display_description이 description_zh와 다르면 description_zh 사용 (백엔드 버그 우회)
        if (!this.exam.display_description || this.exam.display_description !== this.exam.description_zh) {
          forceDebugLog(`⚠️ [ExamDetail] localizedExamDescription - display_description("${this.exam.display_description}")과 description_zh("${this.exam.description_zh}") 불일치, description_zh 사용`)
          return this.exam.description_zh
        }
      } else if (userLang === 'ko' && this.exam.description_ko && this.exam.description_ko.trim()) {
        if (!this.exam.display_description || this.exam.display_description !== this.exam.description_ko) {
          forceDebugLog(`⚠️ [ExamDetail] localizedExamDescription - display_description("${this.exam.display_description}")과 description_ko("${this.exam.description_ko}") 불일치, description_ko 사용`)
          return this.exam.description_ko
        }
      } else if (userLang === 'es' && this.exam.description_es && this.exam.description_es.trim()) {
        if (!this.exam.display_description || this.exam.display_description !== this.exam.description_es) {
          forceDebugLog(`⚠️ [ExamDetail] localizedExamDescription - display_description("${this.exam.display_description}")과 description_es("${this.exam.description_es}") 불일치, description_es 사용`)
          return this.exam.description_es
        }
      } else if (userLang === 'ja' && this.exam.description_ja && this.exam.description_ja.trim()) {
        if (!this.exam.display_description || this.exam.display_description !== this.exam.description_ja) {
          forceDebugLog(`⚠️ [ExamDetail] localizedExamDescription - display_description("${this.exam.display_description}")과 description_ja("${this.exam.description_ja}") 불일치, description_ja 사용`)
          return this.exam.description_ja
        }
      } else if (userLang === 'en' && this.exam.description_en && this.exam.description_en.trim()) {
        if (!this.exam.display_description || this.exam.display_description !== this.exam.description_en) {
          forceDebugLog(`⚠️ [ExamDetail] localizedExamDescription - display_description("${this.exam.display_description}")과 description_en("${this.exam.description_en}") 불일치, description_en 사용`)
          return this.exam.description_en
        }
      }
      
      // display_description 사용 (백엔드에서 올바르게 처리된 경우)
      if (this.exam.display_description && this.exam.display_description.trim()) {
        forceDebugLog(`✅ [ExamDetail] localizedExamDescription - display_description 사용: "${this.exam.display_description}"`)
        return this.exam.display_description
      }
      
      // display_description도 없으면 폴백 로직 사용
      const currentLang = this.currentLanguage;
      if (currentLang === 'ko') {
        return this.exam.description_ko || this.exam.description_en || this.exam.description_zh || this.exam.description_es || this.exam.description_ja || this.exam.description || '';
      } else if (currentLang === 'zh') {
        return this.exam.description_zh || this.exam.description_en || this.exam.description_ko || this.exam.description_es || this.exam.description_ja || this.exam.description || '';
      } else if (currentLang === 'es') {
        return this.exam.description_es || this.exam.description_en || this.exam.description_ko || this.exam.description_zh || this.exam.description_ja || this.exam.description || '';
      } else if (currentLang === 'ja') {
        return this.exam.description_ja || this.exam.description_en || this.exam.description_ko || this.exam.description_es || this.exam.description_zh || this.exam.description || '';
      } else {
        return this.exam.description_en || this.exam.description_zh || this.exam.description_ko || this.exam.description_es || this.exam.description_ja || this.exam.description || '';
      }
    },
    
    // 스터디 제목을 다국어로 처리
    localizedStudyTitle() {
      return (study) => {
        if (!study) return '';
        
        return getLocalizedContentWithI18n(
          study,
          'title',
          this.$i18n,
          this.userProfileLanguage,
          ''
        )
      };
    },
    
    // 문제 내용을 다국어로 처리
    localizedContent() {
      return (question) => {
        if (!question) return '';
        
        return getLocalizedContentWithI18n(
          question,
          'content',
          this.$i18n,
          this.userProfileLanguage,
          ''
        )
      };
    },
    
    // 문제 답안을 다국어로 처리
    localizedAnswer() {
      return (question) => {
        if (!question) return '';
        
        return getLocalizedContentWithI18n(
          question,
          'answer',
          this.$i18n,
          this.userProfileLanguage,
          ''
        )
      };
    },
    
    // 문제 설명을 다국어로 처리
    localizedExplanation() {
      return (question) => {
        if (!question) return '';
        
        return getLocalizedContentWithI18n(
          question,
          'explanation',
          this.$i18n,
          this.userProfileLanguage,
          ''
        )
      };
    },
    
    modalIcon() {
      switch (this.modalType) {
        case 'success':
          return 'fas fa-check-circle text-success'
        case 'error':
          return 'fas fa-exclamation-circle text-danger'
        case 'warning':
          return 'fas fa-exclamation-triangle text-warning'
        case 'info':
          return 'fas fa-info-circle text-info'
        default:
          return 'fas fa-info-circle text-info'
      }
    },

    modalConfirmButtonClass() {
      switch (this.modalType) {
        case 'success':
          return 'btn-success'
        case 'error':
          return 'btn-danger'
        case 'warning':
          return 'btn-warning'
        case 'info':
          return 'btn-info'
        default:
          return 'btn-primary'
      }
    },
    modalConfirmText() {
      return this.safeTranslate('modal.confirm', '확인')
    },
    modalCancelText() {
      return this.safeTranslate('modal.cancel', '취소')
    },
    isCurrentUserDailyExam() {
      if (!this.isAuthenticated || !this.exam || !this.currentUser) {
        return false
      }
      
      // 현재 시험이 현재 사용자의 Daily Exam인지 확인
      const expectedTitle = `Today's Quizzes for ${this.currentUser.username}`
      return this.getLocalizedTitle(this.exam) === expectedTitle
    },
    isAllSelected() {
      return this.filteredQuestions.length > 0 && this.selectedQuestions.length === this.filteredQuestions.length
    },
    isPartiallySelected() {
      return this.selectedQuestions.length > 0 && this.selectedQuestions.length < this.filteredQuestions.length
    },
    filteredQuestions() {
      let filtered = this.questions || []

      // filtered가 배열이 아닌 경우 빈 배열로 초기화
      if (!Array.isArray(filtered)) {
        filtered = []
      }

      // 검색 필터
      if (this.searchTerm) {
        const searchLower = this.searchTerm.toLowerCase()
        filtered = filtered.filter(q =>
          q.localized_title.toLowerCase().includes(searchLower)
        )
      }

      // 난이도 필터
      if (this.difficultyFilter) {
        filtered = filtered.filter(q => {
          if (!q.difficulty) return false
          
          // 난이도 값 정규화
          const normalizeDifficulty = (diff) => {
            if (!diff) return ''
            const normalized = diff.toLowerCase().trim()
            if (normalized === 'med' || normalized === 'medium' || normalized === 'med.') return 'medium'
            if (normalized === 'easy') return 'easy'
            if (normalized === 'hard') return 'hard'
            return normalized
          }
          
          const questionDiff = normalizeDifficulty(q.difficulty)
          const filterDiff = normalizeDifficulty(this.difficultyFilter)
          
          return questionDiff === filterDiff
        })
      }

      // 정답률 필터
      if (this.answerFilter) {
        filtered = filtered.filter(q => {
          const stats = this.getQuestionStatistics(q.id)

          if (!stats || stats.total_attempts === 0) {
            // 시험 기록이 없으면 모든 필터에서 제외
            return false
          }

          const accuracy = stats.correct_attempts / stats.total_attempts

          if (this.answerFilter === 'high') return accuracy >= 0.7 // 70% 이상
          if (this.answerFilter === 'low') return accuracy < 0.7 // 70% 미만
          return true
        })
      }

      // favorite 필터
      if (this.favoriteFilter) {
        filtered = filtered.filter(q => {
          const isFavorite = this.isQuestionFavorite(q.id)
          if (this.favoriteFilter === 'favorite') return isFavorite
          if (this.favoriteFilter === 'not_favorite') return !isFavorite
          return true
        })
      }

      // 무시 필터
      if (this.ignoreFilter) {
        filtered = filtered.filter(q => {
          const isIgnored = this.isQuestionIgnored(q.id)
          if (this.ignoreFilter === 'ignored') return isIgnored
          if (this.ignoreFilter === 'not_ignored') return !isIgnored
          return true
        })
      }

      // 그룹 필터
      if (this.groupIdFilter) {
        const groupLower = this.groupIdFilter.toLowerCase()
        filtered = filtered.filter(q => (q.group_id || '').toLowerCase().includes(groupLower))
      }

              // 원본 시험 필터 (favorite 시험에서만)
      if (this.isFavoriteExam && this.originalExamFilter) {
        filtered = filtered.filter(q => {
          if (!q.original_exams) return false
          return q.original_exams.some(exam => exam.id === this.originalExamFilter)
        })
      }

      // 모든 문제의 통계가 없거나 시도횟수가 0이면 group_id 오름차순 정렬 (사용자 정렬이 설정되지 않은 경우에만)
      const allNoStats = filtered.every(q => {
        const stats = this.getQuestionStatistics(q.id)
        return !stats || !stats.total_attempts || stats.total_attempts === 0
      })
      
      // 사용자가 정렬을 설정한 경우에는 기본 정렬을 건너뛰고 사용자 정렬 적용
      if (allNoStats && this.sortBy === 'priority') {
        filtered.sort((a, b) => {
          // group_id가 숫자라면 숫자형으로 정렬, 아니면 문자로 정렬
          const parseGroup = v => {
            if (v === undefined || v === null || v === '') return Number.NEGATIVE_INFINITY;
            const n = Number(v);
            return isNaN(n) ? v : n;
          };
          const aGroup = parseGroup(a.group_id);
          const bGroup = parseGroup(b.group_id);
          if (typeof aGroup === 'number' && typeof bGroup === 'number') return aGroup - bGroup;
          if (typeof aGroup === 'number') return -1;
          if (typeof bGroup === 'number') return 1;
          if (aGroup < bGroup) return -1;
          if (aGroup > bGroup) return 1;
          return 0;
        })
        return filtered
      }

      // 정렬
      filtered.sort((a, b) => {
        let aValue, bValue

        switch (this.sortBy) {
          case 'priority': {
            // 우선순위 정렬 (정확도가 낮은 것 먼저, 그 다음 시도가 0인 것)
            const aStats = this.getQuestionStatistics(a.id)
            const bStats = this.getQuestionStatistics(b.id)

            const aAttempts = aStats ? aStats.total_attempts : 0
            const bAttempts = bStats ? bStats.total_attempts : 0
            const aCorrect = aStats ? aStats.correct_attempts : 0
            const bCorrect = bStats ? bStats.correct_attempts : 0

            // 1. 정확도가 낮은 것 먼저 (예: 0/2 -> 0/1 -> 1/3)
            const aAccuracy = aAttempts > 0 ? aCorrect / aAttempts : 0
            const bAccuracy = bAttempts > 0 ? bCorrect / bAttempts : 0
            
            if (aAccuracy !== bAccuracy) {
              return aAccuracy - bAccuracy
            }

            // 2. 정확도가 같은 경우 시도 횟수가 많은 것을 우선 (0/2가 0/1보다 먼저)
            if (aAttempts !== bAttempts) {
              return bAttempts - aAttempts  // 내림차순 (많은 것이 먼저)
            }

            // 3. 시도 횟수도 같은 경우 시도가 0인 것을 우선
            if (aAttempts === 0 && bAttempts > 0) return -1
            if (aAttempts > 0 && bAttempts === 0) return 1

            // 모든 조건이 같은 경우 원래 순서 유지
            return 0
          }

          case 'title':
            aValue = a.localized_title || a.title || ''
            bValue = b.localized_title || b.title || ''
            break
          case 'difficulty': {
            // 난이도 정규화 함수
            const normalizeDifficulty = (diff) => {
              if (!diff) return ''
              const normalized = diff.toLowerCase().trim()
              if (normalized === 'med' || normalized === 'medium' || normalized === 'med.') return 'medium'
              if (normalized === 'easy') return 'easy'
              if (normalized === 'hard') return 'hard'
              return normalized
            }
            aValue = normalizeDifficulty(a.difficulty)
            bValue = normalizeDifficulty(b.difficulty)
            break
          }
          case 'csv_id':
            aValue = a.csv_id
            bValue = b.csv_id
            break
          case 'group_id':
            aValue = a.group_id || ''
            bValue = b.group_id || ''
            break
          case 'member':
            aValue = this.getMappedMember(a.id)?.name || ''
            bValue = this.getMappedMember(b.id)?.name || ''
            break
          case 'answer': {
            const aStats = this.getQuestionStatistics(a.id)
            const bStats = this.getQuestionStatistics(b.id)
            // 정답률 기준으로 정렬 (높은 순)
            aValue = aStats && aStats.total_attempts > 0 ? aStats.correct_attempts / aStats.total_attempts : 0
            bValue = bStats && bStats.total_attempts > 0 ? bStats.correct_attempts / bStats.total_attempts : 0
            break
          }
          case 'total_attempts': {
            const aStats = this.getQuestionStatistics(a.id)
            const bStats = this.getQuestionStatistics(b.id)
            aValue = aStats ? aStats.total_attempts : 0
            bValue = bStats ? bStats.total_attempts : 0
            break
          }
          case 'order':
          default:
            // order는 문제의 순서를 나타내므로 csv_id 또는 id를 사용
            aValue = a.csv_id || a.id || 0
            bValue = b.csv_id || b.id || 0
            break
        }

        if (this.sortOrder === 'desc') {
          [aValue, bValue] = [bValue, aValue]
        }

        if (aValue < bValue) return -1
        if (aValue > bValue) return 1
        return 0
      })

      return filtered
    },
    validStudies() {
      return Array.isArray(this.studies) ? this.studies.filter(study => study && study.id) : []
    },
    maxQuestions() {
      if (this.newExam.file_name) {
        const file = this.questionFiles.find(f => f.name === this.newExam.file_name)
        return file ? file.max_questions : 0
      }
      return 0
    },
    examTotalCorrect() {
      if (this.exam && this.exam.id) {
        // 전체 맞춘 횟수: resultDetails에서 is_correct=true인 개수
        if (this.resultDetails && this.resultDetails.length > 0) {
          const totalCorrect = this.resultDetails.filter(detail => detail.is_correct === true).length;
          return totalCorrect;
        }
        
        // questionStatistics가 비어있거나 모든 시도가 0이면 0 반환
        if (this.questionStatistics && Array.isArray(this.questionStatistics) && this.questionStatistics.length > 0) {
          const totalCorrectAttempts = this.questionStatistics.reduce((sum, stat) => sum + (stat.correct_attempts || 0), 0);
          return totalCorrectAttempts;
        }
        
        // fallback: exam.user_correct_questions 사용
        const result = this.exam.user_correct_questions || 0;
        return result;
      }
      return undefined;
    },
    // examTotalQuestions를 computed에서 data로 변경 (무한 루프 방지)
    // examTotalQuestions() {
    //   debugLog('=== examTotalQuestions 계산 시작 ===');
    //   debugLog('exam:', this.exam);
    //   debugLog('exam.total_questions:', this.exam ? this.exam.total_questions : 'exam null');
    //   debugLog('questions.length:', this.questions ? this.questions.length : 'questions null');
    //   debugLog('resultDetails:', this.resultDetails);
    //   debugLog('questionStatistics:', this.questionStatistics);
    //   
    //   if (this.exam && this.exam.id) {
    //     // 전체 시도 횟수: resultDetails의 총 개수
    //     if (this.resultDetails && this.resultDetails.length > 0) {
    //       const totalAttempts = this.resultDetails.length;
    //       debugLog('examTotalQuestions - 전체 시도 횟수 (resultDetails 기반):', totalAttempts);
    //       return totalAttempts;
    //     }
    //     
    //     // questionStatistics 기반 총 시도 횟수 계산
    //     if (this.questionStatistics && this.questionStatistics.length > 0) {
    //       const totalAttempts = this.questionStatistics.reduce((sum, stat) => sum + (stat.total_attempts || 0), 0);
    //       debugLog('examTotalQuestions - questionStatistics 기반 총 시도 횟수:', totalAttempts);
    //       return totalAttempts;
    //     }
    //     
    //     // fallback: 전체 문제 수 사용
    //     if (this.questions && this.questions.length > 0) {
    //       const result = this.questions.length;
    //       debugLog('examTotalQuestions - 전체 문제 수 (questions.length):', result);
    //       return result;
    //     }
    //     
    //     // fallback: exam.total_questions 사용
    //     const result = this.exam.total_questions;
    //       debugLog('examTotalQuestions - exam.total_questions 사용:', result);
    //       return result;
    //     }
    //   return undefined;
    // },
    // latestScorePercentage를 computed에서 data로 변경 (무한 루프 방지)
    // latestScorePercentage() {
    //   debugLog('=== latestScorePercentage 계산 시작 ===');
    //   debugLog('examTotalCorrect:', this.examTotalCorrect);
    //   debugLog('examTotalQuestions:', this.examTotalQuestions);
    //   debugLog('latestResult:', this.latestResult);
    //   
    //   // 누적 정답률: 전체 문제 중 맞춘 문제의 비율
    //   if (this.examTotalCorrect !== undefined && this.examTotalQuestions !== undefined && this.examTotalQuestions > 0) {
    //     const percentage = (this.examTotalCorrect / this.examTotalQuestions) * 100;
    //       debugLog('latestScorePercentage - 누적 정답률 계산:', percentage);
    //       return percentage.toFixed(1);
    //     }
    //     
    //     debugLog('latestScorePercentage undefined 반환');
    //     return undefined;
    //   },
    isAdmin() {
      return isAdmin()
    },
    isStudyAdmin() {
      // 시험과 관련된 스터디에서 관리자 권한 확인
      if (!this.exam) return false
      
      const user = getCurrentUser()
      if (!user) return false
      
      // 백엔드에서 제공하는 리소스별 권한 정보 우선 사용
      if (this.exam.user_permissions) {
        return this.exam.user_permissions.is_admin ||
               this.exam.user_permissions.has_study_admin_role ||
               this.exam.user_permissions.is_study_admin
      }

      // 전역 스터디 관리자 권한 확인
      if (hasStudyAdminRole()) {
        return true
      }
      
      // 시험과 연결된 스터디에서 관리자 권한 확인
      if (this.exam.studies && Array.isArray(this.exam.studies)) {
        return this.exam.studies.some(study => {
          if (!study.members) return false
          
          return study.members.some(member => {
            if (!member.user) return false
            
            const memberUserId = typeof member.user === 'object' ? member.user.id : member.user
            return memberUserId === user.id && 
                   (member.role === 'study_admin' || member.role === 'study_leader') &&
                   member.is_active === true
          })
        })
      }
      
      return false
    },
    currentUser() {
      return getCurrentUser()
    },

    isExamCreator() {
      if (!this.exam || !this.currentUser) {
        return false
      }
      
      // 시험의 생성자가 현재 사용자인지 확인
      return this.exam.created_by && this.exam.created_by.id === this.currentUser.id
    },
    canDeleteQuestions() {
      // 시험 편집 권한이 있으면 문제 삭제 권한도 있음
      const canDelete = canEditExam(this.exam)
      
      // 디버깅: 권한 확인 로그 (개발 환경에서만)
      if (process.env.NODE_ENV === 'development') {
        debugLog('=== 삭제 권한 확인 ===')
        debugLog('exam:', this.exam)
        debugLog('exam.user_permissions:', this.exam?.user_permissions)
        debugLog('exam.created_by:', this.exam?.created_by)
        debugLog('currentUser:', this.currentUser)
        debugLog('isAdmin:', this.isAdmin)
        debugLog('isStudyAdmin:', this.isStudyAdmin)
        debugLog('isExamCreator:', this.isExamCreator)
        debugLog('canDeleteQuestions:', canDelete)
        debugLog('===================')
      }
      
      return canDelete
    },
    isFavoriteExam() {
      return this.exam && this.getLocalizedTitle(this.exam) && this.getLocalizedTitle(this.exam).includes("'s favorite")
    },
    availableOriginalExams() {
      if (!this.isFavoriteExam) return []
      
      // 모든 문제의 원본 시험을 수집
      const originalExams = new Map()
      
      this.questions.forEach(question => {
        if (question.original_exams) {
          question.original_exams.forEach(exam => {
            if (!originalExams.has(exam.id)) {
              originalExams.set(exam.id, exam)
            }
          })
        }
      })
      
      return Array.from(originalExams.values()).sort((a, b) => {
        const aTitle = getLocalizedContentWithI18n(a, 'title', this.$i18n, this.userProfileLanguage, '') || a.title || '';
        const bTitle = getLocalizedContentWithI18n(b, 'title', this.$i18n, this.userProfileLanguage, '') || b.title || '';
        return aTitle.localeCompare(bTitle);
      })
    },
    isAuthenticated() {
      return Boolean(getCurrentUser())
    },
    isDevelopment() {
      return window.location.hostname === 'localhost' || 
             window.location.hostname === '127.0.0.1' ||
             window.location.hostname.includes('localhost') ||
             window.location.hostname.includes('leetcode')
    },
    showMemberMapping() {
      // 관리자, 스터디 관리자, 시험 생성자에게만 표시하고, 멤버 매핑 데이터가 있을 때만 표시
      const hasPermission = this.isAdmin || this.isStudyAdmin || this.isExamCreator
      const hasMappingData = this.memberMappings && this.memberMappings.length > 0
      return hasPermission && hasMappingData
    },
    // 번역 가능한 언어 목록 (원본 언어만 제외)
    availableLanguages() {
      if (!this.exam) return []
      const createdLang = this.exam.created_language || 'en'
      const allLanguages = [
        { code: 'en', name: 'English' },
        { code: 'ko', name: '한국어' },
        { code: 'es', name: 'Español' },
        { code: 'zh', name: '中文' },
        { code: 'ja', name: '日本語' }
      ]
      return allLanguages.filter(lang => 
        lang.code !== createdLang
      )
    }
  },
  created() {
    debugLifecycle('ExamDetail', 'created')
  },
  methods: {
    // 태그 필터 관련 메서드 제거 (시험 목록에서만 사용)
    
    // 태그 관리 관련 메서드들
    handleTagsUpdated(updatedTags) {
      console.log('🔄 ExamDetail handleTagsUpdated 호출됨')
      console.log('📊 업데이트된 태그들:', updatedTags)
      // exam 객체의 tags 업데이트
      if (this.exam) {
        this.exam.tags = updatedTags
      }
    },
    
    handleTagSuccess(message) {
      console.log('✅ ExamDetail handleTagSuccess:', message)
      this.showToastNotification(message, 'success')
    },
    
    handleTagError(error) {
      console.error('❌ ExamDetail handleTagError:', error)
      this.showToastNotification('태그 관리 중 오류가 발생했습니다.', 'error')
    },
    
    // 문제 붙여넣기 관련 메서드들
    onPasteProblemChange() {
      if (!this.pasteProblemMode) {
        // 문제 붙여넣기 모드 비활성화 시 데이터 초기화
        this.parsedProblems = []
        this.leetcodeProblems = ''
      }
    },
    
    parseProblems() {
      // 공통 파싱 함수 사용
      this.parsedProblems = parseLeetCodeProblems(this.leetcodeProblems)
      
      console.log('🔍 parseProblems 완료 - 파싱된 문제들:', this.parsedProblems)
      console.log('🔍 파싱된 문제 개수:', this.parsedProblems.length)
    },
    
    normalizeDifficulty(difficulty) {
      const diff = difficulty.toLowerCase()
      if (diff.includes('easy')) return 'Easy'
      if (diff.includes('med') || diff.includes('medium')) return 'Medium'
      if (diff.includes('hard')) return 'Hard'
      return difficulty
    },
    
    generateUrlTitle(title) {
      return title
        .toLowerCase()
        .replace(/[^a-z0-9\s-]/g, '')
        .replace(/\s+/g, '-')
        .replace(/-+/g, '-')
        .trim()
    },
    
    clearProblems() {
      this.leetcodeProblems = ''
      this.parsedProblems = []
      this.showToastNotification('문제 목록이 지워졌습니다.', 'info')
    },
    
    async addParsedProblemsToExam() {
      if (!this.exam || this.parsedProblems.length === 0) {
        this.showToastNotification('추가할 문제가 없습니다.', 'warning')
        return
      }
      
      try {
        // 기존 시험 문제들의 csv_id 목록을 가져와서 중복 체크
        const existingQuestions = this.exam.questions || []
        const existingCsvIds = new Set(existingQuestions.map(q => q.csv_id))
        
        for (let i = 0; i < this.parsedProblems.length; i++) {
          const problem = this.parsedProblems[i]
          
          // 중복 체크: 같은 csv_id가 이미 존재하는지 확인
          if (existingCsvIds.has(problem.id.toString())) {
            console.log(`⏭️ 문제 건너뛰기 (이미 존재): ${problem.title} (ID: ${problem.id})`)
            continue
          }
          
          // 공통 함수 사용
          const questionData = convertToQuestionData(problem)
          questionData.explanation_ko = 'ㄴㅁㅇㄹㅁㄴㅇㄹㄴㅁㅇㄹ\n\n\nㄴㅁㅇㄹㄴㅁㅇㄹ'
          questionData.explanation_en = 'ㄴㅁㅇㄹㅁㄴㅇㄹㄴㅁㅇㄹ\n\n\nㄴㅁㅇㄹㄴㅁㅇㄹ'
          
          try {
            await axios.post(`/api/exam/${this.exam.id}/add-question/`, questionData)
            console.log(`✅ 문제 추가 완료: ${problem.title}`)
          } catch (questionError) {
            console.error(`❌ 문제 추가 실패: ${problem.title}`, questionError)
          }
        }
        
        // 결과 메시지는 상위 함수에서 처리하므로 여기서는 표시하지 않음
        
        // 시험 문제 목록 새로고침
        await this.loadExam(this.exam.id)
        
      } catch (error) {
        console.error('❌ 파싱된 문제 추가 실패:', error)
        this.showToastNotification('문제 추가 중 오류가 발생했습니다.', 'error')
      }
    },
    
    // 필터 행 토글
    toggleFilterRow() {
      this.showFilterRow = !this.showFilterRow
    },
    
    // 디버깅 메서드들
    debugGroupIdFilter() {
      // 그룹 ID 필터 디버깅용 메서드 (현재는 빈 함수)
      debugLog('Group ID Filter changed:', this.groupIdFilter)
    },
    
    // 무한 루프 방지를 위한 통계 수동 계산
    calculateExamStats() {
      debugLog('=== calculateExamStats 시작 ===')
      
      // examTotalQuestions 계산
      if (this.exam && this.exam.id) {
        // 1. resultDetails 기반 계산
        if (this.resultDetails && this.resultDetails.length > 0) {
          this.examTotalQuestions = this.resultDetails.length
          debugLog('examTotalQuestions - resultDetails 기반:', this.examTotalQuestions)
        }
        // 2. questionStatistics 기반 계산
        else if (this.questionStatistics && Array.isArray(this.questionStatistics) && this.questionStatistics.length > 0) {
          this.examTotalQuestions = this.questionStatistics.reduce((sum, stat) => sum + (stat.total_attempts || 0), 0)
          debugLog('examTotalQuestions - questionStatistics 기반:', this.examTotalQuestions)
        }
        // 3. questions 기반 계산
        else if (this.questions && this.questions.length > 0) {
          this.examTotalQuestions = this.questions.length
          debugLog('examTotalQuestions - questions 기반:', this.examTotalQuestions)
        }
        // 4. exam.total_questions 사용
        else {
          this.examTotalQuestions = this.exam.total_questions || 0
          debugLog('examTotalQuestions - exam.total_questions 사용:', this.examTotalQuestions)
        }
      }
      
      // latestScorePercentage 계산
      if (this.examTotalCorrect !== undefined && this.examTotalQuestions > 0) {
        this.latestScorePercentage = ((this.examTotalCorrect / this.examTotalQuestions) * 100).toFixed(1)
        debugLog('latestScorePercentage 계산 완료:', this.latestScorePercentage)
      } else {
        this.latestScorePercentage = 0
        debugLog('latestScorePercentage - 기본값 설정:', this.latestScorePercentage)
      }
      
      debugLog('=== calculateExamStats 완료 ===', {
        examTotalQuestions: this.examTotalQuestions,
        latestScorePercentage: this.latestScorePercentage
      })
    },
    
    // Notification 관련 메서드들
    showToastNotification(message, type = 'success', duration = 3000) {
      // 메시지 큐가 없으면 초기화
      if (!this.toastMessageQueue) {
        this.toastMessageQueue = []
        this.isShowingToast = false
      }
      
      // 메시지를 큐에 추가
      this.toastMessageQueue.push({ message, type, duration })
      
      // 현재 메시지를 표시하고 있지 않으면 다음 메시지 표시
      if (!this.isShowingToast) {
        this.processToastQueue()
      }
    },
    
    processToastQueue() {
      if (!this.toastMessageQueue || this.toastMessageQueue.length === 0) {
        this.isShowingToast = false
        return
      }
      
      this.isShowingToast = true
      const { message, type, duration } = this.toastMessageQueue.shift()
      
      this.toastMessage = message
      this.toastType = type
      
      // 아이콘 설정
      switch (type) {
        case 'success':
          this.toastIcon = 'fas fa-check-circle'
          break
        case 'error':
          this.toastIcon = 'fas fa-exclamation-circle'
          break
        case 'warning':
          this.toastIcon = 'fas fa-exclamation-triangle'
          break
        case 'info':
          this.toastIcon = 'fas fa-info-circle'
          break
        default:
          this.toastIcon = 'fas fa-check-circle'
      }
      
      this.showToast = true
      
      // 자동 숨김 후 다음 메시지 표시
      setTimeout(() => {
        this.hideToast()
        // 약간의 지연 후 다음 메시지 표시 (애니메이션을 위해)
        setTimeout(() => {
          this.processToastQueue()
        }, 300)
      }, duration)
    },
    
    hideToast() {
      this.showToast = false
    },
    
    showSuccessToast(message) {
      this.showToastNotification(message, 'success')
    },
    
    showErrorToast(message) {
      this.showToastNotification(message, 'error')
    },
    
    showWarningToast(message) {
      this.showToastNotification(message, 'warning')
    },
    
    showInfoToast(message) {
      this.showToastNotification(message, 'info')
    },
    
    showConfirmModal(title, message, callback, type = 'warning') {
      this.modalTitle = title
      this.modalMessage = message
      this.modalType = type
      this.modalCallback = callback
      this.showModal = true
      
      // Options 모달이 열려있으면 임시로 숨김
      if (this.showOptionsModal) {
        this.showOptionsModal = false
        // 확인 모달이 닫힐 때 Options 모달을 다시 열기 위해 플래그 설정
        this.shouldReopenOptionsModal = true
      }
    },
    
    confirmModal() {
      if (this.modalCallback) {
        this.modalCallback(true)
      }
      this.hideModal()
    },
    
    cancelModal() {
      if (this.modalCallback) {
        this.modalCallback(false)
      }
      this.hideModal()
    },
    
    hideModal() {
      this.showModal = false
      this.modalCallback = null
      
      // Options 모달을 다시 열어야 하는 경우
      if (this.shouldReopenOptionsModal) {
        this.showOptionsModal = true
        this.shouldReopenOptionsModal = false
      }
    },
    
    // Daily Exam 생성 메서드
    async createRandomRecommendationExams() {
      // 직접 Daily Exam 생성 로직 구현
      this.showConfirmModal(
        this.$t('examManagement.messages.randomExamConfirm'),
        this.$t('examManagement.messages.randomExamConfirm'),
        async () => {
          try {
            // 현재 사용자 정보 가져오기
            const user = getCurrentUser()
            if (!user) {
              this.showToastNotification('로그인이 필요합니다.', 'error')
              return
            }

            // create_random_recommendation_exam API 호출
            const response = await axios.post('/api/create-random-recommendation-exam/', {
              target_username: user.username,
              title: '',
              questions_per_exam: null,
              is_public: false
            })

            if (response.data.success) {
              const examData = response.data.exam
              this.showToastNotification(this.$t('examManagement.messages.randomExamSuccess'), 'success')
              
              // 캐시 강제 새로고침 플래그 설정
              sessionStorage.setItem('forceRefreshExamManagement', 'true')
              sessionStorage.setItem('forceRefreshProfile', 'true')
              
              this.$router.push(`/take-exam/${examData.id}?returnTo=exam-detail/${this.examId}`)
            } else {
              this.showToastNotification('Daily Exam 생성에 실패했습니다.', 'error')
            }
          } catch (error) {
            debugLog('Daily Exam 생성 실패:', error, 'error')
            if (error.response && error.response.data && error.response.data.error) {
              const errorKey = error.response.data.error
              let errorMessage = 'Daily Exam 생성에 실패했습니다.'
              
              // 번역 키에 따른 오류 메시지 처리
              if (errorKey === 'home.dailyExam.noSubscribedExams') {
                errorMessage = this.$t('home.dailyExam.noSubscribedExams')
                // subscribed exams가 없으면 profile 페이지로 이동
                this.showToastNotification(errorMessage, 'error')
                // 2초 후 profile 페이지로 이동
                setTimeout(() => {
                  this.$router.push('/profile')
                }, 2000)
                return
              } else if (errorKey === 'home.dailyExam.noQuestionsInSubscribedExams') {
                errorMessage = this.$t('home.dailyExam.noQuestionsInSubscribedExams')
              } else if (errorKey === 'home.dailyExam.noAccessibleExams') {
                errorMessage = this.$t('home.dailyExam.noAccessibleExams')
              } else if (errorKey === 'home.dailyExam.noQuestionsAvailable') {
                errorMessage = this.$t('home.dailyExam.noQuestionsAvailable')
              } else if (errorKey.startsWith('home.dailyExam.')) {
                // 번역 키가 있으면 번역된 메시지 사용
                errorMessage = this.$t(errorKey)
              } else {
                // 일반 오류 메시지
                errorMessage = `Daily Exam 생성 실패: ${errorKey}`
              }
              
              this.showToastNotification(errorMessage, 'error')
            } else {
              this.showToastNotification(this.$t('examManagement.messages.randomExamFailed'), 'error')
            }
          }
        }
      )
    },
    
    // 클라이언트 캐시 정리
    clearClientCache() {
      try {
        // localStorage에서 시험 관련 캐시 정리
        const keysToRemove = []
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i)
          if (key && (key.includes('exam') || key.includes('question') || key.includes('statistics'))) {
            keysToRemove.push(key)
          }
        }
        keysToRemove.forEach(key => localStorage.removeItem(key))
        
        // sessionStorage에서 시험 관련 캐시 정리
        const sessionKeysToRemove = []
        for (let i = 0; i < sessionStorage.length; i++) {
          const key = sessionStorage.key(i)
          if (key && (key.includes('exam') || key.includes('question') || key.includes('statistics'))) {
            sessionKeysToRemove.push(key)
          }
        }
        sessionKeysToRemove.forEach(key => sessionStorage.removeItem(key))
        
        // 현재 시험의 필터 캐시도 정리
        if (this.exam && this.exam.id) {
          const examId = this.exam.id
          const filterKeys = [
            `examDetail_${examId}_searchTerm`,
            `examDetail_${examId}_difficultyFilter`,
            `examDetail_${examId}_answerFilter`,
            `examDetail_${examId}_groupIdFilter`,
            `examDetail_${examId}_originalExamFilter`,
            `examDetail_${examId}_sortBy`,
            `examDetail_${examId}_sortOrder`
          ]
          filterKeys.forEach(key => sessionStorage.removeItem(key))
        }
        
        debugLog('클라이언트 캐시 정리 완료')
      } catch (error) {
        debugLog('클라이언트 캐시 정리 오류:', error, 'error')
      }
    },

    // 안전한 번역 메서드
    safeTranslate(key, fallback, count = null) {
      try {
        // 번역이 로드되지 않았으면 현재 언어에 맞는 fallback 반환
        if (!this.translationsLoaded) {
          return fallback
        }
        
        // 특정 키들에 대해서는 번역 시도하지 않고 바로 fallback 반환
        const skipTranslationKeys = [
          'examDetail.groupIdPlaceholder'
        ]
        
        if (skipTranslationKeys.includes(key)) {
          const currentLocale = this.$i18n.locale
          if (currentLocale === 'en') {
            // 영어 환경에서는 영어 fallback 사용
            const englishFallbacks = {
              'examDetail.confirmDeleteTitle': 'Confirm Question Deletion',
              'examDetail.confirmDeleteMessage': `Are you sure you want to delete ${count || this.selectedQuestions?.length || 0} selected question(s)?`,
              'examDetail.groupIdPlaceholder': 'Enter Group ID'
            }
            return englishFallbacks[key] || fallback
          } else {
            // 한국어 환경에서는 fallback 반환
            return fallback
          }
        }
        
        const translation = this.$t(key)
        
        // 번역 결과가 객체인 경우 (중첩된 번역 키) fallback 사용
        if (translation && typeof translation === 'object' && !Array.isArray(translation)) {
          return fallback
        }
        
        // 번역이 키와 같으면 (번역 실패) 현재 언어에 맞는 fallback 사용
        if (translation === key) {
          const currentLocale = this.$i18n.locale
          // 현재 언어에 따라 적절한 fallback 반환
          if (currentLocale === 'en') {
            // 영어 환경에서는 fallback 반환
            return fallback
          } else {
            return fallback
          }
        }
        
        return translation
      } catch (error) {
        return fallback
      }
    },
    

    
    // 설명 텍스트 포맷팅 (줄바꿈과 URL 링크 처리)
    formatDescription(text) {
      return formatTextWithLinks(text)
    },
    
    getSingleQuestionUrl(question) {
      // 현재 필터 상태를 URL 파라미터로 전달
      const filterParams = new URLSearchParams()
      if (this.searchTerm) filterParams.append('searchTerm', this.searchTerm)
      if (this.difficultyFilter) filterParams.append('difficultyFilter', this.difficultyFilter)
      if (this.answerFilter) filterParams.append('answerFilter', this.answerFilter)
      if (this.favoriteFilter) filterParams.append('favoriteFilter', this.favoriteFilter)
      if (this.ignoreFilter) filterParams.append('ignoreFilter', this.ignoreFilter)
      if (this.groupIdFilter) filterParams.append('groupIdFilter', this.groupIdFilter)
      if (this.sortBy) filterParams.append('sortBy', this.sortBy)
      if (this.sortOrder) filterParams.append('sortOrder', this.sortOrder)

      const filterString = filterParams.toString()
      // 인증 여부와 관계없이 문제를 볼 수 있도록 URL 반환 (읽기 전용 모드는 TakeExam에서 처리)
      return `/take-exam?question_id=${question.id}&exam_id=${this.exam.id}${filterString ? '&' + filterString : ''}`
    },

    startExam() {
      if (!this.exam || !this.exam.id) {
        this.showToastNotification(this.$t('examDetail.alerts.noExamInfo'), 'error')
        return
      }

      // 현재 화면에 표시된 문제들(필터된 문제들)만 사용
      const availableQuestions = this.filteredQuestions
      
      if (availableQuestions.length === 0) {
        this.showErrorToast(this.$t('examDetail.alerts.noQuestionDisplayed'))
        return
      }

      // 현재 필터 상태를 URL 파라미터로 전달
      const filterParams = new URLSearchParams()
      if (this.searchTerm) filterParams.append('searchTerm', this.searchTerm)
      if (this.difficultyFilter) filterParams.append('difficultyFilter', this.difficultyFilter)
      if (this.answerFilter) filterParams.append('answerFilter', this.answerFilter)
      if (this.favoriteFilter) filterParams.append('favoriteFilter', this.favoriteFilter)
      if (this.ignoreFilter) filterParams.append('ignoreFilter', this.ignoreFilter)
      if (this.groupIdFilter) filterParams.append('groupIdFilter', this.groupIdFilter)
      if (this.sortBy) filterParams.append('sortBy', this.sortBy)
      if (this.sortOrder) filterParams.append('sortOrder', this.sortOrder)

      // 즐겨찾기 모드인 경우 returnTo 파라미터 추가
      if (this.isFavoriteMode) {
        filterParams.append('returnTo', 'favorites')
      }

      // 선택된 문제가 있으면 선택된 문제들만 사용, 없으면 필터된 문제들 사용
      if (this.selectedQuestions && this.selectedQuestions.length > 0) {
        const selectedIds = this.selectedQuestions.join(',')
        // 선택된 문제들의 순서를 유지하여 전달
        this.$router.push(`/take-exam/${this.exam.id}?selected=${selectedIds}&order=${selectedIds}&restart=true&${filterParams.toString()}`)
      } else {
        // 필터된 문제들만 사용
        const filteredIds = availableQuestions.map(q => q.id).join(',')
        // 필터된 문제들의 순서를 유지하여 전달
        this.$router.push(`/take-exam/${this.exam.id}?selected=${filteredIds}&order=${filteredIds}&restart=true&${filterParams.toString()}`)
      }
    },
    restoreFilterStateFromURL() {
      // URL 파라미터에서 필터 입력란 초기값만 설정 (실제 필터링은 사용자 입력에 의해서만 동작)
      const urlParams = new URLSearchParams(window.location.search)

      // URL 파라미터가 있으면 필터 입력란에만 설정 (sessionStorage에는 저장하지 않음)
      if (urlParams.has('searchTerm')) {
        this.searchTerm = urlParams.get('searchTerm')
      }
      if (urlParams.has('difficultyFilter')) {
        this.difficultyFilter = urlParams.get('difficultyFilter')
      }
      if (urlParams.has('answerFilter')) {
        this.answerFilter = urlParams.get('answerFilter')
      }
      if (urlParams.has('groupIdFilter')) {
        this.groupIdFilter = urlParams.get('groupIdFilter')
      }
      if (urlParams.has('group_id')) {
        this.groupIdFilter = urlParams.get('group_id')
      }
      if (urlParams.has('sortBy')) {
        this.sortBy = urlParams.get('sortBy')
      }
      if (urlParams.has('sortOrder')) {
        this.sortOrder = urlParams.get('sortOrder')
      }
      if (urlParams.has('favoriteFilter')) {
        this.favoriteFilter = urlParams.get('favoriteFilter')
      }
      if (urlParams.has('ignoreFilter')) {
        this.ignoreFilter = urlParams.get('ignoreFilter')
      }
      if (urlParams.has('originalExamFilter')) {
        this.originalExamFilter = urlParams.get('originalExamFilter')
      }
    },
    async loadExam(examId) {
      debugLog('=== loadExam 함수 시작 ===', { examId, isFavoriteMode: this.isFavoriteMode })
      
      // 즐겨찾기 모드인 경우 시험 정보를 직접 설정하고 문제 목록만 로드
      if (this.isFavoriteMode) {
        debugLog('즐겨찾기 모드 - 시험 정보 직접 설정')
        
        // 사용자 프로필 언어를 먼저 가져와서 userProfileLanguage 초기화
        await this.getUserProfileLanguage()
        
        this.exam = {
          id: 'favorites',
          title: this.$t('examDetail.favorites'),
          display_title: this.$t('examDetail.favorites'),
          description: this.$t('examDetail.favoritesDescription'),
          total_questions: 0 // 문제 목록 로드 후 업데이트됨
        }
        debugLog('즐겨찾기 모드 - 시험 정보 설정 완료:', this.exam)
        
        // 즐겨찾기 모드에서는 문제 목록만 로드
        await this.loadQuestions('favorites')
        return
      }
      
      // 일반 모드인 경우 기존 로직 실행
      try {
        // Daily exam인 경우 강제로 캐시 무효화
        const isDailyExam = this.isCurrentUserDailyExam
        const forceRefresh = isDailyExam
        
        debugLog('loadExam - Daily exam 여부:', { isDailyExam, forceRefresh })
        
        // 사용자 프로필 언어 가져오기
        const userProfileLanguage = await this.getUserProfileLanguage()
        
        // 사용자 프로필 언어에 맞는 필드만 선택 (성능 최적화)
        // 현재 언어 필드 + 영어 fallback 필드 + display_title, display_description 필드만 요청
        const selectFields = ['id', 'is_public', 'is_original', 'created_at', 'created_language', 'is_ko_complete', 'is_en_complete', 'file_name', 'questions', 'total_questions', 'tags', 'display_title', 'display_description', 'age_rating', 'exam_difficulty', 'force_answer', 'voice_mode_enabled', 'ai_mock_interview', 'version_number']
        
        // 현재 언어 필드 추가
        if (userProfileLanguage === 'ko') {
          selectFields.push('title_ko', 'description_ko')
        } else if (userProfileLanguage === 'zh') {
          selectFields.push('title_zh', 'description_zh')
        } else if (userProfileLanguage === 'es') {
          selectFields.push('title_es', 'description_es')
        } else if (userProfileLanguage === 'ja') {
          selectFields.push('title_ja', 'description_ja')
        }
        
        // 영어 fallback 필드 추가 (항상 필요)
        selectFields.push('title_en', 'description_en')
        
        const config = forceRefresh ? {
          params: { 
            _t: Date.now(), // 캐시 무시를 위한 타임스탬프
            _nocache: '1', // 추가 캐시 무효화 파라미터
            _refresh: '1', // 서버 캐시 무효화
            select: selectFields.join(','),
            lang: userProfileLanguage
          }
        } : {
          params: {
            select: selectFields.join(','),
            lang: userProfileLanguage
          }
        }
        
        debugLog('loadExam - API 호출 시작')
        const response = await axios.get(`/api/exam/${examId}/`, config)
        debugApi('GET', `/api/exam/${examId}/`, null, response.data, response.status)
        
        this.exam = response.data
        debugObject('exam', this.exam)
        
        // 권한 정보 디버깅
        if (process.env.NODE_ENV === 'development') {
          const user = getCurrentUser()
          console.log('=== doohee323 권한 확인 ===')
          console.log('사용자:', user?.username || user?.email || 'anonymous')
          console.log('exam.user_permissions:', this.exam?.user_permissions)
          console.log('exam.created_by:', this.exam?.created_by)
          console.log('현재 사용자 ID:', user?.id)
          console.log('시험 생성자 ID:', this.exam?.created_by?.id)
          console.log('isAdmin():', isAdmin())
          console.log('hasStudyAdminRole():', hasStudyAdminRole())
          console.log('canDeleteQuestions:', this.canDeleteQuestions)
          console.log('========================')
        }

        // description에서 LeetCode 문제 파싱
        if (this.exam.description_ko || this.exam.description_en) {
          const description = getLocalizedContentWithI18n(
            this.exam,
            'description',
            this.$i18n,
            this.userProfileLanguage,
            ''
          )
          if (description) {
            this.leetcodeProblems = description
            this.parseProblems()
            debugLog('🔍 description에서 문제 파싱 완료:', this.parsedProblems)
          }
        }

        // 시험별 필터 복원
        debugLog('loadExam - 필터 복원 시작')
        this.restoreExamFilters()

        // URL 파라미터에서 필터 상태 복원 (시험 데이터 로드 후)
        debugLog('loadExam - URL 파라미터 복원 시작')
        this.restoreFilterStateFromURL()

        // 시험 로드 후 관련 스터디 자동 선택 (인증된 사용자만)
        if (this.isAuthenticated) {
          debugLog('loadExam - 스터디 자동 선택 시작')
          await this.autoSelectStudyForExam()
        } else {
          debugLog('인증되지 않은 사용자 - 스터디 자동 선택 건너뜀')
        }
        
        // 문제 목록 로드
        debugLog('loadExam - loadQuestions 호출 시작')
        await this.loadQuestions(examId)
        debugLog('loadExam - loadQuestions 호출 완료')
        
        // 연결된 프로젝트 로드 (인증된 사용자만)
        if (this.isAuthenticated) {
          debugLog('loadExam - loadConnectedStudies 호출 시작')
          await this.loadConnectedStudies(examId)
          debugLog('loadExam - loadConnectedStudies 호출 완료')
        } else {
          debugLog('인증되지 않은 사용자 - loadConnectedStudies 건너뜀')
        }
        
        // Voice Interview 결과 개수 확인 (AI 모의 인터뷰가 활성화된 경우)
        if (this.exam && this.exam.ai_mock_interview && this.isAuthenticated) {
          debugLog('loadExam - loadVoiceInterviewResultsCount 호출 시작')
          await this.loadVoiceInterviewResultsCount(examId)
          debugLog('loadExam - loadVoiceInterviewResultsCount 호출 완료')
        }
        
        debugLog('=== loadExam 함수 완료 ===')
      } catch (error) {
        debugLog('시험 로드 실패', error, 'error')
        
        // 401 에러인 경우 공개 시험인지 확인
        if (error.response && error.response.status === 401) {
          const examId = this.$route.params.examId || new URLSearchParams(window.location.search).get('exam_id')
          let isPublicExam = false
          
          // 공개 시험인지 확인
          try {
            const publicExamResponse = await axios.get(`/api/exams/`, {
              params: {
                id: examId,
                is_public: true
              }
            })
            
            const publicExams = publicExamResponse.data.results || publicExamResponse.data || []
            const foundExam = Array.isArray(publicExams) && publicExams.find(exam => exam.id === examId || exam.id === parseInt(examId))
            isPublicExam = !!foundExam
            
            // 공개 시험이면 공개 시험 목록에서 가져온 정보 사용
            if (isPublicExam && foundExam) {
              debugLog('공개 시험 확인됨 - 공개 시험 목록에서 정보 사용', foundExam)
              // 공개 시험 목록에서 가져온 정보로 설정
              this.exam = {
                id: foundExam.id,
                title_ko: foundExam.title_ko,
                title_en: foundExam.title_en,
                display_title: foundExam.display_title,
                description_ko: foundExam.description_ko,
                description_en: foundExam.description_en,
                is_public: foundExam.is_public,
                is_original: foundExam.is_original,
                created_at: foundExam.created_at,
                created_language: foundExam.created_language,
                is_ko_complete: foundExam.is_ko_complete,
                is_en_complete: foundExam.is_en_complete,
                total_questions: foundExam.total_questions || 0,
                questions: [],
                tags: foundExam.tags || []
              }
              // 공개 시험인 경우 문제 목록도 로드
              if (foundExam.is_public) {
                await this.loadQuestions(examId)
              } else {
                this.questionsLoaded = true
              }
              return
            }
          } catch (checkError) {
            debugLog('공개 시험 확인 실패:', checkError)
          }
          
          // 공개 시험이 아니거나 확인 실패한 경우에도 페이지에 머물도록 함
          // 공개 시험 목록 API를 통해 최소한의 정보 가져오기 시도
          if (!isPublicExam) {
            try {
              debugLog('비공개 시험 - 공개 시험 목록에서 최소 정보 가져오기 시도')
              const allExamsResponse = await axios.get(`/api/exams/`, {
                params: {
                  id: examId,
                  is_public: true
                }
              })
              
              const allExams = allExamsResponse.data.results || allExamsResponse.data || []
              const examInfo = Array.isArray(allExams) && allExams.find(exam => exam.id === examId || exam.id === parseInt(examId))
              
              if (examInfo) {
                // 공개 시험 목록에서 찾은 경우 최소한의 정보로 설정
                this.exam = {
                  id: examInfo.id,
                  title_ko: examInfo.title_ko,
                  title_en: examInfo.title_en,
                  display_title: examInfo.display_title,
                  description_ko: examInfo.description_ko,
                  description_en: examInfo.description_en,
                  is_public: examInfo.is_public,
                  total_questions: examInfo.total_questions || 0,
                  questions: []
                }
                // 공개 시험인 경우 문제 목록도 로드
                if (examInfo.is_public) {
                  await this.loadQuestions(examId)
                } else {
                  this.questionsLoaded = true
                }
                return
              }
            } catch (fallbackError) {
              debugLog('최소 정보 가져오기 실패:', fallbackError)
            }
          }
          
          // 정보를 가져올 수 없는 경우에도 페이지에 머물도록 함 (로그인 페이지로 리다이렉트하지 않음)
          this.showErrorToast(this.$t('examDetail.alerts.loginRequired') || '이 시험에 접근하려면 로그인이 필요합니다.')
          // 페이지에 머물도록 리다이렉트하지 않음
          return
        }
        
        // 403 에러인 경우 권한 없음 메시지 표시 및 스터디 가입 요청 체크
        if (error.response && error.response.status === 403) {
          const examId = this.$route.params.examId || new URLSearchParams(window.location.search).get('exam_id')
          
          // 로그인한 사용자인 경우 연결된 스터디 확인 및 가입 요청 생성
          if (this.isAuthenticated && examId) {
            // 연결된 스터디 로드 시도 (403이어도 연결된 스터디 정보는 가져올 수 있어야 함)
            debugLog('403 에러 후 연결된 스터디 로드 시작', { examId, isAuthenticated: this.isAuthenticated })
            this.loadConnectedStudies(examId).then(() => {
              debugLog('연결된 스터디 로드 완료', { 
                connectedStudiesCount: this.connectedStudies?.length || 0,
                connectedStudies: this.connectedStudies 
              })
              
              // 연결된 스터디가 있으면 가입 요청 생성
              if (this.connectedStudies && this.connectedStudies.length > 0) {
                debugLog('가입 요청 생성 시작', { connectedStudiesCount: this.connectedStudies.length })
                // 가입 요청 생성
                this.checkAndRequestStudyJoinFor403Error(examId).then((joinRequestSent) => {
                  debugLog('가입 요청 생성 완료', { joinRequestSent })
                  
                  // 가입 요청 성공 후 권한 없음 메시지 표시
                  if (joinRequestSent) {
                    // 가입 요청 메시지는 checkAndRequestStudyJoinFor403Error 내부에서 이미 표시됨
                    // 권한 없음 메시지를 큐에 추가 (가입 요청 메시지 다음에 표시됨)
                    this.showErrorToast(
                      this.$t('examDetail.alerts.noPermission') || '이 시험에 접근할 권한이 없습니다.'
                    )
                  } else {
                    // 가입 요청이 생성되지 않았으면 바로 권한 없음 메시지 표시
                    this.showErrorToast(
                      this.$t('examDetail.alerts.noPermission') || '이 시험에 접근할 권한이 없습니다.'
                    )
                  }
                }).catch(err => {
                  debugLog('가입 요청 생성 실패:', err, 'error')
                  // 가입 요청 실패 시 권한 없음 메시지 표시
                  this.showErrorToast(
                    this.$t('examDetail.alerts.noPermission') || '이 시험에 접근할 권한이 없습니다.'
                  )
                })
              } else {
                // 연결된 스터디가 없으면 바로 권한 없음 메시지 표시
                debugLog('연결된 스터디가 없음')
                this.showErrorToast(
                  this.$t('examDetail.alerts.noPermission') || '이 시험에 접근할 권한이 없습니다.'
                )
              }
            }).catch(err => {
              debugLog('403 에러 후 연결된 스터디 로드 실패:', err, 'error')
              // 연결된 스터디 로드 실패 시 권한 없음 메시지 표시
              this.showErrorToast(
                this.$t('examDetail.alerts.noPermission') || '이 시험에 접근할 권한이 없습니다.'
              )
            })
          } else {
            // 로그인하지 않은 사용자이거나 examId가 없는 경우
            this.showErrorToast(
              this.$t('examDetail.alerts.noPermission') || '이 시험에 접근할 권한이 없습니다.'
            )
          }
          return
        }
        
        this.showErrorToast(this.$t('examDetail.alerts.loadExamFailed'))
      }
    },
    async loadConnectedStudies(examId) {
      if (!this.isAuthenticated) {
        debugLog('인증되지 않은 사용자 - 연결된 프로젝트 로드 건너뜀');
        this.connectedStudies = [];
        return Promise.resolve();
      }
      debugLog('연결된 프로젝트 로드 시작', { examId })
      try {
        const response = await axios.get(`/api/exam/${examId}/connected-studies/`)
        debugApi('GET', `/api/exam/${examId}/connected-studies/`, null, response.data, response.status)
        
        if (response.data.success) {
          this.connectedStudies = response.data.connected_studies || []
          debugLog('연결된 프로젝트 로드 완료', { count: this.connectedStudies.length })
        } else {
          debugLog('연결된 프로젝트 로드 실패 - API 응답 오류', response.data, 'error')
        }
        return Promise.resolve()
      } catch (error) {
        debugLog('연결된 프로젝트 로드 실패', error, 'error')
        // 연결된 프로젝트 로드 실패는 시험 로드에 영향을 주지 않도록 조용히 처리
        return Promise.resolve()
      }
    },
    
    /**
     * 403 에러 발생 시 연결된 스터디에 가입 요청 생성 (exam 객체가 없는 경우)
     */
    async checkAndRequestStudyJoinFor403Error(examId) {
      if (!this.isAuthenticated || !examId) {
        debugLog('가입 요청 체크 건너뜀 - 인증되지 않음 또는 examId 없음', { isAuthenticated: this.isAuthenticated, examId })
        return Promise.resolve(false)
      }
      
      try {
        // 연결된 스터디가 없으면 건너뛰기
        if (!this.connectedStudies || this.connectedStudies.length === 0) {
          debugLog('가입 요청 체크 건너뜀 - 연결된 스터디 없음', { connectedStudies: this.connectedStudies })
          return Promise.resolve(false)
        }
        
        debugLog('가입 요청 체크 시작', { connectedStudiesCount: this.connectedStudies.length })
        let joinRequestSent = false
        
        // 각 연결된 스터디에 대해 멤버 여부 확인
        for (const connectedStudy of this.connectedStudies) {
          try {
            // 스터디 상세 정보 가져오기 (멤버 정보 포함)
            const studyResponse = await axios.get(`/api/studies/${connectedStudy.study_id}/`)
            const study = studyResponse.data
            
            // 사용자가 이미 멤버인지 확인
            const user = getCurrentUserFromPermissions()
            if (!user) continue
            
            const isMember = study.members && study.members.some(member => {
              if (!member.user) return false
              const memberUserId = typeof member.user === 'object' ? member.user.id : member.user
              return memberUserId === user.id && member.is_active === true
            })
            
            debugLog('멤버 여부 확인', { 
              studyId: connectedStudy.study_id, 
              userId: user.id, 
              isMember,
              membersCount: study.members?.length || 0
            })
            
            // 멤버가 아니면 가입 신청
            if (!isMember) {
              // 이미 가입 요청이 있는지 확인
              try {
                const joinRequestsResponse = await axios.get(`/api/study-join-request/user/`)
                debugLog('가입 요청 목록 확인', { 
                  studyId: connectedStudy.study_id,
                  totalRequests: joinRequestsResponse.data?.length || 0,
                  requests: joinRequestsResponse.data
                })
                
                const existingRequest = joinRequestsResponse.data.find(req => {
                  // study 필드가 객체인 경우와 ID인 경우 모두 처리
                  const reqStudyId = typeof req.study === 'object' ? req.study.id : req.study
                  return reqStudyId === connectedStudy.study_id && req.status === 'pending'
                })
                
                debugLog('기존 가입 요청 확인', { 
                  studyId: connectedStudy.study_id,
                  existingRequest: existingRequest ? { id: existingRequest.id, status: existingRequest.status } : null
                })
                
                if (!existingRequest) {
                  // 시험 정보 가져오기 (제목용) - 403 에러가 발생할 수 있으므로 조용히 처리
                  let examTitle = '시험'
                  try {
                    const examResponse = await axios.get(`/api/exam/${examId}/`)
                    examTitle = getLocalizedContentWithI18n(examResponse.data, 'title', this.$i18n, this.userProfileLanguage, '시험')
                  } catch (e) {
                    // 시험 정보를 가져올 수 없어도 계속 진행
                    debugLog('시험 정보 가져오기 실패 (403 에러 후):', e, 'debug')
                  }
                  
                  // 가입 요청 생성
                  await axios.post('/api/study-join-request/', {
                    study_id: connectedStudy.study_id,
                    message: `비공개 시험 "${examTitle}"에 접근하기 위한 가입 요청입니다.`
                  })
                  
                  joinRequestSent = true
                  debugLog('스터디 가입 신청 완료 (403 에러 후):', connectedStudy.study_id)
                  
                  // 메시지 표시 (가입 요청 성공 메시지)
                  // 스터디 상세 정보에서 현재 언어에 맞는 제목 가져오기
                  const studyTitle = getLocalizedContentWithI18n(study, 'title', this.$i18n, this.userProfileLanguage, connectedStudy.study_title || '스터디')
                  this.showInfoToast(
                    this.$t('takeExam.studyJoinRequestSent', { studyName: studyTitle }) || `"${studyTitle}" 스터디에 가입 요청을 보냈습니다.`
                  )
                } else {
                  // 기존 가입 요청이 있는 경우에도 메시지 표시
                  debugLog('기존 가입 요청 존재 (403 에러 후):', existingRequest)
                  joinRequestSent = true
                  // 스터디 상세 정보에서 현재 언어에 맞는 제목 가져오기
                  const studyTitle = getLocalizedContentWithI18n(study, 'title', this.$i18n, this.userProfileLanguage, connectedStudy.study_title || '스터디')
                  this.showInfoToast(
                    this.$t('takeExam.studyJoinRequestSent', { studyName: studyTitle }) || `"${studyTitle}" 스터디에 가입 요청을 보냈습니다.`
                  )
                }
              } catch (joinRequestError) {
                debugLog('가입 요청 확인/생성 실패 (403 에러 후):', joinRequestError, 'error')
                // 가입 요청 실패는 조용히 처리 (이미 요청이 있거나 다른 이유일 수 있음)
              }
            }
          } catch (studyError) {
            debugLog(`스터디 ${connectedStudy.study_id} 정보 로드 실패 (403 에러 후):`, studyError, 'error')
            // 스터디 정보 로드 실패는 무시하고 계속 진행
          }
        }
        
        return Promise.resolve(joinRequestSent)
      } catch (error) {
        debugLog('스터디 가입 신청 체크 실패 (403 에러 후):', error, 'error')
        // 에러는 조용히 처리 (사용자 경험에 영향을 주지 않도록)
        return Promise.resolve(false)
      }
    },
    restoreExamFilters() {
      // 시험별 필터 복원 (URL 파라미터가 있으면 덮어쓰지 않음)
      if (this.exam && this.exam.id) {
        const urlParams = new URLSearchParams(window.location.search)
        
        // URL 파라미터가 없는 경우에만 세션에서 복원
        if (!urlParams.has('searchTerm')) {
          this.searchTerm = this.getStoredFilter('searchTerm', '')
        }
        if (!urlParams.has('difficultyFilter')) {
          this.difficultyFilter = this.getStoredFilter('difficultyFilter', '')
        }
        if (!urlParams.has('answerFilter')) {
          this.answerFilter = this.getStoredFilter('answerFilter', '')
        }
        if (!urlParams.has('favoriteFilter')) {
          this.favoriteFilter = this.getStoredFilter('favoriteFilter', '')
        }
        if (!urlParams.has('ignoreFilter')) {
          this.ignoreFilter = this.getStoredFilter('ignoreFilter', this.isFavoriteMode ? '' : 'not_ignored')
        }
        if (!urlParams.has('group_id') && !urlParams.has('groupIdFilter')) {
          // URL 파라미터가 없을 때만 세션에서 복원
          this.groupIdFilter = this.getStoredFilter('groupIdFilter', '')
        }
        if (!urlParams.has('originalExamFilter')) {
          this.originalExamFilter = this.getStoredFilter('originalExamFilter', '')
        }
        if (!urlParams.has('sortBy')) {
          this.sortBy = this.getStoredFilter('sortBy', 'priority')
        }
        if (!urlParams.has('sortOrder')) {
          this.sortOrder = this.getStoredFilter('sortOrder', 'asc')
        }
      }
    },
    async loadQuestions(examId, forceRefresh = false) {
      debugLog('=== loadQuestions 함수 시작 ===', { examId, forceRefresh })
      this.questionsLoading = true
      try {
        // 인증된 사용자인 경우 즐겨찾기 상태를 백그라운드에서 비동기로 로드
        // 문제 목록 로딩을 블로킹하지 않도록 await 없이 실행
        // 단, TakeExam 페이지에서는 중복 호출을 방지하기 위해 건너뜀
        // 즐겨찾기 모드가 아닐 때만 호출 (즐겨찾기 모드는 loadQuestions에서 처리)
        debugLog('=== loadQuestions에서 loadFavoriteStatus 호출 조건 확인 ===', {
          isAuthenticated: this.isAuthenticated,
          routePath: this.$route.path,
          startsWithTakeExam: this.$route.path.startsWith('/take-exam'),
          isFavoriteMode: this.isFavoriteMode,
          shouldCallLoadFavoriteStatus: this.isAuthenticated && !this.$route.path.startsWith('/take-exam') && !this.isFavoriteMode
        })
        
        // loadFavoriteStatus를 백그라운드에서 비동기로 실행 (문제 목록 로딩을 블로킹하지 않음)
        if (this.isAuthenticated && !this.$route.path.startsWith('/take-exam') && !this.isFavoriteMode) {
          debugLog('=== loadQuestions에서 loadFavoriteStatus 백그라운드 실행 ===')
          // await 없이 백그라운드에서 실행
          this.loadFavoriteStatus().catch(error => {
            debugLog('❌ loadFavoriteStatus 백그라운드 실행 실패:', error, 'error')
          })
        } else {
          debugLog('=== loadQuestions에서 loadFavoriteStatus 건너뜀 ===', {
            reason: !this.isAuthenticated ? 'not authenticated' : 
                   this.$route.path.startsWith('/take-exam') ? 'take-exam page' : 
                   this.isFavoriteMode ? 'favorite mode' : 'unknown'
          })
        }
        
        const config = forceRefresh ? { 
          headers: { 
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache'
          },
          params: { 
            _t: Date.now(), // 캐시 무시를 위한 타임스탬프
            _nocache: '1', // 추가 캐시 무효화 파라미터
            _refresh: '1', // 서버 캐시 무효화
            select: 'id,csv_id,title_ko,title_en,difficulty,url,group_id,created_at,updated_at,created_language,is_ko_complete,is_en_complete,created_by' // 목록 표시용 최소 필드만
          }
        } : {
          params: {
            select: 'id,csv_id,title_ko,title_en,difficulty,url,group_id,created_at,updated_at,created_language,is_ko_complete,is_en_complete,created_by' // 목록 표시용 최소 필드만
          }
        }
        
        let response
        if (this.isFavoriteMode) {
          // 즐겨찾기 모드인 경우 즐겨찾기 문제만 조회
          debugLog('=== 즐겨찾기 모드 - favorite-exam-questions API 호출 ===', {
            routePath: this.$route.path,
            isFavoriteMode: this.isFavoriteMode,
            config: config
          })
          try {
            response = await axios.get('/api/favorite-exam-questions/', config)
            debugApi('GET', '/api/favorite-exam-questions/', null, response.data, response.status)
            
            // 즐겨찾기 API 응답 구조: {questions: Array, exam: Object}
            debugLog('즐겨찾기 API 응답 구조 확인:', {
              responseData: response.data,
              hasQuestions: !!response.data.questions,
              questionsType: typeof response.data.questions,
              isArray: Array.isArray(response.data.questions)
            })
            
            // questions 초기화 전 상태 확인
            debugLog('questions 초기화 전 상태:', {
              beforeType: typeof this.questions,
              beforeIsArray: Array.isArray(this.questions),
              beforeValue: this.questions
            });
            
            // 안전하게 questions 설정
            if (response.data.questions && Array.isArray(response.data.questions)) {
              this.questions = [...response.data.questions]; // 배열 복사
              debugLog('즐겨찾기 문제 목록 설정 완료 (배열 복사):', {
                questionsLength: this.questions.length,
                questionsType: typeof this.questions,
                isArray: Array.isArray(this.questions)
              });
            } else {
              debugLog('즐겨찾기 문제가 없거나 배열이 아님, 빈 배열로 설정');
              this.questions = [];
            }
            
            // 즐겨찾기 API 응답에서 exam 정보가 있으면 저장 (실제 exam ID를 사용하기 위해)
            if (response.data.exam && response.data.exam.id) {
              debugLog('즐겨찾기 API 응답에서 exam 정보 확인:', response.data.exam)
              // exam 정보 병합 (기존 exam 정보 유지하면서 실제 ID 업데이트)
              this.exam = {
                ...this.exam,
                ...response.data.exam,
                id: response.data.exam.id // 실제 exam ID 사용
              }
              debugLog('즐겨찾기 exam 정보 업데이트 완료:', this.exam)
            }
          } catch (error) {
            debugLog('즐겨찾기 문제 조회 실패:', error, 'error')
            // 즐겨찾기 문제가 없는 경우 빈 배열로 설정
            this.questions = []
            this.questionsLoaded = true
            this.questionsLoading = false
            return
          }
        } else {
          // 일반 모드인 경우 해당 시험의 문제 조회
          // 필요한 필드들을 명시적으로 요청
          const questionConfig = {
            ...config,
            params: {
              ...config.params,
              select: 'id,csv_id,title_ko,title_en,content_ko,content_en,answer_ko,answer_en,explanation_ko,explanation_en,difficulty,url,group_id,created_at,updated_at,created_language,is_ko_complete,is_en_complete,created_by'
            }
          }
          response = await axios.get(`/api/exam/${examId}/questions/`, questionConfig)
          debugApi('GET', `/api/exam/${examId}/questions/`, null, response.data, response.status)
          
          // 일반 API 응답 구조: Array
          debugLog('일반 모드 API 응답 구조 확인:', {
            responseData: response.data,
            responseDataType: typeof response.data,
            isArray: Array.isArray(response.data)
          })
          
          this.questions = response.data
        }
        debugLog('loadQuestions - 응답 데이터:', response.data);
        debugLog('loadQuestions - questions 배열 길이:', this.questions ? this.questions.length : 'null');
        debugLog('questions 타입 확인:', {
          type: typeof this.questions,
          isArray: Array.isArray(this.questions),
          constructor: this.questions?.constructor?.name,
          value: this.questions
        });
        
        // questions가 배열인지 확인하고 안전하게 처리
        if (!Array.isArray(this.questions)) {
          debugLog('questions가 배열이 아님:', this.questions, 'error')
          debugLog('questions 강제로 빈 배열로 설정')
          this.questions = []
          this.questionsLoaded = true
          this.questionsLoading = false
          return
        }
        
        // 목록 표시용 localized 필드만 생성 (content, answer, explanation 제외)
        this.questions.forEach((question, index) => {
          question.localized_title = getLocalizedContentWithI18n(
            question,
            'title',
            this.$i18n,
            this.userProfileLanguage,
            ''
          )
          
          // 첫 번째 문제만 간단하게 로깅
          if (index === 0) {
            debugLog(`첫 번째 문제 목록용 localized 필드:`, {
              title: question.localized_title
            })
          }
        })
        
        debugObject('questions', { count: this.questions.length })
        debugObject('first question localized fields', {
          localized_title: this.questions[0]?.localized_title,
          localized_content: this.questions[0]?.localized_content,
          localized_answer: this.questions[0]?.localized_answer,
          localized_explanation: this.questions[0]?.localized_explanation
        })

        // 즐겨찾기 모드인 경우 추가 처리
        if (this.isFavoriteMode) {
          debugLog('즐겨찾기 모드 - 추가 처리 생략 (문제 목록만 표시)')
          // 즐겨찾기 모드에서는 기본적인 문제 목록만 표시
        } else {
          // 일반 모드인 경우 추가 정보 로드 (인증된 사용자만)
          if (this.isAuthenticated) {
            await this.loadMappings()
            await this.loadQuestionStatistics(examId)
            await this.loadMemberMappings(examId)
          } else {
            debugLog('인증되지 않은 사용자 - 추가 정보 로드 건너뜀 (문제 통계만 로드)')
            // 공개 시험인 경우 문제 통계만 로드
            await this.loadQuestionStatistics(examId)
          }
        }

        // favorite 시험인 경우 원본 시험 정보 로드 (즐겨찾기 모드에서는 제외)
        if (this.isFavoriteExam && !this.isFavoriteMode) {
          await this.loadOriginalExamsForQuestions()
        }
        
        // exam.total_questions 설정 (문제 목록 길이 기반)
        if (this.exam && this.questions) {
          this.exam.total_questions = this.questions.length
          debugLog('exam.total_questions 설정 완료:', this.exam.total_questions)
        }
        
        // 무한 루프 방지를 위한 수동 계산
        this.calculateExamStats()

        // 문제 로드 완료 플래그 설정
        this.questionsLoaded = true

        debugLog('=== loadQuestions 완료 ===', { 
          examId, 
          questionsCount: this.questions.length,
          examTotalQuestions: this.exam?.total_questions,
          firstQuestion: this.questions[0] ? {
            title: this.questions[0].localized_title,
            content: this.questions[0].localized_content ? '있음' : '없음',
            answer: this.questions[0].localized_answer ? '있음' : '없음',
            explanation: this.questions[0].localized_explanation ? '있음' : '없음'
          } : null
        })
      } catch (error) {
        debugLog('문제 목록 로드 실패', error, 'error')
        
        // 인증 오류인 경우에도 페이지에 머물도록 함 (로그인 페이지로 리다이렉트하지 않음)
        // 공개 시험인 경우 문제 목록을 빈 배열로 설정하고 계속 진행
        if (error.response && error.response.status === 401) {
          // 공개 시험인지 확인
          if (this.exam && this.exam.is_public) {
            debugLog('공개 시험 - 문제 목록을 빈 배열로 설정하고 계속 진행')
            this.questions = []
            this.questionsLoaded = true
            return
          }
          // 비공개 시험인 경우에만 에러 처리
          this.questionsLoaded = true
          return
        }
        
        this.showErrorToast(this.$t('examDetail.alerts.loadQuestionListFailed'))
        this.questionsLoaded = true // 에러가 발생해도 로드 완료로 표시
      } finally {
        this.questionsLoading = false
      }
    },
    
    // 엑셀 다운로드용 상세 데이터 로드 (성능 최적화)
    async loadQuestionsForExcel(examId) {
      debugLog('=== loadQuestionsForExcel 시작 ===', { examId })
      
      try {
        // 간단하고 효과적인 캐시 무효화
        const timestamp = Date.now()
        const randomId = Math.random().toString(36).substring(7)
        
        const config = { 
          headers: { 
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache'
          },
          params: { 
            _t: timestamp,
            _nocache: randomId,
            _refresh: '1',
            select: 'id,csv_id,title_ko,title_en,content_ko,content_en,answer_ko,answer_en,explanation_ko,explanation_en,difficulty,url,group_id,created_at,updated_at,created_language,is_ko_complete,is_en_complete,created_by'
          }
        }
        
        debugLog('loadQuestionsForExcel - 캐시 무효화 파라미터:', config.params)
        
        const response = await axios.get(`/api/exam/${examId}/questions/`, config)
        debugApi('GET', `/api/exam/${examId}/questions/`, null, response.data, response.status)
        
        // 첫 번째 문제의 raw data 로깅
        if (response.data && response.data.length > 0) {
          const firstQuestion = response.data[0]
          debugLog('백엔드에서 받은 첫 번째 문제 raw data:', {
            id: firstQuestion.id,
            csv_id: firstQuestion.csv_id,
            title_ko: firstQuestion.title_ko,
            title_en: firstQuestion.title_en,
            content_ko: firstQuestion.content_ko ? '있음' : '없음',
            content_en: firstQuestion.content_en ? '있음' : '없음',
            answer_ko: firstQuestion.answer_ko ? '있음' : '없음',
            answer_en: firstQuestion.answer_en ? '있음' : '없음',
            explanation_ko: firstQuestion.explanation_ko ? '있음' : '없음',
            explanation_en: firstQuestion.explanation_en ? '있음' : '없음',
            difficulty: firstQuestion.difficulty,
            url: firstQuestion.url,
            group_id: firstQuestion.group_id
          })
        }
        
        // 기존 questions 배열을 상세 데이터로 교체 (강제 업데이트)
        this.$set(this, 'questions', response.data)
        
        // 각 문제에 localized 필드 추가
        this.questions.forEach((question, index) => {
          question.localized_title = getLocalizedContentWithI18n(
            question,
            'title',
            this.$i18n,
            this.userProfileLanguage,
            ''
          )
          question.localized_content = getLocalizedContentWithI18n(
            question,
            'content',
            this.$i18n,
            this.userProfileLanguage,
            ''
          )
          question.localized_answer = getLocalizedContentWithI18n(
            question,
            'answer',
            this.$i18n,
            this.userProfileLanguage,
            ''
          )
          question.localized_explanation = getLocalizedContentWithI18n(
            question,
            'explanation',
            this.$i18n,
            this.userProfileLanguage,
            ''
          )
          
          // 첫 번째 문제만 로깅
          if (index === 0) {
            debugLog(`엑셀용 첫 번째 문제 localized 필드:`, {
              title: question.localized_title,
              content: question.localized_content ? '있음' : '없음',
              answer: question.localized_answer ? '있음' : '없음',
              explanation: question.localized_explanation ? '있음' : '없음'
            })
          }
        })
        
        // exam.total_questions 업데이트 (엑셀용 상세 데이터 로드 후)
        if (this.exam && this.questions) {
          this.exam.total_questions = this.questions.length
          debugLog('exam.total_questions 엑셀용 업데이트 완료:', this.exam.total_questions)
        }
        
        debugLog('=== loadQuestionsForExcel 완료 ===', { 
          examId, 
          questionsCount: this.questions.length,
          examTotalQuestions: this.exam?.total_questions
        })
        
      } catch (error) {
        debugLog('엑셀용 문제 목록 로드 실패', error, 'error')
        throw error
      }
    },
    formatDate(dateString) {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      })
    },
    getDifficultyBadgeClass(difficulty) {
      if (!difficulty) return 'bg-secondary'
      
      const normalized = difficulty.toLowerCase().trim()
      if (normalized === 'easy') return 'bg-success'
      if (normalized === 'med' || normalized === 'medium' || normalized === 'med.') return 'bg-warning'
      if (normalized === 'hard') return 'bg-danger'
      return 'bg-secondary'
    },

    resetFilters() {
      this.searchTerm = ''
      this.difficultyFilter = ''
      this.answerFilter = ''
      this.favoriteFilter = ''
      this.ignoreFilter = this.isFavoriteMode ? '' : 'not_ignored'
      this.groupIdFilter = ''
      this.originalExamFilter = ''
      this.sortBy = 'priority'
      this.sortOrder = 'asc'

      // 시험별 sessionStorage에서도 클리어
      this.setStoredFilter('searchTerm', '')
      this.setStoredFilter('difficultyFilter', '')
      this.setStoredFilter('answerFilter', '')
      this.setStoredFilter('favoriteFilter', '')
      this.setStoredFilter('ignoreFilter', this.isFavoriteMode ? '' : 'not_ignored')
      this.setStoredFilter('groupIdFilter', '')
      this.setStoredFilter('originalExamFilter', '')
      this.setStoredFilter('sortBy', 'priority')
      this.setStoredFilter('sortOrder', 'asc')
      
      
    },
    isQuestionSelected(questionId) {
      return this.selectedQuestions.includes(questionId)
    },
    toggleAllQuestions() {
      if (this.isAllSelected) {
        this.selectedQuestions = []
      } else {
        this.selectedQuestions = this.filteredQuestions.map(q => q.id)
      }
    },
    updateSelection() {
      // 선택된 문제 수 업데이트
      this.selectedQuestionCount = this.selectedQuestions.length
    },
    handleCheckboxClick(event, index, questionId) {
      const checked = event.target.checked;
      if (event.shiftKey && this.lastCheckedIndex !== null) {
        // shift+클릭: 범위 선택
        const start = Math.min(this.lastCheckedIndex, index);
        const end = Math.max(this.lastCheckedIndex, index);
        const idsInRange = this.filteredQuestions.slice(start, end + 1).map(q => q.id);
        if (checked) {
          // 범위 추가
          this.selectedQuestions = Array.from(new Set([...this.selectedQuestions, ...idsInRange]));
        } else {
          // 범위 해제
          this.selectedQuestions = this.selectedQuestions.filter(id => !idsInRange.includes(id));
        }
        // shift+클릭에서는 lastCheckedIndex를 갱신하지 않음
      } else {
        // 일반 클릭: 단일 선택/해제
        if (checked) {
          if (!this.selectedQuestions.includes(questionId)) {
            this.selectedQuestions = [...this.selectedQuestions, questionId];
          }
        } else {
          this.selectedQuestions = this.selectedQuestions.filter(id => id !== questionId);
        }
        // 일반 클릭에서만 lastCheckedIndex 갱신
        this.lastCheckedIndex = index;
      }
    },
    selectRandomQuestions() {
      const availableQuestions = this.filteredQuestions.map(q => q.id)
      const count = Math.min(this.selectedQuestionCount, availableQuestions.length)

      // 랜덤 선택
      const shuffled = [...availableQuestions].sort(() => 0.5 - Math.random())
      this.selectedQuestions = shuffled.slice(0, count)
    },
    clearSelection() {
      this.selectedQuestions = []
      this.customExamTitle = '' // 사용자 정의 시험 제목도 초기화
    },
    async createRandomExam() {
      let availableQuestions = []
      let questions = []
      
      if (this.selectedQuestions.length > 0) {
        // Manual Selection: 선택된 문제들만 사용
        // selectedQuestions는 이미 ID 배열이므로 그대로 사용
        questions = this.selectedQuestions
        // ID로 문제 객체들을 찾아서 availableQuestions 설정
        availableQuestions = this.filteredQuestions.filter(q => this.selectedQuestions.includes(q.id))
      } else {
        // Random Selection: 현재 화면에 표시된 문제들(필터된 문제들)만 사용
        availableQuestions = this.filteredQuestions
        questions = availableQuestions.map(q => q.id)
      }
      
      if (availableQuestions.length === 0) {
        this.showToastNotification(this.$t('examDetail.alerts.noQuestionDisplayed'), 'error')
        return
      }

      try {
        // 시험 제목 결정: 사용자가 입력한 제목이 있으면 사용, 없으면 기본 제목 사용
        const examTitle = this.customExamTitle.trim() || `Today's Quizzes for ${this.currentUser.username}`
        
        const examData = {
          title: examTitle,
          questions: questions, // 선택 모드에 따라 문제 ID들 전송
          is_original: false,
          is_public: false, // Private으로 설정
          random_option: this.randomOption,
          question_count: this.selectedQuestionCount,
          selection_mode: this.selectedQuestions.length > 0 ? 'manual' : 'random', // 선택된 문제 여부에 따라 자동 설정
          creation_type: 'random'  // 랜덤 생성 시 기존 문제 참조
        }
        

        
        const response = await axios.post('/api/create-exam/', examData)
        if (!response.data || !response.data.id) {
          this.showErrorToast(this.$t('examDetail.alerts.createExamFailed'))
          return
        }
        
        // 시험 생성 후 강제 새로고침 플래그 설정
        sessionStorage.setItem('forceRefreshExamManagement', 'true')
        
        this.showSuccessToast(`출제 시험이 성공적으로 생성되었습니다!`)
        this.$router.push('/exam-management')
      } catch (error) {
        debugLog('출제 시험 생성 실패:', error, 'error')
        this.showErrorToast(this.$t('examDetail.alerts.createRandomExamFailed'))
      }
    },
    async loadStudies() {
      debugLog('스터디 목록 로드 시작')
      try {
        const response = await axios.get('/api/studies/')
        debugApi('GET', '/api/studies/', null, response.data, response.status)
        
        this.studies = response.data.results || response.data || []
        debugObject('studies', { count: this.studies.length })
        debugLog('스터디 목록 로드 완료')
      } catch (error) {
        debugLog('스터디 목록 로드 실패', error, 'error')
        this.studies = []
        this.showErrorToast(this.$t('examDetail.alerts.loadStudyListFailed'))
      }
    },
    async loadStudyMembers() {
      debugLog('스터디 멤버 로드 시작', { selectedStudyId: this.selectedStudyId })
      if (!this.selectedStudyId) {
        this.studyMembers = [];
        debugLog('스터디 ID가 없어서 멤버 로드 건너뜀')
        return;
      }
      try {
        const response = await axios.get(`/api/studies/${this.selectedStudyId}/members/`)
        debugApi('GET', `/api/studies/${this.selectedStudyId}/members/`, null, response.data, response.status)
        
        // 활성화된 멤버만 필터링
        this.studyMembers = response.data.filter(member => member.is_active === true)
        debugObject('studyMembers', { count: this.studyMembers.length })

        // 스터디 선택 상태를 sessionStorage에 저장
        if (this.exam && this.exam.id) {
          sessionStorage.setItem(`exam_${this.exam.id}_selectedStudyId`, this.selectedStudyId)
        }
        
        debugLog('스터디 멤버 로드 완료')
      } catch (error) {
        debugLog('스터디 멤버 로드 실패', error, 'error')
        this.showErrorToast(this.$t('examDetail.alerts.loadStudyMemberFailed'))
      }
    },
    async createMemberMapping() {
      if (!this.exam) {
        this.showErrorToast(this.$t('examDetail.alerts.loadExamFirst'))
        return
      }
      if (!this.selectedStudyId) {
        this.showErrorToast(this.$t('examDetail.alerts.selectStudy'))
        return
      }
      if (this.studyMembers.length === 0) {
        this.showErrorToast(this.$t('examDetail.alerts.noStudyMember'))
        return
      }

      // 필터된 문제 목록 확인
      const filteredQuestions = this.filteredQuestions
      if (filteredQuestions.length === 0) {
        this.showErrorToast(this.$t('examDetail.alerts.noFilteredQuestion'))
        return
      }

      try {
        const mappingData = {
          exam_id: this.exam.id,
          study_id: this.selectedStudyId,
          question_ids: filteredQuestions.map(q => q.id) // 필터된 문제 ID들만 전송
        }

        await axios.post('/api/create-question-member-mapping/', mappingData)

        // 멤버 매핑 데이터 다시 로드
        await this.loadMemberMappings(this.exam.id)

        // 성공 메시지 표시
        this.showSuccessToast(this.$t('examDetail.memberMappingCreated', { count: filteredQuestions.length }))

        // 스터디 선택 상태는 유지 (초기화하지 않음)

      } catch (error) {
        debugLog('멤버별 문제 매핑 생성 실패:', error, 'error')
        debugLog('에러 상세:', error.response?.data, 'error')
        this.showErrorToast(this.$t('examDetail.alerts.memberQuestionMappingFailed'))
      }
    },
    async loadMappings() {
      console.log('🔍 [loadMappings] 함수 호출됨', {
        isAuthenticated: this.isAuthenticated,
        examId: this.exam?.id,
        stackTrace: new Error().stack
      });
      if (!this.isAuthenticated) {
        console.log('❌ [loadMappings] 인증되지 않은 사용자 - 매핑 목록 로드 건너뜀');
        debugLog('인증되지 않은 사용자 - 매핑 목록 로드 건너뜀');
        this.mappings = [];
        return;
      }
      if (!this.exam || !this.exam.id) {
        console.log('❌ [loadMappings] exam 또는 exam.id가 없음');
        return
      }
      try {
        console.log('✅ [loadMappings] API 호출 시작', `/api/exam/${this.exam.id}/question-member-mappings/`);
        const response = await axios.get(`/api/exam/${this.exam.id}/question-member-mappings/`)
        this.mappings = response.data
        console.log('✅ [loadMappings] API 호출 성공');
      } catch (error) {
        console.error('❌ [loadMappings] API 호출 실패:', error);
        debugLog('매핑 목록 로드 실패:', error, 'error')
        // 매핑이 없을 수도 있으므로 에러를 표시하지 않음
      }
    },
    async loadLatestResult(examId) {
      try {
        debugLog('=== loadLatestResult 시작 ===', examId);
        
        // 인증되지 않은 사용자는 최신 결과를 로드하지 않음
        if (!this.isAuthenticated) {
          debugLog('인증되지 않은 사용자 - 최신 결과 로드 건너뜀');
          this.latestResult = null;
          this.resultDetails = [];
          return;
        }
        
        const response = await axios.get(`/api/exam-results/?exam_id=${examId}&latest=true`)
        debugLog('API 응답:', response.data);
        
        // 페이지네이션된 응답에서 첫 번째 결과 추출
        let latestResult = null;
        if (Array.isArray(response.data)) {
          latestResult = response.data[0];
        } else if (response.data.results && response.data.results.length > 0) {
          latestResult = response.data.results[0];
        } else {
          latestResult = response.data;
        }
        debugLog('추출된 latestResult:', latestResult);
        debugLog('latestResult.details:', latestResult ? latestResult.details : 'latestResult null');
        debugLog('latestResult 구조:', latestResult ? Object.keys(latestResult) : 'latestResult null');
        
        this.latestResult = latestResult
        
        // resultDetails 설정 - details가 없으면 빈 배열로 초기화
        if (latestResult && latestResult.details && latestResult.details.length > 0) {
          this.resultDetails = latestResult.details;
        } else {
          // details가 없으면 빈 배열로 설정
          this.resultDetails = [];
          debugLog('⚠️ latestResult.details가 없거나 비어있음');
        }

        debugLog('설정된 this.latestResult:', this.latestResult);
        debugLog('설정된 this.resultDetails:', this.resultDetails);
        debugLog('resultDetails 길이:', this.resultDetails.length);

        // details가 없으면 question-statistics API 사용
        if (!this.resultDetails || this.resultDetails.length === 0) {
          debugLog('resultDetails가 비어있음 - question-statistics API 사용');
          try {
            // 이미 로드된 questionStatistics 사용
            if (this.questionStatistics && this.questionStatistics.length > 0) {
              // questionStatistics 구조 확인
              debugLog('questionStatistics 첫 번째 항목 구조:', this.questionStatistics[0]);
              debugLog('questionStatistics 첫 번째 항목 키들:', Object.keys(this.questionStatistics[0]));
              
              // questionStatistics를 resultDetails 형태로 변환
              // 각 문제별로 total_attempts만큼 반복하여 시도 기록 생성
              let allAttempts = [];
              this.questionStatistics.forEach(stat => {
                // 해당 문제를 total_attempts만큼 반복
                for (let i = 0; i < stat.total_attempts; i++) {
                  // i < correct_attempts이면 정답, 아니면 오답
                  const is_correct = i < stat.correct_attempts;
                  
                  allAttempts.push({
                    question: { id: stat.question_id }, // question_id만 있으면 됨
                    is_correct: is_correct,
                    user_answer: '', // API에서 제공되지 않음
                    elapsed_seconds: 0 // API에서 제공되지 않음
                  });
                }
              });
              
              this.resultDetails = allAttempts;
              debugLog('questionStatistics로 변환된 resultDetails:', this.resultDetails);
              debugLog('resultDetails 길이:', this.resultDetails.length);
              debugLog('총 시도 횟수:', allAttempts.length);
              debugLog('총 맞춘 횟수:', allAttempts.filter(detail => detail.is_correct).length);
            } else {
              debugLog('questionStatistics가 비어있음 - 통계 초기화');
              this.resultDetails = [];
              // latestResult도 초기화 (삭제 후 상태 반영)
              this.latestResult = null;
            }
          } catch (error) {
            debugLog('questionStatistics 변환 실패:', error, 'error');
            this.resultDetails = [];
            this.latestResult = null;
          }
        }

        // 실제 시험 결과에 포함된 문제 ID들 추출
        this.resultQuestionIds = this.resultDetails.map(detail => detail.question.id)
        debugLog('실제 시험 결과에 포함된 문제 ID들:', this.resultQuestionIds)
        
        // 최신 결과 로드 후 수동 계산
        this.calculateExamStats()
      } catch (error) {
        debugLog('최신 결과 불러오기 실패:', error, 'error')
        this.latestResult = null
        this.resultDetails = []
        this.resultQuestionIds = []
      }
    },
    async loadVoiceInterviewResultsCount(examId) {
      try {
        if (!this.isAuthenticated || !examId) {
          this.voiceInterviewResultsCount = 0
          return
        }
        
        const response = await axios.get(`/api/exam/${examId}/voice-interview-results/`, {
          params: { page_size: 1 }
        })
        
        this.voiceInterviewResultsCount = response.data.total_count || 0
        debugLog('Voice Interview 결과 개수:', this.voiceInterviewResultsCount)
      } catch (error) {
        debugLog('Voice Interview 결과 개수 조회 실패:', error, 'error')
        this.voiceInterviewResultsCount = 0
      }
    },
    getMappedMember(questionId) {
      const mapping = this.mappings.find(m => m.question.id === questionId)
      return mapping ? mapping.member : null
    },
    async loadQuestionStatistics(examId, forceRefresh = false) {
      debugLog('문제별 정답 통계 로드 시작', { examId, forceRefresh })
      try {
        // 캐시 무효화를 위해 타임스탬프 추가
        const timestamp = Date.now()
        const config = forceRefresh ? {
          headers: {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache'
          }
        } : {}
        const response = await axios.get(`/api/exam/${examId}/question-statistics/?t=${timestamp}`, config)
        debugApi('GET', `/api/exam/${examId}/question-statistics/`, null, response.data, response.status)
        
        // response.data가 배열인지 확인하고, 배열이 아니면 빈 배열로 설정
        if (Array.isArray(response.data)) {
          this.questionStatistics = response.data
        } else if (response.data && response.data.results && Array.isArray(response.data.results)) {
          // 페이지네이션 응답 형식인 경우
          this.questionStatistics = response.data.results
        } else {
          // 배열이 아닌 경우 빈 배열로 설정
          debugLog('⚠️ questionStatistics 응답이 배열이 아님:', typeof response.data, response.data)
          this.questionStatistics = []
        }
        debugObject('questionStatistics', { count: this.questionStatistics.length })
        
        // 문제별 통계 로깅 제거 (너무 많은 로그 출력 방지)
        
        debugLog('문제별 정답 통계 로드 완료')
        
        // 통계 로드 후 수동 계산
        this.calculateExamStats()
      } catch (error) {
        debugLog('문제별 정답 통계 로드 실패', error, 'error')
        this.questionStatistics = []
      }
    },
    async loadMemberMappings(examId) {
      console.log('🔍 [loadMemberMappings] 함수 호출됨', {
        isAuthenticated: this.isAuthenticated,
        examId: examId,
        stackTrace: new Error().stack
      });
      if (!this.isAuthenticated) {
        console.log('❌ [loadMemberMappings] 인증되지 않은 사용자 - Member-Question Mapping 로드 건너뜀');
        debugLog('인증되지 않은 사용자 - Member-Question Mapping 로드 건너뜀');
        this.memberMappings = [];
        return;
      }
      debugLog('Member-Question Mapping 로드 시작', { examId })
      try {
        console.log('✅ [loadMemberMappings] API 호출 시작', `/api/exam/${examId}/question-member-mappings/`);
        const response = await axios.get(`/api/exam/${examId}/question-member-mappings/`)
        debugApi('GET', `/api/exam/${examId}/question-member-mappings/`, null, response.data, response.status)
        
        this.memberMappings = response.data
        debugObject('memberMappings', { count: this.memberMappings.length })
        console.log('✅ [loadMemberMappings] API 호출 성공');
        
        // 매핑 정보 로깅 제거 (너무 많은 로그 출력 방지)
        
        debugLog('Member-Question Mapping 로드 완료')
      } catch (error) {
        console.error('❌ [loadMemberMappings] API 호출 실패:', error);
        debugLog('Member-Question Mapping 로드 실패', error, 'error')
        this.memberMappings = []
      }
    },
    
    // 사용자 프로필 언어 가져오기 (캐시 사용)
    async getUserProfileLanguage() {
      // 캐시에 있으면 반환
      if (this.userProfileLanguage) {
        return this.userProfileLanguage
      }
      
      try {
        if (this.isAuthenticated) {
          const response = await axios.get('/api/user-profile/')
          const language = response.data.language || 'en'
          // 캐시에 저장 (중요: this.userProfileLanguage에 저장)
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
    
    // 원본 시험 정보 로드 비활성화 (무한 호출 방지)
    async loadOriginalExamsForQuestions() {
      debugLog('원본 시험 정보 로드 비활성화됨 (무한 호출 방지)')
      return
      
      // try {
      //   debugLog('원본 시험 정보 로드 시작')
      //   
      //   // 각 문제에 대해 원본 시험 정보 로드
      //   for (const question of this.questions) {
      //     try {
      //       const response = await axios.get(`/api/questions/${question.id}/original-exams/`)
      //       
      //       // 문제 객체에 원본 시험 정보 추가
      //       this.$set(question, 'original_exams', [])
      //     } catch (error) {
      //       debugLog(`문제 ${question.id} 원본 시험 정보 로드 실패:`, error, 'error')
      //       this.$set(question, 'original_exams', [])
      //     }
      //   }
      //   
      //   debugLog('원본 시험 정보 로드 완료')
      // } catch (error) {
      //   debugLog('원본 시험 정보 로드 실패:', error, 'error')
      // }
    },
    getQuestionStatistics(questionId) {
      const stats = this.questionStatistics.find(s => String(s.question_id) === String(questionId))
      return stats || null
    },
    getQuestionMemberMappings(questionId) {
      const mappings = this.memberMappings.filter(m => String(m.question.id) === String(questionId))
      return mappings || []
    },

    // 현재 사용자 언어에 맞는 시험 제목 반환 (computed property로 변경)
    getLocalizedTitle(exam) {
      if (!exam) return ''
      
      // 사용자 프로필 언어 가져오기 (동기적으로, 캐시 우선)
      let userLang = this.userProfileLanguage
      
      // userProfileLanguage가 없으면 동적으로 가져오기 (동기적으로는 불가능하므로 기본값 사용)
      if (!userLang) {
        console.warn('[ExamDetail] userProfileLanguage가 null입니다. 기본값 "en" 사용')
        userLang = 'en'
      }
      
      // 사용자 언어에 맞는 언어별 필드가 있으면 우선 사용
      // 백엔드 display_title이 예상과 다를 경우를 대비한 방어적 로직
      if (userLang === 'zh' && exam.title_zh && exam.title_zh.trim()) {
        // display_title이 title_zh와 다르면 title_zh 사용 (백엔드 버그 우회)
        if (!exam.display_title || exam.display_title !== exam.title_zh) {
          forceDebugLog(`⚠️ [ExamDetail] getLocalizedTitle - display_title("${exam.display_title}")과 title_zh("${exam.title_zh}") 불일치, title_zh 사용`)
          return exam.title_zh
        }
      } else if (userLang === 'ko' && exam.title_ko && exam.title_ko.trim()) {
        if (!exam.display_title || exam.display_title !== exam.title_ko) {
          forceDebugLog(`⚠️ [ExamDetail] getLocalizedTitle - display_title("${exam.display_title}")과 title_ko("${exam.title_ko}") 불일치, title_ko 사용`)
          return exam.title_ko
        }
      } else if (userLang === 'es' && exam.title_es && exam.title_es.trim()) {
        if (!exam.display_title || exam.display_title !== exam.title_es) {
          forceDebugLog(`⚠️ [ExamDetail] getLocalizedTitle - display_title("${exam.display_title}")과 title_es("${exam.title_es}") 불일치, title_es 사용`)
          return exam.title_es
        }
      } else if (userLang === 'ja' && exam.title_ja && exam.title_ja.trim()) {
        if (!exam.display_title || exam.display_title !== exam.title_ja) {
          forceDebugLog(`⚠️ [ExamDetail] getLocalizedTitle - display_title("${exam.display_title}")과 title_ja("${exam.title_ja}") 불일치, title_ja 사용`)
          return exam.title_ja
        }
      } else if (userLang === 'en' && exam.title_en && exam.title_en.trim()) {
        if (!exam.display_title || exam.display_title !== exam.title_en) {
          forceDebugLog(`⚠️ [ExamDetail] getLocalizedTitle - display_title("${exam.display_title}")과 title_en("${exam.title_en}") 불일치, title_en 사용`)
          return exam.title_en
        }
      }
      
      // display_title 사용 (백엔드에서 올바르게 처리된 경우)
      if (exam.display_title && exam.display_title.trim()) {
        forceDebugLog(`✅ [ExamDetail] getLocalizedTitle - display_title 사용: "${exam.display_title}"`)
        return exam.display_title
      }
      
      // display_title도 없으면 폴백 로직 사용
      const userLanguage = this.$i18n.locale || 'ko'
      if (userLanguage === 'ko') {
        return exam.title_ko || exam.title_en || exam.title_zh || exam.title_es || exam.title || ''
      } else if (userLanguage === 'zh') {
        return exam.title_zh || exam.title_en || exam.title_ko || exam.title_es || exam.title_ja || exam.title || ''
      } else if (userLanguage === 'es') {
        return exam.title_es || exam.title_en || exam.title_ko || exam.title_zh || exam.title_ja || exam.title || ''
      } else if (userLanguage === 'ja') {
        return exam.title_ja || exam.title_en || exam.title_ko || exam.title_es || exam.title_zh || exam.title || ''
      } else {
        return exam.title_en || exam.title_zh || exam.title_ko || exam.title_es || exam.title_ja || exam.title || ''
      }
    },
    
    // 현재 사용자 언어에 맞는 시험 설명 반환 (computed property로 변경)
    getLocalizedDescription(exam) {
      if (!exam) return ''
      
      return getLocalizedContentWithI18n(
        exam,
        'description',
        this.$i18n,
        this.userProfileLanguage,
        ''
      )
    },
    
    toggleExamInfo() {
      this.showExamInfo = !this.showExamInfo;
    },
    
    toggleEditInfo() {
      if (this.isEditingInfo) {
        // 이미 편집 모드라면 취소
        this.cancelEditInfo();
      } else {
        // 편집 모드가 아니라면 시작
        this.startEditInfo();
      }
    },
    
    startEditInfo() {
      this.isEditingInfo = true;
      this.editingTitle = this.localizedExamTitle || '';
      this.editingDescription = this.localizedExamDescription || '';
      this.editingVersion = this.exam ? (this.exam.version_number || 1) : 1;
              this.editingIsPublic = this.exam ? this.exam.is_public : true;
        this.editingForceAnswer = this.exam ? this.exam.force_answer : false;
      this.editingVoiceModeEnabled = this.exam ? this.exam.voice_mode_enabled : false;
      this.editingAIMockInterview = this.exam ? this.exam.ai_mock_interview : false;
      this.editingAgeRating = this.exam ? (this.exam.age_rating || '17+') : '17+';
      // 사용자의 등급 이하로 제한
      const user = authService.getUserSync()
      if (user && user.age_rating) {
        const ratingOrder = { '4+': 1, '9+': 2, '12+': 3, '17+': 4 }
        const userRatingOrder = ratingOrder[user.age_rating] || 4
        const currentRatingOrder = ratingOrder[this.editingAgeRating] || 4
        if (currentRatingOrder > userRatingOrder) {
          // 현재 선택된 등급이 사용자 등급보다 높으면 사용자 등급으로 제한
          this.editingAgeRating = user.age_rating
        }
      }
      this.editingExamDifficulty = this.exam ? (this.exam.exam_difficulty || 5) : 5;
      this.editingSupportedLanguages = this.exam ? (this.exam.supported_languages || '') : '';
      // created_at을 datetime-local 포맷으로 변환
      if (this.exam && this.exam.created_at) {
        const d = new Date(this.exam.created_at);
        this.editingCreatedAt = d.toISOString().slice(0, 16);
      } else {
        this.editingCreatedAt = '';
      }
    },
    async saveInfo() {
      if (!this.exam || this.isSaving) return;
      
      this.isSaving = true;
      try {
        const payload = {
          title: this.editingTitle,
          description: this.editingDescription,
          version_number: this.editingVersion,
          created_at: this.editingCreatedAt ? new Date(this.editingCreatedAt).toISOString() : undefined,
          is_public: this.editingIsPublic,
          force_answer: this.editingForceAnswer,
          voice_mode_enabled: this.editingVoiceModeEnabled,
          ai_mock_interview: this.editingAIMockInterview,
          age_rating: this.editingAgeRating ? String(this.editingAgeRating).trim() : '17+',
          exam_difficulty: this.editingExamDifficulty || 5
        };
        
        // admin일 때만 supported_languages 포함
        if (this.isAdmin) {
          payload.supported_languages = this.editingSupportedLanguages || '';
          debugLog('Supported Languages 저장:', payload.supported_languages);
        }
        debugLog('saveInfo payload:', payload);
        const response = await axios.patch(`/api/exam/${this.exam.id}/update/`, payload);
        this.exam = response.data;
        
        // 파싱된 문제가 있으면 시험에 추가
        if (this.parsedProblems && this.parsedProblems.length > 0) {
          await this.addParsedProblemsToExam();
          
          // 파싱된 문제 목록 초기화
          this.parsedProblems = []
          this.leetcodeProblems = ''
          this.pasteProblemMode = false
        }
        
        this.isEditingInfo = false;
        
        // 시험 관리 화면 새로고침 플래그 설정
        sessionStorage.setItem('refreshExamManagement', 'true');
        
        this.showSuccessToast(this.$t('examDetail.alerts.examInfoUpdated'));
      } catch (error) {
        debugLog('시험 정보 수정 실패:', error, 'error');
        this.showErrorToast(this.$t('examDetail.alerts.examInfoUpdateFailed'));
      } finally {
        this.isSaving = false;
      }
    },
    cancelEditInfo() {
      this.isEditingInfo = false;
    },
    
    async importFromConnectedFile() {
      if (!this.exam || !this.exam.file_name) {
        this.showErrorToast(this.safeTranslate('examDetail.noConnectedFile', '연결된 파일이 없습니다.'));
        return;
      }
      
      // 모던한 확인 다이얼로그 사용
      this.showConfirmModal(
        this.safeTranslate('examDetail.importFromConnectedFile', '연결된 파일에서 가져오기'),
        this.safeTranslate('examDetail.confirmImportMessage', '연결된 파일로부터 새로운 문제만 가져오시겠습니까? 기존에 있는 문제는 건너뛰고 추가된 문제만 가져옵니다.'),
        async (confirmed) => {
          if (confirmed) {
            try {
              this.isImporting = true;
              
              const response = await axios.post(`/api/exam/${this.exam.id}/import-from-connected-file/`);
              
              // 통계 정보 표시
              const stats = response.data.stats;
              
              if (stats) {
                if (stats.imported > 0) {
                  // 새로 가져온 문제가 있는 경우
                  this.showSuccessToast(this.safeTranslate('examDetail.importSuccess', '연결된 파일로부터 문제 가져오기가 완료되었습니다.'));
                  let message = `총 ${stats.total_rows}개 행 중 ${stats.imported}개 가져옴`;
                  if (stats.skipped > 0) {
                    message += `, ${stats.skipped}개 건너뜀`;
                  }
                  if (stats.errors > 0) {
                    message += `, ${stats.errors}개 오류`;
                  }
                  this.showInfoToast(message);
                } else if (stats.skipped > 0) {
                  // 모든 문제가 이미 존재하는 경우
                  this.showInfoToast(`모든 문제가 이미 시험에 존재합니다. 총 ${stats.total_rows}개 행 중 ${stats.skipped}개 건너뜀`);
                } else {
                  // 기타 경우
                  this.showInfoToast(`처리 완료: 총 ${stats.total_rows}개 행`);
                }
              }
              
              // 문제 목록 새로고침
              await this.loadQuestions(this.exam.id, true);
              
              // 시험 정보 새로고침
              await this.loadExam(this.exam.id);
              
              // 시험 관리 화면 새로고침 플래그 설정
              sessionStorage.setItem('refreshExamManagement', 'true');
              
            } catch (error) {
              debugLog('연결된 파일 가져오기 실패:', error, 'error');
              this.showErrorToast(this.safeTranslate('examDetail.importFailed', '연결된 파일로부터 문제 가져오기에 실패했습니다.'));
            } finally {
              this.isImporting = false;
            }
          }
        },
        'info'
      );
    },

    async deleteSelectedQuestionResultsGlobal() {
      debugLog('=== deleteSelectedQuestionResultsGlobal 시작 ===');
      debugLog('selectedQuestions:', this.selectedQuestions);
      debugLog('selectedQuestions.length:', this.selectedQuestions ? this.selectedQuestions.length : 'null');
      
      if (this.selectedQuestions.length === 0) {
        this.showErrorToast(this.$t('examDetail.alerts.selectQuestionToDelete'))
        return
      }

      // 모던한 확인 다이얼로그 사용
      const title = this.$t('examDetail.confirmDeleteGlobalTitle');
      const message = this.$t('examDetail.confirmDeleteGlobalMessage', { count: this.selectedQuestions.length });
      
      debugLog('확인 다이얼로그 제목:', title);
      debugLog('확인 다이얼로그 메시지:', message);
      debugLog('count 파라미터:', this.selectedQuestions.length);
      debugLog('safeTranslate 호출 결과:', { title, message });
      
      this.showConfirmModal(
        title,
        message,
        async (confirmed) => {
          if (confirmed) {
            try {
              const response = await axios.delete('/api/delete-question-results-global/', {
                data: {
                  question_ids: this.selectedQuestions
                }
              })

              debugLog('문제 전체 기록 삭제 응답:', response.data)

              // 프로젝트 표준: 프론트엔드에서 번역 처리
              this.showSuccessToast(this.$t('examDetail.alerts.questionResultsDeleted', { count: response.data.deleted_count }))

              // 선택 초기화
              this.selectedQuestions = []

              // 클라이언트 캐시 정리
              this.clearClientCache()

              // 모든 캐시 초기화 및 강제 새로고침
              this.questions = [] // 목록 초기화
              this.questionStatistics = [] // 통계 초기화

              // 브라우저 캐시 무효화를 위한 강제 새로고침
              debugLog('삭제 후 데이터 새로고침 시작')
              await this.loadQuestions(this.exam.id, true)
              await this.loadQuestionStatistics(this.exam.id, true)
              await this.loadLatestResult(this.exam.id, true)
              debugLog('삭제 후 데이터 새로고침 완료')

              // 시험 관리 화면 통계 업데이트 플래그 설정
              sessionStorage.setItem('refreshExamManagement', 'true')

              // 현재 필터 상태를 URL 파라미터로 보존
              this.preserveFilterStateInURL()

            } catch (error) {
              debugLog('문제 전체 기록 삭제 실패:', error, 'error')
              this.showErrorToast(this.$t('examDetail.alerts.deleteAllQuestionResultFailed'))
            }
          }
        },
        'error'
      )
    },
    async deleteAllQuestionResults() {
      debugLog('=== deleteAllQuestionResults 시작 ===');
      debugLog('selectedQuestions:', this.selectedQuestions);
      debugLog('selectedQuestions.length:', this.selectedQuestions ? this.selectedQuestions.length : 'null');
      
      if (!this.exam) {
        this.showErrorToast(this.$t('examDetail.alerts.noExamInfo'))
        return
      }

      // 모던한 확인 다이얼로그 사용
      const title = this.$t('examDetail.confirmDeleteAllResultsTitle');
      const message = this.$t('examDetail.confirmDeleteAllResultsMessage');
      
      debugLog('확인 다이얼로그 제목:', title);
      debugLog('확인 다이얼로그 메시지:', message);
      debugLog('safeTranslate 호출 결과:', { title, message });
      
      this.showConfirmModal(
        title,
        message,
        async (confirmed) => {
          if (confirmed) {
            try {
              const response = await axios.delete('/api/delete-question-results/', {
                data: {
                  exam_id: this.exam.id,
                  delete_all: true
                }
              })

              debugLog('모든 문제 풀이 결과 삭제 응답:', response.data)

              // 프로젝트 표준: 프론트엔드에서 번역 처리
              this.showSuccessToast(this.$t('examDetail.alerts.questionResultsDeleted', { count: response.data.deleted_count }))

              // 선택 초기화
              this.selectedQuestions = []

              // 클라이언트 캐시 정리
              this.clearClientCache()

              // 모든 캐시 초기화 및 강제 새로고침
              this.questions = [] // 목록 초기화
              this.questionStatistics = [] // 통계 초기화

              // 브라우저 캐시 무효화를 위한 강제 새로고침
              debugLog('삭제 후 데이터 새로고침 시작')
              await this.loadQuestions(this.exam.id, true)
              await this.loadQuestionStatistics(this.exam.id, true)
              await this.loadLatestResult(this.exam.id, true)
              debugLog('삭제 후 데이터 새로고침 완료')

              // 시험 관리 화면 통계 업데이트 플래그 설정
              sessionStorage.setItem('refreshExamManagement', 'true')

              // 현재 필터 상태를 URL 파라미터로 보존
              this.preserveFilterStateInURL()

            } catch (error) {
              debugLog('모든 문제 풀이 결과 삭제 실패:', error, 'error')
              this.showErrorToast(this.$t('examDetail.alerts.deleteAllQuestionResultFailed'))
            }
          }
        },
        'error'
      )
    },
    async deleteExam() {
      if (!this.exam) {
        this.showErrorToast(this.$t('examDetail.alerts.noExamInfo'))
        return
      }

      // 모던한 확인 다이얼로그 사용
      this.showConfirmModal(
        this.safeTranslate('examDetail.confirmDeleteExamTitle', '시험 삭제 확인'),
        this.safeTranslate('examDetail.confirmDeleteExamMessage', '이 시험을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.'),
        async (confirmed) => {
          if (confirmed) {
            try {
              const response = await axios.delete(`/api/exam/${this.exam.id}/`)
              
              debugLog('시험 삭제 응답:', response.data)
              
              this.showSuccessToast(this.$t('examDetail.alerts.examDeleted'))
              
              // 시험 관리 화면으로 이동
              this.$router.push('/exam-management')
              
            } catch (error) {
              debugLog('시험 삭제 실패:', error, 'error')
              this.showErrorToast(this.$t('examDetail.alerts.deleteExamFailed'))
            }
          }
        },
        'error'
      )
    },
    async deleteSelectedQuestions() {
      if (!this.exam || this.selectedQuestions.length === 0) {
        this.showErrorToast(this.safeTranslate('examDetail.alerts.noQuestionsSelected', '선택된 문제가 없습니다.'))
        return
      }

      // NotificationSystem을 사용한 확인 다이얼로그
      this.showConfirmModal(
        this.$t('examDetail.confirmDeleteTitle'),
        this.$t('examDetail.confirmDeleteMessage', { count: this.selectedQuestions.length }),
        async (confirmed) => {
          if (confirmed) {
            try {
              const response = await axios.post('/api/delete-questions/', {
                question_ids: this.selectedQuestions,
                exam_id: this.exam.id
              });
              
              debugLog('문제 삭제 응답:', response.data);
              
              this.showSuccessToast(this.$t('examDetail.alerts.questionsDeleted', { count: response.data.deleted_count }))
              
              // 선택 초기화
              this.selectedQuestions = []
              
              // 클라이언트 캐시 정리
              this.clearClientCache()
              
              // 모든 캐시 초기화 및 강제 새로고침
              this.questions = [] // 목록 초기화
              this.questionStatistics = [] // 통계 초기화
              
              // 브라우저 캐시 무효화를 위한 강제 새로고침
              await this.loadQuestions(this.exam.id, true)
              await this.loadQuestionStatistics(this.exam.id, true)
              
              // 시험 관리 화면 통계 업데이트 플래그 설정
              sessionStorage.setItem('refreshExamManagement', 'true')
              
              // 현재 필터 상태를 URL 파라미터로 보존
              this.preserveFilterStateInURL()
              
            } catch (error) {
              debugLog('문제 삭제 실패:', error, 'error')
              this.showErrorToast(this.safeTranslate('examDetail.alerts.deleteQuestionsFailed', '문제 삭제에 실패했습니다.'))
            }
          }
        },
        'warning'
      )
    },
    getStoredFilter(key, defaultValue) {
      try {
        const examId = this.exam ? this.exam.id : 'default'
        const stored = sessionStorage.getItem(`examDetail_${examId}_${key}`)
        return stored !== null ? stored : defaultValue
      } catch (error) {
        debugLog('sessionStorage 읽기 오류:', error, 'error')
        return defaultValue
      }
    },
    setStoredFilter(key, value) {
      try {
        const examId = this.exam ? this.exam.id : 'default'
        sessionStorage.setItem(`examDetail_${examId}_${key}`, value)
      } catch (error) {
        debugLog('sessionStorage 쓰기 오류:', error, 'error')
      }
    },
    preserveFilterStateInURL() {
      // 현재 필터 상태를 URL 파라미터로 보존
      const currentUrl = new URL(window.location.href)
      
      // 기존 필터 파라미터들을 보존
      if (this.searchTerm) currentUrl.searchParams.set('searchTerm', this.searchTerm)
      if (this.difficultyFilter) currentUrl.searchParams.set('difficultyFilter', this.difficultyFilter)
      if (this.answerFilter) currentUrl.searchParams.set('answerFilter', this.answerFilter)
      if (this.favoriteFilter) currentUrl.searchParams.set('favoriteFilter', this.favoriteFilter)
      if (this.ignoreFilter) currentUrl.searchParams.set('ignoreFilter', this.ignoreFilter)
      if (this.groupIdFilter) currentUrl.searchParams.set('groupIdFilter', this.groupIdFilter)
      if (this.originalExamFilter) currentUrl.searchParams.set('originalExamFilter', this.originalExamFilter)
      if (this.sortBy) currentUrl.searchParams.set('sortBy', this.sortBy)
      if (this.sortOrder) currentUrl.searchParams.set('sortOrder', this.sortOrder)
      
      // 타임스탬프 추가
      currentUrl.searchParams.set('t', Date.now())
      
      // URL 업데이트
      window.history.replaceState({}, '', currentUrl.toString())
    },
    goToExamManagement() {
      // 시험 관리 화면으로 이동하면서 새로고침 플래그 설정
      sessionStorage.setItem('refreshExamManagement', 'true')
      this.$router.push('/exam-management')
    },
    setSort(column) {
      if (this.sortBy === column) {
        this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
      } else {
        this.sortBy = column;
        this.sortOrder = 'asc';
      }
      
      // sessionStorage에 저장
      this.setStoredFilter('sortBy', this.sortBy)
      this.setStoredFilter('sortOrder', this.sortOrder)
      
      // 강제로 computed 속성 재계산
      this.$forceUpdate()
    },
    async handlePageFocus() {
      debugLog('페이지 포커스 감지 - 통계 새로고침')
      if (this.exam && this.exam.id) {
        await this.loadQuestionStatistics(this.exam.id)
      }
    },
    // 문제 이동 관련 메서드들
    async loadAvailableExams() {
      try {
        const response = await axios.get('/api/exams/')
        this.availableExams = response.data.results || response.data
      } catch (error) {
        debugLog('시험 목록 로드 실패:', error, 'error')
        this.availableExams = []
      }
    },
    async moveQuestionsToExam() {
      if (!this.selectedTargetExamId || this.selectedQuestions.length === 0) return
      
      this.showConfirmModal(
        this.$t('confirm.questionMoveTitle'),
        this.$t('confirm.questionMoveMessage', { count: this.selectedQuestions.length }),
        async (confirmed) => {
          if (confirmed) {
            try {
              await axios.post('/api/move-questions/', {
                from_exam_id: this.exam.id,
                to_exam_id: this.selectedTargetExamId,
                question_ids: this.selectedQuestions
              })
              this.showSuccessToast(this.$t('examDetail.alerts.questionMoveComplete'))
              this.selectedQuestions = []
              await this.loadExam(this.exam.id)
            } catch (error) {
              this.showErrorToast(this.$t('examDetail.alerts.questionMoveFailed'))
            }
          }
        },
        'warning'
      )
    },
    async copyQuestionsToExam() {
      if (!this.selectedTargetExamId || this.selectedQuestions.length === 0) return
      
      this.showConfirmModal(
        this.$t('confirm.questionCopyTitle'),
        this.$t('confirm.questionCopyMessage', { count: this.selectedQuestions.length }),
        async (confirmed) => {
          if (confirmed) {
            try {
              await axios.post('/api/copy-questions/', {
                from_exam_id: this.exam.id,
                to_exam_id: this.selectedTargetExamId,
                question_ids: this.selectedQuestions
              })
              this.showSuccessToast(this.$t('examDetail.alerts.questionCopyComplete'))
              this.selectedQuestions = []
              await this.loadExam(this.exam.id)
            } catch (error) {
              this.showErrorToast(this.$t('examDetail.alerts.questionCopyFailed'))
            }
          }
        },
        'info'
      )
    },

    async applyGroupIdToSelected() {
      if (!this.groupIdInput || this.selectedQuestions.length === 0) return;
      try {
        // PATCH 요청으로 일괄 업데이트
        await axios.patch('/api/questions/bulk-update-group/', {
          question_ids: this.selectedQuestions,
          group_id: this.groupIdInput
        });
        // 프론트엔드 데이터 갱신
        this.questions = this.questions.map(q =>
          this.selectedQuestions.includes(q.id)
            ? { ...q, group_id: this.groupIdInput }
            : q
        );
        this.groupIdInput = '';
        this.showSuccessToast(this.$t('examDetail.alerts.groupApplied'));
      } catch (error) {
        this.showErrorToast(this.$t('examDetail.alerts.groupApplyFailed'));
      }
    },
    async downloadExcel() {
      if (!this.exam || !this.questions.length) {
        this.showErrorToast(this.$t('examDetail.alerts.noQuestionToDownload'))
        return;
      }
      
      debugLog('downloadExcel 시작 - 문제 수:', this.questions.length)
      
      try {
        // 엑셀 다운로드용 상세 데이터 로드
        debugLog('엑셀 다운로드용 상세 데이터 로드 시작')
        await this.loadQuestionsForExcel(this.exam.id)
        debugLog('엑셀 다운로드용 상세 데이터 로드 완료')
        
        // 첫 번째 문제만 간단하게 로깅
        if (this.questions.length > 0) {
          const firstQ = this.questions[0]
          debugLog('첫 번째 문제 엑셀 데이터:', {
            title: firstQ.localized_title,
            content: firstQ.localized_content ? '있음' : '없음',
            answer: firstQ.localized_answer ? '있음' : '없음',
            explanation: firstQ.localized_explanation ? '있음' : '없음'
          })
        }
      } catch (error) {
        debugLog('엑셀 다운로드용 데이터 로드 실패:', error, 'error')
        this.showErrorToast(this.$t('examDetail.alerts.loadQuestionListFailed'))
        return
      }
      
      // 컬럼명 및 데이터 매핑
      const headers = [
        this.$t('examDetail.questionId'), 
        this.$t('examDetail.title'), 
        this.$t('examDetail.questionContent'), 
        this.$t('examDetail.answer'), 
        this.$t('examDetail.description'), 
        this.$t('examDetail.difficulty'), 
        this.$t('examDetail.url'), 
        this.$t('examDetail.groupId')
      ];
      
      const data = this.questions.map((q, index) => {
        const row = [
          q.csv_id || '',
          q.localized_title || '',
          q.localized_content || '',
          q.localized_answer || '',
          q.localized_explanation || '',
          q.difficulty ? (() => {
            const diff = q.difficulty.toLowerCase();
            if (diff === 'easy') return 'Easy';
            if (diff === 'medium') return 'Medium';
            if (diff === 'hard') return 'Hard';
            return q.difficulty.charAt(0).toUpperCase() + q.difficulty.slice(1).toLowerCase();
          })() : '',
          q.url || '',
          q.group_id || ''
        ]
        
        // 첫 번째 문제만 로깅
        if (index === 0) {
          debugLog(`첫 번째 문제 엑셀 행:`, row)
        }
        
        return row
      })
      // 헤더 추가
      data.unshift(headers);
      // 워크시트/워크북 생성
      const ws = XLSX.utils.aoa_to_sheet(data);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, '문제목록');
      // 파일명: Connected File이 있으면 그 파일명 사용, 없으면 시험 제목 사용
      let filename;
      if (this.exam.file_name) {
        // Connected File이 있으면 그 파일명 사용 (확장자 제거 후 .xlsx 추가)
        const baseName = this.exam.file_name.replace(/\.[^/.]+$/, ''); // 확장자 제거
        filename = baseName + '.xlsx';
      } else {
        // Connected File이 없으면 시험 제목 사용
        filename = (this.getLocalizedTitle(this.exam) || '문제목록') + '.xlsx';
      }
      // 엑셀 파일 생성 및 다운로드
      const wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
      saveAs(new Blob([wbout], { type: 'application/octet-stream' }), filename);
    },
    downloadExcelFile() {
      this.downloadExcel();
    },
    getSortIcon(column) {
      if (this.sortBy === column) {
        return this.sortOrder === 'asc' ? 'fas fa-sort-up' : 'fas fa-sort-down';
      }
      return 'fas fa-sort';
    },
    goToAddQuestion() {
      if (!this.exam || !this.exam.id) {
        this.showErrorToast(this.$t('examDetail.alerts.noExamInfo'));
        return;
      }
      this.$router.push(`/take-exam/${this.exam.id}?mode=add-question&returnTo=exam-detail`);
    },
    goToMemberManagement() {
      if (!this.selectedStudyId) {
        this.showErrorToast(this.$t('examDetail.alerts.selectStudyFirst'))
        return;
      }
      this.$router.push(`/member-management/${this.selectedStudyId}`);
    },
    async autoSelectStudyForExam() {
      if (!this.isAuthenticated) {
        console.log('❌ [autoSelectStudyForExam] 인증되지 않은 사용자 - 스터디 자동 선택 건너뜀');
        debugLog('인증되지 않은 사용자 - 스터디 자동 선택 건너뜀');
        return;
      }
      if (!this.exam || !this.exam.id) {
        return;
      }

      try {
        // 시험과 관련된 매핑 정보를 가져와서 스터디 찾기
        console.log('✅ [autoSelectStudyForExam] API 호출 시작', `/api/exam/${this.exam.id}/question-member-mappings/`);
        const response = await axios.get(`/api/exam/${this.exam.id}/question-member-mappings/`)
        const mappings = response.data
        console.log('✅ [autoSelectStudyForExam] API 호출 성공');

        if (mappings && mappings.length > 0) {
          // 첫 번째 매핑에서 스터디 정보 추출
          const firstMapping = mappings[0]
          if (firstMapping.member && firstMapping.member.study) {
            const studyId = firstMapping.member.study
            debugLog('자동 선택된 스터디 ID:', studyId)

            // 스터디 목록에서 해당 스터디 찾기
            const study = this.studies.find(s => s.id === studyId)
            if (study) {
              this.selectedStudyId = studyId
              // sessionStorage에 저장
              sessionStorage.setItem(`exam_${this.exam.id}_selectedStudyId`, studyId)
              const studyTitle = study.title_ko || study.title_en || study.title || '제목 없음';
              debugLog('스터디 자동 선택 완료:', studyTitle)

              // 스터디 멤버도 자동으로 로드
              await this.loadStudyMembers()
            }
          }
        }
      } catch (error) {
        debugLog('스터디 자동 선택 실패:', error, 'error')
        // 에러가 발생해도 사용자에게 알리지 않음 (선택사항이므로)
      }
    },
    restoreSelectedStudy() {
      if (!this.exam || !this.exam.id) {
        return;
      }

      // sessionStorage에서 저장된 스터디 ID 복원
      const savedStudyId = sessionStorage.getItem(`exam_${this.exam.id}_selectedStudyId`)
      if (savedStudyId && this.studies.length > 0) {
        const study = this.studies.find(s => s.id === savedStudyId)
        if (study) {
          this.selectedStudyId = savedStudyId
          const studyTitle = study.title_ko || study.title_en || study.title || '제목 없음';
          debugLog('저장된 스터디 복원 완료:', studyTitle)
          // 스터디 멤버도 로드
          this.loadStudyMembers()
        }
      }
    },
    // favorite과 무시 관련 메서드들 (이제 문제 목록 로드 시 함께 처리됨)
    // async loadFavoriteAndIgnoredQuestions() {
    //   // 이 메서드는 더 이상 사용하지 않음 (문제 목록 로드 시 함께 처리)


    // 번역 관련 메서드
    selectAllLanguages() {
      this.selectedLanguages = this.availableLanguages.map(lang => lang.code)
    },
    deselectAllLanguages() {
      this.selectedLanguages = []
    },
    async handleTranslateExam() {
      if (!this.exam || this.selectedLanguages.length === 0) return
      
      try {
        this.showTranslateModal = false
        this.showToastNotification(
          this.$t('examDetail.translateStarted') || '번역이 시작되었습니다.',
          'info'
        )
        
        // api.js의 인터셉터를 사용하여 CSRF 토큰 자동 추가
        const apiModule = await import('@/services/api')
        const api = apiModule.default || apiModule.api
        const { ensureCsrfToken } = apiModule
        
        if (!api) {
          throw new Error('API 인스턴스를 가져올 수 없습니다.')
        }
        
        debugLog('번역 API 호출 시작:', {
          examId: this.exam.id,
          targetLanguages: this.selectedLanguages
        })
        
        // CSRF 토큰을 명시적으로 확보 (콜백으로 처리하여 완료 후 API 호출)
        if (ensureCsrfToken) {
          debugLog('CSRF 토큰 확보 중...')
          await ensureCsrfToken()
          debugLog('CSRF 토큰 확보 완료')
        }
        
        const response = await api.post(`/api/exam/${this.exam.id}/translate/`, {
          target_languages: this.selectedLanguages
        })
        
        debugLog('번역 API 응답:', response.data)
        
        // 번역은 백그라운드로 처리되므로 즉시 완료 메시지 표시하지 않음
        // 대신 "번역이 시작되었습니다" 메시지만 표시
        // 실제 번역 완료는 사용자가 페이지를 새로고침하거나 다시 로드할 때 확인 가능
        
      } catch (error) {
        debugLog('번역 실패:', error, 'error')
        debugLog('번역 에러 상세:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status,
          statusText: error.response?.statusText
        })
        
        let errorMessage = this.$t('examDetail.translateFailed') || '번역 중 오류가 발생했습니다.'
        if (error.response?.data?.error) {
          errorMessage = error.response.data.error
        } else if (error.response?.status === 403) {
          errorMessage = this.$t('examDetail.translatePermissionDenied') || '번역 권한이 없습니다.'
        } else if (error.response?.status === 404) {
          errorMessage = this.$t('examDetail.translateExamNotFound') || '시험을 찾을 수 없습니다.'
        }
        
        this.showToastNotification(errorMessage, 'error')
      }
    },
    
    // AI 모의 인터뷰 관련 메서드
    async showAIMockInterviewDetail(question) {
      debugLog('🎤 [showAIMockInterviewDetail] 시작', {
        questionId: question?.id,
        questionTitle: question?.localized_title || question?.title
      })
      
      this.selectedQuestionForAI = question
      
      // 모바일 환경 감지
      debugLog('🎤 [showAIMockInterviewDetail] 모바일 환경 감지 시작')
      this.isMobileDevice = this.checkIsMobileDevice()
      debugLog('🎤 [showAIMockInterviewDetail] 모바일 환경 감지 결과:', {
        isMobileDevice: this.isMobileDevice,
        showVoiceInterview: this.showVoiceInterview,
        showAIMockInterviewModal: this.showAIMockInterviewModal
      })
      
      // 모바일 환경이면 바로 Voice Interview 모드로 전환
      if (this.isMobileDevice) {
        debugLog('🎤 [showAIMockInterviewDetail] 모바일 환경 감지됨 → Voice Interview 모드로 전환')
        
        this.showVoiceInterview = true
        this.showAIMockInterviewModal = true
        
        debugLog('🎤 [showAIMockInterviewDetail] 상태 설정 완료', {
          showVoiceInterview: this.showVoiceInterview,
          showAIMockInterviewModal: this.showAIMockInterviewModal
        })
        
        // 기존 loadQuestions 메서드 재사용
        if (question.id) {
          debugLog('🎤 [showAIMockInterviewDetail] 문제 목록 로드 시작:', question.id)
          await this.loadQuestions(question.id, true)
          debugLog('🎤 [showAIMockInterviewDetail] 문제 목록 로드 완료')
        }
        
        // 번역 강제 로드
        debugLog('🎤 [showAIMockInterviewDetail] 번역 로드 시작')
        await this.$loadTranslations()
        debugLog('🎤 [showAIMockInterviewDetail] 번역 로드 완료')
        
        // Voice Interview에서도 프롬프트 텍스트를 사용하므로 초기화 필요
        debugLog('🎤 [showAIMockInterviewDetail] 모바일 환경 - 프롬프트 텍스트 초기화 시작')
        await this.initializePromptText()
        debugLog('🎤 [showAIMockInterviewDetail] 모바일 환경 - 프롬프트 텍스트 초기화 완료:', {
          interviewPromptTextLength: this.interviewPromptText ? this.interviewPromptText.length : 0
        })
        debugLog('🎤 [showAIMockInterviewDetail] Voice Interview 모드 전환 완료')
        return
      }
      
      // 웹 환경: 기존 모달 방식
      debugLog('🎤 [showAIMockInterviewDetail] 웹 환경 감지됨 → 기존 모달 방식 사용')
      this.showAIMockInterviewModal = true
      
      // 기존 loadQuestions 메서드 재사용
      if (question.id) {
        debugLog('🎤 [showAIMockInterviewDetail] 웹 환경 - 문제 목록 로드 시작:', question.id)
        await this.loadQuestions(question.id, true)
        debugLog('🎤 [showAIMockInterviewDetail] 웹 환경 - 문제 목록 로드 완료')
      }
      
      // 번역 강제 로드
      debugLog('🎤 [showAIMockInterviewDetail] 웹 환경 - 번역 로드 시작')
      await this.$loadTranslations()
      debugLog('🎤 [showAIMockInterviewDetail] 웹 환경 - 번역 로드 완료')
      
      debugLog('🎤 [showAIMockInterviewDetail] 웹 환경 - 프롬프트 텍스트 초기화 시작')
      await this.initializePromptText()
      debugLog('🎤 [showAIMockInterviewDetail] 웹 환경 - 프롬프트 텍스트 초기화 완료')
    },
    
    hideAIMockInterviewModal() {
      debugLog('🎤 [hideAIMockInterviewModal] 모달 닫기 시작', {
        showAIMockInterviewModal: this.showAIMockInterviewModal,
        showVoiceInterview: this.showVoiceInterview
      })
      this.showAIMockInterviewModal = false
      this.selectedQuestionForAI = null
      this.showVoiceInterview = false
      debugLog('🎤 [hideAIMockInterviewModal] 모달 닫기 완료', {
        showAIMockInterviewModal: this.showAIMockInterviewModal,
        showVoiceInterview: this.showVoiceInterview
      })
    },
    
    /**
     * 모바일 디바이스 감지
     */
    checkIsMobileDevice() {
      debugLog('📱 [checkIsMobileDevice] 모바일 감지 시작')
      
      if (typeof window === 'undefined') {
        debugLog('📱 [checkIsMobileDevice] window가 undefined → false 반환')
        return false
      }
      
      // Capacitor 네이티브 플랫폼 확인 (가장 확실한 방법)
      if (window.Capacitor) {
        debugLog('📱 [checkIsMobileDevice] window.Capacitor 존재함')
        try {
          // isNativePlatform() 메서드 사용
          if (typeof window.Capacitor.isNativePlatform === 'function') {
            const isNative = window.Capacitor.isNativePlatform()
            debugLog('📱 [checkIsMobileDevice] isNativePlatform() 결과:', isNative)
            if (isNative) {
              debugLog('📱 [checkIsMobileDevice] ✅ Capacitor 네이티브 플랫폼 감지됨 → true 반환')
              return true
            }
          } else {
            debugLog('📱 [checkIsMobileDevice] isNativePlatform() 메서드 없음')
          }
          
          // getPlatform() 메서드 사용 (fallback)
          if (typeof window.Capacitor.getPlatform === 'function') {
            const platform = window.Capacitor.getPlatform()
            debugLog('📱 [checkIsMobileDevice] getPlatform() 결과:', platform)
            if (platform && platform !== 'web') {
              debugLog('📱 [checkIsMobileDevice] ✅ Capacitor 플랫폼 감지됨:', platform, '→ true 반환')
              return true
            } else {
              debugLog('📱 [checkIsMobileDevice] 플랫폼이 web이거나 없음:', platform)
            }
          } else {
            debugLog('📱 [checkIsMobileDevice] getPlatform() 메서드 없음')
          }
        } catch (error) {
          debugLog('📱 [checkIsMobileDevice] ❌ Capacitor 플랫폼 확인 실패:', error, 'error')
        }
      } else {
        debugLog('📱 [checkIsMobileDevice] window.Capacitor 없음')
      }
      
      // User-Agent로 모바일 감지
      if (typeof navigator !== 'undefined') {
        const userAgent = navigator.userAgent || ''
        debugLog('📱 [checkIsMobileDevice] User-Agent 확인:', userAgent.substring(0, 100))
        const isMobileUA = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(userAgent)
        if (isMobileUA) {
          debugLog('📱 [checkIsMobileDevice] ✅ User-Agent로 모바일 감지됨 → true 반환')
        } else {
          debugLog('📱 [checkIsMobileDevice] User-Agent로 모바일 감지 안됨')
        }
        return isMobileUA
      } else {
        debugLog('📱 [checkIsMobileDevice] navigator가 undefined')
      }
      
      debugLog('📱 [checkIsMobileDevice] ❌ 모든 감지 방법 실패 → false 반환')
      return false
    },
    
    /**
     * 음성 인터뷰 시작
     */
    async startVoiceInterview() {
      // 🔴 버튼 클릭 시점 로그 (항상 출력)
      console.log('🔴🔴🔴 [BUTTON CLICK] 음성 인터뷰 시작 버튼 클릭됨! 🔴🔴🔴')
      console.log('🔴 [BUTTON CLICK] 클릭 시점 interviewPromptText 상태:', {
        value: this.interviewPromptText,
        length: this.interviewPromptText ? this.interviewPromptText.length : 0,
        preview: this.interviewPromptText ? this.interviewPromptText.substring(0, 200) + '...' : '없음',
        full: this.interviewPromptText || '(비어있음)'
      })
      console.log('🔴 [BUTTON CLICK] 현재 상태:', {
        showVoiceInterview: this.showVoiceInterview,
        showAIMockInterviewModal: this.showAIMockInterviewModal,
        isMobileDevice: this.isMobileDevice,
        selectedQuestionForAI: this.selectedQuestionForAI ? {
          id: this.selectedQuestionForAI.id,
          title: this.selectedQuestionForAI.title
        } : null
      })
      
      // 필수 규칙이 포함되도록 프롬프트 텍스트 재초기화
      console.log('🔵 [startVoiceInterview] 필수 규칙 포함을 위해 프롬프트 텍스트 재초기화 시작...')
      await this.initializePromptText()
      console.log('🔵 [startVoiceInterview] 프롬프트 텍스트 재초기화 완료:', {
        length: this.interviewPromptText ? this.interviewPromptText.length : 0,
        hasMandatoryRules: this.interviewPromptText && this.interviewPromptText.includes('=== 필수 규칙 (자동 추가) ===')
      })
      
      // instructions 전달 확인을 위한 로그 (항상 출력)
      console.log('🎤 [startVoiceInterview] 메서드 시작 - interviewPromptText 확인:', {
        interviewPromptText: this.interviewPromptText,
        interviewPromptTextLength: this.interviewPromptText ? this.interviewPromptText.length : 0,
        interviewPromptTextPreview: this.interviewPromptText ? this.interviewPromptText.substring(0, 200) + '...' : '없음',
        interviewPromptTextFull: this.interviewPromptText || '(비어있음)', // 전체 내용 항상 포함
        showVoiceInterview: this.showVoiceInterview,
        showAIMockInterviewModal: this.showAIMockInterviewModal,
        isMobileDevice: this.isMobileDevice
      })
      // instructions가 비어있으면 경고
      if (!this.interviewPromptText || this.interviewPromptText.trim().length === 0) {
        console.error('❌❌❌ [startVoiceInterview] ⚠️⚠️⚠️ interviewPromptText가 비어있습니다! ❌❌❌')
      } else {
        console.log('✅✅✅ [startVoiceInterview] interviewPromptText 확인 (길이: ' + this.interviewPromptText.length + ', 미리보기: ' + this.interviewPromptText.substring(0, 200) + '...)')
      }
      debugLog('🎤 [startVoiceInterview] 시작', {
        현재상태: {
          showVoiceInterview: this.showVoiceInterview,
          showAIMockInterviewModal: this.showAIMockInterviewModal,
          isMobileDevice: this.isMobileDevice,
          interviewPromptTextLength: this.interviewPromptText ? this.interviewPromptText.length : 0
        }
      })
      
      console.log('🟢 [startVoiceInterview] showVoiceInterview를 true로 설정합니다...')
      this.showVoiceInterview = true
      console.log('🟢 [startVoiceInterview] showVoiceInterview = true 설정 완료!')
      console.log('🟢 [startVoiceInterview] 이제 MobileVoiceInterview 컴포넌트가 마운트될 것입니다.')
      debugLog('🎤 [startVoiceInterview] 완료', {
        showVoiceInterview: this.showVoiceInterview
      })
    },
    
    /**
     * 세션 생성 완료 처리 - textarea에서 필수 규칙 이후 내용 제거
     */
    handleSessionCreated() {
      console.log('🔵 [handleSessionCreated] 세션 생성 완료 - textarea 업데이트 시작')
      if (this.interviewPromptText) {
        const cleanedText = this.removeMandatoryRules(this.interviewPromptText)
        if (cleanedText !== this.interviewPromptText) {
          this.isInitializingPrompt = true // watch 건너뛰기 (이미 제거됨)
          this.interviewPromptText = cleanedText
          this.$nextTick(() => {
            this.isInitializingPrompt = false
          })
          console.log('🔵 [handleSessionCreated] textarea에서 필수 규칙 이후 내용 제거 완료')
        }
      }
    },
    
    /**
     * 인터뷰 종료 처리
     */
    handleInterviewEnded() {
      debugLog('🎤 [handleInterviewEnded] 인터뷰 종료 처리 시작', {
        현재상태: {
          showVoiceInterview: this.showVoiceInterview,
          showAIMockInterviewModal: this.showAIMockInterviewModal
        }
      })
      this.showVoiceInterview = false
      debugLog('🎤 [handleInterviewEnded] showVoiceInterview = false 설정 완료')
      this.hideAIMockInterviewModal()
      debugLog('🎤 [handleInterviewEnded] 인터뷰 종료 처리 완료')
      // 인터뷰 완료 알림 등 추가 처리 가능
    },

    async initializePromptText() {
      if (this.selectedQuestionForAI) {
        // watch가 트리거되지 않도록 플래그 설정
        this.isInitializingPrompt = true
        
        // 시험의 문제들을 가져와서 프롬프트에 포함
        const questionsText = this.getQuestionsTextForPrompt()
        const currentLang = this.currentLanguage
        
        // 공통 유틸리티를 사용하여 필수 규칙 및 템플릿 로드 (iOS와 웹에서 동일한 source 사용)
        const [mandatoryRulesData, template] = await Promise.all([
          loadMandatoryRules(currentLang),
          loadInterviewPromptTemplate(currentLang)
        ])
        const { languageInstruction, mandatoryRules } = mandatoryRulesData
        
        // 공통 유틸리티를 사용하여 프롬프트 생성 (iOS와 웹에서 동일한 형식 보장)
        const promptText = buildInterviewPrompt({
          language: currentLang,
          questionsText,
          languageInstruction,
          mandatoryRules,
          template
        })
        
        this.interviewPromptText = promptText
        
        // 플래그 해제 (다음 틱에서 watch가 정상 작동하도록)
        this.$nextTick(() => {
          this.isInitializingPrompt = false
        })
      }
    },

    getQuestionsTextForPrompt() {
      // 기존 questions 배열 사용
      if (!this.questions || this.questions.length === 0) {
        const currentLang = this.currentLanguage
        if (currentLang === 'en') {
          return 'Unable to load question information.'
        } else if (currentLang === 'zh') {
          return '无法加载问题信息。'
        } else if (currentLang === 'es') {
          return 'No se puede cargar la información de la pregunta.'
        } else {
          return '문제 정보를 불러올 수 없습니다.'
        }
      }

      const currentLang = this.currentLanguage
      let titleLabel, answerLabel, explanationLabel, noTitle, noAnswer
      
      if (currentLang === 'en') {
        titleLabel = 'Title'
        answerLabel = 'Answer'
        explanationLabel = 'Explanation'
        noTitle = 'No title'
        noAnswer = 'No answer'
      } else if (currentLang === 'zh') {
        titleLabel = '标题'
        answerLabel = '答案'
        explanationLabel = '说明'
        noTitle = '无标题'
        noAnswer = '无答案'
      } else if (currentLang === 'es') {
        titleLabel = 'Título'
        answerLabel = 'Respuesta'
        explanationLabel = 'Explicación'
        noTitle = 'Sin título'
        noAnswer = 'Sin respuesta'
      } else {
        titleLabel = '제목'
        answerLabel = '답변'
        explanationLabel = '설명'
        noTitle = '제목 없음'
        noAnswer = '답변 없음'
      }

      return this.questions.map((question, index) => {
        const title = question.localized_title || question.title || noTitle
        const answer = question.localized_answer || question.answer || noAnswer
        const explanation = question.localized_explanation || question.explanation

        let questionText = `${index + 1}. ${titleLabel}: ${title}
  ${answerLabel}: ${answer}`
        
        // explanation이 있고 빈 값이 아닌 경우에만 설명 라인 추가
        if (explanation && explanation.trim()) {
          questionText += `\n  ${explanationLabel}: ${explanation}`
        }

        return questionText
      }).join('\n\n')
    },

    resetPrompt() {
      this.initializePromptText()
      this.showSuccessToast(this.$t('examDetail.promptReset') || '프롬프트가 초기화되었습니다.')
    },

    /**
     * 필수 규칙 마커 이후의 텍스트를 제거
     * @param {string} text - 원본 텍스트
     * @returns {string} - 필수 규칙이 제거된 텍스트
     */
    removeMandatoryRules(text) {
      if (!text || !text.trim()) {
        return text
      }
      
      const mandatoryRulesMarkers = [
        '=== 필수 규칙 (자동 추가) ===',
        '=== Mandatory Rules (Auto Added) ==='
      ]
      
      for (const marker of mandatoryRulesMarkers) {
        const markerIndex = text.indexOf(marker)
        if (markerIndex !== -1) {
          // 마커가 포함된 줄의 시작 위치 찾기 (이전 줄바꿈부터)
          let cutIndex = text.lastIndexOf('\n', markerIndex - 1)
          
          // 마커 앞의 빈 줄들도 제거
          if (cutIndex !== -1) {
            // 이전 줄바꿈 앞의 빈 줄들 확인
            let checkIndex = cutIndex
            while (checkIndex > 0 && (text[checkIndex - 1] === '\n' || text[checkIndex - 1] === '\r')) {
              checkIndex--
            }
            const prevNewline = text.lastIndexOf('\n', checkIndex - 1)
            if (prevNewline !== -1) {
              const betweenText = text.substring(prevNewline + 1, checkIndex).trim()
              if (betweenText === '') {
                cutIndex = prevNewline
              }
            }
            cutIndex++ // 줄바꿈 다음부터 시작
          } else {
            cutIndex = 0
          }
          
          const cleanedText = text.substring(0, cutIndex).trim()
          console.log('🔵 [removeMandatoryRules] 필수 규칙 제거됨:', {
            marker: marker,
            originalLength: text.length,
            cleanedLength: cleanedText.length
          })
          return cleanedText
        }
      }
      
      return text
    },

    async copyToClipboard() {
      try {
        // 문제 붙여넣기 모드일 때는 leetcodeProblems를 복사
        const textToCopy = this.pasteProblemMode && this.leetcodeProblems 
          ? this.leetcodeProblems 
          : this.interviewPromptText || ''
        
        if (textToCopy) {
          await navigator.clipboard.writeText(textToCopy)
          const message = this.pasteProblemMode 
            ? this.$t('examDetail.problemListCopied')
            : this.$t('examDetail.promptCopied')
          this.showSuccessToast(message)
        } else {
          this.showErrorToast('복사할 텍스트를 찾을 수 없습니다.')
        }
      } catch (error) {
        console.error('클립보드 복사 실패:', error)
        // 폴백: 기존 방식으로 복사
        try {
          const textArea = document.createElement('textarea')
          const textToCopy = this.pasteProblemMode && this.leetcodeProblems 
            ? this.leetcodeProblems 
            : this.interviewPromptText || ''
          textArea.value = textToCopy
          document.body.appendChild(textArea)
          textArea.select()
          document.execCommand('copy')
          document.body.removeChild(textArea)
          const message = this.pasteProblemMode 
            ? this.$t('examDetail.problemListCopied')
            : this.$t('examDetail.promptCopied')
          this.showSuccessToast(message)
        } catch (fallbackError) {
          console.error('폴백 복사도 실패:', fallbackError)
          this.showErrorToast('클립보드 복사에 실패했습니다.')
        }
      }
    },

    // 공통 상태 관리 유틸리티
    async toggleQuestionStatus(statusType, questionId = null) {
      if (!questionId) {
        this.showWarningToast('문제 ID가 필요합니다.');
        return;
      }
      
      const targetQuestionId = questionId;

      try {
        let response;
        
        if (statusType === 'favorite') {
          // 즐겨찾기 토글
          response = await axios.post('/api/add-question-to-favorite/', {
            question_id: targetQuestionId
          });
          
          // 응답으로 상태 확인
          const isFavorited = response.data.is_favorite || false;
          
          // 로컬 상태 업데이트
          if (this.favoriteQuestions) {
            if (isFavorited) {
              this.favoriteQuestions.add(String(targetQuestionId));
            } else {
              this.favoriteQuestions.delete(String(targetQuestionId));
            }
          }
          
          if (isFavorited) {
            this.showSuccessToast(this.$t('takeExam.questionAddedToFavorite'));
          } else {
            this.showInfoToast(this.$t('takeExam.removedFromFavorite'));
          }
        } else if (statusType === 'ignore') {
          // 무시하기 토글
          response = await axios.post(`/api/question/${targetQuestionId}/ignore/`);
          
          // 응답으로 상태 확인
          const isIgnored = response.data.is_ignored || false;
          
          // 로컬 상태 업데이트
          if (this.ignoredQuestions) {
            if (isIgnored) {
              this.ignoredQuestions.add(String(targetQuestionId));
            } else {
              this.ignoredQuestions.delete(String(targetQuestionId));
            }
          }
          
          if (isIgnored) {
            this.showInfoToast(this.$t('takeExam.questionIgnored'));
          } else {
            this.showSuccessToast(this.$t('takeExam.questionUnignored'));
          }
        }
        
        // 서버 상태 동기화
        await this.refreshQuestionStatus(statusType);
        
        debugLog(`${statusType} 상태 토글 완료:`, {
          questionId: targetQuestionId,
          statusType,
          response: response.data
        });
        
      } catch (error) {
        this.handleQuestionStatusError(error, statusType);
      }
    },

    // 공통 상태 새로고침
    async refreshQuestionStatus(statusType) {
      try {
        debugLog(`${statusType} 상태 새로고침 시작`);
        
        if (statusType === 'favorite') {
          await this.loadFavoriteStatus();
        } else if (statusType === 'ignore') {
          await this.loadIgnoredQuestions();
        }
        
        debugLog(`${statusType} 상태 새로고침 완료`);
      } catch (error) {
        debugLog(`${statusType} 상태 새로고침 실패:`, error, 'error');
      }
    },

    // 공통 에러 처리 유틸리티
    handleQuestionStatusError(error, statusType) {
      debugLog(`${statusType} 상태 변경 실패:`, error, 'error');
      
      const errorMessage = statusType === 'favorite' 
        ? '즐겨찾기 상태 변경에 실패했습니다.'
        : '무시 상태 변경에 실패했습니다.';
      
      this.showErrorToast(errorMessage);
    },

    // 즐겨찾기 상태 로드
    async loadFavoriteStatus() {
      debugLog('=== ExamDetail.loadFavoriteStatus 호출 ===', {
        routePath: this.$route.path,
        isFavoriteMode: this.isFavoriteMode,
        timestamp: Date.now()
      })
      try {
        const response = await axios.get('/api/favorite-exam-questions/', {
          params: { 
            t: Date.now(),
            _: Math.random()
          }
        });
        
        debugLog('즐겨찾기 API 응답:', response.data);
        
        const favoriteQuestions = response.data.questions || [];
        
        // 기존 즐겨찾기 목록을 API 응답으로 업데이트
        this.favoriteQuestions.clear();
        this.ignoredQuestions.clear();
        
        favoriteQuestions.forEach(q => {
          // is_favorite이 true인 문제만 favoriteQuestions에 추가
          if (q.is_favorite === true) {
            this.favoriteQuestions.add(String(q.id));
          }
          // is_ignored가 true인 문제만 ignoredQuestions에 추가
          if (q.is_ignored === true) {
            this.ignoredQuestions.add(String(q.id));
          }
        });
        
        // 실제 favorite 문제 수 계산
        const actualFavoriteCount = favoriteQuestions.filter(q => q.is_favorite === true).length;
        const actualIgnoredCount = favoriteQuestions.filter(q => q.is_ignored === true).length;
        
        debugLog('즐겨찾기 상태 로드 완료:', {
          totalQuestionsCount: favoriteQuestions.length,
          actualFavoriteCount: actualFavoriteCount,
          ignoredQuestionsCount: actualIgnoredCount,
          favoriteQuestions: Array.from(this.favoriteQuestions),
          ignoredQuestions: Array.from(this.ignoredQuestions)
        });
      } catch (error) {
        debugLog('즐겨찾기 상태 로드 실패:', error, 'error');
        this.favoriteQuestions.clear();
      }
    },

    // 무시된 문제 목록 로드
    async loadIgnoredQuestions() {
      // 인증되지 않은 사용자는 무시된 문제 목록을 로드하지 않음
      if (!this.isAuthenticated) {
        debugLog('인증되지 않은 사용자 - 무시된 문제 목록 로드 건너뜀');
        this.ignoredQuestions.clear();
        return;
      }
      
      try {
        const response = await axios.get('/api/questions/ignored/');
        debugLog('무시된 문제 목록 응답:', response.data);
        
        // question_id를 문자열로 변환하여 Set에 저장
        const ignoredQuestions = new Set(
          response.data.ignored_questions.map(item => String(item.question_id))
        );
        
        // 로컬 상태 업데이트
        this.ignoredQuestions.clear();
        ignoredQuestions.forEach(id => this.ignoredQuestions.add(id));
        
        debugLog('무시된 문제 목록 로드 완료:', {
          ignoredQuestions: Array.from(this.ignoredQuestions),
          ignoredQuestionsCount: this.ignoredQuestions.size,
          sampleQuestionId: '6a0b2c6a-4e80-484b-b991-5ada50d3f82d',
          isSampleQuestionIgnored: this.ignoredQuestions.has('6a0b2c6a-4e80-484b-b991-5ada50d3f82d')
        });
      } catch (error) {
        debugLog('무시된 문제 목록 로드 실패:', error, 'error');
        this.ignoredQuestions.clear();
      }
    },

    // 문제 상태 확인 메서드들
    isQuestionFavorite(questionId) {
      if (!this.favoriteQuestions) return false;
      const idStr = String(questionId);
      return this.favoriteQuestions.has(idStr);
    },

    isQuestionIgnored(questionId) {
      if (!this.ignoredQuestions) return false;
      const idStr = String(questionId);
      return this.ignoredQuestions.has(idStr);
    },

    // 즐겨찾기 토글 (통합 메서드 사용)
    async toggleFavorite(questionId) {
      await this.toggleQuestionStatus('favorite', questionId);
    },

    // 무시하기 토글 (통합 메서드 사용)
    async toggleIgnore(questionId) {
      await this.toggleQuestionStatus('ignore', questionId);
    },
    async addSelectedToFavorite() {
      if (this.selectedQuestions.length === 0) return;
      
      try {
        for (const questionId of this.selectedQuestions) {
          await axios.post('/api/add-question-to-favorite/', {
            question_id: questionId
          });
          this.favoriteQuestions.add(String(questionId));
        }
        this.showSuccessToast(this.$t('examDetail.questionsAddedToFavorite', { count: this.selectedQuestions.length }));
      } catch (error) {
        debugLog('선택된 문제들 favorite 추가 실패', error, 'error');
        this.showErrorToast(this.$t('examDetail.alerts.favoriteAddFailed'));
      }
    },
    async removeSelectedFromFavorite() {
      if (this.selectedQuestions.length === 0) return;
      
      try {
        let removedCount = 0;
        for (const questionId of this.selectedQuestions) {
          // add-question-to-favorite API를 사용하여 토글 (이미 favorite에 있는 문제는 제거됨)
          const response = await axios.post('/api/add-question-to-favorite/', {
            question_id: questionId
          });
          if (response.data.is_favorite === false) {
            this.favoriteQuestions.delete(String(questionId));
            removedCount++;
          }
        }
        if (removedCount > 0) {
          this.showSuccessToast(this.$t('examDetail.questionsRemovedFromFavorite', { count: removedCount }));
        } else {
          this.showInfoToast(this.$t('examDetail.questionsAlreadyNotInFavorite'));
        }
        
        // 캐시 새로고침
        await this.refreshQuestionStatus('favorite');
      } catch (error) {
        debugLog('선택된 문제들 favorite 제거 실패', error, 'error');
        this.showErrorToast(this.$t('examDetail.alerts.favoriteRemoveFailed'));
      }
    },
    async ignoreSelectedQuestions() {
      if (this.selectedQuestions.length === 0) return;
      
      try {
        for (const questionId of this.selectedQuestions) {
          await axios.post(`/api/question/${questionId}/ignore/`);
          this.ignoredQuestions.add(String(questionId));
        }
        this.showSuccessToast(this.$t('examDetail.questionsAddedToIgnore', { count: this.selectedQuestions.length }));
      } catch (error) {
        debugLog('선택된 문제들 무시 설정 실패', error, 'error');
        this.showErrorToast(this.$t('examDetail.alerts.ignoreSetFailed'));
      }
    },
    async unignoreSelectedQuestions() {
      if (this.selectedQuestions.length === 0) return;
      
      try {
        let unignoredCount = 0;
        for (const questionId of this.selectedQuestions) {
          // ignore API를 사용하여 토글 (이미 무시된 문제는 해제됨)
          const response = await axios.post(`/api/question/${questionId}/ignore/`);
          if (response.data.is_ignored === false) {
            this.ignoredQuestions.delete(String(questionId));
            unignoredCount++;
          }
        }
        if (unignoredCount > 0) {
          this.showSuccessToast(this.$t('examDetail.questionsRemovedFromIgnore', { count: unignoredCount }));
        } else {
          this.showInfoToast(this.$t('examDetail.questionsAlreadyNotIgnored'));
        }
        
        // 캐시 새로고침
        await this.refreshQuestionStatus('ignore');
      } catch (error) {
        debugLog('선택된 문제들 무시 해제 실패', error, 'error');
        this.showErrorToast(this.$t('examDetail.alerts.ignoreUnsetFailed'));
      }
    },
    async addAllToFavorite() {
      if (this.selectedQuestions.length === 0) {
        this.showWarningToast(this.$t('examDetail.noQuestionsSelectedForFavorite'));
        return;
      }
      
      try {
        let addedCount = 0;
        let removedCount = 0;
        
        for (const questionId of this.selectedQuestions) {
          // add-question-to-favorite API를 사용하여 토글
          const response = await axios.post('/api/add-question-to-favorite/', {
            question_id: questionId
          });
          
          if (response.data.is_favorite) {
            this.favoriteQuestions.add(String(questionId));
            addedCount++;
          } else {
            this.favoriteQuestions.delete(String(questionId));
            removedCount++;
          }
        }
        
        let message = '';
        if (addedCount > 0) {
          message += this.$t('examDetail.questionsAddedToFavorite', { count: addedCount });
        }
        if (removedCount > 0) {
          if (message) message += ' ';
          message += this.$t('examDetail.questionsRemovedFromFavorite', { count: removedCount });
        }
        this.showSuccessToast(message);
      } catch (error) {
        debugLog('선택된 문제들 favorite 토글 실패', error, 'error');
        this.showErrorToast(this.$t('examDetail.alerts.favoriteProcessFailed'));
      }
    },
    async ignoreAllQuestions() {
      if (this.selectedQuestions.length === 0) {
        this.showWarningToast(this.$t('examDetail.noQuestionsSelectedForIgnore'));
        return;
      }
      
      try {
        let ignoredCount = 0;
        let unignoredCount = 0;
        
        for (const questionId of this.selectedQuestions) {
          if (this.isQuestionIgnored(questionId)) {
            // 이미 무시된 경우 해제
            await axios.post(`/api/question/${questionId}/unignore/`);
            this.ignoredQuestions.delete(String(questionId));
            unignoredCount++;
          } else {
            // 무시되지 않은 경우 무시 설정
            await axios.post(`/api/question/${questionId}/ignore/`);
            this.ignoredQuestions.add(String(questionId));
            ignoredCount++;
          }
        }
        
        let message = '';
        if (ignoredCount > 0) {
          message += this.$t('examDetail.questionsIgnored', { count: ignoredCount });
        }
        if (unignoredCount > 0) {
          if (message) message += ' ';
          message += this.$t('examDetail.questionsUnignored', { count: unignoredCount });
        }
        this.showSuccessToast(message);
      } catch (error) {
        debugLog('선택된 문제들 무시 토글 실패', error, 'error');
        this.showErrorToast(this.$t('examDetail.alerts.ignoreProcessFailed'));
      }
    },
    clearAllFilters() {
      // Clear sessionStorage filters (groupIdFilter는 세션에 저장되지 않으므로 제외)
      sessionStorage.removeItem('examDetail_searchTerm');
      sessionStorage.removeItem('examDetail_difficultyFilter');
      sessionStorage.removeItem('examDetail_answerFilter');
      sessionStorage.removeItem('examDetail_favoriteFilter');
      sessionStorage.removeItem('examDetail_ignoreFilter');
      sessionStorage.removeItem('examDetail_sortBy');
      sessionStorage.removeItem('examDetail_sortOrder');
      // Clear component state filters
      this.searchTerm = '';
      this.difficultyFilter = '';
      this.answerFilter = '';
      this.favoriteFilter = '';
      this.ignoreFilter = this.isFavoriteMode ? '' : 'not_ignored';
      this.groupIdFilter = '';
      this.sortBy = 'order';
      this.sortOrder = 'asc';
      this.selectedQuestions = [];
    },
    // 엑셀 업로드 관련 메서드들
    toggleExcelUpload() {
      this.showExcelUpload = !this.showExcelUpload;
      this.selectedExcelFile = null;
      this.uploadMessage = '';
      this.uploadMessageType = 'alert-info';
    },
    handleExcelFileSelect(event) {
      this.selectedExcelFile = event.target.files[0];
      this.uploadMessage = '';
      this.uploadMessageType = 'alert-info';
    },
    async uploadExcelFile() {
      if (!this.selectedExcelFile) {
        this.uploadMessage = '파일을 선택해주세요.';
        this.uploadMessageType = 'alert-warning';
        return;
      }

      const formData = new FormData();
      formData.append('file', this.selectedExcelFile);

      try {
        const response = await axios.post(`/api/exam/${this.exam.id}/update-questions-from-excel/`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        debugLog('Excel 업로드 응답:', response.data);

        // 성공 메시지 표시
        this.uploadMessage = response.data.message;
        this.uploadMessageType = 'alert-success';

        // 상세 통계 표시
        if (response.data.stats) {
          const stats = response.data.stats;
          let detailMessage = this.$t('examDetail.totalRowsProcessed', { count: stats.total_rows }) + '\n';
          detailMessage += this.$t('examDetail.updated', { count: stats.updated }) + '\n';
          detailMessage += this.$t('examDetail.skipped', { count: stats.skipped }) + '\n';
          if (stats.errors > 0) {
            detailMessage += this.$t('examDetail.errors', { count: stats.errors }) + '\n';
            if (stats.error_details.length > 0) {
              detailMessage += '\n' + this.$t('examDetail.errorDetails') + '\n' + stats.error_details.slice(0, 5).join('\n');
              if (stats.error_details.length > 5) {
                detailMessage += '\n' + this.$t('examDetail.andMore', { count: stats.error_details.length - 5 });
              }
            }
          }
          this.showInfoToast(detailMessage);
        }

        // 데이터 새로고침
        this.selectedQuestions = []; // 업로드 후 선택 초기화
        await this.loadExam(this.exam.id); // 시험 정보 다시 로드
        await this.loadQuestionStatistics(this.exam.id); // 문제 통계 다시 로드
        await this.loadLatestResult(this.exam.id); // 최신 결과 다시 로드
        sessionStorage.setItem('refreshExamManagement', 'true'); // 시험 관리 화면 새로고침

        // 업로드 폼 초기화
        this.cancelExcelUpload();

      } catch (error) {
        debugLog('Excel 업로드 실패:', error, 'error');
        this.uploadMessage = error.response?.data?.error || this.$t('examDetail.excelUploadFailed');
        this.uploadMessageType = 'alert-danger';
      }
    },
    cancelExcelUpload() {
      this.showExcelUpload = false;
      this.selectedExcelFile = null;
      this.uploadMessage = '';
      this.uploadMessageType = 'alert-info';
    },

    // 공유 모달 열기
    async openShareModal() {
      // 공유 URL 생성
      const params = new URLSearchParams();
      if (this.searchTerm) params.append('searchTerm', this.searchTerm);
      if (this.difficultyFilter) params.append('difficultyFilter', this.difficultyFilter);
      if (this.answerFilter) params.append('answerFilter', this.answerFilter);
      if (this.groupIdFilter) params.append('group_id', this.groupIdFilter);
      if (this.originalExamFilter) params.append('originalExamFilter', this.originalExamFilter);
      if (this.sortBy) params.append('sortBy', this.sortBy);
      if (this.sortOrder) params.append('sortOrder', this.sortOrder);
      
      const baseUrl = `${window.location.origin}/exam-detail/${this.exam.id}`;
      const originalUrl = params.toString() ? `${baseUrl}?${params.toString()}` : baseUrl;
      
      // 단축 URL 생성
      try {
        const response = await axios.post('/api/short-url/create/', {
          url: originalUrl,
          expires_days: 30
        });
        this.shareUrl = response.data.short_url;
      } catch (error) {
        debugLog('단축 URL 생성 실패:', error, 'error');
        // 단축 URL 생성 실패 시 원본 URL 사용
        this.shareUrl = originalUrl;
      }
      
      this.shareEmail = '';
      this.showShareModal = true;
    },
    
    // 공유 모달 닫기
    closeShareModal() {
      this.showShareModal = false;
      this.shareUrl = '';
    },
    
    async shareCurrentUrl() {
      // shareExam 함수를 동적으로 import
      const { shareExam: shareExamFunc } = await import('@/utils/shareExamUtils')
      
      const getShareUrl = (context) => {
        // 현재 필터 상태를 URL 파라미터로 구성
        const params = new URLSearchParams();
        
        // 필터 파라미터들 추가
        if (context.searchTerm) params.append('searchTerm', context.searchTerm);
        if (context.difficultyFilter) params.append('difficultyFilter', context.difficultyFilter);
        if (context.answerFilter) params.append('answerFilter', context.answerFilter);
        if (context.groupIdFilter) params.append('group_id', context.groupIdFilter);
        if (context.originalExamFilter) params.append('originalExamFilter', context.originalExamFilter);
        if (context.sortBy) params.append('sortBy', context.sortBy);
        if (context.sortOrder) params.append('sortOrder', context.sortOrder);
        
        // 현재 URL 구성
        const baseUrl = `${window.location.origin}/exam-detail/${context.exam.id}`;
        return params.toString() ? `${baseUrl}?${params.toString()}` : baseUrl;
      }
      
      await shareExamFunc(
        this,
        this.exam,
        getShareUrl,
        (title, message, callback, type) => {
          this.showConfirmModal(title, message, callback, type)
        },
        (message) => {
          this.showShareMessage(message, 'success')
        },
        (message) => {
          this.showShareMessage(message, 'error')
        },
        this.$i18n.locale || 'en'
      )
    },
    fallbackCopyToClipboard(text) {
      // 클립보드 API가 지원되지 않는 경우의 fallback
      const textArea = document.createElement('textarea');
      textArea.value = text;
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      textArea.style.top = '-999999px';
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      
      try {
        document.execCommand('copy');
        this.showShareMessage(this.$t('examDetail.urlCopied'), 'success');
      } catch (err) {
        debugLog('Fallback 복사 실패:', err, 'error');
        this.showShareMessage(this.$t('examDetail.urlCopyFailed'), 'error');
      } finally {
        document.body.removeChild(textArea);
      }
    },
    showShareMessage(message, type) {
      // 임시 메시지 표시 (Toast 스타일) - 공통 CSS 사용
      const messageDiv = document.createElement('div');
      const typeClassMap = {
        success: 'alert-success',
        error: 'alert-error'
      }
      messageDiv.className = `toast-notification ${typeClassMap[type] || 'alert-success'}`
      messageDiv.innerHTML = `<div class="toast-content">${message}</div>`
      
      document.body.appendChild(messageDiv);
      
      // 3초 후 자동 제거
      setTimeout(() => {
        messageDiv.style.opacity = '0';
        setTimeout(() => {
          if (document.body.contains(messageDiv)) {
            document.body.removeChild(messageDiv);
          }
        }, 300);
      }, 3000);
    },
    toggleDropdownMenu() {
      this.showDropdownMenu = !this.showDropdownMenu;
    },
    
    closeDropdownMenu() {
      this.showDropdownMenu = false;
    },
    
    handleOutsideClick(event) {
      // 드롭다운 메뉴 외부 클릭 시 닫기
      const dropdownContainer = event.target.closest('.dropdown-menu-container');
      const adminDropdownContainer = event.target.closest('.admin-dropdown-container');
      
      if (!dropdownContainer && this.showDropdownMenu) {
        this.showDropdownMenu = false;
      }
      
      if (!adminDropdownContainer && this.showAdminDropdownMenu) {
        this.showAdminDropdownMenu = false;
      }
    },
    
    handleDropdownAction(action) {
      // 드롭다운 메뉴 닫기
      this.showDropdownMenu = false;
      
      // 해당 액션 실행
      switch (action) {
        case 'goToAddQuestion':
          this.goToAddQuestion();
          break;
        case 'shareCurrentUrl':
          this.shareCurrentUrl();
          break;
        case 'downloadExcel':
          this.downloadExcel();
          break;
        case 'toggleExcelUpload':
          this.toggleExcelUpload();
          break;
        case 'addAllToFavorite':
          this.addAllToFavorite();
          break;
        case 'ignoreAllQuestions':
          this.ignoreAllQuestions();
          break;
      }
    },
    
    toggleAdminDropdownMenu() {
      this.showAdminDropdownMenu = !this.showAdminDropdownMenu;
    },
    
    handleAdminDropdownAction(action) {
      // 관리자 드롭다운 메뉴 닫기
      this.showAdminDropdownMenu = false;
      
      // 해당 액션 실행
      switch (action) {
        case 'deleteSelectedQuestions':
          this.deleteSelectedQuestions();
          break;
        case 'deleteSelectedQuestionResultsGlobal':
          this.deleteSelectedQuestionResultsGlobal();
          break;
        case 'deleteAllQuestionResults':
          this.deleteAllQuestionResults();
          break;
        case 'goToExamManagement':
          this.goToExamManagement();
          break;
      }
    },
    
    async openOptionsModal() {
      // Options 모달을 열 때만 시험 목록 로드 (Lazy Loading)
      if (this.availableExams.length === 0) {
        await this.loadAvailableExams();
      }
      this.showOptionsModal = true;
    },
    
    hideOptionsModal() {
      this.showOptionsModal = false;
    },
    
    // 정확도 조정 관련 메서드들
    async decreaseAccuracy() {
      await this.applyAccuracyAdjustment('decrease');
    },
    
    async increaseAccuracy() {
      await this.applyAccuracyAdjustment('increase');
    },
    
    async applyAccuracyAdjustment(adjustmentType) {
      if (!this.exam) {
        this.showToastNotification('시험을 선택해주세요.', 'error');
        return;
      }
      
      if (!this.currentUser) {
        this.showToastNotification('사용자 정보를 찾을 수 없습니다.', 'error');
        return;
      }
      
      // 선택된 문제가 있는지 확인 (선택된 문제가 없으면 모든 문제 처리)
      const hasSelectedQuestions = this.selectedQuestions && this.selectedQuestions.length > 0;
      if (!hasSelectedQuestions) {
        // 선택된 문제가 없으면 확인 다이얼로그 표시
        const messageKey = hasSelectedQuestions ? 'examDetail.accuracyAdjustment.confirmSelectedMessage' : 'examDetail.accuracyAdjustment.confirmAllMessage';
        const messageParams = hasSelectedQuestions ? { count: this.selectedQuestions.length } : { count: 0 };
        
        this.showConfirmModal(
          this.$t('examDetail.accuracyAdjustment.confirmAllTitle'),
          this.$t(messageKey, messageParams),
          async (confirmed) => {
            if (confirmed) {
              // 확인된 경우 정확도 조정 실행
              await this.executeAccuracyAdjustment(adjustmentType);
            }
          },
          'warning'
        );
        return;
      }
      
      // 선택된 문제가 있으면 바로 실행
      await this.executeAccuracyAdjustment(adjustmentType);
    },
    
    async executeAccuracyAdjustment(adjustmentType) {
      try {
        debugLog(`정확도 ${adjustmentType === 'increase' ? '높이기' : '낮추기'} 시작`);
        debugLog('selectedQuestions:', this.selectedQuestions);
        debugLog('selectedQuestions.length:', this.selectedQuestions ? this.selectedQuestions.length : 'null');
        
        // 선택된 문제 ID들 가져오기 (selectedQuestions는 이미 ID 배열)
        const selectedQuestionIds = this.selectedQuestions && this.selectedQuestions.length > 0 
          ? this.selectedQuestions.filter(id => id !== null && id !== undefined) 
          : [];
        
        debugLog('selectedQuestionIds:', selectedQuestionIds);
        
        const response = await axios.post('/api/bulk-adjust-user-accuracy/', {
          target_username: this.currentUser.username,
          exam_id: this.exam.id,
          question_ids: selectedQuestionIds,  // 선택된 문제 ID들 전달
          adjustment_percentage: this.accuracyAdjustmentPercentage,
          adjustment_type: adjustmentType
        });
        
        if (response.data.success) {
          const adjustedCount = response.data.adjusted_count || 0;
          const totalQuestions = response.data.total_questions || 0;
          
          debugLog(`정확도 조정 완료: 조정된 문제 ${adjustedCount}/${totalQuestions}개`);
          
          const message = this.$t('examDetail.accuracyAdjustment.completed', {
            type: adjustmentType === 'increase' ? this.$t('examDetail.accuracyAdjustment.increase') : this.$t('examDetail.accuracyAdjustment.decrease'),
            adjustedCount,
            totalQuestions
          });
          this.showToastNotification(message, 'success');
          
          // 문제 목록 새로고침
          await this.loadQuestions(this.exam.id, true);
          await this.loadQuestionStatistics(this.exam.id, true);
          
          // 최신 결과 새로고침 (정확도 통계 업데이트를 위해)
          await this.loadLatestResult();
        } else {
          debugLog('정확도 조정 실패:', response.data);
          this.showToastNotification(response.data.message || this.$t('examDetail.accuracyAdjustment.failed'), 'error');
        }
      } catch (error) {
        debugLog('정확도 조정 오류:', error, 'error');
        const errorMessage = error.response?.data?.error || this.$t('examDetail.accuracyAdjustment.error');
        this.showToastNotification(errorMessage, 'error');
      }
    },
    
    onAccuracySliderChange() {
      // 슬라이더 값이 변경될 때마다 호출
      // 여기서는 추가 로직이 필요하지 않음
    },
    
    onAccuracySliderMouseUp() {
      // 슬라이더에서 마우스를 놓았을 때 호출
      // 여기서는 추가 로직이 필요하지 않음
    }
  },
  watch: {
    // 언어 변경 감지 및 시험 데이터 다시 로드
    '$i18n.locale'(newLocale, oldLocale) {
      if (newLocale !== oldLocale && this.exam && this.exam.id) {
        debugLog(`🔄 언어 변경 감지: ${oldLocale} → ${newLocale}, 시험 데이터 다시 로드`)
        // 사용자 프로필 언어 캐시 무효화
        this.userProfileLanguage = null
        // 시험 데이터 다시 로드
        this.loadExam(this.exam.id)
      }
    },
    searchTerm(newValue) {
      this.setStoredFilter('searchTerm', newValue)
    },
    difficultyFilter(newValue) {
      this.setStoredFilter('difficultyFilter', newValue)
    },
    answerFilter(newValue) {
      this.setStoredFilter('answerFilter', newValue)
    },
    favoriteFilter(newValue) {
      this.setStoredFilter('favoriteFilter', newValue)
    },
    ignoreFilter(newValue) {
      this.setStoredFilter('ignoreFilter', newValue)
    },
    groupIdFilter(newValue) {
      this.setStoredFilter('groupIdFilter', newValue)
    },
    originalExamFilter(newValue) {
      this.setStoredFilter('originalExamFilter', newValue)
    },
    selectedStudyId(newValue) {
      // 스터디 선택 상태가 변경될 때마다 sessionStorage에 저장
      if (this.exam && this.exam.id && newValue) {
        sessionStorage.setItem(`exam_${this.exam.id}_selectedStudyId`, newValue)
      }
    },
    // interviewPromptText watch 제거 - startVoiceInterview에서 직접 처리
    showVoiceInterview(newValue, oldValue) {
      // 🔵 showVoiceInterview 변경 감지 로그 (항상 출력)
      console.log('🔵🔵🔵 [WATCH] showVoiceInterview 변경됨! 🔵🔵🔵')
      console.log('🔵 [WATCH] 변경 전:', oldValue, '→ 변경 후:', newValue)
      if (newValue) {
        console.log('🔵 [WATCH] showVoiceInterview가 true로 변경됨 - MobileVoiceInterview 컴포넌트가 마운트됩니다!')
        console.log('🔵 [WATCH] 이 시점의 interviewPromptText:', {
          value: this.interviewPromptText,
          length: this.interviewPromptText ? this.interviewPromptText.length : 0,
          preview: this.interviewPromptText ? this.interviewPromptText.substring(0, 200) + '...' : '없음',
          full: this.interviewPromptText || '(비어있음)'
        })
        console.log('🟢 [WATCH] MobileVoiceInterview 컴포넌트 렌더링 시작')
        console.log('🟢 [WATCH] 전달할 instructions prop:', {
          value: this.interviewPromptText,
          length: this.interviewPromptText ? this.interviewPromptText.length : 0,
          preview: this.interviewPromptText ? this.interviewPromptText.substring(0, 200) + '...' : '없음',
          full: this.interviewPromptText || '(비어있음)'
        })
        console.log('🟢 [WATCH] exam-id prop:', this.selectedQuestionForAI?.id)
        console.log('🟢 [WATCH] exam-title prop:', this.selectedQuestionForAI?.localized_title || this.selectedQuestionForAI?.title)
        console.log('🟢 [WATCH] language prop:', this.currentLanguage)
      } else {
        console.log('🔵 [WATCH] showVoiceInterview가 false로 변경됨 - MobileVoiceInterview 컴포넌트가 언마운트됩니다!')
      }
    },
    // watcher 제거 (무한 루프 방지)
    // filteredQuestions(newVal) {
    //   const maxCount = Math.min(newVal.length, 10)
    //   this.selectedQuestionCount = maxCount > 0 ? maxCount : 1
    // },
    // questions(newVal) {
    //   if (newVal && newVal.length > 0) {
    //     const maxCount = Math.min(newVal.length, 10)
    //     this.selectedQuestionCount = maxCount
    //   }
    // }
    
    // route 변경 감지하여 즐겨찾기 모드 활성화
    '$route'(to, from) {
      debugLog('=== route 변경 감지 ===')
      debugLog('to.path:', to.path)
      debugLog('to.name:', to.name)
      debugLog('from.path:', from?.path)
      
      // /favorites 경로로 이동한 경우 즐겨찾기 모드 활성화
      if (to.path === '/favorites') {
        debugLog('즐겨찾기 경로 감지 - 즐겨찾기 모드 활성화')
        this.isFavoriteMode = true
        this.favoriteModeTitle = '즐겨찾기'
        
        // 즐겨찾기 모드에서는 ignore 필터를 'All Ignores'로 설정
        this.ignoreFilter = ''
        this.setStoredFilter('ignoreFilter', '')
        
        // 즐겨찾기 모드로 전환
        this.$nextTick(async () => {
          await this.loadExam(null)
        })
      }
    }
  },
  async mounted() {
    debugLifecycle('ExamDetail', 'mounted')
    
    // props와 route 정보 로깅
    debugLog('=== ExamDetail mounted 시작 ===')
    debugLog('props.favoriteMode:', this.favoriteMode)
    debugLog('props.examId:', this.examId)
    debugLog('route.params.examId:', this.$route.params.examId)
    debugLog('route.path:', this.$route.path)
    debugLog('route.name:', this.$route.name)
    
    // 모바일 환경 감지 및 로깅
    this.isMobileDevice = this.checkIsMobileDevice()
    debugLog('📱 [mounted] 모바일 환경 감지 결과:', this.isMobileDevice)
    debugLog('📱 [mounted] window.Capacitor 존재:', typeof window !== 'undefined' && !!window.Capacitor)
    if (typeof window !== 'undefined' && window.Capacitor) {
      try {
        if (typeof window.Capacitor.isNativePlatform === 'function') {
          debugLog('📱 [mounted] isNativePlatform():', window.Capacitor.isNativePlatform())
        }
        if (typeof window.Capacitor.getPlatform === 'function') {
          debugLog('📱 [mounted] getPlatform():', window.Capacitor.getPlatform())
        }
      } catch (error) {
        debugLog('📱 [mounted] Capacitor 정보 확인 실패:', error)
      }
    }
    if (typeof navigator !== 'undefined') {
      debugLog('📱 [mounted] User-Agent:', navigator.userAgent)
    }
    
    // localhost 환경에서만 문제 붙여넣기 체크박스 표시
    this.showPasteProblemCheckbox = this.isDevelopment
    
    // 페이지 포커스 시 통계 새로고침
    window.addEventListener('focus', this.handlePageFocus)
    
    // 드롭다운 메뉴 외부 클릭 시 닫기
    document.addEventListener('click', this.handleOutsideClick)
    
    // examId 변수 선언
    let examId
    
    // 즐겨찾기 모드 확인 (props 또는 경로 기반)
    if (this.favoriteMode || this.$route.path === '/favorites') {
      this.isFavoriteMode = true
      this.favoriteModeTitle = '즐겨찾기'
      debugLog('즐겨찾기 모드로 진입 - props.favoriteMode:', this.favoriteMode, 'route.path:', this.$route.path)
      
      // 즐겨찾기 모드에서는 ignore 필터를 'All Ignores'로 설정
      this.ignoreFilter = ''
      this.setStoredFilter('ignoreFilter', '')
      
      // 즐겨찾기 모드에서는 examId를 null로 설정하여 loadExam에서 처리하도록 함
      examId = null
    } else {
      // 일반 모드인 경우 props 또는 route params에서 examId 가져오기
      examId = this.examId || this.$route.params.examId
      debugLog('일반 모드 - examId:', examId)
    }
    
    // URL 파라미터에서 타임스탬프가 있으면 필터 초기화 (시험 완료 후 새로고침)
    const urlParams = new URLSearchParams(window.location.search)
    if (urlParams.has('t')) {
      debugLog('시험 완료 후 새로고침 감지 - 필터 초기화')
      this.resetFilters()
    }
    
    // 번역 로딩 상태 확인 및 업데이트
    this.translationsLoaded = this.$isTranslationsLoaded(this.$i18n.locale)
    debugLog('번역 로딩 상태', { translationsLoaded: this.translationsLoaded, locale: this.$i18n.locale })
    
    // 번역이 로드되지 않았다면 번역 데이터를 다시 로드
    if (!this.translationsLoaded) {
      try {
        await this.$loadTranslations(this.$i18n.locale)
        this.translationsLoaded = this.$isTranslationsLoaded(this.$i18n.locale)
        debugLog('번역 데이터 재로드 완료')
        
        // 번역 로딩 완료 후 컴포넌트 강제 업데이트
        this.$forceUpdate()
      } catch (error) {
        debugLog('번역 데이터 로드 실패', error, 'error')
        debugLog('❌ 번역 데이터 로드 실패:', error, 'error')
        
        // 오류 발생 시에도 fallback 텍스트로 표시되도록 설정
        this.translationsLoaded = true
      }
    }
    
    // AI 모의 인터뷰 번역 키가 없으면 강제로 번역 다시 로드
    if (!this.$t('examDetail.aiMockInterview') || this.$t('examDetail.aiMockInterview') === 'examDetail.aiMockInterview') {
      try {
        debugLog('AI 모의 인터뷰 번역 키 누락, 번역 데이터 다시 로드')
        await this.$loadTranslations(this.$i18n.locale)
        this.$forceUpdate()
      } catch (error) {
        debugLog('AI 모의 인터뷰 번역 로드 실패:', error, 'error')
      }
    }
    
    try {
      // 스터디 목록을 먼저 로드
      await this.loadStudies()
      
      if (examId) {
        debugLog('=== mounted에서 loadExam 호출 시작 ===', { examId })
        await this.loadExam(examId)
        debugLog('=== mounted에서 loadExam 완료 ===', { examId })
        
        // loadAvailableExams는 Options 모달을 열 때만 로드 (성능 최적화)
        
        // loadLatestResult 호출 (loadQuestions 완료 후)
        await this.loadLatestResult(examId)
        
        // Voice Interview 결과 개수 확인
        await this.loadVoiceInterviewResultsCount(examId)
      } else if (this.isFavoriteMode) {
        // 즐겨찾기 모드인 경우 loadExam 호출 (examId는 null이지만 loadExam에서 처리)
        debugLog('=== 즐겨찾기 모드에서 loadExam 호출 시작 ===')
        await this.loadExam(null)
        debugLog('=== 즐겨찾기 모드에서 loadExam 완료 ===')
      }
      
      if (this.exam && this.exam.id) {
        
        // 저장된 스터디 선택 상태 복원
        this.restoreSelectedStudy()
        
        // loadQuestions에서 이미 loadFavoriteStatus를 호출했으므로 중복 호출 제거
        // await this.loadFavoriteStatus()
        await this.loadIgnoredQuestions()
      }
      
      debugLog('ExamDetail mounted 완료')
    } catch (error) {
      debugLog('초기 로드 실패', error, 'error')
    }
  },
  beforeDestroy() {
    // 이벤트 리스너 제거
    window.removeEventListener('focus', this.handlePageFocus)
    document.removeEventListener('click', this.handleOutsideClick)
  }
}
</script>

<style scoped>
/* Modern Exam Detail Styles */
.exam-detail-modern {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100vh;
  color: white;
}

/* Loading Container - StudyManagement와 동일한 스타일 */
.loading-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100vh;
  color: white;
}

.loading-container .spinner-border {
  width: 3rem;
  height: 3rem;
}

.loading-container p {
  margin-top: 20px;
  font-size: 1.1rem;
  opacity: 0.9;
}

/* 문제 목록 로딩 (테이블 영역 내부) */
.loading-questions {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 60px 20px;
  color: #6c757d;
}

.loading-questions .spinner-border {
  width: 3rem;
  height: 3rem;
  color: #007bff;
}

.loading-questions p {
  margin-top: 1rem;
  font-size: 1.1rem;
  color: #6c757d;
}

.exam-container {
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

.action-btn-success {
  border-color: #28a745;
  background: #28a745;
  color: white;
}

.action-btn-success:hover:not(:disabled) {
  background: #218838;
  border-color: #1e7e34;
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

.action-btn-info {
  border-color: #17a2b8;
  background: #17a2b8;
  color: white;
}

.action-btn-info:hover:not(:disabled) {
  background: #138496;
  border-color: #117a8b;
}

.ai-mock-interview-btn {
  border-color: #ff6b35 !important;
  background: linear-gradient(135deg, #ff8c42 0%, #ff6b35 100%) !important;
  color: white !important;
}

.ai-mock-interview-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #ff6b35 0%, #ff5722 100%) !important;
  border-color: #ff5722 !important;
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

/* Exam Info Card */
.exam-info-card {
  padding: 30px;
  background: white;
  border-bottom: 1px solid #e9ecef;
}

.exam-info-card > .action-btn-large {
  display: block;
  margin-left: auto;
  margin-right: 0;
}

.card-header-modern {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e9ecef;
}

.card-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.card-header-modern h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
}

.card-action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: 1px solid #e9ecef;
  border-radius: 20px;
  background: #f8f9fa;
  color: #6c757d;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.card-action-btn:hover {
  background: #007bff;
  color: white;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 10px;
  border: 1px solid #e9ecef;
}

.info-label {
  font-weight: 600;
  color: #495057;
}

.info-value {
  font-weight: 500;
  color: #2c3e50;
}

.score-value {
  color: #28a745;
  font-weight: 600;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-public {
  background: #d4edda;
  color: #155724;
}

.status-private {
  background: #f8d7da;
  color: #721c24;
}

.status-enabled {
  background: #d1ecf1;
  color: #0c5460;
}

.status-disabled {
  background: #f8d7da;
  color: #721c24;
}

.file-link {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #007bff;
  text-decoration: none;
  font-weight: 500;
}

.file-link:hover {
  color: #0056b3;
  text-decoration: underline;
}

.progress-button {
  display: inline-block;
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
  font-weight: 500;
  line-height: 1.5;
  text-align: center;
  text-decoration: none;
  vertical-align: middle;
  cursor: pointer;
  border: 1px solid #007bff;
  border-radius: 0.375rem;
  color: #007bff;
  background-color: transparent;
  transition: all 0.15s ease-in-out;
}

.progress-button:hover {
  color: #fff;
  background-color: #007bff;
  border-color: #007bff;
  text-decoration: none;
}

.description-section {
  margin-top: 20px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 10px;
  border: 1px solid #e9ecef;
}

.description-section h4 {
  margin: 0 0 15px 0;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.description-content {
  line-height: 1.6;
  color: #495057;
}

/* Edit Form */
.edit-form {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 10px;
  border: 1px solid #e9ecef;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group input[type="range"] {
  margin-top: 18px;
}

.form-group label {
  font-weight: 600;
  color: #495057;
  font-size: 14px;
}

.form-control {
  padding: 10px 12px;
  border: 1px solid #ced4da;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.3s ease;
}

.form-control:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

/* Range Input 스타일 - 그라데이션 배경 */
input[type="range"].form-control {
  -webkit-appearance: none;
  appearance: none;
  height: 8px;
  background: transparent;
  padding: 0;
}

/* Webkit 브라우저 (Chrome, Safari, Edge) */
input[type="range"].form-control::-webkit-slider-runnable-track {
  width: 100%;
  height: 8px;
  background: linear-gradient(to right, #ffffff 0%, #ff0000 100%);
  border-radius: 4px;
  cursor: pointer;
}

input[type="range"].form-control::-webkit-slider-thumb {
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

input[type="range"].form-control::-webkit-slider-thumb:hover {
  transform: scale(1.1);
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3);
}

/* Firefox */
input[type="range"].form-control::-moz-range-track {
  width: 100%;
  height: 8px;
  background: linear-gradient(to right, #ffffff 0%, #ff0000 100%);
  border-radius: 4px;
  cursor: pointer;
  border: none;
}

input[type="range"].form-control::-moz-range-thumb {
  width: 20px;
  height: 20px;
  background: #007bff;
  border-radius: 50%;
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  transition: all 0.2s ease;
}

input[type="range"].form-control::-moz-range-thumb:hover {
  transform: scale(1.1);
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3);
}

/* IE/Edge */
input[type="range"].form-control::-ms-track {
  width: 100%;
  height: 8px;
  background: transparent;
  border-color: transparent;
  color: transparent;
  cursor: pointer;
}

input[type="range"].form-control::-ms-fill-lower {
  background: linear-gradient(to right, #ffffff 0%, #ff0000 100%);
  border-radius: 4px;
}

input[type="range"].form-control::-ms-fill-upper {
  background: linear-gradient(to right, #ffffff 0%, #ff0000 100%);
  border-radius: 4px;
}

input[type="range"].form-control::-ms-thumb {
  width: 20px;
  height: 20px;
  background: #007bff;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.checkbox-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-check-input {
  margin: 0;
}

.form-check-label {
  margin: 0;
  font-weight: 500;
  color: #495057;
}

.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

/* Questions Section */
.questions-section {
  padding: 30px;
}

.control-card {
  margin-bottom: 30px;
  padding: 25px;
  background: white;
  border-radius: 15px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid #e9ecef;
}

.control-content {
  margin-top: 20px;
}

.control-row {
  display: flex;
  gap: 15px;
  align-items: end;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 200px;
}

.control-group label {
  font-weight: 600;
  color: #495057;
  font-size: 14px;
}

.spacer {
  flex: 1;
}

.selected-count {
  font-weight: 500;
  color: #007bff;
  font-size: 14px;
}

.control-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  flex-wrap: wrap;
}

/* Upload Section */
.upload-info {
  background: #e3f2fd;
  padding: 20px;
  border-radius: 10px;
  margin-bottom: 20px;
  border: 1px solid #bbdefb;
}

.upload-info h6 {
  margin: 0 0 15px 0;
  color: #1976d2;
  font-weight: 600;
}

.upload-info p {
  margin: 0 0 8px 0;
  color: #424242;
  font-size: 14px;
}

.upload-form {
  display: flex;
  gap: 15px;
  align-items: end;
  flex-wrap: wrap;
}

.upload-input {
  flex: 1;
  min-width: 300px;
}

.upload-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end !important;
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
}

/* Filter Card */
.filter-card {
  margin-bottom: 30px;
  padding: 25px;
  background: white;
  border-radius: 15px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid #e9ecef;
}

.filter-content {
  margin-top: 20px;
}

.filter-row {
  display: flex;
  gap: 15px;
  align-items: end;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.filter-row.mobile-hidden {
  display: none;
}

.mobile-filter-toggle {
  display: flex;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 150px;
}

/* Tag Management Card Styling */
.tag-management-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(66, 165, 245, 0.1);
  padding: 30px;
  margin: 20px 0;
  border: 2px solid #e3f2fd;
}

.tag-management-card .card-header-modern {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e3f2fd;
}

.tag-management-card .card-header-modern h3 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 10px;
}


/* Group ID Filter Input Styling */
.group-id-filter {
  border-radius: 20px !important;
  border: 1px solid var(--bs-gray-300) !important;
  background: white !important;
  color: var(--bs-gray-700) !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  padding: 10px 16px !important;
  transition: all 0.3s ease !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
}

.group-id-filter:focus {
  border-color: var(--bs-primary) !important;
  box-shadow: 0 0 0 0.2rem rgba(13, 110, 253, 0.15) !important;
  outline: none !important;
}

.group-id-filter::placeholder {
  color: var(--bs-gray-500) !important;
  font-weight: 400 !important;
}

/* Reset Filter Button Styling */
.reset-filter-btn {
  border-radius: 50rem !important;
  border: 2px solid var(--bs-gray-600) !important;
  background: white !important;
  color: var(--bs-gray-600) !important;
  font-weight: 500 !important;
  transition: all 0.3s ease !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
}

.reset-filter-btn:hover:not(:disabled) {
  background: var(--bs-gray-600) !important;
  border-color: var(--bs-gray-600) !important;
  color: white !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15) !important;
}

.filter-group label {
  font-weight: 600;
  color: #495057;
  font-size: 14px;
}

.filter-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  flex-wrap: wrap;
}

/* Questions Table */
.questions-table {
  background: white;
  border-radius: 15px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid #e9ecef;
  overflow: hidden;
  width: 100%;
  display: flex;
  flex-direction: column;
}

.table-header {
  display: grid;
  grid-template-columns: 50px 80px 100px 35% 100px 100px 100px 100px 120px 100px;
  gap: 15px;
  padding: 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  font-weight: 600;
  color: #495057;
  align-items: center;
  width: 100%;
  min-width: 0;
  flex-shrink: 0;
}

.table-column {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  user-select: none;
  transition: color 0.3s ease;
}

.table-column:hover {
  color: #007bff;
}

.sort-icon {
  font-size: 12px;
  color: #6c757d;
}

.table-select-all {
  display: flex;
  align-items: center;
  justify-content: center;
}

.table-body {
  max-height: 600px;
  overflow-y: auto;
  width: 100%;
  flex: 1;
}

.no-questions {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #6c757d;
  text-align: center;
}

.no-questions i {
  font-size: 48px;
  margin-bottom: 20px;
  color: #dee2e6;
}

.no-questions p {
  margin: 0 0 10px 0;
  font-size: 18px;
  font-weight: 500;
}

.no-questions small {
  color: #adb5bd;
}

.table-row {
  display: grid;
  grid-template-columns: 50px 80px 100px 35% 100px 100px 100px 100px 120px 100px;
  gap: 15px;
  padding: 15px 20px;
  border-bottom: 1px solid #f1f3f4;
  align-items: center;
  transition: background-color 0.3s ease;
  width: 100%;
  min-width: 0;
}

.table-row:hover {
  background: #f8f9fa;
}

.table-row.selected {
  background: #e3f2fd;
}

.table-cell {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: #495057;
  overflow: hidden;
  min-width: 0;
}

.question-link {
  color: #007bff;
  text-decoration: none;
  font-weight: 500;
}

.question-link:hover {
  color: #0056b3;
  text-decoration: underline;
}

.group-id {
  background: #e9ecef;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  word-break: break-word;
  overflow-wrap: break-word;
  max-width: 100%;
  display: block;
  cursor: pointer;
  transition: all 0.2s ease;
  line-height: 1.2;
}

.group-id:hover {
  background: #dee2e6;
  transform: scale(1.02);
  z-index: 10;
  position: relative;
}



.no-group {
  color: #adb5bd;
}

.difficulty-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.difficulty-badge.bg-success {
  background: #d4edda;
  color: #155724;
}

.difficulty-badge.bg-warning {
  background: #fff3cd;
  color: #856404;
}

.difficulty-badge.bg-danger {
  background: #f8d7da;
  color: #721c24;
}

.difficulty-badge.bg-secondary {
  background: #e9ecef;
  color: #495057;
}

.correct-count, .attempt-count {
  font-weight: 600;
  color: #28a745;
}

.no-stats {
  color: #adb5bd;
}

.original-exam {
  margin-bottom: 5px;
}

.exam-link {
  color: #007bff;
  text-decoration: none;
  font-size: 12px;
}

.exam-link:hover {
  color: #0056b3;
  text-decoration: underline;
}

.status-badges {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

.status-favorite {
  background: #fff3cd;
  color: #856404;
}

.status-ignored {
  background: #f8d7da;
  color: #721c24;
}

.no-status {
  color: #adb5bd;
}

/* Responsive Design */
@media (max-width: 1200px) {
  .table-header,
  .table-row {
    grid-template-columns: 50px 80px 100px 30% 100px 100px 100px 100px 120px 100px;
  }
}

@media (max-width: 768px) {
  .exam-detail-modern {
    padding: 10px;
  }
  
  .exam-container {
    border-radius: 15px;
  }
  
  .top-header {
    justify-content: center;
    padding: 10px;
  }
  
  .page-title {
    padding: 10px;
  }
  
  .page-title h1 {
    font-size: 24px;
  }
  
  .exam-info-card {
    padding: 10px;
  }
  
  .card-header-modern {
    margin-bottom: 0;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
    margin-bottom: 0px;
  }
  
  .questions-section {
    padding: 10px;
  }
  
  .filter-card {
    padding: 10px;
  }
  
  .filter-content {
    margin-top: 0;
  }
  
  .control-row,
  .filter-row {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filter-row.mobile-hidden {
    display: none;
  }
  
  .mobile-filter-toggle {
    display: flex;
  }
  
  .exam-info-card > .action-btn-large {
    margin-left: auto;
    margin-right: auto;
    margin-bottom: 0;
  }
  
  .control-group,
  .filter-group {
    min-width: auto;
  }
  
  .control-actions,
  .filter-actions {
    justify-content: center;
  }
  
  .reset-filter-btn {
    align-self: flex-end;
    margin-left: auto;
  }
  
  .table-header,
  .table-row {
    grid-template-columns: 40px 60px 80px 1fr 80px 80px 80px 80px;
    font-size: 12px;
    gap: 10px;
    padding: 10px 15px;
  }
  
  .table-cell {
    font-size: 12px;
  }
  
  /* 원형 버튼 스타일은 공통 CSS (mobile-buttons.css)에서 처리됨 */
  
  /* progress-button을 원형 버튼으로 */
  .progress-button {
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
  
  /* 기존 내용 숨기기 */
  .progress-button i,
  .progress-button > * {
    display: none !important;
  }
  
  /* 아이콘을 ::after로 표시 */
  .progress-button::after {
    content: '\f080'; /* Font Awesome chart-bar icon */
    font-family: 'Font Awesome 5 Free';
    font-weight: 900;
    font-size: 16px !important;
    color: #007bff;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
  }
  
  /* card-action-btn을 원형 버튼으로 */
  .card-action-btn {
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
  
  .card-action-btn i {
    font-size: 14px !important;
    line-height: 1 !important;
  }
  
  .card-action-btn .action-label {
    display: none !important;
  }
  
  .card-actions {
    flex-wrap: wrap;
  }
  
  .card-actions .action-btn-large {
    flex-basis: 100%;
    margin-top: 5px;
    margin-bottom: 10px;
    margin-left: auto;
    margin-right: auto;
  }
  
  .action-btn-large {
    padding: 10px 16px !important;
    width: auto !important;
    min-width: 200px !important;
    height: auto !important;
    border-radius: 25px !important;
    gap: 8px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
  }
  
  .action-btn-large .action-label {
    display: inline !important;
    font-size: 14px !important;
  }
  
  .action-btn-large i {
    font-size: 14px !important;
  }
  
  .options-actions .action-btn {
    padding: 0 !important;
    width: 40px !important;
    height: 40px !important;
    border-radius: 50% !important;
    gap: 0 !important;
    min-width: auto !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
  }
  
  .options-actions .action-btn span {
    display: none !important;
  }
  
  .options-actions .action-btn i {
    font-size: 14px !important;
    line-height: 1 !important;
  }
  
  .action-label {
    display: none;
  }
}

@media (max-width: 576px) {
  .header-actions {
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .action-btn {
    padding: 0;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    gap: 0;
    min-width: auto;
  }
  
  .action-btn-large {
    padding: 10px 16px !important;
    width: auto !important;
    min-width: 180px !important;
    height: auto !important;
    border-radius: 25px !important;
    gap: 8px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
  }
  
  .action-btn-large .action-label {
    display: inline !important;
    font-size: 12px !important;
  }
  
  .action-btn-large i {
    font-size: 12px !important;
  }
  
  .card-action-btn {
    width: 36px !important;
    height: 36px !important;
  }
  
  .card-action-btn i {
    font-size: 12px !important;
  }
  
  .options-actions .action-btn {
    padding: 0 !important;
    width: 36px !important;
    height: 36px !important;
    border-radius: 50% !important;
    gap: 0 !important;
    min-width: auto !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
  }
  
  .options-actions .action-btn span {
    display: none !important;
  }
  
  .options-actions .action-btn i {
    font-size: 12px !important;
    line-height: 1 !important;
  }
  
  .top-header {
    padding: 10px;
  }
  
  .page-title {
    padding: 10px;
  }
  
  .exam-info-card {
    padding: 10px;
  }
  
  .questions-section {
    padding: 10px;
  }
  
  .filter-card {
    padding: 10px;
  }
  
  .table-header,
  .table-row {
    grid-template-columns: 30px 50px 60px 1fr 60px 60px 60px;
    gap: 8px;
    padding: 8px 10px;
  }
  
  .table-cell {
    font-size: 11px;
  }
  
  .difficulty-badge,
  .status-badge {
    font-size: 10px;
    padding: 2px 4px;
  }
}

/* Toast Notifications - 기본 스타일은 공통 CSS (mobile-buttons.css)에 정의됨 */

/* 타입별 스타일은 공통 CSS (mobile-buttons.css)에 정의됨 */

.toast-content {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.toast-content i {
  font-size: 18px;
}

.toast-content span {
  font-size: 14px;
  font-weight: 500;
}

.toast-close {
  background: none;
  border: none;
  color: #6c757d;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.toast-close:hover {
  background-color: #f8f9fa;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 2000; /* 모달 오버레이 */
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.2s ease-out;
}

.modal-content {
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  max-width: 750px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  animation: slideInUp 0.3s ease-out;
  z-index: 2100; /* 모달 콘텐츠 */
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 1px solid #e9ecef;
}

.modal-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 12px;
}

.modal-title i {
  font-size: 20px;
}

.modal-close {
  background: none;
  border: none;
  color: #6c757d;
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: background-color 0.2s;
}

.modal-close:hover {
  background-color: #f8f9fa;
}

.modal-body {
  padding: 20px 24px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px 20px;
  border-top: 1px solid #e9ecef;
}

.btn {
  padding: 8px 16px;
  border-radius: 6px;
  border: 1px solid transparent;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary {
  background: #6c757d;
  color: white;
  border-color: #6c757d;
}

.btn-secondary:hover {
  background: #5a6268;
  border-color: #545b62;
}

.btn-success {
  background: #28a745;
  color: white;
  border-color: #28a745;
}

.btn-success:hover {
  background: #218838;
  border-color: #1e7e34;
}

.btn-danger {
  background: #dc3545;
  color: white;
  border-color: #dc3545;
}

.btn-danger:hover {
  background: #c82333;
  border-color: #bd2130;
}

.btn-warning {
  background: #ffc107;
  color: #212529;
  border-color: #ffc107;
}

.btn-warning:hover {
  background: #e0a800;
  border-color: #d39e00;
}

.btn-info {
  background: #17a2b8;
  color: white;
  border-color: #17a2b8;
}

.btn-info:hover {
  background: #138496;
  border-color: #117a8b;
}

/* Animations */
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
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.dropdown-menu-container {
  position: relative;
  display: inline-block;
  z-index: 1000; /* 드롭다운 */
  /* 컨테이너가 제대로 표시되도록 설정 */
  overflow: visible !important;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(102, 126, 234, 0.2);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.2);
  z-index: 2100; /* 모달 콘텐츠 */
  min-width: 200px;
  padding: 8px 0;
  margin-top: 8px;
  animation: dropdownFadeIn 0.3s ease-out;
  /* 강제로 표시되도록 설정 */
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
}

@keyframes dropdownFadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
  background: none;
  width: 100%;
  text-align: left;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  position: relative;
  overflow: hidden;
}

.dropdown-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  width: 0;
  height: 100%;
  background: linear-gradient(90deg, rgba(102, 126, 234, 0.1), transparent);
  transition: width 0.3s ease;
}

.dropdown-item:hover::before {
  width: 100%;
}

.dropdown-item:hover {
  color: #667eea;
  transform: translateX(4px);
}

.dropdown-item:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.dropdown-item:disabled:hover {
  background-color: transparent;
  color: #333;
  transform: none;
}

.dropdown-item i {
  font-size: 16px;
  min-width: 20px;
  text-align: center;
}

/* 관리자 드롭다운 메뉴 스타일 */
.admin-dropdown-container {
  position: relative;
  display: inline-block;
  z-index: 1000; /* 드롭다운 */
  overflow: visible !important;
}

.admin-dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(220, 53, 69, 0.2);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(220, 53, 69, 0.2);
  z-index: 1100; /* 드롭다운 메뉴 */
  min-width: 200px;
  padding: 8px 0;
  margin-top: 8px;
  animation: dropdownFadeIn 0.3s ease-out;
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
}

.admin-dropdown-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(220, 53, 69, 0.3);
  position: relative;
  overflow: hidden;
}

.admin-dropdown-toggle::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.admin-dropdown-toggle:hover::before {
  left: 100%;
}

.admin-dropdown-toggle:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(220, 53, 69, 0.4);
}

.admin-dropdown-toggle.active {
  background: linear-gradient(135deg, #c82333 0%, #dc3545 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(200, 35, 51, 0.4);
}

.admin-dropdown-toggle i {
  font-size: 16px;
  font-weight: 600;
  z-index: 1;
  position: relative;
}

.admin-dropdown-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
  background: none;
  width: 100%;
  text-align: left;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  position: relative;
  overflow: hidden;
}

.admin-dropdown-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  width: 0;
  height: 100%;
  background: linear-gradient(90deg, rgba(220, 53, 69, 0.1), transparent);
  transition: width 0.3s ease;
}

.admin-dropdown-item:hover::before {
  width: 100%;
}

.admin-dropdown-item:hover {
  color: #dc3545;
  transform: translateX(4px);
}

.admin-dropdown-item:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.admin-dropdown-item:disabled:hover {
  background-color: transparent;
  color: #333;
  transform: none;
}

.admin-dropdown-item i {
  font-size: 16px;
  min-width: 20px;
  text-align: center;
}

.dropdown-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
  position: relative;
  overflow: hidden;
}

.dropdown-toggle::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.dropdown-toggle:hover::before {
  left: 100%;
}

.dropdown-toggle:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.dropdown-toggle.active {
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(118, 75, 162, 0.4);
}

.dropdown-toggle i {
  font-size: 16px;
  font-weight: 600;
  z-index: 1;
  position: relative;
}

/* 화살표 제거 */
.dropdown-toggle::after {
  display: none !important;
  content: none !important;
}

/* Options Modal Styles */
.options-modal {
  max-width: 1200px;
  width: 95%;
  max-height: 80vh;
  overflow-y: auto;
  z-index: 2100 !important; /* 모달 콘텐츠 */
}

.options-content {
  padding: 20px 0;
}

.options-section {
  margin-bottom: 30px;
  padding: 20px;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  background-color: #f8f9fa;
}

.options-section h6 {
  margin-bottom: 15px;
  color: #495057;
  font-weight: 600;
  font-size: 16px;
}

.options-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
  margin-bottom: 15px;
}

.option-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.option-group label {
  font-weight: 500;
  color: #495057;
  font-size: 14px;
}

.option-group .form-control {
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
}

.option-group .selected-count {
  font-weight: 600;
  color: #007bff;
  font-size: 14px;
}

.options-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.options-actions .action-btn {
  padding: 8px 16px;
  font-size: 14px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.options-actions .action-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.options-actions .action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* 정확도 조정 컨트롤 스타일 */
.accuracy-adjustment-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #f8f9fa;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.accuracy-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  font-size: 12px;
}

.accuracy-btn-decrease {
  background: #dc3545;
  color: white;
}

.accuracy-btn-decrease:hover {
  background: #c82333;
  transform: scale(1.05);
}

.accuracy-btn-increase {
  background: #28a745;
  color: white;
}

.accuracy-btn-increase:hover {
  background: #218838;
  transform: scale(1.05);
}

.accuracy-slider-container {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 120px;
}

.accuracy-slider {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: #e9ecef;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
}

.accuracy-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #007bff;
  cursor: pointer;
  border: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.accuracy-slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #007bff;
  cursor: pointer;
  border: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.accuracy-slider:hover::-webkit-slider-thumb {
  background: #0056b3;
  transform: scale(1.1);
}

.accuracy-slider:hover::-moz-range-thumb {
  background: #0056b3;
  transform: scale(1.1);
}

.accuracy-percentage {
  font-size: 12px;
  font-weight: 600;
  color: #495057;
  min-width: 35px;
  text-align: center;
}

/* Member Mapping Styles */
.member-mapping-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.member-mapping {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  background-color: #f8f9fa;
  border-radius: 4px;
  font-size: 12px;
}

.member-name {
  font-weight: 500;
  color: #495057;
}

.no-mapping {
  color: #6c757d;
  font-style: italic;
  font-size: 12px;
}

/* 문제 수 정보 스타일 */
.question-count-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background-color: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
  font-size: 14px;
  min-width: fit-content;
  position: absolute;
  left: 0;
  z-index: 10;
}

/* filter-actions를 왼쪽 벽쪽으로 붙이기 */
.filter-actions {
  position: relative;
}

.count-label {
  color: #6c757d;
  font-weight: 500;
}

.count-value {
  color: #495057;
  font-weight: 600;
  min-width: 20px;
  text-align: center;
}

.count-value.selected {
  color: #007bff;
  font-weight: 700;
}

.count-separator {
  color: #dee2e6;
  font-weight: 300;
  margin: 0 4px;
}

/* 즐겨찾기/무시하기 토글 버튼 스타일 */
.status-favorite-toggle,
.status-ignore-toggle {
  background: none;
  border: none;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 12px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin: 2px;
}

.status-favorite-toggle:hover,
.status-ignore-toggle:hover {
  transform: scale(1.05);
}

.status-favorite-toggle.status-favorite {
  background-color: #ffc107;
  color: #212529;
}

.status-favorite-toggle.status-not-favorite {
  background-color: #e9ecef;
  color: #6c757d;
}

.status-favorite-toggle.status-not-favorite:hover {
  background-color: #ffc107;
  color: #212529;
}

.status-ignore-toggle.status-ignored {
  background-color: #dc3545;
  color: white;
}

.status-ignore-toggle.status-not-ignored {
  background-color: #e9ecef;
  color: #6c757d;
}

.status-ignore-toggle.status-not-ignored:hover {
  background-color: #dc3545;
  color: white;
}

/* 연결된 프로젝트 스타일 */
.connected-projects {
  display: flex;
  align-items: center;
}

.single-project .project-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #007bff;
  text-decoration: none;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s ease;
  font-size: 14px;
}

.single-project .project-link:hover {
  background-color: #f8f9fa;
  color: #0056b3;
  text-decoration: none;
}

.multiple-projects {
  position: relative;
}

.project-selector {
  position: relative;
}

.project-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  z-index: 1000;
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  min-width: 200px;
  max-width: 300px;
}

.project-item {
  padding: 8px 12px;
  border-bottom: 1px solid #f8f9fa;
}

.project-item:last-child {
  border-bottom: none;
}

.project-item .project-link {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #007bff;
  text-decoration: none;
  font-size: 14px;
  width: 100%;
}

.project-item .project-link:hover {
  color: #0056b3;
  text-decoration: none;
}

/* 모바일에서 시험 정보 제목 숨기기 */
@media (max-width: 768px) {
  .exam-info-card .card-header-modern h3 {
    display: none;
  }
  
  /* 모바일에서 문제 수 정보 숨기기 */
  .question-count-info {
    display: none; /* 모바일에서 숨김 */
  }
  
  .count-separator {
    display: none;
  }
  
  /* 그리드 레이아웃을 체크박스 + Title 2컬럼으로 변경 */
  .table-header,
  .table-row {
    grid-template-columns: 40px 1fr !important;
  }
  
  /* 체크박스는 고정 너비, Title은 나머지 공간 사용 */
  .table-header .table-column:nth-child(1),
  .table-row .table-cell:nth-child(1) {
    width: 40px !important;
    flex: 0 0 40px !important;
  }
  
  .table-header .table-column:nth-child(4),
  .table-row .table-cell:nth-child(4) {
    width: 100% !important;
    flex: 1 !important;
    min-width: 0 !important;
  }
  
  /* Title 컬럼의 폰트 크기 증가 */
  .table-row .table-cell:nth-child(4) {
    font-size: 16px !important;
    line-height: 1.4 !important;
  }
  
  .table-row .table-cell:nth-child(4) .question-link {
    font-size: 16px !important;
    line-height: 1.4 !important;
  }
  
  .table-row .table-cell:nth-child(4) strong {
    font-size: 16px !important;
    line-height: 1.4 !important;
  }
  
  /* 나머지 컬럼들 숨기기 (체크박스와 Title 제외) */
  .table-header .table-column:nth-child(2),
  .table-header .table-column:nth-child(3),
  .table-header .table-column:nth-child(5),
  .table-header .table-column:nth-child(6),
  .table-header .table-column:nth-child(7),
  .table-header .table-column:nth-child(8),
  .table-header .table-column:nth-child(9),
  .table-header .table-column:nth-child(10) {
    display: none !important;
    width: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    flex: 0 !important;
    grid-column: unset !important;
  }
  
  .table-row .table-cell:nth-child(2),
  .table-row .table-cell:nth-child(3),
  .table-row .table-cell:nth-child(5),
  .table-row .table-cell:nth-child(6),
  .table-row .table-cell:nth-child(7),
  .table-row .table-cell:nth-child(8),
  .table-row .table-cell:nth-child(9),
  .table-row .table-cell:nth-child(10) {
    display: none !important;
    width: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    flex: 0 !important;
    grid-column: unset !important;
  }
}

/* AI 모의 인터뷰 관련 스타일 */
.ai-mock-interview-info-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: #f8f9fa;
  color: #6c757d;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
}

.ai-mock-interview-info-btn:hover {
  background: #e9ecef;
  border-color: #adb5bd;
  text-decoration: none;
  color: #6c757d;
}

.ai-mock-interview-info-btn.enabled {
  background: #d4edda;
  border-color: #c3e6cb;
  color: #155724;
}

.ai-mock-interview-info-btn.enabled:hover {
  background: #c3e6cb;
  border-color: #b8dacc;
  color: #155724;
}

.ai-mock-interview-info-btn i {
  font-size: 16px;
}

.ai-mock-interview-detail {
  padding: 16px 0;
}

.ai-mock-interview-detail .exam-info {
  margin-bottom: 20px;
  padding: 12px;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  background: #f8f9fa;
}

.ai-mock-interview-detail h6 {
  margin-bottom: 8px;
  color: #495057;
  font-weight: 600;
}

.ai-mock-interview-detail p {
  margin-bottom: 4px;
  color: #6c757d;
}


/* 클립보드 복사 섹션 스타일 */
.clipboard-section {
  margin-top: 20px;
  padding: 16px;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  background: #f8f9fa;
}

.clipboard-section h6 {
  margin-bottom: 12px;
  color: #495057;
  font-weight: 600;
}

.clipboard-content {
  margin-top: 12px;
}

.interview-prompt {
  display: none;
}

.interview-prompt p {
  margin-bottom: 12px;
  color: #6c757d;
  font-size: 14px;
}

/* 모바일 Voice Interview 관련 스타일 */
.mobile-voice-interview-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 2000; /* 모달 오버레이 */
  background: transparent;
}

.mobile-options {
  margin-bottom: 20px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  text-align: center;
}

.voice-interview-btn {
  width: 100%;
  padding: 15px;
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 10px;
}

.option-description {
  font-size: 14px;
  color: #6c757d;
  margin: 0;
  line-height: 1.6;
}

.prompt-textarea {
  width: 100%;
  background: #ffffff;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 12px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  color: #495057;
  resize: vertical;
  min-height: 300px;
  box-sizing: border-box;
}

.prompt-textarea:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.modal-footer {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  align-items: center;
  padding: 16px 24px;
  border-top: 1px solid #e9ecef;
  background: #f8f9fa;
}

.copy-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.copy-btn:hover {
  background: #0056b3;
  transform: translateY(-1px);
}

.copy-btn:active {
  transform: translateY(0);
}

.copy-btn i {
  font-size: 14px;
}

.reset-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.reset-btn:hover {
  background: #5a6268;
  transform: translateY(-1px);
}

.reset-btn:active {
  transform: translateY(0);
}

.reset-btn i {
  font-size: 14px;
}

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

/* AI 문제 생성기 스타일 */
.ai-question-generator {
  margin-top: 1rem;
}

.ai-generator-card {
  border: 2px solid #e3f2fd;
  background: linear-gradient(135deg, #f8f9ff 0%, #e8f4fd 100%);
  border-radius: 8px;
}

.card-header-modern {
  background: transparent;
  border-bottom: none;
  padding: 0;
}

.card-body {
  padding: 1rem;
}

.textarea-container {
  position: relative;
}

.textarea-container .copy-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 6px 8px;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  transition: all 0.2s ease;
  z-index: 10;
}

.textarea-container .copy-btn:hover {
  background: #f8f9fa;
  color: #333;
  border-color: #999;
}

.textarea-container .copy-btn:active {
  transform: scale(0.95);
}

.parsed-problems {
  margin-top: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.parsed-problems h6 {
  color: #495057;
  margin-bottom: 0.75rem;
  font-weight: 600;
}

.problem-list {
  max-height: 200px;
  overflow-y: auto;
}

.problem-item {
  padding: 0.5rem;
  margin-bottom: 0.5rem;
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.problem-item:last-child {
  margin-bottom: 0;
}

.problem-item:hover {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border-color: #007bff;
}

.problem-item.problem-error {
  color: #dc3545;
  border-color: #dc3545;
  background: #f8d7da;
}

.problem-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.problem-number {
  font-weight: 600;
  color: #666;
  font-size: 0.9rem;
  min-width: 2rem;
}

.problem-title {
  flex: 1;
  color: #333;
  font-size: 0.9rem;
  font-weight: 500;
}

.problem-difficulty {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-weight: 500;
  text-transform: uppercase;
}

.difficulty-Easy {
  background-color: #d4edda;
  color: #155724;
}

.difficulty-Medium {
  background-color: #fff3cd;
  color: #856404;
}

.difficulty-Hard {
  background-color: #f8d7da;
  color: #721c24;
}

.problem-url {
  margin-left: auto;
}

.url-link {
  color: #007bff;
  text-decoration: none;
  font-size: 0.8rem;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.url-link:hover {
  background-color: #e3f2fd;
  color: #0056b3;
}

.generator-actions {
  margin-top: 1rem;
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.generator-actions .btn {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.875rem;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  transition: all 0.2s ease;
}

/* 언어 선택 액션 버튼 스타일 */
.language-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.language-actions .btn {
  display: flex;
  align-items: center;
  gap: 6px;
}

.me-1 {
  margin-right: 0.25rem;
}

</style>