import { useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { Layout } from '@/components/shell/Layout';
import { SkeletonChart } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { Button } from '@/components/ui/Button';
import {
  TimeWindowSelector,
  MODULE_TIME_WINDOWS,
} from '@/components/shell/TimeWindowSelector';
import { useFundOverview, useFundAnalysis } from '@/hooks/useFund';
import { FundSummary } from '@/components/pages/fund/FundSummary';
import { FundAnalysisPanels } from '@/components/pages/fund/FundAnalysisPanels';

export default function FundDetailPage() {
  const router = useRouter();
  const rawCode = router.query.code;
  const code = typeof rawCode === 'string' ? rawCode : '';

  const [timeWindow, setTimeWindow] = useState<string>('20D');
  const overview = useFundOverview(code, timeWindow);
  const analysis = useFundAnalysis(code, timeWindow);

  const meta = overview.data?.meta ?? analysis.data?.meta;

  return (
    <Layout
      title={overview.data?.data.name ?? '基金详情'}
      subtitle={code ? `代码 ${code}` : '正在解析路由参数…'}
      meta={meta}
      actions={
        <div className="flex items-center gap-2">
          <TimeWindowSelector
            value={timeWindow}
            onChange={setTimeWindow}
            options={[...MODULE_TIME_WINDOWS]}
          />
          <Link href="/fund">
            <Button variant="ghost" size="sm">
              返回基金池
            </Button>
          </Link>
        </div>
      }
    >
      {!code ? (
        <SkeletonChart height={200} />
      ) : overview.isLoading && !overview.data ? (
        <div className="grid grid-cols-1 gap-4">
          <SkeletonChart height={160} />
          <SkeletonChart height={260} />
        </div>
      ) : overview.error ? (
        <ErrorState error={overview.error} onRetry={() => overview.refetch()} />
      ) : overview.data ? (
        <FundSummary data={overview.data.data} />
      ) : null}

      {analysis.isLoading && !analysis.data ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <SkeletonChart height={280} />
          <SkeletonChart height={280} />
        </div>
      ) : analysis.error ? (
        <ErrorState error={analysis.error} onRetry={() => analysis.refetch()} />
      ) : analysis.data ? (
        <FundAnalysisPanels data={analysis.data.data} />
      ) : null}
    </Layout>
  );
}
