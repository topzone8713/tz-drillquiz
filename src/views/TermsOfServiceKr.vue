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
          <div class="card-header bg-success text-white">
            <h1 class="h3 mb-0">이용약관</h1>
          </div>
          <div class="card-body">
            <div class="mb-4">
              <p class="text-muted">최종 업데이트: 2025년 8월</p>
            </div>

            <section class="mb-4">
              <h2 class="h4 text-success">1. 약관의 수락</h2>
              <p>DrillQuiz("서비스")에 접근하고 사용함으로써, 귀하는 본 약관의 조건과 규정에 동의하고 구속됨에 동의합니다. 위 사항을 준수하지 않으려면 이 서비스를 사용하지 마십시오.</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">2. 서비스 설명</h2>
              <p>DrillQuiz는 다음을 제공하는 온라인 학습 플랫폼입니다:</p>
              <ul>
                <li>대화형 코딩 퀴즈 및 연습 문제</li>
                <li>학습 자료 및 학습 리소스</li>
                <li>진행 상황 추적 및 성능 분석</li>
                <li>협력 학습을 위한 커뮤니티 기능</li>
                <li>개인화된 학습 추천</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">3. 사용자 계정</h2>
              <p>서비스의 특정 기능에 액세스하려면 계정을 만들어야 합니다. 귀하는 다음에 동의합니다:</p>
              <ul>
                <li>정확하고 완전한 정보 제공</li>
                <li>계정 자격 증명의 보안 유지</li>
                <li>귀하의 계정 하에서의 모든 활동에 대한 책임 수락</li>
                <li>무단 사용에 대해 즉시 알림</li>
                <li>계정을 만들려면 최소 13세 이상이어야 함</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">4. 허용 가능한 사용</h2>
              <p>귀하는 법적 목적으로만 서비스를 사용하고 본 약관에 따라 사용하는 것에 동의합니다. 귀하는 다음을 하지 않기로 동의합니다:</p>
              <ul>
                <li>불법적이거나 무단 목적으로 서비스 사용</li>
                <li>시스템에 무단 액세스 시도</li>
                <li>서비스 방해 또는 중단</li>
                <li>다른 사람과 계정 자격 증명 공유</li>
                <li>서비스에 액세스하기 위해 자동화된 도구 사용</li>
                <li>적용 가능한 법률 또는 규정 위반</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">5. 지적 재산권</h2>
              <p>서비스와 그 원본 콘텐츠, 기능 및 기능은 DrillQuiz가 소유하며 국제 저작권, 상표, 특허, 영업 비밀 및 기타 지적 재산권 법률로 보호됩니다.</p>
              <p>귀하는 생성한 콘텐츠의 소유권을 유지하지만, 서비스와 관련하여 사용, 수정 및 표시할 수 있는 라이선스를 부여합니다.</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">6. 사용자 콘텐츠</h2>
              <p>귀하는 서비스에 제출, 게시 또는 표시하는 모든 콘텐츠에 대해 책임이 있습니다. 귀하는 다음 콘텐츠를 제출하지 않기로 동의합니다:</p>
              <ul>
                <li>불법적이거나 유해하거나 위협적이거나 남용적인 콘텐츠</li>
                <li>지적 재산권을 침해하는 콘텐츠</li>
                <li>맬웨어 또는 유해한 코드를 포함하는 콘텐츠</li>
                <li>스팸 또는 원치 않는 상업적 콘텐츠</li>
                <li>개인정보 보호 또는 기밀 유지 위반</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">7. 개인정보 보호 및 데이터 보호</h2>
              <p>귀하의 개인정보 보호는 우리에게 중요합니다. 개인정보의 수집 및 사용은 본 약관에 참조로 통합된 개인정보 보호정책에 의해 규제됩니다.</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">8. 서비스 가용성</h2>
              <p>우리는 서비스의 높은 가용성을 유지하기 위해 노력하지만 중단 없는 액세스를 보장하지는 않습니다. 서비스는 다음으로 인해 일시적으로 사용할 수 없을 수 있습니다:</p>
              <ul>
                <li>예정된 유지보수</li>
                <li>기술적 문제 또는 시스템 업데이트</li>
                <li>불가항력 사건</li>
                <li>제3자 서비스 중단</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">9. 책임의 제한</h2>
              <p>법률이 허용하는 최대 범위까지, DrillQuiz는 이익, 데이터 또는 사용의 손실을 포함하되 이에 국한되지 않는 간접적, 부수적, 특별, 결과적 또는 징벌적 손해에 대해 책임을 지지 않습니다.</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">10. 면책 조항</h2>
              <p>서비스는 어떠한 종류의 보증 없이 "있는 그대로" 및 "사용 가능한 대로" 제공됩니다. 우리는 다음을 보장하지 않습니다:</p>
              <ul>
                <li>콘텐츠의 정확성 또는 완전성</li>
                <li>중단 없거나 오류 없는 서비스</li>
                <li>특정 학습 결과 또는 결과</li>
                <li>모든 장치 또는 브라우저와의 호환성</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">11. 종료</h2>
              <p>우리는 사유 여부와 관계없이, 통지 여부와 관계없이 언제든지 귀하의 계정과 서비스 액세스를 종료하거나 일시 중지할 수 있습니다. 귀하는 또한 언제든지 문의하여 계정을 종료할 수 있습니다.</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">12. 약관 변경</h2>
              <p>우리는 언제든지 본 약관을 수정할 권리를 보유합니다. 우리는 웹사이트에 새로운 약관을 게시하고 "최종 업데이트" 날짜를 업데이트하여 중요한 변경 사항을 사용자에게 알릴 것입니다.</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">13. 준거법</h2>
              <p>본 약관은 DrillQuiz가 운영하는 관할권의 법률에 따라 규율되고 해석되며, 법률 충돌 원칙과 무관합니다.</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">14. 연락처 정보</h2>
              <p>본 이용약관에 대한 질문이 있으시면 다음으로 문의하십시오:</p>
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
  name: 'TermsOfServiceKr',
  metaInfo: {
    title: '이용약관 - DrillQuiz',
    meta: [
      { name: 'description', content: 'DrillQuiz 이용약관 - 플랫폼 사용에 대한 약관 및 조건을 읽어보세요.' }
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

