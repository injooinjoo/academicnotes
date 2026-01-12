#!/usr/bin/env python3
"""
LaTeX에서 & 문자 이스케이프 수정
- 테이블 환경(tabular, tabularx, longtable, array) 내부의 &는 유지
- 그 외의 &는 \&로 변경
"""

import re
from pathlib import Path


def escape_ampersand_outside_tables(content: str) -> str:
    """테이블 환경 외부의 & 문자를 \&로 이스케이프"""
    lines = content.split('\n')
    result = []
    in_table = 0  # 중첩된 테이블 환경 카운트

    table_envs = ['tabular', 'tabularx', 'longtable', 'array', 'matrix',
                  'pmatrix', 'bmatrix', 'vmatrix', 'align', 'align*',
                  'eqnarray', 'eqnarray*', 'cases']

    for line in lines:
        # 테이블 환경 시작 감지
        for env in table_envs:
            if f'\\begin{{{env}}}' in line or f'\\begin{{{env}*}}' in line:
                in_table += line.count(f'\\begin{{{env}}}')
                in_table += line.count(f'\\begin{{{env}*}}')

        # 테이블 환경이 아닐 때만 & 이스케이프
        if in_table == 0:
            # 이미 이스케이프된 \& 는 건드리지 않음
            # & 앞에 \가 없는 경우만 치환
            new_line = re.sub(r'(?<!\\)&', r'\\&', line)
            result.append(new_line)
        else:
            result.append(line)

        # 테이블 환경 종료 감지
        for env in table_envs:
            if f'\\end{{{env}}}' in line or f'\\end{{{env}*}}' in line:
                in_table -= line.count(f'\\end{{{env}}}')
                in_table -= line.count(f'\\end{{{env}*}}')

        # 음수 방지
        in_table = max(0, in_table)

    return '\n'.join(result)


def process_file(file_path: Path) -> bool:
    """단일 파일 처리"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content
        content = escape_ampersand_outside_tables(content)

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
