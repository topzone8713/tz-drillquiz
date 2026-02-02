from django.core.management.base import BaseCommand
from django.conf import settings
import os
import json
import pandas as pd
from datetime import datetime
import boto3
from botocore.exceptions import ClientError


class Command(BaseCommand):
    help = '기존 파일들의 question_count를 계산하여 메타데이터를 업데이트합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제 변경 없이 시뮬레이션만 실행',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN 모드로 실행됩니다.'))
        
        # MinIO 사용 여부 확인
        use_minio = getattr(settings, 'USE_MINIO', False)
        
        if use_minio:
            self.update_minio_files(dry_run)
        else:
            self.update_local_files(dry_run)
    
    def update_minio_files(self, dry_run):
        """MinIO 스토리지의 파일들을 업데이트합니다."""
        try:
            s3_client = boto3.client(
                's3',
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                verify=False
            )
            
            # data/ 폴더의 파일들 가져오기
            response = s3_client.list_objects_v2(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Prefix='data/'
            )
            
            if 'Contents' not in response:
                self.stdout.write(self.style.WARNING('data/ 폴더에 파일이 없습니다.'))
                return
            
            for obj in response['Contents']:
                filename = obj['Key'].replace('data/', '')
                if filename and not filename.endswith('.json'):
                    self.process_minio_file(s3_client, filename, dry_run)
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'MinIO 파일 처리 중 오류: {e}'))
    
    def update_local_files(self, dry_run):
        """로컬 스토리지의 파일들을 업데이트합니다."""
        data_dir = os.path.join(settings.MEDIA_ROOT, 'data')
        
        if not os.path.exists(data_dir):
            self.stdout.write(self.style.WARNING(f'data 디렉토리가 존재하지 않습니다: {data_dir}'))
            return
        
        for filename in os.listdir(data_dir):
            if not filename.endswith('.json'):
                self.process_local_file(data_dir, filename, dry_run)
    
    def process_minio_file(self, s3_client, filename, dry_run):
        """MinIO 파일의 question_count를 계산하고 메타데이터를 업데이트합니다."""
        try:
            # 파일 다운로드
            file_obj = s3_client.get_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=f'data/{filename}'
            )
            
            # 파일 확장자 확인
            file_extension = os.path.splitext(filename)[1].lower()
            
            # 파일 내용 읽기
            if file_extension == '.csv':
                file_content = file_obj['Body'].read().decode('utf-8')
                df = pd.read_csv(file_content)
            elif file_extension in ['.xls', '.xlsx']:
                df = pd.read_excel(file_obj['Body'])
            else:
                self.stdout.write(f'지원하지 않는 파일 형식: {filename}')
                return
            
            # question_count 계산
            question_count = len(df)
            
            # 기존 메타데이터 확인
            metadata = {
                'is_public': True,
                'question_count': question_count,
                'uploaded_at': datetime.now().isoformat(),
                'uploaded_by': 'system'
            }
            
            try:
                # 기존 메타데이터 파일이 있는지 확인
                metadata_obj = s3_client.get_object(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Key=f'data/{filename}.json'
                )
                existing_metadata = json.loads(metadata_obj['Body'].read().decode('utf-8'))
                # 기존 메타데이터 유지하면서 question_count만 업데이트
                metadata.update(existing_metadata)
                metadata['question_count'] = question_count
                self.stdout.write(f'기존 메타데이터에서 question_count 업데이트: {filename}')
            except:
                self.stdout.write(f'새 메타데이터 생성: {filename}')
            
            if not dry_run:
                # 메타데이터 저장
                metadata_json = json.dumps(metadata, ensure_ascii=False)
                s3_client.put_object(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Key=f'data/{filename}.json',
                    Body=metadata_json.encode('utf-8'),
                    ContentType='application/json'
                )
                self.stdout.write(self.style.SUCCESS(f'✅ {filename}: {question_count}개 문제'))
            else:
                self.stdout.write(f'[DRY RUN] {filename}: {question_count}개 문제')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'파일 처리 중 오류 ({filename}): {e}'))
    
    def process_local_file(self, data_dir, filename, dry_run):
        """로컬 파일의 question_count를 계산하고 메타데이터를 업데이트합니다."""
        try:
            file_path = os.path.join(data_dir, filename)
            file_extension = os.path.splitext(filename)[1].lower()
            
            # 파일 읽기
            if file_extension == '.csv':
                df = pd.read_csv(file_path)
            elif file_extension in ['.xls', '.xlsx']:
                df = pd.read_excel(file_path)
            else:
                self.stdout.write(f'지원하지 않는 파일 형식: {filename}')
                return
            
            # question_count 계산
            question_count = len(df)
            
            # 기존 메타데이터 확인
            metadata_path = os.path.join(data_dir, f'{filename}.json')
            metadata = {
                'is_public': True,
                'question_count': question_count,
                'uploaded_at': datetime.now().isoformat(),
                'uploaded_by': 'system'
            }
            
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    existing_metadata = json.load(f)
                # 기존 메타데이터 유지하면서 question_count만 업데이트
                metadata.update(existing_metadata)
                metadata['question_count'] = question_count
                self.stdout.write(f'기존 메타데이터에서 question_count 업데이트: {filename}')
            else:
                self.stdout.write(f'새 메타데이터 생성: {filename}')
            
            if not dry_run:
                # 메타데이터 저장
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
                self.stdout.write(self.style.SUCCESS(f'✅ {filename}: {question_count}개 문제'))
            else:
                self.stdout.write(f'[DRY RUN] {filename}: {question_count}개 문제')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'파일 처리 중 오류 ({filename}): {e}')) 