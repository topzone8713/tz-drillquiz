#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
중국어 번역 스크립트 - message_zh.py의 영어 키를 중국어로 번역
"""

import re
import ast

# 번역 매핑 (주요 패턴)
TRANSLATION_MAP = {
    # Common phrases
    'Language Switch': '切换语言',
    'Switch Language': '切换语言',
    'User information saved': '用户信息已保存',
    'Sign in with Apple': '使用 Apple 登录',
    "Don't have an account?": '没有账户？',
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
    'Loading translations...': '正在加载翻译...',
    'Loading translation data...': '正在加载翻译数据...',
    'Selected Tags': '已选标签',
    'Manage Tags': '管理标签',
    'Remove Tag': '移除标签',
    'Tags have been updated.': '标签已更新。',
    'Tag has been removed.': '标签已移除。',
    'Required': '必填',
    'Active': '激活',
    'Inactive': '未激活',
    'Edit': '编辑',
    'Delete': '删除',
    'Save': '保存',
    'Cancel': '取消',
    'Confirm': '确认',
    'No results found.': '未找到结果。',
    'No tags available': '无可用标签',
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

def translate_value(text, key=None):
    """값을 중국어로 번역"""
    if not text:
        return text
    
    # 이미 중국어가 포함되어 있으면 그대로 반환
    if re.search(r'[\u4e00-\u9fff]', text):
        return text
    
    # 완전히 영어인 경우만 번역
    if not re.match(r'^[A-Za-z\s\.\,\:\!\?\-\(\)\{\}\[\]\/\\\"\']+$', text):
        return text
    
    # 직접 매핑 확인
    if text in TRANSLATION_MAP:
        return TRANSLATION_MAP[text]
    
    # 패턴 기반 번역
    patterns = [
        (r'^Failed to (.+?)\.$', r'无法\1。'),
        (r'^Please (.+?)\.$', r'请\1。'),
        (r'^Are you sure (.+?)\?$', r'您确定\1吗？'),
        (r'^Do you want to (.+?)\?$', r'您想要\1吗？'),
        (r'^Select (.+?)$', r'选择\1'),
        (r'^Enter (.+?)$', r'输入\1'),
        (r'^Create (.+?)$', r'创建\1'),
        (r'^Delete (.+?)$', r'删除\1'),
        (r'^Update (.+?)$', r'更新\1'),
        (r'^Save (.+?)$', r'保存\1'),
        (r'^Cancel (.+?)$', r'取消\1'),
        (r'^Confirm (.+?)$', r'确认\1'),
        (r'^Loading (.+?)$', r'正在加载\1'),
        (r'^(.+?) has been (.+?)\.$', r'\1已\2。'),
        (r'^(.+?) failed\.$', r'\1失败。'),
        (r'^(.+?) successful\.$', r'\1成功。'),
    ]
    
    result = text
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        if result != text:
            break
    
    return result

def translate_file():
    """message_zh.py 파일을 읽어서 번역"""
    with open('quiz/message_en.py', 'r', encoding='utf-8') as f:
        en_content = f.read()
    
    with open('quiz/message_zh.py', 'r', encoding='utf-8') as f:
        zh_content = f.read()
    
    # Parse AST
    en_ast = ast.parse(en_content)
    zh_ast = ast.parse(zh_content)
    
    # Build dictionaries
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
    translations = {}
    for key in en_dict:
        if key in zh_dict:
            if zh_dict[key] == en_dict[key]:
                # Same as English, needs translation
                translated = translate_value(en_dict[key], key)
                if translated != en_dict[key]:
                    translations[key] = (en_dict[key], translated)
    
    print(f"Found {len(translations)} keys to translate")
    
    # Read file and replace
    lines = zh_content.split('\n')
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        original_line = line
        
        # Check for single-line string values
        for key, (en_val, zh_val) in translations.items():
            # Look for the key
            key_pattern = f"'{key}'"
            if key_pattern in line:
                # Single quote string
                pattern = rf":\s*'({re.escape(en_val)})'"
                if re.search(pattern, line):
                    line = re.sub(pattern, f": '{zh_val}'", line)
                    break
                # Double quote string
                pattern = rf':\s*"({re.escape(en_val)})"'
                if re.search(pattern, line):
                    line = re.sub(pattern, f': "{zh_val}"', line)
                    break
        
        # Check for multi-line strings
        if '"""' in line:
            # Find the complete multi-line string
            multi_start = i
            multi_content = line
            while '"""' not in multi_content or multi_content.count('"""') < 2:
                i += 1
                if i >= len(lines):
                    break
                multi_content += '\n' + lines[i]
            
            if '"""' in multi_content and multi_content.count('"""') >= 2:
                # Extract and translate
                for key, (en_val, zh_val) in translations.items():
                    if f"'{key}'" in multi_content:
                        # Check if the value matches
                        match = re.search(r'"""([^"]*)"""', multi_content, re.DOTALL)
                        if match:
                            content = match.group(1)
                            if content.strip() == en_val.strip():
                                # Translate
                                translated_content = translate_value(en_val, key)
                                multi_content = multi_content.replace(
                                    f'"""{content}"""',
                                    f'"""{translated_content}"""'
                                )
                                break
                
                # Split back to lines
                multi_lines = multi_content.split('\n')
                new_lines.extend(multi_lines)
                i += 1
                continue
        
        new_lines.append(line)
        i += 1
    
    # Write back
    with open('quiz/message_zh.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print("Translation completed!")
    print(f"Translated {len(translations)} keys")

if __name__ == '__main__':
    translate_file()





