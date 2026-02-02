<template>
  <div class="container mt-4 mb-3">
    <div class="row justify-content-center">
      <div class="col-lg-8">
        <div class="mb-3">
          <button @click="goBack" class="btn btn-outline-secondary">
            <i class="fas fa-arrow-left"></i> 이전 페이지
          </button>
        </div>
        <div class="card shadow">
          <div class="card-header bg-primary text-white">
            <h1 class="h3 mb-0">개인정보 보호정책</h1>
          </div>
          <div class="card-body">
            <div class="mb-4">
              <p class="text-muted">최종 업데이트: 2025년 8월</p>
            </div>

            <section class="mb-4">
              <h2 class="h4 text-primary">1. 수집하는 정보</h2>
              <p>DrillQuiz는 귀하가 계정을 만들거나, 퀴즈를 완료하거나, 지원을 위해 문의할 때와 같이 직접 제공하는 정보를 수집합니다. 여기에는 다음이 포함될 수 있습니다:</p>
              <ul>
                <li>계정 정보(사용자 이름, 이메일 주소)</li>
                <li>학습 진행 상황 및 퀴즈 결과</li>
                <li>통신 기본 설정</li>
                <li>기기 및 사용에 대한 기술 정보</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">2. 정보 사용 방법</h2>
              <p>우리는 수집한 정보를 다음 목적으로 사용합니다:</p>
              <ul>
                <li>서비스 제공, 유지 및 개선</li>
                <li>학습 진행 상황 추적 및 개인화된 추천 제공</li>
                <li>서비스에 대한 중요한 업데이트 전송</li>
                <li>질문에 답변하고 고객 지원 제공</li>
                <li>플랫폼의 보안 및 무결성 보장</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">3. 정보 공유</h2>
              <p>우리는 귀하의 동의 없이 다음 상황을 제외하고는 귀하의 개인정보를 제3자에게 판매, 거래 또는 양도하지 않습니다:</p>
              <ul>
                <li>귀하의 명시적 허가</li>
                <li>법적 의무 준수</li>
                <li>우리의 권리와 안전 보호</li>
                <li>플랫폼 운영을 지원하는 서비스 제공업체(엄격한 기밀 유지 계약 하에)</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">4. 데이터 보안</h2>
              <p>우리는 무단 액세스, 변경, 공개 또는 파괴로부터 귀하의 개인정보를 보호하기 위해 적절한 보안 조치를 구현합니다. 이러한 조치에는 다음이 포함됩니다:</p>
              <ul>
                <li>민감한 데이터 암호화</li>
                <li>정기적인 보안 평가</li>
                <li>액세스 제어 및 인증</li>
                <li>안전한 데이터 전송 프로토콜</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">5. 귀하의 권리</h2>
              <p>귀하는 다음 권리를 가집니다:</p>
              <ul>
                <li>개인정보에 액세스하고 검토</li>
                <li>부정확한 정보 업데이트 또는 수정</li>
                <li>계정 및 관련 데이터 삭제 요청</li>
                <li>특정 통신 거부</li>
                <li>휴대 가능한 형식으로 데이터 내보내기</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">6. 쿠키 및 추적</h2>
              <p>우리는 귀하의 경험을 향상시키고, 사용 패턴을 분석하며, 개인화된 콘텐츠를 제공하기 위해 쿠키 및 유사한 기술을 사용합니다. 브라우저 기본 설정을 통해 쿠키 설정을 제어할 수 있습니다.</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">7. 아동의 개인정보 보호</h2>
              <p>우리의 서비스는 13세 미만의 아동을 대상으로 하지 않습니다. 우리는 13세 미만의 아동으로부터 고의로 개인정보를 수집하지 않습니다. 그러한 정보를 수집했다고 생각되면 즉시 문의하십시오.</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">8. 국제 데이터 전송</h2>
              <p>귀하의 정보는 귀하의 국가 이외의 국가로 전송되고 처리될 수 있습니다. 우리는 적용 가능한 법률에 따라 귀하의 데이터를 보호하기 위해 적절한 보호 조치가 마련되어 있음을 보장합니다.</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">9. 정책 변경</h2>
              <p>우리는 때때로 이 개인정보 보호정책을 업데이트할 수 있습니다. 우리는 웹사이트에 새로운 정책을 게시하고 "최종 업데이트" 날짜를 업데이트하여 중요한 변경 사항을 알릴 것입니다.</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">10. 문의하기</h2>
              <p>이 개인정보 보호정책이나 데이터 관행에 대한 질문이 있으시면 다음으로 문의하십시오:</p>
              <div class="bg-light p-3 rounded">
                <p class="mb-0"><strong>이메일:</strong> doohee323@gmail.com</p>
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
  name: 'PrivacyPolicyKr',
  metaInfo: {
    title: '개인정보 보호정책 - DrillQuiz',
    meta: [
      { name: 'description', content: 'DrillQuiz 개인정보 보호정책 - 개인정보를 수집, 사용 및 보호하는 방법을 알아보세요.' }
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

