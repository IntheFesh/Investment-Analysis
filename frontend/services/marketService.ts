import { apiClient, unwrapApiEnvelope, type UnwrappedEnvelope } from '@/lib/apiClient';
import type { MarketOverview } from './types';

export interface MarketQuery {
  market_view: string;
  time_window: string;
}

const timeoutSignal = (ms: number): AbortSignal => {
  const ctrl = new AbortController();
  setTimeout(() => ctrl.abort(), ms);
  return ctrl.signal;
};

const mergeSignals = (...signals: Array<AbortSignal | undefined>): AbortSignal | undefined => {
  const valid = signals.filter(Boolean) as AbortSignal[];
  if (valid.length === 0) return undefined;
  const ctrl = new AbortController();
  const onAbort = () => ctrl.abort();
  valid.forEach((s) => {
    if (s.aborted) {
      ctrl.abort();
    } else {
      s.addEventListener('abort', onAbort, { once: true });
    }
  });
  return ctrl.signal;
};

export const marketService = {
  async getOverview(params: MarketQuery, signal?: AbortSignal): Promise<UnwrappedEnvelope<MarketOverview>> {
    const res = await apiClient.get('/api/v1/market/overview', {
      params,
      signal: mergeSignals(signal, timeoutSignal(3000)),
      timeout: 3000,
    });
    return unwrapApiEnvelope<MarketOverview>(res.data);
  },
};
