import type { TaskOut } from '../../api/types';
import { colors } from '../../theme/tokens';

interface TaskSummaryProps {
  tasks: TaskOut[];
}

const SUMMARY_ITEMS = [
  { key: 'running', label: '运行中', accent: 'coral' },
  { key: 'succeeded', label: '当前页成功', accent: 'neutral' },
  { key: 'failed', label: '当前页失败', accent: 'neutral' },
  { key: 'pending', label: '等待执行', accent: 'neutral' },
] as const;

export function TaskSummary({ tasks }: TaskSummaryProps) {
  const counts = tasks.reduce<Record<string, number>>((acc, task) => {
    acc[task.status] = (acc[task.status] || 0) + 1;
    return acc;
  }, {});

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
        gap: 10,
        marginBottom: 16,
      }}
    >
      {SUMMARY_ITEMS.map((item) => {
        const highlighted = item.accent === 'coral';
        return (
          <div
            key={item.key}
            style={{
              border: `1px solid ${highlighted ? colors.signature.coral : colors.border}`,
              borderRadius: 10,
              background: highlighted ? colors.signature.coral : colors.bgElevated,
              color: highlighted ? colors.text.inverse : colors.text.primary,
              padding: '13px 14px',
              minWidth: 0,
            }}
          >
            <div
              style={{
                fontSize: 11,
                color: highlighted ? 'rgba(255,255,255,0.76)' : colors.text.tertiary,
                marginBottom: 6,
              }}
            >
              {item.label}
            </div>
            <div style={{ fontSize: 22, lineHeight: 1, fontWeight: 400 }}>{counts[item.key] || 0}</div>
          </div>
        );
      })}
    </div>
  );
}
