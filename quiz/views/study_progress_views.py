import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from datetime import timedelta, datetime
from django.utils import timezone
from collections import defaultdict
from ..models import Study, StudyProgressRecord, ExamResult, StudyTaskProgress
from ..utils.multilingual_utils import get_localized_field, get_user_language, BASE_LANGUAGE

logger = logging.getLogger(__name__)


@api_view(['POST'])
def record_study_progress(request):
    """스터디 진행율을 기록합니다."""
    try:
        study_id = request.data.get('study_id')
        study_ids = request.data.get('study_ids', [])
        page_type = request.data.get('page_type', 'unknown')
        
        # 단일 스터디 ID 처리
        if study_id:
            study_ids = [study_id]
        elif not study_ids:
            return Response({'error': 'study_id 또는 study_ids가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 익명 사용자인 경우 진행율 기록을 건너뜀
        if not request.user.is_authenticated:
            return Response({
                'message': '익명 사용자는 진행율이 기록되지 않습니다.',
                'anonymous_user': True
            }, status=status.HTTP_200_OK)
        
        # 10분 이내에 같은 페이지에서 기록이 있는지 확인
        ten_minutes_ago = timezone.now() - timedelta(minutes=10)
        recent_records = StudyProgressRecord.objects.filter(
            user=request.user,
            study_id__in=study_ids,
            page_type=page_type,
            recorded_at__gte=ten_minutes_ago
        ).values_list('study_id', flat=True)
        
        # 이미 기록된 스터디 ID 제외
        study_ids = [sid for sid in study_ids if sid not in recent_records]
        
        if not study_ids:
            return Response({'success': True, 'message': 'already_recorded'}, status=status.HTTP_200_OK)
        
        # Celery 태스크로 비동기 처리 (응답 시간 단축)
        try:
            from quiz.tasks import record_study_progress_task
            record_study_progress_task.delay(
                user_id=request.user.id,
                study_ids=study_ids,
                page_type=page_type
            )
            logger.info(f"[STUDY_PROGRESS] 진행율 기록 Celery 태스크 전송 완료: user_id={request.user.id}, study_ids={len(study_ids)}개")
            return Response({
                'message': f'{len(study_ids)}개 스터디의 진행율 기록이 시작되었습니다.',
                'processing': True
            }, status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            # Celery 태스크 전송 실패 시 동기 처리로 폴백
            logger.warning(f"[STUDY_PROGRESS] Celery 태스크 전송 실패, 동기 처리로 폴백: {str(e)}")
            # 기존 동기 처리 로직 실행
            return _record_study_progress_sync(request.user, study_ids, page_type)
        
    except Exception as e:
        return Response({'error': f'기록 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _record_study_progress_sync(user, study_ids, page_type):
    """스터디 진행율을 동기적으로 기록하는 헬퍼 함수 (Celery 실패 시 폴백)."""
    records_created = []
    
    for study_id in study_ids:
        try:
            study = Study.objects.get(id=study_id)
            
            # 현재 진행율 계산 (StudyTaskProgress의 실제 진행률 사용)
            tasks = study.tasks.all()
            task_progresses = {}
            total_progress = 0
            
            for task in tasks:
                # StudyTaskSerializer와 동일한 로직으로 진행률 계산
                if task.exam:
                    correct_attempts = task.exam.get_total_correct_questions_for_user(user)
                    total_attempts = task.exam.get_total_attempted_questions_for_user(user)
                    if total_attempts > 0:
                        task_progress = (correct_attempts / total_attempts) * 100
                    else:
                        task_progress = 0
                else:
                    task_progress = 0
                
                task_progresses[task.id] = task_progress
                total_progress += task_progress
            
            overall_progress = total_progress / len(tasks) if tasks else 0
            
            # 기록 생성
            record = StudyProgressRecord.objects.create(
                user=user,
                study=study,
                overall_progress=overall_progress,
                task_progresses=task_progresses,
                page_type=page_type
            )
            
            records_created.append({
                'study_id': study_id,
                'study_title': get_localized_field(study, 'title', study.created_language if hasattr(study, 'created_language') else BASE_LANGUAGE, 'Unknown'),
                'overall_progress': overall_progress,
                'record_id': record.id
            })
            
        except Study.DoesNotExist:
            continue
        except Exception as e:
            logger.error(f"[STUDY_PROGRESS] 스터디 {study_id} 진행율 기록 실패: {str(e)}")
            continue
    
    return Response({
        'message': f'{len(records_created)}개 스터디의 진행율이 기록되었습니다.',
        'records_created': records_created
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def get_study_progress_history(request, study_id):
    """스터디의 진행율 기록을 조회합니다."""
    try:
        study = Study.objects.get(id=study_id)
        
        # 사용자가 해당 스터디에 접근 권한이 있는지 확인
        if not request.user.is_authenticated:
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # 관리자가 아니면 멤버인지 확인
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'admin_role':
            is_member = study.members.filter(user=request.user).exists()
            if not is_member:
                return Response({'error': '접근 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
        
        # 기간 필터링 파라미터 처리
        days = request.GET.get('days')
        if days and days.isdigit():
            days = int(days)
            
            # 지정된 일수만큼 이전부터의 기록만 조회
            start_date = timezone.now() - timedelta(days=days)
            records = StudyProgressRecord.objects.filter(
                user=request.user,
                study=study,
                recorded_at__gte=start_date
            ).order_by('recorded_at')
        else:
            # 전체 기록 조회
            records = StudyProgressRecord.objects.filter(
                user=request.user,
                study=study
            ).order_by('recorded_at')
        
        # 날짜별로 그룹화 (UTC 시간을 그대로 사용, 프론트엔드에서 로컬 시간대로 변환)
        daily_records = defaultdict(list)
        
        for record in records:
            # UTC 시간을 그대로 사용 (프론트엔드에서 로컬 시간대로 변환)
            date_key = record.recorded_at.strftime('%Y-%m-%d')
            daily_records[date_key].append({
                'id': record.id,
                'overall_progress': record.overall_progress,
                'task_progresses': record.task_progresses,
                'recorded_at': record.recorded_at,
                'page_type': record.page_type
            })
        
        # 각 날짜별 최고 진행율 계산
        daily_max_progress = {}
        for date, records_list in daily_records.items():
            max_progress = max([r['overall_progress'] for r in records_list])
            daily_max_progress[date] = max_progress
        
        # 7일 전부터의 기록만 필터링 (진행률 기록 요약용)
        seven_days_ago = timezone.now() - timedelta(days=7)
        filtered_daily_records = {
            date: records_list for date, records_list in daily_records.items()
            if datetime.strptime(date, '%Y-%m-%d').date() >= seven_days_ago.date()
        }
        
        # 진행률 기록 요약 테이블 생성 (7일 제한)
        summary_table = []
        for date, records_list in filtered_daily_records.items():
            # 페이지 타입별 접속 횟수 계산
            page_type_counts = defaultdict(int)
            for record in records_list:
                page_type_counts[record['page_type']] += 1
            
            # 각 페이지 타입별로 행 생성
            for page_type, count in page_type_counts.items():
                summary_table.append({
                    '일자': date,
                    '페이지': page_type,
                    '접속 횟수': count,
                    '최고 진행률': f"{daily_max_progress[date]:.1f}%"
                })
        
        return Response({
            'study_title': study.title_ko or study.title_en or 'Unknown',
            'daily_records': dict(daily_records),
            'daily_max_progress': daily_max_progress,
            'total_records': len(records),
            'summary_table': summary_table,
            'time_series_data': [{
                'date': record.recorded_at.strftime('%Y-%m-%d'),
                'time': record.recorded_at.strftime('%H:%M'),
                'progress': record.overall_progress,
                'attempted_progress': _calculate_attempted_progress(study, request.user),
                'correct_progress': _calculate_correct_progress(study, request.user),
                'page_type': record.page_type,
                'timestamp': record.recorded_at.isoformat()
            } for record in records]
        }, status=status.HTTP_200_OK)
        
    except Study.DoesNotExist:
        return Response({'error': '스터디를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'조회 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _calculate_attempted_progress(study, user):
    """스터디의 시도한 문제 기반 진행률을 계산합니다."""
    try:
        if not user or user.is_anonymous:
            return 0
        
        tasks = study.tasks.all()
        if not tasks:
            return 0
        
        total_attempted = 0
        total_questions = 0
        
        for task in tasks:
            if task.exam:
                attempted_count = task.exam.get_total_attempted_questions_for_user(user)
                question_count = task.exam.total_questions
                total_attempted += attempted_count
                total_questions += question_count
        
        if total_questions > 0:
            return (total_attempted / total_questions) * 100
        else:
            return 0
    except Exception as e:
        logger.error(f"Error calculating attempted progress for study {study.id}: {str(e)}")
        return 0


def _calculate_correct_progress(study, user):
    """스터디의 맞춘 문제 기반 진행률을 계산합니다."""
    try:
        if not user or user.is_anonymous:
            return 0
        
        tasks = study.tasks.all()
        if not tasks:
            return 0
        
        total_correct = 0
        total_questions = 0
        
        for task in tasks:
            if task.exam:
                correct_count = task.exam.get_total_correct_questions_for_user(user)
                question_count = task.exam.total_questions
                total_correct += correct_count
                total_questions += question_count
        
        if total_questions > 0:
            return (total_correct / total_questions) * 100
        else:
            return 0
    except Exception as e:
        logger.error(f"Error calculating correct progress for study {study.id}: {str(e)}")
        return 0





@api_view(['GET'])
def get_study_time_statistics(request, study_id):
    """스터디의 공부시간 통계를 조회합니다."""
    try:
        study = Study.objects.get(id=study_id)
        
        # 사용자가 해당 스터디에 접근 권한이 있는지 확인
        if not request.user.is_authenticated:
            return Response({'error': '로그인이 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # 관리자가 아니면 멤버인지 확인
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'admin_role':
            is_member = study.members.filter(user=request.user).exists()
            if not is_member:
                return Response({'error': '접근 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
        
        # 기간 필터링 파라미터 처리
        days = request.GET.get('days')
        if days and days.isdigit():
            days = int(days)
            
            # 지정된 일수만큼 이전부터의 기록만 조회
            start_date = timezone.now() - timedelta(days=days)
            all_exam_results = ExamResult.objects.filter(
                user=request.user,
                completed_at__gte=start_date
            )
        else:
            # 전체 기록 조회
            all_exam_results = ExamResult.objects.filter(user=request.user)
        
        task_study_times = {}
        
        # 각 Task에 대해 공부시간 계산
        for task in study.tasks.all():
            task_time = 0
            
            # 해당 Task에 연결된 시험이 있는지 확인
            if hasattr(task, 'exam') and task.exam:
                # 해당 시험의 결과들 찾기
                task_exam_results = all_exam_results.filter(exam=task.exam)
                
                for result in task_exam_results:
                    # 시험 결과의 각 문제별 소요시간 합계
                    detail_time = 0
                    try:
                        for detail in result.examresultdetail_set.all():
                            if detail.elapsed_seconds and detail.elapsed_seconds > 0:
                                detail_time += detail.elapsed_seconds
                            
                            # 실제 기록된 시간만 사용 (추정하지 않음)
                            if detail.elapsed_seconds == 0:
                                if detail.question:
                                    question_lang = detail.question.created_language if hasattr(detail.question, 'created_language') else BASE_LANGUAGE
                                    question_title = get_localized_field(detail.question, 'title', question_lang, '제목 없음')
                                else:
                                    question_title = f"Question ID {detail.question_id}"
                                logger.warning(f"경고: 시험 {result.id}의 문제 {question_title}에 elapsed_seconds 데이터가 없습니다.")
                    except Exception as detail_error:
                        logger.warning(f"시험 결과 상세 정보 처리 중 오류: {detail_error}")
                        continue
                    
                    task_time += detail_time
                
                task_lang = task.created_language if hasattr(task, 'created_language') else BASE_LANGUAGE
                task_name = get_localized_field(task, 'name', task_lang, '이름 없음')
                exam_lang = task.exam.created_language if hasattr(task.exam, 'created_language') else BASE_LANGUAGE
                exam_title = get_localized_field(task.exam, 'title', exam_lang, 'Unknown')
                logger.info(f"Task '{task_name}' (Exam: {exam_title}) - 총 공부시간: {task_time}초")
            else:
                task_lang = task.created_language if hasattr(task, 'created_language') else BASE_LANGUAGE
                task_name = get_localized_field(task, 'name', task_lang, '이름 없음')
                logger.info(f"Task '{task_name}' - 연결된 시험이 없음")
            
            task_study_times[task.id] = task_time
        
        # 기간 필터링에 따른 시험 결과 조회 (날짜별 공부시간용)
        if days and isinstance(days, int):
            # 선택된 기간만큼 이전부터의 기록만 조회
            start_date = timezone.now() - timedelta(days=days)
            exam_results = all_exam_results.filter(completed_at__gte=start_date)
        else:
            # 전체 기록 조회 (기본값: 7일)
            seven_days_ago = timezone.now() - timedelta(days=7)
            exam_results = all_exam_results.filter(completed_at__gte=seven_days_ago)
        
        # 날짜별 누적 공부시간 계산
        daily_study_times = {}
        for result in exam_results:
            if result.completed_at:
                date_key = result.completed_at.strftime('%Y-%m-%d')
                if date_key not in daily_study_times:
                    daily_study_times[date_key] = 0
                
                # 해당 시험의 총 소요시간 계산
                exam_time = 0
                try:
                    for detail in result.examresultdetail_set.all():
                        if detail.elapsed_seconds and detail.elapsed_seconds > 0:
                            exam_time += detail.elapsed_seconds
                    
                    # 실제 기록된 시간만 사용 (추정하지 않음)
                    if exam_time == 0:
                        logger.warning(f"경고: 시험 {result.id}에 elapsed_seconds 데이터가 없습니다.")
                except Exception as detail_error:
                    logger.warning(f"시험 결과 상세 정보 처리 중 오류: {detail_error}")
                    continue
                
                daily_study_times[date_key] += exam_time
        
        # 시간을 분 단위로 변환하는 함수
        def seconds_to_minutes(seconds):
            return round(seconds / 60, 1)
        
        # Task별 공부시간 데이터 (StudyTaskProgress의 실제 진행률 사용)
        task_time_data = []
        for task in study.tasks.all():
            study_time = task_study_times.get(task.id, 0)
            
            # StudyTaskSerializer와 동일한 로직으로 진행률 계산
            if task.exam:
                correct_attempts = task.exam.get_total_correct_questions_for_user(request.user)
                total_attempts = task.exam.get_total_attempted_questions_for_user(request.user)
                if total_attempts > 0:
                    actual_progress = (correct_attempts / total_attempts) * 100
                else:
                    actual_progress = 0
            else:
                actual_progress = 0
            
            # Task에 연결된 시험이 있는지 확인
            has_exam = hasattr(task, 'exam') and task.exam is not None
            exam_title = get_localized_field(task.exam, 'title', task.exam.created_language if hasattr(task.exam, 'created_language') else BASE_LANGUAGE, 'Unknown') if has_exam else None
            
            # 현재 사용자 언어에 맞는 Task 이름 설정
            user_language = get_user_language(request)
            task_lang = task.created_language if hasattr(task, 'created_language') else BASE_LANGUAGE
            task_name = get_localized_field(task, 'name', user_language, f'Task {task.seq}')
            
            task_time_data.append({
                'task_name': task_name,
                'study_time_minutes': seconds_to_minutes(study_time),
                'study_time_seconds': study_time,
                'progress': actual_progress,
                'has_exam': has_exam,
                'exam_title': exam_title,
                'exam_id': task.exam.id if has_exam else None
            })
        
        # 공부시간이 있는 Task만 필터링 (선택사항)
        active_task_data = [task for task in task_time_data if task['study_time_seconds'] > 0]
        inactive_task_data = [task for task in task_time_data if task['study_time_seconds'] == 0]
        
        logger.info(f"활성 Task (공부시간 있음): {len(active_task_data)}개")
        logger.info(f"비활성 Task (공부시간 없음): {len(inactive_task_data)}개")
        
        # 날짜별 누적 공부시간 데이터 (시간역순으로 정렬)
        daily_time_data = []
        for date, total_seconds in sorted(daily_study_times.items(), reverse=True):
            daily_time_data.append({
                'date': date,
                'study_time_minutes': seconds_to_minutes(total_seconds),
                'study_time_seconds': total_seconds
            })
        
        return Response({
            'task_study_times': task_time_data,
            'daily_study_times': daily_time_data,
            'total_study_time_minutes': seconds_to_minutes(sum(daily_study_times.values())),
            'total_study_time_seconds': sum(daily_study_times.values()),
            'summary': {
                'total_tasks': len(task_time_data),
                'active_tasks': len(active_task_data),
                'inactive_tasks': len(inactive_task_data),
                'has_study_time': sum(daily_study_times.values()) > 0,
                'last_study_date': max(daily_study_times.keys()) if daily_study_times else None
            }
        }, status=status.HTTP_200_OK)
        
    except Study.DoesNotExist:
        return Response({'error': '스터디를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"공부시간 통계 조회 중 오류 발생: {str(e)}", exc_info=True)
        return Response({'error': f'공부시간 통계 조회 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 