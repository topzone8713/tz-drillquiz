from django.apps import AppConfig


class QuizConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'quiz'
    verbose_name = '퀴즈'
    
    def ready(self):
        """앱이 준비되었을 때 시그널을 등록합니다."""
        import quiz.signals 