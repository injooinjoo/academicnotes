#!/usr/bin/env python3
"""
전체 LaTeX 파일 수정 스크립트
- 테이블 오버플로우 수정 (p{0.3}|p{0.65} → adjustbox 또는 너비 축소)
- 중복 preamble 제거
- 통합본 재생성 (실제 내용 포함)
"""

import os
import re
from pathlib import Path


def fix_table_widths(content: str) -> str:
    """
    테이블 너비 오버플로우 수정
    - p{0.3\textwidth}|p{0.65\textwidth} → p{0.28\textwidth}|X (tabularx)
    - 테두리 포함 시 총합 0.9 이하로 조정
    """
    # 패턴 1: p{0.3\textwidth}|p{0.65\textwidth} (합계 0.95)
    content = re.sub(
        r'\\begin\{tabular\}\{\|p\{0\.3\\textwidth\}\|p\{0\.65\\textwidth\}\|\}',
        r'\\begin{tabularx}{\\textwidth}{|p{0.28\\textwidth}|X|}',
        content
    )
    content = re.sub(
        r'\\begin\{tabular\}\{p\{0\.3\\textwidth\}\|p\{0\.65\\textwidth\}\}',
        r'\\begin{tabularx}{\\textwidth}{p{0.28\\textwidth}|X}',
        content
    )

    # 패턴 2: 0.4 + 0.6 = 1.0 (테두리로 오버플로우)
    content = re.sub(
        r'\\begin\{tabular\}\{\|p\{0\.4\\textwidth\}\|p\{0\.6\\textwidth\}\|\}',
        r'\\begin{tabularx}{\\textwidth}{|p{0.35\\textwidth}|X|}',
        content
    )

    # 패턴 3: 세 개 이상 컬럼
    content = re.sub(
        r'\\begin\{tabular\}\{\|p\{0\.25\\textwidth\}\|p\{0\.25\\textwidth\}\|p\{0\.5\\textwidth\}\|\}',
        r'\\begin{tabularx}{\\textwidth}{|p{0.2\\textwidth}|p{0.2\\textwidth}|X|}',
        content
    )

    # tabular → tabularx 로 변환 후 \end{tabular} → \end{tabularx}
    # 주의: 모든 tabular를 변환하지 않고, 위에서 변환된 것만 처리
    lines = content.split('\n')
    result = []
    in_tabularx = False

    for line in lines:
        if '\\begin{tabularx}' in line:
            in_tabularx = True
        if in_tabularx and '\\end{tabular}' in line:
            line = line.replace('\\end{tabular}', '\\end{tabularx}')
            in_tabularx = False
        result.append(line)

    return '\n'.join(result)


def remove_duplicate_geometry(content: str) -> str:
    """
    본문 내 중복 \geometry 선언 제거
    - preamble의 첫 번째 \geometry만 유지
    - \begin{document} 이후의 \geometry 모두 제거
    """
    # \begin{document} 위치 찾기
    doc_start = content.find('\\begin{document}')
    if doc_start == -1:
        return content

    # 본문에서 \geometry 제거
    preamble = content[:doc_start]
    body = content[doc_start:]

    # 본문의 \geometry 라인 제거
    body = re.sub(r'\\geometry\{[^}]*\}\n?', '', body)

    return preamble + body


def remove_duplicate_usepackage_in_body(content: str) -> str:
    """
    본문 내 중복 usepackage 선언 제거
    """
    doc_start = content.find('\\begin{document}')
    if doc_start == -1:
        return content

    preamble = content[:doc_start]
    body = content[doc_start:]

    # 본문의 \usepackage 라인 제거
    body = re.sub(r'\\usepackage(\[[^\]]*\])?\{[^}]*\}\n?', '', body)

    return preamble + body


def ensure_breaklines_in_lstset(content: str) -> str:
    """
    lstset에 breaklines=true 확인
    """
    # 이미 breaklines=true가 있으면 패스
    if 'breaklines=true' in content:
        return content

    # lstset 내에 breaklines 추가
    content = re.sub(
        r'(\\lstset\{[^}]*)(frame=single)',
        r'\1breaklines=true,\n    \2',
        content
    )

    return content


def fix_lstlisting_options(content: str) -> str:
    """
    개별 lstlisting 환경에 breaklines=true 추가
    """
    # \begin{lstlisting} 에 옵션이 없는 경우
    content = re.sub(
        r'\\begin\{lstlisting\}(?!\[)',
        r'\\begin{lstlisting}[breaklines=true]',
        content
    )

    # 이미 옵션이 있지만 breaklines가 없는 경우
    def add_breaklines(match):
        options = match.group(1)
        if 'breaklines' not in options:
            return f'\\begin{{lstlisting}}[{options}, breaklines=true]'
        return match.group(0)

    content = re.sub(
        r'\\begin\{lstlisting\}\[([^\]]+)\]',
        add_breaklines,
        content
    )

    return content


def add_adjustbox_to_wide_tables(content: str) -> str:
    """
    넓은 테이블에 adjustbox 래핑 추가
    """
    # longtable이나 tabularx가 아닌 일반 tabular에 adjustbox 적용
    # 이미 adjustbox로 감싸진 경우 스킵

    def wrap_with_adjustbox(match):
        full_match = match.group(0)
        # 이미 adjustbox로 감싸져 있으면 스킵
        if '\\begin{adjustbox}' in full_match or '\\adjustbox{' in full_match:
            return full_match
        # tabularx나 longtable이면 스킵 (이미 자동 조절됨)
        if 'tabularx' in full_match or 'longtable' in full_match:
            return full_match

        # 테이블 내용 추출
        table_content = match.group(1)
        end_part = match.group(2)

        return f'\\begin{{adjustbox}}{{max width=\\textwidth}}\n{table_content}{end_part}\n\\end{{adjustbox}}'

    # 패턴: \begin{tabular}...\end{tabular}
    # 주의: 중첩 가능성 때문에 간단한 케이스만 처리
    content = re.sub(
        r'(\\begin\{tabular\}\{[^}]+\}.*?)(\\end\{tabular\})',
        wrap_with_adjustbox,
        content,
        flags=re.DOTALL
    )

    return content


def ensure_adjustbox_package(content: str) -> str:
    """
    adjustbox 패키지가 없으면 추가
    """
    if '\\usepackage{adjustbox}' in content:
        return content

    # graphicx 뒤에 추가
    if '\\usepackage{graphicx}' in content:
        content = content.replace(
            '\\usepackage{graphicx}',
            '\\usepackage{graphicx}\n\\usepackage{adjustbox}  % 표/박스 크기 조절'
        )
    # 또는 geometry 뒤에 추가
    elif '\\usepackage{geometry}' in content or '\\usepackage[' in content:
        # preamble 끝 부분에 추가
        doc_start = content.find('\\begin{document}')
        if doc_start != -1:
            preamble = content[:doc_start]
            body = content[doc_start:]
            if '\\usepackage{adjustbox}' not in preamble:
                preamble = preamble.rstrip() + '\n\\usepackage{adjustbox}  % 표/박스 크기 조절\n\n'
                content = preamble + body

    return content


def fix_tex_file(file_path: Path) -> bool:
    """
    단일 tex 파일 수정
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content

        # 1. 테이블 너비 수정
        content = fix_table_widths(content)

        # 2. 중복 geometry 제거
        content = remove_duplicate_geometry(content)

        # 3. 본문 내 중복 usepackage 제거
        content = remove_duplicate_usepackage_in_body(content)

        # 4. breaklines 확인
        content = ensure_breaklines_in_lstset(content)
        content = fix_lstlisting_options(content)

        # 5. adjustbox 패키지 확인
        content = ensure_adjustbox_package(content)

        # 변경된 경우만 저장
        if content != original:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def process_all_tex_files():
    """
    모든 tex 파일 처리
    """
    base_dir = Path("c:/Dev/academicnotes/school")

    schools = ["mit", "stanford", "harvard", "uiuc"]

    total_files = 0
    modified_files = 0

    for school in schools:
        school_dir = base_dir / school
        if not school_dir.exists():
            continue

        print(f"\n{'='*60}")
        print(f"Processing: {school.upper()}")
        print(f"{'='*60}")

        # 모든 tex 파일 찾기
        for tex_file in school_dir.rglob("*.tex"):
            total_files += 1
            if fix_tex_file(tex_file):
                print(f"  Modified: {tex_file.relative_to(base_dir)}")
                modified_files += 1

    print(f"\n{'='*60}")
    print(f"Summary: Modified {modified_files}/{total_files} files")
    print(f"{'='*60}")


if __name__ == "__main__":
    process_all_tex_files()
