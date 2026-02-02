#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Academic Notes - Gemini API 2-Pass LaTeX 노트 자동 생성기

워크플로우:
  TXT → Lesson 단위 청킹 → (Pass 1: note_generation.txt) × N청크 → 병합
      → (Pass 2: latex_upgrade.txt) → final LaTeX
      → 저장 → xelatex 컴파일

사용법:
  python src/generate_notes_gemini.py --course all
  python src/generate_notes_gemini.py --course fin-571 --modules 5,6,7,8
  python src/generate_notes_gemini.py --course badm-572 --skip-compile
"""

import sys
import os
import re
import time
import argparse
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.utils import (
    ProjectPaths,
    find_xelatex_path,
    cleanup_aux_files,
    print_header,
    print_separator,
)
from src.fix_latex_errors import fix_latex_file

# .env 로드
load_dotenv(Path(__file__).parent.parent / '.env')

# ============================================================================
# 과목 설정
# ============================================================================

COURSES: Dict[str, Dict[str, Any]] = {
    "fin-571": {
        "name": "FIN-571: Financial Institutions & Monetary Policy",
        "short": "FIN571",
        "university": "uiuc",
        "modules": [
            {"num": 1, "pdf": "Banking and Financial Institutions Module 1 Transcript.pdf",
             "txt": "Banking and Financial Institutions Module 1 Transcript.txt",
             "output": "fin571_01", "title": "Banking and Financial Institutions Module 1"},
            {"num": 2, "pdf": "Banking and Financial Institutions Module 2 Transcript.pdf",
             "txt": "Banking and Financial Institutions Module 2 Transcript.txt",
             "output": "fin571_02", "title": "Banking and Financial Institutions Module 2"},
            {"num": 3, "pdf": "Banking and Financial Institutions Module 3 Transcript.pdf",
             "txt": "Banking and Financial Institutions Module 3 Transcript.txt",
             "output": "fin571_03", "title": "Banking and Financial Institutions Module 3"},
            {"num": 4, "pdf": "Banking and Financial Institutions Module 4 Transcript.pdf",
             "txt": "Banking and Financial Institutions Module 4 Transcript.txt",
             "output": "fin571_04", "title": "Banking and Financial Institutions Module 4"},
            {"num": 5, "pdf": "Central Banks and Monetary Policy Module 1 Transcript.pdf",
             "txt": "Central Banks and Monetary Policy Module 1 Transcript.txt",
             "output": "fin571_05", "title": "Central Banks and Monetary Policy Module 1"},
            {"num": 6, "pdf": "Central Banks and Monetary Policy Module 2 Transcript.pdf",
             "txt": "Central Banks and Monetary Policy Module 2 Transcript.txt",
             "output": "fin571_06", "title": "Central Banks and Monetary Policy Module 2"},
            {"num": 7, "pdf": "Central Banks and Monetary Policy Module 3 Transcript.pdf",
             "txt": "Central Banks and Monetary Policy Module 3 Transcript.txt",
             "output": "fin571_07", "title": "Central Banks and Monetary Policy Module 3"},
            {"num": 8, "pdf": "Central Banks and Monetary Policy Module 4 Transcript.pdf",
             "txt": "Central Banks and Monetary Policy Module 4 Transcript.txt",
             "output": "fin571_08", "title": "Central Banks and Monetary Policy Module 4"},
        ],
    },
    "badm-572": {
        "name": "BADM-572: Data-Driven Decision Making",
        "short": "BADM572",
        "university": "uiuc",
        "modules": [
            {"num": 1, "pdf": "Exploring and Producing Data for Business Decision Making Module 1.pdf",
             "txt": "Exploring and Producing Data for Business Decision Making Module 1.txt",
             "output": "badm572_01", "title": "Exploring and Producing Data Module 1"},
            {"num": 2, "pdf": "Exploring and Producing Data for Business Decision Making Module 2.pdf",
             "txt": "Exploring and Producing Data for Business Decision Making Module 2.txt",
             "output": "badm572_02", "title": "Exploring and Producing Data Module 2"},
            {"num": 3, "pdf": "Exploring and Producing Data for Business Decision Making Module 3.pdf",
             "txt": "Exploring and Producing Data for Business Decision Making Module 3.txt",
             "output": "badm572_03", "title": "Exploring and Producing Data Module 3"},
            {"num": 4, "pdf": "Exploring and Producing Data for Business Decision Making Module 4.pdf",
             "txt": "Exploring and Producing Data for Business Decision Making Module 4.txt",
             "output": "badm572_04", "title": "Exploring and Producing Data Module 4"},
            {"num": 5, "pdf": "Inferential and Predictive Statistics for Business Module 1.pdf",
             "txt": "Inferential and Predictive Statistics for Business Module 1.txt",
             "output": "badm572_05", "title": "Inferential and Predictive Statistics Module 1"},
            {"num": 6, "pdf": "Inferential and Predictive Statistics for Business Module 2.pdf",
             "txt": "Inferential and Predictive Statistics for Business Module 2.txt",
             "output": "badm572_06", "title": "Inferential and Predictive Statistics Module 2"},
            {"num": 7, "pdf": "Inferential and Predictive Statistics for Business Module 3.pdf",
             "txt": "Inferential and Predictive Statistics for Business Module 3.txt",
             "output": "badm572_07", "title": "Inferential and Predictive Statistics Module 3"},
            {"num": 8, "pdf": "Inferential and Predictive Statistics for Business Module 4.pdf",
             "txt": "Inferential and Predictive Statistics for Business Module 4.txt",
             "output": "badm572_08", "title": "Inferential and Predictive Statistics Module 4"},
        ],
    },
    "cs109": {
        "name": "CS109A: Introduction to Data Science",
        "short": "CS109A",
        "university": "harvard",
        "source_type": "materials",
        "modules": [
            {"num": i, "txt": "script.txt", "output": f"cs109_{i:02d}",
             "title": f"CS109A Lecture {i}"}
            for i in range(1, 26)
        ],
    },
    "csci103": {
        "name": "CSCI E-103: Introduction to the Intellectual Enterprises of CS",
        "short": "CSCI103",
        "university": "harvard",
        "source_type": "materials",
        "modules": [
            {"num": i, "txt": "script.txt", "output": f"csci103_{i:02d}",
             "title": f"CSCI103 Lecture {i}"}
            for i in range(1, 15)
        ],
    },
    "csci89": {
        "name": "CSCI E-89: Introduction to Artificial Intelligence",
        "short": "CSCI89",
        "university": "harvard",
        "source_type": "materials",
        "modules": [
            {"num": 1, "txt": ["1.txt", "1-section.txt"], "output": "csci89_01", "title": "CSCI89 Lecture 1"},
            {"num": 2, "txt": ["2.txt", "2-section.txt"], "output": "csci89_02", "title": "CSCI89 Lecture 2"},
            {"num": 3, "txt": ["3.txt", "3-section.txt"], "output": "csci89_03", "title": "CSCI89 Lecture 3"},
            {"num": 4, "txt": ["4.txt", "4-section.txt"], "output": "csci89_04", "title": "CSCI89 Lecture 4"},
            {"num": 5, "txt": ["5.txt", "5-section.txt"], "output": "csci89_05", "title": "CSCI89 Lecture 5"},
            {"num": 6, "txt": "6.txt", "output": "csci89_06", "title": "CSCI89 Lecture 6"},
            {"num": 7, "txt": ["script.txt", "section.txt"], "output": "csci89_07", "title": "CSCI89 Lecture 7"},
            {"num": 8, "txt": ["script.txt", "section.txt"], "output": "csci89_08", "title": "CSCI89 Lecture 8"},
            {"num": 9, "txt": ["script.txt", "section.txt"], "output": "csci89_09", "title": "CSCI89 Lecture 9"},
            {"num": 10, "txt": ["script.txt", "section.txt"], "output": "csci89_10", "title": "CSCI89 Lecture 10"},
            {"num": 11, "txt": "script.txt", "output": "csci89_11", "title": "CSCI89 Lecture 11"},
            {"num": 12, "txt": "script.txt", "output": "csci89_12", "title": "CSCI89 Lecture 12"},
        ],
    },
}

# 처리 순서 (작은 파일부터)
PROCESSING_ORDER = {
    "fin-571": [5, 6, 7, 8, 1, 2, 4, 3],   # Central Banks 먼저, Banking M3 마지막
    "badm-572": [5, 6, 7, 8, 1, 2, 3, 4],   # Inferential 먼저, Exploring 나중
}

# 청크 크기 설정
DEFAULT_CHUNK_MAX_CHARS = 60000   # 청크당 최대 문자수
DEFAULT_CHUNK_MIN_CHARS = 5000    # 청크당 최소 문자수 (이보다 작으면 이전 청크에 합침)


# ============================================================================
# Gemini API 클래스
# ============================================================================

class GeminiNoteGenerator:
    """Gemini API를 사용한 2-pass LaTeX 노트 생성기 (TXT + 청킹 지원)"""

    def __init__(self, model_name: str = "gemini-2.5-flash",
                 chunk_max_chars: int = DEFAULT_CHUNK_MAX_CHARS):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your-api-key-here":
            raise ValueError(
                "GEMINI_API_KEY가 설정되지 않았습니다.\n"
                ".env 파일에 GEMINI_API_KEY=your-actual-key 를 설정하세요."
            )

        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.paths = ProjectPaths()
        self.chunk_max_chars = chunk_max_chars

        # 프롬프트 로드
        self.note_generation_prompt = self._load_prompt("note_generation.txt")
        self.latex_upgrade_prompt = self._load_prompt("latex_upgrade.txt")
        self.master_template = self._load_template()

    def _load_prompt(self, filename: str) -> str:
        prompt_path = self.paths.prompts / filename
        if not prompt_path.exists():
            raise FileNotFoundError(f"프롬프트 파일 없음: {prompt_path}")
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _load_template(self) -> str:
        template_path = self.paths.root / "templates" / "master_template.tex"
        if not template_path.exists():
            raise FileNotFoundError(f"템플릿 파일 없음: {template_path}")
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()

    # ------------------------------------------------------------------
    # 텍스트 분할 (Lesson 단위 청킹)
    # ------------------------------------------------------------------

    def _extract_toc(self, text: str) -> str:
        """텍스트 앞부분에서 목차(Table of Contents) 추출"""
        # TOC는 보통 첫 1000자 이내에 있음
        head = text[:3000]
        # "Table of Contents" ~ 첫 Lesson 시작 전까지
        toc_match = re.search(
            r'(Table of Contents.*?)(?=\nLesson|\n\d+\n)',
            head, re.DOTALL | re.IGNORECASE
        )
        if toc_match:
            return toc_match.group(1).strip()
        # 못 찾으면 빈 문자열
        return ""

    def _split_by_lessons(self, text: str) -> List[Dict[str, Any]]:
        """
        Lesson 단위로 텍스트를 분할하고, chunk_max_chars에 맞게 그룹핑.

        Returns:
            [{"lessons": ["Lesson 1-1", "Lesson 1-2"], "text": "..."}, ...]
        """
        # Lesson 경계 패턴: "Lesson X-X" 또는 "Lesson X-X.X"
        lesson_pattern = re.compile(
            r'^(Lesson\s+\d+-\d+(?:\.\d+)?(?:\s*[.:]\s*.+)?)\s*$',
            re.MULTILINE
        )

        # 모든 Lesson 위치 찾기
        matches = list(lesson_pattern.finditer(text))

        if not matches:
            # Lesson 패턴이 없으면 전체를 하나의 청크로
            return [{"lessons": ["전체"], "text": text}]

        # Lesson별 텍스트 추출
        lesson_segments = []
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            lesson_name = match.group(1).strip()
            segment_text = text[start:end]
            lesson_segments.append({
                "name": lesson_name,
                "text": segment_text,
                "char_count": len(segment_text),
            })

        # TOC 앞부분 (첫 Lesson 이전 텍스트)
        preamble_text = text[:matches[0].start()].strip()

        # Lesson들을 chunk_max_chars에 맞게 그룹핑
        chunks = []
        current_lessons = []
        current_text_parts = []
        current_size = 0

        for seg in lesson_segments:
            # 현재 청크에 추가했을 때 초과하면 새 청크 시작
            if current_size + seg["char_count"] > self.chunk_max_chars and current_size > 0:
                chunks.append({
                    "lessons": current_lessons[:],
                    "text": "\n\n".join(current_text_parts),
                })
                current_lessons = []
                current_text_parts = []
                current_size = 0

            current_lessons.append(seg["name"])
            current_text_parts.append(seg["text"])
            current_size += seg["char_count"]

        # 마지막 청크
        if current_text_parts:
            # 마지막 청크가 너무 작으면 이전 청크에 합침
            if current_size < DEFAULT_CHUNK_MIN_CHARS and chunks:
                chunks[-1]["lessons"].extend(current_lessons)
                chunks[-1]["text"] += "\n\n" + "\n\n".join(current_text_parts)
            else:
                chunks.append({
                    "lessons": current_lessons[:],
                    "text": "\n\n".join(current_text_parts),
                })

        # preamble(목차, 서문)을 첫 번째 청크 앞에 붙이기
        if preamble_text and chunks:
            chunks[0]["text"] = preamble_text + "\n\n" + chunks[0]["text"]

        return chunks

    # ------------------------------------------------------------------
    # Gemini API 호출
    # ------------------------------------------------------------------

    def _call_gemini(self, prompt: str, content_parts: list, pass_name: str) -> str:
        """Gemini API 호출 (재시도 포함)"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"  🤖 {pass_name} API 호출 중... (시도 {attempt + 1}/{max_retries})")

                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=[
                        types.Content(
                            role="user",
                            parts=content_parts + [types.Part.from_text(text=prompt)]
                        )
                    ],
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        max_output_tokens=65536,
                    ),
                )

                result = response.text
                if result:
                    print(f"  ✅ {pass_name} 완료 ({len(result):,}자)")
                    return result
                else:
                    print(f"  ⚠️  {pass_name} 빈 응답")

            except Exception as e:
                print(f"  ❌ {pass_name} 에러: {e}")
                if attempt < max_retries - 1:
                    wait = 30 * (attempt + 1)
                    print(f"  ⏳ {wait}초 후 재시도...")
                    time.sleep(wait)
                else:
                    raise

        raise RuntimeError(f"{pass_name} 실패: {max_retries}회 시도 모두 실패")

    # ------------------------------------------------------------------
    # 프롬프트 빌더
    # ------------------------------------------------------------------

    def _build_pass1_prompt(self, course_name: str, module_title: str,
                            chunk_info: str = "") -> str:
        """Pass 1 프롬프트 구성 (note_generation.txt 기반)"""
        prompt = self.note_generation_prompt
        prompt = prompt.replace("⟪과목명 / 주차 / 강사⟫",
                                f"{course_name} / {module_title} / UIUC Faculty")
        prompt = prompt.replace("⟪시험 대비 / 레포트 / 프로젝트 정리⟫", "시험 대비")
        prompt = prompt.replace("⟪제목⟫", module_title)
        prompt = prompt.replace("⟪이름⟫", "UIUC Student")
        prompt = prompt.replace("⟪과목⟫", course_name)

        # 추가 지시: 내용 누락 방지 강조
        prompt += "\n\n" + "=" * 60 + "\n"
        prompt += "⚠️ 매우 중요한 추가 지시사항:\n"
        prompt += "- 제공된 텍스트의 모든 내용을 빠짐없이 포함하세요. 요약하거나 축약하지 마세요.\n"
        prompt += "- 모든 개념, 정의, 공식, 예시, 절차를 완전히 포함해야 합니다.\n"
        prompt += "- 내용이 길어지더라도 괜찮습니다. 누락보다 중복이 낫습니다.\n"
        prompt += "- 슬라이드/강의의 모든 텍스트, 도표 내용, 주석을 반영하세요.\n"

        if chunk_info:
            prompt += f"\n{chunk_info}\n"

        prompt += "=" * 60 + "\n"

        return prompt

    def _build_pass1_chunk_prompt(self, course_name: str, module_title: str,
                                   toc: str, chunk_idx: int, total_chunks: int,
                                   lesson_names: List[str]) -> str:
        """청크별 Pass 1 프롬프트 (전체 구조 컨텍스트 포함)"""
        lessons_str = ', '.join(lesson_names)
        toc_section = "전체 목차:\n" + toc if toc else ""
        begin_doc = "\\begin{document}"
        end_doc = "\\end{document}"
        chunk_info = (
            f"\n"
            f"📌 이 텍스트는 \"{module_title}\" 전체 중 파트 {chunk_idx + 1}/{total_chunks}입니다.\n"
            f"포함된 Lesson: {lessons_str}\n"
            f"\n"
            f"{toc_section}\n"
            f"\n"
            f"⚠️ 이 파트에 해당하는 내용만 LaTeX 노트로 변환하세요.\n"
            f"- {begin_doc} ~ {end_doc} 형태의 완전한 LaTeX 문서를 출력하세요.\n"
            f"- \\documentclass, \\usepackage 등 프리앰블도 포함하세요 (나중에 병합됩니다).\n"
            f"- 이 파트의 모든 Lesson 내용을 빠짐없이 포함하세요.\n"
        )
        return self._build_pass1_prompt(course_name, module_title, chunk_info)

    def _build_pass2_prompt(self, raw_latex: str) -> str:
        """Pass 2 프롬프트 구성 (latex_upgrade.txt + master_template.tex 기반)"""
        prompt = self.latex_upgrade_prompt
        prompt += "\n\n" + "=" * 60 + "\n"
        prompt += "## 마스터 템플릿 (이 프리앰블을 기준으로 검증하세요):\n"
        prompt += "```latex\n"
        prompt += self.master_template
        prompt += "\n```\n\n"
        prompt += "## 검증 및 수정 대상 LaTeX 소스:\n"
        prompt += "```latex\n"
        prompt += raw_latex
        prompt += "\n```\n\n"
        prompt += "위 LaTeX 소스를 마스터 템플릿 기준으로 검증하고 수정한 전체 LaTeX 소스를 출력하세요.\n"
        prompt += "수정된 전체 LaTeX 소스만 출력하세요. 설명이나 코멘트는 불필요합니다.\n"
        prompt += "내용을 절대 축약하거나 생략하지 마세요. 원본의 모든 내용을 유지하세요.\n"
        return prompt

    def _build_pass2_section_prompt(self, section_latex: str,
                                     section_idx: int, total_sections: int) -> str:
        """Pass 2 섹션별 프롬프트 구성 (큰 문서를 분할 처리할 때 사용)"""
        prompt = self.latex_upgrade_prompt
        prompt += "\n\n" + "=" * 60 + "\n"
        prompt += "## 마스터 템플릿 (이 프리앰블을 기준으로 검증하세요):\n"
        prompt += "```latex\n"
        prompt += self.master_template
        prompt += "\n```\n\n"
        prompt += f"## 검증 및 수정 대상 LaTeX 소스 (섹션 {section_idx}/{total_sections}):\n"
        prompt += "이것은 전체 문서의 일부분입니다. 이 부분만 검증하고 수정하세요.\n"
        prompt += "\\documentclass, \\begin{document}, \\end{document} 등 문서 구조 명령은 출력하지 마세요.\n"
        prompt += "본문 내용만 출력하세요.\n\n"
        prompt += "```latex\n"
        prompt += section_latex
        prompt += "\n```\n\n"
        prompt += "위 LaTeX 소스를 마스터 템플릿 기준으로 검증하고 수정한 LaTeX 본문을 출력하세요.\n"
        prompt += "수정된 LaTeX 본문만 출력하세요. 설명이나 코멘트는 불필요합니다.\n"
        prompt += "내용을 절대 축약하거나 생략하지 마세요. 원본의 모든 내용을 유지하세요.\n"
        return prompt

    def _split_body_into_sections(self, body: str, max_section_chars: int = 40000) -> List[str]:
        """본문을 \\section 경계에서 분할 (Pass 2 분할 처리용)"""
        # \section 위치 찾기
        section_pattern = r'(?=\\section(?:\*)?(?:\[|\{))'
        parts = re.split(section_pattern, body)
        parts = [p for p in parts if p.strip()]

        if not parts:
            return [body]

        # 인접한 섹션들을 max_section_chars 이하로 묶기
        merged = []
        current = ""
        for part in parts:
            if current and len(current) + len(part) > max_section_chars:
                merged.append(current)
                current = part
            else:
                current += part
        if current:
            merged.append(current)

        return merged

    def _run_pass2_chunked(self, raw_latex: str) -> str:
        """큰 문서에 대해 Pass 2를 섹션별로 분할 처리"""
        body = self._extract_body(raw_latex)
        body = self._clean_body(body)

        sections = self._split_body_into_sections(body)
        total = len(sections)
        print(f"  📦 Pass 2 분할 처리: {total}개 섹션")

        upgraded_sections = []
        for i, section in enumerate(sections):
            print(f"\n  --- Pass 2 섹션 {i + 1}/{total} ({len(section):,}자) ---")
            prompt = self._build_pass2_section_prompt(section, i + 1, total)
            result = self._call_gemini(prompt, [], f"Pass 2 섹션 {i + 1}/{total}")
            result = self._extract_latex_from_response(result)
            # 결과에서 문서 구조 제거 (본문만 추출)
            result_body = self._extract_body(result) if '\\begin{document}' in result else result
            result_body = self._clean_body(result_body)
            upgraded_sections.append(result_body)

            if i < total - 1:
                print(f"  ⏳ 다음 섹션 전 5초 대기...")
                time.sleep(5)

        # 병합하여 완전한 문서로 재구성
        merged_body = "\n\n".join(upgraded_sections)
        return (
            "\\documentclass[11pt,a4paper]{article}\n"
            "\\begin{document}\n\n"
            + merged_body +
            "\n\n\\end{document}\n"
        )

    # ------------------------------------------------------------------
    # LaTeX 추출 / 병합
    # ------------------------------------------------------------------

    def _extract_latex_from_response(self, response: str) -> str:
        """API 응답에서 LaTeX 코드 추출"""
        # ```latex ... ``` 블록이 있으면 추출
        latex_block = re.search(r'```latex\s*\n(.*?)```', response, re.DOTALL)
        if latex_block:
            return latex_block.group(1).strip()

        # ``` ... ``` 블록
        code_block = re.search(r'```\s*\n(.*?)```', response, re.DOTALL)
        if code_block:
            content = code_block.group(1).strip()
            if '\\documentclass' in content or '\\begin{document}' in content:
                return content

        # \documentclass로 시작하는 부분 찾기
        doc_match = re.search(r'(\\documentclass.*?)$', response, re.DOTALL)
        if doc_match:
            return doc_match.group(1).strip()

        return response.strip()

    def _extract_body(self, latex: str) -> str:
        """LaTeX 문서에서 \\begin{document} ~ \\end{document} 사이 본문 추출"""
        # 마지막 \begin{document}부터 마지막 \end{document}까지 추출 (greedy)
        body_match = re.search(
            r'\\begin\{document\}(.*?)\\end\{document\}',
            latex, re.DOTALL
        )
        if body_match:
            return body_match.group(1).strip()

        # \begin{document}만 있고 \end{document}가 없는 경우
        begin_match = re.search(r'\\begin\{document\}', latex)
        if begin_match:
            return latex[begin_match.end():].strip()

        return latex.strip()

    def _clean_body(self, body: str) -> str:
        """본문에서 preamble 명령어 제거 (Gemini가 body에 삽입한 경우)"""
        # \documentclass 이하 preamble 전체가 body에 포함된 경우:
        # \documentclass부터 \begin{document}까지를 제거
        body = re.sub(
            r'\\documentclass.*?\\begin\{document\}',
            '', body, flags=re.DOTALL
        )
        # 잔여 \end{document} 제거
        body = body.replace('\\end{document}', '')

        # 개별 preamble 명령 제거
        body = re.sub(r'\\usepackage(?:\[[^\]]*\])?\{[^}]+\}[^\n]*\n?', '', body)
        body = re.sub(r'\\documentclass(?:\[[^\]]*\])?\{[^}]+\}[^\n]*\n?', '', body)
        body = re.sub(r'\\pretitle\{[^}]*\}', '', body)
        body = re.sub(r'\\posttitle\{[^}]*\}', '', body)
        body = re.sub(r'\\preauthor\{[^}]*\}', '', body)
        body = re.sub(r'\\postauthor\{[^}]*\}', '', body)
        body = re.sub(r'\\predate\{[^}]*\}', '', body)
        body = re.sub(r'\\postdate\{[^}]*\}', '', body)
        body = re.sub(r'\\titlespacing\*?\{[^}]+\}\{[^}]+\}\{[^}]+\}\{[^}]+\}', '', body)
        # \newcommand{\metainfo}[4]{...} 블록 (여러 줄에 걸침)
        body = re.sub(
            r'\\newcommand\{\\metainfo\}\[4\]\{.*?(?:\\end\{tcolorbox\}\s*\})',
            '', body, flags=re.DOTALL
        )
        # \renewcommand, \setlength, \onehalfspacing 등 preamble 전용 명령
        body = re.sub(r'\\renewcommand\{\\arraystretch\}\{[^}]+\}', '', body)
        body = re.sub(r'\\setlength\{\\[^}]+\}\{[^}]+\}', '', body)
        body = re.sub(r'\\onehalfspacing\s*', '', body)
        body = re.sub(r'\\pagestyle\{[^}]+\}', '', body)
        body = re.sub(r'\\fancyhf\{[^}]*\}', '', body)
        body = re.sub(r'\\fancyhead(?:\[[^\]]*\])?\{[^}]*\}', '', body)
        body = re.sub(r'\\fancyfoot(?:\[[^\]]*\])?\{[^}]*\}', '', body)
        # \definecolor, \newtcolorbox 등 정의 명령
        body = re.sub(r'\\definecolor\{[^}]+\}\{[^}]+\}\{[^}]+\}', '', body)
        body = re.sub(
            r'\\newtcolorbox\{[^}]+\}(?:\[[^\]]*\])*\{[^}]*(?:\{[^}]*\}[^}]*)*\}',
            '', body
        )
        # \tcbuselibrary, \lstset 등
        body = re.sub(r'\\tcbuselibrary\{[^}]+\}', '', body)
        body = re.sub(r'\\lstset\{.*?\}', '', body, flags=re.DOTALL)
        body = re.sub(r'\\lstdefinestyle\{[^}]+\}\{.*?\}', '', body, flags=re.DOTALL)
        # %=== 구분자 주석 블록 (빈 내용 사이에 있는 것만)
        body = re.sub(r'\n%=+\n%[^\n]*\n%=+\n(?=\s*\n)', '\n', body)
        # 빈 줄 정리
        body = re.sub(r'\n{4,}', '\n\n\n', body)

        return body.strip()

    def _merge_chunk_bodies(self, chunk_results: List[str]) -> str:
        """여러 청크의 LaTeX 본문을 하나로 병합"""
        bodies = []
        for i, latex in enumerate(chunk_results):
            body = self._extract_body(latex)
            body = self._clean_body(body)
            if body:
                if i > 0:
                    bodies.append("\\newpage")
                bodies.append(body)
        return "\n\n".join(bodies)

    def _merge_with_template(self, latex_body: str, course_name: str,
                              module_title: str, module_num: int) -> str:
        """마스터 템플릿 프리앰블 + Gemini 본문 병합"""
        body = self._extract_body(latex_body)
        body = self._clean_body(body)

        # 마스터 템플릿의 헤더 커스터마이즈
        preamble = self.master_template
        preamble = preamble.replace("COURSE\\_NAME", course_name.replace("_", "\\_"))
        preamble = preamble.replace("LECTURE\\_NUMBER", f"Module {module_num:02d}")
        preamble = preamble.replace("COURSE\\_NAME - LECTURE\\_NUMBER",
                                     f"{course_name} - {module_title}")

        final = preamble + "\n\n\\begin{document}\n\n" + body + "\n\n\\end{document}\n"
        return final

    # ------------------------------------------------------------------
    # 메인 생성 로직
    # ------------------------------------------------------------------

    def generate_note(self, course_key: str, module: Dict,
                      skip_pass2: bool = False) -> Optional[Path]:
        """
        단일 모듈의 LaTeX 노트 생성 (TXT 파일 → 청킹 → Pass 1 × N → 병합 → Pass 2)

        Args:
            course_key: 과목 키 (예: 'fin-571')
            module: 모듈 정보 딕셔너리
            skip_pass2: True면 Pass 2(업그레이드) 건너뜀

        Returns:
            생성된 .tex 파일 경로 (실패 시 None)
        """
        course = COURSES[course_key]
        module_num = module["num"]
        txt_name = module["txt"]
        output_name = module["output"]
        module_title = module["title"]
        course_name = course["name"]

        print(f"\n{'=' * 70}")
        print(f"📚 [{course['short']}] Module {module_num}: {module_title}")
        print(f"{'=' * 70}")

        # TXT 파일 경로 확인 및 읽기
        source_type = course.get("source_type", "source")
        base_dir = self.paths.school / course["university"] / course_key

        if source_type == "materials":
            # Harvard style: lecture_XX/materials/script.txt
            materials_dir = base_dir / f"lecture_{module_num:02d}" / "materials"
            if isinstance(txt_name, list):
                # 여러 파일 병합 (예: script.txt + section.txt)
                parts = []
                for fname in txt_name:
                    fpath = materials_dir / fname
                    if fpath.exists():
                        with open(fpath, 'r', encoding='utf-8') as f:
                            parts.append(f.read())
                    else:
                        print(f"  ⚠️ 파일 없음 (건너뜀): {fpath}")
                if not parts:
                    print(f"  ❌ TXT 파일 없음: {materials_dir}")
                    return None
                full_text = "\n\n".join(parts)
                print(f"  📄 TXT: {txt_name} ({len(full_text):,}자, {len(parts)}개 파일 병합)")
            else:
                txt_path = materials_dir / txt_name
                if not txt_path.exists():
                    print(f"  ❌ TXT 파일 없음: {txt_path}")
                    return None
                with open(txt_path, 'r', encoding='utf-8') as f:
                    full_text = f.read()
                print(f"  📄 TXT: {txt_name} ({len(full_text):,}자)")
        else:
            # UIUC style: source/filename.txt
            txt_path = base_dir / "source" / txt_name
            if not txt_path.exists():
                print(f"  ❌ TXT 파일 없음: {txt_path}")
                return None
            with open(txt_path, 'r', encoding='utf-8') as f:
                full_text = f.read()
            print(f"  📄 TXT: {txt_name} ({len(full_text):,}자)")

        # 출력 디렉토리
        output_dir = self.paths.school / course["university"] / course_key / f"lecture_{module_num:02d}"
        output_dir.mkdir(parents=True, exist_ok=True)

        # ----------------------------------------------------------------
        # 텍스트 청킹
        # ----------------------------------------------------------------
        toc = self._extract_toc(full_text)
        chunks = self._split_by_lessons(full_text)
        total_chunks = len(chunks)

        print(f"  📦 청크 분할: {total_chunks}개")
        for i, chunk in enumerate(chunks):
            print(f"    [{i + 1}/{total_chunks}] {', '.join(chunk['lessons'][:3])}"
                  f"{'...' if len(chunk['lessons']) > 3 else ''}"
                  f" ({len(chunk['text']):,}자)")

        # ----------------------------------------------------------------
        # Pass 1: 청크별 note_generation.txt → raw LaTeX
        # ----------------------------------------------------------------
        chunk_results = []

        if total_chunks == 1:
            # 청크가 1개면 일반 처리 (청크 컨텍스트 없이)
            pass1_prompt = self._build_pass1_prompt(course_name, module_title)
            content_parts = [
                types.Part.from_text(
                    text=f"아래는 '{module_title}' 강의 자료의 전체 텍스트입니다:\n\n{chunks[0]['text']}"
                )
            ]
            raw = self._call_gemini(pass1_prompt, content_parts, "Pass 1 (노트 생성)")
            raw = self._extract_latex_from_response(raw)
            chunk_results.append(raw)
        else:
            # 여러 청크: 각각 Pass 1 호출
            for i, chunk in enumerate(chunks):
                print(f"\n  --- 청크 {i + 1}/{total_chunks} ---")
                pass1_prompt = self._build_pass1_chunk_prompt(
                    course_name, module_title, toc,
                    i, total_chunks, chunk["lessons"]
                )
                content_parts = [
                    types.Part.from_text(
                        text=f"아래는 '{module_title}' 파트 {i + 1}/{total_chunks}의 텍스트입니다:\n\n{chunk['text']}"
                    )
                ]
                raw = self._call_gemini(pass1_prompt, content_parts,
                                        f"Pass 1 청크 {i + 1}/{total_chunks}")
                raw = self._extract_latex_from_response(raw)
                chunk_results.append(raw)

                # 청크 간 API rate limit 대비
                if i < total_chunks - 1:
                    print(f"  ⏳ 다음 청크 전 5초 대기...")
                    time.sleep(5)

        # 청크 결과 병합
        if total_chunks > 1:
            merged_body = self._merge_chunk_bodies(chunk_results)
            # 임시 완전한 문서로 래핑 (Pass 2 입력용)
            raw_latex = (
                "\\documentclass[11pt,a4paper]{article}\n"
                "\\begin{document}\n\n"
                + merged_body +
                "\n\n\\end{document}\n"
            )
        else:
            raw_latex = chunk_results[0]

        # 중간 저장 (디버깅용)
        raw_path = output_dir / f"{output_name}_raw.tex"
        with open(raw_path, 'w', encoding='utf-8') as f:
            f.write(raw_latex)
        print(f"  💾 Pass 1 중간 저장: {raw_path.name}")

        # ----------------------------------------------------------------
        # Pass 2: latex_upgrade.txt + raw LaTeX → final LaTeX
        # ----------------------------------------------------------------
        PASS2_CHUNKED_THRESHOLD = 50000  # 본문이 이 크기를 초과하면 분할 처리
        if not skip_pass2:
            raw_body = self._extract_body(raw_latex)
            if len(raw_body) > PASS2_CHUNKED_THRESHOLD:
                print(f"  📏 Pass 1 본문 크기: {len(raw_body):,}자 (>{PASS2_CHUNKED_THRESHOLD:,}) → 분할 처리")
                upgraded_latex = self._run_pass2_chunked(raw_latex)
            else:
                pass2_prompt = self._build_pass2_prompt(raw_latex)
                content_parts_pass2 = []
                upgraded_latex = self._call_gemini(pass2_prompt, content_parts_pass2,
                                                   "Pass 2 (업그레이드)")
                upgraded_latex = self._extract_latex_from_response(upgraded_latex)
        else:
            print(f"  ⏭️ Pass 2 건너뜀")
            upgraded_latex = raw_latex

        # ----------------------------------------------------------------
        # 마스터 템플릿 병합 + 후처리
        # ----------------------------------------------------------------
        final_latex = self._merge_with_template(
            upgraded_latex, course_name, module_title, module_num
        )

        # 파일 저장
        final_path = output_dir / f"{output_name}.tex"
        with open(final_path, 'w', encoding='utf-8') as f:
            f.write(final_latex)
        print(f"  💾 최종 저장: {final_path.name}")

        # fix_latex_errors.py 자동 수정
        print(f"  🔧 LaTeX 에러 자동 수정 중...")
        fix_latex_file(final_path, verbose=False)

        return final_path

    def compile_tex(self, tex_path: Path) -> bool:
        """
        xelatex으로 2-pass 컴파일 + 에러 시 자동 수정 재시도

        Args:
            tex_path: .tex 파일 경로

        Returns:
            성공 여부
        """
        compiler = find_xelatex_path()
        work_dir = tex_path.parent

        for attempt in range(3):  # 최대 3회 시도
            print(f"\n  🔨 컴파일 시도 {attempt + 1}/3...")

            success = True
            for pass_num in range(2):  # 2-pass
                print(f"    [{pass_num + 1}/2] xelatex 실행 중...", end=" ")
                try:
                    result = subprocess.run(
                        [compiler, '-interaction=nonstopmode', tex_path.name],
                        cwd=str(work_dir),
                        capture_output=True,
                        text=True,
                        timeout=180,
                        encoding='utf-8',
                        errors='replace',
                    )
                    if result.returncode != 0:
                        print("⚠️")
                        success = False
                    else:
                        print("✓")
                except subprocess.TimeoutExpired:
                    print("⏱️ 시간 초과")
                    success = False
                    break
                except FileNotFoundError:
                    print(f"❌ '{compiler}' 명령 없음")
                    return False

            # PDF 생성 확인
            pdf_path = tex_path.with_suffix('.pdf')
            if pdf_path.exists() and pdf_path.stat().st_size > 0:
                print(f"  ✅ PDF 생성 완료: {pdf_path.name} ({pdf_path.stat().st_size:,} bytes)")
                cleanup_aux_files(tex_path)
                return True

            # 에러 시 로그 분석 + 자동 수정
            if attempt < 2:
                log_path = tex_path.with_suffix('.log')
                if log_path.exists():
                    print(f"  🔍 로그 분석 중...")
                    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                        log_content = f.read()
                    errors = [l for l in log_content.split('\n') if l.startswith('!')]
                    for e in errors[:5]:
                        print(f"    ❌ {e}")

                print(f"  🔧 자동 수정 후 재시도...")
                fix_latex_file(tex_path, verbose=False)

        print(f"  ❌ 컴파일 실패: 3회 시도 모두 실패")
        cleanup_aux_files(tex_path)
        return False


# ============================================================================
# 메인 함수
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Gemini API를 사용한 2-pass LaTeX 노트 자동 생성기 (TXT + 청킹)'
    )
    parser.add_argument(
        '--course', type=str, required=True,
        choices=list(COURSES.keys()) + ['all'],
        help='처리할 과목 (fin-571, badm-572, cs109, csci103, csci89, all)'
    )
    parser.add_argument(
        '--modules', type=str, default=None,
        help='처리할 모듈 번호 (콤마 구분, 예: 1,2,3)'
    )
    parser.add_argument(
        '--skip-compile', action='store_true',
        help='LaTeX 컴파일 건너뛰기'
    )
    parser.add_argument(
        '--skip-pass2', action='store_true',
        help='Pass 2 (업그레이드) 건너뛰기'
    )
    parser.add_argument(
        '--model', type=str, default='gemini-2.5-flash',
        help='Gemini 모델 (기본값: gemini-2.5-flash)'
    )
    parser.add_argument(
        '--chunk-size', type=int, default=DEFAULT_CHUNK_MAX_CHARS,
        help=f'청크당 최대 문자수 (기본값: {DEFAULT_CHUNK_MAX_CHARS})'
    )

    args = parser.parse_args()

    print_header("🤖 Gemini API 2-Pass LaTeX 노트 생성기 (TXT + 청킹)", width=70)
    print(f"  모델: {args.model}")
    print(f"  과목: {args.course}")
    print(f"  청크 크기: {args.chunk_size:,}자")
    if args.modules:
        print(f"  모듈: {args.modules}")
    if args.skip_pass2:
        print(f"  Pass 2: 건너뜀")
    print()

    # 과목 목록 결정
    if args.course == 'all':
        course_keys = list(COURSES.keys())
    else:
        course_keys = [args.course]

    # 모듈 필터
    module_filter = None
    if args.modules:
        module_filter = [int(m.strip()) for m in args.modules.split(',')]

    # 생성기 초기화
    try:
        generator = GeminiNoteGenerator(
            model_name=args.model,
            chunk_max_chars=args.chunk_size,
        )
    except ValueError as e:
        print(f"\n❌ {e}")
        return 1

    # 결과 추적
    success_files: List[Path] = []
    failed_modules: List[str] = []

    for course_key in course_keys:
        course = COURSES[course_key]
        print_header(f"📘 {course['name']}", width=70)

        # 처리 순서
        max_module = max(m["num"] for m in course["modules"])
        order = PROCESSING_ORDER.get(course_key, list(range(1, max_module + 1)))

        for module_num in order:
            # 모듈 필터 적용
            if module_filter and module_num not in module_filter:
                continue

            # 모듈 정보 찾기
            module = next((m for m in course["modules"] if m["num"] == module_num), None)
            if not module:
                print(f"  ⚠️  모듈 {module_num} 없음, 건너뜀")
                continue

            try:
                tex_path = generator.generate_note(
                    course_key, module, skip_pass2=args.skip_pass2
                )
                if tex_path:
                    if not args.skip_compile:
                        compile_ok = generator.compile_tex(tex_path)
                        if compile_ok:
                            success_files.append(tex_path)
                        else:
                            failed_modules.append(f"{course['short']} M{module_num} (컴파일 실패)")
                    else:
                        success_files.append(tex_path)
                        print(f"  ⏭️ 컴파일 건너뜀")
                else:
                    failed_modules.append(f"{course['short']} M{module_num} (생성 실패)")

            except Exception as e:
                print(f"\n  ❌ 에러: {e}")
                import traceback
                traceback.print_exc()
                failed_modules.append(f"{course['short']} M{module_num} ({e})")

            # API rate limit 대비 대기
            print(f"\n  ⏳ 다음 모듈 전 10초 대기...")
            time.sleep(10)

    # ================================================================
    # 결과 요약
    # ================================================================
    print_separator(width=70)
    print_header("📊 최종 결과", width=70)
    print(f"  ✅ 성공: {len(success_files)}개")
    print(f"  ❌ 실패: {len(failed_modules)}개")

    if success_files:
        print(f"\n  성공 파일:")
        for f in success_files:
            print(f"    ✅ {f}")

    if failed_modules:
        print(f"\n  실패 모듈:")
        for m in failed_modules:
            print(f"    ❌ {m}")

    return 0 if not failed_modules else 1


if __name__ == '__main__':
    sys.exit(main())
