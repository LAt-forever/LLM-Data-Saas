# backend/tests/test_supervisor_poll.py
import asyncio

import pytest


@pytest.mark.asyncio
async def test_poll_loop_calls_recover_periodically(monkeypatch):
    from service import supervisor

    called = {"n": 0}

    def fake_recover():
        called["n"] += 1
        return 0

    monkeypatch.setattr(supervisor, "recover_orphaned_running", fake_recover)
    # The loop takes interval as an explicit kwarg, so settings.supervisor_poll_seconds
    # is not consulted in this test. (settings is a frozen dataclass and cannot be
    # monkeypatched directly; the production wiring in main.py reads the setting.)
    stop = asyncio.Event()
    task = asyncio.create_task(supervisor.poll_loop(interval=0.05, stop=stop))
    await asyncio.sleep(0.2)
    stop.set()
    await task
    assert called["n"] >= 2
