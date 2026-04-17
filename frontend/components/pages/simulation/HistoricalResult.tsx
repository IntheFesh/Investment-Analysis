import { Card, CardHeader, Metric } from '@/components/ui/Card';
import { LineChart } from '@/components/charts/LineChart';
import type { HistoricalSimulationResult } from '@/services/types';
import { formatPercent } from '@/utils/format';

interface Props {
  result: HistoricalSimulationResult;
}

export function HistoricalResult({ result }: Props) {
  const xData = result.path.map((p) => p.date);
  const cumSeries = result.path.map((p) => p.cum_return * 100);
  const retSeries = result.path.map((p) => p.return * 100);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-4">
      <Card>
        <CardHeader
          title={`历史重演 · ${result.event_label}`}
          subtitle={result.description ?? '按组合权重回放该历史窗口的累计收益。'}
        />
        {result.path.length === 0 ? (
          <div className="text-body-sm text-text-tertiary">暂无重演数据。</div>
        ) : (
          <LineChart
            xData={xData}
            series={[
              { name: '累计收益%', data: cumSeries },
              { name: '日度收益%', data: retSeries, dashed: true },
            ]}
            valueFormatter={(v) => `${v.toFixed(2)}%`}
            height={320}
          />
        )}
      </Card>
      <Card>
        <CardHeader title="关键指标" subtitle="窗口累计、最大回撤、情绪叠加后最坏估计。" />
        <div className="mt-2 grid grid-cols-1 gap-2">
          <Metric
            label="窗口累计收益"
            value={formatPercent((result.total_return ?? 0) * 100, { signed: true })}
            tone={(result.total_return ?? 0) >= 0 ? 'up' : 'down'}
          />
          <Metric
            label="最大回撤"
            value={formatPercent((result.max_drawdown ?? 0) * 100, { signed: true })}
            tone="down"
          />
          {typeof result.stress_adjusted_worst === 'number' ? (
            <Metric
              label="情绪叠加最坏"
              value={formatPercent(result.stress_adjusted_worst * 100, { signed: true })}
              tone="down"
            />
          ) : null}
        </div>
      </Card>
    </div>
  );
}
