import { apiClient, unwrapApiData } from '@/lib/apiClient';

export const fundService = {
  async getOverview(code: string) {
    const res = await apiClient.get(`/api/v1/fund/${code}/overview`);
    return unwrapApiData(res.data);
  },
  async getAnalysis(code: string) {
    const res = await apiClient.get(`/api/v1/fund/${code}/analysis`);
    return unwrapApiData(res.data);
  },
};
