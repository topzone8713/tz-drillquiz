#!/usr/bin/env python3
"""
DrillQuiz 번역 자동화 도구
Vue 파일에서 $t() 함수를 추출하고 Django .po 파일과 동기화
"""

import os
import re
import json
import argparse
from pathlib import Path
from typing import Set, Dict, List
import polib

class TranslationExtractor:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.vue_dir = self.project_root / "src"
        self.locale_dir = self.project_root / "locale"
        self.extracted_keys: Set[str] = set()
        self.vue_translations: Dict[str, Dict[str, str]] = {
            'ko': {},
            'en': {},
            'es': {},
            'zh': {},
            'ja': {}
        }
        
    def extract_vue_translations(self) -> Set[str]:
        """Vue 파일에서 $t() 함수를 추출"""
        print("🔍 Vue 파일에서 번역 키 추출 중...")
        
        # $t() 패턴 매칭 (다양한 형태 지원)
        patterns = [
            r'\$t\([\'"`]([^\'"`]+)[\'"`]\)',  # $t('key') 또는 $t("key")
            r'\$t\([\'"`]([^\'"`]+)[\'"`]\s*,\s*[\'"`]([^\'"`]+)[\'"`]\)',  # $t('key', 'default')
        ]
        
        for vue_file in self.vue_dir.rglob("*.vue"):
            print(f"  📄 {vue_file.relative_to(self.project_root)}")
            
            try:
                with open(vue_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        if isinstance(match, tuple):
                            key = match[0]
                            default = match[1] if len(match) > 1 else ""
                        else:
                            key = match
                            default = ""
                        
                        self.extracted_keys.add(key)
                        if default:
                            # 기본값을 BASE_LANGUAGE('en') 번역으로 사용
                            from quiz.utils.multilingual_utils import BASE_LANGUAGE
                            self.vue_translations[BASE_LANGUAGE][key] = default
                            
            except Exception as e:
                print(f"  ❌ {vue_file} 읽기 실패: {e}")
        
        print(f"✅ {len(self.extracted_keys)}개의 번역 키 추출 완료")
        return self.extracted_keys
    
    def load_existing_translations(self) -> Dict[str, Dict[str, str]]:
        """기존 Django .po 파일에서 번역 로드"""
        print("📚 기존 Django 번역 로드 중...")
        
        translations = {'ko': {}, 'en': {}, 'es': {}, 'zh': {}, 'ja': {}}
        
        for lang in ['ko', 'en', 'es', 'zh', 'ja']:
            po_file = self.locale_dir / lang / "LC_MESSAGES" / "django.po"
            
            if po_file.exists():
                try:
                    po = polib.pofile(str(po_file))
                    for entry in po:
                        if entry.msgid and entry.msgstr:
                            translations[lang][entry.msgid] = entry.msgstr
                    print(f"  ✅ {lang}: {len(translations[lang])}개 번역 로드")
                except Exception as e:
                    print(f"  ❌ {lang} .po 파일 읽기 실패: {e}")
            else:
                print(f"  ⚠️  {lang} .po 파일이 없습니다")
        
        return translations
    
    def update_django_translations(self, new_keys: Set[str]):
        """Django .po 파일에 새로운 번역 키 추가"""
        print("🔄 Django .po 파일 업데이트 중...")
        
        for lang in ['ko', 'en', 'es', 'zh', 'ja']:
            po_file = self.locale_dir / lang / "LC_MESSAGES" / "django.po"
            
            # .po 파일이 없으면 생성
            if not po_file.exists():
                po_file.parent.mkdir(parents=True, exist_ok=True)
                po = polib.POFile()
                po.metadata = {
                    'Project-Id-Version': 'DrillQuiz',
                    'Report-Msgid-Bugs-To': '',
                    'POT-Creation-Date': '',
                    'PO-Revision-Date': '',
                    'Last-Translator': '',
                    'Language-Team': '',
                    'Language': lang,
                    'MIME-Version': '1.0',
                    'Content-Type': 'text/plain; charset=utf-8',
                    'Content-Transfer-Encoding': '8bit',
                    'Plural-Forms': 'nplurals=2; plural=(n != 1);',
                }
            else:
                po = polib.pofile(str(po_file))
            
            # 새로운 키 추가
            added_count = 0
            for key in new_keys:
                # 이미 존재하는지 확인
                existing_entry = None
                for entry in po:
                    if entry.msgid == key:
                        existing_entry = entry
                        break
                
                if not existing_entry:
                    # Vue 키를 기본 텍스트로 변환 (모든 언어 동일하게 처리)
                    default_text = key.replace('.', ' ').replace('_', ' ').title()
                    # 모든 언어에 대해 동일하게 처리
                    msgstr = self.vue_translations[lang].get(key, default_text)
                    
                    entry = polib.POEntry(
                        msgid=key,
                        msgstr=msgstr,
                        occurrences=[('vue', 'extracted')]
                    )
                    po.append(entry)
                    added_count += 1
            
            # 파일 저장
            try:
                po.save(str(po_file))
                print(f"  ✅ {lang}: {added_count}개 새 번역 키 추가")
            except Exception as e:
                print(f"  ❌ {lang} .po 파일 저장 실패: {e}")
    
    def update_vue_i18n(self):
        """Vue i18n 설정 업데이트"""
        print("🔄 Vue i18n 설정 업데이트 중...")
        
        # 번역 API에서 사용할 데이터 생성
        api_translations = {}
        for lang in ['ko', 'en', 'es', 'zh', 'ja']:
            po_file = self.locale_dir / lang / "LC_MESSAGES" / "django.po"
            if po_file.exists():
                po = polib.pofile(str(po_file))
                for entry in po:
                    if entry.msgid and entry.msgstr:
                        api_translations[entry.msgid] = entry.msgstr
        
        # Django views.py의 get_translations 함수 업데이트
        self.update_django_translations_api(api_translations)
        
        print("✅ Vue i18n 설정 업데이트 완료")
    
    def update_django_translations_api(self, translations: Dict[str, str]):
        """Django views.py의 get_translations 함수 업데이트"""
        views_file = self.project_root / "quiz" / "views.py"
        
        if not views_file.exists():
            print("❌ quiz/views.py 파일을 찾을 수 없습니다")
            return
        
        try:
            with open(views_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # get_translations 함수 찾기
            pattern = r'def get_translations\(request\):(.*?)(?=def|\Z)'
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                # 새로운 번역 데이터 생성
                translations_code = []
                for key, value in translations.items():
                    # Vue에서 사용하는 점 표기법 키를 그대로 사용
                    translations_code.append(f"        '{key}': _('{value}'),")
                
                # 번역 데이터 섹션 교체
                new_translations_section = '\n'.join(translations_code)
                
                # 기존 번역 섹션 교체
                old_pattern = r'    translations\.update\(\{.*?\}\)'
                new_section = f'    translations.update({{{new_translations_section}\n    }})'
                
                content = re.sub(old_pattern, new_section, content, flags=re.DOTALL)
                
                # 파일 저장
                with open(views_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print("✅ Django views.py 번역 API 업데이트 완료")
            else:
                print("❌ get_translations 함수를 찾을 수 없습니다")
                
        except Exception as e:
            print(f"❌ Django views.py 업데이트 실패: {e}")
    
    def compile_messages(self):
        """Django 번역 메시지 컴파일"""
        print("🔨 Django 번역 메시지 컴파일 중...")
        
        try:
            import subprocess
            result = subprocess.run(
                ['python', 'manage.py', 'compilemessages'],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ 번역 메시지 컴파일 완료")
            else:
                print(f"❌ 번역 메시지 컴파일 실패: {result.stderr}")
                
        except Exception as e:
            print(f"❌ 번역 메시지 컴파일 실패: {e}")
    
    def generate_report(self):
        """번역 상태 리포트 생성"""
        print("\n📊 번역 상태 리포트")
        print("=" * 50)
        
        for lang in ['ko', 'en', 'es', 'zh', 'ja']:
            po_file = self.locale_dir / lang / "LC_MESSAGES" / "django.po"
            if po_file.exists():
                po = polib.pofile(str(po_file))
                total = len(po)
                translated = sum(1 for entry in po if entry.msgstr)
                untranslated = total - translated
                
                print(f"{lang.upper()}:")
                print(f"  총 번역 키: {total}")
                print(f"  번역 완료: {translated}")
                print(f"  번역 필요: {untranslated}")
                print(f"  완성도: {(translated/total*100):.1f}%" if total > 0 else "  0%")
                print()
    
    def run(self):
        """전체 번역 자동화 프로세스 실행"""
        print("🚀 DrillQuiz 번역 자동화 시작")
        print("=" * 50)
        
        # 1. Vue 파일에서 번역 키 추출
        new_keys = self.extract_vue_translations()
        
        # 2. 기존 번역 로드
        existing_translations = self.load_existing_translations()
        
        # 3. Django .po 파일 업데이트
        self.update_django_translations(new_keys)
        
        # 4. Vue i18n 업데이트
        self.update_vue_i18n()
        
        # 5. 번역 메시지 컴파일
        self.compile_messages()
        
        # 6. 리포트 생성
        self.generate_report()
        
        print("🎉 번역 자동화 완료!")

def main():
    parser = argparse.ArgumentParser(description='DrillQuiz 번역 자동화 도구')
    parser.add_argument('--project-root', default='.', help='프로젝트 루트 디렉토리')
    parser.add_argument('--extract-only', action='store_true', help='Vue 파일 추출만 실행')
    parser.add_argument('--compile-only', action='store_true', help='번역 컴파일만 실행')
    
    args = parser.parse_args()
    
    extractor = TranslationExtractor(args.project_root)
    
    if args.extract_only:
        extractor.extract_vue_translations()
    elif args.compile_only:
        extractor.compile_messages()
    else:
        extractor.run()

if __name__ == '__main__':
    main() 