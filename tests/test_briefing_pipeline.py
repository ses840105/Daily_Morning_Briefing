#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit and Integration Tests for Daily Morning Briefing
"""

import os
import sys
import unittest
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.voice.tts_engine import TTSEngine
from src.generators.voice_script_builder import VoiceScriptBuilder, _clean_headline_for_speech
from src.generators.affirmations import get_daily_affirmation
from src.generators.card_news_enricher import enrich_section_items
from src.collectors.stock_heatmap_collector import StockHeatmapCollector
from src.generators.paper_builder import PaperBuilder


class TestTTSNormalization(unittest.TestCase):
    def test_clean_headline_speech(self):
        title = "[단독] 美 연준(Fed) 기준금리 4.0% 동결… 나토(NATO)와 협력 강화"
        cleaned = _clean_headline_for_speech(title)
        self.assertNotIn("[단독]", cleaned)
        self.assertNotIn("…", cleaned)

    def test_normalize_for_speech_korean(self):
        text = "[속보] ArXiv 인공지능 논문 및 S&P 500 지수 1,360~1,380원 환율… HBM3E 공급"
        norm = TTSEngine.normalize_for_speech(text, lang="ko")
        self.assertNotIn("[속보]", norm)
        self.assertIn("아카이브", norm)
        self.assertIn("에스앤피 500", norm)
        self.assertIn("에이치비엠 쓰리이", norm)
        self.assertIn("에서", norm)


class TestCardNewsEnricher(unittest.TestCase):
    def test_enrich_section_items(self):
        raw_items = [
            {
                "title": "OpenAI releases new frontier model with breakthrough reasoning",
                "link": "https://example.com/openai",
                "source": "TechCrunch",
                "pub_date": "Wed, 21 Oct 2026 09:00:00 GMT"
            }
        ]
        enriched = enrich_section_items(raw_items, "ai")
        self.assertEqual(len(enriched), 1)
        self.assertIn("keywords", enriched[0])
        self.assertIn("summary", enriched[0])
        self.assertEqual(enriched[0]["category_id"], "ai")


class TestDailyAffirmations(unittest.TestCase):
    def test_get_daily_affirmation(self):
        aff = get_daily_affirmation("2026-10-21")
        self.assertIsInstance(aff, str)
        self.assertGreater(len(aff), 5)


class TestArtifactIntegrity(unittest.TestCase):
    def test_today_artifacts_exist(self):
        date_str = datetime.now().strftime("%Y-%m-%d")
        outputs_dir = os.path.join(BASE_DIR, "outputs")
        
        # 1. Root index.html
        root_index = os.path.join(BASE_DIR, "index.html")
        self.assertTrue(os.path.exists(root_index), "index.html must exist")
        self.assertGreater(os.path.getsize(root_index), 10000, "index.html must not be empty")

        # 2. Markdown Briefing
        md_file = os.path.join(outputs_dir, "markdown", f"briefing_{date_str}.md")
        self.assertTrue(os.path.exists(md_file), f"{md_file} must exist")
        self.assertGreater(os.path.getsize(md_file), 1000, "Markdown file must not be empty")

        # 3. HTML Briefing
        html_file = os.path.join(outputs_dir, "html", f"briefing_{date_str}.html")
        self.assertTrue(os.path.exists(html_file), f"{html_file} must exist")
        self.assertGreater(os.path.getsize(html_file), 10000, "HTML file must not be empty")

        # 4. Audio files (Korean, English, Chinese)
        for lang in ["ko", "en", "zh"]:
            m4a_file = os.path.join(outputs_dir, "audio", f"briefing_{date_str}_{lang}.m4a")
            mp3_file = os.path.join(outputs_dir, "audio", f"briefing_{date_str}_{lang}.mp3")
            self.assertTrue(os.path.exists(m4a_file) or os.path.exists(mp3_file), f"Audio for {lang} must exist")


class TestStockHeatmap(unittest.TestCase):
    def test_stock_heatmap_collector(self):
        collector = StockHeatmapCollector()
        data = collector.collect_all()
        self.assertIn("us", data)
        self.assertIn("kr", data)
        self.assertGreaterEqual(len(data["us"]["stocks"]), 20)
        self.assertGreaterEqual(len(data["kr"]["stocks"]), 20)
        self.assertGreaterEqual(len(data["us"]["indices"]), 4)
        self.assertGreaterEqual(len(data["kr"]["indices"]), 3)
        self.assertIn("top_gainer", data["us"]["summary"])
        self.assertIn("top_loser", data["kr"]["summary"])

    def test_heatmap_cards_rendered_in_html(self):
        outputs_dir = os.path.join(BASE_DIR, "outputs")
        builder = PaperBuilder(outputs_dir)
        tech_data = {
            "ai_headlines": [{"title": "AI Breakthrough", "link": "http://example.com/ai", "source": "Tech"}]
        }
        econ_data = {
            "economy_headlines": [{"title": "Econ Headline", "link": "http://example.com/econ", "source": "Finance"}]
        }
        scripts = {"ko": "한국어", "en": "English", "zh": "Chinese"}
        html = builder.build_html(tech_data, econ_data, scripts, "긍정 확언", "2026-10-26")

        self.assertIn('id="section-econ"', html)
        self.assertIn('gn-heatmap-card-grid', html)
        self.assertIn('card-2026-10-26-econ-heatmap-us', html)
        self.assertIn('card-2026-10-26-econ-heatmap-kr', html)
        self.assertIn('미국 S&P 500 · NASDAQ 빅테크 섹터 히트맵', html)
        self.assertIn('한국 KOSPI · KOSDAQ 시가총액 히트맵', html)
        self.assertIn('openHeatmapZoomModal', html)
        self.assertIn('toggleHeatmapColorMode', html)
        self.assertIn('heatmapZoomModal', html)

        # Markdown test
        md = builder.build_markdown(tech_data, econ_data, "긍정 확언", "2026-10-26")
        self.assertIn('### 📊 글로벌 증시 히트맵 & 주요 지표', md)
        self.assertIn('미국 S&P 500 / NASDAQ', md)
        self.assertIn('한국 KOSPI / KOSDAQ', md)


if __name__ == "__main__":
    unittest.main()
