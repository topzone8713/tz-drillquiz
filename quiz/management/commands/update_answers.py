from django.core.management.base import BaseCommand
from quiz.models import Question


class Command(BaseCommand):
    help = '모든 문제의 정답을 Y로 업데이트합니다.'

    def handle(self, *args, **options):
        # 모든 문제의 정답을 'Y'로 업데이트
        updated_count = Question.objects.update(answer='Y')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'성공적으로 {updated_count}개의 문제 정답을 Y로 업데이트했습니다.'
            )
        ) 