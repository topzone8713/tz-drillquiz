<template>
  <div class="container mt-4 mb-3">
    <div class="row justify-content-center">
      <div class="col-lg-8">
        <div class="mb-3">
          <button @click="goBack" class="btn btn-outline-secondary">
            <i class="fas fa-arrow-left"></i> Back
          </button>
        </div>
        <div class="card shadow">
          <div class="card-header bg-primary text-white">
            <h1 class="h3 mb-0">Privacy Policy</h1>
          </div>
          <div class="card-body">
            <div class="mb-4">
              <p class="text-muted">Last updated: August 2025</p>
            </div>

            <section class="mb-4">
              <h2 class="h4 text-primary">1. Information We Collect</h2>
              <p>DrillQuiz collects information you provide directly to us, such as when you create an account, complete a quiz, or contact us for support. This may include:</p>
              <ul>
                <li>Account information (username, email address)</li>
                <li>Study progress and quiz results</li>
                <li>Communication preferences</li>
                <li>Technical information about your device and usage</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">2. How We Use Your Information</h2>
              <p>We use the information we collect to:</p>
              <ul>
                <li>Provide, maintain, and improve our services</li>
                <li>Track your learning progress and provide personalized recommendations</li>
                <li>Send you important updates about our services</li>
                <li>Respond to your questions and provide customer support</li>
                <li>Ensure the security and integrity of our platform</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">3. Information Sharing</h2>
              <p>We do not sell, trade, or otherwise transfer your personal information to third parties without your consent, except in the following circumstances:</p>
              <ul>
                <li>With your explicit permission</li>
                <li>To comply with legal obligations</li>
                <li>To protect our rights and safety</li>
                <li>With service providers who assist us in operating our platform (under strict confidentiality agreements)</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">4. Data Security</h2>
              <p>We implement appropriate security measures to protect your personal information against unauthorized access, alteration, disclosure, or destruction. These measures include:</p>
              <ul>
                <li>Encryption of sensitive data</li>
                <li>Regular security assessments</li>
                <li>Access controls and authentication</li>
                <li>Secure data transmission protocols</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">5. Your Rights</h2>
              <p>You have the right to:</p>
              <ul>
                <li>Access and review your personal information</li>
                <li>Update or correct inaccurate information</li>
                <li>Request deletion of your account and associated data</li>
                <li>Opt-out of certain communications</li>
                <li>Export your data in a portable format</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">6. Cookies and Tracking</h2>
              <p>We use cookies and similar technologies to enhance your experience, analyze usage patterns, and provide personalized content. You can control cookie settings through your browser preferences.</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">7. Children's Privacy</h2>
              <p>Our services are not intended for children under 13 years of age. We do not knowingly collect personal information from children under 13. If you believe we have collected such information, please contact us immediately.</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">8. International Data Transfers</h2>
              <p>Your information may be transferred to and processed in countries other than your own. We ensure appropriate safeguards are in place to protect your data in accordance with applicable laws.</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">9. Changes to This Policy</h2>
              <p>We may update this Privacy Policy from time to time. We will notify you of any material changes by posting the new policy on our website and updating the "Last updated" date.</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">10. Contact Us</h2>
              <p>If you have any questions about this Privacy Policy or our data practices, please contact us at:</p>
              <div class="bg-light p-3 rounded">
                <p class="mb-0"><strong>Email:</strong> doohee323@gmail.com</p>
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
  name: 'PrivacyPolicyEn',
  metaInfo: {
    title: 'Privacy Policy - DrillQuiz',
    meta: [
      { name: 'description', content: 'DrillQuiz Privacy Policy - Learn how we collect, use, and protect your personal information.' }
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

