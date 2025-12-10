#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LaTeX 파일 폰트 크기 분석 스크립트
모든 TEX 파일에서 폰트 축소 명령어를 검색하고 가독성 위험도를 평가합니다.
"""

import re
from pathlib import Path
from collections import defaultdict

def analyze_tex_file(filepath):
    """TEX 파일을 분석하여 폰트 관련 이슈를 찾습니다."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    issues = {
        'adjustbox': [],
        'resizebox': [],
        'scalebox': [],
        'tiny': [],
        'scriptsize': [],
        'footnotesize': [],
        'small': [],
        'tabularx_width': [],
        'landscape': []
    }

    # 줄 번호별로 검색
    lines = content.split('\n')
    for line_num, line in enumerate(lines, 1):
        # adjustbox 사용
        if r'\adjustbox' in line and 'max width' in line:
            issues['adjustbox'].append((line_num, line.strip()))

        # resizebox 사용
        if r'\resizebox' in line:
            issues['resizebox'].append((line_num, line.strip()))

        # scalebox 사용
        if r'\scalebox' in line:
            issues['scalebox'].append((line_num, line.strip()))

        # tiny 사용
        if r'\tiny' in line:
            issues['tiny'].append((line_num, line.strip()))

        # scriptsize 사용
        if r'\scriptsize' in line:
            issues['scriptsize'].append((line_num, line.strip()))

        # footnotesize 사용
        if r'\footnotesize' in line:
            issues['footnotesize'].append((line_num, line.strip()))

        # small 사용 (단, lstset 내부는 제외)
        if r'\small' in line and 'basicstyle' not in line:
            issues['small'].append((line_num, line.strip()))

        # tabularx width 지정
        if r'\begin{tabularx}' in line:
            issues['tabularx_width'].append((line_num, line.strip()))

        # landscape 사용
        if r'\begin{landscape}' in line:
            issues['landscape'].append((line_num, line.strip()))

    return issues

def calculate_risk_score(issues):
    """위험도 점수를 계산합니다."""
    score = 0

    # adjustbox는 가장 심각 (각 10점)
    score += len(issues['adjustbox']) * 10

    # resizebox, scalebox (각 8점)
    score += len(issues['resizebox']) * 8
    score += len(issues['scalebox']) * 8

    # tiny, scriptsize (각 5점)
    score += len(issues['tiny']) * 5
    score += len(issues['scriptsize']) * 5

    # footnotesize (각 2점)
    score += len(issues['footnotesize']) * 2

    # small (각 1점)
    score += len(issues['small']) * 1

    # landscape는 위험 아님 (오히려 좋은 대안)
    # tabularx는 카운트만

    return score

def get_risk_level(score):
    """점수를 기반으로 위험도 레벨을 반환합니다."""
    if score >= 20:
        return "HIGH"
    elif score >= 10:
        return "MEDIUM"
    elif score >= 5:
        return "LOW"
    else:
        return "MINIMAL"

def main():
    """메인 실행 함수"""
    base_path = Path("school")

    if not base_path.exists():
        print(f"Error: {base_path} directory not found")
        return

    # 모든 TEX 파일 찾기
    tex_files = sorted(base_path.glob("**/*.tex"))

    print("=" * 80)
    print("📊 LaTeX 파일 폰트 크기 분석 리포트")
    print("=" * 80)
    print(f"\n총 {len(tex_files)}개 파일 분석 중...\n")

    results = []

    for tex_file in tex_files:
        issues = analyze_tex_file(tex_file)
        score = calculate_risk_score(issues)
        risk_level = get_risk_level(score)

        results.append({
            'file': tex_file,
            'issues': issues,
            'score': score,
            'risk_level': risk_level
        })

    # 위험도 순으로 정렬
    results.sort(key=lambda x: x['score'], reverse=True)

    # 통계 계산
    stats = defaultdict(int)
    for result in results:
        stats[result['risk_level']] += 1

    # 통계 출력
    print("=" * 80)
    print("📈 위험도 통계")
    print("=" * 80)
    print(f"HIGH 위험도:    {stats['HIGH']:2d}개")
    print(f"MEDIUM 위험도:  {stats['MEDIUM']:2d}개")
    print(f"LOW 위험도:     {stats['LOW']:2d}개")
    print(f"MINIMAL 위험도: {stats['MINIMAL']:2d}개")
    print()

    # HIGH 위험도 파일 상세 출력
    if stats['HIGH'] > 0:
        print("=" * 80)
        print("🚨 HIGH 위험도 파일 (우선 수정 필요)")
        print("=" * 80)

        for result in results:
            if result['risk_level'] == 'HIGH':
                print(f"\n📄 {result['file']}")
                print(f"   위험도 점수: {result['score']}")

                issues = result['issues']

                if issues['adjustbox']:
                    print(f"   ⚠️  adjustbox 사용: {len(issues['adjustbox'])}회")
                    for line_num, line in issues['adjustbox'][:3]:  # 처음 3개만
                        print(f"      Line {line_num}: {line[:70]}...")

                if issues['resizebox']:
                    print(f"   ⚠️  resizebox 사용: {len(issues['resizebox'])}회")

                if issues['scalebox']:
                    print(f"   ⚠️  scalebox 사용: {len(issues['scalebox'])}회")

                if issues['tiny']:
                    print(f"   ⚠️  tiny 사용: {len(issues['tiny'])}회")

                if issues['scriptsize']:
                    print(f"   ⚠️  scriptsize 사용: {len(issues['scriptsize'])}회")

                if issues['small']:
                    print(f"   ℹ️  small 사용: {len(issues['small'])}회")

                if issues['tabularx_width']:
                    print(f"   ℹ️  tabularx 테이블: {len(issues['tabularx_width'])}개")

    # MEDIUM 위험도 파일 요약 출력
    if stats['MEDIUM'] > 0:
        print("\n" + "=" * 80)
        print("⚠️  MEDIUM 위험도 파일")
        print("=" * 80)

        for result in results:
            if result['risk_level'] == 'MEDIUM':
                issues = result['issues']
                issue_summary = []

                if issues['adjustbox']:
                    issue_summary.append(f"adjustbox×{len(issues['adjustbox'])}")
                if issues['tiny']:
                    issue_summary.append(f"tiny×{len(issues['tiny'])}")
                if issues['scriptsize']:
                    issue_summary.append(f"scriptsize×{len(issues['scriptsize'])}")
                if issues['footnotesize']:
                    issue_summary.append(f"footnotesize×{len(issues['footnotesize'])}")
                if issues['small']:
                    issue_summary.append(f"small×{len(issues['small'])}")

                print(f"   {result['file']} (점수: {result['score']})")
                print(f"      {', '.join(issue_summary)}")

    # LOW 위험도 파일 목록만
    if stats['LOW'] > 0:
        print("\n" + "=" * 80)
        print("ℹ️  LOW 위험도 파일")
        print("=" * 80)

        for result in results:
            if result['risk_level'] == 'LOW':
                print(f"   {result['file']} (점수: {result['score']})")

    # 전체 이슈 통계
    print("\n" + "=" * 80)
    print("📊 전체 이슈 통계")
    print("=" * 80)

    total_issues = defaultdict(int)
    for result in results:
        for issue_type, occurrences in result['issues'].items():
            total_issues[issue_type] += len(occurrences)

    print(f"adjustbox:     {total_issues['adjustbox']:3d}회")
    print(f"resizebox:     {total_issues['resizebox']:3d}회")
    print(f"scalebox:      {total_issues['scalebox']:3d}회")
    print(f"tiny:          {total_issues['tiny']:3d}회")
    print(f"scriptsize:    {total_issues['scriptsize']:3d}회")
    print(f"footnotesize:  {total_issues['footnotesize']:3d}회")
    print(f"small:         {total_issues['small']:3d}회")
    print(f"tabularx:      {total_issues['tabularx_width']:3d}개")
    print(f"landscape:     {total_issues['landscape']:3d}개")

    # 파일로 저장
    report_path = Path("font_analysis_report.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("LaTeX 파일 폰트 크기 분석 리포트\n")
        f.write("=" * 80 + "\n\n")

        for result in results:
            f.write(f"\n파일: {result['file']}\n")
            f.write(f"위험도: {result['risk_level']} (점수: {result['score']})\n")

            issues = result['issues']
            if any(len(v) > 0 for v in issues.values()):
                f.write("이슈:\n")
                for issue_type, occurrences in issues.items():
                    if occurrences:
                        f.write(f"  - {issue_type}: {len(occurrences)}회\n")
                        for line_num, line in occurrences[:5]:  # 처음 5개만
                            f.write(f"      Line {line_num}: {line[:100]}\n")
            f.write("\n" + "-" * 80 + "\n")

    print(f"\n✅ 상세 리포트가 {report_path}에 저장되었습니다.")
    print("=" * 80)

if __name__ == "__main__":
    import sys
    import io
    # Windows console encoding fix
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    main()
