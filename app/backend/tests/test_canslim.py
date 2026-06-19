"""CAN SLIM 정량 스크리닝 테스트 (Phase 2)."""

from datetime import date, timedelta

from core.models import StockIdentity
from features.strategy.canslim import screen_canslim
from services.chart.models import DailyCandle


def _uptrend(n=70, base_vol=1_000_000, last_vol=5_000_000):
    candles = []
    for i in range(n):
        c = float(i + 1)
        vol = last_vol if i == n - 1 else base_vol
        candles.append(
            DailyCandle(
                date=date(2026, 1, 1) + timedelta(days=i),
                open=c, high=c, low=c, close=c, volume=vol,
            )
        )
    return candles


def test_strong_uptrend_passes_all_active_checks():
    res = screen_canslim(StockIdentity(code="005930", name="삼성전자"), _uptrend())
    assert res.passed is True
    assert res.score == res.max_score == 5
    assert res.checks["vol_surge"] is True
    assert res.checks["trend_up"] is True
    # 펀더멘털 항목은 데이터 부재로 정직하게 미평가 분리
    assert len(res.pending_fundamentals) == 4
    assert res.metrics["vol_ratio"] > 1.5


def test_empty_candles_not_passed():
    res = screen_canslim(StockIdentity(code="000000"), [])
    assert res.passed is False
    assert res.score == 0
    assert "데이터 없음" in " ".join(res.reasons)


def test_flat_series_fails_momentum_and_surge():
    flat = [
        DailyCandle(date=date(2026, 1, 1) + timedelta(days=i), open=10, high=10, low=10, close=10.0, volume=1_000_000)
        for i in range(70)
    ]
    res = screen_canslim(StockIdentity(code="111111"), flat)
    assert res.checks.get("momentum") is False
    assert res.checks.get("vol_surge") is False
