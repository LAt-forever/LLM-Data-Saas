# LLM 样本数据生产服务

把硬编码的 Python 样本生成脚本，做成一套可配置、可监控、可续跑的前后端服务。非技术成员也能在网页上配置接口、模板、词库、分类，并启动数据生成任务。

> **安全提示：** 本服务设计为内网部署，已添加管理员登录鉴权。部署时请务必设置 `ADMIN_PASSWORD_HASH`，不要暴露到公网。

---

## 功能特性

- **任务中心**：创建、监控、中止、删除数据生成任务；支持基于历史任务续跑
- **实时进度**：SSE 推送任务事件，浏览器端自动重连
- **数据预览 & 下载**：任务完成后预览 CSV 内容，一键下载结果
- **配置管理**：
  - API 配置：管理 LLM 接口（Base URL、Key、模型）
  - Prompt 模板：可视化编辑模板，自动检测 `{variable}` 变量
  - 词库：场景/语气/其他词库，每行一词批量导入
  - 分类：关联模板、场景词库、语气词库，定义样本类型（黑/灰/白）
- **API 连通性测试**：一键测试 LLM 接口可用性
- **快照隔离**：任务运行时锁定创建时的配置快照，历史任务可复现

---

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | React 19 + TypeScript + Vite + Ant Design 6 + TanStack Query 5 + Zustand 5 + wouter |
| 后端 | Python 3.11 + FastAPI + SQLAlchemy 2 + SQLite (WAL) |
| 进度推送 | SSE (sse-starlette) |
| LLM 客户端 | openai SDK (兼容接口) + requests (raw 接口) |
| 测试 | pytest + httpx |
| 部署 | Docker + uvicorn |

---

## 快速开始（Docker）

```bash
# 1. 创建 .env 文件并设置管理员密码
#    密码需要生成 bcrypt 哈希，参见下方"生成密码哈希"
cp .env.example .env
# 编辑 .env，填入 ADMIN_PASSWORD_HASH

# 2. 启动服务
docker-compose up --build -d

# 3. 访问
open http://localhost:8000
```

**生成密码哈希：**
```bash
cd backend && .venv/bin/python -c "import bcrypt; print(bcrypt.hashpw(b'your-password', bcrypt.gensalt()).decode())"
```

数据持久化：
- `./data/` → 任务 CSV 输出
- `./logs/` → 任务运行日志
- `./app.db` → SQLite 数据库

---

## 开发环境

### 后端

```bash
cd backend

# 创建虚拟环境并安装依赖
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 启动（开发模式）
STATIC_DIR=../frontend/dist uvicorn service.main:app --reload

# 运行测试
pytest tests/ -q
```

### 前端

```bash
cd frontend

# 安装依赖
npm install

# 开发服务器（代理到 localhost:8000）
npm run dev

# 生产构建
npm run build
```

### 完整开发流程

```bash
# 终端 1：启动后端
cd backend && STATIC_DIR=../frontend/dist .venv/bin/uvicorn service.main:app --reload

# 终端 2：启动前端
cd frontend && npm run dev

# 浏览器访问 http://localhost:5173
```

---

## 项目结构

```
.
├── backend/
│   ├── service/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py            # 配置（支持环境变量）
│   │   ├── db.py                # SQLAlchemy 引擎/会话
│   │   ├── models.py            # ORM 模型
│   │   ├── schemas.py           # Pydantic DTO
│   │   ├── crud.py              # 数据库操作
│   │   ├── supervisor.py        # Worker 监督/启动恢复
│   │   ├── worker.py            # Worker 子进程
│   │   ├── worker_run.py        # 任务执行核心
│   │   ├── llm_client.py        # LLM 调用封装
│   │   ├── sse.py               # SSE 推送模块
│   │   ├── static.py            # 静态文件托管（SPA fallback）
│   │   └── routers/             # REST API 路由
│   │       ├── auth.py          # 登录/登出/会话
│   │       ├── tasks.py
│   │       ├── tasks_stream.py
│   │       ├── api_configs.py
│   │       ├── wordlists.py
│   │       ├── prompt_templates.py
│   │       ├── categories.py
│   │       └── meta.py
│   └── tests/                   # pytest 测试（89 个）
├── frontend/
│   ├── src/
│   │   ├── api/                 # fetch 封装 + API 函数 + 类型
│   │   ├── components/          # React 组件
│   │   ├── pages/               # 页面组件
│   │   ├── hooks/               # 自定义 hooks
│   │   ├── store/               # Zustand store
│   │   ├── App.tsx              # 路由入口
│   │   └── theme.ts             # Ant Design 主题
│   └── dist/                    # 生产构建输出
├── docker-compose.yml
├── Dockerfile
└── llm-data-create/             # 遗留脚本（参考来源）
```

---

## API 概览

| 端点 | 说明 |
|---|---|
| `GET /healthz` | 健康检查（公开） |
| `POST /api/auth/login` | 管理员登录 |
| `POST /api/auth/logout` | 退出登录 |
| `GET /api/auth/me` | 当前用户信息 |
| `GET /api/api-configs` | API 配置 CRUD + test/reveal |
| `GET /api/wordlists` | 词库 CRUD |
| `GET /api/prompt-templates` | Prompt 模板 CRUD |
| `GET /api/categories` | 分类 CRUD |
| `GET /api/sample-types` | 样本类型枚举 |
| `GET /api/tasks` | 任务列表 |
| `POST /api/tasks` | 创建任务 |
| `GET /api/tasks/{id}` | 任务详情 |
| `POST /api/tasks/{id}/abort` | 中止任务 |
| `GET /api/tasks/{id}/preview` | 预览 CSV |
| `GET /api/tasks/{id}/download` | 下载结果 |
| `GET /api/tasks/{id}/events` | 任务事件 |
| `GET /api/tasks/{id}/log` | 运行日志 |
| `GET /api/tasks/{id}/stream` | SSE 实时推送 |

完整文档：`http://localhost:8000/docs`（FastAPI 自动生成的 Swagger UI）

---

## 环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `STATIC_DIR` | `frontend/dist` | 前端静态文件目录 |
| `DATA_DIR` | `data` | 任务 CSV 输出目录 |
| `LOG_DIR` | `logs` | 日志目录 |
| `DB_PATH` | `app.db` | SQLite 数据库文件 |
| `SUPERVISOR_POLL_SECONDS` | `30` | Worker 孤儿扫描间隔 |

### 认证（必填）

| 变量 | 默认值 | 说明 |
|---|---|---|
| `ADMIN_USERNAME` | `admin` | 管理员登录账号 |
| `ADMIN_PASSWORD_HASH` | — | 管理员密码 bcrypt 哈希（**必填**） |

生成密码哈希：
```bash
cd backend && python -c "import bcrypt; print(bcrypt.hashpw(b'your-password', bcrypt.gensalt()).decode())"
```

---

## 测试

```bash
cd backend
pytest tests/ -q
```

89 个测试覆盖：路由 CRUD、数据模型、LLM 客户端、Worker 执行、Supervisor 轮询、SSE 推送、启动恢复、静态托管、种子数据迁移。

---

## 设计来源

本项目由 `llm-data-create/` 仓库的硬编码脚本演进而来：

- 黑样本：33 个 `run_A*.py` + `master_runner.py`
- 灰样本：`gray_data/code/generate_gray_deepseek.py`
- 白样本：`white_data/code/generate_white_deepseek.py`

原脚本中的 API 地址、Key、模型名、分类定义、Prompt 模板、词库、并发参数已全部提取为 UI 可配置项。

---

## 后续演进（预留）

- SQLite → PostgreSQL，subprocess → Celery+Redis
- CSV 二次处理（去重 / 抽样 / 评测）
