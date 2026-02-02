<template>
  <div class="question-files-modern">
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
    
    <!-- Modal Confirm -->
    <div v-if="showModal" class="modal-overlay" @click="cancelModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h5 class="modal-title">
            <i :class="modalIcon"></i>
            {{ modalTitle }}
          </h5>
          <button class="modal-close" @click="cancelModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <p class="mb-0">{{ modalMessage }}</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="cancelModal">
            {{ modalCancelText }}
          </button>
          <button class="btn" :class="modalConfirmButtonClass" @click="confirmModal">
            <i class="fas fa-check me-1"></i>
            {{ modalConfirmText }}
          </button>
        </div>
      </div>
    </div>
    
    <!-- 번역 로딩 중일 때 로딩 표시 -->
    <div v-if="!translationsLoaded" class="loading-container">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">{{ $t('common.loadingTranslations') }}</span>
      </div>
      <p class="mt-3">{{ $t('common.loadingTranslationData') }}</p>
    </div>
    
    <!-- 번역이 로드된 후에만 컨텐츠 표시 -->
    <div v-else class="files-container">
      <!-- Top Header -->
      <div class="top-header">
        <div class="header-actions">
          <router-link to="/text-to-questions" class="action-btn action-btn-info">
            <i class="fas fa-magic"></i>
            <span class="action-label">{{ translations.textToQuestions }}</span>
          </router-link>
          <button 
            @click="toggleUploadForm" 
            class="action-btn action-btn-primary"
            v-if="!showUploadForm && isAuthenticated"
          >
            <i class="fas fa-upload"></i>
            <span class="action-label">{{ translations.uploadFile }}</span>
          </button>
          <router-link to="/exam-management" class="action-btn action-btn-success">
            <i class="fas fa-clipboard-list"></i>
            <span class="action-label">{{ translations.examManagement }}</span>
          </router-link>
        </div>
      </div>

      <!-- Page Title -->
      <div class="page-title">
        <h1>{{ translations.pageTitle }}</h1>
      </div>

      <!-- File Upload Section -->
      <div class="upload-section" v-if="showUploadForm">
        <div class="upload-card">
          <div class="card-header-modern">
            <h3>{{ translations.uploadTitle }}</h3>
            <button @click="toggleUploadForm" class="card-action-btn">
              <i class="fas fa-times"></i>
              <span class="action-label">{{ translations.uploadCancel }}</span>
            </button>
          </div>
          
          <div class="upload-content">
            <div class="upload-form">
              <div class="upload-input">
                <input 
                  type="file" 
                  class="form-control" 
                  @change="handleFileSelect" 
                  accept=".xls,.xlsx"
                  ref="fileInput"
                >
              </div>
              
              <!-- Public 설정 -->
              <div class="upload-options">
                <div class="form-check">
                  <input 
                    class="form-check-input" 
                    type="checkbox" 
                    id="isPublic" 
                    v-model="isPublic"
                    :disabled="isUploading"
                  >
                  <label class="form-check-label" for="isPublic">
                    {{ translations.publicFile }}
                  </label>
                </div>
              </div>
              
              <!-- Tags Section -->
              <div class="upload-input" style="flex: 1; min-width: 100%;">
                <label class="form-label">{{ $t('studyDetail.tagManagement') || '태그 관리' }}</label>
                <div class="d-flex align-items-center justify-content-end gap-2 flex-wrap">
                  <!-- Selected Tags Display -->
                  <div v-if="newFileTags.length > 0" class="d-flex align-items-center flex-wrap gap-2">
                    <span 
                      v-for="tagId in newFileTags" 
                      :key="tagId"
                      class="badge bg-primary"
                    >
                      {{ getSelectedTagName(tagId) }}
                      <button 
                        @click="removeFileTag(tagId)" 
                        class="btn-close btn-close-white ms-1" 
                        style="font-size: 0.7em;"
                      ></button>
                    </span>
                  </div>
                  <button 
                    @click="openTagModal" 
                    type="button"
                    class="btn btn-outline-primary btn-sm"
                    :disabled="isUploading"
                  >
                    <i class="fas fa-tags"></i>
                    {{ $t('tagFilterModal.title') || '태그로 검색' }}
                    <span v-if="newFileTags.length > 0" class="badge bg-primary ms-2">{{ newFileTags.length }}</span>
                  </button>
                </div>
              </div>
              
              <div class="upload-actions">
                <button 
                  @click="uploadFile" 
                  class="action-btn action-btn-success"
                  :disabled="!selectedFile || isUploading || isPrivateFile || !canUpload"
                  :title="isPrivateFile ? $t('question.file.private.warning', { filename: selectedFile ? selectedFile.name : '' }) : ''"
                  @mouseenter="logButtonState"
                >
                  <i v-if="isUploading" class="fas fa-spinner fa-spin"></i>
                  <i v-else class="fas fa-upload"></i>
                  <span class="action-label">{{ isUploading ? translations.uploading : translations.uploadUpload }}</span>
                </button>
                <button 
                  @click="cancelUpload" 
                  class="action-btn action-btn-secondary"
                >
                  <i class="fas fa-times"></i>
                  <span class="action-label">{{ translations.uploadCancel }}</span>
                </button>
              </div>
            </div>
            
            <div v-if="uploadMessage" class="upload-message" :class="uploadMessageType">
              {{ uploadMessage }}
            </div>
            
            <!-- File Format Example -->
            <div class="format-example">
              <div class="example-header">
                <h4>{{ translations.uploadFileFormatExample }}</h4>
                <div class="sample-downloads">
                  <a :href="sampleXlsxPath" download class="action-btn action-btn-outline">
                    <i class="fas fa-download"></i>
                    <span class="action-label">{{ $t('questionFiles.upload.sampleXlsx') }}</span>
                  </a>

                </div>
              </div>
              
              <div class="example-info">
                <div class="info-alert">
                  <i class="fas fa-info-circle"></i>
                  <strong>{{ translations.uploadAutoCorrect }}</strong> {{ translations.uploadAutoCorrectDescription }}
                </div>
                
                <div class="supported-formats">
                  <strong>{{ translations.uploadSupportedFormats }}</strong>
                </div>
              </div>
              
              <div class="example-table">
                <div class="table-header">
                  <div class="table-column">{{ translations.questionId }}</div>
                  <div class="table-column">{{ translations.title }}</div>
                  <div class="table-column">{{ translations.questionContent }}</div>
                  <div class="table-column">{{ translations.answer }}</div>
                  <div class="table-column">{{ translations.explanation }}</div>
                  <div class="table-column">{{ translations.difficulty }}</div>
                  <div class="table-column">{{ translations.url }}</div>
                  <div class="table-column">{{ translations.groupId }}</div>
                </div>
                
                <div class="table-body">
                  <div class="table-row">
                    <div class="table-cell">1</div>
                    <div class="table-cell">{{ translations.example1Title }}</div>
                    <div class="table-cell">{{ translations.example1Content }}</div>
                    <div class="table-cell">kubectl run nginx --image=nginx</div>
                    <div class="table-cell">This command creates a new Pod running nginx container</div>
                    <div class="table-cell">Easy</div>
                    <div class="table-cell url-cell">https://kubernetes.io/docs/concepts/workloads/pods/</div>
                    <div class="table-cell">2025/01/15</div>
                  </div>
                  <div class="table-row">
                    <div class="table-cell">2</div>
                    <div class="table-cell">{{ translations.example2Title }}</div>
                    <div class="table-cell">{{ translations.example2Content }}</div>
                    <div class="table-cell">kubectl create deployment nginx --image=nginx</div>
                    <div class="table-cell">This command creates a Deployment that manages Pods</div>
                    <div class="table-cell">Medium</div>
                    <div class="table-cell url-cell">https://kubernetes.io/docs/concepts/services-networking/service/</div>
                    <div class="table-cell">2025/01/20</div>
                  </div>
                  <div class="table-row">
                    <div class="table-cell">3</div>
                    <div class="table-cell">{{ translations.example3Title }}</div>
                    <div class="table-cell">{{ translations.example3Content }}</div>
                    <div class="table-cell">kubectl expose deployment nginx --port=80</div>
                    <div class="table-cell">This command exposes the deployment as a Service</div>
                    <div class="table-cell">Hard</div>
                    <div class="table-cell url-cell">https://kubernetes.io/docs/concepts/services-networking/service/</div>
                    <div class="table-cell">2025/01/25</div>
                  </div>
                </div>
              </div>
              
              <div class="format-notes">
                <small class="text-muted">
                  <strong>{{ translations.uploadRequiredColumns }}</strong><br>
                  <strong>{{ translations.uploadOptionalColumns }}</strong><br>
                  <strong>{{ translations.uploadSupportedFormats }}</strong><br>
  
                </small>
              </div>
            </div>
          </div>
          <button 
            @click="toggleUploadForm" 
            class="action-btn action-btn-primary"
            v-if="!showUploadForm && isAuthenticated"
          >
            <i class="fas fa-upload"></i>
            <span class="action-label">{{ translations.uploadFile }}</span>
          </button>
        </div>
      </div>

      <!-- Files List Section -->
      <div class="card-modern files-list-card">
        <!-- Filter Section -->
        <div class="search-filters mb-3">
          <div class="row filter-row" :class="{ 'mobile-hidden': !showFilterRow }">
            <div class="col-md-3">
              <div class="form-group">
                <input 
                  v-model="searchFilters.fileName"
                  @input="handleSearchInput('fileName', $event.target.value)"
                  type="text" 
                  class="form-control file-name-search-input" 
                  :placeholder="$t('questionFiles.filter.fileNamePlaceholder') || '파일명으로 검색...'"
                >
              </div>
            </div>
            <div class="col-md-2" v-if="isAuthenticated">
              <div class="form-group">
                <select v-model="searchFilters.uploader" @change="handleFilterChange" class="form-control">
                  <option value="">{{ translations.filterAll || '전체' }}</option>
                  <option value="my">{{ $t('questionFiles.filter.myFiles') || '내 파일' }}</option>
                  <option value="others" v-if="isAdmin">{{ $t('questionFiles.filter.othersFiles') || '다른 사용자' }}</option>
                </select>
              </div>
            </div>
            <div class="col-md-2" v-if="isAuthenticated">
              <div class="form-group">
                <select v-model="searchFilters.isPublic" @change="handleFilterChange" class="form-control">
                  <option value="">{{ translations.filterAll || '전체' }}</option>
                  <option value="true">{{ translations.filterPublic || '공개' }}</option>
                  <option value="false">{{ translations.filterPrivate || '비공개' }}</option>
                </select>
              </div>
            </div>
            <div class="col-md-2" v-if="!isAuthenticated">
              <div class="form-group">
                <select v-model="searchFilters.isPublic" @change="handleFilterChange" class="form-control">
                  <option value="">{{ translations.filterAll || '전체' }}</option>
                  <option value="true">{{ translations.filterPublic || '공개' }}</option>
                </select>
              </div>
            </div>
            <div class="col-md-3">
              <div class="form-group">
                <div class="d-flex gap-2">
                  <input 
                    v-model="searchFilters.dateFrom"
                    @change="handleFilterChange"
                    type="date" 
                    class="form-control form-control-sm"
                  >
                  <input 
                    v-model="searchFilters.dateTo"
                    @change="handleFilterChange"
                    type="date" 
                    class="form-control form-control-sm"
                  >
                </div>
              </div>
            </div>
            <div class="col-md-2 d-flex justify-content-end gap-2">
              <!-- Tag Filter Button -->
              <button 
                @click="openTagFilterModal" 
                class="btn btn-outline-primary btn-sm tag-filter-btn"
                style="height: 38px; display: flex; align-items: center; align-self: flex-end; margin-bottom: 25px;"
              >
                <i class="fas fa-tags"></i>
                {{ $t('examManagement.tagFilter') || '태그 필터' }}
                <span v-if="selectedTagFilters.length > 0" class="badge bg-primary ms-1">{{ selectedTagFilters.length }}</span>
              </button>
            </div>
          </div>
          <div class="filter-actions mb-2">
            <button @click="toggleFilterRow" class="action-btn action-btn-info mobile-filter-toggle">
              <i class="fas fa-filter"></i>
              <span class="action-label">{{ $t('examDetail.filter') || 'Filter' }}</span>
            </button>
          </div>
        </div>
        
        <!-- Files Table -->
        <div class="files-table">
          <div class="table-header">
            <div class="table-column" @click="sortBy('name')">
              {{ translations.tableFilename }}
              <i :class="getSortIcon('name')" class="sort-icon"></i>
            </div>
            <div class="table-column" @click="sortBy('size')">
              {{ translations.tableSize }}
              <i :class="getSortIcon('size')" class="sort-icon"></i>
            </div>
            <div class="table-column" @click="sortBy('modified')">
              {{ translations.tableModified }}
              <i :class="getSortIcon('modified')" class="sort-icon"></i>
            </div>
            <div class="table-column" @click="sortBy('max_questions')">
              {{ translations.tableMaxQuestions }}
              <i :class="getSortIcon('max_questions')" class="sort-icon"></i>
            </div>
            <div class="table-column">{{ translations.tablePublicStatus }}</div>
            <div class="table-column" v-if="isAdmin || isAuthenticated">Actions</div>
          </div>
          
          <div class="table-body">
            <div v-if="loading" class="loading-files">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">{{ translations.messagesLoading }}</span>
              </div>
              <p class="mt-3">{{ translations.messagesLoading }}</p>
            </div>
            
            <div v-else-if="files.length === 0" class="no-files">
              <i class="fas fa-folder-open"></i>
              <p>{{ translations.messagesNoFiles }}</p>
              <small>{{ translations.uploadFirst }}</small>
            </div>
            
            <template v-else>
              <div v-for="file in sortedFiles" :key="file.name" class="table-row">
                <div class="table-cell">{{ file.name }}</div>
                <div class="table-cell">{{ formatSize(file.size) }}</div>
                <div class="table-cell">{{ formatDate(file.modified) }}</div>
                <div class="table-cell">{{ file.max_questions || 0 }}{{ $t('questionFiles.table.count') }}</div>
                <div class="table-cell">
                  <span class="status-badge" :class="getFilePublicStatus(file) ? 'status-public' : 'status-private'">
                    {{ getFilePublicStatus(file) ? translations.tablePublic : translations.tablePrivate }}
                  </span>
                </div>
                <div class="table-cell" v-if="isAdmin || isAuthenticated">
                  <div class="action-buttons">
                    <button class="action-btn action-btn-outline" @click="downloadFile(file)">
                      <i class="fas fa-download"></i>
                      <span class="action-label">{{ translations.tableDownload }}</span>
                    </button>
                    <button v-if="canEditFile(file)" class="action-btn action-btn-secondary" @click="toggleFilePublicStatus(file)">
                      <i class="fas fa-edit"></i>
                      <span class="action-label">{{ translations.tableEdit }}</span>
                    </button>
                    <button class="action-btn action-btn-danger" @click="deleteFile(file)" v-if="canDeleteFile(file)">
                      <i class="fas fa-trash"></i>
                      <span class="action-label">{{ translations.tableDelete }}</span>
                    </button>
                  </div>
                </div>
              </div>
            </template>
          </div>
          
          <!-- 페이지네이션 -->
          <div v-if="totalPages > 1" class="pagination-container mt-4">
            <nav aria-label="Page navigation">
              <ul class="pagination justify-content-center">
                <li class="page-item" :class="{ disabled: currentPage === 1 }">
                  <a class="page-link" href="#" @click.prevent="goToPage(1)" :aria-disabled="currentPage === 1">
                    <i class="fas fa-angle-double-left"></i>
                  </a>
                </li>
                <li class="page-item" :class="{ disabled: currentPage === 1 }">
                  <a class="page-link" href="#" @click.prevent="goToPage(currentPage - 1)" :aria-disabled="currentPage === 1">
                    <i class="fas fa-angle-left"></i>
                  </a>
                </li>
                
                <li v-for="page in visiblePages" :key="page" class="page-item" :class="{ active: page === currentPage }">
                  <a class="page-link" href="#" @click.prevent="goToPage(page)">
                    {{ page }}
                  </a>
                </li>
                
                <li class="page-item" :class="{ disabled: currentPage === totalPages }">
                  <a class="page-link" href="#" @click.prevent="goToPage(currentPage + 1)" :aria-disabled="currentPage === totalPages">
                    <i class="fas fa-angle-right"></i>
                  </a>
                </li>
                <li class="page-item" :class="{ disabled: currentPage === totalPages }">
                  <a class="page-link" href="#" @click.prevent="goToPage(totalPages)" :aria-disabled="currentPage === totalPages">
                    <i class="fas fa-angle-double-right"></i>
                  </a>
                </li>
              </ul>
            </nav>
            <div class="pagination-info text-center mt-2">
              <small class="text-muted">
                {{ $t('questionFiles.pagination.info', { 
                  current: currentPage, 
                  total: totalPages, 
                  count: totalCount 
                }) || `페이지 ${currentPage} / ${totalPages} (총 ${totalCount}개 파일)` }}
              </small>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Tag Filter Modal for File Upload -->
    <TagFilterModal
      :show="showTagModal"
      :selectedTags="newFileTags"
      @update:show="showTagModal = $event"
      @update:selectedTags="handleTagUpdate"
      @apply="handleTagApply"
      @error="handleTagError"
      @tag-created="handleTagCreated"
    />
    
    <!-- Tag Filter Modal for Filtering -->
    <TagFilterModal
      :show="showTagFilterModal"
      :selectedTags="selectedTagFilters"
      @update:show="showTagFilterModal = $event"
      @update:selectedTags="handleTagFilterUpdate"
      @apply="handleTagFilterApply"
      @error="handleTagFilterError"
      @tag-created="handleTagCreated"
    />
  </div>
</template>

<script>
import axios from 'axios'
import { debugLog } from '@/utils/debugUtils'
import { isAdmin, hasStudyAdminRole, getCurrentUser as getCurrentUserFromPermissions } from '@/utils/permissionUtils'
import { getCurrentDomainConfig, getForcedTags } from '@/utils/domainUtils'
import TagFilterModal from '@/components/TagFilterModal.vue'

export default {
  name: 'QuestionFiles',
  components: {
    TagFilterModal
  },
  data() {
    return {
      files: [],
      loading: true,
      showUploadForm: false,
      selectedFile: null,
      uploadMessage: '',
      uploadMessageType: 'alert-info',
      sortKey: 'name',
      sortOrder: 'asc',
      publicFilter: '',
      editingFile: null,
      editingFileData: {
        is_public: true
      },
      // 번역 로딩 상태
      translationsLoaded: false,
      // Toast Notifications
      showToast: false,
      toastMessage: '',
      toastType: 'alert-info', // alert-success, alert-danger, alert-warning, alert-info
      toastIcon: 'fas fa-info-circle', // fas fa-check, fas fa-times, fas fa-exclamation-circle, fas fa-info-circle
      // Modal Confirm
      showModal: false,
      modalTitle: '',
      modalMessage: '',
      modalIcon: 'fas fa-question-circle', // fas fa-check-circle, fas fa-times-circle, fas fa-exclamation-triangle, fas fa-info-circle
      modalConfirmText: '',
      modalCancelText: '',
      modalConfirmButtonClass: 'btn-success', // btn-primary, btn-danger, btn-warning, btn-info
      // 업로드 로딩 상태
      isUploading: false,
      // 파일 공개 설정 (기본값: private)
      isPublic: false,
      // 선택된 파일이 private한 기존 파일인지 여부
      isPrivateFile: false,
      // 페이지네이션
      currentPage: 1,
      pageSize: 20,
      totalCount: 0,
      totalPages: 0,
      // Tag Management
      newFileTags: [],
      showTagModal: false,
      availableTags: [],
      // Filter
      searchFilters: {
        fileName: '',
        uploader: '',
        isPublic: '',
        dateFrom: '',
        dateTo: '',
      },
      searchDebounceTimer: null,
      // Tag Filter for filtering files
      selectedTagFilters: [],
      showTagFilterModal: false,
      // Filter row visibility
      showFilterRow: false,
    }
  },
  computed: {
    canUpload() {
      // 태그는 반드시 1개 이상 선택되어야 함
      if (!this.newFileTags || this.newFileTags.length === 0) {
        return false
      }
      return true
    },
    // 번역이 로드되지 않았을 때를 위한 fallback 텍스트
    translations() {
      // 번역 로드 상태 확인
      const isLoaded = this.$isTranslationsLoaded(this.$i18n.locale)
      
      return {
        pageTitle: isLoaded ? this.$t('questionFiles.title') : 'Quiz Files',
        uploadFile: isLoaded ? (this.$t('questionFiles.uploadFile') || '파일 업로드') : '파일 업로드',
        textToQuestions: isLoaded ? (this.$t('questionFiles.textToQuestions') || '텍스트에서 문제 생성') : '텍스트에서 문제 생성',
        examManagement: isLoaded ? (this.$t('questionFiles.examManagement') || '시험 관리') : '시험 관리',
        publicFilter: isLoaded ? (this.$t('questionFiles.publicFilter') || '공개 여부:') : '공개 여부:',
        filterAll: isLoaded ? (this.$t('questionFiles.filter.all') || '전체') : '전체',
        filterPublic: isLoaded ? (this.$t('questionFiles.filter.public') || '공개') : '공개',
        filterPrivate: isLoaded ? (this.$t('questionFiles.filter.private') || '비공개') : '비공개',
        tableFilename: isLoaded ? (this.$t('questionFiles.table.filename') || '파일명') : '파일명',
        tableSize: isLoaded ? (this.$t('questionFiles.table.size') || '크기') : '크기',
        tableModified: isLoaded ? (this.$t('questionFiles.table.modified') || 'Modified') : 'Modified',
        tableMaxQuestions: isLoaded ? (this.$t('questionFiles.table.maxQuestions') || 'Max Quizzes') : 'Max Quizzes',
        tablePublicStatus: isLoaded ? (this.$t('questionFiles.table.publicStatus') || '공개 여부') : '공개 여부',
        tableDownload: isLoaded ? (this.$t('questionFiles.table.download') || '다운로드') : '다운로드',
        tableDelete: isLoaded ? (this.$t('questionFiles.table.delete') || '삭제') : '삭제',
        tableEdit: isLoaded ? (this.$t('questionFiles.table.edit') || '수정') : '수정',
        tableSave: isLoaded ? (this.$t('questionFiles.table.save') || '저장') : '저장',
        tableCancel: isLoaded ? (this.$t('questionFiles.table.cancel') || '취소') : '취소',
        tablePublic: isLoaded ? (this.$t('questionFiles.table.public') || '공개') : '공개',
        tablePrivate: isLoaded ? (this.$t('questionFiles.table.private') || '비공개') : '비공개',
        uploadTitle: isLoaded ? (this.$t('questionFiles.upload.title') || '파일 업로드') : '파일 업로드',
        uploadUpload: isLoaded ? (this.$t('questionFiles.upload.upload') || '업로드') : '업로드',
        uploadCancel: isLoaded ? (this.$t('questionFiles.upload.cancel') || '취소') : '취소',
        uploadAutoCorrect: isLoaded ? (this.$t('questionFiles.upload.autoCorrect') || '자동 보정 기능:') : '자동 보정 기능:',
        uploadAutoCorrectDescription: isLoaded ? (this.$t('questionFiles.upload.autoCorrectDescription') || '업로드 시 컬럼 개수 불일치, 빈 행 등이 자동으로 보정됩니다.') : '업로드 시 컬럼 개수 불일치, 빈 행 등이 자동으로 보정됩니다.',
        uploadFileFormatExample: isLoaded ? (this.$t('questionFiles.upload.fileFormatExample') || '파일 구성 예시 (XLS, XLSX 지원):') : '파일 구성 예시 (XLS, XLSX 지원):',
        uploadRequiredColumns: isLoaded ? (this.$t('questionFiles.upload.requiredColumns') || `* Required Columns: ${this.translations.questionId}, ${this.translations.title}, ${this.translations.questionContent}, ${this.translations.answer}`) : `* Required Columns: ${this.translations.questionId}, ${this.translations.title}, ${this.translations.questionContent}, ${this.translations.answer}`,
        uploadOptionalColumns: isLoaded ? (this.$t('questionFiles.upload.optionalColumns') || `* Optional Columns: ${this.translations.difficulty}, ${this.translations.url}`) : `* Optional Columns: ${this.translations.difficulty}, ${this.translations.url}`,
        uploadSupportedFormats: isLoaded ? (this.$t('questionFiles.upload.supportedFormats') || '* Supported Formats: XLS, XLSX') : '* Supported Formats: XLS, XLSX',

        publicFile: isLoaded ? (this.$t('questionFiles.upload.publicFile') || '공개') : '공개',
        messagesNoFiles: isLoaded ? (this.$t('questionFiles.messages.noFiles') || '업로드된 파일이 없습니다.') : '업로드된 파일이 없습니다.',
        messagesLoading: isLoaded ? (this.$t('questionFiles.messages.loading') || 'Loading...') : 'Loading...',
        uploading: isLoaded ? (this.$t('questionFiles.upload.uploading') || '업로딩 중...') : '업로딩 중...',
        // examDetail 번역들
        questionId: isLoaded ? (this.$t('examDetail.questionId') || '문제 ID') : '문제 ID',
        title: isLoaded ? (this.$t('examDetail.title') || '제목') : '제목',
        questionContent: isLoaded ? (this.$t('examDetail.questionContent') || '문제 내용') : '문제 내용',
        answer: isLoaded ? (this.$t('examDetail.answer') || '답') : '답',
        explanation: isLoaded ? (this.$t('examDetail.explanation') || '설명') : '설명',
        difficulty: isLoaded ? (this.$t('examDetail.difficulty') || '난이도') : '난이도',
        url: isLoaded ? (this.$t('examDetail.url') || 'URL') : 'URL',
        groupId: isLoaded ? (this.$t('examDetail.groupId') || '그룹 ID') : '그룹 ID',
        // 예시 텍스트들
        example1Title: isLoaded ? (this.$t('questionFiles.upload.example1.title') || 'Kubernetes Pod 생성') : 'Kubernetes Pod 생성',
        example1Content: isLoaded ? (this.$t('questionFiles.upload.example1.content') || 'nginx 컨테이너를 실행하는 Pod를 생성하는 명령어는?') : 'nginx 컨테이너를 실행하는 Pod를 생성하는 명령어는?',
        example2Title: isLoaded ? (this.$t('questionFiles.upload.example2.title') || 'Kubernetes Deployment 생성') : 'Kubernetes Deployment 생성',
        example2Content: isLoaded ? (this.$t('questionFiles.upload.example2.content') || 'Pod를 관리하는 Deployment를 생성하는 명령어는?') : 'Pod를 관리하는 Deployment를 생성하는 명령어는?',
        example3Title: isLoaded ? (this.$t('questionFiles.upload.example3.title') || 'Kubernetes Service 생성') : 'Kubernetes Service 생성',
        example3Content: isLoaded ? (this.$t('questionFiles.upload.example3.content') || 'Deployment를 Service로 노출하는 명령어는?') : 'Deployment를 Service로 노출하는 명령어는?',
        // 메시지들
        uploadFirst: isLoaded ? (this.$t('questionFiles.messages.uploadFirst') || '먼저 파일을 업로드해주세요.') : '먼저 파일을 업로드해주세요.',
        uploadSuccess: isLoaded ? (this.$t('questionFiles.messages.uploadSuccess') || '파일 업로드가 완료되었습니다.') : '파일 업로드가 완료되었습니다.',
        uploadError: isLoaded ? (this.$t('questionFiles.messages.uploadError') || '업로드 오류:') : '업로드 오류:',
        uploadFailed: isLoaded ? (this.$t('questionFiles.messages.uploadFailed') || '파일 업로드에 실패했습니다.') : '파일 업로드에 실패했습니다.',
        deleteSuccess: isLoaded ? (this.$t('questionFiles.messages.deleteSuccess') || '파일이 삭제되었습니다.') : '파일이 삭제되었습니다.',
        // 알림 메시지들
        selectFile: isLoaded ? (this.$t('questionFiles.alerts.selectFile') || '파일을 선택해주세요.') : '파일을 선택해주세요.',
        downloadError: isLoaded ? (this.$t('questionFiles.alerts.downloadError') || '다운로드 중 오류가 발생했습니다.') : '다운로드 중 오류가 발생했습니다.',
        noDeletePermission: isLoaded ? (this.$t('questionFiles.alerts.noDeletePermission') || '파일을 삭제할 권한이 없습니다.') : '파일을 삭제할 권한이 없습니다.',
        confirmDeleteTitle: isLoaded ? (this.$t('questionFiles.alerts.confirmDeleteTitle') || '파일 삭제 확인') : '파일 삭제 확인',
        confirmDeleteMessage: isLoaded ? (this.$t('questionFiles.alerts.confirmDeleteMessage') || '정말로 이 파일을 삭제하시겠습니까?') : '정말로 이 파일을 삭제하시겠습니까?',
        delete: isLoaded ? (this.$t('questionFiles.alerts.delete') || '삭제') : '삭제',
        cancel: isLoaded ? (this.$t('questionFiles.alerts.cancel') || '취소') : '취소',
        deleteError: isLoaded ? (this.$t('questionFiles.alerts.deleteError') || '파일 삭제 중 오류가 발생했습니다.') : '파일 삭제 중 오류가 발생했습니다.',
        noEditPermission: isLoaded ? (this.$t('questionFiles.alerts.noEditPermission') || '파일을 편집할 권한이 없습니다.') : '파일을 편집할 권한이 없습니다.',
        publicStatusUpdated: isLoaded ? (this.$t('questionFiles.alerts.publicStatusUpdated') || '파일 공개 상태가 업데이트되었습니다.') : '파일 공개 상태가 업데이트되었습니다.',
        publicStatusUpdateFailed: isLoaded ? (this.$t('questionFiles.alerts.publicStatusUpdateFailed') || '파일 공개 상태 업데이트에 실패했습니다.') : '파일 공개 상태 업데이트에 실패했습니다.'
      }
    },
    sortedFiles() {
      // files가 배열이 아닌 경우 빈 배열로 처리
      if (!Array.isArray(this.files)) {
        debugLog('files가 배열이 아닙니다:', this.files, 'warn')
        return []
      }
      
      let filteredFiles = [...this.files]
      
      // 파일명 필터 적용
      if (this.searchFilters.fileName) {
        const fileNameLower = this.searchFilters.fileName.toLowerCase()
        filteredFiles = filteredFiles.filter(file => 
          file.name.toLowerCase().includes(fileNameLower)
        )
      }
      
      // 업로더 필터 적용
      if (this.searchFilters.uploader === 'my' && this.isAuthenticated) {
        const currentUser = this.getCurrentUser()
        if (currentUser) {
          filteredFiles = filteredFiles.filter(file => 
            file.uploaded_by === currentUser.username
          )
        }
      } else if (this.searchFilters.uploader === 'others' && this.isAuthenticated && this.isAdmin) {
        const currentUser = this.getCurrentUser()
        if (currentUser) {
          filteredFiles = filteredFiles.filter(file => 
            file.uploaded_by && file.uploaded_by !== currentUser.username
          )
        }
      }
      
      // 공개 여부 필터 적용 (새 필터 우선, 하위 호환성을 위해 기존 필터도 지원)
      const isPublicFilter = this.searchFilters.isPublic || this.publicFilter
      if (isPublicFilter !== '') {
        filteredFiles = filteredFiles.filter(file => {
          const isPublic = this.getFilePublicStatus(file)
          return isPublicFilter === 'true' ? isPublic : !isPublic
        })
      }
      
      // 날짜 범위 필터 적용
      if (this.searchFilters.dateFrom) {
        const dateFrom = new Date(this.searchFilters.dateFrom)
        dateFrom.setHours(0, 0, 0, 0)
        filteredFiles = filteredFiles.filter(file => {
          const fileDate = new Date(file.modified * 1000)
          fileDate.setHours(0, 0, 0, 0)
          return fileDate >= dateFrom
        })
      }
      
      if (this.searchFilters.dateTo) {
        const dateTo = new Date(this.searchFilters.dateTo)
        dateTo.setHours(23, 59, 59, 999)
        filteredFiles = filteredFiles.filter(file => {
          const fileDate = new Date(file.modified * 1000)
          fileDate.setHours(23, 59, 59, 999)
          return fileDate <= dateTo
        })
      }
      
      return filteredFiles.sort((a, b) => {
        let aValue = a[this.sortKey]
        let bValue = b[this.sortKey]
        
        // 숫자 정렬을 위한 변환
        if (this.sortKey === 'size' || this.sortKey === 'max_questions') {
          aValue = typeof aValue === 'number' ? aValue : 0
          bValue = typeof bValue === 'number' ? bValue : 0
        }
        
        // 날짜 정렬을 위한 변환
        if (this.sortKey === 'modified') {
          aValue = new Date(aValue * 1000)
          bValue = new Date(bValue * 1000)
        }
        
        if (aValue < bValue) {
          return this.sortOrder === 'asc' ? -1 : 1
        }
        if (aValue > bValue) {
          return this.sortOrder === 'asc' ? 1 : -1
        }
        return 0
      })
    },
    visiblePages() {
      // 현재 페이지 주변의 페이지 번호들을 계산
      const pages = []
      const maxVisible = 5
      let start = Math.max(1, this.currentPage - Math.floor(maxVisible / 2))
      let end = Math.min(this.totalPages, start + maxVisible - 1)
      
      // 끝에서 시작점 조정
      if (end - start < maxVisible - 1) {
        start = Math.max(1, end - maxVisible + 1)
      }
      
      for (let i = start; i <= end; i++) {
        pages.push(i)
      }
      
      return pages
    },
    isAdmin() {
      return isAdmin()
    },
    isStudyAdmin() {
      return hasStudyAdminRole()
    },
    isAuthenticated() {
      return Boolean(getCurrentUserFromPermissions())
    },
    sampleXlsxPath() {
      // 현재 언어에 따라 샘플 파일 경로 결정
      const locale = this.$i18n.locale
      return locale === 'ko' ? '/sample_kr.xlsx' : '/sample_en.xlsx'
    },

  },
  async mounted() {
    // 태그 목록 로드
    await this.loadTags()
    
    // 도메인별 초기 태그 설정
    const domainConfig = getCurrentDomainConfig()
    if (domainConfig) {
      if (domainConfig.keyword === 'devops') {
        console.log('🏷️ DevOps 도메인 감지됨 - 기본 DevOps 태그 강제 적용')
        const devopsTags = getForcedTags(domainConfig, this.availableTags)
        if (devopsTags.length > 0) {
          this.selectedTagFilters = devopsTags
          console.log('📊 강제 적용된 DevOps 태그:', this.selectedTagFilters)
        }
      } else if (domainConfig.keyword === 'leetcode') {
        console.log('🏷️ LeetCode 도메인 감지됨 - 기본 LeetCode 태그 강제 적용')
        const leetcodeTags = getForcedTags(domainConfig, this.availableTags)
        if (leetcodeTags.length > 0) {
          this.selectedTagFilters = leetcodeTags
          console.log('📊 강제 적용된 LeetCode 태그:', this.selectedTagFilters)
        }
      }
    }
    
    // 번역 데이터가 로드되었는지 확인하고, 필요하면 다시 로드
    let retryCount = 0
    const maxRetries = 5
    
    while (!this.$isTranslationsLoaded(this.$i18n.locale) && retryCount < maxRetries) {
      try {
        await this.$loadTranslations(this.$i18n.locale)
      } catch (error) {
        debugLog('번역 로드 실패:', error, 'error')
      }
      
      retryCount++
      
      // 잠시 대기
      if (retryCount < maxRetries) {
        await new Promise(resolve => setTimeout(resolve, 1000))
      }
    }
    
    // 번역이 여전히 로드되지 않았다면 강제로 다시 시도
    if (!this.$isTranslationsLoaded(this.$i18n.locale)) {
      debugLog('강제로 번역 데이터를 다시 로드합니다...')
      try {
        await this.$loadTranslations(this.$i18n.locale)
        debugLog('강제 번역 로드 완료')
      } catch (error) {
        debugLog('강제 번역 로드 실패:', error, 'error')
      }
    }
    
    // 번역 로딩 상태 업데이트
    this.translationsLoaded = this.$isTranslationsLoaded(this.$i18n.locale)
    
    // Vue 강제 업데이트
    this.$forceUpdate()
    
    await this.loadFiles()
    
    // 전역 이벤트 리스너 추가 (로그아웃 시 파일 목록 갱신)
    this.$root.$on('clearAllFilters', this.loadFiles)
  },
  beforeDestroy() {
    // 이벤트 리스너 제거
    this.$root.$off('clearAllFilters', this.loadFiles)
  },
  watch: {
    // 사용자 인증 상태가 변경될 때 파일 목록을 다시 로드
    isAuthenticated() {
      this.currentPage = 1
      this.loadFiles(1)
    },
    // 공개 여부 필터 변경 시 첫 페이지로 이동 (하위 호환성)
    publicFilter() {
      this.currentPage = 1
      this.loadFiles(1)
    },
    // 검색 필터 변경 감지
    'searchFilters.fileName'() {
      this.currentPage = 1
      // 디바운싱은 handleSearchInput에서 처리
    },
    'searchFilters.uploader'() {
      this.currentPage = 1
      this.loadFiles(1)
    },
    'searchFilters.isPublic'() {
      this.currentPage = 1
      this.loadFiles(1)
    },
    'searchFilters.dateFrom'() {
      this.currentPage = 1
      this.loadFiles(1)
    },
    'searchFilters.dateTo'() {
      this.currentPage = 1
      this.loadFiles(1)
    },
    // isPublic 변경 감지 (필요시 추가 로직 구현)
    isPublic(newVal) {
      console.log('파일 공개 설정 변경:', newVal)
    }
  },
  methods: {
    async loadFiles(page = 1) {
      this.loading = true
      try {
        const params = {
          page: page,
          page_size: this.pageSize
        }
        
        // 필터 파라미터 추가
        if (this.searchFilters.fileName) {
          params.search_file_name = this.searchFilters.fileName
        }
        if (this.searchFilters.uploader === 'my' && this.isAuthenticated) {
          params.my_files = 'true'
        } else if (this.searchFilters.uploader === 'others' && this.isAuthenticated && this.isAdmin) {
          params.others_files = 'true'
        }
        if (this.searchFilters.isPublic) {
          params.is_public = this.searchFilters.isPublic
        } else if (this.publicFilter) {
          // 하위 호환성
          params.is_public = this.publicFilter
        }
        if (this.searchFilters.dateFrom) {
          params.date_from = this.searchFilters.dateFrom
        }
        if (this.searchFilters.dateTo) {
          params.date_to = this.searchFilters.dateTo
        }
        // 태그 필터 추가
        if (this.selectedTagFilters.length > 0) {
          params.tags = this.selectedTagFilters.join(',')
        }
        
        const response = await axios.get('/api/question-files/', {
          params: params
        })
        
        // API 응답 구조 확인 및 안전한 처리
        let filesData = response.data
        if (response.data && response.data.files) {
          filesData = response.data.files
        }
        
        // 배열이 아닌 경우 빈 배열로 초기화
        if (!Array.isArray(filesData)) {
          debugLog('API 응답이 배열이 아닙니다:', filesData, 'warn')
          filesData = []
        }
        
        this.files = filesData
        
        // 페이지네이션 정보 업데이트
        if (response.data && response.data.pagination) {
          this.currentPage = response.data.pagination.page || 1
          this.totalCount = response.data.pagination.count || 0
          this.totalPages = response.data.pagination.total_pages || 1
        } else {
          // 페이지네이션 정보가 없는 경우 (하위 호환성)
          this.currentPage = 1
          this.totalCount = filesData.length
          this.totalPages = 1
        }
      } catch (error) {
        debugLog('파일 목록 로드 실패:', error, 'error')
        // 에러 발생 시 빈 배열로 초기화
        this.files = []
        this.currentPage = 1
        this.totalCount = 0
        this.totalPages = 0
      } finally {
        this.loading = false
      }
    },
    goToPage(page) {
      if (page >= 1 && page <= this.totalPages) {
        this.loadFiles(page)
      }
    },
    formatSize(size) {
      if (size < 1024) return size + ' B'
      if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB'
      return (size / (1024 * 1024)).toFixed(1) + ' MB'
    },
    formatDate(dateString) {
      if (!dateString) return 'Invalid Date'
      try {
        const date = new Date(dateString)
        if (isNaN(date.getTime())) return 'Invalid Date'
        
        // 현재 언어 설정에 따라 날짜 형식 결정
        const localeMap = {
          'ko': 'ko-KR',
          'en': 'en-US',
          'es': 'es-ES',
          'zh': 'zh-CN',
          'ja': 'ja-JP'
        }
        const locale = localeMap[this.$i18n.locale] || 'en-US'
        return date.toLocaleString(locale)
      } catch (error) {
        return 'Invalid Date'
      }
    },
    async handleFileSelect(event) {
      this.selectedFile = event.target.files[0]
      this.uploadMessage = ''
      
      // 기존 파일 존재 여부 확인
      if (this.selectedFile) {
        console.log(`[DEBUG] 파일 선택됨: ${this.selectedFile.name}`)
        try {
          const response = await axios.get(`/api/question-files/check-existing/${encodeURIComponent(this.selectedFile.name)}/`)
          console.log(`[DEBUG] API 응답:`, response.data)
          
          if (response.data.exists) {
            console.log(`[DEBUG] 파일 존재함, is_private: ${response.data.is_private}`)
            // 기존 파일이 존재하는 경우, private이어도 public처럼 취급하여 업로드 허용
            console.log(`[DEBUG] 기존 파일 발견 - 업로드 진행 가능 (private이어도 허용)`)
            this.uploadMessage = this.$t('question.file.public.warning', { filename: this.selectedFile.name })
            this.uploadMessageType = 'alert-warning'
            this.isPrivateFile = false
            // 파일 선택 유지 - 업로드 진행 가능
          } else {
            // 파일이 존재하지 않는 경우
            console.log(`[DEBUG] 파일 존재하지 않음 - 새 파일`)
            this.isPrivateFile = false
          }
        } catch (error) {
          // 디버깅을 위한 에러 로그
          console.log('[DEBUG] 파일 존재 여부 확인 에러:', error)
          console.log('[DEBUG] 에러 응답:', error.response)
          
          // 에러 응답 처리
          if (error.response) {
            const { status, data } = error.response
            console.log(`[DEBUG] HTTP 상태: ${status}, 응답 데이터:`, data)
            
            if (status === 500) {
              // 백엔드 에러 처리
              console.log('[DEBUG] 500 에러 처리 시작')
              if (data && data.error) {
                // 에러 메시지에 파일 존재 여부 정보가 포함된 경우
                if (data.exists !== undefined && data.is_private !== undefined) {
                  console.log(`[DEBUG] exists: ${data.exists}, is_private: ${data.is_private}`)
                  if (data.is_private === true) {
                    // Private 파일인 경우 - 업로드 불가
                    console.log('[DEBUG] Private 파일 에러 - 업로드 차단')
                    this.uploadMessage = this.$t('question.file.error.private')
                    this.uploadMessageType = 'alert-danger'
                    this.isPrivateFile = true
                    this.selectedFile = null
                    if (this.$refs.fileInput) {
                      this.$refs.fileInput.value = ''
                    }
                  } else if (data.is_private === false) {
                    // Public 파일인 경우 - 경고만 표시하고 진행 가능
                    console.log('[DEBUG] Public 파일 에러 - 업로드 진행 가능')
                    this.uploadMessage = this.$t('question.file.error.public')
                    this.uploadMessageType = 'alert-warning'
                    this.isPrivateFile = false
                  } else if (data.is_private === null && data.needs_frontend_check) {
                    // 백엔드에서 상태를 확인할 수 없는 경우 - 프론트엔드에서 파일 목록 확인
                    console.log('[DEBUG] 백엔드 상태 확인 불가 - 프론트엔드에서 확인 필요')
                    this.checkFileStatusFromList(this.selectedFile.name)
                  }
                } else if (data.needs_frontend_check) {
                  // needs_frontend_check 플래그가 있는 경우 - 프론트엔드에서 파일 목록 확인
                  console.log('[DEBUG] needs_frontend_check 플래그 발견 - 프론트엔드에서 확인 필요')
                  this.checkFileStatusFromList(this.selectedFile.name)
                } else {
                  // 일반적인 에러 메시지
                  console.log('[DEBUG] 일반적인 에러 메시지')
                  this.uploadMessage = `Error checking file: ${data.error}`
                  this.uploadMessageType = 'alert-danger'
                }
              } else {
                console.log('[DEBUG] 에러 데이터가 없음')
                this.uploadMessage = 'Error occurred while checking file status.'
                this.uploadMessageType = 'alert-danger'
              }
            } else if (status === 404) {
              // 파일이 존재하지 않는 경우 (정상)
              console.log('[DEBUG] 404 - 새로운 파일입니다.')
              this.isPrivateFile = false
            } else {
              // 기타 HTTP 에러
              console.log(`[DEBUG] 기타 HTTP 에러: ${status}`)
              this.uploadMessage = `Error checking file. (${status})`
              this.uploadMessageType = 'alert-danger'
            }
          } else if (error.request) {
            // 네트워크 오류
            console.log('[DEBUG] 네트워크 오류')
            this.uploadMessage = 'Please check your network connection.'
            this.uploadMessageType = 'alert-danger'
          } else {
            // 기타 에러
            console.log('[DEBUG] 기타 에러 - 새로운 파일로 간주')
            this.isPrivateFile = false
          }
        }
      }
    },
    checkFileStatusFromList(filename) {
      console.log(`[DEBUG] 파일 목록에서 상태 확인: ${filename}`)
      console.log(`[DEBUG] 현재 파일 목록:`, this.files)
      console.log(`[DEBUG] 파일 목록 타입:`, typeof this.files)
      console.log(`[DEBUG] 파일 목록이 배열인가:`, Array.isArray(this.files))
      
      // 현재 로드된 파일 목록에서 해당 파일 찾기
      if (this.files && Array.isArray(this.files)) {
        console.log(`[DEBUG] 파일 목록 길이: ${this.files.length}`)
        
        // 파일명으로 정확히 일치하는 파일 찾기
        const existingFile = this.files.find(file => {
          console.log(`[DEBUG] 비교 중: '${file.name}' vs '${filename}'`)
          return file.name === filename
        })
        
        if (existingFile) {
          console.log(`[DEBUG] 파일 목록에서 발견:`, existingFile)
          
          // 파일의 공개 상태 확인
          const isPublic = this.getFilePublicStatus(existingFile)
          console.log(`[DEBUG] 파일 공개 상태: ${isPublic}`)
          
          // 파일의 공개 상태와 업로더 확인
          const currentUser = this.getCurrentUser()
          const isMyFile = currentUser && existingFile.uploaded_by && existingFile.uploaded_by === currentUser.username
          
          if (!isPublic && !isMyFile) {
            // Private 파일이고 내가 업로드한 것이 아닌 경우 - 업로드 불가
            console.log('[DEBUG] Private 파일이고 내가 업로드한 것이 아님 - 업로드 차단')
            this.uploadMessage = this.$t('question.file.private.warning', { filename: filename })
            this.uploadMessageType = 'alert-danger'
            this.isPrivateFile = true
            this.selectedFile = null
            if (this.$refs.fileInput) {
              this.$refs.fileInput.value = ''
            }
          } else {
            // Public 파일이거나 내가 업로드한 파일인 경우 - 업로드 진행 가능
            console.log('[DEBUG] Public 파일이거나 내가 업로드한 파일 - 업로드 진행 가능')
            this.uploadMessage = this.$t('question.file.public.warning', { filename: filename })
            this.uploadMessageType = 'alert-warning'
            this.isPrivateFile = false
          }
        } else {
          console.log(`[DEBUG] 파일 목록에서 찾을 수 없음 - 새 파일로 간주`)
          console.log(`[DEBUG] 파일 목록의 모든 파일명:`, this.files.map(f => f.name))
          this.isPrivateFile = false
        }
      } else {
        console.log(`[DEBUG] 파일 목록이 로드되지 않음 - 새 파일로 간주`)
        this.isPrivateFile = false
      }
    },
    logButtonState() {
      console.log('[DEBUG] Upload 버튼 상태:')
      console.log(`  - selectedFile: ${this.selectedFile ? this.selectedFile.name : 'null'}`)
      console.log(`  - isUploading: ${this.isUploading}`)
      console.log(`  - isPrivateFile: ${this.isPrivateFile}`)
      console.log(`  - 버튼 비활성화: ${!this.selectedFile || this.isUploading || this.isPrivateFile}`)
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
      this.uploadMessageType = 'alert-info'
      this.isPublic = false  // 기본값: private
      this.isPrivateFile = false  // private 파일 플래그 초기화
      this.newFileTags = [] // 태그 초기화
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = ''
      }
    },
    cancelUpload() {
      this.showUploadForm = false
      this.resetUploadForm()
    },
    async uploadFile() {
      if (!this.selectedFile) {
        this.uploadMessage = this.$t('questionFiles.alerts.selectFile')
        this.uploadMessageType = 'alert-warning'
        this.showToastMessage(this.$t('questionFiles.alerts.selectFile'), 'alert-warning', 'fas fa-exclamation-triangle')
        return
      }
      
      // 태그는 반드시 1개 이상 선택되어야 함
      if (!this.newFileTags || this.newFileTags.length === 0) {
        const isLoaded = this.$isTranslationsLoaded(this.$i18n.locale)
        const errorMsg = isLoaded ? this.$t('tagFilterModal.minOneTagRequired') || '최소 1개 이상의 태그를 선택해주세요.' : '최소 1개 이상의 태그를 선택해주세요.'
        this.uploadMessage = errorMsg
        this.uploadMessageType = 'alert-warning'
        this.showToastMessage(errorMsg, 'alert-warning', 'fas fa-exclamation-triangle')
        return
      }

      this.isUploading = true
      try {

        
        const formData = new FormData()
        formData.append('file', this.selectedFile)
        formData.append('is_public', this.isPublic)
        
        // 태그 추가
        if (this.newFileTags && this.newFileTags.length > 0) {
          // FormData에서 배열을 보낼 때는 같은 키로 여러 번 append
          this.newFileTags.forEach((tagId) => {
            formData.append('tags', tagId)
          })
        }

        const response = await axios.post('/api/upload-questions/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        this.uploadMessage = response.data.message
        this.uploadMessageType = 'alert-success'
        this.showToastMessage(this.translations.uploadSuccess, 'alert-success', 'fas fa-check-circle')
        this.currentPage = 1 // 첫 페이지로 이동
        this.loadFiles(1) // Reload files to show the new one
        this.resetUploadForm()
        this.showUploadForm = false
      } catch (error) {
        debugLog('Upload error:', error, 'error')
        this.uploadMessageType = 'alert-danger'
        if (error.response && error.response.data && error.response.data.error) {
          const errorMsg = `${this.translations.uploadError} ${error.response.data.error}`
          this.uploadMessage = errorMsg
          this.showToastMessage(errorMsg, 'alert-danger', 'fas fa-exclamation-circle')
        } else {
          const errorMsg = this.translations.uploadFailed
          this.uploadMessage = errorMsg
          this.showToastMessage(errorMsg, 'alert-danger', 'fas fa-exclamation-circle')
        }
      } finally {
        this.isUploading = false
      }
    },


    async downloadFile(file) {
      try {
        const url = `/api/question-files/${encodeURIComponent(file.name)}/download/`
        
        // fetch를 사용하여 응답 상태 확인
        const response = await fetch(url, {
          method: 'GET',
          credentials: 'include'
        })
        
        // 에러 응답 확인
        if (!response.ok) {
          // JSON 에러 메시지가 있는지 확인
          let errorMessage = this.$t('questionFiles.alerts.downloadError')
          try {
            const errorData = await response.json()
            if (errorData.error) {
              errorMessage = errorData.error
            } else if (errorData.detail) {
              errorMessage = errorData.detail
            }
          } catch (e) {
            // JSON 파싱 실패 시 기본 메시지 사용
            if (response.status === 404) {
              errorMessage = this.$t('questionFiles.alerts.fileNotFound') || '파일을 찾을 수 없습니다.'
            } else if (response.status === 403) {
              errorMessage = this.$t('questionFiles.alerts.noDownloadPermission') || '파일을 다운로드할 권한이 없습니다.'
            }
          }
          this.showToastMessage(errorMessage, 'alert-danger', 'fas fa-exclamation-circle')
          return
        }
        
        // 성공 시 파일 다운로드
        const blob = await response.blob()
        const downloadUrl = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = downloadUrl
        link.download = file.name
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(downloadUrl)
      } catch (error) {
        debugLog('파일 다운로드 실패:', error, 'error')
        const errorMessage = error.message || this.$t('questionFiles.alerts.downloadError')
        this.showToastMessage(errorMessage, 'alert-danger', 'fas fa-exclamation-circle')
      }
    },
    async deleteFile(file) {
      // 권한 확인
      if (!this.canDeleteFile(file)) {
        this.showToastMessage(this.$t('questionFiles.alerts.noDeletePermission'), 'alert-danger', 'fas fa-exclamation-circle')
        return
      }
      
      const confirmed = await this.confirm(
        this.$t('questionFiles.alerts.confirmDeleteTitle'),
        this.$t('questionFiles.alerts.confirmDeleteMessage', { fileName: file.name }),
        'fas fa-exclamation-triangle',
        this.$t('questionFiles.alerts.delete'),
        this.$t('questionFiles.alerts.cancel'),
        'btn-danger'
      )
      
      if (!confirmed) return
      
      try {
        await axios.delete(`/api/question-files/${encodeURIComponent(file.name)}/delete/`)
        // 현재 페이지의 파일 수가 1개이고 마지막 페이지가 아니면 이전 페이지로 이동
        if (this.files.length === 1 && this.currentPage > 1) {
          this.currentPage = this.currentPage - 1
        }
        this.loadFiles(this.currentPage) // 현재 페이지 또는 이전 페이지로 이동
        this.showToastMessage(this.translations.deleteSuccess, 'alert-success', 'fas fa-check-circle')
      } catch (error) {
        debugLog('파일 삭제 실패:', error, 'error')
        
        if (error.response && error.response.status === 403) {
          this.showToastMessage(this.$t('questionFiles.alerts.noDeletePermission'), 'alert-danger', 'fas fa-exclamation-circle')
        } else {
          this.showToastMessage(this.$t('questionFiles.alerts.deleteError'), 'alert-danger', 'fas fa-exclamation-circle')
        }
      }
    },
    sortBy(key) {
      if (this.sortKey === key) {
        this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc'
      } else {
        this.sortKey = key
        this.sortOrder = 'asc'
      }
    },
    getSortIcon(key) {
      if (this.sortKey !== key) {
        return 'fas fa-sort text-muted'
      }
      return this.sortOrder === 'asc' ? 'fas fa-sort-up' : 'fas fa-sort-down'
    },
    
    // 파일 공개 여부 확인
    getFilePublicStatus(file) {
      debugLog('getFilePublicStatus 호출:', { fileName: file.name, isPublic: file.is_public })
      return file.is_public !== undefined ? file.is_public : true
    },
    
    // 파일 공개여부 토글
    async toggleFilePublicStatus(file) {
      // 권한 확인
      if (!this.canEditFile(file)) {
        this.showToastMessage(this.$t('questionFiles.alerts.noEditPermission'), 'alert-danger', 'fas fa-exclamation-circle')
        return
      }
      
      // 현재 공개여부의 반대로 토글
      const currentStatus = this.getFilePublicStatus(file)
      const newStatus = !currentStatus
      
      try {
        // 백엔드에 PATCH 요청
        await axios.patch(`/api/question-files/${encodeURIComponent(file.name)}/`, {
          is_public: newStatus
        })
        
        // 파일 목록 다시 로드
        await this.loadFiles()
        
        // 공개 여부에 따라 다른 메시지 표시
        const messageKey = newStatus 
          ? 'questionFiles.alerts.publicStatusUpdatedToPublic' 
          : 'questionFiles.alerts.publicStatusUpdatedToPrivate'
        this.showToastMessage(this.$t(messageKey), 'alert-success', 'fas fa-check-circle')
      } catch (error) {
        debugLog('파일 공개 여부 업데이트 실패:', error, 'error')
        
        if (error.response && error.response.status === 403) {
          this.showToastMessage(this.$t('questionFiles.alerts.noEditPermission'), 'alert-danger', 'fas fa-exclamation-circle')
        } else {
          this.showToastMessage(this.$t('questionFiles.alerts.publicStatusUpdateFailed'), 'alert-danger', 'fas fa-exclamation-circle')
        }
      }
    },
    
    // 파일 삭제 권한 확인
    canDeleteFile(file) {
      const currentUser = this.getCurrentUser()
      
      if (this.isAdmin) {
        return true
      }
      
      if (!currentUser) {
        return false
      }
      
      // uploaded_by가 있는 경우 해당 사용자만 삭제 가능
      if (file.uploaded_by && file.uploaded_by !== 'unknown') {
        const canDelete = file.uploaded_by === currentUser.username
        return canDelete
      }
      
      // uploaded_by가 'unknown'이거나 없는 경우, 삭제 불가
      return false
    },

    // 파일 편집 권한 확인
    canEditFile(file) {
      const currentUser = this.getCurrentUser()
      
      if (this.isAdmin) {
        return true
      }
      
      if (!currentUser) {
        return false
      }
      
      // uploaded_by가 있는 경우 해당 사용자만 편집 가능
      if (file.uploaded_by && file.uploaded_by !== 'unknown') {
        const canEdit = file.uploaded_by === currentUser.username
        return canEdit
      }
      
      // uploaded_by가 'unknown'이거나 없는 경우, 편집 불가
      return false
    },
    
    // 현재 사용자 정보 가져오기
    getCurrentUser() {
      return getCurrentUserFromPermissions()
    },
    // Tag Management
    async loadTags() {
      try {
        const response = await axios.get('/api/studies/tags/')
        this.availableTags = response.data || []
      } catch (error) {
        console.error('태그 목록 로드 실패:', error)
      }
    },
    openTagModal() {
      this.showTagModal = true
    },
    handleTagUpdate(selectedTags) {
      this.newFileTags = selectedTags
    },
    handleTagApply(selectedTags) {
      this.newFileTags = selectedTags
      this.showTagModal = false
    },
    removeFileTag(tagId) {
      const index = this.newFileTags.indexOf(tagId)
      if (index > -1) {
        this.newFileTags.splice(index, 1)
      }
    },
    getSelectedTagName(tagId) {
      const tag = this.availableTags.find(t => t.id === tagId)
      if (!tag) {
        return 'Loading...'
      }
      const currentLang = this.$i18n.locale
      if (currentLang === 'ko') {
        return tag.name_ko || tag.name_en || tag.localized_name || '태그 없음'
      } else {
        return tag.name_en || tag.name_ko || tag.localized_name || 'No Tag'
      }
    },
    handleTagCreated(tag) {
      // 새로 생성된 태그를 availableTags에 추가
      if (!this.availableTags.find(t => t.id === tag.id)) {
        this.availableTags.push(tag)
        console.log('✅ 새 태그가 availableTags에 추가됨:', tag)
      }
    },
    handleTagError(error) {
      console.error('태그 에러:', error)
      this.showToastMessage('태그 선택 중 오류가 발생했습니다.', 'alert-danger', 'fas fa-exclamation-circle')
    },
    // Tag Filter for filtering files
    openTagFilterModal() {
      this.showTagFilterModal = true
    },
    handleTagFilterUpdate(selectedTags) {
      this.selectedTagFilters = selectedTags
    },
    handleTagFilterApply(selectedTags) {
      this.selectedTagFilters = selectedTags
      this.showTagFilterModal = false
      this.currentPage = 1
      this.loadFiles(1)
    },
    handleTagFilterError(error) {
      console.error('태그 필터 에러:', error)
      this.showToastMessage('태그 필터 로드 중 오류가 발생했습니다.', 'alert-danger', 'fas fa-exclamation-circle')
    },
    removeTagFilter(tagId) {
      // 필수 태그는 삭제할 수 없음
      if (this.isRequiredTag(tagId)) {
        return
      }
      const index = this.selectedTagFilters.indexOf(tagId)
      if (index > -1) {
        this.selectedTagFilters.splice(index, 1)
        this.currentPage = 1
        this.loadFiles(1)
      }
    },
    isRequiredTag(tagId) {
      // 현재 도메인의 필수 태그인지 확인
      const domainConfig = getCurrentDomainConfig()
      if (!domainConfig) {
        return false
      }
      
      // sessionStorage에서 현재 도메인의 태그 ID 가져오기
      const requiredTagId = this.getRequiredTagIdFromStorage()
      return requiredTagId ? tagId === requiredTagId : false
    },
    getRequiredTagIdFromStorage() {
      try {
        const domainConfig = getCurrentDomainConfig()
        if (!domainConfig) {
          return null
        }
        
        const stored = sessionStorage.getItem(domainConfig.storageKey)
        return stored ? parseInt(stored, 10) : null
      } catch (error) {
        console.warn('sessionStorage에서 필수 태그 ID를 읽을 수 없습니다:', error)
        return null
      }
    },
    toggleFilterRow() {
      this.showFilterRow = !this.showFilterRow
    },
    // 필터 관련 메서드
    handleSearchInput(field, value) {
      // 기존 타이머 취소
      if (this.searchDebounceTimer) {
        clearTimeout(this.searchDebounceTimer)
      }
      
      // 300ms 후에 검색 실행
      this.searchDebounceTimer = setTimeout(async () => {
        this.searchFilters[field] = value
        this.currentPage = 1
        await this.loadFiles(1)
      }, 300)
    },
    handleFilterChange() {
      this.currentPage = 1
      this.loadFiles(1)
    },

    // Toast Notifications
    showToastMessage(message, type = 'info', icon = 'fas fa-info-circle') {
      this.toastMessage = message
      this.toastType = type
      this.toastIcon = icon
      this.showToast = true
      setTimeout(() => {
        this.hideToast()
      }, 3000) // 3초 후 사라짐
    },
    hideToast() {
      this.showToast = false
    },

    // Modal Confirm
    async confirm(title, message, icon = 'fas fa-question-circle', confirmText = 'OK', cancelText = 'Cancel', confirmButtonClass = 'btn-success') {
      this.modalTitle = title
      this.modalMessage = message
      this.modalIcon = icon
      this.modalConfirmText = confirmText
      this.modalCancelText = cancelText
      this.modalConfirmButtonClass = confirmButtonClass
      this.showModal = true

      return new Promise(resolve => {
        this.$root.$on('confirm', (confirmed) => {
          this.showModal = false
          resolve(confirmed)
          this.$root.$off('confirm')
        })
      })
    },
    cancelModal() {
      this.showModal = false
      this.$root.$off('confirm')
    },
    confirmModal() {
      this.showModal = false
      this.$root.$emit('confirm', true)
      this.$root.$off('confirm')
    }
  }
}
</script>

<style scoped>
/* Modern Question Files Styles */
.question-files-modern {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 10px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100vh;
  color: white;
}

.files-container {
  max-width: 1400px;
  margin: 0 auto;
  background: white;
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  overflow: hidden;
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
  text-decoration: none;
}

.action-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn-primary {
  border-color: #007bff;
  background: #007bff;
  color: white;
}

.action-btn-primary:hover:not(:disabled) {
  background: #0056b3;
  border-color: #0056b3;
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

.action-btn-info {
  border-color: #17a2b8;
  background: #17a2b8;
  color: white;
}

.action-btn-info:hover:not(:disabled) {
  background: #138496;
  border-color: #117a8b;
}

.action-btn-secondary {
  border-color: #6c757d;
  background: white;
  color: #6c757d;
}

.action-btn-secondary:hover:not(:disabled) {
  background: #6c757d;
  border-color: #6c757d;
  color: white;
}

.action-btn-outline {
  border-color: #007bff;
  background: white;
  color: #007bff;
}

.action-btn-outline:hover:not(:disabled) {
  background: #007bff;
  color: white;
}

.action-label {
  font-size: 12px;
  font-weight: 500;
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
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  padding: 30px;
  margin: 20px 30px;
  border: 1px solid #e9ecef;
}

@media (max-width: 768px) {
  .card-modern {
    margin-top: 10px;
    margin-bottom: 10px;
    padding-top: 20px;
    padding-bottom: 20px;
  }
}

.card-header-modern {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  /* border-bottom: 1px solid #e9ecef; */
}

@media (max-width: 768px) {
  .card-header-modern {
    margin-bottom: 10px;
  }
}

.card-header-modern h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
}

.card-actions {
  display: flex;
  gap: 10px;
}

/* Files List Card */
.files-list-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  padding: 30px;
  padding-top: 0px;
  margin: 20px 30px;
  border: 1px solid #e9ecef;
}

@media (max-width: 768px) {
  .files-list-card {
    margin-top: 10px;
    margin-bottom: 10px;
    padding-top: 0px;
    padding-bottom: 20px;
    margin-left: 0px !important;
    margin-right: 0px !important;
    padding-left: 10px !important;
    padding-right: 10px !important;
  }
}

/* Files Section */
.files-section {
  padding: 30px;
}

/* Files Table */
.files-table {
  background: white;
  border-radius: 8px;
  box-shadow: none;
  border: 1px solid #dee2e6;
  overflow: hidden;
  width: 100%;
  display: flex;
  flex-direction: column;
}

.table-header {
  display: grid;
  grid-template-columns: 2fr 80px 1fr 80px 80px 2fr;
  gap: 15px;
  padding: 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  font-weight: 600;
  color: #495057;
  align-items: center;
  width: 100%;
  min-width: 0;
  flex-shrink: 0;
}

.table-column {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  user-select: none;
  transition: color 0.3s ease;
}

.table-column:hover {
  color: #007bff;
}

.sort-icon {
  font-size: 12px;
  color: #6c757d;
}

.table-body {
  max-height: 600px;
  overflow-y: auto;
  width: 100%;
  flex: 1;
}

.loading-files {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #6c757d;
  text-align: center;
}

.no-files {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #6c757d;
  text-align: center;
}

.no-files i {
  font-size: 48px;
  margin-bottom: 20px;
  color: #dee2e6;
}

.no-files p {
  margin: 0 0 10px 0;
  font-size: 18px;
  font-weight: 500;
}

.no-files small {
  color: #adb5bd;
}

.table-row {
  display: grid;
  grid-template-columns: 2fr 80px 1fr 80px 80px 2fr;
  gap: 15px;
  padding: 15px 20px;
  border-bottom: 1px solid #f1f3f4;
  align-items: center;
  transition: background-color 0.3s ease;
  width: 100%;
  min-width: 0;
}

.table-row:hover {
  background: #f8f9fa;
}

.table-cell {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: #495057;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-public {
  background: #d4edda;
  color: #155724;
}

.status-private {
  background: #f8d7da;
  color: #721c24;
}

.action-buttons {
  display: flex;
  gap: 6px;
  flex-wrap: nowrap;
  align-items: center;
}

/* Upload Section */
.upload-section {
  padding: 20px;
  background: white;
  border-top: 1px solid #e9ecef;
}

.upload-card {
  background: white;
  border-radius: 15px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid #e9ecef;
  overflow: hidden;
}

.card-header-modern {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 20px 25px;
  border-bottom: 1px solid #e9ecef;
  background: #f8f9fa;
}

.card-header-modern h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
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

.upload-content {
  padding: 25px;
}

.upload-form {
  display: flex;
  gap: 15px;
  align-items: end;
  flex-wrap: wrap;
  margin-bottom: 20px;
}

.upload-input {
  flex: 1;
  min-width: 300px;
}

.upload-actions {
  display: flex;
  gap: 10px;
}

.upload-message {
  margin-top: 15px;
  padding: 12px 16px;
  border-radius: 8px;
  font-weight: 500;
}

.upload-message.alert-success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.upload-message.alert-danger {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.upload-message.alert-warning {
  background: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
}

.upload-message.alert-info {
  background: #d1ecf1;
  color: #0c5460;
  border: 1px solid #bee5eb;
}

/* Format Example */
.format-example {
  margin-top: 30px;
}

.example-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.example-header h4 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.sample-downloads {
  display: flex;
  gap: 10px;
}

.example-info {
  margin-bottom: 20px;
}

.info-alert {
  background: #e3f2fd;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 15px;
  border: 1px solid #bbdefb;
  color: #1976d2;
}

.info-alert i {
  margin-right: 8px;
}

.supported-formats {
  background: #f8f9fa;
  padding: 10px 15px;
  border-radius: 6px;
  color: #495057;
  font-size: 14px;
}

.example-table {
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #e9ecef;
  overflow: hidden;
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
}

.example-table .table-header {
  display: grid;
  grid-template-columns: 80px 1.5fr 1.5fr 1.5fr 1.5fr 100px 1.5fr 100px;
  gap: 15px;
  background: #f8f9fa;
  padding: 15px 20px;
  font-size: 12px;
  font-weight: 600;
  color: #495057;
  border-bottom: 1px solid #e9ecef;
}

.example-table .table-body {
  max-height: none;
  display: flex;
  flex-direction: column;
}

.example-table .table-row {
  display: grid;
  grid-template-columns: 80px 1.5fr 1.5fr 1.5fr 1.5fr 100px 1.5fr 100px;
  gap: 15px;
  padding: 12px 20px;
  font-size: 12px;
  border-bottom: 1px solid #f1f3f4;
  align-items: center;
}

.example-table .table-row:last-child {
  border-bottom: none;
}

.example-table .table-cell {
  display: flex;
  align-items: center;
  font-size: 12px;
  color: #495057;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.example-table .table-cell.url-cell {
  word-break: break-all;
  white-space: normal;
  line-height: 1.4;
}

.difficulty-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

.difficulty-badge.bg-success {
  background: #d4edda;
  color: #155724;
}

.difficulty-badge.bg-warning {
  background: #fff3cd;
  color: #856404;
}

.difficulty-badge.bg-danger {
  background: #f8d7da;
  color: #721c24;
}

.format-notes {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

/* Form Controls */
.form-control {
  padding: 10px 12px;
  border: 1px solid #ced4da;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.3s ease;
}

.file-name-search-input {
  width: 70%;
}

.form-control:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.form-control-sm {
  padding: 6px 10px;
  font-size: 12px;
}

.form-select {
  padding: 10px 12px;
  border: 1px solid #ced4da;
  border-radius: 8px;
  font-size: 14px;
  background-color: white;
  transition: border-color 0.3s ease;
}

.form-select:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.form-select-sm {
  padding: 6px 10px;
  font-size: 12px;
}

/* Responsive Design */
@media (max-width: 1200px) {
  .table-header,
  .table-row {
    grid-template-columns: 2fr 60px 1fr 60px 60px 1.5fr;
  }
  
  .example-table .table-header,
  .example-table .table-row {
    grid-template-columns: 60px 1fr 1fr 1fr 1fr 80px 1fr 80px;
    gap: 10px;
  }
}

@media (max-width: 768px) {
  .question-files-modern {
    padding: 10px !important;
    padding-left: 10px !important;
    padding-right: 10px !important;
    display: flex;
    flex-direction: column;
  }
  
  .files-container {
    border-radius: 15px;
    flex: 1;
    min-height: calc(100vh - 20px); /* padding 10px * 2 */
    display: flex;
    flex-direction: column;
    margin: 0;
  }
  
  .files-section {
    padding: 10px;
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
  }
  
  .files-list-card {
    margin-left: 0px !important;
    margin-right: 0px !important;
    padding-left: 10px !important;
    padding-right: 10px !important;
  }
  
  .files-table {
    flex: 1;
    min-height: 0;
  }
  
  .table-body {
    max-height: none;
    min-height: 0;
  }
  
  .top-header {
    justify-content: center;
    padding: 15px 20px;
  }
  
  .page-title h1 {
    font-size: 24px;
  }
  
  .table-header,
  .table-row {
    grid-template-columns: 1.5fr 50px 1fr 50px 50px 1.5fr;
    font-size: 12px;
    gap: 10px;
    padding: 10px 15px;
  }
  
  .table-cell {
    font-size: 12px;
  }
  
  /* 원형 버튼 스타일은 공통 CSS (mobile-buttons.css)에서 처리됨 */
  
  .example-table .table-header,
  .example-table .table-row {
    grid-template-columns: 50px 1fr 1fr 1fr 1fr 70px 1fr 70px;
    font-size: 10px;
    gap: 8px;
    padding: 8px 10px;
  }
  
  .upload-section {
    padding: 10px;
  }
  
  .upload-content {
    padding: 10px;
  }
}

@media (max-width: 576px) {
  .header-actions {
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .action-btn {
    padding: 0;
    width: 36px;
    height: 36px;
    border-radius: 50%; /* 원형으로 변경 */
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    gap: 0;
    min-width: auto; /* min-width 제거 */
  }
  
  .table-header,
  .table-row {
    grid-template-columns: 1fr 40px 1fr 40px 40px 1.5fr;
    gap: 8px;
    padding: 8px 10px;
  }
  
  .table-cell {
    font-size: 11px;
  }
  
  .status-badge {
    font-size: 10px;
    padding: 2px 4px;
  }
  
  .example-table .table-header,
  .example-table .table-row {
    grid-template-columns: 40px 1fr 1fr 1fr 1fr 60px 1fr 60px;
    gap: 6px;
    padding: 6px 8px;
    font-size: 9px;
  }
}

/* Toast Notifications - 기본 스타일은 공통 CSS (mobile-buttons.css)에 정의됨 */

/* 타입별 스타일은 공통 CSS (mobile-buttons.css)에 정의됨 */

.toast-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toast-close {
  background: none;
  border: none;
  color: white;
  font-size: 18px;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

/* Modal Confirm */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
}

.modal-content {
  background: white;
  border-radius: 15px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  width: 90%;
  max-width: 500px;
  max-height: 90%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 25px;
  border-bottom: 1px solid #e9ecef;
  background: #f8f9fa;
}

.modal-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 10px;
}

.modal-title i {
  font-size: 20px;
  color: #007bff;
}

.modal-close {
  background: none;
  border: none;
  color: #6c757d;
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.modal-close:hover {
  color: #343a40;
}

.modal-body {
  padding: 25px;
  overflow-y: auto;
  flex-grow: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-body p {
  margin: 0;
  font-size: 16px;
  color: #495057;
  text-align: center;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 15px 25px;
  border-top: 1px solid #e9ecef;
  background: #f8f9fa;
}

.modal-footer .btn {
  padding: 8px 16px;
  border-radius: 25px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid #e9ecef;
}

.modal-footer .btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.modal-footer .btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.modal-footer .btn-secondary {
  border-color: #6c757d;
  background: white;
  color: #6c757d;
}

.modal-footer .btn-secondary:hover:not(:disabled) {
  background: #6c757d;
  border-color: #6c757d;
  color: white;
}

.modal-footer .btn-success {
  border-color: #28a745;
  background: #28a745;
  color: white;
}

.modal-footer .btn-success:hover:not(:disabled) {
  background: #218838;
  border-color: #1e7e34;
}

.modal-footer .btn-danger {
  border-color: #dc3545;
  background: #dc3545;
  color: white;
}

.modal-footer .btn-danger:hover:not(:disabled) {
  background: #c82333;
  border-color: #bd2130;
}

.modal-footer .btn-warning {
  border-color: #ffc107;
  background: #ffc107;
  color: #212529;
}

.modal-footer .btn-warning:hover:not(:disabled) {
  background: #e0a800;
  border-color: #d39e00;
}

.modal-footer .btn-info {
  border-color: #17a2b8;
  background: #17a2b8;
  color: white;
}

.modal-footer .btn-info:hover:not(:disabled) {
  background: #138496;
  border-color: #117a8b;
}

/* Filter Actions */
.mobile-filter-toggle {
  display: flex;
}

.filter-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 30px;
}

.filter-row {
  margin-top: 30px;
}

.filter-row.mobile-hidden {
  display: none;
}

/* Selected Tags Display */
.selected-tags-display {
  padding: 12px 16px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.selected-tags-display .badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 14px;
  margin-right: 8px;
  margin-bottom: 4px;
}

.selected-tags-display .btn-close {
  background: none;
  border: none;
  color: white;
  font-size: 12px;
  padding: 0;
  margin: 0;
  opacity: 0.8;
  transition: opacity 0.2s;
}

.selected-tags-display .btn-close:hover {
  opacity: 1;
}

/* 모바일에서 테이블 컬럼 숨기기 - Filename과 Actions만 표시 */
@media (max-width: 768px) {
  .mobile-filter-toggle {
    display: flex;
  }
  
  .filter-actions {
    margin-top: 15px !important;
  }
  
  .filter-row.mobile-hidden {
    display: none;
  }
  /* 그리드 레이아웃을 Filename + Actions 2컬럼으로 변경 */
  .table-header,
  .table-row {
    display: grid !important;
    grid-template-columns: 1fr 120px !important;
    gap: 10px !important;
  }
  
  /* Filename은 나머지 공간 사용, Actions는 고정 너비 */
  .table-header .table-column:first-child,
  .table-row .table-cell:first-child {
    width: 100% !important;
    flex: 1 !important;
    min-width: 0 !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    white-space: nowrap !important;
  }
  
  /* Filename 셀 내부 텍스트도 말줄임표 처리 */
  .table-row .table-cell:first-child > * {
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    white-space: nowrap !important;
    min-width: 0 !important;
  }
  
  .table-header .table-column:last-child,
  .table-row .table-cell:last-child {
    width: 120px !important;
    flex: 0 0 120px !important;
  }
  
  /* 나머지 컬럼들 숨기기 (Filename과 Actions 제외) */
  .table-header .table-column:nth-child(2),
  .table-header .table-column:nth-child(3),
  .table-header .table-column:nth-child(4),
  .table-header .table-column:nth-child(5) {
    display: none !important;
  }
  
  .table-row .table-cell:nth-child(2),
  .table-row .table-cell:nth-child(3),
  .table-row .table-cell:nth-child(4),
  .table-row .table-cell:nth-child(5) {
    display: none !important;
  }
  
  /* Filename 컬럼의 폰트 크기 증가 */
  .table-row .table-cell:first-child {
    font-size: 18px !important;
    line-height: 1.4 !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    white-space: nowrap !important;
  }
  
  /* Actions 컬럼의 폰트 크기 증가 */
  .table-row .table-cell:last-child {
    font-size: 16px !important;
    line-height: 1.4 !important;
  }
  
  /* Actions 버튼들의 폰트 크기 증가 */
  .table-row .table-cell:last-child .action-btn {
    font-size: 14px !important;
  }
  
  .table-row .table-cell:last-child .action-label {
    font-size: 14px !important;
  }
}

/* 페이지네이션 스타일 */
.pagination-container {
  margin-top: 2rem;
  padding: 1rem 0;
}

.pagination {
  margin-bottom: 0;
}

.pagination .page-item {
  margin: 0 2px;
}

.pagination .page-link {
  color: #007bff;
  border: 1px solid #dee2e6;
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.pagination .page-link:hover {
  background-color: #e9ecef;
  border-color: #adb5bd;
}

.pagination .page-item.active .page-link {
  background-color: #007bff;
  border-color: #007bff;
  color: white;
  z-index: 1;
}

.pagination .page-item.disabled .page-link {
  color: #6c757d;
  pointer-events: none;
  cursor: not-allowed;
  background-color: #fff;
  border-color: #dee2e6;
  opacity: 0.6;
}

.pagination-info {
  margin-top: 0.5rem;
}
</style> 