#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
adjustbox를 제거하고 tabularx로 변환하는 스크립트
"""

import re
from pathlib import Path

def fix_adjustbox_in_file(filepath):
    """파일에서 adjustbox를 tabularx로 변환"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    changes_made = 0

    # Pattern 1: \adjustbox{max width=\textwidth}{ ... \begin{tabular}{ll} ... }
    # -> \begin{tabularx}{\textwidth}{lX}

    # adjustbox 시작 찾기
    pattern = r'\\adjustbox\{max width=\\textwidth\}\{\s*\\begin\{tabular\}\{([^}]+)\}'

    def replace_adjustbox(match):
        nonlocal changes_made
        col_spec = match.group(1)

        # ll -> lX로 변환 (마지막 l을 X로)
        if col_spec == 'll':
            new_spec = 'lX'
        elif col_spec == 'lll':
            new_spec = 'llX'
        elif col_spec == 'llll':
            new_spec = 'lllX'
        else:
            # 다른 경우는 마지막 컬럼을 X로
            new_spec = col_spec[:-1] + 'X' if col_spec else 'lX'

        changes_made += 1
        return f'\\begin{{tabularx}}{{\\textwidth}}{{{new_spec}}}'

    # adjustbox + tabular 시작 부분을 tabularx로 변환
    content = re.sub(pattern, replace_adjustbox, content)

    # 종료 부분 수정: \end{tabular} \n } \n \end{adjustbox} -> \end{tabularx}
    content = re.sub(
        r'\\end\{tabular\}\s*\}\s*\\end\{adjustbox\}',
        r'\\end{tabularx}',
        content
    )

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True, changes_made

    return False, 0

def main():
    """메인 실행 함수"""
    target_file = Path("school/harvard/csci103/lecture_02/2.tex")

    if not target_file.exists():
        print(f"Error: {target_file} not found")
        return

    print("=" * 80)
    print("adjustbox 제거 및 tabularx 변환")
    print("=" * 80)
    print(f"\n대상 파일: {target_file}\n")

    modified, changes = fix_adjustbox_in_file(target_file)

    if modified:
        print(f"✅ 수정 완료: {changes}개의 adjustbox를 tabularx로 변환")
    else:
        print("ℹ️  변경 사항 없음")

    print("=" * 80)

if __name__ == "__main__":
    import sys
    import io
    # Windows console encoding fix
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    main()
