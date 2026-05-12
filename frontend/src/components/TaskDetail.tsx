import { Card, Button, Space, Popconfirm } from 'antd';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { abortTask, deleteTask, downloadTask } from '../api/tasks';
import type { TaskDetail as TaskDetailType } from '../api/types';
import { TaskProgress } from './TaskProgress';
import { TaskEventTimeline } from './TaskEventTimeline';
import { SSEStatusBadge } from './SSEStatusBadge';
import { useLocation } from 'wouter';

interface Props {
  task: TaskDetailType;
}

export function TaskDetail({ task }: Props) {
  const [, navigate] = useLocation();
  const queryClient = useQueryClient();

  const abortMutation = useMutation({
    mutationFn: () => abortTask(task.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['task', task.id] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteTask(task.id),
    onSuccess: () => {
      navigate('/');
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  const isTerminal = ['succeeded', 'failed', 'aborted'].includes(task.status);

  return (
    <div>
      <Card
        title={
          <Space>
            <span>任务 #{task.id} - {task.category_name}</span>
            <SSEStatusBadge taskId={task.id} />
          </Space>
        }
        extra={
          <Space>
            {!isTerminal && (
              <Popconfirm
                title="确认中止任务？"
                onConfirm={() => abortMutation.mutate()}
              >
                <Button danger loading={abortMutation.isPending}>
                  中止
                </Button>
              </Popconfirm>
            )}
            {isTerminal && (
              <Button onClick={() => downloadTask(task.id)}>
                下载结果
              </Button>
            )}
            <Popconfirm
              title="确认删除任务？"
              description="删除后不可恢复"
              onConfirm={() => deleteMutation.mutate()}
            >
              <Button danger>删除</Button>
            </Popconfirm>
          </Space>
        }
      >
        <TaskProgress task={task} />
      </Card>

      <Card title="事件记录" style={{ marginTop: 16 }}>
        <TaskEventTimeline events={task.recent_events} />
      </Card>
    </div>
  );
}
