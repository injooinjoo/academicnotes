#!/usr/bin/env python3
"""Compile all English TEX files to PDF."""

import os
import subprocess
import glob
from pathlib import Path

def compile_tex(tex_file):
    """Compile a TEX file using xelatex."""
    tex_path = Path(tex_file)
    output_dir = tex_path.parent

    # Run xelatex twice for references
    for _ in range(2):
        result = subprocess.run(
            ['xelatex', '-interaction=nonstopmode', '-output-directory=' + str(output_dir), str(tex_path)],
            capture_output=True,
            text=True,
            cwd=str(output_dir)
        )

    # Check if PDF was created
    pdf_path = tex_path.with_suffix('.pdf')
    if pdf_path.exists():
        return True, str(pdf_path)
    else:
        return False, result.stderr

def main():
    base_dir = Path(__file__).parent.parent

    # Find all English TEX files
    patterns = [
        'school/harvard/cs109/**/[0-9]*_en.tex',
        'school/harvard/csci103/**/[0-9]*_en.tex',
        'school/harvard/csci89/**/csci89_*_en.tex',
    ]

    tex_files = []
    for pattern in patterns:
        tex_files.extend(glob.glob(str(base_dir / pattern), recursive=True))

    tex_files.sort()

    print(f"Found {len(tex_files)} English TEX files to compile")

    success_count = 0
    fail_count = 0

    for tex_file in tex_files:
        print(f"Compiling: {tex_file}")
        success, result = compile_tex(tex_file)
        if success:
            print(f"  SUCCESS: {result}")
            success_count += 1
        else:
            print(f"  FAILED")
            fail_count += 1

    print(f"\nCompleted: {success_count} success, {fail_count} failed")

if __name__ == '__main__':
    main()
