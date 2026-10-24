# -*- coding: utf-8 -*-
"""
Google News Style Card News Enricher
수집된 뉴스, 유튜브 영상, ArXiv 논문 데이터를 구글 뉴스(Google News) 및
카드 뉴스(Card News) UI에 최적화된 메타데이터(파비콘, 도메인, 핵심 요약,
키워드 태그, 3단계 카드 슬라이드 포인트, 관련 보도 클러스터)로 변환/보강합니다.
"""

import re
import urllib.parse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Dict, Any, List, Optional

# 주요 국내외 언론사 및 플랫폼 도메인 매핑 (Google S2 Favicon 연동용)
PUBLISHER_DOMAINS: Dict[str, str] = {
    "연합뉴스": "www.yna.co.kr",
    "연합뉴스 한민족센터": "www.yna.co.kr",
    "조선일보": "www.chosun.com",
    "중앙일보": "www.joongang.co.kr",
    "동아일보": "www.donga.com",
    "한겨레": "www.hani.co.kr",
    "경향신문": "www.khan.co.kr",
    "한국경제": "www.hankyung.com",
    "한국경제TV": "www.wowtv.co.kr",
    "한국경제TV뉴스": "www.wowtv.co.kr",
    "서울경제TV": "www.sentv.co.kr",
    "매일경제": "www.mk.co.kr",
    "서울경제": "www.sedaily.com",
    "파이낸셜뉴스": "www.fnnews.com",
    "머니투데이": "www.mt.co.kr",
    "이데일리": "www.edaily.co.kr",
    "아시아경제": "www.asiae.co.kr",
    "아주경제": "www.ajunews.com",
    "헤럴드경제": "biz.heraldcorp.com",
    "글로벌이코노믹": "www.g-enews.com",
    "이코노미트리뷴": "www.economytribune.co.kr",
    "데일리머니": "www.dailymoney.co.kr",
    "산경일보": "www.sankyungtoday.com",
    "경북매일": "www.kbmaeil.com",
    "전국매일신문": "www.jeonmae.co.kr",
    "전국뉴스": "www.jeonguknews.co.kr",
    "신아일보": "www.shinailbo.co.kr",
    "청년일보": "www.youthdaily.co.kr",
    "뉴스핌": "www.newspim.com",
    "뉴스1": "www.news1.kr",
    "뉴시스": "www.newsis.com",
    "전자신문": "www.etnews.com",
    "디일렉": "www.thelec.kr",
    "지디넷코리아": "zdnet.co.kr",
    "블로터": "www.bloter.net",
    "AI타임스": "www.aitimes.com",
    "인공지능신문": "www.aitimes.kr",
    "테크M": "www.techm.kr",
    "바이라인네트워크": "byline.network",
    "스타트업엔(StartupN)": "www.startupn.kr",
    "스타트업엔": "www.startupn.kr",
    "브런치": "brunch.co.kr",
    "뉴닉": "newneek.co",
    "KB Think": "www.kbthink.com",
    "네이버 프리미엄콘텐츠": "contents.premium.naver.com",
    "Daum": "news.daum.net",
    "디펜스투데이": "www.defensetoday.kr",
    "㈜한국탑뉴스": "www.koreatopnews.com",
    "한국탑뉴스": "www.koreatopnews.com",
    "KBS 뉴스": "news.kbs.co.kr",
    "MBC": "imnews.imbc.com",
    "MBCNEWS": "imnews.imbc.com",
    "SBS 뉴스": "news.sbs.co.kr",
    "JTBC": "news.jtbc.co.kr",
    "YTN": "www.ytn.co.kr",
    "뉴스TVCHOSUN": "news.tvchosun.com",
    "YouTube": "www.youtube.com",
    "Two Minute Papers": "www.youtube.com",
    "Yannic Kilcher": "www.youtube.com",
    "ArXiv": "arxiv.org",
    "GitHub": "github.com",
    "Hugging Face": "huggingface.co",
}

CATEGORY_META: Dict[str, Dict[str, Any]] = {
    "ai": {
        "id": "ai",
        "name": "AI · 머신러닝",
        "en_label": "AI & FRONTIER",
        "icon": "🤖",
        "color": "#1a73e8",
        "surface": "#e8f0fe",
        "default_tags": ["#생성형AI", "#LLM", "#머신러닝"],
        "watchpoint": "글로벌 프론티어 AI 모델의 추론 효율성 및 오픈소스 생태계 확산 추이를 주시하세요."
    },
    "tech": {
        "id": "tech",
        "name": "빅테크 · 반도체",
        "en_label": "BIGTECH & CHIP",
        "icon": "💻",
        "color": "#007b83",
        "surface": "#e4f7fb",
        "default_tags": ["#빅테크", "#AI반도체", "#클라우드"],
        "watchpoint": "AI 데이터센터 인프라 투자 규모와 HBM·맞춤형 ASIC 칩 공급망 변화를 점검하세요."
    },
    "paper": {
        "id": "paper",
        "name": "ArXiv AI 논문",
        "en_label": "ARXIV RESEARCH",
        "icon": "📚",
        "color": "#185abc",
        "surface": "#e8f0fe",
        "default_tags": ["#ArXiv", "#AI논문", "#딥러닝연구"],
        "watchpoint": "최신 학계 연구 방법론이 차세대 상용 AI 모델 아키텍처에 미칠 기술적 파급력을 확인하세요."
    },
    "youtube": {
        "id": "youtube",
        "name": "테크 유튜브 트렌드",
        "en_label": "TECH VIDEO PICK",
        "icon": "📺",
        "color": "#d93025",
        "surface": "#fce8e6",
        "default_tags": ["#테크유튜브", "#AI트렌드", "#인사이트"],
        "watchpoint": "글로벌 테크 크리에이터와 연구자들이 주목하는 핵심 시연 영상 및 기술 리뷰를 살펴보세요."
    },
    "econ": {
        "id": "econ",
        "name": "글로벌 경제 · 금융",
        "en_label": "MACRO & MARKETS",
        "icon": "📈",
        "color": "#188038",
        "surface": "#e6f4ea",
        "default_tags": ["#글로벌경제", "#금리환율", "#금융시장"],
        "watchpoint": "미 연준 통화정책 시그널과 원/달러 환율 변동성에 따른 자산 시장 수급 변화를 체크하세요."
    },
    "military": {
        "id": "military",
        "name": "군사 · 국방 안보",
        "en_label": "DEFENSE & SECURITY",
        "icon": "🛡️",
        "color": "#b06000",
        "surface": "#fef7e0",
        "default_tags": ["#국방안보", "#글로벌방산", "#지정학"],
        "watchpoint": "글로벌 방산 협력 확대와 주요 분쟁 지역의 안보 지형 변화가 공급망에 미치는 영향을 주시하세요."
    },
    "world": {
        "id": "world",
        "name": "세계 외교 · 정세",
        "en_label": "WORLD DIPLOMACY",
        "icon": "🌍",
        "color": "#1967d2",
        "surface": "#e8f0fe",
        "default_tags": ["#국제외교", "#글로벌정세", "#정상회담"],
        "watchpoint": "주요국 외교 회담 결과와 국제 통상·안보 연대 움직임에 따른 글로벌 정책 변수를 파악하세요."
    },
    "tools": {
        "id": "tools",
        "name": "AI 툴 · ML 기법",
        "en_label": "AI TOOLS & METHODS",
        "icon": "🛠️",
        "color": "#7627bb",
        "surface": "#f3e8fd",
        "default_tags": ["#AI툴", "#ML기법", "#LLM엔지니어링"],
        "watchpoint": "최신 오픈소스 AI 툴과 학습·추론 최적화 기법을 실무 파이프라인에 적용해 생산성을 극대화하세요."
    },
}


def resolve_domain_and_favicon(source: str, source_url: str = "", link: str = "") -> Dict[str, str]:
    """출처명 및 URL로부터 정확한 도메인과 Google Favicon URL을 추출합니다."""
    domain = ""
    if source_url:
        try:
            parsed = urllib.parse.urlparse(source_url)
            domain = parsed.netloc or source_url
        except Exception:
            domain = ""

    if not domain and source:
        clean_src = source.strip()
        if clean_src in PUBLISHER_DOMAINS:
            domain = PUBLISHER_DOMAINS[clean_src]
        elif clean_src.startswith("ArXiv"):
            domain = "arxiv.org"
        elif "." in clean_src and " " not in clean_src:
            domain = clean_src

    if not domain and link:
        try:
            parsed_link = urllib.parse.urlparse(link)
            if parsed_link.netloc and "news.google.com" not in parsed_link.netloc:
                domain = parsed_link.netloc
        except Exception:
            pass

    if not domain:
        domain = "news.google.com"

    favicon = f"https://www.google.com/s2/favicons?domain={domain}&sz=64"
    return {"domain": domain, "favicon": favicon}


def format_relative_time(pub_date_raw: str) -> str:
    """RSS pubDate 또는 ISO 날짜 문자열을 구글 뉴스 스타일 시간 표기로 변환합니다."""
    if not pub_date_raw:
        return "오늘"
    raw = pub_date_raw.strip()
    if any(k in raw for k in ["전", "오늘", "최근", "어제"]):
        return raw

    dt: Optional[datetime] = None
    try:
        dt = parsedate_to_datetime(raw)
    except Exception:
        pass

    if dt is None:
        try:
            if "T" in raw:
                dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            elif len(raw) >= 10 and raw[4] == "-" and raw[7] == "-":
                dt = datetime.strptime(raw[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except Exception:
            pass

    if dt is not None:
        try:
            now = datetime.now(timezone.utc)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            diff = now - dt
            hours = int(diff.total_seconds() // 3600)
            if hours < 0:
                return f"{dt.month}월 {dt.day}일"
            elif hours < 1:
                mins = max(1, int(diff.total_seconds() // 60))
                return f"{mins}분 전"
            elif hours < 24:
                return f"{hours}시간 전"
            elif hours < 48:
                return "어제"
            elif hours < 24 * 7:
                return f"{hours // 24}일 전"
            else:
                return f"{dt.month}월 {dt.day}일"
        except Exception:
            pass

    return raw[:10] if len(raw) >= 10 else "오늘"


def extract_keywords(title: str, category_id: str) -> List[str]:
    """제목에서 핵심 키워드 해시태그(최대 3개)를 자동 추출합니다."""
    keyword_rules = [
        (r"오픈AI|OpenAI|GPT", "#오픈AI"),
        (r"딥시크|DeepSeek", "#DeepSeek"),
        (r"클로드|앤트로픽|Anthropic|Claude", "#Anthropic"),
        (r"구글|제미나이|Gemini|Google", "#GoogleAI"),
        (r"엔비디아|NVIDIA", "#엔비디아"),
        (r"브로드컴|Broadcom|할라페뇨", "#AI추론칩"),
        (r"HBM|하이닉스|삼성전자|SK", "#HBM반도체"),
        (r"오픈소스|Open Source|Qwen", "#오픈소스AI"),
        (r"LLM|언어모델|초지능|AGI", "#프론티어LLM"),
        (r"로봇|휴머노이드|Humanoid|Robotic|Manipulation", "#휴머노이드로봇"),
        (r"Transformer|Diffusion|Agent|에이전트", "#AI아키텍처"),
        (r"인프라|데이터센터|서버|클라우드", "#AI인프라"),
        (r"금리|연준|Fed|기준금리", "#기준금리"),
        (r"환율|원·달러|원달러|외환", "#원달러환율"),
        (r"증시|주식|코스피|월가|투자", "#글로벌증시"),
        (r"인플레|물가|긴축|중앙은행", "#매크로경제"),
        (r"방산|국방|군사|무기", "#글로벌방산"),
        (r"안보|전쟁|우크라이나|중동|이란|대만", "#지정학안보"),
        (r"정상회담|미중|외교|유엔|EU", "#정상외교"),
        (r"특허|규제|법안|정책", "#테크정책"),
    ]
    tags = []
    for pattern, tag in keyword_rules:
        if re.search(pattern, title, re.IGNORECASE) and tag not in tags:
            tags.append(tag)
        if len(tags) >= 3:
            break

    default_tags = CATEGORY_META.get(category_id, CATEGORY_META["ai"])["default_tags"]
    for dt in default_tags:
        if len(tags) >= 3:
            break
        if dt not in tags:
            tags.append(dt)

    return tags[:3]


def extract_youtube_video_id(link: str, raw_vid: str = "") -> str:
    """YouTube URL에서 11자리 videoId를 추출합니다."""
    if raw_vid and len(raw_vid) == 11:
        return raw_vid
    if not link:
        return ""
    m = re.search(r"(?:v=|youtu\.be/|/vi/|/v/)([a-zA-Z0-9_-]{11})", link)
    return m.group(1) if m else ""


def generate_card_news_content(item: Dict[str, Any], category_id: str, idx: int = 1) -> Dict[str, Any]:
    """
    단일 뉴스/논문/영상 아이템을 카드 뉴스(Card News) 구조로 보강합니다.
    - summary: 카드 본문에 바로 표시되는 핵심 요약 (2~3문장)
    - highlight_badge: 카드 상단 비주얼 배너에 표시되는 핵심 키워드 구문
    - bullet_points: 카드뉴스 상세 슬라이드 모달용 3단계 요약 (배경 / 핵심 / 전망)
    """
    title = item.get("title", "").strip()
    source = (item.get("source") or item.get("channel") or "Google News").strip()
    link = item.get("link", "#").strip()
    cat_info = CATEGORY_META.get(category_id, CATEGORY_META["ai"])

    # 도메인 및 파비콘
    dom_info = resolve_domain_and_favicon(source, item.get("source_url", ""), link)
    time_ago = format_relative_time(item.get("pub_date") or item.get("published") or "")
    keywords = extract_keywords(title, category_id)

    # YouTube 썸네일 처리
    video_id = extract_youtube_video_id(link, item.get("video_id", ""))
    thumbnail = item.get("thumbnail", "")
    if not thumbnail and video_id:
        thumbnail = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

    # 하이라이트 구문 추출 (따옴표 안의 구문 또는 제목 앞부분 핵심어, 어절 단위 절삭)
    quoted = re.findall(r"['‘“\"]([^'’”\"]{3,28})['’”\"]", title)
    if quoted:
        highlight_badge = quoted[0]
    else:
        parts = re.split(r"[…,:?!]| - ", title)
        first_part = re.sub(r"^\[[^\]]+\]\s*", "", parts[0]).strip()
        if len(first_part) > 28:
            cut = first_part[:28]
            if " " in cut:
                cut = cut.rsplit(" ", 1)[0]
            highlight_badge = cut + "…"
        else:
            highlight_badge = first_part

    # 기존 요약(ArXiv 초록, YouTube 설명 등) 정제
    raw_summary = (item.get("summary") or item.get("description") or "").strip()
    if raw_summary:
        if category_id == "youtube":
            cleaned_lines = []
            for line in raw_summary.splitlines():
                line_s = line.strip()
                if not line_s:
                    continue
                if any(skip in line_s.lower() for skip in ["check out lambda", "patreon", "sponsor", "sign up for"]):
                    continue
                line_s = re.sub(r"https?://\S+", "", line_s).strip()
                if line_s:
                    cleaned_lines.append(line_s)
            raw_summary = " ".join(cleaned_lines)
        else:
            raw_summary = re.sub(r"https?://\S+", "", raw_summary).strip()
            raw_summary = re.sub(r"\s+", " ", raw_summary)

    # 카테고리별 맞춤형 카드뉴스 요약 및 3단계 슬라이드 포인트 생성
    if category_id == "paper":
        primary_cat = item.get("primary_category", "cs.AI")
        comment = item.get("comment", "ArXiv Preprint")
        if raw_summary and len(raw_summary) > 25:
            short_abs = raw_summary[:185].rsplit(" ", 1)[0] + "..." if len(raw_summary) > 185 else raw_summary
            summary_text = f"[{primary_cat}] {short_abs}"
        else:
            summary_text = f"ArXiv 최신 공개 AI/ML 연구 논문({source})으로, 차세대 신경망 모델링 및 학습 최적화 방법론을 제안합니다."
        bullets = [
            f"📌 연구 주제: {title}",
            f"🔬 핵심 초록: {raw_summary[:240] + '...' if len(raw_summary) > 240 else (raw_summary or '차세대 AI 아키텍처 및 정책 학습 효율성 개선 연구')}",
            f"🎯 학술 시사점: {comment or 'ArXiv 최신 프리프린트'} · 실무 AI 엔지니어링 및 후속 모델 벤치마크 적용 가능성 주목"
        ]
    elif category_id == "youtube":
        views_str = item.get("views", "")
        meta_prefix = f"[{views_str}] " if views_str else ""
        if raw_summary and len(raw_summary) > 20:
            short_desc = raw_summary[:150] + ("..." if len(raw_summary) > 150 else "")
            summary_text = f"{meta_prefix}{source} 채널의 최신 테크 브리핑 영상입니다. {short_desc}"
        else:
            summary_text = f"{meta_prefix}{source} 채널의 주요 테크 분석 영상으로, '{highlight_badge}' 관련 핵심 기술 변화와 시사점을 다룹니다."
        bullets = [
            f"🎬 핵심 토픽: {title}",
            f"📺 채널 인사이트: {source} 채널의 시각적 데모 및 심층 기술/시장 분석 리뷰",
            f"💡 시청 포인트: {cat_info['watchpoint']}"
        ]
    elif category_id == "ai":
        summary_text = (
            f"{source} 보도에 따르면 '{highlight_badge}' 이슈가 AI·머신러닝 생태계의 주요 화두로 부각되었습니다. "
            f"프론티어 모델 경쟁력 강화와 엔지니어링 최적화 관점에서 업계의 이목이 집중되고 있습니다."
        )
        bullets = [
            f"📌 핵심 헤드라인: {title}",
            f"🔍 기술 배경: {', '.join(keywords)} 중심의 생성형 AI 및 모델 최적화 패러다임 가속화",
            f"🎯 업계 관전 포인트: {cat_info['watchpoint']}"
        ]
    elif category_id == "tech":
        summary_text = (
            f"{source}에서 전한 빅테크·반도체 주요 소식입니다. "
            f"글로벌 AI 인프라 확충과 차세대 반도체 공급망 재편 속에서 기업들의 대규모 투자 및 기술 동맹이 구체화되고 있습니다."
        )
        bullets = [
            f"📌 핵심 헤드라인: {title}",
            f"🔍 산업 맥락: {', '.join(keywords)} 분야의 글로벌 빅테크 자본 지출(CapEx) 및 공급망 경쟁 심화",
            f"🎯 시장 관전 포인트: {cat_info['watchpoint']}"
        ]
    elif category_id == "econ":
        summary_text = (
            f"{source} 분석에 따르면 글로벌 금리·환율 및 거시경제 지표 변화에 따라 금융 시장의 변동성이 확대되고 있습니다. "
            f"통화 정책 방향성과 외국인 수급 흐름에 대한 면밀한 점검이 필요한 시점입니다."
        )
        bullets = [
            f"📌 핵심 헤드라인: {title}",
            f"🔍 매크로 진단: {', '.join(keywords)} 변수에 따른 대출·환율·증시 연쇄 파급 효과 분석",
            f"🎯 투자 관전 포인트: {cat_info['watchpoint']}"
        ]
    elif category_id == "military":
        summary_text = (
            f"{source} 보도 기준, 국제 국방·안보 및 방산 협력 분야에서 주요 움직임이 포착되었습니다. "
            f"지역 안보 지형 변화와 방위산업 공급망 파트너십 강화가 핵심 의제로 다뤄지고 있습니다."
        )
        bullets = [
            f"📌 핵심 헤드라인: {title}",
            f"🔍 안보 맥락: {', '.join(keywords)} 중심의 국가 간 국방 협력 및 지정학적 리스크 관리",
            f"🎯 전략 관전 포인트: {cat_info['watchpoint']}"
        ]
    elif category_id == "tools":
        custom_bullets = item.get("bullet_points")
        if custom_bullets and len(custom_bullets) >= 3:
            bullets = custom_bullets[:3]
        else:
            bullets = [
                f"🛠️ 도구/기법 개요: {title}",
                f"⚙️ 핵심 원리: {raw_summary[:200] if raw_summary else (', '.join(keywords) + ' 기반의 최신 AI/ML 엔지니어링 최적화 기법')}",
                f"🚀 실무 활용 포인트: {cat_info['watchpoint']}"
            ]
        summary_text = raw_summary if (raw_summary and len(raw_summary) > 25) else (
            f"{source}에서 주목받는 최신 AI/ML 도구 및 기법입니다. "
            f"모델 서빙, 프롬프트 엔지니어링, 파인튜닝 및 자율 에이전트 구축 등 실무 파이프라인의 효율성을 획기적으로 개선합니다."
        )
    else:  # world
        summary_text = (
            f"{source}에서 보도한 글로벌 외교·국제 정세 핵심 뉴스입니다. "
            f"주요국 간 정상 외교와 전략적 소통이 이어지며 향후 국제 질서와 통상 환경에 주요 변수로 작용할 전망입니다."
        )
        bullets = [
            f"📌 핵심 헤드라인: {title}",
            f"🔍 국제 정세: {', '.join(keywords)} 관련 주요국 외교 채널 가동 및 다자간 이해관계 조율",
            f"🎯 외교 관전 포인트: {cat_info['watchpoint']}"
        ]

    enriched = dict(item)
    enriched.update({
        "title": title,
        "source": source,
        "link": link,
        "domain": dom_info["domain"],
        "favicon": dom_info["favicon"],
        "time_ago": time_ago,
        "category_id": category_id,
        "category_name": cat_info["name"],
        "category_en": cat_info["en_label"],
        "category_icon": cat_info["icon"],
        "category_color": cat_info["color"],
        "category_surface": cat_info["surface"],
        "keywords": keywords,
        "highlight_badge": highlight_badge,
        "summary": summary_text,
        "bullet_points": bullets,
        "video_id": video_id,
        "thumbnail": thumbnail,
        "card_index": idx,
        "related_articles": list(item.get("related_articles", [])),
    })
    return enriched


def enrich_section_items(items: List[Dict[str, Any]], category_id: str) -> List[Dict[str, Any]]:
    """
    섹션 내 모든 아이템을 카드뉴스 포맷으로 변환하고,
    관련 기사(Google News Full Coverage 스타일 클러스터)를 상호 연결합니다.
    """
    enriched_list = [
        generate_card_news_content(it, category_id, idx=i + 1)
        for i, it in enumerate(items)
    ]

    # Google News 스타일 관련 보도(Related Coverage) 자동 클러스터링 보강
    for i, card in enumerate(enriched_list):
        if card["related_articles"]:
            continue
        card_tags = set(card["keywords"])
        related_candidates = []
        for j, other in enumerate(enriched_list):
            if i == j:
                continue
            shared = card_tags.intersection(set(other["keywords"]))
            if shared:
                related_candidates.append({
                    "title": other["title"],
                    "source": other["source"],
                    "link": other["link"]
                })
            if len(related_candidates) >= 2:
                break
        # 대표 헤드라인 카드(첫 번째 카드)는 최소 1개의 관련 보도를 보여주어 Google News 클러스터 느낌을 강화
        if i == 0 and not related_candidates and len(enriched_list) > 1:
            related_candidates.append({
                "title": enriched_list[1]["title"],
                "source": enriched_list[1]["source"],
                "link": enriched_list[1]["link"]
            })
        card["related_articles"] = related_candidates[:2]

    return enriched_list
