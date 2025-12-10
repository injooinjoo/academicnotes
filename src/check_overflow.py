#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
컴파일된 PDF의 overflow 경고를 체크하는 스크립트
"""

import subprocess
from pathlib import Path
import re

def check_tex_log_for_overflow(tex_file):
    """TEX 파일의 로그에서 overfull/underfull 경고 확인"""
    log_file = tex_file.with_suffix('.log')

    if not log_file.exists():
        return None, []

    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        log_content = f.read()

    # Overfull \hbox 찾기 (가로 overflow)
    overfull_hbox = re.findall(r'Overfull \\hbox \(([0-9.]+)pt too wide\)', log_content)

    # Overfull \vbox 찾기 (세로 overflow)
    overfull_vbox = re.findall(r'Overfull \\vbox \(([0-9.]+)pt too high\)', log_content)

    issues = []

    if overfull_hbox:
        max_hbox = max(float(x) for x in overfull_hbox)
        issues.append(f"Overfull hbox: {len(overfull_hbox)}회 (최대 {max_hbox:.1f}pt)")

    if overfull_vbox:
        max_vbox = max(float(x) for x in overfull_vbox)
        issues.append(f"Overfull vbox: {len(overfull_vbox)}회 (최대 {max_vbox:.1f}pt)")

    return max(float(x) for x in overfull_hbox) if overfull_hbox else 0, issues

def compile_and_check(tex_file):
    """TEX 파일 컴파일 및 overflow 체크"""
    try:
        # 컴파일
        result = subprocess.run(
            ['python', 'src/compile_latex.py', str(tex_file)],
            capture_output=True,
            text=True,
            timeout=120,
            encoding='utf-8'
        )

        if result.returncode != 0:
            return False, ["컴파일 실패"]

        # 로그 체크
        max_overflow, issues = check_tex_log_for_overflow(tex_file)

        return True, issues

    except Exception as e:
        return False, [f"에러: {e}"]

def main():
    """메인 실행 함수"""
    base_path = Path("school")

    if not base_path.exists():
        print(f"Error: {base_path} not found")
        return

    # 모든 TEX 파일 찾기
    tex_files = sorted(base_path.glob("**/*.tex"))

    print("=" * 80)
    print("📚 PDF Overflow 체크")
    print("=" * 80)
    print(f"\n총 {len(tex_files)}개 파일 체크 중...\n")

    problem_files = []

    for i, tex_file in enumerate(tex_files, 1):
        print(f"[{i}/{len(tex_files)}] {tex_file.name: <20}", end=" ")

        success, issues = compile_and_check(tex_file)

        if not success:
            print("✗ 컴파일 실패")
            problem_files.append((tex_file, issues))
        elif issues:
            print(f"⚠️  Overflow 감지")
            for issue in issues:
                print(f"      {issue}")
            problem_files.append((tex_file, issues))
        else:
            print("✓ OK")

    print("\n" + "=" * 80)
    print("📊 요약")
    print("=" * 80)

    if problem_files:
        print(f"\n⚠️  문제 파일: {len(problem_files)}개\n")

        for tex_file, issues in problem_files:
            print(f"📄 {tex_file}")
            for issue in issues:
                print(f"   - {issue}")
            print()
    else:
        print("\n✅ 모든 파일 정상!")

    print("=" * 80)

if __name__ == "__main__":
    import sys
    import io
    # Windows console encoding fix
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    main()
