import type { TaskOut, TaskStatus } from '../../api/types';
import { statusColors } from '../../theme/tokens';
import {
  CheckCircleFilled,
  CloseCircleFilled,
  ExclamationCircleFilled,
  SyncOutlined,
  ClockCircleFilled,
} from '@ant-design/icons';
import { useAppStore } from '../../store/appStore';

const STATUS_TITLES: Record<TaskStatus, string> = {
  pending: '任务待执行',
  running: '任务运行中',
  succeeded: '任务已完成',
  failed: '任务失败',
  aborted: '任务已中止',
};

const STATUS_ICONS: Record<TaskStatus, React.ReactNode> = {
  pending: <ClockCircleFilled />,
  running: <SyncOutlined spin />,
  succeeded: <CheckCircleFilled />,
  failed: <CloseCircleFilled />,
  aborted: <ExclamationCircleFilled />,
};

const SSE_LABELS: Record<string, string> = {
  connecting: '连接中',
  connected: '已连接',
  reconnecting: '重连中',
  closed: '已关闭',
};

export function TaskStatusBanner({ task }: { task: TaskOut }) {
  const colors = statusColors[task.status] || statusColors.pending;
  const sseState = useAppStore((s) => s.sseStates[task.id]);

  const subtitle = (() => {
    if (task.status === 'running') {
      const pct = task.progress_total > 0
        ? Math.round((task.progress_current / task.progress_total) * 100)
        : 0;
      return `已生成 ${task.progress_current} / ${task.progress_total} 条（${pct}%）`;
    }
    if (task.status === 'succeeded') {
      return `成功生成 ${task.progress_current} 条样本`;
    }
    if (task.status === 'failed') {
      return '任务执行遇到错误，请查看日志详情';
    }
    if (task.status === 'aborted') {
      return `已中止，生成了 ${task.progress_current} 条样本`;
    }
    return '等待 worker 启动';
  })();

  return (
    <div
      style={{
        background: colors.bg,
        border: `1px solid ${colors.dot}33`,
        borderLeft: `3px solid ${colors.dot}`,
        borderRadius: 8,
        padding: '14px 20px',
        display: 'flex',
        alignItems: 'center',
        gap: 14,
      }}
    >
      <span style={{ fontSize: 22, color: colors.dot, display: 'flex', alignItems: 'center' }}>
        {STATUS_ICONS[task.status]}
      </span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 15, fontWeight: 600, color: colors.text }}>
            {STATUS_TITLES[task.status]}
          </span>
          {task.status === 'running' && sseState && (
            <span
              style={{
                fontSize: 11,
                padding: '1px 6px',
                borderRadius: 3,
                background: 'rgba(255,255,255,0.6)',
                color: colors.text,
                fontWeight: 500,
              }}
            >
              SSE: {SSE_LABELS[sseState] || sseState}
            </span>
          )}
        </div>
        <div style={{ fontSize: 13, color: colors.text, opacity: 0.8, marginTop: 2 }}>
          {subtitle}
        </div>
      </div>
    </div>
  );
}
