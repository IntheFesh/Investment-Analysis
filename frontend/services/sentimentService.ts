import { apiClient, unwrapApiEnvelope, type UnwrappedEnvelope } from '@/lib/apiClient';
import type { SentimentOverview } from './types';

export interface SentimentQuery {
  market_view: string;
  time_window: string;
}

export interface SentimentSnapshotLight {
  short_term_score: number;
  short_term_state: string;
  short_term_label: string;
  mid_term_score: number;
  mid_term_state: string;
  mid_term_label: string;
  stress_parameters: Record<string, unknown>;
  computed_at: string | null;
}

export const sentimentService = {
  async getOverview(params: SentimentQuery): Promise<UnwrappedEnvelope<SentimentOverview>> {
    const res = await apiClient.get('/api/v1/sentiment/overview', { params });
    return unwrapApiEnvelope<SentimentOverview>(res.data);
  },
  async getSnapshotLight(marketView: string): Promise<UnwrappedEnvelope<SentimentSnapshotLight>> {
    const res = await apiClient.get('/api/v1/sentiment/snapshot-light', {
      params: { market_view: marketView },
    });
    return unwrapApiEnvelope<SentimentSnapshotLight>(res.data);
  },
};
