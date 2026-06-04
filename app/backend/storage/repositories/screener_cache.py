"""Screener event cache repository."""

from sqlalchemy.orm import Session

from storage.models import ScreenerCacheRow, dumps_json, loads_json


def cache_key(trade_date: str, min_volume: int) -> str:
    return f"screener:{trade_date}:{min_volume}"


def get_cached(db: Session, key: str) -> list[dict] | None:
    row = db.get(ScreenerCacheRow, key)
    if row is None:
        return None
    return loads_json(row.payload_json)


def set_cached(db: Session, key: str, events: list[dict]) -> None:
    row = db.get(ScreenerCacheRow, key)
    payload = dumps_json(events)
    if row:
        row.payload_json = payload
    else:
        db.add(ScreenerCacheRow(cache_key=key, payload_json=payload))
    db.commit()
