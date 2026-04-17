import { Card, CardHeader } from '@/components/ui/Card';
import { Heatmap } from '@/components/charts/Heatmap';
import { DataTable } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { formatPercent } from '@/utils/format';
import type { ScenarioSimulationResult } from '@/services/types';

interface Props {
  result: ScenarioSimulationResult;
}

export function ScenarioResult({ result }: Props) {
  const rowKeys = Object.keys(result.heatmap);
  const colKeys = rowKeys.length ? Object.keys(result.heatmap[rowKeys[0]] ?? {}) : [];
  const heatmapData: Array<[number, number, number]> = [];
  rowKeys.forEach((rk, yi) => {
    colKeys.forEach((ck, xi) => {
      const v = result.heatmap[rk]?.[ck];
      if (typeof v === 'number') heatmapData.push([xi, yi, v]);
    });
  });

  return (
    <>
      <Card>
        <CardHeader title="情景回测" subtitle="预设基准 / 黑天鹅 / 政策拐点——后端生成的滚动结果。" />
        <DataTable
          dense
          columns={[
            {
              key: 'label',
              header: '情景',
              render: (r) => <Badge tone="brand" size="xs">{r.label}</Badge>,
            },
            {
              key: 'expected_return',
              header: '预期收益',
              align: 'right',
              render: (r) => (
                <span
                  className={
                    'tabular ' + (r.expected_return >= 0 ? 'text-up' : 'text-down')
                  }
                >
                  {formatPercent(r.expected_return, { signed: true })}
                </span>
              ),
            },
            {
              key: 'worst_return',
              header: '最差收益',
              align: 'right',
              render: (r) => (
                <span className="tabular text-down">
                  {formatPercent(r.worst_return, { signed: true })}
                </span>
              ),
            },
            {
              key: 'max_exposure',
              header: '暴露最强因子',
              render: (r) => (
                <div className="flex items-center gap-2 text-body-sm">
                  <span>{r.max_exposure_factor[0]}</span>
                  <span className="tabular text-text-tertiary">
                    {formatPercent(r.max_exposure_factor[1], { signed: false })}
                  </span>
                </div>
              ),
            },
          ]}
          rows={result.scenarios}
          getRowKey={(r) => r.scenario_id}
        />
      </Card>

      <Card>
        <CardHeader title="情景 × 因子 热力图" subtitle="衡量各预设下主要因子的偏离程度。" />
        {heatmapData.length === 0 ? (
          <div className="text-body-sm text-text-tertiary mt-3">后端未返回热力图数据。</div>
        ) : (
          <Heatmap
            xLabels={colKeys}
            yLabels={rowKeys}
            data={heatmapData}
            valueFormatter={(v) => `${(v * 100).toFixed(1)}%`}
            height={Math.max(280, rowKeys.length * 42)}
          />
        )}
      </Card>
    </>
  );
}
