<template>
  <div class="take-exam-modern">
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
    
    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteConfirm" class="modal-overlay" @click="cancelDelete">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h5 class="modal-title">
            <i class="fas fa-exclamation-triangle text-warning me-2"></i>
            {{ $t('takeExam.deleteConfirm.title') }}
          </h5>
          <button class="modal-close" @click="cancelDelete">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <p class="mb-0">{{ $t('takeExam.deleteConfirm.message') }}</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="cancelDelete">
            <i class="fas fa-times"></i>
            <span>{{ $t('takeExam.deleteConfirm.cancel') }}</span>
          </button>
          <button class="btn btn-danger" @click="confirmDelete">
            <i class="fas fa-trash"></i>
            <span>{{ $t('takeExam.deleteConfirm.delete') }}</span>
          </button>
        </div>
      </div>
    </div>
    
    <!-- Share Modal -->
    <ShareModal
      v-if="exam"
      :show="showShareModal"
      :share-url="shareUrl"
      :exam-id="exam.id"
      :is-mobile-device="isMobileDevice"
      @close="closeShareModal"
      @success="showToastMessage"
      @error="(msg) => showToastMessage(msg, 'error')"
    />
    
    <!-- Loading -->
    <div v-if="loading" class="loading-container">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">{{ $t('common.loading') }}</span>
      </div>
      
      <!-- 번역 작업으로 인한 로딩 지연 메시지 -->
      <div v-if="showTranslationMessage" class="translation-message">
        <div class="translation-info">
          <i class="fas fa-language text-info me-2"></i>
          <span>{{ $t('takeExam.translationLoading') }}</span>
        </div>
        <div class="translation-detail">
          <small class="text-muted">{{ $t('takeExam.translationDetail') }}</small>
        </div>
      </div>
    </div>
    
    <div v-else-if="exam" class="exam-container">
      <!-- Top Header -->
      <div class="top-header">
        <div class="header-actions">
          <!-- 연결된 프로젝트 선택 (17+ 등급만 표시) -->
          <div v-if="connectedStudies.length > 0 && showShareButton" class="connected-projects">
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
                  class="modern-btn"
                  :title="$t('examDetail.connectedProjects.multiple')"
                >
                  <i class="fas fa-list"></i>
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
          <button class="modern-btn" @click="toggleFavorite" v-if="isAuthenticated" :title="$t('takeExam.favorite')" :class="{ 'favorite-active': isFavorited }">
            <i class="fas fa-star"></i>
            <span class="btn-text">★</span>
          </button>
          <button class="modern-btn" @click="toggleIgnore" v-if="isAuthenticated" :title="$t('takeExam.ignore')" :class="{ 'ignore-active': isQuestionIgnored }">
            <i class="fas fa-ban"></i>
            <span class="btn-text">✗</span>
          </button>
          <button v-if="showShareButton" class="modern-btn" @click="shareExam" :title="$t('takeExam.share')">
            <i class="fas fa-link"></i>
            <span class="btn-text">↗</span>
          </button>
        </div>
      </div>

      <!-- Page Title -->
      <div class="page-title">
        <h1>{{ localizedExamTitle }}</h1>
        <!-- AI Mock Interview 버튼 (모바일에서만 여기에 표시) -->
        <button 
          v-if="exam && exam.ai_mock_interview && isMobileDevice"
          @click="showAIMockInterviewDetail"
          class="action-btn action-btn-info action-btn-large ai-mock-interview-btn page-title-btn mobile-only"
        >
          <i class="fas fa-robot"></i>
          <span class="action-label">{{ $t('examDetail.aiMockInterview') || 'AI Mock Interview' }}</span>
        </button>
      </div>



              <!-- New Question Form -->
        <div v-if="isAddingNewQuestion" class="question-card">
          <div class="card-header-modern">
            <h3>{{ $t('takeExam.addNewQuestion') }}</h3>
          </div>
          
          <div class="question-content-modern">
            <form @submit.prevent="saveNewQuestion" class="new-question-form">
              <div class="form-group">
                <label>{{ $t('takeExam.questionId') }}:</label>
                <input v-model="newQuestion.csv_id" type="text" class="form-control" required />
              </div>

              <div class="form-group">
                <label>{{ $t('takeExam.title') }}:</label>
                <input v-model="newQuestion.title" type="text" class="form-control" required />
              </div>

              <div class="form-group">
                <label>{{ $t('takeExam.questionContent') }}:</label>
                <textarea v-model="newQuestion.content" class="form-control" rows="4" required></textarea>
              </div>

              <div class="form-group">
                <label>{{ $t('takeExam.answer') }}:</label>
                <textarea v-model="newQuestion.answer" class="form-control" rows="2" required></textarea>
              </div>

              <div class="form-group">
                <label>{{ $t('takeExam.explanation') }}:</label>
                <textarea v-model="newQuestion.explanation" class="form-control" rows="18"></textarea>
              </div>

              <div class="form-row">
                <div class="form-group col-md-6">
                  <label>{{ $t('takeExam.difficulty') }}:</label>
                  <select v-model="newQuestion.difficulty" class="form-control">
                    <option value="">{{ $t('takeExam.selectDifficulty') }}</option>
                    <option value="Easy">{{ $t('takeExam.easy') }}</option>
                    <option value="Medium">{{ $t('takeExam.medium') }}</option>
                    <option value="Hard">{{ $t('takeExam.hard') }}</option>
                  </select>
                </div>

                <div class="form-group col-md-6">
                  <label>{{ $t('takeExam.groupId') }}:</label>
                  <input v-model="newQuestion.group_id" type="text" class="form-control" />
                </div>
              </div>

              <div class="form-group">
                <label>{{ $t('takeExam.url') }}:</label>
                <input v-model="newQuestion.url" type="url" class="form-control" />
              </div>

              <div class="form-actions">
                <button type="submit" class="btn btn-primary">
                  <i class="fas fa-save"></i>
                  <span>{{ $t('takeExam.saveQuestion') }}</span>
                </button>
                <button type="button" @click="saveAndNext" class="btn btn-success">
                  <i class="fas fa-save"></i>
                  <span>{{ $t('takeExam.saveAndNext') }}</span>
                </button>
                <button type="button" @click="cancelNewQuestion" class="btn btn-secondary">
                  <i class="fas fa-times"></i>
                  <span>{{ $t('takeExam.cancel') }}</span>
                </button>
              </div>
            </form>
          </div>
        </div>

              <!-- Main Question Card -->
        <div v-else-if="currentQuestion" class="question-card">
        <!-- Card Header -->
        <div class="card-header-modern">
          <div class="question-info">
            <button class="hint-btn" @click="showHint" :title="$t('takeExam.getHint')">
              <i class="fas fa-lightbulb"></i>
              <span>{{ $t('takeExam.getHint') }}</span>
            </button>
                    <div class="question-meta" v-if="currentQuestion.difficulty || currentQuestion.group_id || currentQuestionStats">
          <span v-if="currentQuestion.difficulty" class="meta-item" :class="getDifficultyClass(currentQuestion.difficulty)">
            <i class="fas fa-signal"></i>
            {{ currentQuestion.difficulty }}
          </span>
          <span v-if="currentQuestion.group_id" class="meta-item">
            <i class="fas fa-tags"></i>
            {{ currentQuestion.group_id }}
          </span>
          <span v-if="currentQuestionStats" class="meta-item accuracy-meta">
            <i class="fas fa-percentage"></i>
            {{ $t('takeExam.accuracy') }}: {{ targetAccuracyPercentage }}%
            <div v-if="currentQuestionStats.total_attempts > 0" class="accuracy-adjustment">
              <input
                type="range"
                min="0"
                max="100"
                :value="targetAccuracyPercentage"
                @input="onAccuracySliderChange"
                @mouseup="onAccuracySliderMouseUp"
                class="accuracy-slider"
                :disabled="isAdjustingAccuracy"
                ref="accuracySlider"
              />
            </div>
          </span>
        </div>
          </div>


          <div class="card-actions">
            <button class="card-action-btn" @click="toggleDetails" :title="$t('takeExam.details')" :class="{ 'active': showDetails }">
              <i class="fas fa-info-circle"></i>
              <span class="action-label">{{ $t('takeExam.details') }}</span>
            </button>
            <button class="card-action-btn" @click="editQuestion" v-if="canEditQuestions" :title="$t('takeExam.editQuestion')">
              <i class="fas fa-edit"></i>
              <span class="action-label">{{ $t('takeExam.editQuestion') }}</span>
            </button>
            <button class="card-action-btn" @click="deleteCurrentQuestion" v-if="canEditQuestions" :title="$t('takeExam.deleteQuestion')">
              <i class="fas fa-trash"></i>
              <span class="action-label">{{ $t('takeExam.delete') }}</span>
            </button>
          </div>
        </div>

        <!-- Question Content -->
        <div class="question-content-modern">
          <!-- 문제 제목을 메인으로 표시 -->
          <div class="question-title question-link" @click="toggleDetails" style="cursor: pointer; font-weight: bold; margin-bottom: 15px;">
            {{ getLocalizedQuestionTitle }}
          </div>

          <!-- 문제 내용 표시 -->
          <!-- 인증되지 않은 사용자는 항상 내용 표시 -->
          <div v-if="!isAuthenticated && getLocalizedQuestionContent" class="question-content-text" style="margin-bottom: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 8px; border-left: 4px solid #007bff;">
            <div class="content-text" style="color: #212529; line-height: 1.6; white-space: pre-wrap;">{{ getLocalizedQuestionContent }}
            </div>
          </div>
          <!-- 인증된 사용자는 제목과 다를 때만 내용 표시 (다지선다 문제는 선택지 제외한 본문만 표시) -->
          <div v-else-if="isAuthenticated && shouldShowQuestionContent" class="question-content-text" style="margin-bottom: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 8px; border-left: 4px solid #007bff;">
            <div class="content-text" style="color: #212529; line-height: 1.6; white-space: pre-wrap;">{{ getQuestionContentWithoutChoices }}
            </div>
          </div>

          <!-- URL Display (moved from Details) -->
          <div class="question-url" v-if="currentQuestion.url && currentQuestion.url !== 'nan' && currentQuestion.url !== 'NaN'">
            <a :href="currentQuestion.url" target="_blank" class="url-link">
              <i class="fas fa-external-link-alt"></i>
              {{ currentQuestion.url }}
            </a>
          </div>

          <!-- Question Details -->
          <div class="question-details-modern" v-if="showDetails">
            <div class="details-header">
              <h5>{{ $t('takeExam.details') }}</h5>
              <button class="close-btn" @click="toggleDetails" :title="$t('takeExam.close')">
                <i class="fas fa-times"></i>
              </button>
            </div>
            <div class="detail-item">
              <span class="detail-label">{{ $t('takeExam.questionId') }}:</span>
              <span class="detail-value">{{ currentQuestion.csv_id || currentQuestion.id }}</span>
            </div>
            <div class="detail-item" v-if="getLocalizedQuestionTitle">
              <span class="detail-label">{{ $t('takeExam.title') }}:</span>
              <span class="detail-value">
                <a
                  v-if="currentQuestion.url && currentQuestion.url !== 'nan' && currentQuestion.url !== 'NaN'"
                  :href="currentQuestion.url"
                  target="_blank"
                  class="title-link"
                  @click.stop
                >
                  {{ getLocalizedQuestionTitle }}
                  <i class="fas fa-external-link-alt ms-1"></i>
                </a>
                <span v-else>{{ getLocalizedQuestionTitle }}</span>
              </span>
            </div>


            <div class="detail-item" v-if="currentQuestion.difficulty">
              <span class="detail-label">{{ $t('takeExam.difficulty') }}:</span>
              <span class="detail-value">{{ currentQuestion.difficulty }}</span>
            </div>
            <div class="detail-item" v-if="currentQuestion.group_id">
              <span class="detail-label">{{ $t('takeExam.groupId') }}:</span>
              <span class="detail-value">{{ currentQuestion.group_id }}</span>
            </div>
            <!-- 문제 통계 정보 -->
            <div class="detail-item" v-if="currentQuestionStats">
              <span class="detail-label">{{ $t('takeExam.statistics') }}:</span>
              <span class="detail-value">
                <span class="stat-item">
                  <i class="fas fa-check-circle text-success"></i>
                  {{ $t('takeExam.correct') }}: {{ currentQuestionStats.correct_attempts }}
                </span>
                <span class="stat-item">
                  <i class="fas fa-play-circle text-info"></i>
                  {{ $t('takeExam.attempts') }}: {{ currentQuestionStats.total_attempts }}
                </span>
                <span class="stat-item" v-if="currentQuestionStats.total_attempts > 0">
                  <i class="fas fa-percentage text-warning"></i>
                  {{ $t('takeExam.accuracy') }}: {{ ((currentQuestionStats.correct_attempts / currentQuestionStats.total_attempts) * 100).toFixed(1) }}%
                </span>
              </span>
            </div>
          </div>
          <!-- Answer Section -->
          <div class="answer-section-modern">
            <!-- 선택지가 있는 경우 라디오 버튼 또는 체크박스 표시 -->
            <div v-if="isAuthenticated && hasMultipleChoiceOptions" class="multiple-choice-section">
              <label class="answer-label">{{ $t('takeExam.selectAnswer') }}:</label>

              <!-- 단일 선택 (라디오 버튼) -->
              <div v-if="!isMultipleChoice" class="radio-options">
                <div
                  v-for="option in multipleChoiceOptions"
                  :key="option.key"
                  class="radio-option"
                >
                  <input
                    type="radio"
                    :id="`option-${option.key}`"
                    :value="option.key"
                    v-model="currentAnswer"
                    class="radio-input"
                  >
                  <label :for="`option-${option.key}`" class="radio-label">
                    <span class="option-key">{{ option.key }}{{ isCircledNumber(option.key) ? '' : '.' }}</span>
                    <span class="option-text">{{ option.text }}</span>
                  </label>
                </div>
              </div>

              <!-- 복수 선택 (체크박스) -->
              <div v-else class="checkbox-options">
                <div
                  v-for="option in multipleChoiceOptions"
                  :key="option.key"
                  class="checkbox-option"
                >
                  <input
                    type="checkbox"
                    :id="`option-${option.key}`"
                    :value="option.key"
                    v-model="selectedOptions"
                    class="checkbox-input"
                  >
                  <label :for="`option-${option.key}`" class="checkbox-label">
                    <span class="option-key">{{ option.key }}{{ isCircledNumber(option.key) ? '' : '.' }}</span>
                    <span class="option-text">{{ option.text }}</span>
                  </label>
                </div>
              </div>
            </div>

            <!-- 일반 텍스트 답변인 경우에만 텍스트 입력창 표시 (인증된 사용자만) -->
            <div v-else-if="isAuthenticated && !isYNAnswer" class="text-answer-section">
              <label class="answer-label">{{ $t('takeExam.enterAnswer') }}:</label>
              <textarea
                class="answer-input"
                v-model="currentAnswer"
                :key="currentQuestion.id"
                @keydown.ctrl.enter="nextQuestion"
                :placeholder="$t('takeExam.enterAnswer')"
                ref="answerInput"
                :rows="isMobile ? 3 : 4"
              ></textarea>
            </div>
          </div>

          <!-- Solved Status Buttons or Submit Button (인증된 사용자만 표시) -->
          <div v-if="isAuthenticated && !exam.force_answer" class="solved-buttons">
            <button @click="handleSolvedStatusClick('Y')" class="solved-btn" :class="{ 'active': solvedStatus === 'Y' }">
              <i class="fas fa-check"></i>
              <span>{{ $t('takeExam.solved') }}</span>
            </button>
            <button @click="handleSolvedStatusClick('N')" class="solved-btn" :class="{ 'active': solvedStatus === 'N' }">
              <i class="fas fa-times"></i>
              <span>{{ $t('takeExam.unsolved') }}</span>
            </button>
          </div>
          <!-- Submit Button for Force Answer Mode (인증된 사용자만 표시) -->
          <div v-else-if="isAuthenticated && exam.force_answer" class="submit-button-container">
            <button @click="submitAnswer" class="submit-btn" :disabled="!currentAnswer.trim()">
              <i class="fas fa-check"></i>
              {{ $t('takeExam.submit') }}
            </button>
          </div>
          <!-- 인증되지 않은 사용자에게는 읽기 전용 메시지 표시 (문제 내용 아래에 표시) -->
          <div v-if="!isAuthenticated" class="read-only-message" style="margin-top: 20px;">
            <div class="alert alert-info">
              <i class="fas fa-info-circle"></i>
              {{ $t('takeExam.readOnlyMessage') || '문제를 풀려면 로그인이 필요합니다.' }}
              <router-link to="/login" class="login-link">{{ $t('takeExam.login') || '로그인' }}</router-link>
            </div>
          </div>
        </div>

        <!-- Answer Display -->
        <div v-if="showAnswer" class="answer-display">
          <div class="answer-content">
            <strong>{{ $t('takeExam.answer') }}:</strong>
            <div class="answer-text">{{ getLocalizedQuestionAnswer }}</div>
          </div>
        </div>

        <!-- Explanation Display -->
        <div v-if="showExplanation && getLocalizedQuestionExplanation" class="explanation-display">
          <div class="explanation-content">
            <strong>{{ $t('takeExam.explanation') }}:</strong>
            <div class="explanation-text">{{ getLocalizedQuestionExplanation }}</div>
          </div>
        </div>

        <!-- Question Edit Form -->
        <div v-if="isEditingQuestion" class="question-edit-form">
          <div class="edit-form-header">
            <h4>{{ $t('takeExam.editQuestion') }}</h4>
          </div>
          <div class="edit-form-content">
            <div class="form-row">
              <div class="form-group">
                <label>{{ $t('takeExam.questionId') }}:</label>
                <input v-model="editingQuestion.csv_id" type="text" class="form-control">
              </div>
              <div class="form-group">
                <label>{{ $t('takeExam.title') }}:</label>
                <input v-model="editingQuestion.title" type="text" class="form-control">
              </div>
            </div>
            <div class="form-group">
              <label>{{ $t('takeExam.content') }}:</label>
              <textarea v-model="editingQuestion.content" class="form-control" rows="4"></textarea>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>{{ $t('takeExam.difficulty') }}:</label>
                <select v-model="editingQuestion.difficulty" class="form-control">
                  <option value="">{{ $t('takeExam.selectOption') }}</option>
                  <option value="Easy">{{ $t('takeExam.easy') }}</option>
                  <option value="Medium">{{ $t('takeExam.medium') }}</option>
                  <option value="Hard">{{ $t('takeExam.hard') }}</option>
                </select>
              </div>
              <div class="form-group">
                <label>{{ $t('takeExam.groupId') }}:</label>
                <input v-model="editingQuestion.group_id" type="text" class="form-control">
              </div>
            </div>
            <div class="form-group">
              <label>URL:</label>
              <input v-model="editingQuestion.url" type="url" class="form-control">
            </div>
                          <div class="form-group">
                <label>{{ $t('takeExam.answer') }}:</label>
                <textarea v-model="editingQuestion.answer" class="form-control" rows="3"></textarea>
              </div>
              <div class="form-group">
                <label>{{ $t('takeExam.explanation') }}:</label>
                <textarea v-model="editingQuestion.explanation" class="form-control" rows="18"></textarea>
              </div>
            <div class="edit-form-actions">
              <button @click="saveQuestionEdit" class="btn-save">
                <i class="fas fa-save"></i>
                <span>{{ $t('takeExam.save') }}</span>
              </button>
              <button @click="cancelQuestionEdit" class="btn-cancel">
                <i class="fas fa-times"></i>
                <span>{{ $t('takeExam.cancel') }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Bottom Navigation (새 문제 추가 모드가 아닐 때만 표시) -->
      <div v-if="!isAddingNewQuestion" class="bottom-navigation">
        <div class="nav-left">
          <div class="progress-toggle">
            <span>{{ $t('takeExam.trackProgress') }}</span>
            <label class="toggle-switch">
              <input type="checkbox" v-model="trackProgress" @change="onTrackProgressChange">
              <span class="toggle-slider"></span>
            </label>
          </div>

          <!-- 문제 소요 시간 표시 -->
          <div class="time-display">
            <div class="current-question-time">
              <i class="fas fa-clock"></i>
              <span>{{ formatQuestionTime(currentQuestionTimeReactive) }}</span>
            </div>
            <div class="total-time">
              <i class="fas fa-stopwatch"></i>
              <span>{{ formatElapsed(elapsedSeconds) }}</span>
            </div>
          </div>
        </div>

        <div class="nav-center">
          <button class="modern-nav-btn" @click="goToFirstQuestion" :disabled="currentQuestionIndex === 0" title="맨 처음">
            <i class="fas fa-step-backward"></i>
            <span class="btn-text">⏮</span>
          </button>
          <button class="modern-nav-btn" @click="previousQuestion" :disabled="currentQuestionIndex === 0">
            <i class="fas fa-chevron-left"></i>
            <span class="btn-text">◀</span>
          </button>
          <div class="progress-display">
            {{ currentQuestionIndex + 1 }} / {{ exam?.questions?.length || 0 }}
          </div>
          <button class="modern-nav-btn" @click="nextQuestion" :disabled="currentQuestionIndex >= (exam?.questions?.length || 0) - 1">
            <i class="fas fa-chevron-right"></i>
            <span class="btn-text">▶</span>
          </button>
          <button class="modern-nav-btn" @click="goToLastQuestion" :disabled="currentQuestionIndex >= (exam?.questions?.length || 0) - 1" title="맨 뒤">
            <i class="fas fa-step-forward"></i>
            <span class="btn-text">⏭</span>
          </button>
        </div>

        <div class="nav-right">
          <button 
            class="modern-btn" 
            @click="shuffleQuestions" 
            :title="$t('takeExam.shuffleByAccuracyDesc')"
            data-bs-toggle="tooltip" 
            data-bs-placement="top"
          >
            <i class="fas fa-random"></i>
            <span class="btn-text">⟲</span>
          </button>
          <button class="modern-btn" @click="toggleFullscreen" :title="$t('takeExam.fullscreen')">
            <i class="fas fa-expand"></i>
            <span class="btn-text">⛶</span>
          </button>
        </div>
      </div>

              <!-- Action Buttons (새 문제 추가 모드가 아닐 때만 표시) -->
      <div v-if="!isAddingNewQuestion" class="action-buttons">
        <!-- 왼쪽 영역: 음성 인터페이스 -->
        <div class="action-left">
          <VoiceExamInterface 
            v-if="voiceMode && examId"
            :is-visible="voiceMode"
            :exam-id="examId"
            :current-question="currentQuestion"
            :exam-title="localizedExamTitle"
            :exam-difficulty="exam ? (exam.exam_difficulty || 5) : 5"
            :current-question-index="currentQuestionIndex"
            :total-questions="exam ? exam.questions.length : 0"
            @toggle-voice-mode="toggleVoiceMode"
            @handle-pass="handleVoicePass"
            @handle-fail="handleVoiceFail"
            @show-incorrect-reason="handleVoiceIncorrectReason"
            @hide-incorrect-reason="handleHideVoiceIncorrectReason"
            @realtime-text="handleRealtimeText"
          />
        </div>
        
        <!-- 오른쪽 영역: 기존 버튼들 -->
        <div class="action-right">
          <!-- AI Mock Interview 버튼 (데스크톱에서만 표시, 모바일은 page-title로 이동) -->
          <button 
            v-if="exam && exam.ai_mock_interview && !isMobileDevice"
            @click="showAIMockInterviewDetail"
            class="action-btn action-btn-info action-btn-large ai-mock-interview-btn"
          >
            <i class="fas fa-robot"></i>
            <span class="action-label">{{ $t('examDetail.aiMockInterview') || 'AI Mock Interview' }}</span>
          </button>
          <button @click="goToList" class="action-btn-info">
            <i class="fas fa-list"></i>
            <span>{{ $t('takeExam.list') }}</span>
          </button>
          <button @click="saveExam" class="action-btn-success" v-if="isAuthenticated">
            <i class="fas fa-save"></i>
            <span>{{ $t('takeExam.saveExam') }}</span>
          </button>
          <button @click="exitExam" class="action-btn-danger" v-if="isAuthenticated">
            <i class="fas fa-stop"></i>
            <span>{{ $t('takeExam.endExam') }}</span>
          </button>
          <!-- 음성 모드 토글 버튼 -->
          <button 
            @click="handleVoiceModeClick" 
            class="action-btn-voice"
            :class="{ 'active': voiceMode }"
            v-if="isAuthenticated && exam && exam.voice_mode_enabled"
          >
            <i class="fas fa-microphone-alt"></i>
            <span>{{ voiceMode ? $t('takeExam.disableVoice') : $t('takeExam.enableVoice') }}</span>
          </button>
        </div>
      </div>
      
      <!-- Voice Mode 실시간 텍스트 및 오답 메시지 (action-buttons 밑에 표시) -->
      <div v-if="voiceMode" class="voice-incorrect-reason">
        <!-- 실시간 음성 인식 텍스트 표시 -->
        <div v-if="realtimeVoiceText" class="alert alert-info mb-0">
          <i class="fas fa-microphone me-2"></i>
          <strong>{{ $t('takeExam.enableVoice') }}:</strong>
          <div class="mt-2">
            <div class="realtime-text-container">
              <!-- 전체 텍스트만 표시 -->
              <div class="combined-text" v-if="realtimeVoiceText.combinedText">
                <strong>🎤 {{ $t('takeExam.answer') }}:</strong> 
                <span class="text-info">{{ realtimeVoiceText.combinedText }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 오답 메시지 (기존) -->
        <div v-if="showVoiceIncorrectReason && voiceIncorrectData" class="alert alert-warning mb-0">
          <i class="fas fa-exclamation-triangle me-2"></i>
          <span>{{ voiceIncorrectData.message }}</span>
          <div class="mt-2">
            <div class="mb-1">
              <strong>{{ $t('voiceExam.answerLabel') }}:</strong> {{ voiceIncorrectData.answer }}
            </div>
            <div>
              <strong>{{ $t('voiceExam.evaluationLabel') }}:</strong> 
              <div class="mt-1" v-html="voiceIncorrectData.evaluation.replace(/\n/g, '<br>')"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- AI Mock Interview Modal -->
    <div v-if="showAIMockInterviewModal" class="modal-overlay" @click="hideAIMockInterviewModal">
      <!-- Voice Interview 모드 (모바일 및 웹 환경 모두 지원) -->
      <div v-if="showVoiceInterview" class="mobile-voice-interview-container" @click.stop>
        <MobileVoiceInterview
          :exam-id="selectedQuestionForAI?.id || examId"
          :exam-title="selectedQuestionForAI?.localized_title || selectedQuestionForAI?.title || localizedExamTitle"
          :language="currentLanguage"
          :voice="'alloy'"
          :instructions="interviewPromptText"
          :questions="exam ? exam.questions : []"
          @interview-ended="handleInterviewEnded"
          @session-created="handleSessionCreated"
        />
      </div>
    </div>

  </div>
</template>

<script>
import axios from 'axios'
import { isAdmin, hasStudyAdminRole, canEditExam, getCurrentUser as getCurrentUserFromPermissions } from '@/utils/permissionUtils'
import { isCacheEnabled, setSessionCache, getSessionCache, removeSessionCache, removeLocalCache } from '@/utils/cacheUtils'
import { debugLog, forceDebugLog } from '@/utils/debugUtils'
import VoiceExamInterface from '@/components/VoiceExamInterface.vue'
import { loadMandatoryRules, loadInterviewPromptTemplate, buildInterviewPrompt } from '@/utils/voiceInterviewUtils'
import { getLocalizedContentWithI18n } from '@/utils/multilingualUtils'
import authService from '@/services/authService'


/**
 * 시험 응시 컴포넌트
 *
 * 캐시 정리 정책:
 * 1. 시험 제출(End 버튼) 시: clearExamRelatedCache() 호출로 시험 관련 모든 캐시 정리
 * 2. 세션 정리: clearSession() 호출로 시험 진행 상태 캐시 정리
 * 3. 강제 새로고침: forceRefreshExamManagement, forceRefreshHome 플래그 설정
 * 4. 브라우저 캐시: localStorage, sessionStorage에서 시험 관련 데이터 완전 제거
 */
export default {
  name: 'TakeExam',
  components: {
    VoiceExamInterface,
    'ShareModal': () => import('@/components/ShareModal.vue'),
    'MobileVoiceInterview': () => import('@/components/MobileVoiceInterview.vue')
  },
  data() {
    return {
      exam: null,
      loading: true,
      loadingTimer: null, // 로딩 타이머 추가
      showTranslationMessage: false, // 번역 메시지 표시 여부
      currentQuestionIndex: 0,
      answers: {},
      examCompleted: false,
      elapsedSeconds: 0,
      timer: null,
      showAnswer: false, // 정답 표시 여부
      showExplanation: false, // 설명 표시 여부
      isContinueMode: false, // 이어풀기 모드
      previousResultId: null, // 이전 결과 ID
      answeredQuestions: new Set(), // 이미 푼 문제들
      questionTimes: [], // 각 문제별 소요 시간(초)
      questionStartTime: null, // 현재 문제 시작 시간
      questionTimer: null, // 현재 문제 타이머
      sessionKey: null, // sessionStorage 키
      originalFilterParams: '', // 원래 exam-detail 페이지의 필터 파라미터
      isEditingQuestion: false, // 문제 수정 모드
      showVoiceIncorrectReason: false, // Voice Mode 오답 메시지 표시 여부
      voiceIncorrectData: null, // Voice Mode 오답 데이터 (message, answer, evaluation)
      realtimeVoiceText: null, // 실시간 음성 인식 텍스트
      editingQuestion: {
        csv_id: '',
        title: '',
        content: '',
        answer: '',
        explanation: '',
        difficulty: '',
        url: '',
        group_id: ''
      },
      isAddingNewQuestion: false, // 새 문제 추가 모드
      newQuestion: {
        csv_id: '',
        title: '',
        content: '',
        answer: '',
        explanation: '',
        difficulty: 'Medium',
        url: '',
        group_id: ''
      },
      ignoredQuestions: new Set(), // 무시된 문제 목록
      solvedStatus: null, // 풀었음/못풀었음 상태 (Y/N 문제가 아닌 경우)
      showQuestionDetails: false, // 문제 상세 표시 여부
      showDetails: false, // 상세 정보 표시 여부
      isFavorited: false, // 즐겨찾기 상태
      isPlaying: false, // 오디오 재생 상태
      trackProgress: true, // 진행 상태 추적 여부 (기본 활성화)
      isFullscreen: false, // 전체 화면 모드
      currentQuestionTimeReactive: 0, // 현재 문제 시간 (반응형)
      showToast: false, // 토스트 표시 여부
      toastMessage: '', // 토스트 메시지
      toastType: 'success', // 토스트 타입 (success, error, warning, info)
      toastMessageQueue: [], // 토스트 메시지 큐
      isShowingToast: false, // 현재 토스트 메시지를 표시 중인지 여부
      // 음성 모드 관련
      voiceMode: false, // 음성 모드 활성화 여부
      voiceEnabled: false, // 음성 기능 사용 가능 여부
      toastIcon: 'fas fa-check-circle', // 토스트 아이콘
      showDeleteConfirm: false, // 삭제 확인 다이얼로그 표시 여부
      questionToDelete: null, // 삭제할 문제 정보
      // 공유 모달 관련
      showShareModal: false,
      shareUrl: '',
      questionStatistics: [], // 문제별 통계 정보
      // AI Mock Interview 관련
      showVoiceInterview: false,
      showAIMockInterviewModal: false,
      interviewPromptText: '',
      selectedQuestionForAI: null,
      isMobileDevice: false,
      isInitializingPrompt: false,
      showAccuracyAdjustment: false, // 정확도 조정 패널 표시 여부

      targetAccuracyPercentage: 0, // 목표 정확도 퍼센트
      isAdjustingAccuracy: false, // 정확도 조정 중 여부
      savedQuestionIds: new Set(), // 저장된 문제 ID 목록
      // 연결된 프로젝트 관련
      connectedStudies: [],
      showProjectSelector: false,
      
      // 사용자 프로필 언어 (캐시)
      userProfileLanguage: null,
    }
  },
  computed: {
    isMobile() {
      return window.innerWidth <= 768
    },
    currentQuestion() {
      console.log('🔍 [currentQuestion computed] 호출됨:', {
        exam: this.exam,
        examExists: !!this.exam,
        questions: this.exam?.questions,
        questionsExists: !!this.exam?.questions,
        questionsIsArray: Array.isArray(this.exam?.questions),
        questionsLength: this.exam?.questions?.length,
        currentQuestionIndex: this.currentQuestionIndex
      })
      
      if (!this.exam || !this.exam.questions) {
        console.log('🔍 currentQuestion: exam 또는 questions가 없음', { exam: this.exam, questions: this.exam?.questions })
        return null
      }
      
      // questions 배열이 비어있는 경우 체크
      if (this.exam.questions.length === 0) {
        console.log('🔍 currentQuestion: questions 배열이 비어있음', {
          currentQuestionIndex: this.currentQuestionIndex,
          totalQuestions: this.exam.questions.length
        })
        return null
      }
      
      // currentQuestionIndex가 유효한 범위인지 체크
      if (this.currentQuestionIndex < 0 || this.currentQuestionIndex >= this.exam.questions.length) {
        console.log('🔍 currentQuestion: currentQuestionIndex가 유효하지 않음', {
          currentQuestionIndex: this.currentQuestionIndex,
          totalQuestions: this.exam.questions.length
        })
        return null
      }

      const question = this.exam.questions[this.currentQuestionIndex]
      console.log('🔍 currentQuestion:', {
        currentQuestionIndex: this.currentQuestionIndex,
        totalQuestions: this.exam.questions.length,
        question: question,
        questionKeys: question ? Object.keys(question) : null
      })
      return question
    },
    isYNAnswer() {
      if (!this.currentQuestion) return false

      // 현재 언어에 맞는 정답 필드 사용 (폴백 포함)
      const answer = getLocalizedContentWithI18n(this.currentQuestion, 'answer', this.$i18n, this.userProfileLanguage, '')

      if (!answer) return false;

      const normalizedAnswer = answer.toString().toLowerCase().trim();
      // Y/N, Yes/No, 예/아니오 등의 형태인지 확인
      return /^(y|n|yes|no|예|아니오)$/i.test(normalizedAnswer) ||
             /^(y|n)$/i.test(normalizedAnswer) ||
             normalizedAnswer === 'y' || normalizedAnswer === 'n' ||
             normalizedAnswer === 'yes' || normalizedAnswer === 'no'
    },
    currentAnswer: {
      get() {
        const questionId = this.currentQuestion?.id
        return questionId ? (this.answers[questionId] || '') : ''
      },
      set(value) {
        const questionId = this.currentQuestion?.id
        if (questionId) {
          this.$set(this.answers, questionId, value)
          this.saveSession() // 답안 입력 시 세션 저장
        }
      }
    },
    idMismatch() {
      const questionId = this.currentQuestion?.id
      if (questionId && this.getCurrentQuestionIdFromRoute) {
        return questionId !== this.getCurrentQuestionIdFromRoute()
      }
      return false
    },
    isAdmin() {
      return isAdmin()
    },
    isExamCreator() {
      if (!this.exam || !this.currentUser) {
        return false
      }

      // 시험의 생성자가 현재 사용자인지 확인
      return this.exam.created_by && this.exam.created_by.id === this.currentUser.id
    },
    isStudyAdmin() {
      return hasStudyAdminRole()
    },
    currentUser() {
      return getCurrentUserFromPermissions()
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
    canEditQuestions() {
      // 문제 편집 권한이 있는 사용자들
      // 전역 관리자가 아닌 경우, 리소스별 권한 확인 필요
      if (this.isAdmin) {
        // 전역 관리자는 모든 시험 편집 가능
        return true
      }
      
      // 시험 생성자 확인
      if (this.isExamCreator) {
        return true
      }
      
      // 스터디 관리자 권한 확인 (리소스별)
      if (this.exam && this.exam.user_permissions) {
        // 백엔드에서 제공하는 리소스별 권한 정보 사용
        return this.exam.user_permissions.is_study_admin === true
      }
      
      // 백엔드 권한 정보가 없으면 canEditExam 함수 사용
      return canEditExam(this.exam)
    },
    isYNQuestion() {
      if (!this.currentQuestion) return false

      // 현재 언어에 맞는 정답 필드 사용 (폴백 포함)
      let answer = getLocalizedContentWithI18n(this.currentQuestion, 'answer', this.$i18n, this.userProfileLanguage, '')

      answer = answer?.trim().toUpperCase();
      return answer === 'Y' || answer === 'N'
    },

    shouldShowQuestionContent() {
      if (!this.currentQuestion) {
        console.log('🔍 shouldShowQuestionContent: currentQuestion 없음')
        return false
      }

      // 인증되지 않은 사용자는 항상 내용 표시
      if (!this.isAuthenticated) {
        const content = this.getLocalizedQuestionContent
        return !!content // 내용이 있으면 표시
      }

      const title = this.getLocalizedQuestionTitle
      // 다지선다 문제는 선택지를 제외한 본문과 비교, 그 외는 전체 내용과 비교
      const content = this.hasMultipleChoiceOptions 
        ? this.getQuestionContentWithoutChoices 
        : this.getLocalizedQuestionContent

      console.log('🔍 shouldShowQuestionContent:', {
        title,
        content,
        hasMultipleChoiceOptions: this.hasMultipleChoiceOptions,
        contentLength: content?.length
      })

      // 제목이나 내용이 없으면 표시하지 않음
      if (!title || !content) {
        console.log('🔍 shouldShowQuestionContent: 제목 또는 내용 없음')
        return false
      }

      // 제목과 내용이 같으면 표시하지 않음 (공백과 줄바꿈 제거 후 비교)
      const normalizedTitle = title.trim().replace(/\s+/g, ' ')
      const normalizedContent = content.trim().replace(/\s+/g, ' ')

      return normalizedTitle !== normalizedContent
    },
    canProceedToNext() {
      if (this.isYNQuestion) {
        // Y/N 문제인 경우 Y 또는 N이 선택되어야 함
        return this.currentAnswer === 'Y' || this.currentAnswer === 'N'
      } else {
        // 일반 문제인 경우 답안이 입력되어야 하거나 풀었음/못풀었음이 선택되어야 함
        return this.currentAnswer.trim() !== '' || this.solvedStatus === 'Y' || this.solvedStatus === 'N'
      }
    },
    hasAnsweredCurrentQuestion() {
      if (!this.currentQuestion) return false

      if (this.isYNQuestion) {
        // Y/N 문제인 경우 Y 또는 N이 선택되어야 함
        return this.currentAnswer === 'Y' || this.currentAnswer === 'N'
      } else {
        // 일반 문제인 경우 답안이 입력되어야 하거나 풀었음/못풀었음이 선택되어야 함
        return this.currentAnswer.trim() !== '' || this.solvedStatus === 'Y' || this.solvedStatus === 'N'
      }
    },
    isAuthenticated() {
      const user = getCurrentUserFromPermissions()
      return Boolean(user && user.id)
    },
         // 현재 언어에 맞는 시험 제목 반환
     localizedExamTitle() {
       if (!this.exam) return ''

       // display_title 사용 (백엔드에서 올바르게 처리된 경우)
       if (this.exam.display_title && this.exam.display_title.trim()) {
         forceDebugLog(`✅ [TakeExam] localizedExamTitle - display_title 사용: "${this.exam.display_title}"`)
         return this.exam.display_title
       }
       
       // display_title도 없으면 폴백 로직 사용 (동적 처리)
       return getLocalizedContentWithI18n(this.exam, 'title', this.$i18n, this.userProfileLanguage, '')
     },
         // 현재 언어에 맞는 문제 제목 반환
     localizedQuestionTitle() {
       if (!this.currentQuestion) return ''

      // 동적으로 제목 가져오기
      return getLocalizedContentWithI18n(this.currentQuestion, 'title', this.$i18n, this.userProfileLanguage, '')
     },
    isQuestionIgnored() {
      if (!this.currentQuestion) return false
      // ID 타입을 문자열로 통일하여 비교
      const questionIdStr = String(this.currentQuestion.id)
      const isIgnored = this.ignoredQuestions.has(questionIdStr)



      return isIgnored
    },

    currentQuestionTime() {
      if (this.questionStartTime === null) return 0
      const elapsed = Math.floor((Date.now() - this.questionStartTime) / 1000)
      return elapsed
    },
    currentQuestionStats() {
      if (!this.currentQuestion || !this.questionStatistics) return null
      const stats = this.questionStatistics.find(s => String(s.question_id) === String(this.currentQuestion.id))
      return stats || null
    },
    currentAccuracyPercentage() {
      if (!this.currentQuestionStats || this.currentQuestionStats.total_attempts === 0) return 0
      return Math.round((this.currentQuestionStats.correct_attempts / this.currentQuestionStats.total_attempts) * 100)
    },

    // 현재 사용자 언어
    currentLanguage() {
      const lang = this.$i18n.locale || 'en'
      console.log('🔍 currentLanguage:', lang, 'i18n.locale:', this.$i18n.locale)
      return lang
    },
    examId() {
      // URL에서 examId 추출
      const examId = this.$route.params.examId || this.$route.query.exam_id || null
      debugLog('🎤 examId computed:', examId)
      debugLog('🎤 route.params:', this.$route.params)
      debugLog('🎤 route.query:', this.$route.query)
      return examId
    },

    // 현재 문제의 다국어 제목 (반응형)
    getLocalizedQuestionTitle() {
      if (!this.currentQuestion) return ''
      return getLocalizedContentWithI18n(this.currentQuestion, 'title', this.$i18n, this.userProfileLanguage, '')
    },

    // 현재 문제의 다국어 내용 (반응형)
    getLocalizedQuestionContent() {
      if (!this.currentQuestion) return ''
      return getLocalizedContentWithI18n(this.currentQuestion, 'content', this.$i18n, this.userProfileLanguage, '')
    },

    // 현재 문제의 다국어 정답 (반응형)
    getLocalizedQuestionAnswer() {
      if (!this.currentQuestion) return ''
      return getLocalizedContentWithI18n(this.currentQuestion, 'answer', this.$i18n, this.userProfileLanguage, '')
    },

    // 현재 문제의 다국어 설명 (반응형)
    getLocalizedQuestionExplanation() {
      if (!this.currentQuestion) return ''
      return getLocalizedContentWithI18n(this.currentQuestion, 'explanation', this.$i18n, this.userProfileLanguage, '')
    },

    // 선택지가 있는지 확인 (a, b, c, d 또는 A, B, C, D 또는 1, 2, 3, 4 또는 ①, ②, ③, ④ 형태)
    hasMultipleChoiceOptions() {
      if (!this.getLocalizedQuestionContent) return false

      const content = this.getLocalizedQuestionContent
      const optionPatterns = [
        /^[a-d]\.\s+/m,  // a. b. c. d.
        /^[A-D]\.\s+/m,  // A. B. C. D.
        /^[1-4]\.\s+/m,  // 1. 2. 3. 4.
        /^[a-d]\)\s+/m,  // a) b) c) d)
        /^[A-D]\)\s+/m,  // A) B) C) D)
        /^[1-4]\)\s+/m,  // 1) 2) 3) 4)
        /^[①-④]\s+/m,   // ① ② ③ ④ (한글 원문자)
        /^[①-⑤]\s+/m    // ① ② ③ ④ ⑤ (한글 원문자, 5개까지)
      ]

      return optionPatterns.some(pattern => pattern.test(content))
    },

    // 선택지들을 파싱하여 배열로 반환
    multipleChoiceOptions() {
      if (!this.hasMultipleChoiceOptions) return []

      const content = this.getLocalizedQuestionContent
      const lines = content.split('\n')
      const options = []

      lines.forEach(line => {
        const trimmedLine = line.trim()
        // a. b. c. d. 또는 A. B. C. D. 또는 1. 2. 3. 4. 또는 ① ② ③ ④ 패턴 매칭
        // 한글 원문자(①-⑤)는 공백 없이 바로 텍스트가 올 수 있음
        let match = trimmedLine.match(/^([a-dA-D1-4])[.)]\s*(.+)$/)
        if (match) {
          options.push({
            key: match[1],
            text: match[2].trim()
          })
        } else {
          // 한글 원문자 패턴 (①, ②, ③, ④, ⑤)
          match = trimmedLine.match(/^([①-⑤])\s*(.+)$/)
          if (match) {
            options.push({
              key: match[1],
              text: match[2].trim()
            })
          }
        }
      })

      return options
    },

    // 선택지를 제외한 문제 본문만 반환 (다지선다 문제에서 사용)
    getQuestionContentWithoutChoices() {
      const content = this.getLocalizedQuestionContent
      if (!content) return ''

      // 선택지가 없는 경우 전체 내용 반환
      if (!this.hasMultipleChoiceOptions) {
        return content
      }

      // 선택지가 있는 경우 선택지 부분 제거
      const lines = content.split('\n')
      const contentLines = []

      for (const line of lines) {
        const trimmedLine = line.trim()
        // 선택지 패턴 매칭 (a. b. c. d. 또는 A. B. C. D. 또는 1. 2. 3. 4. 또는 ① ② ③ ④)
        const isOption = /^([a-dA-D1-4])[.)]\s+/.test(trimmedLine) || /^([①-⑤])\s+/.test(trimmedLine)
        
        if (!isOption) {
          contentLines.push(line)
        } else {
          // 선택지가 시작되면 중단 (선택지 이후의 내용은 제외)
          break
        }
      }

      return contentLines.join('\n').trim()
    },

    // 단일 선택인지 복수 선택인지 확인 (정답에 쉼표가 있으면 복수 선택)
    isMultipleChoice() {
      if (!this.hasMultipleChoiceOptions) return false

      const answer = this.getLocalizedQuestionAnswer
      return answer.includes(',') || answer.includes('，') || answer.includes(';') || answer.includes('；')
    },

    // 선택된 답안들 (복수 선택의 경우 배열)
    selectedOptions: {
      get() {
        if (this.isMultipleChoice) {
          return this.currentAnswer.split(/[,，;；]/).map(s => s.trim()).filter(s => s)
        } else {
          return this.currentAnswer ? [this.currentAnswer] : []
        }
      },
      set(value) {
        if (this.isMultipleChoice) {
          this.currentAnswer = value.join(', ')
        } else {
          this.currentAnswer = value[0] || ''
        }
      }
    },
  },

  watch: {
    // 현재 문제가 변경될 때마다 targetAccuracyPercentage 업데이트
    currentQuestionStats: {
      handler(newStats) {
        if (newStats) {
          this.targetAccuracyPercentage = this.currentAccuracyPercentage
        }
      },
      immediate: true
    },

    // 현재 문제가 변경될 때 편집 모드라면 편집 폼 업데이트
    currentQuestion: {
      handler(newQuestion) {
        if (newQuestion && this.isEditingQuestion) {
          // 편집 모드가 활성화된 상태에서 문제가 변경되면 편집 폼 업데이트
          this.updateEditingForm()
        }
      }
    },

    // 언어 변경 감지 시 편집 모드에서만 페이지 새로고침
    '$i18n.locale': {
      handler(newLocale, oldLocale) {
        if (oldLocale && newLocale !== oldLocale) {
          // 편집 모드나 새 문제 추가 모드일 때만 새로고침
          if (this.isEditingQuestion || this.isAddingNewQuestion) {
            // 편집 모드인 경우 편집 모드 종료
            if (this.isEditingQuestion) {
              this.cancelQuestionEdit()
            }
            if (this.isAddingNewQuestion) {
              this.isAddingNewQuestion = false
            }
            // 페이지 새로고침
            window.location.reload()
          }
        }
      }
    }
  },

  async mounted() {
    // 모바일 환경 감지
    this.isMobileDevice = this.checkIsMobileDevice()
    
    const urlParams = new URLSearchParams(window.location.search)
    const questionId = urlParams.get('question_id')
    const mode = urlParams.get('mode')

    console.log('🔍 [mounted] 시작:', {
      questionId,
      mode,
      isAuthenticated: this.isAuthenticated,
      loading: this.loading
    })

    // 로딩 타이머 시작 (3초 후 번역 메시지 표시)
    this.startLoadingTimer()
    
    // 사용자 프로필 언어를 미리 로드하여 캐시에 저장 (loadExam에서 사용하기 전에)
    // 이렇게 하면 loadExam에서 getUserProfileLanguage()를 호출할 때 즉시 반환됨
    this.getUserProfileLanguage().catch(error => {
      console.warn('사용자 프로필 언어 로드 실패 (기본값 사용):', error)
    })

    if (mode === 'add-question') {
      this.isAddingNewQuestion = true
      await this.loadExam()
      this.initializeNewQuestion()
    } else if (questionId) {
      console.log('🔍 [mounted] loadSingleQuestion 호출:', questionId)
      await this.loadSingleQuestion(questionId)
      console.log('🔍 [mounted] loadSingleQuestion 완료:', {
        loading: this.loading,
        exam: this.exam,
        currentQuestion: this.currentQuestion
      })
    } else {
      await this.loadExam()
    }

    // 타이머 시작 (새 문제 추가 모드가 아닐 때만)
    if (this.trackProgress && !this.isAddingNewQuestion) {
      this.startTimer();

      // restart 파라미터가 있으면 시간 정보는 유지하되 타이머 재시작
      const urlParams = new URLSearchParams(window.location.search);
      const restart = urlParams.get('restart');

      if (restart === 'true') {
        // restart 모드에서는 시간 정보를 유지하면서 타이머 재시작
        if (this.questionStartTime) {
          this.startQuestionTimer();
        } else {
          // questionStartTime이 없으면 현재 시간 기준으로 설정
          const currentTime = Date.now();
          const elapsedSeconds = this.elapsedSeconds || 0;
          this.$set(this, 'questionStartTime', currentTime - (elapsedSeconds * 1000));
          this.startQuestionTimer();
        }
      } else if (!sessionStorage.getItem(this.sessionKey)) {
        // 세션이 없으면 새로운 문제 타이머 시작
        this.$set(this, 'questionStartTime', Date.now());
        this.startQuestionTimer();
      }
    }

    // 첫 번째 문제의 즐겨찾기 상태 로드 (새 문제 추가 모드가 아닐 때만)
    // ExamDetail 컴포넌트와의 중복 호출을 방지하기 위해 조건 추가
    if (!this.isAddingNewQuestion && !this.$route.path.startsWith('/exam-detail')) {
      this.loadFavoriteStatus();
    }
  },
  beforeDestroy() {
    // 새 문제 추가 모드가 아닐 때만 타이머 정리 및 세션 저장
    if (!this.isAddingNewQuestion) {
      this.stopTimer()
      this.stopLoadingTimer() // 로딩 타이머 정리
      // 현재 문제 타이머 정지
      if (this.questionTimer) {
        clearInterval(this.questionTimer);
        this.questionTimer = null;
      }
      // 페이지를 떠날 때 세션 정리 (시험 완료가 아닌 경우에만)
      if (!this.examCompleted) {
        this.saveSession()
      }
    }
  },
  methods: {
    // 사용자 프로필 언어 가져오기 (전역 캐시 사용)
    async getUserProfileLanguage() {
      // 컴포넌트 레벨 캐시에 있으면 반환
      if (this.userProfileLanguage) {
        return this.userProfileLanguage
      }
      
      try {
        if (this.isAuthenticated) {
          // 전역 캐시를 사용하는 authAPI.getProfile 사용 (중복 호출 방지)
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
    
    // 한글 원문자(①-⑤)인지 확인
    isCircledNumber(key) {
      if (!key || typeof key !== 'string') return false
      // 한글 원문자 범위: ①(0x2460) ~ ⑤(0x2464)
      return /^[①-⑤]$/.test(key)
    },

    // 난이도 정규화 함수 (백엔드와 동일한 로직)
    normalizeDifficulty(difficulty) {
      if (!difficulty) return 'Medium'
      
      const normalized = String(difficulty).toLowerCase().trim()
      
      if (['easy', '쉬움', '1', '1단계'].includes(normalized)) {
        return 'Easy'
      } else if (['medium', '보통', '2', '2단계', 'med', 'med.'].includes(normalized)) {
        return 'Medium'
      } else if (['hard', '어려움', '3', '3단계', 'high'].includes(normalized)) {
        return 'Hard'
      } else {
        return 'Medium' // 기본값
      }
    },
    
    startTimer() {
      // 새 문제 추가 모드일 때는 타이머 시작하지 않음
      if (this.isAddingNewQuestion) {
        return;
      }

      // 기존 타이머가 있으면 정리
      if (this.timer) {
        clearInterval(this.timer);
        this.timer = null;
      }

      // 세션에서 복원된 elapsedSeconds가 있으면 그대로 사용, 없으면 0으로 시작
      if (this.elapsedSeconds === 0) {
        this.elapsedSeconds = 0;
      }

      this.timer = setInterval(() => {
        this.elapsedSeconds++
        this.saveSession() // 타이머가 업데이트될 때마다 세션 저장
      }, 1000)
    },

    startLoadingTimer() {
      // 기존 로딩 타이머가 있으면 정리
      if (this.loadingTimer) {
        clearTimeout(this.loadingTimer);
        this.loadingTimer = null;
      }

      // 5초 후 번역 메시지 표시 (사용자가 요청한 조건)
      this.loadingTimer = setTimeout(() => {
        if (this.loading) {
          this.showTranslationMessage = true;
        }
      }, 5000);
    },

    stopLoadingTimer() {
      if (this.loadingTimer) {
        clearTimeout(this.loadingTimer);
        this.loadingTimer = null;
      }
      this.showTranslationMessage = false;
    },
    stopTimer() {
      if (this.timer) {
        clearInterval(this.timer)
        this.timer = null
      }
    },
    startQuestionTimer() {
      // 새 문제 추가 모드일 때는 타이머 시작하지 않음
      if (this.isAddingNewQuestion) {
        return;
      }

      // 기존 타이머가 있으면 정리
      if (this.questionTimer) {
        clearInterval(this.questionTimer);
        this.questionTimer = null;
      }

      // 세션에서 복원된 시간이 있으면 기존 시간을 유지, 없으면 새로운 시작 시간 설정
      if (this.questionStartTime && this.currentQuestionTimeReactive > 0) {
        // 현재 문제 시간이 전체 누적 시간보다 클 수 없음
        if (this.currentQuestionTimeReactive > this.elapsedSeconds) {
          this.currentQuestionTimeReactive = this.elapsedSeconds;
        }

        // questionStartTime을 현재 문제 시간에 맞게 조정
        const currentTime = Date.now();
        const adjustedStartTime = currentTime - (this.currentQuestionTimeReactive * 1000);
        this.$set(this, 'questionStartTime', adjustedStartTime);
      } else {
        // 새로운 문제 시작 시 새로운 시작 시간 설정
        this.$set(this, 'questionStartTime', Date.now());
        this.currentQuestionTimeReactive = 0;
      }

      // 현재 문제 타이머 시작
      this.questionTimer = setInterval(() => {
        if (this.questionStartTime) {
          // 현재 문제 시간을 직접 업데이트
          this.currentQuestionTimeReactive = Math.floor((Date.now() - this.questionStartTime) / 1000);

          // 현재 문제 시간이 전체 누적 시간보다 클 수 없음
          if (this.currentQuestionTimeReactive > this.elapsedSeconds) {
            this.currentQuestionTimeReactive = this.elapsedSeconds;
          }

          // sessionStorage 업데이트
          this.saveSession();
        }
      }, 1000);
    },

    getDifficultyClass(difficulty) {
      if (!difficulty) return '';
      const lowerDifficulty = difficulty.toLowerCase();
      if (lowerDifficulty === 'easy') return 'difficulty-easy';
      if (lowerDifficulty === 'medium' || lowerDifficulty === 'med') return 'difficulty-medium';
      if (lowerDifficulty === 'hard' || lowerDifficulty === 'high') return 'difficulty-hard';
      return '';
    },



    // 🚀 자동 번역 감지 메서드 (최적화된 방식)
    async checkAndTriggerTranslation() {
      console.log('🚀 [AUTO_TRANSLATE] checkAndTriggerTranslation 메서드 시작');
      try {
        // exam과 questions가 로드되지 않았으면 리턴
        if (!this.exam || !this.exam.questions || this.exam.questions.length === 0) {
          console.log('🔍 [AUTO_TRANSLATE] exam 또는 questions가 로드되지 않음');
          return;
        }

        // 현재 문제 인덱스 확인
        if (this.currentQuestionIndex < 0 || this.currentQuestionIndex >= this.exam.questions.length) {
          console.log('🔍 [AUTO_TRANSLATE] 잘못된 문제 인덱스:', this.currentQuestionIndex);
          return;
        }

        // 현재 문제 직접 가져오기
        const currentQuestion = this.exam.questions[this.currentQuestionIndex];
        if (!currentQuestion) {
          console.log('🔍 [AUTO_TRANSLATE] 현재 문제를 찾을 수 없음');
          return;
        }

        const currentLanguage = this.$i18n.locale;
        console.log(`🔍 [AUTO_TRANSLATE] 현재 언어: ${currentLanguage}, 문제 ID: ${currentQuestion.id}`);

        // 번역 필요성 체크 (더 관대한 조건) - getLocalizedContent 사용
        const currentContent = getLocalizedContentWithI18n(currentQuestion, 'content', this.$i18n, this.userProfileLanguage, '');
        const currentTitle = getLocalizedContentWithI18n(currentQuestion, 'title', this.$i18n, this.userProfileLanguage, '');
        const needsTranslation = !currentContent || currentContent.trim().length < 10 ||
                                 !currentTitle || currentTitle.trim().length < 3;

                 if (needsTranslation) {
           console.log('🔍 [AUTO_TRANSLATE] 번역 필요 - 백그라운드에서 처리 중');
           // 페이지 리로드 대신 사용자에게 정보 제공
           this.showTranslationMessage = true;
           // 8초 후 자동으로 숨김 (적절한 시간)
           setTimeout(() => {
             this.showTranslationMessage = false;
           }, 8000);
         } else {
          console.log('🔍 [AUTO_TRANSLATE] 번역 불필요 - 콘텐츠가 이미 준비됨');
          this.showTranslationMessage = false;
        }
      } catch (error) {
        console.error('❌ [AUTO_TRANSLATE] 번역 감지 중 오류:', error);
      }
    },



    showToastMessage(message, type = 'success', duration = 3000) {
      // 메시지 큐가 없으면 초기화
      if (!this.toastMessageQueue) {
        this.toastMessageQueue = [];
        this.isShowingToast = false;
      }
      
      // 메시지를 큐에 추가
      this.toastMessageQueue.push({ message, type, duration });
      
      // 현재 메시지를 표시하고 있지 않으면 다음 메시지 표시
      if (!this.isShowingToast) {
        this.processToastQueue();
      }
    },
    
    processToastQueue() {
      if (!this.toastMessageQueue || this.toastMessageQueue.length === 0) {
        this.isShowingToast = false;
        return;
      }
      
      this.isShowingToast = true;
      const { message, type, duration } = this.toastMessageQueue.shift();
      
      this.toastMessage = message;
      this.toastType = type;

      // 아이콘 설정
      switch (type) {
        case 'success':
          this.toastIcon = 'fas fa-check-circle';
          break;
        case 'error':
          this.toastIcon = 'fas fa-exclamation-circle';
          break;
        case 'warning':
          this.toastIcon = 'fas fa-exclamation-triangle';
          break;
        case 'info':
          this.toastIcon = 'fas fa-info-circle';
          break;
        default:
          this.toastIcon = 'fas fa-check-circle';
      }

      this.showToast = true;

      // 자동 숨김 후 다음 메시지 표시
      setTimeout(() => {
        this.hideToast();
        // 약간의 지연 후 다음 메시지 표시 (애니메이션을 위해)
        setTimeout(() => {
          this.processToastQueue();
        }, 300);
      }, duration);
    },

    hideToast() {
      this.showToast = false;
    },

    // 음성 모드 버튼 클릭 핸들러
    handleVoiceModeClick() {
      debugLog('🎤 [음성 모드] 버튼 클릭됨!')
      debugLog('🎤 [음성 모드] 클릭 시점 상태:', {
        examId: this.examId,
        exam: this.exam,
        voiceMode: this.voiceMode,
        isAuthenticated: this.isAuthenticated
      })
      this.toggleVoiceMode()
      // 음성 모드가 활성화되면 실시간 텍스트 초기화
      if (this.voiceMode) {
        this.realtimeVoiceText = null
      }
    },

    // 음성 모드 토글
    async toggleVoiceMode() {
      debugLog('🎤 [음성 모드] toggleVoiceMode 호출됨')
      debugLog('🎤 [음성 모드] 현재 상태:', {
        examId: this.examId,
        currentVoiceMode: this.voiceMode,
        exam: this.exam,
        examVoiceModeEnabled: this.exam ? this.exam.voice_mode_enabled : 'N/A',
        isAuthenticated: this.isAuthenticated
      })
      
      if (!this.examId) {
        debugLog('🎤 [음성 모드] examId가 없음, 음성 모드 비활성화')
        this.showToastMessage(this.$t('takeExam.voiceMode.noExamId'), 'warning')
        return
      }
      
      // 시험의 음성 모드 지원 여부 확인
      if (!this.exam || !this.exam.voice_mode_enabled) {
        debugLog('🎤 [음성 모드] 시험이 음성 모드를 지원하지 않음:', {
          exam: this.exam,
          voice_mode_enabled: this.exam ? this.exam.voice_mode_enabled : 'N/A'
        })
        this.showToastMessage(this.$t('takeExam.voiceMode.notSupported'), 'warning')
        return
      }
      
      debugLog('🎤 [음성 모드] 음성 모드 토글 시작')
      this.voiceMode = !this.voiceMode
      debugLog('🎤 [음성 모드] voiceMode 변경됨:', this.voiceMode)
      
      if (this.voiceMode) {
        debugLog('🎤 [음성 모드] 음성 모드 활성화 중...')
        this.showToastMessage(this.$t('takeExam.voiceMode.activated'), 'success')
        
        // 음성 기능 사용 가능 여부 확인
        debugLog('🎤 [음성 모드] 음성 기능 사용 가능 여부 확인 시작')
        await this.checkVoiceCapability()
        debugLog('🎤 [음성 모드] 음성 기능 사용 가능 여부 확인 완료')
        
        // 1초 딜레이 추가
        debugLog('🎤 [음성 모드] 1초 딜레이 시작')
        await new Promise(resolve => setTimeout(resolve, 1000))
        debugLog('🎤 [음성 모드] 1초 딜레이 완료')
        
        debugLog('🎤 [음성 모드] 음성 모드 활성화 완료')
      } else {
        debugLog('🎤 [음성 모드] 음성 모드 비활성화')
        this.showToastMessage(this.$t('takeExam.voiceMode.deactivated'), 'info')
        
        // Voice Mode 비활성화 시 평가 메시지도 숨기기
        this.showVoiceIncorrectReason = false
        this.voiceIncorrectData = null
        debugLog('🎤 [음성 모드] 평가 메시지 숨김 처리 완료')
      }
    },

    // 음성 기능 사용 가능 여부 확인
    checkVoiceCapability() {
      debugLog('🎤 [음성 기능] checkVoiceCapability 호출됨')
      debugLog('🎤 [음성 기능] 브라우저 지원 여부:', {
        mediaDevices: 'mediaDevices' in navigator,
        getUserMedia: 'getUserMedia' in navigator.mediaDevices,
        speechSynthesis: 'speechSynthesis' in window,
        speechRecognition: 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window
      })
      
      if ('mediaDevices' in navigator && 'getUserMedia' in navigator.mediaDevices) {
        this.voiceEnabled = true
        debugLog('🎤 [음성 기능] 음성 기능 지원됨')
        debugLog('🎤 [음성 기능] voiceEnabled 설정됨:', this.voiceEnabled)
      } else {
        this.voiceEnabled = false
        debugLog('🎤 [음성 기능] 음성 기능 미지원, 음성 모드 비활성화')
        this.showToastMessage(this.$t('takeExam.voiceMode.browserNotSupported'), 'warning')
        this.voiceMode = false
        debugLog('🎤 [음성 기능] voiceMode 비활성화됨:', this.voiceMode)
      }
    },

    // 음성 인터페이스에서 Pass 처리
    handleVoicePass() {
      debugLog('🎤 [VOICE PASS] 음성으로 정답 처리')
      this.handleSolvedStatusClick('Y')
      this.showToastMessage(this.$t('takeExam.voiceMode.correctAnswer'), 'success')
    },

    // 음성 인터페이스에서 Fail 처리
    handleVoiceFail() {
      debugLog('🎤 [VOICE FAIL] 음성으로 오답 처리')
      this.handleSolvedStatusClick('N')
      this.showToastMessage(this.$t('takeExam.voiceMode.incorrectAnswer'), 'info')
    },

    handleVoiceIncorrectReason(data) {
      debugLog('🎤 [VOICE INCORRECT] 오답 데이터 표시:', data)
      this.showVoiceIncorrectReason = true
      this.voiceIncorrectData = data
    },

    handleHideVoiceIncorrectReason() {
      debugLog('🎤 [VOICE INCORRECT] 오답 이유 숨기기')
      this.showVoiceIncorrectReason = false
      this.voiceIncorrectData = null
    },

    handleRealtimeText(data) {
      debugLog('🎤 [REALTIME TEXT] 실시간 텍스트 업데이트:', data)
      console.log('🎤 [REALTIME TEXT] 실시간 텍스트 업데이트:', data)
      this.realtimeVoiceText = data
    },

    cleanQuestionUrls() {
      // 모든 문제의 URL에서 'nan' 제거
      if (this.exam && this.exam.questions) {
        this.exam.questions.forEach(question => {
          if (question.url && (question.url === 'nan' || question.url === 'NaN' || question.url === 'Nan')) {
            question.url = '';
          }
        });
      }
    },

    onTrackProgressChange() {
      // Track Progress 설정 변경 시 세션 저장
      this.saveSession();
    },
    recordCurrentQuestionTime() {
      if (this.questionStartTime !== null) {
        const elapsed = Math.floor((Date.now() - this.questionStartTime) / 1000);
        this.$set(this.questionTimes, this.currentQuestionIndex, elapsed);

        // 전체 누적 시간에 현재 문제 시간 추가
        this.elapsedSeconds += elapsed;
      }
      // 현재 문제 타이머 정지
      if (this.questionTimer) {
        clearInterval(this.questionTimer);
        this.questionTimer = null;
      }
    },
    async loadExam() {
      try {
        const urlParams = new URLSearchParams(window.location.search)
        const selectedParam = urlParams.get('selected')
        const examId = this.$route.params.examId || urlParams.get('exam_id')

        if (!examId) {
          return
        }

        // 즐겨찾기 모드 처리
        if (examId === 'favorites') {
          // 즐겨찾기 모드에서는 선택된 문제들만 사용
          if (!selectedParam) {
            debugLog('즐겨찾기 모드인데 selected 파라미터가 없습니다.')
            return
          }

          // 즐겨찾기 exam 정보 직접 설정
          const currentLanguage = this.$i18n.locale || 'ko'
          this.exam = {
            id: 'favorites',
            title: currentLanguage === 'ko' ? '즐겨찾기' : currentLanguage === 'en' ? 'Favorites' : 'Favoritos',
            display_title: currentLanguage === 'ko' ? '즐겨찾기' : currentLanguage === 'en' ? 'Favorites' : 'Favoritos',
            description: currentLanguage === 'ko' ? '즐겨찾기한 문제들을 풀어보세요.' : currentLanguage === 'en' ? 'Solve your favorite questions.' : 'Resuelve tus preguntas favoritas.',
            questions: []
          }

          // 선택된 문제 ID 목록
          const selectedIds = selectedParam.split(',').filter(id => id.trim())
          
          // 선택된 문제들을 API에서 가져오기
          try {
            const questionsResponse = await axios.get('/api/favorite-exam-questions/', {
              params: {
                select: 'id,csv_id,title_ko,title_en,content_ko,content_en,answer_ko,answer_en,explanation_ko,explanation_en,difficulty,url,group_id,created_at,updated_at,created_language,is_ko_complete,is_en_complete,created_by'
              }
            })
            
            // 선택된 ID에 해당하는 문제들만 필터링
            const allQuestions = questionsResponse.data.questions || []
            this.exam.questions = allQuestions.filter(q => 
              selectedIds.includes(q.id) || selectedIds.includes(q.csv_id?.toString())
            )
            
            debugLog('즐겨찾기 문제 로드 완료:', {
              totalQuestions: allQuestions.length,
              selectedQuestions: this.exam.questions.length,
              selectedIds: selectedIds
            })
          } catch (error) {
            debugLog('즐겨찾기 문제 로드 실패:', error, 'error')
            this.exam.questions = []
            return
          }

          this.$set(this, 'currentQuestionIndex', 0)
          this.sessionKey = `exam_favorites`
          this.answers = {}
          
          // order 파라미터가 있으면 해당 순서대로 정렬
          const orderParam = urlParams.get('order')
          if (orderParam) {
            this.sortQuestionsByOrder(orderParam)
          }
          
          // 문제 URL 정리 및 통계 로드 (비동기)
          this.cleanQuestionUrls()
          this.loadIgnoredQuestions().catch(error => {
            console.warn('무시된 문제 목록 로드 실패:', error)
          })
          this.loadQuestionStatistics(null).then(() => {
            this.mapStatisticsToQuestions()
          }).catch(error => {
            console.warn('문제 통계 로드 실패:', error)
          })
          
          return
        }

        // 원래 exam-detail 페이지의 필터 파라미터 저장 (selected, order, restart 제외)
        const originalParams = new URLSearchParams()
        for (const [key, value] of urlParams.entries()) {
          if (!['selected', 'order', 'restart'].includes(key)) {
            originalParams.append(key, value)
          }
        }
        this.originalFilterParams = originalParams.toString()

        // 시험 정보 불러오기 (언어 헤더 포함)
        const currentLanguage = this.$i18n.locale || 'en'
        
        // 사용자 프로필 언어 가져오기
        const userProfileLanguage = await this.getUserProfileLanguage()
        
        debugLog('🎤 [시험 로드] 시험 데이터 로드 시작:', {
          examId: examId,
          currentLanguage: currentLanguage,
          userProfileLanguage: userProfileLanguage
        })
        
        // 사용자 프로필 언어에 맞는 필드만 선택 (성능 최적화)
        // 현재 언어 필드 + 영어 fallback 필드 + display_title, display_description 필드만 요청
        const selectFields = ['id', 'is_public', 'is_original', 'created_at', 'created_language', 'is_ko_complete', 'is_en_complete', 'file_name', 'questions', 'total_questions', 'tags', 'display_title', 'display_description']
        
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
        
        const response = await axios.get(`/api/exam/${examId}/`, {
          headers: {
            'Accept-Language': currentLanguage
          },
          params: {
            select: selectFields.join(','),
            lang: userProfileLanguage
          }
        })
        
        debugLog('🎤 [시험 로드] 시험 데이터 응답:', {
          exam: response.data,
          voice_mode_enabled: response.data.voice_mode_enabled,
          examKeys: Object.keys(response.data)
        })
        
        // Vue 반응형으로 설정
        this.$set(this, 'exam', response.data)
        this.$set(this, 'currentQuestionIndex', 0) // 첫 번째 문제로 설정
        this.sessionKey = `exam_${examId}`
        this.answers = {} // <-- 답안 초기화



        // 문제 URL에서 'nan' 제거
        this.cleanQuestionUrls()

        // 무시된 문제 목록 로드 (비동기로 백그라운드에서 로딩)
        this.loadIgnoredQuestions().catch(error => {
          console.warn('무시된 문제 목록 로드 실패:', error)
        });

        // 문제 통계 로드 (비동기로 백그라운드에서 로딩)
        this.loadQuestionStatistics(examId).then(() => {
          // 통계 로드 완료 후 문제 데이터에 통계 정보 매핑
          this.mapStatisticsToQuestions()
        }).catch(error => {
          console.warn('문제 통계 로드 실패:', error)
        })

        // selected 파라미터가 있으면 해당 문제만 필터링
        if (selectedParam) {
          const selectedIds = selectedParam.split(',')
          this.exam.questions = this.exam.questions.filter(q => selectedIds.includes(q.id) || selectedIds.includes(q.csv_id?.toString()))
        }

        // order 파라미터가 있으면 해당 순서대로 정렬, 없으면 우선순위에 따라 정렬 후 정확도별 그룹화된 랜덤 순서 적용
        const orderParam = urlParams.get('order')
        if (orderParam) {
          this.sortQuestionsByOrder(orderParam)
        } else {
          // 우선순위에 따라 정렬 후 정확도별 그룹화된 랜덤 순서 적용
          this.sortQuestionsByPriority()
          this.shuffleQuestionsByAccuracyGroups()
        }

        // 이어풀기 모드 등 기존 로직 유지
        const continueMode = urlParams.get('continue')
        const resultId = urlParams.get('result_id')
        if (continueMode === 'true' && resultId) {
          this.isContinueMode = true
          this.previousResultId = resultId
          await this.loadPreviousResult(resultId)
        }
        this.initializeSession(); // initializeSession 내부에서 initializeTimers 호출됨
        if (continueMode === 'true' && resultId) {
          this.isContinueMode = true
          this.previousResultId = resultId
        }

        // 즐겨찾기 상태 로드 (mounted에서 이미 호출했으므로 중복 제거)
        // await this.loadFavoriteStatus();
        
        // 연결된 프로젝트 로드 (비동기로 백그라운드에서 로딩)
        this.loadConnectedStudies(examId).then(() => {
          // 비공개 시험이고 로그인한 사용자인 경우 스터디 가입 신청 체크
          if (this.exam && !this.exam.is_public && this.isAuthenticated) {
            this.checkAndRequestStudyJoin()
          }
        }).catch(error => {
          console.warn('연결된 프로젝트 로드 실패:', error)
        });
      } catch (error) {
        // 에러 처리
        debugLog('시험 로드 실패:', error, 'error')
        
        // 401 에러인 경우 공개 시험인지 확인
        if (error.response && error.response.status === 401) {
          const examId = this.$route.params.examId || new URLSearchParams(window.location.search).get('exam_id')
          
          // 공개 시험인지 확인
          try {
            const publicExamResponse = await axios.get(`/api/exams/`, {
              params: {
                id: examId,
                is_public: true
              }
            })
            
            const publicExams = publicExamResponse.data.results || publicExamResponse.data || []
            const isPublicExam = Array.isArray(publicExams) && publicExams.some(exam => exam.id === examId || exam.id === parseInt(examId))
            
            // 공개 시험이면 에러를 무시하고 계속 진행 (다시 시도)
            if (isPublicExam) {
              debugLog('공개 시험 확인됨 - 시험 정보 다시 로드 시도')
              // 시험 정보를 다시 로드 시도
              try {
                const retryResponse = await axios.get(`/api/exam/${examId}/`, {
                  headers: {
                    'Accept-Language': this.$i18n.locale || 'en'
                  }
                })
                this.$set(this, 'exam', retryResponse.data)
                this.$set(this, 'currentQuestionIndex', 0)
                this.sessionKey = `exam_${examId}`
                this.answers = {}
                this.initializeSession()
                return
              } catch (retryError) {
                debugLog('시험 정보 다시 로드 실패:', retryError)
              }
            }
          } catch (checkError) {
            debugLog('공개 시험 확인 실패:', checkError)
          }
          
          // 공개 시험이 아니거나 확인 실패한 경우 로그인 페이지로 리다이렉트
          const returnTo = encodeURIComponent(`/take-exam/${examId}${window.location.search}`)
          this.$router.push(`/login?returnTo=${returnTo}`)
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
                
                // 가입 요청 생성 (비동기로 실행되지만 await하지 않음)
                this.checkAndRequestStudyJoinFor403Error(examId).then((joinRequestSent) => {
                  debugLog('가입 요청 생성 완료', { joinRequestSent })
                  
                  // 가입 요청 성공 후 권한 없음 메시지 표시
                  if (joinRequestSent) {
                    // 가입 요청 메시지는 checkAndRequestStudyJoinFor403Error 내부에서 이미 표시됨
                    // 권한 없음 메시지를 큐에 추가 (가입 요청 메시지 다음에 표시됨)
                    this.showToastMessage(
                      error.response.data?.error || this.$t('takeExam.alerts.noPermission') || '이 시험에 접근할 권한이 없습니다.',
                      'error'
                    )
                  } else {
                    // 가입 요청이 생성되지 않았으면 바로 권한 없음 메시지 표시
                    this.showToastMessage(
                      error.response.data?.error || this.$t('takeExam.alerts.noPermission') || '이 시험에 접근할 권한이 없습니다.',
                      'error'
                    )
                  }
                  
                  // 메시지가 보이도록 약간의 지연 후 리다이렉트
                  setTimeout(() => {
                    if (examId) {
                      this.$router.push(`/exam-detail/${examId}`)
                    } else {
                      this.$router.push('/exam-management')
                    }
                  }, 2000) // 2초 후 리다이렉트 (메시지가 보이도록)
                }).catch(err => {
                  debugLog('가입 요청 생성 실패:', err, 'error')
                  // 가입 요청 실패 시 권한 없음 메시지 표시
                  this.showToastMessage(
                    error.response.data?.error || this.$t('takeExam.alerts.noPermission') || '이 시험에 접근할 권한이 없습니다.',
                    'error'
                  )
                  // 리다이렉트
                  setTimeout(() => {
                    if (examId) {
                      this.$router.push(`/exam-detail/${examId}`)
                    } else {
                      this.$router.push('/exam-management')
                    }
                  }, 1000)
                })
              } else {
                // 연결된 스터디가 없으면 바로 리다이렉트
                debugLog('연결된 스터디가 없음 - 리다이렉트')
                this.showToastMessage(
                  error.response.data?.error || this.$t('takeExam.alerts.noPermission') || '이 시험에 접근할 권한이 없습니다.',
                  'error'
                )
                if (examId) {
                  this.$router.push(`/exam-detail/${examId}`)
                } else {
                  this.$router.push('/exam-management')
                }
              }
            }).catch(err => {
              debugLog('403 에러 후 연결된 스터디 로드 실패:', err, 'error')
              // 연결된 스터디 로드 실패해도 리다이렉트
              this.showToastMessage(
                error.response.data?.error || this.$t('takeExam.alerts.noPermission') || '이 시험에 접근할 권한이 없습니다.',
                'error'
              )
              if (examId) {
                this.$router.push(`/exam-detail/${examId}`)
              } else {
                this.$router.push('/exam-management')
              }
            })
          } else {
            // 로그인하지 않은 사용자이거나 examId가 없는 경우
            this.showToastMessage(
              error.response.data?.error || this.$t('takeExam.alerts.noPermission') || '이 시험에 접근할 권한이 없습니다.',
              'error'
            )
            // exam-detail 페이지로 리다이렉트
            if (examId) {
              this.$router.push(`/exam-detail/${examId}`)
            } else {
              this.$router.push('/exam-management')
            }
          }
          return
        }
        
        // 404 에러인 경우 시험이 존재하지 않음
        if (error.response && error.response.status === 404) {
          this.showToastMessage(
            error.response?.data?.error || this.$t('takeExam.alerts.examNotFound') || '시험을 찾을 수 없습니다. 시험이 삭제되었거나 존재하지 않습니다.',
            'error'
          )
          // exam-management로 리다이렉트
          setTimeout(() => {
            this.$router.push('/exam-management')
          }, 2000)
          return
        }
        
        // 기타 에러
        this.showToastMessage(
          error.response?.data?.error || this.$t('takeExam.alerts.loadExamFailed') || '시험 정보를 불러오는데 실패했습니다.',
          'error'
        )
      } finally {
        debugLog('=== loadExam 완료 - 화면 즉시 렌더링 ===', {
          examId: this.exam?.id,
          questionCount: this.exam?.questions?.length,
          timestamp: Date.now()
        })
        this.loading = false
        this.stopLoadingTimer() // 로딩 타이머 정리
      }
    },
    
    async loadConnectedStudies(examId) {
      try {
        // 인증되지 않은 사용자는 연결된 프로젝트를 로드하지 않음
        if (!this.isAuthenticated) {
          this.connectedStudies = []
          // 인증되지 않은 사용자의 경우 캐시도 정리
          this.clearConnectedStudiesCache(examId)
          console.log('인증되지 않은 사용자 - 연결된 프로젝트 로드 건너뜀')
          return Promise.resolve()
        }

        // 캐시에서 먼저 확인
        const cacheKey = `connected_studies_${examId}`
        const cachedStudies = getSessionCache(cacheKey)
        
        if (cachedStudies && cachedStudies.length > 0) {
          this.connectedStudies = cachedStudies
          console.log('연결된 프로젝트 캐시에서 로드:', cachedStudies.length, '개')
          return Promise.resolve()
        }
        
        // 캐시에 없으면 API 호출
        debugLog('연결된 스터디 API 호출 시작', { examId })
        const response = await axios.get(`/api/exam/${examId}/connected-studies/`)
        debugLog('연결된 스터디 API 응답', { 
          status: response.status, 
          success: response.data?.success,
          connectedStudiesCount: response.data?.connected_studies?.length || 0
        })
        
        if (response.data.success) {
          this.connectedStudies = response.data.connected_studies || []
          // 캐시에 저장 (30분 유효)
          setSessionCache(cacheKey, this.connectedStudies)
          console.log('연결된 프로젝트 API에서 로드 및 캐시 저장:', this.connectedStudies.length, '개')
          return Promise.resolve()
        } else {
          console.log('연결된 프로젝트 로드 실패 - API 응답 오류')
          this.connectedStudies = []
          return Promise.resolve()
        }
      } catch (error) {
        debugLog('연결된 프로젝트 로드 실패:', error, 'error')
        // 연결된 프로젝트 로드 실패는 시험 로드에 영향을 주지 않도록 조용히 처리
        // 하지만 Promise는 resolve하여 체인을 계속 진행할 수 있도록 함
        this.connectedStudies = []
        return Promise.resolve()
      }
    },

    clearConnectedStudiesCache(examId) {
      try {
        const cacheKey = `connected_studies_${examId}`
        sessionStorage.removeItem(cacheKey)
        console.log('연결된 프로젝트 캐시 정리됨:', cacheKey)
      } catch (error) {
        console.log('캐시 정리 중 오류:', error)
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
            
            // 멤버가 아니면 가입 신청
            if (!isMember) {
              // 이미 가입 요청이 있는지 확인
              try {
                const joinRequestsResponse = await axios.get(`/api/study-join-request/user/`)
                const existingRequest = joinRequestsResponse.data.find(req => {
                  // study 필드가 객체인 경우와 ID인 경우 모두 처리
                  const reqStudyId = typeof req.study === 'object' ? req.study.id : req.study
                  return reqStudyId === connectedStudy.study_id && req.status === 'pending'
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
                  this.showToastMessage(
                    this.$t('takeExam.studyJoinRequestSent') || `"${connectedStudy.study_title}" 스터디에 가입 요청을 보냈습니다.`,
                    'info'
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
    
    /**
     * 비공개 시험에 접근한 로그인 사용자가 연결된 스터디의 멤버가 아니면 가입 신청
     */
    async checkAndRequestStudyJoin() {
      if (!this.isAuthenticated || !this.exam || this.exam.is_public) {
        return
      }
      
      try {
        // 연결된 스터디가 없으면 건너뛰기
        if (!this.connectedStudies || this.connectedStudies.length === 0) {
          return
        }
        
        // 각 연결된 스터디에 대해 멤버 여부 확인
        for (const connectedStudy of this.connectedStudies) {
          try {
            // 스터디 상세 정보 가져오기 (멤버 정보 포함)
            const studyResponse = await axios.get(`/api/studies/${connectedStudy.study_id}/`)
            const study = studyResponse.data
            
            // 사용자가 이미 멤버인지 확인
            const user = getCurrentUserFromPermissions()
            if (!user) return
            
            const isMember = study.members && study.members.some(member => {
              if (!member.user) return false
              const memberUserId = typeof member.user === 'object' ? member.user.id : member.user
              return memberUserId === user.id && member.is_active === true
            })
            
            // 멤버가 아니면 가입 신청
            if (!isMember) {
              // 이미 가입 요청이 있는지 확인
              try {
                const joinRequestsResponse = await axios.get(`/api/study-join-request/user/`)
                const existingRequest = joinRequestsResponse.data.find(req => {
                  // study 필드가 객체인 경우와 ID인 경우 모두 처리
                  const reqStudyId = typeof req.study === 'object' ? req.study.id : req.study
                  return reqStudyId === connectedStudy.study_id && req.status === 'pending'
                })
                
                if (!existingRequest) {
                  // 가입 요청 생성
                  await axios.post('/api/study-join-request/', {
                    study_id: connectedStudy.study_id,
                    message: `비공개 시험 "${getLocalizedContentWithI18n(this.exam, 'title', this.$i18n, this.userProfileLanguage, '시험')}"에 접근하기 위한 가입 요청입니다.`
                  })
                  
                  debugLog('스터디 가입 신청 완료:', connectedStudy.study_id)
                  this.showToastMessage(
                    this.$t('takeExam.studyJoinRequestSent') || `"${connectedStudy.study_title}" 스터디에 가입 요청을 보냈습니다.`,
                    'info'
                  )
                }
              } catch (joinRequestError) {
                debugLog('가입 요청 확인/생성 실패:', joinRequestError, 'error')
                // 가입 요청 실패는 조용히 처리 (이미 요청이 있거나 다른 이유일 수 있음)
              }
            }
          } catch (studyError) {
            debugLog(`스터디 ${connectedStudy.study_id} 정보 로드 실패:`, studyError, 'error')
            // 스터디 정보 로드 실패는 무시하고 계속 진행
          }
        }
      } catch (error) {
        debugLog('스터디 가입 신청 체크 실패:', error, 'error')
        // 에러는 조용히 처리 (사용자 경험에 영향을 주지 않도록)
      }
    },

    async loadSingleQuestion(questionId) {
      try {
        // 로딩 상태 설정
        this.loading = true

        // URL에서 현재 시험 ID 가져오기 (exam_id 또는 examId 모두 지원)
        const urlParams = new URLSearchParams(window.location.search)
        const currentExamId = urlParams.get('exam_id') || urlParams.get('examId')

        // exam_id가 반드시 필요함
        if (!currentExamId) {
          throw new Error('exam_id가 필요합니다. 문제를 열려면 시험 ID가 필요합니다.')
        }

        // 원래 exam-detail 페이지의 필터 파라미터 저장 (question_id, exam_id 제외)
        const originalParams = new URLSearchParams()
        for (const [key, value] of urlParams.entries()) {
          if (!['question_id', 'exam_id', 'examId'].includes(key)) {
            originalParams.append(key, value)
          }
        }
        this.originalFilterParams = originalParams.toString()

        // 인증되지 않은 사용자는 문제를 직접 조회하고 exam 정보는 최소한으로 구성
        if (!this.isAuthenticated) {
          console.log('❌ [loadSingleQuestion] 인증되지 않은 사용자 - 문제 직접 조회', {
            questionId,
            examId: currentExamId,
            isAuthenticated: this.isAuthenticated
          });

          try {
            // 문제 정보 직접 조회
            console.log('문제 조회 시작:', questionId)
            const questionResponse = await axios.get(`/api/questions/${questionId}/`)
            const question = questionResponse.data
            console.log('문제 조회 성공:', question)

            // 시험 정보 최소한으로 조회 (공개 시험인지 확인)
            let examData = null
            try {
              const examResponse = await axios.get(`/api/exam/${currentExamId}/`)
              examData = examResponse.data
              console.log('시험 정보 조회 성공:', examData)
            } catch (examError) {
              console.log('시험 정보 조회 실패, 최소한의 정보로 구성:', examError)
              // 시험 정보를 가져올 수 없으면 최소한의 정보로 구성
              examData = {
                id: currentExamId,
                title_ko: '문제 보기',
                title_en: 'View Question',
                is_public: true,
                total_questions: 1
              }
            }

            // exam 객체 구성 (읽기 전용 모드)
            // Vue 반응형으로 설정 (Vue 2에서는 $set 사용)
            const examObj = {
              ...examData,
              questions: [question],
              total_questions: 1
            }
            this.$set(this, 'exam', examObj)
            this.$set(this, 'currentQuestionIndex', 0)
            this.sessionKey = `exam_${this.exam.id}`
            this.answers = {} // 답안 초기화

            console.log('exam 객체 설정 완료:', {
              exam: this.exam,
              questions: this.exam.questions,
              questionsLength: this.exam.questions?.length,
              currentQuestionIndex: this.currentQuestionIndex,
              currentQuestion: this.currentQuestion,
              examQuestionsType: Array.isArray(this.exam.questions)
            })

            // 로딩 완료 (먼저 설정하여 화면이 업데이트되도록)
            this.loading = false

            // Vue 반응형 업데이트를 위해 nextTick 사용
            await this.$nextTick()

            // 문제 URL에서 'nan' 제거 (nextTick 이후에 실행)
            this.cleanQuestionUrls()
            
            // currentQuestion computed가 제대로 작동하는지 확인
            await this.$nextTick()
            
            console.log('문제 로드 완료, 화면 렌더링 시작:', {
              loading: this.loading,
              exam: this.exam,
              examExists: !!this.exam,
              questions: this.exam?.questions,
              questionsLength: this.exam?.questions?.length,
              questionsIsArray: Array.isArray(this.exam?.questions),
              currentQuestionIndex: this.currentQuestionIndex,
              currentQuestion: this.currentQuestion,
              currentQuestionExists: !!this.currentQuestion,
              currentQuestionTitle: this.currentQuestion?.title_ko || this.currentQuestion?.title_en,
              currentQuestionId: this.currentQuestion?.id
            })
            
            // currentQuestion이 없으면 강제로 재설정
            if (!this.currentQuestion && this.exam && this.exam.questions && this.exam.questions.length > 0) {
              console.log('⚠️ currentQuestion이 null이지만 questions가 있음 - 강제 재설정 시도')
              this.$forceUpdate()
              await this.$nextTick()
              console.log('재설정 후 currentQuestion:', this.currentQuestion)
            }
            return
          } catch (error) {
            console.error('문제 조회 실패:', error)
            this.showToastMessage(
              error.response?.data?.error || this.$t('takeExam.alerts.loadQuestionFailed') || '문제를 불러오는데 실패했습니다.',
              'error'
            )
            // exam-detail 페이지로 리다이렉트
            if (currentExamId) {
              this.$router.push(`/exam-detail/${currentExamId}`)
            } else {
              this.$router.push('/exam-management')
            }
            this.loading = false
            return
          }
        }

        // 인증된 사용자는 기존대로 create-single-question-exam API 호출
        console.log('✅ [loadSingleQuestion] 인증된 사용자 - create-single-question-exam API 호출', {
          questionId,
          examId: currentExamId,
          isAuthenticated: this.isAuthenticated
        });

        const requestData = {
          question_id: questionId,
          exam_id: currentExamId
        }

        // API 호출 전에 짧은 지연 추가 (컴포넌트 완전 마운트 대기)
        await new Promise(resolve => setTimeout(resolve, 100))

        const response = await axios.post('/api/create-single-question-exam/', requestData)

        // Vue 반응형으로 설정
        this.$set(this, 'exam', response.data)
        this.$set(this, 'currentQuestionIndex', 0) // 첫 번째 문제로 설정
        console.log('🔍 loadSingleQuestion - exam 데이터:', {
          exam: this.exam,
          examKeys: Object.keys(this.exam),
          questions: this.exam.questions,
          questionsLength: this.exam.questions?.length,
          firstQuestion: this.exam.questions?.[0],
          firstQuestionKeys: this.exam.questions?.[0] ? Object.keys(this.exam.questions[0]) : null
        })
        this.sessionKey = `exam_${this.exam.id}`
        this.answers = {} // <-- 답안 초기화

        // 문제 URL에서 'nan' 제거
        this.cleanQuestionUrls()

        // 세션 복원 (initializeSession 내부에서 initializeTimers 호출됨)
        this.initializeSession();

        // 즐겨찾기 상태 로드 (mounted에서 이미 호출했으므로 중복 제거)
        // await this.loadFavoriteStatus();

        // 무시된 문제 목록 로드 (비동기로 백그라운드에서 로딩)
        this.loadIgnoredQuestions().catch(error => {
          console.warn('무시된 문제 목록 로드 실패:', error)
        });

        // 문제 통계 로드 (비동기로 백그라운드에서 로딩)
        if (this.exam && this.exam.id) {
          this.loadQuestionStatistics(this.exam.id).then(() => {
            // 통계 로드 완료 후 문제 데이터에 통계 정보 매핑
            this.mapStatisticsToQuestions()
          }).catch(error => {
            console.warn('문제 통계 로드 실패:', error)
          })
        }

        // 로딩 완료 (통계 로드와 무관하게 즉시 화면 표시)
        debugLog('=== loadSingleQuestion 완료 - 화면 즉시 렌더링 ===', {
          examId: this.exam?.id,
          questionCount: this.exam?.questions?.length,
          timestamp: Date.now()
        })
        this.loading = false
        this.stopLoadingTimer() // 로딩 타이머 정리
      } catch (error) {
        this.showToastMessage(this.$t('takeExam.alerts.loadQuestionFailed'), 'error')
        this.loading = false
        this.stopLoadingTimer() // 로딩 타이머 정리
      }
    },

    async loadMultipleQuestionsExam(questionIds, examId) {
      try {
        const response = await axios.post('/api/create-exam/', {
          title: '선택 문제 임시 시험',
          questions: questionIds,
          is_original: false,
          exam_id: examId,
          creation_type: 'copy'  // 기존 문제 복사
        })
        // Vue 반응형으로 설정
        this.$set(this, 'exam', response.data)
        this.$set(this, 'currentQuestionIndex', 0) // 첫 번째 문제로 설정
        this.sessionKey = `exam_${this.exam.id}`
        this.answers = {} // <-- 답안 초기화
        
        // 문제 통계 로드 (비동기로 백그라운드에서 로딩)
        if (this.exam && this.exam.id) {
          this.loadQuestionStatistics(this.exam.id).then(() => {
            // 통계 로드 완료 후 문제 데이터에 통계 정보 매핑
            this.mapStatisticsToQuestions()
          }).catch(error => {
            console.warn('문제 통계 로드 실패:', error)
          })
        }
        
        this.initializeSession() // initializeSession 내부에서 initializeTimers 호출됨
        this.loading = false
        this.stopLoadingTimer() // 로딩 타이머 정리
      } catch (error) {
        this.$toast?.error?.(this.$t('takeExam.alerts.createSingleExamFailed'))
        this.loading = false
        this.stopLoadingTimer() // 로딩 타이머 정리
      }
    },

    async loadPreviousResult(resultId) {
      try {
        const response = await axios.get(`/api/exam-result/${resultId}/`)
        const result = response.data

        // 이미 푼 문제들 수집 (세션에 저장된 답안이 있을 때만 복원)
        for (const detail of result.details) {
          this.answeredQuestions.add(detail.question.id)
          // 세션에 저장된 답안이 있을 때만 복원 (처음 진입 시에는 복원하지 않음)
          const savedSession = sessionStorage.getItem(this.sessionKey)
          if (savedSession) {
            try {
              const sessionData = JSON.parse(savedSession)
              if (sessionData.answers && sessionData.answers[detail.question.id]) {
                this.answers[detail.question.id] = sessionData.answers[detail.question.id]
              }
            } catch (e) { /* ignore */ }
          }
        }

        // 세션에 currentQuestionIndex가 없을 때만 첫 번째 풀지 않은 문제로 이동
        const savedSession = sessionStorage.getItem(this.sessionKey)
        let hasSessionIndex = false
        if (savedSession) {
          try {
            const sessionData = JSON.parse(savedSession)
            hasSessionIndex = typeof sessionData.currentQuestionIndex === 'number' && sessionData.currentQuestionIndex > 0
          } catch (e) { /* ignore */ }
        }
        if (!hasSessionIndex) {
          this.moveToNextUnansweredQuestion()
        }

        // 세션에 currentQuestionIndex가 없을 때만 세션 저장 (기존 답안들 포함)
        if (!hasSessionIndex) {
          this.saveSession()
        }

      } catch (error) {
        // 에러 처리
      }
    },

    moveToNextUnansweredQuestion() {
      if (!this.exam?.questions) return;
      for (let i = 0; i < this.exam.questions.length; i++) {
        const question = this.exam.questions[i]
        if (!this.answeredQuestions.has(question.id)) {
          this.currentQuestionIndex = i
          break
        }
      }
    },

    async nextQuestion() {
      // 인증된 사용자만 답안 저장
      if (this.isAuthenticated) {
        // 현재 답안을 answers에 저장 (실제로 답안을 입력했거나 풀었음/못풀었음 상태를 선택한 경우에만)
        const currentQuestionId = this.currentQuestion?.id;
        if (currentQuestionId) {
          let answerToSave = this.currentAnswer || '';

          // 풀었음/못풀었음 상태가 있으면 답안에 포함
          if (!this.isYNQuestion && this.solvedStatus && (!this.currentAnswer || !this.currentAnswer.trim())) {
            answerToSave = this.solvedStatus;
          }

          // 실제로 답안을 입력했거나 풀었음/못풀었음 상태를 선택한 경우에만 저장
          if (answerToSave && answerToSave.trim()) {
            this.$set(this.answers, currentQuestionId, answerToSave);
            console.log('💾 답안 저장:', currentQuestionId, answerToSave);
          } else {
            console.log('💾 답안이 없어서 저장하지 않음:', currentQuestionId);
          }
        }
      }

      this.recordCurrentQuestionTime();
      if (this.exam?.questions && this.currentQuestionIndex < this.exam.questions.length - 1) {
        this.currentQuestionIndex++
        this.showAnswer = false; // 다음 문제로 이동 시 정답 숨기기
        this.showExplanation = false; // 다음 문제로 이동 시 설명 숨기기
        this.solvedStatus = null; // 풀었음/못풀었음 상태 초기화
        this.currentQuestionTimeReactive = 0; // 현재 문제 시간 초기화
        if (this.isAuthenticated) {
          this.saveSession() // 인증된 사용자만 세션 저장
        }
        this.startQuestionTimer();

        // 새로운 문제의 즐겨찾기 상태 로드
        await this.loadFavoriteStatus();

        this.$nextTick(() => {
          this.$refs.answerInput?.focus()

          // 🚀 문제 이동 완료 후 번역 감지 및 실행
          this.checkAndTriggerTranslation();
        })
      } else {
        this.examCompleted = true
        this.startQuestionTimer(); // 마지막 문제도 기록
        this.saveSession() // 시험 완료 시 세션 저장
      }
    },



    async selectYNAnswer(answer) {
      // 인증되지 않은 사용자는 답안을 선택할 수 없음
      if (!this.isAuthenticated) {
        return
      }

      // 선택한 답안을 저장
      const currentQuestionId = this.currentQuestion?.id;
      if (currentQuestionId) {
        this.$set(this.answers, currentQuestionId, answer);
      }

              // 자동으로 다음 문제로 이동
        this.recordCurrentQuestionTime();
        if (this.currentQuestionIndex < this.exam.questions.length - 1) {
          this.currentQuestionIndex++
          this.showAnswer = false; // 다음 문제로 이동 시 정답 숨기기
          this.showExplanation = false; // 다음 문제로 이동 시 설명 숨기기
          this.solvedStatus = null; // 풀었음/못풀었음 상태 초기화
          this.currentQuestionTimeReactive = 0; // 현재 문제 시간 초기화
          this.saveSession() // 다음 문제로 이동 시 세션 저장
          this.startQuestionTimer();
          // 새로운 문제의 즐겨찾기 상태 로드
          await this.loadFavoriteStatus();
        this.$nextTick(() => {
          this.$refs.answerInput?.focus()
        })
      } else {
        this.examCompleted = true
        this.startQuestionTimer(); // 마지막 문제도 기록
        this.saveSession() // 시험 완료 시 세션 저장
      }
    },

    // 풀었다/못풀었다 버튼 클릭 핸들러
    handleSolvedStatusClick(status) {
      if (!this.isAuthenticated) {
        // 인증되지 않은 경우 로그인 화면으로 이동
        this.$router.push('/login')
        return
      }
      // 인증된 경우 기존 selectSolvedStatus 메서드 호출
      this.selectSolvedStatus(status)
    },

    async selectSolvedStatus(status) {

      // 풀었음/못풀었음 상태 저장
      this.solvedStatus = status;

      // 해결됨(Y)을 선택한 경우 정답을 자동으로 입력
      if (status === 'Y' && this.currentQuestion) {
        // 현재 언어에 맞는 정답 필드 사용 (폴백 포함, 동적 처리)
        const correctAnswer = getLocalizedContentWithI18n(this.currentQuestion, 'answer', this.$i18n, this.userProfileLanguage, '')

        this.currentAnswer = correctAnswer;

        // Pass 버튼 클릭 시 맞춘 문제 로그 추가
        console.log('🔍 [PASS] 문제를 맞췄습니다:', {
          questionIndex: this.currentQuestionIndex + 1,
          questionId: this.currentQuestion.id,
          questionTitle: getLocalizedContentWithI18n(this.currentQuestion, 'title', this.$i18n, this.userProfileLanguage, 'Unknown'),
          userAnswer: this.currentAnswer,
          correctAnswer: correctAnswer,
          language: this.userProfileLanguage || this.$i18n.locale || 'en',
          timestamp: new Date().toLocaleTimeString()
        });
      }

      // 못풀었음(N)을 선택한 경우 공백을 자동으로 입력
      if (status === 'N') {
        this.currentAnswer = ' ';

        // 못풀었음 로그 추가
        console.log('🔍 [FAIL] 문제를 못풀었습니다:', {
          questionIndex: this.currentQuestionIndex + 1,
          questionId: this.currentQuestion.id,
          questionTitle: getLocalizedContentWithI18n(this.currentQuestion, 'title', this.$i18n, this.userProfileLanguage, 'Unknown'),
          userAnswer: this.currentAnswer,
          language: this.$i18n.locale,
          timestamp: new Date().toLocaleTimeString()
        });
      }

              // 풀었음/못풀었음이 선택된 경우 자동으로 다음 문제로 이동
        this.recordCurrentQuestionTime();
        if (this.currentQuestionIndex < this.exam.questions.length - 1) {
          this.currentQuestionIndex++
          this.showAnswer = false; // 다음 문제로 이동 시 정답 숨기기
          this.showExplanation = false; // 다음 문제로 이동 시 설명 숨기기
          this.solvedStatus = null; // 풀었음/못풀었음 상태 초기화
          this.currentQuestionTimeReactive = 0; // 현재 문제 시간 초기화
          this.saveSession() // 다음 문제로 이동 시 세션 저장
          this.startQuestionTimer();
          // 새로운 문제의 즐겨찾기 상태 로드
          await this.loadFavoriteStatus();
        this.$nextTick(() => {
          this.$refs.answerInput?.focus()
        })
      } else {
        this.examCompleted = true
        this.startQuestionTimer(); // 마지막 문제도 기록
        this.saveSession() // 시험 완료 시 세션 저장
      }
    },

    // Submit 버튼 클릭 핸들러 (force_answer 모드용)
    async submitAnswer() {
      if (!this.isAuthenticated) {
        // 인증되지 않은 경우 로그인 화면으로 이동
        this.$router.push('/login')
        return
      }

      if (!this.currentAnswer.trim()) {
        this.showToastMessage(this.$t('takeExam.enterAnswerFirst'), 'warning')
        return
      }

      // 현재 언어에 맞는 정답 가져오기
      const correctAnswer = getLocalizedContentWithI18n(this.currentQuestion, 'answer', this.$i18n, this.userProfileLanguage, '') || this.currentQuestion.answer || '';

      // 답안 비교 (대소문자 무시, 공백 제거, 순서 정규화)
      let isCorrect = false;

      if (this.isMultipleChoice) {
        // 복수 선택의 경우: 순서 무관하게 비교
        const userAnswers = this.currentAnswer.split(/[,，;；]/).map(s => s.trim().toLowerCase()).filter(s => s).sort();
        const expectedAnswers = correctAnswer.split(/[,，;；]/).map(s => s.trim().toLowerCase()).filter(s => s).sort();
        isCorrect = JSON.stringify(userAnswers) === JSON.stringify(expectedAnswers);
      } else {
        // 단일 선택의 경우: 정확히 일치하는지 확인
        const userAnswer = this.currentAnswer.trim().toLowerCase();
        const expectedAnswer = correctAnswer.trim().toLowerCase();
        isCorrect = userAnswer === expectedAnswer;
      }

      // 결과에 따른 상태 설정
      if (isCorrect) {
        this.solvedStatus = 'Y'; // Pass
        this.showToastMessage(this.$t('takeExam.correctAnswer'), 'success')

        console.log('🔍 [SUBMIT] 정답:', {
          questionIndex: this.currentQuestionIndex + 1,
          questionId: this.currentQuestion.id,
          userAnswer: this.currentAnswer,
          correctAnswer: correctAnswer,
          language: this.userProfileLanguage || this.$i18n.locale || 'en',
          timestamp: new Date().toLocaleTimeString()
        });
      } else {
        this.solvedStatus = 'N'; // Fail
        this.showToastMessage(this.$t('takeExam.incorrectAnswer'), 'error')

        console.log('🔍 [SUBMIT] 오답:', {
          questionIndex: this.currentQuestionIndex + 1,
          questionId: this.currentQuestion.id,
          userAnswer: this.currentAnswer,
          correctAnswer: correctAnswer,
          language: this.userProfileLanguage || this.$i18n.locale || 'en',
          timestamp: new Date().toLocaleTimeString()
        });
      }

      // 자동으로 다음 문제로 이동
      this.recordCurrentQuestionTime();
      if (this.currentQuestionIndex < this.exam.questions.length - 1) {
        this.currentQuestionIndex++
        this.showAnswer = false;
        this.showExplanation = false;
        this.solvedStatus = null;
        this.currentQuestionTimeReactive = 0; // 현재 문제 시간 초기화
        this.saveSession()
        this.startQuestionTimer();

        // 새로운 문제의 즐겨찾기 상태 로드
        await this.loadFavoriteStatus();
        this.$nextTick(() => {
          this.$refs.answerInput?.focus()
        })
      } else {
        this.examCompleted = true
        this.startQuestionTimer();
        this.saveSession()
      }
    },

    async previousQuestion() {
      if (this.currentQuestionIndex > 0) {
        // 현재 답안을 answers에 저장 (실제로 답안을 입력했거나 풀었음/못풀었음 상태를 선택한 경우에만)
        const currentQuestionId = this.currentQuestion?.id;
        if (currentQuestionId) {
          let answerToSave = this.currentAnswer || '';

          // 풀었음/못풀었음 상태가 있으면 답안에 포함
          if (!this.isYNQuestion && this.solvedStatus && (!this.currentAnswer || !this.currentAnswer.trim())) {
            answerToSave = this.solvedStatus;
          }

          // 실제로 답안을 입력했거나 풀었음/못풀었음 상태를 선택한 경우에만 저장
          if (answerToSave && answerToSave.trim()) {
            this.$set(this.answers, currentQuestionId, answerToSave);
            console.log('💾 답안 저장:', currentQuestionId, answerToSave);
          } else {
            console.log('💾 답안이 없어서 저장하지 않음:', currentQuestionId);
          }
        }

        this.recordCurrentQuestionTime();
        this.currentQuestionIndex--
        this.showAnswer = false; // 이전 문제로 이동 시 정답 숨기기
        this.showExplanation = false; // 이전 문제로 이동 시 설명 숨기기
        this.solvedStatus = null; // 풀었음/못풀었음 상태 초기화
        this.currentQuestionTimeReactive = 0; // 현재 문제 시간 초기화
        this.startQuestionTimer();
        this.saveSession() // 이전 문제로 이동 시 세션 저장

        // 새로운 문제의 즐겨찾기 상태 로드
        await this.loadFavoriteStatus();

        this.$nextTick(() => {
          this.$refs.answerInput?.focus()

          // 🚀 문제 이동 완료 후 번역 감지 및 실행
          this.checkAndTriggerTranslation();
        })
      }
    },

    async goToFirstQuestion() {
      if (this.currentQuestionIndex > 0) {
        // 현재 답안을 answers에 저장 (실제로 답안을 입력했거나 풀었음/못풀었음 상태를 선택한 경우에만)
        const currentQuestionId = this.currentQuestion?.id;
        if (currentQuestionId) {
          let answerToSave = this.currentAnswer || '';

          // 풀었음/못풀었음 상태가 있으면 답안에 포함
          if (!this.isYNQuestion && this.solvedStatus && (!this.currentAnswer || !this.currentAnswer.trim())) {
            answerToSave = this.solvedStatus;
          }

          // 실제로 답안을 입력했거나 풀었음/못풀었음 상태를 선택한 경우에만 저장
          if (answerToSave && answerToSave.trim()) {
            this.$set(this.answers, currentQuestionId, answerToSave);
            console.log('💾 답안 저장:', currentQuestionId, answerToSave);
          } else {
            console.log('💾 답안이 없어서 저장하지 않음:', currentQuestionId);
          }
        }

        this.recordCurrentQuestionTime();
        this.currentQuestionIndex = 0;
        this.showAnswer = false; // 맨 처음 문제로 이동 시 정답 숨기기
        this.showExplanation = false; // 맨 처음 문제로 이동 시 설명 숨기기
        this.solvedStatus = null; // 풀었음/못풀었음 상태 초기화
        this.currentQuestionTimeReactive = 0; // 현재 문제 시간 초기화
        this.startQuestionTimer();
        this.saveSession() // 맨 처음 문제로 이동 시 세션 저장
        // 새로운 문제의 즐겨찾기 상태 로드
        await this.loadFavoriteStatus();

        this.$nextTick(() => {
          this.$refs.answerInput?.focus()

          // 🚀 문제 이동 완료 후 번역 감지 및 실행
          this.checkAndTriggerTranslation();
        })
      }
    },

    async goToLastQuestion() {
      if (this.currentQuestionIndex < this.exam.questions.length - 1) {
        // 현재 답안을 answers에 저장 (실제로 답안을 입력했거나 풀었음/못풀었음 상태를 선택한 경우에만)
        const currentQuestionId = this.currentQuestion?.id;
        if (currentQuestionId) {
          let answerToSave = this.currentAnswer || '';

          // 풀었음/못풀었음 상태가 있으면 답안에 포함
          if (!this.isYNQuestion && this.solvedStatus && (!this.currentAnswer || !this.currentAnswer.trim())) {
            answerToSave = this.solvedStatus;
          }

          // 실제로 답안을 입력했거나 풀었음/못풀었음 상태를 선택한 경우에만 저장
          if (answerToSave && answerToSave.trim()) {
            this.$set(this.answers, currentQuestionId, answerToSave);
            console.log('💾 답안 저장:', currentQuestionId, answerToSave);
          } else {
            console.log('💾 답안이 없어서 저장하지 않음:', currentQuestionId);
          }
        }

        this.recordCurrentQuestionTime();
        this.currentQuestionIndex = this.exam.questions.length - 1;
        this.showAnswer = false; // 맨 뒤 문제로 이동 시 정답 숨기기
        this.showExplanation = false; // 맨 뒤 문제로 이동 시 설명 숨기기
        this.solvedStatus = null; // 풀었음/못풀었음 상태 초기화
        this.currentQuestionTimeReactive = 0; // 현재 문제 시간 초기화
        this.startQuestionTimer();
        this.saveSession() // 맨 뒤 문제로 이동 시 세션 저장
        // 새로운 문제의 즐겨찾기 상태 로드
        await this.loadFavoriteStatus();

        this.$nextTick(() => {
          this.$refs.answerInput?.focus()

          // 🚀 문제 이동 완료 후 번역 감지 및 실행
          this.checkAndTriggerTranslation();
        })
      }
    },


    


    async saveExam() {
      // Save 기능: 시험 완료 상태 설정 및 타이머 정지 (페이지 이동 없음)
      this.examCompleted = true;
      this.stopTimer();
      this.saveSession();
      
      try {
        // 현재 문제의 답안이 있으면 answers에 추가 (Pass 버튼으로 설정된 답안)
        if (this.currentQuestion && this.currentAnswer && this.currentAnswer.trim()) {
          const currentQuestionId = this.currentQuestion.id;
          if (currentQuestionId && !this.answers[currentQuestionId]) {
            this.$set(this.answers, currentQuestionId, this.currentAnswer);
            console.log('💾 Save 전 현재 문제 답안 추가:', currentQuestionId, this.currentAnswer);
          }
        }

        // 지금까지 푼 문제들만 수집 (이어풀기 모드에서는 새로 푼 문제들만)
        let answeredQuestions
        if (this.isContinueMode) {
          // 이어풀기 모드: 새로 푼 문제들만
          const newAnswers = Object.keys(this.answers).filter(questionId =>
            !this.answeredQuestions.has(questionId)
          ).map(questionId => ({
            question_id: questionId,
            answer: this.answers[questionId],
            elapsed_seconds: this.questionTimes[this.exam.questions.findIndex(q => q.id === questionId)] || 0
          }))
          answeredQuestions = newAnswers
        } else {
          // 일반 모드: 모든 푼 문제들
          answeredQuestions = Object.keys(this.answers).map(questionId => ({
            question_id: questionId,
            answer: this.answers[questionId],
            elapsed_seconds: this.questionTimes[this.exam.questions.findIndex(q => q.id === questionId)] || 0
          }))
        }
        
        if (answeredQuestions.length === 0) {
          // 푼 문제가 없어도 시험을 저장하고 현재 페이지에 머무름
          this.examCompleted = true
          this.saveSession()

          this.showToastMessage(this.$t('takeExam.examSaved'), 'success')
          return
        }

        // answers에 elapsed_seconds 추가
        answeredQuestions = answeredQuestions.map(answerData => {
          const questionIndex = this.exam.questions.findIndex(q => q.id === answerData.question_id);
          const elapsedSeconds = this.questionTimes[questionIndex] || 0;
          return {
            ...answerData,
            elapsed_seconds: elapsedSeconds
          };
        });

        if (this.isContinueMode) {
          // 이어풀기 모드: 기존 결과에 추가
          await axios.post(`/api/exam/${this.exam.id}/continue/`, {
            previous_result_id: this.previousResultId,
            answers: answeredQuestions,
            elapsed_seconds: this.elapsedSeconds
          })
        } else {
          // 일반 모드: 새 결과 생성
          await axios.post('/api/submit-exam/', {
            exam_id: this.exam.id,
            answers: answeredQuestions,
            elapsed_seconds: this.elapsedSeconds
          })
        }
        
        this.showToastMessage(`${this.$t('takeExam.examSaved')}. ${this.$t('takeExam.correctAnswers', { correct: this.calculateCorrectAnswers(answeredQuestions), total: answeredQuestions.length })}`, 'success')

        // 문제 상태를 서버에 저장
        await this.saveQuestionStatusToServer()

        // Save 버튼으로 저장된 문제들을 추적하기 위해 저장된 문제 ID들을 기록
        this.savedQuestionIds = new Set(answeredQuestions.map(q => q.question_id))
        console.log('💾 Save 버튼으로 저장된 문제들:', Array.from(this.savedQuestionIds))

        // 저장된 문제들의 답안을 answers에서 제거 (초기화)
        answeredQuestions.forEach(q => {
          if (this.answers[q.question_id]) {
            delete this.answers[q.question_id]
          }
        })
        console.log('🧹 Save 후 답안 초기화 완료. 남은 답안:', Object.keys(this.answers))

        // 시험 완료 상태로 세션 저장 (답안 초기화를 위해)
        this.examCompleted = true
        this.saveSession()

        // 홈페이지 캐시 무효화 (진행률 업데이트를 위해)
        try {
          sessionStorage.setItem('forceRefreshHome', 'true')
          localStorage.removeItem('homeData')
          console.log('✅ 홈페이지 캐시 무효화 완료')
        } catch (cacheError) {
          console.warn('⚠️ 홈페이지 캐시 무효화 실패:', cacheError)
        }

        // Save 버튼 후에는 세션을 정리하지 않음 (End 버튼을 위해 유지)

      } catch (error) {
        this.showToastMessage(this.$t('takeExam.alerts.saveFailed'), 'error')
      }
    },

    async exitExam() {
      // completeExam 기능: 시험 완료 상태 설정 및 타이머 정지
      this.examCompleted = true;
      this.stopTimer();
      this.saveSession();

      try {
        // 현재 문제의 답안이 있으면 answers에 추가 (Pass 버튼으로 설정된 답안)
        if (this.currentQuestion && this.currentAnswer && this.currentAnswer.trim()) {
          const currentQuestionId = this.currentQuestion.id;
          if (currentQuestionId && !this.answers[currentQuestionId]) {
            this.$set(this.answers, currentQuestionId, this.currentAnswer);
            console.log('💾 End 전 현재 문제 답안 추가:', currentQuestionId, this.currentAnswer);
          }
        }

        // Save 버튼으로 이미 저장된 문제들을 제외하고 새로 푼 문제들만 수집
        let answeredQuestions
        if (this.isContinueMode) {
          // 이어풀기 모드: 새로 푼 문제들만 (이미 저장된 것 제외)
          const newAnswers = Object.keys(this.answers).filter(questionId =>
            !this.answeredQuestions.has(questionId) && !this.savedQuestionIds.has(questionId)
          ).map(questionId => ({
            question_id: questionId,
            answer: this.answers[questionId],
            elapsed_seconds: this.questionTimes[this.exam.questions.findIndex(q => q.id === questionId)] || 0
          }))
          answeredQuestions = newAnswers
        } else {
          // 일반 모드: Save 버튼 이후에 새로 푼 문제들만
          const newAnswers = Object.keys(this.answers).filter(questionId =>
            !this.savedQuestionIds.has(questionId)
          ).map(questionId => ({
            question_id: questionId,
            answer: this.answers[questionId],
            elapsed_seconds: this.questionTimes[this.exam.questions.findIndex(q => q.id === questionId)] || 0
          }))
          answeredQuestions = newAnswers
        }

        if (answeredQuestions.length === 0) {
          // 새로 푼 문제가 없어도 시험을 종료하고 원래 페이지로 돌아감
          this.examCompleted = true
          this.saveSession()

          // returnTo 값에 따라 즉시 페이지 이동
          const returnTo = this.$route.query.returnTo
          if (returnTo === 'favorites') {
            this.$router.push('/favorites')
            return
          } else if (returnTo === 'exam-detail') {
            // exam-detail 페이지로 이동
            const examId = this.$route.query.examId || this.$route.params.examId
            if (examId) {
              const timestamp = Date.now()
              // 원래 필터 파라미터 사용
              this.$router.push(`/exam-detail/${examId}?t=${timestamp}${this.originalFilterParams ? '&' + this.originalFilterParams : ''}`)
            } else {
              this.$router.push('/exam-management')
            }
            return
          }

          // 원래 시험 상세 페이지로 돌아가기
          const examId = this.$route.query.exam_id || this.$route.params.examId
          // 통계 새로고침을 위해 타임스탬프 추가
          const timestamp = Date.now()
          // 원래 필터 파라미터 사용
          const finalUrl = `/exam-detail/${examId}?t=${timestamp}${this.originalFilterParams ? '&' + this.originalFilterParams : ''}`
          this.$router.push(finalUrl)
          return
        }

        console.log('🔚 End 버튼으로 새로 저장할 문제들:', answeredQuestions.map(q => q.question_id))

        if (this.isContinueMode) {
          // 이어풀기 모드: 기존 결과에 추가
          await axios.post(`/api/exam/${this.exam.id}/continue/`, {
            previous_result_id: this.previousResultId,
            answers: answeredQuestions,
            elapsed_seconds: this.elapsedSeconds
          })
        } else {
          // 일반 모드: 새 결과 생성
          await axios.post('/api/submit-exam/', {
            exam_id: this.exam.id,
            answers: answeredQuestions,
            elapsed_seconds: this.elapsedSeconds
          })
        }

        this.showToastMessage(`${this.$t('takeExam.examEnded')}. ${this.$t('takeExam.correctAnswers', { correct: this.calculateCorrectAnswers(answeredQuestions), total: answeredQuestions.length })}`, 'success')

        // 문제 상태를 서버에 저장
        await this.saveQuestionStatusToServer()

        // 저장된 문제들의 답안을 answers에서 제거 (초기화)
        answeredQuestions.forEach(q => {
          if (this.answers[q.question_id]) {
            delete this.answers[q.question_id]
          }
        })
        console.log('🧹 End 후 답안 초기화 완료. 남은 답안:', Object.keys(this.answers))

        // 시험 완료 상태로 세션 저장 (답안 초기화를 위해)
        this.examCompleted = true
        this.saveSession()

        // 홈페이지 캐시 무효화 (진행률 업데이트를 위해)
        try {
          sessionStorage.setItem('forceRefreshHome', 'true')
          localStorage.removeItem('homeData')
          console.log('✅ 홈페이지 캐시 무효화 완료')
        } catch (cacheError) {
          console.warn('⚠️ 홈페이지 캐시 무효화 실패:', cacheError)
        }

        // 시험 완료 후 returnTo 값에 따라 페이지 이동
        const returnTo = this.$route.query.returnTo
        const examId = this.$route.query.exam_id || this.$route.params.examId
        const timestamp = Date.now()

        if (returnTo === 'favorites') {
          // favorites 페이지로 이동
        this.$router.push('/favorites')
        return // 즉시 함수 종료
        } else if (returnTo === 'exam-detail') {
          // exam-detail 페이지로 이동
          const examId = this.$route.query.examId || this.$route.params.examId
          if (examId) {
            // 원래 필터 파라미터 사용
            this.$router.push(`/exam-detail/${examId}?t=${timestamp}${this.originalFilterParams ? '&' + this.originalFilterParams : ''}`)
          } else {
            this.$router.push('/exam-management')
          }
          return // 즉시 함수 종료
        } else if (returnTo === 'exam-management') {
          // exam-management 페이지로 이동하면서 캐시 무효화
          this.$router.push(`/exam-management?t=${timestamp}${this.originalFilterParams ? '&' + this.originalFilterParams : ''}`)
        } else {
          // 기본값: 해당 시험의 상세 페이지로 이동
          // 원래 필터 파라미터 사용
          const finalUrl = `/exam-detail/${examId}?t=${timestamp}${this.originalFilterParams ? '&' + this.originalFilterParams : ''}`
          this.$router.push(finalUrl)
        }

        // 시험 완료 시 세션 정리 및 캐시 무효화
        this.clearSession()
        this.clearExamRelatedCache()

      } catch (error) {
        this.showToastMessage(this.$t('takeExam.alerts.exitFailed'), 'error')
        this.$router.push('/exam-management')
      }
    },

    calculateCorrectAnswers(answeredQuestions) {
      let correctCount = 0
      for (const answerData of answeredQuestions) {
        const question = this.exam.questions.find(q => q.id === answerData.question_id)
        if (question) {
          // 현재 언어에 맞는 정답 필드 선택
          const correctAnswer = getLocalizedContentWithI18n(question, 'answer', this.$i18n, this.userProfileLanguage, '') || question.answer || '';

          if (correctAnswer.toLowerCase().trim() === answerData.answer.toLowerCase().trim()) {
            correctCount++
          }
        }
      }
      return correctCount
    },
    getCurrentQuestionIdFromRoute() {
      // 실제 문제 id를 URI 등에서 추출하는 로직 (예시: exam.questions[currentQuestionIndex].id)
      // 여기서는 currentQuestion.id와 비교만 하므로 그대로 반환
      return this.currentQuestion?.id
    },
    formatElapsed(sec) {
      const m = Math.floor(sec / 60)
      const s = sec % 60
      return `${m}:${s.toString().padStart(2, '0')}`
    },

    formatQuestionTime(sec) {
      const m = Math.floor(sec / 60)
      const s = sec % 60
      return `${m}:${s.toString().padStart(2, '0')}`
    },

    // 문제 수정 관련 메서드들
    toggleQuestionEdit() {
      if (this.isEditingQuestion) {
        this.cancelQuestionEdit()
      } else {
        this.startQuestionEdit()
      }
    },

    startQuestionEdit() {
      if (!this.currentQuestion) return

      // 편집 폼 업데이트
      this.updateEditingForm()
      this.isEditingQuestion = true
    },

    // 편집 폼 업데이트 (문제 변경 시 호출)
    updateEditingForm() {
      if (!this.currentQuestion) return

      // 사용자 언어에 맞는 필드 값 가져오기 (동적 처리)
      const title = getLocalizedContentWithI18n(this.currentQuestion, 'title', this.$i18n, this.userProfileLanguage, '')
      const content = getLocalizedContentWithI18n(this.currentQuestion, 'content', this.$i18n, this.userProfileLanguage, '')
      const answer = getLocalizedContentWithI18n(this.currentQuestion, 'answer', this.$i18n, this.userProfileLanguage, '')
      const explanation = getLocalizedContentWithI18n(this.currentQuestion, 'explanation', this.$i18n, this.userProfileLanguage, '')

      // 편집 폼 데이터 업데이트
      this.editingQuestion = {
        csv_id: this.currentQuestion.csv_id || '',
        title: title,
        content: content,
        answer: answer,
        explanation: explanation,
        difficulty: this.normalizeDifficulty(this.currentQuestion.difficulty),
        url: this.currentQuestion.url || '',
        group_id: this.currentQuestion.group_id || ''
      }
    },

    async saveQuestionEdit() {
      if (!this.currentQuestion) return

      try {
        // 문제 수정 API 호출 - 항상 실제 UUID를 사용
        const questionId = this.currentQuestion.id

        // explanation 필드가 비어있을 때 공백 문자로 변환 (백엔드에서 빈 값으로 처리)
        const explanationValue = this.editingQuestion.explanation && this.editingQuestion.explanation.trim() !== '' 
          ? this.editingQuestion.explanation 
          : ' '

        const response = await axios.patch(`/api/questions/${questionId}/update/`, {
          csv_id: this.editingQuestion.csv_id,
          title: this.editingQuestion.title,
          content: this.editingQuestion.content,
          answer: this.editingQuestion.answer,
          explanation: explanationValue,
          difficulty: this.normalizeDifficulty(this.editingQuestion.difficulty),
          url: this.editingQuestion.url,
          group_id: this.editingQuestion.group_id
        })

        // 성공 시 현재 문제 데이터 업데이트
        Object.assign(this.currentQuestion, response.data)

        // 수정 모드 종료
        this.isEditingQuestion = false
        this.editingQuestion = {
          csv_id: '',
          title: '',
          content: '',
          answer: '',
          explanation: '',
          difficulty: '',
          url: '',
          group_id: ''
        }

        this.showToastMessage(this.$t('takeExam.questionEditedSuccessfully'), 'success');
      } catch (error) {
        this.showToastMessage(this.$t('takeExam.questionEditError'), 'error');
      }
    },

    cancelQuestionEdit() {
      this.isEditingQuestion = false
      this.editingQuestion = {
        csv_id: '',
        title: '',
        content: '',
        answer: '',
        explanation: '',
        difficulty: '',
        url: '',
        group_id: ''
      }
    },

    // 새 문제 추가 관련 메서드들
    initializeNewQuestion() {
      // 전체 시험 목록에서 최대 csv_id 찾기
      const maxCsvId = Math.max(...this.exam.questions.map(q => parseInt(q.csv_id) || 0), 0)
      this.newQuestion = {
        csv_id: (maxCsvId + 1).toString(),
        title: '',
        content: '',
        answer: '',
        explanation: '',
        difficulty: 'Medium',
        url: '',
        group_id: ''
      }
    },

    async saveNewQuestion() {
      try {
        // 필수 필드 검증
        if (!this.newQuestion.title.trim() || !this.newQuestion.content.trim() || !this.newQuestion.answer.trim()) {
          this.showToastMessage(this.$t('takeExam.requiredFields'), 'warning');
          return
        }

        // 새 문제 저장 API 호출 (백엔드에서 다국어 필드로 변환)
        await axios.post(`/api/exam/${this.exam.id}/add-question/`, {
          csv_id: this.newQuestion.csv_id,
          title: this.newQuestion.title,
          content: this.newQuestion.content,
          answer: this.newQuestion.answer,
          explanation: this.newQuestion.explanation,
          difficulty: this.normalizeDifficulty(this.newQuestion.difficulty),
          url: this.newQuestion.url,
          group_id: this.newQuestion.group_id
        })

        // 저장 성공 후 풀기 모드로 전환
        this.isAddingNewQuestion = false
        await this.loadExam() // 시험 데이터 새로고침

        // 새로 추가된 문제로 이동 (마지막 문제)
        this.currentQuestionIndex = this.exam.questions.length - 1

        this.showToastMessage(this.$t('takeExam.newQuestionAddedSuccessfully'), 'success');

      } catch (error) {
        this.showToastMessage(this.$t('takeExam.newQuestionSaveError'), 'error');
      }
    },

    async saveAndNext() {
      try {
        // 필수 필드 검증
        if (!this.newQuestion.title.trim() || !this.newQuestion.content.trim() || !this.newQuestion.answer.trim()) {
          this.showToastMessage(this.$t('takeExam.requiredFields'), 'warning');
          return
        }

        // 새 문제 저장 API 호출 (백엔드에서 다국어 필드로 변환)
        await axios.post(`/api/exam/${this.exam.id}/add-question/`, {
          csv_id: this.newQuestion.csv_id,
          title: this.newQuestion.title,
          content: this.newQuestion.content,
          answer: this.newQuestion.answer,
          explanation: this.newQuestion.explanation,
          difficulty: this.normalizeDifficulty(this.newQuestion.difficulty),
          url: this.newQuestion.url,
          group_id: this.newQuestion.group_id
        })

        // 저장 성공 후 새 문제 폼 초기화 (풀기 모드로 전환하지 않음)
        await this.loadExam() // 시험 데이터 새로고침

        // 새 문제 폼 초기화 (다음 문제 추가를 위해)
        this.initializeNewQuestion()

        this.showToastMessage(this.$t('takeExam.newQuestionAddedSuccessfully'), 'success');

      } catch (error) {
        this.showToastMessage(this.$t('takeExam.newQuestionSaveError'), 'error');
      }
    },

    cancelNewQuestion() {
      this.isAddingNewQuestion = false
      this.newQuestion = {
        csv_id: '',
        title: '',
        content: '',
        answer: '',
        explanation: '',
        difficulty: '',
        url: '',
        group_id: ''
      }
    },

    // sessionStorage 관련 메서드들
    initializeSession() {
      if (!this.sessionKey) return

      const savedSession = sessionStorage.getItem(this.sessionKey)

      if (savedSession) {
        try {
          const sessionData = JSON.parse(savedSession)



          // URL 파라미터 확인하여 시험 재시작 여부 판단
          const urlParams = new URLSearchParams(window.location.search)
          const restart = urlParams.get('restart')

          // 시험 재시작이 요청된 경우 모든 상태 초기화
          if (restart === 'true') {
            // 모든 상태 초기화
            this.examCompleted = false
            this.currentQuestionIndex = 0
            this.answers = {}
            this.answeredQuestions = new Set()
            this.savedQuestionIds = new Set() // 저장된 문제 ID들도 초기화
            this.elapsedSeconds = 0
            this.questionTimes = []
            this.questionStartTime = null
            this.currentQuestionTimeReactive = 0

            // 타이머 정지
            this.stopTimer()
            if (this.questionTimer) {
              clearInterval(this.questionTimer)
              this.questionTimer = null
            }

            // URL에서 restart 파라미터 제거
            const url = new URL(window.location.href);
            url.searchParams.delete('restart');
            window.history.replaceState({}, '', url.toString());

            // 재시작 후 타이머 초기화
            this.initializeTimers();
            return
          }

          // 세션 데이터 복원
          this.currentQuestionIndex = sessionData.currentQuestionIndex || 0
          this.examCompleted = sessionData.examCompleted || false
          this.elapsedSeconds = sessionData.elapsedSeconds || 0
          this.questionTimes = sessionData.questionTimes || []
          this.isContinueMode = sessionData.isContinueMode || false
          this.previousResultId = sessionData.previousResultId || null
          this.answeredQuestions = new Set(sessionData.answeredQuestions || [])
          this.originalFilterParams = sessionData.originalFilterParams || ''
          this.savedQuestionIds = new Set(sessionData.savedQuestionIds || []) // 저장된 문제 ID들 복원
          this.solvedStatus = sessionData.solvedStatus || null
          this.trackProgress = sessionData.trackProgress !== undefined ? sessionData.trackProgress : true
          this.questionStartTime = sessionData.questionStartTime || null
          this.currentQuestionTimeReactive = sessionData.currentQuestionTimeReactive || 0

          // 답안 복원: 시험이 완료되지 않은 경우에만 복원
          if (!sessionData.examCompleted && sessionData.answers) {
            this.answers = sessionData.answers || {}
          } else {
            this.answers = {} // 시험이 완료되었거나 처음 진입한 경우 답안 초기화
          }

          // currentQuestionIndex가 문제 배열 길이를 초과하면 0으로 리셋
          if (this.exam?.questions && this.currentQuestionIndex >= this.exam.questions.length) {
            this.currentQuestionIndex = 0
          }

          // 이어풀기 모드이고 이전 결과가 있으면 기존 답안들도 복원
          if (this.isContinueMode && this.previousResultId) {
            this.loadPreviousResultFromSession()
          }

          // 세션 복원 후 타이머 초기화
          this.initializeTimers();
        } catch (error) {
          // 에러 처리
        }
      } else {
        this.answers = {}; // 세션이 없으면 답안 초기화

        // 세션이 없는 경우에도 타이머 초기화
        this.initializeTimers();
      }
    },

    // 이어풀기 모드에서 기존 답안들을 세션에서 복원
    async loadPreviousResultFromSession() {
      if (!this.previousResultId) return

      try {
        const response = await axios.get(`/api/exam-result/${this.previousResultId}/`)
        const result = response.data

        // 이미 푼 문제들 수집 (세션에 저장된 답안이 있을 때만 복원)
        for (const detail of result.details) {
          this.answeredQuestions.add(detail.question.id)
          // 세션에 저장된 답안이 있을 때만 복원 (처음 진입 시에는 복원하지 않음)
          const savedSession = sessionStorage.getItem(this.sessionKey)
          if (savedSession) {
            try {
              const sessionData = JSON.parse(savedSession)
              if (sessionData.answers && sessionData.answers[detail.question.id] && !this.answers[detail.question.id]) {
                this.answers[detail.question.id] = sessionData.answers[detail.question.id]
              }
            } catch (e) { /* ignore */ }
          }
        }

      } catch (error) {
        // 에러 처리
      }
    },

    // 첫 번째 문제에 대한 타이머 시작 (세션이 없거나 재시작인 경우)
    initializeTimers() {
      // 새 문제 추가 모드일 때는 타이머 시작하지 않음
      if (this.isAddingNewQuestion) {
        return;
      }

      const savedSession = sessionStorage.getItem(this.sessionKey)
      const urlParams = new URLSearchParams(window.location.search)
      const restart = urlParams.get('restart')

      if (!savedSession || restart === 'true') {
        // 세션이 없거나 재시작인 경우: 모든 타이머 시작
        this.startTimer();
        this.startQuestionTimer();
      } else {
        // 세션이 있는 경우 복원된 시간 정보로 타이머 재시작
        if (this.questionStartTime) {
          // 복원된 시작 시간을 기준으로 현재 시간 계산
          const elapsedSinceStart = Math.floor((Date.now() - this.questionStartTime) / 1000);

          // 복원된 시간이 현재 계산된 시간보다 작으면 현재 시간으로 맞춤
          if (this.currentQuestionTimeReactive < elapsedSinceStart) {
            this.currentQuestionTimeReactive = elapsedSinceStart;
          }

          // 현재 문제 시간이 전체 누적 시간보다 클 수 없음
          if (this.currentQuestionTimeReactive > this.elapsedSeconds) {
            this.currentQuestionTimeReactive = this.elapsedSeconds;
          }
        }

        // 모든 타이머 재시작 (복원된 시간으로부터 계속 진행)
        this.startTimer();
        this.startQuestionTimer();
      }
    },

    saveSession() {
      // 인증되지 않은 사용자는 세션 저장하지 않음
      if (!this.isAuthenticated) {
        return
      }

      if (!this.sessionKey) {
        return
      }

      // 이어풀기 모드에서는 모든 답안을 포함 (기존 + 새로운 답안)
      let answersToSave = { ...this.answers }

      const sessionData = {
        currentQuestionIndex: this.currentQuestionIndex,
        answers: answersToSave,
        examCompleted: this.examCompleted,
        elapsedSeconds: this.elapsedSeconds,
        questionTimes: this.questionTimes,
        isContinueMode: this.isContinueMode,
        previousResultId: this.previousResultId,
        answeredQuestions: Array.from(this.answeredQuestions),
        savedQuestionIds: Array.from(this.savedQuestionIds), // 저장된 문제 ID들 추가
        solvedStatus: this.solvedStatus,
        trackProgress: this.trackProgress,
        questionStartTime: this.questionStartTime,
        currentQuestionTimeReactive: this.currentQuestionTimeReactive,
        originalFilterParams: this.originalFilterParams, // 원래 필터 파라미터 저장
        timestamp: Date.now()
      }

      try {
        sessionStorage.setItem(this.sessionKey, JSON.stringify(sessionData))
      } catch (error) {
        // 에러 처리
      }
    },

    clearSession() {
      if (!this.sessionKey) return
      sessionStorage.removeItem(this.sessionKey)
      // 저장된 문제 ID들도 초기화
      this.savedQuestionIds = new Set()
    },

    clearExamRelatedCache() {
      try {
        // Profile.vue의 캐시 설정에 따라 시험 관련 캐시 정리
        if (isCacheEnabled()) {
          // 시험 관련 모든 캐시 정리
          const keys = Object.keys(sessionStorage)

          keys.forEach(key => {
            if (key.includes('exam') || key.includes('Exam') || key.includes('Management')) {
              removeSessionCache(key)
            }
          })

          // localStorage에서도 시험 관련 캐시 정리
          const localKeys = Object.keys(localStorage)
          localKeys.forEach(key => {
            if (key.includes('exam') || key.includes('Exam') || key.includes('Management')) {
              removeLocalCache(key)
            }
          })

          // 강제 새로고침 플래그 설정
          setSessionCache('forceRefreshExamManagement', true)
          setSessionCache('forceRefreshHome', true)
        } else {
          // 캐시가 비활성화되어 시험 관련 캐시 정리를 건너뜁니다.
        }
      } catch (error) {
        // 에러 처리
      }
    },

    // 목록으로 돌아가기
    goToList() {
      // URL 파라미터 확인하여 적절한 목록 페이지로 이동
      const questionId = this.$route.query.question_id
      const examId = this.$route.query.exam_id || this.$route.params.examId
      const returnTo = this.$route.query.returnTo

      // 로그인한 사용자의 경우에만 세션 저장
      if (this.isAuthenticated) {
        this.saveSession()
      }

      // returnTo 파라미터를 먼저 확인
      if (returnTo === 'favorites') {
        // favorites 페이지로 이동
        this.$router.push('/favorites')
      } else if (returnTo === 'study-detail') {
        const studyId = this.$route.query.studyId
        if (studyId) {
          this.$router.push(`/study-detail/${studyId}`)
        } else {
          this.$router.push('/study-management')
        }
      } else if (returnTo === 'exam-detail') {
        // exam-detail 페이지로 이동
        const examId = this.$route.query.examId || this.$route.params.examId
        if (examId) {
          const timestamp = Date.now()
          // 원래 필터 파라미터 사용
          this.$router.push(`/exam-detail/${examId}?t=${timestamp}${this.originalFilterParams ? '&' + this.originalFilterParams : ''}`)
        } else {
          this.$router.push('/exam-management')
        }
      } else if (returnTo === 'exam-management') {
        // 시험 관리 페이지로 이동 (익명 사용자도 접근 가능)
        const timestamp = Date.now()
        // 원래 필터 파라미터 사용
        this.$router.push(`/exam-management?t=${timestamp}${this.originalFilterParams ? '&' + this.originalFilterParams : ''}`)
      } else {
        // returnTo가 없거나 다른 값인 경우 기존 로직 실행
        // favorite 시험인지 확인 (제목 패턴과 is_original 필드로 확인)
        const examTitle = getLocalizedContentWithI18n(this.exam, 'title', this.$i18n, this.userProfileLanguage, '') || this.exam.title || '';
        if (this.exam && examTitle && this.exam.is_original && (
          examTitle.includes("'s favorite") ||
          examTitle.includes('Favorite Exam') ||
          examTitle.includes('favorite exam') ||
          examTitle.includes('favorites')
        )) {
          // favorite 시험에서 온 경우: favorite 페이지로 이동
          this.$router.push('/favorites')
        } else if (questionId && examId) {
          // 단일 문제 풀기 모드: 해당 시험 상세 페이지로 이동
          const timestamp = Date.now()
          // 원래 필터 파라미터 사용
          this.$router.push(`/exam-detail/${examId}?t=${timestamp}${this.originalFilterParams ? '&' + this.originalFilterParams : ''}`)
        } else if (examId) {
          // 시험 ID가 있으면 해당 시험 상세 페이지로 이동
          const timestamp = Date.now()
          // 원래 필터 파라미터 사용
          this.$router.push(`/exam-detail/${examId}?t=${timestamp}${this.originalFilterParams ? '&' + this.originalFilterParams : ''}`)
        } else {
          // 기본: 해당 시험의 상세 페이지로 이동
          const timestamp = Date.now()
          // 원래 필터 파라미터 사용
          this.$router.push(`/exam-detail/${this.exam.id}?t=${timestamp}${this.originalFilterParams ? '&' + this.originalFilterParams : ''}`)
        }
      }
    },

    async deleteCurrentQuestion() {
      if (!this.currentQuestion) return;

      // 모던한 삭제 확인 다이얼로그 표시
      this.questionToDelete = this.currentQuestion;
      this.showDeleteConfirm = true;
    },

    cancelDelete() {
      this.showDeleteConfirm = false;
      this.questionToDelete = null;
    },

    async confirmDelete() {
      if (!this.questionToDelete) return;

      try {
        const questionId = this.questionToDelete.id;
        await axios.delete(`/api/questions/${questionId}/`);
        this.showToastMessage(this.$t('takeExam.questionDeletedSuccessfully'), 'success');
        this.showDeleteConfirm = false;
        this.questionToDelete = null;

        // 삭제된 문제를 시험에서 제거
        const deletedIndex = this.exam.questions.findIndex(q => q.id === questionId);
        if (deletedIndex !== -1) {
          this.exam.questions.splice(deletedIndex, 1);

          // 현재 문제 인덱스 조정
          if (this.currentQuestionIndex >= this.exam.questions.length) {
            // 현재 문제가 마지막 문제였으면 이전 문제로 이동
            this.currentQuestionIndex = Math.max(0, this.exam.questions.length - 1);
          }

          // 문제가 더 이상 없으면 목록으로 이동
          if (this.exam.questions.length === 0) {
            this.goToList();
            return;
          }

          // 다음 문제의 favorite 상태 로드
          this.loadFavoriteStatus();
        }
      } catch (error) {
        this.showToastMessage(this.$t('takeExam.questionDeleteError'), 'error');
        this.showDeleteConfirm = false;
        this.questionToDelete = null;
      }
    },





    async loadQuestionStatistics(examId) {
      try {
        const response = await axios.get(`/api/exam/${examId}/question-statistics/`)
        this.questionStatistics = response.data

        // 현재 문제의 정확도로 targetAccuracyPercentage 초기화
        this.$nextTick(() => {
          if (this.currentQuestionStats) {
            this.targetAccuracyPercentage = this.currentAccuracyPercentage
          }
        })
      } catch (error) {
        this.questionStatistics = []
      }
    },

    // 통계 정보를 문제 데이터에 매핑하는 메서드
    mapStatisticsToQuestions() {
      if (this.questionStatistics && this.exam && this.exam.questions) {
        this.exam.questions.forEach(question => {
          const stats = this.questionStatistics.find(s => s.question_id === question.id)
          if (stats) {
            question.attempt_count = stats.total_attempts || 0
            question.correct_count = stats.correct_attempts || 0
          } else {
            question.attempt_count = 0
            question.correct_count = 0
          }
        })
        
        // 통계 매핑 후 우선순위 정렬 및 정확도별 그룹화된 랜덤 순서 적용
        console.log('🔍 통계 매핑 후 문제 정렬 시작:', {
          questionsLength: this.exam.questions.length,
          currentQuestionIndex: this.currentQuestionIndex
        })
        
        this.sortQuestionsByPriority()
        this.shuffleQuestionsByAccuracyGroups()
        
        console.log('🔍 통계 매핑 후 문제 정렬 완료:', {
          questionsLength: this.exam.questions.length,
          currentQuestionIndex: this.currentQuestionIndex,
          currentQuestion: this.exam.questions[this.currentQuestionIndex]
        })
      }
    },





    // 문제를 우선순위에 따라 정렬하는 메서드
    sortQuestionsByPriority() {
      if (!this.exam || !this.exam.questions) return

      console.log('🔍 우선순위 정렬 시작:')
      console.log('정렬 전 첫 3개 문제:')
      this.exam.questions.slice(0, 3).forEach((q, i) => {
        console.log(`  문제 ${i+1}: ID=${q.id}, 시도=${q.attempt_count || 0}, 정답=${q.correct_count || 0}`)
      })

      this.exam.questions.sort((a, b) => {
        // 시도횟수와 정답 횟수 추출 (기본값 0)
        const aAttempts = a.attempt_count || 0
        const bAttempts = b.attempt_count || 0
        const aCorrect = a.correct_count || 0
        const bCorrect = b.correct_count || 0

        // 1. 정확도가 낮은 것 먼저 (예: 0/2 -> 0/1 -> 1/3)
        const aAccuracy = aAttempts > 0 ? aCorrect / aAttempts : 0
        const bAccuracy = bAttempts > 0 ? bCorrect / bAttempts : 0

        if (aAccuracy !== bAccuracy) {
          const result = aAccuracy - bAccuracy
          console.log(`정확도 비교: ${aAccuracy} vs ${bAccuracy} -> ${result > 0 ? 'b가 먼저' : 'a가 먼저'}`)
          return result
        }

        // 2. 정확도가 같은 경우 시도 횟수가 많은 것을 우선 (0/2가 0/1보다 먼저)
        if (aAttempts !== bAttempts) {
          const result = bAttempts - aAttempts  // 내림차순 (많은 것이 먼저)
          console.log(`시도횟수 비교: ${aAttempts} vs ${bAttempts} -> ${result > 0 ? 'b가 먼저' : 'a가 먼저'}`)
          return result
        }

        // 3. 시도 횟수도 같은 경우 시도가 0인 것을 우선
        if (aAttempts === 0 && bAttempts > 0) {
          console.log(`시도 0 우선: a(시도=0) vs b(시도=${bAttempts}) -> a가 먼저`)
          return -1
        }
        if (aAttempts > 0 && bAttempts === 0) {
          console.log(`시도 0 우선: a(시도=${aAttempts}) vs b(시도=0) -> b가 먼저`)
          return 1
        }

        // 모든 조건이 같은 경우 원래 순서 유지
        console.log(`모든 조건 동일: 원래 순서 유지`)
        return 0
      })

      console.log('정렬 후 첫 3개 문제:')
      this.exam.questions.slice(0, 3).forEach((q, i) => {
        console.log(`  문제 ${i+1}: ID=${q.id}, 시도=${q.attempt_count || 0}, 정답=${q.correct_count || 0}`)
      })
    },

    // 문제를 전달받은 순서대로 정렬하는 메서드
    sortQuestionsByOrder(orderParam) {
      if (!this.exam || !this.exam.questions) return

      const orderIds = orderParam.split(',')

      // orderIds의 순서대로 문제를 정렬
      this.exam.questions.sort((a, b) => {
        const aIndex = orderIds.indexOf(a.id)
        const bIndex = orderIds.indexOf(b.id)

        // orderIds에 없는 문제는 맨 뒤로
        if (aIndex === -1 && bIndex === -1) return 0
        if (aIndex === -1) return 1
        if (bIndex === -1) return -1

        // orderIds의 순서대로 정렬
        return aIndex - bIndex
      })
    },

    // 새로운 모던 UI 메서드들
    async shareExam() {
      // 현재 URL 사용 (take-exam 페이지의 URL)
      const originalUrl = window.location.href
      
      // 단축 URL 생성
      try {
        const response = await axios.post('/api/short-url/create/', {
          url: originalUrl,
          expires_days: 30
        })
        this.shareUrl = response.data.short_url
      } catch (error) {
        debugLog('단축 URL 생성 실패:', error, 'error')
        // 단축 URL 생성 실패 시 원본 URL 사용
        this.shareUrl = originalUrl
      }
      
      this.showShareModal = true
    },
    
    // 공유 모달 닫기
    closeShareModal() {
      this.showShareModal = false
      this.shareUrl = ''
    },

    showHint() {
      // 힌트 표시 (Answer와 Explanation을 보여줌)
      const currentLanguage = this.$i18n.locale;

      // 현재 언어에 따른 answer와 explanation 확인
      const hasAnswer = this.currentQuestion && getLocalizedContentWithI18n(this.currentQuestion, 'answer', this.$i18n, this.userProfileLanguage, '');
      const hasExplanation = this.currentQuestion && getLocalizedContentWithI18n(this.currentQuestion, 'explanation', this.$i18n, this.userProfileLanguage, '');

      if (hasAnswer || hasExplanation) {
        this.showAnswer = !this.showAnswer
        // Explanation이 있으면 함께 표시
        if (hasExplanation) {
          this.showExplanation = this.showAnswer
        }
      } else {
        // 번역이 필요한 경우 안내
        if (!hasAnswer || !hasExplanation) {
          const message = currentLanguage === 'en' 
            ? 'Answer and explanation are not yet translated to English. Please try again later or contact an administrator.'
            : 'La respuesta y la explicación aún no están traducidas al español. Por favor, inténtalo más tarde o contacta a un administrador.';
          this.$toast?.error?.(message);
        } else {
          this.$toast?.error?.('No hint available for this question.');
        }
      }
    },

    toggleDetails() {
      // 상세 정보 토글
      this.showDetails = !this.showDetails
    },

    editQuestion() {
      // 문제 수정 모드 시작
      this.toggleQuestionEdit()
    },

    // 공통 상태 저장 (End 버튼 시 호출)
    async saveQuestionStatusToServer() {
      try {
        // localStorage에서 즐겨찾기 상태 로드
        const favoriteQuestions = JSON.parse(localStorage.getItem('favoriteQuestions') || '[]');

        if (favoriteQuestions.length === 0) {
          return;
        }

        // 각 즐겨찾기 문제를 서버에 저장
        for (const questionId of favoriteQuestions) {
          try {
            await axios.post('/api/add-question-to-favorite/', {
              question_id: questionId
            });
          } catch (error) {
            // 개별 실패는 로그만 남기고 계속 진행
          }
        }

        // localStorage 정리 (서버에 저장 완료 후)
        localStorage.removeItem('favoriteQuestions');

      } catch (error) {
        // 즐겨찾기 저장 실패는 시험 제출을 막지 않음
      }
    },

    // 공통 상태 관리 유틸리티
    async toggleQuestionStatus(statusType) {
      if (!this.currentQuestion) {
        this.showToastMessage(this.$t('takeExam.noQuestionInfo'), 'warning');
        return;
      }

      // 세션이 없으면 기능 비활성화
      if (!this.isAuthenticated) {
        this.showToastMessage('로그인이 필요한 기능입니다.', 'warning');
        return;
      }

      try {
        const questionId = this.currentQuestion.id;
        let response;

        if (statusType === 'favorite') {
          // 즐겨찾기 토글
          response = await axios.post('/api/add-question-to-favorite/', {
            question_id: questionId
          });

          // 응답으로 상태 확인
          this.isFavorited = response.data.is_favorite || false;

          // 즉시 로컬 상태 업데이트
          this.showToastMessage(
            this.isFavorited
              ? this.$t('takeExam.questionAddedToFavorite')
              : this.$t('takeExam.removedFromFavorite'),
            this.isFavorited ? 'success' : 'info'
          );
        } else if (statusType === 'ignore') {
          // 무시하기 토글
          response = await axios.post(`/api/question/${questionId}/ignore/`);

          // 응답으로 상태 확인
          const isIgnored = response.data.is_ignored || false;

          // 로컬 상태 업데이트
          if (isIgnored) {
            this.ignoredQuestions = new Set([...this.ignoredQuestions, String(questionId)]);
          } else {
            const newIgnoredQuestions = new Set(this.ignoredQuestions);
            newIgnoredQuestions.delete(String(questionId));
            this.ignoredQuestions = newIgnoredQuestions;
          }

          this.showToastMessage(
            isIgnored
              ? this.$t('takeExam.questionIgnored')
              : this.$t('takeExam.questionUnignored'),
            isIgnored ? 'info' : 'success'
          );
        }

        // 서버 상태 동기화
        await this.refreshQuestionStatus(statusType);

      } catch (error) {
        // 공통 에러 처리 사용
        if (statusType === 'favorite') {
          // 실패 시 상태 되돌리기
          this.handleQuestionStatusError(error, statusType, () => {
            this.isFavorited = !this.isFavorited;
          });
        } else {
          this.handleQuestionStatusError(error, statusType);
        }
      }
    },

    // 공통 상태 새로고침
    async refreshQuestionStatus(statusType) {
      try {
        if (statusType === 'favorite') {
          await this.loadFavoriteStatus();
        } else if (statusType === 'ignore') {
          await this.loadIgnoredQuestions();
        }
      } catch (error) {
        // 에러 처리
      }
    },

    // 공통 에러 처리 유틸리티
    handleQuestionStatusError(error, statusType, fallbackAction = null) {

      const errorMessage = statusType === 'favorite'
        ? '즐겨찾기 상태 변경에 실패했습니다.'
        : '무시 상태 변경에 실패했습니다.';

      this.showToastMessage(errorMessage, 'error');

      // fallback 액션이 있으면 실행
      if (fallbackAction && typeof fallbackAction === 'function') {
        fallbackAction();
      }
    },

    // 즐겨찾기 상태 로드
    async loadFavoriteStatus() {
      debugLog('=== TakeExam.loadFavoriteStatus 호출 ===', {
        routePath: this.$route.path,
        currentQuestionId: this.currentQuestion?.id,
        isAuthenticated: this.isAuthenticated,
        timestamp: Date.now()
      })
      
      if (!this.currentQuestion) {
        debugLog('=== TakeExam.loadFavoriteStatus 건너뜀 - currentQuestion 없음 ===')
        return;
      }
      
      // 세션이 없으면 즐겨찾기 기능 비활성화
      if (!this.isAuthenticated) {
        debugLog('=== TakeExam.loadFavoriteStatus 건너뜀 - 인증되지 않음 ===')
        this.isFavorited = false;
        return;
      }

      try {
        // 강력한 캐시 무효화를 위한 여러 파라미터 추가
        debugLog('=== TakeExam에서 favorite-exam-questions API 호출 ===', {
          questionId: this.currentQuestion.id,
          timestamp: Date.now()
        })
        const response = await axios.get('/api/favorite-exam-questions/', {
          params: {
            t: Date.now(),
            _: Math.random(), // 추가 랜덤 값
            question_id: this.currentQuestion.id // 현재 문제 ID 추가
          }
        });

        const favoriteQuestions = response.data.questions || [];

        // ID 타입을 문자열로 통일하여 비교
        const currentQuestionIdStr = String(this.currentQuestion.id);

        // API 응답에서 해당 문제의 is_favorite 상태를 확인
        const currentQuestion = favoriteQuestions.find(q => String(q.id) === currentQuestionIdStr);
        this.isFavorited = currentQuestion ? currentQuestion.is_favorite : false;

        // 실제 favorite 문제 수 계산 (사용되지 않음)
      } catch (error) {
        this.isFavorited = false;
      }
    },

    // 무시된 문제 목록 로드
    async loadIgnoredQuestions() {
      // 세션이 없으면 무시된 문제 기능 비활성화
      if (!this.isAuthenticated) {
        this.ignoredQuestions = new Set();
        return;
      }
      
      try {
        const response = await axios.get('/api/questions/ignored/');

        this.ignoredQuestions = new Set(
          response.data.ignored_questions.map(item => String(item.question_id))
        );
      } catch (error) {
        this.ignoredQuestions = new Set();
      }
    },

    // 즐겨찾기 토글 (통합 메서드 사용)
    async toggleFavorite() {
      await this.toggleQuestionStatus('favorite');
    },

    // 무시하기 토글 (통합 메서드 사용)
    async toggleIgnore() {
      await this.toggleQuestionStatus('ignore');
    },

    shuffleQuestions() {
      // 문제 순서 섞기 (정확도별 그룹화 후 각 그룹 내에서 랜덤)
      if (this.exam && this.exam.questions) {
        this.shuffleQuestionsByAccuracyGroups()
        this.currentQuestionIndex = 0
        this.showToastMessage(this.$t('takeExam.questionsShuffledByAccuracy'), 'info')
      }
    },

    // 정확도별로 그룹화하여 각 그룹 내에서 랜덤하게 섞는 메서드
    shuffleQuestionsByAccuracyGroups() {
      if (!this.exam || !this.exam.questions) return

      console.log('🔍 셔플 전 문제 상태:')
      console.log('첫 번째 문제 전체 데이터:', this.exam.questions[0])
      this.exam.questions.slice(0, 5).forEach((q, i) => {
        console.log(`문제 ${i+1}: ID=${q.id}, 시도=${q.attempt_count || 0}, 정답=${q.correct_count || 0}`)
        console.log(`  전체 필드:`, Object.keys(q))
        console.log(`  시도 관련 필드들:`, {
          attempt_count: q.attempt_count,
          total_attempts: q.total_attempts,
          attempts: q.attempts
        })
        console.log(`  정답 관련 필드들:`, {
          correct_count: q.correct_count,
          correct_attempts: q.correct_attempts,
          correct: q.correct
        })
      })

      // 1. 먼저 우선순위에 따라 정렬 (정확도 순서 유지)
      this.sortQuestionsByPriority()
      
      console.log('🔍 우선순위 정렬 후 문제 상태:')
      this.exam.questions.slice(0, 5).forEach((q, i) => {
        console.log(`문제 ${i+1}: ID=${q.id}, 시도=${q.attempt_count || 0}, 정답=${q.correct_count || 0}`)
      })

      // 2. 정확도와 시도횟수를 고려한 그룹화
      const priorityGroups = new Map()
      
      this.exam.questions.forEach(question => {
        const attempts = question.attempt_count || 0
        const correct = question.correct_count || 0
        const accuracy = attempts > 0 ? correct / attempts : 0
        
        // 그룹화 키: 정확도 + 시도횟수 정보
        // 예: 0% 정확도라도 시도횟수가 다르면 다른 그룹
        let groupKey
        if (attempts === 0) {
          // 안 픈 문제 (0/0) - 별도 그룹
          groupKey = 'unattempted'
        } else if (accuracy === 0) {
          // 틀린 문제 (0/N) - 시도횟수별 그룹
          groupKey = `wrong_${attempts}`
        } else if (accuracy === 1) {
          // 맞춘 문제 (N/N) - 시도횟수별 그룹
          groupKey = `correct_${attempts}`
        } else {
          // 부분적으로 맞춘 문제 (M/N) - 정확도별 그룹
          groupKey = `partial_${Math.round(accuracy * 1000) / 1000}`
        }
        
        if (!priorityGroups.has(groupKey)) {
          priorityGroups.set(groupKey, [])
        }
        priorityGroups.get(groupKey).push(question)
      })

      console.log('🔍 그룹화 결과:')
      priorityGroups.forEach((questions, groupKey) => {
        console.log(`그룹 ${groupKey}: ${questions.length}개 문제`)
        if (questions.length <= 3) {
          questions.forEach(q => {
            console.log(`  - ID=${q.id}, 시도=${q.attempt_count || 0}, 정답=${q.correct_count || 0}`)
          })
        }
      })

      // 3. 실제 존재하는 그룹들을 우선순위에 따라 정렬하여 처리
      const shuffledQuestions = []
      
      // 그룹 우선순위 정의 (정확도 낮은 순서)
      const getGroupPriority = (groupKey) => {
        if (groupKey.startsWith('wrong_')) return 1
        if (groupKey === 'unattempted') return 2
        if (groupKey.startsWith('partial_')) return 3
        if (groupKey.startsWith('correct_')) return 4
        return 5 // 기타 그룹은 마지막
      }
      
      // 실제 존재하는 그룹들을 우선순위에 따라 정렬
      const sortedGroups = Array.from(priorityGroups.keys()).sort((a, b) => {
        const priorityA = getGroupPriority(a)
        const priorityB = getGroupPriority(b)
        
        if (priorityA !== priorityB) {
          return priorityA - priorityB
        }
        
        // 같은 우선순위 내에서는 그룹 이름으로 정렬 (안정적 정렬)
        return a.localeCompare(b)
      })
      
      console.log('🔍 정렬된 그룹 순서:', sortedGroups)
      
      sortedGroups.forEach(groupKey => {
        const group = priorityGroups.get(groupKey)
        
        console.log(`🔍 그룹 ${groupKey} 처리 중: ${group.length}개 문제`)
        
        // 그룹 내에서 랜덤하게 섞기
        const shuffledGroup = [...group]
        for (let i = shuffledGroup.length - 1; i > 0; i--) {
          const j = Math.floor(Math.random() * (i + 1))
          ;[shuffledGroup[i], shuffledGroup[j]] = [shuffledGroup[j], shuffledGroup[i]]
        }
        
        shuffledQuestions.push(...shuffledGroup)
      })
      
      console.log('🔍 최종 섞인 문제 상태:')
      console.log(`🔍 총 문제 수: 원본 ${this.exam.questions.length}개 -> 섞인 ${shuffledQuestions.length}개`)
      
      if (shuffledQuestions.length !== this.exam.questions.length) {
        console.error('🔍 경고: 문제 수가 일치하지 않음!', {
          original: this.exam.questions.length,
          shuffled: shuffledQuestions.length,
          missing: this.exam.questions.length - shuffledQuestions.length
        })
      }
      
      shuffledQuestions.slice(0, 5).forEach((q, i) => {
        console.log(`문제 ${i+1}: ID=${q.id}, 시도=${q.attempt_count || 0}, 정답=${q.correct_count || 0}`)
      })
      
      // 4. 섞인 문제들로 교체 (Vue 반응성 유지)
      console.log('🔍 섞인 문제 교체 전:', {
        originalLength: this.exam.questions.length,
        shuffledLength: shuffledQuestions.length,
        currentQuestionIndex: this.currentQuestionIndex
      })
      
      // 섞인 문제가 비어있지 않은 경우에만 교체
      if (shuffledQuestions.length > 0) {
        this.$set(this.exam, 'questions', shuffledQuestions)
        
        console.log('🔍 섞인 문제 교체 후:', {
          newLength: this.exam.questions.length,
          currentQuestionIndex: this.currentQuestionIndex,
          currentQuestion: this.exam.questions[this.currentQuestionIndex]
        })
      } else {
        console.warn('🔍 섞인 문제가 비어있어서 교체하지 않음')
      }
    },

    toggleFullscreen() {
      // 전체화면 토글
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen()
        this.isFullscreen = true
      } else {
        document.exitFullscreen()
        this.isFullscreen = false
      }
    },


    onAccuracySliderChange(event) {
      // DOM에서 직접 값을 가져와서 targetAccuracyPercentage 업데이트
      this.targetAccuracyPercentage = parseInt(event.target.value)
    },

    onAccuracySliderMouseUp(event) {
      // DOM에서 직접 최종 값을 가져와서 targetAccuracyPercentage 업데이트
      const finalValue = parseInt(event.target.value)
      this.targetAccuracyPercentage = finalValue

      // 백엔드 업데이트
      this.applyAccuracyAdjustment()
    },



    // AI Mock Interview 관련 메서드
    async showAIMockInterviewDetail() {
      debugLog('🎤 [showAIMockInterviewDetail] 시작', {
        examId: this.examId,
        examTitle: this.exam?.title
      })
      
      this.selectedQuestionForAI = this.exam
      
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
      
      // 웹 환경: exam-detail로 라우팅
      debugLog('🎤 [showAIMockInterviewDetail] 웹 환경 감지됨 → exam-detail로 라우팅')
      this.$router.push(`/exam-detail/${this.examId}?t=${Date.now()}&returnTo=take-exam`)
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
     * 모바일 디바이스 감지 (User-Agent 기반)
     */
    checkIsMobileDevice() {
      debugLog('📱 [checkIsMobileDevice] 모바일 감지 시작')
      
      if (typeof window === 'undefined' || typeof navigator === 'undefined') {
        debugLog('📱 [checkIsMobileDevice] window 또는 navigator가 undefined → false 반환')
        return false
      }
      
      // User-Agent로 모바일 감지
      const userAgent = navigator.userAgent || ''
      const isMobileUA = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(userAgent)
      if (isMobileUA) {
        debugLog('📱 [checkIsMobileDevice] ✅ User-Agent로 모바일 감지됨 → true 반환')
      }
      return isMobileUA
    },
    
    async initializePromptText() {
      if (this.selectedQuestionForAI || this.exam) {
        // watch가 트리거되지 않도록 플래그 설정
        this.isInitializingPrompt = true
        
        // 시험의 문제들을 가져와서 프롬프트에 포함
        const questionsText = this.getQuestionsTextForPrompt()
        const currentLang = this.currentLanguage
        
        // 공통 유틸리티를 사용하여 필수 규칙 및 템플릿 로드
        const [mandatoryRulesData, template] = await Promise.all([
          loadMandatoryRules(currentLang),
          loadInterviewPromptTemplate(currentLang)
        ])
        const { languageInstruction, mandatoryRules } = mandatoryRulesData
        
        // 공통 유틸리티를 사용하여 프롬프트 생성
        const promptText = buildInterviewPrompt({
          language: currentLang,
          questionsText,
          languageInstruction,
          mandatoryRules,
          template
        })
        
        this.interviewPromptText = promptText
        
        // 플래그 해제
        this.$nextTick(() => {
          this.isInitializingPrompt = false
        })
      }
    },
    
    getQuestionsTextForPrompt() {
      // exam의 questions 배열 사용
      if (!this.exam || !this.exam.questions || this.exam.questions.length === 0) {
        const currentLang = this.currentLanguage
        if (currentLang === 'en') {
          return 'Unable to load question information.'
        } else if (currentLang === 'zh') {
          return '无法加载问题信息。'
        } else if (currentLang === 'es') {
          return 'No se puede cargar la información de la pregunta.'
        } else if (currentLang === 'ja') {
          return '問題情報を読み込めません。'
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
      } else if (currentLang === 'ja') {
        titleLabel = 'タイトル'
        answerLabel = '回答'
        explanationLabel = '説明'
        noTitle = 'タイトルなし'
        noAnswer = '回答なし'
      } else {
        titleLabel = '제목'
        answerLabel = '답변'
        explanationLabel = '설명'
        noTitle = '제목 없음'
        noAnswer = '답변 없음'
      }

      return this.exam.questions.map((question, index) => {
        // 현재 언어에 맞는 제목과 답변 가져오기
        let title = question.localized_title
        let answer = question.localized_answer
        let explanation = question.localized_explanation
        
        // localized 필드가 없으면 직접 다국어 필드 확인
        if (!title) {
          title = getLocalizedContentWithI18n(question, 'title', this.$i18n, this.userProfileLanguage, noTitle) || question.title || noTitle
        }
        
        if (!answer) {
          answer = getLocalizedContentWithI18n(question, 'answer', this.$i18n, this.userProfileLanguage, noAnswer) || question.answer || noAnswer
        }
        
        if (!explanation) {
          explanation = getLocalizedContentWithI18n(question, 'explanation', this.$i18n, this.userProfileLanguage, '') || question.explanation || ''
        }
        
        // 여전히 없으면 기본값 사용
        title = title || noTitle
        answer = answer || noAnswer

        let questionText = `${index + 1}. ${titleLabel}: ${title}
  ${answerLabel}: ${answer}`
        
        // explanation이 있고 빈 값이 아닌 경우에만 설명 라인 추가
        if (explanation && explanation.trim()) {
          questionText += `\n  ${explanationLabel}: ${explanation}`
        }

        return questionText
      }).join('\n\n')
    },
    
    handleInterviewEnded() {
      debugLog('🎤 [handleInterviewEnded] 인터뷰 종료 처리 시작')
      this.hideAIMockInterviewModal()
      debugLog('🎤 [handleInterviewEnded] 인터뷰 종료 처리 완료')
    },
    
    handleSessionCreated(sessionData) {
      debugLog('🎤 [handleSessionCreated] 세션 생성됨:', sessionData)
    },

    async applyAccuracyAdjustment() {
      if (!this.currentQuestionStats || !this.currentQuestion || !this.exam) {
        return;
      }

      // 목표 정확도가 현재 정확도와 같으면 조정하지 않음
      if (this.targetAccuracyPercentage === this.currentAccuracyPercentage) {
        return;
      }

      this.isAdjustingAccuracy = true;

      try {
        // 목표 정확도에 맞는 correct_attempts 계산
        const targetCorrectAttempts = Math.round((this.targetAccuracyPercentage / 100) * this.currentQuestionStats.total_attempts);
        const currentCorrectAttempts = this.currentQuestionStats.correct_attempts;
        const difference = targetCorrectAttempts - currentCorrectAttempts;

        // 조정 타입 결정 (한 번만 호출)
        const adjustmentType = difference > 0 ? 'clear' : 'ambiguous';

        const response = await axios.post('/api/adjust-question-accuracy/', {
          question_id: this.currentQuestion.id,
          exam_id: this.exam.id,
          adjustment_type: adjustmentType
        });

        if (!response.data.success) {
          this.showToastMessage(this.$t('takeExam.accuracyAdjustment.failed'), 'error');
          return;
        }

        // 최종 통계 다시 로드
        await this.loadQuestionStatistics(this.exam.id);

        // 프론트엔드 동기화
        const finalAccuracy = this.currentAccuracyPercentage;
        this.targetAccuracyPercentage = finalAccuracy;

        // 슬라이더 값도 최종 결과로 동기화
        if (this.$refs.accuracySlider) {
          this.$refs.accuracySlider.value = finalAccuracy;
        }

        // 백엔드에서 번역 키를 반환하는 경우 처리
        if (response.data.message && response.data.message_params) {
          this.showToastMessage(this.$t(response.data.message, response.data.message_params), 'success');
        } else {
          // 성공 메시지 표시
          this.showToastMessage(this.$t('takeExam.accuracyAdjustment.success', { accuracy: finalAccuracy }), 'success');
        }

      } catch (error) {
        this.showToastMessage(this.$t('takeExam.accuracyAdjustment.error'), 'error');
      } finally {
        this.isAdjustingAccuracy = false;
      }
    },
  }
}
</script>

<style scoped>
/* Toast Notifications - 기본 스타일은 공통 CSS (mobile-buttons.css)에 정의됨 */

/* 타입별 스타일은 공통 CSS (mobile-buttons.css)에 정의됨 */

.toast-content {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.toast-content i {
  font-size: 18px;
}

.toast-close {
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  padding: 5px;
  border-radius: 50%;
  transition: background-color 0.2s;
}

.toast-close:hover {
  background: rgba(0, 0, 0, 0.1);
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

/* Modern TakeExam Styles */
.take-exam-modern {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.loading-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100vh;
  gap: 20px;
}

.translation-message {
  text-align: center;
  max-width: 450px;
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  animation: fadeInUp 0.5s ease-out;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  backdrop-filter: blur(10px);
}

.translation-info {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  font-size: 18px;
  font-weight: 600;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.translation-detail {
  font-size: 14px;
  line-height: 1.5;
  color: rgba(255, 255, 255, 0.9);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.exam-container {
  max-width: 1200px;
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

@media (max-width: 768px) {
  .top-header {
    padding-top: 0;
    padding-bottom: 0;
  }
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

.action-btn:hover {
  background: #007bff;
  color: white;
  border-color: #007bff;
  transform: translateY(-2px);
}

.action-btn.active {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

.action-btn.active:hover {
  background: #0056b3;
  border-color: #0056b3;
}

.action-label {
  font-size: 12px;
  font-weight: 500;
}

/* Page Title */
.page-title {
  padding: 15px 30px 10px 30px; /* 상단 20px → 15px, 하단 20px → 10px로 감소 */
  background: white;
  border-bottom: 1px solid #e9ecef;
  /* 데스크톱에서는 기본 레이아웃 (버튼이 아래로) */
}

.page-title h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  color: #2c3e50;
}

/* 데스크톱에서 page-title-btn 숨기기 (모바일에서만 표시) */
.page-title .page-title-btn {
  display: none;
}



/* Question Card */
.question-card {
  padding: 15px;
  background: white;
}

@media (max-width: 768px) {
  .question-card {
    padding-bottom: 5px;
    padding-top: 5px;
  }
}

.card-header-modern {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px; /* 30px → 20px로 감소 */
  padding-bottom: 15px; /* 20px → 15px로 감소 */
  border-bottom: 1px solid #e9ecef;
}

@media (max-width: 768px) {
  .card-header-modern {
    padding-top: 5px;
    padding-bottom: 5px;
  }
}

.question-info {
  display: flex;
  align-items: center;
  gap: 15px;
  position: relative;
}

.hint-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border: 1px solid #e9ecef;
  border-radius: 20px;
  background: white;
  color: #6c757d;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.hint-btn:hover {
  background: #f8f9fa;
  border-color: #007bff;
  color: #007bff;
}

.question-meta {
  display: flex;
  gap: 10px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 8px;
  background: #f8f9fa;
  border-radius: 12px;
  font-size: 12px;
  color: #6c757d;
}

.meta-item i {
  font-size: 10px;
  color: #007bff;
}

.difficulty-easy {
  background: #d4edda;
  color: #155724;
}

.difficulty-easy i {
  color: #28a745;
}

.difficulty-medium {
  background: #fff3cd;
  color: #856404;
}

.difficulty-medium i {
  color: #ffc107;
}

.difficulty-hard {
  background: #f8d7da;
  color: #721c24;
}

.difficulty-hard i {
  color: #dc3545;
}

.card-actions {
  display: flex;
  gap: 10px;
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
  border-color: #007bff;
}

.card-action-btn .favorited {
  color: #ffc107;
}

.card-action-btn .action-label {
  font-size: 11px;
  font-weight: 500;
}

/* Question Content */
.question-content-modern {
  margin-bottom: 10px; /* 20px → 15px로 감소 */
}

.question-text {
  font-size: 20px;
  line-height: 1.6;
  color: #2c3e50;
  margin-bottom: 20px;
  white-space: pre-wrap;
}

.question-link {
  color: #007bff;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s;
  cursor: pointer;
}

.question-link:hover {
  color: #0056b3;
  text-decoration: underline;
}

.question-url {
  margin-bottom: 20px;
  padding: 12px 16px;
  background: #e3f2fd;
  border-radius: 8px;
  border: 1px solid #bbdefb;
}

.url-link {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #1976d2;
  text-decoration: none;
  font-weight: 500;
  font-size: 14px;
  word-break: break-all;
}

.url-link:hover {
  color: #1565c0;
  text-decoration: underline;
}

.url-link i {
  font-size: 12px;
  flex-shrink: 0;
}

.title-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #1976d2;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.2s ease;
}

.title-link:hover {
  color: #1565c0;
  text-decoration: underline;
}

.title-link i {
  font-size: 12px;
  flex-shrink: 0;
}

.question-details-modern {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 10px;
  margin-top: 20px;
  border: 1px solid #e9ecef;
}

.details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e9ecef;
}

.details-header h5 {
  margin: 0;
  color: #2c3e50;
  font-size: 16px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  color: #6c757d;
  cursor: pointer;
  padding: 5px;
  border-radius: 50%;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
}

.close-btn:hover {
  background: #e9ecef;
  color: #dc3545;
}

.detail-item {
  display: flex;
  margin-bottom: 10px;
}

.detail-label {
  font-weight: 600;
  color: #6c757d;
  min-width: 120px;
}

.detail-value {
  color: #2c3e50;
}

.stat-item {
  display: inline-block;
  margin-right: 15px;
  font-size: 0.9rem;
}

.stat-item i {
  margin-right: 5px;
}

.text-success {
  color: #28a745 !important;
}

.text-info {
  color: #17a2b8 !important;
}

.text-warning {
  color: #ffc107 !important;
}

.detail-link {
  color: #007bff;
  text-decoration: none;
}

.detail-link:hover {
  text-decoration: underline;
}

/* Answer Section */
.answer-section-modern {
  margin-bottom: 15px; /* 20px → 15px로 감소 */
}

@media (max-width: 768px) {
  .answer-section-modern {
    margin-bottom: 10px;
  }
}

.answer-label {
  display: block;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 10px;
}

@media (max-width: 768px) {
  .answer-label {
    display: none;
  }
}

/* Y/N Answer Section */
.yn-answer-section {
  margin-bottom: 30px;
}

.yn-buttons {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
}

.yn-btn {
  flex: 1;
  padding: 15px 20px;
  border: 2px solid #e9ecef;
  border-radius: 10px;
  background: white;
  color: #6c757d;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.yn-btn:hover {
  border-color: #007bff;
  color: #007bff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.15);
}

.yn-btn.active {
  background: #007bff;
  border-color: #007bff;
  color: white;
}

.yn-btn.active:hover {
  background: #0056b3;
  border-color: #0056b3;
  color: white;
}

.yn-btn i {
  font-size: 14px;
}

.answer-input {
  width: 100%;
  padding: 15px;
  border: 2px solid #e9ecef;
  border-radius: 10px;
  font-size: 16px;
  line-height: 1.5;
  resize: vertical;
  transition: all 0.3s ease;
}

@media (max-width: 768px) {
  .answer-input {
    padding-top: 5px;
    padding-bottom: 5px;
  }
}

/* Multiple Choice Options */
.multiple-choice-section {
  margin-bottom: 20px;
}



.radio-options,
.checkbox-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.radio-option,
.checkbox-option {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  transition: all 0.3s ease;
}

.radio-option:hover,
.checkbox-option:hover {
  border-color: #007bff;
  background-color: #f8f9ff;
}

.radio-input,
.checkbox-input {
  margin: 0;
  margin-top: 2px;
  cursor: pointer;
}

.radio-label,
.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  cursor: pointer;
  flex: 1;
  line-height: 1.5;
}

.option-key {
  font-weight: 600;
  color: #007bff;
  min-width: 20px;
}

.option-text {
  color: #2c3e50;
  flex: 1;
}

/* Radio button specific styles */
.radio-option input[type="radio"]:checked + label {
  color: #007bff;
}

.radio-option input[type="radio"]:checked {
  accent-color: #007bff;
}

/* Checkbox specific styles */
.checkbox-option input[type="checkbox"]:checked + label {
  color: #007bff;
}

.checkbox-option input[type="checkbox"]:checked {
  accent-color: #007bff;
}

@media (max-width: 768px) {
  .radio-option,
  .checkbox-option {
    padding: 10px 12px;
    gap: 10px;
  }
  
  .option-key {
    min-width: 18px;
  }
}

.answer-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}

.solved-buttons {
  display: flex;
  gap: 15px;
  margin-top: 20px;
}

@media (max-width: 768px) {
  .solved-buttons {
    margin-top: 10px;
  }
  
  /* solved-btn 스타일은 공통 CSS (mobile-buttons.css)에서 처리됨 */
}

.solved-btn {
  padding: 12px 24px;
  border: 2px solid;
  border-radius: 25px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.solved-btn:first-child {
  border-color: #007bff;
  background: #007bff;
  color: white;
}

.solved-btn:first-child:hover {
  background: #0056b3;
  border-color: #0056b3;
}

.solved-btn:last-child {
  border-color: #dc3545;
  background: #dc3545;
  color: white;
}

.solved-btn:last-child:hover {
  background: #c82333;
  border-color: #c82333;
}

.solved-btn.active {
  transform: scale(1.05);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

/* Submit Button for Force Answer Mode */
.submit-button-container {
  display: flex;
  justify-content: center;
  margin-top: 15px;
}

.submit-btn {
  padding: 12px 32px;
  border: 2px solid #28a745;
  border-radius: 25px;
  background: #28a745;
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.submit-btn:hover:not(:disabled) {
  background: #218838;
  border-color: #218838;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
}

.submit-btn:disabled {
  background: #6c757d;
  border-color: #6c757d;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
  opacity: 0.6;
}

/* Answer/Explanation Display */
.answer-display,
.explanation-display {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 10px;
  margin-bottom: 20px;
}

.answer-content,
.explanation-content {
  white-space: pre-wrap;
  word-wrap: break-word;
  line-height: 1.5;
}

.answer-text,
.explanation-text {
  margin-top: 10px;
  color: #2c3e50;
}

/* Question Edit Form */
.question-edit-form {
  background: #f8f9fa;
  border: 2px solid #007bff;
  border-radius: 10px;
  padding: 20px;
  margin-top: 20px;
}

.edit-form-header {
  margin-bottom: 20px;
}

.edit-form-header h4 {
  color: #007bff;
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.edit-form-content {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.form-row {
  display: flex;
  gap: 15px;
}

.form-row .form-group {
  flex: 1;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.form-group label {
  font-weight: 600;
  color: #2c3e50;
  font-size: 14px;
}

.form-control {
  padding: 8px 12px;
  border: 1px solid #e9ecef;
  border-radius: 5px;
  font-size: 14px;
  transition: all 0.3s ease;
}

.form-control:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.1);
}

.edit-form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

.btn-save,
.btn-cancel {
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-save {
  background: #007bff;
  color: white;
}

.btn-save:hover {
  background: #0056b3;
}

.btn-cancel {
  background: #6c757d;
  color: white;
}

.btn-cancel:hover {
  background: #5a6268;
}

/* Bottom Navigation */
.bottom-navigation {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.progress-toggle {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #6c757d;
}

.toggle-switch {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 24px;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: .4s;
  border-radius: 24px;
}

.toggle-slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
}

input:checked + .toggle-slider {
  background-color: #007bff;
}

input:checked + .toggle-slider:before {
  transform: translateX(26px);
}

.nav-center {
  display: flex;
  align-items: center;
  gap: 18px; /* 25px → 18px (30% 감소) */
}

.nav-btn {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 50%;
  background: white;
  color: #6c757d;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.nav-btn:hover:not(:disabled) {
  background: #007bff;
  color: white;
  transform: translateY(-2px);
}

.nav-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.progress-display {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  min-width: 90px; /* 현재 너비의 1.5배로 설정 */
  text-align: center;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.time-display {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.current-question-time,
.total-time {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: #6c757d;
}

.current-question-time i,
.total-time i {
  font-size: 10px;
  color: #007bff;
}

.nav-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.nav-action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: 1px solid #e9ecef;
  border-radius: 20px;
  background: white;
  color: #6c757d;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.nav-action-btn:hover {
  background: #007bff;
  color: white;
  border-color: #007bff;
  transform: translateY(-2px);
}

.nav-action-btn .action-label {
  font-size: 11px;
  font-weight: 500;
}

/* Modern Button Styles */
.modern-btn {
  width: 45px;
  height: 45px;
  border: none;
  border-radius: 50%;
  background: #f8f9fa;
  color: #6c757d;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 18px;
  position: relative;
}

.modern-btn .btn-text {
  position: absolute;
  font-size: 14px;
  opacity: 0.7;
}

.modern-btn:hover {
  background: #e9ecef;
  color: #495057;
  transform: scale(1.05);
}

.modern-btn.active {
  background: #007bff;
  color: white;
}

.modern-btn.favorite-active {
  background: #007bff;
  color: white;
}

.modern-btn.ignore-active {
  background: #dc3545;
  color: white;
}

.modern-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.modern-nav-btn {
  width: 50px;
  height: 50px;
  border: none;
  border-radius: 50%;
  background: #f8f9fa;
  color: #6c757d;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 20px;
  position: relative;
}

.modern-nav-btn .btn-text {
  position: absolute;
  font-size: 16px;
  opacity: 0.7;
}

.modern-nav-btn:hover:not(:disabled) {
  background: #e9ecef;
  color: #495057;
  transform: scale(1.05);
}

.modern-nav-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

/* Action Buttons */
.action-buttons {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 15px;
  padding: 20px 30px;
  background: white;
  border-top: 1px solid #e9ecef;
}

.action-left {
  flex: 1;
  display: flex;
  align-items: center;
}

.action-right {
  display: flex;
  gap: 15px;
  align-items: center;
}

.voice-incorrect-reason {
  margin-bottom: 15px;
  padding: 0 30px;
}

.voice-incorrect-reason .alert {
  border-radius: 8px;
  font-size: 14px;
  padding: 10px 15px;
  white-space: pre-line;
}

.realtime-text-container {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  padding: 10px;
  margin-top: 5px;
}

.realtime-text-container div {
  margin-bottom: 8px;
}

.realtime-text-container div:last-child {
  margin-bottom: 0;
}

.combined-text .text-info {
  font-weight: 500;
  background: #d1ecf1;
  padding: 8px 12px;
  border-radius: 6px;
  border-left: 4px solid #17a2b8;
  display: block;
  line-height: 1.5;
}

.interim-status {
  text-align: center;
  padding: 10px;
  color: #6c757d;
}

.interim-status i {
  margin-right: 5px;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

.action-btn-secondary,
.action-btn-primary,
.action-btn-success,
.action-btn-danger,
.action-btn-info {
  padding: 12px 24px;
  border: 2px solid;
  border-radius: 25px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.action-btn-secondary {
  border-color: #6c757d;
  background: white;
  color: #6c757d;
}

.action-btn-secondary:hover:not(:disabled) {
  background: #6c757d;
  color: white;
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
  background: #1e7e34;
  border-color: #1e7e34;
}

.action-btn-danger {
  border-color: #dc3545;
  background: white;
  color: #dc3545;
}

.action-btn-danger:hover:not(:disabled) {
  background: #dc3545;
  border-color: #dc3545;
  color: white;
}

.action-btn-info {
  border-color: #6c757d;
  background: white;
  color: #6c757d;
}

.action-btn-info:hover:not(:disabled) {
  background: #6c757d;
  border-color: #6c757d;
  color: white;
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

.action-btn-secondary:disabled,
.action-btn-primary:disabled,
.action-btn-success:disabled,
.action-btn-danger:disabled,
.action-btn-info:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn-voice {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 25px;
  font-weight: 600;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.action-btn-voice:hover:not(:disabled) {
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.action-btn-voice.active {
  background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%);
  box-shadow: 0 4px 12px rgba(78, 205, 196, 0.4);
}

.action-btn-voice.active:hover {
  background: linear-gradient(135deg, #45b7aa 0%, #3d8b7a 100%);
}

.action-btn-voice:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Error Container */
.error-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
}

.error-message {
  background: white;
  padding: 30px;
  border-radius: 10px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  color: #dc3545;
  font-size: 18px;
  font-weight: 500;
}

/* Responsive Design */
@media (max-width: 768px) {
  .take-exam-modern {
    padding: 8px; /* 10px → 8px (20% 감소) */
  }
  
  .exam-container {
    border-radius: 15px;
  }
  
  .top-header {
    justify-content: center;
    padding: 12px 16px; /* 15px 20px → 12px 16px (20% 감소) */
  }
  
  .page-title {
    padding: 12px 20px 8px 20px; /* 상단 15px → 12px, 하단 10px → 8px로 추가 감소 */
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
  }
  
  .page-title h1 {
    font-size: 24px;
    margin: 0 !important; /* flex 레이아웃이므로 마진 제거 */
    flex: 1; /* 제목이 남은 공간을 차지하도록 */
  }
  
  /* page-title 안의 AI 모의 인터뷰 버튼 스타일 (모바일) */
  .page-title .page-title-btn {
    padding: 0 !important;
    width: 40px !important;
    height: 40px !important;
    border-radius: 50% !important;
    gap: 0 !important;
    min-width: auto !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 0 !important;
    margin-left: auto !important;
    flex-shrink: 0 !important;
    position: relative !important; /* 아이콘 절대 위치 기준 */
  }
  
  .page-title .page-title-btn .action-label {
    display: none !important;
  }
  
  .page-title .page-title-btn i {
    font-size: 14px !important;
    margin: 0 !important;
    padding: 0 !important;
    position: absolute !important;
    left: 50% !important;
    top: 50% !important;
    transform: translate(-50%, -50%) !important;
    line-height: 1 !important;
  }
  
  .study-modes {
    flex-wrap: wrap;
    gap: 8px; /* 10px → 8px (20% 감소) */
    padding: 12px 16px; /* 15px 20px → 12px 16px (20% 감소) */
  }
  
  /* 원형 버튼 스타일은 공통 CSS (mobile-buttons.css)에서 처리됨 */
  
  /* action-right 안의 버튼들 원형 버튼으로 */
  .action-right .action-btn-info,
  .action-right .action-btn-success,
  .action-right .action-btn-danger,
  .action-right .ai-mock-interview-btn {
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
  
  .action-right .action-btn-info span,
  .action-right .action-btn-success span,
  .action-right .ai-mock-interview-btn .action-label,
  .action-right .action-btn-danger span {
    display: none !important;
  }
  
  /* AI Mock Interview 버튼 아이콘 중앙 정렬 */
  .action-right .ai-mock-interview-btn i {
    margin: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    line-height: 1 !important;
  }
  
  /* solved-buttons 안의 버튼들 원형 버튼으로 */
  .solved-btn {
    padding: 0 !important;
    width: 40px !important;
    height: 40px !important;
    border-radius: 50% !important;
    gap: 0 !important;
    min-width: auto !important;
  }
  
  .solved-btn span {
    display: none !important;
  }
  
  /* form-actions 안의 버튼들 원형 버튼으로 */
  .form-actions .btn {
    padding: 0 !important;
    width: 40px !important;
    height: 40px !important;
    border-radius: 50% !important;
    gap: 0 !important;
    min-width: auto !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 0 !important;
  }
  
  .form-actions .btn i {
    font-size: 14px !important;
    line-height: 1 !important;
    color: white !important;
  }
  
  /* form-actions 안의 버튼 텍스트 숨김 (아이콘은 유지) */
  .form-actions .btn span {
    display: none !important;
  }
  
  /* edit-form-actions 안의 버튼들 원형 버튼으로 */
  .edit-form-actions .btn-save,
  .edit-form-actions .btn-cancel {
    padding: 0 !important;
    width: 40px !important;
    height: 40px !important;
    border-radius: 50% !important;
    min-width: auto !important;
    gap: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
  }
  
  .edit-form-actions .btn-save span,
  .edit-form-actions .btn-cancel span {
    display: none !important;
  }
  
  .edit-form-actions .btn-save i,
  .edit-form-actions .btn-cancel i {
    font-size: 14px !important;
    color: white !important;
  }
  
  /* modal-footer 안의 버튼들 원형 버튼으로 */
  .modal-footer .btn {
    padding: 0 !important;
    width: 40px !important;
    height: 40px !important;
    border-radius: 50% !important;
    gap: 0 !important;
    min-width: auto !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 0 !important;
  }
  
  .modal-footer .btn i {
    font-size: 14px !important;
    line-height: 1 !important;
    color: white !important;
  }
  
  .modal-footer .btn span {
    display: none !important;
  }
  
  .card-header-modern {
    flex-direction: column;
    gap: 5px;
    align-items: flex-start;
    padding: 5px 16px;
    margin-bottom: 16px;
  }
  
  .question-text {
    font-size: 18px;
    margin-bottom: 16px; /* 기본 마진에 20% 감소 적용 */
  }
  
  .question-link {
    color: #007bff;
    text-decoration: none;
    font-weight: 500;
    transition: color 0.2s;
    cursor: pointer;
  }
  
  .question-link:hover {
    color: #0056b3;
    text-decoration: underline;
  }
  
  .bottom-navigation {
    flex-direction: column;
    /* gap: 12px; */
    padding: 0px 20px;
  }
  
  .nav-center {
    order: -1;
    gap: 12px; /* 18px → 12px (모바일에서 추가 감소) */
  }
  
  .nav-left {
    gap: 12px; /* 15px → 12px (20% 감소) */
  }
  
  .time-display {
    margin-left: 0;
  }
  
  .current-question-time,
  .total-time {
    font-size: 11px;
  }
  
  .form-row {
    flex-direction: column;
    gap: 8px; /* 10px → 8px (20% 감소) */
  }
  
  .question-edit-form {
    padding: 12px; /* 15px → 12px (20% 감소) */
  }
  
  .action-buttons {
    flex-direction: column;
    align-items: stretch;
    gap: 8px; /* 10px → 8px (20% 감소) */
    padding: 12px 16px; /* 15px 20px → 12px 16px (20% 감소) */
  }
  
  .voice-incorrect-reason {
    padding: 0 16px; /* 모바일에서 패딩 조정 */
    margin-top: 10px;
  }
  
  .action-left {
    order: 2;
    margin-top: 10px;
  }
  
  .action-right {
    order: 1;
    justify-content: center;
    flex-wrap: wrap;
  }
  
  .meta-item {
    margin-bottom: 8px; /* 기본 마진에 20% 감소 적용 */
  }
  .new-question-form {
    padding: 16px; /* 기본 패딩에 20% 감소 적용 */
  }
  
  .form-group {
    margin-bottom: 16px; /* 기본 마진에 20% 감소 적용 */
  }
  
  .form-actions {
    margin-top: 24px; /* 30px → 24px (20% 감소) */
    padding-top: 16px; /* 20px → 16px (20% 감소) */
  }
}

/* Legacy styles for compatibility */
.exam-info {
  font-size: 1.2rem;
}

.btn.active {
  font-weight: bold;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.btn.btn-warning.active {
  box-shadow: 0 0 0 0.2rem rgba(255, 193, 7, 0.25);
}

/* Modal Styles */
.mobile-voice-interview-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  height: 100%;
  z-index: 2000; /* 모달 오버레이 */
  background: white;
  overflow: hidden;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000; /* 모달 오버레이 */
  animation: fadeIn 0.3s ease-out;
}

.modal-content {
  background: white;
  border-radius: 15px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  max-width: 400px;
  width: 90%;
  max-height: 90vh;
  overflow: hidden;
  animation: slideInUp 0.3s ease-out;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 25px;
  border-bottom: 1px solid #e9ecef;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
}

.modal-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #495057;
  display: flex;
  align-items: center;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #6c757d;
  cursor: pointer;
  padding: 5px;
  border-radius: 50%;
  transition: all 0.2s ease;
  width: 35px;
  height: 35px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close:hover {
  background-color: #e9ecef;
  color: #495057;
  transform: scale(1.1);
}

.modal-body {
  padding: 25px;
  text-align: center;
}

.modal-body p {
  font-size: 1.1rem;
  color: #495057;
  margin: 0;
  line-height: 1.5;
}

.modal-footer {
  display: flex;
  gap: 10px;
  padding: 20px 25px;
  border-top: 1px solid #e9ecef;
  background: #f8f9fa;
  justify-content: flex-end;
}

.modal-footer .btn {
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.2s ease;
  min-width: 80px;
}

.modal-footer .btn-secondary {
  background-color: #6c757d;
  border-color: #6c757d;
  color: white;
}

.modal-footer .btn-secondary:hover {
  background-color: #5a6268;
  border-color: #545b62;
  transform: translateY(-1px);
}

.modal-footer .btn-danger {
  background-color: #dc3545;
  border-color: #dc3545;
  color: white;
}

.modal-footer .btn-danger:hover {
  background-color: #c82333;
  border-color: #bd2130;
  transform: translateY(-1px);
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
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Accuracy meta item styling */
.accuracy-meta {
  color: #6c757d;
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 12px;
  position: relative;
}

.accuracy-select {
  background: none;
  border: none;
  color: #6c757d;
  cursor: pointer;
  padding: 2px 4px;
  margin-left: 4px;
  border-radius: 3px;
  font-size: 10px;
  transition: all 0.2s ease;
  outline: none;
}

.accuracy-select:hover {
  background-color: #e9ecef;
  color: #495057;
}

.accuracy-select:focus {
  background-color: #e9ecef;
  color: #495057;
}

.accuracy-adjustment {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: 8px;
}

.accuracy-slider {
  width: 80px;
  height: 4px;
  border-radius: 2px;
  background: #e9ecef;
  outline: none;
  cursor: pointer;
  -webkit-appearance: none;
}

.accuracy-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #007bff;
  cursor: pointer;
  border: 2px solid #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.accuracy-slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #007bff;
  cursor: pointer;
  border: 2px solid #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.accuracy-slider:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.accuracy-slider-value {
  font-size: 11px;
  color: #6c757d;
  min-width: 35px;
  text-align: center;
}

/* 정확도 조정 드롭다운 */
.accuracy-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  margin-top: 4px;
  min-width: 150px;
  max-width: 200px;
}

.dropdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid #e9ecef;
  background: #f8f9fa;
  border-radius: 6px 6px 0 0;
}

.dropdown-title {
  font-weight: 600;
  color: #495057;
  font-size: 12px;
}

.close-dropdown-btn {
  background: none;
  border: none;
  color: #6c757d;
  cursor: pointer;
  padding: 2px;
  border-radius: 3px;
  transition: all 0.2s ease;
  font-size: 10px;
}

.close-dropdown-btn:hover {
  background-color: #e9ecef;
  color: #495057;
}

.adjustment-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.adjustment-buttons {
  display: flex;
  gap: 8px;
}

.adjustment-btn {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  background: white;
  color: #495057;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.adjustment-btn:hover {
  background-color: #f8f9fa;
  border-color: #adb5bd;
}

.adjustment-btn.active {
  background-color: #007bff;
  color: white;
  border-color: #007bff;
}

.clear-btn.active {
  background-color: #28a745;
  border-color: #28a745;
}

.ambiguous-btn.active {
  background-color: #ffc107;
  border-color: #ffc107;
  color: #212529;
}

.adjustment-preview {
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.preview-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}

.preview-label {
  color: #6c757d;
  font-weight: 500;
}

.preview-value {
  color: #495057;
  font-weight: 600;
}

.adjustment-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.apply-btn, .cancel-btn {
  padding: 6px 12px;
  border: 1px solid;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 4px;
}

.apply-btn {
  background-color: #28a745;
  border-color: #28a745;
  color: white;
}

.apply-btn:hover {
  background-color: #218838;
  border-color: #1e7e34;
}

.cancel-btn {
  background-color: #6c757d;
  border-color: #6c757d;
  color: white;
}

.cancel-btn:hover {
  background-color: #5a6268;
  border-color: #545b62;
}

/* 새 문제 추가 폼 스타일 */
.new-question-form {
  padding: 20px;
}

.new-question-form .form-group {
  margin-bottom: 20px;
}

.new-question-form label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #495057;
}

.new-question-form .form-control {
  width: 100%;
  padding: 12px;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.2s ease;
}

.new-question-form .form-control:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}

.new-question-form textarea.form-control {
  resize: vertical;
  min-height: 80px;
}

.new-question-form .form-row {
  display: flex;
  gap: 20px;
}

.new-question-form .form-row .form-group {
  flex: 1;
}

.new-question-form .form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #e9ecef;
}

.new-question-form .btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.new-question-form .btn-primary {
  background-color: #007bff;
  color: white;
}

.new-question-form .btn-primary:hover {
  background-color: #0056b3;
}

.new-question-form .btn-secondary {
  background-color: #6c757d;
  color: white;
}

.new-question-form .btn-secondary:hover {
  background-color: #5a6268;
}

.new-question-form .btn-success {
  background-color: #28a745;
  color: white;
}

.new-question-form .btn-success:hover {
  background-color: #218838;
}



/* 연결된 프로젝트 스타일 (Exam Detail과 동일) */
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

/* 모바일에서 특정 레이블 숨기기 */
@media (max-width: 768px) {
  /* Get a hint 버튼을 원형 버튼으로 */
  .hint-btn {
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
  
  .hint-btn i {
    font-size: 14px !important;
    line-height: 1 !important;
  }
  
  .hint-btn span {
    display: none !important;
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
  
  /* Difficulty (Medium) 레이블 숨기기 */
  .meta-item:has(.fas.fa-signal) {
    font-size: 0;
    line-height: 1;
  }
  
  .meta-item:has(.fas.fa-signal) i {
    font-size: 14px;
    line-height: 1;
  }
  
  /* Accuracy: 레이블 숨기기 */
  .accuracy-meta {
    font-size: 0;
    line-height: 1;
  }
  
  .accuracy-meta i,
  .accuracy-meta .accuracy-adjustment {
    font-size: 14px;
    line-height: 1;
  }
  
  /* solved-buttons 오른쪽 정렬 */
  .solved-buttons {
    display: flex !important;
    justify-content: flex-end !important;
  }
  
  /* modern-btn 원형 버튼으로 (타원 방지) */
  .modern-btn {
    padding: 0 !important;
    width: 40px !important;
    height: 40px !important;
    border-radius: 50% !important;
    min-width: 40px !important;
    max-width: 40px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
  }
  
  .modern-btn i {
    font-size: 16px !important;
    line-height: 1 !important;
    margin: 0 !important;
  }
  
  .modern-btn .btn-text {
    display: none !important;
  }
}

@media (max-width: 576px) {
  .hint-btn,
  .card-action-btn {
    width: 36px !important;
    height: 36px !important;
  }
  
  .hint-btn i,
  .card-action-btn i {
    font-size: 12px !important;
  }
}



</style> 
```
