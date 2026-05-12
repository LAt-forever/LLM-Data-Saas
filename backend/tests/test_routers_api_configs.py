def test_create_list_and_mask_api_config(client):
    r = client.post("/api/api-configs", json={
        "name": "Q", "base_url": "http://x", "api_key": "sk-1234567890ab",
        "model_name": "m", "type": "raw"})
    assert r.status_code == 201, r.text
    items = client.get("/api/api-configs").json()
    assert len(items) == 1
    assert "api_key_masked" in items[0]
    assert "1234" not in items[0]["api_key_masked"]
    assert "api_key" not in items[0]


def test_reveal_returns_plain_key(client):
    cid = client.post("/api/api-configs", json={
        "name": "Q", "base_url": "http://x", "api_key": "sk-1234567890ab",
        "model_name": "m", "type": "raw"}).json()["id"]
    r = client.get(f"/api/api-configs/{cid}/reveal")
    assert r.status_code == 200
    assert r.json()["api_key"] == "sk-1234567890ab"
    assert r.headers.get("cache-control") == "no-store"


def test_delete_blocked_when_running_task_refs(client):
    cid = client.post("/api/api-configs", json={
        "name": "Q", "base_url": "http://x", "api_key": "k",
        "model_name": "m", "type": "raw"}).json()["id"]
    import service.db as dbmod
    from service import models
    with dbmod.SessionLocal() as s:
        wl = models.WordList(name="w", kind="scenario",
                             items_json="[]", created_at="t", updated_at="t")
        pt = models.PromptTemplate(name="p", body="hi",
                                   variables_json="[]",
                                   created_at="t", updated_at="t")
        s.add_all([wl, pt])
        s.flush()
        cat = models.Category(
            sample_type="black", name="X", description="",
            prompt_template_id=pt.id, scenario_list_id=wl.id,
            tone_list_id=wl.id, default_target_count=1,
            created_at="t", updated_at="t",
        )
        s.add(cat)
        s.flush()
        t = models.Task(
            category_id=cat.id, api_config_id=cid,
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
        s.add(t)
        s.commit()
    r = client.delete(f"/api/api-configs/{cid}")
    assert r.status_code == 409
