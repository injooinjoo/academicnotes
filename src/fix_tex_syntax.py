#!/usr/bin/env python3
"""
LaTeX 문법 오류 수정 스크립트
- **text** → \textbf{text} 변환
- tabularx 사용 시 패키지 추가
- 기타 문법 오류 수정
"""

import re
from pathlib import Path


def fix_markdown_bold(content: str) -> str:
    """**text** → \textbf{text} 변환"""
    # **text** 패턴을 \textbf{text}로 변환
    # 단, 이미 \textbf 안에 있거나 수식 안의 ** (지수)는 제외

    def replace_bold(match):
        text = match.group(1)
        return f'\\textbf{{{text}}}'

    # **로 시작하고 **로 끝나는 텍스트 (최소 매칭)
    content = re.sub(r'\*\*([^*]+)\*\*', replace_bold, content)

    return content


def ensure_tabularx_package(content: str) -> str:
    """tabularx 환경 사용 시 패키지 추가"""
    # tabularx를 사용하는지 확인
    if '\\begin{tabularx}' not in content:
        return content

    # 이미 tabularx 패키지가 있으면 패스
    if '\\usepackage{tabularx}' in content or 'usepackage[' in content and 'tabularx' in content:
        return content

    # booktabs 뒤에 추가하거나, geometry 뒤에 추가
    if '\\usepackage{booktabs}' in content:
        content = content.replace(
            '\\usepackage{booktabs}',
            '\\usepackage{booktabs}\n\\usepackage{tabularx}'
        )
    elif '\\usepackage{geometry}' in content:
        content = content.replace(
            '\\usepackage{geometry}',
            '\\usepackage{geometry}\n\\usepackage{tabularx}'
        )
    else:
        # documentclass 다음에 추가
        content = re.sub(
            r'(\\documentclass[^\n]*\n)',
            r'\1\\usepackage{tabularx}\n',
            content
        )

    return content


def fix_hline_in_tabularx(content: str) -> str:
    """tabularx에서 \hline 대신 booktabs 명령어 사용"""
    # tabularx 환경 내의 \hline을 \midrule로 변환
    # 첫 번째 \hline은 \toprule, 마지막은 \bottomrule

    def fix_tabularx_block(match):
        block = match.group(0)
        # 첫 번째 \hline → \toprule
        block = re.sub(r'\\hline\s*\n', '\\toprule\n', block, count=1)
        # 마지막 \hline → \bottomrule (역순으로)
        lines = block.split('\n')
        for i in range(len(lines)-1, -1, -1):
            if '\\hline' in lines[i]:
                lines[i] = lines[i].replace('\\hline', '\\bottomrule')
                break
        block = '\n'.join(lines)
        # 나머지 \hline → \midrule
        block = block.replace('\\hline', '\\midrule')
        return block

    content = re.sub(
        r'\\begin\{tabularx\}.*?\\end\{tabularx\}',
        fix_tabularx_block,
        content,
        flags=re.DOTALL
    )

    return content


def fix_triple_dash(content: str) -> str:
    """--- (마크다운 구분선) → \hrule 또는 제거"""
    # 단독 줄의 --- 제거 또는 \hrule로 변환
    content = re.sub(r'\n---\n', '\n\\\\vspace{0.5cm}\\\\hrule\\\\vspace{0.5cm}\n', content)
    return content


def add_breakable_to_tcolorbox(content: str) -> str:
    """tcolorbox에 breakable 옵션 추가"""
    # 이미 breakable이 있으면 패스
    if 'breakable' in content:
        return content

    # tcbuselibrary가 있으면 breakable 추가
    if '\\tcbuselibrary{' in content:
        content = re.sub(
            r'\\tcbuselibrary\{([^}]+)\}',
            lambda m: f'\\tcbuselibrary{{{m.group(1)}, breakable}}' if 'breakable' not in m.group(1) else m.group(0),
            content
        )
    elif '\\usepackage[most]{tcolorbox}' in content:
        content = content.replace(
            '\\usepackage[most]{tcolorbox}',
            '\\usepackage[most]{tcolorbox}\n\\tcbuselibrary{breakable}'
        )
    elif '\\usepackage{tcolorbox}' in content:
        content = content.replace(
            '\\usepackage{tcolorbox}',
            '\\usepackage[most]{tcolorbox}\n\\tcbuselibrary{breakable}'
        )

    return content


def fix_tex_file(file_path: Path) -> bool:
    """단일 tex 파일 수정"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content

        # 1. **text** → \textbf{text}
        content = fix_markdown_bold(content)

        # 2. tabularx 패키지 확인
        content = ensure_tabularx_package(content)

        # 3. --- 구분선 수정
        content = fix_triple_dash(content)

        # 4. tcolorbox breakable 추가
        content = add_breakable_to_tcolorbox(content)

        # 변경사항이 있으면 저장
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

    schools = ["mit", "stanford", "harvard", "uiuc"]

    total = 0
    modified = 0

    for school in schools:
        school_dir = base_dir / school
        if not school_dir.exists():
            continue

        print(f"\n{'='*60}")
        print(f"Processing: {school.upper()}")
        print(f"{'='*60}")

        for tex_file in school_dir.rglob("*.tex"):
            # unified 파일은 건너뜀
            if '_unified' in tex_file.name:
                continue
            total += 1
            if fix_tex_file(tex_file):
                print(f"  Fixed: {tex_file.relative_to(base_dir)}")
                modified += 1

    print(f"\n{'='*60}")
    print(f"Summary: Fixed {modified}/{total} files")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
