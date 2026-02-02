<template>
  <div class="ai-question-generator">
    <div v-if="showGenerator" class="card-modern ai-generator-card">
      <div class="card-header-modern">
      </div>
      <div class="card-body">
        <div class="form-group">
          <div class="textarea-container">
            <textarea 
              v-model="leetcodeProblems" 
              class="form-control" 
              rows="8"
              :placeholder="$t('examManagement.createForm.leetcodeProblemsPlaceholder')"
              @input="parseProblems"
            ></textarea>
            <button 
              @click="copyToClipboard" 
              class="copy-btn"
              :title="$t('examManagement.createForm.copyToClipboard')"
            >
              <i class="fas fa-copy"></i>
            </button>
          </div>
          <div class="form-text">{{ $t('examManagement.createForm.leetcodeProblemsHelp') }}</div>
        </div>
        
        <div v-if="parsedProblems.length > 0" class="parsed-problems">
          <h6>{{ $t('examManagement.createForm.parsedProblems') }} ({{ parsedProblems.length }})</h6>
          <div class="problem-list">
            <div 
              v-for="(problem, index) in parsedProblems" 
              :key="index"
              class="problem-item"
              :class="{ 'problem-error': problem.error }"
            >
              <div class="problem-info">
                <span class="problem-number">{{ problem.id }}</span>
                <span class="problem-title">{{ problem.title }}</span>
                <span class="problem-difficulty" :class="`difficulty-${problem.difficulty}`">
                  {{ problem.difficulty }}
                </span>
                <span v-if="problem.url" class="problem-url">
                  <a :href="problem.url" target="_blank" class="url-link">
                    <i class="fas fa-external-link-alt"></i>
                  </a>
                </span>
              </div>
              <div v-if="problem.error" class="problem-error-message">
                {{ problem.error }}
              </div>
            </div>
          </div>
        </div>
        
        <div class="generator-actions">
          <button @click="clearProblems" class="btn btn-secondary">
            <i class="fas fa-trash me-1"></i>
            {{ $t('examManagement.createForm.clearProblems') }}
          </button>
        </div>
        
      </div>
    </div>
  </div>
</template>

<script>
import { debugLog } from '@/utils/debugUtils'
import { parseLeetCodeProblems } from '@/utils/problemParser'

export default {
  name: 'AiQuestionGenerator',
  props: {
    showGenerator: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      leetcodeProblems: '146. LRU Cache\nMed.\n\n1. Two Sum\nEasy',
      parsedProblems: []
    }
  },
  methods: {
    toggleGenerator() {
      this.$emit('toggle-generator')
    },
    
    parseProblems() {
      // 공통 파싱 함수 사용
      this.parsedProblems = parseLeetCodeProblems(this.leetcodeProblems)
      
      console.log('🔍 parseProblems 완료 - 파싱된 문제들:', this.parsedProblems)
      console.log('🔍 파싱된 문제 개수:', this.parsedProblems.length)
      debugLog('파싱된 문제들:', this.parsedProblems)
      
      // 파싱 완료 후 자동으로 부모 컴포넌트에 전달
      this.emitParsedProblems()
    },
    
    // 파싱된 문제들을 부모 컴포넌트에 전달
    emitParsedProblems() {
      const emitData = {
        generated_count: this.parsedProblems.length,
        problems: JSON.parse(JSON.stringify(this.parsedProblems))
      }
      this.$emit('questions-generated', emitData)
    },
    
    normalizeDifficulty(difficulty) {
      const normalized = difficulty.toLowerCase()
      if (normalized.includes('easy')) return 'Easy'
      if (normalized.includes('med') || normalized.includes('medium')) return 'Medium'
      if (normalized.includes('hard')) return 'Hard'
      return 'Unknown'
    },
    
    generateUrlTitle(title) {
      return title
        .toLowerCase()
        .replace(/[^a-z0-9\s-]/g, '')
        .replace(/\s+/g, '-')
        .replace(/-+/g, '-')
        .trim('-')
    },
    
    
    clearProblems() {
      this.leetcodeProblems = ''
      this.parsedProblems = []
      // 빈 상태로 부모 컴포넌트에 알림
      this.$emit('questions-generated', {
        generated_count: 0,
        problems: []
      })
    },
    
    // 클립보드에 복사
    async copyToClipboard() {
      try {
        await navigator.clipboard.writeText(this.leetcodeProblems)
        // 성공 메시지 표시 (선택사항)
        console.log('클립보드에 복사되었습니다.')
      } catch (err) {
        console.error('클립보드 복사 실패:', err)
        // 폴백: 기존 방식으로 복사
        this.fallbackCopyToClipboard(this.leetcodeProblems)
      }
    },
    
    // 폴백 복사 방법
    fallbackCopyToClipboard(text) {
      const textArea = document.createElement('textarea')
      textArea.value = text
      document.body.appendChild(textArea)
      textArea.focus()
      textArea.select()
      try {
        document.execCommand('copy')
        console.log('클립보드에 복사되었습니다 (폴백 방법)')
      } catch (err) {
        console.error('클립보드 복사 실패:', err)
      }
      document.body.removeChild(textArea)
    }
  }
}
</script>

<style scoped>
.textarea-container {
  position: relative;
}

.copy-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 6px 8px;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  transition: all 0.2s ease;
  z-index: 10;
}

.copy-btn:hover {
  background: #f8f9fa;
  color: #333;
  border-color: #999;
}

.copy-btn:active {
  transform: scale(0.95);
}
.ai-question-generator {
  margin-top: 1rem;
}

.ai-generator-card {
  border: 2px solid #e3f2fd;
  background: linear-gradient(135deg, #f8f9ff 0%, #e8f4fd 100%);
}

.card-header-modern h5 {
  color: #1976d2;
  font-weight: 600;
}

.parsed-problems {
  margin-top: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.parsed-problems h6 {
  color: #495057;
  margin-bottom: 0.75rem;
  font-weight: 600;
}

.problem-list {
  max-height: 200px;
  overflow-y: auto;
}

.problem-item {
  display: flex;
  flex-direction: column;
  padding: 0.5rem;
  margin-bottom: 0.5rem;
  background: white;
  border-radius: 6px;
  border: 1px solid #dee2e6;
  transition: all 0.2s ease;
}

.problem-item:hover {
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.problem-item.problem-error {
  border-color: #dc3545;
  background: #fff5f5;
}

.problem-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.problem-number {
  font-weight: 600;
  color: #1976d2;
  min-width: 30px;
}

.problem-title {
  flex: 1;
  color: #495057;
  font-weight: 500;
}

.problem-difficulty {
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.difficulty-easy {
  background: #d4edda;
  color: #155724;
}

.difficulty-medium {
  background: #fff3cd;
  color: #856404;
}

.difficulty-hard {
  background: #f8d7da;
  color: #721c24;
}

.difficulty-unknown {
  background: #e2e3e5;
  color: #6c757d;
}

.problem-url {
  margin-left: auto;
}

.url-link {
  color: #1976d2;
  text-decoration: none;
  font-size: 0.875rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.url-link:hover {
  background-color: #e3f2fd;
  text-decoration: none;
}


.problem-error-message {
  color: #dc3545;
  font-size: 0.875rem;
  margin-top: 0.25rem;
  font-style: italic;
}

.generator-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1rem;
  flex-wrap: wrap;
}

.generation-result {
  margin-top: 1rem;
}

.alert {
  border-radius: 8px;
  border: none;
  padding: 1rem;
}

.alert-success {
  background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
  color: #155724;
}

.alert-danger {
  background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
  color: #721c24;
}

@media (max-width: 768px) {
  .problem-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .generator-actions {
    flex-direction: column;
  }
  
  .generator-actions .btn {
    width: 100%;
  }
}
</style>
