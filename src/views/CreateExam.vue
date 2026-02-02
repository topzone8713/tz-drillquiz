<template>
  <div class="create-exam">
    <h2>{{ $t('createExam.title') }}</h2>
    <div v-if="!isAdmin" class="alert alert-warning">
      {{ $t('createExam.adminOnly') }}
    </div>
    
    <div class="card">
      <div class="card-body">
        <h5 class="card-title">{{ $t('createExam.newExamTitle') }}</h5>
        
        <form @submit.prevent="createExam">
          <div class="mb-3">
            <label for="examTitle" class="form-label">{{ $t('createExam.examTitle') }}</label>
            <input 
              type="text" 
              class="form-control" 
              id="examTitle" 
              v-model="examForm.title"
              required
              :placeholder="$t('createExam.examTitlePlaceholder')"
            >
          </div>
          
          <div class="mb-3">
            <label for="questionCount" class="form-label">{{ $t('createExam.questionCount') }}</label>
            <input 
              type="number" 
              class="form-control" 
              id="questionCount" 
              v-model.number="examForm.questionCount"
              min="0" 
              max="100"
              required
            >
            <div class="form-text">{{ $t('createExam.questionCountDescription') }}</div>
          </div>
          
          <div class="mb-3">
            <div class="form-check">
              <input 
                class="form-check-input" 
                type="checkbox" 
                id="wrongQuestionsOnly"
                v-model="examForm.wrongQuestionsOnly"
              >
              <label class="form-check-label" for="wrongQuestionsOnly">
                {{ $t('createExam.wrongQuestionsOnly') }}
              </label>
            </div>
          </div>
          
          <div class="mb-3">
            <label for="difficulty" class="form-label">{{ $t('createExam.difficulty') }}</label>
            <select id="difficulty" class="form-control" v-model="examForm.difficulty">
              <option value="">{{ $t('createExam.allDifficulties') }}</option>
              <option value="easy">{{ $t('createExam.easy') }}</option>
              <option value="medium">{{ $t('createExam.medium') }}</option>
              <option value="hard">{{ $t('createExam.hard') }}</option>
            </select>
            <div class="form-text">{{ $t('createExam.difficultyDescription') }}</div>
          </div>
          
          <div class="mb-3">
            <label for="fileName" class="form-label">{{ $t('examManagement.fileSelection') }}</label>
            <select id="fileName" class="form-control" v-model="examForm.fileName" @change="onFileChange">
              <option value="">{{ $t('examManagement.allQuestions') }}</option>
              <option v-for="file in fileList" :key="file.name" :value="file.name">
                {{ file.name }} ({{ file.question_count }})
              </option>
            </select>
            <div class="form-text">{{ $t('examManagement.fileSelectionDescription') }}</div>
            <div v-if="selectedFileMaxQuestions > 0" class="form-text text-info">
              {{ $t('examManagement.selectedFileMaxQuestions') }}: {{ selectedFileMaxQuestions }}
            </div>
          </div>
          
          <button 
            type="submit" 
            class="btn btn-primary"
            :disabled="creating || !isAdmin"
          >
            {{ creating ? $t('examManagement.creating') : $t('examManagement.createExam') }}
          </button>
        </form>
        
        <div v-if="createResult" class="mt-3">
          <div v-if="createResult.success" class="alert alert-success">
            {{ $t('createExam.createSuccess') }}
            <br>
            <router-link :to="`/exam/${createResult.exam.id}`" class="btn btn-success mt-2">
              {{ $t('createExam.startExam') }}
            </router-link>
          </div>
          <div v-else class="alert alert-danger">
            {{ createResult.error }}
          </div>
        </div>
      </div>
    </div>

    <div class="card mt-4">
      <div class="card-body">
        <h5 class="card-title">{{ $t('createExam.questionPoolInfo') }}</h5>
        <div v-if="loading" class="text-center">
          <div class="spinner-border" role="status">
            <span class="visually-hidden">{{ $t('common.loading') }}</span>
          </div>
        </div>
        <div v-else>
          <p>{{ $t('createExam.totalQuestions') }}: {{ totalQuestions }}</p>
          <div v-if="totalQuestions === 0" class="alert alert-warning">
            {{ $t('createExam.noQuestionsInPool') }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { debugLog } from '@/utils/debugUtils'
import { isAdmin, hasStudyAdminRole } from '@/utils/permissionUtils'

export default {
  name: 'CreateExam',
  data() {
    return {
      examForm: {
        title: '',
        questionCount: 10,
        wrongQuestionsOnly: false,
        fileName: '',
        difficulty: ''
      },
      creating: false,
      createResult: null,
      loading: true,
      totalQuestions: 0,
      fileList: [],
      selectedFileMaxQuestions: 0
    }
  },
  computed: {
    isAdmin() {
      return isAdmin()
    },
    isStudyAdmin() {
      return hasStudyAdminRole()
    }
  },
  async mounted() {
    await this.loadQuestions()
    await this.loadFileList()
  },
  methods: {
    async loadQuestions() {
      try {
        const response = await axios.get('/api/questions/')
        this.totalQuestions = response.data.length
      } catch (error) {
        debugLog(this.$t('createExam.loadQuestionsError'), error, 'error')
      } finally {
        this.loading = false
      }
    },
    async loadFileList() {
      try {
        const response = await axios.get('/api/question-files/')
        this.fileList = response.data
      } catch (error) {
        this.fileList = []
      }
    },
    async createExam() {
      this.creating = true
      this.createResult = null
      try {
        const payload = {
          title: this.examForm.title,
          question_count: this.examForm.questionCount,
          wrong_questions_only: this.examForm.wrongQuestionsOnly,
          random_option: 'random',
          is_original: true,
          is_public: true
        }
        if (this.examForm.fileName) {
          payload.file_name = this.examForm.fileName
        }
        if (this.examForm.difficulty) {
          payload.difficulty = this.examForm.difficulty
        }
        const response = await axios.post('/api/create-exam/', payload)
        this.createResult = {
          success: true,
          exam: response.data
        }
        this.examForm = {
          title: '',
          questionCount: 10,
          wrongQuestionsOnly: false,
          fileName: '',
          difficulty: ''
        }
        this.selectedFileMaxQuestions = 0
      } catch (error) {
        this.createResult = {
          success: false,
          error: error.response?.data?.error || this.$t('createExam.createError')
        }
      } finally {
        this.creating = false
      }
    },
    onFileChange() {
      if (this.examForm.fileName) {
        const selectedFile = this.fileList.find(file => file.name === this.examForm.fileName)
        this.selectedFileMaxQuestions = selectedFile ? selectedFile.question_count : 0
        
        // question_count가 있는 경우에만 자동 업데이트
        if (this.selectedFileMaxQuestions > 0) {
          this.examForm.questionCount = this.selectedFileMaxQuestions
        } else {
          debugLog('📊 파일에 question_count 정보가 없어 자동 업데이트를 건너뜁니다.')
        }
      } else {
        this.selectedFileMaxQuestions = 0
        // 파일을 선택하지 않은 경우 기본값으로 복원
        this.examForm.questionCount = 10
      }
    }
  }
}
</script>

<style scoped>
.card {
  margin-bottom: 1rem;
}
</style> 