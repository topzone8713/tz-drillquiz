/**
 * 고급 음성인식 유틸리티
 * Web Speech API의 한계를 극복하기 위한 대안 구현
 */

import { debugLog } from './debugUtils'

export class AdvancedSpeechRecognition {
  constructor(options = {}) {
    this.options = {
      primaryEngine: 'web-speech', // 'web-speech', 'google-cloud', 'azure', 'aws'
      fallbackEngines: ['google-cloud', 'azure'],
      confidenceThreshold: 0.7,
      maxRetries: 3,
      retryDelay: 1000,
      ...options
    }
    
    this.currentEngine = this.options.primaryEngine
    this.retryCount = 0
    this.isListening = false
    this.recognitionInstance = null
  }

  /**
   * 음성인식 시작
   */
  async startListening() {
    try {
      debugLog('🎤 [고급 음성인식] 음성인식 시작:', {
        engine: this.currentEngine,
        options: this.options
      })

      this.isListening = true
      this.retryCount = 0

      switch (this.currentEngine) {
        case 'web-speech':
          return await this.startWebSpeechRecognition()
        case 'google-cloud':
          return await this.startGoogleCloudRecognition()
        case 'azure':
          return await this.startAzureRecognition()
        case 'aws':
          return await this.startAWSRecognition()
        default:
          throw new Error(`지원하지 않는 음성인식 엔진: ${this.currentEngine}`)
      }
    } catch (error) {
      debugLog('🎤 [고급 음성인식] 음성인식 시작 실패:', error, 'error')
      return await this.handleRecognitionError(error)
    }
  }

  /**
   * Web Speech API 사용
   */
  async startWebSpeechRecognition() {
    return new Promise((resolve, reject) => {
      if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        reject(new Error('Web Speech API를 지원하지 않는 브라우저입니다.'))
        return
      }

      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
      this.recognitionInstance = new SpeechRecognition()
      
      // 최적화된 설정
      this.recognitionInstance.continuous = true
      this.recognitionInstance.interimResults = true
      this.recognitionInstance.maxAlternatives = 5 // 더 많은 대안 수집
      this.recognitionInstance.lang = this.options.language || 'ko-KR'

      this.recognitionInstance.onstart = () => {
        debugLog('🎤 [Web Speech] 음성인식 시작됨')
        resolve()
      }

      this.recognitionInstance.onresult = (event) => {
        this.handleRecognitionResult(event)
      }

      this.recognitionInstance.onerror = (error) => {
        debugLog('🎤 [Web Speech] 오류 발생:', error, 'error')
        this.handleRecognitionError(error)
      }

      this.recognitionInstance.onend = () => {
        debugLog('🎤 [Web Speech] 음성인식 종료됨')
        if (this.isListening) {
          // 자동 재시작
          setTimeout(() => this.startListening(), 1000)
        }
      }

      this.recognitionInstance.start()
    })
  }

  /**
   * Google Cloud Speech-to-Text API 사용
   */
  async startGoogleCloudRecognition() {
    // Google Cloud Speech-to-Text API 구현
    // 실제 구현 시 API 키와 설정이 필요합니다
    debugLog('🎤 [Google Cloud] 음성인식 시작 (구현 예정)')
    throw new Error('Google Cloud Speech-to-Text는 아직 구현되지 않았습니다.')
  }

  /**
   * Azure Speech Services 사용
   */
  async startAzureRecognition() {
    // Azure Speech Services 구현
    debugLog('🎤 [Azure] 음성인식 시작 (구현 예정)')
    throw new Error('Azure Speech Services는 아직 구현되지 않았습니다.')
  }

  /**
   * AWS Transcribe 사용
   */
  async startAWSRecognition() {
    // AWS Transcribe 구현
    debugLog('🎤 [AWS] 음성인식 시작 (구현 예정)')
    throw new Error('AWS Transcribe는 아직 구현되지 않았습니다.')
  }

  /**
   * 음성인식 결과 처리
   */
  handleRecognitionResult(event) {
    let finalTranscript = ''
    let interimTranscript = ''
    let bestConfidence = 0

    for (let i = event.resultIndex; i < event.results.length; i++) {
      const result = event.results[i]
      const isFinal = result.isFinal

      // 가장 높은 신뢰도의 대안 선택
      let bestAlternative = result[0]
      for (let j = 0; j < result.length; j++) {
        if (result[j].confidence > bestAlternative.confidence) {
          bestAlternative = result[j]
        }
      }

      const transcript = bestAlternative.transcript
      const confidence = bestAlternative.confidence

      if (isFinal) {
        if (confidence >= this.options.confidenceThreshold) {
          finalTranscript += transcript
          if (confidence > bestConfidence) {
            bestConfidence = confidence
          }
        } else {
          debugLog('🎤 [고급 음성인식] 낮은 신뢰도로 인한 결과 제외:', {
            transcript,
            confidence,
            threshold: this.options.confidenceThreshold
          })
        }
      } else {
        interimTranscript += transcript
      }
    }

    // 결과 이벤트 발생
    if (finalTranscript) {
      this.emit('result', {
        transcript: finalTranscript,
        confidence: bestConfidence,
        isFinal: true,
        engine: this.currentEngine
      })
    }

    if (interimTranscript) {
      this.emit('interim', {
        transcript: interimTranscript,
        isFinal: false,
        engine: this.currentEngine
      })
    }
  }

  /**
   * 음성인식 오류 처리 및 폴백
   */
  async handleRecognitionError(error) {
    debugLog('🎤 [고급 음성인식] 오류 처리:', {
      error: error.message,
      currentEngine: this.currentEngine,
      retryCount: this.retryCount
    })

    if (this.retryCount < this.options.maxRetries) {
      this.retryCount++
      
      // 폴백 엔진으로 전환
      const fallbackIndex = (this.retryCount - 1) % this.options.fallbackEngines.length
      this.currentEngine = this.options.fallbackEngines[fallbackIndex]
      
      debugLog('🎤 [고급 음성인식] 폴백 엔진으로 전환:', {
        newEngine: this.currentEngine,
        retryCount: this.retryCount
      })

      // 지연 후 재시도
      setTimeout(() => {
        this.startListening()
      }, this.options.retryDelay * this.retryCount)
    } else {
      this.emit('error', {
        message: '모든 음성인식 엔진에서 오류가 발생했습니다.',
        originalError: error,
        engines: [this.options.primaryEngine, ...this.options.fallbackEngines]
      })
    }
  }

  /**
   * 음성인식 중지
   */
  stopListening() {
    debugLog('🎤 [고급 음성인식] 음성인식 중지')
    this.isListening = false

    if (this.recognitionInstance) {
      if (this.currentEngine === 'web-speech') {
        this.recognitionInstance.stop()
      }
      this.recognitionInstance = null
    }
  }

  /**
   * 이벤트 발생
   */
  emit(event, data) {
    if (this.options.onResult && event === 'result') {
      this.options.onResult(data)
    }
    if (this.options.onInterim && event === 'interim') {
      this.options.onInterim(data)
    }
    if (this.options.onError && event === 'error') {
      this.options.onError(data)
    }
  }

  /**
   * 엔진 전환
   */
  switchEngine(engine) {
    if (this.isListening) {
      this.stopListening()
    }
    
    this.currentEngine = engine
    this.retryCount = 0
    
    debugLog('🎤 [고급 음성인식] 엔진 전환:', {
      newEngine: engine
    })
  }

  /**
   * 설정 업데이트
   */
  updateOptions(newOptions) {
    this.options = { ...this.options, ...newOptions }
    debugLog('🎤 [고급 음성인식] 설정 업데이트:', this.options)
  }
}

/**
 * 음성인식 품질 향상을 위한 전처리 유틸리티
 */
export class VoicePreprocessor {
  constructor() {
    this.audioContext = null
    this.analyser = null
    this.microphone = null
  }

  /**
   * 오디오 컨텍스트 초기화
   */
  async initializeAudioContext() {
    try {
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)()
      this.analyser = this.audioContext.createAnalyser()
      this.analyser.fftSize = 256
      
      debugLog('🎤 [전처리] 오디오 컨텍스트 초기화 완료')
      return true
    } catch (error) {
      debugLog('🎤 [전처리] 오디오 컨텍스트 초기화 실패:', error, 'error')
      return false
    }
  }

  /**
   * 마이크 스트림 설정
   */
  async setupMicrophone() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 44100
        } 
      })
      
      this.microphone = this.audioContext.createMediaStreamSource(stream)
      this.microphone.connect(this.analyser)
      
      debugLog('🎤 [전처리] 마이크 설정 완료')
      return stream
    } catch (error) {
      debugLog('🎤 [전처리] 마이크 설정 실패:', error, 'error')
      throw error
    }
  }

  /**
   * 음성 품질 분석
   */
  analyzeVoiceQuality() {
    if (!this.analyser) return null

    const bufferLength = this.analyser.frequencyBinCount
    const dataArray = new Uint8Array(bufferLength)
    this.analyser.getByteFrequencyData(dataArray)

    // 평균 볼륨 계산
    const average = dataArray.reduce((a, b) => a + b) / bufferLength
    
    // 신호 대 잡음비 추정
    const signal = Math.max(...dataArray)
    const noise = dataArray.reduce((a, b) => a + b) / bufferLength
    const snr = signal / (noise + 1) // 1을 더해서 0으로 나누는 것을 방지

    return {
      volume: average,
      signalToNoiseRatio: snr,
      quality: this.calculateQualityScore(average, snr)
    }
  }

  /**
   * 품질 점수 계산
   */
  calculateQualityScore(volume, snr) {
    // 볼륨이 너무 낮거나 높으면 품질 감점
    const volumeScore = volume > 10 && volume < 200 ? 1 : 0.5
    
    // 신호 대 잡음비가 높을수록 좋은 품질
    const snrScore = Math.min(snr / 10, 1)
    
    return (volumeScore + snrScore) / 2
  }

  /**
   * 정리
   */
  cleanup() {
    if (this.microphone) {
      this.microphone.disconnect()
      this.microphone = null
    }
    if (this.audioContext) {
      this.audioContext.close()
      this.audioContext = null
    }
  }
}

export default AdvancedSpeechRecognition
