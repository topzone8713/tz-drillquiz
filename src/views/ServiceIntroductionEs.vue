<template>
  <div class="service-introduction">
    <div class="container-fluid">
      <!-- Sección de Encabezado -->
      <div class="jumbotron bg-primary text-white text-center py-5 mb-5">
        <div class="container">
          <h1 class="display-4 mb-4">Introducción del Servicio</h1>
          <p class="lead">Una plataforma innovadora para el aprendizaje eficiente</p>
        </div>
      </div>

      <!-- Contenido Principal -->
      <div class="container">
        <div class="mb-3">
          <button @click="goBack" class="btn btn-outline-secondary">
            <i class="fas fa-arrow-left"></i> Atrás
          </button>
        </div>
        <!-- 1. Nueva Forma de Aprendizaje Repetitivo -->
        <div class="row mb-5">
          <div class="col-lg-8 mx-auto">
            <div class="card shadow-sm">
              <div class="card-body p-4">
                <div class="d-flex align-items-center mb-3">
                  <div class="feature-icon bg-primary text-white rounded-circle d-flex align-items-center justify-content-center me-3" style="width: 60px; height: 60px;">
                    <i class="fas fa-redo fa-lg"></i>
                  </div>
                  <h2 class="card-title mb-0">Nueva Forma de Aprendizaje Repetitivo</h2>
                </div>
                <p class="card-text mb-4">DrillQuiz proporciona un sistema inteligente de aprendizaje repetitivo basado en la teoría de la curva de olvido. No es solo una simple repetición, sino un patrón de aprendizaje científicamente diseñado que fortalece la memoria a largo plazo.</p>
                
                <div class="row">
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-primary">Sistema de Drenaje</h5>
                      <p class="text-muted">Recopila automáticamente problemas incorrectos para que pueda concentrarse en el aprendizaje repetitivo. Una vez que comete un error, seguirá repitiéndose hasta que aparezca nuevamente.</p>
                    </div>
                  </div>
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-primary">Mejora de la Memoria a Largo Plazo</h5>
                      <p class="text-muted">A medida que pasa el tiempo, el intervalo entre problemas que aparecen nuevamente aumenta gradualmente, ayudando naturalmente a convertir en memoria a largo plazo.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 2. Soporte de Aprendizaje Estilo Entrevista -->
        <div class="row mb-5">
          <div class="col-lg-8 mx-auto">
            <div class="card shadow-sm">
              <div class="card-body p-4">
                <div class="d-flex align-items-center mb-3">
                  <div class="feature-icon bg-success text-white rounded-circle d-flex align-items-center justify-content-center me-3" style="width: 60px; height: 60px;">
                    <i class="fas fa-comments fa-lg"></i>
                  </div>
                  <h2 class="card-title mb-0">Soporte de Aprendizaje Estilo Entrevista</h2>
                </div>
                <p class="card-text mb-4">Simula entornos de entrevistas técnicas reales para desarrollar su capacidad de explicar verbalmente. Proporciona una experiencia de aprendizaje interactiva utilizando tecnología de reconocimiento de voz.</p>
                
                <div class="row">
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-success">Modo de Entrevista por Voz</h5>
                      <p class="text-muted">Puede leer problemas y practicar explicando respuestas verbalmente. Proporciona una experiencia similar a situaciones de entrevistas reales.</p>
                    </div>
                  </div>
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-success">Práctica de Preguntas de Seguimiento</h5>
                      <p class="text-muted">Después de responder, puede recibir preguntas de seguimiento para practicar explicaciones más profundas. Desarrolla la capacidad de pensar desde la perspectiva de un entrevistador.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 3. Gestión Personalizada de Errores -->
        <div class="row mb-5">
          <div class="col-lg-8 mx-auto">
            <div class="card shadow-sm">
              <div class="card-body p-4">
                <div class="d-flex align-items-center mb-3">
                  <div class="feature-icon bg-warning text-white rounded-circle d-flex align-items-center justify-content-center me-3" style="width: 60px; height: 60px;">
                    <i class="fas fa-envelope fa-lg"></i>
                  </div>
                  <h2 class="card-title mb-0">Gestión Personalizada de Errores</h2>
                </div>
                <p class="card-text mb-4">Recopila automáticamente problemas incorrectos y los envía regularmente por correo electrónico para que pueda revisarlos en cualquier momento y lugar. Construye naturalmente hábitos de aprendizaje.</p>
                
                <div class="row">
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-warning">Recopilación Automática de Errores</h5>
                      <p class="text-muted">Los problemas incorrectos se agregan automáticamente a su cuaderno de errores, permitiendo una gestión sistemática sin trabajo adicional.</p>
                    </div>
                  </div>
                  <div class="col-md-6 mb-3">
                    <div class="feature-item">
                      <h5 class="text-warning">Revisión por Correo Electrónico</h5>
                      <p class="text-muted">Reciba problemas de error por correo electrónico en los intervalos que establezca, permitiéndole revisarlos naturalmente en su vida diaria.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 4. Maximizar la Efectividad del Aprendizaje -->
        <div class="row mb-5 mb-md-0">
          <div class="col-lg-8 mx-auto">
            <div class="card shadow-sm">
              <div class="card-body p-4">
                <div class="d-flex align-items-center mb-3">
                  <div class="feature-icon bg-info text-white rounded-circle d-flex align-items-center justify-content-center me-3" style="width: 60px; height: 60px;">
                    <i class="fas fa-chart-line fa-lg"></i>
                  </div>
                  <h2 class="card-title mb-0">Maximizar la Efectividad del Aprendizaje</h2>
                </div>
                <p class="card-text mb-4">Tres características principales trabajan juntas orgánicamente para crear una efectividad de aprendizaje óptima.</p>
                
                <div class="row">
                  <div class="col-md-4 mb-3">
                    <div class="feature-item text-center">
                      <div class="feature-icon-small bg-primary text-white rounded-circle d-inline-flex align-items-center justify-content-center mb-2" style="width: 40px; height: 40px;">
                        <i class="fas fa-redo"></i>
                      </div>
                      <h6 class="text-primary">Sistema de Drenaje</h6>
                      <p class="text-muted small">Recopilación automática de errores y aprendizaje repetitivo</p>
                    </div>
                  </div>
                  <div class="col-md-4 mb-3">
                    <div class="feature-item text-center">
                      <div class="feature-icon-small bg-success text-white rounded-circle d-inline-flex align-items-center justify-content-center mb-2" style="width: 40px; height: 40px;">
                        <i class="fas fa-comments"></i>
                      </div>
                      <h6 class="text-success">Entrevista por Voz</h6>
                      <p class="text-muted small">Simulación de entorno de entrevista real</p>
                    </div>
                  </div>
                  <div class="col-md-4 mb-3">
                    <div class="feature-item text-center">
                      <div class="feature-icon-small bg-warning text-white rounded-circle d-inline-flex align-items-center justify-content-center mb-2" style="width: 40px; height: 40px;">
                        <i class="fas fa-envelope"></i>
                      </div>
                      <h6 class="text-warning">Revisión por Correo Electrónico</h6>
                      <p class="text-muted small">Entrega regular de problemas de error</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Sección CTA - Solo se muestra a usuarios no autenticados -->
        <div v-if="!isAuthenticated" class="row mb-0">
          <div class="col-lg-8 mx-auto text-center">
            <div class="card bg-light">
              <div class="card-body p-5">
                <h3 class="card-title mb-4">Comience Ahora</h3>
                <p class="card-text mb-4">Comience un aprendizaje más eficiente con DrillQuiz. Regístrese gratis y experimente todas las funciones.</p>
                <div class="d-flex justify-content-center gap-3 flex-wrap">
                  <router-link to="/register" class="btn btn-primary btn-lg">
                    <i class="fas fa-user-plus me-md-2"></i><span class="d-none d-md-inline">Registrarse</span>
                  </router-link>
                  <router-link to="/login" class="btn btn-outline-primary btn-lg">
                    <i class="fas fa-sign-in-alt me-md-2"></i><span class="d-none d-md-inline">Iniciar Sesión</span>
                  </router-link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import authService from '@/services/authService'

export default {
  name: 'ServiceIntroductionEs',
  computed: {
    isAuthenticated() {
      return authService.isAuthenticatedSync()
    }
  },
  methods: {
    goBack() {
      if (window.history.length > 1) {
        this.$router.go(-1)
      } else {
        this.$router.push('/register')
      }
    }
  },
  metaInfo: {
    title: 'Introducción del Servicio - DrillQuiz',
    meta: [
      { 
        name: 'description', 
        content: 'Descubra las características innovadoras de aprendizaje de DrillQuiz. Maximice su efectividad de aprendizaje a través del aprendizaje repetitivo, aprendizaje estilo entrevista y gestión personalizada de errores.' 
      },
      { 
        name: 'keywords', 
        content: 'DrillQuiz, introducción del servicio, aprendizaje repetitivo, aprendizaje de entrevista, gestión de errores, efectividad del aprendizaje' 
      }
    ]
  }
}
</script>

<style scoped>
.service-introduction {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding-bottom: 0;
}

.service-introduction .container > .row:last-child {
  margin-bottom: 0 !important;
}

.jumbotron {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border-radius: 0;
}

.feature-icon {
  font-size: 1.5rem;
}

.feature-icon-small {
  font-size: 1rem;
}

.card {
  border: none;
  border-radius: 15px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 25px rgba(0,0,0,0.1) !important;
}

.feature-item {
  padding: 1rem 0;
}

.btn {
  border-radius: 25px;
  padding: 12px 30px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0,0,0,0.2);
}

@media (max-width: 768px) {
  .jumbotron {
    padding: 3rem 1rem !important;
  }
  
  .display-4 {
    font-size: 2rem;
  }
  
  .lead {
    font-size: 1rem;
  }
  
  .card-body {
    padding: 1.5rem !important;
  }
  
  .feature-icon {
    width: 50px !important;
    height: 50px !important;
    font-size: 1.2rem;
  }
  
  .btn {
    padding: 10px 20px;
    font-size: 0.9rem;
  }
}
</style>

