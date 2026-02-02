#!/usr/bin/env python3
"""
모든 UC 스크립트의 SQLite 쿼리를 Django ORM으로 일괄 변경
"""

import re
import os

# 테이블과 Django 모델 매핑
TABLE_TO_MODEL = {
    'auth_user': 'User',
    'quiz_userprofile': 'UserProfile',
    'quiz_examresult': 'ExamResult',
    'quiz_examresultdetail': 'ExamResultDetail',
    'quiz_exam': 'Exam',
    'quiz_examquestion': 'ExamQuestion',
    'quiz_question': 'Question',
    'quiz_study': 'Study',
    'quiz_member': 'Member',
    'quiz_studytask': 'StudyTask',
    'quiz_taskcomment': 'TaskComment',
    'quiz_studyinvitation': 'StudyInvitation',
    'quiz_voicesettings': 'VoiceSettings',
    'quiz_aiinterviewsession': 'AIInterviewSession',
    'quiz_aiinterviewquestion': 'AIInterviewQuestion',
}

def get_import_for_model(model_name):
    """모델에 대한 import 문 생성"""
    if model_name == 'User':
        return 'from django.contrib.auth.models import User'
    else:
        return f'from quiz.models import {model_name}'

def replace_sqlite_with_orm(content, table_name, model_name):
    """SQLite 쿼리를 Django ORM으로 변경"""
    
    # 패턴 1: 기존 sqlite_master 패턴 찾기
    old_pattern = rf"""from django\.db import connection\s*
# \w+ 테이블이 있는지 확인\s*
with connection\.cursor\(\) as cursor:\s*
    cursor\.execute\('SELECT name FROM sqlite_master WHERE type=\\'table\\' AND name=\\'{table_name}\\''\)\s*
    tables = cursor\.fetchall\(\)\s*
    \s*
if tables:\s*
    print\(f'\w+ 테이블 발견: \{{.*?\}}'\)\s*
    exit\(0\)\s*
else:\s*
    print\('\w+ 테이블 없음'\)\s*
    exit\(1\)"""
    
    # 새로운 ORM 코드
    new_code = f"""{get_import_for_model(model_name)}

# Django ORM을 사용하여 {model_name} 테이블 존재 확인 (PostgreSQL/SQLite 모두 지원)
try:
    count = {model_name}.objects.count()
    print(f"{model_name} 테이블 발견: {{count}}개")
    exit(0)
except Exception as e:
    print(f"{model_name} 테이블 접근 오류: {{e}}")
    exit(1)"""
    
    # 교체
    content = re.sub(old_pattern, new_code, content, flags=re.MULTILINE)
    
    return content

def process_file(filepath):
    """파일 처리"""
    print(f"\n처리 중: {os.path.basename(filepath)}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        modified = False
        
        # 파일에서 사용하는 테이블 찾아서 변경
        for table_name, model_name in TABLE_TO_MODEL.items():
            if table_name in content and 'sqlite_master' in content:
                print(f"  Found: {table_name} -> {model_name}")
                content = replace_sqlite_with_orm(content, table_name, model_name)
                modified = True
        
        # 변경사항이 있으면 파일에 쓰기
        if modified and content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ {os.path.basename(filepath)} 수정 완료")
        else:
            print(f"  ℹ️  {os.path.basename(filepath)} 변경사항 없음 또는 이미 수정됨")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")

def main():
    script_dir = "/Users/dhong/workspaces/drillquiz/usecase/scripts"
    
    files = [
        'uc-1.6-withdrawal.sh',
        'uc-2.1-file-upload.sh',
        'uc-3.1-exam-creation.sh',
        'uc-3.2-exam-taking.sh',
        'uc-3.3-exam-results.sh',
        'uc-3.4-wrong-notes.sh',
        'uc-4.1-study-creation.sh',
        'uc-4.2-study-members.sh',
        'uc-4.3-study-tasks.sh',
        'uc-5.1-voice-mode.sh',
        'uc-5.2-ai-mock-interview.sh',
    ]
    
    print("=" * 70)
    print("SQLite 쿼리를 Django ORM으로 일괄 변경")
    print("=" * 70)
    
    for filename in files:
        filepath = os.path.join(script_dir, filename)
        if os.path.exists(filepath):
            process_file(filepath)
    
    print("\n" + "=" * 70)
    print("✅ 완료!")
    print("=" * 70)

if __name__ == '__main__':
    main()




