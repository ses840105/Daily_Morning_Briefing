import re
from datetime import datetime
from typing import Dict, Any
from src.generators.translator import translate_text


def _clean_headline_for_speech(title: str) -> str:
    """헤드라인 내 말머리, 괄호 약어, 가운뎃점, 말줄임표를 자연스러운 구어체 호흡으로 정제합니다."""
    s = re.sub(r"\[[^\]]{1,15}\]\s*", "", title)
    s = re.sub(r"\((?:종합|상보|속보|단독|1보|2보)\)", "", s)
    s = re.sub(r"\([A-Za-z0-9\s&.\-/]{2,20}\)", "", s)
    s = re.sub(r"(\d[\d,.]*)\s*~\s*(\d[\d,.]*)", r"\1에서 \2", s)
    s = s.replace("·", ", ").replace("…", ", ").replace("...", ", ")
    s = s.replace("‘", "").replace("’", "").replace("“", "").replace("”", "")
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
        lines.append("오늘 브리핑은 인공지능과 반도체 기술 동향, 학계 최신 연구 논문과 유튜브 테크 트렌드, 그리고 글로벌 거시 경제와 안보 이슈 순서로 전해드리겠습니다.")
        lines.append("")

        # 2. 1부: AI 및 IT 테크 동향 + 논문
        lines.append("먼저 첫 번째 섹션, 인공지능과 빅테크 반도체, 그리고 학계 연구 동향입니다.")
        
        ai_items = tech_data.get("ai_headlines", [])
        if ai_items:
            for i, item in enumerate(ai_items[:3]):
                clean_title = _clean_headline_for_speech(item["title"])
                if i == 0:
                    lines.append(f"오늘 가장 주목받는 기술 소식입니다. {clean_title} 소식이 전해지며 업계의 큰 관심을 모으고 있습니다.")
                elif i == 1:
                    lines.append(f"이와 함께, {clean_title} 소식도 이어지며 차세대 인공지능 생태계 경쟁이 한층 치열해지고 있습니다.")
                else:
                    lines.append(f"아울러 반도체와 인프라 분야에서는 {clean_title} 관련 흐름이 포착되어 시장의 이목이 집중되고 있습니다.")
        
        lines.append("")
        papers = tech_data.get("arxiv_papers", [])
        if papers:
            paper_title = _clean_headline_for_speech(papers[0]["title"])
            lines.append("다음은 학계에서 주목받고 있는 아카이브 최신 인공지능 논문 소식입니다.")
            lines.append(f"오늘 공개된 주요 연구로는, {paper_title} 논문이 실시간 에이전트 평가와 추론 고도화 분야에서 높은 평가를 받고 있습니다.")

        lines.append("")
        yt_items = tech_data.get("youtube_picks", [])
        if yt_items:
            lines.append("이어서 유튜브 테크 트렌드 살펴보겠습니다.")
            for i, item in enumerate(yt_items[:2]):
                channel = item.get("channel") or item.get("source") or "주요 테크"
                clean_yt = _clean_headline_for_speech(item["title"])
                lines.append(f"{channel} 채널에서는, {clean_yt} 영상을 통해 핵심 기술 변화와 시장의 시사점을 심층 분석했습니다.")
        
        lines.append("")

        # 3. 2부: 글로벌 경제 및 군사 안보
        lines.append("계속해서 두 번째 섹션, 글로벌 거시 경제와 금융 시장, 그리고 안보 외교 동향입니다.")
        
        econ_items = econ_data.get("economy_headlines", [])
        if econ_items:
            for i, item in enumerate(econ_items[:3]):
                clean_econ = _clean_headline_for_speech(item["title"])
                if i == 0:
                    lines.append(f"먼저 금융 시장에서 가장 눈여겨볼 소식입니다. {clean_econ} 흐름이 나타나며 글로벌 투자자들의 시선이 집중되고 있습니다.")
                elif i == 1:
                    lines.append(f"외환 및 자본 시장에서는, {clean_econ} 소식이 전해지면서 향후 외국인 수급과 자산 가격 흐름에 주요 변수로 작용할 전망입니다.")
                else:
                    lines.append(f"또한 증시에서는 {clean_econ} 관련 분석이 제기되며 주요 섹터별 차별화 장세가 이어지고 있습니다.")

        lines.append("")
        mil_items = econ_data.get("military_headlines", [])
        if mil_items:
            for i, item in enumerate(mil_items[:2]):
                clean_mil = _clean_headline_for_speech(item["title"])
                if i == 0:
                    lines.append(f"국제 안보와 국방 분야에서는, {clean_mil} 소식이 가장 중요한 의제로 떠올랐습니다.")
                else:
                    lines.append(f"더불어 글로벌 방산 및 외교 무대에서는 {clean_mil} 움직임이 본격화되며 전략적 협력이 한층 강화되고 있습니다.")
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
