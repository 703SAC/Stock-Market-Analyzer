"""조건식 DSL 평가 엔진.

보안 원칙: 사용자/LLM가 만든 조건식은 절대 eval하지 않는다. 허용된 지표·연산자만,
검증을 통과한 JSON DSL을 결정적으로 평가한다(open-trading-api 가이드 §3.2 / DSL 규칙).
"""

from __future__ import annotations

import math
import operator
from datetime import date

import pandas as pd

from services.chart.condition_schema import (
    ALLOWED_INDICATORS,
    ALLOWED_OPS,
    ConditionClause,
    ConditionDsl,
)

_OPS = {
    ">": operator.gt,
    "<": operator.lt,
    ">=": operator.ge,
    "<=": operator.le,
    "==": operator.eq,
}


def validate_dsl(dsl: ConditionDsl) -> None:
    """허용 지표/연산자 및 피연산자 존재 검증. 위반 시 ValueError."""
    if not dsl.all:
        raise ValueError("Condition DSL must contain at least one clause")
    for c in dsl.all:
        if c.indicator not in ALLOWED_INDICATORS:
            raise ValueError(f"Disallowed indicator: {c.indicator}")
        if c.op not in ALLOWED_OPS:
            raise ValueError(f"Disallowed operator: {c.op}")
        if c.indicator_right is not None and c.indicator_right not in ALLOWED_INDICATORS:
            raise ValueError(f"Disallowed indicator_right: {c.indicator_right}")
        if c.value is None and c.indicator_right is None:
            raise ValueError(
                f"Clause for {c.indicator} needs a value or indicator_right"
            )


def _is_missing(x) -> bool:
    return x is None or (isinstance(x, float) and math.isnan(x))


def _clause_holds(clause: ConditionClause, row: dict) -> bool | None:
    """단일 절 평가. 필요한 값이 없으면(NaN/None) None(평가 불가) 반환."""
    left = row.get(clause.indicator)
    right = row.get(clause.indicator_right) if clause.indicator_right else clause.value
    if _is_missing(left) or _is_missing(right):
        return None
    return _OPS[clause.op](float(left), float(right))


def evaluate_row(dsl: ConditionDsl, row: dict) -> bool:
    """모든 절이 참(AND)일 때만 True. 평가 불가 절이 있으면 매치 실패 처리."""
    validate_dsl(dsl)
    return all(_clause_holds(c, row) is True for c in dsl.all)


def evaluate_frame(dsl: ConditionDsl, df: pd.DataFrame) -> list[date]:
    """지표 DataFrame에서 조건을 만족하는 거래일 목록 반환."""
    validate_dsl(dsl)
    matched: list[date] = []
    for _, row in df.iterrows():
        rowdict = row.to_dict()
        if all(_clause_holds(c, rowdict) is True for c in dsl.all):
            matched.append(rowdict["date"])
    return matched
