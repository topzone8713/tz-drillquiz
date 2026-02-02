#!/usr/bin/env python3
"""
Django dumpdata를 사용한 개발 환경 DB 백업 스크립트
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

def backup_with_django():
    """Django dumpdata를 사용한 백업"""
    try:
        # 백업 디렉토리 생성
        backup_dir = BASE_DIR / 'backups'
        backup_dir.mkdir(exist_ok=True)
        
        # 백업 파일명 생성 (타임스탬프 포함)
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"drillquiz_dev_django_{timestamp}.json"
        backup_path = backup_dir / backup_filename
        
        print("🚀 Django dumpdata를 사용한 개발 환경 DB 백업 시작")
        print("=" * 60)
        print(f"📊 DB 정보:")
        print(f"  - 호스트: localhost:59164")
        print(f"  - 데이터베이스: drillquiz")
        print(f"  - 백업 파일: {backup_path}")
        
        # Django dumpdata 명령어 실행
        cmd = [
            'python', 'manage.py', 'dumpdata',
            '--indent', '2',
            '--output', str(backup_path),
            '--exclude', 'contenttypes',
            '--exclude', 'auth.Permission'
        ]
        
        print(f"\n🔄 Django dumpdata 백업 실행 중...")
        print(f"명령어: {' '.join(cmd)}")
        
        # 백업 실행
        result = subprocess.run(
            cmd,
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Django 백업이 성공적으로 완료되었습니다!")
            
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
                print("💡 복원 명령어: python manage.py loaddata backup_file.json")
                
            else:
                print("❌ 백업 파일이 생성되지 않았습니다.")
                
        else:
            print("❌ Django 백업 실패!")
            print(f"오류 출력: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Django 백업 중 오류 발생: {e}")
        return False
    
    return True

def backup_specific_apps():
    """특정 앱만 백업"""
    try:
        # 백업 디렉토리 생성
        backup_dir = BASE_DIR / 'backups'
        backup_dir.mkdir(exist_ok=True)
        
        # 백업할 앱 목록
        apps = ['quiz', 'auth', 'sessions']
        
        for app in apps:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"drillquiz_dev_{app}_{timestamp}.json"
            backup_path = backup_dir / backup_filename
            
            print(f"\n🔄 {app} 앱 백업 중...")
            
            cmd = [
                'python', 'manage.py', 'dumpdata', app,
                '--indent', '2',
                '--output', str(backup_path)
            ]
            
            result = subprocess.run(
                cmd,
                cwd=BASE_DIR,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                file_size = backup_path.stat().st_size
                print(f"✅ {app} 앱 백업 완료: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
            else:
                print(f"❌ {app} 앱 백업 실패: {result.stderr}")
                
    except Exception as e:
        print(f"❌ 특정 앱 백업 중 오류 발생: {e}")
        return False
    
    return True

def main():
    """메인 함수"""
    print("🚀 Django dumpdata를 사용한 DB 백업 스크립트")
    print("=" * 50)
    
    # Django 설정 확인
    try:
        from django.conf import settings
        print(f"✅ Django 설정 로드 성공")
        print(f"📊 데이터베이스: {settings.DATABASES['default']['ENGINE']}")
        
    except Exception as e:
        print(f"❌ Django 설정 로드 실패: {e}")
        return
    
    # 전체 DB 백업
    print("\n1️⃣ 전체 DB 백업:")
    if backup_with_django():
        print("✅ 전체 DB 백업 성공!")
    else:
        print("❌ 전체 DB 백업 실패!")
    
    # 특정 앱 백업
    print("\n2️⃣ 특정 앱 백업:")
    if backup_specific_apps():
        print("✅ 특정 앱 백업 성공!")
    else:
        print("❌ 특정 앱 백업 실패!")
    
    print("\n🎉 백업 작업이 완료되었습니다!")

if __name__ == "__main__":
    main()
