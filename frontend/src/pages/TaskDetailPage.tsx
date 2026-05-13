import { useQuery } from '@tanstack/react-query';
import { useParams } from 'wouter';
import { getTask } from '../api/tasks';
import { useTaskStream } from '../hooks/useTaskStream';
import { TaskDetail } from '../components/task/TaskDetail';
import { PageShell } from '../components/layout/PageShell';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import { EmptyState } from '../components/common/EmptyState';

export function TaskDetailPage() {
  const params = useParams<{ id: string }>();
  const taskId = parseInt(params.id, 10);

  const { data: task, isLoading, error, refetch } = useQuery({
    queryKey: ['task', taskId],
    queryFn: () => getTask(taskId),
    enabled: !isNaN(taskId),
  });

  const shouldStream =
    !isNaN(taskId) &&
    !!task &&
    !['succeeded', 'failed', 'aborted'].includes(task.status);
  useTaskStream(shouldStream ? taskId : undefined);

  if (isNaN(taskId)) {
    return (
      <PageShell title="任务详情" breadcrumb={[{ label: '任务中心', href: '/' }]}>
        <EmptyState title="无效的任务 ID" description="URL 中的任务 ID 不是有效数字" />
      </PageShell>
    );
  }

  if (isLoading) {
    return (
      <PageShell title="任务详情" breadcrumb={[{ label: '任务中心', href: '/' }]}>
        <LoadingState type="detail" />
      </PageShell>
    );
  }

  if (error) {
    return (
      <PageShell title="任务详情" breadcrumb={[{ label: '任务中心', href: '/' }]}>
        <ErrorState
          title="加载失败"
          message={error.message}
          onRetry={() => refetch()}
        />
      </PageShell>
    );
  }

  if (!task) {
    return (
      <PageShell title="任务详情" breadcrumb={[{ label: '任务中心', href: '/' }]}>
        <EmptyState title="任务不存在" description="该任务可能已被删除" />
      </PageShell>
    );
  }

  return (
    <PageShell
      title={`任务 #${task.id}`}
      subtitle={task.category_name}
      breadcrumb={[
        { label: '任务中心', href: '/' },
        { label: `#${task.id}` },
      ]}
    >
      <TaskDetail task={task} />
    </PageShell>
  );
}
