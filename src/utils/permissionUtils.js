/**
 * 권한 확인을 위한 Utility 함수들
 */
import authService from '@/services/authService'

/**
 * 사용자 정보를 가져옵니다.
 * @returns {Object|null} 사용자 정보 또는 null
 */
export function getCurrentUser() {
  return authService.getCachedUser()
}

/**
 * 사용자가 로그인되어 있는지 확인합니다.
 * @returns {boolean} 로그인 여부
 */
export function isAuthenticated() {
  return authService.isAuthenticatedSync()
}

/**
 * 사용자가 관리자 권한을 가지고 있는지 확인합니다.
 * @returns {boolean} 관리자 권한 여부
 */
export function isAdmin() {
  return authService.isAdminSync()
}

/**
 * 사용자가 전역 스터디 관리자 권한을 가지고 있는지 확인합니다.
 * @returns {boolean} 전역 스터디 관리자 권한 여부
 */
export function hasStudyAdminRole() {
  const user = getCurrentUser()
  if (!user) return false
  
  return user.has_study_admin_role === true
}

/**
 * 사용자가 특정 스터디 관리자 권한을 가지고 있는지 확인합니다.
 * @returns {boolean} 특정 스터디 관리자 권한 여부
 */
export function isStudyAdmin() {
  const user = getCurrentUser()
  if (!user) return false
  
  // 전역 스터디 관리자 권한 확인
  if (hasStudyAdminRole()) {
    return true
  }
  
  // 특정 스터디 관리자 권한은 hasStudySpecificAdminPermission 함수를 사용해야 함
  // 이 함수는 스터디 객체가 필요하므로 여기서는 false 반환
  return false
}

/**
 * 사용자가 관리자 또는 전역 스터디 관리자 권한을 가지고 있는지 확인합니다.
 * @returns {boolean} 관리자 또는 전역 스터디 관리자 권한 여부
 */
export function hasAnyAdminPermission() {
  return isAdmin() || hasStudyAdminRole()
}

/**
 * 사용자가 특정 스터디에 대한 관리자 권한을 가지고 있는지 확인합니다.
 * @param {Object} study - 스터디 객체
 * @returns {boolean} 특정 스터디 관리자 권한 여부
 */
export function hasStudySpecificAdminPermission(study) {
  if (!study || !study.members) return false
  
  const user = getCurrentUser()
  if (!user) return false
  
  // 전역 관리자 권한 확인
  if (isAdmin() || hasStudyAdminRole()) {
    return true
  }
  
  // 특정 스터디 관리자 권한 확인
  return study.members.some(member => {
    if (!member.user) return false
    
    const memberUserId = typeof member.user === 'object' ? member.user.id : member.user
    return memberUserId === user.id && 
           (member.role === 'study_admin' || member.role === 'study_leader') &&
           member.is_active === true
  })
}

/**
 * 사용자가 특정 시험을 편집할 수 있는 권한을 가지고 있는지 확인합니다.
 * @param {Object} exam - 시험 객체
 * @returns {boolean} 시험 편집 권한 여부
 */
export function canEditExam(exam) {
  if (!exam) return false
  
  const user = getCurrentUser()
  if (!user) return false
  
  // 시험 생성자는 항상 편집 권한이 있음 (백엔드 권한 정보보다 우선)
  // created_by가 객체인 경우와 ID인 경우 모두 처리
  if (exam.created_by) {
    const createdById = typeof exam.created_by === 'object' ? exam.created_by.id : exam.created_by
    const userId = user.id
    // 숫자로 변환하여 비교 (타입 불일치 방지)
    if (Number(createdById) === Number(userId)) {
      return true
    }
  }
  
  // 백엔드에서 제공하는 리소스별 권한 정보 확인
  if (exam.user_permissions) {
    return exam.user_permissions.is_admin || 
           exam.user_permissions.has_study_admin_role || 
           exam.user_permissions.is_study_admin
  }
  
  // 백엔드 권한 정보가 없는 경우에만 fallback
  // 전역 관리자 권한 확인
  if (isAdmin() || hasStudyAdminRole()) {
    return true
  }
  
  // 권한 정보가 없으면 기본적으로 false
  return false
}

/**
 * 사용자가 특정 스터디를 편집할 수 있는 권한을 가지고 있는지 확인합니다.
 * @param {Object} study - 스터디 객체
 * @returns {boolean} 스터디 편집 권한 여부
 */
export function canEditStudy(study) {
  if (!study) return false
  
  const user = getCurrentUser()
  if (!user) return false
  
  // 전역 관리자 권한 확인
  if (isAdmin() || hasStudyAdminRole()) {
    return true
  }
  
  // 스터디 생성자 확인
  if (study.created_by && study.created_by.id === user.id) {
    return true
  }
  
  // 스터디 관리자 권한 확인
  return hasStudySpecificAdminPermission(study)
}

/**
 * 사용자가 스터디 멤버인지 확인합니다.
 * @param {Object} study - 스터디 객체
 * @returns {boolean} 스터디 멤버 여부
 */
export function isStudyMember(study) {
  if (!study || !study.members) return false
  
  const user = getCurrentUser()
  if (!user) return false
  
  return study.members.some(member => {
    if (!member.user) return false
    
    const memberUserId = typeof member.user === 'object' ? member.user.id : member.user
    return memberUserId === user.id && member.is_active === true
  })
}

/**
 * 사용자가 스터디 멤버 관리 권한을 가지고 있는지 확인합니다.
 * admin, study_admin, study_leader만 멤버 관리 가능
 * @param {Object} study - 스터디 객체
 * @returns {boolean} 멤버 관리 권한 여부
 */
export function canManageStudyMembers(study) {
  if (!study || !study.members) return false
  
  const user = getCurrentUser()
  if (!user) return false
  
  // 전역 관리자 권한 확인
  if (isAdmin() || hasStudyAdminRole()) {
    return true
  }
  
  // 특정 스터디 관리자 권한 확인 (study_admin, study_leader)
  return study.members.some(member => {
    if (!member.user) return false
    
    const memberUserId = typeof member.user === 'object' ? member.user.id : member.user
    return memberUserId === user.id && 
           (member.role === 'study_admin' || member.role === 'study_leader')
  })
}

/**
 * 사용자의 모든 권한 정보를 반환합니다.
 * @returns {Object} 권한 정보 객체
 */
export function getUserPermissions() {
  const user = getCurrentUser()
  
  if (!user) {
    return {
      isAuthenticated: false,
      isAdmin: false,
      hasStudyAdminRole: false,
      isStudyAdmin: false,
      hasAnyAdminPermission: false
    }
  }
  
  return {
    isAuthenticated: true,
    isAdmin: isAdmin(),
    hasStudyAdminRole: hasStudyAdminRole(),
    isStudyAdmin: isStudyAdmin(),
    hasAnyAdminPermission: hasAnyAdminPermission()
  }
}

export function onAuthStateChange(handler) {
  return authService.subscribe(handler)
}

export function getAuthSnapshot() {
  return authService.getAuthSnapshot()
}
