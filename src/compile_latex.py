#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Academic Notes - LaTeX Compiler
LaTeX 파일을 PDF로 컴파일하고 output 폴더로 복사합니다.
"""

import sys
import subprocess
import shutil
from pathlib import Path
from typing import Optional, List

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import (
    ProjectPaths,
    find_tex_files,
    detect_tex_compiler,
    cleanup_aux_files,
    print_header,
    print_separator
)


class LaTeXCompiler:
    """LaTeX 컴파일러 클래스"""

    def __init__(self, tex_file: Path, project_paths: Optional[ProjectPaths] = None):
        """
        Args:
            tex_file: 컴파일할 .tex 파일 경로
            project_paths: 프로젝트 경로 객체 (None이면 자동 생성)
        """
        self.tex_file = Path(tex_file).absolute()
        self.paths = project_paths or ProjectPaths()
        self.compiler = detect_tex_compiler(self.tex_file)
        self.work_dir = self.tex_file.parent
        self.pdf_file = self.tex_file.with_suffix('.pdf')

    def compile(self, num_runs: int = 2, timeout: int = 120) -> bool:
        """
        LaTeX 파일을 컴파일합니다.

        Args:
            num_runs: 컴파일 실행 횟수 (참조, 목차 등을 위해 보통 2회)
            timeout: 컴파일 타임아웃 (초)

        Returns:
            성공 여부
        """
        print(f"\n{'='*70}")
        print(f"📄 컴파일: {self.tex_file.name}")
        print(f"{'='*70}")
        print(f"작업 디렉토리: {self.work_dir}")
        print(f"컴파일러: {self.compiler}")

        try:
            print(f"\n{num_runs}회 컴파일 실행 중...")

            for i in range(num_runs):
                print(f"[{i+1}/{num_runs}] 컴파일 중...", end=' ')

                result = subprocess.run(
                    [self.compiler, '-interaction=nonstopmode', self.tex_file.name],
                    cwd=str(self.work_dir),
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    encoding='utf-8',
                    errors='replace'
                )

                # 에러가 있어도 계속 진행 (PDF가 생성되면 성공)
                if result.returncode != 0:
                    print("⚠️  (에러 있음)")
                else:
                    print("✓")

            # PDF 생성 확인
            if not self.pdf_file.exists():
                print(f"\n❌ 실패: PDF 파일이 생성되지 않았습니다.")
                return False

            file_size = self.pdf_file.stat().st_size
            print(f"\n✅ 성공: {self.pdf_file.name} 생성됨 ({file_size:,} bytes)")

            return True

        except subprocess.TimeoutExpired:
            print(f"\n❌ 실패: 컴파일 시간 초과 ({timeout}초)")
            return False

        except FileNotFoundError:
            print(f"\n❌ 실패: '{self.compiler}' 명령을 찾을 수 없습니다.")
            print(f"   LaTeX이 설치되어 있는지 확인하세요.")
            print(f"   설치: https://miktex.org/ (Windows) 또는 https://www.tug.org/texlive/")
            return False

        except Exception as e:
            print(f"\n❌ 실패: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def _print_error_details(self, result: subprocess.CompletedProcess):
        """컴파일 에러 상세 정보 출력"""
        print(f"\n❌ 에러 발생 (Return code: {result.returncode})")

        # stdout 출력
        if result.stdout and len(result.stdout) > 0:
            print("\n=== 컴파일 출력 (마지막 3000자) ===")
            print(result.stdout[-3000:])

        # stderr 출력
        if result.stderr and len(result.stderr) > 0:
            print("\n=== 에러 출력 ===")
            print(result.stderr)

        # 로그 파일 확인
        log_file = self.tex_file.with_suffix('.log')
        if log_file.exists():
            print(f"\n💡 자세한 로그: {log_file}")
            self._print_log_errors(log_file)

    def _print_log_errors(self, log_file: Path):
        """로그 파일에서 에러 추출 및 출력"""
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # 에러 관련 라인 찾기
            lines = content.split('\n')
            error_lines = []

            for idx, line in enumerate(lines):
                if any(keyword in line for keyword in ['!', 'Error', 'error', 'Fatal']):
                    # 에러 전후 2줄씩 포함
                    start = max(0, idx - 2)
                    end = min(len(lines), idx + 3)
                    error_lines.extend(lines[start:end])

            if error_lines:
                print("\n주요 에러 (로그 파일에서 추출):")
                # 마지막 20줄만 출력
                for line in error_lines[-20:]:
                    print(f"  {line}")

        except Exception as e:
            print(f"로그 파일 읽기 실패: {e}")

    def cleanup(self) -> List[str]:
        """
        컴파일 후 생성된 보조 파일들을 삭제합니다.

        Returns:
            삭제된 확장자 목록
        """
        cleaned = cleanup_aux_files(self.tex_file)
        if cleaned:
            print(f"🧹 임시 파일 정리: {', '.join(cleaned)}")
        return cleaned

    def copy_to_output(self, output_filename: Optional[str] = None) -> bool:
        """
        생성된 PDF를 output 폴더로 복사합니다.

        Args:
            output_filename: output 폴더에 저장할 파일명 (None이면 원본 이름 사용)

        Returns:
            성공 여부
        """
        if not self.pdf_file.exists():
            print(f"❌ PDF 파일이 존재하지 않습니다: {self.pdf_file}")
            return False

        # output 디렉토리 생성
        self.paths.output.mkdir(parents=True, exist_ok=True)

        # 파일명 결정
        if output_filename is None:
            output_filename = self.pdf_file.name

        output_path = self.paths.output / output_filename

        try:
            shutil.copy2(self.pdf_file, output_path)
            print(f"📦 복사 완료: {output_path}")
            return True

        except Exception as e:
            print(f"❌ 복사 실패: {e}")
            return False


def compile_tex_file(
    tex_file: Path,
    output_filename: Optional[str] = None,
    cleanup: bool = True,
    copy_to_output: bool = True
) -> bool:
    """
    LaTeX 파일을 컴파일하고 PDF를 생성합니다.

    Args:
        tex_file: 컴파일할 .tex 파일 경로
        output_filename: output 폴더에 저장할 파일명
        cleanup: 보조 파일 정리 여부
        copy_to_output: output 폴더로 복사 여부

    Returns:
        성공 여부
    """
    compiler = LaTeXCompiler(tex_file)

    # 컴파일
    if not compiler.compile():
        return False

    # 보조 파일 정리
    if cleanup:
        compiler.cleanup()

    # output 폴더로 복사
    if copy_to_output:
        if not compiler.copy_to_output(output_filename):
            return False

    return True


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(
        description='LaTeX 파일을 PDF로 컴파일하고 output 폴더로 복사합니다.'
    )
    parser.add_argument(
        'path',
        type=str,
        nargs='?',
        default='.',
        help='컴파일할 .tex 파일 또는 디렉토리 경로 (기본값: 현재 디렉토리)'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='output 폴더에 저장할 파일명 (지정하지 않으면 원본 이름 사용)'
    )
    parser.add_argument(
        '--no-cleanup',
        action='store_true',
        help='보조 파일을 정리하지 않음'
    )
    parser.add_argument(
        '--no-copy',
        action='store_true',
        help='output 폴더로 복사하지 않음'
    )
    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        help='하위 디렉토리까지 재귀적으로 검색'
    )

    args = parser.parse_args()

    print_header("📚 LaTeX to PDF Compiler", width=70)

    target_path = Path(args.path)

    # .tex 파일 찾기
    if target_path.is_file() and target_path.suffix == '.tex':
        tex_files = [target_path]
    elif target_path.is_dir():
        if args.recursive:
            tex_files = list(target_path.rglob('*.tex'))
        else:
            tex_files = list(target_path.glob('*.tex'))
    else:
        print(f"❌ 오류: '{target_path}'는 유효한 .tex 파일이나 디렉토리가 아닙니다.")
        return 1

    if not tex_files:
        print(f"\n⚠️  '{target_path}'에서 .tex 파일을 찾을 수 없습니다.")
        return 1

    print(f"\n발견된 .tex 파일: {len(tex_files)}개")
    for tex_file in tex_files:
        print(f"  - {tex_file.name}")

    print_separator(width=70)

    # 각 파일 컴파일
    success_count = 0
    fail_count = 0

    for tex_file in tex_files:
        # 파일이 여러 개인 경우 output 파일명 자동 생성
        if len(tex_files) > 1 and not args.output:
            output_filename = None  # 원본 이름 사용
        else:
            output_filename = args.output

        if compile_tex_file(
            tex_file,
            output_filename=output_filename,
            cleanup=not args.no_cleanup,
            copy_to_output=not args.no_copy
        ):
            success_count += 1
        else:
            fail_count += 1

    # 결과 요약
    print_separator(width=70)
    print(f"\n📊 컴파일 완료")
    print(f"✅ 성공: {success_count}개")
    print(f"❌ 실패: {fail_count}개")
    print(f"📊 총: {len(tex_files)}개")

    return 0 if fail_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
