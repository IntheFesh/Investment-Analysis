import { apiClient, unwrapApiEnvelope, type UnwrappedEnvelope } from '@/lib/apiClient';
import type { TaskRecord } from './types';

export interface ExportPayload {
  page: string;
  portfolio_id: string | null;
  formats: string[];
}

export const exportService = {
  async exportPage(payload: ExportPayload): Promise<UnwrappedEnvelope<{ task_id: string }>> {
    const res = await apiClient.post('/api/v1/export/page', payload);
    return unwrapApiEnvelope<{ task_id: string }>(res.data);
  },
  async history(): Promise<UnwrappedEnvelope<TaskRecord[]>> {
    const res = await apiClient.get('/api/v1/export/history');
    return unwrapApiEnvelope<TaskRecord[]>(res.data);
  },
};
