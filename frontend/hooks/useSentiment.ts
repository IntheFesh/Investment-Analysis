import { useQuery } from '@tanstack/react-query';
import { sentimentService } from '@/services/sentimentService';
import { queryKeys } from '@/lib/queryKeys';
import { useAppContext } from '@/context/AppContext';

export function useSentimentOverview(timeWindow: string = '20D') {
  const { marketView } = useAppContext();
  return useQuery(
    queryKeys.sentiment.overview(marketView, timeWindow),
    () => sentimentService.getOverview({ market_view: marketView, time_window: timeWindow }),
    { staleTime: 60 * 1000, keepPreviousData: true },
  );
}

export function useSentimentSnapshotLight(marketView?: string) {
  const { marketView: contextMarket } = useAppContext();
  const view = marketView ?? contextMarket;
  return useQuery(
    ['sentiment', 'snapshot-light', view],
    () => sentimentService.getSnapshotLight?.(view) ?? Promise.resolve(null),
    { staleTime: 45 * 1000, keepPreviousData: true },
  );
}
