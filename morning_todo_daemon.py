#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Morning To-Do Daemon & 09:00 Daily Action Items Popup Engine (v2.0)
===================================================================
Scans the latest Daily Notes in both Obsidian Vaults:
  1. Work Vault:    /Users/essim/work/Daily_Notes/YYYY-MM-DD.md
  2. Private Vault: /Users/essim/private/Daily_Notes/YYYY-MM-DD.md

Organizes the daily plan along TWO complementary axes:
  Axis 1 — Eisenhower 4-Quadrant Matrix (긴급도 × 중요도 4사분면):
    • Q1 (🔥 급하고 중요한 일 | Urgent & Important — 즉시 실행 / Do First)
    • Q2 (🎯 급하지 않지만 중요한 일 | Not Urgent & Important — 핵심 성장·계획 / Deep Work)
    • Q3 (⚡ 급하지만 덜 중요한 일 | Urgent & Less Important — 위임·자동화 / Delegate & Automate)
    • Q4 (🌱 급하지도 중요하지도 않은 일 | Not Urgent & Less Important — 후순위·배제 / Defer & Eliminate)

  Axis 2 — Execution Ownership (수행 주체별 분리):
    • 🙋‍♂️ 내가 직접 해야 하는 일 (Direct Action — 본인 주도 의사결정·배포·작성·학습)
    • ⏳ 위임 후 피드백/회신 대기 (Waiting & Checkpoints — 파트너/엔지니어 회신 확인)
    • 📡 모니터링만 해야 하는 일 (Monitoring Only — 데몬 자동관제 & 라인 수율/Cpk 관찰)

Renders an interactive dark-mode checklist HTML (`outputs/today_todo.html`)
and pops up a native macOS dialog + system notification every morning at 09:00:00.
"""

import argparse
import datetime
import glob
import html
import re
import subprocess
import sys
import time
from pathlib import Path

PRIVATE_NOTES_DIR = Path("/Users/essim/private/Daily_Notes")
WORK_NOTES_DIR = Path("/Users/essim/work/Daily_Notes")
BRIEFING_DIR = Path("/Users/essim/private/02.Daily_Morning_Briefing")
OUTPUT_HTML = BRIEFING_DIR / "outputs" / "today_todo.html"
LOG_DIR = BRIEFING_DIR / "logs"


def get_latest_note(notes_dir: Path) -> Path | None:
    files = sorted(glob.glob(str(notes_dir / "202*.md")))
    return Path(files[-1]) if files else None


def clean_md_line(line: str) -> str:
    """Strip markdown links/formatting for clean plain-text popup display."""
    line = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", line)
    line = re.sub(r"\[\[([^\]]+)\]\]", r"\1", line)
    line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
    line = line.replace("**", "").replace("`", "")
    return line.strip()


def extract_work_structured(note_path: Path | None) -> dict[str, list[str]]:
    """Extract structured tasks from Work Daily Note (direct, waiting, monitoring, growth)."""
    result: dict[str, list[str]] = {
        "direct": [],
        "waiting": [],
        "monitoring": [],
        "growth": [],
    }
    if not note_path or not note_path.exists():
        return result

    text = note_path.read_text(encoding="utf-8", errors="replace")

    # 1. Check for modern work_todo markdown tables (4-4 Quadrants & 4-2 Leadership)
    if "### 4-4." in text or "4사분면 분류" in text:
        # Parse Leadership requests (4-2)
        m_lead = re.search(r'###\s*4-2\.\s*.*?매니저와 TPM 직접 요청.*?\n(.*?)(?=###|\n##|\Z)', text, re.DOTALL)
        if m_lead:
            lines = [l.strip() for l in m_lead.group(1).splitlines() if l.strip().startswith("|")]
            for l in lines[2:]:
                parts = [p.strip() for p in l.split("|")[1:-1]]
                if len(parts) >= 4:
                    no_str = clean_md_line(parts[0])
                    requester = clean_md_line(parts[1])
                    req = clean_md_line(parts[2]).split("<br>")[0]
                    act = clean_md_line(parts[3])
                    dri = clean_md_line(parts[4]) if len(parts) > 4 else ""
                    result["direct"].append(f"[Work/Leadership] #{no_str} [{requester}] {req} (액션: {act}, DRI: {dri})")

        # Parse 4-4 Quadrants
        m_eisen = re.search(r'###\s*4-4\.\s*.*?4사분면 분류.*?\n(.*?)(?=###\s*4-6|\n##\s*🛠️|\n##\s*🤝|\Z)', text, re.DOTALL)
        if m_eisen:
            eisen_sec = m_eisen.group(1)
            q_matches = [
                ("Q1", r'####\s*🔴\s*1사분면.*?\n(.*?)(?=####|\n---|\Z)'),
                ("Q2", r'####\s*🟡\s*2사분면.*?\n(.*?)(?=####|\n---|\Z)'),
                ("Q3", r'####\s*🟠\s*3사분면.*?\n(.*?)(?=####|\n---|\Z)'),
                ("Q4", r'####\s*⚪\s*4사분면.*?\n(.*?)(?=####|\n---|\Z)'),
            ]
            for q_id, pat in q_matches:
                match = re.search(pat, eisen_sec, re.DOTALL)
                if match:
                    t_lines = [l.strip() for l in match.group(1).splitlines() if l.strip().startswith("|")]
                    for l in t_lines[2:]:
                        parts = [p.strip() for p in l.split("|")[1:-1]]
                        if len(parts) >= 4:
                            no_str = clean_md_line(parts[0])
                            task_str = clean_md_line(parts[1]).split("<br>")[0]
                            act_str = clean_md_line(parts[2])
                            dri_str = clean_md_line(parts[3])

                            formatted = f"[Work/{q_id}] #{no_str} {task_str} (DRI: {dri_str})"

                            if "직접" in act_str:
                                if q_id in ("Q1", "Q2"):
                                    result["direct"].append(formatted)
                                else:
                                    result["growth"].append(formatted)
                            elif "리뷰" in act_str or "승인" in act_str:
                                result["direct"].append(formatted)
                            elif "대기" in act_str or "피드백" in act_str or "위임" in act_str:
                                result["waiting"].append(formatted)
                            elif "모니터링" in act_str or "관찰" in act_str:
                                result["monitoring"].append(formatted)
                            else:
                                if q_id == "Q1":
                                    result["direct"].append(formatted)
                                elif q_id == "Q2":
                                    result["growth"].append(formatted)
                                elif q_id == "Q3":
                                    result["waiting"].append(formatted)
                                else:
                                    result["monitoring"].append(formatted)

        if any(result.values()):
            return result

    # 2. Fallback to legacy parser if modern tables weren't found
    current_bucket: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("### 1️⃣") or "내가 직접 해야 하는 일" in line or "Direct Action Required" in line:
            current_bucket = "direct"
            continue
        elif line.startswith("### 2️⃣") or "위임 후 피드백" in line or "Waiting for Feedback" in line:
            current_bucket = "waiting"
            continue
        elif line.startswith("### 3️⃣") or "모니터링만 해야 하는 일" in line or "Monitoring & Tracking" in line:
            current_bucket = "monitoring"
            continue
        elif line.startswith("### 4️⃣") or "개인 행정 및 역량 개발" in line or "Study & Development" in line:
            current_bucket = "growth"
            continue
        elif line.startswith("## ") and not line.startswith("### "):
            if any(result.values()):
                current_bucket = None

        if not current_bucket:
            continue

        if line.startswith("- [ ]"):
            item = clean_md_line(line[5:]).rstrip(":")
            if item:
                result[current_bucket].append(f"[Work] {item}")
        elif line.startswith("- **`P") or (current_bucket in ("waiting", "monitoring", "growth") and line.startswith("- **")):
            item = clean_md_line(line[2:]).rstrip(":")
            if item:
                result[current_bucket].append(f"[Work] {item}")

    return result


def extract_private_structured(note_path: Path | None) -> dict[str, list[str]]:
    """Extract structured tasks from Private Daily Note (q1_direct, q2_direct, monitoring, eliminate)."""
    result: dict[str, list[str]] = {
        "q1_direct": [],
        "q2_direct": [],
        "monitoring": [],
        "eliminate": [],
    }
    if not note_path or not note_path.exists():
        return result

    text = note_path.read_text(encoding="utf-8", errors="replace")
    in_next_actions = False
    current_bucket = "q1_direct"
    current_group = ""

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("#") and ("Next Action Items" in line or "실행 계획" in line):
            in_next_actions = True
            continue
        if not in_next_actions:
            continue
        if line.startswith("## ") and "Next Action" not in line and "실행 계획" not in line:
            break

        m_num = re.match(r"^(\d+)\.\s+(.+?):?$", line)
        if m_num:
            header_text = clean_md_line(m_num.group(2))
            current_group = header_text
            if "Q1" in header_text and ("직접" in header_text or "Direct" in header_text):
                current_bucket = "q1_direct"
            elif "Q2" in header_text or "학습" in header_text or "HSK" in header_text or "DBA" in header_text:
                current_bucket = "q2_direct"
            elif "모니터링" in header_text or "Monitoring" in header_text or "Q3" in header_text:
                current_bucket = "monitoring"
            elif "Q4" in header_text or "배제" in header_text or "Eliminate" in header_text:
                current_bucket = "eliminate"
            elif "Kaggle" in header_text or "퀀트" in header_text:
                current_bucket = "q1_direct"
            continue

        if line.startswith("- "):
            sub = clean_md_line(line[2:])
            if not sub:
                continue
            # Auto-route items if note uses legacy numbering
            if "모니터링" in sub or "자동관제" in sub or "대기]" in sub or "관찰]" in sub:
                result["monitoring"].append(sub)
            elif "배제]" in sub or "지양" in sub:
                result["eliminate"].append(sub)
            else:
                result[current_bucket].append(sub)

    return result


def build_unified_plan(
    work_data: dict[str, list[str]],
    priv_data: dict[str, list[str]],
) -> dict[str, list[str]]:
    """Combine Work & Private structured tasks into 4 Quadrants (Q1~Q4) + Execution Modes."""
    # Deduplicate helper
    def dedup(items: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for x in items:
            key = x[:45]
            if key not in seen:
                seen.add(key)
                out.append(x)
        return out

    # 1. Execution Ownership Buckets
    direct_actions = dedup(work_data["direct"] + priv_data["q1_direct"] + priv_data["q2_direct"] + work_data["growth"])
    waiting_actions = dedup(work_data["waiting"])
    monitoring_actions = dedup(work_data["monitoring"] + priv_data["monitoring"])
    eliminate_actions = dedup(priv_data["eliminate"])

    # 2. 4-Quadrant Matrix (Q1, Q2, Q3, Q4)
    q1_urgent_important = dedup(
        work_data["direct"][:8]
        + [x for x in priv_data["q1_direct"] if not x.startswith("[Work/")]
        + work_data["waiting"][:3]
    )
    q2_not_urgent_important = dedup(
        priv_data["q2_direct"]
        + work_data["growth"]
        + [x for x in work_data["direct"] if "Image Viewer" in x]
    )
    q3_urgent_less_important = dedup(
        work_data["waiting"][3:]
        + [x for x in priv_data["monitoring"] if "자동관제" in x or "대기" in x]
        + ["[Auto Daemon] 09:00 모닝 브리핑(run_briefing.sh) 및 morning_todo_daemon.py 체크리스트 자동 발행"]
    )
    q4_not_urgent_less_important = dedup(
        work_data["monitoring"]
        + eliminate_actions
    )

    return {
        "Q1": q1_urgent_important,
        "Q2": q2_not_urgent_important,
        "Q3": q3_urgent_less_important,
        "Q4": q4_not_urgent_less_important,
        "direct": direct_actions,
        "waiting": waiting_actions,
        "monitoring": monitoring_actions,
        "eliminate": eliminate_actions,
    }


def render_item_list(items: list[str], prefix_id: str, badge_text: str = "", badge_cls: str = "") -> str:
    if not items:
        return '<div class="empty">등록된 항목이 없습니다.</div>'
    rows: list[str] = []
    for i, text in enumerate(items):
        item_id = f"{prefix_id}_{i}"
        badge_html = f'<span class="tag {badge_cls}">{html.escape(badge_text)}</span>' if badge_text else ""
        rows.append(
            f'<label class="todo-item" for="{item_id}">'
            f'<input type="checkbox" id="{item_id}" data-persist="{item_id}">'
            f'<span>{badge_html}{html.escape(text)}</span>'
            f"</label>"
        )
    return "\n".join(rows)


def extract_briefing_highlights() -> str:
    """Extracts top headlines and market indicators from latest_briefing.md for embedding into today_todo.html."""
    briefing_file = BRIEFING_DIR / "outputs" / "markdown" / "latest_briefing.md"
    if not briefing_file.exists():
        return ""
    try:
        content = briefing_file.read_text(encoding="utf-8")
        ai_matches = re.findall(r'-\s*\*\*\[CARD \d+ \| ([^\]]+)\]\*\*\s*\[([^\]]+)\]\(([^)]+)\)', content)
        
        # Find market text if present
        m_market = re.search(r'###\s*📊?\s*1\.\s*글로벌 주요 증시.*?```text\n(.*?)```', content, re.DOTALL)
        market_str = m_market.group(1).strip() if m_market else ""
        
        cards = []
        if ai_matches:
            cards_html = []
            for source, title, url in ai_matches[:6]:
                cards_html.append(f'<li style="margin-bottom:6px;"><strong style="color:#38bdf8;">[{source}]</strong> <a href="{url}" target="_blank" style="color:#f8fafc; text-decoration:none;">{title} ↗</a></li>')
            cards.append(f"""
            <div style="background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 12px; padding: 14px 18px;">
                <h3 style="color:#38bdf8; font-size: 0.95rem; margin-top:0; margin-bottom:10px;">🤖 AI · 머신러닝 · 빅테크 최신 뉴스</h3>
                <ul style="list-style: none; padding-left: 0; margin: 0; font-size: 0.88rem; line-height: 1.45;">
                    {"".join(cards_html)}
                </ul>
            </div>
            """)
            
        if market_str:
            market_lines = [f"<li>{l.strip()}</li>" for l in market_str.splitlines() if l.strip()]
            cards.append(f"""
            <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 12px; padding: 14px 18px;">
                <h3 style="color:#34d399; font-size: 0.95rem; margin-top:0; margin-bottom:10px;">📊 글로벌 증시 & 환율 지표</h3>
                <ul style="list-style: none; padding-left: 0; margin: 0; font-size: 0.86rem; line-height: 1.45; color: #a7f3d0;">
                    {"".join(market_lines[:6])}
                </ul>
            </div>
            """)
            
        portal_btn = f"""
        <div style="margin-bottom: 22px; background: linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(15, 23, 42, 0.95)); border: 1px solid rgba(56, 189, 248, 0.35); border-radius: 14px; padding: 18px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; flex-wrap: wrap; gap: 10px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 10px;">
                <div style="font-weight: 700; font-size: 1.05rem; color: #38bdf8; display: flex; align-items: center; gap: 8px;">
                    <span>📰</span> 오늘의 모닝 브리핑 인텔리전스 (Morning Briefing Highlights)
                </div>
                <div style="display: flex; gap: 8px;">
                    <a href="file://{BRIEFING_DIR / 'index.html'}" target="_blank" style="background:#0284c7; color:white; padding:6px 14px; border-radius:8px; font-size:0.82rem; text-decoration:none; font-weight:600;">Google News 카드뉴스 포털 ↗</a>
                    <a href="file://{BRIEFING_DIR / 'outputs' / 'audio' / 'latest_briefing_ko.m4a'}" target="_blank" style="background:#7c3aed; color:white; padding:6px 14px; border-radius:8px; font-size:0.82rem; text-decoration:none; font-weight:600;">🎧 5분 오디오 ↗</a>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 14px;">
                {"".join(cards)}
            </div>
        </div>
        """
        return portal_btn
    except Exception:
        return ""


def render_html_checklist(
    today_str: str,
    work_note: Path | None,
    priv_note: Path | None,
    plan: dict[str, list[str]],
) -> Path:
    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    work_link = f"file://{work_note}" if work_note else "#"
    priv_link = f"file://{priv_note}" if priv_note else "#"
    briefing_highlights_html = extract_briefing_highlights()

    q1_html = render_item_list(plan["Q1"], "q1", "Q1 즉시실행", "tag-q1")
    q2_html = render_item_list(plan["Q2"], "q2", "Q2 핵심성장", "tag-q2")
    q3_html = render_item_list(plan["Q3"], "q3", "Q3 위임/자동", "tag-q3")
    q4_html = render_item_list(plan["Q4"], "q4", "Q4 관찰/배제", "tag-q4")

    direct_html = render_item_list(plan["direct"], "dir", "🙋‍♂️ 직접수행", "tag-direct")
    waiting_html = render_item_list(plan["waiting"], "wait", "⏳ 피드백대기", "tag-wait")
    monitoring_html = render_item_list(plan["monitoring"], "mon", "📡 모니터링", "tag-mon")

    total_direct = len(plan["direct"])
    total_mon = len(plan["waiting"]) + len(plan["monitoring"])

    doc = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>☀️ {today_str} 하루 계획 — 4사분면 & 직접수행 vs 모니터링 보드</title>
<style>
  :root {{
    --bg: #0b1120;
    --card: #162033;
    --card-alt: #1e293b;
    --border: #334155;
    --text: #f8fafc;
    --muted: #94a3b8;
    --q1: #f43f5e;
    --q2: #38bdf8;
    --q3: #f59e0b;
    --q4: #10b981;
    --direct: #a855f7;
    --mon: #06b6d4;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 28px 20px 60px;
    font-family: -apple-system, BlinkMacSystemFont, "Pretendard", "Segoe UI", sans-serif;
    background: radial-gradient(circle at top right, #1e1b4b, var(--bg));
    color: var(--text);
    min-height: 100vh;
  }}
  .container {{ max-width: 1240px; margin: 0 auto; }}
  header {{
    display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 16px;
    padding: 24px 28px; background: var(--card);
    border: 1px solid var(--border); border-radius: 18px;
    margin-bottom: 22px; box-shadow: 0 12px 32px rgba(0,0,0,0.4);
  }}
  h1 {{ margin: 0; font-size: 1.55rem; letter-spacing: -0.02em; }}
  .sub {{ color: var(--muted); font-size: 0.92rem; margin-top: 6px; }}
  .header-right {{ display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }}
  .stat-pill {{
    padding: 7px 14px; border-radius: 999px; font-weight: 600; font-size: 0.84rem;
    border: 1px solid var(--border); background: rgba(255,255,255,0.04);
  }}
  .stat-pill.direct {{ color: #e9d5ff; border-color: rgba(168,85,247,0.5); background: rgba(168,85,247,0.15); }}
  .stat-pill.mon {{ color: #a5f3fc; border-color: rgba(6,182,212,0.5); background: rgba(6,182,212,0.15); }}
  .vault-links {{ display: flex; gap: 10px; margin-top: 8px; }}
  .vault-links a {{
    font-size: 0.82rem; color: var(--q2); text-decoration: none;
    padding: 4px 10px; border-radius: 8px; background: rgba(56,189,248,0.1);
    border: 1px solid rgba(56,189,248,0.3);
  }}
  .tabs {{
    display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap;
  }}
  .tab-btn {{
    padding: 10px 18px; border-radius: 12px; border: 1px solid var(--border);
    background: var(--card); color: var(--muted); font-weight: 600; font-size: 0.92rem;
    cursor: pointer; transition: all 0.15s;
  }}
  .tab-btn.active, .tab-btn:hover {{
    color: var(--text); border-color: var(--q2);
    background: rgba(56,189,248,0.16);
  }}
  .section-title {{
    font-size: 1.2rem; font-weight: 700; margin: 26px 0 14px;
    display: flex; align-items: center; gap: 10px;
  }}
  .quadrant-grid {{
    display: grid; grid-template-columns: repeat(2, 1fr); gap: 18px;
  }}
  .role-grid {{
    display: grid; grid-template-columns: repeat(2, 1fr); gap: 18px;
  }}
  @media (max-width: 900px) {{
    .quadrant-grid, .role-grid {{ grid-template-columns: 1fr; }}
  }}
  .card {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: 16px; padding: 20px 22px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.28);
  }}
  .card.q1 {{ border-top: 4px solid var(--q1); }}
  .card.q2 {{ border-top: 4px solid var(--q2); }}
  .card.q3 {{ border-top: 4px solid var(--q3); }}
  .card.q4 {{ border-top: 4px solid var(--q4); }}
  .card.role-direct {{ border-top: 4px solid var(--direct); }}
  .card.role-mon {{ border-top: 4px solid var(--mon); }}
  .card h2 {{
    margin: 0 0 6px 0; font-size: 1.1rem;
    display: flex; justify-content: space-between; align-items: center;
  }}
  .card .desc {{
    color: var(--muted); font-size: 0.83rem; margin-bottom: 14px;
    padding-bottom: 10px; border-bottom: 1px solid var(--border);
  }}
  .todo-item {{
    display: flex; align-items: flex-start; gap: 10px;
    padding: 9px 10px; border-radius: 10px;
    transition: background 0.15s; cursor: pointer;
    line-height: 1.48; font-size: 0.91rem;
  }}
  .todo-item:hover {{ background: rgba(255,255,255,0.05); }}
  .todo-item input[type="checkbox"] {{
    margin-top: 4px; width: 17px; height: 17px; accent-color: var(--q2);
    cursor: pointer; flex-shrink: 0;
  }}
  .todo-item input[type="checkbox"]:checked + span {{
    text-decoration: line-through; color: var(--muted);
  }}
  .tag {{
    display: inline-block; font-size: 0.72rem; font-weight: 700;
    padding: 2px 7px; border-radius: 6px; margin-right: 7px; vertical-align: middle;
  }}
  .tag-q1 {{ background: rgba(244,63,94,0.2); color: #fda4af; border: 1px solid rgba(244,63,94,0.4); }}
  .tag-q2 {{ background: rgba(56,189,248,0.2); color: #7dd3fc; border: 1px solid rgba(56,189,248,0.4); }}
  .tag-q3 {{ background: rgba(245,158,11,0.2); color: #fcd34d; border: 1px solid rgba(245,158,11,0.4); }}
  .tag-q4 {{ background: rgba(16,185,129,0.2); color: #6ee7b7; border: 1px solid rgba(16,185,129,0.4); }}
  .tag-direct {{ background: rgba(168,85,247,0.2); color: #d8b4fe; border: 1px solid rgba(168,85,247,0.4); }}
  .tag-wait {{ background: rgba(245,158,11,0.2); color: #fde68a; border: 1px solid rgba(245,158,11,0.4); }}
  .tag-mon {{ background: rgba(6,182,212,0.2); color: #67e8f9; border: 1px solid rgba(6,182,212,0.4); }}
  .empty {{ color: var(--muted); font-size: 0.88rem; padding: 8px 4px; }}
  .hidden {{ display: none !important; }}
</style>
</head>
<body>
  <div class="container">
    <header>
      <div>
        <h1>🧭 오늘의 하루 계획 마스터 보드 ({today_str})</h1>
        <div class="sub">아이젠하워 4사분면(긴급도 × 중요도) & 수행 주체별(🙋‍♂️ 내가 직접 할 일 vs 📡 모니터링만 할 일) 통합 관제</div>
        <div class="vault-links">
          <a href="{work_link}">🌌 Work Daily Note 열기 ↗</a>
          <a href="{priv_link}">🔒 Private Daily Note 열기 ↗</a>
        </div>
      </div>
      <div class="header-right">
        <div class="stat-pill direct">🙋‍♂️ 내가 직접 수행: {total_direct}건</div>
        <div class="stat-pill mon">📡 대기·모니터링: {total_mon}건</div>
      </div>
    </header>

    {briefing_highlights_html}

    <div class="tabs">
      <button class="tab-btn active" onclick="switchView('all', this)">🌟 전체 통합 보기 (4사분면 + 수행 주체 분리)</button>
      <button class="tab-btn" onclick="switchView('quadrant', this)">🧭 1. 아이젠하워 4사분면 (Q1~Q4) 집중 보기</button>
      <button class="tab-btn" onclick="switchView('role', this)">👥 2. 내가 직접 할 일 vs 모니터링 집중 보기</button>
    </div>

    <!-- Part 1: 4-Quadrant Matrix -->
    <div id="view-quadrant">
      <div class="section-title">🧭 Part 1. 아이젠하워 4사분면 매트릭스 (긴급도 × 중요도)</div>
      <div class="quadrant-grid">
        <section class="card q1">
          <h2><span>🔥 Q1. 급하고 중요한 일 (Urgent & Important)</span><span>{len(plan["Q1"])}건</span></h2>
          <div class="desc">즉시 최우선 실행 (Do First) — 메인 빌드 블로커, 라인 CAPA 검증, 당일 마감 배포·머지, 15:10 종가매매 본장 판정</div>
          {q1_html}
        </section>

        <section class="card q2">
          <h2><span>🎯 Q2. 급하지 않지만 중요한 일 (Not Urgent & Important)</span><span>{len(plan["Q2"])}건</span></h2>
          <div class="desc">핵심 성장 & 전략적 시간 블록 확보 (Schedule & Deep Work) — HSK 5급, My_Dev_Wiki 기술 스택 실습, DBA & PGP AI/ML</div>
          {q2_html}
        </section>

        <section class="card q3">
          <h2><span>⚡ Q3. 급하지만 덜 중요한 일 (Urgent & Less Important)</span><span>{len(plan["Q3"])}건</span></h2>
          <div class="desc">위임·자동화 및 신속 배치 처리 (Delegate & Automate) — 현장 데이터 측정 위임, 루틴 스펙 교체, 데몬 자동 디스패치</div>
          {q3_html}
        </section>

        <section class="card q4">
          <h2><span>🌱 Q4. 급하지도 중요하지도 않은 일 (Not Urgent & Less Important)</span><span>{len(plan["Q4"])}건</span></h2>
          <div class="desc">수동 관제·후순위 유예 및 비효율 배제 (Defer & Eliminate) — 안정화 파라미터 추이 관찰, 임시방편(억지 삽입 등) 차단</div>
          {q4_html}
        </section>
      </div>
    </div>

    <!-- Part 2: Direct Action vs Monitoring -->
    <div id="view-role">
      <div class="section-title">👥 Part 2. 수행 주체별 분리 (🙋‍♂️ 내가 직접 해야 하는 일 vs 📡 모니터링만 해야 하는 일)</div>
      <div class="role-grid">
        <section class="card role-direct">
          <h2><span>🙋‍♂️ 1. 내가 직접 해야 하는 일 (My Direct Action)</span><span>{len(plan["direct"])}건</span></h2>
          <div class="desc">본인이 직접 코딩·배포 승인·FACA 기술 판정·미팅 참석·학습을 주도해야 하는 과업</div>
          {direct_html}
        </section>

        <section class="card role-mon">
          <h2><span>📡 2. 모니터링만 해야 하는 일 & 회신 대기 (Monitoring & Waiting)</span><span>{total_mon}건</span></h2>
          <div class="desc">파트너(FIH/엔지니어) 회신 체크포인트(14:00/16:00) 및 무인 데몬(Kaggle·Quant·수율) 결과 확인</div>
          {waiting_html}
          <hr style="border:0; border-top:1px dashed var(--border); margin:12px 0;">
          {monitoring_html}
        </section>
      </div>
    </div>
  </div>

  <script>
    const STORAGE_Prefix = "todo_{today_str}_";
    document.querySelectorAll('input[type="checkbox"][data-persist]').forEach(cb => {{
      const key = STORAGE_Prefix + cb.getAttribute('data-persist');
      if (localStorage.getItem(key) === '1') cb.checked = true;
      cb.addEventListener('change', () => {{
        localStorage.setItem(key, cb.checked ? '1' : '0');
      }});
    }});

    function switchView(mode, btn) {{
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const q = document.getElementById('view-quadrant');
      const r = document.getElementById('view-role');
      if (mode === 'all') {{
        q.classList.remove('hidden');
        r.classList.remove('hidden');
      }} else if (mode === 'quadrant') {{
        q.classList.remove('hidden');
        r.classList.add('hidden');
      }} else {{
        q.classList.add('hidden');
        r.classList.remove('hidden');
      }}
    }}
  </script>
</body>
</html>
"""
    OUTPUT_HTML.write_text(doc, encoding="utf-8")
    return OUTPUT_HTML


def trigger_macos_popup(
    today_str: str,
    plan: dict[str, list[str]],
    html_path: Path,
    open_browser: bool = False,
    no_popup: bool = False,
) -> None:
    if no_popup:
        if open_browser:
            subprocess.run(["open", str(html_path)], check=False)
        return

    lines: list[str] = [f"🧭 [{today_str}] 4사분면 & 수행주체별 하루 계획 요약", ""]
    lines.append("🔥 [Q1 · 급하고 중요한 일 | 🙋‍♂️ 내가 직접 수행]")
    for idx, item in enumerate(plan["Q1"][:4], 1):
        short = item if len(item) <= 74 else item[:71] + "..."
        lines.append(f"  {idx}. {short}")

    lines.append("")
    lines.append("🎯 [Q2 · 안 급하지만 중요한 일 | 🙋‍♂️ 핵심 성장·학습]")
    for idx, item in enumerate(plan["Q2"][:3], 1):
        short = item if len(item) <= 74 else item[:71] + "..."
        lines.append(f"  {idx}. {short}")

    lines.append("")
    lines.append("📡 [Q3/Q4 · 위임 대기 & 모니터링만 해야 하는 일]")
    mon_combined = plan["waiting"][:2] + plan["monitoring"][:2]
    for idx, item in enumerate(mon_combined[:3], 1):
        short = item if len(item) <= 74 else item[:71] + "..."
        lines.append(f"  {idx}. {short}")

    dialog_text = "\n".join(lines)
    escaped_text = dialog_text.replace("\\", "\\\\").replace('"', '\\"')
    title_text = f"🧭 09:00 하루 계획 (4사분면 · 직접수행 vs 모니터링) [{today_str}]"

    total_cnt = len(plan["direct"]) + len(plan["waiting"]) + len(plan["monitoring"])
    notif_cmd = (
        f'osascript -e \'display notification "직접 수행 {len(plan["direct"])}건 / 모니터링 {len(plan["waiting"]) + len(plan["monitoring"])}건이 정리되었습니다." '
        f'with title "{title_text}" sound name "Glass"\''
    )
    subprocess.run(notif_cmd, shell=True, check=False)
    subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"], check=False)

    apple_script = f'''
    set userChoice to button returned of (display dialog "{escaped_text}" with title "{title_text}" buttons {{"4사분면 웹 보드 열기", "확인"}} default button "확인" giving up after 45)
    if userChoice is "4사분면 웹 보드 열기" then
        do shell script "open " & quoted form of "{html_path}"
    end if
    '''
    subprocess.Popen(["osascript", "-e", apple_script])

    if open_browser:
        subprocess.run(["open", str(html_path)], check=False)


def run_once(open_browser: bool = False, no_popup: bool = False) -> None:
    now = datetime.datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    work_note = get_latest_note(WORK_NOTES_DIR)
    priv_note = get_latest_note(PRIVATE_NOTES_DIR)

    work_data = extract_work_structured(work_note)
    priv_data = extract_private_structured(priv_note)
    plan = build_unified_plan(work_data, priv_data)

    html_path = render_html_checklist(today_str, work_note, priv_note, plan)
    print(f"[{now.isoformat()}] Generated 4-Quadrant & Role-Separated HTML: {html_path}")
    print(f"  - Q1 (Urgent & Important):      {len(plan['Q1'])} items")
    print(f"  - Q2 (Not Urgent & Important):  {len(plan['Q2'])} items")
    print(f"  - Q3 (Urgent & Less Important): {len(plan['Q3'])} items")
    print(f"  - Q4 (Defer / Monitor / Elim):  {len(plan['Q4'])} items")
    print(f"  - 🙋‍♂️ Direct Action:            {len(plan['direct'])} items")
    print(f"  - 📡 Waiting + Monitoring:      {len(plan['waiting']) + len(plan['monitoring'])} items")

    trigger_macos_popup(today_str, plan, html_path, open_browser=open_browser, no_popup=no_popup)


def run_daemon_loop() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[{datetime.datetime.now().isoformat()}] 🚀 Morning To-Do Daemon v2.0 started (Target: 09:00:00 daily).")
    sys.stdout.flush()

    last_triggered_date: str | None = None
    while True:
        now = datetime.datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        if now.hour == 9 and now.minute == 0 and last_triggered_date != today_str:
            try:
                run_once(open_browser=False, no_popup=False)
                last_triggered_date = today_str
            except Exception as exc:
                print(f"[{now.isoformat()}] Error in run_once: {exc}", file=sys.stderr)
            sys.stdout.flush()

        time.sleep(15)


def main() -> None:
    parser = argparse.ArgumentParser(description="09:00 Morning To-Do Popup Daemon (4-Quadrant & Role Split)")
    parser.add_argument("--once", action="store_true", help="Run popup once immediately and exit")
    parser.add_argument("--no-popup", action="store_true", help="Do not trigger native macOS popup dialog or audio alert")
    parser.add_argument("--quiet", action="store_true", help="Run quietly without dialogs or browser popups")
    parser.add_argument("--daemon", action="store_true", help="Run continuous background daemon firing at 09:00 daily")
    parser.add_argument("--open-html", action="store_true", help="Also open HTML checklist in browser")
    args = parser.parse_args()

    no_popup = args.no_popup or args.quiet
    if args.daemon:
        run_daemon_loop()
    else:
        run_once(open_browser=args.open_html, no_popup=no_popup)


if __name__ == "__main__":
    main()
