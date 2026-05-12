from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from service import crud
from service.deps import get_db
from service.schemas import CategoryCreate, CategoryUpdate, CategoryOut

router = APIRouter(prefix="/api/categories", tags=["categories"])


def _to_out(obj) -> CategoryOut:
    return CategoryOut(
        id=obj.id, sample_type=obj.sample_type, name=obj.name,
        description=obj.description,
        prompt_template_id=obj.prompt_template_id,
        scenario_list_id=obj.scenario_list_id,
        tone_list_id=obj.tone_list_id,
        default_target_count=obj.default_target_count,
        created_at=obj.created_at, updated_at=obj.updated_at,
    )


@router.get("")
def list_(sample_type: str | None = None,
          db: Session = Depends(get_db)) -> list[CategoryOut]:
    return [_to_out(o) for o in crud.list_categories(db, sample_type=sample_type)]


@router.get("/{id_}")
def get(id_: int, db: Session = Depends(get_db)) -> CategoryOut:
    obj = crud.get_category(db, id_)
    if obj is None:
        raise HTTPException(404, "not found")
    return _to_out(obj)


@router.post("", status_code=status.HTTP_201_CREATED)
def create(payload: CategoryCreate,
           db: Session = Depends(get_db)) -> CategoryOut:
    try:
        obj = crud.create_category(db, payload)
    except IntegrityError as e:
        raise HTTPException(400, f"foreign key violation: {e.orig}")
    return _to_out(obj)


@router.put("/{id_}")
def update(id_: int, payload: CategoryUpdate,
           db: Session = Depends(get_db)) -> CategoryOut:
    obj = crud.get_category(db, id_)
    if obj is None:
        raise HTTPException(404, "not found")
    return _to_out(crud.update_category(db, obj, payload))


@router.delete("/{id_}", status_code=status.HTTP_204_NO_CONTENT)
def delete(id_: int, db: Session = Depends(get_db)) -> Response:
    obj = crud.get_category(db, id_)
    if obj is None:
        raise HTTPException(404, "not found")
    if crud.category_has_running_refs(db, id_):
        raise HTTPException(409, "category is referenced by a running task")
    crud.delete_category(db, obj)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
