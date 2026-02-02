<template>
  <div class="profile-modern">
    <!-- JSON-LD 구조화된 데이터 -->
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "WebPage",
      "name": "DrillQuiz 프로필",
      "description": "개인 프로필을 관리하고 학습 설정을 조정하세요. 이메일 인증, 언어 설정, 랜덤 시험 설정 등을 관리할 수 있습니다.",
      "url": "https://us.drillquiz.com/profile",
      "mainEntity": {
        "@type": "Person",
        "name": "사용자",
        "description": "DrillQuiz 사용자 프로필",
        "url": "https://us.drillquiz.com/profile"
      }
    }
    </script>
    
    <!-- 번역 로딩 중일 때 로딩 표시 -->
    <div v-if="!$isTranslationsLoaded($i18n.locale)" class="loading-container">
      <div class="loading-spinner">
        <i class="fas fa-spinner fa-spin"></i>
      </div>
      <p class="loading-text">{{ $t('profile.messages.loadingText') }}</p>
    </div>
    
    <!-- 번역이 로드된 후에만 컨텐츠 표시 -->
    <div v-else class="profile-container">
      <!-- 통계 초기화 확인 모달 -->
      <div v-if="showStatisticsResetModal" class="modal-overlay" @click="hideStatisticsResetConfirm">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h5 class="modal-title">
              <i class="fas fa-exclamation-triangle text-danger me-2"></i>
              {{ $t('profile.statistics.resetConfirm.title') }}
            </h5>
            <button class="modal-close" @click="hideStatisticsResetConfirm">
              <i class="fas fa-times"></i>
            </button>
          </div>
          <div class="modal-body">
            <div class="alert alert-danger">
              <i class="fas fa-exclamation-triangle"></i>
              <strong>{{ $t('profile.statistics.resetConfirm.warning') }}</strong>
            </div>
            <p>{{ $t('profile.statistics.resetConfirm.message') }}</p>
            <ul class="reset-impact-list">
              <li>{{ $t('profile.statistics.resetConfirm.impact1') }}</li>
              <li>{{ $t('profile.statistics.resetConfirm.impact2') }}</li>
              <li>{{ $t('profile.statistics.resetConfirm.impact3') }}</li>
              <li>{{ $t('profile.statistics.resetConfirm.impact4') }}</li>
            </ul>
            <div class="form-group">
              <label class="form-label">{{ $t('profile.statistics.resetConfirm.confirmation') }}</label>
              <input v-model="resetConfirmation" type="text" class="form-control-modern" :placeholder="$t('profile.statistics.resetConfirm.placeholder')">
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="hideStatisticsResetConfirm">
              {{ $t('common.cancel') }}
            </button>
            <button class="btn btn-danger" @click="confirmStatisticsReset" :disabled="!canConfirmReset">
              <i class="fas fa-trash-alt me-1"></i>
              {{ $t('common.confirm') }}
            </button>
          </div>
        </div>
      </div>

      <!-- 계정 탈퇴 확인 모달 -->
      <div v-if="showWithdrawalModal" class="modal-overlay" @click="withdrawing ? null : hideWithdrawalConfirm">
        <div class="modal-content" @click.stop :class="{ 'withdrawing': withdrawing }">
          <div class="modal-header">
            <h5 class="modal-title">
              <i class="fas fa-exclamation-triangle text-danger me-2"></i>
              {{ $t('profile.withdrawal.confirm.title') }}
            </h5>
            <button class="modal-close" @click="hideWithdrawalConfirm" :disabled="withdrawing">
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
              <input v-model="withdrawalConfirmation" type="text" class="form-control-modern" :placeholder="$t('profile.withdrawal.confirm.placeholder')" :disabled="withdrawing">
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="hideWithdrawalConfirm" :disabled="withdrawing">
              {{ $t('common.cancel') }}
            </button>
            <button class="btn btn-danger" @click="confirmWithdrawal" :disabled="!canConfirmWithdrawal || withdrawing">
              <i v-if="withdrawing" class="fas fa-spinner fa-spin me-1"></i>
              <i v-else class="fas fa-user-times me-1"></i>
              {{ withdrawing ? $t('profile.withdrawal.processing') : $t('common.confirm') }}
            </button>
          </div>
        </div>
      </div>
      <!-- 상단 헤더 -->
      <div class="top-header">
        <div class="page-title">
          <h1><i class="fas fa-user-circle"></i> {{ $t('profile.title') }}</h1>
        </div>
      </div>

      <!-- 사용자 정보 섹션 -->
      <div class="card-modern">
        <div class="card-header-modern">
          <h3><i class="fas fa-user"></i> {{ $t('profile.title') }} <span v-if="ageRating" class="age-rating-badge">{{ ageRating }}</span></h3>
        </div>
        <div class="card-body-modern">
          <div class="form-group">
            <label class="form-label">{{ $t('profile.username') }}</label>
            <input v-model="userInfo.username" type="text" class="form-control-modern" readonly>
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">{{ $t('profile.firstName') }}</label>
              <input v-model="userInfo.first_name" type="text" class="form-control-modern" @change="updateUserInfo">
            </div>
            <div class="form-group">
              <label class="form-label">{{ $t('profile.lastName') }}</label>
              <input v-model="userInfo.last_name" type="text" class="form-control-modern" @change="updateUserInfo">
            </div>
          </div>
          
          <div class="form-group">
            <label class="form-label">{{ $t('profile.email') }}</label>
            <div class="email-input-group">
              <div class="email-input-row">
                <input v-model="userInfo.email" type="email" class="form-control-modern email-input" @change="updateUserInfo">
                <div class="email-status-badges">
                  <span class="status-badge" :class="{ 'verified': emailVerified, 'not-verified': !emailVerified }">
                    <i :class="emailVerified ? 'fas fa-check-circle' : 'fas fa-exclamation-circle'"></i>
                    {{ emailVerified ? $t('profile.emailVerification.verified') : $t('profile.emailVerification.notVerified') }}
                  </span>
                  <button v-if="!emailVerified && userInfo.email" @click="sendEmailVerification" class="verification-btn" :disabled="sendingEmail">
                    <i class="fas fa-paper-plane"></i>
                    <span>{{ sendingEmail ? $t('profile.emailVerification.sending') : $t('profile.emailVerification.button') }}</span>
                  </button>
                </div>
              </div>
            </div>
            <small class="form-text" v-if="!emailVerified">{{ $t('profile.emailVerification.description') }}</small>
          </div>
          
          <div class="form-actions">
            <button @click="exportUserData" class="action-btn action-btn-success" :disabled="exporting">
              <i class="fas fa-download"></i>
              <span class="action-label">{{ exporting ? $t('profile.exporting') : $t('profile.exportData') }}</span>
            </button>
          </div>
        </div>
      </div>

      

    <!-- 관심 카테고리 설정 -->
    <div class="card-modern">
      <div class="card-header-modern">
        <h3><i class="fas fa-tags"></i> {{ $t('profile.interestedCategories.title') || '관심 카테고리' }}</h3>
      </div>
      <div class="card-body-modern">
        <div class="form-group">
          <label class="form-label">{{ $t('profile.interestedCategories.label') || '관심있는 카테고리를 선택하세요' }}</label>
          <div class="category-selection-container">
            <div class="d-flex align-items-center justify-content-between gap-2 flex-wrap">
              <!-- Selected Categories Display -->
              <div v-if="selectedCategoriesDisplay.length > 0" class="d-flex align-items-center flex-wrap gap-2 flex-grow-1">
                <span 
                  v-for="category in selectedCategoriesDisplay" 
                  :key="category.id"
                  class="badge bg-primary"
                >
                  {{ getCategoryDisplayName(category) }}
                  <button 
                    @click="removeCategory(category.id)" 
                    class="btn-close btn-close-white ms-1" 
                    style="font-size: 0.7em;"
                  ></button>
                </span>
              </div>
              <!-- Tag Filter Button -->
              <button 
                @click="openCategoryFilterModal" 
                class="btn btn-outline-primary tag-filter-btn"
              >
                <i class="fas fa-tags"></i>
                {{ $t('tagFilterModal.title') || '태그 필터' }}
                <span v-if="interestedCategories.length > 0" class="badge bg-primary ms-2">{{ interestedCategories.length }}</span>
              </button>
            </div>
          </div>
          <small class="form-text">{{ $t('profile.interestedCategories.hint') || '관심있는 카테고리를 선택하면 관련 스터디와 시험이 기본으로 필터링됩니다.' }}</small>
        </div>
      </div>
    </div>
    
    <!-- Category Filter Modal -->
    <CategoryFilterModal
      :show="showCategoryFilterModal"
      :selectedCategories="interestedCategories"
      @update:show="showCategoryFilterModal = $event"
      @update:selectedCategories="handleSelectedCategoriesUpdate"
      @apply="handleCategoryFilterApply"
      @error="handleCategoryFilterError"
    />

      <!-- 랜덤 시험 설정 섹션 -->
      <div class="card-modern">
        <div class="card-header-modern">
          <h3><i class="fas fa-random"></i> {{ $t('profile.randomExam.title') }}</h3>
        </div>
        <div class="card-body-modern">
          <div class="form-group">
            <div class="checkbox-group">
              <input 
                v-model="randomExamSettings.emailEnabled" 
                type="checkbox" 
                class="checkbox-modern" 
                id="randomExamEmailEnabled"
                @change="updateRandomExamSettings"
              >
              <label class="checkbox-label" for="randomExamEmailEnabled">
                {{ $t('profile.randomExam.emailEnabled') }}
              </label>
            </div>
            <small class="form-text">{{ $t('profile.randomExam.emailDescription') }}</small>
          </div>
          
          <div class="form-group">
            <label for="questionCount" class="form-label">{{ $t('profile.randomExam.questionCount') }}</label>
            <input 
              v-model="randomExamSettings.questionCount" 
              type="number" 
              class="form-control-modern" 
              id="questionCount"
              min="1" 
              max="50"
              @change="updateRandomExamSettings"
            >
            <small class="form-text">{{ $t('profile.randomExam.questionCountDescription') }}</small>
          </div>

          <!-- My Exams와 Subscribed Exams 관리 -->
          <div class="exam-management-section">
            <div class="exam-lists-container">
              <!-- My Exams (좌측) -->
              <div class="exam-list-section">
                <div class="list-header">
                  <h5 class="list-title">
                    <i class="fas fa-folder"></i>
                    {{ $t('profile.exam.myExams') }}
                  </h5>
                </div>
                <div class="exam-list" :class="{ 'loading': loadingMyExams }">
                  <div v-if="loadingMyExams" class="loading-indicator">
                    <i class="fas fa-spinner fa-spin"></i>
                  </div>
                  <div v-else-if="myExams.length === 0" class="empty-list">
                    {{ $t('profile.exam.noMyExams') }}
                  </div>
                  <div v-else class="exam-items">
                    <div 
                      v-for="exam in myExams" 
                      :key="exam.id" 
                      class="exam-item"
                      :class="{ 'selected': selectedMyExams.includes(exam.id) }"
                      @click="toggleMyExamSelection(exam.id)"
                    >
                      <span class="exam-title">{{ getExamTitle(exam) }}</span>
                      <i v-if="selectedMyExams.includes(exam.id)" class="fas fa-check selection-indicator"></i>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 중앙 컨트롤 버튼들 -->
              <div class="exam-controls">
                <button 
                  @click="moveToSubscribed" 
                  class="control-btn"
                  :disabled="selectedMyExams.length === 0 || loadingSubscriptions"
                  title="선택된 시험을 Subscribed Exams로 이동"
                >
                  <i class="fas fa-arrow-right"></i>
                </button>
                <button 
                  @click="moveToMyExams" 
                  class="control-btn"
                  :disabled="selectedSubscribedExams.length === 0 || loadingSubscriptions"
                  title="선택된 시험 구독 해제"
                >
                  <i class="fas fa-arrow-left"></i>
                </button>
              </div>

              <!-- Subscribed Exams (우측) -->
              <div class="exam-list-section">
                <div class="list-header">
                  <h5 class="list-title">
                    <i class="fas fa-star"></i>
                    {{ $t('profile.exam.subscribedExams') }}
                  </h5>
                </div>
                <div class="exam-list" :class="{ 'loading': loadingSubscriptions }">
                  <div v-if="loadingSubscriptions" class="loading-indicator">
                    <i class="fas fa-spinner fa-spin"></i>
                  </div>
                  <div v-else-if="subscribedExams.length === 0" class="empty-list">
                    {{ $t('profile.exam.noSubscribedExams') }}
                  </div>
                  <div v-else class="exam-items">
                    <div 
                      v-for="exam in subscribedExams" 
                      :key="exam.id" 
                      class="exam-item"
                      :class="{ 'selected': selectedSubscribedExams.includes(exam.id) }"
                      @click="toggleSubscribedExamSelection(exam.id)"
                    >
                      <span class="exam-title">{{ getExamTitle(exam) }}</span>
                      <i v-if="selectedSubscribedExams.includes(exam.id)" class="fas fa-check selection-indicator"></i>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Retention Cleanup 섹션 -->
      <div class="card-modern">
        <div class="card-header-modern">
          <h3><i class="fas fa-broom"></i> {{ $t('profile.retention.title') }}</h3>
        </div>
        <div class="card-body-modern">
          <div class="form-group">
            <div class="slider-container">
              <input 
                v-model.number="retentionSettings.percentage" 
                type="range" 
                class="form-control-modern slider" 
                id="retentionPercentage"
                :min="0" 
                :max="100"
                step="5"
                @change="updateRetentionSettings"
              >
              <span class="slider-value">{{ retentionSettings.percentage }}%</span>
            </div>
            <small class="form-text">
              {{ $t('profile.retention.description', { percentage: retentionSettings.percentage }) }}
            </small>
          </div>
          
          <div class="form-group">
            <div class="checkbox-group">
              <input 
                v-model="retentionSettings.enabled" 
                type="checkbox" 
                class="checkbox-modern" 
                id="retentionEnabled"
                @change="updateRetentionSettings"
              >
              <label class="checkbox-label" for="retentionEnabled">
                {{ $t('profile.retention.enabled') }}
              </label>
            </div>
          </div>
          
          <div class="form-actions">
            <button @click="runManualCleanup" class="action-btn action-btn-warning" :disabled="cleanupRunning">
              <i class="fas fa-broom"></i>
              <span class="action-label">{{ cleanupRunning ? $t('profile.retention.cleaning') : $t('profile.retention.cleanupNow') }}</span>
            </button>
          </div>
        </div>
      </div>

    <!-- 자동 번역 설정 -->
    <div class="card-modern">
      <div class="card-header-modern">
        <h3><i class="fas fa-language"></i> {{ $t('profile.translation.title') }}</h3>
      </div>
      <div class="card-body-modern">
        <div class="form-group">
          <div class="checkbox-group">
            <input
              v-model="translationSettings.autoEnabled"
              type="checkbox"
              class="checkbox-modern"
              id="autoTranslationEnabled"
              @change="updateTranslationSettings"
            >
            <label class="checkbox-label" for="autoTranslationEnabled">
              {{ $t('profile.translation.autoEnabled') }}
            </label>
          </div>
          <small class="form-text">{{ $t('profile.translation.description') }}</small>
          <small class="form-text">{{ $t('profile.translation.help') }}</small>
        </div>
      </div>
    </div>

      <!-- 통계 초기화 섹션 -->
      <div class="card-modern">
        <div class="card-header-modern">
          <h3><i class="fas fa-chart-bar"></i> {{ $t('profile.statistics.title') }}</h3>
        </div>
        <div class="card-body-modern">
          <div class="alert alert-warning">
            <i class="fas fa-exclamation-triangle"></i>
            <strong>{{ $t('profile.statistics.warning') }}</strong>
            <p>{{ $t('profile.statistics.warningDescription') }}</p>
          </div>
          
          <div class="form-actions">
            <button @click="showStatisticsResetConfirm" class="action-btn action-btn-danger" :disabled="resettingStatistics">
              <i class="fas fa-trash-alt"></i>
              <span class="action-label">{{ resettingStatistics ? $t('profile.statistics.resetting') : $t('profile.statistics.resetAll') }}</span>
            </button>
          </div>

        </div>
      </div>

      <!-- 캐시 설정 섹션 -->
      <div class="card-modern">
        <div class="card-header-modern">
          <h3><i class="fas fa-database"></i> {{ $t('profile.cache.title') }}</h3>
        </div>
        <div class="card-body-modern">
          <div class="form-group">
            <div class="checkbox-group">
              <input 
                v-model="cacheSettings.enabled" 
                type="checkbox" 
                class="checkbox-modern" 
                id="cacheEnabled"
                @change="updateCacheSettings"
              >
              <label class="checkbox-label" for="cacheEnabled">
                {{ $t('profile.cache.enabled') }}
              </label>
            </div>
            <small class="form-text">
              {{ $t('profile.cache.description') }}
            </small>
          </div>
          
          <div class="form-group">
            <button @click="clearAllCache" class="action-btn action-btn-warning">
              <i class="fas fa-trash"></i>
              <span class="action-label">{{ $t('profile.cache.clearAll') }}</span>
            </button>
            <small class="form-text">{{ $t('profile.cache.clearDescription') }}</small>
          </div>
        </div>
      </div>



      <!-- 계정 및 보안 섹션 -->
      <div class="card-modern account-security-section">
        <div class="card-header-modern">
          <h3><i class="fas fa-shield-alt"></i> {{ $t('profile.accountSecurity.title') || 'Account & Security' }}</h3>
        </div>
        <div class="card-body-modern">
          <!-- 비밀번호 변경 -->
          <div class="security-subsection">
            <h4 class="subsection-title">
              <i class="fas fa-lock"></i> {{ $t('profile.password.title') }}
            </h4>
            <form @submit.prevent="onChangePassword" autocomplete="off">
              <div class="form-group">
                <label for="newPassword" class="form-label">{{ $t('profile.password.newPassword') }}</label>
                <input v-model="passwordForm.new1" type="password" class="form-control-modern" id="newPassword" required>
              </div>
              <div class="form-group">
                <label for="newPassword2" class="form-label">{{ $t('profile.password.confirmPassword') }}</label>
                <input v-model="passwordForm.new2" type="password" class="form-control-modern" id="newPassword2" required @input="checkPasswordMatch">
                <div class="password-match-indicator" v-if="passwordForm.new2">
                  <i :class="passwordForm.new1 === passwordForm.new2 ? 'fas fa-check-circle text-success' : 'fas fa-times-circle text-danger'"></i>
                  <span :class="passwordForm.new1 === passwordForm.new2 ? 'text-success' : 'text-danger'">
                    {{ passwordForm.new1 === passwordForm.new2 ? '패스워드가 일치합니다' : '패스워드가 일치하지 않습니다' }}
                  </span>
                </div>
              </div>
              <div class="form-actions">
                <button type="submit" class="action-btn action-btn-secondary">
                  <i class="fas fa-key"></i>
                  <span class="action-label">{{ $t('profile.password.change') }}</span>
                </button>
              </div>
            </form>
          </div>

          <!-- 계정 삭제 -->
          <div class="security-subsection account-deletion-subsection">
            <div class="account-deletion-header">
              <h4 class="subsection-title account-deletion-title">
                <i class="fas fa-exclamation-triangle text-danger"></i> 
                {{ $t('profile.accountDeletion.title') || 'Delete Account' }}
              </h4>
            </div>
            <div class="account-deletion-content">
              <div class="withdrawal-warning">
                <i class="fas fa-exclamation-triangle text-danger"></i>
                <strong>{{ $t('profile.withdrawal.warning') || 'Warning: This action cannot be undone' }}</strong>
              </div>
              <p class="withdrawal-description">{{ $t('profile.withdrawal.description') || 'Deleting your account will permanently remove all your data.' }}</p>
              <ul class="withdrawal-impact-list">
                <li>{{ $t('profile.withdrawal.impact1') || 'All your study data will be deleted' }}</li>
                <li>{{ $t('profile.withdrawal.impact2') || 'All your exam records will be deleted' }}</li>
                <li>{{ $t('profile.withdrawal.impact3') || 'All your statistics will be deleted' }}</li>
                <li>{{ $t('profile.withdrawal.impact4') || 'You will not be able to recover your account' }}</li>
                <li>{{ $t('profile.withdrawal.impact5') || 'All your settings will be deleted' }}</li>
              </ul>
              <div class="account-deletion-button-wrapper">
                <button @click="showWithdrawalConfirm" class="action-btn action-btn-danger account-deletion-btn">
                  <i class="fas fa-trash-alt"></i>
                  <span class="action-label">{{ $t('profile.accountDeletion.button') || 'Delete Account' }}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
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
          <p>{{ modalMessage }}</p>
        </div>
        <div class="modal-footer">
          <button @click="cancelModal" class="action-btn action-btn-secondary">
            {{ modalCancelText }}
          </button>
          <button @click="confirmModal" :class="['action-btn', modalConfirmButtonClass]">
            {{ modalConfirmText }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { debugLog } from '@/utils/debugUtils'
import authService from '@/services/authService'
import CategoryFilterModal from '@/components/CategoryFilterModal.vue'
import { getLocalizedContent } from '@/utils/multilingualUtils'

export default {
  name: 'Profile',
  components: {
    CategoryFilterModal
  },
  metaInfo() {
    return {
      title: '프로필',
      meta: [
        { name: 'description', content: 'DrillQuiz 프로필 - 개인 프로필을 관리하고 학습 설정을 조정하세요. 이메일 인증, 언어 설정, 랜덤 시험 설정 등을 관리할 수 있습니다.' },
        { name: 'keywords', content: 'DrillQuiz 프로필, 사용자 설정, 이메일 인증, 언어 설정, 학습 설정 관리' },
        // Open Graph
        { property: 'og:title', content: 'DrillQuiz 프로필 - 사용자 설정 관리' },
        { property: 'og:description', content: 'DrillQuiz 프로필 - 개인 프로필을 관리하고 학습 설정을 조정하세요.' },
        { property: 'og:type', content: 'website' },
        { property: 'og:url', content: 'https://us.drillquiz.com/profile' },
        // Twitter Card
        { name: 'twitter:title', content: 'DrillQuiz 프로필 - 사용자 설정 관리' },
        { name: 'twitter:description', content: 'DrillQuiz 프로필 - 개인 프로필을 관리하고 학습 설정을 조정하세요.' }
      ]
    }
  },
  data() {
    return {
      loading: false,
      userInfo: {
        username: '',
        email: '',
        first_name: '',
        last_name: ''
      },
      passwordForm: {
        new1: '',
        new2: ''
      },
      passwordError: '',
      exporting: false,
      randomExamSettings: {
        emailEnabled: false,
        questionCount: 3
      },
      previousQuestionCount: 3, // 이전 Quiz Count 값 추적
      translationSettings: {
        autoEnabled: sessionStorage.getItem('autoEnabled') !== 'false'
      },
      previousAutoTranslationEnabled: true,
      randomExamError: '',
      randomExamSuccess: '',
      retentionSettings: {
        enabled: false,
        percentage: 0
      },
      retentionError: '',
      retentionSuccess: '',
      cleanupRunning: false,
      cacheSettings: {
        enabled: localStorage.getItem('cacheEnabled') !== 'false'
      },
      cacheError: '',
      cacheSuccess: '',
      emailVerified: false,
      sendingEmail: false,
      // 토스트 알림 설정
      showToast: false,
      toastMessage: '',
      toastType: 'success',
      toastIcon: 'fas fa-check',
      // 모달 설정
      showModal: false,
      modalTitle: '',
      modalMessage: '',
      modalConfirmText: '확인',
      modalCancelText: '취소',
      modalIcon: 'fas fa-info-circle',
      modalConfirmButtonClass: 'action-btn-primary',
      modalCallback: null,
      // 통계 초기화 관련 데이터
      showStatisticsResetModal: false,
      resetConfirmation: '',
      resettingStatistics: false,

      // 랜덤 시험 목록 관리 관련 데이터
      loadingMyExams: false,
      myExams: [],
      selectedMyExams: [],
      loadingSubscriptions: false,
      subscribedExams: [],
      selectedSubscribedExams: [],
      // 탈퇴 관련 설정
      showWithdrawalModal: false,
      withdrawalConfirmation: '',
      withdrawing: false,
      // 관심 카테고리 관련
      availableCategories: [],
      categoryTree: [], // 트리 구조 (경로 생성용)
      loadingCategories: false,
      interestedCategories: [],
      updatingCategories: false,
      showCategoryFilterModal: false,
      // 나이 등급
      ageRating: null
    }
  },
  mounted() {
    this.loadUserInfo()
    this.loadUserProfile()
    this.loadMyExams()
    this.loadSubscribedExams()
    this.loadCategories()
    
    // 이메일 인증 완료 후 강제 새로고침
    if (sessionStorage.getItem('refreshProfile') === 'true') {
      sessionStorage.removeItem('refreshProfile')
      this.refreshProfile()
    }
    
    // Daily Exam 생성 후 강제 새로고침
    if (sessionStorage.getItem('forceRefreshProfile') === 'true') {
      sessionStorage.removeItem('forceRefreshProfile')
      this.loadMyExams()
      this.loadSubscribedExams()
    }
  },
  computed: {
    canConfirmReset() {
      return this.resetConfirmation === 'RESET'
    },
    canConfirmWithdrawal() {
      return this.withdrawalConfirmation === 'WITHDRAW'
    },
    selectedCategoriesDisplay() {
      // interestedCategories ID 배열을 기반으로 카테고리 객체 반환
      if (!this.availableCategories || this.availableCategories.length === 0) {
        return []
      }
      return this.availableCategories.filter(cat => 
        this.interestedCategories.includes(cat.id)
      )
    }
  },
  methods: {
    // 토스트 알림 메서드들
    showToastNotification(message, type = 'success', icon = null) {
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
    
    // 모달 메서드들
    showConfirmModal(title, message, confirmText = '확인', cancelText = '취소', confirmButtonClass = 'btn-success', icon = 'fas fa-question', callback = null) {
      this.modalTitle = title
      this.modalMessage = message
      this.modalConfirmText = confirmText
      this.modalCancelText = cancelText
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

    async refreshProfile() {
      this.loading = true
      try {
        await this.loadUserProfile()
        this.showToastNotification(this.$t('profile.refresh.success'), 'success')
      } catch (error) {
        this.showToastNotification(this.$t('profile.refresh.failed'), 'error')
      } finally {
        this.loading = false
      }
    },

    loadUserInfo() {
      const user = authService.getUserSync()
      if (user) {
        this.userInfo = { ...this.userInfo, ...user }
      }
    },
    
    async loadUserProfile() {
      try {
        const response = await axios.get('/api/user-profile/get/')
        this.randomExamSettings.emailEnabled = response.data.random_exam_email_enabled
        this.randomExamSettings.questionCount = response.data.random_exam_question_count
        
        // 이전 Quiz Count 값 초기화
        this.previousQuestionCount = response.data.random_exam_question_count

        // 자동 번역 설정 로드
        if (Object.prototype.hasOwnProperty.call(response.data, 'auto_translation_enabled')) {
          this.translationSettings.autoEnabled = response.data.auto_translation_enabled
          this.previousAutoTranslationEnabled = response.data.auto_translation_enabled
        } else {
          this.translationSettings.autoEnabled = true
          this.previousAutoTranslationEnabled = true
        }
        
        // Retention Cleanup 설정 로드
        this.retentionSettings.enabled = response.data.retention_cleanup_enabled || false
        this.retentionSettings.percentage = response.data.retention_cleanup_percentage || 0
        
        // 사용자 정보 업데이트
        this.userInfo.email = response.data.email || ''
        this.userInfo.first_name = response.data.first_name || ''
        this.userInfo.last_name = response.data.last_name || ''
        
        // 이메일 인증 상태 업데이트
        this.emailVerified = response.data.email_verified || false
        
        // 관심 카테고리 로드
        this.interestedCategories = response.data.interested_categories || []
        
        // 나이 등급 로드
        this.ageRating = response.data.age_rating || null
        
        // 로컬 사용자 정보도 업데이트
        const userData = await authService.getUser()
        if (userData) {
          const updatedUser = {
            ...userData,
            email: this.userInfo.email,
            first_name: this.userInfo.first_name,
            last_name: this.userInfo.last_name,
            email_verified: this.emailVerified
          }
          await authService.storeAuthResult({ user: updatedUser })
        }
              } catch (error) {
          debugLog(this.$t('profile.messages.loading'), error, 'error')
          this.showToastNotification(this.$t('profile.load.failed'), 'error')
        }
    },
    
    async updateUserInfo() {
      try {
        await axios.patch('/api/user-profile/update/', {
          email: this.userInfo.email,
          first_name: this.userInfo.first_name,
          last_name: this.userInfo.last_name
        })
        
        this.showToastNotification(this.$t('profile.userInfo.update.success'), 'success')
              } catch (error) {
          debugLog(this.$t('profile.messages.userInfoUpdateFailed'), error, 'error')
          this.showToastNotification(this.$t('profile.userInfo.update.failed'), 'error')
        }
    },
    
        async updateRandomExamSettings() {
      try {
        const response = await axios.patch('/api/user-profile/update/', {
          random_exam_email_enabled: this.randomExamSettings.emailEnabled,
          random_exam_question_count: this.randomExamSettings.questionCount
        })
        
        // Quiz Count가 변경된 경우 관련 캐시 정리 및 안내
        if (this.randomExamSettings.questionCount !== this.previousQuestionCount) {
          const oldCount = this.previousQuestionCount
          this.previousQuestionCount = this.randomExamSettings.questionCount
          
          this.clearExamRelatedCache()
          this.clearExamManagementCache()
          
          // Quiz Count 변경 시 사용자에게 안내
          this.showToastNotification(
            `Quiz Count가 ${oldCount}에서 ${this.randomExamSettings.questionCount}로 변경되었습니다. exam-management 페이지에서 Today's exam이 자동으로 업데이트됩니다.`, 
            'info'
          )
        }
        
        // 백엔드 응답에서 업데이트된 값을 사용하여 로컬 상태 업데이트
        if (response.data.random_exam_question_count !== undefined) {
          this.randomExamSettings.questionCount = response.data.random_exam_question_count
          this.previousQuestionCount = response.data.random_exam_question_count
        }
        
        this.showToastNotification(this.$t('profile.randomExam.update.success'), 'success')
      } catch (error) {
        debugLog(this.$t('profile.messages.settingsUpdateFailed'), error, 'error')
        this.showToastNotification(this.$t('profile.randomExam.update.failed'), 'error')
        
        // 에러 발생 시 이전 값으로 되돌리기
        this.randomExamSettings.questionCount = this.previousQuestionCount
      }
    },

    async updateTranslationSettings() {
      try {
        sessionStorage.setItem('autoEnabled', this.translationSettings.autoEnabled.toString())
        await axios.patch('/api/user-profile/update/', {
          auto_translation_enabled: this.translationSettings.autoEnabled
        })

        this.previousAutoTranslationEnabled = this.translationSettings.autoEnabled
        this.showToastNotification(this.$t('profile.translation.update.success'), 'success')
      } catch (error) {
        debugLog(this.$t('profile.translation.update.failed'), error, 'error')
        this.translationSettings.autoEnabled = this.previousAutoTranslationEnabled
        this.showToastNotification(this.$t('profile.translation.update.failed'), 'error')
      }
    },
    
    async loadCategories() {
      this.loadingCategories = true
      try {
        const response = await axios.get('/api/tag-categories/tree/', {
          params: {
            is_active: true
          }
        }).catch(() => {
          // tree API가 없으면 일반 API 사용
          return axios.get('/api/tag-categories/', {
            params: {
              is_active: true
            }
          })
        })
        
        // 트리 구조를 평면화 (표시용) + 트리 구조 유지 (경로 생성용)
        const flattenCategories = (categories) => {
          let result = []
          categories.forEach(cat => {
            if (cat && cat.is_active !== false) {
              result.push(cat)
              if (cat.children && cat.children.length > 0) {
                result = result.concat(flattenCategories(cat.children))
              }
            }
          })
          return result
        }
        
        const categories = response.data || []
        if (Array.isArray(categories) && categories.length > 0 && categories[0].children) {
          // 트리 구조인 경우 평면화 (표시용)
          this.availableCategories = flattenCategories(categories)
          // 트리 구조도 유지 (경로 생성용)
          this.categoryTree = categories.filter(cat => cat && cat.is_active !== false)
        } else {
          // 평면 구조인 경우 그대로 사용
          this.availableCategories = (categories || []).filter(cat => cat && cat.is_active !== false)
          this.categoryTree = (categories || []).filter(cat => cat && cat.is_active !== false)
        }
      } catch (error) {
        debugLog('카테고리 로드 실패:', error, 'error')
        this.availableCategories = []
        this.categoryTree = []
      } finally {
        this.loadingCategories = false
      }
    },
    getCategoryDisplayName(category) {
      const locale = this.$i18n.locale || 'en'
      
      // 현재 언어에 맞는 카테고리 이름 우선 사용
      // full_path는 사용자 프로필 언어로 생성될 수 있어서 신뢰하지 않음
      // 카테고리 트리에서 부모 경로 찾아서 경로 생성
      return this.buildCategoryPath(category, locale)
    },
    buildCategoryPath(category, locale) {
      // 카테고리 트리에서 부모 경로 찾기
      if (!this.categoryTree || this.categoryTree.length === 0) {
        // 트리가 없으면 현재 언어에 맞는 이름만 반환
        return getLocalizedContent(category, 'name', locale) || category.full_path || `Category ${category.id}`
      }
      
      // 카테고리 트리에서 현재 카테고리와 부모 찾기
      const findCategoryInTree = (catId, tree, path = []) => {
        for (const cat of tree) {
          const currentPath = [...path]
          // 현재 언어에 맞는 이름 추가
          const name = getLocalizedContent(cat, 'name', locale)
          
          if (name) {
            currentPath.push(name)
          }
          
          // 찾는 카테고리인 경우 경로 반환
          if (cat.id === catId) {
            return currentPath
          }
          
          // 자식이 있으면 재귀적으로 검색
          if (cat.children && Array.isArray(cat.children) && cat.children.length > 0) {
            const found = findCategoryInTree(catId, cat.children, currentPath)
            if (found) {
              return found
            }
          }
        }
        return null
      }
      
      // 카테고리 트리에서 경로 찾기
      const path = findCategoryInTree(category.id, this.categoryTree)
      if (path && path.length > 0) {
        return path.join(' > ')
      }
      
      // 경로를 찾지 못한 경우 현재 언어에 맞는 이름만 반환
      return getLocalizedContent(category, 'name', locale) || category.full_path || `Category ${category.id}`
    },
    openCategoryFilterModal() {
      this.showCategoryFilterModal = true
    },
    handleSelectedCategoriesUpdate(selectedCategoryIds) {
      this.interestedCategories = selectedCategoryIds
    },
    handleCategoryFilterApply(selectedCategoryIds) {
      console.log('🔄 handleCategoryFilterApply 호출됨, selectedCategoryIds:', selectedCategoryIds)
      
      // 선택된 카테고리 ID를 직접 사용
      this.interestedCategories = selectedCategoryIds || []
      this.updateInterestedCategories()
    },
    handleCategoryFilterError(error) {
      debugLog('카테고리 필터 오류:', error, 'error')
      this.showToastNotification(
        this.$t('profile.interestedCategories.updateFailed') || '카테고리 선택에 실패했습니다.',
        'error'
      )
    },
    removeCategory(categoryId) {
      const index = this.interestedCategories.indexOf(categoryId)
      if (index > -1) {
        this.interestedCategories.splice(index, 1)
        this.updateInterestedCategories()
      }
    },
    async updateInterestedCategories() {
      if (this.updatingCategories) {
        console.log('⚠️ 이미 업데이트 중입니다.')
        return
      }
      
      console.log('🔄 updateInterestedCategories 호출됨')
      console.log('📊 저장할 interestedCategories:', this.interestedCategories)
      
      this.updatingCategories = true
      try {
        const response = await axios.patch('/api/user-profile/', {
          interested_categories: this.interestedCategories || []
        })
        
        console.log('✅ API 응답:', response.data)
        
        // 응답에서 실제 저장된 데이터 확인 및 동기화
        if (response.data && response.data.interested_categories !== undefined) {
          console.log('📊 응답에서 받은 interested_categories:', response.data.interested_categories)
          this.interestedCategories = response.data.interested_categories || []
        } else {
          console.log('⚠️ 응답에 interested_categories 없음, 프로필 다시 로드')
          // 응답에 데이터가 없으면 프로필 다시 로드
          await this.loadUserProfile()
        }
        
        this.showToastNotification(
          this.$t('profile.interestedCategories.updateSuccess') || '관심 카테고리가 업데이트되었습니다.',
          'success'
        )
      } catch (error) {
        console.error('❌ 관심 카테고리 업데이트 실패:', error)
        console.error('❌ 에러 상세:', error.response?.data || error.message)
        debugLog('관심 카테고리 업데이트 실패:', error, 'error')
        // 오류 발생 시 프로필 다시 로드하여 서버 상태와 동기화
        await this.loadUserProfile()
        this.showToastNotification(
          this.$t('profile.interestedCategories.updateFailed') || '관심 카테고리 업데이트에 실패했습니다.',
          'error'
        )
      } finally {
        this.updatingCategories = false
      }
    },
    async updateRetentionSettings() {
      try {
        await axios.patch('/api/user-profile/', {
          retention_cleanup_enabled: this.retentionSettings.enabled,
          retention_cleanup_percentage: this.retentionSettings.percentage
        })
        
        // 프로필 업데이트 후 최신 데이터를 다시 로드하여 즉시 반영
        await this.loadUserProfile()
        
        this.showToastNotification(this.$t('profile.retention.updateSuccess'), 'success')
      } catch (error) {
        debugLog('Retention Cleanup 설정 업데이트 실패:', error, 'error')
        this.showToastNotification(this.$t('profile.retention.updateFailed'), 'error')
      }
    },
    
    async runManualCleanup() {
      this.cleanupRunning = true
      try {
        const response = await axios.post('/api/retention-cleanup/manual/', {
          percentage: this.retentionSettings.percentage
        })
        
        const deletedCount = response.data.deleted_count || 0
        this.showToastNotification(this.$t('profile.retention.cleanupSuccess', { count: deletedCount }), 'success')
      } catch (error) {
        debugLog('수동 정리 실패:', error, 'error')
        this.showToastNotification(this.$t('profile.retention.cleanupFailed'), 'error')
      } finally {
        this.cleanupRunning = false
      }
    },
    

    
    async exportUserData() {
      this.exporting = true
      try {
        const response = await axios.get('/api/export-user-data/', {
          responseType: 'blob'
        })
        
        // 파일 다운로드
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        
        // 파일명 추출 (Content-Disposition 헤더에서)
        const contentDisposition = response.headers['content-disposition']
        let filename = 'user_data_export.xlsx'
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
        
        this.showToastNotification(this.$t('profile.export.success'), 'success')
      } catch (error) {
        debugLog(this.$t('profile.messages.exportFailed'), error, 'error')
        this.showToastNotification(this.$t('profile.export.failed'), 'error')
      } finally {
        this.exporting = false
      }
    },



    showStatisticsResetConfirm() {
      this.showStatisticsResetModal = true
      this.resetConfirmation = ''
    },

    hideStatisticsResetConfirm() {
      this.showStatisticsResetModal = false
      this.resetConfirmation = ''
    },



    async confirmStatisticsReset() {
      if (!this.canConfirmReset) return

      this.resettingStatistics = true
      try {
        // 백엔드 API 호출하여 통계 초기화
        const response = await axios.post('/api/user-statistics/reset/', {
          user_id: this.userInfo.id || this.userInfo.username
        })

        if (response.data.success) {
          this.showToastNotification(this.$t('profile.statistics.reset.success'), 'success')
          
          // 모달 닫기
          this.hideStatisticsResetConfirm()
          
          // 홈페이지 캐시 무효화 (진행률 초기화를 위해)
          try {
            sessionStorage.setItem('forceRefreshHome', 'true')
            localStorage.removeItem('homeData')
            console.log('✅ 통계 초기화 후 홈페이지 캐시 무효화 완료')
          } catch (cacheError) {
            console.warn('⚠️ 홈페이지 캐시 무효화 실패:', cacheError)
          }
          
          // 페이지 새로고침 (캐시 무효화를 위해)
          setTimeout(() => {
            window.location.reload()
          }, 1500)
        } else {
          this.showToastNotification(this.$t('profile.statistics.reset.failed'), 'error')
        }
      } catch (error) {
        debugLog('통계 초기화 실패:', error, 'error')
        this.showToastNotification(this.$t('profile.statistics.reset.error'), 'error')
      } finally {
        this.resettingStatistics = false
      }
    },



    async onChangePassword() {
      if (this.passwordForm.new1 !== this.passwordForm.new2) {
        this.showToastNotification(this.$t('profile.password.mismatch'), 'error')
        return
      }
      
      try {
        // Django 백엔드에서 자동으로 bcrypt 해시화 처리
        // 프론트엔드에서는 평문으로 전송
        await axios.post(`/api/user/${this.userInfo.id}/change-password/`, {
          new_password: this.passwordForm.new1
        })
        
        this.showToastNotification(this.$t('profile.password.change.success'), 'success')

        // 비밀번호 변경 후 자동으로 다시 로그인
        try {
          const loginResponse = await axios.post('/api/login/', {
            username: this.userInfo.username,
            password: this.passwordForm.new1
          })

          if (loginResponse.data.success) {
            await authService.storeAuthResult(loginResponse.data)

            // 로그인 성공 후 비밀번호 필드 비우기
            this.passwordForm.new1 = ''
            this.passwordForm.new2 = ''
          }
        } catch (loginErr) {
          debugLog('자동 로그인 실패:', loginErr, 'error')
          this.showToastNotification('비밀번호가 변경되었습니다. 다시 로그인해주세요.', 'info')
        }
      } catch (err) {
        this.showToastNotification(this.$t('profile.password.change.failed'), 'error')
      }
    },
    
    checkPasswordMatch() {
      if (this.passwordForm.new1 === this.passwordForm.new2) {
        this.passwordError = '';
      } else {
        this.passwordError = this.$t('profile.password.mismatch');
      }
    },

    // 캐시 설정 업데이트
    updateCacheSettings() {
      try {
        localStorage.setItem('cacheEnabled', this.cacheSettings.enabled.toString())
        
        if (!this.cacheSettings.enabled) {
          // 캐시 비활성화 시 기존 캐시 삭제
          this.clearAllCache()
          sessionStorage.setItem('cacheDisabled', 'true')
        } else {
          // 캐시 활성화 시 비활성화 플래그 제거
          sessionStorage.removeItem('cacheDisabled')
        }
        
        this.showToastNotification(
          this.cacheSettings.enabled ? this.$t('profile.cache.enabled') : this.$t('profile.cache.disabled'), 
          'success'
        )
      } catch (error) {
        debugLog(this.$t('profile.messages.cacheUpdateFailed'), error, 'error')
        this.showToastNotification('캐시 설정 업데이트에 실패했습니다.', 'error')
      }
    },
    
    // 시험 관련 캐시만 정리
    clearExamRelatedCache() {
      try {
        // 시험 관리 관련 캐시 정리
        const examKeys = [
          'examManagementCache',
          'forceRefreshExamManagement',
          'forceRefreshHome'
        ]
        
        examKeys.forEach(key => {
          sessionStorage.removeItem(key)
          localStorage.removeItem(key)
        })
        
        // Today's exam 관련 캐시 정리
        const todayExamKeys = Object.keys(sessionStorage).filter(key => 
          key.includes('Today') || key.includes('daily') || key.includes('quiz')
        )
        todayExamKeys.forEach(key => sessionStorage.removeItem(key))
        
        // 강제 새로고침 플래그 설정
        sessionStorage.setItem('forceRefreshExamManagement', 'true')
        sessionStorage.setItem('forceRefreshHome', 'true')
        
        debugLog('시험 관련 캐시 정리 완료')
      } catch (error) {
        debugLog('시험 관련 캐시 정리 중 오류:', error, 'error')
      }
    },
    
    // ExamManagement 페이지 캐시 정리
    clearExamManagementCache() {
      try {
        // ExamManagement 관련 모든 캐시 정리
        const examManagementKeys = [
          'forceRefreshExamManagement',
          'examManagementCache'
        ]
        
        examManagementKeys.forEach(key => {
          sessionStorage.removeItem(key)
          localStorage.removeItem(key)
        })
        
        // 사용자별 Quiz Count 캐시도 정리
        const user = authService.getUserSync()
        if (user && user.username) {
          sessionStorage.removeItem(`quizCount_${user.username}`)
        }
        
        // 강제 새로고침 플래그 설정
        sessionStorage.setItem('forceRefreshExamManagement', 'true')
        
        debugLog('ExamManagement 페이지 캐시 정리 완료')
      } catch (error) {
        debugLog('ExamManagement 페이지 캐시 정리 중 오류:', error, 'error')
      }
    },
    
    // 모든 캐시 삭제
    clearAllCache() {
      try {
        // sessionStorage의 모든 캐시 키 삭제
        const keysToRemove = []
        for (let i = 0; i < sessionStorage.length; i++) {
          const key = sessionStorage.key(i)
          if (key && (
            key.startsWith('examManagement') ||
            key.startsWith('homeData') ||
            key.startsWith('studyManagement_') ||
            key.startsWith('forceRefresh') ||
            key === 'cacheDisabled'
          )) {
            keysToRemove.push(key)
          }
        }
        
        keysToRemove.forEach(key => sessionStorage.removeItem(key))
        
        // localStorage의 홈페이지 관련 캐시도 삭제
        try {
          localStorage.removeItem('homeData')
          console.log('✅ localStorage 홈페이지 캐시 삭제 완료')
        } catch (localStorageError) {
          console.warn('⚠️ localStorage 홈페이지 캐시 삭제 실패:', localStorageError)
        }
        
        this.showToastNotification(this.$t('profile.cache.cleared'), 'success')
        debugLog(this.$t('profile.messages.cacheCleared'))
      } catch (error) {
        debugLog(this.$t('profile.messages.cacheClearFailed'), error, 'error')
        this.showToastNotification(this.$t('profile.cache.clearFailed'), 'error')
      }
    },
    
    async sendEmailVerification() {
      this.sendingEmail = true
      try {
        const response = await axios.post('/api/send-email-verification/')
        
        if (response.data.message) {
          this.showToastNotification(response.data.message, 'success')

          // 이미 인증된 경우 상태 업데이트
          if (response.data.email_verified) {
            this.emailVerified = true

            const userData = await authService.getUser()
            if (userData) {
              await authService.storeAuthResult({
                user: {
                  ...userData,
                  email_verified: true
                }
              })
            }
          }
        } else if (response.data.error) {
          this.showToastNotification(response.data.error, 'error')
        }
      } catch (error) {
        debugLog('이메일 인증 발송 실패:', error, 'error')
        if (error.response && error.response.data && error.response.data.error) {
          this.showToastNotification(error.response.data.error, 'error')
        } else {
          this.showToastNotification(this.$t('profile.emailVerification.failed'), 'error')
        }
      } finally {
        this.sendingEmail = false
      }
    },

    // 시험 제목을 사용자 언어에 맞게 반환하는 메서드
    // 서버에서 이미 사용자 언어에 맞는 title을 반환하므로, 이를 직접 사용
    getExamTitle(exam) {
      return exam.title || '제목 없음'
    },

    // 랜덤 시험 목록 관리 메서드들
    async loadMyExams() {
      this.loadingMyExams = true
      try {
        // get_user_my_exams API 사용 (사용자 언어에 맞는 title 필드 반환)
        const response = await axios.get('/api/user-exams/my-exams/')
        debugLog('My Exams API 응답:', response.data)
        
        // 데이터 구조에 따라 적절히 처리
        if (response.data && response.data.exams) {
          this.myExams = response.data.exams
        } else if (Array.isArray(response.data)) {
          this.myExams = response.data
        } else {
          this.myExams = []
        }
        
        debugLog('로드된 My Exams:', this.myExams)
      } catch (error) {
        debugLog('My Exams 로드 실패:', error, 'error')
        this.showToastNotification('My Exams 로드에 실패했습니다.', 'error')
      } finally {
        this.loadingMyExams = false
      }
    },

    async loadSubscribedExams() {
      this.loadingSubscriptions = true
      try {
        const response = await axios.get('/api/user-exams/subscribed-exams/')
        debugLog('Subscribed Exams API 응답:', response.data)
        
        // 데이터 구조에 따라 적절히 처리
        if (response.data && response.data.exams) {
          this.subscribedExams = response.data.exams
        } else if (Array.isArray(response.data)) {
          this.subscribedExams = response.data
        } else {
          this.subscribedExams = []
        }
        
        debugLog('로드된 Subscribed Exams:', this.subscribedExams)
      } catch (error) {
        debugLog('Subscribed Exams 로드 실패:', error, 'error')
        this.showToastNotification('Subscribed Exams 로드에 실패했습니다.', 'error')
      } finally {
        this.loadingSubscriptions = false
      }
    },

    async toggleMyExamSelection(examId) {
      const index = this.selectedMyExams.indexOf(examId)
      if (index > -1) {
        this.selectedMyExams.splice(index, 1)
      } else {
        this.selectedMyExams.push(examId)
      }
    },

    async toggleSubscribedExamSelection(examId) {
      const index = this.selectedSubscribedExams.indexOf(examId)
      if (index > -1) {
        this.selectedSubscribedExams.splice(index, 1)
      } else {
        this.selectedSubscribedExams.push(examId)
      }
    },

    async moveToSubscribed() {
      if (this.selectedMyExams.length === 0) {
        this.showToastNotification(this.$t('profile.exam.noExamsSelected'), 'warning')
        return
      }
      this.loadingSubscriptions = true
      try {
        await axios.post('/api/user-exams/move-to-subscribed/', {
          exam_ids: this.selectedMyExams
        })
        this.showToastNotification(this.$t('profile.exam.moveToSubscribedSuccess'), 'success')
        this.selectedMyExams = []
        // My Exams 목록 새로고침
        this.loadMyExams()
        // Subscribed Exams 목록도 새로고침
        this.loadSubscribedExams()
      } catch (error) {
        debugLog('My Exams에서 Subscribed Exams로 이동 실패:', error, 'error')
        this.showToastNotification(this.$t('profile.exam.moveToSubscribedFailed'), 'error')
      } finally {
        this.loadingSubscriptions = false
      }
    },

    async moveToMyExams() {
      if (this.selectedSubscribedExams.length === 0) {
        this.showToastNotification(this.$t('profile.exam.noExamsSelected'), 'warning')
        return
      }
      this.loadingSubscriptions = true
      try {
        await axios.post('/api/user-exams/move-to-my-exams/', {
          exam_ids: this.selectedSubscribedExams
        })
        this.showToastNotification(this.$t('profile.exam.moveToMyExamsSuccess'), 'success')
        this.selectedSubscribedExams = []
        // Subscribed Exams 목록 새로고침
        this.loadSubscribedExams()
        // My Exams 목록도 새로고침
        this.loadMyExams()
      } catch (error) {
        debugLog('Subscribed Exams에서 My Exams로 이동 실패:', error, 'error')
        this.showToastNotification(this.$t('profile.exam.moveToMyExamsFailed'), 'error')
      } finally {
        this.loadingSubscriptions = false
      }
    },

    showWithdrawalConfirm() {
      this.showWithdrawalModal = true
    },

    hideWithdrawalConfirm() {
      this.showWithdrawalModal = false
    },

    async confirmWithdrawal() {
      this.withdrawing = true
      try {
        const response = await axios.delete('/api/delete-my-account/')
        if (response.data.message) {
          this.showToastNotification(this.$t('profile.withdrawal.success'), 'success')
          this.hideWithdrawalConfirm()
          
          // 성공 메시지를 보여준 후 잠시 후 로그아웃 처리
          setTimeout(async () => {
            try {
              await authService.clearAuth()
            } catch (clearError) {
              debugLog('로그아웃 정리 중 오류:', clearError, 'error')
            }
            sessionStorage.clear()
            this.$router.push('/login')
          }, 2000)
        } else {
          this.showToastNotification(this.$t('profile.withdrawal.failed'), 'error')
        }
      } catch (error) {
        debugLog('계정 탈퇴 실패:', error, 'error')
        if (error.response && error.response.data && error.response.data.detail) {
          this.showToastNotification(error.response.data.detail, 'error')
        } else {
          this.showToastNotification(this.$t('profile.withdrawal.error'), 'error')
        }
      } finally {
        this.withdrawing = false
      }
    }

  }
}
</script>

<style scoped>
.profile-modern {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  color: white;
}

.loading-spinner {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.loading-text {
  font-size: 1.1rem;
  opacity: 0.9;
}

.profile-container {
  max-width: 800px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.top-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.page-title h1 {
  color: white;
  font-size: 2.5rem;
  font-weight: 700;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-actions {
  display: flex;
  gap: 1rem;
}

.card-modern {
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.card-modern:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
}

  .card-header-modern {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1.5rem 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  
  @media (max-width: 768px) {
    .card-header-modern {
      padding: 10px 20px;
    }
  }

.card-header-modern h3 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.age-rating-badge {
  display: inline-block;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.875rem;
  font-weight: 600;
  margin-left: 0.5rem;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.card-body-modern {
  padding: 2rem;
}

  .form-group {
    margin-bottom: 10px;
  }

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

  .form-label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 600;
    color: #2c3e50;
    font-size: 0.95rem;
  }
  
  @media (max-width: 768px) {
    .form-label {
      margin-bottom: 0.25rem;
      font-size: 0.9rem;
    }
  }

  .form-control-modern {
    width: 100%;
    padding: 0.75rem 1rem;
    border: 2px solid #e1e5e9;
    border-radius: 8px;
    font-size: 1rem;
    transition: all 0.3s ease;
    background: white;
  }
  
  @media (max-width: 768px) {
    .form-control-modern {
      padding: 0.5rem 0.75rem;
      font-size: 0.9rem;
    }
  }

.form-control-modern:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-control-modern:read-only {
  background: #f8f9fa;
  color: #6c757d;
}

.checkbox-group {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.checkbox-modern {
  width: 1.25rem;
  height: 1.25rem;
  accent-color: #667eea;
}

.checkbox-label {
  font-weight: 500;
  color: #2c3e50;
  cursor: pointer;
}

.form-text {
  color: #6c757d;
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

.form-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
  justify-content: flex-end;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.3s ease;
  text-decoration: none;
  min-width: 120px;
  justify-content: center;
}

.action-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.action-btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.action-btn-primary:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.action-btn-success {
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  color: white;
}

.action-btn-success:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
}

.action-btn-warning {
  background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%);
  color: white;
}

.action-btn-warning:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(255, 193, 7, 0.3);
}

.action-btn-secondary {
  background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
  color: white;
}

.action-btn-secondary:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(108, 117, 125, 0.3);
}

.action-btn-danger {
  border-color: #dc3545;
  background-color: #dc3545;
  color: white;
}

.action-btn-danger:hover:not(:disabled) {
  background-color: #c82333;
  border-color: #bd2130;
}

  .action-label {
    font-weight: 500;
  }
  
  /* 이메일 입력 그룹 스타일 */
  .email-input-group {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .email-input-row {
    display: flex;
    gap: 1rem;
    align-items: center;
  }
  
  .email-input {
    flex: 1;
  }
  
  .email-status-badges {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
  }
  
  .status-badge {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-weight: 500;
    font-size: 0.9rem;
    white-space: nowrap;
  }
  
  .status-badge.verified {
    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
    color: white;
  }
  
  .status-badge.not-verified {
    background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%);
    color: white;
  }
  
  .verification-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 0.9rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s ease;
    text-decoration: none;
    white-space: nowrap;
    min-width: 120px;
  }
  
  .verification-btn:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  }
  
  .verification-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

/* 토스트 알림 스타일 - 모든 스타일은 공통 CSS (mobile-buttons.css)에 정의됨 */

.toast-close:hover {
  background: #f8f9fa;
  color: #495057;
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

/* 슬라이더 스타일 */
.slider-container {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.5rem;
}

.slider {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: #e9ecef;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #007bff;
  cursor: pointer;
  border: 2px solid #fff;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #007bff;
  cursor: pointer;
  border: 2px solid #fff;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.slider-value {
  font-weight: 600;
  color: #007bff;
  min-width: 3rem;
  text-align: center;
}

/* 반응형 디자인 */
@media (max-width: 768px) {
  .profile-modern {
    padding: 10px;
  }
  
  .page-title h1 {
    font-size: 2rem;
  }
  
  .top-header {
    display: none; /* 모바일에서 top-header 숨김 */
  }
  
  .card-body-modern {
    padding: 10px 20px;
  }
  
  .form-row {
    grid-template-columns: 1fr;
    gap: 0.5rem;
  }
  
  .form-actions {
    flex-direction: row;
    justify-content: flex-end;
  }
  
  .action-btn {
    width: auto;
  }
  
  .email-input-row {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .email-input {
    width: 100%;
  }
  
  .email-status-badges {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .verification-btn {
    width: 100%;
    justify-content: center;
  }
  
  .toast-notification {
    right: 10px;
    left: 10px;
    max-width: none;
  }
}

/* 패스워드 일치 여부 표시기 스타일 */
.password-match-indicator {
  margin-top: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  transition: all 0.3s ease;
}



.reset-impact-list {
  margin: 1rem 0;
  padding-left: 1.5rem;
}

.reset-impact-list li {
  margin-bottom: 0.5rem;
  color: #6c757d;
}

.alert-warning {
  background-color: #fff3cd;
  border-color: #ffeaa7;
  color: #856404;
}

.alert-warning i {
  color: #f39c12;
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
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.modal-header {
  padding: 1.5rem 1.5rem 1rem;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-title {
  margin: 0;
  font-size: 1.25rem;
  color: #495057;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #6c757d;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s ease;
}

.modal-close:hover {
  background: #f8f9fa;
  color: #495057;
}

.modal-body {
  padding: 1.5rem;
}

.modal-footer {
  padding: 1rem 1.5rem 1.5rem;
  border-top: 1px solid #e9ecef;
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #5a6268;
}

.btn-danger {
  background: #dc3545;
  color: white;
}

.btn-danger:hover {
  background: #c82333;
}

.btn-danger:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

/* 계정 탈퇴 처리 중 스타일 */
.withdrawing .modal-content {
  opacity: 0.8;
  pointer-events: none;
}

.withdrawing .modal-content .modal-header,
.withdrawing .modal-content .modal-body,
.withdrawing .modal-content .modal-footer {
  pointer-events: auto;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.modal-close:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.password-match-indicator i {
  font-size: 1rem;
}

.text-success {
  color: #28a745 !important;
}

.text-danger {
  color: #dc3545 !important;
}

/* 랜덤 시험 관리 섹션 스타일 */
.exam-management-section {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e9ecef;
}

.section-title {
  margin-bottom: 1rem;
  font-size: 1.25rem;
  font-weight: 600;
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.exam-lists-container {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  margin-bottom: 1rem;
  min-height: 300px;
}

.exam-list-section {
  width: 100%;
  flex: 1;
  min-width: 250px;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  min-height: 300px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.list-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 500;
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.shuffle-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  white-space: nowrap;
}

.shuffle-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.shuffle-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.exam-controls {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  justify-content: center;
  padding: 0 1rem;
  min-width: 80px;
  align-self: center;
}

.exam-list {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 12px;
  overflow: hidden;
  /* flex: 1 제거 - 높이 고정을 위해 */
  display: flex;
  flex-direction: column;
  height: 290px; /* 5개 exam-item (48px * 5) + 여백 (50px) */
  overflow-y: auto;
}

/* 스크롤바 스타일링 */
.exam-list::-webkit-scrollbar {
  width: 8px;
}

.exam-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.exam-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.exam-list::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.exam-items {
  padding: 0.5rem;
  /* flex: 1 제거 - 높이 고정을 위해 */
  overflow-y: auto;
}

.exam-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
  background: white;
  border-radius: 8px;
  border: 1px solid #e9ecef;
  margin-bottom: 0.5rem;
  height: 48px; /* 고정 높이 설정 */
  box-sizing: border-box;
}

.exam-item:hover:not(.selected) {
  background: #f1f3f5;
  border-color: #dee2e6;
}

.exam-item.selected {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: #667eea;
}

.exam-item.selected .exam-title {
  color: white;
}

.exam-item.selected .selection-indicator {
  color: white;
}

.exam-title {
  flex: 1;
  font-weight: 500;
  color: #2c3e50;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.selection-indicator {
  font-size: 0.8rem;
  color: #6c757d;
}

.empty-list {
  padding: 1rem;
  text-align: center;
  color: #6c757d;
  font-style: italic;
}

.loading-indicator {
  display: flex;
  justify-content: center;
  padding: 1rem;
}

.control-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0.75rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 40px;
}

.control-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.control-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.exam-actions {
  display: flex;
  justify-content: center;
  margin-top: 1rem;
}

/* 반응형 디자인 */
@media (max-width: 768px) {
  .exam-lists-container {
    flex-direction: column;
    gap: 1rem;
  }
  
  .exam-controls {
    flex-direction: row;
    justify-content: center;
    padding: 0;
    min-width: auto;
  }
  
  .control-btn {
    width: auto;
    min-width: 60px;
  }
}

/* 계정 및 보안 섹션 */
.account-security-section {
  border: 2px solid #ffc107;
  background: linear-gradient(135deg, #fff9e6 0%, #ffffff 100%);
}

.account-security-section .card-header-modern {
  background: linear-gradient(135deg, #ffc107 0%, #ff9800 100%);
  color: white;
}

.account-security-section .card-header-modern h3 {
  color: white;
}

.security-subsection {
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid #e9ecef;
}

.security-subsection:last-child {
  margin-bottom: 10px;
  padding-bottom: 10px;
}

.subsection-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #333;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* 계정 삭제 서브섹션 */
.account-deletion-subsection {
  background: #fff5f5;
  border: 2px solid #fecaca;
  border-radius: 8px;
  padding: 1.5rem;
  margin-top: 1.5rem;
}

.account-deletion-header {
  margin-bottom: 1rem;
}

.account-deletion-title {
  color: #dc3545;
  font-size: 1.3rem;
  font-weight: 700;
}

.account-deletion-content {
  margin-top: 1rem;
}

.account-deletion-button-wrapper {
  margin-top: 1.5rem;
  display: flex;
  justify-content: center;
}

.account-deletion-btn {
  min-width: 200px;
  padding: 0.875rem 2rem;
  font-size: 1rem;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(220, 53, 69, 0.3);
  transition: all 0.3s ease;
}

.account-deletion-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(220, 53, 69, 0.4);
  background-color: #c82333;
}

.account-deletion-btn:active:not(:disabled) {
  transform: translateY(0);
}

.withdrawal-warning {
  background-color: #fff3cd;
  border-color: #ffeaa7;
  color: #856404;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.withdrawal-description {
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

.withdrawal-impact-list {
  margin-top: 0.5rem;
  padding-left: 1.5rem;
}

.withdrawal-impact-list li {
  margin-bottom: 0.5rem;
  color: #6c757d;
}

.withdrawal-btn {
  background: #dc3545;
  color: white;
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.withdrawal-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(220, 53, 69, 0.3);
}

.withdrawal-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Tag Filter Button Styles */
.tag-filter-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: 1px solid #007bff;
  border-radius: 8px;
  background-color: transparent;
  color: #007bff;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.tag-filter-btn:hover {
  background-color: #007bff;
  color: white;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3);
}

.tag-filter-btn .badge {
  margin-left: 0.5rem;
}

.category-selection-container {
  margin-top: 0.5rem;
}

.category-selection-container .badge {
  display: inline-flex;
  align-items: center;
  justify-content: flex-start;
  gap: 0.25rem;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  max-width: 100%;
  white-space: normal;
  word-wrap: break-word;
  overflow-wrap: break-word;
  flex-wrap: wrap;
  text-align: left;
}

.category-selection-container .btn-close {
  font-size: 0.7em;
  opacity: 0.8;
}

.category-selection-container .btn-close:hover {
  opacity: 1;
}

@media (max-width: 768px) {
  .tag-filter-btn {
    padding: 0.5rem 0.75rem;
    font-size: 0.875rem;
  }
  
  .category-selection-container .d-flex {
    justify-content: space-between;
  }
  
  .category-selection-container .d-flex > div:first-child {
    flex: 1 1 auto;
    min-width: 0;
  }
  
  .category-selection-container .tag-filter-btn {
    flex: 0 0 auto;
    margin-left: auto;
  }
  
  .form-group .action-btn-warning {
    margin-left: auto;
    display: block;
  }
  
  .account-deletion-button-wrapper {
    display: flex;
    justify-content: flex-end;
  }
  
  .account-deletion-button-wrapper .account-deletion-btn {
    margin-left: auto;
  }
}
</style>