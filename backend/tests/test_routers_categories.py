def _seed_basics(client):
    wl_s = client.post("/api/wordlists", json={
        "name": "scn", "kind": "scenario", "items": ["a"]}).json()
    wl_t = client.post("/api/wordlists", json={
        "name": "tne", "kind": "tone", "items": ["x"]}).json()
    pt = client.post("/api/prompt-templates", json={
        "name": "P", "body": "hi {scenario} {tone}",
        "variables": ["scenario", "tone"]}).json()
    return wl_s, wl_t, pt


def test_category_crud_and_filter(client):
    wl_s, wl_t, pt = _seed_basics(client)

    r = client.post("/api/categories", json={
        "sample_type": "black", "name": "A.1.a", "description": "",
        "prompt_template_id": pt["id"],
        "scenario_list_id": wl_s["id"], "tone_list_id": wl_t["id"],
        "default_target_count": 100,
    })
    assert r.status_code == 201, r.text
    cid = r.json()["id"]

    # filter by sample_type
    items = client.get("/api/categories?sample_type=black").json()
    assert len(items) == 1 and items[0]["id"] == cid
    assert client.get("/api/categories?sample_type=gray").json() == []

    # update
    u = client.put(f"/api/categories/{cid}", json={"default_target_count": 200})
    assert u.status_code == 200
    assert u.json()["default_target_count"] == 200

    # detail endpoint expands template + wordlists
    d = client.get(f"/api/categories/{cid}").json()
    assert d["prompt_template_id"] == pt["id"]
    assert d["scenario_list_id"] == wl_s["id"]
    assert d["tone_list_id"] == wl_t["id"]

    # delete OK
    assert client.delete(f"/api/categories/{cid}").status_code == 204


def test_create_category_rejects_dangling_fks(client):
    r = client.post("/api/categories", json={
        "sample_type": "black", "name": "X", "description": "",
        "prompt_template_id": 999,
        "scenario_list_id": 999, "tone_list_id": 999,
        "default_target_count": 10,
    })
    # SQLite FK with foreign_keys=ON raises IntegrityError on insert
    assert r.status_code in (400, 409, 500)


def test_delete_category_blocked_by_running_task(client):
    import service.db as dbmod
    from service import models
    wl_s, wl_t, pt = _seed_basics(client)
    r = client.post("/api/categories", json={
        "sample_type": "black", "name": "B", "description": "",
        "prompt_template_id": pt["id"],
        "scenario_list_id": wl_s["id"], "tone_list_id": wl_t["id"],
        "default_target_count": 1,
    })
    cid = r.json()["id"]
    # Inject a running task referencing this category
    api = client.post("/api/api-configs", json={
        "name": "Q", "base_url": "x", "api_key": "k",
        "model_name": "m", "type": "raw"}).json()
    with dbmod.SessionLocal() as s:
        t = models.Task(
            category_id=cid, api_config_id=api["id"],
            snapshot_sample_type="black", snapshot_category_name="x",
            snapshot_prompt_body="x",
            snapshot_scenario_items_json="[]",
            snapshot_tone_items_json="[]",
            snapshot_api_base_url="x", snapshot_api_key="k",
            snapshot_model_name="m", snapshot_api_type="raw",
            target_count=1, batch_size=1, max_workers=1, max_per_file=100,
            status="running", progress_current=0, progress_total=1,
            created_at="t", output_dir="",
        )
        s.add(t); s.commit()
    assert client.delete(f"/api/categories/{cid}").status_code == 409
