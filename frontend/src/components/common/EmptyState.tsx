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
        gridTemplateColumns: 'repeat(auto-fit, minmax(min(180px, 100%), 1fr))',
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
