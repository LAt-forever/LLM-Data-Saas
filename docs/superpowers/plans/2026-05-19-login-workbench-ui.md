# Login Workbench UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the old blue/dark login card with the approved Airtable Workbench Split Gate login experience.

**Architecture:** Keep authentication logic in `LoginPage.tsx` and move visual behavior into scoped `.login-workbench-*` CSS in `index.css`. `LoginPage.tsx` imports existing theme tokens and exposes them to CSS as page-local custom properties, so the login page stays tied to the Airtable/workbench design system without inventing new colors.

**Tech Stack:** React 19, TypeScript, Vite, Wouter, existing CSS, existing `frontend/src/theme/tokens.ts`.

---

## Current State And Guardrails

- Current branch: `codex/frontend-optimization`.
- Do not merge to `main`.
- Do not touch unrelated dirty state:
  - `AGENTS.md` deleted
  - `backend/package-lock.json` untracked
  - `backend/seed.log` untracked
- Do not modify backend authentication.
- Do not add new libraries, icon packages, image assets, SSO, registration, forgot-password, or marketing sections.
- Visual companion direction approved: `A. Workbench Split Gate`.
- Design spec: `docs/superpowers/specs/2026-05-19-login-workbench-design.md`.

## File Structure

- Modify `frontend/src/pages/LoginPage.tsx`
  - Keep login state, `useAuth`, submit handler, and `redirectTo` behavior.
  - Replace old inline dark-blue card with semantic Workbench Split Gate markup.
  - Import theme tokens and expose page-local CSS variables.

- Modify `frontend/src/index.css`
  - Add a scoped `.login-workbench-*` CSS block.
  - Implement desktop split-gate layout, form states, error state, and narrow-screen layout.
  - Keep styles scoped so existing app shell and task center are unaffected.

No other product files are required for this feature.

## Task 1: Replace LoginPage Markup With Workbench Split Gate Structure

**Files:**
- Modify: `frontend/src/pages/LoginPage.tsx`

- [ ] **Step 1: Run baseline checks showing why this page needs replacement**

Run:

```bash
cd /Users/lanhezheng/llm-data-service
rg -n "#2563eb|#1d4ed8|#0f172a|#1e293b|onFocus=|onBlur=|⚠" frontend/src/pages/LoginPage.tsx
```

Expected: PASS with matches. The old page still contains blue colors, dark-slate colors, inline focus/blur mutations, and an emoji-style error icon.

- [ ] **Step 2: Replace `frontend/src/pages/LoginPage.tsx` with semantic markup**

Use this complete file:

```tsx
import { useState, type CSSProperties } from 'react';
import { useLocation } from 'wouter';
import { useAuth } from '../hooks/useAuth';
import { colors, shadow, typography } from '../theme/tokens';

type LoginThemeVars = CSSProperties & Record<`--login-${string}`, string>;

const loginThemeVars: LoginThemeVars = {
  '--login-font': typography.fontFamily,
  '--login-ink': colors.primary,
  '--login-ink-strong': colors.primaryActive,
  '--login-body': colors.text.secondary,
  '--login-muted': colors.text.tertiary,
  '--login-inverse': colors.text.inverse,
  '--login-canvas': colors.bgElevated,
  '--login-surface': colors.bg,
  '--login-dark': colors.bgSidebar,
  '--login-dark-elevated': colors.bgSidebarElevated,
  '--login-border': colors.border,
  '--login-border-light': colors.borderLight,
  '--login-border-strong': colors.borderStrong,
  '--login-cream': colors.primaryBg,
  '--login-coral': colors.signature.coral,
  '--login-peach': colors.signature.peach,
  '--login-error-bg': colors.errorBg,
  '--login-focus-ring': colors.interaction.focusRing,
  '--login-table-header': colors.interaction.tableHeader,
  '--login-sidebar-muted': colors.interaction.sidebarHoverBg,
  '--login-sidebar-active': colors.interaction.sidebarSelectedBg,
  '--login-shadow': shadow.lg,
};

export function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login } = useAuth();
  const [, navigate] = useLocation();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      await login(username, password);
      const params = new URLSearchParams(window.location.search);
      const redirectTo = params.get('redirectTo') || '/';
      navigate(decodeURIComponent(redirectTo));
    } catch {
      setError('账号或密码错误');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="login-workbench" style={loginThemeVars}>
      <section className="login-workbench__stage" aria-label="LLM 样本数据登录">
        <div className="login-workbench__preview" aria-hidden="true">
          <aside className="login-workbench__rail">
            <div className="login-workbench__brand-row">
              <span className="login-workbench__mark" />
              <span className="login-workbench__brand-text">LLM 样本数据</span>
            </div>
            <div className="login-workbench__nav-stack">
              <span className="login-workbench__nav-item login-workbench__nav-item--active" />
              <span className="login-workbench__nav-item" />
              <span className="login-workbench__nav-item login-workbench__nav-item--short" />
              <span className="login-workbench__nav-item login-workbench__nav-item--short" />
            </div>
          </aside>

          <div className="login-workbench__canvas">
            <div className="login-workbench__canvas-header">
              <span className="login-workbench__canvas-title" />
              <span className="login-workbench__canvas-action" />
            </div>
            <div className="login-workbench__tabs">
              <span className="login-workbench__tab login-workbench__tab--active" />
              <span className="login-workbench__tab" />
              <span className="login-workbench__tab" />
              <span className="login-workbench__tab" />
            </div>
            <div className="login-workbench__metrics">
              <span className="login-workbench__metric login-workbench__metric--hot" />
              <span className="login-workbench__metric" />
              <span className="login-workbench__metric" />
            </div>
            <div className="login-workbench__table" />
          </div>
        </div>

        <form className="login-workbench__panel" onSubmit={handleSubmit}>
          <div className="login-workbench__panel-brand">
            <span className="login-workbench__mark" aria-hidden="true" />
            <span>LLM 样本数据</span>
          </div>

          <div className="login-workbench__copy">
            <p className="login-workbench__eyebrow">管理员入口</p>
            <h1>进入工作台</h1>
            <p>使用管理员账号继续管理样本生成任务、配置和运行结果。</p>
          </div>

          <div className="login-workbench__fields">
            <label className="login-workbench__field">
              <span>管理员账号</span>
              <input
                type="text"
                name="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoFocus
                autoComplete="username"
                aria-invalid={Boolean(error)}
                aria-describedby={error ? 'login-error' : undefined}
              />
            </label>

            <label className="login-workbench__field">
              <span>密码</span>
              <input
                type="password"
                name="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                aria-invalid={Boolean(error)}
                aria-describedby={error ? 'login-error' : undefined}
              />
            </label>
          </div>

          <button
            className="login-workbench__submit"
            type="submit"
            disabled={isSubmitting}
            aria-busy={isSubmitting}
          >
            {isSubmitting ? '登录中...' : '登录'}
          </button>

          {error && (
            <div className="login-workbench__error" id="login-error" role="alert">
              <span className="login-workbench__error-dot" aria-hidden="true" />
              <span>{error}</span>
            </div>
          )}
        </form>
      </section>
    </main>
  );
}
```

- [ ] **Step 3: Run TypeScript/build after markup replacement**

Run:

```bash
cd /Users/lanhezheng/llm-data-service/frontend
npm run build
```

Expected: PASS. Vite chunk size warning is acceptable.

- [ ] **Step 4: Commit markup change**

Only commit `LoginPage.tsx`.

```bash
cd /Users/lanhezheng/llm-data-service
git add frontend/src/pages/LoginPage.tsx
git commit -m "feat(frontend): structure workbench login page"
```

## Task 2: Add Scoped Workbench Login CSS

**Files:**
- Modify: `frontend/src/index.css`

- [ ] **Step 1: Add the scoped CSS block to `frontend/src/index.css`**

Append this CSS after the existing `.workbench-action-button` rules and before the `@media (prefers-reduced-motion: reduce)` block:

```css
.login-workbench {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
  background:
    linear-gradient(180deg, var(--login-surface) 0%, var(--login-canvas) 100%);
  color: var(--login-ink);
  font-family: var(--login-font);
}

.login-workbench__stage {
  position: relative;
  width: min(1180px, 100%);
  min-height: min(680px, calc(100vh - 64px));
  border: 1px solid var(--login-border);
  border-radius: 12px;
  overflow: hidden;
  background: var(--login-canvas);
}

.login-workbench__preview {
  min-height: min(680px, calc(100vh - 64px));
  display: grid;
  grid-template-columns: 236px minmax(0, 1fr);
  background: var(--login-surface);
}

.login-workbench__rail {
  padding: 18px 14px;
  background: var(--login-dark);
  color: var(--login-inverse);
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.login-workbench__brand-row,
.login-workbench__panel-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.login-workbench__brand-text,
.login-workbench__panel-brand {
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0;
}

.login-workbench__mark {
  width: 30px;
  height: 30px;
  flex: 0 0 auto;
  border-radius: 8px;
  background:
    linear-gradient(180deg, var(--login-peach) 0%, var(--login-coral) 100%);
}

.login-workbench__nav-stack {
  display: grid;
  gap: 10px;
}

.login-workbench__nav-item {
  height: 34px;
  width: 82%;
  border-radius: 6px;
  background: var(--login-sidebar-muted);
}

.login-workbench__nav-item--active {
  width: 100%;
  background: var(--login-sidebar-active);
}

.login-workbench__nav-item--short {
  width: 68%;
}

.login-workbench__canvas {
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.login-workbench__canvas-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--login-border);
}

.login-workbench__canvas-title,
.login-workbench__canvas-action,
.login-workbench__tab {
  display: block;
  border-radius: 999px;
}

.login-workbench__canvas-title {
  width: 160px;
  height: 22px;
  background: var(--login-ink);
}

.login-workbench__canvas-action {
  width: 112px;
  height: 34px;
  border-radius: 10px;
  background: var(--login-ink);
}

.login-workbench__tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.login-workbench__tab {
  width: 76px;
  height: 30px;
  border: 1px solid var(--login-border);
  background: var(--login-canvas);
}

.login-workbench__tab--active {
  background: var(--login-cream);
}

.login-workbench__metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.login-workbench__metric {
  min-height: 76px;
  border: 1px solid var(--login-border);
  border-radius: 10px;
  background: var(--login-canvas);
}

.login-workbench__metric--hot {
  background: var(--login-coral);
  border-color: var(--login-coral);
}

.login-workbench__table {
  min-height: 180px;
  border: 1px solid var(--login-border);
  border-radius: 10px;
  background:
    linear-gradient(var(--login-table-header) 0 0) 0 0 / 100% 36px no-repeat,
    repeating-linear-gradient(to bottom, transparent 0, transparent 38px, var(--login-border-light) 38px, var(--login-border-light) 39px),
    var(--login-canvas);
}

.login-workbench__panel {
  position: absolute;
  top: 50%;
  right: clamp(28px, 6vw, 72px);
  transform: translateY(-50%);
  width: min(420px, calc(100% - 56px));
  padding: 32px;
  border: 1px solid var(--login-border);
  border-radius: 12px;
  background: var(--login-canvas);
  box-shadow: var(--login-shadow);
}

.login-workbench__panel-brand {
  margin-bottom: 28px;
  color: var(--login-ink);
}

.login-workbench__copy {
  margin-bottom: 24px;
}

.login-workbench__eyebrow {
  margin: 0 0 8px;
  color: var(--login-muted);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0;
}

.login-workbench__copy h1 {
  margin: 0 0 8px;
  color: var(--login-ink);
  font-size: 24px;
  line-height: 1.25;
  font-weight: 600;
  letter-spacing: 0;
}

.login-workbench__copy p {
  margin: 0;
  color: var(--login-muted);
  font-size: 13px;
  line-height: 1.55;
  text-wrap: pretty;
}

.login-workbench__fields {
  display: grid;
  gap: 16px;
}

.login-workbench__field {
  display: grid;
  gap: 7px;
  color: var(--login-body);
  font-size: 12px;
  font-weight: 500;
}

.login-workbench__field input {
  width: 100%;
  min-width: 0;
  height: 40px;
  border: 1px solid var(--login-border);
  border-radius: 6px;
  padding: 0 12px;
  background: var(--login-canvas);
  color: var(--login-ink);
  font-size: 14px;
  outline: none;
  transition: border-color 180ms ease, box-shadow 180ms ease, background-color 180ms ease;
}

.login-workbench__field input:hover {
  border-color: var(--login-border-strong);
}

.login-workbench__field input:focus {
  border-color: var(--login-border-strong);
  box-shadow: 0 0 0 3px var(--login-focus-ring);
}

.login-workbench__field input[aria-invalid="true"] {
  border-color: var(--login-coral);
}

.login-workbench__submit {
  width: 100%;
  height: 42px;
  margin-top: 22px;
  border: 0;
  border-radius: 10px;
  background: var(--login-ink);
  color: var(--login-inverse);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 180ms ease, transform 180ms ease, opacity 180ms ease;
}

.login-workbench__submit:hover:not(:disabled) {
  background: var(--login-ink-strong);
}

.login-workbench__submit:active:not(:disabled) {
  transform: translateY(1px);
}

.login-workbench__submit:disabled {
  cursor: not-allowed;
  opacity: 0.72;
}

.login-workbench__error {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 14px;
  padding: 10px 12px;
  border: 1px solid var(--login-coral);
  border-radius: 6px;
  background: var(--login-error-bg);
  color: var(--login-coral);
  font-size: 12px;
  line-height: 1.4;
}

.login-workbench__error-dot {
  width: 7px;
  height: 7px;
  flex: 0 0 auto;
  border-radius: 999px;
  background: var(--login-coral);
}

@media (max-width: 860px) {
  .login-workbench {
    align-items: flex-start;
    padding: 16px;
  }

  .login-workbench__stage {
    width: 100%;
    min-height: auto;
    border: 0;
    border-radius: 0;
    overflow: visible;
    background: transparent;
  }

  .login-workbench__preview {
    display: none;
  }

  .login-workbench__panel {
    position: static;
    width: min(420px, 100%);
    margin: 48px auto 0;
    transform: none;
    padding: 24px;
  }

  .login-workbench__panel-brand {
    margin-bottom: 24px;
  }

  .login-workbench__copy h1 {
    font-size: 22px;
  }

  .login-workbench__field input,
  .login-workbench__submit {
    min-height: 44px;
  }
}
```

- [ ] **Step 2: Verify CSS is scoped and no blue remains in login files**

Run:

```bash
cd /Users/lanhezheng/llm-data-service
rg -n "#2563eb|#1d4ed8|#0f172a|#1e293b|#334155|#475569|#64748b|#94a3b8|#f1f5f9|⚠" frontend/src/pages/LoginPage.tsx frontend/src/index.css
```

Expected: no output from `LoginPage.tsx`. Existing non-login CSS may still contain old colors only if they predate this feature; do not edit unrelated selectors.

- [ ] **Step 3: Run lint and build**

Run:

```bash
cd /Users/lanhezheng/llm-data-service/frontend
npm run lint
npm run build
```

Expected:
- `npm run lint`: PASS
- `npm run build`: PASS, with current Vite chunk size warning allowed

- [ ] **Step 4: Commit CSS change**

Only commit `index.css`.

```bash
cd /Users/lanhezheng/llm-data-service
git add frontend/src/index.css
git commit -m "style(frontend): add workbench login styles"
```

## Task 3: Browser Verification And Interaction Review

**Files:**
- No planned code changes.

- [ ] **Step 1: Ensure backend and frontend are running**

If the current servers are still active, reuse them. Otherwise run:

```bash
cd /Users/lanhezheng/llm-data-service/backend
ADMIN_PASSWORD_HASH="$(.venv/bin/python -c 'import bcrypt; print(bcrypt.hashpw(b"codex-ui", bcrypt.gensalt()).decode())')" ADMIN_USERNAME=admin STATIC_DIR=../frontend/dist .venv/bin/uvicorn service.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal:

```bash
cd /Users/lanhezheng/llm-data-service/frontend
npm run dev -- --host 127.0.0.1
```

Expected:
- Backend listens on `http://127.0.0.1:8000`
- Frontend listens on `http://127.0.0.1:5173`

- [ ] **Step 2: Verify desktop layout**

Open `http://127.0.0.1:5173/login` at desktop width, around `1280x820`.

Check all of these:

- No blue brand mark, blue button, or blue focus ring.
- Login panel is white and overlays a non-interactive workbench preview.
- Workbench preview uses dark rail, light canvas, cream tab, coral metric, and hairline borders.
- Labels remain visible above inputs.
- Focus state is visible when tabbing into both inputs.
- Button loading text does not change button size.
- Error message appears below button with `role="alert"` and does not overlap content.

- [ ] **Step 3: Verify narrow layout**

Use a narrow viewport around `390x820`.

Check all of these:

- Complex workbench preview is hidden.
- Login panel is centered and fits within the viewport.
- No horizontal scrolling.
- Text does not overflow or truncate.
- Inputs and submit button are at least 44px tall.

- [ ] **Step 4: Verify login behavior**

Use the existing dev credentials if the backend was started with the command above:

```text
admin
codex-ui
```

Check:

- Wrong credentials show `账号或密码错误`.
- Correct credentials navigate to `/` or the decoded `redirectTo`.
- After login, task center renders normally.

- [ ] **Step 5: Commit any verification polish**

If browser verification reveals small visual bugs, fix only:

- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/index.css`

Then run:

```bash
cd /Users/lanhezheng/llm-data-service/frontend
npm run lint
npm run build
```

Expected: both PASS.

Commit only the touched login files:

```bash
cd /Users/lanhezheng/llm-data-service
git add frontend/src/pages/LoginPage.tsx frontend/src/index.css
git commit -m "fix(frontend): polish workbench login details"
```

If no fixes are needed, do not create an empty commit.

## Task 4: Final Review

**Files:**
- No planned code changes.

- [ ] **Step 1: Run final static verification**

Run:

```bash
cd /Users/lanhezheng/llm-data-service/frontend
npm run lint
npm run build
```

Expected:
- `npm run lint`: PASS
- `npm run build`: PASS, with current Vite chunk size warning allowed

- [ ] **Step 2: Confirm commit scope**

Run:

```bash
cd /Users/lanhezheng/llm-data-service
git status --short
git log --oneline -5
```

Expected:
- Only unrelated dirty state remains if the user has not addressed it:
  - `D AGENTS.md`
  - `?? backend/package-lock.json`
  - `?? backend/seed.log`
- Recent commits include login implementation commits.

- [ ] **Step 3: Request final code review**

Use `superpowers:requesting-code-review`.

Review scope:

```bash
PLAN_SHA="$(git log --format=%H -- docs/superpowers/plans/2026-05-19-login-workbench-ui.md | head -1)"
git diff "$PLAN_SHA"..HEAD -- frontend/src/pages/LoginPage.tsx frontend/src/index.css
```

Reviewer must check:

- Login behavior and redirect are preserved.
- `role="alert"` and labels are present.
- Background preview is non-interactive and `aria-hidden`.
- No rogue blue/purple gradients or non-token colors in the login page.
- CSS selectors are scoped under `.login-workbench`.
- Desktop and 390px layouts do not overlap or overflow.

- [ ] **Step 4: Report completion status**

Report:

- Commits created
- Verification results
- Browser review results
- Any remaining unrelated dirty state

Do not merge to `main` unless the user explicitly asks.
