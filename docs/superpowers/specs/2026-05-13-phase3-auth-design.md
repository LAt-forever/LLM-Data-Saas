# Phase 3：登录鉴权入口 + 受保护应用壳 — 设计文档

## 1. 方案对比与决策

### 1.1 方案概览

| 方案 | 描述 | 推荐度 |
|------|------|--------|
| A. 前端假登录 | localStorage 存 `isLoggedIn=true`，不调用后端 | ❌ 不推荐 |
| B. 后端 Cookie Session | 后端维护 signed session cookie，所有 API 受保护 | ✅ **推荐** |
| C. 完整多用户 RBAC | 数据库用户表 + JWT/OAuth2 + 角色权限矩阵 | ❌ 过度设计 |

### 1.2 选择方案 B 的理由

- **安全性**：HttpOnly + SameSite=Lax cookie，XSS 无法窃取，CSRF 天然防御
- **实现成本**：可控，新增 auth router + middleware + 前端 AuthProvider 即可
- **维护性**：结构清晰，后续如需扩展多用户只需替换 user store
- **适用场景**：完全匹配本项目"内部单管理员工具"定位

### 1.3 Session 策略

- **有效期**：固定 24 小时，不刷新（最简实现）
- **存储**：内存 dict（项目规模足够，无需 Redis/DB）
- **Cookie 属性**：`HttpOnly`, `SameSite=Lax`, `Secure`（生产环境）
- **无"记住我"**：保持登录页极简

---

## 2. 页面设计说明

### 2.1 布局方向：居中卡片（Centered Card on Dark Canvas）

全屏 slate-900 深色背景，中央一个精致的登录卡片。与现有 App 的深色侧边栏气质一致，更像"进入工具"而非"进入营销页"。

### 2.2 视觉层次

从上到下：

1. **品牌区**
   - 蓝色菱形 Logo（`#2563eb`，6px 圆角）
   - 产品名 "LLM Data Service"（slate-50，`font-weight: 600`，16px）
   - 副标题 "样本数据生成与任务管理中心"（slate-500，13px）
   - 三个功能标签：任务调度 / 配置管理 / 数据生成（slate-800 底 + slate-700 边框，11px）

2. **分隔线**：1px slate-700 横线

3. **表单区**
   - 账号输入框（label "管理员账号"）
   - 密码输入框（label "密码"，type="password"）
   - 登录按钮（蓝色主按钮，40px 高，6px 圆角）

4. **错误提示区**：红色面板（`#450a0a` 底 + `#fca5a5` 字），卡片内显示，非弹窗

### 2.3 视觉 Token

| 元素 | Token |
|------|-------|
| 页面背景 | `#0f172a` (slate-900) |
| 卡片背景 | `#1e293b` (slate-800) |
| 卡片边框 | `1px solid #334155` (slate-700) |
| 卡片圆角 | `12px` |
| 卡片宽度 | `380px` |
| 卡片内边距 | `40px` |
| 卡片投影 | `0 20px 60px rgba(0,0,0,0.4)` |
| 输入框背景 | `#0f172a` (slate-900) |
| 输入框边框 | `1px solid #475569` (slate-600) |
| 输入框聚焦 | `ring-2 ring-blue-500` |
| 主按钮 | `#2563eb` (blue-600) |
| 错误面板背景 | `#450a0a` |
| 错误文字 | `#fca5a5` |

### 2.4 交互行为

- **表单提交**：按钮显示 loading spinner + disabled
- **登录失败**：红色面板滑入，不清空密码（方便重试）
- **登录成功**：短暂 loading 后跳转到 `redirectTo`（用户原本想访问的页面，默认 `/`）
- **Enter 键**：表单支持 Enter 提交

---

## 3. 架构与数据流

### 3.1 后端架构

```
┌─────────────────────────────────────────────┐
│  FastAPI App                                │
│  ┌──────────────┐  ┌──────────────────────┐ │
│  │ Session      │  │ Auth Router          │ │
│  │ Middleware   │  │ /api/auth/login      │ │
│  │              │  │ /api/auth/logout     │ │
│  │ ┌──────────┐ │  │ /api/auth/me         │ │
│  │ │ Memory   │ │  └──────────────────────┘ │
│  │ │ Session  │ │                           │
│  │ │ Store    │ │  ┌──────────────────────┐ │
│  │ └──────────┘ │  │ Business Routers     │ │
│  └──────────────┘  │ (all + require_auth) │ │
│                    └──────────────────────┘ │
└─────────────────────────────────────────────┘
```

### 3.2 认证流程

```
User ──POST /api/auth/login──→ Backend
                                  │
                                  ▼
                          Verify bcrypt hash
                                  │
                                  ▼
                          Generate session_id
                          Store in memory dict
                          Set session_id cookie
                                  │
User ←────{ username }─────── Backend

User ──GET /api/tasks────────→ Backend
                                  │
                                  ▼
                          Read session_id from cookie
                          Lookup in memory store
                          Check expiry
                                  │
User ←────tasks data─────── Backend (or 401)
```

### 3.3 前端架构

```
┌──────────────────────────────────────────┐
│  AuthProvider (Context)                  │
│  - user state                            │
│  - isLoading state                       │
│  - login() / logout()                    │
│  - /api/auth/me on mount                 │
├──────────────────────────────────────────┤
│  Switch                                  │
│  ┌─────────────┐  ┌──────────────────┐   │
│  │ /login      │  │ ProtectedRoute   │   │
│  │ LoginPage   │  │ ┌──────────────┐ │   │
│  │ (no layout) │  │ │ AppLayout    │ │   │
│  └─────────────┘  │ │ + Sidebar    │ │   │
│                   │ │ + Pages      │ │   │
│                   │ └──────────────┘ │   │
│                   └──────────────────┘   │
└──────────────────────────────────────────┘
```

### 3.4 前端状态机

```
Initial
  │
  ▼
Checking ──/api/auth/me──→ Authenticated ──logout()──→ Unauthenticated
  │                              ▲                              │
  │                              └─────────login()──────────────┘
  │
  └──401──→ Unauthenticated
```

---

## 4. API 设计

### 4.1 端点列表

| 端点 | 方法 | 认证 | 请求体 | 响应 |
|------|------|------|--------|------|
| `/api/auth/me` | GET | 无需 | — | `{ username: string }` / 401 |
| `/api/auth/login` | POST | 无需 | `{ username, password }` | `{ username: string }` + Set-Cookie / 401 |
| `/api/auth/logout` | POST | 需要 | — | `{ ok: true }` + 清除 Cookie |

### 4.2 请求/响应示例

**登录成功**：
```http
POST /api/auth/login
Content-Type: application/json

{"username":"admin","password":"secret"}
```
```http
HTTP/1.1 200 OK
Set-Cookie: session_id=abc123; HttpOnly; SameSite=Lax; Max-Age=86400

{"username":"admin"}
```

**登录失败**：
```http
HTTP/1.1 401 Unauthorized

{"detail":"Invalid credentials"}
```

**获取当前用户**：
```http
GET /api/auth/me
Cookie: session_id=abc123
```
```http
HTTP/1.1 200 OK

{"username":"admin"}
```

### 4.3 Cookie 属性

```
name:     session_id
httpOnly: true
sameSite: lax
secure:   true   (仅当环境变量要求 HTTPS 时)
maxAge:   86400  (24h)
path:     /
```

---

## 5. 前后端改动范围

### 5.1 后端新增文件

| 文件 | 职责 |
|------|------|
| `service/routers/auth.py` | `/api/auth/login`, `/api/auth/logout`, `/api/auth/me` |
| `service/session.py` | 内存 session store：create_session, get_session, delete_session, cleanup_expired |
| `service/security.py` | bcrypt 密码验证：verify_password |

### 5.2 后端修改文件

| 文件 | 修改内容 |
|------|----------|
| `service/config.py` | 新增 `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH` |
| `service/main.py` | 注册 auth router；为所有业务路由添加 `Depends(require_auth)`（或全局 middleware） |
| `service/routers/*.py` | 所有业务 API 加上 auth dependency |

### 5.3 前端新增文件

| 文件 | 职责 |
|------|------|
| `src/context/AuthContext.tsx` | React Context：user, isLoading, login, logout |
| `src/hooks/useAuth.ts` | `useAuth()` hook，封装 Context 消费 |
| `src/components/ProtectedRoute.tsx` | 路由守卫：未登录跳转 `/login?redirectTo=xxx` |
| `src/pages/LoginPage.tsx` | 登录页组件 |

### 5.4 前端修改文件

| 文件 | 修改内容 |
|------|----------|
| `src/App.tsx` | 引入 AuthProvider；路由结构调整：`/login` 在 AppLayout 外，业务路由包在 ProtectedRoute 中 |
| `src/api/client.ts` | 统一处理 401：清除状态、跳转到 `/login`、显示 toast |
| `src/components/layout/Sidebar.tsx` | 底部新增管理员信息 + 退出按钮 |

---

## 6. 路由结构

```tsx
// App.tsx 新结构
<AuthProvider>
  <ConfigProvider theme={antdTheme}>
    <QueryClientProvider client={queryClient}>
      <Switch>
        {/* 公开路由：无布局 */}
        <Route path="/login" component={LoginPage} />

        {/* 受保护路由：有布局 */}
        <Route>
          <ProtectedRoute>
            <AppLayout>
              <Switch>
                <Route path="/" component={HomePage} />
                <Route path="/tasks/:id" component={TaskDetailPage} />
                <Route path="/settings/api-configs" component={ApiConfigsPage} />
                <Route path="/settings/wordlists" component={WordListsPage} />
                <Route path="/settings/prompt-templates" component={PromptTemplatesPage} />
                <Route path="/settings/categories" component={CategoriesPage} />
                <Route>404: 页面不存在</Route>
              </Switch>
            </AppLayout>
          </ProtectedRoute>
        </Route>
      </Switch>
      <ToastContainer />
    </QueryClientProvider>
  </ConfigProvider>
</AuthProvider>
```

---

## 7. 风险与验证方式

| 风险 | 缓解措施 | 验证方式 |
|------|----------|----------|
| Session 内存泄露 | 启动时 sweep 过期 session；定期清理 | 检查 `session.py` cleanup 逻辑 |
| 密码明文存储 | 环境变量读取 bcrypt hash；拒绝明文 | 检查 `config.py`；启动日志拒绝无 hash |
| XSS 窃取凭证 | HttpOnly cookie（JS 不可读） | DevTools → Cookies 验证 HttpOnly 标志 |
| CSRF 攻击 | SameSite=Lax | Network 面板验证跨站 POST cookie 行为 |
| 前端 401 处理遗漏 | `api/client.ts` 统一拦截 | 清除 cookie 后刷新，确认跳转 `/login` |
| 未登录访问 API | 所有业务路由加 `require_auth` | `curl` 不带 cookie 访问 API，确认 401 |
| 密码暴力破解 | 简单 rate limit（后续可加强） | 连续错误 5 次后延迟响应 |

---

## 8. 实施计划

### Step 1：后端鉴权基础设施
1. `config.py` 新增 `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH`
2. `security.py` 实现 bcrypt 验证
3. `session.py` 实现内存 session store
4. `routers/auth.py` 实现三个端点
5. `main.py` 注册 auth router + 全局 auth dependency

### Step 2：后端 API 保护
6. 为所有现有业务 router 添加 `Depends(require_auth)`
7. 测试：`curl` 验证 401 / 登录后 200

### Step 3：前端 Auth 层
8. `AuthContext.tsx` + `useAuth.ts`
9. `ProtectedRoute.tsx`
10. 修改 `App.tsx` 路由结构

### Step 4：前端登录页
11. `LoginPage.tsx` 实现
12. `api/client.ts` 401 拦截 + toast

### Step 5：Sidebar 退出入口
13. Sidebar 底部新增管理员信息 + 退出按钮

### Step 6：验证 & 收尾
14. 端到端验证所有场景（见风险表）
15. 更新 README 部署说明（环境变量）
16. Commit 设计文档

---

## 9. 部署注意事项

部署前需要设置环境变量：

```bash
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=$2b$12$...  # bcrypt hash，可通过脚本生成
```

生成 hash 的辅助命令：
```bash
cd backend && python -c "import bcrypt; print(bcrypt.hashpw(b'your-password', bcrypt.gensalt()).decode())"
```

---

*设计确认日期：2026-05-13*
*方案：后端 Cookie Session（方案 B）*
*Session 策略：24 小时固定*
*登录页布局：居中卡片（方案 B）*
