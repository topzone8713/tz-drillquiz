<template>
  <div class="container mt-4 mb-3">
    <div class="row justify-content-center">
      <div class="col-lg-8">
        <div class="mb-3">
          <button @click="goBack" class="btn btn-outline-secondary">
            <i class="fas fa-arrow-left"></i> Atrás
          </button>
        </div>
        <div class="card shadow">
          <div class="card-header bg-primary text-white">
            <h1 class="h3 mb-0">Política de Privacidad</h1>
          </div>
          <div class="card-body">
            <div class="mb-4">
              <p class="text-muted">Última actualización: Agosto 2025</p>
            </div>

            <section class="mb-4">
              <h2 class="h4 text-primary">1. Información que Recopilamos</h2>
              <p>DrillQuiz recopila información que usted nos proporciona directamente, como cuando crea una cuenta, completa un cuestionario o nos contacta para obtener soporte. Esto puede incluir:</p>
              <ul>
                <li>Información de la cuenta (nombre de usuario, dirección de correo electrónico)</li>
                <li>Progreso de estudio y resultados de cuestionarios</li>
                <li>Preferencias de comunicación</li>
                <li>Información técnica sobre su dispositivo y uso</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">2. Cómo Usamos Su Información</h2>
              <p>Usamos la información que recopilamos para:</p>
              <ul>
                <li>Proporcionar, mantener y mejorar nuestros servicios</li>
                <li>Seguir su progreso de aprendizaje y proporcionar recomendaciones personalizadas</li>
                <li>Enviarle actualizaciones importantes sobre nuestros servicios</li>
                <li>Responder a sus preguntas y proporcionar soporte al cliente</li>
                <li>Asegurar la seguridad e integridad de nuestra plataforma</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">3. Compartir Información</h2>
              <p>No vendemos, intercambiamos o transferimos su información personal a terceros sin su consentimiento, excepto en las siguientes circunstancias:</p>
              <ul>
                <li>Con su permiso explícito</li>
                <li>Para cumplir con obligaciones legales</li>
                <li>Para proteger nuestros derechos y seguridad</li>
                <li>Con proveedores de servicios que nos ayudan a operar nuestra plataforma (bajo estrictos acuerdos de confidencialidad)</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">4. Seguridad de Datos</h2>
              <p>Implementamos medidas de seguridad apropiadas para proteger su información personal contra acceso no autorizado, alteración, divulgación o destrucción. Estas medidas incluyen:</p>
              <ul>
                <li>Cifrado de datos sensibles</li>
                <li>Evaluaciones de seguridad regulares</li>
                <li>Controles de acceso y autenticación</li>
                <li>Protocolos seguros de transmisión de datos</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">5. Sus Derechos</h2>
              <p>Usted tiene derecho a:</p>
              <ul>
                <li>Acceder y revisar su información personal</li>
                <li>Actualizar o corregir información inexacta</li>
                <li>Solicitar la eliminación de su cuenta y datos asociados</li>
                <li>Optar por no recibir ciertas comunicaciones</li>
                <li>Exportar sus datos en un formato portable</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">6. Cookies y Seguimiento</h2>
              <p>Usamos cookies y tecnologías similares para mejorar su experiencia, analizar patrones de uso y proporcionar contenido personalizado. Puede controlar la configuración de cookies a través de las preferencias de su navegador.</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">7. Privacidad de los Niños</h2>
              <p>Nuestros servicios no están destinados a niños menores de 13 años. No recopilamos a sabiendas información personal de niños menores de 13 años. Si cree que hemos recopilado dicha información, contáctenos inmediatamente.</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">8. Transferencias Internacionales de Datos</h2>
              <p>Su información puede ser transferida y procesada en países distintos al suyo. Aseguramos que se implementen salvaguardas apropiadas para proteger sus datos de acuerdo con las leyes aplicables.</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">9. Cambios en Esta Política</h2>
              <p>Podemos actualizar esta Política de Privacidad de vez en cuando. Le notificaremos de cualquier cambio material publicando la nueva política en nuestro sitio web y actualizando la fecha de "Última actualización".</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-primary">10. Contáctenos</h2>
              <p>Si tiene alguna pregunta sobre esta Política de Privacidad o nuestras prácticas de datos, contáctenos en:</p>
              <div class="bg-light p-3 rounded">
                <p class="mb-0"><strong>Correo electrónico:</strong> doohee323@gmail.com</p>
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
  name: 'PrivacyPolicyEs',
  metaInfo: {
    title: 'Política de Privacidad - DrillQuiz',
    meta: [
      { name: 'description', content: 'Política de Privacidad de DrillQuiz - Aprenda cómo recopilamos, usamos y protegemos su información personal.' }
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

