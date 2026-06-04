"""Screener normalizer merge tests."""

from datetime import date

from core.models import StockIdentity, TradingDayStockEvent
from features.screener import normalizer
from services.kis.models import KisRawStockRow


def test_volume_filter_min_volume():
    rows = [
        KisRawStockRow(code="005930", name="삼성전자", volume=5_000_000),
        KisRawStockRow(code="000660", name="SK하이닉스", volume=12_000_000),
    ]
    events = normalizer.volume_events(date(2025, 5, 30), rows, min_volume=10_000_000)
    assert len(events) == 1
    assert events[0].stock.code == "000660"
    assert events[0].event_types == ["HIGH_VOLUME"]


def test_merge_events_combines_tags():
    d = date(2025, 5, 30)
    events = [
        TradingDayStockEvent(
            trade_date=d,
            stock=StockIdentity(code="005930", name="삼성전자"),
            event_types=["HIGH_VOLUME"],
            volume=15_000_000,
            source="kis:volume_rank",
        ),
        TradingDayStockEvent(
            trade_date=d,
            stock=StockIdentity(code="005930", name="삼성전자"),
            event_types=["UPPER_LIMIT"],
            volume=15_000_000,
            source="kis:capture_uplowprice",
        ),
    ]
    merged = normalizer.merge_events(events)
    assert len(merged) == 1
    assert set(merged[0].event_types) == {"HIGH_VOLUME", "UPPER_LIMIT"}
