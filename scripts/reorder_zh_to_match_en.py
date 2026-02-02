#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
message_zh.py를 message_en.py와 완전히 동일한 구조와 순서로 재구성
"""

import ast
import re

def reorder_zh_file():
    """message_zh.py를 message_en.py와 동일한 순서로 재구성"""
    # Read EN file
    with open('quiz/message_en.py', 'r', encoding='utf-8') as f:
        en_content = f.read()
        en_ast = ast.parse(en_content)
    
    # Read ZH file
    with open('quiz/message_zh.py', 'r', encoding='utf-8') as f:
        zh_content = f.read()
        zh_ast = ast.parse(zh_content)
    
    # Build EN dictionary with order and comments
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
    
    # Parse EN file line by line to preserve structure
    en_lines = en_content.split('\n')
    output_lines = ['# Chinese translation messages', 'CHINESE_TRANSLATIONS = {']
    
    i = 0
    while i < len(en_lines):
        line = en_lines[i]
        original_line = line.rstrip()
        
        # Skip header lines we already added
        if i < 2:
            i += 1
            continue
        
        # Check for comments
        if original_line.strip().startswith('#'):
            output_lines.append(original_line)
        
        # Check for key-value pairs
        elif "': '" in original_line or '": "' in original_line or "': " in original_line:
            # Extract key
            key_match = re.search(r"['\"]([^'\"]+)['\"]:\s*", original_line)
            if key_match:
                key = key_match.group(1)
                
                # Get indentation from EN file
                indent = len(original_line) - len(original_line.lstrip())
                
                if key in zh_dict:
                    # Use ZH translation
                    zh_val = zh_dict[key]
                    # Format value (handle multi-line strings)
                    if '\n' in zh_val or '"""' in zh_val:
                        # Multi-line string
                        escaped = zh_val.replace('"""', '\\"\\"\\"')
                        formatted_value = f'"""{escaped}"""'
                    else:
                        # Single-line string - escape single quotes
                        escaped = zh_val.replace("'", "\\'")
                        formatted_value = f"'{escaped}'"
                    
                    output_lines.append(' ' * indent + f"'{key}': {formatted_value},")
                else:
                    # Key not found, use EN value as fallback
                    print(f"Warning: Key {key} not in ZH dict, using EN value")
                    output_lines.append(original_line)
        
        # Check for closing brace
        elif original_line.strip() == '}':
            output_lines.append(original_line)
            # Add get_message function
            i += 1
            if i < len(en_lines) and 'def get_message' in en_lines[i]:
                # Copy get_message function but change the docstring
                while i < len(en_lines):
                    func_line = en_lines[i].rstrip()
                    if 'def get_message' in func_line:
                        output_lines.append('')
                        output_lines.append('def get_message(key, default=None):')
                        output_lines.append('    """Returns the Chinese message for the given translation key."""')
                        output_lines.append('    return CHINESE_TRANSLATIONS.get(key, default or key)')
                        break
                    i += 1
            break
        
        # Empty lines
        elif not original_line.strip():
            # Only add if previous line wasn't empty
            if output_lines and output_lines[-1].strip():
                output_lines.append('')
        
        i += 1
    
    # Write new file
    with open('quiz/message_zh.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    
    print("File reordered successfully!")
    print(f"EN keys: {len(en_keys_ordered)}")
    print(f"ZH translations: {len(zh_dict)}")
    print(f"Missing keys: {len(set(en_keys_ordered) - set(zh_dict.keys()))}")

if __name__ == '__main__':
    reorder_zh_file()





