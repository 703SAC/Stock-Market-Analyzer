"""기술적 지표 — 전부 순수 Pandas 수식 (환각 제로 원칙: LLM 미사용).

입력은 DailyCandle 리스트, 출력은 지표 컬럼이 채워진 DataFrame.
컬럼명은 condition_schema.ALLOWED_INDICATORS와 일치시켜 evaluator가 참조한다.
"""

from __future__ import annotations

import pandas as pd

from services.chart.models import DailyCandle


def candles_to_df(candles: list[DailyCandle]) -> pd.DataFrame:
    """일봉 리스트를 날짜 오름차순 DataFrame으로 변환."""
    if not candles:
        return pd.DataFrame(
            columns=["date", "open", "high", "low", "close", "volume"]
        )
    df = pd.DataFrame([c.model_dump() for c in candles])
    df = df.sort_values("date").reset_index(drop=True)
    return df


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """RSI (단순이동평균 기반, Cutler's RSI). 결정적이며 룩어헤드 없음."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    out = 100 - (100 / (1 + rs))
    # 손실이 0이면 RS=inf → RSI=100; 변동이 전혀 없으면 NaN 유지
    out = out.where(avg_loss != 0, 100.0)
    return out


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """이동평균/RSI/등락률/거래량 변화율 컬럼을 추가한다(원본 비파괴)."""
    if df.empty:
        for col in (
            "ma5",
            "ma20",
            "ma60",
            "rsi14",
            "change_rate",
            "volume_change_rate",
        ):
            df[col] = pd.Series(dtype="float64")
        return df

    out = df.copy()
    close = out["close"].astype("float64")
    out["ma5"] = close.rolling(window=5, min_periods=5).mean()
    out["ma20"] = close.rolling(window=20, min_periods=20).mean()
    out["ma60"] = close.rolling(window=60, min_periods=60).mean()
    out["rsi14"] = rsi(close, period=14)
    out["change_rate"] = close.pct_change() * 100.0
    if "volume" in out.columns:
        vol = out["volume"].astype("float64")
        out["volume_change_rate"] = vol.pct_change() * 100.0
    else:
        out["volume_change_rate"] = pd.Series(dtype="float64")
    return out


def compute_indicator_frame(candles: list[DailyCandle]) -> pd.DataFrame:
    """일봉 → 지표 포함 DataFrame (evaluator/CAN SLIM 공용 입력)."""
    return add_indicators(candles_to_df(candles))
