/**
 * 오디오 처리 유틸리티
 * PCM16 인코딩/디코딩 및 Web Audio API 래퍼
 */

/**
 * PCM16 오디오 데이터를 Float32Array로 변환
 * @param {ArrayBuffer} pcm16Data - PCM16 오디오 데이터
 * @returns {Float32Array} Float32Array 오디오 데이터
 */
export function pcm16ToFloat32(pcm16Data) {
  const int16Array = new Int16Array(pcm16Data)
  const float32Array = new Float32Array(int16Array.length)
  
  for (let i = 0; i < int16Array.length; i++) {
    // Int16 (-32768 ~ 32767)를 Float32 (-1.0 ~ 1.0)로 변환
    float32Array[i] = int16Array[i] / 32768.0
  }
  
  return float32Array
}

/**
 * Float32Array 오디오 데이터를 PCM16으로 변환
 * @param {Float32Array} float32Data - Float32Array 오디오 데이터
 * @returns {ArrayBuffer} PCM16 오디오 데이터
 */
export function float32ToPcm16(float32Data) {
  const int16Array = new Int16Array(float32Data.length)
  
  for (let i = 0; i < float32Data.length; i++) {
    // Float32 (-1.0 ~ 1.0)를 Int16 (-32768 ~ 32767)로 변환
    const sample = Math.max(-1, Math.min(1, float32Data[i]))
    int16Array[i] = sample < 0 ? sample * 0x8000 : sample * 0x7FFF
  }
  
  return int16Array.buffer
}

/**
 * AudioContext 초기화
 * @returns {Promise<AudioContext>} AudioContext 인스턴스
 */
export async function createAudioContext() {
  const AudioContextClass = window.AudioContext || window.webkitAudioContext
  const audioContext = new AudioContextClass({
    sampleRate: 24000 // OpenAI Realtime API 출력 샘플레이트
  })
  
  // AudioContext가 suspended 상태일 수 있으므로 resume
  if (audioContext.state === 'suspended') {
    await audioContext.resume()
  }
  
  return audioContext
}

/**
 * PCM16 오디오 데이터를 AudioBuffer로 변환하여 재생
 * @param {AudioContext} audioContext - AudioContext 인스턴스
 * @param {ArrayBuffer} pcm16Data - PCM16 오디오 데이터
 * @param {number} sampleRate - 샘플레이트 (기본값: 24000)
 * @returns {Promise<AudioBufferSourceNode>} 재생 중인 AudioBufferSourceNode
 */
export async function playPcm16Audio(audioContext, pcm16Data, sampleRate = 24000) {
  const float32Data = pcm16ToFloat32(pcm16Data, sampleRate)
  const audioBuffer = audioContext.createBuffer(1, float32Data.length, sampleRate)
  audioBuffer.getChannelData(0).set(float32Data)
  
  const source = audioContext.createBufferSource()
  source.buffer = audioBuffer
  source.connect(audioContext.destination)
  
  return new Promise((resolve, reject) => {
    source.onended = () => resolve(source)
    source.onerror = (error) => reject(error)
    source.start(0)
  })
}

/**
 * 마이크 스트림에서 오디오 데이터 캡처
 * @param {MediaStream} stream - 마이크 MediaStream
 * @returns {Promise<{audioContext: AudioContext, processor: ScriptProcessorNode}>}
 */
export async function captureAudioFromStream(stream) {
  const audioContext = await createAudioContext()
  
  // MediaStreamAudioSourceNode 생성
  const source = audioContext.createMediaStreamSource(stream)
  
  // ScriptProcessorNode로 오디오 데이터 캡처
  const bufferSize = 4096
  const processor = audioContext.createScriptProcessor(bufferSize, 1, 1)
  
  source.connect(processor)
  processor.connect(audioContext.destination)
  
  return { audioContext, processor }
}

/**
 * 오디오 데이터 버퍼링
 */
export class AudioBuffer {
  constructor(maxSize = 1024 * 1024) { // 1MB 기본
    this.buffer = new Uint8Array(maxSize)
    this.length = 0
    this.maxSize = maxSize
  }
  
  /**
   * 데이터 추가
   * @param {Uint8Array} data - 추가할 데이터
   */
  append(data) {
    if (this.length + data.length > this.maxSize) {
      // 버퍼가 가득 찬 경우, 오래된 데이터 제거
      const removeSize = this.length + data.length - this.maxSize
      this.buffer.set(this.buffer.subarray(removeSize), 0)
      this.length -= removeSize
    }
    
    this.buffer.set(data, this.length)
    this.length += data.length
  }
  
  /**
   * 버퍼에서 데이터 가져오기
   * @param {number} size - 가져올 데이터 크기
   * @returns {Uint8Array} 데이터
   */
  getData(size) {
    if (size > this.length) {
      size = this.length
    }
    
    const data = this.buffer.subarray(0, size)
    this.buffer.set(this.buffer.subarray(size), 0)
    this.length -= size
    
    return data
  }
  
  /**
   * 버퍼 비우기
   */
  clear() {
    this.length = 0
  }
  
  /**
   * 현재 버퍼 크기
   * @returns {number} 버퍼 크기 (바이트)
   */
  getSize() {
    return this.length
  }
}

