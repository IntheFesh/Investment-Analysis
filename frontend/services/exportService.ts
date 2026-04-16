import { apiClient, unwrapApiData } from '@/lib/apiClient';

export const exportService = {
  async exportPage(payload: { page: string; portfolio_id: string | null; formats: string[] }) {
    const res = await apiClient.post('/api/v1/export/page', payload);
    return unwrapApiData<{ download_link: string }>(res.data);
  },
};
