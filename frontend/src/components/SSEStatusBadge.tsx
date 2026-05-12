import { Badge, Tooltip } from 'antd';
import { useAppStore } from '../store/appStore';

const SSE_LABELS: Record<string, string> = {
  connecting: '连接中',
  connected: '已连接',
  reconnecting: '重连中',
  closed: '已关闭',
};

const SSE_COLORS: Record<string, string> = {
  connecting: 'processing',
  connected: 'success',
  reconnecting: 'warning',
  closed: 'default',
};

export function SSEStatusBadge({ taskId }: { taskId: number }) {
  const state = useAppStore((s) => s.sseStates[taskId]);
  if (!state) return null;

  return (
    <Tooltip title={`SSE: ${SSE_LABELS[state] || state}`}>
      <Badge status={SSE_COLORS[state] as any} text={SSE_LABELS[state]} />
    </Tooltip>
  );
}
