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

  return useQuery<UnwrappedEnvelope<MarketOverview>>(
    queryKey,
    ({ signal }) => marketService.getOverview({ market_view: marketView, time_window: timeWindow }, signal),
    {
      staleTime: 60 * 1000,
      cacheTime: 10 * 60 * 1000,
      keepPreviousData: true,
      retry: (failureCount, error: unknown) => {
        const code = (error as { code?: string })?.code;
        if (code === 'TIMEOUT' || code === 'BACKEND_UNAVAILABLE' || code === 'NETWORK_ERROR') {
          return failureCount < 2;
        }
        return failureCount < 1;
      },
      retryDelay: (attempt) => Math.min(1500, 400 * 2 ** attempt),
      refetchOnReconnect: false,
      refetchOnWindowFocus: false,
      placeholderData: () => {
        // While switching time windows or market views, show the most recent
        // successful snapshot for the same marketView (any window) so the UI
        // never flashes empty.
        const sameViewAnyWindow = ['20D', '5D', '60D', '120D', 'YTD', '1Y'].reduce<
          UnwrappedEnvelope<MarketOverview> | undefined
        >((acc, w) => {
          if (acc) return acc;
          return qc.getQueryData<UnwrappedEnvelope<MarketOverview>>(
            queryKeys.market.overview(marketView, w),
          );
        }, undefined);
        return sameViewAnyWindow;
      },
    },
  );
}
