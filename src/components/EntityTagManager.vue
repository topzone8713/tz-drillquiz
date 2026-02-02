<template>
  <div class="entity-tag-manager">
    <div class="info-item">
      <div class="tags-management">
        <div class="tags-display" v-if="!isEditingTags">
          <div class="tags-list">
            <span 
              v-for="tag in currentTags" 
              :key="tag.id"
              class="tag-badge"
            >
              {{ getLocalizedTagName(tag) }}
              <button 
                @click="removeTag(tag.id)" 
                class="tag-remove-btn"
                :title="$t('common.removeTag') || '태그 제거'"
                v-if="canEdit"
              >
                <i class="fas fa-times"></i>
              </button>
            </span>
          </div>
          <button 
            @click="toggleTagEditMode" 
            class="btn btn-sm btn-outline-primary"
            v-if="canEdit"
          >
            <i class="fas fa-edit"></i>
            <span>{{ $t('common.manageTags') || '태그 관리' }}</span>
          </button>
        </div>
        
        <!-- Tag Filter Modal -->
        <TagFilterModal
          :show="isEditingTags"
          :selectedTags="editingTagIds"
          @update:show="handleModalClose"
          @update:selectedTags="handleTagSelectionChange"
          @apply="handleTagsApply"
          @error="handleTagError"
        />
      </div>
    </div>
  </div>
</template>

<script>
import TagFilterModal from '@/components/TagFilterModal.vue'
import axios from 'axios'

export default {
  name: 'EntityTagManager',
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
    tags: {
      type: Array,
      default: () => []
    },
    canEdit: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      currentTags: [],
      isEditingTags: false,
      editingTagIds: [],
      savingTags: false
    }
  },
  mounted() {
    // 초기 태그 설정
    this.currentTags = [...this.tags]
  },
  methods: {
    toggleTagEditMode() {
      this.isEditingTags = !this.isEditingTags
      if (this.isEditingTags) {
        this.editingTagIds = this.currentTags.map(tag => tag.id)
      }
    },
    
    cancelTagEdit() {
      this.isEditingTags = false
      this.editingTagIds = []
    },
    
    handleModalClose(show) {
      // 모달이 닫히면 편집 모드 취소
      if (!show) {
        this.cancelTagEdit()
      }
    },
    
    handleTagSelectionChange(newTagIds) {
      this.editingTagIds = [...newTagIds]
    },
    
    async handleTagsApply(selectedTagIds) {
      // TagFilterModal의 apply 이벤트에서 태그 저장
      this.editingTagIds = [...selectedTagIds]
      await this.saveTags()
    },
    
    async saveTags() {
      // 최소 1개 이상의 태그가 필요함
      if (this.editingTagIds.length === 0) {
        this.$emit('error', { message: this.$t('tagFilterModal.minOneTagRequired') || '최소 1개 이상의 태그를 선택해주세요.' })
        return
      }
      
      try {
        this.savingTags = true
        
        console.log('🔄 EntityTagManager saveTags 시작')
        
        // 엔티티 타입에 따라 다른 API 엔드포인트 사용
        const apiEndpoint = this.entityType === 'study' 
          ? `/api/studies/${this.entityId}/`
          : `/api/exam/${this.entityId}/update/`
        
        console.log('📡 API 엔드포인트:', apiEndpoint)
        console.log('📊 전송할 태그 IDs:', this.editingTagIds)
        
        const response = await axios.patch(apiEndpoint, {
          tags: this.editingTagIds
        })
        
        console.log('📡 API 응답:', response)
        console.log('📊 응답 데이터:', response.data)
        console.log('📊 응답의 tags 필드:', response.data.tags)
        
        // 성공 시 현재 태그 업데이트
        this.currentTags = response.data.tags || []
        console.log('📊 업데이트된 currentTags:', this.currentTags)
        
        // 모달 닫기
        this.isEditingTags = false
        this.editingTagIds = []
        
        this.$emit('tags-updated', this.currentTags)
        this.$emit('success', this.$t('common.tagsUpdated', '태그가 업데이트되었습니다.'))
        
      } catch (error) {
        console.error('태그 저장 실패:', error)
        this.$emit('error', error)
      } finally {
        this.savingTags = false
      }
    },
    
    async removeTag(tagId) {
      // 최소 1개 이상의 태그는 유지해야 함
      if (this.currentTags.length <= 1) {
        this.$emit('error', { message: this.$t('tagFilterModal.minOneTagRequired') || '최소 1개 이상의 태그가 필요합니다.' })
        return
      }
      
      try {
        const updatedTagIds = this.currentTags
          .filter(tag => tag.id !== tagId)
          .map(tag => tag.id)
        
        // 엔티티 타입에 따라 다른 API 엔드포인트 사용
        const apiEndpoint = this.entityType === 'study' 
          ? `/api/studies/${this.entityId}/`
          : `/api/exam/${this.entityId}/update/`
        
        const response = await axios.patch(apiEndpoint, {
          tags: updatedTagIds
        })
        
        this.currentTags = response.data.tags || []
        this.$emit('tags-updated', this.currentTags)
        this.$emit('success', this.$t('common.tagRemoved', '태그가 제거되었습니다.'))
        
      } catch (error) {
        console.error('태그 제거 실패:', error)
        const errorMessage = error.response?.data?.error || error.message || '태그 제거에 실패했습니다.'
        this.$toast?.error?.(errorMessage)
        this.$emit('error', error)
      }
    },
    
    getLocalizedTagName(tag) {
      // 태그 이름은 다국어로 표시하되, 필터링은 항상 tag.id 사용
      const currentLang = this.$i18n.locale || 'en'
      if (currentLang === 'ko') {
        return tag.name_ko || tag.name_en || tag.name_es || tag.name_zh || tag.name_ja || tag.localized_name || '태그 없음'
      } else if (currentLang === 'zh') {
        return tag.name_zh || tag.name_en || tag.name_ko || tag.name_es || tag.name_ja || tag.localized_name || '无标签'
      } else if (currentLang === 'es') {
        return tag.name_es || tag.name_en || tag.name_ko || tag.name_zh || tag.name_ja || tag.localized_name || 'Sin Etiqueta'
      } else if (currentLang === 'ja') {
        return tag.name_ja || tag.name_en || tag.name_ko || tag.name_es || tag.name_zh || tag.localized_name || 'タグなし'
      } else {
        // 영어 또는 기타
        return tag.name_en || tag.name_ko || tag.name_es || tag.name_zh || tag.name_ja || tag.localized_name || 'No Tag'
      }
    },
    
    handleTagError(error) {
      console.error('태그 에러:', error)
      this.$emit('error', error)
    }
  }
}
</script>

<style scoped>
.entity-tag-manager {
  margin-bottom: 1rem;
}

.info-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.info-label {
  font-weight: 600;
  color: #495057;
  min-width: 80px;
  flex-shrink: 0;
}

.tags-management {
  flex: 1;
}

.tags-display {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  flex-wrap: wrap;
  justify-content: space-between;
}

.tags-display .btn {
  margin-left: auto;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
}

.tag-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  background-color: #e9ecef;
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  color: #495057;
}

.tag-remove-btn {
  background: none;
  border: none;
  color: #6c757d;
  padding: 0;
  margin-left: 0.25rem;
  cursor: pointer;
  font-size: 0.75rem;
  line-height: 1;
}

.tag-remove-btn:hover {
  color: #dc3545;
}

.no-tags {
  color: #6c757d;
  font-style: italic;
  font-size: 0.875rem;
}

.tags-edit {
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
  padding: 1rem;
  margin-top: 0.5rem;
}

.tag-selector {
  margin-bottom: 1rem;
}

.tag-edit-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}

@media (max-width: 768px) {
  .info-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .tags-display {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
  
  .tags-display .tags-list {
    flex: 1;
  }
  
  .tags-display .btn {
    margin-left: auto;
    flex-shrink: 0;
  }
  
  .tag-edit-actions {
    justify-content: flex-end;
  }
  
  .tag-edit-actions .btn {
    flex: 0 0 auto;
    justify-content: center;
  }
  
  /* 태그 관리 버튼 텍스트 숨김 (아이콘만 표시) */
  .btn.btn-outline-primary {
    font-size: 0 !important;
    padding: 8px !important;
    gap: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 40px !important;
    height: 40px !important;
    border-radius: 50% !important;
    min-width: auto !important;
  }
  
  .btn.btn-outline-primary i {
    font-size: 1rem !important;
    line-height: 1 !important;
  }
  
  .btn.btn-outline-primary span {
    display: none !important;
  }
  
  /* tag-edit-actions 버튼을 원형 버튼으로 */
  .tag-edit-actions .btn {
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
    flex: 0 0 auto !important;
  }
  
  .tag-edit-actions .btn i {
    font-size: 14px !important;
    line-height: 1 !important;
    color: white !important;
  }
  
  .tag-edit-actions .btn-secondary i {
    color: #6c757d !important;
  }
  
  .tag-edit-actions .btn-secondary:hover i {
    color: white !important;
  }
  
  .tag-edit-actions .btn span {
    display: none !important;
  }
}

@media (max-width: 576px) {
  .tag-edit-actions .btn {
    width: 36px !important;
    height: 36px !important;
  }
  
  .tag-edit-actions .btn i {
    font-size: 12px !important;
  }
}
</style>
