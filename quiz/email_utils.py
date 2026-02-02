import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
import uuid
from datetime import timedelta


def get_email_config():
    """이메일 설정을 환경변수에서 가져옵니다."""
    return {
        'SMTPHost': os.getenv('SMTP_HOST', 'smtp.naver.com'),
        'SMTPPort': int(os.getenv('SMTP_PORT', 587)),
        'Username': os.getenv('SMTP_USERNAME', 'doohee323@naver.com'),
        'Password': os.getenv('SMTP_PASSWORD', 'TUUJB8UUNZSV'),
        'FromEmail': os.getenv('FROM_EMAIL', 'doohee323@naver.com'),
    }


def send_email_verification(user_profile, verification_url):
    """이메일 인증 메일을 발송합니다."""
    email_config = get_email_config()

    # 사용자 언어 설정에 따라 템플릿 선택
    from quiz.utils.multilingual_utils import BASE_LANGUAGE
    language = getattr(user_profile, 'language', BASE_LANGUAGE)
    template_name = f'send_verification_{language}.html'
    
    # 템플릿 컨텍스트
    context = {
        'username': user_profile.user.username,
        'verification_url': verification_url
    }
    
    # HTML 이메일 템플릿 렌더링
    try:
        html_content = render_to_string(template_name, context)
    except:
        # 템플릿이 없으면 기본 한국어 템플릿 사용
        html_content = render_to_string('send_verification_ko.html', context)
    
    # 이메일 제목 설정
    from quiz.utils.multilingual_utils import LANGUAGE_KO, LANGUAGE_EN, LANGUAGE_ES, LANGUAGE_ZH, LANGUAGE_JA
    if language == LANGUAGE_KO:
        subject = "DrillQuiz 이메일 인증"
    elif language == LANGUAGE_ES:
        subject = "DrillQuiz Verificación de Correo Electrónico"
    elif language == LANGUAGE_ZH:
        subject = "DrillQuiz 电子邮件验证"
    elif language == LANGUAGE_JA:
        subject = "DrillQuiz メール認証"
    else:
        subject = "DrillQuiz Email Verification"
    
    try:
        # SMTP 서버 연결
        server = smtplib.SMTP(email_config['SMTPHost'], email_config['SMTPPort'])
        server.starttls()
        server.login(email_config['Username'], email_config['Password'])

        # 이메일 메시지 생성
        msg = MIMEMultipart('alternative')
        msg['From'] = email_config['FromEmail']
        msg['To'] = user_profile.user.email
        msg['Subject'] = subject
        
        # HTML 버전만 추가
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # 이메일 발송
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"이메일 발송 실패: {e}")
        return False


def generate_verification_token():
    """인증 토큰을 생성합니다."""
    return str(uuid.uuid4())


def is_token_expired(sent_at):
    """토큰이 만료되었는지 확인합니다 (24시간)."""
    if not sent_at:
        return True
    
    expiration_time = sent_at + timedelta(hours=24)
    return timezone.now() > expiration_time 