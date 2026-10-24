import re
from datetime import datetime
from typing import Dict, Any
from src.generators.translator import translate_text


def _clean_headline_for_speech(title: str) -> str:
    """헤드라인 내 말머리, 클릭베이트 연쇄, 한자 약어, 괄호 약어, 기호를 자연스러운 구어체 호흡으로 정제합니다."""
    s = title.strip()

    # 1. 기사 말머리 및 분류 태그 제거
    s = re.sub(r"\[[^\]]{1,15}\]\s*", "", s)
    s = re.sub(r"\((?:종합|상보|속보|단독|1보|2보)\)", "", s)
    s = re.sub(r"\([A-Za-z0-9\s&.\-/]{2,20}\)", "", s)

    # 2. 클릭베이트 연쇄 및 화살표 구분자 분할 (->, =>, >>, <<, ▶, ▷, |, =)
    parts = re.split(r"\s*(?:->|=>|>>|<<|▶|▷|►|▻|=|\|)\s*", s)
    if parts:
        valid_parts = [p.strip() for p in parts if p.strip()]
        if valid_parts:
            s = valid_parts[0]
            # 첫 구절이 너무 짧은 경우(예: '속보') 두 번째 구절까지 자연스럽게 연결
            if len(s) < 15 and len(valid_parts) > 1:
                s = f"{s}, {valid_parts[1]}"

    # 3. 주요 뉴스 한자 약어 자연스러운 한글 독음 변환
    hanja_map = {
        "發": "발 ",
        "美": "미국 ",
        "韓": "한국 ",
        "中": "중국 ",
        "日": "일본 ",
        "北": "북한 ",
        "對": "대 ",
        "與": "여당 ",
        "野": "야당 ",
        "英": "영국 ",
        "獨": "독일 ",
        "佛": "프랑스 ",
        "俄": "러시아 ",
        "軍": "군 ",
        "尹": "윤 ",
        "金": "김 ",
        "李": "이 ",
        "前": "전 ",
        "後": "후 ",
        "重": "중 ",
        "行": "행 ",
    }
    for h, k in hanja_map.items():
        s = s.replace(h, k)
    s = re.sub(r"(?<![가-힣])러\s*[·•,]\s*", "러시아, ", s)

    # 4. 숫자 범위 및 호흡 부호 변환
    s = re.sub(r"(\d[\d,.]*)\s*~\s*(\d[\d,.]*)", r"\1에서 \2", s)
    s = s.replace("·", ", ").replace("…", ", ").replace("...", ", ")
    s = s.replace("‘", "").replace("’", "").replace("“", "").replace("”", "").replace('"', "").replace("'", "")
    s = re.sub(r"[:;,~]+$", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


class VoiceScriptBuilder:
    """
    Neural TTS 아나운서 낭독을 위한 자연스러운 5분 라디오 모닝 브리핑 음성 대본 생성기
    """
    def build_scripts(self, tech_data: Dict[str, Any], econ_data: Dict[str, Any], affirmation: str, date_str: str) -> Dict[str, str]:
        lines = []

        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            korean_date = f"{dt.year}년 {dt.month}월 {dt.day}일"
        except Exception:
            korean_date = date_str

        # 1. 오프닝
        lines.append(f"안녕하십니까. {korean_date}, 데일리 모닝 인텔리전스 브리핑입니다.")
        lines.append("오늘 하루를 여시는 여러분을 위해, 밤사이 글로벌 시장과 기술 생태계에서 일어난 핵심 소식을 알기 쉽게 정리해 드립니다.")
        lines.append("오늘 브리핑은 인공지능과 반도체 기술 동향, 학계 최신 연구 논문과 유튜브 테크 트렌드, 주목할 최신 AI 툴과 기법, 그리고 글로벌 거시 경제와 안보 이슈 순서로 전해드리겠습니다.")
        lines.append("")

        # 2. 1부: AI 및 IT 테크 동향 + 논문
        lines.append("먼저 첫 번째 섹션, 인공지능과 빅테크 반도체, 그리고 학계 연구 동향입니다.")
        
        ai_items = tech_data.get("ai_headlines", [])
        if ai_items:
            for i, item in enumerate(ai_items[:3]):
                clean_title = _clean_headline_for_speech(item["title"])
                if i == 0:
                    lines.append(f"오늘 가장 주목받는 기술 소식입니다. {clean_title} 소식이 전해지며 글로벌 테크 업계의 큰 관심을 모으고 있습니다.")
                elif i == 1:
                    lines.append(f"이와 함께 차세대 모델 및 인프라 동향으로는, {clean_title} 흐름이 이어지며 생태계 주도권 경쟁이 한층 가열되는 모습입니다.")
                else:
                    lines.append(f"아울러 반도체와 클라우드 공급망에서는 {clean_title} 관련 분석이 제기되어 시장 참여자들의 시선이 집중되고 있습니다.")
        
        lines.append("")
        papers = tech_data.get("arxiv_papers", [])
        if papers:
            raw_paper_title = papers[0]["title"]
            clean_paper = _clean_headline_for_speech(raw_paper_title)
            # 영문 제목인 경우 한국어로 자연스럽게 번역
            if not re.search(r"[가-힣]", clean_paper):
                try:
                    clean_paper = translate_text(clean_paper, "ko")
                    clean_paper = _clean_headline_for_speech(clean_paper)
                except Exception:
                    pass
            lines.append("다음은 학계에서 주목받고 있는 아카이브 최신 인공지능 연구 소식입니다.")
            lines.append(f"오늘 발표된 주요 논문으로는, {clean_paper} 연구가 공개되어 추론 효율성과 자율 에이전트 고도화 측면에서 높은 평가를 받고 있습니다.")

        lines.append("")
        yt_items = tech_data.get("youtube_picks", [])
        if yt_items:
            lines.append("이어서 유튜브 화제의 테크 영상 살펴보겠습니다.")
            for i, item in enumerate(yt_items[:2]):
                channel = item.get("channel") or item.get("source") or "주요 테크"
                clean_yt = _clean_headline_for_speech(item["title"])
                # 영문 제목인 경우 한국어로 번역하여 아나운서 발음 최적화
                if not re.search(r"[가-힣]", clean_yt):
                    try:
                        clean_yt = translate_text(clean_yt, "ko")
                        clean_yt = _clean_headline_for_speech(clean_yt)
                    except Exception:
                        pass

                if i == 0:
                    lines.append(f"먼저 {channel}에서는 {clean_yt}를 집중 조명하며 기술 혁신이 가져올 변화를 짚었습니다.")
                else:
                    lines.append(f"또한 {channel} 채널에서는 {clean_yt}에 주목하며 실무진과 개발자들이 눈여겨볼 핵심 시사점을 전했습니다.")
        
        lines.append("")

        tools_items = tech_data.get("ai_tools", [])
        if tools_items:
            lines.append("이어서 실무 개발자와 연구진이 주목해야 할 최신 AI/ML 툴과 기법 소개해 드립니다.")
            for i, item in enumerate(tools_items[:2]):
                clean_tool_title = _clean_headline_for_speech(item["title"])
                raw_tool_summary = item.get("summary", "")
                clean_tool_desc = _clean_headline_for_speech(raw_tool_summary[:120])
                if i == 0:
                    lines.append(f"먼저 주목할 도구로는, {clean_tool_title}입니다. {clean_tool_desc}")
                else:
                    lines.append(f"또한 핵심 기법으로는, {clean_tool_title}에 주목할 만합니다. {clean_tool_desc}")
            lines.append("")

        # 3. 2부: 글로벌 경제 및 군사 안보
        lines.append("계속해서 두 번째 섹션, 글로벌 거시 경제와 금융 시장, 그리고 안보 외교 동향입니다.")
        
        econ_items = econ_data.get("economy_headlines", [])
        if econ_items:
            for i, item in enumerate(econ_items[:3]):
                clean_econ = _clean_headline_for_speech(item["title"])
                if i == 0:
                    lines.append(f"먼저 금융 시장에서 가장 눈여겨볼 소식입니다. {clean_econ} 소식이 전해지며 투자자들의 관심이 쏠렸습니다.")
                elif i == 1:
                    lines.append(f"이어서 외환 및 거시 지표를 보면, {clean_econ} 흐름이 감지되어 향후 자산 가격과 유동성에 주요 변수로 작용할 전망입니다.")
                else:
                    lines.append(f"또한 산업과 증시 전반에서는 {clean_econ} 관련 진단이 나오며 섹터별 차별화 양상이 이어지고 있습니다.")

        lines.append("")
        mil_items = econ_data.get("military_headlines", [])
        if mil_items:
            for i, item in enumerate(mil_items[:2]):
                clean_mil = _clean_headline_for_speech(item["title"])
                if i == 0:
                    lines.append(f"국제 안보와 국방 분야에서는, {clean_mil} 소식이 주요 의제로 부각되었습니다.")
                else:
                    lines.append(f"아울러 글로벌 방산 및 외교 협력 무대에서는 {clean_mil} 동향이 확인되며 지정학적 리스크 관리가 강조되고 있습니다.")
        lines.append("")

        # 4. 3부: 오늘 하루 주목할 포인트
        lines.append("세 번째 섹션, 오늘 하루 꼭 챙겨보셔야 할 세 가지 핵심 관전 포인트입니다.")
        lines.append("첫째, 차세대 인공지능 에이전트 기술의 발전과 에이치비엠 포 등 맞춤형 반도체 공급망 재편 추이를 눈여겨보시기 바랍니다.")
        lines.append("둘째, 미국 연준의 통화정책 방향성과 원달러 환율 흐름, 그리고 주요 빅테크 기업들의 실적 가이던스를 면밀히 점검하셔야겠습니다.")
        lines.append("셋째, 글로벌 방산 수주 확대와 주요국 간 통상 및 외교 협상 일정을 주시하며 시장 변동성에 대비하시길 권해드립니다.")
        lines.append("")

        # 5. 아침 명상 및 클로징
        lines.append("끝으로, 오늘 하루를 활기차게 열어줄 아침 긍정 확언입니다.")
        lines.append("편안하게 호흡을 가다듬으시고, 이 문장을 마음속으로 함께 되뇌어 보시기 바랍니다.")
        lines.append(f"{affirmation}")
        lines.append("오늘 하루도 여러분의 잠재력을 마음껏 발휘하시는 뜻깊은 시간 되시기를 바랍니다. 이상으로 데일리 모닝 인텔리전스 브리핑을 마칩니다. 경청해 주셔서 감사합니다.")

        ko_script = "\n".join(lines)
        
        # 번역 진행 (영어, 중국어)
        print("[VoiceScriptBuilder] Translating script to English...")
        en_script = translate_text(ko_script, "en")
        print("[VoiceScriptBuilder] Translating script to Chinese...")
        zh_script = translate_text(ko_script, "zh")

        return {
            "ko": ko_script,
            "en": en_script,
            "zh": zh_script
        }
