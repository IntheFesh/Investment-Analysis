import { apiClient, unwrapApiData } from '@/lib/apiClient';

export const portfolioService = {
  async getOverview(portfolioId: string) {
    const res = await apiClient.get(`/api/v1/portfolio/${portfolioId}/overview`);
    return unwrapApiData(res.data);
  },
  async getDiagnosis(portfolioId: string) {
    const res = await apiClient.get(`/api/v1/portfolio/${portfolioId}/diagnosis`);
    return unwrapApiData(res.data);
  },
  async getExportPack(portfolioId: string) {
    const res = await apiClient.get(`/api/v1/portfolio/${portfolioId}/export-pack`);
    return unwrapApiData(res.data);
  },
};
