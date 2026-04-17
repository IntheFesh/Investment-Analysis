import { useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { marketService } from '@/services/marketService';
import { queryKeys } from '@/lib/queryKeys';
import { useAppContext } from '@/context/AppContext';
import type { MarketOverview } from '@/services/types';
import type { UnwrappedEnvelope } from '@/lib/apiClient';

export function useMarketOverview(timeWindow: string = '20D') {
  const { marketView } = useAppContext();
  const qc = useQueryClient();
  const queryKey = queryKeys.market.overview(marketView, timeWindow);

  useEffect(() => {
    qc.cancelQueries({ queryKey: ['market', 'overview'], exact: false });
  }, [qc, marketView, timeWindow]);

  return useQuery<UnwrappedEnvelope<MarketOverview>>(
    queryKey,
    ({ signal }) => marketService.getOverview({ market_view: marketView, time_window: timeWindow }, signal),
    {
      staleTime: 45 * 1000,
      cacheTime: 10 * 60 * 1000,
      keepPreviousData: true,
      retry: 1,
      retryDelay: 250,
      refetchOnReconnect: false,
      refetchOnWindowFocus: false,
      placeholderData: () => {
        const fallback = qc.getQueryData<UnwrappedEnvelope<MarketOverview>>(queryKeys.market.overview(marketView, '20D'));
        return fallback;
      },
    },
  );
}
