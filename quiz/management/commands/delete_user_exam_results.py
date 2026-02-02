from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from quiz.models import Exam, ExamResult, ExamResultDetail

class Command(BaseCommand):
    help = '특정 사용자의 특정 시험 결과를 삭제합니다.'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='사용자명')
        parser.add_argument('exam_title', type=str, help='시험 제목')

    def handle(self, *args, **options):
        username = options['username']
        exam_title = options['exam_title']
        
        try:
            # 사용자 찾기
            user = User.objects.get(username=username)
            self.stdout.write(f"사용자 '{username}'을 찾았습니다.")
            
            # 시험 찾기
            exam = Exam.objects.get(title=exam_title)
            self.stdout.write(f"시험 '{exam_title}'을 찾았습니다.")
            
            # 해당 사용자의 해당 시험 결과 찾기
            results = ExamResult.objects.filter(user=user, exam=exam)
            
            if not results.exists():
                self.stdout.write(
                    self.style.WARNING(f"사용자 '{username}'의 시험 '{exam_title}' 결과가 없습니다.")
                )
                return
            
            # 결과 삭제
            result_count = results.count()
            for result in results:
                # 관련된 ExamResultDetail도 함께 삭제
                ExamResultDetail.objects.filter(result=result).delete()
                result.delete()
            
            self.stdout.write(
                self.style.SUCCESS(f"사용자 '{username}'의 시험 '{exam_title}' 결과 {result_count}개를 삭제했습니다.")
            )
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"사용자 '{username}'을 찾을 수 없습니다.")
            )
        except Exam.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"시험 '{exam_title}'을 찾을 수 없습니다.")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"오류가 발생했습니다: {str(e)}")
            ) 