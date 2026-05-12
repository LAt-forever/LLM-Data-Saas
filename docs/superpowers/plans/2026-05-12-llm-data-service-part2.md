# LLM 样本数据生产服务 实现计划 · Part 2 (Tasks 14-28)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 续 Part 1,补完后端剩余功能:Prompt 模板/分类/任务三组 CRUD,任务生命周期(LLM 客户端 + worker + supervisor + 启动恢复),实时进度推送 (SSE),静态文件挂载,API 配置连通性测试,以及把 `llm-data-create/` 现有脚本一次性灌成种子数据。完成后后端可独立运行,通过 HTTP/SSE 提供前端所需的全部接口。

**Architecture:** 沿用 Part 1 的总体架构 — FastAPI 单进程 + SQLite WAL + 每任务一个 Python 子进程 Worker。Worker 只写 DB,API 进程内置 supervisor 监督子进程并通过 SSE 把 TaskEvent 表的变更广播给前端。每个 Worker 子进程独立目录 `data/task-{id}/`,通过 Task 行的 snapshot 字段拿到运行所需的全部配置。

**Tech Stack:** Python 3.11 / FastAPI 0.115+ / SQLAlchemy 2 / SQLite WAL / sse-starlette / openai SDK / requests / pytest

**Spec:** `docs/superpowers/specs/2026-05-11-llm-data-service-design.md`
**Part 1 plan:** `docs/superpowers/plans/2026-05-11-llm-data-service.md`

**Branch base:** `main` (Part 1 + cleanup 已合并)。开新分支 `feat/backend-part2`。

---

## 阶段总览

- **M. 配置 REST 收尾** (Task 14-17):PromptTemplate / Category / api-configs `/test` / `/api/sample-types`
- **N. Worker 核心** (Task 18-21):LLM 客户端 / worker_run / worker CLI / mock-LLM 端到端
- **O. 任务编排 (Supervisor)** (Task 22-25):supervisor、tasks router、abort、resume + 启动恢复
- **P. 实时推送 (SSE)** (Task 26):tasks_stream router + sse 模块
- **Q. 静态文件 & 数据迁移** (Task 27-28):前端静态托管 + seed_from_legacy

每个 task 是一次完整 TDD:写测试 → 跑测试看 fail → 写实现 → 跑测试看 pass → commit。每个 task = ONE commit。

执行约定:
- 工作目录 `/Users/lanhezheng/llm-data-service`
- 后端代码在 `backend/`,Python 命令前 `cd backend &&` 或用 `.venv/bin/python -m ...`
- 跑测试 `.venv/bin/python -m pytest tests/...`
- 分支 `feat/backend-part2`,所有 commit 落在这个分支

---

## M. 配置 REST 收尾

### Task 14: PromptTemplate 路由

**Files:**
- Create: `backend/service/routers/prompt_templates.py`
- Modify: `backend/service/main.py` (register router)
- Create: `backend/tests/test_routers_prompt_templates.py`

- [ ] **Step 1: 写测试**

```python
# backend/tests/test_routers_prompt_templates.py
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
```

- [ ] **Step 2: 跑测试,确认失败**

Run: `cd backend && .venv/bin/python -m pytest tests/test_routers_prompt_templates.py -v`
Expected: 404 (路由未注册)

- [ ] **Step 3: 实现 routers/prompt_templates.py**

```python
# backend/service/routers/prompt_templates.py
import json
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from service import crud
from service.deps import get_db
from service.prompt_render import validate_template, PromptValidationError
from service.schemas import (
    PromptTemplateCreate, PromptTemplateUpdate, PromptTemplateOut
)

router = APIRouter(prefix="/api/prompt-templates", tags=["prompt-templates"])


def _to_out(obj) -> PromptTemplateOut:
    return PromptTemplateOut(
        id=obj.id, name=obj.name, body=obj.body,
        variables=json.loads(obj.variables_json),
        created_at=obj.created_at, updated_at=obj.updated_at,
    )


@router.get("")
def list_(db: Session = Depends(get_db)) -> list[PromptTemplateOut]:
    return [_to_out(o) for o in crud.list_prompt_templates(db)]


@router.post("", status_code=status.HTTP_201_CREATED)
def create(payload: PromptTemplateCreate,
           db: Session = Depends(get_db)) -> PromptTemplateOut:
    try:
        validate_template(payload.body, payload.variables)
    except PromptValidationError as e:
        raise HTTPException(400, str(e))
    obj = crud.create_prompt_template(db, payload)
    return _to_out(obj)


@router.put("/{id_}")
def update(id_: int, payload: PromptTemplateUpdate,
           db: Session = Depends(get_db)) -> PromptTemplateOut:
    obj = crud.get_prompt_template(db, id_)
    if obj is None:
        raise HTTPException(404, "not found")
    # Resolve final body+variables (use payload if provided, else existing)
    new_body = payload.body if payload.body is not None else obj.body
    new_vars = (payload.variables if payload.variables is not None
                else json.loads(obj.variables_json))
    try:
        validate_template(new_body, new_vars)
    except PromptValidationError as e:
        raise HTTPException(400, str(e))
    return _to_out(crud.update_prompt_template(db, obj, payload))


@router.delete("/{id_}", status_code=status.HTTP_204_NO_CONTENT)
def delete(id_: int, db: Session = Depends(get_db)) -> Response:
    obj = crud.get_prompt_template(db, id_)
    if obj is None:
        raise HTTPException(404, "not found")
    if crud.prompt_template_has_running_refs(db, id_):
        raise HTTPException(409, "template is referenced by a running task")
    crud.delete_prompt_template(db, obj)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

- [ ] **Step 4: 注册路由到 main.py**

In `backend/service/main.py`, after `from service.routers import wordlists ...` add:

```python
from service.routers import prompt_templates as prompt_templates_router
```

And after `app.include_router(wordlists_router.router)`:

```python
app.include_router(prompt_templates_router.router)
```

- [ ] **Step 5: 跑测试,确认通过**

Run: `cd backend && .venv/bin/python -m pytest tests/test_routers_prompt_templates.py -v`
Expected: 3 passed

- [ ] **Step 6: 跑全套确认无回归**

Run: `cd backend && .venv/bin/python -m pytest tests/ -v 2>&1 | tail -5`
Expected: 43 passed (40 existing + 3 new)

- [ ] **Step 7: Commit**

```bash
git add backend/service/routers/prompt_templates.py backend/service/main.py backend/tests/test_routers_prompt_templates.py
git commit -m "feat(backend): /api/prompt-templates CRUD with placeholder validation"
```

---

### Task 15: Category 路由

**Files:**
- Create: `backend/service/routers/categories.py`
- Modify: `backend/service/main.py` (register router)
- Create: `backend/tests/test_routers_categories.py`

- [ ] **Step 1: 写测试**

```python
# backend/tests/test_routers_categories.py
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
```

- [ ] **Step 2: 跑测试,确认失败**

Run: `cd backend && .venv/bin/python -m pytest tests/test_routers_categories.py -v`
Expected: 404

- [ ] **Step 3: 实现 routers/categories.py**

```python
# backend/service/routers/categories.py
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from service import crud
from service.deps import get_db
from service.schemas import CategoryCreate, CategoryUpdate, CategoryOut

router = APIRouter(prefix="/api/categories", tags=["categories"])


def _to_out(obj) -> CategoryOut:
    return CategoryOut(
        id=obj.id, sample_type=obj.sample_type, name=obj.name,
        description=obj.description,
        prompt_template_id=obj.prompt_template_id,
        scenario_list_id=obj.scenario_list_id,
        tone_list_id=obj.tone_list_id,
        default_target_count=obj.default_target_count,
        created_at=obj.created_at, updated_at=obj.updated_at,
    )


@router.get("")
def list_(sample_type: str | None = None,
          db: Session = Depends(get_db)) -> list[CategoryOut]:
    return [_to_out(o) for o in crud.list_categories(db, sample_type=sample_type)]


@router.get("/{id_}")
def get(id_: int, db: Session = Depends(get_db)) -> CategoryOut:
    obj = crud.get_category(db, id_)
    if obj is None:
        raise HTTPException(404, "not found")
    return _to_out(obj)


@router.post("", status_code=status.HTTP_201_CREATED)
def create(payload: CategoryCreate,
           db: Session = Depends(get_db)) -> CategoryOut:
    try:
        obj = crud.create_category(db, payload)
    except IntegrityError as e:
        raise HTTPException(400, f"foreign key violation: {e.orig}")
    return _to_out(obj)


@router.put("/{id_}")
def update(id_: int, payload: CategoryUpdate,
           db: Session = Depends(get_db)) -> CategoryOut:
    obj = crud.get_category(db, id_)
    if obj is None:
        raise HTTPException(404, "not found")
    return _to_out(crud.update_category(db, obj, payload))


@router.delete("/{id_}", status_code=status.HTTP_204_NO_CONTENT)
def delete(id_: int, db: Session = Depends(get_db)) -> Response:
    obj = crud.get_category(db, id_)
    if obj is None:
        raise HTTPException(404, "not found")
    if crud.category_has_running_refs(db, id_):
        raise HTTPException(409, "category is referenced by a running task")
    crud.delete_category(db, obj)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

- [ ] **Step 4: 注册路由**

In `backend/service/main.py` add:
```python
from service.routers import categories as categories_router
```
and:
```python
app.include_router(categories_router.router)
```

- [ ] **Step 5: 跑测试**

Run: `cd backend && .venv/bin/python -m pytest tests/test_routers_categories.py -v`
Expected: 3 passed

- [ ] **Step 6: 跑全套**

Run: `cd backend && .venv/bin/python -m pytest tests/ 2>&1 | tail -3`
Expected: 46 passed

- [ ] **Step 7: Commit**

```bash
git add backend/service/routers/categories.py backend/service/main.py backend/tests/test_routers_categories.py
git commit -m "feat(backend): /api/categories CRUD with sample_type filter"
```

---

### Task 16: api-configs `/test` 连通性端点

**Files:**
- Modify: `backend/service/routers/api_configs.py`
- Create: `backend/tests/test_routers_api_config_test.py`

- [ ] **Step 1: 写测试**

```python
# backend/tests/test_routers_api_config_test.py
import json

import httpx
import pytest


def test_api_config_test_endpoint_success(client, monkeypatch):
    """Mock the LLM call to return a successful response."""
    cid = client.post("/api/api-configs", json={
        "name": "Q", "base_url": "http://example.com",
        "api_key": "sk-test", "model_name": "m", "type": "raw"}).json()["id"]

    # Patch the underlying helper in routers.api_configs that does the HTTP call
    from service.routers import api_configs as mod

    def fake_ping(base_url, api_key, model_name, api_type):
        return {"ok": True, "latency_ms": 42, "sample_text": "hello"}

    monkeypatch.setattr(mod, "_ping_llm", fake_ping)

    r = client.post(f"/api/api-configs/{cid}/test")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "latency_ms" in body


def test_api_config_test_endpoint_failure(client, monkeypatch):
    cid = client.post("/api/api-configs", json={
        "name": "Q", "base_url": "http://example.com",
        "api_key": "sk-test", "model_name": "m", "type": "raw"}).json()["id"]

    from service.routers import api_configs as mod

    def fake_ping(*a, **kw):
        return {"ok": False, "error": "connect timeout"}

    monkeypatch.setattr(mod, "_ping_llm", fake_ping)

    r = client.post(f"/api/api-configs/{cid}/test")
    assert r.status_code == 200      # endpoint itself returns 200 with body
    body = r.json()
    assert body["ok"] is False
    assert "error" in body
```

- [ ] **Step 2: 跑测试,确认失败**

Run: `cd backend && .venv/bin/python -m pytest tests/test_routers_api_config_test.py -v`
Expected: 404 (endpoint not yet present)

- [ ] **Step 3: 修改 routers/api_configs.py 加 /test 端点**

Add at the bottom of `backend/service/routers/api_configs.py`:

```python
import time

import requests
from openai import OpenAI


def _ping_llm(base_url: str, api_key: str, model_name: str, api_type: str) -> dict:
    """Send a minimal request to verify the endpoint is reachable.
    Returns {ok, latency_ms, sample_text} on success or {ok: False, error}.
    Kept as a module-level function so tests can monkeypatch it."""
    t0 = time.monotonic()
    try:
        if api_type == "openai":
            client = OpenAI(api_key=api_key, base_url=base_url, timeout=15)
            rsp = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=4,
            )
            sample = (rsp.choices[0].message.content or "")[:50]
        else:  # raw
            rsp = requests.post(
                f"{base_url.rstrip('/')}/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}",
                         "Content-Type": "application/json"},
                json={"model": model_name, "stream": False,
                      "messages": [{"role": "user", "content": "ping"}]},
                timeout=15,
            )
            rsp.raise_for_status()
            sample = (rsp.json()["choices"][0]["message"]["content"] or "")[:50]
        latency_ms = int((time.monotonic() - t0) * 1000)
        return {"ok": True, "latency_ms": latency_ms, "sample_text": sample}
    except Exception as e:
        return {"ok": False, "error": str(e)[:300]}


@router.post("/{id_}/test")
def test_config(id_: int, db: Session = Depends(get_db)) -> dict:
    obj = crud.get_api_config(db, id_)
    if obj is None:
        raise HTTPException(404, "not found")
    return _ping_llm(obj.base_url, obj.api_key, obj.model_name, obj.type)
```

- [ ] **Step 4: 跑测试**

Run: `cd backend && .venv/bin/python -m pytest tests/test_routers_api_config_test.py -v`
Expected: 2 passed

- [ ] **Step 5: 跑全套**

Run: `cd backend && .venv/bin/python -m pytest tests/ 2>&1 | tail -3`
Expected: 48 passed

- [ ] **Step 6: Commit**

```bash
git add backend/service/routers/api_configs.py backend/tests/test_routers_api_config_test.py
git commit -m "feat(backend): /api/api-configs/{id}/test connectivity check"
```

---

### Task 17: `/api/sample-types` meta 端点

**Files:**
- Create: `backend/service/routers/meta.py`
- Modify: `backend/service/main.py`
- Create: `backend/tests/test_routers_meta.py`

- [ ] **Step 1: 写测试**

```python
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
```

- [ ] **Step 2: 跑测试,确认失败**

Run: `cd backend && .venv/bin/python -m pytest tests/test_routers_meta.py -v`
Expected: 404

- [ ] **Step 3: 实现 routers/meta.py**

```python
# backend/service/routers/meta.py
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from service import models
from service.deps import get_db

router = APIRouter(prefix="/api", tags=["meta"])

SAMPLE_TYPES = ("black", "gray", "white")


@router.get("/sample-types")
def list_sample_types(db: Session = Depends(get_db)) -> list[dict]:
    counts = dict(db.execute(
        select(models.Category.sample_type, func.count(models.Category.id))
        .group_by(models.Category.sample_type)
    ).all())
    return [{"sample_type": st, "category_count": counts.get(st, 0)}
            for st in SAMPLE_TYPES]
```

- [ ] **Step 4: 注册路由**

In `backend/service/main.py`:
```python
from service.routers import meta as meta_router
```
and:
```python
app.include_router(meta_router.router)
```

- [ ] **Step 5: 跑测试**

Run: `cd backend && .venv/bin/python -m pytest tests/test_routers_meta.py -v`
Expected: 2 passed

- [ ] **Step 6: 跑全套**

Run: `cd backend && .venv/bin/python -m pytest tests/ 2>&1 | tail -3`
Expected: 50 passed

- [ ] **Step 7: Commit**

```bash
git add backend/service/routers/meta.py backend/service/main.py backend/tests/test_routers_meta.py
git commit -m "feat(backend): /api/sample-types meta endpoint"
```

---

## N. Worker 核心

### Task 18: LLM 客户端(openai + raw,带退避重试)

**Files:**
- Create: `backend/service/llm_client.py`
- Create: `backend/tests/test_llm_client.py`

设计:`LlmClient` 接收 snapshot 字段 (`base_url`, `api_key`, `model_name`, `api_type`),提供 `call(prompt: str) -> str` 返回模型生成文本。内部用指数退避重试 (1→2→4→8→16→30 秒, 上限 5 次)。401/403 立刻抛出不重试。

- [ ] **Step 1: 写测试**

```python
# backend/tests/test_llm_client.py
import pytest

from service.llm_client import LlmClient, AuthError, RetryExhausted


class _FakeOpenAI:
    """Stand-in for openai.OpenAI client."""
    def __init__(self, responses):
        # responses: list of (kind, value) — kind in ("ok", "rate", "auth", "server")
        self.responses = list(responses)
        self.chat = self
        self.completions = self

    def create(self, **kw):
        kind, value = self.responses.pop(0)
        if kind == "ok":
            class M: content = value
            class C: message = M()
            class R: choices = [C()]
            return R()
        if kind == "rate":
            from openai import RateLimitError
            raise RateLimitError(message="429", response=None, body=None)
        if kind == "auth":
            from openai import AuthenticationError
            raise AuthenticationError(message="401", response=None, body=None)
        if kind == "server":
            from openai import APIStatusError
            raise APIStatusError(message="500", response=None, body=None)
        raise RuntimeError(kind)


def test_openai_call_success(monkeypatch):
    fake = _FakeOpenAI([("ok", "hello world")])
    monkeypatch.setattr("service.llm_client._make_openai", lambda *a, **k: fake)
    c = LlmClient(base_url="x", api_key="k", model_name="m", api_type="openai",
                  max_retries=3, sleep=lambda s: None)
    out = c.call("ping")
    assert out == "hello world"


def test_openai_call_retries_then_succeeds(monkeypatch):
    fake = _FakeOpenAI([("rate", None), ("server", None), ("ok", "got it")])
    monkeypatch.setattr("service.llm_client._make_openai", lambda *a, **k: fake)
    c = LlmClient(base_url="x", api_key="k", model_name="m", api_type="openai",
                  max_retries=5, sleep=lambda s: None)
    assert c.call("ping") == "got it"


def test_openai_call_raises_auth_error_immediately(monkeypatch):
    fake = _FakeOpenAI([("auth", None)])
    monkeypatch.setattr("service.llm_client._make_openai", lambda *a, **k: fake)
    c = LlmClient(base_url="x", api_key="k", model_name="m", api_type="openai",
                  max_retries=5, sleep=lambda s: None)
    with pytest.raises(AuthError):
        c.call("ping")


def test_openai_call_exhausts_retries(monkeypatch):
    fake = _FakeOpenAI([("rate", None)] * 10)
    monkeypatch.setattr("service.llm_client._make_openai", lambda *a, **k: fake)
    c = LlmClient(base_url="x", api_key="k", model_name="m", api_type="openai",
                  max_retries=3, sleep=lambda s: None)
    with pytest.raises(RetryExhausted):
        c.call("ping")


def test_raw_call_success(monkeypatch):
    class FakeResp:
        status_code = 200
        def json(self):
            return {"choices": [{"message": {"content": "raw-ok"}}]}
        def raise_for_status(self):
            pass

    def fake_post(url, headers, json, timeout):
        return FakeResp()

    monkeypatch.setattr("service.llm_client.requests.post", fake_post)
    c = LlmClient(base_url="http://x", api_key="k", model_name="m", api_type="raw",
                  max_retries=3, sleep=lambda s: None)
    assert c.call("ping") == "raw-ok"


def test_raw_call_429_then_ok(monkeypatch):
    calls = {"n": 0}
    class Resp429:
        status_code = 429
        text = "rate limit"
        def raise_for_status(self):
            import requests
            raise requests.HTTPError("429", response=self)

    class RespOk:
        status_code = 200
        def json(self):
            return {"choices": [{"message": {"content": "ok"}}]}
        def raise_for_status(self):
            pass

    def fake_post(url, headers, json, timeout):
        calls["n"] += 1
        return Resp429() if calls["n"] == 1 else RespOk()

    monkeypatch.setattr("service.llm_client.requests.post", fake_post)
    c = LlmClient(base_url="http://x", api_key="k", model_name="m", api_type="raw",
                  max_retries=3, sleep=lambda s: None)
    assert c.call("ping") == "ok"
    assert calls["n"] == 2
```

- [ ] **Step 2: 跑测试,确认失败**

Run: `cd backend && .venv/bin/python -m pytest tests/test_llm_client.py -v`
Expected: ImportError

- [ ] **Step 3: 实现 llm_client.py**

```python
# backend/service/llm_client.py
import json
from dataclasses import dataclass, field
from typing import Callable

import requests


class LlmError(Exception):
    """Base class for LLM client errors."""


class AuthError(LlmError):
    """401/403 from upstream — non-retryable."""


class RetryExhausted(LlmError):
    """Retry budget exhausted after retryable failures."""


_BACKOFF = [1, 2, 4, 8, 16, 30]


def _make_openai(base_url: str, api_key: str):
    from openai import OpenAI
    return OpenAI(api_key=api_key, base_url=base_url, timeout=120)


@dataclass
class LlmClient:
    base_url: str
    api_key: str
    model_name: str
    api_type: str   # "openai" | "raw"
    max_retries: int = 5
    sleep: Callable[[float], None] = field(default=__import__("time").sleep)

    def call(self, prompt: str) -> str:
        if self.api_type == "openai":
            return self._call_openai(prompt)
        return self._call_raw(prompt)

    # ---- openai path ----
    def _call_openai(self, prompt: str) -> str:
        from openai import (
            AuthenticationError, PermissionDeniedError,
            RateLimitError, APIStatusError, APIConnectionError, APITimeoutError,
        )
        client = _make_openai(self.base_url, self.api_key)
        for attempt in range(self.max_retries):
            try:
                rsp = client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                )
                return rsp.choices[0].message.content or ""
            except (AuthenticationError, PermissionDeniedError) as e:
                raise AuthError(str(e)) from e
            except (RateLimitError, APIStatusError,
                    APIConnectionError, APITimeoutError) as e:
                if attempt >= self.max_retries - 1:
                    raise RetryExhausted(str(e)) from e
                self.sleep(_BACKOFF[min(attempt, len(_BACKOFF) - 1)])
        raise RetryExhausted("budget exhausted")

    # ---- raw path ----
    def _call_raw(self, prompt: str) -> str:
        url = f"{self.base_url.rstrip('/')}/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}",
                   "Content-Type": "application/json"}
        payload = {"model": self.model_name, "stream": False,
                   "messages": [{"role": "user", "content": prompt}]}
        for attempt in range(self.max_retries):
            try:
                rsp = requests.post(url, headers=headers,
                                    json=payload, timeout=120)
                if rsp.status_code in (401, 403):
                    raise AuthError(f"HTTP {rsp.status_code}")
                if rsp.status_code == 429 or 500 <= rsp.status_code < 600:
                    if attempt >= self.max_retries - 1:
                        raise RetryExhausted(f"HTTP {rsp.status_code}")
                    self.sleep(_BACKOFF[min(attempt, len(_BACKOFF) - 1)])
                    continue
                rsp.raise_for_status()
                return rsp.json()["choices"][0]["message"]["content"] or ""
            except AuthError:
                raise
            except (requests.ConnectionError, requests.Timeout) as e:
                if attempt >= self.max_retries - 1:
                    raise RetryExhausted(str(e)) from e
                self.sleep(_BACKOFF[min(attempt, len(_BACKOFF) - 1)])
        raise RetryExhausted("budget exhausted")
```

- [ ] **Step 4: 跑测试**

Run: `cd backend && .venv/bin/python -m pytest tests/test_llm_client.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add backend/service/llm_client.py backend/tests/test_llm_client.py
git commit -m "feat(backend): LLM client with openai + raw modes and exponential backoff"
```

---

### Task 19: Worker 主循环 (`worker_run.py`)

**Files:**
- Create: `backend/service/worker_run.py`
- Create: `backend/tests/test_worker_run.py`

设计:`run_task(task_id, *, mock_llm=False)` — 由 worker CLI 调用。读 Task 行的 snapshot 字段,初始化 LlmClient (或 mock),用 ThreadPoolExecutor 跑并发,每 K 条调 `crud.update_task_progress` + `crud.add_task_event(type="progress")`。检查 status==aborted 立刻退出。

- [ ] **Step 1: 写测试**

```python
# backend/tests/test_worker_run.py
import json

from service import crud, db as dbmod, models
from service.schemas import (
    ApiConfigCreate, WordListCreate, PromptTemplateCreate, CategoryCreate
)


def _bootstrap_running_task(tmp_path, monkeypatch):
    """Create a fully-configured Task in 'running' state and return its id."""
    import sys
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "app.db"))
    for m in [k for k in list(sys.modules) if k == "service" or k.startswith("service.")]:
        sys.modules.pop(m, None)
    import service.config  # noqa: F401
    import service.db as dbmod_fresh
    import service.models  # noqa: F401
    dbmod_fresh.init_engine()
    dbmod_fresh.Base.metadata.create_all(dbmod_fresh.engine)

    from service import crud, models  # noqa
    with dbmod_fresh.SessionLocal() as s:
        api = crud.create_api_config(s, ApiConfigCreate(
            name="A", base_url="x", api_key="k",
            model_name="m", type="openai"))
        s_wl = crud.create_wordlist(s, WordListCreate(
            name="scn", kind="scenario", items=["sa", "sb"]))
        t_wl = crud.create_wordlist(s, WordListCreate(
            name="tne", kind="tone", items=["ta", "tb"]))
        pt = crud.create_prompt_template(s, PromptTemplateCreate(
            name="p", body="cat={category} scn={scenario} tne={tone} n={batch_size}",
            variables=["category", "scenario", "tone", "batch_size"]))
        cat = crud.create_category(s, CategoryCreate(
            sample_type="black", name="X", description="",
            prompt_template_id=pt.id, scenario_list_id=s_wl.id,
            tone_list_id=t_wl.id, default_target_count=10))
        task = crud.create_task_snapshot(
            s, cat.id, api.id,
            target_count=20, batch_size=5, max_workers=2, max_per_file=50,
            created_by_label=None, resume_from_task_id=None)
        out_dir = tmp_path / f"data/task-{task.id}"
        out_dir.mkdir(parents=True, exist_ok=True)
        crud.mark_task_started(s, task.id, worker_pid=0,
                               output_dir=str(out_dir))
        return task.id, dbmod_fresh


def test_worker_run_with_mock_llm_writes_target_rows(tmp_path, monkeypatch):
    task_id, dbmod_fresh = _bootstrap_running_task(tmp_path, monkeypatch)
    from service import worker_run
    worker_run.run_task(task_id, mock_llm=True)

    with dbmod_fresh.SessionLocal() as s:
        t = s.get(models.Task, task_id)
        assert t.status == "succeeded"
        assert t.progress_current == 20
        ev_types = [e.type for e in s.query(models.TaskEvent)
                    .filter_by(task_id=task_id).order_by(models.TaskEvent.id).all()]
        assert ev_types[0] == "started"
        assert ev_types[-1] == "finished"
        assert "progress" in ev_types

    csvs = sorted((tmp_path / f"data/task-{task_id}").glob("*.csv"))
    assert len(csvs) >= 1
    total_rows = 0
    for p in csvs:
        with open(p, "r", encoding="utf-8-sig") as f:
            total_rows += max(0, sum(1 for _ in f) - 1)
    assert total_rows == 20


def test_worker_run_honors_abort_signal(tmp_path, monkeypatch):
    task_id, dbmod_fresh = _bootstrap_running_task(tmp_path, monkeypatch)
    # Pre-abort the task before running
    with dbmod_fresh.SessionLocal() as s:
        crud.set_task_status(s, task_id, "aborted")

    from service import worker_run
    worker_run.run_task(task_id, mock_llm=True)

    with dbmod_fresh.SessionLocal() as s:
        t = s.get(models.Task, task_id)
        # status stays aborted, did not flip to succeeded
        assert t.status == "aborted"
        # progress may be 0 or partial — must not equal target_count
        assert t.progress_current < 20


def test_worker_run_auth_error_marks_failed(tmp_path, monkeypatch):
    task_id, dbmod_fresh = _bootstrap_running_task(tmp_path, monkeypatch)

    # Patch LlmClient.call to raise AuthError
    from service import llm_client, worker_run

    class _AlwaysAuthErr:
        def __init__(self, *a, **kw): pass
        def call(self, prompt):
            raise llm_client.AuthError("forbidden")

    monkeypatch.setattr(worker_run, "LlmClient", _AlwaysAuthErr)
    worker_run.run_task(task_id, mock_llm=False)

    with dbmod_fresh.SessionLocal() as s:
        t = s.get(models.Task, task_id)
        assert t.status == "failed"
        assert "auth" in (t.error_msg or "").lower() or "forbidden" in (t.error_msg or "").lower()
```

- [ ] **Step 2: 跑测试,确认失败**

Run: `cd backend && .venv/bin/python -m pytest tests/test_worker_run.py -v`
Expected: ImportError

- [ ] **Step 3: 实现 worker_run.py**

```python
# backend/service/worker_run.py
import json
import random
import re
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from service import crud, db as dbmod, models
from service.config import settings
from service.llm_client import LlmClient, AuthError, RetryExhausted
from service.prompt_render import render_prompt
from service.worker_io import CsvVolumeWriter


CSV_HEADER = ["评测题", "风险类型"]
_LINE_PREFIX = re.compile(r"^\s*(?:\d+[\.、]\s*|-\s+)")


def _flush_threshold(batch_size: int) -> int:
    return max(settings.progress_flush_min,
               batch_size * settings.progress_flush_batch_multiplier)


def _parse_lines(text: str) -> list[str]:
    out = []
    for raw in (text or "").splitlines():
        line = _LINE_PREFIX.sub("", raw.strip())
        if len(line) >= 10:
            out.append(line)
    return out


def _mock_call(prompt: str, batch_size: int) -> str:
    return "\n".join(f"{i+1}. mocked line {i+1}" for i in range(batch_size))


def run_task(task_id: int, *, mock_llm: bool = False) -> None:
    """Worker main loop. Reads task by id, runs the generation loop, writes
    CSV volumes, updates progress + events. On error/auth/abort, sets the
    task's terminal status before returning. Never raises."""
    if dbmod.SessionLocal is None:
        dbmod.init_engine()
        dbmod.Base.metadata.create_all(dbmod.engine)

    Session = dbmod.SessionLocal
    with Session() as s:
        task = s.get(models.Task, task_id)
        if task is None:
            return
        # If already aborted before worker started, bail without progress.
        if task.status == "aborted":
            crud.add_task_event(s, task_id, "aborted",
                                "worker found task already aborted")
            return
        snapshot_prompt = task.snapshot_prompt_body
        scenario_items = json.loads(task.snapshot_scenario_items_json)
        tone_items = json.loads(task.snapshot_tone_items_json)
        category_name = task.snapshot_category_name
        target_count = task.target_count
        batch_size = task.batch_size
        max_workers = task.max_workers
        max_per_file = task.max_per_file
        output_dir = Path(task.output_dir)

    with Session() as s:
        crud.add_task_event(s, task_id, "started",
                            f"target={target_count} output={output_dir}")

    base_name = f"task_{task_id}"
    writer = CsvVolumeWriter(
        out_dir=output_dir, base_name=base_name,
        header=CSV_HEADER, max_per_file=max_per_file,
    )
    writer.resume()

    # Initial progress from existing rows
    from service.worker_io import count_existing_rows
    current = count_existing_rows(output_dir)
    if current > 0:
        with Session() as s:
            crud.update_task_progress(s, task_id, current)

    flush_thresh = _flush_threshold(batch_size)
    pending_since_flush = 0
    consecutive_batch_failures = 0
    error_terminal_msg: str | None = None
    error_status = "failed"

    def _make_prompt() -> str:
        return render_prompt(snapshot_prompt, {
            "category": category_name,
            "scenario": random.choice(scenario_items) if scenario_items else "",
            "tone": random.choice(tone_items) if tone_items else "",
            "batch_size": str(batch_size),
        })

    def _call_one() -> list[str]:
        prompt = _make_prompt()
        if mock_llm:
            text = _mock_call(prompt, batch_size)
        else:
            client = LlmClient(
                base_url=task_snapshot["base_url"],
                api_key=task_snapshot["api_key"],
                model_name=task_snapshot["model_name"],
                api_type=task_snapshot["api_type"],
            )
            text = client.call(prompt)
        return _parse_lines(text)

    # Read API snapshot once (not via session every batch)
    with Session() as s:
        task = s.get(models.Task, task_id)
        task_snapshot = {
            "base_url": task.snapshot_api_base_url,
            "api_key": task.snapshot_api_key,
            "model_name": task.snapshot_model_name,
            "api_type": task.snapshot_api_type,
        }

    try:
        executor = ThreadPoolExecutor(max_workers=max_workers)
        try:
            while current < target_count:
                # Check abort before each round
                with Session() as s:
                    fresh = s.get(models.Task, task_id)
                    if fresh.status == "aborted":
                        crud.add_task_event(s, task_id, "aborted",
                                            f"aborted at {current}/{target_count}")
                        return

                in_flight_size = min(max_workers, max(1, (target_count - current) // batch_size))
                futures = [executor.submit(_call_one) for _ in range(in_flight_size)]
                batch_added = 0
                for fut in as_completed(futures):
                    try:
                        lines = fut.result()
                    except AuthError as e:
                        error_status = "failed"
                        error_terminal_msg = f"auth error: {e}"[:300]
                        raise
                    except RetryExhausted as e:
                        consecutive_batch_failures += 1
                        with Session() as s:
                            crud.add_task_event(s, task_id, "warning",
                                                f"batch retry exhausted: {e}"[:200])
                        continue
                    consecutive_batch_failures = 0
                    for line in lines:
                        if current >= target_count:
                            break
                        writer.write_row([line, category_name])
                        current += 1
                        batch_added += 1
                        pending_since_flush += 1
                writer.flush()

                if pending_since_flush >= flush_thresh or current >= target_count:
                    with Session() as s:
                        crud.update_task_progress(s, task_id, current)
                        crud.add_task_event(s, task_id, "progress",
                                            f"{current}/{target_count}")
                    pending_since_flush = 0

                if consecutive_batch_failures >= 10:
                    error_status = "failed"
                    error_terminal_msg = "10 consecutive batch failures, aborting"
                    raise RetryExhausted(error_terminal_msg)
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
            writer.close()

        with Session() as s:
            crud.mark_task_finished(s, task_id, "succeeded")
            crud.add_task_event(s, task_id, "finished",
                                f"generated {current}/{target_count}")
    except AuthError as e:
        with Session() as s:
            crud.mark_task_finished(s, task_id, "failed",
                                    error_msg=error_terminal_msg or str(e)[:300])
            crud.add_task_event(s, task_id, "error",
                                error_terminal_msg or str(e)[:200])
    except RetryExhausted as e:
        with Session() as s:
            crud.mark_task_finished(s, task_id, "failed",
                                    error_msg=error_terminal_msg or str(e)[:300])
            crud.add_task_event(s, task_id, "error",
                                error_terminal_msg or str(e)[:200])
    except Exception as e:
        log_path = settings.task_log(task_id)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(traceback.format_exc(), encoding="utf-8")
        with Session() as s:
            crud.mark_task_finished(s, task_id, "failed",
                                    error_msg=f"{type(e).__name__}: {e}"[:300])
            crud.add_task_event(s, task_id, "error",
                                f"{type(e).__name__}: {e}"[:200])
```

- [ ] **Step 4: 跑测试**

Run: `cd backend && .venv/bin/python -m pytest tests/test_worker_run.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add backend/service/worker_run.py backend/tests/test_worker_run.py
git commit -m "feat(backend): worker main loop with mock-LLM, abort, auth handling"
```

---

### Task 20: Worker CLI 入口

**Files:**
- Create: `backend/service/worker.py`
- Create: `backend/tests/test_worker_cli.py`

- [ ] **Step 1: 写测试**

```python
# backend/tests/test_worker_cli.py
import subprocess
import sys
import json

from service.schemas import (
    ApiConfigCreate, WordListCreate, PromptTemplateCreate, CategoryCreate
)


def test_worker_cli_runs_task_with_mock(tmp_path, monkeypatch):
    """End-to-end: spawn `python -m service.worker --task-id N --mock-llm`
    as a real subprocess and verify the task completes."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "app.db"))

    # Setup DB + task via in-process imports (parent process)
    import importlib
    for m in [k for k in list(sys.modules) if k == "service" or k.startswith("service.")]:
        sys.modules.pop(m, None)
    import service.config  # noqa: F401
    import service.db as dbmod
    import service.models  # noqa: F401
    dbmod.init_engine()
    dbmod.Base.metadata.create_all(dbmod.engine)

    from service import crud
    with dbmod.SessionLocal() as s:
        api = crud.create_api_config(s, ApiConfigCreate(
            name="A", base_url="x", api_key="k",
            model_name="m", type="openai"))
        wl_s = crud.create_wordlist(s, WordListCreate(
            name="scn", kind="scenario", items=["a"]))
        wl_t = crud.create_wordlist(s, WordListCreate(
            name="tne", kind="tone", items=["b"]))
        pt = crud.create_prompt_template(s, PromptTemplateCreate(
            name="p", body="x {category} {scenario} {tone} {batch_size}",
            variables=["category", "scenario", "tone", "batch_size"]))
        cat = crud.create_category(s, CategoryCreate(
            sample_type="black", name="C", description="",
            prompt_template_id=pt.id, scenario_list_id=wl_s.id,
            tone_list_id=wl_t.id, default_target_count=5))
        task = crud.create_task_snapshot(s, cat.id, api.id,
            target_count=5, batch_size=2, max_workers=1, max_per_file=50,
            created_by_label=None, resume_from_task_id=None)
        out_dir = tmp_path / f"data/task-{task.id}"
        out_dir.mkdir(parents=True, exist_ok=True)
        crud.mark_task_started(s, task.id, worker_pid=0, output_dir=str(out_dir))
        task_id = task.id

    env = {**__import__("os").environ,
           "DATA_DIR": str(tmp_path / "data"),
           "LOG_DIR": str(tmp_path / "logs"),
           "DB_PATH": str(tmp_path / "app.db")}
    proc = subprocess.run(
        [sys.executable, "-m", "service.worker",
         "--task-id", str(task_id), "--mock-llm"],
        env=env, cwd=".", capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode == 0, proc.stderr

    # Verify
    from service import models
    with dbmod.SessionLocal() as s:
        t = s.get(models.Task, task_id)
        assert t.status == "succeeded"
        assert t.progress_current == 5
```

- [ ] **Step 2: 跑测试,确认失败**

Run: `cd backend && .venv/bin/python -m pytest tests/test_worker_cli.py -v`
Expected: ModuleNotFoundError or exit code != 0

- [ ] **Step 3: 实现 worker.py**

```python
# backend/service/worker.py
"""CLI entry: python -m service.worker --task-id N [--mock-llm]"""
import argparse

from service import db as dbmod
from service.worker_run import run_task


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", type=int, required=True)
    parser.add_argument("--mock-llm", action="store_true",
                        help="Skip real LLM calls; emit synthetic batches.")
    args = parser.parse_args()

    if dbmod.SessionLocal is None:
        dbmod.init_engine()
        dbmod.Base.metadata.create_all(dbmod.engine)

    run_task(args.task_id, mock_llm=args.mock_llm)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 跑测试**

Run: `cd backend && .venv/bin/python -m pytest tests/test_worker_cli.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add backend/service/worker.py backend/tests/test_worker_cli.py
git commit -m "feat(backend): worker CLI entry — python -m service.worker"
```

---

### Task 21: Worker resume(基于已有 CSV 续跑)端到端测试

**Files:**
- Create: `backend/tests/test_worker_resume.py`

只加测试,验证 `run_task` 启动时正确把已存在 CSV 行数当起点 — 实际 resume 逻辑由 `worker_io.count_existing_rows` 和 `CsvVolumeWriter.resume()` 实现,Task 19 已具备。

- [ ] **Step 1: 写测试**

```python
# backend/tests/test_worker_resume.py
import csv
import sys

from service.schemas import (
    ApiConfigCreate, WordListCreate, PromptTemplateCreate, CategoryCreate
)


def test_worker_run_resumes_from_existing_csv(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "app.db"))
    for m in [k for k in list(sys.modules) if k == "service" or k.startswith("service.")]:
        sys.modules.pop(m, None)
    import service.config  # noqa: F401
    import service.db as dbmod
    import service.models  # noqa: F401
    dbmod.init_engine()
    dbmod.Base.metadata.create_all(dbmod.engine)

    from service import crud, models, worker_run

    with dbmod.SessionLocal() as s:
        api = crud.create_api_config(s, ApiConfigCreate(
            name="A", base_url="x", api_key="k",
            model_name="m", type="openai"))
        wl_s = crud.create_wordlist(s, WordListCreate(
            name="scn", kind="scenario", items=["a"]))
        wl_t = crud.create_wordlist(s, WordListCreate(
            name="tne", kind="tone", items=["b"]))
        pt = crud.create_prompt_template(s, PromptTemplateCreate(
            name="p", body="x {category} {scenario} {tone} {batch_size}",
            variables=["category", "scenario", "tone", "batch_size"]))
        cat = crud.create_category(s, CategoryCreate(
            sample_type="black", name="C", description="",
            prompt_template_id=pt.id, scenario_list_id=wl_s.id,
            tone_list_id=wl_t.id, default_target_count=10))
        task = crud.create_task_snapshot(s, cat.id, api.id,
            target_count=10, batch_size=2, max_workers=1, max_per_file=100,
            created_by_label=None, resume_from_task_id=None)
        out_dir = tmp_path / f"data/task-{task.id}"
        out_dir.mkdir(parents=True, exist_ok=True)
        # Pre-existing CSV with 4 rows already
        with open(out_dir / f"task_{task.id}_part1.csv", "w",
                  newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["评测题", "风险类型"])
            for i in range(4):
                w.writerow([f"old line {i}", "C"])
        crud.mark_task_started(s, task.id, worker_pid=0,
                               output_dir=str(out_dir))
        task_id = task.id

    worker_run.run_task(task_id, mock_llm=True)

    with dbmod.SessionLocal() as s:
        t = s.get(models.Task, task_id)
        assert t.status == "succeeded"
        assert t.progress_current == 10

    rows = []
    for p in sorted((tmp_path / f"data/task-{task_id}").glob("*.csv")):
        with open(p, "r", encoding="utf-8-sig") as f:
            r = csv.reader(f)
            next(r)  # header
            rows.extend(list(r))
    assert len(rows) == 10
    assert rows[0][0] == "old line 0"   # original 4 are preserved
    assert rows[3][0] == "old line 3"
```

- [ ] **Step 2: 跑测试,确认通过(应该已经通过,因为 worker_run 在 Task 19 已实现 resume)**

Run: `cd backend && .venv/bin/python -m pytest tests/test_worker_resume.py -v`
Expected: 1 passed

- [ ] **Step 3: 跑全套**

Run: `cd backend && .venv/bin/python -m pytest tests/ 2>&1 | tail -3`
Expected: ~62 passed

- [ ] **Step 4: Commit**

```bash
git add backend/tests/test_worker_resume.py
git commit -m "test(backend): worker resumes from existing CSV rows"
```

---

## O. 任务编排 (Supervisor + Tasks router)

### Task 22: Supervisor (spawn / 监督 / 启动恢复)

**Files:**
- Create: `backend/service/supervisor.py`
- Create: `backend/tests/test_supervisor.py`

设计:
- `spawn_worker(task_id) -> int` — `subprocess.Popen(["python", "-m", "service.worker", "--task-id", ...])`,返回 pid。环境变量继承 `DATA_DIR/LOG_DIR/DB_PATH`。
- `is_pid_alive(pid: int) -> bool` — `os.kill(pid, 0)` 探测
- `recover_orphaned_running() -> int` — 启动时扫所有 `status=running` 的 task,pid 不存活则标 `failed`,返回扫到几条。
- `terminate_worker(pid, grace_seconds=2)` — `SIGTERM` → wait → `SIGKILL`

- [ ] **Step 1: 写测试**

```python
# backend/tests/test_supervisor.py
import os
import signal
import sys
import time

from service.schemas import (
    ApiConfigCreate, WordListCreate, PromptTemplateCreate, CategoryCreate
)


def _fresh_env(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "app.db"))
    for m in [k for k in list(sys.modules) if k == "service" or k.startswith("service.")]:
        sys.modules.pop(m, None)
    import service.config  # noqa: F401
    import service.db as dbmod
    import service.models  # noqa: F401
    dbmod.init_engine()
    dbmod.Base.metadata.create_all(dbmod.engine)
    return dbmod


def _seed_pending_task(dbmod):
    from service import crud
    with dbmod.SessionLocal() as s:
        api = crud.create_api_config(s, ApiConfigCreate(
            name="A", base_url="x", api_key="k",
            model_name="m", type="openai"))
        wl_s = crud.create_wordlist(s, WordListCreate(
            name="scn", kind="scenario", items=["a"]))
        wl_t = crud.create_wordlist(s, WordListCreate(
            name="tne", kind="tone", items=["b"]))
        pt = crud.create_prompt_template(s, PromptTemplateCreate(
            name="p", body="x {category} {scenario} {tone} {batch_size}",
            variables=["category", "scenario", "tone", "batch_size"]))
        cat = crud.create_category(s, CategoryCreate(
            sample_type="black", name="C", description="",
            prompt_template_id=pt.id, scenario_list_id=wl_s.id,
            tone_list_id=wl_t.id, default_target_count=5))
        task = crud.create_task_snapshot(s, cat.id, api.id,
            target_count=5, batch_size=2, max_workers=1, max_per_file=50,
            created_by_label=None, resume_from_task_id=None)
        return task.id


def test_spawn_worker_runs_subprocess_end_to_end(tmp_path, monkeypatch):
    dbmod = _fresh_env(tmp_path, monkeypatch)
    task_id = _seed_pending_task(dbmod)
    from service import supervisor, models

    pid = supervisor.spawn_worker(task_id, mock_llm=True)
    assert pid > 0

    # Wait for subprocess to finish
    for _ in range(120):
        if not supervisor.is_pid_alive(pid):
            break
        time.sleep(0.5)
    else:
        os.kill(pid, signal.SIGKILL)
        raise AssertionError("worker did not finish in 60s")

    with dbmod.SessionLocal() as s:
        t = s.get(models.Task, task_id)
        assert t.status == "succeeded"
        assert t.progress_current == 5


def test_is_pid_alive_false_for_nonexistent(tmp_path, monkeypatch):
    _fresh_env(tmp_path, monkeypatch)
    from service import supervisor
    assert supervisor.is_pid_alive(999_999_999) is False


def test_recover_orphans_marks_dead_pid_as_failed(tmp_path, monkeypatch):
    dbmod = _fresh_env(tmp_path, monkeypatch)
    task_id = _seed_pending_task(dbmod)
    from service import crud, models, supervisor

    with dbmod.SessionLocal() as s:
        crud.mark_task_started(s, task_id,
                               worker_pid=999_999_999,
                               output_dir=str(tmp_path / "x"))

    n = supervisor.recover_orphaned_running()
    assert n == 1

    with dbmod.SessionLocal() as s:
        t = s.get(models.Task, task_id)
        assert t.status == "failed"
        assert "lost" in (t.error_msg or "").lower() or "orphan" in (t.error_msg or "").lower()


def test_terminate_worker_sends_signals(tmp_path, monkeypatch):
    _fresh_env(tmp_path, monkeypatch)
    from service import supervisor

    # Spawn a long-running sleep, then terminate
    import subprocess
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        supervisor.terminate_worker(proc.pid, grace_seconds=1)
        proc.wait(timeout=5)
        assert proc.returncode is not None
    finally:
        if proc.poll() is None:
            proc.kill()
```

- [ ] **Step 2: 跑测试,确认失败**

Run: `cd backend && .venv/bin/python -m pytest tests/test_supervisor.py -v`
Expected: ImportError

- [ ] **Step 3: 实现 supervisor.py**

```python
# backend/service/supervisor.py
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from service import crud, db as dbmod, models
from service.config import settings


def spawn_worker(task_id: int, *, mock_llm: bool = False) -> int:
    """Spawn a worker subprocess for the given task. Returns its pid."""
    out_dir = settings.task_dir(task_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [sys.executable, "-m", "service.worker", "--task-id", str(task_id)]
    if mock_llm:
        cmd.append("--mock-llm")

    log_path = settings.task_log(task_id)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_fh = open(log_path, "a", encoding="utf-8")
    proc = subprocess.Popen(
        cmd,
        stdout=log_fh, stderr=subprocess.STDOUT,
        env={**os.environ,
             "DATA_DIR": str(settings.data_dir),
             "LOG_DIR": str(settings.log_dir),
             "DB_PATH": str(settings.db_path)},
    )

    # Record pid + output_dir in the task row
    if dbmod.SessionLocal is None:
        dbmod.init_engine()
        dbmod.Base.metadata.create_all(dbmod.engine)
    with dbmod.SessionLocal() as s:
        crud.mark_task_started(s, task_id,
                               worker_pid=proc.pid,
                               output_dir=str(out_dir))
    return proc.pid


def is_pid_alive(pid: int | None) -> bool:
    if not pid or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False
    except OSError:
        return False


def terminate_worker(pid: int, *, grace_seconds: int | None = None) -> None:
    if not is_pid_alive(pid):
        return
    grace = grace_seconds if grace_seconds is not None else settings.abort_grace_seconds
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + grace
    while time.monotonic() < deadline:
        if not is_pid_alive(pid):
            return
        time.sleep(0.1)
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        return


def recover_orphaned_running() -> int:
    """Scan tasks with status='running' whose worker_pid is no longer alive.
    Mark each as failed. Returns how many were recovered."""
    if dbmod.SessionLocal is None:
        dbmod.init_engine()
        dbmod.Base.metadata.create_all(dbmod.engine)

    count = 0
    with dbmod.SessionLocal() as s:
        rows = list(s.query(models.Task).filter_by(status="running").all())
    for row in rows:
        if is_pid_alive(row.worker_pid):
            continue
        with dbmod.SessionLocal() as s:
            crud.mark_task_finished(
                s, row.id, "failed",
                error_msg="service restart, worker lost (orphaned pid)")
            crud.add_task_event(s, row.id, "error",
                                f"worker pid {row.worker_pid} no longer alive")
        count += 1
    return count
```

- [ ] **Step 4: 跑测试**

Run: `cd backend && .venv/bin/python -m pytest tests/test_supervisor.py -v`
Expected: 4 passed (the spawn_worker test takes ~5-30s)

- [ ] **Step 5: Commit**

```bash
git add backend/service/supervisor.py backend/tests/test_supervisor.py
git commit -m "feat(backend): supervisor — spawn worker subprocess + orphan recovery"
```

---

### Task 23: `/api/tasks` 路由(创建/列表/详情/中止/删除/预览/下载)

**Files:**
- Create: `backend/service/routers/tasks.py`
- Modify: `backend/service/main.py`
- Create: `backend/tests/test_routers_tasks.py`

- [ ] **Step 1: 写测试**

```python
# backend/tests/test_routers_tasks.py
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
    assert r.headers["content-type"].startswith("application/")
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
```

- [ ] **Step 2: 跑测试,确认失败**

Run: `cd backend && .venv/bin/python -m pytest tests/test_routers_tasks.py -v`
Expected: 404 / ImportError

- [ ] **Step 3: 实现 routers/tasks.py**

```python
# backend/service/routers/tasks.py
import csv
import json
import os
import zipfile
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from service import crud, supervisor, worker_io
from service.config import settings
from service.deps import get_db
from service.schemas import (
    TaskCreate, TaskOut, TaskDetail, TaskEventOut
)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def _row_to_out(t) -> TaskOut:
    return TaskOut(
        id=t.id,
        sample_type=t.snapshot_sample_type,
        category_name=t.snapshot_category_name,
        api_config_id=t.api_config_id,
        api_model=t.snapshot_model_name,
        target_count=t.target_count,
        batch_size=t.batch_size,
        max_workers=t.max_workers,
        max_per_file=t.max_per_file,
        status=t.status,
        progress_current=t.progress_current,
        progress_total=t.progress_total,
        created_at=t.created_at,
        started_at=t.started_at,
        finished_at=t.finished_at,
        error_msg=t.error_msg,
        output_dir=t.output_dir,
        created_by_label=t.created_by_label,
        resume_from_task_id=t.resume_from_task_id,
    )


def _row_to_detail(t, events) -> TaskDetail:
    base = _row_to_out(t).model_dump()
    return TaskDetail(
        **base,
        snapshot_prompt_body=t.snapshot_prompt_body,
        snapshot_scenario_items=json.loads(t.snapshot_scenario_items_json),
        snapshot_tone_items=json.loads(t.snapshot_tone_items_json),
        snapshot_api_base_url=t.snapshot_api_base_url,
        snapshot_api_type=t.snapshot_api_type,
        recent_events=[TaskEventOut(id=e.id, ts=e.ts, type=e.type, message=e.message)
                       for e in events],
    )


@router.get("")
def list_(status: str | None = None, category_id: int | None = None,
          page: int = 1, size: int = 50,
          db: Session = Depends(get_db)) -> list[TaskOut]:
    rows = crud.list_tasks(db, status=status, category_id=category_id,
                           page=max(1, page), size=min(max(1, size), 200))
    return [_row_to_out(t) for t in rows]


@router.get("/{id_}")
def get(id_: int, db: Session = Depends(get_db)) -> TaskDetail:
    t = crud.get_task(db, id_)
    if t is None:
        raise HTTPException(404, "not found")
    return _row_to_detail(t, crud.recent_events(db, id_, limit=50))


@router.post("", status_code=status.HTTP_201_CREATED)
def create(payload: TaskCreate, db: Session = Depends(get_db)) -> TaskOut:
    try:
        t = crud.create_task_snapshot(
            db,
            category_id=payload.category_id,
            api_config_id=payload.api_config_id,
            target_count=payload.target_count,
            batch_size=payload.batch_size,
            max_workers=payload.max_workers,
            max_per_file=payload.max_per_file,
            created_by_label=payload.created_by_label,
            resume_from_task_id=payload.resume_from_task_id,
        )
    except ValueError as e:
        raise HTTPException(404, str(e))

    # If resume_from is given, copy old CSVs into new task dir
    if payload.resume_from_task_id is not None:
        old = crud.get_task(db, payload.resume_from_task_id)
        if old is not None and old.output_dir:
            new_dir = settings.task_dir(t.id)
            worker_io.copy_resume_csvs(Path(old.output_dir), new_dir)

    supervisor.spawn_worker(t.id)
    db.refresh(t)
    return _row_to_out(t)


@router.post("/{id_}/abort")
def abort(id_: int, db: Session = Depends(get_db)) -> dict:
    t = crud.get_task(db, id_)
    if t is None:
        raise HTTPException(404, "not found")
    if t.status not in ("pending", "running"):
        raise HTTPException(409, f"task is {t.status}, cannot abort")
    crud.set_task_status(db, id_, "aborted")
    if t.worker_pid:
        supervisor.terminate_worker(t.worker_pid)
    crud.add_task_event(db, id_, "aborted", "aborted via API")
    return {"id": id_, "status": "aborted"}


@router.delete("/{id_}", status_code=status.HTTP_204_NO_CONTENT)
def delete(id_: int, delete_files: bool = True,
           db: Session = Depends(get_db)) -> Response:
    t = crud.get_task(db, id_)
    if t is None:
        raise HTTPException(404, "not found")
    if t.status == "running":
        raise HTTPException(409, "task is running; abort first")
    out_dir = Path(t.output_dir) if t.output_dir else None

    # delete events then task
    from service import models
    db.query(models.TaskEvent).filter_by(task_id=id_).delete()
    db.delete(t); db.commit()

    if delete_files and out_dir and out_dir.exists():
        import shutil
        shutil.rmtree(out_dir, ignore_errors=True)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{id_}/preview")
def preview(id_: int, db: Session = Depends(get_db)) -> dict:
    t = crud.get_task(db, id_)
    if t is None:
        raise HTTPException(404, "not found")
    out_dir = Path(t.output_dir) if t.output_dir else None
    if not out_dir or not out_dir.exists():
        return {"header": [], "rows": []}
    rows: list[list[str]] = []
    header: list[str] = []
    for p in sorted(out_dir.glob("*.csv")):
        with open(p, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            try:
                file_header = next(reader)
            except StopIteration:
                continue
            if not header:
                header = file_header
            for row in reader:
                rows.append(row)
                if len(rows) >= settings.preview_rows:
                    return {"header": header, "rows": rows}
    return {"header": header, "rows": rows}


@router.get("/{id_}/download")
def download(id_: int, db: Session = Depends(get_db)):
    t = crud.get_task(db, id_)
    if t is None:
        raise HTTPException(404, "not found")
    out_dir = Path(t.output_dir) if t.output_dir else None
    if not out_dir or not out_dir.exists():
        raise HTTPException(404, "no output yet")
    files = sorted(out_dir.glob("*.csv"))
    if not files:
        raise HTTPException(404, "no csv output")

    if len(files) == 1:
        def iter_file():
            with open(files[0], "rb") as f:
                while chunk := f.read(64 * 1024):
                    yield chunk
        return StreamingResponse(
            iter_file(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="task-{id_}.csv"'},
        )

    def iter_zip():
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in files:
                zf.write(p, arcname=p.name)
        buf.seek(0)
        yield from iter(lambda: buf.read(64 * 1024), b"")

    return StreamingResponse(
        iter_zip(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="task-{id_}.zip"'},
    )


@router.get("/{id_}/events")
def events(id_: int, since_id: int = 0, limit: int = 200,
           db: Session = Depends(get_db)) -> list[TaskEventOut]:
    t = crud.get_task(db, id_)
    if t is None:
        raise HTTPException(404, "not found")
    items = crud.events_since(db, id_, since_id=since_id,
                              limit=min(max(1, limit), 1000))
    return [TaskEventOut(id=e.id, ts=e.ts, type=e.type, message=e.message)
            for e in items]


@router.get("/{id_}/log")
def log(id_: int, lines: int = 1000) -> dict:
    if lines <= 0:
        lines = 1000
    path = settings.task_log(id_)
    if not path.exists():
        return {"lines": []}
    # Cheap tail
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        all_lines = f.readlines()
    return {"lines": all_lines[-lines:]}
```

- [ ] **Step 4: 注册路由**

In `backend/service/main.py`:
```python
from service.routers import tasks as tasks_router
```
and:
```python
app.include_router(tasks_router.router)
```

- [ ] **Step 5: 跑测试**

Run: `cd backend && .venv/bin/python -m pytest tests/test_routers_tasks.py -v`
Expected: 5 passed (this batch is slower — uses real subprocess; budget 1-2 minutes)

- [ ] **Step 6: 跑全套**

Run: `cd backend && .venv/bin/python -m pytest tests/ 2>&1 | tail -3`
Expected: ~67 passed

- [ ] **Step 7: Commit**

```bash
git add backend/service/routers/tasks.py backend/service/main.py backend/tests/test_routers_tasks.py
git commit -m "feat(backend): /api/tasks CRUD + abort + preview + download + events + log"
```

---

### Task 24: 启动恢复 — 在 lifespan 里扫 orphans

**Files:**
- Modify: `backend/service/main.py`
- Create: `backend/tests/test_startup_recovery.py`

- [ ] **Step 1: 写测试**

```python
# backend/tests/test_startup_recovery.py
import sys

from fastapi.testclient import TestClient


def test_startup_recovers_running_tasks_with_dead_pids(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "app.db"))

    # First lifecycle: write a running-task row with a fake pid
    for m in [k for k in list(sys.modules) if k == "service" or k.startswith("service.")]:
        sys.modules.pop(m, None)
    import service.config  # noqa: F401
    import service.db as dbmod
    import service.models  # noqa: F401
    dbmod.init_engine()
    dbmod.Base.metadata.create_all(dbmod.engine)

    from service import crud, models
    from service.schemas import (
        ApiConfigCreate, WordListCreate, PromptTemplateCreate, CategoryCreate
    )
    with dbmod.SessionLocal() as s:
        api = crud.create_api_config(s, ApiConfigCreate(
            name="A", base_url="x", api_key="k",
            model_name="m", type="openai"))
        wl = crud.create_wordlist(s, WordListCreate(
            name="w", kind="scenario", items=["a"]))
        wl2 = crud.create_wordlist(s, WordListCreate(
            name="w2", kind="tone", items=["b"]))
        pt = crud.create_prompt_template(s, PromptTemplateCreate(
            name="p", body="x", variables=[]))
        cat = crud.create_category(s, CategoryCreate(
            sample_type="black", name="C", description="",
            prompt_template_id=pt.id, scenario_list_id=wl.id,
            tone_list_id=wl2.id, default_target_count=1))
        t = crud.create_task_snapshot(s, cat.id, api.id, 1, 1, 1, 50, None, None)
        crud.mark_task_started(s, t.id, worker_pid=999_999_999,
                               output_dir=str(tmp_path / "x"))
        task_id = t.id

    # Restart the app (fresh import) → startup hook runs recovery
    for m in [k for k in list(sys.modules) if k == "service" or k.startswith("service.")]:
        sys.modules.pop(m, None)
    import service.config  # noqa: F401
    import service.db as dbmod2
    import service.models  # noqa: F401
    import service.main as mainmod

    with TestClient(mainmod.app) as c:
        r = c.get(f"/api/tasks/{task_id}")
        assert r.status_code == 200
        assert r.json()["status"] == "failed"
        assert "lost" in r.json()["error_msg"].lower() or "orphan" in r.json()["error_msg"].lower()
```

- [ ] **Step 2: 跑测试,确认失败**

Run: `cd backend && .venv/bin/python -m pytest tests/test_startup_recovery.py -v`
Expected: status stays "running" because lifespan doesn't yet call recover

- [ ] **Step 3: 修改 main.py 的 lifespan**

```python
# backend/service/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI

from service import db as dbmod, models  # noqa: F401
from service.config import settings
from service.routers import api_configs as api_configs_router
from service.routers import categories as categories_router
from service.routers import meta as meta_router
from service.routers import prompt_templates as prompt_templates_router
from service.routers import tasks as tasks_router
from service.routers import wordlists as wordlists_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_dirs()
    dbmod.init_engine()
    dbmod.Base.metadata.create_all(dbmod.engine)
    # Late import — supervisor depends on engine being initialized.
    from service import supervisor
    supervisor.recover_orphaned_running()
    yield


app = FastAPI(title="LLM Data Service", version="0.1.0", lifespan=lifespan)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_configs_router.router)
app.include_router(wordlists_router.router)
app.include_router(prompt_templates_router.router)
app.include_router(categories_router.router)
app.include_router(meta_router.router)
app.include_router(tasks_router.router)
```

- [ ] **Step 4: 跑测试**

Run: `cd backend && .venv/bin/python -m pytest tests/test_startup_recovery.py -v`
Expected: 1 passed

- [ ] **Step 5: 跑全套**

Run: `cd backend && .venv/bin/python -m pytest tests/ 2>&1 | tail -3`
Expected: ~68 passed

- [ ] **Step 6: Commit**

```bash
git add backend/service/main.py backend/tests/test_startup_recovery.py
git commit -m "feat(backend): recover orphaned running tasks on startup"
```

---

### Task 25: Supervisor 周期扫描(后台 task)

**Files:**
- Modify: `backend/service/main.py` (lifespan 加 asyncio.create_task)
- Modify: `backend/service/supervisor.py` (加 async poll loop)
- Create: `backend/tests/test_supervisor_poll.py`

设计:lifespan 启动后启一个 asyncio 后台 task,每 `settings.supervisor_poll_seconds` 秒调用 `recover_orphaned_running()`。lifespan 退出时取消它。

- [ ] **Step 1: 写测试**

```python
# backend/tests/test_supervisor_poll.py
import asyncio

import pytest


@pytest.mark.asyncio
async def test_poll_loop_calls_recover_periodically(monkeypatch):
    from service import supervisor

    called = {"n": 0}

    def fake_recover():
        called["n"] += 1
        return 0

    monkeypatch.setattr(supervisor, "recover_orphaned_running", fake_recover)
    # Override poll interval to 0.05s for test
    from service.config import settings
    monkeypatch.setattr(settings, "supervisor_poll_seconds", 0)  # not used directly
    # We'll call the loop with explicit interval kwarg
    stop = asyncio.Event()
    task = asyncio.create_task(supervisor.poll_loop(interval=0.05, stop=stop))
    await asyncio.sleep(0.2)
    stop.set()
    await task
    assert called["n"] >= 2
```

- [ ] **Step 2: 跑测试,确认失败**

Run: `cd backend && .venv/bin/python -m pytest tests/test_supervisor_poll.py -v`
Expected: AttributeError (poll_loop missing)

- [ ] **Step 3: 加 poll_loop 到 supervisor.py**

Append to `backend/service/supervisor.py`:

```python
import asyncio


async def poll_loop(*, interval: float, stop: asyncio.Event) -> None:
    """Periodically scan for orphaned running tasks until `stop` is set."""
    while not stop.is_set():
        try:
            recover_orphaned_running()
        except Exception:
            pass
        try:
            await asyncio.wait_for(stop.wait(), timeout=interval)
        except asyncio.TimeoutError:
            continue
```

- [ ] **Step 4: 修改 main.py 的 lifespan 启用 poll_loop**

```python
# backend/service/main.py — lifespan section
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_dirs()
    dbmod.init_engine()
    dbmod.Base.metadata.create_all(dbmod.engine)

    from service import supervisor
    supervisor.recover_orphaned_running()

    stop = asyncio.Event()
    poll_task = asyncio.create_task(
        supervisor.poll_loop(interval=settings.supervisor_poll_seconds, stop=stop))
    try:
        yield
    finally:
        stop.set()
        await poll_task
```

- [ ] **Step 5: 跑测试**

Run: `cd backend && .venv/bin/python -m pytest tests/test_supervisor_poll.py -v`
Expected: 1 passed

- [ ] **Step 6: 跑全套**

Run: `cd backend && .venv/bin/python -m pytest tests/ 2>&1 | tail -3`
Expected: ~69 passed

- [ ] **Step 7: Commit**

```bash
git add backend/service/supervisor.py backend/service/main.py backend/tests/test_supervisor_poll.py
git commit -m "feat(backend): periodic orphan scan as asyncio background task"
```

---

## P. 实时推送 (SSE)

### Task 26: `/api/tasks/{id}/stream` SSE 端点

**Files:**
- Create: `backend/service/sse.py`
- Create: `backend/service/routers/tasks_stream.py`
- Modify: `backend/service/main.py`
- Create: `backend/tests/test_sse.py`

设计:
- SSE 用 `sse-starlette` 的 `EventSourceResponse`
- 流的实现:`sse.event_stream(task_id, last_event_id, stop)` — async generator,周期性 (0.5s) 用一个新 session 查 `events_since(task_id, last_event_id)`,把每条 TaskEvent yield 为 SSE event (`{event:"event", id:..., data:json}`)。若 task 已是 `succeeded/failed/aborted` 且无新事件,推一条 `event:"finished"` 后退出。
- 支持 `Last-Event-ID` 头(`EventSourceResponse` 自动暴露)。

- [ ] **Step 1: 写测试**

```python
# backend/tests/test_sse.py
import asyncio
import json

import pytest

from service.schemas import (
    ApiConfigCreate, WordListCreate, PromptTemplateCreate, CategoryCreate
)


def _bootstrap(tmp_path, monkeypatch):
    import sys
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "app.db"))
    for m in [k for k in list(sys.modules) if k == "service" or k.startswith("service.")]:
        sys.modules.pop(m, None)
    import service.config  # noqa: F401
    import service.db as dbmod
    import service.models  # noqa: F401
    dbmod.init_engine()
    dbmod.Base.metadata.create_all(dbmod.engine)
    return dbmod


def _make_task(dbmod):
    from service import crud
    with dbmod.SessionLocal() as s:
        api = crud.create_api_config(s, ApiConfigCreate(
            name="A", base_url="x", api_key="k",
            model_name="m", type="openai"))
        wl = crud.create_wordlist(s, WordListCreate(
            name="w", kind="scenario", items=["a"]))
        wl2 = crud.create_wordlist(s, WordListCreate(
            name="w2", kind="tone", items=["b"]))
        pt = crud.create_prompt_template(s, PromptTemplateCreate(
            name="p", body="x", variables=[]))
        cat = crud.create_category(s, CategoryCreate(
            sample_type="black", name="C", description="",
            prompt_template_id=pt.id, scenario_list_id=wl.id,
            tone_list_id=wl2.id, default_target_count=1))
        t = crud.create_task_snapshot(s, cat.id, api.id, 5, 1, 1, 50, None, None)
        return t.id


@pytest.mark.asyncio
async def test_sse_streams_events_and_closes_on_terminal(tmp_path, monkeypatch):
    dbmod = _bootstrap(tmp_path, monkeypatch)
    task_id = _make_task(dbmod)
    from service import crud, sse

    with dbmod.SessionLocal() as s:
        crud.add_task_event(s, task_id, "started", "start msg")

    received: list[dict] = []
    stop = asyncio.Event()

    async def consumer():
        async for event in sse.event_stream(task_id, last_event_id=0, stop=stop,
                                            poll_interval=0.05):
            received.append(event)
            if event.get("event") == "finished":
                break

    # Append a few events then mark task succeeded
    consumer_task = asyncio.create_task(consumer())
    await asyncio.sleep(0.1)
    with dbmod.SessionLocal() as s:
        crud.add_task_event(s, task_id, "progress", "2/5")
        crud.add_task_event(s, task_id, "progress", "4/5")
        crud.mark_task_finished(s, task_id, "succeeded")
        crud.add_task_event(s, task_id, "finished", "done")
    await asyncio.wait_for(consumer_task, timeout=3)

    # We expect at least the started event, two progress events, and a finished event.
    event_types = [e.get("event", "event") for e in received]
    assert "finished" in event_types
    msgs = [json.loads(e["data"]).get("message", "") for e in received
            if "data" in e]
    assert any("2/5" in m or "4/5" in m for m in msgs)


@pytest.mark.asyncio
async def test_sse_respects_last_event_id(tmp_path, monkeypatch):
    dbmod = _bootstrap(tmp_path, monkeypatch)
    task_id = _make_task(dbmod)
    from service import crud, sse

    with dbmod.SessionLocal() as s:
        e1 = crud.add_task_event(s, task_id, "started", "s")
        e2 = crud.add_task_event(s, task_id, "progress", "1/5")

    received: list[dict] = []
    stop = asyncio.Event()

    async def consumer():
        async for evt in sse.event_stream(task_id, last_event_id=e1.id,
                                          stop=stop, poll_interval=0.05):
            received.append(evt)
            stop.set()
            break

    await asyncio.wait_for(consumer(), timeout=2)
    assert len(received) == 1
    assert int(received[0]["id"]) == e2.id
```

- [ ] **Step 2: 跑测试,确认失败**

Run: `cd backend && .venv/bin/python -m pytest tests/test_sse.py -v`
Expected: ImportError

- [ ] **Step 3: 实现 sse.py**

```python
# backend/service/sse.py
import asyncio
import json
from typing import AsyncIterator

from service import crud, db as dbmod, models


_TERMINAL = {"succeeded", "failed", "aborted"}


async def event_stream(task_id: int, *, last_event_id: int = 0,
                       stop: asyncio.Event | None = None,
                       poll_interval: float = 0.5) -> AsyncIterator[dict]:
    """Async generator yielding SSE-shaped dicts:
       {"event": "event"|"finished", "id": "<int>", "data": "<json>"}.
    Stops when task reaches terminal status and no more new events, or when
    `stop` is set."""
    if dbmod.SessionLocal is None:
        dbmod.init_engine()
        dbmod.Base.metadata.create_all(dbmod.engine)

    stop = stop or asyncio.Event()
    cursor = last_event_id

    while not stop.is_set():
        new_events: list[models.TaskEvent] = []
        terminal_status: str | None = None
        with dbmod.SessionLocal() as s:
            new_events = crud.events_since(s, task_id, since_id=cursor, limit=500)
            t = crud.get_task(s, task_id)
            if t is not None and t.status in _TERMINAL:
                terminal_status = t.status

        for ev in new_events:
            cursor = ev.id
            yield {
                "event": "event",
                "id": str(ev.id),
                "data": json.dumps({
                    "type": ev.type,
                    "message": ev.message,
                    "ts": ev.ts,
                }, ensure_ascii=False),
            }

        if terminal_status is not None:
            # Already past any final TaskEvent rows. Emit terminal signal.
            yield {
                "event": "finished",
                "id": str(cursor),
                "data": json.dumps({"status": terminal_status}),
            }
            return

        try:
            await asyncio.wait_for(stop.wait(), timeout=poll_interval)
        except asyncio.TimeoutError:
            continue
```

- [ ] **Step 4: 实现 routers/tasks_stream.py**

```python
# backend/service/routers/tasks_stream.py
import asyncio

from fastapi import APIRouter, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from service import sse, crud, db as dbmod

router = APIRouter(prefix="/api/tasks", tags=["tasks-stream"])


@router.get("/{id_}/stream")
async def stream(id_: int, request: Request) -> EventSourceResponse:
    # 404 if missing
    if dbmod.SessionLocal is None:
        dbmod.init_engine()
    with dbmod.SessionLocal() as s:
        if crud.get_task(s, id_) is None:
            raise HTTPException(404, "not found")
    last_id_header = request.headers.get("last-event-id")
    last_id = int(last_id_header) if last_id_header and last_id_header.isdigit() else 0

    stop = asyncio.Event()

    async def proxy():
        async for evt in sse.event_stream(id_, last_event_id=last_id, stop=stop):
            if await request.is_disconnected():
                stop.set()
                break
            yield evt

    return EventSourceResponse(proxy())
```

- [ ] **Step 5: 注册路由**

In `backend/service/main.py`:
```python
from service.routers import tasks_stream as tasks_stream_router
```
and:
```python
app.include_router(tasks_stream_router.router)
```

- [ ] **Step 6: 跑测试**

Run: `cd backend && .venv/bin/python -m pytest tests/test_sse.py -v`
Expected: 2 passed

- [ ] **Step 7: 跑全套**

Run: `cd backend && .venv/bin/python -m pytest tests/ 2>&1 | tail -3`
Expected: ~71 passed

- [ ] **Step 8: Commit**

```bash
git add backend/service/sse.py backend/service/routers/tasks_stream.py backend/service/main.py backend/tests/test_sse.py
git commit -m "feat(backend): SSE stream for live task progress"
```

---

## Q. 静态文件 & 数据迁移

### Task 27: 静态文件托管 (React `dist/`)

**Files:**
- Create: `backend/service/static.py`
- Modify: `backend/service/main.py`
- Create: `backend/tests/test_static.py`

设计:
- 由 `STATIC_DIR` 环境变量指定路径(默认 `frontend/dist`)
- 如果目录存在 → `app.mount("/", StaticFiles(directory=..., html=True))`,并加一个 fallback route 把 `index.html` 返回给所有非 `/api` 路径(支持 React Router 的 BrowserRouter 刷新)
- 如果目录不存在 → 跳过挂载,只保留 API。便于纯后端开发

- [ ] **Step 1: 写测试**

```python
# backend/tests/test_static.py
import sys
from pathlib import Path

from fastapi.testclient import TestClient


def test_static_skipped_when_dir_missing(tmp_path, monkeypatch, client):
    # When dist doesn't exist, /healthz still works and /any unknown path is 404
    r = client.get("/healthz")
    assert r.status_code == 200
    r = client.get("/some-random-page")
    assert r.status_code == 404


def test_static_mounted_when_dir_present(tmp_path, monkeypatch):
    dist = tmp_path / "frontend_dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>app</html>", encoding="utf-8")
    (dist / "assets").mkdir()
    (dist / "assets" / "main.js").write_text("/* js */", encoding="utf-8")

    monkeypatch.setenv("STATIC_DIR", str(dist))
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "app.db"))
    for m in [k for k in list(sys.modules) if k == "service" or k.startswith("service.")]:
        sys.modules.pop(m, None)
    import service.config  # noqa: F401
    import service.db  # noqa: F401
    import service.models  # noqa: F401
    import service.main as mainmod

    with TestClient(mainmod.app) as c:
        # / serves index.html
        r = c.get("/")
        assert r.status_code == 200
        assert "app" in r.text
        # Assets served
        r = c.get("/assets/main.js")
        assert r.status_code == 200
        assert "/* js */" in r.text
        # /some/path (SPA route) falls back to index.html
        r = c.get("/tasks/142")
        assert r.status_code == 200
        assert "app" in r.text
        # /api/... NOT redirected to index
        r = c.get("/api/sample-types")
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("application/json")
```

- [ ] **Step 2: 跑测试,确认失败**

Run: `cd backend && .venv/bin/python -m pytest tests/test_static.py -v`
Expected: `test_static_mounted_when_dir_present` fails (no mount yet)

- [ ] **Step 3: 实现 static.py**

```python
# backend/service/static.py
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


def mount_static(app: FastAPI) -> bool:
    """Mount the React dist directory if it exists. Returns whether mounted."""
    static_dir_env = os.environ.get("STATIC_DIR", "frontend/dist")
    dist = Path(static_dir_env).resolve()
    if not (dist.is_dir() and (dist / "index.html").is_file()):
        return False

    # Serve real files under /assets and any other top-level static dir.
    # For unknown paths, fall back to index.html (SPA history mode).
    index_file = dist / "index.html"

    @app.get("/", include_in_schema=False)
    def _root() -> FileResponse:
        return FileResponse(str(index_file))

    @app.get("/{full_path:path}", include_in_schema=False)
    def _spa_fallback(full_path: str) -> FileResponse:
        # API paths are matched by their routers first due to route order.
        if full_path.startswith("api/") or full_path.startswith("healthz"):
            raise HTTPException(404)
        candidate = (dist / full_path).resolve()
        if candidate.is_file() and dist in candidate.parents:
            return FileResponse(str(candidate))
        return FileResponse(str(index_file))

    return True
```

- [ ] **Step 4: 在 main.py 调用 mount_static**

In `backend/service/main.py`, AT THE END after all `include_router` calls:

```python
from service.static import mount_static
mount_static(app)
```

- [ ] **Step 5: 跑测试**

Run: `cd backend && .venv/bin/python -m pytest tests/test_static.py -v`
Expected: 2 passed

- [ ] **Step 6: 跑全套**

Run: `cd backend && .venv/bin/python -m pytest tests/ 2>&1 | tail -3`
Expected: ~73 passed

- [ ] **Step 7: Commit**

```bash
git add backend/service/static.py backend/service/main.py backend/tests/test_static.py
git commit -m "feat(backend): mount React dist with SPA fallback when present"
```

---

### Task 28: 从 `llm-data-create/` 灌种子数据

**Files:**
- Create: `backend/scripts/__init__.py`
- Create: `backend/scripts/seed_from_legacy.py`
- Create: `backend/tests/test_seed_from_legacy.py`

设计:CLI 脚本,扫 `../llm-data-create/` 下三类源文件:
- `black_data/run_A*.py` — 每个文件解析 `CURRENT_CATEGORY` / `SCENARIOS` / `TONES` / `META_PROMPT_TEMPLATE` / `API_URL` / `HEADERS` / `MODEL_NAME` / `TARGET_COUNT`
- `gray_data/code/generate_gray_deepseek.py` — `GRAY_SCENARIOS` / `TONES` / `META_TEMPLATES` / `PROXY_API_KEY` / `base_url` / `MODEL_NAME` / `TARGET_COUNT`
- `white_data/code/generate_white_deepseek.py` — 同 gray

把扫到的内容 upsert 成 DB 行(因为我们之前给 WordList.name + Category(sample_type, name) 加了 unique,重跑安全)。

实现用 `ast.parse + ast.walk` 提取模块顶层赋值的字面量,而不是 `exec`。模板字符串若有多条(灰白的 META_TEMPLATES 是 list)→ 拼成单个 PromptTemplate,在 body 里用 `[VARIANT N]` 标记分段。

⚠️ 由于这是一次性工具,容错按「跳过并日志」处理 — 单个脚本解析失败不应中断整体。

- [ ] **Step 1: 写测试**

```python
# backend/tests/test_seed_from_legacy.py
import sys

import pytest


_SAMPLE_BLACK = '''
import requests
API_URL = "http://api.example.com/v1/chat/completions"
HEADERS = {"Content-Type": "application/json",
           "Authorization": "Bearer test-key-123"}
MODEL_NAME = "qwen3:32b"

CURRENT_CATEGORY = "A.1.x Sample Category"
OUTPUT_FILE = "data/A1_x_Black_Samples.csv"
TARGET_COUNT = 1234

SCENARIOS = ["scenario one", "scenario two"]
TONES = ["tone one", "tone two"]

META_PROMPT_TEMPLATE = """
You are an annotator. Category: {category}, scenario: {scenario}, tone: {tone}.
Generate {batch_size} samples.
"""
'''


def test_seed_parses_black_script_and_inserts(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "app.db"))
    for m in [k for k in list(sys.modules) if k == "service" or k.startswith("service.")]:
        sys.modules.pop(m, None)
    import service.config  # noqa: F401
    import service.db as dbmod
    import service.models  # noqa: F401
    dbmod.init_engine()
    dbmod.Base.metadata.create_all(dbmod.engine)

    # Write a synthetic legacy source tree
    legacy_root = tmp_path / "llm-data-create"
    (legacy_root / "black_data").mkdir(parents=True)
    (legacy_root / "black_data" / "run_A1x.py").write_text(_SAMPLE_BLACK, encoding="utf-8")

    from scripts.seed_from_legacy import seed
    result = seed(legacy_root=legacy_root)
    assert result.api_configs == 1
    assert result.wordlists == 2     # SCENARIOS + TONES
    assert result.prompt_templates == 1
    assert result.categories == 1
    assert result.skipped == []

    from service import models
    with dbmod.SessionLocal() as s:
        cats = s.query(models.Category).all()
        assert len(cats) == 1
        assert cats[0].name == "A.1.x Sample Category"
        assert cats[0].sample_type == "black"
        assert cats[0].default_target_count == 1234

        wls = s.query(models.WordList).all()
        kinds = {w.kind: w for w in wls}
        assert kinds["scenario"].name.endswith("scenarios")
        assert kinds["tone"].name.endswith("tones")

        tpls = s.query(models.PromptTemplate).all()
        assert "{scenario}" in tpls[0].body
        assert "{tone}" in tpls[0].body


def test_seed_idempotent_rerun(tmp_path, monkeypatch):
    """Running seed twice should not create duplicates (unique constraints)."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "app.db"))
    for m in [k for k in list(sys.modules) if k == "service" or k.startswith("service.")]:
        sys.modules.pop(m, None)
    import service.config  # noqa: F401
    import service.db as dbmod
    import service.models  # noqa: F401
    dbmod.init_engine()
    dbmod.Base.metadata.create_all(dbmod.engine)

    legacy_root = tmp_path / "llm-data-create"
    (legacy_root / "black_data").mkdir(parents=True)
    (legacy_root / "black_data" / "run_A1x.py").write_text(_SAMPLE_BLACK, encoding="utf-8")

    from scripts.seed_from_legacy import seed
    seed(legacy_root=legacy_root)
    seed(legacy_root=legacy_root)   # second run

    from service import models
    with dbmod.SessionLocal() as s:
        assert s.query(models.Category).count() == 1
        assert s.query(models.WordList).count() == 2
        assert s.query(models.PromptTemplate).count() == 1
        assert s.query(models.ApiConfig).count() == 1


def test_seed_skips_unparseable_file(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "app.db"))
    for m in [k for k in list(sys.modules) if k == "service" or k.startswith("service.")]:
        sys.modules.pop(m, None)
    import service.config  # noqa: F401
    import service.db as dbmod
    import service.models  # noqa: F401
    dbmod.init_engine()
    dbmod.Base.metadata.create_all(dbmod.engine)

    legacy_root = tmp_path / "llm-data-create"
    (legacy_root / "black_data").mkdir(parents=True)
    (legacy_root / "black_data" / "run_bad.py").write_text(
        "this is not python syntax !!!!\n", encoding="utf-8")
    (legacy_root / "black_data" / "run_A1x.py").write_text(
        _SAMPLE_BLACK, encoding="utf-8")

    from scripts.seed_from_legacy import seed
    result = seed(legacy_root=legacy_root)
    assert result.categories == 1
    assert any("run_bad.py" in s for s in result.skipped)
```

- [ ] **Step 2: 跑测试,确认失败**

Run: `cd backend && .venv/bin/python -m pytest tests/test_seed_from_legacy.py -v`
Expected: ImportError (scripts package not found)

- [ ] **Step 3: 实现 seed_from_legacy.py**

```python
# backend/scripts/__init__.py
```

```python
# backend/scripts/seed_from_legacy.py
"""One-shot migration: read llm-data-create/ scripts → populate the DB.

Idempotent: re-runs will not create duplicates because:
  - ApiConfig.name is unique
  - WordList.name is unique
  - PromptTemplate.name is unique
  - Category(sample_type, name) is unique
"""
import argparse
import ast
import json
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy.exc import IntegrityError

from service import crud, db as dbmod, models
from service.schemas import (
    ApiConfigCreate, WordListCreate, PromptTemplateCreate, CategoryCreate
)


@dataclass
class SeedResult:
    api_configs: int = 0
    wordlists: int = 0
    prompt_templates: int = 0
    categories: int = 0
    skipped: list[str] = field(default_factory=list)


def _module_top_level_literals(path: Path) -> dict:
    """Return a dict of top-level NAME = literal assignments. Skip any
    statement that contains non-literal expressions (calls, attribute access,
    etc.) — we only want simple constants and list/dict of literals."""
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(path))
    out: dict = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        name = node.targets[0].id
        try:
            value = ast.literal_eval(node.value)
        except (ValueError, SyntaxError):
            continue
        out[name] = value
    return out


def _ensure_api_config(db, *, name, base_url, api_key, model_name, api_type) -> int:
    obj = db.query(models.ApiConfig).filter_by(name=name).one_or_none()
    if obj is not None:
        return obj.id
    obj = crud.create_api_config(db, ApiConfigCreate(
        name=name, base_url=base_url, api_key=api_key,
        model_name=model_name, type=api_type))
    return obj.id


def _ensure_wordlist(db, *, name, kind, items) -> int:
    obj = db.query(models.WordList).filter_by(name=name).one_or_none()
    if obj is not None:
        return obj.id
    obj = crud.create_wordlist(db, WordListCreate(name=name, kind=kind, items=items))
    return obj.id


def _ensure_template(db, *, name, body, variables) -> int:
    obj = db.query(models.PromptTemplate).filter_by(name=name).one_or_none()
    if obj is not None:
        return obj.id
    obj = crud.create_prompt_template(db, PromptTemplateCreate(
        name=name, body=body, variables=variables))
    return obj.id


def _ensure_category(db, *, sample_type, name, prompt_template_id,
                     scenario_list_id, tone_list_id, default_target_count) -> int:
    obj = db.query(models.Category).filter_by(
        sample_type=sample_type, name=name).one_or_none()
    if obj is not None:
        return obj.id
    obj = crud.create_category(db, CategoryCreate(
        sample_type=sample_type, name=name, description="",
        prompt_template_id=prompt_template_id,
        scenario_list_id=scenario_list_id,
        tone_list_id=tone_list_id,
        default_target_count=default_target_count))
    return obj.id


def _seed_black_file(db, path: Path, result: SeedResult) -> None:
    consts = _module_top_level_literals(path)
    cat_name = consts.get("CURRENT_CATEGORY")
    scenarios = consts.get("SCENARIOS")
    tones = consts.get("TONES")
    body = consts.get("META_PROMPT_TEMPLATE")
    api_url = consts.get("API_URL")
    headers = consts.get("HEADERS")
    model_name = consts.get("MODEL_NAME")
    target_count = consts.get("TARGET_COUNT", 0)

    if not all([cat_name, scenarios, tones, body, api_url, headers, model_name]):
        result.skipped.append(f"{path.name}: missing one of required constants")
        return

    auth = headers.get("Authorization", "") if isinstance(headers, dict) else ""
    api_key = auth.split(" ", 1)[1] if auth.startswith("Bearer ") else auth

    api_id = _ensure_api_config(
        db, name=f"black/{model_name}", base_url=api_url.rsplit("/v1/", 1)[0],
        api_key=api_key, model_name=model_name, api_type="raw")
    s_id = _ensure_wordlist(db, name=f"{path.stem}-scenarios",
                            kind="scenario", items=list(scenarios))
    t_id = _ensure_wordlist(db, name=f"{path.stem}-tones",
                            kind="tone", items=list(tones))
    tpl_id = _ensure_template(
        db, name=f"{path.stem}-template", body=body,
        variables=["category", "scenario", "tone", "batch_size"])
    _ensure_category(
        db, sample_type="black", name=cat_name,
        prompt_template_id=tpl_id, scenario_list_id=s_id, tone_list_id=t_id,
        default_target_count=int(target_count) if target_count else 0)
    result.api_configs += 1 if api_id else 0
    result.wordlists += 2
    result.prompt_templates += 1
    result.categories += 1


def seed(*, legacy_root: Path) -> SeedResult:
    if dbmod.SessionLocal is None:
        dbmod.init_engine()
        dbmod.Base.metadata.create_all(dbmod.engine)

    result = SeedResult()
    # Re-count after the run by querying the DB rather than incrementing,
    # so idempotent re-runs do not show inflated numbers.
    pre = _counts()

    with dbmod.SessionLocal() as db:
        # Black samples
        black_dir = legacy_root / "black_data"
        if black_dir.is_dir():
            for p in sorted(black_dir.glob("run_*.py")):
                try:
                    _seed_black_file(db, p, result)
                except (SyntaxError, ValueError, IntegrityError) as e:
                    db.rollback()
                    result.skipped.append(f"{p.name}: {type(e).__name__}: {e}")

        # Gray + white: similar shape (multiple META_TEMPLATES → join with marker)
        for sample_type, rel in [("gray", "gray_data/code/generate_gray_deepseek.py"),
                                 ("white", "white_data/code/generate_white_deepseek.py")]:
            f = legacy_root / rel
            if not f.is_file():
                continue
            try:
                _seed_gray_white_file(db, f, sample_type, result)
            except (SyntaxError, ValueError, IntegrityError) as e:
                db.rollback()
                result.skipped.append(f"{f.name}: {type(e).__name__}: {e}")

    post = _counts()
    result.api_configs = post["api_config"] - pre["api_config"]
    result.wordlists = post["wordlist"] - pre["wordlist"]
    result.prompt_templates = post["prompt_template"] - pre["prompt_template"]
    result.categories = post["category"] - pre["category"]
    return result


def _seed_gray_white_file(db, path: Path, sample_type: str, result: SeedResult) -> None:
    consts = _module_top_level_literals(path)
    scenarios = consts.get("GRAY_SCENARIOS") or consts.get("WHITE_SCENARIOS") or consts.get("SCENARIOS")
    tones = consts.get("TONES")
    templates = consts.get("META_TEMPLATES")
    api_key = consts.get("PROXY_API_KEY") or consts.get("DEEPSEEK_API_KEY")
    base_url = consts.get("base_url") or consts.get("BASE_URL") or "https://api.deepseek.com"
    model_name = consts.get("MODEL_NAME")
    target_count = consts.get("TARGET_COUNT", 0)

    if not all([scenarios, tones, templates, api_key, model_name]):
        result.skipped.append(f"{path.name}: missing one of required constants")
        return

    body = "\n\n[VARIANT-BREAK]\n\n".join(str(t) for t in templates)

    _ensure_api_config(
        db, name=f"{sample_type}/{model_name}",
        base_url=base_url, api_key=api_key,
        model_name=model_name, api_type="openai")
    s_id = _ensure_wordlist(db, name=f"{sample_type}-scenarios",
                            kind="scenario", items=list(scenarios))
    t_id = _ensure_wordlist(db, name=f"{sample_type}-tones",
                            kind="tone", items=list(tones))
    tpl_id = _ensure_template(
        db, name=f"{sample_type}-template", body=body,
        variables=["scenario", "tone", "batch_size"])
    _ensure_category(
        db, sample_type=sample_type, name=f"{sample_type}-default",
        prompt_template_id=tpl_id, scenario_list_id=s_id, tone_list_id=t_id,
        default_target_count=int(target_count) if target_count else 0)


def _counts() -> dict:
    with dbmod.SessionLocal() as s:
        return {
            "api_config": s.query(models.ApiConfig).count(),
            "wordlist": s.query(models.WordList).count(),
            "prompt_template": s.query(models.PromptTemplate).count(),
            "category": s.query(models.Category).count(),
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--legacy-root", type=Path,
                        default=Path("../llm-data-create"))
    args = parser.parse_args()
    result = seed(legacy_root=args.legacy_root)
    print(json.dumps({
        "api_configs": result.api_configs,
        "wordlists": result.wordlists,
        "prompt_templates": result.prompt_templates,
        "categories": result.categories,
        "skipped": result.skipped,
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 跑测试**

Run: `cd backend && .venv/bin/python -m pytest tests/test_seed_from_legacy.py -v`
Expected: 3 passed

- [ ] **Step 5: 跑全套**

Run: `cd backend && .venv/bin/python -m pytest tests/ 2>&1 | tail -3`
Expected: ~76 passed

- [ ] **Step 6: Commit**

```bash
git add backend/scripts/__init__.py backend/scripts/seed_from_legacy.py backend/tests/test_seed_from_legacy.py
git commit -m "feat(backend): one-shot seed script from llm-data-create legacy"
```

---

## 完成检查

Part 2 全部 15 个 task 完成后,应当:

- 后端 76+ 测试通过
- `cd backend && .venv/bin/python -m uvicorn service.main:app --port 8000` 可直接启动
- `curl http://localhost:8000/api/sample-types` 返回 black/gray/white + 各自分类数
- 创建一个 Task → spawn worker subprocess → 在 `/api/tasks/{id}/stream` 可见实时进度 → 完成后 `/api/tasks/{id}/download` 拿到 CSV
- `python -m scripts.seed_from_legacy --legacy-root ../llm-data-create` 把 33 个黑分类 + 灰白默认分类一次性灌入 DB
- API 启动时打印 orphan 恢复数;运行期 30 秒一次后台扫描
- 前端 `frontend/dist/` 若存在,同源访问 `http://localhost:8000/` 直接出 SPA

完成后,在 main 上合一个 PR,然后开始 Part 3 (前端)。
