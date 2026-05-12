import { Progress } from 'antd';
import type { TaskOut } from '../api/types';

export function TaskProgress({ task }: { task: TaskOut }) {
  const percent = task.progress_total > 0
    ? Math.round((task.progress_current / task.progress_total) * 100)
    : 0;

  const statusMap: Record<string, 'success' | 'exception' | 'normal' | 'active'> = {
    pending: 'normal',
    running: 'active',
    succeeded: 'success',
    failed: 'exception',
    aborted: 'exception',
  };

  return (
    <div>
      <Progress
        percent={percent}
        status={statusMap[task.status] || 'normal'}
        format={() => `${task.progress_current} / ${task.progress_total}`}
      />
      <div style={{ color: '#888', fontSize: 12 }}>
        状态: {task.status} | 创建: {task.created_at}
        {task.started_at && ` | 开始: ${task.started_at}`}
        {task.finished_at && ` | 完成: ${task.finished_at}`}
      </div>
      {task.error_msg && (
        <div style={{ color: '#cf1322', marginTop: 8, whiteSpace: 'pre-wrap' }}>
          {task.error_msg}
        </div>
      )}
    </div>
  );
}
