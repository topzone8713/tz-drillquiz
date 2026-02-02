from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from quiz.models import Study, StudyTaskProgress, ExamResult
from django.db.models import Q

User = get_user_model()

class Command(BaseCommand):
    help = '사용자의 StudyTaskProgress 상태를 확인합니다.'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='확인할 사용자명')
        parser.add_argument('--study-id', type=int, help='확인할 스터디 ID')

    def handle(self, *args, **options):
        username = options.get('username')
        study_id = options.get('study_id')

        if username:
            users = User.objects.filter(username=username)
        else:
            users = User.objects.filter(is_active=True)[:5]  # 최근 5명만

        for user in users:
            self.stdout.write(f"\n=== 사용자: {user.username} ===")
            
            if study_id:
                studies = Study.objects.filter(id=study_id)
            else:
                studies = Study.objects.filter(
                    Q(members__user=user, members__is_active=True) |
                    Q(members__name=user.username, members__is_active=True) |
                    Q(created_by=user)
                ).distinct()

            for study in studies:
                self.stdout.write(f"\n스터디: {study.title_ko or study.title_en or 'Unknown'} (ID: {study.id})")
                
                for task in study.tasks.all():
                    # StudyTaskProgress 확인
                    progress_obj = StudyTaskProgress.objects.filter(user=user, study_task=task).first()
                    
                    if progress_obj:
                        self.stdout.write(f"  Task {task.seq}: {task.name_ko or task.name_en}")
                        self.stdout.write(f"    StudyTaskProgress: {progress_obj.progress:.1f}%")
                    else:
                        self.stdout.write(f"  Task {task.seq}: {task.name_ko or task.name_en}")
                        self.stdout.write(f"    StudyTaskProgress: 기록 없음")
                    
                    # 시험 결과 확인
                    if task.exam:
                        exam_results = ExamResult.objects.filter(user=user, exam=task.exam)
                        if exam_results.exists():
                            latest_result = exam_results.latest('completed_at')
                            self.stdout.write(f"    최근 시험 결과: {latest_result.correct_count}/{latest_result.total_score}")
                        else:
                            self.stdout.write(f"    시험 결과: 없음")
                    else:
                        self.stdout.write(f"    연결된 시험: 없음")

        self.stdout.write(self.style.SUCCESS('\n진행률 확인 완료'))
