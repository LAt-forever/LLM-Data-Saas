import { useQuery } from '@tanstack/react-query';
import { useParams } from 'wouter';
import { getTask } from '../api/tasks';
import { useTaskStream } from '../hooks/useTaskStream';
import { TaskDetail } from '../components/TaskDetail';
import { Spin } from 'antd';

export function TaskDetailPage() {
  const params = useParams<{ id: string }>();
  const taskId = parseInt(params.id, 10);

  const { data: task, isLoading, error } = useQuery({
    queryKey: ['task', taskId],
    queryFn: () => getTask(taskId),
    enabled: !isNaN(taskId),
  });

  const shouldStream = !isNaN(taskId) && !!task && !['succeeded', 'failed', 'aborted'].includes(task.status);
  useTaskStream(shouldStream ? taskId : undefined);

  if (isNaN(taskId)) {
    return <div>无效的任务 ID</div>;
  }

  if (isLoading) {
    return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  }

  if (error) {
    return <div style={{ color: 'red' }}>加载失败: {error.message}</div>;
  }

  if (!task) {
    return <div>任务不存在</div>;
  }

  return <TaskDetail task={task} />;
}
