import { useQuery } from '@tanstack/react-query';
import { Spin, Empty } from 'antd';
import { getTaskLog } from '../api/tasks';

export function TaskLogViewer({ taskId }: { taskId: number }) {
  const { data, isLoading } = useQuery({
    queryKey: ['log', taskId],
    queryFn: () => getTaskLog(taskId, 200),
  });

  if (isLoading) return <Spin />;
  if (!data || data.lines.length === 0) {
    return <Empty description="暂无日志" />;
  }

  return (
    <pre
      style={{
        background: '#1e1e1e',
        color: '#d4d4d4',
        padding: 12,
        borderRadius: 4,
        fontSize: 12,
        maxHeight: 400,
        overflow: 'auto',
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-all',
      }}
    >
      {data.lines.join('')}
    </pre>
  );
}
