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
import { NewsPanel } from '@/components/pages/overview/NewsPanel';
import { SkeletonChart } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { useAppContext } from '@/context/AppContext';

export default function OverviewPage() {
  const { researchMode } = useAppContext();
  const [timeWindow, setTimeWindow] = useState<string>('20D');
  const { data, isLoading, error, refetch } = useMarketOverview(timeWindow);
  const meta = data?.meta;
  const overview = data?.data;

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
      ) : error && !overview ? (
        <ErrorState error={error} onRetry={() => refetch()} />
      ) : overview ? (
        <>
          <IndicesPanel indices={overview.indices} topMetrics={overview.top_metrics} />
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
          {showDetailedPanels ? (
            <NewsPanel
              domestic={overview.news?.domestic ?? []}
              international={overview.news?.international ?? []}
            />
          ) : null}
        </>
      ) : null}
    </Layout>
  );
}
