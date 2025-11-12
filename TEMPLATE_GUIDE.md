# 📘 Harvard Academic Notes - 통합 템플릿 가이드

## 🎉 작업 완료 요약

**30개의 Harvard 강의 노트가 통일된 템플릿으로 성공적으로 변환되었습니다!**

### ✅ 완료된 작업
- ✅ 마스터 템플릿 생성 ([templates/master_template.tex](templates/master_template.tex))
- ✅ 30개 LaTeX 파일 자동 변환 (100% 성공)
- ✅ 메타정보 블록 자동 삽입
- ✅ 원문 내용 100% 보존
- ✅ 스타일 일관성 확보

---

## 📂 프로젝트 구조

```
academicnotes/
├── templates/
│   └── master_template.tex          # 통합 마스터 템플릿
│
├── school/harvard/                   # 변환된 강의 노트
│   ├── cs109/                        # 데이터 과학 입문 (14개)
│   │   ├── lecture_01/1.tex
│   │   ├── lecture_02/2.tex
│   │   └── ...
│   ├── csci103/                      # 재현 가능한 머신러닝 (8개)
│   │   ├── lecture_01/1.tex
│   │   └── ...
│   └── csci89/                       # 자연어 처리 입문 (8개)
│       ├── lecture_01/csci89_01.tex
│       └── ...
│
├── src/
│   ├── convert_latex.py              # 변환 스크립트
│   └── compile_latex.py              # PDF 컴파일 스크립트
│
├── output/                           # 생성된 PDF 저장 위치
│
├── CONVERSION_SUMMARY.md             # 상세 변환 보고서
└── TEMPLATE_GUIDE.md                 # 이 파일
```

---

## 🎨 템플릿 특징

### 통일된 디자인 요소

#### 1. 페이지 레이아웃
- **용지**: A4 (210mm × 297mm)
- **여백**: 25mm (상하좌우)
- **줄간격**: 1.5배 (onehalfspacing)
- **단락 간격**: 0.6em
- **들여쓰기**: 없음

#### 2. 색상 팔레트 (파스텔 톤)
| 색상 | RGB | 용도 |
|-----|-----|------|
| lightblue | (220, 235, 255) | 요약 박스 |
| lightgreen | (220, 255, 235) | 핵심 정보 박스 |
| lightyellow | (255, 250, 220) | 주의사항 박스 |
| lightpurple | (240, 230, 255) | 개요 박스 |
| lightgray | (242, 242, 242) | 예제 박스, 코드 배경 |
| lightpink | (255, 235, 245) | 정의 박스 |

#### 3. 박스 환경 (8가지)

**예제 코드:**

```latex
% 1. 개요 박스
\begin{overviewbox}
강의 전체 개요 내용
\end{overviewbox}

% 2. 요약 박스
\begin{summarybox}
핵심 내용 요약
\end{summarybox}

% 3. 핵심 정보 박스
\begin{infobox}
중요한 정보나 개념
\end{infobox}

% 4. 주의사항 박스
\begin{warningbox}
주의할 사항
\end{warningbox}

% 5. 예제 박스
\begin{examplebox}{예제 제목}
구체적인 예시
\end{examplebox}

% 6. 정의 박스
\begin{definitionbox}{용어명}
용어의 정의
\end{definitionbox}

% 7. 중요 박스
\begin{importantbox}{중요 사항}
매우 중요한 내용
\end{importantbox}

% 8. Caution 박스 (warningbox와 동일)
\begin{cautionbox}
주의사항
\end{cautionbox}
```

#### 4. 코드 블록 스타일

```latex
% Python 코드
\begin{lstlisting}[language=Python]
def hello_world():
    print("Hello, World!")
\end{lstlisting}

% SQL 코드
\begin{lstlisting}[style=sqlstyle]
SELECT * FROM users WHERE age > 18;
\end{lstlisting}
```

**특징:**
- 배경색: lightgray
- 행 번호: 왼쪽 표시
- Syntax highlighting: 키워드(파랑), 주석(초록), 문자열(보라)
- 자동 줄바꿈 지원

#### 5. 표 스타일 (booktabs)

```latex
\begin{table}[h!]
\centering
\caption{표 제목}
\label{tab:example}
\begin{tabular}{@{}lcc@{}}
\toprule
\textbf{항목} & \textbf{값1} & \textbf{값2} \\
\midrule
데이터1 & 100 & 200 \\
데이터2 & 150 & 250 \\
\bottomrule
\end{tabular}
\end{table}
```

---

## 🔧 사용 방법

### 1. PDF 컴파일

#### 개별 파일 컴파일
```bash
# 특정 강의 노트 1개만 컴파일
cd school/harvard/csci103/lecture_08
xelatex 8.tex
xelatex 8.tex  # 목차 업데이트를 위해 2회 실행

# 또는 스크립트 사용
python src/compile_latex.py school/harvard/csci103/lecture_08/8.tex
```

#### 전체 파일 일괄 컴파일
```bash
# Harvard 폴더 내 모든 .tex 파일 컴파일
python src/compile_latex.py school/harvard -r

# 특정 과정만 컴파일
python src/compile_latex.py school/harvard/cs109 -r
python src/compile_latex.py school/harvard/csci103 -r
python src/compile_latex.py school/harvard/csci89 -r
```

### 2. 새 문서 추가

새로운 강의 노트를 추가할 때:

```bash
# 1. 새 .tex 파일 생성
# 2. 템플릿 적용
python src/convert_latex.py

# 또는 수동으로 templates/master_template.tex를 복사하여 시작
```

---

## 📐 메타정보 블록

모든 문서에는 다음과 같은 메타정보 블록이 자동으로 추가되었습니다:

```latex
\metainfo{과정명}{주차}{교수명}{학습 목적}
```

**출력 예시:**
```
▣ 강의명: CSCI E-103: 재현 가능한 머신러닝
▣ 주차: Lecture 08
▣ 교수명: Anindita Mahapatra & Eric Gieseke
▣ 목적: Lecture 08의 핵심 개념 학습
```

---

## 📊 과정별 정보

### CS109A: 데이터 과학 입문
- **파일 수**: 14개
- **교수**: Pavlos Protopapas, Kevin Rader, Chris Gumb
- **경로**: `school/harvard/cs109/`

### CSCI E-103: 재현 가능한 머신러닝
- **파일 수**: 8개
- **교수**: Anindita Mahapatra & Eric Gieseke
- **경로**: `school/harvard/csci103/`

### CSCI E-89B: 자연어 처리 입문
- **파일 수**: 8개
- **교수**: Dmitry Kurochkin
- **경로**: `school/harvard/csci89/`

---

## 🛠️ 커스터마이징

### 색상 변경

템플릿의 색상을 변경하려면 `templates/master_template.tex`에서 색상 정의 부분을 수정:

```latex
% 밝은 배경용 파스텔 색상
\definecolor{lightblue}{RGB}{220, 235, 255}      % 여기를 수정
\definecolor{lightgreen}{RGB}{220, 255, 235}     % 여기를 수정
...
```

### 박스 스타일 변경

박스 환경의 스타일을 변경하려면:

```latex
\newtcolorbox{summarybox}[1][]{
    enhanced,
    colback=lightblue,        % 배경색
    colframe=darkblue,        % 테두리색
    fonttitle=\bfseries,      % 제목 폰트
    title=📝 핵심 요약,       % 제목
    arc=2mm,                  % 모서리 곡률
    boxrule=0.7pt,            % 테두리 두께
    ...
}
```

### 헤더/푸터 변경

각 문서의 헤더는 자동으로 과정명과 강의 번호로 설정됩니다.
수동으로 변경하려면 각 .tex 파일에서:

```latex
\fancyhead[L]{\small\textit{원하는 왼쪽 헤더}}
\fancyhead[R]{\small\textit{원하는 오른쪽 헤더}}
```

---

## ⚡ 빠른 시작 가이드

### 1. PDF 생성 (개별 파일)
```bash
cd school/harvard/csci103/lecture_08
xelatex 8.tex && xelatex 8.tex
```

### 2. PDF 생성 (전체 과정)
```bash
python src/compile_latex.py school/harvard/cs109 -r
```

### 3. 변환 스크립트 재실행
```bash
python src/convert_latex.py
```

---

## 📚 참고 자료

### LaTeX 관련
- [LaTeX 튜토리얼](https://www.overleaf.com/learn)
- [tcolorbox 매뉴얼](https://www.ctan.org/pkg/tcolorbox)
- [booktabs 매뉴얼](https://www.ctan.org/pkg/booktabs)
- [listings 매뉴얼](https://www.ctan.org/pkg/listings)

### TeX 배포판 설치
- **Windows**: [MiKTeX](https://miktex.org/)
- **macOS**: [MacTeX](https://www.tug.org/mactex/)
- **Linux**: [TeX Live](https://www.tug.org/texlive/)

---

## 🤝 기여 및 피드백

템플릿 개선 제안이나 버그 리포트는 이슈로 등록해주세요.

---

## 📝 변경 이력

### v2.0 (2025-10-26)
- ✅ 통합 마스터 템플릿 생성
- ✅ 30개 파일 자동 변환 완료
- ✅ 메타정보 블록 추가
- ✅ 8가지 박스 환경 통일
- ✅ 코드 블록 스타일 통일
- ✅ 헤더/푸터 자동 설정

---

**작성일**: 2025-10-26
**작성자**: Claude Code (Sonnet 4.5)
**문서 버전**: 2.0
