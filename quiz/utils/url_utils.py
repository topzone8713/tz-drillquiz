import os
import logging

logger = logging.getLogger(__name__)

def get_frontend_url(path='', query_params=None):
    """
    환경에 맞는 프론트엔드 URL을 생성합니다.
    
    Args:
        path (str): URL 경로 (예: 'login', 'verify-email/token')
        query_params (dict): 쿼리 파라미터 (예: {'login': 'success', 'email': 'user@example.com'})
    
    Returns:
        str: 완성된 프론트엔드 URL
    """
    # CURRENT_DOMAIN 환경변수에서 프론트엔드 호스트 가져오기
    frontend_host = os.getenv('CURRENT_DOMAIN', 'localhost')
    
    # 상세한 디버깅 로그
    logger.info(f'🔍 [URL_UTILS] 프론트엔드 URL 생성 시작:')
    logger.info(f'  - CURRENT_DOMAIN: {frontend_host}')
    logger.info(f'  - ENVIRONMENT: {os.getenv("ENVIRONMENT")}')
    logger.info(f'  - DOMAIN_PLACEHOLDER in FRONTEND_HOST: {"DOMAIN_PLACEHOLDER" in frontend_host}')
    logger.info(f'  - path: {path}')
    logger.info(f'  - query_params: {query_params}')
    
    # DOMAIN_PLACEHOLDER가 포함된 경우 경고 및 fallback 처리
    if "DOMAIN_PLACEHOLDER" in frontend_host:
        logger.warning(f'⚠️ [URL_UTILS] CURRENT_DOMAIN에 DOMAIN_PLACEHOLDER가 포함됨: {frontend_host}')
        logger.warning(f'⚠️ [URL_UTILS] 이는 Kubernetes 배포 시 도메인이 제대로 설정되지 않았음을 의미합니다.')
        logger.warning(f'⚠️ [URL_UTILS] us-dev.drillquiz.com으로 fallback 처리합니다.')
        # fallback으로 us-dev.drillquiz.com 사용
        frontend_host = "us-dev.drillquiz.com"
        logger.info(f'  - fallback된 frontend_host: {frontend_host}')
    
    # 환경에 따라 스키마 결정
    scheme = 'http' if frontend_host == 'localhost' else 'https'
    logger.info(f'  - 선택된 scheme: {scheme}')
    
    # 기본 URL 구성
    if frontend_host == 'localhost':
        # 로컬 환경: 포트 8080 사용 (Vue.js 기본 포트)
        base_url = f"{scheme}://{frontend_host}:8080"
        logger.info(f'  - 로컬 환경 base_url: {base_url}')
    else:
        # 프로덕션 환경: 포트 없음
        base_url = f"{scheme}://{frontend_host}"
        logger.info(f'  - 프로덕션 환경 base_url: {base_url}')
    
    # 경로 추가
    if path:
        # 경로가 /로 시작하지 않으면 / 추가
        if not path.startswith('/'):
            path = '/' + path
        url = base_url + path
        logger.info(f'  - 경로 추가 후 url: {url}')
    else:
        url = base_url
        logger.info(f'  - 경로 없음, base_url 사용: {url}')
    
    # 쿼리 파라미터 추가
    if query_params:
        query_string = '&'.join([f"{key}={value}" for key, value in query_params.items()])
        url += '?' + query_string
        logger.info(f'  - 쿼리 파라미터 추가 후 url: {url}')
    
    logger.info(f'✅ [URL_UTILS] 최종 생성된 URL: {url}')
    return url

def get_frontend_login_url(success=True, email=None, message=None, original_domain=None, return_url=None):
    """
    로그인 관련 프론트엔드 URL을 생성합니다.
    
    Args:
        success (bool): 로그인 성공 여부
        email (str): 사용자 이메일
        message (str): 에러 메시지
        original_domain (str): 원본 도메인 (선택사항)
        return_url (str): 원본 return URL (모바일 앱 감지용, 선택사항)
    
    Returns:
        str: 로그인 관련 프론트엔드 URL
    """
    if success:
        query_params = {'login': 'success'}
        if email:
            query_params['email'] = email
    else:
        query_params = {'login': 'error'}
        if message:
            query_params['message'] = message
    
    # return_url이 capacitor:// 또는 ionic://로 시작하면 모바일 앱으로 인식
    if return_url and (return_url.startswith('capacitor://') or return_url.startswith('ionic://')):
        logger.info(f'🔍 [URL_UTILS] 모바일 앱 감지 (return_url: {return_url})')
        # 모바일 앱의 경우 capacitor://localhost로 리다이렉트
        from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
        parsed = urlparse(return_url)
        
        # 경로는 /login으로 설정 (또는 원본 경로 유지)
        path = parsed.path if parsed.path else '/login'
        
        # 쿼리 파라미터 병합
        existing_params = parse_qs(parsed.query)
        for key, value in query_params.items():
            existing_params[key] = [str(value)]
        
        query_string = urlencode(existing_params, doseq=True)
        mobile_url = urlunparse(('capacitor', 'localhost', path, '', query_string, ''))
        
        logger.info(f'✅ [URL_UTILS] 모바일 앱으로 리다이렉트 URL: {mobile_url}')
        return mobile_url
    
    # 원본 도메인이 있으면 해당 도메인 사용
    if original_domain:
        # 모바일 앱에서 localhost인 경우 서버 도메인 사용
        if original_domain in ['localhost', '127.0.0.1']:
            logger.info(f'🔍 [URL_UTILS] 모바일 앱 감지, 도메인을 us.drillquiz.com으로 변경 (원본: {original_domain})')
            original_domain = 'us.drillquiz.com'
        
        logger.info(f'🔍 [URL_UTILS] 원본 도메인 사용: {original_domain}')
        scheme = 'https'
        base_url = f"{scheme}://{original_domain}"
        
        # 쿼리 파라미터 추가
        if query_params:
            query_string = '&'.join([f"{key}={value}" for key, value in query_params.items()])
            url = base_url + '?' + query_string
        else:
            url = base_url
        
        logger.info(f'✅ [URL_UTILS] 원본 도메인으로 생성된 URL: {url}')
        return url
    
    return get_frontend_url('', query_params)
