import { useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useAppStore } from '../store/appStore';

export function useTaskStream(taskId: number | undefined) {
  const queryClient = useQueryClient();
  const setSseState = useAppStore((s) => s.setSseState);
  const lastIdRef = useRef(0);

  useEffect(() => {
    if (taskId === undefined) return;

    const es = new EventSource(`/api/tasks/${taskId}/stream`);
    let closedByUs = false;

    es.addEventListener('open', () => {
      setSseState(taskId, 'connected');
    });

    es.addEventListener('event', (e: MessageEvent) => {
      const data = JSON.parse(e.data) as { type: string; message: string; ts: string };
      if (e.lastEventId) {
        lastIdRef.current = parseInt(e.lastEventId, 10);
      }

      // 零延迟更新：progress 事件直接修改缓存
      if (data.type === 'progress') {
        const match = data.message.match(/^(\d+)\/(\d+)$/);
        if (match) {
          queryClient.setQueryData(['task', taskId], (old: any) => {
            if (!old) return old;
            return {
              ...old,
              progress_current: parseInt(match[1], 10),
              progress_total: parseInt(match[2], 10),
            };
          });
        }
      }

      queryClient.invalidateQueries({ queryKey: ['task', taskId] });
      queryClient.invalidateQueries({ queryKey: ['preview', taskId] });
      queryClient.invalidateQueries({ queryKey: ['log', taskId] });
    });

    es.addEventListener('finished', (e: MessageEvent) => {
      void JSON.parse(e.data);
      if (e.lastEventId) {
        lastIdRef.current = parseInt(e.lastEventId, 10);
      }
      queryClient.invalidateQueries({ queryKey: ['task', taskId] });
      queryClient.invalidateQueries({ queryKey: ['preview', taskId] });
      queryClient.invalidateQueries({ queryKey: ['log', taskId] });
      closedByUs = true;
      es.close();
      setSseState(taskId, 'closed');
    });

    es.addEventListener('error', () => {
      if (es.readyState === EventSource.CONNECTING) {
        setSseState(taskId, 'reconnecting');
      }
    });

    return () => {
      closedByUs = true;
      void closedByUs;
      es.close();
    };
  }, [taskId, queryClient, setSseState]);

  return { lastEventId: lastIdRef.current };
}
