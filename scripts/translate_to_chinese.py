#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
중국어 번역 스크립트
message_zh.py의 영어로 된 키들을 중국어로 번역합니다.
"""

import ast
import re

# 기본 번역 매핑
TRANSLATIONS = {
    # Common words
    'Language Switch': '切换语言',
    'Switch Language': '切换语言',
    'Loading translations...': '正在加载翻译...',
    'Loading translation data...': '正在加载翻译数据...',
    'User information saved': '用户信息已保存',
    'Sign in with Apple': '使用 Apple 登录',
    'Cache has been disabled.': '缓存已禁用。',
    'All cache has been cleared.': '所有缓存已清除。',
    'Profile information has been refreshed.': '个人资料信息已刷新。',
    'User information has been updated.': '用户信息已更新。',
    'Automatic Translation': '自动翻译',
    'Language settings have been changed.': '语言设置已更改。',
    'Password has been changed successfully.': '密码已成功更改。',
    'Passwords do not match.': '密码不匹配。',
    'Redirecting...': '正在重定向...',
    'URL has expired.': 'URL 已过期。',
    'Resetting...': '正在重置...',
    'Failed to': '无法',
    'Please': '请',
    'Select': '选择',
    'Enter': '输入',
    'Create': '创建',
    'Delete': '删除',
    'Update': '更新',
    'Save': '保存',
    'Cancel': '取消',
    'Confirm': '确认',
    'Are you sure': '您确定',
    'Do you want': '您想要',
    'This action cannot be undone.': '此操作无法撤销。',
    'Operation completed successfully.': '操作成功完成。',
    'Operation failed.': '操作失败。',
    'No data available.': '无可用数据。',
    'No results found.': '未找到结果。',
    'No tags available': '无可用标签',
    'Selected Tags': '已选标签',
    'Manage Tags': '管理标签',
    'Remove Tag': '移除标签',
    'Tags have been updated.': '标签已更新。',
    'Tag has been removed.': '标签已移除。',
    'Required': '必填',
    'Active': '激活',
    'Inactive': '未激活',
    'Edit': '编辑',
    'Color Code (Optional)': '颜色代码（可选）',
    'e.g., 🟩, 🟦, 🟨': '例如：🟩, 🟦, 🟨',
    'Korean Name': '韩语名称',
    'English Name': '英语名称',
    'Parent Category': '父类别',
    'None (Top Level)': '无（顶级）',
    'Order': '顺序',
    'Level': '级别',
    'Drag to Move': '拖拽移动',
    'Show Inactive Items': '显示未激活项目',
    'Hide Inactive Items': '隐藏未激活项目',
    'Tag Category Management': '标签类别管理',
    'Add New Category': '添加新类别',
    'Edit Category': '编辑类别',
    'Add Child Category': '添加子类别',
    'Activate': '激活',
    'Deactivate': '停用',
    'Delete Category': '删除类别',
}

def translate_text(text, key=None):
    """텍스트를 중국어로 번역"""
    if not text or not isinstance(text, str):
        return text
    
    # 이미 중국어가 포함되어 있으면 그대로 반환
    if re.search(r'[\u4e00-\u9fff]', text):
        # 일부 영어가 섞여있을 수 있으므로 확인
        if re.search(r'[A-Za-z]', text) and not re.match(r'^[A-Za-z\s\.\,\:\!\?\-\(\)\{\}\[\]\/\\]+$', text):
            # 혼합된 경우, 영어 부분만 번역
            pass
    
    # 완전히 영어인 경우만 번역
    if re.match(r'^[A-Za-z\s\.\,\:\!\?\-\(\)\{\}\[\]\/\\]+$', text):
        # 기본 번역 매핑 확인
        for en, zh in TRANSLATIONS.items():
            if text == en:
                return zh
            if text.startswith(en + ' '):
                return text.replace(en, zh, 1)
            if text.endswith(' ' + en):
                return text.replace(' ' + en, ' ' + zh, 1)
            if ' ' + en + ' ' in text:
                return text.replace(' ' + en + ' ', ' ' + zh + ' ', 1)
    
    # 패턴 기반 번역
    patterns = [
        (r'Failed to (.+?)\.', r'无法\1。'),
        (r'Please (.+?)\.', r'请\1。'),
        (r'Are you sure (.+?)\?', r'您确定\1吗？'),
        (r'Do you want to (.+?)\?', r'您想要\1吗？'),
        (r'Select (.+?)', r'选择\1'),
        (r'Enter (.+?)', r'输入\1'),
        (r'Create (.+?)', r'创建\1'),
        (r'Delete (.+?)', r'删除\1'),
        (r'Update (.+?)', r'更新\1'),
        (r'Save (.+?)', r'保存\1'),
        (r'Cancel (.+?)', r'取消\1'),
        (r'Confirm (.+?)', r'确认\1'),
    ]
    
    result = text
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    return result if result != text else text

def translate_file():
    """message_zh.py 파일을 읽어서 번역되지 않은 부분을 번역"""
    with open('quiz/message_en.py', 'r', encoding='utf-8') as f:
        en_content = f.read()
    
    with open('quiz/message_zh.py', 'r', encoding='utf-8') as f:
        zh_content = f.read()
    
    # Parse AST
    en_ast = ast.parse(en_content)
    zh_ast = ast.parse(zh_content)
    
    # Extract dictionaries
    en_dict = {}
    zh_dict = {}
    
    for node in en_ast.body[0].value.keys:
        if isinstance(node, ast.Constant):
            key = node.s
            idx = list(en_ast.body[0].value.keys).index(node)
            if idx < len(en_ast.body[0].value.values):
                val = en_ast.body[0].value.values[idx]
                if isinstance(val, ast.Constant):
                    en_dict[key] = val.s
    
    for node in zh_ast.body[0].value.keys:
        if isinstance(node, ast.Constant):
            key = node.s
            idx = list(zh_ast.body[0].value.keys).index(node)
            if idx < len(zh_ast.body[0].value.values):
                val = zh_ast.body[0].value.values[idx]
                if isinstance(val, ast.Constant):
                    zh_dict[key] = val.s
    
    # Find untranslated keys
    untranslated = {}
    for key in en_dict:
        if key in zh_dict:
            zh_val = zh_dict[key]
            en_val = en_dict[key]
            
            # Check if it's completely English and same as English
            if re.match(r'^[A-Za-z\s\.\,\:\!\?\-\(\)\{\}\[\]\/\\]+$', zh_val) and zh_val == en_val:
                untranslated[key] = (en_val, zh_val)
            # Check if it contains common English phrases that should be translated
            elif any(phrase in zh_val for phrase in ['Are you sure', 'Do you want', 'Failed to', 'Please ', 'Select ', 'Enter ', 'Create ', 'Delete ', 'Update ', 'Save ', 'Cancel ', 'Confirm ']):
                # Partially translated, might need improvement
                pass
    
    print(f"Found {len(untranslated)} completely untranslated keys")
    
    # Read the file line by line and replace
    lines = zh_content.split('\n')
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this line contains an untranslated key
        for key, (en_val, zh_val) in untranslated.items():
            # Look for the key in the line
            if f"'{key}'" in line or f'"{key}"' in line:
                # Find the value part
                if ': ' in line:
                    # Simple case: single line
                    if "'" in line:
                        # Extract the value
                        match = re.search(r":\s*'([^']*)'", line)
                        if match:
                            old_val = match.group(1)
                            if old_val == en_val:
                                # Translate
                                new_val = translate_text(en_val, key)
                                line = line.replace(f": '{old_val}'", f": '{new_val}'")
                    elif '"' in line:
                        match = re.search(r':\s*"([^"]*)"', line)
                        if match:
                            old_val = match.group(1)
                            if old_val == en_val:
                                new_val = translate_text(en_val, key)
                                line = line.replace(f': "{old_val}"', f': "{new_val}"')
                elif '"""' in line:
                    # Multi-line string
                    # Find the end of the multi-line string
                    j = i
                    multi_line = line
                    while '"""' not in multi_line or multi_line.count('"""') < 2:
                        j += 1
                        if j >= len(lines):
                            break
                        multi_line += '\n' + lines[j]
                    
                    if '"""' in multi_line and multi_line.count('"""') >= 2:
                        # Extract the content
                        match = re.search(r'"""([^"]*)"""', multi_line, re.DOTALL)
                        if match:
                            old_val = match.group(1)
                            if old_val.strip() == en_val.strip():
                                new_val = translate_text(en_val, key)
                                # Replace in the multi-line
                                new_multi = multi_line.replace(f'"""{old_val}"""', f'"""{new_val}"""')
                                # Split back to lines
                                new_multi_lines = new_multi.split('\n')
                                new_lines.extend(new_multi_lines)
                                i = j + 1
                                continue
        
        new_lines.append(line)
        i += 1
    
    # Write back
    with open('quiz/message_zh.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print("Translation completed!")

if __name__ == '__main__':
    translate_file()





