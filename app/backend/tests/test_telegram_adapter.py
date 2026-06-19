"""Telegram 어댑터 테스트 (Phase 4). 네트워크 없이 fake client/clock."""

import pytest

from services.telegram.adapter import Deduplicator, TelegramNotifier


class FakeResp:
    def __init__(self, status_code):
        self.status_code = status_code


class FakeClient:
    def __init__(self, status_code=200):
        self.status_code = status_code
        self.calls = []

    async def post(self, url, json=None):
        self.calls.append((url, json))
        return FakeResp(self.status_code)


def test_deduplicator_blocks_within_ttl():
    t = {"v": 0}
    dedup = Deduplicator(ttl_seconds=100, clock=lambda: t["v"])
    assert dedup.should_send("k") is True
    assert dedup.should_send("k") is False
    t["v"] = 201  # TTL 경과
    assert dedup.should_send("k") is True


@pytest.mark.asyncio
async def test_not_configured_returns_status():
    notifier = TelegramNotifier(token="", chat_id="")
    res = await notifier.send("hi")
    assert res["status"] == "not_configured"


@pytest.mark.asyncio
async def test_send_uses_injected_client():
    client = FakeClient(status_code=200)
    notifier = TelegramNotifier(token="T", chat_id="C", client=client)
    res = await notifier.send("안녕")
    assert res["status"] == "sent"
    assert client.calls[0][1]["chat_id"] == "C"
    assert client.calls[0][1]["text"] == "안녕"


@pytest.mark.asyncio
async def test_dedupe_skips_second_send():
    client = FakeClient(status_code=200)
    notifier = TelegramNotifier(token="T", chat_id="C", client=client)
    first = await notifier.send("x", dedupe_key="d1")
    second = await notifier.send("x", dedupe_key="d1")
    assert first["status"] == "sent"
    assert second["status"] == "skipped_duplicate"
    assert len(client.calls) == 1


@pytest.mark.asyncio
async def test_error_status_on_non_200():
    client = FakeClient(status_code=500)
    notifier = TelegramNotifier(token="T", chat_id="C", client=client)
    res = await notifier.send("x")
    assert res["status"] == "error"
    assert len(client.calls) == 2  # 2회 재시도
