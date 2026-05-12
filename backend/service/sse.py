# backend/service/sse.py
import asyncio
import json
from typing import AsyncIterator

from service import crud, db as dbmod, models  # noqa: F401


_TERMINAL = {"succeeded", "failed", "aborted"}


async def event_stream(task_id: int, *, last_event_id: int = 0,
                       stop: asyncio.Event | None = None,
                       poll_interval: float = 0.5) -> AsyncIterator[dict]:
    """Async generator yielding SSE-shaped dicts:
       {"event": "event"|"finished", "id": "<int>", "data": "<json>"}.
    Stops when task reaches terminal status and no more new events, or when
    `stop` is set."""
    if dbmod.SessionLocal is None:
        dbmod.init_engine()
        dbmod.Base.metadata.create_all(dbmod.engine)

    stop = stop or asyncio.Event()
    cursor = last_event_id

    while not stop.is_set():
        # Capture needed fields INSIDE the session to avoid DetachedInstanceError.
        yield_batch: list[tuple[int, str, str, object]] = []
        terminal_status: str | None = None
        with dbmod.SessionLocal() as s:
            new_events = crud.events_since(s, task_id, since_id=cursor, limit=500)
            for ev in new_events:
                # Serialize ts: if datetime, isoformat; else use as-is.
                ts_val = ev.ts.isoformat() if hasattr(ev.ts, "isoformat") else ev.ts
                yield_batch.append((ev.id, ev.type, ev.message, ts_val))
            t = crud.get_task(s, task_id)
            if t is not None and t.status in _TERMINAL:
                terminal_status = t.status

        for ev_id, ev_type, ev_msg, ev_ts in yield_batch:
            cursor = ev_id
            yield {
                "event": "event",
                "id": str(ev_id),
                "data": json.dumps({
                    "type": ev_type,
                    "message": ev_msg,
                    "ts": ev_ts,
                }, ensure_ascii=False),
            }

        if terminal_status is not None:
            yield {
                "event": "finished",
                "id": str(cursor),
                "data": json.dumps({"status": terminal_status}),
            }
            return

        try:
            await asyncio.wait_for(stop.wait(), timeout=poll_interval)
        except asyncio.TimeoutError:
            continue
