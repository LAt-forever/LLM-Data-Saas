import json
from datetime import datetime, timezone

from service.db import Base, create_engine_for_path
from service.models import (
    ApiConfig, WordList, PromptTemplate, Category, Task, TaskEvent
)
from sqlalchemy.orm import sessionmaker


def make_session(tmp_path):
    eng = create_engine_for_path(tmp_path / "m.db")
    Base.metadata.create_all(eng)
    return sessionmaker(bind=eng, expire_on_commit=False)()


def test_all_tables_created(tmp_path):
    s = make_session(tmp_path)
    api = ApiConfig(name="x", base_url="http://x", api_key="k", model_name="m", type="raw")
    wl = WordList(name="s", kind="scenario", items_json=json.dumps(["a"]))
    pt = PromptTemplate(name="p", body="hi {scenario}", variables_json=json.dumps(["scenario"]))
    s.add_all([api, wl, pt])
    s.flush()
    cat = Category(
        sample_type="black", name="A.1.a", description="",
        prompt_template_id=pt.id, scenario_list_id=wl.id, tone_list_id=wl.id,
        default_target_count=100,
    )
    s.add(cat); s.flush()
    t = Task(
        category_id=cat.id, api_config_id=api.id,
        snapshot_sample_type="black", snapshot_category_name="A.1.a",
        snapshot_prompt_body="hi {scenario}",
        snapshot_scenario_items_json=json.dumps(["a"]),
        snapshot_tone_items_json=json.dumps(["b"]),
        snapshot_api_base_url="http://x", snapshot_api_key="k",
        snapshot_model_name="m", snapshot_api_type="raw",
        target_count=100, batch_size=20, max_workers=2, max_per_file=50000,
        status="pending", progress_current=0, progress_total=100,
        output_dir="data/task-1", created_at=datetime.now(timezone.utc).isoformat(),
    )
    s.add(t); s.flush()
    ev = TaskEvent(task_id=t.id, ts=datetime.now(timezone.utc).isoformat(),
                   type="started", message="ok")
    s.add(ev); s.commit()

    assert s.query(Task).count() == 1
    assert s.query(TaskEvent).count() == 1
