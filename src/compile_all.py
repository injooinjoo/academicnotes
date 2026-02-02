#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Academic Notes - 전체 컴파일 및 PDF 파일명 정리 스크립트
모든 TEX 파일을 컴파일하고 과목명_lecture_번호.pdf 형식으로 저장합니다.
"""

import sys
import subprocess
from pathlib import Path
from typing import Optional, Tuple
import re

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import (
    ProjectPaths,
    detect_tex_compiler,
    cleanup_aux_files,
    print_header,
    print_separator
)

# 과정별 짧은 이름
COURSE_SHORT_NAMES = {
    "cs109": "CS109A",
    "csci103": "CSCI103",
    "csci89": "CSCI89",
    "fin-574": "FIN574",
    "fin-571": "FIN571",
    "badm-572": "BADM572",
}


def detect_course_and_lecture(filepath: Path) -> Tuple[Optional[str], Optional[str]]:
    """
    파일 경로에서 과정명과 강의 번호 추출

    Returns:
        (course_code, lecture_num) 튜플
    """
    path_parts = filepath.parts

    course = None
    lecture_num = None

    for part in path_parts:
        if part in ['cs109', 'csci103', 'csci89', 'fin-574', 'fin-571', 'badm-572']:
            course = part
        if part.startswith('lecture_'):
            lecture_num = part.replace('lecture_', '').zfill(2)  # 01, 02, ... 형식

    # 파일명에서 강의 번호 추출 시도
    if not lecture_num:
        filename = filepath.stem
        nums = re.findall(r'\d+', filename)
        if nums:
            lecture_num = nums[0].zfill(2)

    return course, lecture_num


def generate_pdf_filename(course_code: Optional[str], lecture_num: Optional[str]) -> str:
    """
    과목명과 강의 번호로 PDF 파일명 생성

    예: CS109A_lecture_01.pdf, CSCI103_lecture_05.pdf
    """
    if not course_code or not lecture_num:
        return "lecture_note.pdf"

    course_short = COURSE_SHORT_NAMES.get(course_code, course_code.upper())
    return f"{course_short}_lecture_{lecture_num}.pdf"


def compile_single_file(tex_file: Path, output_dir: Path) -> bool:
    """
    단일 TEX 파일을 컴파일하고 적절한 이름으로 저장

    Args:
        tex_file: 컴파일할 .tex 파일 경로
        output_dir: PDF 저장 디렉토리

    Returns:
        성공 여부
    """
    print(f"\n{'='*70}")
    print(f"📄 컴파일: {tex_file.name}")
    print(f"{'='*70}")

    work_dir = tex_file.parent
    compiler = detect_tex_compiler(tex_file)

    print(f"작업 디렉토리: {work_dir}")
    print(f"컴파일러: {compiler}")

    # 과목명 및 강의 번호 감지
    course_code, lecture_num = detect_course_and_lecture(tex_file)
    output_filename = generate_pdf_filename(course_code, lecture_num)

    print(f"출력 파일명: {output_filename}")

    try:
        # 2회 컴파일 (목차, 참조 업데이트)
        print(f"\n2회 컴파일 실행 중...")

        for i in range(2):
            print(f"[{i+1}/2] 컴파일 중...", end=' ')

            result = subprocess.run(
                [compiler, '-interaction=nonstopmode', tex_file.name],
                cwd=str(work_dir),
                capture_output=True,
                text=True,
                timeout=120,
                encoding='utf-8',
                errors='replace'
            )

            if result.returncode != 0:
                print("⚠️  (경고 있음)")
            else:
                print("✓")

        # PDF 생성 확인
        pdf_file = tex_file.with_suffix('.pdf')
        if not pdf_file.exists():
            print(f"\n❌ 실패: PDF 파일이 생성되지 않았습니다.")

            # 로그 파일 확인
            log_file = tex_file.with_suffix('.log')
            if log_file.exists():
                print(f"\n⚠️  로그 파일을 확인하세요: {log_file}")
                # 로그에서 에러 라인 추출
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    log_content = f.read()
                    error_lines = [line for line in log_content.split('\n') if '!' in line or 'Error' in line]
                    if error_lines:
                        print("\n주요 에러:")
                        for line in error_lines[:5]:
                            print(f"  {line}")

            return False

        file_size = pdf_file.stat().st_size
        print(f"\n✅ 성공: {pdf_file.name} 생성됨 ({file_size:,} bytes)")

        # 보조 파일 정리
        cleaned = cleanup_aux_files(tex_file)
        if cleaned:
            print(f"🧹 임시 파일 정리: {', '.join(cleaned)}")

        # output 폴더로 복사 (이름 변경)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / output_filename

        import shutil
        shutil.copy2(pdf_file, output_path)
        print(f"📦 복사 완료: {output_path}")

        return True

    except subprocess.TimeoutExpired:
        print(f"\n❌ 실패: 컴파일 시간 초과 (120초)")
        return False

    except FileNotFoundError:
        print(f"\n❌ 실패: '{compiler}' 명령을 찾을 수 없습니다.")
        print(f"   LaTeX이 설치되어 있는지 확인하세요.")
        return False

    except Exception as e:
        print(f"\n❌ 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 함수"""
    print_header("📚 전체 LaTeX 파일 컴파일", width=70)

    # school 폴더 내 모든 .tex 파일 찾기
    school_path = Path("school")
    if not school_path.exists():
        print(f"❌ 오류: {school_path} 폴더를 찾을 수 없습니다.")
        return 1

    tex_files = sorted(school_path.rglob('*.tex'))

    if not tex_files:
        print(f"\n⚠️  TEX 파일을 찾을 수 없습니다.")
        return 1

    print(f"\n발견된 .tex 파일: {len(tex_files)}개")

    # output 디렉토리 설정
    paths = ProjectPaths()
    output_dir = paths.output

    print(f"출력 디렉토리: {output_dir}\n")
    print_separator(width=70)

    # 각 파일 컴파일
    success_count = 0
    fail_count = 0
    failed_files = []

    for tex_file in tex_files:
        if compile_single_file(tex_file, output_dir):
            success_count += 1
        else:
            fail_count += 1
            failed_files.append(str(tex_file))

    # 결과 요약
    print_separator(width=70)
    print(f"\n📊 컴파일 완료")
    print(f"✅ 성공: {success_count}개")
    print(f"❌ 실패: {fail_count}개")
    print(f"📊 총: {len(tex_files)}개")

    if failed_files:
        print(f"\n⚠️  실패한 파일 목록:")
        for f in failed_files:
            print(f"  - {f}")

    return 0 if fail_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
