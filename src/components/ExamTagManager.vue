<template>
  <div class="exam-tag-manager">
    <div class="info-item">
      <span class="info-label">{{ $t('examDetail.tags', '태그') }}:</span>
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
                :title="$t('examDetail.removeTag', '태그 제거')"
                v-if="canEdit"
              >
                <i class="fas fa-times"></i>
              </button>
            </span>
            <span v-if="currentTags.length === 0" class="no-tags">
              {{ $t('examDetail.noTags', '태그 없음') }}
            </span>
          </div>
          <button 
            @click="toggleTagEditMode" 
            class="btn btn-sm btn-outline-primary"
            v-if="canEdit"
          >
            <i class="fas fa-edit"></i>
            {{ $t('examDetail.manageTags', '태그 관리') }}
          </button>
        </div>
        
        <div class="tags-edit" v-if="isEditingTags">
          <div class="tag-selector">
            <TagFilter
              :value="editingTagIds"
              :apiEndpoint="'/api/studies/tags/'"
              @input="handleTagSelectionChange"
              @error="handleTagError"
              @tag-created="handleTagCreated"
            />
          </div>
          <div class="tag-edit-actions">
            <button 
              @click="saveTags" 
              class="btn btn-sm btn-success"
              :disabled="savingTags"
            >
              <i class="fas fa-save"></i>
              {{ $t('examDetail.save', '저장') }}
            </button>
            <button 
              @click="cancelTagEdit" 
              class="btn btn-sm btn-secondary"
            >
              <i class="fas fa-times"></i>
              {{ $t('examDetail.cancel', '취소') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import TagFilter from '@/components/TagFilter.vue'
import axios from 'axios'

export default {
  name: 'ExamTagManager',
  components: {
    TagFilter
  },
  props: {
    examId: {
      type: String,
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
      currentTags: [...this.tags],
      isEditingTags: false,
      editingTagIds: [],
      savingTags: false
    }
  },
  watch: {
    tags: {
      handler(newTags) {
        this.currentTags = [...newTags]
      },
      immediate: true
    }
  },
  methods: {
    toggleTagEditMode() {
      this.isEditingTags = !this.isEditingTags
      if (this.isEditingTags) {
        this.editingTagIds = this.currentTags.map(tag => tag.id)
      }
    },
    
    handleTagSelectionChange(newTagIds) {
      this.editingTagIds = [...newTagIds]
    },
    
    async saveTags() {
      try {
        this.savingTags = true
        
        // 시험의 태그 업데이트 API 호출
        const response = await axios.patch(`/api/exams/${this.examId}/`, {
          tags: this.editingTagIds
        })
        
        // 성공 시 현재 태그 업데이트
        this.currentTags = response.data.tags || []
        this.isEditingTags = false
        
        this.$emit('tags-updated', this.currentTags)
        this.$emit('success', this.$t('examDetail.tagsUpdated', '태그가 업데이트되었습니다.'))
        
      } catch (error) {
        console.error('태그 저장 실패:', error)
        this.$emit('error', error)
      } finally {
        this.savingTags = false
      }
    },
    
    async removeTag(tagId) {
      try {
        const updatedTagIds = this.currentTags
          .filter(tag => tag.id !== tagId)
          .map(tag => tag.id)
        
        const response = await axios.patch(`/api/exams/${this.examId}/`, {
          tags: updatedTagIds
        })
        
        this.currentTags = response.data.tags || []
        this.$emit('tags-updated', this.currentTags)
        this.$emit('success', this.$t('examDetail.tagRemoved', '태그가 제거되었습니다.'))
        
      } catch (error) {
        console.error('태그 제거 실패:', error)
        this.$emit('error', error)
      }
    },
    
    cancelTagEdit() {
      this.isEditingTags = false
      this.editingTagIds = []
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
    },
    
    handleTagCreated(tag) {
      // 새로 생성된 태그를 현재 편집 중인 태그 목록에 추가
      this.editingTagIds.push(tag.id)
    }
  }
}
</script>

<style scoped>
.exam-tag-manager {
  margin-bottom: 1rem;
}

.info-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
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
    flex-direction: column;
    align-items: flex-start;
  }
  
  .tag-edit-actions {
    justify-content: stretch;
  }
  
  .tag-edit-actions .btn {
    flex: 1;
    justify-content: center;
  }
  
  /* 태그 관리 버튼 텍스트 숨김 (아이콘만 표시) */
  .btn.btn-outline-primary {
    font-size: 0;
    padding: 8px;
    gap: 0;
  }
  
  .btn.btn-outline-primary i {
    font-size: 1rem;
  }
}
</style>
