<template>
  <div class="tag-filter">
    <div class="tag-filter-header">
      <h6 class="tag-filter-title">{{ $t('tagFilter.title') }}</h6>
      <button 
        v-if="internalValue.length > 0" 
        @click="clearAllTags" 
        class="btn btn-sm btn-outline-secondary"
      >
        <i class="fas fa-eraser"></i>
        <span>{{ $t('tagFilter.clearAll') }}</span>
      </button>
    </div>
    
    <div class="tag-filter-content">
      <!-- 태그 검색 및 새 태그 추가 -->
      <div class="tag-search mb-3">
        <div class="input-group">
          <input
            v-model="searchQuery"
            type="text"
            :placeholder="$t('tagFilter.searchPlaceholder')"
            class="form-control form-control-sm"
            @keyup.enter="addNewTag"
          />
          <button 
            @click="addNewTag" 
            class="btn btn-outline-primary btn-sm"
            :disabled="!searchQuery.trim()"
            :title="$t('tagFilter.addNewTag')"
          >
            <i class="fas fa-plus"></i>
          </button>
        </div>
        <small class="text-muted">{{ $t('tagFilter.addNewTagHint') }}</small>
      </div>
      
      <!-- 카테고리 필터 -->
      <div v-if="showCategoryFilter && categories.length > 0" class="category-filter mb-3">
        <select v-model="selectedCategoryId" class="form-select form-select-sm" @change="filterByCategory">
          <option value="">전체 카테고리</option>
          <option v-for="category in categories" :key="category.id" :value="category.id">
            {{ category.full_path || category.localized_name }}
          </option>
        </select>
      </div>
      
      <!-- 태그 목록 (카테고리별 그룹화) -->
      <div v-if="showCategoryGrouping && groupedTags.length > 0" class="tag-list-grouped">
        <div v-for="group in groupedTags" :key="group.categoryId" class="tag-group">
          <div v-if="group.categoryPath" class="tag-group-header">
            <span class="tag-group-name">{{ group.categoryPath }}</span>
            <span class="tag-group-count">({{ group.tags.length }})</span>
          </div>
          <div class="tag-list">
            <div 
              v-for="tag in group.tags" 
              :key="tag.id"
              class="tag-item"
              :class="{ 'selected': internalValue.includes(tag.id) }"
              @click="toggleTag(tag.id)"
            >
              <span class="tag-name">{{ getLocalizedTagName(tag) }}</span>
              <i v-if="internalValue.includes(tag.id)" class="fas fa-check tag-check"></i>
            </div>
          </div>
        </div>
        
        <div v-if="groupedTags.length === 0" class="no-tags">
          {{ $t('tagFilter.noTags') }}
        </div>
      </div>
      
      <!-- 태그 목록 (기본 - 카테고리 그룹화 없음) -->
      <div v-else class="tag-list">
        <div 
          v-for="tag in filteredTags" 
          :key="tag.id"
          class="tag-item"
          :class="{ 'selected': internalValue.includes(tag.id) }"
          @click="toggleTag(tag.id)"
        >
          <span class="tag-name">{{ getLocalizedTagName(tag) }}</span>
          <span v-if="showCategoryPath && tag.category_paths && tag.category_paths.length > 0" class="tag-category-path">
            ({{ tag.category_paths.join(', ') }})
          </span>
          <i v-if="internalValue.includes(tag.id)" class="fas fa-check tag-check"></i>
        </div>
        
        <div v-if="filteredTags.length === 0" class="no-tags">
          {{ $t('tagFilter.noTags') }}
        </div>
      </div>
    </div>
    
    <!-- 선택된 태그 표시 -->
    <div v-if="internalValue.length > 0" class="selected-tags">
      <div class="selected-tags-label">{{ $t('tagFilter.selectedTags') }}:</div>
      <div class="selected-tags-list">
        <span 
          v-for="tagId in internalValue" 
          :key="tagId"
          class="selected-tag"
        >
          {{ getSelectedTagName(tagId) }}
          <button @click="removeTag(tagId)" class="remove-tag-btn">
            <i class="fas fa-times"></i>
          </button>
        </span>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'TagFilter',
  props: {
    value: {
      type: Array,
      default: () => []
    },
    apiEndpoint: {
      type: String,
      required: true
    },
    showCategoryGrouping: {
      type: Boolean,
      default: false
    },
    showCategoryFilter: {
      type: Boolean,
      default: false
    },
    showCategoryPath: {
      type: Boolean,
      default: true
    }
  },
  data() {
    return {
      tags: [],
      categories: [],
      searchQuery: '',
      internalValue: [],
      selectedCategoryId: ''
    }
  },
  computed: {
    filteredTags() {
      let tags = this.tags
      
      // 카테고리 필터링
      if (this.selectedCategoryId) {
        tags = tags.filter(tag => {
          return tag.categories && tag.categories.some(cat => cat.id === parseInt(this.selectedCategoryId))
        })
      }
      
      // 검색어 필터링
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase()
        tags = tags.filter(tag => {
          const koName = (tag.name_ko || '').toLowerCase()
          const enName = (tag.name_en || '').toLowerCase()
          const categoryPaths = (tag.category_paths || []).join(' ').toLowerCase()
          return koName.includes(query) || enName.includes(query) || categoryPaths.includes(query)
        })
      }
      
      return tags
    },
    groupedTags() {
      if (!this.showCategoryGrouping) {
        return []
      }
      
      const groups = {}
      
      this.filteredTags.forEach(tag => {
        if (tag.categories && tag.categories.length > 0) {
          tag.categories.forEach(category => {
            const categoryId = category.id
            const categoryPath = category.full_path || category.name
            
            if (!groups[categoryId]) {
              groups[categoryId] = {
                categoryId,
                categoryPath,
                tags: []
              }
            }
            groups[categoryId].tags.push(tag)
          })
        } else {
          // 카테고리가 없는 태그는 "미분류" 그룹에 추가
          if (!groups['uncategorized']) {
            groups['uncategorized'] = {
              categoryId: 'uncategorized',
              categoryPath: '미분류',
              tags: []
            }
          }
          groups['uncategorized'].tags.push(tag)
        }
      })
      
      // 카테고리 경로로 정렬
      return Object.values(groups).sort((a, b) => {
        return a.categoryPath.localeCompare(b.categoryPath)
      })
    }
  },
  async mounted() {
    // 초기값 설정
    this.internalValue = [...this.value]
    await Promise.all([
      this.loadTags(),
      this.loadCategories()
    ])
  },
  methods: {
    async loadTags() {
      try {
        const response = await axios.get(this.apiEndpoint)
        this.tags = response.data || []
      } catch (error) {
        console.error('태그 로드 실패:', error)
        this.$emit('error', error)
      }
    },
    async loadCategories() {
      if (!this.showCategoryFilter && !this.showCategoryGrouping) {
        return
      }
      
      try {
        const response = await axios.get('/api/tag-categories/tree/')
        // 트리 구조를 평면화하여 모든 카테고리 가져오기
        const flattenCategories = (categories) => {
          let result = []
          categories.forEach(cat => {
            result.push(cat)
            if (cat.children && cat.children.length > 0) {
              result = result.concat(flattenCategories(cat.children))
            }
          })
          return result
        }
        this.categories = flattenCategories(response.data || [])
      } catch (error) {
        console.error('카테고리 로드 실패:', error)
      }
    },
    filterByCategory() {
      // 카테고리 필터링은 computed에서 처리됨
    },
    toggleTag(tagId) {
      if (this.internalValue.includes(tagId)) {
        this.removeTag(tagId)
      } else {
        this.addTag(tagId)
      }
    },
    addTag(tagId) {
      if (!this.internalValue.includes(tagId)) {
        this.internalValue = [...this.internalValue, tagId]
        this.$emit('input', this.internalValue)
      }
    },
    removeTag(tagId) {
      this.internalValue = this.internalValue.filter(id => id !== tagId)
      this.$emit('input', this.internalValue)
    },
    clearAllTags() {
      this.internalValue = []
      this.$emit('input', this.internalValue)
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
    getSelectedTagName(tagId) {
      const tag = this.tags.find(t => t.id === tagId)
      if (!tag) return 'Unknown'
      return this.getLocalizedTagName(tag)
    },
    
    async addNewTag() {
      const tagName = this.searchQuery.trim()
      
      if (!tagName) {
        return
      }
      
      try {
        const response = await axios.post('/api/tags/', {
          name_ko: tagName,
          name_en: tagName
        })
        
        this.tags.push(response.data)
        this.addTag(response.data.id)
        this.searchQuery = ''
        this.$emit('tag-created', response.data)
        
      } catch (error) {
        console.error('태그 생성 실패:', error)
        this.$emit('error', error)
      }
    }
  }
}
</script>

<style scoped>
.tag-filter {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
}

.tag-filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.tag-filter-title {
  margin: 0;
  font-weight: 600;
  color: #495057;
}

.tag-search .input-group {
  margin-bottom: 5px;
}

.tag-search input {
  border-radius: 6px 0 0 6px;
  border: 1px solid #ced4da;
}

.tag-search .btn {
  border-radius: 0 6px 6px 0;
  border-left: none;
}

.tag-search .btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.tag-list {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  background: white;
}

.tag-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  border-bottom: 1px solid #f1f3f4;
  transition: background-color 0.2s;
}

.tag-item:last-child {
  border-bottom: none;
}

.tag-item:hover {
  background-color: #f8f9fa;
}

.tag-item.selected {
  background-color: #e3f2fd;
  color: #1976d2;
}

.tag-name {
  font-size: 14px;
}

.tag-check {
  color: #1976d2;
  font-size: 12px;
}

.no-tags {
  padding: 16px;
  text-align: center;
  color: #6c757d;
  font-style: italic;
}

.selected-tags {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #dee2e6;
}

.selected-tags-label {
  font-size: 12px;
  color: #6c757d;
  margin-bottom: 8px;
}

.selected-tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.selected-tag {
  display: inline-flex;
  align-items: center;
  background-color: #1976d2;
  color: white;
  padding: 4px 8px;
  border-radius: 16px;
  font-size: 12px;
  gap: 4px;
}

.remove-tag-btn {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  padding: 0;
  margin-left: 4px;
  font-size: 10px;
}

.remove-tag-btn:hover {
  color: #ffcdd2;
}

.category-filter {
  margin-bottom: 12px;
}

.tag-list-grouped {
  max-height: 400px;
  overflow-y: auto;
}

.tag-group {
  margin-bottom: 16px;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  background: white;
}

.tag-group-header {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background-color: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
  font-weight: 600;
  font-size: 13px;
  color: #495057;
}

.tag-group-name {
  flex: 1;
}

.tag-group-count {
  color: #6c757d;
  font-size: 12px;
  margin-left: 8px;
}

.tag-category-path {
  font-size: 11px;
  color: #6c757d;
  margin-left: 8px;
  font-style: italic;
}

@media (max-width: 768px) {
  .tag-filter-header .btn {
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
  
  .tag-filter-header .btn i {
    font-size: 14px !important;
    line-height: 1 !important;
  }
  
  .tag-filter-header .btn span {
    display: none !important;
  }
}

@media (max-width: 576px) {
  .tag-filter-header .btn {
    width: 36px !important;
    height: 36px !important;
  }
  
  .tag-filter-header .btn i {
    font-size: 12px !important;
  }
}
</style>
