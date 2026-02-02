import Vue from 'vue'
import VueRouter from 'vue-router'
// axios는 더 이상 사용하지 않음 (즐겨찾기 기능 통합으로 인해)
import Home from '../views/Home.vue'
import GettingStarted from '../views/GettingStarted.vue'
import TakeExam from '../views/TakeExam.vue'
import RandomPractice from '../views/RandomPractice.vue'
import Results from '../views/Results.vue'
import QuestionFiles from '../views/QuestionFiles.vue'
// import TextToQuestions from '../views/TextToQuestions.vue'
import CreateExam from '../views/CreateExam.vue'
import ExamManagement from '../components/ExamManagement.vue'
import StudyManagement from '../components/StudyManagement.vue'
import StudyDetail from '../components/StudyDetail.vue'
import StudyProgressDashboard from '../components/StudyProgressDashboard.vue'
import VoiceInterviewResultDetail from '../components/VoiceInterviewResultDetail.vue'
import VoiceInterviewResultsList from '../components/VoiceInterviewResultsList.vue'
import MemberManagement from '../components/MemberManagement.vue'
import ExamDetail from '../components/ExamDetail.vue'
import Register from '../views/Register.vue'
import Login from '../views/Login.vue'
import Profile from '../views/Profile.vue'
import UserManagement from '../views/UserManagement.vue'
import TagCategoryManager from '../components/TagCategoryManager.vue'
// Favorites.vue는 ExamDetail.vue로 대체됨
import EmailVerification from '../views/EmailVerification.vue'
import PrivacyPolicy from '../views/PrivacyPolicy.vue'
import TermsOfService from '../views/TermsOfService.vue'
import ServiceIntroduction from '../views/ServiceIntroduction.vue'
import DevOpsInterview from '../views/DevOpsInterview.vue'
// Language-specific pages
import PrivacyPolicyKr from '../views/PrivacyPolicyKr.vue'
import PrivacyPolicyZh from '../views/PrivacyPolicyZh.vue'
import PrivacyPolicyEn from '../views/PrivacyPolicyEn.vue'
import PrivacyPolicyEs from '../views/PrivacyPolicyEs.vue'
import PrivacyPolicyJa from '../views/PrivacyPolicyJa.vue'
import TermsOfServiceKr from '../views/TermsOfServiceKr.vue'
import TermsOfServiceZh from '../views/TermsOfServiceZh.vue'
import TermsOfServiceEn from '../views/TermsOfServiceEn.vue'
import TermsOfServiceEs from '../views/TermsOfServiceEs.vue'
import TermsOfServiceJa from '../views/TermsOfServiceJa.vue'
import ServiceIntroductionKr from '../views/ServiceIntroductionKr.vue'
import ServiceIntroductionZh from '../views/ServiceIntroductionZh.vue'
import ServiceIntroductionEn from '../views/ServiceIntroductionEn.vue'
import ServiceIntroductionEs from '../views/ServiceIntroductionEs.vue'
import ServiceIntroductionJa from '../views/ServiceIntroductionJa.vue'
// 불필요한 import 제거 (즐겨찾기 기능 통합을 위해)

Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/getting-started',
    name: 'GettingStarted',
    component: GettingStarted
  },
  {
    path: '/take-exam/:examId',
    name: 'TakeExam',
    component: TakeExam
  },
  {
    path: '/take-exam',
    name: 'TakeExamSingle',
    component: TakeExam
  },
  {
    path: '/random-practice',
    name: 'RandomPractice',
    component: RandomPractice
  },
  {
    path: '/results',
    name: 'Results',
    component: Results
  },
  {
    path: '/question-files',
    name: 'QuestionFiles',
    component: QuestionFiles
  },
  {
    path: '/text-to-questions',
    name: 'TextToQuestions',
    component: () => import('../views/TextToQuestions.vue')
  },
  {
    path: '/create-exam',
    name: 'CreateExam',
    component: CreateExam
  },
  {
    path: '/exam-management',
    name: 'ExamManagement',
    component: ExamManagement
  },
  {
    path: '/study-management',
    name: 'StudyManagement',
    component: StudyManagement
  },
  {
    path: '/study-detail/:studyId',
    name: 'StudyDetail',
    component: StudyDetail
  },
  {
    path: '/study-progress-dashboard/:studyId',
    name: 'StudyProgressDashboard',
    component: StudyProgressDashboard
  },
  {
    path: '/member-management/:studyId',
    name: 'MemberManagement',
    component: MemberManagement
  },
  {
    path: '/exam-detail/:examId',
    name: 'ExamDetail',
    component: ExamDetail
  },
  {
    path: '/voice-interview-result/:resultId',
    name: 'VoiceInterviewResultDetail',
    component: VoiceInterviewResultDetail
  },
  {
    path: '/exam/:examId/voice-interview-results',
    name: 'VoiceInterviewResultsList',
    component: VoiceInterviewResultsList
  },
  {
    path: '/register',
    name: 'Register',
    component: Register
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/profile',
    name: 'Profile',
    component: Profile
  },
  {
    path: '/user-management',
    name: 'UserManagement',
    component: UserManagement
  },
  {
    path: '/category-management',
    name: 'CategoryManagement',
    component: TagCategoryManager
  },
  {
    path: '/favorites',
    name: 'Favorites',
    component: ExamDetail,
    props: () => ({ 
      favoriteMode: true,
      examId: null // ExamDetail에서 즐겨찾기 시험 ID를 자동으로 조회
    })
  },
  {
    path: '/verify-email/:token',
    name: 'EmailVerification',
    component: EmailVerification
  },
  {
    path: '/privacy-policy',
    name: 'PrivacyPolicy',
    component: PrivacyPolicy
  },
  {
    path: '/privacy-policy_kr',
    name: 'PrivacyPolicyKr',
    component: PrivacyPolicyKr
  },
  {
    path: '/privacy-policy_zh',
    name: 'PrivacyPolicyZh',
    component: PrivacyPolicyZh
  },
  {
    path: '/privacy-policy_en',
    name: 'PrivacyPolicyEn',
    component: PrivacyPolicyEn
  },
  {
    path: '/privacy-policy_es',
    name: 'PrivacyPolicyEs',
    component: PrivacyPolicyEs
  },
  {
    path: '/privacy-policy_ja',
    name: 'PrivacyPolicyJa',
    component: PrivacyPolicyJa
  },
  {
    path: '/terms-of-service',
    name: 'TermsOfService',
    component: TermsOfService
  },
  {
    path: '/terms-of-service_kr',
    name: 'TermsOfServiceKr',
    component: TermsOfServiceKr
  },
  {
    path: '/terms-of-service_zh',
    name: 'TermsOfServiceZh',
    component: TermsOfServiceZh
  },
  {
    path: '/terms-of-service_en',
    name: 'TermsOfServiceEn',
    component: TermsOfServiceEn
  },
  {
    path: '/terms-of-service_es',
    name: 'TermsOfServiceEs',
    component: TermsOfServiceEs
  },
  {
    path: '/terms-of-service_ja',
    name: 'TermsOfServiceJa',
    component: TermsOfServiceJa
  },
  {
    path: '/service-introduction',
    name: 'ServiceIntroduction',
    component: ServiceIntroduction
  },
  {
    path: '/service-introduction_kr',
    name: 'ServiceIntroductionKr',
    component: ServiceIntroductionKr
  },
  {
    path: '/service-introduction_zh',
    name: 'ServiceIntroductionZh',
    component: ServiceIntroductionZh
  },
  {
    path: '/service-introduction_en',
    name: 'ServiceIntroductionEn',
    component: ServiceIntroductionEn
  },
  {
    path: '/service-introduction_es',
    name: 'ServiceIntroductionEs',
    component: ServiceIntroductionEs
  },
  {
    path: '/service-introduction_ja',
    name: 'ServiceIntroductionJa',
    component: ServiceIntroductionJa
  },
  {
    path: '/devops-interview',
    name: 'DevOpsInterview',
    component: DevOpsInterview
  },
  {
    path: '/s/:shortCode',
    name: 'ShortUrlRedirect',
    component: () => import('../components/ShortUrlRedirect.vue')
  }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes,
  scrollBehavior(to, from, savedPosition) {
    // 저장된 위치가 있으면 그 위치로, 없으면 스크롤하지 않음
    if (savedPosition) {
      return savedPosition
    } else {
      // 자동 스크롤 완전 비활성화
      // false를 반환하면 스크롤이 발생하지 않음
      return false
    }
  }
})

export default router 