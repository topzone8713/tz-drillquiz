#!/usr/bin/env python3
import os
import sys
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
import django
django.setup()
from django.db import connection

# ExamResult 테이블이 있는지 확인
with connection.cursor() as cursor:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quiz_examresult'")
    result = cursor.fetchone()
    if result:
        print('ExamResult 테이블 존재 확인 성공')
    else:
        print('ExamResult 테이블이 존재하지 않습니다')
        exit(1)
