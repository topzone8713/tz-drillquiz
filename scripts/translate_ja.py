#!/usr/bin/env python3
"""
Translate message_ja.py from English to Japanese
"""
import re
import sys

# Translation dictionary for common terms
COMMON_TRANSLATIONS = {
    'Home': 'ホーム',
    'Study': '学習',
    'Exam': '試験',
    'Login': 'ログイン',
    'Profile': 'プロフィール',
    'Favorites': 'お気に入り',
    'Privacy Policy': 'プライバシーポリシー',
    'Terms of Service': '利用規約',
    'About this': 'このサービスについて',
    'Username': 'ユーザー名',
    'Password': 'パスワード',
    'Register': '登録',
    'Cancel': 'キャンセル',
    'Confirm': '確認',
    'Save': '保存',
    'Delete': '削除',
    'Edit': '編集',
    'Refresh': '更新',
    'Loading...': '読み込み中...',
    'Failed': '失敗',
    'Success': '成功',
    'Error': 'エラー',
    'Warning': '警告',
}

def translate_text(text):
    """Translate English text to Japanese"""
    # Handle common patterns
    if text in COMMON_TRANSLATIONS:
        return COMMON_TRANSLATIONS[text]
    
    # For now, return a placeholder that indicates translation needed
    # In a real scenario, you would use a translation API or service
    return text  # Placeholder - will need manual translation

def translate_file(input_file, output_file):
    """Translate the message_ja.py file"""
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to match translation entries: 'key': 'value'
    pattern = r"('([^']+)':\s*)'([^']+)'"
    
    def replace_match(match):
        key_part = match.group(1)  # 'key': 
        value = match.group(3)      # value
        translated = translate_text(value)
        return f"{key_part}'{translated}'"
    
    # Replace all matches
    translated_content = re.sub(pattern, replace_match, content)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(translated_content)
    
    print(f"Translation complete. Output written to {output_file}")

if __name__ == '__main__':
    translate_file('quiz/message_ja.py', 'quiz/message_ja_translated.py')

