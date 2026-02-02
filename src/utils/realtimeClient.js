/**
 * OpenAI Realtime API WebSocket 클라이언트
 */

import { debugLog } from './debugUtils'

export class RealtimeClient {
  constructor(websocketUrl, clientSecret) {
    this.websocketUrl = websocketUrl
    this.clientSecret = clientSecret
    this.ws = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 3
    this.reconnectDelay = 1000 // 1초
    this.isConnected = false
    this.eventHandlers = {}
    this.audioBuffer = null
  }
  
  /**
   * WebSocket 연결
   * @returns {Promise<void>}
   */
  async connect() {
    return new Promise((resolve, reject) => {
      try {
        // WebSocket URL 검증
        if (!this.websocketUrl) {
          const error = new Error('WebSocket URL이 없습니다.')
          debugLog('❌ WebSocket URL 없음')
          reject(error)
          return
        }
        
        // URL 형식 검증
        if (!this.websocketUrl.startsWith('wss://') && !this.websocketUrl.startsWith('ws://')) {
          const error = new Error(`잘못된 WebSocket URL 형식: ${this.websocketUrl}`)
          debugLog('❌ WebSocket URL 형식 오류:', this.websocketUrl)
          reject(error)
          return
        }
        
        // client_secret 검증 및 로깅
        const clientSecretInfo = this.clientSecret ? {
          exists: true,
          length: this.clientSecret.length,
          prefix: this.clientSecret.substring(0, 10) + '...',
          suffix: '...' + this.clientSecret.substring(this.clientSecret.length - 10),
          startsWithEk: this.clientSecret.startsWith('ek_')
        } : { exists: false }
        
        // URL에서 client_secret 파라미터 확인
        let urlHasClientSecret = false
        let urlClientSecretPrefix = null
        let urlSessionId = null
        try {
          const url = new URL(this.websocketUrl)
          urlSessionId = url.searchParams.get('session_id')
          const clientSecretParam = url.searchParams.get('client_secret')
          urlHasClientSecret = !!clientSecretParam
          if (clientSecretParam) {
            urlClientSecretPrefix = clientSecretParam.substring(0, 10) + '...'
          }
        } catch (e) {
          debugLog('⚠️ URL 파싱 실패:', e)
        }
        
        debugLog('🔌 WebSocket 연결 시작:', {
          url: this.websocketUrl,
          urlLength: this.websocketUrl.length,
          urlSessionId: urlSessionId,
          clientSecret: clientSecretInfo,
          urlHasClientSecret: urlHasClientSecret,
          urlClientSecretPrefix: urlClientSecretPrefix,
          clientSecretMatches: this.clientSecret && urlClientSecretPrefix ? 
            this.clientSecret.startsWith(urlClientSecretPrefix.substring(0, 10)) : false
        })
        
        // 브라우저 WebSocket API는 headers를 지원하지 않음
        // client_secret은 URL 쿼리 파라미터로만 전달됨 (Bearer 인증 사용 안 함)
        // WebSocket 연결 - 쿼리 파라미터만 사용, 헤더 인증 없음
        // 주의: axios interceptor는 WebSocket 연결에 영향을 주지 않음 (axios는 HTTP 요청만 처리)
        this.ws = new WebSocket(this.websocketUrl)
        
        this.ws.onopen = () => {
          debugLog('✅ WebSocket 연결 성공')
          this.isConnected = true
          this.reconnectAttempts = 0
          
          // OpenAI Realtime API는 세션 생성 시 이미 모든 설정이 완료됨
          // session.update 메시지는 선택사항이며, 세션 생성 시 설정된 값만 업데이트 가능
          // modalities는 세션 생성 시에만 설정 가능하고, session.update에서는 업데이트 불가
          // 따라서 session.update 메시지를 보내지 않거나, 최소한의 필드만 업데이트
          // 현재는 세션이 이미 생성되어 있으므로 session.update 메시지 없이 진행
          debugLog('✅ WebSocket 연결 완료, 세션은 이미 활성화됨')
          
          this.emit('connected')
          resolve()
        }
        
        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            this.handleMessage(data)
          } catch (error) {
            debugLog('❌ 메시지 파싱 오류:', error)
          }
        }
        
        this.ws.onerror = (error) => {
          // WebSocket 에러는 일반적으로 이벤트 객체만 제공됨
          const errorInfo = {
            type: error.type || 'unknown',
            target: error.target ? {
              url: error.target.url,
              readyState: error.target.readyState,
              protocol: error.target.protocol
            } : null,
            message: error.message || 'WebSocket 연결 오류'
          }
          debugLog('❌ WebSocket 오류:', errorInfo)
          console.error('WebSocket 에러 상세:', error)
          this.emit('error', error)
          reject(new Error(`WebSocket 연결 오류: ${errorInfo.message}`))
        }
        
        this.ws.onclose = (event) => {
          const closeInfo = {
            code: event.code,
            reason: event.reason || 'Unknown',
            wasClean: event.wasClean,
            url: this.websocketUrl
          }
          debugLog('🔌 WebSocket 연결 종료:', closeInfo)
          this.isConnected = false
          this.emit('disconnected', event)
          
          // 정상 종료가 아닌 경우 에러로 처리
          if (event.code !== 1000) {
            const error = new Error(`WebSocket 연결 종료: ${event.code} - ${event.reason || 'Unknown'}`)
            debugLog('❌ WebSocket 비정상 종료:', closeInfo)
            reject(error)
          }
          
          // 정상 종료가 아닌 경우 재연결 시도
          if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnect()
          }
        }
        
      } catch (error) {
        debugLog('❌ WebSocket 연결 실패 (catch):', {
          message: error.message,
          stack: error.stack,
          url: this.websocketUrl
        })
        console.error('WebSocket 연결 실패 상세:', error)
        reject(error)
      }
    })
  }
  
  /**
   * 재연결 시도
   */
  reconnect() {
    this.reconnectAttempts++
    debugLog(`🔄 재연결 시도 ${this.reconnectAttempts}/${this.maxReconnectAttempts}`)
    
    setTimeout(() => {
      this.connect().catch(error => {
        debugLog('❌ 재연결 실패:', error)
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
          this.emit('reconnect_failed')
        }
      })
    }, this.reconnectDelay * this.reconnectAttempts)
  }
  
  /**
   * 알려진 메시지 타입인지 확인
   * @param {string} type - 메시지 타입
   * @returns {boolean}
   */
  isKnownMessageType(type) {
    const knownTypes = [
      'session.created',
      'session.updated',
      'conversation.item.created',
      'conversation.item.added',
      'conversation.item.done',
      'conversation.item.input_audio_transcription.completed',
      'conversation.item.input_audio_transcription.failed',
      'input_audio_buffer.committed',
      'input_audio_buffer.speech_started',
      'input_audio_buffer.speech_stopped',
      'response.audio_transcript.delta',
      'response.audio_transcript.done',
      'response.audio.delta',
      'response.audio.done',
      'response.output_audio.delta',  // 실제 오디오 데이터 메시지 타입
      'response.output_audio.done',
      'response.output_audio_transcript.delta',  // AI 응답 텍스트 전사
      'response.output_audio_transcript.done',
      'response.output_item.added',
      'response.output_item.done',
      'response.content_part.added',
      'response.content_part.done',
      'response.done',
      'response.created',
      'rate_limits.updated',
      'error'
    ]
    return knownTypes.includes(type)
  }
  
  /**
   * 메시지 처리
   * @param {Object} data - 수신한 메시지 데이터
   */
  handleMessage(data) {
    // 알 수 없는 타입인 경우에만 전체 데이터 로깅
    if (!data.type || !this.isKnownMessageType(data.type)) {
      console.log('📨 알 수 없는 메시지 타입 수신:', {
        type: data.type,
        event_id: data.event_id,
        fullData: JSON.stringify(data, null, 2)
      })
    }
    
    debugLog('📨 메시지 수신:', {
      type: data.type,
      event_id: data.event_id,
      hasDelta: !!data.delta,
      hasAudio: !!data.audio
    })
    
    switch (data.type) {
      case 'session.created':
        // 🔵🔵🔵 session.created 메시지 처리 로그 (항상 출력)
        console.log('🔵🔵🔵 [handleMessage] session.created 메시지 처리! 🔵🔵🔵')
        console.log('🔵 [handleMessage] session.created 데이터:', data)
        console.log('🔵 [handleMessage] session_created 이벤트 emit 예정...')
        this.emit('session_created', data)
        console.log('🔵 [handleMessage] session_created 이벤트 emit 완료!')
        break
        
      case 'session.updated':
        this.emit('session_updated', data)
        break
        
      case 'conversation.item.created':
        this.emit('conversation_item_created', data)
        break
        
      case 'conversation.item.done': {
        // 사용자 입력이 완료됨 - 전사 결과 확인
        console.log('🔵🔵🔵 [conversation.item.done] 메시지 수신! 🔵🔵🔵')
        
        // 여러 방법으로 전사 결과 찾기
        let transcript = null
        
        // 방법 1: data.item.content 배열에서 찾기
        if (data.item && data.item.content && Array.isArray(data.item.content)) {
          const transcriptionContent = data.item.content.find(c => {
            if (c.type === 'input_text' && c.text) {
              return true
            }
            if (c.type === 'input_audio_transcription' && c.transcript) {
              return true
            }
            return false
          })
          
          if (transcriptionContent) {
            transcript = transcriptionContent.transcript || transcriptionContent.text
            console.log('✅ [conversation.item.done] content에서 전사 결과 발견 (길이:', transcript ? transcript.length : 0, ')')
          }
        }
        
        // 방법 2: data.item 자체에 transcript가 있는지 확인
        if (!transcript && data.item && data.item.transcript) {
          transcript = data.item.transcript
          console.log('✅ [conversation.item.done] item.transcript에서 발견 (길이:', transcript.length, ')')
        }
        
        // 방법 3: data 자체에 transcript가 있는지 확인
        if (!transcript && data.transcript) {
          transcript = data.transcript
          console.log('✅ [conversation.item.done] data.transcript에서 발견 (길이:', transcript.length, ')')
        }
        
        if (transcript && transcript.trim()) {
          console.log('✅✅✅ [conversation.item.done] 최종 전사 결과 (길이:', transcript.trim().length, ', 미리보기:', transcript.trim().substring(0, 100) + '...)')
          // transcription_completed 이벤트 발생
          this.emit('transcription_completed', { transcript: transcript.trim(), event_id: data.event_id })
        } else {
          console.warn('⚠️ [conversation.item.done] 전사 결과를 찾을 수 없습니다.')
        }
        debugLog(`📨 메시지 수신 (처리 완료): ${data.type}`)
        break
      }
        
      case 'input_audio_buffer.committed':
        // 오디오 버퍼 커밋 완료 - 이벤트 발생
        debugLog('📤 input_audio_buffer.committed 수신')
        this.emit('audio_buffer_committed', data)
        break
        
      case 'input_audio_buffer.speech_started':
        // 사용자 말하기 시작 감지
        console.log('🎤 [speech_started] 사용자가 말하기 시작했습니다')
        debugLog('🎤 speech_started', data)
        this.emit('speech_started', data)
        break
        
      case 'input_audio_buffer.speech_stopped':
        // 사용자 말하기 중지 감지
        console.log('🛑 [speech_stopped] 사용자가 말하기를 중지했습니다')
        debugLog('🛑 speech_stopped', data)
        this.emit('speech_stopped', data)
        break
        
      case 'conversation.item.input_audio_transcription.completed':
        // 사용자 음성 입력 전사 완료
        console.log('✅ 사용자 음성 입력 전사 완료:', {
          transcription: data.transcript,
          event_id: data.event_id
        })
        this.emit('transcription_completed', data)
        break
        
      case 'conversation.item.input_audio_transcription.failed':
        // 사용자 음성 입력 전사 실패
        console.error('❌ 사용자 음성 입력 전사 실패:', {
          error: data.error,
          event_id: data.event_id
        })
        this.emit('transcription_failed', data)
        break
        
      case 'response.audio_transcript.delta':
        this.emit('audio_transcript_delta', data)
        break
        
      case 'response.audio_transcript.done':
        this.emit('audio_transcript_done', data)
        break
        
      case 'response.audio.delta':
        // 오디오 데이터 수신
        debugLog('🔊 오디오 데이터 수신:', {
          type: 'response.audio.delta',
          hasDelta: !!data.delta,
          deltaLength: data.delta ? data.delta.length : 0,
          deltaPreview: data.delta ? data.delta.substring(0, 50) + '...' : null
        })
        if (data.delta) {
          this.emit('audio_delta', data.delta)
        } else {
          debugLog('⚠️ response.audio.delta에 delta가 없습니다:', data)
        }
        break
        
      case 'response.audio.done':
        debugLog('🔊 오디오 전송 완료')
        this.emit('audio_done', data)
        break
      
      // 실제 OpenAI Realtime API에서 사용하는 메시지 타입들
      case 'response.output_audio.delta':
        // 실제 오디오 데이터 수신 (response.audio.delta가 아닌 response.output_audio.delta)
        // 🔵🔵🔵 AI 오디오 수신 로그 (항상 출력)
        console.log('🔊🔊🔊 [handleMessage] response.output_audio.delta 수신! 🔊🔊🔊')
        console.log('🔊 [handleMessage] 오디오 데이터 정보:', {
          type: 'response.output_audio.delta',
          hasDelta: !!data.delta,
          deltaLength: data.delta ? data.delta.length : 0,
          deltaPreview: data.delta ? data.delta.substring(0, 50) + '...' : null
        })
        debugLog('🔊 오디오 데이터 수신 (output_audio.delta):', {
          type: 'response.output_audio.delta',
          hasDelta: !!data.delta,
          deltaLength: data.delta ? data.delta.length : 0,
          deltaPreview: data.delta ? data.delta.substring(0, 50) + '...' : null
        })
        if (data.delta) {
          console.log('🔊 [handleMessage] audio_delta 이벤트 emit 예정...')
          this.emit('audio_delta', data.delta)
          console.log('🔊 [handleMessage] audio_delta 이벤트 emit 완료!')
        } else {
          console.error('❌❌❌ [handleMessage] response.output_audio.delta에 delta가 없습니다! ❌❌❌', data)
          debugLog('⚠️ response.output_audio.delta에 delta가 없습니다:', data)
        }
        break
        
      case 'response.output_audio.done':
        debugLog('🔊 오디오 전송 완료 (output_audio.done)')
        this.emit('audio_done', data)
        break
        
      case 'response.output_audio_transcript.delta':
        // AI 응답의 텍스트 전사
        debugLog('📝 AI 응답 텍스트 전사 (output_audio_transcript.delta):', data)
        if (data.delta) {
          this.emit('audio_transcript_delta', data)
        }
        break
        
      case 'response.output_audio_transcript.done':
        debugLog('📝 AI 응답 텍스트 전사 완료')
        this.emit('audio_transcript_done', data)
        break
        
      case 'response.output_item.added':
      case 'response.output_item.done':
      case 'response.content_part.added':
      case 'response.content_part.done':
      case 'conversation.item.added':
      case 'rate_limits.updated':
        // 이러한 메시지들은 로깅만 하고 이벤트는 발생시키지 않음
        debugLog(`📨 메시지 수신 (처리 불필요): ${data.type}`)
        break
        
      case 'response.done':
        // 🔵🔵🔵 AI 응답 완료 로그 (항상 출력)
        console.log('🔵🔵🔵 [handleMessage] response.done 수신! 🔵🔵🔵')
        console.log('🔵 [handleMessage] AI 응답이 완료되었습니다!')
        console.log('🔵 [handleMessage] response.done 데이터:', data)
        this.emit('response_done', data)
        break
        
      case 'response.created':
        // 🔵🔵🔵 AI 응답 생성 로그 (항상 출력)
        console.log('🔵🔵🔵 [handleMessage] response.created 수신! 🔵🔵🔵')
        console.log('🔵 [handleMessage] AI가 응답 생성을 시작했습니다!')
        console.log('🔵 [handleMessage] response.created 데이터:', data)
        this.emit('response_created', data)
        break
        
      case 'error': {
        // 에러 상세 정보 로깅
        const errorDetails = {
          type: data.type,
          event_id: data.event_id,
          error: data.error,
          error_type: data.error?.type,
          error_message: data.error?.message,
          error_code: data.error?.code,
          error_param: data.error?.param,
          full_data: JSON.stringify(data, null, 2)
        }
        debugLog('❌ Realtime 오류 상세:', errorDetails)
        console.error('❌ Realtime API 에러 전체 데이터:', JSON.stringify(data, null, 2))
        console.error('❌ Realtime API 에러 객체:', data)
        console.error('❌ Realtime API 에러.error:', data.error)
        if (data.error) {
          console.error('❌ 에러 타입:', data.error.type)
          console.error('❌ 에러 메시지:', data.error.message)
          console.error('❌ 에러 코드:', data.error.code)
          console.error('❌ 에러 파라미터:', data.error.param)
        }
        this.emit('error', data)
        break
      }
        
      default:
        // 알 수 없는 메시지 타입 로깅 (전체 데이터 포함)
        // console.log는 항상 출력되도록 (디버그 모드와 무관)
        console.warn('⚠️ 알 수 없는 메시지 타입:', data.type)
        console.log('⚠️ 알 수 없는 메시지 전체 데이터:', JSON.stringify(data, null, 2))
        console.log('⚠️ 알 수 없는 메시지 객체:', data)
        debugLog('⚠️ 알 수 없는 메시지 타입:', {
          type: data.type,
          event_id: data.event_id,
          fullData: JSON.stringify(data, null, 2)
        })
    }
  }
  
  /**
   * 오디오 데이터 전송
   * @param {ArrayBuffer} audioData - PCM16 오디오 데이터
   */
  sendAudio(audioData) {
    if (!this.isConnected || !this.ws) {
      debugLog('⚠️ WebSocket이 연결되지 않았습니다.')
      return
    }
    
    // Base64로 인코딩
    const base64Audio = btoa(
      String.fromCharCode.apply(null, new Uint8Array(audioData))
    )
    
    const message = {
      type: 'input_audio_buffer.append',
      audio: base64Audio
    }
    
    // 오디오 전송 통계 (매 100번째 전송마다 로그)
    if (!this.audioSendCount) this.audioSendCount = 0
    this.audioSendCount++
    
    if (this.audioSendCount % 100 === 0) {
      console.log('📤 사용자 오디오 전송 중:', {
        전송횟수: this.audioSendCount,
        오디오크기: base64Audio.length,
        원본크기: audioData.byteLength,
        연결상태: this.isConnected
      })
    }
    
    this.ws.send(JSON.stringify(message))
  }
  
  /**
   * 오디오 입력 완료 신호 전송
   */
  commitAudio() {
    if (!this.isConnected || !this.ws) {
      debugLog('⚠️ commitAudio 실패: 연결되지 않음')
      return
    }
    
    const message = {
      type: 'input_audio_buffer.commit'
    }
    
    debugLog('📤 input_audio_buffer.commit 전송')
    this.ws.send(JSON.stringify(message))
  }
  
  /**
   * Response 생성 요청
   * @param {string} text - 텍스트 입력 (선택사항)
   * 
   * 참고: modalities는 세션 생성 시 설정되며, response.create에서는 지정할 수 없습니다.
   * 세션 생성 시 modalities=["audio", "text"]로 설정되어 있으므로,
   * response.create는 단순히 응답 생성을 요청하기만 하면 됩니다.
   */
  requestResponse(text = null) {
    // 🔵🔵🔵 requestResponse 호출 로그 (항상 출력)
    console.log('🔵🔵🔵 [requestResponse] 메서드 호출됨! 🔵🔵🔵')
    console.log('🔵 [requestResponse] 호출 시점 상태:', {
      isConnected: this.isConnected,
      hasWebSocket: !!this.ws,
      textProvided: !!text,
      textLength: text ? text.length : 0
    })
    
    if (!this.isConnected || !this.ws) {
      console.error('❌❌❌ [requestResponse] 실패: 연결되지 않음! ❌❌❌', {
        isConnected: this.isConnected,
        hasWebSocket: !!this.ws
      })
      debugLog('⚠️ requestResponse 실패: 연결되지 않음')
      return
    }
    
    const message = {
      type: 'response.create'
    }
    
    // instructions가 필요한 경우에만 추가
    if (text) {
      message.response = {
        instructions: text
      }
      console.log('🔵 [requestResponse] text 파라미터가 제공됨, response.instructions에 추가:', {
        textLength: text.length,
        textPreview: text.substring(0, 100) + '...'
      })
    } else {
      console.log('🔵 [requestResponse] text 파라미터 없음 - 기본 response.create만 전송')
    }
    
    console.log('🔵🔵🔵 [requestResponse] 전송할 메시지: 🔵🔵🔵')
    console.log('🔵 [requestResponse] 메시지 내용:', JSON.stringify(message, null, 2))
    debugLog('📤 response.create 전송:', message)
    console.log('📤 response.create 메시지:', JSON.stringify(message, null, 2))
    
    try {
      this.ws.send(JSON.stringify(message))
      console.log('✅✅✅ [requestResponse] 메시지 전송 성공! ✅✅✅')
    } catch (error) {
      console.error('❌❌❌ [requestResponse] 메시지 전송 실패! ❌❌❌', error)
    }
  }
  
  /**
   * 텍스트 메시지 전송 (음성 대신 텍스트로 입력)
   * @param {string} text - 전송할 텍스트
   */
  sendText(text) {
    if (!this.isConnected || !this.ws) {
      console.error('❌❌❌ [sendText] 실패: 연결되지 않음! ❌❌❌')
      debugLog('⚠️ sendText 실패: 연결되지 않음')
      return
    }
    
    if (!text || !text.trim()) {
      console.error('❌❌❌ [sendText] 실패: 텍스트가 비어있습니다! ❌❌❌')
      return
    }
    
    // OpenAI Realtime API에서 텍스트를 보내는 방법: conversation.item.create
    const message = {
      type: 'conversation.item.create',
      item: {
        type: 'message',
        role: 'user',
        content: [
          {
            type: 'input_text',
            text: text.trim()
          }
        ]
      }
    }
    
    console.log('🔵🔵🔵 [sendText] 텍스트 메시지 전송! 🔵🔵🔵')
    console.log('🔵 [sendText] 전송할 텍스트 길이:', text.trim().length)
    console.log('🔵 [sendText] 전송할 텍스트 미리보기:', text.trim().substring(0, 200) + '...')
    
    try {
      this.ws.send(JSON.stringify(message))
      console.log('✅✅✅ [sendText] 텍스트 메시지 전송 성공! ✅✅✅')
    } catch (error) {
      console.error('❌❌❌ [sendText] 텍스트 메시지 전송 실패! ❌❌❌', error)
    }
  }
  
  /**
   * 이벤트 리스너 등록
   * @param {string} event - 이벤트 이름
   * @param {Function} handler - 이벤트 핸들러
   */
  on(event, handler) {
    if (!this.eventHandlers[event]) {
      this.eventHandlers[event] = []
    }
    this.eventHandlers[event].push(handler)
  }
  
  /**
   * 이벤트 리스너 제거
   * @param {string} event - 이벤트 이름
   * @param {Function} handler - 이벤트 핸들러
   */
  off(event, handler) {
    if (this.eventHandlers[event]) {
      this.eventHandlers[event] = this.eventHandlers[event].filter(h => h !== handler)
    }
  }
  
  /**
   * 이벤트 발생
   * @param {string} event - 이벤트 이름
   * @param {*} data - 이벤트 데이터
   */
  emit(event, data) {
    if (this.eventHandlers[event]) {
      this.eventHandlers[event].forEach(handler => {
        try {
          handler(data)
        } catch (error) {
          debugLog('❌ 이벤트 핸들러 오류:', error)
        }
      })
    }
  }
  
  /**
   * 연결 종료
   */
  disconnect() {
    if (this.ws) {
      this.ws.close(1000, 'Normal closure')
      this.ws = null
    }
    this.isConnected = false
  }
}

