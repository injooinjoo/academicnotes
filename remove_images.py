#!/usr/bin/env python3
"""
TEX 파일에서 모든 figure 환경 제거/주석처리
"""
import re
from pathlib import Path

def remove_figures(tex_file):
    """Remove all figure environments from tex file"""
    with open(tex_file, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Remove all figure environments
    pattern = r'\\begin\{figure\}\[.*?\].*?\\end\{figure\}'
    content = re.sub(pattern, r'% [Figure removed - image file not found]', content, flags=re.DOTALL)

    if content != original:
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

# Fix lecture_08
tex_file = Path("school/harvard/cs109/lecture_08/8.tex")
if remove_figures(tex_file):
    print(f"Fixed: {tex_file}")
else:
    print(f"No changes: {tex_file}")
