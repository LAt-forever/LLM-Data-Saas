import { Breadcrumb, Space } from 'antd';
import { colors } from '../../theme/tokens';

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
}
