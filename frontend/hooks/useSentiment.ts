import { useQuery } from '@tanstack/react-query';
import { sentimentService } from '@/services/sentimentService';
import { queryKeys } from '@/lib/queryKeys';
import { useAppContext } from '@/context/AppContext';

export function useSentimentOverview() {
  const { marketView, timeWindow } = useAppContext();
  return useQuery(
    queryKeys.sentiment.overview(marketView, timeWindow),
    () => sentimentService.getOverview({ market_view: marketView, time_window: timeWindow }),
    { staleTime: 60 * 1000, keepPreviousData: true }
  );
}
