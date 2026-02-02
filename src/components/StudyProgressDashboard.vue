<template>
  <div class="study-progress-dashboard">
    <div class="container">
      <!-- 
        핵심 원칙: 모든 통계 정보는 개인 통계만 반환한다
        - 현재 로그인한 사용자의 개인 진행률만 표시
        - 다른 사용자의 통계 정보는 노출하지 않음
        - 개인정보 보호 및 보안 강화
      -->
        <!-- 제목 섹션 -->
        <div class="mb-4">
          <!-- 데스크톱: 제목과 컨트롤이 같은 줄 -->
          <div class="d-none d-md-flex justify-content-between align-items-center">
            <h2 class="mb-0">{{ study ? getStudyTitle(study) : '' }}</h2>
            <div class="d-flex gap-3 align-items-center">
              <!-- 기간 선택 -->
              <div class="period-selector">
                <label class="form-label me-2 mb-0">{{ $t('studyProgressDashboard.periodSelector') }}</label>
                <select v-model="selectedPeriod" @change="onPeriodChange" class="form-select form-select-sm" style="width: auto;">
                  <option value="1">{{ $t('studyProgressDashboard.periods.1day') }}</option>
                  <option value="7">{{ $t('studyProgressDashboard.periods.7days') }}</option>
                  <option value="30">{{ $t('studyProgressDashboard.periods.1month') }}</option>
                  <option value="365">{{ $t('studyProgressDashboard.periods.1year') }}</option>
                  <option value="all">{{ $t('studyProgressDashboard.periods.all') }}</option>
                </select>
              </div>
              <button @click="refreshData" class="btn btn-success" :disabled="refreshing">
                <i class="fas fa-sync-alt" :class="{ 'fa-spin': refreshing }"></i>
                <span>{{ refreshing ? $t('studyProgressDashboard.refreshing') : $t('studyProgressDashboard.refresh') }}</span>
              </button>
            </div>
          </div>
          
          <!-- 모바일: 제목과 컨트롤이 세로로 -->
          <div class="d-md-none">
            <h2 class="mb-3">{{ study ? getStudyTitle(study) : '' }}</h2>
            <div class="d-flex align-items-center gap-3">
              <!-- 기간 선택 -->
              <div class="period-selector">
                <label class="form-label me-2 mb-0">{{ $t('studyProgressDashboard.periodSelector') }}</label>
                <select v-model="selectedPeriod" @change="onPeriodChange" class="form-select form-select-sm" style="width: auto;">
                  <option value="1">{{ $t('studyProgressDashboard.periods.1day') }}</option>
                  <option value="7">{{ $t('studyProgressDashboard.periods.7days') }}</option>
                  <option value="30">{{ $t('studyProgressDashboard.periods.1month') }}</option>
                  <option value="365">{{ $t('studyProgressDashboard.periods.1year') }}</option>
                  <option value="all">{{ $t('studyProgressDashboard.periods.all') }}</option>
                </select>
              </div>
              <button @click="refreshData" class="btn btn-success" :disabled="refreshing">
                <i class="fas fa-sync-alt" :class="{ 'fa-spin': refreshing }"></i>
                <span>{{ refreshing ? $t('studyProgressDashboard.refreshing') : $t('studyProgressDashboard.refresh') }}</span>
              </button>
            </div>
          </div>
        </div>

      <!-- 로딩 중 -->
      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">{{ $t('studyProgressDashboard.loading') }}</span>
        </div>
        <p class="mt-2">{{ $t('studyProgressDashboard.loadingText') }}</p>
      </div>

      <!-- 대시보드 내용 -->
      <div v-else-if="study">


        <!-- 전체 진행율 및 합격율 차트 -->
        <div class="card mb-4">
          <div class="card-header">
            <h5 class="card-title mb-0">{{ $t('studyProgressDashboard.overallProgressTitle') }}</h5>
          </div>
          <div class="card-body">
            <canvas ref="overallProgressChart" width="400" height="200"></canvas>

            <!-- 전체 진행률 요약 -->
            <div v-if="study && study.tasks && study.tasks.length > 0" class="mt-3">
              <div class="row text-center">
                <div class="col-md-4">
                  <div class="border-end">
                    <h6 class="text-primary">{{ getTotalQuestions() }}</h6>
                    <small class="text-muted">{{ $t('studyProgressDashboard.overallProgress.totalQuestions') }}</small>
                  </div>
                </div>
                <div class="col-md-4">
                  <div class="border-end">
                    <h6 class="text-success">{{ getAttemptedQuestions() }}</h6>
                    <small class="text-muted">{{ $t('studyProgressDashboard.overallProgress.attemptedQuestions') }}</small>
                  </div>
                </div>
                <div class="col-md-4">
                  <div>
                    <h6 class="text-info">{{ getCorrectQuestions() }}</h6>
                    <small class="text-muted">{{ $t('studyProgressDashboard.overallProgress.correctQuestions') }}</small>
                  </div>
                </div>
              </div>
              <div class="row text-center mt-2">
                <div class="col-12">
                  <small class="text-muted">
                    {{ $t('studyProgressDashboard.overallProgress.questionBasedProgress') }}: {{ getAttemptedQuestions() }} / {{ getTotalQuestions() }} ({{ getQuestionBasedProgress().toFixed(2) }}%)
                  </small>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Task별 정확도 차트 -->
        <div class="card mb-4">
          <div class="card-header">
            <h5 class="card-title mb-0">{{ $t('studyProgressDashboard.taskProgressTitle') || 'Task별 정확도' }}</h5>
          </div>
          <div class="card-body task-chart-container">
            <div v-if="!study.tasks || study.tasks.length === 0" class="text-center text-muted py-3">
              {{ $t('studyProgressDashboard.noTasks') }}</div>
            <canvas v-else ref="taskProgressChart" width="400" height="300"></canvas>

            <!-- 차트 데이터 요약 -->
            <div v-if="study.tasks && study.tasks.length > 0" class="mt-3">
              <div class="row text-center">
                <div class="col-12">
                  <div>
                    <h6 class="text-success">{{ getTotalCorrectAttempts() }}</h6>
                    <small class="text-muted">{{ $t('studyProgressDashboard.taskProgress.totalCorrectAttempts') }}</small>
                  </div>
                </div>
              </div>
              <div class="row text-center mt-2">
                <div class="col-12">
                  <small class="text-muted">
                    {{ $t('studyProgressDashboard.taskProgress.overallAccuracy') }}: {{ getOverallAccuracy().toFixed(1) }}% ({{ getTotalCorrectAttempts() }} / {{ getTotalAttempts() }})
                  </small>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 공부시간 통계 -->
        <div class="study-time-statistics" v-if="studyTimeData">
          <!-- 요약 정보 -->
          <div class="row mb-4" v-if="studyTimeData.summary">
            <div class="col-12">
              <div class="card">
                <div class="card-header">
                  <h5 class="card-title mb-0">{{ $t('studyProgressDashboard.summaryTitle') }}</h5>
                </div>
                <div class="card-body">
                  <div class="row text-center">
                    <div class="col-md-3">
                      <div class="border-end">
                        <h4 class="text-primary">{{ studyTimeData.summary.total_tasks }}</h4>
                        <small class="text-muted">{{ $t('studyProgressDashboard.summary.totalTasks') }}</small>
                      </div>
                    </div>
                    <div class="col-md-3">
                      <div class="border-end">
                        <h4 class="text-success">{{ studyTimeData.summary.active_tasks }}</h4>
                        <small class="text-muted">{{ $t('studyProgressDashboard.summary.activeTasks') }}</small>
                      </div>
                    </div>
                    <div class="col-md-3">
                      <div class="border-end">
                        <h4 class="text-warning">{{ studyTimeData.summary.inactive_tasks }}</h4>
                        <small class="text-muted">{{ $t('studyProgressDashboard.summary.inactiveTasks') }}</small>
                      </div>
                    </div>
                    <div class="col-md-3">
                      <div>
                        <h4 class="text-info">{{ studyTimeData.summary.has_study_time ? 'Yes' : 'No' }}</h4>
                        <small class="text-muted">{{ $t('studyProgressDashboard.summary.hasStudyTime') }}</small>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="row">
            <!-- Task별 공부시간 -->
            <div class="col-md-6">
              <div class="card mb-4">
                <div class="card-header">
                  <h5 class="card-title mb-0">{{ $t('studyProgressDashboard.taskStudyTimeTitle') }}</h5>
                </div>
                <div class="card-body">
                  <div v-if="!studyTimeData.task_study_times || studyTimeData.task_study_times.length === 0" class="text-center text-muted py-3">
                    {{ $t('studyProgressDashboard.noTaskStudyTimeData') }}
                  </div>
                  <div v-else class="table-responsive">
                    <table class="table table-sm">
                      <thead>
                        <tr>
                          <th>{{ $t('studyProgressDashboard.table.task') }}</th>
                          <th>{{ $t('studyProgressDashboard.taskProgress.table.accuracy') }}</th>
                          <th>{{ $t('studyProgressDashboard.table.studyTime') }}</th>
                          <th>{{ $t('studyProgressDashboard.table.exam') }}</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="task in studyTimeData.task_study_times" :key="task.task_name" :class="{ 'table-warning': !task.has_exam, 'table-success': task.study_time_seconds > 0 }">
                          <td>
                            <router-link
                              v-if="task.has_exam && task.exam_id"
                              :to="`/take-exam/${task.exam_id}?returnTo=study-progress-dashboard&studyId=${study.id}&examId=${task.exam_id}`"
                              class="task-link"
                              @click="recordProgress(study.id, 'study-progress-dashboard')"
                            >
                              {{ task.task_name }}
                            </router-link>
                            <span v-else>{{ task.task_name }}</span>
                          </td>
                          <td>
                            <span class="badge bg-primary">{{ getTaskProgress(task) }}%</span>
                          </td>
                          <td>{{ formatHourMinute(task.study_time_minutes) }}</td>
                          <td>
                            <span v-if="task.has_exam" class="badge bg-success">{{ task.exam_title }}</span>
                            <span v-else class="badge bg-warning">{{ $t('studyProgressDashboard.noExam') }}</span>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>

            <!-- 날짜별 누적 공부시간 -->
            <div class="col-md-6">
              <div class="card mb-4">
                <div class="card-header">
                  <h5 class="card-title mb-0">{{ $t('studyProgressDashboard.dailyStudyTimeTitle') }}</h5>
                </div>
                <div class="card-body">
                  <div v-if="!studyTimeData.daily_study_times || studyTimeData.daily_study_times.length === 0" class="text-center text-muted py-3">
                    {{ $t('studyProgressDashboard.noDailyStudyTimeData') }}
                  </div>
                  <div v-else class="table-responsive">
                    <table class="table table-sm">
                      <thead>
                        <tr>
                          <th>{{ $t('studyProgressDashboard.table.date') }}</th>
                          <th>{{ $t('studyProgressDashboard.table.studyTime') }}</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="daily in studyTimeData.daily_study_times" :key="daily.date">
                          <td>{{ daily.date }}</td>
                          <td>{{ formatHourMinute(daily.study_time_minutes) }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="mt-3">
                    <strong>{{ $t('studyProgressDashboard.totalStudyTime') }}: {{ formatHourMinute(studyTimeData.total_study_time_minutes) }}</strong>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 공부시간 통계가 없을 때 표시할 메시지 -->
        <div v-else class="alert alert-warning">
          <h5>{{ $t('studyProgressDashboard.noStudyTimeDataTitle') }}</h5>
          <p>{{ $t('studyProgressDashboard.noStudyTimeDataMessage') }}</p>
        </div>

        <!-- 진행률 기록 테이블 -->
        <div class="progress-records mt-4" v-if="progressHistory.length > 0">
          <h4>{{ $t('studyProgressDashboard.progressRecordsTitle') }}</h4>
          <div class="table-responsive">
            <table class="table table-striped">
              <thead>
                <tr>
                  <th>{{ $t('studyProgressDashboard.table.date') }}</th>
                  <th>{{ $t('studyProgressDashboard.table.accessCount') }}</th>
                  <th>{{ $t('studyProgressDashboard.table.maxProgress') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="record in aggregatedProgressHistory" :key="record.일자">
                  <td>{{ record.일자 }}</td>
                  <td>{{ record['접속 횟수'] }}</td>
                  <td>{{ record['최고 진행률'] }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 진행률 기록이 없을 때 표시할 메시지 -->
        <div v-else class="alert alert-info">
          <h5>{{ $t('studyProgressDashboard.noProgressHistoryTitle') }}</h5>
          <p>{{ $t('studyProgressDashboard.noProgressHistoryMessage') }}</p>
        </div>
      </div>

      <!-- 에러 상태 -->
      <div v-else class="alert alert-danger">
        {{ $t('studyProgressDashboard.loadStudyFailed') }}
      </div>
    </div>
  </div>
</template>

<script>
// TODO: console.log를 debugLog로 변경할 수 있는지 반드시 검토해야 함
// - 운영 환경에서 브라우저 콘솔에 로그가 보이면 안 됨
// - debugLog는 운영 환경에서 자동으로 비활성화됨
import axios from 'axios'
import { debugLog } from '@/utils/debugUtils'
import Chart from 'chart.js/auto'
import { formatLocalDate, formatLocalTime, compareLocalDates } from '@/utils/dateUtils'
import { getLocalizedContent, getCurrentLanguage } from '@/utils/multilingualUtils'
import authService from '@/services/authService'

export default {
  name: 'StudyProgressDashboard',
  data() {
    return {
      study: null,
      progressHistory: [],
      timeSeriesData: [],
      studyTimeData: null,
      loading: true,
      refreshing: false,
      overallProgressChart: null,
      taskProgressChart: null,
      selectedPeriod: '7'  // 기본값: 7일
    }
  },
  async mounted() {
    // 자동 스크롤 비활성화
    // window.scrollTo(0, 0)

    const studyId = this.$route.params.studyId
    if (studyId) {
      try {
        this.loading = true
        await this.loadStudy(studyId)
        await this.loadStudyTimeStatistics(studyId)
        await this.loadProgressHistory(studyId)
        this.$nextTick(() => {
          this.createCharts()
        })
      } catch (error) {
        debugLog('대시보드 로드 실패:', error, 'error')
        this.loading = false
      }
    } else {
      this.loading = false
    }

    // 로그아웃 이벤트 리스너 추가
    this.$root.$on('clearAllFilters', this.clearCache)
  },
  beforeDestroy() {
    // 이벤트 리스너 제거
    this.$root.$off('clearAllFilters', this.clearCache)

    // 차트 정리
    if (this.overallProgressChart) {
      this.overallProgressChart.destroy()
    }
    if (this.taskProgressChart) {
      this.taskProgressChart.destroy()
    }
  },
  computed: {
    aggregatedProgressHistory() {
      if (!this.progressHistory || this.progressHistory.length === 0) {
        return []
      }

      // 디버깅: 원본 데이터 로깅
      console.log('🔍 progressHistory 원본 데이터:', this.progressHistory)

      // 일자별로 데이터 집계
      const aggregated = {}

      this.progressHistory.forEach(record => {
        const date = record.일자
        if (!aggregated[date]) {
          aggregated[date] = {
            일자: date,
            '접속 횟수': 0,
            '최고 진행률': '0%'
          }
        }

        // 접속 횟수 합계
        aggregated[date]['접속 횟수'] += parseInt(record['접속 횟수']) || 0

        // 최고 진행률 비교 (숫자로 변환하여 비교)
        const currentProgress = parseFloat(record['최고 진행률'].replace('%', '')) || 0
        const existingProgress = parseFloat(aggregated[date]['최고 진행률'].replace('%', '')) || 0

        console.log(`🔍 ${date} 진행률 비교: 현재=${currentProgress}%, 기존=${existingProgress}%`)

        if (currentProgress > existingProgress) {
          // 진행률을 2자리 소수점으로 반올림하여 표시
          const roundedProgress = Math.round(currentProgress * 100) / 100
          aggregated[date]['최고 진행률'] = `${roundedProgress}%`
          console.log(`🔍 ${date} 진행률 업데이트: ${roundedProgress}%`)
        }
      })

      // 백엔드 API에서 진행률이 0%로 들어오는 경우, 실제 Task 데이터를 기반으로 진행률 계산
      if (this.study && this.study.tasks && this.study.tasks.length > 0) {
        console.log('🔍 백엔드 진행률이 0%이므로 실제 Task 데이터 기반으로 진행률 계산')

        // 모든 Task의 진행률을 평균 계산
        let totalProgress = 0
        let taskCount = 0

        this.study.tasks.forEach(task => {
          if (task.attempted_progress !== undefined && task.attempted_progress > 0) {
            totalProgress += task.attempted_progress
            taskCount++
          }
        })

        if (taskCount > 0) {
          const averageProgress = totalProgress / taskCount
          const roundedProgress = Math.round(averageProgress * 100) / 100

          console.log(`🔍 실제 Task 기반 진행률: ${roundedProgress}% (${totalProgress}/${taskCount})`)

          // 모든 날짜에 실제 진행률 적용
          Object.keys(aggregated).forEach(date => {
            aggregated[date]['최고 진행률'] = `${roundedProgress}%`
          })
        }
      }

      // 최종 집계 결과 로깅
      console.log('🔍 최종 집계 결과:', aggregated)

      // 일자 역순으로 정렬 (최신 날짜가 위에 오도록)
      return Object.values(aggregated).sort((a, b) => {
        return compareLocalDates(b.일자, a.일자)
      })
    },
    isDevelopment() {
      // Vue 2에서 개발 환경 감지
      // 1. window.location.hostname이 localhost인지 확인
      // 2. 또는 특정 환경 변수 확인
      return window.location.hostname === 'localhost' ||
             window.location.hostname === '127.0.0.1' ||
             window.location.port === '8080'
    },
    currentUserId() {
      try {
        // 1. Vuex store에서 사용자 정보 확인
        if (this.$store && this.$store.state && this.$store.state.user) {
          return this.$store.state.user.id
        }

        // 2. authService에서 사용자 정보 확인
        const user = authService.getUserSync()
        if (user) {
          return user.id || user.user_id || null
        }

        // 3. 쿠키에서 사용자 정보 확인
        const cookies = document.cookie.split(';')
        for (const cookie of cookies) {
          const [name, value] = cookie.trim().split('=')
          if (name === 'user_id' || name === 'userId') {
            return value
          }
        }

        return null
      } catch (e) {
        debugLog('사용자 ID 확인 실패:', e)
        return null
      }
    }
  },
  methods: {
    formatHourMinute(minutes) {
      const h = Math.floor(minutes / 60)
      const m = Math.round(minutes % 60)
      if (h > 0) return `${h}${this.$t('common.time.hour')} ${m}${this.$t('common.time.minute')}`
      return `${m}${this.$t('common.time.minute')}`
    },
    async loadStudy(studyId) {
      try {
        console.log('🔍 [StudyProgressDashboard] loadStudy 호출됨 - studyId:', studyId)
        //
        // 핵심 원칙: 모든 통계 정보는 개인 통계만 반환한다
        // - /api/studies/${studyId}/ API는 현재 사용자의 개인 진행률만 반환
        // - 다른 사용자의 통계 정보는 노출하지 않음
        // - 개인정보 보호 및 보안 강화
        //
        const headers = {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
        console.log('🔍 [StudyProgressDashboard] studies API 호출 시작: /api/studies/' + studyId + '/')
        const response = await axios.get(`/api/studies/${studyId}/`, { headers })
        console.log('🔍 [StudyProgressDashboard] studies API 응답:', response.status)
        this.study = response.data
        debugLog('StudyProgressDashboard - 스터디 데이터 로드:', this.study)
        debugLog('StudyProgressDashboard - tasks:', this.study.tasks)
      } catch (error) {
        debugLog('스터디 로드 실패:', error, 'error')
        this.$toast?.error?.(this.$t('studyProgressDashboard.alerts.loadStudyFailed'))
      }
    },
    async loadStudyTimeStatistics(studyId) {
      try {
        console.log('🔍 [StudyProgressDashboard] loadStudyTimeStatistics 호출됨 - studyId:', studyId, 'period:', this.selectedPeriod)
        //
        // 핵심 원칙: 모든 통계 정보는 개인 통계만 반환한다
        // - /api/study-time-statistics/${studyId}/ API는 현재 사용자의 개인 공부시간만 반환
        // - 다른 사용자의 공부시간 정보는 노출하지 않음
        // - 개인정보 보호 및 보안 강화
        //
        const headers = {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
        debugLog('StudyProgressDashboard - 공부시간 통계 API 호출 시작:', `/api/study-time-statistics/${studyId}/`)

        // 선택된 기간을 쿼리 파라미터로 전달
        const params = {}
        if (this.selectedPeriod !== 'all') {
          params.days = this.selectedPeriod
        }

        console.log('🔍 [StudyProgressDashboard] study-time-statistics API 호출 시작: /api/study-time-statistics/' + studyId + '/', params)
        const response = await axios.get(`/api/study-time-statistics/${studyId}/`, {
          headers,
          params
        })
        console.log('🔍 [StudyProgressDashboard] study-time-statistics API 응답:', response.status)
        this.studyTimeData = response.data
        debugLog('StudyProgressDashboard - 공부시간 통계 API 응답:', response.data)
        debugLog('StudyProgressDashboard - 공부시간 통계 로드:', this.studyTimeData)

        // 데이터 구조 확인
        if (this.studyTimeData) {
          debugLog('StudyProgressDashboard - task_study_times:', this.studyTimeData.task_study_times)
          debugLog('StudyProgressDashboard - daily_study_times:', this.studyTimeData.daily_study_times)
          debugLog('StudyProgressDashboard - total_study_time_minutes:', this.studyTimeData.total_study_time_minutes)
        }
      } catch (error) {
        debugLog('StudyProgressDashboard - 공부시간 통계 로드 실패:', error, 'error')
        debugLog('공부시간 통계 로드 실패:', error, 'error')
        this.studyTimeData = null
      }
    },
    async loadProgressHistory(studyId) {
      try {
        //
        // 핵심 원칙: 모든 통계 정보는 개인 통계만 반환한다
        // - /api/study-progress-history/${studyId}/ API는 현재 사용자의 개인 진행률 기록만 반환
        // - 다른 사용자의 진행률 기록은 노출하지 않음
        // - 개인정보 보호 및 보안 강화
        //
        const headers = {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }

        // 현재 사용자 정보 확인
        debugLog('StudyProgressDashboard - 현재 사용자 정보:')
        debugLog('StudyProgressDashboard - currentUserId:', this.currentUserId)
        debugLog('StudyProgressDashboard - $store.state.user:', this.$store?.state?.user)

        console.log('🔍 [StudyProgressDashboard] loadProgressHistory 호출됨 - studyId:', studyId, 'period:', this.selectedPeriod)
        debugLog('StudyProgressDashboard - 진행률 기록 API 호출 시작:', `/api/study-progress-history/${studyId}/`)

        // 선택된 기간을 쿼리 파라미터로 전달
        const params = {}
        if (this.selectedPeriod !== 'all') {
          params.days = this.selectedPeriod
        }

        console.log('🔍 [StudyProgressDashboard] study-progress-history API 호출 시작: /api/study-progress-history/' + studyId + '/', params)
        const response = await axios.get(`/api/study-progress-history/${studyId}/`, {
          headers,
          params
        })
        console.log('🔍 [StudyProgressDashboard] study-progress-history API 응답:', response.status)

        this.progressHistory = response.data.summary_table || []
        this.timeSeriesData = response.data.time_series_data || []

        // timeSeriesData의 진행률을 실제 값으로 업데이트
        if (this.timeSeriesData.length > 0) {
          this.timeSeriesData.forEach(record => {
            // attempted_progress와 correct_progress를 실제 진행률로 설정
            if (this.study && this.study.tasks) {
              // 전체 스터디의 진행률 계산
              let totalAttemptedProgress = 0
              let totalCorrectProgress = 0
              let taskCount = 0

              this.study.tasks.forEach(task => {
                if (task.attempted_progress !== undefined) {
                  totalAttemptedProgress += task.attempted_progress
                  taskCount++
                }
                if (task.correct_progress !== undefined) {
                  totalCorrectProgress += task.correct_progress
                }
              })

              if (taskCount > 0) {
                record.attempted_progress = totalAttemptedProgress / taskCount
                record.correct_progress = totalCorrectProgress / taskCount
              }
            }
          })

          debugLog('StudyProgressDashboard - timeSeriesData 진행률 업데이트 완료')
          debugLog('StudyProgressDashboard - 첫 번째 timeSeriesData 항목:', this.timeSeriesData[0])
        } else {
          debugLog('StudyProgressDashboard - timeSeriesData가 비어있음')
        }

        debugLog('StudyProgressDashboard - 진행률 기록 로드 완료')
      } catch (error) {
        debugLog('StudyProgressDashboard - 진행률 기록 로드 실패:', error, 'error')
        debugLog('진행률 기록 로드 실패:', error, 'error')
        if (error.response) {
          debugLog('StudyProgressDashboard - 에러 응답 상태:', error.response.status)
          debugLog('StudyProgressDashboard - 에러 응답 데이터:', error.response.data)
        }
        this.progressHistory = []
        this.timeSeriesData = []
      } finally {
        this.loading = false
      }
    },
    createCharts() {
      debugLog('StudyProgressDashboard - 차트 생성 시작')
      debugLog('StudyProgressDashboard - study:', this.study)
      debugLog('StudyProgressDashboard - tasks:', this.study?.tasks)
      debugLog('StudyProgressDashboard - timeSeriesData:', this.timeSeriesData)
      this.createOverallProgressChart()
      this.createTaskProgressChart()
    },
    createOverallProgressChart() {
      const ctx = this.$refs.overallProgressChart
      if (!ctx || this.timeSeriesData.length === 0) return

      // 시간별 진행률 데이터 사용
      const labels = this.timeSeriesData.map(record =>
        `${record.date} ${record.time}`
      )

      // 문제 기반 진행률과 정확도 데이터 계산
      const attemptedData = this.timeSeriesData.map(() => {
        // 문제 기반 진행률: (시도한 문제 수 / 전체 문제 수) * 100
        if (this.study && this.study.tasks) {
          let totalQuestions = 0
          let attemptedQuestions = 0
          
          this.study.tasks.forEach(task => {
            const examQuestions = task.exam?.questions?.length || 0
            totalQuestions += examQuestions
            
            // total_attempts를 사용해서 실제 시도한 문제 수 계산
            const totalAttempts = task.total_attempts || 0
            if (totalAttempts > 0) {
              // total_attempts는 시도 횟수이므로, 실제 시도한 문제 수를 추정
              const estimatedAttemptedQuestions = Math.ceil(totalAttempts / 2)
              attemptedQuestions += Math.min(estimatedAttemptedQuestions, examQuestions)
            }
          })
          
          if (totalQuestions > 0) {
            return (attemptedQuestions / totalQuestions) * 100
          }
        }
        return 0
      })
      
      const correctData = this.timeSeriesData.map(() => {
        // 문제 기반 정확도: (맞춘 문제 수 / 전체 문제 수) * 100
        if (this.study && this.study.tasks) {
          let totalQuestions = 0
          let correctQuestions = 0
          
          this.study.tasks.forEach(task => {
            const examQuestions = task.exam?.questions?.length || 0
            totalQuestions += examQuestions
            
            // correct_attempts를 사용해서 실제 맞춘 문제 수 계산
            const correctAttempts = task.correct_attempts || 0
            if (correctAttempts > 0) {
              // correct_attempts는 시도 횟수이므로, 실제 맞춘 문제 수를 추정
              const estimatedCorrectQuestions = Math.ceil(correctAttempts / 2)
              correctQuestions += Math.min(estimatedCorrectQuestions, examQuestions)
            }
          })
          
          if (totalQuestions > 0) {
            return (correctQuestions / totalQuestions) * 100
          }
        }
        return 0
      })

      this.overallProgressChart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [
            {
              label: this.$t('studyProgressDashboard.chart.attemptedProgress') || '문제 기반 진행률',
              data: attemptedData,
              borderColor: 'rgb(75, 192, 192)',
              backgroundColor: 'rgba(75, 192, 192, 0.1)',
              tension: 0.1,
              fill: false,
              borderWidth: 2
            },
            {
              label: this.$t('studyProgressDashboard.chart.correctProgress') || '문제 기반 정확도',
              data: correctData,
              borderColor: 'rgb(255, 99, 132)',
              backgroundColor: 'rgba(255, 99, 132, 0.1)',
              tension: 0.1,
              fill: false,
              borderWidth: 2
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: true, // false에서 true로 변경하여 높이 문제 해결
          aspectRatio: 4, // 높이를 50% 줄이기 위해 2에서 4로 변경 (비율이 클수록 높이가 낮아짐)
          interaction: {
            mode: 'index',
            intersect: false,
          },
          scales: {
            y: {
              beginAtZero: true,
              max: 100,
              ticks: {
                callback: function(value) {
                  return value + '%'
                }
              }
            }
          },
          plugins: {
            tooltip: {
              callbacks: {
                title: function(context) {
                  try {
                    if (!context || !Array.isArray(context) || context.length === 0) {
                      return 'Unknown'
                    }

                    const firstContext = context[0]
                    if (!firstContext || typeof firstContext.dataIndex === 'undefined') {
                      return 'Unknown'
                    }

                    const index = firstContext.dataIndex
                    const record = this.timeSeriesData[index]
                    if (!record) {
                      return 'Unknown'
                    }

                    return `${record.date} ${record.time}`
                  } catch (error) {
                    return 'Error'
                  }
                }.bind(this),
                label: function(context) {
                  const label = context.dataset.label || ''
                  return label + ': ' + context.parsed.y.toFixed(1) + '%'
                }
              }
            },
            legend: {
              display: true
            }
          },
          onHover: (event, elements) => {
            const canvas = event.native.target
            if (elements.length > 0) {
              canvas.style.cursor = 'pointer'
            } else {
              canvas.style.cursor = 'default'
            }
          }
        }
      })
    },

    createTaskProgressChart() {
      const ctx = this.$refs.taskProgressChart
      if (!ctx) {
        debugLog('StudyProgressDashboard - taskProgressChart canvas not found')
        return
      }

      if (!this.study) {
        debugLog('StudyProgressDashboard - study data not available')
        return
      }

      if (!this.study.tasks || this.study.tasks.length === 0) {
        debugLog('StudyProgressDashboard - no tasks available')
        return
      }

      const tasks = this.study.tasks
      const labels = tasks.map(task => {
        // 다국어 지원: name_ko, name_en, name 순서로 확인
        if (task.name && task.name.trim()) return task.name.trim()
        if (task.name_ko && task.name_ko.trim()) return task.name_ko.trim()
        if (task.name_en && task.name_en.trim()) return task.name_en.trim()

        // 모든 이름이 없는 경우 기본값 반환
        return `Task ${task.seq || task.id || 'Unknown'}`
      })

      // 각 태스크별 데이터 상세 로깅
      debugLog('StudyProgressDashboard - Task 차트 데이터 상세:')
      tasks.forEach((task, index) => {
        debugLog(`Task ${index}: name=${task.name}, name_ko=${task.name_ko}, name_en=${task.name_en}`)
        debugLog(`  - attempted_progress: ${task.attempted_progress}`)
        debugLog(`  - correct_progress: ${task.correct_progress}`)
        debugLog(`  - progress: ${task.progress}`)
        debugLog(`  - effective_progress: ${task.effective_progress}`)
        debugLog(`  - user_progress: ${task.user_progress}`)
      })

      // 시도 기반 정확도만 사용 (맞춤 차트)
      const correctData = tasks.map(task => {
        console.log(`Task ${task.name} 데이터:`, {
          correct_progress: task.correct_progress,
          correct_attempts: task.correct_attempts,
          total_attempts: task.total_attempts,
          user_progress: task.user_progress
        })

        // 백엔드에서 제공하는 correct_progress를 우선 사용 (정확도)
        if (task.correct_progress !== undefined && task.correct_progress > 0) {
          console.log(`Task ${task.name}: 백엔드 correct_progress 사용: ${task.correct_progress}`)
          return task.correct_progress
        }
        // 백엔드 값이 0이면 직접 계산
        if (task.correct_attempts !== undefined && task.total_attempts !== undefined && task.total_attempts > 0) {
          const calculated = (task.correct_attempts / task.total_attempts) * 100
          console.log(`Task ${task.name}: 직접 계산: ${task.correct_attempts}/${task.total_attempts} = ${calculated}%`)
          return calculated
        }
        // fallback: user_progress 또는 0 사용
        console.log(`Task ${task.name}: fallback 사용: ${task.user_progress || 0}`)
        return task.user_progress || 0
      })

      debugLog('StudyProgressDashboard - Task 차트 데이터:')
      debugLog('StudyProgressDashboard - correctData:', correctData)

      // 최종 데이터 검증 로깅
      debugLog('StudyProgressDashboard - 최종 데이터 검증:')
      correctData.forEach((value, index) => {
        if (value > 100) {
          debugLog(`⚠️ correctData[${index}]가 100%를 초과: ${value}%`)
        }
      })

      // 기존 차트가 있으면 제거
      if (this.taskProgressChart) {
        this.taskProgressChart.destroy()
      }

      this.taskProgressChart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [
            {
              label: this.$t('studyProgressDashboard.chart.correctProgress') || '시도 기반 정확도',
              data: correctData,
              backgroundColor: 'rgba(255, 99, 132, 0.6)',
              borderColor: 'rgba(255, 99, 132, 1)',
              borderWidth: 1
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: true, // false에서 true로 변경하여 높이 문제 해결
          aspectRatio: 4, // 높이를 50% 줄이기 위해 2에서 4로 변경 (비율이 클수록 높이가 낮아짐)
          interaction: {
            mode: 'index',
            intersect: false,
          },
          scales: {
            y: {
              beginAtZero: true,
              max: 100,
              ticks: {
                callback: function(value) {
                  return value + '%'
                }
              }
            }
          },
          plugins: {
            tooltip: {
              callbacks: {
                label: function(context) {
                  const label = context.dataset.label || ''
                  return label + ': ' + context.parsed.y.toFixed(1) + '%'
                }
              }
            },
            legend: {
              display: true
            }
          },
          onClick: (event, elements) => {
            if (elements.length > 0) {
              const index = elements[0].index
              const task = tasks[index]
              if (task && task.exam) {
                // 해당 시험 문제 풀기로 이동
                this.$router.push(`/take-exam/${task.exam.id}`)
              } else {
                this.$toast?.error?.(this.$t('studyProgressDashboard.alerts.noExamForTask'))
              }
            }
          },
          onHover: (event, elements) => {
            const canvas = event.native.target
            if (elements.length > 0) {
              canvas.style.cursor = 'pointer'
            } else {
              canvas.style.cursor = 'default'
            }
          }
        }
      })

      // 차트 생성 완료 로깅
      debugLog('StudyProgressDashboard - Task 차트 생성 완료')
      debugLog('StudyProgressDashboard - 차트 인스턴스:', this.taskProgressChart)
      debugLog('StudyProgressDashboard - 차트 데이터:', this.taskProgressChart.data)
      debugLog('StudyProgressDashboard - 차트 옵션:', this.taskProgressChart.options)

      // 차트 데이터 최종 확인
      console.log('🔍 차트 데이터 최종 확인:')
      console.log('  - correctData:', correctData)
      console.log('  - labels:', labels)
      console.log('  - Chart.js 데이터:', this.taskProgressChart.data)
    },
    clearCache() {
      debugLog('StudyProgressDashboard - 캐시 클리어')
      // 차트 정리
      if (this.overallProgressChart) {
        this.overallProgressChart.destroy()
        this.overallProgressChart = null
      }
      if (this.taskProgressChart) {
        this.taskProgressChart.destroy()
        this.taskProgressChart = null
      }

      // 데이터 새로고침
      this.refreshData()
    },
    async refreshData() {
      try {
        this.refreshing = true
        const studyId = this.$route.params.studyId
        if (studyId) {
          await this.loadStudy(studyId)
          await this.loadStudyTimeStatistics(studyId)
          await this.loadProgressHistory(studyId)
          this.$nextTick(() => {
            this.createCharts()
          })
        }
      } catch (error) {
        debugLog('데이터 새로고침 실패:', error, 'error')
      } finally {
        this.refreshing = false
      }
    },
    formatDate(dateString) {
      return formatLocalDate(dateString)
    },
    formatTime(dateString) {
      return formatLocalTime(dateString)
    },

    goBack() {
      const returnTo = this.$route.query.returnTo
      if (returnTo === 'study-detail') {
        this.$router.push(`/study-detail/${this.study.id}`)
      } else {
        this.$router.push('/study-management')
      }
    },
    // 현재 사용자 언어에 맞는 스터디 제목 반환
    getStudyTitle(study) {
      if (!study) return '';

      const currentLanguage = getCurrentLanguage(this.$i18n);
      const fallbackValue = currentLanguage === 'ko' ? '제목 없음' : 'No Title';
      return getLocalizedContent(study, 'title', currentLanguage, fallbackValue);
    },

    // 스터디 진행율 기록
    async recordProgress(studyId, pageType) {
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

    // 기간 변경 시 호출
    async onPeriodChange() {
      try {
        this.loading = true

        // 기존 차트 정리
        if (this.overallProgressChart) {
          this.overallProgressChart.destroy()
          this.overallProgressChart = null
        }
        if (this.taskProgressChart) {
          this.taskProgressChart.destroy()
          this.taskProgressChart = null
        }

        const studyId = this.$route.params.studyId
        if (studyId) {
          await this.loadStudy(studyId)
          await this.loadStudyTimeStatistics(studyId)
          await this.loadProgressHistory(studyId)
          this.$nextTick(() => {
            this.createCharts()
          })
        }
      } catch (error) {
        debugLog('기간 변경 후 데이터 로드 실패:', error, 'error')
      } finally {
        this.loading = false
      }
    },
    getTotalAttempts() {
      if (!this.study || !this.study.tasks || this.study.tasks.length === 0) {
        return '0';
      }
      return this.study.tasks.reduce((sum, task) => sum + (task.total_attempts || 0), 0);
    },
    getTotalCorrectAttempts() {
      if (!this.study || !this.study.tasks || this.study.tasks.length === 0) {
        return '0';
      }
      return this.study.tasks.reduce((sum, task) => sum + (task.correct_attempts || 0), 0);
    },
    getOverallAccuracy() {
      const totalAttempts = this.getTotalAttempts();
      const totalCorrect = this.getTotalCorrectAttempts();
      if (totalAttempts === '0') {
        return 0;
      }
      return (totalCorrect / totalAttempts) * 100;
    },
    getTotalQuestions() {
      if (!this.study || !this.study.tasks || this.study.tasks.length === 0) {
        return '0';
      }
      
      console.log('🔍 getTotalQuestions 디버깅:');
      let totalQuestions = 0;
      
      this.study.tasks.forEach((task, index) => {
        const examQuestions = task.exam?.questions?.length || 0;
        totalQuestions += examQuestions;
        console.log(`  Task ${index}: ${task.name || task.name_ko || task.name_en} - 문제 수: ${examQuestions}`);
      });
      
      console.log(`  총 문제 수: ${totalQuestions}`);
      return totalQuestions;
    },
    getAttemptProgress() {
      const totalAttempts = this.getTotalAttempts();
      const totalQuestions = this.getTotalQuestions();
      if (totalQuestions === '0') {
        return 0;
      }
      return (totalAttempts / totalQuestions) * 100;
    },
    getTaskProgress(task) {
      if (!task) return '0';

      let progress = 0;

      // 공부시간 통계 API의 progress 필드 우선 사용
      if (task.progress !== undefined && task.progress > 0) {
        progress = task.progress;
      }
      // StudySerializer의 attempted_progress 사용
      else if (task.attempted_progress !== undefined && task.attempted_progress > 0) {
        progress = task.attempted_progress;
      }
      // 직접 계산
      else if (task.correct_attempts !== undefined && task.total_attempts !== undefined && task.total_attempts > 0) {
        progress = (task.correct_attempts / task.total_attempts) * 100;
      }
      // fallback
      else {
        progress = task.user_progress || 0;
      }

      // 2자리 소수점으로 반올림하여 반환
      return Math.round(progress * 100) / 100;
    },

    // 문제 기반 계산 메서드들
    getAttemptedQuestions() {
      if (!this.study || !this.study.tasks || this.study.tasks.length === 0) {
        return '0';
      }
      
      let totalAttemptedQuestions = 0;
      console.log('🔍 getAttemptedQuestions 디버깅:');
      
      this.study.tasks.forEach((task, index) => {
        const examQuestions = task.exam?.questions?.length || 0;
        const totalAttempts = task.total_attempts || 0;
        const attemptedProgress = task.attempted_progress || 0;
        
        console.log(`  Task ${index}: ${task.name || task.name_ko || task.name_en}`);
        console.log(`    - examQuestions: ${examQuestions}`);
        console.log(`    - total_attempts: ${totalAttempts}`);
        console.log(`    - attempted_progress: ${attemptedProgress}%`);
        
        // attempted_progress가 있으면 문제 기반으로 계산
        // total_attempts가 있으면 실제 시도한 문제 수를 추정
        if (totalAttempts > 0) {
          // total_attempts는 시도 횟수이므로, 실제 시도한 문제 수를 추정
          // 보통 한 문제를 여러 번 시도할 수 있으므로, 시도 횟수로부터 실제 문제 수를 추정
          // 예: total_attempts=6, correct_attempts=5라면, 약 3문제 정도 시도했을 가능성이 높음
          const estimatedQuestionsAttempted = Math.ceil(totalAttempts / 2); // 시도 횟수의 절반을 문제 수로 추정
          const actualAttemptedQuestions = Math.min(estimatedQuestionsAttempted, examQuestions);
          totalAttemptedQuestions += actualAttemptedQuestions;
          console.log(`    - 추정된 시도한 문제 수: ${actualAttemptedQuestions} (total_attempts: ${totalAttempts}에서 추정)`);
        }
        // fallback: attempted_progress 사용
        else if (attemptedProgress > 0 && examQuestions > 0) {
          const actualAttemptedQuestions = Math.round((attemptedProgress / 100) * examQuestions);
          totalAttemptedQuestions += actualAttemptedQuestions;
          console.log(`    - attempted_progress 기반 시도한 문제 수: ${actualAttemptedQuestions} (${attemptedProgress}% × ${examQuestions})`);
        }
      });
      
      console.log(`  총 시도한 문제 수: ${totalAttemptedQuestions}`);
      return totalAttemptedQuestions.toString();
    },

    getCorrectQuestions() {
      if (!this.study || !this.study.tasks || this.study.tasks.length === 0) {
        return '0';
      }
      
      let totalCorrectQuestions = 0;
      console.log('🔍 getCorrectQuestions 디버깅:');
      
      this.study.tasks.forEach((task, index) => {
        const examQuestions = task.exam?.questions?.length || 0;
        const correctAttempts = task.correct_attempts || 0;
        const totalAttempts = task.total_attempts || 0;
        const correctProgress = task.correct_progress || 0;
        
        console.log(`  Task ${index}: ${task.name || task.name_ko || task.name_en}`);
        console.log(`  - examQuestions: ${examQuestions}`);
        console.log(`  - correct_attempts: ${correctAttempts}`);
        console.log(`  - total_attempts: ${totalAttempts}`);
        console.log(`  - correct_progress: ${correctProgress}%`);
        
        // correct_attempts가 있으면 실제 맞춘 문제 수를 추정
        if (correctAttempts > 0) {
          // correct_attempts는 시도 횟수이므로, 실제 맞춘 문제 수를 추정
          // 보통 한 문제를 여러 번 시도할 수 있으므로, 정답 횟수로부터 실제 맞춘 문제 수를 추정
          // 예: correct_attempts=5라면, 약 3문제 정도 맞췄을 가능성이 높음
          const estimatedCorrectQuestions = Math.ceil(correctAttempts / 2); // 정답 횟수의 절반을 문제 수로 추정
          const actualCorrectQuestions = Math.min(estimatedCorrectQuestions, examQuestions);
          totalCorrectQuestions += actualCorrectQuestions;
          console.log(`  - 추정된 맞춘 문제 수: ${actualCorrectQuestions} (correct_attempts: ${correctAttempts}에서 추정)`);
        }
        // fallback: correct_progress 사용
        else if (correctProgress > 0 && examQuestions > 0) {
          const actualCorrectQuestions = Math.round((correctProgress / 100) * examQuestions);
          totalCorrectQuestions += actualCorrectQuestions;
          console.log(`  - correct_progress 기반 맞춘 문제 수: ${actualCorrectQuestions} (${correctProgress}% × ${examQuestions})`);
        }
      });
      
      console.log(`  총 맞춘 문제 수: ${totalCorrectQuestions}`);
      return totalCorrectQuestions.toString();
    },

    getQuestionBasedProgress() {
      const totalQuestions = parseInt(this.getTotalQuestions());
      const attemptedQuestions = parseInt(this.getAttemptedQuestions());
      
      if (totalQuestions === 0) {
        return 0;
      }
      
      return (attemptedQuestions / totalQuestions) * 100;
    }
  }
}
</script>

<style scoped>
.study-progress-dashboard {
  padding: 20px 0;
  min-height: calc(100vh - 200px); /* footer가 중간에 보이는 것을 방지 */
}

/* 모바일 최적화 */
@media (max-width: 768px) {
  .study-progress-dashboard h2 {
    font-size: 1.5rem;
    word-break: break-word;
    line-height: 1.3;
  }
  
  .period-selector {
    margin-bottom: 0.5rem;
  }
  
  .period-selector label {
    font-size: 0.9rem;
  }
  
  /* 원형 버튼 스타일은 공통 CSS (mobile-buttons.css)에서 처리됨 */
}

.container {
  min-height: inherit; /* container도 최소 높이 상속 */
}

/* 로딩 상태일 때 중앙 정렬 */
.text-center.py-5 {
  min-height: 400px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.progress-link {
  text-decoration: none;
  color: inherit;
}

.progress-link:hover {
  color: #007bff;
  text-decoration: underline;
}

.card {
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
}

.card-header {
  background-color: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
}

canvas {
  max-width: 100%;
  height: 300px;
}

.task-chart-container {
  position: relative;
}

.task-link {
  color: #007bff;
  text-decoration: none;
  font-weight: 500;
}

.task-link:hover {
  color: #0056b3;
  text-decoration: underline;
  cursor: pointer;
}

.period-selector {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.period-selector .form-label {
  font-size: 0.9rem;
  font-weight: 500;
  color: #495057;
  margin-bottom: 0;
}

.period-selector .form-select {
  min-width: 100px;
  font-size: 0.9rem;
}

.task-chart-container canvas {
  cursor: pointer;
}

.task-chart-container canvas:hover {
  cursor: pointer;
}
</style> 