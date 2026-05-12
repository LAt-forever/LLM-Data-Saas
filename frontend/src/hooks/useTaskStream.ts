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
      void JSON.parse(e.data);
      if (e.lastEventId) {
        lastIdRef.current = parseInt(e.lastEventId, 10);
      }
      queryClient.invalidateQueries({ queryKey: ['task', taskId] });
    });

    es.addEventListener('finished', (e: MessageEvent) => {
      void JSON.parse(e.data);
      if (e.lastEventId) {
        lastIdRef.current = parseInt(e.lastEventId, 10);
      }
      queryClient.invalidateQueries({ queryKey: ['task', taskId] });
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
