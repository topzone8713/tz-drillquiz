<template>
  <div class="voice-exam-interface" v-if="isVisible">
    <!-- 음성 인터페이스 헤더 -->
    <div class="voice-header">
      <div class="voice-title">
        <i class="fas fa-microphone-alt text-primary me-2"></i>
        {{ $t('voiceExam.title') }}
      </div>
      <div class="voice-actions">
        <button 
          @click="toggleListening" 
          :class="listeningButtonClass"
          :disabled="isSpeaking"
          v-if="isConnected || isVisible"
        >
          <i :class="listeningIcon"></i>
          {{ listeningButtonText }}
        </button>
        <button 
          @click="toggleVoiceMode" 
          class="btn btn-sm btn-outline-secondary"
          :disabled="isConnecting"
        >
          <i class="fas fa-times"></i>
          {{ $t('voiceExam.close') }}
        </button>
      </div>
    </div>

    <!-- 상태 메시지 표시 -->
    <div class="row">
      <!-- 오류 메시지 -->
      <div class="alert alert-danger" v-if="errorMessage">
        <i class="fas fa-exclamation-triangle me-2"></i>
        {{ errorMessage }}
      </div>
      
      <!-- 음성 품질 상태 -->
      <div class="alert alert-warning" v-if="consecutiveLowQualityCount > 0 && consecutiveLowQualityCount < maxConsecutiveLowQuality">
        <i class="fas fa-microphone-slash me-2"></i>
        {{ $t('voiceExam.qualityWarning', { count: consecutiveLowQualityCount }) }}
      </div>
      
    </div>
  </div>
</template>

<script>
import { debugLog } from '@/utils/debugUtils'
import { getLanguageCodeForSTT, getLocalizedContentWithI18n } from '@/utils/multilingualUtils'

export default {
  name: 'VoiceExamInterface',
  props: {
    isVisible: {
      type: Boolean,
      default: false
    },
    examId: {
      type: String,
      required: false,
      default: null
    },
    currentQuestion: {
      type: Object,
      default: null
    },
    examTitle: {
      type: String,
      required: false,
      default: ''
    },
    currentQuestionIndex: {
      type: Number,
      required: false,
      default: 0
    },
    totalQuestions: {
      type: Number,
      required: false,
      default: 0
    },
    examDifficulty: {
      type: Number,
      required: false,
      default: 5
    }
  },
  data() {
    return {
      // 연결 상태
      isConnecting: false,
      isConnected: false,
      errorMessage: '',
      
      // 음성 상태
      isListening: false,
      isSpeaking: false,
      isRestarting: false,
      isSubmitting: false,
      
      // 음성 품질 관리
      voiceQualityThreshold: 0.6,
      consecutiveLowQualityCount: 0,
      maxConsecutiveLowQuality: 3,
      
      // 설정
      selectedVoice: '',
      selectedLanguage: 'en',
      availableVoices: [],
      
      // WebRTC 및 OpenAI 관련
      realtimeSession: null,
      peerConnection: null,
      mediaStream: null,
      audioContext: null,
      audioWorklet: null,
      speechRecognition: null,
      
      // 타이머
      connectionTimeout: null,
      listeningTimeout: null,
      currentTimeoutDuration: 300000, // 5분 = 300초
      
      // 음성 인식된 텍스트
      recognizedText: '',
      tempInterimText: '',
      fullCombinedText: '', // 전체 텍스트 (확정 + 중간) 별도 관리
      
      // 네트워크 오류 재시도 카운터
      networkRetryCount: 0,
      
      // 오답 이유 표시
      showIncorrectReason: false,
      incorrectReason: ''
    }
  },
  computed: {
    listeningButtonClass() {
      return {
        'btn': true,
        'btn-primary': this.isListening,
        'btn-outline-primary': !this.isListening,
        'btn-lg': true,
        'voice-control-btn': true
      }
    },
    listeningIcon() {
      return this.isListening ? 'fas fa-stop' : 'fas fa-microphone'
    },
    listeningButtonText() {
      return this.isListening ? this.$t('voiceExam.stopListening') : this.$t('voiceExam.startListening')
    }
  },
  watch: {
    isVisible(newVal) {
      debugLog('VoiceExamInterface isVisible changed:', newVal)
      if (newVal) {
        this.$nextTick(() => {
          this.initializeVoiceInterface()
        })
      } else {
        this.cleanup()
      }
    },
    selectedVoice() {
      this.updateVoiceSettings()
    },
    selectedLanguage() {
      this.updateVoiceSettings()
      // 언어 변경 시 Speech Recognition 재설정
      if (this.speechRecognition) {
        const targetLang = getLanguageCodeForSTT(this.selectedLanguage)
        this.speechRecognition.lang = targetLang
        debugLog('🎤 [음성 인식] 언어 설정:', {
          selectedLanguage: this.selectedLanguage,
          targetLang: targetLang,
          actualLang: this.speechRecognition.lang
        })
      }
    },
    currentQuestion(newQuestion, oldQuestion) {
      // 문제가 변경되었을 때 (Pass 처리 후 다음 문제로 넘어간 경우)
      if (newQuestion && oldQuestion && newQuestion.id !== oldQuestion.id) {
        debugLog('🎤 [문제 변경] 감지됨:', {
          oldQuestionId: oldQuestion.id,
          newQuestionId: newQuestion.id,
          newQuestionTitle: newQuestion.title_ko || newQuestion.title_en,
          isVisible: this.isVisible,
          isConnected: this.isConnected,
          isListening: this.isListening,
          isSpeaking: this.isSpeaking
        })
        
        // 음성 모드가 활성화되어 있고 연결된 상태일 때만 다음 문제 읽기
        // 단, Pass/Fail 처리 후에만 실행 (사용자가 직접 답변을 제출한 경우)
        // 초기화 과정에서는 실행하지 않음
        if (this.isVisible && this.isConnected && !this.isConnecting) {
          debugLog('🎤 [문제 변경] 다음 문제 읽기 시작')
          setTimeout(() => {
            this.readNextQuestion()
          }, 500) // 0.5초 후 다음 문제 읽기
        } else {
          debugLog('🎤 [문제 변경] 다음 문제 읽기 건너뜀:', {
            reason: !this.isVisible ? '음성 모드 비활성화' : 
                   !this.isConnected ? '연결되지 않음' : 
                   this.isConnecting ? '초기화 중' : '기타'
          })
        }
      }
    }
  },
  mounted() {
    debugLog('VoiceExamInterface mounted, isVisible:', this.isVisible)
    if (this.isVisible) {
      this.$nextTick(() => {
        this.initializeVoiceInterface()
      })
    }
  },
  beforeDestroy() {
    this.cleanup()
  },
  methods: {
    async initializeVoiceInterface() {
      try {
        debugLog('🎤 initializeVoiceInterface 시작')
        debugLog('🎤 초기화 상태:', {
          isVisible: this.isVisible,
          examId: this.examId,
          currentQuestion: this.currentQuestion,
          selectedLanguage: this.selectedLanguage,
          selectedVoice: this.selectedVoice
        })
        
        this.isConnecting = true
        this.errorMessage = ''
        
        debugLog('🎤 브라우저 호환성 확인 중...')
        // 브라우저 호환성 확인
        if (!('mediaDevices' in navigator) || !('getUserMedia' in navigator.mediaDevices)) {
          throw new Error('이 브라우저는 음성 기능을 지원하지 않습니다.')
        }
        
        debugLog('🎤 브라우저 호환성 확인 완료')
        
        // Web Speech API 지원 확인
        if (!('speechSynthesis' in window)) {
          throw new Error('이 브라우저는 음성 합성 기능을 지원하지 않습니다.')
        }
        
        debugLog('🎤 Web Speech API 지원 확인 완료')
        
        // 사용 가능한 음성 목록 가져오기
        this.loadAvailableVoices()
        
        // 사용자 프로필 언어 설정과 동기화
        await this.syncLanguageWithGlobal()
        
        debugLog('🎤 언어 동기화 완료:', {
          selectedLanguage: this.selectedLanguage,
          availableVoices: this.availableVoices.length
        })
        
        // 마이크 권한 요청
        await this.requestMicrophonePermission()
        
        debugLog('🎤 마이크 권한 획득 완료')
        
        this.isConnected = true
        this.isConnecting = false
        
        debugLog('🎤 음성 인터페이스 초기화 완료 (Web Speech API 모드)')
        debugLog('🎤 최종 상태:', {
          isConnected: this.isConnected,
          isVisible: this.isVisible,
          selectedLanguage: this.selectedLanguage,
          currentQuestion: this.currentQuestion ? this.currentQuestion.id : 'N/A'
        })
        
        // 1초 딜레이 후 현재 문제를 자동으로 읽어주기 (완료 후 자동으로 음성 입력 시작됨)
        setTimeout(async () => {
          debugLog('🎤 문제 읽기 타이머 시작')
          if (this.currentQuestion) {
            debugLog('🎤 현재 문제 읽기 시작:', {
              questionId: this.currentQuestion.id,
              questionTitle: this.currentQuestion.title_ko || this.currentQuestion.title_en
            })
            await this.speakQuestion(this.currentQuestion)
          } else {
            debugLog('🎤 현재 문제가 없어서 읽기 건너뜀')
          }
        }, 1000)
        
      } catch (error) {
        this.errorMessage = error.message || '음성 인터페이스 초기화에 실패했습니다.'
        this.isConnecting = false
        debugLog('🎤 음성 인터페이스 초기화 실패:', error, 'error')
      }
    },

    async requestMicrophonePermission() {
      try {
        this.mediaStream = await navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true
          }
        })
        debugLog('마이크 권한 획득 성공')
      } catch (error) {
        throw new Error(this.$t('voiceExam.microphonePermissionError'))
      }
    },

    async createRealtimeSession() {
      try {
        if (!this.examId) {
          throw new Error('시험 ID가 없습니다.')
        }
        
        debugLog('🎤 OpenAI Realtime API 세션 생성 중...')
        
        const response = await this.$http.post('/api/realtime/session/', {
          exam_id: this.examId,
          voice: this.selectedVoice,
          language: this.selectedLanguage
        })
        
        this.realtimeSession = response.data
        debugLog('🎤 Realtime 세션 생성 완료:', this.realtimeSession.session_id)
        
        return this.realtimeSession
      } catch (error) {
        debugLog('🎤 Realtime 세션 생성 실패:', error, 'error')
        throw new Error(this.$t('voiceExam.sessionCreationError'))
      }
    },

    async setupWebRTCConnection() {
      try {
        debugLog('🎤 WebRTC 연결 설정 시작...')
        
        if (!this.realtimeSession) {
          throw new Error('Realtime 세션이 없습니다.')
        }
        
        // WebRTC PeerConnection 생성
        this.peerConnection = new RTCPeerConnection({
          iceServers: [
            { urls: 'stun:stun.l.google.com:19302' },
            { urls: 'stun:stun1.l.google.com:19302' }
          ]
        })
        
        // 마이크 스트림 가져오기
        this.mediaStream = await navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true
          }
        })
        
        // 마이크 트랙을 PeerConnection에 추가
        this.mediaStream.getTracks().forEach(track => {
          this.peerConnection.addTrack(track, this.mediaStream)
        })
        
        // ICE candidate 이벤트 처리
        this.peerConnection.onicecandidate = (event) => {
          if (event.candidate) {
            debugLog('🎤 ICE candidate 생성:', event.candidate)
            // OpenAI Realtime API에 ICE candidate 전송
            this.sendIceCandidate(event.candidate)
          }
        }
        
        // 원격 스트림 수신 처리
        this.peerConnection.ontrack = (event) => {
          debugLog('🎤 원격 오디오 스트림 수신')
          const remoteStream = event.streams[0]
          this.playRemoteAudio(remoteStream)
        }
        
        // 연결 상태 변경 처리
        this.peerConnection.onconnectionstatechange = () => {
          debugLog('🎤 WebRTC 연결 상태:', this.peerConnection.connectionState)
          if (this.peerConnection.connectionState === 'connected') {
            debugLog('🎤 WebRTC 연결 완료!')
          }
        }
        
        // OpenAI Realtime API와 WebRTC 연결 시작
        await this.connectToOpenAI()
        
        debugLog('🎤 WebRTC 연결 설정 완료')
      } catch (error) {
        debugLog('🎤 WebRTC 연결 설정 실패:', error, 'error')
        throw new Error(this.$t('voiceExam.webrtcConnectionError'))
      }
    },

    async connectToOpenAI() {
      try {
        debugLog('🎤 OpenAI Realtime API 연결 시작...')
        
        // Offer 생성
        const offer = await this.peerConnection.createOffer()
        await this.peerConnection.setLocalDescription(offer)
        
        // OpenAI Realtime API에 offer 전송
        const response = await this.$http.post(`/api/realtime/session/${this.realtimeSession.session_id}/offer/`, {
          offer: offer
        })
        
        // Answer 수신 및 설정
        const answer = response.data.answer
        await this.peerConnection.setRemoteDescription(new RTCSessionDescription(answer))
        
        debugLog('🎤 OpenAI Realtime API 연결 완료')
      } catch (error) {
        debugLog('🎤 OpenAI Realtime API 연결 실패:', error, 'error')
        throw error
      }
    },

    async sendIceCandidate(candidate) {
      try {
        await this.$http.post(`/api/realtime/session/${this.realtimeSession.session_id}/ice-candidate/`, {
          candidate: candidate
        })
        debugLog('🎤 ICE candidate 전송 완료')
      } catch (error) {
        debugLog('🎤 ICE candidate 전송 실패:', error, 'error')
      }
    },

    playRemoteAudio(stream) {
      try {
        // 원격 오디오 스트림 재생
        const audio = new Audio()
        audio.srcObject = stream
        audio.play()
        debugLog('🎤 원격 오디오 재생 시작')
      } catch (error) {
        debugLog('🎤 원격 오디오 재생 실패:', error, 'error')
      }
    },

    async toggleListening() {
      if (this.isListening) {
        // Submit Answer 버튼 - 음성 인식된 텍스트로 평가 진행
        await this.submitAnswer()
      } else {
        // Starting Answer 버튼 - 음성 인식 시작
        await this.startListening()
      }
    },

    async startListening() {
      try {
        this.isListening = true
        this.isSubmitting = false // 제출 상태 초기화
        this.errorMessage = ''
        this.recognizedText = '' // 새로운 음성 인식 시작 시 텍스트 초기화
        this.networkRetryCount = 0 // 네트워크 재시도 카운터 리셋
        this.tempInterimText = '' // 중간 결과 텍스트 초기화
        this.fullCombinedText = '' // 전체 텍스트 초기화
        this.showIncorrectReason = false // 오답 이유 숨기기
        this.incorrectReason = '' // 오답 이유 초기화
        
        // 실시간 텍스트 초기화를 부모 컴포넌트로 전달
        const initData = {
          interimText: '',
          finalText: '',
          combinedText: ''
        }
        console.log('🎤 [REALTIME EMIT] 음성 인식 시작 - 초기화:', initData)
        this.$emit('realtime-text', initData)
        
        // 부모 컴포넌트의 오답 메시지도 숨기기
        this.$emit('hide-incorrect-reason')
        
        debugLog('🎤 음성 입력 시작')
        
        // 마이크 권한 확인 및 트랙 활성화
        try {
          if (this.mediaStream) {
            this.mediaStream.getAudioTracks().forEach(track => {
              track.enabled = true
              debugLog('🎤 [마이크] 트랙 활성화:', {
                kind: track.kind,
                enabled: track.enabled,
                readyState: track.readyState,
                muted: track.muted
              })
            })
          } else {
            debugLog('🎤 [마이크] mediaStream이 없음, 마이크 권한 요청', null, 'warning')
            // 마이크 권한 요청
            navigator.mediaDevices.getUserMedia({ audio: true })
              .then(stream => {
                debugLog('🎤 [마이크] 권한 획득 성공')
                this.mediaStream = stream
                stream.getAudioTracks().forEach(track => {
                  track.enabled = true
                  debugLog('🎤 [마이크] 새 트랙 활성화:', {
                    kind: track.kind,
                    enabled: track.enabled,
                    readyState: track.readyState,
                    muted: track.muted
                  })
                })
              })
              .catch(error => {
                debugLog('🎤 [마이크] 권한 획득 실패:', error, 'error')
                this.errorMessage = '마이크 권한이 필요합니다. 브라우저 설정에서 마이크 권한을 허용해주세요.'
              })
          }
        } catch (error) {
          debugLog('🎤 [마이크] 트랙 활성화 실패:', error, 'error')
        }
        
        // Web Speech Recognition API 사용 (지원하는 경우)
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
          debugLog('🎤 [음성 인식] Speech Recognition API 지원 확인됨')
          this.setupSpeechRecognition()
        } else {
          debugLog('🎤 Speech Recognition API를 지원하지 않는 브라우저입니다.')
        }
        
        // 자동 타임아웃 설정 (5분으로 설정)
        this.currentTimeoutDuration = 300000 // 5분 = 300초
        this.listeningTimeout = setTimeout(() => {
          debugLog('🎤 [자동 재시작] 5분 타임아웃, 음성 인식 재시작')
          this.restartListening()
        }, this.currentTimeoutDuration)
        
        debugLog('🎤 음성 입력 활성화 완료')
        
      } catch (error) {
        this.errorMessage = error.message || '음성 입력 시작에 실패했습니다.'
        this.isListening = false
        debugLog('🎤 음성 입력 시작 실패:', error, 'error')
      }
    },

    async stopListening() {
      try {
        this.isListening = false
        this.isRestarting = false // 재시작 플래그 초기화
        
        // 중지 시 중간 결과는 누적하지 않음 (문장 끊어짐 방지)
        if (this.tempInterimText && this.tempInterimText.trim()) {
          debugLog('🎤 [중지] 중간 결과 무시 (문장 끊어짐 방지):', this.tempInterimText)
          this.tempInterimText = ''
        }
        
        // Speech Recognition 중지
        if (this.speechRecognition) {
          this.speechRecognition.stop()
        }
        
        // 마이크 트랙 비활성화
        if (this.mediaStream) {
          this.mediaStream.getAudioTracks().forEach(track => {
            track.enabled = false
          })
        }
        
        debugLog('🎤 음성 입력 중지')
        
      } catch (error) {
        debugLog('🎤 음성 입력 중지 실패:', error, 'error')
      }
    },

    // 텍스트를 자연스럽게 연결하는 메서드
    connectTexts(existingText, newText) {
      if (!existingText.trim()) {
        return newText.trim()
      }
      
      const existing = existingText.trim()
      const newPart = newText.trim()
      
      // 기존 텍스트가 문장으로 끝나는지 확인
      const endsWithPunctuation = /[.!?]$/.test(existing)
      const startsWithCapital = /^[A-Z가-힣]/.test(newPart)
      
      // 재시작으로 인한 연결인지 확인 (기존 텍스트가 길고 새 텍스트가 짧은 경우)
      const isRestartConnection = existing.length > 50 && newPart.length < 100
      
      // 자연스러운 연결을 위한 처리
      if (endsWithPunctuation && startsWithCapital) {
        // 문장 끝 + 대문자 시작 → 공백으로 연결
        return existing + ' ' + newPart
      } else if (!endsWithPunctuation && startsWithCapital) {
        // 문장 끝 아님 + 대문자 시작 → 마침표 추가 후 연결
        return existing + '. ' + newPart
      } else if (endsWithPunctuation && !startsWithCapital) {
        // 문장 끝 + 소문자 시작 → 공백으로 연결
        return existing + ' ' + newPart
      } else if (isRestartConnection && !endsWithPunctuation) {
        // 재시작 연결 + 문장 끝 아님 → 마침표 추가 후 연결
        return existing + '. ' + newPart
      } else {
        // 기본적으로 공백으로 연결
        return existing + ' ' + newPart
      }
    },
    
    // 문장 완성 감지 함수 제거됨 (음성에서는 구두점을 직접 말할 수 없음)

    // 중간 결과를 최종 텍스트에 누적하는 메서드 (강력한 중복 제거)
    accumulateInterimText() {
      if (this.tempInterimText && this.tempInterimText.trim()) {
        const newText = this.tempInterimText.trim()
        
        // 매우 강력한 중복 제거: 단어 단위로 비교
        const existingWords = this.recognizedText.toLowerCase().split(/\s+/).filter(w => w.length > 2)
        const newWords = newText.toLowerCase().split(/\s+/).filter(w => w.length > 2)
        
        // 새로운 단어가 50% 이상 중복되면 제외 (더 강력한 중복 제거)
        const duplicateCount = newWords.filter(word => existingWords.includes(word)).length
        const duplicateRatio = newWords.length > 0 ? duplicateCount / newWords.length : 0
        
        // 문장 단위로도 중복 체크
        const existingSentences = this.recognizedText.split(/[.!?]\s*/).filter(s => s.trim().length > 10)
        const newSentences = newText.split(/[.!?]\s*/).filter(s => s.trim().length > 10)
        const sentenceDuplicate = newSentences.some(newSentence => 
          existingSentences.some(existingSentence => 
            existingSentence.includes(newSentence) || newSentence.includes(existingSentence)
          )
        )
        
        if (duplicateRatio < 0.5 && !sentenceDuplicate) { // 50% 미만 중복이고 문장 중복이 없을 때만 추가
          this.recognizedText = this.connectTexts(this.recognizedText, newText)
          debugLog('🎤 [중간 결과 누적] 새로운 내용 추가됨:', {
            newText: newText,
            duplicateRatio: duplicateRatio.toFixed(2),
            accumulatedLength: this.recognizedText.length
          })
        } else {
          debugLog('🎤 [중간 결과 누적] 중복 내용 제외됨:', {
            newText: newText,
            duplicateRatio: duplicateRatio.toFixed(2)
          })
        }
        
        // 중간 결과 초기화
        this.tempInterimText = ''
      }
    },

    async restartListening() {
      try {
        // 중복 재시작 방지
        if (this.isRestarting) {
          debugLog('🎤 [자동 재시작] 이미 재시작 중, 건너뜀')
          return
        }
        
        this.isRestarting = true
        debugLog('🎤 [자동 재시작] 음성 인식 재시작 시작')
        
        // 재시작 시 중간 결과는 누적하지 않음 (문장 끊어짐 방지)
        if (this.tempInterimText && this.tempInterimText.trim()) {
          debugLog('🎤 [재시작] 중간 결과 무시 (문장 끊어짐 방지):', this.tempInterimText)
          this.tempInterimText = ''
        }
        
        // 현재까지 누적된 텍스트 보존
        const currentText = this.recognizedText
        debugLog('🎤 [자동 재시작] 현재 누적 텍스트 보존:', {
          length: currentText.length,
          text: currentText.substring(0, 100) + '...'
        })
        
        // 기존 음성 인식 중지
        if (this.speechRecognition) {
          this.speechRecognition.stop()
        }
        
        // 중간 결과 누적 타이머 정리
        if (this.interimUpdateTimer) {
          clearInterval(this.interimUpdateTimer)
          this.interimUpdateTimer = null
        }
        
        // 잠시 대기 후 재시작 (지연 시간 증가)
        setTimeout(() => {
          if (this.isListening && this.isRestarting) {
            debugLog('🎤 [자동 재시작] 음성 인식 재시작 실행')
            this.setupSpeechRecognition()
            this.isRestarting = false
            
            // 새로운 타임아웃 설정 (점진적 증가: 1분씩 증가, 최대 5분)
            this.currentTimeoutDuration = Math.min(this.currentTimeoutDuration + 60000, 300000) // 1분씩 증가, 최대 5분
            this.listeningTimeout = setTimeout(() => {
              debugLog(`🎤 [자동 재시작] ${this.currentTimeoutDuration/1000}초 타임아웃, 음성 인식 재시작`)
              this.restartListening()
            }, this.currentTimeoutDuration)
          } else {
            this.isRestarting = false
          }
        }, 5000) // 3초 → 5초로 증가
        
      } catch (error) {
        debugLog('🎤 [자동 재시작] 재시작 실패:', error, 'error')
        this.isRestarting = false
      }
    },

    async submitAnswer() {
      try {
        // 중복 제출 방지
        if (this.isSubmitting) {
          debugLog('🎤 [Submit Answer] 이미 제출 중, 건너뜀')
          return
        }
        
        this.isSubmitting = true
        debugLog('🎤 [Submit Answer] 답변 제출 시작')
        
        // Submit 시 중간 결과를 확정 텍스트에 누적 (강화된 로직)
        if (this.tempInterimText && this.tempInterimText.trim()) {
          debugLog('🎤 [Submit Answer] 중간 결과를 확정 텍스트에 누적:', {
            interimText: this.tempInterimText,
            length: this.tempInterimText.length,
            beforeAccumulate: this.recognizedText
          })
          this.accumulateInterimText()
          debugLog('🎤 [Submit Answer] 누적 후 확정 텍스트:', {
            afterAccumulate: this.recognizedText,
            length: this.recognizedText.length
          })
        } else {
          debugLog('🎤 [Submit Answer] 중간 결과 없음:', {
            tempInterimText: this.tempInterimText,
            recognizedText: this.recognizedText,
            fullCombinedText: this.fullCombinedText
          })
        }
        
        // 전체 텍스트 사용 (확정된 결과 + 중간 결과)
        let textToSubmit = this.fullCombinedText || this.recognizedText
        if (!textToSubmit && this.tempInterimText) {
          textToSubmit = this.tempInterimText
          debugLog('🎤 [Submit Answer] 최종 결과 없음, 중간 결과 사용:', {
            interimText: this.tempInterimText,
            length: this.tempInterimText.length
          })
        }
        
        debugLog('🎤 [Submit Answer] 서버로 전송할 텍스트:', {
          fullCombinedText: this.fullCombinedText,
          recognizedText: this.recognizedText,
          tempInterimText: this.tempInterimText,
          finalTextToSubmit: textToSubmit
        })
        
        if (!textToSubmit || textToSubmit.trim().length === 0) {
          debugLog('🎤 [Submit Answer] 인식된 텍스트가 없음')
          this.isSubmitting = false
          return
        }
        
        // 음성 입력 중지
        await this.stopListening()
        
        // 인식된 텍스트로 평가 진행
        await this.handleVoiceInput(textToSubmit)
        
        // 인식된 텍스트 초기화
        this.recognizedText = ''
        this.tempInterimText = ''
        
        debugLog('🎤 [Submit Answer] 답변 제출 완료')
        this.isSubmitting = false
      } catch (error) {
        debugLog('🎤 [Submit Answer] 답변 제출 실패:', error, 'error')
        this.isSubmitting = false
      }
    },

    // 음성 출력은 자동으로 작동하므로 별도 버튼 불필요

    isLastQuestion() {
      // 현재 문제가 마지막 문제인지 확인
      // currentQuestionIndex는 0부터 시작하므로 totalQuestions - 1과 비교
      return this.currentQuestionIndex >= this.totalQuestions - 1
    },

    readNextQuestion() {
      try {
        debugLog('🎤 [다음 문제] 읽기 시작')
        
        // 현재 문제가 있는지 확인
        if (this.currentQuestion) {
          // 문제 읽기
          this.speakQuestion(this.currentQuestion)
        } else {
          debugLog('🎤 [다음 문제] 현재 문제가 없음')
          this.speakText('더 이상 문제가 없습니다.')
        }
      } catch (error) {
        debugLog('🎤 [다음 문제] 읽기 실패:', error, 'error')
      }
    },

    handlePass() {
      try {
        debugLog('🎤 [PASS] 정답 처리 시작')
        
        // 부모 컴포넌트(TakeExam)의 Pass 버튼 클릭 효과 호출
        this.$emit('handle-pass')
        
        debugLog('🎤 [PASS] 정답 처리 완료')
      } catch (error) {
        debugLog('🎤 [PASS] 정답 처리 실패:', error, 'error')
      }
    },

    handleFail() {
      try {
        debugLog('🎤 [FAIL] 오답 처리 시작')
        
        // 부모 컴포넌트(TakeExam)의 Fail 버튼 클릭 효과 호출
        this.$emit('handle-fail')
        
        debugLog('🎤 [FAIL] 오답 처리 완료')
      } catch (error) {
        debugLog('🎤 [FAIL] 오답 처리 실패:', error, 'error')
      }
    },

    loadAvailableVoices() {
      try {
        if ('speechSynthesis' in window) {
          // 음성 목록이 로드될 때까지 기다림
          const loadVoices = () => {
            const voices = speechSynthesis.getVoices()
            this.availableVoices = voices.filter(voice => 
              voice.lang.startsWith('ko') || voice.lang.startsWith('en')
            )
            
            // 기본 음성 설정 (한국어 우선)
            if (this.availableVoices.length > 0) {
              const koreanVoice = this.availableVoices.find(voice => voice.lang.startsWith('ko'))
              this.selectedVoice = koreanVoice ? koreanVoice.name : this.availableVoices[0].name
            }
            
            debugLog('🎤 사용 가능한 음성 목록:', this.availableVoices)
          }
          
          // 음성이 로드되지 않은 경우 이벤트 리스너 등록
          if (speechSynthesis.getVoices().length === 0) {
            speechSynthesis.addEventListener('voiceschanged', loadVoices)
          } else {
            loadVoices()
          }
        }
      } catch (error) {
        debugLog('🎤 음성 목록 로드 실패:', error, 'error')
      }
    },

    async syncLanguageWithGlobal() {
      try {
        debugLog('🎤 [언어 동기화] 시작')
        
        // 사용자 프로필에서 언어 설정 가져오기
        try {
          debugLog('🎤 [언어 동기화] 사용자 프로필 API 호출 중...')
          const response = await this.$http.get('/api/user-profile/')
          debugLog('🎤 [언어 동기화] 사용자 프로필 응답:', response.data)
          
          const userLanguage = response.data.language || 'en'
          this.selectedLanguage = userLanguage
          debugLog('🎤 [언어 설정] 사용자 프로필 언어 설정과 동기화:', {
            userLanguage: userLanguage,
            selectedLanguage: this.selectedLanguage,
            responseData: response.data,
            currentI18nLocale: this.$i18n ? this.$i18n.locale : 'unknown'
          })
        } catch (error) {
          // 프로필 가져오기 실패 시 전역 언어 설정 사용
          if (this.$i18n && this.$i18n.locale) {
            this.selectedLanguage = this.$i18n.locale
            debugLog('🎤 전역 언어 설정과 동기화 (프로필 실패):', this.selectedLanguage)
          } else {
            this.selectedLanguage = this.$i18n.locale || 'en' // 기본값
            debugLog('🎤 기본 언어 설정 사용:', this.selectedLanguage)
          }
        }
        
        // Speech Recognition 언어도 즉시 업데이트
        if (this.speechRecognition) {
          const targetLang = getLanguageCodeForSTT(this.selectedLanguage)
          this.speechRecognition.lang = targetLang
          debugLog('🎤 [음성 인식] 언어 설정:', {
            selectedLanguage: this.selectedLanguage,
            targetLang: targetLang,
            actualLang: this.speechRecognition.lang
          })
        }
      } catch (error) {
        debugLog('🎤 언어 설정 동기화 실패:', error, 'error')
        this.selectedLanguage = this.$i18n.locale || 'en' // 기본값
      }
    },

    setupSpeechRecognition() {
      try {
        debugLog('🎤 [음성 인식] Speech Recognition 설정 시작')
        
        // 기존 인스턴스가 있으면 중지
        if (this.speechRecognition) {
          debugLog('🎤 [중복 방지] 기존 Speech Recognition 인스턴스 중지')
          try {
            this.speechRecognition.stop()
            debugLog('🎤 [중복 방지] 기존 인스턴스 중지 완료')
          } catch (stopError) {
            debugLog('🎤 [중복 방지] 기존 인스턴스 중지 실패:', stopError, 'warning')
          }
          this.speechRecognition = null
          
          // 기존 인스턴스 완전 정리 후 잠시 대기
          setTimeout(() => {
            debugLog('🎤 [음성 인식] 기존 인스턴스 정리 완료, 새 인스턴스 생성')
            this.createNewSpeechRecognition()
          }, 500)
          return
        }
        
        debugLog('🎤 [음성 인식] 새 Speech Recognition 인스턴스 생성')
        this.createNewSpeechRecognition()
        
      } catch (error) {
        debugLog('🎤 Speech Recognition 설정 실패:', error, 'error')
      }
    },

    createNewSpeechRecognition() {
      try {
        debugLog('🎤 [음성 인식] 새 Speech Recognition 인스턴스 생성 시작')
        
        // 브라우저 지원 확인
        const hasWebkitSpeechRecognition = 'webkitSpeechRecognition' in window
        const hasSpeechRecognition = 'SpeechRecognition' in window
        
        debugLog('🎤 [음성 인식] 브라우저 지원 확인:', {
          hasWebkitSpeechRecognition,
          hasSpeechRecognition,
          userAgent: navigator.userAgent,
          isSecureContext: window.isSecureContext
        })
        
        if (!hasWebkitSpeechRecognition && !hasSpeechRecognition) {
          debugLog('🎤 [오류] Speech Recognition API를 지원하지 않는 브라우저입니다.', null, 'error')
          this.errorMessage = '이 브라우저는 음성 인식을 지원하지 않습니다.'
          return
        }
        
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
        this.speechRecognition = new SpeechRecognition()
        debugLog('🎤 [음성 인식] Speech Recognition 인스턴스 생성 완료')
        
        this.speechRecognition.continuous = true
        this.speechRecognition.interimResults = true  // 중간 결과도 수집
        
        // 언어 설정
        const targetLang = this.selectedLanguage === 'ko' ? 'ko-KR' : 'en-US'
        this.speechRecognition.lang = targetLang
        debugLog('🎤 [음성 인식] 언어 설정:', {
          selectedLanguage: this.selectedLanguage,
          targetLang: targetLang,
          actualLang: this.speechRecognition.lang,
          currentI18nLocale: this.$i18n.locale
        })
        
        // 언어 설정 후 잠시 대기 (브라우저가 언어를 인식할 시간을 줌)
        setTimeout(() => {
          debugLog('🎤 [음성 인식] 언어 설정 후 상태 확인:', {
            lang: this.speechRecognition.lang,
            selectedLanguage: this.selectedLanguage
          })
        }, 100)
        
        this.speechRecognition.maxAlternatives = 3  // 여러 대안 결과 수집으로 정확도 향상
        
        debugLog('🎤 [음성 인식] 설정 완료:', {
          continuous: this.speechRecognition.continuous,
          interimResults: this.speechRecognition.interimResults,
          lang: this.speechRecognition.lang,
          maxAlternatives: this.speechRecognition.maxAlternatives,
          selectedLanguage: this.selectedLanguage
        })
        
        // 음성 인식 품질 향상을 위한 추가 설정
        if (this.speechRecognition.serviceURI) {
          this.speechRecognition.serviceURI = 'wss://www.google.com/speech-api/full-duplex/v1/up'
        }
        
        this.speechRecognition.onstart = () => {
          console.log('🎤 [음성 인식] onstart 이벤트 발생!')
          console.log('🎤 [음성 인식] speechRecognition 객체:', this.speechRecognition)
          
          debugLog('🎤 [음성 인식] onstart 이벤트 발생')
          debugLog('🎤 [음성 인식] 현재 상태:', {
            isListening: this.isListening,
            isRestarting: this.isRestarting,
            speechRecognition: !!this.speechRecognition,
            lang: this.speechRecognition?.lang,
            continuous: this.speechRecognition?.continuous,
            interimResults: this.speechRecognition?.interimResults,
            maxAlternatives: this.speechRecognition?.maxAlternatives
          })
          
          // 음성 인식 시작 후 잠시 대기하여 상태 확인
          setTimeout(() => {
            debugLog('🎤 [음성 인식] 시작 후 1초 상태 확인:', {
              isListening: this.isListening,
              speechRecognition: !!this.speechRecognition,
              lang: this.speechRecognition?.lang
            })
          }, 1000)
        }
        
        this.speechRecognition.onresult = (event) => {
          console.log('🎤 [음성 인식] onresult 이벤트 발생!')
          
          let newFinalTranscript = ''
          let interimTranscript = ''
          let bestConfidence = 0
          
          debugLog('🎤 [음성 인식] 이벤트 수신:', {
            resultIndex: event.resultIndex,
            resultsLength: event.results.length,
            timestamp: new Date().toLocaleTimeString()
          })
          
          for (let i = event.resultIndex; i < event.results.length; i++) {
            const result = event.results[i]
            const isFinal = result.isFinal
            
            // 여러 대안 결과 중 가장 높은 신뢰도 선택
            let bestAlternative = result[0]
            for (let j = 0; j < result.length; j++) {
              if (result[j].confidence > bestAlternative.confidence) {
                bestAlternative = result[j]
              }
            }
            
            const transcript = bestAlternative.transcript
            const confidence = bestAlternative.confidence
            
            debugLog('🎤 [음성 인식] 개별 결과:', {
              index: i,
              transcript: transcript,
              confidence: confidence,
              isFinal: isFinal,
              alternatives: result.length,
              timestamp: new Date().toLocaleTimeString()
            })
            
            if (isFinal) {
              // 음성 품질 검증 및 처리
              if (this.validateVoiceQuality(transcript, confidence)) {
                newFinalTranscript += transcript
                if (confidence > bestConfidence) {
                  bestConfidence = confidence
                }
                // 연속된 낮은 품질 카운터 리셋
                this.consecutiveLowQualityCount = 0
              } else {
                this.consecutiveLowQualityCount++
                debugLog('🎤 [음성 인식] 낮은 품질로 인한 결과 제외:', {
                  transcript: transcript,
                  confidence: confidence,
                  threshold: this.voiceQualityThreshold,
                  consecutiveLowQuality: this.consecutiveLowQualityCount
                })
                
                // 연속된 낮은 품질이 많으면 사용자에게 알림
                if (this.consecutiveLowQualityCount >= this.maxConsecutiveLowQuality) {
                  this.notifyVoiceQualityIssue()
                }
              }
            } else {
              interimTranscript += transcript
            }
          }
          
          // 중간 결과 저장 및 누적
          if (interimTranscript) {
            debugLog('🎤 [음성 인식] 중간 결과:', {
              text: interimTranscript,
              length: interimTranscript.length,
              isListening: this.isListening
            })
            
            // 중간 결과를 임시로 저장
            this.tempInterimText = interimTranscript
            
            // 중간 결과를 실시간으로 표시 (문장 끊어짐 방지)
            if (interimTranscript && interimTranscript.trim()) {
              // 전체 텍스트 업데이트 (확정 + 중간)
              this.fullCombinedText = this.recognizedText + (this.recognizedText ? ' ' : '') + interimTranscript
              
              // 문장 완성 감지 제거 - Submit 버튼으로만 종료
              
              // 실시간 중간 결과를 부모에게 전달
              this.$emit('realtime-text', {
                interimText: interimTranscript,
                finalText: this.recognizedText,
                combinedText: this.fullCombinedText
              })
            } else {
              // 중간 결과가 없을 때도 현재 상태를 유지
              this.fullCombinedText = this.recognizedText
              this.$emit('realtime-text', {
                interimText: '',
                finalText: this.recognizedText,
                combinedText: this.fullCombinedText
              })
            }
            
            debugLog('🎤 [음성 인식] 중간 결과 저장됨:', {
              interimText: interimTranscript,
              length: interimTranscript.length,
              canSubmitAnswer: this.canSubmitAnswer
            })
          }
          
          // 최종 결과 로깅 및 누적
          if (newFinalTranscript) {
            debugLog('🎤 [음성 인식] 새로운 최종 결과:', {
              text: newFinalTranscript,
              length: newFinalTranscript.length,
              timestamp: new Date().toLocaleTimeString(),
              isListening: this.isListening
            })
            
            // 기존 텍스트에 새로운 텍스트 추가 (강력한 중복 방지)
            if (this.recognizedText) {
              const newText = newFinalTranscript.trim()
              
              // 매우 강력한 중복 제거: 단어 단위로 비교
              const existingWords = this.recognizedText.toLowerCase().split(/\s+/).filter(w => w.length > 2)
              const newWords = newText.toLowerCase().split(/\s+/).filter(w => w.length > 2)
              
              // 새로운 단어가 50% 이상 중복되면 제외 (더 강력한 중복 제거)
              const duplicateCount = newWords.filter(word => existingWords.includes(word)).length
              const duplicateRatio = newWords.length > 0 ? duplicateCount / newWords.length : 0
              
              // 문장 단위 중복 체크는 제거됨 (전체 텍스트 포함 여부 체크로 대체)
              
              // 강력한 중복 방지: 전체 텍스트 포함 여부 체크
              const existingText = this.recognizedText.toLowerCase().trim()
              const newTextLower = newText.toLowerCase().trim()
              
              // 1. 새 텍스트가 기존 텍스트에 완전히 포함되어 있는지 체크
              const isCompletelyContained = existingText.includes(newTextLower) && newTextLower.length > 10
              
              // 2. 기존 텍스트가 새 텍스트에 완전히 포함되어 있는지 체크 (기존 텍스트가 더 짧은 경우)
              const isExistingContained = newTextLower.includes(existingText) && existingText.length > 10
              
              if (isCompletelyContained) {
                debugLog('🎤 [음성 인식] 새 텍스트가 기존 텍스트에 포함됨 - 제외:', {
                  newText: newText,
                  existingLength: existingText.length,
                  newLength: newTextLower.length
                })
              } else if (isExistingContained) {
                // 기존 텍스트가 새 텍스트에 포함되어 있으면 새 텍스트로 교체
                this.recognizedText = newText
                debugLog('🎤 [음성 인식] 기존 텍스트를 새 텍스트로 교체:', {
                  oldLength: existingText.length,
                  newText: newText
                })
              } else if (duplicateRatio < 0.3) { // 30% 미만 중복일 때만 추가
                this.recognizedText = this.connectTexts(this.recognizedText, newText)
                debugLog('🎤 [음성 인식] 새로운 내용 추가됨:', {
                  newText: newText,
                  duplicateRatio: duplicateRatio.toFixed(2),
                  totalLength: this.recognizedText.length
                })
              } else {
                debugLog('🎤 [음성 인식] 중복 내용 제외됨:', {
                  newText: newText,
                  duplicateRatio: duplicateRatio.toFixed(2)
                })
              }
            } else {
              this.recognizedText = newFinalTranscript
              debugLog('🎤 [음성 인식] 첫 텍스트 설정:', {
                text: newFinalTranscript,
                length: newFinalTranscript.length
              })
            }
            
            // 중간 결과 초기화
            this.tempInterimText = ''
            
            // 전체 텍스트 업데이트 (확정된 결과만)
            this.fullCombinedText = this.recognizedText
            
            // 확정된 최종 텍스트만 부모 컴포넌트로 전달
            const finalData = {
              interimText: '',
              finalText: this.recognizedText,
              combinedText: this.fullCombinedText
            }
            console.log('🎤 [REALTIME EMIT] 확정된 결과 전달:', finalData)
            this.$emit('realtime-text', finalData)
            
            debugLog('🎤 [음성 인식] 최종 상태:', {
              recognizedText: this.recognizedText,
              tempInterimText: this.tempInterimText,
              canSubmitAnswer: this.canSubmitAnswer
            })
            debugLog('🎤 [음성 인식] Submit 버튼을 눌러주세요')
          }
        }
        
        this.speechRecognition.onerror = (event) => {
          console.log('🎤 [음성 인식] onerror 이벤트 발생!', event)
          console.log('🎤 [음성 인식] error:', event.error)
          console.log('🎤 [음성 인식] type:', event.type)
          console.log('🎤 [음성 인식] timeStamp:', event.timeStamp)
          console.log('🎤 [음성 인식] 전체 event 객체:', JSON.stringify(event, null, 2))
          
          debugLog('🎤 [음성 인식] onerror 이벤트 발생:', {
            error: event.error,
            type: event.type,
            timeStamp: event.timeStamp,
            isListening: this.isListening,
            isRestarting: this.isRestarting,
            speechRecognition: !!this.speechRecognition,
            lang: this.speechRecognition?.lang,
            continuous: this.speechRecognition?.continuous,
            interimResults: this.speechRecognition?.interimResults
          })
          
          // aborted 오류는 무시 (다른 인스턴스가 시작되면서 발생)
          if (event.error === 'aborted') {
            debugLog('🎤 [오류 무시] aborted 오류 - 다른 인스턴스 시작으로 인한 정상적인 중단')
            return
          }
          
          // 심각한 오류 처리
          if (event.error === 'not-allowed') {
            debugLog('🎤 [오류] 마이크 권한이 거부되었습니다.', null, 'error')
            this.isListening = false
            return
          }
          
          if (event.error === 'no-speech') {
            debugLog('🎤 [오류] 음성이 감지되지 않았습니다.')
            return
          }
          
          if (event.error === 'network') {
            debugLog('🎤 [오류] 네트워크 오류 - Google 음성 인식 서비스 연결 실패', null, 'error')
            
            // 네트워크 오류 시 기존 텍스트 보존
            this.accumulateInterimText()
            
            this.errorMessage = ''
            
            // 네트워크 오류 시 자동 재시작 시도 (3회까지)
            if (this.networkRetryCount < 3) {
              this.networkRetryCount++
              debugLog(`🎤 [네트워크 오류] 자동 재시작 시도 ${this.networkRetryCount}/3`)
              
              setTimeout(() => {
                if (this.isListening) {
                  this.restartListening()
                }
              }, 1500) // 1.5초 후 재시작 (빠른 복구)
            } else {
              debugLog('🎤 [네트워크 오류] 최대 재시도 횟수 초과, 수동 재시작 필요')
              this.errorMessage = ''
              this.isListening = false
            }
            return
          }
          
          if (event.error === 'service-not-allowed') {
            debugLog('🎤 [오류] 서비스 사용 불가 - HTTPS가 아닌 환경', null, 'error')
            this.isListening = false
            return
          }
          
          // 다른 오류는 재시작 시도 (중복 방지 + 지연 시간 증가)
          if (this.isListening && event.error !== 'no-speech' && !this.isRestarting) {
            // 오류 발생 시 기존 텍스트 보존
            this.accumulateInterimText()
            
            this.isRestarting = true
            debugLog('🎤 [오류 재시작] Speech Recognition 오류로 인한 재시작 시도')
            setTimeout(() => {
              if (this.isListening && this.isRestarting) {
                debugLog('🎤 [오류 재시작] Speech Recognition 재시작 실행')
                this.setupSpeechRecognition()
                this.isRestarting = false
              }
            }, 5000) // 3초 → 5초로 증가
          }
        }
        
        this.speechRecognition.onend = () => {
          console.log('🎤 [음성 인식] onend 이벤트 발생!')
          console.log('🎤 [음성 인식] 현재 상태:', {
            isListening: this.isListening,
            isRestarting: this.isRestarting,
            speechRecognition: !!this.speechRecognition
          })
          
          debugLog('🎤 [음성 인식] onend 이벤트 발생')
          debugLog('🎤 [음성 인식] 현재 상태:', {
            isListening: this.isListening,
            isRestarting: this.isRestarting,
            speechRecognition: !!this.speechRecognition,
            lang: this.speechRecognition?.lang,
            recognizedText: this.recognizedText,
            tempInterimText: this.tempInterimText
          })
          
          // onend에서는 재시작하지 않음 (onerror에서 처리)
          // 중복 재시작 방지를 위해 isRestarting 플래그만 초기화
          if (this.isRestarting) {
            debugLog('🎤 [자동 재시작] onend에서 isRestarting 플래그 초기화')
            this.isRestarting = false
          }
        }
        
        debugLog('🎤 [음성 인식] Speech Recognition 시작 전 상태:', {
          speechRecognition: !!this.speechRecognition,
          isListening: this.isListening,
          isRestarting: this.isRestarting,
          continuous: this.speechRecognition.continuous,
          interimResults: this.speechRecognition.interimResults,
          lang: this.speechRecognition.lang
        })
        
        try {
          console.log('🎤 [음성 인식] Speech Recognition 시작 전:', this.speechRecognition)
          console.log('🎤 [음성 인식] Speech Recognition 설정:', {
            lang: this.speechRecognition.lang,
            continuous: this.speechRecognition.continuous,
            interimResults: this.speechRecognition.interimResults,
            maxAlternatives: this.speechRecognition.maxAlternatives
          })
          
          debugLog('🎤 [음성 인식] Speech Recognition 시작')
          this.speechRecognition.start()
          console.log('🎤 [음성 인식] Speech Recognition start() 호출 완료')
          
          // 성공적으로 시작되면 네트워크 재시도 카운터 리셋
          this.networkRetryCount = 0
          
          debugLog('🎤 [음성 인식] Speech Recognition 시작 완료')
        } catch (startError) {
          console.log('🎤 [음성 인식] Speech Recognition 시작 실패:', startError)
          debugLog('🎤 [음성 인식] Speech Recognition 시작 실패:', startError, 'error')
          throw startError
        }
        
        // 이벤트 등록 확인
        debugLog('🎤 [음성 인식] 이벤트 핸들러 등록 상태:', {
          onstart: typeof this.speechRecognition.onstart,
          onresult: typeof this.speechRecognition.onresult,
          onerror: typeof this.speechRecognition.onerror,
          onend: typeof this.speechRecognition.onend
        })
        
      } catch (error) {
        debugLog('🎤 Speech Recognition 설정 실패:', error, 'error')
      }
    },

    // 음성 품질 검증 메서드
    validateVoiceQuality(transcript, confidence) {
      // 기본 신뢰도 검사
      if (confidence < this.voiceQualityThreshold) {
        return false
      }
      
      // 텍스트 길이 검사 (너무 짧거나 긴 경우)
      if (transcript.length < 2 || transcript.length > 200) {
        debugLog('🎤 [품질 검증] 부적절한 텍스트 길이:', {
          length: transcript.length,
          transcript: transcript
        })
        return false
      }
      
      // 특수문자나 숫자만 있는 경우 제외
      if (!/[가-힣a-zA-Z]/.test(transcript)) {
        debugLog('🎤 [품질 검증] 의미있는 텍스트 없음:', {
          transcript: transcript
        })
        return false
      }
      
      return true
    },
    
    // 음성 품질 문제 알림
    notifyVoiceQualityIssue() {
      debugLog('🎤 [품질 알림] 연속된 낮은 품질 감지')
      this.errorMessage = this.$t('voiceExam.qualityIssue', {
        count: this.consecutiveLowQualityCount
      })
      
      // 5초 후 알림 제거
      setTimeout(() => {
        this.errorMessage = ''
      }, 5000)
    },

    async handleVoiceInput(transcript) {
      // 사용자 음성 입력 처리
      debugLog('🎤 [사용자 입력] 음성 인식된 텍스트:', {
        text: transcript,
        length: transcript.length,
        timestamp: new Date().toLocaleTimeString(),
        questionId: this.currentQuestion ? this.currentQuestion.id : 'N/A',
        questionTitle: this.currentQuestion ? (this.currentQuestion.title_ko || this.currentQuestion.title_en) : 'N/A'
      })
      
      // OpenAI를 통한 답변 평가
      try {
        debugLog('🎤 [답변 평가] OpenAI 평가 시작:', {
          userAnswer: transcript,
          correctAnswer: this.getCorrectAnswer(),
          language: this.selectedLanguage
        })
        
        const evaluationResult = await this.evaluateAnswerWithOpenAI(transcript)
        const isCorrect = evaluationResult.isCorrect
        const reason = evaluationResult.reason
        
        debugLog('🎤 [답변 평가] OpenAI 평가 결과:', {
          isCorrect: isCorrect,
          userAnswer: transcript,
          timestamp: new Date().toLocaleTimeString()
        })
        
        // 결과에 따라 Pass/Fail 처리
        if (isCorrect) {
          // 정답인 경우 Pass 처리
          debugLog('🎤 [PASS] 정답 처리 시작')
          this.handlePass()
          const resultMessage = this.$t('takeExam.voiceMode.correct')
          this.speakText(resultMessage)
          
          // 3초 후 자동으로 다음 문제로 넘어가기
          setTimeout(() => {
            if (this.isLastQuestion()) {
              this.speakText(this.$t('takeExam.voiceMode.examCompleted'))
            }
            // currentQuestion 변경 감지로 자동으로 다음 문제 읽기
          }, 3000) // 2초 → 3초로 증가
        } else {
          // 틀린 경우
          const resultMessage = this.$t('takeExam.voiceMode.incorrect')
          
          // Voice Mode에서는 다음 문제로 넘어가지 않음
          if (this.isConnected || this.isVisible) {
            // 오답 이유를 부모 컴포넌트로 전달 (기본 메시지와 상세 내용 분리)
            const incorrectData = {
              message: this.$t('voiceExam.incorrectAnswerMessage'),
              answer: transcript,
              evaluation: reason
            }
            this.$emit('show-incorrect-reason', incorrectData)
            
            // 상세한 평가 내용은 로그에만 기록
            debugLog('🎤 [오답 상세] OpenAI 평가 상세 내용:', reason)
            
            // TTS로만 결과 알림 (다음 문제로 넘어가지 않음)
            this.speakText(resultMessage)
          } else {
            // 일반 모드에서는 기존대로 Fail 처리 (다음 문제로 넘어감)
            this.handleFail()
            this.speakText(resultMessage)
          }
        }
        
      } catch (error) {
        debugLog('🎤 [답변 평가] 평가 실패:', {
          error: error.message,
          userAnswer: transcript,
          timestamp: new Date().toLocaleTimeString()
        }, 'error')
        this.speakText('답변 평가 중 오류가 발생했습니다.')
      }
    },

    async evaluateAnswerWithOpenAI(userAnswer) {
      try {
        if (!this.currentQuestion) {
          debugLog('🎤 [OpenAI 평가] 현재 문제가 없음')
          return false
        }
        
        // 현재 문제의 정답 가져오기
        const correctAnswer = this.getCorrectAnswer()
        if (!correctAnswer) {
          debugLog('🎤 [OpenAI 평가] 정답을 찾을 수 없음')
          return false
        }
        
        const requestData = {
          question: this.currentQuestion.title_ko || this.currentQuestion.title_en,
          user_answer: userAnswer,
          correct_answer: correctAnswer,
          language: this.selectedLanguage,
          exam_difficulty: this.examDifficulty || 5
        }
        
        debugLog('🎤 [OpenAI 평가] API 요청 데이터:', {
          question: requestData.question,
          userAnswer: requestData.user_answer,
          correctAnswer: requestData.correct_answer,
          language: requestData.language,
          timestamp: new Date().toLocaleTimeString()
        })
        
        // OpenAI API를 통한 답변 평가 요청
        const response = await this.$http.post('/api/evaluate-answer/', requestData)
        
        debugLog('🎤 [OpenAI 평가] API 응답:', {
          isCorrect: response.data.is_correct,
          reason: response.data.reason,
          timestamp: new Date().toLocaleTimeString()
        })
        
        return {
          isCorrect: response.data.is_correct,
          reason: response.data.reason
        }
        
      } catch (error) {
        debugLog('🎤 [OpenAI 평가] API 호출 실패:', {
          error: error.message,
          userAnswer: userAnswer,
          timestamp: new Date().toLocaleTimeString()
        }, 'error')
        
        // OpenAI 평가 실패 시 기본 문자열 유사도로 폴백
        debugLog('🎤 [OpenAI 평가] 폴백 평가 시작')
        const fallbackResult = this.fallbackAnswerCheck(userAnswer)
        debugLog('🎤 [OpenAI 평가] 폴백 평가 결과:', fallbackResult)
        return fallbackResult
      }
    },

    getCorrectAnswer() {
      // 현재 문제의 정답과 설명을 모두 반환
      if (this.currentQuestion) {
        // 동적으로 정답과 설명 가져오기
        const answer = getLocalizedContentWithI18n(this.currentQuestion, 'answer', this.$i18n, this.selectedLanguage, '')
        const explanation = getLocalizedContentWithI18n(this.currentQuestion, 'explanation', this.$i18n, this.selectedLanguage, '')
        
        // 정답과 설명을 모두 포함하여 반환
        let finalAnswer = ''
        if (answer && explanation) {
          finalAnswer = `${answer}. ${explanation}`
        } else if (answer) {
          finalAnswer = answer
        } else if (explanation) {
          finalAnswer = explanation
        } else {
          // 정답과 설명이 모두 없으면 문제 내용을 정답으로 사용
          finalAnswer = getLocalizedContentWithI18n(this.currentQuestion, 'content', this.$i18n, this.selectedLanguage, '')
        }
        
        debugLog('🎤 [정답 구성] 정답과 설명 조합:', {
          answer: answer,
          explanation: explanation,
          finalAnswer: finalAnswer,
          language: this.selectedLanguage
        })
        
        return finalAnswer
      }
      return null
    },

    fallbackAnswerCheck(userAnswer) {
      // OpenAI 평가 실패 시 기본 유사도 체크
      const correctAnswer = this.getCorrectAnswer()
      if (!correctAnswer) {
        debugLog('🎤 [폴백 평가] 정답을 찾을 수 없음')
        return false
      }
      
      // 간단한 키워드 매칭
      const userKeywords = userAnswer.toLowerCase().split(' ')
      const correctKeywords = correctAnswer.toLowerCase().split(' ')
      
      const matchingKeywords = userKeywords.filter(keyword => 
        correctKeywords.some(correctKeyword => 
          correctKeyword.includes(keyword) || keyword.includes(correctKeyword)
        )
      )
      
      const matchRatio = matchingKeywords.length / userKeywords.length
      const isCorrect = matchRatio >= 0.5
      
      debugLog('🎤 [폴백 평가] 키워드 매칭 결과:', {
        userAnswer: userAnswer,
        correctAnswer: correctAnswer,
        userKeywords: userKeywords,
        correctKeywords: correctKeywords,
        matchingKeywords: matchingKeywords,
        matchRatio: matchRatio,
        isCorrect: isCorrect,
        timestamp: new Date().toLocaleTimeString()
      })
      
      // 50% 이상 키워드가 매칭되면 정답으로 간주
      return isCorrect
    },

    speakText(text) {
      debugLog('🎤 [TTS] speakText 호출:', {
        text: text,
        textLength: text ? text.length : 0,
        selectedLanguage: this.selectedLanguage,
        utteranceLang: this.selectedLanguage === 'ko' ? 'ko-KR' : 'en-US',
        selectedVoice: this.selectedVoice
      })
      
      if ('speechSynthesis' in window) {
        // 기존 음성 재생 중지
        speechSynthesis.cancel()
        
        const utterance = new SpeechSynthesisUtterance(text)
        utterance.lang = this.selectedLanguage === 'ko' ? 'ko-KR' : 'en-US'
        utterance.rate = 0.8
        utterance.pitch = 1.0
        utterance.volume = 0.8
        
        // 음성 선택 로직 개선
        const voices = speechSynthesis.getVoices()
        debugLog('🎤 [TTS] 사용 가능한 음성 목록:', voices.map(v => ({name: v.name, lang: v.lang})))
        
        if (this.selectedLanguage === 'en') {
          // 영어 음성 우선 선택
          const englishVoice = voices.find(voice => voice.lang === 'en-US' && voice.name.includes('Samantha')) ||
                              voices.find(voice => voice.lang === 'en-US' && voice.name.includes('Alex')) ||
                              voices.find(voice => voice.lang === 'en-US') ||
                              voices.find(voice => voice.lang === 'en-GB') ||
                              voices.find(voice => voice.lang.startsWith('en-')) ||
                              voices.find(voice => voice.lang === 'en')
          
          if (englishVoice) {
            utterance.voice = englishVoice
            debugLog('🎤 [TTS] speakText 영어 음성 선택:', {
              name: englishVoice.name,
              lang: englishVoice.lang,
              voiceURI: englishVoice.voiceURI
            })
          } else {
            debugLog('🎤 [TTS] 영어 음성을 찾을 수 없음, 기본 음성 사용')
          }
        } else if (this.selectedLanguage === 'ko') {
          // 한국어 음성 선택
          const koreanVoice = voices.find(voice => voice.lang === 'ko-KR') ||
                             voices.find(voice => voice.lang.startsWith('ko-')) ||
                             voices.find(voice => voice.lang === 'ko')
          
          if (koreanVoice) {
            utterance.voice = koreanVoice
            debugLog('🎤 [TTS] speakText 한국어 음성 선택:', {
              name: koreanVoice.name,
              lang: koreanVoice.lang
            })
          }
        }
        
        // 음성 재생 이벤트 처리
        utterance.onstart = () => {
          debugLog('🎤 [TTS] 음성 재생 시작:', {
            text: text,
            voice: utterance.voice ? utterance.voice.name : 'default',
            lang: utterance.lang
          })
        }
        
        utterance.onend = () => {
          debugLog('🎤 [TTS] 음성 재생 완료:', {
            text: text,
            voice: utterance.voice ? utterance.voice.name : 'default'
          })
        }
        
        utterance.onerror = (event) => {
          debugLog('🎤 [TTS] 음성 재생 오류:', {
            error: event.error,
            text: text,
            voice: utterance.voice ? utterance.voice.name : 'default'
          }, 'error')
        }
        
        speechSynthesis.speak(utterance)
      } else {
        debugLog('🎤 [TTS] Web Speech API를 지원하지 않는 브라우저입니다.', null, 'error')
      }
    },

    speakTextWithCallback(text, callback) {
      debugLog('🎤 [TTS] speakTextWithCallback 호출:', {
        text: text,
        textLength: text ? text.length : 0,
        selectedLanguage: this.selectedLanguage
      })
      
      if ('speechSynthesis' in window) {
        // 기존 음성 재생 중지 (더 안전하게)
        if (speechSynthesis.speaking) {
          speechSynthesis.cancel()
          // 취소 후 잠시 대기
          setTimeout(() => {
            this.startSpeakTextWithCallback(text, callback)
          }, 100)
        } else {
          this.startSpeakTextWithCallback(text, callback)
        }
      } else {
        debugLog('🎤 [TTS] Web Speech API를 지원하지 않는 브라우저입니다.', null, 'error')
        // Web Speech API를 지원하지 않아도 콜백 실행
        if (callback) {
          callback()
        }
      }
    },

    startSpeakTextWithCallback(text, callback) {
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = this.selectedLanguage === 'ko' ? 'ko-KR' : 'en-US'
      utterance.rate = 0.8
      utterance.pitch = 1.0
      utterance.volume = 0.8
        
      // 음성 선택 로직 (speakText와 동일)
      const voices = speechSynthesis.getVoices()
      
      if (this.selectedLanguage === 'en') {
        const englishVoice = voices.find(voice => voice.lang === 'en-US' && voice.name.includes('Samantha')) ||
                            voices.find(voice => voice.lang === 'en-US' && voice.name.includes('Alex')) ||
                            voices.find(voice => voice.lang === 'en-US') ||
                            voices.find(voice => voice.lang === 'en-GB') ||
                            voices.find(voice => voice.lang.startsWith('en-')) ||
                            voices.find(voice => voice.lang === 'en')
        
        if (englishVoice) {
          utterance.voice = englishVoice
        }
      } else if (this.selectedLanguage === 'ko') {
        const koreanVoice = voices.find(voice => voice.lang === 'ko-KR') ||
                           voices.find(voice => voice.lang.startsWith('ko-')) ||
                           voices.find(voice => voice.lang === 'ko')
        
        if (koreanVoice) {
          utterance.voice = koreanVoice
        }
      }
      
      // 음성 재생 완료 시 콜백 실행
      utterance.onend = () => {
        debugLog('🎤 [TTS] speakTextWithCallback 완료, 콜백 실행')
        if (callback) {
          callback()
        }
      }
      
      utterance.onerror = (event) => {
        debugLog('🎤 [TTS] speakTextWithCallback 오류:', event.error, 'error')
        // 오류가 발생해도 콜백 실행
        if (callback) {
          callback()
        }
      }
      
      speechSynthesis.speak(utterance)
    },

    async requestOpenAISpeech() {
      try {
        if (!this.realtimeSession) {
          throw new Error('Realtime 세션이 없습니다.')
        }
        
        // 현재 문제 정보를 OpenAI에 전송하여 음성으로 읽어달라고 요청
        const questionText = this.getQuestionText(this.currentQuestion)
        const examTitleText = this.examTitle || ''
        
        const speechRequest = {
          text: `${examTitleText}. ${questionText}`,
          voice: this.selectedVoice,
          language: this.selectedLanguage
        }
        
        debugLog('🎤 OpenAI 음성 출력 요청:', speechRequest)
        
        await this.$http.post(`/api/realtime/session/${this.realtimeSession.session_id}/speak/`, speechRequest)
        
        debugLog('🎤 OpenAI 음성 출력 요청 완료')
        
      } catch (error) {
        debugLog('🎤 OpenAI 음성 출력 요청 실패:', error, 'error')
        throw error
      }
    },

    async stopOpenAISpeech() {
      try {
        if (!this.realtimeSession) {
          return
        }
        
        await this.$http.post(`/api/realtime/session/${this.realtimeSession.session_id}/stop-speak/`)
        debugLog('🎤 OpenAI 음성 출력 중지 요청 완료')
        
      } catch (error) {
        debugLog('🎤 OpenAI 음성 출력 중지 요청 실패:', error, 'error')
      }
    },

    async speakExamTitle() {
      try {
        if (!this.examTitle) return
        
        debugLog('🎤 시험 제목 읽기 시작:', this.examTitle)
        
        // 브라우저의 Web Speech API 사용
        if ('speechSynthesis' in window) {
          const utterance = new SpeechSynthesisUtterance(this.examTitle)
          
          // 언어 설정
          utterance.lang = this.selectedLanguage === 'ko' ? 'ko-KR' : 'en-US'
          
          // 음성 설정
          utterance.rate = 0.9
          utterance.pitch = 1.0
          utterance.volume = 0.8
          
          // 선택된 음성 사용
          if (this.selectedVoice) {
            const selectedVoiceObj = this.availableVoices.find(voice => voice.name === this.selectedVoice)
            if (selectedVoiceObj) {
              utterance.voice = selectedVoiceObj
            }
          }
          
          // 음성 재생
          speechSynthesis.speak(utterance)
          
          debugLog('🎤 시험 제목 읽기 완료')
        } else {
          debugLog('🎤 Web Speech API를 지원하지 않는 브라우저입니다.')
        }
        
      } catch (error) {
        debugLog('🎤 시험 제목 읽기 실패:', error, 'error')
      }
    },

    async speakQuestion(question) {
      try {
        debugLog('🎤 [TTS] speakQuestion 호출됨')
        debugLog('🎤 [TTS] 문제 데이터:', {
          question: question,
          questionId: question ? question.id : 'N/A',
          title_ko: question ? question.title_ko : 'N/A',
          title_en: question ? question.title_en : 'N/A',
          content_ko: question ? question.content_ko : 'N/A',
          content_en: question ? question.content_en : 'N/A'
        })
        
        // 문제 내용을 음성으로 변환하여 읽어주기
        let textToSpeak = this.getQuestionText(question)
        
        debugLog('🎤 [TTS] getQuestionText 결과:', {
          textToSpeak: textToSpeak,
          textLength: textToSpeak ? textToSpeak.length : 0
        })
        
        // 텍스트 전처리 - 특수 문자 제거 및 정규화 (한글 포함)
        if (textToSpeak) {
          textToSpeak = textToSpeak
            .replace(/[^\w\s.,!?가-힣]/g, ' ') // 특수 문자 제거 (한글 포함)
            .replace(/\s+/g, ' ') // 여러 공백을 하나로
            .trim()
        }
        
        debugLog('🎤 [TTS] 문제 읽기 시작:', {
          originalText: this.getQuestionText(question),
          processedText: textToSpeak,
          textLength: textToSpeak ? textToSpeak.length : 0,
          selectedLanguage: this.selectedLanguage,
          utteranceLang: this.selectedLanguage === 'ko' ? 'ko-KR' : 'en-US'
        })
        
        // 브라우저의 Web Speech API 사용
        if ('speechSynthesis' in window) {
          // 기존 음성 재생 중지
          speechSynthesis.cancel()
          
          const utterance = new SpeechSynthesisUtterance(textToSpeak)
          
          // 언어 설정 - 더 명확하게 설정
          utterance.lang = this.selectedLanguage === 'ko' ? 'ko-KR' : 'en-US'
          
          // 음성 설정
          utterance.rate = 0.8  // 조금 더 느리게
          utterance.pitch = 1.0
          utterance.volume = 0.8
          
          // 디버깅을 위한 추가 설정
          debugLog('🎤 [TTS] utterance 설정:', {
            text: utterance.text,
            lang: utterance.lang,
            rate: utterance.rate,
            pitch: utterance.pitch,
            volume: utterance.volume,
            availableVoices: speechSynthesis.getVoices().length
          })
          
          // 언어에 따른 음성 선택
          const voices = speechSynthesis.getVoices()
          let selectedVoice = null
          
          if (this.selectedLanguage === 'ko') {
            // 한국어 음성 찾기 (우선순위: ko-KR > ko)
            selectedVoice = voices.find(voice => voice.lang === 'ko-KR') ||
                           voices.find(voice => voice.lang.startsWith('ko-')) ||
                           voices.find(voice => voice.lang === 'ko')
            
            if (selectedVoice) {
              utterance.voice = selectedVoice
              debugLog('🎤 [TTS] 한국어 음성 선택:', {
                name: selectedVoice.name,
                lang: selectedVoice.lang,
                voiceURI: selectedVoice.voiceURI
              })
            } else {
              debugLog('🎤 [TTS] 한국어 음성을 찾을 수 없음, 사용 가능한 음성:', voices.map(v => ({name: v.name, lang: v.lang})))
            }
          } else {
            // 영어 음성 찾기 (우선순위: en-US > en-GB > en)
            selectedVoice = voices.find(voice => voice.lang === 'en-US') ||
                           voices.find(voice => voice.lang === 'en-GB') ||
                           voices.find(voice => voice.lang.startsWith('en-')) ||
                           voices.find(voice => voice.lang === 'en')
            
            if (selectedVoice) {
              utterance.voice = selectedVoice
              debugLog('🎤 [TTS] 영어 음성 선택:', {
                name: selectedVoice.name,
                lang: selectedVoice.lang,
                voiceURI: selectedVoice.voiceURI
              })
            } else {
              debugLog('🎤 [TTS] 영어 음성을 찾을 수 없음, 사용 가능한 음성:', voices.map(v => ({name: v.name, lang: v.lang})))
            }
          }
          
          // 음성 재생 완료 이벤트 처리
          utterance.onend = () => {
            debugLog('🎤 [TTS] 문제 읽기 완료:', {
              text: textToSpeak,
              language: this.selectedLanguage,
              utteranceLang: utterance.lang,
              voice: utterance.voice ? utterance.voice.name : 'default'
            })
            // 문제 읽기 완료 후 자동으로 음성 입력 시작
            setTimeout(() => {
              this.startListening()
            }, 1500) // 1.5초 후 자동 시작
          }
          
          // 음성 재생 오류 이벤트 처리
          utterance.onerror = (event) => {
            debugLog('🎤 [TTS] 음성 재생 오류:', {
              error: event.error,
              text: textToSpeak,
              language: this.selectedLanguage,
              utteranceLang: utterance.lang,
              voice: utterance.voice ? utterance.voice.name : 'default'
            })
          }
          
          // 음성 재생
          speechSynthesis.speak(utterance)
          
        } else {
          debugLog('🎤 Web Speech API를 지원하지 않는 브라우저입니다.')
        }
        
      } catch (error) {
        debugLog('문제 읽기 실패:', error, 'error')
        throw error
      }
    },

    getQuestionText(question) {
      // 동적으로 제목과 내용 가져오기
      const title = getLocalizedContentWithI18n(question, 'title', this.$i18n, this.selectedLanguage, '')
      const content = getLocalizedContentWithI18n(question, 'content', this.$i18n, this.selectedLanguage, '')
      
      debugLog('🎤 [문제 텍스트] 언어 설정:', {
        selectedLanguage: this.selectedLanguage,
        language: this.selectedLanguage,
        title_ko: question.title_ko,
        title_en: question.title_en,
        content_ko: question.content_ko,
        content_en: question.content_en,
        selectedTitle: title,
        selectedContent: content,
        titleLength: title ? title.length : 0,
        contentLength: content ? content.length : 0,
        areEqual: content && title ? content.trim() === title.trim() : false,
        contentTrimmed: content ? content.trim() : '',
        titleTrimmed: title ? title.trim() : ''
      })
      
      // 내용이 있고 제목과 다를 때만 제목 + 내용 반환
      if (content && content.trim() && content.trim() !== title.trim()) {
        return `${title}. ${content}`
      } else {
        // 내용이 없거나 제목과 동일하면 제목만 반환
        return title
      }
    },

    updateVoiceSettings() {
      if (this.realtimeSession) {
        // 음성 설정 업데이트
        debugLog('음성 설정 업데이트:', {
          voice: this.selectedVoice,
          language: this.selectedLanguage
        })
      }
    },

    toggleVoiceMode() {
      this.$emit('toggle-voice-mode')
    },

    cleanup() {
      // 리소스 정리
      if (this.mediaStream) {
        this.mediaStream.getTracks().forEach(track => track.stop())
        this.mediaStream = null
      }
      
      if (this.speechRecognition) {
        this.speechRecognition.stop()
        this.speechRecognition = null
      }
      
      if (this.connectionTimeout) {
        clearTimeout(this.connectionTimeout)
        this.connectionTimeout = null
      }
      
      if (this.listeningTimeout) {
        clearTimeout(this.listeningTimeout)
        this.listeningTimeout = null
      }
      
      // 중간 결과 누적 타이머 제거됨 (문장 끊어짐 방지)
      
      // 음성 재생 중지
      if ('speechSynthesis' in window) {
        speechSynthesis.cancel()
      }
      
      this.isConnected = false
      this.isListening = false
      this.isSpeaking = false
      
      debugLog('🎤 음성 인터페이스 정리 완료')
    },

    async cleanupRealtimeSession() {
      try {
        if (this.realtimeSession && this.realtimeSession.session_id) {
          await this.$http.delete(`/api/realtime/session/${this.realtimeSession.session_id}/delete/`)
          debugLog('🎤 Realtime 세션 정리 완료')
        }
      } catch (error) {
        debugLog('🎤 Realtime 세션 정리 실패:', error, 'error')
      }
    }
  }
}
</script>

<style scoped>
.voice-exam-interface {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 15px;
  padding: 5px 20px;
  margin: 0;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  color: white;
}

.incorrect-reason {
  margin-top: 10px;
}

.incorrect-reason .alert {
  border-radius: 8px;
  font-size: 14px;
  padding: 10px 15px;
}

.voice-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.voice-title {
  font-size: 1.2rem;
  font-weight: 600;
  display: flex;
  align-items: center;
}

.voice-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.voice-actions .btn {
  color: white !important;
}

.connection-status {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 15px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  margin-bottom: 20px;
}

/* voice-controls는 헤더로 이동됨 */

.voice-control-btn {
  width: auto;
  margin-left: 16px;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: 600;
  transition: all 0.3s ease;
  font-size: 0.9rem;
  border-color: white !important;
  color: white !important;
}

.voice-control-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
}

/* 불필요한 스타일들 제거됨 */

.alert {
  margin-top: 15px;
  border-radius: 10px;
}

/* 불필요한 애니메이션 제거됨 */

@media (max-width: 768px) {
  .voice-header {
    flex-direction: column;
    gap: 10px;
  }
  
  .voice-actions {
    width: 100%;
    justify-content: center;
  }
}
</style>
