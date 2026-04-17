import { useQuery } from '@tanstack/react-query';
import { marketService } from '@/services/marketService';
import { queryKeys } from '@/lib/queryKeys';
import { useAppContext } from '@/context/AppContext';

export function useMarketOverview(timeWindow: string = '20D') {
  const { marketView } = useAppContext();
  return useQuery(
    queryKeys.market.overview(marketView, timeWindow),
    // React Query v4 passes ``signal`` when ``queries.useErrorBoundary`` /
    // ``abortOnUnmount`` semantics are honoured by the axios signal. We
    // propagate it so switching market_view / time_window cancels the
    // previous in-flight request instead of racing it.
    ({ signal }) =>
      marketService.getOverview(
        { market_view: marketView, time_window: timeWindow },
        { signal },
      ),
    {
      // The backend refreshes the snapshot every 60 s. Matching that here
      // avoids the UI refetching on every tiny re-render while still
      // picking up a fresh snapshot within one minute.
      staleTime: 30 * 1000,
      // Keep the old snapshot on screen while the new one loads so users
      // never see a blank "loading" state when flipping windows.
      keepPreviousData: true,
      // Background refresh in sync with the backend pipeline.
      refetchInterval: 60 * 1000,
      refetchOnWindowFocus: false,
      retry: (failureCount, err: unknown) => {
        // Don't retry user-cancelled requests.
        const msg = err instanceof Error ? err.message : String(err ?? '');
        if (msg.includes('取消')) return false;
        return failureCount < 1;
      },
    },
  );
}
