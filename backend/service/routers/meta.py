# backend/service/routers/meta.py
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from service import models
from service.deps import get_db, require_auth

router = APIRouter(prefix="/api", tags=["meta"])

SAMPLE_TYPES = ("black", "gray", "white")


@router.get("/sample-types")
def list_sample_types(
    db: Session = Depends(get_db),
    _username: str = Depends(require_auth),
) -> list[dict]:
    counts = dict(db.execute(
        select(models.Category.sample_type, func.count(models.Category.id))
        .group_by(models.Category.sample_type)
    ).all())
    return [{"sample_type": st, "category_count": counts.get(st, 0)}
            for st in SAMPLE_TYPES]
