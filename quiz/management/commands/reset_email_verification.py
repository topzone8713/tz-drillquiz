from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from quiz.models import UserProfile
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = '이메일 인증 상태를 초기화합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='특정 사용자의 이메일 인증 상태를 초기화합니다'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='모든 사용자의 이메일 인증 상태를 초기화합니다'
        )
        parser.add_argument(
            '--verified',
            action='store_true',
            help='이메일 인증 상태를 True로 설정합니다'
        )

    def handle(self, *args, **options):
        username = options.get('username')
        reset_all = options.get('all')
        set_verified = options.get('verified')

        if username:
            # 특정 사용자 초기화
            try:
                user = User.objects.get(username=username)
                profile, created = UserProfile.objects.get_or_create(user=user)
                
                if set_verified:
                    profile.email_verified = True
                    self.stdout.write(
                        self.style.SUCCESS(f'사용자 {username}의 이메일 인증 상태를 True로 설정했습니다.')
                    )
                else:
                    profile.email_verified = False
                    profile.email_verification_token = None
                    profile.email_verification_sent_at = None
                    self.stdout.write(
                        self.style.SUCCESS(f'사용자 {username}의 이메일 인증 상태를 초기화했습니다.')
                    )
                
                profile.save()
                
                self.stdout.write(f'현재 상태: email_verified={profile.email_verified}')
                if profile.email_verification_sent_at:
                    self.stdout.write(f'마지막 발송 시간: {profile.email_verification_sent_at}')
                
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'사용자 {username}을 찾을 수 없습니다.')
                )
        
        elif reset_all:
            # 모든 사용자 초기화
            profiles = UserProfile.objects.all()
            count = 0
            
            for profile in profiles:
                if set_verified:
                    profile.email_verified = True
                else:
                    profile.email_verified = False
                    profile.email_verification_token = None
                    profile.email_verification_sent_at = None
                
                profile.save()
                count += 1
            
            if set_verified:
                self.stdout.write(
                    self.style.SUCCESS(f'모든 사용자({count}명)의 이메일 인증 상태를 True로 설정했습니다.')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'모든 사용자({count}명)의 이메일 인증 상태를 초기화했습니다.')
                )
        
        else:
            # 현재 상태 확인
            if username:
                try:
                    user = User.objects.get(username=username)
                    profile, created = UserProfile.objects.get_or_create(user=user)
                except User.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f'사용자 {username}을 찾을 수 없습니다.')
                    )
                    return
            else:
                # 첫 번째 사용자 확인
                try:
                    user = User.objects.first()
                    if not user:
                        self.stdout.write(
                            self.style.ERROR('등록된 사용자가 없습니다.')
                        )
                        return
                    profile, created = UserProfile.objects.get_or_create(user=user)
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'사용자 정보를 가져오는데 실패했습니다: {e}')
                    )
                    return
            
            self.stdout.write(f'사용자: {profile.user.username}')
            self.stdout.write(f'이메일: {profile.user.email}')
            self.stdout.write(f'이메일 인증 상태: {profile.email_verified}')
            self.stdout.write(f'인증 토큰: {profile.email_verification_token}')
            if profile.email_verification_sent_at:
                self.stdout.write(f'마지막 발송 시간: {profile.email_verification_sent_at}')
            else:
                self.stdout.write('마지막 발송 시간: 없음')
            
            self.stdout.write('\n사용법:')
            self.stdout.write('  python manage.py reset_email_verification --username <사용자명>')
            self.stdout.write('  python manage.py reset_email_verification --username <사용자명> --verified')
            self.stdout.write('  python manage.py reset_email_verification --all')
            self.stdout.write('  python manage.py reset_email_verification --all --verified') 