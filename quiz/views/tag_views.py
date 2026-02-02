import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db import models
from django.urls import path
from ..models import Tag, Exam, Study
from ..serializers import TagSerializer

logger = logging.getLogger(__name__)
User = get_user_model()


class TagViewSet(viewsets.ModelViewSet):
    """
    태그 관리 ViewSet
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    
    def _invalidate_category_cache(self, category):
        """카테고리 관련 캐시 무효화 (현재 카테고리 및 모든 상위 카테고리)"""
        try:
            from django.core.cache import cache
            
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
        except Exception as e:
            logger.error(f"[TAG] 카테고리 캐시 무효화 실패: category_id={category.id}, error={str(e)}")
    
    def get_queryset(self):
        """태그 목록을 알파벳 순으로 정렬하여 반환"""
        queryset = Tag.objects.all()
        
        # DevOps 도메인 필터링: devops 도메인인 경우 "IT 기술 > IT 기술" 카테고리의 태그만 반환
        from quiz.utils.domain_utils import is_devops_domain, get_devops_category_id
        if is_devops_domain(self.request):
            category_id = get_devops_category_id()
            if category_id:
                queryset = queryset.filter(categories__id=category_id).distinct()
                logger.info(f"[TAG] DevOps 도메인 필터링 적용: 카테고리 ID={category_id}")
            else:
                logger.warning("[TAG] DevOps 카테고리 ID를 찾을 수 없습니다.")
                # 카테고리를 찾을 수 없으면 빈 결과 반환
                queryset = Tag.objects.none()
        
        return queryset.order_by('name_ko')
    
    def destroy(self, request, *args, **kwargs):
        """태그 삭제 시 사용 여부 확인"""
        try:
            instance = self.get_object()
            from quiz.utils.multilingual_utils import get_localized_field, BASE_LANGUAGE
            tag_lang = instance.created_language if hasattr(instance, 'created_language') else BASE_LANGUAGE
            tag_name = get_localized_field(instance, 'name', tag_lang, f'태그 #{instance.id}')
            
            # Exam에서 사용 중인지 확인
            exams_using_tag = Exam.objects.filter(tags=instance).count()
            if exams_using_tag > 0:
                return Response(
                    {
                        'error': f'태그 "{tag_name}"은(는) {exams_using_tag}개의 시험(Exam)에서 사용 중이므로 삭제할 수 없습니다.',
                        'detail': f'This tag is being used in {exams_using_tag} exam(s).',
                        'usage_count': {
                            'exams': exams_using_tag,
                            'studies': 0
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Study에서 사용 중인지 확인
            studies_using_tag = Study.objects.filter(tags=instance).count()
            if studies_using_tag > 0:
                return Response(
                    {
                        'error': f'태그 "{tag_name}"은(는) {studies_using_tag}개의 스터디(Study)에서 사용 중이므로 삭제할 수 없습니다.',
                        'detail': f'This tag is being used in {studies_using_tag} study(studies).',
                        'usage_count': {
                            'exams': 0,
                            'studies': studies_using_tag
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 사용 중이 아니면 삭제 진행
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Exception as e:
            logger.error(f"태그 삭제 중 오류 발생: {str(e)}")
            return Response(
                {'error': f'태그 삭제 중 오류가 발생했습니다: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def perform_create(self, serializer):
        """태그 생성 시 현재 사용자를 생성자로 설정"""
        if self.request.user and not self.request.user.is_anonymous:
            return serializer.save(created_by=self.request.user)
        else:
            return serializer.save(created_by=None)
    
    def create(self, request, *args, **kwargs):
        """태그 생성 API"""
        try:
            # 현재 사용자 언어에 따라 적절한 필드에 저장
            from quiz.utils.multilingual_utils import BASE_LANGUAGE
            user_language = BASE_LANGUAGE  # 기본값
            if request.user and not request.user.is_anonymous:
                try:
                    user_profile = request.user.profile
                    user_language = user_profile.language
                except:
                    pass
            
            # 다국어 필드 처리
            from quiz.utils.multilingual_utils import LANGUAGE_KO, LANGUAGE_EN, LANGUAGE_ES, LANGUAGE_ZH, BASE_LANGUAGE
            tag_name = (request.data.get('name_ko') or 
                       request.data.get('name_en') or 
                       request.data.get('name_es') or 
                       request.data.get('name_zh') or '')
            
            # 현재 사용자 언어에 맞는 필드에 저장
            if user_language == LANGUAGE_KO:
                request.data['name_ko'] = tag_name
                if not request.data.get('name_en'):
                    request.data['name_en'] = tag_name
            elif user_language == LANGUAGE_ES:
                request.data['name_es'] = tag_name
                if not request.data.get('name_en'):
                    request.data['name_en'] = tag_name
            elif user_language == LANGUAGE_ZH:
                request.data['name_zh'] = tag_name
                if not request.data.get('name_en'):
                    request.data['name_en'] = tag_name
            else:
                # LANGUAGE_EN 또는 기본값
                request.data['name_en'] = tag_name
                if not request.data.get('name_ko'):
                    request.data['name_ko'] = tag_name
            
            # 중복 태그 확인 - 기존 태그가 있으면 반환
            # 현재 Tag 모델은 name_ko, name_en만 지원하므로 두 필드만 확인
            existing_tag = Tag.objects.filter(
                models.Q(name_ko=tag_name) | models.Q(name_en=tag_name)
            ).first()
            
            if existing_tag:
                serializer = self.get_serializer(existing_tag)
                return Response(serializer.data, status=status.HTTP_200_OK)
            
            # 카테고리 정보를 임시로 저장 (태그 생성 후 연결하기 위해)
            category_ids = request.data.get('categories', [])
            # categories는 ManyToMany 필드이므로 시리얼라이저에서 제외
            if 'categories' in request.data:
                request_data_copy = request.data.copy()
                # categories를 제거하여 시리얼라이저 검증 통과
                if hasattr(request_data_copy, '_mutable'):
                    request_data_copy._mutable = True
                request_data_copy.pop('categories', None)
            else:
                request_data_copy = request.data
            
            serializer = self.get_serializer(data=request_data_copy)
            serializer.is_valid(raise_exception=True)
            
            # 태그 생성 (perform_create를 통해 created_by 설정)
            tag_instance = self.perform_create(serializer)
            
            # 카테고리 연결 처리
            if category_ids:
                from ..models import TagCategory
                from django.core.cache import cache
                categories = TagCategory.objects.filter(id__in=category_ids)
                tag_instance.categories.set(categories)
                
                # 태그의 카테고리가 변경되었으므로 관련 카테고리 캐시 무효화
                for category in categories:
                    # 해당 카테고리와 모든 상위 카테고리의 캐시 무효화
                    self._invalidate_category_cache(category)
            
            # 카테고리가 연결된 태그 정보 다시 시리얼라이즈
            serializer = self.get_serializer(tag_instance)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            
        except Exception as e:
            logger.error(f"태그 생성 중 오류 발생: {str(e)}")
            return Response(
                {'error': f'태그 생성 중 오류가 발생했습니다: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """태그 검색 API"""
        try:
            query = request.query_params.get('q', '').strip()
            if not query:
                return Response({'results': []})
            
            # 한국어와 영어 이름으로 검색
            tags = Tag.objects.filter(
                models.Q(name_ko__icontains=query) | 
                models.Q(name_en__icontains=query)
            ).order_by('name_ko')[:10]  # 최대 10개 결과
            
            serializer = self.get_serializer(tags, many=True)
            return Response({'results': serializer.data})
            
        except Exception as e:
            logger.error(f"태그 검색 중 오류 발생: {str(e)}")
            return Response(
                {'error': f'태그 검색 중 오류가 발생했습니다: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def devops_info(self, request):
        """DevOps 태그 정보 조회 API"""
        try:
            # DevOps 태그 찾기
            devops_tag = Tag.objects.filter(
                models.Q(name_ko='DevOps') | 
                models.Q(name_en='DevOps')
            ).first()
            
            if not devops_tag:
                return Response({
                    'found': False,
                    'message': 'DevOps 태그를 찾을 수 없습니다.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = self.get_serializer(devops_tag)
            return Response({
                'found': True,
                'tag': serializer.data
            })
            
        except Exception as e:
            logger.error(f"DevOps 태그 정보 조회 중 오류 발생: {str(e)}")
            return Response(
                {'error': f'DevOps 태그 정보 조회 중 오류가 발생했습니다: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# URL 패턴
urlpatterns = [
    path('', TagViewSet.as_view({'get': 'list', 'post': 'create'}), name='tag-list'),
    path('<int:pk>/', TagViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='tag-detail'),
    path('search/', TagViewSet.as_view({'get': 'search'}), name='tag-search'),
    path('devops-info/', TagViewSet.as_view({'get': 'devops_info'}), name='tag-devops-info'),
]
