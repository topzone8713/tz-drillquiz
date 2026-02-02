from django.core.management.base import BaseCommand
from quiz.models import Study

class Command(BaseCommand):
    help = '스터디들의 공개 상태를 확인합니다.'

    def handle(self, *args, **options):
        studies = Study.objects.all()
        
        self.stdout.write(f"총 스터디 수: {studies.count()}")
        self.stdout.write("")
        
        for study in studies:
            self.stdout.write(f"ID: {study.id}")
            self.stdout.write(f"제목: {study.title}")
            self.stdout.write(f"공개 여부: {study.is_public}")
            self.stdout.write(f"생성자: {study.created_by}")
            self.stdout.write(f"멤버 수: {study.members.count()}")
            self.stdout.write("-" * 50)
        
        public_studies = Study.objects.filter(is_public=True)
        private_studies = Study.objects.filter(is_public=False)
        
        self.stdout.write("")
        self.stdout.write(f"공개 스터디 수: {public_studies.count()}")
        self.stdout.write(f"비공개 스터디 수: {private_studies.count()}")
        
        if public_studies.count() > 0:
            self.stdout.write("")
            self.stdout.write("공개 스터디 목록:")
            for study in public_studies:
                self.stdout.write(f"- {study.title} (ID: {study.id})") 