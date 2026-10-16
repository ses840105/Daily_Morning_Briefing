import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any
from datetime import datetime


class TechAICollector:
    """
    최신 ML, AI, IT 기술 동향 및 YouTube 테크 영상, ArXiv 논문 수집기
    (Google News Style & Card News 메타데이터 지원)
    """
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
        }

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
        items = []
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                xml_data = resp.read()
                tree = ET.fromstring(xml_data)
                for item in tree.findall('.//item')[:10]:
                    title = item.find('title').text if item.find('title') is not None else ""
                    link = item.find('link').text if item.find('link') is not None else ""
                    pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                    desc_el = item.find('description')
                    desc_html = desc_el.text if (desc_el is not None and desc_el.text) else ""

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
                    related = self._parse_related_from_desc(desc_html, title_clean)

                    items.append({
                        "title": title_clean,
                        "source": source.strip(),
                        "source_url": source_url.strip(),
                        "link": link.strip(),
                        "pub_date": pub_date.strip(),
                        "related_articles": related
                    })
        except Exception as e:
            print(f"[TechAICollector] RSS fetch error ({url[:40]}...): {e}")
        return items

    def _fetch_youtube_channel_feed(self, channel_id: str, channel_name: str) -> List[Dict[str, Any]]:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        videos = []
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                tree = ET.fromstring(resp.read())
                ns = {
                    'atom': 'http://www.w3.org/2005/Atom',
                    'yt': 'http://www.youtube.com/xml/schemas/2015',
                    'media': 'http://search.yahoo.com/mrss/'
                }
                for entry in tree.findall('atom:entry', ns)[:5]:
                    title = entry.find('atom:title', ns).text if entry.find('atom:title', ns) is not None else ""
                    link_el = entry.find('atom:link', ns)
                    link = link_el.attrib.get('href', '') if link_el is not None else ""
                    published = entry.find('atom:published', ns).text if entry.find('atom:published', ns) is not None else ""
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
                        "published": published[:10] if published else ""
                    })
        except Exception as e:
            print(f"[TechAICollector] YouTube feed error ({channel_name}): {e}")
        return videos

    def _fetch_korean_youtube_search(self, query: str = "인공지능 AI 반도체 신기술 뉴스") -> List[Dict[str, Any]]:
        """한국어 최신 AI/테크 유튜브 영상을 실제 썸네일 및 조회수와 함께 수집합니다."""
        videos = []
        try:
            url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query) + "&sp=CAI%253D"
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
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
                            if len(videos) >= 4:
                                return videos
        except Exception as e:
            print(f"[TechAICollector] Korean YouTube search fallback ({e})")
        return videos

    def _fetch_arxiv_papers(self) -> List[Dict[str, Any]]:
        url = 'https://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CL&sortBy=submittedDate&sortOrder=descending&max_results=6'
        papers = []
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                tree = ET.fromstring(resp.read())
                ns = {
                    'atom': 'http://www.w3.org/2005/Atom',
                    'arxiv': 'http://arxiv.org/schemas/atom'
                }
                for entry in tree.findall('atom:entry', ns):
                    title_el = entry.find('atom:title', ns)
                    title = title_el.text.replace('\n', ' ').strip() if (title_el is not None and title_el.text) else ""
                    title = re.sub(r"\s+", " ", title)

                    summary_el = entry.find('atom:summary', ns)
                    summary = summary_el.text.replace('\n', ' ').strip() if (summary_el is not None and summary_el.text) else ""
                    summary = re.sub(r"\s+", " ", summary)

                    # Find main PDF or abs link
                    pdf_link = ""
                    abs_link = ""
                    for link_el in entry.findall('atom:link', ns):
                        if link_el.attrib.get('title') == 'pdf':
                            pdf_link = link_el.attrib.get('href', '')
                        elif link_el.attrib.get('rel') == 'alternate':
                            abs_link = link_el.attrib.get('href', '')
                    if not abs_link:
                        id_el = entry.find('atom:id', ns)
                        abs_link = id_el.text.strip() if (id_el is not None and id_el.text) else ""
                    link = pdf_link or abs_link

                    authors = []
                    for author in entry.findall('atom:author', ns):
                        name = author.find('atom:name', ns)
                        if name is not None and name.text:
                            authors.append(name.text.strip())
                    author_str = (authors[0] + (" et al." if len(authors) > 1 else "")) if authors else "ArXiv"

                    prim_cat_el = entry.find('arxiv:primary_category', ns)
                    primary_category = prim_cat_el.attrib.get('term', 'cs.AI') if prim_cat_el is not None else "cs.AI"

                    comment_el = entry.find('arxiv:comment', ns)
                    comment = comment_el.text.strip() if (comment_el is not None and comment_el.text) else ""

                    pub_el = entry.find('atom:published', ns)
                    published = pub_el.text[:10] if (pub_el is not None and pub_el.text) else ""

                    papers.append({
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
            print(f"[TechAICollector] ArXiv feed error: {e}")
        return papers

    def collect_all(self) -> Dict[str, Any]:
        q_ai = urllib.parse.quote("인공지능 LLM 머신러닝 오픈AI")
        q_tech = urllib.parse.quote("반도체 빅테크 클라우드 엔비디아")

        with ThreadPoolExecutor(max_workers=6) as ex:
            f_ai = ex.submit(self._fetch_rss, f"https://news.google.com/rss/search?q={q_ai}&hl=ko&gl=KR&ceid=KR:ko")
            f_tech = ex.submit(self._fetch_rss, f"https://news.google.com/rss/search?q={q_tech}&hl=ko&gl=KR&ceid=KR:ko")
            f_yt_tm = ex.submit(self._fetch_youtube_channel_feed, "UCbfYPyITQ-7l4upoX8nvctg", "Two Minute Papers")
            f_yt_yk = ex.submit(self._fetch_youtube_channel_feed, "UCZHmQk67mSJgfCCTn7xBfew", "Yannic Kilcher")
            f_yt_kr = ex.submit(self._fetch_korean_youtube_search, "인공지능 AI 반도체 신기술 뉴스")
            f_arxiv = ex.submit(self._fetch_arxiv_papers)

            ai_news = f_ai.result()
            tech_news = f_tech.result()
            yt_twominute = f_yt_tm.result()
            yt_yannic = f_yt_yk.result()
            yt_korea_direct = f_yt_kr.result()
            arxiv_papers = f_arxiv.result()

        yt_combined = []
        for v in yt_twominute[:2]:
            yt_combined.append(v)
        for v in yt_yannic[:2]:
            yt_combined.append(v)

        if yt_korea_direct:
            for v in yt_korea_direct[:2]:
                yt_combined.append(v)
        else:
            q_yt = urllib.parse.quote("site:youtube.com AI 인공지능 신기술")
            yt_korea_rss = self._fetch_rss(f"https://news.google.com/rss/search?q={q_yt}&hl=ko&gl=KR&ceid=KR:ko")
            for v in yt_korea_rss[:2]:
                yt_combined.append({
                    "title": v["title"],
                    "channel": v["source"],
                    "source": v["source"],
                    "source_url": "https://www.youtube.com",
                    "link": v["link"],
                    "published": "최근"
                })

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "ai_headlines": ai_news[:6],
            "tech_headlines": tech_news[:6],
            "youtube_picks": yt_combined[:6],
            "arxiv_papers": arxiv_papers[:6]
        }
