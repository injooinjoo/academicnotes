# MIT 강의노트 PDF

4개 MIT 강의 노트를 정리된 PDF로 제공합니다.

## 📚 강의 목록

| 강의 코드 | 강의명 | PDF | 페이지 | 크기 |
|----------|--------|-----|--------|------|
| **MIT 6.431** | Introduction to Probability | [6.431.pdf](6.431.pdf) | 50 | 375KB |
| **MIT 6.419** | High-Dimensional Data Analysis | [6.419.pdf](6.419.pdf) | 40+ | 409KB |
| **MIT 6.86** | Machine Learning | [6.86.pdf](6.86.pdf) | 45+ | 398KB |
| **MIT 18.6501** | Fundamentals of Statistics | [18.6501.pdf](18.6501.pdf) | 42+ | 428KB |

## 📁 파일 구조

```
school/mit/
├── 6.431.pdf          # 확률론 PDF
├── 6.431.tex          # LaTeX 소스
├── 6.419.pdf          # 고차원 데이터 분석 PDF
├── 6.419.tex          # LaTeX 소스
├── 6.86.pdf           # 머신러닝 PDF
├── 6.86.tex           # LaTeX 소스
├── 18.6501.pdf        # 통계학 PDF
├── 18.6501.tex        # LaTeX 소스
├── original_files/    # 원본 파일 백업
└── README.md          # 이 파일
```

## 🎯 주요 특징

- ✅ **A4 최적화**: 인쇄 및 화면 보기에 적합한 여백 (25mm)
- ✅ **한글 지원**: 완벽한 한글 렌더링
- ✅ **수식 가독성**: amsmath 환경으로 명확한 수식 표현
- ✅ **깔끔한 디자인**: 색상 박스, 체계적인 섹션 구조
- ✅ **자동 목차**: 전체 구조 한눈에 파악

## 🔄 PDF 재생성

LaTeX 소스를 수정한 후 PDF를 재생성하려면:

```bash
xelatex 6.431.tex
xelatex 6.431.tex  # 두 번째 패스 (목차용)
```

## 📝 구조 변경사항

원본 파일은 여러 개의 독립 문서가 합쳐진 형태였으나, 정리 과정에서:
- 중복된 preamble 제거
- 단일 통합 문서로 재구성
- 목차 자동 생성
- 모듈/유닛 번호 일관성 유지

## 💾 원본 파일

원본 파일은 `original_files/` 디렉토리에 백업되어 있습니다.
