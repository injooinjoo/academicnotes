#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Academic Notes - Utility Functions
공통으로 사용되는 유틸리티 함수 모음
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class ProjectPaths:
    """프로젝트 경로 관리 클래스"""

    def __init__(self, project_root: Optional[Path] = None):
        """
        Args:
            project_root: 프로젝트 루트 경로. None이면 자동 탐지
        """
        if project_root is None:
            # src/ 폴더의 부모 디렉토리를 프로젝트 루트로 설정
            self.root = Path(__file__).parent.parent.absolute()
        else:
            self.root = Path(project_root).absolute()

        self.src = self.root / 'src'
        self.prompts = self.root / 'prompts'
        self.output = self.root / 'output'
        self.school = self.root / 'school'

    def get_course_path(self, university: str, course: str) -> Path:
        """
        특정 과목의 경로를 반환

        Args:
            university: 대학명 (예: 'harvard', 'uiuc')
            course: 과목 코드 (예: 'csci103', 'fin574')

        Returns:
            과목 디렉토리 경로
        """
        return self.school / university / course

    def get_lecture_path(self, university: str, course: str, lecture_num: int) -> Path:
        """
        특정 강의의 경로를 반환

        Args:
            university: 대학명
            course: 과목 코드
            lecture_num: 강의 번호

        Returns:
            강의 디렉토리 경로
        """
        return self.get_course_path(university, course) / f'lecture_{lecture_num:02d}'

    def get_materials_path(self, university: str, course: str, lecture_num: int) -> Path:
        """
        강의 자료 경로를 반환

        Args:
            university: 대학명
            course: 과목 코드
            lecture_num: 강의 번호

        Returns:
            materials 디렉토리 경로
        """
        return self.get_lecture_path(university, course, lecture_num) / 'materials'

    def get_tex_filename(self, course: str, lecture_num: int) -> str:
        """
        LaTeX 파일명 생성

        Args:
            course: 과목 코드
            lecture_num: 강의 번호

        Returns:
            파일명 (예: 'csci103_01.tex')
        """
        return f'{course}_{lecture_num:02d}.tex'

    def get_pdf_filename(self, university: str, course: str, lecture_num: int) -> str:
        """
        PDF 파일명 생성 (output 폴더용)

        Args:
            university: 대학명
            course: 과목 코드
            lecture_num: 강의 번호

        Returns:
            파일명 (예: 'harvard_csci103_01.pdf')
        """
        return f'{university}_{course}_{lecture_num:02d}.pdf'


def find_tex_files(path: Path) -> List[Path]:
    """
    지정된 경로에서 .tex 파일을 찾습니다.

    Args:
        path: 검색할 경로 (파일 또는 디렉토리)

    Returns:
        발견된 .tex 파일 목록
    """
    if path.is_file() and path.suffix == '.tex':
        return [path]
    elif path.is_dir():
        return list(path.glob('*.tex'))
    else:
        print(f"⚠️  경고: '{path}'는 유효한 .tex 파일이나 디렉토리가 아닙니다.")
        return []


def find_xelatex_path() -> str:
    """
    시스템에서 xelatex 실행 파일을 찾습니다.
    TexLive를 우선적으로 사용합니다.

    Returns:
        xelatex 실행 파일 경로 또는 'xelatex'
    """
    # TexLive 경로 (bash 환경에서 안정적)
    texlive_paths = [
        r'C:\texlive\2025\bin\windows\xelatex.exe',
        r'C:\texlive\2024\bin\windows\xelatex.exe',
        r'C:\texlive\2023\bin\windows\xelatex.exe',
    ]

    for path in texlive_paths:
        if Path(path).exists():
            return path

    # MiKTeX 경로
    miktex_path = r'C:\Users\injoo\AppData\Local\Programs\MiKTeX\miktex\bin\x64\xelatex.exe'
    if Path(miktex_path).exists():
        return miktex_path

    # PATH에서 찾기
    return 'xelatex'


def detect_tex_compiler(tex_file: Path) -> str:
    """
    .tex 파일을 분석하여 적절한 컴파일러를 결정합니다.

    Args:
        tex_file: .tex 파일 경로

    Returns:
        컴파일러 경로 또는 이름
    """
    try:
        with open(tex_file, 'r', encoding='utf-8') as f:
            content = f.read(5000)  # 처음 5000자만 확인

            # kotex, xeCJK, fontspec 등이 있으면 xelatex 사용
            if any(pkg in content for pkg in ['\\usepackage{kotex}', '\\usepackage[hangul]{kotex}',
                                               '\\usepackage{xeCJK}', '\\usepackage{fontspec}',
                                               'XeLaTeX', 'xelatex']):
                return find_xelatex_path()

            # luatex 관련 패키지가 있으면 lualatex 사용
            if 'lualatex' in content.lower() or 'luatex' in content.lower():
                return 'lualatex'

    except Exception:
        pass

    # 기본값은 pdflatex
    return 'pdflatex'


def cleanup_aux_files(tex_file: Path) -> List[str]:
    """
    컴파일 후 생성된 보조 파일들을 삭제합니다.

    Args:
        tex_file: .tex 파일 경로

    Returns:
        삭제된 확장자 목록
    """
    aux_extensions = ['.aux', '.log', '.out', '.toc', '.lof', '.lot',
                      '.fls', '.fdb_latexmk', '.synctex.gz', '.xdv']

    cleaned = []
    for ext in aux_extensions:
        aux_file = tex_file.with_suffix(ext)
        if aux_file.exists():
            try:
                aux_file.unlink()
                cleaned.append(ext)
            except Exception:
                pass  # 삭제 실패해도 무시

    return cleaned


def parse_course_code(course_code: str) -> Tuple[str, str]:
    """
    과목 코드에서 대학과 과목을 분리합니다.

    Args:
        course_code: 전체 과목 코드 (예: 'harvard_csci103' 또는 'csci103')

    Returns:
        (university, course) 튜플

    Examples:
        >>> parse_course_code('harvard_csci103')
        ('harvard', 'csci103')
        >>> parse_course_code('csci103')
        ('', 'csci103')
    """
    parts = course_code.split('_')
    if len(parts) >= 2:
        return parts[0], '_'.join(parts[1:])
    else:
        return '', parts[0]


def format_timestamp() -> str:
    """
    현재 시간을 포맷팅된 문자열로 반환

    Returns:
        포맷팅된 시간 문자열 (예: '2024-10-24 15:30:45')
    """
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def print_header(title: str, width: int = 60, char: str = '='):
    """
    헤더를 출력합니다.

    Args:
        title: 헤더 제목
        width: 헤더 너비
        char: 테두리 문자
    """
    print(f"\n{char * width}")
    print(f"{title}")
    print(f"{char * width}")


def print_separator(width: int = 60, char: str = '-'):
    """
    구분선을 출력합니다.

    Args:
        width: 구분선 너비
        char: 구분선 문자
    """
    print(char * width)


if __name__ == '__main__':
    # 테스트 코드
    paths = ProjectPaths()
    print(f"프로젝트 루트: {paths.root}")
    print(f"School 디렉토리: {paths.school}")
    print(f"Output 디렉토리: {paths.output}")

    # 경로 생성 테스트
    print(f"\ncsci103 경로: {paths.get_course_path('harvard', 'csci103')}")
    print(f"Lecture 01 경로: {paths.get_lecture_path('harvard', 'csci103', 1)}")
    print(f"Materials 경로: {paths.get_materials_path('harvard', 'csci103', 1)}")

    # 파일명 생성 테스트
    print(f"\nTeX 파일명: {paths.get_tex_filename('csci103', 1)}")
    print(f"PDF 파일명: {paths.get_pdf_filename('harvard', 'csci103', 1)}")

    # XeLaTeX 경로 찾기
    print(f"\nXeLaTeX 경로: {find_xelatex_path()}")
