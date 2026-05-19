import { Skeleton, Spin } from 'antd';
import { colors } from '../../theme/tokens';

interface LoadingStateProps {
  type?: 'table' | 'card' | 'detail' | 'inline';
  rows?: number;
}

export function LoadingState({ type = 'inline', rows = 5 }: LoadingStateProps) {
  if (type === 'table') {
    return (
      <div
        style={{
          padding: 16,
          background: colors.bgElevated,
          border: `1px solid ${colors.border}`,
          borderRadius: 10,
        }}
      >
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
      <span style={{ fontSize: 13, color: colors.text.tertiary }}>加载中...</span>
    </div>
  );
}
