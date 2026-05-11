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
