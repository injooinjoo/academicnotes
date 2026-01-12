#!/usr/bin/env python3
"""
tabular/tabularx 불일치 수정 스크립트
- \begin{tabular}로 시작하면 \end{tabular}로 끝나야 함
- \begin{tabularx}로 시작하면 \end{tabularx}로 끝나야 함
"""

import re
from pathlib import Path


def fix_table_mismatch(content: str) -> str:
    """tabular/tabularx 불일치 수정"""
    lines = content.split('\n')
    result = []
    table_stack = []  # 열린 테이블 환경 추적

    for i, line in enumerate(lines):
        # tabular 시작 감지
        if '\\begin{tabular}' in line and '\\begin{tabularx}' not in line:
            table_stack.append('tabular')
        elif '\\begin{tabularx}' in line:
            table_stack.append('tabularx')

        # 닫는 태그 수정
        if '\\end{tabular}' in line and table_stack:
            if table_stack[-1] == 'tabularx':
                line = line.replace('\\end{tabular}', '\\end{tabularx}')
            table_stack.pop()
        elif '\\end{tabularx}' in line and table_stack:
            if table_stack[-1] == 'tabular':
                line = line.replace('\\end{tabularx}', '\\end{tabular}')
            table_stack.pop()

        result.append(line)

    return '\n'.join(result)


def process_file(file_path: Path) -> bool:
    """단일 파일 처리"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content
        content = fix_table_mismatch(content)

        if content != original:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    base_dir = Path("c:/Dev/academicnotes/school")

    total = 0
    modified = 0

    for tex_file in base_dir.rglob("*.tex"):
        total += 1
        if process_file(tex_file):
            print(f"Fixed: {tex_file.relative_to(base_dir)}")
            modified += 1

    print(f"\nTotal: {modified}/{total} files modified")


if __name__ == "__main__":
    main()
