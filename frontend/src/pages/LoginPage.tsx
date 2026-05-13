import { useState } from 'react';
import { useLocation } from 'wouter';
import { useAuth } from '../hooks/useAuth';

export function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login } = useAuth();
  const [_, navigate] = useLocation();

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
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#0f172a',
        padding: 24,
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: 380,
          background: '#1e293b',
          border: '1px solid #334155',
          borderRadius: 12,
          padding: '40px',
          boxShadow: '0 20px 60px rgba(0,0,0,0.4)',
        }}
      >
        {/* Brand */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <div
              style={{
                width: 28,
                height: 28,
                background: '#2563eb',
                borderRadius: 6,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
                fontSize: 14,
                fontWeight: 600,
              }}
            >
              ◆
            </div>
            <span style={{ color: '#f1f5f9', fontSize: 16, fontWeight: 600 }}>
              LLM Data Service
            </span>
          </div>
          <div style={{ color: '#64748b', fontSize: 13 }}>
            样本数据生成与任务管理中心
          </div>
          <div
            style={{
              marginTop: 12,
              display: 'flex',
              gap: 6,
              justifyContent: 'center',
              flexWrap: 'wrap',
            }}
          >
            {['任务调度', '配置管理', '数据生成'].map((tag) => (
              <span
                key={tag}
                style={{
                  background: '#0f172a',
                  border: '1px solid #334155',
                  padding: '3px 10px',
                  borderRadius: 4,
                  fontSize: 11,
                  color: '#94a3b8',
                }}
              >
                {tag}
              </span>
            ))}
          </div>
        </div>

        {/* Divider */}
        <div style={{ height: 1, background: '#334155', marginBottom: 24 }} />

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 16 }}>
            <label
              style={{
                display: 'block',
                fontSize: 12,
                color: '#94a3b8',
                marginBottom: 6,
                fontWeight: 500,
              }}
            >
              管理员账号
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus
              style={{
                width: '100%',
                height: 40,
                background: '#0f172a',
                border: '1px solid #475569',
                borderRadius: 6,
                padding: '0 12px',
                color: '#f1f5f9',
                fontSize: 14,
                outline: 'none',
                boxSizing: 'border-box',
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = '#2563eb';
                e.currentTarget.style.boxShadow = '0 0 0 2px rgba(37,99,235,0.2)';
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = '#475569';
                e.currentTarget.style.boxShadow = 'none';
              }}
            />
          </div>

          <div style={{ marginBottom: 24 }}>
            <label
              style={{
                display: 'block',
                fontSize: 12,
                color: '#94a3b8',
                marginBottom: 6,
                fontWeight: 500,
              }}
            >
              密码
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{
                width: '100%',
                height: 40,
                background: '#0f172a',
                border: '1px solid #475569',
                borderRadius: 6,
                padding: '0 12px',
                color: '#f1f5f9',
                fontSize: 14,
                outline: 'none',
                boxSizing: 'border-box',
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = '#2563eb';
                e.currentTarget.style.boxShadow = '0 0 0 2px rgba(37,99,235,0.2)';
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = '#475569';
                e.currentTarget.style.boxShadow = 'none';
              }}
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            style={{
              width: '100%',
              height: 40,
              background: isSubmitting ? '#1d4ed8' : '#2563eb',
              border: 'none',
              borderRadius: 6,
              color: '#fff',
              fontSize: 14,
              fontWeight: 500,
              cursor: isSubmitting ? 'not-allowed' : 'pointer',
              opacity: isSubmitting ? 0.8 : 1,
            }}
          >
            {isSubmitting ? '登录中...' : '登录'}
          </button>
        </form>

        {/* Error */}
        {error && (
          <div
            style={{
              marginTop: 16,
              background: '#450a0a',
              border: '1px solid #7f1d1d',
              borderRadius: 6,
              padding: '10px 12px',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <span style={{ color: '#ef4444', fontSize: 13 }}>⚠</span>
            <span style={{ color: '#fca5a5', fontSize: 12 }}>{error}</span>
          </div>
        )}
      </div>
    </div>
  );
}
