"""
This will make sure the app is always imported when
Django starts so that shared_task will use this app.
"""
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    # Celery가 설치되지 않은 경우에도 Django가 실행될 수 있도록 함
    celery_app = None
    __all__ = ()
