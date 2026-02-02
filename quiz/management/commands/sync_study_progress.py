from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from quiz.models import Study, StudyTask, StudyTaskProgress, StudyProgressRecord, ExamResult, Exam
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '기존 시험 결과를 기반으로 StudyTaskProgress와 StudyProgressRecord를 동기화합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--study-id',
            type=int,
            help='특정 스터디 ID만 동기화 (없으면 모든 스터디)'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='특정 사용자 ID만 동기화 (없으면 모든 사용자)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제 변경하지 않고 확인만 수행'
        )

    def handle(self, *args, **options):
        study_id = options.get('study_id')
        user_id = options.get('user_id')
        dry_run = options.get('dry_run')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN 모드 - 실제 변경하지 않습니다.'))
        
        # 동기화할 스터디 선택
        if study_id:
            studies = Study.objects.filter(id=study_id)
        else:
            studies = Study.objects.all()
        
        # 동기화할 사용자 선택
        if user_id:
            users = User.objects.filter(id=user_id)
        else:
            users = User.objects.filter(is_active=True)
        
        self.stdout.write(f'동기화 시작: {studies.count()}개 스터디, {users.count()}명 사용자')
        
        total_updated = 0
        
        for study in studies:
            self.stdout.write(f'\n스터디: {study.title} (ID: {study.id})')
            
            for user in users:
                try:
                    updated_count = self.sync_user_study_progress(study, user, dry_run)
                    total_updated += updated_count
                    
                    if updated_count > 0:
                        self.stdout.write(f'  사용자 {user.username} (ID: {user.id}): {updated_count}개 Task 동기화')
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  사용자 {user.username} 동기화 실패: {str(e)}')
                    )
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'\nDRY RUN 완료: 총 {total_updated}개 Task가 동기화될 예정입니다.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\n동기화 완료: 총 {total_updated}개 Task가 동기화되었습니다.')
            )

    def sync_user_study_progress(self, study, user, dry_run=False):
        """사용자의 특정 스터디 진행률을 동기화합니다."""
        updated_count = 0
        
        # 해당 스터디의 모든 Task에 대해 진행률 계산
        for study_task in study.tasks.all():
            if not study_task.exam:
                continue  # 시험이 연결되지 않은 Task는 건너뛰기
            
            try:
                # 해당 시험의 사용자 결과 찾기
                exam_results = ExamResult.objects.filter(
                    exam=study_task.exam,
                    user=user
                )
                
                if not exam_results.exists():
                    continue  # 시험 결과가 없으면 건너뛰기
                
                # 가장 최근 결과 사용
                latest_result = exam_results.order_by('-completed_at').first()
                
                # 진행률 계산 (정답률 기반)
                if latest_result.total_score > 0:
                    progress_percentage = (latest_result.correct_count / latest_result.total_score) * 100
                else:
                    progress_percentage = 0
                
                # StudyTaskProgress 업데이트 또는 생성
                if not dry_run:
                    progress_obj, created = StudyTaskProgress.objects.get_or_create(
                        user=user,
                        study_task=study_task,
                        defaults={'progress': progress_percentage}
                    )
                    
                    if not created and progress_percentage > progress_obj.progress:
                        progress_obj.progress = progress_percentage
                        progress_obj.save()
                
                updated_count += 1
                
            except Exception as e:
                logger.error(f"Task {study_task.name_ko or study_task.name_en or '이름 없음'} 동기화 실패: {str(e)}")
                continue
        
        # StudyProgressRecord 생성 (기존 기록이 없거나 최신 데이터로 업데이트)
        if updated_count > 0 and not dry_run:
            try:
                # 현재 사용자의 모든 Task 진행률 수집
                task_progresses = {}
                overall_progress = 0
                total_tasks = 0
                
                for study_task in study.tasks.all():
                    try:
                        progress_obj = StudyTaskProgress.objects.get(user=user, study_task=study_task)
                        task_progress = progress_obj.progress
                    except StudyTaskProgress.DoesNotExist:
                        task_progress = 0
                    
                    task_progresses[str(study_task.id)] = task_progress
                    overall_progress += task_progress
                    total_tasks += 1
                
                # 전체 진행률 계산 (평균)
                if total_tasks > 0:
                    overall_progress = overall_progress / total_tasks
                
                # 기존 기록이 있으면 업데이트, 없으면 생성
                existing_record = StudyProgressRecord.objects.filter(
                    user=user,
                    study=study
                ).order_by('-recorded_at').first()
                
                if existing_record:
                    # 기존 기록 업데이트
                    existing_record.overall_progress = overall_progress
                    existing_record.task_progresses = task_progresses
                    existing_record.save()
                else:
                    # 새 기록 생성
                    StudyProgressRecord.objects.create(
                        user=user,
                        study=study,
                        overall_progress=overall_progress,
                        task_progresses=task_progresses,
                        page_type='sync-command'
                    )
                
            except Exception as e:
                logger.error(f"StudyProgressRecord 동기화 실패: {str(e)}")
        
        return updated_count
