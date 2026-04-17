import {
  apiClient,
  unwrapApiEnvelope,
  withRequestConfig,
  type UnwrappedEnvelope,
} from '@/lib/apiClient';
import type { MarketOverview } from './types';

export interface MarketQuery {
  market_view: string;
  time_window: string;
}

export interface MarketRequestOptions {
  signal?: AbortSignal;
}

// Market endpoints are served from the backend's hot snapshot cache with
// a ~3 s internal deadline. A 6 s client-side timeout is more than enough
// and prevents the old 15 s stalls on view/window switches.
const MARKET_TIMEOUT_MS = 6000;

export const marketService = {
  async getOverview(
    params: MarketQuery,
    options: MarketRequestOptions = {},
  ): Promise<UnwrappedEnvelope<MarketOverview>> {
    const res = await apiClient.get(
      '/api/v1/market/overview',
      withRequestConfig({
        params: params as unknown as Record<string, unknown>,
        signal: options.signal,
        timeout: MARKET_TIMEOUT_MS,
      }),
    );
    return unwrapApiEnvelope<MarketOverview>(res.data);
  },
};
