#!/usr/bin/env python3
"""
pg_dump를 사용한 개발 환경 PostgreSQL DB 백업 스크립트
"""

import os
import sys
import subprocess
import datetime
from pathlib import Path

# Django 설정 로드
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

def backup_database():
    """PostgreSQL DB 백업 실행"""
    
    # 백업 설정
    DB_HOST = 'localhost'
    DB_PORT = '59164'
    DB_NAME = 'drillquiz'
    DB_USER = 'postgres'
    DB_PASSWORD = 'DevOps!323'
    
    # 백업 디렉토리 생성
    backup_dir = BASE_DIR / 'backups'
    backup_dir.mkdir(exist_ok=True)
    
    # 백업 파일명 생성 (타임스탬프 포함)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"drillquiz_dev_backup_{timestamp}.sql"
    backup_path = backup_dir / backup_filename
    
    print("🚀 개발 환경 PostgreSQL DB 백업 시작")
    print("=" * 50)
    print(f"📊 DB 정보:")
    print(f"  - 호스트: {DB_HOST}:{DB_PORT}")
    print(f"  - 데이터베이스: {DB_NAME}")
    print(f"  - 사용자: {DB_USER}")
    print(f"  - 백업 파일: {backup_path}")
    
    try:
        # 환경 변수 설정
        env = os.environ.copy()
        env['PGPASSWORD'] = DB_PASSWORD
        
        # pg_dump 명령어 실행
        cmd = [
            'pg_dump',
            f'--host={DB_HOST}',
            f'--port={DB_PORT}',
            f'--username={DB_USER}',
            '--verbose',
            '--clean',
            '--create',
            '--if-exists',
            '--no-owner',
            '--no-privileges',
            f'--file={backup_path}',
            DB_NAME
        ]
        
        print(f"\n🔄 백업 명령어 실행 중...")
        print(f"명령어: {' '.join(cmd)}")
        
        # 백업 실행
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            cwd=BASE_DIR
        )
        
        if result.returncode == 0:
            print("✅ 백업이 성공적으로 완료되었습니다!")
            
            # 백업 파일 크기 확인
            if backup_path.exists():
                file_size = backup_path.stat().st_size
                print(f"📁 백업 파일 크기: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
                
                # 백업 파일 내용 미리보기 (처음 10줄)
                print(f"\n📋 백업 파일 내용 미리보기 (처음 10줄):")
                with open(backup_path, 'r') as f:
                    for i, line in enumerate(f):
                        if i < 10:
                            print(f"  {i+1:2d}: {line.rstrip()}")
                        else:
                            break
                
                print(f"\n💡 백업 파일 위치: {backup_path}")
                print("💡 복원 명령어: psql -h localhost -p 59164 -U postgres -d drillquiz < backup_file.sql")
                
            else:
                print("❌ 백업 파일이 생성되지 않았습니다.")
                
        else:
            print("❌ 백업 실패!")
            print(f"오류 출력: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ pg_dump 명령어를 찾을 수 없습니다.")
        print("💡 PostgreSQL 클라이언트가 설치되어 있는지 확인하세요.")
        print("💡 macOS: brew install postgresql")
        print("💡 Ubuntu: sudo apt-get install postgresql-client")
        return False
        
    except Exception as e:
        print(f"❌ 백업 중 오류 발생: {e}")
        return False
    
    return True

def main():
    """메인 함수"""
    print("🚀 PostgreSQL DB 백업 스크립트")
    print("=" * 40)
    
    # pg_dump 설치 확인
    try:
        result = subprocess.run(['pg_dump', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ pg_dump 버전: {result.stdout.strip()}")
        else:
            print("❌ pg_dump 실행 실패")
            return
    except FileNotFoundError:
        print("❌ pg_dump가 설치되어 있지 않습니다.")
        return
    
    # 백업 실행
    if backup_database():
        print("\n🎉 백업이 완료되었습니다!")
    else:
        print("\n❌ 백업에 실패했습니다.")

if __name__ == "__main__":
    main()
