import json
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from service import crud
from service.deps import get_db, require_auth
from service.schemas import WordListCreate, WordListUpdate, WordListOut

router = APIRouter(prefix="/api/wordlists", tags=["wordlists"])


def _to_out(obj) -> WordListOut:
    return WordListOut(
        id=obj.id, name=obj.name, kind=obj.kind,
        items=json.loads(obj.items_json),
        created_at=obj.created_at, updated_at=obj.updated_at,
    )


@router.get("")
def list_(
    kind: str | None = None,
    db: Session = Depends(get_db),
    _username: str = Depends(require_auth),
) -> list[WordListOut]:
    return [_to_out(o) for o in crud.list_wordlists(db, kind=kind)]


@router.post("", status_code=status.HTTP_201_CREATED)
def create(
    payload: WordListCreate,
    db: Session = Depends(get_db),
    _username: str = Depends(require_auth),
) -> WordListOut:
    return _to_out(crud.create_wordlist(db, payload))


@router.put("/{id_}")
def update(
    id_: int,
    payload: WordListUpdate,
    db: Session = Depends(get_db),
    _username: str = Depends(require_auth),
) -> WordListOut:
    obj = crud.get_wordlist(db, id_)
    if obj is None:
        raise HTTPException(404, "not found")
    return _to_out(crud.update_wordlist(db, obj, payload))


@router.delete("/{id_}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    id_: int,
    db: Session = Depends(get_db),
    _username: str = Depends(require_auth),
) -> Response:
    obj = crud.get_wordlist(db, id_)
    if obj is None:
        raise HTTPException(404, "not found")
    if crud.wordlist_has_running_refs(db, id_):
        raise HTTPException(409, "wordlist is referenced by a running task")
    crud.delete_wordlist(db, obj)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
