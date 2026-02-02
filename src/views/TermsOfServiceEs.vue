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
          <div class="card-header bg-success text-white">
            <h1 class="h3 mb-0">Términos de Servicio</h1>
          </div>
          <div class="card-body">
            <div class="mb-4">
              <p class="text-muted">Última actualización: Agosto 2025</p>
            </div>

            <section class="mb-4">
              <h2 class="h4 text-success">1. Aceptación de los Términos</h2>
              <p>Al acceder y usar DrillQuiz ("Servicio"), usted acepta y se compromete a cumplir con los términos y disposiciones de este acuerdo. Si no está de acuerdo en cumplir con lo anterior, por favor no use este servicio.</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">2. Descripción del Servicio</h2>
              <p>DrillQuiz es una plataforma de aprendizaje en línea que proporciona:</p>
              <ul>
                <li>Cuestionarios de programación interactivos y problemas de práctica</li>
                <li>Materiales de estudio y recursos de aprendizaje</li>
                <li>Seguimiento del progreso y análisis de rendimiento</li>
                <li>Características comunitarias para aprendizaje colaborativo</li>
                <li>Recomendaciones de estudio personalizadas</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">3. Cuentas de Usuario</h2>
              <p>Para acceder a ciertas funciones del Servicio, debe crear una cuenta. Usted acepta:</p>
              <ul>
                <li>Proporcionar información precisa y completa</li>
                <li>Mantener la seguridad de las credenciales de su cuenta</li>
                <li>Aceptar la responsabilidad de todas las actividades bajo su cuenta</li>
                <li>Notificarnos inmediatamente de cualquier uso no autorizado</li>
                <li>Tener al menos 13 años de edad para crear una cuenta</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">4. Uso Aceptable</h2>
              <p>Usted acepta usar el Servicio solo para fines legales y de acuerdo con estos Términos. Usted acepta no:</p>
              <ul>
                <li>Usar el Servicio para cualquier propósito ilegal o no autorizado</li>
                <li>Intentar obtener acceso no autorizado a nuestros sistemas</li>
                <li>Interferir o interrumpir el Servicio</li>
                <li>Compartir las credenciales de su cuenta con otros</li>
                <li>Usar herramientas automatizadas para acceder al Servicio</li>
                <li>Violar cualquier ley o regulación aplicable</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">5. Propiedad Intelectual</h2>
              <p>El Servicio y su contenido original, características y funcionalidad son propiedad de DrillQuiz y están protegidos por leyes internacionales de derechos de autor, marcas registradas, patentes, secretos comerciales y otras leyes de propiedad intelectual.</p>
              <p>Usted conserva la propiedad del contenido que crea, pero nos otorga una licencia para usar, modificar y mostrarlo en relación con el Servicio.</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">6. Contenido del Usuario</h2>
              <p>Usted es responsable de cualquier contenido que envíe, publique o muestre en el Servicio. Usted acepta no enviar contenido que:</p>
              <ul>
                <li>Sea ilegal, dañino, amenazante o abusivo</li>
                <li>Infrinja los derechos de propiedad intelectual</li>
                <li>Contenga malware o código dañino</li>
                <li>Sea spam o contenido comercial no solicitado</li>
                <li>Viole la privacidad o confidencialidad</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">7. Privacidad y Protección de Datos</h2>
              <p>Su privacidad es importante para nosotros. Nuestra recopilación y uso de información personal se rige por nuestra Política de Privacidad, que se incorpora a estos Términos por referencia.</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">8. Disponibilidad del Servicio</h2>
              <p>Nos esforzamos por mantener una alta disponibilidad del Servicio, pero no garantizamos acceso ininterrumpido. El Servicio puede estar temporalmente no disponible debido a:</p>
              <ul>
                <li>Mantenimiento programado</li>
                <li>Problemas técnicos o actualizaciones del sistema</li>
                <li>Eventos de fuerza mayor</li>
                <li>Interrupciones de servicios de terceros</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">9. Limitación de Responsabilidad</h2>
              <p>En la máxima medida permitida por la ley, DrillQuiz no será responsable de ningún daño indirecto, incidental, especial, consecuente o punitivo, incluyendo pero no limitado a pérdida de ganancias, datos o uso.</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">10. Descargos de Responsabilidad</h2>
              <p>El Servicio se proporciona "tal cual" y "según disponibilidad" sin garantías de ningún tipo. No garantizamos:</p>
              <ul>
                <li>La precisión o integridad del contenido</li>
                <li>Servicio ininterrumpido o libre de errores</li>
                <li>Resultados o resultados de aprendizaje específicos</li>
                <li>Compatibilidad con todos los dispositivos o navegadores</li>
              </ul>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">11. Terminación</h2>
              <p>Podemos terminar o suspender su cuenta y acceso al Servicio en cualquier momento, con o sin causa, con o sin previo aviso. También puede terminar su cuenta en cualquier momento contactándonos.</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">12. Cambios en los Términos</h2>
              <p>Nos reservamos el derecho de modificar estos Términos en cualquier momento. Notificaremos a los usuarios de cambios materiales publicando los nuevos Términos en nuestro sitio web y actualizando la fecha de "Última actualización".</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">13. Ley Aplicable</h2>
              <p>Estos Términos se regirán e interpretarán de acuerdo con las leyes de la jurisdicción en la que opera DrillQuiz, sin tener en cuenta los principios de conflicto de leyes.</p>
            </section>

            <section class="mb-4">
              <h2 class="h4 text-success">14. Información de Contacto</h2>
              <p>Si tiene alguna pregunta sobre estos Términos de Servicio, contáctenos en:</p>
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
  name: 'TermsOfServiceEs',
  metaInfo: {
    title: 'Términos de Servicio - DrillQuiz',
    meta: [
      { name: 'description', content: 'Términos de Servicio de DrillQuiz - Lea nuestros términos y condiciones para usar la plataforma.' }
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

