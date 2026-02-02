from django.core.management.base import BaseCommand
from django.db import models
from quiz.models import Question, Exam
import pandas as pd
import os


class Command(BaseCommand):
    help = 'neetcode_150.xlsx 파일에서 그룹ID를 읽어와서 데이터베이스를 업데이트합니다'

    def handle(self, *args, **options):
        # neetcode_150 시험 찾기
        try:
            exam = Exam.objects.get(title='neetcode_150')
        except Exam.DoesNotExist:
            self.stdout.write(self.style.ERROR('neetcode_150 시험을 찾을 수 없습니다.'))
            return

        # Excel 파일 읽기
        file_path = os.path.join('media', 'data', 'neetcode_150.xlsx')
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'파일을 찾을 수 없습니다: {file_path}'))
            return

        try:
            df = pd.read_excel(file_path)
            self.stdout.write(f'Excel 파일 읽기 완료: {len(df)}행')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Excel 파일 읽기 실패: {str(e)}'))
            return

        # 그룹ID 컬럼 확인
        if '그룹ID' not in df.columns:
            self.stdout.write(self.style.ERROR('그룹ID 컬럼이 없습니다.'))
            return

        # 시험에 속한 문제들 가져오기
        exam_questions = Question.objects.filter(examquestion__exam=exam)
        self.stdout.write(f'시험 문제 수: {exam_questions.count()}개')

        updated_count = 0
        not_found_count = 0

        for index, row in df.iterrows():
            try:
                title = str(row['제목']).strip()
                group_id = str(row['그룹ID']).strip() if pd.notna(row['그룹ID']) else None

                # 제목으로 문제 찾기 (한국어와 영어 제목 모두에서 검색)
                questions = Question.objects.filter(
                    models.Q(title_ko=title) | models.Q(title_en=title),
                    examquestion__exam=exam
                )
                
                if questions.exists():
                    for question in questions:
                        old_group_id = question.group_id
                        question.group_id = group_id
                        question.save()
                        updated_count += 1
                        self.stdout.write(f'✅ 업데이트: {title} - "{old_group_id}" -> "{group_id}"')
                else:
                    not_found_count += 1
                    self.stdout.write(f'⚠️  찾을 수 없음: {title}')

            except Exception as e:
                self.stdout.write(f'❌ 오류 (행 {index + 2}): {str(e)}')

        self.stdout.write(
            self.style.SUCCESS(
                f'\n업데이트 완료:\n'
                f'- 업데이트된 문제: {updated_count}개\n'
                f'- 찾을 수 없는 문제: {not_found_count}개\n'
                f'- 총 처리된 행: {len(df)}개'
            )
        ) 