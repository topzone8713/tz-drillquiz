from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings


class MinIOStorage(S3Boto3Storage):
    """
    MinIO 스토리지를 위한 커스텀 스토리지 백엔드
    """
    location = 'data'  # MinIO 버킷 내의 data 폴더에 저장
    file_overwrite = False
    default_acl = None
    querystring_auth = False


class MinIOStaticStorage(S3Boto3Storage):
    """
    정적 파일을 위한 MinIO 스토리지 백엔드
    """
    location = 'static'
    file_overwrite = True
    default_acl = 'public-read'
    querystring_auth = False 