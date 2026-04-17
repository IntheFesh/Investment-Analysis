import { apiClient, unwrapApiEnvelope, type UnwrappedEnvelope } from '@/lib/apiClient';

export interface RiskProfile {
  risk_type: string;
  investment_horizon: string;
  drawdown_tolerance?: number | null;
  return_expectation?: number | null;
  liquidity_preference?: string | null;
  defensive_ratio?: number | null;
  offensive_ratio?: number | null;
  questionnaire_score?: number | null;
}

export interface Preferences {
  market_view: string;
  research_mode: string;
  theme: string;
  default_export_format: string[];
  include_global_events: boolean;
  include_charts_in_export: boolean;
}

export interface EnumCatalogue {
  risk_types: Array<{
    id: string;
    label_zh: string;
    target_vol: [number, number];
    defensive_ratio: number;
    description?: string;
  }>;
  investment_horizons: Array<{
    id: string;
    label_zh: string;
    drawdown_tolerance: number;
    description?: string;
  }>;
  market_views: string[];
  research_modes: string[];
  themes: string[];
  export_formats: string[];
  liquidity_preferences: string[];
}

export const settingsService = {
  async getProfile(): Promise<UnwrappedEnvelope<RiskProfile>> {
    const res = await apiClient.get('/api/v1/settings/profile');
    return unwrapApiEnvelope<RiskProfile>(res.data);
  },
  async getPreferences(): Promise<UnwrappedEnvelope<Preferences>> {
    const res = await apiClient.get('/api/v1/settings/preferences');
    return unwrapApiEnvelope<Preferences>(res.data);
  },
  async getEnums(): Promise<UnwrappedEnvelope<EnumCatalogue>> {
    const res = await apiClient.get('/api/v1/settings/enums');
    return unwrapApiEnvelope<EnumCatalogue>(res.data);
  },
  async updateProfile(profile: RiskProfile): Promise<UnwrappedEnvelope<RiskProfile>> {
    const res = await apiClient.put('/api/v1/settings/profile', profile);
    return unwrapApiEnvelope<RiskProfile>(res.data);
  },
  async updatePreferences(prefs: Preferences): Promise<UnwrappedEnvelope<Preferences>> {
    const res = await apiClient.put('/api/v1/settings/preferences', prefs);
    return unwrapApiEnvelope<Preferences>(res.data);
  },
};
