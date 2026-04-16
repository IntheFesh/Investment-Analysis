import { apiClient, unwrapApiData } from '@/lib/apiClient';

export const simulationService = {
  async run(payload: {
    mode: string;
    horizon_days: number;
    num_paths: number;
    confidence_interval: number;
    bootstrap: boolean;
  }) {
    const res = await apiClient.post('/api/v1/simulation/run', payload);
    return unwrapApiData(res.data);
  },
};
