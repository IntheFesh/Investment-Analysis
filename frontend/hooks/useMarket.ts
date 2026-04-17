import { useEffect, useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { marketService } from '@/services/marketService';
import { queryKeys } from '@/lib/queryKeys';
import { useAppContext } from '@/context/AppContext';
import type { MarketOverview } from '@/services/types';
import type { UnwrappedEnvelope } from '@/lib/apiClient';

const WINDOWS = ['5D', '20D', '60D', '120D', 'YTD', '1Y'] as const;
const VIEWS = ['cn_a', 'hk', 'global'] as const;

export function useMarketOverview(timeWindow: string = '20D') {
  const { marketView } = useAppContext();
  const qc = useQueryClient();
  const queryKey = queryKeys.market.overview(marketView, timeWindow);

  const query = useQuery<UnwrappedEnvelope<MarketOverview>>(
    queryKey,
    ({ signal }) => marketService.getOverview({ market_view: marketView, time_window: timeWindow }, signal),
    {
      staleTime: 30 * 1000,
      keepPreviousData: true,
      retry: 2,
      retryDelay: (attempt) => Math.min(2000, 300 * 2 ** attempt),
      refetchOnReconnect: true,
      placeholderData: () => {
        const fallback = qc.getQueryData<UnwrappedEnvelope<MarketOverview>>(queryKeys.market.overview(marketView, '20D'));
        return fallback;
      },
    },
  );

  const neighborWindows = useMemo(
    () => WINDOWS.filter((w) => w !== timeWindow).slice(0, 2),
    [timeWindow],
  );

  useEffect(() => {
    neighborWindows.forEach((w) => {
      qc.prefetchQuery(
        queryKeys.market.overview(marketView, w),
        ({ signal }) => marketService.getOverview({ market_view: marketView, time_window: w }, signal),
        { staleTime: 30 * 1000 },
      );
    });

    VIEWS.filter((v) => v !== marketView)
      .slice(0, 2)
      .forEach((v) => {
        qc.prefetchQuery(
          queryKeys.market.overview(v, timeWindow),
          ({ signal }) => marketService.getOverview({ market_view: v, time_window: timeWindow }, signal),
          { staleTime: 30 * 1000 },
        );
      });
  }, [qc, marketView, timeWindow, neighborWindows]);

  return query;
}
