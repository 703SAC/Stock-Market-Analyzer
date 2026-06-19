"""스케줄러 잡 등록 테스트 (Phase 4)."""

from services.scheduler import DEFAULT_JOBS, build_scheduler


def test_default_jobs_cover_day_and_night():
    sessions = {j.session for j in DEFAULT_JOBS}
    assert sessions == {"KR_DAY", "US_NIGHT"}
    kr = next(j for j in DEFAULT_JOBS if j.session == "KR_DAY")
    assert kr.day_of_week == "mon-fri" and kr.hour == 15


async def _noop(session):
    return None


def test_build_scheduler_registers_all_jobs():
    sched = build_scheduler(_noop, tz="Asia/Seoul")
    try:
        ids = {j.id for j in sched.get_jobs()}
        assert ids == {"kr_day_close", "us_night_close"}
    finally:
        sched.shutdown(wait=False) if sched.running else None
