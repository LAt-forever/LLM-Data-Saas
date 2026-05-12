# backend/tests/test_supervisor.py
import os
import signal
import sys
import time

from service.schemas import (
    ApiConfigCreate, WordListCreate, PromptTemplateCreate, CategoryCreate
)


def _fresh_env(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "app.db"))
    for m in [k for k in list(sys.modules) if k == "service" or k.startswith("service.")]:
        sys.modules.pop(m, None)
    import service.config  # noqa: F401
    import service.db as dbmod
    import service.models  # noqa: F401
    dbmod.init_engine()
    dbmod.Base.metadata.create_all(dbmod.engine)
    return dbmod


def _seed_pending_task(dbmod):
    from service import crud
    with dbmod.SessionLocal() as s:
        api = crud.create_api_config(s, ApiConfigCreate(
            name="A", base_url="x", api_key="k",
            model_name="m", type="openai"))
        wl_s = crud.create_wordlist(s, WordListCreate(
            name="scn", kind="scenario", items=["a"]))
        wl_t = crud.create_wordlist(s, WordListCreate(
            name="tne", kind="tone", items=["b"]))
        pt = crud.create_prompt_template(s, PromptTemplateCreate(
            name="p", body="x {category} {scenario} {tone} {batch_size}",
            variables=["category", "scenario", "tone", "batch_size"]))
        cat = crud.create_category(s, CategoryCreate(
            sample_type="black", name="C", description="",
            prompt_template_id=pt.id, scenario_list_id=wl_s.id,
            tone_list_id=wl_t.id, default_target_count=5))
        task = crud.create_task_snapshot(s, cat.id, api.id,
            target_count=5, batch_size=2, max_workers=1, max_per_file=50,
            created_by_label=None, resume_from_task_id=None)
        return task.id


def test_spawn_worker_runs_subprocess_end_to_end(tmp_path, monkeypatch):
    dbmod = _fresh_env(tmp_path, monkeypatch)
    task_id = _seed_pending_task(dbmod)
    from service import supervisor, models

    pid = supervisor.spawn_worker(task_id, mock_llm=True)
    assert pid > 0

    # Wait for subprocess to finish
    for _ in range(120):
        if not supervisor.is_pid_alive(pid):
            break
        time.sleep(0.5)
    else:
        os.kill(pid, signal.SIGKILL)
        raise AssertionError("worker did not finish in 60s")

    with dbmod.SessionLocal() as s:
        t = s.get(models.Task, task_id)
        assert t.status == "succeeded"
        assert t.progress_current == 5


def test_is_pid_alive_false_for_nonexistent(tmp_path, monkeypatch):
    _fresh_env(tmp_path, monkeypatch)
    from service import supervisor
    assert supervisor.is_pid_alive(999_999_999) is False


def test_recover_orphans_marks_dead_pid_as_failed(tmp_path, monkeypatch):
    dbmod = _fresh_env(tmp_path, monkeypatch)
    task_id = _seed_pending_task(dbmod)
    from service import crud, models, supervisor

    with dbmod.SessionLocal() as s:
        crud.mark_task_started(s, task_id,
                               worker_pid=999_999_999,
                               output_dir=str(tmp_path / "x"))

    n = supervisor.recover_orphaned_running()
    assert n == 1

    with dbmod.SessionLocal() as s:
        t = s.get(models.Task, task_id)
        assert t.status == "failed"
        assert "lost" in (t.error_msg or "").lower() or "orphan" in (t.error_msg or "").lower()


def test_terminate_worker_sends_signals(tmp_path, monkeypatch):
    _fresh_env(tmp_path, monkeypatch)
    from service import supervisor

    # Spawn a long-running sleep, then terminate
    import subprocess
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        supervisor.terminate_worker(proc.pid, grace_seconds=1)
        proc.wait(timeout=5)
        assert proc.returncode is not None
    finally:
        if proc.poll() is None:
            proc.kill()
