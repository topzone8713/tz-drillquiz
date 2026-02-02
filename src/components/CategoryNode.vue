<template>
  <div 
    v-if="category && category.id"
    class="category-node" 
    :class="{ 'inactive': !category.is_active }"
    :style="{ marginLeft: level * 20 + 'px' }"
    :data-category-id="category.id"
  >
    <div class="category-node-header">
      <span class="drag-handle" :title="$t('categoryManager.dragToMove')">
        <i class="fas fa-grip-vertical"></i>
      </span>
      <span class="category-name">
        <span v-if="category.color" class="category-color">{{ category.color }}</span>
        {{ localizedCategoryName }}
      </span>
      <span class="category-meta">
        <span class="badge" :class="category.is_active ? 'bg-success' : 'bg-secondary'">
          {{ category.is_active ? $t('common.active') : $t('common.inactive') }}
        </span>
        <span class="badge bg-secondary">{{ category.level }}{{ $t('categoryManager.level') }}</span>
        <span v-if="category.tags_count > 0" class="badge bg-info">
          {{ category.tags_count }}{{ $t('categoryManager.tags') }}
        </span>
      </span>
      <div class="category-actions">
        <button 
          @click="$emit('toggle-active', category)" 
          class="btn btn-sm"
          :class="category.is_active ? 'btn-outline-warning' : 'btn-outline-success'"
          :title="category.is_active ? $t('categoryManager.deactivate') : $t('categoryManager.activate')"
        >
          <i class="fas" :class="category.is_active ? 'fa-toggle-on' : 'fa-toggle-off'"></i>
        </button>
        <button @click="$emit('add-child', category)" class="btn btn-sm btn-outline-primary" :title="$t('categoryManager.addChild')">
          <i class="fas fa-plus"></i>
        </button>
        <button @click="$emit('edit', category)" class="btn btn-sm btn-outline-secondary" :title="$t('common.edit')">
          <i class="fas fa-edit"></i>
        </button>
        <button @click="$emit('delete', category)" class="btn btn-sm btn-outline-danger" :title="$t('common.delete')">
          <i class="fas fa-trash"></i>
        </button>
      </div>
    </div>
    <draggable
      :list="localChildren"
      :animation="200"
      group="categories"
      :disabled="false"
      ghost-class="ghost"
      @end="(evt) => handleDragEnd(evt)"
      @add="(evt) => handleDragAdd(evt)"
      handle=".drag-handle"
      class="category-children"
      :data-parent-id="category.id"
    >
        <CategoryNode
          v-for="child in filteredChildren"
          :key="child.id"
          :category="child"
          :level="level + 1"
          :show-inactive="showInactive"
          @edit="$emit('edit', $event)"
          @delete="$emit('delete', $event)"
          @add-child="$emit('add-child', $event)"
          @toggle-active="$emit('toggle-active', $event)"
          @move="$emit('move', $event)"
          @update-children="$emit('update-children', $event)"
        />
    </draggable>
  </div>
</template>

<script>
import draggable from 'vuedraggable'

export default {
  name: 'CategoryNode',
  components: {
    draggable,
    CategoryNode: () => import('./CategoryNode.vue')
  },
  props: {
    category: {
      type: Object,
      required: true
    },
    level: {
      type: Number,
      default: 0
    },
    showInactive: {
      type: Boolean,
      default: false
    }
  },
  emits: ['edit', 'delete', 'add-child', 'toggle-active', 'move', 'update-children'],
  data() {
    return {
      localChildren: []
    }
  },
  watch: {
    'category.children': {
      handler(newVal) {
        // children이 없어도 빈 배열로 초기화하여 드롭 영역을 유지
        this.localChildren = newVal ? [...newVal] : []
      },
      immediate: true,
      deep: true
    }
  },
  computed: {
    filteredChildren() {
      if (!this.localChildren || !Array.isArray(this.localChildren)) {
        return []
      }
      if (this.showInactive) {
        return this.localChildren.filter(c => c && c.id)
      }
      return this.localChildren.filter(c => c && c.id && c.is_active !== false)
    },
    localizedCategoryName() {
      if (!this.category) return ''
      
      // 프론트엔드에서 현재 언어에 맞는 이름 직접 선택
      const currentLang = this.$i18n.locale || 'en'
      
      // 언어별 우선순위: 현재 언어 → 영어 → 한국어 → 스페인어 → 중국어 → 일본어
      if (currentLang === 'ko') {
        return this.category.name_ko || this.category.name_en || this.category.name_es || this.category.name_zh || this.category.name_ja || ''
      } else if (currentLang === 'zh') {
        return this.category.name_zh || this.category.name_en || this.category.name_ko || this.category.name_es || this.category.name_ja || ''
      } else if (currentLang === 'es') {
        return this.category.name_es || this.category.name_en || this.category.name_ko || this.category.name_zh || this.category.name_ja || ''
      } else if (currentLang === 'ja') {
        return this.category.name_ja || this.category.name_en || this.category.name_ko || this.category.name_es || this.category.name_zh || ''
      } else {
        // 영어 또는 기타: name_en 우선, 없으면 다른 언어
        return this.category.name_en || this.category.name_ko || this.category.name_es || this.category.name_zh || this.category.name_ja || ''
      }
    }
  },
  methods: {
    handleDragAdd(evt) {
      console.log('[CategoryNode] handleDragAdd 이벤트 발생:', {
        categoryId: this.category.id,
        categoryName: this.category.name_ko,
        newIndex: evt.newIndex,
        item: evt.item,
        from: evt.from,
        to: evt.to,
        fromElement: evt.from?.element,
        toElement: evt.to?.element
      })
      
      // 다른 그룹에서 아이템이 추가된 경우
      if (evt.from !== evt.to) {
        const addedItem = evt.item
        // category-node 요소에서 ID 찾기
        const categoryNode = addedItem.closest('.category-node') || addedItem.querySelector('.category-node')
        const addedCategoryId = categoryNode?.getAttribute('data-category-id') || 
                               addedItem.getAttribute('data-category-id') ||
                               addedItem.querySelector('[data-category-id]')?.getAttribute('data-category-id')
        
        console.log('[CategoryNode] 외부에서 카테고리 추가됨:', {
          addedCategoryId,
          parentCategoryId: this.category.id,
          newIndex: evt.newIndex,
          itemElement: addedItem,
          categoryNode: categoryNode
        })
        
        if (addedCategoryId) {
          // 부모에게 알림
          this.$emit('move', {
            category: { id: parseInt(addedCategoryId) },
            newParent: this.category,
            newOrder: evt.newIndex,
            evt
          })
        } else {
          console.warn('[CategoryNode] 추가된 카테고리의 ID를 찾을 수 없음')
        }
      }
    },
    handleDragEnd(evt) {
      console.log('[CategoryNode] handleDragEnd 이벤트 발생:', {
        categoryId: this.category.id,
        categoryName: this.category.name_ko,
        oldIndex: evt.oldIndex,
        newIndex: evt.newIndex,
        from: evt.from,
        to: evt.to,
        localChildren: this.localChildren.map(c => ({ id: c.id, name: c.name_ko }))
      })
      
      // 같은 그룹 내에서 순서만 변경된 경우
      if (evt.from === evt.to && evt.oldIndex !== evt.newIndex) {
        console.log('[CategoryNode] 같은 그룹 내 순서 변경')
        
        // 부모에게 변경사항 알림
        this.$emit('update-children', {
          category: this.category,
          children: this.localChildren
        })
        
        this.$emit('move', {
          category: this.category,
          evt
        })
      }
    }
  }
}
</script>

<style scoped>
.category-node {
  margin-bottom: 8px;
}

.category-node.inactive {
  opacity: 0.6;
}

.category-node.inactive .category-name {
  text-decoration: line-through;
}

.category-node-header {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 4px;
  gap: 12px;
}

.drag-handle {
  cursor: move;
  color: #6c757d;
  margin-right: 8px;
  padding: 4px;
}

.drag-handle:hover {
  color: #495057;
}

.category-name {
  flex: 1;
  font-weight: 500;
}

.name-ko {
  font-weight: 600;
}

.name-en {
  color: #6c757d;
  font-size: 0.9em;
}

.category-color {
  margin-right: 4px;
}

.category-meta {
  display: flex;
  gap: 4px;
}

.category-actions {
  display: flex;
  gap: 4px;
}

.category-children {
  margin-top: 8px;
  padding-left: 20px;
  border-left: 2px solid #dee2e6;
}

.ghost {
  opacity: 0.5;
  background: #f0f0f0;
}
</style>

