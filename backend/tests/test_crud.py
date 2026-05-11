import json
from service import crud
from service.schemas import (
    ApiConfigCreate, WordListCreate, PromptTemplateCreate, CategoryCreate
)


def _seed_basics(db_session):
    api = crud.create_api_config(
        db_session, ApiConfigCreate(name="a", base_url="http://x", api_key="k",
                                    model_name="m", type="openai"))
    s_wl = crud.create_wordlist(
        db_session, WordListCreate(name="s", kind="scenario", items=["a"]))
    t_wl = crud.create_wordlist(
        db_session, WordListCreate(name="t", kind="tone", items=["x"]))
    pt = crud.create_prompt_template(
        db_session, PromptTemplateCreate(
            name="p", body="hi {scenario} {tone}", variables=["scenario", "tone"]))
    cat = crud.create_category(
        db_session, CategoryCreate(
            sample_type="black", name="A.1.a", description="",
            prompt_template_id=pt.id, scenario_list_id=s_wl.id,
            tone_list_id=t_wl.id, default_target_count=10))
    return api, s_wl, t_wl, pt, cat


def test_create_and_list_api_configs(db_session):
    cfg = crud.create_api_config(
        db_session, ApiConfigCreate(name="a", base_url="http://x", api_key="k",
                                    model_name="m", type="raw"))
    items = crud.list_api_configs(db_session)
    assert len(items) == 1 and items[0].id == cfg.id


def test_delete_category_blocked_when_running_task_refs(db_session):
    api, s_wl, t_wl, pt, cat = _seed_basics(db_session)
    task = crud.create_task_snapshot(db_session, cat.id, api.id,
        target_count=10, batch_size=5, max_workers=1, max_per_file=100,
        created_by_label=None, resume_from_task_id=None)
    task.status = "running"
    db_session.commit()
    assert crud.category_has_running_refs(db_session, cat.id) is True


def test_list_tasks_filters_by_status(db_session):
    api, s_wl, t_wl, pt, cat = _seed_basics(db_session)
    a = crud.create_task_snapshot(db_session, cat.id, api.id, 10, 5, 1, 100, None, None)
    a.status = "running"; db_session.commit()
    b = crud.create_task_snapshot(db_session, cat.id, api.id, 10, 5, 1, 100, None, None)
    b.status = "succeeded"; db_session.commit()
    only_running = crud.list_tasks(db_session, status="running")
    assert [t.id for t in only_running] == [a.id]
