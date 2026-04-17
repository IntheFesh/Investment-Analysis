import { ReactNode } from 'react';
import clsx from 'clsx';
import { ApiError } from '@/lib/apiTypes';
import { Button } from './Button';

interface ErrorStateProps {
  error: unknown;
  title?: string;
  onRetry?: () => void;
  action?: ReactNode;
  className?: string;
}

const DIAGNOSIS: Record<string, string> = {
  BACKEND_UNAVAILABLE: '后端服务未启动。请运行 `uvicorn backend.app:app --reload` 后重试。',
  TIMEOUT: '请求超时，可能网络不稳定或后端处理耗时过长。',
  NOT_FOUND: '接口不存在。请确认前后端版本一致或路由未变更。',
  SERVER_ERROR: '后端返回 5xx。请查看 uvicorn 日志定位堆栈。',
  NETWORK_ERROR: '网络异常。请检查代理 / 防火墙配置。',
  BAD_RESPONSE: '接口返回结构异常。请检查后端 envelope 是否符合 {success,message,data,meta}。',
  TASK_FAILED: '异步任务执行失败，请在任务详情处查看具体错误。',
};

export function ErrorState({ error, title, onRetry, action, className }: ErrorStateProps) {
  const isApi = error instanceof ApiError;
  const heading = title ?? (isApi ? `请求失败 · ${error.type}` : '加载失败');
  const message = error instanceof Error ? error.message : String(error ?? '未知错误');
  const hint = isApi ? DIAGNOSIS[error.type] : undefined;
  const code = isApi && error.errorCode ? error.errorCode : null;

  return (
    <div
      className={clsx(
        'flex flex-col items-start gap-2 rounded-card border border-danger-muted bg-danger-soft p-4',
        className
      )}
    >
      <div className="flex items-center gap-2 text-heading-sm text-danger">
        <svg width="18" height="18" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6">
          <circle cx="10" cy="10" r="8" />
          <path d="M10 6v4" strokeLinecap="round" />
          <circle cx="10" cy="13.5" r="0.8" fill="currentColor" stroke="none" />
        </svg>
        {heading}
      </div>
      <div className="text-body-sm text-text-primary">{message}</div>
      {hint ? <div className="text-caption text-text-secondary">{hint}</div> : null}
      {code ? (
        <div className="text-micro text-text-tertiary font-mono uppercase tracking-wider">error_code · {code}</div>
      ) : null}
      <div className="flex gap-2 mt-1">
        {onRetry ? (
          <Button variant="secondary" size="sm" onClick={onRetry}>
            重试
          </Button>
        ) : null}
        {action}
      </div>
    </div>
  );
}
