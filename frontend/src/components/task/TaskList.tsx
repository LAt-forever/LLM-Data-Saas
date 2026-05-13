import { Table, Button, Progress, Tooltip } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { Link } from 'wouter';
import { EyeOutlined } from '@ant-design/icons';
import type { TaskOut } from '../../api/types';
import { StatusTag } from '../common/StatusTag';
import { EmptyState } from '../common/EmptyState';
import { LoadingState } from '../common/LoadingState';

function formatRelativeTime(ts: string): string {
  const date = new Date(ts);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return '刚刚';
  if (diffMins < 60) return `${diffMins} 分钟前`;
  if (diffHours < 24) return `${diffHours} 小时前`;
  if (diffDays < 7) return `${diffDays} 天前`;
  return date.toLocaleDateString('zh-CN');
}

interface Props {
  tasks: TaskOut[];
  loading: boolean;
  onRowClick?: (task: TaskOut) => void;
}

export function TaskList({ tasks, loading, onRowClick }: Props) {
  if (loading) return <LoadingState type="table" rows={6} />;

  if (tasks.length === 0) {
    return (
      <EmptyState
        title="暂无任务"
        description="还没有创建任何数据生成任务"
      />
    );
  }

  const columns: ColumnsType<TaskOut> = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 56,
      render: (id) => <span style={{ fontFamily: 'monospace', fontSize: 13 }}>{id}</span>,
    },
    {
      title: '分类',
      dataIndex: 'category_name',
      width: 120,
      ellipsis: true,
    },
    {
      title: '类型',
      dataIndex: 'sample_type',
      width: 60,
      render: (t: string) => (
        <span style={{ fontSize: 12, color: '#64748b', fontWeight: 500 }}>{t}</span>
      ),
    },
    {
      title: '模型',
      dataIndex: 'api_model',
      width: 100,
      ellipsis: true,
      render: (m: string) => <span style={{ fontSize: 12 }}>{m}</span>,
    },
    {
      title: '进度',
      key: 'progress',
      width: 140,
      render: (_, t) => {
        const pct = t.progress_total > 0
          ? Math.round((t.progress_current / t.progress_total) * 100)
          : 0;
        return (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Progress
              percent={pct}
              size={[60, 6]}
              showInfo={false}
              style={{ margin: 0, transition: 'all 0.5s ease' }}
            />
            <span style={{ fontSize: 12, color: '#64748b', fontFamily: 'monospace' }}>
              {t.progress_current}/{t.progress_total}
            </span>
          </div>
        );
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 90,
      render: (s: string) => (
        <StatusTag
          status={s as any}
          size="sm"
          pulse={s === 'running'}
        />
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 90,
      render: (ts: string) => (
        <span style={{ fontSize: 12, color: '#94a3b8' }}>
          {formatRelativeTime(ts)}
        </span>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 70,
      align: 'center',
      render: (_, t) => (
        <Link href={`/tasks/${t.id}`}>
          <Tooltip title="查看详情">
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined />}
              style={{ color: '#2563eb' }}
            />
          </Tooltip>
        </Link>
      ),
    },
  ];

  return (
    <Table
      rowKey="id"
      columns={columns}
      dataSource={tasks}
      pagination={false}
      size="small"
      rowClassName={() => 'task-row'}
      onRow={(record) => ({
        onClick: () => onRowClick?.(record),
        style: { cursor: 'pointer' },
      })}
    />
  );
}
