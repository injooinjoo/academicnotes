"""
PDF에서 순수 텍스트를 추출하여 같은 이름의 .txt 파일로 저장하는 스크립트.
"""

import sys
from pathlib import Path

import pymupdf


TARGET_DIRS = [
    "school/uiuc/badm-572/source",
    "school/uiuc/fin-571/source",
]


def extract_text_from_pdf(pdf_path: Path) -> str:
    doc = pymupdf.open(pdf_path)
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return "\n".join(text_parts)


def main():
    project_root = Path(__file__).resolve().parent.parent

    total = 0
    for rel_dir in TARGET_DIRS:
        source_dir = project_root / rel_dir
        if not source_dir.exists():
            print(f"[SKIP] Directory not found: {source_dir}")
            continue

        pdf_files = sorted(source_dir.glob("*.pdf"))
        if not pdf_files:
            print(f"[SKIP] No PDF files in: {source_dir}")
            continue

        for pdf_path in pdf_files:
            txt_path = pdf_path.with_suffix(".txt")
            try:
                text = extract_text_from_pdf(pdf_path)
                txt_path.write_text(text, encoding="utf-8")
                print(f"[OK] {txt_path.relative_to(project_root)}")
                total += 1
            except Exception as e:
                print(f"[ERROR] {pdf_path.name}: {e}", file=sys.stderr)

    print(f"\nDone. {total} files converted.")


if __name__ == "__main__":
    main()
