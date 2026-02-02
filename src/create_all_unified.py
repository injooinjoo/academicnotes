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
    Gemini가 body에 삽입한 preamble 명령도 제거
    """
    match = re.search(r'\\begin\{document\}(.*?)\\end\{document\}', tex_content, re.DOTALL)
    if match:
        body = match.group(1).strip()

        # body에 두 번째 \documentclass...\begin{document} 가 있으면 제거
        body = re.sub(
            r'\\documentclass.*?\\begin\{document\}',
            '', body, flags=re.DOTALL
        )

        # \maketitle, \tableofcontents 등 제거
        body = re.sub(r'\\maketitle', '', body)
        body = re.sub(r'\\tableofcontents', '', body)
        body = re.sub(r'\\thispagestyle\{[^}]*\}', '', body)
        body = re.sub(r'\\newpage\s*(?=\n|$)', '', body)

        # preamble 명령 제거 (Gemini가 body에 삽입한 경우)
        body = re.sub(r'\\usepackage(?:\[[^\]]*\])?\{[^}]+\}[^\n]*\n?', '', body)
        body = re.sub(r'\\documentclass(?:\[[^\]]*\])?\{[^}]+\}[^\n]*\n?', '', body)
        body = re.sub(r'\\pretitle\{[^}]*\}', '', body)
        body = re.sub(r'\\posttitle\{[^}]*\}', '', body)
        body = re.sub(r'\\preauthor\{[^}]*\}', '', body)
        body = re.sub(r'\\postauthor\{[^}]*\}', '', body)
        body = re.sub(r'\\predate\{[^}]*\}', '', body)
        body = re.sub(r'\\postdate\{[^}]*\}', '', body)
        body = re.sub(r'\\titlespacing\*?\{[^}]+\}\{[^}]+\}\{[^}]+\}\{[^}]+\}', '', body)
        # \newcommand{\metainfo} 블록 제거 (unified는 자체 정의 사용)
        body = re.sub(
            r'\\newcommand\{\\metainfo\}\[4\]\{.*?(?:\\end\{tcolorbox\}\s*\})',
            '', body, flags=re.DOTALL
        )
        body = re.sub(r'\\renewcommand\{\\arraystretch\}\{[^}]+\}', '', body)
        body = re.sub(r'\\setlength\{\\[^}]+\}\{[^}]+\}', '', body)
        body = re.sub(r'\\onehalfspacing\s*', '', body)
        body = re.sub(r'\\pagestyle\{[^}]+\}', '', body)
        body = re.sub(r'\\fancyhf\{[^}]*\}', '', body)
        body = re.sub(r'\\fancyhead(?:\[[^\]]*\])?\{[^}]*\}', '', body)
        body = re.sub(r'\\fancyfoot(?:\[[^\]]*\])?\{[^}]*\}', '', body)
        body = re.sub(r'\\definecolor\{[^}]+\}\{[^}]+\}\{[^}]+\}', '', body)
        body = re.sub(r'\\newtcolorbox\{[^}]+\}(?:\[[^\]]*\])*\{[^}]*(?:\{[^}]*\}[^}]*)*\}', '', body)
        body = re.sub(r'\\tcbuselibrary\{[^}]+\}', '', body)
        body = re.sub(r'\\lstset\{.*?\}', '', body, flags=re.DOTALL)
        body = re.sub(r'\\lstdefinestyle\{[^}]+\}\{.*?\}', '', body, flags=re.DOTALL)
        body = re.sub(r'\\newcommand\{\\newsection\}.*\n?', '', body)
        # \let\cautionbox, \let\endcautionbox 등
        body = re.sub(r'\\let\\[a-zA-Z]+\\[a-zA-Z]+\s*\n?', '', body)
        # %=== 구분자 주석 블록 (빈 내용 사이)
        body = re.sub(r'\n%=+\n%[^\n]*\n%=+\n(?=\s*\n)', '\n', body)
        # \title{}, \author{}, \date{} 명령
        body = re.sub(r'\\title\{[^}]*(?:\{[^}]*\}[^}]*)*\}', '', body)
        body = re.sub(r'\\author\{[^}]*\}', '', body)
        body = re.sub(r'\\date\{[^}]*\}', '', body)
        # 잔여 \end{document} 제거
        body = body.replace('\\end{document}', '')

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
\\usepackage{{colortbl}}
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

% MIT/Harvard 추가 색상
\\definecolor{{mainblue}}{{RGB}}{{50, 80, 150}}
\\definecolor{{subgray}}{{RGB}}{{180, 180, 180}}
\\definecolor{{codebg}}{{RGB}}{{245, 245, 245}}
\\definecolor{{boxbgcolor}}{{RGB}}{{245, 245, 250}}

% Stanford CS230 스타일 색상
\\definecolor{{myblue}}{{RGB}}{{50, 100, 180}}
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
    title=주의,
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
    title=예제,
    arc=2mm,
    boxrule=0.7pt,
    breakable,
    #1
}}

\\newtcolorbox{{definitionbox}}[1][]{{
    enhanced,
    colback=lightpink,
    colframe=purple!70!black,
    fonttitle=\\bfseries,
    title=정의,
    arc=2mm,
    boxrule=0.7pt,
    breakable,
    #1
}}

\\newtcolorbox{{importantbox}}[1][]{{
    enhanced,
    colback=boxred,
    colframe=red!70!black,
    fonttitle=\\bfseries,
    title=매우 중요,
    arc=2mm,
    boxrule=0.7pt,
    breakable,
    #1
}}

\\newtcolorbox{{conceptbox}}[1][]{{
    enhanced,
    colback=lightgreen,
    colframe=darkgreen,
    fonttitle=\\bfseries,
    title=개념,
    arc=2mm,
    boxrule=0.7pt,
    breakable,
    #1
}}

\\newtcolorbox{{analogybox}}[1][]{{
    enhanced,
    colback=green!5!white,
    colframe=green!60!black,
    fonttitle=\\bfseries,
    title=비유,
    arc=2mm,
    boxrule=0.7pt,
    breakable,
    #1
}}

\\let\\cautionbox\\warningbox
\\let\\endcautionbox\\endwarningbox

% tcbset 스타일 정의 (\\begin{{tcolorbox}}[summarybox] 형식 사용 시 호환)
\\tcbset{{
    summarybox/.style={{enhanced, colback=lightblue, colframe=darkblue, fonttitle=\\bfseries, title=핵심 요약, arc=2mm, boxrule=0.7pt, breakable}},
    warningbox/.style={{enhanced, colback=lightyellow, colframe=darkorange, fonttitle=\\bfseries, title=주의, arc=2mm, boxrule=0.7pt, breakable}},
    examplebox/.style={{enhanced, colback=lightgray, colframe=black!60, fonttitle=\\bfseries, title=예제, arc=2mm, boxrule=0.7pt, breakable}},
    definitionbox/.style={{enhanced, colback=lightpink, colframe=purple!70!black, fonttitle=\\bfseries, title=정의, arc=2mm, boxrule=0.7pt, breakable}},
    importantbox/.style={{enhanced, colback=boxred, colframe=red!70!black, fonttitle=\\bfseries, title=매우 중요, arc=2mm, boxrule=0.7pt, breakable}},
    infobox/.style={{enhanced, colback=lightgreen, colframe=darkgreen, fonttitle=\\bfseries, title=핵심 정보, arc=2mm, boxrule=0.7pt, breakable}},
    conceptbox/.style={{enhanced, colback=lightgreen, colframe=darkgreen, fonttitle=\\bfseries, title=개념, arc=2mm, boxrule=0.7pt, breakable}},
    analogybox/.style={{enhanced, colback=green!5!white, colframe=green!60!black, fonttitle=\\bfseries, title=비유, arc=2mm, boxrule=0.7pt, breakable}},
    overviewbox/.style={{enhanced, colback=lightpurple, colframe=darkpurple, fonttitle=\\bfseries\\large, title=강의 개요, arc=3mm, boxrule=1pt, breakable}},
    cautionbox/.style={{enhanced, colback=lightyellow, colframe=darkorange, fonttitle=\\bfseries, title=주의, arc=2mm, boxrule=0.7pt, breakable}},
    mybox/.style={{enhanced, colback=lightblue, colframe=darkblue, fonttitle=\\bfseries, title={{#1}}, arc=2mm, boxrule=0.7pt, breakable}},
    definition/.style={{enhanced, colback=lightpink, colframe=purple!70!black, fonttitle=\\bfseries, title={{#1}}, arc=2mm, boxrule=0.7pt, breakable}},
    example/.style={{enhanced, colback=lightgray, colframe=black!60, fonttitle=\\bfseries, title={{#1}}, arc=2mm, boxrule=0.7pt, breakable}},
    summary/.style={{enhanced, colback=lightblue, colframe=darkblue, fonttitle=\\bfseries, title={{#1}}, arc=2mm, boxrule=0.7pt, breakable}},
    warning/.style={{enhanced, colback=lightyellow, colframe=darkorange, fonttitle=\\bfseries, title={{#1}}, arc=2mm, boxrule=0.7pt, breakable}},
}}

% mybox 환경 (UIUC용)
\\newtcolorbox{{mybox}}[1]{{
    enhanced,
    colback=lightblue,
    colframe=darkblue,
    fonttitle=\\bfseries,
    title={{#1}},
    arc=2mm,
    boxrule=0.7pt,
    breakable
}}

% 추가 환경 (Gemini 생성 콘텐츠에서 사용)
\\newtcolorbox{{tipbox}}[1][]{{enhanced, colback=green!5!white, colframe=green!60!black, fonttitle=\\bfseries, title=팁, arc=2mm, boxrule=0.7pt, breakable, #1}}
\\newtcolorbox{{solutionbox}}[1][]{{enhanced, colback=lightblue, colframe=darkblue, fonttitle=\\bfseries, title=풀이, arc=2mm, boxrule=0.7pt, breakable, #1}}
\\newtcolorbox{{downloadbox}}[1][]{{enhanced, colback=boxgray, colframe=black!40, fonttitle=\\bfseries, title=다운로드, arc=2mm, boxrule=0.7pt, breakable, #1}}
\\newtcolorbox{{practicebox}}[1][]{{enhanced, colback=lightyellow, colframe=darkorange, fonttitle=\\bfseries, title=연습, arc=2mm, boxrule=0.7pt, breakable, #1}}
\\newtcolorbox{{keypointbox}}[1][]{{enhanced, colback=lightyellow, colframe=darkorange, fonttitle=\\bfseries, title=핵심 포인트, arc=2mm, boxrule=0.7pt, breakable, #1}}
\\newtcolorbox{{storybox}}[1][]{{enhanced, colback=lightyellow, colframe=darkorange!80!black, fonttitle=\\bfseries, title=이야기, arc=2mm, boxrule=0.7pt, breakable, #1}}
\\newtcolorbox{{mathstep}}[1][]{{enhanced, colback=lightblue, colframe=darkblue, fonttitle=\\bfseries, title=수학 단계, arc=2mm, boxrule=0.7pt, breakable, #1}}
\\newtcolorbox{{systembox}}[1][]{{enhanced, colback=lightgray, colframe=black!60, fonttitle=\\bfseries, title=시스템, arc=2mm, boxrule=0.7pt, breakable, #1}}
\\newtcolorbox{{toolbox}}[1][]{{enhanced, colback=boxgray, colframe=black!40, fonttitle=\\bfseries, title=도구, arc=2mm, boxrule=0.7pt, breakable, #1}}
\\newtcolorbox{{bayesbox}}[1][]{{enhanced, colback=lightpurple, colframe=darkpurple, fonttitle=\\bfseries, title=베이즈, arc=2mm, boxrule=0.7pt, breakable, #1}}
\\newtcolorbox{{formulabox}}[1][]{{enhanced, colback=lightblue, colframe=darkblue, fonttitle=\\bfseries, title=공식, arc=2mm, boxrule=0.7pt, breakable, #1}}
\\newtcolorbox{{mathbox}}[1][]{{enhanced, colback=lightblue, colframe=darkblue, fonttitle=\\bfseries, title=수학, arc=2mm, boxrule=0.7pt, breakable, #1}}
\\newtcolorbox{{strategybox}}[1][]{{enhanced, colback=lightgreen, colframe=darkgreen, fonttitle=\\bfseries, title=전략, arc=2mm, boxrule=0.7pt, breakable, #1}}
\\newtcolorbox{{diagnosisbox}}[1][]{{enhanced, colback=lightpink, colframe=purple!70!black, fonttitle=\\bfseries, title=진단, arc=2mm, boxrule=0.7pt, breakable, #1}}
\\newtcolorbox{{featurebox}}[1][]{{enhanced, colback=lightgreen, colframe=darkgreen, fonttitle=\\bfseries, title=특징, arc=2mm, boxrule=0.7pt, breakable, #1}}
\\newtcolorbox{{faqbox}}[1][]{{enhanced, colback=lightyellow, colframe=darkorange, fonttitle=\\bfseries, title=FAQ, arc=2mm, boxrule=0.7pt, breakable, #1}}
\\newtcolorbox{{notebox}}[1][]{{enhanced, colback=lightyellow, colframe=darkorange, fonttitle=\\bfseries, title=노트, arc=2mm, boxrule=0.7pt, breakable, #1}}
\\newtcolorbox{{codeexamplebox}}[1][]{{enhanced, colback=lightgray, colframe=black!60, fonttitle=\\bfseries, title=코드 예제, arc=2mm, boxrule=0.7pt, breakable, #1}}
\\newtcolorbox{{keyconceptbox}}[1][]{{enhanced, colback=lightgreen, colframe=darkgreen, fonttitle=\\bfseries, title=핵심 개념, arc=2mm, boxrule=0.7pt, breakable, #1}}
\\newtcolorbox{{termbox}}[1][]{{enhanced, colback=lightpurple, colframe=darkpurple, fonttitle=\\bfseries, title=용어, arc=2mm, boxrule=0.7pt, breakable, #1}}
\\let\\cautionbox\\warningbox
\\let\\endcautionbox\\endwarningbox

% 커스텀 명령어 (Gemini 생성 콘텐츠에서 사용)
\\newcommand{{\\excel}}[1]{{\\texttt{{#1}}}}
\\newcommand{{\\code}}[1]{{\\texttt{{#1}}}}
\\newcommand{{\\concept}}[1]{{\\textbf{{#1}}}}
\\newcommand{{\\formula}}[1]{{\\textit{{#1}}}}
\\providecommand{{\\captionof}}[2]{{\\textbf{{#2}}}}
\\newcommand{{\\chaptertitle}}[2]{{\\section*{{#1: #2}}}}
\\providecommand{{\\newsection}}{{\\section}}

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


def create_unified_harvard(course_dir_name: str, course_code: str, course_name: str, num_lectures: int, file_prefix: str = None):
    """Harvard 통합본 생성"""
    base_dir = Path("c:/Dev/academicnotes/school/harvard")
    course_dir = base_dir / course_dir_name
    short_code = file_prefix or course_code.lower().replace("-", "")

    print(f"\n{'='*60}")
    print(f"Creating: {course_code} - {course_name}")
    print(f"{'='*60}")

    unified_content = get_unified_preamble(course_code, course_name)

    for i in range(1, num_lectures + 1):
        lecture_dir = course_dir / f"lecture_{i:02d}"
        # 새 파일명 우선 (예: cs109_17.tex, csci103_01.tex)
        new_file = lecture_dir / f"{short_code}_{i:02d}.tex"
        old_file = lecture_dir / f"{i}.tex"
        tex_file = new_file if new_file.exists() else old_file
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
    print(f"Creating: CSCI89 - Introduction to AI")
    print(f"{'='*60}")

    unified_content = get_unified_preamble("CSCI89", "Introduction to Artificial Intelligence")

    # 모든 강의에 대해 새 파일명 우선 (csci89_XX.tex), 없으면 구 파일명 (X.tex)
    file_mappings = []
    for i in range(1, 13):
        file_mappings.append((i, f"lecture_{i:02d}"))

    for lecture_num, dir_name in file_mappings:
        new_file = course_dir / dir_name / f"csci89_{lecture_num:02d}.tex"
        old_file = course_dir / dir_name / f"{lecture_num}.tex"
        tex_file = new_file if new_file.exists() else old_file
        if tex_file.exists():
            print(f"  Processing: {tex_file.name}")
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


def create_unified_uiuc_fin571():
    """UIUC FIN-571 통합본 생성"""
    base_dir = Path("c:/Dev/academicnotes/school/uiuc")
    course_dir = base_dir / "fin-571"

    print(f"\n{'='*60}")
    print(f"Creating: FIN571 - Financial Institutions & Monetary Policy")
    print(f"{'='*60}")

    unified_content = get_unified_preamble("FIN571", "Financial Institutions \\& Monetary Policy")

    for i in range(1, 9):  # 8개 모듈
        tex_file = course_dir / f"lecture_{i:02d}" / f"fin571_{i:02d}.tex"
        if tex_file.exists():
            print(f"  Processing: fin571_{i:02d}.tex")
            with open(tex_file, 'r', encoding='utf-8') as f:
                content = f.read()

            title = extract_lecture_title(content, i)
            body = extract_document_body(content)

            if body:
                unified_content += f'''
%=======================================================================
% Module {i}: {title}
%=======================================================================
\\chapter{{{title}}}
\\label{{ch:module{i}}}

{body}

'''
        else:
            print(f"  File not found: {tex_file}")

    unified_content += '''
\\end{document}
'''

    unified_path = course_dir / "FIN571_unified.tex"
    with open(unified_path, 'w', encoding='utf-8') as f:
        f.write(unified_content)

    print(f"Created: {unified_path}")
    return unified_path


def create_unified_uiuc_badm572():
    """UIUC BADM-572 통합본 생성"""
    base_dir = Path("c:/Dev/academicnotes/school/uiuc")
    course_dir = base_dir / "badm-572"

    print(f"\n{'='*60}")
    print(f"Creating: BADM572 - Data-Driven Decision Making")
    print(f"{'='*60}")

    unified_content = get_unified_preamble("BADM572", "Data-Driven Decision Making")

    for i in range(1, 9):  # 8개 모듈
        tex_file = course_dir / f"lecture_{i:02d}" / f"badm572_{i:02d}.tex"
        if tex_file.exists():
            print(f"  Processing: badm572_{i:02d}.tex")
            with open(tex_file, 'r', encoding='utf-8') as f:
                content = f.read()

            title = extract_lecture_title(content, i)
            body = extract_document_body(content)

            if body:
                unified_content += f'''
%=======================================================================
% Module {i}: {title}
%=======================================================================
\\chapter{{{title}}}
\\label{{ch:module{i}}}

{body}

'''
        else:
            print(f"  File not found: {tex_file}")

    unified_content += '''
\\end{document}
'''

    unified_path = course_dir / "BADM572_unified.tex"
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
    create_unified_harvard("cs109", "CS109A", "Introduction to Data Science", 25, file_prefix="cs109")
    create_unified_harvard("csci103", "CSCI103", "Data Engineering", 14)
    create_unified_csci89()

    # UIUC
    create_unified_uiuc()
    create_unified_uiuc_fin571()
    create_unified_uiuc_badm572()

    print("\n" + "=" * 70)
    print("All unified files created successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
