from django.core.management.base import BaseCommand
from quiz.models import Question


class Command(BaseCommand):
    help = 'URL이 "nan"인 문제들을 모두 삭제합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제 삭제하지 않고 삭제될 문제들을 미리보기만 합니다.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # URL이 'nan'인 문제들 찾기
        nan_url_questions = Question.objects.filter(url='nan')
        
        if dry_run:
            self.stdout.write(f'URL이 "nan"인 문제 {nan_url_questions.count()}개를 찾았습니다:')
            for question in nan_url_questions:
                question_title = question.title_ko if question.title_ko else question.title_en or '제목 없음'
                self.stdout.write(f'  - ID: {question.id}, 제목: {question_title}')
            self.stdout.write(self.style.WARNING('--dry-run 옵션으로 실제 삭제하지 않았습니다.'))
        else:
            count = nan_url_questions.count()
            if count > 0:
                self.stdout.write(f'URL이 "nan"인 문제 {count}개를 삭제합니다...')
                
                # 삭제할 문제들의 정보 출력
                for question in nan_url_questions:
                    question_title = question.title_ko if question.title_ko else question.title_en or '제목 없음'
                    self.stdout.write(f'  - 삭제: ID: {question.id}, 제목: {question_title}')
                
                # 실제 삭제
                nan_url_questions.delete()
                
                self.stdout.write(
                    self.style.SUCCESS(f'성공적으로 {count}개의 문제를 삭제했습니다.')
                )
            else:
                self.stdout.write(self.style.SUCCESS('URL이 "nan"인 문제가 없습니다.')) 