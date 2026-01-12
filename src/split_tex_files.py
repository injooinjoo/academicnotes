#!/usr/bin/env python3
"""
LaTeX 파일 분리 스크립트
- \documentclass 경계를 기준으로 여러 개의 완전한 tex 파일로 분리
- Harvard 스타일 디렉토리 구조 생성 (lecture_01/1.tex, lecture_02/2.tex, ...)
"""

import os
import re
from pathlib import Path

def split_tex_file(input_path: str, output_base_dir: str, course_code: str):
    """
    tex 파일을 \documentclass 경계로 분리

    Args:
        input_path: 원본 tex 파일 경로
        output_base_dir: 출력 기본 디렉토리 (예: school/mit/18.6501)
        course_code: 과목 코드 (예: 18.6501)
    """
    print(f"Reading: {input_path}")

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # \documentclass로 분리
    # 패턴: \documentclass로 시작하는 각 문서
    pattern = r'(\\documentclass.*?)(?=\\documentclass|$)'
    documents = re.findall(pattern, content, re.DOTALL)

    print(f"Found {len(documents)} documents in {input_path}")

    # 출력 디렉토리 생성
    output_base = Path(output_base_dir)
    output_base.mkdir(parents=True, exist_ok=True)

    chapter_titles = []

    for i, doc in enumerate(documents, 1):
        # 디렉토리 생성
        lecture_dir = output_base / f"lecture_{i:02d}"
        lecture_dir.mkdir(exist_ok=True)

        # 제목 추출 (Unit/Chapter/Module 등)
        title_match = re.search(r'\\section\{([^}]+)\}', doc)
        if title_match:
            title = title_match.group(1)
        else:
            title_match = re.search(r'\\title\{[^}]*\\textbf\{([^}]+)\}', doc)
            if title_match:
                title = title_match.group(1)
            else:
                title = f"Lecture {i}"

        chapter_titles.append(title)

        # 파일 저장
        output_file = lecture_dir / f"{i}.tex"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(doc.strip())

        print(f"  Created: {output_file} - {title[:50]}...")

    return chapter_titles


def create_unified_tex(output_base_dir: str, course_code: str, course_name: str, chapter_titles: list):
    """
    통합 tex 파일 생성

    Args:
        output_base_dir: 챕터 파일들이 있는 디렉토리
        course_code: 과목 코드
        course_name: 과목 이름
        chapter_titles: 챕터 제목 리스트
    """
    output_base = Path(output_base_dir)
    num_chapters = len(chapter_titles)

    # 통합본 preamble
    unified_content = f'''%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% {course_code}: {course_name} - 통합본
% 자동 생성됨
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\\documentclass[11pt,a4paper]{{book}}

% --- 한국어 지원 ---
\\usepackage{{kotex}}

% --- 페이지 레이아웃 ---
\\usepackage[top=20mm, bottom=20mm, left=20mm, right=18mm]{{geometry}}
\\usepackage{{setspace}}
\\onehalfspacing

% --- 수학 ---
\\usepackage{{amsmath, amssymb, amsthm}}

% --- 표 및 그림 ---
\\usepackage{{booktabs}}
\\usepackage{{tabularx}}
\\usepackage{{graphicx}}

% --- 색상 및 박스 ---
\\usepackage[dvipsnames]{{xcolor}}
\\usepackage[most]{{tcolorbox}}
\\tcbuselibrary{{skins, breakable}}

% 색상 정의
\\definecolor{{mainblue}}{{RGB}}{{0, 51, 102}}
\\definecolor{{subblue}}{{RGB}}{{230, 240, 255}}
\\definecolor{{warningred}}{{RGB}}{{204, 0, 0}}
\\definecolor{{conceptgreen}}{{RGB}}{{0, 102, 51}}
\\definecolor{{storypurple}}{{RGB}}{{102, 0, 102}}

% 박스 스타일
\\newtcolorbox{{summarybox}}[1]{{
  colback=subblue, colframe=mainblue,
  title=\\textbf{{#1}}, fonttitle=\\bfseries,
  boxrule=0.5mm, arc=2mm, breakable
}}

\\newtcolorbox{{warningbox}}[1]{{
  colback=white, colframe=warningred,
  title=\\textbf{{#1}}, fonttitle=\\bfseries,
  boxrule=0.5mm, arc=0mm, breakable
}}

\\newtcolorbox{{conceptbox}}[1]{{
  colback=white, colframe=conceptgreen,
  title=\\textbf{{#1}}, fonttitle=\\bfseries,
  boxrule=0.5mm, arc=2mm, breakable
}}

\\newtcolorbox{{storybox}}[1]{{
  colback=white, colframe=storypurple,
  title=\\textbf{{#1}}, fonttitle=\\bfseries,
  boxrule=0.5mm, arc=2mm, breakable
}}

% --- 하이퍼링크 ---
\\usepackage[
    colorlinks=true,
    linkcolor=blue!80!black,
    urlcolor=blue!80!black,
    bookmarks=true
]{{hyperref}}

% --- 헤더/푸터 ---
\\usepackage{{fancyhdr}}
\\pagestyle{{fancy}}
\\fancyhf{{}}
\\fancyhead[LE,RO]{{\\thepage}}
\\fancyhead[LO]{{\\leftmark}}
\\fancyhead[RE]{{{course_code}}}
\\renewcommand{{\\headrulewidth}}{{0.5pt}}

% --- 제목 ---
\\title{{\\textbf{{{course_code}: {course_name}}}}}
\\author{{통합 강의 노트}}
\\date{{}}

\\begin{{document}}

\\maketitle
\\tableofcontents

'''

    # 각 챕터 포함
    for i, title in enumerate(chapter_titles, 1):
        # 제목에서 불필요한 부분 정리
        clean_title = title.replace('\\textbf{', '').replace('}', '').strip()
        unified_content += f'''
%-----------------------------------------------------------------------
% Chapter {i}
%-----------------------------------------------------------------------
\\chapter{{{clean_title}}}
\\label{{ch:{i}}}

% 내용은 개별 파일에서 직접 복사하거나 \\input 사용
% \\input{{lecture_{i:02d}/{i}_content.tex}}

'''

    unified_content += '''
\\end{document}
'''

    # 통합본 저장
    unified_path = output_base.parent / f"{course_code}_unified.tex"
    with open(unified_path, 'w', encoding='utf-8') as f:
        f.write(unified_content)

    print(f"Created unified file: {unified_path}")
    return unified_path


def process_mit_files():
    """MIT 파일들 처리"""
    base_dir = Path("c:/Dev/academicnotes/school/mit")
    original_dir = base_dir / "original_files"

    courses = [
        ("18.6501.tex", "18.6501", "통계학의 수학적 기초 (Fundamentals of Statistics)"),
        ("6.419.tex", "6.419", "데이터 과학을 위한 통계 (Statistics for Data Science)"),
        ("6.431.tex", "6.431", "확률론 (Probabilistic Systems Analysis)"),
        ("6.86.tex", "6.86", "머신러닝 개론 (Introduction to Machine Learning)"),
    ]

    for filename, code, name in courses:
        input_path = original_dir / filename
        if input_path.exists():
            output_dir = base_dir / code
            print(f"\n{'='*60}")
            print(f"Processing: {code} - {name}")
            print(f"{'='*60}")

            titles = split_tex_file(str(input_path), str(output_dir), code)
            create_unified_tex(str(output_dir), code, name, titles)
        else:
            print(f"File not found: {input_path}")


def process_stanford_files():
    """Stanford 파일들 처리"""
    base_dir = Path("c:/Dev/academicnotes/school/stanford")

    input_path = base_dir / "cs230.tex"
    if input_path.exists():
        output_dir = base_dir / "cs230"
        print(f"\n{'='*60}")
        print(f"Processing: CS230 - Deep Learning")
        print(f"{'='*60}")

        titles = split_tex_file(str(input_path), str(output_dir), "cs230")
        create_unified_tex(str(output_dir), "CS230", "Deep Learning", titles)
    else:
        print(f"File not found: {input_path}")


if __name__ == "__main__":
    print("LaTeX File Splitter")
    print("="*60)

    # MIT 파일 처리
    process_mit_files()

    # Stanford 파일 처리
    process_stanford_files()

    print("\n" + "="*60)
    print("Done!")
