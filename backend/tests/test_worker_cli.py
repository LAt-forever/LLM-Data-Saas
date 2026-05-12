# backend/tests/test_worker_cli.py
import subprocess
import sys

from service.schemas import (
    ApiConfigCreate, WordListCreate, PromptTemplateCreate, CategoryCreate
)


def test_worker_cli_runs_task_with_mock(tmp_path, monkeypatch):
    """End-to-end: spawn `python -m service.worker --task-id N --mock-llm`
    as a real subprocess and verify the task completes."""
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
        out_dir = tmp_path / f"data/task-{task.id}"
        out_dir.mkdir(parents=True, exist_ok=True)
        crud.mark_task_started(s, task.id, worker_pid=0, output_dir=str(out_dir))
        task_id = task.id

    import os
    env = {**os.environ,
           "DATA_DIR": str(tmp_path / "data"),
           "LOG_DIR": str(tmp_path / "logs"),
           "DB_PATH": str(tmp_path / "app.db")}
    proc = subprocess.run(
        [sys.executable, "-m", "service.worker",
         "--task-id", str(task_id), "--mock-llm"],
        env=env, capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode == 0, proc.stderr

    from service import models
    with dbmod.SessionLocal() as s:
        t = s.get(models.Task, task_id)
        assert t.status == "succeeded"
        assert t.progress_current == 5
