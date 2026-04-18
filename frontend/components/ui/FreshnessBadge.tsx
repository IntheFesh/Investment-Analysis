import clsx from 'clsx';
import type { ApiMeta, EnvelopeStatus } from '@/lib/apiTypes';

interface FreshnessBadgeProps {
  meta?: ApiMeta;
  /** When the envelope ships ``status`` at the top level, pass it through so
   *  the badge prefers it over ad-hoc meta inference. */
  status?: EnvelopeStatus;
  className?: string;
  compact?: boolean;
}

interface Tone {
  label: string;
  dot: string;
  ring: string;
  text: string;
}

const TONES: Record<EnvelopeStatus, Tone> = {
  success: {
    label: '实时',
    dot: 'bg-success',
    ring: 'border-success/40 bg-success/5',
    text: 'text-success',
  },
  partial: {
    label: '部分',
    dot: 'bg-info',
    ring: 'border-info/40 bg-info/5',
    text: 'text-info',
  },
  degraded: {
    label: '降级',
    dot: 'bg-warn',
    ring: 'border-warn/40 bg-warn/10',
    text: 'text-warn',
  },
  failed: {
    label: '失败',
    dot: 'bg-danger',
    ring: 'border-danger/50 bg-danger/10',
    text: 'text-danger',
  },
};

function inferStatus(meta?: ApiMeta): EnvelopeStatus {
  if (!meta) return 'degraded';
  if (meta.is_demo || meta.source_tier === 'fallback_demo') return 'degraded';
  if (meta.fallback_used || meta.fallback_reason) return 'degraded';
  if (meta.is_stale) return 'degraded';
  if (meta.partial) return 'partial';
  return 'success';
}

function ageLabel(age?: number | null): string | null {
  if (age == null || Number.isNaN(age)) return null;
  if (age < 60) return `${Math.round(age)}s`;
  if (age < 3600) return `${Math.round(age / 60)}m`;
  return `${Math.round(age / 3600)}h`;
}

/**
 * Small badge that summarises the honesty contract of the data the user is
 * looking at. Placed next to every key number in Round-0 pages.
 */
export function FreshnessBadge({ meta, status, className, compact = false }: FreshnessBadgeProps) {
  const resolved = status ?? inferStatus(meta);
  const tone = TONES[resolved];
  const age = ageLabel(meta?.age_seconds ?? null);
  const delay = meta?.delay_seconds;
  const reason = meta?.degraded_reason ?? meta?.fallback_reason ?? null;

  const detail = resolved === 'success'
    ? delay && delay > 0 ? `延迟 ${delay >= 900 ? `${Math.round(delay / 60)}m` : `${delay}s`}` : '直取'
    : resolved === 'partial'
    ? '部分因子缺失'
    : resolved === 'degraded'
    ? age ? `缓存 ${age}` : '回退'
    : '无数据';

  const tooltip = [
    `状态 ${tone.label}`,
    meta?.source_vendor ? `来源 ${meta.source_vendor}` : meta?.source_name ? `来源 ${meta.source_name}` : null,
    meta?.as_of ? `截止 ${meta.as_of}` : null,
    reason ? `原因 ${reason}` : null,
    meta?.latency_ms != null ? `延迟 ${meta.latency_ms}ms` : null,
    meta?.trace_id ? `trace ${meta.trace_id}` : null,
  ]
    .filter(Boolean)
    .join(' · ');

  return (
    <span
      title={tooltip}
      className={clsx(
        'inline-flex items-center gap-1.5 rounded-pill border text-caption whitespace-nowrap',
        compact ? 'px-2 py-0.5' : 'px-2.5 py-1',
        tone.ring,
        tone.text,
        className,
      )}
    >
      <span className={clsx('h-1.5 w-1.5 rounded-full', tone.dot)} />
      <span className="font-medium">{tone.label}</span>
      {!compact ? <span className="text-text-tertiary">· {detail}</span> : null}
    </span>
  );
}
