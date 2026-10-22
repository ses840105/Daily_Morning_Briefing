import random
from datetime import datetime

AFFIRMATIONS = [
    "나는 날마다 모든 면에서 점점 더 좋아지고 있다.",
    "내 안에는 어떤 어려움도 극복할 수 있는 무한한 지혜와 힘이 있다.",
    "오늘은 내 인생의 가장 멋진 기회들이 찾아오는 하루가 될 것이다.",
    "나는 나 자신을 있는 그대로 사랑하며, 나의 무한한 잠재력을 굳게 믿는다.",
    "내가 내리는 모든 긍정적인 결정은 큰 성공과 풍요로 연결되어 있다.",
    "어떤 시련이 와도 나는 유연하게 대처하며 한 단계 더 성장한다.",
    "나는 매 순간 감사하는 마음으로 오늘 하루가 주는 기적들을 맞이한다.",
    "나의 마음은 평온하며, 내 삶은 긍정적인 에너지로 가득 차 있다.",
    "나는 내 삶의 창조자이며, 오늘 하루도 걸작으로 만들어낼 것이다.",
    "나의 열정과 노력은 반드시 훌륭한 결실을 맺는다."
]

def get_daily_affirmation(date_str: str = None) -> str:
    """
    날짜를 시드로 사용하여 매일 고정된 하나의 확언을 순차 회전 방식으로 반환합니다.
    """
    if date_str:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return AFFIRMATIONS[dt.toordinal() % len(AFFIRMATIONS)]
        except Exception:
            try:
                seed_val = int(date_str.replace("-", ""))
                return AFFIRMATIONS[seed_val % len(AFFIRMATIONS)]
            except Exception:
                random.seed()
    else:
        return AFFIRMATIONS[datetime.now().toordinal() % len(AFFIRMATIONS)]
    
    return random.choice(AFFIRMATIONS)
