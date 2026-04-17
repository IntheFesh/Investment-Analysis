import { Card, CardHeader, Metric } from '@/components/ui/Card';
import { Heatmap } from '@/components/charts/Heatmap';
import { LineChart } from '@/components/charts/LineChart';
import { DataTable } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { formatPercent } from '@/utils/format';
import type { StatisticalSimulationResult } from '@/services/types';

interface Props {
  result: StatisticalSimulationResult;
}

export function StatisticalResult({ result }: Props) {
  const quantiles = Object.keys(result.heatmap);
  const horizonLabels = result.horizons.map((h) => `${h}D`);
  const heatmapData: Array<[number, number, number]> = [];
  quantiles.forEach((q, yi) => {
    result.horizons.forEach((h, xi) => {
      const value = result.heatmap[q]?.[String(h)];
      if (typeof value === 'number') heatmapData.push([xi, yi, value]);
    });
  });

  const curveX = result.extreme_curve.map((c) => `${c.horizon}D`);

  return (
    <>
      <Card>
        <CardHeader
          title="关键指标"
          subtitle={`路径数 ${result.num_paths.toLocaleString()} · 抽样 ${result.bootstrap ? 'Bootstrap' : '高斯'} · 置信区间 ${(result.confidence_interval * 100).toFixed(0)}%`}
        />
        <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-4">
          <Metric
            label="最大回撤"
            value={formatPercent(result.max_drawdown, { signed: false })}
            tone="down"
            size="md"
          />
          <Metric
            label="区间覆盖"
            value={`${horizonLabels.join(' / ')}`}
            size="md"
          />
          <Metric
            label="分位数量"
            value={`${quantiles.length}`}
            hint="收益分布分位"
            size="md"
          />
          <Metric
            label="敏感因子"
            value={`${result.sensitivity.length}`}
            hint="暴露关联因素"
            size="md"
          />
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-[1.2fr_1fr] gap-4">
        <Card>
          <CardHeader title="收益分位热力图" subtitle="列：持有期；行：分位数；值：累计收益。" />
          <Heatmap
            xLabels={horizonLabels}
            yLabels={quantiles}
            data={heatmapData}
            valueFormatter={(v) => `${(v * 100).toFixed(1)}%`}
            height={320}
          />
        </Card>
        <Card>
          <CardHeader title="极端路径包络" subtitle="最优 / 中位 / 最差走势。" />
          <LineChart
            xData={curveX}
            series={[
              {
                name: '最优',
                data: result.extreme_curve.map((c) => c.best_return * 100),
                area: true,
              },
              {
                name: '中位',
                data: result.extreme_curve.map((c) => c.median * 100),
                dashed: true,
              },
              {
                name: '最差',
                data: result.extreme_curve.map((c) => c.worst_return * 100),
              },
            ]}
            valueFormatter={(v) => `${v.toFixed(1)}%`}
            height={320}
            yAxisName="%"
          />
        </Card>
      </div>

      <Card>
        <CardHeader title="敏感性分析" subtitle="因子变化与潜在回撤的一阶联动。" />
        <DataTable
          dense
          columns={[
            { key: 'factor', header: '因子', render: (r) => r.factor },
            {
              key: 'expected_change',
              header: '预期冲击',
              align: 'right',
              render: (r) => (
                <span className="tabular">{formatPercent(r.expected_change, { signed: true })}</span>
              ),
            },
            {
              key: 'loss_risk',
              header: '潜在回撤',
              align: 'right',
              render: (r) => (
                <span className="tabular text-down">
                  {formatPercent(r.loss_risk, { signed: false })}
                </span>
              ),
            },
            {
              key: 'affected_exposure',
              header: '影响暴露',
              render: (r) => <Badge tone="info" size="xs">{r.affected_exposure}</Badge>,
            },
          ]}
          rows={result.sensitivity}
          getRowKey={(r) => r.factor}
        />
      </Card>
    </>
  );
}
