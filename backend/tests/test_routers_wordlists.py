def test_wordlist_crud_and_filter(client):
    a = client.post("/api/wordlists", json={
        "name": "scn", "kind": "scenario", "items": ["a", "b"]}).json()
    client.post("/api/wordlists", json={
        "name": "tne", "kind": "tone", "items": ["t1"]})
    r = client.get("/api/wordlists?kind=scenario").json()
    assert len(r) == 1 and r[0]["items"] == ["a", "b"]
    u = client.put(f"/api/wordlists/{a['id']}", json={"items": ["x"]}).json()
    assert u["items"] == ["x"]
    assert client.delete(f"/api/wordlists/{a['id']}").status_code == 204
