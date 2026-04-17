import { useQuery } from '@tanstack/react-query';
import { portfolioService } from '@/services/portfolioService';
import { queryKeys } from '@/lib/queryKeys';
import { useAppContext } from '@/context/AppContext';

export function usePortfolioOverview() {
  const { portfolioId, timeWindow } = useAppContext();
  return useQuery(
    queryKeys.portfolio.overview(portfolioId, timeWindow),
    () => portfolioService.getOverview(portfolioId),
    { staleTime: 60 * 1000, keepPreviousData: true, enabled: Boolean(portfolioId) }
  );
}

export function usePortfolioDiagnosis() {
  const { portfolioId, timeWindow, marketView } = useAppContext();
  return useQuery(
    queryKeys.portfolio.diagnosis(portfolioId, timeWindow, marketView),
    () => portfolioService.getDiagnosis(portfolioId),
    { staleTime: 60 * 1000, keepPreviousData: true, enabled: Boolean(portfolioId) }
  );
}

export function usePortfolioExportPack() {
  const { portfolioId } = useAppContext();
  return useQuery(
    queryKeys.portfolio.exportPack(portfolioId),
    () => portfolioService.getExportPack(portfolioId),
    { staleTime: 5 * 60 * 1000, enabled: Boolean(portfolioId) }
  );
}
