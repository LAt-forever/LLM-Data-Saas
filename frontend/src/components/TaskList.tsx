import { Table, Tag, Button, Space } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { Link } from 'wouter';
import type { TaskOut } from '../api/types';

const STATUS_COLORS: Record<string, string> = {
  pending: 'default',
  running: 'processing',
  succeeded: 'success',
  failed: 'error',
  aborted: 'warning',
};

const STATUS_LABELS: Record<string, string> = {
  pending: '待执行',
  running: '运行中',
  succeeded: '成功',
  failed: '失败',
  aborted: '已中止',
};

interface Props {
  tasks: TaskOut[];
  loading: boolean;
  onRefresh: () => void;
}

export function TaskList({ tasks, loading, onRefresh }: Props) {
  const columns: ColumnsType<TaskOut> = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 60,
      render: (id) => <Link href={`/tasks/${id}`}>{id}</Link>,
    },
    {
      title: '分类',
      dataIndex: 'category_name',
      width: 150,
    },
    {
      title: '样本类型',
      dataIndex: 'sample_type',
      width: 80,
      render: (t: string) => <Tag>{t}</Tag>,
    },
    {
      title: '模型',
      dataIndex: 'api_model',
      width: 120,
    },
    {
      title: '目标数量',
      dataIndex: 'target_count',
      width: 90,
    },
    {
      title: '进度',
      key: 'progress',
      width: 120,
      render: (_, t) => `${t.progress_current} / ${t.progress_total}`,
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 90,
      render: (s: string) => (
        <Tag color={STATUS_COLORS[s] as any}>{STATUS_LABELS[s] || s}</Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 170,
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, t) => (
        <Space>
          <Link href={`/tasks/${t.id}`}>
            <Button size="small">详情</Button>
          </Link>
        </Space>
      ),
    },
  ];

  return (
    <Table
      rowKey="id"
      columns={columns}
      dataSource={tasks}
      loading={loading}
      pagination={false}
      size="small"
    />
  );
}
