# LLM 样本数据生产服务 · Part 3 前端实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建 React + TypeScript 前端，实现 Phase 1 MVP：任务列表、创建、详情、SSE 实时进度、abort、preview、download、log。后端 API 已全部就绪，前端从 0 搭建。

**Architecture:** Vite + React 18 + TypeScript + Ant Design 5 + TanStack Query 5（服务端状态）+ Zustand 4（UI 状态）+ wouter（轻量路由）。TanStack Query 是服务端数据唯一数据源，Zustand 只管理 toast 和 SSE 连接状态。FastAPI 同源托管生产构建。

**Tech Stack:** Vite 5, React 18, TypeScript 5, Ant Design 5, @tanstack/react-query 5, zustand 4, wouter 3

**Spec:** `docs/superpowers/specs/2026-05-12-llm-data-service-frontend-design.md`

**Branch base:** `main`

---

## 文件结构

```
frontend/
├── index.html
├── vite.config.ts
├── package.json
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── api/
│   │   ├── client.ts       # fetch 封装，统一错误处理
│   │   ├── tasks.ts        # 任务 API 函数
│   │   ├── configs.ts      # 配置 API 函数（只读）
│   │   └── types.ts        # DTO 类型
│   ├── hooks/
│   │   ├── useTaskStream.ts   # SSE EventSource hook
│   │   └── useTaskPolling.ts  # 任务列表轮询 hook
│   ├── store/
│   │   └── appStore.ts        # Zustand：toast + SSE 状态
│   ├── components/
│   │   ├── Layout.tsx
│   │   ├── TaskList.tsx
│   │   ├── TaskCreateModal.tsx
│   │   ├── TaskDetail.tsx
│   │   ├── TaskProgress.tsx
│   │   ├── TaskEventTimeline.tsx
│   │   ├── TaskPreview.tsx
│   │   ├── TaskLogViewer.tsx
│   │   ├── SSEStatusBadge.tsx
│   │   └── ToastContainer.tsx
│   └── pages/
│       ├── HomePage.tsx
│       └── TaskDetailPage.tsx
└── public/
```

---

## Task 1: 项目脚手架

**Files:**
- Create: `frontend/` 目录及 Vite 模板
- Create: `frontend/vite.config.ts`
- Modify: `frontend/index.html`
- Modify: `frontend/tsconfig.json`

- [ ] **Step 1: 用 Vite 创建项目**

```bash
cd /Users/lanhezheng/llm-data-service
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

- [ ] **Step 2: 安装运行时依赖**

```bash
cd /Users/lanhezheng/llm-data-service/frontend
npm install antd @tanstack/react-query zustand wouter
```

- [ ] **Step 3: 配置 Vite 代理**

创建 `frontend/vite.config.ts`（覆盖默认）：

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
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

- [ ] **Step 4: 修改 index.html 标题**

修改 `frontend/index.html`：

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>LLM 样本数据生产服务</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 5: 清理默认样板代码**

删除 `frontend/src/App.css`（如果存在），清空 `frontend/src/App.tsx`：

```tsx
function App() {
  return <div>LLM Data Service</div>;
}

export default App;
```

清空 `frontend/src/index.css`（保留文件但清空内容，后续 Ant Design 自带样式）。

- [ ] **Step 6: 验证开发服务器能启动**

```bash
cd /Users/lanhezheng/llm-data-service/frontend
npm run dev
```

另开一个终端验证：
```bash
curl -s http://localhost:5173/ | head -5
# 期望输出包含 "LLM Data Service" 或 HTML 内容
```

停止 dev server（Ctrl+C）。

- [ ] **Step 7: Commit**

```bash
cd /Users/lanhezheng/llm-data-service
git add frontend/
git commit -m "chore(frontend): scaffold Vite + React + TS + deps"
```

---

## Task 2: API 类型定义 + 客户端封装

**Files:**
- Create: `frontend/src/api/types.ts`
- Create: `frontend/src/api/client.ts`

- [ ] **Step 1: 写 types.ts**

创建 `frontend/src/api/types.ts`：

```typescript
export type TaskStatus = 'pending' | 'running' | 'succeeded' | 'failed' | 'aborted';
export type SampleType = 'black' | 'gray' | 'white';
export type ApiType = 'openai' | 'raw';
export type WordListKind = 'scenario' | 'tone' | 'other';

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
  snapshot_api_type: ApiType;
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
  type: ApiType;
}

export interface WordListOut {
  id: number;
  name: string;
  kind: WordListKind;
  items: string[];
}

export interface PromptTemplateOut {
  id: number;
  name: string;
  body: string;
  variables: string[];
}

export interface PreviewData {
  header: string[];
  rows: string[][];
}

export interface LogData {
  lines: string[];
}
```

- [ ] **Step 2: 写 client.ts**

创建 `frontend/src/api/client.ts`：

```typescript
const BASE = '';

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    const text = await res.text().catch(() => 'unknown error');
    throw new ApiError(res.status, text);
  }
  return res.json() as Promise<T>;
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => 'unknown error');
    throw new ApiError(res.status, text);
  }
  return res.json() as Promise<T>;
}

export async function apiDelete(path: string): Promise<void> {
  const res = await fetch(`${BASE}${path}`, { method: 'DELETE' });
  if (!res.ok) {
    const text = await res.text().catch(() => 'unknown error');
    throw new ApiError(res.status, text);
  }
}
```

- [ ] **Step 3: 验证 TypeScript 编译通过**

```bash
cd /Users/lanhezheng/llm-data-service/frontend
npx tsc --noEmit
```

期望：无错误输出。

- [ ] **Step 4: Commit**

```bash
cd /Users/lanhezheng/llm-data-service
git add frontend/src/api/
git commit -m "feat(frontend): API types and fetch client"
```

---

## Task 3: API 函数（tasks + configs）

**Files:**
- Create: `frontend/src/api/tasks.ts`
- Create: `frontend/src/api/configs.ts`

- [ ] **Step 1: 写 tasks.ts**

创建 `frontend/src/api/tasks.ts`：

```typescript
import { apiGet, apiPost, apiDelete } from './client';
import type { TaskOut, TaskDetail, TaskCreatePayload, TaskEventOut, PreviewData, LogData } from './types';

export function listTasks(params?: { status?: string; category_id?: number; page?: number; size?: number }) {
  const search = new URLSearchParams();
  if (params?.status) search.set('status', params.status);
  if (params?.category_id) search.set('category_id', String(params.category_id));
  if (params?.page) search.set('page', String(params.page));
  if (params?.size) search.set('size', String(params.size));
  const qs = search.toString();
  return apiGet<TaskOut[]>(`/api/tasks${qs ? '?' + qs : ''}`);
}

export function getTask(id: number) {
  return apiGet<TaskDetail>(`/api/tasks/${id}`);
}

export function createTask(payload: TaskCreatePayload) {
  return apiPost<TaskOut>('/api/tasks', payload);
}

export function abortTask(id: number) {
  return apiPost<{ id: number; status: string }>(`/api/tasks/${id}/abort`, {});
}

export function deleteTask(id: number) {
  return apiDelete(`/api/tasks/${id}`);
}

export function previewTask(id: number) {
  return apiGet<PreviewData>(`/api/tasks/${id}/preview`);
}

export function downloadTask(id: number) {
  window.location.href = `/api/tasks/${id}/download`;
}

export function listTaskEvents(id: number, since_id?: number, limit?: number) {
  const search = new URLSearchParams();
  if (since_id !== undefined) search.set('since_id', String(since_id));
  if (limit !== undefined) search.set('limit', String(limit));
  const qs = search.toString();
  return apiGet<TaskEventOut[]>(`/api/tasks/${id}/events${qs ? '?' + qs : ''}`);
}

export function getTaskLog(id: number, lines?: number) {
  const search = new URLSearchParams();
  if (lines !== undefined) search.set('lines', String(lines));
  const qs = search.toString();
  return apiGet<LogData>(`/api/tasks/${id}/log${qs ? '?' + qs : ''}`);
}
```

- [ ] **Step 2: 写 configs.ts**

创建 `frontend/src/api/configs.ts`：

```typescript
import { apiGet } from './client';
import type { ApiConfigOut, CategoryOut, WordListOut, PromptTemplateOut } from './types';

export function listApiConfigs() {
  return apiGet<ApiConfigOut[]>('/api/api-configs');
}

export function listCategories(sample_type?: string) {
  const qs = sample_type ? `?sample_type=${encodeURIComponent(sample_type)}` : '';
  return apiGet<CategoryOut[]>(`/api/categories${qs}`);
}

export function listWordlists(kind?: string) {
  const qs = kind ? `?kind=${encodeURIComponent(kind)}` : '';
  return apiGet<WordListOut[]>(`/api/wordlists${qs}`);
}

export function listPromptTemplates() {
  return apiGet<PromptTemplateOut[]>('/api/prompt-templates');
}
```

- [ ] **Step 3: 验证 TypeScript 编译通过**

```bash
cd /Users/lanhezheng/llm-data-service/frontend
npx tsc --noEmit
```

期望：无错误。

- [ ] **Step 4: Commit**

```bash
cd /Users/lanhezheng/llm-data-service
git add frontend/src/api/tasks.ts frontend/src/api/configs.ts
git commit -m "feat(frontend): task and config API functions"
```

---

## Task 4: Zustand Store

**Files:**
- Create: `frontend/src/store/appStore.ts`

- [ ] **Step 1: 写 appStore.ts**

创建 `frontend/src/store/appStore.ts`：

```typescript
import { create } from 'zustand';

export type SseState = 'connecting' | 'connected' | 'reconnecting' | 'closed';

export interface ToastItem {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
}

interface AppState {
  sseStates: Record<number, SseState>;
  setSseState: (taskId: number, state: SseState) => void;
  toasts: ToastItem[];
  addToast: (toast: Omit<ToastItem, 'id'>) => void;
  removeToast: (id: string) => void;
}

let toastIdCounter = 0;

export const useAppStore = create<AppState>((set) => ({
  sseStates: {},
  setSseState: (taskId, state) =>
    set((s) => ({
      sseStates: { ...s.sseStates, [taskId]: state },
    })),
  toasts: [],
  addToast: (toast) =>
    set((s) => ({
      toasts: [...s.toasts, { ...toast, id: `toast-${++toastIdCounter}` }],
    })),
  removeToast: (id) =>
    set((s) => ({
      toasts: s.toasts.filter((t) => t.id !== id),
    })),
}));
```

- [ ] **Step 2: 验证 TypeScript 编译通过**

```bash
cd /Users/lanhezheng/llm-data-service/frontend
npx tsc --noEmit
```

- [ ] **Step 3: Commit**

```bash
cd /Users/lanhezheng/llm-data-service
git add frontend/src/store/
git commit -m "feat(frontend): Zustand store for SSE state and toast"
```

---

## Task 5: useTaskStream Hook（SSE）

**Files:**
- Create: `frontend/src/hooks/useTaskStream.ts`
- Create: `frontend/src/hooks/useTaskPolling.ts`

- [ ] **Step 1: 写 useTaskStream.ts**

创建 `frontend/src/hooks/useTaskStream.ts`：

```typescript
import { useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useAppStore } from '../store/appStore';

export function useTaskStream(taskId: number | undefined) {
  const queryClient = useQueryClient();
  const setSseState = useAppStore((s) => s.setSseState);
  const lastIdRef = useRef(0);

  useEffect(() => {
    if (taskId === undefined) return;

    const es = new EventSource(`/api/tasks/${taskId}/stream`);
    let closedByUs = false;

    es.addEventListener('open', () => {
      setSseState(taskId, 'connected');
    });

    es.addEventListener('event', (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      if (e.lastEventId) {
        lastIdRef.current = parseInt(e.lastEventId, 10);
      }
      queryClient.invalidateQueries({ queryKey: ['task', taskId] });
    });

    es.addEventListener('finished', (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      if (e.lastEventId) {
        lastIdRef.current = parseInt(e.lastEventId, 10);
      }
      queryClient.invalidateQueries({ queryKey: ['task', taskId] });
      closedByUs = true;
      es.close();
      setSseState(taskId, 'closed');
    });

    es.addEventListener('error', () => {
      if (es.readyState === EventSource.CONNECTING) {
        setSseState(taskId, 'reconnecting');
      }
    });

    return () => {
      closedByUs = true;
      es.close();
    };
  }, [taskId, queryClient, setSseState]);

  return { lastEventId: lastIdRef.current };
}
```

- [ ] **Step 2: 写 useTaskPolling.ts**

创建 `frontend/src/hooks/useTaskPolling.ts`：

```typescript
import { useQuery } from '@tanstack/react-query';
import { listTasks } from '../api/tasks';

export function useTaskPolling(enabled: boolean) {
  return useQuery({
    queryKey: ['tasks-running'],
    queryFn: () => listTasks({ status: 'running', size: 200 }),
    refetchInterval: enabled ? 3000 : false,
    refetchIntervalInBackground: true,
    enabled,
  });
}
```

- [ ] **Step 3: 验证 TypeScript 编译通过**

```bash
cd /Users/lanhezheng/llm-data-service/frontend
npx tsc --noEmit
```

- [ ] **Step 4: Commit**

```bash
cd /Users/lanhezheng/llm-data-service
git add frontend/src/hooks/
git commit -m "feat(frontend): SSE stream hook + task polling hook"
```

---

## Task 6: Layout + 路由 + App 入口

**Files:**
- Create: `frontend/src/components/Layout.tsx`
- Create: `frontend/src/components/ToastContainer.tsx`
- Create: `frontend/src/components/SSEStatusBadge.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/main.tsx`

- [ ] **Step 1: 写 Layout.tsx**

创建 `frontend/src/components/Layout.tsx`：

```tsx
import { Layout as AntLayout, Menu } from 'antd';
import { Link, useLocation } from 'wouter';

const { Header, Content } = AntLayout;

export function Layout({ children }: { children: React.ReactNode }) {
  const [location] = useLocation();

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center' }}>
        <div style={{ color: 'white', fontSize: 18, fontWeight: 'bold', marginRight: 32 }}>
          LLM 样本数据服务
        </div>
        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={[location === '/' ? 'home' : '']}
          items={[
            { key: 'home', label: <Link href="/">任务中心</Link> },
          ]}
          style={{ flex: 1 }}
        />
      </Header>
      <Content style={{ padding: 24, background: '#f0f2f5' }}>
        {children}
      </Content>
    </AntLayout>
  );
}
```

- [ ] **Step 2: 写 ToastContainer.tsx**

创建 `frontend/src/components/ToastContainer.tsx`：

```tsx
import { message } from 'antd';
import { useEffect } from 'react';
import { useAppStore } from '../store/appStore';

export function ToastContainer() {
  const toasts = useAppStore((s) => s.toasts);
  const removeToast = useAppStore((s) => s.removeToast);

  useEffect(() => {
    toasts.forEach((t) => {
      if (t.type === 'success') message.success(t.message);
      else if (t.type === 'error') message.error(t.message);
      else if (t.type === 'warning') message.warning(t.message);
      else message.info(t.message);
      removeToast(t.id);
    });
  }, [toasts, removeToast]);

  return null;
}
```

- [ ] **Step 3: 写 SSEStatusBadge.tsx**

创建 `frontend/src/components/SSEStatusBadge.tsx`：

```tsx
import { Badge, Tooltip } from 'antd';
import { useAppStore } from '../store/appStore';

const SSE_LABELS: Record<string, string> = {
  connecting: '连接中',
  connected: '已连接',
  reconnecting: '重连中',
  closed: '已关闭',
};

const SSE_COLORS: Record<string, string> = {
  connecting: 'processing',
  connected: 'success',
  reconnecting: 'warning',
  closed: 'default',
} as const;

export function SSEStatusBadge({ taskId }: { taskId: number }) {
  const state = useAppStore((s) => s.sseStates[taskId]);
  if (!state) return null;

  return (
    <Tooltip title={`SSE: ${SSE_LABELS[state] || state}`}>
      <Badge status={SSE_COLORS[state] as any} text={SSE_LABELS[state]} />
    </Tooltip>
  );
}
```

- [ ] **Step 4: 修改 App.tsx**

```tsx
import { Route, Switch } from 'wouter';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/Layout';
import { ToastContainer } from './components/ToastContainer';
import { HomePage } from './pages/HomePage';
import { TaskDetailPage } from './pages/TaskDetailPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5000,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Layout>
        <Switch>
          <Route path="/" component={HomePage} />
          <Route path="/tasks/:id" component={TaskDetailPage} />
          <Route>404: 页面不存在</Route>
        </Switch>
      </Layout>
      <ToastContainer />
    </QueryClientProvider>
  );
}

export default App;
```

- [ ] **Step 5: 修改 main.tsx**

```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

- [ ] **Step 6: 验证**

```bash
cd /Users/lanhezheng/llm-data-service/frontend
npx tsc --noEmit
npm run dev
```

浏览器访问 http://localhost:5173/ 应能看到 "LLM 样本数据服务" 顶部导航 + "任务中心" 菜单。此时 HomePage 还未实现，内容区可能空白。

停止 dev server。

- [ ] **Step 7: Commit**

```bash
cd /Users/lanhezheng/llm-data-service
git add frontend/src/components/Layout.tsx frontend/src/components/ToastContainer.tsx frontend/src/components/SSEStatusBadge.tsx frontend/src/App.tsx frontend/src/main.tsx
git commit -m "feat(frontend): Layout, routing, QueryClient, Toast, SSE badge"
```

---

## Task 7: HomePage + TaskList

**Files:**
- Create: `frontend/src/pages/HomePage.tsx`
- Create: `frontend/src/components/TaskList.tsx`

- [ ] **Step 1: 写 TaskList.tsx**

创建 `frontend/src/components/TaskList.tsx`：

```tsx
import { Table, Tag, Button, Space } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { Link } from 'wouter';
import type { TaskOut } from '../api/types';

const STATUS_COLORS: Record<string, string> = {
  pending: 'default',
  running: 'processing',
  succeeded: 'success',
  failed: 'error',
  aborted: 'warning',
};

const STATUS_LABELS: Record<string, string> = {
  pending: '待执行',
  running: '运行中',
  succeeded: '成功',
  failed: '失败',
  aborted: '已中止',
};

interface Props {
  tasks: TaskOut[];
  loading: boolean;
  onRefresh: () => void;
}

export function TaskList({ tasks, loading, onRefresh }: Props) {
  const columns: ColumnsType<TaskOut> = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 60,
      render: (id) => <Link href={`/tasks/${id}`}>{id}</Link>,
    },
    {
      title: '分类',
      dataIndex: 'category_name',
      width: 150,
    },
    {
      title: '样本类型',
      dataIndex: 'sample_type',
      width: 80,
      render: (t: string) => <Tag>{t}</Tag>,
    },
    {
      title: '模型',
      dataIndex: 'api_model',
      width: 120,
    },
    {
      title: '目标数量',
      dataIndex: 'target_count',
      width: 90,
    },
    {
      title: '进度',
      key: 'progress',
      width: 120,
      render: (_, t) => `${t.progress_current} / ${t.progress_total}`,
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 90,
      render: (s: string) => (
        <Tag color={STATUS_COLORS[s] as any}>{STATUS_LABELS[s] || s}</Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 170,
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, t) => (
        <Space>
          <Link href={`/tasks/${t.id}`}>
            <Button size="small">详情</Button>
          </Link>
        </Space>
      ),
    },
  ];

  return (
    <Table
      rowKey="id"
      columns={columns}
      dataSource={tasks}
      loading={loading}
      pagination={false}
      size="small"
    />
  );
}
```

- [ ] **Step 2: 写 HomePage.tsx**

创建 `frontend/src/pages/HomePage.tsx`：

```tsx
import { useState } from 'react';
import { Button, Space, Select, Card } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { listTasks } from '../api/tasks';
import { TaskList } from '../components/TaskList';
import { TaskCreateModal } from '../components/TaskCreateModal';

export function HomePage() {
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);
  const [page, setPage] = useState(1);
  const [createOpen, setCreateOpen] = useState(false);

  const { data: tasks, isLoading, refetch } = useQuery({
    queryKey: ['tasks', statusFilter, page],
    queryFn: () => listTasks({ status: statusFilter, page, size: 50 }),
  });

  return (
    <Card
      title="任务列表"
      extra={
        <Space>
          <Select
            placeholder="状态筛选"
            allowClear
            style={{ width: 120 }}
            options={[
              { value: 'pending', label: '待执行' },
              { value: 'running', label: '运行中' },
              { value: 'succeeded', label: '成功' },
              { value: 'failed', label: '失败' },
              { value: 'aborted', label: '已中止' },
            ]}
            onChange={(v) => { setStatusFilter(v); setPage(1); }}
          />
          <Button onClick={() => refetch()}>刷新</Button>
          <Button type="primary" onClick={() => setCreateOpen(true)}>
            新建任务
          </Button>
        </Space>
      }
    >
      <TaskList tasks={tasks || []} loading={isLoading} onRefresh={refetch} />
      <div style={{ marginTop: 16, textAlign: 'center' }}>
        <Button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
          上一页
        </Button>
        <span style={{ margin: '0 16px' }}>第 {page} 页</span>
        <Button
          disabled={!tasks || tasks.length < 50}
          onClick={() => setPage((p) => p + 1)}
        >
          下一页
        </Button>
      </div>
      <TaskCreateModal open={createOpen} onClose={() => setCreateOpen(false)} />
    </Card>
  );
}
```

- [ ] **Step 3: 创建空占位 TaskCreateModal（下一 Task 填充）**

创建 `frontend/src/components/TaskCreateModal.tsx`：

```tsx
import { Modal } from 'antd';

interface Props {
  open: boolean;
  onClose: () => void;
}

export function TaskCreateModal({ open, onClose }: Props) {
  return (
    <Modal open={open} onCancel={onClose} title="新建任务" footer={null}>
      <p>TODO</p>
    </Modal>
  );
}
```

- [ ] **Step 4: 验证**

确保后端已启动（`cd backend && .venv/bin/uvicorn service.main:app --reload`）。

```bash
cd /Users/lanhezheng/llm-data-service/frontend
npm run dev
```

浏览器访问 http://localhost:5173/，应能看到：
- "任务列表" 标题
- 状态筛选下拉、刷新按钮、新建任务按钮
- 表格列头（即使无数据）
- 上一页/下一页按钮

停止 dev server。

- [ ] **Step 5: Commit**

```bash
cd /Users/lanhezheng/llm-data-service
git add frontend/src/components/TaskList.tsx frontend/src/pages/HomePage.tsx frontend/src/components/TaskCreateModal.tsx
git commit -m "feat(frontend): HomePage + TaskList with filter and pagination"
```

---

## Task 8: TaskCreateModal（创建任务弹窗）

**Files:**
- Modify: `frontend/src/components/TaskCreateModal.tsx`

- [ ] **Step 1: 实现完整 TaskCreateModal**

替换 `frontend/src/components/TaskCreateModal.tsx`：

```tsx
import { useState } from 'react';
import { Modal, Form, InputNumber, Select, Button, Space, message } from 'antd';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { createTask } from '../api/tasks';
import { listCategories } from '../api/configs';
import { listApiConfigs } from '../api/configs';
import type { TaskCreatePayload } from '../api/types';

interface Props {
  open: boolean;
  onClose: () => void;
}

export function TaskCreateModal({ open, onClose }: Props) {
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => listCategories(),
    enabled: open,
  });

  const { data: configs } = useQuery({
    queryKey: ['api-configs'],
    queryFn: () => listApiConfigs(),
    enabled: open,
  });

  const mutation = useMutation({
    mutationFn: createTask,
    onSuccess: () => {
      message.success('任务创建成功');
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      form.resetFields();
      onClose();
    },
    onError: (err: Error) => {
      message.error(`创建失败: ${err.message}`);
    },
  });

  const handleSubmit = (values: TaskCreatePayload) => {
    mutation.mutate(values);
  };

  return (
    <Modal
      open={open}
      onCancel={onClose}
      title="新建任务"
      footer={null}
      destroyOnClose
      width={560}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          target_count: 1000,
          batch_size: 10,
          max_workers: 5,
          max_per_file: 10000,
        }}
      >
        <Form.Item
          name="category_id"
          label="分类"
          rules={[{ required: true, message: '请选择分类' }]}
        >
          <Select
            placeholder="选择分类"
            options={categories?.map((c) => ({
              value: c.id,
              label: `[${c.sample_type}] ${c.name}`,
            }))}
            showSearch
            filterOption={(input, option) =>
              (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
            }
          />
        </Form.Item>

        <Form.Item
          name="api_config_id"
          label="API 配置"
          rules={[{ required: true, message: '请选择 API 配置' }]}
        >
          <Select
            placeholder="选择 API 配置"
            options={configs?.map((c) => ({
              value: c.id,
              label: `${c.name} (${c.model_name})`,
            }))}
          />
        </Form.Item>

        <Form.Item
          name="target_count"
          label="目标数量"
          rules={[{ required: true }]}
        >
          <InputNumber min={1} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item
          name="batch_size"
          label="批次大小"
          rules={[{ required: true }]}
        >
          <InputNumber min={1} max={100} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item
          name="max_workers"
          label="并发数"
          rules={[{ required: true }]}
        >
          <InputNumber min={1} max={50} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item
          name="max_per_file"
          label="每文件最大条数"
          rules={[{ required: true }]}
        >
          <InputNumber min={1} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={mutation.isPending}>
              创建
            </Button>
            <Button onClick={onClose}>取消</Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  );
}
```

- [ ] **Step 2: 验证**

启动后端 + 前端 dev server：

```bash
# 终端 1
cd /Users/lanhezheng/llm-data-service/backend
.venv/bin/uvicorn service.main:app --reload

# 终端 2
cd /Users/lanhezheng/llm-data-service/frontend
npm run dev
```

确保后端已有种子数据（分类和 API 配置）。如果没有：
```bash
cd /Users/lanhezheng/llm-data-service/backend
.venv/bin/python -m scripts.seed_from_legacy
```

浏览器访问 http://localhost:5173/ → 点击"新建任务" → 弹窗应显示分类和 API 配置下拉 → 填写表单 → 提交 → 应能看到成功提示，列表刷新。

- [ ] **Step 3: Commit**

```bash
cd /Users/lanhezheng/llm-data-service
git add frontend/src/components/TaskCreateModal.tsx
git commit -m "feat(frontend): TaskCreateModal with category + config selects"
```

---

## Task 9: TaskDetailPage + 进度 + 事件时间线

**Files:**
- Create: `frontend/src/pages/TaskDetailPage.tsx`
- Create: `frontend/src/components/TaskProgress.tsx`
- Create: `frontend/src/components/TaskEventTimeline.tsx`
- Create: `frontend/src/components/TaskDetail.tsx`

- [ ] **Step 1: 写 TaskProgress.tsx**

创建 `frontend/src/components/TaskProgress.tsx`：

```tsx
import { Progress } from 'antd';
import type { TaskOut } from '../api/types';

export function TaskProgress({ task }: { task: TaskOut }) {
  const percent = task.progress_total > 0
    ? Math.round((task.progress_current / task.progress_total) * 100)
    : 0;

  const statusMap: Record<string, 'success' | 'exception' | 'normal' | 'active'> = {
    pending: 'normal',
    running: 'active',
    succeeded: 'success',
    failed: 'exception',
    aborted: 'exception',
  };

  return (
    <div>
      <Progress
        percent={percent}
        status={statusMap[task.status] || 'normal'}
        format={() => `${task.progress_current} / ${task.progress_total}`}
      />
      <div style={{ color: '#888', fontSize: 12 }}>
        状态: {task.status} | 创建: {task.created_at}
        {task.started_at && ` | 开始: ${task.started_at}`}
        {task.finished_at && ` | 完成: ${task.finished_at}`}
      </div>
      {task.error_msg && (
        <div style={{ color: '#cf1322', marginTop: 8, whiteSpace: 'pre-wrap' }}>
          {task.error_msg}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: 写 TaskEventTimeline.tsx**

创建 `frontend/src/components/TaskEventTimeline.tsx`：

```tsx
import { Timeline, Tag } from 'antd';
import type { TaskEventOut } from '../api/types';

const TYPE_COLORS: Record<string, string> = {
  info: 'blue',
  progress: 'green',
  error: 'red',
  aborted: 'orange',
  completed: 'purple',
};

export function TaskEventTimeline({ events }: { events: TaskEventOut[] }) {
  if (events.length === 0) {
    return <div style={{ color: '#888' }}>暂无事件</div>;
  }

  return (
    <Timeline
      items={events.map((e) => ({
        children: (
          <div>
            <Tag color={TYPE_COLORS[e.type] || 'default'} size="small">
              {e.type}
            </Tag>
            <span style={{ marginLeft: 8, color: '#888', fontSize: 12 }}>
              {e.ts}
            </span>
            <div style={{ marginTop: 4 }}>{e.message}</div>
          </div>
        ),
      }))}
    />
  );
}
```

- [ ] **Step 3: 写 TaskDetail.tsx（子组件容器）**

创建 `frontend/src/components/TaskDetail.tsx`：

```tsx
import { Card, Button, Space, Popconfirm } from 'antd';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { abortTask, deleteTask, downloadTask } from '../api/tasks';
import type { TaskDetail as TaskDetailType } from '../api/types';
import { TaskProgress } from './TaskProgress';
import { TaskEventTimeline } from './TaskEventTimeline';
import { SSEStatusBadge } from './SSEStatusBadge';
import { useLocation } from 'wouter';

interface Props {
  task: TaskDetailType;
}

export function TaskDetail({ task }: Props) {
  const [, navigate] = useLocation();
  const queryClient = useQueryClient();

  const abortMutation = useMutation({
    mutationFn: () => abortTask(task.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['task', task.id] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteTask(task.id),
    onSuccess: () => {
      navigate('/');
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  const isTerminal = ['succeeded', 'failed', 'aborted'].includes(task.status);

  return (
    <div>
      <Card
        title={
          <Space>
            <span>任务 #{task.id} - {task.category_name}</span>
            <SSEStatusBadge taskId={task.id} />
          </Space>
        }
        extra={
          <Space>
            {!isTerminal && (
              <Popconfirm
                title="确认中止任务？"
                onConfirm={() => abortMutation.mutate()}
              >
                <Button danger loading={abortMutation.isPending}>
                  中止
                </Button>
              </Popconfirm>
            )}
            {isTerminal && (
              <Button onClick={() => downloadTask(task.id)}>
                下载结果
              </Button>
            )}
            <Popconfirm
              title="确认删除任务？"
              description="删除后不可恢复"
              onConfirm={() => deleteMutation.mutate()}
            >
              <Button danger>删除</Button>
            </Popconfirm>
          </Space>
        }
      >
        <TaskProgress task={task} />
      </Card>

      <Card title="事件记录" style={{ marginTop: 16 }}>
        <TaskEventTimeline events={task.recent_events} />
      </Card>
    </div>
  );
}
```

- [ ] **Step 4: 写 TaskDetailPage.tsx**

创建 `frontend/src/pages/TaskDetailPage.tsx`：

```tsx
import { useQuery } from '@tanstack/react-query';
import { useParams } from 'wouter';
import { getTask } from '../api/tasks';
import { useTaskStream } from '../hooks/useTaskStream';
import { TaskDetail } from '../components/TaskDetail';
import { Spin } from 'antd';

export function TaskDetailPage() {
  const params = useParams<{ id: string }>();
  const taskId = parseInt(params.id, 10);

  const { data: task, isLoading, error } = useQuery({
    queryKey: ['task', taskId],
    queryFn: () => getTask(taskId),
    enabled: !isNaN(taskId),
  });

  useTaskStream(!isNaN(taskId) ? taskId : undefined);

  if (isNaN(taskId)) {
    return <div>无效的任务 ID</div>;
  }

  if (isLoading) {
    return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  }

  if (error) {
    return <div style={{ color: 'red' }}>加载失败: {error.message}</div>;
  }

  if (!task) {
    return <div>任务不存在</div>;
  }

  return <TaskDetail task={task} />;
}
```

- [ ] **Step 5: 验证**

启动后端 + 前端 dev server，浏览器访问 http://localhost:5173/ → 点击某个任务行 → 应跳转到详情页 → 显示：
- 任务标题 + SSE 状态 badge
- 进度条
- 事件时间线
- 中止/下载/删除按钮

如果有运行中的任务，SSE badge 应显示"已连接"，进度条应随 SSE 事件实时更新。

- [ ] **Step 6: Commit**

```bash
cd /Users/lanhezheng/llm-data-service
git add frontend/src/pages/TaskDetailPage.tsx frontend/src/components/TaskProgress.tsx frontend/src/components/TaskEventTimeline.tsx frontend/src/components/TaskDetail.tsx
git commit -m "feat(frontend): TaskDetailPage with progress, events, abort, download"
```

---

## Task 10: Preview + LogViewer + 完整 E2E

**Files:**
- Create: `frontend/src/components/TaskPreview.tsx`
- Create: `frontend/src/components/TaskLogViewer.tsx`
- Modify: `frontend/src/components/TaskDetail.tsx`

- [ ] **Step 1: 写 TaskPreview.tsx**

创建 `frontend/src/components/TaskPreview.tsx`：

```tsx
import { useQuery } from '@tanstack/react-query';
import { Table, Spin } from 'antd';
import { previewTask } from '../api/tasks';

export function TaskPreview({ taskId }: { taskId: number }) {
  const { data, isLoading } = useQuery({
    queryKey: ['preview', taskId],
    queryFn: () => previewTask(taskId),
  });

  if (isLoading) return <Spin />;
  if (!data || data.rows.length === 0) {
    return <div style={{ color: '#888' }}>暂无预览数据</div>;
  }

  const columns = data.header.map((h, i) => ({
    title: h,
    dataIndex: i,
    key: i,
    ellipsis: true,
  }));

  const dataSource = data.rows.map((row, idx) => ({
    key: idx,
    ...row.reduce((acc, val, i) => ({ ...acc, [i]: val }), {}),
  }));

  return (
    <Table
      columns={columns}
      dataSource={dataSource}
      size="small"
      pagination={{ pageSize: 10 }}
      scroll={{ x: 'max-content' }}
    />
  );
}
```

- [ ] **Step 2: 写 TaskLogViewer.tsx**

创建 `frontend/src/components/TaskLogViewer.tsx`：

```tsx
import { useQuery } from '@tanstack/react-query';
import { Spin, Empty } from 'antd';
import { getTaskLog } from '../api/tasks';

export function TaskLogViewer({ taskId }: { taskId: number }) {
  const { data, isLoading } = useQuery({
    queryKey: ['log', taskId],
    queryFn: () => getTaskLog(taskId, 200),
  });

  if (isLoading) return <Spin />;
  if (!data || data.lines.length === 0) {
    return <Empty description="暂无日志" />;
  }

  return (
    <pre
      style={{
        background: '#1e1e1e',
        color: '#d4d4d4',
        padding: 12,
        borderRadius: 4,
        fontSize: 12,
        maxHeight: 400,
        overflow: 'auto',
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-all',
      }}
    >
      {data.lines.join('')}
    </pre>
  );
}
```

- [ ] **Step 3: 修改 TaskDetail.tsx 加入 Preview 和 Log**

修改 `frontend/src/components/TaskDetail.tsx`，在文件顶部添加 import：

```tsx
import { TaskPreview } from './TaskPreview';
import { TaskLogViewer } from './TaskLogViewer';
```

在 JSX 末尾（`</div>` 之前）添加两个 Card：

```tsx
      <Card title="数据预览" style={{ marginTop: 16 }}>
        <TaskPreview taskId={task.id} />
      </Card>

      <Card title="运行日志" style={{ marginTop: 16 }}>
        <TaskLogViewer taskId={task.id} />
      </Card>
```

完整修改后的 `TaskDetail.tsx`：

```tsx
import { Card, Button, Space, Popconfirm } from 'antd';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { abortTask, deleteTask, downloadTask } from '../api/tasks';
import type { TaskDetail as TaskDetailType } from '../api/types';
import { TaskProgress } from './TaskProgress';
import { TaskEventTimeline } from './TaskEventTimeline';
import { TaskPreview } from './TaskPreview';
import { TaskLogViewer } from './TaskLogViewer';
import { SSEStatusBadge } from './SSEStatusBadge';
import { useLocation } from 'wouter';

interface Props {
  task: TaskDetailType;
}

export function TaskDetail({ task }: Props) {
  const [, navigate] = useLocation();
  const queryClient = useQueryClient();

  const abortMutation = useMutation({
    mutationFn: () => abortTask(task.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['task', task.id] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteTask(task.id),
    onSuccess: () => {
      navigate('/');
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  const isTerminal = ['succeeded', 'failed', 'aborted'].includes(task.status);

  return (
    <div>
      <Card
        title={
          <Space>
            <span>任务 #{task.id} - {task.category_name}</span>
            <SSEStatusBadge taskId={task.id} />
          </Space>
        }
        extra={
          <Space>
            {!isTerminal && (
              <Popconfirm
                title="确认中止任务？"
                onConfirm={() => abortMutation.mutate()}
              >
                <Button danger loading={abortMutation.isPending}>
                  中止
                </Button>
              </Popconfirm>
            )}
            {isTerminal && (
              <Button onClick={() => downloadTask(task.id)}>
                下载结果
              </Button>
            )}
            <Popconfirm
              title="确认删除任务？"
              description="删除后不可恢复"
              onConfirm={() => deleteMutation.mutate()}
            >
              <Button danger>删除</Button>
            </Popconfirm>
          </Space>
        }
      >
        <TaskProgress task={task} />
      </Card>

      <Card title="事件记录" style={{ marginTop: 16 }}>
        <TaskEventTimeline events={task.recent_events} />
      </Card>

      <Card title="数据预览" style={{ marginTop: 16 }}>
        <TaskPreview taskId={task.id} />
      </Card>

      <Card title="运行日志" style={{ marginTop: 16 }}>
        <TaskLogViewer taskId={task.id} />
      </Card>
    </div>
  );
}
```

- [ ] **Step 4: 完整 E2E 验证**

启动后端 + 前端：

```bash
# 终端 1
cd /Users/lanhezheng/llm-data-service/backend
.venv/bin/uvicorn service.main:app --reload

# 终端 2
cd /Users/lanhezheng/llm-data-service/frontend
npm run dev
```

走完整流程验证：
1. 访问 http://localhost:5173/ → 任务列表页正常显示
2. 点击"新建任务" → 选择分类和 API 配置 → 填写参数 → 创建
3. 列表自动刷新 → 点击新任务 → 跳转到详情页
4. 详情页显示进度条（running 状态）
5. SSE badge 显示"已连接"
6. 事件时间线显示事件
7. 等待任务完成（或手动 abort）
8. 完成后：下载按钮出现，点击下载 CSV
9. 数据预览显示 CSV 内容
10. 运行日志显示 worker 日志
11. 删除任务 → 返回列表页

- [ ] **Step 5: Commit**

```bash
cd /Users/lanhezheng/llm-data-service
git add frontend/src/components/TaskPreview.tsx frontend/src/components/TaskLogViewer.tsx frontend/src/components/TaskDetail.tsx
git commit -m "feat(frontend): preview, log viewer, and full task detail"
```

---

## Task 11: 生产构建 + 后端集成验证

**Files:**
- Create: `frontend/.env.production`
- Modify: `frontend/vite.config.ts`（如需调整 base）

- [ ] **Step 1: 创建生产环境配置**

创建 `frontend/.env.production`：

```
# 生产环境 API 同源，无需代理
VITE_API_BASE=
```

- [ ] **Step 2: 确保 client.ts 支持 VITE_API_BASE**

修改 `frontend/src/api/client.ts`，将 BASE 改为：

```typescript
const BASE = import.meta.env.VITE_API_BASE || '';
```

- [ ] **Step 3: 生产构建**

```bash
cd /Users/lanhezheng/llm-data-service/frontend
npm run build
```

期望：`frontend/dist/` 目录生成，包含 `index.html` 和静态资源。

- [ ] **Step 4: 验证 FastAPI 托管**

```bash
cd /Users/lanhezheng/llm-data-service/backend
STATIC_DIR=/Users/lanhezheng/llm-data-service/frontend/dist .venv/bin/uvicorn service.main:app --reload
```

浏览器访问 http://localhost:8000/ → 应能看到前端页面（非后端 JSON）。

访问 http://localhost:8000/api/tasks → 应返回任务列表 JSON。

- [ ] **Step 5: Commit**

```bash
cd /Users/lanhezheng/llm-data-service
git add frontend/.env.production frontend/src/api/client.ts
git commit -m "feat(frontend): production build + FastAPI static mount verification"
```

---

## 自检

### Spec 覆盖检查

| Spec 要求 | 对应 Task |
|---|---|
| Vite + React + TS + Ant Design 脚手架 | Task 1 |
| TanStack Query 管理服务端数据 | Task 6 (QueryClientProvider), Task 8-10 (useQuery/useMutation) |
| Zustand 管理 UI 状态 | Task 4 (toast + SSE state) |
| wouter 轻量路由 | Task 6 (App.tsx) |
| API 类型从 schemas.py 映射 | Task 2 (types.ts) |
| fetch 客户端统一错误处理 | Task 2 (client.ts) |
| 任务列表 + 筛选 + 简单分页 | Task 7 (HomePage + TaskList) |
| 创建任务弹窗（下拉选择配置） | Task 8 (TaskCreateModal) |
| SSE 命名事件 (addEventListener) | Task 5 (useTaskStream) |
| 浏览器原生重连 + 轮询兜底 | Task 5 (useTaskStream + useTaskPolling) |
| 任务详情（进度/事件/日志/预览） | Task 9-10 |
| Abort + Download + Delete | Task 9-10 |
| Toast 通知 | Task 4 + Task 6 (ToastContainer) |
| 生产构建 + FastAPI 托管 | Task 11 |

### Placeholder 扫描

- 无 "TBD" / "TODO" / "implement later"
- 无 "add appropriate error handling" 等模糊描述
- 所有代码块包含完整实现
- 所有命令包含完整路径和期望输出

### 类型一致性

- `TaskOut`, `TaskDetail`, `TaskEventOut` 等类型在 `types.ts` (Task 2) 定义，被所有后续 task 引用
- `TaskCreatePayload` 在 Task 2 定义，Task 8 使用
- `ApiConfigOut`, `CategoryOut` 在 Task 2 定义，Task 8 使用
- `SseState` 在 Task 4 定义，Task 5 使用

全部一致，无漂移。
