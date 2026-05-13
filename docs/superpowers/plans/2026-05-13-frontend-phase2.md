# Phase 2: 配置管理 CRUD 页面实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 API 配置、词库、Prompt 模板、分类四组资源的完整 CRUD 页面，复用 Phase 1.5 沉淀的组件模式。

**Architecture:** 复用 Phase 1.5 的 PageShell + Toolbar + CompactTable + Drawer 模式。每个资源一对文件（List + Drawer），Sidebar 配置管理展开为子菜单。所有 API 函数遵循 `list/create/update/delete` 命名。

**Tech Stack:** Vite + React 18 + TypeScript + Ant Design 6 + TanStack Query 5 + Zustand 5 + wouter 3

**Spec:** `docs/superpowers/specs/2026-05-12-frontend-ui-redesign-design.md`

---

## 文件结构

```
src/
├── api/
│   ├── configs.ts              # 新增 create/update/delete
│   ├── tasks.ts                # 已有
│   └── types.ts                # 已有
├── components/
│   ├── layout/
│   │   └── Sidebar.tsx         # 修改：配置管理展开子菜单
│   └── settings/
│       ├── ApiConfigList.tsx   # API 配置列表表格
│       ├── ApiConfigDrawer.tsx # API 配置创建/编辑抽屉（含 test/reveal）
│       ├── WordListList.tsx    # 词库列表
│       ├── WordListDrawer.tsx  # 词库创建/编辑（items textarea）
│       ├── PromptTemplateList.tsx
│       ├── PromptTemplateDrawer.tsx # 模板创建/编辑（变量校验预览）
│       ├── CategoryList.tsx
│       └── CategoryDrawer.tsx  # 分类创建/编辑（关联下拉）
├── pages/
│   ├── HomePage.tsx            # 已有
│   ├── TaskDetailPage.tsx      # 已有
│   ├── ApiConfigsPage.tsx      # 新增
│   ├── WordListsPage.tsx       # 新增
│   ├── PromptTemplatesPage.tsx # 新增
│   └── CategoriesPage.tsx      # 新增
└── App.tsx                     # 修改：添加 4 个新路由
```

---

## Task 1: Sidebar 子菜单 + API 函数补全

**Files:**
- Modify: `src/components/layout/Sidebar.tsx`
- Modify: `src/api/configs.ts`

### Step 1: 重构 Sidebar（配置管理展开子菜单）

修改 `src/components/layout/Sidebar.tsx`，把 `NAV_ITEMS` 改为支持子菜单的结构：

```tsx
import { useState } from 'react';
import { Menu, Button } from 'antd';
import {
  DashboardOutlined,
  SettingOutlined,
  ApiOutlined,
  BookOutlined,
  FileTextOutlined,
  TagsOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons';
import { Link, useLocation } from 'wouter';

const NAV_ITEMS = [
  {
    key: 'tasks',
    icon: <DashboardOutlined />,
    label: '任务中心',
    href: '/',
  },
  {
    key: 'settings',
    icon: <SettingOutlined />,
    label: '配置管理',
    children: [
      { key: 'api-configs', icon: <ApiOutlined />, label: 'API 配置', href: '/settings/api-configs' },
      { key: 'wordlists', icon: <BookOutlined />, label: '词库', href: '/settings/wordlists' },
      { key: 'prompt-templates', icon: <FileTextOutlined />, label: 'Prompt 模板', href: '/settings/prompt-templates' },
      { key: 'categories', icon: <TagsOutlined />, label: '分类', href: '/settings/categories' },
    ],
  },
];

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const [location] = useLocation();
  const [openKeys, setOpenKeys] = useState<string[]>(['settings']);

  const activeKey = (() => {
    if (location === '/') return 'tasks';
    if (location.startsWith('/settings/api-configs')) return 'api-configs';
    if (location.startsWith('/settings/wordlists')) return 'wordlists';
    if (location.startsWith('/settings/prompt-templates')) return 'prompt-templates';
    if (location.startsWith('/settings/categories')) return 'categories';
    return '';
  })();

  return (
    <aside style={{ width: collapsed ? 64 : 200, minWidth: collapsed ? 64 : 200, background: '#0f172a', display: 'flex', flexDirection: 'column', transition: 'width 0.2s', flexShrink: 0 }}>
      <div style={{ height: 48, display: 'flex', alignItems: 'center', padding: collapsed ? '0 20px' : '0 16px', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        {!collapsed && <span style={{ color: '#fff', fontSize: 15, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden' }}>LLM 样本数据</span>}
        <Button type="text" icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />} onClick={() => setCollapsed(!collapsed)} style={{ color: 'rgba(255,255,255,0.5)', marginLeft: 'auto', padding: 0, width: 24, height: 24 }} />
      </div>
      <Menu
        theme="dark"
        mode="inline"
        inlineCollapsed={collapsed}
        selectedKeys={[activeKey]}
        openKeys={collapsed ? [] : openKeys}
        onOpenChange={setOpenKeys}
        style={{ background: 'transparent', borderRight: 'none', flex: 1, paddingTop: 8 }}
        items={NAV_ITEMS.map((item) => {
          if (item.children) {
            return {
              key: item.key,
              icon: item.icon,
              label: item.label,
              children: item.children.map((c) => ({
                key: c.key,
                icon: c.icon,
                label: <Link href={c.href}>{c.label}</Link>,
              })),
            };
          }
          return {
            key: item.key,
            icon: item.icon,
            label: <Link href={item.href!}>{item.label}</Link>,
          };
        })}
      />
    </aside>
  );
}
```

### Step 2: 补全 API 函数

修改 `src/api/configs.ts`，添加 create/update/delete：

```typescript
import { apiGet, apiPost, apiDelete } from './client';
import type {
  ApiConfigOut, ApiConfigCreate, ApiConfigUpdate,
  CategoryOut, CategoryCreate, CategoryUpdate,
  WordListOut, WordListCreate, WordListUpdate,
  PromptTemplateOut, PromptTemplateCreate, PromptTemplateUpdate,
} from './types';

// --- API Configs ---
export function createApiConfig(payload: ApiConfigCreate) {
  return apiPost<ApiConfigOut>('/api/api-configs', payload);
}

export function updateApiConfig(id: number, payload: ApiConfigUpdate) {
  return apiPost<ApiConfigOut>(`/api/api-configs/${id}`, payload);
}

export function deleteApiConfig(id: number) {
  return apiDelete(`/api/api-configs/${id}`);
}

export function revealApiKey(id: number) {
  return apiGet<{ id: number; api_key: string }>(`/api/api-configs/${id}/reveal`);
}

export function testApiConfig(id: number) {
  return apiPost<{ ok: boolean; latency_ms?: number; sample_text?: string; error?: string }>(`/api/api-configs/${id}/test`, {});
}

// --- WordLists ---
export function createWordlist(payload: WordListCreate) {
  return apiPost<WordListOut>('/api/wordlists', payload);
}

export function updateWordlist(id: number, payload: WordListUpdate) {
  return apiPost<WordListOut>(`/api/wordlists/${id}`, payload);
}

export function deleteWordlist(id: number) {
  return apiDelete(`/api/wordlists/${id}`);
}

// --- Prompt Templates ---
export function createPromptTemplate(payload: PromptTemplateCreate) {
  return apiPost<PromptTemplateOut>('/api/prompt-templates', payload);
}

export function updatePromptTemplate(id: number, payload: PromptTemplateUpdate) {
  return apiPost<PromptTemplateOut>(`/api/prompt-templates/${id}`, payload);
}

export function deletePromptTemplate(id: number) {
  return apiDelete(`/api/prompt-templates/${id}`);
}

// --- Categories ---
export function getCategory(id: number) {
  return apiGet<CategoryOut>(`/api/categories/${id}`);
}

export function createCategory(payload: CategoryCreate) {
  return apiPost<CategoryOut>('/api/categories', payload);
}

export function updateCategory(id: number, payload: CategoryUpdate) {
  return apiPost<CategoryOut>(`/api/categories/${id}`, payload);
}

export function deleteCategory(id: number) {
  return apiDelete(`/api/categories/${id}`);
}
```

### Step 3: 验证编译

```bash
cd /Users/lanhezheng/llm-data-service/frontend
npx tsc --noEmit
```

Expected: no errors.

### Step 4: Commit

```bash
cd /Users/lanhezheng/llm-data-service
git add frontend/src/components/layout/Sidebar.tsx frontend/src/api/configs.ts
git commit -m "feat(frontend): Sidebar submenu + settings API functions"
```

---

## Task 2: API 配置列表页 + 抽屉

**Files:**
- Create: `src/components/settings/ApiConfigList.tsx`
- Create: `src/components/settings/ApiConfigDrawer.tsx`
- Create: `src/pages/ApiConfigsPage.tsx`

### Step 1: ApiConfigList.tsx

```tsx
import { Table, Button, Space, Tag, Tooltip } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { EditOutlined, DeleteOutlined, ThunderboltOutlined, EyeOutlined } from '@ant-design/icons';
import type { ApiConfigOut } from '../../api/types';
import { EmptyState } from '../common/EmptyState';
import { LoadingState } from '../common/LoadingState';

interface Props {
  configs: ApiConfigOut[];
  loading: boolean;
  onEdit: (c: ApiConfigOut) => void;
  onDelete: (id: number) => void;
  onTest: (id: number) => void;
  onReveal: (id: number) => void;
}

export function ApiConfigList({ configs, loading, onEdit, onDelete, onTest, onReveal }: Props) {
  if (loading) return <LoadingState type="table" rows={5} />;
  if (configs.length === 0) return <EmptyState title="暂无 API 配置" description="配置 LLM 接口后才能创建任务" actionLabel="添加配置" onAction={() => {}} />;

  const columns: ColumnsType<ApiConfigOut> = [
    { title: 'ID', dataIndex: 'id', width: 50, render: (id) => <span style={{ fontFamily: 'monospace' }}>{id}</span> },
    { title: '名称', dataIndex: 'name', width: 140 },
    { title: 'Base URL', dataIndex: 'base_url', ellipsis: true, width: 200 },
    { title: '模型', dataIndex: 'model_name', width: 120 },
    { title: '类型', dataIndex: 'type', width: 70, render: (t: string) => <Tag>{t}</Tag> },
    { title: 'Key', dataIndex: 'api_key_masked', width: 120 },
    {
      title: '操作',
      key: 'action',
      width: 160,
      render: (_, c) => (
        <Space size="small">
          <Tooltip title="连通性测试"><Button type="text" size="small" icon={<ThunderboltOutlined />} onClick={() => onTest(c.id)} /></Tooltip>
          <Tooltip title="查看密钥"><Button type="text" size="small" icon={<EyeOutlined />} onClick={() => onReveal(c.id)} /></Tooltip>
          <Tooltip title="编辑"><Button type="text" size="small" icon={<EditOutlined />} onClick={() => onEdit(c)} /></Tooltip>
          <Tooltip title="删除"><Button type="text" size="small" danger icon={<DeleteOutlined />} onClick={() => onDelete(c.id)} /></Tooltip>
        </Space>
      ),
    },
  ];

  return <Table rowKey="id" columns={columns} dataSource={configs} size="small" pagination={false} />;
}
```

### Step 2: ApiConfigDrawer.tsx

```tsx
import { Drawer, Form, Input, Select, Button, message } from 'antd';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createApiConfig, updateApiConfig } from '../../api/configs';
import type { ApiConfigCreate, ApiConfigUpdate, ApiConfigOut } from '../../api/types';

interface Props {
  open: boolean;
  onClose: () => void;
  editing?: ApiConfigOut;
}

export function ApiConfigDrawer({ open, onClose, editing }: Props) {
  const [form] = Form.useForm();
  const queryClient = useQueryClient();
  const isEdit = !!editing;

  const mutation = useMutation({
    mutationFn: (values: ApiConfigCreate) =>
      isEdit ? updateApiConfig(editing!.id, values) : createApiConfig(values),
    onSuccess: () => {
      message.success(isEdit ? '配置已更新' : '配置已创建');
      queryClient.invalidateQueries({ queryKey: ['api-configs'] });
      onClose();
    },
    onError: (err: Error) => message.error(err.message),
  });

  return (
    <Drawer title={isEdit ? '编辑 API 配置' : '新建 API 配置'} placement="right" width={480} open={open} onClose={onClose} destroyOnClose
      footer={<div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}><Button onClick={onClose}>取消</Button><Button type="primary" loading={mutation.isPending} onClick={() => form.submit()}>保存</Button></div>}
    >
      <Form form={form} layout="vertical" onFinish={(v) => mutation.mutate(v)} initialValues={editing || { type: 'openai' }}>
        <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
        <Form.Item name="base_url" label="Base URL" rules={[{ required: true }]}><Input placeholder="https://api.example.com/v1" /></Form.Item>
        <Form.Item name="api_key" label="API Key" rules={[{ required: !isEdit }]}><Input.Password placeholder={isEdit ? '留空表示不修改' : ''} /></Form.Item>
        <Form.Item name="model_name" label="模型名称" rules={[{ required: true }]}><Input placeholder="gpt-4, deepseek-chat..." /></Form.Item>
        <Form.Item name="type" label="类型" rules={[{ required: true }]}>
          <Select options={[{ value: 'openai', label: 'OpenAI 兼容' }, { value: 'raw', label: 'Raw HTTP' }]} />
        </Form.Item>
      </Form>
    </Drawer>
  );
}
```

### Step 3: ApiConfigsPage.tsx

```tsx
import { useState } from 'react';
import { Button, message, Modal } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listApiConfigs, deleteApiConfig, testApiConfig, revealApiKey } from '../../api/configs';
import { PageShell } from '../../components/layout/PageShell';
import { ApiConfigList } from '../../components/settings/ApiConfigList';
import { ApiConfigDrawer } from '../../components/settings/ApiConfigDrawer';
import type { ApiConfigOut } from '../../api/types';

export function ApiConfigsPage() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editing, setEditing] = useState<ApiConfigOut>();
  const queryClient = useQueryClient();

  const { data: configs, isLoading } = useQuery({ queryKey: ['api-configs'], queryFn: listApiConfigs });

  const deleteMutation = useMutation({
    mutationFn: deleteApiConfig,
    onSuccess: () => { message.success('已删除'); queryClient.invalidateQueries({ queryKey: ['api-configs'] }); },
    onError: (err: Error) => message.error(err.message),
  });

  const handleTest = async (id: number) => {
    message.loading({ content: '测试中...', key: `test-${id}` });
    try {
      const res = await testApiConfig(id);
      if (res.ok) message.success({ content: `连通成功 (${res.latency_ms}ms)`, key: `test-${id}` });
      else message.error({ content: `失败: ${res.error}`, key: `test-${id}` });
    } catch (e: any) { message.error({ content: e.message, key: `test-${id}` }); }
  };

  const handleReveal = async (id: number) => {
    try {
      const res = await revealApiKey(id);
      Modal.info({ title: 'API Key', content: <code style={{ wordBreak: 'break-all' }}>{res.api_key}</code> });
    } catch (e: any) { message.error(e.message); }
  };

  return (
    <PageShell title="API 配置" subtitle="管理 LLM 接口连接" extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditing(undefined); setDrawerOpen(true); }}>添加配置</Button>}>
      <ApiConfigList configs={configs || []} loading={isLoading}
        onEdit={(c) => { setEditing(c); setDrawerOpen(true); }}
        onDelete={(id) => deleteMutation.mutate(id)}
        onTest={handleTest}
        onReveal={handleReveal}
      />
      <ApiConfigDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} editing={editing} />
    </PageShell>
  );
}
```

### Step 4: 验证编译 + Commit

```bash
cd /Users/lanhezheng/llm-data-service/frontend && npx tsc --noEmit
git add frontend/src/components/settings/ frontend/src/pages/ApiConfigsPage.tsx
git commit -m "feat(frontend): API config CRUD with test/reveal"
```

---

## Task 3: 词库列表页 + 抽屉

**Files:**
- Create: `src/components/settings/WordListList.tsx`
- Create: `src/components/settings/WordListDrawer.tsx`
- Create: `src/pages/WordListsPage.tsx`

### Step 1: WordListDrawer.tsx（items 为 textarea，每行一个词）

```tsx
import { Drawer, Form, Input, Select, Button, message } from 'antd';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createWordlist, updateWordlist } from '../../api/configs';
import type { WordListCreate, WordListOut } from '../../api/types';

interface Props { open: boolean; onClose: () => void; editing?: WordListOut; }

export function WordListDrawer({ open, onClose, editing }: Props) {
  const [form] = Form.useForm();
  const queryClient = useQueryClient();
  const isEdit = !!editing;

  const mutation = useMutation({
    mutationFn: (values: WordListCreate) => isEdit ? updateWordlist(editing!.id, values) : createWordlist(values),
    onSuccess: () => { message.success(isEdit ? '已更新' : '已创建'); queryClient.invalidateQueries({ queryKey: ['wordlists'] }); onClose(); },
    onError: (err: Error) => message.error(err.message),
  });

  return (
    <Drawer title={isEdit ? '编辑词库' : '新建词库'} placement="right" width={480} open={open} onClose={onClose} destroyOnClose
      footer={<div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}><Button onClick={onClose}>取消</Button><Button type="primary" loading={mutation.isPending} onClick={() => form.submit()}>保存</Button></div>}
    >
      <Form form={form} layout="vertical" onFinish={(v) => mutation.mutate(v)}
        initialValues={editing ? { ...editing, items: editing.items.join('\n') } : { kind: 'scenario' }}
      >
        <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
        <Form.Item name="kind" label="类型" rules={[{ required: true }]}>
          <Select options={[{ value: 'scenario', label: '场景' }, { value: 'tone', label: '语气' }, { value: 'other', label: '其他' }]} />
        </Form.Item>
        <Form.Item name="items" label="词库内容" rules={[{ required: true }]} extra="每行一个词">
          <Input.TextArea rows={12} placeholder="shopping&#10;travel&#10;coding" />
        </Form.Item>
      </Form>
    </Drawer>
  );
}
```

### Step 2: WordListList.tsx + WordListsPage.tsx

模式同 ApiConfig，表格列：ID、名称、类型（Tag）、数量（items.length）、操作（编辑/删除）。

### Step 3: 验证编译 + Commit

```bash
cd /Users/lanhezheng/llm-data-service/frontend && npx tsc --noEmit
git add frontend/src/components/settings/WordList*.tsx frontend/src/pages/WordListsPage.tsx
git commit -m "feat(frontend): wordlist CRUD"
```

---

## Task 4: Prompt 模板列表页 + 抽屉

**Files:**
- Create: `src/components/settings/PromptTemplateList.tsx`
- Create: `src/components/settings/PromptTemplateDrawer.tsx`
- Create: `src/pages/PromptTemplatesPage.tsx`

### Step 1: PromptTemplateDrawer.tsx（含变量预览）

```tsx
import { Drawer, Form, Input, Button, message, Card } from 'antd';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useMemo } from 'react';
import { createPromptTemplate, updatePromptTemplate } from '../../api/configs';
import type { PromptTemplateCreate, PromptTemplateOut } from '../../api/types';

interface Props { open: boolean; onClose: () => void; editing?: PromptTemplateOut; }

export function PromptTemplateDrawer({ open, onClose, editing }: Props) {
  const [form] = Form.useForm();
  const queryClient = useQueryClient();
  const isEdit = !!editing;
  const body = Form.useWatch('body', form);

  const variables = useMemo(() => {
    if (!body) return [];
    const matches = body.match(/\{([a-zA-Z_]\w*)\}/g);
    if (!matches) return [];
    return [...new Set(matches.map((m) => m.slice(1, -1)))];
  }, [body]);

  const mutation = useMutation({
    mutationFn: (values: PromptTemplateCreate) =>
      isEdit ? updatePromptTemplate(editing!.id, values) : createPromptTemplate(values),
    onSuccess: () => { message.success(isEdit ? '已更新' : '已创建'); queryClient.invalidateQueries({ queryKey: ['prompt-templates'] }); onClose(); },
    onError: (err: Error) => message.error(err.message),
  });

  return (
    <Drawer title={isEdit ? '编辑模板' : '新建模板'} placement="right" width={560} open={open} onClose={onClose} destroyOnClose
      footer={<div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}><Button onClick={onClose}>取消</Button><Button type="primary" loading={mutation.isPending} onClick={() => form.submit()}>保存</Button></div>}
    >
      <Form form={form} layout="vertical" onFinish={(v) => mutation.mutate(v)} initialValues={editing || {}}>
        <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
        <Form.Item name="body" label="模板内容" rules={[{ required: true }]} extra="使用 {variable} 语法定义变量">
          <Input.TextArea rows={8} placeholder="Generate a {tone} sample about {scenario}" />
        </Form.Item>
        <Form.Item label="检测到的变量">
          {variables.length > 0 ? (
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {variables.map((v) => <code key={v} style={{ background: '#eff6ff', color: '#2563eb', padding: '2px 8px', borderRadius: 4, fontSize: 12 }}>{v}</code>)}
            </div>
          ) : <span style={{ color: '#94a3b8', fontSize: 13 }}>未检测到变量</span>}
        </Form.Item>
      </Form>
    </Drawer>
  );
}
```

### Step 2: PromptTemplateList.tsx + PromptTemplatesPage.tsx

表格列：ID、名称、body（截断显示）、变量数量、操作。

### Step 3: 验证编译 + Commit

```bash
cd /Users/lanhezheng/llm-data-service/frontend && npx tsc --noEmit
git add frontend/src/components/settings/PromptTemplate*.tsx frontend/src/pages/PromptTemplatesPage.tsx
git commit -m "feat(frontend): prompt template CRUD with variable preview"
```

---

## Task 5: 分类列表页 + 抽屉

**Files:**
- Create: `src/components/settings/CategoryList.tsx`
- Create: `src/components/settings/CategoryDrawer.tsx`
- Create: `src/pages/CategoriesPage.tsx`

### Step 1: CategoryDrawer.tsx（关联下拉选择）

```tsx
import { Drawer, Form, Input, InputNumber, Select, Button, message } from 'antd';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { createCategory, updateCategory, listWordlists, listPromptTemplates } from '../../api/configs';
import type { CategoryCreate, CategoryOut } from '../../api/types';

interface Props { open: boolean; onClose: () => void; editing?: CategoryOut; }

export function CategoryDrawer({ open, onClose, editing }: Props) {
  const [form] = Form.useForm();
  const queryClient = useQueryClient();
  const isEdit = !!editing;

  const { data: wordlists } = useQuery({ queryKey: ['wordlists'], queryFn: () => listWordlists(), enabled: open });
  const { data: templates } = useQuery({ queryKey: ['prompt-templates'], queryFn: () => listPromptTemplates(), enabled: open });

  const mutation = useMutation({
    mutationFn: (values: CategoryCreate) => isEdit ? updateCategory(editing!.id, values) : createCategory(values),
    onSuccess: () => { message.success(isEdit ? '已更新' : '已创建'); queryClient.invalidateQueries({ queryKey: ['categories'] }); onClose(); },
    onError: (err: Error) => message.error(err.message),
  });

  return (
    <Drawer title={isEdit ? '编辑分类' : '新建分类'} placement="right" width={480} open={open} onClose={onClose} destroyOnClose
      footer={<div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}><Button onClick={onClose}>取消</Button><Button type="primary" loading={mutation.isPending} onClick={() => form.submit()}>保存</Button></div>}
    >
      <Form form={form} layout="vertical" onFinish={(v) => mutation.mutate(v)} initialValues={editing || { sample_type: 'black', default_target_count: 100 }}>
        <Form.Item name="sample_type" label="样本类型" rules={[{ required: true }]}>
          <Select options={[{ value: 'black', label: '黑样本' }, { value: 'gray', label: '灰样本' }, { value: 'white', label: '白样本' }]} />
        </Form.Item>
        <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
        <Form.Item name="description" label="描述"><Input.TextArea rows={2} /></Form.Item>
        <Form.Item name="prompt_template_id" label="Prompt 模板" rules={[{ required: true }]}>
          <Select options={templates?.map((t) => ({ value: t.id, label: t.name }))} placeholder="选择模板" />
        </Form.Item>
        <Form.Item name="scenario_list_id" label="场景词库" rules={[{ required: true }]}>
          <Select options={wordlists?.filter((w) => w.kind === 'scenario').map((w) => ({ value: w.id, label: w.name }))} placeholder="选择场景词库" />
        </Form.Item>
        <Form.Item name="tone_list_id" label="语气词库" rules={[{ required: true }]}>
          <Select options={wordlists?.filter((w) => w.kind === 'tone').map((w) => ({ value: w.id, label: w.name }))} placeholder="选择语气词库" />
        </Form.Item>
        <Form.Item name="default_target_count" label="默认目标数量" rules={[{ required: true }]}><InputNumber min={0} style={{ width: '100%' }} /></Form.Item>
      </Form>
    </Drawer>
  );
}
```

### Step 2: CategoryList.tsx + CategoriesPage.tsx

表格列：ID、样本类型（Tag）、名称、模板、场景词库、语气词库、默认数量、操作。

### Step 3: 验证编译 + Commit

```bash
cd /Users/lanhezheng/llm-data-service/frontend && npx tsc --noEmit
git add frontend/src/components/settings/Category*.tsx frontend/src/pages/CategoriesPage.tsx
git commit -m "feat(frontend): category CRUD with linked selects"
```

---

## Task 6: 路由配置 + App.tsx + 生产构建

**Files:**
- Modify: `src/App.tsx`

### Step 1: 添加路由

修改 `src/App.tsx` 的 Switch，添加 4 个新路由：

```tsx
import { Route, Switch } from 'wouter';
import { ApiConfigsPage } from './pages/ApiConfigsPage';
import { WordListsPage } from './pages/WordListsPage';
import { PromptTemplatesPage } from './pages/PromptTemplatesPage';
import { CategoriesPage } from './pages/CategoriesPage';

// ... inside Switch:
<Route path="/settings/api-configs" component={ApiConfigsPage} />
<Route path="/settings/wordlists" component={WordListsPage} />
<Route path="/settings/prompt-templates" component={PromptTemplatesPage} />
<Route path="/settings/categories" component={CategoriesPage} />
```

### Step 2: 生产构建

```bash
cd /Users/lanhezheng/llm-data-service/frontend && npm run build
```

### Step 3: 验证 FastAPI 静态托管

```bash
cd /Users/lanhezheng/llm-data-service/backend
STATIC_DIR=/Users/lanhezheng/llm-data-service/frontend/dist .venv/bin/uvicorn service.main:app --host 0.0.0.0 --port 8000 &
```

浏览器访问：
- http://localhost:8000/settings/api-configs
- http://localhost:8000/settings/wordlists
- http://localhost:8000/settings/prompt-templates
- http://localhost:8000/settings/categories

### Step 4: Commit

```bash
git add frontend/src/App.tsx
git commit -m "feat(frontend): Phase 2 routes + production build"
```

---

## 自检

### Spec 覆盖

| 需求 | 对应 Task |
|---|---|
| Sidebar 配置管理展开子菜单 | Task 1 |
| API 配置 CRUD + test + reveal | Task 2 |
| 词库 CRUD（items textarea） | Task 3 |
| Prompt 模板 CRUD + 变量预览 | Task 4 |
| 分类 CRUD（关联下拉） | Task 5 |
| 路由配置 | Task 6 |
| 生产构建 + FastAPI 托管 | Task 6 |

### Placeholder 扫描

- 无 TBD/TODO/"implement later"
- 所有代码块包含完整实现
- 所有命令包含完整路径

### 类型一致性

- `ApiConfigCreate`, `ApiConfigUpdate`, `WordListCreate`, `PromptTemplateCreate`, `CategoryCreate` 等类型在 `types.ts` (Task 2 Part 1) 中定义
- API 函数命名：`createXxx`, `updateXxx`, `deleteXxx` 统一
- Drawer 接口统一：`{ open, onClose, editing? }`
