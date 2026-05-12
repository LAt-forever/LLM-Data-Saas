# backend/tests/test_sse.py
import asyncio
import json

import pytest

from service.schemas import (
    ApiConfigCreate, WordListCreate, PromptTemplateCreate, CategoryCreate
)


def _bootstrap(tmp_path, monkeypatch):
    import sys
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "app.db"))
    for m in [k for k in list(sys.modules) if k == "service" or k.startswith("service.")]:
        sys.modules.pop(m, None)
    import service.config  # noqa: F401
    import service.db as dbmod
    import service.models  # noqa: F401
    dbmod.init_engine()
    dbmod.Base.metadata.create_all(dbmod.engine)
    return dbmod


def _make_task(dbmod):
    from service import crud
    with dbmod.SessionLocal() as s:
        api = crud.create_api_config(s, ApiConfigCreate(
            name="A", base_url="x", api_key="k",
            model_name="m", type="openai"))
        wl = crud.create_wordlist(s, WordListCreate(
            name="w", kind="scenario", items=["a"]))
        wl2 = crud.create_wordlist(s, WordListCreate(
            name="w2", kind="tone", items=["b"]))
        pt = crud.create_prompt_template(s, PromptTemplateCreate(
            name="p", body="x", variables=[]))
        cat = crud.create_category(s, CategoryCreate(
            sample_type="black", name="C", description="",
            prompt_template_id=pt.id, scenario_list_id=wl.id,
            tone_list_id=wl2.id, default_target_count=1))
        t = crud.create_task_snapshot(s, cat.id, api.id, 5, 1, 1, 50, None, None)
        return t.id


@pytest.mark.asyncio
async def test_sse_streams_events_and_closes_on_terminal(tmp_path, monkeypatch):
    dbmod = _bootstrap(tmp_path, monkeypatch)
    task_id = _make_task(dbmod)
    from service import crud, sse

    with dbmod.SessionLocal() as s:
        crud.add_task_event(s, task_id, "started", "start msg")

    received: list[dict] = []
    stop = asyncio.Event()

    async def consumer():
        async for event in sse.event_stream(task_id, last_event_id=0, stop=stop,
                                            poll_interval=0.05):
            received.append(event)
            if event.get("event") == "finished":
                break

    consumer_task = asyncio.create_task(consumer())
    await asyncio.sleep(0.1)
    with dbmod.SessionLocal() as s:
        crud.add_task_event(s, task_id, "progress", "2/5")
        crud.add_task_event(s, task_id, "progress", "4/5")
        crud.mark_task_finished(s, task_id, "succeeded")
        crud.add_task_event(s, task_id, "finished", "done")
    await asyncio.wait_for(consumer_task, timeout=3)

    event_types = [e.get("event", "event") for e in received]
    assert "finished" in event_types
    msgs = [json.loads(e["data"]).get("message", "") for e in received
            if "data" in e]
    assert any("2/5" in m or "4/5" in m for m in msgs)
    # This is the event the worker writes AFTER mark_task_finished — it must
    # survive the terminal race. Adding this assertion would have caught the
    # lost-event bug fixed by the events_since drain.
    assert any("done" in m for m in msgs), (
        "the worker's final 'done' event was lost — likely the terminal-flip race"
    )


@pytest.mark.asyncio
async def test_sse_respects_last_event_id(tmp_path, monkeypatch):
    dbmod = _bootstrap(tmp_path, monkeypatch)
    task_id = _make_task(dbmod)
    from service import crud, sse

    with dbmod.SessionLocal() as s:
        e1 = crud.add_task_event(s, task_id, "started", "s")
        e2 = crud.add_task_event(s, task_id, "progress", "1/5")

    received: list[dict] = []
    stop = asyncio.Event()

    async def consumer():
        async for evt in sse.event_stream(task_id, last_event_id=e1.id,
                                          stop=stop, poll_interval=0.05):
            received.append(evt)
            stop.set()
            break

    await asyncio.wait_for(consumer(), timeout=2)
    assert len(received) == 1
    assert int(received[0]["id"]) == e2.id
