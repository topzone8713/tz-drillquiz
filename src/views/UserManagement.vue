<template>
  <div class="user-management-modern">
    <!-- Toast Notifications -->
    <div v-if="showToast" class="toast-notification" :class="toastType">
      <div class="toast-content">
        <i :class="toastIcon"></i>
        <span>{{ toastMessage }}</span>
      </div>
      <button class="toast-close" @click="hideToast">
        <i class="fas fa-times"></i>
      </button>
    </div>

    <!-- 번역 로딩 중일 때 로딩 표시 -->
    <div v-if="!$isTranslationsLoaded($i18n.locale)" class="loading-container">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">{{ $t('common.loadingTranslations') }}</span>
      </div>
      <p class="mt-3">{{ $t('common.loadingTranslationData') }}</p>
    </div>

    <!-- 번역이 로드된 후에만 컨텐츠 표시 -->
    <div v-else class="user-management-content">
      <!-- Top Header -->
      <div class="top-header">
        <div class="header-actions">
        </div>
      </div>

      <!-- Page Title -->
      <div class="page-title">
        <h1>{{ $t('userManagement.title') }}</h1>
      </div>

      <!-- 사용자 추가 폼 -->
      <div class="card-modern user-form-card" v-if="showAddUserForm">
        <div class="card-header-modern">
          <h3>{{ $t('userManagement.addUser') }}</h3>
          <button @click="toggleAddUserForm" class="card-action-btn">
            <i class="fas fa-times"></i>
            <span class="action-label">{{ $t('userManagement.upload.cancel') }}</span>
          </button>
        </div>
        <div class="card-body">
        <form @submit.prevent="createUser">
          <div class="row">
            <div class="col-md-4">
              <div class="form-group">
                <label>{{ $t('userManagement.table.name') }}</label>
                <input
                  v-model="newUser.first_name"
                  type="text"
                  class="form-control"
                  :placeholder="$t('userManagement.table.name')"
                >
              </div>
            </div>
            <div class="col-md-4">
              <div class="form-group">
                <label>{{ $t('userManagement.table.username') }} *</label>
                <input
                  v-model="newUser.username"
                  type="text"
                  class="form-control"
                  :placeholder="$t('userManagement.table.username')"
                  required
                >
              </div>
            </div>
            <div class="col-md-4">
              <div class="form-group">
                <label>{{ $t('userManagement.table.changePassword') }} *</label>
                <div class="input-group">
                <input
                  v-model="newUser.password"
                  type="password"
                  class="form-control"
                  :placeholder="$t('userManagement.table.changePassword')"
                  required
                >
                </div>
              </div>
            </div>
          </div>
          <div class="row">
            <div class="col-md-4">
              <div class="form-group">
                <label>{{ $t('userManagement.table.email') }}</label>
                <input
                  v-model="newUser.email"
                  type="email"
                  class="form-control"
                  :placeholder="$t('userManagement.table.email')"
                >
              </div>
            </div>
            <div class="col-md-4">
              <div class="form-group">
                <label>{{ $t('userManagement.table.role') }}</label>
                <select v-model="newUser.role" class="form-control">
                  <option value="user_role">{{ $t('userManagement.table.roleOptions.generalUser') }}</option>
                  <option value="study_admin_role">{{ $t('userManagement.table.roleOptions.studyAdmin') }}</option>
                  <option value="admin_role">{{ $t('userManagement.table.roleOptions.admin') }}</option>
                </select>
              </div>
            </div>
            <div class="col-md-4">
               <div class="form-group float-end">
                 <label>&nbsp;</label>
                 <div class="d-flex gap-3 justify-content-end">
                   <button type="submit" class="action-btn action-btn-success" :disabled="!newUser.username || !newUser.password">
                     <i class="fas fa-save"></i>
                     <span class="action-label">Save</span>
                   </button>
                 </div>
               </div>
             </div>
          </div>
          <div v-if="addUserMessage" class="alert alert-info mt-3">
            <i class="fas fa-info-circle me-2"></i>
            {{ addUserMessage }}
          </div>
        </form>
        </div>
      </div>

              <!-- Excel 업로드 폼 -->
        <div class="card-modern upload-form-card" v-if="showUploadForm">
          <div class="card-header-modern">
            <h3>{{ $t('userManagement.upload.title') }}</h3>
            <button @click="toggleUploadForm" class="card-action-btn">
              <i class="fas fa-times"></i>
              <span class="action-label">{{ $t('userManagement.upload.cancel') }}</span>
            </button>
          </div>
          <div class="card-body">
            <div class="row">
              <div class="col-md-8">
                <div class="form-group">
                  <label>{{ $t('userManagement.upload.fileSelection') }}</label>
                  <input 
                    type="file" 
                    class="form-control" 
                    @change="handleFileSelect" 
                    accept=".xlsx,.xls"
                    ref="fileInput"
                  >
                </div>
              </div>
              <div class="col-md-4">
                <div class="form-group">
                  <label>&nbsp;</label>
                  <div class="d-flex gap-3 justify-content-end">
                    <button 
                      @click="uploadUsersExcel" 
                      class="action-btn action-btn-primary"
                      :disabled="!selectedFile"
                    >
                      <i class="fas fa-upload"></i>
                      <span class="action-label">{{ $t('userManagement.upload.upload') }}</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
            
            <div v-if="uploadMessage" class="alert alert-info mt-3">
              <i class="fas fa-info-circle me-2"></i>
              {{ uploadMessage }}
            </div>
            
            <!-- Excel 파일 형식 안내 -->
            <div class="mt-4">
              <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                <strong>{{ $t('userManagement.upload.fileFormat') }}</strong> {{ $t('userManagement.upload.fileFormatDescription') }}
              </div>
              <h6>{{ $t('userManagement.upload.formatExample') }}</h6>
              <div class="table-responsive">
                <table class="table table-sm table-bordered">
                  <thead class="table-light">
                    <tr>
                      <th>{{ $t('userManagement.table.name') }}</th>
                      <th>{{ $t('userManagement.table.username') }}</th>
                      <th>{{ $t('userManagement.table.email') }}</th>
                      <th>{{ $t('userManagement.table.role') }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>Doohee Hong</td>
                      <td>admin</td>
                      <td>admin@example.com</td>
                      <td>{{ $t('userManagement.table.roleOptions.admin') }}</td>
                    </tr>
                    <tr>
                      <td>Doogee Hong</td>
                      <td>user1</td>
                      <td>user1@example.com</td>
                      <td>{{ $t('userManagement.table.roleOptions.generalUser') }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <small class="text-muted">
                * {{ $t('userManagement.upload.requiredColumns') }}<br>
                * {{ $t('userManagement.upload.roleOptions') }}<br>
                * {{ $t('userManagement.upload.updateNote') }}
              </small>
            </div>
          </div>
        </div>

      <!-- 사용자 목록 -->
      <div class="card-modern user-list-card">
        <div class="card-header-modern">
          <h3>{{ $t('userManagement.userList') }}</h3>
          <div class="card-actions">

            <button
              @click="toggleAddUserForm"
              class="action-btn action-btn-success"
              v-if="!showAddUserForm && isAdmin"
            >
              <i class="fas fa-plus"></i>
              <span class="action-label">{{ $t('userManagement.add') }}</span>
            </button>
            <button
              @click="toggleUploadForm"
              class="action-btn action-btn-primary"
              v-if="!showUploadForm && isAdmin"
            >
              <i class="fas fa-upload"></i>
              <span class="action-label">{{ $t('userManagement.uploadExcel') }}</span>
            </button>

            <button @click="downloadUsersExcel" class="action-btn action-btn-info" v-if="isAdmin">
              <i class="fas fa-download"></i>
              <span class="action-label">{{ $t('userManagement.downloadExcel') }}</span>
            </button>
            <button @click="deleteSelectedUsers" class="action-btn action-btn-danger" :disabled="selectedUsers.length === 0" v-if="isAdmin">
              <i class="fas fa-trash"></i>
              <span class="action-label">{{ $t('userManagement.deleteSelected') }} ({{ selectedUsers.length }})</span>
            </button>
          </div>
        </div>

        <div class="card-body">
          <div class="table-responsive">
            <table class="table table-striped">
              <thead>
                <tr>
                  <th v-if="isAdmin">
                    <input 
                      type="checkbox" 
                      @change="isAllSelected ? selectedUsers = [] : selectedUsers = users.map(user => user.id)"
                      :checked="isAllSelected"
                      class="form-check-input"
                    >
                  </th>
                  <th @click="setSort('first_name')" style="cursor:pointer">
                    {{ $t('userManagement.table.name') }}
                    <i :class="getSortIcon('first_name')" class="ms-1"></i>
                  </th>
                  <th @click="setSort('username')" style="cursor:pointer">
                    {{ $t('userManagement.table.username') }}
                    <i :class="getSortIcon('username')" class="ms-1"></i>
                  </th>
                  <th @click="setSort('email')" style="cursor:pointer">
                    {{ $t('userManagement.table.email') }}
                    <i :class="getSortIcon('email')" class="ms-1"></i>
                  </th>
                  <th @click="setSort('role')" style="cursor:pointer">
                    {{ $t('userManagement.table.role') }}
                    <i :class="getSortIcon('role')" class="ms-1"></i>
                  </th>
                  <th @click="setSort('date_joined')" style="cursor:pointer">
                    {{ $t('userManagement.table.joinDate') }}
                    <i :class="getSortIcon('date_joined')" class="ms-1"></i>
                  </th>
                  <th>{{ $t('userManagement.table.actions') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in sortedUsers" :key="user.id">
                  <td v-if="isAdmin">
                    <input 
                      type="checkbox" 
                      :value="user.id"
                      v-model="selectedUsers"
                      class="form-check-input"
                    >
                  </td>
                  <td>
                    <input 
                      v-if="isAdmin"
                      v-model="user.first_name"
                      type="text"
                      class="form-control form-control-sm"
                      @blur="updateUser(user)"
                      :placeholder="$t('userManagement.table.name')"
                    >
                    <span v-else>{{ user.first_name }}</span>
                  </td>
                  <td>{{ user.username }}</td>
                  <td>
                    <input 
                      v-if="isAdmin"
                      v-model="user.email" 
                      type="email" 
                      class="form-control form-control-sm"
                      @blur="updateUser(user)"
                    >
                    <span v-else>{{ user.email }}</span>
                  </td>
                  <td>
                    <select 
                      v-if="isAdmin"
                      v-model="user.role" 
                      class="form-select form-select-sm"
                      @change="updateUser(user)"
                    >
                      <option value="user_role">{{ $t('userManagement.table.roleOptions.generalUser') }}</option>
                      <option value="study_admin_role">{{ $t('userManagement.table.roleOptions.studyAdmin') }}</option>
                      <option value="admin_role">{{ $t('userManagement.table.roleOptions.admin') }}</option>
                    </select>
                    <span v-else>
                      <span class="badge" :class="getRoleBadgeClass(user.role)">
                        {{ getRoleText(user.role) }}
                      </span>
                    </span>
                  </td>
                  <td>{{ formatDate(user.date_joined) }}</td>
                  <td>
                    <div v-if="editingPasswordUserId === user.id">
                      <div class="input-group input-group-sm">
                        <input type="password" v-model="newPassword" class="form-control" :placeholder="$t('userManagement.table.changePassword')">
                        <button class="btn btn-success" @click="changeUserPassword(user, newPassword)">Save</button>
                      </div>
                    </div>
                    <div v-else>
                      <button class="btn btn-sm btn-outline-secondary" @click="startEditPassword(user.id)">{{ $t('userManagement.table.changePassword') }}</button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <div v-if="users.length === 0" class="text-center py-4">
            <i class="fas fa-users fa-3x text-muted mb-3"></i>
            <p class="text-muted">{{ $t('userManagement.messages.noUsers') }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 사용자 삭제 확인 모달 -->
    <div v-if="showDeleteConfirmModal" class="modal-overlay" @click="deleting ? null : hideDeleteConfirm">
      <div class="modal-content" @click.stop :class="{ 'deleting': deleting }">
                  <div class="modal-header">
            <h5 class="modal-title">
              <i class="fas fa-exclamation-triangle text-danger me-2"></i>
              {{ $t('profile.withdrawal.confirm.title') }}
            </h5>
            <button class="modal-close" @click="hideDeleteConfirm" :disabled="deleting">
              <i class="fas fa-times"></i>
            </button>
          </div>
          <div class="modal-body">
            <div class="alert alert-danger">
              <i class="fas fa-exclamation-triangle"></i>
              <strong>{{ $t('profile.withdrawal.confirm.warning') }}</strong>
            </div>
            <p>{{ $t('profile.withdrawal.confirm.message') }}</p>
            <ul class="withdrawal-impact-list">
              <li>{{ $t('profile.withdrawal.confirm.impact1') }}</li>
              <li>{{ $t('profile.withdrawal.confirm.impact2') }}</li>
              <li>{{ $t('profile.withdrawal.confirm.impact3') }}</li>
              <li>{{ $t('profile.withdrawal.confirm.impact4') }}</li>
              <li>{{ $t('profile.withdrawal.confirm.impact5') }}</li>
            </ul>
            <div class="form-group">
              <label class="form-label">{{ $t('profile.withdrawal.confirm.confirmation') }}</label>
              <input v-model="deleteConfirmation" type="text" class="form-control-modern" :placeholder="$t('profile.withdrawal.confirm.placeholder')" :disabled="deleting">
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="hideDeleteConfirm" :disabled="deleting">
              {{ $t('common.cancel') }}
            </button>
            <button class="btn btn-danger" @click="confirmDeleteUsers" :disabled="!canConfirmDelete || deleting">
              <i v-if="deleting" class="fas fa-spinner fa-spin me-1"></i>
              <i v-else class="fas fa-trash me-1"></i>
              {{ deleting ? $t('profile.withdrawal.processing') : $t('common.confirm') }}
            </button>
          </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { debugLog } from '@/utils/debugUtils'
import { isAdmin, hasStudyAdminRole } from '@/utils/permissionUtils'

export default {
  name: 'UserManagement',
  data() {
    return {
      users: [],
      error: '',
      success: '',
      showUploadForm: false,
      selectedFile: null,
      uploadMessage: '',
      selectedUsers: [],
      showAddUserForm: false,
      newUser: {
        first_name: '',
        username: '',
        password: '',
        email: '',
        role: 'user_role'
      },
      addUserMessage: '',
      sortKey: 'username',
      sortOrder: 'asc',
      editingPasswordUserId: null,
      newPassword: '',
      showToast: false,
      toastMessage: '',
      toastType: 'success',
      toastIcon: '',
      showDeleteConfirmModal: false,
      deleteConfirmation: '',
      deleting: false
    }
  },
  computed: {
    isAdmin() {
      return isAdmin()
    },
    isStudyAdmin() {
      return hasStudyAdminRole()
    },
    isAllSelected() {
      return this.users.length > 0 && this.selectedUsers.length === this.users.length
    },
    sortedUsers() {
      return [...this.users].sort((a, b) => {
        let aValue = a[this.sortKey]
        let bValue = b[this.sortKey]
        
        // 날짜 정렬을 위한 변환
        if (this.sortKey === 'date_joined') {
          aValue = new Date(aValue)
          bValue = new Date(bValue)
        }
        
        // 문자열 비교
        if (aValue < bValue) {
          return this.sortOrder === 'asc' ? -1 : 1
        }
        if (aValue > bValue) {
          return this.sortOrder === 'asc' ? 1 : -1
        }
        return 0
      })
    },
    canConfirmDelete() {
      return this.deleteConfirmation === this.$t('profile.withdrawal.confirm.placeholder')
    }
  },
  async mounted() {
    await this.loadUsers()
  },
  methods: {
    async loadUsers() {
      try {
        const response = await axios.get('/api/users/')
        this.users = response.data
      } catch (err) {
        this.showToastNotification(this.$t('userManagement.messages.loading'), 'error')
      }
    },
    async updateUser(user) {
      try {
        await axios.put(`/api/users/${user.id}/`, {
          first_name: user.first_name,
          email: user.email,
          role: user.role,
          language: this.$i18n.locale
        })
        this.showToastNotification(this.$t('userManagement.messages.updateUserSuccess'), 'success')
      } catch (err) {
        this.showToastNotification(err.response?.data?.detail || this.$t('userManagement.messages.updateUserFailed'), 'error')
      }
    },
    formatDate(dateString) {
      if (!dateString) {
        return '-'
      }
      try {
        const date = new Date(dateString)
        if (isNaN(date.getTime())) {
          return '-'
        }
        return date.toLocaleDateString('ko-KR')
      } catch (error) {
        debugLog('날짜 파싱 오류:', error, 'error')
        return '-'
      }
    },
    async downloadUsersExcel() {
      try {
        const response = await axios.get('/api/users/download-excel/', {
          responseType: 'blob'
        })
        
        // 파일 다운로드
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        
        // 파일명 추출 (Content-Disposition 헤더에서)
        const contentDisposition = response.headers['content-disposition']
        let filename = 'users.xlsx'
        if (contentDisposition) {
          const filenameMatch = contentDisposition.match(/filename="(.+)"/)
          if (filenameMatch) {
            filename = filenameMatch[1]
          }
        }
        
        link.setAttribute('download', filename)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
        
        this.showToastNotification(this.$t('userManagement.messages.downloadSuccess'), 'success')
      } catch (error) {
        debugLog('Excel 다운로드 오류:', error, 'error')
        this.showToastNotification(this.$t('userManagement.messages.downloadFailed'), 'error')
      }
    },
    toggleUploadForm() {
      this.showUploadForm = !this.showUploadForm
      if (!this.showUploadForm) {
        this.resetUploadForm()
      }
    },
    resetUploadForm() {
      this.selectedFile = null
      this.uploadMessage = ''
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = ''
      }
    },
    cancelUpload() {
      this.showUploadForm = false
      this.resetUploadForm()
    },
    handleFileSelect(event) {
      this.selectedFile = event.target.files[0]
      this.uploadMessage = ''
    },
    async uploadUsersExcel() {
      if (!this.selectedFile) {
        this.showToastNotification(this.$t('userManagement.messages.uploadFailed'), 'error')
        return
      }

      try {
        const formData = new FormData()
        formData.append('file', this.selectedFile)

        const response = await axios.post('/api/users/upload-excel/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        
        this.uploadMessage = response.data.message
        this.loadUsers() // 사용자 목록 새로고침
        this.resetUploadForm()
        this.showUploadForm = false
        
        // 상세 통계 표시
        if (response.data.stats) {
          const stats = response.data.stats
          let detailMessage = `총 ${stats.total_rows}행 처리\n`
          detailMessage += `생성: ${stats.created}명\n`
          detailMessage += `업데이트: ${stats.updated}명\n`
          if (stats.errors > 0) {
            detailMessage += `오류: ${stats.errors}건\n`
            if (stats.error_details.length > 0) {
              detailMessage += '\n오류 상세:\n' + stats.error_details.slice(0, 5).join('\n')
              if (stats.error_details.length > 5) {
                detailMessage += `\n... 외 ${stats.error_details.length - 5}건`
              }
            }
          }
          this.showToastNotification(detailMessage, 'info')
        }
      } catch (error) {
        debugLog('Upload error:', error, 'error')
        if (error.response && error.response.data && error.response.data.detail) {
          this.uploadMessage = `${this.$t('userManagement.messages.uploadFailed')}: ${error.response.data.detail}`
        } else {
          this.uploadMessage = this.$t('userManagement.messages.uploadFailed')
        }
      }
    },
        async deleteSelectedUsers() {
      if (this.selectedUsers.length === 0) {
        this.showToastNotification(this.$t('userManagement.messages.noUsers'), 'warning')
        return
      }
      
      // 모달 표시
      this.showDeleteConfirmModal = true
      this.deleteConfirmation = ''
    },
    
    // 모달 관련 함수들
    hideDeleteConfirm() {
      this.showDeleteConfirmModal = false
      this.deleteConfirmation = ''
    },
    
    async confirmDeleteUsers() {
      this.deleting = true
      try {
        const deletedUsers = []
        const errors = []
        
        // 각 사용자를 개별적으로 삭제 (delete_user API 사용)
        for (const userId of this.selectedUsers) {
          try {
            // 해당 사용자의 정보를 가져와서 username 확인
            const user = this.users.find(u => u.id === userId)
            if (!user) {
              errors.push(`사용자 ID ${userId}: 사용자를 찾을 수 없습니다.`)
              continue
            }
            
            // delete_user API 호출 (delete_my_account와 동일한 로직 사용)
            await axios.delete(`/api/users/${userId}/delete/`)
            deletedUsers.push(user.username)
            
          } catch (error) {
            const username = this.users.find(u => u.id === userId)?.username || `ID ${userId}`
            if (error.response && error.response.data && error.response.data.detail) {
              errors.push(`${username}: ${error.response.data.detail}`)
            } else {
              errors.push(`${username}: 삭제 중 오류가 발생했습니다.`)
            }
          }
        }
        
        // 결과 표시
        if (deletedUsers.length > 0) {
          this.showToastNotification(this.$t('userManagement.messages.deleteSuccess', { count: deletedUsers.length }), 'success')
          const deletedNames = deletedUsers.join(', ')
          this.showToastNotification(this.$t('userManagement.deleteConfirm.deletedUsers', { names: deletedNames }), 'info')
        }
        
        if (errors.length > 0) {
          this.showToastNotification(`오류가 발생한 사용자:\n${errors.join('\n')}`, 'error')
        }
        
        // 선택 초기화 및 사용자 목록 새로고침
        this.selectedUsers = []
        this.loadUsers()
        
        // 모달 닫기
        this.hideDeleteConfirm()
        
      } catch (error) {
        debugLog('Bulk delete error:', error, 'error')
        this.showToastNotification('사용자 삭제 중 오류가 발생했습니다.', 'error')
      } finally {
        this.deleting = false
      }
    },
    
    toggleAddUserForm() {
      this.showAddUserForm = !this.showAddUserForm
      if (!this.showAddUserForm) {
        this.resetAddUserForm()
      }
    },
    resetAddUserForm() {
      this.newUser = {
        first_name: '',
        username: '',
        password: '',
        email: '',
        role: 'user_role'
      }
      this.addUserMessage = ''
    },
    cancelAddUser() {
      this.showAddUserForm = false
      this.resetAddUserForm()
    },
    async createUser() {
      if (!this.newUser.username || !this.newUser.password) {
        this.addUserMessage = this.$t('userManagement.messages.addUserFailed')
        return
      }

      try {
        const userData = { ...this.newUser, language: this.$i18n.locale }
        const response = await axios.post('/api/users/create/', userData)
        
        this.showToastNotification(response.data.detail, 'success')
        this.loadUsers() // 사용자 목록 새로고침
        this.resetAddUserForm()
        this.showAddUserForm = false
      } catch (error) {
        debugLog('Create user error:', error, 'error')
        if (error.response && error.response.data && error.response.data.detail) {
          this.addUserMessage = `${this.$t('userManagement.messages.addUserFailed')}: ${error.response.data.detail}`
        } else {
          this.addUserMessage = this.$t('userManagement.messages.addUserFailed')
        }
      }
    },
    setSort(key) {
      if (this.sortKey === key) {
        this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc'
      } else {
        this.sortKey = key
        this.sortOrder = 'asc'
      }
    },
    getSortIcon(key) {
      if (this.sortKey === key) {
        return this.sortOrder === 'asc' ? 'fas fa-sort-up' : 'fas fa-sort-down'
      }
      return 'fas fa-sort'
    },
    startEditPassword(userId) {
      this.editingPasswordUserId = userId;
      this.newPassword = '';
    },
    cancelEditPassword() {
      this.editingPasswordUserId = null;
      this.newPassword = '';
    },
    async changeUserPassword(user, newPassword) {
      debugLog('changeUserPassword 호출', { user, newPassword });
      if (!newPassword || newPassword.length < 6) {
        this.showToastNotification(this.$t('userManagement.messages.addUserFailed'), 'error');
        return;
      }
      try {
        await axios.post(`/api/user/${user.id}/change-password/`, { password: newPassword });
        this.showToastNotification(this.$t('userManagement.messages.updateUserSuccess'), 'success');
        this.cancelEditPassword();
      } catch (err) {
        this.showToastNotification(err.response?.data?.detail || this.$t('userManagement.messages.updateUserFailed'), 'error');
      }
    },
    getRoleBadgeClass(role) {
      return role || 'user_role';
    },
    getRoleText(role) {
      switch (role) {
        case 'admin_role':
          return this.$t('userManagement.table.roleOptions.admin')
        case 'study_admin_role':
          return this.$t('userManagement.table.roleOptions.studyAdmin')
        case 'user_role':
        default:
          return this.$t('userManagement.table.roleOptions.generalUser')
      }
    },
    showToastNotification(message, type = 'success') {
      this.toastMessage = message
      this.toastType = type
      this.toastIcon = this.getToastIcon(type)
      this.showToast = true
      
      setTimeout(() => {
        this.hideToast()
      }, 5000)
    },
    hideToast() {
      this.showToast = false
    },
    getToastIcon(type) {
      switch (type) {
        case 'success':
          return 'fas fa-check-circle'
        case 'error':
          return 'fas fa-exclamation-circle'
        case 'warning':
          return 'fas fa-exclamation-triangle'
        case 'info':
          return 'fas fa-info-circle'
        default:
          return 'fas fa-info-circle'
      }
    }
  }
}
</script>

<style scoped>
.user-management-modern {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.user-management-content {
  max-width: 1400px;
  margin: 0 auto;
  background: white;
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}





/* Action Buttons */
.action-btn {
  display: inline-flex;
  align-items: center;
  padding: 12px 24px;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  font-size: 0.95rem;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.action-btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.action-btn-success {
  background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
  color: white;
}

.action-btn-info {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
}

.action-btn-danger {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
  color: white;
}

.action-btn-secondary {
  background: linear-gradient(135deg, #95a5a6 0%, #7f8c8d 100%);
  color: white;
}

.action-btn-outline {
  background: transparent;
  border: 2px solid #667eea;
  color: #667eea;
}

.action-btn-outline:hover {
  background: #667eea;
  color: white;
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.action-btn.btn-sm {
  padding: 8px 16px;
  font-size: 0.85rem;
}

.action-label {
  margin-left: 8px;
}

/* Top Header */
.top-header {
  padding: 20px 30px;
  background: white;
  border-bottom: 1px solid #e9ecef;
}

.header-actions {
  display: flex;
  gap: 15px;
  justify-content: flex-end;
}

/* Page Title */
.page-title {
  padding: 30px;
  background: white;
  border-bottom: 1px solid #e9ecef;
}

@media (max-width: 768px) {
  .page-title {
    padding-top: 20px;
    padding-bottom: 20px;
  }
}

.page-title h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  color: #2c3e50;
}

/* Modern Cards */
.card-modern {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  padding: 30px;
  margin: 20px 30px;
  border: 1px solid #e9ecef;
}

.card-header-modern {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e9ecef;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

  .card-header-modern h3 {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
    color: #2c3e50;
  }

  /* Form Styles */
  .form-group {
    margin-bottom: 1rem;
  }

  .form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: #495057;
  }

  .form-control {
    display: block;
    width: 100%;
    padding: 0.375rem 0.75rem;
    font-size: 1rem;
    font-weight: 400;
    line-height: 1.5;
    color: #495057;
    background-color: #fff;
    background-clip: padding-box;
    border: 1px solid #ced4da;
    border-radius: 0.375rem;
    transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
  }

  .form-control:focus {
    color: #495057;
    background-color: #fff;
    border-color: #86b7fe;
    outline: 0;
    box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
  }

  .form-control::placeholder {
    color: #6c757d;
    opacity: 1;
  }

  /* Action Button Styles */
  .action-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 500;
    text-decoration: none;
    cursor: pointer;
    transition: all 0.2s ease;
    white-space: nowrap;
  }

  .action-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .action-btn-success {
    background: #28a745;
    color: white;
  }

  .action-btn-success:hover:not(:disabled) {
    background: #218838;
    transform: translateY(-1px);
  }

  .action-btn-secondary {
    background: #6c757d;
    color: white;
  }

  .action-btn-secondary:hover:not(:disabled) {
    background: #5a6268;
    transform: translateY(-1px);
  }

  .action-btn-primary {
    background: #007bff;
    color: white;
  }

  .action-btn-primary:hover:not(:disabled) {
    background: #0056b3;
    transform: translateY(-1px);
  }

  .action-btn-info {
    background: #17a2b8;
    color: white;
  }

  .action-btn-info:hover:not(:disabled) {
    background: #138496;
    transform: translateY(-1px);
  }

  .action-btn-danger {
    background: #dc3545;
    color: white;
  }

  .action-btn-danger:hover:not(:disabled) {
    background: #c82333;
    transform: translateY(-1px);
  }

  .action-btn-warning {
    background: #ffc107;
    color: #212529;
  }

  .action-btn-warning:hover:not(:disabled) {
    background: #e0a800;
    transform: translateY(-1px);
  }

.card-actions {
  display: flex;
  gap: 10px;
}

.card-action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: 1px solid #e9ecef;
  border-radius: 20px;
  background: #f8f9fa;
  color: #6c757d;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.card-action-btn:hover {
  background: #007bff;
  color: white;
}

.card-title-modern {
  font-size: 1.5rem;
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
  display: flex;
  align-items: center;
}

.card-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

.user-count {
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.9rem;
}

.card-body-modern {
  padding: 30px;
}

/* Close Button */
.close-btn-modern {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 50%;
  background: rgba(108, 117, 125, 0.1);
  color: #6c757d;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.close-btn-modern:hover {
  background: rgba(108, 117, 125, 0.2);
  transform: scale(1.1);
}

/* Modern Table */
.table-modern {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.table-modern th {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  color: #2c3e50;
  font-weight: 600;
  padding: 15px;
  text-align: left;
  border-bottom: 2px solid rgba(0, 0, 0, 0.05);
  position: relative;
}

.sortable-column {
  cursor: pointer;
  user-select: none;
  transition: background-color 0.3s ease;
}

.sortable-column:hover {
  background: rgba(102, 126, 234, 0.1);
}

.sort-icon {
  margin-left: 8px;
  color: #667eea;
  font-size: 0.9rem;
}

.checkbox-column {
  width: 50px;
  text-align: center;
}

.table-modern td {
  padding: 15px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  vertical-align: middle;
}

.table-row-modern:hover {
  background: rgba(102, 126, 234, 0.02);
}

/* Form Elements */
.form-input-modern {
  width: 100%;
  padding: 10px 15px;
  border: 2px solid rgba(0, 0, 0, 0.1);
  border-radius: 10px;
  font-size: 0.9rem;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.8);
}

.form-input-modern:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  background: white;
}

.form-select-modern {
  width: 100%;
  padding: 10px 15px;
  border: 2px solid rgba(0, 0, 0, 0.1);
  border-radius: 10px;
  font-size: 0.9rem;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.8);
  cursor: pointer;
}

.form-select-modern:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  background: white;
}

.form-check-input-modern {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.form-label-modern {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #2c3e50;
  font-size: 0.9rem;
}

/* Upload Form */
.upload-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.file-input-section {
  display: flex;
  gap: 15px;
  align-items: center;
  flex-wrap: wrap;
}

.file-input-modern {
  flex: 1;
  min-width: 300px;
  padding: 12px;
  border: 2px dashed rgba(102, 126, 234, 0.3);
  border-radius: 10px;
  background: rgba(102, 126, 234, 0.05);
  cursor: pointer;
  transition: all 0.3s ease;
}

.file-input-modern:hover {
  border-color: rgba(102, 126, 234, 0.5);
  background: rgba(102, 126, 234, 0.1);
}

.file-input-actions {
  display: flex;
  gap: 10px;
}

/* Format Guide */
.format-guide {
  background: rgba(102, 126, 234, 0.05);
  border-radius: 15px;
  padding: 20px;
  border: 1px solid rgba(102, 126, 234, 0.1);
}

.guide-header {
  font-size: 1.1rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 10px;
}

.guide-description {
  color: #7f8c8d;
  margin-bottom: 15px;
}

.guide-subtitle {
  font-size: 1rem;
  font-weight: 600;
  color: #2c3e50;
  margin: 20px 0 10px 0;
}

.guide-notes {
  margin-top: 15px;
}

/* Add User Form */
.add-user-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 20px;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

/* Password Edit Form */
.password-edit-form {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.password-input {
  min-width: 200px;
}

/* User Info Display */
.user-name, .username, .user-email, .join-date {
  font-weight: 500;
  color: #2c3e50;
}

.username {
  font-weight: 600;
  color: #667eea;
}

.user-role {
  display: flex;
  align-items: center;
}

.role-badge {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.badge.admin_role {
  background-color: #dc3545;
}

.badge.study_admin_role {
  background-color: #0d6efd;
}

.badge.user_role {
  background-color: #198754;
}

/* Actions Column */
.actions-column {
  min-width: 200px;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #7f8c8d;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 20px;
  opacity: 0.5;
}

.empty-text {
  font-size: 1.1rem;
  margin: 0;
}

/* Alerts */
.alert-modern {
  padding: 15px 20px;
  border-radius: 12px;
  border: none;
  font-weight: 500;
  display: flex;
  align-items: center;
}

.alert-info {
  background: rgba(52, 152, 219, 0.1);
  color: #2980b9;
  border-left: 4px solid #3498db;
}

/* Toast Notifications - 기본 스타일은 공통 CSS (mobile-buttons.css)에 정의됨 */

/* 타입별 스타일은 공통 CSS (mobile-buttons.css)에 정의됨 */

.toast-content {
  padding: 15px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.toast-close {
  position: absolute;
  top: 10px;
  right: 10px;
  background: none;
  border: none;
  color: #7f8c8d;
  cursor: pointer;
  padding: 5px;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.toast-close:hover {
  background: rgba(0, 0, 0, 0.1);
  color: #2c3e50;
}

@keyframes slideInRight {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* Loading Container */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  color: white;
}

.loading-container .spinner-border {
  width: 3rem;
  height: 3rem;
}

.loading-container p {
  margin-top: 20px;
  font-size: 1.1rem;
  opacity: 0.9;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000; /* 모달 오버레이 */
}

.modal-content {
  background: white;
  border-radius: 16px;
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  animation: modalSlideIn 0.3s ease;
}

.modal-content.deleting {
  pointer-events: none;
  opacity: 0.8;
}

.modal-header {
  padding: 20px 25px 15px;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #2c3e50;
  display: flex;
  align-items: center;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #6c757d;
  cursor: pointer;
  padding: 5px;
  border-radius: 50%;
  transition: all 0.3s ease;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close:hover {
  background: rgba(0, 0, 0, 0.1);
  color: #2c3e50;
}

.modal-body {
  padding: 20px 25px;
}

.modal-footer {
  padding: 15px 25px 20px;
  border-top: 1px solid #e9ecef;
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.withdrawal-impact-list {
  list-style: none;
  padding: 0;
  margin: 15px 0;
}

.withdrawal-impact-list li {
  padding: 8px 0;
  border-bottom: 1px solid #f8f9fa;
  color: #6c757d;
  position: relative;
  padding-left: 20px;
}

.withdrawal-impact-list li:before {
  content: "•";
  color: #dc3545;
  font-weight: bold;
  position: absolute;
  left: 0;
}

.withdrawal-impact-list li:last-child {
  border-bottom: none;
}

@keyframes modalSlideIn {
  from {
    transform: translateY(-50px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

/* Responsive Design */
@media (max-width: 768px) {
  .user-management-modern {
    padding: 15px;
  }
  
  .top-header {
    padding: 20px;
  }
  
  .page-title {
    font-size: 2rem;
  }
  
  .header-actions {
    flex-direction: column;
    width: 100%;
  }
  
  .action-btn {
    width: 100%;
    justify-content: center;
  }
  
  .card-header-modern {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .file-input-section {
    flex-direction: column;
    align-items: stretch;
  }
  
  .file-input-modern {
    min-width: auto;
  }
  
  .password-edit-form {
    flex-direction: column;
    align-items: stretch;
  }
  
  .password-input {
    min-width: auto;
  }
}
</style>