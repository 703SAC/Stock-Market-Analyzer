"""Trading day calendar using KIS chk_holiday when available."""

from __future__ import annotations

import logging
from datetime import date, timedelta

import pandas as pd

from config import get_settings
from services.kis.adapter import get_kis_adapter

logger = logging.getLogger(__name__)


def _weekdays_between(start: date, end: date) -> list[date]:
    days: list[date] = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


def _parse_bass_dt(value) -> date | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip()[:8]
    if len(s) != 8 or not s.isdigit():
        return None
    return date(int(s[:4]), int(s[4:6]), int(s[6:8]))


async def get_trading_days(start: date, end: date) -> list[date]:
    """Return trading days in range. Uses KIS calendar when configured."""
    svr = (get_settings().kis_svr or "prod").lower().strip()
    if svr == "vps":
        logger.debug("vps: chk_holiday unavailable; using weekday calendar")
        return _weekdays_between(start, end)

    adapter = get_kis_adapter()
    if not adapter.is_available:
        return _weekdays_between(start, end)

    trading: set[date] = set()
    months_seen: set[tuple[int, int]] = set()
    current = start.replace(day=1)
    while current <= end:
        key = (current.year, current.month)
        if key not in months_seen:
            months_seen.add(key)
            if current.month == 12:
                month_end = date(current.year, 12, 31)
            else:
                month_end = date(current.year, current.month + 1, 1) - timedelta(days=1)
            query_dt = min(month_end, end)
            try:
                df = await adapter.get_holiday_calendar(query_dt.strftime("%Y%m%d"))
            except Exception as exc:
                logger.warning("KIS holiday calendar failed, using weekdays: %s", exc)
                return _weekdays_between(start, end)
            if not df.empty and "tr_day_yn" in df.columns:
                for _, row in df.iterrows():
                    d = _parse_bass_dt(row.get("bass_dt"))
                    if d and start <= d <= end and str(row.get("tr_day_yn", "")).upper() == "Y":
                        trading.add(d)
            else:
                trading.update(_weekdays_between(start, end))
                break
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)

    if not trading:
        return _weekdays_between(start, end)
    return sorted(trading)
