import { useQuery } from '@tanstack/react-query';
import { marketService } from '@/services/marketService';
import { queryKeys } from '@/lib/queryKeys';
import { useAppContext } from '@/context/AppContext';

export function useMarketOverview() {
  const { marketView, timeWindow } = useAppContext();
  return useQuery(
    queryKeys.market.overview(marketView, timeWindow),
    () => marketService.getOverview({ market_view: marketView, time_window: timeWindow }),
    {
      staleTime: 60 * 1000,
      keepPreviousData: true,
    }
  );
}
