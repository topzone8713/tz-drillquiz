#!/usr/bin/env python3
"""
간단한 Django 백업 스크립트
"""

import os
import sys
import django
import subprocess
import datetime
from pathlib import Path

# Django 설정 로드
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drillquiz.settings')
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '59164'
os.environ['POSTGRES_DB'] = 'drillquiz'
os.environ['POSTGRES_USER'] = 'postgres'
os.environ['POSTGRES_PASSWORD'] = 'DevOps!323'
os.environ['USE_DOCKER'] = 'true'

django.setup()

def backup_database():
    """Django dumpdata로 백업"""
    try:
        # 백업 디렉토리 생성
        backup_dir = BASE_DIR / 'backups'
        backup_dir.mkdir(exist_ok=True)
        
        # 백업 파일명 생성
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"drillquiz_dev_backup_{timestamp}.json"
        backup_path = backup_dir / backup_filename
        
        print("🚀 Django dumpdata 백업 시작")
        print("=" * 40)
        print(f"📊 백업 파일: {backup_path}")
        
        # Django dumpdata 명령어 실행
        cmd = [
            sys.executable, 'manage.py', 'dumpdata',
            '--indent', '2',
            '--output', str(backup_path),
            '--exclude', 'contenttypes',
            '--exclude', 'auth.Permission'
        ]
        
        print(f"🔄 명령어 실행: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ 백업 성공!")
            
            if backup_path.exists():
                file_size = backup_path.stat().st_size
                print(f"📁 파일 크기: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
                print(f"💡 백업 위치: {backup_path}")
            else:
                print("❌ 백업 파일이 생성되지 않음")
                
        else:
            print("❌ 백업 실패!")
            print(f"오류: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False
    
    return True

def main():
    """메인 함수"""
    print("🚀 개발 DB 백업 스크립트")
    print("=" * 30)
    
    if backup_database():
        print("\n🎉 백업 완료!")
    else:
        print("\n❌ 백업 실패!")

if __name__ == "__main__":
    main()
