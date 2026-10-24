# -*- coding: utf-8 -*-
"""
Tech & AI Collector for Daily Morning Briefing
Collects fresh AI/ML news, semiconductor/bigtech news, ArXiv papers, YouTube videos,
and Cutting-Edge AI/ML Tools & Techniques with cross-day deduplication and time-window filtering.
"""

import os
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import re
from email.utils import parsedate_to_datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta

from src.collectors.history_filter import HistoryFilter, normalize_title
from src.collectors.tools_catalog import get_daily_tools_and_methods


class TechAICollector:
    """
    최신 ML, AI, IT 기술 동향 및 YouTube 테크 영상, ArXiv 논문, AI 툴/기법 수집기
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
            print(f"[TechAICollector] RSS fetch error ({url[:45]}...): {e}")
        return items

    def _filter_and_cap_items(self, candidate_items: List[Dict[str, Any]], target_count: int = 6, max_per_source: int = 2) -> List[Dict[str, Any]]:
        """
        1) 최신순 정렬
        2) 최근 14일 이전 브리핑 수록 기사 중복 제거 (HistoryFilter)
        3) 동일 언론사 최대 max_per_source건 제한
        4) 세션 내 제목 유사도 중복 제거
        """
        # 최신순 정렬 (pub_dt 기준, 없으면 뒤로)
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
            # 과거 브리핑 중복 배제
            if self.history_filter.is_duplicate(item):
                continue

            src = item.get("source", "Google News")
            if source_counts.get(src, 0) >= max_per_source:
                continue

            # 섹션 내 제목 중복 검사
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

        # 2차 패스: 6건 미만일 경우 언론사 제한 완화 및 백필
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

    def _fetch_youtube_channel_feed(self, channel_id: str, channel_name: str) -> List[Dict[str, Any]]:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        videos = []
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                tree = ET.fromstring(resp.read())
                ns = {
                    'atom': 'http://www.w3.org/2005/Atom',
                    'yt': 'http://www.youtube.com/xml/schemas/2015',
                    'media': 'http://search.yahoo.com/mrss/'
                }
                for entry in tree.findall('atom:entry', ns)[:6]:
                    title = entry.findtext('atom:title', namespaces=ns) or ""
                    link_el = entry.find('atom:link', ns)
                    link = link_el.attrib.get('href', '') if link_el is not None else ""
                    published = entry.findtext('atom:published', namespaces=ns) or ""
                    vid_el = entry.find('yt:videoId', ns)
                    video_id = vid_el.text.strip() if (vid_el is not None and vid_el.text) else ""

                    thumbnail = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg" if video_id else ""
                    description = ""
                    views_str = ""

                    mg = entry.find('media:group', ns)
                    if mg is not None:
                        thumb_el = mg.find('media:thumbnail', ns)
                        if thumb_el is not None and thumb_el.attrib.get('url'):
                            thumbnail = thumb_el.attrib.get('url', thumbnail)
                        desc_el = mg.find('media:description', ns)
                        if desc_el is not None and desc_el.text:
                            description = desc_el.text.strip()
                        comm_el = mg.find('media:community', ns)
                        if comm_el is not None:
                            stat_el = comm_el.find('media:statistics', ns)
                            if stat_el is not None and stat_el.attrib.get('views'):
                                try:
                                    v_cnt = int(stat_el.attrib['views'])
                                    views_str = f"조회수 {v_cnt:,}회"
                                except Exception:
                                    pass

                    videos.append({
                        "title": title.strip(),
                        "channel": channel_name,
                        "source": channel_name,
                        "source_url": "https://www.youtube.com",
                        "link": link,
                        "video_id": video_id,
                        "thumbnail": thumbnail,
                        "description": description,
                        "views": views_str,
                        "published": published[:10] if published else "최근"
                    })
        except Exception as e:
            print(f"[TechAICollector] YouTube feed error ({channel_name}): {e}")
        return videos

    def _fetch_korean_youtube_search(self, query: str = "인공지능 AI 반도체 신기술 뉴스", max_items: int = 6) -> List[Dict[str, Any]]:
        """최신 AI/테크 유튜브 영상을 실제 썸네일 및 조회수와 함께 수집합니다."""
        videos = []
        try:
            url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query) + "&sp=CAI%253D"
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                if "var ytInitialData = " in html:
                    raw = html.split("var ytInitialData = ", 1)[1].split(";</script>", 1)[0]
                    data = json.loads(raw)
                    sections = (
                        data.get("contents", {})
                        .get("twoColumnSearchResultsRenderer", {})
                        .get("primaryContents", {})
                        .get("sectionListRenderer", {})
                        .get("contents", [])
                    )
                    for sec in sections:
                        for c in sec.get("itemSectionRenderer", {}).get("contents", []):
                            vr = c.get("videoRenderer")
                            if not vr:
                                continue
                            vid = vr.get("videoId", "")
                            if not vid:
                                continue
                            title = "".join(r.get("text", "") for r in vr.get("title", {}).get("runs", [])).strip()
                            channel = "".join(r.get("text", "") for r in vr.get("ownerText", {}).get("runs", [])).strip() or "YouTube"
                            pub = vr.get("publishedTimeText", {}).get("simpleText", "최근")
                            views = vr.get("viewCountText", {}).get("simpleText", "")
                            snippets = vr.get("detailedMetadataSnippets", [])
                            desc = ""
                            if snippets:
                                desc = "".join(r.get("text", "") for r in snippets[0].get("snippetText", {}).get("runs", [])).strip()
                            videos.append({
                                "title": title,
                                "channel": channel,
                                "source": channel,
                                "source_url": "https://www.youtube.com",
                                "link": f"https://www.youtube.com/watch?v={vid}",
                                "video_id": vid,
                                "thumbnail": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                                "description": desc,
                                "views": views,
                                "published": pub
                            })
                            if len(videos) >= max_items:
                                return videos
        except Exception as e:
            print(f"[TechAICollector] Korean YouTube search error ({e})")
        return videos

    def _fetch_arxiv_papers(self) -> List[Dict[str, Any]]:
        """ArXiv API에서 최신 논문 30편을 검색한 후, 이전 브리핑 중복을 배제하고 카테고리별로 균형있게 선별합니다."""
        query_cats = "cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CL+OR+cat:cs.CV+OR+cat:cs.RO"
        url = f"https://export.arxiv.org/api/query?search_query={query_cats}&sortBy=submittedDate&sortOrder=descending&max_results=30"

        candidates = []
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=20) as resp:
                tree = ET.fromstring(resp.read())
                ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}
                for entry in tree.findall('atom:entry', ns):
                    title = (entry.findtext('atom:title', namespaces=ns) or "").replace('\n', ' ').strip()
                    title = re.sub(r"\s+", " ", title)
                    summary = (entry.findtext('atom:summary', namespaces=ns) or "").replace('\n', ' ').strip()
                    summary = re.sub(r"\s+", " ", summary)

                    pdf_link = ""
                    abs_link = ""
                    for link_el in entry.findall('atom:link', ns):
                        if link_el.attrib.get('title') == 'pdf':
                            pdf_link = link_el.attrib.get('href', '')
                        elif link_el.attrib.get('rel') == 'alternate':
                            abs_link = link_el.attrib.get('href', '')
                    if not abs_link:
                        abs_link = entry.findtext('atom:id', namespaces=ns) or ""
                    link = pdf_link or abs_link

                    authors = []
                    for author in entry.findall('atom:author', ns):
                        name = author.findtext('atom:name', namespaces=ns)
                        if name:
                            authors.append(name.strip())
                    author_str = (authors[0] + (" et al." if len(authors) > 1 else "")) if authors else "ArXiv"

                    prim_cat_el = entry.find('arxiv:primary_category', ns)
                    primary_category = prim_cat_el.attrib.get('term', 'cs.AI') if prim_cat_el is not None else "cs.AI"
                    comment = entry.findtext('arxiv:comment', namespaces=ns) or ""
                    published = (entry.findtext('atom:published', namespaces=ns) or "")[:10]

                    candidates.append({
                        "title": title,
                        "source": f"ArXiv ({author_str})",
                        "source_url": "https://arxiv.org",
                        "link": link,
                        "abs_link": abs_link,
                        "pdf_link": pdf_link,
                        "summary": summary,
                        "primary_category": primary_category,
                        "comment": comment,
                        "pub_date": published
                    })
        except Exception as e:
            print(f"[TechAICollector] ArXiv API error: {e}")

        # Fallback to RSS if API fails
        if not candidates:
            try:
                rss_req = urllib.request.Request("https://rss.arxiv.org/rss/cs.AI", headers=self.headers)
                with urllib.request.urlopen(rss_req, timeout=15) as resp:
                    tree = ET.fromstring(resp.read())
                    dc_ns = "{http://purl.org/dc/elements/1.1/}"
                    for item in tree.findall(".//item")[:10]:
                        title = (item.findtext("title") or "").replace("\n", " ").strip()
                        link = (item.findtext("link") or "").strip()
                        desc = re.sub(r"<[^>]+>", "", (item.findtext("description") or "").replace("\n", " ").strip())
                        if "Abstract:" in desc:
                            desc = desc.split("Abstract:", 1)[1].strip()
                        creator = (item.findtext(f"{dc_ns}creator") or "ArXiv").strip()
                        first_author = creator.split(",")[0].strip()
                        author_str = f"{first_author} et al." if "," in creator else first_author
                        pdf_link = link.replace("/abs/", "/pdf/") if "/abs/" in link else link
                        candidates.append({
                            "title": title,
                            "source": f"ArXiv ({author_str})",
                            "source_url": "https://arxiv.org",
                            "link": pdf_link,
                            "abs_link": link,
                            "pdf_link": pdf_link,
                            "summary": desc,
                            "primary_category": "cs.AI",
                            "comment": "ArXiv CS.AI",
                            "pub_date": datetime.now().strftime("%Y-%m-%d")
                        })
            except Exception as e_rss:
                print(f"[TechAICollector] ArXiv RSS error: {e_rss}")

        # 중복 제거 및 하위 분야(AI, LG, CL, CV, RO) 다양성 확보
        selected = []
        seen_cats = set()
        for p in candidates:
            if self.history_filter.is_duplicate(p):
                continue
            cat = p.get("primary_category", "cs.AI")
            # 각 카테고리당 최대 2건 선정하여 다양성 확보
            if list(p.get("primary_category") for p in selected).count(cat) >= 2:
                continue
            selected.append(p)
            seen_cats.add(cat)
            if len(selected) >= 6:
                return selected

        # 6건 미만인 경우 후보군에서 잔여 보충
        if len(selected) < 6:
            for p in candidates:
                if p not in selected:
                    selected.append(p)
                    if len(selected) >= 6:
                        break

        return selected[:6]

    def collect_all(self) -> Dict[str, Any]:
        """AI 헤드라인, 빅테크/반도체, ArXiv 논문, 유튜브, AI 툴/기법을 종합 수집합니다."""
        date_str = datetime.now().strftime("%Y-%m-%d")

        # 1. AI 서브토픽 쿼리군 (when:2d)
        ai_queries = [
            '("오픈AI" OR "제미나이" OR "클로드" OR "딥시크" OR "거대언어모델") when:2d',
            '("AI 에이전트" OR "생성형 AI" OR "멀티모달" OR "휴머노이드" OR "피지컬 AI") when:2d',
            '("머신러닝" OR "오픈소스 AI" OR "AI 추론" OR "신경망") when:2d'
        ]

        # 2. 테크/반도체 서브토픽 쿼리군 (when:2d)
        tech_queries = [
            '("HBM" OR "AI 반도체" OR "엔비디아" OR "TSMC" OR "파운드리") when:2d',
            '("삼성전자 반도체" OR "SK하이닉스" OR "브로드컴" OR "AMD") when:2d',
            '("클라우드" OR "AI 데이터센터" OR "빅테크" OR "사이버보안") when:2d'
        ]

        def fetch_multi_subqueries(queries: List[str]) -> List[Dict[str, Any]]:
            combined = []
            for q in queries:
                url = f"https://news.google.com/rss/search?q={urllib.parse.quote(q)}&hl=ko&gl=KR&ceid=KR:ko"
                items = self._fetch_rss(url)
                combined.extend(items)
            # 만약 2d 필터로 수집된 기사가 부족하면 when:7d 쿼리로 완화 검색
            if len(combined) < 10:
                relaxed_q = queries[0].replace("when:2d", "when:7d")
                url_rel = f"https://news.google.com/rss/search?q={urllib.parse.quote(relaxed_q)}&hl=ko&gl=KR&ceid=KR:ko"
                combined.extend(self._fetch_rss(url_rel))
            return combined

        with ThreadPoolExecutor(max_workers=8) as ex:
            f_ai = ex.submit(fetch_multi_subqueries, ai_queries)
            f_tech = ex.submit(fetch_multi_subqueries, tech_queries)
            f_arxiv = ex.submit(self._fetch_arxiv_papers)
            f_yt_tm = ex.submit(self._fetch_youtube_channel_feed, "UCbfYPyITQ-7l4upoX8nvctg", "Two Minute Papers")
            f_yt_yk = ex.submit(self._fetch_youtube_channel_feed, "UCZHmQk67mSJgfCCTn7xBfew", "Yannic Kilcher")
            f_yt_ai = ex.submit(self._fetch_youtube_channel_feed, "UCNJ1Ymd5yFuUPtn21xtRbbw", "AI Explained")
            f_yt_fs = ex.submit(self._fetch_youtube_channel_feed, "UCsBjURrPoezykLs9EqgamOA", "Fireship")
            f_yt_kr = ex.submit(self._fetch_korean_youtube_search, "AI 에이전트 신기술 LLM 딥러닝", 6)

            ai_raw = f_ai.result()
            tech_raw = f_tech.result()
            arxiv_papers = f_arxiv.result()
            yt_tm = f_yt_tm.result()
            yt_yk = f_yt_yk.result()
            yt_ai = f_yt_ai.result()
            yt_fs = f_yt_fs.result()
            yt_kr = f_yt_kr.result()

        # 기사 필터링 (최신순 + 중복제거 + 언론사 다양화)
        ai_news = self._filter_and_cap_items(ai_raw, target_count=6, max_per_source=2)
        tech_news = self._filter_and_cap_items(tech_raw, target_count=6, max_per_source=2)

        # 유튜브 채널 다양화 및 중복 필터링
        yt_candidates = []
        for v in yt_tm[:2]:
            yt_candidates.append(v)
        for v in yt_yk[:2]:
            yt_candidates.append(v)
        for v in yt_ai[:2]:
            yt_candidates.append(v)
        for v in yt_fs[:2]:
            yt_candidates.append(v)
        for v in yt_kr[:4]:
            yt_candidates.append(v)

        yt_selected = []
        yt_channel_counts = {}
        for v in yt_candidates:
            if self.history_filter.is_duplicate(v):
                continue
            ch = v.get("channel", "YouTube")
            if yt_channel_counts.get(ch, 0) >= 2:
                continue
            yt_selected.append(v)
            yt_channel_counts[ch] = yt_channel_counts.get(ch, 0) + 1
            if len(yt_selected) >= 6:
                break

        if len(yt_selected) < 6:
            for v in yt_candidates:
                if v not in yt_selected:
                    yt_selected.append(v)
                    if len(yt_selected) >= 6:
                        break

        # 최신 AI/ML 툴 및 기법 6선 추출 (날짜 기반 순환 + 중복 배제)
        ai_tools = get_daily_tools_and_methods(date_str, history_filter=self.history_filter, count=6)

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "ai_headlines": ai_news[:6],
            "tech_headlines": tech_news[:6],
            "youtube_picks": yt_selected[:6],
            "arxiv_papers": arxiv_papers[:6],
            "ai_tools": ai_tools[:6]
        }
