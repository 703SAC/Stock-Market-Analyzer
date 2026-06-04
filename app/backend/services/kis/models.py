"""KIS adapter internal models."""

from pydantic import BaseModel


class KisRawStockRow(BaseModel):
    code: str
    name: str | None = None
    price: int | None = None
    change_rate: float | None = None
    volume: int | None = None
