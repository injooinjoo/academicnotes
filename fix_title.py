#!/usr/bin/env python3
"""
모든 TEX 파일에 \title, \author, \date 추가 및 구조 수정
"""
from pathlib import Path
import re

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
        nums = re.findall(r'\d+', filename)
        if nums:
            lecture_num = nums[0]

    return course, lecture_num

def fix_title(tex_file):
    """TEX 파일에 title, author, date 추가"""
    course_code, lecture_num = detect_course_and_lecture(tex_file)

    if not course_code or course_code not in COURSE_META:
        print(f"  Skip: {tex_file} (unknown course)")
        return False

    meta = COURSE_META[course_code]
    course_name = meta["name"]
    prof_name = meta["prof"]
    lecture_str = f"Lecture {lecture_num}" if lecture_num else ""

    with open(tex_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 이미 title이 정의되어 있는지 확인
    if r'\title{' in content:
        return False  # 이미 있으면 스킵

    # \begin{document} 찾기
    doc_start = content.find(r'\begin{document}')
    if doc_start == -1:
        return False

    # preamble 끝 위치 (여러 줄 백슬래시들 다음)
    preamble_end = content.rfind('\n', 0, doc_start)

    # title, author, date 추가
    title_block = f"""
% --- Title Information ---
\\title{{{course_name} \\\\ {lecture_str}}}
\\author{{{prof_name}}}
\\date{{\\today}}

"""

    # preamble 끝에 title 정보 삽입
    new_content = content[:preamble_end+1] + title_block + content[preamble_end+1:]

    with open(tex_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return True

def main():
    school_path = Path("school")
    tex_files = list(school_path.rglob("*.tex"))

    fixed_count = 0
    for tex_file in tex_files:
        if fix_title(tex_file):
            print(f"Fixed: {tex_file}")
            fixed_count += 1

    print(f"\n총 {fixed_count}개 파일 수정 완료")

if __name__ == "__main__":
    main()
