import { useState } from 'react';
import { Card, Button, Tabs, Popconfirm, message, Alert } from 'antd';
import {
  StopOutlined,
  DeleteOutlined,
  DownloadOutlined,
  HistoryOutlined,
  DatabaseOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { abortTask, deleteTask, downloadTask } from '../../api/tasks';
import type { TaskDetail as TaskDetailType } from '../../api/types';
import { useLocation } from 'wouter';
import { TaskProgress } from './TaskProgress';
import { TaskEventTimeline } from './TaskEventTimeline';
import { TaskPreview } from './TaskPreview';
import { TaskLogViewer } from './TaskLogViewer';
import { TaskStatusBanner } from './TaskStatusBanner';

interface Props {
  task: TaskDetailType;
}

function MetaRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'baseline',
        padding: '8px 0',
        borderBottom: '1px solid #f1f5f9',
        fontSize: 13,
      }}
    >
      <span style={{ color: '#94a3b8' }}>{label}</span>
      <span
        style={{
          color: '#334155',
          fontWeight: 500,
          textAlign: 'right',
          wordBreak: 'break-all',
          maxWidth: '65%',
        }}
      >
        {value}
      </span>
    </div>
  );
}

export function TaskDetail({ task }: Props) {
  const [, navigate] = useLocation();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('events');

  const abortMutation = useMutation({
    mutationFn: () => abortTask(task.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['task', task.id] });
      message.success('任务已中止');
    },
    onError: (err: Error) => {
      message.error(err.message);
      queryClient.invalidateQueries({ queryKey: ['task', task.id] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteTask(task.id),
    onSuccess: () => {
      navigate('/');
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      message.success('任务已删除');
    },
    onError: (err: Error) => {
      message.error(err.message);
    },
  });

  const isTerminal = ['succeeded', 'failed', 'aborted'].includes(task.status);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <TaskStatusBanner task={task} />

      {task.error_msg && (
        <Alert
          type="error"
          showIcon
          title="错误详情"
          description={
            <pre
              style={{
                margin: 0,
                fontSize: 12,
                fontFamily: 'ui-monospace, monospace',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}
            >
              {task.error_msg}
            </pre>
          }
        />
      )}

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '300px 1fr',
          gap: 16,
          alignItems: 'start',
        }}
      >
        {/* Left: info panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card size="small" styles={{ body: { padding: 20 } }}>
            <TaskProgress task={task} />
          </Card>

          <Card size="small" title="任务信息" styles={{ body: { padding: '8px 20px' } }}>
            <MetaRow
              label="分类"
              value={`[${task.sample_type}] ${task.category_name}`}
            />
            <MetaRow label="模型" value={task.api_model} />
            <MetaRow
              label="API 类型"
              value={task.snapshot_api_type}
            />
            <MetaRow label="目标数量" value={task.target_count} />
            <MetaRow label="批次大小" value={task.batch_size} />
            <MetaRow label="并发数" value={task.max_workers} />
            <MetaRow label="每文件最大" value={task.max_per_file} />
            {task.resume_from_task_id && (
              <MetaRow label="续跑自" value={`#${task.resume_from_task_id}`} />
            )}
            <MetaRow
              label="创建时间"
              value={<span style={{ fontFamily: 'monospace' }}>{task.created_at}</span>}
            />
            {task.started_at && (
              <MetaRow
                label="开始时间"
                value={<span style={{ fontFamily: 'monospace' }}>{task.started_at}</span>}
              />
            )}
            {task.finished_at && (
              <MetaRow
                label="完成时间"
                value={<span style={{ fontFamily: 'monospace' }}>{task.finished_at}</span>}
              />
            )}
          </Card>

          <Card size="small" title="操作" styles={{ body: { padding: 16 } }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {!isTerminal && (
                <Popconfirm
                  title="确认中止任务？"
                  description="中止后 worker 会尽快停止，已生成的数据会保留"
                  onConfirm={() => abortMutation.mutate()}
                >
                  <Button
                    danger
                    icon={<StopOutlined />}
                    loading={abortMutation.isPending}
                    block
                  >
                    中止任务
                  </Button>
                </Popconfirm>
              )}
              {task.status === 'succeeded' && (
                <Button
                  type="primary"
                  icon={<DownloadOutlined />}
                  onClick={() => downloadTask(task.id)}
                  block
                >
                  下载结果
                </Button>
              )}
              <Popconfirm
                title="确认删除任务？"
                description="删除后不可恢复，输出文件也会一并删除"
                onConfirm={() => deleteMutation.mutate()}
              >
                <Button
                  danger
                  icon={<DeleteOutlined />}
                  loading={deleteMutation.isPending}
                  block
                >
                  删除任务
                </Button>
              </Popconfirm>
            </div>
          </Card>
        </div>

        {/* Right: tabs */}
        <Card
          size="small"
          styles={{ body: { padding: 0 } }}
          style={{ minHeight: 480 }}
        >
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            tabBarStyle={{ padding: '0 16px', margin: 0 }}
            items={[
              {
                key: 'events',
                label: (
                  <span>
                    <HistoryOutlined style={{ marginRight: 6 }} />
                    事件记录
                    {task.recent_events.length > 0 && (
                      <span
                        style={{
                          marginLeft: 6,
                          fontSize: 11,
                          color: '#94a3b8',
                          fontWeight: 500,
                        }}
                      >
                        ({task.recent_events.length})
                      </span>
                    )}
                  </span>
                ),
                children: (
                  <div style={{ padding: 20 }}>
                    <TaskEventTimeline events={task.recent_events} />
                  </div>
                ),
              },
              {
                key: 'preview',
                label: (
                  <span>
                    <DatabaseOutlined style={{ marginRight: 6 }} />
                    数据预览
                  </span>
                ),
                children: (
                  <div style={{ padding: 16 }}>
                    <TaskPreview taskId={task.id} />
                  </div>
                ),
              },
              {
                key: 'log',
                label: (
                  <span>
                    <FileTextOutlined style={{ marginRight: 6 }} />
                    运行日志
                  </span>
                ),
                children: (
                  <div style={{ padding: 16 }}>
                    <TaskLogViewer taskId={task.id} />
                  </div>
                ),
              },
            ]}
          />
        </Card>
      </div>
    </div>
  );
}
