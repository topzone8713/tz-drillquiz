from django.core.management.base import BaseCommand
from django.conf import settings
import os
import json
from datetime import datetime


class Command(BaseCommand):
    help = 'Add metadata to existing files that don\'t have uploaded_by information'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Username to set as uploaded_by for existing files'
        )

    def handle(self, *args, **options):
        username = options['username']
        
        # MinIO를 사용하는 경우와 로컬 스토리지를 사용하는 경우를 구분
        use_minio = getattr(settings, 'USE_MINIO', False)
        
        if use_minio:
            self.handle_minio_files(username)
        else:
            self.handle_local_files(username)

    def handle_minio_files(self, username):
        """MinIO 스토리지의 파일들에 메타데이터 추가"""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            s3_client = boto3.client(
                's3',
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                verify=False
            )
            
            # data/ 폴더의 파일들 조회
            response = s3_client.list_objects_v2(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Prefix='data/'
            )
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    filename = obj['Key'].replace('data/', '')
                    if filename and not filename.endswith('.json'):
                        # 메타데이터 파일 경로
                        metadata_key = f'data/{filename}.json'
                        
                        # 메타데이터 파일이 있는지 확인
                        try:
                            s3_client.head_object(
                                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                                Key=metadata_key
                            )
                            self.stdout.write(f"메타데이터 파일이 이미 존재합니다: {filename}")
                        except ClientError as e:
                            if e.response['Error']['Code'] == 'NoSuchKey':
                                # 메타데이터 파일이 없으면 생성
                                metadata = {
                                    'is_public': True,
                                    'question_count': 0,  # 기본값
                                    'uploaded_at': datetime.now().isoformat(),
                                    'uploaded_by': username
                                }
                                
                                metadata_json = json.dumps(metadata, ensure_ascii=False)
                                s3_client.put_object(
                                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                                    Key=metadata_key,
                                    Body=metadata_json.encode('utf-8'),
                                    ContentType='application/json'
                                )
                                self.stdout.write(
                                    self.style.SUCCESS(f"메타데이터 추가됨: {filename} -> {username}")
                                )
                            else:
                                self.stdout.write(
                                    self.style.ERROR(f"메타데이터 파일 확인 실패: {filename} - {e}")
                                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"MinIO 처리 실패: {e}")
            )

    def handle_local_files(self, username):
        """로컬 스토리지의 파일들에 메타데이터 추가"""
        data_dir = os.path.join(settings.MEDIA_ROOT, 'data')
        
        if not os.path.exists(data_dir):
            self.stdout.write(
                self.style.ERROR(f"data 디렉토리가 존재하지 않습니다: {data_dir}")
            )
            return
        
        for filename in os.listdir(data_dir):
            file_path = os.path.join(data_dir, filename)
            if os.path.isfile(file_path) and not filename.endswith('.json'):
                # 메타데이터 파일 경로
                metadata_path = os.path.join(data_dir, f'{filename}.json')
                
                if os.path.exists(metadata_path):
                    self.stdout.write(f"메타데이터 파일이 이미 존재합니다: {filename}")
                else:
                    # 메타데이터 파일이 없으면 생성
                    metadata = {
                        'is_public': True,
                        'question_count': 0,  # 기본값
                        'uploaded_at': datetime.now().isoformat(),
                        'uploaded_by': username
                    }
                    
                    with open(metadata_path, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=2)
                    
                    self.stdout.write(
                        self.style.SUCCESS(f"메타데이터 추가됨: {filename} -> {username}")
                    ) 