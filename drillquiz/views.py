from django.shortcuts import render
from django.http import HttpResponse, Http404
import os
from django.conf import settings
import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)

def robots_txt(request):
    """도메인별로 robots.txt를 동적으로 생성하는 뷰
    
    허용된 도메인:
    - drillquiz.com
    - devops.drillquiz.com
    - leetcode.drillquiz.com
    - us.drillquiz.com
    
    차단된 도메인:
    - us-dev.drillquiz.com
    - us-qa.drillquiz.com
    - 기타 -dev, -qa 서브도메인
    """
    # 현재 요청의 호스트 확인
    host = request.get_host().lower()
    
    # 허용된 도메인 목록
    allowed_domains = [
        'drillquiz.com',
        'www.drillquiz.com',
        'devops.drillquiz.com',
        'leetcode.drillquiz.com',
        'us.drillquiz.com',
    ]
    
    # 차단할 도메인 패턴 (dev, qa 환경)
    blocked_patterns = ['-dev.drillquiz.com', '-qa.drillquiz.com']
    
    # 도메인이 차단 패턴에 해당하는지 확인
    is_blocked = any(pattern in host for pattern in blocked_patterns)
    
    # 도메인이 허용 목록에 있는지 확인
    is_allowed = any(domain in host or host == domain for domain in allowed_domains)
    
    # robots.txt 내용 생성
    if is_blocked or not is_allowed:
        # 차단 환경: 모든 크롤링 차단
        robots_content = """User-agent: *
Disallow: /

# Block all search engine crawling
# This environment is not production
# Domain: {host}
""".format(host=host)
    else:
        # 허용 환경: SEO 설정 포함
        # sitemap URL을 도메인에 맞게 설정
        sitemap_url = f"https://{host}/sitemap.xml"
        
        robots_content = """User-agent: *
# 기본적으로 모든 페이지 허용
Allow: /

# 공개 엔드포인트 명시적으로 허용 (Google 크롤러 접근)
Allow: /api/health/
Allow: /api/translations/
Allow: /api/exams/
Allow: /api/studies/
Allow: /api/tag-categories/
Allow: /api/questions/
Allow: /api/exam/
Allow: /api/realtime/mandatory-rules/
Allow: /api/realtime/interview-prompt-template/

# Vue.js SPA 페이지들 허용
Allow: /getting-started
Allow: /random-practice
Allow: /question-files
Allow: /login
Allow: /register

# Sitemap 위치
Sitemap: {sitemap_url}

# 관리자 페이지 및 개인정보 관련 페이지 차단
Disallow: /admin/
Disallow: /api/users/
Disallow: /api/user-profile/
Disallow: /api/exam-results/
Disallow: /api/study-progress-history/
Disallow: /api/user-statistics/
Disallow: /api/realtime/session/
Disallow: /api/auth/
Disallow: /api/token/
Disallow: /api/google-oauth/

# API 다운로드 엔드포인트 차단 (인덱싱 불필요)
Disallow: /api/question-files/*/download/

# 쿼리 파라미터가 있는 동적 URL 차단 (canonical 태그로 처리되지만 크롤링 부하 감소)
Disallow: /*?returnTo=
Disallow: /*?fromHomeMenu=
Disallow: /*?question_id=
Disallow: /*?exam_id=
Disallow: /*?group_id=
Disallow: /*?sortBy=
Disallow: /*?sortOrder=
""".format(sitemap_url=sitemap_url)
    
    response = HttpResponse(robots_content, content_type='text/plain')
    response['Cache-Control'] = 'public, max-age=3600'
    return response

def sitemap_xml(request):
    """도메인별로 sitemap.xml을 동적으로 생성하는 뷰
    
    현재 도메인에 맞게 sitemap을 생성합니다.
    """
    # 현재 요청의 호스트 확인
    host = request.get_host().lower()
    
    # 허용된 도메인 목록
    allowed_domains = [
        'drillquiz.com',
        'www.drillquiz.com',
        'devops.drillquiz.com',
        'leetcode.drillquiz.com',
        'us.drillquiz.com',
    ]
    
    # 차단할 도메인 패턴 (dev, qa 환경)
    blocked_patterns = ['-dev.drillquiz.com', '-qa.drillquiz.com']
    
    # 도메인이 차단 패턴에 해당하는지 확인
    is_blocked = any(pattern in host for pattern in blocked_patterns)
    
    # 도메인이 허용 목록에 있는지 확인
    is_allowed = any(domain in host or host == domain for domain in allowed_domains)
    
    # 차단되거나 허용되지 않은 도메인은 빈 sitemap 반환
    if is_blocked or not is_allowed:
        sitemap_content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
</urlset>"""
    else:
        # 현재 날짜 (YYYY-MM-DD 형식)
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 기본 URL 생성
        base_url = f"https://{host}"
        
        # sitemap.xml 내용 생성
        sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{base_url}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>{base_url}/getting-started</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>{base_url}/random-practice</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>{base_url}/question-files</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>{base_url}/login</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>
  <url>
    <loc>{base_url}/register</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>
  <url>
    <loc>{base_url}/privacy-policy</loc>
    <lastmod>{today}</lastmod>
    <changefreq>yearly</changefreq>
    <priority>0.3</priority>
  </url>
  <url>
    <loc>{base_url}/terms-of-service</loc>
    <lastmod>{today}</lastmod>
    <changefreq>yearly</changefreq>
    <priority>0.3</priority>
  </url>
</urlset>"""
    
    response = HttpResponse(sitemap_content, content_type='application/xml; charset=utf-8')
    response['Cache-Control'] = 'public, max-age=3600'
    return response

def vue_app(request):
    """Vue.js 앱을 서빙하는 뷰
    
    모든 경로에 대해 index.html을 반환하여 Vue.js SPA 라우팅을 지원합니다.
    Google 크롤러를 포함한 모든 요청을 허용합니다.
    """
    try:
        # index.html 파일 경로
        index_path = os.path.join(settings.BASE_DIR, 'public', 'index.html')
        
        # 파일이 존재하는지 확인
        if not os.path.exists(index_path):
            logger.error(f"index.html not found at {index_path}")
            return HttpResponse(f"index.html not found at {index_path}", status=404, content_type='text/plain')
        
        # index.html 읽기
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 현재 도메인에 맞게 canonical URL 및 meta 태그 동적 설정
        host = request.get_host().lower()
        scheme = 'https' if not settings.DEBUG else request.scheme
        base_url = f"{scheme}://{host}"
        
        # 사용자 언어 감지 (Accept-Language 헤더 또는 쿠키에서)
        user_language = 'en'  # 기본값
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        if accept_language:
            # Accept-Language 헤더 파싱 (예: "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7")
            languages = [lang.split(';')[0].split('-')[0].lower() for lang in accept_language.split(',')]
            from quiz.utils.multilingual_utils import SUPPORTED_LANGUAGES
            supported_languages = SUPPORTED_LANGUAGES
            for lang in languages:
                if lang in supported_languages:
                    user_language = lang
                    break
        
        # 언어별 메타 설명 설정
        meta_descriptions = {
            'ko': 'DrillQuiz - 최고의 온라인 퀴즈 학습 플랫폼. DrillQuiz 퀴즈로 연습하고, 시험을 관리하며, 학습 진도를 추적하세요. 지금 DrillQuiz로 학습을 시작하세요!',
            'en': 'DrillQuiz - The best online quiz learning platform. Practice with DrillQuiz quizzes, manage exams, and track your learning progress. Start learning with DrillQuiz today!',
            'es': 'DrillQuiz - La mejor plataforma de aprendizaje de cuestionarios en línea. Practica con cuestionarios DrillQuiz, gestiona exámenes y rastrea tu progreso de aprendizaje. ¡Comienza a aprender con DrillQuiz hoy!',
            'zh': 'DrillQuiz - 最佳在线测验学习平台。使用DrillQuiz测验进行练习，管理考试并跟踪您的学习进度。立即开始使用DrillQuiz学习！',
            'ja': 'DrillQuiz - 最高のオンラインクイズ学習プラットフォーム。DrillQuizクイズで練習し、試験を管理し、学習の進捗を追跡します。今すぐDrillQuizで学習を始めましょう！'
        }
        
        meta_description = meta_descriptions.get(user_language, meta_descriptions['en'])
        
        # canonical URL 생성 (쿼리 파라미터 제거)
        # request.path는 쿼리 파라미터를 포함하지 않음
        current_path = request.path
        # 쿼리 파라미터가 있는 경우에도 경로만 사용
        if current_path == '/':
            canonical_url = base_url
        else:
            canonical_url = f"{base_url}{current_path}"
        
        # canonical URL 교체 (쿼리 파라미터 제거된 버전 사용)
        content = re.sub(
            r'<link rel="canonical" href="[^"]*">',
            f'<link rel="canonical" href="{canonical_url}">',
            content
        )
        # Open Graph URL 교체
        content = content.replace(
            'content="https://us.drillquiz.com"',
            f'content="{base_url}"'
        )
        # Twitter Card URL 교체
        content = content.replace(
            'name="twitter:url" content="https://us.drillquiz.com"',
            f'name="twitter:url" content="{base_url}"'
        )
        # Open Graph image URL도 동적으로 설정 (필요시)
        if 'us.drillquiz.com/favicon.ico' in content:
            content = content.replace(
                'us.drillquiz.com/favicon.ico',
                f'{host}/favicon.ico'
            )
        
        # hreflang 태그 동적 설정
        hreflang_tags = f'''    <!-- Hreflang Tags for Multilingual SEO -->
    <link rel="alternate" hreflang="x-default" href="{base_url}">
    <link rel="alternate" hreflang="en" href="{base_url}">
    <link rel="alternate" hreflang="ko" href="{base_url}">
    <link rel="alternate" hreflang="es" href="{base_url}">
    <link rel="alternate" hreflang="zh" href="{base_url}">
    <link rel="alternate" hreflang="ja" href="{base_url}">
    '''
        
        # 기존 hreflang 태그가 있으면 교체, 없으면 추가
        if '<link rel="alternate" hreflang=' in content:
            # 기존 hreflang 태그 제거 (여러 줄에 걸쳐 있을 수 있음)
            content = re.sub(r'    <!-- Hreflang Tags for Multilingual SEO -->\n.*?<link rel="alternate" hreflang="ja".*?\n', '', content, flags=re.DOTALL)
            # canonical 태그 다음에 추가
            content = content.replace(
                '<link rel="canonical"',
                hreflang_tags + '    <link rel="canonical"'
            )
        else:
            # canonical 태그 다음에 추가
            content = content.replace(
                '<link rel="canonical"',
                hreflang_tags + '    <link rel="canonical"'
            )
        
        # 메타 설명 동적 설정
        content = re.sub(
            r'<meta name="description" content="[^"]*">',
            f'<meta name="description" content="{meta_description}">',
            content
        )
        
        # Open Graph description 동적 설정
        content = re.sub(
            r'<meta property="og:description" content="[^"]*">',
            f'<meta property="og:description" content="{meta_description}">',
            content
        )
        
        # Twitter description 동적 설정
        twitter_description = meta_description[:200]  # Twitter는 200자 제한
        content = re.sub(
            r'<meta name="twitter:description" content="[^"]*">',
            f'<meta name="twitter:description" content="{twitter_description}">',
            content
        )
        
        # Google 크롤러 감지 (로깅용)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        is_google_crawler = any(bot in user_agent.lower() for bot in [
            'googlebot', 'google-inspectiontool', 'googleother',
            'google-extended', 'apis-google', 'mediapartners-google'
        ])
        
        if is_google_crawler:
            logger.info(f"Google crawler detected: {user_agent[:100]} - Serving index.html for path: {request.path} on domain: {host}")
        
        # HTML 응답 반환
        response = HttpResponse(content, content_type='text/html; charset=utf-8')
        
        # 캐시 헤더 설정 (Google 크롤러를 위한 최적화)
        response['Cache-Control'] = 'public, max-age=3600'
        
        return response
        
    except Exception as e:
        logger.error(f"Error serving Vue app: {str(e)}", exc_info=True)
        # 오류 발생 시에도 500이 아닌 기본 페이지를 반환하여 Soft 404 방지
        try:
            index_path = os.path.join(settings.BASE_DIR, 'public', 'index.html')
            if os.path.exists(index_path):
                with open(index_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return HttpResponse(content, content_type='text/html; charset=utf-8')
        except:
            pass
        return HttpResponse(f"Server error: {str(e)}", status=500, content_type='text/plain') 