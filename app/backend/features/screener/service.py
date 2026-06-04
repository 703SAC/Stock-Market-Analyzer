"""Screener feature orchestration."""

from __future__ import annotations

import csv
import io
from datetime import date

from sqlalchemy.orm import Session

from core.models import TradingDayStockEvent
from features.screener import normalizer
from features.screener.schemas import ScreenerEventsResponse, ScreenerQuery
from services.kis.adapter import get_kis_adapter
from services.kis.trading_calendar import get_trading_days
from storage.repositories import screener_cache as cache_repo


class ScreenerService:
    async def find_events(self, db: Session, query: ScreenerQuery) -> ScreenerEventsResponse:
        if query.end_date < query.start_date:
            query = query.model_copy(update={"end_date": query.start_date})

        trading_days = await get_trading_days(query.start_date, query.end_date)
        all_events: list[TradingDayStockEvent] = []
        cached_days: list[str] = []
        adapter = get_kis_adapter()

        for trade_date in trading_days:
            key = cache_repo.cache_key(trade_date.isoformat(), query.min_volume)
            cached = cache_repo.get_cached(db, key)
            if cached is not None:
                cached_days.append(trade_date.isoformat())
                all_events.extend(
                    TradingDayStockEvent.model_validate(e) for e in cached
                )
                continue

            day_events: list[TradingDayStockEvent] = []
            if adapter.is_available:
                vol_rows = await adapter.get_volume_rank(trade_date)
                day_events.extend(
                    normalizer.volume_events(trade_date, vol_rows, query.min_volume)
                )
                if query.include_upper_limit:
                    upper_rows = await adapter.get_upper_limit_stocks()
                    day_events.extend(
                        normalizer.upper_limit_events(trade_date, upper_rows)
                    )

            merged_day = normalizer.merge_events(day_events)
            cache_repo.set_cached(
                db,
                key,
                [e.model_dump(mode="json") for e in merged_day],
            )
            all_events.extend(merged_day)

        final = normalizer.merge_events(all_events)
        return ScreenerEventsResponse(
            events=final,
            total=len(final),
            cached_days=cached_days,
        )

    async def get_event_by_id(
        self, db: Session, event_id: str, query: ScreenerQuery
    ) -> TradingDayStockEvent | None:
        result = await self.find_events(db, query)
        for ev in result.events:
            if ev.id == event_id:
                return ev
        return None

    def events_to_csv(self, events: list[TradingDayStockEvent]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "trade_date",
                "stock_code",
                "stock_name",
                "event_types",
                "volume",
                "change_rate",
                "price",
                "source",
            ]
        )
        for ev in events:
            writer.writerow(
                [
                    ev.trade_date.isoformat(),
                    ev.stock.code,
                    ev.stock.name or "",
                    ",".join(ev.event_types),
                    ev.volume or "",
                    ev.change_rate or "",
                    ev.price or "",
                    ev.source,
                ]
            )
        return output.getvalue()


screener_service = ScreenerService()
