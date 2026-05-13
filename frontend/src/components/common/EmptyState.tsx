import { Button, Empty } from 'antd';
import { InboxOutlined } from '@ant-design/icons';

interface EmptyStateProps {
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function EmptyState({
  title = '暂无数据',
  description = '还没有创建任何内容',
  actionLabel,
  onAction,
}: EmptyStateProps) {
  return (
    <div style={{ padding: '48px 24px', textAlign: 'center' }}>
      <Empty
        image={<InboxOutlined style={{ fontSize: 48, color: '#cbd5e1' }} />}
        description={
          <div>
            <div style={{ fontSize: 14, fontWeight: 500, color: '#0f172a', marginBottom: 4 }}>
              {title}
            </div>
            <div style={{ fontSize: 13, color: '#94a3b8' }}>{description}</div>
          </div>
        }
      />
      {actionLabel && onAction && (
        <Button type="primary" style={{ marginTop: 16 }} onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
