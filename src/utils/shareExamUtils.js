import axios from 'axios'
import { debugLog } from '@/utils/debugUtils'
import { hasStudySpecificAdminPermission } from '@/utils/permissionUtils'
import { SUPPORTED_LANGUAGES } from '@/utils/multilingualUtils'

/**
 * 시험 공유 관련 공통 유틸리티 함수들
 */

/**
 * 비공개 시험 공유를 위한 스터디와 Task 생성
 * @param {Object} context - Vue 컴포넌트 컨텍스트 (this)
 * @param {Object} exam - 시험 객체
 * @param {string} currentLang - 현재 언어 ('ko', 'en', 'es', 'zh', 'ja'), 기본값은 'en'
 * @returns {Promise<Object>} 생성된 스터디 객체
 */
export async function createStudyAndTaskForSharing(context, exam, currentLang = 'en') {
  if (!exam) {
    throw new Error('시험 정보가 없습니다.')
  }
  
  // 스터디 생성
  const studyData = {
    is_public: false, // 비공개 스터디
  }
  
  // Exam 제목 가져오기 (모든 언어 지원, 프로필 언어 우선)
  const getExamTitle = (lang) => {
    // 프로필 언어 우선, 그 다음 display_title, title, 기본 언어 순서
    if (lang === 'ko') {
      return exam.title_ko || exam.display_title || exam.title || exam.title_en || exam.title_es || exam.title_zh || exam.title_ja || '공유 시험'
    } else if (lang === 'en') {
      return exam.title_en || exam.display_title || exam.title || exam.title_ko || exam.title_es || exam.title_zh || exam.title_ja || 'Shared Exam'
    } else if (lang === 'es') {
      return exam.title_es || exam.display_title || exam.title || exam.title_en || exam.title_ko || exam.title_zh || exam.title_ja || 'Examen compartido'
    } else if (lang === 'zh') {
      return exam.title_zh || exam.display_title || exam.title || exam.title_en || exam.title_ko || exam.title_es || exam.title_ja || '共享考试'
    } else if (lang === 'ja') {
      return exam.title_ja || exam.display_title || exam.title || exam.title_en || exam.title_ko || exam.title_es || exam.title_zh || '共有試験'
    } else {
      // 기본 언어는 'en'
      return exam.title_en || exam.display_title || exam.title || exam.title_ko || exam.title_es || exam.title_zh || exam.title_ja || 'Shared Exam'
    }
  }
  
  // 프로필 언어를 우선적으로 사용하여 스터디 제목 설정
  // Study 모델은 모든 지원 언어를 지원
  const studySupportedLanguages = SUPPORTED_LANGUAGES
  
  // 모든 지원 언어에 대해 제목 설정
  studySupportedLanguages.forEach(lang => {
    studyData[`title_${lang}`] = getExamTitle(lang)
  })
  
  // 스터디 목표 설정 (Exam 설명을 그대로 복사하지 않고, 공유 목적을 명시)
  // Study 모델은 goal_ko와 goal_en만 지원하므로, 프로필 언어에 따라 적절히 설정
  const getStudyGoal = (lang) => {
    const examTitle = getExamTitle(lang)
    debugLog(`[getStudyGoal] lang=${lang}, examTitle=${examTitle}`)
    
    let goal
    if (lang === 'ko') {
      goal = `"${examTitle}" 시험을 공유하기 위해 생성된 스터디입니다.`
    } else if (lang === 'en') {
      goal = `Study created to share the exam "${examTitle}".`
    } else if (lang === 'es') {
      goal = `Estudio creado para compartir el examen "${examTitle}".`
    } else if (lang === 'zh') {
      goal = `为分享考试"${examTitle}"而创建的学习小组。`
    } else if (lang === 'ja') {
      goal = `試験"${examTitle}"を共有するために作成されたスタディです。`
    } else {
      // 기본 언어는 'en'
      goal = `Study created to share the exam "${examTitle}".`
    }
    
    debugLog(`[getStudyGoal] 결과: ${goal}`)
    return goal
  }
  
  debugLog('[스터디 goal 설정 시작]', { currentLang, exam: { title_ko: exam.title_ko, title_en: exam.title_en, display_title: exam.display_title } })
  
  // Study 모델은 5개 언어를 모두 지원: ['ko', 'en', 'es', 'zh', 'ja']
  // 모든 지원 언어에 대해 goal 설정
  studySupportedLanguages.forEach(lang => {
    studyData[`goal_${lang}`] = getStudyGoal(lang)
  })
  
  debugLog('[스터디 goal 설정 완료]', {
    goal_ko: studyData.goal_ko,
    goal_en: studyData.goal_en,
    currentLang
  })
  
  debugLog('스터디 제목 설정:', {
    title_ko: studyData.title_ko,
    title_en: studyData.title_en,
    exam_title_ko: exam.title_ko,
    exam_title_en: exam.title_en,
    exam_display_title: exam.display_title,
    exam_title: exam.title
  })
  
  // 시험의 태그를 스터디에 복사
  if (exam.tags && Array.isArray(exam.tags) && exam.tags.length > 0) {
    studyData.tags = exam.tags.map(tag => typeof tag === 'object' ? tag.id : tag)
    debugLog('시험 태그를 스터디에 복사:', studyData.tags)
  }
  
  debugLog('[스터디 생성 요청 데이터]', {
    is_public: studyData.is_public,
    title_ko: studyData.title_ko,
    title_en: studyData.title_en,
    goal_ko: studyData.goal_ko,
    goal_en: studyData.goal_en,
    tags: studyData.tags
  })
  
  const studyResponse = await axios.post('/api/studies/', studyData)
  const study = studyResponse.data
  
  debugLog('[스터디 생성 응답 데이터]', {
    id: study.id,
    title_ko: study.title_ko,
    title_en: study.title_en,
    goal_ko: study.goal_ko,
    goal_en: study.goal_en
  })
  
  // Task 생성
  const taskData = {
    study: study.id,
    exam: exam.id,
    is_public: false, // 비공개 Task
    progress: 0
  }
  
  // 프로필 언어에 따라 Task 이름 설정 (시험 이름과 동일)
  // StudyTask 모델은 모든 지원 언어를 지원
  const taskSupportedLanguages = SUPPORTED_LANGUAGES
  
  // 모든 지원 언어에 대해 Task 이름 설정
  taskSupportedLanguages.forEach(lang => {
    taskData[`name_${lang}`] = getExamTitle(lang)
  })
  
  debugLog('Task 이름 설정:', {
    currentLang,
    name_ko: taskData.name_ko,
    name_en: taskData.name_en,
    exam_title_ko: exam.title_ko,
    exam_title_en: exam.title_en,
    exam_display_title: exam.display_title,
    exam_title: exam.title
  })
  
  debugLog('Task 생성 시작:', taskData)
  const taskResponse = await axios.post(`/api/studies/${study.id}/add_task/`, taskData)
  debugLog('Task 생성 성공:', taskResponse.data)
  
  return study
}

/**
 * 단축 URL 생성 및 클립보드 복사
 * @param {Object} context - Vue 컴포넌트 컨텍스트 (this)
 * @param {string} url - 공유할 URL
 * @param {Function} onSuccess - 성공 시 콜백 (메시지 표시용)
 * @param {Function} onError - 실패 시 콜백 (에러 메시지 표시용)
 */
export async function createShortUrlAndCopy(context, url, onSuccess, onError) {
  try {
    // 단축 URL 생성
    const response = await axios.post('/api/short-url/create/', {
      url: url,
      expires_days: 30
    })
    
    const shortUrl = response.data.short_url
    
    // 클립보드에 단축 URL 복사
    await navigator.clipboard.writeText(shortUrl)
    
    if (onSuccess) {
      onSuccess(shortUrl)
    }
    
    debugLog('공유 단축 URL:', shortUrl)
  } catch (shortUrlError) {
    console.error('단축 URL 생성 실패:', shortUrlError)
    // 단축 URL 생성에 실패하면 원본 URL 사용
    try {
      await navigator.clipboard.writeText(url)
      if (onSuccess) {
        onSuccess(url)
      }
    } catch (copyError) {
      // 폴백: 기존 방식으로 복사
      fallbackCopyToClipboard(url, onSuccess, onError)
    }
    
    debugLog('공유 URL (원본):', url)
  }
}

/**
 * 클립보드 복사 폴백 함수
 * @param {string} text - 복사할 텍스트
 * @param {Function} onSuccess - 성공 시 콜백
 * @param {Function} onError - 실패 시 콜백
 */
function fallbackCopyToClipboard(text, onSuccess, onError) {
  const textArea = document.createElement('textarea')
  textArea.value = text
  textArea.style.position = 'fixed'
  textArea.style.left = '-999999px'
  textArea.style.top = '-999999px'
  document.body.appendChild(textArea)
  textArea.focus()
  textArea.select()
  
  try {
    document.execCommand('copy')
    if (onSuccess) {
      onSuccess(text)
    }
  } catch (err) {
    debugLog('Fallback 복사 실패:', err, 'error')
    if (onError) {
      onError(err)
    }
  } finally {
    if (document.body.contains(textArea)) {
      document.body.removeChild(textArea)
    }
  }
}

/**
 * 시험 공유 메인 함수
 * @param {Object} context - Vue 컴포넌트 컨텍스트 (this)
 * @param {Object} exam - 시험 객체
 * @param {Function} getShareUrl - 공유할 URL을 생성하는 함수 (context를 받아서 URL 반환)
 * @param {Function} showConfirmModal - 확인 모달을 표시하는 함수
 * @param {Function} showSuccessMessage - 성공 메시지를 표시하는 함수
 * @param {Function} showErrorMessage - 에러 메시지를 표시하는 함수
 * @param {string} currentLang - 현재 언어 ('ko', 'en', 'es', 'zh', 'ja'), 기본값은 'en'
 */
export async function shareExam(
  context,
  exam,
  getShareUrl,
  showConfirmModal,
  showSuccessMessage,
  showErrorMessage,
  currentLang = 'en'
) {
  try {
    // 비공개 시험인지 확인
    if (exam && !exam.is_public) {
      // 연결된 스터디 목록 가져오기
      try {
        const connectedStudiesResponse = await axios.get(`/api/exam/${exam.id}/connected-studies/`)
        const connectedStudies = connectedStudiesResponse.data?.connected_studies || []
        
        debugLog('연결된 스터디 목록:', connectedStudies)
        
        // 연결된 스터디가 있는 경우
        if (connectedStudies.length > 0) {
          // 각 스터디의 상세 정보를 가져와서 관리자 권한 확인
          let hasAdminPermission = false
          
          for (const connectedStudy of connectedStudies) {
            try {
              const studyDetailResponse = await axios.get(`/api/studies/${connectedStudy.study_id}/`)
              const study = studyDetailResponse.data
              
              // 스터디에 members 정보가 있는지 확인
              if (study && study.members) {
                // 관리자 권한 확인
                if (hasStudySpecificAdminPermission(study)) {
                  hasAdminPermission = true
                  break
                }
              }
            } catch (studyError) {
              debugLog(`스터디 ${connectedStudy.study_id} 상세 정보 로드 실패:`, studyError, 'error')
              // 스터디 상세 정보 로드 실패는 무시하고 계속 진행
            }
          }
          
          // 관리자 권한이 없으면 권한 없음 메시지 표시
          if (!hasAdminPermission) {
            const noPermissionMessage = context.$t('examDetail.alerts.noSharePermission')
            showErrorMessage(noPermissionMessage)
            return
          }
          
          // 관리자 권한이 있으면 바로 공유 진행 (스터디 생성 모달 표시 안 함)
          const shareUrl = getShareUrl(context)
          await createShortUrlAndCopy(
            context,
            shareUrl,
            () => {
              showSuccessMessage(context.$t('examDetail.urlCopied') || context.$t('takeExam.linkCopied'))
            },
            () => {
              showErrorMessage(context.$t('examDetail.urlCopyFailed') || context.$t('takeExam.copyFailed'))
            }
          )
          return
        }
      } catch (connectedStudiesError) {
        debugLog('연결된 스터디 목록 로드 실패:', connectedStudiesError, 'error')
        // 연결된 스터디 목록 로드 실패는 무시하고 계속 진행 (스터디 생성 모달 표시)
      }
      
      // 연결된 스터디가 없는 경우 스터디 생성 확인 모달 표시
      const confirmTitle = context.$t('examDetail.alerts.studyCreationTitle') || '스터디 생성'
      const confirmMessage = context.$t('examDetail.alerts.privateExamShareRequiresStudy')
      
      showConfirmModal(
        confirmTitle,
        confirmMessage,
        async (confirmed) => {
          if (confirmed) {
            try {
              // 스터디와 Task 생성
              await createStudyAndTaskForSharing(context, exam, currentLang)
              
              // 단축 URL 생성 및 복사
              const shareUrl = getShareUrl(context)
              await createShortUrlAndCopy(
                context,
                shareUrl,
                () => {
                  const successMessage = context.$t('examDetail.shareStudyCreated') || 
                    '스터디와 Task가 생성되었고 링크가 복사되었습니다.'
                  showSuccessMessage(successMessage)
                },
                () => {
                  showErrorMessage(context.$t('examDetail.urlCopyFailed'))
                }
              )
            } catch (error) {
              debugLog('스터디/Task 생성 실패:', error, 'error')
              if (error.response?.status === 400 && error.response?.data?.error) {
                showErrorMessage(error.response.data.error)
              } else if (error.response?.data?.study) {
                // 스터디는 생성되었지만 Task 생성 실패
                showErrorMessage(context.$t('examDetail.alerts.taskCreationFailed'))
              } else {
                showErrorMessage(context.$t('examDetail.alerts.studyCreationFailed'))
              }
            }
          }
        },
        'info'
      )
      return
    }
    
    // 공개 시험인 경우 단축 URL 생성 및 복사
    const shareUrl = getShareUrl(context)
    await createShortUrlAndCopy(
      context,
      shareUrl,
      () => {
        showSuccessMessage(context.$t('examDetail.urlCopied') || context.$t('takeExam.linkCopied'))
      },
      () => {
        showErrorMessage(context.$t('examDetail.urlCopyFailed') || context.$t('takeExam.copyFailed'))
      }
    )
  } catch (error) {
    debugLog('URL 공유 실패:', error, 'error')
    showErrorMessage(context.$t('examDetail.urlCopyFailed') || context.$t('takeExam.copyFailed'))
  }
}

