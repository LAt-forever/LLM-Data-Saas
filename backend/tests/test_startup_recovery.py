import sys

from fastapi.testclient import TestClient


def test_startup_recovers_running_tasks_with_dead_pids(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "app.db"))

    # First lifecycle: write a running-task row with a fake pid
    for m in [k for k in list(sys.modules) if k == "service" or k.startswith("service.")]:
        sys.modules.pop(m, None)
    import service.config  # noqa: F401
    import service.db as dbmod
    import service.models  # noqa: F401
    dbmod.init_engine()
    dbmod.Base.metadata.create_all(dbmod.engine)

    from service import crud, models
    from service.schemas import (
        ApiConfigCreate, WordListCreate, PromptTemplateCreate, CategoryCreate
    )
    with dbmod.SessionLocal() as s:
        api = crud.create_api_config(s, ApiConfigCreate(
            name="A", base_url="x", api_key="k",
            model_name="m", type="openai"))
        wl = crud.create_wordlist(s, WordListCreate(
            name="w", kind="scenario", items=["a"]))
        wl2 = crud.create_wordlist(s, WordListCreate(
            name="w2", kind="tone", items=["b"]))
        pt = crud.create_prompt_template(s, PromptTemplateCreate(
            name="p", body="x", variables=[]))
        cat = crud.create_category(s, CategoryCreate(
            sample_type="black", name="C", description="",
            prompt_template_id=pt.id, scenario_list_id=wl.id,
            tone_list_id=wl2.id, default_target_count=1))
        t = crud.create_task_snapshot(s, cat.id, api.id, 1, 1, 1, 50, None, None)
        crud.mark_task_started(s, t.id, worker_pid=999_999_999,
                               output_dir=str(tmp_path / "x"))
        task_id = t.id

    # Restart the app (fresh import) → startup hook runs recovery
    for m in [k for k in list(sys.modules) if k == "service" or k.startswith("service.")]:
        sys.modules.pop(m, None)
    import service.config  # noqa: F401
    import service.db as dbmod2
    import service.models  # noqa: F401
    import service.main as mainmod

    with TestClient(mainmod.app) as c:
        r = c.get(f"/api/tasks/{task_id}")
        assert r.status_code == 200
        assert r.json()["status"] == "failed"
        assert "lost" in r.json()["error_msg"].lower() or "orphan" in r.json()["error_msg"].lower()
