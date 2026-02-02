<template>
  <div class="container mt-4 mb-3">
    <div class="row justify-content-center">
      <div class="col-lg-8">
        <div class="mb-3">
          <button @click="goBack" class="btn btn-outline-secondary">
            <i class="fas fa-arrow-left"></i> 返回
          </button>
        </div>
        <div class="card shadow">
          <div class="card-header bg-primary text-white">
            <h1 class="h3 mb-0">隐私政策</h1>
          </div>
          <div class="card-body">
            <div class="mb-4">
              <p class="text-muted">最后更新：2025年8月</p>
            </div>

            <section class="mb-4">
              <h2 class="h4 text-primary">1. 我们收集的信息</h2>
              <p>DrillQuiz收集您直接提供给我们的信息，例如当您创建账户、完成测验或联系我们寻求支持时。这可能包括：</p>
              <ul>
                <li>账户信息（用户名、电子邮件地址）</li>
                <li>学习进度和测验结果</li>
                <li>通信偏好</li>
                <li>关于您的设备和使用情况的技术信息</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">2. 我们如何使用您的信息</h2>
              <p>我们使用收集的信息来：</p>
              <ul>
                <li>提供、维护和改进我们的服务</li>
                <li>跟踪您的学习进度并提供个性化推荐</li>
                <li>向您发送有关我们服务的重要更新</li>
                <li>回答您的问题并提供客户支持</li>
                <li>确保我们平台的安全性和完整性</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">3. 信息共享</h2>
              <p>未经您同意，我们不会向第三方出售、交易或以其他方式转让您的个人信息，但以下情况除外：</p>
              <ul>
                <li>在您明确许可的情况下</li>
                <li>遵守法律义务</li>
                <li>保护我们的权利和安全</li>
                <li>与协助我们运营平台的服务提供商（在严格的保密协议下）</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">4. 数据安全</h2>
              <p>我们实施适当的安全措施，以保护您的个人信息免受未经授权的访问、更改、披露或破坏。这些措施包括：</p>
              <ul>
                <li>敏感数据加密</li>
                <li>定期安全评估</li>
                <li>访问控制和身份验证</li>
                <li>安全的数据传输协议</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">5. 您的权利</h2>
              <p>您有权：</p>
              <ul>
                <li>访问和查看您的个人信息</li>
                <li>更新或更正不准确的信息</li>
                <li>请求删除您的账户和相关数据</li>
                <li>选择退出某些通信</li>
                <li>以可移植格式导出您的数据</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">6. Cookie和跟踪</h2>
              <p>我们使用Cookie和类似技术来增强您的体验、分析使用模式并提供个性化内容。您可以通过浏览器首选项控制Cookie设置。</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">7. 儿童隐私</h2>
              <p>我们的服务不适用于13岁以下的儿童。我们不会故意收集13岁以下儿童的个人信息。如果您认为我们收集了此类信息，请立即联系我们。</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">8. 国际数据传输</h2>
              <p>您的信息可能会被传输到您所在国家/地区以外的国家/地区进行处理。我们确保根据适用法律采取适当的保护措施来保护您的数据。</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">9. 本政策的变更</h2>
              <p>我们可能会不时更新此隐私政策。我们将通过在网站上发布新政策并更新"最后更新"日期来通知您任何重大变更。</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">10. 联系我们</h2>
              <p>如果您对此隐私政策或我们的数据做法有任何疑问，请通过以下方式联系我们：</p>
              <div class="bg-light p-3 rounded">
                <p class="mb-0"><strong>电子邮件：</strong> doohee323@gmail.com</p>
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
  name: 'PrivacyPolicyZh',
  metaInfo: {
    title: '隐私政策 - DrillQuiz',
    meta: [
      { name: 'description', content: 'DrillQuiz隐私政策 - 了解我们如何收集、使用和保护您的个人信息。' }
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

