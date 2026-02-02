<template>
  <div class="container mt-4 mb-3">
    <div class="row justify-content-center">
      <div class="col-lg-8">
        <div class="card shadow">
          <div class="card-header bg-success text-white">
            <h1 class="h3 mb-0">Terms of Service</h1>
          </div>
          <div class="card-body">
            <div class="mb-4">
              <p class="text-muted">Last updated: August 2025</p>
            </div>

            <section class="mb-4">
              <h2 class="h4 text-success">1. Acceptance of Terms</h2>
              <p>By accessing and using DrillQuiz ("Service"), you accept and agree to be bound by the terms and provision of this agreement. If you do not agree to abide by the above, please do not use this service.</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">2. Description of Service</h2>
              <p>DrillQuiz is an online learning platform that provides:</p>
              <ul>
                <li>Interactive coding quizzes and practice problems</li>
                <li>Study materials and learning resources</li>
                <li>Progress tracking and performance analytics</li>
                <li>Community features for collaborative learning</li>
                <li>Personalized study recommendations</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">3. User Accounts</h2>
              <p>To access certain features of the Service, you must create an account. You agree to:</p>
              <ul>
                <li>Provide accurate and complete information</li>
                <li>Maintain the security of your account credentials</li>
                <li>Accept responsibility for all activities under your account</li>
                <li>Notify us immediately of any unauthorized use</li>
                <li>Be at least 13 years old to create an account</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">4. Acceptable Use</h2>
              <p>You agree to use the Service only for lawful purposes and in accordance with these Terms. You agree not to:</p>
              <ul>
                <li>Use the Service for any illegal or unauthorized purpose</li>
                <li>Attempt to gain unauthorized access to our systems</li>
                <li>Interfere with or disrupt the Service</li>
                <li>Share your account credentials with others</li>
                <li>Use automated tools to access the Service</li>
                <li>Violate any applicable laws or regulations</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">5. Intellectual Property</h2>
              <p>The Service and its original content, features, and functionality are owned by DrillQuiz and are protected by international copyright, trademark, patent, trade secret, and other intellectual property laws.</p>
              <p>You retain ownership of content you create, but grant us a license to use, modify, and display it in connection with the Service.</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">6. User Content</h2>
              <p>You are responsible for any content you submit, post, or display on the Service. You agree not to submit content that:</p>
              <ul>
                <li>Is illegal, harmful, threatening, or abusive</li>
                <li>Infringes on intellectual property rights</li>
                <li>Contains malware or harmful code</li>
                <li>Is spam or unsolicited commercial content</li>
                <li>Violates privacy or confidentiality</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">7. Privacy and Data Protection</h2>
              <p>Your privacy is important to us. Our collection and use of personal information is governed by our Privacy Policy, which is incorporated into these Terms by reference.</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">8. Service Availability</h2>
              <p>We strive to maintain high availability of the Service, but we do not guarantee uninterrupted access. The Service may be temporarily unavailable due to:</p>
              <ul>
                <li>Scheduled maintenance</li>
                <li>Technical issues or system updates</li>
                <li>Force majeure events</li>
                <li>Third-party service disruptions</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">9. Limitation of Liability</h2>
              <p>To the maximum extent permitted by law, DrillQuiz shall not be liable for any indirect, incidental, special, consequential, or punitive damages, including but not limited to loss of profits, data, or use.</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">10. Disclaimers</h2>
              <p>The Service is provided "as is" and "as available" without warranties of any kind. We do not guarantee:</p>
              <ul>
                <li>The accuracy or completeness of content</li>
                <li>Uninterrupted or error-free service</li>
                <li>Specific learning outcomes or results</li>
                <li>Compatibility with all devices or browsers</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">11. Termination</h2>
              <p>We may terminate or suspend your account and access to the Service at any time, with or without cause, with or without notice. You may also terminate your account at any time by contacting us.</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">12. Changes to Terms</h2>
              <p>We reserve the right to modify these Terms at any time. We will notify users of material changes by posting the new Terms on our website and updating the "Last updated" date.</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">13. Governing Law</h2>
              <p>These Terms shall be governed by and construed in accordance with the laws of the jurisdiction in which DrillQuiz operates, without regard to conflict of law principles.</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">14. Contact Information</h2>
              <p>If you have any questions about these Terms of Service, please contact us at:</p>
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
  name: 'TermsOfService',
  metaInfo: {
    title: 'Terms of Service - DrillQuiz',
    meta: [
      { name: 'description', content: 'DrillQuiz Terms of Service - Read our terms and conditions for using the platform.' }
    ]
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
