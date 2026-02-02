/**
 * 음성 인터뷰 관련 공통 유틸리티
 * iOS와 웹에서 동일한 instruction을 사용하도록 통합 관리
 */

import axios from 'axios'
import { debugLog } from './debugUtils'

/**
 * 필수 규칙(mandatory rules)을 API에서 로드
 * iOS와 웹 모두에서 동일한 source를 사용하도록 보장
 * 
 * @param {string} language - 언어 코드
 * @returns {Promise<{languageInstruction: string, mandatoryRules: string}>}
 */
export async function loadMandatoryRules(language = 'ko') {
  try {
    debugLog('🔵 [loadMandatoryRules] 필수 프롬프트 로드 시작:', { language })
    
    const response = await axios.get(`/api/realtime/mandatory-rules/?language=${language}`)
    
    debugLog('🔵 [loadMandatoryRules] API 응답 받음:', {
      status: response.status,
      hasData: !!response.data,
      dataKeys: response.data ? Object.keys(response.data) : []
    })
    
    if (response.data) {
      const languageInstruction = response.data.language_instruction || ''
      const mandatoryPrompts = response.data.mandatory_prompts || ''
      
      debugLog('✅ [loadMandatoryRules] 필수 프롬프트 로드 성공:', {
        language,
        languageInstructionLength: languageInstruction.length,
        mandatoryPromptsLength: mandatoryPrompts.length,
        languageInstructionPreview: languageInstruction ? languageInstruction.substring(0, 100) + '...' : '(비어있음)',
        mandatoryPromptsPreview: mandatoryPrompts ? mandatoryPrompts.substring(0, 100) + '...' : '(비어있음)'
      })
      
      return {
        languageInstruction,
        mandatoryRules: mandatoryPrompts  // 하위 호환성을 위해 mandatoryRules로도 반환
      }
    } else {
      debugLog('⚠️ [loadMandatoryRules] API 응답에 data가 없습니다:', response)
      return {
        languageInstruction: '',
        mandatoryRules: ''
      }
    }
  } catch (error) {
    debugLog('❌ [loadMandatoryRules] 필수 프롬프트 로드 실패:', {
      error: error,
      message: error.message,
      response: error.response ? {
        status: error.response.status,
        data: error.response.data
      } : null
    })
    
    // 에러 발생 시 빈 값 반환 (기본 템플릿은 계속 사용)
    return {
      languageInstruction: '',
      mandatoryRules: ''
    }
  }
}

/**
 * 인터뷰 프롬프트 템플릿을 API에서 로드
 * 
 * @param {string} language - 언어 코드
 * @returns {Promise<{baseTemplate: string, questionRestriction: string, mandatoryRulesMarker: string}>}
 */
export async function loadInterviewPromptTemplate(language = 'ko') {
  try {
    debugLog('🔵 [loadInterviewPromptTemplate] 인터뷰 프롬프트 템플릿 로드 시작:', { language })
    
    const response = await axios.get(`/api/realtime/interview-prompt-template/?language=${language}`)
    
    debugLog('🔵 [loadInterviewPromptTemplate] API 응답 받음:', {
      status: response.status,
      hasData: !!response.data,
      dataKeys: response.data ? Object.keys(response.data) : []
    })
    
    if (response.data) {
      const template = {
        baseTemplate: response.data.base_template || '',
        questionRestriction: response.data.question_restriction || '',
        mandatoryRulesMarker: response.data.mandatory_rules_marker || ''
      }
      
      debugLog('✅ [loadInterviewPromptTemplate] 인터뷰 프롬프트 템플릿 로드 성공:', {
        language,
        baseTemplateLength: template.baseTemplate.length,
        questionRestrictionLength: template.questionRestriction.length,
        mandatoryRulesMarker: template.mandatoryRulesMarker
      })
      
      return template
    } else {
      debugLog('⚠️ [loadInterviewPromptTemplate] API 응답에 data가 없습니다:', response)
      return {
        baseTemplate: '',
        questionRestriction: '',
        mandatoryRulesMarker: ''
      }
    }
  } catch (error) {
    debugLog('❌ [loadInterviewPromptTemplate] 인터뷰 프롬프트 템플릿 로드 실패:', {
      error: error,
      message: error.message,
      response: error.response ? {
        status: error.response.status,
        data: error.response.data
      } : null
    })
    
    // 에러 발생 시 빈 값 반환
    return {
      baseTemplate: '',
      questionRestriction: '',
      mandatoryRulesMarker: ''
    }
  }
}

/**
 * 인터뷰 프롬프트 텍스트 생성
 * iOS와 웹에서 동일한 형식으로 프롬프트를 생성하도록 보장
 * 
 * @param {Object} options - 프롬프트 생성 옵션
 * @param {string} options.language - 언어 코드
 * @param {string} options.questionsText - 질문 목록 텍스트
 * @param {string} options.languageInstruction - 언어 지시사항 (loadMandatoryRules에서 가져옴)
 * @param {string} options.mandatoryRules - 필수 규칙 (loadMandatoryRules에서 가져옴)
 * @param {Object} options.template - 프롬프트 템플릿 (loadInterviewPromptTemplate에서 가져옴, 선택적)
 * @returns {string} 생성된 프롬프트 텍스트
 */
export function buildInterviewPrompt({ language, questionsText, languageInstruction, mandatoryRules, template = null }) {
  const currentLang = language || 'ko'
  
  // 템플릿이 제공되지 않았거나 비어있으면 기본값 사용 (fallback)
  let baseTemplate = template?.baseTemplate || ''
  let questionRestriction = template?.questionRestriction || ''
  let mandatoryRulesMarker = template?.mandatoryRulesMarker || ''
  
  // 템플릿이 없을 때 fallback (하위 호환성)
  if (!baseTemplate) {
    if (currentLang === 'en') {
      baseTemplate = `[Step 1] Preparation
- Read file (load question list)
- Declare interview format: "I am the interviewer, you are the interviewee"

[Step 2] Interview Start
- Present one question from the question list in order
- Wait for user's answer

[Step 3] Evaluation and Next Question
- Provide evaluation of user's answer (strengths, improvement points)
- ⚠️ DO NOT create follow-up questions or additional questions
- ⚠️ MUST only present the next question from the question list
- DO NOT create or add questions that are not in the question list

[Step 4] Feedback
- After all questions are completed
- Summarize strengths / improvement points based on answers`
    } else if (currentLang === 'zh') {
      baseTemplate = `[步骤 1] 准备
- 读取文件（加载问题列表）
- 声明面试格式："我是面试官，你是面试者"

[步骤 2] 面试开始
- 按顺序从问题列表中提出一个问题
- 等待用户的回答

[步骤 3] 评估和下一个问题
- 提供用户回答的评估（优点、改进点）
- ⚠️ 不要创建后续问题或额外问题
- ⚠️ 必须只从问题列表中提出下一个问题
- 不要创建或添加不在问题列表中的问题

[步骤 4] 反馈
- 所有问题完成后
- 根据答案总结优点 / 改进点`
    } else if (currentLang === 'es') {
      baseTemplate = `[Paso 1] Preparación
- Leer archivo (cargar lista de preguntas)
- Declarar formato de entrevista: "Yo soy el entrevistador, tú eres el entrevistado"

[Paso 2] Inicio de la Entrevista
- Presentar una pregunta de la lista de preguntas en orden
- Esperar la respuesta del usuario

[Paso 3] Evaluación y Siguiente Pregunta
- Proporcionar evaluación de la respuesta del usuario (fortalezas, puntos de mejora)
- ⚠️ NO crear preguntas de seguimiento o preguntas adicionales
- ⚠️ DEBE solo presentar la siguiente pregunta de la lista de preguntas
- NO crear o agregar preguntas que no estén en la lista de preguntas

[Paso 4] Retroalimentación
- Después de que se completen todas las preguntas
- Resumir fortalezas / puntos de mejora basados en las respuestas`
    } else {
      baseTemplate = `[Step 1] 준비
- 파일 읽기 (질문 목록 로드)
- 인터뷰 형식 선언: "나는 인터뷰어, 사용자는 인터뷰이"

[Step 2] 인터뷰 시작
- 질문 목록에서 순서대로 질문 하나 제시
- 사용자의 답변 대기

[Step 3] 평가 및 다음 질문
- 사용자의 답변에 대한 평가 제공 (강점, 개선점)
- ⚠️ 절대 꼬리 질문이나 추가 질문을 생성하지 마세요
- ⚠️ 반드시 질문 목록에서 다음 질문만 제시하세요
- 질문 목록에 없는 질문을 생성하거나 추가하지 마세요

[Step 4] 피드백
- 모든 질문이 끝난 뒤
- 답변 내용을 바탕으로 강점 / 개선 포인트 요약`
    }
  }
  
  if (!questionRestriction) {
    if (currentLang === 'en') {
      questionRestriction = `⚠️⚠️⚠️ CRITICAL: You MUST ONLY use questions from the question list below. ⚠️⚠️⚠️
- DO NOT create or generate any questions that are NOT in the question list below.
- DO NOT add new questions or modify existing questions.
- DO NOT create follow-up questions or additional questions based on user's answers.
- You can ONLY select questions from the provided list in order.
- After evaluating a user's answer, proceed to the NEXT question from the list.
- This is essential for scoring and evaluation purposes.

Question List (You MUST only use these questions in order):`
    } else if (currentLang === 'zh') {
      questionRestriction = `⚠️⚠️⚠️ 非常重要：您必须仅使用下面问题列表中的问题。⚠️⚠️⚠️
- 不要创建或生成不在下面问题列表中的任何问题。
- 不要添加新问题或修改现有问题。
- 不要根据用户的答案创建后续问题或额外问题。
- 您只能按顺序从提供的列表中选择问题。
- 评估用户的答案后，继续列表中的下一个问题。
- 这对于评分和评估目的至关重要。

问题列表（您必须仅按顺序使用这些问题）：`
    } else if (currentLang === 'es') {
      questionRestriction = `⚠️⚠️⚠️ CRÍTICO: DEBE usar SOLO preguntas de la lista de preguntas a continuación. ⚠️⚠️⚠️
- NO crear o generar ninguna pregunta que NO esté en la lista de preguntas a continuación.
- NO agregar nuevas preguntas o modificar preguntas existentes.
- NO crear preguntas de seguimiento o preguntas adicionales basadas en las respuestas del usuario.
- Solo puede seleccionar preguntas de la lista proporcionada en orden.
- Después de evaluar la respuesta del usuario, proceda a la SIGUIENTE pregunta de la lista.
- Esto es esencial para fines de puntuación y evaluación.

Lista de Preguntas (DEBE usar solo estas preguntas en orden):`
    } else {
      questionRestriction = `⚠️⚠️⚠️ 매우 중요: 반드시 아래 질문 목록에서만 질문을 선택하세요. ⚠️⚠️⚠️
- 아래 질문 목록에 없는 질문을 생성하거나 추가하지 마세요.
- 기존 질문을 수정하지 마세요.
- 사용자의 답변을 바탕으로 꼬리 질문이나 추가 질문을 생성하지 마세요.
- 제공된 목록의 질문만 순서대로 선택할 수 있습니다.
- 사용자의 답변을 평가한 후, 목록에서 다음 질문으로 진행하세요.
- 이것은 점수 처리 및 평가를 위해 필수입니다.

질문 목록 (반드시 이 목록에서만 순서대로 질문을 선택하세요):`
    }
  }
  
  if (!mandatoryRulesMarker) {
    if (currentLang === 'en') {
      mandatoryRulesMarker = '=== Mandatory Rules (Auto Added) ==='
    } else if (currentLang === 'zh') {
      mandatoryRulesMarker = '=== 强制规则（自动添加）==='
    } else if (currentLang === 'es') {
      mandatoryRulesMarker = '=== Reglas Obligatorias (Agregadas Automáticamente) ==='
    } else {
      mandatoryRulesMarker = '=== 필수 규칙 (자동 추가) ==='
    }
  }

  let promptText = `${baseTemplate}

${questionRestriction}

${questionsText}`

  // YAML 내용이 있으면 맨 아래에 append
  if (languageInstruction || mandatoryRules) {
    promptText += `


${mandatoryRulesMarker}

${languageInstruction}

${mandatoryRules}`
  }
  
  return promptText
}

/**
 * AI 응답에서 묵음 처리 메시지 제거
 * iOS와 웹에서 동일한 필터링 로직을 사용하도록 보장
 * 
 * @param {string} text - 필터링할 텍스트
 * @returns {string} 필터링된 텍스트
 */
export function filterSilenceMessages(text) {
  if (!text) return text

  let filtered = text

  // 묵음 처리 메시지 제거 (절대 표시되면 안 됨)
  const silencePatterns = [
    /\([^)]*사용자가\s*말을\s*마칠\s*때까지\s*기다립니다[^)]*\)/gi,
    /\([^)]*사용자가\s*말하는\s*중입니다[^)]*\)/gi,
    /\([^)]*사용자의\s*답변을\s*기다리는\s*중입니다[^)]*\)/gi,
    /\([^)]*waiting\s*for\s*user\s*to\s*finish[^)]*\)/gi,
    /\([^)]*waiting\s*for\s*user\s*speech[^)]*\)/gi,
    /사용자가\s*말을\s*마칠\s*때까지\s*기다립니다[^\n]*/gi,
    /사용자가\s*말하는\s*중입니다[^\n]*/gi,
    /사용자의\s*답변을\s*기다리는\s*중입니다[^\n]*/gi,
    /waiting\s*for\s*user\s*to\s*finish[^\n]*/gi,
    /waiting\s*for\s*user\s*speech[^\n]*/gi,
  ]

  for (const pattern of silencePatterns) {
    filtered = filtered.replace(pattern, '')
  }

  return filtered
}

/**
 * AI 응답에서 마무리 인사말 필터링
 * iOS와 웹에서 동일한 필터링 로직을 사용하도록 보장
 * 
 * @param {string} text - 필터링할 텍스트
 * @returns {string} 필터링된 텍스트
 */
export function filterEndingGreeting(text) {
  if (!text) return text

  // 먼저 묵음 처리 메시지 제거
  let filtered = filterSilenceMessages(text)

  // 마무리 인사말 패턴 제거
  const endingPatterns = [
    /^[^\n]*네,\s*모든\s*질문에\s*대한\s*답변을\s*들었습니다[^\n]*\n?/i,
    /^[^\n]*모든\s*질문에\s*대한\s*답변을\s*들었습니다[^\n]*\n?/i,
    /^[^\n]*인터뷰를\s*마무리하겠습니다[^\n]*\n?/i,
    /^[^\n]*인터뷰를\s*종료하겠습니다[^\n]*\n?/i,
    /^[^\n]*Thank\s*you\s*for\s*all\s*your\s*answers[^\n]*\n?/i,
    /^[^\n]*I\s*will\s*now\s*conclude\s*the\s*interview[^\n]*\n?/i,
  ]

  for (const pattern of endingPatterns) {
    filtered = filtered.replace(pattern, '')
  }

  // 빈 줄 제거 및 정리
  filtered = filtered.replace(/^\s*\n+/, '')
  filtered = filtered.replace(/\n+\s*$/, '')
  filtered = filtered.replace(/\n{3,}/g, '\n\n')
  filtered = filtered.trim()

  if (filtered !== text) {
    debugLog('🔍 [filterEndingGreeting] 마무리 인사말 필터링:', {
      original: text.substring(0, 200),
      filtered: filtered.substring(0, 200)
    })
  }

  return filtered
}

/**
 * AI 응답에서 초기 인사말 필터링
 * iOS와 웹에서 동일한 필터링 로직을 사용하도록 보장
 * 
 * @param {string} text - 필터링할 텍스트
 * @returns {string} 필터링된 텍스트 (질문 내용만 추출)
 */
export function filterInitialGreeting(text) {
  if (!text) return text

  // 먼저 묵음 처리 메시지 제거
  let filtered = filterSilenceMessages(text)

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
}

