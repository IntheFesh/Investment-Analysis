import { apiClient, unwrapApiEnvelope, type UnwrappedEnvelope } from '@/lib/apiClient';

export interface StatisticalSimulationInput {
  mode: 'statistical';
  portfolio_id: string;
  horizon_days: number;
  num_paths: number;
  confidence_interval: number;
  bootstrap: boolean;
  market_view?: string;
  use_sentiment_stress?: boolean;
}

export interface ScenarioSimulationInput {
  mode: 'scenario';
  portfolio_id: string;
  scenario_ids: string[];
  market_view?: string;
  use_sentiment_stress?: boolean;
}

export interface HistoricalSimulationInput {
  mode: 'historical';
  portfolio_id: string;
  event_id: string;
  market_view?: string;
  use_sentiment_stress?: boolean;
}

export type SimulationInput =
  | StatisticalSimulationInput
  | ScenarioSimulationInput
  | HistoricalSimulationInput;

export interface HistoricalEventOption {
  id: string;
  label: string;
  description?: string;
}

export const simulationService = {
  async run(
    payload: SimulationInput,
  ): Promise<UnwrappedEnvelope<{ task_id: string; watermark?: string }>> {
    const res = await apiClient.post('/api/v1/simulation/run', payload);
    return unwrapApiEnvelope<{ task_id: string; watermark?: string }>(res.data);
  },
  async listPresets(): Promise<
    UnwrappedEnvelope<Array<{ id: string; label: string; factors?: Record<string, unknown> }>>
  > {
    const res = await apiClient.get('/api/v1/simulation/presets');
    return unwrapApiEnvelope<Array<{ id: string; label: string; factors?: Record<string, unknown> }>>(
      res.data,
    );
  },
  async listHistoricalEvents(): Promise<UnwrappedEnvelope<HistoricalEventOption[]>> {
    const res = await apiClient.get('/api/v1/simulation/historical-events');
    return unwrapApiEnvelope<HistoricalEventOption[]>(res.data);
  },
};
