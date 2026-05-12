import json
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from service import crud
from service.deps import get_db
from service.prompt_render import validate_template, PromptValidationError
from service.schemas import (
    PromptTemplateCreate, PromptTemplateUpdate, PromptTemplateOut
)

router = APIRouter(prefix="/api/prompt-templates", tags=["prompt-templates"])


def _to_out(obj) -> PromptTemplateOut:
    return PromptTemplateOut(
        id=obj.id, name=obj.name, body=obj.body,
        variables=json.loads(obj.variables_json),
        created_at=obj.created_at, updated_at=obj.updated_at,
    )


@router.get("")
def list_(db: Session = Depends(get_db)) -> list[PromptTemplateOut]:
    return [_to_out(o) for o in crud.list_prompt_templates(db)]


@router.post("", status_code=status.HTTP_201_CREATED)
def create(payload: PromptTemplateCreate,
           db: Session = Depends(get_db)) -> PromptTemplateOut:
    try:
        validate_template(payload.body, payload.variables)
    except PromptValidationError as e:
        raise HTTPException(400, str(e))
    obj = crud.create_prompt_template(db, payload)
    return _to_out(obj)


@router.put("/{id_}")
def update(id_: int, payload: PromptTemplateUpdate,
           db: Session = Depends(get_db)) -> PromptTemplateOut:
    obj = crud.get_prompt_template(db, id_)
    if obj is None:
        raise HTTPException(404, "not found")
    # Resolve final body+variables (use payload if provided, else existing)
    new_body = payload.body if payload.body is not None else obj.body
    new_vars = (payload.variables if payload.variables is not None
                else json.loads(obj.variables_json))
    try:
        validate_template(new_body, new_vars)
    except PromptValidationError as e:
        raise HTTPException(400, str(e))
    return _to_out(crud.update_prompt_template(db, obj, payload))


@router.delete("/{id_}", status_code=status.HTTP_204_NO_CONTENT)
def delete(id_: int, db: Session = Depends(get_db)) -> Response:
    obj = crud.get_prompt_template(db, id_)
    if obj is None:
        raise HTTPException(404, "not found")
    if crud.prompt_template_has_running_refs(db, id_):
        raise HTTPException(409, "template is referenced by a running task")
    crud.delete_prompt_template(db, obj)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
