from django.core.management.base import BaseCommand
from quiz.models import Question, Exam, ExamQuestion
from django.db import transaction


class Command(BaseCommand):
    help = '기존 문제들의 group_id를 원본 시험 제목으로 설정'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제 변경사항을 적용하지 않고 시뮬레이션만 실행',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN 모드 - 실제 변경사항이 적용되지 않습니다.'))
        
        # group_id가 비어있는 문제들 찾기
        questions_without_group_id = Question.objects.filter(
            group_id__isnull=True
        ) | Question.objects.filter(
            group_id=''
        )
        
        self.stdout.write(f'group_id가 설정되지 않은 문제 수: {questions_without_group_id.count()}')
        
        updated_count = 0
        
        for question in questions_without_group_id:
            # 해당 문제가 속한 시험들 중에서 원본 시험 찾기
            exam_questions = ExamQuestion.objects.filter(question=question)
            
            original_exam = None
            
            # 1. 원본 시험(is_original=True)을 우선 찾기
            for eq in exam_questions:
                if eq.exam.is_original:
                    original_exam = eq.exam
                    break
            
            # 2. 원본 시험이 없으면 첫 번째 시험 사용
            if not original_exam and exam_questions.exists():
                original_exam = exam_questions.first().exam
            
            if original_exam:
                if not dry_run:
                    question.group_id = original_exam.title
                    question.save()
                
                question_title = question.title_ko if question.title_ko else question.title_en or '제목 없음'
                exam_title = original_exam.title_ko if original_exam.title_ko else original_exam.title_en or '제목 없음'
                self.stdout.write(
                    f'문제 "{question_title[:50]}..." -> group_id: "{exam_title}"'
                )
                updated_count += 1
            else:
                question_title = question.title_ko if question.title_ko else question.title_en or '제목 없음'
                self.stdout.write(
                    self.style.WARNING(f'문제 "{question_title[:50]}..." -> 원본 시험을 찾을 수 없음')
                )
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'DRY RUN 완료: {updated_count}개 문제의 group_id가 설정될 예정')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'완료: {updated_count}개 문제의 group_id가 설정됨')
            ) 