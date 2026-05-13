# backend/service/routers/tasks_stream.py
import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from service import sse, crud, db as dbmod
from service.deps import require_auth

router = APIRouter(prefix="/api/tasks", tags=["tasks-stream"])


@router.get("/{id_}/stream")
async def stream(
    id_: int,
    request: Request,
    _username: str = Depends(require_auth),
) -> EventSourceResponse:
    if dbmod.SessionLocal is None:
        dbmod.init_engine()
    with dbmod.SessionLocal() as s:
        if crud.get_task(s, id_) is None:
            raise HTTPException(404, "not found")
    last_id_header = request.headers.get("last-event-id")
    last_id = int(last_id_header) if last_id_header and last_id_header.isdigit() else 0

    stop = asyncio.Event()

    async def proxy():
        async for evt in sse.event_stream(id_, last_event_id=last_id, stop=stop):
            if await request.is_disconnected():
                stop.set()
                break
            yield evt

    return EventSourceResponse(proxy(), ping=15)
