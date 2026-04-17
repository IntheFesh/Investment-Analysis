import { apiClient, unwrapApiEnvelope, type UnwrappedEnvelope } from '@/lib/apiClient';
import type { ImportPreview } from './types';

export interface FundImportEntry {
  code: string;
  name?: string;
  shares?: number;
  market_value?: number;
  cost?: number;
}

export const importService = {
  async parseCodes(codes: string[]): Promise<UnwrappedEnvelope<ImportPreview>> {
    const res = await apiClient.post('/api/v1/import/codes', { codes });
    return unwrapApiEnvelope<ImportPreview>(res.data);
  },
  async parseScreenshot(images: string[]): Promise<UnwrappedEnvelope<{ task_id: string }>> {
    const res = await apiClient.post('/api/v1/import/screenshot', { images });
    return unwrapApiEnvelope<{ task_id: string }>(res.data);
  },
  async parseCsv(csvData: string, delimiter = ','): Promise<UnwrappedEnvelope<ImportPreview>> {
    const res = await apiClient.post('/api/v1/import/csv', {
      csv_data: csvData,
      delimiter,
    });
    return unwrapApiEnvelope<ImportPreview>(res.data);
  },
  async confirm(payload: {
    funds: FundImportEntry[];
    total_cost: number;
    label?: string;
  }): Promise<UnwrappedEnvelope<{
    portfolio_id: string;
    label: string;
    fund_count: number;
    total_cost: number;
  }>> {
    const res = await apiClient.post('/api/v1/import/confirm', payload);
    return unwrapApiEnvelope<{
      portfolio_id: string;
      label: string;
      fund_count: number;
      total_cost: number;
    }>(res.data);
  },
};
