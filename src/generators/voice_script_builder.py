from datetime import datetime
from typing import Dict, Any
from src.generators.translator import translate_text

class VoiceScriptBuilder:
    """
    macOS TTS(say) 낭독을 위한 자연스러운 5분 라디오 모닝 브리핑 음성 대본 생성기
    """
    def build_scripts(self, tech_data: Dict[str, Any], econ_data: Dict[str, Any], affirmation: str, date_str: str) -> Dict[str, str]:
        lines = []

        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            korean_date = f"{dt.year}년 {dt.month}월 {dt.day}일"
        except Exception:
            korean_date = date_str

        # 1. 오프닝
        lines.append(f"안녕하십니까. {korean_date}, 데일리 모닝 인텔리전스 브리핑을 시작하겠습니다.")
        lines.append("오늘 하루를 준비하시는 여러분을 위해, 어제부터 밤사이 일어난 핵심 뉴스와 글로벌 동향을 심도 있게 전해드립니다.")
        lines.append("본 브리핑은 인공지능 기술과 논문 동향, 유튜브 테크 트렌드, 글로벌 거시 경제와 지정학적 이슈, 그리고 아침 긍정 명상 순서로 진행됩니다.")
        lines.append("그럼 첫 번째 소식부터 자세히 살펴보겠습니다.")
        lines.append("")

        # 2. 1부: AI 및 IT 테크 동향 + 논문
        lines.append("첫 번째 섹션, 최신 인공지능과 IT 기술, 그리고 연구 논문 동향입니다.")
        
        ai_items = tech_data.get("ai_headlines", [])
        if ai_items:
            lines.append("먼저 가장 눈에 띄는 AI 주요 소식입니다.")
            for i, item in enumerate(ai_items[:3]):
                if i == 0:
                    lines.append(f"가장 헤드라인을 장식한 뉴스로는, {item['title']} 소식이 있습니다.")
                elif i == 1:
                    lines.append(f"이어서 주목할 만한 소식으로 {item['title']}에 대한 내용이 보고되었습니다.")
                else:
                    lines.append(f"또한 {item['title']} 관련 동향도 포착되어, 업계 관계자들의 면밀한 분석이 이어지고 있습니다.")
        
        lines.append("")
        papers = tech_data.get("arxiv_papers", [])
        if papers:
            lines.append("다음은 학계에서 주목받고 있는 최신 AI 머신러닝 논문 소식입니다.")
            lines.append(f"오늘 새롭게 발표된 주요 논문으로는, {papers[0]['title']} 연구가 학계의 높은 관심을 받고 있습니다.")

        lines.append("")
        lines.append("다음은 유튜브 테크 트렌드입니다.")
        yt_items = tech_data.get("youtube_picks", [])
        if yt_items:
            for i, item in enumerate(yt_items[:2]):
                channel = item.get('channel', '채널')
                lines.append(f"{channel} 채널에서는 {item['title']} 영상을 공개하여 기술적인 분석과 함께 높은 조회수를 기록하고 있습니다.")
        
        lines.append("")

        # 3. 2부: 글로벌 경제 및 군사 안보
        lines.append("두 번째 섹션, 글로벌 거시 경제 및 군사 안보 동향입니다.")
        
        econ_items = econ_data.get("economy_headlines", [])
        if econ_items:
            lines.append("글로벌 경제 및 금융 시장의 주요 소식입니다.")
            for i, item in enumerate(econ_items[:3]):
                if i == 0:
                    lines.append(f"가장 핵심적인 매크로 경제 지표 관련 뉴스로, {item['title']} 소식이 시장의 주목을 받고 있습니다.")
                elif i == 1:
                    lines.append(f"아울러 투자자들의 이목이 쏠린 {item['title']} 소식이 전해지면서, 관련 자산군의 가격 흐름에 영향을 줄 가능성이 높습니다.")
                else:
                    lines.append(f"추가적으로 금융시장에서 {item['title']}에 관한 분석 보고서가 나오며 투자 심리에 변수로 작용할 전망입니다.")

        lines.append("")
        mil_items = econ_data.get("military_headlines", [])
        if mil_items:
            for i, item in enumerate(mil_items[:2]):
                if i == 0:
                    lines.append(f"국제 외교 및 국방 분야에서는 {item['title']} 관련 소식이 가장 중요한 사안으로 대두되었습니다.")
                else:
                    lines.append(f"또한 지역 안보와 관련해 {item['title']} 사태가 지속되며 긴장감을 늦출 수 없는 상황입니다.")
        lines.append("")

        # 4. 3부: 오늘 하루 주목할 포인트
        lines.append("세 번째 섹션, 오늘 하루 성공적인 비즈니스를 위해 반드시 체크해야 할 관전 포인트입니다.")
        lines.append("첫째, 글로벌 빅테크 기업들의 신규 AI 모델 성능 공개 여부와 최신 논문들의 응용 가능성을 지속적으로 모니터링해야 합니다.")
        lines.append("둘째, 원달러 환율의 단기 변동성과 주요국 중앙은행의 기준금리 관련 발언을 주시하시기 바랍니다.")
        lines.append("셋째, 지정학적 이슈와 글로벌 무역 규제 동향에 따른 경제적 파급 효과를 주의 깊게 살피시길 권해드립니다.")
        lines.append("")

        # 5. 아침 명상 및 클로징
        lines.append("마지막으로, 당신의 하루를 눈부시게 밝혀줄 오늘의 긍정 확언입니다.")
        lines.append("편안하게 숨을 들이마시고 내쉬며, 이 문장을 마음속으로 세 번 되뇌어 보십시오.")
        lines.append(f"'{affirmation}'")
        lines.append("오늘 하루도 당신의 잠재력을 마음껏 발휘하시기를 바라며, 이상으로 오늘의 모닝 브리핑을 모두 마치겠습니다. 대단히 감사합니다.")

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
