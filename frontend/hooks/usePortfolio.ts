import { useQuery } from '@tanstack/react-query';
import { portfolioService } from '@/services/portfolioService';
import { queryKeys } from '@/lib/queryKeys';
import { useAppContext } from '@/context/AppContext';

export function usePortfolioOverview() {
  const { portfolioId } = useAppContext();
  return useQuery(
    queryKeys.portfolio.overview(portfolioId),
    () => portfolioService.getOverview(portfolioId),
    { staleTime: 60 * 1000, keepPreviousData: true, enabled: Boolean(portfolioId) },
  );
}

export function usePortfolioDiagnosis() {
  const { portfolioId, marketView } = useAppContext();
  return useQuery(
    queryKeys.portfolio.diagnosis(portfolioId, marketView),
    () => portfolioService.getDiagnosis(portfolioId, marketView),
    { staleTime: 60 * 1000, keepPreviousData: true, enabled: Boolean(portfolioId) },
  );
}

export function usePortfolioExportPack() {
  const { portfolioId, marketView } = useAppContext();
  return useQuery(
    queryKeys.portfolio.exportPack(portfolioId, marketView),
    () => portfolioService.getExportPack(portfolioId, marketView),
    { staleTime: 5 * 60 * 1000, enabled: Boolean(portfolioId) },
  );
}
