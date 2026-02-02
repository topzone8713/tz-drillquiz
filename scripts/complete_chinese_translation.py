#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
완전한 중국어 번역 스크립트
message_zh.py의 모든 영어 값을 중국어로 번역
"""

import ast
import re

def translate_text(text):
    """텍스트를 중국어로 번역 (기본 패턴)"""
    if not text:
        return text
    
    # 이미 중국어가 포함되어 있으면 그대로 반환
    if re.search(r'[\u4e00-\u9fff]', text):
        return text
    
    # 완전히 영어인 경우만 번역
    if not re.match(r'^[A-Za-z\s\.\,\:\!\?\-\(\)\{\}\[\]\/\\\"\']+$', text):
        return text
    
    # 기본 번역 매핑
    translations = {
        "Don't have an account?": "没有账户？",
        "Are you sure you want to delete the tag \"{tagName}\" from the database?\n\nThis action cannot be undone.": "您确定要从数据库中删除标签 \"{tagName}\" 吗？\n\n此操作无法撤销。",
        "Exporting...": "正在导出...",
        "Accuracy adjustment records": "准确率调整记录",
        "Account & Security": "账户与安全",
        "Account Withdrawal": "账户注销",
        "User profile and personal settings": "用户资料和个人设置",
        "Withdraw Account": "注销账户",
        "WITHDRAW": "注销",
        "Back": "返回",
        "Send": "发送",
        "Drill, Quiz, Drill": "练习、测验、练习",
        "Master the quizzes you often get wrong with DrillQuiz!": "使用 DrillQuiz 掌握您经常出错的测验！",
        "Key Features": "主要功能",
        "Discover the core features of DrillQuiz": "发现 DrillQuiz 的核心功能",
        "Getting Started": "开始使用",
        "Get today's quizzes": "获取今天的测验",
        "Random Practice": "随机练习",
        "Practice with random quizzes": "使用随机测验进行练习",
        "Start Practice": "开始练习",
        "User Management": "用户管理",
        "Manage users and permissions": "管理用户和权限",
        "Manage Users": "管理用户",
        "increase": "增加",
        "decrease": "减少",
        "Period": "期间",
        "Recent Quizzes": "最近的测验",
        "Elapsed": "已用时间",
    }
    
    if text in translations:
        return translations[text]
    
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
                translated = translate_text(en_dict[key])
                if translated != en_dict[key]:
                    translations[key] = (en_dict[key], translated)
    
    print(f"Found {len(translations)} keys to translate")
    
    # Read file line by line and replace
    lines = zh_content.split('\n')
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        original_line = line
        
        # Check for key-value pairs
        for key, (en_val, zh_val) in translations.items():
            # Look for the key in the line
            if f"'{key}'" in line or f'"{key}"' in line:
                # Single-line string
                if "': '" in line or '": "' in line:
                    # Find and replace the value
                    # Pattern: 'key': 'value'
                    pattern1 = rf"'{key}':\s*'({re.escape(en_val)})'"
                    if re.search(pattern1, line):
                        line = re.sub(pattern1, f"'{key}': '{zh_val}'", line)
                        break
                    # Pattern: "key": "value"
                    pattern2 = rf'"{key}":\s*"({re.escape(en_val)})"'
                    if re.search(pattern2, line):
                        line = re.sub(pattern2, f'"{key}": "{zh_val}"', line)
                        break
                
                # Multi-line string
                if '"""' in line:
                    # Collect multi-line string
                    multi_start = i
                    multi_lines = [line]
                    i += 1
                    while i < len(lines) and '"""' not in lines[i-1] or lines[i-1].count('"""') < 2:
                        multi_lines.append(lines[i])
                        i += 1
                        if i >= len(lines):
                            break
                    
                    multi_content = '\n'.join(multi_lines)
                    
                    # Check if this multi-line contains our key and value
                    if f"'{key}'" in multi_content:
                        # Extract the value between triple quotes
                        match = re.search(r'"""([^"]*)"""', multi_content, re.DOTALL)
                        if match:
                            content = match.group(1)
                            if content.strip() == en_val.strip():
                                # Translate
                                translated_content = translate_text(en_val)
                                multi_content = multi_content.replace(
                                    f'"""{content}"""',
                                    f'"""{translated_content}"""'
                                )
                                # Split back to lines
                                new_lines.extend(multi_content.split('\n'))
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





