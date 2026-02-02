import pandas as pd
import random
import csv
import io
import xml.etree.ElementTree as ET
from xml.dom import minidom
import logging
import openai
import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import yaml
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
from ..message_ko import KOREAN_TRANSLATIONS
from ..message_en import ENGLISH_TRANSLATIONS

logger = logging.getLogger(__name__)
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db import transaction
from django.middleware.csrf import get_token
from django.utils import timezone
from io import BytesIO
from ..models import Question, Exam, ExamResult, ExamResultDetail, Study, StudyTask, Member, ExamQuestion, QuestionMemberMapping, UserProfile, StudyTaskProgress, StudyProgressRecord, IgnoredQuestion
from ..utils.multilingual_utils import get_localized_field, get_user_language
from ..serializers import (
    QuestionSerializer, ExamSerializer, ExamResultSerializer, ExamResultDetailSerializer,
    CreateExamSerializer, SubmitExamSerializer, StudySerializer, StudyTaskSerializer, StudyTaskUpdateSerializer,
    MemberSerializer, QuestionMemberMappingSerializer, CreateQuestionMemberMappingSerializer
)
import os
from django.conf import settings
from django.http import FileResponse, Http404
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from django.db import models
from django.db.models import Q
from ..models import StudyTaskProgress
from io import BytesIO
from datetime import datetime
import uuid

User = get_user_model()


QUESTION_FILES_DIR = os.path.join(settings.MEDIA_ROOT, 'data')


def auto_correct_csv_from_content(content):
    """CSV 내용을 자동으로 보정합니다."""
    try:
        print(f"auto_correct_csv_from_content 호출됨. 내용 길이: {len(content)}")
        
        # 먼저 전체 내용을 한 번에 파싱해서 문제가 있는 줄 찾기
        import csv
        from io import StringIO
        
        # 원본 내용으로 pandas 읽기 시도
        try:
            test_df = pd.read_csv(StringIO(content))
            print(f"원본 CSV 읽기 성공. 컬럼 수: {len(test_df.columns)}")
            return StringIO(content)  # 원본이 정상이면 그대로 반환
        except Exception as e:
            print(f"원본 CSV 읽기 실패: {e}")
        
        # 수동으로 줄 단위 처리
        lines = content.splitlines()
        print(f"분할된 행 수: {len(lines)}")
        
        # 빈 행 제거
        lines = [line.strip() for line in lines if line.strip()]
        print(f"빈 행 제거 후 행 수: {len(lines)}")
        
        if not lines:
            raise ValueError("파일이 비어있습니다.")
        
        # 첫 번째 행을 헤더로 사용
        header = lines[0]
        header_columns = list(csv.reader([header]))[0]
        expected_columns = len(header_columns)
        print(f"헤더 컬럼 수: {expected_columns}, 헤더: {header_columns}")
        
        corrected_lines = [header]
        newline_cells_count = 0  # 줄바꿈이 포함된 셀 수 추적
        
        for i, line in enumerate(lines[1:], 1):
            try:
                print(f"처리 중인 행 {i}: {line[:100]}...")
                
                # CSV reader를 사용해서 파싱 시도
                try:
                    parsed_row = list(csv.reader([line]))[0]
                    print(f"  CSV reader로 파싱 성공: {len(parsed_row)}개 컬럼")
                    
                    # 컬럼 개수 맞추기
                    while len(parsed_row) < expected_columns:
                        parsed_row.append('')
                    if len(parsed_row) > expected_columns:
                        parsed_row = parsed_row[:expected_columns]
                    
                    # 줄바꿈이 포함된 셀 확인 및 처리
                    corrected_row = []
                    for j, cell in enumerate(parsed_row):
                        has_newline = '\n' in cell or '\r' in cell
                        if has_newline:
                            newline_cells_count += 1
                            print(f"    셀 {j}: 줄바꿈 포함 - 길이: {len(cell)}")
                        
                        # 쉼표나 줄바꿈이 포함된 셀을 자동으로 큰따옴표로 감싸기
                        if (',' in cell or '\n' in cell or '\r' in cell) and not (cell.startswith('"') and cell.endswith('"')):
                            cell = f'"{cell}"'
                        
                        # 인용부호가 제대로 닫히지 않은 경우 처리
                        if cell.count('"') % 2 != 0:
                            cell = cell.replace('"', '""')
                        
                        corrected_row.append(cell)
                    
                    corrected_lines.append(','.join(corrected_row))
                    
                except Exception as csv_error:
                    print(f"  CSV reader 파싱 실패: {csv_error}")
                    
                    # 수동 파싱으로 대체
                    row = []
                    current_cell = ""
                    in_quotes = False
                    char_index = 0
                    
                    while char_index < len(line):
                        char = line[char_index]
                        
                        if char == '"':
                            if in_quotes and char_index + 1 < len(line) and line[char_index + 1] == '"':
                                # 이스케이프된 따옴표
                                current_cell += '"'
                                char_index += 2  # 두 개의 따옴표를 건너뛰기
                                continue
                            else:
                                # 따옴표 시작/끝
                                in_quotes = not in_quotes
                        elif char == ',' and not in_quotes:
                            # 쉼표 (따옴표 밖에서만)
                            row.append(current_cell)
                            current_cell = ""
                        else:
                            current_cell += char
                        
                        char_index += 1
                    
                    # 마지막 셀 추가
                    row.append(current_cell)
                    
                    print(f"  수동 파싱 결과: {len(row)}개 컬럼")
                    
                    # 컬럼 개수 맞추기
                    while len(row) < expected_columns:
                        row.append('')
                    if len(row) > expected_columns:
                        row = row[:expected_columns]
                    
                    # 줄바꿈이 포함된 셀 확인 및 처리
                    corrected_row = []
                    for j, cell in enumerate(row):
                        has_newline = '\n' in cell or '\r' in cell
                        if has_newline:
                            newline_cells_count += 1
                            print(f"    셀 {j}: 줄바꿈 포함 - 길이: {len(cell)}")
                        
                        # 쉼표나 줄바꿈이 포함된 셀을 자동으로 큰따옴표로 감싸기
                        if (',' in cell or '\n' in cell or '\r' in cell) and not (cell.startswith('"') and cell.endswith('"')):
                            cell = f'"{cell}"'
                        
                        # 인용부호가 제대로 닫히지 않은 경우 처리
                        if cell.count('"') % 2 != 0:
                            cell = cell.replace('"', '""')
                        
                        corrected_row.append(cell)
                    
                    corrected_lines.append(','.join(corrected_row))
                
            except Exception as e:
                print(f"행 {i} 처리 중 오류: {e}")
                # 오류가 발생한 행은 건너뛰기
                continue
        
        print(f"총 {newline_cells_count}개의 셀에 줄바꿈 문자가 포함되어 있었습니다.")
        
        # 보정된 CSV를 StringIO로 반환
        corrected_content = '\n'.join(corrected_lines)
        output = StringIO(corrected_content)
        output.seek(0)
        return output
        
    except Exception as e:
        raise ValueError(f"CSV 보정 중 오류: {str(e)}")


def auto_correct_csv(file):
    """CSV 파일을 자동으로 보정합니다."""
    try:
        # 파일을 텍스트로 읽기
        content = file.read().decode('utf-8')
        return auto_correct_csv_from_content(content)
    except Exception as e:
        raise ValueError(f"CSV 보정 중 오류: {str(e)}")


@api_view(['POST'])
def upload_questions(request):
    """CSV, XLS, XLSX 파일에서 문제를 업로드합니다."""
    if 'file' not in request.FILES:
        return Response({'error': '파일이 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
    
    file = request.FILES['file']
    allowed_extensions = ['.csv', '.xls', '.xlsx']
    file_extension = os.path.splitext(file.name)[1].lower()
    
    print(f"파일 확장자: {file_extension}")
    print(f"허용된 확장자: {allowed_extensions}")
    
    if file_extension not in allowed_extensions:
        return Response({'error': 'CSV, XLS, XLSX 파일만 업로드 가능합니다.'}, status=status.HTTP_400_BAD_REQUEST)
    
    # 기존 파일 확인 및 경고 (파일 시스템 기반)
    existing_file_path = os.path.join(QUESTION_FILES_DIR, file.name)
    existing_metadata_path = os.path.join(QUESTION_FILES_DIR, f"{file.name}.json")
    
    if os.path.exists(existing_file_path):
        # 기존 파일이 존재하는 경우 경고 메시지와 함께 업로드 허용
        warning_message = f"경고: '{file.name}' 파일이 이미 존재합니다. 업로드하면 기존 파일이 덮어쓰기됩니다."
        print(f"[upload_questions] {warning_message}")
        
        # 기존 메타데이터가 있으면 읽어서 공개 여부 확인
        existing_is_public = True  # 기본값은 공개
        if os.path.exists(existing_metadata_path):
            try:
                import json
                with open(existing_metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    existing_is_public = metadata.get('is_public', True)
            except Exception as e:
                print(f"[upload_questions] 기존 메타데이터 읽기 실패: {e}")
        
        print(f"[upload_questions] 기존 파일 발견: {file.name} (공개: {existing_is_public})")
    
    # is_public 파라미터 확인
    is_public = request.POST.get('is_public', 'true').lower() == 'true'
    print(f"[upload_questions] 파일 공개 설정: {is_public}")
    
    # tags 파라미터 확인
    tags_from_post = request.POST.getlist('tags[]') or request.POST.getlist('tags')
    tag_ids = []
    if tags_from_post:
        tag_ids = [int(tid) for tid in tags_from_post if tid.isdigit()]
        print(f"[upload_questions] 태그 설정: {tag_ids}")
    
    # 파일 저장 (문제 파일 관리용)
    from django.core.files.storage import default_storage
    from django.conf import settings
    
    # MinIO를 사용하는 경우와 로컬 스토리지를 사용하는 경우를 구분
    use_minio = getattr(settings, 'USE_MINIO', False)
    print(f"[upload_questions] USE_MINIO: {use_minio}")
    print(f"[upload_questions] settings.USE_MINIO: {getattr(settings, 'USE_MINIO', 'NOT_SET')}")
    print(f"[upload_questions] os.environ.get('USE_MINIO'): {os.environ.get('USE_MINIO', 'NOT_SET')}")
    print(f"[upload_questions] AWS_S3_ENDPOINT_URL: {getattr(settings, 'AWS_S3_ENDPOINT_URL', 'NOT_SET')}")
    print(f"[upload_questions] AWS_STORAGE_BUCKET_NAME: {getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'NOT_SET')}")
    print(f"[upload_questions] DEFAULT_FILE_STORAGE: {getattr(settings, 'DEFAULT_FILE_STORAGE', 'NOT_SET')}")
    
    if use_minio:
        # MinIO 스토리지에 저장 시도
        try:
            # 기존 파일이 있으면 먼저 삭제
            import boto3
            from botocore.exceptions import ClientError
            
            s3_client = boto3.client(
                's3',
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                verify=False
            )
            
            # 기존 파일 삭제 시도
            try:
                s3_client.delete_object(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Key=f'data/{file.name}'
                )
                print(f"[upload_questions] 기존 파일 삭제됨: data/{file.name}")
            except ClientError as e:
                if e.response['Error']['Code'] != 'NoSuchKey':
                    print(f"[upload_questions] 기존 파일 삭제 실패 (무시): {e}")
            
            # 메타데이터 파일도 삭제 시도
            try:
                s3_client.delete_object(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Key=f'data/{file.name}.json'
                )
                print(f"[upload_questions] 기존 메타데이터 삭제됨: data/{file.name}.json")
            except ClientError as e:
                if e.response['Error']['Code'] != 'NoSuchKey':
                    print(f"[upload_questions] 기존 메타데이터 삭제 실패 (무시): {e}")
            
            # 새 파일 저장
            print(f"[upload_questions] MinIO 저장 시도: {file.name}")
            saved_path = default_storage.save(file.name, file)
            print(f"MinIO에 파일 저장됨: {saved_path}")
        except Exception as e:
            print(f"MinIO 저장 실패, 로컬 스토리지로 폴백: {e}")
            print(f"[upload_questions] 에러 타입: {type(e)}")
            import traceback
            print(f"[upload_questions] 스택 트레이스: {traceback.format_exc()}")
            # MinIO 실패 시 로컬 스토리지로 폴백
            os.makedirs(QUESTION_FILES_DIR, exist_ok=True)
            file_path = os.path.join(QUESTION_FILES_DIR, file.name)
            with open(file_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            print(f"로컬에 파일 저장됨 (폴백): {file_path}")
    else:
        # 로컬 스토리지에 저장
        os.makedirs(QUESTION_FILES_DIR, exist_ok=True)
        file_path = os.path.join(QUESTION_FILES_DIR, file.name)
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        print(f"로컬에 파일 저장됨: {file_path}")
    
    try:
        # 파일 정보 디버깅
        print(f"파일 이름: {file.name}")
        print(f"파일 크기: {file.size}")
        print(f"파일 타입: {file.content_type}")
        
        # 파일 내용을 먼저 읽어서 저장
        file.seek(0)  # 파일 포인터를 처음으로 되돌림
        
        print(f"파일 확장자 체크: {file_extension}")
        print(f"CSV 처리 여부: {file_extension == '.csv'}")
        
        # 파일 확장자에 따라 다른 처리
        if file_extension == '.csv':
            # CSV 파일 처리
            try:
                file_content = file.read().decode('utf-8')
            except UnicodeDecodeError:
                # UTF-8로 읽기 실패시 다른 인코딩 시도
                file.seek(0)
                file_content = file.read().decode('latin-1')
            
            print(f"CSV 파일 내용 길이: {len(file_content)}")
            print(f"CSV 파일 내용 처음 200자: {file_content[:200]}")
            
            # 파일이 비어있으면 에러
            if not file_content.strip():
                return Response({'error': '업로드된 파일이 비어있습니다.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # CSV 자동 보정
            corrected_file = auto_correct_csv_from_content(file_content)
            
            # 보정된 파일로 pandas 읽기
            df = pd.read_csv(corrected_file)
        else:
            # XLS, XLSX 파일 처리
            print(f"엑셀 파일 처리: {file.name}, 확장자: {file_extension}")
            
            try:
                if file_extension == '.xlsx':
                    print("XLSX 파일 읽기 시도 (openpyxl 엔진)")
                    df = pd.read_excel(file, engine='openpyxl')
                else:  # .xls
                    print("XLS 파일 읽기 시도 (xlrd 엔진)")
                    df = pd.read_excel(file, engine='xlrd')
                
                print(f"엑셀 파일 읽기 성공. 컬럼: {list(df.columns)}")
                print(f"데이터 행 수: {len(df)}")
            except Exception as e:
                print(f"엑셀 파일 읽기 실패: {str(e)}")
                import traceback
                traceback.print_exc()
                return Response({'error': f'엑셀 파일 읽기 실패: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        print(f"CSV 읽기 성공. 컬럼: {list(df.columns)}")
        print(f"데이터 행 수: {len(df)}")
        
        # 컬럼명 매핑 (한글 ↔ 영어)
        column_mapping = {
            # 필수 컬럼
            '문제id': ['문제id', 'Question ID', 'question_id', 'questionid'],
            '제목': ['제목', 'Title', 'title'],
            '문제 내용': ['문제 내용', 'Question Content', 'question_content', 'content'],
            '정답': ['정답', 'Answer', 'answer'],
            # 선택적 컬럼
            '설명': ['설명', 'Explanation', 'explanation'],
            '난이도': ['난이도', 'Difficulty', 'difficulty', 'level'],
            'URL': ['URL', 'url', 'link'],
            'Group ID': ['Group ID', 'group_id', 'groupid', 'groupId']
        }
        
        # 실제 컬럼명 찾기
        actual_columns = {}
        print(f"[upload_questions] 파일의 컬럼들: {list(df.columns)}")
        for key, possible_names in column_mapping.items():
            found = False
            for name in possible_names:
                if name in df.columns:
                    actual_columns[key] = name
                    found = True
                    print(f"[upload_questions] 컬럼 매핑 성공: {key} -> {name}")
                    break
            if not found:
                print(f"[upload_questions] 컬럼 매핑 실패: {key} (찾은 이름들: {possible_names})")
                if key in ['문제id', '제목', '문제 내용', '정답']:  # 필수 컬럼인 경우
                    return Response({
                        'error': f'필수 컬럼이 누락되었습니다: {key}',
                        'available_columns': list(df.columns),
                        'expected_columns': [name for name in possible_names]
                    }, status=status.HTTP_400_BAD_REQUEST)

        numeric_ids = pd.to_numeric(df[actual_columns['문제id']], errors='coerce')
        max_id = 0
        if hasattr(numeric_ids, 'max'):
            max_numeric = numeric_ids.max()
            if isinstance(max_numeric, (int, float)) and pd.notna(max_numeric):
                max_id = int(max_numeric)
        next_id = max_id + 1
        for idx, row in df.iterrows():
            val = row[actual_columns['문제id']]
            if pd.isna(val) or str(val).strip().lower() in ['nan', 'none', '']:
                df.at[idx, actual_columns['문제id']] = next_id
                next_id += 1

        created_count = 0
        updated_count = 0
        failed_count = 0
        skipped_count = 0
        total_rows = len(df)
        print(f"[upload_questions] 총 처리할 행 수: {total_rows}개")
        
        # 데이터 검증 및 중복 검사
        print("[upload_questions] 데이터 검증 시작...")
        unique_data = set()
        duplicate_rows = []
        
        for index, row in df.iterrows():
            # 데이터 검증
            title = str(row[actual_columns['제목']]).strip()
            content = str(row[actual_columns['문제 내용']]).strip()
            answer = str(row[actual_columns['정답']]).strip()
            csv_id = str(row[actual_columns['문제id']]).strip()
            
            # 필수 필드 검증
            if not title or title.lower() in ['nan', 'none', '']:
                print(f"  -> 행 {index + 1}: 제목이 비어있음, 건너뜀")
                skipped_count += 1
                continue
                
            if not content or content.lower() in ['nan', 'none', '']:
                print(f"  -> 행 {index + 1}: 내용이 비어있음, 건너뜀")
                skipped_count += 1
                continue
                
            if not answer or answer.lower() in ['nan', 'none', '']:
                print(f"  -> 행 {index + 1}: 답안이 비어있음, 건너뜀")
                skipped_count += 1
                continue
            
            # 중복 검사
            data_key = (csv_id, title, content, answer)
            if data_key in unique_data:
                print(f"  -> 행 {index + 1}: 중복 데이터 발견, 건너뜀")
                print(f"     CSV_ID: {csv_id}, 제목: {title[:30]}...")
                duplicate_rows.append(index + 1)
                skipped_count += 1
                continue
            else:
                unique_data.add(data_key)
        
        print(f"[upload_questions] 데이터 검증 완료:")
        print(f"  - 중복 제거 후 처리할 행 수: {len(unique_data)}개")
        print(f"  - 건너뛴 행 수: {skipped_count}개")
        if duplicate_rows:
            print(f"  - 중복된 행 번호: {duplicate_rows}")
        
        # 파일명 + 제목 기준으로 기존 문제 확인 (업데이트 모드)
        print(f"[upload_questions] 파일명({file.name}) + 제목 기준으로 기존 문제 확인...")
        
        # 이번 업로드에서 처리할 모든 제목들을 미리 수집
        titles_to_check = []
        for index, row in df.iterrows():
            title = str(row[actual_columns['제목']]).strip()
            if title and title.lower() not in ['nan', 'none', '']:
                titles_to_check.append(title)
        
        # 같은 파일명으로 업로드된 기존 문제들을 제목으로 매핑
        file_base_name = os.path.splitext(file.name)[0]
        # 다국어 필드로 검색하기 위해 모든 언어 필드 확인
        from django.db.models import Q
        from ..utils.multilingual_utils import SUPPORTED_LANGUAGES
        title_filters = Q()
        for lang in SUPPORTED_LANGUAGES:
            title_filters |= Q(**{f'title_{lang}__in': titles_to_check})
        existing_questions = Question.objects.filter(
            csv_id=file_base_name,  # 파일명만으로 필터링
        ).filter(title_filters)
        # 첫 번째 언어 필드로 매핑 (기존 로직 유지)
        existing_map = {}
        for q in existing_questions:
            for lang in SUPPORTED_LANGUAGES:
                title = getattr(q, f'title_{lang}', None)
                if title and title in titles_to_check:
                    existing_map[title] = q
                    break
        
        if existing_questions.exists():
            update_mode = True
            print(f"[upload_questions] 같은 파일명 + 제목의 기존 문제 {len(existing_questions)}개 발견 - 업데이트 모드")
        else:
            update_mode = False
            print(f"[upload_questions] 같은 파일명 + 제목의 기존 문제 없음 - 신규 생성 모드")
        
        # 실제 문제 생성
        for index, row in df.iterrows():
            # 이미 검증된 데이터만 처리
            title = str(row[actual_columns['제목']]).strip()
            content = str(row[actual_columns['문제 내용']]).strip()
            answer = str(row[actual_columns['정답']]).strip()
            csv_id = str(row[actual_columns['문제id']]).strip()
            
            # 필수 필드 재검증
            if not title or title.lower() in ['nan', 'none', '']:
                continue
            if not content or content.lower() in ['nan', 'none', '']:
                continue
            if not answer or answer.lower() in ['nan', 'none', '']:
                continue
            
            # 중복 재검증
            data_key = (csv_id, title, content, answer)
            if data_key not in unique_data:
                continue
            
            print(f"처리 중인 행 {index + 1}: {title[:50]}...")
            
            # csv_id 설정 (엑셀의 문제 순서 번호)
            csv_id = str(row[actual_columns['문제id']]).strip()
            
            # source_id 설정 (엑셀 파일명으로 출처 기록)
            source_id = file.name
            
            # 기본 필드들 (csv_id와 source_id만 설정, content/answer는 다국어 필드로 직접 설정)
            defaults = {
                'csv_id': csv_id,      # 엑셀의 문제 순서 번호
                'source_id': source_id # 엑셀 파일명 (출처 식별용)
            }
            
            # 선택적 필드들 (CSV에 있는 경우에만)
            explanation = None
            if '설명' in actual_columns:
                explanation = str(row[actual_columns['설명']]).strip()
                if explanation and explanation.lower() not in ['nan', 'none', '']:
                    # explanation은 다국어 필드로 직접 설정하므로 defaults에 추가하지 않음
                    pass
            if '난이도' in actual_columns:
                difficulty_value = row[actual_columns['난이도']]
                if pd.notna(difficulty_value) and str(difficulty_value).strip() not in ['nan', 'none', '']:
                    print(f"  -> 난이도 값: {difficulty_value} (타입: {type(difficulty_value)})")
                    defaults['difficulty'] = str(difficulty_value).strip()
            if 'URL' in actual_columns:
                url = str(row[actual_columns['URL']]).strip()
                if url and url.lower() not in ['nan', 'none', '']:
                    defaults['url'] = url
            if 'Group ID' in actual_columns:
                group_id = str(row[actual_columns['Group ID']]).strip()
                if group_id and group_id.lower() not in ['nan', 'none', '']:
                    defaults['group_id'] = group_id
            
            try:
                # 기존 문제가 있는지 확인 (업데이트 모드)
                if update_mode and title in existing_map:
                    # 기존 문제 업데이트
                    question = existing_map[title]
                    # 백업용 title 필드는 더 이상 사용하지 않음
                    # question.title = title  # 제거 예정
                    # 다국어 필드 사용 (기존 필드는 제거 예정)
                    question.content_ko = content
                    question.answer_ko = answer
                    if explanation:
                        question.explanation_ko = explanation
                    if 'difficulty' in defaults:
                        question.difficulty = defaults['difficulty']
                    if 'url' in defaults:
                        question.url = defaults['url']
                    if 'group_id' in defaults:
                        question.group_id = defaults['group_id']
                    
                    # =============================================================================
                    # 🎯 다국어 필드 업데이트 - 사용자 프로필 언어 기반
                    # =============================================================================
                    # 중요: 무조건 사용자의 프로필 언어를 기준으로 모든 처리가 이루어져야 함
                    # - 영어 사용자: title_en, content_en, answer_en, explanation_en 필드에 저장
                    # - 한국어 사용자: title_ko, content_ko, answer_ko, explanation_ko 필드에 저장
                    # - created_language, is_ko_complete, is_en_complete 자동 설정
                    # =============================================================================
                    
                    # 사용자 프로필 언어 확인 (기본값: ko)
                    from quiz.utils.multilingual_utils import BASE_LANGUAGE
                    user_language = BASE_LANGUAGE
                    try:
                        if hasattr(request.user, 'userprofile'):
                            user_language = request.user.userprofile.language
                        elif hasattr(request.user, 'profile'):
                            user_language = request.user.profile.language
                        logger.info(f"[upload_questions] 사용자 언어 감지: {request.user.username} -> {user_language}")
                    except Exception as e:
                        logger.warning(f"[upload_questions] 사용자 언어 감지 실패: {e}, 기본값 'en' 사용")
                    
                    # 사용자 언어에 맞는 필드에 동적으로 저장
                    # Question 모델에 해당 언어 필드가 있는지 확인
                    title_field = f'title_{user_language}'
                    if not hasattr(question, title_field):
                        # 필드가 없으면 BASE_LANGUAGE로 폴백
                        user_language = BASE_LANGUAGE
                    
                    # 동적으로 필드 설정
                    setattr(question, f'title_{user_language}', title)
                    setattr(question, f'content_{user_language}', content)
                    setattr(question, f'answer_{user_language}', answer)
                    if explanation:
                        setattr(question, f'explanation_{user_language}', explanation)
                    
                    # 완성도 필드 업데이트 (동적으로 처리)
                    # Question 모델에 존재하는 모든 완성도 필드를 동적으로 확인
                    completion_field_name = f'is_{user_language}_complete'
                    if hasattr(question, completion_field_name):
                        setattr(question, completion_field_name, True)
                    
                    question.created_language = user_language
                    question.save()
                    
                    print(f"  -> 기존 문제 업데이트됨: {title[:30]}")
                    updated_count += 1
                else:
                    # 새로운 문제 생성
                    # 백업용 title 필드는 더 이상 사용하지 않음
                    # question = Question.objects.create(title=title, **defaults)  # 제거 예정
                    question = Question.objects.create(**defaults)
                    
                    # =============================================================================
                    # 🎯 다국어 필드 설정 - 사용자 프로필 언어 기반
                    # =============================================================================
                    # 중요: 무조건 사용자의 프로필 언어를 기준으로 모든 처리가 이루어져야 함
                    # - 영어 사용자: title_en, content_en, answer_en, explanation_en 필드에 저장
                    # - 한국어 사용자: title_ko, content_ko, answer_ko, explanation_ko 필드에 저장
                    # - created_language, is_ko_complete, is_en_complete 자동 설정
                    # =============================================================================
                    
                    # 사용자 프로필 언어 확인 (기본값: ko)
                    from quiz.utils.multilingual_utils import BASE_LANGUAGE
                    user_language = BASE_LANGUAGE
                    try:
                        if hasattr(request.user, 'userprofile'):
                            user_language = request.user.userprofile.language
                        elif hasattr(request.user, 'profile'):
                            user_language = request.user.profile.language
                        logger.info(f"[upload_questions] 사용자 언어 감지: {request.user.username} -> {user_language}")
                    except Exception as e:
                        logger.warning(f"[upload_questions] 사용자 언어 감지 실패: {e}, 기본값 'en' 사용")
                    
                    # 사용자 언어에 맞는 필드에 동적으로 저장
                    # Question 모델에 해당 언어 필드가 있는지 확인
                    title_field = f'title_{user_language}'
                    if not hasattr(question, title_field):
                        # 필드가 없으면 BASE_LANGUAGE로 폴백
                        user_language = BASE_LANGUAGE
                    
                    # 동적으로 필드 설정
                    setattr(question, f'title_{user_language}', title)
                    setattr(question, f'content_{user_language}', content)
                    setattr(question, f'answer_{user_language}', answer)
                    if explanation:
                        setattr(question, f'explanation_{user_language}', explanation)
                    
                    # 완성도 필드 업데이트 (동적으로 처리)
                    # Question 모델에 존재하는 모든 완성도 필드를 동적으로 확인
                    completion_field_name = f'is_{user_language}_complete'
                    if hasattr(question, completion_field_name):
                        setattr(question, completion_field_name, True)
                    
                    question.created_language = user_language
                    question.save()
                    
                    print(f"  -> 새 문제 생성됨: {title[:30]}")
                    created_count += 1
                
                # 문제 생성/업데이트 후 자동 번역 처리 (content는 선택지이므로 번역 제외)
                try:
                    from ..utils.multilingual_utils import MultilingualContentManager
                    # 번역 처리 (title, answer, explanation 필드만 번역, content는 제외)
                    # 생성/업데이트 시에는 완성도 상태 업데이트 필요 (skip_completion_update=False, 기본값)
                    manager = MultilingualContentManager(question, request.user, ['title', 'answer', 'explanation'])
                    manager.handle_multilingual_update()
                    # 번역 후 문제 다시 조회
                    question.refresh_from_db()
                    logger.info(f"[UPLOAD_QUESTIONS] 문제 {question.id} 자동 번역 완료 (content 제외)")
                except Exception as e:
                    logger.warning(f"[UPLOAD_QUESTIONS] 문제 {question.id} 자동 번역 실패: {str(e)}")
                
                # unique_data에서 처리된 항목 제거 (중복 방지)
                unique_data.discard(data_key)
                
            except Exception as e:
                failed_count += 1
                print(f"  -> 행 {index + 1} 처리 중 오류: {e}")
                continue
        
        print(f"[upload_questions] 처리 결과 요약:")
        print(f"  - 총 행 수: {total_rows}개")
        print(f"  - 새로 생성: {created_count}개")
        print(f"  - 업데이트: {updated_count}개")
        print(f"  - 건너뜀: {skipped_count}개")
        print(f"  - 실패: {failed_count}개")
        total_processed = created_count + updated_count
        if total_processed > 0:
            print(f"  - 성공률: {(total_processed / total_rows * 100):.1f}%")
        if duplicate_rows:
            print(f"  - 중복 제거됨: {len(duplicate_rows)}개")
        
        # 파일 메타데이터 저장 (문제 수 포함)
        question_count = created_count + updated_count  # 생성된 문제 수 + 업데이트된 문제 수
        print(f"[upload_questions] 계산된 문제 수: {question_count}개")
        
        # 태그 유효성 검증
        valid_tag_ids = []
        if tag_ids:
            try:
                from ..models import Tag
                for tag_id in tag_ids:
                    try:
                        tag = Tag.objects.get(id=tag_id)
                        valid_tag_ids.append(tag_id)
                        user_lang = get_user_language(request)
                        tag_name = get_localized_field(tag, 'name', user_lang, '')
                        print(f"[upload_questions] 유효한 태그 ID: {tag_id} ({tag_name})")
                    except Tag.DoesNotExist:
                        print(f"[upload_questions] 존재하지 않는 태그 ID: {tag_id}")
            except Exception as e:
                print(f"[upload_questions] 태그 유효성 검증 실패: {e}")
        
        metadata = {
            'is_public': is_public,  # 사용자가 설정한 공개 여부
            'question_count': question_count,
            'uploaded_at': timezone.now().isoformat(),
            'uploaded_by': request.user.username if request.user.is_authenticated else 'anonymous',
            'tags': valid_tag_ids if valid_tag_ids else []  # 태그 ID 목록
        }
        print(f"[upload_questions] 메타데이터 생성: {metadata}")
        
        # QuestionFile 모델은 삭제되었으므로 파일 시스템 기반 메타데이터만 저장
        print(f"[upload_questions] 파일 시스템 기반 메타데이터 저장: {file.name}")
        
        # MinIO 또는 로컬 스토리지에 메타데이터 저장
        if use_minio:
            try:
                import json
                import boto3
                metadata_json = json.dumps(metadata, ensure_ascii=False)
                s3_client = boto3.client(
                    's3',
                    endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    verify=False
                )
                s3_client.put_object(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Key=f'data/{file.name}.json',
                    Body=metadata_json.encode('utf-8'),
                    ContentType='application/json'
                )
                print(f"MinIO에 메타데이터 저장됨: data/{file.name}.json")
            except Exception as e:
                print(f"MinIO 메타데이터 저장 실패: {e}")
                print(f"[upload_questions] 에러 타입: {type(e)}")
                import traceback
                print(f"[upload_questions] 스택 트레이스: {traceback.format_exc()}")
        else:
            # 로컬 스토리지에 메타데이터 저장
            import json
            metadata_file = os.path.join(QUESTION_FILES_DIR, f"{file.name}.json")
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            print(f"로컬에 메타데이터 저장됨: {metadata_file}")
        
        if updated_count > 0:
            message = f'{created_count}개 문제 생성, {updated_count}개 문제 업데이트되었습니다.'
        else:
            message = f'{created_count}개의 문제가 업로드되었습니다.'
        if skipped_count > 0:
            message += f' ({skipped_count}개 건너뜀)'
        if duplicate_rows:
            message += f' (중복 {len(duplicate_rows)}개 제거됨)'
        message += ' (데이터 검증 및 중복 제거 적용됨)'
        
        return Response({
            'message': message,
            'total_questions': Question.objects.count(),
            'file_question_count': question_count,
            'created_count': created_count,
            'skipped_count': skipped_count,
            'failed_count': failed_count
        })
    
    except Exception as e:
        print(f"업로드 에러: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_questions(request):
    """모든 문제를 조회합니다."""
    questions = Question.objects.all()
    serializer = QuestionSerializer(questions, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def get_question_statistics_by_title(request, title):
    """제목 기반으로 문제 통계를 취합하여 반환합니다."""
    if not request.user.is_authenticated:
        return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)
    
    # 사용자 언어 확인
    from quiz.utils.multilingual_utils import BASE_LANGUAGE, SUPPORTED_LANGUAGES
    from django.db import models
    user_language = BASE_LANGUAGE  # 기본값
    try:
        if hasattr(request.user, 'userprofile'):
            user_language = request.user.userprofile.language
        elif hasattr(request.user, 'profile'):
            user_language = request.user.profile.language
    except Exception:
        pass
    
    # 사용자 언어에 맞는 제목 필드로 문제 찾기
    # 1. 사용자 언어로 먼저 검색
    # 2. 없으면 BASE_LANGUAGE로 검색
    # 3. 그래도 없으면 모든 지원 언어에서 검색
    questions = Question.objects.none()
    
    # 사용자 언어로 검색
    if user_language in SUPPORTED_LANGUAGES:
        questions = Question.objects.filter(**{f'title_{user_language}': title})
    
    # 사용자 언어로 찾지 못했고, BASE_LANGUAGE와 다르면 BASE_LANGUAGE로 검색
    if not questions.exists() and user_language != BASE_LANGUAGE:
        questions = Question.objects.filter(**{f'title_{BASE_LANGUAGE}': title})
    
    # 그래도 없으면 모든 지원 언어에서 검색
    if not questions.exists():
        q_objects = models.Q()
        for lang in SUPPORTED_LANGUAGES:
            q_objects |= models.Q(**{f'title_{lang}': title})
        questions = Question.objects.filter(q_objects)
    
    if not questions.exists():
        return Response({'error': '해당 제목의 문제를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    
    total_attempts = 0
    total_correct = 0
    question_details = []
    
    for question in questions:
        # 해당 문제의 시험 결과들
        results = ExamResultDetail.objects.filter(
            question=question,
            result__user=request.user
        )
        
        question_attempts = results.count()
        question_correct = results.filter(is_correct=True).count()
        
        total_attempts += question_attempts
        total_correct += question_correct
        
        question_details.append({
            'question_id': question.id,
            'csv_id': question.csv_id,
            'group_id': question.group_id,
            'difficulty': question.difficulty,
            'attempts': question_attempts,
            'correct': question_correct,
            'accuracy': question_correct / question_attempts if question_attempts > 0 else 0
        })
    
    overall_accuracy = total_correct / total_attempts if total_attempts > 0 else 0
    
    return Response({
        'title': title,
        'total_questions': questions.count(),
        'total_attempts': total_attempts,
        'total_correct': total_correct,
        'overall_accuracy': overall_accuracy,
        'question_details': question_details
    })


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([AllowAny])  # GET 요청은 unauthenticated 사용자도 허용
def get_question(request, question_id):
    """특정 문제를 조회, 수정하거나 삭제합니다."""
    print(f"get_question 호출됨 - question_id: {question_id}, type: {type(question_id)}")
    print(f"요청 메서드: {request.method}")
    
    # PATCH와 DELETE는 인증 필요
    if request.method in ['PATCH', 'DELETE'] and not request.user.is_authenticated:
        return Response({
            'error': '이 작업을 수행하려면 로그인이 필요합니다.',
            'requires_login': True
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        # 먼저 UUID로 시도
        try:
            question = Question.objects.get(id=question_id)
            print(f"UUID로 문제 찾음: {question.id}")
        except (Question.DoesNotExist, ValueError) as e:
            print(f"UUID로 찾을 수 없음: {e}")
            # UUID가 아니거나 찾을 수 없으면 csv_id로 시도
            # csv_id가 float로 저장되어 있을 수 있으므로 문자열로 변환하여 비교
            try:
                # 숫자인 경우 float로 변환하여 비교
                csv_id_float = float(question_id)
                print(f"float로 변환: {csv_id_float}")
                question = Question.objects.get(csv_id=csv_id_float)
                print(f"float csv_id로 문제 찾음: {question.id}")
            except (ValueError, Question.DoesNotExist) as e:
                print(f"float csv_id로도 찾을 수 없음: {e}")
                # 문자열로 직접 비교
                question = Question.objects.get(csv_id=question_id)
                print(f"문자열 csv_id로 문제 찾음: {question.id}")
        
        if request.method == 'GET':
            # 사용자 언어 확인
            from quiz.utils.multilingual_utils import BASE_LANGUAGE
            user_language = BASE_LANGUAGE  # 기본값
            try:
                if hasattr(request.user, 'userprofile'):
                    user_language = request.user.userprofile.language
                elif hasattr(request.user, 'profile'):
                    user_language = request.user.profile.language
            except Exception:
                pass
            
            # 번역이 필요한지 확인하고 자동 번역 수행
            translation_needed = False
            # 사용자 언어에 해당하는 필드가 비어있는지 동적으로 확인
            title_field = getattr(question, f'title_{user_language}', None)
            content_field = getattr(question, f'content_{user_language}', None)
            answer_field = getattr(question, f'answer_{user_language}', None)
            
            if not title_field or not content_field or not answer_field:
                translation_needed = True
            
            if translation_needed:
                try:
                    from ..utils.multilingual_utils import MultilingualContentManager
                    # 번역 처리 (조회 시에는 완성도 상태 업데이트를 건너뛰기)
                    manager = MultilingualContentManager(question, request.user, skip_completion_update=True)
                    manager.handle_multilingual_update()
                    # 번역 후 문제 다시 조회
                    question.refresh_from_db()
                    logger.info(f"[AUTO_TRANSLATION] 문제 {question.id} 자동 번역 완료")
                except Exception as e:
                    logger.warning(f"[AUTO_TRANSLATION] 문제 {question.id} 자동 번역 실패: {str(e)}")
            
            serializer = QuestionSerializer(question, context={'request': request})
            return Response(serializer.data)
        elif request.method == 'PATCH':
            # 관리자 권한 확인
            print(f"=== PATCH 요청 처리 시작 ===")
            print(f"현재 사용자: {request.user}")
            print(f"사용자 인증 여부: {request.user.is_authenticated}")
            print(f"요청 데이터: {request.data}")
            
            if not request.user.is_authenticated:
                print("사용자가 인증되지 않음")
                return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)
            
            # 권한 확인: 관리자, 스터디 관리자, 또는 생성자
            from quiz.utils.permissions import has_any_admin_permission, has_study_admin_permission
            has_permission = has_any_admin_permission(request.user) or has_study_admin_permission(request.user)
            
            # 3. 생성자 권한 확인 (문제가 속한 시험의 생성자인지)
            if not has_permission:
                from quiz.models import Exam, ExamQuestion
                # 문제가 속한 시험들 중 하나라도 생성자인지 확인
                user_exams = Exam.objects.filter(
                    created_by=request.user,
                    examquestion__question=question
                ).distinct()
                if user_exams.exists():
                    has_permission = True
            
            if not has_permission:
                print(f"권한 없음. 사용자: {request.user.username}")
                return Response({'error': '관리자, 스터디 관리자 또는 생성자 권한이 필요합니다.'}, status=status.HTTP_403_FORBIDDEN)
            
            print("관리자 권한 확인됨, 시리얼라이저 검증 시작")
            print(f"요청 데이터: {request.data}")
            serializer = QuestionSerializer(question, data=request.data, partial=True, context={'request': request})
            if serializer.is_valid():
                print("시리얼라이저 검증 성공, 저장 중...")
                serializer.save()
                print("저장 완료")
                return Response(serializer.data)
            else:
                print(f"시리얼라이저 검증 실패: {serializer.errors}")
                return Response({
                    'error': '데이터 검증 실패',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'DELETE':
            # 관리자 권한 확인
            print(f"현재 사용자: {request.user}")
            print(f"사용자 인증 여부: {request.user.is_authenticated}")
            
            if not request.user.is_authenticated:
                return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)
            
            # 권한 확인: 관리자, 스터디 관리자, 또는 생성자
            from quiz.utils.permissions import has_any_admin_permission, has_study_admin_permission
            has_permission = has_any_admin_permission(request.user) or has_study_admin_permission(request.user)
            
            # 3. 생성자 권한 확인 (문제가 속한 시험의 생성자인지)
            if not has_permission:
                from quiz.models import Exam, ExamQuestion
                # 문제가 속한 시험들 중 하나라도 생성자인지 확인
                user_exams = Exam.objects.filter(
                    created_by=request.user,
                    examquestion__question=question
                ).distinct()
                if user_exams.exists():
                    has_permission = True
            
            if not has_permission:
                return Response({'error': '관리자, 스터디 관리자 또는 생성자 권한이 필요합니다.'}, status=status.HTTP_403_FORBIDDEN)
            
            # 문제 제목 저장 (삭제 후 사용)
            user_lang = get_user_language(request)
            question_title = get_localized_field(question, 'title', user_lang, '제목 없음')
            
            # 문제 삭제
            question.delete()
            
            return Response({
                'message': f'문제 "{question_title}"이(가) 성공적으로 삭제되었습니다.'
            }, status=status.HTTP_200_OK)
                
    except Question.DoesNotExist:
        return Response({'error': '문제를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
def delete_question(request, question_id):
    """단일 문제를 삭제합니다."""
    try:
        # 관리자 권한 확인
        if not request.user.is_authenticated:
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # UserProfile에서 role 가져오기
        try:
            user_profile = request.user.profile
            user_role = user_profile.role
        except:
            user_role = None
        
        # 권한 확인: 관리자, 스터디 관리자, 또는 생성자
        has_permission = False
        
        # 1. 관리자 권한 확인
        if user_role in ['admin_role', 'study_admin_role']:
            has_permission = True
        
        # 2. 스터디 관리자 권한 확인 (Member 테이블에서)
        if not has_permission:
            from quiz.models import Member
            is_study_admin = Member.objects.filter(
                user=request.user,
                is_active=True,
                role__in=['study_admin', 'study_leader']
            ).exists()
            if is_study_admin:
                has_permission = True
        
        # 3. 생성자 권한 확인 (문제가 속한 시험의 생성자인지)
        if not has_permission:
            from quiz.models import Exam, ExamQuestion
            # 문제가 속한 시험들 중 하나라도 생성자인지 확인
            user_exams = Exam.objects.filter(
                created_by=request.user,
                examquestion__question=question
            ).distinct()
            if user_exams.exists():
                has_permission = True
        
        if not has_permission:
            return Response({'error': '관리자, 스터디 관리자 또는 생성자 권한이 필요합니다.'}, status=status.HTTP_403_FORBIDDEN)
        
        # 문제 존재 확인
        question = Question.objects.get(id=question_id)
        
        # 문제 제목 저장 (삭제 후 사용)
        question_lang = question.created_language if hasattr(question, 'created_language') else BASE_LANGUAGE
        from quiz.utils.multilingual_utils import BASE_LANGUAGE
        question_title = get_localized_field(question, 'title', question_lang, '제목 없음')
        
        # 문제 삭제
        question.delete()
        
        return Response({
            'message': f'문제 "{question_title}"이(가) 성공적으로 삭제되었습니다.'
        }, status=status.HTTP_200_OK)
        
    except Question.DoesNotExist:
        return Response({'error': '문제를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'문제 삭제 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def create_single_question_exam(request):
    """단일 문제 풀기를 위한 시험 데이터를 반환합니다."""
    try:
        question_id = request.data.get('question_id')
        exam_id = request.data.get('exam_id')  # 현재 시험 ID
        
        if not question_id:
            return Response({'error': '문제 ID가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        question = Question.objects.get(id=question_id)
        
        # 사용자 언어 확인 및 번역 처리
        if request.user.is_authenticated:
            from quiz.utils.multilingual_utils import BASE_LANGUAGE
            user_language = BASE_LANGUAGE  # 기본값
            try:
                if hasattr(request.user, 'userprofile'):
                    user_language = request.user.userprofile.language
                elif hasattr(request.user, 'profile'):
                    user_language = request.user.profile.language
            except Exception:
                pass
            
            # 번역이 필요한지 확인하고 자동 번역 수행
            translation_needed = False
            # 사용자 언어에 해당하는 필드가 비어있는지 동적으로 확인
            title_field = getattr(question, f'title_{user_language}', None)
            content_field = getattr(question, f'content_{user_language}', None)
            answer_field = getattr(question, f'answer_{user_language}', None)
            
            if not title_field or not content_field or not answer_field:
                translation_needed = True
            
            if translation_needed:
                try:
                    from ..utils.multilingual_utils import MultilingualContentManager
                    # 번역 처리 (조회 시에는 완성도 상태 업데이트를 건너뛰기)
                    manager = MultilingualContentManager(question, request.user, skip_completion_update=True)
                    manager.handle_multilingual_update()
                    # 번역 후 문제 다시 조회
                    question.refresh_from_db()
                    logger.info(f"[AUTO_TRANSLATION] 문제 {question.id} 자동 번역 완료")
                except Exception as e:
                    logger.warning(f"[AUTO_TRANSLATION] 문제 {question.id} 자동 번역 실패: {str(e)}")
        
        if exam_id:
            # 현재 시험을 사용
            try:
                exam = Exam.objects.get(id=exam_id)
                # 현재 시험에 해당 문제가 있는지 확인
                exam_question = ExamQuestion.objects.filter(exam=exam, question=question).first()
                if not exam_question:
                    return Response({'error': '해당 문제가 시험에 포함되어 있지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)
                
                # 현재 시험에서 해당 문제만 필터링하여 반환
                exam_data = ExamSerializer(exam, context={'request': request}).data
                exam_data['questions'] = [QuestionSerializer(question, context={'request': request}).data]
                exam_data['total_questions'] = 1
                
                return Response(exam_data, status=status.HTTP_200_OK)
                
            except Exam.DoesNotExist:
                return Response({'error': '시험을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            # 임시 시험 생성 (기존 로직)
            user_lang = get_user_language(request)
            question_title = get_localized_field(question, 'title', user_lang, '제목 없음')
            exam = Exam.objects.create(
                title=f"단일 문제 - {question_title}",
                total_questions=1,
                is_original=False
            )
            
            # 시험에 문제 추가
            ExamQuestion.objects.create(
                exam=exam,
                question=question,
                order=1
            )
            
            serializer = ExamSerializer(exam, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Question.DoesNotExist:
        return Response({'error': '문제를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'시험 생성 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
def delete_question_results(request):
    """선택한 문제들의 풀이 결과를 삭제합니다."""
    try:
        print(f"delete_question_results 호출됨 - request.data: {request.data}")
        
        question_ids = request.data.get('question_ids', [])
        exam_id = request.data.get('exam_id')
        delete_all = request.data.get('delete_all', False)  # 모든 문제 결과 삭제 옵션
        
        print(f"question_ids: {question_ids}")
        print(f"exam_id: {exam_id}")
        print(f"delete_all: {delete_all}")
        
        if not exam_id:
            return Response({'error': '시험 ID가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 현재 로그인한 사용자의 결과만 필터링
        current_user = request.user
        print(f"현재 사용자: {current_user}")
        
        # 해당 시험의 결과들 중에서 현재 사용자의 결과만 선택
        exam_results = ExamResult.objects.filter(exam_id=exam_id, user=current_user)
        
        print(f"찾은 현재 사용자의 시험 결과 수: {exam_results.count()}")
        
        if delete_all:
            # 모든 문제 결과 삭제 (현재 사용자의 것만)
            deleted_count = 0
            for result in exam_results:
                details_to_delete = ExamResultDetail.objects.filter(result=result)
                count = details_to_delete.count()
                deleted_count += count
                print(f"시험 결과 {result.id}에서 모든 답안 삭제: {count}개")
                
                # 디버깅: 실제로 푼 문제들 확인
                if count > 0:
                    for detail in details_to_delete:
                        question = detail.question
                        user_lang = get_user_language(request)
                        question_title = get_localized_field(question, 'title', user_lang, '제목 없음')
                        print(f"  - 문제: {question_title} (ID: {question.id}) - 답안: {detail.user_answer} (정답: {detail.is_correct})")
                
                details_to_delete.delete()
        else:
            # 선택된 문제들의 결과만 삭제 (현재 사용자의 것만)
            if not question_ids:
                return Response({'error': '삭제할 문제 ID가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 문자열을 UUID로 변환
            import uuid
            question_uuids = []
            for qid in question_ids:
                try:
                    question_uuids.append(uuid.UUID(qid))
                except ValueError:
                    print(f"잘못된 UUID 형식: {qid}")
            
            print(f"변환된 UUID들: {question_uuids}")
            
            # 디버깅: 시험에 포함된 문제들 확인
            try:
                exam = Exam.objects.get(id=exam_id)
                exam_questions = Question.objects.filter(examquestion__exam=exam)
                logger.info(f"시험에 포함된 문제들: {len(exam_questions)}개")
                print(f"선택된 문제들이 시험에 포함되어 있는지 확인:")
                for qid in question_uuids:
                    is_in_exam = exam_questions.filter(id=qid).exists()
                    print(f"  문제 {qid}: {'포함됨' if is_in_exam else '포함되지 않음'}")
            except Exam.DoesNotExist:
                print(f"시험 {exam_id}를 찾을 수 없습니다.")
            
            deleted_count = 0
            for result in exam_results:
                # 해당 결과에서 선택된 문제들의 답안만 삭제
                details_to_delete = ExamResultDetail.objects.filter(
                    result=result,
                    question_id__in=question_uuids
                )
                count = details_to_delete.count()
                deleted_count += count
                print(f"시험 결과 {result.id}에서 삭제할 답안 수: {count}")
                
                # 디버깅: 이 시험 결과에 포함된 문제들 확인
                result_questions = ExamResultDetail.objects.filter(result=result).values_list('question_id', flat=True)
                logger.info(f"시험 결과 {result.id}에 포함된 문제들: {len(result_questions)}개")
                
                details_to_delete.delete()
        
        print(f"총 삭제된 답안 수: {deleted_count}")
        
        # ========================================
        # 🔄 REDIS 캐시 무효화 (중요!)
        # ========================================
        # 
        # 문제 풀이 결과 삭제 후 통계 데이터와 캐시 간의 불일치를 방지하기 위해
        # 관련된 모든 캐시를 무효화해야 합니다.
        #
        # 🎯 캐시 무효화가 필요한 이유:
        # 1. 문제 풀이 결과가 삭제되었지만 통계는 이전 데이터를 반환하는 문제
        # 2. 화면에 표시되는 통계와 실제 DB 데이터 간의 불일치
        # 3. 사용자가 삭제 후에도 이전 통계를 보게 되는 문제
        #
        # 🏗️ 캐시 무효화 전략:
        # 1차: ExamCacheManager를 통한 체계적인 캐시 무효화
        # 2차: Redis 패턴 매칭을 통한 포괄적인 캐시 무효화 (폴백)
        # 3차: 개별 키 기반 캐시 무효화 (최후 수단)
        #
        # 📋 무효화 대상 캐시:
        # - exams_*: 시험 관련 모든 캐시
        # - exam_results_*: 시험 결과 관련 모든 캐시
        # - question_statistics_*: 문제 통계 관련 모든 캐시
        # - statistics_*: 통계 관련 모든 캐시
        #
        # ⚠️ 주의사항:
        # - Redis 환경에서는 delete_pattern을 사용하여 효율적으로 패턴 매칭
        # - 로컬 환경에서는 개별 키를 하나씩 삭제
        # - 모든 단계에서 예외 처리를 통해 안정성 확보
        # ========================================

        # 1차: ExamCacheManager를 통한 체계적인 캐시 무효화
        try:
            from ..utils.cache_utils import ExamCacheManager
            # 문제 풀이 결과 삭제 후 관련 캐시 무효화
            ExamCacheManager.invalidate_all_exam_cache()
            if current_user.is_authenticated:
                ExamCacheManager.invalidate_user_exam_cache(current_user.id)
            logger.info(f"[DELETE_QUESTION_RESULTS] ExamCacheManager를 통한 캐시 무효화 완료: {current_user.username}")
        except Exception as e:
            logger.error(f"[DELETE_QUESTION_RESULTS] ExamCacheManager 캐시 무효화 실패: {e}")
            # 폴백: 기존 방식으로 캐시 무효화
            try:
                if hasattr(cache, 'delete_pattern'):
                    # 문제 풀이 결과 관련 캐시 무효화
                    cache.delete_pattern("exams_*")
                    cache.delete_pattern("exam_results_*")
                    cache.delete_pattern("question_statistics_*")
                    cache.delete_pattern("statistics_*")
                    logger.info("[DELETE_QUESTION_RESULTS] Redis 패턴 기반 캐시 무효화 완료")
                else:
                    # 다른 캐시 백엔드의 경우 개별 키 삭제
                    cache.delete("exams_anonymous")
                    if current_user.is_authenticated:
                        cache.delete(f"exams_{current_user.id}")
                    cache.delete("exam_results_anonymous")
                    if current_user.is_authenticated:
                        cache.delete(f"exam_results_{current_user.id}")
                    logger.info("[DELETE_QUESTION_RESULTS] 개별 키 기반 캐시 무효화 완료")
            except Exception as e2:
                logger.error(f"[DELETE_QUESTION_RESULTS] 폴백 캐시 무효화도 실패: {e2}")
        
        # 프로젝트 표준: 백엔드에서는 메시지 없이 데이터만 반환, 프론트엔드에서 번역 처리
        return Response({
            'deleted_count': deleted_count
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"delete_question_results 오류: {str(e)}")
        import traceback
        print(f"오류 상세: {traceback.format_exc()}")
        return Response({'error': f'문제 풀이 결과 삭제 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
def delete_question_results_global(request):
    """특정 문제의 모든 풀이 결과를 삭제합니다 (어떤 시험에서 푼 것인지 상관없이)."""
    try:
        print(f"delete_question_results_global 호출됨 - request.data: {request.data}")
        
        question_ids = request.data.get('question_ids', [])
        
        print(f"question_ids: {question_ids}")
        
        if not question_ids:
            return Response({'error': '삭제할 문제 ID가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 현재 로그인한 사용자의 결과만 필터링
        current_user = request.user
        print(f"현재 사용자: {current_user}")
        
        # 문자열을 UUID로 변환
        import uuid
        from django.db import models  # models import 추가
        question_uuids = []
        for qid in question_ids:
            try:
                question_uuids.append(uuid.UUID(qid))
            except ValueError:
                print(f"잘못된 UUID 형식: {qid}")
        
        print(f"변환된 UUID들: {question_uuids}")
        
        # 현재 사용자의 해당 문제들의 모든 풀이 결과 삭제
        deleted_count = 0
        
        for question_id in question_uuids:
            # 해당 문제의 제목 찾기
            try:
                question = Question.objects.get(id=question_id)
                user_lang = get_user_language(request)
                question_title = get_localized_field(question, 'title', user_lang, '제목 없음')
                print(f"대상 문제: '{question_title}' (ID: {question_id})")
                
                # 같은 제목을 가진 모든 문제 찾기 (다국어 필드 모두 확인)
                from ..utils.multilingual_utils import SUPPORTED_LANGUAGES
                title_filters = models.Q()
                for lang in SUPPORTED_LANGUAGES:
                    title_value = getattr(question, f'title_{lang}', None)
                    if title_value:
                        title_filters |= models.Q(**{f'title_{lang}': title_value})
                same_title_questions = Question.objects.filter(title_filters).exclude(
                    **{f'title_{lang}__isnull': True for lang in SUPPORTED_LANGUAGES}
                )
                
                print(f"같은 제목의 문제 수: {same_title_questions.count()}")
                
                # 같은 제목의 모든 문제에 대한 풀이 결과 삭제
                for same_question in same_title_questions:
                    details_to_delete = ExamResultDetail.objects.filter(
                        question=same_question,
                        result__user=current_user
                    )
                    count = details_to_delete.count()
                    deleted_count += count
                    
                    # 디버깅: 삭제할 문제 정보 출력
                    if count > 0:
                        user_lang = get_user_language(request)
                        same_question_title = get_localized_field(same_question, 'title', user_lang, '')
                        print(f"문제 '{same_question_title}' (ID: {same_question.id})의 현재 사용자 풀이 결과 {count}개 삭제")
                        
                        # 어떤 시험에서 푼 것인지 확인
                        for detail in details_to_delete:
                            result = detail.result
                            exam_title = get_localized_field(result.exam, 'title', user_lang, 'Unknown')
                            print(f"  - 시험: {exam_title} (ID: {result.exam.id}) - 답안: {detail.user_answer} (정답: {detail.is_correct})")
                    
                    details_to_delete.delete()
                    
            except Question.DoesNotExist:
                print(f"문제 ID {question_id}를 찾을 수 없습니다.")
                continue
        
        print(f"총 삭제된 답안 수: {deleted_count}")
        
        # 캐시 무효화 (ExamCacheManager 사용)
        try:
            from ..utils.cache_utils import ExamCacheManager
            # 문제 풀이 결과 삭제 후 관련 캐시 무효화
            ExamCacheManager.invalidate_all_exam_cache()
            if current_user.is_authenticated:
                ExamCacheManager.invalidate_user_exam_cache(current_user.id)
            logger.info(f"[DELETE_QUESTION_RESULTS_GLOBAL] ExamCacheManager를 통한 캐시 무효화 완료: {current_user.username}")
        except Exception as e:
            logger.error(f"[DELETE_QUESTION_RESULTS_GLOBAL] ExamCacheManager 캐시 무효화 실패: {e}")
            # 폴백: 기존 방식으로 캐시 무효화
            try:
                if hasattr(cache, 'delete_pattern'):
                    # 문제 풀이 결과 관련 캐시 무효화
                    cache.delete_pattern("exams_*")
                    cache.delete_pattern("exam_results_*")
                    cache.delete_pattern("question_statistics_*")
                    cache.delete_pattern("statistics_*")
                    logger.info("[DELETE_QUESTION_RESULTS_GLOBAL] Redis 패턴 기반 캐시 무효화 완료")
                else:
                    # 다른 캐시 백엔드의 경우 개별 키 삭제
                    cache.delete("exams_anonymous")
                    if current_user.is_authenticated:
                        cache.delete(f"exams_{current_user.id}")
                    cache.delete("exam_results_anonymous")
                    if current_user.is_authenticated:
                        cache.delete(f"exam_results_{current_user.id}")
                    logger.info("[DELETE_QUESTION_RESULTS_GLOBAL] 개별 키 기반 캐시 무효화 완료")
            except Exception as e2:
                logger.error(f"[DELETE_QUESTION_RESULTS_GLOBAL] 폴백 캐시 무효화도 실패: {e2}")
        
        # 프로젝트 표준: 백엔드에서는 메시지 없이 데이터만 반환, 프론트엔드에서 번역 처리
        return Response({
            'deleted_count': deleted_count
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"delete_question_results_global 오류: {str(e)}")
        import traceback
        print(f"오류 상세: {traceback.format_exc()}")
        return Response({'error': f'문제 풀이 결과 삭제 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 


@api_view(['PATCH'])
def bulk_update_question_group(request):
    """문제들의 Group ID를 일괄 업데이트합니다."""
    if not request.user.is_authenticated:
        return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)
    
    # 권한 확인: 관리자, 스터디 관리자, 또는 생성자
    has_permission = False
    
    # 1. 관리자 권한 확인
    try:
        user_profile = request.user.profile
        user_role = user_profile.role
        if user_role in ['admin_role', 'study_admin_role']:
            has_permission = True
    except:
        user_role = None
    
    # 2. 스터디 관리자 권한 확인 (Member 테이블에서)
    if not has_permission:
        from quiz.models import Member
        is_study_admin = Member.objects.filter(
            user=request.user,
            is_active=True,
            role__in=['study_admin', 'study_leader']
        ).exists()
        if is_study_admin:
            has_permission = True
    
    # 3. 생성자 권한 확인 (문제가 속한 시험의 생성자인지)
    if not has_permission:
        question_ids = request.data.get('question_ids', [])
        if question_ids:
            from quiz.models import Exam, ExamQuestion
            # 문제가 속한 시험들 중 하나라도 생성자인지 확인
            user_exams = Exam.objects.filter(
                created_by=request.user,
                examquestion__question_id__in=question_ids
            ).distinct()
            if user_exams.exists():
                has_permission = True
    
    if not has_permission:
        return Response({'error': '관리자, 스터디 관리자 또는 생성자 권한이 필요합니다.'}, status=status.HTTP_403_FORBIDDEN)
    
    question_ids = request.data.get('question_ids', [])
    group_id = request.data.get('group_id', '')
    if not question_ids or not group_id:
        return Response({'error': 'question_ids와 group_id가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
    
    updated = Question.objects.filter(id__in=question_ids).update(group_id=group_id)
    return Response({'updated': updated}, status=status.HTTP_200_OK) 


@api_view(['GET'])
def get_ignored_questions(request):
    """현재 사용자가 무시한 문제 목록을 조회합니다."""
    try:
        if not request.user.is_authenticated:
            return Response({'ignored_questions': []}, status=status.HTTP_200_OK)
        
        ignored_questions = IgnoredQuestion.objects.filter(user_id=request.user.id).select_related('question')
        
        data = []
        for ignored in ignored_questions:
            user_lang = get_user_language(request)
            question_title = get_localized_field(ignored.question, 'title', user_lang, '제목 없음')
            data.append({
                'id': ignored.id,
                'question_id': ignored.question.id,
                'question_title': question_title,
                'ignored_at': ignored.ignored_at
            })
        
        return Response({'ignored_questions': data}, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': f'무시된 문제 목록 조회 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 


@api_view(['GET'])
def get_question_original_exams(request, question_id):
    """문제가 속한 원본 시험들을 조회합니다."""
    try:
        # 문제 존재 확인
        question = Question.objects.get(id=question_id)
        
        # 해당 문제가 속한 모든 시험 조회
        exams = Exam.objects.filter(
            examquestion__question=question,
            is_original=True
        ).exclude(
            Q(title_ko__contains="'s favorite") | Q(title_en__contains="'s favorite") | 
            Q(title_es__contains="'s favorite") | Q(title_zh__contains="'s favorite") | 
            Q(title_ja__contains="'s favorite")
        ).distinct()
        
        # 사용자의 개인 favorite 시험도 포함 (문제가 해당 시험에 있는 경우)
        if request.user.is_authenticated:
            user_lang = get_user_language(request)
            user_favorite_exams = Exam.objects.filter(
                **{f'title_{user_lang}': f"{request.user.username}'s favorite"},
                is_original=True,
                examquestion__question=question
            ).distinct()
            exams = (exams | user_favorite_exams).distinct()
            
            # 사용자의 "Today's Quizzes for username" 시험도 포함 (문제가 해당 시험에 있는 경우)
            # is_original 여부와 관계없이 포함
            user_today_quizzes = Exam.objects.filter(
                title_ko=f"Today's Quizzes for {request.user.username}",
                examquestion__question=question
            ).distinct()
            exams = (exams | user_today_quizzes).distinct()
            
            # 만약 시험을 찾을 수 없다면, 문제의 group_id를 통해 원본 시험 찾기 시도
            if not exams.exists() and question.group_id:
                # group_id가 "Today's Quizzes for username" 형식인 경우
                if "Today's Quizzes for" in question.group_id:
                    username = question.group_id.replace("Today's Quizzes for ", "")
                    # 해당 사용자의 "Today's Quizzes for username" 시험 찾기
                    original_exam = Exam.objects.filter(
                        title_ko=question.group_id
                    ).first()
                    if original_exam:
                        exams = Exam.objects.filter(id=original_exam.id)
                else:
                    # group_id가 원본 시험 제목인 경우 (예: "NeetCode 150", "LeetCode Dev" 등)
                    original_exam = Exam.objects.filter(
                        title_ko=question.group_id,
                        is_original=True
                    ).first()
                    if original_exam:
                        exams = Exam.objects.filter(id=original_exam.id)
            
            # 여전히 시험을 찾을 수 없다면, 사용자의 "Today's Quizzes for username" 시험을 기본으로 포함
            if not exams.exists():
                user_today_quiz = Exam.objects.filter(
                    title_ko=f"Today's Quizzes for {request.user.username}"
                ).first()
                if user_today_quiz:
                    exams = Exam.objects.filter(id=user_today_quiz.id)
        
        user_lang = get_user_language(request)
        exam_list = []
        for exam in exams:
            exam_title = get_localized_field(exam, 'title', user_lang, 'Unknown')
            exam_list.append({
                'id': exam.id,
                'title': exam_title,
                'created_at': exam.created_at
            })
        
        return Response({
            'question_id': question_id,
            'original_exams': exam_list
        })
        
    except Question.DoesNotExist:
        return Response({'error': '문제를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'원본 시험 조회 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 


@api_view(['POST'])
def ignore_question(request, question_id):
    """문제를 무시 목록에 토글합니다."""
    try:
        if not request.user.is_authenticated:
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return Response({'error': '문제를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        # 이미 무시된 문제인지 확인
        ignored_question = IgnoredQuestion.objects.filter(user=request.user, question=question).first()
        
        if ignored_question:
            # 이미 무시된 경우 제거
            ignored_question.delete()
            return Response({'is_ignored': False}, status=status.HTTP_200_OK)
        else:
            # 무시되지 않은 경우 추가
            IgnoredQuestion.objects.create(user=request.user, question=question)
            
            # 문제를 사용자의 개인 favorite 시험에도 추가 (Favorites 페이지에서 접근할 수 있도록)
            try:
                from ..models import Exam, ExamQuestion
                from django.db import models
                
                # 사용자의 favorite 시험 찾기 또는 생성
                favorite_exams = Exam.objects.filter(
                    title_ko=f"{request.user.username}'s favorite",
                    is_original=True
                ).order_by('created_at')
                
                if favorite_exams.exists():
                    favorite_exam = favorite_exams.first()
                    
                    # 중복된 favorite 시험이 있으면 나머지는 삭제
                    if favorite_exams.count() > 1:
                        for duplicate_exam in favorite_exams[1:]:
                            # 중복 시험의 문제들을 첫 번째 시험으로 이동
                            duplicate_questions = ExamQuestion.objects.filter(exam=duplicate_exam)
                            for eq in duplicate_questions:
                                # 이미 첫 번째 시험에 같은 문제가 있는지 확인
                                existing = ExamQuestion.objects.filter(
                                    exam=favorite_exam,
                                    question=eq.question
                                ).first()
                                if not existing:
                                    eq.exam = favorite_exam
                                    eq.save()
                            
                            # 중복 시험 삭제
                            duplicate_exam.delete()
                        
                        # 첫 번째 시험의 총 문제 수 업데이트
                        favorite_exam.total_questions = ExamQuestion.objects.filter(exam=favorite_exam).count()
                        favorite_exam.save()
                else:
                    favorite_exam = Exam.objects.create(
                        title_ko=f"{request.user.username}'s favorite",
                        total_questions=0,
                        is_original=True,
                        is_public=False
                    )
                
                # 이미 favorite에 추가되어 있는지 확인
                existing_question = ExamQuestion.objects.filter(
                    exam=favorite_exam,
                    question=question
                ).first()
                
                if not existing_question:
                    # favorite에 없는 경우 추가
                    max_order = ExamQuestion.objects.filter(exam=favorite_exam).aggregate(
                        models.Max('order')
                    )['order__max'] or 0
                    
                    ExamQuestion.objects.create(
                        exam=favorite_exam,
                        question=question,
                        order=max_order + 1
                    )
                    
                    # 자동 번역 로직: 모든 지원 언어에 대해 콘텐츠가 있지만 다른 언어로 번역이 필요한 경우
                    try:
                        from quiz.utils.multilingual_utils import (
                            batch_translate_texts, 
                            is_auto_translation_enabled,
                            get_user_language,
                            SUPPORTED_LANGUAGES,
                            BASE_LANGUAGE
                        )
                        
                        if is_auto_translation_enabled(request.user):
                            user_language = get_user_language(request)
                            
                            # 사용자 언어와 기본 언어('en') 사이의 번역 우선 처리
                            target_languages = [user_language, BASE_LANGUAGE] if user_language != BASE_LANGUAGE else [BASE_LANGUAGE]
                            
                            for target_lang in target_languages:
                                target_content_field = f'content_{target_lang}'
                                
                                # 대상 언어의 콘텐츠가 없으면 번역 시도
                                if not hasattr(question, target_content_field) or not getattr(question, target_content_field, None):
                                    # 모든 지원 언어에서 콘텐츠를 찾아서 번역
                                    for source_lang in SUPPORTED_LANGUAGES:
                                        if source_lang == target_lang:
                                            continue
                                        
                                        source_content_field = f'content_{source_lang}'
                                        if hasattr(question, source_content_field) and getattr(question, source_content_field, None):
                                            try:
                                                source_content = getattr(question, source_content_field)
                                                translated_texts = batch_translate_texts([source_content], source_lang, target_lang)
                                                if translated_texts and translated_texts[0]:
                                                    setattr(question, target_content_field, translated_texts[0])
                                                    question.save()
                                                    print(f"[ignore_question] 문제 {question.id} {source_lang} → {target_lang} 번역 완료")
                                                    break  # 번역 성공 시 다음 언어로 이동
                                            except Exception as trans_e:
                                                print(f"[ignore_question] 문제 {question.id} {source_lang} → {target_lang} 번역 실패: {trans_e}")
                        else:
                            print(f"[ignore_question] 사용자 설정으로 자동 번역이 비활성화되어 번역을 건너뜀 (question_id={question.id})")
                                
                    except Exception as e:
                        print(f"[ignore_question] 자동 번역 중 오류: {e}")
                    
                    # 시험의 총 문제 수 업데이트
                    favorite_exam.total_questions = ExamQuestion.objects.filter(exam=favorite_exam).count()
                    favorite_exam.save()
                    
            except Exception as e:
                # favorite 시험 추가 실패해도 무시 목록 추가는 계속 진행
                print(f"Warning: Failed to add question to favorite exam: {e}")
            
            return Response({'is_ignored': True}, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({'error': f'문제 무시 토글 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def unignore_question(request, question_id):
    """문제를 무시 목록에서 제거합니다."""
    try:
        if not request.user.is_authenticated:
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return Response({'error': '문제를 찾을 수 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 무시 목록에서 제거
        ignored_question = IgnoredQuestion.objects.filter(user=request.user, question=question).first()
        if not ignored_question:
            return Response({'error': '무시 목록에 없는 문제입니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        ignored_question.delete()
        
        # 문제를 사용자의 개인 favorite 시험에서도 제거
        try:
            from ..models import Exam, ExamQuestion
            
            # 사용자의 favorite 시험 찾기
            favorite_exam = Exam.objects.filter(
                title_ko=f"{request.user.username}'s favorite",
                is_original=True
            ).first()
            
            if favorite_exam:
                # favorite 시험에서 해당 문제 제거
                ExamQuestion.objects.filter(
                    exam=favorite_exam,
                    question=question
                ).delete()
                
                # 시험의 총 문제 수 업데이트
                favorite_exam.total_questions = ExamQuestion.objects.filter(exam=favorite_exam).count()
                favorite_exam.save()
                
        except Exception as e:
            # favorite 시험에서 제거 실패해도 무시 목록 제거는 계속 진행
            print(f"Warning: Failed to remove question from favorite exam: {e}")
        
        return Response({'is_ignored': False}, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': f'문제 무시 해제 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def check_question_ignored(request, question_id):
    """문제가 무시 목록에 있는지 확인합니다."""
    try:
        if not request.user.is_authenticated:
            return Response({'is_ignored': False}, status=status.HTTP_200_OK)
        
        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return Response({'error': '문제를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        is_ignored = IgnoredQuestion.objects.filter(user=request.user, question=question).exists()
        
        return Response({'is_ignored': is_ignored}, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': f'문제 무시 상태 확인 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
def update_question(request, question_id):
    """문제를 수정합니다. 다국어 처리를 자동으로 수행합니다."""
    try:
        if not request.user.is_authenticated:
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return Response({'error': '문제를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        # 수정 권한 확인 (문제 생성자, 시스템 관리자, 스터디 관리자, 시험 생성자)
        can_edit = False
        
        # 시스템 관리자 확인
        if request.user.is_staff or request.user.is_superuser:
            can_edit = True
        # 문제 생성자 확인
        elif hasattr(question, 'created_by') and question.created_by == request.user:
            can_edit = True
        # 스터디 관리자 권한 확인
        else:
            try:
                if hasattr(request.user, 'userprofile'):
                    user_role = request.user.userprofile.role
                    if user_role in ['admin_role', 'study_admin_role']:
                        can_edit = True
            except Exception:
                pass
        
        # Member 테이블의 스터디 관리자 권한 확인
        if not can_edit:
            try:
                from ..models import Member
                is_study_admin = Member.objects.filter(
                    user=request.user,
                    is_active=True,
                    role__in=['study_admin', 'study_leader']
                ).exists()
                if is_study_admin:
                    can_edit = True
            except Exception:
                pass
        
        # 시험 생성자 확인 (문제가 속한 시험의 생성자)
        if not can_edit:
            try:
                # 문제가 속한 시험들 찾기
                from ..models import ExamQuestion
                exam_questions = ExamQuestion.objects.filter(question=question)
                for eq in exam_questions:
                    if eq.exam.created_by == request.user:
                        can_edit = True
                        break
            except Exception:
                pass
        
        if not can_edit:
            return Response({'error': '수정 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
        
        # 요청 데이터에서 필드 추출
        data = request.data
        
        # 다국어 처리: 사용자 언어에 맞는 필드에 저장 (Exam과 동일한 방식)
        from quiz.utils.multilingual_utils import BASE_LANGUAGE
        user_language = BASE_LANGUAGE  # 기본값
        try:
            if hasattr(request.user, 'userprofile'):
                user_language = request.user.userprofile.language
            elif hasattr(request.user, 'profile'):
                user_language = request.user.profile.language
        except Exception:
            pass
        
        # 사용자 언어에 맞는 필드에 데이터 저장
        if 'title' in data:
            setattr(question, f'title_{user_language}', data['title'])
            # 백업용 title 필드는 더 이상 사용하지 않음
            # question.title = data['title']  # 제거 예정
        
        if 'content' in data:
            setattr(question, f'content_{user_language}', data['content'])
        
        if 'answer' in data:
            setattr(question, f'answer_{user_language}', data['answer'])
        
        if 'explanation' in data:
            # 빈 문자열이나 공백도 허용하여 explanation을 완전히 비울 수 있도록 함
            explanation_value = data['explanation']
            # 공백만 있는 경우 빈 문자열로 정규화
            if isinstance(explanation_value, str) and not explanation_value.strip():
                explanation_value = ''
                # explanation을 완전히 비울 때는 모든 언어 필드를 다 비움
                question.explanation_ko = ''
                question.explanation_en = ''
            else:
                # 내용이 있는 경우에만 현재 언어 필드에 설정
                setattr(question, f'explanation_{user_language}', explanation_value)
        
        # 기타 필드들
        if 'csv_id' in data:
            question.csv_id = data['csv_id']
        if 'difficulty' in data:
            question.difficulty = data['difficulty']
        if 'url' in data:
            question.url = data['url']
        if 'group_id' in data:
            question.group_id = data['group_id']
        
        # 생성자 설정 (첫 번째 수정 시)
        if not question.created_by:
            question.created_by = request.user
        
        # 생성 언어 설정 (첫 번째 수정 시)
        if not question.created_language:
            question.created_language = user_language
        
        # 다국어 콘텐츠 자동 처리 (Exam과 동일한 방식)
        try:
            from ..utils.multilingual_utils import MultilingualContentManager
            # 저장 후 다국어 처리
            question.save()
            
            # explanation이 공백 문자로 설정된 경우 동기화 건너뛰기
            language_fields = ['title', 'content', 'answer', 'explanation']
            if 'explanation' in data and isinstance(data['explanation'], str) and not data['explanation'].strip():
                # explanation 동기화를 건너뛰고 다른 필드만 처리
                language_fields = ['title', 'content', 'answer']
            
            manager = MultilingualContentManager(question, request.user, language_fields, preserve_empty_values=True)
            manager.handle_multilingual_update()
        except Exception as e:
            # 다국어 처리 실패해도 문제 수정은 계속 진행
            pass
        
        # 최종 저장
        question.save()
        
        # 수정된 문제 데이터 반환
        serializer = QuestionSerializer(question, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': f'문제 수정 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 


@api_view(['GET'])
def check_existing_file(request, filename):
    """파일명으로 기존 파일 존재 여부를 확인합니다."""
    try:
        # URL 디코딩
        import urllib.parse
        decoded_filename = urllib.parse.unquote(filename)
        print(f"[DEBUG] check_existing_file 호출됨: {filename} -> {decoded_filename}")
        
        # 파일 시스템에서 파일 존재 여부 확인
        import os
        file_path = os.path.join(QUESTION_FILES_DIR, decoded_filename)
        metadata_path = os.path.join(QUESTION_FILES_DIR, f"{decoded_filename}.json")
        
        if os.path.exists(file_path):
            print(f"[DEBUG] 파일 시스템에서 파일 발견: {decoded_filename}")
            
            # 메타데이터 파일에서 공개 여부 확인
            is_public = True  # 기본값
            uploaded_at = None
            uploaded_by = 'Unknown'
            
            if os.path.exists(metadata_path):
                try:
                    import json
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        is_public = metadata.get('is_public', True)
                        uploaded_at = metadata.get('uploaded_at')
                        uploaded_by = metadata.get('uploaded_by', 'Unknown')
                except Exception as e:
                    print(f"[DEBUG] 메타데이터 읽기 실패: {e}")
            
            is_private = not is_public
            print(f"[DEBUG] 파일 상태: is_public={is_public}, is_private={is_private}")
            
            response_data = {
                'exists': True,
                'is_private': is_private,
                'file_name': decoded_filename,
                'uploaded_at': uploaded_at,
                'uploaded_by': uploaded_by
            }
            print(f"[DEBUG] 응답 데이터: {response_data}")
            return Response(response_data)
        else:
            print(f"[DEBUG] 파일이 존재하지 않음: {decoded_filename}")
            return Response({
                'exists': False,
                'file_name': decoded_filename
            })
            
    except Exception as e:
        # 디버깅을 위한 에러 로그
        error_str = str(e)
        print(f"[DEBUG] check_existing_file 에러 발생: {error_str}")
        print(f"[DEBUG] 에러 타입: {type(e)}")
        
        # 사용자 언어에 맞는 메시지 반환
        from quiz.utils.multilingual_utils import BASE_LANGUAGE
        user_language = BASE_LANGUAGE  # 기본값
        try:
            if hasattr(request.user, 'userprofile'):
                user_language = request.user.userprofile.language
            elif hasattr(request.user, 'profile'):
                user_language = request.user.profile.language
        except Exception:
            pass
        
        # 언어별 메시지 선택 (모든 지원 언어 동적 처리)
        from quiz.utils.multilingual_utils import BASE_LANGUAGE, LANGUAGE_KO, LANGUAGE_EN, LANGUAGE_ES, LANGUAGE_ZH, LANGUAGE_JA
        
        # 사용자 언어에 맞는 번역 파일 동적 로드
        if user_language == LANGUAGE_KO:
            translations = KOREAN_TRANSLATIONS
        elif user_language == LANGUAGE_ES:
            from ..message_es import SPANISH_TRANSLATIONS
            translations = SPANISH_TRANSLATIONS
        elif user_language == LANGUAGE_ZH:
            from ..message_zh import CHINESE_TRANSLATIONS
            translations = CHINESE_TRANSLATIONS
        elif user_language == LANGUAGE_JA:
            from ..message_ja import JAPANESE_TRANSLATIONS
            translations = JAPANESE_TRANSLATIONS
        else:
            translations = ENGLISH_TRANSLATIONS  # 기본 언어
        
        error_message = translations.get(
            'question.file.exists.warning',
            ENGLISH_TRANSLATIONS.get('question.file.exists.warning', 'A file with the same name already exists. Continuing will overwrite existing questions.')
        )
        
        print(f"[DEBUG] 다국어 메시지: {error_message}")
        return Response({
            'error': error_message
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def translate_question(request):
    """개별 문제를 번역합니다."""
    try:
        question_id = request.data.get('question_id')
        target_language = request.data.get('target_language')
        
        if not question_id or not target_language:
            return Response({
                'success': False,
                'error': '문제 ID와 대상 언어가 필요합니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
        if target_language not in SUPPORTED_LANGUAGES:
            return Response({
                'success': False,
                'error': '유효하지 않은 대상 언어입니다. (ko 또는 en)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return Response({
                'success': False,
                'error': '문제를 찾을 수 없습니다.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 번역 처리
        try:
            from ..utils.multilingual_utils import MultilingualContentManager
            
            # MultilingualContentManager를 사용하여 번역 처리
            manager = MultilingualContentManager(question, request.user, language_fields=['title', 'content', 'answer', 'explanation'])
            manager.handle_multilingual_update()
            
            # 번역 후 문제 다시 조회
            question.refresh_from_db()
            
            # 번역된 데이터 반환
            translated_data = {}
            if target_language == 'en':
                translated_data = {
                    'title_en': question.title_en,
                    'content_en': question.content_en,
                    'answer_en': question.answer_en,
                    'explanation_en': question.explanation_en
                }
            else:
                translated_data = {
                    'title_ko': question.title_ko,
                    'content_ko': question.content_ko,
                    'answer_ko': question.answer_ko,
                    'explanation_ko': question.explanation_ko
                }
            
            logger.info(f"[TRANSLATE_QUESTION] 문제 {question.id} 번역 완료: {target_language}")
            
            return Response({
                'success': True,
                'message': '문제 번역이 완료되었습니다.',
                'translated_data': translated_data
            })
            
        except Exception as e:
            logger.error(f"[TRANSLATE_QUESTION] 문제 {question.id} 번역 실패: {str(e)}")
            return Response({
                'success': False,
                'error': f'번역 처리 중 오류가 발생했습니다: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        logger.error(f'[TRANSLATE_QUESTION] API 오류: {str(e)}')
        return Response({
            'success': False,
            'error': f'API 처리 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_openai_client():
    """OpenAI 클라이언트를 반환합니다."""
    if not hasattr(settings, 'OPENAI_API_KEY') or not settings.OPENAI_API_KEY:
        raise ValueError("OpenAI API 키가 설정되지 않았습니다.")
    
    return openai.OpenAI(api_key=settings.OPENAI_API_KEY)


def get_gemini_client():
    """Gemini 클라이언트를 반환합니다."""
    if not GEMINI_AVAILABLE:
        raise ValueError("google-generativeai 패키지가 설치되지 않았습니다.")
    
    gemini_api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if not gemini_api_key:
        raise ValueError("Gemini API 키가 설정되지 않았습니다.")
    
    genai.configure(api_key=gemini_api_key)
    return genai


def get_leaf_categories():
    """카테고리 리프 노드(children이 없는 노드)를 모두 가져옵니다."""
    from ..models import TagCategory
    # children이 없는 카테고리만 가져오기
    leaf_categories = TagCategory.objects.filter(children__isnull=True).distinct()
    return leaf_categories


def get_tags_from_leaf_categories(category_ids):
    """리프 노드 카테고리 ID 목록에 연결된 모든 태그를 가져옵니다."""
    from ..models import Tag, TagCategory
    if not category_ids:
        return []
    
    # 카테고리들 가져오기
    categories = TagCategory.objects.filter(id__in=category_ids)
    # 각 카테고리에 연결된 태그들 가져오기
    tags = Tag.objects.filter(categories__in=categories).distinct()
    return list(tags.values_list('id', flat=True))


# AI Instruction YAML 파일 로드 함수들
_category_analysis_rules_cache = None
_question_generation_rules_cache = None

def load_category_analysis_rules():
    """ai/prompts/text_to_questions_category_analysis.yaml 파일을 로드합니다."""
    global _category_analysis_rules_cache
    if _category_analysis_rules_cache is not None:
        return _category_analysis_rules_cache
    
    try:
        base_dir = settings.BASE_DIR
        yaml_path = os.path.join(base_dir, 'ai', 'prompts', 'text_to_questions_category_analysis.yaml')
        
        if not os.path.exists(yaml_path):
            logger.warning(f"⚠️ 카테고리 분석 프롬프트 YAML 파일을 찾을 수 없습니다: {yaml_path}")
            _category_analysis_rules_cache = {'system_prompt': '', 'prompt_template': ''}
            return _category_analysis_rules_cache
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            rules = yaml.safe_load(f)
        
        _category_analysis_rules_cache = rules or {'system_prompt': '', 'prompt_template': ''}
        logger.info(f"✅ 카테고리 분석 프롬프트 YAML 파일 로드 성공: {yaml_path}")
        return _category_analysis_rules_cache
    except Exception as e:
        logger.error(f"❌ 카테고리 분석 프롬프트 YAML 파일 로드 실패: {e}", exc_info=True)
        _category_analysis_rules_cache = {'system_prompt': '', 'prompt_template': ''}
        return _category_analysis_rules_cache

_question_generation_rules_cache = {}  # 언어별로 캐시 관리

def load_question_generation_rules(language='en'):
    """
    ai/prompts/text_to_questions_generation.yaml 파일을 로드합니다.
    
    Args:
        language: 언어 코드 (기본값: 'en')
    
    Returns:
        dict: 해당 언어의 프롬프트 딕셔너리 {'system_prompt': str, 'prompt_template': str}
    """
    global _question_generation_rules_cache
    
    # 언어별 캐시 키
    cache_key = f'{language}_rules'
    
    if cache_key in _question_generation_rules_cache:
        return _question_generation_rules_cache[cache_key]
    
    try:
        base_dir = settings.BASE_DIR
        yaml_path = os.path.join(base_dir, 'ai', 'prompts', 'text_to_questions_generation.yaml')
        
        if not os.path.exists(yaml_path):
            logger.warning(f"⚠️ 문제 생성 프롬프트 YAML 파일을 찾을 수 없습니다: {yaml_path}")
            _question_generation_rules_cache[cache_key] = {'system_prompt': '', 'prompt_template': ''}
            return _question_generation_rules_cache[cache_key]
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            all_rules = yaml.safe_load(f)
        
        # 언어별 프롬프트 추출
        if isinstance(all_rules, dict) and language in all_rules:
            rules = all_rules[language]
        else:
            # fallback: 기존 형식 지원 (언어별 분리가 안 된 경우)
            logger.warning(f"⚠️ 언어별 프롬프트를 찾을 수 없습니다. 기본 형식 사용: language={language}")
            rules = all_rules or {'system_prompt': '', 'prompt_template': ''}
        
        _question_generation_rules_cache[cache_key] = rules
        logger.info(f"✅ 문제 생성 프롬프트 YAML 파일 로드 성공: {yaml_path} (language={language})")
        return _question_generation_rules_cache[cache_key]
    except Exception as e:
        logger.error(f"❌ 문제 생성 프롬프트 YAML 파일 로드 실패: {e}", exc_info=True)
        _question_generation_rules_cache[cache_key] = {'system_prompt': '', 'prompt_template': ''}
        return _question_generation_rules_cache[cache_key]


def analyze_text_for_categories(text_content):
    """
    텍스트 내용을 분석하여 적절한 카테고리 리프 노드를 자동으로 선정합니다.
    AI를 사용하여 텍스트 내용을 분석하고, 가장 적합한 카테고리를 찾습니다.
    
    Returns:
        list: 선정된 카테고리 ID 목록
    """
    from ..models import TagCategory
    
    # 텍스트가 너무 길면 처음 3000자만 사용 (카테고리 분석용)
    text_to_analyze = text_content[:3000] if len(text_content) > 3000 else text_content
    
    # 모든 리프 노드 카테고리 가져오기
    leaf_categories = get_leaf_categories()
    
    if not leaf_categories.exists():
        logger.warning("[analyze_text_for_categories] 리프 노드 카테고리가 없습니다.")
        return []
    
    # 카테고리 정보를 문자열로 구성
    category_list = []
    for cat in leaf_categories:
        category_path = cat.get_full_path('en')  # 한국어 경로 사용
        category_list.append(f"- {category_path}")
    
    categories_text = '\n'.join(category_list)
    
    # YAML 파일에서 프롬프트 로드
    rules = load_category_analysis_rules()
    system_prompt = rules.get('system_prompt', '')
    prompt_template = rules.get('prompt_template', '')
    
    # YAML 파일이 없으면 에러 발생
    if not prompt_template or not system_prompt:
        error_msg = "프롬프트 YAML 파일을 로드할 수 없습니다. ai/prompts/text_to_questions_category_analysis.yaml 파일을 확인해주세요."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # 템플릿에 변수 치환
    prompt = prompt_template.format(
        text_to_analyze=text_to_analyze,
        categories_text=categories_text
    )
    
    # OpenAI 사용 가능 여부 확인 (캐시 체크)
    from quiz.utils.multilingual_utils import check_openai_availability, mark_openai_unavailable
    is_openai_unavailable = not check_openai_availability()
    
    # OpenAI가 사용 불가능하면 바로 Gemini로 전환
    if is_openai_unavailable:
        logger.info("[analyze_text_for_categories] OpenAI가 캐시에서 사용 불가능 상태로 확인됨, Gemini로 바로 전환...")
        ai_response = None
    else:
        # OpenAI 시도
        ai_response = None
        try:
            if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
                logger.info("[analyze_text_for_categories] OpenAI API를 사용하여 카테고리 분석 시도...")
                client = get_openai_client()
                
                response = client.chat.completions.create(
                    model=getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo'),
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.3
                )
                
                ai_response = response.choices[0].message.content.strip()
                logger.info(f"[analyze_text_for_categories] OpenAI 응답 받음: {ai_response}")
                
                # JSON 파싱
                import json
                import re
                
                # JSON 부분만 추출 (중첩된 JSON도 처리)
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = ai_response
                
                # JSON 파싱 시도
                try:
                    result = json.loads(json_str)
                except json.JSONDecodeError:
                    # JSON 파싱 실패 시, 코드 블록에서 추출 시도
                    code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
                    if code_block_match:
                        json_str = code_block_match.group(1)
                        result = json.loads(json_str)
                    else:
                        raise ValueError(f"JSON 파싱 실패: {ai_response}")
                selected_paths = result.get('categories', [])
                
                # 카테고리 경로로 ID 찾기
                selected_category_ids = []
                for path in selected_paths:
                    # 경로로 카테고리 찾기
                    category = None
                    for cat in leaf_categories:
                        if cat.get_full_path('en') == path:
                            category = cat
                            break
                    
                    if category:
                        selected_category_ids.append(category.id)
                        logger.info(f"[analyze_text_for_categories] 카테고리 선정: {path} (ID: {category.id})")
                    else:
                        logger.warning(f"[analyze_text_for_categories] 카테고리를 찾을 수 없음: {path}")
                
                return selected_category_ids
        except Exception as e:
            logger.warning(f"[analyze_text_for_categories] OpenAI API 호출 실패: {e}, Gemini로 전환 시도...")
            # OpenAI 실패 시 캐시에 마킹
            mark_openai_unavailable()
    
    # OpenAI 실패했거나 사용 불가능한 경우 Gemini로 fallback
    if ai_response is None:
        # Gemini 시도
        try:
            if hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY:
                logger.info("[analyze_text_for_categories] Gemini API를 사용하여 카테고리 분석 시도...")
                genai = get_gemini_client()
                model = genai.GenerativeModel('gemini-pro')
                
                response = model.generate_content(
                    f"{system_prompt}\n\n{prompt}",
                    generation_config={
                        'temperature': 0.3,
                        'max_output_tokens': 500,
                    }
                )
                
                ai_response = response.text.strip()
                logger.info(f"[analyze_text_for_categories] Gemini 응답 받음: {ai_response}")
                
                # JSON 파싱
                import json
                import re
                
                # JSON 부분만 추출 (중첩된 JSON도 처리)
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = ai_response
                
                # JSON 파싱 시도
                try:
                    result = json.loads(json_str)
                except json.JSONDecodeError:
                    # JSON 파싱 실패 시, 코드 블록에서 추출 시도
                    code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
                    if code_block_match:
                        json_str = code_block_match.group(1)
                        result = json.loads(json_str)
                    else:
                        raise ValueError(f"JSON 파싱 실패: {ai_response}")
                selected_paths = result.get('categories', [])
                
                # 카테고리 경로로 ID 찾기
                selected_category_ids = []
                for path in selected_paths:
                    # 경로로 카테고리 찾기
                    category = None
                    for cat in leaf_categories:
                        if cat.get_full_path('en') == path:
                            category = cat
                            break
                    
                    if category:
                        selected_category_ids.append(category.id)
                        logger.info(f"[analyze_text_for_categories] 카테고리 선정: {path} (ID: {category.id})")
                    else:
                        logger.warning(f"[analyze_text_for_categories] 카테고리를 찾을 수 없음: {path}")
                
                return selected_category_ids
        except Exception as e:
            logger.error(f"[analyze_text_for_categories] Gemini API 호출 실패: {e}")
    
    # AI 분석 실패 시 빈 리스트 반환
    logger.warning("[analyze_text_for_categories] AI 분석 실패, 빈 카테고리 반환")
    return []


def generate_questions_from_text(text_content, question_count=10, language=None, exam_difficulty=5, age_rating=None):
    """
    텍스트 내용을 분석하여 문제를 생성합니다. OpenAI를 먼저 시도하고, 실패하면 Gemini를 사용합니다.
    
    Args:
        text_content: 분석할 텍스트 내용
        question_count: 생성할 문제 개수 (기본값: 10)
        language: 사용자 언어 (기본값: None, BASE_LANGUAGE('en') 사용)
        exam_difficulty: 시험 난이도 (1~10, 기본값: 5)
        age_rating: 연령 등급 ('4+', '9+', '12+', '17+', 기본값: None)
    
    Returns:
        list: 생성된 문제 리스트
    """
    # 텍스트가 너무 길면 처음 5000자만 사용
    text_to_analyze = text_content[:5000] if len(text_content) > 5000 else text_content
    
    # 문제 개수 제한 (1~50)
    question_count = max(1, min(50, int(question_count)))
    
    # 언어 기본값 설정
    from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES, BASE_LANGUAGE
    if language is None or language not in SUPPORTED_LANGUAGES:
        language = BASE_LANGUAGE
    
    # 시험 난이도 기본값 설정 및 검증
    exam_difficulty = max(1, min(10, int(exam_difficulty) if exam_difficulty else 5))
    
    # 시험 난이도에 따른 문제 난이도 분배 계산
    from quiz.views.exam_views import calculate_difficulty_distribution
    difficulty_distribution = calculate_difficulty_distribution(exam_difficulty, question_count)
    logger.info(f"[generate_questions_from_text] 시험 난이도 {exam_difficulty}에 따른 문제 난이도 분배: {difficulty_distribution}")
    
    # YAML 파일에서 프롬프트 로드 (언어별)
    rules = load_question_generation_rules(language=language)
    system_prompt = rules.get('system_prompt', '')
    prompt_template = rules.get('prompt_template', '')
    
    # YAML 파일이 없으면 에러 발생
    if not prompt_template or not system_prompt:
        error_msg = "프롬프트 YAML 파일을 로드할 수 없습니다. ai/prompts/text_to_questions_generation.yaml 파일을 확인해주세요."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # 난이도 분배 가이드 문자열 생성 (언어별)
    difficulty_guide = ""
    if difficulty_distribution['easy'] > 0 or difficulty_distribution['medium'] > 0 or difficulty_distribution['hard'] > 0:
        # 언어별 난이도 표현 매핑
        difficulty_labels = {
            'ko': {'easy': '쉬움', 'medium': '보통', 'hard': '어려움', 'count': '개'},
            'en': {'easy': 'Easy', 'medium': 'Medium', 'hard': 'Hard', 'count': ''},
            'es': {'easy': 'Fácil', 'medium': 'Medio', 'hard': 'Difícil', 'count': ''},
            'ja': {'easy': '易しい', 'medium': '普通', 'hard': '難しい', 'count': '個'},
            'zh': {'easy': '简单', 'medium': '中等', 'hard': '困难', 'count': '个'}
        }
        
        labels = difficulty_labels.get(language, difficulty_labels['en'])
        difficulty_guide_parts = []
        
        if difficulty_distribution['easy'] > 0:
            if labels['count']:
                difficulty_guide_parts.append(f"{labels['easy']}: {difficulty_distribution['easy']}{labels['count']}")
            else:
                difficulty_guide_parts.append(f"{labels['easy']}: {difficulty_distribution['easy']}")
        if difficulty_distribution['medium'] > 0:
            if labels['count']:
                difficulty_guide_parts.append(f"{labels['medium']}: {difficulty_distribution['medium']}{labels['count']}")
            else:
                difficulty_guide_parts.append(f"{labels['medium']}: {difficulty_distribution['medium']}")
        if difficulty_distribution['hard'] > 0:
            if labels['count']:
                difficulty_guide_parts.append(f"{labels['hard']}: {difficulty_distribution['hard']}{labels['count']}")
            else:
                difficulty_guide_parts.append(f"{labels['hard']}: {difficulty_distribution['hard']}")
        
        difficulty_guide = ", ".join(difficulty_guide_parts)
    
    # 템플릿에 변수 치환
    prompt = prompt_template.format(
        question_count=question_count,
        text_to_analyze=text_to_analyze,
        difficulty_distribution=difficulty_guide
    )
    
    # OpenAI 사용 가능 여부 확인 (캐시 체크)
    from quiz.utils.multilingual_utils import check_openai_availability, mark_openai_unavailable
    is_openai_unavailable = not check_openai_availability()
    
    # OpenAI가 사용 불가능하면 바로 Gemini로 전환
    if is_openai_unavailable:
        logger.info("[generate_questions_from_text] OpenAI가 캐시에서 사용 불가능 상태로 확인됨, Gemini로 바로 전환...")
        openai_error = "OpenAI가 캐시에서 사용 불가능 상태"
    else:
        openai_error = None
    
    # OpenAI 시도
    if not is_openai_unavailable:
        try:
            if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
                logger.info("OpenAI API를 사용하여 문제 생성 시도...")
                client = get_openai_client()
                
                response = client.chat.completions.create(
                    model=getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo'),
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=3000,
                    temperature=0.7
                )
                
                ai_response = response.choices[0].message.content.strip()
                logger.info(f"OpenAI 응답 받음 (길이: {len(ai_response)})")
                
                questions = _parse_ai_response(ai_response)
                logger.info(f"OpenAI로 생성된 문제 수: {len(questions)}개")
                
                # 난이도 분배 검증 및 재조정
                questions = _adjust_question_difficulty_distribution(questions, difficulty_distribution, language)
                
                return questions
            else:
                openai_error = "OpenAI API 키가 설정되지 않았습니다."
                logger.warning(f"OpenAI API 키 없음: {openai_error}")
                mark_openai_unavailable()
        except Exception as e:
            openai_error = str(e)
            # 429 에러(quota 초과) 또는 RateLimitError는 즉시 캐시에 마킹
            is_rate_limit = False
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                if e.response.status_code == 429:
                    is_rate_limit = True
            elif '429' in str(e) or 'insufficient_quota' in str(e) or 'RateLimitError' in str(type(e).__name__):
                is_rate_limit = True
            
            if is_rate_limit:
                logger.warning(f"OpenAI 429/quota 초과 에러 감지: {e}, 즉시 캐시에 마킹하고 Gemini로 전환...", exc_info=True)
            else:
                logger.warning(f"OpenAI API 호출 실패: {e}, Gemini로 전환 시도...", exc_info=True)
            # OpenAI 실패 시 캐시에 마킹 (429 에러는 즉시, 다른 에러도 재시도 방지)
            mark_openai_unavailable()
    
    # OpenAI 실패했거나 사용 불가능한 경우 Gemini로 fallback
    if openai_error:
        # Gemini 시도
        gemini_error = None
        try:
            if GEMINI_AVAILABLE and hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY:
                logger.info("Gemini API를 사용하여 문제 생성 시도...")
                genai = get_gemini_client()
                model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-pro')
                
                # 사용 가능한 모델 목록 확인 (디버깅용)
                try:
                    available_models = [m.name for m in genai.list_models()]
                    logger.info(f"사용 가능한 Gemini 모델: {available_models[:5]}...")
                except Exception as e:
                    logger.warning(f"모델 목록 조회 실패 (무시): {e}")
                
                # 모델 생성 시도 (여러 모델 이름 시도)
                model = None
                model_names_to_try = [
                    model_name,
                    'gemini-2.5-flash',
                    'gemini-pro',
                    'gemini-1.5-pro',
                    'gemini-1.5-pro-latest',
                    'models/gemini-pro',
                ]
                
                for name in model_names_to_try:
                    try:
                        model = genai.GenerativeModel(name)
                        logger.info(f"Gemini 모델 '{name}' 사용")
                        break
                    except Exception as e:
                        logger.debug(f"모델 '{name}' 시도 실패: {e}")
                        continue
                
                if model is None:
                    raise ValueError(f"사용 가능한 Gemini 모델을 찾을 수 없습니다. 시도한 모델: {model_names_to_try}")
                
                full_prompt = f"{system_prompt}\n\n{prompt}"
                
                # 안전 필터 설정: 연령 등급에 따라 안전 필터 민감도 조정 (유틸 함수 사용)
                from ..utils.exam_utils import get_gemini_safety_settings_by_age_rating
                safety_settings = get_gemini_safety_settings_by_age_rating(age_rating)
                
                # generation_config 준비
                generation_config = {
                    'temperature': 0.7,
                    'max_output_tokens': 8000,  # 토큰 수 대폭 증가로 완전한 응답 보장
                }
                
                # safety_settings가 있으면 사용, 없으면 기본 설정 사용
                if safety_settings:
                    response = model.generate_content(
                        full_prompt,
                        generation_config=generation_config,
                        safety_settings=safety_settings
                    )
                else:
                    # safety_settings를 가져올 수 없는 경우 기본 설정으로 fallback
                    logger.warning("[generate_questions_from_text] 안전 필터 설정 실패, 기본 설정 사용")
                    response = model.generate_content(
                        full_prompt,
                        generation_config=generation_config
                    )
                
                # 응답 확인
                if not response or not response.candidates:
                    raise ValueError("Gemini API 응답이 비어있습니다.")
                
                # 응답 완료 여부 확인
                candidate = response.candidates[0]
                finish_reason = getattr(candidate, 'finish_reason', None)
                
                # finish_reason 확인 (0: STOP, 1: MAX_TOKENS, 2: SAFETY, 3: RECITATION, 4: OTHER)
                if finish_reason == 2:  # SAFETY
                    # 안전 필터링 차단 상세 정보 수집
                    safety_ratings = getattr(candidate, 'safety_ratings', None)
                    safety_info = ""
                    if safety_ratings:
                        blocked_categories = []
                        for rating in safety_ratings:
                            category = getattr(rating, 'category', 'UNKNOWN')
                            probability = getattr(rating, 'probability', 'UNKNOWN')
                            if probability in ['HIGH', 'MEDIUM']:
                                blocked_categories.append(f"{category}({probability})")
                        if blocked_categories:
                            safety_info = f" 차단된 카테고리: {', '.join(blocked_categories)}"
                    
                    logger.warning(f"Gemini 응답이 안전 필터링으로 차단됨: finish_reason={finish_reason}{safety_info}")
                    
                    # 사용자에게 더 명확한 안내 메시지
                    error_msg = "Gemini 응답이 안전 필터링으로 차단되었습니다."
                    if safety_info:
                        error_msg += safety_info
                    error_msg += " 입력 텍스트의 내용을 검토하고 다시 시도해주세요."
                    raise ValueError(error_msg)
                elif finish_reason == 1:  # MAX_TOKENS
                    logger.warning("Gemini 응답이 max_tokens로 인해 잘렸을 수 있습니다.")
                
                # response.text 접근 시도 (안전하게)
                try:
                    ai_response = response.text.strip()
                except Exception as e:
                    logger.error(f"Gemini 응답 텍스트 추출 실패: {e}, finish_reason: {finish_reason}")
                    # 응답 구조 확인
                    logger.error(f"Gemini 응답 구조: candidates={len(response.candidates) if response.candidates else 0}")
                    if response.candidates:
                        logger.error(f"첫 번째 candidate: {dir(candidate)}")
                    raise ValueError(f"Gemini 응답을 읽을 수 없습니다: {str(e)}")
                
                logger.info(f"Gemini 응답 받음 (길이: {len(ai_response)}, finish_reason: {finish_reason})")
                
                questions = _parse_ai_response(ai_response)
                logger.info(f"Gemini로 생성된 문제 수: {len(questions)}개")
                
                # 난이도 분배 검증 및 재조정
                questions = _adjust_question_difficulty_distribution(questions, difficulty_distribution, language)
                
                return questions
            else:
                gemini_error = "Gemini API 키가 설정되지 않았거나 패키지가 설치되지 않았습니다."
                logger.warning(f"Gemini API 키 없음: {gemini_error}")
        except Exception as e:
            gemini_error = str(e)
            logger.error(f"Gemini API 호출도 실패: {e}", exc_info=True)
    
    # 모든 API 실패 시 상세한 에러 메시지 반환 (사용자 친화적으로)
    error_details = []
    user_friendly_msg = None
    
    if openai_error:
        # OpenAI 에러 메시지 정리 (사용자 친화적으로)
        if "insufficient_quota" in openai_error or "할당량 초과" in openai_error or "quota" in openai_error.lower():
            error_details.append("OpenAI 할당량 초과")
            user_friendly_msg = "AI 서비스 할당량이 초과되었습니다. 잠시 후 다시 시도해주세요."
        elif "캐시에서 사용 불가능 상태" in openai_error:
            error_details.append("OpenAI 서비스 일시 중단")
            user_friendly_msg = "AI 서비스가 일시적으로 중단되었습니다. 잠시 후 다시 시도해주세요."
        else:
            error_details.append(f"OpenAI 오류")
            logger.error(f"OpenAI 에러 상세: {openai_error}")
    
    if gemini_error:
        # Gemini 에러 메시지 정리
        if "안전 필터링" in gemini_error or "safety" in gemini_error.lower():
            error_details.append("Gemini 안전 필터링 차단")
            if not user_friendly_msg:
                user_friendly_msg = "입력하신 텍스트가 안전 필터링에 의해 차단되었습니다. 텍스트 내용을 검토하고 수정 후 다시 시도해주세요."
        else:
            error_details.append(f"Gemini 오류")
            logger.error(f"Gemini 에러 상세: {gemini_error}")
    
    # 사용자 친화적인 에러 메시지 생성
    if not user_friendly_msg:
        if error_details:
            user_friendly_msg = "AI 문제 생성에 실패했습니다. 잠시 후 다시 시도해주세요."
        else:
            user_friendly_msg = "AI 서비스에 연결할 수 없습니다. 잠시 후 다시 시도해주세요."
    
    # 개발/디버깅용 상세 에러 메시지 (로그에만 기록)
    if error_details:
        detailed_msg = "AI 문제 생성 실패 상세: " + " / ".join(error_details)
        logger.warning(f"[generate_questions_from_text] {detailed_msg}")
        if openai_error:
            logger.debug(f"OpenAI 에러 상세: {openai_error}")
        if gemini_error:
            logger.debug(f"Gemini 에러 상세: {gemini_error}")
    
    raise ValueError(user_friendly_msg)


def _adjust_question_difficulty_distribution(questions, target_distribution, language='en'):
    """
    생성된 문제들의 난이도 분배를 검증하고 목표 분배에 맞게 재조정합니다.
    
    Args:
        questions: 생성된 문제 리스트
        target_distribution: 목표 난이도 분배 {'easy': count, 'medium': count, 'hard': count}
        language: 언어 코드
    
    Returns:
        list: 난이도가 재조정된 문제 리스트
    """
    if not questions or not target_distribution:
        return questions
    
    # 언어별 난이도 매핑
    difficulty_mapping = {
        'ko': {'easy': ['쉬움', 'easy', 'Easy'], 'medium': ['보통', 'medium', 'Medium'], 'hard': ['어려움', 'hard', 'Hard']},
        'en': {'easy': ['Easy', 'easy'], 'medium': ['Medium', 'medium'], 'hard': ['Hard', 'hard']},
        'es': {'easy': ['Fácil', 'fácil', 'Easy'], 'medium': ['Medio', 'medio', 'Medium'], 'hard': ['Difícil', 'difícil', 'Hard']},
        'ja': {'easy': ['易しい', 'Easy'], 'medium': ['普通', 'Medium'], 'hard': ['難しい', 'Hard']},
        'zh': {'easy': ['简单', 'Easy'], 'medium': ['中等', 'Medium'], 'hard': ['困难', 'Hard']}
    }
    
    mapping = difficulty_mapping.get(language, difficulty_mapping['en'])
    
    # 현재 난이도 분배 계산
    current_distribution = {'easy': 0, 'medium': 0, 'hard': 0}
    unclassified = []
    
    for question in questions:
        difficulty = str(question.get('difficulty', '')).strip()
        if not difficulty:
            unclassified.append(question)
            continue
        
        difficulty_lower = difficulty.lower()
        if any(d.lower() in difficulty_lower for d in mapping['easy']):
            current_distribution['easy'] += 1
        elif any(d.lower() in difficulty_lower for d in mapping['medium']):
            current_distribution['medium'] += 1
        elif any(d.lower() in difficulty_lower for d in mapping['hard']):
            current_distribution['hard'] += 1
        else:
            unclassified.append(question)
    
    logger.info(f"[_adjust_question_difficulty_distribution] 현재 분배: {current_distribution}, 목표 분배: {target_distribution}")
    
    # 목표 분배와 현재 분배 비교
    easy_diff = target_distribution['easy'] - current_distribution['easy']
    medium_diff = target_distribution['medium'] - current_distribution['medium']
    hard_diff = target_distribution['hard'] - current_distribution['hard']
    
    # 난이도가 지정되지 않은 문제들을 먼저 분배
    for question in unclassified:
        if easy_diff > 0:
            question['difficulty'] = mapping['easy'][0] if mapping['easy'] else 'Easy'
            easy_diff -= 1
            current_distribution['easy'] += 1
        elif medium_diff > 0:
            question['difficulty'] = mapping['medium'][0] if mapping['medium'] else 'Medium'
            medium_diff -= 1
            current_distribution['medium'] += 1
        elif hard_diff > 0:
            question['difficulty'] = mapping['hard'][0] if mapping['hard'] else 'Hard'
            hard_diff -= 1
            current_distribution['hard'] += 1
    
    # 여전히 차이가 있으면 문제들의 난이도를 재조정
    if easy_diff != 0 or medium_diff != 0 or hard_diff != 0:
        logger.info(f"[_adjust_question_difficulty_distribution] 난이도 재조정 필요: easy_diff={easy_diff}, medium_diff={medium_diff}, hard_diff={hard_diff}")
        
        # easy가 부족하면 medium이나 hard를 easy로 변경
        if easy_diff > 0:
            for question in questions:
                if easy_diff <= 0:
                    break
                difficulty = str(question.get('difficulty', '')).strip().lower()
                if any(d.lower() in difficulty for d in mapping['medium']) and medium_diff < 0:
                    question['difficulty'] = mapping['easy'][0] if mapping['easy'] else 'Easy'
                    easy_diff -= 1
                    medium_diff += 1
                elif any(d.lower() in difficulty for d in mapping['hard']) and hard_diff < 0:
                    question['difficulty'] = mapping['easy'][0] if mapping['easy'] else 'Easy'
                    easy_diff -= 1
                    hard_diff += 1
        
        # hard가 부족하면 easy나 medium을 hard로 변경
        if hard_diff > 0:
            for question in reversed(questions):  # 뒤에서부터 처리
                if hard_diff <= 0:
                    break
                difficulty = str(question.get('difficulty', '')).strip().lower()
                if any(d.lower() in difficulty for d in mapping['easy']) and easy_diff < 0:
                    question['difficulty'] = mapping['hard'][0] if mapping['hard'] else 'Hard'
                    hard_diff -= 1
                    easy_diff += 1
                elif any(d.lower() in difficulty for d in mapping['medium']) and medium_diff < 0:
                    question['difficulty'] = mapping['hard'][0] if mapping['hard'] else 'Hard'
                    hard_diff -= 1
                    medium_diff += 1
        
        # medium 조정 (easy와 hard 사이의 균형)
        if medium_diff != 0:
            for question in questions:
                if medium_diff == 0:
                    break
                difficulty = str(question.get('difficulty', '')).strip().lower()
                if medium_diff > 0:
                    # medium이 부족하면 easy나 hard를 medium으로
                    if any(d.lower() in difficulty for d in mapping['easy']) and easy_diff < 0:
                        question['difficulty'] = mapping['medium'][0] if mapping['medium'] else 'Medium'
                        medium_diff -= 1
                        easy_diff += 1
                    elif any(d.lower() in difficulty for d in mapping['hard']) and hard_diff < 0:
                        question['difficulty'] = mapping['medium'][0] if mapping['medium'] else 'Medium'
                        medium_diff -= 1
                        hard_diff += 1
                else:
                    # medium이 많으면 easy나 hard로 변경
                    if any(d.lower() in difficulty for d in mapping['medium']):
                        if easy_diff > 0:
                            question['difficulty'] = mapping['easy'][0] if mapping['easy'] else 'Easy'
                            medium_diff += 1
                            easy_diff -= 1
                        elif hard_diff > 0:
                            question['difficulty'] = mapping['hard'][0] if mapping['hard'] else 'Hard'
                            medium_diff += 1
                            hard_diff -= 1
    
    logger.info(f"[_adjust_question_difficulty_distribution] 난이도 재조정 완료")
    return questions


def _parse_ai_response(ai_response):
    """AI 응답을 파싱하여 문제 리스트를 반환합니다."""
    # JSON 부분만 추출 (코드 블록 제거)
    ai_response = re.sub(r'```json\s*', '', ai_response)
    ai_response = re.sub(r'```\s*$', '', ai_response, flags=re.MULTILINE)
    ai_response = ai_response.strip()
    
    # JSON 파싱 시도
    try:
        data = json.loads(ai_response)
        questions = data.get('questions', [])
        
        if not questions:
            # questions 키가 없으면 배열 자체가 응답일 수 있음
            if isinstance(data, list):
                questions = data
            else:
                raise ValueError("생성된 문제가 없습니다.")
        
        return questions
        
    except json.JSONDecodeError as e:
        logger.warning(f"JSON 파싱 실패: {e}, 복구 시도...")
        logger.debug(f"AI 응답 내용 (처음 1000자): {ai_response[:1000]}")
        
        # JSON 복구 시도: 잘린 문자열 닫기
        try:
            # "questions" 키를 찾아서 부분 파싱 시도
            questions_match = re.search(r'"questions"\s*:\s*\[', ai_response)
            if questions_match:
                start_pos = questions_match.end() - 1  # '[' 위치
                # 닫는 괄호 찾기 (마지막 ']' 찾기)
                bracket_count = 0
                end_pos = len(ai_response)
                for i in range(start_pos, len(ai_response)):
                    if ai_response[i] == '[':
                        bracket_count += 1
                    elif ai_response[i] == ']':
                        bracket_count -= 1
                        if bracket_count == 0:
                            end_pos = i + 1
                            break
                
                # questions 배열만 추출
                questions_json = ai_response[start_pos:end_pos]
                questions = json.loads(questions_json)
                
                if questions:
                    logger.info(f"부분 JSON 파싱 성공: {len(questions)}개 문제 복구")
                    return questions
        except Exception as recover_error:
            logger.debug(f"JSON 복구 시도 1 실패: {recover_error}")
        
        # JSON 복구 시도 2: 잘린 문자열을 수동으로 닫기
        try:
            # 마지막 불완전한 문자열 찾아서 닫기
            fixed_response = ai_response
            
            # 마지막 따옴표가 없는 경우 찾기
            # "question": "로 시작하는데 닫히지 않은 경우
            question_pattern = r'"question"\s*:\s*"([^"]*(?:\\.[^"]*)*)'
            matches = list(re.finditer(question_pattern, fixed_response))
            
            if matches:
                last_match = matches[-1]
                # 마지막 매치 이후에 닫는 따옴표가 없으면 추가
                end_pos = last_match.end()
                if end_pos < len(fixed_response) and fixed_response[end_pos] != '"':
                    # 불완전한 문자열 닫기
                    # 현재 위치부터 다음 쉼표나 닫는 괄호까지 찾기
                    next_comma = fixed_response.find(',', end_pos)
                    next_brace = fixed_response.find('}', end_pos)
                    
                    if next_comma != -1 and (next_brace == -1 or next_comma < next_brace):
                        # 쉼표 앞에 따옴표 추가
                        fixed_response = fixed_response[:next_comma] + '"' + fixed_response[next_comma:]
                    elif next_brace != -1:
                        # 닫는 괄호 앞에 따옴표 추가
                        fixed_response = fixed_response[:next_brace] + '"' + fixed_response[next_brace:]
                    else:
                        # 끝에 따옴표 추가
                        fixed_response = fixed_response + '"'
                
                # 전체 JSON 닫기
                if not fixed_response.rstrip().endswith(']'):
                    fixed_response = fixed_response.rstrip().rstrip(',') + '\n  ]\n}'
                
                try:
                    data = json.loads(fixed_response)
                    questions = data.get('questions', [])
                    if questions:
                        logger.info(f"수동 복구 성공: {len(questions)}개 문제 복구")
                        return questions
                except:
                    pass
        except Exception as recover_error2:
            logger.debug(f"JSON 복구 시도 2 실패: {recover_error2}")
        
        # JSON 복구 시도 3: 정규식으로 개별 문제 객체 추출
        try:
            # 각 문제 객체를 개별적으로 추출
            # "question_id"로 시작하는 객체 찾기
            question_objects = []
            current_pos = 0
            
            while True:
                # 다음 question_id 찾기
                id_match = re.search(r'"question_id"\s*:\s*"([^"]+)"', ai_response[current_pos:])
                if not id_match:
                    break
                
                obj_start = current_pos + id_match.start()
                # 이전 '{' 찾기
                brace_start = ai_response.rfind('{', 0, obj_start)
                if brace_start == -1:
                    current_pos = obj_start + id_match.end()
                    continue
                
                # 이 객체의 끝 찾기 (다음 '{' 또는 ']' 전까지)
                brace_end = ai_response.find('}', brace_start + 1)
                next_brace = ai_response.find('{', brace_start + 1)
                next_bracket = ai_response.find(']', brace_start)
                
                if brace_end == -1:
                    # 닫는 괄호가 없으면 수동으로 닫기
                    if next_bracket != -1:
                        obj_end = next_bracket
                    else:
                        obj_end = len(ai_response)
                    # 불완전한 객체 닫기
                    obj_text = ai_response[brace_start:obj_end].rstrip().rstrip(',') + '}'
                else:
                    if next_brace != -1 and next_brace < brace_end:
                        # 중첩된 객체가 있으면 더 찾기
                        brace_count = 1
                        search_pos = next_brace + 1
                        while brace_count > 0 and search_pos < len(ai_response):
                            if ai_response[search_pos] == '{':
                                brace_count += 1
                            elif ai_response[search_pos] == '}':
                                brace_count -= 1
                            search_pos += 1
                        obj_end = search_pos
                        obj_text = ai_response[brace_start:obj_end]
                    else:
                        obj_end = brace_end + 1
                        obj_text = ai_response[brace_start:obj_end]
                
                # JSON 파싱 시도
                try:
                    # 불완전한 문자열 필드 닫기
                    obj_text = re.sub(r'"question"\s*:\s*"([^"]*?)(?:"|$)', r'"question": "\1"', obj_text)
                    obj_text = re.sub(r'"answer"\s*:\s*"([^"]*?)(?:"|$)', r'"answer": "\1"', obj_text)
                    obj_text = re.sub(r'"title"\s*:\s*"([^"]*?)(?:"|$)', r'"title": "\1"', obj_text)
                    
                    q_obj = json.loads(obj_text)
                    question_objects.append(q_obj)
                except Exception as parse_err:
                    logger.debug(f"개별 객체 파싱 실패: {parse_err}")
                
                current_pos = obj_end
            
            if question_objects:
                logger.info(f"개별 객체 추출 성공: {len(question_objects)}개 문제 복구")
                return question_objects
        except Exception as regex_error:
            logger.debug(f"정규식 추출 실패: {regex_error}")
        
        # 모든 복구 시도 실패
        logger.error(f"JSON 파싱 실패 (복구 불가): {e}")
        logger.error(f"AI 응답 내용 (처음 500자): {ai_response[:500]}")
        logger.error(f"AI 응답 내용 (마지막 500자): {ai_response[-500:]}")
        raise ValueError(f"AI 응답을 JSON으로 파싱할 수 없습니다: {str(e)}")


def convert_questions_to_excel(questions, filename):
    """생성된 문제들을 sample_kr.xlsx 형식으로 변환합니다."""
    import openpyxl
    from openpyxl.styles import Font, Alignment
    
    # 워크북 생성
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Questions"
    
    # 헤더 작성 (sample_kr.xlsx 형식에 맞춤)
    headers = ['문제id', '제목', '문제 내용', '정답', '난이도', 'URL']
    ws.append(headers)
    
    # 헤더 스타일
    header_font = Font(bold=True, size=12)
    header_alignment = Alignment(horizontal='center', vertical='center')
    for cell in ws[1]:
        cell.font = header_font
        cell.alignment = header_alignment
    
    # 문제 데이터 작성
    for idx, q in enumerate(questions, start=1):
        question_id = q.get('question_id', str(idx))
        title = q.get('title', f'문제 {idx}')
        question_content = q.get('question', q.get('question_content', ''))
        answer = q.get('answer', '')
        difficulty = q.get('difficulty', '보통')
        url = q.get('url', '')
        
        # 선택지가 있으면 문제 내용에 포함
        choices = q.get('choices')
        if choices and isinstance(choices, list) and len(choices) > 0:
            # 선택지를 문제 내용에 추가 (원본 형식 유지: ①, ②, ③, ④ 또는 1., 2., 3., 4.)
            # 원본 텍스트에서 선택지 형식을 추론하여 사용
            choice_markers = ['①', '②', '③', '④', '⑤']  # 한국어 형식
            if len(choices) <= 4:
                choice_text = '\n'.join([f'{choice_markers[i]} {choice}' for i, choice in enumerate(choices)])
            else:
                # 5개 이상이면 숫자 형식 사용
                choice_text = '\n'.join([f'{i+1}. {choice}' for i, choice in enumerate(choices)])
            question_content = f"{question_content}\n\n{choice_text}"
            
            # 정답이 선택지 내용인 경우 선택지 번호로 변환
            if answer and answer not in ['①', '②', '③', '④', '⑤', '1', '2', '3', '4', '5']:
                # 정답이 choices 배열에 있는지 확인
                try:
                    answer_index = choices.index(answer)
                    # 선택지 번호로 변환 (①, ②, ③, ④ 형식)
                    if len(choices) <= 4:
                        answer = choice_markers[answer_index]
                    else:
                        answer = str(answer_index + 1)
                except ValueError:
                    # choices에 없으면 그대로 유지 (주관식 답변일 수 있음)
                    pass
        
        ws.append([
            question_id,
            title,
            question_content,
            answer,
            difficulty,
            url
        ])
    
    # 컬럼 너비 자동 조정
    column_widths = {
        'A': 12,  # 문제id
        'B': 30,  # 제목
        'C': 50,  # 문제 내용
        'D': 30,  # 정답
        'E': 12,  # 난이도
        'F': 30   # URL
    }
    
    for col, width in column_widths.items():
        ws.column_dimensions[col].width = width
    
    # 파일 저장
    output_path = os.path.join(QUESTION_FILES_DIR, filename)
    os.makedirs(QUESTION_FILES_DIR, exist_ok=True)
    
    wb.save(output_path)
    logger.info(f"엑셀 파일 생성 완료: {output_path} (문제 수: {len(questions)}개)")
    
    return output_path


def parse_url_content(url):
    """
    URL에서 웹페이지 컨텐츠를 파싱하여 텍스트를 추출합니다.
    
    Args:
        url: 파싱할 웹페이지 URL
        
    Returns:
        str: 추출된 텍스트 컨텐츠
        
    Raises:
        Exception: URL 접근 또는 파싱 실패 시
    """
    try:
        # URL 유효성 검사
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError('유효한 URL 형식이 아닙니다.')
        
        # User-Agent 설정 (일부 사이트에서 봇 차단 방지)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 요청 타임아웃 설정 (30초)
        response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        response.raise_for_status()
        
        # Content-Type 확인
        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' not in content_type and 'text/plain' not in content_type:
            logger.warning(f"[parse_url_content] 예상치 못한 Content-Type: {content_type}")
        
        # HTML 파싱
        soup = BeautifulSoup(response.content, 'lxml')
        
        # 불필요한 태그 제거 (script, style, nav, header, footer 등)
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'noscript']):
            tag.decompose()
        
        # 메인 컨텐츠 영역 찾기 (article, main, content 등)
        main_content = None
        for selector in ['article', 'main', '[role="main"]', '.content', '#content', '.main-content', '#main-content']:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        # 메인 컨텐츠가 있으면 그것만 사용, 없으면 body 전체 사용
        if main_content:
            text_content = main_content.get_text(separator='\n', strip=True)
        else:
            # body에서 텍스트 추출
            body = soup.find('body')
            if body:
                text_content = body.get_text(separator='\n', strip=True)
            else:
                text_content = soup.get_text(separator='\n', strip=True)
        
        # 빈 줄 정리 및 텍스트 정규화
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        text_content = '\n'.join(lines)
        
        if not text_content or len(text_content.strip()) < 50:
            raise ValueError('웹페이지에서 충분한 텍스트 컨텐츠를 추출할 수 없습니다.')
        
        logger.info(f"[parse_url_content] URL 파싱 완료: {url} (추출된 텍스트 길이: {len(text_content)}자)")
        return text_content
        
    except requests.exceptions.RequestException as e:
        logger.error(f"[parse_url_content] URL 요청 실패: {url} - {str(e)}")
        raise Exception(f'URL에 접근할 수 없습니다: {str(e)}')
    except Exception as e:
        logger.error(f"[parse_url_content] URL 파싱 실패: {url} - {str(e)}")
        raise


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def text_to_questions(request):
    """텍스트 파일 또는 URL을 업로드하여 AI로 문제를 생성하고 엑셀 파일로 저장합니다."""
    try:
        # 파일 또는 URL 중 하나가 있어야 함
        has_file = 'file' in request.FILES
        has_url = 'url' in request.POST and request.POST.get('url', '').strip()
        
        if not has_file and not has_url:
            return Response({'error': '파일 또는 URL이 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if has_file and has_url:
            return Response({'error': '파일과 URL을 동시에 제공할 수 없습니다. 하나만 선택해주세요.'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        text_content = None
        source_name = None
        
        if has_file:
            # 파일 처리 (기존 로직)
            file = request.FILES['file']
            file_extension = os.path.splitext(file.name)[1].lower()
            
            if file_extension != '.txt':
                return Response({'error': '텍스트 파일(.txt)만 업로드 가능합니다.'}, 
                               status=status.HTTP_400_BAD_REQUEST)
            
            # 텍스트 파일 읽기
            file.seek(0)
            try:
                text_content = file.read().decode('utf-8')
            except UnicodeDecodeError:
                # UTF-8로 읽기 실패시 다른 인코딩 시도
                file.seek(0)
                try:
                    text_content = file.read().decode('cp949')
                except:
                    return Response({'error': '텍스트 파일 인코딩 오류. UTF-8 또는 CP949 형식의 파일을 업로드해주세요.'}, 
                                   status=status.HTTP_400_BAD_REQUEST)
            
            if not text_content.strip():
                return Response({'error': '텍스트 파일이 비어있습니다.'}, 
                               status=status.HTTP_400_BAD_REQUEST)
            
            source_name = file.name
            
        elif has_url:
            # URL 처리
            url = request.POST.get('url', '').strip()
            try:
                text_content = parse_url_content(url)
                source_name = urlparse(url).netloc or url
            except Exception as e:
                return Response({'error': f'URL 파싱 실패: {str(e)}'}, 
                               status=status.HTTP_400_BAD_REQUEST)
        
        if not text_content or not text_content.strip():
            return Response({'error': '텍스트 컨텐츠를 추출할 수 없습니다.'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        # is_public 파라미터 확인
        is_public = request.POST.get('is_public', 'false').lower() == 'true'
        logger.info(f"[text_to_questions] 파일 공개 설정: {is_public}")
        
        # ai_mock_interview 파라미터 확인
        ai_mock_interview = request.POST.get('ai_mock_interview', 'false').lower() == 'true'
        logger.info(f"[text_to_questions] AI 모의 인터뷰 설정: {ai_mock_interview}")
        
        # exam_difficulty 파라미터 확인
        # 사용자가 명시적으로 전달하지 않은 경우 프로필의 age_rating에 따라 기본값 설정
        exam_difficulty_param = request.POST.get('exam_difficulty', None)
        if exam_difficulty_param is None or exam_difficulty_param == '':
            # 프로필의 age_rating에 따라 기본 난이도 설정
            try:
                from ..utils.exam_utils import get_default_difficulty_by_age_rating
                from ..utils.user_utils import calculate_age_rating
                
                profile = request.user.profile
                age_rating = calculate_age_rating(profile.date_of_birth)
                exam_difficulty = get_default_difficulty_by_age_rating(age_rating)
                logger.info(f"[text_to_questions] 프로필 age_rating({age_rating})에 따른 기본 난이도: {exam_difficulty}")
            except Exception as e:
                logger.warning(f"[text_to_questions] 프로필 기반 기본 난이도 설정 실패: {e}, 기본값 5 사용")
                exam_difficulty = 5
        else:
            try:
                exam_difficulty = int(exam_difficulty_param)
                exam_difficulty = max(1, min(10, exam_difficulty))  # 1~10 사이로 제한
            except (ValueError, TypeError):
                exam_difficulty = 5
        logger.info(f"[text_to_questions] 시험 난이도: {exam_difficulty}")
        
        # 제목 파라미터 확인
        custom_title = request.POST.get('title', '').strip()
        
        # 문제 개수 파라미터 확인
        try:
            question_count = int(request.POST.get('question_count', 10))
            question_count = max(1, min(50, question_count))  # 1~50 사이로 제한
        except (ValueError, TypeError):
            question_count = 10
        
        logger.info(f"[text_to_questions] 문제 개수: {question_count}개")
        
        # 사용자가 선택한 태그 가져오기
        user_selected_tags = []
        if hasattr(request, 'POST'):
            tags_from_post = request.POST.getlist('tags[]') or request.POST.getlist('tags')
            if tags_from_post:
                user_selected_tags = [int(tid) for tid in tags_from_post if tid.isdigit()]
                logger.info(f"[text_to_questions] 사용자 선택 태그: {user_selected_tags}")
        
        # 태그는 반드시 1개 이상 필요 (사용자 선택 태그만 사용)
        final_tag_ids = user_selected_tags
        if not final_tag_ids:
            return Response(
                {'error': '시험에는 반드시 1개 이상의 태그가 필요합니다. 태그를 선택해주세요.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.info(f"[text_to_questions] 최종 태그 ID (사용자 선택): {final_tag_ids}")
        
        # 사용자 프로필 언어 확인 (유틸 함수 사용)
        from quiz.utils.multilingual_utils import BASE_LANGUAGE, get_user_language
        user_language = get_user_language(request)
        
        # 디버깅: 사용자 프로필 언어 직접 확인
        try:
            if request.user.is_authenticated:
                if hasattr(request.user, 'profile'):
                    profile_language = request.user.profile.language
                    logger.info(f"[text_to_questions] 사용자 프로필 언어 직접 확인: {profile_language} (사용자: {request.user.username})")
                elif hasattr(request.user, 'userprofile'):
                    profile_language = request.user.userprofile.language
                    logger.info(f"[text_to_questions] 사용자 프로필 언어 직접 확인: {profile_language} (사용자: {request.user.username})")
        except Exception as e:
            logger.warning(f"[text_to_questions] 프로필 언어 직접 확인 실패: {e}")
        
        from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
        if not user_language or user_language not in SUPPORTED_LANGUAGES:
            user_language = BASE_LANGUAGE
            logger.warning(f"[text_to_questions] user_language가 유효하지 않음 ({user_language}), 기본값 {BASE_LANGUAGE} 사용")
        
        logger.info(f"[text_to_questions] 최종 사용자 언어: {user_language} (사용자: {request.user.username if request.user.is_authenticated else 'anonymous'})")
        
        # AI로 문제 생성 (사용자 언어 및 시험 난이도 전달)
        # 텍스트 내용으로 초기 age_rating 추정 및 exam_difficulty 조정
        initial_age_rating = None
        try:
            from ..utils.exam_utils import estimate_age_rating_from_text, adjust_exam_difficulty_by_age_rating
            initial_age_rating = estimate_age_rating_from_text(text_content, title=custom_title)
            original_difficulty = exam_difficulty
            exam_difficulty = adjust_exam_difficulty_by_age_rating(exam_difficulty, initial_age_rating)
            if exam_difficulty != original_difficulty:
                logger.info(f"[text_to_questions] 연령 등급({initial_age_rating})에 따라 난이도 조정: {original_difficulty} → {exam_difficulty}")
        except Exception as e:
            logger.warning(f"[text_to_questions] 연령 등급 추정 및 난이도 조정 실패: {e}, 원래 난이도 사용")
        
        # 사용자 프로필에서 age_rating 가져오기 (안전 필터 설정용)
        user_age_rating = None
        try:
            from ..utils.user_utils import calculate_age_rating
            profile = request.user.profile
            user_age_rating = calculate_age_rating(profile.date_of_birth)
            logger.info(f"[text_to_questions] 사용자 age_rating: {user_age_rating} (안전 필터 설정에 사용)")
        except Exception as e:
            logger.warning(f"[text_to_questions] 사용자 age_rating 조회 실패: {e}, 기본 안전 필터 사용")
        
        # 추정된 age_rating이 있으면 우선 사용, 없으면 사용자 프로필의 age_rating 사용
        # 17+ 등급일 경우 안전 필터를 완전히 비활성화하기 위해 사용
        final_age_rating = initial_age_rating if initial_age_rating else user_age_rating
        
        logger.info(f"[text_to_questions] 텍스트 분석 시작 (길이: {len(text_content)}자, 언어: {user_language}, 시험 난이도: {exam_difficulty}, age_rating: {final_age_rating})")
        generated_questions = []
        generation_error = None
        
        try:
            generated_questions = generate_questions_from_text(
                text_content, 
                question_count, 
                language=user_language, 
                exam_difficulty=exam_difficulty,
                age_rating=final_age_rating
            )
        except ValueError as e:
            # 문제 생성 실패 시 에러 메시지 저장하되, 부분 성공 허용
            generation_error = str(e)
            logger.warning(f"[text_to_questions] 문제 생성 실패: {generation_error}")
            # 빈 리스트로 계속 진행 (부분 성공 허용)
            generated_questions = []
        except Exception as e:
            # 예상치 못한 에러도 처리
            generation_error = f"예상치 못한 오류: {str(e)}"
            logger.error(f"[text_to_questions] 문제 생성 중 예외 발생: {e}", exc_info=True)
            generated_questions = []
        
        # 문제 개수 제한 (생성된 문제가 요청한 개수보다 많으면 자름)
        if len(generated_questions) > question_count:
            generated_questions = generated_questions[:question_count]
            logger.info(f"[text_to_questions] 생성된 문제를 {question_count}개로 제한")
        
        # 문제 생성 상태 로깅 (에러는 로그만 남기고 처리 흐름은 계속 진행)
        if not generated_questions:
            # 문제가 하나도 생성되지 않은 경우 - 에러는 로그만 남기고 계속 진행
            error_msg = '문제 생성에 실패했습니다.'
            if generation_error:
                error_msg += f' 오류: {generation_error}'
            else:
                error_msg += ' 텍스트 내용을 확인해주세요.'
            
            logger.warning(f"[text_to_questions] 문제 생성 실패 - 에러는 로그에만 기록하고 처리 흐름은 계속 진행: {error_msg}")
        elif generation_error:
            # 부분 성공 시 경고 로그
            logger.warning(f"[text_to_questions] 부분 성공: {len(generated_questions)}개 문제 생성됨 (요청: {question_count}개). 생성 에러: {generation_error}")
        
        # 엑셀 파일 생성 (sample_kr.xlsx 형식)
        # 파일명에 사용자 계정 추가
        if custom_title:
            # 사용자가 제목을 입력한 경우
            base_filename = custom_title.replace(' ', '_').replace('/', '_').replace('\\', '_')
        elif has_file:
            # 파일 업로드인 경우 파일명 사용
            base_filename = os.path.splitext(source_name)[0]
        else:
            # URL의 경우 도메인명을 파일명으로 사용
            parsed_url = urlparse(source_name if source_name.startswith('http') else f'http://{source_name}')
            base_filename = parsed_url.netloc.replace('.', '_') or 'webpage'
        username = request.user.username if request.user.is_authenticated else 'anonymous'
        excel_filename = f"{base_filename}_{username}.xlsx"
        excel_file_path = convert_questions_to_excel(generated_questions, excel_filename)
        
        # 메타데이터 생성
        metadata = {
            'filename': excel_filename,
            'original_filename': source_name if has_file else None,
            'original_url': source_name if has_url else None,
            'question_count': len(generated_questions),
            'is_public': is_public,
            'created_at': timezone.now().isoformat(),
            'created_by': request.user.username if request.user.is_authenticated else None,
            'uploaded_by': request.user.username if request.user.is_authenticated else None  # 목록 조회에서 사용
        }
        
        # 메타데이터 저장
        metadata_path = os.path.join(QUESTION_FILES_DIR, f"{excel_filename}.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"[text_to_questions] 메타데이터 저장 완료: {metadata_path}")
        
        # 자동으로 Exam 생성 (기존 create_exam 로직 재사용)
        exam = None
        try:
            logger.info(f"[text_to_questions] Exam 자동 생성 시작: {excel_filename}")
            
            # Exam 제목 생성 (사용자 입력 제목 또는 원본 파일명/URL 기반)
            if custom_title:
                exam_title = custom_title
            else:
                exam_title = base_filename.replace('_', ' ').title()
            
            # Exam description을 사용자 언어에 맞게 생성
            # user_language는 이미 위에서 설정됨
            if user_language == 'en':
                if has_file:
                    exam_description = f'Exam automatically generated from text file "{source_name}"'
                else:
                    exam_description = f'Exam automatically generated from webpage "{source_name}"'
            else:
                if has_file:
                    exam_description = f'텍스트 파일 "{source_name}"에서 자동 생성된 시험'
                else:
                    exam_description = f'웹페이지 "{source_name}"에서 자동 생성된 시험'
            
            # 같은 제목의 Exam이 있는지 확인 (사용자별로)
            existing_exam = None
            if request.user.is_authenticated:
                # 사용자가 생성한 Exam 중에서 같은 제목 찾기
                existing_exam = Exam.objects.filter(
                    created_by=request.user,
                    title_ko=exam_title
                ).first()
                if not existing_exam:
                    existing_exam = Exam.objects.filter(
                        created_by=request.user,
                        title_en=exam_title
                    ).first()
            else:
                # 비로그인 사용자의 경우 제목만으로 찾기 (비추천이지만 일단 지원)
                existing_exam = Exam.objects.filter(
                    title_ko=exam_title,
                    created_by__isnull=True
                ).first()
                if not existing_exam:
                    existing_exam = Exam.objects.filter(
                        title_en=exam_title,
                        created_by__isnull=True
                    ).first()
            
            if existing_exam:
                # 기존 Exam이 있으면 업데이트
                logger.info(f"[text_to_questions] 기존 Exam 발견: {existing_exam.id} - {exam_title}, 문제 교체 시작")
                exam = existing_exam
                
                # 기존 Exam의 문제들 삭제 (ExamQuestion만 삭제, Question은 유지)
                ExamQuestion.objects.filter(exam=exam).delete()
                logger.info(f"[text_to_questions] 기존 Exam의 문제 연결 삭제 완료")
                
                # Exam 정보 업데이트
                # 현재 언어 필드에만 설정 (MultilingualContentManager가 번역 처리)
                setattr(exam, f'description_{user_language}', exam_description)
                
                # 자동 번역이 비활성화된 경우: 다른 언어 필드는 설정하지 않음 (빈 상태 유지)
                # 자동 번역이 활성화된 경우: MultilingualContentManager가 번역하므로 여기서는 현재 언어 필드만 설정
                
                exam.is_public = is_public
                exam.ai_mock_interview = ai_mock_interview
                exam.total_questions = 0  # 나중에 업데이트
                exam.save()
                
                # 자동 번역이 활성화된 경우 백그라운드로 번역 처리
                from quiz.utils.multilingual_utils import is_auto_translation_enabled
                if is_auto_translation_enabled(request.user):
                    import threading
                    
                    def translate_exam_background():
                        try:
                            logger.info(f"[text_to_questions] 백그라운드 번역 시작 - Exam ID: {exam.id}")
                            from quiz.utils.multilingual_utils import MultilingualContentManager
                            exam.refresh_from_db()  # 최신 데이터 가져오기
                            manager = MultilingualContentManager(exam, request.user, ['title', 'description'])
                            manager.handle_multilingual_update()
                            logger.info(f"[text_to_questions] 백그라운드 번역 완료 - Exam ID: {exam.id}")
                        except Exception as e:
                            logger.error(f"[text_to_questions] 백그라운드 번역 실패 - Exam ID: {exam.id}, 오류: {e}", exc_info=True)
                    
                    thread = threading.Thread(target=translate_exam_background, daemon=True)
                    thread.start()
                    logger.info(f"[text_to_questions] Exam 번역 백그라운드 스레드 시작: {exam.id}")
                logger.info(f"[text_to_questions] 기존 Exam 업데이트 완료: {exam.id} - {exam_title}")
                
                # 기존 Exam 태그 업데이트 (사용자 선택 + 자동 선정 태그, 반드시 1개 이상)
                if final_tag_ids:
                    # 유효한 태그 ID만 필터링
                    valid_tag_ids = []
                    for tag_id in final_tag_ids:
                        try:
                            from ..models import Tag
                            tag = Tag.objects.get(id=tag_id)
                            valid_tag_ids.append(tag_id)
                            tag_lang = tag.created_language if hasattr(tag, 'created_language') else BASE_LANGUAGE
                            from quiz.utils.multilingual_utils import BASE_LANGUAGE
                            tag_name = get_localized_field(tag, 'name', tag_lang, 'Unknown')
                            logger.info(f"[text_to_questions] 유효한 태그 ID: {tag_id} ({tag_name})")
                        except Tag.DoesNotExist:
                            logger.warning(f"[text_to_questions] 존재하지 않는 태그 ID: {tag_id}")
                    
                    # 태그 설정 (반드시 1개 이상)
                    if valid_tag_ids:
                        exam.tags.set(valid_tag_ids)
                        logger.info(f"[text_to_questions] 기존 시험 태그 설정 완료 - 총 {len(valid_tag_ids)}개 태그 (사용자 선택: {len(user_selected_tags)}개)")
                    else:
                        logger.error(f"[text_to_questions] 유효한 태그가 없어 태그 설정 실패")
                else:
                    logger.error(f"[text_to_questions] final_tag_ids가 비어있어 태그 설정 실패")
            else:
                # 기존 Exam이 없으면 새로 생성
                exam = Exam.objects.create(
                    is_original=True,
                    is_public=is_public,
                    ai_mock_interview=ai_mock_interview,
                    exam_difficulty=exam_difficulty,
                    created_by=request.user if request.user.is_authenticated else None,
                    total_questions=0  # 나중에 업데이트
                )
                
                # 다국어 필드 설정 (create_exam과 동일한 방식)
                # 현재 언어 필드에만 설정 (MultilingualContentManager가 번역 처리)
                setattr(exam, f'title_{user_language}', exam_title)
                setattr(exam, f'description_{user_language}', exam_description)
                
                # 자동 번역이 비활성화된 경우: 다른 언어 필드는 설정하지 않음 (빈 상태 유지)
                # 자동 번역이 활성화된 경우: MultilingualContentManager가 번역하므로 여기서는 현재 언어 필드만 설정
                
                exam.save()
                
                # 자동 번역이 활성화된 경우 백그라운드로 번역 처리
                from quiz.utils.multilingual_utils import is_auto_translation_enabled
                if is_auto_translation_enabled(request.user):
                    import threading
                    
                    def translate_exam_background():
                        try:
                            logger.info(f"[text_to_questions] 백그라운드 번역 시작 - Exam ID: {exam.id}")
                            from quiz.utils.multilingual_utils import MultilingualContentManager
                            exam.refresh_from_db()  # 최신 데이터 가져오기
                            manager = MultilingualContentManager(exam, request.user, ['title', 'description'])
                            manager.handle_multilingual_update()
                            logger.info(f"[text_to_questions] 백그라운드 번역 완료 - Exam ID: {exam.id}")
                        except Exception as e:
                            logger.error(f"[text_to_questions] 백그라운드 번역 실패 - Exam ID: {exam.id}, 오류: {e}", exc_info=True)
                    
                    thread = threading.Thread(target=translate_exam_background, daemon=True)
                    thread.start()
                    logger.info(f"[text_to_questions] Exam 번역 백그라운드 스레드 시작: {exam.id}")
                logger.info(f"[text_to_questions] 새 Exam 생성 완료: {exam.id} - {exam_title}")
                
                # 태그 설정 (사용자 선택 태그만, 반드시 1개 이상)
                if final_tag_ids:
                    # 유효한 태그 ID만 필터링
                    valid_tag_ids = []
                    for tag_id in final_tag_ids:
                        try:
                            from ..models import Tag
                            tag = Tag.objects.get(id=tag_id)
                            valid_tag_ids.append(tag_id)
                            tag_lang = tag.created_language if hasattr(tag, 'created_language') else BASE_LANGUAGE
                            from quiz.utils.multilingual_utils import BASE_LANGUAGE
                            tag_name = get_localized_field(tag, 'name', tag_lang, 'Unknown')
                            logger.info(f"[text_to_questions] 유효한 태그 ID: {tag_id} ({tag_name})")
                        except Tag.DoesNotExist:
                            logger.warning(f"[text_to_questions] 존재하지 않는 태그 ID: {tag_id}")
                    
                    # 태그 설정 (반드시 1개 이상)
                    if valid_tag_ids:
                        exam.tags.set(valid_tag_ids)
                        logger.info(f"[text_to_questions] 시험 태그 설정 완료 - 총 {len(valid_tag_ids)}개 태그 (사용자 선택: {len(user_selected_tags)}개)")
                    else:
                        logger.error(f"[text_to_questions] 유효한 태그가 없어 태그 설정 실패")
                else:
                    logger.error(f"[text_to_questions] final_tag_ids가 비어있어 태그 설정 실패")
            
            # 엑셀 파일에서 문제 읽어서 Exam에 연결 (create_exam 로직 재사용)
            import pandas as pd
            from .exam_views import normalize_difficulty
            
            df = pd.read_excel(excel_file_path, engine='openpyxl')
            
            # 컬럼명 매핑 (create_exam과 동일한 로직)
            csv_id_column = None
            title_column = None
            content_column = None
            answer_column = None
            difficulty_column = None
            url_column = None
            
            # CSV ID 컬럼 찾기
            if '문제id' in df.columns:
                csv_id_column = '문제id'
            elif '문제ID' in df.columns:
                csv_id_column = '문제ID'
            elif 'Question ID' in df.columns:
                csv_id_column = 'Question ID'
            
            # 제목 컬럼 찾기
            if '제목' in df.columns:
                title_column = '제목'
            elif 'Title' in df.columns:
                title_column = 'Title'
            
            # 문제 내용 컬럼 찾기
            if '문제 내용' in df.columns:
                content_column = '문제 내용'
            elif 'Question Content' in df.columns:
                content_column = 'Question Content'
            
            # 정답 컬럼 찾기
            if '정답' in df.columns:
                answer_column = '정답'
            elif 'Answer' in df.columns:
                answer_column = 'Answer'
            
            # 난이도 컬럼 찾기
            if '난이도' in df.columns:
                difficulty_column = '난이도'
            elif 'Difficulty' in df.columns:
                difficulty_column = 'Difficulty'
            
            # URL 컬럼 찾기
            if 'URL' in df.columns:
                url_column = 'URL'
            
            # 문제 생성 및 Exam에 연결 (create_exam과 동일한 로직)
            # user_language는 이미 위에서 설정됨
            created_questions = []
            for idx, row in df.iterrows():
                try:
                    # 데이터 읽기
                    title_value = str(row[title_column]).strip() if title_column and title_column in df.columns else f'문제 {idx + 1}'
                    content_value = str(row[content_column]).strip() if content_column and content_column in df.columns else title_value
                    answer_value = str(row[answer_column]).strip() if answer_column and answer_column in df.columns else ''
                    difficulty_value = normalize_difficulty(str(row[difficulty_column]).strip()) if difficulty_column and difficulty_column in df.columns else None
                    url_value = str(row[url_column]).strip() if url_column and url_column in df.columns else ''
                    csv_id_value = str(row[csv_id_column]).strip() if csv_id_column and csv_id_column in df.columns else str(idx + 1)
                    
                    # Question 생성
                    new_q = Question.objects.create(
                        difficulty=difficulty_value,
                        url=url_value if url_value and url_value.lower() not in ['nan', 'none', 'null', ''] else '',
                        csv_id=csv_id_value,
                        source_id=excel_filename,
                        created_at=timezone.now(),
                        updated_at=timezone.now()
                    )
                    
                    # 다국어 필드 설정 (사용자 언어 기반)
                    if user_language == 'en':
                        new_q.title_en = title_value
                        new_q.content_en = content_value
                        new_q.answer_en = answer_value
                        new_q.is_en_complete = True
                        new_q.is_ko_complete = False
                    else:
                        new_q.title_ko = title_value
                        new_q.content_ko = content_value
                        new_q.answer_ko = answer_value
                        new_q.is_ko_complete = True
                        new_q.is_en_complete = False
                    
                    new_q.created_language = user_language
                    new_q.save()
                    
                    created_questions.append(new_q)
                    
                    # ExamQuestion 연결
                    ExamQuestion.objects.create(
                        exam=exam,
                        question=new_q,
                        order=idx + 1
                    )
                except Exception as e:
                    logger.error(f"[text_to_questions] 문제 생성 실패 (행 {idx + 1}): {e}", exc_info=True)
                    continue
            
            exam.total_questions = len(created_questions)
            exam.save()
            
            # 시험 내용 분석하여 연령 등급 추정 (난이도는 이미 문제 생성 전에 조정됨)
            try:
                from ..utils.exam_utils import estimate_exam_age_rating
                # 시험에 포함된 모든 문제 가져오기
                exam_questions = [eq.question for eq in exam.examquestion_set.select_related('question').all()]
                estimated_rating = estimate_exam_age_rating(exam, exam_questions)
                exam.age_rating = estimated_rating
                exam.save(update_fields=['age_rating'])
                logger.info(f"[text_to_questions] 시험 연령 등급 추정 완료: {estimated_rating} (시험 ID: {exam.id})")
            except Exception as e:
                logger.error(f"[text_to_questions] 시험 연령 등급 추정 실패: {e}", exc_info=True)
                # 추정 실패 시 기본값 17+ 유지
            
            logger.info(f"[text_to_questions] Exam 생성 완료: {exam.id}, 연결된 문제 수: {len(created_questions)}개")
            
            # 자동 번역이 활성화된 경우 문제들에 대한 번역을 백그라운드로 처리
            from quiz.utils.multilingual_utils import is_auto_translation_enabled
            if is_auto_translation_enabled(request.user) and created_questions:
                import threading
                
                def translate_questions_background():
                    try:
                        logger.info(f"[text_to_questions] 백그라운드 문제 번역 시작 - Exam ID: {exam.id}, 문제 수: {len(created_questions)}개")
                        from quiz.utils.multilingual_utils import MultilingualContentManager
                        from quiz.models import Question
                        
                        # 문제 ID 리스트 저장 (exam이 변경될 수 있으므로)
                        question_ids = [q.id for q in created_questions]
                        
                        # 각 문제에 대해 번역 처리
                        for question_id in question_ids:
                            try:
                                question = Question.objects.get(id=question_id)
                                manager = MultilingualContentManager(question, request.user, ['title', 'content', 'answer', 'explanation'])
                                manager.handle_multilingual_update()
                                logger.debug(f"[text_to_questions] 문제 {question_id} 번역 완료")
                            except Question.DoesNotExist:
                                logger.warning(f"[text_to_questions] 문제 {question_id}를 찾을 수 없음")
                            except Exception as e:
                                logger.error(f"[text_to_questions] 문제 {question_id} 번역 실패: {e}", exc_info=True)
                        
                        logger.info(f"[text_to_questions] 백그라운드 문제 번역 완료 - Exam ID: {exam.id}")
                    except Exception as e:
                        logger.error(f"[text_to_questions] 백그라운드 문제 번역 실패 - Exam ID: {exam.id}, 오류: {e}", exc_info=True)
                
                thread = threading.Thread(target=translate_questions_background, daemon=True)
                thread.start()
                logger.info(f"[text_to_questions] 문제 번역 백그라운드 스레드 시작: {exam.id}, 문제 수: {len(created_questions)}개")
            
        except Exception as e:
            logger.error(f"[text_to_questions] Exam 자동 생성 실패: {e}", exc_info=True)
            # Exam 생성 실패해도 엑셀 파일 생성은 성공으로 처리
        
        # MinIO 사용 여부 확인
        use_minio = getattr(settings, 'USE_MINIO', False)
        
        if use_minio:
            # MinIO에 파일 업로드
            try:
                from django.core.files.storage import default_storage
                import boto3
                from botocore.exceptions import ClientError
                
                s3_client = boto3.client(
                    's3',
                    endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    verify=False
                )
                
                # 엑셀 파일 업로드
                with open(excel_file_path, 'rb') as excel_file:
                    default_storage.save(excel_filename, excel_file)
                
                # 메타데이터 업로드
                with open(metadata_path, 'rb') as meta_file:
                    default_storage.save(f"{excel_filename}.json", meta_file)
                
                logger.info(f"[text_to_questions] MinIO에 파일 업로드 완료: {excel_filename}")
            except Exception as e:
                logger.warning(f"[text_to_questions] MinIO 업로드 실패, 로컬 파일 유지: {e}")
        
        # 문제 생성 상태에 따라 응답 데이터 구성
        if not generated_questions:
            # 문제가 하나도 생성되지 않은 경우 - 에러 정보 포함하되 200 OK 반환
            # 다국어 메시지 처리
            from ..views.auth_views import get_message_by_language
            
            if user_language == 'ko':
                error_msg = '문제 생성에 실패했습니다.'
                message = '문제를 생성할 수 없었지만 처리 프로세스는 완료되었습니다.'
                warning_msg = generation_error if generation_error else 'AI 서비스 연결에 실패했습니다. 잠시 후 다시 시도해주세요.'
                if generation_error:
                    error_msg += f' 오류: {generation_error}'
                else:
                    error_msg += ' 텍스트 내용을 확인해주세요.'
            elif user_language == 'es':
                error_msg = 'Error al generar preguntas.'
                message = 'No se pudieron generar preguntas, pero el proceso se completó.'
                warning_msg = generation_error if generation_error else 'Error al conectar con el servicio de IA. Por favor, inténtelo de nuevo más tarde.'
                if generation_error:
                    error_msg += f' Error: {generation_error}'
                else:
                    error_msg += ' Por favor, revise el contenido del texto.'
            elif user_language == 'zh':
                error_msg = '问题生成失败。'
                message = '无法生成问题，但处理过程已完成。'
                warning_msg = generation_error if generation_error else 'AI 服务连接失败。请稍后再试。'
                if generation_error:
                    error_msg += f' 错误：{generation_error}'
                else:
                    error_msg += ' 请检查文本内容。'
            elif user_language == 'ja':
                error_msg = '問題の生成に失敗しました。'
                message = '問題を生成できませんでしたが、処理プロセスは完了しました。'
                warning_msg = generation_error if generation_error else 'AIサービスへの接続に失敗しました。しばらくしてからもう一度お試しください。'
                if generation_error:
                    error_msg += f' エラー：{generation_error}'
                else:
                    error_msg += ' テキストの内容を確認してください。'
            else:
                error_msg = 'Failed to generate questions.'
                message = 'Could not generate questions, but the processing process has been completed.'
                warning_msg = generation_error if generation_error else 'Failed to connect to AI service. Please try again later.'
                if generation_error:
                    error_msg += f' Error: {generation_error}'
                else:
                    error_msg += ' Please check the text content.'
            
            response_data = {
                'success': False,
                'error': error_msg,
                'message': message,
                'filename': excel_filename if 'excel_filename' in locals() else None,
                'question_count': 0,
                'warning': warning_msg,
                'generation_error': generation_error
            }
        else:
            # 문제가 생성된 경우
            # 다국어 메시지 처리
            # user_language가 제대로 설정되었는지 재확인 (함수 스코프에서 다시 가져오기)
            from quiz.utils.multilingual_utils import get_user_language
            current_user_language = get_user_language(request)
            from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
            if not current_user_language or current_user_language not in SUPPORTED_LANGUAGES:
                current_user_language = BASE_LANGUAGE
                logger.warning(f"[text_to_questions] 메시지 생성 시 user_language 재확인 실패, 기본값 {BASE_LANGUAGE} 사용")
            else:
                # 재확인한 언어가 다르면 경고
                if current_user_language != user_language:
                    logger.warning(f"[text_to_questions] user_language 불일치 감지: 초기={user_language}, 재확인={current_user_language}, 재확인 값 사용")
                user_language = current_user_language
            
            logger.info(f"[text_to_questions] 성공 메시지 생성 - user_language: {user_language}, 문제 개수: {len(generated_questions)}")
            
            # 문제 개수와 파일명을 포함한 메시지 생성
            if user_language == 'ko':
                message = f'{len(generated_questions)}개의 문제가 생성되어 엑셀 파일로 저장되었습니다.'
            elif user_language == 'es':
                message = f'Se generaron {len(generated_questions)} preguntas y se guardaron en un archivo Excel.'
            elif user_language == 'zh':
                message = f'已生成 {len(generated_questions)} 个问题并保存为 Excel 文件。'
            elif user_language == 'ja':
                message = f'{len(generated_questions)}個の問題が生成され、Excelファイルとして保存されました。'
            else:
                # 기본값: 영어
                message = f'{len(generated_questions)} questions have been generated and saved to an Excel file.'
            
            response_data = {
                'success': True,
                'message': message,
                'filename': excel_filename,
                'question_count': len(generated_questions),
                'file_path': excel_file_path
            }
            
            # 부분 성공 시 경고 메시지 추가
            if generation_error:
                if user_language == 'ko':
                    warning_msg = f'일부 문제 생성에 실패했습니다. {len(generated_questions)}개 문제만 생성되었습니다. (요청: {question_count}개)'
                elif user_language == 'es':
                    warning_msg = f'Falló la generación de algunas preguntas. Solo se generaron {len(generated_questions)} preguntas. (Solicitado: {question_count})'
                elif user_language == 'zh':
                    warning_msg = f'部分问题生成失败。仅生成了 {len(generated_questions)} 个问题。（请求：{question_count} 个）'
                elif user_language == 'ja':
                    warning_msg = f'一部の問題生成に失敗しました。{len(generated_questions)}個の問題のみ生成されました。（リクエスト：{question_count}個）'
                else:
                    warning_msg = f'Some questions failed to generate. Only {len(generated_questions)} questions were generated. (Requested: {question_count})'
                
                response_data['warning'] = warning_msg
                response_data['generation_error'] = generation_error
                logger.warning(f"[text_to_questions] 부분 성공 응답: {len(generated_questions)}개 문제 생성, 경고 메시지 포함")
        
        # Exam이 생성된 경우 exam_id 추가 (메시지에는 ID 포함하지 않음)
        if exam is not None:
            response_data['exam_id'] = str(exam.id)
            user_lang = get_user_language(request)
            response_data['exam_title'] = get_localized_field(exam, 'title', user_lang, '제목 없음')
            
            # 메시지 추가 시에도 user_language 재확인 (프로필 언어 우선)
            from quiz.utils.multilingual_utils import get_user_language
            message_language = get_user_language(request)
            from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
            if not message_language or message_language not in SUPPORTED_LANGUAGES:
                message_language = BASE_LANGUAGE
            logger.info(f"[text_to_questions] 시험 생성 메시지 추가 - message_language: {message_language} (초기 user_language: {user_language})")
            
            if response_data.get('success'):
                # 시험 생성 메시지 추가 (ID 제외, 다국어 처리)
                if message_language == 'ko':
                    response_data['message'] += ' 시험이 자동으로 생성되었습니다.'
                elif message_language == 'es':
                    response_data['message'] += ' El examen se creó automáticamente.'
                elif message_language == 'zh':
                    response_data['message'] += ' 考试已自动创建。'
                elif message_language == 'ja':
                    response_data['message'] += ' 試験が自動的に作成されました。'
                else:
                    response_data['message'] += ' Exam has been automatically created.'
            else:
                # 실패 시 메시지 (ID 제외, 다국어 처리)
                if message_language == 'ko':
                    response_data['message'] = '시험은 생성되었지만 문제가 없습니다.'
                elif message_language == 'es':
                    response_data['message'] = 'El examen se creó pero no tiene preguntas.'
                elif message_language == 'zh':
                    response_data['message'] = '考试已创建但没有问题。'
                elif message_language == 'ja':
                    response_data['message'] = '試験は作成されましたが、問題がありません。'
                else:
                    response_data['message'] = 'Exam was created but has no questions.'
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except UnicodeDecodeError:
        return Response({'error': '텍스트 파일 인코딩 오류. UTF-8 형식의 파일을 업로드해주세요.'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"텍스트 파일 처리 실패: {e}", exc_info=True)
        return Response({'error': f'텍스트 파일 처리 중 오류가 발생했습니다: {str(e)}'}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)