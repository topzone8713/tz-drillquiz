<template>
  <div class="container mt-4 mb-3">
    <div class="row justify-content-center">
      <div class="col-lg-8">
        <div class="mb-3">
          <button @click="goBack" class="btn btn-outline-secondary">
            <i class="fas fa-arrow-left"></i> 戻る
          </button>
        </div>
        <div class="card shadow">
          <div class="card-header bg-primary text-white">
            <h1 class="h3 mb-0">プライバシーポリシー</h1>
          </div>
          <div class="card-body">
            <div class="mb-4">
              <p class="text-muted">最終更新日: 2025年8月</p>
            </div>

            <section class="mb-4">
              <h2 class="h4 text-primary">1. 収集する情報</h2>
              <p>DrillQuizは、アカウントの作成、クイズの完了、サポートへのお問い合わせなど、お客様が直接提供する情報を収集します。これには以下が含まれる場合があります：</p>
              <ul>
                <li>アカウント情報（ユーザー名、メールアドレス）</li>
                <li>学習の進行状況およびクイズの結果</li>
                <li>通信の基本設定</li>
                <li>デバイスおよび使用に関する技術情報</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">2. 情報の使用方法</h2>
              <p>収集した情報は、以下の目的で使用します：</p>
              <ul>
                <li>サービスの提供、維持、改善</li>
                <li>学習の進行状況の追跡および個人化された推奨事項の提供</li>
                <li>サービスに関する重要な更新の送信</li>
                <li>ご質問への回答およびカスタマーサポートの提供</li>
                <li>プラットフォームのセキュリティおよび整合性の確保</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">3. 情報の共有</h2>
              <p>お客様の同意なしに、以下の状況を除き、お客様の個人情報を第三者に販売、取引、または譲渡することはありません：</p>
              <ul>
                <li>お客様の明示的な許可</li>
                <li>法的義務の遵守</li>
                <li>当社の権利と安全性の保護</li>
                <li>プラットフォームの運営を支援するサービスプロバイダー（厳格な機密保持契約の下で）</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">4. データセキュリティ</h2>
              <p>不正アクセス、変更、開示、または破壊からお客様の個人情報を保護するため、適切なセキュリティ対策を実装しています。これらの対策には以下が含まれます：</p>
              <ul>
                <li>機密データの暗号化</li>
                <li>定期的なセキュリティ評価</li>
                <li>アクセス制御および認証</li>
                <li>安全なデータ伝送プロトコル</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">5. お客様の権利</h2>
              <p>お客様には以下の権利があります：</p>
              <ul>
                <li>個人情報へのアクセスおよび閲覧</li>
                <li>不正確な情報の更新または修正</li>
                <li>アカウントおよび関連データの削除要求</li>
                <li>特定の通信の拒否</li>
                <li>ポータブル形式でのデータのエクスポート</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">6. クッキーおよびトラッキング</h2>
              <p>お客様の体験を向上させ、使用パターンを分析し、個人化されたコンテンツを提供するために、クッキーおよび類似のテクノロジーを使用しています。ブラウザの設定を通じてクッキー設定を制御できます。</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">7. 児童のプライバシー</h2>
              <p>当社のサービスは、13歳未満の児童を対象としていません。13歳未満の児童から意図的に個人情報を収集することはありません。そのような情報を収集したと思われる場合は、すぐにお問い合わせください。</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">8. 国際的なデータ転送</h2>
              <p>お客様の情報は、お客様の国以外の国に転送され、処理される場合があります。適用される法律に従ってお客様のデータを保護するため、適切な保護措置が講じられていることを保証します。</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">9. ポリシーの変更</h2>
              <p>このプライバシーポリシーを随時更新する場合があります。重要な変更については、ウェブサイトに新しいポリシーを投稿し、「最終更新日」を更新してお知らせします。</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">10. お問い合わせ</h2>
              <p>このプライバシーポリシーまたはデータの取り扱いに関するご質問がございましたら、以下までお問い合わせください：</p>
              <div class="bg-light p-3 rounded">
                <p class="mb-0"><strong>メール:</strong> doohee323@gmail.com</p>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PrivacyPolicyJa',
  metaInfo: {
    title: 'プライバシーポリシー - DrillQuiz',
    meta: [
      { name: 'description', content: 'DrillQuizプライバシーポリシー - 個人情報を収集、使用、保護する方法をご確認ください。' }
    ]
  },
  methods: {
    goBack() {
      if (window.history.length > 1) {
        this.$router.go(-1)
      } else {
        this.$router.push('/register')
      }
    }
  }
}
</script>

<style scoped>
.card {
  border: none;
  border-radius: 12px;
}

.card-header {
  border-radius: 12px 12px 0 0 !important;
  border-bottom: none;
}

h2 {
  color: #495057;
  margin-top: 1.5rem;
}

ul {
  padding-left: 1.2rem;
}

li {
  margin-bottom: 0.5rem;
}

.bg-light {
  background-color: #f8f9fa !important;
}
</style>





