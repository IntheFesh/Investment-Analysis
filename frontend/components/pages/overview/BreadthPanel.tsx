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
      <CardHeader
        title="市场广度"
        subtitle="基于跨指数上涨家数 / 总样本。heat 取值 0–1，1 为广度极强。"
      />
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
        <Metric
          label="上涨占比"
          value={formatPercent(data.advancers_ratio * 100, { signed: false })}
          tone={data.advancers_ratio >= 0.5 ? 'up' : 'down'}
          size="md"
        />
        <Metric
          label="代理涨停"
          value={data.limit_up}
          tone="up"
          hint="上涨样本 × 5%（代理）"
          size="md"
        />
        <Metric
          label="代理跌停"
          value={data.limit_down}
          tone="down"
          hint="下跌样本 × 3%（代理）"
          size="md"
        />
        <Metric
          label="波动指示"
          value={formatPercent(data.turnover_change, { signed: false })}
          tone="neutral"
          hint="abs 行业收益均值，代理成交量方差"
          size="md"
        />
      </div>
      <div className="mt-5">
        <div className="flex items-center justify-between text-caption text-text-tertiary mb-1.5">
          <span>市场热度</span>
          <span className="tabular">{formatPercent(data.market_heat * 100, { signed: false })}</span>
        </div>
        <ProgressBar
          value={data.market_heat}
          tone={data.market_heat >= 0.6 ? 'warn' : data.market_heat >= 0.45 ? 'up' : 'down'}
        />
      </div>
    </Card>
  );
}
