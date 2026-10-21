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


if __name__ == "__main__":
    unittest.main()
