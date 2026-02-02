/**
 * 텍스트 포맷팅 유틸리티 함수들
 */

/**
 * 텍스트를 HTML로 포맷팅 (줄바꿈과 URL 링크 처리)
 * @param {string} text - 포맷팅할 텍스트
 * @returns {string} 포맷팅된 HTML 문자열
 */
export function formatTextWithLinks(text) {
  if (!text) return ''
  
  // 줄바꿈을 <br> 태그로 변환
  let formatted = text.replace(/\n/g, '<br>')
  
  // URL을 링크로 변환 (더 정확한 URL 패턴)
  const urlRegex = /\b(https?:\/\/[^\s<>"{}|\\^`[\]]+|www\.[^\s<>"{}|\\^`[\]]+)\b/g
  formatted = formatted.replace(urlRegex, (url) => {
    let linkUrl = url
    let displayUrl = url
    
    // URL 끝에 문장 부호가 있으면 제거
    const punctuationMatch = url.match(/^(.+?)([.,;:!?]+)$/)
    if (punctuationMatch) {
      linkUrl = punctuationMatch[1]
      displayUrl = url // 원본 텍스트 유지
    }
    
    if (linkUrl.startsWith('www.')) {
      linkUrl = 'https://' + linkUrl
    }
    
    return `<a href="${linkUrl}" target="_blank" rel="noopener noreferrer" class="text-primary">${displayUrl}</a>`
  })
  
  return formatted
} 