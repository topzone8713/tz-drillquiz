"""
Celery configuration for drillquiz project.

This module configures Celery to use Redis as the message broker and result backend.
"""

import os
from celery import Celery
from django.conf import settings

# Django 설정 모듈 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')

# Celery 앱 생성
app = Celery('drillquiz')

# Django 설정에서 Celery 설정 로드
app.config_from_object('django.conf:settings', namespace='CELERY')

# Celery 브로커가 설정되지 않은 경우 비활성화
if not settings.CELERY_BROKER_URL:
    # Celery를 비활성화 (태스크는 등록되지만 실행되지 않음)
    app.conf.task_always_eager = True  # 동기 실행 (테스트용)
    app.conf.task_eager_propagates = True
else:
    # Django 앱에서 태스크 자동 발견
    app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """디버깅용 테스트 태스크"""
    print(f'Request: {self.request!r}')

