<template>
  <div>
    <div v-if="show" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <!-- Modal Header -->
        <div class="modal-header">
          <h5 class="modal-title">{{ $t('categoryFilterModal.title') || '카테고리 선택' }}</h5>
          <button type="button" class="btn-close" @click="closeModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <!-- Modal Body -->
        <div class="modal-body">
          <!-- Search Input -->
          <div class="search-section mb-4">
            <div class="input-group">
              <span class="input-group-text">
                <i class="fas fa-search"></i>
              </span>
              <input
                v-model="searchQuery"
                type="text"
                class="form-control"
                :placeholder="$t('categoryFilterModal.searchPlaceholder') || '카테고리 검색...'"
                @input="filterCategories"
              />
            </div>
          </div>
          
          <!-- Category List -->
          <div class="category-list-section">
            <div v-if="loading" class="loading-container text-center py-4">
              <i class="fas fa-spinner fa-spin"></i>
              <span class="ms-2">{{ $t('common.loading') || '로딩 중...' }}</span>
            </div>
            
            <div v-else-if="filteredCategories.length > 0" class="categories-list">
              <div
                v-for="category in filteredCategories"
                :key="category.id"
                class="category-item"
                :class="{ 'selected': selectedCategoryIds.includes(category.id) }"
                @click.stop="toggleCategory(category.id)"
              >
                <input
                  type="checkbox"
                  :checked="selectedCategoryIds.includes(category.id)"
                  class="category-checkbox"
                  @click.stop="toggleCategory(category.id)"
                />
                <span class="category-name">{{ getCategoryDisplayName(category) }}</span>
              </div>
            </div>
            
            <div v-else class="no-results text-center py-4">
              <i class="fas fa-search"></i>
              <p class="mt-2">{{ $t('categoryFilterModal.noResults') || '검색 결과가 없습니다.' }}</p>
            </div>
          </div>
        </div>
        
        <!-- Modal Footer -->
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="clearAll">
            <i class="fas fa-eraser"></i>
            <span>{{ $t('categoryFilterModal.clearAll') || '모두 지우기' }}</span>
          </button>
          <div class="footer-actions">
            <button type="button" class="btn btn-outline-secondary" @click="closeModal">
              <i class="fas fa-times"></i>
              <span>{{ $t('categoryFilterModal.cancel') || '취소' }}</span>
            </button>
            <button type="button" class="btn btn-primary" @click="applyFilters">
              <i class="fas fa-check"></i>
              <span>{{ $t('categoryFilterModal.apply') || '적용' }} ({{ selectedCategoryIds.length }})</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'CategoryFilterModal',
  props: {
    show: {
      type: Boolean,
      default: false
    },
    selectedCategories: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      allCategories: [],
      categoryTree: [],
      searchQuery: '',
      selectedCategoryIds: [...this.selectedCategories],
      loading: false
    }
  },
  computed: {
    filteredCategories() {
      let categories = this.allCategories
      
      // 검색어 필터링
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase()
        const supportedLanguages = ['ko', 'en', 'es', 'zh', 'ja']
        const currentLang = this.$i18n?.locale || 'en'  // 기본 언어는 'en'
        
        categories = categories.filter(category => {
          // 모든 지원 언어의 이름 확인
          for (const lang of supportedLanguages) {
            const nameField = `name_${lang}`
            if (category[nameField] && category[nameField].toLowerCase().includes(query)) {
              return true
            }
          }
          
          // 전체 경로 확인
          const fullPath = this.buildCategoryPath(category, currentLang).toLowerCase()
          return fullPath.includes(query)
        })
      }
      
      // 활성화된 카테고리만 표시
      return categories.filter(cat => cat.is_active !== false)
    }
  },
  watch: {
    selectedCategories: {
      handler(newValue) {
        this.selectedCategoryIds = [...newValue]
      },
      immediate: true
    },
    show: {
      handler(newValue) {
        if (newValue) {
          this.loadCategories()
        }
      }
    }
  },
  async mounted() {
    await this.loadCategories()
  },
  methods: {
    async loadCategories() {
      try {
        this.loading = true
        
        // DevOps 도메인 필터링 확인
        const { getCurrentDomainConfig, getDevOpsCategoryId } = await import('@/utils/domainUtils')
        const domainConfig = getCurrentDomainConfig()
        const isDevOps = domainConfig && domainConfig.keyword === 'devops'
        
        // 트리 구조를 평면화하여 리스트로 저장
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
        
        // 카테고리 트리 API 호출
        let response
        try {
          response = await axios.get('/api/tag-categories/tree/', {
            params: {
              is_active: true
            }
          })
        } catch (treeError) {
          // tree API가 실패하면 일반 API 사용
          console.log('⚠️ 카테고리 트리 API 실패, 일반 API 사용:', treeError)
          try {
            response = await axios.get('/api/tag-categories/', {
              params: {
                is_active: true
              }
            })
          } catch (listError) {
            console.error('❌ 카테고리 로드 실패:', listError)
            throw listError
          }
        }
        
        // 카테고리 트리 저장
        let categories = response?.data || []
        
        // DevOps 도메인인 경우 필터링 적용
        if (isDevOps && Array.isArray(categories) && categories.length > 0) {
          // "IT 기술 > IT 기술" 카테고리만 표시
          const categoryId = getDevOpsCategoryId(categories)
          if (categoryId) {
            // 해당 카테고리만 포함하도록 필터링
            const findCategory = (cats, targetId) => {
              for (const cat of cats) {
                if (cat.id === targetId) {
                  return cat
                }
                if (cat.children && Array.isArray(cat.children)) {
                  const found = findCategory(cat.children, targetId)
                  if (found) {
                    return found
                  }
                }
              }
              return null
            }
            
            const devopsCategory = findCategory(categories, categoryId)
            if (devopsCategory) {
              // 해당 카테고리를 루트로 하는 트리로 변환
              categories = [devopsCategory]
              console.log('✅ DevOps 도메인 카테고리 필터링 적용:', devopsCategory.name_ko)
            }
          }
        }
        
        if (Array.isArray(categories) && categories.length > 0 && categories[0].children) {
          // 트리 구조인 경우 평면화 및 트리 구조 유지
          this.allCategories = flattenCategories(categories)
          this.categoryTree = categories.filter(cat => cat && cat.is_active !== false)
        } else {
          // 평면 구조인 경우 그대로 사용
          this.allCategories = (categories || []).filter(cat => cat && cat.is_active !== false)
          this.categoryTree = []
        }
        
        console.log('✅ 카테고리 로드 완료:', this.allCategories.length, '개')
      } catch (error) {
        console.error('❌ 카테고리 로드 실패:', error)
        console.error('❌ 에러 상세:', error.response?.data || error.message)
        this.allCategories = []
        this.categoryTree = []
        this.$emit('error', error)
      } finally {
        this.loading = false
      }
    },
    
    toggleCategory(categoryId) {
      const index = this.selectedCategoryIds.indexOf(categoryId)
      if (index > -1) {
        this.selectedCategoryIds.splice(index, 1)
      } else {
        this.selectedCategoryIds.push(categoryId)
      }
    },
    
    clearAll() {
      this.selectedCategoryIds = []
    },
    
    applyFilters() {
      this.$emit('update:selectedCategories', [...this.selectedCategoryIds])
      this.$emit('apply', [...this.selectedCategoryIds])
      this.closeModal()
    },
    
    closeModal() {
      this.$emit('update:show', false)
      this.searchQuery = ''
    },
    
    filterCategories() {
      // 검색어가 변경될 때마다 필터링 (computed property가 자동으로 처리)
    },
    
    getCategoryDisplayName(category) {
      // 카테고리 경로로 표시
      const locale = this.$i18n.locale || 'en'
      return this.buildCategoryPath(category, locale)
    },
    
    buildCategoryPath(category, locale) {
      // 카테고리 트리에서 부모 경로 찾기
      if (!this.categoryTree || this.categoryTree.length === 0) {
        // 트리가 없으면 이름만 반환
        if (locale === 'ko') {
          return category.name_ko || category.name_en || category.name_zh || category.name_ja || ''
        } else if (locale === 'zh') {
          return category.name_zh || category.name_ko || category.name_en || category.name_ja || ''
        } else if (locale === 'ja') {
          return category.name_ja || category.name_en || category.name_ko || category.name_zh || ''
        } else {
          return category.name_en || category.name_ko || category.name_zh || category.name_ja || ''
        }
      }
      
      const findPathInTree = (catId, tree, currentPath = []) => {
        for (const cat of tree) {
          const currentPathCopy = [...currentPath]
          let name = ''
          if (locale === 'ko') {
            name = cat.name_ko || cat.name_en || cat.name_zh || cat.name_ja || ''
          } else if (locale === 'zh') {
            name = cat.name_zh || cat.name_ko || cat.name_en || cat.name_ja || ''
          } else if (locale === 'ja') {
            name = cat.name_ja || cat.name_en || cat.name_ko || cat.name_zh || ''
          } else {
            name = cat.name_en || cat.name_ko || cat.name_zh || cat.name_ja || ''
          }
          
          if (name) {
            currentPathCopy.push(name)
          }
          
          if (cat.id === catId) {
            return currentPathCopy
          }
          
          if (cat.children && cat.children.length > 0) {
            const childPath = findPathInTree(catId, cat.children, currentPathCopy)
            if (childPath) {
              return childPath
            }
          }
        }
        return null
      }
      
      const pathParts = findPathInTree(category.id, this.categoryTree)
      if (pathParts && pathParts.length > 0) {
        return pathParts.join(' > ')
      }
      
      // 경로를 찾지 못한 경우 현재 언어에 맞는 이름만 반환
      if (locale === 'ko') {
        return category.name_ko || category.name_en || category.name_zh || category.name_ja || ''
      } else if (locale === 'zh') {
        return category.name_zh || category.name_ko || category.name_en || category.name_ja || ''
      } else if (locale === 'ja') {
        return category.name_ja || category.name_en || category.name_ko || category.name_zh || ''
      } else {
        return category.name_en || category.name_ko || category.name_zh || category.name_ja || ''
      }
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000; /* 모달 오버레이 */
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.modal-header {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #dee2e6;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: #6c757d;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-close:hover {
  color: #212529;
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid #dee2e6;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.footer-actions {
  display: flex;
  gap: 0.5rem;
}

.search-section {
  margin-bottom: 1rem;
}

.input-group-text {
  background-color: #f8f9fa;
  border-right: none;
}

.categories-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 400px;
  overflow-y: auto;
}

.category-item {
  display: flex;
  align-items: center;
  padding: 0.75rem;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.category-item:hover {
  background-color: #f8f9fa;
  border-color: #0d6efd;
}

.category-item.selected {
  background-color: #e7f1ff;
  border-color: #0d6efd;
}

.category-checkbox {
  margin-right: 0.75rem;
  cursor: pointer;
}

.category-name {
  flex: 1;
  font-size: 0.95rem;
}

.loading-container,
.no-results {
  padding: 2rem;
  color: #6c757d;
}

.no-results i {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.btn {
  padding: 0.5rem 1rem;
  border-radius: 4px;
  border: 1px solid transparent;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.95rem;
  transition: all 0.2s;
}

.btn-primary {
  background-color: #0d6efd;
  color: white;
  border-color: #0d6efd;
}

.btn-primary:hover {
  background-color: #0b5ed7;
  border-color: #0a58ca;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
  border-color: #6c757d;
}

.btn-secondary:hover {
  background-color: #5c636a;
  border-color: #565e64;
}

.btn-outline-secondary {
  background-color: transparent;
  color: #6c757d;
  border-color: #6c757d;
}

.btn-outline-secondary:hover {
  background-color: #6c757d;
  color: white;
}

/* Responsive - 모바일 스타일 */
@media (max-width: 768px) {
  .modal-content {
    width: 95%;
    max-height: 90vh;
  }
}
</style>

