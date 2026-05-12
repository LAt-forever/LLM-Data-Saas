import { Timeline, Tag } from 'antd';
import type { TaskEventOut } from '../api/types';

const TYPE_COLORS: Record<string, string> = {
  info: 'blue',
  progress: 'green',
  error: 'red',
  aborted: 'orange',
  completed: 'purple',
};

export function TaskEventTimeline({ events }: { events: TaskEventOut[] }) {
  if (events.length === 0) {
    return <div style={{ color: '#888' }}>暂无事件</div>;
  }

  return (
    <Timeline
      items={events.map((e) => ({
        children: (
          <div>
            <Tag color={TYPE_COLORS[e.type] || 'default'} size="small">
              {e.type}
            </Tag>
            <span style={{ marginLeft: 8, color: '#888', fontSize: 12 }}>
              {e.ts}
            </span>
            <div style={{ marginTop: 4 }}>{e.message}</div>
          </div>
        ),
      }))}
    />
  );
}
