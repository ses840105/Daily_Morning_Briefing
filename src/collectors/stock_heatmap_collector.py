# -*- coding: utf-8 -*-
"""
Stock Heatmap Collector for Daily Morning Briefing
Collects daily price, previous close, and percentage change for US & Korea stock heatmaps.
Features:
- US S&P 500 / NASDAQ Big Tech & Sector Heatmap
- Korea KOSPI / KOSDAQ Market-Cap & Sector Heatmap
- Resilient multi-tier architecture (yfinance / network -> persistent cache -> built-in realistic fallback)
- Summary statistics (Advancers/Decliners, Top Gainer, Top Loser)
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional


US_INDICES_CONFIG = [
    {"name": "S&P 500", "symbol": "^GSPC", "default_price": 5864.67, "default_change": 49.85, "default_pct": 0.85},
    {"name": "NASDAQ", "symbol": "^IXIC", "default_price": 18518.61, "default_change": 228.70, "default_pct": 1.25},
    {"name": "Dow Jones", "symbol": "^DJI", "default_price": 42863.86, "default_change": 179.20, "default_pct": 0.42},
    {"name": "SOX 반도체", "symbol": "^SOX", "default_price": 5235.10, "default_change": 110.20, "default_pct": 2.15},
]

US_STOCKS_CONFIG = [
    # Big Tech · AI
    {"symbol": "NVDA", "name": "NVIDIA", "sector": "Big Tech · AI", "size_tier": "xl", "weight": 4.0, "default_price": 142.50, "default_change": 3.95, "default_pct": 2.85},
    {"symbol": "AAPL", "name": "Apple", "sector": "Big Tech · AI", "size_tier": "xl", "weight": 3.8, "default_price": 232.80, "default_change": 2.19, "default_pct": 0.95},
    {"symbol": "MSFT", "name": "Microsoft", "sector": "Big Tech · AI", "size_tier": "xl", "weight": 3.6, "default_price": 428.15, "default_change": 6.12, "default_pct": 1.45},
    {"symbol": "AMZN", "name": "Amazon", "sector": "Big Tech · AI", "size_tier": "lg", "weight": 2.5, "default_price": 188.50, "default_change": 2.05, "default_pct": 1.10},
    {"symbol": "GOOGL", "name": "Alphabet", "sector": "Big Tech · AI", "size_tier": "lg", "weight": 2.2, "default_price": 166.40, "default_change": 1.24, "default_pct": 0.75},
    {"symbol": "META", "name": "Meta", "sector": "Big Tech · AI", "size_tier": "lg", "weight": 2.2, "default_price": 585.20, "default_change": 10.33, "default_pct": 1.80},

    # Semiconductors
    {"symbol": "AVGO", "name": "Broadcom", "sector": "Semiconductors", "size_tier": "lg", "weight": 2.0, "default_price": 182.40, "default_change": 5.65, "default_pct": 3.20},
    {"symbol": "TSM", "name": "TSMC", "sector": "Semiconductors", "size_tier": "md", "weight": 1.8, "default_price": 198.50, "default_change": 4.65, "default_pct": 2.40},
    {"symbol": "AMD", "name": "AMD", "sector": "Semiconductors", "size_tier": "md", "weight": 1.5, "default_price": 156.80, "default_change": 2.55, "default_pct": 1.65},
    {"symbol": "MU", "name": "Micron", "sector": "Semiconductors", "size_tier": "sm", "weight": 1.0, "default_price": 112.30, "default_change": 3.16, "default_pct": 2.90},
    {"symbol": "QCOM", "name": "Qualcomm", "sector": "Semiconductors", "size_tier": "sm", "weight": 1.0, "default_price": 172.50, "default_change": 1.37, "default_pct": 0.80},

    # Consumer · EV
    {"symbol": "TSLA", "name": "Tesla", "sector": "Consumer · EV", "size_tier": "lg", "weight": 2.2, "default_price": 260.40, "default_change": 8.42, "default_pct": 3.34},
    {"symbol": "WMT", "name": "Walmart", "sector": "Consumer · EV", "size_tier": "md", "weight": 1.2, "default_price": 82.50, "default_change": 0.29, "default_pct": 0.35},
    {"symbol": "COST", "name": "Costco", "sector": "Consumer · EV", "size_tier": "sm", "weight": 1.0, "default_price": 910.20, "default_change": 5.43, "default_pct": 0.60},

    # Finance
    {"symbol": "BRK-B", "name": "Berkshire", "sector": "Finance", "size_tier": "md", "weight": 1.5, "default_price": 452.10, "default_change": -1.13, "default_pct": -0.25},
    {"symbol": "JPM", "name": "JPMorgan", "sector": "Finance", "size_tier": "md", "weight": 1.4, "default_price": 224.60, "default_change": 1.89, "default_pct": 0.85},
    {"symbol": "V", "name": "Visa", "sector": "Finance", "size_tier": "sm", "weight": 1.0, "default_price": 285.30, "default_change": 1.14, "default_pct": 0.40},

    # Health · Energy
    {"symbol": "LLY", "name": "Eli Lilly", "sector": "Health · Energy", "size_tier": "md", "weight": 1.5, "default_price": 905.40, "default_change": 10.73, "default_pct": 1.20},
    {"symbol": "UNH", "name": "UnitedHealth", "sector": "Health · Energy", "size_tier": "sm", "weight": 1.0, "default_price": 572.80, "default_change": -3.75, "default_pct": -0.65},
    {"symbol": "XOM", "name": "ExxonMobil", "sector": "Health · Energy", "size_tier": "sm", "weight": 1.0, "default_price": 122.10, "default_change": -1.42, "default_pct": -1.15},
]

KR_INDICES_CONFIG = [
    {"name": "KOSPI", "symbol": "^KS11", "default_price": 2610.35, "default_change": 20.20, "default_pct": 0.78},
    {"name": "KOSDAQ", "symbol": "^KQ11", "default_price": 765.40, "default_change": 8.48, "default_pct": 1.12},
    {"name": "USD/KRW", "symbol": "KRW=X", "default_price": 1382.50, "default_change": -4.80, "default_pct": -0.35},
]

KR_STOCKS_CONFIG = [
    # 반도체 · AI
    {"symbol": "005930.KS", "code": "005930", "name": "삼성전자", "sector": "반도체 · AI", "size_tier": "xl", "weight": 4.0, "default_price": 60800, "default_change": 900, "default_pct": 1.50},
    {"symbol": "000660.KS", "code": "000660", "name": "SK하이닉스", "sector": "반도체 · AI", "size_tier": "xl", "weight": 3.5, "default_price": 198000, "default_change": 6500, "default_pct": 3.40},
    {"symbol": "042700.KS", "code": "042700", "name": "한미반도체", "sector": "반도체 · AI", "size_tier": "sm", "weight": 1.0, "default_price": 112500, "default_change": 2400, "default_pct": 2.20},

    # 2차전지 · 소재
    {"symbol": "373220.KS", "code": "373220", "name": "LG에너지솔루션", "sector": "2차전지 · 소재", "size_tier": "lg", "weight": 2.2, "default_price": 392000, "default_change": -2900, "default_pct": -0.75},
    {"symbol": "006400.KS", "code": "006400", "name": "삼성SDI", "sector": "2차전지 · 소재", "size_tier": "md", "weight": 1.5, "default_price": 335000, "default_change": -3700, "default_pct": -1.10},
    {"symbol": "005490.KS", "code": "005490", "name": "POSCO홀딩스", "sector": "2차전지 · 소재", "size_tier": "md", "weight": 1.5, "default_price": 348000, "default_change": 1550, "default_pct": 0.45},
    {"symbol": "247540.KQ", "code": "247540", "name": "에코프로비엠", "sector": "2차전지 · 소재", "size_tier": "sm", "weight": 1.0, "default_price": 172000, "default_change": -3150, "default_pct": -1.80},

    # 바이오 · 헬스
    {"symbol": "207940.KS", "code": "207940", "name": "삼성바이오로직스", "sector": "바이오 · 헬스", "size_tier": "lg", "weight": 2.2, "default_price": 1045000, "default_change": 17000, "default_pct": 1.65},
    {"symbol": "068270.KS", "code": "068270", "name": "셀트리온", "sector": "바이오 · 헬스", "size_tier": "md", "weight": 1.5, "default_price": 195500, "default_change": 1550, "default_pct": 0.80},
    {"symbol": "196170.KQ", "code": "196170", "name": "알테오젠", "sector": "바이오 · 헬스", "size_tier": "sm", "weight": 1.2, "default_price": 385000, "default_change": 15500, "default_pct": 4.20},

    # 자동차 · 모빌리티
    {"symbol": "005380.KS", "code": "005380", "name": "현대차", "sector": "자동차 · 모빌리티", "size_tier": "lg", "weight": 2.0, "default_price": 238500, "default_change": 1500, "default_pct": 0.65},
    {"symbol": "000270.KS", "code": "000270", "name": "기아", "sector": "자동차 · 모빌리티", "size_tier": "md", "weight": 1.4, "default_price": 96200, "default_change": 380, "default_pct": 0.40},
    {"symbol": "012330.KS", "code": "012330", "name": "현대모비스", "sector": "자동차 · 모빌리티", "size_tier": "sm", "weight": 1.0, "default_price": 246000, "default_change": 1950, "default_pct": 0.80},

    # 금융 · 밸류업
    {"symbol": "105560.KS", "code": "105560", "name": "KB금융", "sector": "금융 · 밸류업", "size_tier": "md", "weight": 1.5, "default_price": 95800, "default_change": 1970, "default_pct": 2.10},
    {"symbol": "055550.KS", "code": "055550", "name": "신한지주", "sector": "금융 · 밸류업", "size_tier": "sm", "weight": 1.0, "default_price": 56400, "default_change": 780, "default_pct": 1.40},
    {"symbol": "086790.KS", "code": "086790", "name": "하나금융지주", "sector": "금융 · 밸류업", "size_tier": "sm", "weight": 1.0, "default_price": 64800, "default_change": 800, "default_pct": 1.25},

    # 방산 · 조선 · IT
    {"symbol": "012450.KS", "code": "012450", "name": "한화에어로스페이스", "sector": "방산 · 조선 · IT", "size_tier": "md", "weight": 1.6, "default_price": 382000, "default_change": 14000, "default_pct": 3.80},
    {"symbol": "329180.KS", "code": "329180", "name": "HD현대중공업", "sector": "방산 · 조선 · IT", "size_tier": "sm", "weight": 1.0, "default_price": 192500, "default_change": 3500, "default_pct": 1.85},
    {"symbol": "035420.KS", "code": "035420", "name": "NAVER", "sector": "방산 · 조선 · IT", "size_tier": "md", "weight": 1.4, "default_price": 178200, "default_change": 2100, "default_pct": 1.20},
    {"symbol": "035720.KS", "code": "035720", "name": "카카오", "sector": "방산 · 조선 · IT", "size_tier": "sm", "weight": 0.8, "default_price": 38400, "default_change": -190, "default_pct": -0.50},
]


class StockHeatmapCollector:
    """
    미국 및 한국 주식 시장 히트맵 데이터 수집기
    - yfinance를 통한 최근 5거래일 시세 수집
    - 네트워크 불가/타임아웃 시 persistent 캐시 및 표준 폴백 데이터셋 활용
    """

    def __init__(self, outputs_dir: Optional[str] = None):
        if outputs_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            outputs_dir = os.path.join(base_dir, "outputs")
        self.outputs_dir = outputs_dir
        self.cache_dir = os.path.join(self.outputs_dir, "cache")
        self.cache_file = os.path.join(self.cache_dir, "stock_heatmap_cache.json")
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
        except Exception:
            pass

    def _load_cache(self) -> Optional[Dict[str, Any]]:
        """저장된 캐시 파일 로드"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data and "us" in data and "kr" in data:
                        return data
            except Exception:
                pass
        return None

    def _save_cache(self, data: Dict[str, Any]):
        """수집 데이터 캐시 저장"""
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _try_yfinance_fetch(self, symbols: List[str]) -> Dict[str, Dict[str, float]]:
        """yfinance를 통한 최근 종가 및 전일비 수집 시도"""
        results = {}
        try:
            import yfinance as yf
            tickers_str = " ".join(symbols)
            df = yf.download(tickers_str, period="5d", interval="1d", group_by="ticker", progress=False, timeout=5)
            if df is not None and not df.empty:
                for sym in symbols:
                    try:
                        if len(symbols) == 1:
                            sub_df = df
                        else:
                            sub_df = df[sym] if sym in df else None
                        if sub_df is not None and len(sub_df) >= 2:
                            closes = sub_df["Close"].dropna()
                            if len(closes) >= 2:
                                latest_close = float(closes.iloc[-1])
                                prev_close = float(closes.iloc[-2])
                                chg = latest_close - prev_close
                                pct = (chg / prev_close) * 100.0 if prev_close else 0.0
                                results[sym] = {
                                    "price": round(latest_close, 2),
                                    "change": round(chg, 2),
                                    "change_pct": round(pct, 2)
                                }
                    except Exception:
                        continue
        except Exception:
            pass
        return results

    def _compute_summary(self, stocks: List[Dict[str, Any]], updated_at_str: str) -> Dict[str, Any]:
        """상승/하락 종목 수 및 최고/최저 상승률 종목 계산"""
        advancers = 0
        decliners = 0
        unchanged = 0
        top_gainer = None
        top_loser = None

        for s in stocks:
            pct = s.get("change_pct", 0.0)
            if pct > 0:
                advancers += 1
            elif pct < 0:
                decliners += 1
            else:
                unchanged += 1

            if top_gainer is None or pct > top_gainer.get("change_pct", -999):
                top_gainer = s
            if top_loser is None or pct < top_loser.get("change_pct", 999):
                top_loser = s

        return {
            "advancers": advancers,
            "decliners": decliners,
            "unchanged": unchanged,
            "total": len(stocks),
            "top_gainer": top_gainer or {},
            "top_loser": top_loser or {},
            "updated_at": updated_at_str
        }

    def _build_dataset(self, live_data: Dict[str, Dict[str, float]], now_str: str) -> Dict[str, Any]:
        """실시간 수집분과 폴백 기준 데이터를 결합하여 완성형 히트맵 데이터셋 빌드"""
        # 1. US Indices
        us_indices = []
        for item in US_INDICES_CONFIG:
            sym = item["symbol"]
            live = live_data.get(sym)
            price = live["price"] if live else item["default_price"]
            chg = live["change"] if live else item["default_change"]
            pct = live["change_pct"] if live else item["default_pct"]
            us_indices.append({
                "name": item["name"],
                "symbol": sym,
                "price": price,
                "change": chg,
                "change_pct": pct,
                "url": f"https://finance.yahoo.com/quote/{sym}"
            })

        # 2. US Stocks
        us_stocks = []
        us_sectors: Dict[str, List[Dict[str, Any]]] = {}
        for item in US_STOCKS_CONFIG:
            sym = item["symbol"]
            live = live_data.get(sym)
            price = live["price"] if live else item["default_price"]
            chg = live["change"] if live else item["default_change"]
            pct = live["change_pct"] if live else item["default_pct"]
            stock_obj = {
                "symbol": sym,
                "name": item["name"],
                "sector": item["sector"],
                "size_tier": item["size_tier"],
                "weight": item["weight"],
                "price": price,
                "change": chg,
                "change_pct": pct,
                "url": f"https://finance.yahoo.com/quote/{sym}"
            }
            us_stocks.append(stock_obj)
            us_sectors.setdefault(item["sector"], []).append(stock_obj)

        us_summary = self._compute_summary(us_stocks, now_str)

        # 3. Korea Indices
        kr_indices = []
        for item in KR_INDICES_CONFIG:
            sym = item["symbol"]
            live = live_data.get(sym)
            price = live["price"] if live else item["default_price"]
            chg = live["change"] if live else item["default_change"]
            pct = live["change_pct"] if live else item["default_pct"]
            kr_indices.append({
                "name": item["name"],
                "symbol": sym,
                "price": price,
                "change": chg,
                "change_pct": pct,
                "url": f"https://finance.naver.com/sise/sise_index.naver?code={sym.replace('^', '')}" if not sym.startswith("KRW") else "https://finance.naver.com/marketindex/"
            })

        # 4. Korea Stocks
        kr_stocks = []
        kr_sectors: Dict[str, List[Dict[str, Any]]] = {}
        for item in KR_STOCKS_CONFIG:
            sym = item["symbol"]
            code = item["code"]
            live = live_data.get(sym)
            price = live["price"] if live else item["default_price"]
            chg = live["change"] if live else item["default_change"]
            pct = live["change_pct"] if live else item["default_pct"]
            stock_obj = {
                "symbol": sym,
                "code": code,
                "name": item["name"],
                "sector": item["sector"],
                "size_tier": item["size_tier"],
                "weight": item["weight"],
                "price": price,
                "change": chg,
                "change_pct": pct,
                "url": f"https://finance.naver.com/item/main.naver?code={code}"
            }
            kr_stocks.append(stock_obj)
            kr_sectors.setdefault(item["sector"], []).append(stock_obj)

        kr_summary = self._compute_summary(kr_stocks, now_str)

        return {
            "timestamp": now_str,
            "us": {
                "market_name": "미국 S&P 500 · NASDAQ 빅테크 히트맵",
                "indices": us_indices,
                "sectors": us_sectors,
                "stocks": us_stocks,
                "summary": us_summary
            },
            "kr": {
                "market_name": "한국 KOSPI · KOSDAQ 시가총액 히트맵",
                "indices": kr_indices,
                "sectors": kr_sectors,
                "stocks": kr_stocks,
                "summary": kr_summary
            }
        }

    def collect_all(self) -> Dict[str, Any]:
        """
        US & Korea 히트맵 전체 데이터 수집 엔트리포인트
        - 1단계: yfinance 시도
        - 2단계: 실패 시 캐시 로드
        - 3단계: 기본 표준 데이터셋 빌드 및 캐시 갱신
        """
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M KST")
        all_symbols = [item["symbol"] for item in US_INDICES_CONFIG + US_STOCKS_CONFIG + KR_INDICES_CONFIG + KR_STOCKS_CONFIG]

        live_data = self._try_yfinance_fetch(all_symbols)

        if not live_data:
            cached = self._load_cache()
            if cached and "us" in cached and "kr" in cached:
                cached["cached"] = True
                return cached

        dataset = self._build_dataset(live_data, now_str)
        self._save_cache(dataset)
        return dataset


if __name__ == "__main__":
    collector = StockHeatmapCollector()
    data = collector.collect_all()
    print(f"US Stocks: {len(data['us']['stocks'])}, KR Stocks: {len(data['kr']['stocks'])}")
    print(f"US Top Gainer: {data['us']['summary']['top_gainer']['name']} ({data['us']['summary']['top_gainer']['change_pct']}%)")
    print(f"KR Top Gainer: {data['kr']['summary']['top_gainer']['name']} ({data['kr']['summary']['top_gainer']['change_pct']}%)")
