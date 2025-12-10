#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSCI103 Lecture 2의 adjustbox를 개선하는 스크립트
"""

import re
from pathlib import Path

def fix_lecture_02():
    """CSCI103 Lecture 2 파일의 adjustbox를 tabularx로 변환"""
    filepath = Path("school/harvard/csci103/lecture_02/2.tex")

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    i = 0
    changes = 0

    while i < len(lines):
        line = lines[i]

        # adjustbox 시작 찾기
        if '\\adjustbox{max width=\\textwidth}{' in line:
            # 다음 줄에서 tabular 사양 찾기
            next_line = lines[i + 1] if i + 1 < len(lines) else ""

            if '\\begin{tabular}{ll}' in next_line:
                # tabularx로 변경
                new_lines.append(line.replace(
                    '\\adjustbox{max width=\\textwidth}{',
                    ''
                ))
                new_lines.append(next_line.replace(
                    '\\begin{tabular}{ll}',
                    '\\begin{tabularx}{\\textwidth}{lX}'
                ))
                changes += 1
                i += 2
                continue
            elif '\\begin{tabular}{lll}' in next_line:
                # 3컬럼 테이블
                new_lines.append(line.replace(
                    '\\adjustbox{max width=\\textwidth}{',
                    ''
                ))
                new_lines.append(next_line.replace(
                    '\\begin{tabular}{lll}',
                    '\\begin{tabularx}{\\textwidth}{llX}'
                ))
                changes += 1
                i += 2
                continue

        # }\n\end{adjustbox} 패턴 찾기
        if line.strip() == '}' and i + 1 < len(lines) and '\\end{adjustbox}' in lines[i + 1]:
            # tabular 종료로 변경
            prev_line = lines[i - 1] if i > 0 else ""
            if '\\end{tabular}' in prev_line:
                # 이전 줄의 \end{tabular}를 \end{tabularx}로 변경
                new_lines[-1] = new_lines[-1].replace('\\end{tabular}', '\\end{tabularx}')
                # } 줄은 스킵
                i += 1
                # \end{adjustbox} 줄도 스킵
                i += 1
                changes += 1
                continue

        new_lines.append(line)
        i += 1

    # 파일 쓰기
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    return changes

def main():
    """메인 함수"""
    print("=" * 80)
    print("CSCI103 Lecture 2 adjustbox 수정")
    print("=" * 80)

    changes = fix_lecture_02()

    print(f"\n✅ {changes}개의 adjustbox를 tabularx로 변환 완료")
    print("=" * 80)

if __name__ == "__main__":
    import sys
    import io
    # Windows console encoding fix
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    main()
