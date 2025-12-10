#!/usr/bin/env python3
"""
모든 TEX 파일에서 \maketitle 제거
"""
from pathlib import Path

def fix_maketitle(tex_file):
    """Remove \maketitle from tex file"""
    with open(tex_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    modified = False
    new_lines = []
    for line in lines:
        if line.strip() == r'\maketitle':
            modified = True
            continue  # Skip this line
        new_lines.append(line)

    if modified:
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True
    return False

def main():
    school_path = Path("school")
    tex_files = list(school_path.rglob("*.tex"))

    fixed_count = 0
    for tex_file in tex_files:
        if fix_maketitle(tex_file):
            print(f"Fixed: {tex_file}")
            fixed_count += 1

    print(f"\n총 {fixed_count}개 파일 수정 완료")

if __name__ == "__main__":
    main()
