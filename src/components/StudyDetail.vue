<template>
  <div class="study-detail-modern">
    <div class="study-container">
      <!-- Top Header -->
      <div class="top-header">
        <div class="header-actions">
          <!-- 우측 상단 Edit 버튼 제거 - 중복 방지 -->
        </div>
      </div>

      <!-- Page Title -->
      <div class="page-title">
        <h1>{{ study ? getStudyTitle(study) : '' }}</h1>
      </div>
      
      <!-- 스터디 정보 -->
      <div class="card-modern study-info-card">
        <div class="card-header-modern">
          <h3>{{ $t('studyDetail.studyInfo') }}</h3>
          <div class="card-actions" v-if="!editingStudy && (isAdmin || isStudyCreator || isStudyAdmin)">
            <button @click="startEditStudy" class="card-action-btn">
              <i class="fas fa-edit"></i>
              <span class="action-label">{{ $t('studyDetail.edit') }}</span>
            </button>
          </div>
          <div class="card-actions" v-else-if="isAdmin || isStudyCreator || isStudyAdmin">
            <button @click="saveStudyEdit" class="action-btn action-btn-success">
              <i class="fas fa-save"></i>
              <span class="action-label">{{ $t('studyDetail.save') }}</span>
            </button>
            <button @click="cancelEditStudy" class="action-btn action-btn-secondary">
              <i class="fas fa-times"></i>
              <span class="action-label">{{ $t('studyDetail.cancel') }}</span>
            </button>
          </div>
        </div>
        <div class="row align-items-center">
          <div class="col-md-12">
            <div class="row">
              <div class="col-md-6">
                <div class="info-item">
                  <strong>{{ $t('studyDetail.titleLabel') }}</strong>
                  <span v-if="!editingStudy">{{ study ? getStudyTitle(study) : '' }}</span>
                  <div v-else>
                    <div class="mb-2">
                      <label class="form-label">{{ $t('studyDetail.titleLabel') }}</label>
                      <input v-model="editingStudyData[`title_${$i18n.locale}`]" type="text" class="form-control" required>
                    </div>
                  </div>
                </div>
              </div>
              <div class="col-md-6">
                <div class="info-item">
                  <strong>{{ $t('studyDetail.periodLabel') }}</strong>
                  <span v-if="!editingStudy">{{ study ? formatDate(study.start_date) : '' }} ~ {{ study ? formatDate(study.end_date) : '' }}</span>
                  <span v-else>
                    <input v-model="editingStudyData.start_date" type="date" class="form-control d-inline-block w-auto" style="min-width:130px;" required>
                    ~
                    <input v-model="editingStudyData.end_date" type="date" class="form-control d-inline-block w-auto" style="min-width:130px;" required>
                  </span>
                </div>
                <div class="info-item" v-if="isAuthenticated && study">
                  <strong>{{ $t('studyDetail.progressLabel') }}</strong> 
                  <div class="progress-container">
                    <span class="progress-values">
                      {{ $t('studyDetail.correctQuestionsLabel') }} {{ getStudyProgressText(study) }}
                      <small v-if="getStudyProgressPercentage(study) > 0" class="text-muted d-block">
                        ({{ getStudyProgressPercentage(study).toFixed(1) }}%)
                      </small>
                    </span>
                    <router-link 
                      v-if="study"
                      :to="`/study-progress-dashboard/${study.id}`" 
                      class="progress-button"
                      @click="recordProgress(study.id, 'study-detail')"
                    >
                      {{ $t('studyDetail.viewDetails') }}
                    </router-link>
                  </div>
                </div>
                <div class="info-item">
                  <strong>{{ $t('studyDetail.publicStatusLabel') }}</strong>
                  <span v-if="!editingStudy" class="d-inline-flex align-items-center gap-2">
                    <span class="badge" :class="study && study.is_public ? 'bg-success' : 'bg-secondary'">
                      {{ study && study.is_public ? $t('studyDetail.public') : $t('studyDetail.private') }}
                    </span>
                    <button 
                      v-if="!editingStudy && isStudyMember && !isAdmin"
                      @click="leaveStudy" 
                      class="action-btn action-btn-success"
                    >
                      <i class="fas fa-sign-out-alt"></i>
                      <span class="action-label">{{ $t('studyDetail.leaveStudy') }}</span>
                    </button>
                  </span>
                  <select v-else v-model="editingStudyData.is_public" class="form-control d-inline-block w-auto" style="min-width:100px;">
                    <option :value="true">{{ $t('studyDetail.public') }}</option>
                    <option :value="false">{{ $t('studyDetail.private') }}</option>
                  </select>
                </div>
                <div class="info-item" v-if="isAdmin && study">
                  <strong>{{ $t('studyDetail.supportedLanguagesLabel') || 'Supported Languages' }}</strong>
                  <span v-if="!editingStudy">{{ study.supported_languages || '' }}</span>
                  <input 
                    v-else 
                    v-model="editingStudyData.supported_languages" 
                    type="text" 
                    class="form-control d-inline-block w-auto" 
                    style="min-width:200px;"
                    :placeholder="$t('studyDetail.supportedLanguagesPlaceholder') || '예: ko,en'"
                  >
                </div>
              </div>
            </div>
            <div class="row mt-3">
              <div class="col-12">
                <div class="info-item">
                  <strong>{{ $t('studyDetail.goalLabel') }}</strong>
                  <div v-if="!editingStudy" class="goal-content mt-2">
                    <div class="p-3 bg-light rounded" v-html="formatGoal(study ? getStudyGoal(study) : '')"></div>
                  </div>
                  <div v-else>
                    <div class="mb-2">
                      <label class="form-label">{{ $t('studyDetail.goalLabel') }}</label>
                      <textarea 
                        v-model="editingStudyData[`goal_${$i18n.locale}`]" 
                        class="form-control" 
                        rows="3"
                        :placeholder="$t('studyDetail.goalPlaceholder')"
                        style="min-height: 80px; resize: vertical;"
                        required
                      ></textarea>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 태그 관리 섹션 -->
      <div class="card-modern tag-management-card" v-if="isAdmin || isStudyCreator || isStudyAdmin">
        <div class="card-header-modern">
          <h3>{{ $t('studyDetail.tagManagement') }}</h3>
        </div>
        
        <EntityTagManager
          v-if="study"
          entityType="study"
          :entityId="study.id"
          :tags="study.tags || []"
          :canEdit="isAdmin || isStudyCreator || isStudyAdmin"
          @tags-updated="handleTagsUpdated"
          @success="handleTagSuccess"
          @error="handleTagError"
        />
      </div>
      
      <!-- Task 목록 -->
      <div class="task-section mb-5">
        
        <!-- Task 복사 기능 -->
        <div class="task-copy-section mb-4" v-if="isAdmin">
          <div class="row">
            <div class="col-md-3">
              <select v-model="selectedCopyStudy" class="form-control">
                <option value="">{{ $t('studyDetail.selectStudyToCopy') }}</option>
                <option v-for="otherStudy in otherStudies" :key="otherStudy.id" :value="otherStudy.id">
                  {{ getStudyTitle(otherStudy) }}
                </option>
              </select>
            </div>
            <div class="col-md-5">
              <button @click="copyTasksFromStudy" class="btn btn-secondary" :disabled="!selectedCopyStudy">
                {{ $t('studyDetail.copyTasks') }}
              </button>
            </div>
            <div class="col-md-4 d-flex justify-content-end gap-2">
              <button @click="uploadStudyExcel" class="btn btn-info">
                {{ $t('studyDetail.excelUpload') }}
              </button>
              <button 
                @click="downloadStudyExcel" 
                class="btn btn-success"
                v-if="study && study.tasks && study.tasks.length > 0"
              >
                {{ $t('studyDetail.excelDownload') }}
              </button>
              <button v-if="(isAdmin || isStudyCreator || isStudyAdmin) && study && study.tasks && study.tasks.length > 0" @click="deleteSelectedTasks" class="btn btn-danger" :disabled="selectedTasks.length === 0">
                {{ $t('studyDetail.deleteSelected') }} ({{ selectedTasks.length }}{{ $t('studyDetail.memberCount') }})
              </button>
            </div>
          </div>
        </div>
        
        <!-- 엑셀 업로드 카드 (ExamManagement 스타일) -->
        <div v-if="showExcelUpload" class="card mb-4">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-center mb-3">
              <h5 class="card-title mb-0">{{ $t('studyDetail.excelUploadCard') }}</h5>
              <button @click="cancelExcelUpload" class="btn btn-sm btn-secondary">
                <i class="fas fa-times"></i>
              </button>
            </div>
            <div class="row">
              <div class="col-md-8">
                <input 
                  type="file" 
                  ref="excelFileInput" 
                  @change="handleExcelFileChange" 
                  accept=".xlsx,.xls"
                  class="form-control"
                >
              </div>
              <div class="col-md-4">
                <div class="d-flex gap-2">
                  <button @click="submitExcelUpload" class="btn btn-primary" :disabled="!selectedExcelFile">
                    <i class="fas fa-upload me-2"></i>{{ $t('studyDetail.upload') }}
                  </button>
                  <button @click="cancelExcelUpload" class="btn btn-secondary">
                    {{ $t('studyDetail.cancelUpload') }}
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
                <strong>{{ $t('studyDetail.excelFileFormat') }}</strong> {{ $t('studyDetail.taskListSheet') }}
              </div>
              <h6>{{ $t('studyDetail.excelFormatExample') }}</h6>
              <div class="table-responsive">
                <table class="table table-sm table-bordered">
                  <thead class="table-light">
                    <tr>
                      <th>{{ $t('studyDetail.sheetName') }}</th>
                      <th>{{ $t('studyDetail.column') }}</th>
                      <th>{{ $t('studyDetail.description') }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>{{ $t('studyDetail.taskList') }}</td>
                      <td>{{ $t('studyDetail.taskName') }}</td>
                      <td>{{ $t('studyDetail.taskNameRequired') }}</td>
                    </tr>
                    <tr>
                      <td>{{ $t('studyDetail.taskList') }}</td>
                      <td>{{ $t('studyDetail.connectedExam') }}</td>
                      <td>{{ $t('studyDetail.connectedExamOptional') }}</td>
                    </tr>
                    <tr>
                      <td>{{ $t('studyDetail.taskList') }}</td>
                      <td>{{ $t('studyDetail.progressRate') }}</td>
                      <td>{{ $t('studyDetail.progressRateOptional') }}</td>
                    </tr>
                    <tr>
                      <td>{{ $t('studyDetail.taskList') }}</td>
                      <td>{{ $t('studyDetail.examId') }}</td>
                      <td>{{ $t('studyDetail.examIdOptional') }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <small class="text-muted" v-html="$t('studyDetail.excelUploadNotes')">
              </small>
            </div>
          </div>
        </div>
        
        <!-- Task 추가 폼 -->
        <div class="task-form mb-4" v-if="showTaskForm && (isAdmin || isStudyCreator || isStudyAdmin)">
          <div class="d-flex justify-content-between align-items-center mb-3">
            <h3>{{ $t('studyDetail.taskForm') }}</h3>
            <button @click="toggleTaskForm" class="btn btn-sm btn-secondary">
              <i class="fas fa-times"></i>
            </button>
          </div>
          <form @submit.prevent="addTask" class="row" id="addTaskForm">
            <!-- 현재 사용자 언어에 맞는 Task 이름 입력 필드 표시 (모든 언어 지원) -->
            <div class="col-md-3">
              <div class="form-group">
                <label>{{ $t(`studyDetail.taskNameLabel${getCurrentUserLanguage().charAt(0).toUpperCase() + getCurrentUserLanguage().slice(1)}`) || $t('studyDetail.taskNameLabel') }}</label>
                <input 
                  v-model="newTask[`name_${getCurrentUserLanguage()}`]" 
                  type="text" 
                  class="form-control" 
                  :placeholder="$t(`studyDetail.taskNamePlaceholder${getCurrentUserLanguage().charAt(0).toUpperCase() + getCurrentUserLanguage().slice(1)}`) || $t('studyDetail.taskNamePlaceholder') || 'Enter task name'" 
                  required
                >
              </div>
            </div>
            <div class="col-md-3">
              <div class="form-group">
                <label>{{ $t('studyDetail.examSelection') }}</label>
                <select v-model="newTask.exam" class="form-control" required>
                  <option value="">{{ $t('studyDetail.selectExam') }}</option>
                  <option v-for="exam in filteredExams" :key="exam.id" :value="exam.id">
                    {{ getExamTitle(exam) }}
                  </option>
                </select>
              </div>
            </div>
            <div class="col-md-2">
              <div class="form-group">
                <label>{{ $t('studyDetail.progressRateLabel') }}</label>
                <input v-model="newTask.progress" type="number" min="0" max="100" class="form-control" required>
              </div>
            </div>
            <div class="col-md-2">
              <div class="form-group">
                <label>{{ $t('studyDetail.publicStatusLabel2') }}</label>
                <select v-model="newTask.is_public" class="form-control">
                  <option :value="true">{{ $t('studyDetail.public') }}</option>
                  <option :value="false">{{ $t('studyDetail.private') }}</option>
                </select>
              </div>
            </div>
            <div class="col-md-2">
              <div class="form-group">
                <label>&nbsp;</label>
                <button type="submit" class="btn btn-primary form-control" style="display: block !important; visibility: visible !important; opacity: 1 !important; position: static !important; z-index: 1000 !important; /* 드롭다운 */">{{ $t('studyDetail.addTaskButton') }}</button>
              </div>
            </div>
          </form>
          <!-- 별도 행에 저장 버튼 추가 -->
          <div class="row mt-3">
            <div class="col-12 text-center">
              <button type="submit" form="addTaskForm" class="btn btn-primary btn-lg px-5 float-end">{{ $t('studyDetail.addTaskButton') }}</button>
            </div>
          </div>
        </div>

        <!-- Task 테이블 -->
        <div class="card-modern task-table-card">
          <div class="card-header-modern">
            <h3>{{ $t('studyDetail.taskSection') }}</h3>
            <div class="card-actions">
              <button 
                @click="toggleTaskForm" 
                class="action-btn action-btn-success"
                v-if="!showTaskForm && (isAdmin || isStudyCreator || isStudyAdmin)"
              >
                <i class="fas fa-plus"></i>
                <span class="action-label">{{ $t('studyDetail.addTask') }}</span>
              </button>
              <router-link 
                to="/exam-management" 
                class="action-btn action-btn-primary"
              >
                <i class="fas fa-file-alt"></i>
                <span class="action-label">{{ $t('studyDetail.myExams') }}</span>
              </router-link>
            </div>
          </div>
          <div v-if="loading" class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">{{ $t('studyDetail.loading') }}</span>
            </div>
          </div>
          <div v-else-if="!study || !study.tasks || study.tasks.length === 0" class="alert alert-info">
            {{ $t('studyDetail.noTasks') }}
          </div>
          <div v-else class="table-responsive">
          <table class="table table-striped">
            <thead>
              <tr>
                <th v-if="isAdmin || isStudyCreator || isStudyAdmin">
                  <input v-if="isAdmin" type="checkbox" @change="toggleAllTasks" :checked="isAllSelected" :indeterminate="isIndeterminate">
                </th>
                <th class="sortable-header" @click="sortByColumn('name')">
                  {{ $t('studyDetail.taskNameHeader') }}
                  <i :class="getSortIcon('name')" class="ms-1"></i>
                </th>
                <th v-if="isAuthenticated" class="sortable-header" data-column="correct" @click="sortByColumn('exam')">
                  {{ $t('studyDetail.correctQuestionsHeader') }}
                  <i :class="getSortIcon('exam')" class="ms-1"></i>
                </th>
                <th v-if="isAuthenticated" class="sortable-header" data-column="accuracy" @click="sortByColumn('progress')">
                  {{ $t('studyDetail.accuracyHeader') }}
                  <i :class="getSortIcon('progress')" class="ms-1"></i>
                </th>
                <th>{{ $t('studyDetail.publicStatusHeader') }}</th>
                <th v-if="isAdmin || isStudyCreator || isStudyAdmin" data-column="actions">{{ $t('studyDetail.managementHeader') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="task in sortedTasks" :key="task.id">
                <td v-if="isAdmin || isStudyCreator || isStudyAdmin">
                  <input v-if="isAdmin || isStudyCreator || isStudyAdmin" type="checkbox" :value="task.id" v-model="selectedTasks">
                </td>
                <td>
                  <div v-if="editingTask !== task.id">
                    <strong>
                      <!-- exam_summary가 있거나 exam이 있고 (공개 시험이거나 인증된 사용자)면 링크 표시 -->
                      <router-link v-if="(task.exam_summary || task.exam) && (task.exam_summary?.id || task.exam?.id) && 
                                         (task.exam_summary || (task.exam && (task.exam.is_public || isAuthenticated)))" 
                                   :to="getTaskLink(task)" 
                                   class="task-link">
                        {{ getTaskName(task) }}
                      </router-link>
                      <span v-else>{{ getTaskName(task) }}</span>
                    </strong>
                  </div>
                  <div v-else>
                    <!-- 편집 모드에서는 현재 사용자 언어에 맞는 입력 필드 표시 (모든 언어 지원) -->
                    <div>
                      <label class="form-label">{{ $t(`studyDetail.taskNameLabel${getCurrentUserLanguage().charAt(0).toUpperCase() + getCurrentUserLanguage().slice(1)}`) || $t('studyDetail.taskNameLabel') }}</label>
                      <input 
                        v-model="editingTaskData[`name_${getCurrentUserLanguage()}`]" 
                        type="text" 
                        class="form-control mb-2" 
                        :placeholder="$t(`studyDetail.taskNamePlaceholder${getCurrentUserLanguage().charAt(0).toUpperCase() + getCurrentUserLanguage().slice(1)}`) || $t('studyDetail.taskNamePlaceholder') || 'Enter task name'" 
                        required
                      >
                    </div>
                  </div>
                </td>
                <td v-if="isAuthenticated" data-column="correct">
                  <div v-if="editingTask !== task.id">
                    <div v-if="task.exam && task.total_attempts > 0">
                      <span class="text-success">
                        {{ task.correct_attempts }} / {{ task.total_attempts }}
                      </span>
                    </div>
                    <div v-else>
                      <span class="text-muted">-</span>
                    </div>
                  </div>
                  <div v-else>
                    <select v-model="editingTaskData.exam" class="form-control" required>
                      <option value="">{{ $t('studyDetail.selectExam') }}</option>
                      <option v-for="exam in filteredExams" :key="exam.id" :value="exam.id">
                        {{ getExamTitle(exam) }}
                      </option>
                    </select>
                  </div>
                </td>
                <td v-if="isAuthenticated" data-column="accuracy">
                  <div v-if="editingTask !== task.id">
                    <div v-if="task.exam && task.accuracy_percentage !== null">
                      <span class="text-success">
                        {{ task.accuracy_percentage.toFixed(1) }}%
                      </span>
                    </div>
                    <div v-else>
                      <span class="text-muted">-</span>
                    </div>
                  </div>
                  <div v-else>
                    <input v-model="editingTaskData.progress" type="number" min="0" max="100" class="form-control" required>
                  </div>
                </td>
                <td>
                  <div v-if="editingTask !== task.id">
                    <!-- exam_summary나 exam이 있으면 시험의 공개 여부 표시, 없으면 Task의 공개 여부 표시 -->
                    <span v-if="task.exam_summary || task.exam" 
                          class="badge" 
                          :class="(task.exam_summary?.is_public !== undefined ? task.exam_summary.is_public : (task.exam?.is_public || false)) ? 'bg-success' : 'bg-secondary'">
                      {{ (task.exam_summary?.is_public !== undefined ? task.exam_summary.is_public : (task.exam?.is_public || false)) ? $t('studyDetail.public') : $t('studyDetail.private') }}
                    </span>
                    <span v-else class="badge" :class="task.is_public ? 'bg-success' : 'bg-secondary'">
                      {{ task.is_public ? $t('studyDetail.public') : $t('studyDetail.private') }}
                    </span>
                  </div>
                  <div v-else>
                    <select v-model="editingTaskData.is_public" class="form-control">
                      <option :value="true">{{ $t('studyDetail.public') }}</option>
                      <option :value="false">{{ $t('studyDetail.private') }}</option>
                    </select>
                  </div>
                </td>
                <td v-if="isAdmin || isStudyCreator || isStudyAdmin" data-column="actions">
                  <div v-if="isAdmin || isStudyCreator || isStudyAdmin">
                                      <div v-if="editingTask !== task.id">
                    <button @click="startEditTask(task)" class="btn btn-sm btn-secondary me-1">{{ $t('studyDetail.edit') }}</button>
                    <button @click="deleteTask(task.id)" class="btn btn-sm btn-danger">{{ $t('studyDetail.delete') }}</button>
                  </div>
                  <div v-else>
                    <button @click="saveTaskEdit(task.id)" class="btn btn-sm btn-success me-1">{{ $t('studyDetail.save') }}</button>
                    <button @click="cancelEditTask" class="btn btn-sm btn-secondary">{{ $t('studyDetail.cancel') }}</button>
                  </div>
                </div>
                <div v-else>
                  <router-link v-if="task.exam" :to="`/exam-detail/${task.exam.id}`" class="btn btn-sm btn-outline-primary">{{ $t('studyDetail.details') }}</router-link>
                </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      
      <!-- 멤버 목록 섹션 (로그인한 사용자에게만 표시) -->
      <div class="card-modern member-table-card" v-if="isAuthenticated">
        <div class="card-header-modern">
          <h3>{{ $t('studyDetail.memberSection') }}</h3>
          <div class="card-actions">
            <router-link :to="`/member-management/${study ? study.id : ''}`" class="action-btn action-btn-warning" v-if="isAdmin || isStudyCreator || isStudyAdmin">
              <i class="fas fa-users-cog"></i>
              <span class="action-label">{{ $t('studyDetail.memberManagement') }}</span>
            </router-link>
          </div>
        </div>
        
        <div v-if="loading" class="text-center py-3">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">{{ $t('studyDetail.loading') }}</span>
          </div>
        </div>
        <div v-else-if="!study || !study.members || study.members.length === 0" class="alert alert-info">
          {{ $t('studyDetail.noMembers') }}
        </div>
        <div v-else class="table-responsive">
          <table class="table table-striped">
            <thead>
              <tr>
                <th>{{ $t('studyDetail.memberName') }}</th>
                <th>{{ $t('studyDetail.memberId') }}</th>
                <th>{{ $t('studyDetail.affiliation') }}</th>
                <th>{{ $t('studyDetail.location') }}</th>
                <th>{{ $t('studyDetail.role') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="member in study.members.filter(Boolean)" :key="member.id">
                <td>
                  <strong>{{ member.name }}</strong>
                </td>
                <td>{{ member.member_id || '-' }}</td>
                <td>{{ member.affiliation || '-' }}</td>
                <td>{{ member.location || '-' }}</td>
                <td>
                  <span class="badge" :class="getRoleBadgeClass(member.role)">
                    {{ getRoleText(member.role) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      
      <!-- 가입 요청 목록 -->
      <div class="card-modern join-requests-card" v-if="isStudyAdmin">
        <div class="card-header-modern">
          <h3>
            <i class="fas fa-user-plus me-2"></i>
            {{ $t('studyDetail.joinRequestList') }}
          </h3>
        </div>
        <div class="card-body join-requests-body">

          
          <div v-if="joinRequestsLoading" class="text-center">
            <div class="spinner-border" role="status">
              <span class="visually-hidden">{{ $t('studyDetail.loading') }}</span>
            </div>
          </div>
          <div v-else-if="joinRequests.length === 0" class="alert alert-info">
            {{ $t('studyDetail.noJoinRequests') }}
          </div>
          <div v-else class="table-responsive join-requests-table-responsive">
            <table class="table table-striped join-requests-table">
                          <thead>
              <tr>
                <th class="col-requester">{{ $t('studyDetail.requester') }}</th>
                <th class="col-email">{{ $t('studyDetail.email') }}</th>
                <th class="col-message">{{ $t('studyDetail.message') }}</th>
                <th class="col-date">{{ $t('studyDetail.requestDate') }}</th>
                <th class="col-status">{{ $t('studyDetail.status') }}</th>
                <th class="col-actions">{{ $t('studyDetail.actions') }}</th>
              </tr>
            </thead>
              <tbody>
                <tr v-for="request in joinRequests" :key="request.id">
                  <td>
                    <strong>{{ request.user_username }}</strong>
                  </td>
                  <td class="email-cell">{{ request.user_email }}</td>
                  <td class="message-cell">{{ request.message || '-' }}</td>
                  <td>{{ formatDate(request.requested_at) }}</td>
                  <td>
                    <span class="badge" :class="getStatusBadgeClass(request.status)">
                      {{ getStatusText(request.status) }}
                    </span>
                  </td>
                  <td v-if="request.status === 'pending'">
                    <button @click="approveJoinRequest(request)" class="btn btn-sm btn-success me-1">
                      {{ $t('studyDetail.approve') }}
                    </button>
                    <button @click="rejectJoinRequest(request)" class="btn btn-sm btn-danger">
                      {{ $t('studyDetail.reject') }}
                    </button>
                  </td>
                  <td v-else>
                    <small class="text-muted">
                      {{ request.responded_by_username }}{{ $t('studyDetail.respondedBy') }} {{ getStatusText(request.status) }}
                    </small>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
      
      <!-- 확인 모달 -->
      <div v-if="showConfirmModalState" class="modal-overlay" @click="cancelAction">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h5 class="modal-title">
              <i :class="confirmModalData.type === 'danger' ? 'fas fa-exclamation-triangle text-danger' : 'fas fa-question-circle text-warning'"></i>
              {{ confirmModalData.title }}
            </h5>
            <button type="button" class="btn-close" @click="cancelAction"></button>
          </div>
          <div class="modal-body">
            <p>{{ confirmModalData.message }}</p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="cancelAction">
              {{ confirmModalData.cancelText }}
            </button>
            <button type="button" :class="`btn btn-${confirmModalData.type === 'danger' ? 'danger' : 'primary'}`" @click="confirmAction">
              {{ confirmModalData.confirmText }}
            </button>
          </div>
        </div>
      </div>

      <!-- 가입 요청 모달 -->
      <div v-if="showJoinRequestModal" class="modal-overlay" @click="hideJoinRequestModal">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">
              <i class="fas fa-user-plus"></i>
              {{ $t('studyDetail.joinRequest') }}
            </h3>
            <button @click="hideJoinRequestModal" class="modal-close">
              <i class="fas fa-times"></i>
            </button>
          </div>
          <div class="modal-body">
            <p>{{ $t('studyDetail.enterJoinMessage') }}</p>
            <input v-model="joinRequestMessage" type="text" class="form-control" :placeholder="$t('studyDetail.enterJoinMessage')">
          </div>
          <div class="modal-footer">
            <button @click="hideJoinRequestModal" class="action-btn action-btn-secondary">
              {{ $t('common.cancel') }}
            </button>
            <button @click="submitJoinRequest" class="action-btn action-btn-primary">
              {{ $t('studyDetail.joinRequest') }}
            </button>
          </div>
        </div>
      </div>

    </div>
  </div>
  </div>
</template>

<script>
import axios from 'axios'
import { debugLog } from '@/utils/debugUtils'
import { isAdmin, hasStudyAdminRole, hasStudySpecificAdminPermission, getCurrentUser as getCurrentUserFromPermissions } from '@/utils/permissionUtils'
import { formatTextWithLinks } from '@/utils/textUtils'
import { formatLocalDate } from '@/utils/dateUtils'
import { 
  getLocalizedContent, 
  validateMultilingualFields, 
  createMultilingualEditData,
  getCurrentLanguage
} from '@/utils/multilingualUtils'
import EntityTagManager from '@/components/EntityTagManager.vue'

/**
 * 스터디 상세 컴포넌트
 * 
 * 캐시 정리 정책:
 * 1. 스터디 정보 변경 시: clearStudyCache() 호출로 스터디 관련 캐시 정리
 * 2. 멤버 변경 시: clearStudyManagementCache() 호출로 스터디 관리 캐시 정리
 * 3. 강제 새로고침 시: clearAllFilters 이벤트로 모든 캐시 정리
 * 4. 브라우저 캐시: localStorage, sessionStorage에서 스터디 관련 데이터 완전 제거
 * 
 * TODO: console.log를 debugLog로 변경할 수 있는지 반드시 검토해야 함
 * - 운영 환경에서 브라우저 콘솔에 로그가 보이면 안 됨
 * - debugLog는 운영 환경에서 자동으로 비활성화됨
 */
export default {
  name: 'StudyDetail',
  components: {
    EntityTagManager
  },
  data() {
    return {
      study: null,
      otherStudies: [],
      exams: [],
      loading: true, // 로딩 상태 추가
      editingTask: null,
      editingTaskData: {
        name_ko: '',
        name_en: '',
        exam: '',
        progress: 0,
        is_public: true
      },
      newTask: {
        name_ko: '',
        name_en: '',
        exam: '',
        progress: 0,
        is_public: true
      },
      joinRequestsLoading: false,
      selectedTasks: [],
      selectedCopyStudy: null,
      showTaskForm: false,
      editingStudy: false,
      editingStudyData: {
        title_ko: '',
        title_en: '',
        goal_ko: '',
        goal_en: '',
        start_date: new Date().toISOString().split('T')[0],
        end_date: '',
        is_public: true,
        supported_languages: ''
      },
      showExcelUpload: false,
      selectedExcelFile: null,
      sortBy: 'name',
      sortOrder: 'asc',
      uploadMessage: '', // 업로드 결과 메시지
      joinRequests: [], // 가입 요청 목록 저장 (배열)
      // 확인 모달 관련 데이터
      showConfirmModalState: false,
      confirmModalData: {
        title: '',
        message: '',
        confirmText: '',
        cancelText: '',
        confirmCallback: null,
        type: 'warning' // warning, danger, info
      },
      // 가입 요청 모달 관련 데이터
      showJoinRequestModal: false,
      joinRequestMessage: '',
      selectedStudyForJoin: null,
    }
  },
  computed: {
    isAllSelected() {
      return this.study && this.study.tasks && this.study.tasks.length > 0 && 
             this.selectedTasks.length === this.study.tasks.length
    },
    isIndeterminate() {
      return this.study && this.study.tasks && this.study.tasks.length > 0 && 
             this.selectedTasks.length > 0 && this.selectedTasks.length < this.study.tasks.length
    },
    isAdmin() {
      return isAdmin()
    },
    isStudyAdmin() {
      if (!this.study) {
        debugLog('isStudyAdmin: 스터디가 없음')
        return false
      }
      
      const user = this.getCurrentUser()
      if (!user) {
        debugLog('isStudyAdmin: 사용자가 없음')
        return false
      }
      
      debugLog('isStudyAdmin 체크 - 사용자:', user)
      debugLog('사용자 역할:', user.role)
      debugLog('스터디 멤버들:', this.study.members)
      
      // 전역 관리자 권한 확인
      if (isAdmin() || hasStudyAdminRole()) {
        return true
      }
      
      // 특정 스터디 관리자 권한 확인
      return hasStudySpecificAdminPermission(this.study)
    },
    isStudyMember() {
      if (!this.study) return false
      
      const user = this.getCurrentUser()
      if (!user) return false
      
      // 스터디 멤버인지 확인
      return this.study.members && Array.isArray(this.study.members) &&
        this.study.members.some(member => {
          // user 필드가 null이거나 undefined인 경우 건너뛰기
          if (!member.user) {
            return false
          }
          
          // user 필드가 숫자인지 확인하고 타입 변환
          const memberUserId = typeof member.user === 'object' ? member.user.id : member.user
          return memberUserId === user.id && member.is_active === true
        })
    },
    isAuthenticated() {
      const user = getCurrentUserFromPermissions()
      debugLog('🔍 isAuthenticated 호출됨')
      debugLog('🔍 current user:', user)
      return Boolean(user)
    },
    isStudyCreator() {
      if (!this.study || !this.study.created_by) return false
      
      const user = this.getCurrentUser()
      if (!user) return false
      
      // created_by가 객체인 경우 id 필드 사용
      const createdById = typeof this.study.created_by === 'object' ? this.study.created_by.id : this.study.created_by
      
      return createdById === user.id
    },
    sortedTasks() {
      if (!this.study || !this.study.tasks) return []
      
      let tasks = [...this.study.tasks]
      
      // 공개 스터디에 가입하지 않은 사용자의 경우 비공개 시험 Task 필터링
      if (this.study.is_public && !this.isStudyMember && !this.isStudyCreator && !this.isAdmin) {
        tasks = tasks.filter(task => {
          // exam_summary가 있으면 공개 시험이거나 권한이 있는 시험
          if (task.exam_summary) {
            return true
          }
          // exam 객체가 있으면 공개 여부 확인
          if (task.exam) {
            return task.exam.is_public === true
          }
          // exam이 없는 Task는 표시
          return true
        })
      }
      
      tasks.sort((a, b) => {
        let aValue = a[this.sortBy]
        let bValue = b[this.sortBy]
        
        // exam 필드의 경우 다국어 title로 정렬
        if (this.sortBy === 'exam') {
          // 모든 지원 언어를 확인하여 정렬에 사용할 제목 찾기
          const userLang = this.userProfileLanguage || this.$i18n?.locale || 'en'
          
          const getExamTitleForSort = (exam) => {
            if (!exam) return ''
            if (exam.display_title) return exam.display_title
            return getLocalizedContent(exam, 'title', userLang) || exam.title || ''
          }
          
          // exam_summary가 있으면 exam_summary에서 제목 가져오기
          if (a.exam_summary) {
            aValue = getExamTitleForSort(a.exam_summary)
          } else {
            aValue = a.exam ? getExamTitleForSort(a.exam) : ''
          }
          
          if (b.exam_summary) {
            bValue = getExamTitleForSort(b.exam_summary)
          } else {
            bValue = b.exam ? getExamTitleForSort(b.exam) : ''
          }
        }
        
        if (this.sortOrder === 'asc') {
          return aValue > bValue ? 1 : -1
        } else {
          return aValue < bValue ? 1 : -1
        }
      })
      
      return tasks
    },
    // Today's Exam을 제외한 시험 목록
    filteredExams() {
      console.log('🔍 filteredExams 호출됨')
      console.log('🔍 this.exams:', this.exams)
      console.log('🔍 this.exams 타입:', typeof this.exams)
      console.log('🔍 this.exams가 배열인가:', Array.isArray(this.exams))
      
      if (!this.exams || !Array.isArray(this.exams)) {
        console.log('🔍 exams가 없거나 배열이 아님, 빈 배열 반환')
        return []
      }
      
      const filtered = this.exams.filter(exam => {
        // 다국어 제목 필드 확인 (모든 지원 언어 확인)
        const userLang = this.userProfileLanguage || this.$i18n?.locale || 'en'
        
        const examTitle = exam.display_title || getLocalizedContent(exam, 'title', userLang) || exam.title || ''
        console.log('🔍 시험 제목:', examTitle, 'ID:', exam.id)
        
        // "Today's Quizzes for"로 시작하는 시험 제외
        const shouldInclude = !examTitle.startsWith("Today's Quizzes for")
        console.log('🔍 포함 여부:', shouldInclude)
        return shouldInclude
      })
      
      console.log('🔍 필터링 후 시험 수:', filtered.length)
      console.log('🔍 필터링된 시험들:', filtered)
      
      return filtered
    }
  },
  async mounted() {
    console.log('🔍 StudyDetail mounted 시작')
    // 자동 스크롤 비활성화
    // window.scrollTo(0, 0)
    
    this.loading = true
    const studyId = this.$route.params.studyId
    console.log('🔍 studyId:', studyId)
    
    if (studyId) {
      try {
        console.log('🔍 loadStudy 시작')
        await this.loadStudy(studyId)
        console.log('🔍 loadStudy 완료')
        
        console.log('🔍 loadOtherStudies 시작')
        await this.loadOtherStudies(studyId)
        console.log('🔍 loadOtherStudies 완료')
        
        console.log('🔍 loadExams 시작')
        await this.loadExams()
        console.log('🔍 loadExams 완료')
        
        console.log('🔍 loadJoinRequestStatus 시작')
        await this.loadJoinRequestStatus() // 가입 요청 상태 로드
        console.log('🔍 loadJoinRequestStatus 완료')
        
        // 스터디 관리자인 경우 가입 요청 목록도 로드
        if (this.isStudyAdmin) {
          console.log('🔍 스터디 관리자이므로 가입 요청 목록 로드')
          await this.loadJoinRequests()
        } else {
          console.log('🔍 스터디 관리자가 아니므로 가입 요청 목록 로드 안함')
        }
        
        // 페이지 로드 시 진행율 기록 (인증된 사용자만)
        if (this.isAuthenticated) {
          console.log('🔍 recordStudyProgress 시작')
          await this.recordStudyProgress(studyId, 'study-detail')
          console.log('🔍 recordStudyProgress 완료')
        } else {
          console.log('🔍 인증되지 않은 사용자 - recordStudyProgress 건너뜀')
        }
      } finally {
        this.loading = false
        console.log('🔍 mounted 완료')
      }
    } else {
      console.log('🔍 studyId가 없음')
    }
  },
  methods: {
    // 현재 사용자 언어 가져오기 (프로필 언어 우선, 기본값은 'en')
    getCurrentUserLanguage() {
      // 사용자 프로필 언어 우선, 없으면 i18n locale, 기본값은 'en'
      return this.userProfileLanguage || this.$i18n?.locale || 'en'
    },
    
    // 현재 사용자 언어에 맞는 스터디 제목 반환
    getStudyTitle(study) {
      if (!study) return '';
      
      const currentLanguage = getCurrentLanguage(this.$i18n);
      return getLocalizedContent(study, 'title', currentLanguage, '제목 없음');
    },
    
    // 현재 사용자 언어에 맞는 스터디 목표 반환
    getStudyGoal(study) {
      if (!study) return '';
      
      const currentLanguage = getCurrentLanguage(this.$i18n);
      return getLocalizedContent(study, 'goal', currentLanguage, '목표 없음');
    },
    
    // 현재 사용자 언어에 맞는 시험 제목 반환
    getExamTitle(exam) {
      if (!exam) return '';
      
      const currentLanguage = getCurrentLanguage(this.$i18n);
      
      // 다국어 제목 필드 확인 (display_title 우선, 그 다음 사용자 언어, 영어 폴백)
      if (exam.display_title) {
        return exam.display_title;
      }
      
      // 사용자 프로필 언어 우선, 없으면 i18n locale, 기본값은 'en'
      const userLang = this.userProfileLanguage || currentLanguage || 'en'
      
      // 모든 지원 언어 필드를 확인하여 사용자 언어에 맞는 값 반환
      // 사용자 언어 우선
      return exam.display_title || getLocalizedContent(exam, 'title', userLang) || exam.title || ''
    },

    // 스터디 진행률 텍스트 반환 (맞춘 문제수: X / Y 형태) - 시도 기반
    getStudyProgressText(study) {
      if (!study || !study.tasks || study.tasks.length === 0) {
        return '0 / 0';
      }
      
      let totalCorrect = 0;
      let totalAttempts = 0;
      
      for (const task of study.tasks) {
        if (task.exam) {
          // 백엔드에서 제공하는 정확도 계산 근거 데이터 우선 사용
          if (task.correct_attempts !== undefined && task.total_attempts !== undefined) {
            totalCorrect += task.correct_attempts;
            totalAttempts += task.total_attempts;
          } else if (task.exam.questions) {
            // fallback: 기존 로직 사용
            const correctCount = task.exam.user_correct_questions || 0;
            const questionCount = task.exam.questions.length || 0;
            
            totalCorrect += correctCount;
            totalAttempts += questionCount;
          }
        }
      }
      
      if (totalAttempts === 0) {
        return '0 / 0';
      }
      
      return `${totalCorrect} / ${totalAttempts}`;
    },

    // 스터디 진행률 퍼센티지 계산 (시도 기반)
    getStudyProgressPercentage(study) {
      if (!study || !study.tasks || study.tasks.length === 0) {
        return 0;
      }
      
      let totalCorrect = 0;
      let totalAttempts = 0;
      
      for (const task of study.tasks) {
        if (task.exam) {
          // 백엔드에서 제공하는 정확도 계산 근거 데이터 우선 사용
          if (task.correct_attempts !== undefined && task.total_attempts !== undefined) {
            totalCorrect += task.correct_attempts;
            totalAttempts += task.total_attempts;
          } else if (task.exam.questions) {
            // fallback: 기존 로직 사용
            const correctCount = task.exam.user_correct_questions || 0;
            const questionCount = task.exam.questions.length || 0;
            
            totalCorrect += correctCount;
            totalAttempts += questionCount;
          }
        }
      }
      
      if (totalAttempts === 0) {
        return 0;
      }
      
      return (totalCorrect / totalAttempts) * 100;
    },

    // 태스크별 진행률 텍스트 반환 (맞춘 문제수: X / Y 형태) - exam-detail과 동일한 로직
    getTaskProgressText(task) {
      if (!task || !task.exam) {
        return '0 / 0';
      }
      
      // 백엔드에서 제공하는 정확도 계산 근거 데이터 우선 사용
      if (task.correct_attempts !== undefined && task.total_attempts !== undefined) {
        return `${task.correct_attempts} / ${task.total_attempts}`;
      }
      
      // exam-detail과 동일한 로직 사용
      // 1. resultDetails 기반 계산 (우선순위 1)
      if (task.exam.result_details && task.exam.result_details.length > 0) {
        const totalCorrect = task.exam.result_details.filter(detail => detail.is_correct === true).length;
        const totalAttempts = task.exam.result_details.length;
        return `${totalCorrect} / ${totalAttempts}`;
      }
      
      // 2. questionStatistics 기반 계산 (우선순위 2)
      if (task.exam.question_statistics && task.exam.question_statistics.length > 0) {
        const totalCorrect = task.exam.question_statistics.reduce((sum, stat) => sum + (stat.correct_attempts || 0), 0);
        const totalAttempts = task.exam.question_statistics.reduce((sum, stat) => sum + (stat.total_attempts || 0), 0);
        return `${totalCorrect} / ${totalAttempts}`;
      }
      
      // 3. fallback: user_correct_questions와 questions.length 사용
      const correctCount = task.exam.user_correct_questions || 0;
      const questionCount = task.exam.questions ? task.exam.questions.length : 0;
      
      if (questionCount === 0) {
        return '0 / 0';
      }
      
      return `${correctCount} / ${questionCount}`;
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
    
    // 확인 모달 표시 메서드
    openConfirmModal(title, message, confirmText = '확인', cancelText = '취소', type = 'warning', callback = null) {
      this.confirmModalData = {
        title,
        message,
        confirmText,
        cancelText,
        confirmCallback: callback,
        type
      }
      this.showConfirmModalState = true
    },
    
    // 확인 모달 확인 버튼 클릭
    confirmAction() {
      if (this.confirmModalData.confirmCallback) {
        this.confirmModalData.confirmCallback()
      }
      this.showConfirmModalState = false
    },
    
    // 확인 모달 취소 버튼 클릭
    cancelAction() {
      this.showConfirmModalState = false
    },
    
    // 확인 모달 표시 함수 (StudyManagement와 동일한 구조)
    showConfirmModal(title, message, confirmText = '확인', cancelText = '취소', type = 'warning', confirmCallback = null) {
      this.confirmModalData = {
        title: title,
        message: message,
        confirmText: confirmText,
        cancelText: cancelText,
        confirmCallback: confirmCallback,
        type: type
      }
      this.showConfirmModalState = true
    },
    
    async loadStudy(studyId) {
      this.loading = true
      try {
        const response = await axios.get(`/api/studies/${studyId}/`)
        this.study = response.data
        
        // 스터디 관리자인 경우 가입 요청 목록도 로드
        if (this.isStudyAdmin) {
          await this.loadJoinRequests()
        }
      } catch (error) {
        debugLog('스터디 로드 실패:', error, 'error')
        this.showToastNotification(this.$t('studyDetail.alerts.loadStudyFailed'), 'error')
      } finally {
        this.loading = false
      }
    },
    
    async loadJoinRequests() {
      try {
        this.joinRequestsLoading = true
        const studyId = this.$route.params.studyId
        debugLog('가입 요청 목록 로드 시작, studyId:', studyId)
        
        // 현재 사용자 정보 로그
        const user = this.getCurrentUser()
        debugLog('현재 사용자:', user)
        debugLog('isStudyAdmin:', this.isStudyAdmin)
        
        const response = await axios.get(`/api/studies/${studyId}/join-requests/`)
        debugLog('API 응답:', response.data)
        debugLog('API 응답 타입:', typeof response.data)
        debugLog('API 응답이 배열인가:', Array.isArray(response.data))
        
        // 배열인지 확인하고 설정
        if (Array.isArray(response.data)) {
          this.joinRequests = [...response.data] // 스프레드 연산자로 새 배열 생성
        } else {
          debugLog('API 응답이 배열이 아님, 빈 배열로 설정')
          this.joinRequests = []
        }
        
        debugLog('설정 후 joinRequests:', this.joinRequests)
        debugLog('가입 요청 개수:', this.joinRequests.length)
      } catch (error) {
        debugLog('가입 요청 목록 로드 실패:', error, 'error')
        debugLog('오류 응답:', error.response?.data)
        debugLog('오류 상태:', error.response?.status)
        this.joinRequests = []
      } finally {
        this.joinRequestsLoading = false
      }
    },
    
    getStatusText(status) {
      const statusMap = {
        'pending': this.$t('studyDetail.pending'),
        'approved': this.$t('studyDetail.approved'),
        'rejected': this.$t('studyDetail.rejected')
      }
      return statusMap[status] || status
    },
    
    getStatusBadgeClass(status) {
      const classMap = {
        'pending': 'bg-warning',
        'approved': 'bg-success',
        'rejected': 'bg-danger'
      }
      return classMap[status] || 'bg-secondary'
    },
    
    async approveJoinRequest(request) {
      try {
        await axios.post(`/api/study-join-request/${request.id}/respond/`, {
          status: 'approved'
        })
        
        this.showToastNotification(this.$t('studyDetail.approveJoinRequestSuccess'), 'success')
        await this.loadJoinRequests()
        await this.loadStudy(this.$route.params.studyId) // 스터디 정보 새로고침
      } catch (error) {
        debugLog('가입 요청 승인 실패:', error, 'error')
        this.showToastNotification(this.$t('studyDetail.approveJoinRequestFailed'), 'error')
      }
    },
    
    async rejectJoinRequest(request) {
      try {
        await axios.post(`/api/study-join-request/${request.id}/respond/`, {
          status: 'rejected'
        })
        
        this.showToastNotification(this.$t('studyDetail.rejectJoinRequestSuccess'), 'success')
        await this.loadJoinRequests()
      } catch (error) {
        debugLog('가입 요청 거절 실패:', error, 'error')
        this.showToastNotification(this.$t('studyDetail.rejectJoinRequestFailed'), 'error')
      }
    },
    
    getCurrentUser() {
      return getCurrentUserFromPermissions()
    },
    
    async leaveStudy() {
      this.showConfirmModal(
        this.$t('studyDetail.confirmLeaveStudy'),
        this.$t('studyDetail.confirmLeaveStudyMessage'),
        this.$t('studyDetail.leaveStudy'),
        this.$t('studyDetail.cancel'),
        'danger',
        async () => {
          try {
            const user = this.getCurrentUser()
            if (!user) {
              this.showToastNotification(this.$t('studyDetail.loginRequired'), 'error')
              return
            }
            
            // 멤버 정보 찾기
            const member = this.study.members.find(m => m.user === user.id)
            if (!member) {
              this.showToastNotification(this.$t('studyDetail.memberNotFound'), 'error')
              return
            }
            
            // 멤버 삭제 API 호출
            await axios.delete(`/api/members/${member.id}/`)
            
            // 가입 요청도 함께 삭제
            try {
              await axios.delete(`/api/study-join-request/user/${this.study.id}/`)
              debugLog('가입 요청 삭제 완료')
            } catch (error) {
              debugLog('가입 요청 삭제 실패 (무시):', error, 'error')
            }
            
            this.showToastNotification(this.$t('studyDetail.leaveStudySuccess'), 'success')
            
            // 캐시 클리어
            this.clearStudyManagementCache()
            
            // 추가 캐시 무효화
            this.forceClearAllCache()
            
            // 스터디 상세 페이지에서 나가기 (강제 새로고침 파라미터 추가)
            this.$router.push('/study-management?refresh=true')
          } catch (error) {
            debugLog('스터디 탈퇴 실패:', error, 'error')
            if (error.response && error.response.data && error.response.data.error) {
              this.showToastNotification(error.response.data.error, 'error')
            } else {
              this.showToastNotification(this.$t('studyDetail.leaveStudyFailed'), 'error')
            }
          }
        }
      )
    },
      
      // 강제로 모든 캐시 클리어
      forceClearAllCache() {
        try {
          // localStorage 완전 삭제
          localStorage.clear()
          debugLog('🗑️ localStorage 완전 삭제 완료')
          
          // sessionStorage 완전 삭제
          sessionStorage.clear()
          debugLog('🗑️ sessionStorage 완전 삭제 완료')
          
          // 브라우저 캐시 무효화를 위한 강제 새로고침 플래그 설정
          localStorage.setItem('forceRefresh', Date.now().toString())
          debugLog('🔄 강제 새로고침 플래그 설정')
          
          debugLog('모든 캐시 강제 클리어 완료')
        } catch (error) {
          debugLog('캐시 강제 클리어 실패:', error, 'error')
        }
      },
      
      // 스터디 관리 페이지 캐시 클리어
      clearStudyManagementCache() {
        try {
          // sessionStorage 완전 삭제
          sessionStorage.clear()
          
          // localStorage에서 studyManagement 관련 항목만 삭제
          const keysToRemove = []
          for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i)
            if (key && (key.startsWith('studyManagement_') || key.includes('studyManagement'))) {
              keysToRemove.push(key)
            }
          }
          
          keysToRemove.forEach(key => {
            localStorage.removeItem(key)
            debugLog(`🗑️ 캐시 제거: ${key}`)
          })
          
          // 추가로 모든 캐시 관련 키들도 삭제
          const allKeysToRemove = []
          for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i)
            if (key && (key.includes('Cache') || key.includes('cache'))) {
              allKeysToRemove.push(key)
            }
          }
          
          allKeysToRemove.forEach(key => {
            localStorage.removeItem(key)
            debugLog(`🗑️ 추가 캐시 제거: ${key}`)
          })
          
          debugLog('스터디 관리 캐시 클리어 완료:', keysToRemove.length + allKeysToRemove.length, '개 항목 삭제')
        } catch (error) {
          debugLog('캐시 클리어 실패:', error, 'error')
        }
      },
      
      // checkAndUpdateProgress 메서드 제거 - 백엔드에서 개인별 진행률을 올바르게 계산하므로 더 이상 필요하지 않음
    async loadOtherStudies(currentStudyId) {
      try {
        const response = await axios.get('/api/studies/')
        
        // API 응답이 {count, results} 형태인지 확인
        let studiesData
        if (response.data && response.data.results) {
          studiesData = response.data.results
        } else {
          studiesData = response.data
        }
        
        this.otherStudies = studiesData.filter(study => study.id !== currentStudyId)
      } catch (error) {
        debugLog('다른 스터디 로드 실패:', error, 'error')
      }
    },
    async loadExams() {
      try {
        console.log('🔍 loadExams 시작')
        console.log('🔍 this.isAuthenticated:', this.isAuthenticated)
        
        // 사용자 인증 상태에 따라 적절한 파라미터로 시험 목록 요청
        let url = '/api/exams/'
        const params = []
        
        if (this.isAuthenticated) {
          // 로그인한 사용자의 경우: 내가 생성한 시험 + 공개 시험 모두 포함
          params.push('my_exams_public=true')
          console.log('🔍 로그인 사용자: my_exams_public=true 추가')
        } else {
          // 익명 사용자의 경우: 공개 시험만
          params.push('is_public=true')
          console.log('🔍 익명 사용자: is_public=true 추가')
        }
        
        // 페이지네이션 없이 모든 시험 조회
        params.push('page_size=1000')
        
        // 필요한 필드만 선택 (questions 제외하여 성능 최적화)
        params.push('select=id,title_ko,title_en,display_title,description_ko,description_en,created_at,is_original,original_exam,version_number,is_public,total_questions,created_by,created_language,is_ko_complete,is_en_complete,ai_mock_interview')
        
        if (params.length > 0) {
          url += '?' + params.join('&')
        }
        
        console.log('🔍 최종 URL:', url)
        console.log('🔍 axios 요청 시작')
        
        const response = await axios.get(url)
        console.log('🔍 axios 응답 상태:', response.status)
        console.log('🔍 axios 응답 헤더:', response.headers)
        console.log('🔍 API 응답:', response.data)
        
        // API 응답이 {count, results} 형태인지 확인
        if (response.data && response.data.results) {
          this.exams = response.data.results
          console.log('🔍 results 구조 사용, 시험 수:', this.exams.length)
        } else {
          this.exams = response.data
          console.log('🔍 배열 구조 사용, 시험 수:', this.exams.length)
        }
        
        console.log('🔍 this.exams:', this.exams)
        console.log('🔍 시험 목록 로드 완료:', this.exams.length, '개')
      } catch (error) {
        console.error('🔍 시험 목록 로드 실패:', error)
        this.exams = []
      }
    },
    formatDate(dateString) {
      return formatLocalDate(dateString)
    },
    
    // 목표 텍스트 포맷팅 (줄바꿈과 URL 링크 처리)
    formatGoal(text) {
      return formatTextWithLinks(text)
    },
    /**
     * Task 편집을 시작합니다.
     * 현재 사용자 언어에 맞는 이름 필드만 설정합니다.
     */
    startEditTask(task) {
      this.editingTask = task.id
      const userLang = this.getCurrentUserLanguage()
      
      // 다국어 필드 편집 데이터 생성 (사용자 언어에 맞는 필드만 설정)
      const nameEditData = createMultilingualEditData(task, 'name', userLang);
      
      this.editingTaskData = {
        ...nameEditData,
        exam: task.exam ? task.exam.id : '',
        progress: task.progress || 0,
        is_public: task.is_public
      }
      
      // 스터디 공개 여부도 편집 모드로 설정
      this.editingStudy = true
      this.editingStudyData = {
        title: this.getStudyTitle(this.study),
        goal: this.study.goal,
        start_date: this.study.start_date,
        end_date: this.study.end_date,
        is_public: this.study.is_public
      }
      debugLog('편집 시작 - task:', task)
      debugLog('편집 데이터:', this.editingTaskData)
    },
    /**
     * Task 편집 내용을 저장합니다.
     * 현재 사용자 언어에 맞는 이름 필드만 처리합니다.
     */
    async saveTaskEdit(taskId) {
      try {
        const userLang = this.getCurrentUserLanguage()
        
        // 다국어 필드 유효성 검사
        if (!validateMultilingualFields(this.editingTaskData, 'name')) {
          // StudyTask는 name_ko와 name_en만 지원하므로, 사용자 언어에 맞는 메시지 표시
          // i18n 키를 동적으로 생성하여 모든 언어 지원
          const messageKey = `studyDetail.enterTaskName${userLang.charAt(0).toUpperCase() + userLang.slice(1)}`;
          const fallbackMessage = this.$t('studyDetail.enterTaskName') || 'Please enter the task name.';
          const message = this.$t(messageKey) || fallbackMessage;
          this.showToastNotification(message, 'warning');
          return;
        }
        
        // Task 정보 업데이트 - 사용자 언어에 맞는 필드 설정 (모든 언어 지원)
        const nameEditData = createMultilingualEditData(this.editingTaskData, 'name', userLang)
        const updateData = {
          // 모든 언어 필드 포함
          ...nameEditData,
          exam: this.editingTaskData.exam,
          progress: this.editingTaskData.progress,
          is_public: this.editingTaskData.is_public,
          study: this.study.id
        }
        
        debugLog('전송할 데이터:', updateData)
        debugLog('원본 editingTaskData:', this.editingTaskData)
        
        await axios.put(`/api/study-tasks/${taskId}/`, updateData)
        
        // 스터디 정보도 업데이트 (공개 여부 포함)
        const studyPayload = {
          title: this.editingStudyData.title,
          goal: this.editingStudyData.goal,
          start_date: this.editingStudyData.start_date,
          end_date: this.editingStudyData.end_date,
          is_public: this.editingStudyData.is_public
        }
        await axios.patch(`/api/studies/${this.study.id}/`, studyPayload)
        
        this.editingTask = null
        this.editingStudy = false
        this.editingTaskData = { name_ko: '', name_en: '', exam: '', progress: 0 }
        await this.loadStudy(this.study.id)
        this.showToastNotification(this.$t('studyDetail.alerts.updateTaskSuccess'), 'success')
      } catch (error) {
        debugLog('Task 수정 실패:', error, 'error')
        debugLog('에러 응답:', error.response?.data, 'error')
        this.showToastNotification(this.$t('studyDetail.alerts.updateTaskFailed'), 'error')
      }
    },
    cancelEditTask() {
      this.editingTask = null
      this.editingStudy = false
      this.editingTaskData = { name_ko: '', name_en: '', exam: '', progress: 0, is_public: true }
    },

    toggleTaskForm() {
      this.showTaskForm = !this.showTaskForm
      debugLog('Toggle Task Form - showTaskForm:', this.showTaskForm)
      debugLog('Permissions - isAdmin:', this.isAdmin, 'isStudyCreator:', this.isStudyCreator, 'isStudyAdmin:', this.isStudyAdmin)
      if (this.showTaskForm) {
        // Task 폼을 열 때 스터디의 공개 상태에 따라 기본값 설정
        this.newTask = { 
          name_ko: '', 
          name_en: '', 
          exam: '', 
          progress: 0, 
          is_public: this.study ? this.study.is_public : true 
        }
        debugLog('Task form opened, newTask:', this.newTask)
      } else {
        this.resetTaskForm()
      }
    },
    resetTaskForm() {
      this.newTask = { name_ko: '', name_en: '', exam: '', progress: 0, is_public: true }
    },
    /**
     * 새로운 Task를 추가합니다.
     * 현재 사용자 언어에 맞는 이름 필드만 처리합니다.
     */
    async addTask() {
      try {
        const userLang = this.getCurrentUserLanguage()
        
        // 다국어 필드 유효성 검사
        if (!validateMultilingualFields(this.newTask, 'name')) {
          // 모든 언어 지원 - i18n 키를 동적으로 생성
          const messageKey = `studyDetail.enterTaskName${userLang.charAt(0).toUpperCase() + userLang.slice(1)}`;
          const fallbackMessage = this.$t('studyDetail.enterTaskName') || 'Please enter the task name.';
          const message = this.$t(messageKey) || fallbackMessage;
          this.showToastNotification(message, 'warning');
          return;
        }
        
        // Task 데이터 구성 - 사용자 언어에 맞는 필드 설정 (모든 언어 지원)
        const taskData = {
          ...createMultilingualEditData(this.newTask, 'name', userLang),
          exam: this.newTask.exam,
          progress: this.newTask.progress,
          is_public: this.newTask.is_public,
          study: this.study.id
        }
        
        await axios.post('/api/study-tasks/', taskData)
        
        this.resetTaskForm()
        this.showTaskForm = false
        await this.loadStudy(this.study.id)
        this.showToastNotification(this.$t('studyDetail.alerts.addTaskSuccess'), 'success')
      } catch (error) {
        debugLog('Task 추가 실패:', error, 'error')
        this.showToastNotification(this.$t('studyDetail.alerts.addTaskFailed'), 'error')
      }
    },
    async deleteTask(taskId) {
      this.openConfirmModal(
        this.$t('confirm.deleteStudy'),
        this.$t('confirm.deleteStudy'),
        this.$t('confirm.delete'),
        this.$t('confirm.cancel'),
        'danger',
        async () => {
          try {
            await axios.delete(`/api/study-tasks/${taskId}/`)
            await this.loadStudy(this.study.id)
          } catch (error) {
            debugLog('Task 삭제 실패:', error, 'error')
            this.showToastNotification(this.$t('studyDetail.alerts.deleteTaskFailed'), 'error')
          }
        }
      )
    },
    toggleAllTasks() {
      if (this.isAllSelected) {
        this.selectedTasks = []
      } else {
        if (this.study && this.study.tasks) {
          this.selectedTasks = this.study.tasks.map(task => task.id)
        }
      }
    },
    async deleteSelectedTasks() {
      if (this.selectedTasks.length === 0) {
        this.showToastNotification(this.$t('studyDetail.alerts.selectTaskToDelete'), 'warning')
        return
      }
      
      this.openConfirmModal(
        this.$t('confirm.deleteSelectedTasks', { count: this.selectedTasks.length }),
        this.$t('confirm.deleteSelectedTasks', { count: this.selectedTasks.length }),
        this.$t('confirm.delete'),
        this.$t('confirm.cancel'),
        'danger',
        async () => {
          try {
            for (const taskId of this.selectedTasks) {
              try {
                await axios.delete(`/api/study-tasks/${taskId}/`)
              } catch (error) {
                debugLog(`Task ${taskId} 삭제 실패:`, error, 'error')
              }
            }
            
            await this.loadStudy(this.study.id)
            this.selectedTasks = []
            this.showToastNotification(`${this.selectedTasks.length}개의 Task가 삭제되었습니다.`, 'success')
            
          } catch (error) {
            debugLog('Task 일괄 삭제 실패:', error, 'error')
            this.showToastNotification(this.$t('studyDetail.alerts.deleteTaskFailed'), 'error')
          }
        }
      )
    },
    /**
     * 선택된 스터디에서 Task들을 복사합니다.
     * 다국어 필드를 올바르게 처리합니다.
     */
    async copyTasksFromStudy() {
      if (!this.selectedCopyStudy) {
        this.showToastNotification(this.$t('studyDetail.alerts.selectStudyToCopy'), 'warning')
        return
      }
      
      try {
        const sourceStudy = this.otherStudies.find(s => s.id === this.selectedCopyStudy)
        if (!sourceStudy || !sourceStudy.tasks) {
          this.showToastNotification(this.$t('studyDetail.alerts.noTaskToCopy'), 'warning')
          return
        }
        
        for (const task of sourceStudy.tasks) {
          try {
            // 다국어 필드 처리: 기존 name 필드가 있으면 양쪽 언어에 모두 설정
            const taskData = {
              name_ko: task.name_ko || task.name || '',
              name_en: task.name_en || task.name || '',
              exam: task.exam,
              progress: task.progress,
              study: this.study.id
            }
            
            await axios.post('/api/study-tasks/', taskData)
          } catch (error) {
            // 다국어 필드에서 이름 추출하여 로깅
            const taskName = getLocalizedContent(task, 'name', getCurrentLanguage(this.$i18n), 'Unknown');
            debugLog(`Task ${taskName} 복사 실패:`, error, 'error')
          }
        }
        
        await this.loadStudy(this.study.id)
        this.selectedCopyStudy = null
        this.showToastNotification(this.$t('studyDetail.alerts.taskCopyComplete'), 'success')
        
      } catch (error) {
        debugLog('Task 복사 실패:', error, 'error')
        this.showToastNotification(this.$t('studyDetail.alerts.taskCopyFailed'), 'error')
      }
    },
    startEditStudy() {
      if (!this.study) return
      this.editingStudy = true
      
      // 현재 언어에 해당하는 제목이 없으면 다른 언어의 제목을 fallback으로 사용
      this.editingStudyData = {
        title_ko: this.study.title_ko || getLocalizedContent(this.study, 'title', 'ko') || '',
        title_en: this.study.title_en || getLocalizedContent(this.study, 'title', 'en') || '',
        goal_ko: this.study.goal_ko || getLocalizedContent(this.study, 'goal', 'ko') || '',
        goal_en: this.study.goal_en || getLocalizedContent(this.study, 'goal', 'en') || '',
        start_date: this.study.start_date,
        end_date: this.study.end_date,
        is_public: this.study.is_public,
        supported_languages: this.study.supported_languages || ''
      }
    },
    async saveStudyEdit() {
      try {
        const payload = {
          title_ko: this.editingStudyData.title_ko,
          title_en: this.editingStudyData.title_en,
          goal_ko: this.editingStudyData.goal_ko,
          goal_en: this.editingStudyData.goal_en,
          start_date: this.editingStudyData.start_date,
          end_date: this.editingStudyData.end_date,
          is_public: this.editingStudyData.is_public,
          supported_languages: this.editingStudyData.supported_languages || ''
        }
        await axios.patch(`/api/studies/${this.study.id}/`, payload)
        this.editingStudy = false
        await this.loadStudy(this.study.id)
      } catch (error) {
        this.showToastNotification(this.$t('studyDetail.alerts.updateStudyFailed'), 'error')
        debugLog(error, null, 'error')
      }
    },
    cancelEditStudy() {
      this.editingStudy = false
    },
    
    // 엑셀 다운로드
    async downloadStudyExcel() {
      try {
        const response = await axios.get(`/api/studies/${this.study.id}/download-excel/`, {
          responseType: 'blob'
        })
        
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        const studyTitle = this.getStudyTitle(this.study);
        link.setAttribute('download', `${studyTitle}_tasks.xlsx`)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
      } catch (error) {
        debugLog('엑셀 다운로드 실패:', error, 'error')
        this.showToastNotification(this.$t('studyDetail.alerts.excelDownloadFailed'), 'error')
      }
    },
    
    // 엑셀 업로드 토글
    uploadStudyExcel() {
      this.showExcelUpload = !this.showExcelUpload
      if (!this.showExcelUpload) {
        this.cancelExcelUpload()
      }
    },
    
    // 엑셀 파일 선택
    handleExcelFileChange(event) {
      const file = event.target.files[0]
      if (file) {
        this.selectedExcelFile = file
      }
    },
    
    // 엑셀 업로드 제출
    async submitExcelUpload() {
      if (!this.selectedExcelFile) {
        this.showToastNotification(this.$t('studyDetail.alerts.selectFile'), 'warning')
        return
      }
      try {
        const formData = new FormData()
        formData.append('file', this.selectedExcelFile)
        formData.append('study_id', this.study.id)
        const response = await axios.post('/api/studies/upload-excel/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        this.uploadMessage = response.data.message
        this.cancelExcelUpload()
        await this.loadStudy(this.study.id)
        this.showToastNotification(this.$t('studyDetail.alerts.excelUploadComplete'), 'success')
      } catch (error) {
        debugLog('엑셀 업로드 실패:', error, 'error')
        if (error.response && error.response.data && error.response.data.detail) {
          this.uploadMessage = `업로드 실패: ${error.response.data.detail}`
        } else {
          this.uploadMessage = '파일 업로드 중 오류가 발생했습니다.'
        }
      }
    },
    
    // 엑셀 업로드 취소
    cancelExcelUpload() {
      this.showExcelUpload = false
      this.selectedExcelFile = null
      this.uploadMessage = ''
      if (this.$refs.excelFileInput) {
        this.$refs.excelFileInput.value = ''
      }
    },
    
    // 정렬 기능
    sortByColumn(column) {
      if (this.sortBy === column) {
        // 같은 컬럼을 클릭하면 정렬 순서 변경
        this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc'
      } else {
        // 다른 컬럼을 클릭하면 해당 컬럼으로 정렬하고 오름차순으로 설정
        this.sortBy = column
        this.sortOrder = 'asc'
      }
    },
    
    // 정렬 아이콘 반환
    getSortIcon(column) {
      if (this.sortBy !== column) {
        return 'fas fa-sort'
      }
      return this.sortOrder === 'asc' ? 'fas fa-sort-up' : 'fas fa-sort-down'
    },

    // 현재 시험의 최신 점수 백분율 계산
    getCurrentExamScorePercentage(exam) {
      if (!exam || !exam.id || !exam.total_questions) {
        return 0;
      }
      
      const correctCount = exam.user_correct_questions || 0;
      if (exam.total_questions > 0) {
        return (correctCount / exam.total_questions) * 100;
      }
      return 0;
    },

    // 진행율 기록 페이지로 이동
    recordProgress(studyId, returnTo) {
      this.$router.push({
        name: 'StudyProgressDashboard',
        params: { studyId: studyId },
        query: { returnTo: returnTo }
      })
    },

    // 스터디 진행율 기록
    async recordStudyProgress(studyId, pageType) {
      // 인증되지 않은 사용자는 진행율 기록하지 않음
      if (!this.isAuthenticated) {
        debugLog('인증되지 않은 사용자 - 진행율 기록 건너뜀')
        return
      }
      
      try {
        // 브라우저의 로컬 시간을 ISO 형식으로 전송
        const clientTime = new Date().toISOString()
        
        await axios.post('/api/record-study-progress/', {
          study_id: studyId,
          page_type: pageType,
          client_time: clientTime
        })
      } catch (error) {
        debugLog('진행율 기록 실패:', error, 'error')
      }
    },
    
    // 멤버 역할 관련 헬퍼 메서드들
    getRoleDisplayName(role) {
      const roleMap = {
        'member': '멤버',
        'study_admin': '스터디 관리자',
        'study_leader': '스터디 리더'
      }
      return roleMap[role] || role
    },
    
    getRoleBadgeClass(role) {
      const badgeMap = {
        'member': 'bg-primary',
        'study_admin': 'bg-warning',
        'study_leader': 'bg-success'
      }
      return badgeMap[role] || 'bg-secondary'
    },
    
    // 가입 요청 보내기
    async requestJoinStudy(study) {
      // 로그인하지 않은 사용자인 경우 로그인 화면으로 이동
      if (!this.isAuthenticated) {
        this.$router.push('/login')
        return
      }
      
      this.selectedStudyForJoin = study
      this.joinRequestMessage = ''
      this.showJoinRequestModal = true
    },
    
    // 가입 요청 모달 숨기기
    hideJoinRequestModal() {
      this.showJoinRequestModal = false
      this.selectedStudyForJoin = null
      this.joinRequestMessage = ''
    },
    
    // 가입 요청 제출
    async submitJoinRequest() {
      if (!this.selectedStudyForJoin) return
      
      // 로그인하지 않은 사용자인 경우 로그인 화면으로 이동
      if (!this.isAuthenticated) {
        this.hideJoinRequestModal()
        this.$router.push('/login')
        return
      }
      
      try {
        const response = await axios.post('/api/study-join-request/', {
          study_id: this.selectedStudyForJoin.id,
          message: this.joinRequestMessage
        })
        
        this.showToastNotification(this.$t('studyDetail.joinRequestSent'), 'success')
        
        // 가입 요청 상태 업데이트
        this.joinRequests[this.selectedStudyForJoin.id] = response.data.join_request_id
        
        // 스터디 정보 새로고침
        await this.loadStudy(this.study.id)
        
        // 모달 닫기
        this.hideJoinRequestModal()
      } catch (error) {
        debugLog('가입 요청 실패:', error, 'error')
        
        // 인증 오류인 경우 로그인 화면으로 이동
        if (error.response && error.response.status === 401) {
          this.hideJoinRequestModal()
          this.$router.push('/login')
          return
        }
        
        if (error.response && error.response.data && error.response.data.error) {
          this.showToastNotification(error.response.data.error, 'error')
        } else {
          this.showToastNotification(this.$t('studyDetail.joinRequestFailed'), 'error')
        }
      }
    },
    
    // 가입 요청 취소
    async cancelJoinRequest(study) {
      // 로그인하지 않은 사용자인 경우 로그인 화면으로 이동
      if (!this.isAuthenticated) {
        this.$router.push('/login')
        return
      }
      
      this.openConfirmModal(
        this.$t('studyDetail.confirmCancelJoinRequest'),
        this.$t('studyDetail.confirmCancelJoinRequest'),
        this.$t('confirm.cancel'),
        this.$t('confirm.cancel'),
        'warning',
        async () => {
          try {
            const requestId = this.joinRequests[study.id]
            if (!requestId) {
              this.showToastNotification(this.$t('studyDetail.joinRequestNotFound'), 'error')
              return
            }
            
            await axios.delete(`/api/study-join-request/${requestId}/cancel/`)
            
            this.showToastNotification(this.$t('studyDetail.joinRequestCancelled'), 'success')
            
            // 가입 요청 상태 제거
            delete this.joinRequests[study.id]
            
            // 스터디 정보 새로고침
            await this.loadStudy(this.study.id)
          } catch (error) {
            debugLog('가입 요청 취소 실패:', error, 'error')
            
            // 인증 오류인 경우 로그인 화면으로 이동
            if (error.response && error.response.status === 401) {
              this.$router.push('/login')
              return
            }
            
            if (error.response && error.response.data && error.response.data.error) {
              this.showToastNotification(error.response.data.error, 'error')
            } else {
              this.showToastNotification(this.$t('studyDetail.cancelJoinRequestFailed'), 'error')
            }
          }
        }
      )
    },
    
    // 스터디에 가입 요청이 있는지 확인
    hasJoinRequest(study) {
      return Object.prototype.hasOwnProperty.call(this.joinRequests, study.id)
    },
    
    // 가입 요청 상태 로드
    async loadJoinRequestStatus() {
      try {
        const user = this.getCurrentUser()
        if (!user) return
        
        // 현재 사용자의 모든 가입 요청 조회
        const response = await axios.get('/api/study-join-request/user/')
        const requests = response.data
        
        // 스터디별로 가입 요청 상태 저장
        this.joinRequests = {}
        requests.forEach(request => {
          if (request.status === 'pending') {
            this.joinRequests[request.study] = request.id
          }
        })
        
        debugLog('가입 요청 상태 로드:', this.joinRequests)
      } catch (error) {
        debugLog('가입 요청 상태 로드 실패:', error, 'error')
        this.joinRequests = {}
      }
    },
    
    // 멤버 역할 텍스트 반환
    getRoleText(role) {
      const roleMap = {
        'member': this.$t('studyDetail.roleMember'),
        'study_admin': this.$t('studyDetail.roleStudyAdmin'),
        'study_leader': this.$t('studyDetail.roleStudyLeader')
      }
      return roleMap[role] || role
    },
    /**
     * 현재 사용자 언어에 맞는 Task 이름을 반환
     * Study의 Title과 동일한 방식으로 동작:
     * - 한국어 사용자: name_ko 우선, 없으면 name_en, 둘 다 없으면 name
     * - 영어 사용자: name_en 우선, 없으면 name_ko, 둘 다 없으면 name
     * @param {Object} task - Task 객체
     * @returns {string} 현재 언어에 맞는 Task 이름
     */
    // Task 링크 반환 (인증 여부와 공개 여부에 따라 다른 경로)
    getTaskLink(task) {
      const examId = task.exam_summary?.id || task.exam?.id
      if (!examId) return '#'
      
      // 인증되지 않은 사용자가 공개 시험을 클릭한 경우 exam-detail로 이동
      if (!this.isAuthenticated && task.exam && task.exam.is_public) {
        return `/exam-detail/${examId}?studyId=${this.study.id}&examId=${examId}`
      }
      
      // 그 외의 경우 (인증된 사용자 또는 exam_summary가 있는 경우) take-exam으로 이동
      return `/take-exam/${examId}?returnTo=exam-detail&studyId=${this.study.id}&examId=${examId}`
    },
    getTaskName(task) {
      if (!task) return '';
      
      const currentLanguage = getCurrentLanguage(this.$i18n);
      return getLocalizedContent(task, 'name', currentLanguage, '이름 없음');
    },
    
    // 태그 관련 메서드들
    getLocalizedTagName(tag) {
      if (!tag) return '';
      
      // 태그 이름은 다국어로 표시하되, 필터링은 항상 tag.id 사용
      const currentLanguage = getCurrentLanguage(this.$i18n) || 'en';
      return getLocalizedContent(tag, 'name', currentLanguage) || tag.localized_name || 'No Tag';
    },
    
    // EntityTagManager 이벤트 핸들러들
    handleTagsUpdated(updatedTags) {
      console.log('🔄 StudyDetail handleTagsUpdated 호출됨')
      console.log('📊 업데이트된 태그들:', updatedTags)
      // study 객체의 tags 업데이트
      if (this.study) {
        this.study.tags = updatedTags
      }
    },
    
    handleTagSuccess(message) {
      console.log('✅ StudyDetail handleTagSuccess:', message)
      this.showToastNotification(message, 'success')
    },
    
    handleTagError(error) {
      console.error('❌ StudyDetail handleTagError:', error)
      this.showToastNotification('태그 관리 중 오류가 발생했습니다.', 'error')
    }
  }
}
</script>

<style scoped>
/* Modern Study Detail Styles */
.study-detail-modern {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.container {
  max-width: 1400px;
  margin: 0 auto;
  background: white;
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.study-container {
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

.card-header-modern {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e9ecef;
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

.action-label {
  font-weight: 500;
}

.action-btn-success .action-label {
  color: white;
}

/* Study Info Styles */
.study-info-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(66, 165, 245, 0.1);
  padding: 30px;
  margin: 20px 30px;
  border: 1px solid #e9ecef;
}

.info-item {
  margin-bottom: 15px;
  padding: 10px 0;
  border-bottom: 1px solid #f8f9fa;
  display: flex;
  align-items: flex-start;
  flex-wrap: wrap;
}

.info-item:last-child {
  border-bottom: none;
}

.info-item strong {
  color: #2c3e50;
  font-weight: 600;
  margin-right: 10px;
  min-width: 120px;
  display: inline-block;
}

@media (max-width: 768px) {
  .info-item {
    padding: 0px;
  }
  
  .info-item strong {
    display: none !important;
  }
  
  .info-item:has(.goal-content) {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .info-item:has(.goal-content) strong {
    display: none !important;
  }
  
  .form-label {
    display: none !important;
  }
  
  /* 원형 버튼 스타일은 공통 CSS (mobile-buttons.css)에서 처리됨 */
  
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
}

@media (max-width: 576px) {
  .card-action-btn {
    width: 36px !important;
    height: 36px !important;
  }
  
  .card-action-btn i {
    font-size: 12px !important;
  }
}

.info-item span {
  color: #495057;
  font-weight: 500;
}

@media (max-width: 768px) {
  /* 공개 여부 info-item의 span을 flex로 만들어 badge와 버튼을 좌우 배치 */
  .info-item:has(.badge) > span {
    display: flex !important;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    gap: 10px;
  }
  
  .info-item:has(.badge) > span .badge {
    flex-shrink: 0;
  }
  
  .info-item:has(.badge) > span .action-btn {
    flex-shrink: 0;
    margin-left: auto;
  }
}


/* Form Controls */
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

.form-control.d-inline-block {
  display: inline-block;
  width: auto;
}

/* Badge Styles */
.badge {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.bg-success {
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%) !important;
  color: white !important;
}

.bg-secondary {
  background: linear-gradient(135deg, #8d9aa6 0%, #6c757d 100%) !important;
  color: white !important;
}

/* Link Styles */
.exam-link, .task-link {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.3s ease;
  padding: 4px 8px;
  border-radius: 6px;
  text-align: left !important;
  display: inline-block;
}

.exam-link:hover, .task-link:hover {
  color: #5a6fd8;
  background: rgba(102, 126, 234, 0.1);
  text-decoration: none;
}



/* Goal Content */
.goal-content {
  background: #f8fafc;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e9ecef;
  overflow-wrap: break-word;
  word-wrap: break-word;
}

.goal-content p {
  margin: 0;
  line-height: 1.6;
  color: #495057;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

/* goal-content 내부의 링크가 긴 URL에서도 줄바꿈되도록 */
.goal-content a {
  word-break: break-all;
  overflow-wrap: break-word;
  display: inline-block;
  max-width: 100%;
}

/* 가입 요청 테이블 컬럼 너비 설정 */
.join-requests-table {
  table-layout: auto; /* auto로 변경하여 내용에 맞게 조정 */
  width: 100%;
  min-width: 100%;
}

.join-requests-table .col-requester {
  width: auto;
  min-width: 80px;
}

.join-requests-table .col-email {
  width: auto;
  min-width: 150px;
  max-width: 180px;
}

.join-requests-table .col-message {
  width: auto;
  min-width: 200px;
}

.join-requests-table .col-date {
  width: auto;
  min-width: 100px;
}

.join-requests-table .col-status {
  width: auto;
  min-width: 70px;
}

.join-requests-table .col-actions {
  width: auto;
  min-width: 150px;
}

/* 가입 요청 테이블 반응형 컨테이너 */
.join-requests-table-responsive {
  width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

/* 가입 요청 테이블의 email 컬럼 너비 제한 */
.join-requests-card .table td.email-cell {
  max-width: 180px;
  word-break: break-all;
  overflow-wrap: break-word;
  white-space: normal;
  font-size: 0.9em;
}

/* 가입 요청 테이블의 message 컬럼 줄바꿈 처리 */
.join-requests-card .table td.message-cell {
  word-wrap: break-word;
  overflow-wrap: break-word;
  word-break: break-word;
  white-space: normal;
}

/* Task Section */
.task-section {
  margin-bottom: 50px;
}

/* Member Section */
.member-section {
  margin-bottom: 50px;
}

/* Task Copy Section */
.task-copy-section {
  margin-bottom: 30px;
  padding: 20px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e9ecef;
}

/* Task Table Card */
.task-table-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  padding: 30px;
  margin: 20px 30px;
  border: 1px solid #e9ecef;
}

/* Member Table Card */
.member-table-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  padding: 30px;
  margin: 20px 30px;
  border: 1px solid #e9ecef;
}

/* Join Requests Card */
.join-requests-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  padding: 30px;
  margin: 20px 30px;
  border: 1px solid #e9ecef;
  overflow-x: auto; /* 테이블이 카드를 넘어가도 스크롤 가능 */
}

/* Tag Management Card */
.tag-management-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  padding: 30px;
  margin: 20px 30px;
  border: 1px solid #e9ecef;
}

.tag-display {
  margin-top: 10px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-item {
  display: inline-flex;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
  transition: all 0.3s ease;
}

.tag-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.no-tags {
  text-align: center;
  color: #6c757d;
  font-style: italic;
  padding: 40px 20px;
  background: #f8f9fa;
  border-radius: 12px;
  border: 2px dashed #dee2e6;
}

.no-tags i {
  font-size: 24px;
  margin-bottom: 10px;
  display: block;
  color: #adb5bd;
}

.task-form {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  padding: 30px;
  margin: 20px 30px;
  border: 1px solid #e9ecef;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 8px;
  display: block;
  font-size: 14px;
}

/* Table Styles */
.table-responsive {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  margin: 20px 30px;
  overflow-x: auto;
  overflow-y: hidden;
  -webkit-overflow-scrolling: touch;
  /* iOS Safari에서 테이블이 제대로 스크롤되도록 함 */
}

/* Table Column Widths */
.table th:nth-child(1), .table td:nth-child(1) {
  width: 50px !important;
  min-width: 50px !important;
  max-width: 50px !important; /* Checkbox column - iOS에서 고정 너비 */
}

/* 체크박스 컬럼 강제 고정 (인증된 사용자) */
.task-table-card .table th:nth-child(1):has(+ th[data-column="correct"]),
.task-table-card .table td:nth-child(1):has(+ td[data-column="correct"]) {
  width: 50px !important;
  min-width: 50px !important;
  max-width: 50px !important;
}

.table th:nth-child(2), .table td:nth-child(2) {
  width: 25%;
  min-width: 200px; /* Task name column - 인증되지 않은 사용자일 때 더 넓게 */
  word-wrap: break-word;
  overflow-wrap: break-word;
  text-align: left !important; /* Task 항목 좌측 정렬 */
}

/* Task 테이블의 Task 컬럼 강제 좌측 정렬 */
.task-table-card .table th:nth-child(2),
.task-table-card .table td:nth-child(2),
.task-table-card .table th:first-child,
.task-table-card .table td:first-child {
  text-align: left !important;
}

/* Task 컬럼 내부 요소들도 좌측 정렬 */
.task-table-card .table td:nth-child(2) > div,
.task-table-card .table td:first-child > div,
.task-table-card .table td:nth-child(2) strong,
.task-table-card .table td:first-child strong,
.task-table-card .table td:nth-child(2) .task-link,
.task-table-card .table td:first-child .task-link {
  text-align: left !important;
  display: block;
}

.table th:nth-child(3), .table td:nth-child(3) {
  width: 15%;
  min-width: 80px; /* Correct questions column - iOS에서 최소 너비 보장 */
  white-space: nowrap;
}

.table th:nth-child(4), .table td:nth-child(4) {
  width: 15%;
  min-width: 80px; /* Progress column - iOS에서 최소 너비 보장 */
  white-space: nowrap;
}

.table th:nth-child(5), .table td:nth-child(5) {
  width: 20%;
  min-width: 150px; /* Public status column - 더 넓게 설정 */
  white-space: nowrap;
}

/* Public 컬럼 - 인증되지 않은 사용자일 때 마지막 컬럼 */
.task-table-card .table th:last-child:not([data-column]),
.task-table-card .table td:last-child:not([data-column]) {
  min-width: 150px !important; /* Public 컬럼 최소 너비 */
  max-width: 200px !important; /* Public 컬럼 최대 너비 */
  width: 20% !important;
}

/* Public 컬럼 (인증되지 않은 사용자일 때 두 번째 컬럼) */
.task-table-card .table td:nth-child(2):not([data-column]),
.task-table-card .table th:nth-child(2):not([data-column]) {
  text-align: left !important;
  min-width: 150px !important; /* Public 컬럼 최소 너비 */
  max-width: 200px !important; /* Public 컬럼 최대 너비 */
  width: 20% !important;
}

.table th:nth-child(6), .table td:nth-child(6) {
  width: 20%;
  min-width: 100px; /* Management column - iOS에서 최소 너비 보장 */
  white-space: nowrap;
}

/* 인증되지 않은 사용자일 때 Task 컬럼이 더 넓어지도록 */
.task-table-card .table th:nth-child(1):not(:has(+ th[data-column="correct"])),
.task-table-card .table td:nth-child(1):not(:has(+ td[data-column="correct"])) {
  width: 70%;
  min-width: 300px; /* Task name column - 인증되지 않은 사용자일 때 더 넓게 */
}

/* Period column specific styling */
.table th[data-column="period"], .table td[data-column="period"] {
  min-width: 180px;
  white-space: nowrap;
}

/* Responsive table adjustments */
@media (max-width: 768px) {
  .table-responsive {
    margin: 10px;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
  
  .table {
    min-width: 600px; /* iOS에서 최소 테이블 너비 보장 */
    table-layout: fixed;
  }
  
  .table th, .table td {
    min-width: auto;
    white-space: normal;
    font-size: 12px; /* 모바일에서 폰트 크기 감소 */
    padding: 8px 6px; /* 모바일에서 패딩 더 감소 */
    word-wrap: break-word;
    overflow-wrap: break-word;
    word-break: break-word;
  }
  
  /* col-12에 적절한 패딩 추가 (인라인 스타일 오버라이드) */
  .study-info-card .row .col-12 {
    padding-left: 15px !important;
    padding-right: 15px !important;
  }
  
  .goal-content {
    padding: 8px; /* 모바일에서 더 작은 패딩 */
    overflow-wrap: break-word;
    word-wrap: break-word;
    word-break: break-all;
    max-width: 100%;
    box-sizing: border-box;
  }
  
  .goal-content > div {
    padding: 8px !important;
  }
  
  /* goal-content 내부의 링크가 화면을 넘지 않도록 */
  .goal-content a {
    word-break: break-all;
    overflow-wrap: break-word;
    display: inline-block;
    max-width: 100%;
    box-sizing: border-box;
  }
  
  /* goal-content 내부의 div도 너비 제한 */
  .goal-content > div {
    max-width: 100%;
    overflow-wrap: break-word;
    word-wrap: break-word;
    word-break: break-all;
  }
  
  /* iOS에서 테이블 컬럼 너비 재조정 */
  .table th:nth-child(1), .table td:nth-child(1) {
    width: 40px;
    min-width: 40px;
    max-width: 40px;
  }
  
  .table th:nth-child(2), .table td:nth-child(2) {
    width: auto;
    min-width: 150px;
  }
  
  .table th:nth-child(3), .table td:nth-child(3) {
    width: 80px;
    min-width: 80px;
  }
  
  .table th:nth-child(4), .table td:nth-child(4) {
    width: 80px;
    min-width: 80px;
  }
  
  .table th:nth-child(5), .table td:nth-child(5) {
    width: 90px;
    min-width: 90px;
  }
  
  .table th:nth-child(6), .table td:nth-child(6) {
    width: 100px;
    min-width: 100px;
  }
}

.table {
  margin: 0;
  border-collapse: separate;
  border-spacing: 0;
  table-layout: auto; /* auto로 변경하여 컬럼이 동적으로 조정되도록 */
  width: 100%;
  /* iOS에서 테이블 레이아웃을 auto로 하여 컬럼이 내용에 맞게 조정되도록 함 */
}

/* Task 테이블 전체에 대한 기본 정렬 설정 */
.task-table-card .table {
  text-align: left !important;
}

.task-table-card .table th,
.task-table-card .table td {
  text-align: left !important;
}

/* 인증되지 않은 사용자: Task가 첫 번째, Public이 두 번째 */
.task-table-card .table td:first-child:not(:has(input[type="checkbox"])),
.task-table-card .table th:first-child:not(:has(input[type="checkbox"])) {
  text-align: left !important;
  width: auto !important;
  min-width: 200px !important;
}

/* 체크박스가 있는 첫 번째 컬럼은 50px로 고정 */
.task-table-card .table td:first-child:has(input[type="checkbox"]),
.task-table-card .table th:first-child:has(input[type="checkbox"]) {
  width: 50px !important;
  min-width: 50px !important;
  max-width: 50px !important;
  text-align: center !important;
}

.task-table-card .table td:first-child > *,
.task-table-card .table td:first-child > * > *,
.task-table-card .table td:first-child > * > * > * {
  text-align: left !important;
}

/* Public 컬럼 (인증되지 않은 사용자일 때 두 번째 컬럼) */
.task-table-card .table td:nth-child(2):not([data-column]),
.task-table-card .table th:nth-child(2):not([data-column]) {
  text-align: left !important;
  min-width: 200px !important; /* Public 컬럼도 더 넓게 */
  width: auto !important;
}

.table th {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-weight: 600;
  font-size: 14px;
  padding: 16px 12px;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.table th:hover {
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
  transform: translateY(-1px);
}

.table th i {
  margin-left: 8px;
  font-size: 12px;
}

.table td {
  padding: 16px 12px;
  border: none;
  border-bottom: 1px solid #f8f9fa;
  vertical-align: middle;
  transition: all 0.3s ease;
  word-wrap: break-word;
  overflow-wrap: break-word;
  word-break: break-word;
}

/* Task 테이블의 Task 컬럼 강제 좌측 정렬 */
.task-table-card .table td:first-child,
.task-table-card .table th:first-child {
  text-align: left !important;
}

.task-table-card .table td:nth-child(2),
.task-table-card .table th:nth-child(2) {
  text-align: left !important;
}

.table tbody tr {
  transition: all 0.3s ease;
}

.table tbody tr:hover {
  background: #f8fafc;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* Sortable Header */
.sortable-header {
  cursor: pointer;
  user-select: none;
  transition: background-color 0.2s;
}

.sortable-header:hover {
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%) !important;
}

.sortable-header i {
  font-size: 0.8em;
}

/* Alert Styles */
.alert {
  border-radius: 12px;
  padding: 16px 20px;
  margin: 20px 30px;
  border: none;
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

.btn-sm.btn-secondary {
  background: white;
  border-color: #6c757d;
  color: #6c757d;
}

.btn-sm.btn-secondary:hover {
  background: #6c757d;
  border-color: #6c757d;
  color: white;
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

/* Responsive Design */
@media (max-width: 768px) {
  .study-detail-modern {
    padding: 5px;
  }
  
  .container {
    margin: 0;
    border-radius: 0;
  }
  
  .alert {
    padding: 8px;
    margin: 5px 0;
  }
  
  .card-modern,
  .study-info-card,
  .task-table-card,
  .member-table-card,
  .join-requests-card,
  .tag-management-card,
  .task-form {
    margin: 5px;
    padding: 12px;
  }
  
  .table-responsive {
    margin: 5px;
    padding: 0;
  }
  
  /* Join Requests 테이블은 더 넓은 공간 사용 */
  .join-requests-card {
    margin: 5px 0;
    padding: 12px 0; /* 좌우 패딩 제거 */
    overflow: visible; /* 테이블이 카드를 넘어가도 보이도록 */
  }
  
  .join-requests-card .card-header-modern {
    padding: 10px 12px; /* 헤더만 좌우 패딩 유지 */
  }
  
  .join-requests-body {
    padding: 0 !important; /* body 패딩 완전 제거 */
    margin: 0;
    width: 100%;
    overflow-x: auto;
  }
  
  .join-requests-card .table-responsive,
  .join-requests-table-responsive {
    margin: 0;
    padding: 0;
    width: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
  
  .join-requests-table {
    width: 100%;
    min-width: 750px; /* 최소 너비 더 증가 */
    table-layout: auto; /* 내용에 맞게 조정 */
  }
  
  /* Join Requests 테이블 컬럼 최소 너비 조정 */
  .join-requests-table .col-requester {
    min-width: 100px;
  }
  
  .join-requests-table .col-email {
    min-width: 160px;
  }
  
  .join-requests-table .col-message {
    min-width: 250px;
  }
  
  .join-requests-table .col-date {
    min-width: 110px;
  }
  
  .join-requests-table .col-status {
    min-width: 80px;
  }
  
  .join-requests-table .col-actions {
    min-width: 180px;
  }
  
  .page-title {
    padding: 10px 5px;
    margin: 0;
  }
  
  .page-title h1 {
    font-size: 1.5rem;
    margin: 0;
  }
  
  .card-header-modern {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
    padding: 10px 0;
    margin-bottom: 10px;
  }
  
  .card-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  .card-body {
    padding: 10px 0;
  }
}

/* 확인 모달 스타일 */
.modal-overlay {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  width: 100% !important;
  height: 100% !important;
  background: rgba(0, 0, 0, 0.5) !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  z-index: 2000 !important; /* 모달 오버레이 */
  backdrop-filter: blur(5px) !important;
}

.modal-content {
  background: white !important;
  border-radius: 12px !important;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3) !important;
  max-width: 500px !important;
  width: 90% !important;
  max-height: 80vh !important;
  overflow-y: auto !important;
  position: relative !important;
  margin: 20px !important;
  border: none !important;
  outline: none !important;
}

.modal-header {
  padding: 20px 24px 0 !important;
  border-bottom: none !important;
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  background: transparent !important;
}

.modal-title {
  margin: 0 !important;
  font-size: 18px !important;
  font-weight: 600 !important;
  display: flex !important;
  align-items: center !important;
  gap: 8px !important;
  color: #2c3e50 !important;
}

.modal-body {
  padding: 20px 24px !important;
  color: #495057 !important;
  line-height: 1.6 !important;
}

.modal-footer {
  padding: 0 24px 20px !important;
  border-top: none !important;
  display: flex !important;
  gap: 12px !important;
  justify-content: flex-end !important;
  background: transparent !important;
}

.btn-close {
  background: none !important;
  border: none !important;
  font-size: 20px !important;
  cursor: pointer !important;
  padding: 0 !important;
  width: 24px !important;
  height: 24px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  border-radius: 50% !important;
  transition: background-color 0.2s !important;
  color: #6c757d !important;
}

.btn-close:hover {
  background-color: #f8f9fa !important;
}

/* 모달 내부 버튼 스타일 */
.modal-footer .btn {
  padding: 10px 20px !important;
  border-radius: 8px !important;
  font-weight: 500 !important;
  border: 2px solid transparent !important;
  transition: all 0.3s ease !important;
  cursor: pointer !important;
  text-decoration: none !important;
  display: inline-flex !important;
  align-items: center !important;
  gap: 6px !important;
}

.modal-footer .btn-secondary {
  background: #6c757d !important;
  color: white !important;
  border-color: #6c757d !important;
}

.modal-footer .btn-secondary:hover {
  background: #5a6268 !important;
  border-color: #545b62 !important;
}

.modal-footer .btn-primary {
  background: #007bff !important;
  color: white !important;
  border-color: #007bff !important;
}

.modal-footer .btn-primary:hover {
  background: #0056b3 !important;
  border-color: #0056b3 !important;
}

.modal-footer .btn-danger {
  background: #dc3545 !important;
  color: white !important;
  border-color: #dc3545 !important;
}

.modal-footer .btn-danger:hover {
  background: #c82333 !important;
  border-color: #bd2130 !important;
}

/* 모달 애니메이션 */
.modal-overlay {
  animation: fadeIn 0.3s ease-out !important;
}

.modal-content {
  animation: slideIn 0.3s ease-out !important;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-50px) scale(0.9);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* 진행률 표시 스타일 */
.progress-container {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-left: 0.5rem;
}

.progress-values {
  color: #28a745 !important;
  text-decoration: none !important;
  font-weight: 600 !important;
  transition: all 0.3s ease !important;
  padding: 4px 8px !important;
  border-radius: 6px !important;
  font-size: 1.1rem !important;
}

.progress-button {
  display: inline-block !important;
  padding: 0.375rem 0.75rem !important;
  font-size: 0.875rem !important;
  font-weight: 500 !important;
  line-height: 1.5 !important;
  text-align: center !important;
  text-decoration: none !important;
  vertical-align: middle !important;
  cursor: pointer !important;
  border: 1px solid #007bff !important;
  border-radius: 0.375rem !important;
  color: #007bff !important;
  background-color: transparent !important;
  transition: all 0.15s ease-in-out !important;
}

.progress-button:hover {
  color: #fff !important;
  background-color: #007bff !important;
  border-color: #007bff !important;
  text-decoration: none !important;
}

/* 모바일에서 테이블 컬럼 제한 */
@media (max-width: 768px) {
  /* Members 테이블 - Name과 MemberID만 표시 */
  .member-table-card .table th:nth-child(3),
  .member-table-card .table th:nth-child(4),
  .member-table-card .table th:nth-child(5),
  .member-table-card .table td:nth-child(3),
  .member-table-card .table td:nth-child(4),
  .member-table-card .table td:nth-child(5) {
    display: none;
  }
  
  /* Join Request 테이블 - Requester와 Actions만 표시 */
  .card .table th:nth-child(2),
  .card .table th:nth-child(3),
  .card .table th:nth-child(4),
  .card .table th:nth-child(5),
  .card .table td:nth-child(2),
  .card .table td:nth-child(3),
  .card .table td:nth-child(4),
  .card .table td:nth-child(5) {
    display: none;
  }
  
  /* Task 테이블 - 모바일에서 맞춘 문제, 합격률, Actions 열 숨기기 */
  /* data-column 속성을 사용하여 권한이 있든 없든 올바른 열을 숨김 */
  .task-table-card .table th[data-column="correct"],
  .task-table-card .table td[data-column="correct"],
  .task-table-card .table th[data-column="accuracy"],
  .task-table-card .table td[data-column="accuracy"],
  .task-table-card .table th[data-column="actions"],
  .task-table-card .table td[data-column="actions"] {
    display: none;
  }
  
  /* Task 테이블 체크박스 컬럼 너비 조정 */
  .task-table-card .table th:nth-child(1),
  .task-table-card .table td:nth-child(1) {
    width: 40px;
    min-width: 40px;
    max-width: 40px;
    padding: 8px 4px;
    text-align: center;
  }
  
  /* Task 이름 컬럼 너비 조정 - 체크박스가 있을 때 2번째 열 */
  .task-table-card .table th:nth-child(2),
  .task-table-card .table td:nth-child(2) {
    width: calc(100% - 40px);
    min-width: 0;
  }
  
  /* Members 테이블 컬럼 너비 조정 */
  .member-table-card .table th:nth-child(1),
  .member-table-card .table td:nth-child(1) {
    width: 60%;
    min-width: 0;
  }
  
  .member-table-card .table th:nth-child(2),
  .member-table-card .table td:nth-child(2) {
    width: 40%;
    min-width: 0;
  }
  
  /* progress-button을 원형 버튼으로 */
  .progress-button {
    padding: 0 !important;
    width: 40px !important;
    height: 40px !important;
    border-radius: 50% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 0 !important;
    min-width: auto !important;
  }
  
  .progress-button::after {
    content: '\f06e'; /* Font Awesome eye icon */
    font-family: 'Font Awesome 5 Free';
    font-weight: 900;
    font-size: 14px !important;
    color: #007bff;
  }
}
</style>