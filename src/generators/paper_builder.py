import os
import glob
import json
import html as html_lib
from datetime import datetime
from typing import Dict, Any, List, Tuple
from src.generators.card_news_enricher import enrich_section_items, CATEGORY_META


class PaperBuilder:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.root_dir = os.path.dirname(self.output_dir)  # root directory (Daily_Morning_Briefing)
        self.html_dir = os.path.join(self.output_dir, "html")
        self.md_dir = os.path.join(self.output_dir, "markdown")
        os.makedirs(self.html_dir, exist_ok=True)
        os.makedirs(self.md_dir, exist_ok=True)

    def build_markdown(self, tech_data: Dict[str, Any], econ_data: Dict[str, Any], affirmation: str, date_str: str) -> str:
        ai_cards = enrich_section_items(tech_data.get("ai_headlines", [])[:6], "ai")
        tech_cards = enrich_section_items(tech_data.get("tech_headlines", [])[:6], "tech")
        paper_cards = enrich_section_items(tech_data.get("arxiv_papers", [])[:6], "paper")
        yt_cards = enrich_section_items(tech_data.get("youtube_picks", [])[:6], "youtube")
        tools_cards = enrich_section_items(tech_data.get("ai_tools", [])[:6], "tools")
        econ_cards = enrich_section_items(econ_data.get("economy_headlines", [])[:6], "econ")
        mil_cards = enrich_section_items(econ_data.get("military_headlines", [])[:6], "military")
        world_cards = enrich_section_items(econ_data.get("world_headlines", [])[:6], "world")

        total_cards_count = len(ai_cards) + len(tech_cards) + len(paper_cards) + len(yt_cards) + len(tools_cards) + len(econ_cards) + len(mil_cards) + len(world_cards)
        md = []
        md.append("# 📰 GOOGLE NEWS BRIEFING | 데일리 모닝 카드뉴스 인텔리전스")
        md.append(f"> **발행 일시**: {date_str} 09:00 KST | **에디션**: Google News Style Card Edition | **총 {total_cards_count}개 카드뉴스**\n")
        md.append("=" * 80)

        def append_md_cards(section_title: str, cards: List[Dict[str, Any]]):
            md.append(f"\n### {section_title}")
            for c in cards:
                tags_str = " ".join(c.get("keywords", []))
                md.append(f"- **[CARD {c['card_index']:02d} | {c['source']}]** [{c['title']}]({c['link']}) `{c['time_ago']}`")
                md.append(f"  - 💡 **핵심 요약**: {c['summary']}")
                if tags_str:
                    md.append(f"  - 🏷️ **키워드**: {tags_str}")

        md.append("\n## 📄 [SECTION 1] 🤖 최신 ML · AI · IT 테크 & 논문/유튜브/신규 툴 카드뉴스")
        append_md_cards("🧠 1. 인공지능 & 머신러닝 (AI & Frontier LLM)", ai_cards)
        append_md_cards("💻 2. 빅테크 · 반도체 & 엔지니어링 동향", tech_cards)
        append_md_cards("📚 3. 최신 AI/ML 연구 논문 (ArXiv Papers)", paper_cards)
        append_md_cards("📺 4. 유튜브 추천 테크 영상 (YouTube Tech Picks)", yt_cards)
        append_md_cards("🛠️ 5. 주목할 만한 AI/ML 신규 툴 & 핵심 기법 (New AI Tools & Techniques)", tools_cards)

        md.append("\n" + "-" * 80)
        md.append("\n## 📄 [SECTION 2] 🌐 글로벌 경제 · 군사/안보 · 세계 정세 카드뉴스")

        stock_heatmaps = econ_data.get("stock_heatmaps")
        if not stock_heatmaps:
            try:
                from src.collectors.stock_heatmap_collector import StockHeatmapCollector
                stock_heatmaps = StockHeatmapCollector(self.output_dir).collect_all()
            except Exception:
                stock_heatmaps = {}
        if stock_heatmaps:
            md.append("\n### 📊 글로벌 증시 히트맵 & 주요 지표 (US & KR Stock Heatmaps)")
            us_map = stock_heatmaps.get("us", {})
            if us_map:
                us_indices_str = " | ".join([f"**{idx['name']}**: {idx['price']:,.2f} ({'+' if idx['change_pct']>0 else ''}{idx['change_pct']:.2f}%)" for idx in us_map.get("indices", [])])
                us_sum = us_map.get("summary", {})
                tg = us_sum.get("top_gainer", {})
                tl = us_sum.get("top_loser", {})
                md.append(f"- **🇺🇸 미국 S&P 500 / NASDAQ**: {us_indices_str}")
                md.append(f"  - 📈 시장 등락: 상승 {us_sum.get('advancers', 0)} / 하락 {us_sum.get('decliners', 0)} | 🔥 최고: {tg.get('name', '')} ({'+' if tg.get('change_pct',0)>0 else ''}{tg.get('change_pct',0):.2f}%) | 💧 최저: {tl.get('name', '')} ({tl.get('change_pct',0):.2f}%)")
            kr_map = stock_heatmaps.get("kr", {})
            if kr_map:
                kr_indices_str = " | ".join([f"**{idx['name']}**: {idx['price']:,.2f} ({'+' if idx['change_pct']>0 else ''}{idx['change_pct']:.2f}%)" for idx in kr_map.get("indices", [])])
                kr_sum = kr_map.get("summary", {})
                tg = kr_sum.get("top_gainer", {})
                tl = kr_sum.get("top_loser", {})
                md.append(f"- **🇰🇷 한국 KOSPI / KOSDAQ**: {kr_indices_str}")
                md.append(f"  - 📈 시장 등락: 상승 {kr_sum.get('advancers', 0)} / 하락 {kr_sum.get('decliners', 0)} | 🔥 최고: {tg.get('name', '')} ({'+' if tg.get('change_pct',0)>0 else ''}{tg.get('change_pct',0):.2f}%) | 💧 최저: {tl.get('name', '')} ({tl.get('change_pct',0):.2f}%)")

        append_md_cards("📈 1. 글로벌 거시 경제 & 금융 지표 (Macro Economy & Markets)", econ_cards)
        append_md_cards("🛡️ 2. 군사 · 국방 안보 & 지정학 이슈 (Military & Defense)", mil_cards)
        append_md_cards("🌍 3. 국제 외교 & 글로벌 정세 (World Diplomacy)", world_cards)

        md.append("\n" + "-" * 80)
        md.append("\n## 📄 [SECTION 3] 💡 오늘의 1분 브리핑 & 핵심 시사점\n")

        top_ai = ai_cards[0]["title"] if ai_cards else "AI 기술 진화 가속"
        top_econ = econ_cards[0]["title"] if econ_cards else "글로벌 매크로 불확실성 지속"
        top_mil = mil_cards[0]["title"] if mil_cards else "지정학적 안보 긴장 고조"

        md.append("### ⚡ 오늘 아침 꼭 알아야 할 3대 헤드라인 카드")
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

    @staticmethod
    def _get_heat_class(pct: float) -> str:
        if pct >= 3.0:
            return "heat-p3"
        elif pct >= 1.5:
            return "heat-p2"
        elif pct >= 0.2:
            return "heat-p1"
        elif pct <= -3.0:
            return "heat-m3"
        elif pct <= -1.5:
            return "heat-m2"
        elif pct <= -0.2:
            return "heat-m1"
        else:
            return "heat-zero"

    def _render_heatmap_card(self, market_key: str, market_data: Dict[str, Any], card_meta: Dict[str, Any], date_str: str) -> str:
        c_uid = card_meta["card_uid"]
        g_idx = card_meta["global_idx"]
        c_title = card_meta["title"]
        c_source = card_meta["source"]
        c_favicon = card_meta["favicon"]
        c_time = card_meta["time_ago"]
        c_highlight = card_meta["highlight_badge"]
        c_summary = card_meta["summary"]
        c_link = card_meta["link"]
        c_cta = card_meta["cta_text"]

        search_blob = html_lib.escape(
            f"{c_title} {c_source} {c_summary} {' '.join(card_meta.get('keywords', []))} 히트맵 s&p nasdaq kospi 코스피 증시".lower()
        )

        index_pills = []
        for idx in market_data.get("indices", []):
            pct = idx.get("change_pct", 0.0)
            cls = "pos" if pct > 0 else ("neg" if pct < 0 else "zero")
            sign = "+" if pct > 0 else ""
            p_val = idx.get("price", 0.0)
            p_str = f"{p_val:,.2f}" if p_val >= 100 else f"{p_val:.2f}"
            index_pills.append(
                f'<a href="{idx.get("url", "#")}" target="_blank" rel="noopener noreferrer" class="gn-index-pill" title="{html_lib.escape(idx["name"])}">'
                f'<span class="gn-idx-name">{html_lib.escape(idx["name"])}</span>'
                f'<span class="gn-idx-val">{p_str}</span>'
                f'<span class="gn-idx-chg {cls}">{sign}{pct:.2f}%</span>'
                f'</a>'
            )
        index_strip_html = f'<div class="gn-heatmap-index-strip">{"".join(index_pills)}</div>'

        sector_blocks = []
        for sec_name, sec_stocks in market_data.get("sectors", {}).items():
            tiles_html = []
            for st in sec_stocks:
                pct = st.get("change_pct", 0.0)
                h_cls = self._get_heat_class(pct)
                sign = "+" if pct > 0 else ""
                p_val = st.get("price", 0.0)
                if market_key == "kr" and p_val >= 1000:
                    p_str = f"{p_val:,.0f}원"
                elif market_key == "us":
                    p_str = f"${p_val:,.2f}"
                else:
                    p_str = f"{p_val:,.2f}"

                sym_code = st.get("code") or st["symbol"].replace(".KS", "").replace(".KQ", "")
                tier = st.get("size_tier", "sm")
                tooltip = f"{st['name']} ({st['symbol']}) · 현재가 {p_str} ({sign}{pct:.2f}%)"

                tiles_html.append(
                    f'<a href="{st.get("url", "#")}" target="_blank" rel="noopener noreferrer" '
                    f'class="gn-stock-tile tier-{tier} {h_cls}" data-pct="{pct:.2f}" title="{html_lib.escape(tooltip)}">'
                    f'<span class="tile-sym">{html_lib.escape(sym_code)}</span>'
                    f'<span class="tile-name">{html_lib.escape(st["name"])}</span>'
                    f'<span class="tile-pct">{sign}{pct:.2f}%</span>'
                    f'</a>'
                )
            sector_blocks.append(
                f'<div class="gn-heatmap-sector">'
                f'<div class="gn-sector-header"><span>{html_lib.escape(sec_name)}</span><span>{len(sec_stocks)}종목</span></div>'
                f'<div class="gn-sector-tiles">{"".join(tiles_html)}</div>'
                f'</div>'
            )
        treemap_html = f'<div class="gn-heatmap-treemap-wrap">{"".join(sector_blocks)}</div>'

        sum_info = market_data.get("summary", {})
        adv = sum_info.get("advancers", 0)
        dec = sum_info.get("decliners", 0)
        tot = adv + dec if (adv + dec) > 0 else 1
        adv_pct = round((adv / tot) * 100.0, 1)
        tg = sum_info.get("top_gainer", {})
        tl = sum_info.get("top_loser", {})
        tg_sign = "+" if tg.get("change_pct", 0) > 0 else ""
        tl_sign = "+" if tl.get("change_pct", 0) > 0 else ""

        breadth_html = f"""
        <div class="gn-heatmap-breadth">
            <div class="breadth-stats">
                <span class="breadth-adv" style="color:var(--gn-green);">▲ 상승 {adv}</span>
                <div class="breadth-ratio-bar" title="상승 {adv_pct}% / 하락 {100-adv_pct:.1f}%">
                    <div class="adv-fill" style="width: {adv_pct}%;"></div>
                </div>
                <span class="breadth-dec" style="color:var(--gn-red);">하락 {dec} ▼</span>
            </div>
            <div class="breadth-movers">
                <span class="mover-gainer">🔥 최고 상승: <strong>{html_lib.escape(tg.get("name",""))}</strong> ({tg_sign}{tg.get("change_pct",0):.2f}%)</span>
                <span class="mover-loser">💧 최대 하락: <strong>{html_lib.escape(tl.get("name",""))}</strong> ({tl_sign}{tl.get("change_pct",0):.2f}%)</span>
            </div>
        </div>
        """

        legend_html = """
        <div class="gn-heatmap-legend">
            <span>-3% 이하</span>
            <div class="legend-bar">
                <span class="legend-chip heat-m3" title="-3% 이하"></span>
                <span class="legend-chip heat-m2" title="-1.5% ~ -3%"></span>
                <span class="legend-chip heat-m1" title="-0.2% ~ -1.5%"></span>
                <span class="legend-chip heat-zero" title="보합 ±0.2%"></span>
                <span class="legend-chip heat-p1" title="+0.2% ~ +1.5%"></span>
                <span class="legend-chip heat-p2" title="+1.5% ~ +3%"></span>
                <span class="legend-chip heat-p3" title="+3% 이상"></span>
            </div>
            <span>+3% 이상</span>
        </div>
        """

        tags_chips_html = "".join(
            f'<button type="button" class="gn-tag-chip" onclick="filterByKeyword(\'{html_lib.escape(k)}\')">{html_lib.escape(k)}</button>'
            for k in card_meta.get("keywords", [])
        )

        badge_txt = "HEATMAP US" if market_key == "us" else "HEATMAP KR"
        market_label = "🇺🇸 미국 S&P 500 · NASDAQ" if market_key == "us" else "🇰🇷 한국 KOSPI · KOSDAQ"

        card_html = f"""
        <article class="gn-news-card gn-heatmap-card" id="card-{c_uid}" data-category="econ" data-card-uid="{c_uid}" data-global-idx="{g_idx}" data-search="{search_blob}">
            <div class="gn-card-banner" style="--card-accent: #188038; --card-surface: #e6f4ea;">
                <div class="gn-banner-top">
                    <span class="gn-card-num-badge">{badge_txt}</span>
                    <span class="gn-banner-cat">📊 {market_label}</span>
                </div>
                <div class="gn-banner-quote">
                    <span class="gn-quote-mark">“</span>
                    <span class="gn-quote-text">{html_lib.escape(c_highlight)}</span>
                    <span class="gn-quote-mark">”</span>
                </div>
            </div>
            {index_strip_html}
            <div class="gn-card-body" style="padding-bottom: 0;">
                <div class="gn-card-pub-row">
                    <img src="{c_favicon}" alt="" class="gn-pub-favicon" loading="lazy" onerror="this.style.display=\'none\'">
                    <span class="gn-pub-name">{html_lib.escape(c_source)}</span>
                    <span class="gn-pub-dot">&middot;</span>
                    <span class="gn-pub-time">{html_lib.escape(c_time)}</span>
                </div>
                <h3 class="gn-card-title">
                    <a href="{c_link}" target="_blank" rel="noopener noreferrer">{html_lib.escape(c_title)}</a>
                </h3>
                <p class="gn-card-summary">{html_lib.escape(c_summary)}</p>
                {treemap_html}
                {breadth_html}
                {legend_html}
                <div class="gn-card-tags" style="margin-top: 8px;">
                    {tags_chips_html}
                </div>
            </div>
            <div class="gn-card-footer">
                <button type="button" class="gn-btn-slide-view" onclick="openCardModal({g_idx})" title="3단 카드뉴스 슬라이드로 보기">
                    <span>🃏 카드뉴스 보기</span>
                </button>
                <div class="gn-card-footer-right">
                    <button type="button" class="gn-section-deck-btn" onclick="openHeatmapZoomModal(\'{market_key}\')" title="히트맵 전체화면으로 크게 보기" style="padding: 5px 10px; font-size: 0.78rem;">
                        🔍 크게 보기
                    </button>
                    <button type="button" class="gn-section-deck-btn btn-color-toggle" onclick="toggleHeatmapColorMode()" title="글로벌/한국식 색상 전환" style="padding: 5px 10px; font-size: 0.78rem;">
                        🎨 색상전환
                    </button>
                    <button type="button" class="gn-btn-bookmark" data-uid="{c_uid}" onclick="toggleBookmark(\'{c_uid}\', this)" title="북마크에 저장" aria-label="북마크 저장">
                        🔖
                    </button>
                    <a href="{c_link}" target="_blank" rel="noopener noreferrer" class="gn-btn-fullcoverage" title="외부 증시맵 열기">
                        <span>{html_lib.escape(c_cta)}</span>
                        <span aria-hidden="true">&nearr;</span>
                    </a>
                </div>
            </div>
        </article>
        """
        return card_html

    def build_html(self, tech_data: Dict[str, Any], econ_data: Dict[str, Any], scripts: Dict[str, str], affirmation: str, date_str: str) -> str:
        cache_ts = int(datetime.now().timestamp())
        # 0. 주식 히트맵 데이터 로드
        stock_heatmaps = econ_data.get("stock_heatmaps")
        if not stock_heatmaps:
            try:
                from src.collectors.stock_heatmap_collector import StockHeatmapCollector
                stock_heatmaps = StockHeatmapCollector(self.output_dir).collect_all()
            except Exception:
                stock_heatmaps = {}

        # 1. 섹션별 카드뉴스 데이터 생성
        ai_cards = enrich_section_items(tech_data.get("ai_headlines", [])[:6], "ai")
        tech_cards = enrich_section_items(tech_data.get("tech_headlines", [])[:6], "tech")
        paper_cards = enrich_section_items(tech_data.get("arxiv_papers", [])[:6], "paper")
        yt_cards = enrich_section_items(tech_data.get("youtube_picks", [])[:6], "youtube")
        tools_cards = enrich_section_items(tech_data.get("ai_tools", [])[:6], "tools")
        econ_cards = enrich_section_items(econ_data.get("economy_headlines", [])[:6], "econ")
        mil_cards = enrich_section_items(econ_data.get("military_headlines", [])[:6], "military")
        world_cards = enrich_section_items(econ_data.get("world_headlines", [])[:6], "world")

        # 1-1. 주식 히트맵 카드 생성 (US & KR)
        heatmap_cards: List[Dict[str, Any]] = []
        if stock_heatmaps and "us" in stock_heatmaps and "kr" in stock_heatmaps:
            us_data = stock_heatmaps["us"]
            kr_data = stock_heatmaps["kr"]
            us_sum = us_data.get("summary", {})
            kr_sum = kr_data.get("summary", {})

            us_tg = us_sum.get("top_gainer", {})
            us_tl = us_sum.get("top_loser", {})
            kr_tg = kr_sum.get("top_gainer", {})
            kr_tl = kr_sum.get("top_loser", {})

            us_tg_sign = "+" if us_tg.get("change_pct", 0) > 0 else ""
            us_tl_sign = "+" if us_tl.get("change_pct", 0) > 0 else ""
            kr_tg_sign = "+" if kr_tg.get("change_pct", 0) > 0 else ""
            kr_tl_sign = "+" if kr_tl.get("change_pct", 0) > 0 else ""

            us_hc = {
                "card_index": 1,
                "card_uid": f"{date_str}-econ-heatmap-us",
                "category_id": "econ",
                "category_name": "글로벌 거시 경제 & 금융 시장",
                "category_en": "MACRO & MARKETS",
                "category_icon": "📈",
                "category_color": "#188038",
                "title": "미국 S&P 500 · NASDAQ 빅테크 섹터 히트맵",
                "source": "Yahoo Finance · S&P 500",
                "favicon": "https://www.google.com/s2/favicons?domain=finance.yahoo.com&sz=64",
                "time_ago": "오늘 실시간",
                "highlight_badge": "빅테크·AI 주도 강세 속 섹터별 랠리",
                "summary": f"미국 S&P 500, NASDAQ, 다우존스 및 필라델피아 반도체 지수 동향과 빅테크 6대 기업(NVDA, AAPL 등) 및 주요 섹터의 실시간 등락률 히트맵입니다. (상승 {us_sum.get('advancers', 0)} / 하락 {us_sum.get('decliners', 0)})",
                "bullet_points": [
                    "📌 미국 지수 동향: S&P 500 및 나스닥 주요 지수 중심의 기술주 모멘텀 지속",
                    f"🔍 주도 종목 진단: 최고 상승 {us_tg.get('name', '')} ({us_tg_sign}{us_tg.get('change_pct', 0):.2f}%), 최대 하락 {us_tl.get('name', '')} ({us_tl_sign}{us_tl.get('change_pct', 0):.2f}%)",
                    "🎯 글로벌 투자 관점: 미 연준 통화정책과 빅테크 실적 발표에 따른 포트폴리오 영향 점검"
                ],
                "keywords": ["#미국증시히트맵", "#S&P500", "#빅테크", "#AI반도체"],
                "link": "https://finviz.com/map.ashx",
                "cta_text": "Finviz 히트맵 보기",
                "related_articles": []
            }

            kr_hc = {
                "card_index": 2,
                "card_uid": f"{date_str}-econ-heatmap-kr",
                "category_id": "econ",
                "category_name": "글로벌 거시 경제 & 금융 시장",
                "category_en": "MACRO & MARKETS",
                "category_icon": "📈",
                "category_color": "#188038",
                "title": "한국 KOSPI · KOSDAQ 시가총액 히트맵",
                "source": "Naver Finance · KRX",
                "favicon": "https://www.google.com/s2/favicons?domain=finance.naver.com&sz=64",
                "time_ago": "오늘 실시간",
                "highlight_badge": "코스피 2,600선 공방 및 반도체·방산 차별화",
                "summary": f"코스피, 코스닥 지수 및 원/달러 환율 흐름과 반도체(삼성전자, SK하이닉스), 2차전지, 바이오, 방산 등 시총 상위 종목의 등락률 분포 히트맵입니다. (상승 {kr_sum.get('advancers', 0)} / 하락 {kr_sum.get('decliners', 0)})",
                "bullet_points": [
                    "📌 국내 지수 진단: 코스피, 코스닥 지수 및 원/달러 환율 연동 수급 진단",
                    f"🔍 주도 종목 진단: 최고 상승 {kr_tg.get('name', '')} ({kr_tg_sign}{kr_tg.get('change_pct', 0):.2f}%), 최대 하락 {kr_tl.get('name', '')} ({kr_tl_sign}{kr_tl.get('change_pct', 0):.2f}%)",
                    "🎯 국내 투자 관점: 외국인·기관 수급 편중 및 수출 주도 섹터 실적 모멘텀 주시"
                ],
                "keywords": ["#한국증시히트맵", "#코스피", "#K반도체", "#원달러환율"],
                "link": "https://finance.naver.com/",
                "cta_text": "네이버 증시맵 보기",
                "related_articles": []
            }
            heatmap_cards = [us_hc, kr_hc]

        sections_config = [
            {
                "id": "ai",
                "title": "인공지능 & 머신러닝",
                "subtitle": "AI & Frontier LLM · 모델 아키텍처 · 오픈소스 생태계",
                "icon": "🤖",
                "color": "#1a73e8",
                "badge_bg": "#e8f0fe",
                "cards": ai_cards,
                "cta": "기사 읽기"
            },
            {
                "id": "tech",
                "title": "빅테크 · 반도체 & 인프라",
                "subtitle": "BigTech · AI 반도체(HBM/ASIC) · 클라우드 데이터센터",
                "icon": "💻",
                "color": "#007b83",
                "badge_bg": "#e4f7fb",
                "cards": tech_cards,
                "cta": "기사 읽기"
            },
            {
                "id": "paper",
                "title": "최신 AI/ML 연구 논문",
                "subtitle": "ArXiv CS.AI / CS.LG / CS.CL 프리프린트 핵심 요약",
                "icon": "📚",
                "color": "#185abc",
                "badge_bg": "#e8f0fe",
                "cards": paper_cards,
                "cta": "논문(PDF) 보기"
            },
            {
                "id": "youtube",
                "title": "화제의 테크 유튜브 트렌드",
                "subtitle": "Two Minute Papers · Yannic Kilcher · 국내외 AI/테크 영상 Pick",
                "icon": "📺",
                "color": "#d93025",
                "badge_bg": "#fce8e6",
                "cards": yt_cards,
                "cta": "유튜브 시청"
            },
            {
                "id": "tools",
                "title": "AI/ML 신기술 툴 & 기법",
                "subtitle": "New AI Tools & Techniques · 오픈소스 프레임워크 · 최신 학습/추론 최적화 기법",
                "icon": "🛠️",
                "color": "#7627bb",
                "badge_bg": "#f3e8fd",
                "cards": tools_cards,
                "cta": "도구/기술 살펴보기"
            },
            {
                "id": "econ",
                "title": "글로벌 거시 경제 & 금융 시장",
                "subtitle": "Macro Economy · 미 연준 기준금리 · 원/달러 환율 · 글로벌 증시",
                "icon": "📈",
                "color": "#188038",
                "badge_bg": "#e6f4ea",
                "cards": econ_cards,
                "cta": "기사 읽기"
            },
            {
                "id": "military",
                "title": "군사 · 국방 안보 & 지정학",
                "subtitle": "Military & Defense · 글로벌 방산 협력 · 지역 안보 지형",
                "icon": "🛡️",
                "color": "#b06000",
                "badge_bg": "#fef7e0",
                "cards": mil_cards,
                "cta": "기사 읽기"
            },
            {
                "id": "world",
                "title": "국제 외교 & 세계 정세",
                "subtitle": "World Diplomacy · 주요국 정상회담 · 글로벌 통상 및 다자 외교",
                "icon": "🌍",
                "color": "#1967d2",
                "badge_bg": "#e8f0fe",
                "cards": world_cards,
                "cta": "기사 읽기"
            },
        ]

        # 전체 카드 리스트 및 글로벌 인덱스 부여 (모달 슬라이드 뷰어 연동용)
        all_cards: List[Dict[str, Any]] = []
        for sec in sections_config:
            if sec["id"] == "econ" and heatmap_cards:
                for hc in heatmap_cards:
                    hc["global_idx"] = len(all_cards)
                    all_cards.append(hc)
            for c in sec["cards"]:
                c["global_idx"] = len(all_cards)
                c["card_uid"] = f"{date_str}-{sec['id']}-{c['card_index']}"
                c["cta_text"] = sec["cta"]
                all_cards.append(c)

        total_cards = len(all_cards)

        # 한국어 날짜 포맷팅 (예: 2026년 10월 16일 금요일)
        weekday_ko = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        try:
            dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date_ko = f"{dt_obj.year}년 {dt_obj.month}월 {dt_obj.day}일 {weekday_ko[dt_obj.weekday()]}"
            short_date_ko = f"{dt_obj.month}월 {dt_obj.day}일 ({weekday_ko[dt_obj.weekday()][0]})"
        except Exception:
            formatted_date_ko = date_str
            short_date_ko = date_str

        # 오늘의 대표 키워드 추출 (상위 빈도 해시태그 8개)
        tag_counts: Dict[str, int] = {}
        for c in all_cards:
            for t in c.get("keywords", []):
                tag_counts[t] = tag_counts.get(t, 0) + 1
        top_keywords = [k for k, _ in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:8]]
        if not top_keywords:
            top_keywords = ["#생성형AI", "#AI반도체", "#기준금리", "#원달러환율", "#글로벌방산", "#정상외교"]

        # 대표 3대 헤드라인
        top_ai_card = ai_cards[0] if ai_cards else (all_cards[0] if all_cards else {"title": "AI 기술 진화 가속", "source": "Google News", "link": "#", "global_idx": 0})
        top_econ_card = econ_cards[0] if econ_cards else (all_cards[0] if all_cards else {"title": "글로벌 매크로 불확실성 지속", "source": "Google News", "link": "#", "global_idx": 0})
        top_mil_card = mil_cards[0] if mil_cards else (all_cards[0] if all_cards else {"title": "지정학적 안보 긴장 고조", "source": "Google News", "link": "#", "global_idx": 0})

        # 오늘의 대표 카드뉴스 슬라이드 데크 (Hero Carousel용 8~9장 구성)
        hero_slides_data = []
        # Slide 0: Cover Card
        hero_slides_data.append({
            "slide_type": "cover",
            "badge": "TODAY'S EDITION COVER",
            "category_name": "오늘의 브리핑 표지",
            "icon": "📰",
            "color": "#1a73e8",
            "title": f"{formatted_date_ko} 모닝 카드뉴스 브리핑",
            "source": "Google News Daily Briefing",
            "time_ago": "09:00 KST 발행",
            "summary": f"바쁜 아침 5분 만에 읽는 글로벌 인텔리전스 카드뉴스입니다. AI·반도체·논문·유튜브 트렌드부터 거시경제·안보·외교까지 총 {total_cards}개의 핵심 뉴스를 카드로 확인하세요.",
            "bullets": [
                f"🤖 AI/기술 대표: {top_ai_card.get('title', '')}",
                f"📈 경제/금융 대표: {top_econ_card.get('title', '')}",
                f"🛡️ 안보/세계 대표: {top_mil_card.get('title', '')}"
            ],
            "keywords": top_keywords[:4],
            "link": "#section-ai",
            "global_idx": 0,
            "thumbnail": ""
        })

        # 각 섹션의 1위 카드를 Hero Slide Deck에 추가
        for sec in sections_config:
            if sec["cards"]:
                top_c = sec["cards"][0]
                hero_slides_data.append({
                    "slide_type": "story",
                    "badge": f"TOP {sec['id'].upper()} STORY",
                    "category_name": sec["title"],
                    "icon": sec["icon"],
                    "color": sec["color"],
                    "title": top_c["title"],
                    "source": top_c["source"],
                    "favicon": top_c["favicon"],
                    "time_ago": top_c["time_ago"],
                    "summary": top_c["summary"],
                    "bullets": top_c["bullet_points"],
                    "keywords": top_c["keywords"],
                    "link": top_c["link"],
                    "global_idx": top_c["global_idx"],
                    "thumbnail": top_c.get("thumbnail", ""),
                    "cta_text": sec["cta"]
                })

        # 마지막 Slide: 오늘의 관전 포인트 & 아침 긍정 확언 카드
        hero_slides_data.append({
            "slide_type": "outro",
            "badge": "WATCHPOINTS & AFFIRMATION",
            "category_name": "오늘의 관전 포인트 & 긍정 확언",
            "icon": "✨",
            "color": "#188038",
            "title": f"\"{affirmation}\"",
            "source": "Daily Morning Meditation",
            "time_ago": "오늘의 마인드셋",
            "summary": "오늘 하루 비즈니스와 일상을 성공으로 이끄는 3대 핵심 체크리스트와 아침 긍정 확언입니다.",
            "bullets": [
                "🤖 엔지니어링/AI: 글로벌 프론티어 모델 성능 및 AI 반도체 공급망 동향 모니터링",
                "📈 경제/투자: 미 연준 금리 시그널 및 원/달러 환율 단기 변동성 주시",
                "🌍 안보/지정학: 주요국 외교 정상회담 및 글로벌 방산·통상 정책 체크"
            ],
            "keywords": ["#긍정확언", "#오늘의관전포인트", "#모닝루틴"],
            "link": "#affirmationSection",
            "global_idx": 0,
            "thumbnail": ""
        })

        # Hero Carousel HTML 빌드
        total_hero_slides = len(hero_slides_data)
        hero_progress_bars_html = ""
        hero_slides_html = ""

        for s_idx, s in enumerate(hero_slides_data):
            active_cls = "active" if s_idx == 0 else ""
            hero_progress_bars_html += f"""
            <button class="deck-progress-seg {active_cls}" onclick="goToHeroSlide({s_idx})" aria-label="슬라이드 {s_idx + 1} 이동">
                <span class="deck-progress-fill"></span>
            </button>
            """
            s_title_esc = html_lib.escape(s["title"])
            s_source_esc = html_lib.escape(s["source"])
            s_summary_esc = html_lib.escape(s["summary"])
            bullets_html = "".join(f"<li>{html_lib.escape(b)}</li>" for b in s.get("bullets", []))
            tags_html = "".join(
                f'<button class="gn-tag-chip" onclick="filterByKeyword(\'{html_lib.escape(k)}\')">{html_lib.escape(k)}</button>'
                for k in s.get("keywords", [])
            )

            thumb_block = ""
            if s.get("thumbnail"):
                thumb_block = f"""
                <div class="deck-slide-media">
                    <img src="{html_lib.escape(s['thumbnail'])}" alt="{s_title_esc}" loading="lazy" onerror="this.parentElement.style.display='none'">
                    <span class="deck-media-badge">▶ VIDEO PICK</span>
                </div>
                """

            favicon_img = ""
            if s.get("favicon"):
                favicon_img = f'<img src="{html_lib.escape(s["favicon"])}" class="gn-pub-favicon" alt="" loading="lazy" onerror="this.style.display=\'none\'">'

            if s["slide_type"] == "cover":
                action_btns = f"""
                <button class="gn-deck-action-primary" onclick="nextHeroSlide()">첫 번째 카드뉴스 시작 &rarr;</button>
                <button class="gn-deck-action-secondary" onclick="openCardModal(0)">🃏 전체화면 슬라이드 열기</button>
                """
            elif s["slide_type"] == "outro":
                action_btns = f"""
                <button class="gn-deck-action-primary" onclick="speakAffirmation()">🔊 오늘의 확언 음성 듣기</button>
                <button class="gn-deck-action-secondary" onclick="goToHeroSlide(0)">↺ 처음으로 돌아가기</button>
                """
            else:
                action_btns = f"""
                <a href="{html_lib.escape(s['link'])}" target="_blank" rel="noopener noreferrer" class="gn-deck-action-primary">{html_lib.escape(s.get('cta_text', '원문 읽기'))} &nearr;</a>
                <button class="gn-deck-action-secondary" onclick="openCardModal({s['global_idx']})">🃏 3단 카드뉴스 상세보기</button>
                """

            hero_slides_html += f"""
            <div class="deck-slide {active_cls}" data-slide-idx="{s_idx}" style="--slide-accent: {s['color']};">
                <div class="deck-slide-topbar">
                    <div class="deck-cat-pill">
                        <span>{s['icon']}</span>
                        <span>{html_lib.escape(s['category_name'])}</span>
                    </div>
                    <span class="deck-counter-badge">CARD {s_idx + 1:02d} / {total_hero_slides:02d}</span>
                </div>
                {thumb_block}
                <div class="deck-pub-meta">
                    {favicon_img}
                    <span class="gn-pub-name">{s_source_esc}</span>
                    <span class="gn-pub-dot">&middot;</span>
                    <span class="gn-pub-time">{html_lib.escape(s['time_ago'])}</span>
                </div>
                <h2 class="deck-slide-title">{s_title_esc}</h2>
                <p class="deck-slide-summary">{s_summary_esc}</p>
                <ul class="deck-slide-bullets">
                    {bullets_html}
                </ul>
                <div class="deck-slide-footer">
                    <div class="deck-tags-wrap">{tags_html}</div>
                    <div class="deck-actions-wrap">{action_btns}</div>
                </div>
            </div>
            """

        # 각 섹션별 카드 그리드 HTML 생성
        sections_html = ""
        for sec in sections_config:
            sec_id = sec["id"]
            cards = sec["cards"]
            if not cards and not (sec_id == "econ" and heatmap_cards):
                continue

            first_global_idx = heatmap_cards[0]["global_idx"] if (sec_id == "econ" and heatmap_cards) else (cards[0]["global_idx"] if cards else 0)
            cards_grid_html = ""

            for c in cards:
                c_title = html_lib.escape(c["title"])
                c_source = html_lib.escape(c["source"])
                c_link = html_lib.escape(c["link"])
                c_summary = html_lib.escape(c["summary"])
                c_highlight = html_lib.escape(c["highlight_badge"])
                c_time = html_lib.escape(c["time_ago"])
                c_favicon = html_lib.escape(c["favicon"])
                c_uid = html_lib.escape(c["card_uid"])
                g_idx = c["global_idx"]
                c_idx = c["card_index"]

                # 검색용 통합 텍스트 속성
                search_blob = html_lib.escape(
                    f"{c['title']} {c['source']} {c['summary']} {' '.join(c['keywords'])} {sec['title']}".lower()
                )

                # 비주얼 헤더: 유튜브 썸네일 또는 구글 뉴스 스타일 카드 그래픽 배너
                if c.get("thumbnail"):
                    visual_header_html = f"""
                    <div class="gn-card-media">
                        <img src="{html_lib.escape(c['thumbnail'])}" alt="{c_title}" loading="lazy" onerror="this.parentElement.classList.add('media-fallback')">
                        <div class="gn-media-overlay">
                            <span class="gn-card-num-badge">CARD {c_idx:02d}</span>
                            <span class="gn-yt-play-pill">▶ YouTube</span>
                        </div>
                    </div>
                    """
                else:
                    extra_meta = ""
                    if sec_id == "paper" and c.get("primary_category"):
                        extra_meta = f'<span class="gn-banner-subtag">{html_lib.escape(c["primary_category"])}</span>'
                    visual_header_html = f"""
                    <div class="gn-card-banner" style="--card-accent: {sec['color']}; --card-surface: {sec['badge_bg']};">
                        <div class="gn-banner-top">
                            <span class="gn-card-num-badge">CARD {c_idx:02d}</span>
                            <span class="gn-banner-cat">{sec['icon']} {html_lib.escape(c['category_en'])} {extra_meta}</span>
                        </div>
                        <div class="gn-banner-quote">
                            <span class="gn-quote-mark">“</span>
                            <span class="gn-quote-text">{c_highlight}</span>
                            <span class="gn-quote-mark">”</span>
                        </div>
                    </div>
                    """

                tags_chips_html = "".join(
                    f'<button type="button" class="gn-tag-chip" onclick="filterByKeyword(\'{html_lib.escape(k)}\')">{html_lib.escape(k)}</button>'
                    for k in c.get("keywords", [])
                )

                # 관련 보도 클러스터 (Google News Full Coverage style)
                related_html = ""
                if c.get("related_articles"):
                    rel_items = ""
                    for r_art in c["related_articles"][:2]:
                        r_title = html_lib.escape(r_art.get("title", ""))
                        r_src = html_lib.escape(r_art.get("source", ""))
                        r_lnk = html_lib.escape(r_art.get("link", "#"))
                        rel_items += f"""
                        <li class="gn-related-item">
                            <a href="{r_lnk}" target="_blank" rel="noopener noreferrer" class="gn-related-link">{r_title}</a>
                            <span class="gn-related-src">{r_src}</span>
                        </li>
                        """
                    related_html = f"""
                    <div class="gn-related-cluster">
                        <div class="gn-related-label">관련 보도 · 심층 맥락</div>
                        <ul class="gn-related-list">{rel_items}</ul>
                    </div>
                    """

                cards_grid_html += f"""
                <article class="gn-news-card" id="card-{c_uid}" data-category="{sec_id}" data-card-uid="{c_uid}" data-global-idx="{g_idx}" data-search="{search_blob}">
                    {visual_header_html}
                    <div class="gn-card-body">
                        <div class="gn-card-pub-row">
                            <img src="{c_favicon}" alt="" class="gn-pub-favicon" loading="lazy" onerror="this.style.display='none'">
                            <span class="gn-pub-name">{c_source}</span>
                            <span class="gn-pub-dot">&middot;</span>
                            <span class="gn-pub-time">{c_time}</span>
                        </div>
                        <h3 class="gn-card-title">
                            <a href="{c_link}" target="_blank" rel="noopener noreferrer">{c_title}</a>
                        </h3>
                        <p class="gn-card-summary">{c_summary}</p>
                        <div class="gn-card-tags">
                            {tags_chips_html}
                        </div>
                        {related_html}
                    </div>
                    <div class="gn-card-footer">
                        <button type="button" class="gn-btn-slide-view" onclick="openCardModal({g_idx})" title="3단 카드뉴스 슬라이드로 보기">
                            <span>🃏 카드뉴스 보기</span>
                        </button>
                        <div class="gn-card-footer-right">
                            <button type="button" class="gn-btn-bookmark" data-uid="{c_uid}" onclick="toggleBookmark('{c_uid}', this)" title="북마크에 저장" aria-label="북마크 저장">
                                🔖
                            </button>
                            <a href="{c_link}" target="_blank" rel="noopener noreferrer" class="gn-btn-fullcoverage" title="원문 전체 기사 열기">
                                <span>{html_lib.escape(sec['cta'])}</span>
                                <span aria-hidden="true">&nearr;</span>
                            </a>
                        </div>
                    </div>
                </article>
                """

            heatmap_grid_html = ""
            if sec_id == "econ" and heatmap_cards and len(heatmap_cards) >= 2:
                us_card_html = self._render_heatmap_card("us", stock_heatmaps.get("us", {}), heatmap_cards[0], date_str)
                kr_card_html = self._render_heatmap_card("kr", stock_heatmaps.get("kr", {}), heatmap_cards[1], date_str)
                heatmap_grid_html = f"""
                <div class="gn-heatmap-card-grid">
                    {us_card_html}
                    {kr_card_html}
                </div>
                """

            sec_card_count = len(cards) + (len(heatmap_cards) if sec_id == 'econ' else 0)
            sections_html += f"""
            <section class="gn-category-section" id="section-{sec_id}" data-section="{sec_id}">
                <div class="gn-section-header">
                    <div class="gn-section-title-group">
                        <span class="gn-section-icon" style="background: {sec['badge_bg']}; color: {sec['color']};">{sec['icon']}</span>
                        <div>
                            <h2 class="gn-section-title">{html_lib.escape(sec['title'])}</h2>
                            <p class="gn-section-subtitle">{html_lib.escape(sec['subtitle'])}</p>
                        </div>
                    </div>
                    <div class="gn-section-actions">
                        <span class="gn-section-count">{sec_card_count}개 카드</span>
                        <button type="button" class="gn-section-deck-btn" onclick="openCardModal({first_global_idx})">
                            📱 슬라이드 연속보기 &rsaquo;
                        </button>
                    </div>
                </div>
                {heatmap_grid_html}
                <div class="gn-card-grid">
                    {cards_grid_html}
                </div>
            </section>
            """

        # 상단 트렌딩 해시태그 칩 HTML
        trending_chips_html = "".join(
            f'<button type="button" class="gn-trending-chip" onclick="filterByKeyword(\'{html_lib.escape(k)}\')">{html_lib.escape(k)}</button>'
            for k in top_keywords
        )

        # 대본 HTML 변환
        ko_script_html = html_lib.escape(scripts.get('ko', '')).replace('\n', '<br><br>')
        en_script_html = html_lib.escape(scripts.get('en', '')).replace('\n', '<br><br>')
        zh_script_html = html_lib.escape(scripts.get('zh', '')).replace('\n', '<br><br>')

        # 모달 뷰어용 전체 카드 JSON 직렬화
        modal_cards_data = []
        for c in all_cards:
            modal_cards_data.append({
                "global_idx": c["global_idx"],
                "card_index": c["card_index"],
                "card_uid": c["card_uid"],
                "category_id": c["category_id"],
                "category_name": c["category_name"],
                "category_en": c["category_en"],
                "category_icon": c["category_icon"],
                "category_color": c["category_color"],
                "title": c["title"],
                "source": c["source"],
                "favicon": c["favicon"],
                "time_ago": c["time_ago"],
                "highlight_badge": c["highlight_badge"],
                "summary": c["summary"],
                "bullet_points": c["bullet_points"],
                "keywords": c["keywords"],
                "link": c["link"],
                "thumbnail": c.get("thumbnail", ""),
                "cta_text": c.get("cta_text", "원문 보기"),
                "related_articles": c.get("related_articles", [])
            })
        modal_cards_json = json.dumps(modal_cards_data, ensure_ascii=False)

        html_content = f"""<!DOCTYPE html>
<html lang="ko" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{date_str} 데일리 모닝 브리핑 - Google News 스타일 AI·테크·경제·세계 카드뉴스 및 5분 다국어 음성 브리핑">
    <title>Google News Daily Briefing - {date_str} 카드뉴스 에디션</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            /* Google News Material Design 3 Light Theme Tokens */
            --gn-bg: #f8f9fa;
            --gn-surface: #ffffff;
            --gn-surface-variant: #f1f3f4;
            --gn-surface-hover: #f8fafd;
            --gn-text-primary: #1f1f1f;
            --gn-text-secondary: #444746;
            --gn-text-muted: #5f6368;
            --gn-border: #dadce0;
            --gn-border-subtle: #e8eaed;
            --gn-blue: #1a73e8;
            --gn-blue-hover: #1557b0;
            --gn-blue-surface: #e8f0fe;
            --gn-blue-text: #1967d2;
            --gn-red: #d93025;
            --gn-yellow: #f9ab00;
            --gn-green: #188038;
            --gn-shadow-sm: 0 1px 2px 0 rgba(60,64,67,0.1), 0 1px 3px 1px rgba(60,64,67,0.06);
            --gn-shadow-md: 0 4px 12px rgba(60,64,67,0.12), 0 1px 3px rgba(60,64,67,0.08);
            --gn-shadow-lg: 0 12px 28px rgba(60,64,67,0.18), 0 4px 10px rgba(60,64,67,0.1);
            --gn-radius-card: 16px;
            --gn-radius-pill: 999px;
            --gn-font-sans: "Pretendard", "Noto Sans KR", "Inter", -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Segoe UI", Roboto, sans-serif;
        }}

        [data-theme="dark"] {{
            --gn-bg: #131314;
            --gn-surface: #1e1f20;
            --gn-surface-variant: #282a2c;
            --gn-surface-hover: #2d2f31;
            --gn-text-primary: #e3e3e3;
            --gn-text-secondary: #c4c7c5;
            --gn-text-muted: #8e918f;
            --gn-border: #3c4043;
            --gn-border-subtle: #2d2f31;
            --gn-blue: #8ab4f8;
            --gn-blue-hover: #aecbfa;
            --gn-blue-surface: rgba(138, 180, 248, 0.16);
            --gn-blue-text: #8ab4f8;
            --gn-shadow-sm: 0 1px 3px rgba(0,0,0,0.4);
            --gn-shadow-md: 0 6px 16px rgba(0,0,0,0.5);
            --gn-shadow-lg: 0 16px 36px rgba(0,0,0,0.65);
        }}

        * {{
            box-sizing: border-box;
        }}

        html {{
            scroll-behavior: smooth;
        }}

        body {{
            margin: 0;
            padding: 0;
            font-family: var(--gn-font-sans);
            background-color: var(--gn-bg);
            color: var(--gn-text-primary);
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
            transition: background-color 0.2s ease, color 0.2s ease;
        }}

        /* ==========================================================================
           Google News Sticky Top App Bar & Category Navigation
           ========================================================================== */
        .gn-app-header {{
            position: sticky;
            top: 0;
            z-index: 100;
            background-color: var(--gn-surface);
            border-bottom: 1px solid var(--gn-border-subtle);
            box-shadow: 0 1px 4px rgba(60,64,67,0.06);
        }}

        .gn-top-row {{
            max-width: 1360px;
            margin: 0 auto;
            padding: 10px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
        }}

        .gn-brand {{
            display: flex;
            align-items: center;
            gap: 10px;
            text-decoration: none;
            color: var(--gn-text-primary);
            flex-shrink: 0;
        }}

        .gn-brand-icon {{
            width: 34px;
            height: 34px;
            border-radius: 8px;
            background: var(--gn-blue-surface);
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }}

        .gn-brand-text {{
            display: flex;
            align-items: baseline;
            gap: 6px;
            font-size: 1.32rem;
            font-weight: 700;
            letter-spacing: -0.4px;
        }}

        .gn-g-blue {{ color: #4285F4; }}
        .gn-g-red {{ color: #EA4335; }}
        .gn-g-yellow {{ color: #FBBC04; }}
        .gn-g-green {{ color: #34A853; }}

        .gn-brand-news {{
            color: var(--gn-text-secondary);
            font-weight: 600;
        }}

        .gn-brand-badge {{
            font-size: 0.78rem;
            font-weight: 700;
            padding: 3px 9px;
            border-radius: var(--gn-radius-pill);
            background: var(--gn-blue-surface);
            color: var(--gn-blue-text);
            margin-left: 4px;
        }}

        /* Google News Omnibox Search */
        .gn-search-box {{
            flex: 1;
            max-width: 540px;
            position: relative;
            display: flex;
            align-items: center;
        }}

        .gn-search-icon {{
            position: absolute;
            left: 16px;
            color: var(--gn-text-muted);
            font-size: 0.95rem;
            pointer-events: none;
        }}

        .gn-search-input {{
            width: 100%;
            height: 44px;
            padding: 0 40px 0 44px;
            border-radius: var(--gn-radius-pill);
            border: 1px solid transparent;
            background-color: var(--gn-surface-variant);
            color: var(--gn-text-primary);
            font-size: 0.95rem;
            font-family: inherit;
            transition: all 0.2s ease;
            outline: none;
        }}

        .gn-search-input:focus {{
            background-color: var(--gn-surface);
            border-color: var(--gn-blue);
            box-shadow: var(--gn-shadow-sm);
        }}

        .gn-search-clear {{
            position: absolute;
            right: 12px;
            background: none;
            border: none;
            color: var(--gn-text-muted);
            font-size: 1rem;
            cursor: pointer;
            display: none;
            padding: 4px 6px;
            border-radius: 50%;
        }}

        .gn-search-clear:hover {{
            background: rgba(128,128,128,0.15);
        }}

        /* Top Right Controls */
        .gn-top-actions {{
            display: flex;
            align-items: center;
            gap: 8px;
            flex-shrink: 0;
        }}

        .gn-view-switcher {{
            display: inline-flex;
            background: var(--gn-surface-variant);
            padding: 3px;
            border-radius: var(--gn-radius-pill);
            gap: 2px;
        }}

        .gn-view-btn {{
            border: none;
            background: transparent;
            color: var(--gn-text-secondary);
            padding: 6px 12px;
            border-radius: var(--gn-radius-pill);
            font-size: 0.83rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.15s ease;
            font-family: inherit;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }}

        .gn-view-btn.active {{
            background: var(--gn-surface);
            color: var(--gn-blue-text);
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}

        .gn-icon-btn {{
            height: 38px;
            padding: 0 14px;
            border-radius: var(--gn-radius-pill);
            border: 1px solid var(--gn-border);
            background: var(--gn-surface);
            color: var(--gn-text-secondary);
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            text-decoration: none;
            transition: all 0.15s ease;
            font-family: inherit;
        }}

        .gn-icon-btn:hover {{
            background: var(--gn-surface-variant);
            color: var(--gn-blue-text);
            border-color: var(--gn-blue);
        }}

        /* Category Navigation Bar */
        .gn-nav-bar {{
            max-width: 1360px;
            margin: 0 auto;
            padding: 0 24px;
            display: flex;
            align-items: center;
            gap: 4px;
            overflow-x: auto;
            scrollbar-width: none;
        }}

        .gn-nav-bar::-webkit-scrollbar {{
            display: none;
        }}

        .gn-nav-tab {{
            position: relative;
            background: transparent;
            border: none;
            color: var(--gn-text-muted);
            font-family: inherit;
            font-size: 0.9rem;
            font-weight: 600;
            padding: 12px 16px;
            cursor: pointer;
            white-space: nowrap;
            transition: color 0.15s ease;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}

        .gn-nav-tab:hover {{
            color: var(--gn-text-primary);
        }}

        .gn-nav-tab.active {{
            color: var(--gn-blue-text);
            font-weight: 700;
        }}

        .gn-nav-tab.active::after {{
            content: "";
            position: absolute;
            left: 12px;
            right: 12px;
            bottom: 0;
            height: 3px;
            background-color: var(--gn-blue);
            border-radius: 3px 3px 0 0;
        }}

        .gn-saved-count {{
            font-size: 0.72rem;
            background: var(--gn-blue-surface);
            color: var(--gn-blue-text);
            padding: 1px 6px;
            border-radius: 10px;
            font-weight: 700;
        }}

        /* ==========================================================================
           Main Container & Google News "Your Briefing" Hero Section
           ========================================================================== */
        .gn-main {{
            max-width: 1360px;
            margin: 0 auto;
            padding: 28px 24px 64px 24px;
        }}

        .gn-briefing-header {{
            display: flex;
            flex-wrap: wrap;
            align-items: flex-end;
            justify-content: space-between;
            gap: 16px;
            margin-bottom: 24px;
        }}

        .gn-briefing-title-wrap h1 {{
            margin: 0 0 6px 0;
            font-size: 2rem;
            font-weight: 800;
            letter-spacing: -0.6px;
            color: var(--gn-text-primary);
        }}

        .gn-briefing-meta {{
            font-size: 0.95rem;
            color: var(--gn-text-muted);
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }}

        .gn-trending-bar {{
            display: flex;
            align-items: center;
            gap: 6px;
            flex-wrap: wrap;
        }}

        .gn-trending-label {{
            font-size: 0.82rem;
            font-weight: 700;
            color: var(--gn-text-muted);
            margin-right: 4px;
        }}

        .gn-trending-chip {{
            border: 1px solid var(--gn-border);
            background: var(--gn-surface);
            color: var(--gn-text-secondary);
            padding: 5px 12px;
            border-radius: var(--gn-radius-pill);
            font-size: 0.82rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.15s ease;
            font-family: inherit;
        }}

        .gn-trending-chip:hover,
        .gn-trending-chip.active {{
            background: var(--gn-blue-surface);
            color: var(--gn-blue-text);
            border-color: var(--gn-blue);
        }}

        /* Hero 2-Column Grid: Left = Card News Slide Deck, Right = Briefing Widgets */
        .gn-hero-grid {{
            display: grid;
            grid-template-columns: 1.35fr 1fr;
            gap: 24px;
            margin-bottom: 40px;
            align-items: stretch;
        }}

        /* Interactive Card News Slide Deck */
        .gn-hero-deck-card {{
            background: var(--gn-surface);
            border: 1px solid var(--gn-border-subtle);
            border-radius: 20px;
            box-shadow: var(--gn-shadow-sm);
            padding: 22px 26px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            position: relative;
            overflow: hidden;
        }}

        .deck-progress-bar {{
            display: grid;
            grid-template-columns: repeat({total_hero_slides}, 1fr);
            gap: 6px;
            margin-bottom: 18px;
        }}

        .deck-progress-seg {{
            height: 5px;
            border-radius: 3px;
            background: var(--gn-surface-variant);
            border: none;
            padding: 0;
            cursor: pointer;
            overflow: hidden;
            position: relative;
        }}

        .deck-progress-seg .deck-progress-fill {{
            display: block;
            height: 100%;
            width: 0%;
            background: var(--gn-blue);
            transition: width 0.25s ease;
        }}

        .deck-progress-seg.active .deck-progress-fill,
        .deck-progress-seg.passed .deck-progress-fill {{
            width: 100%;
        }}

        .deck-slide {{
            display: none;
            flex-direction: column;
            flex: 1;
            animation: fadeInSlide 0.25s ease;
        }}

        .deck-slide.active {{
            display: flex;
        }}

        @keyframes fadeInSlide {{
            from {{ opacity: 0; transform: translateY(4px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .deck-slide-topbar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 14px;
        }}

        .deck-cat-pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 5px 12px;
            border-radius: var(--gn-radius-pill);
            background: var(--gn-blue-surface);
            color: var(--gn-blue-text);
            font-size: 0.82rem;
            font-weight: 700;
        }}

        .deck-counter-badge {{
            font-size: 0.78rem;
            font-weight: 700;
            color: var(--gn-text-muted);
            letter-spacing: 0.5px;
            background: var(--gn-surface-variant);
            padding: 4px 10px;
            border-radius: var(--gn-radius-pill);
        }}

        .deck-slide-media {{
            position: relative;
            width: 100%;
            height: 190px;
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 14px;
            background: #0f172a;
        }}

        .deck-slide-media img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}

        .deck-media-badge {{
            position: absolute;
            bottom: 10px;
            right: 10px;
            background: rgba(217, 48, 37, 0.92);
            color: #fff;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 6px;
        }}

        .deck-pub-meta {{
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 8px;
            font-size: 0.85rem;
            color: var(--gn-text-muted);
        }}

        .deck-slide-title {{
            font-size: 1.48rem;
            font-weight: 800;
            line-height: 1.38;
            margin: 0 0 12px 0;
            color: var(--gn-text-primary);
            word-break: keep-all;
        }}

        .deck-slide-summary {{
            font-size: 0.96rem;
            color: var(--gn-text-secondary);
            margin: 0 0 14px 0;
            line-height: 1.6;
        }}

        .deck-slide-bullets {{
            margin: 0 0 18px 0;
            padding: 14px 16px 14px 18px;
            background: var(--gn-surface-variant);
            border-radius: 12px;
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}

        .deck-slide-bullets li {{
            font-size: 0.88rem;
            color: var(--gn-text-primary);
            font-weight: 500;
            line-height: 1.5;
        }}

        .deck-slide-footer {{
            margin-top: auto;
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            padding-top: 12px;
            border-top: 1px solid var(--gn-border-subtle);
        }}

        .deck-tags-wrap {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}

        .deck-actions-wrap {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .gn-deck-action-primary {{
            background: var(--gn-blue);
            color: #ffffff;
            border: none;
            padding: 8px 16px;
            border-radius: var(--gn-radius-pill);
            font-size: 0.85rem;
            font-weight: 700;
            text-decoration: none;
            cursor: pointer;
            transition: background 0.15s ease;
            font-family: inherit;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }}

        .gn-deck-action-primary:hover {{
            background: var(--gn-blue-hover);
        }}

        .gn-deck-action-secondary {{
            background: var(--gn-surface-variant);
            color: var(--gn-text-primary);
            border: 1px solid var(--gn-border);
            padding: 7px 14px;
            border-radius: var(--gn-radius-pill);
            font-size: 0.83rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.15s ease;
            font-family: inherit;
        }}

        .gn-deck-action-secondary:hover {{
            border-color: var(--gn-blue);
            color: var(--gn-blue-text);
        }}

        .deck-nav-controls {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-top: 16px;
            padding-top: 12px;
            border-top: 1px solid var(--gn-border-subtle);
        }}

        .deck-nav-btn {{
            background: var(--gn-surface-variant);
            border: 1px solid var(--gn-border);
            color: var(--gn-text-primary);
            padding: 6px 14px;
            border-radius: var(--gn-radius-pill);
            font-size: 0.82rem;
            font-weight: 600;
            cursor: pointer;
            font-family: inherit;
            transition: all 0.15s ease;
        }}

        .deck-nav-btn:hover {{
            background: var(--gn-blue-surface);
            color: var(--gn-blue-text);
            border-color: var(--gn-blue);
        }}

        .deck-nav-center {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.82rem;
            color: var(--gn-text-muted);
            font-weight: 600;
        }}

        /* Right Column Widgets Stack */
        .gn-hero-widgets-col {{
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}

        /* Widget 1: Google Podcast/News Audio Player Card */
        .gn-audio-widget {{
            background: var(--gn-surface);
            border: 1px solid var(--gn-border-subtle);
            border-radius: 20px;
            padding: 20px 22px;
            box-shadow: var(--gn-shadow-sm);
        }}

        .gn-widget-top {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            margin-bottom: 12px;
        }}

        .gn-widget-title {{
            font-size: 1rem;
            font-weight: 700;
            color: var(--gn-text-primary);
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .gn-status-pill {{
            font-size: 0.75rem;
            font-weight: 700;
            padding: 3px 10px;
            border-radius: var(--gn-radius-pill);
            background: var(--gn-blue-surface);
            color: var(--gn-blue-text);
        }}

        .gn-lang-tabs {{
            display: flex;
            gap: 6px;
            margin-bottom: 14px;
        }}

        .gn-lang-btn {{
            flex: 1;
            padding: 7px 10px;
            border-radius: 10px;
            border: 1px solid var(--gn-border);
            background: var(--gn-surface-variant);
            color: var(--gn-text-secondary);
            font-size: 0.82rem;
            font-weight: 600;
            cursor: pointer;
            font-family: inherit;
            transition: all 0.15s ease;
        }}

        .gn-lang-btn.active {{
            background: var(--gn-blue-surface);
            color: var(--gn-blue-text);
            border-color: var(--gn-blue);
            font-weight: 700;
        }}

        .gn-audio-progress-row {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 12px;
        }}

        .gn-time-lbl {{
            font-size: 0.78rem;
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
            color: var(--gn-text-muted);
            min-width: 38px;
        }}

        .gn-scrub-slider {{
            flex: 1;
            height: 5px;
            border-radius: 3px;
            background: var(--gn-border);
            outline: none;
            cursor: pointer;
            -webkit-appearance: none;
        }}

        .gn-scrub-slider::-webkit-slider-thumb {{
            -webkit-appearance: none;
            width: 14px;
            height: 14px;
            border-radius: 50%;
            background: var(--gn-blue);
            cursor: pointer;
        }}

        .gn-audio-controls-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
        }}

        .gn-audio-btns {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .gn-ctrl-circle {{
            width: 34px;
            height: 34px;
            border-radius: 50%;
            border: 1px solid var(--gn-border);
            background: var(--gn-surface-variant);
            color: var(--gn-text-primary);
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 0.85rem;
            transition: all 0.15s ease;
        }}

        .gn-ctrl-circle:hover {{
            border-color: var(--gn-blue);
            color: var(--gn-blue-text);
        }}

        .gn-ctrl-play {{
            width: 42px;
            height: 42px;
            background: var(--gn-blue);
            color: #ffffff;
            border: none;
            font-size: 1rem;
        }}

        .gn-ctrl-play:hover {{
            background: var(--gn-blue-hover);
            color: #ffffff;
        }}

        .gn-audio-extra {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .gn-speed-pill {{
            background: var(--gn-surface-variant);
            border: 1px solid var(--gn-border);
            color: var(--gn-text-secondary);
            padding: 4px 10px;
            border-radius: 8px;
            font-size: 0.78rem;
            font-weight: 700;
            cursor: pointer;
            font-family: inherit;
        }}

        .gn-vol-wrap {{
            display: flex;
            align-items: center;
            gap: 4px;
        }}

        .gn-vol-slider {{
            width: 60px;
            height: 4px;
            -webkit-appearance: none;
            background: var(--gn-border);
            border-radius: 2px;
        }}

        .gn-vol-slider::-webkit-slider-thumb {{
            -webkit-appearance: none;
            width: 11px;
            height: 11px;
            border-radius: 50%;
            background: var(--gn-text-muted);
            cursor: pointer;
        }}

        .gn-script-toggle-btn {{
            width: 100%;
            margin-top: 12px;
            padding: 8px;
            border-radius: 10px;
            border: 1px dashed var(--gn-border);
            background: var(--gn-surface-variant);
            color: var(--gn-text-secondary);
            font-size: 0.82rem;
            font-weight: 600;
            cursor: pointer;
            font-family: inherit;
            transition: all 0.15s ease;
        }}

        .gn-script-toggle-btn:hover {{
            color: var(--gn-blue-text);
            border-color: var(--gn-blue);
        }}

        /*Widget 2: Executive Top 3 Summary Widget */
        .gn-exec-widget {{
            background: var(--gn-surface);
            border: 1px solid var(--gn-border-subtle);
            border-radius: 20px;
            padding: 18px 22px;
            box-shadow: var(--gn-shadow-sm);
        }}

        .gn-exec-list {{
            margin: 10px 0 0 0;
            padding: 0;
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}

        .gn-exec-item {{
            display: flex;
            align-items: flex-start;
            gap: 10px;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--gn-border-subtle);
            cursor: pointer;
        }}

        .gn-exec-item:last-child {{
            border-bottom: none;
            padding-bottom: 0;
        }}

        .gn-exec-num {{
            font-size: 0.75rem;
            font-weight: 800;
            padding: 2px 7px;
            border-radius: 6px;
            background: var(--gn-blue-surface);
            color: var(--gn-blue-text);
            flex-shrink: 0;
            margin-top: 2px;
        }}

        .gn-exec-text {{
            font-size: 0.88rem;
            font-weight: 600;
            color: var(--gn-text-primary);
            line-height: 1.42;
            transition: color 0.15s ease;
        }}

        .gn-exec-item:hover .gn-exec-text {{
            color: var(--gn-blue-text);
        }}

        /* Widget 3: Daily Affirmation Widget */
        .gn-affirmation-widget {{
            background: var(--gn-surface);
            border: 1px solid var(--gn-border-subtle);
            border-left: 4px solid var(--gn-green);
            border-radius: 16px;
            padding: 16px 20px;
            box-shadow: var(--gn-shadow-sm);
        }}

        .gn-affirm-label {{
            font-size: 0.78rem;
            font-weight: 700;
            color: var(--gn-green);
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .gn-affirm-quote {{
            font-size: 1.02rem;
            font-weight: 700;
            color: var(--gn-text-primary);
            margin: 0;
            line-height: 1.48;
            word-break: keep-all;
        }}

        /* Collapsible Full Script Drawer */
        .gn-script-drawer {{
            display: none;
            background: var(--gn-surface);
            border: 1px solid var(--gn-border);
            border-radius: 16px;
            padding: 24px 28px;
            margin-bottom: 36px;
            box-shadow: var(--gn-shadow-sm);
        }}

        .gn-script-drawer.open {{
            display: block;
        }}

        .script-content {{
            display: none;
            font-size: 0.98rem;
            line-height: 1.8;
            color: var(--gn-text-secondary);
        }}

        .script-content.active {{
            display: block;
        }}

        /* ==========================================================================
           Google News Category Sections & Visual Card News Grid
           ========================================================================== */
        .gn-category-section {{
            margin-bottom: 44px;
            scroll-margin-top: 120px;
        }}

        .gn-section-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            padding-bottom: 14px;
            margin-bottom: 20px;
            border-bottom: 1px solid var(--gn-border);
        }}

        .gn-section-title-group {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .gn-section-icon {{
            width: 42px;
            height: 42px;
            border-radius: 12px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 1.3rem;
            flex-shrink: 0;
        }}

        .gn-section-title {{
            margin: 0;
            font-size: 1.35rem;
            font-weight: 800;
            letter-spacing: -0.3px;
            color: var(--gn-text-primary);
        }}

        .gn-section-subtitle {{
            margin: 2px 0 0 0;
            font-size: 0.84rem;
            color: var(--gn-text-muted);
        }}

        .gn-section-actions {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .gn-section-count {{
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--gn-text-muted);
        }}

        .gn-section-deck-btn {{
            background: var(--gn-surface);
            border: 1px solid var(--gn-border);
            color: var(--gn-blue-text);
            padding: 7px 14px;
            border-radius: var(--gn-radius-pill);
            font-size: 0.82rem;
            font-weight: 700;
            cursor: pointer;
            font-family: inherit;
            transition: all 0.15s ease;
        }}

        .gn-section-deck-btn:hover {{
            background: var(--gn-blue-surface);
            border-color: var(--gn-blue);
        }}

        /* Card Grid Mode (Default: 3 Columns on Desktop) */
        .gn-card-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
        }}

        /* Google News Cluster Feed Mode (2 Columns Horizontal Cards) */
        body.view-cluster .gn-card-grid {{
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
        }}

        body.view-cluster .gn-card-banner {{
            padding: 10px 18px;
            min-height: auto;
        }}

        body.view-cluster .gn-banner-quote {{
            display: none;
        }}

        .gn-news-card {{
            background: var(--gn-surface);
            border: 1px solid var(--gn-border-subtle);
            border-radius: var(--gn-radius-card);
            box-shadow: var(--gn-shadow-sm);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
        }}

        .gn-news-card:hover {{
            transform: translateY(-3px);
            box-shadow: var(--gn-shadow-md);
            border-color: var(--gn-border);
        }}

        /* Card Visual Header Banner (Card News Visual Top) */
        .gn-card-banner {{
            background: var(--card-surface, #e8f0fe);
            border-bottom: 1px solid var(--gn-border-subtle);
            padding: 14px 18px;
            min-height: 88px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            gap: 8px;
        }}

        [data-theme="dark"] .gn-card-banner {{
            background: rgba(138, 180, 248, 0.08);
        }}

        .gn-banner-top {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
        }}

        .gn-card-num-badge {{
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.6px;
            padding: 3px 8px;
            border-radius: 6px;
            background: rgba(15, 23, 42, 0.75);
            color: #ffffff;
        }}

        .gn-banner-cat {{
            font-size: 0.74rem;
            font-weight: 800;
            color: var(--card-accent, #1a73e8);
            letter-spacing: 0.3px;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }}

        [data-theme="dark"] .gn-banner-cat {{
            color: var(--gn-blue);
        }}

        .gn-banner-subtag {{
            background: rgba(0,0,0,0.08);
            padding: 1px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
        }}

        .gn-banner-quote {{
            font-size: 0.92rem;
            font-weight: 700;
            color: var(--gn-text-primary);
            display: flex;
            align-items: center;
            gap: 3px;
            line-height: 1.35;
        }}

        .gn-quote-mark {{
            color: var(--card-accent, #1a73e8);
            font-weight: 800;
            font-size: 1.05rem;
        }}

        /* YouTube Real Thumbnail Media Header */
        .gn-card-media {{
            position: relative;
            width: 100%;
            height: 176px;
            background: #0f172a;
            overflow: hidden;
        }}

        .gn-card-media img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s ease;
        }}

        .gn-news-card:hover .gn-card-media img {{
            transform: scale(1.03);
        }}

        .gn-media-overlay {{
            position: absolute;
            inset: 0;
            background: linear-gradient(180deg, rgba(0,0,0,0.45) 0%, transparent 45%, rgba(0,0,0,0.55) 100%);
            padding: 12px 16px;
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
        }}

        .gn-yt-play-pill {{
            background: #d93025;
            color: #ffffff;
            font-size: 0.74rem;
            font-weight: 700;
            padding: 3px 9px;
            border-radius: 6px;
        }}

        /* Card Body */
        .gn-card-body {{
            padding: 16px 18px;
            display: flex;
            flex-direction: column;
            flex: 1;
        }}

        .gn-card-pub-row {{
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 8px;
            font-size: 0.8rem;
            color: var(--gn-text-muted);
        }}

        .gn-pub-favicon {{
            width: 16px;
            height: 16px;
            border-radius: 3px;
            object-fit: contain;
            flex-shrink: 0;
        }}

        .gn-pub-name {{
            font-weight: 700;
            color: var(--gn-text-secondary);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            max-width: 180px;
        }}

        .gn-pub-dot {{
            color: var(--gn-text-muted);
        }}

        .gn-pub-time {{
            color: var(--gn-text-muted);
            white-space: nowrap;
        }}

        .gn-card-title {{
            margin: 0 0 10px 0;
            font-size: 1.08rem;
            font-weight: 700;
            line-height: 1.44;
            word-break: keep-all;
        }}

        .gn-card-title a {{
            color: var(--gn-text-primary);
            text-decoration: none;
            transition: color 0.15s ease;
        }}

        .gn-card-title a:hover {{
            color: var(--gn-blue-text);
            text-decoration: underline;
            text-underline-offset: 3px;
        }}

        .gn-card-summary {{
            margin: 0 0 14px 0;
            font-size: 0.88rem;
            color: var(--gn-text-secondary);
            line-height: 1.58;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}

        .gn-card-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin-top: auto;
            padding-top: 4px;
        }}

        .gn-tag-chip {{
            border: none;
            background: var(--gn-surface-variant);
            color: var(--gn-text-secondary);
            font-size: 0.75rem;
            font-weight: 600;
            padding: 4px 9px;
            border-radius: 6px;
            cursor: pointer;
            font-family: inherit;
            transition: all 0.15s ease;
        }}

        .gn-tag-chip:hover {{
            background: var(--gn-blue-surface);
            color: var(--gn-blue-text);
        }}

        /* Google News Related Coverage Cluster inside Card */
        .gn-related-cluster {{
            margin-top: 12px;
            padding-top: 10px;
            border-top: 1px dashed var(--gn-border);
        }}

        .gn-related-label {{
            font-size: 0.72rem;
            font-weight: 700;
            color: var(--gn-text-muted);
            margin-bottom: 5px;
        }}

        .gn-related-list {{
            margin: 0;
            padding: 0 0 0 14px;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}

        .gn-related-item {{
            font-size: 0.8rem;
            line-height: 1.38;
            color: var(--gn-text-secondary);
        }}

        .gn-related-link {{
            color: var(--gn-text-secondary);
            text-decoration: none;
            font-weight: 500;
        }}

        .gn-related-link:hover {{
            color: var(--gn-blue-text);
            text-decoration: underline;
        }}

        .gn-related-src {{
            font-size: 0.72rem;
            color: var(--gn-text-muted);
            margin-left: 4px;
        }}

        /* Card Action Footer */
        .gn-card-footer {{
            padding: 10px 18px;
            background: var(--gn-surface);
            border-top: 1px solid var(--gn-border-subtle);
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
        }}

        .gn-btn-slide-view {{
            background: var(--gn-blue-surface);
            color: var(--gn-blue-text);
            border: none;
            padding: 6px 12px;
            border-radius: var(--gn-radius-pill);
            font-size: 0.78rem;
            font-weight: 700;
            cursor: pointer;
            font-family: inherit;
            transition: all 0.15s ease;
        }}

        .gn-btn-slide-view:hover {{
            background: var(--gn-blue);
            color: #ffffff;
        }}

        .gn-card-footer-right {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        .gn-btn-bookmark {{
            width: 30px;
            height: 30px;
            border-radius: 50%;
            border: 1px solid transparent;
            background: transparent;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 0.88rem;
            opacity: 0.65;
            transition: all 0.15s ease;
        }}

        .gn-btn-bookmark:hover,
        .gn-btn-bookmark.saved {{
            opacity: 1;
            background: var(--gn-blue-surface);
            border-color: var(--gn-blue);
        }}

        .gn-btn-fullcoverage {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 5px 11px;
            border-radius: var(--gn-radius-pill);
            border: 1px solid var(--gn-border);
            background: var(--gn-surface);
            color: var(--gn-text-secondary);
            font-size: 0.78rem;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.15s ease;
        }}

        .gn-btn-fullcoverage:hover {{
            border-color: var(--gn-blue);
            color: var(--gn-blue-text);
            background: var(--gn-surface-hover);
        }}

        /* ==========================================================================
           3-Slide Card News Detail Modal (Lightbox Story Viewer)
           ========================================================================== */
        .gn-modal-backdrop {{
            position: fixed;
            inset: 0;
            z-index: 200;
            background: rgba(15, 23, 42, 0.72);
            backdrop-filter: blur(4px);
            display: none;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}

        .gn-modal-backdrop.open {{
            display: flex;
        }}

        .gn-modal-card {{
            width: 100%;
            max-width: 560px;
            background: var(--gn-surface);
            border: 1px solid var(--gn-border);
            border-radius: 24px;
            box-shadow: var(--gn-shadow-lg);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            animation: modalPop 0.2s ease;
        }}

        @keyframes modalPop {{
            from {{ opacity: 0; transform: scale(0.96); }}
            to {{ opacity: 1; transform: scale(1); }}
        }}

        .modal-top-bar {{
            padding: 16px 22px 12px 22px;
            border-bottom: 1px solid var(--gn-border-subtle);
        }}

        .modal-step-bars {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 6px;
            margin-bottom: 12px;
        }}

        .modal-step-bar {{
            height: 4px;
            border-radius: 2px;
            background: var(--gn-surface-variant);
            cursor: pointer;
        }}

        .modal-step-bar.active {{
            background: var(--gn-blue);
        }}

        .modal-header-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .modal-cat-badge {{
            font-size: 0.8rem;
            font-weight: 700;
            padding: 4px 11px;
            border-radius: var(--gn-radius-pill);
            background: var(--gn-blue-surface);
            color: var(--gn-blue-text);
        }}

        .modal-close-btn {{
            background: var(--gn-surface-variant);
            border: none;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            font-size: 1rem;
            color: var(--gn-text-secondary);
            cursor: pointer;
        }}

        .modal-slide-body {{
            padding: 26px 26px 22px 26px;
            min-height: 340px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}

        .modal-step-label {{
            font-size: 0.76rem;
            font-weight: 800;
            color: var(--gn-blue-text);
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}

        .modal-headline {{
            font-size: 1.42rem;
            font-weight: 800;
            line-height: 1.4;
            margin: 0 0 14px 0;
            color: var(--gn-text-primary);
            word-break: keep-all;
        }}

        .modal-quote-box {{
            background: var(--gn-surface-variant);
            border-left: 4px solid var(--gn-blue);
            padding: 14px 16px;
            border-radius: 0 12px 12px 0;
            font-size: 0.95rem;
            font-weight: 600;
            color: var(--gn-text-primary);
            margin-bottom: 16px;
        }}

        .modal-bullet-list {{
            list-style: none;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}

        .modal-bullet-list li {{
            background: var(--gn-surface-variant);
            padding: 12px 16px;
            border-radius: 12px;
            font-size: 0.92rem;
            line-height: 1.55;
            color: var(--gn-text-primary);
        }}

        .modal-footer-bar {{
            padding: 14px 22px;
            background: var(--gn-surface-variant);
            border-top: 1px solid var(--gn-border-subtle);
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
        }}

        .modal-nav-group {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        /* Empty filter state */
        .gn-empty-state {{
            display: none;
            text-align: center;
            padding: 60px 20px;
            background: var(--gn-surface);
            border-radius: 20px;
            border: 1px dashed var(--gn-border);
            margin: 24px 0;
        }}

        .gn-footer {{
            max-width: 1360px;
            margin: 0 auto;
            padding: 28px 24px;
            border-top: 1px solid var(--gn-border);
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            color: var(--gn-text-muted);
            font-size: 0.85rem;
        }}

        /* ======================================================================
           Stock Heatmap Cards & Treemap Styling
           ====================================================================== */
        .gn-heatmap-card-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-bottom: 24px;
        }}

        @media (max-width: 980px) {{
            .gn-heatmap-card-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        .gn-heatmap-card {{
            background: var(--gn-surface);
            border: 1px solid var(--gn-border-subtle);
            border-radius: var(--gn-radius-card);
            box-shadow: var(--gn-shadow-sm);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
        }}

        .gn-heatmap-card:hover {{
            transform: translateY(-2px);
            box-shadow: var(--gn-shadow-md);
            border-color: var(--gn-border);
        }}

        .gn-heatmap-index-strip {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            padding: 10px 18px;
            background: rgba(0, 0, 0, 0.025);
            border-top: 1px solid var(--gn-border-subtle);
            border-bottom: 1px solid var(--gn-border-subtle);
        }}

        [data-theme="dark"] .gn-heatmap-index-strip {{
            background: rgba(255, 255, 255, 0.035);
        }}

        .gn-index-pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: var(--gn-surface);
            border: 1px solid var(--gn-border);
            padding: 4px 10px;
            border-radius: var(--gn-radius-pill);
            font-size: 0.78rem;
            font-weight: 600;
            text-decoration: none;
            color: var(--gn-text-primary);
            transition: all 0.15s ease;
        }}

        .gn-index-pill:hover {{
            border-color: var(--gn-blue);
            transform: translateY(-1px);
        }}

        .gn-idx-val {{
            font-weight: 700;
            color: var(--gn-text-primary);
        }}

        .gn-idx-chg {{
            padding: 1px 6px;
            border-radius: 4px;
            font-size: 0.74rem;
            font-weight: 700;
        }}

        .gn-idx-chg.pos {{
            background: #e6f4ea;
            color: #137333;
        }}

        .gn-idx-chg.neg {{
            background: #fce8e6;
            color: #c5221f;
        }}

        .gn-idx-chg.zero {{
            background: var(--gn-surface-variant);
            color: var(--gn-text-muted);
        }}

        body.heatmap-kr-colors .gn-idx-chg.pos {{
            background: #fce8e6;
            color: #c5221f;
        }}

        body.heatmap-kr-colors .gn-idx-chg.neg {{
            background: #e8f0fe;
            color: #1a73e8;
        }}

        .gn-heatmap-treemap-wrap {{
            padding: 14px 18px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}

        .gn-heatmap-sector {{
            border: 1px solid var(--gn-border-subtle);
            border-radius: 12px;
            padding: 10px;
            background: var(--gn-bg);
        }}

        .gn-sector-header {{
            font-size: 0.74rem;
            font-weight: 800;
            color: var(--gn-text-muted);
            letter-spacing: 0.3px;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .gn-sector-tiles {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(78px, 1fr));
            gap: 6px;
        }}

        .gn-stock-tile {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            padding: 6px 4px;
            border-radius: 8px;
            text-decoration: none;
            color: #ffffff !important;
            cursor: pointer;
            position: relative;
            transition: transform 0.15s ease, filter 0.15s ease, box-shadow 0.15s ease;
            overflow: hidden;
            min-height: 48px;
        }}

        .gn-stock-tile:hover {{
            transform: scale(1.04);
            filter: brightness(1.12);
            box-shadow: 0 4px 12px rgba(0,0,0,0.25);
            z-index: 2;
        }}

        .gn-stock-tile.tier-xl {{
            grid-column: span 2;
            min-height: 56px;
            padding: 8px 6px;
        }}

        .gn-stock-tile.tier-lg {{
            min-height: 52px;
        }}

        .tile-sym {{
            font-size: 0.82rem;
            font-weight: 800;
            line-height: 1.1;
            letter-spacing: -0.2px;
        }}

        .tile-name {{
            font-size: 0.67rem;
            opacity: 0.92;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 90%;
            line-height: 1.1;
            margin-top: 1px;
        }}

        .tile-pct {{
            font-size: 0.75rem;
            font-weight: 800;
            margin-top: 2px;
            line-height: 1.1;
        }}

        /* 7-Step Heatmap Gradient: Global Mode (Default: Green=Up, Red=Down) */
        .heat-p3 {{ background: #0d652d; }}
        .heat-p2 {{ background: #188038; }}
        .heat-p1 {{ background: #34a853; }}
        .heat-zero {{ background: #70757a; }}
        .heat-m1 {{ background: #ea4335; }}
        .heat-m2 {{ background: #d93025; }}
        .heat-m3 {{ background: #a50e0e; }}

        /* 7-Step Heatmap Gradient: Korean Mode (Red=Up, Blue=Down) */
        body.heatmap-kr-colors .heat-p3 {{ background: #a50e0e; }}
        body.heatmap-kr-colors .heat-p2 {{ background: #d93025; }}
        body.heatmap-kr-colors .heat-p1 {{ background: #ea4335; }}
        body.heatmap-kr-colors .heat-zero {{ background: #70757a; }}
        body.heatmap-kr-colors .heat-m1 {{ background: #4285f4; }}
        body.heatmap-kr-colors .heat-m2 {{ background: #1a73e8; }}
        body.heatmap-kr-colors .heat-m3 {{ background: #174ea6; }}

        /* Market Breadth Bar */
        .gn-heatmap-breadth {{
            padding: 10px 18px 12px 18px;
            border-top: 1px solid var(--gn-border-subtle);
            display: flex;
            flex-direction: column;
            gap: 6px;
            font-size: 0.78rem;
        }}

        .breadth-stats {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            font-weight: 700;
        }}

        .breadth-ratio-bar {{
            flex: 1;
            height: 6px;
            background: #d93025;
            border-radius: 999px;
            overflow: hidden;
            display: flex;
        }}

        body.heatmap-kr-colors .breadth-ratio-bar {{
            background: #1a73e8;
        }}

        .adv-fill {{
            height: 100%;
            background: #188038;
            transition: width 0.3s ease;
        }}

        body.heatmap-kr-colors .adv-fill {{
            background: #d93025;
        }}

        .breadth-movers {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            font-size: 0.74rem;
            color: var(--gn-text-secondary);
        }}

        /* Scale Legend */
        .gn-heatmap-legend {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            padding: 8px 18px;
            font-size: 0.7rem;
            color: var(--gn-text-muted);
            border-top: 1px dashed var(--gn-border-subtle);
        }}

        .legend-bar {{
            display: flex;
            border-radius: 4px;
            overflow: hidden;
        }}

        .legend-chip {{
            width: 22px;
            height: 12px;
        }}

        /* Fullscreen Heatmap Zoom Modal */
        .gn-heatmap-modal .gn-heatmap-modal-card {{
            max-width: 1120px;
            width: 95vw;
            max-height: 90vh;
            display: flex;
            flex-direction: column;
        }}

        .gn-heatmap-treemap-wrap.zoomed .gn-sector-tiles {{
            grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
            gap: 8px;
        }}

        .gn-heatmap-treemap-wrap.zoomed .gn-stock-tile {{
            min-height: 64px;
            padding: 10px 8px;
        }}

        .gn-heatmap-treemap-wrap.zoomed .tile-sym {{
            font-size: 0.95rem;
        }}

        .gn-heatmap-treemap-wrap.zoomed .tile-name {{
            font-size: 0.76rem;
        }}

        .gn-heatmap-treemap-wrap.zoomed .tile-pct {{
            font-size: 0.85rem;
        }}

        /* Responsive Breakpoints */
        @media (max-width: 1120px) {{
            .gn-hero-grid {{
                grid-template-columns: 1fr;
            }}
            .gn-card-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}

        @media (max-width: 720px) {{
            .gn-top-row {{
                flex-wrap: wrap;
                padding: 10px 16px;
            }}
            .gn-search-box {{
                order: 3;
                max-width: 100%;
                flex-basis: 100%;
            }}
            .gn-card-grid,
            body.view-cluster .gn-card-grid {{
                grid-template-columns: 1fr;
            }}
            .gn-main {{
                padding: 20px 16px 48px 16px;
            }}
            .deck-slide-title {{
                font-size: 1.25rem;
            }}
        }}
    </style>
</head>
<body>
    <!-- Audio Sources (MP3 + M4A Dual Format for 100% Browser Support) -->
    <audio id="audio-ko" preload="metadata">
        <source src="AUDIO_BASE_PATHbriefing_{date_str}_ko.mp3?v={cache_ts}" type="audio/mpeg">
        <source src="AUDIO_BASE_PATHbriefing_{date_str}_ko.m4a?v={cache_ts}" type="audio/mp4">
    </audio>
    <audio id="audio-en" preload="metadata">
        <source src="AUDIO_BASE_PATHbriefing_{date_str}_en.mp3?v={cache_ts}" type="audio/mpeg">
        <source src="AUDIO_BASE_PATHbriefing_{date_str}_en.m4a?v={cache_ts}" type="audio/mp4">
    </audio>
    <audio id="audio-zh" preload="metadata">
        <source src="AUDIO_BASE_PATHbriefing_{date_str}_zh.mp3?v={cache_ts}" type="audio/mpeg">
        <source src="AUDIO_BASE_PATHbriefing_{date_str}_zh.m4a?v={cache_ts}" type="audio/mp4">
    </audio>

    <!-- ==========================================================================
         Google News Sticky Top App Bar & Category Tabs
         ========================================================================== -->
    <header class="gn-app-header">
        <div class="gn-top-row">
            <a href="#" class="gn-brand" onclick="resetAllFilters(); return false;">
                <span class="gn-brand-icon" aria-hidden="true">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                        <rect x="2" y="4" width="20" height="16" rx="3" fill="#4285F4"/>
                        <rect x="5" y="7" width="8" height="5" rx="1" fill="#FFFFFF"/>
                        <rect x="5" y="14" width="14" height="2" rx="1" fill="#FBBC04"/>
                        <rect x="15" y="7" width="4" height="5" rx="1" fill="#34A853"/>
                    </svg>
                </span>
                <span class="gn-brand-text">
                    <span><span class="gn-g-blue">G</span><span class="gn-g-red">o</span><span class="gn-g-yellow">o</span><span class="gn-g-blue">g</span><span class="gn-g-green">l</span><span class="gn-g-red">e</span></span>
                    <span class="gn-brand-news">News</span>
                    <span class="gn-brand-badge">카드뉴스 브리핑</span>
                </span>
            </a>

            <div class="gn-search-box" role="search">
                <span class="gn-search-icon" aria-hidden="true">🔍</span>
                <input
                    type="search"
                    id="gnSearchInput"
                    class="gn-search-input"
                    placeholder="뉴스, 키워드(#오픈AI, #금리), 언론사 검색..."
                    aria-label="뉴스 카드 검색"
                    oninput="handleSearchInput(this.value)"
                >
                <button type="button" id="gnSearchClear" class="gn-search-clear" onclick="clearSearch()" aria-label="검색어 지우기">✕</button>
            </div>

            <div class="gn-top-actions">
                <div class="gn-view-switcher" role="group" aria-label="보기 모드 전환">
                    <button type="button" id="viewBtnCard" class="gn-view-btn active" onclick="setViewMode('card')" title="카드뉴스 그리드 보기">
                        🃏 카드뉴스
                    </button>
                    <button type="button" id="viewBtnCluster" class="gn-view-btn" onclick="setViewMode('cluster')" title="구글 뉴스 클러스터 피드 보기">
                        📰 클러스터
                    </button>
                    <button type="button" id="viewBtnModal" class="gn-view-btn" onclick="openCardModal(0)" title="전체화면 카드뉴스 슬라이드 모달">
                        📱 슬라이드
                    </button>
                </div>
                <button type="button" id="themeToggleBtn" class="gn-icon-btn" onclick="toggleTheme()" title="다크/라이트 모드 전환">
                    <span id="themeIcon">🌙</span>
                </button>
                <a href="ARCHIVE_LINK_PATH" id="archiveNavBtn" class="gn-icon-btn" title="지난 날짜 브리핑 아카이브">
                    🗂️ 지난 신문
                </a>
            </div>
        </div>

        <nav class="gn-nav-bar" aria-label="뉴스 카테고리">
            <button type="button" class="gn-nav-tab active" data-cat="all" onclick="selectCategory('all', this)">🏠 홈 (전체 브리핑)</button>
            <button type="button" class="gn-nav-tab" data-cat="ai" onclick="selectCategory('ai', this)">🤖 AI · 머신러닝</button>
            <button type="button" class="gn-nav-tab" data-cat="tech" onclick="selectCategory('tech', this)">💻 빅테크 · 반도체</button>
            <button type="button" class="gn-nav-tab" data-cat="paper" onclick="selectCategory('paper', this)">📚 ArXiv 논문</button>
            <button type="button" class="gn-nav-tab" data-cat="youtube" onclick="selectCategory('youtube', this)">📺 테크 유튜브</button>
            <button type="button" class="gn-nav-tab" data-cat="tools" onclick="selectCategory('tools', this)">🛠️ AI 툴 · 기법</button>
            <button type="button" class="gn-nav-tab" data-cat="econ" onclick="selectCategory('econ', this)">📈 글로벌 경제</button>
            <button type="button" class="gn-nav-tab" data-cat="military" onclick="selectCategory('military', this)">🛡️ 군사 · 안보</button>
            <button type="button" class="gn-nav-tab" data-cat="world" onclick="selectCategory('world', this)">🌍 세계 · 외교</button>
            <button type="button" class="gn-nav-tab" data-cat="saved" onclick="selectCategory('saved', this)">
                🔖 저장한 카드 <span id="savedCountBadge" class="gn-saved-count">0</span>
            </button>
        </nav>
    </header>

    <!-- ==========================================================================
         Main Briefing Content
         ========================================================================== -->
    <main class="gn-main">
        <div class="gn-briefing-header">
            <div class="gn-briefing-title-wrap">
                <h1>오늘의 브리핑</h1>
                <div class="gn-briefing-meta">
                    <span>📅 {formatted_date_ko}</span>
                    <span>&middot;</span>
                    <span>오전 09:00 KST 발행</span>
                    <span>&middot;</span>
                    <span id="visibleCardsCounter">총 {total_cards}개 카드뉴스</span>
                </div>
            </div>
            <div class="gn-trending-bar" aria-label="오늘의 핵심 키워드">
                <span class="gn-trending-label">🔥 인기 토픽:</span>
                {trending_chips_html}
            </div>
        </div>

        <!-- Google News "Your Briefing" Hero Section -->
        <section class="gn-hero-grid" id="heroBriefingSection" aria-label="오늘의 대표 카드뉴스 및 음성 브리핑">
            <!-- Left: Interactive Card News Slide Deck -->
            <div class="gn-hero-deck-card">
                <div>
                    <div class="deck-progress-bar" role="tablist" aria-label="카드뉴스 슬라이드 진행바">
                        {hero_progress_bars_html}
                    </div>
                    <div id="heroDeckSlidesContainer">
                        {hero_slides_html}
                    </div>
                </div>
                <div class="deck-nav-controls">
                    <button type="button" class="deck-nav-btn" onclick="prevHeroSlide()">◀ 이전 카드</button>
                    <div class="deck-nav-center">
                        <span id="heroSlideIndicator">1 / {total_hero_slides}</span>
                        <button type="button" id="heroAutoPlayBtn" class="deck-nav-btn" onclick="toggleHeroAutoPlay()">⏸ 자동재생 켜짐</button>
                    </div>
                    <button type="button" class="deck-nav-btn" onclick="nextHeroSlide()">다음 카드 ▶</button>
                </div>
            </div>

            <!-- Right: Audio Briefing Player + Top 3 Summary + Affirmation -->
            <aside class="gn-hero-widgets-col">
                <!-- 1. Multi-language Audio Player Widget -->
                <div class="gn-audio-widget">
                    <div class="gn-widget-top">
                        <div class="gn-widget-title" id="playerCurrentTitle">🎙️ 5분 라디오 브리핑 · 🇰🇷 한국어</div>
                        <span class="gn-status-pill" id="playerStatusBadge">준비됨</span>
                    </div>
                    <div class="gn-lang-tabs" role="group" aria-label="음성 브리핑 언어 선택">
                        <button type="button" id="btn-ko" class="gn-lang-btn active" onclick="switchTab('ko')">🇰🇷 한국어</button>
                        <button type="button" id="btn-en" class="gn-lang-btn" onclick="switchTab('en')">🇺🇸 English</button>
                        <button type="button" id="btn-zh" class="gn-lang-btn" onclick="switchTab('zh')">🇨🇳 中文</button>
                    </div>
                    <div class="gn-audio-progress-row">
                        <span class="gn-time-lbl" id="timeCurrent">00:00</span>
                        <input type="range" class="gn-scrub-slider" id="progressSlider" min="0" max="100" value="0" oninput="seekAudio(this.value)" aria-label="오디오 탐색 바">
                        <span class="gn-time-lbl" id="timeDuration">--:--</span>
                    </div>
                    <div class="gn-audio-controls-row">
                        <div class="gn-audio-btns">
                            <button type="button" class="gn-ctrl-circle" onclick="skipTime(-10)" title="10초 뒤로" aria-label="10초 뒤로">⏪</button>
                            <button type="button" class="gn-ctrl-circle gn-ctrl-play" id="playMainBtn" onclick="togglePlay()" title="재생 / 일시정지" aria-label="재생 또는 일시정지">▶️</button>
                            <button type="button" class="gn-ctrl-circle" onclick="skipTime(10)" title="10초 앞으로" aria-label="10초 앞으로">⏩</button>
                        </div>
                        <div class="gn-audio-extra">
                            <button type="button" class="gn-speed-pill" id="speedBtn" onclick="cycleSpeed()" title="재생 배속 변경">1.0x</button>
                            <div class="gn-vol-wrap" title="볼륨 조절">
                                <span style="font-size:0.8rem;">🔊</span>
                                <input type="range" class="gn-vol-slider" min="0" max="1" step="0.05" value="1" oninput="setVolume(this.value)" aria-label="볼륨 조절">
                            </div>
                        </div>
                    </div>
                    <div id="playerStatusMsg" style="font-size: 0.76rem; color: var(--gn-text-muted); margin-top: 8px; text-align: center;">
                        재생 버튼을 누르면 아나운서 음성 브리핑이 시작됩니다.
                    </div>
                    <button type="button" id="scriptDrawerBtn" class="gn-script-toggle-btn" onclick="toggleScriptDrawer()">
                        📜 5분 브리핑 전체 대본 펼치기 (한/영/중) ▾
                    </button>
                </div>

                <!-- 2. Top 3 Executive Headlines Widget -->
                <div class="gn-exec-widget">
                    <div class="gn-widget-top" style="margin-bottom: 6px;">
                        <div class="gn-widget-title">⚡ 바쁜 아침 1분 3대 헤드라인</div>
                        <span style="font-size: 0.74rem; color: var(--gn-text-muted);">{short_date_ko}</span>
                    </div>
                    <ul class="gn-exec-list">
                        <li class="gn-exec-item" onclick="openCardModal({top_ai_card.get('global_idx', 0)})">
                            <span class="gn-exec-num">AI·테크</span>
                            <span class="gn-exec-text">{html_lib.escape(top_ai_card.get('title', ''))}</span>
                        </li>
                        <li class="gn-exec-item" onclick="openCardModal({top_econ_card.get('global_idx', 0)})">
                            <span class="gn-exec-num" style="background:#e6f4ea; color:#188038;">경제·금융</span>
                            <span class="gn-exec-text">{html_lib.escape(top_econ_card.get('title', ''))}</span>
                        </li>
                        <li class="gn-exec-item" onclick="openCardModal({top_mil_card.get('global_idx', 0)})">
                            <span class="gn-exec-num" style="background:#fef7e0; color:#b06000;">안보·세계</span>
                            <span class="gn-exec-text">{html_lib.escape(top_mil_card.get('title', ''))}</span>
                        </li>
                    </ul>
                </div>

                <!-- 3. Daily Affirmation Widget -->
                <div class="gn-affirmation-widget" id="affirmationSection">
                    <div class="gn-affirm-label">
                        <span>🌅 오늘의 긍정 확언 & 명상</span>
                        <button type="button" onclick="speakAffirmation()" style="background:none; border:none; color:var(--gn-green); cursor:pointer; font-size:0.76rem; font-weight:700; padding:0;">🔊 듣기</button>
                    </div>
                    <p class="gn-affirm-quote" id="affirmationTextEl">"{html_lib.escape(affirmation)}"</p>
                </div>
            </aside>
        </section>

        <!-- Collapsible Multi-language Script Drawer -->
        <section id="scriptDrawer" class="gn-script-drawer" aria-label="다국어 브리핑 대본">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; border-bottom:1px solid var(--gn-border-subtle); padding-bottom:10px;">
                <h2 style="margin:0; font-size:1.15rem;">🎙️ 5-Minute Multi-Language Briefing Script</h2>
                <button type="button" class="gn-icon-btn" onclick="toggleScriptDrawer()">닫기 ✕</button>
            </div>
            <div id="content-ko" class="script-content active">{ko_script_html}</div>
            <div id="content-en" class="script-content">{en_script_html}</div>
            <div id="content-zh" class="script-content">{zh_script_html}</div>
        </section>

        <!-- Empty Search / Saved Filter State -->
        <div id="emptyStateBox" class="gn-empty-state">
            <div style="font-size: 2.4rem; margin-bottom: 10px;">🔍</div>
            <h3 style="margin: 0 0 8px 0; font-size: 1.15rem;">조건에 맞는 카드뉴스가 없습니다</h3>
            <p style="margin: 0 0 16px 0; color: var(--gn-text-muted); font-size: 0.9rem;">검색어를 변경하거나 전체 브리핑 보기로 돌아가세요.</p>
            <button type="button" class="gn-deck-action-primary" onclick="resetAllFilters()">전체 카드뉴스 보기</button>
        </div>

        <!-- Google News Category Card Sections -->
        <div id="allSectionsContainer">
            {sections_html}
        </div>
    </main>

    <!-- ==========================================================================
         Interactive 3-Slide Card News Detail Modal
         ========================================================================== -->
    <div id="cardNewsModal" class="gn-modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="modalHeadline" onclick="handleBackdropClick(event)">
        <div class="gn-modal-card">
            <div class="modal-top-bar">
                <div class="modal-step-bars">
                    <div class="modal-step-bar active" onclick="setModalStep(0)"></div>
                    <div class="modal-step-bar" onclick="setModalStep(1)"></div>
                    <div class="modal-step-bar" onclick="setModalStep(2)"></div>
                </div>
                <div class="modal-header-row">
                    <span id="modalCatBadge" class="modal-cat-badge">🤖 AI · 머신러닝</span>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span id="modalCardCounter" style="font-size:0.78rem; color:var(--gn-text-muted); font-weight:700;">CARD 1 / {total_cards}</span>
                        <button type="button" class="modal-close-btn" onclick="closeCardModal()" aria-label="모달 닫기">✕</button>
                    </div>
                </div>
            </div>

            <div class="modal-slide-body" id="modalSlideBody">
                <!-- Populated dynamically via JS -->
            </div>

            <div class="modal-footer-bar">
                <div class="modal-nav-group">
                    <button type="button" class="deck-nav-btn" onclick="prevModalCard()" title="이전 뉴스 카드로 이동">◀ 이전 뉴스</button>
                    <button type="button" class="deck-nav-btn" onclick="nextModalCard()" title="다음 뉴스 카드로 이동">다음 뉴스 ▶</button>
                </div>
                <div class="modal-nav-group">
                    <button type="button" class="deck-nav-btn" id="modalStepBtn" onclick="nextModalStep()">다음 슬라이드 (1/3) &rsaquo;</button>
                    <a href="#" id="modalSourceLink" target="_blank" rel="noopener noreferrer" class="gn-deck-action-primary">원문 보기 &nearr;</a>
                </div>
            </div>
        </div>
    </div>

    <!-- ==========================================================================
         Interactive Fullscreen Stock Heatmap Zoom Modal
         ========================================================================== -->
    <div id="heatmapZoomModal" class="gn-modal-backdrop gn-heatmap-modal" role="dialog" aria-modal="true" aria-labelledby="heatmapModalTitle" onclick="handleHeatmapBackdropClick(event)">
        <div class="gn-modal-card gn-heatmap-modal-card">
            <div class="modal-top-bar">
                <div class="modal-header-row">
                    <div style="display:flex; align-items:center; gap:10px;">
                        <span id="heatmapModalCatBadge" class="modal-cat-badge">📊 주식 시장 히트맵</span>
                        <h3 id="heatmapModalTitle" style="margin:0; font-size:1.15rem; font-weight:800; color:var(--gn-text-primary);">히트맵 상세</h3>
                    </div>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <button type="button" class="gn-section-deck-btn btn-color-toggle" onclick="toggleHeatmapColorMode()" title="글로벌/한국식 색상 전환">🎨 색상전환</button>
                        <button type="button" class="modal-close-btn" onclick="closeHeatmapZoomModal()" aria-label="모달 닫기">✕</button>
                    </div>
                </div>
            </div>

            <div class="heatmap-modal-body" id="heatmapModalBody" style="padding: 16px; overflow-y: auto; max-height: calc(85vh - 70px);">
                <!-- Populated dynamically via JS -->
            </div>
        </div>
    </div>

    <footer class="gn-footer">
        <div>&copy; {datetime.now().year} <strong>Google News Style Daily Morning Briefing</strong> &middot; Automated Card News Intelligence System</div>
        <div>매일 아침 09:00 KST 자동 발행 &middot; <a href="ARCHIVE_LINK_PATH" style="color:var(--gn-blue-text); text-decoration:none; font-weight:600;">지난 브리핑 아카이브 열람 &rarr;</a></div>
    </footer>

    <script>
        const ALL_CARDS = {modal_cards_json};
        const CURRENT_DATE = "{date_str}";
        const TOTAL_HERO_SLIDES = {total_hero_slides};
        const STORAGE_KEY_SAVED = 'gn_briefing_saved_cards_v1';
        const STORAGE_KEY_THEME = 'gn_briefing_theme_v1';

        let currentLang = 'ko';
        const langNames = {{ ko: '🇰🇷 한국어', en: '🇺🇸 English', zh: '🇨🇳 中文' }};
        let currentRate = 1.0;

        let currentHeroSlide = 0;
        let heroAutoPlayTimer = null;
        let isHeroAutoPlaying = true;

        let activeCategory = 'all';
        let activeSearchQuery = '';
        let savedCards = new Set();

        let modalCardIdx = 0;
        let modalStepIdx = 0;

        /* ======================================================================
           1. Theme & Bookmark Initialization
           ====================================================================== */
        function initPreferences() {{
            try {{
                const savedTheme = localStorage.getItem(STORAGE_KEY_THEME);
                if (savedTheme === 'dark' || savedTheme === 'light') {{
                    document.documentElement.setAttribute('data-theme', savedTheme);
                    updateThemeIcon(savedTheme);
                }}
                const rawSaved = localStorage.getItem(STORAGE_KEY_SAVED);
                if (rawSaved) {{
                    JSON.parse(rawSaved).forEach(id => savedCards.add(id));
                }}
                initHeatmapPreferences();
            }} catch (e) {{
                console.warn('LocalStorage unavailable:', e);
            }}
            syncBookmarksUI();
        }}

        function toggleTheme() {{
            const cur = document.documentElement.getAttribute('data-theme') || 'light';
            const next = cur === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', next);
            updateThemeIcon(next);
            try {{
                localStorage.setItem(STORAGE_KEY_THEME, next);
            }} catch (e) {{}}
        }}

        function updateThemeIcon(theme) {{
            const el = document.getElementById('themeIcon');
            if (el) el.textContent = theme === 'dark' ? '☀️' : '🌙';
        }}

        function toggleBookmark(uid, btnEl) {{
            if (savedCards.has(uid)) {{
                savedCards.delete(uid);
            }} else {{
                savedCards.add(uid);
            }}
            try {{
                localStorage.setItem(STORAGE_KEY_SAVED, JSON.stringify(Array.from(savedCards)));
            }} catch (e) {{}}
            syncBookmarksUI();
            if (activeCategory === 'saved') {{
                applyFilters();
            }}
        }}

        function syncBookmarksUI() {{
            const badge = document.getElementById('savedCountBadge');
            if (badge) badge.textContent = savedCards.size;
            document.querySelectorAll('.gn-btn-bookmark').forEach(btn => {{
                const uid = btn.getAttribute('data-uid');
                if (savedCards.has(uid)) {{
                    btn.classList.add('saved');
                    btn.textContent = '🔖';
                }} else {{
                    btn.classList.remove('saved');
                    btn.textContent = '🔖';
                }}
            }});
        }}

        /* ======================================================================
           2. Hero Card News Slide Deck (Carousel)
           ====================================================================== */
        function goToHeroSlide(idx) {{
            if (TOTAL_HERO_SLIDES <= 0) return;
            currentHeroSlide = (idx + TOTAL_HERO_SLIDES) % TOTAL_HERO_SLIDES;
            const slides = document.querySelectorAll('.deck-slide');
            const segs = document.querySelectorAll('.deck-progress-seg');
            slides.forEach((s, i) => {{
                s.classList.toggle('active', i === currentHeroSlide);
            }});
            segs.forEach((seg, i) => {{
                seg.classList.toggle('active', i === currentHeroSlide);
                seg.classList.toggle('passed', i < currentHeroSlide);
            }});
            const ind = document.getElementById('heroSlideIndicator');
            if (ind) ind.textContent = (currentHeroSlide + 1) + ' / ' + TOTAL_HERO_SLIDES;
            resetHeroAutoPlayTimer();
        }}

        function nextHeroSlide() {{
            goToHeroSlide(currentHeroSlide + 1);
        }}

        function prevHeroSlide() {{
            goToHeroSlide(currentHeroSlide - 1);
        }}

        function resetHeroAutoPlayTimer() {{
            if (heroAutoPlayTimer) clearInterval(heroAutoPlayTimer);
            if (isHeroAutoPlaying) {{
                heroAutoPlayTimer = setInterval(() => {{
                    goToHeroSlide(currentHeroSlide + 1);
                }}, 6500);
            }}
        }}

        function toggleHeroAutoPlay() {{
            isHeroAutoPlaying = !isHeroAutoPlaying;
            const btn = document.getElementById('heroAutoPlayBtn');
            if (btn) {{
                btn.textContent = isHeroAutoPlaying ? '⏸ 자동재생 켜짐' : '▶️ 자동재생 꺼짐';
            }}
            resetHeroAutoPlayTimer();
        }}

        /* ======================================================================
           3. Category Filtering, Keyword Search & View Switcher
           ====================================================================== */
        function selectCategory(cat, tabEl) {{
            activeCategory = cat;
            document.querySelectorAll('.gn-nav-tab').forEach(t => t.classList.remove('active'));
            if (tabEl) tabEl.classList.add('active');
            applyFilters();
        }}

        function handleSearchInput(val) {{
            activeSearchQuery = (val || '').trim().toLowerCase();
            const clearBtn = document.getElementById('gnSearchClear');
            if (clearBtn) clearBtn.style.display = activeSearchQuery ? 'block' : 'none';
            document.querySelectorAll('.gn-trending-chip').forEach(c => {{
                c.classList.toggle('active', c.textContent.toLowerCase() === activeSearchQuery);
            }});
            applyFilters();
        }}

        function filterByKeyword(keyword) {{
            const input = document.getElementById('gnSearchInput');
            if (!input) return;
            if (input.value.trim() === keyword) {{
                clearSearch();
            }} else {{
                input.value = keyword;
                handleSearchInput(keyword);
            }}
        }}

        function clearSearch() {{
            const input = document.getElementById('gnSearchInput');
            if (input) input.value = '';
            handleSearchInput('');
        }}

        function resetAllFilters() {{
            clearSearch();
            const homeTab = document.querySelector('.gn-nav-tab[data-cat="all"]');
            selectCategory('all', homeTab);
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}

        function applyFilters() {{
            let totalVisible = 0;
            const sections = document.querySelectorAll('.gn-category-section');

            sections.forEach(sec => {{
                const secId = sec.getAttribute('data-section');
                const cards = sec.querySelectorAll('.gn-news-card');
                let secVisible = 0;

                cards.forEach(card => {{
                    const cardCat = card.getAttribute('data-category');
                    const cardUid = card.getAttribute('data-card-uid');
                    const searchBlob = card.getAttribute('data-search') || '';

                    let catMatch = true;
                    if (activeCategory === 'saved') {{
                        catMatch = savedCards.has(cardUid);
                    }} else if (activeCategory !== 'all') {{
                        catMatch = (cardCat === activeCategory);
                    }}

                    let searchMatch = true;
                    if (activeSearchQuery) {{
                        searchMatch = searchBlob.includes(activeSearchQuery);
                    }}

                    const visible = catMatch && searchMatch;
                    card.style.display = visible ? 'flex' : 'none';
                    if (visible) {{
                        secVisible++;
                        totalVisible++;
                    }}
                }});

                sec.style.display = secVisible > 0 ? 'block' : 'none';
            }});

            const heroSec = document.getElementById('heroBriefingSection');
            if (heroSec) {{
                heroSec.style.display = (activeCategory === 'all' && !activeSearchQuery) ? 'grid' : 'none';
            }}

            const emptyBox = document.getElementById('emptyStateBox');
            if (emptyBox) {{
                emptyBox.style.display = totalVisible === 0 ? 'block' : 'none';
            }}

            const counterEl = document.getElementById('visibleCardsCounter');
            if (counterEl) {{
                counterEl.textContent = (activeCategory === 'all' && !activeSearchQuery)
                    ? `총 ${{totalVisible}}개 카드뉴스`
                    : `검색/필터 결과 ${{totalVisible}}개 카드뉴스`;
            }}
        }}

        function setViewMode(mode) {{
            document.body.classList.toggle('view-cluster', mode === 'cluster');
            const btnCard = document.getElementById('viewBtnCard');
            const btnCluster = document.getElementById('viewBtnCluster');
            if (btnCard) btnCard.classList.toggle('active', mode === 'card');
            if (btnCluster) btnCluster.classList.toggle('active', mode === 'cluster');
        }}

        /* ======================================================================
           4. Interactive 3-Slide Card News Detail Modal
           ====================================================================== */
        function openCardModal(globalIdx) {{
            if (!ALL_CARDS || ALL_CARDS.length === 0) return;
            modalCardIdx = Math.max(0, Math.min(ALL_CARDS.length - 1, globalIdx));
            modalStepIdx = 0;
            renderModalContent();
            const modal = document.getElementById('cardNewsModal');
            if (modal) modal.classList.add('open');
            document.body.style.overflow = 'hidden';
        }}

        function closeCardModal() {{
            const modal = document.getElementById('cardNewsModal');
            if (modal) modal.classList.remove('open');
            document.body.style.overflow = '';
        }}

        function handleBackdropClick(e) {{
            if (e.target && e.target.id === 'cardNewsModal') {{
                closeCardModal();
            }}
        }}

        function setModalStep(step) {{
            modalStepIdx = Math.max(0, Math.min(2, step));
            renderModalContent();
        }}

        function nextModalStep() {{
            if (modalStepIdx < 2) {{
                modalStepIdx++;
                renderModalContent();
            }} else {{
                nextModalCard();
            }}
        }}

        function prevModalCard() {{
            modalCardIdx = (modalCardIdx - 1 + ALL_CARDS.length) % ALL_CARDS.length;
            modalStepIdx = 0;
            renderModalContent();
        }}

        function nextModalCard() {{
            modalCardIdx = (modalCardIdx + 1) % ALL_CARDS.length;
            modalStepIdx = 0;
            renderModalContent();
        }}

        function renderModalContent() {{
            const card = ALL_CARDS[modalCardIdx];
            if (!card) return;

            const stepBars = document.querySelectorAll('#cardNewsModal .modal-step-bar');
            stepBars.forEach((bar, i) => {{
                bar.classList.toggle('active', i <= modalStepIdx);
            }});

            const catBadge = document.getElementById('modalCatBadge');
            if (catBadge) {{
                catBadge.textContent = `${{card.category_icon}} ${{card.category_name}} · CARD 0${{card.card_index}}`;
            }}

            const counter = document.getElementById('modalCardCounter');
            if (counter) {{
                counter.textContent = `뉴스 ${{modalCardIdx + 1}} / ${{ALL_CARDS.length}}`;
            }}

            const stepBtn = document.getElementById('modalStepBtn');
            if (stepBtn) {{
                stepBtn.textContent = modalStepIdx < 2
                    ? `다음 슬라이드 (${{modalStepIdx + 1}}/3) ›`
                    : `다음 뉴스 카드로 ▶`;
            }}

            const srcLink = document.getElementById('modalSourceLink');
            if (srcLink) {{
                srcLink.href = card.link;
                srcLink.textContent = `${{card.cta_text}} ↗`;
            }}

            const bodyEl = document.getElementById('modalSlideBody');
            if (!bodyEl) return;

            const tagsHtml = (card.keywords || []).map(k => `<span class="gn-tag-chip">${{k}}</span>`).join(' ');

            if (modalStepIdx === 0) {{
                const mediaHtml = card.thumbnail
                    ? `<div class="deck-slide-media" style="height:175px; margin-bottom:14px;"><img src="${{card.thumbnail}}" alt="" style="width:100%;height:100%;object-fit:cover;"></div>`
                    : '';
                bodyEl.innerHTML = `
                    <div>
                        <div class="modal-step-label">SLIDE 01 / 03 · HEADLINE BRIEF</div>
                        ${{mediaHtml}}
                        <div class="deck-pub-meta" style="margin-bottom:10px;">
                            <img src="${{card.favicon}}" class="gn-pub-favicon" alt="" onerror="this.style.display='none'">
                            <span class="gn-pub-name">${{card.source}}</span>
                            <span>&middot;</span>
                            <span>${{card.time_ago}}</span>
                        </div>
                        <h3 id="modalHeadline" class="modal-headline">${{card.title}}</h3>
                        <div class="modal-quote-box">💡 핵심 키워드: “${{card.highlight_badge}}”</div>
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                        <div style="display:flex; gap:6px; flex-wrap:wrap;">${{tagsHtml}}</div>
                        <span style="font-size:0.78rem; color:var(--gn-text-muted);">슬라이드 1/3 (표지)</span>
                    </div>
                `;
            }} else if (modalStepIdx === 1) {{
                const bulletsHtml = (card.bullet_points || []).map(b => `<li>${{b}}</li>`).join('');
                bodyEl.innerHTML = `
                    <div>
                        <div class="modal-step-label">SLIDE 02 / 03 · KEY TAKEAWAYS (핵심 3단 요약)</div>
                        <h3 class="modal-headline" style="font-size:1.15rem; margin-bottom:16px;">${{card.title}}</h3>
                        <ul class="modal-bullet-list">${{bulletsHtml}}</ul>
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:16px;">
                        <span style="font-size:0.8rem; color:var(--gn-text-muted);">출처: ${{card.source}}</span>
                        <span style="font-size:0.78rem; color:var(--gn-text-muted);">슬라이드 2/3 (핵심 분석)</span>
                    </div>
                `;
            }} else {{
                let relHtml = '';
                if (card.related_articles && card.related_articles.length > 0) {{
                    const items = card.related_articles.map(r =>
                        `<li style="margin-bottom:6px;"><a href="${{r.link}}" target="_blank" rel="noopener noreferrer" style="color:var(--gn-blue-text); text-decoration:none; font-weight:600;">${{r.title}}</a> <span style="font-size:0.78rem; color:var(--gn-text-muted);">(${{r.source}})</span></li>`
                    ).join('');
                    relHtml = `<div style="margin-top:14px; padding-top:12px; border-top:1px dashed var(--gn-border);"><div style="font-size:0.8rem; font-weight:700; margin-bottom:6px;">🔗 Google News 관련 보도 클러스터</div><ul style="margin:0; padding-left:18px; font-size:0.86rem;">${{items}}</ul></div>`;
                }}
                bodyEl.innerHTML = `
                    <div>
                        <div class="modal-step-label">SLIDE 03 / 03 · INSIGHT & FULL COVERAGE</div>
                        <h3 class="modal-headline" style="font-size:1.15rem;">🔍 종합 요약 및 원문 연결</h3>
                        <div class="modal-quote-box" style="font-weight:500; line-height:1.65;">${{card.summary}}</div>
                        ${{relHtml}}
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:16px;">
                        <div style="display:flex; gap:6px;">${{tagsHtml}}</div>
                        <span style="font-size:0.78rem; color:var(--gn-text-muted);">슬라이드 3/3 (종합 요약)</span>
                    </div>
                `;
            }}
        }}

        /* ======================================================================
           5. Multi-Language Audio Player & Affirmation TTS
           ====================================================================== */
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
            if (!audio) return;
            const playBtn = document.getElementById('playMainBtn');
            const statusBadge = document.getElementById('playerStatusBadge');
            const titleEl = document.getElementById('playerCurrentTitle');
            const timeCur = document.getElementById('timeCurrent');
            const timeDur = document.getElementById('timeDuration');
            const slider = document.getElementById('progressSlider');

            if (titleEl) titleEl.innerText = '🎙️ 5분 라디오 브리핑 · ' + langNames[currentLang];

            if (audio.paused) {{
                if (playBtn) playBtn.innerHTML = '▶️';
                if (statusBadge) statusBadge.innerText = '준비됨';
            }} else {{
                if (playBtn) playBtn.innerHTML = '⏸️';
                if (statusBadge) statusBadge.innerText = '재생 중';
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
            if (!audio) return;
            if (audio.paused) {{
                pauseAllAudio();
                audio.playbackRate = currentRate;
                const playPromise = audio.play();
                if (playPromise !== undefined) {{
                    playPromise.then(() => {{
                        updatePlayerUI();
                        if (statusMsg) statusMsg.innerText = '🔊 오디오 브리핑이 재생 중입니다.';
                    }}).catch(err => {{
                        console.error('Audio play error:', err);
                        updatePlayerUI();
                        if (statusMsg) statusMsg.innerText = '⚠️ 화면을 클릭한 뒤 다시 재생 버튼을 눌러주세요.';
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
            if (!audio) return;
            audio.currentTime = parseFloat(val);
            updatePlayerUI();
        }}

        function skipTime(delta) {{
            const audio = getActiveAudio();
            if (!audio) return;
            audio.currentTime = Math.max(0, Math.min(audio.duration || 0, audio.currentTime + delta));
            updatePlayerUI();
        }}

        function cycleSpeed() {{
            const speeds = [1.0, 1.25, 1.5, 2.0];
            const nextIdx = (speeds.indexOf(currentRate) + 1) % speeds.length;
            currentRate = speeds[nextIdx];
            const audio = getActiveAudio();
            if (audio) audio.playbackRate = currentRate;
            const btn = document.getElementById('speedBtn');
            if (btn) btn.innerText = currentRate + 'x';
        }}

        function setVolume(val) {{
            const audios = document.getElementsByTagName('audio');
            for (let i = 0; i < audios.length; i++) {{
                audios[i].volume = parseFloat(val);
            }}
        }}

        function pauseAllAudio() {{
            const audios = document.getElementsByTagName('audio');
            for (let i = 0; i < audios.length; i++) {{
                audios[i].pause();
            }}
        }}

        function switchTab(lang) {{
            document.querySelectorAll('.gn-lang-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.script-content').forEach(content => content.classList.remove('active'));

            const btn = document.getElementById('btn-' + lang);
            const content = document.getElementById('content-' + lang);
            if (btn) btn.classList.add('active');
            if (content) content.classList.add('active');

            pauseAllAudio();
            currentLang = lang;
            updatePlayerUI();
        }}

        function toggleScriptDrawer() {{
            const drawer = document.getElementById('scriptDrawer');
            const btn = document.getElementById('scriptDrawerBtn');
            if (!drawer) return;
            const isOpen = drawer.classList.toggle('open');
            if (btn) {{
                btn.innerText = isOpen
                    ? '📜 5분 브리핑 전체 대본 접기 (한/영/중) ▴'
                    : '📜 5분 브리핑 전체 대본 펼치기 (한/영/중) ▾';
            }}
            if (isOpen) {{
                drawer.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
            }}
        }}

        function speakAffirmation() {{
            const el = document.getElementById('affirmationTextEl');
            if (!el || !('speechSynthesis' in window)) return;
            window.speechSynthesis.cancel();
            const text = el.textContent.replace(/"/g, '').trim();
            const utter = new SpeechSynthesisUtterance(text);
            utter.lang = 'ko-KR';
            utter.rate = 0.95;
            utter.pitch = 1.0;

            const voices = window.speechSynthesis.getVoices() || [];
            const koVoices = voices.filter(v => v.lang && (v.lang === 'ko-KR' || v.lang.startsWith('ko')));
            if (koVoices.length > 0) {{
                const preferredVoice = koVoices.find(v =>
                    /natural|neural|premium|online|google|yuna|sunhi/i.test(v.name)
                ) || koVoices[0];
                utter.voice = preferredVoice;
            }}
            window.speechSynthesis.speak(utter);
        }}

        /* ======================================================================
           8. Stock Heatmap Color Mode & Fullscreen Zoom Modal
           ====================================================================== */
        function initHeatmapPreferences() {{
            try {{
                const savedKr = localStorage.getItem('gn_heatmap_kr_colors');
                if (savedKr === '1') {{
                    document.body.classList.add('heatmap-kr-colors');
                    updateColorModeButtons(true);
                }}
            }} catch (e) {{}}
        }}

        function toggleHeatmapColorMode() {{
            document.body.classList.toggle('heatmap-kr-colors');
            const isKr = document.body.classList.contains('heatmap-kr-colors');
            try {{
                localStorage.setItem('gn_heatmap_kr_colors', isKr ? '1' : '0');
            }} catch (e) {{}}
            updateColorModeButtons(isKr);
        }}

        function updateColorModeButtons(isKr) {{
            document.querySelectorAll('.btn-color-toggle').forEach(btn => {{
                btn.textContent = isKr ? '🎨 한국식(🔴/🔵)' : '🎨 글로벌(🟢/🔴)';
            }});
        }}

        function openHeatmapZoomModal(market) {{
            const modal = document.getElementById('heatmapZoomModal');
            const titleEl = document.getElementById('heatmapModalTitle');
            const bodyEl = document.getElementById('heatmapModalBody');
            const cardId = market === 'us' ? 'card-' + CURRENT_DATE + '-econ-heatmap-us' : 'card-' + CURRENT_DATE + '-econ-heatmap-kr';
            const sourceCard = document.getElementById(cardId);
            if (!modal || !sourceCard) return;

            titleEl.textContent = market === 'us' ? '🇺🇸 미국 S&P 500 · NASDAQ 섹터 히트맵 (전체화면)' : '🇰🇷 한국 KOSPI · KOSDAQ 시가총액 히트맵 (전체화면)';

            bodyEl.innerHTML = '';
            const strip = sourceCard.querySelector('.gn-heatmap-index-strip');
            const treemap = sourceCard.querySelector('.gn-heatmap-treemap-wrap');
            const breadth = sourceCard.querySelector('.gn-heatmap-breadth');
            const legend = sourceCard.querySelector('.gn-heatmap-legend');

            if (strip) bodyEl.appendChild(strip.cloneNode(true));
            if (treemap) {{
                const treemapClone = treemap.cloneNode(true);
                treemapClone.classList.add('zoomed');
                bodyEl.appendChild(treemapClone);
            }}
            if (breadth) bodyEl.appendChild(breadth.cloneNode(true));
            if (legend) bodyEl.appendChild(legend.cloneNode(true));

            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }}

        function closeHeatmapZoomModal() {{
            const modal = document.getElementById('heatmapZoomModal');
            if (modal) modal.classList.remove('active');
            document.body.style.overflow = '';
        }}

        function handleHeatmapBackdropClick(e) {{
            if (e.target && e.target.id === 'heatmapZoomModal') {{
                closeHeatmapZoomModal();
            }}
        }}

        document.addEventListener('keydown', (e) => {{
            const modal = document.getElementById('cardNewsModal');
            if (modal && modal.classList.contains('open')) {{
                if (e.key === 'Escape') closeCardModal();
                else if (e.key === 'ArrowRight') nextModalStep();
                else if (e.key === 'ArrowLeft') prevModalCard();
            }}
            const hmModal = document.getElementById('heatmapZoomModal');
            if (hmModal && hmModal.classList.contains('active')) {{
                if (e.key === 'Escape') closeHeatmapZoomModal();
            }}
        }});

        document.addEventListener('DOMContentLoaded', () => {{
            initPreferences();
            resetHeroAutoPlayTimer();

            const audios = document.getElementsByTagName('audio');
            for (let i = 0; i < audios.length; i++) {{
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
            }}
            updatePlayerUI();
        }});
    </script>
</body>
</html>
"""
        return html_content

    def build_archive(self) -> str:
        files = glob.glob(os.path.join(self.html_dir, "briefing_*.html"))
        dates = []
        for f in files:
            basename = os.path.basename(f)
            if basename.startswith("briefing_") and basename != "latest_briefing.html":
                date_str = basename.replace("briefing_", "").replace(".html", "")
                dates.append(date_str)
        dates.sort(reverse=True)

        cards_html = ""
        weekday_ko = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        for idx, date_str in enumerate(dates, 1):
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                ko_label = f"{dt.year}년 {dt.month}월 {dt.day}일 ({weekday_ko[dt.weekday()]})"
            except Exception:
                ko_label = date_str
            badge_text = "LATEST EDITION" if idx == 1 else f"ARCHIVE #{len(dates) - idx + 1:02d}"
            cards_html += f"""
            <a href="outputs/html/briefing_{date_str}.html" class="gn-archive-card">
                <div class="gn-archive-banner">
                    <span class="gn-archive-badge">{badge_text}</span>
                    <span class="gn-archive-icon">📰</span>
                </div>
                <div class="gn-archive-body">
                    <div class="gn-archive-date">{date_str}</div>
                    <div class="gn-archive-sub">{ko_label} · 09:00 KST 발행</div>
                    <p class="gn-archive-desc">AI · 빅테크 · ArXiv 논문 · 테크 유튜브 · 글로벌 경제 · 안보 · 외교 카드뉴스 및 5분 다국어 음성 브리핑</p>
                    <div class="gn-archive-cta">카드뉴스 에디션 열람하기 &rarr;</div>
                </div>
            </a>
            """

        if not cards_html:
            cards_html = "<div style='text-align:center; padding: 60px; color: #5f6368;'>아직 발행된 브리핑이 없습니다.</div>"

        archive_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Google News 스타일 데일리 모닝 카드뉴스 브리핑 아카이브">
    <title>Google News Daily Briefing - 지난 브리핑 아카이브</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --gn-bg: #f8f9fa;
            --gn-surface: #ffffff;
            --gn-text-primary: #1f1f1f;
            --gn-text-secondary: #444746;
            --gn-text-muted: #5f6368;
            --gn-border: #dadce0;
            --gn-blue: #1a73e8;
            --gn-blue-surface: #e8f0fe;
        }}
        * {{ box-sizing: border-box; }}
        body {{
            font-family: "Pretendard", "Noto Sans KR", "Inter", -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--gn-bg);
            color: var(--gn-text-primary);
            margin: 0;
            padding: 0;
        }}
        .gn-app-header {{
            background: var(--gn-surface);
            border-bottom: 1px solid var(--gn-border);
            padding: 14px 24px;
            position: sticky;
            top: 0;
            z-index: 50;
        }}
        .gn-top-row {{
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .gn-brand {{
            display: flex;
            align-items: center;
            gap: 8px;
            text-decoration: none;
            color: var(--gn-text-primary);
            font-size: 1.25rem;
            font-weight: 700;
        }}
        .gn-g-blue {{ color: #4285F4; }}
        .gn-g-red {{ color: #EA4335; }}
        .gn-g-yellow {{ color: #FBBC04; }}
        .gn-g-green {{ color: #34A853; }}
        .gn-back-btn {{
            background: var(--gn-blue);
            color: #ffffff;
            text-decoration: none;
            padding: 8px 18px;
            border-radius: 999px;
            font-size: 0.88rem;
            font-weight: 700;
            transition: background 0.15s ease;
        }}
        .gn-back-btn:hover {{ background: #1557b0; }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 36px 24px 64px 24px;
        }}
        .archive-hero {{
            margin-bottom: 32px;
        }}
        .archive-hero h1 {{
            margin: 0 0 8px 0;
            font-size: 2rem;
            font-weight: 800;
            letter-spacing: -0.5px;
        }}
        .archive-hero p {{
            margin: 0;
            color: var(--gn-text-muted);
            font-size: 0.98rem;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 22px;
        }}
        .gn-archive-card {{
            background: var(--gn-surface);
            border: 1px solid var(--gn-border);
            border-radius: 16px;
            text-decoration: none;
            color: inherit;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            box-shadow: 0 1px 3px rgba(60,64,67,0.08);
        }}
        .gn-archive-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(60,64,67,0.14);
            border-color: var(--gn-blue);
        }}
        .gn-archive-banner {{
            background: var(--gn-blue-surface);
            padding: 14px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .gn-archive-badge {{
            font-size: 0.74rem;
            font-weight: 800;
            color: var(--gn-blue);
            letter-spacing: 0.5px;
        }}
        .gn-archive-icon {{ font-size: 1.2rem; }}
        .gn-archive-body {{
            padding: 20px;
            display: flex;
            flex-direction: column;
            flex: 1;
        }}
        .gn-archive-date {{
            font-size: 1.4rem;
            font-weight: 800;
            color: var(--gn-text-primary);
            margin-bottom: 4px;
        }}
        .gn-archive-sub {{
            font-size: 0.84rem;
            color: var(--gn-text-muted);
            font-weight: 600;
            margin-bottom: 12px;
        }}
        .gn-archive-desc {{
            font-size: 0.88rem;
            color: var(--gn-text-secondary);
            line-height: 1.55;
            margin: 0 0 18px 0;
            flex: 1;
        }}
        .gn-archive-cta {{
            font-size: 0.85rem;
            font-weight: 700;
            color: var(--gn-blue);
            text-align: right;
        }}
    </style>
</head>
<body>
    <header class="gn-app-header">
        <div class="gn-top-row">
            <a href="index.html" class="gn-brand">
                <span><span class="gn-g-blue">G</span><span class="gn-g-red">o</span><span class="gn-g-yellow">o</span><span class="gn-g-blue">g</span><span class="gn-g-green">l</span><span class="gn-g-red">e</span> News</span>
                <span style="color:#5f6368; font-weight:600; font-size:1rem;">| Daily Briefing Archives</span>
            </a>
            <a href="index.html" class="gn-back-btn">&larr; 오늘의 카드뉴스 브리핑으로 돌아가기</a>
        </div>
    </header>
    <main class="container">
        <div class="archive-hero">
            <h1>🗂️ 데일리 모닝 카드뉴스 아카이브</h1>
            <p>날짜별로 발행된 Google News 스타일 카드뉴스 브리핑 및 5분 다국어 음성 에디션 전체 목록입니다.</p>
        </div>
        <div class="grid">
            {cards_html}
        </div>
    </main>
</body>
</html>
"""
        archive_path = os.path.join(self.root_dir, "archive.html")
        with open(archive_path, "w", encoding="utf-8") as f:
            f.write(archive_html)
        return archive_path

    def save(self, md_content: str, html_content: str, date_str: str) -> Tuple[str, str]:
        md_file = os.path.join(self.md_dir, f"briefing_{date_str}.md")
        latest_md_file = os.path.join(self.md_dir, "latest_briefing.md")
        html_file = os.path.join(self.html_dir, f"briefing_{date_str}.html")
        latest_html_file = os.path.join(self.html_dir, "latest_briefing.html")

        # 1. Save standard HTML in outputs/html/ (Relative links: audio in ../audio/, archive in ../../archive.html)
        html_content_archived = html_content.replace("AUDIO_BASE_PATH", "../audio/").replace("ARCHIVE_LINK_PATH", "../../archive.html")
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content_archived)
        with open(latest_html_file, "w", encoding="utf-8") as f:
            f.write(html_content_archived)

        # 2. Save root index.html as TODAY's briefing (Relative links: audio in outputs/audio/, archive in archive.html)
        index_file = os.path.join(self.root_dir, "index.html")
        html_content_root = html_content.replace("AUDIO_BASE_PATH", "outputs/audio/").replace("ARCHIVE_LINK_PATH", "archive.html")
        with open(index_file, "w", encoding="utf-8") as f:
            f.write(html_content_root)

        # 3. Save standard Markdown + latest_briefing.md
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_content)
        with open(latest_md_file, "w", encoding="utf-8") as f:
            f.write(md_content)

        # 4. Generate the chronological archive page
        self.build_archive()

        return md_file, index_file
