#!/usr/bin/env python3
"""
통합본 생성 스크립트 v2
- 각 강의 파일의 preamble에서 박스 정의 등을 추출
- 모든 박스 정의를 통합 preamble에 포함
- 본문만 추출하여 chapter로 구성
"""

import re
from pathlib import Path
from collections import OrderedDict


def extract_preamble_and_body(tex_content: str):
    """preamble과 body 분리"""
    match = re.search(r'\\begin\{document\}', tex_content)
    if not match:
        return "", tex_content

    preamble = tex_content[:match.start()]
    body_with_tags = tex_content[match.start():]

    # body에서 \begin{document}와 \end{document} 제거
    body = re.sub(r'\\begin\{document\}', '', body_with_tags)
    body = re.sub(r'\\end\{document\}', '', body)

    # maketitle, tableofcontents 제거
    body = re.sub(r'\\maketitle', '', body)
    body = re.sub(r'\\tableofcontents', '', body)
    body = re.sub(r'\\thispagestyle\{[^}]*\}', '', body)

    return preamble.strip(), body.strip()


def extract_tcolorbox_definitions(preamble: str) -> dict:
    """preamble에서 tcolorbox 정의 추출"""
    boxes = OrderedDict()

    # 더 유연한 방식: newtcolorbox 라인별로 찾기
    lines = preamble.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        if '\\newtcolorbox{' in line:
            # 박스 이름 추출
            name_match = re.search(r'\\newtcolorbox\{(\w+)\}', line)
            if name_match:
                box_name = name_match.group(1)
                # 전체 정의 수집 (여러 줄에 걸쳐 있을 수 있음)
                full_def = line
                brace_count = line.count('{') - line.count('}')
                while brace_count > 0 and i + 1 < len(lines):
                    i += 1
                    full_def += '\n' + lines[i]
                    brace_count += lines[i].count('{') - lines[i].count('}')

                # 인자와 정의 추출
                args_match = re.search(r'\\newtcolorbox\{\w+\}((?:\[[^\]]*\])*)', full_def)
                args = args_match.group(1) if args_match else ''

                # 마지막 중괄호 블록이 정의
                last_brace = full_def.rfind('{')
                if last_brace != -1:
                    def_content = full_def[last_brace+1:].rstrip().rstrip('}')
                    boxes[box_name] = (args, def_content)
        i += 1

    return boxes


def extract_color_definitions(preamble: str) -> dict:
    """preamble에서 색상 정의 추출"""
    colors = OrderedDict()

    # \definecolor{name}{type}{value}
    pattern = r'\\definecolor\{(\w+)\}\{([^}]+)\}\{([^}]+)\}'

    for match in re.finditer(pattern, preamble):
        color_name = match.group(1)
        color_type = match.group(2)
        color_value = match.group(3)
        colors[color_name] = (color_type, color_value)

    return colors


def extract_newcommand_definitions(preamble: str) -> dict:
    """preamble에서 newcommand 정의 추출"""
    commands = OrderedDict()

    # \newcommand{\name}[args]{def} 또는 \newcommand{\name}{def}
    pattern = r'\\newcommand\{(\\[a-zA-Z]+)\}(\[[0-9]+\])?\{([^}]+(?:\{[^}]*\}[^}]*)*)\}'

    for match in re.finditer(pattern, preamble):
        cmd_name = match.group(1)
        cmd_args = match.group(2) or ''
        cmd_def = match.group(3)
        commands[cmd_name] = (cmd_args, cmd_def)

    return commands


def get_lecture_title(tex_content: str, lecture_num: int) -> str:
    """강의 제목 추출"""
    # \title{...} 에서 추출
    title_match = re.search(r'\\title\{([^}]+(?:\\textbf\{[^}]+\}[^}]*)*)\}', tex_content)
    if title_match:
        title = title_match.group(1)
        # \textbf{} 제거
        title = re.sub(r'\\textbf\{([^}]+)\}', r'\1', title)
        title = re.sub(r'\\Large', '', title)
        title = title.strip()
        if title and len(title) > 2:
            return title

    # 첫 번째 \section{...} 에서 추출 (본문에서)
    doc_start = tex_content.find('\\begin{document}')
    if doc_start != -1:
        body = tex_content[doc_start:]
        section_match = re.search(r'\\section\*?\{([^}]+)\}', body)
        if section_match:
            title = section_match.group(1).strip()
            if title and len(title) > 2 and '#' not in title:
                return title

    return f"Lecture {lecture_num}"


def create_unified_preamble(course_code: str, course_name: str,
                            all_colors: dict, all_boxes: dict, all_commands: dict) -> str:
    """통합 preamble 생성"""

    # 색상 정의 문자열
    color_defs = ""
    for name, (ctype, cvalue) in all_colors.items():
        color_defs += f"\\definecolor{{{name}}}{{{ctype}}}{{{cvalue}}}\n"

    # 박스 정의 문자열
    box_defs = ""
    for name, (args, definition) in all_boxes.items():
        box_defs += f"\\newtcolorbox{{{name}}}{args}{{{definition}}}\n\n"

    # 명령어 정의 문자열
    cmd_defs = ""
    for name, (args, definition) in all_commands.items():
        cmd_defs += f"\\newcommand{{{name}}}{args}{{{definition}}}\n"

    preamble = f'''%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% {course_code}: {course_name} - 통합본
% 자동 생성됨
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\\documentclass[11pt,a4paper]{{book}}

%========================================================================================
% 기본 패키지
%========================================================================================

\\usepackage{{kotex}}
\\usepackage[top=25mm, bottom=25mm, left=25mm, right=25mm]{{geometry}}
\\usepackage{{setspace}}
\\onehalfspacing
\\setlength{{\\parskip}}{{0.5em}}
\\setlength{{\\parindent}}{{0pt}}

\\usepackage{{amsmath, amssymb, amsthm}}
\\usepackage{{graphicx}}
\\usepackage{{booktabs}}
\\usepackage{{tabularx}}
\\usepackage{{array}}
\\usepackage{{longtable}}
\\usepackage{{adjustbox}}
\\renewcommand{{\\arraystretch}}{{1.1}}

\\usepackage{{enumitem}}
\\setlist{{nosep, leftmargin=*, itemsep=0.3em}}

\\usepackage{{fancyhdr}}
\\pagestyle{{fancy}}
\\fancyhf{{}}
\\fancyhead[LE,RO]{{\\thepage}}
\\fancyhead[LO]{{\\leftmark}}
\\fancyhead[RE]{{{course_code}}}
\\renewcommand{{\\headrulewidth}}{{0.5pt}}
\\setlength{{\\headheight}}{{15pt}}

\\usepackage[
    colorlinks=true,
    linkcolor=blue!80!black,
    urlcolor=blue!80!black,
    bookmarks=true,
    bookmarksnumbered=true
]{{hyperref}}

%========================================================================================
% 색상 정의
%========================================================================================

\\usepackage[dvipsnames]{{xcolor}}

{color_defs}

%========================================================================================
% 박스 환경 (tcolorbox)
%========================================================================================

\\usepackage[most]{{tcolorbox}}
\\tcbuselibrary{{skins, breakable}}

{box_defs}

%========================================================================================
% 사용자 정의 명령어
%========================================================================================

{cmd_defs}

%========================================================================================
% 문서 시작
%========================================================================================

\\title{{\\textbf{{{course_code}: {course_name}}}}}
\\author{{통합 강의 노트}}
\\date{{}}

\\begin{{document}}

\\maketitle
\\tableofcontents
\\newpage

'''
    return preamble


def create_unified_tex(course_dir: Path, course_code: str, course_name: str,
                       lecture_files: list, output_path: Path):
    """통합 tex 파일 생성"""

    print(f"\n{'='*60}")
    print(f"Creating: {course_code} - {course_name}")
    print(f"{'='*60}")

    all_colors = OrderedDict()
    all_boxes = OrderedDict()
    all_commands = OrderedDict()
    chapters = []

    # 모든 강의 파일 처리
    for i, tex_file in enumerate(lecture_files, 1):
        if not tex_file.exists():
            print(f"  [SKIP] File not found: {tex_file}")
            continue

        print(f"  Processing: {tex_file.name}")

        with open(tex_file, 'r', encoding='utf-8') as f:
            content = f.read()

        preamble, body = extract_preamble_and_body(content)

        # 색상, 박스, 명령어 정의 수집
        colors = extract_color_definitions(preamble)
        boxes = extract_tcolorbox_definitions(preamble)
        commands = extract_newcommand_definitions(preamble)

        all_colors.update(colors)
        all_boxes.update(boxes)
        all_commands.update(commands)

        # 제목 추출
        title = get_lecture_title(content, i)

        # 챕터 추가
        chapters.append((i, title, body))

    # 통합 preamble 생성
    unified_content = create_unified_preamble(
        course_code, course_name, all_colors, all_boxes, all_commands
    )

    # 각 챕터 추가
    for lecture_num, title, body in chapters:
        unified_content += f'''
%=======================================================================
% Chapter {lecture_num}: {title}
%=======================================================================
\\chapter{{{title}}}
\\label{{ch:lecture{lecture_num}}}

{body}

\\newpage

'''

    unified_content += '''
\\end{document}
'''

    # 파일 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(unified_content)

    print(f"Created: {output_path}")
    print(f"  - {len(chapters)} chapters")
    print(f"  - {len(all_colors)} colors")
    print(f"  - {len(all_boxes)} box types")


def main():
    base_dir = Path("c:/Dev/academicnotes/school")

    # MIT 과목들
    mit_courses = [
        ("18.6501", "Fundamentals of Statistics", 12),
        ("6.419", "Statistics for Data Science", 12),
        ("6.431", "Probabilistic Systems Analysis", 9),
        ("6.86", "Introduction to Machine Learning", 14),
    ]

    for code, name, num_lectures in mit_courses:
        course_dir = base_dir / "mit" / code
        lecture_files = [
            course_dir / f"lecture_{i:02d}" / f"{i}.tex"
            for i in range(1, num_lectures + 1)
        ]
        output_path = base_dir / "mit" / f"{code}_unified.tex"
        create_unified_tex(course_dir, code, name, lecture_files, output_path)

    # Stanford CS230
    stanford_dir = base_dir / "stanford" / "cs230"
    lecture_files = [
        stanford_dir / f"lecture_{i:02d}" / f"{i}.tex"
        for i in range(1, 52)
    ]
    output_path = base_dir / "stanford" / "CS230_unified.tex"
    create_unified_tex(stanford_dir, "CS230", "Deep Learning", lecture_files, output_path)

    # Harvard CS109A
    cs109_dir = base_dir / "harvard" / "cs109"
    lecture_files = [
        cs109_dir / f"lecture_{i:02d}" / f"{i}.tex"
        for i in range(1, 26)
    ]
    output_path = cs109_dir / "CS109A_unified.tex"
    create_unified_tex(cs109_dir, "CS109A", "Introduction to Data Science", lecture_files, output_path)

    # Harvard CSCI103
    csci103_dir = base_dir / "harvard" / "csci103"
    lecture_files = [
        csci103_dir / f"lecture_{i:02d}" / f"{i}.tex"
        for i in range(1, 15)
    ]
    output_path = csci103_dir / "CSCI103_unified.tex"
    create_unified_tex(csci103_dir, "CSCI103", "Data Engineering", lecture_files, output_path)

    # Harvard CSCI89 (특수 파일명)
    csci89_dir = base_dir / "harvard" / "csci89"
    lecture_files = []
    for i in range(1, 9):
        lecture_files.append(csci89_dir / f"lecture_{i:02d}" / f"csci89_{i:02d}.tex")
    for i in range(9, 14):
        lecture_files.append(csci89_dir / f"lecture_{i:02d}" / f"{i}.tex")
    output_path = csci89_dir / "CSCI89_unified.tex"
    create_unified_tex(csci89_dir, "CSCI89", "Introduction to NLP", lecture_files, output_path)

    # UIUC FIN574
    uiuc_dir = base_dir / "uiuc" / "fin-574"
    lecture_files = [
        uiuc_dir / f"lecture_{i:02d}" / f"fin574_{i:02d}.tex"
        for i in range(1, 3)
    ]
    output_path = uiuc_dir / "FIN574_unified.tex"
    create_unified_tex(uiuc_dir, "FIN574", "Firm Level Economics", lecture_files, output_path)

    print("\n" + "="*60)
    print("All unified files created!")
    print("="*60)


if __name__ == "__main__":
    main()
