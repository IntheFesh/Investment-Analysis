import { apiClient, unwrapApiEnvelope, type UnwrappedEnvelope } from '@/lib/apiClient';
import type { FundAnalysis, FundOverview } from './types';

export interface FundListItem {
  code: string;
  name: string;
  type: string;
  manager: string;
}

export const fundService = {
  async list(): Promise<UnwrappedEnvelope<FundListItem[]>> {
    const res = await apiClient.get('/api/v1/fund/');
    return unwrapApiEnvelope<FundListItem[]>(res.data);
  },
  async getOverview(code: string): Promise<UnwrappedEnvelope<FundOverview>> {
    const res = await apiClient.get(`/api/v1/fund/${code}/overview`);
    return unwrapApiEnvelope<FundOverview>(res.data);
  },
  async getAnalysis(code: string, portfolioId: string): Promise<UnwrappedEnvelope<FundAnalysis>> {
    const res = await apiClient.get(`/api/v1/fund/${code}/analysis`, {
      params: { portfolio_id: portfolioId },
    });
    return unwrapApiEnvelope<FundAnalysis>(res.data);
  },
};
