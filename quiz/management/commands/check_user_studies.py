from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from quiz.models import Study, Member

class Command(BaseCommand):
    help = '특정 사용자의 스터디 멤버십을 확인합니다.'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='확인할 사용자명')

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
            self.stdout.write(f"사용자: {user.username}")
            self.stdout.write(f"이메일: {user.email}")
            self.stdout.write("")
            
            # 사용자가 멤버인 스터디들
            memberships = Member.objects.filter(user=user)
            self.stdout.write(f"멤버로 등록된 스터디 수: {memberships.count()}")
            
            for membership in memberships:
                study = membership.study
                self.stdout.write(f"- {study.title} (ID: {study.id})")
                self.stdout.write(f"  공개 여부: {study.is_public}")
                self.stdout.write(f"  역할: {membership.role}")
                self.stdout.write(f"  활성화: {membership.is_active}")
                self.stdout.write("")
            
            # 사용자가 생성한 스터디들
            created_studies = Study.objects.filter(created_by=user)
            self.stdout.write(f"생성한 스터디 수: {created_studies.count()}")
            
            for study in created_studies:
                self.stdout.write(f"- {study.title} (ID: {study.id})")
                self.stdout.write(f"  공개 여부: {study.is_public}")
                self.stdout.write("")
            
            # 모든 공개 스터디
            all_public_studies = Study.objects.filter(is_public=True)
            self.stdout.write(f"전체 공개 스터디 수: {all_public_studies.count()}")
            
            for study in all_public_studies:
                self.stdout.write(f"- {study.title} (ID: {study.id})")
                self.stdout.write("")
                
        except User.DoesNotExist:
            self.stdout.write(f"사용자 '{username}'를 찾을 수 없습니다.") 