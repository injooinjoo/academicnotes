#!/usr/bin/env python3
"""
LaTeX 문서 통합 템플릿 변환 스크립트
- 기존 프리앰블을 마스터 템플릿으로 교체
- 메타정보 블록 추가
- 본문 내용은 100% 보존
"""

import os
import re
from pathlib import Path

# 과정별 메타데이터
COURSE_META = {
    "cs109": {
        "name": "CS109A: 데이터 과학 입문",
        "prof": "Pavlos Protopapas, Kevin Rader, Chris Gumb"
    },
    "csci103": {
        "name": "CSCI E-103: 재현 가능한 머신러닝",
        "prof": "Anindita Mahapatra & Eric Gieseke"
    },
    "csci89": {
        "name": "CSCI E-89B: 자연어 처리 입문",
        "prof": "Dmitry Kurochkin"
    },
    "fin-574": {
        "name": "FIN 574: 기업 수준 경제학",
        "prof": "UIUC Faculty"
    }
}

def read_template():
    """마스터 템플릿 읽기"""
    template_path = Path("templates/master_template.tex")
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def extract_document_body(content):
    """
    LaTeX 문서에서 \begin{document} 이후 본문만 추출
    """
    # \begin{document} 위치 찾기
    doc_start = content.find(r'\begin{document}')
    if doc_start == -1:
        print("Warning: \\begin{document} not found")
        return content

    # 본문 시작 (\\begin{document} 이후)
    body_start = content.find('\n', doc_start) + 1

    # \end{document} 찾기
    doc_end = content.rfind(r'\end{document}')
    if doc_end == -1:
        print("Warning: \\end{document} not found")
        return content[body_start:]

    body = content[body_start:doc_end].strip()

    # Remove \title, \author, \date from body if present (these belong in preamble)
    # Use non-greedy matching and handle potential nested braces
    body = re.sub(r'\\title\{[^}]*(?:\{[^}]*\}[^}]*)*\}\s*', '', body)
    body = re.sub(r'\\author\{[^}]*(?:\\and[^}]*)*\}\s*', '', body)
    body = re.sub(r'\\date\{[^}]*\}\s*', '', body)

    return body

def extract_title_info(body):
    """본문에서 제목 정보 추출"""
    title_match = re.search(r'\\title\{([^}]+)\}', body)
    author_match = re.search(r'\\author\{([^}]+)\}', body)

    title = title_match.group(1) if title_match else "강의 노트"
    author = author_match.group(1) if author_match else ""

    return title, author

def detect_course_and_lecture(filepath):
    """파일 경로에서 과정명과 강의 번호 추출"""
    path_parts = Path(filepath).parts

    course = None
    lecture_num = None

    for part in path_parts:
        if part in ['cs109', 'csci103', 'csci89', 'fin-574']:
            course = part
        if part.startswith('lecture_'):
            lecture_num = part.replace('lecture_', '')

    # 파일명에서 강의 번호 추출 시도
    if not lecture_num:
        filename = Path(filepath).stem
        # 숫자 추출
        nums = re.findall(r'\d+', filename)
        if nums:
            lecture_num = nums[0]

    return course, lecture_num

def generate_metadata_block(course_code, lecture_num):
    """메타정보 블록 생성"""
    if course_code not in COURSE_META:
        return ""

    meta = COURSE_META[course_code]
    course_name = meta["name"]
    prof_name = meta["prof"]
    lecture_str = f"Lecture {lecture_num}" if lecture_num else "강의 노트"

    purpose = f"{lecture_str}의 핵심 개념 학습"

    return f"""\\metainfo{{{course_name}}}{{{lecture_str}}}{{{prof_name}}}{{{purpose}}}

"""

def update_header_info(template, course_code, lecture_num):
    """헤더 정보 업데이트"""
    if course_code in COURSE_META:
        course_name = COURSE_META[course_code]["name"]
    else:
        course_name = "강의 노트"

    lecture_str = f"Lecture {lecture_num}" if lecture_num else ""

    # Fix: Replace with proper escaping
    template = template.replace(r"COURSE\_NAME", course_name)
    template = template.replace(r"LECTURE\_NUMBER", lecture_str)

    # Also update PDF metadata
    template = template.replace("COURSE_NAME", course_name)
    template = template.replace("LECTURE_NUMBER", lecture_str)

    return template

def convert_file(input_path, output_path=None):
    """
    단일 LaTeX 파일 변환
    """
    print(f"Processing: {input_path}")

    # 출력 경로가 없으면 원본 덮어쓰기
    if output_path is None:
        output_path = input_path

    # 파일 읽기
    with open(input_path, 'r', encoding='utf-8') as f:
        original_content = f.read()

    # 과정 및 강의 번호 감지
    course_code, lecture_num = detect_course_and_lecture(input_path)
    print(f"  Detected: {course_code} - Lecture {lecture_num}")

    # 템플릿 읽기
    template = read_template()

    # 헤더 정보 업데이트
    template = update_header_info(template, course_code, lecture_num)

    # 본문 추출
    body = extract_document_body(original_content)

    # 제목 정보 추출
    title, author = extract_title_info(body)

    # 메타정보 블록 생성
    meta_block = generate_metadata_block(course_code, lecture_num)

    # 최종 문서 조립
    # 본문 시작 부분에 메타정보 삽입
    # titlepage 환경이 있으면 그 다음에, 없으면 \maketitle 다음에, 없으면 처음에 삽입

    # titlepage와 maketitle이 같이 있는 경우 maketitle 제거
    if r'\begin{titlepage}' in body and r'\maketitle' in body:
        # maketitle이 titlepage 다음에 있으면 제거
        body = re.sub(r'\\end\{titlepage\}\s*\\maketitle\s*\\thispagestyle\{[^}]*\}',
                     r'\\end{titlepage}', body)
        body = re.sub(r'\\end\{titlepage\}\s*\\maketitle',
                     r'\\end{titlepage}', body)

    # 기존에 삽입된 중복 메타정보 블록과 thispagestyle 제거
    body = re.sub(r'\\thispagestyle\{firstpage\}\s*\\metainfo\{[^}]*\}\{[^}]*\}\{[^}]*\}\{[^}]*\}\s*', '', body)
    body = re.sub(r'\\thispagestyle\{empty\}\s*', '', body)

    if r'\end{titlepage}' in body:
        # titlepage 다음에 삽입
        body = body.replace(r'\end{titlepage}',
                          r'\end{titlepage}' + '\n\\thispagestyle{firstpage}\n\n' + meta_block)
    elif r'\maketitle' in body:
        # maketitle 다음에 삽입
        body = body.replace(r'\maketitle',
                          r'\maketitle' + '\n\\thispagestyle{firstpage}\n\n' + meta_block)
    elif r'\begin{summarybox}' in body:
        # summarybox 앞에 삽입
        body = meta_block + body
    else:
        # 맨 앞에 삽입
        body = meta_block + body

    # 최종 문서 생성
    final_document = template + '\n\n\\begin{document}\n\n' + body + '\n\n\\end{document}\n'

    # 파일 쓰기
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_document)

    print(f"  ✓ Converted: {output_path}")
    return True

def convert_all_files():
    """school 폴더 내 모든 .tex 파일 변환 (Harvard + UIUC)"""
    base_path = Path("school")

    if not base_path.exists():
        print(f"Error: {base_path} not found")
        return

    # 모든 .tex 파일 찾기
    tex_files = list(base_path.glob("**/*.tex"))

    print(f"\n총 {len(tex_files)}개 파일 발견\n")

    success_count = 0
    fail_count = 0

    for tex_file in tex_files:
        try:
            convert_file(str(tex_file))
            success_count += 1
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            fail_count += 1

    print(f"\n" + "="*60)
    print(f"변환 완료: {success_count}개 성공, {fail_count}개 실패")
    print("="*60)

if __name__ == "__main__":
    import sys
    import io
    # Windows console encoding fix
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("LaTeX 문서 통합 템플릿 변환 시작...\n")
    convert_all_files()
