import { apiClient, unwrapApiData } from '@/lib/apiClient';

export const importService = {
  async confirm(payload: { funds: any[]; total_cost: number }) {
    const res = await apiClient.post('/api/v1/import/confirm', payload);
    return unwrapApiData<{ portfolio_id: string }>(res.data);
  },
  async parseScreenshot(images: string[]) {
    const res = await apiClient.post('/api/v1/import/screenshot', { images });
    return unwrapApiData(res.data);
  },
  async parseCsv(csvData: string) {
    const res = await apiClient.post('/api/v1/import/csv', { csv_data: csvData });
    return unwrapApiData(res.data);
  },
};
