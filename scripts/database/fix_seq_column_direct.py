#!/usr/bin/env python3
"""
Django dbshell을 사용해서 PostgreSQL DB에서 seq 컬럼을 삭제하는 스크립트
"""

import os
import sys
import subprocess
from pathlib import Path

# Django 설정 로드
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

def run_dbshell_command(command):
    """Django dbshell에서 SQL 명령어 실행"""
    try:
        # 환경 변수 설정
        env = os.environ.copy()
        env.update({
            'POSTGRES_HOST': 'localhost',
            'POSTGRES_PORT': '51452',
            'POSTGRES_DB': 'drillquiz',
            'POSTGRES_USER': 'postgres',
            'POSTGRES_PASSWORD': 'DevOps!323',
            'USE_DOCKER': 'true',
            'DJANGO_SETTINGS_MODULE': 'drillquiz.settings'
        })
        
        # Django dbshell 명령어 실행
        result = subprocess.run(
            ['python', 'manage.py', 'dbshell'],
            input=command.encode(),
            capture_output=True,
            text=True,
            env=env,
            cwd=BASE_DIR
        )
        
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    """메인 함수"""
    print("🚀 Django dbshell을 사용한 seq 컬럼 삭제 스크립트 시작")
    print("=" * 60)
    
    # 1. 현재 테이블 구조 확인
    print("🔍 quiz_studytask 테이블 구조 확인 중...")
    check_command = """
    \d quiz_studytask
    """
    
    success, stdout, stderr = run_dbshell_command(check_command)
    if success:
        print("✅ 테이블 구조 확인 성공:")
        print(stdout)
    else:
        print("❌ 테이블 구조 확인 실패:")
        print(stderr)
        return
    
    # 2. seq 컬럼 존재 여부 확인
    print("\n🔍 seq 컬럼 존재 여부 확인 중...")
    check_seq_command = """
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'quiz_studytask' 
    AND column_name = 'seq';
    """
    
    success, stdout, stderr = run_dbshell_command(check_seq_command)
    if success:
        if 'seq' in stdout:
            print("✅ seq 컬럼이 존재합니다. 삭제를 시작합니다...")
            
            # 3. seq 컬럼 삭제
            print("\n🗑️ seq 컬럼 삭제 중...")
            drop_command = """
            ALTER TABLE quiz_studytask DROP COLUMN IF EXISTS seq;
            """
            
            success, stdout, stderr = run_dbshell_command(drop_command)
            if success:
                print("✅ seq 컬럼 삭제 성공!")
            else:
                print("❌ seq 컬럼 삭제 실패:")
                print(stderr)
                return
            
            # 4. seq 관련 인덱스 삭제
            print("\n🗑️ seq 관련 인덱스 삭제 중...")
            drop_index_command = """
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'quiz_studytask' 
            AND indexdef LIKE '%seq%';
            """
            
            success, stdout, stderr = run_dbshell_command(drop_index_command)
            if success and stdout.strip():
                indexes = [line.strip() for line in stdout.split('\n') if line.strip() and not line.startswith('indexname')]
                for index in indexes:
                    if index:
                        print(f"🗑️ 인덱스 {index} 삭제 중...")
                        drop_index_sql = f"DROP INDEX IF EXISTS {index};"
                        success, _, stderr = run_dbshell_command(drop_index_sql)
                        if success:
                            print(f"✅ 인덱스 {index} 삭제 성공!")
                        else:
                            print(f"❌ 인덱스 {index} 삭제 실패: {stderr}")
            else:
                print("ℹ️ seq 관련 인덱스가 없습니다.")
            
            # 5. 최종 테이블 구조 확인
            print("\n📋 최종 테이블 구조 확인:")
            final_check_command = """
            \d quiz_studytask
            """
            
            success, stdout, stderr = run_dbshell_command(final_check_command)
            if success:
                print(stdout)
            else:
                print(f"❌ 최종 확인 실패: {stderr}")
            
            print("\n🎉 seq 컬럼 삭제가 완료되었습니다!")
            print("💡 이제 마이그레이션을 다시 실행할 수 있습니다.")
            
        else:
            print("ℹ️ seq 컬럼이 이미 존재하지 않습니다.")
    else:
        print("❌ seq 컬럼 확인 실패:")
        print(stderr)

if __name__ == "__main__":
    main()
