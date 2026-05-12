# LLM 样本数据生产服务 · 前端设计文档（Part 3）

- 起草日期：2026-05-12
- 关联后端版本：Part 2（main 分支，commit `ed9eacd` 及之前）
- 关联设计文档：`2026-05-11-llm-data-service-design.md`

## 1. 背景与目标

后端 Part 1 + Part 2 已完成全部 REST API 和 SSE 推送能力。Part 3 目标是为内部小团队（2~10 人）提供网页交互界面，实现：

- 在网页上启动、监控、中止、续跑数据生成任务
- 实时查看任务进度（SSE 推送）
- 预览并下载生成结果（CSV）
- 配置接口/模板/词库/分类（第二阶段）

## 2. 范围与边界

### 第一阶段 MVP（任务中心）

**包含：**
- 任务列表页（表格、状态筛选、分页、排序）
- 创建任务弹窗（下拉选择已有分类/API 配置，输入目标数量/并发参数）
- 任务详情页（进度条、事件时间线、日志查看器、CSV 预览、下载按钮）
- Abort 按钮（确认弹窗）
- SSE 实时进度推送（含断线重连）
- 全局 Toast 通知
- 404/错误页面

**不包含：**
- API 配置/词库/Prompt 模板/分类的完整 CRUD（只读下拉选择）
- 创建任务时的分类/配置新建
- 编辑/删除分类和配置
- 移动端适配、国际化、暗色主题

### 第二阶段（配置管理）

补全以下资源的 CRUD 页面：
- API 配置（含连通性测试、密钥揭示）
- 词库管理
- Prompt 模板管理（含变量校验）
- 分类管理（关联词库和模板）

## 3. 技术栈

| 层 | 选型 | 版本/说明 |
|---|---|---|
| 构建工具 | Vite | React + TypeScript 模板 |
| UI 框架 | React | 18.x |
| UI 组件库 | Ant Design | 5.x |
| 类型系统 | TypeScript | 5.x |
| 服务端状态管理 | TanStack Query (React Query) | 5.x — 只管理服务端数据和缓存 |
| 客户端状态管理 | Zustand | 4.x — 只管理 UI 状态、toast、SSE 连接状态 |
| 路由 | `wouter` | 3.x — 轻量，本项目只有 2 个页面 |
| HTTP 客户端 | `fetch` | 浏览器原生，配合 TanStack Query 使用 |
| SSE | 原生 `EventSource` | 浏览器原生，断线自动重连 |

### 数据所有权原则（关键）

> **TanStack Query 是服务端数据的唯一数据源。** 任务主数据（列表、详情、事件、日志、预览）全部通过 `useQuery` 获取和缓存，不在 Zustand 中重复存储。
>
> **Zustand 只管理客户端 UI 状态：** toast 通知队列、SSE 连接状态（连接中/已连接/已断开/重连中）、页面布局偏好（如侧边栏折叠）、全局错误弹窗控制。
>
> 任何组件需要任务数据时，必须通过 `useQuery` 读取；需要 SSE 状态或 toast 时，通过 `useAppStore` 读取。避免双数据源导致的不一致性。

## 4. 目录结构

```
frontend/
├── index.html
├── vite.config.ts          # proxy /api → localhost:8000
├── package.json
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
├── src/
│   ├── main.tsx            # React root，QueryClientProvider
│   ├── App.tsx             # 路由 + 布局 shell
│   ├── api/
│   │   ├── client.ts       # fetch 封装，baseURL=/api，统一错误处理
│   │   ├── tasks.ts        # 任务相关 API 函数
│   │   ├── configs.ts      # 配置相关 API 函数（第一阶段只读）
│   │   └── types.ts        # 共享 DTO 类型（从 backend/schemas.py 映射）
│   ├── hooks/
│   │   ├── useTaskStream.ts   # SSE EventSource hook
│   │   └── useTaskPolling.ts  # 任务列表轮询 hook
│   ├── store/
│   │   └── appStore.ts        # Zustand store
│   ├── components/
│   │   ├── Layout.tsx         # 顶部导航 + 内容区
│   │   ├── TaskList.tsx       # 任务列表表格
│   │   ├── TaskCreateModal.tsx # 创建任务弹窗
│   │   ├── TaskDetail.tsx     # 任务详情页（子组件容器）
│   │   ├── TaskProgress.tsx   # 进度条组件
│   │   ├── TaskEventTimeline.tsx # 事件时间线
│   │   ├── TaskPreview.tsx    # CSV 预览表格
│   │   ├── TaskLogViewer.tsx  # 日志查看器
│   │   ├── SSEStatusBadge.tsx # SSE 连接状态指示器
│   │   └── ToastContainer.tsx # 全局 Toast 容器
│   └── pages/
│       ├── HomePage.tsx       # 任务列表（默认页）
│       └── TaskDetailPage.tsx # 任务详情
└── public/                  # 静态资源（favicon 等）
```

## 5. 数据流

### 5.1 任务列表页

后端只支持 `status`、`category_id`、`page`、`size` 参数，返回 `list[TaskOut]` **无 total 计数**。前端分页降级为简单翻页（上一页/下一页），不显示总页数；排序在前端内存中完成。

```
HomePage
└── useTaskList(filters)        // useQuery(['tasks', filters], fetchTasks)
    └── 每 3s 轮询 running 任务
    └── 点击行 → navigate(`/tasks/${id}`)
    └── 点击"新建" → 打开 TaskCreateModal
```

### 5.2 任务详情页

```
TaskDetailPage (taskId)
├── useTaskDetail(taskId)       // useQuery(['task', taskId], fetchTaskDetail)
│   └── 初始加载 + 手动刷新按钮
├── useTaskStream(taskId)       // 自定义 hook，管理 EventSource
│   ├── 连接 /api/tasks/{taskId}/stream
│   ├── 收到 event → queryClient.invalidateQueries(['task', taskId])
│   │   └── TanStack Query 自动刷新详情数据
│   ├── 收到 finished 事件 → 主动 close EventSource
│   └── 断线 → 浏览器原生自动重连（自动带 Last-Event-ID），轮询兜底
├── useTaskPreview(taskId)      // useQuery(['preview', taskId], fetchPreview)
├── useTaskLog(taskId)          // useQuery(['log', taskId], fetchLog)
└── useTaskEvents(taskId)       // useQuery(['events', taskId], fetchEvents)
```

### 5.3 创建任务

```
TaskCreateModal
├── useConfigs()                // useQuery(['configs'], fetchConfigs) — 只读
├── useCategories()             // useQuery(['categories'], fetchCategories) — 只读
├── 表单提交 → mutate(createTask)
│   └── onSuccess → invalidateQueries(['tasks']) + toast.success() + 跳转详情页
│   └── onError → toast.error()
```

### 5.4 Abort 任务

```
TaskDetailPage
└── mutate(abortTask)
    └── onSuccess → invalidateQueries(['task', taskId]) + toast.success()
    └── onError(409) → toast.warning("任务已结束，无法中止")
```

## 6. SSE 对接策略

### EventSource 封装 (`useTaskStream`)

后端发送命名 SSE 事件（`event` 和 `finished`），必须用 `addEventListener` 注册，不能用 `onmessage`。浏览器原生 `EventSource` 断线后会**自动重连**，并自动在重连请求中携带 `Last-Event-ID` header（后端 `tasks_stream.py:19` 已处理）。**不在 `onerror` 中手动 `close()` + 重建**，否则会丢失 last event id 上下文。

```typescript
function useTaskStream(taskId: number) {
  const setSseState = useAppStore(s => s.setSseState);
  const queryClient = useQueryClient();

  useEffect(() => {
    const es = new EventSource(`/api/tasks/${taskId}/stream`);
    let closedByUs = false;

    es.addEventListener('open', () => {
      setSseState(taskId, 'connected');
    });

    es.addEventListener('event', (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      // 刷新任务详情（自动拉取最新 events + status）
      queryClient.invalidateQueries({ queryKey: ['task', taskId] });
    });

    es.addEventListener('finished', (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      queryClient.invalidateQueries({ queryKey: ['task', taskId] });
      closedByUs = true;
      es.close();
      setSseState(taskId, 'closed');
    });

    es.addEventListener('error', () => {
      // 依赖浏览器原生自动重连；浏览器会自动带 Last-Event-ID
      // 状态变化：connected → reconnecting（浏览器内部）→ connected
      if (es.readyState === EventSource.CONNECTING) {
        setSseState(taskId, 'reconnecting');
      }
      // 如果浏览器长期重连失败（如网络恢复后），由轮询兜底
    });

    return () => { closedByUs = true; es.close(); };
  }, [taskId]);
}
```

**重连兜底：** 原生 EventSource 自动重连间隔固定约 3s，如果超过 60s 仍未恢复，轮询机制（`useTaskPolling` 3s 间隔）会保持数据新鲜。如果确实需要程序控制重连（如用户点击"刷新"按钮），应先通过 `GET /api/tasks/{taskId}/events?since_id=<last_id>` 补拉遗漏事件，再重建连接。

### SSE 状态（Zustand）

```typescript
interface AppState {
  sseStates: Record<number, 'connecting' | 'connected' | 'reconnecting' | 'closed'>;
  setSseState: (taskId: number, state: SseState) => void;
  toasts: ToastItem[];
  addToast: (toast: ToastItem) => void;
  removeToast: (id: string) => void;
}
```

## 7. API 类型映射

从 `backend/service/schemas.py` 直接映射：

```typescript
// src/api/types.ts
export type TaskStatus = 'pending' | 'running' | 'succeeded' | 'failed' | 'aborted';
export type SampleType = 'black' | 'gray' | 'white';

export interface TaskOut {
  id: number;
  sample_type: SampleType;
  category_name: string;
  api_config_id: number;
  api_model: string;
  target_count: number;
  batch_size: number;
  max_workers: number;
  max_per_file: number;
  status: TaskStatus;
  progress_current: number;
  progress_total: number;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  error_msg: string | null;
  output_dir: string;
  created_by_label: string | null;
  resume_from_task_id: number | null;
}

export interface TaskDetail extends TaskOut {
  snapshot_prompt_body: string;
  snapshot_scenario_items: string[];
  snapshot_tone_items: string[];
  snapshot_api_base_url: string;
  snapshot_api_type: 'openai' | 'raw';
  recent_events: TaskEventOut[];
}

export interface TaskEventOut {
  id: number;
  ts: string;
  type: string;
  message: string;
}

export interface TaskCreatePayload {
  category_id: number;
  api_config_id: number;
  target_count: number;
  batch_size: number;
  max_workers: number;
  max_per_file: number;
  created_by_label?: string;
  resume_from_task_id?: number;
}

export interface CategoryOut {
  id: number;
  sample_type: SampleType;
  name: string;
  description: string;
  prompt_template_id: number;
  scenario_list_id: number;
  tone_list_id: number;
  default_target_count: number;
}

export interface ApiConfigOut {
  id: number;
  name: string;
  base_url: string;
  api_key_masked: string;
  model_name: string;
  type: 'openai' | 'raw';
}

export interface WordListOut {
  id: number;
  name: string;
  kind: 'scenario' | 'tone' | 'other';
  items: string[];
}

export interface PromptTemplateOut {
  id: number;
  name: string;
  body: string;
  variables: string[];
}
```

## 8. 错误处理策略

| 场景 | 处理方式 |
|---|---|
| API 500 错误 | Toast 通知 + 按钮重试 |
| API 404（任务不存在） | 跳转 404 页面 |
| API 409（任务已结束，无法 abort） | Toast warning，按钮禁用 |
| API 400（表单校验失败） | 表单内显示错误信息 |
| SSE 断线 | SSEStatusBadge 显示"重连中"（浏览器原生自动重连） |
| SSE 持续断线（>60s） | 轮询兜底保持数据新鲜，Toast 提示网络异常 |
| 下载失败 | Toast error + 保留按钮可重试 |

## 9. 路由设计

使用 `wouter`（1KB），本项目只有 2 个顶级路由：

```tsx
// App.tsx
<Layout>
  <Route path="/" component={HomePage} />
  <Route path="/tasks/:id" component={TaskDetailPage} />
  <Route component={NotFoundPage} />
</Layout>
```

点击任务列表行 → `navigate(`/tasks/${id}`)`，无需复杂路由守卫（无登录）。

## 10. Vite 开发代理配置

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/healthz': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

## 11. 测试策略

第一阶段 MVP 以手工 E2E 测试为主（启动后端 + 前端 dev server，走完整流程）。

第二阶段补单元测试：
- `useTaskStream` hook 测试（mock EventSource）
- API 函数测试（mock fetch）
- 组件快照测试（React Testing Library）

## 12. 部署

生产构建：

```bash
cd frontend && npm run build
```

输出到 `frontend/dist/`，FastAPI 的 `static.py` 会自动检测并挂载为 SPA fallback。开发阶段 `npm run dev` 通过 Vite 代理访问后端 API。
