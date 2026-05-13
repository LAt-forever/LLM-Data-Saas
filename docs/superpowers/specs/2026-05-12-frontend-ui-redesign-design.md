# Part 3 Phase 1.5 UI Redesign · Design System

- 日期: 2026-05-12
- 方案: C (Ant Design + 深度主题定制)
- 前提: 不改后端 API、不重写数据流、不新增 Phase 2 业务功能

---

## Design Tokens

### Colors

```typescript
// src/theme/tokens.ts
export const colors = {
  primary: '#2563eb',      // 靛蓝主色
  primaryHover: '#1d4ed8',
  primaryActive: '#1e40af',
  primaryBg: '#eff6ff',    // primary-50

  success: '#10b981',
  successBg: '#ecfdf5',
  warning: '#f59e0b',
  warningBg: '#fffbeb',
  error: '#ef4444',
  errorBg: '#fef2f2',
  info: '#3b82f6',
  infoBg: '#eff6ff',

  text: {
    primary: '#0f172a',    // slate-900
    secondary: '#475569',  // slate-600
    tertiary: '#94a3b8',   // slate-400
    disabled: '#cbd5e1',   // slate-300
  },

  border: '#e2e8f0',       // slate-200
  borderLight: '#f1f5f9',  // slate-100
  bg: '#f8fafc',           // slate-50
  bgElevated: '#ffffff',
  bgSidebar: '#0f172a',    // slate-900
};

export const statusColors: Record<string, { dot: string; bg: string; text: string }> = {
  pending:    { dot: '#94a3b8', bg: '#f8fafc', text: '#64748b' },
  running:    { dot: '#3b82f6', bg: '#eff6ff', text: '#2563eb' },
  succeeded:  { dot: '#10b981', bg: '#ecfdf5', text: '#059669' },
  failed:     { dot: '#ef4444', bg: '#fef2f2', text: '#dc2626' },
  aborted:    { dot: '#f59e0b', bg: '#fffbeb', text: '#d97706' },
};
```

### Typography

```typescript
export const typography = {
  fontFamily: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
               "Helvetica Neue", Arial, "Noto Sans", sans-serif,
               "Apple Color Emoji", "Segoe UI Emoji"`,
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
    bold: 700,
  },
  lineHeights: {
    tight: '1.25',
    normal: '1.5',
    relaxed: '1.75',
  },
};
```

### Spacing

```typescript
export const spacing = {
  unit: 8,
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
  xxl: '48px',
};
```

### Border & Shadow

```typescript
export const border = {
  radius: {
    sm: '4px',
    md: '6px',
    lg: '8px',
    full: '9999px',
  },
};

export const shadow = {
  sm: '0 1px 2px rgba(0,0,0,0.04)',
  md: '0 1px 3px rgba(0,0,0,0.08)',
  lg: '0 4px 12px rgba(0,0,0,0.08)',
};
```

---

## Ant Design ConfigProvider Theme

```typescript
// src/theme/antdTheme.ts
import type { ThemeConfig } from 'antd';

export const antdTheme: ThemeConfig = {
  token: {
    colorPrimary: '#2563eb',
    colorSuccess: '#10b981',
    colorWarning: '#f59e0b',
    colorError: '#ef4444',
    colorInfo: '#3b82f6',
    borderRadius: 6,
    borderRadiusSM: 4,
    borderRadiusLG: 8,
    fontSize: 14,
    fontSizeSM: 13,
    fontSizeLG: 16,
    controlHeight: 32,
    controlHeightSM: 28,
    controlHeightLG: 40,
    paddingContentHorizontal: 16,
    paddingContentVertical: 12,
    colorText: '#0f172a',
    colorTextSecondary: '#475569',
    colorTextTertiary: '#94a3b8',
    colorBorder: '#e2e8f0',
    colorBorderSecondary: '#f1f5f9',
    colorBgContainer: '#ffffff',
    colorBgElevated: '#ffffff',
    colorBgLayout: '#f8fafc',
  },
  components: {
    Table: {
      borderRadius: 6,
      padding: 12,
      paddingXS: 8,
      paddingSM: 8,
      fontSize: 13,
      fontSizeSM: 12,
    },
    Card: {
      borderRadius: 8,
      paddingLG: 20,
    },
    Button: {
      borderRadius: 6,
      paddingInline: 16,
    },
    Tag: {
      borderRadius: 4,
      fontSize: 12,
      lineHeight: 1.5,
    },
    Menu: {
      iconSize: 18,
      iconMarginInlineEnd: 12,
    },
    Drawer: {
      borderRadius: 0,
      paddingLG: 24,
    },
    Tabs: {
      borderRadius: 6,
      margin: 0,
    },
    Progress: {
      borderRadius: 4,
    },
  },
};
```

---

## Component Interfaces

### PageShell

```typescript
interface PageShellProps {
  title: string;
  subtitle?: string;
  breadcrumb?: { label: string; href?: string }[];
  extra?: React.ReactNode;
  children: React.ReactNode;
}
```

### Sidebar

```typescript
interface SidebarProps {
  collapsed?: boolean;
  onCollapse?: (collapsed: boolean) => void;
  activeKey: string;
}

interface NavItem {
  key: string;
  icon: React.ReactNode;
  label: string;
  href: string;
}
```

### Toolbar

```typescript
interface ToolbarProps {
  filters?: {
    key: string;
    label: string;
    active?: boolean;
    count?: number;
    badgeColor?: string;
  }[];
  onFilterChange?: (key: string) => void;
  search?: boolean;
  onSearch?: (value: string) => void;
  extra?: React.ReactNode;
}
```

### StatusTag

```typescript
interface StatusTagProps {
  status: TaskStatus;
  showDot?: boolean;
  showLabel?: boolean;
  size?: 'sm' | 'md';
  pulse?: boolean; // running 时呼吸效果
}
```

### MetricCard

```typescript
interface MetricCardProps {
  label: string;
  value: string | number;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  icon?: React.ReactNode;
}
```

### DetailSection

```typescript
interface DetailSectionProps {
  title: string;
  icon?: React.ReactNode;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
  extra?: React.ReactNode;
  children: React.ReactNode;
}
```

### EmptyState / ErrorState / LoadingState

```typescript
interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: { label: string; onClick: () => void };
}

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

interface LoadingStateProps {
  type: 'table' | 'card' | 'detail' | 'inline';
  rows?: number;
}
```

### CompactTable

```typescript
interface CompactTableProps<T> {
  data: T[];
  columns: ColumnType<T>[];
  loading?: boolean;
  rowKey: string;
  onRowClick?: (record: T) => void;
  emptyState?: React.ReactNode;
}
```

---

## File Structure（重构后）

```
frontend/src/
├── theme/
│   ├── tokens.ts          # 设计 token
│   ├── antdTheme.ts       # ConfigProvider theme
│   └── index.ts           # 导出
├── components/
│   ├── layout/
│   │   ├── AppLayout.tsx      # 全局布局（Sidebar + Header + Content）
│   │   ├── Sidebar.tsx        # 侧边栏导航
│   │   ├── PageShell.tsx      # 页面外壳
│   │   └── Toolbar.tsx        # 工具栏
│   ├── common/
│   │   ├── StatusTag.tsx      # 状态标签
│   │   ├── MetricCard.tsx     # 指标卡片
│   │   ├── DetailSection.tsx  # 详情区块
│   │   ├── EmptyState.tsx     # 空态
│   │   ├── ErrorState.tsx     # 错误态
│   │   └── LoadingState.tsx   # 加载态
│   ├── task/
│   │   ├── TaskList.tsx           # 任务列表表格
│   │   ├── TaskProgress.tsx       # 进度条（大号）
│   │   ├── TaskEventTimeline.tsx  # 事件时间线
│   │   ├── TaskPreview.tsx        # 数据预览
│   │   ├── TaskLogViewer.tsx      # 日志查看器
│   │   └── TaskCreateDrawer.tsx   # 创建任务抽屉（替代 Modal）
│   └── sse/
│       └── SSEStatusBadge.tsx     # SSE 状态徽标
├── pages/
│   ├── HomePage.tsx           # 任务列表页
│   └── TaskDetailPage.tsx     # 任务详情页
├── hooks/
│   ├── useTaskStream.ts
│   └── useTaskPolling.ts
├── store/
│   └── appStore.ts
├── api/
│   ├── client.ts
│   ├── tasks.ts
│   ├── configs.ts
│   └── types.ts
├── App.tsx
└── main.tsx
```

---

## Implementation Order

1. **Theme foundation**：tokens + antdTheme + ConfigProvider
2. **Layout**：AppLayout + Sidebar + PageShell
3. **Common components**：StatusTag + Empty/Error/Loading states
4. **Task list page**：Toolbar + CompactTable + HomePage refactor
5. **Task create**：TaskCreateDrawer（替代 Modal）
6. **Task detail page**：两栏布局 + 状态横幅 + Tabs
7. **Cleanup**：删除旧组件文件、验证构建
