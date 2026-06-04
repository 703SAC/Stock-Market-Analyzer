"""KIS market data adapter wrapping open-trading-api."""

from __future__ import annotations

import asyncio
from datetime import date

import pandas as pd

from config import get_settings
from services.kis.auth_status import check_kis_status
from services.kis.kis_loader import get_domestic_stock_module
from services.kis.kis_session import ensure_kis_authenticated
from services.kis.models import KisRawStockRow
from services.kis.rate_limit import kis_throttle_async


def _safe_int(value) -> int | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return int(float(str(value).replace(",", "")))
    except (ValueError, TypeError):
        return None


def _safe_float(value) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return None


def _df_to_rows(df: pd.DataFrame) -> list[KisRawStockRow]:
    if df is None or df.empty:
        return []
    rows: list[KisRawStockRow] = []
    for _, row in df.iterrows():
        code = str(row.get("mksc_shrn_iscd", row.get("stck_shrn_iscd", ""))).strip()
        if not code:
            continue
        rows.append(
            KisRawStockRow(
                code=code.zfill(6),
                name=str(row.get("hts_kor_isnm", "")).strip() or None,
                price=_safe_int(row.get("stck_prpr")),
                change_rate=_safe_float(row.get("prdy_ctrt")),
                volume=_safe_int(row.get("acml_vol")),
            )
        )
    return rows


class KisMarketAdapter:
    def __init__(self):
        self._module = get_domestic_stock_module()
        self._status = check_kis_status()

    @property
    def is_available(self) -> bool:
        return self._module is not None and self._status.get("configured", False)

    def _prepare_kis_call(self) -> None:
        if not self.is_available:
            return
        ensure_kis_authenticated()

    async def smoke_test(self) -> dict:
        if not self.is_available:
            return {"status": "not_configured", "message": self._status.get("message", "")}
        from services.kis.kis_session import diagnose_kis_auth

        return await asyncio.to_thread(diagnose_kis_auth)

    async def get_volume_rank(self, trade_date: date | None = None) -> list[KisRawStockRow]:
        if not self.is_available:
            return []
        await kis_throttle_async()
        self._prepare_kis_call()

        def _call():
            return self._module.volume_rank(
                fid_cond_mrkt_div_code="J",
                fid_cond_scr_div_code="20171",
                fid_input_iscd="0000",
                fid_div_cls_code="0",
                fid_blng_cls_code="0",
                fid_trgt_cls_code="111111111",
                fid_trgt_exls_cls_code="0000000000",
                fid_input_price_1="",
                fid_input_price_2="",
                fid_vol_cnt="",
                fid_input_date_1=trade_date.strftime("%Y%m%d") if trade_date else "",
            )

        df = await asyncio.to_thread(_call)
        return _df_to_rows(df if isinstance(df, pd.DataFrame) else pd.DataFrame())

    async def get_upper_limit_stocks(self) -> list[KisRawStockRow]:
        if not self.is_available:
            return []
        await kis_throttle_async()
        self._prepare_kis_call()

        def _call():
            return self._module.capture_uplowprice(
                fid_cond_mrkt_div_code="J",
                fid_cond_scr_div_code="11300",
                fid_prc_cls_code="0",
                fid_div_cls_code="0",
                fid_input_iscd="0000",
            )

        df = await asyncio.to_thread(_call)
        return _df_to_rows(df if isinstance(df, pd.DataFrame) else pd.DataFrame())

    async def get_holiday_calendar(self, bass_dt: str) -> pd.DataFrame:
        if not self.is_available:
            return pd.DataFrame()
        # 모의(vps)에는 국내휴장일조회(CTCA0903R) 미제공 → OPSQ0002
        svr = (get_settings().kis_svr or "prod").lower().strip()
        if svr == "vps":
            return pd.DataFrame()
        await kis_throttle_async()
        self._prepare_kis_call()
        df = await asyncio.to_thread(self._module.chk_holiday, bass_dt=bass_dt)
        return df if isinstance(df, pd.DataFrame) else pd.DataFrame()


_adapter: KisMarketAdapter | None = None


def get_kis_adapter() -> KisMarketAdapter:
    global _adapter
    if _adapter is None:
        _adapter = KisMarketAdapter()
    return _adapter
