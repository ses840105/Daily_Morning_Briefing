import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any
from datetime import datetime


class WorldEconCollector:
    """
    글로벌 경제, 군사/안보, 세계 정세 뉴스 수집기
    (Google News Style & Card News 메타데이터 지원)
    """
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
        }

    def _parse_related_from_desc(self, desc_html: str, main_title: str) -> List[Dict[str, str]]:
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
            print(f"[WorldEconCollector] RSS error: {e}")
        return items

    def collect_all(self) -> Dict[str, Any]:
        """
        경제, 군사/안보, 세계 외교 뉴스 병렬 수집
        """
        q_econ = urllib.parse.quote("글로벌 경제 금리 환율 연준 주식")
        q_mil = urllib.parse.quote("군사 안보 국방 방산 전쟁")
        q_world = urllib.parse.quote("국제 외교 정세 미중 정상회담")

        with ThreadPoolExecutor(max_workers=3) as ex:
            f_econ = ex.submit(self._fetch_rss, f"https://news.google.com/rss/search?q={q_econ}&hl=ko&gl=KR&ceid=KR:ko")
            f_mil = ex.submit(self._fetch_rss, f"https://news.google.com/rss/search?q={q_mil}&hl=ko&gl=KR&ceid=KR:ko")
            f_world = ex.submit(self._fetch_rss, f"https://news.google.com/rss/search?q={q_world}&hl=ko&gl=KR&ceid=KR:ko")

            econ_news = f_econ.result()
            military_news = f_mil.result()
            world_news = f_world.result()

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "economy_headlines": econ_news[:6],
            "military_headlines": military_news[:6],
            "world_headlines": world_news[:6]
        }
