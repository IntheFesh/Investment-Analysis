import clsx from 'clsx';
import type { ApiMeta } from '@/lib/apiTypes';
import { formatTimestamp } from '@/utils/format';

interface DataSourceBadgeProps {
  meta?: ApiMeta;
  className?: string;
  compact?: boolean;
}

const ADAPTER_LABEL: Record<string, string> = {
  'demo-snapshot': '演示快照',
  yfinance: 'yfinance 实时',
  'yfinance-fallback-demo': 'yfinance 回退（演示）',
  akshare: 'akshare 实时',
  tushare: 'tushare 实时',
};

export function DataSourceBadge({ meta, className, compact = false }: DataSourceBadgeProps) {
  if (!meta) {
    return (
      <span className={clsx('inline-flex items-center gap-2 rounded-pill border px-3 py-1 text-caption data-source-demo', className)}>
        <span className="h-1.5 w-1.5 rounded-full bg-warn" />
        数据源未知
      </span>
    );
  }

  const name = (meta.data_source as string) || 'demo-snapshot';
  const label = ADAPTER_LABEL[name] ?? name;
  const isDemo = Boolean(meta.is_demo);
  const fallback = name === 'yfinance-fallback-demo';
  const klass = fallback ? 'data-source-fallback' : isDemo ? 'data-source-demo' : 'data-source-live';
  const asOf = (meta.as_of_trading_day as string) || (meta.as_of as string | undefined);

  return (
    <span
      className={clsx(
        'inline-flex items-center gap-2 rounded-pill border text-caption tabular whitespace-nowrap',
        compact ? 'px-2 py-0.5' : 'px-3 py-1',
        klass,
        className
      )}
      title={`数据源 ${name} · 截止 ${asOf ?? '—'}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      <span>{label}</span>
      {asOf ? (
        <span className="text-text-tertiary">
          · {compact ? (asOf as string).slice(0, 10) : `截止 ${formatTimestamp(asOf, { includeSeconds: false })}`}
        </span>
      ) : null}
    </span>
  );
}
