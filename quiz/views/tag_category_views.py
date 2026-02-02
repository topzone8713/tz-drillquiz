import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db import models
from django.urls import path
from django.core.cache import cache
from ..models import TagCategory, Tag
from ..serializers import TagCategorySerializer, TagSerializer

logger = logging.getLogger(__name__)
User = get_user_model()

# 카테고리 캐시 설정
CATEGORY_DESCENDANTS_CACHE_TIMEOUT = 3600  # 1시간
CATEGORY_TAGS_CACHE_TIMEOUT = 1800  # 30분


class TagCategoryViewSet(viewsets.ModelViewSet):
    """
    태그 카테고리 관리 ViewSet
    GET 요청은 로그인하지 않은 사용자도 접근 가능 (AllowAny)
    POST, PUT, DELETE 등은 인증 필요 (기본 권한 설정)
    """
    queryset = TagCategory.objects.all()
    serializer_class = TagCategorySerializer
    
    def get_permissions(self):
        """액션별 권한 설정"""
        if self.action in ['list', 'retrieve', 'tree', 'children', 'tags', 'search']:
            # GET 요청은 모두 접근 가능
            return [AllowAny()]
        else:
            # POST, PUT, DELETE 등은 인증 필요
            return [IsAuthenticated()]
    
    def get_queryset(self):
        """카테고리 목록을 레벨과 순서로 정렬하여 반환"""
        queryset = TagCategory.objects.all()
        
        # 레벨 필터링
        level = self.request.query_params.get('level')
        if level:
            try:
                queryset = queryset.filter(level=int(level))
            except ValueError:
                pass
        
        # 부모 카테고리 필터링
        parent_id = self.request.query_params.get('parent')
        if parent_id:
            try:
                queryset = queryset.filter(parent_id=int(parent_id))
            except ValueError:
                pass
        
        return queryset.order_by('level', 'order', 'name_ko')
    
    def perform_create(self, serializer):
        """카테고리 생성 시 현재 사용자를 생성자로 설정, 다국어 번역 처리 및 캐시 무효화"""
        try:
            if self.request.user and not self.request.user.is_anonymous:
                instance = serializer.save(created_by=self.request.user)
            else:
                instance = serializer.save(created_by=None)
            
            # 다국어 콘텐츠 자동 처리 (영어 → 다른 언어 번역)
            self._handle_category_translation(instance)
            
            # 카테고리 생성 시 관련 캐시 무효화
            self._invalidate_category_cache(instance)
        except ValueError as e:
            raise ValidationError({'detail': str(e)})
    
    def perform_update(self, serializer):
        """카테고리 수정 시 깊이 검증 에러 처리, 다국어 번역 처리 및 캐시 무효화"""
        try:
            instance = serializer.save()
            
            # 다국어 콘텐츠 자동 처리 (영어 → 다른 언어 번역)
            self._handle_category_translation(instance)
            
            # 카테고리 수정 시 관련 캐시 무효화
            self._invalidate_category_cache(instance)
        except ValueError as e:
            raise ValidationError({'detail': str(e)})
    
    def perform_destroy(self, instance):
        """카테고리 삭제 시 캐시 무효화"""
        # 삭제 전에 캐시 무효화
        self._invalidate_category_cache(instance)
        instance.delete()
    
    def _handle_category_translation(self, category):
        """
        카테고리 다국어 번역 처리 (영어 → 다른 언어)
        카테고리 관리자는 영어 사용자이므로 영어로 입력한 내용을 ko, es, zh로 번역
        """
        try:
            from quiz.utils.multilingual_utils import (
                batch_translate_texts, 
                is_auto_translation_enabled,
                LANGUAGE_KO,
                LANGUAGE_EN,
                LANGUAGE_ES,
                LANGUAGE_ZH,
                LANGUAGE_JA,
                BASE_LANGUAGE
            )
            
            # 자동 번역이 비활성화된 경우 번역하지 않음
            if not is_auto_translation_enabled(self.request.user):
                logger.info(f"[TAG_CATEGORY_TRANSLATE] 자동 번역이 비활성화되어 번역을 건너뜁니다.")
                return
            
            # 영어 이름이 없으면 번역할 수 없음
            if not category.name_en or not category.name_en.strip():
                logger.info(f"[TAG_CATEGORY_TRANSLATE] 영어 이름이 없어 번역을 건너뜁니다.")
                return
            
            # 번역 대상 언어 목록 (ko, es, zh, ja)
            target_languages = [LANGUAGE_KO, LANGUAGE_ES, LANGUAGE_ZH, LANGUAGE_JA]
            english_name = category.name_en.strip()
            
            # 각 언어별로 번역 수행
            update_fields = []
            for target_lang in target_languages:
                target_field = f"name_{target_lang}"
                current_value = getattr(category, target_field, None)
                
                # 이미 값이 있으면 번역하지 않음 (기존 번역 유지)
                if current_value and current_value.strip():
                    logger.info(f"[TAG_CATEGORY_TRANSLATE] {target_lang} 이름이 이미 있어 번역을 건너뜁니다: {current_value}")
                    continue
                
                # 영어 → 대상 언어 번역
                try:
                    translated_names = batch_translate_texts([english_name], LANGUAGE_EN, target_lang)
                    if translated_names and translated_names[0]:
                        translated_name = translated_names[0].strip()
                        setattr(category, target_field, translated_name)
                        update_fields.append(target_field)
                        logger.info(f"[TAG_CATEGORY_TRANSLATE] 번역 완료: {LANGUAGE_EN} '{english_name}' → {target_lang} '{translated_name}'")
                    else:
                        logger.warning(f"[TAG_CATEGORY_TRANSLATE] 번역 실패: {LANGUAGE_EN} → {target_lang}")
                except Exception as e:
                    logger.error(f"[TAG_CATEGORY_TRANSLATE] 번역 중 오류 발생 ({LANGUAGE_EN} → {target_lang}): {str(e)}")
            
            # 번역된 필드가 있으면 저장
            if update_fields:
                # 완성도 필드도 함께 업데이트
                if 'name_ko' in update_fields:
                    category.is_ko_complete = bool(category.name_ko)
                    update_fields.append('is_ko_complete')
                if 'name_es' in update_fields:
                    category.is_es_complete = bool(category.name_es)
                    update_fields.append('is_es_complete')
                if 'name_zh' in update_fields:
                    category.is_zh_complete = bool(category.name_zh)
                    update_fields.append('is_zh_complete')
                if 'name_ja' in update_fields:
                    category.is_ja_complete = bool(category.name_ja)
                    update_fields.append('is_ja_complete')
                
                category.save(update_fields=update_fields)
                logger.info(f"[TAG_CATEGORY_TRANSLATE] 카테고리 번역 저장 완료: category_id={category.id}, 업데이트된 필드={update_fields}")
        except Exception as e:
            logger.error(f"[TAG_CATEGORY_TRANSLATE] 카테고리 번역 처리 중 오류: category_id={category.id}, error={str(e)}")
            # 번역 실패해도 카테고리 생성/수정은 계속 진행
    
    def _invalidate_category_cache(self, category):
        """카테고리 관련 캐시 무효화 (현재 카테고리 및 모든 상위 카테고리)"""
        try:
            # 현재 카테고리의 캐시 무효화
            cache_key_descendants = f"tag_category_{category.id}_descendants"
            cache_key_tags = f"tag_category_{category.id}_tags"
            cache.delete(cache_key_descendants)
            cache.delete(cache_key_tags)
            
            # 모든 상위 카테고리의 캐시도 무효화 (하위 카테고리가 변경되었으므로)
            parent = category.parent
            while parent:
                parent_cache_key_descendants = f"tag_category_{parent.id}_descendants"
                parent_cache_key_tags = f"tag_category_{parent.id}_tags"
                cache.delete(parent_cache_key_descendants)
                cache.delete(parent_cache_key_tags)
                parent = parent.parent
            
            logger.info(f"[TAG_CATEGORY] 카테고리 캐시 무효화 완료: category_id={category.id}")
        except Exception as e:
            logger.error(f"[TAG_CATEGORY] 카테고리 캐시 무효화 실패: category_id={category.id}, error={str(e)}")
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """계층 구조 트리 형태로 카테고리 반환"""
        try:
            # DevOps 도메인 필터링: devops 도메인인 경우 "IT 기술 > IT 기술" 카테고리만 반환
            from quiz.utils.domain_utils import is_devops_domain, get_devops_category_id
            if is_devops_domain(request):
                category_id = get_devops_category_id()
                if category_id:
                    # 해당 카테고리만 조회
                    category = TagCategory.objects.filter(id=category_id).first()
                    if category:
                        # 해당 카테고리를 루트로 하는 트리 구성
                        def build_tree_from_category(cat):
                            """특정 카테고리부터 시작하는 트리 구조 구성"""
                            serializer = self.get_serializer(cat, context={'request': request})
                            data = serializer.data
                            # 하위 카테고리들도 포함
                            children = TagCategory.objects.filter(
                                parent=cat
                            ).order_by('order', 'name_ko')
                            data['children'] = [build_tree_from_category(child) for child in children]
                            return data
                        
                        tree_data = [build_tree_from_category(category)]
                        logger.info(f"[TAG_CATEGORY] DevOps 도메인 필터링 적용: 카테고리 ID={category_id}")
                        return Response(tree_data)
                    else:
                        logger.warning(f"[TAG_CATEGORY] DevOps 카테고리를 찾을 수 없습니다: ID={category_id}")
                        return Response([])
                else:
                    logger.warning("[TAG_CATEGORY] DevOps 카테고리 ID를 찾을 수 없습니다.")
                    return Response([])
            
            # 일반 도메인: 전체 트리 반환
            # 1단계 카테고리만 가져오기
            root_categories = TagCategory.objects.filter(
                parent=None
            ).order_by('order', 'name_ko')
            
            def build_tree(category):
                """재귀적으로 트리 구조 구성"""
                children = TagCategory.objects.filter(
                    parent=category
                ).order_by('order', 'name_ko')
                
                # serializer에 request context 전달 (다국어 지원을 위해)
                serializer = self.get_serializer(category, context={'request': request})
                data = serializer.data
                data['children'] = [build_tree(child) for child in children]
                return data
            
            tree_data = [build_tree(cat) for cat in root_categories]
            return Response(tree_data)
        except Exception as e:
            logger.error(f"카테고리 트리 조회 중 오류 발생: {str(e)}")
            return Response(
                {'error': f'카테고리 트리 조회 중 오류가 발생했습니다: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """특정 카테고리의 하위 카테고리 조회"""
        try:
            category = self.get_object()
            children = TagCategory.objects.filter(
                parent=category
            ).order_by('order', 'name_ko')
            
            serializer = self.get_serializer(children, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"하위 카테고리 조회 중 오류 발생: {str(e)}")
            return Response(
                {'error': f'하위 카테고리 조회 중 오류가 발생했습니다: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def tags(self, request, pk=None):
        """특정 카테고리에 속한 태그 조회 (하위 카테고리의 태그도 포함, 캐싱 지원)"""
        try:
            category = self.get_object()
            
            # 캐시 키 생성
            cache_key_tags = f"tag_category_{category.id}_tags"
            cache_key_descendants = f"tag_category_{category.id}_descendants"
            
            # 캐시에서 하위 카테고리 ID 조회
            all_category_ids = cache.get(cache_key_descendants)
            
            if all_category_ids is None:
                # 캐시에 없으면 재귀적으로 모든 하위 카테고리 ID 수집
                def get_all_descendant_ids(category):
                    """카테고리와 모든 하위 카테고리 ID를 재귀적으로 수집"""
                    category_ids = [category.id]
                    children = TagCategory.objects.filter(parent=category)
                    for child in children:
                        category_ids.extend(get_all_descendant_ids(child))
                    return category_ids
                
                all_category_ids = get_all_descendant_ids(category)
                # 캐시에 저장
                cache.set(cache_key_descendants, all_category_ids, CATEGORY_DESCENDANTS_CACHE_TIMEOUT)
                logger.info(f"[TAG_CATEGORY] 하위 카테고리 ID 캐시 저장: category_id={category.id}, count={len(all_category_ids)}")
            else:
                logger.debug(f"[TAG_CATEGORY] 하위 카테고리 ID 캐시 히트: category_id={category.id}, count={len(all_category_ids)}")
            
            # 캐시에서 태그 ID 목록 조회
            tag_ids = cache.get(cache_key_tags)
            
            if tag_ids is None:
                # 캐시에 없으면 데이터베이스에서 조회
                tags_queryset = Tag.objects.filter(categories__id__in=all_category_ids).distinct().order_by('name_ko')
                tag_ids = list(tags_queryset.values_list('id', flat=True))
                # 캐시에 저장
                cache.set(cache_key_tags, tag_ids, CATEGORY_TAGS_CACHE_TIMEOUT)
                logger.info(f"[TAG_CATEGORY] 태그 ID 목록 캐시 저장: category_id={category.id}, count={len(tag_ids)}")
            else:
                logger.debug(f"[TAG_CATEGORY] 태그 ID 목록 캐시 히트: category_id={category.id}, count={len(tag_ids)}")
            
            # 태그 ID로 실제 태그 객체 조회
            tags = Tag.objects.filter(id__in=tag_ids).order_by('name_ko')
            
            # 페이지네이션 지원
            page = self.paginate_queryset(tags)
            if page is not None:
                serializer = TagSerializer(page, many=True, context={'request': request})
                return self.get_paginated_response(serializer.data)
            
            serializer = TagSerializer(tags, many=True, context={'request': request})
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"카테고리 태그 조회 중 오류 발생: {str(e)}")
            return Response(
                {'error': f'카테고리 태그 조회 중 오류가 발생했습니다: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """카테고리 검색 API"""
        try:
            query = request.query_params.get('q', '').strip()
            if not query:
                return Response({'results': []})
            
            # 다국어 이름으로 검색 (ko, en, es, zh, ja)
            categories = TagCategory.objects.filter(
                models.Q(name_ko__icontains=query) |
                models.Q(name_en__icontains=query) |
                models.Q(name_es__icontains=query) |
                models.Q(name_zh__icontains=query) |
                models.Q(name_ja__icontains=query)
            ).order_by('level', 'order', 'name_ko')[:20]  # 최대 20개 결과
            
            serializer = self.get_serializer(categories, many=True)
            return Response({'results': serializer.data})
        except Exception as e:
            logger.error(f"카테고리 검색 중 오류 발생: {str(e)}")
            return Response(
                {'error': f'카테고리 검색 중 오류가 발생했습니다: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        """카테고리 노드 이동 (부모 변경 및 순서 변경) - 관리자 전용"""
        try:
            # 관리자 권한 확인
            if not request.user or request.user.is_anonymous:
                return Response(
                    {'error': '인증이 필요합니다.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # UserProfile에서 role 확인
            try:
                user_profile = request.user.profile
                is_admin = user_profile.role == 'admin_role'
            except:
                # UserProfile이 없거나 role이 없는 경우 Django의 is_superuser/is_staff 확인
                is_admin = request.user.is_superuser or request.user.is_staff
            
            if not is_admin:
                return Response(
                    {'error': '관리자 권한이 필요합니다.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            category = self.get_object()
            new_parent_id = request.data.get('parent_id')  # None이면 최상위
            new_order = request.data.get('order', 0)
            
            # 부모 변경
            if new_parent_id is None:
                category.parent = None
            else:
                try:
                    new_parent = TagCategory.objects.get(id=new_parent_id)
                    # 순환 참조 방지
                    if new_parent.id == category.id:
                        return Response(
                            {'error': '자기 자신을 부모로 설정할 수 없습니다.'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    # 깊이 검증 (최대 3단계)
                    if new_parent.level >= 3:
                        return Response(
                            {'error': '최대 3단계까지만 가능합니다.'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    category.parent = new_parent
                except TagCategory.DoesNotExist:
                    return Response(
                        {'error': '상위 카테고리를 찾을 수 없습니다.'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            
            category.order = new_order
            category.save()
            
            serializer = self.get_serializer(category)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"카테고리 이동 중 오류 발생: {str(e)}")
            return Response(
                {'error': f'카테고리 이동 중 오류가 발생했습니다: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    @permission_classes([IsAuthenticated])
    def translate_all(self, request):
        """
        모든 카테고리의 다국어 번역을 채워 넣는 API
        관리자 또는 인증된 사용자만 접근 가능
        """
        try:
            # 관리자 권한 확인 (선택사항)
            try:
                user_profile = request.user.profile
                is_admin = user_profile.role == 'admin_role'
            except:
                is_admin = request.user.is_superuser or request.user.is_staff
            
            if not is_admin:
                return Response(
                    {'error': '관리자 권한이 필요합니다.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            from quiz.models import TagCategory
            from quiz.utils.multilingual_utils import (
                batch_translate_texts,
                LANGUAGE_KO,
                LANGUAGE_EN,
                LANGUAGE_ES,
                LANGUAGE_ZH,
                LANGUAGE_JA,
            )
            
            # 모든 카테고리 조회
            categories = TagCategory.objects.all().order_by('id')
            total_count = categories.count()
            
            translated_count = 0
            skipped_count = 0
            error_count = 0
            errors = []
            
            for category in categories:
                try:
                    # 영어 이름 확인
                    english_name = category.name_en
                    if not english_name or not english_name.strip():
                        # 영어가 없으면 한국어를 영어로 번역
                        korean_name = category.name_ko
                        if korean_name and korean_name.strip():
                            try:
                                translated_names = batch_translate_texts([korean_name], LANGUAGE_KO, LANGUAGE_EN)
                                if translated_names and translated_names[0]:
                                    english_name = translated_names[0].strip()
                                    category.name_en = english_name
                                    category.is_en_complete = True
                            except Exception as e:
                                logger.warning(f"한국어 → 영어 번역 실패: {e}")
                        else:
                            skipped_count += 1
                            continue
                    
                    english_name = english_name.strip()
                    update_fields = []
                    
                    # 번역 대상 언어별 처리
                    target_languages = [
                        (LANGUAGE_KO, 'name_ko', 'is_ko_complete'),
                        (LANGUAGE_ES, 'name_es', 'is_es_complete'),
                        (LANGUAGE_ZH, 'name_zh', 'is_zh_complete'),
                        (LANGUAGE_JA, 'name_ja', 'is_ja_complete'),
                    ]
                    
                    for target_lang, name_field, complete_field in target_languages:
                        current_value = getattr(category, name_field, None)
                        
                        # 이미 값이 있으면 건너뜀
                        if current_value and current_value.strip():
                            continue
                        
                        # 영어 → 대상 언어 번역
                        try:
                            translated_names = batch_translate_texts([english_name], LANGUAGE_EN, target_lang)
                            if translated_names and translated_names[0] and translated_names[0].strip():
                                translated_name = translated_names[0].strip()
                                setattr(category, name_field, translated_name)
                                setattr(category, complete_field, True)
                                update_fields.extend([name_field, complete_field])
                        except Exception as e:
                            logger.error(f"번역 중 오류 ({LANGUAGE_EN} → {target_lang}): {str(e)}")
                    
                    # 번역된 필드가 있으면 저장
                    if update_fields:
                        category.save(update_fields=update_fields)
                        translated_count += 1
                    else:
                        skipped_count += 1
                        
                except Exception as e:
                    error_count += 1
                    errors.append(f"카테고리 {category.id}: {str(e)}")
                    logger.error(f"카테고리 번역 중 오류: category_id={category.id}, error={str(e)}")
            
            return Response({
                'success': True,
                'message': '모든 카테고리 번역 완료',
                'total': total_count,
                'translated': translated_count,
                'skipped': skipped_count,
                'errors': error_count,
                'error_details': errors[:10]  # 최대 10개 오류만 반환
            })
        except Exception as e:
            logger.error(f"카테고리 번역 API 오류: {str(e)}")
            return Response(
                {'error': f'카테고리 번역 중 오류가 발생했습니다: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# URL 패턴
urlpatterns = [
    path('', TagCategoryViewSet.as_view({'get': 'list', 'post': 'create'}), name='tag-category-list'),
    path('<int:pk>/', TagCategoryViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='tag-category-detail'),
    path('<int:pk>/move/', TagCategoryViewSet.as_view({'post': 'move'}), name='tag-category-move'),
    path('tree/', TagCategoryViewSet.as_view({'get': 'tree'}), name='tag-category-tree'),
    path('<int:pk>/children/', TagCategoryViewSet.as_view({'get': 'children'}), name='tag-category-children'),
    path('<int:pk>/tags/', TagCategoryViewSet.as_view({'get': 'tags'}), name='tag-category-tags'),
    path('search/', TagCategoryViewSet.as_view({'get': 'search'}), name='tag-category-search'),
    path('translate-all/', TagCategoryViewSet.as_view({'post': 'translate_all'}), name='tag-category-translate-all'),
]

