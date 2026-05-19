import { Table, Button, Progress, Tooltip } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { EyeOutlined } from '@ant-design/icons';
import type { TaskOut } from '../../api/types';
import { colors } from '../../theme/tokens';
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
  onCreate?: () => void;
}

export function TaskList({ tasks, loading, onRowClick, onCreate }: Props) {
  if (loading) return <LoadingState type="table" rows={6} />;

  if (tasks.length === 0) {
    return (
      <EmptyState
        title="暂无任务"
        description="创建第一个数据生成任务后，可以在这里追踪进度、状态和结果。"
        actionLabel={onCreate ? '新建任务' : undefined}
        onAction={onCreate}
      />
    );
  }

  const columns: ColumnsType<TaskOut> = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 64,
      render: (id) => <span style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace', fontSize: 13, color: colors.text.primary }}>#{id}</span>,
    },
    {
      title: '分类',
      dataIndex: 'category_name',
      minWidth: 160,
      ellipsis: true,
      render: (name: string) => <span style={{ color: colors.text.primary, fontWeight: 500 }}>{name}</span>,
    },
    {
      title: '类型',
      dataIndex: 'sample_type',
      width: 76,
      render: (t: string) => (
        <span style={{ fontSize: 12, color: colors.text.secondary, fontWeight: 500, background: colors.bg, borderRadius: 4, padding: '2px 6px' }}>{t}</span>
      ),
    },
    {
      title: '模型',
      dataIndex: 'api_model',
      width: 120,
      ellipsis: true,
      render: (m: string) => <span style={{ fontSize: 12, color: colors.text.secondary }}>{m}</span>,
    },
    {
      title: '进度',
      key: 'progress',
      width: 164,
      render: (_, t) => {
        const pct = t.progress_total > 0 ? Math.round((t.progress_current / t.progress_total) * 100) : 0;
        return (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
            <Progress
              percent={pct}
              size={[78, 7]}
              showInfo={false}
              strokeColor={t.status === 'succeeded' ? colors.signature.forest : colors.signature.coral}
              style={{ margin: 0, flexShrink: 0 }}
            />
            <span style={{ fontSize: 12, color: colors.text.tertiary, fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace' }}>
              {t.progress_current}/{t.progress_total}
            </span>
          </div>
        );
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (s: TaskOut['status']) => <StatusTag status={s} size="sm" pulse={s === 'running'} />,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 100,
      render: (ts: string) => <span style={{ fontSize: 12, color: colors.text.tertiary }}>{formatRelativeTime(ts)}</span>,
    },
    {
      title: '',
      key: 'action',
      width: 52,
      align: 'center',
      render: (_, t) => (
        <Tooltip title="查看详情">
          <Button
            aria-label="查看详情"
            className="workbench-action-button"
            type="text"
            size="small"
            icon={<EyeOutlined />}
            onClick={(event) => {
              event.stopPropagation();
              onRowClick?.(t);
            }}
          />
        </Tooltip>
      ),
    },
  ];

  return (
    <Table
      className="airtable-table"
      rowKey="id"
      columns={columns}
      dataSource={tasks}
      pagination={false}
      size="small"
      rowClassName={() => 'task-row'}
      scroll={{ x: 780 }}
      onRow={(record) => ({
        onClick: () => onRowClick?.(record),
        style: { cursor: 'pointer' },
      })}
    />
  );
}
