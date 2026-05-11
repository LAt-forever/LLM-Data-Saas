# LLM 样本数据生产服务 · 设计文档

- 起草日期:2026-05-11
- 来源参考:`llm-data-create/` 仓库现有的黑/灰/白样本生成脚本

## 1. 背景与目标

现有数据生成能力以三组 Python 脚本形式存在(`llm-data-create/`):

- 黑样本:33 个 `run_A*.py` + `master_runner.py` 调度
- 灰样本:`gray_data/code/generate_gray_deepseek.py`
- 白样本:`white_data/code/generate_white_deepseek.py`

所有 API 地址、Key、模型名、分类定义、Prompt 模板、场景/语气词库、目标数量、并发参数**全部硬编码**在源码里;调度依赖 `subprocess` + `time.sleep`,只能在命令行运行,任务状态靠数 CSV 行数推测。

**本项目的目标**是把上述能力做成一套部署在内网的前后端服务,让非技术成员也能:

- 在网页上配置接口/模板/词库/分类,无需改代码
- 在网页上启动、监控、中止、续跑数据生成任务
- 预览并下载生成结果

## 2. 范围与边界

**在范围内**

- 内部小团队 (2~10 人) 共享一台机器使用
- 同时支持小批试跑 (100~10k 条) 与大批量产 (10 万~120 万条)
- 无访问控制(信任内网,显式提示「请勿暴露公网」)
- 任意数量的任务并发执行(无 worker 池上限)
- 任务可中止、可基于历史任务续跑
- 配置和历史任务的状态对所有用户可见

**不在范围内**

- 用户登录 / 角色 / 权限
- 多租户隔离
- 任务真正的「暂停 / 恢复」语义(只做 abort + 新建续跑)
- 分布式部署 / 横向扩展
- 移动端适配 / 国际化 / 暗色主题
- 公网访问 / SSL 终端 / WAF

## 3. 总体架构

```
┌──────────────────────────────────────────────────────────────┐
│                       浏览器 (React SPA)                       │
│  任务中心 · 配置管理 · Prompt 模板 · 词库 · 分类 · 接口设置      │
└──────────────────────────────────────────────────────────────┘
                       ↕  HTTP / JSON · SSE
┌──────────────────────────────────────────────────────────────┐
│                  FastAPI 进程 (同源部署)                       │
│  REST API · SSE 推送 · 静态托管 dist/ · Worker 监督模块         │
└──────────────────────────────────────────────────────────────┘
        │ spawn (subprocess.Popen)              │ 读/写
        ▼                                       ▼
┌──────────────┐  ┌──────────────┐    ┌──────────────────┐
│  Worker #1   │  │  Worker #N   │ …  │  SQLite (app.db)  │
│  跑 task=101 │  │  跑 task=N   │    │  WAL 模式          │
└──────────────┘  └──────────────┘    └──────────────────┘
        │ 写 CSV                               
        ▼                                  
┌─────────────────────────────────────┐  
│  文件系统:data/task-{id}/*.csv      │  
│            logs/task-{id}.log       │  
└─────────────────────────────────────┘  
        │ HTTP
        ▼
┌─────────────────────────────────────┐
│  外部 LLM 接口                       │
│  (DeepSeek 代理 · 内网 Qwen · 等)    │
└─────────────────────────────────────┘
```

**关键决策:**

- **进程模型**:API 进程 + 每个任务一个 Python 子进程 Worker。API 重启不影响在跑任务;Worker 崩溃不影响 API。无 Redis / 消息队列依赖。
- **数据库**:SQLite 单文件,WAL 模式。结构化数据全进 DB,CSV 仍走文件。
- **进程间通信**:Worker 不直接和 API 进程通信,**只写 DB**;API 进程内置 watcher 把 DB 变更广播给前端 SSE 订阅者。
- **进度推送**:Server-Sent Events (SSE),浏览器原生 `EventSource`,断线自动重连。
- **前端**:React + Ant Design SPA,生产打包后由 FastAPI 同源托管。开发阶段 `npm run dev` 走代理。
- **部署**:单 Docker 镜像,uvicorn 启动。`app.db` 和 `data/` 通过 volume 持久化。

## 4. 数据模型

所有表使用 SQLite,主键 `id INTEGER PRIMARY KEY AUTOINCREMENT`,时间列用 ISO8601 字符串或 INTEGER unix 秒。

### 4.1 配置实体

```
ApiConfig
─────────────────────────────────────────────────────────
id, name, base_url, api_key, model_name,
type ('openai' | 'raw'),     -- openai 走 OpenAI SDK,raw 走 requests.post
created_at, updated_at

WordList
─────────────────────────────────────────────────────────
id, name,
kind ('scenario' | 'tone' | 'other'),
items_json,                  -- JSON 数组,字符串列表
created_at, updated_at

PromptTemplate
─────────────────────────────────────────────────────────
id, name,
body,                        -- 含占位符的 prompt 文本
variables_json,              -- 占位符列表如 ["category","scenario","tone","batch_size"]
created_at, updated_at

Category
─────────────────────────────────────────────────────────
id,
sample_type ('black' | 'gray' | 'white'),
name,                        -- 例: "A.1.a 煽动颠覆国家政权"
description,
prompt_template_id   → PromptTemplate.id
scenario_list_id     → WordList.id   (kind=scenario)
tone_list_id         → WordList.id   (kind=tone)
default_target_count,
created_at, updated_at
```

### 4.2 任务实体

```
Task
─────────────────────────────────────────────────────────
id,
category_id     → Category.id   -- 仅引用,真正运行用 snapshot
api_config_id   → ApiConfig.id

-- snapshot (创建任务时复制,只读,保证历史可复现)
snapshot_sample_type,
snapshot_category_name,
snapshot_prompt_body,
snapshot_scenario_items_json,
snapshot_tone_items_json,
snapshot_api_base_url,
snapshot_api_key,
snapshot_model_name,
snapshot_api_type,

-- 运行参数
target_count,
batch_size,
max_workers,                 -- worker 内部 ThreadPool 并发
max_per_file,                -- 单 CSV 最大行数,超过分卷

-- 状态
status,                      -- pending | running | succeeded | failed | aborted
progress_current,            -- 已生成行数
progress_total,              -- = target_count,冗余便于读
created_at, started_at, finished_at,
error_msg,                   -- 简短业务错误,长 traceback 进 logs/

-- 运行环境
output_dir,                  -- 例: data/task-142/
worker_pid,
created_by_label,            -- 自由文本(可选,无登录)
resume_from_task_id          -- 续跑来源 (可空)
```

### 4.3 事件流

```
TaskEvent
─────────────────────────────────────────────────────────
id,
task_id        → Task.id
ts,
type,                        -- started | progress | warning | error | aborted | finished
message                      -- 一行业务信息

只存业务事件,debug/traceback 走 logs/task-{id}.log。
```

### 4.4 索引

- `Task(status)`、`Task(created_at)` — 列表页过滤
- `Task(category_id)`、`Task(api_config_id)` — 引用检查
- `TaskEvent(task_id, id)` — 详情页按时间翻页

### 4.5 初始化数据迁移

一次性脚本 `scripts/seed_from_legacy.py`:

- 读取 `llm-data-create/black_data/run_A*.py`:解析每个文件里的 `CURRENT_CATEGORY` / `SCENARIOS` / `TONES` / `META_PROMPT_TEMPLATE` / `TARGET_COUNT` / `API_URL` / `HEADERS` / `MODEL_NAME`
- 生成对应的 `ApiConfig` / `PromptTemplate` / `WordList` / `Category` 行
- 灰、白样本同理处理。源脚本里的 `META_TEMPLATES` 是一组等价模板(同一类样本随机用其中一个),v1 实现选择**合并成单个 PromptTemplate**,在 `body` 里用 `{{variant_a}} ... ||| {{variant_b}} ...` 之类的语法,渲染时按行随机挑。Category 仍 1 对 1 引用一个 PromptTemplate。
- 单元测试断言所有分类、词库、模板都导入成功且内容与源文件一致

## 5. 任务生命周期

### 5.1 创建任务

```
1. 前端 POST /api/tasks  body={category_id, api_config_id, target_count, ...,
                                resume_from_task_id?}
2. API 加载 category + 关联 template/wordlists + api_config
3. 把上述内容复制为 snapshot 字段,INSERT Task,status=pending
4. 创建 output_dir = data/task-{id}/
5. 如有 resume_from_task_id:
     拷贝旧 task 的 *.csv 到新 output_dir
6. spawn subprocess: python -m service.worker --task-id={id}
   记录 worker_pid,UPDATE status=running
7. 返回 task_id
```

### 5.2 Worker 主循环

```
1. 启动:从 DB 读 Task by id (含所有 snapshot 字段)
2. 扫 output_dir 下已有 CSV,数行 → 设 current_count
3. 根据 snapshot_api_type 选 OpenAI SDK / requests
4. ThreadPoolExecutor(max_workers) 并发请求:
   while current_count < target_count:
     batch = thread_pool.submit(call_llm × N)
     for result in batch:
       解析返回 → 写 CSV (写满 max_per_file 切下一卷)
       current_count += k
     每 K 条 (K = max(50, batch_size×5),后端写死) → UPDATE Task.progress_current
                                                  + INSERT TaskEvent(type=progress,
                                                    message="N/total")
                                                  + 触发一次 progress watcher
     检查 Task.status:见到 aborted 立刻退出
5. 完成 → INSERT TaskEvent(finished) + UPDATE status=succeeded
6. 异常:
   - 已知业务错误 (429 重试穷尽、鉴权失败、连续 10 批全失败 等):
       UPDATE status=failed, error_msg=简短原因
       INSERT TaskEvent(error, message=简短)
   - 未知异常:
       traceback 写 logs/task-{id}.log
       UPDATE status=failed, error_msg=异常类型
```

### 5.3 中止

```
前端 POST /api/tasks/{id}/abort
  ↓
API: UPDATE Task.status='aborted'
     os.kill(worker_pid, SIGTERM)   -- 兜底强杀,2 秒后 SIGKILL
  ↓
Worker 主循环每次 batch 后检查 status,见 aborted 退出
INSERT TaskEvent(aborted)
```

### 5.4 续跑 (resume)

不复用旧 task。创建新 task 并传 `resume_from_task_id`:

- 拷贝旧 `data/task-{old}/*.csv` 到新 `data/task-{new}/`
- 新任务 worker 启动后照旧扫目录数行,从断点继续

每个 task 严格独立目录,绝对避免并发写冲突。

### 5.5 服务重启恢复

API 启动时扫所有 `status=running` 的 Task:

- worker_pid 进程仍在 → 继续监控,worker 自己跑
- 进程不在 → UPDATE status=failed, error_msg="服务重启,worker 已丢失"

用户在 UI 上看到 failed 任务,可用「以此为基础续跑」恢复进度。

## 6. HTTP 接口

### 6.1 配置管理

```
GET    /api/api-configs
POST   /api/api-configs           body: name, base_url, api_key, model_name, type
PUT    /api/api-configs/{id}
DELETE /api/api-configs/{id}      有 running task 引用则 409
POST   /api/api-configs/{id}/test 发一个最简请求,返回连接是否可用

GET    /api/wordlists             ?kind=scenario|tone|other
POST   /api/wordlists
PUT    /api/wordlists/{id}
DELETE /api/wordlists/{id}

GET    /api/prompt-templates
POST   /api/prompt-templates      body: name, body, variables
PUT    /api/prompt-templates/{id}
DELETE /api/prompt-templates/{id}

GET    /api/categories            ?sample_type=black|gray|white
GET    /api/categories/{id}       含 template / wordlists 展开
POST   /api/categories
PUT    /api/categories/{id}
DELETE /api/categories/{id}
```

**列表/详情中的 api_key 默认脱敏返回 `sk-****d4`,前端编辑表单点「显示」按钮时调 `GET /api/api-configs/{id}/reveal` 返回明文。该接口在响应头加 `Cache-Control: no-store`。**

### 6.2 任务管理

```
GET    /api/tasks                 ?status=&category_id=&page=&size=
POST   /api/tasks                 body: category_id, api_config_id, target_count,
                                        batch_size, max_workers, max_per_file,
                                        created_by_label, resume_from_task_id?
GET    /api/tasks/{id}            含 snapshot + 最新进度 + 最近 50 条 events
POST   /api/tasks/{id}/abort
DELETE /api/tasks/{id}            ?delete_files=true|false 默认 true
GET    /api/tasks/{id}/preview    返回 CSV 前 200 行的 JSON
GET    /api/tasks/{id}/download   StreamingResponse 下载完整 CSV (多卷打包 zip)
GET    /api/tasks/{id}/events     ?page=&size= 翻页查看 events
GET    /api/tasks/{id}/log        ?lines=1000 tail logs/task-{id}.log
```

### 6.3 SSE 进度推送

```
GET    /api/tasks/{id}/stream     Content-Type: text/event-stream

事件类型:
  progress  { current, total, ts }
  event     { type, message, ts }    -- 镜像 TaskEvent
  finished  { status, ts }           -- 服务端发完主动关闭连接
  error     { message, ts }
```

前端用 `EventSource(url)`,断线自动重连,后端从 `last_event_id` 之后的 TaskEvent 回放,不丢消息。

### 6.4 辅助

```
GET    /api/sample-types          返回 ['black','gray','white'] + 各自的 category 计数
```

## 7. 前端页面

### 7.1 导航

```
顶部菜单
├─ 任务中心    (默认页)
├─ 配置管理
│   ├─ 接口配置 (ApiConfig)
│   ├─ 词库管理 (WordList)
│   ├─ Prompt 模板
│   └─ 分类管理 (Category)
└─ 帮助 / 关于
```

页面顶部固定显示「⚠️ 本系统无访问控制,请勿暴露公网」横幅。

### 7.2 页面清单

1. **任务列表** — Ant Design Table:ID / 名称 / 类型 / 分类 / 状态 / 进度条 / 创建时间 / 操作。顶部状态、类型、分类筛选 +「新建任务」
2. **任务详情** — 见 8.3
3. **新建任务向导** — 3 步:选分类 → 选 API 配置 → 数量/并发参数,有「试跑模式」按钮一键填 100 条
4. **接口配置管理** — 列表 + 表单,每行有「测试连接」按钮;Key 默认脱敏
5. **词库管理** — 按 kind tab 分组,编辑器是可加可删的字符串数组
6. **Prompt 模板** — 大文本框 + 占位符高亮 +「预览渲染」按钮(选一个 Category 套数据看实际 prompt)
7. **分类管理** — 按 sample_type 分 tab,表单关联 template + 两个 wordlist

### 7.3 任务详情页布局

从上到下:

1. 顶栏:任务标识 + 状态徽章 + 操作按钮(中止/续跑/下载/删除) + SSE 连接状态指示
2. 进度面板:大进度条 + 已用时 / 预计剩余 / 平均速率 / 失败重试计数
3. 双栏:
   - 左:Snapshot 只读展示(分类、API、目标、并发、单批、模板链接、输出目录)
   - 右:事件流(SSE 实时,最新在底,monospace,带级别配色)
4. CSV 预览(前 200 行,可折叠)

### 7.4 通用 UX

- 删除全部二次确认
- SSE 断开右上角红点提示
- 表格优先,卡片次之
- 不做暗色 / 国际化 / 移动端

## 8. 错误处理与边界场景

### 8.1 LLM API 异常

| 场景 | Worker 行为 |
|------|-------------|
| 429 限流 | 指数退避 1→2→4→8→16→30 秒,累计 5 次失败放弃当批,记 warning |
| 401/403 | 立刻终止,status=failed,error_msg="API 鉴权失败" |
| 5xx / 超时 | 同 429 退避重试 |
| 连续 10 批全失败 | 终止任务,避免空转 |
| 返回内容解析失败 | 记 warning,跳过该批,不影响整体 |

### 8.2 Worker 进程异常

- Worker 主循环 try/except 包裹,未捕获异常 → TaskEvent(error) + traceback 落 logs + status=failed
- 进程被外部 kill -9:API supervisor 每 30 秒检查 running task 的 worker_pid,死了标 failed

### 8.3 FastAPI 服务重启

- 启动扫所有 running task 的 pid;不在则标 failed (error_msg="服务重启,worker 已丢失")
- 用户用「续跑」恢复

### 8.4 SQLite 并发

- 开启 `PRAGMA journal_mode=WAL`
- Worker 写进度独立连接,API 用连接池
- Worker 内存累计 K 条才落库一次(K 后端写死,不暴露 UI)

### 8.5 SSE 连接

- 浏览器断开自动重连
- 重连后从 `last_event_id` 之后回放 TaskEvent
- 任务结束推 finished 事件后主动关闭

### 8.6 磁盘 / 路径

- 每个 task 独立 `data/task-{id}/`
- 大 CSV 下载用 StreamingResponse,多卷打包 zip 流式输出
- 删除任务时选项「同时删除 CSV」默认勾选

### 8.7 配置校验

- 创建/更新 PromptTemplate:`body` 中 `{xxx}` 占位符必须出现在 `variables`,反之亦然
- 创建 Task:`target_count > 0`、`max_workers ∈ [1, 50]`、`batch_size ∈ [1, 100]`
- DELETE Category/Template/WordList:running task 引用 → 409,只有历史 snapshot 引用 → 允许

## 9. 测试策略

### 9.1 单元 (pytest)

- 数据模型 / CRUD
- Prompt 占位符渲染与校验
- API Key 脱敏函数
- CSV 行数统计 / resume 拷贝逻辑

### 9.2 集成

- FastAPI + 内存 SQLite,跑一遍主要 REST 接口
- 用 `httpx.MockTransport` 或本地 mock server 模拟 LLM,跑 100 条小任务全流程

### 9.3 Worker

- Worker 入口支持 `--mock-llm` 跳过真实调用,用伪造数据测 abort / resume / 并发 / 重试
- abort 测试:跑 1000 条,200 条时 SQL 改 status=aborted,断言 worker 在 ≤2 个 batch 内退出

### 9.4 端到端 (可选)

- Playwright 跑前端关键路径(创建 → 看进度 → 下载)
- 内部小工具,有时间再加

### 9.5 数据迁移

- `seed_from_legacy.py` 加单测,断言 33 个黑样本分类 + 灰白样本相关模板/词库导入成功

## 10. 部署形态

- 单 Docker 镜像,`uvicorn service.main:app --host 0.0.0.0 --port 8000`
- 镜像内含编译好的 React `dist/`,FastAPI 同源托管
- Volume:
  - `/app/data` → 宿主机持久化 CSV
  - `/app/logs` → 宿主机持久化日志
  - `/app/app.db` → 宿主机持久化 SQLite
- 启动后访问 `http://<host>:8000` 即用

## 11. 技术栈汇总

| 层 | 选型 |
|---|---|
| 前端框架 | React 18 + TypeScript |
| 前端组件库 | Ant Design 5 |
| 前端构建 | Vite |
| 后端框架 | FastAPI |
| ORM | SQLAlchemy 2 (或 SQLModel) |
| 数据库 | SQLite (WAL 模式) |
| 进度推送 | SSE (sse-starlette) |
| LLM 客户端 | openai (兼容代理) + requests (raw 接口) |
| 测试 | pytest + httpx + Playwright(可选) |
| 部署 | Docker + uvicorn |

## 12. 待办与后续可演进项

不在 v1 实现,但设计上预留:

- 真正的用户登录 (加一张 User 表,Task 关联 user_id)
- 任务调度优先级
- 多机部署(届时把 SQLite 换 Postgres,subprocess 换 Celery+Redis,数据模型不变)
- CSV 二次处理(去重 / 抽样 / 评测)
