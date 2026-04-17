import { apiClient, unwrapApiEnvelope, type UnwrappedEnvelope } from '@/lib/apiClient';
import type {
  PortfolioDiagnosis,
  PortfolioExportPack,
  PortfolioOverview,
} from './types';

export const portfolioService = {
  async getOverview(portfolioId: string): Promise<UnwrappedEnvelope<PortfolioOverview>> {
    const res = await apiClient.get(`/api/v1/portfolio/${portfolioId}/overview`);
    return unwrapApiEnvelope<PortfolioOverview>(res.data);
  },
  async getDiagnosis(
    portfolioId: string,
    marketView?: string,
  ): Promise<UnwrappedEnvelope<PortfolioDiagnosis>> {
    const res = await apiClient.get(`/api/v1/portfolio/${portfolioId}/diagnosis`, {
      params: marketView ? { market_view: marketView } : undefined,
    });
    return unwrapApiEnvelope<PortfolioDiagnosis>(res.data);
  },
  async getExportPack(
    portfolioId: string,
    marketView?: string,
  ): Promise<UnwrappedEnvelope<PortfolioExportPack>> {
    const res = await apiClient.get(`/api/v1/portfolio/${portfolioId}/export-pack`, {
      params: marketView ? { market_view: marketView } : undefined,
    });
    return unwrapApiEnvelope<PortfolioExportPack>(res.data);
  },
  async requestExport(
    portfolioId: string,
    formats: string[],
    marketView?: string,
  ): Promise<UnwrappedEnvelope<{ task_id: string }>> {
    const res = await apiClient.post(`/api/v1/portfolio/${portfolioId}/export-pack/run`, {
      formats,
      market_view: marketView,
    });
    return unwrapApiEnvelope<{ task_id: string }>(res.data);
  },
};
