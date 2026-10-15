import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import re
from typing import Dict, List, Any
from datetime import datetime

class TechAICollector:
    """
    최신 ML, AI, IT 기술 동향 및 YouTube 테크 영상, ArXiv 논문 수집기
    """
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}

    def _fetch_rss(self, url: str) -> List[Dict[str, str]]:
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
                    source = item.find('source').text if item.find('source') is not None else "Google News"
                    
                    # 제목 정제 (언론사 태그 분리)
                    title_clean = title
                    if " - " in title:
                        parts = title.rsplit(" - ", 1)
                        title_clean = parts[0]
                        source = parts[1]

                    items.append({
                        "title": title_clean.strip(),
                        "source": source.strip(),
                        "link": link.strip(),
                        "pub_date": pub_date.strip()
                    })
        except Exception as e:
            print(f"[TechAICollector] RSS fetch error ({url[:40]}...): {e}")
        return items

    def _fetch_youtube_channel_feed(self, channel_id: str, channel_name: str) -> List[Dict[str, str]]:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        videos = []
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                tree = ET.fromstring(resp.read())
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                for entry in tree.findall('atom:entry', ns)[:5]:
                    title = entry.find('atom:title', ns).text if entry.find('atom:title', ns) is not None else ""
                    link_el = entry.find('atom:link', ns)
                    link = link_el.attrib.get('href', '') if link_el is not None else ""
                    published = entry.find('atom:published', ns).text if entry.find('atom:published', ns) is not None else ""
                    videos.append({
                        "title": title.strip(),
                        "channel": channel_name,
                        "link": link,
                        "published": published[:10] if published else ""
                    })
        except Exception as e:
            print(f"[TechAICollector] YouTube feed error ({channel_name}): {e}")
        return videos

    def _fetch_arxiv_papers(self) -> List[Dict[str, str]]:
        url = 'http://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CL&sortBy=submittedDate&sortOrder=desc&max_results=5'
        papers = []
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                tree = ET.fromstring(resp.read())
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                for entry in tree.findall('atom:entry', ns):
                    title = entry.find('atom:title', ns).text
                    if title:
                        title = title.replace('\n', ' ').strip()
                        
                    # Find main PDF or abs link
                    link = ""
                    for link_el in entry.findall('atom:link', ns):
                        if link_el.attrib.get('title') == 'pdf':
                            link = link_el.attrib.get('href', '')
                            break
                    if not link:
                        link_el = entry.find('atom:id', ns)
                        link = link_el.text if link_el is not None else ""

                    authors = []
                    for author in entry.findall('atom:author', ns):
                        name = author.find('atom:name', ns)
                        if name is not None and name.text:
                            authors.append(name.text)
                    author_str = authors[0] + (" et al." if len(authors) > 1 else "")
                    
                    published = entry.find('atom:published', ns).text
                    
                    papers.append({
                        "title": title,
                        "source": f"ArXiv ({author_str})",
                        "link": link,
                        "pub_date": published[:10] if published else ""
                    })
        except Exception as e:
            print(f"[TechAICollector] ArXiv feed error: {e}")
        return papers

    def collect_all(self) -> Dict[str, Any]:
        # 1. 국내외 생성형 AI 및 머신러닝 뉴스
        q_ai = urllib.parse.quote("인공지능 LLM 머신러닝 오픈AI")
        ai_news = self._fetch_rss(f"https://news.google.com/rss/search?q={q_ai}&hl=ko&gl=KR&ceid=KR:ko")

        # 2. 글로벌 빅테크 및 반도체/클라우드 기술 동향
        q_tech = urllib.parse.quote("반도체 빅테크 클라우드 엔비디아")
        tech_news = self._fetch_rss(f"https://news.google.com/rss/search?q={q_tech}&hl=ko&gl=KR&ceid=KR:ko")

        # 3. 유튜브 최신 AI/기술 영상 수집
        yt_twominute = self._fetch_youtube_channel_feed("UCbfYPyITQ-7l4upoX8nvctg", "Two Minute Papers")
        yt_yannic = self._fetch_youtube_channel_feed("UCZHmQk67mSJgfCCTn7xBfew", "Yannic Kilcher")

        q_yt = urllib.parse.quote("site:youtube.com AI 인공지능 신기술")
        yt_korea = self._fetch_rss(f"https://news.google.com/rss/search?q={q_yt}&hl=ko&gl=KR&ceid=KR:ko")

        yt_combined = []
        for v in yt_twominute[:2]: yt_combined.append(v)
        for v in yt_yannic[:2]: yt_combined.append(v)
        for v in yt_korea[:3]:
            yt_combined.append({
                "title": v["title"],
                "channel": v["source"],
                "link": v["link"],
                "published": "최근"
            })

        # 4. 최신 ArXiv 논문 수집
        arxiv_papers = self._fetch_arxiv_papers()

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "ai_headlines": ai_news[:6],
            "tech_headlines": tech_news[:5],
            "youtube_picks": yt_combined[:6],
            "arxiv_papers": arxiv_papers[:5]
        }
