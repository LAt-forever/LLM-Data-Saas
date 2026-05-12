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


def _bootstrap_long_running_task(tmp_path, monkeypatch, *, target_count=1000,
                                 batch_size=5, max_workers=2):
    """Bootstrap helper that creates a task big enough to observe mid-run abort."""
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

    from service import crud
    with dbmod_fresh.SessionLocal() as s:
        api = crud.create_api_config(s, ApiConfigCreate(
            name="A", base_url="x", api_key="k",
            model_name="m", type="openai"))
        s_wl = crud.create_wordlist(s, WordListCreate(
            name="scn", kind="scenario", items=["sa"]))
        t_wl = crud.create_wordlist(s, WordListCreate(
            name="tne", kind="tone", items=["ta"]))
        pt = crud.create_prompt_template(s, PromptTemplateCreate(
            name="p", body="cat={category} scn={scenario} tne={tone} n={batch_size}",
            variables=["category", "scenario", "tone", "batch_size"]))
        cat = crud.create_category(s, CategoryCreate(
            sample_type="black", name="X", description="",
            prompt_template_id=pt.id, scenario_list_id=s_wl.id,
            tone_list_id=t_wl.id, default_target_count=target_count))
        task = crud.create_task_snapshot(
            s, cat.id, api.id,
            target_count=target_count, batch_size=batch_size,
            max_workers=max_workers, max_per_file=10000,
            created_by_label=None, resume_from_task_id=None)
        out_dir = tmp_path / f"data/task-{task.id}"
        out_dir.mkdir(parents=True, exist_ok=True)
        crud.mark_task_started(s, task.id, worker_pid=0,
                               output_dir=str(out_dir))
        return task.id, dbmod_fresh


def test_worker_run_honors_abort_mid_run(tmp_path, monkeypatch):
    """Verify abort requested WHILE the worker is running stops CSV growth
    quickly (within bounded extra rows) — not at the next while iteration."""
    import threading
    import time

    task_id, dbmod_fresh = _bootstrap_long_running_task(
        tmp_path, monkeypatch,
        target_count=2000, batch_size=5, max_workers=2)

    from service import worker_run

    # Make mock calls slow so we have time to observe + abort mid-batch.
    original = worker_run._mock_call

    def slow_mock(prompt, batch_size):
        time.sleep(0.05)
        return original(prompt, batch_size)

    monkeypatch.setattr(worker_run, "_mock_call", slow_mock)

    done = threading.Event()

    def runner():
        try:
            worker_run.run_task(task_id, mock_llm=True)
        finally:
            done.set()

    t = threading.Thread(target=runner)
    t.start()

    # Let it write some rows.
    time.sleep(0.4)

    with dbmod_fresh.SessionLocal() as s:
        progress_before_abort = s.get(models.Task, task_id).progress_current
        crud.set_task_status(s, task_id, "aborted")

    # Wait for worker to notice and exit.
    done.wait(timeout=5)
    assert not t.is_alive()

    with dbmod_fresh.SessionLocal() as s:
        task = s.get(models.Task, task_id)

    assert task.status == "aborted"
    # Worker actually ran (wrote some rows before abort).
    assert task.progress_current > 0
    # Did not complete the target.
    assert task.progress_current < 2000

    # Bleed bound: after abort flag was set, at most one batch worth of
    # extra rows should leak through. With max_workers=2, batch_size=5, that
    # is ≤ 10 rows per parallel future, so ≤ 20 total. Use 30 as a safety
    # margin for scheduling jitter across platforms.
    extra_rows_after_abort = task.progress_current - progress_before_abort
    assert extra_rows_after_abort <= 30, (
        f"too many rows leaked after abort: {extra_rows_after_abort}")


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
