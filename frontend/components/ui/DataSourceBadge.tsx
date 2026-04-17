import clsx from 'clsx';
import type { ApiMeta, SourceTier, TruthGrade } from '@/lib/apiTypes';
import { formatTimestamp } from '@/utils/format';

interface DataSourceBadgeProps {
  meta?: ApiMeta;
  className?: string;
  compact?: boolean;
}

const SOURCE_LABEL: Record<string, string> = {
  'demo-snapshot': '演示快照',
  'yfinance-research': 'Yahoo 研究接口',
  'yfinance-research-degraded': 'Yahoo 研究（降级）',
  akshare: 'AkShare 研究接口',
  tushare: 'Tushare 研究接口',
};

const TIER_LABEL: Record<SourceTier, string> = {
  production_authorized: '授权实时',
  production_delayed: '授权延迟',
  research_only: '研究源',
  derived: '派生/代理',
  fallback_demo: '演示回退',
};

const GRADE_HUE: Record<TruthGrade, string> = {
  A: 'border-success/40 text-success bg-success/5',
  B: 'border-info/40 text-info bg-info/5',
  C: 'border-warn/40 text-warn bg-warn/5',
  D: 'border-warn/60 text-warn bg-warn/10',
  E: 'border-muted/40 text-text-tertiary bg-surface-raised',
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

  const name = meta.source_name ?? (meta.data_source as string | undefined) ?? 'unknown';
  const label = SOURCE_LABEL[name] ?? name;
  const grade: TruthGrade = (meta.truth_grade as TruthGrade) ?? 'E';
  const tier: SourceTier = (meta.source_tier as SourceTier) ?? 'fallback_demo';
  const isDemo = Boolean(meta.is_demo);
  const isProxy = Boolean(meta.is_proxy);
  const isRealtime = Boolean(meta.is_realtime);
  const delaySeconds = typeof meta.delay_seconds === 'number' ? meta.delay_seconds : 0;
  const fallbackReason = (meta.fallback_reason as string | null | undefined) ?? null;
  const asOf = (meta.trading_day as string | undefined) || (meta.as_of_trading_day as string | undefined) || (meta.computed_at as string | undefined);
  const methodVersion = meta.calculation_method_version as string | undefined;

  const tone = GRADE_HUE[grade] ?? GRADE_HUE.E;
  const timeliness = isRealtime
    ? '实时'
    : delaySeconds >= 900
    ? `延迟 ${Math.round(delaySeconds / 60)}m`
    : delaySeconds > 0
    ? `延迟 ${delaySeconds}s`
    : '快照';

  const tooltipParts = [
    `来源 ${name}`,
    `分级 ${grade} · ${TIER_LABEL[tier]}`,
    asOf ? `截止 ${asOf}` : null,
    methodVersion ? `算法 ${methodVersion}` : null,
    fallbackReason ? `降级原因 ${fallbackReason}` : null,
  ].filter(Boolean) as string[];

  return (
    <span
      className={clsx(
        'inline-flex items-center gap-2 rounded-pill border text-caption tabular whitespace-nowrap',
        compact ? 'px-2 py-0.5' : 'px-3 py-1',
        tone,
        className,
      )}
      title={tooltipParts.join(' · ')}
    >
      <span className={clsx('inline-flex items-center justify-center rounded-sm px-1 font-mono text-[10px] font-semibold', 'bg-current/10')}>
        {grade}
      </span>
      <span className="font-medium">{label}</span>
      {!compact && <span className="text-text-tertiary">· {TIER_LABEL[tier]}</span>}
      <span className="text-text-tertiary">· {timeliness}</span>
      {isProxy ? <span className="text-warn">· 代理</span> : null}
      {isDemo ? <span className="text-warn">· 演示</span> : null}
      {fallbackReason ? <span className="text-warn">· 降级</span> : null}
      {asOf ? (
        <span className="text-text-tertiary">· {compact ? asOf.slice(0, 10) : `截止 ${formatTimestamp(asOf, { includeSeconds: false })}`}</span>
      ) : null}
    </span>
  );
}
