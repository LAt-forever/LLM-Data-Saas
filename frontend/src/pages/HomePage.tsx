import { useState, useMemo } from 'react';
import { Button } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { PlusOutlined } from '@ant-design/icons';
import { listTasks } from '../api/tasks';
import { PageShell } from '../components/layout/PageShell';
import { Toolbar } from '../components/layout/Toolbar';
import { TaskList } from '../components/task/TaskList';
import { TaskCreateDrawer } from '../components/task/TaskCreateDrawer';
import { TaskSummary } from '../components/task/TaskSummary';
import type { TaskOut } from '../api/types';

const FILTERS = [
  { key: 'all', label: '全部' },
  { key: 'pending', label: '待执行' },
  { key: 'running', label: '运行中' },
  { key: 'succeeded', label: '成功' },
  { key: 'failed', label: '失败' },
  { key: 'aborted', label: '已中止' },
];

export function HomePage() {
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [page, setPage] = useState(1);
  const [createOpen, setCreateOpen] = useState(false);

  const { data: tasks, isLoading } = useQuery({
    queryKey: ['tasks', statusFilter === 'all' ? undefined : statusFilter, page],
    queryFn: () =>
      listTasks({
        status: statusFilter === 'all' ? undefined : statusFilter,
        page,
        size: 50,
      }),
    refetchInterval: (query) =>
      (query.state.data as TaskOut[] | undefined)?.some(
        (t) => t.status === 'running'
      )
        ? 1000
        : false,
  });

  const filterItems = useMemo(() => {
    const counts: Record<string, number> = {};
    tasks?.forEach((t) => {
      counts[t.status] = (counts[t.status] || 0) + 1;
    });
    return FILTERS.map((f) => ({
      ...f,
      active: f.key === statusFilter,
      count: f.key === 'all' ? tasks?.length || 0 : counts[f.key] || 0,
    }));
  }, [tasks, statusFilter]);

  return (
    <PageShell
      title="任务中心"
      subtitle="LLM 样本数据生成任务管理"
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
          新建任务
        </Button>
      }
    >
      <Toolbar
        filters={filterItems}
        onFilterChange={(key) => {
          setStatusFilter(key);
          setPage(1);
        }}
      />

      {!isLoading && (tasks?.length || 0) > 0 && <TaskSummary tasks={tasks || []} />}

      <TaskList
        tasks={tasks || []}
        loading={isLoading}
        onCreate={() => setCreateOpen(true)}
        onRowClick={(task) => {
          window.location.href = `/tasks/${task.id}`;
        }}
      />

      {/* Pagination */}
      {(tasks?.length || 0) > 0 && (
        <div style={{ marginTop: 16, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 10 }}>
          <Button
            size="small"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
          >
            上一页
          </Button>
          <span style={{ fontSize: 12, color: '#6f737b', padding: '4px 8px' }}>
            第 {page} 页
          </span>
          <Button
            size="small"
            disabled={!tasks || tasks.length < 50}
            onClick={() => setPage((p) => p + 1)}
          >
            下一页
          </Button>
        </div>
      )}

      <TaskCreateDrawer open={createOpen} onClose={() => setCreateOpen(false)} />
    </PageShell>
  );
}
