#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Academic Notes - 템플릿 적용 스크립트
모든 .tex 파일의 프리앰블을 통일된 템플릿으로 교체합니다.
"""

import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import ProjectPaths, print_header, print_separator


class TemplateApplicator:
    """템플릿 적용 클래스"""

    # 과목명 매핑
    COURSE_NAMES = {
        'csci103': 'CSCI E-103: 데이터 엔지니어링 입문',
        'csci89': 'CSCI E-89B: 자연어 처리 입문',
        'cs109': 'CS 109: 데이터 사이언스',
        'fin574': 'FIN 574: 기업 수준 경제학',
    }

    def __init__(self, template_path: Path, project_paths: Optional[ProjectPaths] = None):
        """
        Args:
            template_path: 템플릿 파일 경로
            project_paths: 프로젝트 경로 객체
        """
        self.template_path = Path(template_path)
        self.paths = project_paths or ProjectPaths()
        self.template_content = self._load_template()

    def _load_template(self) -> str:
        """템플릿 파일 로드"""
        with open(self.template_path, 'r', encoding='utf-8') as f:
            return f.read()

    def extract_body(self, tex_content: str) -> Tuple[str, str]:
        """
        .tex 파일에서 프리앰블과 본문을 분리합니다.

        Args:
            tex_content: 전체 .tex 파일 내용

        Returns:
            (preamble, body) 튜플
        """
        # \begin{document}를 기준으로 분리
        match = re.search(r'\\begin\{document\}', tex_content)
        if match:
            split_pos = match.start()
            preamble = tex_content[:split_pos].strip()
            body = tex_content[split_pos:].strip()
            return preamble, body
        else:
            # \begin{document}가 없으면 전체를 본문으로 간주
            return '', tex_content

    def extract_title_info(self, tex_content: str) -> Dict[str, str]:
        """
        기존 .tex 파일에서 제목 정보를 추출합니다.

        Args:
            tex_content: 전체 .tex 파일 내용

        Returns:
            {'title': '...', 'author': '...', 'date': '...'} 딕셔너리
        """
        info = {}

        # \title 추출
        title_match = re.search(r'\\title\{([^}]+)\}', tex_content)
        if title_match:
            info['title'] = title_match.group(1)

        # \author 추출
        author_match = re.search(r'\\author\{([^}]+)\}', tex_content)
        if author_match:
            info['author'] = author_match.group(1)

        # \date 추출
        date_match = re.search(r'\\date\{([^}]+)\}', tex_content)
        if date_match:
            info['date'] = date_match.group(1)

        return info

    def infer_course_info(self, tex_file: Path) -> Tuple[str, str, int]:
        """
        파일 경로에서 과목 정보를 추론합니다.

        Args:
            tex_file: .tex 파일 경로

        Returns:
            (course_code, course_name, lecture_num) 튜플
        """
        # 파일명에서 정보 추출
        # 예: csci103_01.tex -> csci103, 1
        filename = tex_file.stem
        match = re.match(r'([a-z]+\d+)_(\d+)', filename)

        if match:
            course_code = match.group(1)
            lecture_num = int(match.group(2))
        else:
            course_code = 'unknown'
            lecture_num = 1

        # 과목명 가져오기
        course_name = self.COURSE_NAMES.get(course_code, f'{course_code.upper()} 강의')

        return course_code, course_name, lecture_num

    def add_overview_section(self, body: str) -> str:
        """
        본문에 개요 섹션을 추가합니다 (없는 경우에만).

        Args:
            body: 본문 내용

        Returns:
            개요 섹션이 추가된 본문
        """
        # 이미 overviewbox가 있는지 확인
        if 'overviewbox' in body:
            return body

        # \begin{document} 다음에 개요 추가
        overview_template = r'''
% 개요 섹션
\begin{overviewbox}
\textbf{학습 목표:}
\begin{itemize}
    \item 이 강의의 핵심 개념을 이해합니다
    \item 실전에 적용할 수 있는 지식을 습득합니다
\end{itemize}

\textbf{주요 키워드:} [자동으로 채워질 예정]

\textbf{선행 지식:} 기본적인 컴퓨터 사용 능력
\end{overviewbox}

'''

        # \begin{document} 바로 다음에 삽입
        body = body.replace('\\begin{document}',
                           '\\begin{document}\n' + overview_template)

        return body

    def add_table_of_contents(self, body: str) -> str:
        """
        본문에 목차를 추가합니다 (없는 경우에만).

        Args:
            body: 본문 내용

        Returns:
            목차가 추가된 본문
        """
        # 이미 tableofcontents가 있는지 확인
        if '\\tableofcontents' in body:
            return body

        # overviewbox 다음에 목차 추가
        if 'overviewbox' in body:
            # overviewbox 종료 바로 다음에 삽입
            body = re.sub(
                r'(\\end\{overviewbox\})',
                r'\1\n\n% 목차\n\\tableofcontents\n\\newpage\n',
                body,
                count=1
            )
        else:
            # \begin{document} 다음에 삽입
            body = body.replace(
                '\\begin{document}',
                '\\begin{document}\n\n% 목차\n\\tableofcontents\n\\newpage\n'
            )

        return body

    def fix_overfull_boxes(self, body: str) -> str:
        """
        칸 넘어가는 문제를 수정합니다.

        Args:
            body: 본문 내용

        Returns:
            수정된 본문
        """
        # 1. 긴 URL을 \url{} 또는 \href{}로 감싸기
        # http나 https로 시작하는 긴 URL 찾기
        def wrap_urls(match):
            url = match.group(0)
            if '\\url{' in url or '\\href{' in url:
                return url  # 이미 감싸져 있음
            return f'\\url{{{url}}}'

        body = re.sub(
            r'https?://[^\s\)]+',
            wrap_urls,
            body
        )

        # 2. 긴 코드/명령어를 \texttt{}로 감싸기
        # 이미 감싸져 있지 않은 30자 이상의 연속된 문자열
        def wrap_long_monospace(match):
            text = match.group(0)
            if len(text) > 30 and '\\' not in text and not text.startswith('http'):
                return f'\\texttt{{{text}}}'
            return text

        # 3. 표(tabular) 환경의 컬럼 너비 문제 수정
        # & 기호가 너무 많은지 확인하고 tabularx로 변환

        # 4. 긴 단어에 하이픈 허용
        # 특정 기술 용어들에 대해 \- 추가
        long_technical_terms = [
            'Transformation', 'Classification', 'Optimization',
            'Implementation', 'Architecture', 'Infrastructure',
            'Authentication', 'Authorization', 'Configuration'
        ]

        for term in long_technical_terms:
            # 단어를 하이픈 허용 버전으로 변경
            # 예: Implementation -> Imple\-men\-ta\-tion
            if term in body:
                hyphenated = '\\-'.join([term[i:i+4] for i in range(0, len(term), 4)])
                body = body.replace(term, hyphenated)

        return body

    def apply_template(self, tex_file: Path, dry_run: bool = False) -> bool:
        """
        하나의 .tex 파일에 템플릿을 적용합니다.

        Args:
            tex_file: .tex 파일 경로
            dry_run: True이면 실제로 파일을 수정하지 않음

        Returns:
            성공 여부
        """
        print(f"\n처리 중: {tex_file.name}")

        try:
            # 파일 읽기
            with open(tex_file, 'r', encoding='utf-8') as f:
                original_content = f.read()

            # 본문 추출
            _, body = self.extract_body(original_content)

            # 과목 정보 추론
            course_code, course_name, lecture_num = self.infer_course_info(tex_file)
            lecture_title = f'강의 {lecture_num:02d}'

            print(f"  과목: {course_name}")
            print(f"  강의: {lecture_title}")

            # 템플릿 복사 및 변수 설정
            new_preamble = self.template_content.replace(
                '\\COURSENAME', course_name
            ).replace(
                '\\LECTURETITLE', lecture_title
            )

            # 본문 개선
            body = self.add_overview_section(body)
            body = self.add_table_of_contents(body)
            body = self.fix_overfull_boxes(body)

            # 새로운 내용 구성
            new_content = new_preamble + '\n\n' + body

            if dry_run:
                print(f"  [DRY RUN] 변경 사항이 있을 것으로 예상됩니다")
                return True

            # 파일 쓰기
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(new_content)

            print(f"  ✅ 템플릿 적용 완료")
            return True

        except Exception as e:
            print(f"  ❌ 실패: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(
        description='모든 .tex 파일에 통일된 템플릿을 적용합니다.'
    )
    parser.add_argument(
        '--template',
        type=str,
        default='templates/standard_preamble.tex',
        help='템플릿 파일 경로'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='실제로 파일을 수정하지 않고 시뮬레이션만 수행'
    )
    parser.add_argument(
        '--course',
        type=str,
        help='특정 과목만 처리 (예: csci103, cs109)'
    )

    args = parser.parse_args()

    print_header("📄 LaTeX 템플릿 적용", width=70)

    if args.dry_run:
        print("\n⚠️  DRY RUN 모드: 실제로 파일을 수정하지 않습니다.\n")

    paths = ProjectPaths()
    template_path = paths.root / args.template

    if not template_path.exists():
        print(f"❌ 템플릿 파일을 찾을 수 없습니다: {template_path}")
        return 1

    applicator = TemplateApplicator(template_path, paths)

    # .tex 파일 찾기
    if args.course:
        # 특정 과목만
        tex_files = list(paths.school.rglob(f'**/{args.course}_*.tex'))
    else:
        # 모든 과목
        tex_files = []
        for pattern in ['**/csci103_*.tex', '**/csci89_*.tex', '**/cs109_*.tex', '**/fin574_*.tex']:
            tex_files.extend(paths.school.glob(pattern))

    if not tex_files:
        print("⚠️  처리할 .tex 파일을 찾을 수 없습니다.")
        return 1

    print(f"\n발견된 .tex 파일: {len(tex_files)}개")
    print_separator(width=70)

    # 각 파일 처리
    success_count = 0
    fail_count = 0

    for tex_file in sorted(tex_files):
        if applicator.apply_template(tex_file, dry_run=args.dry_run):
            success_count += 1
        else:
            fail_count += 1

    # 결과 요약
    print_separator(width=70)
    print(f"\n📊 템플릿 적용 완료")
    print(f"✅ 성공: {success_count}개")
    print(f"❌ 실패: {fail_count}개")
    print(f"📊 총: {len(tex_files)}개")

    if args.dry_run:
        print("\n💡 실제로 파일을 수정하려면 --dry-run 옵션 없이 다시 실행하세요.")

    return 0 if fail_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
