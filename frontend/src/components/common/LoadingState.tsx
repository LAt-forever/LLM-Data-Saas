import { Skeleton, Spin } from 'antd';

interface LoadingStateProps {
  type?: 'table' | 'card' | 'detail' | 'inline';
  rows?: number;
}

export function LoadingState({ type = 'inline', rows = 5 }: LoadingStateProps) {
  if (type === 'table') {
    return (
      <div style={{ padding: 16 }}>
        <Skeleton active paragraph={{ rows: rows }} title={false} />
      </div>
    );
  }

  if (type === 'card') {
    return (
      <div style={{ padding: 24 }}>
        <Skeleton active paragraph={{ rows: rows }} />
      </div>
    );
  }

  if (type === 'detail') {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 100 }}>
        <Spin size="large" description="加载中..." />
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: 16 }}>
      <Spin size="small" />
      <span style={{ fontSize: 13, color: '#94a3b8' }}>加载中...</span>
    </div>
  );
}
