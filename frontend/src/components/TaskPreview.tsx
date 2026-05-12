import { useQuery } from '@tanstack/react-query';
import { Table, Spin } from 'antd';
import { previewTask } from '../api/tasks';

export function TaskPreview({ taskId }: { taskId: number }) {
  const { data, isLoading } = useQuery({
    queryKey: ['preview', taskId],
    queryFn: () => previewTask(taskId),
  });

  if (isLoading) return <Spin />;
  if (!data || data.rows.length === 0) {
    return <div style={{ color: '#888' }}>暂无预览数据</div>;
  }

  const columns = data.header.map((h, i) => ({
    title: h,
    dataIndex: i,
    key: i,
    ellipsis: true,
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
      pagination={{ pageSize: 10 }}
      scroll={{ x: 'max-content' }}
    />
  );
}
