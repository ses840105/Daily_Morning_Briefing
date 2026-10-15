import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Dict, List, Any
from datetime import datetime

class WorldEconCollector:
    """
    글로벌 경제, 군사/안보, 세계 정세 뉴스 수집기
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
            print(f"[WorldEconCollector] RSS error: {e}")
        return items

    def collect_all(self) -> Dict[str, Any]:
        """
        경제, 군사/안보, 세계 외교 뉴스 수집
        """
        # 1. 글로벌 경제, 금융, 금리, 환율
        q_econ = urllib.parse.quote("글로벌 경제 금리 환율 연준 주식")
        econ_news = self._fetch_rss(f"https://news.google.com/rss/search?q={q_econ}&hl=ko&gl=KR&ceid=KR:ko")

        # 2. 군사, 국방, 안보, 방산, 지정학적 충돌
        q_mil = urllib.parse.quote("군사 안보 국방 방산 전쟁")
        military_news = self._fetch_rss(f"https://news.google.com/rss/search?q={q_mil}&hl=ko&gl=KR&ceid=KR:ko")

        # 3. 국제 외교 및 세계 정세 (미국, 중국, 유럽, 중동)
        q_world = urllib.parse.quote("국제 외교 정세 미중 정상회담")
        world_news = self._fetch_rss(f"https://news.google.com/rss/search?q={q_world}&hl=ko&gl=KR&ceid=KR:ko")

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "economy_headlines": econ_news[:6],
            "military_headlines": military_news[:6],
            "world_headlines": world_news[:6]
        }
