<template>
  <div class="entity-tag-filter">
    <!-- Tag Filter Button -->
    <button 
      @click="openTagFilterModal" 
      class="action-btn action-btn-outline-primary tag-filter-btn modern-tag-filter-btn"
      :title="$t('tagFilterModal.title')"
    >
      <i class="fas fa-tags"></i>
      <span class="action-label">{{ $t('tagFilterModal.title') }}</span>
      <span v-if="selectedTags.length > 0" class="badge bg-primary ms-2">{{ selectedTags.length }}</span>
    </button>

    <!-- Selected Tags Display -->
    <div v-if="selectedTags.length > 0" class="selected-tags-display mt-2">
      <div class="d-flex align-items-center flex-wrap gap-2">
        <span class="text-muted small">{{ $t('tagFilter.selectedTags') }}:</span>
        <span 
          v-for="tagId in selectedTags" 
          :key="tagId"
          class="badge bg-primary"
        >
          {{ getSelectedTagName(tagId) }}
          <button @click="removeTag(tagId)" class="btn-close btn-close-white ms-1" style="font-size: 0.7em;"></button>
        </span>
      </div>
    </div>

    <!-- Tag Filter Modal -->
    <TagFilterModal
      :show="showTagFilterModal"
      :selectedTags="selectedTags"
      @update:show="showTagFilterModal = $event"
      @update:selectedTags="handleSelectedTagsUpdate"
      @apply="handleTagFilterApply"
      @error="handleTagFilterError"
    />
  </div>
</template>

<script>
import axios from 'axios'
import TagFilterModal from '@/components/TagFilterModal.vue'
import { debugLog } from '@/utils/debugUtils'

export default {
  name: 'EntityTagFilter',
  components: {
    TagFilterModal
  },
  props: {
    entityType: {
      type: String,
      required: true,
      validator: value => ['study', 'exam'].includes(value)
    },
    entityId: {
      type: [String, Number],
      required: true
    },
    initialSelectedTags: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      selectedTags: [...this.initialSelectedTags],
      showTagFilterModal: false,
      availableTags: [] // 모든 태그 목록 (이름 표시용)
    }
  },
  async mounted() {
    await this.loadAvailableTags()
  },
  methods: {
    async loadAvailableTags() {
      try {
        debugLog('🔄 EntityTagFilter loadAvailableTags 시작')
        const response = await axios.get('/api/studies/tags/') // 공통 태그 API 사용
        this.availableTags = response.data || []
        debugLog('📊 EntityTagFilter 로드된 태그 수:', this.availableTags.length)
      } catch (error) {
        console.error('EntityTagFilter 태그 목록 로드 실패:', error)
        this.$emit('error', error)
      }
    },
    
    openTagFilterModal() {
      debugLog('🔄 EntityTagFilter openTagFilterModal 호출됨')
      this.showTagFilterModal = true
    },
    
    handleSelectedTagsUpdate(selectedTagIds) {
      debugLog('🔄 EntityTagFilter handleSelectedTagsUpdate 호출됨')
      this.selectedTags = selectedTagIds
    },
    
    handleTagFilterApply(selectedTagIds) {
      debugLog('🔄 EntityTagFilter handleTagFilterApply 호출됨')
      this.selectedTags = selectedTagIds
      this.$emit('tag-filter-changed', [...this.selectedTags])
      this.showTagFilterModal = false
    },
    
    handleTagFilterError(error) {
      debugLog('EntityTagFilter 에러 발생:', error)
      this.$emit('error', error)
    },
    
    getSelectedTagName(tagId) {
      const tag = this.availableTags.find(t => t.id === tagId)
      if (!tag) return 'Unknown'
      
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
      
      // 최종 폴백 - i18n 사용
      return this.$t('common.noTag') || 'No Tag'
    },
    
    removeTag(tagId) {
      this.selectedTags = this.selectedTags.filter(id => id !== tagId)
      this.$emit('tag-filter-changed', [...this.selectedTags])
    }
  }
}
</script>

<style scoped>
.entity-tag-filter {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}

.tag-filter-btn {
  /* Inherit styles from action-btn */
}

/* Modern Tag Filter Button Styling */
.modern-tag-filter-btn {
  border-radius: 8px !important;
  border: 2px solid var(--bs-primary) !important;
  background: white !important;
  color: var(--bs-primary) !important;
  font-weight: 500 !important;
  transition: all 0.3s ease !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
  display: flex !important;
  align-items: center !important;
  gap: 8px !important;
  padding: 10px 16px !important;
}

.modern-tag-filter-btn:hover:not(:disabled) {
  background: var(--bs-primary) !important;
  border-color: var(--bs-primary) !important;
  color: white !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 8px rgba(13, 110, 253, 0.25) !important;
}

.modern-tag-filter-btn i {
  font-size: 14px !important;
}

.modern-tag-filter-btn .badge {
  background: rgba(13, 110, 253, 0.2) !important;
  color: var(--bs-primary) !important;
  font-size: 11px !important;
  font-weight: 600 !important;
}

.modern-tag-filter-btn:hover:not(:disabled) .badge {
  background: rgba(255, 255, 255, 0.2) !important;
  color: white !important;
}

.selected-tags-display {
  padding: 8px 12px;
  background-color: #e9ecef;
  border-radius: 6px;
  border: 1px solid #dee2e6;
  font-size: 0.85em;
  color: #495057;
  width: 100%;
}

.selected-tags-display .badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 15px;
  font-size: 0.8em;
  margin-right: 6px;
  margin-bottom: 4px;
}

.selected-tags-display .btn-close {
  background: none;
  border: none;
  color: white;
  font-size: 0.6em;
  padding: 0;
  margin: 0;
  opacity: 0.8;
  transition: opacity 0.2s;
}

.selected-tags-display .btn-close:hover {
  opacity: 1;
}
</style>
