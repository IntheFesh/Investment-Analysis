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

export interface ApiMeta {
  timestamp?: string;
  version?: string;
  data_source?: string;
  is_demo?: boolean;
  as_of_trading_day?: string;
  as_of?: string;
  market_session?: string;
  tz?: string;
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
