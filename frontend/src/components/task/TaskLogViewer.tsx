import { useQuery } from '@tanstack/react-query';
import { getTaskLog } from '../../api/tasks';
import { LoadingState } from '../common/LoadingState';
import { EmptyState } from '../common/EmptyState';

export function TaskLogViewer({ taskId }: { taskId: number }) {
  const { data, isLoading } = useQuery({
    queryKey: ['log', taskId],
    queryFn: () => getTaskLog(taskId, 500),
  });

  if (isLoading) return <LoadingState type="card" rows={6} />;

  if (!data || data.lines.length === 0) {
    return (
      <EmptyState
        title="暂无日志"
        description="任务启动后，worker 进程的标准输出会显示在这里"
      />
    );
  }

  return (
    <pre
      style={{
        background: '#0f172a',
        color: '#cbd5e1',
        padding: '14px 16px',
        borderRadius: 6,
        fontSize: 12,
        lineHeight: 1.6,
        maxHeight: 480,
        overflow: 'auto',
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-all',
        fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
        margin: 0,
      }}
    >
      {data.lines.join('')}
    </pre>
  );
}
