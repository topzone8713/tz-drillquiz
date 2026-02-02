"""
URL configuration for drillquiz project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from . import views
from quiz.views.short_url_views import redirect_short_url
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('quiz.urls')),
]

# 정적 파일 서빙 (프로덕션 환경에서도 작동하도록 수정)
# favicon.ico 특별 처리
urlpatterns += [
    re_path(r'^favicon\.ico$', serve, {
        'document_root': os.path.join(settings.BASE_DIR, 'public'),
        'path': 'favicon.ico'
    }),
]

# public 디렉토리의 정적 파일들 직접 서빙
urlpatterns += [
    # JavaScript 파일
    re_path(r'^js/(?P<path>.*)$', serve, {
        'document_root': os.path.join(settings.BASE_DIR, 'public', 'js'),
    }),
    # CSS 파일
    re_path(r'^css/(?P<path>.*)$', serve, {
        'document_root': os.path.join(settings.BASE_DIR, 'public', 'css'),
    }),
    # 이미지 파일
    re_path(r'^img/(?P<path>.*)$', serve, {
        'document_root': os.path.join(settings.BASE_DIR, 'public', 'img'),
    }),
    # 폰트 파일
    re_path(r'^fonts/(?P<path>.*)$', serve, {
        'document_root': os.path.join(settings.BASE_DIR, 'public', 'fonts'),
    }),
    # sitemap.xml 동적 생성 (도메인별로 다르게 처리)
    re_path(r'^sitemap\.xml$', views.sitemap_xml, name='sitemap_xml'),
    # robots.txt 동적 생성 (도메인별로 다르게 처리)
    re_path(r'^robots\.txt$', views.robots_txt, name='robots_txt'),
    # 기타 정적 파일들 (ico, png, jpg, jpeg, gif, svg, woff, woff2, ttf, eot)
    re_path(r'^(?P<path>.*\.(ico|png|jpg|jpeg|gif|svg|woff|woff2|ttf|eot))$', serve, {
        'document_root': os.path.join(settings.BASE_DIR, 'public'),
    }),
]

# 정적 파일 서빙 (DEBUG 모드에서)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# 단축 URL 리다이렉션 (Vue 앱 라우팅보다 우선)
urlpatterns += [
    re_path(r'^s/(?P<short_code>[a-zA-Z0-9]+)/?$', redirect_short_url, name='redirect_short_url'),
]

# 반드시 마지막에 catch-all 패턴 추가
urlpatterns += [
    re_path(r'^.*$', views.vue_app),
] 