from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from quiz.models import UserProfile

class Command(BaseCommand):
    help = '기존 사용자들에게 UserProfile을 생성합니다.'

    def handle(self, *args, **options):
        users = User.objects.all()
        created_count = 0
        
        for user in users:
            try:
                # 이미 프로필이 있는지 확인
                profile = user.profile
                self.stdout.write(f"사용자 {user.username}의 프로필이 이미 존재합니다.")
            except UserProfile.DoesNotExist:
                # 프로필이 없으면 생성
                profile = UserProfile.objects.create(user=user, role='user_role')
                created_count += 1
                self.stdout.write(f"사용자 {user.username}의 프로필을 생성했습니다.")
        
        self.stdout.write(
            self.style.SUCCESS(f'총 {created_count}개의 프로필이 생성되었습니다.')
        ) 