"""DART filing models stub."""

from pydantic import BaseModel


class DartFilingStub(BaseModel):
    rcept_no: str
    report_nm: str
    stock_code: str
