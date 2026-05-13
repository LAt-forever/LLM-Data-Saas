import { useQuery } from '@tanstack/react-query';
import { Table } from 'antd';
import { previewTask } from '../../api/tasks';
import { LoadingState } from '../common/LoadingState';
import { EmptyState } from '../common/EmptyState';

export function TaskPreview({ taskId }: { taskId: number }) {
  const { data, isLoading } = useQuery({
    queryKey: ['preview', taskId],
    queryFn: () => previewTask(taskId),
  });

  if (isLoading) return <LoadingState type="table" rows={4} />;

  if (!data || data.rows.length === 0) {
    return (
      <EmptyState
        title="暂无预览数据"
        description="任务生成数据后，将自动显示前几行内容"
      />
    );
  }

  const columns = data.header.map((h, i) => ({
    title: h,
    dataIndex: i,
    key: i,
    ellipsis: true,
    width: 180,
  }));

  const dataSource = data.rows.map((row, idx) => ({
    key: idx,
    ...row.reduce((acc, val, i) => ({ ...acc, [i]: val }), {}),
  }));

  return (
    <Table
      columns={columns}
      dataSource={dataSource}
      size="small"
      pagination={{ pageSize: 10, size: 'small', showSizeChanger: false }}
      scroll={{ x: 'max-content' }}
    />
  );
}
