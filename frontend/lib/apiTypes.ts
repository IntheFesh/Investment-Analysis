export type ApiErrorType =
  | 'BACKEND_UNAVAILABLE'
  | 'NOT_FOUND'
  | 'TIMEOUT'
  | 'SERVER_ERROR'
  | 'NETWORK_ERROR'
  | 'BAD_RESPONSE'
  | 'TASK_FAILED'
  | 'TASK_TIMEOUT'
  | 'UNKNOWN';

export class ApiError extends Error {
  readonly type: ApiErrorType;
  readonly status?: number;
  readonly errorCode?: string;

  constructor(type: ApiErrorType, message: string, status?: number, errorCode?: string) {
    super(message);
    this.name = 'ApiError';
    this.type = type;
    this.status = status;
    this.errorCode = errorCode;
  }
}

export type TruthGrade = 'A' | 'B' | 'C' | 'D' | 'E';
export type SourceTier =
  | 'production_authorized'
  | 'production_delayed'
  | 'research_only'
  | 'derived'
  | 'fallback_demo';
export type LicenseScope = 'commercial' | 'research_only' | 'internal_preview';
export type MarketSession = 'pre' | 'open' | 'close' | 'after' | 'snapshot';

export interface ApiMeta {
  timestamp?: string;
  version?: string;
  computed_at?: string;

  // truth metadata
  source_name?: string;
  source_tier?: SourceTier;
  truth_grade?: TruthGrade;
  is_demo?: boolean;
  is_proxy?: boolean;
  is_realtime?: boolean;
  delay_seconds?: number;
  license_scope?: LicenseScope;
  fallback_reason?: string | null;
  trading_day?: string | null;
  coverage_universe?: string;
  calculation_method_version?: string;
  evidence_count?: number;
  market_session?: MarketSession;
  tz?: string;

  // legacy aliases
  data_source?: string;
  as_of_trading_day?: string | null;
  as_of?: string;
  [key: string]: unknown;
}

export interface ApiEnvelope<T> {
  success: boolean;
  message: string;
  data: T;
  meta?: ApiMeta;
  error_code?: string;
}

export const isApiEnvelope = <T>(value: unknown): value is ApiEnvelope<T> => {
  if (!value || typeof value !== 'object') {
    return false;
  }

  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.success === 'boolean' &&
    typeof candidate.message === 'string' &&
    'data' in candidate
  );
};
