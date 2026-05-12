import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from service import models
from service.schemas import (
    ApiConfigCreate, ApiConfigUpdate,
    WordListCreate, WordListUpdate,
    PromptTemplateCreate, PromptTemplateUpdate,
    CategoryCreate, CategoryUpdate,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------- ApiConfig ----------
def create_api_config(db: Session, payload: ApiConfigCreate) -> models.ApiConfig:
    obj = models.ApiConfig(
        name=payload.name, base_url=payload.base_url, api_key=payload.api_key,
        model_name=payload.model_name, type=payload.type,
        created_at=_now(), updated_at=_now(),
    )
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


def list_api_configs(db: Session) -> list[models.ApiConfig]:
    return list(db.scalars(select(models.ApiConfig).order_by(models.ApiConfig.id)))


def get_api_config(db: Session, id_: int) -> models.ApiConfig | None:
    return db.get(models.ApiConfig, id_)


def update_api_config(db: Session, obj: models.ApiConfig,
                      payload: ApiConfigUpdate) -> models.ApiConfig:
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    obj.updated_at = _now()
    db.commit(); db.refresh(obj); return obj


def delete_api_config(db: Session, obj: models.ApiConfig) -> None:
    db.delete(obj); db.commit()


def api_config_has_running_refs(db: Session, id_: int) -> bool:
    q = select(models.Task.id).where(
        models.Task.api_config_id == id_,
        models.Task.status == "running",
    ).limit(1)
    return db.scalar(q) is not None


# ---------- WordList ----------
def create_wordlist(db: Session, payload: WordListCreate) -> models.WordList:
    obj = models.WordList(
        name=payload.name, kind=payload.kind,
        items_json=json.dumps(payload.items, ensure_ascii=False),
        created_at=_now(), updated_at=_now(),
    )
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


def list_wordlists(db: Session, kind: str | None = None) -> list[models.WordList]:
    stmt = select(models.WordList).order_by(models.WordList.id)
    if kind:
        stmt = stmt.where(models.WordList.kind == kind)
    return list(db.scalars(stmt))


def get_wordlist(db: Session, id_: int) -> models.WordList | None:
    return db.get(models.WordList, id_)


def update_wordlist(db: Session, obj: models.WordList,
                    payload: WordListUpdate) -> models.WordList:
    data = payload.model_dump(exclude_unset=True)
    if "items" in data:
        obj.items_json = json.dumps(data.pop("items"), ensure_ascii=False)
    for k, v in data.items():
        setattr(obj, k, v)
    obj.updated_at = _now()
    db.commit(); db.refresh(obj); return obj


def delete_wordlist(db: Session, obj: models.WordList) -> None:
    db.delete(obj); db.commit()


def wordlist_has_running_refs(db: Session, id_: int) -> bool:
    q = select(models.Category.id).where(
        (models.Category.scenario_list_id == id_)
        | (models.Category.tone_list_id == id_)
    )
    cat_ids = list(db.scalars(q))
    if not cat_ids:
        return False
    q2 = select(models.Task.id).where(
        models.Task.category_id.in_(cat_ids),
        models.Task.status == "running",
    ).limit(1)
    return db.scalar(q2) is not None


# ---------- PromptTemplate ----------
def create_prompt_template(db: Session, payload: PromptTemplateCreate) -> models.PromptTemplate:
    obj = models.PromptTemplate(
        name=payload.name, body=payload.body,
        variables_json=json.dumps(payload.variables, ensure_ascii=False),
        created_at=_now(), updated_at=_now(),
    )
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


def list_prompt_templates(db: Session) -> list[models.PromptTemplate]:
    return list(db.scalars(select(models.PromptTemplate).order_by(models.PromptTemplate.id)))


def get_prompt_template(db: Session, id_: int) -> models.PromptTemplate | None:
    return db.get(models.PromptTemplate, id_)


def update_prompt_template(db: Session, obj: models.PromptTemplate,
                           payload: PromptTemplateUpdate) -> models.PromptTemplate:
    data = payload.model_dump(exclude_unset=True)
    if "variables" in data:
        obj.variables_json = json.dumps(data.pop("variables"), ensure_ascii=False)
    for k, v in data.items():
        setattr(obj, k, v)
    obj.updated_at = _now()
    db.commit(); db.refresh(obj); return obj


def delete_prompt_template(db: Session, obj: models.PromptTemplate) -> None:
    db.delete(obj); db.commit()


def prompt_template_has_running_refs(db: Session, id_: int) -> bool:
    q = select(models.Category.id).where(
        models.Category.prompt_template_id == id_
    )
    cat_ids = list(db.scalars(q))
    if not cat_ids:
        return False
    q2 = select(models.Task.id).where(
        models.Task.category_id.in_(cat_ids),
        models.Task.status == "running",
    ).limit(1)
    return db.scalar(q2) is not None


# ---------- Category ----------
def create_category(db: Session, payload: CategoryCreate) -> models.Category:
    obj = models.Category(**payload.model_dump(),
                          created_at=_now(), updated_at=_now())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


def list_categories(db: Session, sample_type: str | None = None) -> list[models.Category]:
    stmt = select(models.Category).order_by(models.Category.id)
    if sample_type:
        stmt = stmt.where(models.Category.sample_type == sample_type)
    return list(db.scalars(stmt))


def get_category(db: Session, id_: int) -> models.Category | None:
    return db.get(models.Category, id_)


def update_category(db: Session, obj: models.Category,
                    payload: CategoryUpdate) -> models.Category:
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    obj.updated_at = _now()
    db.commit(); db.refresh(obj); return obj


def delete_category(db: Session, obj: models.Category) -> None:
    db.delete(obj); db.commit()


def category_has_running_refs(db: Session, id_: int) -> bool:
    q = select(models.Task.id).where(
        models.Task.category_id == id_,
        models.Task.status == "running",
    ).limit(1)
    return db.scalar(q) is not None


# ---------- Task (snapshot creation) ----------
def create_task_snapshot(
    db: Session, category_id: int, api_config_id: int,
    target_count: int, batch_size: int, max_workers: int, max_per_file: int,
    created_by_label: str | None, resume_from_task_id: int | None,
) -> models.Task:
    cat = db.get(models.Category, category_id)
    api = db.get(models.ApiConfig, api_config_id)
    if cat is None or api is None:
        raise ValueError("category or api_config not found")
    pt = db.get(models.PromptTemplate, cat.prompt_template_id)
    s_wl = db.get(models.WordList, cat.scenario_list_id)
    t_wl = db.get(models.WordList, cat.tone_list_id)
    if pt is None or s_wl is None or t_wl is None:
        raise ValueError("dangling foreign keys on category")

    obj = models.Task(
        category_id=category_id, api_config_id=api_config_id,
        snapshot_sample_type=cat.sample_type,
        snapshot_category_name=cat.name,
        snapshot_prompt_body=pt.body,
        snapshot_scenario_items_json=s_wl.items_json,
        snapshot_tone_items_json=t_wl.items_json,
        snapshot_api_base_url=api.base_url,
        snapshot_api_key=api.api_key,
        snapshot_model_name=api.model_name,
        snapshot_api_type=api.type,
        target_count=target_count, batch_size=batch_size,
        max_workers=max_workers, max_per_file=max_per_file,
        status="pending", progress_current=0, progress_total=target_count,
        created_at=_now(),
        output_dir="",  # filled by supervisor when spawning
        created_by_label=created_by_label,
        resume_from_task_id=resume_from_task_id,
    )
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


def list_tasks(db: Session, *, status: str | None = None,
               category_id: int | None = None,
               page: int = 1, size: int = 50) -> list[models.Task]:
    stmt = select(models.Task).order_by(models.Task.id.desc())
    if status:
        stmt = stmt.where(models.Task.status == status)
    if category_id:
        stmt = stmt.where(models.Task.category_id == category_id)
    stmt = stmt.offset((page - 1) * size).limit(size)
    return list(db.scalars(stmt))


def get_task(db: Session, id_: int) -> models.Task | None:
    return db.get(models.Task, id_)


def mark_task_started(db: Session, task_id: int, worker_pid: int,
                      output_dir: str) -> models.Task:
    obj = db.get(models.Task, task_id)
    if obj is None:
        raise ValueError(f"task {task_id} not found")
    # Race protection: a very fast child may have already written a terminal
    # status before the parent's mark_task_started landed. Don't overwrite;
    # leave the row untouched and record a warning event so the flip is visible.
    if obj.status in ("succeeded", "failed", "aborted"):
        add_task_event(
            db, task_id, "warning",
            f"mark_task_started skipped: task already {obj.status}")
        return obj
    obj.worker_pid = worker_pid
    obj.output_dir = output_dir
    obj.status = "running"
    obj.started_at = _now()
    db.commit(); db.refresh(obj)
    return obj


def set_task_worker_pid(db: Session, task_id: int, pid: int) -> None:
    """Narrow update: write worker_pid only. Does not change status,
    output_dir, started_at, or emit events. Used by the supervisor after
    Popen returns to patch in the real pid without racing against the
    child's own status writes."""
    obj = db.get(models.Task, task_id)
    if obj is None:
        raise ValueError(f"task {task_id} not found")
    obj.worker_pid = pid
    db.commit()


def update_task_progress(db: Session, task_id: int, current: int) -> models.Task:
    obj = db.get(models.Task, task_id)
    if obj is None:
        raise ValueError(f"task {task_id} not found")
    obj.progress_current = current
    db.commit(); db.refresh(obj)
    return obj


def set_task_status(db: Session, task_id: int, status: str,
                    error_msg: str | None = None) -> models.Task:
    obj = db.get(models.Task, task_id)
    if obj is None:
        raise ValueError(f"task {task_id} not found")
    obj.status = status
    if error_msg is not None:
        obj.error_msg = error_msg
    db.commit(); db.refresh(obj)
    return obj


def mark_task_finished(db: Session, task_id: int, status: str,
                       error_msg: str | None = None) -> models.Task:
    obj = db.get(models.Task, task_id)
    if obj is None:
        raise ValueError(f"task {task_id} not found")
    obj.status = status
    obj.finished_at = _now()
    if error_msg is not None:
        obj.error_msg = error_msg
    db.commit(); db.refresh(obj)
    return obj


def add_task_event(db: Session, task_id: int, type_: str, message: str) -> models.TaskEvent:
    ev = models.TaskEvent(task_id=task_id, ts=_now(), type=type_, message=message)
    db.add(ev); db.commit(); db.refresh(ev)
    return ev


def recent_events(db: Session, task_id: int, limit: int = 50) -> list[models.TaskEvent]:
    stmt = (select(models.TaskEvent)
            .where(models.TaskEvent.task_id == task_id)
            .order_by(models.TaskEvent.id.desc())
            .limit(limit))
    return list(reversed(list(db.scalars(stmt))))


def events_since(db: Session, task_id: int, since_id: int,
                 limit: int = 500) -> list[models.TaskEvent]:
    stmt = (select(models.TaskEvent)
            .where(models.TaskEvent.task_id == task_id,
                   models.TaskEvent.id > since_id)
            .order_by(models.TaskEvent.id.asc())
            .limit(limit))
    return list(db.scalars(stmt))
