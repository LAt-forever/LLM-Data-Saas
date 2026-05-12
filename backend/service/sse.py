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
        # Read status FIRST so that any events the worker writes between our
        # status check and our events_since are guaranteed to be visible to
        # events_since (events_since happens later in the same iteration).
        # Then events_since picks up everything committed up to that point,
        # including events written concurrently with the status flip.
        yield_batch: list[tuple[int, str, str, object]] = []
        terminal_status: str | None = None
        with dbmod.SessionLocal() as s:
            t = crud.get_task(s, task_id)
            if t is not None and t.status in _TERMINAL:
                terminal_status = t.status
            new_events = crud.events_since(s, task_id, since_id=cursor, limit=500)
            for ev in new_events:
                # Serialize ts: if datetime, isoformat; else use as-is.
                ts_val = ev.ts.isoformat() if hasattr(ev.ts, "isoformat") else ev.ts
                yield_batch.append((ev.id, ev.type, ev.message, ts_val))

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
            # Defensive final drain: events committed AFTER our events_since
            # call within this iteration would otherwise be lost on the
            # forthcoming `return`. Do one more fetch in a fresh session
            # to flush any straggler events that arrived in the meantime.
            drain_batch: list[tuple[int, str, str, object]] = []
            with dbmod.SessionLocal() as s:
                final_events = crud.events_since(s, task_id, since_id=cursor, limit=500)
                for ev in final_events:
                    ts_val = ev.ts.isoformat() if hasattr(ev.ts, "isoformat") else ev.ts
                    drain_batch.append((ev.id, ev.type, ev.message, ts_val))
            for ev_id, ev_type, ev_msg, ev_ts in drain_batch:
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
