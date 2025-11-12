#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Academic Notes - Migration Script
기존 파일들을 새로운 디렉토리 구조로 재배치합니다.
"""

import sys
import shutil
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import ProjectPaths, print_header, print_separator


class FileMigrator:
    """파일 마이그레이션 클래스"""

    def __init__(self, project_paths: Optional[ProjectPaths] = None, dry_run: bool = False):
        """
        Args:
            project_paths: 프로젝트 경로 객체
            dry_run: True이면 실제로 파일을 이동하지 않고 시뮬레이션만 수행
        """
        self.paths = project_paths or ProjectPaths()
        self.dry_run = dry_run
        self.migrations = []  # (source, dest) 튜플 리스트

    def parse_lecture_number(self, filename: str) -> Optional[int]:
        """
        파일명에서 강의 번호를 추출합니다.

        Args:
            filename: 파일명 (예: 'cs103-day1.tex', '01.txt', 'lecture01.pdf')

        Returns:
            강의 번호 또는 None
        """
        # 다양한 패턴 시도
        patterns = [
            r'day[\-_]?(\d+)',      # day1, day-1, day_01
            r'lecture[\-_]?(\d+)',  # lecture1, lecture-01
            r'^(\d+)[\.\-_]',       # 01.txt, 1-1.tex
            r'[\-_](\d+)[\.\-_]',   # cs109-01.tex, fin-574-1-1.tex
        ]

        for pattern in patterns:
            match = re.search(pattern, filename.lower())
            if match:
                return int(match.group(1))

        return None

    def normalize_course_code(self, course: str) -> str:
        """
        과목 코드를 정규화합니다.

        Args:
            course: 원본 과목 코드 (예: 'csci103', 'CSCI103', 'cs109', 'fin-574')

        Returns:
            정규화된 과목 코드 (예: 'csci103', 'cs109', 'fin574')
        """
        # 소문자로 변환하고 하이픈 제거
        normalized = course.lower().replace('-', '')
        return normalized

    def get_new_tex_filename(self, course: str, lecture_num: int) -> str:
        """
        새로운 LaTeX 파일명 생성

        Args:
            course: 과목 코드
            lecture_num: 강의 번호

        Returns:
            파일명 (예: 'csci103_01.tex')
        """
        return f'{self.normalize_course_code(course)}_{lecture_num:02d}.tex'

    def scan_course_directory(self, university: str, course: str) -> Dict[int, Dict[str, List[Path]]]:
        """
        특정 과목 디렉토리를 스캔하여 파일들을 강의 번호별로 그룹화합니다.

        Args:
            university: 대학명
            course: 과목 코드

        Returns:
            {lecture_num: {'tex': [files], 'materials': [files], 'pdf': [files]}} 형태의 딕셔너리
        """
        course_path = self.paths.get_course_path(university, course)

        if not course_path.exists():
            return {}

        lectures = {}

        # 모든 파일 스캔
        for item in course_path.rglob('*'):
            if not item.is_file():
                continue

            lecture_num = self.parse_lecture_number(item.name)
            if lecture_num is None:
                continue

            if lecture_num not in lectures:
                lectures[lecture_num] = {
                    'tex': [],
                    'materials': [],
                    'pdf': []
                }

            # 파일 타입별 분류
            if item.suffix == '.tex':
                lectures[lecture_num]['tex'].append(item)
            elif item.suffix == '.pdf':
                lectures[lecture_num]['pdf'].append(item)
            elif item.suffix in ['.txt', '.md']:
                lectures[lecture_num]['materials'].append(item)
            else:
                lectures[lecture_num]['materials'].append(item)

        return lectures

    def plan_migration(self, university: str, course: str) -> List[Tuple[Path, Path, str]]:
        """
        마이그레이션 계획을 수립합니다.

        Args:
            university: 대학명
            course: 과목 코드

        Returns:
            [(source, dest, operation)] 튜플 리스트
            operation: 'move_tex', 'move_material', 'move_pdf', 'skip'
        """
        lectures = self.scan_course_directory(university, course)
        plan = []

        for lecture_num, files in sorted(lectures.items()):
            # 새 디렉토리 경로
            lecture_dir = self.paths.get_lecture_path(university, course, lecture_num)
            materials_dir = lecture_dir / 'materials'

            # LaTeX 파일 처리
            if files['tex']:
                # 첫 번째 .tex 파일을 메인으로 사용
                source_tex = files['tex'][0]
                new_tex_name = self.get_new_tex_filename(course, lecture_num)
                dest_tex = lecture_dir / new_tex_name

                # 이미 올바른 위치에 있는지 확인
                if source_tex != dest_tex:
                    plan.append((source_tex, dest_tex, 'move_tex'))

                # 추가 .tex 파일들 (있다면)
                for extra_tex in files['tex'][1:]:
                    if extra_tex != dest_tex:
                        dest_extra = lecture_dir / extra_tex.name
                        plan.append((extra_tex, dest_extra, 'move_tex'))

            # 자료 파일 처리
            for material in files['materials']:
                # 이미 materials/ 폴더에 있는지 확인
                if 'materials' not in material.parts:
                    dest_material = materials_dir / material.name
                    if material != dest_material:
                        plan.append((material, dest_material, 'move_material'))

            # PDF 파일 처리 (원본 슬라이드 등)
            for pdf in files['pdf']:
                # .tex와 같은 이름의 PDF는 건너뛰기 (컴파일된 결과물)
                tex_names = [t.stem for t in files['tex']]
                if pdf.stem in tex_names or self.normalize_course_code(course) in pdf.stem.lower():
                    continue

                # materials로 이동
                if 'materials' not in pdf.parts:
                    dest_pdf = materials_dir / pdf.name
                    if pdf != dest_pdf:
                        plan.append((pdf, dest_pdf, 'move_material'))

        return plan

    def execute_migration(self, plan: List[Tuple[Path, Path, str]]):
        """
        마이그레이션 계획을 실행합니다.

        Args:
            plan: [(source, dest, operation)] 튜플 리스트
        """
        for source, dest, operation in plan:
            # 대상 디렉토리 생성
            dest.parent.mkdir(parents=True, exist_ok=True)

            if self.dry_run:
                print(f"[DRY RUN] {operation}: {source} → {dest}")
            else:
                try:
                    # 파일 이동
                    shutil.move(str(source), str(dest))
                    print(f"✓ {operation}: {source.name} → {dest.relative_to(self.paths.root)}")
                except Exception as e:
                    print(f"✗ 실패: {source} → {dest}: {e}")

    def cleanup_empty_dirs(self, course_path: Path):
        """
        빈 디렉토리를 정리합니다.

        Args:
            course_path: 정리할 과목 디렉토리
        """
        if self.dry_run:
            print(f"[DRY RUN] 빈 디렉토리 정리: {course_path}")
            return

        # 하위 디렉토리부터 정리 (재귀적)
        for item in sorted(course_path.rglob('*'), reverse=True):
            if item.is_dir() and not any(item.iterdir()):
                try:
                    item.rmdir()
                    print(f"🗑️  빈 디렉토리 삭제: {item.relative_to(self.paths.root)}")
                except Exception as e:
                    print(f"⚠️  디렉토리 삭제 실패: {item}: {e}")

    def migrate_course(self, university: str, course: str):
        """
        특정 과목의 파일들을 마이그레이션합니다.

        Args:
            university: 대학명
            course: 과목 코드
        """
        print(f"\n{'='*70}")
        print(f"📚 마이그레이션: {university}/{course}")
        print(f"{'='*70}")

        # 마이그레이션 계획 수립
        plan = self.plan_migration(university, course)

        if not plan:
            print("⚠️  마이그레이션할 파일이 없습니다.")
            return

        print(f"\n계획된 작업: {len(plan)}개")
        print_separator(width=70)

        # 마이그레이션 실행
        self.execute_migration(plan)

        # 빈 디렉토리 정리
        print_separator(width=70)
        course_path = self.paths.get_course_path(university, course)
        self.cleanup_empty_dirs(course_path)

        print(f"\n✅ 마이그레이션 완료: {university}/{course}")


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(
        description='기존 파일들을 새로운 디렉토리 구조로 재배치합니다.'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='실제로 파일을 이동하지 않고 시뮬레이션만 수행'
    )
    parser.add_argument(
        '--university',
        type=str,
        help='특정 대학만 마이그레이션 (예: harvard, uiuc)'
    )
    parser.add_argument(
        '--course',
        type=str,
        help='특정 과목만 마이그레이션 (예: csci103, fin574)'
    )

    args = parser.parse_args()

    print_header("🔄 Academic Notes - File Migration", width=70)

    if args.dry_run:
        print("\n⚠️  DRY RUN 모드: 실제로 파일을 이동하지 않습니다.\n")

    migrator = FileMigrator(dry_run=args.dry_run)
    paths = migrator.paths

    # 마이그레이션할 과목 목록 구성
    courses_to_migrate = []

    if args.university and args.course:
        # 특정 과목만
        courses_to_migrate.append((args.university, args.course))
    else:
        # 모든 과목 스캔
        for univ_dir in paths.school.iterdir():
            if not univ_dir.is_dir():
                continue

            university = univ_dir.name

            if args.university and university != args.university:
                continue

            for course_dir in univ_dir.iterdir():
                if not course_dir.is_dir():
                    continue

                course = course_dir.name

                if args.course and course != args.course:
                    continue

                courses_to_migrate.append((university, course))

    if not courses_to_migrate:
        print("⚠️  마이그레이션할 과목을 찾을 수 없습니다.")
        return 1

    print(f"마이그레이션 대상: {len(courses_to_migrate)}개 과목")
    for university, course in courses_to_migrate:
        print(f"  - {university}/{course}")

    print_separator(width=70)

    # 각 과목 마이그레이션
    for university, course in courses_to_migrate:
        migrator.migrate_course(university, course)

    print_separator(width=70)
    print(f"\n✅ 전체 마이그레이션 완료!")

    if args.dry_run:
        print("\n💡 실제로 파일을 이동하려면 --dry-run 옵션 없이 다시 실행하세요.")

    return 0


if __name__ == '__main__':
    sys.exit(main())
