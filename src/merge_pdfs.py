#!/usr/bin/env python3
"""Merge PDFs into integrated documents."""

from pathlib import Path
import glob

try:
    from PyPDF2 import PdfMerger
except ImportError:
    print("Installing PyPDF2...")
    import subprocess
    subprocess.run(['pip', 'install', 'PyPDF2'], capture_output=True)
    from PyPDF2 import PdfMerger

def merge_pdfs(pdf_files, output_path):
    """Merge multiple PDFs into one."""
    merger = PdfMerger()
    for pdf in sorted(pdf_files):
        try:
            print(f"  Adding: {Path(pdf).name}")
            merger.append(pdf)
        except Exception as e:
            print(f"  SKIPPED (error): {Path(pdf).name} - {e}")
    merger.write(output_path)
    merger.close()
    print(f"Created: {output_path}")

def main():
    base_dir = Path("C:/Dev/academicnotes")
    output_dir = base_dir / "output"
    english_dir = output_dir / "english"

    # Create integrated directories
    integrated_dir = output_dir / "integrated"
    integrated_dir.mkdir(exist_ok=True)

    # CS109A English
    print("\n=== Creating CS109A Complete English PDF ===")
    cs109_files = sorted(english_dir.glob("CS109A_Lecture_*_EN.pdf"))
    if cs109_files:
        merge_pdfs(cs109_files, integrated_dir / "CS109A_Complete_EN.pdf")

    # CSCI103 English
    print("\n=== Creating CSCI103 Complete English PDF ===")
    csci103_files = sorted(english_dir.glob("CSCI103_Lecture_*_EN.pdf"))
    if csci103_files:
        merge_pdfs(csci103_files, integrated_dir / "CSCI103_Complete_EN.pdf")

    # CSCI89 English
    print("\n=== Creating CSCI89 Complete English PDF ===")
    csci89_files = sorted(english_dir.glob("CSCI89_Lecture_*_EN.pdf"))
    if csci89_files:
        merge_pdfs(csci89_files, integrated_dir / "CSCI89_Complete_EN.pdf")

    # Korean PDFs (from main output folder)
    print("\n=== Creating CS109A Complete Korean PDF ===")
    cs109_kr = sorted(output_dir.glob("CS109A_Lecture_*.pdf"))
    cs109_kr = [f for f in cs109_kr if "_EN" not in f.name and "Complete" not in f.name]
    if cs109_kr:
        merge_pdfs(cs109_kr, integrated_dir / "CS109A_Complete_KR.pdf")

    print("\n=== Creating CSCI103 Complete Korean PDF ===")
    csci103_kr = sorted(output_dir.glob("CSCI103_Lecture_*.pdf"))
    csci103_kr = [f for f in csci103_kr if "_EN" not in f.name and "Complete" not in f.name]
    if csci103_kr:
        merge_pdfs(csci103_kr, integrated_dir / "CSCI103_Complete_KR.pdf")

    print("\n=== Creating CSCI89 Complete Korean PDF ===")
    csci89_kr = sorted(output_dir.glob("CSCI89_lecture_*.pdf"))
    csci89_kr = [f for f in csci89_kr if "_EN" not in f.name and "Complete" not in f.name]
    if csci89_kr:
        merge_pdfs(csci89_kr, integrated_dir / "CSCI89_Complete_KR.pdf")

    print("\n=== Done! ===")
    print(f"Integrated PDFs created in: {integrated_dir}")

if __name__ == '__main__':
    main()
