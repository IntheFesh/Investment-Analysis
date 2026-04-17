import { apiClient, unwrapApiEnvelope, type UnwrappedEnvelope } from '@/lib/apiClient';
import type { MarketOverview } from './types';

export interface MarketQuery {
  market_view: string;
  time_window: string;
}

export const marketService = {
  async getOverview(params: MarketQuery, signal?: AbortSignal): Promise<UnwrappedEnvelope<MarketOverview>> {
    const res = await apiClient.get('/api/v1/market/overview', { params, signal });
    return unwrapApiEnvelope<MarketOverview>(res.data);
  },
};
