<template>
  <div class="member-management-modern">
    <!-- 확인 모달 -->
    <div v-if="showConfirmModal" class="modal-overlay" @click="cancelAction">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h5 class="modal-title">
            <i :class="confirmModalData.type === 'danger' ? 'fas fa-exclamation-triangle text-danger' : 'fas fa-question-circle text-warning'"></i>
            {{ confirmModalData.title }}
          </h5>
          <button class="modal-close" @click="cancelAction">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <p class="mb-0">{{ confirmModalData.message }}</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="cancelAction">
            {{ confirmModalData.cancelText }}
          </button>
          <button class="btn" :class="`btn-${confirmModalData.type === 'danger' ? 'danger' : 'primary'}`" @click="confirmAction">
            <i class="fas fa-check me-1"></i>
            {{ confirmModalData.confirmText }}
          </button>
        </div>
      </div>
    </div>
    
    <div class="member-container">
      <!-- Top Header -->
      <div class="top-header">
        <div class="header-actions">
          <button 
            @click="toggleMemberForm" 
            class="action-btn action-btn-success"
            v-if="!showMemberForm"
          >
            <i class="fas fa-plus"></i>
            <span class="action-label">{{ $t('memberManagement.add') }}</span>
          </button>
        </div>
      </div>

      <!-- Page Title -->
      <div class="page-title">
        <h1>{{ study ? getStudyTitle(study) : '' }} - {{ $t('memberManagement.memberManagement') }}</h1>
      </div>
      
      <!-- 멤버 추가 폼 -->
      <div class="card-modern member-form-card" v-if="showMemberForm">
        <div class="card-header-modern">
          <h3>{{ $t('memberManagement.addMember') }}</h3>
          <div class="card-actions">
            <button @click="toggleMemberForm" class="card-action-btn">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>
        <div class="card-body">
        
        <!-- 사용자 검색 섹션 -->
        <div class="user-search-section mb-4">
          <div class="card-modern">
            <div class="card-header-modern">
              <h5 class="mb-0">
                <i class="fas fa-search me-2"></i>
                {{ userMappingTarget ? `${$t('memberManagement.userMapping')} - ${userMappingTarget.name}` : $t('memberManagement.registeredUserSearch') }}
              </h5>
            </div>
            <div class="card-body">
              <div class="row">
                <div class="col-md-6">
                  <div class="form-group">
                    <label>{{ userMappingTarget ? $t('memberManagement.connectedUserSearch') : $t('memberManagement.userSearch') }}</label>
                    <div class="input-group">
                      <input 
                        v-model="userSearchQuery" 
                        @input="searchUsers" 
                        type="text" 
                        class="form-control" 
                        :placeholder="$t('memberManagement.searchPlaceholder')"
                      >
                      <button 
                        @click="searchUsers" 
                        class="btn btn-outline-secondary" 
                        type="button"
                      >
                        <i class="fas fa-search"></i>
                      </button>
                    </div>
                  </div>
                </div>
                <div class="col-md-6" v-if="userMappingTarget">
                  <div class="d-flex align-items-end h-100">
                    <button @click="cancelUserMapping" class="btn btn-outline-secondary">
                      <i class="fas fa-times me-1"></i>{{ $t('memberManagement.cancel') }}
                    </button>
                  </div>
                </div>
              </div>
              
              <!-- 검색 결과 -->
              <div v-if="searchResults.length > 0" class="mt-3">
                <h6>{{ $t('memberManagement.searchUsers') }}:</h6>
                <div class="table-responsive">
                  <table class="table table-sm">
                    <thead>
                      <tr>
                        <th>{{ $t('memberManagement.username') }}</th>
                        <th>{{ $t('memberManagement.email') }}</th>
                        <th>{{ $t('memberManagement.name') }}</th>
                        <th>{{ $t('memberManagement.actions') }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="user in searchResults" :key="user.id">
                        <td>{{ user.username }}</td>
                        <td>{{ user.email }}</td>
                        <td>{{ user.first_name }} {{ user.last_name }}</td>
                        <td>
                          <button 
                            @click="userMappingTarget ? selectUserForMapping(user) : selectUser(user)" 
                            class="btn btn-sm btn-success"
                            :disabled="userMappingTarget ? false : isUserAlreadyMember(user.id)"
                          >
                            {{ userMappingTarget ? $t('memberManagement.connectToUser') : (isUserAlreadyMember(user.id) ? $t('memberManagement.alerts.alreadyMember') : $t('memberManagement.confirm')) }}
                          </button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
              
              <div v-else-if="userSearchQuery && !isSearching" class="mt-3">
                <div class="alert alert-info">
                  {{ $t('memberManagement.noUsersFound') }}
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 멤버 추가 폼 -->
        <div class="member-add-form">
          <div class="card-modern">
            <div class="card-header-modern">
              <h5 class="mb-0">
                <i class="fas fa-user-plus me-2"></i>
                {{ $t('memberManagement.addNewMember') }}
              </h5>
            </div>
            <div class="card-body">
              <form @submit.prevent="addMember" class="row" id="addMemberForm">
                <div class="col-md-3">
                  <div class="form-group">
                    <label>{{ $t('memberManagement.name') }} *</label>
                    <input v-model="newMember.name" type="text" class="form-control" required>
                  </div>
                </div>
                <div class="col-md-3">
                  <div class="form-group">
                    <label>{{ $t('memberManagement.email') }}</label>
                    <input v-model="newMember.email" type="email" class="form-control">
                  </div>
                </div>
                <div class="col-md-2">
                  <div class="form-group">
                    <label>{{ $t('memberManagement.memberId') }}</label>
                    <input v-model="newMember.member_id" type="text" class="form-control">
                  </div>
                </div>
                <div class="col-md-2">
                  <div class="form-group">
                    <label>{{ $t('memberManagement.affiliation') }}</label>
                    <input v-model="newMember.affiliation" type="text" class="form-control">
                  </div>
                </div>
                <div class="col-md-2">
                  <div class="form-group">
                    <label>{{ $t('memberManagement.location') }}</label>
                    <input v-model="newMember.location" type="text" class="form-control">
                  </div>
                </div>
              </form>
              <div class="row mt-3">
                <div class="col-12 text-end">
                  <button type="submit" form="addMemberForm" class="btn btn-primary btn-lg px-5">
                    <i class="fas fa-plus"></i>
                    <span>{{ $t('memberManagement.add') }}</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
        </div>
      </div>
      
      <!-- 멤버 가져오기 기능 -->
      <div class="card-modern member-import-card">
        <div class="card-header-modern">
          <h3>{{ $t('memberManagement.importMembers') }}</h3>
        </div>
        <div class="card-body">
          <div class="row align-items-center">
            <div class="col-md-4">
              <div class="form-group">
                <select v-model="selectedImportStudy" class="form-control">
                  <option value="">{{ $t('memberManagement.selectStudy') }}</option>
                  <option v-for="otherStudy in otherStudies" :key="otherStudy.id" :value="otherStudy.id">
                    {{ getStudyTitle(otherStudy) }} ({{ otherStudy.members ? otherStudy.members.length : 0 }})
                  </option>
                </select>
              </div>
            </div>
            <div class="col-md-4 d-flex justify-content-end">
              <button @click="importMembersFromStudy" class="action-btn action-btn-info" :disabled="!selectedImportStudy">
                <i class="fas fa-download"></i>
                <span class="action-label">{{ $t('memberManagement.import') }}</span>
              </button>
            </div>
            <div class="col-md-4 d-flex justify-content-end gap-2" v-if="study && study.members && study.members.length > 0">
              <button @click="activateSelectedMembers" class="action-btn action-btn-success" :disabled="selectedMembers.length === 0">
                <i class="fas fa-check"></i>
                <span class="action-label">{{ $t('memberManagement.activate') }}</span>
              </button>
              <button @click="deactivateSelectedMembers" class="action-btn action-btn-warning" :disabled="selectedMembers.length === 0">
                <i class="fas fa-pause"></i>
                <span class="action-label">{{ $t('memberManagement.deactivate') }}</span>
              </button>
              <button @click="deleteSelectedMembers" class="action-btn action-btn-danger" :disabled="selectedMembers.length === 0">
                <i class="fas fa-trash"></i>
                <span class="action-label">{{ $t('memberManagement.delete') }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 멤버 목록 -->
      <div class="card-modern member-table-card">
        <div class="card-header-modern">
          <h3>{{ $t('memberManagement.memberList') }}</h3>
        </div>
        <div class="card-body">
          <div v-if="study && study.members && study.members.length === 0" class="alert alert-info">
            {{ $t('memberManagement.noMembers') }}
          </div>
          <div v-else-if="study && study.members" class="table-responsive">
            <table class="table table-striped">
            <thead>
              <tr>
                <th>
                  <input type="checkbox" @change="toggleAllMembers" :checked="isAllSelected" :indeterminate="isIndeterminate">
                </th>
                <th>{{ $t('memberManagement.name') }}</th>
                <th>{{ $t('memberManagement.username') }}</th>
                <th>{{ $t('memberManagement.email') }}</th>
                <th>{{ $t('memberManagement.memberId') }}</th>
                <th>{{ $t('memberManagement.affiliation') }}</th>
                <th>{{ $t('memberManagement.location') }}</th>
                <th>{{ $t('memberManagement.role') }}</th>
                <th>{{ $t('memberManagement.status') }}</th>
                <th>{{ $t('memberManagement.actions') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="member in (study?.members || []).filter(Boolean)" :key="member.id">
                <td>
                  <input type="checkbox" :value="member.id" v-model="selectedMembers">
                </td>
                <td>
                  <div v-if="editingMember !== member.id">
                    <strong>{{ member.name }}</strong>
                  </div>
                  <div v-else>
                    <input v-model="editingMemberData.name" type="text" class="form-control" required>
                  </div>
                </td>
                <td>
                  <div v-if="editingMember !== member.id">
                    <span v-if="member.user_username" class="badge bg-primary">{{ member.user_username }}</span>
                    <span v-else class="text-muted">{{ $t('memberManagement.noConnectedUser') }}</span>
                    <button v-if="!member.user" @click="openUserMapping(member)" class="btn btn-sm btn-outline-success ms-2">{{ $t('memberManagement.connectUser') }}</button>
                  </div>
                  <div v-else>
                    <span class="text-muted">{{ $t('memberManagement.cancel') }}</span>
                  </div>
                </td>
                <td>
                  <div v-if="editingMember !== member.id">
                    {{ member.email || $t('memberManagement.noEmail') }}
                  </div>
                  <div v-else>
                    <input v-model="editingMemberData.email" type="email" class="form-control">
                  </div>
                </td>
                <td>
                  <div v-if="editingMember !== member.id">
                    {{ member.member_id || $t('memberManagement.noId') }}
                  </div>
                  <div v-else>
                    <input v-model="editingMemberData.member_id" type="text" class="form-control">
                  </div>
                </td>
                <td>
                  <div v-if="editingMember !== member.id">
                    {{ member.affiliation || $t('memberManagement.noAffiliation') }}
                  </div>
                  <div v-else>
                    <input v-model="editingMemberData.affiliation" type="text" class="form-control">
                  </div>
                </td>
                <td>
                  <div v-if="editingMember !== member.id">
                    {{ member.location || $t('memberManagement.noLocation') }}
                  </div>
                  <div v-else>
                    <input v-model="editingMemberData.location" type="text" class="form-control">
                  </div>
                </td>
                <td>
                  <div v-if="editingMember !== member.id">
                    <span class="badge" :class="getRoleBadgeClass(member.role)">
                      {{ getRoleDisplayName(member.role) }}
                    </span>
                  </div>
                  <div v-else>
                    <select v-model="editingMemberData.role" class="form-control">
                      <option value="member">{{ $t('memberManagement.member') }}</option>
                      <option value="study_admin">{{ $t('memberManagement.studyAdmin') }}</option>
                      <option value="study_leader">{{ $t('memberManagement.studyLeader') }}</option>
                    </select>
                  </div>
                </td>
                <td>
                  <div v-if="editingMember !== member.id">
                    <span class="badge" :class="member.is_active ? 'bg-success' : 'bg-danger'">
                      {{ member.is_active ? $t('memberManagement.active') : $t('memberManagement.inactive') }}
                    </span>
                  </div>
                  <div v-else>
                    <select v-model="editingMemberData.is_active" class="form-control">
                      <option :value="true">{{ $t('memberManagement.active') }}</option>
                      <option :value="false">{{ $t('memberManagement.inactive') }}</option>
                    </select>
                  </div>
                </td>
                <td>
                  <div v-if="editingMember !== member.id">
                    <button @click="startEditMember(member)" class="btn btn-sm btn-secondary me-1">{{ $t('memberManagement.edit') }}</button>
                    <button @click="deleteMember(member.id)" class="btn btn-sm btn-danger">{{ $t('memberManagement.delete') }}</button>
                  </div>
                  <div v-else>
                    <button @click="saveMemberEdit(member.id)" class="btn btn-sm btn-success me-1">{{ $t('memberManagement.confirm') }}</button>
                    <button @click="cancelEditMember" class="btn btn-sm btn-secondary">{{ $t('memberManagement.cancel') }}</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        </div>
      </div>
      
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { debugLog } from '@/utils/debugUtils'
import { isAdmin, hasStudyAdminRole } from '@/utils/permissionUtils'
import { getLocalizedContent, getCurrentLanguage } from '@/utils/multilingualUtils'

export default {
  name: 'MemberManagement',
  data() {
    return {
      study: null,
      editingMember: null,
      editingMemberData: {
        name: '',
        email: '',
        member_id: '',
        affiliation: '',
        location: '',
        role: 'member',
        is_active: true
      },
      newMember: {
        name: '',
        email: '',
        member_id: '',
        affiliation: '',
        location: '',
        role: 'member',
        is_active: true
      },
      selectedMembers: [],
      selectedImportStudy: '',
      otherStudies: [],
      showMemberForm: false,
      userSearchQuery: '',
      searchResults: [],
      isSearching: false,
      userMappingTarget: null,
      // 확인 모달 관련 데이터
      showConfirmModal: false,
      confirmModalData: {
        title: '',
        message: '',
        confirmText: '',
        cancelText: '',
        confirmCallback: null,
        type: 'warning' // warning, danger, info
      },
    }
  },
  computed: {
    isAllSelected() {
      if (!this.study || !this.study.members) return false
      return this.study.members.length > 0 && this.selectedMembers.length === this.study.members.length
    },
    isIndeterminate() {
      if (!this.study || !this.study.members) return false
      return this.selectedMembers.length > 0 && this.selectedMembers.length < this.study.members.length
    },
    isAdmin() {
      return isAdmin()
    },
    isStudyAdmin() {
      return hasStudyAdminRole()
    }
  },
  async created() {
    const studyId = this.$route.params.studyId
    if (studyId) {
      await this.loadStudy(studyId)
    }
    await this.loadOtherStudies()
  },
  methods: {
    // 현재 사용자 언어에 맞는 스터디 제목 반환
    getStudyTitle(study) {
      if (!study) return '';
      
      const currentLanguage = getCurrentLanguage(this.$i18n);
      const fallbackValue = currentLanguage === 'ko' ? '제목 없음' : 'No Title';
      return getLocalizedContent(study, 'title', currentLanguage, fallbackValue);
    },
    
    showToastNotification(message, type = 'success', icon = null) {
      // 토스트 알림 생성 - 공통 CSS 사용
      const toast = document.createElement('div')
      const typeClassMap = {
        success: 'alert-success',
        error: 'alert-error',
        warning: 'alert-warning',
        info: 'alert-info'
      }
      toast.className = `toast-notification ${typeClassMap[type] || 'alert-success'}`
      
      // 공통 CSS를 사용하므로 인라인 스타일 최소화 (애니메이션용 transform만)
      toast.style.transform = 'translateX(100%)'
      toast.style.transition = 'transform 0.3s ease'
      
      // 아이콘 추가
      const iconMap = {
        success: '✓',
        error: '✗',
        warning: '⚠',
        info: 'ℹ'
      }
      
      const iconElement = icon || iconMap[type] || ''
      toast.innerHTML = `<div class="toast-content">${iconElement} ${message}</div>`
      
      document.body.appendChild(toast)
      
      // 애니메이션 시작
      setTimeout(() => {
        toast.style.transform = 'translateX(0)'
      }, 100)
      
      // 자동 제거
      setTimeout(() => {
        toast.style.transform = 'translateX(100%)'
        setTimeout(() => {
          if (document.body.contains(toast)) {
            document.body.removeChild(toast)
          }
        }, 300)
      }, 3000)
    },
    
    async loadStudy(studyId) {
      try {
        const response = await axios.get(`/api/studies/${studyId}/`)
        this.study = response.data
      } catch (error) {
        debugLog('스터디 로드 실패:', error, 'error')
        this.showToastNotification(this.$t('memberManagement.alerts.loadStudyFailed'), 'error')
      }
    },
    async loadOtherStudies() {
      try {
        const response = await axios.get('/api/studies/')
        
        // API 응답이 {count, results} 형태인지 확인
        let studiesData
        if (response.data && response.data.results) {
          studiesData = response.data.results
        } else {
          studiesData = response.data
        }
        
        this.otherStudies = studiesData.filter(s => s.id !== this.study?.id)
      } catch (error) {
        debugLog('다른 스터디 로드 실패:', error, 'error')
        this.showToastNotification(this.$t('memberManagement.alerts.loadOtherStudiesFailed'), 'error')
      }
    },
    startEditMember(member) {
      this.editingMember = member.id
      this.editingMemberData = {
        name: member.name,
        email: member.email || '',
        member_id: member.member_id || '',
        affiliation: member.affiliation || '',
        location: member.location || '',
        role: member.role || 'member', // 기존 권한 유지
        is_active: member.is_active || true // 기존 활성화 상태 유지
      }
    },
    async saveMemberEdit(memberId) {
      try {
        const memberData = { ...this.editingMemberData };
        memberData.study = this.study.id;
        memberData.user = this.editingMemberData.user || null;
        await axios.put(`/api/members/${memberId}/`, memberData);
        this.editingMember = null;
        this.editingMemberData = { name: '', email: '', member_id: '', affiliation: '', location: '', role: 'member', is_active: true };
        await this.loadStudy(this.study.id);
      } catch (error) {
        debugLog('멤버 수정 실패:', error, 'error');
        this.showToastNotification(this.$t('memberManagement.alerts.updateMemberFailed'), 'error');
      }
    },
    cancelEditMember() {
      this.editingMember = null
      this.editingMemberData = { name: '', email: '', member_id: '', affiliation: '', location: '', role: 'member', is_active: true }
    },
    toggleMemberForm() {
      this.showMemberForm = !this.showMemberForm
      if (!this.showMemberForm) {
        this.resetMemberForm()
      }
    },
    resetMemberForm() {
      this.newMember = { name: '', email: '', member_id: '', affiliation: '', location: '', role: 'member', is_active: true }
      this.userSearchQuery = ''
      this.searchResults = []
    },
    
    // 확인 모달 표시 메서드
    openConfirmModal(title, message, confirmText = this.$t('memberManagement.confirm'), cancelText = this.$t('memberManagement.cancel'), type = 'warning', callback = null) {
      this.confirmModalData = {
        title,
        message,
        confirmText,
        cancelText,
        confirmCallback: callback,
        type
      }
      this.showConfirmModal = true
    },
    
    // 확인 모달 확인 버튼 클릭
    confirmAction() {
      if (this.confirmModalData.confirmCallback) {
        this.confirmModalData.confirmCallback()
      }
      this.showConfirmModal = false
    },
    
    // 확인 모달 취소 버튼 클릭
    cancelAction() {
      this.showConfirmModal = false
    },
    
    async addMember() {
      try {
        const memberData = { ...this.newMember }
        if (memberData.email === '') {
          memberData.email = null
        }
        if (memberData.member_id === '') {
          memberData.member_id = null
        }
        if (memberData.affiliation === '') {
          memberData.affiliation = null
        }
        if (memberData.location === '') {
          memberData.location = null
        }
        
        await axios.post(`/api/members/`, {
          ...memberData,
          study: this.study.id
        })
        this.resetMemberForm()
        this.showMemberForm = false
        await this.loadStudy(this.study.id)
      } catch (error) {
        debugLog('멤버 추가 실패:', error, 'error')
        debugLog('에러 응답:', error.response?.data, 'error')
        
        let errorMessage = this.$t('memberManagement.alerts.addMemberFailed')
        if (error.response?.data) {
          if (error.response.data.email) {
            errorMessage = this.$t('memberManagement.alerts.emailAlreadyExists')
          } else if (error.response.data.detail) {
            errorMessage = error.response.data.detail
          } else if (typeof error.response.data === 'string') {
            errorMessage = error.response.data
          }
        }
        
        this.showToastNotification(errorMessage, 'error')
      }
    },
    async deleteMember(memberId) {
      const member = this.study.members.find(m => m.id === memberId)
              const memberName = member ? member.name : this.$t('memberManagement.member')
      
      this.openConfirmModal(
                  this.$t('memberManagement.deleteMember'),
        this.$t('memberManagement.confirmDeleteMember', { name: memberName }),
        this.$t('confirm.delete'),
        this.$t('confirm.cancel'),
        'danger',
        async () => {
          try {
            await axios.delete(`/api/members/${memberId}/`)
            await this.loadStudy(this.study.id)
          } catch (error) {
            debugLog('멤버 삭제 실패:', error, 'error')
            this.showToastNotification(this.$t('memberManagement.alerts.deleteMemberFailed'), 'error')
          }
        }
      )
    },
    toggleAllMembers() {
      if (this.isAllSelected) {
        this.selectedMembers = []
      } else {
        if (this.study && this.study.members) {
          this.selectedMembers = this.study.members.map(member => member.id)
        }
      }
    },
    async deleteSelectedMembers() {
      if (this.selectedMembers.length === 0) {
        this.showToastNotification(this.$t('memberManagement.alerts.selectMemberToDelete'), 'warning')
        return
      }
      
      this.openConfirmModal(
                  this.$t('memberManagement.deleteSelectedMembers'),
        this.$t('memberManagement.confirmDeleteSelectedMembers', { count: this.selectedMembers.length }),
        this.$t('confirm.delete'),
        this.$t('confirm.cancel'),
        'danger',
        async () => {
          try {
            for (const memberId of this.selectedMembers) {
              try {
                await axios.delete(`/api/members/${memberId}/`)
              } catch (error) {
                debugLog(`멤버 ${memberId} 삭제 실패:`, error, 'error')
              }
            }
            
            await this.loadStudy(this.study.id)
            this.selectedMembers = []
            this.showToastNotification(this.$t('memberManagement.deleteSelectedMembersSuccess', { count: this.selectedMembers.length }), 'success')
            
          } catch (error) {
            debugLog('멤버 일괄 삭제 실패:', error, 'error')
            this.showToastNotification(this.$t('memberManagement.alerts.deleteMemberFailed'), 'error')
          }
        }
      )
    },
    async activateSelectedMembers() {
      if (this.selectedMembers.length === 0) {
        this.showToastNotification(this.$t('memberManagement.alerts.selectMemberToActivate'), 'warning')
        return
      }
      
      this.openConfirmModal(
                  this.$t('memberManagement.activateSelectedMembers'),
        this.$t('memberManagement.confirmActivateSelectedMembers', { count: this.selectedMembers.length }),
        this.$t('confirm.activate'),
        this.$t('confirm.cancel'),
        'warning',
        async () => {
          try {
            let successCount = 0
            let errorCount = 0
            
            for (const memberId of this.selectedMembers) {
              try {
                // 현재 멤버 정보 가져오기
                const member = this.study.members.find(m => m.id === memberId)
                if (!member) continue
                
                // 활성화 상태로 업데이트
                const updateData = {
                  study: this.study.id,
                  name: member.name,
                  email: member.email,
                  member_id: member.member_id,
                  affiliation: member.affiliation,
                  location: member.location,
                  role: member.role,
                  is_active: true,
                  user: member.user
                }
                
                await axios.put(`/api/members/${memberId}/`, updateData)
                successCount++
              } catch (error) {
                debugLog(`멤버 ${memberId} 활성화 실패:`, error, 'error')
                errorCount++
              }
            }
            
            await this.loadStudy(this.study.id)
            this.selectedMembers = []
            
            if (successCount > 0) {
              this.showToastNotification(`${successCount}개의 멤버가 활성화되었습니다.${errorCount > 0 ? ` (${errorCount}개 실패)` : ''}`, 'success')
            } else {
              this.showToastNotification(this.$t('memberManagement.alerts.noMemberToActivate'), 'warning')
            }
            
          } catch (error) {
            debugLog('멤버 일괄 활성화 실패:', error, 'error')
            this.showToastNotification(this.$t('memberManagement.alerts.activateMemberFailed'), 'error')
          }
        }
      )
    },
    async deactivateSelectedMembers() {
      if (this.selectedMembers.length === 0) {
        this.showToastNotification(this.$t('memberManagement.alerts.selectMemberToDeactivate'), 'warning')
        return
      }
      
      this.openConfirmModal(
                  this.$t('memberManagement.deactivateSelectedMembers'),
        this.$t('memberManagement.confirmDeactivateSelectedMembers', { count: this.selectedMembers.length }),
        this.$t('confirm.deactivate'),
        this.$t('confirm.cancel'),
        'warning',
        async () => {
          try {
            let successCount = 0
            let errorCount = 0
            
            for (const memberId of this.selectedMembers) {
              try {
                // 현재 멤버 정보 가져오기
                const member = this.study.members.find(m => m.id === memberId)
                if (!member) continue
                
                // 비활성화 상태로 업데이트
                const updateData = {
                  study: this.study.id,
                  name: member.name,
                  email: member.email,
                  member_id: member.member_id,
                  affiliation: member.affiliation,
                  location: member.location,
                  role: member.role,
                  is_active: false,
                  user: member.user
                }
                
                await axios.put(`/api/members/${memberId}/`, updateData)
                successCount++
              } catch (error) {
                debugLog(`멤버 ${memberId} 비활성화 실패:`, error, 'error')
                errorCount++
              }
            }
            
            await this.loadStudy(this.study.id)
            this.selectedMembers = []
            
            if (successCount > 0) {
              this.showToastNotification(`${successCount}개의 멤버가 비활성화되었습니다.${errorCount > 0 ? ` (${errorCount}개 실패)` : ''}`, 'success')
            } else {
              this.showToastNotification(this.$t('memberManagement.alerts.noMemberToDeactivate'), 'warning')
            }
            
          } catch (error) {
            debugLog('멤버 일괄 비활성화 실패:', error, 'error')
            this.showToastNotification(this.$t('memberManagement.alerts.deactivateMemberFailed'), 'error')
          }
        }
      )
    },
    async importMembersFromStudy() {
      if (!this.selectedImportStudy) {
        this.showToastNotification(this.$t('memberManagement.alerts.selectStudyToImport'), 'warning')
        return
      }

      try {
        const response = await axios.get(`/api/studies/${this.selectedImportStudy}/members/`)
        const importedMembers = response.data
        
        if (importedMembers.length === 0) {
          this.showToastNotification(this.$t('memberManagement.alerts.noMemberToImport'), 'warning')
          return
        }

        let successCount = 0
        let errorCount = 0

        for (const member of importedMembers) {
          try {
            // 기존 멤버와 중복되지 않는지 확인
            const existingMember = this.study.members?.find(m => 
              m.email === member.email || m.member_id === member.member_id
            )
            
            if (existingMember) {
              debugLog(`멤버 ${member.name}은 이미 존재합니다.`)
              continue
            }

            await axios.post(`/api/members/`, {
              name: member.name,
              email: member.email,
              member_id: member.member_id,
              affiliation: member.affiliation,
              location: member.location,
              role: member.role || 'member',
              is_active: member.is_active !== undefined ? member.is_active : true,
              study: this.study.id
            })
            successCount++
          } catch (error) {
            debugLog(`멤버 ${member.name} 가져오기 실패:`, error, 'error')
            errorCount++
          }
        }
        
        if (successCount > 0) {
          this.showToastNotification(`${successCount}개의 멤버가 성공적으로 가져와졌습니다.${errorCount > 0 ? ` (${errorCount}개 실패)` : ''}`, 'success')
          await this.loadStudy(this.study.id)
        } else {
          this.showToastNotification(this.$t('memberManagement.alerts.noMemberToImportAvailable'), 'warning')
        }
        
        this.selectedImportStudy = ''
      } catch (error) {
        debugLog('멤버 가져오기 실패:', error, 'error')
        this.showToastNotification(this.$t('memberManagement.alerts.importMemberFailed'), 'error')
      }
    },
    
    // 사용자 검색 관련 메서드들
    async searchUsers() {
      if (!this.userSearchQuery.trim()) {
        this.searchResults = []
        return
      }
      
      this.isSearching = true
      try {
        const response = await axios.get(`/api/search-users/?q=${encodeURIComponent(this.userSearchQuery.trim())}`)
        this.searchResults = response.data.users || []
      } catch (error) {
        debugLog('사용자 검색 실패:', error, 'error')
        this.searchResults = []
      } finally {
        this.isSearching = false
      }
    },
    
    isUserAlreadyMember(userId) {
      if (!this.study || !this.study.members) return false
      return this.study.members.some(member => member.user === userId)
    },
    
    // isEmailAlreadyMember 함수 및 관련 코드 전체 삭제
    
    async selectUser(user) {
      if (this.isUserAlreadyMember(user.id)) {
        this.showToastNotification(this.$t('memberManagement.alerts.alreadyMember'), 'warning')
        return
      }
      // isEmailAlreadyMember 관련 코드 삭제
      try {
        const memberData = {
          study: this.study.id,
          user: user.id,
          name: user.first_name && user.last_name ? `${user.first_name} ${user.last_name}` : user.username,
          email: user.email,
          member_id: '',
          affiliation: '',
          location: '',
          role: 'member',
          is_active: true
        }
        await axios.post(`/api/members/`, memberData)
        this.searchResults = []
        this.userSearchQuery = ''
        await this.loadStudy(this.study.id)
        this.showToastNotification(this.$t('memberManagement.memberAddedSuccess', { username: user.username }), 'success')
      } catch (error) {
        debugLog('사용자 멤버 추가 실패:', error, 'error')
        let errorMessage = this.$t('memberManagement.alerts.addUserFailed')
        if (error.response?.data) {
          if (error.response.data.non_field_errors) {
            errorMessage = this.$t('memberManagement.alerts.alreadyMember')
          } else if (error.response.data.detail) {
            errorMessage = error.response.data.detail
          } else if (typeof error.response.data === 'string') {
            errorMessage = error.response.data
          }
        }
        this.showToastNotification(errorMessage, 'error')
      }
    },
    openUserMapping(member) {
      this.userMappingTarget = member
      this.userSearchQuery = ''
      this.searchResults = []
      this.showMemberForm = true  // 멤버 추가 영역 표시
    },
    cancelUserMapping() {
      this.userMappingTarget = null
      this.userSearchQuery = ''
      this.searchResults = []
      this.showMemberForm = false  // 멤버 추가 영역 숨김
    },
    async selectUserForMapping(user) {
      if (!this.userMappingTarget) return
      try {
        // PUT 요청에 read_only 필드(user_username, user_email 등) 포함하지 않음
        const requestData = { 
          user: user.id,
          study: this.study.id,
          name: this.userMappingTarget.name,
          email: this.userMappingTarget.email,
          member_id: this.userMappingTarget.member_id,
          affiliation: this.userMappingTarget.affiliation,
          location: this.userMappingTarget.location,
          role: this.userMappingTarget.role, // 권한 포함
          is_active: this.userMappingTarget.is_active // 활성화 상태 포함
        }
        const requestUrl = `/api/members/${this.userMappingTarget.id}/`
        
        // CSRF 토큰 처리
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                         document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1]
        const config = {
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
          }
        }
        
        debugLog('사용자 연결 요청 URL:', requestUrl)
        debugLog('사용자 연결 요청 데이터:', requestData)

        const response = await axios.put(requestUrl, requestData, config)
        debugLog('사용자 연결 성공:', response.data)

        this.userMappingTarget = null
        this.userSearchQuery = ''
        this.searchResults = []
        this.showMemberForm = false
        await this.loadStudy(this.study.id)
        this.showToastNotification(this.$t('memberManagement.userConnectedSuccess', { username: user.username }), 'success')
      } catch (error) {
        debugLog('사용자 연결 실패:', error, 'error')
        debugLog('오류 응답:', error.response?.data, 'error')
        let errorMessage = this.$t('memberManagement.alerts.connectUserFailed')
        if (error.response?.data) {
          if (error.response.data.detail) {
            errorMessage = error.response.data.detail
          } else if (typeof error.response.data === 'string') {
            errorMessage = error.response.data
          }
        }
        this.showToastNotification(errorMessage, 'error')
      }
    },
    getRoleBadgeClass(role) {
      switch (role) {
        case 'study_admin':
          return 'bg-info'
        case 'study_leader':
          return 'bg-warning'
        default:
          return 'bg-secondary'
      }
    },
    getRoleDisplayName(role) {
      switch (role) {
        case 'study_admin':
          return this.$t('memberManagement.studyAdmin')
        case 'study_leader':
          return this.$t('memberManagement.studyLeader')
        default:
          return this.$t('memberManagement.member')
      }
    }
  }
}
</script>

<style scoped>
/* Modern Member Management Styles */
.member-management-modern {
  min-height: 100vh;
  background: #f8f9fa;
}

.member-container {
  max-width: 1400px;
  margin: 0 auto;
  background: white;
  min-height: 100vh;
}

/* Top Header */
.top-header {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 20px 30px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: flex-end;
}

/* Page Title */
.page-title {
  padding: 30px;
  background: white;
  border-bottom: 1px solid #e9ecef;
}

.page-title h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  color: #2c3e50;
}

/* Card Styles */
.card-modern {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  margin: 20px;
  overflow: hidden;
  border: 1px solid #e9ecef;
}

.card-header-modern {
  background: #f8f9fa;
  padding: 20px 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #dee2e6;
}

.card-header-modern h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #2c3e50;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.card-action-btn {
  background: none;
  border: none;
  color: #6c757d;
  font-size: 18px;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.card-action-btn:hover {
  background: #e9ecef;
  color: #495057;
}

.card-body {
  padding: 30px;
}

/* Action Button Styles */
.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: 2px solid #e9ecef;
  border-radius: 25px;
  background: white;
  color: #6c757d;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.action-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn-success {
  border-color: #28a745;
  background: #28a745;
  color: white;
}

.action-btn-success:hover:not(:disabled) {
  background: #218838;
  border-color: #1e7e34;
}

.action-btn-info {
  border-color: #17a2b8;
  background: #17a2b8;
  color: white;
}

.action-btn-info:hover:not(:disabled) {
  background: #138496;
  border-color: #117a8b;
}

.action-btn-warning {
  border-color: #ffc107;
  background: #ffc107;
  color: #212529;
}

.action-btn-warning:hover:not(:disabled) {
  background: #e0a800;
  border-color: #d39e00;
}

.action-btn-danger {
  border-color: #dc3545;
  background: #dc3545;
  color: white;
}

.action-btn-danger:hover:not(:disabled) {
  background: #c82333;
  border-color: #bd2130;
}

.action-label {
  font-weight: 500;
}

/* Form Styles */
.form-group {
  margin-bottom: 20px;
}

.form-group label {
  font-weight: 600;
  margin-bottom: 8px;
  display: block;
  color: #495057;
  font-size: 14px;
}

.form-control {
  border-radius: 12px;
  border: 2px solid #e9ecef;
  padding: 12px 16px;
  font-size: 14px;
  transition: all 0.3s ease;
}

.form-control:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
}

/* Table Styles */
.table {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.table th {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  font-weight: 600;
  color: #495057;
  border: none;
  padding: 16px 12px;
}

.table td {
  padding: 16px 12px;
  border-bottom: 1px solid #f8f9fa;
  vertical-align: middle;
}

.table tbody tr:hover {
  background: #f8f9fa;
}

/* Badge Styles */
.badge {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

/* Alert Styles */
.alert {
  border-radius: 12px;
  border: none;
  padding: 16px 20px;
  margin: 20px 0;
  font-weight: 500;
}

.alert-info {
  background: linear-gradient(135deg, #17a2b8 0%, #20c997 100%);
  color: white;
}

.alert-success {
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  color: white;
}

.alert-warning {
  background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%);
  color: #212529;
}

.alert-danger {
  background: linear-gradient(135deg, #dc3545 0%, #e83e8c 100%);
  color: white;
}

/* Button Styles */
.btn {
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

.btn-outline-primary {
  border-color: #007bff;
  color: #007bff;
  background: white;
}

.btn-outline-primary:hover {
  background: #007bff;
  color: white;
}

.btn-outline-warning {
  border-color: #ffc107;
  color: #ffc107;
  background: white;
}

.btn-outline-warning:hover {
  background: #ffc107;
  color: #212529;
}

.btn-danger {
  border-color: #dc3545;
  background: #dc3545;
  color: white;
}

.btn-danger:hover {
  background: #c82333;
  border-color: #bd2130;
}

/* "추가" 버튼 컨테이너 우측 정렬 (기본) */
.col-12.text-end {
  display: flex;
  justify-content: flex-end;
  text-align: right;
}

/* Responsive Design */
@media (max-width: 768px) {
  .member-container {
    margin: 0;
    border-radius: 0;
  }
  
  .card-modern,
  .member-import-card,
  .member-table-card,
  .member-form-card,
  .table-responsive {
    margin: 10px;
    /* padding: 20px; */
  }
  
  .card-modern {
    margin: 0px;
    padding-left: 0px;
    padding-right: 0px;
  }
  
  .page-title h1 {
    font-size: 2rem;
  }
  
  .card-header-modern {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }
  
  .card-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  /* "추가" 버튼 컨테이너 우측 정렬 */
  .col-12.text-end {
    display: flex !important;
    justify-content: flex-end !important;
    text-align: right !important;
  }
  
  /* "추가" 버튼을 원형 버튼으로 */
  .btn-primary.btn-lg {
    padding: 0 !important;
    width: 40px !important;
    height: 40px !important;
    border-radius: 50% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 0 !important;
    gap: 0 !important;
    min-width: auto !important;
    float: none !important;
  }
  
  .btn-primary.btn-lg i {
    font-size: 14px !important;
    line-height: 1 !important;
    color: white !important;
  }
  
  .btn-primary.btn-lg span {
    display: none !important;
  }
}

@media (max-width: 576px) {
  .btn-primary.btn-lg {
    width: 36px !important;
    height: 36px !important;
  }
  
  .btn-primary.btn-lg i {
    font-size: 12px !important;
  }
}

/* 확인 모달 스타일 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000; /* 모달 오버레이 */
  animation: fadeIn 0.3s ease-out;
}

.modal-content {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow: hidden;
  animation: slideInUp 0.3s ease-out;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #e9ecef;
  background: #f8f9fa;
}

.modal-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 10px;
}

.modal-close {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #6c757d;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s;
}

.modal-close:hover {
  background: #e9ecef;
  color: #495057;
}

.modal-body {
  padding: 24px;
}

.modal-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding: 20px 24px;
  border-top: 1px solid #e9ecef;
  background: #f8f9fa;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideInUp {
  from {
    transform: translateY(50px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
</style> 