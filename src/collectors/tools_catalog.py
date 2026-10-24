# -*- coding: utf-8 -*-
"""
Curated Catalog of Cutting-Edge AI/ML Tools & Techniques
Includes 24 high-value, modern tools and ML methods rotated deterministically by date
and deduplicated against recent days' briefings.
"""

from typing import List, Dict, Any

TOOLS_AND_METHODS_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "mcp-protocol",
        "title": "MCP (Model Context Protocol) - 에이전트 도구 표준 연동 규격",
        "category_type": "tool",
        "source": "Anthropic / Open Source",
        "source_url": "https://modelcontextprotocol.io",
        "link": "https://github.com/modelcontextprotocol",
        "summary": "LLM 애플리케이션과 로컬/원격 데이터 소스 및 도구(Tools)를 안전하고 표준화된 방식으로 연결하는 오픈 프로토콜입니다. 에이전트가 로컬 파일, DB, 웹 API를 일관된 인터페이스로 탐색하고 호출할 수 있도록 지원합니다.",
        "bullet_points": [
            "🛠️ 도구/기법 개요: Anthropic이 주도하고 리눅스 재단 등 오픈소스 진영이 채택한 에이전트-도구 간 표준 프로토콜 규격",
            "⚙️ 핵심 원리 및 특징: JSON-RPC 2.0 기반 클라이언트-서버 구조로, 도구 목록 제공(Tools), 리소스 읽기(Resources), 프롬프트 템플릿(Prompts)을 단일 규격으로 추상화",
            "🚀 실무 활용 포인트: 레거시 API 및 사내 데이터베이스를 MCP 서버로 한 번만 래핑하면 Claude, Gemini 등 다양한 에이전트 런타임에서 즉시 재사용 가능"
        ],
        "keywords": ["#MCP", "#AI에이전트", "#도구연동", "#Anthropic", "#오픈소스"]
    },
    {
        "id": "grpo-reasoning",
        "title": "GRPO (Group Relative Policy Optimization) - 추론 강화학습 기법",
        "category_type": "method",
        "source": "DeepSeek Research",
        "source_url": "https://github.com/deepseek-ai",
        "link": "https://arxiv.org/abs/2402.03300",
        "summary": "별도의 거대한 가치(Critic) 신경망 없이, 동일 프롬프트에 대한 여러 출력 그룹의 상대적 보상만으로 모델을 강화학습시키는 혁신적 기법입니다. DeepSeek-R1의 핵심 추론 능력 도약의 기반이 되었습니다.",
        "bullet_points": [
            "🛠️ 도구/기법 개요: PPO의 고비용 비평가(Critic) 모델을 제거하고 그룹 내 상대 비교로 정책을 갱신하는 차세대 RLHF 기법",
            "⚙️ 핵심 원리 및 특징: 단일 질의에 대해 N개 응답을 동시 샘플링한 후, 정답 일치도 및 포맷 규칙 보상의 평균·표준편차를 기준으로 어드밴티지(Advantage)를 계산",
            "🚀 실무 활용 포인트: Critic 모델 저장을 위한 GPU VRAM을 최대 50% 절감하며, 수학·코딩 등 검증 가능한 도메인에서 모델의 자가 추론(CoT) 체인을 효과적으로 유도"
        ],
        "keywords": ["#GRPO", "#DeepSeek", "#추론강화학습", "#RLHF", "#LLM엔지니어링"]
    },
    {
        "id": "vllm-serving",
        "title": "vLLM & PagedAttention - 메모리 단편화 제로 고속 서빙 엔진",
        "category_type": "tool",
        "source": "vLLM Project / UC Berkeley",
        "source_url": "https://vllm.ai",
        "link": "https://github.com/vllm-project/vllm",
        "summary": "OS의 가상 메모리 페이징 기법에서 착안한 PagedAttention 알고리즘을 도입하여, LLM 서빙 시 KV 캐시 메모리 낭비를 제로화하고 처리량을 최대 24배 끌어올린 오픈소스 서빙 엔진입니다.",
        "bullet_points": [
            "🛠️ 도구/기법 개요: 대규모 동시 요청 환경에서 GPU VRAM 낭비를 극적으로 줄여주는 업계 표준 고성능 LLM 추론 서빙 프레임워크",
            "⚙️ 핵심 원리 및 특징: 고정 크기 블록 단위로 KV 캐시를 비연속 물리 메모리에 동적 할당하여 외부 단편화를 해결하고 동적 연속 배치(Continuous Batching) 지원",
            "🚀 실무 활용 포인트: 사내 인하우스 모델 서빙 시 GPU 인프라 비용을 대폭 절감하며, Speculative Decoding 및 Chunked Prefill로 첫 토큰 응답 속도(TTFT) 개선"
        ],
        "keywords": ["#vLLM", "#PagedAttention", "#고속서빙", "#KVCache", "#GPU최적화"]
    },
    {
        "id": "graphrag-crag",
        "title": "GraphRAG & Corrective RAG - 지식 그래프 결합 자율 검색 증강",
        "category_type": "method",
        "source": "Microsoft Research / 학계",
        "source_url": "https://microsoft.github.io/graphrag",
        "link": "https://github.com/microsoft/graphrag",
        "summary": "단순 키워드나 밀집 벡터 유사도 검색의 한계를 극복하기 위해, 비정형 텍스트에서 엔티티와 관계 그래프를 추출하고 커뮤니티 요약을 결합하여 전체 맥락을 포괄하는 고급 RAG 아키텍처입니다.",
        "bullet_points": [
            "🛠️ 도구/기법 개요: 방대한 문서군에서 거시적 테마와 세부 엔티티 간 관계망을 동시에 파악할 수 있는 지식 그래프 기반 증강 생성 기법",
            "⚙️ 핵심 원리 및 특징: LLM으로 그래프 노드와 엣지를 생성한 뒤 계층적 커뮤니티 감지 알고리즘(Leiden)을 적용해 '데이터셋 전체를 관통하는 종합 질문'에 정확히 답변",
            "🚀 실무 활용 포인트: 법률 판례, 사내 정책, 금융 리서치 등 파편화된 다중 문서 간 복합 인과관계를 추론해야 하는 엔터프라이즈 지식 베이스 구축에 최적"
        ],
        "keywords": ["#GraphRAG", "#지식그래프", "#CorrectiveRAG", "#고급RAG", "#엔터프라이즈AI"]
    },
    {
        "id": "unsloth-lora",
        "title": "Unsloth & QLoRA - 2배 빠른 초경량 LLM 파인튜닝 프레임워크",
        "category_type": "tool",
        "source": "Unsloth AI",
        "source_url": "https://unsloth.ai",
        "link": "https://github.com/unslothai/unsloth",
        "summary": "수학적으로 정확하게 수동 유도된 커스텀 역전파(Backpropagation) GPU 커널을 적용하여, 허깅페이스 대비 파인튜닝 속도를 2배 가속하고 메모리 사용량을 최대 80% 줄인 경량화 도구입니다.",
        "bullet_points": [
            "🛠️ 도구/기법 개요: 단일 GPU 환경에서도 Llama, Qwen, Gemma 등 거대 언어모델을 초고속으로 파인튜닝할 수 있는 오픈소스 가속 툴킷",
            "⚙️ 핵심 원리 및 특징: PyTorch 오버헤드를 우회하는 순수 OpenAI Triton 기반 맞춤형 행렬곱/크로스 엔트로피 커널과 4비트 양자화 QLoRA/DoRA 완벽 통합",
            "🚀 실무 활용 포인트: 고가의 A100/H100 없이도 RTX 4090 및 무료 Colab GPU에서 최신 LLM을 수 시간 만에 도메인 특화 모델로 미세조정 가능"
        ],
        "keywords": ["#Unsloth", "#QLoRA", "#DoRA", "#파인튜닝", "#Triton"]
    },
    {
        "id": "langgraph-swarm",
        "title": "LangGraph & Swarm - 상태 그래프 기반 멀티 에이전트 제어",
        "category_type": "tool",
        "source": "LangChain / OpenAI",
        "source_url": "https://www.langchain.com/langgraph",
        "link": "https://github.com/langchain-ai/langgraph",
        "summary": "단방향 DAG 파이프라인의 한계를 넘어, 순환(Cycles), 분기, 휴먼인더루프(Human-in-the-loop), 분산 체크포인팅을 완벽하게 제어할 수 있는 상태 머신 기반 에이전트 프레임워크입니다.",
        "bullet_points": [
            "🛠️ 도구/기법 개요: 여러 전문 에이전트 간의 자율 위임, 피드백 루프 및 상태 동기화를 결정론적으로 제어하는 오케스트레이션 엔진",
            "⚙️ 핵심 원리 및 특징: 그래프 노드(에이전트/도구)와 엣지(조건부 분기)를 정의하고, 전역 상태(State)의 점진적 변경 사항을 불변 스냅샷으로 영속화",
            "🚀 실무 활용 포인트: 오류 발생 시 이전 체크포인트로 롤백하거나 사람이 중간에 개입하여 계획을 수정할 수 있어 프로덕션 에이전트의 안정성을 극대화"
        ],
        "keywords": ["#LangGraph", "#멀티에이전트", "#Swarm", "#에이전트오케스트레이션", "#상태그래프"]
    },
    {
        "id": "sglang-engine",
        "title": "SGLang & RadixAttention - KV 캐시 계층 트리 재사용 추론 엔진",
        "category_type": "tool",
        "source": "LMSYS Org / UC Berkeley",
        "source_url": "https://sgl-project.github.io",
        "link": "https://github.com/sgl-project/sglang",
        "summary": "프롬프트 템플릿, 퓨샷 예제, 시스템 프롬프트 등 공통 접두사(Prefix)를 기수 트리(Radix Tree)로 자동 캐싱하여 재계산 없이 즉각 응답하는 초고속 복합 추론 서빙 시스템입니다.",
        "bullet_points": [
            "🛠️ 도구/기법 개요: 에이전트 및 멀티턴 대화처럼 긴 접두사 공유가 빈번한 복합 워크플로우를 위해 설계된 최신 LLM 프로그래밍 프레임워크",
            "⚙️ 핵심 원리 및 특징: Radix Tree 기반 LRU 페이지 캐시로 세션 간 중복 토큰 계산을 0으로 만들고, 정규식 기반 정형(JSON) 디코딩을 FSM으로 가속",
            "🚀 실무 활용 포인트: 벤치마크 평가, 복합 RAG, 에이전트 워크플로우에서 vLLM 대비 2~5배의 처리량 향상과 응답 지연 시간 단축 실현"
        ],
        "keywords": ["#SGLang", "#RadixAttention", "#구조화출력", "#고속추론", "#LMSYS"]
    },
    {
        "id": "dspy-programming",
        "title": "DSPy - 프롬프트 엔지니어링 대신 선언적 프로그래밍과 자동 최적화",
        "category_type": "method",
        "source": "Stanford NLP",
        "source_url": "https://dspy.ai",
        "link": "https://github.com/stanfordnlp/dspy",
        "summary": "취약한 자연어 프롬프트 작성에서 벗어나, 파이썬 서명(Signatures)과 모듈(Modules)로 AI 파이프라인을 조립하고 컴파일러(Teleprompter)가 예시와 프롬프트를 자동 최적화하는 패러다임입니다.",
        "bullet_points": [
            "🛠️ 도구/기법 개요: 딥러닝에서 PyTorch가 신경망 가중치를 옵티마이저로 학습시키듯, LLM 파이프라인의 프롬프트와 데모를 알고리즘으로 최적화하는 프레임워크",
            "⚙️ 핵심 원리 및 특징: '입력 -> 출력' 인터페이스를 코드로 선언하고, 평가 지표(Metric)에 따라 MIPROv2, BootstrapFewShot 등의 컴파일러가 최적 파라미터를 탐색",
            "🚀 실무 활용 포인트: 모델이 업그레이드되거나 데이터 분포가 바뀌어도 프롬프트를 수동으로 다시 쓸 필요 없이 단 한 줄의 `compile()` 호출로 성능 복원"
        ],
        "keywords": ["#DSPy", "#Stanford", "#프롬프트최적화", "#선언적AI", "#자동화파이프라인"]
    },
    {
        "id": "speculative-decoding",
        "title": "Speculative Decoding (추측 디코딩) - 무손실 3배 추론 가속 기법",
        "category_type": "method",
        "source": "Google DeepMind / 학계",
        "source_url": "https://research.google",
        "link": "https://arxiv.org/abs/2211.17192",
        "summary": "소형 드래프트 모델(Draft Model)이 여러 토큰을 초고속으로 추측 생성하고, 주 타깃 모델이 단 한 번의 순방향 연산으로 이를 병렬 검증함으로써 정확도 손실 없이 디코딩 속도를 2~3배 단축합니다.",
        "bullet_points": [
            "🛠️ 도구/기법 개요: 자귀회귀(Autoregressive) 생성의 고유한 메모리 대역폭 병목을 극복하기 위해 제안된 무손실 가속 알고리즘",
            "⚙️ 핵심 원리 및 특징: 작은 모델이 생성한 토큰 후보를 타깃 모델의 확률 분포와 수정된 기각 샘플링(Rejection Sampling)으로 판정해 수학적 동등성을 보장",
            "🚀 실무 활용 포인트: Medusa(멀티 헤드 기반 자가 추측) 및 Eagle 등 단일 모델 변형 기법과 결합하여 vLLM, TensorRT-LLM의 프로덕션 지연 시간을 획기적으로 개선"
        ],
        "keywords": ["#SpeculativeDecoding", "#추측디코딩", "#추론가속", "#무손실최적화", "#DeepMind"]
    },
    {
        "id": "dpo-simpo",
        "title": "DPO & SimPO - 보상 모델 없는 다이렉트 선호도 정렬 기법",
        "category_type": "method",
        "source": "Stanford / Princeton",
        "source_url": "https://arxiv.org/abs/2305.18290",
        "link": "https://github.com/eric-mitchell/direct-preference-optimization",
        "summary": "강화학습 기반 RLHF의 복잡한 보상 모델 학습 및 PPO 샘플링 루프를 수학적으로 치환하여, 단순 교차 엔트로피 손실 함수만으로 인간 선호 데이터셋을 직접 학습하는 정렬 기법입니다.",
        "bullet_points": [
            "🛠️ 도구/기법 개요: RLHF 정렬 과정을 지도학습(SFT)처럼 간결하고 안정적으로 만들어 오픈소스 진영의 모델 정렬 표준으로 자리잡은 방법론",
            "⚙️ 핵심 원리 및 특징: 암묵적 보상 함수를 모델의 로그 확률 비로 표현하여 참조 모델(Reference Model)과의 KL 발산 제약 조건 하에서 선호 응답의 확률을 최대화",
            "🚀 실무 활용 포인트: 하이퍼파라미터 튜닝이 극도로 까다로운 PPO 대신 단일 손실함수로 학습 안정성을 보장하며, 최근 참조 모델조차 생략하는 SimPO로 진화"
        ],
        "keywords": ["#DPO", "#SimPO", "#RLHF", "#선호도학습", "#모델정렬"]
    },
    {
        "id": "ollama-local",
        "title": "Ollama & llama.cpp - 로컬 GGUF 양자화 모델 고성능 런타임",
        "category_type": "tool",
        "source": "Ollama / Georgi Gerganov",
        "source_url": "https://ollama.com",
        "link": "https://github.com/ollama/ollama",
        "summary": "순수 C/C++ 기반의 llama.cpp 엔진을 백엔드로 삼아, macOS의 Metal 및 일반 GPU 환경에서 외부 클라우드 통신 없이 오픈소스 LLM을 원클릭으로 패키징하고 로컬 서빙하는 도구입니다.",
        "bullet_points": [
            "🛠️ 도구/기법 개요: 로컬 PC 및 사내 프라이빗 서버에서 보안 우려 없이 파운데이션 모델을 즉시 구동할 수 있는 온디바이스 AI 도구",
            "⚙️ 핵심 원리 및 특징: Q4_K_M 등 정밀한 양자화(Quantization) 기법을 통해 70B 모델도 소비자용 하드웨어에서 구동 가능하며, 모드파일(Modelfile)로 시스템 프롬프트 관리",
            "🚀 실무 활용 포인트: 민감한 사내 코드 및 개인정보 분석 작업을 로컬에서 100% 안전하게 수행하며, 표준 REST API를 제공하여 다양한 웹 UI와 손쉽게 연동"
        ],
        "keywords": ["#Ollama", "#llamacpp", "#온디바이스AI", "#GGUF양자화", "#프라이빗AI"]
    },
    {
        "id": "tensorrt-llm",
        "title": "TensorRT-LLM & FP8 Quantization - 엔비디아 GPU 전용 추론 컴파일러",
        "category_type": "tool",
        "source": "NVIDIA",
        "source_url": "https://developer.nvidia.com/tensorrt-llm",
        "link": "https://github.com/NVIDIA/TensorRT-LLM",
        "summary": "엔비디아 텐서 코어(Tensor Cores) 하드웨어에 최적화된 최신 FP8 양자화, In-flight Batching, 커스텀 FlashAttention 커널을 결합하여 데이터센터급 최대 연산 처리량을 제공하는 추론 가속 라이브러리입니다.",
        "bullet_points": [
            "🛠️ 도구/기법 개요: 엔비디아 H100, L40S, B200 등 현대 GPU 하드웨어의 연산 잠재력을 100% 한계치까지 끌어올리는 엔터프라이즈 추론 엔진",
            "⚙️ 핵심 원리 및 특징: 딥러닝 그래프 퓨전(Graph Fusion), KV 캐시 FP8 압축, 다중 GPU 텐서 병렬화(TP) 및 파이프라인 병렬화(PP)를 하드웨어 수준에서 직결",
            "🚀 실무 활용 포인트: 대규모 실시간 서비스에서 동시 접속자가 폭증하는 피크 타임에 GPU 대당 처리량을 극대화하여 클라우드 인프라 운용 비용을 절감"
        ],
        "keywords": ["#TensorRT", "#NVIDIA", "#FP8양자화", "#하드웨어가속", "#엔터프라이즈AI"]
    }
]


def get_daily_tools_and_methods(date_str: str, history_filter=None, count: int = 6) -> List[Dict[str, Any]]:
    """
    일자별(date_str) 시드 기반 순환 및 이전 브리핑 이력 필터링을 결합하여,
    항상 6개의 중복 없는 최신 AI/ML 툴과 기법을 반환합니다.
    """
    try:
        # 날짜 기반 시드 오프셋 계산 (일별 결정론적 회전)
        date_hash = sum(ord(c) for c in date_str)
    except Exception:
        date_hash = 0

    total = len(TOOLS_AND_METHODS_CATALOG)
    # 시작 인덱스를 날짜에 맞추어 회전
    start_idx = (date_hash * 2) % total

    ordered_candidates = []
    for i in range(total):
        idx = (start_idx + i) % total
        ordered_candidates.append(TOOLS_AND_METHODS_CATALOG[idx])

    selected = []
    # 1차: 과거 브리핑에 등장하지 않은 신선한 항목 우선 선정
    for item in ordered_candidates:
        if history_filter and history_filter.is_duplicate(item):
            continue
        selected.append(item)
        if len(selected) >= count:
            break

    # 2차: 필터링 후 6개 미만인 경우, 후보군에서 보충
    if len(selected) < count:
        for item in ordered_candidates:
            if item not in selected:
                selected.append(item)
                if len(selected) >= count:
                    break

    return selected[:count]
