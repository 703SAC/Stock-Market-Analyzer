"""조건식 DSL 평가 엔진 테스트 (Phase 2)."""

from datetime import date, timedelta

import pytest

from services.chart.condition_schema import ConditionClause, ConditionDsl
from services.chart.evaluator import evaluate_frame, evaluate_row, validate_dsl
from services.chart.indicators import compute_indicator_frame
from services.chart.models import DailyCandle


def _candles(closes, vols, start=date(2026, 1, 1)):
    return [
        DailyCandle(
            date=start + timedelta(days=i),
            open=c, high=c, low=c, close=float(c), volume=v,
        )
        for i, (c, v) in enumerate(zip(closes, vols))
    ]


def test_validate_rejects_disallowed_indicator():
    dsl = ConditionDsl(all=[ConditionClause(indicator="os.system", op=">", value=1)])
    with pytest.raises(ValueError, match="Disallowed indicator"):
        validate_dsl(dsl)


def test_validate_requires_value_or_right():
    dsl = ConditionDsl(all=[ConditionClause(indicator="close", op=">")])
    with pytest.raises(ValueError, match="needs a value"):
        validate_dsl(dsl)


def test_evaluate_row_value_comparison():
    dsl = ConditionDsl(all=[ConditionClause(indicator="volume", op=">", value=5_000_000)])
    assert evaluate_row(dsl, {"volume": 6_000_000}) is True
    assert evaluate_row(dsl, {"volume": 1_000_000}) is False


def test_evaluate_row_missing_indicator_is_false():
    dsl = ConditionDsl(all=[ConditionClause(indicator="rsi14", op="<", value=70)])
    assert evaluate_row(dsl, {"close": 100}) is False  # rsi14 없음 → 매치 실패


def test_evaluate_frame_indicator_vs_indicator():
    # 상승 추세: 후반 종가가 ma5 위로 올라옴
    closes = list(range(1, 21))
    vols = [1_000_000] * 20
    df = compute_indicator_frame(_candles(closes, vols))
    dsl = ConditionDsl(
        all=[ConditionClause(indicator="close", op=">", indicator_right="ma5")]
    )
    matched = evaluate_frame(dsl, df)
    # 단조 증가에서는 종가가 항상 5일 평균 위 → ma5가 채워진 모든 날 매치
    assert len(matched) == len(closes) - 4  # ma5는 5번째부터 유효
    assert all(isinstance(d, date) for d in matched)
