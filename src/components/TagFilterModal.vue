<template>
  <div>
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
    
    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteConfirm" class="modal-overlay delete-confirm-overlay" @click="cancelDeleteConfirm">
      <div class="modal-content delete-confirm-modal" @click.stop>
        <div class="modal-header">
          <h5 class="modal-title">
            <i class="fas fa-exclamation-triangle text-danger"></i>
            {{ deleteConfirmTitle }}
          </h5>
          <button type="button" class="btn-close" @click="cancelDeleteConfirm">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <p class="mb-0">{{ deleteConfirmMessage }}</p>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="cancelDeleteConfirm">
            <i class="fas fa-times"></i>
            <span>{{ $t('tagFilterModal.cancel') }}</span>
          </button>
          <button type="button" class="btn btn-danger" @click="confirmDeleteTag">
            <i class="fas fa-trash"></i>
            <span>{{ $t('tagFilterModal.deleteConfirm') }}</span>
          </button>
        </div>
      </div>
    </div>

    <div v-if="show" class="modal-overlay" @click="closeModal">
    <div class="modal-content" @click.stop>
      <!-- Modal Header -->
      <div class="modal-header">
        <h5 class="modal-title">{{ $t('tagFilterModal.title') }}</h5>
        <button type="button" class="btn-close" @click="closeModal">
          <i class="fas fa-times"></i>
        </button>
      </div>
      
      <!-- Modal Body -->
      <div class="modal-body">
        <!-- Category Filter -->
        <div v-if="categories.length > 0" class="category-filter-section mb-4">
          <label class="form-label small text-muted">{{ $t('tagFilterModal.categoryFilter') }}</label>
          <select v-model="selectedCategoryId" class="form-select form-select-sm" @change="filterTags">
            <option value="">{{ $t('tagFilterModal.allCategories') }}</option>
            <option v-for="category in categories" :key="category.id" :value="category.id">
              {{ getCategoryDisplayName(category) }}
            </option>
          </select>
        </div>
        
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
              :placeholder="$t('tagFilterModal.searchPlaceholder')"
              @input="filterTags"
              @keyup.enter="addNewTag"
            />
            <button 
              @click="addNewTag" 
              class="btn btn-outline-primary"
              :disabled="!searchQuery.trim()"
              :title="$t('tagFilter.addNewTag') || '새 태그 추가'"
            >
              <i class="fas fa-plus"></i>
            </button>
          </div>
          <small v-if="searchQuery.trim()" class="text-muted mt-1 d-block">
            {{ $t('tagFilter.addNewTagHint') || 'Enter 키를 누르거나 + 버튼을 클릭하여 새 태그를 추가할 수 있습니다.' }}
          </small>
        </div>
        
        <!-- Popular Tags Section -->
        <div v-if="!searchQuery && popularTags.length > 0" class="popular-tags-section mb-4">
          <h6 class="section-title">{{ $t('tagFilterModal.popularTags') }}</h6>
          <div class="tags-grid">
            <div
              v-for="tag in popularTags"
              :key="tag.id"
              class="tag-item"
              :class="{ 
                'selected': selectedTagIds.includes(tag.id),
                'disabled': tag.id === requiredTagId
              }"
              @click.stop="toggleTag(tag.id)"
            >
              <input
                type="checkbox"
                :checked="selectedTagIds.includes(tag.id)"
                :disabled="tag.id === requiredTagId"
                class="tag-checkbox"
                @click.stop="toggleTag(tag.id)"
              />
              <span class="tag-name">{{ getLocalizedTagName(tag) }}</span>
              <span v-if="getCategoryPathsForTag(tag).length > 0" class="tag-category-path">
                ({{ getCategoryPathsForTag(tag).join(', ') }})
              </span>
              <span v-if="tag.id === requiredTagId" class="tag-badge">{{ $t('common.required') }}</span>
              <button
                v-if="selectedTagIds.includes(tag.id) && tag.id !== requiredTagId"
                @click.stop="deleteTagFromDB(tag)"
                class="tag-delete-btn"
                :title="$t('tagFilterModal.deleteTag')"
              >
                <i class="fas fa-times"></i>
              </button>
            </div>
          </div>
        </div>
        
        <!-- All Tags Section -->
        <div class="all-tags-section">
          <h6 class="section-title">
            {{ searchQuery ? $t('tagFilterModal.searchResults') : $t('tagFilterModal.allTags') }}
            <span v-if="filteredTags.length > 0" class="tag-count">({{ filteredTags.length }})</span>
          </h6>
          
          <div v-if="filteredTags.length > 0" class="tags-list">
            <div
              v-for="tag in filteredTags"
              :key="tag.id"
              class="tag-item"
              :class="{ 
                'selected': selectedTagIds.includes(tag.id),
                'disabled': tag.id === requiredTagId
              }"
              @click.stop="toggleTag(tag.id)"
            >
              <input
                type="checkbox"
                :checked="selectedTagIds.includes(tag.id)"
                :disabled="tag.id === requiredTagId"
                class="tag-checkbox"
                @click.stop="toggleTag(tag.id)"
              />
              <span class="tag-name">{{ getLocalizedTagName(tag) }}</span>
              <span v-if="getCategoryPathsForTag(tag).length > 0" class="tag-category-path">
                ({{ getCategoryPathsForTag(tag).join(', ') }})
              </span>
              <span v-if="tag.id === requiredTagId" class="tag-badge">{{ $t('common.required') }}</span>
              <button
                v-if="selectedTagIds.includes(tag.id) && tag.id !== requiredTagId"
                @click.stop="deleteTagFromDB(tag)"
                class="tag-delete-btn"
                :title="$t('tagFilterModal.deleteTag')"
              >
                <i class="fas fa-times"></i>
              </button>
            </div>
          </div>
          
          <div v-else class="no-results">
            <i class="fas fa-search"></i>
            <p>{{ $t('tagFilterModal.noResults') }}</p>
          </div>
        </div>
      </div>
      
      <!-- Modal Footer -->
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" @click="clearAll">
          <i class="fas fa-eraser"></i>
          <span>{{ $t('tagFilterModal.clearAll') }}</span>
        </button>
        <div class="footer-actions">
          <button type="button" class="btn btn-outline-secondary" @click="closeModal">
            <i class="fas fa-times"></i>
            <span>{{ $t('tagFilterModal.cancel') }}</span>
          </button>
          <button type="button" class="btn btn-primary" @click="applyFilters">
            <i class="fas fa-check"></i>
            <span>{{ $t('tagFilterModal.showResults') }} ({{ selectedTagIds.length }})</span>
          </button>
        </div>
      </div>
    </div>
  </div>
  </div>
</template>

<script>
import axios from 'axios'
import { getCurrentDomainConfig } from '@/utils/domainUtils'

export default {
  name: 'TagFilterModal',
  props: {
    show: {
      type: Boolean,
      default: false
    },
    selectedTags: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      allTags: [],
      categories: [],
      categoryTree: [],
      searchQuery: '',
      selectedTagIds: Array.isArray(this.selectedTags) ? [...this.selectedTags] : [],
      selectedCategoryId: '',
      loading: false,
      showDeleteConfirm: false,
      deleteConfirmTitle: '',
      deleteConfirmMessage: '',
      tagToDelete: null,
      // Toast notification
      showToast: false,
      toastMessage: '',
      toastType: 'alert-warning',
      toastIcon: 'fas fa-exclamation-triangle',
      tagsLoaded: false // 태그 로드 상태 추적
    }
  },
  computed: {
    popularTags() {
      // 자주 사용되는 태그 (사용 빈도 기준으로 상위 10개)
      console.log('🔄 popularTags computed 호출 - allTags:', this.allTags, 'selectedCategoryId:', this.selectedCategoryId)
      
      let filtered = this.allTags.filter(tag => tag.usage_count > 0)
      
      // 카테고리 필터가 선택된 경우 해당 카테고리 안의 태그만 필터링
      if (this.selectedCategoryId) {
        filtered = filtered.filter(tag => {
          return tag.categories && tag.categories.some(cat => cat.id === parseInt(this.selectedCategoryId))
        })
      }
      
      const popular = filtered
        .sort((a, b) => (b.usage_count || 0) - (a.usage_count || 0))
        .slice(0, 10)
      console.log('📊 popularTags 결과:', popular)
      return popular
    },
    filteredTags() {
      console.log('🔄 filteredTags computed 호출 - searchQuery:', this.searchQuery, 'selectedCategoryId:', this.selectedCategoryId, 'allTags:', this.allTags)
      
      let filtered = this.allTags
      
      // 카테고리 필터링
      if (this.selectedCategoryId) {
        const categoryId = parseInt(this.selectedCategoryId)
        console.log('🔍 카테고리 필터링 - categoryId:', categoryId)
        filtered = filtered.filter(tag => {
          if (!tag.categories || !Array.isArray(tag.categories)) {
            return false
          }
          // 카테고리 ID 직접 비교
          const hasCategory = tag.categories.some(cat => {
            const catId = typeof cat === 'object' ? cat.id : cat
            return parseInt(catId) === categoryId
          })
          if (hasCategory) {
            console.log('✅ 태그가 카테고리에 속함:', tag.name_ko || tag.name_en, '카테고리:', tag.categories)
          }
          return hasCategory
        })
        console.log('📊 카테고리 필터링 후 태그 수:', filtered.length)
      }
      
      // 검색어 필터링
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase()
        filtered = filtered.filter(tag => {
          const koName = (tag.name_ko || '').toLowerCase()
          const enName = (tag.name_en || '').toLowerCase()
          const categoryPaths = (tag.category_paths || []).join(' ').toLowerCase()
          return koName.includes(query) || enName.includes(query) || categoryPaths.includes(query)
        })
      }
      
      console.log('📊 filteredTags 결과:', filtered)
      return filtered
    },
    requiredTagId() {
      // 현재 도메인의 필수 태그 ID 반환 (DevOps, LeetCode 등)
      const domainConfig = getCurrentDomainConfig()
      if (!domainConfig) {
        return null
      }
      
      try {
        const stored = sessionStorage.getItem(domainConfig.storageKey)
        return stored ? parseInt(stored, 10) : null
      } catch (error) {
        console.warn(`sessionStorage에서 ${domainConfig.tagName} 태그 ID를 읽을 수 없습니다:`, error)
        return null
      }
    }
  },
  watch: {
    selectedTags: {
      handler(newValue) {
        // newValue가 null이거나 배열이 아닌 경우 빈 배열로 설정
        this.selectedTagIds = Array.isArray(newValue) ? [...newValue] : []
      },
      immediate: true
    },
    show: {
      handler(newValue) {
        console.log('🔄 TagFilterModal show watch - show:', newValue)
        if (newValue && !this.tagsLoaded) {
          this.loadTags()
        }
      }
    },
    selectedCategoryId: {
      handler(newValue, oldValue) {
        console.log('🔄 selectedCategoryId 변경:', oldValue, '->', newValue)
        // 카테고리 변경 시 강제로 업데이트
        this.$nextTick(() => {
          this.$forceUpdate()
        })
      }
    }
  },
  async mounted() {
    console.log('🔄 TagFilterModal mounted - show:', this.show)
    // show가 true일 때만 로드 (중복 로드 방지)
    if (this.show && !this.tagsLoaded) {
    await this.loadTags()
    }
  },
  methods: {
    async loadTags() {
      try {
        this.loading = true
        console.log('🔄 TagFilterModal loadTags 시작')
        
        // DevOps 도메인 필터링 유틸리티 import
        const { getCurrentDomainConfig, getDevOpsCategoryId, getDevOpsCategoryTags } = await import('@/utils/domainUtils')
        const domainConfig = getCurrentDomainConfig()
        const isDevOps = domainConfig && domainConfig.keyword === 'devops'
        
        // DevOps 도메인인 경우 서버에서 DevOps 태그 정보를 먼저 가져오기
        if (isDevOps) {
          console.log('🏷️ DevOps 도메인 감지 - 서버에서 DevOps 태그 정보 조회')
          await this.fetchDevOpsTagFromServer()
        }
        
        // 태그와 카테고리를 병렬로 로드
        const [tagsResponse, categoriesResponse] = await Promise.all([
          axios.get('/api/studies/tags/'),
          axios.get('/api/tag-categories/tree/').catch(() => ({ data: [] })) // 카테고리 로드 실패해도 계속 진행
        ])
        
        console.log('📡 태그 API 응답 전체:', tagsResponse)
        console.log('📡 태그 API 응답 데이터:', tagsResponse.data)
        console.log('📡 태그 API 응답 상태:', tagsResponse.status)
        
        let allTags = tagsResponse.data || []
        let categories = categoriesResponse.data || []
        
        if (isDevOps) {
          // 카테고리 ID 가져오기
          const categoryId = getDevOpsCategoryId(categories)
          if (categoryId) {
            // "IT 기술 > IT 기술" 카테고리의 태그만 필터링
            allTags = getDevOpsCategoryTags(allTags, categoryId)
            console.log('✅ DevOps 도메인 태그 필터링 적용:', allTags.length, '개 태그')
            
            // 카테고리 트리도 필터링
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
              categories = [devopsCategory]
              console.log('✅ DevOps 도메인 카테고리 필터링 적용:', devopsCategory.name_ko)
            }
          }
        }
        
        this.allTags = allTags
        
        // 카테고리 트리 저장 (경로 생성용)
        this.categoryTree = categories
        
        // 카테고리 트리를 평면화 (필터 드롭다운용)
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
        this.categories = flattenCategories(categories)
        
        // 태그 로드 완료 표시
        this.tagsLoaded = true
        
        console.log('📊 allTags 설정 후:', this.allTags)
        console.log('📊 로드된 태그 수:', this.allTags.length)
        console.log('📊 로드된 카테고리 수:', this.categories.length)
        console.log('📊 인기 태그 수:', this.popularTags.length)
        console.log('📊 인기 태그 목록:', this.popularTags)
      } catch (error) {
        console.error('태그 로드 실패:', error)
        this.$emit('error', error)
      } finally {
        this.loading = false
      }
    },
    
    async fetchDevOpsTagFromServer() {
      try {
        const response = await fetch('/api/tags/')
        const data = await response.json()
        
        if (data.results && Array.isArray(data.results)) {
          // 모든 지원 언어 필드를 확인하도록 수정
          const devopsTag = data.results.find(tag => {
            // 모든 지원 언어 필드 확인 (ko, en, es, zh, ja)
            const supportedLanguages = ['ko', 'en', 'es', 'zh', 'ja']
            for (const lang of supportedLanguages) {
              if (tag[`name_${lang}`] === 'DevOps') {
                return true
              }
            }
            // localized_name도 확인
            return tag.localized_name === 'DevOps'
          })
          
          if (devopsTag) {
            const tagId = devopsTag.id
            this.setDevOpsTagIdToStorage(tagId)
            console.log('✅ 서버에서 DevOps 태그 ID 가져옴:', tagId)
          } else {
            console.warn('⚠️ 서버에서 DevOps 태그를 찾을 수 없습니다.')
          }
        } else {
          console.warn('⚠️ 태그 API 응답 형식이 올바르지 않습니다.')
        }
      } catch (error) {
        console.error('DevOps 태그 정보 조회 실패:', error)
      }
    },
    
    setDevOpsTagIdToStorage(tagId) {
      try {
        sessionStorage.setItem('devops_tag_id', tagId.toString())
      } catch (error) {
        console.warn('sessionStorage에 DevOps 태그 ID를 저장할 수 없습니다:', error)
      }
    },
    filterTags() {
      // 검색어가 변경될 때마다 필터링 (computed property가 자동으로 처리)
    },
    async addNewTag() {
      const tagName = this.searchQuery.trim()
      
      if (!tagName) {
        return
      }
      
      // 이미 존재하는 태그인지 확인
      const existingTag = this.allTags.find(tag => {
        const koName = (tag.name_ko || '').toLowerCase()
        const enName = (tag.name_en || '').toLowerCase()
        const query = tagName.toLowerCase()
        return koName === query || enName === query
      })
      
      if (existingTag) {
        // 이미 존재하는 태그인 경우 선택만 추가
        if (!this.selectedTagIds.includes(existingTag.id)) {
          this.selectedTagIds.push(existingTag.id)
        }
        this.searchQuery = ''
        return
      }
      
      try {
        // 태그 생성 데이터 준비
        const tagData = {
          name_ko: tagName,
          name_en: tagName
        }
        
        // 선택된 카테고리가 있으면 카테고리 ID 추가
        if (this.selectedCategoryId) {
          tagData.categories = [parseInt(this.selectedCategoryId)]
        }
        
        const response = await axios.post('/api/tags/', tagData)
        
        // 태그 목록을 다시 로드하여 카테고리 정보 포함
        await this.loadTags()
        
        // 새 태그를 자동으로 선택
        if (!this.selectedTagIds.includes(response.data.id)) {
          this.selectedTagIds.push(response.data.id)
        }
        
        this.searchQuery = ''
        this.$emit('tag-created', response.data)
        
        // 태그 목록 업데이트를 위해 강제 리렌더링
        this.$nextTick(() => {
          this.$forceUpdate()
        })
        
      } catch (error) {
        console.error('태그 생성 실패:', error)
        this.$emit('error', error)
      }
    },
    toggleTag(tagId) {
      console.log('🔄 toggleTag 호출됨 - tagId:', tagId)
      console.log('📊 현재 selectedTagIds:', this.selectedTagIds)
      
      // 필수 태그는 제거할 수 없음
      if (tagId === this.requiredTagId) {
        console.log('🚫 필수 태그는 제거할 수 없음')
        return
      }
      
      const index = this.selectedTagIds.indexOf(tagId)
      console.log('📊 index:', index)
      if (index > -1) {
        // 태그 제거 시도 - 최소 1개는 유지해야 함
        if (this.selectedTagIds.length <= 1) {
          this.showToastMessage(this.$t('tagFilterModal.minOneTagRequired') || '최소 1개 이상의 태그가 필요합니다.', 'alert-warning', 'fas fa-exclamation-triangle')
          console.log('🚫 최소 1개 태그 유지 필요')
          return
        }
        console.log('➖ 태그 제거')
        this.selectedTagIds.splice(index, 1)
      } else {
        console.log('➕ 태그 추가')
        this.selectedTagIds.push(tagId)
      }
      console.log('📊 업데이트된 selectedTagIds:', this.selectedTagIds)
    },
    clearAll() {
      console.log('🔄 clearAll 호출됨')
      console.log('📊 clearAll 전 selectedTagIds:', this.selectedTagIds)
      
      // 필수 태그가 있으면 유지, 없으면 최소 1개는 유지해야 함
      if (this.requiredTagId && this.selectedTagIds.includes(this.requiredTagId)) {
        this.selectedTagIds = [this.requiredTagId]
        console.log('📊 필수 태그 유지 후 selectedTagIds:', this.selectedTagIds)
      } else {
        // 최소 1개 태그는 유지해야 함
        if (this.selectedTagIds.length > 0) {
          // 첫 번째 태그만 유지
          this.selectedTagIds = [this.selectedTagIds[0]]
          console.log('📊 최소 1개 태그 유지 후 selectedTagIds:', this.selectedTagIds)
          this.showToastMessage(this.$t('tagFilterModal.minOneTagRequired') || '최소 1개 이상의 태그가 필요합니다. 첫 번째 태그를 유지합니다.', 'alert-warning', 'fas fa-exclamation-triangle')
        } else {
          // 태그가 없으면 clearAll 불가
          this.showToastMessage(this.$t('tagFilterModal.minOneTagRequired') || '최소 1개 이상의 태그가 필요합니다.', 'alert-warning', 'fas fa-exclamation-triangle')
          console.log('🚫 clearAll 불가: 최소 1개 태그 필요')
          return
        }
      }
      
      // 부모 컴포넌트에 즉시 업데이트 알림
      this.$emit('update:selectedTags', [...this.selectedTagIds])
      // 강제로 UI 업데이트
      this.$nextTick(() => {
        this.$forceUpdate()
      })
    },
    applyFilters() {
      console.log('🔄 TagFilterModal applyFilters 호출됨')
      console.log('📊 selectedTagIds:', this.selectedTagIds)
      console.log('📊 selectedTagIds 길이:', this.selectedTagIds.length)
      
      // 최소 1개 이상의 태그가 필요함
      if (this.selectedTagIds.length === 0) {
        this.showToastMessage(this.$t('tagFilterModal.minOneTagRequired') || '최소 1개 이상의 태그를 선택해주세요.', 'alert-warning', 'fas fa-exclamation-triangle')
        console.log('🚫 applyFilters 실패: 최소 1개 태그 필요')
        return
      }
      
      console.log('📊 selectedTagIds 복사본:', [...this.selectedTagIds])
      this.$emit('update:selectedTags', [...this.selectedTagIds])
      this.$emit('apply', [...this.selectedTagIds])
      console.log('📤 apply 이벤트 발생됨')
      this.closeModal()
    },
    closeModal() {
      this.$emit('update:show', false)
      this.searchQuery = ''
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
    deleteTagFromDB(tag) {
      const tagName = this.getLocalizedTagName(tag)
      this.tagToDelete = tag
      this.deleteConfirmTitle = this.$t('tagFilterModal.deleteTagTitle') || '태그 삭제 확인'
      this.deleteConfirmMessage = this.$t('tagFilterModal.deleteTagConfirm', { tagName }) || `태그 "${tagName}"을(를) 데이터베이스에서 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.`
      this.showDeleteConfirm = true
    },
    async confirmDeleteTag() {
      if (!this.tagToDelete) {
        this.showDeleteConfirm = false
        return
      }
      
      const tag = this.tagToDelete
      const tagName = this.getLocalizedTagName(tag)
      this.showDeleteConfirm = false
      
      try {
        console.log('🗑️ 태그 삭제 시작 - tagId:', tag.id, 'tagName:', tagName)
        
        // API 호출하여 태그 삭제
        await axios.delete(`/api/tags/${tag.id}/`)
        
        console.log('✅ 태그 삭제 성공')
        
        // 선택 목록에서도 제거
        const index = this.selectedTagIds.indexOf(tag.id)
        if (index > -1) {
          this.selectedTagIds.splice(index, 1)
        }
        
        // 태그 목록에서 제거
        const tagIndex = this.allTags.findIndex(t => t.id === tag.id)
        if (tagIndex > -1) {
          this.allTags.splice(tagIndex, 1)
        }
        
        // 부모 컴포넌트에 업데이트 알림
        this.$emit('update:selectedTags', [...this.selectedTagIds])
        this.$emit('tag-deleted', tag)
        
        // 성공 메시지 (선택사항)
        console.log(`✅ 태그 "${tagName}"이(가) 삭제되었습니다.`)
        
      } catch (error) {
        console.error('❌ 태그 삭제 실패:', error)
        
        // 백엔드에서 반환한 에러 메시지 확인
        const errorData = error.response?.data || {}
        let errorMessage = errorData.error || errorData.detail || error.message || '태그 삭제에 실패했습니다.'
        
        // 사용 중인 경우 특별한 메시지 표시
        if (error.response?.status === 400 && errorData.usage_count) {
          const usageCount = errorData.usage_count
          const usageList = []
          
          if (usageCount.exams > 0) {
            usageList.push(this.$t('tagFilterModal.usageCount.exam', { count: usageCount.exams }))
          }
          if (usageCount.studies > 0) {
            usageList.push(this.$t('tagFilterModal.usageCount.study', { count: usageCount.studies }))
          }
          
          if (usageList.length > 0) {
            errorMessage = this.$t('tagFilterModal.deleteTagInUse', { 
              usage: usageList.join(', ')
            }) || `태그가 ${usageList.join(', ')}에서 사용 중이므로 삭제할 수 없습니다.`
          }
        }
        
        this.showToastMessage(errorMessage, 'alert-danger', 'fas fa-exclamation-circle')
        this.$emit('error', error)
      } finally {
        this.tagToDelete = null
      }
    },
    cancelDeleteConfirm() {
      this.showDeleteConfirm = false
      this.tagToDelete = null
      this.deleteConfirmTitle = ''
      this.deleteConfirmMessage = ''
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
    getCategoryDisplayName(category) {
      // full_path는 이미 다국어로 처리되어 있으므로 그대로 사용
      // 또는 localized_name이 있으면 사용
      const currentLang = this.$i18n.locale
      if (category.full_path) {
        return category.full_path
      }
      if (currentLang === 'ko') {
        return category.name_ko || category.name_en || category.name_es || category.name_zh || category.name_ja || category.localized_name || '카테고리 없음'
      } else if (currentLang === 'zh') {
        return category.name_zh || category.name_en || category.name_ko || category.name_es || category.name_ja || category.localized_name || '无类别'
      } else if (currentLang === 'es') {
        return category.name_es || category.name_en || category.name_ko || category.name_zh || category.name_ja || category.localized_name || 'Sin Categoría'
      } else if (currentLang === 'ja') {
        return category.name_ja || category.name_en || category.name_ko || category.name_es || category.name_zh || category.localized_name || 'カテゴリなし'
      } else {
        // 영어 또는 기타
        return category.name_en || category.name_ko || category.name_es || category.name_zh || category.name_ja || category.localized_name || 'No Category'
      }
    },
    getCategoryPathsForTag(tag) {
      // 태그의 카테고리 경로를 프론트엔드 언어에 맞게 생성
      if (!tag.categories || tag.categories.length === 0) {
        return []
      }
      
      const currentLang = this.$i18n.locale
      
      // 카테고리 트리에서 해당 카테고리를 찾아서 경로 생성
      const buildPath = (categoryId, tree) => {
        for (const cat of tree) {
          if (cat.id === categoryId) {
            return this.getCategoryFullPath(cat, currentLang)
          }
          if (cat.children && cat.children.length > 0) {
            const childPath = buildPath(categoryId, cat.children)
            if (childPath) return childPath
          }
        }
        return null
      }
      
      const paths = tag.categories.map(cat => {
        // 먼저 카테고리 트리에서 찾기
        if (this.categoryTree.length > 0) {
          const path = buildPath(cat.id, this.categoryTree)
          if (path) return path
        }
        
        // 카테고리 트리에서 찾지 못한 경우 full_path 사용
        if (cat.full_path) {
          return cat.full_path
        }
        
        // full_path도 없으면 카테고리 이름만 반환
        if (currentLang === 'ko') {
          return cat.name || cat.name_ko || cat.name_en || cat.name_es || cat.name_zh || cat.name_ja || '카테고리 없음'
        } else if (currentLang === 'zh') {
          return cat.name || cat.name_zh || cat.name_en || cat.name_ko || cat.name_es || cat.name_ja || '无类别'
        } else if (currentLang === 'es') {
          return cat.name || cat.name_es || cat.name_en || cat.name_ko || cat.name_zh || cat.name_ja || 'Sin Categoría'
        } else if (currentLang === 'ja') {
          return cat.name || cat.name_ja || cat.name_en || cat.name_ko || cat.name_es || cat.name_zh || 'カテゴリなし'
        } else {
          // 영어 또는 기타
          return cat.name || cat.name_en || cat.name_ko || cat.name_es || cat.name_zh || cat.name_ja || 'No Category'
        }
      })
      
      return paths.filter(p => p) // null 제거
    },
    getCategoryFullPath(category, language) {
      // 카테고리 트리에서 해당 카테고리를 찾고 부모까지 경로 구성
      const findCategoryAndBuildPath = (catId, tree, currentPath = []) => {
        for (const cat of tree) {
          const currentPathCopy = [...currentPath]
          
          // 현재 언어에 맞는 카테고리 이름 추가
          let categoryName = ''
          if (language === 'ko') {
            categoryName = cat.name_ko || cat.name_en || cat.name_es || cat.name_zh || cat.name_ja || cat.localized_name || '카테고리 없음'
          } else if (language === 'zh') {
            categoryName = cat.name_zh || cat.name_en || cat.name_ko || cat.name_es || cat.name_ja || cat.localized_name || '无类别'
          } else if (language === 'es') {
            categoryName = cat.name_es || cat.name_en || cat.name_ko || cat.name_zh || cat.name_ja || cat.localized_name || 'Sin Categoría'
          } else if (language === 'ja') {
            categoryName = cat.name_ja || cat.name_en || cat.name_ko || cat.name_es || cat.name_zh || cat.localized_name || 'カテゴリなし'
          } else {
            // 영어 또는 기타
            categoryName = cat.name_en || cat.name_ko || cat.name_es || cat.name_zh || cat.name_ja || cat.localized_name || 'No Category'
          }
          currentPathCopy.push(categoryName)
          
          // 찾는 카테고리인 경우 경로 반환
          if (cat.id === catId) {
            return currentPathCopy
          }
          
          // 자식이 있으면 재귀적으로 검색
          if (cat.children && cat.children.length > 0) {
            const foundPath = findCategoryAndBuildPath(catId, cat.children, currentPathCopy)
            if (foundPath) {
              return foundPath
            }
          }
        }
        return null
      }
      
      // 카테고리 트리에서 경로 찾기
      if (this.categoryTree.length > 0) {
        const path = findCategoryAndBuildPath(category.id, this.categoryTree)
        if (path && path.length > 0) {
          return path.join(' > ')
        }
      }
      
      // 트리에서 찾지 못한 경우 카테고리 객체의 정보 사용
      if (category.full_path) {
        // full_path가 있으면 사용 (백엔드 언어 기준일 수 있지만 일단 사용)
        return category.full_path
      }
      
      // 이름만 반환
      if (language === 'ko') {
        return category.name_ko || category.name_en || category.name_zh || category.name_ja || category.localized_name || category.name || '카테고리 없음'
      } else if (language === 'zh') {
        return category.name_zh || category.name_en || category.name_ko || category.name_es || category.name_ja || category.localized_name || category.name || '无类别'
      } else if (language === 'es') {
        return category.name_es || category.name_en || category.name_ko || category.name_zh || category.name_ja || category.localized_name || category.name || 'Sin Categoría'
      } else if (language === 'ja') {
        return category.name_ja || category.name_en || category.name_ko || category.name_es || category.name_zh || category.localized_name || category.name || 'カテゴリなし'
      } else {
        return category.name_en || category.name_ko || category.name_es || category.name_zh || category.name_ja || category.localized_name || category.name || 'No Category'
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
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000; /* 모달 오버레이 */
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e9ecef;
}

.modal-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
}

.btn-close {
  background: none;
  border: none;
  font-size: 18px;
  color: #6c757d;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
}

.btn-close:hover {
  background-color: #f8f9fa;
  color: #495057;
}

.modal-body {
  padding: 24px;
  flex: 1;
  overflow-y: auto;
}

.search-section .input-group-text {
  background-color: #f8f9fa;
  border-color: #ced4da;
  color: #6c757d;
}

.search-section .form-control {
  border-left: none;
  border-right: none;
}

.search-section .form-control:focus {
  border-color: #ced4da;
  box-shadow: none;
}

.search-section .btn {
  border-left: none;
  border-radius: 0 6px 6px 0;
}

.search-section .btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #495057;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.tag-count {
  font-size: 14px;
  font-weight: 400;
  color: #6c757d;
}

.tags-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 8px;
  margin-bottom: 16px;
}

.tags-list {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 8px;
}

.tag-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
  margin-bottom: 4px;
}

.tag-item:hover {
  background-color: #f8f9fa;
}

.tag-item.selected {
  background-color: #e3f2fd;
  color: #1976d2;
}

.tag-checkbox {
  margin-right: 12px;
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.tag-name {
  font-size: 14px;
  font-weight: 500;
  flex: 1;
}

.no-results {
  text-align: center;
  padding: 40px 20px;
  color: #6c757d;
}

.no-results i {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.no-results p {
  margin: 0;
  font-size: 16px;
}

.modal-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-top: 1px solid #e9ecef;
  background-color: #f8f9fa;
  border-radius: 0 0 12px 12px;
}

.footer-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.btn {
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
  border-color: #6c757d;
}

.btn-secondary:hover {
  background-color: #5a6268;
  border-color: #545b62;
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

.btn-outline-primary {
  background-color: transparent;
  color: #007bff;
  border: 1px solid #007bff;
}

.btn-outline-primary:hover {
  background-color: #007bff;
  color: white;
  border-color: #007bff;
}

.btn-outline-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background-color: transparent;
  color: #007bff;
  border-color: #007bff;
}

.btn-primary {
  background-color: #007bff;
  color: white;
  border-color: #007bff;
}

.btn-primary:hover {
  background-color: #0056b3;
  border-color: #004085;
}

/* Disabled tag styles */
.tag-item.disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background-color: #f8f9fa;
}

.tag-item.disabled:hover {
  background-color: #f8f9fa;
}

.tag-item.disabled .tag-checkbox:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.tag-item.disabled .tag-name {
  color: #6c757d;
}

/* Required tag badge */
.tag-badge {
  background-color: #dc3545;
  color: white;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 10px;
  margin-left: 8px;
  font-weight: 500;
}

.category-filter-section {
  margin-bottom: 16px;
}

.tag-category-path {
  font-size: 11px;
  color: #6c757d;
  margin-left: 8px;
  font-style: italic;
  font-weight: normal;
}

.tag-delete-btn {
  margin-left: auto;
  background: none;
  border: none;
  color: #dc3545;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  font-size: 12px;
  opacity: 0.7;
}

.tag-delete-btn:hover {
  background-color: #f8d7da;
  opacity: 1;
  color: #721c24;
}

.tag-delete-btn:active {
  transform: scale(0.95);
}

/* Delete Confirmation Modal Styles */
/* Toast Notification Styles - 기본 스타일은 공통 CSS (mobile-buttons.css)에 정의됨 */

.toast-content {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.toast-close {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  margin-left: 15px;
  opacity: 0.7;
}

.toast-close:hover {
  opacity: 1;
}

/* 타입별 스타일은 공통 CSS (mobile-buttons.css)에 정의됨 */

.delete-confirm-overlay {
  z-index: 2100; /* 삭제 확인 모달 */
}

.delete-confirm-modal {
  max-width: 500px;
  animation: modalFadeIn 0.2s ease-out;
}

.delete-confirm-modal .modal-header {
  border-bottom: 2px solid #dc3545;
  background: linear-gradient(135deg, #fff5f5 0%, #ffffff 100%);
}

.delete-confirm-modal .modal-title {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #dc3545;
  font-weight: 600;
}

.delete-confirm-modal .modal-title i {
  font-size: 20px;
}

.delete-confirm-modal .modal-body {
  padding: 24px;
  font-size: 15px;
  line-height: 1.6;
  color: #495057;
}

.delete-confirm-modal .modal-body p {
  white-space: pre-line; /* \n을 줄바꿈으로 표시 */
}

.delete-confirm-modal .modal-footer {
  border-top: 1px solid #e9ecef;
  padding: 16px 24px;
  gap: 12px;
}

.delete-confirm-modal .btn-danger {
  background-color: #dc3545;
  color: white;
  border-color: #dc3545;
  display: flex;
  align-items: center;
  gap: 6px;
}

.delete-confirm-modal .btn-danger:hover {
  background-color: #c82333;
  border-color: #bd2130;
}

.delete-confirm-modal .btn-secondary {
  display: flex;
  align-items: center;
  gap: 6px;
}

@keyframes modalFadeIn {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(-10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

/* Responsive */
@media (max-width: 768px) {
  .modal-content {
    width: 95%;
    max-height: 90vh;
  }
  
  .tags-grid {
    grid-template-columns: 1fr;
  }
  
  .modal-footer {
    flex-direction: row;
    gap: 12px;
    justify-content: flex-end;
  }
  
  .footer-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  /* 모달 푸터 버튼들 원형 버튼으로 */
  .modal-footer .btn {
    padding: 0 !important;
    width: 40px !important;
    height: 40px !important;
    border-radius: 50% !important;
    gap: 0 !important;
    min-width: auto !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 0 !important;
    flex-shrink: 0;
  }
  
  .modal-footer .btn i {
    font-size: 14px !important;
    line-height: 1 !important;
    color: white !important;
  }
  
  .modal-footer .btn-outline-secondary i {
    color: #6c757d !important;
  }
  
  .modal-footer .btn-outline-secondary:hover i {
    color: white !important;
  }
  
  .modal-footer .btn span {
    display: none !important;
  }
  
  /* Delete Confirm Modal 모바일 스타일 */
  .delete-confirm-modal {
    width: 95%;
    max-width: 95%;
  }
  
  .delete-confirm-modal .modal-footer {
    flex-direction: row;
    justify-content: flex-end;
  }
  
  .delete-confirm-modal .modal-footer .btn {
    width: auto;
    min-width: 40px;
    justify-content: center;
  }
  
  /* 모바일에서 Category Filter 라벨 숨기기 */
  .category-filter-section .form-label {
    display: none;
  }
}
</style>
