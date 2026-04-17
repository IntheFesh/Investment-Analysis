import { apiClient, unwrapApiEnvelope, type UnwrappedEnvelope } from '@/lib/apiClient';

export interface StatisticalSimulationInput {
  mode: 'statistical';
  portfolio_id: string;
  horizon_days: number;
  num_paths: number;
  confidence_interval: number;
  bootstrap: boolean;
}

export interface ScenarioSimulationInput {
  mode: 'scenario';
  portfolio_id: string;
  scenario_ids: string[];
}

export type SimulationInput = StatisticalSimulationInput | ScenarioSimulationInput;

export const simulationService = {
  async run(payload: SimulationInput): Promise<UnwrappedEnvelope<{ task_id: string }>> {
    const res = await apiClient.post('/api/v1/simulation/run', payload);
    return unwrapApiEnvelope<{ task_id: string }>(res.data);
  },
  async listPresets(): Promise<UnwrappedEnvelope<Array<{ id: string; label: string }>>> {
    const res = await apiClient.get('/api/v1/simulation/presets');
    return unwrapApiEnvelope<Array<{ id: string; label: string }>>(res.data);
  },
};
