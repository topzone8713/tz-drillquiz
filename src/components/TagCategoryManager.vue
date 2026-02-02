<template>
  <div class="tag-category-manager">
    <!-- Toast Notification -->
    <div v-if="showToast" class="toast-notification" :class="toastType">
      <div class="toast-content">
        <i :class="toastIcon"></i>
        <span>{{ toastMessage }}</span>
      </div>
      <button class="toast-close" @click="hideToast">
        <i class="fas fa-times"></i>
      </button>
    </div>
    
    <div class="manager-header">
      <h5>{{ $t('categoryManager.title') }}</h5>
      <div class="header-actions">
        <button @click="showInactive = !showInactive" class="btn btn-sm btn-outline-secondary">
          <i class="fas" :class="showInactive ? 'fa-eye-slash' : 'fa-eye'"></i>
          {{ showInactive ? $t('categoryManager.hideInactive') : $t('categoryManager.showInactive') }}
        </button>
        <button @click="showCreateModal = true" class="btn btn-primary btn-sm">
          <i class="fas fa-plus"></i> {{ $t('categoryManager.addNew') }}
        </button>
      </div>
    </div>
    
    <div v-if="loading" class="text-center p-4">
      <div class="spinner-border" role="status">
        <span class="visually-hidden">{{ $t('common.loading') }}</span>
      </div>
    </div>
    
    <div v-else class="category-tree-container">
      <draggable
        v-model="categoryTree"
        :animation="200"
        group="categories"
        :disabled="false"
        ghost-class="ghost"
        @end="onDragEnd"
        handle=".drag-handle"
        class="category-tree"
      >
        <template v-for="category in filteredTree">
          <CategoryNode
            v-if="category && category.id"
            :key="category.id"
            :category="category"
            :level="0"
            :show-inactive="showInactive"
            :data-category-id="category.id"
            @edit="handleEdit"
            @delete="handleDelete"
            @add-child="handleAddChild"
            @toggle-active="handleToggleActive"
            @move="handleMove"
            @update-children="handleUpdateChildren"
          />
        </template>
      </draggable>
    </div>
    
    <!-- 삭제 확인 모달 -->
    <div v-if="showDeleteConfirm" class="modal-overlay" @click="cancelDelete">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h5 class="modal-title">
            <i class="fas fa-exclamation-triangle text-danger me-2"></i>
            {{ $t('categoryManager.deleteConfirmTitle') }}
          </h5>
          <button type="button" class="btn-close" @click="cancelDelete">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <p class="mb-0">{{ deleteConfirmMessage }}</p>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="cancelDelete">
            <i class="fas fa-times"></i>
            <span>{{ $t('common.cancel') }}</span>
          </button>
          <button type="button" class="btn btn-danger" @click="confirmDelete">
            <i class="fas fa-trash"></i>
            <span>{{ $t('common.delete') }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 카테고리 생성/편집 모달 -->
    <div v-if="showCreateModal || editingCategory" class="modal show d-block" tabindex="-1" style="background-color: rgba(0,0,0,0.5);">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              {{ editingCategory ? $t('categoryManager.editCategory') : $t('categoryManager.addNew') }}
            </h5>
            <button type="button" class="btn-close" @click="closeModal"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="saveCategory">
              <div class="mb-3">
                <label class="form-label">{{ $t('categoryManager.nameEn') }}</label>
                <input
                  v-model="categoryForm.name_en"
                  type="text"
                  class="form-control"
                />
              </div>
              <div class="mb-3">
                <label class="form-label">{{ $t('categoryManager.nameKo') }}</label>
                <input
                  v-model="categoryForm.name_ko"
                  type="text"
                  class="form-control"
                  required
                />
              </div>
              <div class="mb-3">
                <label class="form-label">{{ $t('categoryManager.nameEs') || 'Spanish Name' }}</label>
                <input
                  v-model="categoryForm.name_es"
                  type="text"
                  class="form-control"
                />
              </div>
              <div class="mb-3">
                <label class="form-label">{{ $t('categoryManager.nameZh') || 'Chinese Name' }}</label>
                <input
                  v-model="categoryForm.name_zh"
                  type="text"
                  class="form-control"
                />
              </div>
              <div class="mb-3">
                <label class="form-label">{{ $t('categoryManager.nameJa') || 'Japanese Name' }}</label>
                <input
                  v-model="categoryForm.name_ja"
                  type="text"
                  class="form-control"
                />
              </div>
              <div class="mb-3">
                <label class="form-label">{{ $t('categoryManager.parentCategory') }}</label>
                <select v-model="categoryForm.parent" class="form-select">
                  <option :value="null">{{ $t('categoryManager.noParent') }}</option>
                  <template v-for="cat in allCategories">
                    <option
                      v-if="cat && cat.id"
                      :key="cat.id"
                      :value="cat.id"
                      :disabled="editingCategory && cat.id === editingCategory.id"
                    >
                      {{ getCategoryPath(cat) }}
                    </option>
                  </template>
                </select>
              </div>
              <div class="mb-3">
                <label class="form-label">{{ $t('categoryManager.order') }}</label>
                <input
                  v-model.number="categoryForm.order"
                  type="number"
                  class="form-control"
                  min="0"
                />
              </div>
              <div class="mb-3">
                <label class="form-label">{{ $t('categoryManager.colorCode') }}</label>
                <input
                  v-model="categoryForm.color"
                  type="text"
                  class="form-control"
                  :placeholder="$t('categoryManager.colorPlaceholder')"
                />
              </div>
              <div class="mb-3" v-if="editingCategory">
                <div class="form-check">
                  <input
                    v-model="categoryForm.is_active"
                    type="checkbox"
                    class="form-check-input"
                    id="isActive"
                  />
                  <label class="form-check-label" for="isActive">
                    {{ $t('categoryManager.isActive') }}
                  </label>
                </div>
              </div>
              <div class="modal-footer">
                <button type="button" class="btn btn-secondary" @click="closeModal">{{ $t('common.cancel') }}</button>
                <button type="submit" class="btn btn-primary">{{ $t('common.save') }}</button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import draggable from 'vuedraggable'
import CategoryNode from './CategoryNode.vue'

export default {
  name: 'TagCategoryManager',
  components: {
    CategoryNode,
    draggable
  },
  data() {
    return {
      loading: false,
      categoryTree: [],
      allCategories: [],
      showCreateModal: false,
      editingCategory: null,
      showInactive: false,
      showDeleteConfirm: false,
      deletingCategory: null,
      deleteConfirmMessage: '',
      showToast: false,
      toastMessage: '',
      toastType: 'alert-error',
      toastIcon: 'fas fa-exclamation-circle',
      categoryForm: {
        name_ko: '',
        name_en: '',
        name_es: '',
        name_zh: '',
        name_ja: '',
        parent: null,
        order: 0,
        color: '',
        is_active: true
      }
    }
  },
  computed: {
    filteredTree() {
      if (!this.categoryTree || !Array.isArray(this.categoryTree)) {
        return []
      }
      if (this.showInactive) {
        return this.categoryTree.filter(c => c && c.id)
      }
      return this.categoryTree.filter(c => c && c.id && c.is_active !== false)
    }
  },
  watch: {
    '$i18n.locale': {
      async handler(newLocale) {
        // 언어가 변경되면 번역을 다시 로드
        if (newLocale) {
          try {
            await this.$loadTranslations(newLocale)
            this.$forceUpdate()
          } catch (error) {
            console.error('언어 변경 시 번역 로드 실패:', error)
          }
        }
      },
      immediate: false
    }
  },
  async mounted() {
    // 번역 데이터가 로드되었는지 확인하고, 필요하면 다시 로드
    let retryCount = 0
    const maxRetries = 5
    
    while (!this.$isTranslationsLoaded(this.$i18n.locale) && retryCount < maxRetries) {
      try {
        await this.$loadTranslations(this.$i18n.locale)
      } catch (error) {
        console.error('번역 로드 실패:', error)
      }
      
      retryCount++
      
      // 잠시 대기
      if (retryCount < maxRetries) {
        await new Promise(resolve => setTimeout(resolve, 1000))
      }
    }
    
    // 번역이 여전히 로드되지 않았다면 강제로 다시 시도
    if (!this.$isTranslationsLoaded(this.$i18n.locale)) {
      console.log('강제로 번역 데이터를 다시 로드합니다...')
      try {
        await this.$loadTranslations(this.$i18n.locale)
        console.log('강제 번역 로드 완료')
      } catch (error) {
        console.error('강제 번역 로드 실패:', error)
      }
    }
    
    // Vue 강제 업데이트
    this.$forceUpdate()
    
    await this.loadCategories()
  },
  methods: {
    async loadCategories() {
      this.loading = true
      try {
        const [treeResponse, listResponse] = await Promise.all([
          axios.get('/api/tag-categories/tree/'),
          axios.get('/api/tag-categories/')
        ])
        // null이나 undefined 항목 필터링
        const filterValidCategories = (categories) => {
          if (!Array.isArray(categories)) return []
          return categories.filter(c => c && c.id).map(cat => {
            if (cat.children && Array.isArray(cat.children)) {
              cat.children = filterValidCategories(cat.children)
            }
            return cat
          })
        }
        this.categoryTree = filterValidCategories(treeResponse.data || [])
        this.allCategories = filterValidCategories(listResponse.data || [])
      } catch (error) {
        console.error('카테고리 로드 실패:', error)
        this.$emit('error', error)
      } finally {
        this.loading = false
      }
    },
    async onDragEnd(evt) {
      console.log('[TagCategoryManager] onDragEnd 이벤트 발생:', {
        oldIndex: evt.oldIndex,
        newIndex: evt.newIndex,
        item: evt.item,
        to: evt.to,
        from: evt.from,
        toElement: evt.to?.element,
        fromElement: evt.from?.element,
        relatedContext: evt.relatedContext
      })
      
      // 같은 그룹 내에서 다른 위치로 이동한 경우
      if (evt.oldIndex !== evt.newIndex && evt.from === evt.to) {
        const movedCategory = this.categoryTree[evt.newIndex]
        const newOrder = evt.newIndex
        
        console.log('[TagCategoryManager] 같은 레벨 내 이동:', {
          category: movedCategory,
          newOrder,
          categoryTree: this.categoryTree.map(c => ({ id: c.id, name: c.name_ko }))
        })
        
        await this.handleMove({
          category: movedCategory,
          newParent: null,
          newOrder
        })
        return
      }
      
      // 다른 그룹으로 이동한 경우 (자식으로 이동)
      if (evt.from !== evt.to && evt.to) {
        console.log('[TagCategoryManager] 다른 그룹으로 이동 감지:', {
          from: evt.from?.element,
          to: evt.to?.element,
          newIndex: evt.newIndex
        })
        
        // to 요소에서 부모 카테고리를 찾기
        const toElement = evt.to?.element
        if (toElement) {
          // 가장 가까운 category-node 찾기
          const parentNode = toElement.closest('.category-node')
          if (parentNode) {
            const categoryId = parentNode.getAttribute('data-category-id') || 
                              parentNode.querySelector('[data-category-id]')?.getAttribute('data-category-id')
            console.log('[TagCategoryManager] 부모 카테고리 찾음:', categoryId)
            
            // 이동된 카테고리 찾기
            const movedItem = evt.item
            const movedCategoryId = movedItem.getAttribute('data-category-id') || 
                                   movedItem.querySelector('[data-category-id]')?.getAttribute('data-category-id')
            
            if (movedCategoryId && categoryId) {
              const movedCategory = this.allCategories.find(c => c.id === parseInt(movedCategoryId))
              const parentCategory = this.allCategories.find(c => c.id === parseInt(categoryId))
              
              if (movedCategory && parentCategory) {
                console.log('[TagCategoryManager] 자식으로 이동:', {
                  movedCategory: { id: movedCategory.id, name: movedCategory.name_ko },
                  parentCategory: { id: parentCategory.id, name: parentCategory.name_ko },
                  newOrder: evt.newIndex
                })
                
                await this.handleMove({
                  category: movedCategory,
                  newParent: parentCategory,
                  newOrder: evt.newIndex
                })
                return
              }
            }
          }
        }
      }
      
      if (evt.oldIndex === evt.newIndex) {
        console.log('[TagCategoryManager] 인덱스 변경 없음, 이동 취소')
        return
      }
    },
    handleUpdateChildren({ category, children }) {
      console.log('[TagCategoryManager] handleUpdateChildren 호출:', {
        category: category ? { id: category.id, name: category.name_ko } : null,
        childrenCount: children ? children.length : 0,
        children: children ? children.map(c => ({ id: c.id, name: c.name_ko })) : []
      })
      
      if (!category || !category.id) {
        console.error('[TagCategoryManager] Invalid category for update children:', category)
        return
      }
      // 로컬 상태 업데이트
      const findAndUpdate = (categories) => {
        for (let cat of categories) {
          if (cat && cat.id === category.id) {
            console.log('[TagCategoryManager] 카테고리 children 업데이트:', {
              categoryId: cat.id,
              categoryName: cat.name_ko,
              oldChildrenCount: cat.children ? cat.children.length : 0,
              newChildrenCount: children ? children.length : 0
            })
            cat.children = children
            return true
          }
          if (cat && cat.children && cat.children.length > 0) {
            if (findAndUpdate(cat.children)) {
              return true
            }
          }
        }
        return false
      }
      findAndUpdate(this.categoryTree)
    },
    async handleMove({ category, newParent = null, newOrder = 0, evt }) {
      console.log('[TagCategoryManager] handleMove 호출:', {
        category: category ? { id: category.id, name: category.name_ko } : null,
        newParent: newParent ? { id: newParent.id, name: newParent.name_ko } : null,
        newOrder,
        evt: evt ? { oldIndex: evt.oldIndex, newIndex: evt.newIndex } : null
      })
      
      if (!category || !category.id) {
        console.error('[TagCategoryManager] Invalid category for move:', category)
        return
      }
      
      try {
        const requestData = {
          parent_id: newParent?.id || null,
          order: newOrder
        }
        console.log('[TagCategoryManager] API 요청 전송:', {
          url: `/api/tag-categories/${category.id}/move/`,
          data: requestData
        })
        
        const response = await axios.post(`/api/tag-categories/${category.id}/move/`, requestData)
        
        console.log('[TagCategoryManager] API 응답 성공:', response.data)
        
        await this.loadCategories()
        
        console.log('[TagCategoryManager] 카테고리 재로드 완료')
      } catch (error) {
        console.error('[TagCategoryManager] 카테고리 이동 실패:', {
          error: error.message,
          response: error.response?.data,
          status: error.response?.status
        })
        this.showToastMessage(this.$t('categoryManager.moveFailed'), 'alert-error', 'fas fa-exclamation-circle')
        await this.loadCategories() // 롤백
      }
    },
    async handleToggleActive(category) {
      if (!category || !category.id) {
        console.error('Invalid category for toggle:', category)
        return
      }
      try {
        await axios.patch(`/api/tag-categories/${category.id}/`, {
          is_active: !category.is_active
        })
        await this.loadCategories()
      } catch (error) {
        console.error('카테고리 상태 변경 실패:', error)
        this.showToastMessage(this.$t('categoryManager.toggleFailed'), 'alert-error', 'fas fa-exclamation-circle')
      }
    },
    getCategoryPath(category) {
      if (!category) return ''
      return category.full_path || category.localized_name || category.name_ko || ''
    },
    handleEdit(category) {
      if (!category || !category.id) {
        console.error('Invalid category for edit:', category)
        return
      }
      this.editingCategory = category
      this.categoryForm = {
        name_ko: category.name_ko || '',
        name_en: category.name_en || '',
        name_es: category.name_es || '',
        name_zh: category.name_zh || '',
        name_ja: category.name_ja || '',
        parent: category.parent || null,
        order: category.order || 0,
        color: category.color || '',
        is_active: category.is_active !== false
      }
    },
    handleAddChild(parentCategory) {
      if (!parentCategory || !parentCategory.id) {
        console.error('Invalid parent category:', parentCategory)
        return
      }
      this.editingCategory = null
      this.categoryForm = {
        name_ko: '',
        name_en: '',
        name_es: '',
        name_zh: '',
        name_ja: '',
        parent: parentCategory.id,
        order: 0,
        color: '',
        is_active: true
      }
      this.showCreateModal = true
    },
    handleDelete(category) {
      if (!category || !category.id) {
        console.error('Invalid category for delete:', category)
        return
      }
      this.deletingCategory = category
      
      // 하위 카테고리 개수 계산 (재귀적으로)
      const countDescendants = (cat) => {
        if (!cat || !cat.children || !Array.isArray(cat.children)) return 0
        let count = cat.children.length
        cat.children.forEach(child => {
          count += countDescendants(child)
        })
        return count
      }
      
      const descendantCount = countDescendants(category)
      const categoryName = category.localized_name || category.name_ko || category.name_en || ''
      
      if (descendantCount > 0) {
        this.deleteConfirmMessage = this.$t('categoryManager.deleteConfirmWithChildren', { 
          name: categoryName,
          count: descendantCount
        })
      } else {
        this.deleteConfirmMessage = this.$t('categoryManager.deleteConfirm', { 
          name: categoryName
        })
      }
      
      this.showDeleteConfirm = true
    },
    cancelDelete() {
      this.showDeleteConfirm = false
      this.deletingCategory = null
      this.deleteConfirmMessage = ''
    },
    async confirmDelete() {
      if (!this.deletingCategory || !this.deletingCategory.id) {
        this.cancelDelete()
        return
      }
      
      try {
        await axios.delete(`/api/tag-categories/${this.deletingCategory.id}/`)
        await this.loadCategories()
        this.$emit('category-deleted', this.deletingCategory)
        this.cancelDelete()
      } catch (error) {
        console.error('카테고리 삭제 실패:', error)
        this.showToastMessage(this.$t('categoryManager.deleteFailed'), 'alert-error', 'fas fa-exclamation-circle')
        this.cancelDelete()
      }
    },
    async saveCategory() {
      try {
        if (this.editingCategory) {
          // 편집
          await axios.put(`/api/tag-categories/${this.editingCategory.id}/`, this.categoryForm)
        } else {
          // 생성
          await axios.post('/api/tag-categories/', this.categoryForm)
        }
        await this.loadCategories()
        this.closeModal()
      } catch (error) {
        console.error('카테고리 저장 실패:', error)
        
        // 구체적인 에러 메시지 추출
        let errorMessage = this.$t('categoryManager.saveFailed')
        
        if (error.response?.data) {
          // Django REST Framework의 에러 응답 형식 확인
          if (error.response.data.detail) {
            errorMessage = error.response.data.detail
          } else if (error.response.data.error) {
            errorMessage = error.response.data.error
          } else if (typeof error.response.data === 'string') {
            errorMessage = error.response.data
          } else if (error.response.data.non_field_errors) {
            // non_field_errors는 배열일 수 있음
            const errors = error.response.data.non_field_errors
            errorMessage = Array.isArray(errors) ? errors.join(', ') : errors
          } else {
            // 필드별 에러가 있는 경우 첫 번째 에러 메시지 사용
            const errorKeys = Object.keys(error.response.data)
            if (errorKeys.length > 0) {
              const firstError = error.response.data[errorKeys[0]]
              if (Array.isArray(firstError)) {
                errorMessage = firstError[0]
              } else if (typeof firstError === 'string') {
                errorMessage = firstError
              }
            }
          }
        } else if (error.message) {
          errorMessage = error.message
        }
        
        this.showToastMessage(errorMessage, 'alert-error', 'fas fa-exclamation-circle')
      }
    },
    showToastMessage(message, type, icon) {
      this.toastMessage = message
      this.toastType = type
      this.toastIcon = icon
      this.showToast = true
      setTimeout(() => {
        this.hideToast()
      }, 5000)
    },
    hideToast() {
      this.showToast = false
    },
    closeModal() {
      this.showCreateModal = false
      this.editingCategory = null
      this.categoryForm = {
        name_ko: '',
        name_en: '',
        name_es: '',
        name_zh: '',
        name_ja: '',
        parent: null,
        order: 0,
        color: '',
        is_active: true
      }
    }
  }
}
</script>

<style scoped>
.tag-category-manager {
  padding: 20px;
}

.manager-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.category-tree-container {
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 16px;
  background: white;
}

.category-tree {
  min-height: 100px;
}

.ghost {
  opacity: 0.5;
  background: #f0f0f0;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1050;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #dee2e6;
}

.modal-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.modal-body {
  padding: 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 20px;
  border-top: 1px solid #dee2e6;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.5rem;
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
  color: #495057;
}

/* Toast Notification - 기본 스타일은 공통 CSS (mobile-buttons.css)에 정의됨 */
</style>
