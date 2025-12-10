#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
모든 TEX 파일을 재컴파일하는 스크립트
"""

import subprocess
from pathlib import Path
import time

def compile_file(tex_file):
    """단일 TEX 파일 컴파일"""
    try:
        result = subprocess.run(
            ['python', 'src/compile_latex.py', str(tex_file)],
            capture_output=True,
            text=True,
            timeout=120,
            encoding='utf-8'
        )
        return result.returncode == 0
    except Exception as e:
        print(f"  ✗ 컴파일 실패: {e}")
        return False

def main():
    """메인 실행 함수"""
    base_path = Path("school")

    if not base_path.exists():
        print(f"Error: {base_path} not found")
        return

    # 모든 TEX 파일 찾기
    tex_files = sorted(base_path.glob("**/*.tex"))

    print("=" * 80)
    print("📚 전체 PDF 재컴파일")
    print("=" * 80)
    print(f"\n총 {len(tex_files)}개 파일 컴파일 시작...\n")

    success_count = 0
    fail_count = 0
    start_time = time.time()

    for i, tex_file in enumerate(tex_files, 1):
        print(f"[{i}/{len(tex_files)}] {tex_file}")

        if compile_file(tex_file):
            success_count += 1
            print(f"  ✓ 성공")
        else:
            fail_count += 1
            print(f"  ✗ 실패")

    elapsed = time.time() - start_time

    print("\n" + "=" * 80)
    print("📊 컴파일 완료")
    print("=" * 80)
    print(f"✅ 성공: {success_count}개")
    print(f"❌ 실패: {fail_count}개")
    print(f"⏱️  소요 시간: {elapsed:.1f}초")
    print("=" * 80)

if __name__ == "__main__":
    import sys
    import io
    # Windows console encoding fix
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    main()
