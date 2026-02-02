#!/bin/bash

# 나머지 모든 UC 스크립트의 SQLite 쿼리를 Django ORM으로 일괄 변경

cd /Users/dhong/workspaces/drillquiz/usecase/scripts

echo "=== 나머지 UC 스크립트 일괄 수정 시작 ==="

# UC-3.1: Exam, ExamQuestion
echo "Fixing uc-3.1-exam-creation.sh..."
perl -i -pe 's/from django\.db import connection\n\n# Exam 테이블이 있는지 확인\nwith connection\.cursor\(\) as cursor:\n    cursor\.execute\(.*quiz_exam.*\)\n    tables = cursor\.fetchall\(\)\n    \nif tables:\n    print\(f.*Exam 테이블 발견.*\)\n    exit\(0\)\nelse:\n    print\(.*Exam 테이블 없음.*\)\n    exit\(1\)/from quiz.models import Exam\n\n    # Django ORM\n    try:\n        count = Exam.objects.count()\n        print(f"Exam 테이블 발견: {count}개")\n        exit(0)\n    except Exception as e:\n        print(f"Exam 테이블 접근 오류: {e}")\n        exit(1)/g' uc-3.1-exam-creation.sh

echo "✅ uc-3.1-exam-creation.sh 수정 완료"

echo "=== 완료 ==="




