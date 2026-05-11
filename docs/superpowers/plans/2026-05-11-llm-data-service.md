# LLM 样本数据生产服务 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `llm-data-create/` 里硬编码的黑/灰/白样本生成脚本,做成一个内网部署的前后端服务,所有配置 UI 可改,任务可启停续跑。

**Architecture:** FastAPI 进程 + 每个任务一个 Python 子进程 Worker + SQLite (WAL) + React/Ant Design SPA。Worker 只写 DB,API 进程内置 watcher 把变更通过 SSE 推给前端。同源部署(FastAPI 静态托管打包后的 React)。

**Tech Stack:** Python 3.11 / FastAPI / SQLAlchemy 2 / SQLite / sse-starlette / openai SDK / requests / pytest / React 18 / TypeScript / Ant Design 5 / Vite

**Spec:** `docs/superpowers/specs/2026-05-11-llm-data-service-design.md`

---

## 阶段总览(本文件:阶段 A-D Task 1-13)

- **A. 后端骨架** (Task 1-3) ✍ 本文件
- **B. 数据层** (Task 4-7) ✍ 本文件
- **C. 共用工具** (Task 8-10) ✍ 本文件
- **D. 配置 REST · 部分** (Task 11-13) ✍ 本文件
- **D. 配置 REST · 收尾 (Task 14-15:PromptTemplate / Category 路由 + 校验 + /test 端点)** → 续篇 plan
- **E. Worker 核心** (Task 16-19) → 续篇 plan
- **F. 任务编排** (Task 20-23) → 续篇 plan
- **G. 实时推送 (SSE)** (Task 24-25) → 续篇 plan
- **H. 启动恢复 & 静态托管** (Task 26-27) → 续篇 plan
- **I. 数据迁移** (Task 28) → 续篇 plan
- **J. 前端骨架** (Task 29-31) → 续篇 plan
- **K. 前端页面** (Task 32-38) → 续篇 plan
- **L. Docker & 文档** (Task 39-40) → 续篇 plan

> 注:为避免单 plan 过长(每个 task 都包含完整 TDD 代码),Task 14 以后另起 plan
> 文件,在本文件第一阶段完成后再写下一份。续篇 plan 在 Task 13 执行完后由
> writing-plans skill 接续生成。

---

## A. 后端骨架

### Task 1: 创建后端目录与依赖

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/service/__init__.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`

- [ ] **Step 1: 写 pyproject.toml**

```toml
# backend/pyproject.toml
[project]
name = "llm-data-service"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.115",
  "uvicorn[standard]>=0.30",
  "sqlalchemy>=2.0",
  "pydantic>=2.7",
  "sse-starlette>=2.1",
  "openai>=1.40",
  "requests>=2.32",
  "python-multipart>=0.0.9",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
  "pytest-asyncio>=0.23",
  "httpx>=0.27",
]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
asyncio_mode = "auto"
```

- [ ] **Step 2: 创建 service 包占位**

```python
# backend/service/__init__.py
"""LLM data service backend package."""
```

- [ ] **Step 3: 创建 tests 包占位与 conftest**

```python
# backend/tests/__init__.py
```

```python
# backend/tests/conftest.py
"""Shared pytest fixtures (filled in subsequent tasks)."""
```

- [ ] **Step 4: 安装依赖并验证**

Run: `cd backend && pip install -e ".[dev]" && python -c "import fastapi, sqlalchemy, sse_starlette, openai" && pytest --collect-only`
Expected: 安装成功;collect 输出 0 tests 但无报错。

- [ ] **Step 5: Commit**

```bash
git add backend/pyproject.toml backend/service/__init__.py backend/tests/__init__.py backend/tests/conftest.py
git commit -m "build(backend): bootstrap project with FastAPI + SQLAlchemy deps"
```

---

### Task 2: 配置模块 (路径常量)

**Files:**
- Create: `backend/service/config.py`
- Create: `backend/tests/test_config.py`

- [ ] **Step 1: 写测试**

```python
# backend/tests/test_config.py
from pathlib import Path
from service.config import settings

def test_settings_defaults_resolve_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "app.db"))
    from importlib import reload
    import service.config as cfg
    reload(cfg)
    assert cfg.settings.data_dir == Path(tmp_path / "data")
    assert cfg.settings.log_dir == Path(tmp_path / "logs")
    assert cfg.settings.db_path == Path(tmp_path / "app.db")

def test_settings_ensure_dirs_creates_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "app.db"))
    from importlib import reload
    import service.config as cfg
    reload(cfg)
    cfg.settings.ensure_dirs()
    assert (tmp_path / "data").is_dir()
    assert (tmp_path / "logs").is_dir()
```

- [ ] **Step 2: 跑测试,确认失败**

Run: `cd backend && pytest tests/test_config.py -v`
Expected: ImportError (service.config 不存在)

- [ ] **Step 3: 实现 config.py**

```python
# backend/service/config.py
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    log_dir: Path
    db_path: Path
    progress_flush_min: int = 50
    progress_flush_batch_multiplier: int = 5
    max_workers_hard_limit: int = 50
    batch_size_hard_limit: int = 100
    preview_rows: int = 200
    supervisor_poll_seconds: int = 30
    abort_grace_seconds: int = 2

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def task_dir(self, task_id: int) -> Path:
        return self.data_dir / f"task-{task_id}"

    def task_log(self, task_id: int) -> Path:
        return self.log_dir / f"task-{task_id}.log"


def _load() -> Settings:
    return Settings(
        data_dir=Path(os.environ.get("DATA_DIR", "data")).resolve(),
        log_dir=Path(os.environ.get("LOG_DIR", "logs")).resolve(),
        db_path=Path(os.environ.get("DB_PATH", "app.db")).resolve(),
    )


settings = _load()
```

- [ ] **Step 4: 跑测试,确认通过**

Run: `cd backend && pytest tests/test_config.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add backend/service/config.py backend/tests/test_config.py
git commit -m "feat(backend): add Settings with env-driven paths and tunables"
```

---

### Task 3: FastAPI app 入口 + health 端点

**Files:**
- Create: `backend/service/main.py`
- Create: `backend/tests/test_health.py`

- [ ] **Step 1: 写测试**

```python
# backend/tests/test_health.py
from fastapi.testclient import TestClient
from service.main import app


def test_healthz_returns_ok():
    client = TestClient(app)
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
```

- [ ] **Step 2: 跑测试,确认失败**

Run: `cd backend && pytest tests/test_health.py -v`
Expected: ImportError (service.main 不存在)

- [ ] **Step 3: 实现 main.py 的最小版本**

```python
# backend/service/main.py
from fastapi import FastAPI

from service.config import settings

app = FastAPI(title="LLM Data Service", version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    settings.ensure_dirs()


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 4: 跑测试,确认通过**

Run: `cd backend && pytest tests/test_health.py -v`
Expected: 1 passed

- [ ] **Step 5: 手动验证 uvicorn 起得来**

Run: `cd backend && uvicorn service.main:app --port 8765 &` 然后 `curl http://localhost:8765/healthz`,完事 `kill %1`
Expected: 看到 `{"status":"ok"}`

- [ ] **Step 6: Commit**

```bash
git add backend/service/main.py backend/tests/test_health.py
git commit -m "feat(backend): scaffold FastAPI app with /healthz"
```

---

## B. 数据层

### Task 4: SQLAlchemy engine + WAL 模式

**Files:**
- Create: `backend/service/db.py`
- Create: `backend/tests/test_db.py`

- [ ] **Step 1: 写测试**

```python
# backend/tests/test_db.py
from sqlalchemy import text
from service.db import create_engine_for_path, init_engine, SessionLocal


def test_create_engine_enables_wal(tmp_path):
    db = tmp_path / "x.db"
    engine = create_engine_for_path(db)
    with engine.connect() as conn:
        mode = conn.execute(text("PRAGMA journal_mode")).scalar()
    assert mode.lower() == "wal"


def test_init_engine_sets_module_session(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "y.db"))
    from importlib import reload
    import service.config as cfg; reload(cfg)
    import service.db as dbmod; reload(dbmod)
    dbmod.init_engine()
    with dbmod.SessionLocal() as s:
        assert s.execute(text("SELECT 1")).scalar() == 1
```

- [ ] **Step 2: 跑测试,确认失败**

Run: `cd backend && pytest tests/test_db.py -v`
Expected: ImportError

- [ ] **Step 3: 实现 db.py**

```python
# backend/service/db.py
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from service.config import settings


class Base(DeclarativeBase):
    pass


engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None  # set by init_engine


def create_engine_for_path(db_path: Path) -> Engine:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    eng = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False, "timeout": 30},
        future=True,
    )

    @event.listens_for(eng, "connect")
    def _set_pragmas(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute("PRAGMA synchronous=NORMAL;")
        cur.execute("PRAGMA foreign_keys=ON;")
        cur.close()

    # Force one connection to apply pragmas immediately
    with eng.connect() as _:
        pass
    return eng


def init_engine() -> None:
    global engine, SessionLocal
    engine = create_engine_for_path(settings.db_path)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
```

- [ ] **Step 4: 跑测试,确认通过**

Run: `cd backend && pytest tests/test_db.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add backend/service/db.py backend/tests/test_db.py
git commit -m "feat(backend): SQLAlchemy engine factory with WAL pragma"
```

---

### Task 5: ORM 模型(7 张表)

**Files:**
- Create: `backend/service/models.py`
- Create: `backend/tests/test_models.py`

- [ ] **Step 1: 写测试**

```python
# backend/tests/test_models.py
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
```

- [ ] **Step 2: 跑测试,确认失败**

Run: `cd backend && pytest tests/test_models.py -v`
Expected: ImportError (service.models 不存在)

- [ ] **Step 3: 实现 models.py**

```python
# backend/service/models.py
from sqlalchemy import (
    Integer, String, Text, ForeignKey, Index
)
from sqlalchemy.orm import Mapped, mapped_column

from service.db import Base


class ApiConfig(Base):
    __tablename__ = "api_config"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    base_url: Mapped[str] = mapped_column(String(500))
    api_key: Mapped[str] = mapped_column(String(500))
    model_name: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(20))  # 'openai' | 'raw'
    created_at: Mapped[str] = mapped_column(String(40), default="")
    updated_at: Mapped[str] = mapped_column(String(40), default="")


class WordList(Base):
    __tablename__ = "wordlist"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(40))  # scenario|tone|other
    items_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String(40), default="")
    updated_at: Mapped[str] = mapped_column(String(40), default="")


class PromptTemplate(Base):
    __tablename__ = "prompt_template"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    body: Mapped[str] = mapped_column(Text)
    variables_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String(40), default="")
    updated_at: Mapped[str] = mapped_column(String(40), default="")


class Category(Base):
    __tablename__ = "category"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sample_type: Mapped[str] = mapped_column(String(20))  # black|gray|white
    name: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")
    prompt_template_id: Mapped[int] = mapped_column(ForeignKey("prompt_template.id"))
    scenario_list_id: Mapped[int] = mapped_column(ForeignKey("wordlist.id"))
    tone_list_id: Mapped[int] = mapped_column(ForeignKey("wordlist.id"))
    default_target_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[str] = mapped_column(String(40), default="")
    updated_at: Mapped[str] = mapped_column(String(40), default="")


class Task(Base):
    __tablename__ = "task"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("category.id"))
    api_config_id: Mapped[int] = mapped_column(ForeignKey("api_config.id"))

    snapshot_sample_type: Mapped[str] = mapped_column(String(20))
    snapshot_category_name: Mapped[str] = mapped_column(String(300))
    snapshot_prompt_body: Mapped[str] = mapped_column(Text)
    snapshot_scenario_items_json: Mapped[str] = mapped_column(Text)
    snapshot_tone_items_json: Mapped[str] = mapped_column(Text)
    snapshot_api_base_url: Mapped[str] = mapped_column(String(500))
    snapshot_api_key: Mapped[str] = mapped_column(String(500))
    snapshot_model_name: Mapped[str] = mapped_column(String(200))
    snapshot_api_type: Mapped[str] = mapped_column(String(20))

    target_count: Mapped[int] = mapped_column(Integer)
    batch_size: Mapped[int] = mapped_column(Integer)
    max_workers: Mapped[int] = mapped_column(Integer)
    max_per_file: Mapped[int] = mapped_column(Integer)

    status: Mapped[str] = mapped_column(String(20))  # pending|running|succeeded|failed|aborted
    progress_current: Mapped[int] = mapped_column(Integer, default=0)
    progress_total: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[str] = mapped_column(String(40))
    started_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    finished_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    error_msg: Mapped[str | None] = mapped_column(Text, nullable=True)

    output_dir: Mapped[str] = mapped_column(String(500))
    worker_pid: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_by_label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    resume_from_task_id: Mapped[int | None] = mapped_column(
        ForeignKey("task.id"), nullable=True
    )


Index("ix_task_status", Task.status)
Index("ix_task_created_at", Task.created_at)
Index("ix_task_category_id", Task.category_id)
Index("ix_task_api_config_id", Task.api_config_id)


class TaskEvent(Base):
    __tablename__ = "task_event"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("task.id"))
    ts: Mapped[str] = mapped_column(String(40))
    type: Mapped[str] = mapped_column(String(40))
    message: Mapped[str] = mapped_column(Text, default="")


Index("ix_task_event_task_id_id", TaskEvent.task_id, TaskEvent.id)
```

- [ ] **Step 4: 跑测试,确认通过**

Run: `cd backend && pytest tests/test_models.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add backend/service/models.py backend/tests/test_models.py
git commit -m "feat(backend): ORM models for configs, categories, tasks, events"
```

---

### Task 6: Pydantic schemas

**Files:**
- Create: `backend/service/schemas.py`
- Create: `backend/tests/test_schemas.py`

- [ ] **Step 1: 写测试**

```python
# backend/tests/test_schemas.py
import pytest
from pydantic import ValidationError

from service.schemas import (
    ApiConfigCreate, WordListCreate, PromptTemplateCreate,
    CategoryCreate, TaskCreate
)


def test_api_config_create_valid():
    cfg = ApiConfigCreate(name="x", base_url="http://a", api_key="k",
                          model_name="m", type="openai")
    assert cfg.type == "openai"


def test_api_config_create_rejects_bad_type():
    with pytest.raises(ValidationError):
        ApiConfigCreate(name="x", base_url="http://a", api_key="k",
                        model_name="m", type="bogus")


def test_wordlist_create_requires_items_list():
    wl = WordListCreate(name="s", kind="scenario", items=["a", "b"])
    assert wl.items == ["a", "b"]
    with pytest.raises(ValidationError):
        WordListCreate(name="s", kind="banned", items=[])


def test_task_create_param_bounds():
    base = dict(category_id=1, api_config_id=1, target_count=10,
                batch_size=5, max_workers=2, max_per_file=1000)
    TaskCreate(**base)
    with pytest.raises(ValidationError):
        TaskCreate(**{**base, "target_count": 0})
    with pytest.raises(ValidationError):
        TaskCreate(**{**base, "max_workers": 999})
    with pytest.raises(ValidationError):
        TaskCreate(**{**base, "batch_size": 9999})
```

- [ ] **Step 2: 跑测试,确认失败**

Run: `cd backend && pytest tests/test_schemas.py -v`
Expected: ImportError

- [ ] **Step 3: 实现 schemas.py**

```python
# backend/service/schemas.py
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


ApiType = Literal["openai", "raw"]
SampleType = Literal["black", "gray", "white"]
WordListKind = Literal["scenario", "tone", "other"]
TaskStatus = Literal["pending", "running", "succeeded", "failed", "aborted"]


class ApiConfigCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    base_url: str = Field(min_length=1, max_length=500)
    api_key: str = Field(min_length=1, max_length=500)
    model_name: str = Field(min_length=1, max_length=200)
    type: ApiType


class ApiConfigUpdate(BaseModel):
    name: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    model_name: str | None = None
    type: ApiType | None = None


class ApiConfigOut(BaseModel):
    id: int
    name: str
    base_url: str
    api_key_masked: str
    model_name: str
    type: ApiType
    created_at: str
    updated_at: str


class WordListCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    kind: WordListKind
    items: list[str] = Field(min_length=1)


class WordListUpdate(BaseModel):
    name: str | None = None
    kind: WordListKind | None = None
    items: list[str] | None = None


class WordListOut(BaseModel):
    id: int
    name: str
    kind: WordListKind
    items: list[str]
    created_at: str
    updated_at: str


class PromptTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1)
    variables: list[str]


class PromptTemplateUpdate(BaseModel):
    name: str | None = None
    body: str | None = None
    variables: list[str] | None = None


class PromptTemplateOut(BaseModel):
    id: int
    name: str
    body: str
    variables: list[str]
    created_at: str
    updated_at: str


class CategoryCreate(BaseModel):
    sample_type: SampleType
    name: str = Field(min_length=1, max_length=300)
    description: str = ""
    prompt_template_id: int
    scenario_list_id: int
    tone_list_id: int
    default_target_count: int = Field(ge=0)


class CategoryUpdate(BaseModel):
    sample_type: SampleType | None = None
    name: str | None = None
    description: str | None = None
    prompt_template_id: int | None = None
    scenario_list_id: int | None = None
    tone_list_id: int | None = None
    default_target_count: int | None = None


class CategoryOut(BaseModel):
    id: int
    sample_type: SampleType
    name: str
    description: str
    prompt_template_id: int
    scenario_list_id: int
    tone_list_id: int
    default_target_count: int
    created_at: str
    updated_at: str


class TaskCreate(BaseModel):
    category_id: int
    api_config_id: int
    target_count: int = Field(gt=0)
    batch_size: int = Field(gt=0, le=100)
    max_workers: int = Field(ge=1, le=50)
    max_per_file: int = Field(gt=0)
    created_by_label: str | None = None
    resume_from_task_id: int | None = None


class TaskEventOut(BaseModel):
    id: int
    ts: str
    type: str
    message: str


class TaskOut(BaseModel):
    id: int
    sample_type: SampleType
    category_name: str
    api_config_id: int
    api_model: str
    target_count: int
    batch_size: int
    max_workers: int
    max_per_file: int
    status: TaskStatus
    progress_current: int
    progress_total: int
    created_at: str
    started_at: str | None
    finished_at: str | None
    error_msg: str | None
    output_dir: str
    created_by_label: str | None
    resume_from_task_id: int | None


class TaskDetail(TaskOut):
    snapshot_prompt_body: str
    snapshot_scenario_items: list[str]
    snapshot_tone_items: list[str]
    snapshot_api_base_url: str
    snapshot_api_type: ApiType
    recent_events: list[TaskEventOut]
```

- [ ] **Step 4: 跑测试,确认通过**

Run: `cd backend && pytest tests/test_schemas.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add backend/service/schemas.py backend/tests/test_schemas.py
git commit -m "feat(backend): pydantic schemas with field bounds"
```

---

### Task 7: CRUD 帮助层

**Files:**
- Create: `backend/service/crud.py`
- Modify: `backend/tests/conftest.py`
- Create: `backend/tests/test_crud.py`

- [ ] **Step 1: 更新 conftest 提供 db_session fixture**

```python
# backend/tests/conftest.py
"""Shared pytest fixtures."""
import pytest
from sqlalchemy.orm import sessionmaker

from service.db import Base, create_engine_for_path


@pytest.fixture
def db_session(tmp_path):
    eng = create_engine_for_path(tmp_path / "test.db")
    Base.metadata.create_all(eng)
    Session = sessionmaker(bind=eng, expire_on_commit=False)
    s = Session()
    try:
        yield s
    finally:
        s.close()
```

- [ ] **Step 2: 写 CRUD 测试**

```python
# backend/tests/test_crud.py
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
```

- [ ] **Step 3: 跑测试,确认失败**

Run: `cd backend && pytest tests/test_crud.py -v`
Expected: ImportError

- [ ] **Step 4: 实现 crud.py**

```python
# backend/service/crud.py
import json
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from service import models
from service.schemas import (
    ApiConfigCreate, ApiConfigUpdate,
    WordListCreate, WordListUpdate,
    PromptTemplateCreate, PromptTemplateUpdate,
    CategoryCreate, CategoryUpdate,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------- ApiConfig ----------
def create_api_config(db: Session, payload: ApiConfigCreate) -> models.ApiConfig:
    obj = models.ApiConfig(
        name=payload.name, base_url=payload.base_url, api_key=payload.api_key,
        model_name=payload.model_name, type=payload.type,
        created_at=_now(), updated_at=_now(),
    )
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


def list_api_configs(db: Session) -> list[models.ApiConfig]:
    return list(db.scalars(select(models.ApiConfig).order_by(models.ApiConfig.id)))


def get_api_config(db: Session, id_: int) -> models.ApiConfig | None:
    return db.get(models.ApiConfig, id_)


def update_api_config(db: Session, obj: models.ApiConfig,
                      payload: ApiConfigUpdate) -> models.ApiConfig:
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    obj.updated_at = _now()
    db.commit(); db.refresh(obj); return obj


def delete_api_config(db: Session, obj: models.ApiConfig) -> None:
    db.delete(obj); db.commit()


def api_config_has_running_refs(db: Session, id_: int) -> bool:
    q = select(models.Task.id).where(
        models.Task.api_config_id == id_,
        models.Task.status == "running",
    ).limit(1)
    return db.scalar(q) is not None


# ---------- WordList ----------
def create_wordlist(db: Session, payload: WordListCreate) -> models.WordList:
    obj = models.WordList(
        name=payload.name, kind=payload.kind,
        items_json=json.dumps(payload.items, ensure_ascii=False),
        created_at=_now(), updated_at=_now(),
    )
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


def list_wordlists(db: Session, kind: str | None = None) -> list[models.WordList]:
    stmt = select(models.WordList).order_by(models.WordList.id)
    if kind:
        stmt = stmt.where(models.WordList.kind == kind)
    return list(db.scalars(stmt))


def get_wordlist(db: Session, id_: int) -> models.WordList | None:
    return db.get(models.WordList, id_)


def update_wordlist(db: Session, obj: models.WordList,
                    payload: WordListUpdate) -> models.WordList:
    data = payload.model_dump(exclude_unset=True)
    if "items" in data:
        obj.items_json = json.dumps(data.pop("items"), ensure_ascii=False)
    for k, v in data.items():
        setattr(obj, k, v)
    obj.updated_at = _now()
    db.commit(); db.refresh(obj); return obj


def delete_wordlist(db: Session, obj: models.WordList) -> None:
    db.delete(obj); db.commit()


def wordlist_has_running_refs(db: Session, id_: int) -> bool:
    q = select(models.Category.id).where(
        (models.Category.scenario_list_id == id_)
        | (models.Category.tone_list_id == id_)
    )
    cat_ids = list(db.scalars(q))
    if not cat_ids:
        return False
    q2 = select(models.Task.id).where(
        models.Task.category_id.in_(cat_ids),
        models.Task.status == "running",
    ).limit(1)
    return db.scalar(q2) is not None


# ---------- PromptTemplate ----------
def create_prompt_template(db: Session, payload: PromptTemplateCreate) -> models.PromptTemplate:
    obj = models.PromptTemplate(
        name=payload.name, body=payload.body,
        variables_json=json.dumps(payload.variables, ensure_ascii=False),
        created_at=_now(), updated_at=_now(),
    )
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


def list_prompt_templates(db: Session) -> list[models.PromptTemplate]:
    return list(db.scalars(select(models.PromptTemplate).order_by(models.PromptTemplate.id)))


def get_prompt_template(db: Session, id_: int) -> models.PromptTemplate | None:
    return db.get(models.PromptTemplate, id_)


def update_prompt_template(db: Session, obj: models.PromptTemplate,
                           payload: PromptTemplateUpdate) -> models.PromptTemplate:
    data = payload.model_dump(exclude_unset=True)
    if "variables" in data:
        obj.variables_json = json.dumps(data.pop("variables"), ensure_ascii=False)
    for k, v in data.items():
        setattr(obj, k, v)
    obj.updated_at = _now()
    db.commit(); db.refresh(obj); return obj


def delete_prompt_template(db: Session, obj: models.PromptTemplate) -> None:
    db.delete(obj); db.commit()


def prompt_template_has_running_refs(db: Session, id_: int) -> bool:
    q = select(models.Category.id).where(
        models.Category.prompt_template_id == id_
    )
    cat_ids = list(db.scalars(q))
    if not cat_ids:
        return False
    q2 = select(models.Task.id).where(
        models.Task.category_id.in_(cat_ids),
        models.Task.status == "running",
    ).limit(1)
    return db.scalar(q2) is not None


# ---------- Category ----------
def create_category(db: Session, payload: CategoryCreate) -> models.Category:
    obj = models.Category(**payload.model_dump(),
                          created_at=_now(), updated_at=_now())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


def list_categories(db: Session, sample_type: str | None = None) -> list[models.Category]:
    stmt = select(models.Category).order_by(models.Category.id)
    if sample_type:
        stmt = stmt.where(models.Category.sample_type == sample_type)
    return list(db.scalars(stmt))


def get_category(db: Session, id_: int) -> models.Category | None:
    return db.get(models.Category, id_)


def update_category(db: Session, obj: models.Category,
                    payload: CategoryUpdate) -> models.Category:
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    obj.updated_at = _now()
    db.commit(); db.refresh(obj); return obj


def delete_category(db: Session, obj: models.Category) -> None:
    db.delete(obj); db.commit()


def category_has_running_refs(db: Session, id_: int) -> bool:
    q = select(models.Task.id).where(
        models.Task.category_id == id_,
        models.Task.status == "running",
    ).limit(1)
    return db.scalar(q) is not None


# ---------- Task (snapshot creation) ----------
def create_task_snapshot(
    db: Session, category_id: int, api_config_id: int,
    target_count: int, batch_size: int, max_workers: int, max_per_file: int,
    created_by_label: str | None, resume_from_task_id: int | None,
) -> models.Task:
    cat = db.get(models.Category, category_id)
    api = db.get(models.ApiConfig, api_config_id)
    if cat is None or api is None:
        raise ValueError("category or api_config not found")
    pt = db.get(models.PromptTemplate, cat.prompt_template_id)
    s_wl = db.get(models.WordList, cat.scenario_list_id)
    t_wl = db.get(models.WordList, cat.tone_list_id)
    if pt is None or s_wl is None or t_wl is None:
        raise ValueError("dangling foreign keys on category")

    obj = models.Task(
        category_id=category_id, api_config_id=api_config_id,
        snapshot_sample_type=cat.sample_type,
        snapshot_category_name=cat.name,
        snapshot_prompt_body=pt.body,
        snapshot_scenario_items_json=s_wl.items_json,
        snapshot_tone_items_json=t_wl.items_json,
        snapshot_api_base_url=api.base_url,
        snapshot_api_key=api.api_key,
        snapshot_model_name=api.model_name,
        snapshot_api_type=api.type,
        target_count=target_count, batch_size=batch_size,
        max_workers=max_workers, max_per_file=max_per_file,
        status="pending", progress_current=0, progress_total=target_count,
        created_at=_now(),
        output_dir="",  # filled by supervisor when spawning
        created_by_label=created_by_label,
        resume_from_task_id=resume_from_task_id,
    )
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


def list_tasks(db: Session, *, status: str | None = None,
               category_id: int | None = None,
               page: int = 1, size: int = 50) -> list[models.Task]:
    stmt = select(models.Task).order_by(models.Task.id.desc())
    if status:
        stmt = stmt.where(models.Task.status == status)
    if category_id:
        stmt = stmt.where(models.Task.category_id == category_id)
    stmt = stmt.offset((page - 1) * size).limit(size)
    return list(db.scalars(stmt))


def get_task(db: Session, id_: int) -> models.Task | None:
    return db.get(models.Task, id_)


def add_task_event(db: Session, task_id: int, type_: str, message: str) -> models.TaskEvent:
    ev = models.TaskEvent(task_id=task_id, ts=_now(), type=type_, message=message)
    db.add(ev); db.commit(); db.refresh(ev)
    return ev


def recent_events(db: Session, task_id: int, limit: int = 50) -> list[models.TaskEvent]:
    stmt = (select(models.TaskEvent)
            .where(models.TaskEvent.task_id == task_id)
            .order_by(models.TaskEvent.id.desc())
            .limit(limit))
    return list(reversed(list(db.scalars(stmt))))


def events_since(db: Session, task_id: int, since_id: int,
                 limit: int = 500) -> list[models.TaskEvent]:
    stmt = (select(models.TaskEvent)
            .where(models.TaskEvent.task_id == task_id,
                   models.TaskEvent.id > since_id)
            .order_by(models.TaskEvent.id.asc())
            .limit(limit))
    return list(db.scalars(stmt))
```

- [ ] **Step 5: 跑测试,确认通过**

Run: `cd backend && pytest tests/test_crud.py -v`
Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add backend/service/crud.py backend/tests/conftest.py backend/tests/test_crud.py
git commit -m "feat(backend): crud helpers for configs, categories, tasks"
```

---

## C. 共用工具

### Task 8: api_key 脱敏

**Files:**
- Create: `backend/service/security.py`
- Create: `backend/tests/test_security.py`

- [ ] **Step 1: 写测试**

```python
# backend/tests/test_security.py
from service.security import mask_api_key


def test_mask_short_key():
    assert mask_api_key("k") == "****"
    assert mask_api_key("") == "****"


def test_mask_normal_key_keeps_prefix_and_suffix():
    out = mask_api_key("sk-1234567890abcdef")
    assert out.startswith("sk-")
    assert out.endswith("cdef")
    assert "*" in out
    assert "1234567890ab" not in out


def test_mask_idempotent():
    once = mask_api_key("sk-1234567890abcdef")
    twice = mask_api_key(once)
    assert twice == once or "*" in twice
```

- [ ] **Step 2: 跑测试,确认失败**

Run: `cd backend && pytest tests/test_security.py -v`
Expected: ImportError

- [ ] **Step 3: 实现 security.py**

```python
# backend/service/security.py
def mask_api_key(key: str) -> str:
    if not key or len(key) < 8:
        return "****"
    prefix_len = 3 if key.startswith("sk-") else 2
    suffix_len = 4
    return key[:prefix_len] + "****" + key[-suffix_len:]
```

- [ ] **Step 4: 跑测试,确认通过**

Run: `cd backend && pytest tests/test_security.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add backend/service/security.py backend/tests/test_security.py
git commit -m "feat(backend): api_key masking utility"
```

---

### Task 9: Prompt 占位符校验 + 渲染

**Files:**
- Create: `backend/service/prompt_render.py`
- Create: `backend/tests/test_prompt_render.py`

- [ ] **Step 1: 写测试**

```python
# backend/tests/test_prompt_render.py
import pytest
from service.prompt_render import (
    extract_placeholders, validate_template,
    render_prompt, PromptValidationError
)


def test_extract_placeholders_basic():
    s = "hi {a} and {b} and {a}"
    assert extract_placeholders(s) == {"a", "b"}


def test_validate_template_ok():
    validate_template("hi {x} {y}", ["x", "y"])


def test_validate_template_missing_var_declaration():
    with pytest.raises(PromptValidationError):
        validate_template("hi {x} {y}", ["x"])


def test_validate_template_unused_declared_var():
    with pytest.raises(PromptValidationError):
        validate_template("hi {x}", ["x", "y"])


def test_render_prompt_substitutes():
    out = render_prompt("hi {scenario} {tone}",
                       {"scenario": "a", "tone": "b"})
    assert out == "hi a b"


def test_render_prompt_strict_missing_key():
    with pytest.raises(PromptValidationError):
        render_prompt("hi {missing}", {})
```

- [ ] **Step 2: 跑测试,确认失败**

Run: `cd backend && pytest tests/test_prompt_render.py -v`
Expected: ImportError

- [ ] **Step 3: 实现 prompt_render.py**

```python
# backend/service/prompt_render.py
import re
from typing import Mapping


_PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


class PromptValidationError(ValueError):
    pass


def extract_placeholders(body: str) -> set[str]:
    return set(_PLACEHOLDER_RE.findall(body))


def validate_template(body: str, variables: list[str]) -> None:
    body_vars = extract_placeholders(body)
    declared = set(variables)
    missing = body_vars - declared
    unused = declared - body_vars
    problems = []
    if missing:
        problems.append(f"body uses undeclared variables: {sorted(missing)}")
    if unused:
        problems.append(f"declared but unused variables: {sorted(unused)}")
    if problems:
        raise PromptValidationError("; ".join(problems))


def render_prompt(body: str, values: Mapping[str, str]) -> str:
    needed = extract_placeholders(body)
    missing = needed - set(values)
    if missing:
        raise PromptValidationError(f"missing values for placeholders: {sorted(missing)}")

    def _sub(m: re.Match[str]) -> str:
        return str(values[m.group(1)])

    return _PLACEHOLDER_RE.sub(_sub, body)
```

- [ ] **Step 4: 跑测试,确认通过**

Run: `cd backend && pytest tests/test_prompt_render.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add backend/service/prompt_render.py backend/tests/test_prompt_render.py
git commit -m "feat(backend): prompt placeholder validation and rendering"
```

---

### Task 10: Worker I/O — CSV 写入 + 行数统计 + resume 拷贝

**Files:**
- Create: `backend/service/worker_io.py`
- Create: `backend/tests/test_worker_io.py`

- [ ] **Step 1: 写测试**

```python
# backend/tests/test_worker_io.py
from pathlib import Path
from service.worker_io import (
    CsvVolumeWriter, count_existing_rows, copy_resume_csvs
)


def test_count_existing_rows_skips_header(tmp_path):
    p = tmp_path / "a.csv"
    p.write_text("评测题,风险类型\n行1,c\n行2,c\n", encoding="utf-8-sig")
    assert count_existing_rows(tmp_path) == 2


def test_count_existing_rows_multiple_files(tmp_path):
    (tmp_path / "a.csv").write_text("h1,h2\n1,c\n2,c\n", encoding="utf-8-sig")
    (tmp_path / "b.csv").write_text("h1,h2\n3,c\n", encoding="utf-8-sig")
    assert count_existing_rows(tmp_path) == 3


def test_writer_splits_at_max_per_file(tmp_path):
    w = CsvVolumeWriter(
        out_dir=tmp_path, base_name="X_Samples",
        header=["评测题", "风险类型"], max_per_file=2,
    )
    for i in range(5):
        w.write_row([f"line{i}", "cat"])
    w.close()
    files = sorted(tmp_path.glob("*.csv"))
    assert [p.name for p in files] == [
        "X_Samples_part1.csv", "X_Samples_part2.csv", "X_Samples_part3.csv"]
    # Total rows excluding headers == 5
    total = sum(count_existing_rows_in_file(p) for p in files)
    assert total == 5


def count_existing_rows_in_file(path: Path) -> int:
    with open(path, "r", encoding="utf-8-sig") as f:
        return max(0, sum(1 for _ in f) - 1)


def test_writer_resumes_into_existing_partial_volume(tmp_path):
    # Pre-existing partial volume with 1 row
    (tmp_path / "X_Samples_part1.csv").write_text(
        "h1,h2\nexisting,cat\n", encoding="utf-8-sig")
    w = CsvVolumeWriter(out_dir=tmp_path, base_name="X_Samples",
                        header=["h1", "h2"], max_per_file=3)
    w.resume()
    w.write_row(["new1", "cat"])
    w.write_row(["new2", "cat"])
    w.write_row(["new3", "cat"])  # triggers next volume
    w.close()
    files = sorted(tmp_path.glob("*.csv"))
    assert [p.name for p in files] == [
        "X_Samples_part1.csv", "X_Samples_part2.csv"]


def test_copy_resume_csvs(tmp_path):
    src = tmp_path / "src"; src.mkdir()
    dst = tmp_path / "dst"; dst.mkdir()
    (src / "A.csv").write_text("h\n1\n2\n", encoding="utf-8-sig")
    (src / "ignored.txt").write_text("nope", encoding="utf-8")
    copy_resume_csvs(src, dst)
    assert (dst / "A.csv").read_text(encoding="utf-8-sig") == "h\n1\n2\n"
    assert not (dst / "ignored.txt").exists()
```

- [ ] **Step 2: 跑测试,确认失败**

Run: `cd backend && pytest tests/test_worker_io.py -v`
Expected: ImportError

- [ ] **Step 3: 实现 worker_io.py**

```python
# backend/service/worker_io.py
import csv
import shutil
from pathlib import Path


def count_existing_rows(out_dir: Path) -> int:
    if not out_dir.exists():
        return 0
    total = 0
    for p in sorted(out_dir.glob("*.csv")):
        with open(p, "r", encoding="utf-8-sig") as f:
            total += max(0, sum(1 for _ in f) - 1)
    return total


def copy_resume_csvs(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for p in sorted(src.glob("*.csv")):
        shutil.copy2(p, dst / p.name)


class CsvVolumeWriter:
    """Writes rows into base_name_part{N}.csv files, splitting when a volume
    reaches `max_per_file` data rows (header excluded)."""

    def __init__(self, *, out_dir: Path, base_name: str,
                 header: list[str], max_per_file: int) -> None:
        self.out_dir = out_dir
        self.base_name = base_name
        self.header = header
        self.max_per_file = max_per_file
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self._volume_idx = 1
        self._rows_in_volume = 0
        self._file = None
        self._writer = None

    def _path(self, idx: int) -> Path:
        return self.out_dir / f"{self.base_name}_part{idx}.csv"

    def resume(self) -> None:
        """Pick up where existing volumes left off."""
        idx = 1
        while self._path(idx).exists():
            idx += 1
        self._volume_idx = max(1, idx - 1) if self._path(max(1, idx - 1)).exists() else 1
        path = self._path(self._volume_idx)
        if path.exists():
            with open(path, "r", encoding="utf-8-sig") as f:
                rows = max(0, sum(1 for _ in f) - 1)
            if rows >= self.max_per_file:
                self._volume_idx += 1
                self._rows_in_volume = 0
            else:
                self._rows_in_volume = rows

    def _ensure_open(self) -> None:
        path = self._path(self._volume_idx)
        is_new = not path.exists()
        if self._file is None:
            self._file = open(path, "a", newline="", encoding="utf-8-sig")
            self._writer = csv.writer(self._file)
            if is_new:
                self._writer.writerow(self.header)

    def write_row(self, row: list[str]) -> None:
        if self._rows_in_volume >= self.max_per_file:
            self.close()
            self._volume_idx += 1
            self._rows_in_volume = 0
        self._ensure_open()
        self._writer.writerow(row)
        self._rows_in_volume += 1

    def flush(self) -> None:
        if self._file is not None:
            self._file.flush()

    def close(self) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None
            self._writer = None
```

- [ ] **Step 4: 跑测试,确认通过**

Run: `cd backend && pytest tests/test_worker_io.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add backend/service/worker_io.py backend/tests/test_worker_io.py
git commit -m "feat(backend): csv volume writer with resume + row counting"
```

---

## D. 配置 REST

### Task 11: FastAPI 依赖 + DB 初始化挂到 startup

**Files:**
- Create: `backend/service/deps.py`
- Modify: `backend/service/main.py`
- Create: `backend/tests/test_main_startup.py`

- [ ] **Step 1: 写测试**

```python
# backend/tests/test_main_startup.py
import os
from fastapi.testclient import TestClient


def test_startup_creates_db_and_tables(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "app.db"))
    from importlib import reload
    import service.config as cfg; reload(cfg)
    import service.db as dbmod; reload(dbmod)
    import service.main as mainmod; reload(mainmod)

    with TestClient(mainmod.app) as client:
        r = client.get("/healthz")
        assert r.status_code == 200
        # tables created
        from sqlalchemy import inspect
        names = set(inspect(dbmod.engine).get_table_names())
        assert {"api_config", "wordlist", "prompt_template",
                "category", "task", "task_event"} <= names
```

- [ ] **Step 2: 跑测试,确认失败**

Run: `cd backend && pytest tests/test_main_startup.py -v`
Expected: 表不存在 / 启动钩子未初始化 DB

- [ ] **Step 3: 实现 deps.py**

```python
# backend/service/deps.py
from typing import Iterator

from sqlalchemy.orm import Session

from service import db as dbmod


def get_db() -> Iterator[Session]:
    assert dbmod.SessionLocal is not None, "DB not initialized"
    s = dbmod.SessionLocal()
    try:
        yield s
    finally:
        s.close()
```

- [ ] **Step 4: 改 main.py 启动钩子,在 startup 初始化 engine 并建表**

```python
# backend/service/main.py
from fastapi import FastAPI

from service import db as dbmod, models  # noqa: F401  ensures models import
from service.config import settings

app = FastAPI(title="LLM Data Service", version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    settings.ensure_dirs()
    dbmod.init_engine()
    dbmod.Base.metadata.create_all(dbmod.engine)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 5: 跑测试,确认通过**

Run: `cd backend && pytest tests/test_main_startup.py tests/test_health.py -v`
Expected: 全 passed

- [ ] **Step 6: Commit**

```bash
git add backend/service/deps.py backend/service/main.py backend/tests/test_main_startup.py
git commit -m "feat(backend): wire DB init into FastAPI startup"
```

---

### Task 12: ApiConfig 路由 (CRUD + reveal + 脱敏)

**Files:**
- Create: `backend/service/routers/__init__.py`
- Create: `backend/service/routers/api_configs.py`
- Modify: `backend/service/main.py` 注册路由
- Create: `backend/tests/test_routers_api_configs.py`

- [ ] **Step 1: 写测试**

```python
# backend/tests/test_routers_api_configs.py
from fastapi.testclient import TestClient


def _client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "app.db"))
    from importlib import reload
    import service.config as cfg; reload(cfg)
    import service.db as dbmod; reload(dbmod)
    import service.main as mainmod; reload(mainmod)
    return TestClient(mainmod.app)


def test_create_list_and_mask_api_config(tmp_path, monkeypatch):
    with _client(tmp_path, monkeypatch) as c:
        r = c.post("/api/api-configs", json={
            "name": "Q", "base_url": "http://x", "api_key": "sk-1234567890ab",
            "model_name": "m", "type": "raw"})
        assert r.status_code == 201, r.text
        items = c.get("/api/api-configs").json()
        assert len(items) == 1
        assert "api_key_masked" in items[0]
        assert "1234" not in items[0]["api_key_masked"]
        assert "api_key" not in items[0]  # never leak raw key in list


def test_reveal_returns_plain_key(tmp_path, monkeypatch):
    with _client(tmp_path, monkeypatch) as c:
        cid = c.post("/api/api-configs", json={
            "name": "Q", "base_url": "http://x", "api_key": "sk-1234567890ab",
            "model_name": "m", "type": "raw"}).json()["id"]
        r = c.get(f"/api/api-configs/{cid}/reveal")
        assert r.status_code == 200
        assert r.json()["api_key"] == "sk-1234567890ab"
        assert r.headers.get("cache-control") == "no-store"


def test_delete_blocked_when_running_task_refs(tmp_path, monkeypatch):
    """We can't easily run a task in a unit test; simulate by writing
    a running task row directly via the DB."""
    with _client(tmp_path, monkeypatch) as c:
        cid = c.post("/api/api-configs", json={
            "name": "Q", "base_url": "http://x", "api_key": "k",
            "model_name": "m", "type": "raw"}).json()["id"]
        # Insert fk targets + a fake running task referencing this config
        import service.db as dbmod
        from service import models
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
            s.add(cat); s.flush()
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
            s.add(t); s.commit()
        r = c.delete(f"/api/api-configs/{cid}")
        assert r.status_code == 409
```

- [ ] **Step 2: 跑测试,确认失败**

Run: `cd backend && pytest tests/test_routers_api_configs.py -v`
Expected: 404 (路由未注册)

- [ ] **Step 3: 实现 routers/api_configs.py**

```python
# backend/service/routers/__init__.py
```

```python
# backend/service/routers/api_configs.py
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from service import crud
from service.deps import get_db
from service.schemas import (
    ApiConfigCreate, ApiConfigUpdate, ApiConfigOut
)
from service.security import mask_api_key

router = APIRouter(prefix="/api/api-configs", tags=["api-configs"])


def _to_out(obj) -> ApiConfigOut:
    return ApiConfigOut(
        id=obj.id, name=obj.name, base_url=obj.base_url,
        api_key_masked=mask_api_key(obj.api_key),
        model_name=obj.model_name, type=obj.type,
        created_at=obj.created_at, updated_at=obj.updated_at,
    )


@router.get("")
def list_(db: Session = Depends(get_db)) -> list[ApiConfigOut]:
    return [_to_out(o) for o in crud.list_api_configs(db)]


@router.post("", status_code=status.HTTP_201_CREATED)
def create(payload: ApiConfigCreate, db: Session = Depends(get_db)) -> ApiConfigOut:
    obj = crud.create_api_config(db, payload)
    return _to_out(obj)


@router.put("/{id_}")
def update(id_: int, payload: ApiConfigUpdate,
           db: Session = Depends(get_db)) -> ApiConfigOut:
    obj = crud.get_api_config(db, id_)
    if obj is None:
        raise HTTPException(404, "not found")
    obj = crud.update_api_config(db, obj, payload)
    return _to_out(obj)


@router.delete("/{id_}", status_code=status.HTTP_204_NO_CONTENT)
def delete(id_: int, db: Session = Depends(get_db)) -> Response:
    obj = crud.get_api_config(db, id_)
    if obj is None:
        raise HTTPException(404, "not found")
    if crud.api_config_has_running_refs(db, id_):
        raise HTTPException(409, "config is referenced by a running task")
    crud.delete_api_config(db, obj)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{id_}/reveal")
def reveal(id_: int, db: Session = Depends(get_db)) -> Response:
    from fastapi.responses import JSONResponse
    obj = crud.get_api_config(db, id_)
    if obj is None:
        raise HTTPException(404, "not found")
    return JSONResponse(
        {"id": obj.id, "api_key": obj.api_key},
        headers={"Cache-Control": "no-store"},
    )
```

- [ ] **Step 4: 注册路由到 main.py**

```python
# backend/service/main.py
from fastapi import FastAPI

from service import db as dbmod, models  # noqa: F401
from service.config import settings
from service.routers import api_configs as api_configs_router

app = FastAPI(title="LLM Data Service", version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    settings.ensure_dirs()
    dbmod.init_engine()
    dbmod.Base.metadata.create_all(dbmod.engine)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_configs_router.router)
```

- [ ] **Step 5: 跑测试,确认通过**

Run: `cd backend && pytest tests/test_routers_api_configs.py -v`
Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add backend/service/routers/__init__.py backend/service/routers/api_configs.py backend/service/main.py backend/tests/test_routers_api_configs.py
git commit -m "feat(backend): /api/api-configs CRUD with mask + reveal"
```

---

### Task 13: WordList 路由

**Files:**
- Create: `backend/service/routers/wordlists.py`
- Modify: `backend/service/main.py`
- Create: `backend/tests/test_routers_wordlists.py`

- [ ] **Step 1: 写测试**

```python
# backend/tests/test_routers_wordlists.py
from fastapi.testclient import TestClient


def _client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("DB_PATH", str(tmp_path / "app.db"))
    from importlib import reload
    import service.config as cfg; reload(cfg)
    import service.db as dbmod; reload(dbmod)
    import service.main as mainmod; reload(mainmod)
    return TestClient(mainmod.app)


def test_wordlist_crud_and_filter(tmp_path, monkeypatch):
    with _client(tmp_path, monkeypatch) as c:
        a = c.post("/api/wordlists", json={
            "name": "scn", "kind": "scenario", "items": ["a", "b"]}).json()
        c.post("/api/wordlists", json={
            "name": "tne", "kind": "tone", "items": ["t1"]})
        r = c.get("/api/wordlists?kind=scenario").json()
        assert len(r) == 1 and r[0]["items"] == ["a", "b"]
        u = c.put(f"/api/wordlists/{a['id']}", json={"items": ["x"]}).json()
        assert u["items"] == ["x"]
        assert c.delete(f"/api/wordlists/{a['id']}").status_code == 204
```

- [ ] **Step 2: 跑测试,确认失败**

Run: `cd backend && pytest tests/test_routers_wordlists.py -v`
Expected: 404

- [ ] **Step 3: 实现 routers/wordlists.py**

```python
# backend/service/routers/wordlists.py
import json
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from service import crud
from service.deps import get_db
from service.schemas import WordListCreate, WordListUpdate, WordListOut

router = APIRouter(prefix="/api/wordlists", tags=["wordlists"])


def _to_out(obj) -> WordListOut:
    return WordListOut(
        id=obj.id, name=obj.name, kind=obj.kind,
        items=json.loads(obj.items_json),
        created_at=obj.created_at, updated_at=obj.updated_at,
    )


@router.get("")
def list_(kind: str | None = None,
          db: Session = Depends(get_db)) -> list[WordListOut]:
    return [_to_out(o) for o in crud.list_wordlists(db, kind=kind)]


@router.post("", status_code=status.HTTP_201_CREATED)
def create(payload: WordListCreate, db: Session = Depends(get_db)) -> WordListOut:
    return _to_out(crud.create_wordlist(db, payload))


@router.put("/{id_}")
def update(id_: int, payload: WordListUpdate,
           db: Session = Depends(get_db)) -> WordListOut:
    obj = crud.get_wordlist(db, id_)
    if obj is None:
        raise HTTPException(404, "not found")
    return _to_out(crud.update_wordlist(db, obj, payload))


@router.delete("/{id_}", status_code=status.HTTP_204_NO_CONTENT)
def delete(id_: int, db: Session = Depends(get_db)) -> Response:
    obj = crud.get_wordlist(db, id_)
    if obj is None:
        raise HTTPException(404, "not found")
    if crud.wordlist_has_running_refs(db, id_):
        raise HTTPException(409, "wordlist is referenced by a running task")
    crud.delete_wordlist(db, obj)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

- [ ] **Step 4: 注册路由**

In `backend/service/main.py`, after the `api_configs_router` include line add:

```python
from service.routers import wordlists as wordlists_router
app.include_router(wordlists_router.router)
```

- [ ] **Step 5: 跑测试,确认通过**

Run: `cd backend && pytest tests/test_routers_wordlists.py -v`
Expected: 1 passed

- [ ] **Step 6: Commit**

```bash
git add backend/service/routers/wordlists.py backend/service/main.py backend/tests/test_routers_wordlists.py
git commit -m "feat(backend): /api/wordlists CRUD with kind filter"
```

---
