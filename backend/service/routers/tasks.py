import csv
import json
import zipfile
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from service import crud, supervisor, worker_io
from service.config import settings
from service.deps import get_db
from service.schemas import (
    TaskCreate, TaskOut, TaskDetail, TaskEventOut
)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def _row_to_out(t) -> TaskOut:
    return TaskOut(
        id=t.id,
        sample_type=t.snapshot_sample_type,
        category_name=t.snapshot_category_name,
        api_config_id=t.api_config_id,
        api_model=t.snapshot_model_name,
        target_count=t.target_count,
        batch_size=t.batch_size,
        max_workers=t.max_workers,
        max_per_file=t.max_per_file,
        status=t.status,
        progress_current=t.progress_current,
        progress_total=t.progress_total,
        created_at=t.created_at,
        started_at=t.started_at,
        finished_at=t.finished_at,
        error_msg=t.error_msg,
        output_dir=t.output_dir,
        created_by_label=t.created_by_label,
        resume_from_task_id=t.resume_from_task_id,
    )


def _row_to_detail(t, events) -> TaskDetail:
    base = _row_to_out(t).model_dump()
    return TaskDetail(
        **base,
        snapshot_prompt_body=t.snapshot_prompt_body,
        snapshot_scenario_items=json.loads(t.snapshot_scenario_items_json),
        snapshot_tone_items=json.loads(t.snapshot_tone_items_json),
        snapshot_api_base_url=t.snapshot_api_base_url,
        snapshot_api_type=t.snapshot_api_type,
        recent_events=[TaskEventOut(id=e.id, ts=e.ts, type=e.type, message=e.message)
                       for e in events],
    )


@router.get("")
def list_(status: str | None = None, category_id: int | None = None,
          page: int = 1, size: int = 50,
          db: Session = Depends(get_db)) -> list[TaskOut]:
    rows = crud.list_tasks(db, status=status, category_id=category_id,
                           page=max(1, page), size=min(max(1, size), 200))
    return [_row_to_out(t) for t in rows]


@router.get("/{id_}")
def get(id_: int, db: Session = Depends(get_db)) -> TaskDetail:
    t = crud.get_task(db, id_)
    if t is None:
        raise HTTPException(404, "not found")
    return _row_to_detail(t, crud.recent_events(db, id_, limit=50))


@router.post("", status_code=status.HTTP_201_CREATED)
def create(payload: TaskCreate, db: Session = Depends(get_db)) -> TaskOut:
    try:
        t = crud.create_task_snapshot(
            db,
            category_id=payload.category_id,
            api_config_id=payload.api_config_id,
            target_count=payload.target_count,
            batch_size=payload.batch_size,
            max_workers=payload.max_workers,
            max_per_file=payload.max_per_file,
            created_by_label=payload.created_by_label,
            resume_from_task_id=payload.resume_from_task_id,
        )
    except ValueError as e:
        raise HTTPException(404, str(e))

    # If resume_from is given, copy old CSVs into new task dir
    if payload.resume_from_task_id is not None:
        old = crud.get_task(db, payload.resume_from_task_id)
        if old is not None and old.output_dir:
            new_dir = settings.task_dir(t.id)
            worker_io.copy_resume_csvs(Path(old.output_dir), new_dir)

    supervisor.spawn_worker(t.id)
    db.refresh(t)
    return _row_to_out(t)


@router.post("/{id_}/abort")
def abort(id_: int, db: Session = Depends(get_db)) -> dict:
    t = crud.get_task(db, id_)
    if t is None:
        raise HTTPException(404, "not found")
    if t.status not in ("pending", "running"):
        raise HTTPException(409, f"task is {t.status}, cannot abort")
    crud.set_task_status(db, id_, "aborted")
    if t.worker_pid:
        supervisor.terminate_worker(t.worker_pid)
    crud.add_task_event(db, id_, "aborted", "aborted via API")
    return {"id": id_, "status": "aborted"}


@router.delete("/{id_}", status_code=status.HTTP_204_NO_CONTENT)
def delete(id_: int, delete_files: bool = True,
           db: Session = Depends(get_db)) -> Response:
    t = crud.get_task(db, id_)
    if t is None:
        raise HTTPException(404, "not found")
    if t.status == "running":
        raise HTTPException(409, "task is running; abort first")
    out_dir = Path(t.output_dir) if t.output_dir else None

    # delete events then task
    from service import models
    db.query(models.TaskEvent).filter_by(task_id=id_).delete()
    db.delete(t); db.commit()

    if delete_files and out_dir and out_dir.exists():
        import shutil
        shutil.rmtree(out_dir, ignore_errors=True)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{id_}/preview")
def preview(id_: int, db: Session = Depends(get_db)) -> dict:
    t = crud.get_task(db, id_)
    if t is None:
        raise HTTPException(404, "not found")
    out_dir = Path(t.output_dir) if t.output_dir else None
    if not out_dir or not out_dir.exists():
        return {"header": [], "rows": []}
    rows: list[list[str]] = []
    header: list[str] = []
    for p in sorted(out_dir.glob("*.csv")):
        with open(p, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            try:
                file_header = next(reader)
            except StopIteration:
                continue
            if not header:
                header = file_header
            for row in reader:
                rows.append(row)
                if len(rows) >= settings.preview_rows:
                    return {"header": header, "rows": rows}
    return {"header": header, "rows": rows}


@router.get("/{id_}/download")
def download(id_: int, db: Session = Depends(get_db)):
    t = crud.get_task(db, id_)
    if t is None:
        raise HTTPException(404, "not found")
    out_dir = Path(t.output_dir) if t.output_dir else None
    if not out_dir or not out_dir.exists():
        raise HTTPException(404, "no output yet")
    files = sorted(out_dir.glob("*.csv"))
    if not files:
        raise HTTPException(404, "no csv output")

    if len(files) == 1:
        def iter_file():
            with open(files[0], "rb") as f:
                while chunk := f.read(64 * 1024):
                    yield chunk
        return StreamingResponse(
            iter_file(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="task-{id_}.csv"'},
        )

    def iter_zip():
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in files:
                zf.write(p, arcname=p.name)
        buf.seek(0)
        yield from iter(lambda: buf.read(64 * 1024), b"")

    return StreamingResponse(
        iter_zip(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="task-{id_}.zip"'},
    )


@router.get("/{id_}/events")
def events(id_: int, since_id: int = 0, limit: int = 200,
           db: Session = Depends(get_db)) -> list[TaskEventOut]:
    t = crud.get_task(db, id_)
    if t is None:
        raise HTTPException(404, "not found")
    items = crud.events_since(db, id_, since_id=since_id,
                              limit=min(max(1, limit), 1000))
    return [TaskEventOut(id=e.id, ts=e.ts, type=e.type, message=e.message)
            for e in items]


@router.get("/{id_}/log")
def log(id_: int, lines: int = 1000) -> dict:
    if lines <= 0:
        lines = 1000
    path = settings.task_log(id_)
    if not path.exists():
        return {"lines": []}
    # Cheap tail
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        all_lines = f.readlines()
    return {"lines": all_lines[-lines:]}
