<template>
  <div class="voice-interview-results-list">
    <div class="container">
      <!-- 제목 섹션 -->
      <div class="mb-4">
        <div class="d-flex justify-content-between align-items-center">
          <h2>
            <i class="fas fa-microphone-alt text-primary me-2"></i>
            {{ $t('voiceInterview.resultsList.title') || 'Voice Interviews' }}
          </h2>
          <button @click="goBack" class="btn btn-secondary">
            <i class="fas fa-arrow-left me-1"></i>
            {{ $t('voiceInterview.resultsList.back') || '돌아가기' }}
          </button>
        </div>
        <div v-if="exam" class="mt-2">
          <p class="text-muted mb-0">
            <strong>{{ $t('voiceInterview.resultsList.exam') || '시험' }}:</strong> 
            {{ getExamTitle(exam) }}
            <span v-if="getUserName()" class="ms-3">
              <strong>{{ $t('voiceInterview.resultsList.user') || '사용자' }}:</strong> 
              {{ getUserName() }}
            </span>
          </p>
        </div>
      </div>

      <!-- 로딩 중 -->
      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">{{ $t('voiceInterview.resultsList.loading') || '로딩 중...' }}</span>
        </div>
        <p class="mt-2">{{ $t('voiceInterview.resultsList.loadingText') || '결과를 불러오는 중입니다...' }}</p>
      </div>

      <!-- 에러 메시지 -->
      <div v-else-if="error" class="alert alert-danger">
        <i class="fas fa-exclamation-triangle me-2"></i>
        {{ error }}
      </div>

      <!-- 결과 목록 -->
      <div v-else-if="results && results.length > 0" class="results-list">
        <div class="card">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h5 class="card-title mb-0">
              <i class="fas fa-list me-2"></i>
              {{ $t('voiceInterview.resultsList.totalResults', { count: totalCount }) || `총 ${totalCount}개의 결과` }}
            </h5>
            <button 
              v-if="selectedResults.length > 0"
              @click="deleteSelectedResults"
              class="btn btn-danger btn-sm delete-selected-btn"
              :disabled="isDeleting"
            >
              <i class="fas fa-trash me-1"></i>
              <span>{{ $t('voiceInterview.resultsList.delete') || 'Delete' }}</span>
            </button>
          </div>
          <div class="card-body">
            <div class="table-responsive">
              <table class="table table-hover">
                <thead>
                  <tr>
                    <th style="width: 40px;">
                      <input 
                        type="checkbox" 
                        :checked="isAllSelected"
                        @change="toggleSelectAll"
                        class="form-check-input"
                      />
                    </th>
                    <th>#</th>
                    <th>{{ $t('voiceInterview.resultsList.completedAt') || '완료일시' }}</th>
                    <th>{{ $t('voiceInterview.resultsList.totalQuestions') || '전체 문제' }}</th>
                    <th>{{ $t('voiceInterview.resultsList.correctAnswers') || '정답' }}</th>
                    <th>{{ $t('voiceInterview.resultsList.wrongAnswers') || '오답' }}</th>
                    <th>{{ $t('voiceInterview.resultsList.accuracy') || '정확도' }}</th>
                    <th>{{ $t('voiceInterview.resultsList.elapsedTime') || '소요 시간' }}</th>
                    <th>{{ $t('voiceInterview.resultsList.actions') || '작업' }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(result, index) in results" :key="result.id">
                    <td>
                      <input 
                        type="checkbox" 
                        :value="result.id"
                        v-model="selectedResults"
                        class="form-check-input"
                      />
                    </td>
                    <td>{{ (page - 1) * pageSize + index + 1 }}</td>
                    <td>{{ formatDateTime(result.completed_at) }}</td>
                    <td>{{ result.total_score }}</td>
                    <td class="text-success">{{ result.correct_count }}</td>
                    <td class="text-danger">{{ result.wrong_count }}</td>
                    <td>
                      <span :class="getAccuracyClass(result.accuracy)">
                        {{ result.accuracy.toFixed(1) }}%
                      </span>
                    </td>
                    <td>{{ formatTime(result.elapsed_seconds) }}</td>
                    <td>
                      <div class="btn-group" role="group">
                        <router-link 
                          :to="`/voice-interview-result/${result.id}`" 
                          class="btn btn-sm btn-primary"
                        >
                          <i class="fas fa-eye me-1"></i>
                          {{ $t('voiceInterview.resultsList.view') || '보기' }}
                        </router-link>
                        <button 
                          v-if="showShareButton"
                          class="btn btn-sm btn-info"
                          @click="openShareModal(result)"
                        >
                          <i class="fas fa-share-alt me-1"></i>
                          {{ $t('voiceInterview.shareResults') || '공유' }}
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- 페이지네이션 -->
            <nav v-if="totalPages > 1" aria-label="페이지 네비게이션">
              <ul class="pagination justify-content-center">
                <li class="page-item" :class="{ disabled: page === 1 }">
                  <a class="page-link" href="#" @click.prevent="goToPage(page - 1)">
                    {{ $t('voiceInterview.resultsList.previous') || '이전' }}
                  </a>
                </li>
                <li 
                  v-for="p in totalPages" 
                  :key="p" 
                  class="page-item" 
                  :class="{ active: p === page }"
                >
                  <a class="page-link" href="#" @click.prevent="goToPage(p)">{{ p }}</a>
                </li>
                <li class="page-item" :class="{ disabled: page === totalPages }">
                  <a class="page-link" href="#" @click.prevent="goToPage(page + 1)">
                    {{ $t('voiceInterview.resultsList.next') || '다음' }}
                  </a>
                </li>
              </ul>
            </nav>
          </div>
        </div>
      </div>

      <!-- 결과 없음 -->
      <div v-else class="alert alert-info">
        <i class="fas fa-info-circle me-2"></i>
        {{ $t('voiceInterview.resultsList.noResults') || 'Voice Interview 결과가 없습니다.' }}
      </div>
    </div>

    <!-- 공유 모달 -->
    <div v-if="showShareModal" class="modal-overlay" @click="closeShareModal">
      <div class="modal-content share-modal" @click.stop>
        <div class="modal-header">
          <h5 class="modal-title">
            <i class="fas fa-share-alt text-info"></i>
            {{ $t('voiceInterview.shareResults') || '결과 공유하기' }}
          </h5>
          <button class="modal-close" @click="closeShareModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <!-- 스터디가 없는 경우 -->
          <div v-if="!hasStudies" class="alert alert-warning">
            <i class="fas fa-exclamation-triangle me-2"></i>
            {{ $t('voiceInterview.share.noStudy') || '결과를 공유하려면 스터디가 필요합니다. 스터디를 먼저 만들어주세요.' }}
            <div class="mt-3">
              <button 
                class="btn btn-primary" 
                @click="createStudyForSharing"
                :disabled="isCreatingStudy"
              >
                <i class="fas fa-users me-1"></i>
                <span v-if="isCreatingStudy">
                  {{ $t('voiceInterview.share.creatingStudy') || '그룹 만들기 중...' }}
                </span>
                <span v-else>
                  {{ $t('voiceInterview.share.createStudy') || '그룹 만들기' }}
                </span>
              </button>
            </div>
          </div>

          <!-- 스터디가 있는 경우 -->
          <div v-else>
            <!-- 스터디 선택 -->
            <div class="mb-3">
              <label class="form-label">
                <i class="fas fa-users me-1"></i>
                {{ $t('voiceInterview.share.selectStudy') || '스터디 선택' }}
              </label>
              <select v-model="selectedStudyId" @change="loadStudyMembers" class="form-select">
                <option value="">{{ $t('voiceInterview.share.selectStudyPlaceholder') || '스터디를 선택하세요' }}</option>
                <option v-for="study in connectedStudies" :key="study.study_id || study.id" :value="String(study.study_id || study.id)">
                  {{ getStudyTitle(study) }}
                </option>
              </select>
            </div>

            <!-- 멤버 목록 (이메일이 있는 멤버만) -->
            <div v-if="selectedStudyId && membersWithEmail.length > 0" class="mb-3">
              <label class="form-label">
                <i class="fas fa-envelope me-1"></i>
                {{ $t('voiceInterview.share.selectMembers') || '멤버 선택 (이메일이 있는 멤버만)' }}
              </label>
              <div class="member-list" style="max-height: 300px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; border-radius: 4px;">
                <div v-for="member in membersWithEmail" :key="member.id" class="form-check mb-2">
                  <input 
                    class="form-check-input" 
                    type="checkbox" 
                    :value="member.id" 
                    :id="`member-${member.id}`"
                    v-model="selectedMemberIds"
                  >
                  <label class="form-check-label" :for="`member-${member.id}`">
                    <strong>{{ member.name }}</strong>
                    <span class="text-muted ms-2">({{ member.email }})</span>
                  </label>
                </div>
              </div>
              <div class="mt-2">
                <button class="btn btn-sm btn-outline-primary" @click="selectAllMembers">
                  {{ $t('voiceInterview.share.selectAll') || '전체 선택' }}
                </button>
                <button class="btn btn-sm btn-outline-secondary ms-2" @click="deselectAllMembers">
                  {{ $t('voiceInterview.share.deselectAll') || '전체 해제' }}
                </button>
              </div>
            </div>

            <!-- 멤버가 없는 경우 -->
            <div v-if="selectedStudyId && membersWithEmail.length === 0" class="alert alert-info">
              <i class="fas fa-info-circle me-2"></i>
              {{ $t('voiceInterview.share.noMembersWithEmail') || '이메일이 있는 멤버가 없습니다.' }}
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeShareModal">
            <i class="fas fa-times me-1"></i>
            {{ $t('voiceInterview.cancel') || '취소' }}
          </button>
          <button 
            v-if="hasStudies && selectedStudyId && selectedMemberIds.length > 0" 
            class="btn btn-primary" 
            :disabled="isSendingEmails"
            @click="sendShareEmails"
          >
            <i class="fas fa-paper-plane me-1"></i>
            <span v-if="isSendingEmails">
              {{ $t('voiceInterview.share.sending') || '전송 중...' }}
            </span>
            <span v-else>
              {{ $t('voiceInterview.share.send') || '이메일 전송' }}
            </span>
          </button>
        </div>
      </div>
    </div>

    <!-- 삭제 확인 모달 -->
    <div v-if="showDeleteConfirmModal" class="modal-overlay" @click="cancelDelete">
      <div class="modal-content delete-confirm-modal" @click.stop>
        <div class="modal-header">
          <h5 class="modal-title">
            <i class="fas fa-exclamation-triangle text-warning me-2"></i>
            {{ $t('voiceInterview.resultsList.confirmDeleteTitle') || '삭제 확인' }}
          </h5>
          <button class="modal-close" @click="cancelDelete">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <p>
            {{ $t('voiceInterview.resultsList.confirmDelete', { count: selectedResults.length }) || 
               `선택한 ${selectedResults.length}개의 결과를 삭제하시겠습니까?` }}
          </p>
          <p class="text-muted small mb-0">
            {{ $t('voiceInterview.resultsList.confirmDeleteWarning') || '이 작업은 되돌릴 수 없습니다.' }}
          </p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="cancelDelete" :disabled="isDeleting">
            {{ $t('voiceInterview.cancel') || '취소' }}
          </button>
          <button 
            class="btn btn-danger" 
            @click="confirmDelete"
            :disabled="isDeleting"
          >
            <i class="fas fa-trash me-1"></i>
            <span v-if="isDeleting">
              {{ $t('voiceInterview.resultsList.deleting') || '삭제 중...' }}
            </span>
            <span v-else>
              {{ $t('voiceInterview.resultsList.delete') || '삭제' }}
            </span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../services/api'
import { createStudyAndTaskForSharing } from '@/utils/shareExamUtils'
import { getLocalizedContentWithI18n } from '@/utils/multilingualUtils'
import { debugLog } from '@/utils/debugUtils'
import authService from '@/services/authService'

export default {
  name: 'VoiceInterviewResultsList',
  data() {
    return {
      exam: null,
      results: [],
      loading: true,
      error: null,
      page: 1,
      pageSize: 10,
      totalCount: 0,
      totalPages: 0,
      // 공유 모달 관련
      showShareModal: false,
      selectedResult: null,
      connectedStudies: [],
      selectedStudyId: null,
      studyMembers: [],
      selectedMemberIds: [],
      isSendingEmails: false,
      isCreatingStudy: false,
      // 사용자 프로필 언어 캐시
      userProfileLanguage: null,
      // 선택된 결과 ID 목록
      selectedResults: [],
      // 삭제 중 상태
      isDeleting: false,
      // 삭제 확인 모달
      showDeleteConfirmModal: false
    }
  },
  computed: {
    hasStudies() {
      return this.connectedStudies && this.connectedStudies.length > 0
    },
    membersWithEmail() {
      return this.studyMembers.filter(member => member.email && member.email.trim() !== '')
    },
    isAllSelected() {
      if (!this.results || this.results.length === 0) return false
      return this.results.every(result => this.selectedResults.includes(result.id))
    },
    // 공유 버튼 표시 여부 (17+ 등급만 표시)
    showShareButton() {
      // 세션이 없을 때는 기본적으로 표시
      const user = authService.getUserSync()
      if (!user) {
        return true
      }
      // 세션이 있을 때 17+ 미만이면 숨김
      if (user && user.age_rating) {
        return user.age_rating === '17+'
      }
      // age_rating이 없으면 기본적으로 표시 (기존 사용자 호환성)
      return true
    }
  },
  mounted() {
    this.loadResults()
  },
  watch: {
    '$route'(to, from) {
      if (to.params.examId !== from.params.examId) {
        this.loadResults()
      }
    }
  },
  methods: {
    async loadResults() {
      const examId = this.$route.params.examId
      if (!examId) {
        this.error = this.$t('voiceInterview.resultsList.noExamId') || '시험 ID가 없습니다.'
        this.loading = false
        return
      }

      try {
        this.loading = true
        this.page = parseInt(this.$route.query.page) || 1
        // 페이지 변경 시 선택 초기화
        this.selectedResults = []
        
        // 시험 정보 로드
        try {
          const examResponse = await api.get(`/api/exam/${examId}/`)
          this.exam = examResponse.data
        } catch (error) {
          console.warn('시험 정보 로드 실패:', error)
        }

        // 결과 목록 로드
        const response = await api.get(`/api/exam/${examId}/voice-interview-results/`, {
          params: {
            page: this.page,
            page_size: this.pageSize
          }
        })
        
        this.results = response.data.results || []
        this.totalCount = response.data.total_count || 0
        this.totalPages = response.data.total_pages || 0
      } catch (error) {
        console.error('Voice Interview 결과 목록 조회 실패:', error)
        this.error = error.response?.data?.error || this.$t('voiceInterview.resultsList.loadError') || '결과를 불러오는 중 오류가 발생했습니다.'
      } finally {
        this.loading = false
      }
    },
    getExamTitle(exam) {
      if (!exam) return 'Unknown'
      return getLocalizedContentWithI18n(
        exam,
        'title',
        this.$i18n,
        this.userProfileLanguage,
        'Unknown'
      )
    },
    getUserName() {
      // results에서 첫 번째 결과의 사용자 이름 가져오기
      if (this.results && this.results.length > 0 && this.results[0].user) {
        return this.results[0].user.username
      }
      return null
    },
    formatDateTime(dateTime) {
      if (!dateTime) return '-'
      const date = new Date(dateTime)
      const currentLang = this.$i18n?.locale || 'en'
      const localeMap = {
        'ko': 'ko-KR',
        'en': 'en-US',
        'es': 'es-ES',
        'zh': 'zh-CN',
        'ja': 'ja-JP'
      }
      const locale = localeMap[currentLang] || 'en-US'
      return date.toLocaleString(locale, {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    },
    formatTime(seconds) {
      if (!seconds) {
        const currentLang = this.$i18n?.locale || 'en'
        if (currentLang === 'ko') return '0초'
        else if (currentLang === 'ja') return '0秒'
        else if (currentLang === 'zh') return '0秒'
        else if (currentLang === 'es') return '0s'
        else return '0s'
      }
      
      const currentLang = this.$i18n?.locale || 'en'
      const hours = Math.floor(seconds / 3600)
      const minutes = Math.floor((seconds % 3600) / 60)
      const secs = seconds % 60
      
      if (currentLang === 'ko') {
        if (hours > 0) {
          return `${hours}시간 ${minutes}분 ${secs}초`
        } else if (minutes > 0) {
          return `${minutes}분 ${secs}초`
        } else {
          return `${secs}초`
        }
      } else if (currentLang === 'ja') {
        if (hours > 0) {
          return `${hours}時間 ${minutes}分 ${secs}秒`
        } else if (minutes > 0) {
          return `${minutes}分 ${secs}秒`
        } else {
          return `${secs}秒`
        }
      } else if (currentLang === 'zh') {
        if (hours > 0) {
          return `${hours}小时 ${minutes}分 ${secs}秒`
        } else if (minutes > 0) {
          return `${minutes}分 ${secs}秒`
        } else {
          return `${secs}秒`
        }
      } else if (currentLang === 'es') {
        if (hours > 0) {
          return `${hours}h ${minutes}m ${secs}s`
        } else if (minutes > 0) {
          return `${minutes}m ${secs}s`
        } else {
          return `${secs}s`
        }
      } else {
        // English
        if (hours > 0) {
          return `${hours}h ${minutes}m ${secs}s`
        } else if (minutes > 0) {
          return `${minutes}m ${secs}s`
        } else {
          return `${secs}s`
        }
      }
    },
    getAccuracyClass(accuracy) {
      if (accuracy >= 80) return 'text-success fw-bold'
      if (accuracy >= 60) return 'text-warning fw-bold'
      return 'text-danger fw-bold'
    },
    goToPage(page) {
      if (page < 1 || page > this.totalPages) return
      this.$router.push({
        path: this.$route.path,
        query: { ...this.$route.query, page }
      }).then(() => {
        this.loadResults()
      })
    },
    goBack() {
      if (this.exam && this.exam.id) {
        this.$router.push(`/exam-detail/${this.exam.id}`)
      } else {
        this.$router.go(-1)
      }
    },
    /**
     * 공유 모달 열기
     */
    async openShareModal(result) {
      this.selectedResult = result
      this.showShareModal = true
      
      // 연결된 스터디 로드
      await this.loadConnectedStudies()
    },
    /**
     * 연결된 스터디 로드
     */
    async loadConnectedStudies() {
      const examId = this.$route.params.examId
      if (!examId) {
        this.connectedStudies = []
        return
      }

      try {
        const response = await api.get(`/api/exam/${examId}/connected-studies/`)
        if (response.data.success) {
          this.connectedStudies = response.data.connected_studies || []
        } else {
          this.connectedStudies = []
        }
      } catch (error) {
        console.error('연결된 스터디 로드 실패:', error)
        this.connectedStudies = []
      }
    },
    /**
     * 스터디 멤버 로드
     */
    async loadStudyMembers() {
      if (!this.selectedStudyId) {
        this.studyMembers = []
        this.selectedMemberIds = []
        return
      }

      try {
        // studyId를 숫자로 변환 (API가 숫자를 기대하는 경우)
        const studyId = Number(this.selectedStudyId) || this.selectedStudyId
        debugLog('스터디 멤버 로드 시작:', { 
          selectedStudyId: this.selectedStudyId, 
          studyId: studyId,
          type: typeof this.selectedStudyId 
        })
        const response = await api.get(`/api/studies/${studyId}/members/`)
        debugLog('스터디 멤버 응답:', response.data)
        // 활성화된 멤버만 필터링
        this.studyMembers = (response.data || []).filter(member => member.is_active === true)
        debugLog('필터링된 멤버:', this.studyMembers)
        debugLog('이메일이 있는 멤버:', this.membersWithEmail)
        this.selectedMemberIds = []
      } catch (error) {
        console.error('스터디 멤버 로드 실패:', error)
        debugLog('스터디 멤버 로드 실패:', error)
        this.studyMembers = []
        this.selectedMemberIds = []
      }
    },
    /**
     * 전체 멤버 선택
     */
    selectAllMembers() {
      this.selectedMemberIds = this.membersWithEmail.map(m => m.id)
    },
    /**
     * 전체 멤버 해제
     */
    deselectAllMembers() {
      this.selectedMemberIds = []
    },
    /**
     * 공유 이메일 전송
     */
    async sendShareEmails() {
      if (!this.selectedResult || !this.selectedStudyId || this.selectedMemberIds.length === 0) {
        return
      }

      this.isSendingEmails = true

      try {
        const resultUrl = `${window.location.origin}/voice-interview-result/${this.selectedResult.id}`
        
        const response = await api.post('/api/voice-interview-result/share/', {
          result_id: this.selectedResult.id,
          exam_id: this.$route.params.examId,
          study_id: this.selectedStudyId,
          member_ids: this.selectedMemberIds,
          share_link: resultUrl
        })

        if (response.data.success) {
          if (this.$toast) {
            this.$toast.success(
              this.$t('voiceInterview.share.success') || 
              `${this.selectedMemberIds.length}명에게 이메일이 전송되었습니다.`
            )
          }
          this.closeShareModal()
        } else {
          if (this.$toast) {
            this.$toast.error(
              response.data.error || 
              this.$t('voiceInterview.share.error') || 
              '이메일 전송에 실패했습니다.'
            )
          }
        }
      } catch (error) {
        console.error('이메일 전송 실패:', error)
        if (this.$toast) {
          this.$toast.error(
            error.response?.data?.error || 
            this.$t('voiceInterview.share.error') || 
            '이메일 전송에 실패했습니다.'
          )
        }
      } finally {
        this.isSendingEmails = false
      }
    },
    /**
     * 공유 모달 닫기
     */
    closeShareModal() {
      this.showShareModal = false
      this.selectedResult = null
      this.selectedStudyId = null
      this.studyMembers = []
      this.selectedMemberIds = []
    },
    /**
     * 전체 선택/해제
     */
    toggleSelectAll(event) {
      if (event.target.checked) {
        // 모든 결과 선택
        this.selectedResults = this.results.map(result => result.id)
      } else {
        // 모든 선택 해제
        this.selectedResults = []
      }
    },
    /**
     * 선택된 결과 삭제
     */
    async deleteSelectedResults() {
      if (!this.selectedResults || this.selectedResults.length === 0) {
        return
      }

      const examId = this.$route.params.examId
      if (!examId) {
        if (this.$toast) {
          this.$toast.error(this.$t('voiceInterview.resultsList.noExamId') || '시험 ID가 없습니다.')
        }
        return
      }

      // 확인 모달 표시
      this.showDeleteConfirmModal = true
    },
    /**
     * 삭제 확인 후 실제 삭제 수행
     */
    async confirmDelete() {
      this.showDeleteConfirmModal = false
      this.isDeleting = true

      const examId = this.$route.params.examId
      if (!examId) {
        if (this.$toast) {
          this.$toast.error(this.$t('voiceInterview.resultsList.noExamId') || '시험 ID가 없습니다.')
        }
        this.isDeleting = false
        return
      }

      try {
        const response = await api.delete('/api/voice-interview-results/delete/', {
          data: {
            result_ids: this.selectedResults,
            exam_id: examId
          }
        })

        if (response.data.success) {
          // 성공 메시지
          if (this.$toast) {
            this.$toast.success(
              response.data.message || 
              this.$t('voiceInterview.resultsList.deleteSuccess', { 
                count: response.data.deleted_count 
              }) || 
              `${response.data.deleted_count}개의 결과가 삭제되었습니다.`
            )
          }

          // 선택 초기화
          this.selectedResults = []

          // 결과 목록 새로고침
          await this.loadResults()
        } else {
          throw new Error(response.data.error || '삭제 실패')
        }
      } catch (error) {
        console.error('결과 삭제 실패:', error)
        const errorMessage = error.response?.data?.error || 
                           error.message || 
                           this.$t('voiceInterview.resultsList.deleteError') || 
                           '결과 삭제 중 오류가 발생했습니다.'
        
        this.$toast?.error?.(errorMessage)
      } finally {
        this.isDeleting = false
      }
    },
    /**
     * 삭제 취소
     */
    cancelDelete() {
      this.showDeleteConfirmModal = false
    },
    /**
     * 공유를 위한 스터디 생성 (Exam 이름으로)
     */
    async createStudyForSharing() {
      const examId = this.$route.params.examId
      if (!examId) {
        this.$toast?.error?.(this.$t('voiceInterview.share.noExamId') || '시험 ID가 없습니다.')
        return
      }

      this.isCreatingStudy = true

      try {
        // 시험 정보 가져오기
        const examResponse = await api.get(`/api/exam/${examId}/`)
        const exam = examResponse.data

        // 사용자 프로필 언어 가져오기 (기본값은 'en')
        const currentLang = await this.getUserProfileLanguage()

        // 스터디와 Task 생성
        const study = await createStudyAndTaskForSharing(this, exam, currentLang)

        debugLog('✅ 스터디 생성 완료:', study)

        // 성공 메시지 표시
        if (this.$toast) {
          this.$toast.success(
            this.$t('voiceInterview.share.studyCreated') || 
            '그룹이 생성되었습니다.'
          )
        }

        // 연결된 스터디 목록 새로고침
        await this.loadConnectedStudies()

        // 생성된 스터디 자동 선택
        if (study && study.id) {
          this.selectedStudyId = study.id
          await this.loadStudyMembers()
        }
      } catch (error) {
        console.error('스터디 생성 실패:', error)
        let errorMessage = this.$t('voiceInterview.share.studyCreationFailed') || '그룹 생성에 실패했습니다.'
        
        if (error.response?.status === 400 && error.response?.data?.error) {
          errorMessage = error.response.data.error
        } else if (error.response?.status === 500) {
          // 서버 에러인 경우 더 자세한 메시지
          if (error.response?.data?.detail) {
            errorMessage = error.response.data.detail
          } else {
            errorMessage = this.$t('voiceInterview.share.studyCreationFailed') || '그룹 생성에 실패했습니다. 서버 오류가 발생했습니다.'
          }
        } else if (error.response?.data?.study) {
          // 스터디는 생성되었지만 Task 생성 실패
          errorMessage = this.$t('voiceInterview.share.taskCreationFailed') || 'Task 생성에 실패했습니다.'
        } else if (error.message) {
          errorMessage = error.message
        }

        // Toast가 있으면 사용, 없으면 console.error만 출력 (alert 제거)
        if (this.$toast) {
          this.$toast.error(errorMessage)
        } else {
          console.error('Toast가 없어 메시지를 표시할 수 없습니다:', errorMessage)
          // alert 대신 console.error만 사용
        }
      } finally {
        this.isCreatingStudy = false
      }
    },
    /**
     * 사용자 프로필 언어 가져오기 (캐시 사용)
     */
    async getUserProfileLanguage() {
      // 캐시된 언어가 있으면 사용
      if (this.userProfileLanguage) {
        return this.userProfileLanguage
      }
      
      try {
        // i18n locale을 먼저 확인 (이미 설정된 경우)
        if (this.$i18n && this.$i18n.locale) {
          this.userProfileLanguage = this.$i18n.locale
          return this.userProfileLanguage
        }
        
        // API에서 프로필 언어 가져오기
        const response = await api.get('/api/user-profile/')
        const language = response.data?.language || 'en'
        this.userProfileLanguage = language
        return language
      } catch (error) {
        console.error('사용자 프로필 언어 가져오기 실패:', error)
        // 기본 언어는 'en'
        this.userProfileLanguage = 'en'
        return 'en'
      }
    },

    /**
     * 스터디 제목을 사용자 프로필 언어에 맞게 반환
     */
    getStudyTitle(study) {
      if (!study) return '제목 없음'
      return getLocalizedContentWithI18n(
        study,
        'title',
        this.$i18n,
        this.userProfileLanguage,
        '제목 없음'
      )
    }
  }
}
</script>

<style scoped>
.voice-interview-results-list {
  padding: 20px 0;
  min-height: 100vh;
  background-color: #f5f5f5;
}

.card {
  border: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
}

.card-header {
  background-color: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
  padding: 15px 20px;
}

.card-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #333;
}

.table th {
  background-color: #f8f9fa;
  font-weight: 600;
  border-bottom: 2px solid #dee2e6;
}

.table tbody tr:hover {
  background-color: #f8f9fa;
}

.pagination {
  margin-top: 20px;
}

/* 공유 모달 스타일 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.share-modal .modal-header {
  padding: 20px;
  border-bottom: 1px solid #dee2e6;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.share-modal .modal-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.share-modal .modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6c757d;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.share-modal .modal-close:hover {
  color: #000;
}

.share-modal .modal-body {
  padding: 20px;
}

.share-modal .modal-footer {
  padding: 15px 20px;
  border-top: 1px solid #dee2e6;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.btn-group {
  display: flex;
  gap: 5px;
}

/* 삭제 확인 모달 스타일 */
.delete-confirm-modal {
  max-width: 500px;
}

.delete-confirm-modal .modal-header {
  padding: 20px;
  border-bottom: 1px solid #dee2e6;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.delete-confirm-modal .modal-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #333;
}

.delete-confirm-modal .modal-body {
  padding: 20px;
}

.delete-confirm-modal .modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6c757d;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.delete-confirm-modal .modal-close:hover {
  color: #000;
}

.delete-confirm-modal .modal-footer {
  padding: 15px 20px;
  border-top: 1px solid #dee2e6;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

@media (max-width: 768px) {
  /* Back 버튼을 원형 버튼으로 */
  .btn-secondary {
    padding: 0 !important;
    width: 40px !important;
    height: 40px !important;
    border-radius: 50% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    min-width: auto !important;
    font-size: 0 !important;
    position: relative;
  }
  
  .btn-secondary i,
  .btn-secondary > * {
    display: none !important;
  }
  
  .btn-secondary::after {
    content: '\f060'; /* Font Awesome arrow-left icon */
    font-family: 'Font Awesome 5 Free';
    font-weight: 900;
    font-size: 16px !important;
    color: #fff;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
  }
  
  /* View 버튼을 원형 버튼으로 */
  .btn-sm.btn-primary {
    padding: 0 !important;
    width: 32px !important;
    height: 32px !important;
    border-radius: 50% !important;
    min-width: auto !important;
    font-size: 0 !important;
    position: relative;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
  }
  
  .btn-sm.btn-primary i {
    margin: 0 !important;
    margin-right: 0 !important;
    margin-left: 0 !important;
    font-size: 14px !important;
    color: #fff;
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
  }
  
  .btn-sm.btn-primary .me-1 {
    margin-right: 0 !important;
    margin-left: 0 !important;
  }
  
  .btn-sm.btn-primary > *:not(i) {
    display: none !important;
  }
  
  /* Share Results 버튼을 원형 버튼으로 */
  .btn-sm.btn-info {
    padding: 0 !important;
    width: 32px !important;
    height: 32px !important;
    border-radius: 50% !important;
    min-width: auto !important;
    font-size: 0 !important;
    position: relative;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
  }
  
  .btn-sm.btn-info i {
    margin: 0 !important;
    margin-right: 0 !important;
    margin-left: 0 !important;
    font-size: 14px !important;
    color: #fff;
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
  }
  
  .btn-sm.btn-info .me-1 {
    margin-right: 0 !important;
    margin-left: 0 !important;
  }
  
  .btn-sm.btn-info > *:not(i) {
    display: none !important;
  }
  
  /* Select All 버튼을 원형 버튼으로 */
  .btn-sm.btn-outline-primary {
    padding: 0 !important;
    width: 32px !important;
    height: 32px !important;
    border-radius: 50% !important;
    min-width: auto !important;
    font-size: 0 !important;
    position: relative;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
  }
  
  .btn-sm.btn-outline-primary::after {
    content: '\f046'; /* Font Awesome check-square icon */
    font-family: 'Font Awesome 5 Free';
    font-weight: 900;
    font-size: 14px !important;
    color: #007bff;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
  }
  
  .btn-sm.btn-outline-primary > * {
    display: none !important;
  }
  
  /* Deselect All 버튼을 원형 버튼으로 */
  .btn-sm.btn-outline-secondary {
    padding: 0 !important;
    width: 32px !important;
    height: 32px !important;
    border-radius: 50% !important;
    min-width: auto !important;
    font-size: 0 !important;
    position: relative;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
  }
  
  .btn-sm.btn-outline-secondary::after {
    content: '\f096'; /* Font Awesome square icon */
    font-family: 'Font Awesome 5 Free';
    font-weight: 900;
    font-size: 14px !important;
    color: #6c757d;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
  }
  
  .btn-sm.btn-outline-secondary > * {
    display: none !important;
  }
  
  /* Delete 버튼을 원형 버튼으로 (카드 헤더) */
  .delete-selected-btn {
    padding: 0 !important;
    width: 40px !important;
    height: 40px !important;
    border-radius: 50% !important;
    min-width: auto !important;
    font-size: 0 !important;
    position: relative;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
  }
  
  .delete-selected-btn i {
    margin: 0 !important;
    margin-right: 0 !important;
    margin-left: 0 !important;
    font-size: 16px !important;
    color: #fff;
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
  }
  
  .delete-selected-btn .me-1 {
    margin-right: 0 !important;
    margin-left: 0 !important;
  }
  
  .delete-selected-btn span {
    display: none !important;
  }
  
  /* 모달의 Delete 버튼도 원형으로 */
  .modal-footer .btn-danger {
    padding: 0 !important;
    width: 40px !important;
    height: 40px !important;
    border-radius: 50% !important;
    min-width: auto !important;
    font-size: 0 !important;
    position: relative;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
  }
  
  .modal-footer .btn-danger i {
    margin: 0 !important;
    margin-right: 0 !important;
    margin-left: 0 !important;
    font-size: 16px !important;
    color: #fff;
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
  }
  
  .modal-footer .btn-danger .me-1 {
    margin-right: 0 !important;
    margin-left: 0 !important;
  }
  
  .modal-footer .btn-danger span {
    display: none !important;
  }
}
</style>

