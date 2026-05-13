import { Breadcrumb, Space } from 'antd';

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface PageShellProps {
  title: string;
  subtitle?: string;
  breadcrumb?: BreadcrumbItem[];
  extra?: React.ReactNode;
  children: React.ReactNode;
}

export function PageShell({ title, subtitle, breadcrumb, extra, children }: PageShellProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0 }}>
      {/* Header bar */}
      <div
        style={{
          padding: '16px 24px',
          background: '#fff',
          borderBottom: '1px solid #e2e8f0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 16,
        }}
      >
        <div style={{ minWidth: 0 }}>
          {breadcrumb && breadcrumb.length > 0 && (
            <Breadcrumb
              style={{ marginBottom: 4 }}
              items={breadcrumb.map((b) => ({
                title: b.href ? <a href={b.href}>{b.label}</a> : b.label,
              }))}
            />
          )}
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <h1
              style={{
                margin: 0,
                fontSize: 20,
                fontWeight: 600,
                color: '#0f172a',
                lineHeight: 1.4,
              }}
            >
              {title}
            </h1>
            {subtitle && (
              <span style={{ fontSize: 13, color: '#94a3b8' }}>{subtitle}</span>
            )}
          </div>
        </div>
        {extra && (
          <Space style={{ flexShrink: 0 }}>{extra}</Space>
        )}
      </div>

      {/* Content */}
      <div style={{ flex: 1, padding: 24, background: '#f8fafc', overflow: 'auto' }}>
        {children}
      </div>
    </div>
  );
}
