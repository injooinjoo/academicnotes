#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Academic Notes - LaTeX Error Fixer
LaTeX 파일의 일반적인 컴파일 에러를 자동으로 수정합니다.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import print_header, print_separator


class LaTeXErrorFixer:
    """LaTeX 에러 자동 수정 클래스"""

    def __init__(self, filepath: Path):
        """
        Args:
            filepath: 수정할 .tex 파일 경로
        """
        self.filepath = Path(filepath)
        self.original_content = ""
        self.content = ""
        self.fixes_applied = []

    def read_file(self) -> bool:
        """
        파일을 읽어옵니다.

        Returns:
            성공 여부
        """
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.original_content = f.read()
                self.content = self.original_content
            return True
        except Exception as e:
            print(f"❌ 파일 읽기 실패: {e}")
            return False

    def write_file(self) -> bool:
        """
        수정된 내용을 파일에 씁니다.

        Returns:
            성공 여부
        """
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                f.write(self.content)
            return True
        except Exception as e:
            print(f"❌ 파일 쓰기 실패: {e}")
            return False

    def fix_cite_tags(self):
        """[cite_start], [cite: ...] 등의 태그 제거"""
        patterns = [
            r'\[cite_start\]',
            r'\[cite:\s*[^\]]*\]',
            r'\[cite\]',
        ]

        for pattern in patterns:
            if re.search(pattern, self.content):
                self.content = re.sub(pattern, '', self.content)
                self.fixes_applied.append(f"제거됨: {pattern} 태그")

    def fix_nonexistent_images(self):
        """존재하지 않는 이미지 참조 주석 처리"""
        # \includegraphics 명령 찾기
        image_pattern = r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}'
        matches = list(re.finditer(image_pattern, self.content))

        for match in reversed(matches):  # 뒤에서부터 처리 (인덱스 유지)
            image_path = match.group(1)
            full_path = self.filepath.parent / image_path

            # 확장자가 없으면 일반적인 확장자 시도
            if not full_path.suffix:
                possible_extensions = ['.png', '.jpg', '.jpeg', '.pdf', '.eps']
                exists = any((self.filepath.parent / (image_path + ext)).exists()
                           for ext in possible_extensions)
            else:
                exists = full_path.exists()

            if not exists:
                # 주석 처리
                start, end = match.span()
                original = self.content[start:end]
                commented = f'% {original}  % Image not found: {image_path}'
                self.content = self.content[:start] + commented + self.content[end:]
                self.fixes_applied.append(f"주석 처리됨: 존재하지 않는 이미지 {image_path}")

    def fix_undefined_colors(self):
        """미정의 색상 사용 수정"""
        # xcolor 패키지가 로드되었는지 확인
        has_xcolor = '\\usepackage{xcolor}' in self.content or \
                     '\\usepackage[' in self.content and 'xcolor' in self.content

        if not has_xcolor:
            # xcolor 패키지 추가
            # \documentclass 다음에 추가
            doc_class_pattern = r'(\\documentclass(?:\[[^\]]*\])?\{[^}]+\})'
            if re.search(doc_class_pattern, self.content):
                self.content = re.sub(
                    doc_class_pattern,
                    r'\1\n\\usepackage{xcolor}  % Auto-added for color support',
                    self.content,
                    count=1
                )
                self.fixes_applied.append("추가됨: xcolor 패키지")

        # 미정의 색상을 정의된 색상으로 변경
        color_replacements = {
            r'\\color\{gray\}': r'\\color{black!50}',
            r'\\textcolor\{gray\}': r'\\textcolor{black!50}',
        }

        for old, new in color_replacements.items():
            if re.search(old, self.content):
                self.content = re.sub(old, new, self.content)
                self.fixes_applied.append(f"대체됨: {old} → {new}")

    def fix_backticks(self):
        """백틱(`) 문자를 LaTeX 명령으로 변경"""
        # 코드 블록 외부의 백틱 찾기 (간단한 버전)
        backtick_pattern = r'`([^`]+)`'

        if re.search(backtick_pattern, self.content):
            self.content = re.sub(backtick_pattern, r'\\texttt{\1}', self.content)
            self.fixes_applied.append("변경됨: 백틱(`) → \\texttt{}")

    def fix_markdown_bold(self):
        """마크다운 굵게(**text**) → LaTeX 굵게"""
        bold_pattern = r'\*\*([^*]+)\*\*'

        if re.search(bold_pattern, self.content):
            self.content = re.sub(bold_pattern, r'\\textbf{\1}', self.content)
            self.fixes_applied.append("변경됨: **text** → \\textbf{text}")

    def fix_unclosed_environments(self):
        """닫히지 않은 환경 수정"""
        # 문서 끝 위치 찾기
        doc_end_match = re.search(r'\\end\{document\}', self.content)
        if not doc_end_match:
            return

        doc_end_pos = doc_end_match.start()
        content_before_end = self.content[:doc_end_pos]

        # 확인할 환경 목록
        environments = [
            'warningbox', 'mybox', 'summarybox', 'infobox', 'cautionbox',
            'examplebox', 'itemize', 'enumerate', 'tabular', 'table', 'figure'
        ]

        missing_ends = []

        for env in environments:
            begin_pattern = rf'\\begin\{{{env}\}}'
            end_pattern = rf'\\end\{{{env}\}}'

            opens = len(re.findall(begin_pattern, content_before_end))
            closes = len(re.findall(end_pattern, content_before_end))

            if opens > closes:
                missing_count = opens - closes
                missing_ends.extend([env] * missing_count)

        if missing_ends:
            # 닫히지 않은 환경 닫기
            closing_cmds = '\n'.join([f'\\end{{{env}}}  % Auto-closed' for env in missing_ends])
            insert_text = f'\n% Auto-added missing environment closes:\n{closing_cmds}\n\n'
            self.content = self.content[:doc_end_pos] + insert_text + self.content[doc_end_pos:]
            self.fixes_applied.append(f"닫힘: {len(missing_ends)}개 환경 ({', '.join(set(missing_ends))})")

    def fix_invalid_commands(self):
        """잘못된 LaTeX 명령 수정"""
        # \\end{subsection} 같은 잘못된 명령 제거
        invalid_ends = ['subsection', 'section', 'chapter']

        for cmd in invalid_ends:
            pattern = rf'\\end\{{{cmd}\}}'
            if re.search(pattern, self.content):
                self.content = re.sub(
                    pattern,
                    rf'% \\end{{{cmd}}}  % Invalid command removed',
                    self.content
                )
                self.fixes_applied.append(f"제거됨: 잘못된 \\end{{{cmd}}} 명령")

    def fix_duplicate_commands(self):
        """중복된 명령 제거 (예: 중복된 \\setmonofont)"""
        font_commands = [
            r'\\setmainfont',
            r'\\setsansfont',
            r'\\setmonofont',
            r'\\setCJKmainfont',
            r'\\setCJKsansfont',
            r'\\setCJKmonofont',
        ]

        for cmd in font_commands:
            pattern = rf'{cmd}\{{[^}}]+\}}'
            matches = list(re.finditer(pattern, self.content))

            if len(matches) > 1:
                # 첫 번째를 제외한 나머지 주석 처리
                for match in reversed(matches[1:]):
                    start, end = match.span()
                    original = self.content[start:end]
                    commented = f'% {original}  % Duplicate removed'
                    self.content = self.content[:start] + commented + self.content[end:]

                self.fixes_applied.append(f"제거됨: 중복된 {cmd} 명령 {len(matches)-1}개")

    def fix_font_issues(self):
        """폰트 관련 문제 수정"""
        # Noto Mono → Noto Sans Mono
        if 'Noto Mono' in self.content and 'Noto Sans Mono' not in self.content:
            self.content = self.content.replace('Noto Mono', 'Noto Sans Mono')
            self.fixes_applied.append("대체됨: Noto Mono → Noto Sans Mono")

        # 미지원 hangul 폰트 명령 주석 처리 (xeCJK 없이 사용된 경우)
        if '\\usepackage{xeCJK}' not in self.content and '\\usepackage{kotex}' not in self.content:
            hangul_cmds = [
                r'\\setmainhangulfont',
                r'\\setsanshangulfont',
                r'\\setmonohangulfont',
            ]

            for cmd in hangul_cmds:
                pattern = rf'{cmd}\{{[^}}]+\}}'
                if re.search(pattern, self.content):
                    self.content = re.sub(
                        pattern,
                        lambda m: f'% {m.group(0)}  % Requires xeCJK or kotex',
                        self.content
                    )
                    self.fixes_applied.append(f"주석 처리됨: {cmd} (xeCJK/kotex 필요)")

    def fix_special_characters(self):
        """특수 문자 이스케이프 처리"""
        # 이미 이스케이프되지 않은 특수 문자 찾기 및 수정
        # (너무 공격적이지 않게 제한적으로 적용)

        # URL이나 경로가 아닌 곳의 underscore
        # 예: text_with_underscore (but not in \verb or \texttt or URLs)

        # 이 부분은 매우 조심스럽게 처리해야 하므로, 일단 보수적으로 접근
        pass

    def apply_all_fixes(self):
        """모든 수정 적용"""
        self.fixes_applied = []

        self.fix_cite_tags()
        self.fix_nonexistent_images()
        self.fix_undefined_colors()
        self.fix_backticks()
        self.fix_markdown_bold()
        self.fix_invalid_commands()
        self.fix_duplicate_commands()
        self.fix_font_issues()
        self.fix_unclosed_environments()  # 마지막에 실행
        self.fix_special_characters()

    def has_changes(self) -> bool:
        """내용이 변경되었는지 확인"""
        return self.content != self.original_content

    def get_summary(self) -> str:
        """수정 요약 반환"""
        if not self.fixes_applied:
            return "변경 사항 없음"

        return "\n".join([f"  ✓ {fix}" for fix in self.fixes_applied])


def fix_latex_file(filepath: Path, verbose: bool = True) -> bool:
    """
    LaTeX 파일의 에러를 수정합니다.

    Args:
        filepath: 수정할 .tex 파일 경로
        verbose: 상세 출력 여부

    Returns:
        수정 여부 (True: 수정됨, False: 변경 없음)
    """
    if verbose:
        print(f"\n처리 중: {filepath.name}")

    fixer = LaTeXErrorFixer(filepath)

    if not fixer.read_file():
        return False

    fixer.apply_all_fixes()

    if fixer.has_changes():
        if fixer.write_file():
            if verbose:
                print(f"✅ 수정 완료:")
                print(fixer.get_summary())
            return True
        else:
            return False
    else:
        if verbose:
            print(f"   변경 사항 없음")
        return False


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(
        description='LaTeX 파일의 일반적인 컴파일 에러를 자동으로 수정합니다.'
    )
    parser.add_argument(
        'path',
        type=str,
        nargs='?',
        default='.',
        help='수정할 .tex 파일 또는 디렉토리 경로 (기본값: 현재 디렉토리)'
    )
    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        help='하위 디렉토리까지 재귀적으로 검색'
    )

    args = parser.parse_args()

    print_header("📝 LaTeX Error Fixer", width=70)

    target_path = Path(args.path)

    # .tex 파일 찾기
    if target_path.is_file() and target_path.suffix == '.tex':
        tex_files = [target_path]
    elif target_path.is_dir():
        if args.recursive:
            tex_files = list(target_path.rglob('*.tex'))
        else:
            tex_files = list(target_path.glob('*.tex'))
    else:
        print(f"❌ 오류: '{target_path}'는 유효한 .tex 파일이나 디렉토리가 아닙니다.")
        return 1

    if not tex_files:
        print(f"\n⚠️  '{target_path}'에서 .tex 파일을 찾을 수 없습니다.")
        return 1

    print(f"\n발견된 .tex 파일: {len(tex_files)}개")
    print_separator(width=70)

    # 각 파일 수정
    fixed_count = 0
    for tex_file in sorted(tex_files):
        if fix_latex_file(tex_file):
            fixed_count += 1

    # 결과 요약
    print_separator(width=70)
    print(f"\n📊 수정 완료: {fixed_count}/{len(tex_files)}개 파일")

    return 0


if __name__ == '__main__':
    sys.exit(main())
