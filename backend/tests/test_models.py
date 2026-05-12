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


def test_wordlist_name_is_unique(tmp_path):
    from sqlalchemy.exc import IntegrityError
    s = make_session(tmp_path)
    s.add(WordList(name="dup", kind="scenario", items_json="[]"))
    s.commit()
    s.add(WordList(name="dup", kind="tone", items_json="[]"))
    import pytest
    with pytest.raises(IntegrityError):
        s.commit()


def test_category_unique_per_sample_type_and_name(tmp_path):
    from sqlalchemy.exc import IntegrityError
    s = make_session(tmp_path)
    wl = WordList(name="w", kind="scenario", items_json="[]")
    pt = PromptTemplate(name="p", body="hi", variables_json="[]")
    s.add_all([wl, pt]); s.flush()

    def mk(sample_type, name):
        return Category(
            sample_type=sample_type, name=name, description="",
            prompt_template_id=pt.id, scenario_list_id=wl.id,
            tone_list_id=wl.id, default_target_count=0,
        )

    # Same name across different sample_types is allowed
    s.add_all([mk("black", "X"), mk("gray", "X")])
    s.commit()

    # Same (sample_type, name) collides
    s.add(mk("black", "X"))
    import pytest
    with pytest.raises(IntegrityError):
        s.commit()
