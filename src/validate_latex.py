#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LaTeX 파일 검증 및 자동 수정 스크립트
latex_upgrade.txt 기준으로 모든 TEX 파일을 검증하고 수정합니다.
"""

import sys
import io
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 마스터 템플릿 헤더
MASTER_TEMPLATE_HEADER = """%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Harvard Academic Notes - 통합 마스터 템플릿
% 모든 강의 노트에 적용되는 통일된 스타일"""

# 과목별 메타정보
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
    }
}


class LaTeXValidator:
    """LaTeX 파일 검증 및 수정 클래스"""

    def __init__(self, tex_file: Path):
        self.tex_file = tex_file
        self.content = ""
        self.issues = []
        self.fixes = []
        self.modified = False

    def load(self) -> bool:
        """파일 읽기"""
        try:
            with open(self.tex_file, 'r', encoding='utf-8') as f:
                self.content = f.read()
            return True
        except Exception as e:
            print(f"  [ERROR] 파일 읽기 실패: {e}")
            return False

    def save(self) -> bool:
        """파일 저장"""
        if not self.modified:
            return True
        try:
            with open(self.tex_file, 'w', encoding='utf-8') as f:
                f.write(self.content)
            return True
        except Exception as e:
            print(f"  [ERROR] 파일 저장 실패: {e}")
            return False

    def check_preamble_after_document(self) -> bool:
        """
        검증 1: \\begin{document} 이후 프리앰블 명령 체크
        """
        doc_match = re.search(r'\\begin\{document\}', self.content)
        if not doc_match:
            self.issues.append("\\begin{document} 없음")
            return False

        doc_start = doc_match.end()
        body = self.content[doc_start:]

        # 프리앰블 명령어 패턴
        preamble_patterns = [
            (r'\\usepackage\{[^}]*\}', 'usepackage'),
            (r'\\newcommand\{[^}]*\}', 'newcommand'),
            (r'\\renewcommand\{[^}]*\}', 'renewcommand'),
            (r'\\newtcolorbox\{[^}]*\}', 'newtcolorbox'),
            (r'\\definecolor\{[^}]*\}', 'definecolor'),
            (r'\\tcbuselibrary\{[^}]*\}', 'tcbuselibrary'),
        ]

        found_issues = []
        for pattern, name in preamble_patterns:
            matches = list(re.finditer(pattern, body))
            if matches:
                for match in matches:
                    line_num = self.content[:doc_start + match.start()].count('\n') + 1
                    found_issues.append((name, line_num, match.group()))

        if found_issues:
            for name, line, cmd in found_issues:
                self.issues.append(f"\\begin{{document}} 이후 {name} 명령 발견 (라인 {line})")
                # 자동 수정: 해당 라인 제거
                self.content = self.content.replace(cmd + '\n', '')
                self.fixes.append(f"{name} 명령 제거 (라인 {line})")
                self.modified = True
            return False
        return True

    def check_unclosed_environments(self) -> bool:
        """
        검증 2: 닫히지 않은 환경 검사
        """
        # 주요 환경들
        envs = ['itemize', 'enumerate', 'tabular', 'table', 'figure',
                'equation', 'align', 'lstlisting', 'verbatim',
                'summarybox', 'warningbox', 'examplebox', 'infobox',
                'overviewbox', 'definitionbox', 'importantbox', 'cautionbox',
                'tcolorbox', 'center', 'minipage']

        issues_found = False
        for env in envs:
            begins = len(re.findall(rf'\\begin\{{{env}\}}', self.content))
            ends = len(re.findall(rf'\\end\{{{env}\}}', self.content))

            if begins != ends:
                self.issues.append(f"환경 불일치: {env} (begin: {begins}, end: {ends})")
                issues_found = True

        return not issues_found

    def check_first_page_structure(self) -> bool:
        """
        검증 3: 첫 페이지 구조 통일 확인
        표준: \\begin{document} → \\thispagestyle{firstpage} → \\metainfo → \\tableofcontents
        """
        doc_match = re.search(r'\\begin\{document\}', self.content)
        if not doc_match:
            return False

        doc_start = doc_match.end()
        # 첫 500자 정도만 확인
        first_part = self.content[doc_start:doc_start + 2000]

        has_thispagestyle = '\\thispagestyle{firstpage}' in first_part
        has_metainfo = '\\metainfo{' in first_part
        has_toc = '\\tableofcontents' in first_part

        issues = []
        if not has_thispagestyle:
            issues.append("\\thispagestyle{firstpage} 없음")
        if not has_metainfo:
            issues.append("\\metainfo 없음")
        if not has_toc:
            issues.append("\\tableofcontents 없음")

        if issues:
            self.issues.extend(issues)
            # 자동 수정 시도
            if not has_metainfo:
                self._add_metainfo()
            if not has_toc and has_metainfo:
                self._add_tableofcontents()
            return False

        return True

    def _add_metainfo(self):
        """메타정보 블록 추가"""
        # 과목 감지
        path_str = str(self.tex_file).lower()
        course = None
        lecture_num = "01"

        for key in COURSE_META:
            if key in path_str:
                course = key
                break

        # 강의 번호 감지
        match = re.search(r'lecture_(\d+)', path_str)
        if match:
            lecture_num = match.group(1).zfill(2)

        if course:
            meta = COURSE_META[course]
            metainfo = f'\\metainfo{{{meta["name"]}}}{{Lecture {lecture_num}}}{{{meta["prof"]}}}{{Lecture {lecture_num}의 핵심 개념 학습}}'

            # \begin{document} 바로 다음에 추가
            doc_match = re.search(r'(\\begin\{document\})', self.content)
            if doc_match:
                insert_pos = doc_match.end()
                insert_text = f'\n\n\\thispagestyle{{firstpage}}\n\n{metainfo}\n'
                self.content = self.content[:insert_pos] + insert_text + self.content[insert_pos:]
                self.fixes.append("metainfo 블록 추가")
                self.modified = True

    def _add_tableofcontents(self):
        """목차 추가"""
        # metainfo 다음에 추가
        metainfo_match = re.search(r'(\\metainfo\{[^}]*\}\{[^}]*\}\{[^}]*\}\{[^}]*\})', self.content)
        if metainfo_match:
            insert_pos = metainfo_match.end()
            insert_text = '\n\n\\tableofcontents\n\\newpage\n'
            self.content = self.content[:insert_pos] + insert_text + self.content[insert_pos:]
            self.fixes.append("tableofcontents 추가")
            self.modified = True

    def check_table_width(self) -> bool:
        """
        검증 4: 표 가로 크기 자동 조절 확인
        넓은 표는 adjustbox로 감싸야 함
        """
        # tabular 환경 찾기
        tabular_pattern = r'\\begin\{tabular\}\{([^}]+)\}'
        matches = list(re.finditer(tabular_pattern, self.content))

        issues_found = False
        for match in matches:
            col_spec = match.group(1)
            # 컬럼이 5개 이상이면 넓은 표로 판단
            col_count = len(re.findall(r'[lcr|p]', col_spec))

            if col_count >= 5:
                # adjustbox로 감싸져 있는지 확인
                start = match.start()
                # 앞 100자 확인
                before = self.content[max(0, start-100):start]

                if 'adjustbox' not in before:
                    line_num = self.content[:start].count('\n') + 1
                    self.issues.append(f"넓은 표({col_count}컬럼)가 adjustbox 없음 (라인 {line_num})")
                    issues_found = True

        return not issues_found

    def check_template_header(self) -> bool:
        """
        검증 5: 마스터 템플릿 헤더 확인
        """
        if MASTER_TEMPLATE_HEADER not in self.content[:500]:
            self.issues.append("마스터 템플릿 헤더 없음")
            return False
        return True

    def validate_all(self) -> Dict:
        """모든 검증 실행"""
        if not self.load():
            return {"success": False, "issues": ["파일 읽기 실패"], "fixes": []}

        results = {
            "preamble": self.check_preamble_after_document(),
            "environments": self.check_unclosed_environments(),
            "first_page": self.check_first_page_structure(),
            "table_width": self.check_table_width(),
            "template": self.check_template_header()
        }

        # 수정사항이 있으면 저장
        if self.modified:
            self.save()

        return {
            "success": all(results.values()),
            "results": results,
            "issues": self.issues,
            "fixes": self.fixes,
            "modified": self.modified
        }


def find_tex_files(base_path: Path) -> List[Path]:
    """harvard 폴더 내 모든 .tex 파일 찾기"""
    tex_files = []
    harvard_path = base_path / "school" / "harvard"

    if harvard_path.exists():
        tex_files = list(harvard_path.rglob("*.tex"))

    return sorted(tex_files)


def main():
    """메인 함수"""
    print("=" * 60)
    print("TEX 파일 품질 검증 시작")
    print("=" * 60)

    base_path = Path(".")
    tex_files = find_tex_files(base_path)

    print(f"\n총 파일 수: {len(tex_files)}개\n")

    results = {
        "total": len(tex_files),
        "passed": 0,
        "failed": 0,
        "modified": 0,
        "files": {}
    }

    passed_files = []
    failed_files = []

    for tex_file in tex_files:
        relative_path = tex_file.relative_to(base_path)
        print(f"검증 중: {relative_path}")

        validator = LaTeXValidator(tex_file)
        result = validator.validate_all()

        results["files"][str(relative_path)] = result

        if result["success"]:
            results["passed"] += 1
            passed_files.append(relative_path)
            print(f"  [PASS] 모든 검증 통과")
        else:
            results["failed"] += 1
            failed_files.append((relative_path, result))
            for issue in result["issues"]:
                print(f"  [ISSUE] {issue}")
            for fix in result["fixes"]:
                print(f"  [FIX] {fix}")

        if result["modified"]:
            results["modified"] += 1

    # 결과 보고서 출력
    print("\n")
    print("=" * 60)
    print("TEX 파일 품질 검증 결과")
    print("=" * 60)

    print(f"\n총 파일 수: {results['total']}개")
    print(f"검증 통과: {results['passed']}개")
    print(f"문제 발견: {results['failed']}개")
    print(f"수정됨: {results['modified']}개")

    if failed_files:
        print("\n=== 문제가 있는 파일 목록 ===\n")
        for i, (path, result) in enumerate(failed_files, 1):
            print(f"{i}. {path}")
            for issue in result["issues"]:
                print(f"   - [문제] {issue}")
            for fix in result["fixes"]:
                print(f"   - [해결] {fix}")
            print()

    if passed_files:
        print("\n=== 검증 통과 파일 ===\n")
        for path in passed_files:
            print(f"- {path} [OK]")

    print("\n=== 최종 통계 ===")
    print(f"[OK] 에러 없음: {results['passed']}개")
    print(f"[OK] 수정 완료: {results['modified']}개")

    if results['failed'] == 0:
        print("\n모든 검증 항목 통과!")

    return 0 if results['failed'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
