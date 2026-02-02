/**
 * Google Analytics 추적을 위한 안전한 유틸리티 함수들
 */

// 운영 환경 확인
function isProduction() {
  const hostname = window.location.hostname;
  return hostname === 'drillquiz.com' || 
         hostname === 'us.drillquiz.com' || 
         hostname.endsWith('.drillquiz.com');
}

// Google Analytics가 사용 가능한지 확인
function isAnalyticsAvailable() {
  return isProduction() && window.gtag && typeof window.gtag === 'function';
}

/**
 * 안전한 Google Analytics 이벤트 전송
 * @param {string} eventName - 이벤트 이름
 * @param {object} parameters - 이벤트 파라미터
 */
export function trackEvent(eventName, parameters = {}) {
  if (!isAnalyticsAvailable()) {
    return;
  }
  
  try {
    window.gtag('event', eventName, {
      ...parameters,
      // 기본 파라미터 추가
      event_timeout: 2000,
      non_interaction: false
    });
  } catch (error) {
    console.warn('Google Analytics 이벤트 전송 실패:', error);
  }
}

/**
 * 페이지뷰 추적
 * @param {string} pageTitle - 페이지 제목
 * @param {string} pagePath - 페이지 경로
 */
export function trackPageView(pageTitle, pagePath = window.location.pathname) {
  if (!isAnalyticsAvailable()) {
    return;
  }
  
  try {
    window.gtag('event', 'page_view', {
      page_title: pageTitle,
      page_location: window.location.href,
      page_path: pagePath,
      page_referrer: document.referrer || ''
    });
  } catch (error) {
    console.warn('Google Analytics 페이지뷰 전송 실패:', error);
  }
}

/**
 * 사용자 로그인 추적
 * @param {string} method - 로그인 방법 (google, email 등)
 */
export function trackLogin(method) {
  trackEvent('login', {
    method: method,
    event_category: 'engagement',
    event_label: method
  });
}

/**
 * 퀴즈 시작 추적
 * @param {string} examId - 시험 ID
 * @param {string} examTitle - 시험 제목
 */
export function trackQuizStart(examId, examTitle) {
  trackEvent('quiz_start', {
    exam_id: examId,
    exam_title: examTitle,
    event_category: 'quiz',
    event_label: examTitle
  });
}

/**
 * 퀴즈 완료 추적
 * @param {string} examId - 시험 ID
 * @param {string} examTitle - 시험 제목
 * @param {number} score - 점수
 * @param {number} totalQuestions - 총 문제 수
 */
export function trackQuizComplete(examId, examTitle, score, totalQuestions) {
  trackEvent('quiz_complete', {
    exam_id: examId,
    exam_title: examTitle,
    score: score,
    total_questions: totalQuestions,
    event_category: 'quiz',
    event_label: examTitle
  });
}

/**
 * 오류 추적
 * @param {string} errorType - 오류 유형
 * @param {string} errorMessage - 오류 메시지
 */
export function trackError(errorType, errorMessage) {
  trackEvent('error', {
    error_type: errorType,
    error_message: errorMessage,
    event_category: 'error',
    non_interaction: true
  });
}

/**
 * 사용자 행동 추적
 * @param {string} action - 행동 유형
 * @param {string} category - 카테고리
 * @param {string} label - 라벨
 */
export function trackUserAction(action, category, label) {
  trackEvent(action, {
    event_category: category,
    event_label: label
  });
}
