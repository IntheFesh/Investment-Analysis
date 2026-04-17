import { apiClient, unwrapApiEnvelope, type UnwrappedEnvelope } from '@/lib/apiClient';
import type { TaskRecord } from './types';

export const taskService = {
  async get(taskId: string): Promise<UnwrappedEnvelope<TaskRecord>> {
    const res = await apiClient.get(`/api/v1/tasks/${taskId}`);
    return unwrapApiEnvelope<TaskRecord>(res.data);
  },
  async list(kind?: string): Promise<UnwrappedEnvelope<TaskRecord[]>> {
    const res = await apiClient.get('/api/v1/tasks/', {
      params: kind ? { kind } : undefined,
    });
    return unwrapApiEnvelope<TaskRecord[]>(res.data);
  },
};
