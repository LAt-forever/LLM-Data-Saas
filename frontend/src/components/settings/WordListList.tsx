import { Table, Button, Space, Tag, Tooltip } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { EditOutlined, DeleteOutlined } from '@ant-design/icons';
import type { WordListOut } from '../../api/types';
import { EmptyState } from '../common/EmptyState';
import { LoadingState } from '../common/LoadingState';

interface Props {
  wordlists: WordListOut[];
  loading: boolean;
  onEdit: (w: WordListOut) => void;
  onDelete: (id: number) => void;
}

export function WordListList({ wordlists, loading, onEdit, onDelete }: Props) {
  if (loading) return <LoadingState type="table" rows={5} />;
  if (wordlists.length === 0) return <EmptyState title="暂无词库" description="词库用于生成样本时的场景/语气词替换" />;

  const columns: ColumnsType<WordListOut> = [
    { title: 'ID', dataIndex: 'id', width: 50, render: (id) => <span style={{ fontFamily: 'monospace' }}>{id}</span> },
    { title: '名称', dataIndex: 'name', width: 160 },
    { title: '类型', dataIndex: 'kind', width: 80, render: (k: string) => <Tag>{k}</Tag> },
    { title: '数量', width: 80, render: (_, w) => w.items.length },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, w) => (
        <Space size="small">
          <Tooltip title="编辑"><Button type="text" size="small" icon={<EditOutlined />} onClick={() => onEdit(w)} /></Tooltip>
          <Tooltip title="删除"><Button type="text" size="small" danger icon={<DeleteOutlined />} onClick={() => onDelete(w.id)} /></Tooltip>
        </Space>
      ),
    },
  ];

  return <Table rowKey="id" columns={columns} dataSource={wordlists} size="small" pagination={false} />;
}
