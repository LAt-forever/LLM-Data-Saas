def test_prompt_template_crud_and_validation(client):
    r = client.post("/api/prompt-templates", json={
        "name": "T1",
        "body": "hi {category} {scenario}",
        "variables": ["category", "scenario"],
    })
    assert r.status_code == 201, r.text
    tid = r.json()["id"]

    items = client.get("/api/prompt-templates").json()
    assert len(items) == 1 and items[0]["body"].startswith("hi ")

    # update with valid body+vars
    u = client.put(f"/api/prompt-templates/{tid}", json={
        "body": "x {tone}",
        "variables": ["tone"],
    })
    assert u.status_code == 200
    assert u.json()["variables"] == ["tone"]

    # update body w/ undeclared placeholder → 400
    bad = client.put(f"/api/prompt-templates/{tid}", json={
        "body": "x {tone} {unknown}",
        "variables": ["tone"],
    })
    assert bad.status_code == 400

    # delete
    assert client.delete(f"/api/prompt-templates/{tid}").status_code == 204


def test_prompt_template_create_rejects_invalid_body(client):
    r = client.post("/api/prompt-templates", json={
        "name": "T2",
        "body": "hi {a}",
        "variables": ["a", "b"],   # unused declared var
    })
    assert r.status_code == 400


def test_delete_prompt_template_blocked_by_running_task(client):
    import service.db as dbmod
    from service import models
    # Seed: template + wordlist + category + running task
    with dbmod.SessionLocal() as s:
        wl = models.WordList(name="w", kind="scenario",
                             items_json="[]", created_at="t", updated_at="t")
        pt = models.PromptTemplate(name="p", body="hi",
                                   variables_json="[]",
                                   created_at="t", updated_at="t")
        s.add_all([wl, pt]); s.flush()
        cat = models.Category(
            sample_type="black", name="X", description="",
            prompt_template_id=pt.id, scenario_list_id=wl.id,
            tone_list_id=wl.id, default_target_count=1,
            created_at="t", updated_at="t",
        )
        api = models.ApiConfig(name="A", base_url="x", api_key="k",
                               model_name="m", type="raw",
                               created_at="t", updated_at="t")
        s.add_all([cat, api]); s.flush()
        t = models.Task(
            category_id=cat.id, api_config_id=api.id,
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
        pt_id = pt.id
    r = client.delete(f"/api/prompt-templates/{pt_id}")
    assert r.status_code == 409
