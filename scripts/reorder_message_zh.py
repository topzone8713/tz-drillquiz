#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
message_zh.py를 message_en.py와 동일한 키 순서와 구조로 재구성
"""

import ast
import re

def escape_string(s):
    """문자열을 Python 코드에 안전하게 이스케이프"""
    # Single quotes를 escape
    s = s.replace("'", "\\'")
    # Newlines를 \n으로 변환
    s = s.replace('\n', '\\n')
    return s

def format_value(value):
    """값을 Python 코드 형식으로 포맷"""
    if '\n' in value or '"""' in value:
        # Multi-line string
        # Escape triple quotes
        escaped = value.replace('"""', '\\"\\"\\"')
        return f'"""{escaped}"""'
    else:
        # Single-line string
        escaped = escape_string(value)
        return f"'{escaped}'"

def reorder_message_zh():
    """message_zh.py를 message_en.py와 동일한 순서로 재구성"""
    # Read EN file to get structure and order
    with open('quiz/message_en.py', 'r', encoding='utf-8') as f:
        en_content = f.read()
        en_ast = ast.parse(en_content)
    
    # Read ZH file to get translations
    with open('quiz/message_zh.py', 'r', encoding='utf-8') as f:
        zh_content = f.read()
        zh_ast = ast.parse(zh_content)
    
    # Build EN dictionary with order
    en_keys_ordered = []
    en_dict = {}
    for node in en_ast.body[0].value.keys:
        if isinstance(node, ast.Constant):
            key = node.s
            en_keys_ordered.append(key)
            idx = list(en_ast.body[0].value.keys).index(node)
            if idx < len(en_ast.body[0].value.values):
                val = en_ast.body[0].value.values[idx]
                if isinstance(val, ast.Constant):
                    en_dict[key] = val.s
    
    # Build ZH dictionary
    zh_dict = {}
    for node in zh_ast.body[0].value.keys:
        if isinstance(node, ast.Constant):
            key = node.s
            idx = list(zh_ast.body[0].value.keys).index(node)
            if idx < len(zh_ast.body[0].value.values):
                val = zh_ast.body[0].value.values[idx]
                if isinstance(val, ast.Constant):
                    zh_dict[key] = val.s
    
    # Read EN file to get comments and structure
    en_lines = en_content.split('\n')
    
    # Build new ZH file following EN structure
    output_lines = ['# Chinese translation messages', 'CHINESE_TRANSLATIONS = {']
    
    # Track current section comment
    current_comment = None
    i = 0
    
    while i < len(en_lines):
        line = en_lines[i].rstrip()
        
        # Check for comments
        if line.strip().startswith('#'):
            # Section comment
            if 'translations' in line.lower() or line.strip().startswith('# '):
                output_lines.append('')
                output_lines.append(line)
                current_comment = line
            else:
                # Inline comment, keep it
                if i > 0 and en_lines[i-1].strip() and not en_lines[i-1].strip().startswith('#'):
                    output_lines.append('')
                output_lines.append(line)
        
        # Check for key-value pairs
        elif "': '" in line or '": "' in line or "': " in line:
            # Extract key
            key_match = re.search(r"['\"]([^'\"]+)['\"]:\s*", line)
            if key_match:
                key = key_match.group(1)
                
                if key in zh_dict:
                    # Use ZH translation
                    zh_val = zh_dict[key]
                    # Format the line similar to EN
                    indent = len(line) - len(line.lstrip())
                    formatted_value = format_value(zh_val)
                    output_lines.append(' ' * indent + f"'{key}': {formatted_value},")
                else:
                    # Key not in ZH, use EN value (shouldn't happen, but just in case)
                    print(f"Warning: Key {key} not found in ZH, using EN value")
                    output_lines.append(line)
        
        # Check for closing brace
        elif line.strip() == '}' or line.strip().startswith('def get_message'):
            # End of dictionary, add get_message function
            output_lines.append('}')
            output_lines.append('')
            output_lines.append('def get_message(key, default=None):')
            output_lines.append('    """Returns the Chinese message for the given translation key."""')
            output_lines.append('    return CHINESE_TRANSLATIONS.get(key, default or key)')
            break
        
        # Empty lines
        elif not line.strip():
            # Only add if previous line wasn't empty
            if output_lines and output_lines[-1].strip():
                output_lines.append('')
        
        i += 1
    
    # Write new file
    with open('quiz/message_zh.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    
    print("File reordered successfully!")
    print(f"Total keys: {len(en_keys_ordered)}")
    print(f"ZH translations: {len(zh_dict)}")

if __name__ == '__main__':
    reorder_message_zh()





