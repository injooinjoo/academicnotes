#!/usr/bin/env python3
"""
Harvard 강의 통합본 생성 스크립트
- 각 챕터별 tex 파일에서 본문만 추출
- 하나의 통합 book 문서로 생성
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
        body = re.sub(r'\\newpage', '', body)
        # 빈 줄 정리
        body = re.sub(r'\n{3,}', '\n\n', body)
        return body.strip()
    return ""


def extract_lecture_title(tex_content: str, lecture_num: int) -> str:
    """강의 제목 추출"""
    # \title{...} 에서 추출
    title_match = re.search(r'\\title\{[^}]*\\textbf\{([^}]+)\}', tex_content)
    if title_match:
        return title_match.group(1)

    # 첫 번째 \section{...} 에서 추출
    section_match = re.search(r'\\section\{([^}]+)\}', tex_content)
    if section_match:
        return section_match.group(1)

    return f"Lecture {lecture_num}"


def create_unified_harvard(course_dir: str, course_code: str, course_name: str, num_lectures: int):
    """
    Harvard 과목 통합본 생성

    Args:
        course_dir: 과목 디렉토리 경로 (예: school/harvard/cs109)
        course_code: 과목 코드 (예: CS109A)
        course_name: 과목 이름 (예: Introduction to Data Science)
        num_lectures: 강의 수
    """
    course_path = Path(course_dir)

    # Preamble 생성 (master_template 기반)
    unified_content = f'''%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
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
    title=핵심 요약,
    arc=2mm,
    boxrule=0.7pt,
    breakable,
    #1
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
    title=주의사항,
    arc=2mm,
    boxrule=0.7pt,
    breakable,
    #1
}}

\\newtcolorbox{{examplebox}}[1][]{{
    enhanced,
    colback=lightgray,
    colframe=black!60,
    fonttitle=\\bfseries,
    title=예제: #1,
    arc=2mm,
    boxrule=0.7pt,
    breakable
}}

\\newtcolorbox{{definitionbox}}[1][]{{
    enhanced,
    colback=lightpink,
    colframe=purple!70!black,
    fonttitle=\\bfseries,
    title=정의: #1,
    arc=2mm,
    boxrule=0.7pt,
    breakable
}}

\\newtcolorbox{{importantbox}}[1][]{{
    enhanced,
    colback=boxred,
    colframe=red!70!black,
    fonttitle=\\bfseries,
    title=매우 중요: #1,
    arc=2mm,
    boxrule=0.7pt,
    breakable
}}

\\let\\cautionbox\\warningbox
\\let\\endcautionbox\\endwarningbox

%========================================================================================
% 코드 블록
%========================================================================================

\\usepackage{{listings}}

\\definecolor{{codegray}}{{rgb}}{{0.5,0.5,0.5}}
\\definecolor{{codepurple}}{{rgb}}{{0.58,0,0.82}}
\\definecolor{{backcolour}}{{rgb}}{{0.95,0.95,0.95}}

\\lstset{{
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

\\usepackage{{amsmath, amssymb, amsthm}}

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
% 문서 시작
%========================================================================================

\\title{{\\textbf{{{course_code}: {course_name}}}}}
\\author{{통합 강의 노트}}
\\date{{}}

\\begin{{document}}

\\maketitle
\\tableofcontents

'''

    # 각 강의 추가
    for i in range(1, num_lectures + 1):
        lecture_dir = course_path / f"lecture_{i:02d}"
        tex_file = lecture_dir / f"{i}.tex"

        if tex_file.exists():
            print(f"  Processing: {tex_file}")
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

\\newpage
'''
        else:
            print(f"  File not found: {tex_file}")

    unified_content += '''
\\end{document}
'''

    # 통합본 저장
    unified_path = course_path / f"{course_code}_unified.tex"
    with open(unified_path, 'w', encoding='utf-8') as f:
        f.write(unified_content)

    print(f"Created: {unified_path}")
    return unified_path


def create_unified_csci89(course_dir: str, course_code: str, course_name: str):
    """
    CSCI89 통합본 생성 (파일명 혼재 처리)
    - lecture 1-8: csci89_01.tex ~ csci89_08.tex
    - lecture 9-13: 9.tex ~ 13.tex
    """
    course_path = Path(course_dir)

    # Preamble (간단화)
    unified_content = f'''%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% {course_code}: {course_name} - 통합본
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\\documentclass[11pt,a4paper]{{book}}

\\usepackage{{kotex}}
\\usepackage[top=20mm, bottom=20mm, left=20mm, right=18mm]{{geometry}}
\\usepackage{{setspace}}
\\onehalfspacing
\\setlength{{\\parskip}}{{0.5em}}
\\setlength{{\\parindent}}{{0pt}}

\\usepackage{{booktabs}}
\\usepackage{{tabularx}}
\\usepackage{{array}}
\\usepackage{{longtable}}
\\renewcommand{{\\arraystretch}}{{1.1}}

\\usepackage{{fancyhdr}}
\\pagestyle{{fancy}}
\\fancyhf{{}}
\\fancyhead[LE,RO]{{\\thepage}}
\\fancyhead[LO]{{\\leftmark}}
\\fancyhead[RE]{{{course_code}}}
\\renewcommand{{\\headrulewidth}}{{0.5pt}}

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

\\usepackage[most]{{tcolorbox}}
\\tcbuselibrary{{skins, breakable}}

\\newtcolorbox{{overviewbox}}[1][]{{enhanced, colback=lightpurple, colframe=darkpurple, fonttitle=\\bfseries\\large, title=강의 개요, arc=3mm, boxrule=1pt, breakable, #1}}
\\newtcolorbox{{summarybox}}[1][]{{enhanced, colback=lightblue, colframe=darkblue, fonttitle=\\bfseries, title=핵심 요약, arc=2mm, boxrule=0.7pt, breakable, #1}}
\\newtcolorbox{{infobox}}[1][]{{enhanced, colback=lightgreen, colframe=darkgreen, fonttitle=\\bfseries, title=핵심 정보, arc=2mm, boxrule=0.7pt, breakable, #1}}
\\newtcolorbox{{warningbox}}[1][]{{enhanced, colback=lightyellow, colframe=darkorange, fonttitle=\\bfseries, title=주의사항, arc=2mm, boxrule=0.7pt, breakable, #1}}
\\newtcolorbox{{examplebox}}[1][]{{enhanced, colback=lightgray, colframe=black!60, fonttitle=\\bfseries, title=예제: #1, arc=2mm, boxrule=0.7pt, breakable}}
\\newtcolorbox{{definitionbox}}[1][]{{enhanced, colback=lightpink, colframe=purple!70!black, fonttitle=\\bfseries, title=정의: #1, arc=2mm, boxrule=0.7pt, breakable}}
\\newtcolorbox{{importantbox}}[1][]{{enhanced, colback=boxred, colframe=red!70!black, fonttitle=\\bfseries, title=매우 중요: #1, arc=2mm, boxrule=0.7pt, breakable}}
\\let\\cautionbox\\warningbox
\\let\\endcautionbox\\endwarningbox

\\usepackage{{listings}}
\\lstset{{basicstyle=\\ttfamily\\small, backgroundcolor=\\color{{lightgray}}, keywordstyle=\\color{{darkblue}}\\bfseries, commentstyle=\\color{{darkgreen}}\\itshape, stringstyle=\\color{{purple!80!black}}, numberstyle=\\tiny\\color{{black!60}}, numbers=left, numbersep=8pt, breaklines=true, frame=single, frameround=tttt, rulecolor=\\color{{black!30}}, showstringspaces=false, tabsize=2, xleftmargin=15pt, xrightmargin=5pt}}

\\usepackage{{amsmath, amssymb, amsthm}}
\\theoremstyle{{definition}}
\\newtheorem{{theorem}}{{정리}}[chapter]
\\newtheorem{{lemma}}[theorem]{{보조정리}}
\\newtheorem{{proposition}}[theorem]{{명제}}
\\newtheorem{{corollary}}[theorem]{{따름정리}}
\\newtheorem{{definition}}{{정의}}[chapter]
\\newtheorem{{example}}{{예제}}[chapter]

\\usepackage[colorlinks=true, linkcolor=blue!80!black, urlcolor=blue!80!black, bookmarks=true, bookmarksnumbered=true]{{hyperref}}

\\usepackage{{enumitem}}
\\setlist{{nosep, leftmargin=*, itemsep=0.3em}}
\\usepackage{{microtype}}
\\usepackage{{graphicx}}
\\usepackage{{url}}
\\urlstyle{{same}}

\\title{{\\textbf{{{course_code}: {course_name}}}}}
\\author{{통합 강의 노트}}
\\date{{}}

\\begin{{document}}

\\maketitle
\\tableofcontents

'''

    # 파일 매핑 (lecture 1-8: csci89_XX.tex, 9-13: X.tex)
    file_mappings = []
    for i in range(1, 9):
        file_mappings.append((i, f"lecture_{i:02d}", f"csci89_{i:02d}.tex"))
    for i in range(9, 14):
        file_mappings.append((i, f"lecture_{i:02d}", f"{i}.tex"))

    for lecture_num, dir_name, filename in file_mappings:
        tex_file = course_path / dir_name / filename
        if tex_file.exists():
            print(f"  Processing: {tex_file}")
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

\\newpage
'''
        else:
            print(f"  File not found: {tex_file}")

    unified_content += '''
\\end{document}
'''

    unified_path = course_path / f"{course_code}_unified.tex"
    with open(unified_path, 'w', encoding='utf-8') as f:
        f.write(unified_content)

    print(f"Created: {unified_path}")
    return unified_path


def main():
    base_dir = Path("c:/Dev/academicnotes/school/harvard")

    # CS109A와 CSCI103
    courses = [
        ("cs109", "CS109A", "Introduction to Data Science", 25),
        ("csci103", "CSCI103", "Data Engineering", 14),
    ]

    for dir_name, code, name, num_lectures in courses:
        course_dir = base_dir / dir_name
        if course_dir.exists():
            print(f"\n{'='*60}")
            print(f"Processing: {code} - {name}")
            print(f"{'='*60}")
            create_unified_harvard(str(course_dir), code, name, num_lectures)
        else:
            print(f"Directory not found: {course_dir}")

    # CSCI89
    csci89_dir = base_dir / "csci89"
    if csci89_dir.exists():
        print(f"\n{'='*60}")
        print(f"Processing: CSCI89 - Introduction to NLP")
        print(f"{'='*60}")
        create_unified_csci89(str(csci89_dir), "CSCI89", "Introduction to NLP")


def create_unified_uiuc(course_dir: str, course_code: str, course_name: str, num_lectures: int):
    """
    UIUC 통합본 생성 (fin574_XX.tex 형식)
    """
    course_path = Path(course_dir)

    unified_content = f'''%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% {course_code}: {course_name} - 통합본
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\\documentclass[11pt,a4paper]{{book}}

\\usepackage{{kotex}}
\\usepackage[top=20mm, bottom=20mm, left=20mm, right=18mm]{{geometry}}
\\usepackage{{setspace}}
\\onehalfspacing
\\setlength{{\\parskip}}{{0.5em}}
\\setlength{{\\parindent}}{{0pt}}

\\usepackage{{booktabs}}
\\usepackage{{tabularx}}
\\usepackage{{array}}
\\usepackage{{longtable}}
\\renewcommand{{\\arraystretch}}{{1.1}}

\\usepackage{{fancyhdr}}
\\pagestyle{{fancy}}
\\fancyhf{{}}
\\fancyhead[LE,RO]{{\\thepage}}
\\fancyhead[LO]{{\\leftmark}}
\\fancyhead[RE]{{{course_code}}}
\\renewcommand{{\\headrulewidth}}{{0.5pt}}

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

\\usepackage[most]{{tcolorbox}}
\\tcbuselibrary{{skins, breakable}}

\\newtcolorbox{{overviewbox}}[1][]{{enhanced, colback=lightpurple, colframe=darkpurple, fonttitle=\\bfseries\\large, title=강의 개요, arc=3mm, boxrule=1pt, breakable, #1}}
\\newtcolorbox{{summarybox}}[1][]{{enhanced, colback=lightblue, colframe=darkblue, fonttitle=\\bfseries, title=핵심 요약, arc=2mm, boxrule=0.7pt, breakable, #1}}
\\newtcolorbox{{infobox}}[1][]{{enhanced, colback=lightgreen, colframe=darkgreen, fonttitle=\\bfseries, title=핵심 정보, arc=2mm, boxrule=0.7pt, breakable, #1}}
\\newtcolorbox{{warningbox}}[1][]{{enhanced, colback=lightyellow, colframe=darkorange, fonttitle=\\bfseries, title=주의사항, arc=2mm, boxrule=0.7pt, breakable, #1}}
\\newtcolorbox{{examplebox}}[1][]{{enhanced, colback=lightgray, colframe=black!60, fonttitle=\\bfseries, title=예제: #1, arc=2mm, boxrule=0.7pt, breakable}}
\\newtcolorbox{{definitionbox}}[1][]{{enhanced, colback=lightpink, colframe=purple!70!black, fonttitle=\\bfseries, title=정의: #1, arc=2mm, boxrule=0.7pt, breakable}}
\\newtcolorbox{{importantbox}}[1][]{{enhanced, colback=boxred, colframe=red!70!black, fonttitle=\\bfseries, title=매우 중요: #1, arc=2mm, boxrule=0.7pt, breakable}}
\\let\\cautionbox\\warningbox
\\let\\endcautionbox\\endwarningbox

\\usepackage{{listings}}
\\lstset{{basicstyle=\\ttfamily\\small, backgroundcolor=\\color{{lightgray}}, keywordstyle=\\color{{darkblue}}\\bfseries, commentstyle=\\color{{darkgreen}}\\itshape, stringstyle=\\color{{purple!80!black}}, numberstyle=\\tiny\\color{{black!60}}, numbers=left, numbersep=8pt, breaklines=true, frame=single, frameround=tttt, rulecolor=\\color{{black!30}}, showstringspaces=false, tabsize=2, xleftmargin=15pt, xrightmargin=5pt}}

\\usepackage{{amsmath, amssymb, amsthm}}
\\theoremstyle{{definition}}
\\newtheorem{{theorem}}{{정리}}[chapter]
\\newtheorem{{lemma}}[theorem]{{보조정리}}
\\newtheorem{{proposition}}[theorem]{{명제}}
\\newtheorem{{corollary}}[theorem]{{따름정리}}
\\newtheorem{{definition}}{{정의}}[chapter]
\\newtheorem{{example}}{{예제}}[chapter]

\\usepackage[colorlinks=true, linkcolor=blue!80!black, urlcolor=blue!80!black, bookmarks=true, bookmarksnumbered=true]{{hyperref}}

\\usepackage{{enumitem}}
\\setlist{{nosep, leftmargin=*, itemsep=0.3em}}
\\usepackage{{microtype}}
\\usepackage{{graphicx}}
\\usepackage{{url}}
\\urlstyle{{same}}

\\title{{\\textbf{{{course_code}: {course_name}}}}}
\\author{{통합 강의 노트}}
\\date{{}}

\\begin{{document}}

\\maketitle
\\tableofcontents

'''

    for i in range(1, num_lectures + 1):
        tex_file = course_path / f"lecture_{i:02d}" / f"fin574_{i:02d}.tex"
        if tex_file.exists():
            print(f"  Processing: {tex_file}")
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

\\newpage
'''
        else:
            print(f"  File not found: {tex_file}")

    unified_content += '''
\\end{document}
'''

    unified_path = course_path / f"{course_code}_unified.tex"
    with open(unified_path, 'w', encoding='utf-8') as f:
        f.write(unified_content)

    print(f"Created: {unified_path}")
    return unified_path


if __name__ == "__main__":
    main()

    # UIUC
    uiuc_dir = Path("c:/Dev/academicnotes/school/uiuc/fin-574")
    if uiuc_dir.exists():
        print(f"\n{'='*60}")
        print(f"Processing: FIN574 - Firm Level Economics")
        print(f"{'='*60}")
        create_unified_uiuc(str(uiuc_dir), "FIN574", "Firm Level Economics", 2)
