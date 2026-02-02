<template>
  <div class="exam-management-modern">
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
            <i class="fas fa-times"></i>
            <span>{{ modalCancelText }}</span>
          </button>
          <button class="btn" :class="modalConfirmButtonClass" @click="confirmModal">
            <i class="fas fa-check"></i>
            <span>{{ modalConfirmText }}</span>
          </button>
        </div>
      </div>
    </div>
    
    <div class="exam-container">
      <!-- Top Header -->
      <div class="top-header">
        <div class="header-actions">
          <button 
            @click="handleCreateExam" 
            class="action-btn action-btn-success"
            v-if="!showCreateForm && isAuthenticated"
          >
            <i class="fas fa-plus"></i>
            <span class="action-label">{{ $t('examManagement.createExam') }}</span>
          </button>
          <button 
            @click="createRandomRecommendationExams" 
            class="action-btn action-btn-warning"
            v-if="isAuthenticated"
          >
            <i class="fas fa-random"></i>
            <span class="action-label desktop-only">{{ $t('examManagement.randomExam') }}</span>
            <span class="action-label mobile-only">Daily</span>
          </button>
          <router-link to="/question-files" class="action-btn action-btn-primary">
            <i class="fas fa-file-alt"></i>
            <span class="action-label desktop-only">{{ $t('examManagement.questionManagement') }}</span>
            <span class="action-label mobile-only">Quizzes</span>
          </router-link>
        </div>
      </div>

      <!-- Page Title -->
      <div class="page-title">
        <h1>{{ $t('examManagement.title') }}</h1>
      </div>
      

      
      <!-- 시험 생성 폼 -->
      <div class="card-modern exam-form-card" v-if="showCreateForm">
        <div class="card-header-modern">
          <h3>{{ $t('examManagement.createForm.title') }}</h3>
          <button @click="toggleCreateForm" class="card-action-btn">
            <i class="fas fa-times"></i>
            <span class="action-label">{{ $t('examManagement.createForm.cancel') }}</span>
          </button>
        </div>
        <div class="card-body">
        <form @submit.prevent="createExam">
                    <div class="row">
            <div class="col-md-3">
              <div class="form-group">
                <label>{{ $t('examManagement.createForm.titleLabel') }}</label>
                <input 
                  v-model="newExam.title" 
                  type="text" 
                  class="form-control" 
                  :class="{ 'is-invalid': titleError }"
                  @blur="checkTitleDuplicate"
                  @input="handleTitleInput"
                  required
                >
                <div v-if="titleError" class="invalid-feedback">
                  {{ titleError }}
                </div>
              </div>
            </div>
            <div class="col-md-2">
              <div class="form-group">
                <label>{{ $t('examManagement.createForm.questionCount') }}</label>
                <div class="input-group">
                  <input 
                    v-model="newExam.question_count" 
                    type="number" 
                    :min="0" 
                    :max="maxQuestions" 
                    class="form-control" 
                    required
                  >
                  <button 
                    v-if="maxQuestions > 0" 
                    type="button" 
                    class="btn btn-outline-secondary" 
                    @click="setMaxQuestions"
                  >
                    {{ $t('examManagement.createForm.max') }}
                  </button>
                </div>
              </div>
            </div>
            <div class="col-md-3">
              <div class="form-group">
                <label>{{ $t('examManagement.createForm.fileSelection') }}</label>
                <select v-model="newExam.file_name" class="form-control" @change="onFileChange">
                  <option value="">{{ $t('examManagement.createForm.selectFile') }}</option>
                  <option v-if="!questionFiles || questionFiles.length === 0" value="" disabled>{{ $t('examManagement.noFilesUploaded') }}</option>
                  <option v-for="file in questionFiles" :key="file.name" :value="file.name">
                    {{ file.name }} ({{ file.question_count }})
                  </option>
                </select>
              </div>
            </div>
            <div class="col-md-2">
              <div class="form-group">
                <label>&nbsp;</label>
                <div class="form-check" style="padding-top: 8px;">
                  <input 
                    type="checkbox" 
                    v-model="newExam.is_public" 
                    class="form-check-input" 
                    id="isPublicCheck"
                  >
                  <label class="form-check-label" for="isPublicCheck">
                    {{ $t('examManagement.createForm.public') }}
                  </label>
                </div>
              </div>
            </div>

          </div>
          
          <!-- Force Answer, 음성 모드 지원, AI 모의 인터뷰 행 -->
          <div class="row mt-3">
            <div class="col-md-4">
              <div class="form-group">
                <div class="form-check">
                  <input 
                    type="checkbox" 
                    v-model="newExam.force_answer" 
                    class="form-check-input" 
                    id="forceAnswerCheck"
                  >
                  <label class="form-check-label" for="forceAnswerCheck">
                    {{ $t('examManagement.createForm.forceAnswer') }}
                  </label>
                </div>
              </div>
            </div>
            <div class="col-md-4">
              <div class="form-group">
                <div class="form-check">
                  <input 
                    type="checkbox" 
                    v-model="newExam.voice_mode_enabled" 
                    class="form-check-input" 
                    id="voiceModeCheck"
                  >
                  <label class="form-check-label" for="voiceModeCheck">
                    {{ $t('examManagement.createForm.voiceMode') }}
                  </label>
                </div>
              </div>
            </div>
            <div class="col-md-4">
              <div class="form-group">
                <div class="form-check">
                  <input 
                    type="checkbox" 
                    v-model="newExam.ai_mock_interview" 
                    class="form-check-input" 
                    id="aiMockInterviewCheck"
                  >
                  <label class="form-check-label" for="aiMockInterviewCheck">
                    {{ $t('examManagement.createForm.aiMockInterview') }}
                  </label>
                </div>
              </div>
            </div>
          </div>
          
          <!-- AI로 문제 생성 체크박스 (LeetCode 도메인 또는 localhost에서 표시) -->
          <div v-if="isLeetCodeDomain || isLocalhost" class="row mt-3">
            <div class="col-12">
              <div class="form-group">
                <div class="form-check">
                  <input 
                    type="checkbox" 
                    v-model="showAiGenerator" 
                    class="form-check-input" 
                    id="aiGenerateCheck"
                    @change="onAiGenerateChange"
                  >
                  <label class="form-check-label" for="aiGenerateCheck">
                    {{ $t('examManagement.createForm.aiGenerateQuestions') }}
                  </label>
                </div>
              </div>
            </div>
          </div>
          
          <!-- AI 문제 생성 컴포넌트 -->
          <AiQuestionGenerator 
            :show-generator="showAiGenerator"
            @toggle-generator="toggleAiGenerator"
            @questions-generated="onQuestionsGenerated"
          />
          
          <div class="row mt-3">
            <div class="col-12">
              <div class="form-group">
                <label>{{ $t('examManagement.createForm.descriptionLabel') }}</label>
                <textarea 
                  v-model="newExam.description" 
                  class="form-control" 
                  rows="3"
                  :placeholder="$t('examManagement.createForm.descriptionPlaceholder')"
                ></textarea>
              </div>
            </div>
          </div>
          
          <!-- Tags Section -->
          <div class="row mt-3">
            <div class="col-12">
              <div class="form-group">
                <label>
                  {{ $t('examDetail.tagManagement') || '태그 관리' }}
                  <span class="text-danger">*</span>
                </label>
                <div class="d-flex align-items-center justify-content-end gap-2 flex-wrap">
                  <!-- Selected Tags Display -->
                  <div v-if="newExamTags && newExamTags.length > 0" class="d-flex align-items-center flex-wrap gap-2">
                    <span 
                      v-for="tagId in newExamTags" 
                      :key="tagId"
                      class="badge bg-primary"
                    >
                      {{ getSelectedTagName(tagId) }}
                      <button 
                        @click="removeNewExamTag(tagId)" 
                        class="btn-close btn-close-white ms-1" 
                        style="font-size: 0.7em;"
                      ></button>
                    </span>
                  </div>
                  <button 
                    @click="openNewExamTagModal" 
                    type="button"
                    class="btn btn-outline-primary btn-sm"
                  >
                    <i class="fas fa-tags"></i>
                    {{ $t('tagFilterModal.title') || '태그로 검색' }}
                    <span v-if="newExamTags && newExamTags.length > 0" class="badge bg-primary ms-2">{{ newExamTags.length }}</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div class="row mt-3">
            <div class="col-12">
              <div class="d-flex gap-3 justify-content-end">
                <button 
                  type="submit" 
                  class="action-btn action-btn-success"
                  :disabled="saving || !newExamTags || newExamTags.length === 0"
                  :title="(!newExamTags || newExamTags.length === 0) ? ($t('examManagement.createForm.tagRequired') || '태그를 선택해주세요.') : ''"
                >
                  <i :class="saving ? 'fas fa-spinner fa-spin' : 'fas fa-save'"></i>
                  <span class="action-label">
                    {{ saving ? $t('examManagement.createForm.saving') : $t('examManagement.createForm.save') }}
                  </span>
                </button>
              </div>
            </div>
          </div>
        </form>
        </div>
      </div>

      <!-- Excel 업로드 폼 -->
      <div class="card mb-4" v-if="showUploadForm">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-center mb-3">
            <h5 class="card-title mb-0">{{ $t('examManagement.upload.title') }}</h5>
            <button @click="toggleUploadForm" class="btn btn-sm btn-secondary close-btn">
              <span aria-hidden="true">&times;</span>
            </button>
          </div>
          <div class="row">
            <div class="col-md-8">
              <input 
                type="file" 
                class="form-control" 
                @change="handleFileSelect" 
                accept=".xlsx,.xls"
                ref="fileInput"
              >
            </div>
            <div class="col-md-4">
              <div class="d-flex gap-2">
                <button 
                  @click="uploadExamsExcel" 
                  class="btn btn-primary"
                  :disabled="!selectedFile"
                >
                  <i class="fas fa-upload me-2"></i>{{ $t('examManagement.upload.upload') }}
                </button>
                <button 
                  @click="cancelUpload" 
                  class="btn btn-secondary"
                >
                  {{ $t('examManagement.upload.cancel') }}
                </button>
              </div>
            </div>
          </div>
          <div v-if="uploadMessage" class="alert alert-info mt-2">
            {{ uploadMessage }}
          </div>
          
          <!-- Excel 파일 형식 안내 -->
          <div class="mt-3">
            <div class="alert alert-info">
              <i class="fas fa-info-circle me-2"></i>
              <strong>{{ $t('examManagement.upload.fileFormat') }}</strong>
            </div>
            <h6>{{ $t('examManagement.upload.formatExample') }}</h6>
            <div class="table-responsive">
              <table class="table table-sm table-bordered">
                <thead class="table-light">
                  <tr>
                    <th>{{ $t('examManagement.upload.sheetName') }}</th>
                    <th>{{ $t('examManagement.upload.column') }}</th>
                    <th>{{ $t('examManagement.upload.description') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>{{ $t('examManagement.upload.examList') }}</td>
                    <td>{{ $t('examManagement.upload.examTitle') }}</td>
                    <td>{{ $t('examManagement.upload.examTitleRequired') }}</td>
                  </tr>
                  <tr>
                    <td>{{ $t('examManagement.upload.examSheet') }}</td>
                    <td>{{ $t('examManagement.upload.questionColumns') }}</td>
                    <td>{{ $t('examManagement.upload.questionDetails') }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <small class="text-muted">
              {{ $t('examManagement.upload.notes') }}
            </small>
          </div>
        </div>
      </div>

      <!-- 시험 목록 -->
      <div class="card-modern exam-list-card">
        <!-- 조회 조건 -->
        <div class="search-filters mb-3">
          <div class="row filter-row" :class="{ 'mobile-hidden': !showFilterRow }">
            <div class="col-md-2">
              <div class="form-group">
                <select v-model="examTypeFilter" class="form-control">
                  <option value="my" v-if="isAuthenticated">{{ $t('examManagement.filter.myExams') }}</option>
                  <option value="public">{{ $t('examManagement.filter.publicExams') }}</option>
                  <option value="all" v-if="isAdmin">{{ $t('examManagement.filter.allExams') }}</option>
                </select>
              </div>
            </div>
            <div class="col-md-2">
              <div class="form-group">
                <input 
                  :value="searchFilters.title"
                  @input="handleSearchInput('title', $event.target.value)"
                  type="text" 
                  class="form-control" 
                  :placeholder="$t('examManagement.search.placeholder')"
                >
              </div>
            </div>
            <div class="col-6 col-md-2" v-if="isAuthenticated">
              <div class="form-group">
                <select 
                  :value="searchFilters.isOriginal"
                  @change="handleSearchInput('isOriginal', $event.target.value)"
                  class="form-control" 
                  style="width: 120px; min-width: 0;"
                >
                  <option value="">{{ $t('examManagement.filter.all') }}</option>
                  <option value="true">{{ $t('examManagement.filter.originalOnly') }}</option>
                  <option value="false">{{ $t('examManagement.filter.copyOnly') }}</option>
                </select>
              </div>
            </div>
            <div class="col-6 col-md-1" v-if="isAuthenticated">
              <div class="form-group">
                <select 
                  :value="searchFilters.isPublic"
                  @change="handleSearchInput('isPublic', $event.target.value)"
                  class="form-control" 
                  style="width: 120px; min-width: 0;"
                >
                  <option value="">{{ $t('examManagement.filter.all') }}</option>
                  <option value="true">{{ $t('examManagement.filter.public') }}</option>
                  <option value="false">{{ $t('examManagement.filter.private') }}</option>
                </select>
              </div>
            </div>
          </div>
          <div class="filter-actions mb-2">
            <!-- Tag Filter Button -->
            <button 
              @click="openTagFilterModal" 
              class="btn btn-outline-primary btn-sm tag-filter-btn"
              style="height: 38px; display: flex; align-items: center;"
            >
              <i class="fas fa-tags"></i>
              {{ $t('examManagement.tagFilter') || '태그 필터' }}
              <span v-if="selectedTagFilters && selectedTagFilters.length > 0" class="badge bg-primary ms-1">{{ selectedTagFilters.length }}</span>
            </button>
            <button @click="toggleFilterRow" class="action-btn action-btn-info mobile-filter-toggle">
              <i class="fas fa-filter"></i>
              <span class="action-label">{{ $t('examDetail.filter') || 'Filter' }}</span>
            </button>
            <button @click="toggleSelectedSubscriptions" class="action-btn" :class="getBulkSubscriptionButtonClass()" :disabled="!selectedExams || selectedExams.length === 0" v-if="isAuthenticated && selectedExams && selectedExams.length > 0">
              <i :class="getBulkSubscriptionButtonIcon()"></i>
              <span class="action-label">{{ getBulkSubscriptionButtonText() }}</span>
            </button>
            <button @click="deleteSelected" class="action-btn action-btn-danger" :disabled="!selectedExams || selectedExams.length === 0" v-if="isAuthenticated && selectedExams && selectedExams.length > 0">
              <i class="fas fa-trash"></i>
              <span class="action-label">{{ $t('examManagement.delete') }}</span>
            </button>
          </div>
        </div>

        <!-- 로딩 중 -->
        <div v-if="loading" class="text-center py-4">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">{{ $t('examManagement.loading') }}</span>
          </div>
          <p class="mt-2">{{ $t('examManagement.loadingText') }}</p>
        </div>
        
        <!-- 데이터 로딩 완료 후 -->
        <div v-else>
          <div v-if="filteredExams && filteredExams.length > 0" class="exam-tree">
          <div class="tree-header">
            <div class="d-flex align-items-center">
                              <div class="checkbox-column" style="width: 21px; flex-shrink: 0;" v-if="isAuthenticated"><input type="checkbox" @change="toggleAllExams" :checked="isAllSelected" :indeterminate="isIndeterminate"></div>
              <div class="sortable-header flex-grow-1" @click="sortTreeBy('title')" style="min-width: 200px;">
                {{ $t('examManagement.table.title') }}
                <i :class="getTreeSortIcon('title')" class="ms-1"></i>
              </div>

              <div class="text-center sortable-header" @click="sortTreeBy('total_questions')" style="width: 80px; flex-shrink: 0;" v-if="isAuthenticated">
                {{ $t('examManagement.table.count') }}
                <i :class="getTreeSortIcon('total_questions')" class="ms-1"></i>
              </div>


              <div class="text-center" style="width: 80px; flex-shrink: 0;" v-if="isAuthenticated">{{ $t('examManagement.table.public') }}</div>
              <div class="text-center" style="width: 100px; flex-shrink: 0;" v-if="isAuthenticated">{{ $t('examManagement.table.subscribe') }}</div>
              <div class="text-center" style="width: 180px; flex-shrink: 0;" v-if="isAuthenticated">{{ $t('examManagement.table.actions') }}</div>
            </div>
          </div>
          
                <div class="tree-body">
        <div v-for="exam in filteredExamTree" :key="String(exam.id)" class="exam-node">
              <!-- 원본 시험 -->
              <div class="exam-row original-exam">
                <div class="d-flex align-items-center">
                  <div class="checkbox-column" style="width: 21px; flex-shrink: 0;" v-if="isAuthenticated"><input type="checkbox" :checked="isExamSelected(String(exam.id))" @change="toggleExamSelection(String(exam.id), $event)" :disabled="!isAdmin && !isExamForCurrentUser(exam)"></div>
                  <div class="flex-grow-1">
                    <div class="exam-title">
                      <button 
                        v-if="exam.children && exam.children.length > 0" 
                        @click="toggleExam(exam.id)" 
                        class="btn btn-sm btn-link p-0 me-2"
                      >
                        <i :class="expandedExams[exam.id] ? 'fas fa-chevron-down' : 'fas fa-chevron-right'"></i>
                      </button>
                      <strong v-if="hasVersions(exam)">
                        {{ getLocalizedTitle(exam) }}
                        <i 
                          v-if="exam.ai_mock_interview" 
                          @click.stop="$router.push(`/exam-detail/${exam.id}?t=${Date.now()}&returnTo=exam-detail`)"
                          class="fas fa-robot ms-2" 
                          style="color: #ff6b35; cursor: pointer;" 
                          :title="$t('examManagement.createForm.aiMockInterview')"
                        ></i>
                      </strong>
                      <template v-else>
                        <router-link v-if="getExamLink(exam)" :to="getExamLink(exam)" class="exam-title-link">
                          <strong>{{ getLocalizedTitle(exam) }}</strong>
                        </router-link>
                        <strong v-else class="exam-title-link" style="color: #6c757d; cursor: not-allowed;">
                          {{ getLocalizedTitle(exam) }}
                        </strong>
                        <i 
                          v-if="exam.ai_mock_interview" 
                          @click="$router.push(`/exam-detail/${exam.id}?t=${Date.now()}&returnTo=exam-detail`)"
                          class="fas fa-robot ms-2" 
                          style="color: #ff6b35; cursor: pointer;" 
                          :title="$t('examManagement.createForm.aiMockInterview')"
                        ></i>
                      </template>
                      <span v-if="exam.accuracy_percentage !== null && exam.accuracy_percentage !== undefined">
                        <small class="text-success ms-2">
                          {{ $t('examManagement.table.passRate') }}: {{ exam.accuracy_percentage.toFixed(1) }}%
                        </small>
                      </span>

                    </div>
                  </div>

                  <div class="text-center" style="width: 80px; flex-shrink: 0;">{{ exam.total_questions }}</div>
                  <div class="text-center" style="width: 80px; flex-shrink: 0;">
                    <span class="badge" :class="getExamPublicStatus(exam) ? 'bg-success' : 'bg-secondary'">
                      {{ getExamPublicStatus(exam) ? $t('examManagement.table.public') : $t('examManagement.filter.private') }}
                    </span>
                  </div>
                  <div class="text-center" style="width: 100px; flex-shrink: 0;" v-if="isAuthenticated">
                    <i v-if="getSubscribeStatus(exam)" class="fas fa-check text-success" style="font-size: 18px;" title="구독됨"></i>
                    <i v-else class="fas fa-circle text-muted" style="font-size: 12px; opacity: 0.3;" title="구독되지 않음"></i>
                  </div>
                  <div class="text-center" style="width: 180px; flex-shrink: 0;">
                    <div class="btn-group d-flex justify-content-start flex-wrap" role="group">
                      <button @click="viewExamDetails(exam)" class="btn btn-sm btn-secondary">{{ $t('examManagement.table.details') }}</button>
                      <button @click="retakeExam(exam.id)" class="btn btn-sm btn-warning" v-if="isAuthenticated">{{ $t('examManagement.table.copy') }}</button>
                      <button v-if="hasWrongQuestions(exam) && isAuthenticated" @click="retakeWrongQuestions(exam.id, exam.total_questions)" class="btn btn-sm btn-danger">{{ $t('examManagement.table.wrongQuestions') }}</button>

                      <button 
                        v-if="!isAdmin && isExamForCurrentUser(exam)" 
                        @click="deleteExam(exam.id)" 
                        class="btn btn-sm btn-danger"
                        :title="$t('examManagement.table.delete')"
                      >
                        {{ $t('examManagement.table.delete') }}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              
                                              <!-- 버전 시험들 -->
                <div v-if="expandedExams[exam.id] && exam.children && exam.children.length > 0" class="exam-versions">
                  <div v-for="version in exam.children" :key="String(version.id)" class="exam-row version-exam">
                    <div class="d-flex align-items-center">
                      <div class="checkbox-column" style="width: 15px; flex-shrink: 0;" v-if="isAuthenticated"><input type="checkbox" :checked="isExamSelected(String(version.id))" @change="toggleExamSelection(String(version.id), $event)" :disabled="!isAdmin && !isExamForCurrentUser(version)"></div>
                      <div class="flex-grow-1">
                        <div class="exam-title">
                          <span class="version-indent">└─</span>
                          <router-link 
                            v-if="getExamLink(version)"
                            :to="getExamLink(version)" 
                            class="exam-title-link"
                          >
                            <span class="text-muted">
                              {{ getLocalizedTitle(version) }}
                              <span v-if="version.version_number"> (v{{ version.version_number }})</span>
                            </span>
                          </router-link>
                          <span v-else class="text-muted" style="color: #6c757d; cursor: not-allowed;">
                            {{ getLocalizedTitle(version) }}
                            <span v-if="version.version_number"> (v{{ version.version_number }})</span>
                          </span>
                          <i 
                            v-if="version.ai_mock_interview" 
                            @click="$router.push(`/exam-detail/${version.id}?t=${Date.now()}&returnTo=exam-detail`)"
                            class="fas fa-robot ms-2" 
                            style="color: #17a2b8; cursor: pointer;" 
                            :title="$t('examManagement.createForm.aiMockInterview')"
                          ></i>
                          <span v-if="version.accuracy_percentage !== null && version.accuracy_percentage !== undefined">
                            <small class="text-success ms-2">
                              {{ $t('examManagement.table.passRate') }}: {{ version.accuracy_percentage.toFixed(1) }}%
                            </small>
                          </span>

                        </div>
                      </div>

                      <div class="text-center" style="width: 80px; flex-shrink: 0;">{{ version.total_questions }}</div>
                      <div class="text-center" style="width: 80px; flex-shrink: 0;">
                        <span class="badge" :class="getExamPublicStatus(version) ? 'bg-success' : 'bg-secondary'">
                          {{ getExamPublicStatus(version) ? $t('examManagement.table.public') : $t('examManagement.filter.private') }}
                        </span>
                      </div>
                      <div class="text-center" style="width: 100px; flex-shrink: 0;" v-if="isAuthenticated">
                        <i v-if="getSubscribeStatus(version)" class="fas fa-check text-success" style="font-size: 18px;" title="구독됨"></i>
                        <i v-else class="fas fa-circle text-muted" style="font-size: 12px; opacity: 0.3;" title="구독되지 않음"></i>
                      </div>
                      <div class="text-center" style="width: 180px; flex-shrink: 0;">
                        <div class="btn-group d-flex justify-content-start flex-wrap" role="group">
                          <button @click="viewExamDetails(version)" class="btn btn-sm btn-secondary">{{ $t('examManagement.table.details') }}</button>
                          <button 
                            v-if="hasWrongQuestions(version) && isAuthenticated"
                            @click="retakeWrongQuestions(version.id, version.total_questions)" 
                            class="btn btn-sm btn-danger"
                          >
                            {{ $t('examManagement.table.wrongQuestions') }}
                          </button>

                          <button 
                            v-if="!isAdmin && isExamForCurrentUser(version)" 
                            @click="deleteExam(version.id)" 
                            class="btn btn-sm btn-danger"
                            :title="$t('examManagement.table.delete')"
                          >
                            {{ $t('examManagement.table.delete') }}
                          </button>
                        </div>
                      </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
          <div v-else class="alert alert-info mt-3">
            {{ isAdmin ? $t('examManagement.noExams.admin') : isAuthenticated ? $t('examManagement.noExams.user') : $t('examManagement.noExams.guest') }}
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
                {{ $t('examManagement.pagination.info', { 
                  current: currentPage, 
                  total: totalPages, 
                  count: totalCount 
                }) || `페이지 ${currentPage} / ${totalPages} (총 ${totalCount}개 시험)` }}
              </small>
            </div>
          </div>
        </div>
      </div>

      <!-- 시험 상세 모달 -->
      <div v-if="selectedExam" class="modal fade show" style="display: block;" tabindex="-1">
        <div class="modal-dialog modal-lg">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">{{ getLocalizedTitle(selectedExam) }} {{ $t('examManagement.table.details') }}</h5>
              <button type="button" class="btn-close" @click="closeModal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
              <div class="row">
                <div class="col-md-6">
                  <h6>시험 정보</h6>
                  <p><strong>제목:</strong> {{ getLocalizedTitle(selectedExam) }}</p>
                  <p><strong>문제 수:</strong> {{ selectedExam.total_questions }}</p>
                  <p><strong>생성일:</strong> {{ formatDate(selectedExam.created_at) }}</p>
                  <p v-if="selectedExam.latest_score_percentage !== null">
                    <strong>{{ $t('examDetail.latestScore') }}:</strong> {{ selectedExam.latest_score_percentage ? selectedExam.latest_score_percentage.toFixed(1) : 'N/A' }}%
                  </p>
                </div>
                <div class="col-md-6">
                  <h6>시험 결과</h6>

                  <p><strong>평균 점수:</strong> {{ getAverageScore(selectedExam.id) }}</p>
                  <div v-if="selectedExam.versions && selectedExam.versions.length > 0">
                    <h6>재시험 버전</h6>
                    <div v-for="version in selectedExam.versions" :key="version.id" class="mb-2">
                      <small class="text-muted">{{ getLocalizedTitle(version) }}</small>
                    </div>
                  </div>
                </div>
              </div>
              <div v-if="selectedExam.questions && selectedExam.questions.length > 0">
                <h6>문제 목록</h6>
                <div v-for="(question, index) in selectedExam.questions" :key="String(question.id)" class="card mb-2">
                  <div class="card-body">
                    <h6>문제 {{ index + 1 }}</h6>
                    <p>{{ question.content }}</p>
                    <small class="text-muted">정답: {{ question.answer }}</small>
                    
                    <!-- 문제 통계 정보 -->
                    <div class="mt-2" v-if="getQuestionStats(question.id).total_attempts > 0">
                      <small class="text-info">
                        <i class="fas fa-play-circle"></i>
                        시도 횟수: {{ getQuestionStats(question.id).total_attempts }}회
                      </small>
                      <small class="text-success ms-3">
                        <i class="fas fa-check-circle"></i>
                        정답 횟수: {{ getQuestionStats(question.id).correct_attempts }}회
                      </small>
                      <small class="text-warning ms-3">
                        <i class="fas fa-percentage"></i>
                        정확도: {{ getQuestionStats(question.id).total_attempts > 0 ? 
                          ((getQuestionStats(question.id).correct_attempts / getQuestionStats(question.id).total_attempts) * 100).toFixed(1) : 0 }}%
                      </small>
                    </div>
                    <div v-else class="mt-2">
                      <small class="text-muted">
                        <i class="fas fa-info-circle"></i>
                        아직 시도하지 않은 문제입니다.
                      </small>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <router-link 
                v-if="!hasVersions(selectedExam)"
                :to="`/exam/${selectedExam.id}`" 
                class="btn btn-primary"
              >
                {{ $t('examManagement.table.details') }}
              </router-link>
              <button type="button" class="btn btn-secondary" @click="closeModal">{{ $t('common.close') }}</button>
            </div>
          </div>
        </div>
      </div>
      <div v-if="selectedExam" class="modal-backdrop fade show"></div>
    </div>
    
    <!-- Tag Filter Modal -->
    <TagFilterModal
      :show="showTagFilterModal"
      :selectedTags="selectedTagFilters"
      @update:show="showTagFilterModal = $event"
      @update:selectedTags="handleTagFilterUpdate"
      @apply="handleTagFilterApply"
      @error="handleTagFilterError"
    />
    
    <!-- New Exam Tag Modal -->
    <TagFilterModal
      :show="showNewExamTagModal"
      :selectedTags="newExamTags"
      @update:show="showNewExamTagModal = $event"
      @update:selectedTags="handleNewExamTagUpdate"
      @apply="handleNewExamTagApply"
      @error="handleTagFilterError"
      @tag-created="handleTagCreated"
    />
  </div>
</template>

<script>
// TODO: console.log를 debugLog로 변경할 수 있는지 반드시 검토해야 함
// - 운영 환경에서 브라우저 콘솔에 로그가 보이면 안 됨
// - debugLog는 운영 환경에서 자동으로 비활성화됨
import axios from 'axios'
import { debugLog } from '@/utils/debugUtils'
import { getLocalizedContentWithI18n, SUPPORTED_LANGUAGES } from '@/utils/multilingualUtils'
import {
  isAdmin,
  hasStudyAdminRole,
  getCurrentUser,
  isAuthenticated as isAuthenticatedUser
} from '@/utils/permissionUtils'
import { createDailyExam, checkTitleDuplicate } from '@/utils/examUtils'
import { formatLocalDate } from '@/utils/dateUtils'
import { isCacheEnabled, setSessionCache, getSessionCache, removeSessionCache, removeLocalCache } from '@/utils/cacheUtils'
import { convertToQuestionData } from '@/utils/problemParser'
import TagFilterModal from '@/components/TagFilterModal.vue'
import AiQuestionGenerator from '@/components/AiQuestionGenerator.vue'
import { 
  getCurrentDomainConfig,
  getForcedTags,
  applyTagFilter
} from '@/utils/domainUtils'

// 환경 확인
const isProduction = process.env.NODE_ENV === 'production'

/**
 * 시험 관리 컴포넌트
 * 
 * 캐시 정리 정책:
 * 1. 시험 생성/삭제/수정 시: clearCache() 호출로 관련 캐시 정리
 * 2. 강제 새로고침 시: emergencyCacheCleanup() 호출로 긴급 캐시 정리
 * 3. 시험 목록 로드 시: forceRefreshExamManagement 플래그로 캐시 무효화
 * 4. 브라우저 캐시: clearBrowserCache() 호출로 localStorage/sessionStorage 정리
 */
export default {
  name: 'ExamManagement',
  components: {
    TagFilterModal,
    AiQuestionGenerator
  },
  data() {
    return {
      exams: [],
      examResults: [],
      questionFiles: [],
      studyTasks: [], // StudyTask 데이터 추가
      loading: true, // 로딩 상태 추가
      saving: false, // 저장 중 상태 추가
      showCreateForm: false,
      showAiGenerator: false, // AI 문제 생성기 표시 상태
      parsedProblems: [], // 파싱된 문제 목록
      isLeetCodeDomain: false, // LeetCode 도메인 여부
      isLocalhost: false, // localhost 환경 여부
      newExam: {
        title: '',
        question_count: 0,
        file_name: '',
        is_public: true,
        force_answer: false,
        voice_mode_enabled: false,
        ai_mock_interview: false
      },
      titleError: '', // 제목 중복 에러 메시지
      titleValidationTimer: null, // 제목 검증 타이머
      selectedExam: null,
      selectedExams: [], // 일괄 삭제를 위한 배열
      questionStatistics: {}, // 문제별 통계 정보
      sortKey: 'title', // 정렬 키
      sortOrder: 'asc', // 정렬 순서 (asc, desc)
      expandedExams: {}, // 트리 확장/축소 상태 관리
      treeSortKey: 'default', // 트리 정렬 키 (기본값: 'default'로 설정하여 자동 정렬 적용)
      treeSortOrder: 'asc', // 트리 정렬 순서
      searchFilters: {
        title: '',
        isOriginal: '',
        isPublic: ''
      },
      selectedTagFilters: [], // 선택된 태그 필터들
      showTagFilterModal: false, // 태그 필터 모달 표시 상태
      newExamTags: [], // 새 시험 생성 시 선택된 태그들
      showNewExamTagModal: false, // 새 시험 태그 모달 표시 상태
      availableTags: [], // 사용 가능한 태그 목록
      // 검색 디바운싱을 위한 변수
      searchDebounceTimer: null,
      examTypeFilter: 'my', // 'my', 'public', 'all' - 기본값은 내 시험
      showUploadForm: false,
      selectedFile: null,
      uploadMessage: '',
      // 캐시 설정
      cacheEnabled: localStorage.getItem('cacheEnabled') !== 'false',
      // 토스트 알림 설정
      showToast: false,
      toastMessage: '',
      toastType: 'success',
      toastIcon: 'fas fa-check',
      // 모달 설정
      showModal: false,
      modalTitle: '',
      modalMessage: '',
      modalConfirmText: '',
      modalCancelText: '',
      modalConfirmButtonClass: 'btn-success',
      modalIcon: 'fas fa-question',
      modalCallback: null,
      isAutoSwitchingToPublic: false, // 자동 전환 플래그 추가


      // 페이지네이션 관련 변수들
      currentPage: 1,
      pageSize: 20,
      totalCount: 0,
      totalPages: 0,
      // 필터 row 표시 상태
      showFilterRow: false,
      // 사용자 프로필 언어 캐시
      userProfileLanguage: null
    }
  },
  computed: {
    isProductionEnv() {
      return process.env.NODE_ENV === 'production'
    },
    isAllSelected() {
      if (this.isAdmin) {
        // admin은 모든 시험과 버전 고려
        let totalCount = 0;
        this.filteredExamTree.forEach(exam => {
          totalCount++;
          if (exam.children && exam.children.length > 0) {
            totalCount += exam.children.length;
          }
        });
        return totalCount > 0 && this.selectedExams.length === totalCount;
      } else {
        // 일반 사용자는 자신의 시험과 버전만 고려
        let userExamCount = 0;
        this.filteredExamTree.forEach(exam => {
          if (this.isExamForCurrentUser(exam)) {
            userExamCount++;
          }
          if (exam.children && exam.children.length > 0) {
            exam.children.forEach(version => {
              if (this.isExamForCurrentUser(version)) {
                userExamCount++;
              }
            });
          }
        });
        return userExamCount > 0 && this.selectedExams.length === userExamCount;
      }
    },
    isIndeterminate() {
      if (this.isAdmin) {
        // admin은 모든 시험과 버전 고려
        let totalCount = 0;
        this.filteredExamTree.forEach(exam => {
          totalCount++;
          if (exam.children && exam.children.length > 0) {
            totalCount += exam.children.length;
          }
        });
        return this.selectedExams.length > 0 && this.selectedExams.length < totalCount;
      } else {
        // 일반 사용자는 자신의 시험과 버전만 고려
        let userExamCount = 0;
        this.filteredExamTree.forEach(exam => {
          if (this.isExamForCurrentUser(exam)) {
            userExamCount++;
          }
          if (exam.children && exam.children.length > 0) {
            exam.children.forEach(version => {
              if (this.isExamForCurrentUser(version)) {
                userExamCount++;
              }
            });
          }
        });
        return this.selectedExams.length > 0 && this.selectedExams.length < userExamCount;
      }
    },
    sortedExams() {
      // filteredExams가 배열인지 확인
      const filteredExams = this.filteredExams
      if (!Array.isArray(filteredExams)) {
        return []
      }
      
      const examsWithResultCount = filteredExams.map(exam => ({
        ...exam
      }))
      
      // 사용자가 멤버인 스터디의 시험만 반환 (원본/복제 구분 없이)
      return examsWithResultCount.sort((a, b) => {
        // 1순위: "Today's Quizzes for" 시험을 맨 위에
        const aTitle = getLocalizedContentWithI18n(a, 'title', this.$i18n, this.userProfileLanguage, '') || ''
        const bTitle = getLocalizedContentWithI18n(b, 'title', this.$i18n, this.userProfileLanguage, '') || ''
        const aIsTodayQuiz = aTitle.includes("Today's Quizzes for")
        const bIsTodayQuiz = bTitle.includes("Today's Quizzes for")
        
        if (aIsTodayQuiz && !bIsTodayQuiz) return -1
        if (!aIsTodayQuiz && bIsTodayQuiz) return 1
        
        // 2순위: 최근 생성된 시험을 위쪽에 (created_at 기준 내림차순)
        const aCreatedAt = new Date(a.created_at || 0)
        const bCreatedAt = new Date(b.created_at || 0)
        
        if (aCreatedAt > bCreatedAt) return -1
        if (aCreatedAt < bCreatedAt) return 1
        
        // 3순위: 생성일이 같은 경우, 종료되지 않은 시험(결과가 없는 시험)을 위쪽에
        const aHasResults = a.has_results || false
        const bHasResults = b.has_results || false
        
        if (!aHasResults && bHasResults) return -1
        if (aHasResults && !bHasResults) return 1
        
        // 4순위: 제목 알파벳 순 (다국어 지원) - 이미 위에서 계산한 aTitle, bTitle 재사용
        return aTitle.localeCompare(bTitle)
      })
    },
    
    // 현재 사용자 언어에 맞는 시험 제목 반환
    getLocalizedTitle() {
      return (exam) => {
        if (!exam) return ''
        
        // 사용자 프로필 언어 가져오기 (동기적으로, 캐시 우선)
        let userLang = this.userProfileLanguage
        
        // userProfileLanguage가 없으면 동적으로 가져오기 (동기적으로는 불가능하므로 기본값 사용)
        if (!userLang) {
          console.warn('[ExamManagement] userProfileLanguage가 null입니다. 기본값 "en" 사용')
          userLang = 'en'
        }
        
        // 사용자 언어에 맞는 언어별 필드가 있으면 우선 사용
        // display_title 사용 (백엔드에서 올바르게 처리된 경우)
        if (exam.display_title && exam.display_title.trim()) {
          debugLog(`✅ [ExamManagement] getLocalizedTitle - display_title 사용: "${exam.display_title}"`)
          return exam.display_title
        }
        
        // display_title도 없으면 폴백 로직 사용
        debugLog(`⚠️ [ExamManagement] getLocalizedTitle - display_title이 없음. exam.display_title: "${exam.display_title}", exam.id: ${exam.id}`)
        
        // 사용자 언어에 맞는 제목 반환
        const result = getLocalizedContentWithI18n(exam, 'title', this.$i18n, userLang, exam.title || 'No Title')
        debugLog(`🔄 [ExamManagement] getLocalizedTitle - fallback 사용: "${result}", userLang: "${userLang}"`)
        return result
      }
    },
    
    // 현재 사용자 언어에 맞는 시험 설명 반환
    getLocalizedDescription() {
      return (exam) => {
        if (!exam) return ''
        
        return getLocalizedContentWithI18n(
          exam,
          'description',
          this.$i18n,
          this.userProfileLanguage,
          ''
        )
      }
    },
    

    
    // 사용자와 연관된 시험만 필터링 (내 시험 - 공개 여부와 상관없이 사용자와 연관된 시험)
    filteredExams() {
      console.log('🔍 filteredExams 호출됨')
      console.log('🔍 this.exams:', this.exams)
      console.log('🔍 this.examTypeFilter:', this.examTypeFilter)
      console.log('🔍 this.isAuthenticated:', this.isAuthenticated)
      console.log('🔍 this.currentUser:', this.currentUser)
      
      // exams가 최적화된 API 응답 구조인지 확인
      let examList = []
      if (this.exams && this.exams.results) {
        examList = this.exams.results
        if (!isProduction) {
          debugLog('🔍 results 구조 사용, examList 길이:', examList.length)
        }
      } else if (Array.isArray(this.exams)) {
        examList = this.exams
        if (!isProduction) {
          debugLog('🔍 배열 구조 사용, examList 길이:', examList.length)
        }
      } else {
        if (!isProduction) {
          debugLog('🔍 exams가 예상과 다른 구조:', this.exams)
        }
        examList = []
      }
      
      // examList가 배열이 아니면 빈 배열로 설정
      if (!Array.isArray(examList)) {
        examList = []
      }
      
      const user = this.currentUser
      
      // 익명 사용자 처리
      if (!user) {
        // 익명 사용자는 공개 시험만 접근 가능
        return examList.filter(exam => exam && exam.is_public === true)
      }
      
      // examTypeFilter에 따른 필터링 적용
      if (this.examTypeFilter === 'public') {
        // 공개 시험 필터: 모든 공개 시험 반환
        return examList.filter(exam => exam.is_public === true)
      } else if (this.examTypeFilter === 'all') {
        // 모든 시험 필터: 관리자만 모든 시험 반환
        if (user.role === 'admin_role' || user.role === 'study_admin_role') {
          return examList
        } else {
          // 일반 사용자는 공개 시험만 반환
          return examList.filter(exam => exam.is_public === true)
        }
      } else {
        // 'my' 필터 또는 기본값: 사용자와 연관된 시험만 반환
        
        // admin_role 또는 study_admin_role 사용자는 모든 시험에 접근 가능
        if (user.role === 'admin_role' || user.role === 'study_admin_role') {
          return examList
        }
        
        // 일반 사용자는 다음 조건 중 하나를 만족하는 시험만 필터링
        return examList.filter(exam => {
          // 1. 공개된 시험 (공개 시험은 모든 사용자가 접근 가능)
          if (exam.is_public === true) {
            return true
          }
          
          // 2. favorite 시험은 자신과 admin에게만 노출 (내 시험)
          const examTitle = getLocalizedContentWithI18n(exam, 'title', this.$i18n, this.userProfileLanguage, '') || ''
          if (examTitle.includes("'s favorite")) {
            const favoriteUsername = examTitle.replace("'s favorite", '')
            return user.username === favoriteUsername || user.role === 'admin_role'
          }
          
          // 3. 사용자가 멤버인 스터디의 StudyTask에 연결된 시험 (내 시험 - 공개 여부와 상관없이)
          if (Array.isArray(this.studyTasks)) {
            const currentUser = this.currentUser
            const isStudyTaskExam = this.studyTasks.some(task => {
              if (!task || !task.exam || task.exam.id !== exam.id) return false
              
              // 사용자가 해당 스터디의 멤버인지 확인
              if (!currentUser || !task.study || !task.study.members) return false
              
              return Array.isArray(task.study.members) &&
                task.study.members.some(member => {
                  if (!member.user) return false
                  const memberUserId = typeof member.user === 'object' ? member.user.id : member.user
                  return String(memberUserId) === String(currentUser.id)
                })
            })
            if (isStudyTaskExam) {
              return true
            }
          }
          
          // 4. "내 시험" 필터일 때만 풀어본 시험 표시
          if (this.examTypeFilter === 'my') {
            const examResults = this.examResults || []
            const hasTakenExam = examResults.some(result => 
              result && result.exam && result.exam.id === exam.id
            )
            if (hasTakenExam) {
              return true
            }
          }
          
          // 5. 내가 생성한 시험 (created_by 필드로 확인)
          if (exam.created_by && exam.created_by.username === user.username) {
            return true
          }
          
          return false
        })
      }
    },
    // 사용자가 특정 스터디의 멤버인지 확인 (computed 내부에서 사용)
    checkUserMemberOfStudy(study) {
      const user = this.currentUser
      if (!user || !study || !study.members) return false
      
      return Array.isArray(study.members) &&
        study.members.some(member => {
          if (!member.user) return false
          const memberUserId = typeof member.user === 'object' ? member.user.id : member.user
          return String(memberUserId) === String(user.id)
        })
    },
    // 사용자가 특정 스터디의 멤버인지 확인
    isUserMemberOfStudy(study) {
      const user = this.currentUser
      if (!user || !study || !study.members) return false
      
      return Array.isArray(study.members) &&
        study.members.some(member => {
          if (!member.user) return false
          const memberUserId = typeof member.user === 'object' ? member.user.id : member.user
          return String(memberUserId) === String(user.id)
        })
    },
    // 트리 구조로 시험 데이터 구성 - 성능 최적화
    examTree() {
      const tree = []
      const sortedExams = this.sortedExams || []
      
      sortedExams.forEach(originalExam => {
        const examNode = {
          ...originalExam,
          children: [],
        }
        
        // 버전들 추가
        if (originalExam.versions && originalExam.versions.length > 0) {
          examNode.children.push(...originalExam.versions.map(version => ({
            ...version,
            isChild: true
          })))
        }
        
        tree.push(examNode)
      })
      
      return tree
    },
    filteredExamTree() {
      const examTree = this.examTree || []
      let filtered = examTree

      console.log('🔍 filteredExamTree 시작 - 전체 시험 수:', filtered ? filtered.length : 0)
      console.log('🔍 현재 필터 설정:', {
        examTypeFilter: this.examTypeFilter,
        searchFilters: this.searchFilters
      })
      console.log('🔍 this.examTree:', this.examTree)

      // 시험 타입 필터 적용
      if (this.examTypeFilter === 'my') {
        // 내 시험만 표시 - 공개 여부와 상관없이 사용자와 연관된 시험들만 필터링
        if (this.isAuthenticated) {
          filtered = filtered.filter(exam => this.isExamForCurrentUser(exam))
          if (!isProduction) {
            debugLog('🔍 내 시험 필터 적용 후:', filtered.length, '개')
          }
        } else {
          // 익명 사용자는 내 시험 필터를 사용할 수 없음
          filtered = []
          if (!isProduction) {
            debugLog('🔍 익명 사용자는 내 시험 필터를 사용할 수 없음')
          }
        }
      } else if (this.examTypeFilter === 'public') {
        // 공개 시험만 표시
        console.log('🔍 공개 시험 필터 적용 시작')
        console.log('🔍 필터링 전 시험들:', filtered.map(exam => ({
          id: exam.id,
          title: this.getLocalizedTitle(exam),
          is_public: exam.is_public,
          getExamPublicStatus: this.getExamPublicStatus(exam)
        })))
        
        filtered = filtered.filter(exam => this.getExamPublicStatus(exam))
        
        console.log('🔍 공개 시험 필터 적용 후:', filtered.length, '개')
        console.log('🔍 필터링 후 시험들:', filtered.map(exam => ({
          id: exam.id,
          title: this.getLocalizedTitle(exam),
          is_public: exam.is_public
        })))
      }
      // 'all'인 경우 모든 시험 표시 (관리자만)

      if (this.searchFilters.title) {
        filtered = filtered.filter(exam => 
          exam.display_title.toLowerCase().includes(this.searchFilters.title.toLowerCase())
        )
        if (!isProduction) {
          debugLog('🔍 제목 검색 필터 적용 후:', filtered.length, '개')
        }
      }

      if (this.searchFilters.isOriginal) {
        filtered = filtered.filter(exam => 
          exam.is_original === (this.searchFilters.isOriginal === 'true')
        )
        if (!isProduction) {
          debugLog('🔍 원본/복제 필터 적용 후:', filtered.length, '개')
        }
      }

      if (this.searchFilters.isPublic) {
        filtered = filtered.filter(exam => 
          this.getExamPublicStatus(exam) === (this.searchFilters.isPublic === 'true')
        )
        if (!isProduction) {
          debugLog('🔍 공개/비공개 필터 적용 후:', filtered.length, '개')
        }
      }

      // LeetCode Dev 시험 확인
              const leetcodeExam = filtered.find(exam => 
          getLocalizedContentWithI18n(exam, 'title', this.$i18n, this.userProfileLanguage, '') === 'LeetCode Dev'
        )
      if (!isProduction) {
        if (leetcodeExam) {
          debugLog('✅ 필터링 후 LeetCode Dev 시험 발견:', leetcodeExam.title)
        } else {
          debugLog('❌ 필터링 후 LeetCode Dev 시험을 찾을 수 없습니다')
          debugLog('🔍 필터링된 시험 제목들:', filtered.map(exam => this.getLocalizedTitle(exam)))
        }
      }

      // 정렬 적용
      if (!filtered || !Array.isArray(filtered)) {
        return []
      }
      const sorted = filtered.sort((a, b) => {
        // 사용자가 정렬 컬럼을 클릭한 경우 해당 정렬 적용
        if (this.treeSortKey && this.treeSortKey !== 'default') {
          let aValue, bValue
          
          // 제목 정렬을 위한 특별 처리
          if (this.treeSortKey === 'title') {
            aValue = this.getLocalizedTitle(a) || ''
            bValue = this.getLocalizedTitle(b) || ''
          } else {
            aValue = a[this.treeSortKey]
            bValue = b[this.treeSortKey]
          }
          
          // 날짜 정렬을 위한 변환
          if (this.treeSortKey === 'created_at') {
            aValue = new Date(aValue)
            bValue = new Date(bValue)
          }
          
          // 문제 수 정렬을 위한 변환
          if (this.treeSortKey === 'total_questions') {
            aValue = parseInt(aValue) || 0
            bValue = parseInt(bValue) || 0
          }
          
          // 점수 정렬을 위한 변환
          if (this.treeSortKey === 'latest_score_percentage') {
            aValue = aValue || 0
            bValue = bValue || 0
          }
          
          if (aValue < bValue) {
            return this.treeSortOrder === 'asc' ? -1 : 1
          }
          if (aValue > bValue) {
            return this.treeSortOrder === 'asc' ? 1 : -1
          }
          return 0
        }
        
        // 기본 정렬: Today's Quizzes for xxxx를 맨 위에, 그 다음 최근 생성된 시험 순서
        // 1순위: "Today's Quizzes for xxxx" 형식의 시험을 맨 위에
        const aTitle = getLocalizedContentWithI18n(a, 'title', this.$i18n, this.userProfileLanguage, '') || ''
        const bTitle = getLocalizedContentWithI18n(b, 'title', this.$i18n, this.userProfileLanguage, '') || ''
        const aIsDailyQuiz = aTitle.includes("Today's Quizzes for")
        const bIsDailyQuiz = bTitle.includes("Today's Quizzes for")
        
        if (aIsDailyQuiz && !bIsDailyQuiz) return -1
        if (!aIsDailyQuiz && bIsDailyQuiz) return 1
        
        // 2순위: Daily Quiz가 아닌 경우, 최근 생성된 시험을 위쪽에 (created_at 기준 내림차순)
        const aCreatedAt = new Date(a.created_at || 0)
        const bCreatedAt = new Date(b.created_at || 0)
        
        if (aCreatedAt > bCreatedAt) return -1
        if (aCreatedAt < bCreatedAt) return 1
        
        // 3순위: 생성일이 같은 경우, 종료되지 않은 시험(결과가 없는 시험)을 위쪽에
        const aHasResults = a.has_results || false
        const bHasResults = b.has_results || false
        
        if (!aHasResults && bHasResults) return -1
        if (aHasResults && !bHasResults) return 1
        
        // 4순위: 제목 알파벳 순 (다국어 지원) - 이미 위에서 계산한 aTitle, bTitle 재사용
        return aTitle.localeCompare(bTitle)
      })
      
      return sorted
    },
    maxQuestions() {
      if (this.newExam.file_name) {
        const file = this.questionFiles.find(f => f.name === this.newExam.file_name)
        return file ? file.max_questions : 0
      }
      return 0
    },
    isAdmin() {
      return isAdmin()
    },
    isStudyAdmin() {
      return hasStudyAdminRole()
    },
    isAuthenticated() {
      return isAuthenticatedUser()
    },
    currentUser() {
      return getCurrentUser()
    },
    hasUserExams() {
      // 현재 사용자를 위해 생성된 시험이 있는지 확인
      return this.filteredExamTree.some(exam => this.isExamForCurrentUser(exam))
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
    }
  },
  watch: {
    'newExam.file_name': function(newFileName) {
      if (newFileName) {
        const file = this.questionFiles.find(f => f.name === newFileName)
        if (file && file.max_questions > 0) {
          this.newExam.question_count = file.max_questions
        }
      }
    },
    'searchFilters.isOriginal': function(newVal) {
      if (newVal === '') {
        this.expandedExams = {};
      }
      // 필터 변경 시 첫 페이지로 이동
      this.currentPage = 1
    },
    'searchFilters.isPublic': function() {
      // 필터 변경 시 첫 페이지로 이동
      this.currentPage = 1
    },
    'searchFilters.title': function() {
      // 검색어 변경 시 첫 페이지로 이동
      this.currentPage = 1
    },
    async examTypeFilter(newValue) {
      console.log('🔄 examTypeFilter watch 호출됨:', newValue, 'isAuthenticated:', this.isAuthenticated)
      // 시험 타입 필터가 변경되면 캐시를 클리어하고 데이터를 다시 로드
      this.clearCache()
      // 강제 새로고침 플래그 설정
      sessionStorage.setItem('forceRefreshExamManagement', 'true')
      // 필터 변경 시 첫 페이지로 이동
      this.currentPage = 1
      
      if (newValue === 'my') {
        // My Exams로 변경할 때는 태그 필터를 초기화하여 태그가 없는 시험도 보여줌
        console.log('📋 My Exams로 변경됨, 태그 필터 초기화')
        this.selectedTagFilters = []
      } else if (newValue === 'public' && this.isAuthenticated) {
        // Public Exams로 변경되고 로그인된 사용자인 경우 관심 카테고리 태그 자동 설정
        // 태그 설정 후 loadExams가 호출되므로 태그 필터가 적용됨
        console.log('📋 Public Exams로 변경됨, 관심 카테고리 태그 설정 시작')
        await this.setupInterestedCategoryTags()
        console.log('✅ setupInterestedCategoryTags 완료, selectedTagFilters:', this.selectedTagFilters)
      }
      
      // loadExams는 setupInterestedCategoryTags 후에 호출되어 태그 필터가 적용된 상태로 로드됨
      this.loadExams()
    },
    selectedExam: {
      handler(newExam) {
        if (newExam && newExam.id) {
          this.loadQuestionStatistics(newExam.id)
        }
      },
      immediate: true
    }
  },
  async mounted() {
    // LeetCode 도메인 감지
    this.isLeetCodeDomain = window.location.hostname.includes('leetcode')
    
    // localhost 환경 감지
    this.isLocalhost = window.location.hostname === 'localhost' || 
                      window.location.hostname === '127.0.0.1' || 
                      window.location.hostname.includes('localhost')
    
    // 로그인하지 않은 사용자의 경우 기본 필터를 "public"으로 설정
    if (!this.isAuthenticated) {
      this.examTypeFilter = 'public'
    }
    
    // 사용자 프로필 언어 초기화
    await this.getUserProfileLanguage()
    
    // 태그 목록 로드 (도메인별 태그 설정 전에 먼저 로드)
    await this.loadAvailableTags();
    
    // 도메인별 초기 태그 설정 (태그 목록 로드 후 실행)
    const domainConfig = getCurrentDomainConfig()
      if (domainConfig) {
        if (domainConfig.keyword === 'devops') {
          const devopsTags = getForcedTags(domainConfig, this.availableTags)
          if (devopsTags.length > 0) {
            this.selectedTagFilters = devopsTags
          }
        } else if (domainConfig.keyword === 'leetcode') {
          const leetcodeTags = getForcedTags(domainConfig, this.availableTags)
          if (leetcodeTags.length > 0) {
            this.selectedTagFilters = leetcodeTags
          }
        }
      }
    
    this.loading = true
    try {
      // URL에서 타임스탬프 파라미터 확인 (시험 완료 후 자동 새로고침)
      const urlParams = new URLSearchParams(window.location.search)
      const timestamp = urlParams.get('t')
      
      // 타임스탬프가 있거나 강제 새로고침 플래그가 있을 때만 캐시 무효화
      const forceRefresh = sessionStorage.getItem('forceRefreshExamManagement')
      if (timestamp || forceRefresh) {
        if (timestamp) {
          // 타임스탬프가 있으면 강제 새로고침 수행
          debugLog('🔄 시험 완료 후 자동 새로고침 감지됨')
          
          // URL에서 타임스탬프 파라미터 제거
          const newUrl = window.location.pathname + (urlParams.toString() ? '?' + urlParams.toString().replace(/[&]t=\d+/, '') : '')
          window.history.replaceState({}, '', newUrl)
        }
        
        // 강제로 캐시 무효화하고 새 데이터 로드
        this.clearCache()
        this.emergencyCacheCleanup()
        this.clearBrowserCache()
        sessionStorage.setItem('forceRefreshExamManagement', 'true')
        sessionStorage.setItem('forceRefreshHome', 'true')
        sessionStorage.setItem('forceRefreshProfile', 'true')
      }
      
      // 병렬로 데이터 로드 및 초기화 작업 수행
      // Promise.allSettled를 사용하여 일부 실패해도 나머지는 계속 진행
      const loadPromises = []
      
      if (this.isAuthenticated) {
        // 인증된 사용자의 경우 모든 데이터 로드
        loadPromises.push(
          this.loadExams(),
          this.loadExamResults(),
          this.loadQuestionFiles(),
          this.loadStudyTasks()
        )
        
        // Quiz Count 변경 감지와 관심 카테고리 태그 설정을 병렬로 실행
        // (이미 user-profile API가 호출되었을 수 있으므로 병렬 실행으로 중복 최소화)
        if (this.examTypeFilter === 'public' && this.selectedTagFilters.length === 0) {
          loadPromises.push(this.setupInterestedCategoryTags())
        }
        loadPromises.push(this.checkQuizCountChange())
      } else {
        // 익명 사용자는 공개 시험 목록과 문제 파일만 로드
        loadPromises.push(
          this.loadExams(),
          this.loadQuestionFiles()
        )
      }
      
      await Promise.allSettled(loadPromises)
      
      this.selectedExams = [];
    } finally {
      this.loading = false
    }
  },
  methods: {
    toggleFilterRow() {
      this.showFilterRow = !this.showFilterRow
    },
    // 사용자의 Quiz Count 변경 감지 (캐시 활용하여 성능 최적화)
    async checkQuizCountChange() {
      try {
        // 현재 사용자 정보 가져오기
        const userData = this.currentUser
        if (!userData) return
        const currentUsername = userData.username
        
        // 이전 Quiz Count 확인
        const previousQuizCount = sessionStorage.getItem(`quizCount_${currentUsername}`)
        
        // 마지막 체크 시간 확인 (5분 이내면 스킵)
        const lastCheckTime = sessionStorage.getItem(`quizCountCheckTime_${currentUsername}`)
        const now = Date.now()
        if (lastCheckTime && (now - parseInt(lastCheckTime)) < 5 * 60 * 1000) {
          // 5분 이내에 체크했으면 스킵
          return
        }
        
        // 사용자 프로필에서 현재 Quiz Count 가져오기
        const response = await axios.get('/api/user-profile/get/')
        const currentQuizCount = response.data.random_exam_question_count
        
        // 체크 시간 저장
        sessionStorage.setItem(`quizCountCheckTime_${currentUsername}`, now.toString())
        
        // Quiz Count가 변경된 경우 캐시 정리
        if (previousQuizCount && previousQuizCount !== currentQuizCount.toString()) {
          debugLog(`🔄 Quiz Count 변경 감지: ${previousQuizCount} -> ${currentQuizCount}`)
          
          // Today's exam 관련 캐시 정리
          this.clearTodayExamCache()
          
          // 새로운 Quiz Count 저장
          sessionStorage.setItem(`quizCount_${currentUsername}`, currentQuizCount.toString())
          
          // 사용자에게 안내
          this.showToastNotification(
            `Quiz Count가 ${previousQuizCount}에서 ${currentQuizCount}로 변경되었습니다. Today's exam이 업데이트되었습니다.`, 
            'info'
          )
        } else if (!previousQuizCount) {
          // 처음 로드하는 경우 현재 Quiz Count 저장
          sessionStorage.setItem(`quizCount_${currentUsername}`, currentQuizCount.toString())
        }
      } catch (error) {
        debugLog('Quiz Count 변경 감지 중 오류:', error, 'error')
      }
    },
    
    // Today's exam 관련 캐시만 정리
    clearTodayExamCache() {
      try {
        // Today's exam 관련 캐시 키들
        const todayExamKeys = [
          'forceRefreshExamManagement',
          'forceRefreshHome'
        ]
        
        todayExamKeys.forEach(key => {
          sessionStorage.removeItem(key)
          localStorage.removeItem(key)
        })
        
        // Today's exam 관련 키들을 포함하는 모든 캐시 정리
        const sessionKeys = Object.keys(sessionStorage)
        sessionKeys.forEach(key => {
          if (key.includes('Today') || key.includes('daily') || key.includes('quiz') || key.includes('Exam')) {
            sessionStorage.removeItem(key)
          }
        })
        
        // 강제 새로고침 플래그 설정
        sessionStorage.setItem('forceRefreshExamManagement', 'true')
        
        debugLog('Today\'s exam 관련 캐시 정리 완료')
      } catch (error) {
        debugLog('Today\'s exam 관련 캐시 정리 중 오류:', error, 'error')
      }
    },
    
    // 토스트 알림 메서드들
    showToastNotification(message, type = 'success', icon = null) {
      this.toastMessage = message
      this.toastType = type
      this.toastIcon = icon || this.getToastIcon(type)
      this.showToast = true
      
      // 3초 후 자동으로 숨기기
      setTimeout(() => {
        this.hideToast()
      }, 3000)
    },
    
    hideToast() {
      this.showToast = false
    },
    
    getToastIcon(type) {
      switch (type) {
        case 'success':
          return 'fas fa-check'
        case 'error':
          return 'fas fa-exclamation-triangle'
        case 'warning':
          return 'fas fa-exclamation-circle'
        case 'info':
          return 'fas fa-info-circle'
        default:
          return 'fas fa-info-circle'
      }
    },
    
    // 모달 메서드들
    showConfirmModal(title, message, confirmText = null, cancelText = null, confirmButtonClass = 'btn-success', icon = 'fas fa-question', callback = null) {
      this.modalTitle = title
      this.modalMessage = message
      this.modalConfirmText = confirmText || this.$t('common.confirm')
      this.modalCancelText = cancelText || this.$t('common.cancel')
      this.modalConfirmButtonClass = confirmButtonClass
      this.modalIcon = icon
      this.modalCallback = callback
      this.showModal = true
    },
    
    confirmModal() {
      if (this.modalCallback) {
        this.modalCallback()
      }
      this.hideModal()
    },
    
    cancelModal() {
      this.hideModal()
    },
    
    hideModal() {
      this.showModal = false
      this.modalCallback = null
    },
    
    handleCreateExam() {
      if (!this.isAuthenticated) {
        this.$router.push('/login')
        return
      }
      this.toggleCreateForm()
    },
    
    async refreshExams() {
      try {
        // 로딩 상태 시작
        this.loading = true
        
        // 강제 새로고침 플래그 설정
        sessionStorage.setItem('forceRefreshExamManagement', 'true')
        
        // 병렬로 데이터 로드
        await Promise.all([
          this.loadExams(),
          this.loadExamResults()
        ])
        
        // 캐시 업데이트
        this.cacheData()
        
        // 강제 새로고침 플래그 제거
        sessionStorage.removeItem('forceRefreshExamManagement')
      } catch (error) {
        debugLog('시험 목록 새로고침 실패:', error, 'error')
      } finally {
        // 로딩 상태 종료
        this.loading = false
      }
    },
    async getUserProfileLanguage() {
      try {
        // 캐시에 있으면 반환
        if (this.userProfileLanguage) {
          return this.userProfileLanguage
        }
        
        // 사용자 프로필에서 언어 가져오기
        if (this.isAuthenticated) {
          const response = await axios.get('/api/user-profile/get/')
          const language = response.data.language || 'en'
          // 캐시에 저장 (중요: this.userProfileLanguage에 저장)
          this.userProfileLanguage = language
          return language
        }
        
        // 비로그인 사용자는 기본값
        this.userProfileLanguage = 'en'
        return 'en'
      } catch (error) {
        console.error('사용자 프로필 언어 가져오기 실패:', error)
        this.userProfileLanguage = 'en'
        return 'en'
      }
    },
    async loadExams() {
      try {
        // 로딩 상태 시작
        this.loading = true
        
        // 사용자의 Quiz Count 변경 감지는 mounted에서만 수행 (성능 최적화)
        // loadExams는 페이지네이션 등으로 자주 호출되므로 여기서는 체크하지 않음
        
        // 강제 새로고침 플래그 확인
        const forceRefresh = sessionStorage.getItem('forceRefreshExamManagement')
        let url = '/api/exams/'
        const params = []
        
        // 페이지네이션 파라미터
        params.push(`page=${this.currentPage}`)
        params.push(`page_size=${this.pageSize}`)
        
        // 사용자 프로필 언어에 맞는 필드만 선택 (성능 최적화)
        // 현재 언어 필드 + 영어 fallback 필드 + display_title, display_description 필드만 요청
        const userProfileLanguage = await this.getUserProfileLanguage()
        const selectFields = ['id', 'created_at', 'is_original', 'original_exam', 'version_number', 'is_public', 'total_questions', 'created_by', 'created_language', 'ai_mock_interview', 'display_title']
        
        // 현재 언어 필드 추가 (모든 지원 언어 동적 처리)
        const supportedLanguages = SUPPORTED_LANGUAGES
        if (supportedLanguages.includes(userProfileLanguage)) {
          selectFields.push(`title_${userProfileLanguage}`, `description_${userProfileLanguage}`, `is_${userProfileLanguage}_complete`)
        }
        
        // 영어 fallback 필드 추가 (항상 필요)
        selectFields.push('title_en', 'description_en', 'is_en_complete')
        
        params.push(`select=${selectFields.join(',')}`)
        params.push(`lang=${userProfileLanguage}`)
        
        debugLog(`🌐 [ExamManagement] API 요청 URL: ${url}?${params.join('&')}`)
        debugLog(`🌐 [ExamManagement] 요청 파라미터 - lang: ${userProfileLanguage}, select: ${selectFields.join(',')}`)
        
        // examTypeFilter에 따른 API 파라미터 설정
        if (this.examTypeFilter === 'public') {
          // 공개 시험만 요청
          params.push('is_public=true')
        } else if (this.examTypeFilter === 'my' && this.isAuthenticated) {
          // 내 시험만 요청 (로그인한 사용자)
          // my_exams=true: 내가 생성한 시험 + 내가 참여한 스터디의 시험 + 내가 응시한 시험 + Today's Quizzes
          // TODO: 백엔드에서 my_exams=true 로직에 공개 시험을 포함하고 있어서 수정 필요
          params.push('my_exams=true')
        } else if (!this.isAuthenticated) {
          // 익명 사용자는 공개 시험만 볼 수 있음
          params.push('is_public=true')
        }
        
        // 검색 필터 파라미터 추가
        if (this.searchFilters.isPublic) {
          params.push(`is_public=${this.searchFilters.isPublic}`)
        }
        if (this.searchFilters.isOriginal) {
          params.push(`is_original=${this.searchFilters.isOriginal}`)
        }
        if (this.searchFilters.title) {
          params.push(`search_title=${encodeURIComponent(this.searchFilters.title)}`)
        }
        
        // 사용자 연령 등급 기반 자동 필터링 (로그인한 사용자만)
        if (this.isAuthenticated && this.currentUser && this.currentUser.age_rating) {
          // 사용자의 연령 등급에 맞는 시험만 표시
          // 예: 12+ 사용자는 4+, 9+, 12+ 시험만 볼 수 있음
          const userAgeRating = this.currentUser.age_rating
          params.push(`age_rating=${userAgeRating}`)
        }
        
        // Public Exams에서 관심 카테고리에 태그가 없을 때는 빈 결과를 직접 설정
        // (My Exams에서는 태그가 없어도 모든 시험을 보여줘야 하므로 이 조건은 적용하지 않음)
        // selectedTagFilters가 null이거나 undefined이거나 빈 배열이면 태그 필터를 적용하지 않음
        // 이는 관심 카테고리가 없거나 태그가 없을 때 모든 공개 시험을 보여주기 위함
        // DevOps 도메인인 경우는 강제로 DevOps 태그를 적용하므로 제외
        const domainConfig = getCurrentDomainConfig()
        
        // DevOps 도메인인 경우 강제로 DevOps 태그를 적용
        if (domainConfig && domainConfig.keyword === 'devops') {
          console.log('🏷️ DevOps 도메인 - 강제 DevOps 태그 적용')
          const devopsTags = applyTagFilter(domainConfig, this.selectedTagFilters)
          devopsTags.forEach(tagId => {
            params.push(`tags=${tagId}`)
          })
          console.log('📊 강제 적용된 DevOps 태그:', devopsTags)
        } else if (this.selectedTagFilters && Array.isArray(this.selectedTagFilters) && this.selectedTagFilters.length > 0) {
          // 각 태그 ID를 개별 파라미터로 전달 (백엔드 getlist() 메서드용)
          this.selectedTagFilters.forEach(tagId => {
            params.push(`tags=${tagId}`)
          })
        }
        
        if (forceRefresh === 'true') {
          // 강제 새로고침: 캐시 완전 무효화
          params.push('t=' + Date.now())
          params.push('cache=' + Math.random())
          params.push('refresh=' + Date.now())
          params.push('force=' + Date.now())
          
          // 추가 캐시 무효화
          this.clearCache()
          this.emergencyCacheCleanup()
          this.clearBrowserCache()
          
          // 강제 새로고침 플래그 제거
          sessionStorage.removeItem('forceRefreshExamManagement')
          debugLog('🔄 강제 새로고침 모드로 데이터 로드')
        }
        // 일반 로드: 타임스탬프를 추가하지 않아 백엔드 캐시 활용 (성능 최적화)
        
        // 파라미터가 있으면 URL에 추가
        if (params.length > 0) {
          url += '?' + params.join('&')
        }
        
        if (!isProduction) {
          debugLog('🔍 최적화된 시험 데이터 로드 시작:', url)
          debugLog('🔍 examTypeFilter:', this.examTypeFilter)
          debugLog('🔍 현재 사용자:', this.currentUser?.username)
          debugLog('🔍 인증 상태:', this.isAuthenticated)
        }
        
        const response = await axios.get(url)
        debugLog(`📥 [ExamManagement] API 응답 수신 - 전체 응답:`, JSON.stringify(response.data, null, 2))
        if (!isProduction) {
          debugLog('🔍 API 응답:', response.data)
        }
        
        // 페이지네이션 정보 먼저 업데이트 (응답 구조와 관계없이)
        if (response.data.pagination) {
          this.currentPage = response.data.pagination.page || 1
          this.totalCount = response.data.pagination.total_count || 0
          const receivedTotalPages = response.data.pagination.total_pages || 0
          
          // total_pages 검증: total_count와 page_size로 재계산하여 일치하는지 확인
          const calculatedTotalPages = this.totalCount > 0 
            ? Math.ceil(this.totalCount / this.pageSize) 
            : 0
          
          // 백엔드에서 받은 total_pages와 계산한 값이 다르면 경고
          if (receivedTotalPages !== calculatedTotalPages) {
            console.warn(`⚠️ [ExamManagement] total_pages 불일치: 받은 값=${receivedTotalPages}, 계산한 값=${calculatedTotalPages}, total_count=${this.totalCount}, page_size=${this.pageSize}`)
            // 계산한 값을 사용 (더 정확함)
            this.totalPages = calculatedTotalPages
          } else {
            this.totalPages = receivedTotalPages
          }
          
          // totalCount가 0이면 totalPages도 0이어야 함
          if (this.totalCount === 0 && this.totalPages > 0) {
            console.warn(`⚠️ [ExamManagement] total_count=0인데 total_pages=${this.totalPages} > 0, 0으로 수정`)
            this.totalPages = 0
          }
          if (!isProduction) {
            debugLog('📊 페이지네이션 정보:', {
              currentPage: this.currentPage,
              totalCount: this.totalCount,
              totalPages: this.totalPages
            })
          }
        } else {
          // 페이지네이션 정보가 없는 경우 (하위 호환성)
          this.currentPage = 1
          this.totalCount = 0
          this.totalPages = 0
          console.warn(`⚠️ [ExamManagement] 페이지네이션 정보가 없습니다.`)
        }
        
        // 최적화된 API 응답 구조 처리
        if (response.data.results) {
          this.exams = response.data.results  // ✅ results 배열만 할당
          
          // 페이지네이션 정보가 없었던 경우 results 길이로 설정
          if (!response.data.pagination) {
            this.totalCount = this.exams.length
            this.totalPages = Math.ceil(this.exams.length / this.pageSize) || 1
          }
          if (!isProduction) {
            // ai_mock_interview 필드 확인을 위한 디버깅
            const nwTrafficExam = response.data.results.find(exam => 
              (getLocalizedContentWithI18n(exam, 'title', this.$i18n, this.userProfileLanguage, '') || '').includes('N/W traffic DevOps')
            )
            if (nwTrafficExam) {
              debugLog('🔍 N/W traffic DevOps 시험 데이터:', {
                id: nwTrafficExam.id,
                title_ko: nwTrafficExam.title_ko,
                title_en: nwTrafficExam.title_en,
                ai_mock_interview: nwTrafficExam.ai_mock_interview,
                ai_mock_interview_type: typeof nwTrafficExam.ai_mock_interview,
                all_fields: Object.keys(nwTrafficExam)
              })
            }
            debugLog('🔍 시험 목록 로드됨 (구독 정보 포함):', response.data.results.map(exam => ({
              id: exam.id,
              title: this.getLocalizedTitle(exam),
              is_subscribed: exam.is_subscribed,
              ai_mock_interview: exam.ai_mock_interview,
              versions: exam.versions ? exam.versions.map(v => ({ id: v.id, ai_mock_interview: v.ai_mock_interview })) : []
            })))
            
            // 디버깅: 각 시험의 display_title 확인 (상세)
            const userProfileLanguageForDebug = await this.getUserProfileLanguage()
            response.data.results.forEach(exam => {
              debugLog(`🔍 [ExamManagement] 시험 ID ${exam.id} - 전체 exam 객체:`, JSON.stringify(exam, null, 2))
              debugLog(`🔍 [ExamManagement] 시험 ID ${exam.id} - display_title: "${exam.display_title}" (type: ${typeof exam.display_title}), title_zh: "${exam.title_zh}" (type: ${typeof exam.title_zh}), title_en: "${exam.title_en}" (type: ${typeof exam.title_en}), userProfileLanguage: ${userProfileLanguageForDebug}`)
              // getLocalizedTitle 호출하여 실제 반환값 확인
              const computedTitle = this.getLocalizedTitle(exam)
              debugLog(`🔍 [ExamManagement] 시험 ID ${exam.id} - getLocalizedTitle() 반환값: "${computedTitle}"`)
            })
          }
        } else {
          // 기존 응답 구조 지원 (하위 호환성)
          this.exams = Array.isArray(response.data) ? response.data : []  // ✅ 배열 확인 후 할당
          
          // 페이지네이션 정보가 없었던 경우 results 길이로 설정
          if (!response.data.pagination) {
            this.totalCount = this.exams.length
            this.totalPages = Math.ceil(this.exams.length / this.pageSize) || 0
          }
          
          if (!isProduction) {
            debugLog('🔍 시험 목록 로드됨 (기존 구조):', this.exams.map(exam => ({
              id: exam.id,
              title: this.getLocalizedTitle(exam),
              is_subscribed: exam.is_subscribed
            })))
            debugLog('📊 페이지네이션 정보 (기존 구조):', {
              currentPage: this.currentPage,
              totalCount: this.totalCount,
              totalPages: this.totalPages,
              examsLength: this.exams.length
            })
          }
        }

        // My Exam이 없고 현재 필터가 'my'인 경우 자동으로 Public Exams로 전환
        const examCount = response.data.results ? response.data.results.length : (Array.isArray(response.data) ? response.data.length : 0)
        // 인증 상태와 관계없이 my_exams가 0개면 자동으로 public으로 전환
        if (this.examTypeFilter === 'my' && examCount === 0 && !this.isAutoSwitchingToPublic) {
          if (!isProduction) {
            debugLog('📝 My Exam이 없어서 자동으로 Public Exams로 전환합니다.')
          }
          this.isAutoSwitchingToPublic = true
          this.examTypeFilter = 'public'
          // 사용자에게 자동 전환 알림 (메시지가 불필요하므로 토스트 표시하지 않음)
          // this.showToastNotification(this.$t('examManagement.messages.autoSwitchToPublic'), 'info', 'fas fa-info-circle')
          // Public Exams 다시 로드
          await this.loadExams()
          this.isAutoSwitchingToPublic = false
          return
        }
        
        // LeetCode Dev 시험 확인
        const examList = response.data.results || response.data
        const leetcodeExam = examList.find(exam => 
          (exam.title_ko && exam.title_ko === 'LeetCode Dev') || 
          (exam.title_en && exam.title_en === 'LeetCode Dev')
        )
        if (!isProduction) {
          if (leetcodeExam) {
            debugLog('✅ LeetCode Dev 시험 발견:', leetcodeExam)
          } else {
            debugLog('❌ LeetCode Dev 시험을 찾을 수 없습니다')
            debugLog('🔍 모든 시험 제목:', examList.map(exam => this.getLocalizedTitle(exam)))
          }
        }
      } catch (error) {
        debugLog('시험 목록 로드 실패:', error, 'error')
        console.error('🔍 [ExamManagement] 에러 상세:', {
          status: error.response?.status,
          statusText: error.response?.statusText,
          data: error.response?.data,
          url: error.config?.url,
          isAuthenticated: this.isAuthenticated,
          examTypeFilter: this.examTypeFilter,
          currentPage: this.currentPage,
          pageSize: this.pageSize,
          selectedTagFilters: this.selectedTagFilters
        })
        
        // my_exams 요청이 실패한 경우 (인증 오류 등) 자동으로 public으로 전환 시도
        if (this.examTypeFilter === 'my' && !this.isAutoSwitchingToPublic) {
          const url = error.config?.url || ''
          if (url.includes('my_exams=true')) {
            if (!isProduction) {
              debugLog('📝 my_exams 요청 실패 - 자동으로 Public Exams로 전환합니다.')
            }
            this.isAutoSwitchingToPublic = true
            this.examTypeFilter = 'public'
            // Public Exams 다시 로드
            try {
              await this.loadExams()
            } catch (retryError) {
              debugLog('Public Exams 로드도 실패:', retryError, 'error')
              this.exams = []
              this.totalCount = 0
              this.totalPages = 0
            }
            this.isAutoSwitchingToPublic = false
            return
          }
        }
        
        // 로그인하지 않은 사용자가 공개 시험을 조회할 때 401 에러가 발생할 수 있음
        // 하지만 공개 API는 401을 반환해도 에러를 무시하고 빈 배열로 설정하지 말고
        // 실제로는 공개 시험이 있을 수 있으므로 재시도해야 함
        if (!this.isAuthenticated && this.examTypeFilter === 'public' && error.response?.status === 401) {
          console.log('⚠️ 공개 시험 조회 시 401 에러 발생 - 재시도하지 않고 빈 결과 표시')
          // 공개 시험이 있을 수 있지만 백엔드에서 인증을 요구하는 경우
          // 빈 배열을 표시하는 대신 사용자에게 로그인이 필요할 수 있음을 표시할 수 있음
          this.exams = []
          this.totalCount = 0
          this.totalPages = 0
          this.cacheData()
        } else {
          // 기타 에러의 경우 빈 배열로 설정
          this.exams = []
          this.totalCount = 0
          this.totalPages = 0
        }
      } finally {
        // 로딩 상태 종료
        this.loading = false
      }
    },
    async loadExamResults() {
      try {
        // 점수 계산에 필요한 최소한의 데이터만 로드 (최적화된 API 사용)
        const response = await axios.get('/api/exam-results/summary/?page_size=100')
        if (response.data.results) {
          // 새로운 페이지네이션 응답 형식
          this.examResults = response.data.results.filter(result =>
            result && result.exam && result.exam.id
          )
        } else {
          // 기존 응답 형식 (하위 호환성)
          this.examResults = (response.data || []).filter(result =>
            result && result.exam && result.exam.id
          )
        }
      } catch (error) {
        debugLog('시험 결과 로드 실패:', error, 'error')
        this.examResults = []
      }
    },

    // 전체 시험 결과 정보가 필요한 경우 사용 (상세 정보 포함)
    async loadFullExamResults() {
      try {
        const response = await axios.get('/api/exam-results/?page_size=100')
        if (response.data.results) {
          this.examResults = response.data.results.filter(result =>
            result && result.exam && result.exam.id
          )
        } else {
          this.examResults = (response.data || []).filter(result =>
            result && result.exam && result.exam.id
          )
        }
      } catch (error) {
        debugLog('전체 시험 결과 로드 실패:', error, 'error')
        this.examResults = []
      }
    },
    async loadQuestionFiles() {
      try {
        debugLog('문제 파일 목록 로드 시작...')
        // 익명 사용자도 문제 파일 목록을 볼 수 있음 (공개 파일만)
        const response = await axios.get('/api/question-files/')
        debugLog('문제 파일 목록 응답:', response.data)
        
        // API 응답에서 files 배열을 가져오거나 전체 응답을 사용
        const files = response.data.files || response.data
        
        // 각 파일에 question_count 필드가 있는지 확인하고 없으면 추가
        this.questionFiles = files.map(file => {
          if (!Object.prototype.hasOwnProperty.call(file, 'question_count')) {
            // API에서 받은 question_count가 없으면 기본값 설정
            file.question_count = 0
            debugLog('⚠️ 파일에 question_count가 없음:', file.name, '기본값 0으로 설정')
          }
          return file
        })
        
        debugLog('questionFiles 설정됨:', this.questionFiles.length, '개 파일')
        debugLog('📁 로드된 파일들:', this.questionFiles.map(f => ({ name: f.name, question_count: f.question_count })))
      } catch (error) {
        debugLog('문제 파일 목록 로드 실패:', error, 'error')
        this.questionFiles = []
      }
    },
    async loadStudyTasks() {
      try {
        const response = await axios.get('/api/study-tasks/')
        // API 응답이 페이지네이션 형식인지 확인하고 results 배열 추출
        if (response.data && response.data.results) {
          // 페이지네이션 응답 형식 (results 배열 포함)
          this.studyTasks = Array.isArray(response.data.results) ? response.data.results : []
        } else if (Array.isArray(response.data)) {
          // 직접 배열 응답 형식
          this.studyTasks = response.data
        } else {
          // 기타 형식
          this.studyTasks = []
        }
        debugLog('StudyTasks 로드됨:', this.studyTasks.length, '개')
      } catch (error) {
        debugLog('StudyTask 목록 로드 실패:', error, 'error')
        // 에러 발생 시 빈 배열로 설정
        this.studyTasks = []
      }
    },
    // 캐싱 관련 메서드들
    getCachedData() {
      try {
        const cached = sessionStorage.getItem('examManagementCache')
        if (cached) {
          const data = JSON.parse(cached)
          // 캐시 유효성 확인 (5분)
          if (data.timestamp && (Date.now() - data.timestamp) < 5 * 60 * 1000) {
            // examTypeFilter 복원
            if (data.examTypeFilter) {
              // 로그인하지 않은 사용자는 항상 "public" 필터 사용
              if (!this.isAuthenticated) {
                this.examTypeFilter = 'public'
              } else {
                this.examTypeFilter = data.examTypeFilter
              }
            }
            return data
          }
        }
      } catch (error) {
        debugLog('캐시 데이터 파싱 실패:', error, 'error')
      }
      return null
    },
    cacheData() {
      try {
        // 캐시 저장 전에 오래된 캐시 정리
        this.cleanupOldCache()
        
        // 극도로 최소화된 데이터만 캐시 (용량 절약)
        const cacheData = {
          exams: this.exams.slice(0, 10).map(exam => ({
            id: exam.id,
            title: this.getLocalizedTitle(exam),
            display_title: this.getLocalizedTitle(exam),
            total_questions: exam.total_questions,
            user_correct_questions: exam.user_correct_questions,
            created_at: exam.created_at,
            is_public: exam.is_public,
            is_original: exam.is_original,
            isChild: exam.isChild,
            children: exam.children || []
          })),
          examResults: this.examResults.slice(0, 5).map(result => ({
            id: result.id,
            exam: result.exam?.id,
            score: result.score,
            completed_at: result.completed_at
          })),
          questionFiles: this.questionFiles.slice(0, 5).map(file => ({
            name: file.name,
            size: file.size
          })),
          studyTasks: this.studyTasks.slice(0, 5).map(task => ({
            id: task.id,
            name: task.name,
            study: task.study?.id
          })),
          examTypeFilter: this.examTypeFilter,
          timestamp: Date.now()
        }
        
        const cacheString = JSON.stringify(cacheData)
        
        // 캐시 크기 확인 (200KB 제한으로 조정)
        if (cacheString.length > 200 * 1024) {
          debugLog('캐시 데이터가 너무 큽니다. 캐시를 저장하지 않습니다.', null, 'warn')
          return
        }
        
        // Profile.vue의 캐시 설정에 따라 캐시 저장
        if (setSessionCache('examManagementCache', cacheData)) {
          debugLog('캐시 데이터 저장됨 (크기:', Math.round(cacheString.length / 1024), 'KB)')
        } else {
          debugLog('캐시가 비활성화되어 데이터를 저장하지 않습니다.')
        }
      } catch (error) {
        debugLog('캐시 데이터 저장 실패:', error, 'error')
        
        // 긴급 캐시 정리 시도
        if (this.emergencyCacheCleanup()) {
          try {
            // 다시 한 번 저장 시도
            const minimalCache = {
              exams: this.exams.slice(0, 5).map(exam => ({
                id: exam.id,
                title: this.getLocalizedTitle(exam),
                display_title: this.getLocalizedTitle(exam),
                total_questions: exam.total_questions,
                user_correct_questions: exam.user_correct_questions,
                created_at: exam.created_at,
                is_public: exam.is_public,
                is_original: exam.is_original,
                isChild: exam.isChild,
                children: exam.children || []
              })),
              timestamp: Date.now()
            }
            // Profile.vue의 캐시 설정에 따라 최소 캐시 저장
            if (setSessionCache('examManagementCache', minimalCache)) {
              debugLog('최소 캐시 저장 성공')
            } else {
              debugLog('캐시가 비활성화되어 최소 캐시도 저장하지 않습니다.')
            }
          } catch (retryError) {
            debugLog('최소 캐시 저장도 실패:', retryError, 'error')
            // Profile.vue의 캐시 설정과 별개로 긴급 캐시 비활성화
            sessionStorage.setItem('emergencyCacheDisabled', 'true')
            debugLog('긴급 상황으로 인해 캐시가 비활성화되었습니다.')
          }
        } else {
          this.clearCache()
        }
      }
    },
    shouldRefreshCache() {
      // Profile.vue의 캐시 설정 확인
      if (!isCacheEnabled()) {
        debugLog('캐시가 비활성화되어 항상 새로고침이 필요합니다.')
        return true
      }
      
      // 강제 새로고침 플래그 확인
      return getSessionCache('forceRefreshExamManagement', false)
    },
    clearCache() {
      // Profile.vue의 캐시 설정에 따라 캐시 정리
      if (isCacheEnabled()) {
        // 시험 관리 관련 캐시 정리
        removeSessionCache('examManagementCache')
        removeSessionCache('forceRefreshExamManagement')
        
        // localStorage에서 examManagement 관련 캐시도 삭제
        const keys = Object.keys(localStorage)
        keys.forEach(key => {
          if (key.startsWith('examManagement_')) {
            removeLocalCache(key)
          }
        })
        
        // 추가로 시험 관련 모든 캐시 정리
        this.clearAllExamCache()
        
        debugLog('시험 관리 캐시 클리어 완료')
      } else {
        debugLog('캐시가 비활성화되어 정리 작업을 건너뜁니다.')
      }
    },
    
    clearAllExamCache() {
      try {
        // Profile.vue의 캐시 설정에 따라 시험 관련 캐시 정리
        if (isCacheEnabled()) {
          // 시험 관련 모든 캐시 정리
          const sessionKeys = Object.keys(sessionStorage)
          let deletedCount = 0
          
          sessionKeys.forEach(key => {
            if (key.includes('exam') || key.includes('Exam') || key.includes('Management')) {
              removeSessionCache(key)
              deletedCount++
            }
          })
          
          // localStorage에서도 시험 관련 캐시 정리
          const localKeys = Object.keys(localStorage)
          localKeys.forEach(key => {
            if (key.includes('exam') || key.includes('Exam') || key.includes('Management')) {
              removeLocalCache(key)
              deletedCount++
            }
          })
          
          debugLog(`시험 관련 모든 캐시 정리 완료: ${deletedCount}개 항목 삭제`)
        } else {
          debugLog('캐시가 비활성화되어 시험 관련 캐시 정리를 건너뜁니다.')
        }
      } catch (error) {
        debugLog('시험 관련 모든 캐시 정리 중 오류:', error, 'error')
      }
    },
    
    cleanupOldCache() {
      try {
        // 모든 캐시 키 확인
        const keys = Object.keys(sessionStorage)
        const now = Date.now()
        const maxAge = 10 * 60 * 1000 // 10분
        
        keys.forEach(key => {
          if (key.includes('Cache') || key.includes('Data')) {
            try {
              const cached = sessionStorage.getItem(key)
              if (cached) {
                const data = JSON.parse(cached)
                if (data.timestamp && (now - data.timestamp > maxAge)) {
                  sessionStorage.removeItem(key)
                  debugLog('오래된 캐시 삭제:', key)
                }
              }
            } catch (e) {
              // 파싱 실패 시 삭제
              sessionStorage.removeItem(key)
              debugLog('손상된 캐시 삭제:', key)
            }
          }
        })
      } catch (error) {
        debugLog('캐시 정리 중 오류:', error, 'error')
      }
    },
    
    // 긴급 캐시 정리 (용량 한계 해결용)
    emergencyCacheCleanup() {
      try {
        debugLog('긴급 캐시 정리 시작')
        const keys = Object.keys(sessionStorage)
        let deletedCount = 0
        
        keys.forEach(key => {
          if (key.includes('Cache') || key.includes('Data') || key.includes('Management')) {
            sessionStorage.removeItem(key)
            deletedCount++
            debugLog('긴급 캐시 삭제:', key)
          }
        })
        
        debugLog(`긴급 캐시 정리 완료: ${deletedCount}개 삭제`)
        return deletedCount > 0
      } catch (error) {
        debugLog('긴급 캐시 정리 중 오류:', error, 'error')
        return false
      }
    },
    
    clearBrowserCache() {
      try {
        debugLog('브라우저 캐시 강제 정리 시작')
        
        // 모든 관련 캐시 키 삭제
        const sessionKeys = Object.keys(sessionStorage)
        const localKeys = Object.keys(localStorage)
        let deletedCount = 0
        
        // sessionStorage 정리
        sessionKeys.forEach(key => {
          if (key.includes('exam') || key.includes('Exam') || key.includes('Management')) {
            sessionStorage.removeItem(key)
            deletedCount++
          }
        })
        
        // localStorage 정리
        localKeys.forEach(key => {
          if (key.includes('exam') || key.includes('Exam') || key.includes('Management')) {
            localStorage.removeItem(key)
            deletedCount++
          }
        })
        
        // 강제 새로고침 플래그 설정
        sessionStorage.setItem('forceRefreshExamManagement', 'true')
        
        debugLog(`브라우저 캐시 정리 완료: ${deletedCount}개 삭제`)
        return deletedCount > 0
      } catch (error) {
        debugLog('브라우저 캐시 정리 중 오류:', error, 'error')
        return false
      }
    },
    toggleCreateForm() {
      this.showCreateForm = !this.showCreateForm
      if (!this.showCreateForm) {
        this.resetForm()
      } else {
        // 폼이 열릴 때 도메인별 기본 태그 자동 추가
        this.setupDefaultTagsForNewExam()
      }
    },
    setupDefaultTagsForNewExam() {
      // 도메인별 기본 태그 설정
      const domainConfig = getCurrentDomainConfig()
      if (domainConfig) {
        const forcedTags = getForcedTags(domainConfig, this.availableTags)
        if (forcedTags.length > 0) {
          this.newExamTags = [...forcedTags]
          console.log(`🏷️ ${domainConfig.tagName} 도메인 - 새 시험 생성 시 기본 태그 자동 추가:`, this.newExamTags)
        }
      }
    },
    resetForm() {
      this.newExam = {
        title: '',
        description: '',
        question_count: 0,
        file_name: '',
        wrong_questions_only: false,
        random_option: 'random',
        is_original: true,
        is_public: true,
        force_answer: false,
        voice_mode_enabled: false,
        ai_mock_interview: false
      }
      this.newExamTags = [] // 태그 초기화
      this.titleError = '' // 에러 메시지 초기화
    },
    cancelCreate() {
      this.showCreateForm = false
      this.resetForm()
    },
    onFileChange() {
      debugLog('📁 파일 변경됨:', this.newExam.file_name)
      debugLog('📁 전체 questionFiles:', this.questionFiles)
      
      if (this.newExam.file_name) {
        const selectedFile = this.questionFiles.find(file => file.name === this.newExam.file_name)
        debugLog('📊 선택된 파일 (전체):', selectedFile)
        debugLog('📊 선택된 파일 (JSON):', JSON.stringify(selectedFile, null, 2))
        debugLog('📊 선택된 파일 (Object.keys):', selectedFile ? Object.keys(selectedFile) : 'null')
        
        // question_count가 없을 경우 다른 방법으로 찾기
        let selectedFileMaxQuestions = 0
        if (selectedFile) {
          selectedFileMaxQuestions = selectedFile.question_count || selectedFile.questionCount || 0
          debugLog('📊 파일의 최대 문제 수 (직접 접근):', selectedFile.question_count)
          debugLog('📊 파일의 최대 문제 수 (대체):', selectedFile.questionCount)
          debugLog('📊 파일의 최대 문제 수 (최종):', selectedFileMaxQuestions)
        }
        
        debugLog('📊 현재 문제 수:', this.newExam.question_count)
        
        // question_count가 있는 경우에만 자동 업데이트 및 체크
        if (selectedFileMaxQuestions > 0) {
          // 비동기 처리 문제 해결을 위해 setTimeout 사용
          setTimeout(() => {
            // Vue.set을 사용하여 강제로 반응성 업데이트
            this.$set(this.newExam, 'question_count', selectedFileMaxQuestions)
            debugLog('✅ 문제 수 업데이트됨 (Vue.set):', this.newExam.question_count)
            
            // 추가로 강제 업데이트
            this.$forceUpdate()
            
            // Vue 반응성 보장을 위해 $nextTick 사용
            this.$nextTick(() => {
              debugLog('🔄 DOM 업데이트 후 문제 수:', this.newExam.question_count)
            })
          }, 200) // 200ms 지연
        } else {
          debugLog('📊 파일에 question_count 정보가 없어 자동 업데이트를 건너뜁니다.')
        }
      } else {
        // 파일을 선택하지 않은 경우 기본값으로 복원
        this.newExam.question_count = 0
        debugLog('🔄 기본값으로 복원됨:', this.newExam.question_count)
      }
    },
    
    // 제목 중복 체크 (API 호출)
    async checkTitleDuplicate() {
      if (!this.newExam.title || !this.newExam.title.trim()) {
        // 번역이 로드되지 않았을 수 있으므로 안전하게 처리
        const translation = this.$t('examManagement.messages.titleRequired')
        this.titleError = translation && translation !== 'examManagement.messages.titleRequired' 
          ? translation 
          : 'Please enter an exam title'
        return false
      }
      
      try {
        // 공통 함수 사용하여 API로 중복 체크
        const isDuplicate = await checkTitleDuplicate(this.newExam.title.trim(), true)
        
        if (isDuplicate) {
          // 번역이 로드되지 않았을 수 있으므로 안전하게 처리
          const translation = this.$t('examManagement.messages.duplicateTitle')
          // 번역 키가 그대로 반환되면 번역이 없는 것이므로 현재 언어에 맞는 fallback 사용
          if (translation === 'examManagement.messages.duplicateTitle' || !translation) {
            // 현재 언어에 맞는 fallback 메시지
            const currentLang = this.$i18n.locale || 'en'
            const fallbackMessages = {
              'ko': '이미 같은 이름의 시험이 존재합니다',
              'en': 'An exam with this title already exists',
              'es': 'Ya existe un examen con este título',
              'zh': '已存在相同标题的考试',
              'ja': 'このタイトルの試験が既に存在します'
            }
            this.titleError = fallbackMessages[currentLang] || fallbackMessages['en']
          } else {
            this.titleError = translation
          }
          return false
        }
        
        this.titleError = ''
        return true
      } catch (error) {
        debugLog('시험 제목 중복 체크 오류:', error, 'error')
        // 오류 발생 시 중복이 아니라고 가정하고 통과
        this.titleError = ''
        return true
      }
    },
    
    // 제목 입력 시 실시간 검증
    handleTitleInput() {
      // 기존 타이머가 있으면 취소
      if (this.titleValidationTimer) {
        clearTimeout(this.titleValidationTimer)
      }
      
      // 입력이 비어있으면 검증 오류 제거
      if (!this.newExam.title || !this.newExam.title.trim()) {
        this.titleError = ''
        return
      }
      
      // debounce: 500ms 후에 검증 실행
      this.titleValidationTimer = setTimeout(() => {
        this.checkTitleDuplicate()
      }, 500)
    },
    
    // 검색 디바운싱 처리
    handleSearchInput(field, value) {
      // 기존 타이머 취소
      if (this.searchDebounceTimer) {
        clearTimeout(this.searchDebounceTimer)
      }
      
      // 300ms 후에 검색 실행
      this.searchDebounceTimer = setTimeout(async () => {
        this.searchFilters[field] = value
        
        // 필터 변경 시 데이터 다시 로드
        if (field === 'isPublic' || field === 'isOriginal' || field === 'title') {
          await this.loadExams()
        }
      }, 300)
    },
    

    

    

    
    async createExam() {
      // 제목 중복 체크
      const isTitleValid = await this.checkTitleDuplicate()
      if (!isTitleValid) {
        return
      }
      
      // 제목이 입력되어야 함
      if (!this.newExam.title.trim()) {
        this.showToastNotification('제목을 입력해주세요.', 'error')
        return
      }
      
      try {
        // 저장 상태 시작
        this.saving = true

        debugLog('📝 시험 생성 시작:', this.newExam)
        // 새 시험 생성 시 creation_type을 'new'로 설정
        // 시험 생성 데이터 준비 (Study Title/Goal과 동일한 다국어 처리 방식)
        // 사용자는 title, description 필드에만 입력
        // 백엔드에서 자동으로 사용자 언어에 맞는 필드에 저장하고 번역 수행
        // 파싱된 문제들이 있으면 question_count를 0으로 설정하고 parsed_problems만 사용
        const examData = {
          title: this.newExam.title,
          description: this.newExam.description,
          question_count: (this.parsedProblems && this.parsedProblems.length > 0) ? 0 : this.newExam.question_count,
          file_name: this.newExam.file_name,
          wrong_questions_only: this.newExam.wrong_questions_only,
          random_option: this.newExam.random_option,
          is_original: this.newExam.is_original,
          is_public: this.newExam.is_public,
          force_answer: this.newExam.force_answer,
          voice_mode_enabled: this.newExam.voice_mode_enabled,
          ai_mock_interview: this.newExam.ai_mock_interview,
          tags: this.newExamTags, // 태그 추가
          creation_type: 'new'
        }
        
        // 파싱된 문제들이 있으면 추가
        if (this.parsedProblems && this.parsedProblems.length > 0) {
          examData.parsed_problems = this.parsedProblems
          debugLog('📝 파싱된 문제들 추가:', this.parsedProblems)
          debugLog('📝 question_count를 0으로 설정하여 추가 문제 생성 방지')
        }
        
        const response = await axios.post('/api/create-exam/', examData)
        debugLog('✅ 시험 생성 성공:', response.data)
        
        // 파싱된 문제들이 있으면 시험에 추가
        if (this.parsedProblems && this.parsedProblems.length > 0) {
          await this.addParsedProblemsToExam(response.data.id)
        }
        
        // 백엔드에서 이미 자동 구독이 생성되었으므로 추가 API 호출 불필요
        debugLog('🔔 백엔드에서 자동 구독 완료됨 (추가 API 호출 불필요)')
        
        // 사용자에게 자동 구독 알림
        this.showToastNotification(
          this.$t('examManagement.messages.autoSubscribed'), 
          'success', 
          'fas fa-bell'
        )
        
        this.resetForm()
        this.showCreateForm = false
        
        // 캐시 무효화 후 데이터 다시 로드
        debugLog('🔄 캐시 무효화 및 데이터 다시 로드')
        this.clearCache()
        await this.loadExams()
        this.cacheData()
        
        debugLog('📊 로드된 시험 수:', this.exams.length)
        debugLog('📊 시험 목록:', this.exams.map(e => ({ id: e.id, title: e.title, created_by: e.created_by })))
        
        this.showToastNotification(this.$t('examManagement.messages.createSuccess'), 'success')
      } catch (error) {
        debugLog('❌ 시험 생성 실패:', error, 'error')
        debugLog('시험 생성 실패:', error, 'error')
        this.showToastNotification(this.$t('examManagement.messages.createFailed'), 'error')
      } finally {
        // 저장 상태 종료
        this.saving = false
      }
    },
    async createRandomRecommendationExams() {
      try {
        // 로딩 상태 시작
        this.loading = true
        
        // ExamDetail에서도 사용할 수 있도록 성공 콜백을 전달
        await createDailyExam(this, async (examData) => {
          debugLog('🔄 Daily Exam 생성 성공, 캐시 무효화 시작')
          
          // 강력한 캐시 무효화
          this.clearCache()
          this.emergencyCacheCleanup()
          this.clearBrowserCache()
          
          // 강제 새로고침 플래그 설정
          sessionStorage.setItem('forceRefreshExamManagement', 'true')
          sessionStorage.setItem('forceRefreshHome', 'true')
          sessionStorage.setItem('forceRefreshProfile', 'true')
          
          // 캐시 무효화 후 시험 목록 새로고침
          debugLog('🔄 시험 목록 새로고침 시작')
          await this.loadExams()
          
          debugLog('📊 새로고침된 시험 수:', this.exams.length)
          debugLog('📊 새로고침된 시험 목록:', this.exams.map(e => ({ id: e.id, title: e.title, created_by: e.created_by })))
          
          // 생성된 시험이 목록에 있는지 확인
          const createdExam = this.exams.find(e => e.id === examData.id)
          if (createdExam) {
            debugLog('✅ 생성된 시험이 목록에 정상적으로 표시됨')
          } else {
            debugLog('⚠️ 생성된 시험이 목록에 표시되지 않음, 강제 새로고침 필요')
            // 강제 새로고침
            window.location.reload()
            return
          }

          // 생성된 시험으로 바로 이동
          this.$router.push(`/take-exam/${examData.id}`)
        })
      } catch (error) {
        debugLog('❌ 랜덤 시험 생성 실패:', error, 'error')
        this.showToastNotification(this.$t('examManagement.messages.createFailed'), 'error')
      } finally {
        // 로딩 상태 종료
        this.loading = false
      }
    },
    async deleteExam(examId) {
      this.showConfirmModal(
        this.$t('examManagement.messages.deleteConfirm'),
        this.$t('examManagement.messages.deleteConfirm'),
        'Delete',
        this.$t('common.cancel'),
        'btn-danger',
        'fas fa-trash',
        () => this.executeDeleteExam(examId)
      )
    },
    
    async executeDeleteExam(examId) {
      try {
        // 로딩 상태 시작
        this.loading = true
        
        await axios.delete(`/api/exam/${examId}/delete/`)
        
        // 강력한 캐시 무효화
        this.clearCache()
        this.emergencyCacheCleanup()
        
        // 브라우저 캐시도 강제 정리
        this.clearBrowserCache()
        
        // 삭제된 시험과 관련된 결과 데이터도 정리
        this.examResults = this.examResults.filter(result =>
          result && result.exam && result.exam.id !== examId
        )
        
        // 강제 새로고침 플래그 설정
        sessionStorage.setItem('forceRefreshExamManagement', 'true')
        
        // 삭제 후 시험 목록 새로고침 (캐시 무시)
        await this.loadExams()
        
        // 선택된 시험 목록에서도 제거
        this.selectedExams = this.selectedExams.filter(id => id !== String(examId));
        
        this.showToastNotification(this.$t('examManagement.messages.deleteSuccess'), 'success')
      } catch (error) {
        debugLog('시험 삭제 실패:', error, 'error')
        this.showToastNotification(this.$t('examManagement.messages.deleteFailed'), 'error')
      } finally {
        // 로딩 상태 종료
        this.loading = false
      }
    },
    async viewExamDetails(exam) {
      // 모든 사용자(인증 여부와 관계없이) 상세 페이지로 이동
      this.$router.push(`/exam-detail/${exam.id}`)
    },
    closeModal() {
      this.selectedExam = null
      this.questionStatistics = {}
    },

    // 문제 통계 로드
    async loadQuestionStatistics(examId) {
      try {
        const response = await axios.get(`/api/exam/${examId}/question-statistics/`)
        this.questionStatistics = {}
        response.data.forEach(stat => {
          this.questionStatistics[stat.question_id] = {
            total_attempts: stat.total_attempts,
            correct_attempts: stat.correct_attempts
          }
        })
        console.log('문제 통계 로드 완료:', this.questionStatistics)
      } catch (error) {
        console.error('문제 통계 로드 실패:', error)
        this.questionStatistics = {}
      }
    },

    // 문제 통계 가져오기
    getQuestionStats(questionId) {
      return this.questionStatistics[questionId] || {
        total_attempts: 0,
        correct_attempts: 0
      }
    },

    getAverageScore(examId) {
      const results = this.examResults.filter(result => result.exam && result.exam.id === examId)
      if (results.length === 0) return 'N/A'
      const totalScore = results.reduce((sum, result) => sum + (result.score || 0), 0)
      const average = totalScore / results.length
      return isNaN(average) ? 'N/A' : average.toFixed(1)
    },
    formatDate(dateString) {
      return formatLocalDate(dateString)
    },
    scrollToTop() {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    },
    // 일괄 선택/해제 로직
    toggleSelectAll(event) {
      if (event.target.checked) {
        this.selectedExams = this.filteredExamTree.map(exam => String(exam.id))
      } else {
        this.selectedExams = []
      }
    },
    // 정렬 로직
    sortBy(key) {
      if (this.sortKey === key) {
        this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc'
      } else {
        this.sortKey = key
        this.sortOrder = 'asc'
      }
    },
    // 트리 정렬 로직
    sortTreeBy(key) {
      if (this.treeSortKey === key) {
        this.treeSortOrder = this.treeSortOrder === 'asc' ? 'desc' : 'asc'
      } else {
        this.treeSortKey = key
        this.treeSortOrder = 'asc'
      }
      
      // 강제로 computed 속성 재계산
      this.$forceUpdate()
    },
    getTreeSortIcon(key) {
      if (this.treeSortKey !== key) {
        return 'fas fa-sort text-muted'
      }
      return this.treeSortOrder === 'asc' ? 'fas fa-sort-up' : 'fas fa-sort-down'
    },
    // 일괄 삭제 로직
    async deleteSelected() {
      this.showConfirmModal(
        this.$t('examManagement.messages.bulkDeleteConfirm', { count: this.selectedExams.length }),
        this.$t('examManagement.messages.bulkDeleteConfirm', { count: this.selectedExams.length }),
        'Delete',
        this.$t('common.cancel'),
        'btn-danger',
        'fas fa-trash',
        () => this.executeBulkDelete()
      )
    },
    
    async executeBulkDelete() {
      try {
        // 로딩 상태 시작
        this.loading = true
        
        for (const examId of this.selectedExams) {
          await axios.delete(`/api/exam/${examId}/delete/`)
        }
        
        // 캐시 무효화
        this.clearCache()
        
        // 삭제 후 시험 목록 새로고침
        await this.loadExams();
        
        // 캐시 업데이트
        this.cacheData()
        
        this.selectedExams = [] // 선택 해제
        this.showToastNotification(this.$t('examManagement.messages.bulkDeleteSuccess'), 'success')
      } catch (error) {
        debugLog('일괄 삭제 실패:', error, 'error')
        this.showToastNotification(this.$t('examManagement.messages.bulkDeleteFailed'), 'error')
      } finally {
        // 로딩 상태 종료
        this.loading = false
      }
    },

    // 재시험 생성
    async retakeExam(examId) {
      this.showConfirmModal(
        this.$t('examManagement.messages.retakeConfirm'),
        this.$t('examManagement.messages.retakeConfirm'),
        'Create',
        this.$t('common.cancel'),
        'btn-success',
        'fas fa-copy',
        () => this.executeRetakeExam(examId)
      )
    },
    
    async executeRetakeExam(examId) {
      try {
        // 로딩 상태 시작
        this.loading = true
        
        const response = await axios.post(`/api/exam/${examId}/retake/`)
        debugLog('재시험 생성 성공:', response.data)
        await this.loadExams() // 시험 목록 새로고침
        this.showToastNotification(this.$t('examManagement.messages.retakeSuccess'), 'success')
      } catch (error) {
        debugLog('재시험 생성 실패:', error, 'error')
        this.showToastNotification(this.$t('examManagement.messages.retakeFailed'), 'error')
      } finally {
        // 로딩 상태 종료
        this.loading = false
      }
    },
    // 시험이 현재 사용자를 위해 생성되었는지 확인 (내 시험 - 공개 여부와 상관없이 사용자와 연관된 시험)
    isExamForCurrentUser(exam) {
      if (!this.currentUser) return false
      
      if (!isProduction) {
        debugLog('🔍 isExamForCurrentUser 디버깅:', {
          examTitle: this.getLocalizedTitle(exam),
          examCreatedBy: exam.created_by,
          currentUser: this.currentUser.username,
          hasCreatedBy: !!exam.created_by,
          createdByUsername: exam.created_by?.username,
          usernameMatch: exam.created_by?.username === this.currentUser.username,
          titleMatch: (exam.title_ko && exam.title_ko.includes(this.currentUser.username)) || (exam.title_en && exam.title_en.includes(this.currentUser.username))
        })
      }
      
      // 백엔드에서 이미 다음 조건으로 시험을 필터링하여 반환 (내 시험 - 공개 여부와 상관없이):
      // 1. 내가 가입한 스터디에 속한 시험 (공개 여부와 상관없이)
      // 2. 내가 문제를 푼 시험 (공개 여부와 상관없이)
      // 3. 내가 생성한 시험 (공개 여부와 상관없이)
      // 따라서 프론트엔드에서 받은 모든 시험은 "내 시험"으로 간주
      
      // 1. created_by 필드로 확인 (우선순위) - 내가 생성한 시험
      if (exam.created_by && exam.created_by.username === this.currentUser.username) {
        if (!isProduction) {
          debugLog('✅ created_by 필드로 매치됨')
        }
        return true
      }
      
      // 2. 시험 제목에 현재 사용자 이름이 포함되어 있는지 확인 (하위 호환성) - 내 시험
      const username = this.currentUser.username
      const titleMatch = (exam.title_ko && exam.title_ko.includes(username)) || (exam.title_en && exam.title_en.includes(username))
      if (titleMatch) {
        if (!isProduction) {
          debugLog('✅ 제목으로 매치됨')
        }
        return true
      }
      
      // 3. 백엔드에서 이미 스터디 멤버십을 기반으로 필터링되어 반환되었으므로
      // 여기서 받은 모든 시험은 "내 시험"으로 간주 (공개 여부와 상관없이)
      if (!isProduction) {
        debugLog('✅ 백엔드 필터링으로 매치됨 (스터디 멤버십 또는 풀어본 시험)')
      }
      return true
    },
    
    // 사용자가 접근 가능한 시험인지 확인 (내 시험 필터용)
    isExamAccessibleToUser(exam) {
      if (!this.currentUser) return false
      
      // 1. 사용자가 생성한 시험 (제목에 사용자명 포함)
      const username = this.currentUser.username
      if ((exam.title_ko && exam.title_ko.includes(username)) || (exam.title_en && exam.title_en.includes(username))) {
        return true
      }
      
      // 2. 공개된 시험
      if (exam.is_public) {
        return true
      }
      
      // 3. 사용자가 멤버인 스터디의 시험 (백엔드에서 이미 필터링됨)
      // 백엔드에서 이미 사용자가 멤버인 스터디의 시험들을 포함하여 반환하므로
      // 여기서는 추가 필터링이 필요하지 않음
      
      return false
    },
    // 트리 확장/축소 토글
    toggleExam(examId) {
      this.$set(this.expandedExams, examId, !this.expandedExams[examId]);
      // 트리 확장 시 원본만 필터 자동 적용
      if (this.searchFilters.isOriginal !== 'true') {
        this.searchFilters.isOriginal = 'true';
      }
    },
    setMaxQuestions() {
      this.newExam.question_count = this.maxQuestions
    },

    // 버전 존재 여부 확인
    hasVersions(exam) {
      return exam.children && exam.children.length > 0
    },
    // 틀린문제만 재시험 생성
    async retakeWrongQuestions(examId, questionCount) {
      this.showConfirmModal(
        this.$t('examManagement.messages.wrongQuestionsConfirm'),
        this.$t('examManagement.messages.wrongQuestionsConfirm'),
        'Create',
        this.$t('common.cancel'),
        'btn-success',
        'fas fa-exclamation-triangle',
        () => this.executeRetakeWrongQuestions(examId, questionCount)
      )
    },
    
    async executeRetakeWrongQuestions(examId, questionCount) {
      try {
        const response = await axios.post(`/api/exam/${examId}/wrong-questions/`, {
          question_count: questionCount
        })
        debugLog('틀린문제 재시험 생성 성공:', response.data)
        await this.loadExams() // 시험 목록 새로고침
        this.showToastNotification(this.$t('examManagement.messages.wrongQuestionsSuccess'), 'success')
      } catch (error) {
        debugLog('틀린문제 재시험 생성 실패:', error, 'error')
        this.showToastNotification(this.$t('examManagement.messages.wrongQuestionsFailed'), 'error')
      }
    },
    // 틀린문제 여부 확인 (누적 오답 기준으로 변경)
    hasWrongQuestions(exam) {
      // exam이 undefined이거나 id가 없으면 false 반환
      if (!exam || !exam.id) {
        return false
      }

      // 모든 결과에서 오답이 1개 이상 있으면 true
      const allResults = this.examResults.filter(result =>
        result && result.exam && result.exam.id === exam.id
      )
      return allResults.some(result =>
        result.wrong_questions && Array.isArray(result.wrong_questions) && result.wrong_questions.length > 0
      )
    },
    // 시험 시작 (새로 풀기 또는 이어풀기)
    async startExam(exam) {
      try {
        // 해당 시험의 최신 결과 찾기
        const examResults = this.examResults.filter(result => result.exam.id === exam.id)
        
        if (examResults.length === 0) {
                  // 시험 결과가 없으면 새로 풀기
        this.$router.push(`/take-exam/${exam.id}`)
        } else {
          // 시험 결과가 있으면 이어풀기 가능 여부 확인
          const latestResult = examResults.sort((a, b) => 
            new Date(b.completed_at) - new Date(a.completed_at)
          )[0]
          
          // 모든 문제를 풀었는지 확인
          if (latestResult.total_score < exam.total_questions) {
            // 이어풀기 가능
            this.showConfirmModal(
              this.$t('examManagement.messages.continueExam'),
              this.$t('examManagement.messages.continueExam'),
              'Continue',
              this.$t('common.cancel'),
              'btn-primary',
              'fas fa-play',
              () => this.$router.push(`/take-exam/${exam.id}?continue=true&result_id=${latestResult.id}`)
            )
          } else {
            // 모든 문제를 풀었으면 새로 풀기
            this.showConfirmModal(
              this.$t('examManagement.messages.newExam'),
              this.$t('examManagement.messages.newExam'),
              'Start New',
              this.$t('common.cancel'),
              'btn-success',
              'fas fa-plus',
              () => this.$router.push(`/take-exam/${exam.id}`)
            )
          }
        }
      } catch (error) {
        debugLog('시험 시작 실패:', error, 'error')
        this.showToastNotification(this.$t('examManagement.messages.examStartFailed'), 'error')
      }
    },
    // 원본/복제 시험 토글
    async toggleOriginal(examId) {
      this.showConfirmModal(
        this.$t('examManagement.messages.toggleOriginalConfirm'),
        this.$t('examManagement.messages.toggleOriginalConfirm'),
        'Change',
        this.$t('common.cancel'),
        'btn-warning',
        'fas fa-exchange-alt',
        () => this.executeToggleOriginal(examId)
      )
    },
    
    async executeToggleOriginal(examId) {
      try {
        const response = await axios.post(`/api/exam/${examId}/toggle-original/`)
        debugLog('원본/복제 시험 토글 성공:', response.data)
        await this.loadExams() // 시험 목록 새로고침
        this.showToastNotification(this.$t('examManagement.messages.toggleOriginalSuccess'), 'success')
      } catch (error) {
        debugLog('원본/복제 시험 토글 실패:', error, 'error')
        this.showToastNotification(this.$t('examManagement.messages.toggleOriginalFailed'), 'error')
      }
    },
    // 전체 선택 토글
    toggleAllExams(event) {
      if (event.target.checked) {
        if (this.isAdmin) {
          // admin은 모든 시험과 버전 선택 가능
          const allExamIds = [];
          this.filteredExamTree.forEach(exam => {
            allExamIds.push(String(exam.id));
            if (exam.children && exam.children.length > 0) {
              exam.children.forEach(version => {
                allExamIds.push(String(version.id));
              });
            }
          });
          this.selectedExams = JSON.parse(JSON.stringify(allExamIds));
        } else {
          // 일반 사용자는 자신의 시험과 버전만 선택 가능
          const userExamIds = [];
          this.filteredExamTree.forEach(exam => {
            if (this.isExamForCurrentUser(exam)) {
              userExamIds.push(String(exam.id));
            }
            if (exam.children && exam.children.length > 0) {
              exam.children.forEach(version => {
                if (this.isExamForCurrentUser(version)) {
                  userExamIds.push(String(version.id));
                }
              });
            }
          });
          this.selectedExams = JSON.parse(JSON.stringify(userExamIds));
        }
      } else {
        this.selectedExams = [];
      }
    },
    // 전체 선택
    selectAll() {
      this.selectedExams = JSON.parse(JSON.stringify(this.filteredExamTree.map(exam => String(exam.id))));
    },
    // 전체 해제
    deselectAll() {
      this.selectedExams = []
    },
    // 필터 초기화
    clearFilters() {
      this.searchFilters.title = ''
      this.searchFilters.isOriginal = ''
      this.selectedTagFilters = []
    },
    
    // 태그 필터 관련 메서드들
    openTagFilterModal() {
      console.log('🔄 ExamManagement openTagFilterModal 호출됨')
      this.showTagFilterModal = true
    },
    
    handleTagFilterUpdate(selectedTags) {
      console.log('🔄 ExamManagement handleTagFilterUpdate 호출됨')
      // DevOps 도메인인 경우 카테고리 태그 유지
      const filteredTags = this.ensureDevOpsCategoryTags(selectedTags)
      this.selectedTagFilters = filteredTags
    },
    
    handleTagFilterApply(selectedTags) {
      console.log('🔄 ExamManagement handleTagFilterApply 호출됨')
      // DevOps 도메인인 경우 카테고리 태그 유지
      const filteredTags = this.ensureDevOpsCategoryTags(selectedTags)
      this.selectedTagFilters = filteredTags
      this.showTagFilterModal = false
      console.log('📊 적용된 태그 필터:', this.selectedTagFilters)
      
      // 태그 필터 적용 후 시험 목록 다시 로드
      this.loadExams()
    },
    
    ensureDevOpsCategoryTags(selectedTags) {
      // DevOps 도메인인 경우 "IT 기술 > IT 기술" 카테고리의 태그만 유지
      const domainConfig = getCurrentDomainConfig()
      if (domainConfig && domainConfig.keyword === 'devops') {
        const { getDevOpsCategoryId, getDevOpsCategoryTagIds } = require('@/utils/domainUtils')
        const categoryId = getDevOpsCategoryId(this.categoryTree || [])
        if (categoryId && this.availableTags) {
          const allowedTagIds = getDevOpsCategoryTagIds(this.availableTags, categoryId)
          // 선택된 태그 중 허용된 태그만 유지
          return selectedTags.filter(tagId => allowedTagIds.includes(tagId))
        }
      }
      return selectedTags
    },
    
    handleTagFilterError(error) {
      console.error('ExamManagement 태그 필터 에러:', error)
      this.showToastNotification('태그 필터 로드 중 오류가 발생했습니다.', 'error')
    },
    
    // New Exam Tag Management
    openNewExamTagModal() {
      this.showNewExamTagModal = true
    },
    
    handleNewExamTagUpdate(selectedTags) {
      this.newExamTags = selectedTags
    },
    
    handleNewExamTagApply(selectedTags) {
      this.newExamTags = selectedTags
      this.showNewExamTagModal = false
    },
    
    handleTagCreated(tag) {
      // 새로 생성된 태그를 availableTags에 추가
      if (!this.availableTags.find(t => t.id === tag.id)) {
        this.availableTags.push(tag)
        console.log('✅ 새 태그가 availableTags에 추가됨:', tag)
      }
    },
    
    removeNewExamTag(tagId) {
      const index = this.newExamTags.indexOf(tagId)
      if (index > -1) {
        this.newExamTags.splice(index, 1)
      }
    },
    
    getSelectedTagName(tagId) {
      const tag = this.availableTags.find(t => t.id === tagId);
      if (!tag) {
        console.warn(`태그 ID ${tagId}를 찾을 수 없습니다. availableTags:`, this.availableTags);
        return `Loading...`;
      }
      
      // 사용자 프로필 언어 우선, 없으면 i18n locale, 기본값은 'en'
      const userLang = this.userProfileLanguage || this.$i18n?.locale || 'en'
      
      // 모든 지원 언어 필드를 확인하여 사용자 언어에 맞는 값 반환
      const supportedLanguages = ['ko', 'en', 'es', 'zh', 'ja']
      
      // 사용자 언어 우선
      if (tag[`name_${userLang}`]) {
        return tag[`name_${userLang}`]
      }
      
      // 영어 폴백 (기본 언어)
      if (tag.name_en) {
        return tag.name_en
      }
      
      // 다른 지원 언어 확인
      for (const lang of supportedLanguages) {
        if (tag[`name_${lang}`]) {
          return tag[`name_${lang}`]
        }
      }
      
      // localized_name 폴백
      if (tag.localized_name) {
        return tag.localized_name
      }
      
      // 최종 폴백
      return userLang === 'ko' ? '태그 없음' : 'No Tag'
    },
    
    isRequiredTag(tagId) {
      // DevOps 도메인인 경우 "IT 기술 > IT 기술" 카테고리의 모든 태그는 필수
      const domainConfig = getCurrentDomainConfig()
      if (domainConfig && domainConfig.keyword === 'devops') {
        const { getDevOpsCategoryId, getDevOpsCategoryTagIds } = require('@/utils/domainUtils')
        const categoryId = getDevOpsCategoryId(this.categoryTree || [])
        if (categoryId && this.availableTags) {
          const allowedTagIds = getDevOpsCategoryTagIds(this.availableTags, categoryId)
          return allowedTagIds.includes(tagId)
        }
      }
      
      // 기존 로직: 현재 도메인의 필수 태그인지 확인
      if (!domainConfig) {
        return false;
      }
      
      // sessionStorage에서 현재 도메인의 태그 ID 가져오기
      const requiredTagId = this.getRequiredTagIdFromStorage();
      return requiredTagId ? tagId === requiredTagId : false;
    },
    
    getRequiredTagIdFromStorage() {
      try {
        const domainConfig = getCurrentDomainConfig()
        if (!domainConfig) {
          return null;
        }
        
        const stored = sessionStorage.getItem(domainConfig.storageKey);
        return stored ? parseInt(stored, 10) : null;
      } catch (error) {
        console.warn('sessionStorage에서 필수 태그 ID를 읽을 수 없습니다:', error);
        return null;
      }
    },
    
    setRequiredTagIdToStorage(tagId) {
      try {
        const domainConfig = getCurrentDomainConfig()
        if (!domainConfig) {
          return;
        }
        
        sessionStorage.setItem(domainConfig.storageKey, tagId.toString());
      } catch (error) {
        console.warn('sessionStorage에 필수 태그 ID를 저장할 수 없습니다:', error);
      }
    },
    
    
    removeTag(tagId) {
      // 필수 태그는 제거할 수 없음
      if (this.isRequiredTag(tagId)) {
        return;
      }
      
      const index = this.selectedTagFilters.indexOf(tagId);
      if (index > -1) {
        this.selectedTagFilters.splice(index, 1);
        this.loadExams();
      }
    },
    
    async setupInterestedCategoryTags() {
      console.log('🔄 setupInterestedCategoryTags 호출됨')
      console.log('📊 현재 selectedTagFilters:', this.selectedTagFilters, '길이:', this.selectedTagFilters?.length || 0)
      
      // 이미 태그가 선택되어 있으면 관심 카테고리 태그를 적용하지 않음
      if (this.selectedTagFilters && this.selectedTagFilters.length > 0) {
        console.log('⚠️ 이미 태그가 선택되어 있어 관심 카테고리 태그를 적용하지 않음')
        return
      }
      
      try {
        console.log('📋 사용자 프로필 조회 시작')
        // 사용자 프로필에서 관심 카테고리 가져오기
        const profileResponse = await axios.get('/api/user-profile/get/')
        const interestedCategoryIds = profileResponse.data?.interested_categories || []
        console.log('📊 관심 카테고리 ID:', interestedCategoryIds)
        
        if (interestedCategoryIds.length === 0) {
          console.log('⚠️ 관심 카테고리가 없음 - 태그 필터를 적용하지 않고 모든 공개 시험을 표시합니다')
          // 관심 카테고리가 없으면 selectedTagFilters를 null로 설정하여 태그 필터를 적용하지 않도록 함
          this.selectedTagFilters = []
          return
        }
        
        console.log('📋 각 카테고리의 태그 조회 시작')
        // 각 관심 카테고리에 속한 태그들 가져오기
        const tagPromises = interestedCategoryIds.map(categoryId => 
          axios.get(`/api/tag-categories/${categoryId}/tags/`)
        )
        
        const tagResponses = await Promise.all(tagPromises)
        const allTagIds = []
        
        tagResponses.forEach((response, index) => {
          const categoryId = interestedCategoryIds[index]
          const tags = response.data?.results || response.data || []
          console.log(`📊 카테고리 ${categoryId}의 태그 개수: ${tags.length} 태그:`, tags)
          tags.forEach(tag => {
            if (tag.id && !allTagIds.includes(tag.id)) {
              allTagIds.push(tag.id)
            }
          })
        })
        
        console.log('📊 추출된 모든 태그 ID:', allTagIds)
        
        // 태그가 있으면 필터링 적용, 없으면 null로 설정하여 태그 필터를 적용하지 않도록 함
        if (allTagIds.length > 0) {
          this.selectedTagFilters = allTagIds
          console.log('✅ 관심 카테고리 태그 적용:', allTagIds)
        } else {
          console.log('⚠️ 관심 카테고리에 태그가 없음 - 태그 필터를 적용하지 않고 모든 공개 시험을 표시합니다')
          this.selectedTagFilters = []
        }
      } catch (error) {
        console.error('관심 카테고리 태그 설정 실패:', error)
      }
    },
    
    async loadAvailableTags() {
      try {
        // DevOps 도메인인 경우 서버에서 DevOps 태그 정보를 먼저 가져오기
        const domainConfig = getCurrentDomainConfig()
        if (domainConfig && domainConfig.keyword === 'devops') {
          await this.fetchDevOpsTagFromServer();
        }
        
        const response = await axios.get('/api/studies/tags/');
        this.availableTags = response.data || [];
        
        // 강제 업데이트하여 태그 이름이 올바르게 표시되도록 함
        this.$forceUpdate();
      } catch (error) {
        console.error('태그 목록 로드 실패:', error);
      }
    },
    
    async fetchDevOpsTagFromServer() {
      try {
        const response = await fetch('/api/tags/');
        const data = await response.json();
        
        if (data.results && Array.isArray(data.results)) {
          // 모든 지원 언어 필드를 확인하도록 수정
          const devopsTag = data.results.find(tag => {
            // 모든 지원 언어 필드 확인 (ko, en, es, zh, ja)
            const supportedLanguages = SUPPORTED_LANGUAGES
            for (const lang of supportedLanguages) {
              if (tag[`name_${lang}`] === 'DevOps') {
                return true
              }
            }
            // localized_name도 확인
            return tag.localized_name === 'DevOps'
          });
          
          if (devopsTag) {
            const tagId = devopsTag.id;
            this.setRequiredTagIdToStorage(tagId);
          }
        }
      } catch (error) {
        console.error('DevOps 태그 정보 조회 실패:', error);
      }
    },
    // 원본 시험 선택 로직
    isExamSelected(id) {
      return this.selectedExams.includes(id);
    },
    // 시험 선택 토글
    toggleExamSelection(id, event) {
      id = String(id);
      
      // 비활성화된 체크박스는 선택 불가
      if (event.target.disabled) {
        return;
      }
      
      // 강제 순수 배열화
      this.selectedExams = JSON.parse(JSON.stringify(this.selectedExams.filter(eid => typeof eid === 'string')));
              debugLog('toggleExamSelection:', { id, checked: event.target.checked, selectedExams: this.selectedExams });
      if (event.target.checked) {
        if (!this.selectedExams.includes(id)) {
          this.selectedExams = JSON.parse(JSON.stringify([...this.selectedExams, id]));
        }
      } else {
        this.selectedExams = JSON.parse(JSON.stringify(this.selectedExams.filter(eid => eid !== id)));
      }
              debugLog('selectedExams after:', this.selectedExams);
    },
    // Excel 다운로드
    async downloadExamsExcel() {
      try {
        const response = await axios.get('/api/exams/download-excel/', {
          responseType: 'blob'
        })
        
        // 파일 다운로드
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-')
        const filename = `exams_${timestamp}.xlsx`
        
        link.setAttribute('href', url)
        link.setAttribute('download', filename)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
        
      } catch (error) {
        debugLog('Excel 다운로드 오류:', error, 'error')
        this.showToastNotification(this.$t('examManagement.messages.downloadFailed'), 'error')
      }
    },
    // Excel 업로드 폼 토글
    toggleUploadForm() {
      this.showUploadForm = !this.showUploadForm
      if (!this.showUploadForm) {
        this.resetUploadForm()
      }
    },
    // 업로드 폼 초기화
    resetUploadForm() {
      this.selectedFile = null
      this.uploadMessage = ''
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = ''
      }
    },
    // 업로드 취소
    cancelUpload() {
      this.showUploadForm = false
      this.resetUploadForm()
    },
    // 파일 선택
    handleFileSelect(event) {
      this.selectedFile = event.target.files[0]
      this.uploadMessage = ''
    },
    // Excel 업로드
    async uploadExamsExcel() {
      if (!this.selectedFile) {
        this.showToastNotification(this.$t('examManagement.messages.selectFile'), 'warning')
        return
      }

      try {
        // 로딩 상태 시작
        this.loading = true
        
        const formData = new FormData()
        formData.append('file', this.selectedFile)

        const response = await axios.post('/api/exams/upload-excel/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        
        this.uploadMessage = this.$t('examManagement.messages.uploadSuccess')
        this.loadExams() // 시험 목록 새로고침
        this.resetUploadForm()
        this.showUploadForm = false
        
        // 상세 통계 표시
        if (response.data.stats) {
          const stats = response.data.stats
          let detailMessage = `총 ${stats.total_exams}개 시험 처리\n`
          detailMessage += `생성: ${stats.created}개\n`
          if (stats.skipped > 0) {
            detailMessage += `건너뜀: ${stats.skipped}개\n`
          }
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
          this.uploadMessage = `${this.$t('examManagement.messages.uploadFailed')}: ${error.response.data.detail}`
        } else {
          this.uploadMessage = this.$t('examManagement.messages.uploadFailed')
        }
      } finally {
        // 로딩 상태 종료
        this.loading = false
      }
    },
    // 문제 추가 기능 (원본 시험에 문제 추가)
    async addQuestionToExam(examId) {
              // TakeExam 페이지로 이동하여 새 문제 추가 모드로 전환
        this.$router.push(`/take-exam/${examId}?mode=add-question`)
    },
    
    // 시험 공개 여부 확인
    getExamPublicStatus(exam) {
      // 백엔드에서 제공하는 is_public 필드 사용
      return exam.is_public === true // 명시적으로 true인 경우만 공개로 처리
    },
    
    // 시험 링크 반환 (인증 여부와 공개 여부에 따라 다른 경로)
    getExamLink(exam) {
      if (!exam || !exam.id) return '#'
      
      // 인증된 사용자는 항상 take-exam으로 이동
      if (this.isAuthenticated) {
        return `/take-exam/${exam.id}?returnTo=exam-detail`
      }
      
      // 인증되지 않은 사용자는 공개 시험인 경우 exam-detail로 이동
      if (this.getExamPublicStatus(exam)) {
        return `/exam-detail/${exam.id}`
      }
      
      // 비공개 시험이고 인증되지 않은 사용자는 링크 없음
      return null
    },
    
    // 시험 구독 상태 확인
    getSubscribeStatus(exam) {
      // 자신이 만든 시험은 항상 구독된 것으로 표시
      if (this.isExamForCurrentUser(exam)) {
        if (!isProduction) {
          debugLog('🔍 구독 상태 확인 (자신이 만든 시험):', {
            examId: exam.id,
            examTitle: this.getLocalizedTitle(exam),
            isSubscribed: true,
            reason: '자신이 만든 시험'
          })
        }
        return true
      }
      
      if (!isProduction) {
        debugLog('🔍 구독 상태 확인:', {
          examId: exam.id,
          examTitle: this.getLocalizedTitle(exam),
          isSubscribed: exam.is_subscribed,
          examData: exam
        })
      }
      return exam.is_subscribed === true
    },
    

    
    // 선택된 시험들의 구독 상태에 따른 토글 버튼 클래스
    getBulkSubscriptionButtonClass() {
      if (this.selectedExams.length === 0) return 'action-btn-secondary'
      
      const selectedExamData = this.getSelectedExamData()
      const allSubscribed = selectedExamData.every(exam => exam.is_subscribed)
      const allUnsubscribed = selectedExamData.every(exam => !exam.is_subscribed)
      
      if (allSubscribed) {
        return 'action-btn-warning' // 모두 구독된 경우 구독해제 버튼
      } else if (allUnsubscribed) {
        return 'action-btn-success' // 모두 구독되지 않은 경우 구독 버튼
      } else {
        return 'action-btn-info' // 혼재된 경우 토글 버튼
      }
    },
    
    // 선택된 시험들의 구독 상태에 따른 토글 버튼 아이콘
    getBulkSubscriptionButtonIcon() {
      if (this.selectedExams.length === 0) return 'fas fa-bell'
      
      const selectedExamData = this.getSelectedExamData()
      const allSubscribed = selectedExamData.every(exam => exam.is_subscribed)
      const allUnsubscribed = selectedExamData.every(exam => !exam.is_subscribed)
      
      if (allSubscribed) {
        return 'fas fa-bell-slash' // 모두 구독된 경우 구독해제 아이콘
      } else if (allUnsubscribed) {
        return 'fas fa-bell' // 모두 구독되지 않은 경우 구독 아이콘
      } else {
        return 'fas fa-exchange-alt' // 혼재된 경우 토글 아이콘
      }
    },
    
    // 선택된 시험들의 구독 상태에 따른 토글 버튼 텍스트
    getBulkSubscriptionButtonText() {
      if (this.selectedExams.length === 0) return this.$t('examManagement.subscribe')
      
      const selectedExamData = this.getSelectedExamData()
      const allSubscribed = selectedExamData.every(exam => exam.is_subscribed)
      const allUnsubscribed = selectedExamData.every(exam => !exam.is_subscribed)
      
      if (allSubscribed) {
        return this.$t('examManagement.unsubscribe') // 모두 구독된 경우 구독해제
      } else if (allUnsubscribed) {
        return this.$t('examManagement.subscribe') // 모두 구독되지 않은 경우 구독
      } else {
        return this.$t('examManagement.toggle') // 혼재된 경우 토글
      }
    },
    
    // 선택된 시험들의 데이터 가져오기
    getSelectedExamData() {
      const selectedData = []
      
      this.filteredExamTree.forEach(exam => {
        if (this.selectedExams.includes(String(exam.id))) {
          selectedData.push(exam)
        }
        if (exam.children && exam.children.length > 0) {
          exam.children.forEach(version => {
            if (this.selectedExams.includes(String(version.id))) {
              selectedData.push(version)
            }
          })
        }
      })
      
      return selectedData
    },
    
    // 선택된 시험들의 구독 상태 토글
    async toggleSelectedSubscriptions() {
      if (this.selectedExams.length === 0) {
        this.showToastNotification('구독 상태를 변경할 시험을 선택해주세요.', 'warning')
        return
      }
      
      const selectedExamData = this.getSelectedExamData()
      const allSubscribed = selectedExamData.every(exam => exam.is_subscribed)
      const allUnsubscribed = selectedExamData.every(exam => !exam.is_subscribed)
      
      let action
      
      if (allSubscribed) {
        // 모두 구독된 경우 구독해제
        action = 'unsubscribe'
      } else if (allUnsubscribed) {
        // 모두 구독되지 않은 경우 구독
        action = 'subscribe'
      } else {
        // 혼재된 경우 구독 상태에 따라 개별 처리
        await this.handleMixedSubscriptionToggle(selectedExamData)
        return
      }
      
      try {
        const response = await axios.post('/api/exam-subscription/bulk-toggle/', {
          exam_ids: this.selectedExams,
          action: action
        })
        
        if (response.data.success) {
          this.showToastNotification(response.data.message, 'success')
          
          // 강제로 캐시 무효화하고 시험 목록 새로고침
          this.clearCache()
          sessionStorage.setItem('forceRefreshExamManagement', 'true')
          await this.loadExams()
          
          // 선택 해제
          this.selectedExams = []
        }
      } catch (error) {
        debugLog(`일괄 ${action === 'subscribe' ? '구독' : '구독해제'} 실패:`, error, 'error')
        this.showToastNotification(`일괄 ${action === 'subscribe' ? '구독' : '구독해제'}에 실패했습니다.`, 'error')
      }
    },
    
    // 혼재된 구독 상태 처리
    async handleMixedSubscriptionToggle(selectedExamData) {
      try {
        // 구독할 시험과 구독해제할 시험을 분리
        const toSubscribe = selectedExamData.filter(exam => !exam.is_subscribed).map(exam => exam.id)
        const toUnsubscribe = selectedExamData.filter(exam => exam.is_subscribed).map(exam => exam.id)
        
        // 구독 처리
        if (toSubscribe.length > 0) {
          await axios.post('/api/exam-subscription/bulk-toggle/', {
            exam_ids: toSubscribe,
            action: 'subscribe'
          })
        }
        
        // 구독해제 처리
        if (toUnsubscribe.length > 0) {
          await axios.post('/api/exam-subscription/bulk-toggle/', {
            exam_ids: toUnsubscribe,
            action: 'unsubscribe'
          })
        }
        
        this.showToastNotification(`${toSubscribe.length}개 구독, ${toUnsubscribe.length}개 구독해제 완료`, 'success')
        
        // 강제로 캐시 무효화하고 시험 목록 새로고침
        this.clearCache()
        sessionStorage.setItem('forceRefreshExamManagement', 'true')
        await this.loadExams()
        
        // 선택 해제
        this.selectedExams = []
      } catch (error) {
        debugLog('혼재 구독 상태 토글 실패:', error, 'error')
        this.showToastNotification('구독 상태 변경에 실패했습니다.', 'error')
      }
    },
    
    // AI로 문제 생성 체크박스 변경 이벤트
    onAiGenerateChange() {
      // 체크박스 상태에 따라 AI 생성기 표시/숨김
      // 별도의 추가 로직이 필요하면 여기에 추가
    },
    
    // AI 문제 생성기 토글
    toggleAiGenerator() {
      this.showAiGenerator = !this.showAiGenerator
    },
    
    // AI 문제 생성 완료 이벤트
    onQuestionsGenerated(data) {
      debugLog('파싱된 문제 준비 완료:', data)
      
      // Vue 반응성 문제 해결을 위해 깊은 복사 사용
      this.parsedProblems = JSON.parse(JSON.stringify(data.problems || []))
      
        if (this.parsedProblems.length > 0) {
          this.showToastNotification(
            this.$t('examManagement.createForm.problemsReady', { count: this.parsedProblems.length }),
            'success'
          )
        }
    },
    
    // 파싱된 문제들을 시험에 추가
    goToPage(page) {
      // totalPages 재계산 (안전장치)
      const calculatedTotalPages = this.totalCount > 0 
        ? Math.ceil(this.totalCount / this.pageSize) 
        : 0
      
      if (calculatedTotalPages !== this.totalPages) {
        console.warn(`⚠️ [ExamManagement] totalPages 불일치 감지: 저장된 값=${this.totalPages}, 계산한 값=${calculatedTotalPages}, totalCount=${this.totalCount}, pageSize=${this.pageSize}`)
        this.totalPages = calculatedTotalPages
      }
      
      if (page >= 1 && page <= this.totalPages) {
        this.currentPage = page
        this.loadExams()
      } else {
        console.warn(`⚠️ [ExamManagement] 유효하지 않은 페이지: ${page} (범위: 1-${this.totalPages}, totalCount=${this.totalCount})`)
      }
    },
    async addParsedProblemsToExam(examId) {
      try {
        debugLog('📝 파싱된 문제들을 시험에 추가 시작:', examId)
        
        let successCount = 0
        
        for (let i = 0; i < this.parsedProblems.length; i++) {
          const problem = this.parsedProblems[i]
          
          // 공통 함수 사용
          const questionData = convertToQuestionData(problem)
          
          try {
            await axios.post(`/api/exam/${examId}/add-question/`, questionData)
            debugLog(`✅ 문제 추가 완료: ${problem.title}`)
            successCount++
          } catch (questionError) {
            debugLog(`❌ 문제 추가 실패: ${problem.title}`, questionError, 'error')
          }
        }
        
        debugLog('✅ 모든 파싱된 문제 추가 완료')
        this.showToastNotification(
          `${successCount}개의 파싱된 문제가 시험에 추가되었습니다.`, 
          'success'
        )
        
        // 파싱된 문제 목록 초기화
        this.parsedProblems = []
        
      } catch (error) {
        debugLog('❌ 파싱된 문제 추가 실패:', error, 'error')
        this.showToastNotification(
          '파싱된 문제 추가 중 오류가 발생했습니다.', 
          'error'
        )
      }
    }
  }
}
</script>

<style scoped>
/* Modern Exam Management Styles */
.exam-management-modern {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 10px;
}

/* Form Control Styles */
.form-control {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e9ecef;
  border-radius: 12px;
  font-size: 14px;
  transition: all 0.3s ease;
  background: white;
}



.form-control:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-control.is-invalid {
  border-color: #dc3545;
  box-shadow: 0 0 0 3px rgba(220, 53, 69, 0.1);
}

.invalid-feedback {
  display: block;
  width: 100%;
  margin-top: 0.25rem;
  font-size: 0.875rem;
  color: #dc3545;
  font-weight: 500;
}

.exam-container {
  max-width: 1400px;
  margin: 0 auto;
  background: white;
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  overflow-x: hidden;
  overflow-y: visible;
  position: relative;
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
  text-decoration: none;
}

.action-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
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

.action-btn-danger {
  border-color: #dc3545;
  background: #dc3545;
  color: white;
}

.action-btn-danger:hover:not(:disabled) {
  background: #c82333;
  border-color: #bd2130;
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

.action-btn-info {
  border-color: #17a2b8;
  background: #17a2b8;
  color: white;
}

.action-btn-info:hover:not(:disabled) {
  background: #138496;
  border-color: #117a8b;
}

.action-label {
  font-size: 12px;
  font-weight: 500;
}

.desktop-only {
  display: inline;
}

.mobile-only {
  display: none;
}

.mobile-filter-toggle {
  display: flex;
}

.filter-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.filter-row.mobile-hidden {
  display: none;
}

@media (max-width: 768px) {
  .desktop-only {
    display: none;
  }
  
  /* 원형 버튼 스타일은 공통 CSS (mobile-buttons.css)에서 처리됨 */
  
  .mobile-only {
    display: inline;
  }
  
  .mobile-filter-toggle {
    display: flex;
  }
  
  .filter-row.mobile-hidden {
    display: none;
  }
  
  .filter-row .form-group label {
    display: none;
  }
  
  /* 모바일에서 필터 행의 모든 요소 사이 간격 추가 */
  .filter-row [class*="col-"] {
    margin-bottom: 12px;
  }
  
  /* 모바일에서 Original/Copy와 Public/Private select 가로 정렬 */
  .filter-row .col-6 .form-control {
    width: 100% !important;
    min-width: 0 !important;
  }
  
  /* 모바일에서 두 select 사이 간격 추가 */
  .filter-row .col-6:first-of-type {
    padding-right: 8px;
  }
  
  .filter-row .col-6:last-of-type {
    padding-left: 8px;
  }
  
  /* 모바일에서 form-group 여백 추가 */
  .filter-row .form-group {
    margin-bottom: 0;
    position: relative;
    overflow: visible;
  }
  
  /* 모바일에서 select 드롭다운이 올바른 위치에 표시되도록 */
  .search-filters {
    position: relative;
    overflow-x: hidden;
    overflow-y: visible;
  }
  
  .filter-row {
    position: relative;
    overflow: visible;
  }
  
  .filter-row select {
    position: relative;
    z-index: 10;
  }
  
  .filter-row [class*="col-"] {
    position: relative;
    overflow: visible;
  }
  
  .filter-row [class*="col-"]:focus-within {
    z-index: 1000;
  }
  
  .filter-row select:focus {
    z-index: 1000;
    position: relative;
    outline: none;
  }
  
  /* exam-container overflow 조정 */
  .exam-container {
    overflow-x: hidden;
    overflow-y: visible;
    position: relative;
  }
  
  /* 모달 푸터 버튼을 원형 버튼으로 */
  .modal-footer .btn {
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
  }
  
  .modal-footer .btn i {
    font-size: 14px !important;
    line-height: 1 !important;
    color: white !important;
  }
  
  .modal-footer .btn-secondary i {
    color: white !important;
  }
  
  .modal-footer .btn-secondary:hover i {
    color: white !important;
  }
  
  .modal-footer .btn span {
    display: none !important;
  }
  
  /* card-action-btn을 원형 버튼으로 */
  .card-action-btn {
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
  }
  
  .card-action-btn i {
    font-size: 14px !important;
    line-height: 1 !important;
  }
  
  .card-action-btn .action-label {
    display: none !important;
  }
  
  /* Search by Tags 버튼 모바일 스타일 - 텍스트 숨기고 아이콘만 표시 */
  .btn-outline-primary.btn-sm:has(.fa-tags) {
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
    position: relative !important;
  }
  
  .btn-outline-primary.btn-sm:has(.fa-tags) i {
    font-size: 14px !important;
    line-height: 1 !important;
    margin: 0 !important;
  }
  
  .btn-outline-primary.btn-sm:has(.fa-tags) span:not(.badge),
  .btn-outline-primary.btn-sm:has(.fa-tags) > :not(i):not(.badge) {
    display: none !important;
  }
  
  .btn-outline-primary.btn-sm:has(.fa-tags) .badge {
    position: absolute !important;
    top: -5px !important;
    right: -5px !important;
    font-size: 10px !important;
    padding: 2px 5px !important;
    min-width: 18px !important;
    height: 18px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
  }
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
  border-bottom: 1px solid #e9ecef;
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

/* Exam Form Card */
.exam-form-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  padding: 30px;
  margin: 20px 30px;
  border: 1px solid #e9ecef;
}

@media (max-width: 768px) {
  .exam-form-card {
    margin: 10px;
    padding: 10px;
  }
}

/* Exam List Card */
.exam-list-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  padding: 30px;
  margin: 20px 30px;
  border: 1px solid #e9ecef;
}

@media (max-width: 768px) {
  .exam-list-card {
    margin-top: 10px;
    margin-bottom: 10px;
    padding-top: 20px;
    padding-bottom: 20px;
  }
}

/* Toast Notifications - 기본 스타일은 공통 CSS (mobile-buttons.css)에 정의됨 */

/* 타입별 스타일은 공통 CSS (mobile-buttons.css)에 정의됨 */

.toast-content {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.toast-close {
  background: none;
  border: none;
  color: inherit;
  font-size: 18px;
  cursor: pointer;
  padding: 0;
  margin-left: 15px;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.toast-close:hover {
  opacity: 1;
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

/* Modal Styles */
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

.modal-footer .btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.modal-footer .btn-secondary {
  background: #6c757d;
  color: white;
  border-color: #6c757d;
}

.modal-footer .btn-secondary:hover {
  background: #5a6268;
  border-color: #545b62;
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

.exam-management {
  padding: 20px;
}

.exam-form {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
}

.form-group {
  margin-bottom: 15px;
}

@media (max-width: 768px) {
  .form-group {
    margin-bottom: 0px;
  }
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.btn-group .btn {
  margin-right: 5px;
}

.modal {
  background-color: rgba(0, 0, 0, 0.5);
}

.modal-backdrop {
  z-index: 1040;
}

.modal {
  z-index: 1050;
}

/* 정렬 아이콘 스타일 */
.sortable {
  cursor: pointer;
}

.sort-icon {
  margin-left: 5px;
  font-size: 0.8em;
}

.sortable-header {
  cursor: pointer;
  user-select: none;
  transition: background-color 0.2s;
}

.sortable-header:hover {
  background-color: #e9ecef !important;
}

.sortable-header i {
  font-size: 0.8em;
}

/* 트리 구조 스타일 */
.exam-tree {
  border: 1px solid #dee2e6;
  border-radius: 8px;
  overflow: hidden;
}

.tree-header {
  background-color: #f8f9fa;
  padding: 12px 15px;
  border-bottom: 1px solid #dee2e6;
  font-weight: bold;
}

.tree-body {
  background-color: white;
}

.exam-node {
  border-bottom: 1px solid #f0f0f0;
}

.exam-row {
  padding: 12px 15px;
  transition: background-color 0.2s;
}

.exam-row:hover {
  background-color: #f8f9fa;
}

.original-exam {
  background-color: #f8f9fa;
  border-left: 4px solid #007bff;
}

.version-exam {
  background-color: white;
  border-left: 4px solid #6c757d;
}

.exam-title {
  display: flex;
  align-items: center;
}

.version-indent {
  color: #6c757d;
  margin-right: 8px;
  font-weight: bold;
}

.exam-versions {
  background-color: #fafafa;
  border-top: 1px solid #e9ecef;
}

.btn-link {
  text-decoration: none;
  color: #007bff;
}

.btn-link:hover {
  color: #0056b3;
}

.exam-title-link {
  color: #007bff;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s;
}

.exam-title-link:hover {
  color: #0056b3;
  text-decoration: underline;
}

/* 닫기 버튼 스타일 */
.btn-close {
  background: transparent url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='%23000'%3e%3cpath d='M.293.293a1 1 0 011.414 0L8 6.586 14.293.293a1 1 0 111.414 1.414L9.414 8l6.293 6.293a1 1 0 01-1.414 1.414L8 9.414l-6.293 6.293a1 1 0 01-1.414-1.414L6.586 8 .293 1.707A1 1 0 010.293.293z'/%3e%3c/svg%3e") center/1em auto no-repeat;
  border: 0;
  border-radius: 0.375rem;
  box-sizing: content-box;
  color: #000;
  cursor: pointer;
  height: 1em;
  opacity: 0.5;
  padding: 0.25em;
  transition: opacity 0.15s ease-in-out;
  width: 1em;
}

.btn-close:hover {
  color: #000;
  opacity: 0.75;
}

.btn-close:focus {
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
  opacity: 1;
  outline: 0;
}

/* 커스텀 닫기 버튼 스타일 */
.close-btn {
  width: 24px;
  height: 24px;
  padding: 0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: bold;
  line-height: 1;
  color: #6c757d;
  background-color: transparent;
  border: 1px solid #6c757d;
  transition: all 0.2s ease-in-out;
}

.close-btn:hover {
  color: #fff;
  background-color: #6c757d;
  border-color: #6c757d;
}

.close-btn:focus {
  box-shadow: 0 0 0 0.25rem rgba(108, 117, 125, 0.25);
  outline: 0;
}

.close-btn span {
  display: inline-block;
  transform: scale(1.2);
}

/* 모바일에서 테이블 컬럼 숨기기 - Title만 표시 */
@media (max-width: 768px) {
  /* 기본 그리드 레이아웃 */
  .tree-header .d-flex,
  .exam-row .d-flex {
    display: flex !important;
    width: 100% !important;
    flex-direction: row !important;
  }
  
  /* 체크박스 컬럼 (세션이 있을 때만) - 고정 너비 */
  .tree-header .d-flex .checkbox-column,
  .exam-row .d-flex .checkbox-column {
    width: 21px !important;
    flex: 0 0 21px !important;
  }
  
  /* Title 컬럼 - 전체 남은 공간 사용 (체크박스 제외) */
  .tree-header .d-flex > div:nth-child(2),
  .exam-row .d-flex > div:nth-child(2) {
    width: auto !important;
    flex: 1 !important;
    min-width: 0 !important;
  }
  
  /* 나머지 컬럼들 숨기기 (체크박스와 Title 제외) */
  .tree-header .d-flex > div:nth-child(3),
  .tree-header .d-flex > div:nth-child(4),
  .tree-header .d-flex > div:nth-child(5),
  .tree-header .d-flex > div:nth-child(6),
  .tree-header .d-flex > div:nth-child(7) {
    display: none !important;
  }
  
  .exam-row .d-flex > div:nth-child(3),
  .exam-row .d-flex > div:nth-child(4),
  .exam-row .d-flex > div:nth-child(5),
  .exam-row .d-flex > div:nth-child(6),
  .exam-row .d-flex > div:nth-child(7) {
    display: none !important;
  }
  
  /* Title 컬럼의 폰트 크기 증가 */
  .exam-title {
    font-size: 16px !important;
    line-height: 1.4 !important;
  }
  
  .exam-title strong,
  .exam-title-link {
    font-size: 16px !important;
    line-height: 1.4 !important;
  }
  
  /* exam-list-card 좌우 마진 제거 및 패딩 추가 */
  .card-modern.exam-list-card {
    margin-left: 0px !important;
    margin-right: 0px !important;
    padding-left: 10px !important;
    padding-right: 10px !important;
  }
  

  
  /* Correct 정보와 점수 정보 숨기기 */
  .exam-title .text-success,
  .exam-title .text-success small {
    display: none !important;
  }
  
  /* 점수 퍼센트 정보도 숨기기 */
  .exam-title .text-success.small {
    display: none !important;
  }
}

/* Selected Tags Display Styles */
.selected-tags-display {
  padding: 12px 16px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
  margin: 10px 30px;
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

.selected-tags-display .badge.devops-required {
  background-color: #6c757d !important;
  cursor: default;
}

.selected-tags-display .tag-badge {
  font-size: 10px;
  font-weight: bold;
  background-color: rgba(255, 255, 255, 0.2);
  padding: 2px 4px;
  border-radius: 3px;
}

/* Gap utility class for older browsers */
.gap-2 > * + * {
  margin-left: 8px;
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

/* 모바일 페이지네이션 스타일 */
@media (max-width: 768px) {
  .pagination-container {
    margin-top: 1.5rem;
    padding: 0.75rem 0;
    display: block !important;
  }
  
  .pagination {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    align-items: center;
    gap: 0.25rem;
    padding: 0.75rem;
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  }
  
  .pagination .page-item {
    margin: 0;
  }
  
  .pagination .page-link {
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 36px;
    height: 36px;
    padding: 0.5rem;
    font-size: 0.875rem;
    border-radius: 8px;
  }
  
  .pagination .page-item.active .page-link {
    box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3);
  }
  
  .pagination-info {
    margin-top: 0.75rem;
    font-size: 0.9rem;
    color: #6c757d;
    text-align: center;
  }
}
</style> 