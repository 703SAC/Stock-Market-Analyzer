"""타임라인 프로파일 — 장전/장중/마감별 브리핑 관점 설정."""

from __future__ import annotations

from typing import Literal

TimelinePhase = Literal["PRE_MARKET", "INTRADAY", "CLOSE"]


class TimelineProfile:
    def __init__(
        self,
        phase: TimelinePhase,
        label: str,
        emphasis: str,
        digest_lookback_days: int,
        event_window_days: int,
    ):
        self.phase = phase
        self.label = label
        self.emphasis = emphasis
        self.digest_lookback_days = digest_lookback_days
        self.event_window_days = event_window_days


_PROFILES: dict[str, TimelineProfile] = {
    "PRE_MARKET": TimelineProfile(
        phase="PRE_MARKET",
        label="장 시작 전 브리핑",
        emphasis=(
            "간밤 미국/글로벌 시황과 오늘 예정된 일정을 중심으로, 개장 시 주목할 "
            "테마와 종목 후보를 정리하라. 전일 마감 시황과의 연결을 강조하라."
        ),
        digest_lookback_days=3,
        event_window_days=5,  # 향후 일정 강조
    ),
    "INTRADAY": TimelineProfile(
        phase="INTRADAY",
        label="장중 점검 브리핑",
        emphasis=(
            "현재 진행 중인 메가 내러티브의 변화와 수급 흐름을 점검하라. "
            "장전 시나리오 대비 실제 전개를 비교하라."
        ),
        digest_lookback_days=2,
        event_window_days=2,
    ),
    "CLOSE": TimelineProfile(
        phase="CLOSE",
        label="장 마감 종합 시황",
        emphasis=(
            "오늘 시장의 종합 시황을 정리하라. 주도 테마, 특징주, 그룹사 역학, "
            "내일로 이어질 내러티브와 점검 포인트를 구조화하라."
        ),
        digest_lookback_days=5,
        event_window_days=3,
    ),
}


def get_profile(phase: TimelinePhase) -> TimelineProfile:
    if phase not in _PROFILES:
        raise ValueError(f"Unknown timeline phase: {phase}")
    return _PROFILES[phase]
