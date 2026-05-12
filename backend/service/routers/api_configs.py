from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from service import crud
from service.deps import get_db
from service.schemas import (
    ApiConfigCreate, ApiConfigUpdate, ApiConfigOut
)
from service.security import mask_api_key

router = APIRouter(prefix="/api/api-configs", tags=["api-configs"])


def _to_out(obj) -> ApiConfigOut:
    return ApiConfigOut(
        id=obj.id, name=obj.name, base_url=obj.base_url,
        api_key_masked=mask_api_key(obj.api_key),
        model_name=obj.model_name, type=obj.type,
        created_at=obj.created_at, updated_at=obj.updated_at,
    )


@router.get("")
def list_(db: Session = Depends(get_db)) -> list[ApiConfigOut]:
    return [_to_out(o) for o in crud.list_api_configs(db)]


@router.post("", status_code=status.HTTP_201_CREATED)
def create(payload: ApiConfigCreate, db: Session = Depends(get_db)) -> ApiConfigOut:
    obj = crud.create_api_config(db, payload)
    return _to_out(obj)


@router.put("/{id_}")
def update(id_: int, payload: ApiConfigUpdate,
           db: Session = Depends(get_db)) -> ApiConfigOut:
    obj = crud.get_api_config(db, id_)
    if obj is None:
        raise HTTPException(404, "not found")
    obj = crud.update_api_config(db, obj, payload)
    return _to_out(obj)


@router.delete("/{id_}", status_code=status.HTTP_204_NO_CONTENT)
def delete(id_: int, db: Session = Depends(get_db)) -> Response:
    obj = crud.get_api_config(db, id_)
    if obj is None:
        raise HTTPException(404, "not found")
    if crud.api_config_has_running_refs(db, id_):
        raise HTTPException(409, "config is referenced by a running task")
    crud.delete_api_config(db, obj)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{id_}/reveal")
def reveal(id_: int, db: Session = Depends(get_db)) -> Response:
    from fastapi.responses import JSONResponse
    obj = crud.get_api_config(db, id_)
    if obj is None:
        raise HTTPException(404, "not found")
    return JSONResponse(
        {"id": obj.id, "api_key": obj.api_key},
        headers={"Cache-Control": "no-store"},
    )


import time

import requests
from openai import OpenAI


def _ping_llm(base_url: str, api_key: str, model_name: str, api_type: str) -> dict:
    """Send a minimal request to verify the endpoint is reachable.
    Returns {ok, latency_ms, sample_text} on success or {ok: False, error}.
    Kept as a module-level function so tests can monkeypatch it."""
    t0 = time.monotonic()
    try:
        if api_type == "openai":
            client = OpenAI(api_key=api_key, base_url=base_url, timeout=15)
            rsp = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=4,
            )
            sample = (rsp.choices[0].message.content or "")[:50]
        else:  # raw
            rsp = requests.post(
                f"{base_url.rstrip('/')}/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}",
                         "Content-Type": "application/json"},
                json={"model": model_name, "stream": False,
                      "messages": [{"role": "user", "content": "ping"}]},
                timeout=15,
            )
            rsp.raise_for_status()
            sample = (rsp.json()["choices"][0]["message"]["content"] or "")[:50]
        latency_ms = int((time.monotonic() - t0) * 1000)
        return {"ok": True, "latency_ms": latency_ms, "sample_text": sample}
    except Exception as e:
        return {"ok": False, "error": str(e)[:300]}


@router.post("/{id_}/test")
def test_config(id_: int, db: Session = Depends(get_db)) -> dict:
    obj = crud.get_api_config(db, id_)
    if obj is None:
        raise HTTPException(404, "not found")
    return _ping_llm(obj.base_url, obj.api_key, obj.model_name, obj.type)
