import os
import glob
from datetime import datetime
from typing import Dict, Any, List

class PaperBuilder:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.root_dir = os.path.dirname(self.output_dir) # root directory (Daily_Morning_Briefing)
        self.html_dir = os.path.join(self.output_dir, "html")
        self.md_dir = os.path.join(self.output_dir, "markdown")
        os.makedirs(self.html_dir, exist_ok=True)
        os.makedirs(self.md_dir, exist_ok=True)

    def build_markdown(self, tech_data: Dict[str, Any], econ_data: Dict[str, Any], affirmation: str, date_str: str) -> str:
        md = []
        md.append(f"# 📰 DAILY MORNING BRIEFING | 데일리 모닝 인텔리전스")
        md.append(f"> **발행 일시**: {date_str} 09:00 KST | **에디션**: 제{datetime.now().strftime('%Y%m%d')}호 | **총 3페이지 특집**\n")
        md.append("=" * 80)
        
        md.append("\n## 📄 [PAGE 1] 🤖 최신 ML · AI · IT 테크 동향 & 유튜브 인사이트\n")
        md.append("### 🧠 1. 인공지능 & 머신러닝 (AI & Frontier LLM)")
        for idx, item in enumerate(tech_data.get("ai_headlines", [])[:5], 1):
            md.append(f"{idx}. **[{item['source']}]** [{item['title']}]({item['link']})")
        
        md.append("\n### 📺 2. 유튜브 추천 테크 영상 (YouTube Tech Picks)")
        for idx, item in enumerate(tech_data.get("youtube_picks", [])[:5], 1):
            md.append(f"• **[{item.get('channel', 'YouTube')}]** [{item['title']}]({item['link']})")

        md.append("\n### 📚 3. 최신 AI/ML 논문 (ArXiv Papers)")
        for idx, item in enumerate(tech_data.get("arxiv_papers", [])[:4], 1):
            md.append(f"• **[{item['source']}]** [{item['title']}]({item['link']})")
            
        md.append("\n### 💻 4. 빅테크 · 반도체 & 엔지니어링 기술 동향")
        for idx, item in enumerate(tech_data.get("tech_headlines", [])[:4], 1):
            md.append(f"- **{item['title']}** ({item['source']})")

        md.append("\n" + "-" * 80)

        md.append("\n## 📄 [PAGE 2] 🌐 글로벌 경제 · 군사/안보 · 세계 정세\n")
        md.append("### 📈 1. 글로벌 거시 경제 & 금융 지표 (Macro Economy & Markets)")
        for idx, item in enumerate(econ_data.get("economy_headlines", [])[:5], 1):
            md.append(f"{idx}. **[{item['source']}]** [{item['title']}]({item['link']})")

        md.append("\n### 🛡️ 2. 군사 · 국방 안보 & 지정학 이슈 (Military & Defense Intelligence)")
        for idx, item in enumerate(econ_data.get("military_headlines", [])[:5], 1):
            md.append(f"• **[{item['source']}]** [{item['title']}]({item['link']})")

        md.append("\n### 🌍 3. 국제 외교 & 글로벌 정세 (World Diplomacy)")
        for idx, item in enumerate(econ_data.get("world_headlines", [])[:4], 1):
            md.append(f"- **{item['title']}** ({item['source']})")

        md.append("\n" + "-" * 80)
        md.append("\n## 📄 [PAGE 3] 💡 오늘의 인사이트 & 1분 초압축 총괄 브리핑\n")
        
        top_ai = tech_data.get("ai_headlines", [{}])[0].get("title", "AI 기술 진화 가속")
        top_econ = econ_data.get("economy_headlines", [{}])[0].get("title", "글로벌 매크로 불확실성 지속")
        top_mil = econ_data.get("military_headlines", [{}])[0].get("title", "지정학적 안보 긴장 고조")
        
        md.append("### ⚡ 오늘 아침 꼭 알아야 할 3대 헤드라인")
        md.append(f"1. **AI/기술**: {top_ai}")
        md.append(f"2. **경제/금융**: {top_econ}")
        md.append(f"3. **안보/세계**: {top_mil}")

        md.append("\n### 🎯 오늘 하루 관전 포인트 (Today's Watchpoints)")
        md.append("- **엔지니어링/AI**: 신규 AI 모델 성능 공개 여부 및 반도체 공급망 현황 지속 모니터링")
        md.append("- **경제/투자**: 원달러 환율 단기 변동성 및 주요국 중앙은행 기준금리 관련 발언 주시")
        md.append("- **안보/지정학**: 우크라이나/중동 군사 움직임 및 글로벌 무역 규제 동향 주의")
        
        md.append("\n" + "=" * 80)
        md.append("\n## 🌅 [SPECIAL] 아침 긍정 명상 & 확언\n")
        md.append(f"> **\"{affirmation}\"**")
        md.append("\n*이 문장을 마음속으로 3번 되뇌어 보세요. 당신의 하루가 긍정적인 에너지로 가득 찰 것입니다.*\n")
        
        return "\n".join(md)

    def build_html(self, tech_data: Dict[str, Any], econ_data: Dict[str, Any], scripts: Dict[str, str], affirmation: str, date_str: str) -> str:
        def make_items_html(items, type_flag="news"):
            html = ""
            for it in items:
                title = it.get('title', '')
                link = it.get('link', '#')
                
                if type_flag == "youtube":
                    source = it.get('channel', 'YouTube')
                    badge_class = "badge-yt"
                    btn_text = "유튜브 시청 &rarr;"
                elif type_flag == "paper":
                    source = it.get('source', 'ArXiv')
                    badge_class = "badge-paper"
                    btn_text = "논문(PDF) 보기 &rarr;"
                else:
                    source = it.get('source', 'News')
                    badge_class = "badge-news"
                    btn_text = "기사 읽기 &rarr;"
                    
                html += f"""
                <div class="news-item">
                    <span class="source-badge {badge_class}">{source}</span>
                    <a href="{link}" target="_blank" class="news-link">{title}</a>
                    <a href="{link}" target="_blank" class="detail-btn">{btn_text}</a>
                </div>
                """
            return html

        ai_items_html = make_items_html(tech_data.get("ai_headlines", [])[:6], "news")
        yt_items_html = make_items_html(tech_data.get("youtube_picks", [])[:5], "youtube")
        paper_items_html = make_items_html(tech_data.get("arxiv_papers", [])[:5], "paper")
        tech_items_html = make_items_html(tech_data.get("tech_headlines", [])[:5], "news")
        
        econ_items_html = make_items_html(econ_data.get("economy_headlines", [])[:6], "news")
        mil_items_html = make_items_html(econ_data.get("military_headlines", [])[:5], "news")
        world_items_html = make_items_html(econ_data.get("world_headlines", [])[:5], "news")

        ko_script_html = scripts.get('ko', '').replace('\n', '<br><br>')
        en_script_html = scripts.get('en', '').replace('\n', '<br><br>')
        zh_script_html = scripts.get('zh', '').replace('\n', '<br><br>')

        # AUDIO_BASE_PATH and ARCHIVE_LINK_PATH placeholders will be replaced in save()
        html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Morning Briefing - {date_str}</title>
    <style>
        :root {{
            --bg-color: #f8fafc; --card-bg: #ffffff; --text-main: #1e293b; --text-sub: #64748b;
            --accent-blue: #2563eb; --border-color: #e2e8f0;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Pretendard", "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg-color); color: var(--text-main); margin: 0; padding: 24px; line-height: 1.6;
        }}
        .container {{ max-width: 1040px; margin: 0 auto; }}
        
        .top-nav {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
        .nav-btn {{
            background: #ffffff; border: 1px solid #cbd5e1; padding: 8px 16px; border-radius: 8px; color: #475569;
            text-decoration: none; font-weight: 600; font-size: 0.95rem; cursor: pointer; transition: all 0.2s;
            display: inline-flex; align-items: center; gap: 6px;
        }}
        .nav-btn:hover {{ background: #f1f5f9; color: var(--accent-blue); }}
        
        .header {{ text-align: center; border-bottom: 4px double #334155; padding-bottom: 20px; margin-bottom: 30px; position: relative; }}
        .header h1 {{ font-size: 2.5rem; margin: 0 0 8px 0; letter-spacing: -1px; color: #0f172a; font-weight: 800; }}
        .header .meta {{ font-size: 1rem; color: var(--text-sub); font-weight: 600; }}
        
        .play-btn {{
            display: inline-flex; align-items: center; gap: 8px; background: var(--accent-blue); color: white; border: none;
            padding: 10px 20px; border-radius: 20px; font-size: 1rem; font-weight: bold; cursor: pointer; margin-top: 15px; transition: background 0.2s;
        }}
        .play-btn:hover {{ background: #1d4ed8; }}

        /* Modern Audio Player Card */
        .audio-player-card {{
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #ffffff;
            border-radius: 16px;
            padding: 20px 26px;
            margin: 20px auto 10px auto;
            max-width: 760px;
            box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.25);
            text-align: left;
            border: 1px solid #334155;
        }}
        .player-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}
        .player-title {{
            font-size: 1.05rem;
            font-weight: 700;
            color: #93c5fd;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .player-badge {{
            background: rgba(59, 130, 246, 0.25);
            border: 1px solid #3b82f6;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
            color: #bfdbfe;
            font-weight: 600;
        }}
        .progress-container {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 14px;
        }}
        .time-text {{
            font-size: 0.85rem;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            color: #94a3b8;
            min-width: 45px;
        }}
        .progress-bar-slider {{
            flex-grow: 1;
            height: 6px;
            border-radius: 3px;
            background: #334155;
            outline: none;
            cursor: pointer;
            -webkit-appearance: none;
        }}
        .progress-bar-slider::-webkit-slider-thumb {{
            -webkit-appearance: none;
            width: 15px;
            height: 15px;
            border-radius: 50%;
            background: #38bdf8;
            cursor: pointer;
            box-shadow: 0 0 8px rgba(56, 189, 248, 0.8);
        }}
        .player-controls {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
        }}
        .controls-main {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .ctrl-btn {{
            background: #334155;
            color: white;
            border: none;
            border-radius: 50%;
            width: 38px;
            height: 38px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 0.95rem;
        }}
        .ctrl-btn:hover {{
            background: #475569;
            transform: scale(1.06);
        }}
        .ctrl-btn-play {{
            background: #2563eb;
            width: 48px;
            height: 48px;
            font-size: 1.25rem;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
        }}
        .ctrl-btn-play:hover {{
            background: #1d4ed8;
        }}
        .controls-extra {{
            display: flex;
            align-items: center;
            gap: 14px;
        }}
        .speed-btn {{
            background: rgba(255, 255, 255, 0.1);
            color: #e2e8f0;
            border: 1px solid rgba(255, 255, 255, 0.2);
            padding: 5px 12px;
            border-radius: 6px;
            font-size: 0.85rem;
            cursor: pointer;
            font-weight: 600;
            transition: background 0.2s;
        }}
        .speed-btn:hover {{
            background: rgba(255, 255, 255, 0.2);
        }}
        .volume-control {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .volume-slider {{
            width: 75px;
            height: 5px;
            -webkit-appearance: none;
            background: #334155;
            border-radius: 3px;
        }}
        .volume-slider::-webkit-slider-thumb {{
            -webkit-appearance: none;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #94a3b8;
            cursor: pointer;
        }}
        .player-status-msg {{
            font-size: 0.82rem;
            color: #94a3b8;
            margin-top: 10px;
            text-align: center;
        }}
        
        .tabs {{ display: flex; gap: 10px; margin-bottom: -1px; position: relative; z-index: 10; }}
        .tab-btn {{
            padding: 12px 24px; background: #f1f5f9; border: 1px solid var(--border-color); border-bottom: none; border-radius: 8px 8px 0 0;
            font-weight: bold; font-size: 1.1rem; cursor: pointer; color: var(--text-sub); transition: all 0.2s;
        }}
        .tab-btn.active {{ background: var(--card-bg); color: var(--accent-blue); border-top: 3px solid var(--accent-blue); }}
        
        .script-container {{
            background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 0 8px 8px 8px; padding: 30px;
            margin-bottom: 40px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); font-size: 1.05rem; line-height: 1.8; color: #334155;
        }}
        .script-content {{ display: none; }}
        .script-content.active {{ display: block; }}

        .page-card {{
            background: var(--card-bg); border-radius: 12px; border: 1px solid var(--border-color);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); padding: 28px; margin-bottom: 28px;
        }}
        
        .affirmation-card {{
            background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
            border: 1px solid #e2e8f0; border-radius: 12px; padding: 40px 20px; text-align: center;
            margin-bottom: 40px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05);
        }}
        .affirmation-title {{ font-size: 1.25rem; font-weight: 700; color: #6366f1; margin-bottom: 20px; }}
        .affirmation-text {{ font-size: 1.8rem; font-weight: 800; color: #1e293b; margin: 0 0 20px 0; line-height: 1.5; word-break: keep-all; }}
        .affirmation-sub {{ color: #64748b; font-size: 1.05rem; margin: 0; }}
        
        .page-header {{ border-bottom: 2px solid #94a3b8; padding-bottom: 12px; margin-bottom: 20px; }}
        .page-header h2 {{ margin: 0; font-size: 1.6rem; color: #0f172a; }}
        .section-title {{
            font-size: 1.25rem; font-weight: 700; margin: 24px 0 16px 0; color: var(--accent-blue);
            display: flex; align-items: center; gap: 8px; border-left: 4px solid var(--accent-blue); padding-left: 10px;
        }}
        .news-item {{ display: flex; align-items: center; gap: 12px; padding: 12px 0; border-bottom: 1px dashed #cbd5e1; }}
        .news-item:last-child {{ border-bottom: none; }}
        
        .source-badge {{ font-size: 0.8rem; font-weight: 700; padding: 4px 10px; border-radius: 6px; white-space: nowrap; }}
        .badge-news {{ background: #e0f2fe; color: #0369a1; }}
        .badge-yt {{ background: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }}
        .badge-paper {{ background: #f3e8ff; color: #7e22ce; border: 1px solid #d8b4fe; }}
        
        .news-link {{ flex-grow: 1; color: #1e293b; text-decoration: none; font-size: 1.05rem; font-weight: 600; }}
        .news-link:hover {{ color: var(--accent-blue); text-decoration: underline; }}
        .detail-btn {{
            font-size: 0.85rem; font-weight: 600; background-color: #f8fafc; border: 1px solid #cbd5e1; padding: 6px 12px;
            border-radius: 6px; color: #475569; text-decoration: none; white-space: nowrap; transition: all 0.2s;
        }}
        .detail-btn:hover {{ background-color: var(--accent-blue); color: white; border-color: var(--accent-blue); }}
        
        .footer {{ text-align: center; color: var(--text-sub); font-size: 0.9rem; margin-top: 50px; padding-top: 20px; border-top: 1px solid var(--border-color); }}
    </style>
    <script>
        let currentLang = 'ko';
        const langNames = {{ ko: '🇰🇷 한국어 (Korean)', en: '🇺🇸 English', zh: '🇨🇳 中文 (Chinese)' }};
        let currentRate = 1.0;

        function getActiveAudio() {{
            return document.getElementById('audio-' + currentLang);
        }}

        function formatTime(seconds) {{
            if (isNaN(seconds) || seconds < 0) return '00:00';
            const m = Math.floor(seconds / 60);
            const s = Math.floor(seconds % 60);
            return (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s;
        }}

        function updatePlayerUI() {{
            const audio = getActiveAudio();
            const playBtn = document.getElementById('playMainBtn');
            const statusBadge = document.getElementById('playerStatusBadge');
            const titleEl = document.getElementById('playerCurrentTitle');
            const timeCur = document.getElementById('timeCurrent');
            const timeDur = document.getElementById('timeDuration');
            const slider = document.getElementById('progressSlider');

            if (titleEl) titleEl.innerText = '🎙️ 5분 브리핑: ' + langNames[currentLang];

            if (audio.paused) {{
                if (playBtn) playBtn.innerHTML = '▶️';
                if (statusBadge) statusBadge.innerText = '준비됨';
            }} else {{
                if (playBtn) playBtn.innerHTML = '⏸️';
                if (statusBadge) statusBadge.innerText = '재생 중...';
            }}

            if (timeCur) timeCur.innerText = formatTime(audio.currentTime);
            if (timeDur && audio.duration) timeDur.innerText = formatTime(audio.duration);

            if (slider && audio.duration) {{
                slider.max = audio.duration;
                slider.value = audio.currentTime;
            }}
        }}

        function togglePlay() {{
            const audio = getActiveAudio();
            const statusMsg = document.getElementById('playerStatusMsg');
            if (audio.paused) {{
                pauseAllAudio();
                audio.playbackRate = currentRate;
                const playPromise = audio.play();
                if (playPromise !== undefined) {{
                    playPromise.then(() => {{
                        updatePlayerUI();
                        if (statusMsg) statusMsg.innerText = '🔊 오디오가 정상적으로 재생되고 있습니다.';
                    }}).catch(err => {{
                        console.error('Audio play error:', err);
                        updatePlayerUI();
                        if (statusMsg) statusMsg.innerText = '⚠️ 브라우저 정책으로 인해 재생이 제한되었습니다. 화면을 클릭 후 다시 시도해주세요.';
                    }});
                }}
            }} else {{
                audio.pause();
                updatePlayerUI();
                if (statusMsg) statusMsg.innerText = '일시정지되었습니다.';
            }}
        }}

        function seekAudio(val) {{
            const audio = getActiveAudio();
            audio.currentTime = parseFloat(val);
            updatePlayerUI();
        }}

        function skipTime(delta) {{
            const audio = getActiveAudio();
            audio.currentTime = Math.max(0, Math.min(audio.duration || 0, audio.currentTime + delta));
            updatePlayerUI();
        }}

        function cycleSpeed() {{
            const speeds = [1.0, 1.25, 1.5, 2.0];
            const nextIdx = (speeds.indexOf(currentRate) + 1) % speeds.length;
            currentRate = speeds[nextIdx];
            const audio = getActiveAudio();
            audio.playbackRate = currentRate;
            document.getElementById('speedBtn').innerText = currentRate + 'x';
        }}

        function setVolume(val) {{
            const audios = document.getElementsByTagName('audio');
            for(let i=0; i<audios.length; i++) {{
                audios[i].volume = parseFloat(val);
            }}
        }}

        function pauseAllAudio() {{
            const audios = document.getElementsByTagName('audio');
            for(let i=0; i<audios.length; i++) {{
                audios[i].pause();
            }}
        }}

        function switchTab(lang) {{
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.script-content').forEach(content => content.classList.remove('active'));
            
            const btn = document.getElementById('btn-' + lang);
            const content = document.getElementById('content-' + lang);
            if (btn) btn.classList.add('active');
            if (content) content.classList.add('active');
            
            pauseAllAudio();
            currentLang = lang;
            updatePlayerUI();
        }}

        document.addEventListener('DOMContentLoaded', () => {{
            const audios = document.getElementsByTagName('audio');
            for(let i=0; i<audios.length; i++) {{
                const a = audios[i];
                a.addEventListener('timeupdate', () => {{
                    if (a === getActiveAudio()) updatePlayerUI();
                }});
                a.addEventListener('loadedmetadata', () => {{
                    if (a === getActiveAudio()) updatePlayerUI();
                }});
                a.addEventListener('ended', () => {{
                    updatePlayerUI();
                    const statusMsg = document.getElementById('playerStatusMsg');
                    if (statusMsg) statusMsg.innerText = '브리핑 재생이 완료되었습니다.';
                }});
                a.addEventListener('error', (e) => {{
                    console.error('Audio element error:', e);
                    const statusMsg = document.getElementById('playerStatusMsg');
                    if (statusMsg) statusMsg.innerText = '오디오 로드 중 오류가 발생했습니다.';
                }});
            }}
            updatePlayerUI();
        }});
    </script>
</head>
<body>
    <div class="container">
        <div class="top-nav">
            <span style="color: #64748b; font-size: 0.95rem; font-weight: 700;">Daily Morning Briefing System</span>
            <a href="ARCHIVE_LINK_PATH" class="nav-btn">🗂️ 지난 신문 보기 (Archive)</a>
        </div>

        <header class="header">
            <h1>📰 The Daily Intelligence Times</h1>
            <div class="meta">발행 일시: {date_str} 09:00 | Global Morning Briefing | Multi-Language Edition</div>
            
            <!-- Dual format sources: MP3 (Standard) + M4A (Apple AAC) for 100% universal browser support -->
            <audio id="audio-ko" preload="metadata">
                <source src="AUDIO_BASE_PATHbriefing_{date_str}_ko.mp3" type="audio/mpeg">
                <source src="AUDIO_BASE_PATHbriefing_{date_str}_ko.m4a" type="audio/mp4">
            </audio>
            <audio id="audio-en" preload="metadata">
                <source src="AUDIO_BASE_PATHbriefing_{date_str}_en.mp3" type="audio/mpeg">
                <source src="AUDIO_BASE_PATHbriefing_{date_str}_en.m4a" type="audio/mp4">
            </audio>
            <audio id="audio-zh" preload="metadata">
                <source src="AUDIO_BASE_PATHbriefing_{date_str}_zh.mp3" type="audio/mpeg">
                <source src="AUDIO_BASE_PATHbriefing_{date_str}_zh.m4a" type="audio/mp4">
            </audio>
            
            <!-- Interactive Modern Audio Player -->
            <div class="audio-player-card">
                <div class="player-header">
                    <div class="player-title" id="playerCurrentTitle">🎙️ 5분 브리핑: 🇰🇷 한국어 (Korean)</div>
                    <div class="player-badge" id="playerStatusBadge">준비됨</div>
                </div>
                <div class="progress-container">
                    <span class="time-text" id="timeCurrent">00:00</span>
                    <input type="range" class="progress-bar-slider" id="progressSlider" min="0" max="100" value="0" oninput="seekAudio(this.value)">
                    <span class="time-text" id="timeDuration">--:--</span>
                </div>
                <div class="player-controls">
                    <div class="controls-main">
                        <button class="ctrl-btn" onclick="skipTime(-10)" title="10초 뒤로">⏪</button>
                        <button class="ctrl-btn ctrl-btn-play" id="playMainBtn" onclick="togglePlay()" title="재생 / 일시정지">▶️</button>
                        <button class="ctrl-btn" onclick="skipTime(10)" title="10초 앞으로">⏩</button>
                    </div>
                    <div class="controls-extra">
                        <button class="speed-btn" id="speedBtn" onclick="cycleSpeed()" title="재생 속도 조절">1.0x</button>
                        <div class="volume-control" title="볼륨 조절">
                            <span style="font-size: 0.85rem;">🔊</span>
                            <input type="range" class="volume-slider" min="0" max="1" step="0.05" value="1" oninput="setVolume(this.value)">
                        </div>
                    </div>
                </div>
                <div class="player-status-msg" id="playerStatusMsg">재생 버튼을 누르면 오늘의 5분 음성 브리핑이 시작됩니다.</div>
            </div>
        </header>

        <!-- AFFIRMATION SECTION -->
        <div class="affirmation-card">
            <div class="affirmation-title">✨ 오늘의 긍정 확언 & 명상 ✨</div>
            <p class="affirmation-text">"{affirmation}"</p>
            <p class="affirmation-sub">이 문장을 눈을 감고 마음속으로 3번 되뇌어 보세요. 긍정적인 에너지가 하루를 바꿀 것입니다.</p>
        </div>

        <div style="margin-bottom: 10px;">
            <h2 style="margin:0 0 15px 0; color:#0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom:10px;">🎙️ 5-Minute Briefing Script</h2>
        </div>
        <div class="tabs">
            <button id="btn-ko" class="tab-btn active" onclick="switchTab('ko')">🇰🇷 한국어</button>
            <button id="btn-en" class="tab-btn" onclick="switchTab('en')">🇺🇸 English</button>
            <button id="btn-zh" class="tab-btn" onclick="switchTab('zh')">🇨🇳 中文</button>
        </div>
        <div class="script-container">
            <div id="content-ko" class="script-content active">{ko_script_html}</div>
            <div id="content-en" class="script-content">{en_script_html}</div>
            <div id="content-zh" class="script-content">{zh_script_html}</div>
        </div>

        <article class="page-card">
            <div class="page-header"><h2>📄 [SECTION 1] 🤖 최신 ML · AI · IT 테크 & 논문/영상 트렌드</h2></div>
            <div class="section-title">🧠 인공지능 & 머신러닝 최신 기술 동향 (AI Frontier)</div>
            {ai_items_html}
            
            <div class="section-title">📚 최신 AI/ML 논문 리뷰 (ArXiv Papers)</div>
            {paper_items_html}
            
            <div class="section-title">📺 화제의 유튜브 테크 영상 (YouTube Tech Picks)</div>
            {yt_items_html}
            
            <div class="section-title">💻 빅테크 · 반도체 & 엔지니어링 동향</div>
            {tech_items_html}
        </article>

        <article class="page-card">
            <div class="page-header"><h2>📄 [SECTION 2] 🌐 글로벌 경제 · 군사/안보 · 세계 정세</h2></div>
            <div class="section-title">📈 거시 경제 & 금융 시장 지표 (Macro Economy & Financials)</div>
            {econ_items_html}
            <div class="section-title">🛡️ 군사 · 국방 안보 & 지정학 이슈 (Military & Geopolitics)</div>
            {mil_items_html}
            <div class="section-title">🌍 국제 외교 & 글로벌 주요 뉴스 (World Diplomacy)</div>
            {world_items_html}
        </article>

        <footer class="footer">&copy; {datetime.now().year} Automated Daily Intelligence System | Generated for Executive Review | Daily at 09:00</footer>
    </div>
</body>
</html>
"""
        return html_content

    def build_archive(self):
        files = glob.glob(os.path.join(self.html_dir, "briefing_*.html"))
        dates = []
        for f in files:
            basename = os.path.basename(f)
            if basename.startswith("briefing_") and basename != "latest_briefing.html":
                date_str = basename.replace("briefing_", "").replace(".html", "")
                dates.append(date_str)
        dates.sort(reverse=True)

        cards_html = ""
        for date_str in dates:
            cards_html += f"""
            <a href="outputs/html/briefing_{date_str}.html" class="date-card">
                <div class="date-header">{date_str}</div>
                <div class="date-desc">Daily Intelligence Edition</div>
                <div class="read-more">열람하기 &rarr;</div>
            </a>
            """

        if not cards_html:
            cards_html = "<div style='text-align:center; padding: 40px; color: #64748b;'>아직 생성된 브리핑이 없습니다.</div>"

        archive_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Morning Briefing Archives</title>
    <style>
        :root {{ --bg-color: #f8fafc; --text-main: #1e293b; --accent-blue: #2563eb; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Segoe UI", sans-serif; background-color: var(--bg-color); color: var(--text-main); margin: 0; padding: 40px 20px; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        .top-nav {{ margin-bottom: 30px; text-align: left; }}
        .nav-btn {{ background: #ffffff; border: 1px solid #cbd5e1; padding: 8px 16px; border-radius: 8px; color: #475569; text-decoration: none; font-weight: 600; font-size: 0.95rem; cursor: pointer; transition: all 0.2s; }}
        .nav-btn:hover {{ background: #f1f5f9; color: var(--accent-blue); }}
        .header {{ text-align: center; margin-bottom: 40px; }}
        .header h1 {{ font-size: 2.8rem; margin: 0 0 10px 0; color: #0f172a; }}
        .header p {{ font-size: 1.1rem; color: #64748b; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 20px; }}
        .date-card {{ background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; text-decoration: none; color: inherit; transition: all 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.02); display: flex; flex-direction: column; }}
        .date-card:hover {{ transform: translateY(-4px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); border-color: #cbd5e1; }}
        .date-header {{ font-size: 1.5rem; font-weight: 700; color: var(--accent-blue); margin-bottom: 8px; }}
        .date-desc {{ font-size: 0.95rem; color: #64748b; margin-bottom: 20px; flex-grow: 1; }}
        .read-more {{ font-size: 0.9rem; font-weight: 600; color: #0f172a; text-align: right; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="top-nav">
            <a href="index.html" class="nav-btn">&larr; 오늘의 브리핑으로 돌아가기</a>
        </div>
        <div class="header">
            <h1>🗂️ Morning Briefing Archives</h1>
            <p>날짜별로 발행된 지난 데일리 모닝 인텔리전스 목록입니다.</p>
        </div>
        <div class="grid">
            {cards_html}
        </div>
    </div>
</body>
</html>
"""
        archive_path = os.path.join(self.root_dir, "archive.html")
        with open(archive_path, "w", encoding="utf-8") as f:
            f.write(archive_html)
        return archive_path

    def save(self, md_content: str, html_content: str, date_str: str) -> (str, str):
        md_file = os.path.join(self.md_dir, f"briefing_{date_str}.md")
        html_file = os.path.join(self.html_dir, f"briefing_{date_str}.html")
        
        # 1. Save standard HTML in outputs/html/ (Relative links: audio in ../audio/, archive in ../../archive.html)
        html_content_archived = html_content.replace("AUDIO_BASE_PATH", "../audio/").replace("ARCHIVE_LINK_PATH", "../../archive.html")
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content_archived)

        # 2. Save root index.html as TODAY's briefing (Relative links: audio in outputs/audio/, archive in archive.html)
        index_file = os.path.join(self.root_dir, "index.html")
        html_content_root = html_content.replace("AUDIO_BASE_PATH", "outputs/audio/").replace("ARCHIVE_LINK_PATH", "archive.html")
        with open(index_file, "w", encoding="utf-8") as f:
            f.write(html_content_root)

        # 3. Save standard Markdown
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_content)

        # 4. Generate the chronological archive page
        self.build_archive()

        return md_file, index_file
