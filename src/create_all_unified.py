#!/usr/bin/env python3
"""
모든 학교의 통합본 생성 스크립트
- MIT, Stanford, Harvard, UIUC 통합본 생성
- 각 챕터별 tex 파일에서 본문만 추출하여 하나의 book 문서로 생성
"""

import os
import re
from pathlib import Path


def extract_document_body(tex_content: str) -> str:
    """
    tex 파일에서 \\begin{document}와 \\end{document} 사이의 내용 추출
    """
    match = re.search(r'\\begin\{document\}(.*?)\\end\{document\}', tex_content, re.DOTALL)
    if match:
        body = match.group(1).strip()
        # \maketitle, \tableofcontents 등 제거
        body = re.sub(r'\\maketitle', '', body)
        body = re.sub(r'\\tableofcontents', '', body)
        body = re.sub(r'\\thispagestyle\{[^}]*\}', '', body)
        body = re.sub(r'\\newpage\s*(?=\n|$)', '', body)  # 문서 시작 부분의 newpage만 제거
        # 빈 줄 정리
        body = re.sub(r'\n{4,}', '\n\n\n', body)
        return body.strip()
    return ""


def extract_lecture_title(tex_content: str, lecture_num: int) -> str:
    """강의 제목 추출"""
    # \title{...\textbf{...}} 에서 추출
    title_match = re.search(r'\\title\{[^}]*\\textbf\{([^}]+)\}', tex_content)
    if title_match:
        return title_match.group(1).strip()

    # \title{...} 에서 추출
    title_match = re.search(r'\\title\{([^}]+)\}', tex_content)
    if title_match:
        title = title_match.group(1).strip()
        # 불필요한 LaTeX 명령어 제거
        title = re.sub(r'\\textbf\{([^}]+)\}', r'\1', title)
        title = re.sub(r'\\Large', '', title)
        return title.strip()

    # 첫 번째 \section{...} 에서 추출 (단, preamble의 \newcommand 내부는 제외)
    # \begin{document} 이후의 내용에서만 검색
    doc_start = tex_content.find('\\begin{document}')
    if doc_start != -1:
        body = tex_content[doc_start:]
        section_match = re.search(r'\\section\*?\{([^}#]+)\}', body)
        if section_match:
            title = section_match.group(1).strip()
            if title and len(title) > 2:  # 의미있는 제목인지 확인
                return title

    return f"Lecture {lecture_num}"


def get_unified_preamble(course_code: str, course_name: str) -> str:
    """통합본용 preamble 생성"""
    return f'''%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% {course_code}: {course_name} - 통합본
% 자동 생성됨
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\\documentclass[11pt,a4paper]{{book}}

%========================================================================================
% 기본 패키지
%========================================================================================

\\usepackage{{kotex}}
\\usepackage[top=20mm, bottom=20mm, left=20mm, right=18mm]{{geometry}}
\\usepackage{{setspace}}
\\onehalfspacing
\\setlength{{\\parskip}}{{0.5em}}
\\setlength{{\\parindent}}{{0pt}}

% --- 표 관련 ---
\\usepackage{{booktabs}}
\\usepackage{{tabularx}}
\\usepackage{{array}}
\\usepackage{{longtable}}
\\usepackage{{adjustbox}}
\\renewcommand{{\\arraystretch}}{{1.1}}

%========================================================================================
% 헤더 및 푸터
%========================================================================================

\\usepackage{{fancyhdr}}
\\pagestyle{{fancy}}
\\fancyhf{{}}
\\fancyhead[LE,RO]{{\\thepage}}
\\fancyhead[LO]{{\\leftmark}}
\\fancyhead[RE]{{{course_code}}}
\\renewcommand{{\\headrulewidth}}{{0.5pt}}
\\renewcommand{{\\footrulewidth}}{{0.3pt}}

%========================================================================================
% 색상 정의
%========================================================================================

\\usepackage[dvipsnames]{{xcolor}}

\\definecolor{{lightblue}}{{RGB}}{{220, 235, 255}}
\\definecolor{{lightgreen}}{{RGB}}{{220, 255, 235}}
\\definecolor{{lightyellow}}{{RGB}}{{255, 250, 220}}
\\definecolor{{lightpurple}}{{RGB}}{{240, 230, 255}}
\\definecolor{{lightgray}}{{gray}}{{0.95}}
\\definecolor{{lightpink}}{{RGB}}{{255, 235, 245}}
\\definecolor{{boxgray}}{{gray}}{{0.95}}
\\definecolor{{boxblue}}{{rgb}}{{0.9, 0.95, 1.0}}
\\definecolor{{boxred}}{{rgb}}{{1.0, 0.95, 0.95}}

\\definecolor{{darkblue}}{{RGB}}{{50, 80, 150}}
\\definecolor{{darkgreen}}{{RGB}}{{40, 120, 70}}
\\definecolor{{darkorange}}{{RGB}}{{200, 100, 30}}
\\definecolor{{darkpurple}}{{RGB}}{{100, 60, 150}}

% Stanford CS230 스타일 색상
\\definecolor{{sblue}}{{RGB}}{{70, 130, 180}}
\\definecolor{{wgray}}{{RGB}}{{245, 245, 245}}
\\definecolor{{codegreen}}{{rgb}}{{0,0.6,0}}
\\definecolor{{codegray}}{{rgb}}{{0.5,0.5,0.5}}
\\definecolor{{codepurple}}{{rgb}}{{0.58,0,0.82}}
\\definecolor{{backcolour}}{{rgb}}{{0.95,0.95,0.92}}

%========================================================================================
% 박스 환경
%========================================================================================

\\usepackage[most]{{tcolorbox}}
\\tcbuselibrary{{skins, breakable}}

\\newtcolorbox{{overviewbox}}[1][]{{
    enhanced,
    colback=lightpurple,
    colframe=darkpurple,
    fonttitle=\\bfseries\\large,
    title=강의 개요,
    arc=3mm,
    boxrule=1pt,
    breakable,
    #1
}}

\\newtcolorbox{{summarybox}}[1][]{{
    enhanced,
    colback=lightblue,
    colframe=darkblue,
    fonttitle=\\bfseries,
    title=#1,
    arc=2mm,
    boxrule=0.7pt,
    breakable
}}

\\newtcolorbox{{infobox}}[1][]{{
    enhanced,
    colback=lightgreen,
    colframe=darkgreen,
    fonttitle=\\bfseries,
    title=핵심 정보,
    arc=2mm,
    boxrule=0.7pt,
    breakable,
    #1
}}

\\newtcolorbox{{warningbox}}[1][]{{
    enhanced,
    colback=lightyellow,
    colframe=darkorange,
    fonttitle=\\bfseries,
    title=#1,
    arc=2mm,
    boxrule=0.7pt,
    breakable
}}

\\newtcolorbox{{examplebox}}[1][]{{
    enhanced,
    colback=lightgray,
    colframe=black!60,
    fonttitle=\\bfseries,
    title=#1,
    arc=2mm,
    boxrule=0.7pt,
    breakable
}}

\\newtcolorbox{{definitionbox}}[1][]{{
    enhanced,
    colback=lightpink,
    colframe=purple!70!black,
    fonttitle=\\bfseries,
    title=#1,
    arc=2mm,
    boxrule=0.7pt,
    breakable
}}

\\newtcolorbox{{importantbox}}[1][]{{
    enhanced,
    colback=boxred,
    colframe=red!70!black,
    fonttitle=\\bfseries,
    title=#1,
    arc=2mm,
    boxrule=0.7pt,
    breakable
}}

\\newtcolorbox{{conceptbox}}[1][]{{
    enhanced,
    colback=lightgreen,
    colframe=darkgreen,
    fonttitle=\\bfseries,
    title=#1,
    arc=2mm,
    boxrule=0.7pt,
    breakable
}}

\\newtcolorbox{{analogybox}}[1][]{{
    enhanced,
    colback=green!5!white,
    colframe=green!60!black,
    fonttitle=\\bfseries,
    title=#1,
    arc=2mm,
    boxrule=0.7pt,
    breakable
}}

\\let\\cautionbox\\warningbox
\\let\\endcautionbox\\endwarningbox

% mybox 환경 (UIUC용)
\\newtcolorbox{{mybox}}[1]{{
    enhanced,
    colback=lightblue,
    colframe=darkblue,
    fonttitle=\\bfseries,
    title=#1,
    arc=2mm,
    boxrule=0.7pt,
    breakable
}}

%========================================================================================
% 코드 블록
%========================================================================================

\\usepackage{{listings}}

\\lstdefinestyle{{mystyle}}{{
    backgroundcolor=\\color{{backcolour}},
    commentstyle=\\color{{codegreen}},
    keywordstyle=\\color{{magenta}},
    numberstyle=\\tiny\\color{{codegray}},
    stringstyle=\\color{{codepurple}},
    basicstyle=\\ttfamily\\footnotesize,
    breakatwhitespace=false,
    breaklines=true,
    captionpos=b,
    keepspaces=true,
    numbers=left,
    numbersep=5pt,
    showspaces=false,
    showstringspaces=false,
    showtabs=false,
    tabsize=2
}}

\\lstset{{
    style=mystyle,
    basicstyle=\\ttfamily\\small,
    backgroundcolor=\\color{{lightgray}},
    keywordstyle=\\color{{darkblue}}\\bfseries,
    commentstyle=\\color{{darkgreen}}\\itshape,
    stringstyle=\\color{{purple!80!black}},
    numberstyle=\\tiny\\color{{black!60}},
    numbers=left,
    numbersep=8pt,
    breaklines=true,
    frame=single,
    frameround=tttt,
    rulecolor=\\color{{black!30}},
    showstringspaces=false,
    tabsize=2,
    xleftmargin=15pt,
    xrightmargin=5pt
}}

%========================================================================================
% 수학
%========================================================================================

\\usepackage{{amsmath, amssymb, amsthm, amsfonts}}

\\theoremstyle{{definition}}
\\newtheorem{{theorem}}{{정리}}[chapter]
\\newtheorem{{lemma}}[theorem]{{보조정리}}
\\newtheorem{{proposition}}[theorem]{{명제}}
\\newtheorem{{corollary}}[theorem]{{따름정리}}
\\newtheorem{{definition}}{{정의}}[chapter]
\\newtheorem{{example}}{{예제}}[chapter]

%========================================================================================
% 하이퍼링크
%========================================================================================

\\usepackage[
    colorlinks=true,
    linkcolor=blue!80!black,
    urlcolor=blue!80!black,
    bookmarks=true,
    bookmarksnumbered=true
]{{hyperref}}

%========================================================================================
% 기타
%========================================================================================

\\usepackage{{enumitem}}
\\setlist{{nosep, leftmargin=*, itemsep=0.3em}}

\\usepackage{{microtype}}
\\usepackage{{graphicx}}
\\usepackage{{url}}
\\urlstyle{{same}}

%========================================================================================
% 메타 정보 박스 명령어
%========================================================================================

\\newcommand{{\\metainfo}}[4]{{
\\begin{{tcolorbox}}[
    colback=lightpurple,
    colframe=darkpurple,
    boxrule=1pt,
    arc=2mm,
    left=10pt,
    right=10pt,
    top=8pt,
    bottom=8pt
]
\\begin{{tabular}}{{@{{}}rl@{{}}}}
\\textbf{{강의명:}} & #1 \\\\[0.3em]
\\textbf{{주차:}} & #2 \\\\[0.3em]
\\textbf{{교수명:}} & #3 \\\\[0.3em]
\\textbf{{목적:}} & \\begin{{minipage}}[t]{{0.75\\textwidth}}#4\\end{{minipage}}
\\end{{tabular}}
\\end{{tcolorbox}}
}}

%========================================================================================
% 문서 시작
%========================================================================================

\\title{{\\textbf{{{course_code}: {course_name}}}}}
\\author{{통합 강의 노트}}
\\date{{}}

\\begin{{document}}

\\maketitle
\\tableofcontents

'''


def create_unified_mit(course_code: str, course_name: str, num_lectures: int):
    """MIT 통합본 생성"""
    base_dir = Path("c:/Dev/academicnotes/school/mit")
    course_dir = base_dir / course_code

    print(f"\n{'='*60}")
    print(f"Creating: {course_code} - {course_name}")
    print(f"{'='*60}")

    unified_content = get_unified_preamble(course_code, course_name)

    for i in range(1, num_lectures + 1):
        tex_file = course_dir / f"lecture_{i:02d}" / f"{i}.tex"
        if tex_file.exists():
            print(f"  Processing: {tex_file.name}")
            with open(tex_file, 'r', encoding='utf-8') as f:
                content = f.read()

            title = extract_lecture_title(content, i)
            body = extract_document_body(content)

            if body:
                unified_content += f'''
%=======================================================================
% Lecture {i}: {title}
%=======================================================================
\\chapter{{{title}}}
\\label{{ch:lecture{i}}}

{body}

'''
        else:
            print(f"  File not found: {tex_file}")

    unified_content += '''
\\end{document}
'''

    # 저장
    unified_path = base_dir / f"{course_code}_unified.tex"
    with open(unified_path, 'w', encoding='utf-8') as f:
        f.write(unified_content)

    print(f"Created: {unified_path}")
    return unified_path


def create_unified_stanford():
    """Stanford CS230 통합본 생성"""
    base_dir = Path("c:/Dev/academicnotes/school/stanford")
    course_dir = base_dir / "cs230"

    print(f"\n{'='*60}")
    print(f"Creating: CS230 - Deep Learning")
    print(f"{'='*60}")

    unified_content = get_unified_preamble("CS230", "Deep Learning")

    for i in range(1, 52):  # 51개 강의
        tex_file = course_dir / f"lecture_{i:02d}" / f"{i}.tex"
        if tex_file.exists():
            print(f"  Processing: {tex_file.name}")
            with open(tex_file, 'r', encoding='utf-8') as f:
                content = f.read()

            title = extract_lecture_title(content, i)
            body = extract_document_body(content)

            if body:
                unified_content += f'''
%=======================================================================
% Lecture {i}: {title}
%=======================================================================
\\chapter{{{title}}}
\\label{{ch:lecture{i}}}

{body}

'''
        else:
            print(f"  File not found: {tex_file}")

    unified_content += '''
\\end{document}
'''

    unified_path = base_dir / "CS230_unified.tex"
    with open(unified_path, 'w', encoding='utf-8') as f:
        f.write(unified_content)

    print(f"Created: {unified_path}")
    return unified_path


def create_unified_harvard(course_dir_name: str, course_code: str, course_name: str, num_lectures: int):
    """Harvard 통합본 생성"""
    base_dir = Path("c:/Dev/academicnotes/school/harvard")
    course_dir = base_dir / course_dir_name

    print(f"\n{'='*60}")
    print(f"Creating: {course_code} - {course_name}")
    print(f"{'='*60}")

    unified_content = get_unified_preamble(course_code, course_name)

    for i in range(1, num_lectures + 1):
        tex_file = course_dir / f"lecture_{i:02d}" / f"{i}.tex"
        if tex_file.exists():
            print(f"  Processing: {tex_file.name}")
            with open(tex_file, 'r', encoding='utf-8') as f:
                content = f.read()

            title = extract_lecture_title(content, i)
            body = extract_document_body(content)

            if body:
                unified_content += f'''
%=======================================================================
% Lecture {i}: {title}
%=======================================================================
\\chapter{{{title}}}
\\label{{ch:lecture{i}}}

{body}

'''
        else:
            print(f"  File not found: {tex_file}")

    unified_content += '''
\\end{document}
'''

    unified_path = course_dir / f"{course_code}_unified.tex"
    with open(unified_path, 'w', encoding='utf-8') as f:
        f.write(unified_content)

    print(f"Created: {unified_path}")
    return unified_path


def create_unified_csci89():
    """CSCI89 통합본 생성 (파일명 혼재 처리)"""
    base_dir = Path("c:/Dev/academicnotes/school/harvard")
    course_dir = base_dir / "csci89"

    print(f"\n{'='*60}")
    print(f"Creating: CSCI89 - Introduction to NLP")
    print(f"{'='*60}")

    unified_content = get_unified_preamble("CSCI89", "Introduction to NLP")

    # 파일 매핑 (lecture 1-8: csci89_XX.tex, 9-13: X.tex)
    file_mappings = []
    for i in range(1, 9):
        file_mappings.append((i, f"lecture_{i:02d}", f"csci89_{i:02d}.tex"))
    for i in range(9, 14):
        file_mappings.append((i, f"lecture_{i:02d}", f"{i}.tex"))

    for lecture_num, dir_name, filename in file_mappings:
        tex_file = course_dir / dir_name / filename
        if tex_file.exists():
            print(f"  Processing: {filename}")
            with open(tex_file, 'r', encoding='utf-8') as f:
                content = f.read()

            title = extract_lecture_title(content, lecture_num)
            body = extract_document_body(content)

            if body:
                unified_content += f'''
%=======================================================================
% Lecture {lecture_num}: {title}
%=======================================================================
\\chapter{{{title}}}
\\label{{ch:lecture{lecture_num}}}

{body}

'''
        else:
            print(f"  File not found: {tex_file}")

    unified_content += '''
\\end{document}
'''

    unified_path = course_dir / "CSCI89_unified.tex"
    with open(unified_path, 'w', encoding='utf-8') as f:
        f.write(unified_content)

    print(f"Created: {unified_path}")
    return unified_path


def create_unified_uiuc():
    """UIUC FIN574 통합본 생성"""
    base_dir = Path("c:/Dev/academicnotes/school/uiuc")
    course_dir = base_dir / "fin-574"

    print(f"\n{'='*60}")
    print(f"Creating: FIN574 - Firm Level Economics")
    print(f"{'='*60}")

    unified_content = get_unified_preamble("FIN574", "Firm Level Economics")

    for i in range(1, 3):  # 2개 강의
        tex_file = course_dir / f"lecture_{i:02d}" / f"fin574_{i:02d}.tex"
        if tex_file.exists():
            print(f"  Processing: fin574_{i:02d}.tex")
            with open(tex_file, 'r', encoding='utf-8') as f:
                content = f.read()

            title = extract_lecture_title(content, i)
            body = extract_document_body(content)

            if body:
                unified_content += f'''
%=======================================================================
% Lecture {i}: {title}
%=======================================================================
\\chapter{{{title}}}
\\label{{ch:lecture{i}}}

{body}

'''
        else:
            print(f"  File not found: {tex_file}")

    unified_content += '''
\\end{document}
'''

    unified_path = course_dir / "FIN574_unified.tex"
    with open(unified_path, 'w', encoding='utf-8') as f:
        f.write(unified_content)

    print(f"Created: {unified_path}")
    return unified_path


def main():
    print("=" * 70)
    print("Creating All Unified LaTeX Files")
    print("=" * 70)

    # MIT
    mit_courses = [
        ("18.6501", "Fundamentals of Statistics", 12),
        ("6.419", "Statistics for Data Science", 12),
        ("6.431", "Probabilistic Systems Analysis", 9),
        ("6.86", "Introduction to Machine Learning", 14),
    ]
    for code, name, num in mit_courses:
        create_unified_mit(code, name, num)

    # Stanford
    create_unified_stanford()

    # Harvard
    create_unified_harvard("cs109", "CS109A", "Introduction to Data Science", 25)
    create_unified_harvard("csci103", "CSCI103", "Data Engineering", 14)
    create_unified_csci89()

    # UIUC
    create_unified_uiuc()

    print("\n" + "=" * 70)
    print("All unified files created successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
