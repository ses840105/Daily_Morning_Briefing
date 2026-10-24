# -*- coding: utf-8 -*-
"""
World & Economy Collector for Daily Morning Briefing
Collects fresh global economy, military/defense, and world diplomacy news
with cross-day deduplication, time-window filtering (when:2d), and publisher diversity.
"""

import os
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import re
from email.utils import parsedate_to_datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from src.collectors.history_filter import HistoryFilter, normalize_title


class WorldEconCollector:
    """
    글로벌 경제, 군사/안보, 세계 정세 뉴스 수집기
    (다채로운 서브토픽, 시의성 48시간 필터링, 언론사 편중 방지 및 일자 간 중복 제거 지원)
    """

    def __init__(self, outputs_dir: Optional[str] = None):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        if outputs_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            outputs_dir = os.path.join(base_dir, "outputs")
        self.outputs_dir = outputs_dir
        today_str = datetime.now().strftime("%Y-%m-%d")
        self.history_filter = HistoryFilter(self.outputs_dir, days=14, current_date_str=today_str)

    def _parse_related_from_desc(self, desc_html: str, main_title: str) -> List[Dict[str, str]]:
        """Google News RSS <description> 내 <ol><li> 클러스터에서 관련 기사를 추출합니다."""
        related = []
        if not desc_html or "<li" not in desc_html:
            return related
        try:
            li_blocks = re.findall(r"<li[^>]*>(.*?)</li>", desc_html, re.DOTALL)
            for block in li_blocks:
                a_match = re.search(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', block, re.DOTALL)
                font_match = re.search(r'<font[^>]*>(.*?)</font>', block, re.DOTALL)
                if a_match:
                    r_link = a_match.group(1).strip()
                    r_title = re.sub(r"<[^>]+>", "", a_match.group(2)).strip()
                    r_source = re.sub(r"<[^>]+>", "", font_match.group(1)).strip() if font_match else "Google News"
                    if r_title and r_title != main_title:
                        related.append({
                            "title": r_title,
                            "source": r_source,
                            "link": r_link
                        })
        except Exception:
            pass
        return related[:3]

    def _fetch_rss(self, url: str) -> List[Dict[str, Any]]:
        """RSS 피드를 요청하고 파싱하여 발행일시 datetime 객체와 함께 반환합니다."""
        items = []
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                xml_data = resp.read()
                tree = ET.fromstring(xml_data)
                now_utc = datetime.now(timezone.utc)
                for item in tree.findall('.//item')[:20]:
                    title = item.findtext('title') or ""
                    link = item.findtext('link') or ""
                    pub_date = item.findtext('pubDate') or ""
                    desc_html = item.findtext('description') or ""

                    source_el = item.find('source')
                    source = source_el.text if (source_el is not None and source_el.text) else "Google News"
                    source_url = source_el.attrib.get('url', '') if source_el is not None else ""

                    # 제목 정제 (언론사 태그 분리)
                    title_clean = title
                    if " - " in title:
                        parts = title.rsplit(" - ", 1)
                        title_clean = parts[0]
                        if source == "Google News":
                            source = parts[1]

                    title_clean = title_clean.strip()
                    if not title_clean or len(title_clean) < 5:
                        continue

                    # 발행일시 파싱 및 시간 차 계산
                    pub_dt = None
                    time_ago_str = "오늘"
                    if pub_date:
                        try:
                            pub_dt = parsedate_to_datetime(pub_date)
                            diff_hours = (now_utc - pub_dt).total_seconds() / 3600
                            if diff_hours < 1:
                                time_ago_str = "방금 전"
                            elif diff_hours < 24:
                                time_ago_str = f"{int(diff_hours)}시간 전"
                            elif diff_hours < 48:
                                time_ago_str = "어제"
                            else:
                                diff_days = int(diff_hours / 24)
                                time_ago_str = f"{diff_days}일 전"
                        except Exception:
                            pass

                    related = self._parse_related_from_desc(desc_html, title_clean)

                    items.append({
                        "title": title_clean,
                        "source": source.strip(),
                        "source_url": source_url.strip(),
                        "link": link.strip(),
                        "pub_date": pub_date.strip(),
                        "pub_dt": pub_dt,
                        "time_ago": time_ago_str,
                        "related_articles": related
                    })
        except Exception as e:
            print(f"[WorldEconCollector] RSS error: {e}")
        return items

    def _filter_and_cap_items(self, candidate_items: List[Dict[str, Any]], target_count: int = 6, max_per_source: int = 2) -> List[Dict[str, Any]]:
        """
        1) 최신순 정렬
        2) 최근 14일 이전 브리핑 수록 기사 중복 제거 (HistoryFilter)
        3) 동일 언론사 최대 max_per_source건 제한
        4) 세션 내 제목 유사도 중복 제거
        """
        candidates = sorted(
            candidate_items,
            key=lambda x: x.get("pub_dt") or datetime.fromtimestamp(0, tz=timezone.utc),
            reverse=True
        )

        selected = []
        source_counts: Dict[str, int] = {}
        seen_session_titles: List[str] = []

        # 1차 패스: 이전 날짜에 보도되지 않은 신선한 기사 우선 선별
        for item in candidates:
            if self.history_filter.is_duplicate(item):
                continue

            src = item.get("source", "Google News")
            if source_counts.get(src, 0) >= max_per_source:
                continue

            norm_t = normalize_title(item["title"])
            is_dup_title = False
            for past_t in seen_session_titles:
                if len(norm_t) >= 10 and len(past_t) >= 10:
                    if norm_t in past_t or past_t in norm_t:
                        is_dup_title = True
                        break
            if is_dup_title:
                continue

            selected.append(item)
            source_counts[src] = source_counts.get(src, 0) + 1
            seen_session_titles.append(norm_t)
            if len(selected) >= target_count:
                return selected

        # 2차 패스: 잔여분 보충
        if len(selected) < target_count:
            for item in candidates:
                if item in selected:
                    continue
                norm_t = normalize_title(item["title"])
                if norm_t in seen_session_titles:
                    continue
                selected.append(item)
                seen_session_titles.append(norm_t)
                if len(selected) >= target_count:
                    break

        return selected[:target_count]

    def collect_all(self) -> Dict[str, Any]:
        """경제, 군사/안보, 세계 외교 뉴스 다각도 병렬 수집 (when:2d)"""
        econ_queries = [
            '("기준금리" OR "연준" OR "한국은행" OR "물가" OR "국채금리") when:2d',
            '("원달러 환율" OR "코스피" OR "나스닥" OR "뉴욕증시" OR "반도체 수출") when:2d',
            '("글로벌 경제" OR "관세" OR "무역수지" OR "외환시장") when:2d'
        ]

        mil_queries = [
            '("국방" OR "K방산" OR "방위산업" OR "군사안보" OR "무기수출") when:2d',
            '("나토" OR "중동 안보" OR "우크라이나" OR "한미연합" OR "드론 방어") when:2d'
        ]

        world_queries = [
            '("정상회담" OR "외교" OR "미중관계" OR "한미외교" OR "유럽연합") when:2d',
            '("국제정세" OR "글로벌 공급망" OR "통상협상" OR "유엔") when:2d'
        ]

        def fetch_multi_subqueries(queries: List[str]) -> List[Dict[str, Any]]:
            combined = []
            for q in queries:
                url = f"https://news.google.com/rss/search?q={urllib.parse.quote(q)}&hl=ko&gl=KR&ceid=KR:ko"
                items = self._fetch_rss(url)
                combined.extend(items)
            if len(combined) < 10:
                relaxed_q = queries[0].replace("when:2d", "when:7d")
                url_rel = f"https://news.google.com/rss/search?q={urllib.parse.quote(relaxed_q)}&hl=ko&gl=KR&ceid=KR:ko"
                combined.extend(self._fetch_rss(url_rel))
            return combined

        with ThreadPoolExecutor(max_workers=6) as ex:
            f_econ = ex.submit(fetch_multi_subqueries, econ_queries)
            f_mil = ex.submit(fetch_multi_subqueries, mil_queries)
            f_world = ex.submit(fetch_multi_subqueries, world_queries)

            econ_raw = f_econ.result()
            mil_raw = f_mil.result()
            world_raw = f_world.result()

        econ_news = self._filter_and_cap_items(econ_raw, target_count=6, max_per_source=2)
        military_news = self._filter_and_cap_items(mil_raw, target_count=6, max_per_source=2)
        world_news = self._filter_and_cap_items(world_raw, target_count=6, max_per_source=2)

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "economy_headlines": econ_news[:6],
            "military_headlines": military_news[:6],
            "world_headlines": world_news[:6]
        }
