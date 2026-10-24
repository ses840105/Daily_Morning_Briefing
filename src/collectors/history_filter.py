# -*- coding: utf-8 -*-
"""
Cross-Day History & Duplicate Filter for Daily Morning Briefing
Scans previous days' markdown briefings in outputs/markdown/ to prevent repetitive news,
duplicate ArXiv papers, and redundant YouTube videos across consecutive days.
"""

import os
import glob
import re
from datetime import datetime, timedelta
from typing import Set, Dict, List, Any


def normalize_title(title: str) -> str:
    """헤드라인 제목의 노이즈(대괄호, 언론사 태그, 기호, 공백)를 제거하여 순수 텍스트로 정규화합니다."""
    s = title.strip()
    s = re.sub(r"\[[^\]]*\]", "", s)
    s = re.sub(r"\([^\)]*\)", "", s)
    s = re.sub(r"[^가-힣a-zA-Z0-9]", "", s)
    return s.lower()


def extract_arxiv_id(link_or_title: str) -> str:
    """ArXiv 논문 ID(예: 2410.12345, 2610.30132)를 추출합니다."""
    m = re.search(r"(\d{4}\.\d{4,5})", link_or_title)
    return m.group(1) if m else ""


def extract_youtube_id(link: str) -> str:
    """YouTube 비디오 ID(11글자)를 추출합니다."""
    m = re.search(r"(?:v=|/vi/|youtu\.be/|/v/|/embed/)([a-zA-Z0-9_-]{11})", link)
    return m.group(1) if m else ""


class HistoryFilter:
    """최근 14일간의 브리핑 아티팩트에서 이미 보도된 기사, 논문, 유튜브를 추적하는 필터 클래스"""

    def __init__(self, outputs_dir: str, days: int = 14, current_date_str: str = None):
        self.outputs_dir = outputs_dir
        self.md_dir = os.path.join(outputs_dir, "markdown")
        self.seen_titles: Set[str] = set()
        self.seen_links: Set[str] = set()
        self.seen_arxiv_ids: Set[str] = set()
        self.seen_youtube_ids: Set[str] = set()

        self._load_history(days=days, exclude_date=current_date_str)

    def _load_history(self, days: int = 14, exclude_date: str = None):
        if not os.path.exists(self.md_dir):
            return

        today = datetime.now().date()
        min_date = today - timedelta(days=days)

        pattern = os.path.join(self.md_dir, "briefing_*.md")
        for md_file in glob.glob(pattern):
            basename = os.path.basename(md_file)
            if basename == "latest_briefing.md":
                continue

            date_match = re.search(r"briefing_(\d{4}-\d{2}-\d{2})\.md", basename)
            if not date_match:
                continue

            file_date_str = date_match.group(1)
            # 오늘 날짜는 검사 대상(과거 이력)에서 제외
            if exclude_date and file_date_str == exclude_date:
                continue

            try:
                f_date = datetime.strptime(file_date_str, "%Y-%m-%d").date()
                if f_date < min_date:
                    continue
            except Exception:
                pass

            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # 마크다운 링크 파싱: [제목](링크)
                matches = re.findall(r"\[([^\]]+)\]\((https?://[^\)]+)\)", content)
                for title, link in matches:
                    norm_t = normalize_title(title)
                    if len(norm_t) >= 6:
                        self.seen_titles.add(norm_t)
                    self.seen_links.add(link.strip())

                    a_id = extract_arxiv_id(link) or extract_arxiv_id(title)
                    if a_id:
                        self.seen_arxiv_ids.add(a_id)

                    y_id = extract_youtube_id(link)
                    if y_id:
                        self.seen_youtube_ids.add(y_id)
            except Exception as e:
                print(f"[HistoryFilter] Error reading {md_file}: {e}")

    def is_duplicate(self, item: Dict[str, Any]) -> bool:
        """기사/논문/영상 아이템이 이전 브리핑에 이미 수록되었는지 판별합니다."""
        title = item.get("title", "")
        link = item.get("link", "")
        vid = item.get("video_id", "") or extract_youtube_id(link)

        # 1. 유튜브 비디오 ID 중복 검사
        if vid and vid in self.seen_youtube_ids:
            return True

        # 2. ArXiv 논문 ID 중복 검사
        a_id = extract_arxiv_id(link) or extract_arxiv_id(title)
        if a_id and a_id in self.seen_arxiv_ids:
            return True

        # 3. 링크 완전 일치 검사
        if link and link in self.seen_links:
            return True

        # 4. 정규화 제목 일치 검사
        norm_t = normalize_title(title)
        if len(norm_t) >= 8 and norm_t in self.seen_titles:
            return True

        # 5. 핵심 어휘 겹침(유사도) 검사: 80% 이상 유사할 경우 같은 뉴스 클러스터로 판정
        for past_t in self.seen_titles:
            if len(norm_t) >= 12 and len(past_t) >= 12:
                if norm_t in past_t or past_t in norm_t:
                    return True

        return False
