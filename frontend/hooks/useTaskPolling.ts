import { useEffect, useMemo, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { taskService } from '@/services/taskService';
import { queryKeys } from '@/lib/queryKeys';
import type { TaskRecord } from '@/services/types';

export interface TaskPollingResult {
  task?: TaskRecord;
  loading: boolean;
  error: unknown;
  refetch: () => void;
}

/**
 * Polls an async task until it enters a terminal state. The polling interval
 * is aggressive while `running` and stops as soon as `succeeded` / `failed`.
 */
export function useTaskPolling(taskId?: string | null): TaskPollingResult {
  const qc = useQueryClient();
  const query = useQuery(
    queryKeys.task.detail(taskId ?? undefined),
    () => taskService.get(taskId as string),
    {
      enabled: Boolean(taskId),
      refetchInterval: (data) => {
        if (!data?.data) return 600;
        return data.data.state === 'running' || data.data.state === 'pending' ? 600 : false;
      },
      refetchIntervalInBackground: false,
      staleTime: 0,
    }
  );

  useEffect(() => {
    const state = query.data?.data.state;
    if (state === 'succeeded' || state === 'failed') {
      qc.invalidateQueries(queryKeys.task.list());
    }
  }, [query.data, qc]);

  return {
    task: query.data?.data,
    loading: query.isFetching && !query.data,
    error: query.error,
    refetch: () => query.refetch(),
  };
}

/** Wrapper that tracks an in-flight task id alongside its polling state. */
export function useTaskRunner() {
  const [taskId, setTaskId] = useState<string | null>(null);
  const polling = useTaskPolling(taskId);

  const reset = () => setTaskId(null);
  const start = (id: string) => setTaskId(id);

  const isRunning = useMemo(() => {
    if (!polling.task) return Boolean(taskId);
    return polling.task.state === 'running' || polling.task.state === 'pending';
  }, [polling.task, taskId]);

  return { taskId, start, reset, ...polling, isRunning };
}
