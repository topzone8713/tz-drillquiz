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
          <div class="card-header bg-success text-white">
            <h1 class="h3 mb-0">服务条款</h1>
          </div>
          <div class="card-body">
            <div class="mb-4">
              <p class="text-muted">最后更新：2025年8月</p>
            </div>

            <section class="mb-4">
              <h2 class="h4 text-success">1. 接受条款</h2>
              <p>通过访问和使用DrillQuiz（"服务"），您接受并同意受本协议的条款和规定约束。如果您不同意遵守上述规定，请不要使用此服务。</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">2. 服务说明</h2>
              <p>DrillQuiz是一个提供以下内容的在线学习平台：</p>
              <ul>
                <li>交互式编程测验和练习题</li>
                <li>学习材料和资源</li>
                <li>进度跟踪和性能分析</li>
                <li>协作学习的社区功能</li>
                <li>个性化学习推荐</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">3. 用户账户</h2>
              <p>要访问服务的某些功能，您必须创建一个账户。您同意：</p>
              <ul>
                <li>提供准确完整的信息</li>
                <li>维护账户凭据的安全性</li>
                <li>接受您账户下所有活动的责任</li>
                <li>立即通知我们任何未经授权的使用</li>
                <li>创建账户时至少年满13岁</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">4. 可接受的使用</h2>
              <p>您同意仅将服务用于合法目的，并按照这些条款使用。您同意不：</p>
              <ul>
                <li>将服务用于任何非法或未经授权的目的</li>
                <li>试图未经授权访问我们的系统</li>
                <li>干扰或中断服务</li>
                <li>与他人共享您的账户凭据</li>
                <li>使用自动化工具访问服务</li>
                <li>违反任何适用的法律或法规</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">5. 知识产权</h2>
              <p>服务及其原始内容、功能和特性归DrillQuiz所有，并受国际版权、商标、专利、商业秘密和其他知识产权法律保护。</p>
              <p>您保留创建内容的所有权，但授予我们在与服务相关的情况下使用、修改和显示它的许可。</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">6. 用户内容</h2>
              <p>您对在服务上提交、发布或显示的任何内容负责。您同意不提交以下内容：</p>
              <ul>
                <li>非法、有害、威胁性或辱骂性内容</li>
                <li>侵犯知识产权的内容</li>
                <li>包含恶意软件或有害代码的内容</li>
                <li>垃圾邮件或未经请求的商业内容</li>
                <li>违反隐私或保密性的内容</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">7. 隐私和数据保护</h2>
              <p>您的隐私对我们很重要。我们收集和使用个人信息受我们的隐私政策管辖，该政策通过引用纳入本条款。</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">8. 服务可用性</h2>
              <p>我们努力保持服务的高可用性，但不保证不间断访问。服务可能因以下原因暂时不可用：</p>
              <ul>
                <li>计划维护</li>
                <li>技术问题或系统更新</li>
                <li>不可抗力事件</li>
                <li>第三方服务中断</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">9. 责任限制</h2>
              <p>在法律允许的最大范围内，DrillQuiz不对任何间接、偶然、特殊、后果性或惩罚性损害承担责任，包括但不限于利润、数据或使用的损失。</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">10. 免责声明</h2>
              <p>服务按"原样"和"可用"提供，不提供任何形式的保证。我们不保证：</p>
              <ul>
                <li>内容的准确性或完整性</li>
                <li>不间断或无错误的服务</li>
                <li>特定的学习成果或结果</li>
                <li>与所有设备或浏览器的兼容性</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">11. 终止</h2>
              <p>我们可以在任何时候，无论是否有原因，无论是否通知，终止或暂停您的账户和服务访问。您也可以随时通过联系我们终止您的账户。</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">12. 条款变更</h2>
              <p>我们保留随时修改这些条款的权利。我们将通过在网站上发布新条款并更新"最后更新"日期来通知用户重大变更。</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">13. 适用法律</h2>
              <p>这些条款应受DrillQuiz运营所在司法管辖区的法律管辖和解释，不考虑法律冲突原则。</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">14. 联系信息</h2>
              <p>如果您对这些服务条款有任何疑问，请通过以下方式联系我们：</p>
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
  name: 'TermsOfServiceZh',
  metaInfo: {
    title: '服务条款 - DrillQuiz',
    meta: [
      { name: 'description', content: 'DrillQuiz服务条款 - 阅读我们使用平台的服务条款和条件。' }
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

