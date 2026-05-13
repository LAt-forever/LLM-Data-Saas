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
  const colors = statusColors[status] || statusColors.pending;
  const label = STATUS_LABELS[status] || status;

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: size === 'sm' ? 4 : 6,
        padding: size === 'sm' ? '1px 6px' : '2px 8px',
        borderRadius: 4,
        fontSize: size === 'sm' ? 12 : 13,
        fontWeight: 500,
        lineHeight: 1.5,
        background: colors.bg,
        color: colors.text,
        whiteSpace: 'nowrap',
      }}
    >
      {showDot && (
        <span
          style={{
            width: size === 'sm' ? 6 : 8,
            height: size === 'sm' ? 6 : 8,
            borderRadius: '50%',
            background: colors.dot,
            flexShrink: 0,
            animation: pulse ? 'pulse 2s infinite' : undefined,
          }}
        />
      )}
      {showLabel && label}
    </span>
  );
}
