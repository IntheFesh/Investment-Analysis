import { apiClient, unwrapApiData } from '@/lib/apiClient';

export interface MarketOption {
  id: string;
  label: string;
  hint?: string;
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
  region?: string;
}

export interface ScenarioPreset {
  id: string;
  label: string;
  factors?: string[];
}

export interface HistoricalEvent {
  id: string;
  label: string;
  description?: string;
}

export interface RiskTypeOption {
  id: string;
  label_zh: string;
  target_vol: [number, number];
  defensive_ratio: number;
  description?: string;
}

export interface HorizonOption {
  id: string;
  label_zh: string;
  drawdown_tolerance: number;
  description?: string;
}

export interface BootstrapEnums {
  risk_types: RiskTypeOption[];
  investment_horizons: HorizonOption[];
  market_views: string[];
  research_modes: string[];
  themes: string[];
  export_formats: string[];
  liquidity_preferences: Array<{ id: string; label_zh: string }>;
}

export interface DataSourceInfo {
  name: string;
  tier: string;
  truth_grade: string;
  license_scope: string;
  delay_seconds: number;
  is_realtime: boolean;
}

export interface BootstrapData {
  markets: MarketOption[];
  research_modes: ResearchModeOption[];
  themes: ThemeOption[];
  portfolios: PortfolioOption[];
  enums: BootstrapEnums;
  default_settings: {
    market_view: string;
    research_mode: string;
    theme: string;
    default_export_format: string[];
  };
  profile: Record<string, unknown>;
  funds: FundSummary[];
  scenario_presets: ScenarioPreset[];
  historical_events: HistoricalEvent[];
  data_source: DataSourceInfo;
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
