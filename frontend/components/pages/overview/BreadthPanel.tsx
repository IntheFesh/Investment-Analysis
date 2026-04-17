import { Card, CardHeader, Metric } from '@/components/ui/Card';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { formatPercent } from '@/utils/format';
import type { BreadthStats } from '@/services/types';

interface Props {
  data: BreadthStats;
}

export function BreadthPanel({ data }: Props) {
  return (
    <Card>
      <CardHeader title="市场广度" subtitle="上涨占比、均线站上比例、创新高/低与热点扩散度。" />
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
        <Metric
          label="上涨占比"
          value={formatPercent(data.advancers_ratio * 100, { signed: false })}
          tone={data.advancers_ratio >= 0.5 ? 'up' : 'down'}
          size="md"
        />
        <Metric
          label="下跌占比"
          value={formatPercent(data.decliners_ratio * 100, { signed: false })}
          tone={data.decliners_ratio <= 0.5 ? 'up' : 'down'}
          size="md"
        />
        <Metric
          label="站上MA20"
          value={formatPercent(data.above_ma20_ratio * 100, { signed: false })}
          tone="neutral"
          size="md"
        />
        <Metric
          label="站上MA60"
          value={formatPercent(data.above_ma60_ratio * 100, { signed: false })}
          tone="neutral"
          size="md"
        />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3">
        <Metric label="创新高占比" value={formatPercent(data.new_high_ratio * 100, { signed: false })} tone="up" size="md" />
        <Metric label="创新低占比" value={formatPercent(data.new_low_ratio * 100, { signed: false })} tone="down" size="md" />
        <Metric label="热点集中度" value={formatPercent(data.hotspot_concentration * 100, { signed: false })} tone="warn" size="md" />
        <Metric label="扩散波动" value={data.diffusion.toFixed(2)} tone="neutral" size="md" />
      </div>

      <div className="mt-5 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <div className="flex items-center justify-between text-caption text-text-tertiary mb-1.5">
            <span>市场热度</span>
            <span className="tabular">{formatPercent(data.market_heat * 100, { signed: false })}</span>
          </div>
          <ProgressBar value={data.market_heat} tone={data.market_heat >= 0.62 ? 'warn' : data.market_heat >= 0.48 ? 'up' : 'down'} />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div className="rounded-md border border-border bg-surface-sunken/40 p-2.5">
            <div className="text-caption text-text-tertiary">涨停代理</div>
            <div className="text-body-md text-up tabular">{data.limit_up}</div>
          </div>
          <div className="rounded-md border border-border bg-surface-sunken/40 p-2.5">
            <div className="text-caption text-text-tertiary">跌停代理</div>
            <div className="text-body-md text-down tabular">{data.limit_down}</div>
          </div>
        </div>
      </div>
    </Card>
  );
}
