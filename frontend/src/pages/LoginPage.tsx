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
