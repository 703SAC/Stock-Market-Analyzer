"""News article cache repository."""

from sqlalchemy.orm import Session

from storage.models import NewsCacheRow, dumps_json, loads_json


def cache_key(stock_code: str, base_date: str) -> str:
    return f"news:{stock_code}:{base_date}"


def get_cached(db: Session, key: str) -> list[dict] | None:
    row = db.get(NewsCacheRow, key)
    if row is None:
        return None
    return loads_json(row.payload_json)


def set_cached(db: Session, key: str, articles: list[dict]) -> None:
    row = db.get(NewsCacheRow, key)
    payload = dumps_json(articles)
    if row:
        row.payload_json = payload
    else:
        db.add(NewsCacheRow(cache_key=key, payload_json=payload))
    db.commit()
