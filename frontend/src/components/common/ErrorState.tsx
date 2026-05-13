import { Button, Result } from 'antd';
import { FrownOutlined } from '@ant-design/icons';

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({
  title = '加载失败',
  message = '请求数据时发生错误',
  onRetry,
}: ErrorStateProps) {
  return (
    <Result
      status="error"
      icon={<FrownOutlined style={{ color: '#ef4444' }} />}
      title={
        <span style={{ fontSize: 16, fontWeight: 500, color: '#0f172a' }}>
          {title}
        </span>
      }
      subTitle={
        <span style={{ fontSize: 13, color: '#94a3b8' }}>{message}</span>
      }
      style={{ padding: 48 }}
      extra={
        onRetry && (
          <Button type="primary" onClick={onRetry}>
            重试
          </Button>
        )
      }
    />
  );
}
