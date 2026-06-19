"""CAN SLIM 스타일 정량 스크리닝 — 순수 Pandas (LLM 미사용).

CAN SLIM 원형은 펀더멘털(분기/연간 EPS 등) 중심이나, 현재 가용 데이터는 OHLCV뿐이다.
따라서 가격/거래량으로 계산 가능한 항목만 정량 평가하고, 펀더멘털 항목(C/A/N/I)은
DART 연동(향후 Phase) 전까지 'pending'으로 정직하게 분리한다.

활성 평가 항목(가격/수급 기반 근사):
- trend_up   : 추세 상승 (close > ma60, ma20 > ma60)
- above_ma20 : 단기 추세 (close > ma20)
- near_high  : 신고가 근접 (close >= 기간 최고가 * threshold) — Leader/RS 근사
- vol_surge  : 거래량 급증 (당일 vol >= 평균 vol * factor) — Supply/Demand 근사
- momentum   : 최근 N일 모멘텀 (구간 수익률 > 0)
"""

from __future__ import annotations

import math

from core.models import StockIdentity
from features.strategy.schemas import CanSlimResult
from services.chart.indicators import compute_indicator_frame
from services.chart.models import DailyCandle

PENDING_FUNDAMENTALS = [
    "C(분기 EPS 성장)",
    "A(연간 EPS 성장)",
    "N(신제품/신고가 촉매)",
    "I(기관 수급)",
]


def _f(x) -> float | None:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    return float(x)


def screen_canslim(
    stock: StockIdentity,
    candles: list[DailyCandle],
    *,
    near_high_threshold: float = 0.85,
    vol_surge_factor: float = 1.5,
    momentum_window: int = 20,
    pass_score: int = 3,
    high_lookback: int = 120,
) -> CanSlimResult:
    df = compute_indicator_frame(candles)
    as_of = candles[-1].date if candles else None

    result = CanSlimResult(
        stock=stock,
        as_of=as_of or _epoch_date(),
        pending_fundamentals=list(PENDING_FUNDAMENTALS),
    )
    if df.empty:
        result.reasons.append("일봉 데이터 없음 — 평가 불가")
        return result

    latest = df.iloc[-1]
    close = _f(latest.get("close"))
    ma20 = _f(latest.get("ma20"))
    ma60 = _f(latest.get("ma60"))
    volume = _f(latest.get("volume"))

    checks: dict[str, bool] = {}
    metrics: dict[str, float] = {}

    # trend_up / above_ma20
    if close is not None and ma60 is not None and ma20 is not None:
        checks["trend_up"] = close > ma60 and ma20 > ma60
    if close is not None and ma20 is not None:
        checks["above_ma20"] = close > ma20

    # near_high (Leader / Relative Strength 근사)
    high_series = df["high"].astype("float64").tail(high_lookback)
    period_high = _f(high_series.max()) if not high_series.empty else None
    if close is not None and period_high:
        ratio = close / period_high
        metrics["high_ratio"] = round(ratio, 4)
        checks["near_high"] = ratio >= near_high_threshold

    # vol_surge (Supply/Demand 근사)
    vol_series = df["volume"].astype("float64").tail(momentum_window)
    avg_vol = _f(vol_series.mean()) if not vol_series.empty else None
    if volume is not None and avg_vol and avg_vol > 0:
        metrics["vol_ratio"] = round(volume / avg_vol, 4)
        checks["vol_surge"] = volume >= avg_vol * vol_surge_factor

    # momentum (구간 수익률)
    if len(df) > momentum_window:
        past_close = _f(df.iloc[-momentum_window - 1]["close"])
        if past_close and close is not None:
            ret = (close / past_close - 1) * 100
            metrics["momentum_pct"] = round(ret, 2)
            checks["momentum"] = ret > 0

    result.checks = checks
    result.metrics = metrics
    result.max_score = len(checks)
    result.score = sum(1 for v in checks.values() if v)
    result.passed = result.score >= pass_score
    result.reasons = _reasons(checks, metrics)
    return result


def _reasons(checks: dict[str, bool], metrics: dict[str, float]) -> list[str]:
    label = {
        "trend_up": "중기 추세 상승(종가>60일선, 20일선>60일선)",
        "above_ma20": "20일선 상회",
        "near_high": "신고가 근접",
        "vol_surge": "거래량 급증",
        "momentum": "구간 모멘텀 양호",
    }
    out: list[str] = []
    for key, ok in checks.items():
        mark = "충족" if ok else "미충족"
        out.append(f"{label.get(key, key)}: {mark}")
    return out


def _epoch_date():
    # candles가 비어 as_of를 못 구한 경우의 자리표시(테스트에서는 항상 candles 존재).
    from datetime import date

    return date(1970, 1, 1)
