/** Shared response types used across multiple services. */

export interface IndexRow {
  symbol: string;
  name: string;
  last: number;
  change: number;
  change_percent: number;
  turnover: number;
  trend: number[];
  as_of: string;
}

export interface SectorItem {
  sector: string;
  score: number;
  note?: string;
}

export interface FlowItem {
  sector: string;
  value: number;
  note?: string;
}

export interface SectorRotation {
  strongest: SectorItem[];
  candidate: SectorItem[];
  high_crowding: SectorItem[];
}

export interface FundFlows {
  top_inflows: FlowItem[];
  top_outflows: FlowItem[];
  view: string;
}

export interface BreadthStats {
  advancers_ratio: number;
  limit_up: number;
  limit_down: number;
  turnover_change: number;
  market_heat: number;
}

import type { Evidence } from '@/components/ui/EvidencePanel';

export interface Explanation {
  id: string;
  fact: string;
  inference: string;
  risk: string;
  evidence: Evidence;
  tag: string;
}

export interface MarketOverview {
  market_view: string;
  time_window: string;
  indices: IndexRow[];
  signals: {
    sector_rotation: SectorRotation;
    fund_flows: FundFlows;
    breadth: BreadthStats;
  };
  explanations: Explanation[];
  summary: string;
}

export interface SentimentFactor {
  id: string;
  name: string;
  short_score: number;
  mid_score: number;
  direction: 'up' | 'down';
  driver: string;
  indicators: Record<string, unknown>;
  indicators_mid?: Record<string, unknown>;
  evidence: Evidence;
}

export interface SentimentTimePoint {
  date: string;
  short: number;
  mid: number;
}

export interface SentimentContribution {
  name: string;
  weight: number;
  score: number;
}

export interface SentimentOverview {
  market_view: string;
  universe_id?: string;
  universe_label?: string;
  time_window: string;
  short_term_score: number;
  mid_term_score: number;
  short_term_label: string;
  mid_term_label: string;
  short_term_state?: string;
  mid_term_state?: string;
  state_transition?: Record<string, unknown>;
  short_term_drivers: string[];
  mid_term_drivers: string[];
  factors: SentimentFactor[];
  time_series: SentimentTimePoint[];
  contributions: SentimentContribution[];
  stress_parameters?: Record<string, unknown>;
  method_version?: string;
}

export interface PortfolioSummary {
  total_assets: number;
  total_cost: number;
  profit_loss: number;
  return_percent: number;
  volatility: number;
  max_drawdown: number;
  fund_count: number;
}

export interface PortfolioHolding {
  code: string;
  name: string;
  type: string;
  weight: number;
  manager: string;
}

export interface PortfolioOverlap {
  funds: string[];
  matrix: number[][];
}

export interface PortfolioTargetDeviation {
  risk_profile: string;
  recommended_risk_range: [number, number];
  actual_risk: number;
  deviation: number;
}

export interface PortfolioOverview {
  portfolio_id: string;
  summary: PortfolioSummary;
  holdings: PortfolioHolding[];
  exposures: {
    industry: Record<string, number>;
    style: Record<string, number>;
    market: Record<string, number>;
  };
  overlap: PortfolioOverlap;
  target_deviation: PortfolioTargetDeviation;
}

export interface PortfolioRiskWarning {
  kind: string;
  severity?: string;
  message: string;
  evidence?: Evidence;
}

export interface PortfolioAdjustment {
  action: string;
  expected_effect: string;
  preconditions: string;
  side_effects: string;
  evidence?: Evidence;
}

export interface PortfolioDiagnosis {
  portfolio_id: string;
  risk_profile: {
    risk_type: string;
    risk_type_label?: string;
    investment_horizon: string;
    investment_horizon_label?: string;
    target_vol_range?: [number, number];
    drawdown_tolerance?: number | null;
    liquidity_preference?: string | null;
    return_expectation?: number | null;
  };
  risk_warnings: PortfolioRiskWarning[];
  environment_fit: {
    tone: string;
    message: string;
    sentiment_short_score?: number | null;
    sentiment_short_state?: string | null;
  };
  attribution?: unknown;
  adjustments?: PortfolioAdjustment[];
  optimization: string[];
  evidence: Record<string, string>;
  method_version?: string;
}

export interface PortfolioExportPack {
  portfolio_id: string;
  formats: {
    json: unknown;
    markdown: string;
    csv: string;
  };
  recommendation_prompt: string;
}

export interface FundOverview {
  code: string;
  name: string;
  type: string;
  manager: string;
  aum: number;
  inception_date: string;
  returns: Record<string, number>;
  proxy_index: string;
}

export interface FundAnalysis {
  code: string;
  nav_curve: Array<{ date: string; nav: number }>;
  drawdown_curve: Array<{ date: string; drawdown: number }>;
  metrics: {
    volatility: number;
    max_drawdown: number;
    benchmark_deviation: number;
    rolling_rank: Record<string, number>;
  };
  exposures: {
    industry: Record<string, number>;
    style: Record<string, number>;
    style_drift_flag: string;
  };
  top_holdings: Array<{ ticker: string; name: string; weight: number }>;
  portfolio_relation: {
    portfolio_id: string;
    overlap_score: number;
    correlation: number;
    if_added: string;
    if_removed: string;
  };
  conclusion: {
    suitable_scenarios: string;
    advantages: string;
    risks: string;
  };
}

export type TaskState = 'pending' | 'running' | 'succeeded' | 'failed';

export interface TaskRecord {
  id: string;
  kind: string;
  state: TaskState;
  progress: number;
  message: string;
  result: unknown;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface StatisticalSimulationResult {
  mode: 'statistical';
  portfolio_id: string;
  horizons: number[];
  heatmap: Record<string, Record<string, number>>;
  extreme_curve: Array<{
    horizon: number;
    best_return: number;
    worst_return: number;
    median: number;
  }>;
  sensitivity: Array<{
    factor: string;
    expected_change: number;
    loss_risk: number;
    affected_exposure: string;
  }>;
  max_drawdown: number;
  confidence_interval: number;
  num_paths: number;
  bootstrap: boolean;
}

export interface ScenarioSimulationResult {
  mode: 'scenario';
  portfolio_id: string;
  scenarios: Array<{
    scenario_id: string;
    label: string;
    expected_return: number;
    worst_return: number;
    max_exposure_factor: [string, number];
  }>;
  heatmap: Record<string, Record<string, number>>;
  presets: Array<{ id: string; label: string }>;
}

export interface HistoricalSimulationResult {
  mode: 'historical';
  portfolio_id: string;
  event_id: string;
  event_label: string;
  description?: string;
  path: Array<{ date: string; return: number; cum_return: number }>;
  total_return?: number;
  max_drawdown?: number;
  stress_adjusted_worst?: number;
  stress_parameters?: Record<string, unknown> | null;
}

export type SimulationResult =
  | StatisticalSimulationResult
  | ScenarioSimulationResult
  | HistoricalSimulationResult;

export interface ExportTaskResult {
  page: string;
  portfolio_id: string | null;
  formats: string[];
  preview: unknown;
  download_link: string;
}

export interface OcrPreviewRow {
  code: string;
  name: string;
  shares: number;
  market_value: number;
  confidence: number;
}

export interface ImportPreview {
  preview: unknown;
  needs_review: boolean;
  source: string;
  rejected?: string[];
}
