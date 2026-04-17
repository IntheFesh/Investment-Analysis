import { useState } from 'react';
import { Layout } from '@/components/shell/Layout';
import { ExportButton } from '@/components/shell/ExportButton';
import { Tabs } from '@/components/ui/Tabs';
import { SkeletonChart } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import {
  usePortfolioOverview,
  usePortfolioDiagnosis,
  usePortfolioExportPack,
} from '@/hooks/usePortfolio';
import { PortfolioOverviewTab } from '@/components/pages/portfolio/OverviewTab';
import { PortfolioDiagnosisTab } from '@/components/pages/portfolio/DiagnosisTab';
import { PortfolioAIExportTab } from '@/components/pages/portfolio/AIExportTab';

const TABS = [
  { id: 'overview', label: '组合穿透' },
  { id: 'diagnosis', label: '组合诊断' },
  { id: 'export', label: 'AI 导出包' },
];

export default function PortfolioPage() {
  const [tab, setTab] = useState('overview');

  const overview = usePortfolioOverview();
  const diagnosis = usePortfolioDiagnosis();
  const exportPack = usePortfolioExportPack();

  const activeQuery =
    tab === 'overview' ? overview : tab === 'diagnosis' ? diagnosis : exportPack;
  const meta = activeQuery.data?.meta ?? overview.data?.meta;

  return (
    <Layout
      title="基金组合"
      subtitle="穿透单持仓、结构性诊断、AI 导出包——三视图一套组合数据。"
      meta={meta}
      actions={<ExportButton page="portfolio" portfolioId={overview.data?.data.portfolio_id ?? null} />}
    >
      <Tabs value={tab} onChange={setTab} items={TABS} />

      {tab === 'overview' && (
        overview.isLoading && !overview.data ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <SkeletonChart />
            <SkeletonChart />
          </div>
        ) : overview.error ? (
          <ErrorState error={overview.error} onRetry={() => overview.refetch()} />
        ) : overview.data ? (
          <PortfolioOverviewTab data={overview.data.data} />
        ) : null
      )}

      {tab === 'diagnosis' && (
        diagnosis.isLoading && !diagnosis.data ? (
          <SkeletonChart />
        ) : diagnosis.error ? (
          <ErrorState error={diagnosis.error} onRetry={() => diagnosis.refetch()} />
        ) : diagnosis.data ? (
          <PortfolioDiagnosisTab data={diagnosis.data.data} />
        ) : null
      )}

      {tab === 'export' && (
        exportPack.isLoading && !exportPack.data ? (
          <SkeletonChart />
        ) : exportPack.error ? (
          <ErrorState error={exportPack.error} onRetry={() => exportPack.refetch()} />
        ) : exportPack.data ? (
          <PortfolioAIExportTab data={exportPack.data.data} />
        ) : null
      )}
    </Layout>
  );
}
