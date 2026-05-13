import { Table, Button, Space, Tooltip } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { EditOutlined, DeleteOutlined } from '@ant-design/icons';
import type { PromptTemplateOut } from '../../api/types';
import { EmptyState } from '../common/EmptyState';
import { LoadingState } from '../common/LoadingState';

interface Props {
  templates: PromptTemplateOut[];
  loading: boolean;
  onEdit: (t: PromptTemplateOut) => void;
  onDelete: (id: number) => void;
}

export function PromptTemplateList({ templates, loading, onEdit, onDelete }: Props) {
  if (loading) return <LoadingState type="table" rows={5} />;
  if (templates.length === 0) return <EmptyState title="暂无模板" description="Prompt 模板用于定义样本生成格式" />;

  const columns: ColumnsType<PromptTemplateOut> = [
    { title: 'ID', dataIndex: 'id', width: 50, render: (id) => <span style={{ fontFamily: 'monospace' }}>{id}</span> },
    { title: '名称', dataIndex: 'name', width: 160 },
    { title: '内容', dataIndex: 'body', ellipsis: true },
    { title: '变量', width: 120, render: (_, t) => t.variables.join(', ') },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, t) => (
        <Space size="small">
          <Tooltip title="编辑"><Button type="text" size="small" icon={<EditOutlined />} onClick={() => onEdit(t)} /></Tooltip>
          <Tooltip title="删除"><Button type="text" size="small" danger icon={<DeleteOutlined />} onClick={() => onDelete(t.id)} /></Tooltip>
        </Space>
      ),
    },
  ];

  return <Table rowKey="id" columns={columns} dataSource={templates} size="small" pagination={false} />;
}
