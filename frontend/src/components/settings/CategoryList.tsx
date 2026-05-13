import { Table, Button, Space, Tag, Tooltip } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { EditOutlined, DeleteOutlined } from '@ant-design/icons';
import type { CategoryOut } from '../../api/types';
import { EmptyState } from '../common/EmptyState';
import { LoadingState } from '../common/LoadingState';

interface Props {
  categories: CategoryOut[];
  loading: boolean;
  onEdit: (c: CategoryOut) => void;
  onDelete: (id: number) => void;
}

export function CategoryList({ categories, loading, onEdit, onDelete }: Props) {
  if (loading) return <LoadingState type="table" rows={5} />;
  if (categories.length === 0) return <EmptyState title="暂无分类" description="分类用于组织不同样本类型的生成任务" />;

  const columns: ColumnsType<CategoryOut> = [
    { title: 'ID', dataIndex: 'id', width: 50, render: (id) => <span style={{ fontFamily: 'monospace' }}>{id}</span> },
    { title: '名称', dataIndex: 'name', width: 140 },
    { title: '类型', dataIndex: 'sample_type', width: 80, render: (t: string) => <Tag>{t}</Tag> },
    { title: '模板ID', dataIndex: 'prompt_template_id', width: 80, render: (id) => <span style={{ fontFamily: 'monospace' }}>{id}</span> },
    { title: '默认数量', dataIndex: 'default_target_count', width: 90 },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, c) => (
        <Space size="small">
          <Tooltip title="编辑"><Button type="text" size="small" icon={<EditOutlined />} onClick={() => onEdit(c)} /></Tooltip>
          <Tooltip title="删除"><Button type="text" size="small" danger icon={<DeleteOutlined />} onClick={() => onDelete(c.id)} /></Tooltip>
        </Space>
      ),
    },
  ];

  return <Table rowKey="id" columns={columns} dataSource={categories} size="small" pagination={false} />;
}
