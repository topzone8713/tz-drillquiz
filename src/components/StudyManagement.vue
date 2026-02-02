<template>
  <div class="study-management">
    <div class="container">
      <!-- Page Title -->
      <div class="page-title">
        <h1 @click="resetCalendarToToday" style="cursor: pointer;" :title="$t('studyManagement.resetToToday') || '오늘 날짜로 초기화'">{{ $t('studyManagement.title') }}</h1>
      </div>
      
      
      <!-- Calendar UI -->
      <div class="calendar-container">
        <div class="d-flex justify-content-between align-items-center mb-3">
          <div class="d-flex gap-2">
            <button class="action-btn action-btn-secondary" @click="prevYear" :title="$t('studyManagement.calendar.prevYear') || '이전 연도'">
              <i class="fas fa-angle-double-left"></i>
            </button>
            <button class="action-btn action-btn-secondary" @click="prevMonth" :title="$t('studyManagement.calendar.prevMonth') || '이전 월'">
              <i class="fas fa-chevron-left"></i>
            </button>
          </div>
          <div class="calendar-label">{{ $t('studyManagement.calendar.yearMonth', { year: calendarYear, month: currentMonthName }) }}</div>
          <div class="d-flex gap-2">
            <button class="action-btn action-btn-secondary" @click="nextMonth" :title="$t('studyManagement.calendar.nextMonth') || '다음 월'">
              <i class="fas fa-chevron-right"></i>
            </button>
            <button class="action-btn action-btn-secondary" @click="nextYear" :title="$t('studyManagement.calendar.nextYear') || '다음 연도'">
              <i class="fas fa-angle-double-right"></i>
            </button>
          </div>
        </div>
        <table class="calendar-table table table-bordered">
          <thead>
            <tr>
              <th v-for="day in weekDays" :key="day">{{ day }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(week, wIdx) in calendarGrid" :key="wIdx">
              <td 
                v-for="(date, dIdx) in week" 
                :key="dIdx" 
                :class="{ 
                  'text-muted': !date.isCurrentMonth, 
                  'bg-light': date.isToday,
                  'selected-date-start': selectedDateRange.startDate && date.isCurrentMonth && isSameDate(date.date, selectedDateRange.startDate),
                  'selected-date-end': selectedDateRange.endDate && date.isCurrentMonth && isSameDate(date.date, selectedDateRange.endDate),
                  'selected-date-range': isDateInRange(date.date, selectedDateRange.startDate, selectedDateRange.endDate)
                }"
                @click="selectDate(date)"
                style="cursor: pointer;"
              >
                <div class="calendar-date-label">{{ date.day }}</div>
                <div class="calendar-bars">
                  <template v-if="getStudyBarsForDate(date) && Array.isArray(getStudyBarsForDate(date))">
                    <div v-for="(bar, idx) in getStudyBarsForDate(date).slice(0, 3)" :key="bar.study.id" class="calendar-bar" :style="{ backgroundColor: bar.color, top: (idx * 8) + 13 + 'px' }" :title="getStudyTitle(bar.study)"></div>
                    <div v-if="getStudyBarsForDate(date) && getStudyBarsForDate(date).length > 3" class="calendar-bar-more" :style="{ top: (3 * 8) + 13 + 'px' }">
                      +{{ getStudyBarsForDate(date).length - 3 }}
                    </div>
                  </template>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <!-- 스터디 생성 폼 - 테이블 위에 표시 -->
      <div class="card-modern" v-if="showCreateForm">
        <div class="card-header-modern">
          <h3>{{ $t('studyManagement.createForm.title') }}</h3>
        </div>
        <form @submit.prevent="createStudy">
          <!-- 현재 언어로 입력 -->
                    <div class="form-group">
            <label class="form-label">{{ $t('studyManagement.createForm.titleLabel') }}</label>
            <input 
              v-model="newStudy[`title_${currentUserLanguage}`]" 
              type="text" 
              class="form-control" 
              :class="{ 'is-invalid': titleError }"
              @blur="checkTitleDuplicate"
              @input="clearTitleError"
              required
            >
            <div v-if="titleError" class="invalid-feedback">
              {{ titleError }}
            </div>
          </div>
          
          <div class="form-group">
                        <label class="form-label">{{ $t('studyManagement.createForm.goalLabel') }}</label>
            <textarea 
              v-model="newStudy[`goal_${currentUserLanguage}`]" 
              class="form-control" 
              rows="3" 
              required
            ></textarea>
          </div>
          

          
          <div class="row">
            <div class="col-md-6">
              <div class="form-group">
                <label class="form-label">{{ $t('studyManagement.createForm.startDateLabel') }}</label>
                <input v-model="newStudy.start_date" type="date" class="form-control">
              </div>
            </div>
            <div class="col-md-6">
              <div class="form-group">
                <label class="form-label">{{ $t('studyManagement.createForm.endDateLabel') }}</label>
                <input v-model="newStudy.end_date" type="date" class="form-control">
              </div>
            </div>
          </div>
          <div class="form-group">
            <div class="form-check">
              <input 
                v-model="newStudy.is_public" 
                type="checkbox" 
                class="form-check-input" 
                id="isPublic"
              >
              <label class="form-check-label" for="isPublic">
                {{ $t('studyManagement.createForm.publicStudy') }}
              </label>
            </div>
          </div>
          
          <!-- Tags Section -->
          <div class="form-group">
            <label class="form-label">
              {{ $t('studyDetail.tagManagement') || '태그 관리' }}
              <span class="text-danger">*</span>
            </label>
            <div class="d-flex align-items-center justify-content-end gap-2 flex-wrap">
              <!-- Selected Tags Display -->
              <div v-if="newStudyTags && newStudyTags.length > 0" class="d-flex align-items-center flex-wrap gap-2">
                <span 
                  v-for="tagId in newStudyTags" 
                  :key="tagId"
                  class="badge bg-primary"
                >
                  {{ getSelectedTagName(tagId) }}
                  <button 
                    @click="removeNewStudyTag(tagId)" 
                    class="btn-close btn-close-white ms-1" 
                    style="font-size: 0.7em;"
                  ></button>
                </span>
              </div>
              <button 
                @click="openNewStudyTagModal" 
                type="button"
                class="btn btn-outline-primary tag-filter-btn"
              >
                <i class="fas fa-tags"></i>
                {{ $t('tagFilterModal.title') || '태그로 검색' }}
                <span v-if="newStudyTags && newStudyTags.length > 0" class="badge bg-primary ms-2">{{ newStudyTags.length }}</span>
              </button>
            </div>
          </div>
          
          <div class="d-flex gap-3 justify-content-end">
            <button 
              type="submit" 
              class="action-btn action-btn-primary"
              :disabled="!newStudyTags || newStudyTags.length === 0"
              :title="(!newStudyTags || newStudyTags.length === 0) ? ($t('studyManagement.createForm.tagRequired') || '태그를 선택해주세요.') : ''"
            >
              <i class="fas fa-save"></i>
              <span class="action-label">{{ $t('studyManagement.createForm.create') }}</span>
            </button>
            <button type="button" @click="cancelCreate" class="action-btn action-btn-secondary">
              <i class="fas fa-times"></i>
              <span class="action-label">{{ $t('studyManagement.createForm.cancel') }}</span>
            </button>
          </div>
        </form>
      </div>
      
      <!-- 필터 컨트롤 -->
      <div class="filter-controls">
        <div class="row align-items-end">
          <div class="col-md-3">
            <label class="form-label">{{ $t('studyManagement.filter.studyType') }}</label>
            <select v-model="studyTypeFilter" class="form-control" @change="clearDateRange">
              <option value="my" v-if="isAuthenticated">{{ $t('studyManagement.filter.myStudies') }}</option>
              <option value="public">{{ $t('studyManagement.filter.publicStudies') }}</option>
              <option value="all" v-if="isAdmin">{{ $t('studyManagement.filter.allStudies') }}</option>
            </select>
          </div>
          <div class="col-md-3" v-if="isAdmin && studyTypeFilter !== 'public'">
            <label class="form-label">{{ $t('studyManagement.filter.visibility') }}</label>
            <select v-model="publicFilter" class="form-control">
              <option value="">{{ $t('studyManagement.filter.all') }}</option>
              <option value="true">{{ $t('studyManagement.filter.public') }}</option>
              <option value="false">{{ $t('studyManagement.filter.private') }}</option>
            </select>
          </div>
          <div class="col-md-6 d-flex justify-content-end align-items-center gap-2">
            <!-- Selected Date Range Filter Display -->
            <div v-if="selectedDateRange.startDate || selectedDateRange.endDate" class="d-flex align-items-center gap-2 date-range-filter">
              <span class="badge bg-info date-range-badge">
                <i class="fas fa-calendar date-range-icon"></i>
                <span class="date-range-text">
                  <span v-if="selectedDateRange.startDate && selectedDateRange.endDate">
                    <span class="date-start">{{ formatShortDate(selectedDateRange.startDate.toISOString()) }}</span>
                    <span class="date-separator"> ~ </span>
                    <span class="date-end">{{ formatShortDate(selectedDateRange.endDate.toISOString()) }}</span>
                  </span>
                  <span v-else-if="selectedDateRange.startDate">
                    <span class="date-start">{{ formatShortDate(selectedDateRange.startDate.toISOString()) }}</span>
                    <span class="date-separator"> ~</span>
                  </span>
                  <span v-else-if="selectedDateRange.endDate">
                    <span class="date-separator">~ </span>
                    <span class="date-end">{{ formatShortDate(selectedDateRange.endDate.toISOString()) }}</span>
                  </span>
                </span>
              </span>
              <button 
                @click="clearDateRange" 
                class="btn btn-sm btn-outline-secondary date-range-clear-btn"
                :title="$t('studyManagement.filter.clearDateFilter') || '날짜 범위 필터 해제'"
              >
                <i class="fas fa-times"></i>
              </button>
            </div>
            <!-- Tag Filter Button -->
            <button 
              @click="openTagFilterModal" 
              class="btn btn-outline-primary tag-filter-btn"
            >
              <i class="fas fa-tags"></i>
              {{ $t('examManagement.tagFilter') || 'Tag Filter' }}
              <span v-if="selectedTags && selectedTags.length > 0" class="badge bg-primary ms-2">{{ selectedTags.length }}</span>
            </button>
            
            <button 
              @click="handleCreateStudy" 
              class="action-btn action-btn-success"
              v-if="!showCreateForm"
            >
              <i class="fas fa-plus"></i>
              <span class="action-label">{{ $t('studyManagement.createStudy') }}</span>
            </button>
            <button 
              @click="deleteSelected" 
              class="action-btn action-btn-danger" 
              :disabled="!selectedStudies || selectedStudies.length === 0" 
              v-if="isAdmin && selectedStudies && selectedStudies.length > 0"
            >
              <i class="fas fa-trash"></i>
              <span class="action-label">{{ $t('studyManagement.delete') || 'Delete' }}</span>
            </button>
          </div>
        </div>
      </div>
      
      <!-- 스터디 목록 테이블 -->
      <div v-if="!loading" class="table-responsive">
        <table v-if="sortedStudies && sortedStudies.length > 0" class="table desktop-table">
          <thead>
            <tr>
              <th v-if="isAdmin" style="width: 21px; flex-shrink: 0;">
                <input type="checkbox" @change="toggleSelectAll" :checked="isAllSelected" :indeterminate="isIndeterminate">
              </th>
              <th @click="setSort('title')" style="cursor:pointer">
                {{ $t('studyManagement.table.title') }}
                <i :class="getSortIcon('title')" class="ms-1"></i>
              </th>
              <th @click="setSort('start_date')" style="cursor:pointer">
                {{ $t('studyManagement.table.period') }}
                <i :class="getSortIcon('start_date')" class="ms-1"></i>
              </th>
              <th v-if="isAuthenticated" @click="setSort('overall_progress')" style="cursor:pointer">
                {{ $t('studyManagement.table.progress') }}
                <i :class="getSortIcon('overall_progress')" class="ms-1"></i>
              </th>
              <th>{{ $t('studyManagement.table.publicStatus') }}</th>
              <th v-if="isAuthenticated">{{ $t('studyManagement.table.actions') }}</th>
              <th v-if="!isAdmin && studyTypeFilter === 'public'">{{ $t('studyManagement.table.joinRequest') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="study in sortedStudies" :key="study.id">
              <td v-if="isAdmin">
                <input 
                  type="checkbox" 
                  :checked="isStudySelected(String(study.id))" 
                  @change="toggleStudySelection(String(study.id), $event)"
                >
              </td>
              <td>
                <span class="study-color-bullet" :style="{ backgroundColor: getStudyColor(study.id) }"></span>
                <router-link :to="`/study-detail/${study.id}`" class="study-title-link">
                  {{ getStudyTitle(study) }}
                </router-link>
              </td>
              <td>
                {{ formatDate(study.start_date) }}
                <span v-if="study.end_date && !isMaxDate(study.end_date)"> ~ {{ formatDate(study.end_date) }}</span>
                <span v-else> ~</span>
              </td>
              <td v-if="isAuthenticated">
                <router-link 
                  :to="`/study-progress-dashboard/${study.id}`" 
                  class="progress-link"
                  @click="recordProgress(study.id)"
                >
                  {{ (typeof study.overall_progress === 'number' ? study.overall_progress : 0).toFixed(1) }}%
                </router-link>
              </td>
              <td>
                <span class="badge" :class="study.is_public ? 'bg-success' : 'bg-secondary'">
                  {{ study.is_public ? $t('studyManagement.table.public') : $t('studyManagement.table.private') }}
                </span>
              </td>
              <td v-if="isAuthenticated">
                <button v-if="canDeleteStudy(study)" @click="deleteStudy(study.id)" class="btn btn-sm btn-outline-danger">{{ $t('studyManagement.table.delete') }}</button>
              </td>
              <td v-if="!isAdmin && studyTypeFilter === 'public'">
                <button 
                  v-if="!isStudyMember(study) && !hasJoinRequest(study)" 
                  @click="requestJoinStudy(study)" 
                  class="btn btn-sm btn-outline-primary"
                >
                  {{ $t('studyManagement.table.joinRequest') }}
                </button>
                <button 
                  v-else-if="!isStudyMember(study) && hasJoinRequest(study)" 
                  @click="cancelJoinRequest(study)" 
                  class="btn btn-sm btn-outline-warning"
                >
                  {{ $t('studyManagement.table.cancelRequest') }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        
        <!-- 모바일용 스터디 카드 -->
        <div class="mobile-study-cards">
          <div v-for="study in (sortedStudies || []).slice(0, 7)" :key="study.id" class="mobile-study-card">
            <div class="mobile-study-card-header">
              <div class="mobile-study-title-section">
                <input 
                  v-if="isAdmin"
                  type="checkbox" 
                  :checked="isStudySelected(String(study.id))" 
                  @change="toggleStudySelection(String(study.id), $event)"
                  style="margin-right: 8px;"
                >
                <span class="mobile-study-color-bullet" :style="{ backgroundColor: getStudyColor(study.id) }"></span>
                <router-link :to="`/study-detail/${study.id}`" class="mobile-study-title-link">
                  <h3 class="mobile-study-title">{{ getStudyTitle(study) }}</h3>
                </router-link>
                <!-- Join 버튼을 제목 옆으로 이동 -->
                <button 
                  v-if="!isAdmin && studyTypeFilter === 'public' && !isStudyMember(study) && !hasJoinRequest(study)" 
                  @click="requestJoinStudy(study)" 
                  class="mobile-study-btn join mobile-join-btn"
                >
                  <i class="fas fa-user-plus"></i>
                  <span class="mobile-join-btn-text">{{ $t('studyManagement.table.joinRequest') }}</span>
                </button>
                <button 
                  v-if="!isAdmin && studyTypeFilter === 'public' && !isStudyMember(study) && hasJoinRequest(study)" 
                  @click="cancelJoinRequest(study)" 
                  class="mobile-study-btn cancel mobile-join-btn"
                >
                  <i class="fas fa-times"></i>
                  <span class="mobile-join-btn-text">{{ $t('studyManagement.table.cancelRequest') }}</span>
                </button>
              </div>
            </div>
            
            <div class="mobile-study-info">
              <div class="mobile-study-date-progress">
                <p class="mobile-study-date">
                  {{ formatDate(study.start_date) }}
                  <span v-if="study.end_date && !isMaxDate(study.end_date)"> ~ {{ formatDate(study.end_date) }}</span>
                  <span v-else> ~</span>
                </p>
                <div class="mobile-study-progress" v-if="isAuthenticated">
                  {{ (typeof study.overall_progress === 'number' ? study.overall_progress : 0).toFixed(1) }}%
                </div>
              </div>
              <div class="mobile-study-status" v-if="isAdmin">
                <span class="mobile-study-badge" :class="study.is_public ? 'public' : 'private'">
                  {{ study.is_public ? $t('studyManagement.table.public') : $t('studyManagement.table.private') }}
                </span>
              </div>
            </div>
            
            <div class="mobile-study-actions">
              <router-link 
                v-if="isAuthenticated"
                :to="`/study-progress-dashboard/${study.id}`" 
                class="mobile-study-btn progress"
                @click="recordProgress(study.id)"
              >
                <i class="fas fa-chart-line"></i>
                <span>{{ $t('studyManagement.table.progress') }}</span>
              </router-link>
              <button 
                v-if="isAuthenticated && canDeleteStudy(study)" 
                @click="deleteStudy(study.id)" 
                class="mobile-study-btn delete"
              >
                <i class="fas fa-trash"></i>
                <span>{{ $t('studyManagement.table.delete') }}</span>
              </button>
            </div>
          </div>
        </div>
        
        <div v-if="!sortedStudies || sortedStudies.length === 0" class="alert alert-info">
          {{ isAdmin ? $t('studyManagement.noStudies.admin') : $t('studyManagement.noStudies.user') }}
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
              {{ $t('studyManagement.pagination.info', { 
                current: currentPage, 
                total: totalPages, 
                count: totalCount 
              }) || `페이지 ${currentPage} / ${totalPages} (총 ${totalCount}개 스터디)` }}
            </small>
          </div>
        </div>
      </div>
      
      <!-- 로딩 중 -->
      <div v-if="loading" class="loading-container">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">{{ $t('studyManagement.loading') }}</span>
        </div>
        <p class="mt-3">{{ $t('studyManagement.loadingText') }}</p>
      </div>
    </div>
    
    <!-- 토스트 알림 -->
    <div v-if="showToast" class="toast-notification" :class="toastType">
      <div class="toast-content">
        <i :class="toastIcon"></i>
        <span>{{ toastMessage }}</span>
      </div>
      <button @click="hideToast" class="toast-close">
        <i class="fas fa-times"></i>
      </button>
    </div>

    <!-- 모달 -->
    <div v-if="showModal" class="modal-overlay" @click="hideModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">
            <i :class="modalIcon"></i>
            {{ modalTitle }}
          </h3>
          <button @click="hideModal" class="modal-close">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <div v-if="modalType === 'join-request'">
            <p>{{ $t('studyManagement.messages.enterJoinMessage') }}</p>
            <input v-model="joinRequestInput" type="text" class="form-control mt-2" :placeholder="$t('studyManagement.messages.enterJoinMessage')">
          </div>
          <p v-else>{{ modalMessage }}</p>
        </div>
        <div class="modal-footer">
          <button @click="cancelModal" class="action-btn action-btn-secondary">
            <i class="fas fa-times"></i>
            <span>{{ modalCancelText }}</span>
          </button>
          <button @click="confirmModal" :class="['action-btn', modalConfirmButtonClass]">
            <i class="fas fa-trash"></i>
            <span>{{ modalConfirmText }}</span>
          </button>
        </div>
      </div>
    </div>
    
    <!-- Tag Filter Modal -->
    <TagFilterModal
      :show="showTagFilterModal"
      :selectedTags="selectedTags"
      @update:show="showTagFilterModal = $event"
      @update:selectedTags="handleSelectedTagsUpdate"
      @apply="handleTagFilterApply"
      @error="handleTagError"
      @tag-created="handleTagCreated"
    />
    
    <!-- New Study Tag Modal -->
    <TagFilterModal
      :show="showNewStudyTagModal"
      :selectedTags="newStudyTags"
      @update:show="showNewStudyTagModal = $event"
      @update:selectedTags="handleNewStudyTagUpdate"
      @apply="handleNewStudyTagApply"
      @error="handleTagError"
      @tag-created="handleTagCreated"
    />
  </div>
</template>

<script>
// TODO: console.log를 debugLog로 변경할 수 있는지 반드시 검토해야 함
// - 운영 환경에서 브라우저 콘솔에 로그가 보이면 안 됨
// - debugLog는 운영 환경에서 자동으로 비활성화됨
import axios from 'axios'
import { debugLog, forceDebugLog } from '@/utils/debugUtils'
import { getLocalizedContentWithI18n, SUPPORTED_LANGUAGES } from '@/utils/multilingualUtils'
import {
  isAdmin,
  getCurrentUser as getCurrentUserFromPermissions,
  isAuthenticated as isAuthenticatedUser
} from '@/utils/permissionUtils'
import { isCacheEnabled, setSessionCache, removeSessionCache, removeLocalCache } from '@/utils/cacheUtils'
import TagFilterModal from '@/components/TagFilterModal.vue'
import { 
  getCurrentDomainTagInfo,
  getCurrentDomainConfig,
  getForcedTags
} from '@/utils/domainUtils'

function getRandomColor(seed) {
  // Deterministic color for a given seed (study id)
  const colors = [
    '#42a5f5', '#66bb6a', '#ffa726', '#ab47bc', '#ef5350', '#26a69a', '#8d6e63', '#d4e157', '#5c6bc0', '#ec407a',
    '#bdbdbd', '#ff7043', '#26c6da', '#7e57c2', '#789262', '#fbc02d', '#8d8d8d', '#00bcd4', '#cddc39', '#ffb300'
  ];
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = seed.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}

/**
 * 스터디 관리 컴포넌트
 * 
 * 캐시 정리 정책:
 * 1. 스터디 생성/삭제/수정 시: clearCache() 호출로 관련 캐시 정리
 * 2. 멤버 추가/삭제 시: clearStudyCache() 호출로 스터디 관련 캐시 정리
 * 3. 강제 새로고침 시: emergencyCacheCleanup() 호출로 긴급 캐시 정리
 * 4. 브라우저 캐시: clearBrowserCache() 호출로 localStorage/sessionStorage 정리
 */
export default {
  name: 'StudyManagement',
  components: {
    TagFilterModal
  },
  data() {
    const today = new Date();
    return {
      userProfileLanguage: null, // 사용자 프로필 언어 캐시
      studies: [],
      loading: true, // 로딩 상태 추가
      // 페이지네이션
      currentPage: 1,
      pageSize: 20,
      totalCount: 0,
      totalPages: 0,
      showCreateForm: false,
      selectedTags: [], // 선택된 태그들 (필터링용)
      showTagFilterModal: false, // 태그 필터 모달 표시 상태
      newStudyTags: [], // 새 스터디 생성 시 선택된 태그들
      showNewStudyTagModal: false, // 새 스터디 태그 모달 표시 상태
      availableTags: [], // 사용 가능한 태그 목록
      sortKey: 'default', // 정렬 키 (기본값: 'default'로 설정하여 자동 정렬 적용)
      sortOrder: 'asc',
      newStudy: {
        title_ko: '',
        title_en: '',
        goal_ko: '',
        goal_en: '',
        start_date: today.toISOString().split('T')[0],
        end_date: '',
        is_public: true
      },
      titleError: '', // 제목 중복 에러 메시지
      // Calendar state
      calendarYear: today.getFullYear(),
      calendarMonth: today.getMonth(), // 0-indexed
      selectedDateRange: { startDate: null, endDate: null }, // 선택된 날짜 범위 (필터링용)
      dateSelectionMode: 'start', // 'start' 또는 'end'
      publicFilter: '', // 공개/비공개 필터
              studyTypeFilter: 'my', // 스터디 타입 필터 (my, public, all)
        joinRequests: {}, // 스터디별 가입 요청 상태 저장
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
        modalConfirmButtonClass: 'btn-primary',
        modalIcon: 'fas fa-question-circle',
        modalCallback: null,
        modalType: '', // 모달 타입 추가
        joinRequestInput: '', // 가입 요청 입력 필드
        isAutoSwitchingToPublic: false, // 자동 전환 플래그 추가
        selectedStudies: [], // 일괄 삭제를 위한 배열

    }
  },
  computed: {
    weekDays() {
      return this.$t('studyManagement.calendar.weekDays').split(',');
    },
    currentMonthName() {
      // 사용자 언어에 따라 월 이름 반환 (i18n 사용)
      const userLang = this.$i18n?.locale || 'en'
      const monthNames = {
        'ko': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'],
        'en': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
        'es': ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'],
        'zh': ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月'],
        'ja': ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
      }
      // 사용자 언어가 있으면 사용, 없으면 영어 기본값
      return (monthNames[userLang] || monthNames['en'])[this.calendarMonth]
    },
    currentUserLanguage() {
      return this.$i18n.locale
    },


    filteredStudies() {
      // 태그 필터링이 적용된 경우 백엔드에서 이미 필터링된 결과를 그대로 사용
      if (this.selectedTags && Array.isArray(this.selectedTags) && this.selectedTags.length > 0) {
        console.log('🏷️ 태그 필터링이 적용되어 백엔드 결과를 그대로 사용')
        console.log('📊 현재 studies 개수:', this.studies ? this.studies.length : 0)
        console.log('📊 studies 데이터:', this.studies)
        return this.studies || []
      }
      
      // 익명 사용자 처리
      const user = getCurrentUserFromPermissions()
      
      let filtered = this.studies || []
      
      console.log('🔍 filteredStudies 디버깅:', {
        totalStudies: this.studies?.length || 0,
        user: user ? { id: user.id, role: user.role } : 'anonymous',
        studyTypeFilter: this.studyTypeFilter,
        publicFilter: this.publicFilter
      })
      
      // Study 멤버 정보 디버깅
      if (this.studies && this.studies.length > 0) {
        this.studies.forEach((study, index) => {
          console.log(`🔍 Study ${index + 1} 멤버 정보:`, {
            id: study.id,
            title: getLocalizedContentWithI18n(study, 'title', this.$i18n, this.userProfileLanguage, ''),
            members: study.members,
            created_by: study.created_by
          })
        })
      }
      
      if (!user) {
        // 익명 사용자는 공개 스터디만 볼 수 있음
        if (this.studyTypeFilter === 'my') {
          // 로그인하지 않은 사용자는 "My study"에서 빈 목록 표시
          filtered = []
        } else if (this.studyTypeFilter === 'public') {
          // 공개 스터디만 표시
          filtered = filtered.filter(study => study.is_public === true)
        } else {
          // 기본적으로 공개 스터디만 표시
          filtered = filtered.filter(study => study.is_public === true)
        }
      } else if (user.role === 'admin_role') {
        // 관리자는 스터디 타입 필터에 따라 필터링
        if (this.studyTypeFilter === 'my') {
          // 내 스터디: 사용자가 멤버인 스터디 또는 사용자가 만든 스터디
          filtered = filtered.filter(study => {
            // 멤버 체크: 타입 변환하여 비교
            const isMember = Array.isArray(study.members) &&
              study.members.some(member => {
                if (!member.user || !member.is_active) return false
                const memberUserId = typeof member.user === 'object' ? member.user.id : member.user
                // 타입 변환하여 비교 (문자열/숫자 모두 처리)
                return String(memberUserId) === String(user.id)
              })
            
            // 생성자 체크: 타입 변환하여 비교
            const isCreator = study.created_by && (
              (typeof study.created_by === 'object' && String(study.created_by.id) === String(user.id)) ||
              String(study.created_by) === String(user.id)
            )
            
            return isMember || isCreator
          })
        } else if (this.studyTypeFilter === 'public') {
          // 공개 스터디: 모든 공개 스터디
          filtered = filtered.filter(study => study.is_public === true)
        } else if (this.studyTypeFilter === 'all') {
          // 모든 스터디: 추가 필터 적용
          if (this.publicFilter === 'true') {
            filtered = filtered.filter(study => study.is_public === true)
          } else if (this.publicFilter === 'false') {
            filtered = filtered.filter(study => study.is_public === false)
          }
        }
      } else {
        // 일반 사용자는 스터디 타입 필터에 따라 필터링
        if (this.studyTypeFilter === 'my') {
          // 내 스터디: 사용자가 멤버인 스터디 또는 사용자가 만든 스터디
          filtered = filtered.filter(study => {
            // 멤버 체크: 타입 변환하여 비교
            const isMember = Array.isArray(study.members) &&
              study.members.some(member => {
                if (!member.user || !member.is_active) return false
                const memberUserId = typeof member.user === 'object' ? member.user.id : member.user
                // 타입 변환하여 비교 (문자열/숫자 모두 처리)
                return String(memberUserId) === String(user.id)
              })
            
            // 생성자 체크: 타입 변환하여 비교
            const isCreator = study.created_by && (
              (typeof study.created_by === 'object' && String(study.created_by.id) === String(user.id)) ||
              String(study.created_by) === String(user.id)
            )
            
            return isMember || isCreator
          })
        } else if (this.studyTypeFilter === 'public') {
          // 공개 스터디: 모든 공개 스터디
          filtered = filtered.filter(study => study.is_public === true)
        }
      }
      
      // 날짜 범위 필터링 적용
      if (this.selectedDateRange.startDate || this.selectedDateRange.endDate) {
        filtered = filtered.filter(study => {
          if (!study.start_date) return false
          
          const studyStart = new Date(study.start_date)
          // end_date가 null이면 무한 기간으로 간주 (미래로 확장)
          const studyEnd = study.end_date ? new Date(study.end_date) : null
          
          // 날짜 비교를 위해 시간 부분 제거
          studyStart.setHours(0, 0, 0, 0)
          if (studyEnd) studyEnd.setHours(0, 0, 0, 0)
          
          const rangeStart = this.selectedDateRange.startDate ? new Date(this.selectedDateRange.startDate) : null
          const rangeEnd = this.selectedDateRange.endDate ? new Date(this.selectedDateRange.endDate) : null
          
          if (rangeStart) rangeStart.setHours(0, 0, 0, 0)
          if (rangeEnd) rangeEnd.setHours(0, 0, 0, 0)
          
          // 스터디 기간과 선택된 범위가 겹치는지 확인
          // 겹치는 경우: (studyStart <= rangeEnd) && (studyEnd >= rangeStart)
          if (rangeStart && rangeEnd) {
            // 시작일과 종료일이 모두 있으면 범위 내에 겹치는 스터디
            if (studyEnd) {
              return studyStart <= rangeEnd && studyEnd >= rangeStart
            } else {
              // end_date가 null이면 무한 기간이므로 시작일이 범위 종료일 이전이면 포함
              return studyStart <= rangeEnd
            }
          } else if (rangeStart) {
            // 시작일만 있으면 스터디가 시작일 이후에 시작하거나, 시작일을 포함하는 기간인 경우
            if (studyEnd) {
              // 스터디 시작일이 필터 시작일 이후이거나, 스터디 기간이 필터 시작일을 포함하는 경우
              return studyStart >= rangeStart || (studyStart <= rangeStart && studyEnd >= rangeStart)
            } else {
              // end_date가 null이면 무한 기간이므로 시작일이 필터 시작일 이전이면 포함
              return studyStart <= rangeStart
            }
          } else if (rangeEnd) {
            // 종료일만 있으면 스터디 기간이 종료일과 겹치는지 확인
            if (studyEnd) {
              // 스터디가 종료일 이전에 시작하고 종료일을 포함하는 기간인 경우
              return studyStart <= rangeEnd && studyEnd >= rangeEnd
            } else {
              // end_date가 null이면 무한 기간이므로 항상 포함
              return true
            }
          }
          return false
        })
      }
      
      console.log('🔍 filteredStudies 결과:', {
        filteredCount: filtered.length,
        selectedDateRange: this.selectedDateRange,
        studies: filtered.map(s => ({ id: s.id, title: getLocalizedContentWithI18n(s, 'title', this.$i18n, this.userProfileLanguage, ''), is_public: s.is_public }))
      })
      
      return filtered
    },
    visiblePages() {
      // 현재 페이지 주변의 페이지 번호들을 계산
      const pages = []
      const maxVisible = 5
      const totalPages = this.totalPages || 1
      const currentPage = this.currentPage || 1
      let start = Math.max(1, currentPage - Math.floor(maxVisible / 2))
      let end = Math.min(totalPages, start + maxVisible - 1)
      
      // 끝에서 시작점 조정
      if (end - start < maxVisible - 1) {
        start = Math.max(1, end - maxVisible + 1)
      }
      
      for (let i = start; i <= end; i++) {
        pages.push(i)
      }
      
      return pages
    },
    sortedStudies() {
      const filtered = this.filteredStudies
      if (!filtered || !Array.isArray(filtered)) {
        return []
      }
      const studies = [...filtered]
      return studies.sort((a, b) => {
        // 사용자가 정렬 컬럼을 클릭한 경우 해당 정렬 적용
        if (this.sortKey && this.sortKey !== 'default') {
          let aValue, bValue
          
          switch (this.sortKey) {
            case 'title':
              aValue = this.getStudyTitle(a) || ''
              bValue = this.getStudyTitle(b) || ''
              break
            case 'start_date':
              aValue = a.start_date || ''
              bValue = b.start_date || ''
              break
            case 'overall_progress':
              aValue = typeof a.overall_progress === 'number' ? a.overall_progress : 0
              bValue = typeof b.overall_progress === 'number' ? b.overall_progress : 0
              break
            default:
              return 0
          }
          
          if (this.sortOrder === 'asc') {
            return aValue < bValue ? -1 : aValue > bValue ? 1 : 0
          } else {
            return aValue > bValue ? -1 : aValue < bValue ? 1 : 0
          }
        }
        
        // 기본 정렬: 최근 시작된 스터디를 위쪽에, 만료된 스터디를 아래쪽에
        // 1순위: 최근 시작된 스터디를 위쪽에 (start_date 기준 내림차순)
        const aStartDate = new Date(a.start_date || 0)
        const bStartDate = new Date(b.start_date || 0)
        
        if (aStartDate > bStartDate) return -1
        if (aStartDate < bStartDate) return 1
        
        // 2순위: 시작일이 같은 경우, 만료되지 않은 스터디를 위쪽에
        const aEndDate = new Date(a.end_date || 0)
        const bEndDate = new Date(b.end_date || 0)
        const today = new Date()
        
        const aIsExpired = aEndDate > 0 && aEndDate < today
        const bIsExpired = bEndDate > 0 && bEndDate < today
        
        if (!aIsExpired && bIsExpired) return -1
        if (aIsExpired && !bIsExpired) return 1
        
        // 3순위: 제목 알파벳 순
        return this.getStudyTitle(a).localeCompare(this.getStudyTitle(b))
      })
    },
    calendarGrid() {
      // Returns a 2D array for the calendar (weeks x days)
      const year = this.calendarYear;
      const month = this.calendarMonth;
      const firstDay = new Date(year, month, 1);
      const lastDay = new Date(year, month + 1, 0);
      const prevLastDay = new Date(year, month, 0);
      const today = new Date();
      let grid = [];
      let week = [];
      // Fill leading days from previous month
      for (let i = 0; i < firstDay.getDay(); i++) {
        week.push({
          day: prevLastDay.getDate() - firstDay.getDay() + i + 1,
          isCurrentMonth: false,
          isToday: false,
          date: new Date(year, month - 1, prevLastDay.getDate() - firstDay.getDay() + i + 1)
        });
      }
      // Fill current month days
      for (let d = 1; d <= lastDay.getDate(); d++) {
        const isToday = year === today.getFullYear() && month === today.getMonth() && d === today.getDate();
        week.push({
          day: d,
          isCurrentMonth: true,
          isToday,
          date: new Date(year, month, d)
        });
        if (week.length === 7) {
          grid.push(week);
          week = [];
        }
      }
      // Fill trailing days from next month
      let nextDay = 1;
      while (week.length > 0 && week.length < 7) {
        week.push({
          day: nextDay++,
          isCurrentMonth: false,
          isToday: false,
          date: new Date(year, month + 1, nextDay - 1)
        });
      }
      if (week.length) grid.push(week);
      return grid;
    },
    isAdmin() {
      return isAdmin()
    },

    isAuthenticated() {
      return isAuthenticatedUser()
    },
    currentUser() {
      return getCurrentUserFromPermissions()
    },
    isAllSelected() {
      if (!this.isAdmin || !this.sortedStudies || this.sortedStudies.length === 0) {
        return false
      }
      return this.sortedStudies.length > 0 && this.selectedStudies.length === this.sortedStudies.length
    },
    isIndeterminate() {
      if (!this.isAdmin || !this.sortedStudies || this.sortedStudies.length === 0) {
        return false
      }
      return this.selectedStudies.length > 0 && this.selectedStudies.length < this.sortedStudies.length
    }
  },
  watch: {
    publicFilter() {
      // 필터 변경 시 첫 페이지로 이동
      this.currentPage = 1
      this.loadStudies()
    },
    async studyTypeFilter(newValue) {
      console.log('🔄 studyTypeFilter watch 호출됨:', newValue, 'isAuthenticated:', this.isAuthenticated)
      // 필터 변경 시 첫 페이지로 이동
      this.currentPage = 1
      
      if (newValue === 'my') {
        // My Studies로 변경할 때는 태그 필터를 초기화하여 태그가 없는 스터디도 보여줌
        console.log('📋 My Studies로 변경됨, 태그 필터 초기화')
        this.selectedTags = []
      } else if (newValue === 'public') {
        if (this.isAuthenticated) {
          // Public Studies로 변경되고 로그인된 사용자인 경우 관심 카테고리 태그 자동 설정
          // 태그 설정 후 loadStudies가 호출되므로 태그 필터가 적용됨
          console.log('📋 Public Studies로 변경됨, 관심 카테고리 태그 설정 시작')
          await this.setupInterestedCategoryTags()
          console.log('✅ setupInterestedCategoryTags 완료, selectedTags:', this.selectedTags)
        } else {
          // 로그인하지 않은 사용자는 태그 필터를 적용하지 않음
          console.log('📋 Public Studies로 변경됨 (비로그인), 태그 필터 초기화')
          this.selectedTags = []
        }
      }
      
      // loadStudies는 setupInterestedCategoryTags 후에 호출되어 태그 필터가 적용된 상태로 로드됨
      this.loadStudies()
    },
    selectedTags() {
      // 태그 필터 변경 시 첫 페이지로 이동
      this.currentPage = 1
    }
  },
        async mounted() {
    // 로그인하지 않은 사용자의 경우 기본 필터를 "public"으로 설정
    if (!this.isAuthenticated) {
      this.studyTypeFilter = 'public'
    }
    
    // 태그 목록 로드 (도메인별 태그 설정 전에 먼저 로드)
    await this.loadAvailableTags();
    
    // 현재 도메인의 기본 태그 설정 확인 (범용) - 태그 목록 로드 후 실행
    await this.setupCurrentDomainDefaultTagsIfNeeded()
    
    // 전역 캐시 설정 확인
    const cacheEnabled = localStorage.getItem('cacheEnabled') !== 'false'
    const cacheDisabled = sessionStorage.getItem('cacheDisabled') === 'true'
    
    // URL 파라미터에서 강제 새로고침 확인
    const forceRefresh = this.$route.query.refresh === 'true'
    
    // localStorage에서 강제 새로고침 플래그 확인
    const forceRefreshFlag = localStorage.getItem('forceRefresh')
    
    // 사용자 프로필 언어 초기화 (loadStudies 전에 호출하여 캐시에 저장)
    // loadStudies 내부에서도 getUserProfileLanguage를 호출하지만, 이미 호출되었으므로 캐시 사용
    await this.getUserProfileLanguage()
    
    // 독립적인 작업들을 병렬로 처리
    const independentPromises = []
    
    // 사용자 관심 카테고리 기반 기본 태그 설정 (public 필터일 때만, 독립적)
    if (this.isAuthenticated && this.studyTypeFilter === 'public') {
      independentPromises.push(this.setupInterestedCategoryTags())
    }
    
    // 가입 요청 상태 로드 (mounted에서만 한 번 수행, 독립적)
    if (this.isAuthenticated) {
      independentPromises.push(this.loadJoinRequestStatus())
    }
    
    // 독립적인 작업들을 병렬로 실행 (loadStudies와 병렬 처리 가능)
    await Promise.allSettled(independentPromises)
    
    if (!cacheEnabled || cacheDisabled || forceRefresh || forceRefreshFlag) {
      if (forceRefreshFlag) {
        localStorage.removeItem('forceRefresh') // 플래그 제거
        debugLog('강제 새로고침 플래그 감지됨, 캐시 무효화')
      }
      debugLog('캐시가 비활성화되어 있거나 강제 새로고침이 요청되었습니다. 새 데이터를 로드합니다.')
      // loadStudies는 getUserProfileLanguage를 내부에서 await하지만, 이미 호출되었으므로 캐시 사용
      await this.loadStudies()
      // recordAllStudyProgress는 loadStudies 후에 실행되어야 함 (종속)
      await this.recordAllStudyProgress()
      return
    }
    
    // 캐시된 데이터 확인 (스터디 탈퇴 후 새로고침을 위해 강제로 새 데이터 로드)
    const cachedData = this.getCachedData()
    // eslint-disable-next-line no-constant-condition
    if (cachedData && false) {
      debugLog('캐시된 스터디 데이터 사용')
      this.studies = cachedData.studies || []
      // 로그인하지 않은 사용자는 항상 "public" 필터 사용
      if (!this.isAuthenticated) {
        this.studyTypeFilter = 'public'
      } else {
        this.studyTypeFilter = cachedData.studyTypeFilter || 'my'
      }
      this.publicFilter = cachedData.publicFilter || ''
      this.loading = false  // 캐시 사용 시 로딩 상태 해제
    } else {
      debugLog('새로운 스터디 데이터 로드')
      // loadStudies는 getUserProfileLanguage를 내부에서 await하지만, 이미 호출되었으므로 캐시 사용
      await this.loadStudies()
      this.cacheData()
    }
    
    // 페이지 로드 시 모든 스터디의 진행율 기록 (loadStudies 후에 실행되어야 함, 종속)
    await this.recordAllStudyProgress()
  },
  methods: {
    // 사용자 프로필 언어 가져오기 (캐시 사용)
    async getUserProfileLanguage() {
      // 캐시된 언어가 있으면 사용
      if (this.userProfileLanguage) {
        forceDebugLog(`✅ [StudyManagement] getUserProfileLanguage - 캐시된 언어 사용: ${this.userProfileLanguage}`)
        return this.userProfileLanguage
      }
      
      try {
        if (this.isAuthenticated) {
          const response = await axios.get('/api/user-profile/')
          const language = response.data.language || 'en'
          // 캐시에 저장 (중요: this.userProfileLanguage에 저장)
          this.userProfileLanguage = language
          forceDebugLog(`✅ [StudyManagement] getUserProfileLanguage - API에서 언어 가져옴: ${language}`)
          forceDebugLog(`  - API 응답 전체:`, response.data)
          return language
        }
        this.userProfileLanguage = 'en'
        forceDebugLog(`⚠️ [StudyManagement] getUserProfileLanguage - 비로그인 사용자, 기본값 'en' 사용`)
        return 'en' // 기본값
      } catch (error) {
        console.error('사용자 프로필 언어 가져오기 실패:', error)
        this.userProfileLanguage = 'en'
        forceDebugLog(`❌ [StudyManagement] getUserProfileLanguage - 에러 발생, 기본값 'en' 사용:`, error)
        return 'en' // 기본값
      }
    },
    // 현재 사용자 언어에 맞는 스터디 제목 반환 (사용자 프로필 언어 기준)
    getStudyTitle(study) {
      // 디버깅: study 객체 전체 확인
      forceDebugLog(`🔍 [StudyManagement] getStudyTitle 호출 - study.id: ${study.id}`)
      forceDebugLog(`  - study.display_title: "${study.display_title}" (type: ${typeof study.display_title})`)
      forceDebugLog(`  - study.title_zh: "${study.title_zh}"`)
      forceDebugLog(`  - study.title_en: "${study.title_en}"`)
      forceDebugLog(`  - study.title_ko: "${study.title_ko}"`)
      forceDebugLog(`  - this.userProfileLanguage: "${this.userProfileLanguage}"`)
      
      // 사용자 프로필 언어 가져오기 (동기적으로, 캐시 우선)
      let userLang = this.userProfileLanguage
      
      // userProfileLanguage가 없으면 동적으로 가져오기 (동기적으로는 불가능하므로 기본값 사용)
      // 하지만 이는 버그이므로, mounted에서 확실히 초기화되어야 함
      if (!userLang) {
        console.warn('[StudyManagement] userProfileLanguage가 null입니다. 기본값 "en" 사용')
        userLang = 'en'
      }
      
      // display_title 사용 (백엔드에서 올바르게 처리된 경우)
      if (study.display_title && study.display_title.trim()) {
        forceDebugLog(`✅ [StudyManagement] getStudyTitle - display_title 사용: "${study.display_title}"`)
        return study.display_title
      }
      
      // display_title도 없으면 폴백 로직 사용
      forceDebugLog(`⚠️ [StudyManagement] getStudyTitle - display_title이 없음. study.display_title: "${study.display_title}", study.id: ${study.id}`)
      
      // 사용자 언어에 맞는 제목 반환
      const result = getLocalizedContentWithI18n(study, 'title', this.$i18n, userLang, 'No Title')
      forceDebugLog(`🔄 [StudyManagement] getStudyTitle - fallback 사용: "${result}", userLang: "${userLang}"`)
      return result
    },
    // 토스트 알림 메서드들
    showToastNotification(message, type = 'success', icon = null) {
      // 메시지가 없거나 빈 문자열인 경우 토스트를 표시하지 않음
      if (!message || (typeof message === 'string' && message.trim() === '')) {
        debugLog('⚠️ [StudyManagement] 빈 메시지로 토스트 표시 시도 - 무시됨')
        return
      }
      
      this.toastMessage = message
      this.toastType = type
      this.toastIcon = icon || this.getToastIcon(type)
      this.showToast = true
      
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
    
    // 태그 필터 에러 처리
    handleTagError(error) {
      console.error('태그 필터 에러:', error)
      this.showToastNotification(
        this.$t('studyManagement.messages.loadFailed'),
        'error'
      )
    },
    
    handleTagCreated(tag) {
      // 새로 생성된 태그를 availableTags에 추가
      if (!this.availableTags.find(t => t.id === tag.id)) {
        this.availableTags.push(tag)
        console.log('✅ 새 태그가 availableTags에 추가됨:', tag)
      }
    },
    
    handleSelectedTagsUpdate(selectedTagIds) {
      console.log('🔄 StudyManagement handleSelectedTagsUpdate 호출됨')
      console.log('📊 새로운 selectedTagIds:', selectedTagIds)
      this.selectedTags = selectedTagIds;
      console.log('📊 업데이트된 selectedTags:', this.selectedTags)
    },
    
    handleTagFilterApply(selectedTagIds) {
      console.log('🔄 StudyManagement handleTagFilterApply 호출됨')
      console.log('📊 apply된 selectedTagIds:', selectedTagIds)
      console.log('📊 selectedTagIds 타입:', typeof selectedTagIds)
      console.log('📊 selectedTagIds 길이:', selectedTagIds ? selectedTagIds.length : 'undefined')
      // DevOps 도메인인 경우 카테고리 태그 유지
      const filteredTags = this.ensureDevOpsCategoryTags(selectedTagIds)
      this.selectedTags = filteredTags;
      console.log('📊 this.selectedTags 설정 후:', this.selectedTags)
      console.log('📊 this.selectedTags 길이:', this.selectedTags ? this.selectedTags.length : 'undefined')
      console.log('🔄 loadStudies() 호출 시작')
      this.loadStudies();
      console.log('🔄 loadStudies() 호출 완료')
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
    
    getSelectedTagName(tagId) {
      // availableTags가 아직 로드되지 않았거나 비어있는 경우
      if (!this.availableTags || this.availableTags.length === 0) {
        return 'Loading...';
      }
      
      const tag = this.availableTags.find(t => t.id === tagId);
      if (!tag) {
        console.warn(`태그 ID ${tagId}를 찾을 수 없습니다. availableTags:`, this.availableTags);
        return 'Loading...';
      }
      
      // 사용자 프로필 언어 우선, 없으면 i18n locale, 기본값은 'en'
      const userLang = this.userProfileLanguage || this.$i18n?.locale || 'en'
      
      // 모든 지원 언어 필드를 확인하여 사용자 언어에 맞는 값 반환
      return getLocalizedContentWithI18n(tag, 'name', this.$i18n, userLang, '') || tag.localized_name || (userLang === 'ko' ? '태그 없음' : 'No Tag')
    },
    
    
    // 범용 함수: 현재 도메인의 필수 태그인지 확인
    isRequiredTag(tagId) {
      const domainInfo = getCurrentDomainTagInfo(this.availableTags);
      return domainInfo.isDomainSpecific && domainInfo.isTagRequired(tagId);
    },
    
    
    removeTag(tagId) {
      // 현재 도메인의 필수 태그는 제거할 수 없음
      if (this.isRequiredTag(tagId)) {
        return;
      }
      
      const index = this.selectedTags.indexOf(tagId);
      if (index > -1) {
        this.selectedTags.splice(index, 1);
        this.loadStudies();
      }
    },
    
    
    // 범용 함수: 현재 도메인의 기본 태그 설정
    async setupCurrentDomainDefaultTagsIfNeeded() {
      const domainInfo = getCurrentDomainTagInfo(this.availableTags);
      if (!domainInfo.isDomainSpecific) {
        return;
      }
      
      try {
        console.log(`🏷️ ${domainInfo.config.tagName} 도메인 - 기본 태그 설정 확인`);
        
        // 이미 설정된 태그가 있는지 확인
        const existingTags = localStorage.getItem(domainInfo.config.localStorageKey);
        if (existingTags) {
          const tagIds = JSON.parse(existingTags);
          this.selectedTags = tagIds;
          console.log(`📊 기존 ${domainInfo.config.tagName} 태그 적용:`, tagIds);
          return;
        }
        
        // 서버에서 태그 정보 가져오기
        const response = await fetch('/api/tags/');
        const data = await response.json();
        
        if (data.results && Array.isArray(data.results)) {
          const tag = data.results.find(t => 
            t.name_ko === domainInfo.config.tagName || 
            t.name_en === domainInfo.config.tagName || 
            t.localized_name === domainInfo.config.tagName
          );
          
          if (tag) {
            // sessionStorage에 태그 ID 저장
            sessionStorage.setItem(domainInfo.config.storageKey, tag.id.toString());
            
            // localStorage에 기본 태그 설정
            localStorage.setItem(domainInfo.config.localStorageSetKey, 'true');
            localStorage.setItem(domainInfo.config.localStorageKey, JSON.stringify([tag.id]));
            
            // 현재 컴포넌트에 적용
            this.selectedTags = [tag.id];
            
            console.log(`✅ ${domainInfo.config.tagName} 기본 태그 설정 완료:`, [tag.id]);
          } else {
            console.warn(`⚠️ ${domainInfo.config.tagName} 태그를 찾을 수 없습니다`);
          }
        }
      } catch (error) {
        console.error(`❌ ${domainInfo.config.tagName} 기본 태그 설정 실패:`, error);
      }
    },

    async setupInterestedCategoryTags() {
      console.log('🔄 setupInterestedCategoryTags 호출됨')
      console.log('📊 현재 selectedTags:', this.selectedTags, '길이:', this.selectedTags?.length || 0)
      
      // 이미 태그가 선택되어 있으면 관심 카테고리 태그를 적용하지 않음
      if (this.selectedTags && this.selectedTags.length > 0) {
        console.log('⚠️ 이미 태그가 선택되어 있어서 관심 카테고리 태그를 적용하지 않음')
        return
      }
      
      try {
        // 사용자 프로필에서 관심 카테고리 가져오기
        console.log('📋 사용자 프로필 조회 시작')
        const profileResponse = await axios.get('/api/user-profile/get/')
        const interestedCategoryIds = profileResponse.data?.interested_categories || []
        console.log('📊 관심 카테고리 ID:', interestedCategoryIds)
        
        if (interestedCategoryIds.length === 0) {
          console.log('⚠️ 관심 카테고리가 없음 - 태그 필터를 적용하지 않고 모든 공개 스터디를 표시합니다')
          // 관심 카테고리가 없으면 selectedTags를 빈 배열로 설정하여 태그 필터를 적용하지 않도록 함
          this.selectedTags = []
          return
        }
        
        // 각 관심 카테고리에 속한 태그들 가져오기
        console.log('📋 각 카테고리의 태그 조회 시작')
        const tagPromises = interestedCategoryIds.map(categoryId => 
          axios.get(`/api/tag-categories/${categoryId}/tags/`)
        )
        
        const tagResponses = await Promise.all(tagPromises)
        const allTagIds = []
        
        tagResponses.forEach((response, index) => {
          const tags = response.data?.results || response.data || []
          console.log(`📊 카테고리 ${interestedCategoryIds[index]}의 태그 개수:`, tags.length, '태그:', tags.map(t => getLocalizedContentWithI18n(t, 'name', this.$i18n, this.userProfileLanguage, '') || t.localized_name || ''))
          tags.forEach(tag => {
            if (tag.id && !allTagIds.includes(tag.id)) {
              allTagIds.push(tag.id)
            }
          })
        })
        
        console.log('📊 추출된 모든 태그 ID:', allTagIds)
        
        // 태그가 있으면 필터링 적용, 없으면 null로 설정하여 태그 필터를 적용하지 않도록 함
        if (allTagIds.length > 0) {
          this.selectedTags = allTagIds
          console.log('✅ 관심 카테고리 태그 적용:', allTagIds)
        } else {
          console.log('⚠️ 관심 카테고리에 태그가 없음 - 태그 필터를 적용하지 않고 모든 공개 스터디를 표시합니다')
          this.selectedTags = null
        }
      } catch (error) {
        console.error('❌ 관심 카테고리 태그 설정 실패:', error)
      }
    },
    
    async loadAvailableTags() {
      try {
        // 현재 도메인의 태그 정보를 먼저 가져오기 (범용)
        const domainInfo = getCurrentDomainTagInfo();
        if (domainInfo.isDomainSpecific) {
          await this.fetchCurrentDomainTagFromServer();
        }
        
        const response = await axios.get('/api/studies/tags/');
        this.availableTags = response.data || [];
        
        // 현재 도메인의 기본 태그 적용 (범용)
        const domainInfoAfterFetch = getCurrentDomainTagInfo(this.availableTags);
        if (domainInfoAfterFetch.isDomainSpecific && domainInfoAfterFetch.forcedTags.length > 0) {
          this.selectedTags = domainInfoAfterFetch.forcedTags;
          // 태그 적용은 하되, loadStudies는 mounted에서 호출하므로 여기서는 호출하지 않음
        }
        
        // 강제 업데이트하여 태그 이름이 올바르게 표시되도록 함
        this.$forceUpdate();
      } catch (error) {
        console.error('태그 목록 로드 실패:', error);
      }
    },
    
    
    // 범용 함수: 현재 도메인의 태그를 서버에서 조회
    async fetchCurrentDomainTagFromServer() {
      const domainInfo = getCurrentDomainTagInfo();
      if (!domainInfo.isDomainSpecific) {
        return;
      }
      
      try {
        const response = await fetch('/api/tags/');
        const data = await response.json();
        
        if (data.results && Array.isArray(data.results)) {
          // 모든 지원 언어 필드를 확인하도록 수정
          const tag = data.results.find(t => {
            // 모든 지원 언어 필드 확인 (ko, en, es, zh, ja)
            const supportedLanguages = SUPPORTED_LANGUAGES
            for (const lang of supportedLanguages) {
              if (t[`name_${lang}`] === domainInfo.config.tagName) {
                return true
              }
            }
            // localized_name도 확인
            return t.localized_name === domainInfo.config.tagName
          });
          
          if (tag) {
            const tagId = tag.id;
            // 범용 storage 함수 사용
            sessionStorage.setItem(domainInfo.config.storageKey, tagId.toString());
            console.log(`✅ 서버에서 ${domainInfo.config.tagName} 태그 ID 가져옴:`, tagId);
          } else {
            console.warn(`⚠️ 서버에서 ${domainInfo.config.tagName} 태그를 찾을 수 없습니다.`);
          }
        } else {
          console.warn('⚠️ 태그 API 응답 형식이 올바르지 않습니다.');
        }
      } catch (error) {
        console.error(`${domainInfo.config.tagName} 태그 정보 조회 실패:`, error);
      }
    },
    
    
    // 범용 함수: storage에서 태그 ID 가져오기
    getTagIdFromStorage(storageKey) {
      try {
        const stored = sessionStorage.getItem(storageKey);
        return stored ? parseInt(stored, 10) : null;
      } catch (error) {
        console.warn(`sessionStorage에서 ${storageKey}를 읽을 수 없습니다:`, error);
        return null;
      }
    },
    
    openTagFilterModal() {
      console.log('🔄 openTagFilterModal 호출됨');
      this.showTagFilterModal = true;
      console.log('📊 showTagFilterModal:', this.showTagFilterModal);
    },
    
    // New Study Tag Management
    openNewStudyTagModal() {
      this.showNewStudyTagModal = true
    },
    
    handleNewStudyTagUpdate(selectedTags) {
      this.newStudyTags = selectedTags
    },
    
    handleNewStudyTagApply(selectedTags) {
      this.newStudyTags = selectedTags
      this.showNewStudyTagModal = false
    },
    
    removeNewStudyTag(tagId) {
      const index = this.newStudyTags.indexOf(tagId)
      if (index > -1) {
        this.newStudyTags.splice(index, 1)
      }
    },
    
    // 모달 메서드들
    showConfirmModal(title, message, confirmText = '', cancelText = '', confirmButtonClass = 'btn-success', icon = 'fas fa-question', callback = null, modalType = '') {
      console.log('🔍 showConfirmModal 호출됨 - 제목:', title)
      this.modalTitle = title
      this.modalMessage = message
      this.modalConfirmText = confirmText
      this.modalCancelText = cancelText
      this.modalConfirmButtonClass = confirmButtonClass
      this.modalIcon = icon
      this.modalCallback = callback
      this.modalType = modalType
      this.showModal = true
      console.log('🔍 showConfirmModal 완료 - showModal:', this.showModal)
    },
    
    confirmModal() {
      if (this.modalCallback) {
        // 가입 요청 모달인 경우 입력된 메시지를 전달
        if (this.modalType === 'join-request') {
          this.modalCallback(this.joinRequestInput)
        } else {
          this.modalCallback()
        }
      }
      this.hideModal()
    },
    
    cancelModal() {
      this.hideModal()
    },
    
    hideModal() {
      console.log('🔍 hideModal 호출됨 - 현재 showModal:', this.showModal)
      this.showModal = false
      this.modalCallback = null
      this.modalType = '' // 모달 타입 초기화
      this.joinRequestInput = '' // 입력 필드 초기화
      console.log('🔍 hideModal 완료 - showModal:', this.showModal)
    },
    
    handleCreateStudy() {
      if (!this.isAuthenticated) {
        this.$router.push('/login')
        return
      }
      this.toggleCreateForm()
    },

    // 스터디 생성자인지 확인
    isStudyCreator(study) {
      const studyTitle = getLocalizedContentWithI18n(study, 'title', this.$i18n, this.userProfileLanguage, study.title || '제목 없음');
      debugLog('🔍 isStudyCreator 체크:', {
        studyTitle: studyTitle,
        studyCreatedBy: study.created_by,
        currentUser: this.currentUser,
        hasCurrentUser: !!this.currentUser,
        hasCreatedBy: !!study.created_by,
        userIdMatch: study.created_by && study.created_by.id === this.currentUser?.id
      })
      
      if (!this.currentUser || !study) {
        debugLog('❌ 사용자 또는 스터디 정보 없음')
        return false
      }
      
      const isCreator = study.created_by && (
        (typeof study.created_by === 'object' && String(study.created_by.id) === String(this.currentUser.id)) ||
        String(study.created_by) === String(this.currentUser.id)
      )
      debugLog('✅ 스터디 생성자 여부:', isCreator)
      return isCreator
    },
    // 스터디 관리자인지 확인
    isStudyAdmin(study) {
      if (!this.currentUser || !study || !study.members) {
        debugLog('❌ 스터디 관리자 확인 불가: 사용자 또는 스터디 정보 없음')
        return false
      }
      
      const studyTitle = getLocalizedContentWithI18n(study, 'title', this.$i18n, this.userProfileLanguage, study.title || '제목 없음');
      debugLog('🔍 isStudyAdmin 체크:', {
        studyTitle: studyTitle,
        currentUser: this.currentUser,
        members: study.members
      })
      
      // 스터디 멤버 중에서 현재 사용자가 study_admin 또는 study_leader 역할을 가지고 있는지 확인
      const isAdmin = study.members.some(member => {
        if (!member.user) return false
        const memberUserId = typeof member.user === 'object' ? member.user.id : member.user
        return String(memberUserId) === String(this.currentUser.id) && 
               (member.role === 'study_admin' || member.role === 'study_leader')
      })
      
      debugLog('✅ 스터디 관리자 여부:', isAdmin)
      return isAdmin
    },
    // 스터디를 삭제할 수 있는 권한이 있는지 확인 (관리자, 생성자, 또는 스터디 관리자)
    canDeleteStudy(study) {
      const studyTitle = getLocalizedContentWithI18n(study, 'title', this.$i18n, this.userProfileLanguage, study.title || '제목 없음');
      debugLog('🔍 canDeleteStudy 체크:', {
        studyTitle: studyTitle,
        studyId: study.id,
        studyCreatedBy: study.created_by,
        currentUser: this.currentUser,
        isAdmin: this.isAdmin,
        isStudyCreator: this.isStudyCreator(study),
        isStudyAdmin: this.isStudyAdmin(study)
      })
      
      const canDelete = this.isAdmin || this.isStudyCreator(study) || this.isStudyAdmin(study)
      debugLog('✅ 삭제 권한:', canDelete)
      return canDelete
    },
    goToPage(page) {
      if (page >= 1 && page <= this.totalPages) {
        this.currentPage = page
        // 태그 필터링이 있으면 loadAllStudies, 없으면 loadStudies 호출
        if (this.selectedTags && this.selectedTags.length > 0) {
          this.loadAllStudies()
        } else {
          this.loadStudies()
        }
      }
    },
    async loadStudies() {
      // 태그 필터링이 있으면 loadAllStudies 사용
      // Public Studies에서 selectedTags가 배열이고 길이가 0보다 크면 loadAllStudies를 호출
      // selectedTags가 null이거나 undefined이면 태그 필터를 적용하지 않고 일반 loadStudies 로직 사용
      // 단, 로그인하지 않은 사용자는 태그 필터를 적용하지 않음
      if (this.studyTypeFilter === 'public' && Array.isArray(this.selectedTags) && this.selectedTags.length > 0 && this.isAuthenticated) {
        await this.loadAllStudies()
        return
      }
      if (this.selectedTags && Array.isArray(this.selectedTags) && this.selectedTags.length > 0) {
        await this.loadAllStudies()
        return
      }
      
      try {
        this.loading = true
        
        // 가입 요청 상태는 mounted에서만 로드 (성능 최적화)
        // loadStudies는 페이지네이션 등으로 자주 호출되므로 여기서는 체크하지 않음
        
        // 익명 사용자 처리
        const user = getCurrentUserFromPermissions()
        
        let url = '/api/studies/'
        const params = []
        
        // 사용자 프로필 언어를 lang 파라미터로 전송
        const userProfileLanguage = await this.getUserProfileLanguage()
        
        // 사용자 프로필 언어에 맞는 필드만 선택 (성능 최적화)
        // 현재 언어 필드 + 영어 fallback 필드 + display_title, display_goal 필드만 요청
        const selectFields = ['id', 'created_language', 'start_date', 'end_date', 'is_public', 'created_by', 'members', 'tasks', 'display_title', 'display_goal']
        
        // 현재 언어 필드 추가
        if (userProfileLanguage === 'ko') {
          selectFields.push('title_ko', 'goal_ko', 'is_ko_complete')
        } else if (userProfileLanguage === 'zh') {
          selectFields.push('title_zh', 'goal_zh', 'is_zh_complete')
        } else if (userProfileLanguage === 'es') {
          selectFields.push('title_es', 'goal_es', 'is_es_complete')
        }
        
        // 영어 fallback 필드 추가 (항상 필요)
        selectFields.push('title_en', 'goal_en', 'is_en_complete')
        
        params.push(`select=${selectFields.join(',')}`)
        params.push(`lang=${userProfileLanguage}`)
        
        // 페이지네이션 파라미터
        params.push(`page=${this.currentPage}`)
        params.push(`page_size=${this.pageSize}`)
        
        // 스터디 타입 필터에 따라 API 파라미터 설정
        if (this.studyTypeFilter === 'public') {
          // 공개 스터디만 요청
          params.push('is_public=true')
        } else if (this.studyTypeFilter === 'my') {
          // 내 스터디만 요청 (멤버이거나 생성자인 스터디)
          params.push('my_studies=true')
        } else if (this.studyTypeFilter === 'all' && user && user.role === 'admin_role') {
          // 관리자가 모든 스터디를 볼 때 추가 필터 적용
          if (this.publicFilter === 'true') {
            params.push('is_public=true')
          } else if (this.publicFilter === 'false') {
            params.push('is_public=false')
          }
        }
        
        // 파라미터가 있으면 URL에 추가
        if (params.length > 0) {
          url += '?' + params.join('&')
        }
        
        forceDebugLog(`🌐 [StudyManagement] API 요청 URL: ${url}`)
        forceDebugLog(`🌐 [StudyManagement] 요청 파라미터 - lang: ${userProfileLanguage}, select: ${selectFields.join(',')}`)
        
        const response = await axios.get(url)
        forceDebugLog(`📥 [StudyManagement] API 응답 수신 - 전체 응답:`, JSON.stringify(response.data, null, 2))
        debugLog('스터디 API 응답:', response.data)
        
        // 페이지네이션 응답에서 results 배열을 가져옴
        const studiesData = response.data.results || response.data
        this.studies = Array.isArray(studiesData) ? studiesData : []
        debugLog('로드된 스터디 수:', this.studies.length)
        
        // 디버깅: 각 스터디의 display_title 확인 (상세)
        if (this.studies && Array.isArray(this.studies)) {
          this.studies.forEach(study => {
            forceDebugLog(`🔍 [StudyManagement] 스터디 ID ${study.id} - 전체 study 객체:`, JSON.stringify(study, null, 2))
            forceDebugLog(`🔍 [StudyManagement] 스터디 ID ${study.id} - display_title: "${study.display_title}" (type: ${typeof study.display_title}), title_zh: "${study.title_zh}" (type: ${typeof study.title_zh}), title_en: "${study.title_en}" (type: ${typeof study.title_en}), userProfileLanguage: ${userProfileLanguage}`)
            // getStudyTitle 호출하여 실제 반환값 확인
            const computedTitle = this.getStudyTitle(study)
            forceDebugLog(`🔍 [StudyManagement] 스터디 ID ${study.id} - getStudyTitle() 반환값: "${computedTitle}"`)
          })
        }
        
        // 페이지네이션 정보 업데이트
        // currentPage는 goToPage에서 설정한 값을 유지하고, API 응답의 page는 검증용으로만 사용
        if (response.data.pagination) {
          // API 응답의 page가 현재 설정된 currentPage와 다르면 API 응답 값 사용 (서버가 올바른 페이지를 반환했는지 확인)
          const apiPage = response.data.pagination.page || this.currentPage || 1
          // API 응답의 페이지가 유효한 범위 내에 있으면 사용
          if (apiPage >= 1) {
            this.currentPage = apiPage
          }
          this.totalCount = response.data.pagination.total_count || response.data.pagination.count || 0
          this.totalPages = response.data.pagination.total_pages || 1
        } else if (response.data.count !== undefined) {
          // DRF 기본 페이지네이션 형식 지원
          const apiPage = parseInt(response.data.current || this.currentPage || 1)
          if (apiPage >= 1) {
            this.currentPage = apiPage
          }
          this.totalCount = response.data.count || 0
          this.totalPages = Math.ceil((response.data.count || 0) / this.pageSize)
        } else {
          // 페이지네이션 정보가 없는 경우 (하위 호환성)
          // currentPage는 이미 goToPage에서 설정되었으므로 유지
          this.totalCount = this.studies.length
          this.totalPages = Math.ceil(this.studies.length / this.pageSize) || 1
        }
        
        // 디버깅: 현재 사용자 정보와 스터디 멤버 정보 출력
        const currentUser = getCurrentUserFromPermissions() || {}
        debugLog('🔍 현재 사용자 정보:', currentUser)
        
        if (this.studies && Array.isArray(this.studies)) {
          this.studies.forEach(study => {
            const studyTitle = getLocalizedContentWithI18n(study, 'title', this.$i18n, this.userProfileLanguage, study.title || '제목 없음');
        debugLog(`📚 스터디 "${studyTitle}" (ID: ${study.id}):`)
            debugLog(`  - 공개 여부: ${study.is_public}`)
            debugLog(`  - 생성자: ${study.created_by?.username || '없음'}`)
            debugLog(`  - 멤버 수: ${study.members?.length || 0}`)
            if (study.members && study.members.length > 0) {
              study.members.forEach(member => {
                debugLog(`    - 멤버: ${member.name} (user: ${member.user}, email: ${member.email})`)
              })
            }
          })
          
          // My Study가 없고 현재 필터가 'my'인 경우 자동으로 Public Studies로 전환
          // select 콤보박스도 자동으로 "Public Studies"로 변경됨 (v-model="studyTypeFilter"로 바인딩되어 있음)
          if (this.studyTypeFilter === 'my' && this.studies.length === 0 && this.isAuthenticated && !this.isAutoSwitchingToPublic) {
            debugLog('📝 My Study가 없어서 자동으로 Public Studies로 전환합니다.')
            this.isAutoSwitchingToPublic = true
            this.studyTypeFilter = 'public'
            // 사용자에게 자동 전환 알림
            this.showToastNotification(this.$t('studyManagement.messages.autoSwitchToPublic'), 'info', 'fas fa-info-circle')
            // Public Studies 다시 로드
            await this.loadStudies()
            this.isAutoSwitchingToPublic = false
            return
          }
        } else {
          debugLog('⚠️ studies가 undefined이거나 배열이 아닙니다:', this.studies)
        }
        
        // 캐시 업데이트
        this.cacheData()
      } catch (error) {
        debugLog('스터디 목록 로드 실패:', error, 'error')
        this.studies = []
        this.showToastNotification(this.$t('studyManagement.messages.loadFailed'), 'error')
      } finally {
        this.loading = false
      }
    },
    async loadAllStudies() {
      try {
        this.loading = true
        forceDebugLog('loadAllStudies 시작')
        
        // 가입 요청 상태는 mounted에서만 로드 (성능 최적화)
        // loadAllStudies는 태그 필터 변경 시 호출되므로 여기서는 체크하지 않음
        
        // 스터디 타입과 태그 필터링을 모두 적용하여 로드
        // 사용자 프로필 언어를 lang 파라미터로 전송
        const userProfileLanguage = await this.getUserProfileLanguage()
        
        // 사용자 프로필 언어에 맞는 필드만 선택 (성능 최적화)
        // 현재 언어 필드 + 영어 fallback 필드 + display_title, display_goal 필드만 요청
        const selectFields = ['id', 'created_language', 'start_date', 'end_date', 'is_public', 'created_by', 'members', 'tasks', 'tags', 'display_title', 'display_goal']
        
        // 현재 언어 필드 추가
        if (userProfileLanguage === 'ko') {
          selectFields.push('title_ko', 'goal_ko', 'is_ko_complete')
        } else if (userProfileLanguage === 'zh') {
          selectFields.push('title_zh', 'goal_zh', 'is_zh_complete')
        } else if (userProfileLanguage === 'es') {
          selectFields.push('title_es', 'goal_es', 'is_es_complete')
        }
        
        // 영어 fallback 필드 추가 (항상 필요)
        selectFields.push('title_en', 'goal_en', 'is_en_complete')
        
        const params = new URLSearchParams({
          select: selectFields.join(','),
          lang: userProfileLanguage,
          page: this.currentPage.toString(),
          page_size: this.pageSize.toString()
        })
        
        // 스터디 타입 필터 적용
        if (this.studyTypeFilter === 'public') {
          params.append('is_public', 'true')
        } else if (this.studyTypeFilter === 'my') {
          params.append('my_studies', 'true')
        } else if (this.studyTypeFilter === 'all') {
          // 관리자만 모든 스터디를 볼 수 있음
        }
        
        // 태그 필터링 적용 (도메인 강제 태그 또는 선택된 태그)
        const domainInfo = getCurrentDomainTagInfo(this.availableTags);
        if (domainInfo.isDomainSpecific) {
          // 도메인별 강제 태그가 있는 경우
          const tagId = this.getTagIdFromStorage(domainInfo.config.storageKey);
          if (tagId) {
            params.append('tags', tagId);
          } else {
            // sessionStorage에 없으면 서버에서 가져와서 적용 (최초 1회만)
            try {
              const response = await fetch('/api/tags/');
              const data = await response.json();
              
              if (data.results && Array.isArray(data.results)) {
                // 모든 지원 언어 필드를 확인하도록 수정
                const tag = data.results.find(t => {
                  // 모든 지원 언어 필드 확인 (ko, en, es, zh, ja)
                  const supportedLanguages = SUPPORTED_LANGUAGES
                  for (const lang of supportedLanguages) {
                    if (t[`name_${lang}`] === domainInfo.config.tagName) {
                      return true
                    }
                  }
                  // localized_name도 확인
                  return t.localized_name === domainInfo.config.tagName
                });
                
                if (tag) {
                  sessionStorage.setItem(domainInfo.config.storageKey, tag.id.toString());
                  params.append('tags', tag.id);
                }
              }
            } catch (error) {
              console.error(`❌ ${domainInfo.config.tagName} 태그 조회 실패:`, error);
            }
          }
        } else if (this.selectedTags && this.selectedTags.length > 0) {
          // 선택된 태그로 필터링
          this.selectedTags.forEach(tagId => {
            params.append('tags', tagId)
          })
        }
        
        // Public Studies에서 관심 카테고리에 태그가 없을 때는 빈 결과를 직접 설정
        // selectedTags가 null이거나 undefined이거나 빈 배열이면 태그 필터를 적용하지 않음
        // 이는 관심 카테고리가 없거나 태그가 없을 때 모든 공개 스터디를 보여주기 위함
        // 빈 배열일 때만 빈 결과를 반환하는 로직은 제거 (관심 카테고리가 없으면 null로 설정하므로)
        
        const requestUrl = `/api/studies/?${params.toString()}`
        forceDebugLog(`🌐 [StudyManagement] API 요청 URL (전체): ${requestUrl}`)
        forceDebugLog(`🌐 [StudyManagement] 요청 파라미터 - lang: ${userProfileLanguage}, select: ${selectFields.join(',')}`)
        
        const response = await axios.get(requestUrl)
        forceDebugLog(`📥 [StudyManagement] API 응답 수신 (loadAllStudies) - 전체 응답:`, JSON.stringify(response.data, null, 2))
        forceDebugLog('스터디 API 응답 (전체):', response.data)
        
        // 페이지네이션 응답에서 results 배열을 가져옴
        const studiesData = response.data.results || response.data
        this.studies = Array.isArray(studiesData) ? studiesData : []
        forceDebugLog('로드된 스터디 수 (전체):', this.studies.length)
        
        // 디버깅: 각 스터디의 display_title 확인 (상세)
        if (this.studies && Array.isArray(this.studies)) {
          this.studies.forEach(study => {
            forceDebugLog(`🔍 [StudyManagement] 스터디 ID ${study.id} - 전체 study 객체:`, JSON.stringify(study, null, 2))
            forceDebugLog(`🔍 [StudyManagement] 스터디 ID ${study.id} - display_title: "${study.display_title}" (type: ${typeof study.display_title}), title_zh: "${study.title_zh}" (type: ${typeof study.title_zh}), title_en: "${study.title_en}" (type: ${typeof study.title_en}), userProfileLanguage: ${userProfileLanguage}`)
            // getStudyTitle 호출하여 실제 반환값 확인
            const computedTitle = this.getStudyTitle(study)
            forceDebugLog(`🔍 [StudyManagement] 스터디 ID ${study.id} - getStudyTitle() 반환값: "${computedTitle}"`)
          })
        }
        
        // 페이지네이션 정보 업데이트
        // currentPage는 goToPage에서 설정한 값을 유지하고, API 응답의 page는 검증용으로만 사용
        if (response.data.pagination) {
          // API 응답의 page가 현재 설정된 currentPage와 다르면 API 응답 값 사용 (서버가 올바른 페이지를 반환했는지 확인)
          const apiPage = response.data.pagination.page || this.currentPage || 1
          // API 응답의 페이지가 유효한 범위 내에 있으면 사용
          if (apiPage >= 1) {
            this.currentPage = apiPage
          }
          this.totalCount = response.data.pagination.total_count || response.data.pagination.count || 0
          this.totalPages = response.data.pagination.total_pages || 1
        } else if (response.data.count !== undefined) {
          // DRF 기본 페이지네이션 형식 지원
          const apiPage = parseInt(response.data.current || this.currentPage || 1)
          if (apiPage >= 1) {
            this.currentPage = apiPage
          }
          this.totalCount = response.data.count || 0
          this.totalPages = Math.ceil((response.data.count || 0) / this.pageSize)
        } else {
          // 페이지네이션 정보가 없는 경우 (하위 호환성)
          // currentPage는 이미 goToPage에서 설정되었으므로 유지
          this.totalCount = this.studies.length
          this.totalPages = Math.ceil(this.studies.length / this.pageSize) || 1
        }
        forceDebugLog('스터디 목록:', this.studies.map(s => ({ 
          id: s.id, 
          title: getLocalizedContentWithI18n(s, 'title', this.$i18n, this.userProfileLanguage, s.title || '제목 없음'), 
          is_public: s.is_public 
        })))
        
        // My Study가 없고 현재 필터가 'my'인 경우 자동으로 Public Studies로 전환
        // select 콤보박스도 자동으로 "Public Studies"로 변경됨 (v-model="studyTypeFilter"로 바인딩되어 있음)
        if (this.studyTypeFilter === 'my' && this.studies.length === 0 && this.isAuthenticated && !this.isAutoSwitchingToPublic) {
          debugLog('📝 My Study가 없어서 자동으로 Public Studies로 전환합니다.')
          this.isAutoSwitchingToPublic = true
          this.studyTypeFilter = 'public'
          // 사용자에게 자동 전환 알림
          this.showToastNotification(this.$t('studyManagement.messages.autoSwitchToPublic'), 'info', 'fas fa-info-circle')
          // Public Studies 다시 로드
          await this.loadAllStudies()
          this.isAutoSwitchingToPublic = false
          return
        }
        
        // 캐시 업데이트
        this.cacheData()
      } catch (error) {
        debugLog('스터디 목록 로드 실패 (전체):', error, 'error')
        this.studies = []
        this.showToastNotification(this.$t('studyManagement.messages.loadFailed'), 'error')
      } finally {
        this.loading = false
        forceDebugLog('loadAllStudies 완료')
      }
    },
    formatDate(dateString) {
      if (!dateString) return ''
      const date = new Date(dateString)
      const localeMap = {
        'ko': 'ko-KR',
        'en': 'en-US',
        'es': 'es-ES',
        'zh': 'zh-CN',
        'ja': 'ja-JP'
      }
      const locale = localeMap[this.$i18n.locale] || 'en-US'
      return date.toLocaleDateString(locale)
    },
    formatShortDate(dateString) {
      if (!dateString) return ''
      const date = new Date(dateString)
      const month = date.getMonth() + 1
      const day = date.getDate()
      const year = date.getFullYear()
      return `${month}/${day}/${year}`
    },
    isMaxDate(dateString) {
      if (!dateString) return false
      // 최대값 날짜 확인: 9999-12-31 또는 9999년도
      const date = new Date(dateString)
      return date.getFullYear() >= 9999
    },
    toggleCreateForm() {
      this.showCreateForm = !this.showCreateForm
      if (!this.showCreateForm) {
        this.resetForm()
      } else {
        // 폼이 열릴 때 도메인별 기본 태그 자동 추가
        this.setupDefaultTagsForNewStudy()
      }
    },
    setupDefaultTagsForNewStudy() {
      // 도메인별 기본 태그 설정
      const domainConfig = getCurrentDomainConfig()
      if (domainConfig) {
        const forcedTags = getForcedTags(domainConfig, this.availableTags)
        if (forcedTags.length > 0) {
          this.newStudyTags = [...forcedTags]
          console.log(`🏷️ ${domainConfig.tagName} 도메인 - 새 스터디 생성 시 기본 태그 자동 추가:`, this.newStudyTags)
        }
      }
    },
    resetForm() {
      this.newStudy = {
        title_ko: '',
        title_en: '',
        goal_ko: '',
        goal_en: '',
        start_date: new Date().toISOString().split('T')[0],
        end_date: '',
        is_public: true
      }
      this.newStudyTags = [] // 태그 초기화
      this.titleError = '' // 에러 메시지 초기화
    },
    cancelCreate() {
      this.showCreateForm = false
      this.newStudy = {
        title_ko: '',
        title_en: '',
        goal_ko: '',
        goal_en: '',
        start_date: new Date().toISOString().split('T')[0],
        end_date: '',
        is_public: true
      }
      this.newStudyTags = [] // 태그 초기화
      this.titleError = '' // 에러 메시지 초기화
    },
    // 제목 중복 체크
    checkTitleDuplicate() {
      const currentTitle = this.newStudy[`title_${this.currentUserLanguage}`]
      if (!currentTitle || !currentTitle.trim()) {
        this.titleError = this.$t('studyManagement.messages.titleRequired')
        return false
      }
      
      // 현재 스터디 목록에서 같은 제목이 있는지 확인 (현재 언어 기준)
      const isDuplicate = this.studies.some(study => {
        const studyTitle = study[`title_${this.currentUserLanguage}`] || study.title || ''
        return studyTitle.toLowerCase().trim() === currentTitle.toLowerCase().trim()
      })
      
      if (isDuplicate) {
        this.titleError = this.$t('studyManagement.messages.duplicateTitle')
        return false
      }
      
      this.titleError = ''
      return true
    },
    
    // 제목 입력 시 에러 메시지 제거
    clearTitleError() {
      if (this.titleError) {
        this.titleError = ''
      }
    },
    
    async createStudy() {
      // 제목 중복 체크
      if (!this.checkTitleDuplicate()) {
        return
      }
      
      try {
        const studyData = {
          // 현재 언어에 맞는 필드 전송 (다른 언어는 백엔드에서 자동 번역)
          is_public: this.newStudy.is_public,
          // 프론트엔드에서 명시적으로 언어 전달 (프로필 언어와 다를 수 있음)
          created_language: this.currentUserLanguage
        }
        
        // 현재 언어에 따라 적절한 필드 설정
        if (this.currentUserLanguage === 'ko') {
          studyData.title_ko = this.newStudy.title_ko || ''
          studyData.goal_ko = this.newStudy.goal_ko || ''
        } else if (this.currentUserLanguage === 'en') {
          studyData.title_en = this.newStudy.title_en || ''
          studyData.goal_en = this.newStudy.goal_en || ''
        } else if (this.currentUserLanguage === 'zh') {
          studyData.title_zh = this.newStudy.title_zh || ''
          studyData.goal_zh = this.newStudy.goal_zh || ''
        } else if (this.currentUserLanguage === 'es') {
          studyData.title_es = this.newStudy.title_es || ''
          studyData.goal_es = this.newStudy.goal_es || ''
        }
        
        // 빈 값이 아닌 경우에만 날짜 필드 추가
        if (this.newStudy.start_date && this.newStudy.start_date.trim() !== '') {
          studyData.start_date = this.newStudy.start_date
        }
        // End Date가 비어있으면 최대값(9999-12-31)으로 설정
        if (this.newStudy.end_date && this.newStudy.end_date.trim() !== '') {
          studyData.end_date = this.newStudy.end_date
        } else {
          // End Date가 지정되지 않으면 최대값으로 설정
          studyData.end_date = '9999-12-31'
        }
        
        // 태그 추가
        if (this.newStudyTags && this.newStudyTags.length > 0) {
          studyData.tags = this.newStudyTags
        }
        
        const response = await axios.post('/api/studies/', studyData)
        debugLog('스터디 생성 성공:', response.data)
        
        // 캐시 무효화 후 스터디 목록 새로고침 (필터 초기화)
        this.clearCache()
        this.publicFilter = '' // 필터 초기화
        
        // 스터디 생성 후에는 모든 스터디를 로드
        forceDebugLog('스터디 생성 후 목록 새로고침 시작')
        await this.loadAllStudies()
        forceDebugLog('스터디 생성 후 목록 새로고침 완료, 현재 스터디 수:', this.studies.length)
        
        // 폼 초기화
        this.cancelCreate()
        
        this.showToastNotification(this.$t('studyManagement.messages.createSuccess'), 'success')
      } catch (error) {
        debugLog('스터디 생성 실패:', error, 'error')
        this.showToastNotification(this.$t('studyManagement.messages.createFailed'), 'error')
      }
    },
    async deleteStudy(studyId) {
      this.showConfirmModal(
        this.$t('studyManagement.messages.deleteConfirmTitle'),
        this.$t('studyManagement.messages.deleteConfirm'),
        this.$t('studyManagement.messages.delete'),
        this.$t('studyManagement.messages.cancel'),
        'btn-danger',
        'fas fa-trash',
        async () => {
          try {
            await axios.delete(`/api/studies/${studyId}/`)
            // 캐시 무효화 후 스터디 목록 새로고침
            this.clearCache()
            await this.loadAllStudies()
            // 삭제 성공 메시지 표시하지 않음
          } catch (error) {
            debugLog('스터디 삭제 실패:', error, 'error')
            this.showToastNotification(this.$t('studyManagement.messages.deleteFailed'), 'error')
          }
        }
      )
    },
    // 일괄 선택/해제 로직
    toggleSelectAll(event) {
      if (event.target.checked) {
        this.selectedStudies = this.sortedStudies.map(study => String(study.id))
      } else {
        this.selectedStudies = []
      }
    },
    // 스터디 선택 확인
    isStudySelected(id) {
      return this.selectedStudies.includes(String(id))
    },
    // 스터디 선택 토글
    toggleStudySelection(id, event) {
      id = String(id)
      
      if (event.target.checked) {
        if (!this.selectedStudies.includes(id)) {
          this.selectedStudies = [...this.selectedStudies, id]
        }
      } else {
        this.selectedStudies = this.selectedStudies.filter(sid => sid !== id)
      }
    },
    // 일괄 삭제 로직
    async deleteSelected() {
      this.showConfirmModal(
        this.$t('studyManagement.messages.bulkDeleteConfirm', { count: this.selectedStudies.length }) || `선택한 ${this.selectedStudies.length}개의 스터디를 삭제하시겠습니까?`,
        this.$t('studyManagement.messages.bulkDeleteConfirm', { count: this.selectedStudies.length }) || `선택한 ${this.selectedStudies.length}개의 스터디를 삭제하시겠습니까?`,
        this.$t('studyManagement.delete') || 'Delete',
        this.$t('studyManagement.messages.cancel') || 'Cancel',
        'btn-danger',
        'fas fa-trash',
        () => this.executeBulkDelete()
      )
    },
    // 일괄 삭제 실행
    async executeBulkDelete() {
      try {
        // 로딩 상태 시작
        this.loading = true
        
        const deleteCount = this.selectedStudies.length
        const selectedStudiesCopy = [...this.selectedStudies]
        
        for (const studyId of selectedStudiesCopy) {
          await axios.delete(`/api/studies/${studyId}/`)
        }
        
        // 캐시 무효화
        this.clearCache()
        
        // 삭제 후 스터디 목록 새로고침
        await this.loadAllStudies()
        
        // 선택 해제
        this.selectedStudies = []
        
        this.showToastNotification(
          this.$t('studyManagement.messages.bulkDeleteSuccess', { count: deleteCount }) || `${deleteCount}개의 스터디가 성공적으로 삭제되었습니다.`,
          'success'
        )
      } catch (error) {
        debugLog('일괄 삭제 실패:', error, 'error')
        this.showToastNotification(
          this.$t('studyManagement.messages.bulkDeleteFailed') || '스터디 삭제에 실패했습니다.',
          'error'
        )
      } finally {
        // 로딩 상태 종료
        this.loading = false
      }
    },

    setSort(key) {
      if (this.sortKey === key) {
        this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc'
      } else {
        this.sortKey = key
        this.sortOrder = 'asc'
      }
      
      // 사용자가 정렬을 변경한 경우, 기본 정렬 로직을 우선 적용
      // 하지만 여전히 최근 생성된 스터디를 위쪽에, 만료된 스터디를 아래쪽에 표시
    },
    getSortIcon(key) {
      if (this.sortKey === key) {
        return this.sortOrder === 'asc' ? 'fas fa-sort-up' : 'fas fa-sort-down'
      }
      return 'fas fa-sort'
    },
    prevMonth() {
      if (this.calendarMonth === 0) {
        this.calendarMonth = 11;
        this.calendarYear--;
      } else {
        this.calendarMonth--;
      }
    },
    nextMonth() {
      if (this.calendarMonth === 11) {
        this.calendarMonth = 0;
        this.calendarYear++;
      } else {
        this.calendarMonth++;
      }
    },
    prevYear() {
      this.calendarYear--;
    },
    nextYear() {
      this.calendarYear++;
    },
    getStudyColor(studyId) {
      return getRandomColor(studyId + '');
    },
    getStudyBarsForDate(dateObj) {
      // dateObj: { day, isCurrentMonth, isToday, date: Date }
      if (!dateObj || !dateObj.isCurrentMonth) return [];
      const bars = [];
      const studies = this.sortedStudies || [];
      studies.forEach((study) => {
        if (!study.start_date || !study.end_date) return;
        const start = new Date(study.start_date);
        const end = new Date(study.end_date);
        // 해당 날짜가 스터디 기간 내에 있는지 확인
        if (dateObj.date >= start && dateObj.date <= end) {
          bars.push({
            study,
            color: this.getStudyColor(study.id)
          });
        }
      });
      return bars;
    },
    selectDate(dateObj) {
      // 현재 월이 아닌 날짜는 선택 불가
      if (!dateObj.isCurrentMonth) return;
      
      const clickedDate = new Date(dateObj.date);
      clickedDate.setHours(0, 0, 0, 0);
      
      // 시작일과 종료일을 모두 선택한 상태에서 같은 날짜를 클릭하면 필터 해제
      if (this.selectedDateRange.startDate && this.selectedDateRange.endDate) {
        if (this.isSameDate(clickedDate, this.selectedDateRange.startDate) || 
            this.isSameDate(clickedDate, this.selectedDateRange.endDate)) {
          this.clearDateRange();
          return;
        }
      }
      
      if (this.dateSelectionMode === 'start' || !this.selectedDateRange.startDate) {
        // 시작일 선택
        this.selectedDateRange.startDate = clickedDate;
        this.selectedDateRange.endDate = null;
        this.dateSelectionMode = 'end';
      } else {
        // 종료일 선택
        if (clickedDate < this.selectedDateRange.startDate) {
          // 종료일이 시작일보다 이전이면 시작일과 종료일을 교체
          this.selectedDateRange.endDate = new Date(this.selectedDateRange.startDate);
          this.selectedDateRange.startDate = clickedDate;
        } else {
          this.selectedDateRange.endDate = clickedDate;
        }
        // 범위 선택 완료 후 다시 시작 모드로
        this.dateSelectionMode = 'start';
      }
    },
    clearDateRange() {
      this.selectedDateRange = { startDate: null, endDate: null };
      this.dateSelectionMode = 'start';
    },
    resetCalendarToToday() {
      const today = new Date();
      this.calendarYear = today.getFullYear();
      this.calendarMonth = today.getMonth();
      this.clearDateRange();
    },
    isSameDate(date1, date2) {
      if (!date1 || !date2) return false;
      const d1 = new Date(date1);
      const d2 = new Date(date2);
      d1.setHours(0, 0, 0, 0);
      d2.setHours(0, 0, 0, 0);
      return d1.getTime() === d2.getTime();
    },
    isDateInRange(date, startDate, endDate) {
      if (!startDate || !endDate) return false;
      const d = new Date(date);
      const start = new Date(startDate);
      const end = new Date(endDate);
      d.setHours(0, 0, 0, 0);
      start.setHours(0, 0, 0, 0);
      end.setHours(0, 0, 0, 0);
      return d > start && d < end;
    },
    recordProgress(studyId) {
      // 익명 사용자 처리
      const user = getCurrentUserFromPermissions()
      
      if (!user) {
        this.showToastNotification(this.$t('studyManagement.messages.loginRequired'), 'error');
        return;
      }

      const study = this.studies.find(s => s.id === studyId);
      if (!study) {
        this.showToastNotification(this.$t('studyManagement.messages.studyNotFound'), 'error');
        return;
      }

      const member = study.members.find(m => m.user === user.id);
      if (!member) {
        this.showToastNotification(this.$t('studyManagement.messages.notMember'), 'error');
        return;
      }

      const progress = member.progress || 0;
      const studyTitle = getLocalizedContentWithI18n(study, 'title', this.$i18n, this.userProfileLanguage, study.title || '제목 없음');
      const newProgress = prompt(this.$t('studyManagement.messages.enterProgress', { title: studyTitle, progress: progress }), progress);

      if (newProgress !== null && newProgress !== '') {
        const numericProgress = parseFloat(newProgress);
        if (!isNaN(numericProgress) && numericProgress >= 0 && numericProgress <= 100) {
          const updatedMember = { ...member, progress: numericProgress };
          const index = study.members.findIndex(m => m.user === user.id);
          if (index !== -1) {
            study.members[index] = updatedMember;
          }
          this.$emit('progress-updated', { studyId: studyId, progress: numericProgress });
          this.showToastNotification(this.$t('studyManagement.messages.progressUpdated', { title: studyTitle, progress: numericProgress }), 'success');
        } else {
                      this.showToastNotification(this.$t('studyManagement.messages.invalidProgress'), 'error');
        }
      }
    },
    async recordAllStudyProgress() {
      // 익명 사용자는 진행율 기록하지 않음
      const user = getCurrentUserFromPermissions()
      
      if (!user) {
        debugLog('익명 사용자이므로 진행율 기록을 건너뜁니다.')
        return
      }
      
      // 캐시된 진행율 기록 확인 (5분 내에 이미 기록했는지)
      const lastRecordTime = sessionStorage.getItem('lastStudyProgressRecord')
      const now = Date.now()
      if (lastRecordTime && (now - parseInt(lastRecordTime)) < 5 * 60 * 1000) {
        debugLog('최근에 이미 진행율을 기록했으므로 건너뜁니다.')
        return
      }
      
      try {
        debugLog('모든 스터디의 진행율 기록 시작')
        
        // 모든 스터디 ID를 한 번에 전송
        const studyIds = this.studies.map(study => study.id)
        if (studyIds.length > 0) {
          await axios.post('/api/record-study-progress/', {
            study_ids: studyIds,
            page_type: 'study-management'
          })
          
          // 기록 시간 저장
          sessionStorage.setItem('lastStudyProgressRecord', now.toString())
        }
              } catch (error) {
          debugLog('전체 스터디 진행율 기록 실패:', error, 'error')
        }
    },
    async recordStudyProgress(studyId, pageType) {
      // 인증되지 않은 사용자는 진행율 기록하지 않음
      if (!this.isAuthenticated) {
        debugLog('인증되지 않은 사용자 - 진행율 기록 건너뜀')
        return
      }
      
      try {
        await axios.post('/api/record-study-progress/', {
          study_id: studyId,
          page_type: pageType
        })
              } catch (error) {
          debugLog('진행율 기록 실패:', error, 'error')
        }
    },
    
    // 캐시 관련 메서드들
    getCachedData() {
      try {
        const user = this.getCurrentUser()
        // 스터디 타입 필터, 공개 필터, 선택된 태그를 조합하여 캐시 키 생성
        const studyTypeValue = this.studyTypeFilter || 'my'
        const publicFilterValue = this.publicFilter || 'all'
        const selectedTagsValue = this.selectedTags && this.selectedTags.length > 0 ? this.selectedTags.sort().join(',') : 'no-tags'
        const cacheKey = `studyManagement_${user ? user.role : 'anonymous'}_${studyTypeValue}_${publicFilterValue}_${selectedTagsValue}`
        debugLog('캐시 키 확인:', cacheKey)
        
        const cached = sessionStorage.getItem(cacheKey)
        if (cached) {
          const data = JSON.parse(cached)
          // 캐시 유효성 검사 (5분)
          const now = Date.now()
          if (now - data.timestamp < 5 * 60 * 1000) {
            debugLog('유효한 캐시 데이터 발견:', cacheKey)
            return data
          } else {
            debugLog('캐시 데이터가 만료됨:', cacheKey)
          }
        } else {
          debugLog('캐시 데이터 없음:', cacheKey)
        }
              } catch (error) {
          debugLog('캐시 데이터 파싱 오류:', error, 'error')
        }
      return null
    },
    
    cacheData() {
      // Profile.vue의 캐시 설정 확인
      if (!isCacheEnabled()) {
        debugLog('캐시가 비활성화되어 있어 저장하지 않습니다.')
        return
      }
      
      try {
        // 캐시 저장 전에 오래된 캐시 정리
        this.cleanupOldCache()
        
        const user = this.getCurrentUser()
        const studyTypeValue = this.studyTypeFilter || 'my'
        const publicFilterValue = this.publicFilter || 'all'
        const selectedTagsValue = this.selectedTags && this.selectedTags.length > 0 ? this.selectedTags.sort().join(',') : 'no-tags'
        const cacheKey = `studyManagement_${user ? user.role : 'anonymous'}_${studyTypeValue}_${publicFilterValue}_${selectedTagsValue}`
        const data = {
          studies: this.studies.slice(0, 50), // 최대 50개 스터디만 캐시
          studyTypeFilter: this.studyTypeFilter,
          publicFilter: this.publicFilter,
          timestamp: Date.now()
        }
        
        const cacheString = JSON.stringify(data)
        
        // 캐시 크기 확인 (3MB 제한)
        if (cacheString.length > 3 * 1024 * 1024) {
          debugLog('스터디 관리 캐시 데이터가 너무 큽니다. 캐시를 저장하지 않습니다.', null, 'warn')
          return
        }
        
        // Profile.vue의 캐시 설정에 따라 캐시 저장
        if (setSessionCache(cacheKey, data)) {
          debugLog('스터디 관리 데이터 캐시 저장됨:', cacheKey, '(크기:', Math.round(cacheString.length / 1024), 'KB)')
        } else {
          debugLog('캐시가 비활성화되어 데이터를 저장하지 않습니다.')
        }
      } catch (error) {
        debugLog('캐시 저장 오류:', error, 'error')
        this.clearCache()
      }
    },
    

    
    clearCache() {
      // Profile.vue의 캐시 설정에 따라 캐시 정리
      if (isCacheEnabled()) {
        // 모든 스터디 관리 관련 캐시 삭제
        const keys = Object.keys(sessionStorage)
        keys.forEach(key => {
          if (key.startsWith('studyManagement_')) {
            removeSessionCache(key)
          }
        })

        // 추가로 스터디 관련 모든 캐시 정리
        this.clearStudyCache()
        
        debugLog('스터디 관리 데이터 캐시 삭제됨')
      } else {
        debugLog('캐시가 비활성화되어 정리 작업을 건너뜁니다.')
      }
    },
    
    clearStudyCache() {
      try {
        // Profile.vue의 캐시 설정에 따라 스터디 관련 캐시 정리
        if (isCacheEnabled()) {
          // 스터디 관련 모든 캐시 정리
          const sessionKeys = Object.keys(sessionStorage)
          const localKeys = Object.keys(localStorage)
          let deletedCount = 0
          
          // sessionStorage 정리
          sessionKeys.forEach(key => {
            if (key.includes('study') || key.includes('Study') || key.includes('Management')) {
              removeSessionCache(key)
              deletedCount++
            }
          })
          
          // localStorage 정리
          localKeys.forEach(key => {
            if (key.includes('study') || key.includes('Study') || key.includes('Management')) {
              removeLocalCache(key)
              deletedCount++
            }
          })
          
          // 강제 새로고침 플래그 설정
          setSessionCache('forceRefreshStudyManagement', true)
          setSessionCache('forceRefreshHome', true)
          
          debugLog(`스터디 관련 모든 캐시 정리 완료: ${deletedCount}개 항목 삭제`)
        } else {
          debugLog('캐시가 비활성화되어 스터디 관련 캐시 정리를 건너뜁니다.')
        }
      } catch (error) {
        debugLog('스터디 관련 캐시 정리 중 오류:', error, 'error')
      }
    },
    
    cleanupOldCache() {
      try {
        // 모든 캐시 키 확인
        const keys = Object.keys(sessionStorage)
        const now = Date.now()
        const maxAge = 10 * 60 * 1000 // 10분
        
        keys.forEach(key => {
          if (key.includes('Cache') || key.includes('Data') || key.startsWith('studyManagement_')) {
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
    
    getCurrentUser() {
      return getCurrentUserFromPermissions()
    },
    
    // 데이터 새로고침 메서드
    async refreshData() {
      this.loading = true
      try {
        this.clearCache()
        await this.loadStudies()
      } finally {
        this.loading = false
      }
    },
    

    
    // 스터디 멤버 여부 확인
    isStudyMember(study) {
      const user = this.getCurrentUser()
      if (!user) return false
      
      return study.members && Array.isArray(study.members) &&
        study.members.some(member => {
          if (!member.user) return false
          const memberUserId = typeof member.user === 'object' ? member.user.id : member.user
          return String(memberUserId) === String(user.id)
        })
    },
    
    // 가입 요청 보내기
    async requestJoinStudy(study) {
      // 로그인하지 않은 사용자인 경우 로그인 화면으로 이동
      if (!this.isAuthenticated) {
        this.$router.push('/login')
        return
      }
      
      // 모달로 메시지 입력 받기
      this.showConfirmModal(
        this.$t('studyManagement.messages.joinRequestTitle'),
        this.$t('studyManagement.messages.enterJoinMessage'),
        this.$t('studyManagement.messages.send'),
        this.$t('studyManagement.messages.cancel'),
        'btn-primary',
        'fas fa-user-plus',
        async (message) => {
          try {
            const joinMessage = message || ''
            
            const response = await axios.post('/api/study-join-request/', {
              study_id: study.id,
              message: joinMessage
            })
            
            this.showToastNotification(this.$t('studyManagement.messages.joinRequestSent'), 'success')
            
            // 가입 요청 상태 업데이트
            this.joinRequests[study.id] = response.data.join_request_id
            
            // 스터디 목록 새로고침
            await this.loadStudies()
          } catch (error) {
            debugLog('가입 요청 실패:', error, 'error')
            
            // 인증 오류인 경우 로그인 화면으로 이동
            if (error.response && error.response.status === 401) {
              this.$router.push('/login')
              return
            }
            
            if (error.response && error.response.data && error.response.data.error) {
              const errorMessage = error.response.data.error
              if (errorMessage && errorMessage.trim()) {
                this.showToastNotification(errorMessage, 'error')
              } else {
                this.showToastNotification(this.$t('studyManagement.messages.joinRequestFailed'), 'error')
              }
            } else {
              this.showToastNotification(this.$t('studyManagement.messages.joinRequestFailed'), 'error')
            }
          }
        },
        'join-request' // modalType 추가
      )
    },
    
    // 가입 요청 취소
    async cancelJoinRequest(study) {
      // 로그인하지 않은 사용자인 경우 로그인 화면으로 이동
      if (!this.isAuthenticated) {
        this.$router.push('/login')
        return
      }
      
      this.showConfirmModal(
        this.$t('studyManagement.messages.cancelRequestTitle'),
        this.$t('studyManagement.messages.confirmCancelRequest'),
        this.$t('studyManagement.messages.cancel'),
        this.$t('studyManagement.messages.back'),
        'btn-warning',
        'fas fa-times',
        async () => {
          try {
            const requestId = this.joinRequests[study.id]
            if (!requestId) {
              this.showToastNotification(this.$t('studyManagement.messages.requestNotFound'), 'error')
              return
            }
            
            await axios.delete(`/api/study-join-request/${requestId}/cancel/`)
            
            this.showToastNotification(this.$t('studyManagement.messages.joinRequestCancelled'), 'success')
            
            // 가입 요청 상태 제거
            delete this.joinRequests[study.id]
            
            // 스터디 목록 새로고침
            await this.loadStudies()
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
              this.showToastNotification(this.$t('studyManagement.messages.cancelRequestFailed'), 'error')
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
    }
  }
}
</script>

<style scoped>
/* Modern Study Management Styles */
.study-management {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 10px;
}

.container {
  max-width: 1400px;
  margin: 0 auto;
  background: white;
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  padding: 0;
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

.action-btn-success {
  border-color: #28a745;
  background: #28a745;
  color: white;
}

.action-btn-success:hover:not(:disabled) {
  background: #218838;
  border-color: #1e7e34;
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

/* Page Title */
.page-title {
  padding: 20px 30px 20px;
  background: white;
}

.page-title h1 {
  margin: 0;
  font-size: 2.5rem;
  font-weight: 700;
  color: #2c3e50;
  text-align: center;
}

/* Card Styles */
.card-modern {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  padding: 20px;
  margin: 10px 30px;
  border: 1px solid #e9ecef;
}

.card-header-modern {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #f8f9fa;
}

.card-header-modern h3 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: #2c3e50;
}

.card-action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border: 2px solid #e9ecef;
  border-radius: 20px;
  background: white;
  color: #6c757d;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.card-action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  color: #dc3545;
  border-color: #dc3545;
}

/* Study Form */
.study-form {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(66, 165, 245, 0.1);
  padding: 30px;
  margin: 20px 30px;
  border: 2px solid #e3f2fd;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #2c3e50;
  font-size: 14px;
}

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

.form-check {
  display: flex;
  align-items: center;
  gap: 10px;
}

.form-check-input {
  width: 18px;
  height: 18px;
  border: 2px solid #e9ecef;
  border-radius: 4px;
  cursor: pointer;
}

.form-check-label {
  font-weight: 500;
  color: #2c3e50;
  cursor: pointer;
}

/* Filter Controls */
.filter-controls {
  background: #f8fafc;
  border-radius: 12px;
  padding: 15px;
  margin: 10px 30px;
  border: 1px solid #e9ecef;
}

@media (max-width: 768px) {
  .filter-controls {
    padding-top: 10px;
    padding-bottom: 10px;
  }
  
  /* 모바일에서 Study Type 라벨 숨기기 */
  .filter-controls .form-label {
    display: none;
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
  .btn-outline-primary.btn-sm:has(.fa-tags),
  .btn-outline-primary.tag-filter-btn:has(.fa-tags) {
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
  
  .btn-outline-primary.btn-sm:has(.fa-tags) i,
  .btn-outline-primary.tag-filter-btn:has(.fa-tags) i {
    font-size: 14px !important;
    line-height: 1 !important;
    margin: 0 !important;
  }
  
  .btn-outline-primary.btn-sm:has(.fa-tags) span:not(.badge),
  .btn-outline-primary.btn-sm:has(.fa-tags) > :not(i):not(.badge),
  .btn-outline-primary.tag-filter-btn:has(.fa-tags) span:not(.badge),
  .btn-outline-primary.tag-filter-btn:has(.fa-tags) > :not(i):not(.badge) {
    display: none !important;
  }
  
  .btn-outline-primary.btn-sm:has(.fa-tags) .badge,
  .btn-outline-primary.tag-filter-btn:has(.fa-tags) .badge {
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

.filter-controls .row {
  margin: 0;
}

.filter-controls .col-md-3,
.filter-controls .col-md-6 {
  padding: 0 10px;
}

.filter-controls .col-md-6 {
  display: flex;
  justify-content: flex-end;
}

.create-study-btn {
  min-width: 120px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-weight: 600;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.create-study-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
}

.form-label {
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 8px;
  font-size: 14px;
}

/* Table Styles */
.table-responsive {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  margin: 10px 30px;
  overflow: hidden;
}

@media (max-width: 768px) {
  .table-responsive {
    padding-top: 0px;
  }
}

.table {
  margin: 0;
  border-collapse: separate;
  border-spacing: 0;
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
}

.table tbody tr {
  transition: all 0.3s ease;
}

.table tbody tr:hover {
  background: #f8fafc;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* Study Title Link */
.study-title-link {
  color: #007bff;
  text-decoration: none;
  font-weight: 700;
  transition: all 0.3s ease;
  padding: 6px 10px;
  border-radius: 8px;
  display: inline-block;
  position: relative;
  cursor: pointer;
}

.study-title-link:hover {
  color: #0056b3;
  background: rgba(0, 123, 255, 0.1);
  text-decoration: none;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.2);
}

.study-title-link:active {
  color: #004085;
  transform: translateY(0);
}

/* Progress Link */
.progress-link {
  color: #28a745;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.3s ease;
  padding: 4px 8px;
  border-radius: 6px;
}

.progress-link:hover {
  color: #218838;
  background: rgba(40, 167, 69, 0.1);
  text-decoration: none;
}

/* Badge Styles */
.badge {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.bg-success {
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%) !important;
}

.bg-secondary {
  background: linear-gradient(135deg, #6c757d 0%, #495057 100%) !important;
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

.btn-outline-danger {
  border-color: #dc3545;
  color: #dc3545;
  background: white;
}

.btn-outline-danger:hover {
  background: #dc3545;
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

/* Alert Styles */
.alert {
  border-radius: 12px;
  padding: 16px 20px;
  margin: 10px 30px;
  border: none;
  font-weight: 500;
}

.alert-info {
  background: linear-gradient(135deg, #17a2b8 0%, #20c997 100%);
  color: white;
}

/* Calendar Styles */
.calendar-container {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  padding: 15px;
  margin: 10px 30px;
  border: 1px solid #e9ecef;
}

.calendar-label {
  font-size: 1.3rem;
  font-weight: 700;
  color: #2c3e50;
  text-align: center;
  margin-bottom: 15px;
}

.calendar-table {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.calendar-table th {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-weight: 600;
  padding: 12px 8px;
  border: none;
  text-align: center;
}

.calendar-table td {
  width: 40px;
  height: 60px;
  text-align: left;
  vertical-align: top;
  position: relative;
  padding: 4px;
  border: 1px solid #f8f9fa;
  transition: all 0.3s ease;
}

.calendar-table td:hover {
  background: #f8fafc;
}

.calendar-table td.bg-light {
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%) !important;
  font-weight: bold;
}

.calendar-table td.text-muted {
  color: #adb5bd;
}

.calendar-table td.selected-date-start {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  color: white;
  font-weight: bold;
}

.calendar-table td.selected-date-end {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  color: white;
  font-weight: bold;
}

.calendar-table td.selected-date-range {
  background: rgba(102, 126, 234, 0.2) !important;
}

.calendar-table td.selected-date-start .calendar-date-label,
.calendar-table td.selected-date-end .calendar-date-label {
  color: white;
}

.calendar-date-label {
  font-size: 0.9em;
  font-weight: 600;
  margin-bottom: 2px;
  z-index: 2;
  position: relative;
  line-height: 1.1;
  color: #2c3e50;
}

.calendar-bars {
  position: relative;
  min-height: 12px;
}

.calendar-bar {
  position: absolute;
  left: 0;
  right: 0;
  height: 6px;
  border-radius: 4px;
  opacity: 0.9;
  z-index: 1;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.calendar-bar-more {
  position: absolute;
  left: 0;
  right: 0;
  height: 10px;
  font-size: 0.7em;
  color: #6c757d;
  background: #f8f9fa;
  border-radius: 6px;
  text-align: center;
  line-height: 10px;
  z-index: 2;
  pointer-events: none;
  border: 1px solid #e9ecef;
}

.study-color-bullet {
  display: inline-block;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  margin-right: 10px;
  vertical-align: middle;
  border: 2px solid #e9ecef;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* Loading Styles */
.loading-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100vh;
  color: white;
}

.spinner-border {
  width: 3rem;
  height: 3rem;
}

/* Tag Filter Styles */
.tag-filter-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.2s;
  border: 1px solid #007bff;
  background-color: transparent;
  color: #007bff;
}

.tag-filter-btn:hover {
  background-color: #007bff;
  color: white;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 123, 255, 0.2);
}

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

/* Responsive Design */
@media (max-width: 768px) {
  .container {
    margin: 0;
    border-radius: 20px;
  }
  
  .card-modern,
  .study-form,
  .filter-controls,
  .table-responsive {
    margin: 1px;
    padding: 15px;
  }
  
  .page-title h1 {
    font-size: 2rem;
  }
  
  .header-actions {
    flex-direction: column;
    gap: 8px;
  }
  
  /* 원형 버튼 스타일은 공통 CSS (mobile-buttons.css)에서 처리됨 */
  
  /* 토스트 알림 스타일 - 기본 스타일은 공통 CSS (mobile-buttons.css)에 정의됨 */
  
  /* 타입별 스타일은 공통 CSS (mobile-buttons.css)에 정의됨 */
  
  .toast-content {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex: 1;
  }
  
  .toast-close {
    background: none;
    border: none;
    color: #6c757d;
    cursor: pointer;
    padding: 0.25rem;
    border-radius: 4px;
    transition: all 0.2s;
  }
  
}

/* 모달 스타일 */
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
  z-index: 1001;
  animation: fadeIn 0.3s ease;
}

.modal-content {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow: hidden;
  animation: slideInUp 0.3s ease;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem 2rem;
  border-bottom: 1px solid #e9ecef;
  background: #f8f9fa;
}

.modal-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: #6c757d;
  padding: 0.5rem;
  border-radius: 50%;
  transition: all 0.2s;
}

.modal-close:hover {
  background: #e9ecef;
  color: #495057;
}

.modal-body {
  padding: 2rem;
}

.modal-footer {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  padding: 1.5rem 2rem;
  border-top: 1px solid #e9ecef;
  background: #f8f9fa;
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

/* 모바일 카드 스타일 */
.mobile-study-cards {
  display: none; /* 기본적으로 숨김 */
  grid-template-columns: 1fr;
  gap: 15px;
  margin-top: 20px;
  padding: 0 10px;
  width: 100%;
  box-sizing: border-box;
  max-width: 100vw;
  overflow-x: hidden;
}

@media (max-width: 768px) {
  .mobile-study-cards {
    margin-top: 10px;
  }
}

.mobile-study-card {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 15px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  min-height: 140px;
  width: 100%;
  box-sizing: border-box;
  overflow: hidden;
}

@media (max-width: 768px) {
  .mobile-study-card {
    padding-top: 10px;
    padding-bottom: 10px;
  }
}

.mobile-study-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
}

.mobile-study-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  gap: 10px;
  width: 100%;
}

@media (max-width: 768px) {
  .mobile-study-card-header {
    margin-bottom: 0px;
  }
}

.mobile-study-title-section {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.mobile-study-color-bullet {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.mobile-study-title-link {
  text-decoration: none;
  color: #007bff;
  flex: 1;
  min-width: 0;
  font-weight: 700;
  transition: all 0.3s ease;
  padding: 4px 8px;
  border-radius: 6px;
  display: block;
}

.mobile-study-title-link:hover {
  text-decoration: none;
  color: #0056b3;
  background: rgba(0, 123, 255, 0.1);
  transform: translateY(-1px);
}

.mobile-study-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: inherit; /* 링크 색상 상속 */
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.mobile-study-progress {
  background: #e9ecef;
  color: #495057;
  padding: 4px 8px;
  border-radius: 10px;
  font-size: 0.8rem;
  font-weight: 600;
  min-width: 60px;
  text-align: center;
  flex-shrink: 0;
}

.mobile-study-info {
  font-size: 0.85rem;
  color: #6c757d;
  margin-bottom: 10px;
  display: flex;
  flex-direction: column;
  gap: 5px;
  width: 100%;
}

.mobile-study-date-progress {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
}

@media (max-width: 768px) {
  .mobile-study-info {
    margin-bottom: 0px;
  }
}

.mobile-study-date {
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin: 0;
  flex: 1;
}

.mobile-study-status {
  align-self: center;
  display: flex;
  justify-content: center;
  width: 100%;
}

.mobile-study-badge {
  padding: 3px 8px;
  border-radius: 10px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.mobile-study-badge.public {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.mobile-study-badge.private {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.mobile-study-actions {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-top: 12px;
  width: 100%;
  flex-wrap: wrap;
}

@media (max-width: 768px) {
  .mobile-study-actions {
    margin-top: 0px;
  }
}

.mobile-study-btn {
  flex: 1;
  padding: 10px 12px;
  border: none;
  border-radius: 15px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  text-align: center;
  text-decoration: none;
  transition: all 0.2s ease;
  white-space: nowrap;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1.2;
}

.mobile-study-btn.view {
  background: #007bff;
  color: white;
  font-weight: 600;
}

.mobile-study-btn.view:hover {
  background: #0056b3;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3);
}

.mobile-study-btn.progress {
  background: #6f42c1;
  color: white;
  font-weight: 600;
}

.mobile-study-btn.progress:hover {
  background: #5a32a3;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(111, 66, 193, 0.3);
}

.mobile-study-btn.delete {
  background: #dc3545;
  color: white;
  font-weight: 600;
}

.mobile-study-btn.delete:hover {
  background: #c82333;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(220, 53, 69, 0.3);
}

.mobile-study-btn.join {
  background: #28a745;
  color: white;
  font-weight: 600;
}

.mobile-study-btn.join:hover {
  background: #218838;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
}

.mobile-study-btn.cancel {
  background: #ffc107;
  color: #212529;
  font-weight: 600;
}

.mobile-study-btn.cancel:hover {
  background: #e0a800;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 193, 7, 0.3);
}

.mobile-join-btn {
  flex-shrink: 0;
  padding: 6px 12px;
  font-size: 0.8rem;
  min-height: 32px;
  white-space: nowrap;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

@media (max-width: 768px) {
  .mobile-join-btn-text {
    display: none;
  }
  
  .mobile-join-btn {
    padding: 6px;
    min-width: 32px;
    width: 32px;
    height: 32px;
  }
  
  .mobile-join-btn i {
    margin: 0;
  }
}

/* 모바일에서 테이블 숨기고 카드 보이기 */
@media (max-width: 768px) {
  .desktop-table {
    display: none;
  }
  
  .mobile-study-cards {
    display: grid;
  }
  
  .study-management {
    overflow-x: hidden;
    width: 100%;
    box-sizing: border-box;
  }
  
  .container {
    overflow-x: hidden;
    overflow-y: visible;
    width: 100%;
    box-sizing: border-box;
    padding: 0 10px;
    position: relative;
  }
  
  .filter-controls {
    overflow-x: hidden;
    overflow-y: visible;
    box-sizing: border-box;
    margin: 1px;
    position: relative;
    /* 모바일에서 select 드롭다운이 잘리지 않도록 */
    isolation: isolate;
  }
  
  .filter-controls select {
    margin-bottom: 10px;
    position: relative;
    z-index: 10;
  }
  
  /* 모바일에서 select 드롭다운이 올바른 위치에 표시되도록 */
  .filter-controls .col-md-3,
  .filter-controls .col-md-6 {
    position: relative;
    z-index: 1;
    overflow: visible;
  }
  
  .filter-controls .col-md-3 select:focus,
  .filter-controls .col-md-6 select:focus {
    z-index: 1000;
    position: relative;
    outline: none;
  }
  
  /* select의 부모 요소에서 overflow 제한 */
  .filter-controls .form-group {
    position: relative;
    overflow: visible;
  }
  
  .filter-controls .row {
    flex-direction: column;
  }
  
  .filter-controls .col-md-3,
  .filter-controls .col-md-6 {
    width: 100%;
    margin-bottom: 15px;
  }
  
  .filter-controls .col-md-6 {
    justify-content: flex-end;
  }
  
  .tag-filter-btn {
    font-size: 0 !important;
    padding: 0 !important;
    gap: 0 !important;
    width: 40px !important;
    height: 40px !important;
    min-width: 40px !important;
    min-height: 40px !important;
    max-width: 40px !important;
    max-height: 40px !important;
    border-radius: 50% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex-shrink: 0 !important;
  }
  
  .tag-filter-btn i {
    font-size: 1rem !important;
    margin: 0 !important;
  }
  
  .tag-filter-btn .badge {
    font-size: 0.75rem;
    margin-left: 4px;
  }
  
  /* 태그 필터 버튼 텍스트 숨기기 */
  .tag-filter-btn > :not(i):not(.badge) {
    display: none !important;
  }
  
  /* 모바일에서 날짜 범위 필터 스타일 */
  .date-range-filter {
    flex-wrap: wrap;
    width: 100%;
    margin-bottom: 11px;
  }
  
  .date-range-badge {
    flex: 0 1 auto;
    min-width: 0;
    max-width: 100%;
    font-size: 0.75rem;
    padding: 4px 6px 4px 6px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    display: flex;
    align-items: center;
    gap: 3px;
    margin-left: 30px;
  }
  
  /* 모바일에서 캘린더 아이콘 숨기기 */
  .date-range-icon {
    display: none;
  }
  
  .date-range-text {
    display: flex;
    align-items: center;
    min-width: 0;
    flex: 1;
  }
  
  .date-range-text .date-start,
  .date-range-text .date-end {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .date-range-text .date-separator {
    margin: 0 1px;
    flex-shrink: 0;
  }
  
  /* 날짜 범위 배지 오른쪽 공백 제거 */
  .date-range-text > span:last-child {
    margin-right: 0;
    padding-right: 0;
  }
  
  /* 모바일에서 X 버튼 숨기기 */
  .date-range-clear-btn {
    display: none !important;
  }
  
  /* 모바일에서 col-md-9 패딩 제거 */
  .filter-controls .col-md-9.d-flex {
    padding-left: 0px;
    padding-right: 0px;
  }
  
  /* create-study-btn, mobile-study-btn 스타일은 공통 CSS (mobile-buttons.css)에서 처리됨 */
  
  .calendar-container {
    overflow-x: hidden;
    box-sizing: border-box;
    margin: 1px;
    padding: 15px;
  }
  
  .calendar-table {
    width: 100%;
    font-size: 0.9rem;
  }
  
  .calendar-table th,
  .calendar-table td {
    padding: 8px 4px;
  }
  
  .calendar-table td {
    width: auto;
    height: 50px;
  }
  
  .page-title {
    padding: 20px 15px 15px;
  }
  
  .card-modern {
    margin: 5px;
    padding: 15px;
  }
  
  .table-responsive {
    margin: 5px;
  }
  
  /* 모달 푸터 버튼을 원형 버튼으로 */
  .modal-footer .action-btn {
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
  
  .modal-footer .action-btn i {
    font-size: 14px !important;
    line-height: 1 !important;
    color: white !important;
  }
  
  .modal-footer .action-btn-secondary i {
    color: #6c757d !important;
  }
  
  .modal-footer .action-btn-secondary:hover i {
    color: white !important;
  }
  
  .modal-footer .action-btn.btn-danger {
    background-color: #dc3545 !important;
    border-color: #dc3545 !important;
  }
  
  .modal-footer .action-btn.btn-danger i {
    color: white !important;
  }
  
  .modal-footer .action-btn.btn-danger:hover {
    background-color: #c82333 !important;
    border-color: #bd2130 !important;
  }
  
  .modal-footer .action-btn span {
    display: none !important;
  }
}

@media (max-width: 576px) {
  .modal-footer .action-btn {
    width: 36px !important;
    height: 36px !important;
  }
  
  .modal-footer .action-btn i {
    font-size: 12px !important;
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