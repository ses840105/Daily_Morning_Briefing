#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Morning Briefing Main Orchestrator
매일 아침 09:00 기준 최신 AI/ML/IT + 경제/군사/세계뉴스 수집 및 5분 분량 다국어 신문/음성 생성기
"""

import os
import sys
import argparse
import subprocess
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.collectors.tech_ai_collector import TechAICollector
from src.collectors.world_econ_collector import WorldEconCollector
from src.generators.paper_builder import PaperBuilder
from src.generators.voice_script_builder import VoiceScriptBuilder
from src.generators.affirmations import get_daily_affirmation
from src.voice.tts_engine import TTSEngine

def main():
    parser = argparse.ArgumentParser(description="Daily Morning Briefing Generator")
    parser.add_argument("--voice", action="store_true", help="생성 완료 후 음성(TTS)으로 브리핑 낭독")
    parser.add_argument("--open-html", action="store_true", help="생성된 신문 HTML을 브라우저로 열기")
    parser.add_argument("--print", action="store_true", help="터미널에 마크다운 신문 전문 출력")
    args = parser.parse_args()

    date_str = datetime.now().strftime("%Y-%m-%d")
    print("=" * 70)
    print(f"📰 [Daily Morning Briefing] {date_str} 09:00 다국어 에디션 발행 시작")
    print("=" * 70)

    # 1. 수집 단계
    print("[1/4] 🤖 AI, ML, IT 기술 동향 및 YouTube 테크 영상 수집 중...")
    tech_collector = TechAICollector()
    tech_data = tech_collector.collect_all()

    print("[2/4] 🌐 글로벌 경제, 군사/안보, 세계 정세 뉴스 수집 중...")
    econ_collector = WorldEconCollector()
    econ_data = econ_collector.collect_all()

    # 오늘의 긍정 확언 추출
    daily_affirmation = get_daily_affirmation(date_str)

    # 3. 다국어 대본 생성
    print("[3/4] 🎙️ 5분 분량 다국어(한국어, 영어, 중국어) 음성 브리핑 대본 생성 및 번역 중...")
    script_builder = VoiceScriptBuilder()
    scripts = script_builder.build_scripts(tech_data, econ_data, daily_affirmation, date_str)
    
    outputs_dir = os.path.join(BASE_DIR, "outputs")
    scripts_dir = os.path.join(outputs_dir, "scripts")
    os.makedirs(scripts_dir, exist_ok=True)
    
    for lang, text in scripts.items():
        script_path = os.path.join(scripts_dir, f"script_{date_str}_{lang}.txt")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(text)

    # 4. 오디오 생성 (m4a 확장자로 변경하여 웹 브라우저 호환성 확보)
    print("[+] 🎧 다국어 TTS 음성 파일 생성 중 (Korean, English, Chinese)...")
    audio_dir = os.path.join(outputs_dir, "audio")
    os.makedirs(audio_dir, exist_ok=True)
    
    voices = {"ko": "ko", "en": "en", "zh": "zh-CN"}
    audio_paths = {}
    for lang, text in scripts.items():
        a_path = os.path.join(audio_dir, f"briefing_{date_str}_{lang}.m4a")
        tts = TTSEngine(voice=voices[lang], rate=185 if lang == "ko" else 170)
        tts.save_audio(text, a_path)
        audio_paths[lang] = a_path

    latest_audio = os.path.join(audio_dir, "latest_briefing_ko.m4a")
    if os.path.exists(audio_paths["ko"]):
        subprocess.run(["cp", audio_paths["ko"], latest_audio], check=False)

    # 5. 신문 생성 단계 (MD & HTML) - 오디오 생성 후 실행 (HTML에서 오디오 경로를 참조하기 때문)
    print("[4/4] 📄 상세 뉴스 링크가 포함된 다국어 웹 신문(HTML) 및 인덱스 렌더링 중...")
    builder = PaperBuilder(outputs_dir)
    md_content = builder.build_markdown(tech_data, econ_data, daily_affirmation, date_str)
    html_content = builder.build_html(tech_data, econ_data, scripts, daily_affirmation, date_str)
    md_path, html_path = builder.save(md_content, html_content, date_str)
    index_path = os.path.join(BASE_DIR, "index.html")

    print("\n" + "=" * 70)
    print("✨ [발행 완료] 다국어 5분 모닝 브리핑 신문 및 음성이 성공적으로 생성되었습니다!")
    print(f"  • 인덱스 페이지 : {index_path}")
    print(f"  • 오늘 웹 신문  : {html_path}")
    print(f"  • 한국어 오디오 : {audio_paths.get('ko')}")
    print("=" * 70)

    # macOS 시스템 알림
    top_ai = tech_data.get("ai_headlines", [{}])[0].get("title", "")
    notif_msg = f"오늘의 AI: {top_ai[:30]}..." if top_ai else "다국어 5분 종합 신문 발행 완료"
    script = f'display notification "{notif_msg}" with title "📰 Daily Morning Briefing" subtitle "{date_str} 09:00 신문 도착"'
    subprocess.Popen(["osascript", "-e", script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if args.print:
        print("\n" + md_content + "\n")
    if args.open_html:
        subprocess.Popen(["open", index_path])
    if args.voice:
        print("\n🔊 [Voice Briefing] 한국어 아나운서 음성 브리핑을 재생합니다...\n")
        tts_ko = TTSEngine(voice="ko", rate=185)
        tts_ko.speak(scripts["ko"], background=False)

if __name__ == "__main__":
    main()
