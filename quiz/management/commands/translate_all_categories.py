#!/usr/bin/env python3
"""
모든 카테고리의 다국어 번역을 채워 넣는 Django 관리 명령어

사용법:
    python manage.py translate_all_categories

이 명령어는 모든 TagCategory 레코드를 조회하여:
1. name_en이 있지만 다른 언어(ko, es, zh)가 비어있는 경우 번역 수행
2. 번역 완료 후 완성도 필드 자동 업데이트
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from quiz.models import TagCategory
from quiz.utils.multilingual_utils import (
    batch_translate_texts,
    LANGUAGE_KO,
    LANGUAGE_EN,
    LANGUAGE_ES,
    LANGUAGE_ZH,
    LANGUAGE_JA,
)
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = '모든 카테고리의 다국어 번역을 채워 넣습니다 (영어 → 다른 언어)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='이미 번역이 있어도 다시 번역합니다',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제로 저장하지 않고 번역 결과만 확인합니다',
        )

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.SUCCESS('=== 카테고리 다국어 번역 시작 ==='))
        
        # 모든 카테고리 조회
        categories = TagCategory.objects.all().order_by('id')
        total_count = categories.count()
        
        self.stdout.write(f'총 {total_count}개의 카테고리를 처리합니다.')
        
        translated_count = 0
        skipped_count = 0
        error_count = 0
        
        for category in categories:
            try:
                result = self.translate_category(category, force=force, dry_run=dry_run)
                if result['translated']:
                    translated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ [{category.id}] {category.name_en or category.name_ko}: '
                            f'{result["message"]}'
                        )
                    )
                elif result['skipped']:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'⊘ [{category.id}] {category.name_en or category.name_ko}: '
                            f'{result["message"]}'
                        )
                    )
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ [{category.id}] {category.name_en or category.name_ko}: '
                        f'오류 발생 - {str(e)}'
                    )
                )
                logger.error(f"카테고리 번역 중 오류: category_id={category.id}, error={str(e)}")
        
        # 결과 요약
        self.stdout.write(self.style.SUCCESS('\n=== 번역 완료 ==='))
        self.stdout.write(f'총 처리: {total_count}개')
        self.stdout.write(self.style.SUCCESS(f'번역 완료: {translated_count}개'))
        self.stdout.write(self.style.WARNING(f'건너뜀: {skipped_count}개'))
        self.stdout.write(self.style.ERROR(f'오류: {error_count}개'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠ DRY RUN 모드: 실제로 저장하지 않았습니다.'))

    def translate_category(self, category, force=False, dry_run=False):
        """
        개별 카테고리의 다국어 번역 처리
        
        Args:
            category: TagCategory 인스턴스
            force: 이미 번역이 있어도 다시 번역할지 여부
            dry_run: 실제로 저장하지 않고 결과만 반환할지 여부
        
        Returns:
            dict: {'translated': bool, 'skipped': bool, 'message': str}
        """
        # 영어 이름 확인
        english_name = category.name_en
        if not english_name or not english_name.strip():
            # 영어가 없으면 한국어를 영어로 번역
            korean_name = category.name_ko
            if korean_name and korean_name.strip():
                english_name = korean_name
                # 한국어를 영어로 번역
                try:
                    translated_names = batch_translate_texts([korean_name], LANGUAGE_KO, LANGUAGE_EN)
                    if translated_names and translated_names[0]:
                        english_name = translated_names[0].strip()
                        category.name_en = english_name
                        category.is_en_complete = True
                except Exception as e:
                    logger.warning(f"한국어 → 영어 번역 실패: {e}")
            else:
                return {
                    'translated': False,
                    'skipped': True,
                    'message': '번역할 원본 이름이 없음 (name_en, name_ko 모두 비어있음)'
                }
        
        english_name = english_name.strip()
        update_fields = []
        translated_languages = []
        
        # 번역 대상 언어 목록 (영어 → 다른 언어만 번역, 한국어는 제외)
        target_languages = [
            (LANGUAGE_ES, 'name_es', 'is_es_complete'),
            (LANGUAGE_ZH, 'name_zh', 'is_zh_complete'),
            (LANGUAGE_JA, 'name_ja', 'is_ja_complete'),
        ]
        
        # 각 언어별로 번역 수행
        for target_lang, name_field, complete_field in target_languages:
            current_value = getattr(category, name_field, None) or ""
            current_value = current_value.strip() if isinstance(current_value, str) else ""
            
            # force 모드가 아니고 이미 값이 있으면 건너뜀
            if not force and current_value:
                logger.info(
                    f"[CATEGORY_TRANSLATE] [{category.id}] {name_field} 이미 있음: '{current_value}' - 건너뜀"
                )
                continue
            
            # 번역 필요 여부 로그
            logger.info(
                f"[CATEGORY_TRANSLATE] [{category.id}] 번역 시작: {LANGUAGE_EN} '{english_name}' → {target_lang}"
            )
            
            # 영어 → 대상 언어 번역
            try:
                translated_names = batch_translate_texts([english_name], LANGUAGE_EN, target_lang)
                if translated_names and len(translated_names) > 0 and translated_names[0]:
                    translated_name = translated_names[0].strip() if translated_names[0] else None
                    if translated_name:
                        setattr(category, name_field, translated_name)
                        setattr(category, complete_field, True)
                        update_fields.extend([name_field, complete_field])
                        translated_languages.append(target_lang)
                        logger.info(
                            f"[CATEGORY_TRANSLATE] 번역 완료: {LANGUAGE_EN} '{english_name}' → "
                            f"{target_lang} '{translated_name}'"
                        )
                    else:
                        logger.warning(
                            f"[CATEGORY_TRANSLATE] [{category.id}] 번역 실패: {LANGUAGE_EN} '{english_name}' → {target_lang} "
                            f"(번역 결과가 빈 문자열)"
                        )
                else:
                    logger.warning(
                        f"[CATEGORY_TRANSLATE] [{category.id}] 번역 실패: {LANGUAGE_EN} '{english_name}' → {target_lang} "
                        f"(번역 결과 없음: {translated_names})"
                    )
            except Exception as e:
                logger.error(
                    f"[CATEGORY_TRANSLATE] [{category.id}] 번역 중 예외 발생 ({LANGUAGE_EN} '{english_name}' → {target_lang}): {str(e)}",
                    exc_info=True
                )
        
        # name_en이 새로 번역된 경우 update_fields에 추가
        if category.name_en and 'name_en' not in update_fields:
            # 영어가 새로 설정되었지만 아직 저장되지 않은 경우
            # 이미 저장되었거나 원래 있던 값이므로 추가하지 않음
            pass
        
        # 번역된 필드가 있으면 저장
        if update_fields:
            if not dry_run:
                category.save(update_fields=update_fields)
                logger.info(
                    f"[CATEGORY_TRANSLATE] 카테고리 번역 저장 완료: "
                    f"category_id={category.id}, 언어={translated_languages}, 필드={update_fields}"
                )
            
            return {
                'translated': True,
                'skipped': False,
                'message': f'{", ".join(translated_languages)} 번역 완료'
            }
        else:
            # 번역된 필드가 없는 경우 - 원인 파악을 위한 상세 정보
            missing_languages = []
            for target_lang, name_field, _ in target_languages:
                current_value = getattr(category, name_field, None) or ""
                if not (current_value and str(current_value).strip()):
                    missing_languages.append(f"{name_field}({target_lang})")
            
            if missing_languages:
                return {
                    'translated': False,
                    'skipped': False,
                    'message': f'번역 실패: {", ".join(missing_languages)} - 번역 API 응답 없음 또는 오류'
                }
            else:
                return {
                    'translated': False,
                    'skipped': True,
                    'message': '모든 언어 번역이 이미 완료되어 있음'
                }

