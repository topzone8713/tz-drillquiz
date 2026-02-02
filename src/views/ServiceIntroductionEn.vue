<template>
  <div class="service-introduction">
    <div class="container-fluid">
      <!-- Header Section -->
      <div class="jumbotron bg-primary text-white text-center py-5 mb-5">
        <div class="container">
          <h1 class="display-4 mb-4">Service Introduction</h1>
          <p class="lead">An innovative platform for efficient learning</p>
        </div>
      </div>

      <!-- Main Content -->
      <div class="container">
        <div class="mb-3">
          <button @click="goBack" class="btn btn-outline-secondary">
            <i class="fas fa-arrow-left"></i> Back
          </button>
        </div>
        <!-- 1. New Way of Repetitive Learning -->
        <div class="row mb-5">
          <div class="col-lg-8 mx-auto">
            <div class="card shadow-sm">
              <div class="card-body p-4">
                <div class="d-flex align-items-center mb-3">
                  <div class="feature-icon bg-primary text-white rounded-circle d-flex align-items-center justify-content-center me-3" style="width: 60px; height: 60px;">
                    <i class="fas fa-redo fa-lg"></i>
                  </div>
                  <h2 class="card-title mb-0">New Way of Repetitive Learning</h2>
                </div>
                <p class="card-text mb-4">DrillQuiz provides a smart repetitive learning system based on the forgetting curve theory. It's not just simple repetition, but a scientifically designed learning pattern that strengthens long-term memory.</p>
                
                <div class="row">
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-primary">Drain System</h5>
                      <p class="text-muted">Automatically collects incorrect problems so you can focus on repetitive learning. Once you get a problem wrong, it will keep repeating until it appears again.</p>
                    </div>
                  </div>
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-primary">Long-term Memory Enhancement</h5>
                      <p class="text-muted">As time passes, the interval between problems appearing again gradually increases, naturally helping to convert to long-term memory.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 2. Interview-style Learning Support -->
        <div class="row mb-5">
          <div class="col-lg-8 mx-auto">
            <div class="card shadow-sm">
              <div class="card-body p-4">
                <div class="d-flex align-items-center mb-3">
                  <div class="feature-icon bg-success text-white rounded-circle d-flex align-items-center justify-content-center me-3" style="width: 60px; height: 60px;">
                    <i class="fas fa-comments fa-lg"></i>
                  </div>
                  <h2 class="card-title mb-0">Interview-style Learning Support</h2>
                </div>
                <p class="card-text mb-4">Simulate real technical interview environments to develop your ability to explain verbally. Provides an interactive learning experience using voice recognition technology.</p>
                
                <div class="row">
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-success">Voice Interview Mode</h5>
                      <p class="text-muted">You can read problems and practice explaining answers verbally. Provides an experience similar to real interview situations.</p>
                    </div>
                  </div>
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-success">Follow-up Question Practice</h5>
                      <p class="text-muted">After answering, you can receive follow-up questions to practice more in-depth explanations. Develops the ability to think from an interviewer's perspective.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 3. Personalized Error Management -->
        <div class="row mb-5">
          <div class="col-lg-8 mx-auto">
            <div class="card shadow-sm">
              <div class="card-body p-4">
                <div class="d-flex align-items-center mb-3">
                  <div class="feature-icon bg-warning text-white rounded-circle d-flex align-items-center justify-content-center me-3" style="width: 60px; height: 60px;">
                    <i class="fas fa-envelope fa-lg"></i>
                  </div>
                  <h2 class="card-title mb-0">Personalized Error Management</h2>
                </div>
                <p class="card-text mb-4">Automatically collects incorrect problems and sends them regularly via email so you can review them anytime, anywhere. Naturally builds learning habits.</p>
                
                <div class="row">
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-warning">Automatic Error Collection</h5>
                      <p class="text-muted">Incorrect problems are automatically added to your error notebook, allowing systematic management without additional work.</p>
                    </div>
                  </div>
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-warning">Email Review</h5>
                      <p class="text-muted">Receive error problems via email at your set intervals, allowing you to naturally review them in your daily life.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 4. Maximize Learning Effectiveness -->
        <div class="row mb-5 mb-md-0">
          <div class="col-lg-8 mx-auto">
            <div class="card shadow-sm">
              <div class="card-body p-4">
                <div class="d-flex align-items-center mb-3">
                  <div class="feature-icon bg-info text-white rounded-circle d-flex align-items-center justify-content-center me-3" style="width: 60px; height: 60px;">
                    <i class="fas fa-chart-line fa-lg"></i>
                  </div>
                  <h2 class="card-title mb-0">Maximize Learning Effectiveness</h2>
                </div>
                <p class="card-text mb-4">Three core features work together organically to create optimal learning effectiveness.</p>
                
                <div class="row">
                  <div class="col-md-4 mb-3">
                    <div class="feature-item text-center">
                      <div class="feature-icon-small bg-primary text-white rounded-circle d-inline-flex align-items-center justify-content-center mb-2" style="width: 40px; height: 40px;">
                        <i class="fas fa-redo"></i>
                      </div>
                      <h6 class="text-primary">Drain System</h6>
                      <p class="text-muted small">Automatic error collection and repetitive learning</p>
                    </div>
                  </div>
                  <div class="col-md-4 mb-3">
                    <div class="feature-item text-center">
                      <div class="feature-icon-small bg-success text-white rounded-circle d-inline-flex align-items-center justify-content-center mb-2" style="width: 40px; height: 40px;">
                        <i class="fas fa-comments"></i>
                      </div>
                      <h6 class="text-success">Voice Interview</h6>
                      <p class="text-muted small">Real interview environment simulation</p>
                    </div>
                  </div>
                  <div class="col-md-4 mb-3">
                    <div class="feature-item text-center">
                      <div class="feature-icon-small bg-warning text-white rounded-circle d-inline-flex align-items-center justify-content-center mb-2" style="width: 40px; height: 40px;">
                        <i class="fas fa-envelope"></i>
                      </div>
                      <h6 class="text-warning">Email Review</h6>
                      <p class="text-muted small">Regular error problem delivery</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- CTA Section - Only shown to non-authenticated users -->
        <div v-if="!isAuthenticated" class="row mb-0">
          <div class="col-lg-8 mx-auto text-center">
            <div class="card bg-light">
              <div class="card-body p-5">
                <h3 class="card-title mb-4">Get Started Now</h3>
                <p class="card-text mb-4">Start more efficient learning with DrillQuiz. Sign up for free and experience all features.</p>
                <div class="d-flex justify-content-center gap-3 flex-wrap">
                  <router-link to="/register" class="btn btn-primary btn-lg">
                    <i class="fas fa-user-plus me-md-2"></i><span class="d-none d-md-inline">Sign Up</span>
                  </router-link>
                  <router-link to="/login" class="btn btn-outline-primary btn-lg">
                    <i class="fas fa-sign-in-alt me-md-2"></i><span class="d-none d-md-inline">Login</span>
                  </router-link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import authService from '@/services/authService'

export default {
  name: 'ServiceIntroductionEn',
  computed: {
    isAuthenticated() {
      return authService.isAuthenticatedSync()
    }
  },
  methods: {
    goBack() {
      if (window.history.length > 1) {
        this.$router.go(-1)
      } else {
        this.$router.push('/register')
      }
    }
  },
  metaInfo: {
    title: 'Service Introduction - DrillQuiz',
    meta: [
      { 
        name: 'description', 
        content: 'Discover DrillQuiz\'s innovative learning features. Maximize your learning effectiveness through repetitive learning, interview-style learning, and personalized error management.' 
      },
      { 
        name: 'keywords', 
        content: 'DrillQuiz, service introduction, repetitive learning, interview learning, error management, learning effectiveness' 
      }
    ]
  }
}
</script>

<style scoped>
.service-introduction {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding-bottom: 0;
}

.service-introduction .container > .row:last-child {
  margin-bottom: 0 !important;
}

.jumbotron {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border-radius: 0;
}

.feature-icon {
  font-size: 1.5rem;
}

.feature-icon-small {
  font-size: 1rem;
}

.card {
  border: none;
  border-radius: 15px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 25px rgba(0,0,0,0.1) !important;
}

.feature-item {
  padding: 1rem 0;
}

.btn {
  border-radius: 25px;
  padding: 12px 30px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0,0,0,0.2);
}

@media (max-width: 768px) {
  .jumbotron {
    padding: 3rem 1rem !important;
  }
  
  .display-4 {
    font-size: 2rem;
  }
  
  .lead {
    font-size: 1rem;
  }
  
  .card-body {
    padding: 1.5rem !important;
  }
  
  .feature-icon {
    width: 50px !important;
    height: 50px !important;
    font-size: 1.2rem;
  }
  
  .btn {
    padding: 10px 20px;
    font-size: 0.9rem;
  }
}
</style>

