from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from quiz.models import Study, Member, StudyTaskProgress, StudyProgressRecord, ExamResult, ExamResultDetail, IgnoredQuestion

User = get_user_model()

class Command(BaseCommand):
    help = 'admin 계정의 study 이력을 doohee323 계정으로 복사합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source-username',
            type=str,
            default='admin',
            help='복사할 소스 사용자명 (기본값: admin)'
        )
        parser.add_argument(
            '--target-username',
            type=str,
            default='doohee323',
            help='복사할 대상 사용자명 (기본값: doohee323)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제 복사하지 않고 미리보기만 실행'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='기존 데이터를 무시하고 강제로 덮어쓰기'
        )

    def handle(self, *args, **options):
        source_username = options['source_username']
        target_username = options['target_username']
        dry_run = options['dry_run']
        force = options['force']

        self.stdout.write(f"소스 사용자: {source_username}")
        self.stdout.write(f"대상 사용자: {target_username}")
        self.stdout.write(f"드라이 런: {dry_run}")
        self.stdout.write(f"강제 덮어쓰기: {force}")

        # 사용자 확인
        try:
            source_user = User.objects.get(username=source_username)
            self.stdout.write(f"✓ 소스 사용자 '{source_username}' 찾음 (ID: {source_user.id})")
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ 소스 사용자 '{source_username}'를 찾을 수 없습니다."))
            return

        try:
            target_user = User.objects.get(username=target_username)
            self.stdout.write(f"✓ 대상 사용자 '{target_username}' 찾음 (ID: {target_user.id})")
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ 대상 사용자 '{target_username}'를 찾을 수 없습니다."))
            return

        if source_user == target_user:
            self.stdout.write(self.style.ERROR("❌ 소스와 대상 사용자가 같습니다."))
            return

        # 복사할 데이터 분석
        self.analyze_data(source_user, target_user)

        if dry_run:
            self.stdout.write(self.style.WARNING("드라이 런 모드: 실제 복사는 수행되지 않습니다."))
            return

        # 사용자 확인
        if force:
            confirm = input(f"\n⚠️  경고: {target_username}의 기존 데이터를 모두 삭제하고 {source_username}의 데이터로 덮어쓰겠습니다. 계속하시겠습니까? (yes/no): ")
        else:
            confirm = input(f"\n정말로 {source_username}의 study 이력을 {target_username}로 복사하시겠습니까? (yes/no): ")
        
        if confirm.lower() != 'yes':
            self.stdout.write("복사가 취소되었습니다.")
            return

        # 실제 복사 실행
        self.copy_study_history(source_user, target_user, force)

    def analyze_data(self, source_user, target_user):
        """복사할 데이터를 분석하고 미리보기를 제공합니다."""
        self.stdout.write("\n" + "="*50)
        self.stdout.write("복사할 데이터 분석")
        self.stdout.write("="*50)

        # 1. Study 생성자로 생성된 스터디들
        studies_created = Study.objects.filter(created_by=source_user)
        self.stdout.write(f"✓ 생성한 스터디: {studies_created.count()}개")
        for study in studies_created:
            self.stdout.write(f"  - {study.title} (ID: {study.id})")

        # 2. 멤버로 참여한 스터디들
        memberships = Member.objects.filter(user=source_user)
        self.stdout.write(f"✓ 멤버로 참여한 스터디: {memberships.count()}개")
        for member in memberships:
            self.stdout.write(f"  - {member.study.title} (역할: {member.get_role_display()})")

        # 3. StudyTaskProgress
        task_progresses = StudyTaskProgress.objects.filter(user=source_user)
        self.stdout.write(f"✓ 스터디 태스크 진행률: {task_progresses.count()}개")

        # 4. StudyProgressRecord
        progress_records = StudyProgressRecord.objects.filter(user=source_user)
        self.stdout.write(f"✓ 스터디 진행률 기록: {progress_records.count()}개")

        # 5. ExamResult
        exam_results = ExamResult.objects.filter(user=source_user)
        self.stdout.write(f"✓ 시험 결과: {exam_results.count()}개")

        # 6. ExamResultDetail
        exam_result_details = ExamResultDetail.objects.filter(result__user=source_user)
        self.stdout.write(f"✓ 시험 결과 상세: {exam_result_details.count()}개")

        # 7. IgnoredQuestion
        ignored_questions = IgnoredQuestion.objects.filter(user=source_user)
        self.stdout.write(f"✓ 무시한 문제: {ignored_questions.count()}개")

        # 기존 데이터 확인
        self.stdout.write("\n" + "="*50)
        self.stdout.write("대상 사용자의 기존 데이터 확인")
        self.stdout.write("="*50)

        existing_memberships = Member.objects.filter(user=target_user)
        existing_task_progresses = StudyTaskProgress.objects.filter(user=target_user)
        existing_progress_records = StudyProgressRecord.objects.filter(user=target_user)
        existing_exam_results = ExamResult.objects.filter(user=target_user)
        existing_ignored_questions = IgnoredQuestion.objects.filter(user=target_user)

        self.stdout.write(f"✓ 기존 멤버십: {existing_memberships.count()}개")
        self.stdout.write(f"✓ 기존 태스크 진행률: {existing_task_progresses.count()}개")
        self.stdout.write(f"✓ 기존 진행률 기록: {existing_progress_records.count()}개")
        self.stdout.write(f"✓ 기존 시험 결과: {existing_exam_results.count()}개")
        self.stdout.write(f"✓ 기존 무시한 문제: {existing_ignored_questions.count()}개")

    @transaction.atomic
    def copy_study_history(self, source_user, target_user, force=False):
        """실제로 study 이력을 복사합니다."""
        self.stdout.write("\n" + "="*50)
        self.stdout.write("Study 이력 복사 시작")
        self.stdout.write("="*50)

        copied_count = 0

        # 강제 모드인 경우 기존 데이터 삭제
        if force:
            self.stdout.write("🗑️  기존 데이터 삭제 중...")
            
            # 기존 데이터 삭제
            deleted_memberships = Member.objects.filter(user=target_user).delete()
            deleted_task_progresses = StudyTaskProgress.objects.filter(user=target_user).delete()
            deleted_progress_records = StudyProgressRecord.objects.filter(user=target_user).delete()
            deleted_exam_results = ExamResult.objects.filter(user=target_user).delete()
            deleted_ignored_questions = IgnoredQuestion.objects.filter(user=target_user).delete()
            
            self.stdout.write(f"✓ 삭제된 멤버십: {deleted_memberships[0]}개")
            self.stdout.write(f"✓ 삭제된 태스크 진행률: {deleted_task_progresses[0]}개")
            self.stdout.write(f"✓ 삭제된 진행률 기록: {deleted_progress_records[0]}개")
            self.stdout.write(f"✓ 삭제된 시험 결과: {deleted_exam_results[0]}개")
            self.stdout.write(f"✓ 삭제된 무시한 문제: {deleted_ignored_questions[0]}개")

        # 1. Study 생성자로 생성된 스터디들 복사 (created_by만 변경)
        studies_created = Study.objects.filter(created_by=source_user)
        for study in studies_created:
            study.created_by = target_user
            study.save()
            self.stdout.write(f"✓ 스터디 '{study.title}'의 생성자를 {target_user.username}로 변경")
            copied_count += 1

        # 2. 멤버십 복사
        memberships = Member.objects.filter(user=source_user)
        for member in memberships:
            # 새 멤버 생성 (force 모드에서는 중복 체크 없음)
            new_member = Member.objects.create(
                study=member.study,
                user=target_user,
                name=member.name,
                email=member.email,
                member_id=member.member_id,
                affiliation=member.affiliation,
                location=member.location,
                role=member.role,
                is_active=member.is_active
            )
            self.stdout.write(f"✓ 스터디 '{member.study.title}'에 멤버로 추가 (역할: {member.get_role_display()})")
            copied_count += 1

        # 3. StudyTaskProgress 복사
        task_progresses = StudyTaskProgress.objects.filter(user=source_user)
        for progress in task_progresses:
            # 새 진행률 생성 (force 모드에서는 중복 체크 없음)
            StudyTaskProgress.objects.create(
                user=target_user,
                study_task=progress.study_task,
                progress=progress.progress
            )
            self.stdout.write(f"✓ 스터디 태스크 '{progress.study_task.name_ko or progress.study_task.name_en or '이름 없음'}'의 진행률 복사 ({progress.progress}%)")
            copied_count += 1

        # 4. StudyProgressRecord 복사
        progress_records = StudyProgressRecord.objects.filter(user=source_user)
        for record in progress_records:
            StudyProgressRecord.objects.create(
                user=target_user,
                study=record.study,
                overall_progress=record.overall_progress,
                task_progresses=record.task_progresses,
                page_type=record.page_type
            )
            self.stdout.write(f"✓ 스터디 '{record.study.title}'의 진행률 기록 복사 ({record.overall_progress}%)")
            copied_count += 1

        # 5. ExamResult 복사
        exam_results = ExamResult.objects.filter(user=source_user)
        for result in exam_results:
            # 새 시험 결과 생성 (force 모드에서는 중복 체크 없음)
            new_result = ExamResult.objects.create(
                exam=result.exam,
                user=target_user,
                score=result.score,
                total_score=result.total_score,
                correct_count=result.correct_count,
                wrong_count=result.wrong_count,
                completed_at=result.completed_at,
                elapsed_seconds=result.elapsed_seconds
            )
            
            # ExamResultDetail도 함께 복사
            result_details = ExamResultDetail.objects.filter(result=result)
            for detail in result_details:
                ExamResultDetail.objects.create(
                    result=new_result,
                    question=detail.question,
                    user_answer=detail.user_answer,
                    is_correct=detail.is_correct,
                    elapsed_seconds=detail.elapsed_seconds
                )
            
            self.stdout.write(f"✓ 시험 '{result.exam.title}'의 결과 복사 (점수: {result.score}/{result.total_score})")
            copied_count += 1

        # 6. IgnoredQuestion 복사
        ignored_questions = IgnoredQuestion.objects.filter(user=source_user)
        for ignored in ignored_questions:
            IgnoredQuestion.objects.create(
                user=target_user,
                question=ignored.question
            )
            question_title = ignored.question.title_ko if ignored.question.title_ko else ignored.question.title_en or '제목 없음'
            self.stdout.write(f"✓ 문제 '{question_title}'를 무시 목록에 추가")
            copied_count += 1

        self.stdout.write("\n" + "="*50)
        self.stdout.write("복사 완료!")
        self.stdout.write("="*50)
        self.stdout.write(f"총 복사된 항목: {copied_count}개")
        self.stdout.write(f"소스 사용자 '{source_user.username}'의 study 이력이 '{target_user.username}'로 성공적으로 복사되었습니다.") 