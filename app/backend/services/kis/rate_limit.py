"""Simple rate limiter for KIS API calls."""

import asyncio
import time
from threading import Lock

_lock = Lock()
_last_call = 0.0
_min_interval = 0.2


def kis_throttle() -> None:
    global _last_call
    with _lock:
        now = time.monotonic()
        elapsed = now - _last_call
        if elapsed < _min_interval:
            time.sleep(_min_interval - elapsed)
        _last_call = time.monotonic()


async def kis_throttle_async() -> None:
    await asyncio.to_thread(kis_throttle)
