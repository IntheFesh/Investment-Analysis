import axios, { AxiosError } from 'axios';
import { ApiEnvelope, ApiError, isApiEnvelope } from './apiTypes';

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
  if (status === 404) {
    return new ApiError('NOT_FOUND', '接口不存在（404），请检查前后端路由');
  }

  if (status >= 500) {
    return new ApiError('SERVER_ERROR', '后端服务异常（5xx），请查看后端日志', status);
  }

  return new ApiError('UNKNOWN', `请求失败（HTTP ${status}）`, status);
};

export const unwrapApiData = <T>(payload: unknown): T => {
  if (!isApiEnvelope<T>(payload)) {
    throw new ApiError('BAD_RESPONSE', '接口返回结构异常，请检查后端响应格式');
  }

  return (payload as ApiEnvelope<T>).data;
};

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
