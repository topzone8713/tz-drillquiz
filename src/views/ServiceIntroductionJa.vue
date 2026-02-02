<template>
  <div class="service-introduction">
    <div class="container-fluid">
      <!-- ヘッダーセクション -->
      <div class="jumbotron bg-primary text-white text-center py-5 mb-5">
        <div class="container">
          <h1 class="display-4 mb-4">サービス紹介</h1>
          <p class="lead">効率的な学習のための革新的なプラットフォーム</p>
        </div>
      </div>

      <!-- メインコンテンツ -->
      <div class="container">
        <div class="mb-3">
          <button @click="goBack" class="btn btn-outline-secondary">
            <i class="fas fa-arrow-left"></i> 戻る
          </button>
        </div>
        <!-- 1. 反復学習の新しい方法 -->
        <div class="row mb-5">
          <div class="col-lg-8 mx-auto">
            <div class="card shadow-sm">
              <div class="card-body p-4">
                <div class="d-flex align-items-center mb-3">
                  <div class="feature-icon bg-primary text-white rounded-circle d-flex align-items-center justify-content-center me-3" style="width: 60px; height: 60px;">
                    <i class="fas fa-redo fa-lg"></i>
                  </div>
                  <h2 class="card-title mb-0">反復学習の新しい方法</h2>
                </div>
                <p class="card-text mb-4">DrillQuizは、忘却曲線理論に基づいたスマートな反復学習システムを提供します。単純な反復ではなく、科学的に設計された学習パターンで長期記憶を強化します。</p>
                
                <div class="row">
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-primary">ドレインシステム</h5>
                      <p class="text-muted">間違えた問題を自動的に収集し、集中的に反復学習できるようにします。一度間違えた問題は、再び現れるまで繰り返し出題されます。</p>
                    </div>
                  </div>
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-primary">長期記憶の強化</h5>
                      <p class="text-muted">時間が経つにつれて問題が再び出題される間隔を延ばしていき、自然に長期記憶へと変換されるようにします。</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 2. インタビュー形式の学習サポート -->
        <div class="row mb-5">
          <div class="col-lg-8 mx-auto">
            <div class="card shadow-sm">
              <div class="card-body p-4">
                <div class="d-flex align-items-center mb-3">
                  <div class="feature-icon bg-success text-white rounded-circle d-flex align-items-center justify-content-center me-3" style="width: 60px; height: 60px;">
                    <i class="fas fa-comments fa-lg"></i>
                  </div>
                  <h2 class="card-title mb-0">インタビュー形式の学習サポート</h2>
                </div>
                <p class="card-text mb-4">実際の技術面接環境をシミュレートし、言葉で説明する能力を身につけることができます。音声認識技術を活用したインタラクティブな学習体験を提供します。</p>
                
                <div class="row">
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-success">音声インタビューモード</h5>
                      <p class="text-muted">問題を読み、音声で答えを説明する練習ができます。実際の面接状況と同様の体験を提供します。</p>
                    </div>
                  </div>
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-success">追加質問の練習</h5>
                      <p class="text-muted">回答後に追加の質問を受け、より深い説明を練習できます。面接官の視点から考える能力を養います。</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 3. 個人化された誤答管理 -->
        <div class="row mb-5">
          <div class="col-lg-8 mx-auto">
            <div class="card shadow-sm">
              <div class="card-body p-4">
                <div class="d-flex align-items-center mb-3">
                  <div class="feature-icon bg-warning text-white rounded-circle d-flex align-items-center justify-content-center me-3" style="width: 60px; height: 60px;">
                    <i class="fas fa-envelope fa-lg"></i>
                  </div>
                  <h2 class="card-title mb-0">個人化された誤答管理</h2>
                </div>
                <p class="card-text mb-4">間違えた問題を自動的に収集し、定期的にメールで送信して、いつでもどこでも復習できるようにします。学習習慣を自然に作り上げます。</p>
                
                <div class="row">
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-warning">自動誤答収集</h5>
                      <p class="text-muted">間違えた問題が自動的に誤答ノートに追加され、追加の作業なしで体系的に管理されます。</p>
                    </div>
                  </div>
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-warning">メール復習</h5>
                      <p class="text-muted">設定した周期ごとに誤答問題をメールで受け取り、日常生活の中で自然に復習できます。</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 4. 学習効果の最大化 -->
        <div class="row mb-5 mb-md-0">
          <div class="col-lg-8 mx-auto">
            <div class="card shadow-sm">
              <div class="card-body p-4">
                <div class="d-flex align-items-center mb-3">
                  <div class="feature-icon bg-info text-white rounded-circle d-flex align-items-center justify-content-center me-3" style="width: 60px; height: 60px;">
                    <i class="fas fa-chart-line fa-lg"></i>
                  </div>
                  <h2 class="card-title mb-0">学習効果の最大化</h2>
                </div>
                <p class="card-text mb-4">3つの核心機能が有機的に結合し、最適な学習効果を生み出します。</p>
                
                <div class="row">
                  <div class="col-md-4 mb-3">
                    <div class="feature-item text-center">
                      <div class="feature-icon-small bg-primary text-white rounded-circle d-inline-flex align-items-center justify-content-center mb-2" style="width: 40px; height: 40px;">
                        <i class="fas fa-redo"></i>
                      </div>
                      <h6 class="text-primary">ドレインシステム</h6>
                      <p class="text-muted small">間違えた問題の自動収集と反復学習</p>
                    </div>
                  </div>
                  <div class="col-md-4 mb-3">
                    <div class="feature-item text-center">
                      <div class="feature-icon-small bg-success text-white rounded-circle d-inline-flex align-items-center justify-content-center mb-2" style="width: 40px; height: 40px;">
                        <i class="fas fa-comments"></i>
                      </div>
                      <h6 class="text-success">音声インタビュー</h6>
                      <p class="text-muted small">実際の面接環境のシミュレーション</p>
                    </div>
                  </div>
                  <div class="col-md-4 mb-3">
                    <div class="feature-item text-center">
                      <div class="feature-icon-small bg-warning text-white rounded-circle d-inline-flex align-items-center justify-content-center mb-2" style="width: 40px; height: 40px;">
                        <i class="fas fa-envelope"></i>
                      </div>
                      <h6 class="text-warning">メール復習</h6>
                      <p class="text-muted small">定期的な誤答問題の配信</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- CTAセクション - ログインしていないユーザーのみ表示 -->
        <div v-if="!isAuthenticated" class="row mb-0">
          <div class="col-lg-8 mx-auto text-center">
            <div class="card bg-light">
              <div class="card-body p-5">
                <h3 class="card-title mb-4">今すぐ始めましょう</h3>
                <p class="card-text mb-4">DrillQuizでより効率的な学習を始めましょう。無料で登録し、すべての機能を体験できます。</p>
                <div class="d-flex justify-content-center gap-3 flex-wrap">
                  <router-link to="/register" class="btn btn-primary btn-lg">
                    <i class="fas fa-user-plus me-md-2"></i><span class="d-none d-md-inline">会員登録</span>
                  </router-link>
                  <router-link to="/login" class="btn btn-outline-primary btn-lg">
                    <i class="fas fa-sign-in-alt me-md-2"></i><span class="d-none d-md-inline">ログイン</span>
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
  name: 'ServiceIntroductionJa',
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
    title: 'サービス紹介 - DrillQuiz',
    meta: [
      { 
        name: 'description', 
        content: 'DrillQuizの革新的な学習機能をご紹介します。反復学習、インタビュー形式の学習、個人化された誤答管理を通じて学習効果を最大化しましょう。' 
      },
      { 
        name: 'keywords', 
        content: 'DrillQuiz, サービス紹介, 反復学習, インタビュー形式の学習, 誤答管理, 学習効果' 
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





