"""Normalize KIS rows to TradingDayStockEvent."""

from datetime import date

from core.models import StockIdentity, TradingDayStockEvent
from services.kis.models import KisRawStockRow


def volume_events(
    trade_date: date,
    rows: list[KisRawStockRow],
    min_volume: int,
) -> list[TradingDayStockEvent]:
    events: list[TradingDayStockEvent] = []
    for row in rows:
        vol = row.volume or 0
        if vol < min_volume:
            continue
        events.append(
            TradingDayStockEvent(
                trade_date=trade_date,
                stock=StockIdentity(code=row.code, name=row.name, market="KRX"),
                event_types=["HIGH_VOLUME"],
                price=row.price,
                change_rate=row.change_rate,
                volume=vol,
                source="kis:volume_rank",
            )
        )
    return events


def upper_limit_events(
    trade_date: date,
    rows: list[KisRawStockRow],
) -> list[TradingDayStockEvent]:
    return [
        TradingDayStockEvent(
            trade_date=trade_date,
            stock=StockIdentity(code=row.code, name=row.name, market="KRX"),
            event_types=["UPPER_LIMIT"],
            price=row.price,
            change_rate=row.change_rate,
            volume=row.volume,
            source="kis:capture_uplowprice",
        )
        for row in rows
    ]


def merge_events(events: list[TradingDayStockEvent]) -> list[TradingDayStockEvent]:
    merged: dict[tuple[date, str], TradingDayStockEvent] = {}
    for ev in events:
        key = (ev.trade_date, ev.stock.code)
        if key not in merged:
            merged[key] = ev.model_copy(deep=True)
            continue
        existing = merged[key]
        for et in ev.event_types:
            if et not in existing.event_types:
                existing.event_types.append(et)
        if ev.volume and (not existing.volume or ev.volume > existing.volume):
            existing.volume = ev.volume
        if ev.price is not None:
            existing.price = ev.price
        if ev.change_rate is not None:
            existing.change_rate = ev.change_rate
        existing.source = f"{existing.source}+{ev.source}"
    result = list(merged.values())
    for i, ev in enumerate(result):
        ev.id = f"{ev.trade_date.isoformat()}_{ev.stock.code}"
    return sorted(result, key=lambda e: (e.trade_date, e.stock.code), reverse=True)
