"""기술적 지표(순수 Pandas) 테스트 (Phase 2)."""

import math
from datetime import date, timedelta

from services.chart.indicators import add_indicators, candles_to_df, compute_indicator_frame, rsi
from services.chart.models import DailyCandle


def _candles(closes, start=date(2026, 1, 1), volume=1_000_000):
    return [
        DailyCandle(
            date=start + timedelta(days=i),
            open=c,
            high=c,
            low=c,
            close=float(c),
            volume=volume,
        )
        for i, c in enumerate(closes)
    ]


def test_empty_candles_yield_indicator_columns():
    df = compute_indicator_frame([])
    assert df.empty
    for col in ("ma5", "ma20", "ma60", "rsi14", "change_rate", "volume_change_rate"):
        assert col in df.columns


def test_moving_average_and_change_rate():
    df = compute_indicator_frame(_candles(list(range(1, 31))))  # 1..30
    last = df.iloc[-1]
    assert math.isclose(last["ma5"], 28.0)  # mean(26..30)
    assert not math.isnan(last["ma20"])  # 30 rows >= 20
    assert math.isclose(last["change_rate"], (30 / 29 - 1) * 100, rel_tol=1e-6)


def test_ma20_is_nan_before_window_fills():
    df = compute_indicator_frame(_candles(list(range(1, 11))))  # 10 rows < 20
    assert math.isnan(df.iloc[-1]["ma20"])
    assert not math.isnan(df.iloc[-1]["ma5"])  # 10 >= 5


def test_rsi_all_gains_is_100():
    df = compute_indicator_frame(_candles(list(range(1, 21))))  # strictly rising
    assert math.isclose(df.iloc[-1]["rsi14"], 100.0)


def test_candles_sorted_by_date():
    unsorted = list(reversed(_candles([10, 11, 12])))
    df = candles_to_df(unsorted)
    assert list(df["date"]) == sorted(df["date"])
