import { useMemo, useState } from 'react';
import { Card, CardHeader, Metric } from '@/components/ui/Card';
import { Sparkline } from '@/components/charts/Sparkline';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { formatCompact, formatNumber, formatPercent, formatSignedNumber } from '@/utils/format';
import type { IndexRow, MarketOverview } from '@/services/types';

interface IndicesPanelProps {
  indices: IndexRow[];
  topMetrics?: MarketOverview['top_metrics'];
}

function toneClass(value: number) {
  if (value > 0) return 'text-up';
  if (value < 0) return 'text-down';
  return 'text-text-secondary';
}

function qualityTone(label?: string): 'info' | 'warn' | 'neutral' {
  if (label === '实时') return 'info';
  if (label === '回退') return 'warn';
  return 'neutral';
}

function IndexCard({ item, expanded, onToggle }: { item: IndexRow; expanded: boolean; onToggle: () => void }) {
  return (
    <div
      className={`rounded-xl border transition-all duration-standard ${
        expanded ? 'border-brand/60 bg-brand/5' : 'border-border bg-surface-sunken/40 hover:border-border-strong'
      }`}
    >
      <button className="w-full text-left p-4" onClick={onToggle}>
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-body-md font-semibold text-text-primary">{item.name}</div>
            <div className="text-caption text-text-tertiary mt-0.5">{item.code ?? item.symbol}</div>
          </div>
          <div className="text-right">
            <div className="text-title-sm tabular text-text-primary">{formatNumber(item.last)}</div>
            <div className={`text-body-sm tabular ${toneClass(item.change_percent)}`}>
              {formatSignedNumber(item.change)} / {formatPercent(item.change_percent)}
            </div>
          </div>
        </div>

        <div className="mt-3 flex items-center justify-between gap-3">
          <Sparkline data={item.trend ?? []} width="100%" height={36} />
          <div className="min-w-[140px] text-right">
            <div className="text-caption text-text-tertiary">成交额</div>
            <div className="text-body-sm text-text-primary tabular">{formatCompact(item.turnover)}</div>
            <div className="text-micro text-text-tertiary mt-1">{item.as_of}</div>
          </div>
        </div>
      </button>

      {expanded ? (
        <div className="px-4 pb-4 grid grid-cols-1 lg:grid-cols-3 gap-3">
          <div className="rounded-lg border border-border/70 bg-surface-raised/60 p-3">
            <div className="text-caption text-text-tertiary">支撑 / 阻力</div>
            <div className="text-body-md tabular mt-1 text-text-primary">
              {item.support ? formatNumber(item.support) : '--'} / {item.resistance ? formatNumber(item.resistance) : '--'}
            </div>
            <div className="mt-2 text-caption text-text-tertiary">估值分位（PE/PB）</div>
            <div className="text-body-sm mt-1 tabular text-text-secondary">
              {(item.valuation?.pe_percentile ?? 0).toFixed(1)}% / {(item.valuation?.pb_percentile ?? 0).toFixed(1)}%
            </div>
          </div>

          <div className="rounded-lg border border-border/70 bg-surface-raised/60 p-3">
            <div className="text-caption text-text-tertiary">板块贡献</div>
            <div className="mt-2 space-y-1.5">
              {(item.contributors ?? []).map((c) => (
                <div key={c.name} className="flex items-center justify-between text-caption border-b border-border/50 pb-1.5 last:border-b-0 last:pb-0">
                  <div className="flex items-center gap-2">
                    <span className={`inline-block h-1.5 w-1.5 rounded-full ${c.value >= 0 ? 'bg-up' : 'bg-down'}`} />
                    <span className="text-text-secondary">{c.name}</span>
                  </div>
                  <span className={toneClass(c.value)}>{formatPercent(c.value * 100)}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-lg border border-border/70 bg-surface-raised/60 p-3">
            <div className="flex items-center justify-between">
              <div className="text-caption text-text-tertiary">基差 / 领涨跌</div>
              <div className="text-caption text-text-secondary">{item.basis?.name ?? '期现价差'}</div>
            </div>
            <div className={`text-body-md tabular mt-1 ${toneClass(item.basis?.value ?? 0)}`}>
              {formatPercent(item.basis?.value ?? 0)}
            </div>
            <div className="mt-2 space-y-1">
              {(item.leaders ?? []).map((l) => (
                <div key={l.name} className="flex items-center justify-between text-caption">
                  <span className="text-text-secondary">{l.name}</span>
                  <span className={toneClass(l.change_percent)}>{formatPercent(l.change_percent)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

export function IndicesPanel({ indices, topMetrics }: IndicesPanelProps) {
  const [open, setOpen] = useState<string>('000300.SS');

  const headline = useMemo(() => indices.filter((x) => x.role === 'headline'), [indices]);
  const supports = useMemo(() => indices.filter((x) => x.role !== 'headline'), [indices]);
  const top = headline.slice(0, 2);
  const bottom = [...headline.slice(2), ...supports];

  return (
    <Card>
      <CardHeader title="市场总览" subtitle="核心指标 → 重点指数 → 扩展资产，支持展开查看关键驱动。" />

      {topMetrics && topMetrics.length > 0 ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-3">
          {topMetrics.map((m) => (
            <Metric
              key={m.label}
              label={m.label}
              value={m.unit === '%' ? formatPercent(m.value * 100, { signed: false }) : m.value.toFixed(2)}
              tone={m.tone ?? 'neutral'}
              size="md"
            />
          ))}
        </div>
      ) : null}

      {indices.length === 0 ? (
        <div className="mt-4">
          <EmptyState compact title="暂无可用行情" description="当前时段未获取到可用指数数据。" />
        </div>
      ) : (
        <div className="mt-4 space-y-4">
          <section>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-caption uppercase tracking-wider text-text-tertiary">重点指数主视图</span>
            </div>
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
              {top.map((item) => (
                <div key={item.symbol}>
                  <div className="mb-1 flex items-center justify-between">
                    <Badge tone={qualityTone(item.data_quality?.label)} size="xs">
                      {item.data_quality?.label ?? '研究'}数据
                    </Badge>
                    {item.data_quality?.delay_seconds ? (
                      <span className="text-micro text-text-tertiary">延迟 {Math.round(item.data_quality.delay_seconds / 60)} 分钟</span>
                    ) : null}
                  </div>
                  <IndexCard item={item} expanded={open === item.symbol} onToggle={() => setOpen(open === item.symbol ? '' : item.symbol)} />
                </div>
              ))}
            </div>
          </section>

          {bottom.length > 0 ? (
            <section>
              <div className="text-caption uppercase tracking-wider text-text-tertiary mb-2">扩展指数与关联资产</div>
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
                {bottom.map((item) => (
                  <IndexCard key={item.symbol} item={item} expanded={open === item.symbol} onToggle={() => setOpen(open === item.symbol ? '' : item.symbol)} />
                ))}
              </div>
            </section>
          ) : null}
        </div>
      )}
    </Card>
  );
}
