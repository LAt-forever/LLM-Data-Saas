# Airtable Workbench UI 实施计划

> **给 agentic workers：** REQUIRED SUB-SKILL：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 按任务逐步实施本计划。步骤使用复选框（`- [ ]`）语法追踪。

**目标：** 先将已批准的 Airtable Workbench Reskin 应用到前端外壳，再细化任务中心首页。

**架构：** 保留当前 React + Ant Design 应用结构。将视觉决策集中到 theme tokens 和 AntD theme 配置中，再通过小而聚焦的改动让 layout/common/task 组件消费这些 token。

**技术栈：** React 19、TypeScript、Vite、Ant Design 6、Wouter、TanStack Query。

---

## 文件结构

- 修改 `frontend/src/main.tsx`：引入全局 CSS，确保应用级覆盖样式和 keyframes 被加载。
- 修改 `frontend/src/index.css`：定义基础页面样式、AntD 表格/菜单/按钮覆盖、响应式辅助样式和 `pulse`。
- 修改 `frontend/src/theme/tokens.ts`：用 Airtable 风格 token 和状态色替换蓝色 SaaS 调色板。
- 修改 `frontend/src/theme/antdTheme.ts`：将 Airtable token 映射到 AntD 组件 token。
- 修改 `frontend/src/components/layout/AppLayout.tsx`：设置全局工作台表面。
- 修改 `frontend/src/components/layout/Sidebar.tsx`：保留导航结构，应用深墨色侧边栏样式、品牌标记和紧凑用户区。
- 修改 `frontend/src/components/layout/PageShell.tsx`：应用白色头部、更轻的标题层级和柔和内容画布。
- 修改 `frontend/src/components/layout/Toolbar.tsx`：将筛选器改为 Airtable 式 view tabs，并保留搜索/创建支持。
- 修改 `frontend/src/components/common/StatusTag.tsx`：使用新的状态色和克制的圆点脉冲。
- 修改 `frontend/src/components/common/EmptyState.tsx`：用克制工作台空状态替换通用纯图标空状态。
- 修改 `frontend/src/components/common/LoadingState.tsx`：让加载状态匹配中性调色板。
- 创建 `frontend/src/components/task/TaskSummary.tsx`：从已加载任务数组派生当前页任务指标。
- 修改 `frontend/src/pages/HomePage.tsx`：插入任务摘要，并使用更新后的工具栏/列表行为。
- 修改 `frontend/src/components/task/TaskList.tsx`：细化表格密度、行节奏、进度、状态和显式详情操作。

## 任务 1：建立 Airtable Tokens 和 AntD 主题

**文件：**
- 修改：`frontend/src/theme/tokens.ts`
- 修改：`frontend/src/theme/antdTheme.ts`

- [ ] **步骤 1：运行前端基线构建**

运行：

```bash
cd /Users/lanhezheng/llm-data-service/frontend
npm run build
```

预期：PASS。如果修改前就失败，记录现有错误并停止等待 review。

- [ ] **步骤 2：用 Airtable tokens 替换 `frontend/src/theme/tokens.ts`**

使用以下完整文件内容：

```typescript
export const colors = {
  primary: '#181d26',
  primaryHover: '#0d1218',
  primaryActive: '#0d1218',
  primaryBg: '#f5e9d4',

  success: '#0a2e0e',
  successBg: '#e7f0ea',
  warning: '#d9a441',
  warningBg: '#fff7d6',
  error: '#aa2d00',
  errorBg: '#f5e6df',
  info: '#254fad',
  infoBg: '#eef4ff',

  signature: {
    coral: '#aa2d00',
    forest: '#0a2e0e',
    cream: '#f5e9d4',
    peach: '#fcab79',
    mint: '#a8d8c4',
    yellow: '#f4d35e',
    mustard: '#d9a441',
  },

  text: {
    primary: '#181d26',
    secondary: '#333840',
    tertiary: '#6f737b',
    disabled: '#b8bdc5',
    inverse: '#ffffff',
  },

  border: '#dddddd',
  borderStrong: '#9297a0',
  borderLight: '#ececec',
  bg: '#f8fafc',
  bgElevated: '#ffffff',
  bgSidebar: '#181d26',
  bgSidebarElevated: '#1d1f25',
};

export const statusColors: Record<string, { dot: string; bg: string; text: string; border?: string }> = {
  pending: { dot: '#9297a0', bg: '#f8fafc', text: '#41454d', border: '#dddddd' },
  running: { dot: '#aa2d00', bg: '#f5e9d4', text: '#181d26', border: '#d8c8aa' },
  succeeded: { dot: '#0a2e0e', bg: '#e7f0ea', text: '#0a2e0e', border: '#b9d3c1' },
  failed: { dot: '#aa2d00', bg: '#f5e6df', text: '#aa2d00', border: '#dfb8a9' },
  aborted: { dot: '#d9a441', bg: '#fff7d6', text: '#6f4f12', border: '#ead58e' },
};

export const typography = {
  fontFamily: `-apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, "Noto Sans", sans-serif`,
  sizes: {
    xs: '12px',
    sm: '13px',
    base: '14px',
    md: '16px',
    lg: '20px',
    xl: '24px',
  },
  weights: {
    normal: 400,
    medium: 500,
    semibold: 600,
  },
};

export const spacing = {
  unit: 8,
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
};

export const border = {
  radius: {
    xs: '2px',
    sm: '4px',
    md: '6px',
    lg: '10px',
    full: '9999px',
  },
};

export const shadow = {
  sm: 'none',
  md: 'none',
  lg: '0 8px 24px rgba(24,29,38,0.08)',
};
```

- [ ] **步骤 3：用 Airtable 映射主题替换 `frontend/src/theme/antdTheme.ts`**

使用以下完整文件内容：

```typescript
import type { ThemeConfig } from 'antd';
import { colors, typography } from './tokens';

export const antdTheme: ThemeConfig = {
  token: {
    colorPrimary: colors.primary,
    colorPrimaryHover: colors.primaryHover,
    colorPrimaryActive: colors.primaryActive,
    colorSuccess: colors.success,
    colorWarning: colors.warning,
    colorError: colors.error,
    colorInfo: colors.info,
    borderRadius: 6,
    borderRadiusSM: 4,
    borderRadiusLG: 10,
    fontFamily: typography.fontFamily,
    fontSize: 14,
    fontSizeSM: 13,
    fontSizeLG: 16,
    controlHeight: 34,
    controlHeightSM: 30,
    controlHeightLG: 40,
    paddingContentHorizontal: 16,
    paddingContentVertical: 12,
    colorText: colors.text.primary,
    colorTextSecondary: colors.text.secondary,
    colorTextTertiary: colors.text.tertiary,
    colorTextDisabled: colors.text.disabled,
    colorBorder: colors.border,
    colorBorderSecondary: colors.borderLight,
    colorBgContainer: colors.bgElevated,
    colorBgElevated: colors.bgElevated,
    colorBgLayout: colors.bg,
  },
  components: {
    Button: {
      borderRadius: 10,
      paddingInline: 18,
      primaryShadow: 'none',
      defaultShadow: 'none',
      fontWeight: 500,
    },
    Card: {
      borderRadiusLG: 10,
      paddingLG: 20,
      boxShadow: 'none',
    },
    Drawer: {
      borderRadius: 0,
      paddingLG: 24,
    },
    Input: {
      borderRadius: 6,
      activeBorderColor: colors.borderStrong,
      hoverBorderColor: colors.borderStrong,
      activeShadow: '0 0 0 2px rgba(24,29,38,0.08)',
    },
    InputNumber: {
      borderRadius: 6,
      activeBorderColor: colors.borderStrong,
      hoverBorderColor: colors.borderStrong,
      activeShadow: '0 0 0 2px rgba(24,29,38,0.08)',
    },
    Menu: {
      iconSize: 17,
      iconMarginInlineEnd: 10,
      itemBorderRadius: 6,
      darkItemBg: colors.bgSidebar,
      darkSubMenuItemBg: colors.bgSidebar,
      darkItemColor: 'rgba(255,255,255,0.68)',
      darkItemHoverBg: 'rgba(255,255,255,0.08)',
      darkItemSelectedBg: 'rgba(255,255,255,0.12)',
      darkItemSelectedColor: '#ffffff',
    },
    Progress: {
      borderRadius: 999,
      defaultColor: colors.signature.coral,
      remainingColor: '#e0e2e6',
    },
    Select: {
      borderRadius: 6,
      optionSelectedBg: colors.primaryBg,
    },
    Table: {
      borderRadius: 10,
      headerBg: '#fafafa',
      headerColor: colors.text.tertiary,
      rowHoverBg: '#fbfaf7',
      padding: 12,
      paddingXS: 8,
      paddingSM: 8,
      fontSize: 13,
      fontSizeSM: 12,
      borderColor: colors.borderLight,
    },
    Tabs: {
      borderRadius: 8,
      margin: 0,
      itemSelectedColor: colors.primary,
      itemHoverColor: colors.primary,
      inkBarColor: colors.primary,
    },
    Tag: {
      borderRadiusSM: 4,
      fontSize: 12,
      lineHeight: 1.5,
    },
  },
};
```

- [ ] **步骤 4：验证 TypeScript 和 Vite 构建**

运行：

```bash
cd /Users/lanhezheng/llm-data-service/frontend
npm run build
```

预期：PASS。

- [ ] **步骤 5：提交任务 1**

运行：

```bash
cd /Users/lanhezheng/llm-data-service
git add frontend/src/theme/tokens.ts frontend/src/theme/antdTheme.ts
git commit -m "style(frontend): add Airtable workbench theme tokens"
```

## 任务 2：加载全局 CSS 并添加工作台覆盖样式

**文件：**
- 修改：`frontend/src/main.tsx`
- 修改：`frontend/src/index.css`

- [ ] **步骤 1：在 `frontend/src/main.tsx` 中引入全局 CSS**

在 React imports 后立即添加 CSS import：

```typescript
import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
```

- [ ] **步骤 2：用基础样式和 AntD 覆盖替换 `frontend/src/index.css`**

使用以下完整文件内容：

```css
:root {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, "Noto Sans", sans-serif;
  color: #181d26;
  background: #f8fafc;
  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

* {
  box-sizing: border-box;
}

html,
body,
#root {
  min-width: 0;
  min-height: 100%;
  margin: 0;
}

body {
  background: #f8fafc;
}

button,
input,
textarea,
select {
  font: inherit;
}

a {
  color: inherit;
  text-decoration: none;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(170, 45, 0, 0.28);
  }
  70% {
    box-shadow: 0 0 0 6px rgba(170, 45, 0, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(170, 45, 0, 0);
  }
}

.airtable-table .ant-table {
  border: 1px solid #dddddd;
  border-radius: 10px;
  overflow: hidden;
}

.airtable-table .ant-table-thead > tr > th {
  border-bottom: 1px solid #dddddd;
  font-weight: 500;
  letter-spacing: 0;
}

.airtable-table .ant-table-tbody > tr > td {
  border-bottom: 1px solid #ececec;
}

.airtable-table .ant-table-tbody > tr:last-child > td {
  border-bottom: 0;
}

.task-row {
  transition: background-color 160ms ease;
}

.task-row:hover > td {
  background: #fbfaf7 !important;
}

.workbench-action-button.ant-btn-text:not(.ant-btn-dangerous) {
  color: #333840;
}

.workbench-action-button.ant-btn-text:not(.ant-btn-dangerous):hover {
  color: #181d26;
  background: #f5e9d4;
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
    transition-duration: 0.001ms !important;
  }
}
```

- [ ] **步骤 3：验证 CSS 引入和构建**

运行：

```bash
cd /Users/lanhezheng/llm-data-service/frontend
npm run build
```

预期：PASS。

- [ ] **步骤 4：提交任务 2**

运行：

```bash
cd /Users/lanhezheng/llm-data-service
git add frontend/src/main.tsx frontend/src/index.css
git commit -m "style(frontend): load workbench global styles"
```

## 任务 3：重设全局布局外壳样式

**文件：**
- 修改：`frontend/src/components/layout/AppLayout.tsx`
- 修改：`frontend/src/components/layout/Sidebar.tsx`
- 修改：`frontend/src/components/layout/PageShell.tsx`

- [ ] **步骤 1：更新 `AppLayout` 工作台表面**

将组件替换为：

```tsx
import { Sidebar } from './Sidebar';
import { colors } from '../../theme/tokens';

export function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: colors.bg }}>
      <Sidebar />
      <main
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          minWidth: 0,
          background: colors.bg,
        }}
      >
        {children}
      </main>
    </div>
  );
}
```

- [ ] **步骤 2：在不改变导航的前提下更新 `Sidebar` 样式**

在 `frontend/src/components/layout/Sidebar.tsx` 中添加这个 import：

```tsx
import { colors } from '../../theme/tokens';
```

保留 `NAV_ITEMS`、`activeKey` 和 `openKeys` 逻辑。只把返回的 JSX 替换为以下结构：

```tsx
return (
  <aside
    style={{
      width: collapsed ? 64 : 214,
      minWidth: collapsed ? 64 : 214,
      background: colors.bgSidebar,
      display: 'flex',
      flexDirection: 'column',
      transition: 'width 0.2s ease',
      flexShrink: 0,
      borderRight: '1px solid rgba(255,255,255,0.08)',
    }}
  >
    <div
      style={{
        height: 64,
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: collapsed ? '0 18px' : '0 16px',
        borderBottom: '1px solid rgba(255,255,255,0.08)',
      }}
    >
      <div
        style={{
          width: 28,
          height: 28,
          borderRadius: 6,
          background: colors.signature.peach,
          boxShadow: `inset 0 -8px 0 ${colors.signature.coral}`,
          flexShrink: 0,
        }}
      />
      {!collapsed && (
        <span
          style={{
            color: colors.text.inverse,
            fontSize: 14,
            fontWeight: 500,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          LLM 样本数据
        </span>
      )}
      <Button
        type="text"
        icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
        onClick={() => setCollapsed(!collapsed)}
        style={{
          color: 'rgba(255,255,255,0.58)',
          marginLeft: 'auto',
          padding: 0,
          width: 26,
          height: 26,
        }}
        title={collapsed ? '展开侧边栏' : '收起侧边栏'}
      />
    </div>

    <Menu
      theme="dark"
      mode="inline"
      inlineCollapsed={collapsed}
      selectedKeys={[activeKey]}
      openKeys={collapsed ? [] : openKeys}
      onOpenChange={setOpenKeys}
      style={{ background: 'transparent', borderRight: 'none', flex: 1, padding: '10px 8px' }}
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

    {user && (
      <div
        style={{
          padding: collapsed ? '14px 18px' : '14px 16px',
          borderTop: '1px solid rgba(255,255,255,0.08)',
          display: 'flex',
          alignItems: 'center',
          gap: 10,
        }}
      >
        {!collapsed && (
          <>
            <div
              style={{
                width: 24,
                height: 24,
                borderRadius: '50%',
                background: colors.bgElevated,
                color: colors.primary,
                display: 'grid',
                placeItems: 'center',
                fontSize: 11,
                fontWeight: 500,
                flexShrink: 0,
              }}
            >
              {user.username.slice(0, 1).toUpperCase()}
            </div>
            <span
              style={{
                color: 'rgba(255,255,255,0.72)',
                fontSize: 13,
                flex: 1,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {user.username}
            </span>
            <Button
              type="text"
              icon={<LogoutOutlined />}
              onClick={logout}
              style={{ color: 'rgba(255,255,255,0.48)', padding: 0, width: 26, height: 26 }}
              title="退出登录"
            />
          </>
        )}
        {collapsed && (
          <Button
            type="text"
            icon={<LogoutOutlined />}
            onClick={logout}
            style={{ color: 'rgba(255,255,255,0.48)', padding: 0, width: 26, height: 26, margin: '0 auto' }}
            title="退出登录"
          />
        )}
      </div>
    )}
  </aside>
);
```

- [ ] **步骤 3：更新 `PageShell` 头部和内容画布**

添加这个 import：

```tsx
import { colors } from '../../theme/tokens';
```

将外层 JSX 样式替换为：

```tsx
return (
  <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0 }}>
    <div
      style={{
        padding: '18px 28px',
        background: colors.bgElevated,
        borderBottom: `1px solid ${colors.border}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 16,
        flexWrap: 'wrap',
      }}
    >
      <div style={{ minWidth: 0 }}>
        {breadcrumb && breadcrumb.length > 0 && (
          <Breadcrumb
            style={{ marginBottom: 6, color: colors.text.tertiary }}
            items={breadcrumb.map((b) => ({
              title: b.href ? <a href={b.href}>{b.label}</a> : b.label,
            }))}
          />
        )}
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap' }}>
          <h1
            style={{
              margin: 0,
              fontSize: 22,
              fontWeight: 400,
              color: colors.text.primary,
              lineHeight: 1.25,
              letterSpacing: 0,
            }}
          >
            {title}
          </h1>
          {subtitle && <span style={{ fontSize: 13, color: colors.text.tertiary }}>{subtitle}</span>}
        </div>
      </div>
      {extra && <Space style={{ flexShrink: 0 }}>{extra}</Space>}
    </div>

    <div style={{ flex: 1, padding: 28, background: colors.bg, overflow: 'auto', minWidth: 0 }}>
      {children}
    </div>
  </div>
);
```

- [ ] **步骤 4：验证外壳构建**

运行：

```bash
cd /Users/lanhezheng/llm-data-service/frontend
npm run build
```

预期：PASS。

- [ ] **步骤 5：提交任务 3**

运行：

```bash
cd /Users/lanhezheng/llm-data-service
git add frontend/src/components/layout/AppLayout.tsx frontend/src/components/layout/Sidebar.tsx frontend/src/components/layout/PageShell.tsx
git commit -m "style(frontend): reskin app shell as Airtable workbench"
```

## 任务 4：更新共享工作台组件

**文件：**
- 修改：`frontend/src/components/layout/Toolbar.tsx`
- 修改：`frontend/src/components/common/StatusTag.tsx`
- 修改：`frontend/src/components/common/EmptyState.tsx`
- 修改：`frontend/src/components/common/LoadingState.tsx`

- [ ] **步骤 1：用 view-tab 样式替换 `Toolbar`**

使用以下完整文件内容：

```tsx
import { Button, Space, Input } from 'antd';
import { PlusOutlined, SearchOutlined } from '@ant-design/icons';
import { colors } from '../../theme/tokens';

interface FilterItem {
  key: string;
  label: string;
  active?: boolean;
  count?: number;
}

interface ToolbarProps {
  filters?: FilterItem[];
  onFilterChange?: (key: string) => void;
  searchPlaceholder?: string;
  onSearch?: (value: string) => void;
  onCreate?: () => void;
  createLabel?: string;
}

export function Toolbar({
  filters,
  onFilterChange,
  searchPlaceholder,
  onSearch,
  onCreate,
  createLabel = '新建任务',
}: ToolbarProps) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 14,
        marginBottom: 16,
        flexWrap: 'wrap',
        minWidth: 0,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap', minWidth: 0 }}>
        {filters?.map((f) => (
          <button
            key={f.key}
            onClick={() => onFilterChange?.(f.key)}
            style={{
              height: 32,
              padding: '0 12px',
              borderRadius: 8,
              border: f.active ? `1px solid #d8c8aa` : '1px solid transparent',
              fontSize: 13,
              fontWeight: 500,
              cursor: 'pointer',
              background: f.active ? colors.primaryBg : 'transparent',
              color: f.active ? colors.text.primary : colors.text.secondary,
              transition: 'background 160ms ease, border-color 160ms ease, color 160ms ease',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              whiteSpace: 'nowrap',
            }}
          >
            {f.label}
            {typeof f.count === 'number' && (
              <span style={{ fontSize: 11, fontWeight: 500, color: colors.text.tertiary }}>{f.count}</span>
            )}
          </button>
        ))}
      </div>

      <Space wrap>
        {onSearch && (
          <Input
            prefix={<SearchOutlined style={{ color: colors.text.tertiary }} />}
            placeholder={searchPlaceholder}
            onChange={(e) => onSearch(e.target.value)}
            style={{ width: 220 }}
            size="middle"
          />
        )}
        {onCreate && (
          <Button type="primary" icon={<PlusOutlined />} onClick={onCreate}>
            {createLabel}
          </Button>
        )}
      </Space>
    </div>
  );
}
```

- [ ] **步骤 2：用 Airtable 状态处理替换 `StatusTag`**

使用以下完整文件内容：

```tsx
import type { TaskStatus } from '../../api/types';
import { statusColors } from '../../theme/tokens';

interface StatusTagProps {
  status: TaskStatus;
  showDot?: boolean;
  showLabel?: boolean;
  size?: 'sm' | 'md';
  pulse?: boolean;
}

const STATUS_LABELS: Record<string, string> = {
  pending: '待执行',
  running: '运行中',
  succeeded: '成功',
  failed: '失败',
  aborted: '已中止',
};

export function StatusTag({
  status,
  showDot = true,
  showLabel = true,
  size = 'md',
  pulse = false,
}: StatusTagProps) {
  const color = statusColors[status] || statusColors.pending;
  const label = STATUS_LABELS[status] || status;

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: size === 'sm' ? 4 : 6,
        padding: size === 'sm' ? '1px 7px' : '2px 8px',
        borderRadius: 4,
        border: `1px solid ${color.border || 'transparent'}`,
        fontSize: size === 'sm' ? 12 : 13,
        fontWeight: 500,
        lineHeight: 1.5,
        background: color.bg,
        color: color.text,
        whiteSpace: 'nowrap',
      }}
    >
      {showDot && (
        <span
          style={{
            width: size === 'sm' ? 6 : 8,
            height: size === 'sm' ? 6 : 8,
            borderRadius: '50%',
            background: color.dot,
            flexShrink: 0,
            animation: pulse ? 'pulse 2s infinite' : undefined,
          }}
        />
      )}
      {showLabel && label}
    </span>
  );
}
```

- [ ] **步骤 3：用克制工作台提示替换 `EmptyState`**

使用以下完整文件内容：

```tsx
import { Button } from 'antd';
import { colors } from '../../theme/tokens';

interface EmptyStateProps {
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function EmptyState({
  title = '暂无数据',
  description = '还没有创建任何内容',
  actionLabel,
  onAction,
}: EmptyStateProps) {
  return (
    <div
      style={{
        border: `1px solid ${colors.border}`,
        borderRadius: 10,
        background: colors.bgElevated,
        padding: 28,
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: 20,
        alignItems: 'center',
      }}
    >
      <div style={{ minWidth: 0 }}>
        <div style={{ fontSize: 18, fontWeight: 400, color: colors.text.primary, marginBottom: 6 }}>
          {title}
        </div>
        <div style={{ fontSize: 13, color: colors.text.tertiary, lineHeight: 1.5, maxWidth: 520 }}>
          {description}
        </div>
        {actionLabel && onAction && (
          <Button type="primary" style={{ marginTop: 16 }} onClick={onAction}>
            {actionLabel}
          </Button>
        )}
      </div>
      <div
        aria-hidden
        style={{
          height: 104,
          borderRadius: 10,
          background: colors.signature.forest,
          padding: 18,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'flex-end',
          gap: 8,
        }}
      >
        <div style={{ width: 120, height: 8, borderRadius: 999, background: 'rgba(255,255,255,0.68)' }} />
        <div style={{ width: 82, height: 8, borderRadius: 999, background: 'rgba(255,255,255,0.5)' }} />
      </div>
    </div>
  );
}
```

- [ ] **步骤 4：更新 `LoadingState` 颜色**

将 `LoadingState` 中的内联文字颜色从 `#94a3b8` 改为 `#6f737b`，并用同样的表格表面包裹表格加载态：

```tsx
if (type === 'table') {
  return (
    <div style={{ padding: 16, background: '#ffffff', border: '1px solid #dddddd', borderRadius: 10 }}>
      <Skeleton active paragraph={{ rows: rows }} title={false} />
    </div>
  );
}
```

- [ ] **步骤 5：验证共享组件**

运行：

```bash
cd /Users/lanhezheng/llm-data-service/frontend
npm run build
```

预期：PASS。

- [ ] **步骤 6：提交任务 4**

运行：

```bash
cd /Users/lanhezheng/llm-data-service
git add frontend/src/components/layout/Toolbar.tsx frontend/src/components/common/StatusTag.tsx frontend/src/components/common/EmptyState.tsx frontend/src/components/common/LoadingState.tsx
git commit -m "style(frontend): update shared workbench components"
```

## 任务 5：添加任务中心摘要

**文件：**
- 创建：`frontend/src/components/task/TaskSummary.tsx`
- 修改：`frontend/src/pages/HomePage.tsx`

- [ ] **步骤 1：创建 `TaskSummary`**

使用以下完整文件内容：

```tsx
import type { TaskOut } from '../../api/types';
import { colors } from '../../theme/tokens';

interface TaskSummaryProps {
  tasks: TaskOut[];
}

const SUMMARY_ITEMS = [
  { key: 'running', label: '运行中', accent: 'coral' },
  { key: 'succeeded', label: '当前页成功', accent: 'neutral' },
  { key: 'failed', label: '当前页失败', accent: 'neutral' },
  { key: 'pending', label: '等待执行', accent: 'neutral' },
] as const;

export function TaskSummary({ tasks }: TaskSummaryProps) {
  const counts = tasks.reduce<Record<string, number>>((acc, task) => {
    acc[task.status] = (acc[task.status] || 0) + 1;
    return acc;
  }, {});

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
        gap: 10,
        marginBottom: 16,
      }}
    >
      {SUMMARY_ITEMS.map((item) => {
        const highlighted = item.accent === 'coral';
        return (
          <div
            key={item.key}
            style={{
              border: `1px solid ${highlighted ? colors.signature.coral : colors.border}`,
              borderRadius: 10,
              background: highlighted ? colors.signature.coral : colors.bgElevated,
              color: highlighted ? colors.text.inverse : colors.text.primary,
              padding: '13px 14px',
              minWidth: 0,
            }}
          >
            <div
              style={{
                fontSize: 11,
                color: highlighted ? 'rgba(255,255,255,0.76)' : colors.text.tertiary,
                marginBottom: 6,
              }}
            >
              {item.label}
            </div>
            <div style={{ fontSize: 22, lineHeight: 1, fontWeight: 400 }}>{counts[item.key] || 0}</div>
          </div>
        );
      })}
    </div>
  );
}
```

- [ ] **步骤 2：将摘要插入 `HomePage`**

添加这个 import：

```tsx
import { TaskSummary } from '../components/task/TaskSummary';
```

将摘要插入 `Toolbar` 和 `TaskList` 之间：

```tsx
{!isLoading && (tasks?.length || 0) > 0 && <TaskSummary tasks={tasks || []} />}
```

- [ ] **步骤 3：在任务 6 中通过 `TaskList` 为 `HomePage` 添加空状态操作**

本步骤不改代码。任务 6 会更新 `TaskList` props，让空状态可以打开现有创建抽屉。

- [ ] **步骤 4：验证摘要构建**

运行：

```bash
cd /Users/lanhezheng/llm-data-service/frontend
npm run build
```

预期：PASS。

- [ ] **步骤 5：提交任务 5**

运行：

```bash
cd /Users/lanhezheng/llm-data-service
git add frontend/src/components/task/TaskSummary.tsx frontend/src/pages/HomePage.tsx
git commit -m "feat(frontend): add task center summary"
```

## 任务 6：细化任务中心表格和空状态接线

**文件：**
- 修改：`frontend/src/components/task/TaskList.tsx`
- 修改：`frontend/src/pages/HomePage.tsx`

- [ ] **步骤 1：扩展 `TaskList` props**

将 props interface 改为：

```tsx
interface Props {
  tasks: TaskOut[];
  loading: boolean;
  onRowClick?: (task: TaskOut) => void;
  onCreate?: () => void;
}
```

将组件签名改为：

```tsx
export function TaskList({ tasks, loading, onRowClick, onCreate }: Props) {
```

- [ ] **步骤 2：将任务空状态接到创建抽屉**

将空状态代码块替换为：

```tsx
if (tasks.length === 0) {
  return (
    <EmptyState
      title="暂无任务"
      description="创建第一个数据生成任务后，可以在这里追踪进度、状态和结果。"
      actionLabel={onCreate ? '新建任务' : undefined}
      onAction={onCreate}
    />
  );
}
```

- [ ] **步骤 3：更新 `TaskList` 表格列**

保留现有 `formatRelativeTime`。将 `columns` 替换为：

```tsx
const columns: ColumnsType<TaskOut> = [
  {
    title: 'ID',
    dataIndex: 'id',
    width: 64,
    render: (id) => <span style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace', fontSize: 13, color: '#181d26' }}>#{id}</span>,
  },
  {
    title: '分类',
    dataIndex: 'category_name',
    minWidth: 160,
    ellipsis: true,
    render: (name: string) => <span style={{ color: '#181d26', fontWeight: 500 }}>{name}</span>,
  },
  {
    title: '类型',
    dataIndex: 'sample_type',
    width: 76,
    render: (t: string) => (
      <span style={{ fontSize: 12, color: '#333840', fontWeight: 500, background: '#f3f4f6', borderRadius: 4, padding: '2px 6px' }}>{t}</span>
    ),
  },
  {
    title: '模型',
    dataIndex: 'api_model',
    width: 120,
    ellipsis: true,
    render: (m: string) => <span style={{ fontSize: 12, color: '#333840' }}>{m}</span>,
  },
  {
    title: '进度',
    key: 'progress',
    width: 164,
    render: (_, t) => {
      const pct = t.progress_total > 0 ? Math.round((t.progress_current / t.progress_total) * 100) : 0;
      return (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
          <Progress
            percent={pct}
            size={[78, 7]}
            showInfo={false}
            strokeColor={t.status === 'succeeded' ? '#0a2e0e' : '#aa2d00'}
            style={{ margin: 0, flexShrink: 0 }}
          />
          <span style={{ fontSize: 12, color: '#6f737b', fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace' }}>
            {t.progress_current}/{t.progress_total}
          </span>
        </div>
      );
    },
  },
  {
    title: '状态',
    dataIndex: 'status',
    width: 100,
    render: (s: TaskOut['status']) => <StatusTag status={s} size="sm" pulse={s === 'running'} />,
  },
  {
    title: '创建时间',
    dataIndex: 'created_at',
    width: 100,
    render: (ts: string) => <span style={{ fontSize: 12, color: '#6f737b' }}>{formatRelativeTime(ts)}</span>,
  },
  {
    title: '',
    key: 'action',
    width: 52,
    align: 'center',
    render: (_, t) => (
      <span onClick={(event) => event.stopPropagation()}>
        <Link href={`/tasks/${t.id}`}>
          <Tooltip title="查看详情">
            <Button className="workbench-action-button" type="text" size="small" icon={<EyeOutlined />} />
          </Tooltip>
        </Link>
      </span>
    ),
  },
];
```

- [ ] **步骤 4：更新 `TaskList` 表格 props**

将返回的表格替换为：

```tsx
return (
  <Table
    className="airtable-table"
    rowKey="id"
    columns={columns}
    dataSource={tasks}
    pagination={false}
    size="small"
    rowClassName={() => 'task-row'}
    scroll={{ x: 780 }}
    onRow={(record) => ({
      onClick: () => onRowClick?.(record),
      style: { cursor: 'pointer' },
    })}
  />
);
```

- [ ] **步骤 5：从 `HomePage` 传入创建处理函数**

更新 `TaskList` 用法：

```tsx
<TaskList
  tasks={tasks || []}
  loading={isLoading}
  onCreate={() => setCreateOpen(true)}
  onRowClick={(task) => {
    window.location.href = `/tasks/${task.id}`;
  }}
/>
```

- [ ] **步骤 6：重设 `HomePage` 分页样式**

将分页容器和页码标签改为：

```tsx
<div style={{ marginTop: 16, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 10 }}>
```

```tsx
<span style={{ fontSize: 12, color: '#6f737b', padding: '4px 8px' }}>
  第 {page} 页
</span>
```

- [ ] **步骤 7：验证任务中心构建**

运行：

```bash
cd /Users/lanhezheng/llm-data-service/frontend
npm run build
```

预期：PASS。

- [ ] **步骤 8：提交任务 6**

运行：

```bash
cd /Users/lanhezheng/llm-data-service
git add frontend/src/components/task/TaskList.tsx frontend/src/pages/HomePage.tsx
git commit -m "style(frontend): refine task center workbench view"
```

## 任务 7：最终验证和浏览器审查

**文件：**
- 无计划代码变更。

- [ ] **步骤 1：运行 lint**

运行：

```bash
cd /Users/lanhezheng/llm-data-service/frontend
npm run lint
```

预期：PASS。

- [ ] **步骤 2：运行生产构建**

运行：

```bash
cd /Users/lanhezheng/llm-data-service/frontend
npm run build
```

预期：PASS。

- [ ] **步骤 3：启动本地前端开发服务器**

运行：

```bash
cd /Users/lanhezheng/llm-data-service/frontend
npm run dev -- --host 127.0.0.1
```

预期：Vite 输出一个 localhost URL，通常是 `http://127.0.0.1:5173/`。

- [ ] **步骤 4：桌面宽度浏览器审查**

在内置浏览器中以桌面宽度打开 Vite URL。验证：

- 侧边栏使用深墨色表面、蜜桃/珊瑚标记、紧凑导航和可读的收起控件。
- 页面头部为白色，标题字重克制，副标题弱化。
- 任务中心筛选器像 view tabs，激活态为奶油色。
- 摘要卡片从已加载任务派生，不宣称全局总数。
- 表格紧凑、有边框，且不使用蓝色。
- 行点击仍能打开任务详情。
- 显式眼睛操作能打开任务详情，且没有双重点击副作用。

- [ ] **步骤 5：窄屏宽度浏览器审查**

将内置浏览器调整到类似移动端的窄屏宽度。验证：

- 头部和工具栏换行且不重叠。
- 侧边栏收起模式仍然可用。
- 表格横向滚动，而不是把文字挤压到重叠。
- 按钮文字和 tab 标签保持在控件内部。

- [ ] **步骤 6：停止开发服务器**

在对应终端会话中用 `Ctrl+C` 停止正在运行的 Vite 进程。

- [ ] **步骤 7：提交所有仅验证阶段产生的修复**

如果步骤 4 或 5 需要小修复，只提交那些变更过的前端文件：

```bash
cd /Users/lanhezheng/llm-data-service
git add frontend/src
git commit -m "fix(frontend): polish workbench responsive details"
```

如果不需要修复，不要创建空提交。
