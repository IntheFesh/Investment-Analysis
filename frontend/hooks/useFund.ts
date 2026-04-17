import { useQuery } from '@tanstack/react-query';
import { fundService } from '@/services/fundService';
import { queryKeys } from '@/lib/queryKeys';
import { useAppContext } from '@/context/AppContext';

export function useFundList() {
  return useQuery(queryKeys.fund.list(), fundService.list, {
    staleTime: 10 * 60 * 1000,
  });
}

export function useFundOverview(code: string, timeWindow: string = '20D') {
  return useQuery(
    queryKeys.fund.overview(code, timeWindow),
    () => fundService.getOverview(code),
    { enabled: Boolean(code), staleTime: 60 * 1000 },
  );
}

export function useFundAnalysis(code: string, timeWindow: string = '20D') {
  const { portfolioId } = useAppContext();
  return useQuery(
    queryKeys.fund.analysis(code, portfolioId, timeWindow),
    () => fundService.getAnalysis(code, portfolioId),
    { enabled: Boolean(code), staleTime: 60 * 1000 },
  );
}
