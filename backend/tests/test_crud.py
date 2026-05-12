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


def test_mark_task_started_sets_pid_dir_and_status(db_session):
    api, _, _, _, cat = _seed_basics(db_session)
    t = crud.create_task_snapshot(db_session, cat.id, api.id, 10, 5, 1, 100, None, None)
    out = crud.mark_task_started(db_session, t.id, worker_pid=12345,
                                 output_dir="data/task-1")
    assert out.status == "running"
    assert out.worker_pid == 12345
    assert out.output_dir == "data/task-1"
    assert out.started_at is not None


def test_update_task_progress(db_session):
    api, _, _, _, cat = _seed_basics(db_session)
    t = crud.create_task_snapshot(db_session, cat.id, api.id, 100, 5, 1, 100, None, None)
    out = crud.update_task_progress(db_session, t.id, current=42)
    assert out.progress_current == 42


def test_set_and_finish_task_status(db_session):
    api, _, _, _, cat = _seed_basics(db_session)
    t = crud.create_task_snapshot(db_session, cat.id, api.id, 10, 5, 1, 100, None, None)
    out = crud.set_task_status(db_session, t.id, "aborted")
    assert out.status == "aborted"
    out = crud.mark_task_finished(db_session, t.id, "failed", error_msg="boom")
    assert out.status == "failed"
    assert out.finished_at is not None
    assert out.error_msg == "boom"


def test_wordlist_has_running_refs_via_tone_link(db_session):
    api, s_wl, t_wl, pt, cat = _seed_basics(db_session)
    task = crud.create_task_snapshot(db_session, cat.id, api.id, 10, 5, 1, 100, None, None)
    task.status = "running"; db_session.commit()
    assert crud.wordlist_has_running_refs(db_session, t_wl.id) is True


def test_wordlist_has_running_refs_returns_false_when_no_category_refs(db_session):
    standalone = crud.create_wordlist(
        db_session, WordListCreate(name="orphan", kind="other", items=["z"]))
    assert crud.wordlist_has_running_refs(db_session, standalone.id) is False


def test_set_task_worker_pid_updates_only_pid(db_session):
    api, _, _, _, cat = _seed_basics(db_session)
    t = crud.create_task_snapshot(db_session, cat.id, api.id, 10, 5, 1, 100, None, None)
    # Seed via mark_task_started with pid=0 (matches new spawn_worker flow).
    crud.mark_task_started(db_session, t.id, worker_pid=0,
                           output_dir="data/task-x")
    pre_status = t.status
    pre_output_dir = t.output_dir
    pre_started_at = t.started_at

    crud.set_task_worker_pid(db_session, t.id, 42)

    db_session.refresh(t)
    assert t.worker_pid == 42
    assert t.status == pre_status
    assert t.output_dir == pre_output_dir
    assert t.started_at == pre_started_at


def test_mark_task_started_noops_when_already_terminal(db_session):
    api, _, _, _, cat = _seed_basics(db_session)
    t = crud.create_task_snapshot(db_session, cat.id, api.id, 10, 5, 1, 100, None, None)
    # Fast child scenario: task reached a terminal status before parent's
    # late mark_task_started landed.
    crud.mark_task_finished(db_session, t.id, "succeeded")
    pre_finished_at = t.finished_at
    pre_output_dir = t.output_dir
    pre_worker_pid = t.worker_pid

    crud.mark_task_started(db_session, t.id, worker_pid=123,
                           output_dir="/tmp/x")

    db_session.refresh(t)
    assert t.status == "succeeded"
    assert t.worker_pid == pre_worker_pid
    assert t.output_dir == pre_output_dir
    assert t.finished_at == pre_finished_at

    evs = crud.recent_events(db_session, t.id, limit=50)
    warn_msgs = [e.message for e in evs if e.type == "warning"]
    assert any(("skipped" in m or "terminal" in m) for m in warn_msgs), (
        f"expected a warning event about skipped/terminal, got: {warn_msgs}")
