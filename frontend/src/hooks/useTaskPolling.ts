import { useQuery } from '@tanstack/react-query';
import { listTasks } from '../api/tasks';

export function useTaskPolling(enabled: boolean) {
  return useQuery({
    queryKey: ['tasks-running'],
    queryFn: () => listTasks({ status: 'running', size: 200 }),
    refetchInterval: enabled ? 3000 : false,
    refetchIntervalInBackground: true,
    enabled,
  });
}
