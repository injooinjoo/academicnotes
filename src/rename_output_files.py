#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
output 폴더의 PDF 파일명을 올바른 형식으로 변경하는 스크립트
"""

import os
from pathlib import Path

def rename_output_files():
    """output 폴더의 파일명 정리"""
    output_path = Path("output")

    if not output_path.exists():
        print(f"Error: {output_path} not found")
        return

    # CS109A 파일 (1-20)
    for i in range(1, 21):
        old_name = output_path / f"{i}.pdf"
        new_name = output_path / f"CS109A_lecture_{i:02d}.pdf"

        if old_name.exists() and not new_name.exists():
            os.rename(old_name, new_name)
            print(f"✓ {old_name.name} → {new_name.name}")

    # CSCI103 파일 (1-10) - 이미 변경됨
    # CSCI89 파일 (9-11)
    for i in [9, 10, 11]:
        old_name = output_path / f"{i}.pdf"
        new_name = output_path / f"CSCI89_lecture_{i:02d}.pdf"

        # 이 파일들은 CSCI89인지 다른 과목인지 확인 필요
        # 일단 csci89_XX.pdf 형식으로 되어 있는지 확인
        if old_name.exists():
            print(f"⚠️  {old_name.name}는 수동으로 확인 필요")

    print("\n완료!")

if __name__ == "__main__":
    import sys
    import io
    # Windows console encoding fix
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    rename_output_files()
