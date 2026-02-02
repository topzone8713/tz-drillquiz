from django.core.management.base import BaseCommand
from quiz.models import Question


class Command(BaseCommand):
    help = '잘못된 그룹ID 값들을 수정합니다'

    def handle(self, *args, **options):
        # "None" 문자열로 저장된 그룹ID를 None으로 변경
        questions_with_none_string = Question.objects.filter(group_id="None")
        count_none_string = questions_with_none_string.count()
        questions_with_none_string.update(group_id=None)
        
        # 빈 문자열로 저장된 그룹ID를 None으로 변경
        questions_with_empty_string = Question.objects.filter(group_id="")
        count_empty_string = questions_with_empty_string.count()
        questions_with_empty_string.update(group_id=None)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'그룹ID 수정 완료:\n'
                f'- "None" 문자열을 None으로 변경: {count_none_string}개\n'
                f'- 빈 문자열을 None으로 변경: {count_empty_string}개\n'
                f'- 총 수정된 문제 수: {count_none_string + count_empty_string}개'
            )
        ) 