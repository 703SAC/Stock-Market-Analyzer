"""Analysis report repository."""

import uuid
from datetime import date

from sqlalchemy.orm import Session

from core.models import AnalysisReport
from storage.models import ReportRow, dumps_json, loads_json


def save_report(db: Session, report: AnalysisReport) -> AnalysisReport:
    report_id = report.id or str(uuid.uuid4())
    row = ReportRow(
        id=report_id,
        stock_code=report.stock.code,
        base_date=report.base_date,
        report_type=report.report_type,
        payload_json=dumps_json(report.model_dump(mode="json")),
    )
    db.merge(row)
    db.commit()
    report.id = report_id
    return report


def get_report(db: Session, report_id: str) -> AnalysisReport | None:
    row = db.get(ReportRow, report_id)
    if row is None:
        return None
    data = loads_json(row.payload_json)
    return AnalysisReport.model_validate(data)
