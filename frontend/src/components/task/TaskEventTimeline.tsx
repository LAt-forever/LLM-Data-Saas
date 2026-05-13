import type { TaskEventOut } from '../../api/types';
import { EmptyState } from '../common/EmptyState';

const TYPE_COLORS: Record<string, string> = {
  started: '#3b82f6',
  info: '#3b82f6',
  progress: '#10b981',
  error: '#ef4444',
  aborted: '#f59e0b',
  completed: '#8b5cf6',
  finished: '#10b981',
};

function formatTime(ts: string): string {
  try {
    const d = new Date(ts);
    return d.toLocaleTimeString('zh-CN', { hour12: false });
  } catch {
    return ts;
  }
}

export function TaskEventTimeline({ events }: { events: TaskEventOut[] }) {
  if (events.length === 0) {
    return <EmptyState title="暂无事件" description="任务开始执行后会在这里显示事件流" />;
  }

  return (
    <div style={{ position: 'relative' }}>
      {events.map((e, idx) => {
        const color = TYPE_COLORS[e.type] || '#94a3b8';
        const isLast = idx === events.length - 1;
        return (
          <div
            key={e.id}
            style={{ display: 'flex', gap: 12, paddingBottom: isLast ? 0 : 16, position: 'relative' }}
          >
            {/* timeline line */}
            {!isLast && (
              <div
                style={{
                  position: 'absolute',
                  left: 5,
                  top: 16,
                  bottom: 0,
                  width: 2,
                  background: '#e2e8f0',
                }}
              />
            )}
            {/* dot */}
            <div
              style={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                background: color,
                flexShrink: 0,
                marginTop: 4,
                border: '2px solid #fff',
                boxShadow: `0 0 0 2px ${color}40`,
                position: 'relative',
                zIndex: 1,
              }}
            />
            {/* content */}
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <span
                  style={{
                    fontSize: 12,
                    fontWeight: 600,
                    color,
                    textTransform: 'uppercase',
                    letterSpacing: '0.03em',
                  }}
                >
                  {e.type}
                </span>
                <span style={{ fontSize: 12, color: '#94a3b8', fontFamily: 'monospace' }}>
                  {formatTime(e.ts)}
                </span>
              </div>
              <div
                style={{
                  fontSize: 13,
                  color: '#334155',
                  lineHeight: 1.5,
                  wordBreak: 'break-word',
                  whiteSpace: 'pre-wrap',
                }}
              >
                {e.message}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
