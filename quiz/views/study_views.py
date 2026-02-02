"""
스터디 관련 API 뷰

캐시 정리 정책:
1. 스터디 생성/삭제/수정 시: StudyCacheManager를 통한 체계적인 캐시 무효화
2. 멤버 추가/삭제 시: 스터디 관련 캐시 무효화
3. 폴백 메커니즘: StudyCacheManager 실패 시 기존 방식으로 캐시 무효화
4. 로깅: 모든 캐시 무효화 작업에 대한 상세 로그 기록

캐시 계층:
- Redis 환경: delete_pattern을 사용한 효율적인 패턴 매칭
- 로컬 환경: cache.clear() 또는 개별 키 삭제
- 프론트엔드: localStorage, sessionStorage 정리
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.db import models
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.utils import timezone
from io import BytesIO
import pandas as pd
from django.core.cache import cache
from django.conf import settings
import requests
import json
from ..models import Study, StudyTask, Member, StudyTaskProgress, ExamResult, Exam, Question, QuestionMemberMapping, StudyJoinRequest, Tag
from ..serializers import StudySerializer, StudyTaskSerializer, StudyTaskUpdateSerializer, MemberSerializer, CreateQuestionMemberMappingSerializer, QuestionMemberMappingSerializer, StudyJoinRequestSerializer, CreateStudyJoinRequestSerializer, UpdateStudyJoinRequestSerializer, TagSerializer
from ..utils.cache_utils import StudyCacheManager
from ..utils.multilingual_utils import MultilingualContentManager, get_localized_field, get_user_language, SUPPORTED_LANGUAGES
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class StudyViewSet(viewsets.ModelViewSet):
    queryset = Study.objects.all()  # Add queryset attribute
    serializer_class = StudySerializer
    permission_classes = []  # 모든 사용자가 접근 가능하도록 설정

    def get_serializer_class(self):
        """select 파라미터에 따라 시리얼라이저 선택"""
        select_fields = self.request.query_params.get('select', '').split(',') if self.request.query_params.get('select') else []
        
        # select 파라미터가 있고 exam 상세 정보가 포함되지 않으면 StudyListSerializer 사용
        # tasks와 members는 StudyListSerializer에서도 포함 (최적화된 버전)
        if select_fields and 'exam' not in select_fields and 'questions' not in select_fields:
            from ..serializers import StudyListSerializer
            return StudyListSerializer
        
        return StudySerializer
    
    def get_serializer_context(self):
        """시리얼라이저에 추가 컨텍스트 전달"""
        context = super().get_serializer_context()
        
        # lang 파라미터 우선 사용 (프론트엔드에서 명시적으로 전달한 언어)
        # 없으면 사용자 프로필 언어 사용
        from quiz.utils.multilingual_utils import BASE_LANGUAGE
        user_language = self.request.query_params.get('lang')
        logger.debug(f"[STUDY_VIEWSET] get_serializer_context - lang 파라미터: {user_language}")
        
        # lang 파라미터가 없으면 사용자 프로필 언어 확인
        if not user_language and self.request.user.is_authenticated:
            if hasattr(self.request.user, 'profile') and hasattr(self.request.user.profile, 'language'):
                user_language = self.request.user.profile.language
                logger.debug(f"[STUDY_VIEWSET] get_serializer_context - 프로필 언어 사용: {user_language}")
            elif hasattr(self.request.user, 'userprofile') and hasattr(self.request.user.userprofile, 'language'):
                user_language = self.request.user.userprofile.language
                logger.debug(f"[STUDY_VIEWSET] get_serializer_context - userprofile 언어 사용: {user_language}")
        
        # lang 파라미터도 없고 프로필 언어도 없으면 기본값 사용
        if not user_language:
            user_language = BASE_LANGUAGE
            logger.debug(f"[STUDY_VIEWSET] get_serializer_context - 기본값 사용: {user_language}")
        
        logger.debug(f"[STUDY_VIEWSET] get_serializer_context - 최종 user_language: {user_language}")
        context['user_language'] = user_language
        # request를 context에 추가 (StudyTaskSerializer에서 user 정보 접근용)
        context['request'] = self.request
        return context

    def get_queryset(self):
        user = self.request.user
        is_public = self.request.query_params.get('is_public')
        my_studies = self.request.query_params.get('my_studies')
        
        # select 파라미터 확인 (성능 최적화)
        select_fields = self.request.query_params.get('select', '').split(',') if self.request.query_params.get('select') else []
        
        # 사용자 언어 확인 (lang 파라미터 우선, 없으면 사용자 프로필 언어 사용)
        # 프론트엔드에서 사용자 프로필 언어를 lang 파라미터로 전송
        user_language = self.request.query_params.get('lang')
        # lang 파라미터가 없으면 사용자 프로필 언어 확인
        if not user_language and user.is_authenticated:
            if hasattr(user, 'profile') and hasattr(user.profile, 'language'):
                user_language = user.profile.language
            elif hasattr(user, 'userprofile') and hasattr(user.userprofile, 'language'):
                user_language = user.userprofile.language
        # lang 파라미터도 없고 프로필 언어도 없으면 기본값 BASE_LANGUAGE 사용
        if not user_language:
            from quiz.utils.multilingual_utils import BASE_LANGUAGE
            user_language = BASE_LANGUAGE
        
        # prefetch_related 조건부 적용 (성능 최적화)
        prefetch_list = []
        if not select_fields or 'tasks' in select_fields:
            prefetch_list.append('tasks__exam')
        if not select_fields or 'members' in select_fields:
            prefetch_list.append('members__user')
        # tags는 항상 prefetch (StudyListSerializer에서 사용)
        if not select_fields or 'tags' in select_fields:
            prefetch_list.append('tags')
        
        if user.is_authenticated:
            # admin_role 사용자는 모든 스터디에 접근 가능
            is_admin = hasattr(user, 'profile') and hasattr(user.profile, 'role') and user.profile.role == 'admin_role'
            if is_admin:
                queryset = Study.objects.select_related('created_by')
                if prefetch_list:
                    queryset = queryset.prefetch_related(*prefetch_list)
                queryset = queryset.all()
            else:
                # 일반 사용자는 공개 스터디, 자신이 멤버인 스터디, 자신이 만든 스터디에 접근 가능
                # 멤버 필터링: 사용자 계정이 연결된 멤버 또는 사용자명이 일치하는 멤버 (활성화된 멤버만)
                queryset = Study.objects.select_related('created_by')
                if prefetch_list:
                    queryset = queryset.prefetch_related(*prefetch_list)
                queryset = queryset.filter(
                    models.Q(is_public=True) | 
                    models.Q(members__user=user, members__is_active=True) |  # 사용자 계정이 연결된 활성 멤버
                    models.Q(members__name=user.username, members__is_active=True) |  # 멤버 이름이 사용자명과 일치하는 활성 멤버
                    models.Q(created_by=user)  # 사용자가 만든 스터디
                ).distinct()
            
            # my_studies 파라미터가 있으면 내 스터디만 필터링
            if my_studies is not None and my_studies.lower() == 'true':
                # 내 스터디만: 사용자가 멤버인 스터디 또는 사용자가 만든 스터디 (공개 여부와 관계없이)
                queryset = Study.objects.select_related('created_by')
                if prefetch_list:
                    queryset = queryset.prefetch_related(*prefetch_list)
                queryset = queryset.filter(
                    models.Q(members__user=user, members__is_active=True) |  # 사용자 계정이 연결된 활성 멤버
                    models.Q(members__name=user.username, members__is_active=True) |  # 멤버 이름이 사용자명과 일치하는 활성 멤버
                    models.Q(created_by=user)  # 사용자가 만든 스터디
                ).distinct()
                # 태그 필터링 적용
                queryset = self._apply_tag_filter(queryset)
                # 지원 언어 필터링 추가 (my_studies일 때도 적용)
                # 생성자가 만든 스터디는 지원언어 필터를 건너뛰어야 함 (자신이 만든 스터디는 항상 볼 수 있어야 함)
                # supported_languages에 사용자 언어가 포함되어 있어야 조회됨
                # Study.save() 메서드에서 항상 supported_languages를 설정하므로 빈 문자열은 거의 없음
                # 성능 최적화: 단일 __contains 조건 사용 (인덱스는 부분적으로 활용)
                # supported_languages는 지원 언어들의 조합 (예: 'ko', 'en', 'ko,en', 'en,ko', 'en,es,zh,ja' 등)
                # 지원 언어: ko, en, es, zh, ja
                from django.db.models import Q
                logger.info(f"[STUDY_QUERY] my_studies=true, user_language={user_language}, user_id={user.id if user.is_authenticated else 'anonymous'}")
                queryset_before = queryset.count()
                queryset = queryset.filter(
                    Q(supported_languages__contains=user_language) | Q(created_by=user)
                )
                queryset_after = queryset.count()
                logger.info(f"[STUDY_QUERY] 필터링 전: {queryset_before}개, 필터링 후: {queryset_after}개")
                return queryset
            # is_public 파라미터가 있으면 필터링
            elif is_public is not None:
                if is_public.lower() == 'true':
                    # 공개 스터디만 요청한 경우, 공개 스터디와 사용자가 멤버인 스터디 포함
                    public_studies = Study.objects.select_related('created_by')
                    if prefetch_list:
                        public_studies = public_studies.prefetch_related(*prefetch_list)
                    public_studies = public_studies.filter(is_public=True)
                    member_studies = Study.objects.select_related('created_by')
                    if prefetch_list:
                        member_studies = member_studies.prefetch_related(*prefetch_list)
                    member_studies = member_studies.filter(
                        members__user=user,
                        members__is_active=True,
                        is_public=False
                    )
                    # 두 쿼리를 결합하기 전에 모두 distinct() 적용
                    queryset = (public_studies.distinct() | member_studies.distinct()).distinct()
                elif is_public.lower() == 'false':
                    queryset = queryset.filter(is_public=False)
            
            # 태그 필터링 적용
            queryset = self._apply_tag_filter(queryset)
            
            # 지원 언어 필터링 추가 (마지막에 추가)
            # admin 권한이고 모든 스터디를 조회할 때(my_studies나 is_public 파라미터가 없을 때)는 지원언어 필터를 적용하지 않음
            # 생성자가 만든 스터디는 지원언어 필터를 건너뛰어야 함 (자신이 만든 스터디는 항상 볼 수 있어야 함)
            # supported_languages에 사용자 언어가 포함되어 있어야 조회됨
            # Study.save() 메서드에서 항상 supported_languages를 설정하므로 빈 문자열은 거의 없음
            # 성능 최적화: 단일 __contains 조건 사용 (인덱스는 부분적으로 활용)
            # supported_languages는 지원 언어들의 조합 (예: 'ko', 'en', 'ko,en', 'en,ko', 'en,es,zh,ja' 등)
            # 지원 언어: ko, en, es, zh, ja
            if not (is_admin and my_studies is None and is_public is None):
                # admin이 모든 스터디를 조회할 때가 아니면 지원언어 필터 적용
                # 단, 생성자가 만든 스터디는 필터에서 제외
                from django.db.models import Q
                queryset = queryset.filter(
                    Q(supported_languages__contains=user_language) | Q(created_by=user)
                )
            
            return queryset
        else:
            # 비로그인 사용자는 공개 스터디만 접근 가능
            # my_studies 파라미터가 있으면 빈 결과 반환 (익명 사용자는 내 스터디가 없음)
            if my_studies is not None and my_studies.lower() == 'true':
                queryset = Study.objects.none()
            else:
                queryset = Study.objects.select_related('created_by')
                if prefetch_list:
                    queryset = queryset.prefetch_related(*prefetch_list)
                queryset = queryset.filter(is_public=True)
                
                # is_public 파라미터가 있으면 필터링
                if is_public is not None:
                    if is_public.lower() == 'true':
                        queryset = queryset.filter(is_public=True)
                    elif is_public.lower() == 'false':
                        queryset = queryset.filter(is_public=False)
            
            # 태그 필터링 적용
            queryset = self._apply_tag_filter(queryset)
            
            # 지원 언어 필터링 추가 (마지막에 추가)
            # 익명 사용자의 경우 지원언어 필터만 적용 (생성자 필터는 불가능)
            # supported_languages에 사용자 언어가 포함되어 있어야 조회됨
            # Study.save() 메서드에서 항상 supported_languages를 설정하므로 빈 문자열은 거의 없음
            # 성능 최적화: 단일 __contains 조건 사용 (인덱스는 부분적으로 활용)
            # supported_languages는 지원 언어들의 조합 (예: 'ko', 'en', 'ko,en', 'en,ko', 'en,es,zh,ja' 등)
            # 지원 언어: ko, en, es, zh, ja
            from django.db.models import Q
            queryset = queryset.filter(
                Q(supported_languages__contains=user_language)
            )
            
            return queryset
    
    def _apply_tag_filter(self, queryset):
        """태그 필터링을 적용하는 헬퍼 메서드"""
        tag_ids = self.request.query_params.getlist('tags')
        if tag_ids:
            # 태그 ID 리스트를 정수로 변환
            try:
                tag_ids = [int(tag_id) for tag_id in tag_ids if tag_id.isdigit()]
                if tag_ids:
                    # 선택된 태그 중 하나라도 포함하는 스터디 필터링
                    queryset = queryset.filter(tags__id__in=tag_ids).distinct()
            except ValueError:
                pass  # 잘못된 태그 ID는 무시
        return queryset

    def perform_create(self, serializer):
        """
        스터디 생성 시 자동 번역 및 멤버 설정
        
        자동 번역 로직:
        - 사용자 언어가 기본 언어('en')가 아닌 경우:
           - title_{user_language} → title_en 자동 번역
           - goal_{user_language} → goal_en 자동 번역
        - 사용자 언어가 기본 언어('en')인 경우:
           - 번역하지 않음 (영어가 기본 언어)
        
        번역 조건:
        - 현재 언어의 제목/목표가 있고, 다른 언어의 제목/목표가 비어있을 때
        - OpenAI API를 사용하여 실시간 번역 수행
        - 번역 실패 시에도 스터디 생성은 계속 진행 (에러 로그만 기록)
        
        번역 모델: gpt-3.5-turbo
        타임아웃: 10초
        최대 토큰: 100
        온도: 0.3 (일관된 번역 품질)
        
        작성일: 2025-08-17
        작성자: AI Assistant
        """
        # 현재 사용자를 created_by로 설정 (익명 사용자는 None)
        if self.request.user.is_authenticated:
            # 언어 설정: request data에서 명시적으로 전달된 언어를 우선 사용
            # 없으면 사용자 프로필 언어 사용
            user_language = self.request.data.get('created_language')  # 프론트엔드에서 명시적으로 전달
            if not user_language:
                # 사용자 프로필에서 언어 설정 가져오기
                from quiz.utils.multilingual_utils import BASE_LANGUAGE
                user_language = BASE_LANGUAGE  # 기본값
                try:
                    if hasattr(self.request.user, 'profile'):
                        user_language = self.request.user.profile.language
                        logger.info(f"[STUDY_CREATE] user.profile에서 언어 설정 가져옴: {user_language}")
                    elif hasattr(self.request.user, 'userprofile'):
                        user_language = self.request.user.userprofile.language
                        logger.info(f"[STUDY_CREATE] user.userprofile에서 언어 설정 가져옴: {user_language}")
                    else:
                        logger.warning(f"[STUDY_CREATE] 사용자 프로필을 찾을 수 없음, 기본값 사용: {user_language}")
                except Exception as e:
                    logger.error(f"[STUDY_CREATE] 언어 설정 가져오기 실패: {e}")
            else:
                logger.info(f"[STUDY_CREATE] request data에서 언어 설정 가져옴: {user_language}")
            
            # 스터디 생성 요청 데이터 로깅 (모든 언어 동일하게 처리)
            goal_data_request = {f'goal_{lang}': self.request.data.get(f'goal_{lang}', 'N/A') 
                                for lang in SUPPORTED_LANGUAGES}
            goal_data_validated = {f'goal_{lang}': serializer.validated_data.get(f'goal_{lang}', 'N/A') 
                                  for lang in SUPPORTED_LANGUAGES}
            logger.info(f"[STUDY_CREATE] 요청 데이터 - goals: {goal_data_request}")
            logger.info(f"[STUDY_CREATE] validated_data - goals: {goal_data_validated}")
            
            # 스터디 생성 시 언어 자동 설정
            # 초기 저장 시에는 supported_languages 업데이트를 건너뛰기 (번역 완료 후 업데이트)
            study = serializer.save(
                created_by=self.request.user,
                created_language=user_language
            )
            
            # 저장된 스터디 데이터 로깅 (모든 언어 동일하게 처리)
            goal_data_saved = {f'goal_{lang}': getattr(study, f'goal_{lang}', 'N/A') 
                              for lang in SUPPORTED_LANGUAGES}
            logger.info(f"[STUDY_CREATE] 저장된 스터디 - id: {study.id}, goals: {goal_data_saved}")
            # 초기 저장 시 supported_languages 자동 업데이트 건너뛰기 플래그 설정
            study._skip_auto_supported_languages = True
            # 초기에는 생성 언어만 지원하도록 설정
            study.supported_languages = user_language
            study.save()
            
            # 다국어 콘텐츠 직접 처리 (Study 생성 시 즉시 번역)
            # 영어를 기본 언어로 하여, 다른 언어는 영어로 번역
            try:
                # 영어가 아닌 언어로 입력한 경우 영어로 번역
                from quiz.utils.multilingual_utils import BASE_LANGUAGE, LANGUAGE_EN
                if user_language != LANGUAGE_EN:
                    fields_to_translate = ['title', 'goal']
                    translation_success = False
                    
                    for field_name in fields_to_translate:
                        # 현재 언어 필드
                        current_field = f"{field_name}_{user_language}"
                        # 영어 필드 (기본 언어)
                        en_field = f"{field_name}_{LANGUAGE_EN}"
                        
                        # 현재 언어 내용 가져오기
                        current_content = getattr(study, current_field, None)
                        
                        if current_content and current_content.strip():
                            # 현재 언어 → 영어 번역 수행
                            try:
                                translated_text = self._translate_content(
                                    current_content, 
                                    user_language, 
                                    BASE_LANGUAGE
                                )
                                
                                if translated_text:
                                    # 번역된 텍스트를 영어 필드에 저장
                                    setattr(study, en_field, translated_text)
                                    translation_success = True
                                    logger.info(f"[STUDY_CREATE] {field_name} 번역 완료: {user_language} → {BASE_LANGUAGE}")
                                else:
                                    logger.warning(f"[STUDY_CREATE] {field_name} 번역 실패: {user_language} → {BASE_LANGUAGE}")
                            except Exception as e:
                                logger.error(f"[STUDY_CREATE] {field_name} 번역 중 오류: {e}")
                        else:
                            logger.info(f"[STUDY_CREATE] {field_name} 건너뜀: {current_field}에 콘텐츠가 없음")
                    
                    # 번역이 성공적으로 완료된 경우에만 저장 및 supported_languages 업데이트
                    if translation_success:
                        # 플래그를 제거하여 번역 완료 후 supported_languages가 정상적으로 업데이트되도록 함
                        study._skip_auto_supported_languages = False
                        study.save()  # 이제 supported_languages가 번역 완료 상태에 맞게 업데이트됨
                        logger.info(f"[STUDY_CREATE] 다국어 콘텐츠 처리 완료 (번역 성공): {study.id}, supported_languages: {study.supported_languages}")
                    else:
                        # 번역이 실패한 경우에도 플래그를 제거하여 다음 번역 시도 시 업데이트 가능하도록 함
                        study._skip_auto_supported_languages = False
                        logger.warning(f"[STUDY_CREATE] 번역이 완료되지 않아 supported_languages가 생성 언어만 포함: {study.id}, supported_languages: {study.supported_languages}")
                else:
                    # 영어 사용자는 번역하지 않음 (영어가 기본 언어)
                    # MultilingualContentManager는 번역이 필요한 경우에만 사용
                    manager = MultilingualContentManager(study, self.request.user, ['title', 'goal'])
                    manager.handle_multilingual_update()
                    
            except Exception as e:
                logger.error(f"[STUDY_CREATE] 다국어 콘텐츠 처리 실패: {e}")
            
            # tags 필드 처리 (ManyToManyField는 별도로 처리해야 함)
            if 'tags' in self.request.data:
                tag_ids = self.request.data.get('tags', [])
                logger.info(f"[STUDY_CREATE] 태그 설정 - study_id: {study.id}, tag_ids: {tag_ids}")
                
                # 유효한 태그 ID만 필터링
                valid_tag_ids = []
                for tag_id in tag_ids:
                    try:
                        from ..models import Tag
                        tag = Tag.objects.get(id=tag_id)
                        valid_tag_ids.append(tag_id)
                        user_lang = get_user_language(self.request)
                        tag_name = get_localized_field(tag, 'name', user_lang, '')
                        logger.info(f"[STUDY_CREATE] 유효한 태그 ID: {tag_id} ({tag_name})")
                    except Tag.DoesNotExist:
                        logger.warning(f"[STUDY_CREATE] 존재하지 않는 태그 ID: {tag_id}")
                
                # 태그는 반드시 1개 이상 필요
                if not valid_tag_ids:
                    study.delete()  # 생성된 스터디 삭제
                    from rest_framework.response import Response
                    from rest_framework import status
                    return Response(
                        {'error': '스터디에는 반드시 1개 이상의 태그가 필요합니다.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # 태그 설정
                study.tags.set(valid_tag_ids)
                logger.info(f"[STUDY_CREATE] 스터디 태그 설정 완료 - 총 {len(valid_tag_ids)}개 태그")
            else:
                # 태그가 제공되지 않은 경우
                study.delete()  # 생성된 스터디 삭제
                from rest_framework.response import Response
                from rest_framework import status
                return Response(
                    {'error': '스터디에는 반드시 1개 이상의 태그가 필요합니다.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 스터디 생성자를 자동으로 study_admin 역할의 멤버로 추가
            Member.objects.create(
                user=self.request.user,
                study=study,
                name=self.request.user.username,
                email=self.request.user.email,
                role='study_admin',
                is_active=True
            )
        else:
            serializer.save(created_by=None)
        
        # 캐시 무효화 (StudyCacheManager 사용)
        try:
            # 모든 사용자의 스터디 관련 캐시 무효화
            StudyCacheManager.invalidate_all_study_cache()
            logger.info(f"[STUDY_CREATE] StudyCacheManager를 통한 캐시 무효화 완료")
        except Exception as e:
            logger.error(f"[STUDY_CREATE] StudyCacheManager 캐시 무효화 실패: {e}")
            # 폴백: 기존 방식으로 캐시 무효화
            self._invalidate_study_cache()
        
        # 추가 캐시 무효화 (K8s Redis 환경 대응)
        try:
            from django.core.cache import cache
            # Redis 패턴 기반 캐시 무효화
            if hasattr(cache, 'delete_pattern'):
                cache.delete_pattern("studies_*")
                cache.delete_pattern("exams_*")
                logger.info(f"[STUDY_CREATE] Redis 패턴 기반 추가 캐시 무효화 완료")
            else:
                # 로컬 캐시의 경우 전체 클리어
                cache.clear()
                logger.info(f"[STUDY_CREATE] 로컬 캐시 전체 클리어 완료")
        except Exception as e:
            logger.error(f"[STUDY_CREATE] 추가 캐시 무효화 실패: {e}")

    def perform_update(self, serializer):
        # 권한 확인
        user = self.request.user
        study = serializer.instance
        
        # 받은 파라미터 로깅
        logger.info(f"[STUDY_UPDATE] 받은 파라미터 - request.data: {self.request.data}")
        
        # 변경 전 상태 저장
        old_title_ko = study.title_ko
        old_title_en = study.title_en
        old_goal_ko = study.goal_ko
        old_goal_en = study.goal_en
        
        logger.info(f"[STUDY_UPDATE] 변경 전 - title_ko: '{old_title_ko}', title_en: '{old_title_en}', goal_ko: '{old_goal_ko}', goal_en: '{old_goal_en}'")
        
        # 사용자 프로필 상세 로깅
        logger.info(f"[STUDY_UPDATE] 사용자 정보 - user.id: {user.id}, username: {user.username}")
        logger.info(f"[STUDY_UPDATE] userprofile 존재 여부: {hasattr(user, 'userprofile')}")
        if hasattr(user, 'userprofile'):
            logger.info(f"[STUDY_UPDATE] userprofile 객체: {user.userprofile}")
            logger.info(f"[STUDY_UPDATE] userprofile.language: {getattr(user.userprofile, 'language', 'N/A')}")
        else:
            logger.info(f"[STUDY_UPDATE] userprofile이 존재하지 않음")
        
        # 현재 사용자 언어 설정을 확인하여 번역 방향 결정
        from quiz.utils.multilingual_utils import BASE_LANGUAGE
        current_user_language = BASE_LANGUAGE  # 기본값
        
        if hasattr(user, 'profile') and user.profile:
            # 사용자 프로필이 있으면 그것을 우선으로 사용 (related_name='profile' 사용)
            from quiz.utils.multilingual_utils import BASE_LANGUAGE
            current_user_language = getattr(user.profile, 'language', BASE_LANGUAGE)
            logger.info(f"[STUDY_UPDATE] user.profile에서 언어 설정 가져옴: {current_user_language}")
        else:
            # userprofile이 없는 경우에만 프론트엔드 데이터로 언어 자동 감지
            logger.warning(f"[STUDY_UPDATE] userprofile을 찾을 수 없어 프론트엔드 데이터로 언어 자동 감지")
            
            # title_en과 title_ko 중 어느 것이 더 최신인지 확인
            # 사용자 프로필 언어를 우선적으로 사용
            from quiz.utils.multilingual_utils import BASE_LANGUAGE
            current_user_language = BASE_LANGUAGE  # 기본값은 'en'
            
            if self.request.user.is_authenticated:
                try:
                    if hasattr(self.request.user, 'profile') and hasattr(self.request.user.profile, 'language'):
                        current_user_language = self.request.user.profile.language
                        logger.info(f"[STUDY_UPDATE] user.profile에서 언어 설정 가져옴: {current_user_language}")
                    elif hasattr(self.request.user, 'userprofile') and hasattr(self.request.user.userprofile, 'language'):
                        current_user_language = self.request.user.userprofile.language
                        logger.info(f"[STUDY_UPDATE] user.userprofile에서 언어 설정 가져옴: {current_user_language}")
                except Exception as e:
                    logger.error(f"[STUDY_UPDATE] 언어 설정 가져오기 실패: {e}")
            
            # 요청 데이터에서 언어 힌트 확인 (프로필 언어가 없을 때만)
            if current_user_language == BASE_LANGUAGE:
                # 모든 언어 확인 (ko, en, es, zh, ja)
                available_languages = []
                for lang in SUPPORTED_LANGUAGES:
                    if self.request.data.get(f'title_{lang}'):
                        available_languages.append(lang)
                
                if len(available_languages) == 1:
                    current_user_language = available_languages[0]
                    logger.info(f"[STUDY_UPDATE] title_{current_user_language}만 있어서 {current_user_language} 모드로 감지")
                elif len(available_languages) > 1:
                    # 여러 언어가 있는 경우, 더 긴 텍스트가 있는 쪽을 우선
                    max_length = 0
                    selected_lang = BASE_LANGUAGE
                    for lang in available_languages:
                        length = len(self.request.data.get(f'title_{lang}', ''))
                        if length > max_length:
                            max_length = length
                            selected_lang = lang
                    current_user_language = selected_lang
                    logger.info(f"[STUDY_UPDATE] 여러 언어 중 {current_user_language}가 가장 길어서 선택 (길이: {max_length})")
                else:
                    logger.warning(f"[STUDY_UPDATE] 언어 감지 실패, 기본값 '{BASE_LANGUAGE}' 사용")
        
        logger.info(f"[STUDY_UPDATE] 최종 설정된 current_user_language: {current_user_language}")
        
        # admin_role 사용자는 모든 스터디 수정 가능
        is_admin = False
        if hasattr(user, 'is_superuser') and user.is_superuser:
            is_admin = True
        elif hasattr(user, 'profile') and hasattr(user.profile, 'role') and user.profile.role == 'admin_role':
            is_admin = True
        
        if not is_admin:
            # 스터디 생성자 또는 스터디 관리자인지 확인
            is_creator = study.created_by == user
            is_study_admin = study.members.filter(
                user=user, 
                is_active=True,
                role__in=['study_admin', 'study_leader']
            ).exists()
            
            if not (is_creator or is_study_admin):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('이 스터디를 수정할 권한이 없습니다.')
        
        # supported_languages가 명시적으로 제공된 경우, 플래그를 먼저 설정
        if 'supported_languages' in self.request.data:
            # serializer.save() 전에 플래그 설정 (to_representation에서도 유지되도록)
            serializer.instance._skip_auto_supported_languages = True
        
        study = serializer.save()
        
        # supported_languages가 명시적으로 제공된 경우, 직접 저장
        if 'supported_languages' in self.request.data:
            study._skip_auto_supported_languages = True
            study.supported_languages = self.request.data.get('supported_languages', '')
            study.save(update_fields=['supported_languages'])
        
        # 변경된 필드 확인
        changed_fields = []
        if old_title_ko != study.title_ko:
            changed_fields.append('title_ko')
        if old_title_en != study.title_en:
            changed_fields.append('title_en')
        if old_goal_ko != study.goal_ko:
            changed_fields.append('goal_ko')
        if old_goal_en != study.goal_en:
            changed_fields.append('goal_en')
        
        logger.info(f"[STUDY_UPDATE] 변경된 필드: {changed_fields}")
        
        # tags 필드 처리 (ManyToManyField는 별도로 처리해야 함)
        if 'tags' in self.request.data:
            tag_ids = self.request.data.get('tags', [])
            logger.info(f"[STUDY_UPDATE] 태그 업데이트 - tag_ids: {tag_ids}")
            
            # 유효한 태그 ID만 필터링
            valid_tag_ids = []
            for tag_id in tag_ids:
                try:
                    tag = Tag.objects.get(id=tag_id)
                    valid_tag_ids.append(tag_id)
                    tag_lang = tag.created_language if hasattr(tag, 'created_language') else BASE_LANGUAGE
                    from quiz.utils.multilingual_utils import BASE_LANGUAGE
                    tag_name = get_localized_field(tag, 'name', tag_lang, 'Unknown')
                    logger.info(f"[STUDY_UPDATE] 유효한 태그 ID: {tag_id} ({tag_name})")
                except Tag.DoesNotExist:
                    logger.warning(f"[STUDY_UPDATE] 존재하지 않는 태그 ID: {tag_id}")
            
            # 태그는 반드시 1개 이상 필요
            if not valid_tag_ids:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'tags': '스터디에는 반드시 1개 이상의 태그가 필요합니다.'})
            
            # 태그 설정
            study.tags.set(valid_tag_ids)
            logger.info(f"[STUDY_UPDATE] 스터디 태그 설정 완료 - 총 {len(valid_tag_ids)}개 태그")
        
        # 변경된 필드가 있을 때만 번역 수행
        if changed_fields:
            self._handle_study_multilingual_update(study, current_user_language, changed_fields)
        
        # 캐시 무효화 (StudyCacheManager 사용)
        try:
            # 수정된 스터디 관련 캐시 무효화
            StudyCacheManager.invalidate_study_cache(study.id)
            StudyCacheManager.invalidate_all_study_cache()
            logger.info(f"[STUDY_UPDATE] StudyCacheManager를 통한 캐시 무효화 완료: {study.id}")
        except Exception as e:
            logger.error(f"[STUDY_UPDATE] StudyCacheManager 캐시 무효화 실패: {e}")
            # 폴백: 기존 방식으로 캐시 무효화
            self._invalidate_study_cache()
        
    def perform_destroy(self, instance):
        # 권한 확인
        user = self.request.user
        
        # admin_role 사용자는 모든 스터디 삭제 가능
        is_admin = False
        if hasattr(user, 'is_superuser') and user.is_superuser:
            is_admin = True
        elif hasattr(user, 'profile') and hasattr(user.profile, 'role') and user.profile.role == 'admin_role':
            is_admin = True
        
        if not is_admin:
            # 스터디 생성자 또는 스터디 관리자인지 확인
            is_creator = instance.created_by == user
            is_study_admin = instance.members.filter(
                user=user, 
                is_active=True,
                role__in=['study_admin', 'study_leader']
            ).exists()
            
            if not (is_creator or is_study_admin):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('이 스터디를 삭제할 권한이 없습니다.')
        
        study_id = instance.id
        instance.delete()
        # 캐시 무효화 (StudyCacheManager 사용)
        try:
            # 삭제된 스터디 관련 캐시 무효화
            StudyCacheManager.invalidate_study_cache(study_id)
            StudyCacheManager.invalidate_all_study_cache()
            logger.info(f"[STUDY_DELETE] StudyCacheManager를 통한 캐시 무효화 완료: {study_id}")
        except Exception as e:
            logger.error(f"[STUDY_DELETE] StudyCacheManager 캐시 무효화 실패: {e}")
            # 폴백: 기존 방식으로 캐시 무효화
            self._invalidate_study_cache()
        
    def _invalidate_study_cache(self):
        """스터디 관련 캐시를 무효화하는 헬퍼 메서드"""
        try:
            from django.core.cache import cache
            # 스터디 캐시 무효화
            cache.clear()
            print("🔄 StudyViewSet 스터디 캐시 무효화 완료")
            
            # 시험 관련 캐시도 무효화 (멤버 변경으로 인한 시험 접근 권한 변경)
            try:
                cache.delete_pattern("exams_*")
                print("🔄 시험 캐시 무효화 완료 (Redis)")
            except AttributeError:
                # 로컬 캐시의 경우 개별 키 삭제
                cache.delete("exams_anonymous")
                cache.delete("exams_anonymous_true")
                cache.delete("exams_anonymous_false")
                cache.delete("exams_anonymous_all")
                # 관리자 사용자 캐시도 삭제
                cache.delete("exams_1")
                cache.delete("exams_1_true")
                cache.delete("exams_1_false")
                cache.delete("exams_1_all")
                print("🔄 시험 캐시 무효화 완료 (로컬)")
        except Exception as e:
            print(f"StudyViewSet 캐시 무효화 중 오류: {e}")

    def _handle_study_multilingual_update(self, study, current_user_language, changed_fields):
        """
        스터디의 다국어 콘텐츠를 직접 처리합니다.
        
        Args:
            study: 업데이트된 스터디 인스턴스
            current_user_language: 현재 사용자 언어 ('ko', 'en', 'es', 'zh', 'ja')
            changed_fields: 실제로 변경된 필드 목록
        """
        try:
            logger.info(f"[STUDY_UPDATE] 다국어 콘텐츠 직접 처리 시작: 언어={current_user_language}, 변경된 필드={changed_fields}")
            
            # 번역이 필요한 필드들 처리
            fields_to_translate = ['title', 'goal']
            
            # 변경된 필드만 번역 수행
            fields_to_update = []
            
            for field_name in fields_to_translate:
                # 현재 언어의 필드
                current_field = f"{field_name}_{current_user_language}"
                # 대상 언어의 필드 (기본 언어로 번역)
                from quiz.utils.multilingual_utils import BASE_LANGUAGE
                # 사용자 언어가 기본 언어가 아닐 때만 기본 언어로 번역
                if current_user_language != BASE_LANGUAGE:
                    target_language = BASE_LANGUAGE
                    target_field = f"{field_name}_{target_language}"
                else:
                    # 사용자 언어가 기본 언어이면 번역하지 않음
                    continue
                
                # 현재 언어 필드가 변경되었는지 확인
                if current_field in changed_fields:
                    # 현재 언어의 콘텐츠 가져오기
                    current_content = getattr(study, current_field, None)
                    
                    if current_content and current_content.strip():
                        # 변경된 내용이 있으면 번역 수행
                        try:
                            translated_text = self._translate_content(
                                current_content, 
                                current_user_language, 
                                target_language
                            )
                            
                            if translated_text and translated_text != current_content:
                                setattr(study, target_field, translated_text)
                                fields_to_update.append(target_field)
                                logger.info(f"[STUDY_UPDATE] {field_name} 번역 완료: {current_user_language} → {target_language}")
                            else:
                                logger.warning(f"[STUDY_UPDATE] {field_name} 번역 실패 또는 번역 결과가 원본과 동일")
                        except Exception as e:
                            logger.error(f"[STUDY_UPDATE] {field_name} 번역 중 오류: {e}")
                    else:
                        logger.info(f"[STUDY_UPDATE] {field_name} 건너뜀: {current_field}에 콘텐츠가 없음")
                else:
                    logger.info(f"[STUDY_UPDATE] {field_name} 건너뜀: {current_field}가 변경되지 않음")
            
            # 번역된 필드만 저장
            if fields_to_update:
                study.save(update_fields=fields_to_update)
                logger.info(f"[STUDY_UPDATE] 번역된 필드 저장 완료: {fields_to_update}")
            else:
                logger.info(f"[STUDY_UPDATE] 번역할 필드 없음")
            
        except Exception as e:
            logger.error(f"[STUDY_UPDATE] 다국어 콘텐츠 처리 중 오류: {e}")

    def _translate_content(self, text, from_language, to_language):
        """
        텍스트를 지정된 언어로 번역하는 통합 메서드 (Gemini 폴백 지원)
        
        Args:
            text (str): 번역할 텍스트
            from_language (str): 원본 언어 ('ko', 'en', 'es', 'zh', 'ja')
            to_language (str): 대상 언어 ('ko', 'en', 'es', 'zh', 'ja')
        
        Returns:
            str: 번역된 텍스트, 실패 시 None
        """
        if not text or not text.strip():
            return None
        
        # batch_translate_texts를 사용하여 Gemini 폴백 지원
        from quiz.utils.multilingual_utils import batch_translate_texts
        
        try:
            translated_results = batch_translate_texts([text], from_language, to_language)
            if translated_results and len(translated_results) > 0 and translated_results[0]:
                translated_text = translated_results[0]
                logger.info(f"[TRANSLATE] 번역 성공: '{text}' → '{translated_text}' ({from_language} → {to_language})")
                return translated_text
            else:
                logger.warning(f"[TRANSLATE] 번역 실패: {from_language} → {to_language}")
                return None
        except Exception as e:
            logger.warning(f"[TRANSLATE] 번역 중 예상치 못한 오류: {str(e)} - {from_language} → {to_language}")
            return None

    def _translate_to_base_language(self, text, from_language):
        """
        텍스트를 기본 언어(영어)로 번역하는 헬퍼 메서드
        
        Args:
            text (str): 번역할 텍스트
            from_language (str): 원본 언어 ('ko', 'en', 'es', 'zh', 'ja')
        
        Returns:
            str: 영어로 번역된 텍스트, 실패 시 None
        
        내부적으로 _translate_content 메서드를 사용하여 최적화
        """
        from quiz.utils.multilingual_utils import BASE_LANGUAGE
        return self._translate_content(text, from_language, BASE_LANGUAGE)

    def retrieve(self, request, *args, **kwargs):
        """
        스터디 상세 조회 - 다국어 처리 최적화
        
        최적화 포인트:
        1. 사용자 언어 설정을 한 번만 확인
        2. 다국어 콘텐츠를 효율적으로 로드
        3. 응답 데이터에 언어별 메타데이터 포함
        4. 캐시 활용 가능성 고려
        """
        response = super().retrieve(request, *args, **kwargs)
        
        if hasattr(response, 'data') and response.data:
            # 사용자 언어 설정 확인 (한 번만)
            from quiz.utils.multilingual_utils import BASE_LANGUAGE
            user_language = BASE_LANGUAGE  # 기본값
            if request.user.is_authenticated and hasattr(request.user, 'userprofile'):
                user_language = request.user.userprofile.language
            
            # 다국어 콘텐츠 메타데이터 추가
            study_data = response.data
            study_data['current_user_language'] = user_language
            study_data['available_languages'] = []
            
            # 사용 가능한 언어 목록 생성 (모든 언어 동일하게 처리)
            for lang in SUPPORTED_LANGUAGES:
                if study_data.get(f'title_{lang}') or study_data.get(f'goal_{lang}'):
                    study_data['available_languages'].append(lang)
            
            # 현재 언어 우선 콘텐츠 설정 (모든 언어 동일하게 처리)
            from quiz.utils.multilingual_utils import BASE_LANGUAGE
            # 사용자 언어를 우선 사용, 없으면 기본 언어('en') 사용
            title = study_data.get(f'title_{user_language}')
            goal = study_data.get(f'goal_{user_language}')
            
            # 사용자 언어에 해당하는 콘텐츠가 없으면 기본 언어로 폴백
            if not title:
                title = study_data.get(f'title_{BASE_LANGUAGE}')
                # 기본 언어도 없으면 다른 언어 중 하나라도 사용
                if not title:
                    for lang in SUPPORTED_LANGUAGES:
                        if study_data.get(f'title_{lang}'):
                            title = study_data.get(f'title_{lang}')
                            break
            
            if not goal:
                goal = study_data.get(f'goal_{BASE_LANGUAGE}')
                # 기본 언어도 없으면 다른 언어 중 하나라도 사용
                if not goal:
                    for lang in SUPPORTED_LANGUAGES:
                        if study_data.get(f'goal_{lang}'):
                            goal = study_data.get(f'goal_{lang}')
                            break
            
            study_data['title'] = title or ''
            study_data['goal'] = goal or ''
            
            # 로깅 (요약 정보만)
            study_title = study_data.get('title', 'Unknown')
            tasks_count = len(study_data.get('tasks', []))
            members_count = len(study_data.get('members', []))
            logger.info(f"Study retrieve response: title='{study_title}', tasks={tasks_count}, members={members_count}, language={user_language}")
        else:
            logger.info("Study retrieve response: empty")
        
        return response

    def list(self, request, *args, **kwargs):
        import time
        from django.db import connection
        start_time = time.time()
        
        # 사용자 언어 설정 확인 (캐시 키에 포함하기 위해 먼저 확인)
        from quiz.utils.multilingual_utils import BASE_LANGUAGE
        # 1. API 요청의 lang 파라미터를 먼저 확인
        user_language = request.query_params.get('lang')
        # 2. lang 파라미터가 없으면 인증된 사용자의 언어 사용
        if not user_language and request.user.is_authenticated:
            if hasattr(request.user, 'userprofile') and hasattr(request.user.userprofile, 'language'):
                user_language = request.user.userprofile.language
            elif hasattr(request.user, 'profile') and hasattr(request.user.profile, 'language'):
                user_language = request.user.profile.language
        # 3. 여전히 없으면 기본 언어('en') 사용
        if not user_language:
            user_language = BASE_LANGUAGE
        
        # 캐시 키 생성 (태그 필터링과 my_studies 파라미터 포함)
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        is_public = request.query_params.get('is_public', 'all')
        my_studies = request.query_params.get('my_studies', 'false')
        tags = request.query_params.getlist('tags')
        
        # DevOps 도메인 필터링: devops 도메인인 경우 자동으로 카테고리 태그 필터 적용
        from quiz.utils.domain_utils import is_devops_domain, get_devops_category_tag_ids
        if is_devops_domain(request):
            devops_tag_ids = get_devops_category_tag_ids()
            if devops_tag_ids:
                # 기존 tags와 병합 (중복 제거)
                existing_tag_ids = [int(tid) for tid in tags if str(tid).isdigit()]
                # devops 태그 ID와 교집합만 유지 (둘 다 만족해야 함)
                if existing_tag_ids:
                    # devops 태그 중에서 기존 태그와 일치하는 것만 사용
                    tags = [str(tid) for tid in existing_tag_ids if tid in devops_tag_ids]
                else:
                    # 기존 태그가 없으면 devops 태그만 사용
                    tags = [str(tid) for tid in devops_tag_ids]
                logger.info(f"[STUDY_LIST] DevOps 도메인 필터링 적용: {len(tags)}개 태그")
        
        tags_str = ','.join(sorted(tags)) if tags else 'no-tags'
        cache_key = f"studies_{user_id}_{is_public}_{my_studies}_{tags_str}_{user_language}"
        
        # 강제 새로고침 파라미터 확인
        force_refresh = request.query_params.get('refresh') == 'true'
        
        # 캐시에서 데이터 확인 (강제 새로고침이 아닌 경우에만)
        cache_check_start = time.time()
        if not force_refresh:
            try:
                from django.core.cache import cache
                cached_data = cache.get(cache_key)
                cache_check_time = time.time() - cache_check_start
                if cached_data:
                    total_time = time.time() - start_time
                    logger.info(f"[STUDY_LIST] 캐시 히트: user_id={user_id}, 캐시 조회={cache_check_time*1000:.2f}ms, 총 시간={total_time*1000:.2f}ms")
                    return Response(cached_data)
            except Exception as e:
                logger.warning(f"[STUDY_LIST] 캐시 확인 중 오류: {e}")
        cache_check_time = time.time() - cache_check_start
        
        # 캐시가 없으면 새로 생성
        # 시리얼라이저 컨텍스트에 미리 계산된 데이터 추가 (N+1 쿼리 방지)
        # get_serializer_context를 오버라이드하여 미리 계산된 데이터 추가
        original_get_serializer_context = self.get_serializer_context
        
        # 사용자별 진행률 데이터를 미리 계산
        user_progress_dict = {}
        user_exam_result_dict = {}
        user_last_progress_dict = {}
        
        progress_calc_start = time.time()
        queries_before = len(connection.queries)
        if request.user.is_authenticated:
            # queryset을 가져와서 진행률 데이터 미리 계산
            queryset = self.get_queryset()
            study_ids = list(queryset.values_list('id', flat=True))
            queryset_time = time.time() - progress_calc_start
            
            if study_ids:
                from ..models import StudyTaskProgress, ExamResult, StudyProgressRecord
                
                # 모든 스터디의 태스크 진행률을 한 번에 조회
                progress_query_start = time.time()
                progress_records = StudyTaskProgress.objects.filter(
                    user=request.user,
                    study_task__study_id__in=study_ids
                ).select_related('study_task', 'study_task__study', 'study_task__exam')
                
                for progress in progress_records:
                    study_id = progress.study_task.study_id
                    if study_id not in user_progress_dict:
                        user_progress_dict[study_id] = []
                    # StudyTaskProgress 객체를 직렬화 가능한 딕셔너리로 변환
                    user_progress_dict[study_id].append({
                        'study_task_id': progress.study_task_id,
                        'progress': progress.progress,
                        'id': progress.id,
                    })
                progress_query_time = time.time() - progress_query_start
                
                # 모든 스터디의 시험 결과를 한 번에 조회 (최적화: StudyTask를 먼저 조회하여 exam_id 목록 생성)
                exam_result_query_start = time.time()
                # 먼저 해당 스터디들의 exam_id 목록을 조회
                from ..models import StudyTask
                study_tasks = StudyTask.objects.filter(
                    study_id__in=study_ids
                ).select_related('exam').values_list('exam_id', 'study_id').distinct()
                
                # exam_id와 study_id 매핑 생성
                exam_to_study = {}
                exam_ids = []
                for exam_id, study_id in study_tasks:
                    if exam_id:  # exam_id가 None이 아닌 경우만
                        exam_ids.append(exam_id)
                        if exam_id not in exam_to_study:
                            exam_to_study[exam_id] = []
                        exam_to_study[exam_id].append(study_id)
                
                # exam_ids를 사용하여 ExamResult 조회 (더 효율적)
                if exam_ids:
                    exam_results = ExamResult.objects.filter(
                        user=request.user,
                        exam_id__in=exam_ids
                    ).select_related('exam')
                    
                    for result in exam_results:
                        exam_id = result.exam_id
                        if exam_id in exam_to_study:
                            for study_id in exam_to_study[exam_id]:
                                if study_id not in user_exam_result_dict:
                                    user_exam_result_dict[study_id] = {}
                                user_exam_result_dict[study_id][exam_id] = result
                exam_result_query_time = time.time() - exam_result_query_start
                
                # 모든 스터디의 최근 진행률 기록을 한 번에 조회
                # distinct('study_id')는 PostgreSQL 전용이므로 Python에서 처리
                last_progress_query_start = time.time()
                last_progress_records = StudyProgressRecord.objects.filter(
                    user=request.user,
                    study_id__in=study_ids
                ).order_by('study_id', '-recorded_at')
                
                # 각 study_id별로 최신 기록만 선택 (Python에서 처리)
                for record in last_progress_records:
                    study_id = record.study_id
                    if study_id not in user_last_progress_dict:
                        user_last_progress_dict[study_id] = record.recorded_at
                last_progress_query_time = time.time() - last_progress_query_start
            else:
                queryset_time = time.time() - progress_calc_start
                progress_query_time = 0
                exam_result_query_time = 0
                last_progress_query_time = 0
        else:
            queryset_time = 0
            progress_query_time = 0
            exam_result_query_time = 0
            last_progress_query_time = 0
        
        progress_calc_time = time.time() - progress_calc_start
        queries_after_progress = len(connection.queries)
        
        # 각 study별 진행률을 미리 계산 (N+1 쿼리 방지)
        study_progress_dict = {}
        study_correct_progress_dict = {}
        study_attempted_progress_dict = {}
        study_accuracy_dict = {}
        
        if request.user.is_authenticated and study_ids:
            progress_calc_detail_start = time.time()
            from ..models import StudyTask, ExamResultDetail
            from django.db.models import Count, Sum, Q
            
            # 각 study의 tasks를 미리 조회
            study_tasks_dict = {}
            for study_id in study_ids:
                study_tasks_dict[study_id] = []
            
            tasks = StudyTask.objects.filter(study_id__in=study_ids).select_related('exam').prefetch_related('exam__questions')
            for task in tasks:
                if task.study_id in study_tasks_dict:
                    study_tasks_dict[task.study_id].append(task)
            
            # exam별 questions 수를 미리 계산 (N+1 쿼리 방지)
            exam_question_count_dict = {}
            exam_ids = [task.exam_id for task in tasks if task.exam_id]
            if exam_ids:
                from ..models import ExamQuestion
                exam_question_counts = ExamQuestion.objects.filter(exam_id__in=exam_ids).values('exam_id').annotate(count=Count('id'))
                for item in exam_question_counts:
                    exam_question_count_dict[item['exam_id']] = item['count']
            
            # 각 study별로 진행률 계산
            for study_id in study_ids:
                tasks = study_tasks_dict.get(study_id, [])
                if not tasks:
                    continue
                
                total_progress = 0
                total_correct = 0
                total_attempted = 0
                total_questions = 0
                total_correct_attempts = 0
                total_attempts = 0
                task_count = 0
                
                for task in tasks:
                    if not task.exam:
                        continue
                    
                    exam_id = task.exam_id
                    # exam_result_dict에서 해당 exam의 결과 찾기
                    exam_result = user_exam_result_dict.get(study_id, {}).get(exam_id) if study_id in user_exam_result_dict else None
                    
                    if exam_result:
                        # ExamResultDetail에서 통계 계산
                        exam_result_details = ExamResultDetail.objects.filter(
                            result=exam_result
                        ).aggregate(
                            total_attempted=Count('id'),
                            total_correct=Count('id', filter=Q(is_correct=True))
                        )
                        
                        attempted_count = exam_result_details['total_attempted'] or 0
                        correct_count = exam_result_details['total_correct'] or 0
                    else:
                        attempted_count = 0
                        correct_count = 0
                    
                    # 미리 계산된 questions 수 사용
                    question_count = exam_question_count_dict.get(exam_id, 0)
                    
                    if question_count > 0:
                        task_progress = (attempted_count / question_count) * 100
                        total_progress += task_progress
                        total_questions += question_count
                        total_attempted += attempted_count
                        total_correct += correct_count
                        total_attempts += attempted_count
                        total_correct_attempts += correct_count
                        task_count += 1
                
                if task_count > 0:
                    study_progress_dict[study_id] = total_progress / task_count
                else:
                    study_progress_dict[study_id] = 0
                
                if total_questions > 0:
                    study_correct_progress_dict[study_id] = (total_correct / total_questions) * 100
                    study_attempted_progress_dict[study_id] = (total_attempted / total_questions) * 100
                else:
                    study_correct_progress_dict[study_id] = 0
                    study_attempted_progress_dict[study_id] = 0
                
                if total_attempts > 0:
                    study_accuracy_dict[study_id] = (total_correct_attempts / total_attempts) * 100
                else:
                    study_accuracy_dict[study_id] = None
            
            progress_calc_detail_time = time.time() - progress_calc_detail_start
            logger.info(f"[STUDY_LIST] 진행률 상세 계산 완료 - {progress_calc_detail_time*1000:.2f}ms")
        
        # get_serializer_context를 오버라이드하여 미리 계산된 데이터 추가
        def get_serializer_context_with_data():
            context = original_get_serializer_context()
            context['user_progress_dict'] = user_progress_dict
            context['user_exam_result_dict'] = user_exam_result_dict
            context['user_last_progress_dict'] = user_last_progress_dict
            context['study_progress_dict'] = study_progress_dict
            context['study_correct_progress_dict'] = study_correct_progress_dict
            context['study_attempted_progress_dict'] = study_attempted_progress_dict
            context['study_accuracy_dict'] = study_accuracy_dict
            return context
        
        # 임시로 get_serializer_context 메서드 교체
        self.get_serializer_context = get_serializer_context_with_data
        
        # 시리얼라이저 처리
        serializer_start = time.time()
        queries_before_serializer = len(connection.queries)
        try:
            response = super().list(request, *args, **kwargs)
        finally:
            # 원래 메서드 복원
            self.get_serializer_context = original_get_serializer_context
        serializer_time = time.time() - serializer_start
        queries_after_serializer = len(connection.queries)
        
        # 다국어 처리 최적화
        multilingual_start = time.time()
        if hasattr(response, 'data') and response.data:
            
            # 각 스터디에 다국어 콘텐츠 최적화 적용
            if isinstance(response.data, dict) and 'results' in response.data:
                studies = response.data['results']
                for study in studies:
                    self._optimize_study_multilingual_content(study, user_language)
            else:
                # 단일 스터디 목록인 경우
                for study in response.data:
                    self._optimize_study_multilingual_content(study, user_language)
        multilingual_time = time.time() - multilingual_start
        
        # 응답 데이터 캐시에 저장 (비동기 처리로 성능 개선)
        cache_save_start = time.time()
        try:
            if hasattr(response, 'data') and response.data:
                # Celery 태스크로 비동기 저장
                from quiz.tasks import save_study_list_cache
                save_study_list_cache.delay(cache_key, response.data, timeout=300)
                logger.debug(f"[STUDY_LIST] 캐시 저장 Celery 태스크 전송 완료: {cache_key}")
                
                # 전체 데이터셋 대신 요약 정보만 출력
                if isinstance(response.data, dict) and 'results' in response.data:
                    count = response.data.get('count', 0)
                    results_count = len(response.data.get('results', []))
                    logger.debug(f"[STUDY_LIST] response: count={count}, results_count={results_count}")
                else:
                    logger.debug(f"[STUDY_LIST] response: {len(response.data)} items")
            else:
                logger.debug("[STUDY_LIST] response: empty")
        except Exception as e:
            # Celery 태스크 전송 실패 시 동기 저장으로 폴백
            logger.warning(f"[STUDY_LIST] Celery 태스크 전송 실패, 동기 저장으로 폴백: {str(e)}")
            try:
                if hasattr(response, 'data') and response.data:
                    from django.core.cache import cache
                    cache.set(cache_key, response.data, 300)
                    logger.debug(f"[STUDY_LIST] 캐시 저장 완료 (동기 저장): {cache_key}")
            except Exception as e2:
                logger.error(f"[STUDY_LIST] 캐시 저장 중 오류: {e2}")
        cache_save_time = time.time() - cache_save_start
        
        total_time = time.time() - start_time
        total_queries = len(connection.queries)
        
        logger.info(f"[STUDY_LIST] 캐시 미스: user_id={user_id}, "
                   f"캐시 조회={cache_check_time*1000:.2f}ms, "
                   f"진행률 계산={progress_calc_time*1000:.2f}ms "
                   f"(queryset={queryset_time*1000:.2f}ms, "
                   f"progress={progress_query_time*1000:.2f}ms, "
                   f"exam_result={exam_result_query_time*1000:.2f}ms, "
                   f"last_progress={last_progress_query_time*1000:.2f}ms), "
                   f"시리얼라이저={serializer_time*1000:.2f}ms ({queries_after_serializer - queries_before_serializer}개 쿼리), "
                   f"다국어 처리={multilingual_time*1000:.2f}ms, "
                   f"캐시 저장 태스크 전송={cache_save_time*1000:.2f}ms, "
                   f"총 시간={total_time*1000:.2f}ms, 총 쿼리={total_queries}개")
        
        return response
    
    def _optimize_study_multilingual_content(self, study_data, user_language):
        """
        개별 스터디 데이터의 다국어 콘텐츠를 최적화하는 헬퍼 메서드
        
        Args:
            study_data (dict): 스터디 데이터 딕셔너리
            user_language (str): 사용자 언어 ('ko', 'en', 'es', 'zh', 'ja')
        """
        from quiz.utils.multilingual_utils import BASE_LANGUAGE
        
        # 사용 가능한 언어 목록 생성 (모든 언어 동일하게 처리)
        study_data['available_languages'] = []
        for lang in SUPPORTED_LANGUAGES:
            if study_data.get(f'title_{lang}') or study_data.get(f'goal_{lang}'):
                study_data['available_languages'].append(lang)
        
        # 현재 언어 우선 콘텐츠 설정 (모든 언어 동일하게 처리)
        # 사용자 언어를 우선 사용, 없으면 기본 언어('en') 사용
        title = study_data.get(f'title_{user_language}')
        goal = study_data.get(f'goal_{user_language}')
        
        # 사용자 언어에 해당하는 콘텐츠가 없으면 기본 언어로 폴백
        if not title:
            title = study_data.get(f'title_{BASE_LANGUAGE}')
            # 기본 언어도 없으면 다른 언어 중 하나라도 사용
            if not title:
                for lang in SUPPORTED_LANGUAGES:
                    if study_data.get(f'title_{lang}'):
                        title = study_data.get(f'title_{lang}')
                        break
        
        if not goal:
            goal = study_data.get(f'goal_{BASE_LANGUAGE}')
            # 기본 언어도 없으면 다른 언어 중 하나라도 사용
            if not goal:
                for lang in SUPPORTED_LANGUAGES:
                    if study_data.get(f'goal_{lang}'):
                        goal = study_data.get(f'goal_{lang}')
                        break
        
        study_data['title'] = title or ''
        study_data['goal'] = goal or ''
        study_data['display_title'] = title or ''
        study_data['display_goal'] = goal or ''
        
        # 언어별 완성도 정보 추가 (모든 언어 동일하게 처리)
        for lang in SUPPORTED_LANGUAGES:
            study_data[f'is_{lang}_complete'] = bool(study_data.get(f'title_{lang}') and study_data.get(f'goal_{lang}'))

    @action(detail=True, methods=['post'])
    def add_task(self, request, pk=None):
        study = self.get_object()
        task_data = request.data.copy()
        task_data['study'] = study.id
        print(f"Task 추가 요청 데이터: {task_data}")
        print(f"exam 필드 값: {task_data.get('exam')}")
        print(f"exam 필드 타입: {type(task_data.get('exam'))}")
        
        # StudyTaskUpdateSerializer를 사용하여 study와 exam 필드를 쓸 수 있도록 함
        from quiz.serializers import StudyTaskUpdateSerializer
        serializer = StudyTaskUpdateSerializer(data=task_data)
        if serializer.is_valid():
            task = serializer.save()
            print(f"Task 저장 성공: {task.id} - exam: {task.exam}")
            # 응답은 StudyTaskSerializer를 사용하여 완전한 데이터 반환
            from quiz.serializers import StudyTaskSerializer
            response_serializer = StudyTaskSerializer(task, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        else:
            print(f"Task 저장 실패 - 에러: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def update_task_progress(self, request, pk=None):
        study = self.get_object()
        task_id = request.data.get('task_id')
        new_progress = request.data.get('progress')
        
        try:
            task = study.tasks.get(id=task_id)
            StudyTaskProgress.objects.update_or_create(
                user=request.user,
                study_task=task,
                defaults={'progress': new_progress}
            )
            return Response({'message': 'Progress updated'}, status=status.HTTP_200_OK)
        except StudyTask.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """스터디에 멤버 추가"""
        study = self.get_object()
        member_data = request.data.copy()
        member_data['study'] = study.id
        
        # 빈 문자열을 None으로 변환
        for field in ['email', 'member_id', 'affiliation', 'location']:
            if field in member_data and member_data[field] == '':
                member_data[field] = None
        
        serializer = MemberSerializer(data=member_data)
        if serializer.is_valid():
            serializer.save()
            # 캐시 무효화 (StudyCacheManager 사용)
            try:
                # 멤버가 추가된 스터디 관련 캐시 무효화
                StudyCacheManager.invalidate_study_cache(member.study.id)
                StudyCacheManager.invalidate_all_study_cache()
                logger.info(f"[MEMBER_CREATE] StudyCacheManager를 통한 캐시 무효화 완료: study_id={member.study.id}")
            except Exception as e:
                logger.error(f"[MEMBER_CREATE] StudyCacheManager 캐시 무효화 실패: {e}")
                # 폴백: 기존 방식으로 캐시 무효화
                self._invalidate_study_cache()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_members(self, request, pk=None):
        """스터디의 멤버 목록을 가져옵니다."""
        try:
            study = self.get_object()
            members = Member.objects.filter(study=study)
            
            # 멤버들의 사용자 연결 상태 확인 및 자동 연결 시도
            for member in members:
                if not member.user and member.name:
                    try:
                        user = User.objects.get(username=member.name)
                        member.user = user
                        member.save()
                        print(f"멤버 사용자 자동 연결: {member.name} -> {user.id}")
                    except User.DoesNotExist:
                        pass  # 사용자를 찾을 수 없으면 무시
            
            serializer = MemberSerializer(members, many=True)
            return Response(serializer.data)
        except Study.DoesNotExist:
            return Response({'error': '스터디를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def tags(self, request):
        """사용 가능한 태그 목록 조회 (사용 빈도 포함)"""
        try:
            from django.db.models import Count
            
            # 태그 사용 빈도 계산
            tags = Tag.objects.annotate(
                usage_count=Count('studies')
            ).order_by('-usage_count', 'name_ko')
            
            serializer = TagSerializer(tags, many=True, context={'request': request})
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"태그 목록 조회 중 오류 발생: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StudyTaskViewSet(viewsets.ModelViewSet):
    queryset = StudyTask.objects.all()
    serializer_class = StudyTaskSerializer

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return StudyTaskUpdateSerializer
        return StudyTaskSerializer

    def perform_create(self, serializer):
        print(f"Task 생성 요청 데이터: {self.request.data}")
        print(f"serializer.validated_data: {serializer.validated_data}")
        
        # study 필드가 제대로 설정되었는지 확인
        if 'study' not in serializer.validated_data:
            from rest_framework.exceptions import ValidationError
            print(f"study 필드가 없음. validated_data: {serializer.validated_data}")
            raise ValidationError('study 필드가 필요합니다.')
        
        # 권한 확인
        user = self.request.user
        study = serializer.validated_data['study']
        print(f"study 객체: {study}")
        print(f"study.id: {study.id}")
        
        # admin_role 사용자는 모든 Task 생성 가능
        is_admin = False
        if hasattr(user, 'is_superuser') and user.is_superuser:
            is_admin = True
        elif hasattr(user, 'profile') and hasattr(user.profile, 'role') and user.profile.role == 'admin_role':
            is_admin = True
        
        if not is_admin:
            # 스터디 생성자 또는 스터디 관리자인지 확인
            is_creator = study.created_by == user
            is_study_admin = study.members.filter(
                user=user, 
                is_active=True,
                role__in=['study_admin', 'study_leader']
            ).exists()
            
            if not (is_creator or is_study_admin):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionError('이 스터디에 Task를 생성할 권한이 없습니다.')
        
        print(f"Task 저장 시작")
        task = serializer.save()
        
        # 다국어 콘텐츠 자동 처리
        from quiz.utils.multilingual_utils import MultilingualContentManager
        manager = MultilingualContentManager(task, self.request.user, ['name'])
        manager.handle_multilingual_update()
        
        print(f"Task 저장 완료")

    def get_queryset(self):
        study_id = self.request.query_params.get('study_id')
        queryset = StudyTask.objects.select_related('study', 'exam', 'exam__created_by').prefetch_related(
            'study__members__user',
            'study__members__user__profile'
        )
        if study_id:
            return queryset.filter(study_id=study_id)
        return queryset.all()

    def list(self, request, *args, **kwargs):
        import time
        from django.db import connection
        
        start_time = time.time()
        queries_before = len(connection.queries)
        logger.info(f"[STUDY_TASKS_LIST] API 호출 시작 - 사용자: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
        logger.info(f"[STUDY_TASKS_LIST] 요청 파라미터: {dict(request.query_params)}")
        
        # 사용자별 진행률 데이터를 미리 로드 (N+1 쿼리 방지)
        user_progress_dict = {}
        if request.user.is_authenticated:
            progress_query_start = time.time()
            study_id = request.query_params.get('study_id')
            if study_id:
                progress_records = StudyTaskProgress.objects.filter(
                    user=request.user,
                    study_task__study_id=study_id
                ).select_related('study_task')
            else:
                progress_records = StudyTaskProgress.objects.filter(
                    user=request.user
                ).select_related('study_task')
            
            for progress in progress_records:
                user_progress_dict[progress.study_task_id] = progress.progress
            progress_query_time = time.time() - progress_query_start
            logger.info(f"[STUDY_TASKS_LIST] 사용자 진행률 조회 완료 - {len(user_progress_dict)}개, {progress_query_time*1000:.2f}ms")
        else:
            progress_query_time = 0
        
        # serializer context에 사용자 진행률 데이터 전달
        original_get_serializer_context = self.get_serializer_context
        def get_serializer_context_with_data():
            context = original_get_serializer_context()
            context['user_progress_dict'] = user_progress_dict
            return context
        self.get_serializer_context = get_serializer_context_with_data
        
        serializer_start = time.time()
        try:
            response = super().list(request, *args, **kwargs)
        finally:
            self.get_serializer_context = original_get_serializer_context
        
        serializer_time = time.time() - serializer_start
        queries_after_serializer = len(connection.queries)
        
        if hasattr(response, 'data') and response.data and 'results' in response.data:
            # 사용자 언어 설정 확인 (한 번만)
            from quiz.utils.multilingual_utils import BASE_LANGUAGE
            user_language = BASE_LANGUAGE  # 기본값
            if request.user.is_authenticated and hasattr(request.user, 'userprofile'):
                user_language = request.user.userprofile.language
            
            multilingual_start = time.time()
            # 각 Task에 대해 다국어 콘텐츠 처리 (모든 언어 동일하게 처리)
            for task_data in response.data['results']:
                # 사용자 언어를 우선 사용, 없으면 기본 언어('en') 사용
                name = task_data.get(f'name_{user_language}')
                
                # 사용자 언어에 해당하는 콘텐츠가 없으면 기본 언어로 폴백
                if not name:
                    name = task_data.get(f'name_{BASE_LANGUAGE}')
                    # 기본 언어도 없으면 다른 언어 중 하나라도 사용
                    if not name:
                        for lang in SUPPORTED_LANGUAGES:
                            if task_data.get(f'name_{lang}'):
                                name = task_data.get(f'name_{lang}')
                                break
                
                task_data['name'] = name or task_data.get('name', '')
            multilingual_time = time.time() - multilingual_start
            
            # 로깅
            tasks_count = len(response.data['results'])
            total_time = time.time() - start_time
            total_queries = queries_after_serializer - queries_before
            logger.info(f"[STUDY_TASKS_LIST] 응답 완료 - {tasks_count}개 tasks, 진행률 조회={progress_query_time*1000:.2f}ms, 시리얼라이저={serializer_time*1000:.2f}ms, 다국어 처리={multilingual_time*1000:.2f}ms, 총 시간={total_time*1000:.2f}ms, 총 쿼리: {total_queries}개")
        else:
            total_time = time.time() - start_time
            total_queries = queries_after_serializer - queries_before
            logger.info(f"[STUDY_TASKS_LIST] 응답 완료 - 빈 결과, 총 시간={total_time*1000:.2f}ms, 총 쿼리: {total_queries}개")
        
        return response

    def destroy(self, request, *args, **kwargs):
        print(f"Task delete request - pk: {kwargs.get('pk')}")
        try:
            task = self.get_object()
            user_lang = get_user_language(request)
            task_name = get_localized_field(task, 'name', user_lang, '이름 없음')
            print(f"Task found: {task.id} - {task_name}")
            
            # 권한 확인
            user = request.user
            study = task.study
            
            # admin_role 사용자는 모든 Task 삭제 가능
            is_admin = False
            if hasattr(user, 'is_superuser') and user.is_superuser:
                is_admin = True
            elif hasattr(user, 'profile') and hasattr(user.profile, 'role') and user.profile.role == 'admin_role':
                is_admin = True
            
            if not is_admin:
                # 스터디 생성자 또는 스터디 관리자인지 확인
                is_creator = study.created_by == user
                is_study_admin = study.members.filter(
                    user=user, 
                    is_active=True,
                    role__in=['study_admin', 'study_leader']
                ).exists()
                
                if not (is_creator or is_study_admin):
                    from rest_framework.exceptions import PermissionDenied
                    raise PermissionDenied('이 Task를 삭제할 권한이 없습니다.')
            
            response = super().destroy(request, *args, **kwargs)
            print(f"Task delete successful")
            return response
        except StudyTask.DoesNotExist:
            print(f"Task not found with pk: {kwargs.get('pk')}")
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Task delete error: {str(e)}")
            return Response({'error': f'Delete failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        print(f"Task update request data: {request.data}")
        print(f"exam 필드 값: {request.data.get('exam')}")
        print(f"exam 필드 타입: {type(request.data.get('exam'))}")
        
        try:
            # 권한 확인
            instance = self.get_object()
            user = request.user
            study = instance.study
            
            # admin_role 사용자는 모든 Task 수정 가능
            is_admin = False
            if hasattr(user, 'is_superuser') and user.is_superuser:
                is_admin = True
            elif hasattr(user, 'profile') and hasattr(user.profile, 'role') and user.profile.role == 'admin_role':
                is_admin = True
            
            if not is_admin:
                # 스터디 생성자 또는 스터디 관리자인지 확인
                is_creator = study.created_by == user
                is_study_admin = study.members.filter(
                    user=user, 
                    is_active=True,
                    role__in=['study_admin', 'study_leader']
                ).exists()
                
                if not (is_creator or is_study_admin):
                    from rest_framework.exceptions import PermissionDenied
                    raise PermissionDenied('이 Task를 수정할 권한이 없습니다.')
            
            # 업데이트용 serializer 사용
            serializer = StudyTaskUpdateSerializer(instance, data=request.data, partial=True)
            if serializer.is_valid():
                task = serializer.save()
                
                # 다국어 콘텐츠 자동 처리
                from quiz.utils.multilingual_utils import MultilingualContentManager
                manager = MultilingualContentManager(task, request.user, ['name'])
                manager.handle_multilingual_update()
                
                print(f"Task update successful")
                user_lang = get_user_language(request)
                exam_title = get_localized_field(task.exam, 'title', user_lang, 'Unknown') if task.exam else None
                print(f"업데이트된 Task - exam: {exam_title}")
                return Response(serializer.data)
            else:
                print(f"Task update validation error: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Task update error: {str(e)}")
            print(f"Request data: {request.data}")
            raise

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        
        if hasattr(response, 'data') and response.data:
            # 사용자 언어 설정 확인 (한 번만)
            from quiz.utils.multilingual_utils import BASE_LANGUAGE
            user_language = BASE_LANGUAGE  # 기본값
            if request.user.is_authenticated and hasattr(request.user, 'userprofile'):
                user_language = request.user.userprofile.language
            
            # 다국어 콘텐츠 메타데이터 추가
            task_data = response.data
            task_data['current_user_language'] = user_language
            task_data['available_languages'] = []
            
            # 사용 가능한 언어 목록 생성 (모든 지원 언어 확인)
            from quiz.utils.multilingual_utils import BASE_LANGUAGE
            for lang in SUPPORTED_LANGUAGES:
                if task_data.get(f'name_{lang}'):
                    task_data['available_languages'].append(lang)
            
            # 현재 사용자 언어에 맞는 이름만 설정 (모든 언어 동일하게 처리)
            # 사용자 언어를 우선 사용, 없으면 기본 언어('en') 사용
            name = task_data.get(f'name_{user_language}')
            
            # 사용자 언어에 해당하는 콘텐츠가 없으면 기본 언어로 폴백
            if not name:
                name = task_data.get(f'name_{BASE_LANGUAGE}')
                # 기본 언어도 없으면 다른 언어 중 하나라도 사용
                if not name:
                    for lang in SUPPORTED_LANGUAGES:
                        if task_data.get(f'name_{lang}'):
                            name = task_data.get(f'name_{lang}')
                            break
            
            task_data['name'] = name or task_data.get('name', '')
            
            # 로깅 (요약 정보만)
            task_name = task_data.get('name', 'Unknown')
            study_id = task_data.get('study', 'Unknown')
            exam_id = task_data.get('exam', 'None')
            progress = task_data.get('progress', 0)
            logger.info(f"Task retrieve response: name='{task_name}', study={study_id}, exam={exam_id}, progress={progress}, language={user_language}")
        else:
            logger.info("Task retrieve response: empty")
        
        return response

    @action(detail=True, methods=['post'])
    def update_progress_from_exam(self, request, pk=None):
        task = self.get_object()
        exam_result_id = request.data.get('exam_result_id')
        
        try:
            exam_result = ExamResult.objects.get(id=exam_result_id)
            if exam_result.exam == task.exam:
                task.progress = exam_result.score
                task.save()
                return Response({'message': 'Progress updated from exam result'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Exam result does not match task exam'}, status=status.HTTP_400_BAD_REQUEST)
        except ExamResult.DoesNotExist:
            return Response({'error': 'Exam result not found'}, status=status.HTTP_404_NOT_FOUND)


class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer

    def _invalidate_study_cache(self):
        """스터디 관련 캐시를 무효화하는 헬퍼 메서드"""
        try:
            from django.core.cache import cache
            cache.clear()
            print("🔄 MemberViewSet 스터디 캐시 무효화 완료")
        except Exception as e:
            print(f"MemberViewSet 캐시 무효화 중 오류: {e}")

    def get_queryset(self):
        study_id = self.request.query_params.get('study_id')
        queryset = Member.objects.select_related('study', 'user')
        if study_id:
            return queryset.filter(study_id=study_id)
        return queryset.all()

    def create(self, request, *args, **kwargs):
        print(f"Member create request data: {request.data}")
        try:
            # 멤버 데이터 가져오기
            member_data = request.data.copy()
            
            # 사용자 연결 시도: 멤버 이름과 일치하는 사용자가 있는지 확인
            if not member_data.get('user') and member_data.get('name'):
                try:
                    user = User.objects.get(username=member_data['name'])
                    member_data['user'] = user.id
                    print(f"사용자 자동 연결: {member_data['name']} -> {user.id}")
                except User.DoesNotExist:
                    print(f"사용자를 찾을 수 없음: {member_data['name']}")
            
            # 시리얼라이저로 데이터 검증
            serializer = self.get_serializer(data=member_data)
            serializer.is_valid(raise_exception=True)
            
            # 멤버 생성
            member = serializer.save()
            
            # 캐시 무효화 (StudyCacheManager 사용)
            try:
                # 멤버가 추가된 스터디 관련 캐시 무효화
                StudyCacheManager.invalidate_study_cache(member.study.id)
                StudyCacheManager.invalidate_all_study_cache()
                logger.info(f"[MEMBER_CREATE] StudyCacheManager를 통한 캐시 무효화 완료: study_id={member.study.id}")
            except Exception as e:
                logger.error(f"[MEMBER_CREATE] StudyCacheManager 캐시 무효화 실패: {e}")
                # 폴백: 기존 방식으로 캐시 무효화
                self._invalidate_study_cache()
            
            response_serializer = self.get_serializer(member)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"Member create error: {str(e)}")
            print(f"Request data: {request.data}")
            raise 

    def destroy(self, request, *args, **kwargs):
        """멤버 삭제"""
        try:
            member = self.get_object()
            member.delete()
            
            # 캐시 무효화 (StudyCacheManager 사용)
            try:
                # 멤버가 삭제된 스터디 관련 캐시 무효화
                StudyCacheManager.invalidate_study_cache(member.study.id)
                StudyCacheManager.invalidate_all_study_cache()
                logger.info(f"[MEMBER_DELETE] StudyCacheManager를 통한 캐시 무효화 완료: study_id={member.study.id}")
            except Exception as e:
                logger.error(f"[MEMBER_DELETE] StudyCacheManager 캐시 무효화 실패: {e}")
                # 폴백: 기존 방식으로 캐시 무효화
                self._invalidate_study_cache()
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            print(f"Member destroy error: {str(e)}")
            raise

@api_view(['GET'])
def download_study_excel(request, study_id):
    """스터디의 Task 정보를 엑셀로 다운로드합니다."""
    try:
        study = Study.objects.get(id=study_id)
        
        # 사용자 언어 확인 (모든 언어 동일하게 처리)
        from quiz.utils.multilingual_utils import BASE_LANGUAGE
        user_language = BASE_LANGUAGE  # 기본값
        if request.user.is_authenticated:
            if hasattr(request.user, 'userprofile') and hasattr(request.user.userprofile, 'language'):
                user_language = request.user.userprofile.language
            elif hasattr(request.user, 'profile') and hasattr(request.user.profile, 'language'):
                user_language = request.user.profile.language
        
        # 다국어 제목/목표 가져오기 헬퍼 함수
        def get_localized_text(obj, field_prefix, user_lang):
            """사용자 언어를 우선 사용, 없으면 기본 언어('en') 사용"""
            text = getattr(obj, f'{field_prefix}_{user_lang}', None)
            if not text:
                text = getattr(obj, f'{field_prefix}_{BASE_LANGUAGE}', None)
                # 기본 언어도 없으면 다른 언어 중 하나라도 사용
                if not text:
                    for lang in SUPPORTED_LANGUAGES:
                        if hasattr(obj, f'{field_prefix}_{lang}'):
                            text = getattr(obj, f'{field_prefix}_{lang}', None)
                            if text:
                                break
            return text or 'Unknown'
        
        # 스터디 정보와 Task 정보 수집
        data = []
        for task in study.tasks.all():
            # StudyTask는 모든 언어 지원
            task_name = get_localized_field(task, 'name', user_language, '이름 없음')
            exam_title = 'Unknown'
            if task.exam:
                exam_title = get_localized_text(task.exam, 'title', user_language)
            
            data.append({
                'Task 이름': task_name,
                '연결된 시험': exam_title,
                '진도율 (%)': task.progress,
                '시험 ID': task.exam.id if task.exam else '',
                'Task ID': task.id
            })
        
        # DataFrame 생성
        df = pd.DataFrame(data)
        
        # Excel 파일 생성
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Task 목록 시트
            df.to_excel(writer, sheet_name='Task목록', index=False)
            
            # 스터디 정보 시트
            study_title = get_localized_text(study, 'title', user_language)
            study_goal = get_localized_text(study, 'goal', user_language)
            
            study_info = pd.DataFrame([{
                '스터디 제목': study_title,
                '스터디 목표': study_goal,
                '시작일': study.start_date,
                '종료일': study.end_date,
                '전체 진행률': "0%"  # Study 모델에 overall_progress 속성이 없으므로 기본값 사용
            }])
            study_info.to_excel(writer, sheet_name='스터디정보', index=False)
        
        output.seek(0)
        
        # 파일명 설정
        filename = f"{study_title}_tasks.xlsx"
        
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Study.DoesNotExist:
        return Response({'error': '스터디를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"스터디 엑셀 다운로드 중 오류: {str(e)}")
        return Response({'error': f'엑셀 다운로드 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def upload_study_excel(request):
    """Excel 파일로 스터디 Task 정보를 업로드합니다."""
    try:
        if 'file' not in request.FILES:
            return Response({'detail': '파일이 업로드되지 않았습니다.'}, status=400)
        
        file = request.FILES['file']
        study_id = request.data.get('study_id')
        
        if not study_id:
            return Response({'detail': '스터디 ID가 필요합니다.'}, status=400)
        
        try:
            study = Study.objects.get(id=study_id)
        except Study.DoesNotExist:
            return Response({'detail': '스터디를 찾을 수 없습니다.'}, status=400)
        
        # 파일 확장자 확인
        if not file.name.endswith(('.xlsx', '.xls')):
            return Response({'detail': 'Excel 파일(.xlsx, .xls)만 업로드 가능합니다.'}, status=400)
        
        # Excel 파일 읽기
        try:
            excel_file = pd.ExcelFile(file)
        except Exception as e:
            return Response({'detail': f'Excel 파일 읽기 실패: {str(e)}'}, status=400)
        
        stats = {
            'total_tasks': 0,
            'created': 0,
            'skipped': 0,
            'errors': 0,
            'error_details': []
        }
        
        # Task 목록 시트 처리
        if 'Task목록' in excel_file.sheet_names:
            try:
                task_list_df = pd.read_excel(file, sheet_name='Task목록')
                print(f"Task목록 시트 읽기 완료: {len(task_list_df)} 행")
                
                for index, row in task_list_df.iterrows():
                    stats['total_tasks'] += 1
                    
                    try:
                        task_name = str(row.get('Task 이름', '')).strip()
                        if not task_name or task_name == 'nan':
                            stats['skipped'] += 1
                            continue
                        
                        # 기존 Task 확인 (이름과 스터디로)
                        existing_task = StudyTask.objects.filter(name=task_name, study=study).first()
                        if existing_task:
                            stats['skipped'] += 1
                            continue
                        
                        # 시험 찾기
                        exam_id = row.get('시험 ID')
                        exam = None
                        if exam_id and pd.notna(exam_id):
                            try:
                                exam = Exam.objects.get(id=int(exam_id))
                            except (Exam.DoesNotExist, ValueError):
                                pass
                        
                        # 새 Task 생성
                        task_data = {
                            'name': task_name,
                            'exam': exam,
                            'progress': float(row.get('진도율 (%)', 0)),
                            'study': study
                        }
                        
                        task = StudyTask.objects.create(**task_data)
                        stats['created'] += 1
                        
                    except Exception as e:
                        stats['errors'] += 1
                        stats['error_details'].append(f"Task '{task_name if 'task_name' in locals() else 'Unknown'}' 생성 실패: {str(e)}")
                        print(f"Task 생성 오류: {str(e)}")
                
            except Exception as e:
                return Response({'detail': f'Task목록 시트 처리 실패: {str(e)}'}, status=400)
        
        return Response({
            'message': '스터디 Task 업로드 완료',
            'stats': stats
        })
        
    except Exception as e:
        print(f"스터디 Task 업로드 중 오류: {str(e)}")
        return Response({'detail': f'스터디 Task 업로드 중 오류가 발생했습니다: {str(e)}'}, status=500)


# 스터디 가입 요청 관련 뷰들
@api_view(['POST'])
def create_join_request(request):
    """스터디 가입 요청을 생성합니다."""
    try:
        serializer = CreateStudyJoinRequestSerializer(data=request.data)
        if serializer.is_valid():
            study_id = serializer.validated_data['study_id']
            message = serializer.validated_data.get('message', '')
            
            # 스터디 확인
            try:
                study = Study.objects.get(id=study_id)
            except Study.DoesNotExist:
                return Response({'error': '스터디를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
            
            # 이미 멤버인지 확인
            if Member.objects.filter(study=study, user=request.user).exists():
                return Response({'error': '이미 해당 스터디의 멤버입니다.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 이미 가입 요청이 있는지 확인 (unique_together 제약 때문에)
            existing_request = StudyJoinRequest.objects.filter(study=study, user=request.user).first()
            if existing_request:
                if existing_request.status == 'pending':
                    return Response({'error': '이미 가입 요청을 보냈습니다.'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    # 기존 요청이 approved/rejected 상태면 pending으로 변경하고 메시지 업데이트
                    existing_request.status = 'pending'
                    existing_request.message = message
                    existing_request.requested_at = timezone.now()
                    existing_request.responded_at = None
                    existing_request.responded_by = None
                    existing_request.save()
                    join_request = existing_request
            else:
                # 가입 요청 생성
                join_request = StudyJoinRequest.objects.create(
                    study=study,
                    user=request.user,
                    message=message
                )
            
            return Response({
                'message': '가입 요청이 성공적으로 전송되었습니다.',
                'join_request_id': join_request.id
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': f'가입 요청 생성 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_study_join_requests(request, study_id):
    """스터디의 가입 요청 목록을 조회합니다."""
    try:
        # 스터디 확인
        try:
            study = Study.objects.get(id=study_id)
        except Study.DoesNotExist:
            return Response({'error': '스터디를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        # 인증 확인
        if not request.user.is_authenticated:
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # 권한 확인 (스터디 관리자, 리더, 또는 관리자만 조회 가능)
        is_admin = hasattr(request.user, 'profile') and request.user.profile.role in ['admin_role', 'study_admin_role']
        is_study_admin = Member.objects.filter(
            study=study, 
            user=request.user, 
            role__in=['study_admin', 'study_leader']
        ).exists()
        
        # admin 사용자는 항상 접근 가능
        if request.user.username == 'admin':
            is_admin = True
        
        if not (is_admin or is_study_admin):
            return Response({'error': '가입 요청을 조회할 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
        
        # 가입 요청 목록 조회
        join_requests = StudyJoinRequest.objects.filter(study=study).order_by('-requested_at')
        serializer = StudyJoinRequestSerializer(join_requests, many=True)
        
        return Response(serializer.data)
    except Exception as e:
        return Response({'error': f'가입 요청 목록 조회 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def respond_to_join_request(request, request_id):
    """가입 요청에 응답합니다 (승인/거절)."""
    try:
        serializer = UpdateStudyJoinRequestSerializer(data=request.data)
        if serializer.is_valid():
            request_status = serializer.validated_data['status']
            message = serializer.validated_data.get('message', '')
            
            # 가입 요청 확인
            try:
                join_request = StudyJoinRequest.objects.get(id=request_id)
            except StudyJoinRequest.DoesNotExist:
                return Response({'error': '가입 요청을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
            
            # 권한 확인 (admin 또는 스터디 관리자만 응답 가능)
            is_admin = hasattr(request.user, 'profile') and hasattr(request.user.profile, 'role') and request.user.profile.role == 'admin_role'
            is_study_admin = Member.objects.filter(study=join_request.study, user=request.user, role__in=['study_admin', 'study_leader']).exists()
            
            if not is_admin and not is_study_admin:
                return Response({'error': '가입 요청에 응답할 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
            
            # 이미 처리된 요청인지 확인
            if join_request.status != 'pending':
                return Response({'error': '이미 처리된 가입 요청입니다.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 요청 상태 업데이트
            join_request.status = request_status
            join_request.responded_at = timezone.now()
            join_request.responded_by = request.user
            join_request.save()
            
            # 승인된 경우 멤버로 추가
            if request_status == 'approved':
                # 이미 멤버인지 다시 확인
                if not Member.objects.filter(study=join_request.study, user=join_request.user).exists():
                    Member.objects.create(
                        study=join_request.study,
                        user=join_request.user,
                        name=join_request.user.username,
                        email=join_request.user.email,
                        role='member'
                    )
                    
                    # 캐시 무효화 (멤버가 추가되었으므로)
                    from django.core.cache import cache
                    cache.clear()
                    print("🔄 가입 승인 후 캐시 무효화 완료")
            
            return Response({
                'message': f'가입 요청이 {request_status}되었습니다.',
                'status': request_status
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': f'가입 요청 응답 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
def cancel_join_request(request, request_id):
    """가입 요청을 취소합니다."""
    try:
        # 가입 요청 확인
        try:
            join_request = StudyJoinRequest.objects.get(id=request_id)
        except StudyJoinRequest.DoesNotExist:
            return Response({'error': '가입 요청을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        # 권한 확인 (요청자 본인만 취소 가능)
        if join_request.user != request.user:
            return Response({'error': '가입 요청을 취소할 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
        
        # 이미 처리된 요청인지 확인
        if join_request.status != 'pending':
            return Response({'error': '이미 처리된 가입 요청은 취소할 수 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 가입 요청 삭제
        join_request.delete()
        
        return Response({
            'message': '가입 요청이 취소되었습니다.'
        })
    except Exception as e:
        return Response({'error': f'가입 요청 취소 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_user_join_requests(request):
    """현재 사용자의 가입 요청 목록을 조회합니다."""
    try:
        # 현재 사용자의 가입 요청 목록 조회
        join_requests = StudyJoinRequest.objects.filter(user=request.user).order_by('-requested_at')
        serializer = StudyJoinRequestSerializer(join_requests, many=True)
        
        return Response(serializer.data)
    except Exception as e:
        return Response({'error': f'가입 요청 목록 조회 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 


@api_view(['DELETE'])
def delete_user_study_join_request(request, study_id):
    """사용자의 특정 스터디 가입 요청을 삭제합니다."""
    try:
        # 스터디 확인
        try:
            study = Study.objects.get(id=study_id)
        except Study.DoesNotExist:
            return Response({'error': '스터디를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        # 가입 요청 확인 및 삭제
        try:
            join_request = StudyJoinRequest.objects.get(study=study, user=request.user)
            join_request.delete()
            return Response({'success': True}, status=status.HTTP_200_OK)
        except StudyJoinRequest.DoesNotExist:
            return Response({'error': '가입 요청이 존재하지 않습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        return Response({'error': f'가입 요청 삭제 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def translate_text(request):
    """OpenAI API를 사용하여 텍스트를 기본 언어(영어)로 번역합니다."""
    try:
        # 요청 데이터 확인
        text = request.data.get('text')
        if not text:
            return Response({'error': '번역할 텍스트가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # OpenAI API 키 확인
        openai_api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not openai_api_key:
            return Response({'error': 'OpenAI API 키가 설정되지 않았습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # OpenAI API 호출
        headers = {
            'Authorization': f'Bearer {openai_api_key}',
            'Content-Type': 'application/json'
        }
        
        # 사용자 언어 확인 (요청에서 전달되거나 프로필에서 가져오기)
        from quiz.utils.multilingual_utils import BASE_LANGUAGE
        from_language = request.data.get('from_language')
        to_language = request.data.get('to_language', BASE_LANGUAGE)  # 기본값은 'en' (BASE_LANGUAGE)
        
        # 사용자 프로필 언어가 있으면 그것을 사용
        if not from_language and request.user.is_authenticated:
            if hasattr(request.user, 'userprofile') and hasattr(request.user.userprofile, 'language'):
                from_language = request.user.userprofile.language
            elif hasattr(request.user, 'profile') and hasattr(request.user.profile, 'language'):
                from_language = request.user.profile.language
        
        # 여전히 없으면 기본 언어 사용
        if not from_language:
            from_language = BASE_LANGUAGE
        
        payload = {
            'model': 'gpt-3.5-turbo',
            'messages': [
                {
                    'role': 'system',
                    'content': f'You are a helpful assistant that translates text from {from_language} to {to_language}. Provide only the translated text without any additional explanation or formatting.'
                },
                {
                    'role': 'user',
                    'content': f'Translate the following text from {from_language} to {to_language}: {text}'
                }
            ],
            'max_tokens': 100,
            'temperature': 0.3
        }
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            translated_text = result['choices'][0]['message']['content'].strip()
            
            return Response({
                'original_text': text,
                'translated_text': translated_text
            })
        else:
            logger.error(f'OpenAI API 오류: {response.status_code} - {response.text}')
            return Response({'error': '번역 중 오류가 발생했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except requests.exceptions.Timeout:
        return Response({'error': '번역 요청 시간이 초과되었습니다.'}, status=status.HTTP_408_REQUEST_TIMEOUT)
    except requests.exceptions.RequestException as e:
        logger.error(f'OpenAI API 요청 오류: {str(e)}')
        return Response({'error': '번역 서비스에 연결할 수 없습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f'번역 중 예상치 못한 오류: {str(e)}')
        return Response({'error': f'번역 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def update_user_language(request):
    """사용자의 언어 설정을 업데이트합니다."""
    try:
        # 요청 데이터 확인
        from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
        language = request.data.get('language')
        if not language or language not in SUPPORTED_LANGUAGES:
            return Response({'error': f'유효한 언어 설정이 필요합니다 ({", ".join(SUPPORTED_LANGUAGES)}).'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 현재 사용자 확인
        user = request.user
        if not user.is_authenticated:
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # UserProfile 생성 또는 업데이트
        from .models import UserProfile
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'role': 'user_role',
                'language': language
            }
        )
        
        if not created:
            # 기존 프로필이 있으면 언어 설정만 업데이트
            profile.language = language
            profile.save(update_fields=['language'])
            logger.info(f"✅ 사용자 언어 설정 업데이트: {user.username} -> {language}")
        else:
            logger.info(f"✅ 사용자 프로필 생성 및 언어 설정: {user.username} -> {language}")
        
        # 캐시 무효화 (사용자 관련 캐시)
        from django.core.cache import cache
        cache.delete(f"user_profile_{user.id}")
        cache.delete(f"user_language_{user.id}")
        
        return Response({
            'message': '언어 설정이 업데이트되었습니다.',
            'language': language,
            'username': user.username
        })
        
    except Exception as e:
        logger.error(f'사용자 언어 설정 업데이트 실패: {str(e)}')
        return Response({'error': f'언어 설정 업데이트 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _translate_content(text, from_language, to_language):
    """
    텍스트를 지정된 언어로 번역하는 함수 (Gemini 폴백 지원)
    
    Args:
        text: 번역할 텍스트
        from_language: 원본 언어 ('ko', 'en', 'es', 'zh', 'ja')
        to_language: 대상 언어 ('ko', 'en', 'es', 'zh', 'ja')
    
    Returns:
        str: 번역된 텍스트 또는 None (번역 실패 시)
    """
    if not text or not text.strip():
        return None
    
    # batch_translate_texts를 사용하여 Gemini 폴백 지원
    from quiz.utils.multilingual_utils import batch_translate_texts
    
    try:
        translated_results = batch_translate_texts([text], from_language, to_language)
        if translated_results and len(translated_results) > 0 and translated_results[0]:
            translated_text = translated_results[0]
            logger.info(f"[TRANSLATE] 번역 성공: '{text}' → '{translated_text}' ({from_language} → {to_language})")
            return translated_text
        else:
            logger.warning(f"[TRANSLATE] 번역 실패: {from_language} → {to_language}")
            return None
    except Exception as e:
        logger.warning(f"[TRANSLATE] 번역 중 예상치 못한 오류: {str(e)} - {from_language} → {to_language}")
        return None
