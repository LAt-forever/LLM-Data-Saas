import { Table, Button, Space, Tag, Tooltip } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { EditOutlined, DeleteOutlined, ThunderboltOutlined, EyeOutlined } from '@ant-design/icons';
import type { ApiConfigOut } from '../../api/types';
import { EmptyState } from '../common/EmptyState';
import { LoadingState } from '../common/LoadingState';

interface Props {
  configs: ApiConfigOut[];
  loading: boolean;
  onEdit: (c: ApiConfigOut) => void;
  onDelete: (id: number) => void;
  onTest: (id: number) => void;
  onReveal: (id: number) => void;
}

export function ApiConfigList({ configs, loading, onEdit, onDelete, onTest, onReveal }: Props) {
  if (loading) return <LoadingState type="table" rows={5} />;
  if (configs.length === 0) return <EmptyState title="暂无 API 配置" description="配置 LLM 接口后才能创建任务" />;

  const columns: ColumnsType<ApiConfigOut> = [
    { title: 'ID', dataIndex: 'id', width: 50, render: (id) => <span style={{ fontFamily: 'monospace' }}>{id}</span> },
    { title: '名称', dataIndex: 'name', width: 140 },
    { title: 'Base URL', dataIndex: 'base_url', ellipsis: true, width: 200 },
    { title: '模型', dataIndex: 'model_name', width: 120 },
    { title: '类型', dataIndex: 'type', width: 70, render: (t: string) => <Tag>{t}</Tag> },
    { title: 'Key', dataIndex: 'api_key_masked', width: 120 },
    {
      title: '操作',
      key: 'action',
      width: 160,
      render: (_, c) => (
        <Space size="small">
          <Tooltip title="连通性测试"><Button type="text" size="small" icon={<ThunderboltOutlined />} onClick={() => onTest(c.id)} /></Tooltip>
          <Tooltip title="查看密钥"><Button type="text" size="small" icon={<EyeOutlined />} onClick={() => onReveal(c.id)} /></Tooltip>
          <Tooltip title="编辑"><Button type="text" size="small" icon={<EditOutlined />} onClick={() => onEdit(c)} /></Tooltip>
          <Tooltip title="删除"><Button type="text" size="small" danger icon={<DeleteOutlined />} onClick={() => onDelete(c.id)} /></Tooltip>
        </Space>
      ),
    },
  ];

  return <Table rowKey="id" columns={columns} dataSource={configs} size="small" pagination={false} />;
}
