#!/usr/bin/env python3
"""
통합본 생성 스크립트 v3
- 원본 preamble을 더 정확하게 파싱
- 박스 정의를 완전하게 추출
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


def find_matching_brace(text: str, start: int) -> int:
    """중괄호 매칭 찾기 - start는 '{' 위치"""
    if start >= len(text) or text[start] != '{':
        return -1

    count = 1
    i = start + 1
    while i < len(text) and count > 0:
        if text[i] == '{':
            count += 1
        elif text[i] == '}':
            count -= 1
        i += 1

    return i - 1 if count == 0 else -1


def extract_tcolorbox_definitions(preamble: str) -> str:
    """preamble에서 모든 newtcolorbox 정의를 문자열로 추출"""
    result = []

    # \newtcolorbox 시작 위치 찾기
    pattern = r'\\newtcolorbox\{'
    for match in re.finditer(pattern, preamble):
        start = match.start()

        # 이름 추출
        name_start = match.end()
        name_end = preamble.find('}', name_start)
        if name_end == -1:
            continue

        # 전체 정의 끝 찾기 (마지막 }까지)
        # optional 인자들 건너뛰기
        pos = name_end + 1
        while pos < len(preamble) and preamble[pos] == '[':
            bracket_end = preamble.find(']', pos)
            if bracket_end == -1:
                break
            pos = bracket_end + 1

        # 메인 정의 블록 찾기
        while pos < len(preamble) and preamble[pos] in ' \t\n':
            pos += 1

        if pos < len(preamble) and preamble[pos] == '{':
            end = find_matching_brace(preamble, pos)
            if end != -1:
                full_def = preamble[start:end+1]
                result.append(full_def)

    return '\n\n'.join(result)


def extract_color_definitions(preamble: str) -> str:
    """preamble에서 모든 definecolor를 문자열로 추출"""
    result = []
    pattern = r'\\definecolor\{[^}]+\}\{[^}]+\}\{[^}]+\}'
    for match in re.finditer(pattern, preamble):
        result.append(match.group(0))
    return '\n'.join(result)


def extract_newcommand_definitions(preamble: str) -> str:
    """preamble에서 newcommand 정의 추출"""
    result = []

    pattern = r'\\newcommand\{'
    for match in re.finditer(pattern, preamble):
        start = match.start()

        # 명령어 이름 끝 찾기
        name_end = preamble.find('}', match.end())
        if name_end == -1:
            continue

        pos = name_end + 1

        # optional 인자 건너뛰기
        while pos < len(preamble) and preamble[pos] in ' \t\n':
            pos += 1
        if pos < len(preamble) and preamble[pos] == '[':
            bracket_end = preamble.find(']', pos)
            if bracket_end != -1:
                pos = bracket_end + 1

        # 정의 블록 찾기
        while pos < len(preamble) and preamble[pos] in ' \t\n':
            pos += 1

        if pos < len(preamble) and preamble[pos] == '{':
            end = find_matching_brace(preamble, pos)
            if end != -1:
                full_def = preamble[start:end+1]
                result.append(full_def)

    return '\n'.join(result)


def extract_braced_content(text: str, start_pos: int) -> str:
    """중괄호로 감싸진 내용 추출 (중첩 지원)"""
    if start_pos >= len(text) or text[start_pos] != '{':
        return ""

    end_pos = find_matching_brace(text, start_pos)
    if end_pos == -1:
        return ""

    return text[start_pos + 1:end_pos]


def get_lecture_title(tex_content: str, lecture_num: int) -> str:
    """강의 제목 추출 - 중첩 중괄호 지원"""
    # \title{ 시작 위치 찾기
    title_start = tex_content.find('\\title{')
    if title_start != -1:
        brace_start = title_start + len('\\title')
        title = extract_braced_content(tex_content, brace_start)

        if title:
            # \textbf{} 내용만 추출 (중첩 지원)
            textbf_start = title.find('\\textbf{')
            if textbf_start != -1:
                inner_brace_start = textbf_start + len('\\textbf')
                title = extract_braced_content(title, inner_brace_start)

            # \Large 등 제거
            title = re.sub(r'\\Large\s*', '', title)
            title = re.sub(r'\\large\s*', '', title)
            title = re.sub(r'\\\\', '', title)  # 줄바꿈 제거
            title = title.strip()

            if title and len(title) > 2:
                return title

    # 첫 번째 \section{...} 에서 추출 (본문에서)
    doc_start = tex_content.find('\\begin{document}')
    if doc_start != -1:
        body = tex_content[doc_start:]
        section_start = re.search(r'\\section\*?\{', body)
        if section_start:
            brace_pos = body.find('{', section_start.start())
            if brace_pos != -1:
                title = extract_braced_content(body, brace_pos)
                title = title.strip()
                if title and len(title) > 2 and '#' not in title:
                    return title

    return f"Lecture {lecture_num}"


def create_unified_preamble(course_code: str, course_name: str,
                            color_defs: str, box_defs: str, cmd_defs: str) -> str:
    """통합 preamble 생성"""

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

    all_colors = set()
    all_boxes = set()
    all_commands = set()
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

        # 정의들 수집
        colors = extract_color_definitions(preamble)
        boxes = extract_tcolorbox_definitions(preamble)
        commands = extract_newcommand_definitions(preamble)

        if colors:
            all_colors.add(colors)
        if boxes:
            all_boxes.add(boxes)
        if commands:
            all_commands.add(commands)

        # 제목 추출
        title = get_lecture_title(content, i)

        # 챕터 추가
        chapters.append((i, title, body))

    # 중복 제거된 정의들 합치기
    color_defs = '\n'.join(all_colors)
    box_defs = '\n\n'.join(all_boxes)
    cmd_defs = '\n'.join(all_commands)

    # 통합 preamble 생성
    unified_content = create_unified_preamble(
        course_code, course_name, color_defs, box_defs, cmd_defs
    )

    # 각 챕터 추가
    for lecture_num, title, body in chapters:
        # 제목에서 특수문자 이스케이프
        safe_title = title.replace('\\', '\\\\').replace('{', '\\{').replace('}', '\\}')
        # 하지만 이미 LaTeX 명령어가 있으면 그대로 사용
        if '\\textbf' in title or '\\' in title:
            safe_title = title

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
