# 登录页 Airtable Workbench 设计规格

## 背景

当前登录页仍是旧的深蓝 SaaS 风格：暗色整屏背景、蓝色品牌块、蓝色登录按钮、重阴影卡片。它能完成登录流程，但和已经完成的 Airtable Workbench 外壳不一致，用户从登录页进入任务中心时视觉断层明显。

本规格将登录页改为 **Airtable Workbench Split Gate**：登录页看起来像覆盖在工作台之上的入口层，而不是独立的旧式登录卡片。

## 目标

- 让登录页和已完成的 Airtable Workbench 外壳保持一致。
- 去掉蓝色主视觉，统一使用深墨色、白色画布、奶油激活态、珊瑚品牌标记和灰色 hairline。
- 保留现有登录逻辑：账号、密码、提交、loading、错误提示、`redirectTo` 跳转。
- 提升 UX：更清晰的表单层级、更稳定的 focus/disabled/error 状态、更好的桌面与窄屏布局。

## 非目标

- 不新增注册、忘记密码、多账号、SSO 或权限功能。
- 不修改后端认证接口。
- 不引入新的图标库、图片资源、字体文件或营销页面内容。
- 不改变已登录后的 AppShell 信息架构。

## 设计方向

采用用户批准的 **A. Workbench Split Gate**。

桌面端页面分成两个视觉层：

1. **Workbench Preview Layer**
   - 背后展示简化后的工作台骨架：深墨色侧栏、品牌标记、页面头部、view tabs、摘要卡片和任务表格轮廓。
   - 它不承载交互，只负责暗示“登录后进入这个工作台”。

2. **Login Gate Layer**
   - 白色登录面板覆盖在预览层右侧。
   - 面板包含品牌标题、简短说明、账号输入、密码输入、主按钮和错误提示。
   - 面板是唯一可操作区域，避免背景内容抢注意力。

窄屏端隐藏复杂工作台预览，只保留紧凑品牌条和登录面板，保证 390px 宽度下没有横向滚动和文字挤压。

## 设计系统

### 色彩

只使用现有 Airtable/workbench token：

- 主色 / 文字：`colors.primary` / `colors.text.primary` (`#181d26`)
- 文字次级：`colors.text.secondary`、`colors.text.tertiary`
- 页面背景：`colors.bg`
- 面板背景：`colors.bgElevated`
- 侧栏背景：`colors.bgSidebar`
- 边线：`colors.border`、`colors.borderLight`
- focus ring：`colors.interaction.focusRing`
- 品牌标记和错误强调：`colors.signature.coral`、`colors.errorBg`
- 激活/柔和强调：`colors.primaryBg`

登录页不再使用蓝色、紫色渐变或独立新色。

### 字体

沿用项目已有字体栈和 token：

- 标题：`typography.sizes.lg` 或 `xl`，字重 `semibold`
- 正文和标签：`typography.sizes.sm` / `base`
- 字距保持 `0`
- 中文文案保持克制、工具型，不使用营销式大标题

### 间距

以 8px 为基础：

- 页面外边距：桌面 32px，移动 16px
- 登录面板内边距：桌面 32px，移动 24px
- 表单项间距：14-18px
- 按钮高度：40px 以上，移动端触控目标不小于 44px

### 圆角与阴影

- 登录面板：12px
- 输入框：6px
- 主按钮：10px
- 品牌标记：7-8px
- 只允许登录面板使用一层轻阴影；工作台预览主要靠边线和色块分层。

### 动效

- hover / focus / disabled 使用 160-220ms ease 过渡。
- 输入 focus 使用深墨色透明 focus ring。
- 登录按钮 loading 时保持布局稳定，不改变按钮宽高。
- 尊重 `prefers-reduced-motion`。

## 页面结构

### 桌面布局

- 根容器：全屏高度，背景 `colors.bg`。
- 主舞台：最大宽度约 1120-1240px，居中，使用两层结构。
- 背景工作台预览：
  - 左侧深墨色 rail，带当前品牌标记和若干导航轮廓。
  - 右侧浅色工作台画布，带页头、view tabs、摘要卡片、表格轮廓。
  - 预览元素必须是非交互的装饰性结构，不能出现可点击假控件。
- 登录面板：
  - 位于右侧或右中区域，覆盖在预览层上。
  - 标题为“进入工作台”。
  - 副文案为“使用管理员账号继续管理样本生成任务、配置和运行结果。”
  - 包含账号和密码输入、登录按钮、错误提示。

### 窄屏布局

- 隐藏详细工作台预览，避免小屏空间被假 UI 占满。
- 顶部保留品牌标记 + `LLM 样本数据`。
- 登录面板占满可用宽度，最大宽度约 420px。
- 表单和按钮不重叠、不截断，页面可自然纵向滚动。

## 交互与状态

### 默认

- 账号输入框自动聚焦。
- 主按钮为深墨色，文字白色。
- 输入框白底、灰边线，和工作台表单一致。

### Focus

- 输入框边线切到 `colors.borderStrong`。
- 使用 `colors.interaction.focusRing` 作为 2-3px focus ring。
- 保持浏览器可访问焦点，不移除键盘可见状态。

### Loading

- 提交后按钮进入 disabled/loading 视觉状态。
- 文案保留现有“登录中...”。
- 禁止重复提交。

### Error

- 错误提示使用 `colors.errorBg`、`colors.signature.coral` 和细边框。
- 文案保留“账号或密码错误”。
- 错误区域出现在按钮下方，不推动页面产生明显跳动。

### Redirect

- 保留现有逻辑：
  - 登录成功后读取 `redirectTo`
  - 若没有则跳转 `/`
  - 使用 `navigate(decodeURIComponent(redirectTo))`

## 可访问性

- 输入框必须保留可见 label，不用 placeholder 代替 label。
- 按钮使用 `type="submit"`。
- 错误提示需要使用可被读屏感知的语义或 `role="alert"`。
- 背景工作台预览不能进入 tab 顺序。
- 颜色对比应满足常规后台工具阅读要求。

## 实现范围

预计修改：

- `frontend/src/pages/LoginPage.tsx`

可选修改：

- 如果需要复用响应式和状态样式，可在 `frontend/src/index.css` 增加以 `.login-workbench-*` 命名的登录页专用样式。

实现应优先复用：

- `frontend/src/theme/tokens.ts`
- 当前 `AuthProvider` / `useAuth`
- 当前 `useLocation` 跳转方式

实现不应触碰：

- 后端认证代码
- 已登录后的 layout 组件
- 任务中心页面逻辑
- 无关脏状态文件

## 验收标准

- `npm run lint` 通过。
- `npm run build` 通过，允许保留当前 Vite chunk size warning。
- 浏览器桌面宽度验证：
  - 页面不再出现蓝色主按钮或蓝色品牌块。
  - 登录页和工作台外壳视觉一致。
  - 输入、按钮、错误提示状态正常。
  - 成功登录后进入任务中心。
- 浏览器窄屏验证：
  - 390px 宽度下没有横向滚动。
  - 表单控件不重叠，文字不溢出。
  - 触控目标可用。
- 工作区提交时只包含登录页相关文件，不能混入 `AGENTS.md` 或 backend 未跟踪文件。

## 视觉伴侣记录

视觉伴侣会话：

- URL: `http://localhost:62187`
- 选定方向：`A. Workbench Split Gate`
- v0 文件：`.superpowers/brainstorm/41679-1779182671/content/login-v0-workbench-split.html`
