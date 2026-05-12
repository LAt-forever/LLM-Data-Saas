# backend/tests/test_worker_resume.py
import csv
import sys

from service.schemas import (
    ApiConfigCreate, WordListCreate, PromptTemplateCreate, CategoryCreate
)


def test_worker_run_resumes_from_existing_csv(tmp_path, monkeypatch):
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

    from service import crud, models, worker_run

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
            tone_list_id=wl_t.id, default_target_count=10))
        task = crud.create_task_snapshot(s, cat.id, api.id,
            target_count=10, batch_size=2, max_workers=1, max_per_file=100,
            created_by_label=None, resume_from_task_id=None)
        out_dir = tmp_path / f"data/task-{task.id}"
        out_dir.mkdir(parents=True, exist_ok=True)
        # Pre-existing CSV with 4 rows already
        with open(out_dir / f"task_{task.id}_part1.csv", "w",
                  newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["评测题", "风险类型"])
            for i in range(4):
                w.writerow([f"old line {i}", "C"])
        crud.mark_task_started(s, task.id, worker_pid=0,
                               output_dir=str(out_dir))
        task_id = task.id

    worker_run.run_task(task_id, mock_llm=True)

    with dbmod.SessionLocal() as s:
        t = s.get(models.Task, task_id)
        assert t.status == "succeeded"
        assert t.progress_current == 10

    rows = []
    for p in sorted((tmp_path / f"data/task-{task_id}").glob("*.csv")):
        with open(p, "r", encoding="utf-8-sig") as f:
            r = csv.reader(f)
            next(r)  # header
            rows.extend(list(r))
    assert len(rows) == 10
    assert rows[0][0] == "old line 0"   # original 4 are preserved
    assert rows[3][0] == "old line 3"
