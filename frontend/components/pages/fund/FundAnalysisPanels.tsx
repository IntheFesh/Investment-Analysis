import { Card, CardHeader, Metric } from '@/components/ui/Card';
import { AreaChart } from '@/components/charts/AreaChart';
import { BarChart } from '@/components/charts/BarChart';
import { DonutChart } from '@/components/charts/DonutChart';
import { DataTable } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { formatPercent } from '@/utils/format';
import type { FundAnalysis } from '@/services/types';

interface Props {
  data: FundAnalysis;
}

export function FundAnalysisPanels({ data }: Props) {
  const navDates = data.nav_curve.map((x) => x.date);
  const navValues = data.nav_curve.map((x) => x.nav);
  const drawdownDates = data.drawdown_curve.map((x) => x.date);
  const drawdownValues = data.drawdown_curve.map((x) => x.drawdown);

  const industryEntries = Object.entries(data.exposures.industry);
  const styleEntries = Object.entries(data.exposures.style);

  return (
    <>
      <div className="grid grid-cols-1 lg:grid-cols-[1.4fr_1fr] gap-4">
        <Card>
          <CardHeader title="净值曲线" subtitle="基于代理指数推算（最近 120 个交易日）。" />
          <AreaChart
            xData={navDates}
            values={navValues}
            name="净值"
            valueFormatter={(v) => v.toFixed(3)}
            height={280}
            tone="brand"
          />
        </Card>
        <Card>
          <CardHeader title="风险指标" subtitle="滚动分位与基准偏差。" />
          <div className="grid grid-cols-2 gap-4 mt-3">
            <Metric
              label="年化波动"
              value={formatPercent(data.metrics.volatility, { signed: false })}
              size="md"
            />
            <Metric
              label="最大回撤"
              value={formatPercent(data.metrics.max_drawdown, { signed: false })}
              tone="down"
              size="md"
            />
            <Metric
              label="20D 分位"
              value={`${Math.round((data.metrics.rolling_rank['20D'] ?? 0) * 100)}%`}
              size="md"
            />
            <Metric
              label="60D 分位"
              value={`${Math.round((data.metrics.rolling_rank['60D'] ?? 0) * 100)}%`}
              size="md"
            />
          </div>
          <div className="mt-4">
            <div className="text-caption text-text-tertiary uppercase tracking-wider mb-1">
              基准偏差
            </div>
            <div className="text-body-sm text-text-secondary">
              相关性 - 1 = {data.metrics.benchmark_deviation.toFixed(3)}
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1.4fr_1fr] gap-4">
        <Card>
          <CardHeader title="回撤曲线" subtitle="单位：百分比。距历史高点的距离。" />
          <AreaChart
            xData={drawdownDates}
            values={drawdownValues}
            name="drawdown"
            valueFormatter={(v) => `${v.toFixed(1)}%`}
            height={260}
            tone="down"
          />
        </Card>
        <Card>
          <CardHeader
            title="风格暴露"
            subtitle={`漂移标签：${data.exposures.style_drift_flag}`}
          />
          <DonutChart
            data={styleEntries.map(([name, value]) => ({ name, value: value * 100 }))}
            height={220}
            valueFormatter={(v) => `${v.toFixed(1)}%`}
          />
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader title="行业分布" />
          <BarChart
            categories={industryEntries.map(([k]) => k)}
            values={industryEntries.map(([, v]) => v * 100)}
            horizontal
            valueFormatter={(v) => `${v.toFixed(1)}%`}
            height={260}
          />
        </Card>
        <Card>
          <CardHeader title="代理重仓（Top 5）" subtitle="基于行业权重代理生成的合成持仓。" />
          <DataTable
            dense
            columns={[
              { key: 'ticker', header: '代理代码', render: (r) => <span className="font-mono text-text-secondary">{r.ticker}</span> },
              { key: 'name', header: '映射行业', render: (r) => r.name },
              {
                key: 'weight',
                header: '权重',
                align: 'right',
                render: (r) => <span className="tabular">{formatPercent(r.weight, { signed: false })}</span>,
              },
            ]}
            rows={data.top_holdings}
            getRowKey={(r) => r.ticker}
          />
        </Card>
      </div>

      <Card>
        <CardHeader
          title="与当前组合的关系"
          subtitle={`组合 ${data.portfolio_relation.portfolio_id}`}
        />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3">
          <Metric
            label="重叠度"
            value={(data.portfolio_relation.overlap_score * 100).toFixed(1) + '%'}
            size="md"
          />
          <Metric
            label="相关性"
            value={data.portfolio_relation.correlation.toFixed(2)}
            tone={data.portfolio_relation.correlation > 0.8 ? 'warn' : 'up'}
            size="md"
          />
          <div className="col-span-2">
            <div className="text-caption text-text-tertiary mb-1 uppercase tracking-wider">情景对比</div>
            <div className="flex flex-wrap items-center gap-2 text-body-sm">
              <Badge tone="up" size="sm">加入后</Badge>
              <span className="text-text-secondary">{data.portfolio_relation.if_added}</span>
              <Badge tone="down" size="sm">剔除后</Badge>
              <span className="text-text-secondary">{data.portfolio_relation.if_removed}</span>
            </div>
          </div>
        </div>
      </Card>

      <Card>
        <CardHeader title="研究结论" subtitle="由指标联合生成，面向研报式陈述。" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-3 text-body-sm">
          <div className="rounded-md border border-border bg-surface-sunken/40 p-3">
            <div className="text-caption text-text-tertiary uppercase tracking-wider mb-1">适用情景</div>
            <div className="text-text-primary">{data.conclusion.suitable_scenarios}</div>
          </div>
          <div className="rounded-md border border-border bg-surface-sunken/40 p-3">
            <div className="text-caption text-text-tertiary uppercase tracking-wider mb-1">优势</div>
            <div className="text-text-primary">{data.conclusion.advantages}</div>
          </div>
          <div className="rounded-md border border-border bg-surface-sunken/40 p-3">
            <div className="text-caption text-text-tertiary uppercase tracking-wider mb-1">风险</div>
            <div className="text-text-primary">{data.conclusion.risks}</div>
          </div>
        </div>
      </Card>
    </>
  );
}
