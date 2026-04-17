import { Card, CardHeader, Metric } from '@/components/ui/Card';
import { DataTable } from '@/components/ui/Table';
import { BarChart } from '@/components/charts/BarChart';
import { Heatmap } from '@/components/charts/Heatmap';
import { DonutChart } from '@/components/charts/DonutChart';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { formatCurrency, formatPercent, formatSignedNumber, directionClass } from '@/utils/format';
import type { PortfolioOverview } from '@/services/types';

interface Props {
  data: PortfolioOverview;
}

export function PortfolioOverviewTab({ data }: Props) {
  const { summary, holdings, exposures, overlap, target_deviation } = data;

  const industryEntries = Object.entries(exposures.industry).slice(0, 8);
  const styleEntries = Object.entries(exposures.style);
  const marketEntries = Object.entries(exposures.market);

  const overlapData: Array<[number, number, number]> = [];
  overlap.funds.forEach((_a, i) => {
    overlap.funds.forEach((_b, j) => {
      const v = overlap.matrix?.[i]?.[j];
      if (typeof v === 'number') overlapData.push([i, j, v]);
    });
  });

  return (
    <>
      <Card>
        <CardHeader title="组合摘要" subtitle="总资产、浮动盈亏、风险测度。单位：人民币元。" />
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-5 mt-4">
          <Metric label="总资产" value={formatCurrency(summary.total_assets)} size="md" />
          <Metric label="总成本" value={formatCurrency(summary.total_cost)} size="md" />
          <Metric
            label="浮动盈亏"
            value={formatSignedNumber(summary.profit_loss)}
            tone={summary.profit_loss >= 0 ? 'up' : 'down'}
            size="md"
          />
          <Metric
            label="年化收益"
            value={formatPercent(summary.return_percent, { signed: true })}
            tone={summary.return_percent >= 0 ? 'up' : 'down'}
            size="md"
          />
          <Metric
            label="年化波动"
            value={formatPercent(summary.volatility, { signed: false })}
            size="md"
          />
          <Metric
            label="最大回撤"
            value={formatPercent(summary.max_drawdown, { signed: false })}
            tone="down"
            size="md"
          />
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-4">
        <Card>
          <CardHeader
            title="持仓构成"
            subtitle="按权重降序排列，穿透到标的名称、类型与基金经理。"
          />
          <DataTable
            dense
            columns={[
              { key: 'code', header: '代码', render: (r) => <span className="font-mono text-text-secondary">{r.code}</span> },
              { key: 'name', header: '名称', render: (r) => <span className="text-text-primary">{r.name}</span> },
              { key: 'type', header: '类型', render: (r) => r.type },
              { key: 'manager', header: '基金经理', render: (r) => r.manager },
              {
                key: 'weight',
                header: '权重',
                align: 'right',
                render: (r) => (
                  <div className="flex items-center justify-end gap-2">
                    <span className={`tabular ${directionClass(r.weight)}`}>
                      {formatPercent(r.weight, { signed: false })}
                    </span>
                    <div className="w-16">
                      <ProgressBar value={r.weight / 100} size="xs" tone="brand" />
                    </div>
                  </div>
                ),
              },
            ]}
            rows={holdings}
            getRowKey={(r) => r.code}
          />
        </Card>

        <Card>
          <CardHeader
            title="风险偏差"
            subtitle={`目标：${target_deviation.risk_profile} · 参考波动区间 ${target_deviation.recommended_risk_range
              .map((v) => (v * 100).toFixed(0) + '%')
              .join(' – ')}`}
          />
          <div className="mt-3 flex flex-col gap-4">
            <Metric
              label="当前波动"
              value={formatPercent(target_deviation.actual_risk * 100, { signed: false })}
              size="md"
              tone="primary"
            />
            <div>
              <div className="flex items-center justify-between text-caption text-text-tertiary mb-1.5">
                <span>偏差度</span>
                <span className="tabular">
                  {formatPercent(target_deviation.deviation * 100, { signed: false })}
                </span>
              </div>
              <ProgressBar
                value={Math.min(1, target_deviation.deviation * 5)}
                tone={target_deviation.deviation > 0.04 ? 'down' : target_deviation.deviation > 0.02 ? 'warn' : 'up'}
              />
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card>
          <CardHeader title="行业暴露" subtitle="穿透加权后的行业分布（Top 8）。" />
          <BarChart
            categories={industryEntries.map(([k]) => k)}
            values={industryEntries.map(([, v]) => v * 100)}
            valueFormatter={(v) => `${v.toFixed(1)}%`}
            horizontal
            height={260}
          />
        </Card>
        <Card>
          <CardHeader title="风格分布" subtitle="成长 / 价值 / 红利 / 防御。" />
          <DonutChart
            data={styleEntries.map(([name, value]) => ({ name, value: value * 100 }))}
            height={260}
            valueFormatter={(v) => `${v.toFixed(1)}%`}
          />
        </Card>
        <Card>
          <CardHeader title="市场切片" subtitle="按风格映射的 A 股与防御仓位。" />
          <DonutChart
            data={marketEntries.map(([name, value]) => ({ name, value: value * 100 }))}
            height={260}
            valueFormatter={(v) => `${v.toFixed(1)}%`}
          />
        </Card>
      </div>

      <Card>
        <CardHeader
          title="基金重叠矩阵"
          subtitle="基于代理日收益的相关性矩阵（-1 到 1）。值越高表示两个基金收益越同步。"
        />
        {overlap.funds.length === 0 ? (
          <div className="text-body-sm text-text-tertiary py-4">暂无重叠数据。</div>
        ) : (
          <Heatmap
            xLabels={overlap.funds}
            yLabels={overlap.funds}
            data={overlapData}
            valueFormatter={(v) => v.toFixed(2)}
            height={300}
            min={-1}
            max={1}
          />
        )}
      </Card>
    </>
  );
}
