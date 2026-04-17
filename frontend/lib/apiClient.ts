import axios, { AxiosError } from 'axios';
import { ApiEnvelope, ApiError, ApiMeta, isApiEnvelope } from './apiTypes';

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL?.trim() || 'http://127.0.0.1:8000';

export const apiClient = axios.create({
  baseURL: apiBaseUrl,
  timeout: 10000,
});

const parseAxiosError = (error: AxiosError): ApiError => {
  if (error.code === 'ECONNABORTED') {
    return new ApiError('TIMEOUT', '请求超时，请检查网络或稍后重试');
  }

  if (!error.response) {
    if (error.code === 'ERR_NETWORK') {
      return new ApiError('BACKEND_UNAVAILABLE', '无法连接后端服务，请确认 uvicorn 已启动');
    }
    return new ApiError('NETWORK_ERROR', '网络异常，请检查网络连接');
  }

  const status = error.response.status;
  const body = error.response.data as ApiEnvelope<unknown> | { detail?: ApiEnvelope<unknown> | string } | undefined;
  const envelope = body && typeof body === 'object' && 'detail' in body && body.detail && typeof body.detail === 'object'
    ? (body.detail as ApiEnvelope<unknown>)
    : (body as ApiEnvelope<unknown> | undefined);

  const message = (envelope && typeof envelope.message === 'string' && envelope.message) || undefined;
  const errorCode = envelope && typeof envelope.error_code === 'string' ? envelope.error_code : undefined;

  if (status === 404) {
    return new ApiError('NOT_FOUND', message || '接口不存在（404），请检查前后端路由', status, errorCode);
  }

  if (status >= 500) {
    return new ApiError('SERVER_ERROR', message || '后端服务异常（5xx），请查看后端日志', status, errorCode);
  }

  return new ApiError('UNKNOWN', message || `请求失败（HTTP ${status}）`, status, errorCode);
};

export interface UnwrappedEnvelope<T> {
  data: T;
  meta: ApiMeta;
  message: string;
}

export const unwrapApiEnvelope = <T>(payload: unknown): UnwrappedEnvelope<T> => {
  if (!isApiEnvelope<T>(payload)) {
    throw new ApiError('BAD_RESPONSE', '接口返回结构异常，请检查后端响应格式');
  }
  const env = payload as ApiEnvelope<T>;
  if (!env.success) {
    throw new ApiError(
      'UNKNOWN',
      env.message || '后端返回 success=false',
      undefined,
      env.error_code
    );
  }
  return { data: env.data, meta: env.meta ?? {}, message: env.message };
};

export const unwrapApiData = <T>(payload: unknown): T =>
  unwrapApiEnvelope<T>(payload).data;

apiClient.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (axios.isAxiosError(error)) {
      return Promise.reject(parseAxiosError(error));
    }

    return Promise.reject(new ApiError('UNKNOWN', '未知错误'));
  }
);

export { apiBaseUrl };
