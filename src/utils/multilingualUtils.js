/**
 * 프론트엔드 다국어 처리를 위한 유틸리티 함수들
 * 
 * 이 모듈은 Vue.js 컴포넌트에서 다국어 콘텐츠를 일관되게 처리하기 위한
 * 공통 기능들을 제공합니다.
 * 
 * 주요 기능:
 * 1. 다국어 필드에서 현재 사용자 언어에 맞는 값 추출
 * 2. 폴백 로직 처리 (한국어 → 영어 → 기본값)
 * 3. 다국어 필드 유효성 검사
 * 4. 다국어 콘텐츠 메타데이터 생성
 * 
 * 사용 예시:
 * ```javascript
 * import { getLocalizedContent, validateMultilingualFields, SUPPORTED_LANGUAGES } from '@/utils/multilingualUtils'
 * 
 * // 현재 언어에 맞는 콘텐츠 가져오기
 * const title = getLocalizedContent(item, 'title', 'ko')
 * 
 * // 다국어 필드 유효성 검사
 * const isValid = validateMultilingualFields(item, ['title', 'goal'])
 * 
 * // 모든 지원 언어 순회
 * for (const lang of SUPPORTED_LANGUAGES) {
 *   console.log(lang)
 * }
 * ```
 * 
 * 작성일: 2025-08-17
 * 작성자: AI Assistant
 */

// 지원하는 모든 언어 코드 (백엔드와 동일)
export const SUPPORTED_LANGUAGES = ['ko', 'en', 'es', 'zh', 'ja']

/**
 * 현재 사용자 언어를 가져옵니다.
 * i18n 인스턴스가 없으면 기본값 'en'을 반환합니다.
 * 
 * @param {Object} i18n - Vue i18n 인스턴스
 * @returns {string} 현재 언어 코드 ('ko', 'en', 'es', 'zh', 'ja'), 기본값은 'en'
 */
export function getCurrentLanguage(i18n) {
  if (!i18n || !i18n.locale) {
    return 'en'; // 기본 언어는 'en'
  }
  return i18n.locale;
}

/**
 * 다국어 필드에서 현재 사용자 언어에 맞는 값을 추출합니다.
 * Study Title과 동일한 방식으로 동작:
 * - 한국어 사용자: ko 필드 우선, 없으면 en 필드, 둘 다 없으면 기본 필드
 * - 영어 사용자: en 필드 우선, 없으면 ko 필드, 둘 다 없으면 기본 필드
 * 
 * @param {Object} item - 다국어 필드를 가진 객체
 * @param {string} fieldName - 기본 필드명 (예: 'title', 'name', 'goal')
 * @param {string} currentLanguage - 현재 사용자 언어
 * @param {string} fallbackValue - 모든 필드가 없을 때 반환할 기본값
 * @returns {string} 현재 언어에 맞는 콘텐츠
 * 
 * @example
 * // 한국어 사용자의 경우
 * const title = getLocalizedContent(study, 'title', 'ko', '제목 없음')
 * // study.title_ko가 있으면 study.title_ko 반환
 * // 없고 study.title_en이 있으면 study.title_en 반환
 * // 둘 다 없으면 study.title 반환
 * // 모든 것이 없으면 '제목 없음' 반환
 */
export function getLocalizedContent(item, fieldName, currentLanguage, fallbackValue = '') {
  if (!item || !fieldName) {
    return fallbackValue;
  }
  
  const koField = `${fieldName}_ko`;
  const enField = `${fieldName}_en`;
  const esField = `${fieldName}_es`;
  const zhField = `${fieldName}_zh`;
  const jaField = `${fieldName}_ja`;
  const defaultField = fieldName;
  
  if (currentLanguage === 'ko') {
    // 한국어 사용자: 한국어 필드 우선, 없으면 영어 필드, 없으면 스페인어 필드, 없으면 중국어 필드, 없으면 일본어 필드, 둘 다 없으면 기본 필드
    return item[koField] || item[enField] || item[esField] || item[zhField] || item[jaField] || item[defaultField] || fallbackValue;
  } else if (currentLanguage === 'en') {
    // 영어 사용자: 영어 필드 우선, 없으면 한국어 필드, 없으면 스페인어 필드, 없으면 중국어 필드, 없으면 일본어 필드, 둘 다 없으면 기본 필드
    return item[enField] || item[koField] || item[esField] || item[zhField] || item[jaField] || item[defaultField] || fallbackValue;
  } else if (currentLanguage === 'es') {
    // 스페인어 사용자: 스페인어 필드 우선, 없으면 영어 필드, 없으면 한국어 필드, 없으면 중국어 필드, 없으면 일본어 필드, 둘 다 없으면 기본 필드
    return item[esField] || item[enField] || item[koField] || item[zhField] || item[jaField] || item[defaultField] || fallbackValue;
  } else if (currentLanguage === 'zh') {
    // 중국어 사용자: 중국어 필드 우선, 없으면 영어 필드, 없으면 한국어 필드, 없으면 스페인어 필드, 없으면 일본어 필드, 둘 다 없으면 기본 필드
    return item[zhField] || item[enField] || item[koField] || item[esField] || item[jaField] || item[defaultField] || fallbackValue;
  } else if (currentLanguage === 'ja') {
    // 일본어 사용자: 일본어 필드 우선, 없으면 영어 필드, 없으면 한국어 필드, 없으면 스페인어 필드, 없으면 중국어 필드, 둘 다 없으면 기본 필드
    return item[jaField] || item[enField] || item[koField] || item[esField] || item[zhField] || item[defaultField] || fallbackValue;
  } else {
    // 기본: 영어 필드 우선
    return item[enField] || item[koField] || item[esField] || item[zhField] || item[jaField] || item[defaultField] || fallbackValue;
  }
}

/**
 * i18n 인스턴스를 사용하여 다국어 필드에서 현재 사용자 언어에 맞는 값을 추출합니다.
 * 사용자 프로필 언어를 우선하고, 없으면 i18n locale을 사용하며, 기본값은 'en'입니다.
 * 
 * @param {Object} item - 다국어 필드를 가진 객체
 * @param {string} fieldName - 기본 필드명 (예: 'title', 'name', 'goal')
 * @param {Object} i18n - Vue i18n 인스턴스 (선택사항)
 * @param {string} userProfileLanguage - 사용자 프로필 언어 (선택사항, 우선순위가 높음)
 * @param {string} fallbackValue - 모든 필드가 없을 때 반환할 기본값
 * @returns {string} 현재 언어에 맞는 콘텐츠
 * 
 * @example
 * // Vue 컴포넌트에서 사용
 * import { getLocalizedContentWithI18n } from '@/utils/multilingualUtils'
 * 
 * // 템플릿에서
 * {{ getLocalizedContentWithI18n(study, 'title', $i18n, userProfileLanguage, '제목 없음') }}
 * 
 * // 메서드에서
 * const title = getLocalizedContentWithI18n(study, 'title', this.$i18n, this.userProfileLanguage, '제목 없음')
 */
export function getLocalizedContentWithI18n(item, fieldName, i18n = null, userProfileLanguage = null, fallbackValue = '') {
  if (!item || !fieldName) {
    return fallbackValue;
  }
  
  // 사용자 프로필 언어 우선, 없으면 i18n locale, 없으면 'en' 기본값
  let currentLanguage = 'en'; // 기본 언어는 'en'
  
  if (userProfileLanguage) {
    currentLanguage = userProfileLanguage;
  } else if (i18n && i18n.locale) {
    currentLanguage = i18n.locale;
  }
  
  return getLocalizedContent(item, fieldName, currentLanguage, fallbackValue);
}

/**
 * 태그나 다른 다국어 객체에서 특정 이름과 일치하는지 확인합니다.
 * 모든 지원 언어 필드를 확인합니다.
 * 
 * @param {Object} item - 다국어 필드를 가진 객체 (예: tag)
 * @param {string} fieldName - 기본 필드명 (예: 'name')
 * @param {string} searchValue - 찾고자 하는 값
 * @returns {boolean} 일치 여부
 * 
 * @example
 * const tag = { name_ko: 'DevOps', name_en: 'DevOps', name_es: 'DevOps' }
 * const matches = matchesMultilingualName(tag, 'name', 'DevOps')
 * // true
 */
export function matchesMultilingualName(item, fieldName, searchValue) {
  if (!item || !fieldName || !searchValue) {
    return false
  }
  
  // 모든 지원 언어 필드 확인
  for (const lang of SUPPORTED_LANGUAGES) {
    const field = `${fieldName}_${lang}`
    if (item[field] === searchValue) {
      return true
    }
  }
  
  // localized_name도 확인 (백엔드에서 제공하는 경우)
  if (item.localized_name === searchValue) {
    return true
  }
  
  return false
}

/**
 * 다국어 필드의 사용 가능한 언어 목록을 생성합니다.
 * 
 * @param {Object} item - 다국어 필드를 가진 객체
 * @param {string} fieldName - 기본 필드명
 * @returns {Array<string>} 사용 가능한 언어 코드 배열
 * 
 * @example
 * const languages = getAvailableLanguages(study, 'title')
 * // SUPPORTED_LANGUAGES 또는 ['ko'] 또는 ['en'] 또는 ['es'] 또는 ['zh'] 또는 ['ja'] 또는 []
 */
export function getAvailableLanguages(item, fieldName) {
  if (!item || !fieldName) {
    return [];
  }
  
  const languages = [];
  const koField = `${fieldName}_ko`;
  const enField = `${fieldName}_en`;
  const esField = `${fieldName}_es`;
  const zhField = `${fieldName}_zh`;
  const jaField = `${fieldName}_ja`;
  
  if (item[koField]) {
    languages.push('ko');
  }
  if (item[enField]) {
    languages.push('en');
  }
  if (item[esField]) {
    languages.push('es');
  }
  if (item[zhField]) {
    languages.push('zh');
  }
  if (item[jaField]) {
    languages.push('ja');
  }
  
  return languages;
}

/**
 * 다국어 필드의 유효성을 검사합니다.
 * 최소한 하나의 언어로 콘텐츠가 입력되었는지 확인합니다.
 * 
 * @param {Object} item - 다국어 필드를 가진 객체
 * @param {string} fieldName - 기본 필드명
 * @returns {boolean} 유효성 여부
 * 
 * @example
 * const isValid = validateMultilingualFields(study, 'title')
 * // title_ko 또는 title_en 중 하나라도 있으면 true
 */
export function validateMultilingualFields(item, fieldName) {
  if (!item || !fieldName) {
    return false;
  }
  
  const koField = `${fieldName}_ko`;
  const enField = `${fieldName}_en`;
  const esField = `${fieldName}_es`;
  const zhField = `${fieldName}_zh`;
  const jaField = `${fieldName}_ja`;
  
  return !!(item[koField] || item[enField] || item[esField] || item[zhField] || item[jaField]);
}

/**
 * 다국어 필드의 완성도 상태를 확인합니다.
 * 각 언어별로 콘텐츠가 완성되었는지 확인합니다.
 * 
 * @param {Object} item - 다국어 필드를 가진 객체
 * @param {string} fieldName - 기본 필드명
 * @returns {Object} 언어별 완성도 상태
 * 
 * @example
 * const completion = getMultilingualCompletion(study, 'title')
 * // { ko: true, en: false } - 한국어는 완성, 영어는 미완성
 */
export function getMultilingualCompletion(item, fieldName) {
  if (!item || !fieldName) {
    return { ko: false, en: false, es: false, zh: false, ja: false };
  }
  
  const koField = `${fieldName}_ko`;
  const enField = `${fieldName}_en`;
  const esField = `${fieldName}_es`;
  const zhField = `${fieldName}_zh`;
  const jaField = `${fieldName}_ja`;
  
  return {
    ko: !!item[koField],
    en: !!item[enField],
    es: !!item[esField],
    zh: !!item[zhField],
    ja: !!item[jaField]
  };
}

/**
 * 다국어 콘텐츠의 메타데이터를 생성합니다.
 * 현재 언어, 사용 가능한 언어, 완성도 상태 등을 포함합니다.
 * 
 * @param {Object} item - 다국어 필드를 가진 객체
 * @param {string} fieldName - 기본 필드명
 * @param {string} currentLanguage - 현재 사용자 언어
 * @returns {Object} 다국어 콘텐츠 메타데이터
 * 
 * @example
 * const metadata = getMultilingualMetadata(study, 'title', 'ko')
 * // {
 * //   current_language: 'ko',
 * //   available_languages: ['ko', 'en', 'es', 'zh'],
 * //   localized_value: '스터디 제목',
 * //   completion: { ko: true, en: false }
 * // }
 */
export function getMultilingualMetadata(item, fieldName, currentLanguage) {
  if (!item || !fieldName) {
    return {
      current_language: currentLanguage,
      available_languages: [],
      localized_value: '',
      completion: { ko: false, en: false, es: false, zh: false, ja: false }
    };
  }
  
  const availableLanguages = getAvailableLanguages(item, fieldName);
  const completion = getMultilingualCompletion(item, fieldName);
  const localizedValue = getLocalizedContent(item, fieldName, currentLanguage);
  
  return {
    current_language: currentLanguage,
    available_languages: availableLanguages,
    localized_value: localizedValue,
    completion: completion
  };
}

/**
 * 다국어 필드 편집을 위한 초기 데이터를 생성합니다.
 * 현재 사용자 언어에 맞는 필드만 설정합니다.
 * 
 * @param {Object} item - 기존 객체 (편집 시)
 * @param {string} fieldName - 기본 필드명
 * @param {string} currentLanguage - 현재 사용자 언어
 * @returns {Object} 편집용 초기 데이터
 * 
 * @example
 * const editData = createMultilingualEditData(task, 'name', 'ko')
 * // { name_ko: '기존 한국어 이름', name_en: '' }
 */
export function createMultilingualEditData(item, fieldName, currentLanguage) {
  if (!fieldName) {
    return {};
  }
  
  // 기본 언어는 'en'
  const targetLanguage = SUPPORTED_LANGUAGES.includes(currentLanguage) ? currentLanguage : 'en';
  
  // 모든 언어 필드에 대해 빈 문자열로 초기화
  const result = {};
  SUPPORTED_LANGUAGES.forEach(lang => {
    const langField = `${fieldName}_${lang}`;
    // 현재 언어에 해당하는 필드만 기존 값으로 설정, 나머지는 빈 문자열
    result[langField] = (lang === targetLanguage && item) ? (item[langField] || '') : '';
  });
  
  return result;
}

/**
 * 다국어 필드의 변경 사항을 감지합니다.
 * 실제로 값이 변경되었는지 확인합니다.
 * 
 * @param {Object} original - 원본 객체
 * @param {Object} updated - 업데이트된 객체
 * @param {string} fieldName - 기본 필드명
 * @returns {boolean} 변경 여부
 * 
 * @example
 * const hasChanged = detectMultilingualChanges(originalTask, updatedTask, 'name')
 * // name_ko 또는 name_en이 변경되었으면 true
 */
export function detectMultilingualChanges(original, updated, fieldName) {
  if (!original || !updated || !fieldName) {
    return false;
  }
  
  const koField = `${fieldName}_ko`;
  const enField = `${fieldName}_en`;
  const esField = `${fieldName}_es`;
  const zhField = `${fieldName}_zh`;
  const jaField = `${fieldName}_ja`;
  
  return (
    original[koField] !== updated[koField] ||
    original[enField] !== updated[enField] ||
    original[esField] !== updated[esField] ||
    original[zhField] !== updated[zhField] ||
    original[jaField] !== updated[jaField]
  );
}

/**
 * 다국어 필드의 요약 정보를 생성합니다.
 * 여러 필드의 다국어 상태를 한 번에 확인할 수 있습니다.
 * 
 * @param {Object} item - 다국어 필드를 가진 객체
 * @param {Array<string>} fieldNames - 필드명 배열
 * @param {string} currentLanguage - 현재 사용자 언어
 * @returns {Object} 다국어 요약 정보
 * 
 * @example
 * const summary = getMultilingualSummary(study, ['title', 'goal'], 'ko')
 * // {
 * //   current_language: 'ko',
 * //   available_languages: ['ko', 'en', 'es', 'zh'],
 * //   fields: {
 * //     title: { localized_value: '제목', completion: { ko: true, en: false } },
 * //     goal: { localized_value: '목표', completion: { ko: true, en: true } }
 * //   }
 * // }
 */
export function getMultilingualSummary(item, fieldNames, currentLanguage) {
  if (!item || !fieldNames || !Array.isArray(fieldNames)) {
    return {
      current_language: currentLanguage,
      available_languages: [],
      fields: {}
    };
  }
  
  const summary = {
    current_language: currentLanguage,
    available_languages: [],
    fields: {}
  };
  
  // 모든 필드의 사용 가능한 언어 수집
  const allLanguages = new Set();
  
  fieldNames.forEach(fieldName => {
    const metadata = getMultilingualMetadata(item, fieldName, currentLanguage);
    summary.fields[fieldName] = metadata;
    
    // 사용 가능한 언어 추가
    metadata.available_languages.forEach(lang => allLanguages.add(lang));
  });
  
  summary.available_languages = Array.from(allLanguages);
  
  return summary;
}

/**
 * 언어 코드를 Speech Recognition/TTS용 BCP 47 형식으로 변환합니다.
 * 
 * @param {string} language - 언어 코드 ('ko', 'en', 'es', 'zh', 'ja')
 * @returns {string} BCP 47 형식의 언어 코드 (예: 'ko-KR', 'en-US')
 * 
 * @example
 * const sttLang = getLanguageCodeForSTT('ko') // 'ko-KR'
 * const sttLang = getLanguageCodeForSTT('en') // 'en-US'
 */
export function getLanguageCodeForSTT(language) {
  const langMap = {
    'ko': 'ko-KR',
    'en': 'en-US',
    'es': 'es-ES',
    'zh': 'zh-CN',
    'ja': 'ja-JP'
  }
  // 매핑된 언어가 있으면 사용, 없으면 'en-US' 기본값
  return langMap[language] || 'en-US'
}

/**
 * 날짜 포맷을 위한 locale 코드를 반환합니다.
 * 
 * @param {string} language - 언어 코드 ('ko', 'en', 'es', 'zh', 'ja')
 * @returns {string} locale 코드 (예: 'ko-KR', 'en-US')
 * 
 * @example
 * const locale = getLocaleForDateFormat('ko') // 'ko-KR'
 */
export function getLocaleForDateFormat(language) {
  return getLanguageCodeForSTT(language)
}

/**
 * 언어별 기본 fallback 값을 반환합니다.
 * 
 * @param {string} language - 언어 코드 ('ko', 'en', 'es', 'zh', 'ja')
 * @param {string} fieldType - 필드 타입 ('title', 'description', 'name', 'tag', 'goal')
 * @returns {string} 해당 언어의 fallback 값
 * 
 * @example
 * const fallback = getLocalizedFallback('ko', 'title') // '제목 없음'
 * const fallback = getLocalizedFallback('en', 'title') // 'No Title'
 * const fallback = getLocalizedFallback('es', 'description') // 'Sin Descripción'
 */
export function getLocalizedFallback(language, fieldType = 'title') {
  const fallbacks = {
    title: {
      ko: '제목 없음',
      en: 'No Title',
      es: 'Sin Título',
      zh: '无标题',
      ja: 'タイトルなし'
    },
    description: {
      ko: '설명 없음',
      en: 'No Description',
      es: 'Sin Descripción',
      zh: '无描述',
      ja: '説明なし'
    },
    name: {
      ko: '이름 없음',
      en: 'No Name',
      es: 'Sin Nombre',
      zh: '无名称',
      ja: '名前なし'
    },
    tag: {
      ko: '태그 없음',
      en: 'No Tag',
      es: 'Sin Etiqueta',
      zh: '无标签',
      ja: 'タグなし'
    },
    goal: {
      ko: '목표 없음',
      en: 'No Goal',
      es: 'Sin Objetivo',
      zh: '无目标',
      ja: '目標なし'
    }
  }
  
  const typeFallbacks = fallbacks[fieldType] || fallbacks.title
  return typeFallbacks[language] || typeFallbacks.en
}

export default {
  SUPPORTED_LANGUAGES,
  getCurrentLanguage,
  getLocalizedContent,
  getLocalizedContentWithI18n,
  matchesMultilingualName,
  getAvailableLanguages,
  validateMultilingualFields,
  getMultilingualCompletion,
  getMultilingualMetadata,
  createMultilingualEditData,
  detectMultilingualChanges,
  getMultilingualSummary,
  getLanguageCodeForSTT,
  getLocaleForDateFormat,
  getLocalizedFallback
};
