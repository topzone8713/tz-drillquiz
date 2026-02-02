<template>
  <div class="mobile-voice-interview">
    <!-- 종료 확인 모달 -->
    <div v-if="showEndConfirmModal" class="modal-overlay" @click="cancelEndInterview">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h5 class="modal-title">
            <i class="fas fa-exclamation-triangle text-warning"></i>
            {{ $t('voiceInterview.confirmEndTitle') || '인터뷰 종료 확인' }}
          </h5>
          <button class="modal-close" @click="cancelEndInterview">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <p class="mb-0">{{ $t('voiceInterview.confirmEnd') || '인터뷰를 종료하시겠습니까?' }}</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="cancelEndInterview">
            <i class="fas fa-times"></i>
            <span>{{ $t('voiceInterview.cancel') || '취소' }}</span>
          </button>
          <button class="btn btn-danger" @click="confirmEndInterview">
            <i class="fas fa-check"></i>
            <span>{{ $t('voiceInterview.end') || '종료' }}</span>
          </button>
        </div>
      </div>
    </div>
    
    <!-- 인터뷰 결과 모달 -->
    <div v-if="showResultsModal" class="modal-overlay" @click="closeResultsModal">
      <div class="modal-content results-modal" @click.stop>
        <div class="modal-header">
          <h5 class="modal-title">
            <i class="fas fa-chart-bar text-primary"></i>
            {{ $t('voiceInterview.resultsTitle') || '인터뷰 결과' }}
          </h5>
          <button class="modal-close" @click="closeResultsModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body results-body">
          <!-- 결과 요약 -->
          <div class="results-summary">
            <div class="summary-item">
              <span class="summary-label">{{ $t('voiceInterview.totalQuestions') || '전체 문제' }}</span>
              <span class="summary-value">{{ questionEvaluations.length }}</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">{{ $t('voiceInterview.correctAnswers') || '정답' }}</span>
              <span class="summary-value correct">{{ correctCount }}</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">{{ $t('voiceInterview.wrongAnswers') || '오답' }}</span>
              <span class="summary-value wrong">{{ wrongCount }}</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">{{ $t('voiceInterview.accuracy') || '정확도' }}</span>
              <span class="summary-value" :class="{ 'high': averageAccuracy >= 80, 'medium': averageAccuracy >= 60 && averageAccuracy < 80, 'low': averageAccuracy < 60 }">
                {{ averageAccuracy.toFixed(1) }}%
              </span>
            </div>
          </div>
          
          <!-- 문제별 상세 결과 -->
          <div class="results-details">
            <h6 class="details-title">
              <i class="fas fa-list-ul"></i>
              {{ $t('voiceInterview.questionDetails') || '문제별 상세 결과' }}
            </h6>
            <div class="results-table-container">
              <table class="results-table">
                <thead>
                  <tr>
                    <th class="col-number">#</th>
                    <th class="col-question">{{ $t('voiceInterview.question') || '문제' }}</th>
                    <th class="col-answer">{{ $t('voiceInterview.yourAnswer') || '답변' }}</th>
                    <th class="col-evaluation">{{ $t('voiceInterview.evaluation') || '평가 내용' }}</th>
                    <th class="col-accuracy">{{ $t('voiceInterview.accuracy') || '정확도' }}</th>
                    <th class="col-result">{{ $t('voiceInterview.result') || '결과' }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr 
                    v-for="(evaluation, index) in questionEvaluations" 
                    :key="index"
                    :class="{ 'correct': evaluation.isCorrect, 'wrong': !evaluation.isCorrect }"
                  >
                    <td class="col-number">{{ index + 1 }}</td>
                    <td class="col-question" :title="evaluation.questionTitle">
                      {{ evaluation.questionTitle.length > 30 ? evaluation.questionTitle.substring(0, 30) + '...' : evaluation.questionTitle }}
                    </td>
                    <td class="col-answer" :title="evaluation.userAnswer">
                      {{ evaluation.userAnswer.length > 40 ? evaluation.userAnswer.substring(0, 40) + '...' : evaluation.userAnswer }}
                    </td>
                    <td class="col-evaluation" :title="evaluation.aiEvaluation">
                      <div class="evaluation-content">
                        {{ evaluation.aiEvaluation && evaluation.aiEvaluation.length > 50 ? evaluation.aiEvaluation.substring(0, 50) + '...' : (evaluation.aiEvaluation || '-') }}
                      </div>
                    </td>
                    <td class="col-accuracy">
                      <span :class="{ 'high': evaluation.accuracy >= 80, 'medium': evaluation.accuracy >= 60 && evaluation.accuracy < 80, 'low': evaluation.accuracy < 60 }">
                        {{ evaluation.accuracy }}%
                      </span>
                    </td>
                    <td class="col-result">
                      <i v-if="evaluation.isCorrect" class="fas fa-check-circle text-success"></i>
                      <i v-else class="fas fa-times-circle text-danger"></i>
                      <span>{{ evaluation.isCorrect ? ($t('voiceInterview.correct') || '정답') : ($t('voiceInterview.wrong') || '오답') }}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="downloadResults">
            <i class="fas fa-download me-1"></i>
            {{ $t('voiceInterview.downloadResults') || '다운로드' }}
          </button>
          <button v-if="examId" class="btn btn-success" @click="viewResultsList">
            <i class="fas fa-list me-1"></i>
            {{ getViewResultsText() }}
          </button>
          <button v-if="examId" class="btn btn-info" @click="shareResults">
            <i class="fas fa-share-alt me-1"></i>
            {{ $t('voiceInterview.shareResults') || '결과 공유하기' }}
          </button>
          <button class="btn btn-primary" @click="closeResultsModal">
            <i class="fas fa-check me-1"></i>
            {{ $t('voiceInterview.close') || '확인' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 공유 모달 -->
    <div v-if="showShareModal" class="modal-overlay" @click="closeShareModal">
      <div class="modal-content share-modal" @click.stop>
        <div class="modal-header">
          <h5 class="modal-title">
            <i class="fas fa-share-alt text-info"></i>
            {{ $t('voiceInterview.shareResults') || '결과 공유하기' }}
          </h5>
          <button class="modal-close" @click="closeShareModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <!-- 스터디가 없는 경우 -->
          <div v-if="!hasStudies" class="alert alert-warning">
            <i class="fas fa-exclamation-triangle me-2"></i>
            {{ $t('voiceInterview.share.noStudy') || '결과를 공유하려면 스터디가 필요합니다. 스터디를 먼저 만들어주세요.' }}
            <div class="mt-3">
              <button 
                class="btn btn-primary" 
                @click="createStudyForSharing"
                :disabled="isCreatingStudy"
              >
                <i class="fas fa-users me-1"></i>
                <span v-if="isCreatingStudy">
                  {{ $t('voiceInterview.share.creatingStudy') || '그룹 만들기 중...' }}
                </span>
                <span v-else>
                  {{ $t('voiceInterview.share.createStudy') || '그룹 만들기' }}
                </span>
              </button>
            </div>
          </div>

          <!-- 스터디가 있는 경우 -->
          <div v-else>
            <!-- 스터디 선택 -->
            <div class="mb-3">
              <label class="form-label">
                <i class="fas fa-users me-1"></i>
                {{ $t('voiceInterview.share.selectStudy') || '스터디 선택' }}
              </label>
              <select v-model="selectedStudyId" @change="loadStudyMembers" class="form-select">
                <option value="">{{ $t('voiceInterview.share.selectStudyPlaceholder') || '스터디를 선택하세요' }}</option>
                <option v-for="study in connectedStudies" :key="study.id" :value="study.id">
                  {{ getStudyTitle(study) }}
                </option>
              </select>
            </div>

            <!-- 멤버 목록 (이메일이 있는 멤버만) -->
            <div v-if="selectedStudyId && membersWithEmail.length > 0" class="mb-3">
              <label class="form-label">
                <i class="fas fa-envelope me-1"></i>
                {{ $t('voiceInterview.share.selectMembers') || '멤버 선택 (이메일이 있는 멤버만)' }}
              </label>
              <div class="member-list" style="max-height: 300px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; border-radius: 4px;">
                <div v-for="member in membersWithEmail" :key="member.id" class="form-check mb-2">
                  <input 
                    class="form-check-input" 
                    type="checkbox" 
                    :value="member.id" 
                    :id="`member-${member.id}`"
                    v-model="selectedMemberIds"
                  >
                  <label class="form-check-label" :for="`member-${member.id}`">
                    <strong>{{ member.name }}</strong>
                    <span class="text-muted ms-2">({{ member.email }})</span>
                  </label>
                </div>
              </div>
              <div class="mt-2">
                <button class="btn btn-sm btn-outline-primary" @click="selectAllMembers">
                  {{ $t('voiceInterview.share.selectAll') || '전체 선택' }}
                </button>
                <button class="btn btn-sm btn-outline-secondary ms-2" @click="deselectAllMembers">
                  {{ $t('voiceInterview.share.deselectAll') || '전체 해제' }}
                </button>
              </div>
            </div>

            <!-- 멤버가 없는 경우 -->
            <div v-if="selectedStudyId && membersWithEmail.length === 0" class="alert alert-info">
              <i class="fas fa-info-circle me-2"></i>
              {{ $t('voiceInterview.share.noMembersWithEmail') || '이메일이 있는 멤버가 없습니다.' }}
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeShareModal">
            <i class="fas fa-times me-1"></i>
            {{ $t('voiceInterview.cancel') || '취소' }}
          </button>
          <button 
            v-if="hasStudies && selectedStudyId && selectedMemberIds.length > 0" 
            class="btn btn-primary" 
            @click="sendShareEmails"
            :disabled="sendingEmails"
          >
            <i class="fas fa-paper-plane me-1"></i>
            <span v-if="sendingEmails">
              {{ $t('voiceInterview.share.sending') || '전송 중...' }}
            </span>
            <span v-else>
              {{ $t('voiceInterview.share.send') || '이메일 전송' }}
            </span>
          </button>
        </div>
      </div>
    </div>
    
    <!-- 전달된 Instructions 표시 (임시 디버그 영역) - 숨김 처리 -->
    <!--
    <div class="instructions-debug-panel" :class="{ 'empty': !instructions || instructions.trim().length === 0 }">
      <div class="instructions-header">
        <i class="fas fa-info-circle"></i>
        <strong>전달된 Instructions (임시 표시)</strong>
        <span class="instructions-length" :class="{ 'empty': !instructions || instructions.trim().length === 0 }">
          {{ instructions ? instructions.length + '자' : '0자 (비어있음!)' }}
        </span>
        <button 
          v-if="instructions && instructions.trim().length > 0 && isConnected" 
          @click="sendInstructionsAsText"
          class="btn-send-instructions"
          :disabled="!isConnected || isSendingInstructions"
        >
          <i class="fas fa-paper-plane"></i>
          {{ isSendingInstructions ? '전송 중...' : '텍스트로 전송' }}
        </button>
      </div>
      <div class="instructions-content">
        <pre v-if="instructions && instructions.trim().length > 0">{{ instructions }}</pre>
        <pre v-else class="empty-instructions">⚠️ Instructions가 비어있습니다! ⚠️</pre>
      </div>
    </div>
    -->

    <!-- 연결 상태 표시 -->
    <div v-if="!isConnected" class="connection-status">
      <div v-if="isConnecting" class="connecting">
        <i class="fas fa-spinner fa-spin"></i>
        <span>{{ $t('voiceInterview.connecting') || '준비 중...' }}</span>
      </div>
      <div v-else-if="errorMessage" class="error">
        <i class="fas fa-exclamation-triangle"></i>
        <span>{{ errorMessage }}</span>
        <button @click="retryConnection" class="retry-btn">
          {{ $t('voiceInterview.retry') || '다시 시도' }}
        </button>
      </div>
    </div>

    <!-- 인터뷰 화면 -->
    <div v-else class="interview-screen">
      <!-- 진행 상황 -->
      <div class="progress-bar">
        <div class="progress-info">
          <span class="question-number">{{ currentQuestionIndex + 1 }} / {{ totalQuestions }}</span>
          <span class="elapsed-time">{{ formatTime(elapsedTime) }}</span>
        </div>
        <div class="progress-fill" :style="{ width: `${progressPercentage}%` }"></div>
      </div>

      <!-- AI 응답 영역 -->
      <div class="ai-response-area" :class="{ 'ai-active': isAISpeaking }">
        <div class="area-header">
          <i class="fas fa-robot"></i>
          <span>{{ $t('voiceInterview.aiResponse') || 'AI 응답' }}</span>
          <div v-if="isAISpeaking" class="speaking-badge">
            <div class="wave-animation-mini">
              <div class="wave-bar-mini" v-for="i in 3" :key="i" :style="{ animationDelay: `${i * 0.15}s` }"></div>
            </div>
            <span>{{ $t('voiceInterview.aiSpeaking') || '말하는 중' }}</span>
          </div>
        </div>
        <!-- 모바일 앱 설치 안내 (웹브라우저 환경에서만 표시) -->
        <div v-if="isWebBrowser && (conversationHistory.length > 0 || currentAIText || finalTranscription)" class="mobile-app-banner">
          <div class="banner-content">
            <i class="fas fa-mobile-alt"></i>
            <span class="banner-text">
              {{ $t('voiceInterview.mobileAppNotice') || '보다 좋은 음성 서비스를 위해서는 모바일 앱을 설치하세요.' }}
            </span>
            <a 
              href="https://apps.apple.com/us/app/drillquiz/id6755402441" 
              target="_blank" 
              rel="noopener noreferrer"
              class="app-store-link"
            >
              <i class="fab fa-apple"></i>
              {{ $t('voiceInterview.downloadApp') || '앱 설치' }}
            </a>
          </div>
        </div>
        <!-- 안내 문구: 접기/펼치기 -->
        <button
          v-if="!(instructionExpanded) && (conversationHistory.length > 0 || currentAIText || finalTranscription)"
          class="instruction-toggle"
          @click="instructionExpanded = true"
        >
          <i class="fas fa-info-circle"></i>
          {{ $t('voiceInterview.showTips') || '안내 보기' }}
        </button>
        <div 
          v-if="instructionExpanded && (conversationHistory.length > 0 || currentAIText || finalTranscription)"
          class="instruction-notice"
        >
          <i class="fas fa-info-circle"></i>
          <span>{{ $t('voiceInterview.answerNotice') || '답변을 마치고 나서 "이상입니다.", "응답완료" 같은 말을 하세요.' }}</span>
          <button class="instruction-hide" @click="instructionExpanded = false">{{ $t('voiceInterview.hideTips') || '숨기기' }}</button>
        </div>
        <!-- 전체 대화 기록 영역 (사용자 + AI 모두 표시) -->
        <div 
          v-if="conversationHistory.length > 0 || currentAIText || finalTranscription" 
          ref="conversationContainer"
          class="conversation-container"
        >
          <div v-if="isAISpeaking" class="wave-animation">
            <div class="wave-bar" v-for="i in 5" :key="i" :style="{ animationDelay: `${i * 0.1}s` }"></div>
          </div>
          <!-- 대화 기록 -->
          <div v-for="(message, index) in conversationHistory" :key="'conv-' + index" 
               :class="['conversation-item', message.role === 'user' ? 'user' : 'ai']">
            <div class="message-header">
              <i :class="message.role === 'user' ? 'fas fa-user' : 'fas fa-robot'"></i>
              <span class="message-label">{{ message.role === 'user' ? $t('voiceInterview.you') : $t('voiceInterview.ai') }}</span>
            </div>
            <p class="message-text">{{ message.content }}</p>
          </div>
          <!-- 현재 사용자 응답 (실시간 업데이트) -->
          <div v-if="finalTranscription || interimTranscription" class="conversation-item user current">
            <div class="message-header">
              <i class="fas fa-user"></i>
              <span class="message-label">{{ $t('voiceInterview.you') }}</span>
            </div>
            <p class="message-text">
              <span v-if="finalTranscription">{{ finalTranscription }}</span>
              <span v-if="interimTranscription" class="interim-text">{{ interimTranscription }}</span>
            </p>
          </div>
          <!-- 현재 AI 응답 (실시간 업데이트) - conversationHistory에 아직 추가되지 않은 경우만 표시 -->
          <div v-if="currentAIText && !isCurrentAITextInHistory" class="conversation-item ai current">
            <div class="message-header">
              <i class="fas fa-robot"></i>
              <span class="message-label">{{ $t('voiceInterview.ai') }}</span>
            </div>
            <p class="message-text">{{ currentAIText }}</p>
          </div>
          <div v-else-if="isAISpeaking && !currentAIText" class="conversation-item ai current">
            <div class="message-header">
              <i class="fas fa-robot"></i>
              <span class="message-label">{{ $t('voiceInterview.ai') }}</span>
            </div>
            <p class="message-text placeholder">{{ $t('voiceInterview.aiSpeaking') || 'AI is speaking...' }}</p>
          </div>
        </div>
        <div v-else-if="currentQuestion" class="question-display">
          <h3 class="question-title">{{ currentQuestion.title }}</h3>
          <p class="question-content">{{ currentQuestion.content }}</p>
        </div>
        <div v-else class="empty-state">
          <p>{{ $t('voiceInterview.waitingForAI') || 'AI 응답을 기다리는 중...' }}</p>
        </div>
      </div>

      <!-- 사용자 답변 영역 -->
      <div class="user-response-area" :class="{ 'user-active': isUserSpeaking }">
        <div class="area-header">
          <i class="fas fa-user"></i>
          <span>{{ $t('voiceInterview.yourResponse') || '당신의 답변' }}</span>
          <div v-if="isUserSpeaking" class="speaking-badge recording">
            <div class="pulse-mini"></div>
            <span>{{ $t('voiceInterview.speaking') || '말하는 중...' }}</span>
          </div>
        </div>
        <div v-if="isUserSpeaking" class="user-speaking">
          <div class="recording-indicator">
            <div class="pulse"></div>
            <span>{{ $t('voiceInterview.speaking') || '말하는 중...' }}</span>
          </div>
          <div class="transcription" ref="transcriptionContainer">
            <p class="final-text">{{ finalTranscription }}</p>
            <p class="interim-text">{{ interimTranscription }}</p>
          </div>
        </div>
        <div v-else class="waiting">
          <i class="fas fa-microphone-slash"></i>
          <p>{{ $t('voiceInterview.waitingForYou') || '말하기 버튼을 눌러 답변을 시작하세요' }}</p>
        </div>
      </div>

      <!-- 컨트롤 버튼 -->
      <div class="controls">
        <button
          v-if="!isUserSpeaking"
          @click="startSpeaking"
          class="control-btn speak-btn"
          :disabled="!canSpeak || isAISpeaking"
        >
          <i class="fas fa-microphone"></i>
          <span>{{ $t('voiceInterview.startSpeaking') || '말하기 시작' }}</span>
        </button>

        <button
          v-if="isUserSpeaking"
          @click="stopSpeaking"
          class="control-btn stop-btn"
        >
          <i class="fas fa-stop"></i>
          <span>{{ $t('voiceInterview.stopSpeaking') || '말하기 중지' }}</span>
        </button>

        <button
          v-if="isAISpeaking || isWaitingForResponse"
          @click="stopAIResponse"
          class="control-btn stop-ai-btn"
        >
          <i class="fas fa-stop-circle"></i>
          <span>{{ $t('voiceInterview.stopAIResponse') || 'AI 응답 중지' }}</span>
        </button>

        <button
          @click="moveToNextQuestion"
          class="control-btn next-question-btn"
          :disabled="isLastQuestion"
        >
          <i class="fas fa-arrow-right"></i>
          <span>{{ $t('voiceInterview.nextQuestion') || '다음 문제' }}</span>
        </button>

        <button
          @click="endInterview"
          class="control-btn end-btn"
        >
          <i class="fas fa-stop-circle"></i>
          <span>{{ $t('voiceInterview.end') || '종료' }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'
import { apiBaseURL } from '@/config/apiConfig'
import { createStudyAndTaskForSharing } from '@/utils/shareExamUtils'
import { getLocalizedContentWithI18n } from '@/utils/multilingualUtils'
// Realtime API 대신 Chat Completions API 사용
// import { RealtimeClient } from '@/utils/realtimeClient'
// import { createAudioContext, playPcm16Audio, captureAudioFromStream, AudioBuffer } from '@/utils/audioUtils'
import { debugLog } from '@/utils/debugUtils'
import { filterEndingGreeting as filterEndingGreetingUtil, filterInitialGreeting as filterInitialGreetingUtil } from '@/utils/voiceInterviewUtils'

export default {
  name: 'MobileVoiceInterview',
  props: {
    examId: {
      type: String,
      required: true
    },
    examTitle: {
      type: String,
      default: ''
    },
    language: {
      type: String,
      default: 'en'
    },
    voice: {
      type: String,
      default: 'alloy'
    },
    instructions: {
      type: String,
      default: ''
    },
    questions: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      // 연결 상태
      isConnecting: false,
      isConnected: false,
      errorMessage: '',

      // 세션 정보 (Chat API 방식에서는 불필요하지만 호환성을 위해 유지)
      sessionId: null,
      clientSecret: null,
      websocketUrl: null,
      realtimeClient: null,

      // STT/TTS 관련
      speechRecognition: null,
      isListening: false,
      mediaStream: null,
      isAISpeaking: false,
      isUserSpeaking: false,
      isWaitingForResponse: false, // AI 응답 대기 중
      // iOS 네이티브 플러그인
      nativeTTS: null,
      nativeSTT: null,
      isUsingNativeTTS: false,
      isUsingNativeSTT: false,
      // iOS 네이티브 권한이 플러그인으로 이미 보장되었는지
      sttPermissionEnsured: false,
      // 초기 인사말이 전송되었는지 가드
      hasSentInitialGreeting: false,
      // iOS 권한 안내 UI
      showMicPermissionPrompt: false,
      // iOS 네이티브 STT 리스너 정리용
      nativeSTTListeners: [],

      // 인터뷰 진행
      currentQuestionIndex: 0,
      totalQuestions: 0,
      currentQuestion: null,
      currentAIText: '',
      aiConversationHistory: [], // AI 응답 전체 기록
      conversationHistory: [], // 전체 대화 기록 (사용자 + AI)
      finalTranscription: '',
      interimTranscription: '',
      isSendingInstructions: false, // Instructions 텍스트 전송 중 플래그
      originalInstructions: '', // 원본 Instructions 저장 (필수 규칙 포함)

      // 시간 관리
      elapsedTime: 0,
      timerInterval: null,
      startTime: null,

      // 상태
      isPaused: false,
      canSpeak: true,
      showEndConfirmModal: false,
      showResultsModal: false, // 결과 모달 표시 여부

      // API 요청 취소용
      abortController: null,

      // 말하기 종료 타이머
      speakingEndTimer: null,
      // 리스닝 상태 하트비트 로그용
      listeningHeartbeatTimer: null,

      // 문제별 평가 기록 (인터뷰 종료 시 DB 저장용)
      questionEvaluations: [], // [{ questionId, questionTitle, userAnswer, aiEvaluation, isCorrect, accuracy }]
      examQuestions: [], // 시험 문제 목록 (종료 시 저장용)
      originalQuestions: [], // 최초 로딩 시 전달받은 질문 목록 (고정, 점수 처리용)
      savedResultId: null, // 저장된 결과 ID (공유 기능용)

      // UI 상태: 안내문 접기/펼치기
      instructionExpanded: false,

      // 공유 모달 관련
      showShareModal: false,
      connectedStudies: [],
      selectedStudyId: null,
      studyMembers: [],
      selectedMemberIds: [],
      sendingEmails: false,
      isCreatingStudy: false,
      // 사용자 프로필 언어 캐시
      userProfileLanguage: null
    }
  },
  computed: {
    isWebBrowser() {
      // 웹브라우저 환경인지 확인 (Capacitor 네이티브 앱이 아닌 경우)
      if (typeof window === 'undefined') return false
      
      // Capacitor가 없으면 웹브라우저
      if (!window.Capacitor) return true
      
      // Capacitor가 있어도 플랫폼이 'web'이면 웹브라우저
      try {
        if (typeof window.Capacitor.isNativePlatform === 'function') {
          return !window.Capacitor.isNativePlatform()
        }
        if (typeof window.Capacitor.getPlatform === 'function') {
          return window.Capacitor.getPlatform() === 'web'
        }
      } catch (error) {
        debugLog('웹브라우저 환경 감지 실패:', error, 'debug')
      }
      
      // 기본값: 웹브라우저로 간주
      return true
    },
    hasStudies() {
      return this.connectedStudies && this.connectedStudies.length > 0
    },
    membersWithEmail() {
      return this.studyMembers.filter(member => member.email && member.email.trim() !== '')
    },
    progressPercentage() {
      if (this.totalQuestions === 0) return 0
      return (this.currentQuestionIndex / this.totalQuestions) * 100
    },

    isCurrentAITextInHistory() {
      if (!this.currentAIText) return false
      const lastMessage = this.conversationHistory[this.conversationHistory.length - 1]
      return lastMessage && lastMessage.role === 'assistant' && lastMessage.content === this.currentAIText
    },

    // 결과 모달용 computed
    correctCount() {
      return this.questionEvaluations.filter(evaluation => evaluation.isCorrect).length
    },

    wrongCount() {
      return this.questionEvaluations.filter(evaluation => !evaluation.isCorrect).length
    },

    averageAccuracy() {
      if (this.questionEvaluations.length === 0) return 0
      const sum = this.questionEvaluations.reduce((acc, evaluation) => acc + (evaluation.accuracy || 0), 0)
      return sum / this.questionEvaluations.length
    },

    // 사용자가 한 문제라도 답변했는지 확인 (conversationHistory에 user 메시지가 있는지)
    hasAnsweredAnyQuestion() {
      return this.questionEvaluations.length > 0 ||
             this.conversationHistory.some(msg => msg.role === 'user' && msg.content && msg.content.trim().length > 0) ||
             (this.finalTranscription && this.finalTranscription.trim().length > 0)
    },
    
    // 마지막 문제인지 확인
    isLastQuestion() {
      const actualTotalQuestions = this.originalQuestions?.length || this.questions?.length || this.totalQuestions || 0
      return actualTotalQuestions > 0 && this.currentQuestionIndex >= actualTotalQuestions - 1
    }
  },
  async mounted() {
    // 🔵🔵🔵 컴포넌트 마운트 시점 로그 (항상 출력)
    console.log('🔵🔵🔵 [MOUNTED] MobileVoiceInterview 컴포넌트 마운트됨! 🔵🔵🔵')
    console.log('🔵 [MOUNTED] 마운트 시점 props:', {
      examId: this.examId,
      examTitle: this.examTitle,
      language: this.language,
      voice: this.voice,
      instructions: this.instructions,
      instructionsLength: this.instructions ? this.instructions.length : 0,
      instructionsPreview: this.instructions ? this.instructions.substring(0, 200) + '...' : '없음',
      questions: this.questions,
      questionsLength: this.questions ? this.questions.length : 0
    })

    // 최초 로딩 시 전달받은 질문 목록 저장 (고정, 점수 처리용)
    if (this.questions && Array.isArray(this.questions) && this.questions.length > 0) {
      this.originalQuestions = JSON.parse(JSON.stringify(this.questions)) // deep copy
      this.totalQuestions = this.questions.length
      console.log('📝 [MOUNTED] 질문 목록 저장 완료:', {
        questionsCount: this.originalQuestions.length,
        totalQuestions: this.totalQuestions
      })
    } else {
      console.warn('⚠️ [MOUNTED] 질문 목록이 비어있거나 배열이 아닙니다:', {
        questions: this.questions,
        isArray: Array.isArray(this.questions),
        length: this.questions ? this.questions.length : 0
      })
    }
    // instructions 전달 확인을 위한 로그 (항상 출력)
    console.log('📱 [MOUNTED] MobileVoiceInterview 마운트됨 - instructions 확인:', {
      instructionsLength: this.instructions ? this.instructions.length : 0,
      instructionsPreview: this.instructions ? this.instructions.substring(0, 200) + '...' : '없음'
    })
    // instructions가 비어있으면 경고
    if (!this.instructions || this.instructions.trim().length === 0) {
      console.error('❌❌❌ [MOUNTED] ⚠️⚠️⚠️ instructions prop이 비어있습니다! ❌❌❌')
    }

    // instructions가 비어있으면 잠시 대기 후 다시 확인
    if (!this.instructions || this.instructions.trim().length === 0) {
      console.warn('⚠️ MobileVoiceInterview: instructions가 비어있습니다. 500ms 후 재시도...')
      await new Promise(resolve => setTimeout(resolve, 500))
      console.log('📱 MobileVoiceInterview 재확인 - instructions:', {
        instructions: this.instructions,
        instructionsLength: this.instructions ? this.instructions.length : 0
      })
    }

    await this.initializeInterview()
  },
  watch: {
    // instructions prop이 변경될 때 감지
    instructions: {
      handler(newVal, oldVal) {
        console.log('📱 MobileVoiceInterview: instructions prop 변경 감지:', {
          oldLength: oldVal ? oldVal.length : 0,
          newLength: newVal ? newVal.length : 0,
          newPreview: newVal ? newVal.substring(0, 200) + '...' : '없음'
        })
        // 이미 초기화된 경우, instructions가 비어있지 않으면 세션 재생성 고려
        if (this.isConnected && newVal && newVal.trim().length > 0 && (!oldVal || oldVal.trim().length === 0)) {
          console.log('📱 MobileVoiceInterview: instructions가 나중에 전달됨. 세션 재생성 필요할 수 있음.')
        }
      },
      immediate: true
    },
    // 대화 기록이 변경될 때 자동 스크롤
    conversationHistory: {
      handler(newVal, oldVal) {
        // 길이 변경 또는 내용 변경 시 스크롤
        if (!oldVal || newVal.length !== oldVal.length || 
            (newVal.length > 0 && oldVal.length > 0 && 
             newVal[newVal.length - 1]?.content !== oldVal[oldVal.length - 1]?.content)) {
          this.$nextTick(() => {
            this.scrollToBottom()
          })
        }
      },
      deep: true,
      immediate: false
    },
    // 현재 AI 텍스트가 변경될 때 자동 스크롤
    currentAIText(newVal, oldVal) {
      if (newVal !== oldVal && newVal && newVal.trim()) {
        this.$nextTick(() => {
          this.scrollToBottom()
        })
      }
    },
    // 현재 사용자 전사가 변경될 때 자동 스크롤 (transcription 영역)
    finalTranscription() {
      this.$nextTick(() => {
        this.scrollTranscriptionToBottom()
        // conversation-container도 스크롤 (사용자 메시지가 conversation-container에 표시되므로)
        this.scrollToBottom()
      })
    },
    // interim 전사가 변경될 때도 transcription 영역 스크롤
    interimTranscription() {
      this.$nextTick(() => {
        this.scrollTranscriptionToBottom()
        // conversation-container도 스크롤 (사용자 메시지가 conversation-container에 표시되므로)
        this.scrollToBottom()
      })
    }
  },
  beforeDestroy() {
    this.cleanup()
  },
  methods: {
    /**
     * 사용자 언어 설정 가져오기 (localStorage 또는 i18n에서)
     */
    getUserLanguage() {
      // 1. localStorage에서 언어 설정 가져오기
      const storedLanguage = typeof window !== 'undefined' ? localStorage.getItem('language') : null
      if (storedLanguage) {
        debugLog('🔍 [getUserLanguage] localStorage 언어:', storedLanguage)
        return storedLanguage
      }
      
      // 2. i18n locale 사용
      if (this.$i18n?.locale) {
        debugLog('🔍 [getUserLanguage] i18n.locale 언어:', this.$i18n.locale)
        return this.$i18n.locale
      }
      
      // 3. prop의 language 사용
      if (this.language) {
        debugLog('🔍 [getUserLanguage] prop language:', this.language)
        return this.language
      }
      
      // 4. 기본값
      debugLog('🔍 [getUserLanguage] 기본값 사용: en')
      return 'en'
    },
    /**
     * 언어 코드를 Web Speech API의 BCP 47 형식으로 변환
     * @param {string} lang - 언어 코드 ('ko', 'en', 'es', 'zh', 'ja')
     * @returns {string} BCP 47 형식의 언어 코드
     */
    getSpeechRecognitionLang(lang) {
      const langMap = {
        'ko': 'ko-KR',
        'en': 'en-US',
        'es': 'es-ES',
        'zh': 'zh-CN',
        'ja': 'ja-JP'
      }
      // 매핑된 언어가 있으면 사용, 없으면 'en-US' 기본값
      return langMap[lang] || 'en-US'
    },
    isIOSPlatform() {
      return typeof window !== 'undefined' && window.Capacitor && typeof window.Capacitor.getPlatform === 'function'
        ? window.Capacitor.getPlatform() === 'ios'
        : false
    },
    async retryNativePermission() {
      try {
        debugLog('🔁 [retryNativePermission] iOS 네이티브 권한 재요청 시작')
        await this.forceSpeechPermission()
        await this.setupSpeechRecognition()
        if (this.isUsingNativeSTT) {
          await this.startNativeSTT()
        }
        // 성공 시 안내 닫기
        this.showMicPermissionPrompt = false
        this.errorMessage = ''
        debugLog('✅ [retryNativePermission] 재시도 완료')
      } catch (e) {
        console.warn('⚠️ [retryNativePermission] 재시도 실패:', e)
      }
    },
    /**
     * 인터뷰 초기화 (Chat API + TTS/STT 방식)
     */
    async initializeInterview() {
      try {
        debugLog('🔍 [initializeInterview] 함수 시작')
        this.isConnecting = true
        this.errorMessage = ''

        debugLog('🎤 [initializeInterview] Chat API + TTS/STT 방식으로 인터뷰 초기화 시작')

        // Instructions 확인 및 재시도 로직
        const maxRetries = 5
        let retryDelay = 500 // 시작 500ms
        let retryCount = 0
        let hasInstructions = false

        debugLog('🔍 [initializeInterview] Instructions 확인 시작:', { instructionsLength: this.instructions ? this.instructions.length : 0, hasInstructions: !!this.instructions })

        while (retryCount < maxRetries && (!this.instructions || this.instructions.trim().length === 0)) {
          console.warn(`⚠️ [initializeInterview] Instructions가 비어있습니다. 재시도 ${retryCount + 1}/${maxRetries}... ${retryDelay}ms 대기`)
          await new Promise(resolve => setTimeout(resolve, retryDelay))
          retryCount++
          // 지수 백오프 (최대 2000ms)
          retryDelay = Math.min(retryDelay + 500, 2000)

          // 재시도 중 instructions 다시 확인
          if (this.instructions && this.instructions.trim().length > 0) {
            hasInstructions = true
            console.log(`✅ [initializeInterview] 재시도 ${retryCount}번째에 Instructions 로드 성공!`)
            break
          }
        }

        // 모든 재시도 실패 시 에러
        if (!hasInstructions && (!this.instructions || this.instructions.trim().length === 0)) {
          const errorMsg = 'Instructions가 비어있습니다. 필수 규칙을 로드한 후 다시 시도해주세요.'
          debugLog('❌ [initializeInterview] Instructions 로드 실패:', { retryCount, maxRetries })
          this.isConnecting = false
          this.errorMessage = errorMsg
          throw new Error(errorMsg)
        }

        debugLog('✅ [initializeInterview] Instructions 확인 완료:', { instructionsLength: this.instructions.length })

        // 원본 Instructions 저장
        this.originalInstructions = this.instructions

        // 1. 마이크 권한 요청 (오디오 세션 우선 확보)
        debugLog('🔍 [initializeInterview] 1단계: 마이크 권한 요청 시작')
        await this.requestMicrophonePermission()
        debugLog('✅ [initializeInterview] 1단계: 마이크 권한 요청 완료')

        // 2. (비차단) iOS 음성 인식 권한 강제 요청 - 백그라운드 트리거
        debugLog('🔍 [initializeInterview] 2단계: (비차단) 음성 인식 권한 강제 요청 트리거')
        this.forceSpeechPermission().catch(() => {})
        debugLog('✅ [initializeInterview] 2단계: (비차단) 음성 인식 권한 요청 트리거 완료')

        // 3. TTS 초기화 (STT보다 먼저)
        debugLog('🔍 [initializeInterview] 3단계: TTS 초기화 시작')
        await this.setupTTS()
        debugLog('✅ [initializeInterview] 3단계: TTS 초기화 완료', { isUsingNativeTTS: this.isUsingNativeTTS })

        // 4. Instructions를 히스토리에 추가
        debugLog('🔍 [initializeInterview] 4단계: Instructions 히스토리 추가 시작')
        this.addInstructionsToHistory()
        debugLog('✅ [initializeInterview] 4단계: Instructions 히스토리 추가 완료')

        // 5. 타이머 시작
        debugLog('🔍 [initializeInterview] 5단계: 타이머 시작')
        this.startTimer()
        debugLog('✅ [initializeInterview] 5단계: 타이머 시작 완료')

        // 6. 연결 상태 설정 (화면 전환: "연결중..." → 인터뷰 화면)
        // 초기 인사말 TTS 재생 전에 화면이 준비되도록 함
        this.isConnected = true
        this.isConnecting = false
        debugLog('✅ [initializeInterview] 6단계: 연결 상태 설정 완료 (화면 준비됨)')

        // 7. 초기 인사말 요청 (TTS 재생 시작) - 화면 준비 후
        debugLog('🔍 [initializeInterview] 7단계: 초기 인사말 요청 시작')
        if (!this.hasSentInitialGreeting) {
          await this.sendInitialGreeting()
          debugLog('✅ [initializeInterview] 7단계: 초기 인사말 요청 완료')
        } else {
          debugLog('✅ [initializeInterview] 7단계: 이미 초기 인사말 전송됨 - 스킵')
        }

        // 8. 초기 인사말 TTS 재생 완료 대기
        // iOS 네이티브 TTS의 speak() Promise는 실제 재생 완료 전에 resolve될 수 있으므로
        // isAISpeaking이 false가 될 때까지 대기
        if (this.isAISpeaking) {
          debugLog('🔍 [initializeInterview] 8단계: 초기 인사말 TTS 재생 완료 대기 시작')
          let waitCount = 0
          const maxWait = 150 // 15초 (긴 질문 대비)
          while (this.isAISpeaking && waitCount < maxWait) {
            await new Promise(res => setTimeout(res, 100))
            waitCount++
          }
          if (this.isAISpeaking) {
            debugLog('⚠️ [initializeInterview] 8단계: TTS 재생 완료 대기 타임아웃 (15초), 강제 진행')
          } else {
            debugLog('✅ [initializeInterview] 8단계: 초기 인사말 TTS 재생 완료')
          }
          // TTS 완료 후 추가 지연 (오디오 버퍼 정리)
          await new Promise(res => setTimeout(res, 300))
        } else {
          debugLog('✅ [initializeInterview] 8단계: 초기 인사말 TTS 재생 중이 아님 (또는 이미 완료)')
        }

        // 9. Speech Recognition 초기화 (STT) - 초기 인사말 재생 완료 후
        debugLog('🔍 [initializeInterview] 9단계: Speech Recognition 초기화 시작')
        await this.setupSpeechRecognition()
        debugLog('✅ [initializeInterview] 9단계: Speech Recognition 초기화 완료', { isUsingNativeSTT: this.isUsingNativeSTT })

        // 10. iOS 네이티브 STT인 경우 시작 (초기 인사말 재생 완료 후)
        if (this.isUsingNativeSTT) {
          debugLog('🔍 [initializeInterview] 10단계: iOS 네이티브 STT 시작 - startNativeSTT() 호출 전')
          // 초기 인사말 TTS는 이미 완료되었으므로 TTS 중단 로직은 실행되지 않음
          await this.startNativeSTT()
          debugLog('✅ [initializeInterview] 10단계: iOS 네이티브 STT 시작 완료')
        }

        debugLog('✅ [initializeInterview] 인터뷰 초기화 완료 (Chat API + TTS/STT)', { isConnected: this.isConnected, isConnecting: this.isConnecting })
      } catch (error) {
        debugLog('❌ [initializeInterview] 인터뷰 초기화 실패:', { errorMessage: error.message, errorStack: error.stack, errorName: error.name })
        this.errorMessage = error.message || '인터뷰 초기화에 실패했습니다.'
        this.isConnecting = false
        throw error
      }
    },

    /**
     * 세션 생성 (Chat API 방식에서는 사용하지 않음)
     */
    async createSession() {
      // Chat API 방식에서는 세션 생성이 필요 없음
      debugLog('⚠️ createSession은 Chat API 방식에서 사용하지 않습니다.')
      return
    },

    /**
     * WebSocket 연결 (Chat API 방식에서는 사용하지 않음)
     */
    async connectWebSocket() {
      // Chat API 방식에서는 WebSocket 연결이 필요 없음
      debugLog('⚠️ connectWebSocket은 Chat API 방식에서 사용하지 않습니다.')
      return
    },

    /**
     * 마이크 권한 요청
     */
    async requestMicrophonePermission() {
      debugLog('🔍 [requestMicrophonePermission] 함수 시작')
      try {
        // 가능한 한 항상 getUserMedia로 권한 프롬프트를 트리거한다(iOS 포함)
        if (navigator && navigator.mediaDevices && typeof navigator.mediaDevices.getUserMedia === 'function') {
          debugLog('🔍 [requestMicrophonePermission] getUserMedia 호출 시작')
          this.mediaStream = await navigator.mediaDevices.getUserMedia({
            audio: {
              echoCancellation: true,
              noiseSuppression: true,
              autoGainControl: true
            }
          })
          debugLog('✅ [requestMicrophonePermission] 마이크 권한 승인 및 스트림 확보', {
            hasStream: !!this.mediaStream,
            trackCount: this.mediaStream ? this.mediaStream.getAudioTracks().length : 0
          })
          return
        }

        debugLog('⚠️ [requestMicrophonePermission] navigator.mediaDevices.getUserMedia 미지원')
      } catch (err) {
        console.error('❌ [requestMicrophonePermission] 마이크 권한 요청 실패:', err)
        this.mediaStream = null
        // 실패해도 흐름을 막지 않고 STT 초기화로 넘어가되, 이후 STT 시작 시 다시 알림 가능
      }
    },

    /**
     * 오디오 초기화 (Chat API 방식에서는 사용하지 않음)
     */
    async initializeAudio() {
      // Chat API 방식에서는 오디오 스트림 처리가 필요 없음
      debugLog('⚠️ initializeAudio는 Chat API 방식에서 사용하지 않습니다.')
      return
    },

    /**
     * 이벤트 리스너 설정 (Chat API 방식에서는 사용하지 않음)
     */
    setupEventListeners() {
      // Chat API 방식에서는 RealtimeClient 이벤트 리스너가 필요 없음
      debugLog('⚠️ setupEventListeners는 Chat API 방식에서 사용하지 않습니다.')
      return
    },

    /**
     * AI 오디오 처리 (Chat API 방식에서는 사용하지 않음 - TTS 사용)
     */
    async handleAIAudio() {
      // Chat API 방식에서는 TTS를 사용하므로 이 메서드는 사용하지 않음
      debugLog('⚠️ handleAIAudio는 Chat API 방식에서 사용하지 않습니다. TTS를 사용합니다.')
      return
    },

    /**
     * 말하기 시작 (Chat API 방식)
     */
    startSpeaking() {
      if (!this.canSpeak || this.isPaused) return

      const platform = typeof window !== 'undefined' && window.Capacitor && typeof window.Capacitor.getPlatform === 'function'
        ? window.Capacitor.getPlatform()
        : 'web'

      debugLog('🎤 말하기 시작 버튼 클릭', {
        platform,
        isUsingNativeSTT: this.isUsingNativeSTT,
        hasNativeSTT: !!this.nativeSTT,
        hasWebSTT: !!this.speechRecognition,
        isListening: this.isListening,
        isConnected: this.isConnected,
        isPaused: this.isPaused,
        canSpeak: this.canSpeak,
        hasMediaStream: !!this.mediaStream
      })

      // iOS에서 음성 인식 권한이 없을 수 있으니, 시작 시 한 번 더 강제 요청 시도 (비차단)
      if (platform === 'ios') {
        this.forceSpeechPermission().catch(() => {})
      }

      this.isUserSpeaking = true
      this.finalTranscription = ''
      this.interimTranscription = ''
      this.canSpeak = false

      // iOS 네이티브 STT: 필요 시 즉시 시작/재시작
      if (platform === 'ios' && this.isUsingNativeSTT) {
        // 사용자 제스처 시점에서 권한을 확실히 확보 (대기 허용)
        this.ensureSpeechPermissionUserInitiated()
          .then((granted) => {
            if (!granted) {
              console.warn('⚠️ [startSpeaking] STT 권한이 없어 청취를 시작할 수 없습니다.')
              this.canSpeak = true
              this.isUserSpeaking = false
              return
            }
            if (!this.isListening) {
              debugLog('🎤 [startSpeaking] iOS 네이티브 STT가 듣지 않는 상태 -> 시작/재시작 시도')
              this.startNativeSTT()
            } else {
              debugLog('🎤 [startSpeaking] iOS 네이티브 STT가 이미 청취 중')
            }
            // 권한 보장/시작과 동시에 AI 문장 준비를 비동기로 선행
            if (typeof this.prepareNextAIPrompt === 'function') {
              this.prepareNextAIPrompt().catch(() => {})
            }
          })
          .catch(err => {
            console.error('❌ [startSpeaking] STT 권한 확인/요청 실패:', err)
            this.canSpeak = true
            this.isUserSpeaking = false
          })
      }

      // Web Speech API: 필요 시 start() 호출
      if (!this.isUsingNativeSTT && this.speechRecognition) {
        this.safeStartSpeechRecognition('startSpeaking')
      }

      debugLog('🎤 말하기 시작')
    },

    /**
     * 사용자 제스처로 트리거되는 STT 권한 보장 (대기 허용)
     */
    async ensureSpeechPermissionUserInitiated() {
      try {
        // 웹 환경에서는 항상 true 반환 (iOS 네이티브 플러그인 제거됨)
        const platform = typeof window !== 'undefined' && window.Capacitor && typeof window.Capacitor.getPlatform === 'function'
          ? window.Capacitor.getPlatform()
          : 'web'
        if (platform !== 'ios') return true
        const { SpeechRecognition, provider } = await this.loadSpeechPlugin()
        debugLog('🔍 [ensureSTTPermission] 사용 플러그인:', { provider, hasSpeechRecognition: !!SpeechRecognition })
        let has = { permission: false }
        if (typeof SpeechRecognition.hasPermission === 'function') {
          has = await SpeechRecognition.hasPermission()
          debugLog('🔍 [ensureSTTPermission] 현재 권한 상태:', has)
        }
        if (has?.permission) return true
        if (typeof SpeechRecognition.requestPermission !== 'function') return false
        debugLog('🔍 [ensureSTTPermission] requestPermission() 호출 (사용자 제스처)')
        const res = await Promise.race([
          SpeechRecognition.requestPermission(),
          new Promise(resolve => setTimeout(() => resolve({ permission: false, timeout: true }), 12000))
        ])
        debugLog('✅ [ensureSTTPermission] 요청 결과:', res)
        return !!res?.permission
      } catch (e) {
        console.error('❌ [ensureSTTPermission] 실패:', e)
        return false
      }
    },

    // 음성과 무관하게 문제 텍스트/AI 문장 준비를 미리 수행해 병목을 줄인다
    async prepareNextAIPrompt() {
      try {
        debugLog('🔧 [prepareNextAIPrompt] 다음 AI 프롬프트 사전 준비 시작')
        if (typeof this.sendInitialGreeting === 'function' && !this.hasSentInitialGreeting) {
          await this.sendInitialGreeting()
          this.hasSentInitialGreeting = true
          debugLog('🔧 [prepareNextAIPrompt] 초기 인사말 전송 완료')
          return
        }
        if (typeof this.requestNextQuestionFromAI === 'function') {
          await this.requestNextQuestionFromAI()
          debugLog('🔧 [prepareNextAIPrompt] 다음 질문 요청 완료')
        }
      } catch (e) {
        console.warn('⚠️ [prepareNextAIPrompt] 준비 실패:', e)
      }
    },

    /**
     * STT 플러그인 동적 로드 (웹 전용: Web Speech API 사용)
     */
    async loadSpeechPlugin() {
      let SpeechRecognition = null
      let provider = 'web'
      // 웹 환경에서는 Web Speech API 사용
      if (typeof window !== 'undefined' && ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)) {
        SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
        provider = 'web-speech-api'
      }
      return { SpeechRecognition, provider }
    },

    /**
     * 플러그인별 권한 API 호환 래퍼
     */
    getPermissionFns(SpeechRecognition) {
      const hasPerm = SpeechRecognition?.hasPermission || SpeechRecognition?.checkPermissions
      const requestPerm = SpeechRecognition?.requestPermission || SpeechRecognition?.requestPermissions
      return { hasPerm, requestPerm }
    },

    /**
     * iOS SpeechRecognition 권한 강제 요청
     */
    async forceSpeechPermission() {
      try {
        const platform = typeof window !== 'undefined' && window.Capacitor && typeof window.Capacitor.getPlatform === 'function'
          ? window.Capacitor.getPlatform()
          : 'web'
        if (platform !== 'ios') return
        debugLog('🔍 [forceSpeechPermission] iOS 권한 강제 요청 시작')
        const { SpeechRecognition, provider } = await this.loadSpeechPlugin()
        debugLog('🔍 [forceSpeechPermission] 사용 플러그인:', { provider, hasSpeechRecognition: !!SpeechRecognition })
        // 가능하면 상태 로그
        const { hasPerm, requestPerm } = this.getPermissionFns(SpeechRecognition)
        if (typeof hasPerm === 'function') {
          const cur = await hasPerm()
          debugLog('🔍 [forceSpeechPermission] 현재 권한 상태:', cur)
        }
        if (typeof requestPerm === 'function') {
          // 15초 타임아웃 방어 (iOS 브리지 응답 지연 대비)
          const req = await Promise.race([
            requestPerm(),
            new Promise(resolve => setTimeout(() => resolve({ permission: false, timeout: true }), 15000))
          ])
          debugLog('✅ [forceSpeechPermission] 권한 요청 결과:', req)
        }
      } catch (e) {
        console.warn('⚠️ [forceSpeechPermission] 권한 강제 요청 실패:', e)
      }
    },

    /**
     * 말하기 중지 (Chat API 방식)
     */
    async stopSpeaking() {
      if (!this.isUserSpeaking) return

      // 타이머 클리어
      if (this.speakingEndTimer) {
        clearTimeout(this.speakingEndTimer)
        this.speakingEndTimer = null
      }

      this.isUserSpeaking = false
      this.canSpeak = true

      // finalTranscription이 있으면 처리
      if (this.finalTranscription && this.finalTranscription.trim()) {
        const message = this.finalTranscription.trim()
        // 종료 표현 체크
        if (this.isEndingMessage(message)) {
          debugLog('🛑 말하기 중지 (수동), 종료 표현 감지, 답변 내용 추출:', message)

          // 종료 표현 제거하고 답변 내용만 추출
          let userMessage = message
          const endingPatterns = this.getEndingPatterns()

          for (const pattern of endingPatterns) {
            userMessage = userMessage.replace(pattern, '').trim()
          }

          this.finalTranscription = ''
          this.interimTranscription = ''

          // 답변 내용이 있으면 AI 평가 요청
          if (userMessage && userMessage.trim()) {
            debugLog('🛑 말하기 중지 (수동), 종료 표현 제거 후 답변 내용:', userMessage)
            // 메시지 처리 (AI 평가 요청)
            this.handleUserMessage(userMessage.trim())
          } else {
            debugLog('🛑 말하기 중지 (수동), 종료 표현만 있고 답변 내용 없음')
            // 진행 중인 AI 응답 취소
            if (this.isWaitingForResponse && this.abortController) {
              this.abortController.abort()
              this.abortController = null
              this.isWaitingForResponse = false
            }
            // TTS 중지
            if (this.isUsingNativeTTS && this.nativeTTS) {
              try {
                await this.nativeTTS.stop()
              } catch (error) {
                debugLog('❌ iOS 네이티브 TTS 중지 실패:', error)
              }
            }
            if ('speechSynthesis' in window) {
              speechSynthesis.cancel()
            }
            this.isAISpeaking = false
          }
        } else {
          debugLog('🛑 말하기 중지 (수동), 메시지 처리:', message)
          this.handleUserMessage(message)
        }
      } else {
        debugLog('🛑 말하기 중지 (수동), 메시지 없음')
      }
    },

    /**
     * AI 응답 중지 (TTS만 중지, 대화 히스토리는 유지)
     */
    async stopAIResponse() {
      debugLog('🛑 AI 응답 중지 요청')

      // TTS 중지
      if (this.isUsingNativeTTS && this.nativeTTS) {
        try {
          await this.nativeTTS.stop()
        } catch (error) {
          debugLog('❌ iOS 네이티브 TTS 중지 실패:', error)
        }
      }
      if ('speechSynthesis' in window) {
        speechSynthesis.cancel()
      }

      // API 요청 취소 (진행 중인 요청만 취소)
      if (this.abortController) {
        this.abortController.abort()
        this.abortController = null
      }

      // 상태만 초기화 (대화 히스토리는 유지)
      this.isAISpeaking = false
      this.isWaitingForResponse = false
      // currentAIText는 유지 (이미 conversationHistory에 추가된 경우)
      // 사용자가 바로 답변할 수 있도록 canSpeak 활성화
      this.canSpeak = true

      debugLog('✅ AI 응답 중지 완료 (대화 히스토리 유지)')
    },

    /**
     * 인터뷰 일시정지
     */
    pauseInterview() {
      this.isPaused = !this.isPaused
      if (this.isPaused) {
        this.stopTimer()
      } else {
        this.startTimer()
      }
    },

    /**
     * 다음 문제로 이동
     */
    async moveToNextQuestion() {
      console.log('🔍 [moveToNextQuestion] ========== 다음 문제로 이동 시작 ==========')
      console.log('🔍 [moveToNextQuestion] 버튼 클릭됨!')
      debugLog('🔍 [moveToNextQuestion] 다음 문제로 이동 버튼 클릭')
      
      // ========== 진행 중인 모든 음성 활동 즉시 중지 ==========
      debugLog('🛑 [moveToNextQuestion] 진행 중인 모든 음성 활동 중지 시작')
      
      // 1. AI 응답 중지 (TTS)
      if (this.isAISpeaking || this.isWaitingForResponse) {
        debugLog('🛑 [moveToNextQuestion] AI 응답 중지')
        // TTS 중지
        if (this.isUsingNativeTTS && this.nativeTTS) {
          try {
            await this.nativeTTS.stop()
          } catch (error) {
            debugLog('❌ [moveToNextQuestion] iOS 네이티브 TTS 중지 실패:', error)
          }
        }
        if ('speechSynthesis' in window) {
          speechSynthesis.cancel()
        }
        
        // API 요청 취소
        if (this.abortController) {
          this.abortController.abort()
          this.abortController = null
        }
        
        this.isAISpeaking = false
        this.isWaitingForResponse = false
      }
      
      // 2. 사용자 말하기 중지 (음성 인식)
      if (this.isUserSpeaking || this.isListening) {
        debugLog('🛑 [moveToNextQuestion] 사용자 말하기 중지')
        
        // 말하기 종료 타이머 정리
        if (this.speakingEndTimer) {
          clearTimeout(this.speakingEndTimer)
          this.speakingEndTimer = null
        }
        
        // iOS 네이티브 STT 중지
        if (this.isUsingNativeSTT && this.nativeSTT) {
          try {
            await this.nativeSTT.stop()
            this.isListening = false
          } catch (error) {
            debugLog('❌ [moveToNextQuestion] iOS 네이티브 STT 중지 실패:', error)
            this.isListening = false
          }
        }
        
        // Web Speech API Speech Recognition 중지
        if (this.speechRecognition) {
          try {
            this.speechRecognition.stop()
          } catch (error) {
            debugLog('❌ [moveToNextQuestion] Speech Recognition 중지 실패:', error)
          }
        }
        
        this.isUserSpeaking = false
        this.canSpeak = true
      }
      
      debugLog('✅ [moveToNextQuestion] 모든 음성 활동 중지 완료')
      // ========== 중지 완료 ==========
      
      // 현재 상태 확인
      console.log('🔍 [moveToNextQuestion] 현재 상태:', {
        currentQuestionIndex: this.currentQuestionIndex,
        totalQuestions: this.totalQuestions,
        originalQuestionsLength: this.originalQuestions ? this.originalQuestions.length : 0,
        questionsLength: this.questions ? this.questions.length : 0,
        condition: `currentQuestionIndex (${this.currentQuestionIndex}) < totalQuestions - 1 (${this.totalQuestions - 1}) = ${this.currentQuestionIndex < this.totalQuestions - 1}`
      })
      
      // 다음 문제가 있는지 확인 - totalQuestions 대신 실제 배열 길이로 확인
      const actualTotalQuestions = this.originalQuestions?.length || this.questions?.length || this.totalQuestions || 0
      console.log('🔍 [moveToNextQuestion] 실제 질문 개수:', {
        actualTotalQuestions: actualTotalQuestions,
        fromOriginalQuestions: this.originalQuestions?.length || 0,
        fromQuestions: this.questions?.length || 0,
        fromTotalQuestions: this.totalQuestions || 0
      })
      
      // 다음 문제가 실제로 존재하는지 확인
      const hasNextQuestion = actualTotalQuestions > 0 && this.currentQuestionIndex < actualTotalQuestions - 1
      console.log('🔍 [moveToNextQuestion] 다음 문제 존재 여부:', {
        hasNextQuestion: hasNextQuestion,
        currentQuestionIndex: this.currentQuestionIndex,
        actualTotalQuestions: actualTotalQuestions,
        nextIndex: this.currentQuestionIndex + 1,
        canMove: this.currentQuestionIndex + 1 < actualTotalQuestions
      })
      
      if (hasNextQuestion) {
        const previousIndex = this.currentQuestionIndex
        
        // ========== 현재 문제를 틀린 것으로 기록 ==========
        // 이전 문제(현재 문제)에 대한 평가 기록 추가
        if (previousIndex >= 0 && previousIndex < actualTotalQuestions) {
          const currentQuestionObj = this.originalQuestions && this.originalQuestions[previousIndex]
            ? this.originalQuestions[previousIndex]
            : (this.questions && this.questions[previousIndex] ? this.questions[previousIndex] : null)
          
          if (currentQuestionObj) {
            // 현재 문제의 제목 가져오기
            const questionTitle = getLocalizedContentWithI18n(
              currentQuestionObj,
              'title',
              this.$i18n,
              this.language,
              `Question ${previousIndex + 1}`
            )
            
            // 이미 해당 문제에 대한 평가가 있는지 확인
            const existingEval = this.questionEvaluations.find(e => 
              e.questionIndex === previousIndex || 
              (e.questionTitle === questionTitle && questionTitle && questionTitle.trim() !== '')
            )
            
            if (!existingEval) {
              // 사용자 답변 추출 (conversationHistory에서 찾기)
              let userAnswer = ''
              // conversationHistory에서 해당 문제 이후의 user 메시지 찾기
              const userMessages = this.conversationHistory.filter((msg) => {
                // 현재 문제 이후의 사용자 메시지 찾기
                return msg.role === 'user' && msg.content && msg.content.trim()
              })
              
              if (userMessages.length > 0) {
                // 가장 최근 사용자 메시지를 답변으로 사용
                userAnswer = userMessages[userMessages.length - 1].content
              } else {
                // 사용자 답변이 없으면 빈 문자열 또는 기본 메시지
                userAnswer = this.language === 'ko' ? '(답변 없음 - 다음 문제로 이동)' : '(No answer - moved to next question)'
              }
              
              // 틀린 것으로 기록
              this.questionEvaluations.push({
                questionIndex: previousIndex,
                questionTitle: questionTitle,
                userAnswer: userAnswer,
                aiEvaluation: this.language === 'ko' 
                  ? '사용자가 다음 문제로 이동하여 미완료 처리'
                  : 'User moved to next question without completing',
                isCorrect: false, // 틀린 것으로 기록
                accuracy: 0 // 0%로 기록
              })
              
              console.log('🔍 [moveToNextQuestion] 현재 문제를 틀린 것으로 기록:', {
                questionIndex: previousIndex,
                questionTitle: questionTitle.substring(0, 50),
                userAnswer: userAnswer.substring(0, 50),
                isCorrect: false,
                accuracy: 0
              })
              debugLog('📝 [moveToNextQuestion] 평가 기록 추가 (틀림):', {
                questionIndex: previousIndex,
                questionTitle: questionTitle.substring(0, 50)
              })
            } else {
              console.log('🔍 [moveToNextQuestion] 이미 평가가 존재함:', {
                questionIndex: previousIndex,
                existingEval: existingEval
              })
            }
          }
        }
        // ========== 평가 기록 완료 ==========
        
        this.currentQuestionIndex++
        
        // totalQuestions가 실제 질문 개수와 다르면 업데이트
        if (actualTotalQuestions > 0 && this.totalQuestions !== actualTotalQuestions) {
          this.totalQuestions = actualTotalQuestions
          console.log('🔍 [moveToNextQuestion] totalQuestions 업데이트:', this.totalQuestions)
        }
        
        console.log('🔍 [moveToNextQuestion] 다음 문제로 이동:', {
          previousIndex: previousIndex,
          currentIndex: this.currentQuestionIndex,
          totalQuestions: this.totalQuestions,
          actualTotalQuestions: actualTotalQuestions,
          conditionResult: this.currentQuestionIndex < actualTotalQuestions
        })
        
        // Vue 반응성 보장을 위해 강제 업데이트
        this.$forceUpdate()
        
        // 다음 문제 정보 업데이트
        let nextQuestion = null
        if (this.originalQuestions && this.originalQuestions.length > 0 && this.currentQuestionIndex < this.originalQuestions.length) {
          nextQuestion = this.originalQuestions[this.currentQuestionIndex]
          this.currentQuestion = nextQuestion
          console.log('🔍 [moveToNextQuestion] 다음 문제 정보 업데이트:', {
            questionIndex: this.currentQuestionIndex,
            hasQuestion: !!nextQuestion
          })
        } else if (this.questions && this.questions.length > 0 && this.currentQuestionIndex < this.questions.length) {
          nextQuestion = this.questions[this.currentQuestionIndex]
          this.currentQuestion = nextQuestion
          console.log('🔍 [moveToNextQuestion] questions 배열에서 다음 문제 정보 업데이트')
        }
        
        // AI 응답 텍스트 초기화
        this.currentAIText = ''
        
        // 음성 인식 텍스트 초기화
        this.finalTranscription = ''
        this.interimTranscription = ''
        
        // 말하기 상태 초기화
        this.isUserSpeaking = false
        this.isAISpeaking = false
        this.canSpeak = true
        
        // 다음 질문을 직접 읽어주기
        if (nextQuestion) {
          try {
            // 질문 제목과 내용 가져오기
            const questionTitle = getLocalizedContentWithI18n(
              nextQuestion,
              'title',
              this.$i18n,
              this.language,
              `Question ${this.currentQuestionIndex + 1}`
            )
            const questionContent = getLocalizedContentWithI18n(
              nextQuestion,
              'content',
              this.$i18n,
              this.language,
              ''
            )
            
            console.log('🔍 [moveToNextQuestion] 다음 질문 정보:', {
              questionTitle: questionTitle,
              questionContent: questionContent || '(없음)',
              questionTitleLength: questionTitle ? questionTitle.length : 0,
              questionContentLength: questionContent ? questionContent.length : 0,
              questionIndex: this.currentQuestionIndex
            })
            
            // 다음 질문을 대화 히스토리에 추가
            // questionContent가 있으면 완전한 질문 문장이므로 그것만 사용
            // questionContent가 없으면 questionTitle을 질문 형식으로 변환
            let questionText = ''
            
            if (questionContent && questionContent.trim()) {
              // questionContent가 완전한 질문 문장이므로 그것만 사용
              questionText = questionContent.trim()
            } else if (questionTitle && questionTitle.trim()) {
              // questionContent가 없으면 questionTitle을 질문 형식으로 변환
              questionText = this.language === 'ko'
                ? `${questionTitle.trim()}에 대해 설명해주세요.`
                : `Please explain ${questionTitle.trim()}.`
            } else {
              // 둘 다 없으면 기본 메시지
              questionText = this.language === 'ko'
                ? `질문 ${this.currentQuestionIndex + 1}`
                : `Question ${this.currentQuestionIndex + 1}`
            }
            
            // 대화 이력은 유지하고 새로운 질문만 추가
            // 기존 대화 히스토리를 삭제하지 않음
            this.conversationHistory.push({
              role: 'assistant',
              content: questionText
            })
            console.log('🔍 [moveToNextQuestion] 다음 질문을 대화 히스토리에 추가 (기존 이력 유지):', {
              questionText: questionText.substring(0, 50),
              conversationHistoryLength: this.conversationHistory.length
            })
            debugLog('📝 [moveToNextQuestion] 다음 질문 추가 (기존 대화 이력 유지):', {
              totalMessages: this.conversationHistory.length
            })
            
            // currentAIText 업데이트 (기존 질문 텍스트 제거)
            this.currentAIText = questionText
            
            // TTS로 다음 질문 읽기 (중지 후 약간의 지연 추가)
            await new Promise(resolve => setTimeout(resolve, 300))
            console.log('🔍 [moveToNextQuestion] 다음 질문 TTS 재생 시작')
            debugLog('🔊 [moveToNextQuestion] 다음 질문 TTS 재생:', questionText.substring(0, 100))
            this.speakText(questionText)
            
            // 음성 인식 재시작 (이미 중지했으므로)
            if (!this.isListening) {
              await this.setupSpeechRecognition()
              if (this.isUsingNativeSTT) {
                await this.startNativeSTT()
              }
            }
          } catch (error) {
            console.error('❌ [moveToNextQuestion] 다음 질문 처리 실패:', error)
            debugLog('❌ 다음 질문 처리 실패:', error, 'error')
            // 에러가 발생해도 질문 인덱스는 이미 증가했으므로 계속 진행
          }
        } else {
          console.warn('⚠️ [moveToNextQuestion] 다음 질문 정보를 찾을 수 없음')
        }
        
        debugLog('✅ 다음 문제로 이동 완료', {
          currentQuestionIndex: this.currentQuestionIndex,
          totalQuestions: this.totalQuestions
        })
      } else {
        console.log('🔍 [moveToNextQuestion] 마지막 문제입니다.')
        console.log('🔍 [moveToNextQuestion] 상태 상세:', {
          currentQuestionIndex: this.currentQuestionIndex,
          actualTotalQuestions: actualTotalQuestions,
          originalQuestionsLength: this.originalQuestions?.length || 0,
          questionsLength: this.questions?.length || 0,
          totalQuestions: this.totalQuestions,
          isLastQuestion: this.currentQuestionIndex >= actualTotalQuestions - 1
        })
        debugLog('⚠️ 마지막 문제입니다. 더 이상 이동할 수 없습니다.', {
          currentQuestionIndex: this.currentQuestionIndex,
          totalQuestions: actualTotalQuestions
        })
      }
    },

    /**
     * 인터뷰 종료 확인 모달 표시
     */
    endInterview() {
      this.showEndConfirmModal = true
    },

    /**
     * 인터뷰 종료 취소
     */
    cancelEndInterview() {
      this.showEndConfirmModal = false
    },

    /**
     * AI 응답에서 마무리 인사말 필터링
     * 공통 유틸리티 사용 (iOS와 웹에서 동일한 필터링 로직 보장)
     */
    filterEndingGreeting(text) {
      return filterEndingGreetingUtil(text)
    },

    /**
     * AI 응답에서 평가 부분과 다음 질문 부분을 분리
     * @returns {Object} { evaluationText: 평가 텍스트, nextQuestionText: 다음 질문 텍스트 }
     */
    separateEvaluationAndNextQuestion(aiResponse) {
      console.log('🔍 [separateEvaluationAndNextQuestion] 시작')
      console.log('🔍 [separateEvaluationAndNextQuestion] 입력 텍스트 전체:', aiResponse)
      console.log('🔍 [separateEvaluationAndNextQuestion] 입력 텍스트 길이:', aiResponse ? aiResponse.length : 0)

      if (!aiResponse) {
        console.log('🔍 [separateEvaluationAndNextQuestion] aiResponse가 비어있음, 빈 객체 반환')
        return { evaluationText: '', nextQuestionText: '' }
      }

      // 명시적인 질문 시작 패턴만 사용 (구분자로 사용할 수 있는 패턴만)
      const questionStartPatterns = [
        // 다음 질문 시작 패턴 (가장 명확한 패턴)
        /(?:다음\s*질문|Next\s*question|두\s*번째\s*질문|세\s*번째\s*질문|네\s*번째\s*질문|다섯\s*번째\s*질문|Second\s*question|Third\s*question|Fourth\s*question|Fifth\s*question)[:：\s]*/i,
        /(?:이제|Now|다음으로|Next)[\s\n]+(?:질문|question)[:：\s]*/i,
      ]

      console.log('🔍 [separateEvaluationAndNextQuestion] 명시적 질문 패턴 검색 시작')
      let nextQuestionIndex = -1
      for (let i = 0; i < questionStartPatterns.length; i++) {
        const pattern = questionStartPatterns[i]
        const match = aiResponse.match(pattern)
        console.log(`🔍 [separateEvaluationAndNextQuestion] 패턴 ${i + 1} 검색 결과:`, match ? `매칭됨 (인덱스: ${match.index}, 길이: ${match[0].length})` : '매칭 안됨')
        if (match) {
          nextQuestionIndex = match.index + match[0].length
          console.log(`🔍 [separateEvaluationAndNextQuestion] 명시적 질문 패턴 발견! 인덱스: ${nextQuestionIndex}`)
          console.log(`🔍 [separateEvaluationAndNextQuestion] 매칭된 텍스트: "${match[0]}"`)
          break
        }
      }

      // 명시적인 질문 패턴이 없으면, 평가 마무리 표현 이후의 내용을 질문으로 간주
      // "감사합니다", "좋습니다" 등의 평가 마무리 표현 후에 질문이 시작될 수 있음
      if (nextQuestionIndex < 0) {
        console.log('🔍 [separateEvaluationAndNextQuestion] 명시적 질문 패턴 없음, 평가 마무리 표현 검색 시작')
        const evaluationEndKeywords = [
          /(?:감사합니다|고맙습니다|좋습니다|좋아요|알겠습니다)[\s\n.]+/i,
          /(?:Thank\s*you|Thanks|Good|Great)[\s\n.]+/i,
        ]

        // 평가 마무리 표현을 찾아서 그 이후를 질문으로 간주
        for (let i = 0; i < evaluationEndKeywords.length; i++) {
          const pattern = evaluationEndKeywords[i]
          const match = aiResponse.match(pattern)
          console.log(`🔍 [separateEvaluationAndNextQuestion] 평가 마무리 패턴 ${i + 1} 검색 결과:`, match ? `매칭됨 (인덱스: ${match.index}, 길이: ${match[0].length})` : '매칭 안됨')
          if (match) {
            const afterMatch = aiResponse.substring(match.index + match[0].length).trim()
            console.log(`🔍 [separateEvaluationAndNextQuestion] 평가 마무리 표현 이후 텍스트: "${afterMatch.substring(0, 100)}"`)
            console.log(`🔍 [separateEvaluationAndNextQuestion] 평가 마무리 표현 이후 텍스트 길이: ${afterMatch.length}`)
            // 평가 마무리 표현 이후의 내용이 충분히 길면 (최소 10자 이상) 질문으로 간주
            if (afterMatch.length >= 10) {
              nextQuestionIndex = match.index + match[0].length
              console.log(`🔍 [separateEvaluationAndNextQuestion] 평가 마무리 표현 이후 질문으로 간주! 인덱스: ${nextQuestionIndex}`)
              console.log(`🔍 [separateEvaluationAndNextQuestion] 매칭된 평가 마무리 텍스트: "${match[0]}"`)
              break
            } else {
              console.log(`🔍 [separateEvaluationAndNextQuestion] 평가 마무리 표현 이후 텍스트가 너무 짧음 (${afterMatch.length}자), 질문으로 간주하지 않음`)
            }
          }
        }
      }

      if (nextQuestionIndex > 0) {
        // 평가 부분과 다음 질문 부분 분리
        const evaluationText = aiResponse.substring(0, nextQuestionIndex).trim()
        const afterPatternText = aiResponse.substring(nextQuestionIndex)

        console.log('🔍 [separateEvaluationAndNextQuestion] 패턴 이후 텍스트:', afterPatternText.substring(0, 100))

        // 첫 번째 줄바꿈(`\n`) 또는 마침표(`.`) 중 먼저 나오는 것 이후의 내용만 질문으로 추출
        const firstNewlineIndex = afterPatternText.indexOf('\n')
        const firstPeriodIndex = afterPatternText.indexOf('.')
        let nextQuestionText = ''

        // 줄바꿈과 마침표 중 먼저 나오는 것을 찾음
        let separatorIndex = -1
        if (firstNewlineIndex >= 0 && firstPeriodIndex >= 0) {
          // 둘 다 있으면 더 앞에 있는 것을 사용
          separatorIndex = Math.min(firstNewlineIndex, firstPeriodIndex)
          console.log('🔍 [separateEvaluationAndNextQuestion] 줄바꿈과 마침표 모두 발견, 더 앞에 있는 것 사용:', separatorIndex === firstNewlineIndex ? '줄바꿈' : '마침표')
        } else if (firstNewlineIndex >= 0) {
          separatorIndex = firstNewlineIndex
          console.log('🔍 [separateEvaluationAndNextQuestion] 첫 번째 줄바꿈 발견, 인덱스:', separatorIndex)
        } else if (firstPeriodIndex >= 0) {
          separatorIndex = firstPeriodIndex
          console.log('🔍 [separateEvaluationAndNextQuestion] 첫 번째 마침표 발견, 인덱스:', separatorIndex)
        }

        if (separatorIndex >= 0) {
          // 구분자 이후의 내용만 추출
          nextQuestionText = afterPatternText.substring(separatorIndex + 1).trim()
          console.log('🔍 [separateEvaluationAndNextQuestion] 구분자 이후 텍스트:', nextQuestionText.substring(0, 100))
        } else {
          // 줄바꿈이나 마침표가 없으면 전체를 질문으로 간주 (하지만 평가 마무리 표현 제거 시도)
          // "으로 넘어가겠습니다." 같은 표현 제거
          const trimmedAfter = afterPatternText.trim()
          const transitionPatterns = [
            /^으로\s*넘어가겠습니다[.。]?\s*/i,
            /^으로\s*이동하겠습니다[.。]?\s*/i,
            /^로\s*넘어가겠습니다[.。]?\s*/i,
            /^로\s*이동하겠습니다[.。]?\s*/i,
            /^Now\s*let['\s]*s\s*move\s*on[.。]?\s*/i,
            /^Let['\s]*s\s*move\s*on[.。]?\s*/i,
          ]

          let cleanedText = trimmedAfter
          for (const pattern of transitionPatterns) {
            cleanedText = cleanedText.replace(pattern, '').trim()
          }

          // 전환 표현을 제거한 후에도 내용이 있으면 질문으로 간주
          if (cleanedText.length > 0) {
            nextQuestionText = cleanedText
            console.log('🔍 [separateEvaluationAndNextQuestion] 구분자 없음, 전환 표현 제거 후:', nextQuestionText.substring(0, 100))
          } else {
            // 전환 표현만 있고 질문이 없으면 빈 문자열
            nextQuestionText = ''
            console.log('🔍 [separateEvaluationAndNextQuestion] 전환 표현만 있고 질문 없음')
          }
        }

        console.log('🔍 [separateEvaluationAndNextQuestion] 분리 성공!')
        console.log('🔍 [separateEvaluationAndNextQuestion] 평가 텍스트:', evaluationText)
        console.log('🔍 [separateEvaluationAndNextQuestion] 평가 텍스트 길이:', evaluationText.length)
        console.log('🔍 [separateEvaluationAndNextQuestion] 다음 질문 텍스트:', nextQuestionText)
        console.log('🔍 [separateEvaluationAndNextQuestion] 다음 질문 텍스트 길이:', nextQuestionText.length)
        return {
          evaluationText,
          nextQuestionText
        }
      }

      // 다음 질문 패턴이 없으면 전체를 평가로 간주
      console.log('🔍 [separateEvaluationAndNextQuestion] 질문 패턴을 찾지 못함, 전체를 평가로 간주')
      console.log('🔍 [separateEvaluationAndNextQuestion] 반환: 전체를 평가로, 질문 없음')
      return {
        evaluationText: aiResponse,
        nextQuestionText: ''
      }
    },

    /**
     * AI 응답에서 평가 내용 추출 (80% 기준으로 맞춤/틀림 판단)
     */
    extractEvaluationFromAIResponse(aiResponse, userAnswer) {
      if (!aiResponse || !userAnswer) return null

      console.log('🔍 [extractEvaluationFromAIResponse] 정확도 추출 시작')
      console.log('🔍 [extractEvaluationFromAIResponse] AI 응답:', aiResponse)
      console.log('🔍 [extractEvaluationFromAIResponse] 사용자 답변:', userAnswer)

      // AI 응답에서 평가 관련 키워드 찾기 (소수점 포함 패턴 추가)
      const evaluationKeywords = [
        /정확도[^\d]*(\d+(?:\.\d+)?)[^\d]*%/i,
        /accuracy[^\d]*(\d+(?:\.\d+)?)[^\d]*%/i,
        /(\d+(?:\.\d+)?)[^\d]*%[^\d]*정확/i,
        /(\d+(?:\.\d+)?)[^\d]*%[^\d]*맞/i,
        /(\d+(?:\.\d+)?)[^\d]*%[^\d]*correct/i,
        /맞[^\d]*(\d+(?:\.\d+)?)[^\d]*%/i,
        /correct[^\d]*(\d+(?:\.\d+)?)[^\d]*%/i,
        // 소수점 포함 패턴 추가
        /(\d+\.\d+)[^\d]*%/i,
        /(\d+)[^\d]*\.\s*(\d+)[^\d]*%/i, // "63.3%" 또는 "63 . 3%" 같은 패턴
      ]

      let accuracy = null
      let matchedPattern = null
      for (let i = 0; i < evaluationKeywords.length; i++) {
        const pattern = evaluationKeywords[i]
        const match = aiResponse.match(pattern)
        if (match) {
          console.log(`🔍 [extractEvaluationFromAIResponse] 패턴 ${i + 1} 매칭됨:`, pattern.toString(), match)
          // 두 번째 패턴의 경우 두 숫자를 합침 (예: "63 . 3" -> 63.3)
          if (i === 8 && match[1] && match[2]) {
            accuracy = parseFloat(`${match[1]}.${match[2]}`)
          } else if (match[1]) {
            accuracy = parseFloat(match[1])
          }
          matchedPattern = pattern.toString()
          console.log(`🔍 [extractEvaluationFromAIResponse] 추출된 정확도: ${accuracy}% (패턴: ${matchedPattern})`)
          break
        }
      }

      // 사용자 답변에 "모르겠습니다" 같은 표현이 있는지 확인
      const userAnswerLower = userAnswer.toLowerCase()
      const userDoesntKnowPatterns = [
        /모르겠/i, /잘\s*모르/i, /모름/i, /알\s*수\s*없/i,
        /don't\s*know/i, /don't\s*understand/i, /no\s*idea/i, /not\s*sure/i,
        /잘\s*모르겠습니다/i, /모르겠습니다/i, /모르겠어요/i
      ]
      
      const userDoesntKnow = userDoesntKnowPatterns.some(pattern => pattern.test(userAnswerLower))
      
      // AI가 정확도를 높게 주었더라도, 사용자가 "모르겠습니다"라고 답변했다면 0점으로 조정
      if (userDoesntKnow && accuracy !== null && accuracy > 0) {
        console.log('🔍 [extractEvaluationFromAIResponse] 사용자 답변에 "모르겠습니다" 표현 감지 + AI가 정확도 부여 → 0점으로 조정')
        console.log(`🔍 [extractEvaluationFromAIResponse] AI 정확도: ${accuracy}% → 0%로 조정 (사용자가 모르겠다고 답변)`)
        accuracy = 0 // "모르겠습니다" 같은 답변은 0점으로 간주
      }

      // 정확도를 찾지 못한 경우, 긍정/부정 키워드로 판단
      if (accuracy === null) {
        console.log('🔍 [extractEvaluationFromAIResponse] 정확도 숫자를 찾지 못함, 키워드 기반 판단 시작')
        
        // 사용자 답변에 "모르겠습니다" 같은 표현이 있으면 0점 부여
        if (userDoesntKnow) {
          console.log('🔍 [extractEvaluationFromAIResponse] 사용자 답변에 "모르겠습니다" 표현 감지 → 0점 부여')
          accuracy = 0 // "모르겠습니다" 같은 답변은 0점으로 간주
          console.log('🔍 [extractEvaluationFromAIResponse] 사용자가 모르겠다고 답변 → 0%')
        } else {
          const positiveKeywords = [
            /정확/i, /맞/i, /올바/i, /좋/i, /훌륭/i, /완벽/i,
            /correct/i, /right/i, /good/i, /excellent/i, /perfect/i,
            /성공/i, /success/i
          ]
          const negativeKeywords = [
            /부정확/i, /틀/i, /잘못/i, /부족/i, /개선/i, /어렵/i, /어려/i,
            /모르겠/i, /잘\s*모르/i, /모름/i, /알\s*수\s*없/i,
            /incorrect/i, /wrong/i, /insufficient/i, /improve/i,
            /difficult/i, /don't\s*know/i, /don't\s*understand/i, /no\s*idea/i
          ]

          const hasPositive = positiveKeywords.some(pattern => pattern.test(aiResponse))
          const hasNegative = negativeKeywords.some(pattern => pattern.test(aiResponse))

          console.log('🔍 [extractEvaluationFromAIResponse] 키워드 분석:', {
            hasPositive,
            hasNegative,
            positiveMatches: positiveKeywords.filter(p => p.test(aiResponse)).map(p => p.toString()),
            negativeMatches: negativeKeywords.filter(p => p.test(aiResponse)).map(p => p.toString())
          })

          if (hasPositive && !hasNegative) {
            accuracy = 85 // 긍정적 평가는 85%로 간주
            console.log('🔍 [extractEvaluationFromAIResponse] 긍정적 평가로 판단 → 85%')
          } else if (hasNegative && !hasPositive) {
            accuracy = 50 // 부정적 평가는 50%로 간주
            console.log('🔍 [extractEvaluationFromAIResponse] 부정적 평가로 판단 → 50%')
          } else {
            accuracy = 70 // 애매한 경우 70%로 간주
            console.log('🔍 [extractEvaluationFromAIResponse] 애매한 평가로 판단 → 70%')
          }
        }
      }

      // 80% 이상이면 맞춤으로 간주
      const isCorrect = accuracy >= 80

      console.log('🔍 [extractEvaluationFromAIResponse] 최종 결과:', {
        accuracy,
        isCorrect,
        matchedPattern,
        evaluationPreview: aiResponse.substring(0, 200)
      })

      return {
        accuracy,
        isCorrect,
        evaluation: aiResponse
      }
    },

    /**
     * 인터뷰 종료 확인
     */
    async confirmEndInterview() {
      this.showEndConfirmModal = false

      // ========== 마지막 문제 평가 확인 및 추가 ==========
      // 인터뷰 종료 전에 평가되지 않은 문제들을 확인하고 추가
      const actualTotalQuestions = this.originalQuestions?.length || this.questions?.length || this.totalQuestions || 0
      
      if (actualTotalQuestions > 0) {
        // 모든 문제 인덱스 확인 (0부터 actualTotalQuestions-1까지)
        for (let i = 0; i < actualTotalQuestions; i++) {
          // 이미 평가가 있는지 확인
          const existingEval = this.questionEvaluations.find(e => e.questionIndex === i)
          
          if (!existingEval) {
            // 평가가 없는 문제 찾기
            const questionObj = this.originalQuestions && this.originalQuestions[i]
              ? this.originalQuestions[i]
              : (this.questions && this.questions[i] ? this.questions[i] : null)
            
            if (questionObj) {
              // 질문 제목 가져오기
              const questionTitle = getLocalizedContentWithI18n(
                questionObj,
                'title',
                this.$i18n,
                this.language,
                `Question ${i + 1}`
              )
              
              // 사용자 답변 찾기 (conversationHistory에서)
              // 해당 문제에 해당하는 사용자 메시지 찾기
              let userAnswer = ''
              
              // conversationHistory에서 해당 문제 이후의 사용자 메시지 찾기
              // 간단하게: conversationHistory에서 user 메시지를 찾되, 
              // 문제 순서대로 매핑 (첫 번째 문제 = 첫 번째 user 메시지)
              const userMessages = []
              let questionCount = 0
              for (const msg of this.conversationHistory) {
                if (msg.role === 'assistant') {
                  questionCount++
                } else if (msg.role === 'user' && msg.content && msg.content.trim()) {
                  // 해당 문제에 해당하는 사용자 메시지인지 확인
                  // questionCount가 i+1일 때 (해당 문제 이후) 사용자 메시지 찾기
                  if (questionCount === i + 1 || (userMessages.length === 0 && questionCount > i)) {
                    userMessages.push(msg.content)
                  }
                }
              }
              
              if (userMessages.length > 0) {
                userAnswer = userMessages[0]
              } else {
                // 사용자 메시지를 찾지 못한 경우
                userAnswer = this.language === 'ko' ? '(답변 없음)' : '(No answer)'
              }
              
              // 평가되지 않은 문제는 틀린 것으로 기록
              this.questionEvaluations.push({
                questionIndex: i,
                questionTitle: questionTitle,
                userAnswer: userAnswer,
                aiEvaluation: this.language === 'ko' 
                  ? '인터뷰 종료 시 평가 미완료 처리'
                  : 'Evaluation incomplete at interview end',
                isCorrect: false,
                accuracy: 0
              })
              
              console.log('🔍 [confirmEndInterview] 평가되지 않은 문제 추가:', {
                questionIndex: i,
                questionTitle: questionTitle.substring(0, 50),
                userAnswer: userAnswer.substring(0, 50)
              })
              debugLog('📝 [confirmEndInterview] 평가 기록 추가 (미완료):', {
                questionIndex: i,
                questionTitle: questionTitle.substring(0, 50)
              })
            }
          }
        }
      }
      // ========== 평가 확인 완료 ==========

      // 문제별 평가 결과를 DB에 저장
      await this.saveInterviewResults()

      // 결과 모달 표시 - 한 문제라도 풀었다면 통계 정보 보여주기
      // 문제가 총 2문제였는데 한 문제라도 풀었다면 통계 정보 표시
      if (this.questionEvaluations.length > 0) {
        this.showResultsModal = true
      } else {
        // 평가 기록이 없으면 바로 종료
        await this.cleanup()
        this.$emit('interview-ended')
      }
    },

    /**
     * 결과 모달 닫기
     */
    async closeResultsModal() {
      this.showResultsModal = false
      await this.cleanup()
      this.$emit('interview-ended')
    },

    /**
     * 인터뷰 결과 다운로드 (CSV 형식)
     */
    downloadResults() {
      if (!this.questionEvaluations || this.questionEvaluations.length === 0) {
        debugLog('⚠️ 다운로드할 결과가 없습니다')
        return
      }

      try {
        // CSV 헤더
        const headers = [
          '#',
          this.$t('voiceInterview.question') || '문제',
          this.$t('voiceInterview.yourAnswer') || '답변',
          this.$t('voiceInterview.evaluation') || '평가 내용',
          this.$t('voiceInterview.accuracy') || '정확도',
          this.$t('voiceInterview.result') || '결과'
        ]

        // CSV 데이터 생성
        const rows = this.questionEvaluations.map((evaluation, index) => {
          return [
            index + 1,
            evaluation.questionTitle || '',
            evaluation.userAnswer || '',
            evaluation.aiEvaluation || '',
            `${evaluation.accuracy || 0}%`,
            evaluation.isCorrect ? (this.$t('voiceInterview.correct') || '정답') : (this.$t('voiceInterview.wrong') || '오답')
          ]
        })

        // CSV 내용 생성
        const csvContent = [
          headers.join(','),
          ...rows.map(row => row.map(cell => {
            // 셀 내용에 쉼표나 따옴표가 있으면 따옴표로 감싸고 내부 따옴표는 이스케이프
            const cellStr = String(cell || '').replace(/"/g, '""')
            if (cellStr.includes(',') || cellStr.includes('"') || cellStr.includes('\n')) {
              return `"${cellStr}"`
            }
            return cellStr
          }).join(','))
        ].join('\n')

        // BOM 추가 (한글 깨짐 방지)
        const BOM = '\uFEFF'
        const blob = new Blob([BOM + csvContent], { type: 'application/vnd.ms-excel;charset=utf-8;' })
        
        // 파일명 생성 (Excel에서 바로 열 수 있도록 .xls 확장자 사용)
        const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-')
        const filename = `인터뷰_결과_${timestamp}.xls`

        // 다운로드
        const link = document.createElement('a')
        const url = URL.createObjectURL(blob)
        link.setAttribute('href', url)
        link.setAttribute('download', filename)
        link.style.visibility = 'hidden'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)

        debugLog('✅ 인터뷰 결과 다운로드 완료:', filename)
      } catch (error) {
        debugLog('❌ 인터뷰 결과 다운로드 실패:', error)
        console.error('다운로드 오류:', error)
      }
    },

    /**
     * 인터뷰 결과를 DB에 저장
     */
    async saveInterviewResults() {
      if (!this.examId || this.questionEvaluations.length === 0) {
        debugLog('⚠️ 인터뷰 결과 저장 건너뜀: examId 또는 평가 기록 없음')
        return
      }

      try {
        // 시험 문제 목록 로드 (아직 없는 경우)
        if (this.examQuestions.length === 0) {
          const response = await api.get(`/api/exam/${this.examId}/questions/`)
          this.examQuestions = response.data || []
        }

        // 평가 기록을 answers 형식으로 변환
        const answers = this.questionEvaluations.map(evaluation => {
          // 문제 ID 찾기
          const question = this.examQuestions.find(q => {
            // 사용자 프로필 언어에 맞는 제목 사용
            const title = getLocalizedContentWithI18n(
              q,
              'title',
              this.$i18n,
              this.userProfileLanguage || this.language,
              ''
            )
            return title && evaluation.questionTitle && (
              title.includes(evaluation.questionTitle.substring(0, 20)) ||
              evaluation.questionTitle.includes(title.substring(0, 20))
            )
          })

          return {
            question_id: question ? question.id : null,
            answer: evaluation.userAnswer,
            is_correct: evaluation.isCorrect,
            elapsed_seconds: 0, // 인터뷰에서는 시간 추적 안 함
            evaluation: evaluation.aiEvaluation || '' // AI 평가 내용 추가
          }
        }).filter(a => a.question_id !== null) // question_id가 있는 것만

        if (answers.length === 0) {
          debugLog('⚠️ 저장할 답안이 없음')
          // 답안이 없어도 저장은 시도 (에러를 throw하지 않음)
          // 대신 빈 answers 배열로 저장 시도
        }

        // 시험 결과 저장 API 호출 (Voice Interview 플래그 추가)
        // Voice Interview 결과는 데이터가 많을 수 있으므로 타임아웃을 60초로 설정
        const response = await api.post('/api/submit-exam/', {
          exam_id: this.examId,
          answers: answers,
          elapsed_seconds: this.elapsedTime,
          is_voice_interview: true // Voice Interview 모드 플래그
        }, {
          timeout: 60000 // 60초 타임아웃
        })

        debugLog('📝 저장 API 응답:', {
          status: response.status,
          data: response.data,
          hasExamResult: !!(response.data && response.data.exam_result),
          examResultId: response.data?.exam_result?.id
        })

        // 저장된 결과 ID 저장 (공유 기능용)
        if (response.data && response.data.exam_result && response.data.exam_result.id) {
          this.savedResultId = response.data.exam_result.id
          debugLog('✅ 인터뷰 결과 저장 완료:', {
            examId: this.examId,
            answersCount: answers.length,
            savedResultId: this.savedResultId
          })
        } else {
          debugLog('⚠️ 저장 API 응답에 exam_result.id가 없음:', response.data)
          // 응답에 ID가 없어도 저장은 성공했을 수 있으므로 에러를 throw하지 않음
          // 하지만 savedResultId는 설정되지 않음
        }
      } catch (error) {
        debugLog('❌ 인터뷰 결과 저장 실패:', error)
        // 에러를 다시 throw하여 호출자가 처리할 수 있도록 함
        throw error
      }
    },

    /**
     * 결과보기 텍스트 가져오기
     */
    getViewResultsText() {
      try {
        const translation = this.$t('voiceInterview.viewResults')
        // 번역이 객체인 경우 fallback 사용
        if (translation && typeof translation === 'object' && !Array.isArray(translation)) {
          return this.$i18n.locale === 'en' ? 'View Results' : '결과보기'
        }
        // 번역이 키와 같으면 (번역 실패) fallback 사용
        if (translation === 'voiceInterview.viewResults') {
          return this.$i18n.locale === 'en' ? 'View Results' : '결과보기'
        }
        return translation || (this.$i18n.locale === 'en' ? 'View Results' : '결과보기')
      } catch (error) {
        return this.$i18n.locale === 'en' ? 'View Results' : '결과보기'
      }
    },

    /**
     * 결과보기 (결과 목록 페이지로 이동)
     */
    viewResultsList() {
      if (!this.examId) {
        debugLog('⚠️ 시험 ID가 없음')
        this.$toast?.error?.(this.$t('voiceInterview.viewResults.noExamId') || '시험 ID가 없습니다.')
        return
      }
      
      this.closeResultsModal()
      this.$router.push(`/exam/${this.examId}/voice-interview-results`)
    },

    /**
     * 결과 공유하기
     */
    async shareResults() {
      if (!this.examId) {
        debugLog('⚠️ 시험 ID가 없음')
        this.$toast?.error?.(this.$t('voiceInterview.share.noExamId') || '시험 ID가 없습니다.')
        return
      }

      // 결과가 저장되지 않았으면 먼저 저장 시도
      if (!this.savedResultId) {
        debugLog('⚠️ 저장된 결과 ID가 없음, 결과 저장 시도...')
        
        // 저장할 평가 기록이 있는지 확인
        if (!this.questionEvaluations || this.questionEvaluations.length === 0) {
          this.$toast?.error?.(this.$t('voiceInterview.share.noResults') || '저장할 결과가 없습니다.')
          return
        }
        
        try {
          // 저장 중 표시
          if (this.$toast) {
            this.$toast.info(this.$t('voiceInterview.share.saving') || '결과를 저장하는 중...')
          }
          
          await this.saveInterviewResults()
          
          // 저장 후에도 savedResultId가 없으면 에러
          if (!this.savedResultId) {
            debugLog('❌ 결과 저장 후에도 savedResultId가 없음')
            this.$toast?.error?.(this.$t('voiceInterview.share.saveFailed') || '결과 저장에 실패했습니다.')
            return
          }
          
          debugLog('✅ 결과 저장 완료, savedResultId:', this.savedResultId)
        } catch (error) {
          console.error('결과 저장 실패:', error)
          
          // 타임아웃 에러인 경우 특별한 메시지 표시
          let errorMessage = this.$t('voiceInterview.share.saveFailed') || '결과 저장에 실패했습니다.'
          
          if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
            errorMessage = this.$t('voiceInterview.share.saveTimeout') || '결과 저장에 시간이 오래 걸려 타임아웃이 발생했습니다. 잠시 후 다시 시도해주세요.'
          } else if (error.response?.data?.error) {
            errorMessage = error.response.data.error
          } else if (error.message) {
            errorMessage = error.message
          }
          
          this.$toast?.error?.(errorMessage)
          return
        }
      }

      // 공유 모달 열기
      this.showShareModal = true
      
      // 연결된 스터디 로드
      await this.loadConnectedStudies()
    },

    /**
     * 연결된 스터디 로드
     */
    async loadConnectedStudies() {
      try {
        const response = await api.get(`/api/exam/${this.examId}/connected-studies/`)
        if (response.data.success) {
          this.connectedStudies = response.data.connected_studies || []
        } else {
          this.connectedStudies = []
        }
      } catch (error) {
        console.error('연결된 스터디 로드 실패:', error)
        this.connectedStudies = []
      }
    },

    /**
     * 스터디 멤버 로드
     */
    async loadStudyMembers() {
      if (!this.selectedStudyId) {
        this.studyMembers = []
        this.selectedMemberIds = []
        return
      }

      try {
        const response = await api.get(`/api/studies/${this.selectedStudyId}/members/`)
        // 활성화된 멤버만 필터링
        this.studyMembers = (response.data || []).filter(member => member.is_active === true)
        this.selectedMemberIds = []
      } catch (error) {
        console.error('스터디 멤버 로드 실패:', error)
        this.studyMembers = []
        this.selectedMemberIds = []
      }
    },

    /**
     * 전체 멤버 선택
     */
    selectAllMembers() {
      this.selectedMemberIds = this.membersWithEmail.map(m => m.id)
    },

    /**
     * 전체 멤버 해제
     */
    deselectAllMembers() {
      this.selectedMemberIds = []
    },

    /**
     * 공유 이메일 전송
     */
    async sendShareEmails() {
      if (!this.savedResultId || !this.selectedStudyId || this.selectedMemberIds.length === 0) {
        return
      }

      this.sendingEmails = true

      try {
        const response = await api.post('/api/voice-interview-result/share/', {
          result_id: this.savedResultId,
          study_id: this.selectedStudyId,
          member_ids: this.selectedMemberIds
        })

        if (response.data.success) {
          if (this.$toast) {
            this.$toast.success(
              this.$t('voiceInterview.share.success') || 
              `${this.selectedMemberIds.length}명에게 이메일이 전송되었습니다.`
            )
          }
          this.closeShareModal()
        } else {
          if (this.$toast) {
            this.$toast.error(
              response.data.error || 
              this.$t('voiceInterview.share.error') || 
              '이메일 전송에 실패했습니다.'
            )
          }
        }
      } catch (error) {
        console.error('이메일 전송 실패:', error)
        if (this.$toast) {
          this.$toast.error(
            error.response?.data?.error || 
            this.$t('voiceInterview.share.error') || 
            '이메일 전송에 실패했습니다.'
          )
        }
      } finally {
        this.sendingEmails = false
      }
    },

    /**
     * 공유 모달 닫기
     */
    closeShareModal() {
      this.showShareModal = false
      this.selectedStudyId = null
      this.studyMembers = []
      this.selectedMemberIds = []
    },

    /**
     * 공유를 위한 스터디 생성 (Exam 이름으로)
     */
    async createStudyForSharing() {
      if (!this.examId) {
        this.$toast?.error?.(this.$t('voiceInterview.share.noExamId') || '시험 ID가 없습니다.')
        return
      }

      this.isCreatingStudy = true

      try {
        // 시험 정보 가져오기
        const examResponse = await api.get(`/api/exam/${this.examId}/`)
        const exam = examResponse.data

        // 사용자 프로필 언어 가져오기 (기본값은 'en')
        const currentLang = await this.getUserProfileLanguage()

        // 스터디와 Task 생성
        const study = await createStudyAndTaskForSharing(this, exam, currentLang)

        debugLog('✅ 스터디 생성 완료:', study)

        // 성공 메시지 표시
        if (this.$toast) {
          this.$toast.success(
            this.$t('voiceInterview.share.studyCreated') || 
            '그룹이 생성되었습니다.'
          )
        }

        // 연결된 스터디 목록 새로고침
        await this.loadConnectedStudies()

        // 생성된 스터디 자동 선택
        if (study && study.id) {
          this.selectedStudyId = study.id
          await this.loadStudyMembers()
        }
      } catch (error) {
        console.error('스터디 생성 실패:', error)
        let errorMessage = this.$t('voiceInterview.share.studyCreationFailed') || '그룹 생성에 실패했습니다.'
        
        if (error.response?.status === 400 && error.response?.data?.error) {
          errorMessage = error.response.data.error
        } else if (error.response?.data?.study) {
          // 스터디는 생성되었지만 Task 생성 실패
          errorMessage = this.$t('voiceInterview.share.taskCreationFailed') || 'Task 생성에 실패했습니다.'
        }

        this.$toast?.error?.(errorMessage)
      } finally {
        this.isCreatingStudy = false
      }
    },

    /**
     * 사용자 프로필 언어 가져오기 (캐시 사용)
     */
    async getUserProfileLanguage() {
      // 캐시된 언어가 있으면 사용
      if (this.userProfileLanguage) {
        return this.userProfileLanguage
      }
      
      try {
        // props로 전달된 language를 먼저 확인
        if (this.language) {
          this.userProfileLanguage = this.language
          return this.userProfileLanguage
        }
        
        // i18n locale을 확인
        if (this.$i18n && this.$i18n.locale) {
          this.userProfileLanguage = this.$i18n.locale
          return this.userProfileLanguage
        }
        
        // API에서 프로필 언어 가져오기
        const response = await api.get('/api/user-profile/')
        const language = response.data?.language || 'en'
        this.userProfileLanguage = language
        return language
      } catch (error) {
        console.error('사용자 프로필 언어 가져오기 실패:', error)
        // 기본 언어는 'en'
        this.userProfileLanguage = 'en'
        return 'en'
      }
    },

    /**
     * 스터디 제목을 사용자 프로필 언어에 맞게 반환
     */
    getStudyTitle(study) {
      if (!study) return '제목 없음'
      return getLocalizedContentWithI18n(
        study,
        'title',
        this.$i18n,
        this.userProfileLanguage,
        '제목 없음'
      )
    },

    /**
     * 재연결 시도
     */
    async retryConnection() {
      await this.initializeInterview()
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

    /**
     * Instructions를 히스토리에 추가 (필수 규칙 숨김)
     * 세션 생성 전에 호출되어 히스토리에 먼저 표시됨
     */
    addInstructionsToHistory() {
      if (!this.instructions || !this.instructions.trim()) {
        console.error('❌ [addInstructionsToHistory] Instructions가 비어있습니다!')
        return
      }

      console.log('🔵🔵🔵 [addInstructionsToHistory] Instructions 히스토리 추가 시작! 🔵🔵🔵')
      console.log('🔵 [addInstructionsToHistory] instructions 길이:', this.instructions.length)

      // 필수 규칙 부분은 대화 히스토리에서 숨김 (AI에게는 전체 전달하지만 화면에는 표시 안 함)
      let displayText = this.instructions

      // 필수 규칙 마커 찾기
      const mandatoryRulesMarkers = [
        '=== 필수 규칙 (자동 추가) ===',
        '=== Mandatory Rules (Auto Added) ==='
      ]

      let found = false
      for (const marker of mandatoryRulesMarkers) {
        const markerIndex = displayText.indexOf(marker)
        if (markerIndex !== -1) {
          // 마커가 포함된 줄의 시작 위치 찾기 (이전 줄바꿈부터)
          let cutIndex = displayText.lastIndexOf('\n', markerIndex - 1)

          // 마커 앞의 빈 줄들도 제거
          if (cutIndex !== -1) {
            // 이전 줄바꿈 앞의 빈 줄들 확인
            let checkIndex = cutIndex
            while (checkIndex > 0 && (displayText[checkIndex - 1] === '\n' || displayText[checkIndex - 1] === '\r')) {
              checkIndex--
            }
            const prevNewline = displayText.lastIndexOf('\n', checkIndex - 1)
            if (prevNewline !== -1) {
              const betweenText = displayText.substring(prevNewline + 1, checkIndex).trim()
              if (betweenText === '') {
                cutIndex = prevNewline
              }
            }
            cutIndex++ // 줄바꿈 다음부터 시작
          } else {
            cutIndex = 0
          }

          displayText = displayText.substring(0, cutIndex).trim()
          found = true
          console.log('🔵🔵🔵 [addInstructionsToHistory] 필수 규칙 부분 제거됨! 🔵🔵🔵')
          console.log('🔵 [addInstructionsToHistory] 마커:', marker)
          console.log('🔵 [addInstructionsToHistory] 마커 위치:', markerIndex, '제거 위치:', cutIndex)
          console.log('🔵 [addInstructionsToHistory] 원본 길이:', this.instructions.length, '→ 표시 길이:', displayText.length)
          console.log('🔵 [addInstructionsToHistory] 표시할 텍스트 끝부분:', displayText.substring(Math.max(0, displayText.length - 150)))
          break
        }
      }

      if (!found) {
        console.warn('⚠️⚠️⚠️ [addInstructionsToHistory] 필수 규칙 마커를 찾을 수 없습니다! ⚠️⚠️⚠️')
        console.warn('⚠️ [addInstructionsToHistory] instructions 전체 길이:', this.instructions.length)
        console.warn('⚠️ [addInstructionsToHistory] instructions 끝부분 (200자):', this.instructions.substring(Math.max(0, this.instructions.length - 200)))
      }

      // 대화 기록에 추가 (사용자 메시지로) - 임시 주석 처리
      // Instructions 히스토리 추가를 주석 처리 (최초 한 번 그려지고 나중에 다시 업데이트되는 것 방지)
      // this.conversationHistory.push({
      //   type: 'user',
      //   text: `[Instructions 전송]\n${displayText}`,
      //   timestamp: new Date().toISOString()
      // })

      // console.log('✅✅✅ [addInstructionsToHistory] Instructions 히스토리 추가 완료! ✅✅✅')
      // console.log('✅ [addInstructionsToHistory] 히스토리 항목 수:', this.conversationHistory.length)

      // 스크롤을 맨 아래로
      // this.$nextTick(() => {
      //   this.scrollToBottom()
      // })
    },

    /**
     * Instructions를 텍스트로 AI에게 전송
     * WebSocket이 연결된 후에 호출됨
     * @param {string} instructionsToSend - 전송할 Instructions (선택적, 없으면 this.instructions 사용)
     */
    /**
     * Instructions 전송 (Chat API 방식에서는 사용하지 않음)
     */
    async sendInstructionsAsText() {
      // Chat API 방식에서는 Instructions를 초기화 시점에 전달하므로 이 메서드는 사용하지 않음
      debugLog('⚠️ sendInstructionsAsText는 Chat API 방식에서 사용하지 않습니다.')
      return
    },

    /**
     * 대화 기록 컨테이너를 맨 아래로 스크롤
     */
    scrollToBottom() {
      this.$nextTick(() => {
        if (this.$refs.conversationContainer) {
          const container = this.$refs.conversationContainer
          // 스크롤을 맨 아래로 이동 (부드러운 스크롤)
          // requestAnimationFrame을 사용하여 DOM 업데이트 후 스크롤
          requestAnimationFrame(() => {
            container.scrollTo({
              top: container.scrollHeight,
              behavior: 'smooth'
            })
            // 추가로 한 번 더 확인 (일부 경우 스크롤이 제대로 적용되지 않을 수 있음)
            setTimeout(() => {
              if (container.scrollTop + container.clientHeight < container.scrollHeight - 10) {
                container.scrollTo({
                  top: container.scrollHeight,
                  behavior: 'smooth'
                })
              }
            }, 100)
          })
        }
      })
    },

    /**
     * transcription 영역을 맨 아래로 스크롤
     */
    scrollTranscriptionToBottom() {
      const container = this.$refs.transcriptionContainer
      if (container) {
        // 스크롤을 맨 아래로 이동 (부드러운 스크롤)
        container.scrollTo({
          top: container.scrollHeight,
          behavior: 'smooth'
        })
      }
    },

    /**
     * 타이머 시작
     */
    startTimer() {
      if (this.timerInterval) return

      this.startTime = Date.now() - (this.elapsedTime * 1000)
      this.timerInterval = setInterval(() => {
        if (!this.isPaused) {
          this.elapsedTime = Math.floor((Date.now() - this.startTime) / 1000)
        }
      }, 1000)
    },

    /**
     * 타이머 중지
     */
    stopTimer() {
      if (this.timerInterval) {
        clearInterval(this.timerInterval)
        this.timerInterval = null
      }
    },

    /**
     * 시간 포맷팅
     */
    formatTime(seconds) {
      const mins = Math.floor(seconds / 60)
      const secs = seconds % 60
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    },

    /**
     * 정리
     */
    /**
     * Speech Recognition 안전하게 시작 (중복 호출 방지)
     */
    safeStartSpeechRecognition(context = 'unknown') {
      if (!this.speechRecognition) {
        debugLog(`⚠️ [safeStartSpeechRecognition] ${context}: speechRecognition이 없습니다.`)
        return false
      }

      // 이미 청취 중이면 시작하지 않음
      if (this.isListening) {
        debugLog(`⚠️ [safeStartSpeechRecognition] ${context}: 이미 청취 중입니다.`)
        return false
      }

      // SpeechRecognition의 상태 확인 (가능한 경우)
      // 일부 브라우저에서는 state 속성을 지원하지 않을 수 있음
      try {
        if (this.speechRecognition.state) {
          const state = this.speechRecognition.state
          if (state === 'listening' || state === 'starting') {
            debugLog(`⚠️ [safeStartSpeechRecognition] ${context}: recognition 상태가 이미 ${state}입니다.`)
            this.isListening = true // 상태 동기화
            return false
          }
        }
      } catch (e) {
        // state 속성이 없거나 접근할 수 없는 경우 무시
      }

      try {
        debugLog(`🎤 [safeStartSpeechRecognition] ${context}: Speech Recognition 시작 시도`)
        this.speechRecognition.start()
        return true
      } catch (err) {
        // "already started" 오류는 무시 (상태 동기화만 수행)
        if (err.name === 'InvalidStateError' || err.message?.includes('already started')) {
          debugLog(`⚠️ [safeStartSpeechRecognition] ${context}: 이미 시작된 상태입니다. (오류 무시)`)
          this.isListening = true // 상태 동기화
          return false
        }
        // 다른 오류는 로그 출력
        console.error(`❌ [safeStartSpeechRecognition] ${context}: Speech Recognition start() 실패:`, err)
        return false
      }
    },

    /**
     * Speech Recognition 초기화 (STT)
     */
    async setupSpeechRecognition() {
      try {
        debugLog('🔍 [setupSpeechRecognition] 함수 시작')

        // 플랫폼 확인
        const platform = typeof window !== 'undefined' && window.Capacitor && typeof window.Capacitor.getPlatform === 'function'
          ? window.Capacitor.getPlatform()
          : 'web'

        debugLog('🔍 [setupSpeechRecognition] 플랫폼 확인:', { platform, hasWindow: typeof window !== 'undefined', hasCapacitor: typeof window !== 'undefined' && !!window.Capacitor })

        // iOS 네이티브 STT 사용
        if (platform === 'ios') {
          try {
            debugLog('🔍 [setupSpeechRecognition] iOS 네이티브 STT 플러그인 import 시작')
            const { SpeechRecognition, provider } = await this.loadSpeechPlugin()
            debugLog('🔍 [setupSpeechRecognition] 사용 플러그인:', { provider, hasSpeechRecognition: !!SpeechRecognition })
            debugLog('🔍 [setupSpeechRecognition] iOS 네이티브 STT 플러그인 import 완료:', { hasSpeechRecognition: !!SpeechRecognition, hasHasPermission: typeof SpeechRecognition.hasPermission === 'function', hasRequestPermission: typeof SpeechRecognition.requestPermission === 'function' })

            this.nativeSTT = SpeechRecognition
            this.isUsingNativeSTT = true
            debugLog('✅ [setupSpeechRecognition] iOS 네이티브 STT 플러그인 로드 완료')

            // 권한이 이미 보장된 경우 빠른 경로로 완료 처리
            if (this.sttPermissionEnsured) {
              debugLog('✅ [setupSpeechRecognition] sttPermissionEnsured=true → 권한 확인/요청 스킵')
              return
            }

            // 권한 확인 및 요청
            debugLog('🔍 [setupSpeechRecognition] 권한 확인 시작 - hasPermission() 호출 전')
            debugLog('🔍 [setupSpeechRecognition] SpeechRecognition 객체 확인:', {
              hasSpeechRecognition: !!SpeechRecognition,
              speechRecognitionType: typeof SpeechRecognition,
              hasHasPermission: typeof SpeechRecognition.hasPermission === 'function',
              hasRequestPermission: typeof SpeechRecognition.requestPermission === 'function'
            })

            // hasPermission() 호출 (타임아웃 처리 포함)
            let hasPermission = null
            let permissionCheckTimedOut = false

            try {
              debugLog('🔍 [setupSpeechRecognition] hasPermission() 호출 시작 - await 전')

              // Promise.race로 타임아웃 처리 (최대 12초 대기)
              const { hasPerm } = this.getPermissionFns(SpeechRecognition)
              const permissionCheckPromise = typeof hasPerm === 'function' ? hasPerm() : Promise.resolve(null)
              const timeoutPromise = new Promise((resolve) => {
                setTimeout(() => {
                  permissionCheckTimedOut = true
                  console.error('❌ [setupSpeechRecognition] hasPermission() 호출 타임아웃 (12초 초과)')
                  debugLog('❌ [setupSpeechRecognition] hasPermission() 타임아웃 - Promise가 resolve되지 않음, requestPermission()으로 폴백')
                  resolve(null) // 타임아웃 시 null 반환
                }, 12000)
              })

              hasPermission = await Promise.race([permissionCheckPromise, timeoutPromise])

              if (permissionCheckTimedOut) {
                debugLog('⚠️ [setupSpeechRecognition] hasPermission() 타임아웃 발생 - iOS에서 네이티브 유지')
                hasPermission = null // 타임아웃 시 권한 없음으로 간주
                this.isUsingNativeSTT = true
                this.nativeSTT = SpeechRecognition
                this.showMicPermissionPrompt = true
                this.errorMessage = (this.$t && this.$t('voiceInterview.iosMicPermissionTimeout')) || 'iOS microphone permission timed out. Please enable microphone in Settings and retry.'
              } else {
                debugLog('🔍 [setupSpeechRecognition] hasPermission() 호출 완료 - await 후')
                debugLog('🔍 [setupSpeechRecognition] 권한 확인 결과:', {
                  hasPermission: hasPermission?.permission,
                  fullResult: hasPermission,
                })
              }
            } catch (error) {
              console.error('❌ [setupSpeechRecognition] hasPermission() 호출 중 에러:', error)
              debugLog('❌ [setupSpeechRecognition] hasPermission() 에러 상세:', {
                errorMessage: error.message,
                errorStack: error.stack,
                errorName: error.name
              })
              // 에러 발생 시 권한 없음으로 간주하고 requestPermission()으로 진행
              hasPermission = null
            }

            if (!hasPermission || !hasPermission?.permission) {
              debugLog('🔍 [setupSpeechRecognition] 권한 없음 - requestPermission() 호출 (fire-and-forget)')

              // GettingStarted.vue와 동일: fire-and-forget 방식 (대기하지 않음)
              try {
                const { requestPerm } = this.getPermissionFns(SpeechRecognition)
                if (typeof requestPerm === 'function') {
                  const reqPromise = requestPerm()
                  debugLog('🔍 [setupSpeechRecognition] requestPermission() 호출 (fire-and-forget):', reqPromise)
                  // 결과는 로그만 남기고 대기하지 않음
                  reqPromise.then((result) => {
                    debugLog('🔍 [setupSpeechRecognition] requestPermission() 결과:', result)
                  }).catch((e) => {
                    debugLog('🔍 [setupSpeechRecognition] requestPermission() 에러 (무시):', e)
                  })
                }
              } catch (error) {
                debugLog('🔍 [setupSpeechRecognition] requestPermission() 호출 에러 (무시):', error)
              }

              // 권한 요청을 기다리지 않고 바로 진행 (콘솔 흐름과 동일)
              debugLog('✅ [setupSpeechRecognition] requestPermission() 발사 완료, 다음 단계 진행')
            } else {
              debugLog('✅ [setupSpeechRecognition] 이미 권한 있음')
            }

            // iOS 네이티브 STT는 이벤트 기반이므로 별도 초기화 불필요
            debugLog('✅ [setupSpeechRecognition] iOS 네이티브 Speech Recognition 초기화 완료')
            return
          } catch (error) {
            console.error('❌ [setupSpeechRecognition] iOS 네이티브 STT 로드 실패, Web Speech API로 폴백:', error)
            debugLog('❌ [setupSpeechRecognition] iOS 네이티브 STT 에러 상세:', { errorMessage: error.message, errorStack: error.stack, errorName: error.name })
            // 폴백: Web Speech API 사용
          }
        }

        // Web Speech API 사용 (웹 또는 iOS 네이티브 실패 시)
        if (platform === 'ios') {
          // iOS에서는 Web Speech API 미지원 → 폴백 차단
          debugLog('⛔ [setupSpeechRecognition] iOS에서 Web Speech API 폴백 차단, 네이티브 권한 안내 표시')
          this.showMicPermissionPrompt = true
          this.errorMessage = (this.$t && this.$t('voiceInterview.iosMicPermissionRequired')) || 'Microphone permission is required on iOS. Please allow and retry.'
          return
        }
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
          throw new Error('이 브라우저는 음성 인식을 지원하지 않습니다.')
        }

        this.isUsingNativeSTT = false
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
        this.speechRecognition = new SpeechRecognition()
        this.speechRecognition.continuous = true
        this.speechRecognition.interimResults = true
        
        // 사용자 언어 가져오기 (localStorage 또는 i18n에서)
        const userLanguage = this.getUserLanguage()
        const sttLang = this.getSpeechRecognitionLang(userLanguage)
        this.speechRecognition.lang = sttLang
        debugLog('🔍 [setupSpeechRecognition] Web Speech API 언어 설정:', { userLanguage, sttLang })
        
        this.speechRecognition.maxAlternatives = 3

        this.speechRecognition.onstart = () => {
          debugLog('🎤 [STT] 음성 인식 시작')
          this.isListening = true
        }

        this.speechRecognition.onresult = (event) => {
          let finalTranscript = ''
          let interimTranscript = ''

          for (let i = event.resultIndex; i < event.results.length; i++) {
            const result = event.results[i]
            const transcript = result[0].transcript

            if (result.isFinal) {
              finalTranscript += transcript + ' '
            } else {
              interimTranscript += transcript
            }
          }

          if (finalTranscript) {
            const message = finalTranscript.trim()
            // finalTranscription에 누적 (중복 및 불필요한 텍스트 제거)
            let accumulatedMessage = ''
            if (this.finalTranscription) {
              // 기존 텍스트와 새 텍스트를 합치되, 중복된 부분 제거
              const existingText = this.finalTranscription.trim()
              const newText = message.trim()
              
              // 새 텍스트가 기존 텍스트의 끝부분과 중복되는지 확인
              // 예: "이상입니다" + "이상입니다. 입니다" → "이상입니다"만 유지
              if (existingText.endsWith(newText) || newText.endsWith(existingText)) {
                // 더 긴 텍스트를 사용하되, 불필요한 반복 제거
                accumulatedMessage = existingText.length > newText.length ? existingText : newText
              } else {
                // 중복이 없으면 공백으로 연결
                accumulatedMessage = existingText + ' ' + newText
              }
              
              // 불필요한 반복 패턴 제거
              // "이상입니다. 입니다" → "이상입니다"
              accumulatedMessage = accumulatedMessage.replace(/([^.\s]+)(\.\s*\1)+/g, '$1')
              // "입니다. 입니다" 같은 패턴 제거
              accumulatedMessage = accumulatedMessage.replace(/(입니다|이다|이에요|이예요)(\.\s*\1)+/gi, '$1')
              // "이상입니다. 입니다" 같은 패턴 제거 (더 정확한 패턴)
              accumulatedMessage = accumulatedMessage.replace(/([^.]+)(\.\s*입니다|\.\s*이다|\.\s*이에요|\.\s*이예요)+/gi, '$1')
              // 중복된 단어 제거 (예: "이상입니다 이상입니다" → "이상입니다")
              accumulatedMessage = accumulatedMessage.replace(/\b(\w+)\s+\1\b/gi, '$1')
            } else {
              accumulatedMessage = message
            }
            this.finalTranscription = accumulatedMessage.trim()
            this.interimTranscription = ''

            debugLog('🎤 [STT] finalTranscript 수신:', message)
            debugLog('🎤 [STT] 누적된 finalTranscription:', this.finalTranscription)

            // 종료 표현이 포함되어 있는지 확인
            if (this.isEndingMessage(accumulatedMessage)) {
              debugLog('🛑 [STT] 종료 표현 감지, 답변 내용만 추출:', accumulatedMessage)

              // 종료 표현 제거하고 답변 내용만 추출
              let userMessage = accumulatedMessage
              const endingPatterns = this.getEndingPatterns()

              for (const pattern of endingPatterns) {
                userMessage = userMessage.replace(pattern, '').trim()
              }

              // 타이머 클리어
              if (this.speakingEndTimer) {
                clearTimeout(this.speakingEndTimer)
                this.speakingEndTimer = null
              }

              // finalTranscription 초기화
              this.finalTranscription = ''
              this.interimTranscription = ''

              // 말하기 종료
              this.isUserSpeaking = false
              this.canSpeak = true

              // 답변 내용이 있으면 AI 평가 요청
              if (userMessage && userMessage.trim()) {
                debugLog('🛑 [STT] 종료 표현 제거 후 답변 내용:', userMessage)
                // 메시지 처리 (AI 평가 요청)
                this.handleUserMessage(userMessage.trim())
              } else {
                debugLog('🛑 [STT] 종료 표현만 있고 답변 내용 없음')
                // 답변이 없으면 단순히 말하기만 종료
              }

              return
            }

            // 사용자가 말하는 중이면, 일정 시간 후 말하기 종료 처리
            if (this.isUserSpeaking) {
              // 기존 타이머 클리어
              if (this.speakingEndTimer) {
                clearTimeout(this.speakingEndTimer)
              }

              // 1.5초 후에 말하기 종료 (사용자가 말을 끝냈다고 간주)
              this.speakingEndTimer = setTimeout(() => {
                if (this.isUserSpeaking && this.finalTranscription && this.finalTranscription.trim()) {
                  const finalMessage = this.finalTranscription.trim()
                  // 종료 표현 체크 - 종료 표현이 있을 때만 처리
                  if (this.isEndingMessage(finalMessage)) {
                    debugLog('🛑 [STT] 타이머 만료 시 종료 표현 감지, 답변 내용 추출:', finalMessage)

                    // 종료 표현 제거하고 답변 내용만 추출
                    let userMessage = finalMessage
                    const endingPatterns = this.getEndingPatterns()

                    for (const pattern of endingPatterns) {
                      userMessage = userMessage.replace(pattern, '').trim()
                    }

                    this.finalTranscription = ''
                    this.interimTranscription = ''
                    this.isUserSpeaking = false
                    this.canSpeak = true
                    this.speakingEndTimer = null

                    // 답변 내용이 있으면 AI 평가 요청
                    if (userMessage && userMessage.trim()) {
                      debugLog('🛑 [STT] 타이머 만료 시 종료 표현 제거 후 답변 내용:', userMessage)
                      // 메시지 처리 (AI 평가 요청)
                      this.handleUserMessage(userMessage.trim())
                    } else {
                      debugLog('🛑 [STT] 타이머 만료 시 종료 표현만 있고 답변 내용 없음')
                    }
                    return
                  }
                  
                  // 종료 표현이 없으면 타이머만 정리하고 계속 대기 (사용자가 아직 말하는 중일 수 있음)
                  debugLog('⏸️ [STT] 타이머 만료되었지만 종료 표현이 없음 - 계속 대기:', finalMessage)
                  // 타이머는 정리하되, 메시지는 처리하지 않음
                  // 사용자가 계속 말할 수 있도록 isUserSpeaking은 true로 유지
                  this.speakingEndTimer = null
                }
              }, 1500) // 1.5초 대기
            }
          } else {
            this.interimTranscription = interimTranscript
          }
        }

        this.speechRecognition.onerror = (event) => {
          debugLog('🎤 [STT] 오류:', event.error)
          if (event.error === 'no-speech') {
            // 무음 오류는 무시하고 재시작 (단, 인터뷰가 종료되지 않은 경우만)
            if (this.isConnected && !this.isPaused && !this.showResultsModal) {
              setTimeout(() => {
                // 재시작 전에 다시 한 번 상태 확인
                if (this.speechRecognition && !this.isListening && !this.showResultsModal && this.isConnected) {
                  this.safeStartSpeechRecognition('onerror no-speech')
                } else {
                  debugLog('🎤 [STT] onerror 자동 재시작 건너뜀:', {
                    hasRecognition: !!this.speechRecognition,
                    isListening: this.isListening,
                    showResultsModal: this.showResultsModal,
                    isConnected: this.isConnected
                  })
                }
              }, 1000)
            } else {
              debugLog('🎤 [STT] onerror 자동 재시작 조건 불만족:', {
                isConnected: this.isConnected,
                isPaused: this.isPaused,
                showResultsModal: this.showResultsModal
              })
            }
          }
        }

        this.speechRecognition.onend = () => {
          this.isListening = false
          debugLog('🎤 [STT] 음성 인식 종료 (onend)')

          // 타이머가 설정되어 있지 않고, 사용자가 말하는 중이었다면
          // finalTranscription이 있으면 즉시 처리 (타이머가 설정되지 않은 경우)
          if (this.isUserSpeaking && !this.speakingEndTimer) {
            if (this.finalTranscription && this.finalTranscription.trim()) {
              const message = this.finalTranscription.trim()
              // 종료 표현 체크
              if (this.isEndingMessage(message)) {
                debugLog('🛑 [STT] onend에서 종료 표현 감지, 답변 내용 추출:', message)

                // 종료 표현 제거하고 답변 내용만 추출
                let userMessage = message
                const endingPatterns = this.getEndingPatterns()

                for (const pattern of endingPatterns) {
                  userMessage = userMessage.replace(pattern, '').trim()
                }

                this.finalTranscription = ''
                this.interimTranscription = ''
                this.isUserSpeaking = false
                this.canSpeak = true

                // 답변 내용이 있으면 AI 평가 요청
                if (userMessage && userMessage.trim()) {
                  debugLog('🛑 [STT] onend에서 종료 표현 제거 후 답변 내용:', userMessage)
                  // 메시지 처리 (AI 평가 요청)
                  this.handleUserMessage(userMessage.trim())
                } else {
                  debugLog('🛑 [STT] onend에서 종료 표현만 있고 답변 내용 없음')
                  // 진행 중인 AI 응답 취소
                  if (this.isWaitingForResponse && this.abortController) {
                    this.abortController.abort()
                    this.abortController = null
                    this.isWaitingForResponse = false
                  }
                  // TTS 중지
                  if ('speechSynthesis' in window) {
                    speechSynthesis.cancel()
                  }
                  this.isAISpeaking = false
                }
              } else {
                debugLog('🎤 [STT] onend에서 즉시 처리:', message)
                this.isUserSpeaking = false
                this.canSpeak = true
                // 메시지 처리
                this.handleUserMessage(message)
              }
            }
          }

          // 인터뷰가 종료되었거나 결과 모달이 표시된 경우 재시작하지 않음
          if (this.isConnected && !this.isPaused && !this.showResultsModal) {
            // 자동 재시작
            setTimeout(() => {
              // 재시작 전에 다시 한 번 상태 확인 (인터뷰가 종료되지 않았는지)
              if (this.speechRecognition && !this.isListening && !this.showResultsModal && this.isConnected) {
                this.safeStartSpeechRecognition('onend auto-restart')
              } else {
                debugLog('🎤 [STT] onend 자동 재시작 건너뜀:', {
                  hasRecognition: !!this.speechRecognition,
                  isListening: this.isListening,
                  showResultsModal: this.showResultsModal,
                  isConnected: this.isConnected
                })
              }
            }, 500)
          } else {
            debugLog('🎤 [STT] onend 자동 재시작 조건 불만족:', {
              isConnected: this.isConnected,
              isPaused: this.isPaused,
              showResultsModal: this.showResultsModal
            })
          }
        }

        // 음성 인식 시작
        this.safeStartSpeechRecognition('setupSpeechRecognition')
        debugLog('✅ Speech Recognition 초기화 완료 (Web Speech API)')
      } catch (error) {
        debugLog('❌ Speech Recognition 초기화 실패:', error)
        throw error
      }
    },

    /**
     * iOS 네이티브 STT로 음성 인식 시작 (GettingStarted.vue 콘솔 흐름 방식)
     */
    async startNativeSTT() {
      debugLog('🔍 [startNativeSTT] 함수 시작:', { isUsingNativeSTT: this.isUsingNativeSTT, hasNativeSTT: !!this.nativeSTT })

      if (!this.isUsingNativeSTT || !this.nativeSTT) {
        debugLog('⚠️ [startNativeSTT] 네이티브 STT 사용 불가 - 함수 종료')
        return
      }

      try {
        const SR = this.nativeSTT

        // 콘솔 흐름과 동일: available, hasPermission, requestPermission (fire-and-forget)
        const a = SR.available()
        debugLog('[console-flow] SR.available() →', a)
        a.then((v) => debugLog('[console-flow] available result:', v))

        const hp = SR.hasPermission()
        debugLog('[console-flow] SR.hasPermission() →', hp)
        hp.then((v) => debugLog('[console-flow] hasPermission result:', v))

        // fire-and-forget (대기하지 않음)
        const rp = SR.requestPermission()
        debugLog('[console-flow] SR.requestPermission() →', rp)
        rp.then((v) => debugLog('[console-flow] requestPermission result:', v))

        // 기존 리스너 정리
        this.nativeSTTListeners.forEach(off => {
          try {
            if (off && typeof off === 'function') {
              off()
            } else if (off && typeof off.remove === 'function') {
              off.remove()
            }
          } catch (e) {
            debugLog('[console-flow] listener cleanup error (ignored):', e)
          }
        })
        this.nativeSTTListeners = []

        // 리스너 등록 (콘솔 흐름과 동일)
        const offResultHandle = await SR.addListener('result', async (data) => {
          debugLog('[result]', data)
          const matches = data?.matches || []
          if (Array.isArray(matches) && matches.length > 0) {
            const transcript = matches[0]

            // finalTranscription에 누적 (사용자가 말하는 중에는 누적만 하고 처리하지 않음)
            // 중복 및 불필요한 텍스트 제거
            if (this.finalTranscription) {
              const existingText = this.finalTranscription.trim()
              const newText = transcript.trim()
              
              // 새 텍스트가 기존 텍스트의 끝부분과 중복되는지 확인
              if (existingText.endsWith(newText) || newText.endsWith(existingText)) {
                // 더 긴 텍스트를 사용하되, 불필요한 반복 제거
                this.finalTranscription = existingText.length > newText.length ? existingText : newText
              } else {
                // 중복이 없으면 공백으로 연결
                this.finalTranscription = existingText + ' ' + newText
              }
              
              // 불필요한 반복 패턴 제거
              // "이상입니다. 입니다" → "이상입니다"
              this.finalTranscription = this.finalTranscription.replace(/([^.\s]+)(\.\s*\1)+/g, '$1')
              // "입니다. 입니다" 같은 패턴 제거
              this.finalTranscription = this.finalTranscription.replace(/(입니다|이다|이에요|이예요)(\.\s*\1)+/gi, '$1')
              // "이상입니다. 입니다" 같은 패턴 제거 (더 정확한 패턴)
              this.finalTranscription = this.finalTranscription.replace(/([^.]+)(\.\s*입니다|\.\s*이다|\.\s*이에요|\.\s*이예요)+/gi, '$1')
              // 중복된 단어 제거 (예: "이상입니다 이상입니다" → "이상입니다")
              this.finalTranscription = this.finalTranscription.replace(/\b(\w+)\s+\1\b/gi, '$1')
              this.finalTranscription = this.finalTranscription.trim()
            } else {
              this.finalTranscription = transcript.trim()
            }
            this.interimTranscription = ''
            debugLog('🎤 [STT] iOS 네이티브 finalTranscript 수신:', transcript)
            debugLog('🎤 [STT] 누적된 finalTranscription:', this.finalTranscription)

            // 종료 표현 체크 및 메시지 처리
            if (this.isEndingMessage(this.finalTranscription)) {
              debugLog('🛑 [STT] 종료 표현 감지, 음성 인식 중지:', this.finalTranscription)

              // 음성 인식 즉시 중지
              try {
                await SR.stop()
                this.isListening = false
                debugLog('✅ [STT] 종료 표현 감지로 인한 음성 인식 중지 완료')
              } catch (e) {
                debugLog('⚠️ [STT] stop() 호출 에러 (무시):', e)
                this.isListening = false
              }

              let userMessage = this.finalTranscription
              const endingPatterns = this.getEndingPatterns()

              for (const pattern of endingPatterns) {
                userMessage = userMessage.replace(pattern, '').trim()
              }

              this.finalTranscription = ''
              this.isUserSpeaking = false
              this.canSpeak = true

              if (userMessage && userMessage.trim()) {
                this.handleUserMessage(userMessage.trim())
              }
              return
            }

            // 종료 표현이 없으면 말하기가 계속되는 중이므로 누적만 하고 처리하지 않음
            // 타이머를 설정하여 일정 시간 후 자동 처리
            if (this.speakingEndTimer) {
              clearTimeout(this.speakingEndTimer)
            }

            this.speakingEndTimer = setTimeout(() => {
              // 말하기가 끝난 것으로 간주하고 처리
              // isUserSpeaking이 여전히 true이면 말하기가 계속되는 중이므로 처리하지 않음
              if (this.isUserSpeaking && this.finalTranscription && this.finalTranscription.trim()) {
                const finalMessage = this.finalTranscription.trim()
                
                // 종료 표현 체크 - 종료 표현이 있을 때만 처리
                if (this.isEndingMessage(finalMessage)) {
                  debugLog('🛑 [STT] iOS 타이머 만료 시 종료 표현 감지, 답변 내용 추출:', finalMessage)
                  
                  // 종료 표현 제거하고 답변 내용만 추출
                  let userMessage = finalMessage
                  const endingPatterns = this.getEndingPatterns()
                  
                  for (const pattern of endingPatterns) {
                    userMessage = userMessage.replace(pattern, '').trim()
                  }
                  
                  this.finalTranscription = ''
                  this.interimTranscription = ''
                  this.isUserSpeaking = false
                  this.canSpeak = true
                  this.speakingEndTimer = null
                  
                  // 답변 내용이 있으면 AI 평가 요청
                  if (userMessage && userMessage.trim()) {
                    debugLog('🛑 [STT] iOS 타이머 만료 시 종료 표현 제거 후 답변 내용:', userMessage)
                    // isUserSpeaking을 false로 설정한 후 handleUserMessage 호출
                    this.$nextTick(() => {
                      this.handleUserMessage(userMessage.trim())
                    })
                  } else {
                    debugLog('🛑 [STT] iOS 타이머 만료 시 종료 표현만 있고 답변 내용 없음')
                  }
                  return
                }
                
                // 종료 표현이 없으면 타이머만 정리하고 계속 대기 (사용자가 아직 말하는 중일 수 있음)
                debugLog('⏸️ [STT] iOS 타이머 만료되었지만 종료 표현이 없음 - 계속 대기:', finalMessage)
                // 타이머는 정리하되, 메시지는 처리하지 않음
                // 사용자가 계속 말할 수 있도록 isUserSpeaking은 true로 유지
                this.speakingEndTimer = null
              } else if (!this.isUserSpeaking) {
                // 이미 말하기가 끝난 경우 타이머만 정리
                this.speakingEndTimer = null
              }
            }, 2000) // 2초 동안 추가 입력이 없으면 처리
          }
        })

        const offPartialHandle = await SR.addListener('partialResults', async (data) => {
          debugLog('[partial]', data)
          const matches = data?.matches || []
          if (Array.isArray(matches) && matches.length > 0) {
            const transcript = matches[0]
            this.interimTranscription = transcript
            this.isUserSpeaking = true
            debugLog('🎤 [STT] iOS 네이티브 interimTranscript 수신:', transcript)

            // partialResults에서도 종료 표현 체크 (finalTranscription + 현재 transcript 조합으로 체크)
            const combinedText = (this.finalTranscription ? this.finalTranscription + ' ' : '') + transcript
            if (this.isEndingMessage(combinedText)) {
              debugLog('🛑 [STT] partialResults에서 종료 표현 감지, 음성 인식 중지:', combinedText)

              // 음성 인식 즉시 중지
              try {
                await SR.stop()
                this.isListening = false
                debugLog('✅ [STT] partialResults 종료 표현 감지로 인한 음성 인식 중지 완료')
              } catch (e) {
                debugLog('⚠️ [STT] stop() 호출 에러 (무시):', e)
                this.isListening = false
              }

              let userMessage = combinedText
              const endingPatterns = this.getEndingPatterns()

              for (const pattern of endingPatterns) {
                userMessage = userMessage.replace(pattern, '').trim()
              }

              this.finalTranscription = ''
              this.interimTranscription = ''
              this.isUserSpeaking = false
              this.canSpeak = true

              // 타이머가 있으면 취소
              if (this.speakingEndTimer) {
                clearTimeout(this.speakingEndTimer)
                this.speakingEndTimer = null
              }

              if (userMessage && userMessage.trim()) {
                this.handleUserMessage(userMessage.trim())
              }
              return
            }
          }
        })

        const offErrorHandle = await SR.addListener('error', (err) => {
          debugLog('[error]', err)
          this.errorMessage = (err && (err.message || err.error)) ? String(err.message || err.error) : String(this.$t('voiceInterview.unknownError') || 'Unknown error')
        })

        const offEndHandle = await SR.addListener('end', () => {
          debugLog('[end]')
          this.isListening = false
        })

        this.nativeSTTListeners.push(() => offResultHandle.remove())
        this.nativeSTTListeners.push(() => offPartialHandle.remove())
        this.nativeSTTListeners.push(() => offErrorHandle.remove())
        this.nativeSTTListeners.push(() => offEndHandle.remove())

        // TTS 중단 후 짧은 지연
        // 초기 인사말 TTS는 initializeInterview에서 이미 완료 대기를 했으므로
        // 여기서는 기존 TTS만 중단 (혹시 모를 이전 세션 정리)
        try {
          // iOS 네이티브 TTS 중단
          if (this.isUsingNativeTTS && this.nativeTTS) {
            debugLog('🔍 [startNativeSTT] 네이티브 TTS 중단 시도')
            await this.nativeTTS.stop()
            debugLog('✅ [startNativeSTT] 네이티브 TTS 중단 완료')
          }

          // Web TTS 중단
          if (typeof window !== 'undefined' && window.speechSynthesis?.cancel) {
            window.speechSynthesis.cancel()
          }
        } catch (e) {
          debugLog('[console-flow] TTS cancel error (ignored):', e)
        }
        await new Promise(res => setTimeout(res, 400))

        // 사용자 언어 가져오기 (localStorage 또는 i18n에서)
        const userLanguage = this.getUserLanguage()
        const lang = this.getSpeechRecognitionLang(userLanguage)
        debugLog('🔍 [startNativeSTT] iOS 네이티브 STT 언어 설정:', { userLanguage, lang })
        const startPromise = SR.start({
          language: lang,
          partialResults: true,
          popup: true,
          maxResults: 1
        })
        debugLog('[console-flow] SR.start(...) →', startPromise)
        this.isListening = true
      } catch (error) {
        this.isListening = false
        debugLog('❌ iOS 네이티브 STT 시작 실패:', error)
        throw error
      }
    },

    /**
     * TTS 초기화
     */
    async setupTTS() {
      debugLog('🔍 [setupTTS] 함수 시작')

      // 플랫폼 확인
      const platform = typeof window !== 'undefined' && window.Capacitor && typeof window.Capacitor.getPlatform === 'function'
        ? window.Capacitor.getPlatform()
        : 'web'

      debugLog('🔍 [setupTTS] 플랫폼 확인:', { platform, hasWindow: typeof window !== 'undefined', hasCapacitor: typeof window !== 'undefined' && !!window.Capacitor })

      // iOS 네이티브 TTS 사용
      if (platform === 'ios') {
        try {
          debugLog('🔍 [setupTTS] iOS 네이티브 TTS 플러그인 import 시작')
          const { TextToSpeech } = await import('@capacitor-community/text-to-speech')
          debugLog('🔍 [setupTTS] iOS 네이티브 TTS 플러그인 import 완료:', { hasTextToSpeech: !!TextToSpeech, hasSpeak: typeof TextToSpeech.speak === 'function', hasStop: typeof TextToSpeech.stop === 'function' })

          this.nativeTTS = TextToSpeech
          this.isUsingNativeTTS = true
          debugLog('✅ [setupTTS] iOS 네이티브 TTS 플러그인 로드 완료')
          return
        } catch (error) {
          console.error('❌ [setupTTS] iOS 네이티브 TTS 로드 실패, Web Speech API로 폴백:', error)
          debugLog('❌ [setupTTS] iOS 네이티브 TTS 에러 상세:', { errorMessage: error.message, errorStack: error.stack, errorName: error.name })
          // 폴백: Web Speech API 사용
        }
      }

      // Web Speech API 사용 (웹 또는 iOS 네이티브 실패 시)
      debugLog('🔍 [setupTTS] Web Speech API 사용으로 전환')
      this.isUsingNativeTTS = false
      if (!('speechSynthesis' in window)) {
        debugLog('⚠️ [setupTTS] TTS를 지원하지 않는 브라우저입니다.')
        return
      }
      debugLog('✅ [setupTTS] TTS 초기화 완료 (Web Speech API)')
    },

    /**
     * TTS로 텍스트 읽기
     */
    async speakText(text) {
      console.log('🔊 [speakText] ========== 함수 호출됨 ==========')
      console.log('🔊 [speakText] 입력 텍스트:', text)
      console.log('🔊 [speakText] 입력 텍스트 길이:', text ? text.length : 0)
      console.log('🔊 [speakText] 입력 텍스트 전체 내용:', text)
      console.log('🔊 [speakText] isUsingNativeTTS:', this.isUsingNativeTTS)
      console.log('🔊 [speakText] nativeTTS 존재:', !!this.nativeTTS)
      console.log('🔊 [speakText] 플랫폼:', typeof window !== 'undefined' && window.Capacitor && typeof window.Capacitor.getPlatform === 'function' ? window.Capacitor.getPlatform() : 'web')

      if (!text || !text.trim()) {
        console.log('🔊 [speakText] 텍스트가 비어있어서 종료')
        return
      }

      // 종합 피드백(모든 질문 종료 후 피드백)인 경우 TTS 재생하지 않음
      const isFinalFeedback = this.isFinalFeedbackMessage(text)
      if (isFinalFeedback) {
        console.log('🔊 [speakText] 종합 피드백 감지 - TTS 재생 안함')
        console.log('🔊 [speakText] 종합 피드백 내용:', text.substring(0, 200))
        return
      }

      // iOS 네이티브 TTS 사용
      console.log('🔊 [speakText] 네이티브 TTS 사용 여부 확인:', this.isUsingNativeTTS && this.nativeTTS)
      if (this.isUsingNativeTTS && this.nativeTTS) {
        try {
          // 기존 음성 재생 중지
          await this.nativeTTS.stop()

          // iOS에서 블루투스 연결 상태 확인 후 조건부로 스피커 강제 출력
          // 블루투스가 연결되어 있지 않을 때만 overrideToSpeaker() 호출 (스피커 볼륨 문제 해결)
          const platform = typeof window !== 'undefined' && window.Capacitor && typeof window.Capacitor.getPlatform === 'function'
            ? window.Capacitor.getPlatform()
            : 'web'
          
          let shouldOverrideToSpeaker = false
          if (platform === 'ios' && window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.AudioRoute) {
            try {
              const route = await window.Capacitor.Plugins.AudioRoute.getCurrentRoute()
              const output = route.outputs && route.outputs[0]
              
              console.log('🔊 [speakText] 현재 오디오 라우트:', {
                outputCount: route.outputCount,
                output: output ? {
                  portName: output.portName,
                  deviceType: output.deviceType,
                  isSpeaker: output.isSpeaker,
                  isBluetooth: output.isBluetooth,
                  isWiredHeadphones: output.isWiredHeadphones
                } : null
              })
              
              // 블루투스나 유선 이어폰이 연결되어 있지 않을 때만 스피커로 강제 출력
              if (!output || (!output.isBluetooth && !output.isWiredHeadphones)) {
                shouldOverrideToSpeaker = true
                await window.Capacitor.Plugins.AudioRoute.overrideToSpeaker()
                console.log('🔊 [speakText] 블루투스/유선 이어폰 미연결 - 스피커로 강제 출력 설정')
              } else {
                console.log('🔊 [speakText] 블루투스/유선 이어폰 연결됨 - iOS 자동 라우팅 사용', {
                  deviceType: output.deviceType,
                  portName: output.portName
                })
              }
            } catch (error) {
              console.warn('🔊 [speakText] 오디오 라우트 확인 실패 (무시):', error)
            }
          }

          this.isAISpeaking = true
          console.log('🔊 [speakText] iOS 네이티브 TTS로 재생 시작')
          console.log('🔊 [speakText] 재생할 텍스트:', text)
          debugLog('🔊 [TTS] iOS 네이티브 음성 재생 시작')

          // TTS 재생 시작 (비동기로 실행)
          const ttsPromise = this.nativeTTS.speak({
            text: text,
            lang: this.getSpeechRecognitionLang(this.language),
            rate: 0.8,
            pitch: 1.0,
            volume: 1.0  // 최대 볼륨으로 설정
          })

          // TTS 재생 중에도 주기적으로 스피커 출력 확인 및 재설정 (블루투스 미연결 시에만)
          let speakerCheckInterval = null
          if (shouldOverrideToSpeaker && platform === 'ios' && window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.AudioRoute) {
            speakerCheckInterval = setInterval(async () => {
              try {
                // 현재 라우트 확인
                const route = await window.Capacitor.Plugins.AudioRoute.getCurrentRoute()
                const output = route.outputs && route.outputs[0]
                
                // 블루투스/유선 이어폰이 연결되지 않았고, 스피커로 출력되지 않을 때만 재설정
                if (!output || (!output.isBluetooth && !output.isWiredHeadphones && !output.isSpeaker)) {
                  await window.Capacitor.Plugins.AudioRoute.overrideToSpeaker()
                  console.log('🔊 [speakText] TTS 재생 중 스피커 출력 재확인 완료')
                }
              } catch (error) {
                // 무시
              }
            }, 500)  // 0.5초마다 확인
          }

          // TTS 재생 완료 대기
          await ttsPromise

          // 인터벌 정리
          if (speakerCheckInterval) {
            clearInterval(speakerCheckInterval)
          }

          // TTS 재생 완료 후, 스피커로 강제 출력했던 경우 오버라이드 해제
          if (shouldOverrideToSpeaker && platform === 'ios' && window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.AudioRoute) {
            try {
              await window.Capacitor.Plugins.AudioRoute.resetOverride()
              console.log('🔊 [speakText] TTS 재생 완료 후 오디오 포트 오버라이드 해제')
            } catch (error) {
              console.warn('🔊 [speakText] 오디오 포트 오버라이드 해제 실패 (무시):', error)
            }
          }

          this.isAISpeaking = false
          console.log('🔊 [speakText] iOS 네이티브 TTS 재생 완료')
          // TTS 완료 후 currentAIText 비우기 (이미 conversationHistory에 포함됨)
          if (this.isCurrentAITextInHistory) {
            this.currentAIText = ''
          }
          debugLog('🔊 [TTS] iOS 네이티브 음성 재생 완료')

          // TTS 완료 후 자동으로 말하기 시작
          this.canSpeak = true
          if (this.isConnected && !this.isPaused) {
            // 짧은 지연 후 자동 시작 (사용자가 질문을 듣고 이해할 시간)
            setTimeout(() => {
              if (this.canSpeak && !this.isPaused && this.isConnected && !this.isAISpeaking) {
                debugLog('🔊 [TTS] 자동으로 말하기 시작')
                this.startSpeaking()
              }
            }, 500)
          }
        } catch (error) {
          this.isAISpeaking = false
          console.log('🔊 [speakText] iOS 네이티브 TTS 재생 오류:', error)
          debugLog('🔊 [TTS] iOS 네이티브 음성 재생 오류:', error)
          // 폴백: Web Speech API 사용
          this.speakTextWeb(text)
        }
        return
      }

      // Web Speech API 사용
      console.log('🔊 [speakText] Web Speech API로 재생')
      this.speakTextWeb(text)
    },

    /**
     * Web Speech API로 텍스트 읽기 (폴백)
     */
    speakTextWeb(text) {
      if (!('speechSynthesis' in window)) {
        debugLog('⚠️ TTS를 지원하지 않는 브라우저입니다.')
        return
      }

      // 기존 음성 재생 중지
      speechSynthesis.cancel()

      const utterance = new SpeechSynthesisUtterance(text)
      const targetLang = this.getSpeechRecognitionLang(this.language)
      utterance.lang = targetLang
      utterance.rate = 0.8
      utterance.pitch = 1.0
      utterance.volume = 1.0  // 최대 볼륨으로 설정

      // 음성 선택
      const voices = speechSynthesis.getVoices()
      const voice = voices.find(v => v.lang === targetLang) ||
                   voices.find(v => v.lang.startsWith(this.language))
      if (voice) {
        utterance.voice = voice
      }

      utterance.onstart = () => {
        this.isAISpeaking = true
        debugLog('🔊 [TTS] Web Speech API 음성 재생 시작')
      }

      utterance.onend = () => {
        this.isAISpeaking = false
        // TTS 완료 후 currentAIText 비우기 (이미 conversationHistory에 포함됨)
        if (this.isCurrentAITextInHistory) {
          this.currentAIText = ''
        }
        debugLog('🔊 [TTS] Web Speech API 음성 재생 완료')

        // TTS 완료 후 자동으로 말하기 시작
        this.canSpeak = true
        if (this.isConnected && !this.isPaused) {
          // 짧은 지연 후 자동 시작 (사용자가 질문을 듣고 이해할 시간)
          setTimeout(() => {
            if (this.canSpeak && !this.isPaused && this.isConnected && !this.isAISpeaking) {
              debugLog('🔊 [TTS] 자동으로 말하기 시작')
              this.startSpeaking()
            }
          }, 500)
        }
      }

      utterance.onerror = (event) => {
        this.isAISpeaking = false
        debugLog('🔊 [TTS] Web Speech API 음성 재생 오류:', event.error)
      }

      speechSynthesis.speak(utterance)
    },

    /**
     * 초기 인사말에서 불필요한 부분 제거
     * 공통 유틸리티 사용 (iOS와 웹에서 동일한 필터링 로직 보장)
     */
    filterInitialGreeting(text) {
      return filterInitialGreetingUtil(text)
    },
    
    /**
     * @deprecated 이 메서드는 더 이상 사용되지 않습니다. filterInitialGreetingUtil을 직접 사용하세요.
     */
    _filterInitialGreeting_old(text) {
      if (!text) return text

      let filtered = text

      // 1. 불필요한 인사말 및 역할 소개 제거
      const patternsToRemove = [
        // 인사말 패턴 (줄 단위로 제거)
        /^[^\n]*안녕하세요[^\n]*\n?/i,
        /^[^\n]*네,\s*안녕하세요[^\n]*\n?/i,
        /^[^\n]*Hello[^\n]*\n?/i,

        // 인터뷰 시작 선언
        /^[^\n]*인터뷰를\s*시작하겠습니다[^\n]*\n?/i,
        /^[^\n]*지금부터\s*인터뷰를\s*시작하겠습니다[^\n]*\n?/i,
        /^[^\n]*Let's\s*start\s*the\s*interview[^\n]*\n?/i,

        // 역할 소개 패턴
        /^[^\n]*저는\s*[^입니다\n]*인터뷰어입니다[^\n]*\n?/i,
        /^[^\n]*I\s*am\s*the\s*interviewer[^\n]*\n?/i,
        /^[^\n]*사용자님께서는\s*인터뷰이[^\n]*\n?/i,
        /^[^\n]*you\s*are\s*the\s*interviewee[^\n]*\n?/i,
        /^[^\n]*역할을\s*맡아주시면\s*됩니다[^\n]*\n?/i,
        /^[^\n]*역할을\s*맡아주세요[^\n]*\n?/i,
      ]

      // 각 패턴 제거 (반복적으로 제거)
      let previousLength = filtered.length
      let iterations = 0
      while (iterations < 10) { // 최대 10회 반복
        for (const pattern of patternsToRemove) {
          filtered = filtered.replace(pattern, '')
        }
        if (filtered.length === previousLength) break // 더 이상 제거할 것이 없으면 중지
        previousLength = filtered.length
        iterations++
      }

      // 2. "첫 번째 질문입니다." 같은 표현 제거 (질문 내용은 유지)
      // "첫 번째 질문입니다. 질문내용" -> "질문내용"
      // 정규식으로 "첫 번째 질문입니다" 뒤의 내용만 추출
      const questionPatterns = [
        /^[^\n]*첫\s*번째\s*질문입니다\.\s*(.+)$/i,
        /^[^\n]*첫\s*번째\s*질문입니다\s+(.+)$/i,
        /^[^\n]*첫\s*번째\s*질문\.\s*(.+)$/i,
        /^[^\n]*First\s*question\.\s*(.+)$/i,
        /^[^\n]*First\s*question\s+(.+)$/i,
      ]

      let questionExtracted = false
      for (const pattern of questionPatterns) {
        const match = filtered.match(pattern)
        if (match && match[1]) {
          // 패턴 뒤의 내용만 추출
          filtered = match[1].trim()
          questionExtracted = true
          debugLog('🔍 [filterInitialGreeting] 질문 내용 추출:', {
            pattern: pattern.toString(),
            extracted: filtered.substring(0, 100)
          })
          break
        }
      }

      // 패턴 매칭이 안 된 경우, 단순히 "첫 번째 질문입니다" 부분만 제거
      if (!questionExtracted) {
        filtered = filtered.replace(/^[^\n]*첫\s*번째\s*질문입니다\.?\s*/i, '')
        filtered = filtered.replace(/^[^\n]*첫\s*번째\s*질문\.?\s*/i, '')
        filtered = filtered.replace(/^[^\n]*First\s*question\.?\s*/i, '')
      }

      // 3. 빈 줄 제거 및 정리
      filtered = filtered.replace(/^\s*\n+/, '') // 앞의 빈 줄 제거
      filtered = filtered.replace(/\n+\s*$/, '') // 뒤의 빈 줄 제거
      filtered = filtered.replace(/\n{3,}/g, '\n\n') // 연속된 줄바꿈을 2개로

      // 4. 앞뒤 공백 제거
      filtered = filtered.trim()

      // 5. 필터링 결과가 비어있으면 원본 반환 (질문이 없으면 안 됨)
      if (!filtered || filtered.length === 0) {
        debugLog('⚠️ [filterInitialGreeting] 필터링 결과가 비어있음, 원본 반환:', text.substring(0, 100))
        return text
      }

      // 필터링 전후 비교 로그
      if (filtered !== text) {
        debugLog('🔍 [filterInitialGreeting] 필터링 적용:', {
          original: text.substring(0, 200),
          filtered: filtered.substring(0, 200),
          originalLength: text.length,
          filteredLength: filtered.length
        })
      }

      return filtered
    },

    /**
     * 초기 인사말 요청
     */
    async sendInitialGreeting() {
      debugLog('🔍 [sendInitialGreeting] 함수 시작')
      // 중복 방지: 이미 전송되었다면 즉시 반환
      if (this.hasSentInitialGreeting) {
        debugLog('🔍 [sendInitialGreeting] 이미 전송됨 - 스킵')
        return
      }
      
      // conversationHistory에 이미 초기 질문(assistant 메시지)이 있는지 확인
      const hasInitialQuestion = this.conversationHistory.some(msg => msg.role === 'assistant')
      if (hasInitialQuestion) {
        debugLog('🔍 [sendInitialGreeting] conversationHistory에 이미 초기 질문이 있음 - 스킵')
        this.hasSentInitialGreeting = true
        return
      }
      
      // 레이스 방지: 바로 가드 플래그 설정
      this.hasSentInitialGreeting = true
      try {
        debugLog('🔍 [sendInitialGreeting] isWaitingForResponse = true 설정 전')
        this.isWaitingForResponse = true
        debugLog('🔍 [sendInitialGreeting] isWaitingForResponse = true 설정 완료')

        // 이전 요청 취소
        if (this.abortController) {
          debugLog('🔍 [sendInitialGreeting] 이전 AbortController 취소')
          this.abortController.abort()
        }

        // 새로운 AbortController 생성
        debugLog('🔍 [sendInitialGreeting] 새로운 AbortController 생성')
        this.abortController = new AbortController()
        debugLog('🔍 [sendInitialGreeting] AbortController 생성 완료')

        // 빈 메시지로 초기 인사말 요청 (시스템이 자동으로 인사말 생성)
        const conversationHistory = []
        debugLog('🔍 [sendInitialGreeting] conversationHistory 초기화 완료')

        const instructionsToSend = this.originalInstructions || this.instructions
        debugLog('📤 [sendInitialGreeting] Instructions 전달 확인:', {
          hasOriginalInstructions: !!this.originalInstructions,
          originalInstructionsLength: this.originalInstructions?.length || 0,
          hasInstructions: !!this.instructions,
          instructionsLength: this.instructions?.length || 0,
          instructionsToSendLength: instructionsToSend?.length || 0,
          instructionsPreview: instructionsToSend?.substring(0, 200) || '(없음)'
        })

        const requestUrl = '/api/chat/interview/'
        const fullUrl = apiBaseURL ? `${apiBaseURL}${requestUrl}` : requestUrl

        debugLog('📤 [sendInitialGreeting] API 호출 시작:', {
          requestUrl: requestUrl,
          baseURL: apiBaseURL,
          fullUrl: fullUrl,
          examId: this.examId,
          messageLength: 0,
          conversationHistoryCount: conversationHistory.length,
          language: this.language,
          instructionsLength: instructionsToSend?.length || 0
        })

        const response = await api.post(requestUrl, {
          exam_id: this.examId,
          message: '', // 빈 메시지로 초기 인사말 요청
          conversation_history: conversationHistory,
          language: this.language,
          instructions: instructionsToSend
        }, {
          signal: this.abortController.signal
        })

        debugLog('✅ [sendInitialGreeting] API 호출 성공:', {
          status: response.status,
          statusText: response.statusText,
          headers: response.headers,
          dataKeys: response.data ? Object.keys(response.data) : [],
          responseData: response.data,
          responseLength: response.data?.response?.length || 0,
          model: response.data?.model,
          usage: response.data?.usage
        })

        if (!response.data || !response.data.response) {
          debugLog('❌ [sendInitialGreeting] 응답 데이터가 없거나 형식이 잘못되었습니다:', response.data)
          throw new Error('AI 응답을 받지 못했습니다.')
        }

        let aiResponse = response.data.response

        // 초기 인사말 필터링 (공통 유틸리티 사용)
        aiResponse = filterInitialGreetingUtil(aiResponse)

        // 마무리 인사말 필터링 (혹시 있을 경우를 대비)
        aiResponse = this.filterEndingGreeting(aiResponse)

        // 대화 히스토리에 이미 초기 질문이 없는지 다시 한 번 확인 (레이스 컨디션 방지)
        const hasInitialQuestion = this.conversationHistory.some(msg => msg.role === 'assistant')
        if (!hasInitialQuestion) {
          // 대화 히스토리에 추가
          this.conversationHistory.push({
            role: 'assistant',
            content: aiResponse
          })
          debugLog('✅ [sendInitialGreeting] 초기 질문을 conversationHistory에 추가')
        } else {
          debugLog('⚠️ [sendInitialGreeting] conversationHistory에 이미 초기 질문이 있어 추가하지 않음')
        }

        // AI 응답 텍스트 업데이트
        this.currentAIText = aiResponse

        // TTS로 읽기
        this.speakText(aiResponse)

        debugLog('✅ 초기 인사말 수신 (필터링 완료)')
      } catch (error) {
        // AbortController로 취소된 경우는 에러로 처리하지 않음
        if (error.name === 'AbortError' || error.code === 'ERR_CANCELED') {
          debugLog('🛑 초기 인사말 요청 취소됨')
          return
        }

        debugLog('❌ 초기 인사말 요청 실패:', error)
        debugLog('❌ [sendInitialGreeting] 에러 상세:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status,
          statusText: error.response?.statusText,
          requestUrl: error.config?.url,
          requestData: error.config?.data
        })
        this.errorMessage = error.response?.data?.error || error.message || '초기 인사말 요청에 실패했습니다.'
      } finally {
        this.isWaitingForResponse = false
        this.abortController = null
      }
    },

    /**
     * Chat API로 메시지 전송
     */
    async sendChatMessage(userMessage) {
      try {
        if (!userMessage || !userMessage.trim()) {
          return null
        }

        // 사용자가 말하는 중이면 AI 응답 요청하지 않음
        if (this.isUserSpeaking) {
          debugLog('⏸️ [sendChatMessage] 사용자가 말하는 중이므로 AI 응답 요청 무시')
          return null
        }

        this.isWaitingForResponse = true

        // 이전 요청 취소
        if (this.abortController) {
          this.abortController.abort()
        }

        // 새로운 AbortController 생성
        this.abortController = new AbortController()

        // 대화 히스토리 구성
        const conversationHistory = this.conversationHistory.map(msg => ({
          role: msg.role,
          content: msg.content
        }))

        const instructionsToSend = this.originalInstructions || this.instructions
        debugLog('📤 [sendChatMessage] Instructions 전달 확인:', {
          hasOriginalInstructions: !!this.originalInstructions,
          originalInstructionsLength: this.originalInstructions?.length || 0,
          hasInstructions: !!this.instructions,
          instructionsLength: this.instructions?.length || 0,
          instructionsToSendLength: instructionsToSend?.length || 0,
          instructionsPreview: instructionsToSend?.substring(0, 200) || '(없음)'
        })

        debugLog('📤 [sendChatMessage] API 호출 시작:', {
          url: '/api/chat/interview/',
          examId: this.examId,
          messageLength: userMessage.length,
          conversationHistoryCount: conversationHistory.length,
          language: this.language,
          instructionsLength: instructionsToSend?.length || 0
        })

        const response = await api.post('/api/chat/interview/', {
          exam_id: this.examId,
          message: userMessage,
          conversation_history: conversationHistory,
          language: this.language,
          instructions: instructionsToSend
        }, {
          signal: this.abortController.signal
        })

        debugLog('✅ [sendChatMessage] API 호출 성공:', {
          status: response.status,
          responseLength: response.data?.response?.length || 0,
          model: response.data?.model,
          usage: response.data?.usage
        })

        const aiResponse = response.data.response

        // 사용자 메시지는 handleUserMessage에서 이미 추가했으므로 중복 추가 방지
        // 마지막 메시지가 사용자 메시지인지 확인
        let lastMessage = this.conversationHistory[this.conversationHistory.length - 1]
        if (!lastMessage || lastMessage.role !== 'user' || lastMessage.content !== userMessage) {
          // 사용자 메시지가 없으면 추가
          this.conversationHistory.push({
            role: 'user',
            content: userMessage
          })
        }

        // AI 응답 필터링 (마무리 인사말 제거)
        const filteredResponse = this.filterEndingGreeting(aiResponse)

        console.log('🔍 [sendChatMessage] AI 응답 수신')
        console.log('🔍 [sendChatMessage] 원본 응답:', aiResponse)
        console.log('🔍 [sendChatMessage] 원본 응답 길이:', aiResponse ? aiResponse.length : 0)
        console.log('🔍 [sendChatMessage] 필터링된 응답:', filteredResponse)
        console.log('🔍 [sendChatMessage] 필터링된 응답 길이:', filteredResponse ? filteredResponse.length : 0)

        // 중복 방지: 마지막 메시지가 이미 같은 assistant 메시지인지 확인
        // 사용자 메시지 추가 후 다시 확인 (conversationHistory가 변경되었을 수 있음)
        lastMessage = this.conversationHistory[this.conversationHistory.length - 1]
        const isDuplicate = lastMessage && 
                           lastMessage.role === 'assistant' && 
                           lastMessage.content === filteredResponse
        
        if (isDuplicate) {
          debugLog('⚠️ [sendChatMessage] conversationHistory에 이미 같은 AI 응답이 있어 추가하지 않음:', {
            lastMessageContent: lastMessage.content.substring(0, 50) + '...',
            newResponseContent: filteredResponse.substring(0, 50) + '...'
          })
        } else {
          // AI 응답을 대화 히스토리에 추가 (필터링된 응답)
          this.conversationHistory.push({
            role: 'assistant',
            content: filteredResponse
          })
          debugLog('✅ [sendChatMessage] AI 응답을 conversationHistory에 추가')
        }

        // AI 응답 텍스트 업데이트 (필터링된 응답 사용)
        this.currentAIText = filteredResponse

        debugLog('✅ Chat API 응답 수신:', {
          userMessage: userMessage.substring(0, 50) + '...',
          originalResponse: aiResponse.substring(0, 50) + '...',
          filteredResponse: filteredResponse.substring(0, 50) + '...'
        })

        console.log('🔍 [sendChatMessage] filteredResponse 반환')
        return filteredResponse
      } catch (error) {
        // AbortController로 취소된 경우는 에러로 처리하지 않음
        if (error.name === 'AbortError' || error.code === 'ERR_CANCELED') {
          debugLog('🛑 Chat API 요청 취소됨')
          return null
        }

        debugLog('❌ Chat API 호출 실패:', error)
        debugLog('❌ [sendChatMessage] 에러 상세:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status,
          statusText: error.response?.statusText,
          requestUrl: error.config?.url,
          requestData: error.config?.data
        })
        this.errorMessage = error.response?.data?.error || error.message || 'AI 응답 생성에 실패했습니다.'
        return null
      } finally {
        this.isWaitingForResponse = false
        this.abortController = null
      }
    },

    /**
     * 종료 표현 감지
     */
    /**
     * 종합 피드백 메시지(인터뷰 종료 피드백)인지 확인
     */
    isFinalFeedbackMessage(text) {
      if (!text || !text.trim()) return false
      
      const finalFeedbackPatterns = [
        /모든\s*질문이\s*끝났습니다/i,
        /모든\s*질문이\s*끝났/i,
        /전반적으로/i,
        /개선\s*포인트/i,
        /All\s*questions\s*are\s*complete/i,
        /All\s*questions\s*are\s*finished/i,
        /Overall/i,
        /Improvement\s*points/i,
        /Overall\s*feedback/i,
        /전체\s*평가/i,
        /종합\s*평가/i,
        /Final\s*feedback/i,
        /Summary/i
      ]
      
      return finalFeedbackPatterns.some(pattern => pattern.test(text))
    },

    /**
     * 종료 표현 패턴 배열 반환 (정규식 패턴)
     * 문자열 끝에서 매칭되는 패턴들
     */
    getEndingPatterns() {
      return [
        /\s*이상입니다\s*$/i,
        /\s*이상\s*이다\s*$/i,
        /\s*이상이에요\s*$/i,
        /\s*이상이예요\s*$/i,
        /\s*응답완료\s*$/i,
        /\s*답변완료\s*$/i,
        /\s*완료\s*$/i,
        /\s*끝\s*$/i,
        /\s*종료\s*$/i,
        /\s*마무리\s*$/i,
        /\s*끝내기\s*$/i,
        /\s*그만\s*$/i,
        /\s*다음\s*질문\s*$/i,
        /\s*다음질문\s*$/i,
        /\s*that's\s*all\s*$/i,
        /\s*that\s*is\s*all\s*$/i,
        /\s*response\s*complete\s*$/i,
        /\s*answer\s*complete\s*$/i,
        /\s*complete\s*$/i,
        /\s*end\s*$/i,
        /\s*finish\s*$/i,
        /\s*done\s*$/i,
        /\s*over\s*$/i,
        /\s*next\s*question\s*$/i,
        /\s*nextquestion\s*$/i,
      ]
    },

    /**
     * 종료 표현 패턴 배열 반환 (문자열 시작에서 매칭되는 패턴들)
     * 전체 메시지가 종료 표현만 있는지 확인할 때 사용
     */
    getEndingPatternsExact() {
      return [
        /^이상입니다$/i,
        /^이상\s*이다$/i,
        /^이상이에요$/i,
        /^이상이예요$/i,
        /^응답완료$/i,
        /^답변완료$/i,
        /^완료$/i,
        /^끝$/i,
        /^종료$/i,
        /^마무리$/i,
        /^끝내기$/i,
        /^그만$/i,
        /^다음\s*질문$/i,
        /^다음질문$/i,
        /^that's\s*all$/i,
        /^that\s*is\s*all$/i,
        /^response\s*complete$/i,
        /^answer\s*complete$/i,
        /^complete$/i,
        /^end$/i,
        /^finish$/i,
        /^done$/i,
        /^over$/i,
        /^next\s*question$/i,
        /^nextquestion$/i,
      ]
    },

    /**
     * 종료 표현 패턴 배열 반환 (문자열 포함 여부 확인용)
     * 메시지에 종료 표현이 포함되어 있는지 확인할 때 사용
     */
    getEndingPatternsString() {
      return [
        '이상입니다',
        '이상 이다',
        '이상이에요',
        '이상이예요',
        '응답완료',
        '답변완료',
        '완료',
        '끝',
        '종료',
        '마무리',
        '끝내기',
        '그만',
        '다음 질문',
        '다음질문',
        'that\'s all',
        'that is all',
        'response complete',
        'answer complete',
        'complete',
        'end',
        'finish',
        'done',
        'over',
        'next question',
        'nextquestion'
      ]
    },

    isEndingMessage(message) {
      if (!message) return false
      const trimmed = message.trim().toLowerCase()
      const endingPatterns = this.getEndingPatternsString()
      return endingPatterns.some(pattern => trimmed.includes(pattern))
    },

    /**
     * 사용자 메시지 처리
     */
    async handleUserMessage(message) {
      console.log('🔍 [handleUserMessage] ========== 함수 호출됨 ==========')
      console.log('🔍 [handleUserMessage] 입력 메시지:', message)
      console.log('🔍 [handleUserMessage] 입력 메시지 타입:', typeof message)
      console.log('🔍 [handleUserMessage] 입력 메시지 길이:', message ? message.length : 0)

      if (!message || !message.trim()) {
        console.log('🔍 [handleUserMessage] 메시지가 비어있어서 종료')
        return
      }

      // 종료 표현만 있는 경우 (답변 내용 없음)
      const trimmedMessage = message.trim()
      console.log('🔍 [handleUserMessage] trimmedMessage:', trimmedMessage)
      if (this.isEndingMessage(trimmedMessage)) {
        console.log('🔍 [handleUserMessage] 종료 표현만 있음')
        // 종료 표현만 있고 답변 내용이 없는 경우
        const endingPatterns = this.getEndingPatternsExact()

        const isOnlyEnding = endingPatterns.some(pattern => pattern.test(trimmedMessage))

        if (isOnlyEnding) {
          debugLog('🛑 종료 표현만 감지, AI 응답 요청하지 않음:', message)
          // 히스토리에 추가하지 않음
          // AI 응답 요청하지 않음
          // 진행 중인 AI 응답 취소
          if (this.isWaitingForResponse && this.abortController) {
            this.abortController.abort()
            this.abortController = null
            this.isWaitingForResponse = false
          }
          // TTS 중지
          if (this.isUsingNativeTTS && this.nativeTTS) {
            try {
              await this.nativeTTS.stop()
            } catch (error) {
              debugLog('❌ iOS 네이티브 TTS 중지 실패:', error)
            }
          }
          if ('speechSynthesis' in window) {
            speechSynthesis.cancel()
          }
          this.isAISpeaking = false
          // finalTranscription 초기화
          this.finalTranscription = ''
          this.interimTranscription = ''
          // 말하기 종료
          this.isUserSpeaking = false
          this.canSpeak = true
          return
        }
        // 종료 표현이 포함되어 있지만 답변 내용도 있는 경우는 계속 진행 (이미 STT에서 처리됨)
      }

      if (this.isWaitingForResponse) {
        debugLog('⏸️ AI 응답 대기 중이므로 사용자 메시지 무시')
        return // 이미 응답 대기 중이면 무시
      }

      // 사용자가 말하는 중이면 절대 AI 응답 요청하지 않음 (최우선 규칙)
      if (this.isUserSpeaking) {
        debugLog('⏸️ 사용자가 말하는 중이므로 AI 응답 요청 무시')
        return // 사용자가 말하는 중이면 무시
      }

      // interimTranscription이 있으면 사용자가 아직 말하고 있는 중
      if (this.interimTranscription && this.interimTranscription.trim()) {
        debugLog('⏸️ interimTranscription이 있으므로 사용자가 아직 말하는 중 - AI 응답 요청 무시')
        return
      }

      // speakingEndTimer가 설정되어 있으면 사용자가 말하는 중 (타이머 대기 중)
      if (this.speakingEndTimer) {
        debugLog('⏸️ speakingEndTimer가 설정되어 있으므로 사용자가 말하는 중 - AI 응답 요청 무시')
        return
      }
      
      debugLog('📝 사용자 메시지 수신:', message)
      
      // 대화 히스토리에 사용자 메시지 추가 (sendChatMessage에서도 추가하지만 여기서 먼저 추가)
      // 중복 방지를 위해 마지막 메시지 확인
      const lastMessage = this.conversationHistory[this.conversationHistory.length - 1]
      if (!lastMessage || lastMessage.role !== 'user' || lastMessage.content !== message) {
        this.conversationHistory.push({
          role: 'user',
          content: message
        })
      }
      
      // finalTranscription 초기화 (히스토리에 추가했으므로)
      this.finalTranscription = ''
      this.interimTranscription = ''
      
      // Chat API 호출
      console.log('🔍 [handleUserMessage] sendChatMessage 호출 전:', {
        message: message.substring(0, 50),
        currentQuestionIndex: this.currentQuestionIndex
      })
      const aiResponse = await this.sendChatMessage(message)
      console.log('🔍 [handleUserMessage] sendChatMessage 호출 후:', {
        aiResponse: aiResponse ? aiResponse.substring(0, 50) : null,
        hasResponse: !!aiResponse
      })
      
      if (aiResponse) {
        // 마무리 인사말 필터링
        let filteredResponse = this.filterEndingGreeting(aiResponse)
        
        // AI 응답에서 평가 내용 추출 및 기록
        // 현재 질문 정보 찾기 (conversationHistory에서 첫 번째 질문 찾기)
        const firstQuestion = this.conversationHistory.find(msg => 
          msg.role === 'assistant' && 
          (msg.content.includes('첫 번째') || msg.content.includes('First question'))
        )
        
        console.log('🔍 [handleUserMessage] 평가/질문 분리 조건 확인:', {
          hasFirstQuestion: !!firstQuestion,
          currentQuestionIndex: this.currentQuestionIndex,
          conditionResult: !!(firstQuestion || this.currentQuestionIndex > 0),
          conversationHistoryLength: this.conversationHistory.length
        })
        
        // 사용자가 답변한 후의 응답은 항상 평가일 가능성이 높으므로 평가/질문 분리 로직 실행
        // (firstQuestion이 없거나 currentQuestionIndex가 0이어도 평가일 수 있음)
        const shouldSeparate = firstQuestion || this.currentQuestionIndex > 0 || this.conversationHistory.length > 1
        
        if (shouldSeparate) {
          // 마지막 질문인지 확인
          const isLastQuestion = this.currentQuestionIndex >= this.totalQuestions - 1
          
          // 문제 제목 추출 (currentQuestionIndex를 사용하여 originalQuestions에서 직접 가져오기)
          let questionTitle = ''
          
          // currentQuestionIndex를 사용하여 originalQuestions에서 현재 질문 찾기
          if (this.originalQuestions && this.originalQuestions.length > 0 && this.currentQuestionIndex >= 0 && this.currentQuestionIndex < this.originalQuestions.length) {
            const currentQuestionObj = this.originalQuestions[this.currentQuestionIndex]
            if (currentQuestionObj) {
              // 언어에 따라 title_ko 또는 title_en 사용
              questionTitle = this.language === 'ko' 
                ? (currentQuestionObj.title_ko || currentQuestionObj.title || '')
                : (currentQuestionObj.title_en || currentQuestionObj.title || '')
            }
          }
          
          // originalQuestions에서 찾지 못한 경우, conversationHistory에서 추출 시도
          if (!questionTitle || questionTitle.trim() === '') {
            const currentQuestion = this.conversationHistory
              .filter(msg => msg.role === 'assistant')
              .slice(-1)[0] // 마지막 assistant 메시지
            
            if (currentQuestion) {
              // 평가와 질문이 합쳐진 메시지인 경우, 질문 부분만 추출
              const content = currentQuestion.content
              // "다음 질문" 또는 "Next question" 이후의 텍스트를 찾기
              const nextQuestionMatch = content.match(/(?:다음\s*질문|Next\s*question)[\s:]*\n*(.+)/i)
              if (nextQuestionMatch) {
                const questionText = nextQuestionMatch[1]
                const questionMatch = questionText.match(/(.+?)(?:에\s*대해|about|에\s*대한|에\s*대해\s*설명)/i)
                if (questionMatch) {
                  questionTitle = questionMatch[1].trim()
                } else {
                  questionTitle = questionText.substring(0, 50).trim()
                }
              } else {
                // 일반적인 질문 패턴 추출
                const questionMatch = content.match(/(.+?)(?:에\s*대해|about|에\s*대한|에\s*대해\s*설명)/i)
                if (questionMatch) {
                  questionTitle = questionMatch[1].trim()
                } else {
                  // 간단히 첫 50자만
                  questionTitle = content.substring(0, 50).trim()
                }
              }
            } else if (firstQuestion) {
              // 첫 번째 질문이 있으면 그것 사용
              const questionMatch = firstQuestion.content.match(/(.+?)(?:에\s*대해|about|에\s*대한)/i)
              if (questionMatch) {
                questionTitle = questionMatch[1].trim()
              } else {
                questionTitle = firstQuestion.content.substring(0, 50).trim()
              }
            }
          }
          
          console.log('🔍 [handleUserMessage] questionTitle 추출 결과:', {
            questionTitle: questionTitle.substring(0, 50),
            currentQuestionIndex: this.currentQuestionIndex,
            originalQuestionsLength: this.originalQuestions ? this.originalQuestions.length : 0,
            language: this.language
          })
          
          console.log('🔍 [handleUserMessage] 평가 추출 시작')
          console.log('🔍 [handleUserMessage] filteredResponse:', filteredResponse)
          console.log('🔍 [handleUserMessage] filteredResponse 길이:', filteredResponse.length)
          console.log('🔍 [handleUserMessage] user message:', message)
          
          // 평가 추출
          const evaluation = this.extractEvaluationFromAIResponse(filteredResponse, message)
          console.log('🔍 [handleUserMessage] 평가 추출 결과:', evaluation)
          console.log('🔍 [handleUserMessage] 평가 감지 여부:', !!evaluation)
          if (evaluation) {
            console.log('🔍 [handleUserMessage] 평가 상세:', {
              accuracy: evaluation.accuracy,
              isCorrect: evaluation.isCorrect
            })
          }
          
          // 평가가 감지되면 (사용자가 답변한 후이므로 평가일 가능성이 높음)
          // 평가 부분과 다음 질문 부분을 분리하여 평가는 스킵하고 다음 질문만 TTS로 재생
          console.log('🔍 [handleUserMessage] 평가/질문 분리 함수 호출 시작')
          const { evaluationText, nextQuestionText } = this.separateEvaluationAndNextQuestion(filteredResponse)
          console.log('🔍 [handleUserMessage] 평가/질문 분리 함수 호출 완료')
          console.log('🔍 [handleUserMessage] evaluationText:', evaluationText)
          console.log('🔍 [handleUserMessage] nextQuestionText:', nextQuestionText)
          console.log('🔍 [handleUserMessage] nextQuestionText 존재 여부:', !!(nextQuestionText && nextQuestionText.trim()))
          console.log('🔍 [handleUserMessage] nextQuestionText 길이:', nextQuestionText ? nextQuestionText.length : 0)
          
          // 마지막 질문인지 확인 (이미 위에서 확인했지만 다시 확인)
          console.log('🔍 [handleUserMessage] 마지막 질문 여부:', {
            isLastQuestion,
            currentQuestionIndex: this.currentQuestionIndex,
            totalQuestions: this.totalQuestions
          })
          
          debugLog('🔍 평가/질문 분리 결과:', {
            hasEvaluation: !!evaluation,
            hasNextQuestion: !!(nextQuestionText && nextQuestionText.trim()),
            isLastQuestion: isLastQuestion,
            nextQuestionPreview: nextQuestionText ? nextQuestionText.substring(0, 100) : '(없음)',
            fullResponsePreview: filteredResponse.substring(0, 200)
          })
          
          // 평가 기록에 추가
          // evaluation이 있으면 사용하고, 없어도 마지막 질문이거나 evaluationText가 있으면 저장
          // nextQuestionText가 있어도 평가는 저장해야 함 (평가와 다음 질문이 함께 있는 경우)
          const shouldSaveEvaluation = evaluation || (isLastQuestion && evaluationText && evaluationText.trim()) || (evaluationText && evaluationText.trim())
          if (shouldSaveEvaluation) {
            // questionTitle이 비어있으면 currentQuestionIndex를 기반으로 생성
            if (!questionTitle || questionTitle.trim() === '') {
              if (this.originalQuestions && this.originalQuestions.length > 0 && this.currentQuestionIndex >= 0 && this.currentQuestionIndex < this.originalQuestions.length) {
                const currentQuestionObj = this.originalQuestions[this.currentQuestionIndex]
                if (currentQuestionObj) {
                  questionTitle = getLocalizedContentWithI18n(
                    currentQuestionObj,
                    'title',
                    this.$i18n,
                    this.language,
                    this.$t('voiceInterview.questionNumber', { number: this.currentQuestionIndex + 1 }) || `Question ${this.currentQuestionIndex + 1}`
                  )
                } else {
                  questionTitle = this.$t('voiceInterview.questionNumber', { number: this.currentQuestionIndex + 1 }) || `Question ${this.currentQuestionIndex + 1}`
                }
              } else {
                questionTitle = this.$t('voiceInterview.questionNumber', { number: this.currentQuestionIndex + 1 }) || `Question ${this.currentQuestionIndex + 1}`
              }
            }
            
            // questionTitle과 currentQuestionIndex를 모두 사용하여 중복 체크
            const existingEval = this.questionEvaluations.find(e => 
              e.questionIndex === this.currentQuestionIndex || 
              (e.questionTitle === questionTitle && questionTitle && questionTitle.trim() !== '')
            )
            if (!existingEval) {
              // 평가 부분만 저장 (evaluationText가 있으면 사용, 없으면 filteredResponse 전체)
              const evaluationContent = evaluationText && evaluationText.trim() ? evaluationText : filteredResponse
              
              // evaluation이 없으면 기본값 사용 (마지막 질문인 경우)
              const finalEvaluation = evaluation || {
                isCorrect: false, // 기본값: 평가 추출 실패 시 false
                accuracy: 70 // 기본값: 평가 추출 실패 시 70%
              }
              
              this.questionEvaluations.push({
                questionIndex: this.currentQuestionIndex, // 질문 인덱스 추가
                questionTitle: questionTitle,
                userAnswer: message,
                aiEvaluation: evaluationContent,
                isCorrect: finalEvaluation.isCorrect,
                accuracy: finalEvaluation.accuracy
              })
              debugLog('📝 평가 기록 추가:', {
                questionIndex: this.currentQuestionIndex,
                questionTitle: questionTitle.substring(0, 50),
                isCorrect: finalEvaluation.isCorrect,
                accuracy: finalEvaluation.accuracy,
                isLastQuestion: isLastQuestion,
                hasEvaluation: !!evaluation,
                totalEvaluations: this.questionEvaluations.length
              })
            } else {
              debugLog('⚠️ 평가 기록 중복 - 저장하지 않음:', {
                questionIndex: this.currentQuestionIndex,
                questionTitle: questionTitle.substring(0, 50),
                existingQuestionIndex: existingEval.questionIndex,
                existingQuestionTitle: existingEval.questionTitle ? existingEval.questionTitle.substring(0, 50) : '(없음)'
              })
            }
          }
          
          // conversationHistory에는 이미 sendChatMessage에서 추가됨
          // 하지만 평가와 질문이 분리된 경우, conversationHistory를 업데이트해야 함
          
          // 마지막 질문이고 평가만 있는 경우: conversationHistory의 마지막 assistant 메시지를 평가 부분만으로 업데이트
          // 또는 종합 피드백(인터뷰 종료 메시지)이 포함된 경우
          const isFinalFeedback = this.isFinalFeedbackMessage(evaluationText || filteredResponse)
          if ((isLastQuestion && evaluationText && evaluationText.trim() && !nextQuestionText) || isFinalFeedback) {
            console.log('🔍 [handleUserMessage] 마지막 질문 또는 종합 피드백 - conversationHistory에 평가만 표시 (TTS 재생 안함)', { isFinalFeedback, isLastQuestion })
            const finalText = evaluationText && evaluationText.trim() ? evaluationText : filteredResponse
            // conversationHistory의 마지막 assistant 메시지를 평가 부분만으로 업데이트
            for (let i = this.conversationHistory.length - 1; i >= 0; i--) {
              if (this.conversationHistory[i].role === 'assistant') {
                this.conversationHistory[i].content = finalText
                console.log('🔍 [handleUserMessage] conversationHistory 업데이트 완료 (평가만 표시)')
                debugLog('📝 마지막 질문 평가 또는 종합 피드백 conversationHistory 업데이트:', finalText.substring(0, 100))
                break
              }
            }
            // currentAIText도 업데이트 (화면 표시용)
            this.currentAIText = finalText
            // TTS는 재생하지 않음 (평가 또는 종합 피드백은 화면에만 표시)
            this.canSpeak = true
          } else if (evaluationText && evaluationText.trim() && nextQuestionText && nextQuestionText.trim()) {
            // 평가와 다음 질문이 모두 있는 경우: 하나의 메시지로 합쳐서 표시
            // (평가와 질문을 분리하지 않고 하나의 AI 메시지로 표시)
            const combinedMessage = evaluationText + '\n\n' + nextQuestionText
            console.log('🔍 [handleUserMessage] 평가와 질문 분리 - 하나의 메시지로 합쳐서 표시')
            for (let i = this.conversationHistory.length - 1; i >= 0; i--) {
              if (this.conversationHistory[i].role === 'assistant') {
                this.conversationHistory[i].content = combinedMessage
                console.log('🔍 [handleUserMessage] conversationHistory 업데이트 완료 (평가+질문 합쳐서 표시)')
                debugLog('📝 평가+질문 conversationHistory 업데이트:', combinedMessage.substring(0, 100))
                break
              }
            }
            // currentAIText는 전체 메시지로 설정 (화면 표시용)
            this.currentAIText = combinedMessage
            // 다음 질문으로 넘어가므로 currentQuestionIndex 증가
            if (this.currentQuestionIndex < this.totalQuestions - 1) {
              this.currentQuestionIndex++
              console.log('🔍 [handleUserMessage] 다음 질문으로 이동, currentQuestionIndex:', this.currentQuestionIndex)
              debugLog('📝 다음 질문으로 이동:', {
                previousIndex: this.currentQuestionIndex - 1,
                currentIndex: this.currentQuestionIndex,
                totalQuestions: this.totalQuestions
              })
            }
            // 다음 질문만 TTS로 재생 (평가 부분은 스킵)
            console.log('🔍 [handleUserMessage] 다음 질문이 있음, TTS로 재생 (평가 부분 스킵)')
            debugLog('🔊 다음 질문만 TTS 재생 (평가 부분 스킵):', nextQuestionText.substring(0, 100))
            this.speakText(nextQuestionText)
          } else if (nextQuestionText && nextQuestionText.trim()) {
            // 다음 질문만 있는 경우 (평가가 없는 경우 - 드물지만 가능)
            console.log('🔍 [handleUserMessage] 다음 질문만 있음')
            // 다음 질문을 conversationHistory에 추가 (화면 표시용)
            this.conversationHistory.push({
              role: 'assistant',
              content: nextQuestionText
            })
            console.log('🔍 [handleUserMessage] 다음 질문을 conversationHistory에 추가')
            debugLog('📝 다음 질문 conversationHistory 추가:', nextQuestionText.substring(0, 100))
            // currentAIText는 다음 질문으로 설정 (화면 표시용)
            this.currentAIText = nextQuestionText
            // 다음 질문으로 넘어가므로 currentQuestionIndex 증가
            if (this.currentQuestionIndex < this.totalQuestions - 1) {
              this.currentQuestionIndex++
              console.log('🔍 [handleUserMessage] 다음 질문으로 이동, currentQuestionIndex:', this.currentQuestionIndex)
              debugLog('📝 다음 질문으로 이동:', {
                previousIndex: this.currentQuestionIndex - 1,
                currentIndex: this.currentQuestionIndex,
                totalQuestions: this.totalQuestions
              })
            }
            // TTS로 재생
            console.log('🔍 [handleUserMessage] 다음 질문 TTS로 재생')
            debugLog('🔊 다음 질문 TTS 재생:', nextQuestionText.substring(0, 100))
            this.speakText(nextQuestionText)
          } else {
            // 평가만 있고 질문이 없는 경우 (마지막 질문일 가능성 또는 종합 피드백)
            if (evaluationText && evaluationText.trim()) {
              // 종합 피드백인지 확인
              const isFinalFeedback = this.isFinalFeedbackMessage(evaluationText)
              console.log('🔍 [handleUserMessage] 평가만 있음 - conversationHistory에 평가 표시', { isFinalFeedback })
              // conversationHistory의 마지막 assistant 메시지를 평가로 업데이트
              for (let i = this.conversationHistory.length - 1; i >= 0; i--) {
                if (this.conversationHistory[i].role === 'assistant') {
                  this.conversationHistory[i].content = evaluationText
                  console.log('🔍 [handleUserMessage] conversationHistory 업데이트 완료 (평가만 표시)')
                  debugLog('📝 평가 conversationHistory 업데이트:', evaluationText.substring(0, 100))
                  break
                }
              }
              // currentAIText도 업데이트 (화면 표시용)
              this.currentAIText = evaluationText
              // TTS는 재생하지 않음 (평가 또는 종합 피드백은 화면에만 표시)
              this.canSpeak = true
            } else {
              // 평가도 없고 질문도 없는 경우
              console.log('🔍 [handleUserMessage] 평가도 없고 질문도 없음')
              debugLog('📝 평가/질문 없음')
              this.canSpeak = true
            }
          }
        } else {
          // 평가가 아닌 경우 (초기 인사말 등) 전체를 TTS로 읽기
          // 단, 종합 피드백인 경우 TTS로 재생하지 않음
          const isFinalFeedback = this.isFinalFeedbackMessage(filteredResponse)
          if (isFinalFeedback) {
            console.log('🔍 [handleUserMessage] 종합 피드백 감지 - TTS 재생 안함')
            debugLog('📝 종합 피드백 감지, TTS 재생 안함:', filteredResponse.substring(0, 100))
            this.canSpeak = true
          } else {
            this.speakText(filteredResponse)
          }
        }
      } else {
        // API 호출 실패 시 사용자 메시지는 이미 추가했으므로 그대로 유지
        console.log('🔍 [handleUserMessage] ========== API 호출 실패 처리 시작 ==========')
        debugLog('⚠️ AI 응답을 받지 못했지만 사용자 메시지는 히스토리에 추가됨')
        
        // ========== API 실패 시에도 평가 기록 ==========
        // API 호출이 실패해도 사용자가 답변했으므로 평가를 기록해야 함
        const actualTotalQuestions = this.originalQuestions?.length || this.questions?.length || this.totalQuestions || 0
        const isLastQuestion = actualTotalQuestions > 0 && this.currentQuestionIndex >= actualTotalQuestions - 1
        
        console.log('🔍 [handleUserMessage] API 실패 시 평가 기록 시작:', {
          currentQuestionIndex: this.currentQuestionIndex,
          actualTotalQuestions: actualTotalQuestions,
          isLastQuestion: isLastQuestion,
          message: message.substring(0, 50)
        })
        
        // 현재 문제 정보 가져오기
        let questionTitle = ''
        if (this.originalQuestions && this.originalQuestions.length > 0 && this.currentQuestionIndex >= 0 && this.currentQuestionIndex < this.originalQuestions.length) {
          const currentQuestionObj = this.originalQuestions[this.currentQuestionIndex]
          if (currentQuestionObj) {
            questionTitle = getLocalizedContentWithI18n(
              currentQuestionObj,
              'title',
              this.$i18n,
              this.language,
              `Question ${this.currentQuestionIndex + 1}`
            )
          }
        } else if (this.questions && this.questions.length > 0 && this.currentQuestionIndex >= 0 && this.currentQuestionIndex < this.questions.length) {
          const currentQuestionObj = this.questions[this.currentQuestionIndex]
          if (currentQuestionObj) {
            questionTitle = getLocalizedContentWithI18n(
              currentQuestionObj,
              'title',
              this.$i18n,
              this.language,
              `Question ${this.currentQuestionIndex + 1}`
            )
          }
        }
        
        if (!questionTitle || questionTitle.trim() === '') {
          questionTitle = this.$t('voiceInterview.questionNumber', { number: this.currentQuestionIndex + 1 }) || `Question ${this.currentQuestionIndex + 1}`
        }
        
        // 이미 평가가 있는지 확인
        const existingEval = this.questionEvaluations.find(e => 
          e.questionIndex === this.currentQuestionIndex || 
          (e.questionTitle === questionTitle && questionTitle && questionTitle.trim() !== '')
        )
        
        if (!existingEval) {
          // API 실패 시 평가: 사용자 답변을 확인하여 "모르겠습니다" 같은 표현이 있으면 0점, 아니면 기본값
          let accuracy = 0
          let isCorrect = false
          
          const userMessageLower = message.trim().toLowerCase()
          const userDoesntKnowPatterns = [
            /모르겠/i, /잘\s*모르/i, /모름/i, /알\s*수\s*없/i,
            /don't\s*know/i, /don't\s*understand/i, /no\s*idea/i, /not\s*sure/i,
            /잘\s*모르겠습니다/i, /모르겠습니다/i, /모르겠어요/i
          ]
          
          const userDoesntKnow = userDoesntKnowPatterns.some(pattern => pattern.test(userMessageLower))
          
          if (userDoesntKnow) {
            accuracy = 0
            isCorrect = false
          } else {
            // 답변이 있는 경우 기본값 (API 실패로 정확한 평가 불가)
            accuracy = 50 // 기본값: API 실패 시 50%
            isCorrect = false
          }
          
          // 평가 기록 추가
          this.questionEvaluations.push({
            questionIndex: this.currentQuestionIndex,
            questionTitle: questionTitle,
            userAnswer: message.trim(),
            aiEvaluation: this.language === 'ko' 
              ? 'API 호출 실패로 인한 평가 미완료'
              : 'Evaluation incomplete due to API failure',
            isCorrect: isCorrect,
            accuracy: accuracy
          })
          
          console.log('🔍 [handleUserMessage] ✅ API 실패 시 평가 기록 추가 완료:', {
            questionIndex: this.currentQuestionIndex,
            questionTitle: questionTitle.substring(0, 50),
            userAnswer: message.trim().substring(0, 50),
            isCorrect: isCorrect,
            accuracy: accuracy,
            isLastQuestion: isLastQuestion,
            totalEvaluations: this.questionEvaluations.length
          })
          debugLog('📝 [handleUserMessage] ✅ API 실패 시 평가 기록 추가 완료:', {
            questionIndex: this.currentQuestionIndex,
            questionTitle: questionTitle.substring(0, 50),
            isLastQuestion: isLastQuestion,
            totalEvaluations: this.questionEvaluations.length
          })
        } else {
          console.log('🔍 [handleUserMessage] ⚠️ API 실패 시 평가 기록 스킵 (이미 평가 존재):', {
            questionIndex: this.currentQuestionIndex,
            questionTitle: questionTitle.substring(0, 50),
            existingEvaluations: this.questionEvaluations.filter(e => 
              e.questionIndex === this.currentQuestionIndex || 
              (e.questionTitle === questionTitle && questionTitle && questionTitle.trim() !== '')
            ).length
          })
          debugLog('📝 [handleUserMessage] ⚠️ API 실패 시 평가 기록 스킵 (이미 평가 존재)')
        }
        // ========== 평가 기록 완료 ==========
        console.log('🔍 [handleUserMessage] ========== API 호출 실패 처리 완료 ==========')
      }
    },
    
    async cleanup() {
      this.stopTimer()
      
      // 말하기 종료 타이머 정리
      if (this.speakingEndTimer) {
        clearTimeout(this.speakingEndTimer)
        this.speakingEndTimer = null
      }
      
      // iOS 네이티브 STT 정리
      if (this.isUsingNativeSTT && this.nativeSTT) {
        try {
          // 리스너 정리
          this.nativeSTTListeners.forEach(off => {
            try {
              if (off && typeof off === 'function') {
                off()
              } else if (off && typeof off.remove === 'function') {
                off.remove()
              }
            } catch (e) {
              debugLog('[cleanup] listener cleanup error (ignored):', e)
            }
          })
          this.nativeSTTListeners = []
          
          await this.nativeSTT.stop()
          this.isListening = false
          debugLog('✅ iOS 네이티브 STT 정리 완료')
        } catch (error) {
          debugLog('❌ iOS 네이티브 STT 정리 실패:', error)
        }
      }
      
      // Web Speech API Speech Recognition 정리
      if (this.speechRecognition) {
        this.speechRecognition.stop()
        this.speechRecognition = null
      }
      
      // iOS 네이티브 TTS 정리
      if (this.isUsingNativeTTS && this.nativeTTS) {
        try {
          await this.nativeTTS.stop()
          debugLog('✅ iOS 네이티브 TTS 정리 완료')
        } catch (error) {
          debugLog('❌ iOS 네이티브 TTS 정리 실패:', error)
        }
      }
      
      // Web Speech API TTS 정리
      if ('speechSynthesis' in window) {
        speechSynthesis.cancel()
      }
      
      // 미디어 스트림 정리
      if (this.mediaStream) {
        this.mediaStream.getTracks().forEach(track => track.stop())
        this.mediaStream = null
      }
    }
  }
}
</script>

<style scoped>
.mobile-voice-interview {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
}

/* 전달된 Instructions 디버그 패널 (임시 표시) */
.instructions-debug-panel {
  background: rgba(255, 255, 255, 0.95);
  color: #333;
  border: 3px solid #ff6b6b;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 20px;
  max-height: 300px;
  overflow-y: auto;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.instructions-debug-panel.empty {
  border-color: #ff0000;
  background: rgba(255, 240, 240, 0.95);
}

.instructions-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 2px solid #ff6b6b;
  font-size: 14px;
  flex-wrap: wrap;
}

.btn-send-instructions {
  margin-left: auto;
  padding: 6px 12px;
  background: #4a90e2;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.btn-send-instructions:hover:not(:disabled) {
  background: #357abd;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.btn-send-instructions:disabled {
  background: #999;
  cursor: not-allowed;
  opacity: 0.6;
}

.btn-send-instructions i {
  font-size: 11px;
}

.instructions-header i {
  color: #ff6b6b;
  font-size: 18px;
}

.instructions-header strong {
  flex: 1;
  color: #ff6b6b;
}

.instructions-length {
  background: #ff6b6b;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

.instructions-length.empty {
  background: #ff0000;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.instructions-content {
  max-height: 250px;
  overflow-y: auto;
}

.instructions-content pre {
  margin: 0;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 4px;
  font-size: 11px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
  color: #333;
  border: 1px solid #dee2e6;
}

.instructions-content pre.empty-instructions {
  background: #fff3cd;
  border-color: #ff0000;
  color: #ff0000;
  font-weight: bold;
  text-align: center;
  padding: 20px;
}

.connection-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 20px;
}

.connecting {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  font-size: 18px;
}

.error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  text-align: center;
}

.retry-btn {
  padding: 10px 20px;
  background: white;
  color: #667eea;
  border: none;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
}

.interview-screen {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 20px;
}

/* 대화 상태 표시기 */
.conversation-status {
  display: flex;
  justify-content: space-around;
  align-items: center;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 12px;
  padding: 12px;
  gap: 8px;
  margin-bottom: 10px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
  position: relative;
  flex: 1;
  justify-content: center;
  border: 2px solid transparent;
}

.status-indicator.active {
  background: rgba(255, 255, 255, 0.25);
  color: white;
  font-weight: 700;
  border-color: rgba(255, 255, 255, 0.3);
  box-shadow: 0 0 15px rgba(255, 255, 255, 0.2);
}

.status-indicator.ai-status.active {
  background: rgba(74, 144, 226, 0.4);
  color: #6bb3ff;
  border-color: rgba(74, 144, 226, 0.6);
  box-shadow: 0 0 20px rgba(74, 144, 226, 0.4);
}

.status-indicator.user-status.active {
  background: rgba(46, 204, 113, 0.4);
  color: #52e68a;
  border-color: rgba(46, 204, 113, 0.6);
  box-shadow: 0 0 20px rgba(46, 204, 113, 0.4);
}

.status-indicator.waiting-status.active {
  background: rgba(255, 255, 255, 0.15);
  color: rgba(255, 255, 255, 0.8);
  border-color: rgba(255, 255, 255, 0.2);
}

.status-indicator i {
  font-size: 16px;
}

.status-pulse {
  position: absolute;
  top: 50%;
  right: 10px;
  transform: translateY(-50%);
  width: 10px;
  height: 10px;
  background: currentColor;
  border-radius: 50%;
  animation: statusPulse 1.5s ease-in-out infinite;
  box-shadow: 0 0 10px currentColor;
}

@keyframes statusPulse {
  0%, 100% { 
    opacity: 1; 
    transform: translateY(-50%) scale(1); 
  }
  50% { 
    opacity: 0.7; 
    transform: translateY(-50%) scale(1.4); 
  }
}

.progress-bar {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  padding: 10px;
  position: relative;
  overflow: hidden;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0;
  font-size: 14px;
}

.progress-fill {
  height: 4px;
  background: white;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.instruction-notice {
  background: rgba(255, 193, 7, 0.15);
  border: 1px solid rgba(255, 193, 7, 0.4);
  border-radius: 8px;
  padding: 10px 15px;
  margin: 10px 0;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.9);
}

.instruction-notice i {
  color: #ffc107;
  font-size: 16px;
  flex-shrink: 0;
}

.instruction-notice span {
  line-height: 1.5;
}

.ai-response-area {
  flex: 1;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  padding: 0 20px;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  min-height: 200px;
  border: 2px solid transparent;
  transition: all 0.3s ease;
}

.ai-response-area.ai-active {
  background: rgba(74, 144, 226, 0.15);
  border-color: rgba(74, 144, 226, 0.5);
  box-shadow: 0 0 20px rgba(74, 144, 226, 0.3);
}

.area-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
  padding-top: 10px;
  font-size: 16px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.speaking-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
  padding: 4px 10px;
  background: rgba(74, 144, 226, 0.3);
  border-radius: 12px;
  font-size: 12px;
  color: #ffffff;
}

.speaking-badge.recording {
  background: rgba(46, 204, 113, 0.3);
  color: #2ecc71;
}

.wave-animation-mini {
  display: flex;
  gap: 2px;
  align-items: center;
  height: 12px;
}

.wave-bar-mini {
  width: 2px;
  height: 8px;
  background: currentColor;
  border-radius: 1px;
  animation: waveMini 0.8s ease-in-out infinite;
}

@keyframes waveMini {
  0%, 100% { transform: scaleY(0.5); }
  50% { transform: scaleY(1.5); }
}

.pulse-mini {
  width: 6px;
  height: 6px;
  background: currentColor;
  border-radius: 50%;
  animation: pulseMini 1s ease-in-out infinite;
}

@keyframes pulseMini {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.3); }
}

.empty-state {
  text-align: center;
  color: rgba(255, 255, 255, 0.5);
  padding: 40px 20px;
}

.ai-speaking {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.wave-animation {
  display: flex;
  gap: 4px;
  align-items: center;
  height: 40px;
}

.wave-bar {
  width: 4px;
  height: 20px;
  background: white;
  border-radius: 2px;
  animation: wave 1s ease-in-out infinite;
}

@keyframes wave {
  0%, 100% { transform: scaleY(0.5); }
  50% { transform: scaleY(1.5); }
}

.conversation-container {
  max-height: 500px;
  overflow-y: auto;
  padding: 15px;
  margin: 10px 0;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  scroll-behavior: smooth;
}

.ai-text-container {
  max-height: 400px;
  overflow-y: auto;
  padding: 15px;
  margin: 10px 0;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  scroll-behavior: smooth;
}

.conversation-item {
  margin-bottom: 20px;
  padding: 12px;
  border-radius: 8px;
  animation: fadeIn 0.3s ease-in;
}

.conversation-item.user {
  background: rgba(74, 144, 226, 0.15);
  border-left: 4px solid rgba(74, 144, 226, 0.8);
  margin-left: 20px;
}

.conversation-item.ai {
  background: rgba(255, 255, 255, 0.05);
  border-left: 4px solid rgba(255, 193, 7, 0.8);
  margin-right: 20px;
}

.conversation-item.current {
  background: rgba(74, 144, 226, 0.2);
  border-left-width: 5px;
}

.conversation-item.user.current {
  background: rgba(74, 144, 226, 0.25);
}

.conversation-item.ai.current {
  background: rgba(255, 193, 7, 0.15);
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 12px;
  font-weight: bold;
  color: rgba(255, 255, 255, 0.7);
}

.message-header i {
  font-size: 14px;
}

.conversation-item.user .message-header i {
  color: rgba(74, 144, 226, 1);
}

.conversation-item.ai .message-header i {
  color: rgba(255, 193, 7, 1);
}

.message-label {
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.message-text {
  font-size: 15px;
  line-height: 1.6;
  text-align: left;
  color: #e0e0e0;
  margin: 0;
  word-wrap: break-word;
  white-space: pre-wrap;
}

.message-text.placeholder {
  color: rgba(255, 255, 255, 0.5);
  font-style: italic;
}

.ai-text-item {
  margin-bottom: 15px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 6px;
  border-left: 3px solid rgba(74, 144, 226, 0.5);
}

.ai-text-item.current {
  background: rgba(74, 144, 226, 0.1);
  border-left-color: rgba(74, 144, 226, 0.8);
  animation: fadeIn 0.3s ease-in;
}

.ai-text-item:last-child {
  margin-bottom: 0;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.ai-text {
  font-size: 16px;
  line-height: 1.6;
  text-align: left;
  color: #e0e0e0;
  margin: 0;
  word-wrap: break-word;
  white-space: pre-wrap;
}

.ai-text.placeholder {
  color: rgba(255, 255, 255, 0.5);
  font-style: italic;
}

.question-display {
  text-align: center;
}

.question-title {
  font-size: 24px;
  margin-bottom: 15px;
}

.question-content {
  font-size: 18px;
  line-height: 1.6;
}

.user-response-area {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  padding: 0 20px;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
  min-height: 150px;
  border: 2px solid transparent;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.user-response-area.user-active {
  background: rgba(46, 204, 113, 0.15);
  border-color: rgba(46, 204, 113, 0.5);
  box-shadow: 0 0 20px rgba(46, 204, 113, 0.3);
  padding-top: 0 !important;
  padding-bottom: 0 !important;
}

.user-speaking {
  display: flex;
  flex-direction: column;
  gap: 15px;
  flex: 1;
  min-height: 80px; /* 120px → 80px로 축소 (2줄 기준) */
  overflow: hidden;
}

.recording-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
}

.pulse {
  width: 12px;
  height: 12px;
  background: #ff4444;
  border-radius: 50%;
  animation: pulse 1s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.2); }
}

.transcription {
  font-size: 16px;
  line-height: 1.6;
  flex: 1;
  min-height: 0;
  max-height: 60px; /* 2줄 정도 (line-height 1.6 * 2 = 3.2, 약 60px) */
  overflow-y: auto;
  overflow-x: hidden;
  scroll-behavior: smooth;
  padding: 0;
  margin: 0;
  word-wrap: break-word;
  white-space: pre-wrap;
  -webkit-overflow-scrolling: touch;
}

.final-text {
  color: white;
  margin-bottom: 5px;
}

.interim-text {
  color: rgba(255, 255, 255, 0.6);
  font-style: italic;
}

.waiting {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  text-align: center;
  color: rgba(255, 255, 255, 0.7);
  padding: 0px 20px;
  min-height: 100px;
  width: 100%;
  box-sizing: border-box;
}

.waiting i {
  font-size: 32px;
  opacity: 0.5;
}

.waiting p {
  width: 100%;
  word-wrap: break-word;
  overflow-wrap: break-word;
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

.controls {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.control-btn {
  flex: 1;
  min-width: 120px;
  padding: 15px;
  background: rgba(255, 255, 255, 0.2);
  border: 2px solid white;
  border-radius: 10px;
  color: white;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  transition: all 0.3s ease;
}

.control-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
}

.control-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.speak-btn {
  background: #4CAF50;
  border-color: #4CAF50;
}

.stop-btn {
  background: #ff4444;
  border-color: #ff4444;
}

.pause-btn {
  background: #ff9800;
  border-color: #ff9800;
}

.end-btn {
  background: #666;
  border-color: #666;
}

/* 종료 확인 모달 스타일 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000; /* 모달 오버레이 */
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 15px;
  max-width: 400px;
  width: 100%;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  color: #333;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.modal-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.modal-close {
  background: none;
  border: none;
  font-size: 20px;
  color: #999;
  cursor: pointer;
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
  background: #f0f0f0;
  color: #333;
}

.modal-body {
  padding: 20px;
}

.modal-footer {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  padding: 20px;
  border-top: 1px solid #eee;
}

.modal-footer .btn {
  padding: 10px 20px;
  border-radius: 8px;
  border: none;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.modal-footer .btn-secondary {
  background: #f0f0f0;
  color: #333;
}

.modal-footer .btn-secondary:hover {
  background: #e0e0e0;
}

.modal-footer .btn-danger {
  background: #dc3545;
  color: white;
}

.modal-footer .btn-danger:hover {
  background: #c82333;
}

.text-warning {
  color: #ff9800;
}

/* 결과 모달 스타일 */
.results-modal {
  max-width: 900px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.results-body {
  overflow-y: auto;
  max-height: calc(90vh - 140px);
  padding: 20px;
}

.results-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
  margin-bottom: 30px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 10px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.summary-label {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.summary-value {
  font-size: 24px;
  font-weight: bold;
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
  color: #ff9800;
}

.summary-value.low {
  color: #dc3545;
}

.results-details {
  margin-top: 20px;
}

.details-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #333;
}

.results-table-container {
  overflow-x: auto;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
}

.results-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
}

.results-table thead {
  background: #f8f9fa;
}

.results-table th {
  padding: 12px;
  text-align: left;
  font-weight: 600;
  font-size: 14px;
  color: #333;
  border-bottom: 2px solid #e0e0e0;
}

.results-table td {
  padding: 12px;
  font-size: 14px;
  color: #666;
  border-bottom: 1px solid #f0f0f0;
}

.results-table tbody tr:hover {
  background: #f8f9fa;
}

.results-table tbody tr.correct {
  background: #f0f9f4;
}

.results-table tbody tr.wrong {
  background: #fff5f5;
}

.results-table .col-number {
  width: 50px;
  text-align: center;
  font-weight: 600;
}

.results-table .col-question {
  max-width: 250px;
  word-break: break-word;
}

.results-table .col-answer {
  max-width: 300px;
  word-break: break-word;
}

.results-table .col-evaluation {
  max-width: 400px;
  word-break: break-word;
}

.results-table .col-evaluation .evaluation-content {
  max-height: 100px;
  overflow-y: auto;
  font-size: 13px;
  line-height: 1.4;
  color: #555;
}

.results-table .col-accuracy {
  width: 100px;
  text-align: center;
}

.results-table th.col-result {
  width: 100px;
  text-align: center;
}

.results-table td.col-result {
  width: 100px;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.results-table .col-accuracy .high {
  color: #28a745;
  font-weight: 600;
}

.results-table .col-accuracy .medium {
  color: #ff9800;
  font-weight: 600;
}

.results-table .col-accuracy .low {
  color: #dc3545;
  font-weight: 600;
}

.text-success {
  color: #28a745;
}

.text-danger {
  color: #dc3545;
}

.text-primary {
  color: #007bff;
}

.modal-footer .btn-primary {
  background: #007bff;
  color: white;
}

.modal-footer .btn-primary:hover {
  background: #0056b3;
}

@media (max-width: 768px) {
  .results-modal {
    max-width: 95%;
  }
  
  .results-summary {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .results-table-container {
    overflow-x: scroll;
  }
  
  .results-table {
    min-width: 600px;
  }
}

/* 모바일 전용 레이아웃 조정 */
@media (max-width: 768px) {
  /* 상단 여백 50px 추가 */
  .interview-screen {
    padding-top: 50px;
  }

  /* AI 응답 영역 높이 증가 (300px → 360px로 증가, 사용자 영역 축소분만큼) */
  .ai-response-area {
    min-height: 360px;
  }

  /* 대화 컨테이너도 약간 증가 */
  .conversation-container {
    max-height: 560px;
  }

  /* 사용자 응답 영역 높이 축소 (180px → 120px로 축소, 2줄 기준) */
  .user-response-area {
    min-height: 120px;
  }
  
  /* 사용자 말하는 중 상태에서 최소 높이 보장 */
  .user-response-area.user-active {
    min-height: 120px;
  }

  /* 컨트롤 버튼 높이 30% 축소: 패딩/폰트 사이즈 조정 */
  .control-btn {
    padding: 10px !important; /* 15px → 10px (약 33% 감소) */
    font-size: 14px !important; /* 16px → 14px */
    gap: 4px !important; /* 시각적 균형을 위해 간격 축소 */
    width: auto !important;
    height: auto !important;
    border-radius: 10px !important;
    min-width: 120px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
  }
  
  .control-btn span {
    display: inline !important;
  }
  
  .control-btn i {
    font-size: 14px !important;
  }
  
  /* 모달 푸터 버튼을 원형 버튼으로 */
  .modal-footer .btn {
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
    position: relative !important; /* 아이콘 절대 위치 기준 */
  }
  
  .modal-footer .btn i {
    font-size: 14px !important;
    line-height: 1 !important;
    color: white !important;
    margin: 0 !important; /* me-1 클래스의 마진 제거 */
    padding: 0 !important; /* 패딩 제거 */
    position: absolute !important; /* 절대 위치로 중앙 정렬 */
    left: 50% !important;
    top: 50% !important;
    transform: translate(-50%, -50%) !important; /* 정확한 중앙 정렬 */
  }
  
  .modal-footer .btn-secondary i {
    color: #333 !important;
  }
  
  .modal-footer .btn-secondary:hover i {
    color: white !important;
  }
  
  .modal-footer .btn span,
  .modal-footer .btn > :not(i) {
    display: none !important;
  }
}

@media (max-width: 576px) {
  .modal-footer .btn {
    width: 36px !important;
    height: 36px !important;
  }
  
  .modal-footer .btn i {
    font-size: 12px !important;
    margin: 0 !important; /* me-1 클래스의 마진 제거 */
    padding: 0 !important; /* 패딩 제거 */
    position: absolute !important; /* 절대 위치로 중앙 정렬 */
    left: 50% !important;
    top: 50% !important;
    transform: translate(-50%, -50%) !important; /* 정확한 중앙 정렬 */
  }
}

/* 모바일 앱 설치 안내 배너 (웹브라우저 전용) */
.mobile-app-banner {
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 10px;
  padding: 12px 16px;
  margin-bottom: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.banner-content {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.banner-content i.fa-mobile-alt {
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
  flex-shrink: 0;
}

.banner-text {
  flex: 1;
  color: rgba(255, 255, 255, 0.95);
  font-size: 13px;
  line-height: 1.5;
  min-width: 200px;
}

.app-store-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  color: white;
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.app-store-link:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
  text-decoration: none;
  color: white;
}

.app-store-link i {
  font-size: 16px;
}

@media (max-width: 768px) {
  .banner-content {
    flex-direction: column;
    align-items: stretch;
  }
  
  .app-store-link {
    width: 100%;
    justify-content: center;
  }
}

/* 안내 토글 버튼 */
.instruction-toggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.9);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: 8px;
}
.instruction-toggle:hover {
  background: rgba(255, 255, 255, 0.15);
}

/* 안내 숨기기 버튼 */
.instruction-hide {
  margin-left: auto;
  padding: 4px 8px;
  font-size: 12px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.25);
  background: transparent;
  color: rgba(255, 255, 255, 0.8);
  cursor: pointer;
}
</style>

