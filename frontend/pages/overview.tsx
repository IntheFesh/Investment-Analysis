import { Layout } from '@/components/shell/Layout';
import { ExportButton } from '@/components/shell/ExportButton';
import { useMarketOverview } from '@/hooks/useMarket';
import { IndicesPanel } from '@/components/pages/overview/IndicesPanel';
import { SectorRotationPanel } from '@/components/pages/overview/SectorRotationPanel';
import { FundFlowsPanel } from '@/components/pages/overview/FundFlowsPanel';
import { BreadthPanel } from '@/components/pages/overview/BreadthPanel';
import { ExplanationsPanel } from '@/components/pages/overview/ExplanationsPanel';
import { SkeletonChart } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';

export default function OverviewPage() {
  const { data, isLoading, error, refetch } = useMarketOverview();
  const meta = data?.meta;
  const overview = data?.data;

  return (
    <Layout
      title="市场总览"
      subtitle="统一视角下的指数、板块轮动、资金偏好、广度与自动解读。所有数值来源于后端 /api/v1/market/overview。"
      meta={meta}
      actions={<ExportButton page="overview" />}
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
            <FundFlowsPanel data={overview.signals.fund_flows} />
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <BreadthPanel data={overview.signals.breadth} />
            <ExplanationsPanel
              explanations={overview.explanations}
              summary={overview.summary}
            />
          </div>
        </>
      ) : null}
    </Layout>
  );
}
