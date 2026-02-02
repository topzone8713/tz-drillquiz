/**
 * 플랫폼 감지 유틸리티 함수들
 */

/**
 * 웹뷰 환경 감지 (웹 환경에서는 항상 false 반환)
 * @returns {boolean} 웹 환경에서는 항상 false
 */
export const isWebView = () => {
  // 웹 환경에서는 웹뷰가 아님
  return false
}
