from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from quiz.models import Study, StudyTask, StudyTaskProgress, StudyProgressRecord
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = '새로운 진행률 기록을 생성하여 수정된 진행률을 확인합니다'

    def handle(self, *args, **options):
        self.stdout.write("=== 새로운 진행률 기록 생성 ===")
        
        # 사용자 정보
        try:
            user = User.objects.get(username='doohee323')
            self.stdout.write(f"사용자: {user.username}")
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("사용자를 찾을 수 없습니다."))
            return
        
        # 스터디 정보
        try:
            study = Study.objects.get(id=6)
            self.stdout.write(f"스터디: {study.title}")
        except Study.DoesNotExist:
            self.stdout.write(self.style.ERROR("스터디를 찾을 수 없습니다."))
            return
        
        # 현재 StudyTaskProgress 확인
        self.stdout.write(f"\n=== 현재 StudyTaskProgress ===")
        progress_records = StudyTaskProgress.objects.filter(user=user, study_task__study=study)
        
        task_progresses = {}
        total_progress = 0
        
        for record in progress_records:
            self.stdout.write(f"- {record.study_task.name_ko or record.study_task.name_en or '이름 없음'}: {record.progress}%")
            task_progresses[record.study_task.id] = record.progress
            total_progress += record.progress
        
        # 전체 진행률 계산
        if progress_records.count() > 0:
            overall_progress = total_progress / progress_records.count()
            self.stdout.write(f"\n=== 전체 진행률 계산 ===")
            self.stdout.write(f"총 Task 수: {progress_records.count()}")
            self.stdout.write(f"진행률 합계: {total_progress}%")
            self.stdout.write(f"평균 진행률: {overall_progress}%")
        else:
            self.stdout.write(self.style.WARNING("진행률 기록이 없습니다."))
            return
        
        # 새로운 StudyProgressRecord 생성
        self.stdout.write(f"\n=== 새로운 StudyProgressRecord 생성 ===")
        try:
            record = StudyProgressRecord.objects.create(
                user=user,
                study=study,
                overall_progress=overall_progress,
                task_progresses=task_progresses,
                page_type='study-progress-dashboard'
            )
            self.stdout.write(self.style.SUCCESS(f"✅ 새로운 기록 생성 완료!"))
            self.stdout.write(f"- 기록 ID: {record.id}")
            self.stdout.write(f"- 전체 진행률: {record.overall_progress}%")
            self.stdout.write(f"- Task별 진행률: {record.task_progresses}")
            self.stdout.write(f"- 기록 시간: {record.recorded_at}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ 기록 생성 실패: {e}"))
        
        # 최신 기록 확인
        self.stdout.write(f"\n=== 최신 기록 확인 ===")
        latest_records = StudyProgressRecord.objects.filter(
            user=user, 
            study=study
        ).order_by('-recorded_at')[:5]
        
        for record in latest_records:
            self.stdout.write(f"- {record.recorded_at}: {record.overall_progress}%") 