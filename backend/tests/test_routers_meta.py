# backend/tests/test_routers_meta.py
def test_sample_types_empty_db(client):
    r = client.get("/api/sample-types")
    assert r.status_code == 200
    body = r.json()
    types = {item["sample_type"]: item for item in body}
    assert types.keys() == {"black", "gray", "white"}
    for v in body:
        assert v["category_count"] == 0


def test_sample_types_with_categories(client):
    wl = client.post("/api/wordlists", json={
        "name": "w", "kind": "scenario", "items": ["a"]}).json()
    wl2 = client.post("/api/wordlists", json={
        "name": "w2", "kind": "tone", "items": ["b"]}).json()
    pt = client.post("/api/prompt-templates", json={
        "name": "p", "body": "hi {x}", "variables": ["x"]}).json()

    for st, name in [("black", "B1"), ("black", "B2"), ("gray", "G1")]:
        r = client.post("/api/categories", json={
            "sample_type": st, "name": name, "description": "",
            "prompt_template_id": pt["id"],
            "scenario_list_id": wl["id"], "tone_list_id": wl2["id"],
            "default_target_count": 10,
        })
        assert r.status_code == 201, r.text

    body = client.get("/api/sample-types").json()
    types = {item["sample_type"]: item for item in body}
    assert types["black"]["category_count"] == 2
    assert types["gray"]["category_count"] == 1
    assert types["white"]["category_count"] == 0
