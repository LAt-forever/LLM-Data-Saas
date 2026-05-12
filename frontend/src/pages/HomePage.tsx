import { useState } from 'react';
import { Button, Space, Select, Card } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { listTasks } from '../api/tasks';
import { TaskList } from '../components/TaskList';
import { TaskCreateModal } from '../components/TaskCreateModal';

export function HomePage() {
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);
  const [page, setPage] = useState(1);
  const [createOpen, setCreateOpen] = useState(false);

  const { data: tasks, isLoading, refetch } = useQuery({
    queryKey: ['tasks', statusFilter, page],
    queryFn: () => listTasks({ status: statusFilter, page, size: 50 }),
    refetchInterval: (data) =>
      data?.some((t) => t.status === 'running') ? 3000 : false,
  });

  return (
    <Card
      title="任务列表"
      extra={
        <Space>
          <Select
            placeholder="状态筛选"
            allowClear
            style={{ width: 120 }}
            options={[
              { value: 'pending', label: '待执行' },
              { value: 'running', label: '运行中' },
              { value: 'succeeded', label: '成功' },
              { value: 'failed', label: '失败' },
              { value: 'aborted', label: '已中止' },
            ]}
            onChange={(v) => { setStatusFilter(v); setPage(1); }}
          />
          <Button onClick={() => refetch()}>刷新</Button>
          <Button type="primary" onClick={() => setCreateOpen(true)}>
            新建任务
          </Button>
        </Space>
      }
    >
      <TaskList tasks={tasks || []} loading={isLoading} onRefresh={refetch} />
      <div style={{ marginTop: 16, textAlign: 'center' }}>
        <Button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
          上一页
        </Button>
        <span style={{ margin: '0 16px' }}>第 {page} 页</span>
        <Button
          disabled={!tasks || tasks.length < 50}
          onClick={() => setPage((p) => p + 1)}
        >
          下一页
        </Button>
      </div>
      <TaskCreateModal open={createOpen} onClose={() => setCreateOpen(false)} />
    </Card>
  );
}
