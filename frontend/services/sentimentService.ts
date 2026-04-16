import { apiClient, unwrapApiData } from '@/lib/apiClient';

export const sentimentService = {
  async getOverview(params: { market_view: string; time_window: string }) {
    const res = await apiClient.get('/api/v1/sentiment/overview', { params });
    return unwrapApiData(res.data);
  },
};
