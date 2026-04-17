import { apiClient, unwrapApiData } from '@/lib/apiClient';

export interface MarketOption {
  id: string;
  label: string;
}

export interface ResearchModeOption {
  id: string;
  label: string;
  density: string;
}

export interface ThemeOption {
  id: string;
  label: string;
}

export interface PortfolioOption {
  id: string;
  label: string;
  is_default: boolean;
}

export interface FundSummary {
  code: string;
  name: string;
  type: string;
}

export interface ScenarioPreset {
  id: string;
  label: string;
}

export interface BootstrapData {
  markets: MarketOption[];
  time_windows: string[];
  research_modes: ResearchModeOption[];
  themes: ThemeOption[];
  portfolios: PortfolioOption[];
  default_settings: {
    market_view: string;
    time_window: string;
    research_mode: string;
    theme: string;
    default_export_format: string[];
  };
  funds: FundSummary[];
  scenario_presets: ScenarioPreset[];
}

export const systemService = {
  async getBootstrap(): Promise<BootstrapData> {
    const res = await apiClient.get('/api/v1/system/bootstrap');
    return unwrapApiData<BootstrapData>(res.data);
  },
  async getHealth(): Promise<{ status: string }> {
    const res = await apiClient.get('/api/v1/system/health');
    return unwrapApiData<{ status: string }>(res.data);
  },
};
