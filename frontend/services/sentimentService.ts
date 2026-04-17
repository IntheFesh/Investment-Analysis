import { apiClient, unwrapApiEnvelope, type UnwrappedEnvelope } from '@/lib/apiClient';
import type { SentimentOverview } from './types';

export interface SentimentQuery {
  market_view: string;
  time_window: string;
}

export const sentimentService = {
  async getOverview(params: SentimentQuery): Promise<UnwrappedEnvelope<SentimentOverview>> {
    const res = await apiClient.get('/api/v1/sentiment/overview', { params });
    return unwrapApiEnvelope<SentimentOverview>(res.data);
  },
};
