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
          <div class="card-header bg-success text-white">
            <h1 class="h3 mb-0">利用規約</h1>
          </div>
          <div class="card-body">
            <div class="mb-4">
              <p class="text-muted">最終更新日: 2025年8月</p>
            </div>

            <section class="mb-4">
              <h2 class="h4 text-success">1. 規約の承認</h2>
              <p>DrillQuiz（「サービス」）にアクセスし、使用することにより、お客様は本規約の条件および規定に拘束されることに同意したものとみなされます。上記を遵守することに同意しない場合は、このサービスを使用しないでください。</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">2. サービスの説明</h2>
              <p>DrillQuizは、以下を提供するオンライン学習プラットフォームです：</p>
              <ul>
                <li>インタラクティブなコーディングクイズおよび練習問題</li>
                <li>学習資料および学習リソース</li>
                <li>進行状況の追跡およびパフォーマンス分析</li>
                <li>協力学習のためのコミュニティ機能</li>
                <li>個人化された学習推奨事項</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">3. ユーザーアカウント</h2>
              <p>サービスの特定の機能にアクセスするには、アカウントを作成する必要があります。お客様は以下に同意するものとします：</p>
              <ul>
                <li>正確かつ完全な情報の提供</li>
                <li>アカウント認証情報のセキュリティの維持</li>
                <li>お客様のアカウント下でのすべての活動に対する責任の受諾</li>
                <li>不正使用があった場合の即座の通知</li>
                <li>アカウント作成には最低13歳以上であること</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">4. 許容される使用</h2>
              <p>お客様は、合法的な目的でのみサービスを使用し、これらの規約に従って使用することに同意するものとします。お客様は以下を行わないことに同意するものとします：</p>
              <ul>
                <li>違法または不正な目的でのサービスの使用</li>
                <li>当社のシステムへの不正アクセスの試行</li>
                <li>サービスの妨害または中断</li>
                <li>他者とのアカウント認証情報の共有</li>
                <li>サービスへのアクセスのための自動化ツールの使用</li>
                <li>適用される法律または規制の違反</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">5. 知的財産権</h2>
              <p>サービスおよびそのオリジナルコンテンツ、機能、機能性はDrillQuizが所有し、国際的な著作権、商標、特許、営業秘密、およびその他の知的財産法によって保護されています。</p>
              <p>お客様は作成したコンテンツの所有権を保持しますが、サービスに関連して使用、変更、表示するためのライセンスを当社に付与します。</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">6. ユーザーコンテンツ</h2>
              <p>お客様は、サービスに投稿、公開、または表示するすべてのコンテンツに対して責任を負います。お客様は以下のコンテンツを投稿しないことに同意するものとします：</p>
              <ul>
                <li>違法、有害、脅迫的、または乱用的なコンテンツ</li>
                <li>知的財産権を侵害するコンテンツ</li>
                <li>マルウェアまたは有害なコードを含むコンテンツ</li>
                <li>スパムまたは未承諾の商業コンテンツ</li>
                <li>プライバシーまたは機密性に違反するコンテンツ</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">7. プライバシーおよびデータ保護</h2>
              <p>お客様のプライバシーは当社にとって重要です。個人情報の収集および使用は、これらの規約に参照として組み込まれているプライバシーポリシーによって規制されます。</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">8. サービスの可用性</h2>
              <p>当社はサービスの高い可用性を維持するよう努めますが、中断のないアクセスを保証するものではありません。サービスは以下の理由により一時的に利用できない場合があります：</p>
              <ul>
                <li>予定されたメンテナンス</li>
                <li>技術的な問題またはシステム更新</li>
                <li>不可抗力</li>
                <li>第三者サービスの中断</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">9. 責任の制限</h2>
              <p>法律で許可される最大限の範囲で、DrillQuizは、利益、データ、または使用の損失を含むがこれに限定されない、間接的、偶発的、特別、結果的、または懲罰的損害について責任を負いません。</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">10. 免責事項</h2>
              <p>サービスは「現状のまま」および「利用可能な限り」で、いかなる種類の保証もなく提供されます。当社は以下を保証しません：</p>
              <ul>
                <li>コンテンツの正確性または完全性</li>
                <li>中断のない、またはエラーのないサービス</li>
                <li>特定の学習成果または結果</li>
                <li>すべてのデバイスまたはブラウザとの互換性</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">11. 終了</h2>
              <p>当社は、理由の有無に関わらず、通知の有無に関わらず、いつでもお客様のアカウントおよびサービスへのアクセスを終了または停止する権利を留保します。お客様は、いつでもお問い合わせによりアカウントを終了することもできます。</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">12. 規約の変更</h2>
              <p>当社は、いつでもこれらの規約を変更する権利を留保します。重要な変更については、ウェブサイトに新しい規約を投稿し、「最終更新日」を更新してお知らせします。</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">13. 準拠法</h2>
              <p>これらの規約は、DrillQuizが運営する管轄区域の法律に従って管理され、解釈され、法の抵触原則に関係なく適用されます。</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">14. 連絡先情報</h2>
              <p>これらの利用規約に関するご質問がございましたら、以下までお問い合わせください：</p>
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
  name: 'TermsOfServiceJa',
  metaInfo: {
    title: '利用規約 - DrillQuiz',
    meta: [
      { name: 'description', content: 'DrillQuiz利用規約 - プラットフォームの使用に関する規約および条件をお読みください。' }
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





