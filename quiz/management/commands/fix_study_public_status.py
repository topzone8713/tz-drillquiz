from django.core.management.base import BaseCommand
from django.db import models
from quiz.models import Study

class Command(BaseCommand):
    help = '스터디의 공개 상태를 수정합니다.'

    def add_arguments(self, parser):
        parser.add_argument('--list', action='store_true', help='현재 스터디 상태를 나열')
        parser.add_argument('--fix', action='store_true', help='공개 상태를 수정')

    def handle(self, *args, **options):
        if options['list']:
            self.list_studies()
        elif options['fix']:
            self.fix_study_status()
        else:
            self.stdout.write("--list 또는 --fix 옵션을 사용하세요.")

    def list_studies(self):
        studies = Study.objects.all()
        self.stdout.write("현재 스터디 상태:")
        self.stdout.write("-" * 60)
        
        for study in studies:
            study_title = study.title_ko if study.title_ko else study.title_en or '제목 없음'
            self.stdout.write(f"ID: {study.id}")
            self.stdout.write(f"제목: {study_title}")
            self.stdout.write(f"공개 여부: {study.is_public}")
            self.stdout.write(f"생성자: {study.created_by}")
            self.stdout.write("-" * 60)

    def fix_study_status(self):
        # A Interview Prep을 공개로 변경
        try:
            study = Study.objects.get(
                models.Q(title_ko="A Interview Prep") | models.Q(title_en="A Interview Prep")
            )
            study.is_public = True
            study.save()
            study_title = study.title_ko if study.title_ko else study.title_en or '제목 없음'
            self.stdout.write(f"✅ {study_title}을 공개로 변경했습니다.")
        except Study.DoesNotExist:
            self.stdout.write("❌ 'A Interview Prep' 스터디를 찾을 수 없습니다.")
        
        # B Interview Prep을 공개로 변경
        try:
            study = Study.objects.get(
                models.Q(title_ko="B Interview Prep") | models.Q(title_en="B Interview Prep")
            )
            study.is_public = True
            study.save()
            study_title = study.title_ko if study.title_ko else study.title_en or '제목 없음'
            self.stdout.write(f"✅ {study_title}을 공개로 변경했습니다.")
        except Study.DoesNotExist:
            self.stdout.write("❌ 'B Interview Prep' 스터디를 찾을 수 없습니다.")
        
        self.stdout.write("")
        self.list_studies() 