/**
 * 도메인 관련 유틸리티 함수들
 */

// 도메인별 설정
const DOMAIN_CONFIGS = {
  devops: {
    keyword: 'devops',
    tagName: 'DevOps',
    storageKey: 'devops_tag_id',
    localStorageKey: 'devops_default_tags',
    localStorageSetKey: 'devops_default_tags_set',
    categoryName: 'IT 기술', // "IT 기술 > IT 기술" 카테고리 이름
    categoryStorageKey: 'devops_category_id'
  },
  leetcode: {
    keyword: 'leetcode',
    tagName: 'LeetCode',
    storageKey: 'leetcode_tag_id',
    localStorageKey: 'leetcode_default_tags',
    localStorageSetKey: 'leetcode_default_tags_set'
  },
  // 새로운 도메인 추가 예시
  // python: {
  //   keyword: 'python',
  //   tagName: 'Python',
  //   storageKey: 'python_tag_id',
  //   localStorageKey: 'python_default_tags',
  //   localStorageSetKey: 'python_default_tags_set'
  // }
}

/**
 * 현재 도메인이 특정 키워드를 포함하는지 확인
 * @param {string} keyword 확인할 키워드
 * @returns {boolean} 도메인 포함 여부
 */
export function isDomainContains(keyword) {
  const hostname = window.location.hostname
  return hostname.includes(keyword)
}


/**
 * 현재 도메인에 해당하는 설정을 반환
 * @returns {Object|null} 도메인 설정 또는 null
 */
export function getCurrentDomainConfig() {
  for (const [key, config] of Object.entries(DOMAIN_CONFIGS)) {
    if (isDomainContains(config.keyword)) {
      return { key, ...config }
    }
  }
  return null
}

/**
 * sessionStorage에서 태그 ID를 가져오기 (범용)
 * @param {string} storageKey storage 키
 * @returns {number|null} 태그 ID 또는 null
 */
export function getTagIdFromStorage(storageKey) {
  try {
    const stored = sessionStorage.getItem(storageKey)
    return stored ? parseInt(stored, 10) : null
  } catch (error) {
    console.warn(`sessionStorage에서 ${storageKey}를 읽을 수 없습니다:`, error)
    return null
  }
}

/**
 * sessionStorage에 태그 ID 저장 (범용)
 * @param {string} storageKey storage 키
 * @param {number} tagId 태그 ID
 */
export function setTagIdToStorage(storageKey, tagId) {
  try {
    sessionStorage.setItem(storageKey, tagId.toString())
  } catch (error) {
    console.warn(`sessionStorage에 ${storageKey}를 저장할 수 없습니다:`, error)
  }
}


/**
 * 기본 태그 ID를 반환 (범용)
 * @param {Object} config 도메인 설정
 * @param {Array} availableTags 사용 가능한 태그 목록 (fallback용)
 * @returns {number|null} 태그 ID 또는 null
 */
export function getDefaultTagId(config, availableTags = []) {
  if (!isDomainContains(config.keyword)) {
    return null
  }
  
  // 먼저 sessionStorage에서 확인
  let tagId = getTagIdFromStorage(config.storageKey)
  
  // sessionStorage에 없으면 태그 목록에서 찾기 (fallback)
  if (!tagId && availableTags.length > 0) {
    // 모든 지원 언어 필드를 확인하도록 수정
    const tag = availableTags.find(t => {
      // 모든 지원 언어 필드 확인 (ko, en, es, zh, ja)
      const supportedLanguages = ['ko', 'en', 'es', 'zh', 'ja']
      for (const lang of supportedLanguages) {
        if (t[`name_${lang}`] === config.tagName) {
          return true
        }
      }
      // localized_name도 확인
      return t.localized_name === config.tagName
    })
    
    if (tag) {
      tagId = tag.id
      // 찾은 태그 ID를 sessionStorage에 저장
      setTagIdToStorage(config.storageKey, tagId)
    }
  }
  
  return tagId
}

/**
 * 강제로 적용할 태그 ID 목록을 반환 (범용)
 * @param {Object} config 도메인 설정
 * @param {Array} availableTags 사용 가능한 태그 목록
 * @returns {number[]} 태그 ID 배열
 */
export function getForcedTags(config, availableTags = []) {
  if (!isDomainContains(config.keyword)) {
    return []
  }
  
  const tagId = getDefaultTagId(config, availableTags)
  return tagId ? [tagId] : []
}


/**
 * 기본 태그를 포함한 태그 필터를 반환 (범용)
 * @param {Object} config 도메인 설정
 * @param {number[]} userSelectedTags 사용자가 선택한 태그들
 * @param {Array} availableTags 사용 가능한 태그 목록
 * @returns {number[]} 강제 적용된 태그들
 */
export function applyTagFilter(config, userSelectedTags = [], availableTags = []) {
  if (!isDomainContains(config.keyword)) {
    return userSelectedTags
  }
  
  const forcedTags = getForcedTags(config, availableTags)
  const result = [...forcedTags]
  
  // 사용자가 선택한 태그 중 강제 태그와 중복되지 않는 것들만 추가
  userSelectedTags.forEach(tagId => {
    if (!result.includes(tagId)) {
      result.push(tagId)
    }
  })
  
  return result
}




// ===== 범용 함수들 (새로운 도메인 추가 시 사용) =====

/**
 * 현재 도메인에 대한 모든 태그 관련 작업을 처리하는 범용 함수
 * @param {Array} availableTags 사용 가능한 태그 목록
 * @returns {Object} 태그 관련 정보
 */
export function getCurrentDomainTagInfo(availableTags = []) {
  const config = getCurrentDomainConfig()
  if (!config) {
    return {
      isDomainSpecific: false,
      forcedTags: [],
      tagId: null,
      config: null
    }
  }

  const tagId = getDefaultTagId(config, availableTags)
  const forcedTags = getForcedTags(config, availableTags)

  return {
    isDomainSpecific: true,
    forcedTags,
    tagId,
    config,
    isTagRequired: (tagIdToCheck) => tagIdToCheck === tagId
  }
}

/**
 * 현재 도메인에 대한 태그 필터를 적용
 * @param {number[]} userSelectedTags 사용자가 선택한 태그들
 * @param {Array} availableTags 사용 가능한 태그 목록
 * @returns {number[]} 강제 적용된 태그들
 */
export function applyCurrentDomainTagFilter(userSelectedTags = [], availableTags = []) {
  const config = getCurrentDomainConfig()
  if (!config) {
    return userSelectedTags
  }
  return applyTagFilter(config, userSelectedTags, availableTags)
}

// ===== DevOps 도메인 전용 함수들 =====

/**
 * 현재 도메인이 DevOps 도메인인지 확인
 * @returns {boolean} DevOps 도메인 여부
 */
export function isDevOpsDomain() {
  return isDomainContains('devops')
}

/**
 * DevOps 도메인에서 필터링을 강제해야 하는지 확인
 * @returns {boolean} 필터링 강제 여부
 */
export function shouldForceDevOpsFilter() {
  return isDevOpsDomain()
}

/**
 * "IT 기술 > IT 기술" 카테고리 ID를 가져오기
 * @param {Array} availableCategories 사용 가능한 카테고리 목록 (트리 구조)
 * @returns {number|null} 카테고리 ID 또는 null
 */
export function getDevOpsCategoryId(availableCategories = []) {
  if (!isDevOpsDomain()) {
    return null
  }
  
  // sessionStorage에서 먼저 확인
  const stored = getTagIdFromStorage('devops_category_id')
  if (stored) {
    return stored
  }
  
  // 카테고리 트리에서 찾기
  const findCategory = (categories) => {
    for (const category of categories) {
      // 1단계 "IT 기술" 카테고리 찾기
      if (category.level === 1 && category.name_ko === 'IT 기술') {
        // 2단계 "IT 기술" 카테고리 찾기 (order=6)
        if (category.children && Array.isArray(category.children)) {
          for (const child of category.children) {
            if (child.level === 2 && 
                child.name_ko === 'IT 기술' && 
                child.order === 6) {
              return child.id
            }
          }
        }
      }
      
      // 재귀적으로 자식 카테고리 검색
      if (category.children && Array.isArray(category.children)) {
        const found = findCategory(category.children)
        if (found) {
          return found
        }
      }
    }
    return null
  }
  
  const categoryId = findCategory(availableCategories)
  if (categoryId) {
    setTagIdToStorage('devops_category_id', categoryId)
  }
  
  return categoryId
}

/**
 * "IT 기술 > IT 기술" 카테고리의 태그들만 필터링
 * @param {Array} availableTags 사용 가능한 태그 목록
 * @param {number} categoryId 카테고리 ID
 * @returns {Array} 필터링된 태그 목록
 */
export function getDevOpsCategoryTags(availableTags = [], categoryId = null) {
  if (!isDevOpsDomain()) {
    return availableTags
  }
  
  if (!categoryId) {
    return []
  }
  
  // 태그 목록에서 해당 카테고리에 속한 태그만 필터링
  return availableTags.filter(tag => {
    if (!tag.categories || !Array.isArray(tag.categories)) {
      return false
    }
    
    // 태그의 categories가 배열인 경우 (ID 배열)
    if (typeof tag.categories[0] === 'number') {
      return tag.categories.includes(categoryId)
    }
    
    // 태그의 categories가 객체 배열인 경우
    return tag.categories.some(cat => 
      (typeof cat === 'object' && cat.id === categoryId) || 
      cat === categoryId
    )
  })
}

/**
 * DevOps 도메인에서 사용 가능한 태그 ID 목록 반환
 * @param {Array} availableTags 사용 가능한 태그 목록
 * @param {number} categoryId 카테고리 ID
 * @returns {number[]} 태그 ID 배열
 */
export function getDevOpsCategoryTagIds(availableTags = [], categoryId = null) {
  const filteredTags = getDevOpsCategoryTags(availableTags, categoryId)
  return filteredTags.map(tag => tag.id).filter(id => id != null)
}

/**
 * DevOps 도메인에서 "DrillQuiz"를 "DrillQuiz DevOps"로 변환
 * @param {string} text 원본 텍스트
 * @returns {string} 변환된 텍스트
 */
export function replaceDrillQuizName(text) {
  if (!text || typeof text !== 'string') {
    return text
  }
  
  if (isDevOpsDomain()) {
    // "DrillQuiz"를 "DrillQuiz DevOps"로 변환 (단, 이미 "DrillQuiz DevOps"인 경우는 제외)
    return text.replace(/DrillQuiz(?!\s+DevOps)/g, 'DrillQuiz DevOps')
  }
  
  return text
}

