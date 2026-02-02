from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from quiz.models import Question, Exam, ExamResultDetail, ExamResult

User = get_user_model()

class Command(BaseCommand):
    help = 'Check user question statistics for specific questions'

    def handle(self, *args, **options):
        try:
            # doohee323 사용자 찾기
            user = User.objects.get(username='doohee323')
            self.stdout.write(f"사용자: {user.username}")
            
            # Course Schedule과 Task Scheduler 문제 찾기
            questions = Question.objects.filter(
                models.Q(title_ko__in=['Course Schedule', 'Task Scheduler']) | 
                models.Q(title_en__in=['Course Schedule', 'Task Scheduler'])
            )
            
            for question in questions:
                question_title = question.title_ko if question.title_ko else question.title_en or '제목 없음'
                self.stdout.write(f"\n문제: {question_title} (ID: {question.id}, CSV ID: {question.csv_id})")
                
                # 해당 문제의 시험 결과 상세 조회
                result_details = ExamResultDetail.objects.filter(
                    question=question,
                    result__user=user
                )
                
                total_attempts = result_details.count()
                wrong_count = result_details.filter(is_correct=False).count()
                
                self.stdout.write(f"  총 시도 횟수: {total_attempts}")
                self.stdout.write(f"  틀린 횟수: {wrong_count}")
                
                if total_attempts > 0:
                    wrong_rate = wrong_count / total_attempts
                    score = total_attempts * wrong_rate
                    self.stdout.write(f"  틀린 비율: {wrong_rate:.2f}")
                    self.stdout.write(f"  점수: {score:.2f}")
                
                # 해당 문제가 포함된 시험들
                exams = Exam.objects.filter(examquestion__question=question)
                for exam in exams:
                    exam_title = exam.title_ko if exam.title_ko else exam.title_en or '제목 없음'
                    self.stdout.write(f"  시험: {exam_title}")
                
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('doohee323 사용자를 찾을 수 없습니다.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'오류 발생: {str(e)}')) 