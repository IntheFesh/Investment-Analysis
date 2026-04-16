import { apiClient, unwrapApiData } from '@/lib/apiClient';

export interface BootstrapData {
  market_views: string[];
  time_windows: string[];
  research_modes: string[];
  portfolios: string[];
  default_settings: {
    market_view: string;
    time_window: string;
    research_mode: string;
    default_export_format: string[];
  };
}

export const systemService = {
  async getBootstrap(): Promise<BootstrapData> {
    const res = await apiClient.get('/api/v1/system/bootstrap');
    return unwrapApiData<BootstrapData>(res.data);
  },
};
