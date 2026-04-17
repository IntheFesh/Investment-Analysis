import { useState } from 'react';
import { Layout } from '@/components/shell/Layout';
import { ExportButton } from '@/components/shell/ExportButton';
import {
  TimeWindowSelector,
  MODULE_TIME_WINDOWS,
} from '@/components/shell/TimeWindowSelector';
import { useSentimentOverview } from '@/hooks/useSentiment';
import { Card, CardHeader, Metric } from '@/components/ui/Card';
import { GaugeChart } from '@/components/charts/GaugeChart';
import { LineChart } from '@/components/charts/LineChart';
import { FactorCard } from '@/components/pages/sentiment/FactorCard';
import { DataTable } from '@/components/ui/Table';
import { SkeletonChart } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { Badge } from '@/components/ui/Badge';
import { EvidencePanel, type Evidence } from '@/components/ui/EvidencePanel';
import { formatPercent } from '@/utils/format';
import { useAppContext } from '@/context/AppContext';

export default function SentimentPage() {
  const { researchMode } = useAppContext();
  const [timeWindow, setTimeWindow] = useState<string>('20D');
  const { data, isLoading, error, refetch } = useSentimentOverview(timeWindow);
  const meta = data?.meta;
  const sentiment = data?.data;
  const showAdvanced = researchMode !== 'light';

  const factorEvidences: Evidence[] = (sentiment?.factors ?? [])
    .map((f) => f.evidence)
    .filter((e): e is Evidence => !!e && typeof e === 'object');

  return (
    <Layout
      title="风险情绪"
      subtitle="短/中期综合评分、四因子解释、历史轨迹与贡献度分解；评分进入仿真压力参数。"
      meta={meta}
      actions={
        <div className="flex items-center gap-2">
          <TimeWindowSelector
            value={timeWindow}
            onChange={setTimeWindow}
            options={[...MODULE_TIME_WINDOWS]}
          />
          <ExportButton page="sentiment" />
        </div>
      }
    >
      {isLoading && !sentiment ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <SkeletonChart />
          <SkeletonChart />
        </div>
      ) : error ? (
        <ErrorState error={error} onRetry={() => refetch()} />
      ) : sentiment ? (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader
                title="短期风险温度（~20 交易日）"
                subtitle="0 为极度恐慌，100 为过热。基于跨指数波动与收益折算。"
                action={<Badge tone="brand">{sentiment.short_term_label}</Badge>}
              />
              <GaugeChart
                value={sentiment.short_term_score}
                label="短期得分"
                subtitle={sentiment.short_term_drivers.join(' · ') || '暂无驱动'}
                height={220}
              />
            </Card>
            <Card>
              <CardHeader
                title="中期风险温度（~60 交易日）"
                subtitle="长周期波动对比。与短期的差值代表情绪切换方向。"
                action={<Badge tone="brand">{sentiment.mid_term_label}</Badge>}
              />
              <GaugeChart
                value={sentiment.mid_term_score}
                label="中期得分"
                subtitle={sentiment.mid_term_drivers.join(' · ') || '暂无驱动'}
                height={220}
              />
            </Card>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            {sentiment.factors.map((f) => (
              <FactorCard key={f.id ?? f.name} factor={f} />
            ))}
          </div>

          {showAdvanced ? (
            <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-4">
              <Card>
                <CardHeader
                  title="得分轨迹（近 30 交易日）"
                  subtitle="短/中期得分随时间滚动重算。"
                />
                <LineChart
                  xData={sentiment.time_series.map((t) => t.date)}
                  series={[
                    { name: '短期', data: sentiment.time_series.map((t) => t.short) },
                    { name: '中期', data: sentiment.time_series.map((t) => t.mid), dashed: true },
                  ]}
                  valueFormatter={(v) => v.toFixed(0)}
                  height={300}
                />
              </Card>
              <Card>
                <CardHeader title="贡献度分解" subtitle="按权重加权后的因子得分。" />
                <DataTable
                  columns={[
                    { key: 'name', header: '因子', render: (r) => r.name },
                    {
                      key: 'weight',
                      header: '权重',
                      align: 'right',
                      render: (r) => (
                        <span className="tabular">
                          {formatPercent(r.weight * 100, { signed: false })}
                        </span>
                      ),
                    },
                    {
                      key: 'score',
                      header: '得分',
                      align: 'right',
                      render: (r) => <span className="tabular">{r.score.toFixed(1)}</span>,
                    },
                    {
                      key: 'contrib',
                      header: '贡献',
                      align: 'right',
                      render: (r) => (
                        <span className="tabular text-brand">
                          {(r.score * r.weight).toFixed(1)}
                        </span>
                      ),
                    },
                  ]}
                  rows={sentiment.contributions}
                  getRowKey={(r) => r.name}
                  dense
                />
                <div className="mt-3">
                  <Metric
                    label="加权综合"
                    value={sentiment.contributions
                      .reduce((s, c) => s + c.score * c.weight, 0)
                      .toFixed(1)}
                    tone="primary"
                    size="md"
                  />
                </div>
              </Card>
            </div>
          ) : null}

          {showAdvanced && factorEvidences.length > 0 ? (
            <EvidencePanel
              title="因子证据追溯"
              subtitle={`${factorEvidences.length} 条因子级证据 · 点击查看指标、失效条件与风险`}
              evidences={factorEvidences}
            />
          ) : null}
        </>
      ) : null}
    </Layout>
  );
}
