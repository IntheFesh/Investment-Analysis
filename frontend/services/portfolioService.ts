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
  async getDiagnosis(portfolioId: string): Promise<UnwrappedEnvelope<PortfolioDiagnosis>> {
    const res = await apiClient.get(`/api/v1/portfolio/${portfolioId}/diagnosis`);
    return unwrapApiEnvelope<PortfolioDiagnosis>(res.data);
  },
  async getExportPack(portfolioId: string): Promise<UnwrappedEnvelope<PortfolioExportPack>> {
    const res = await apiClient.get(`/api/v1/portfolio/${portfolioId}/export-pack`);
    return unwrapApiEnvelope<PortfolioExportPack>(res.data);
  },
  async requestExport(
    portfolioId: string,
    formats: string[]
  ): Promise<UnwrappedEnvelope<{ task_id: string }>> {
    const res = await apiClient.post(`/api/v1/portfolio/${portfolioId}/export-pack/run`, {
      formats,
    });
    return unwrapApiEnvelope<{ task_id: string }>(res.data);
  },
};
