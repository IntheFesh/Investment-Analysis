import { useState } from 'react';
import { Layout } from '@/components/shell/Layout';
import { ExportButton } from '@/components/shell/ExportButton';
import {
  TimeWindowSelector,
  MODULE_TIME_WINDOWS,
} from '@/components/shell/TimeWindowSelector';
import { useMarketOverview } from '@/hooks/useMarket';
import { IndicesPanel } from '@/components/pages/overview/IndicesPanel';
import { SectorRotationPanel } from '@/components/pages/overview/SectorRotationPanel';
import { FundFlowsPanel } from '@/components/pages/overview/FundFlowsPanel';
import { BreadthPanel } from '@/components/pages/overview/BreadthPanel';
import { ExplanationsPanel } from '@/components/pages/overview/ExplanationsPanel';
import { EvidencePanel, type Evidence } from '@/components/ui/EvidencePanel';
import { SkeletonChart } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { useAppContext } from '@/context/AppContext';

export default function OverviewPage() {
  const { researchMode } = useAppContext();
  const [timeWindow, setTimeWindow] = useState<string>('20D');
  const { data, isLoading, error, refetch } = useMarketOverview(timeWindow);
  const meta = data?.meta;
  const overview = data?.data;

  const evidences: Evidence[] = (overview?.explanations ?? [])
    .map((e) => e.evidence)
    .filter((e): e is Evidence => !!e && typeof e === 'object');

  const showDetailedPanels = researchMode !== 'light';

  return (
    <Layout
      title="市场总览"
      subtitle="指数、板块轮动、资金偏好、广度与自动解读；每条结论可展开追溯。"
      meta={meta}
      actions={
        <div className="flex items-center gap-2">
          <TimeWindowSelector
            value={timeWindow}
            onChange={setTimeWindow}
            options={[...MODULE_TIME_WINDOWS]}
          />
          <ExportButton page="overview" />
        </div>
      }
    >
      {isLoading && !overview ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <SkeletonChart />
          <SkeletonChart />
          <SkeletonChart />
          <SkeletonChart />
        </div>
      ) : error ? (
        <ErrorState error={error} onRetry={() => refetch()} />
      ) : overview ? (
        <>
          <IndicesPanel indices={overview.indices} />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <SectorRotationPanel data={overview.signals.sector_rotation} />
            {showDetailedPanels ? (
              <FundFlowsPanel data={overview.signals.fund_flows} />
            ) : null}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {showDetailedPanels ? <BreadthPanel data={overview.signals.breadth} /> : null}
            <ExplanationsPanel
              explanations={overview.explanations}
              summary={overview.summary}
            />
          </div>
          {showDetailedPanels && evidences.length > 0 ? (
            <EvidencePanel
              title="今日结论追溯"
              subtitle={`${evidences.length} 条解读级证据 · 方法版本、指标、失效条件均可追溯`}
              evidences={evidences}
            />
          ) : null}
        </>
      ) : null}
    </Layout>
  );
}
