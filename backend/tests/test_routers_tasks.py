import csv
import json
import time


def _seed_full(client):
    wl_s = client.post("/api/wordlists", json={
        "name": "scn", "kind": "scenario", "items": ["a"]}).json()
    wl_t = client.post("/api/wordlists", json={
        "name": "tne", "kind": "tone", "items": ["b"]}).json()
    pt = client.post("/api/prompt-templates", json={
        "name": "P", "body": "x {category} {scenario} {tone} {batch_size}",
        "variables": ["category", "scenario", "tone", "batch_size"]}).json()
    cat = client.post("/api/categories", json={
        "sample_type": "black", "name": "C", "description": "",
        "prompt_template_id": pt["id"],
        "scenario_list_id": wl_s["id"], "tone_list_id": wl_t["id"],
        "default_target_count": 5,
    }).json()
    api = client.post("/api/api-configs", json={
        "name": "A", "base_url": "x", "api_key": "k",
        "model_name": "m", "type": "openai"}).json()
    return cat, api


def test_create_task_spawns_worker_and_runs_to_completion(client, monkeypatch):
    # Force mock_llm mode for task creation
    from service.routers import tasks as tasks_router
    real_spawn = tasks_router.supervisor.spawn_worker
    monkeypatch.setattr(tasks_router.supervisor, "spawn_worker",
                        lambda tid, mock_llm=False: real_spawn(tid, mock_llm=True))

    cat, api = _seed_full(client)
    r = client.post("/api/tasks", json={
        "category_id": cat["id"], "api_config_id": api["id"],
        "target_count": 5, "batch_size": 2, "max_workers": 1,
        "max_per_file": 50,
    })
    assert r.status_code == 201, r.text
    task_id = r.json()["id"]

    # Poll until finished (mock_llm is fast)
    for _ in range(60):
        d = client.get(f"/api/tasks/{task_id}").json()
        if d["status"] in ("succeeded", "failed"):
            break
        time.sleep(0.5)

    detail = client.get(f"/api/tasks/{task_id}").json()
    assert detail["status"] == "succeeded"
    assert detail["progress_current"] == 5
    assert len(detail["recent_events"]) >= 2


def test_list_tasks_filters(client, monkeypatch):
    from service.routers import tasks as tasks_router
    real_spawn = tasks_router.supervisor.spawn_worker
    monkeypatch.setattr(tasks_router.supervisor, "spawn_worker",
                        lambda tid, mock_llm=False: real_spawn(tid, mock_llm=True))
    cat, api = _seed_full(client)
    payload = {"category_id": cat["id"], "api_config_id": api["id"],
               "target_count": 2, "batch_size": 1,
               "max_workers": 1, "max_per_file": 10}
    t1 = client.post("/api/tasks", json=payload).json()["id"]
    for _ in range(40):
        s = client.get(f"/api/tasks/{t1}").json()["status"]
        if s in ("succeeded", "failed"): break
        time.sleep(0.3)

    # status filter
    succ = client.get("/api/tasks?status=succeeded").json()
    assert any(t["id"] == t1 for t in succ)
    failed = client.get("/api/tasks?status=failed").json()
    assert all(t["id"] != t1 for t in failed)


def test_preview_returns_first_n_rows(client, tmp_path, monkeypatch):
    from service.routers import tasks as tasks_router
    real_spawn = tasks_router.supervisor.spawn_worker
    monkeypatch.setattr(tasks_router.supervisor, "spawn_worker",
                        lambda tid, mock_llm=False: real_spawn(tid, mock_llm=True))
    cat, api = _seed_full(client)
    tid = client.post("/api/tasks", json={
        "category_id": cat["id"], "api_config_id": api["id"],
        "target_count": 4, "batch_size": 2, "max_workers": 1,
        "max_per_file": 50,
    }).json()["id"]
    for _ in range(40):
        s = client.get(f"/api/tasks/{tid}").json()["status"]
        if s in ("succeeded", "failed"): break
        time.sleep(0.3)

    r = client.get(f"/api/tasks/{tid}/preview")
    assert r.status_code == 200
    body = r.json()
    assert "header" in body and "rows" in body
    assert len(body["rows"]) <= 200
    assert len(body["rows"]) == 4


def test_download_returns_csv_stream(client, monkeypatch):
    from service.routers import tasks as tasks_router
    real_spawn = tasks_router.supervisor.spawn_worker
    monkeypatch.setattr(tasks_router.supervisor, "spawn_worker",
                        lambda tid, mock_llm=False: real_spawn(tid, mock_llm=True))
    cat, api = _seed_full(client)
    tid = client.post("/api/tasks", json={
        "category_id": cat["id"], "api_config_id": api["id"],
        "target_count": 3, "batch_size": 1, "max_workers": 1,
        "max_per_file": 50,
    }).json()["id"]
    for _ in range(40):
        s = client.get(f"/api/tasks/{tid}").json()["status"]
        if s in ("succeeded", "failed"): break
        time.sleep(0.3)
    r = client.get(f"/api/tasks/{tid}/download")
    assert r.status_code == 200
    ct = r.headers["content-type"]
    assert ct.startswith("text/csv") or ct.startswith("application/")
    assert "attachment" in r.headers.get("content-disposition", "")


def test_abort_running_task(client, monkeypatch):
    """Abort a long-running task. Use a high target_count + mock so worker
    has to poll many batches before finishing — gives us time to abort."""
    from service.routers import tasks as tasks_router
    real_spawn = tasks_router.supervisor.spawn_worker
    monkeypatch.setattr(tasks_router.supervisor, "spawn_worker",
                        lambda tid, mock_llm=False: real_spawn(tid, mock_llm=True))
    cat, api = _seed_full(client)
    tid = client.post("/api/tasks", json={
        "category_id": cat["id"], "api_config_id": api["id"],
        "target_count": 100_000, "batch_size": 2, "max_workers": 1,
        "max_per_file": 50,
    }).json()["id"]
    time.sleep(0.5)
    r = client.post(f"/api/tasks/{tid}/abort")
    assert r.status_code == 200
    for _ in range(60):
        s = client.get(f"/api/tasks/{tid}").json()["status"]
        if s == "aborted": break
        time.sleep(0.3)
    assert client.get(f"/api/tasks/{tid}").json()["status"] == "aborted"
