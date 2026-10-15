# 📰 Daily Morning Briefing & Voice News (데일리 모닝 브리핑)

매일 아침 **09:00** 기준으로 어제부터 오늘까지의 최신 **AI/ML/IT 기술 동향, 유튜브 트렌드, 글로벌 경제, 군사/안보, 세계 정세**를 종합 수집하여 **3페이지 분량의 데일리 신문(Markdown/HTML)**과 **3분 라디오 음성 브리핑(TTS/AI Audio)**을 자동 발행하는 인텔리전스 시스템입니다.

---

## 🏛️ 신문 구성 (3-Page Layout)

### 📄 [Page 1] 🤖 최신 ML · AI · IT 테크 & 유튜브 트렌드
- **AI & Frontier LLM**: 오픈AI, 딥시크, 글로벌 연구진의 최신 모델 및 벤치마크, 오픈소스 프로젝트
- **YouTube Tech Picks**: Two Minute Papers, Yannic Kilcher 및 국내외 화제의 테크 영상 Pick
- **BigTech & Semiconductor**: 엔비디아, 빅테크, AI 칩, 클라우드 인프라 동향

### 📄 [Page 2] 🌐 글로벌 경제 · 군사/안보 · 세계 정세
- **Macro Economy & Markets**: 미국 연준 기준금리, 원/달러 환율, 글로벌 증시 및 유가 동향
- **Military & Defense**: 글로벌 방산, 무기 체계, 지정학적 분쟁(우크라이나, 중동, 대만해협 등)
- **World Diplomacy**: 주요국 정상회담 및 글로벌 외교 현안

### 📄 [Page 3] 💡 오늘의 1분 브리핑 & 핵심 시사점 (Executive Brief)
- **바쁜 아침 1분 3대 헤드라인 요약**: AI/기술, 경제/금융, 안보/세계 1줄 요약
- **오늘의 핵심 키워드 5선**: 해시태그 기반 오늘의 핵심 테마
- **오늘의 관전 포인트 (Watchpoints)**: 엔지니어링, 거시 금융, 지정학 체크리스트

---

## 🎙️ 3분 라디오 음성 브리핑 (Voice News / TTS)
- macOS의 자연스러운 한국어 아나운서 음성(`Yuna`)을 기반으로 한 구어체 대본 자동 생성.
- 바쁜 아침 출근 준비를 하며 3분 동안 라디오 방송처럼 핵심 뉴스 청취 가능.
- 생성된 오디오 파일(`audio/latest_briefing.aiff`)은 언제든 즉시 재생 가능.

---

## ⏰ 매일 아침 09:00 자동 실행 스케줄러 (`launchd`)
macOS 시스템 데몬인 `launchd`에 등록되어 **매일 오전 09:00:00**에 자동으로 발행됩니다:
- **등록 서비스**: `com.essim.morningbriefing` (`~/Library/LaunchAgents/com.essim.morningbriefing.plist`)
- **자동 동작**: 09:00 정각 뉴스 수집 ➔ 신문(MD/HTML) 렌더링 ➔ 오디오 파일 생성 ➔ **macOS 시스템 알림 배너 도착**.

---

## 🚀 수동 실행 명령어 (언제든 즉시 확인)

```bash
cd /Users/essim/Desktop/Daily_Morning_Briefing

# 1. 신문 및 오디오 파일 즉시 생성 + macOS 알림
./run_briefing.sh

# 2. 신문 생성 후 브라우저(Safari/Chrome)에서 웹 신문으로 바로 열기
./run_briefing.sh --open-html

# 3. 신문 생성 후 아나운서 음성(TTS)으로 즉시 낭독 듣기
./run_briefing.sh --voice

# 4. 이미 생성된 오늘자 오디오 브리핑 바로 듣기
./run_briefing.sh --play

# 5. 터미널 화면에 마크다운 신문 전문 출력
./run_briefing.sh --print
```
