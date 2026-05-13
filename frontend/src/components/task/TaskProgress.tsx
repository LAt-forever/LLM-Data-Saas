import { Progress } from 'antd';
import type { TaskOut } from '../../api/types';
import { statusColors } from '../../theme/tokens';

export function TaskProgress({ task }: { task: TaskOut }) {
  const percent = task.progress_total > 0
    ? Math.round((task.progress_current / task.progress_total) * 100)
    : 0;

  const colors = statusColors[task.status] || statusColors.pending;

  return (
    <div>
      <div
        style={{
          display: 'flex',
          alignItems: 'baseline',
          justifyContent: 'space-between',
          marginBottom: 8,
        }}
      >
        <span style={{ fontSize: 13, color: '#64748b', fontWeight: 500 }}>进度</span>
        <span
          style={{
            fontSize: 24,
            fontWeight: 700,
            color: colors.text,
            fontFamily: 'monospace',
          }}
        >
          {percent}%
        </span>
      </div>
      <Progress
        percent={percent}
        strokeColor={colors.dot}
        size={['100%', 8]}
        railColor="#e2e8f0"
        showInfo={false}
        status={task.status === 'failed' ? 'exception' : undefined}
      />
      <div
        style={{
          fontSize: 12,
          color: '#94a3b8',
          marginTop: 6,
          fontFamily: 'monospace',
          textAlign: 'right',
        }}
      >
        {task.progress_current} / {task.progress_total}
      </div>
    </div>
  );
}
