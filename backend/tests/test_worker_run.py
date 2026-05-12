# backend/tests/test_worker_run.py
import json

from service import crud, db as dbmod, models
from service.schemas import (
    ApiConfigCreate, WordListCreate, PromptTemplateCreate, CategoryCreate
)


def _bootstrap_running_task(tmp_path, monkeypatch):
    """Create a fully-configured Task in 'running' state and return its id."""
    import sys
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "app.db"))
    for m in [k for k in list(sys.modules) if k == "service" or k.startswith("service.")]:
        sys.modules.pop(m, None)
    import service.config  # noqa: F401
    import service.db as dbmod_fresh
    import service.models  # noqa: F401
    dbmod_fresh.init_engine()
    dbmod_fresh.Base.metadata.create_all(dbmod_fresh.engine)

    from service import crud, models  # noqa
    with dbmod_fresh.SessionLocal() as s:
        api = crud.create_api_config(s, ApiConfigCreate(
            name="A", base_url="x", api_key="k",
            model_name="m", type="openai"))
        s_wl = crud.create_wordlist(s, WordListCreate(
            name="scn", kind="scenario", items=["sa", "sb"]))
        t_wl = crud.create_wordlist(s, WordListCreate(
            name="tne", kind="tone", items=["ta", "tb"]))
        pt = crud.create_prompt_template(s, PromptTemplateCreate(
            name="p", body="cat={category} scn={scenario} tne={tone} n={batch_size}",
            variables=["category", "scenario", "tone", "batch_size"]))
        cat = crud.create_category(s, CategoryCreate(
            sample_type="black", name="X", description="",
            prompt_template_id=pt.id, scenario_list_id=s_wl.id,
            tone_list_id=t_wl.id, default_target_count=10))
        task = crud.create_task_snapshot(
            s, cat.id, api.id,
            target_count=20, batch_size=5, max_workers=2, max_per_file=50,
            created_by_label=None, resume_from_task_id=None)
        out_dir = tmp_path / f"data/task-{task.id}"
        out_dir.mkdir(parents=True, exist_ok=True)
        crud.mark_task_started(s, task.id, worker_pid=0,
                               output_dir=str(out_dir))
        return task.id, dbmod_fresh


def test_worker_run_with_mock_llm_writes_target_rows(tmp_path, monkeypatch):
    task_id, dbmod_fresh = _bootstrap_running_task(tmp_path, monkeypatch)
    from service import worker_run
    worker_run.run_task(task_id, mock_llm=True)

    with dbmod_fresh.SessionLocal() as s:
        t = s.get(models.Task, task_id)
        assert t.status == "succeeded"
        assert t.progress_current == 20
        ev_types = [e.type for e in s.query(models.TaskEvent)
                    .filter_by(task_id=task_id).order_by(models.TaskEvent.id).all()]
        assert ev_types[0] == "started"
        assert ev_types[-1] == "finished"
        assert "progress" in ev_types

    csvs = sorted((tmp_path / f"data/task-{task_id}").glob("*.csv"))
    assert len(csvs) >= 1
    total_rows = 0
    for p in csvs:
        with open(p, "r", encoding="utf-8-sig") as f:
            total_rows += max(0, sum(1 for _ in f) - 1)
    assert total_rows == 20


def test_worker_run_honors_abort_signal(tmp_path, monkeypatch):
    task_id, dbmod_fresh = _bootstrap_running_task(tmp_path, monkeypatch)
    # Pre-abort the task before running
    with dbmod_fresh.SessionLocal() as s:
        crud.set_task_status(s, task_id, "aborted")

    from service import worker_run
    worker_run.run_task(task_id, mock_llm=True)

    with dbmod_fresh.SessionLocal() as s:
        t = s.get(models.Task, task_id)
        # status stays aborted, did not flip to succeeded
        assert t.status == "aborted"
        # progress may be 0 or partial — must not equal target_count
        assert t.progress_current < 20


def test_worker_run_auth_error_marks_failed(tmp_path, monkeypatch):
    task_id, dbmod_fresh = _bootstrap_running_task(tmp_path, monkeypatch)

    # Patch LlmClient.call to raise AuthError
    from service import llm_client, worker_run

    class _AlwaysAuthErr:
        def __init__(self, *a, **kw): pass
        def call(self, prompt):
            raise llm_client.AuthError("forbidden")

    monkeypatch.setattr(worker_run, "LlmClient", _AlwaysAuthErr)
    worker_run.run_task(task_id, mock_llm=False)

    with dbmod_fresh.SessionLocal() as s:
        t = s.get(models.Task, task_id)
        assert t.status == "failed"
        assert "auth" in (t.error_msg or "").lower() or "forbidden" in (t.error_msg or "").lower()
