import clsx from 'clsx';
import type { ApiMeta } from '@/lib/apiTypes';
import { formatTimestamp } from '@/utils/format';

interface SourceFootnoteProps {
  meta?: ApiMeta;
  /** Override default disclaimer copy for pages with a stricter tone. */
  disclaimer?: string;
  className?: string;
}

const DEFAULT_DISCLAIMER = '仅供研究教学使用，不构成投资建议';

const VENDOR_LABEL: Record<string, string> = {
  eastmoney: '东方财富公开接口',
  tencent: '腾讯证券公开接口',
  yahoo: 'Yahoo Finance 研究接口',
  akshare: 'AkShare 开源数据',
  tushare: 'Tushare 开源数据',
  'demo-snapshot': '确定性演示快照',
  'hybrid-research': '研究级行情源',
  'yfinance-research': 'Yahoo 研究接口',
};

function labelForVendor(vendor?: string | null): string {
  if (!vendor) return '未识别来源';
  return VENDOR_LABEL[vendor] ?? vendor;
}

function delayCopy(seconds?: number): string {
  if (!seconds || seconds <= 0) return '直取';
  if (seconds >= 3600) return `延迟约 ${Math.round(seconds / 3600)} 小时`;
  if (seconds >= 60) return `延迟约 ${Math.round(seconds / 60)} 分钟`;
  return `延迟约 ${seconds} 秒`;
}

/**
 * Small grey line that sits under every data card: tells the user exactly
 * which vendor is behind the number, how fresh it is, and reminds them
 * this is research-only data. Round-0 requires every page to show this.
 */
export function SourceFootnote({ meta, disclaimer, className }: SourceFootnoteProps) {
  if (!meta) {
    return (
      <p className={clsx('text-caption text-text-tertiary', className)}>
        {disclaimer ?? DEFAULT_DISCLAIMER}
      </p>
    );
  }
  const vendor = (meta.source_vendor as string | undefined) ?? meta.source_name;
  const delay = delayCopy(meta.delay_seconds);
  const asOf = meta.as_of ?? meta.computed_at ?? meta.trading_day;
  const asOfLabel = asOf ? formatTimestamp(asOf, { includeSeconds: false }) : null;
  const trace = meta.trace_id;
  const fallback = meta.fallback_used || meta.is_stale;

  return (
    <p className={clsx('text-caption text-text-tertiary', className)}>
      数据来源：{labelForVendor(vendor)}
      <span className="mx-1 text-border">·</span>
      {delay}
      {asOfLabel ? (
        <>
          <span className="mx-1 text-border">·</span>
          截止 {asOfLabel}
        </>
      ) : null}
      {fallback ? (
        <>
          <span className="mx-1 text-border">·</span>
          <span className="text-warn">缓存回退</span>
        </>
      ) : null}
      <span className="mx-1 text-border">·</span>
      {disclaimer ?? DEFAULT_DISCLAIMER}
      {trace ? <span className="ml-2 opacity-60">trace={trace.slice(0, 8)}</span> : null}
    </p>
  );
}
