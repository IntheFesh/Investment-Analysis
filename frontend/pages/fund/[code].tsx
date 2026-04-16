import { useRouter } from 'next/router';
import { useQuery } from '@tanstack/react-query';
import Layout from '@/components/Layout';
import QueryErrorState from '@/components/QueryErrorState';
import { fundService } from '@/services/fundService';

export default function FundDetailPage() {
  const router = useRouter();
  const { code } = router.query as { code: string };

  const overviewQuery = useQuery(['fund-overview', code], () => fundService.getOverview(code), { enabled: !!code, staleTime: 2 * 60 * 1000 });
  const analysisQuery = useQuery(['fund-analysis', code], () => fundService.getAnalysis(code), { enabled: !!code, staleTime: 2 * 60 * 1000 });

  return (
    <Layout>
      {(!code || overviewQuery.isLoading || analysisQuery.isLoading) && <p>加载中…</p>}
      {overviewQuery.error && <QueryErrorState error={overviewQuery.error} />}
      {analysisQuery.error && <QueryErrorState error={analysisQuery.error} />}
      {overviewQuery.data && analysisQuery.data && (
        <div>
          <h1 className="text-2xl font-bold mb-2">{(overviewQuery.data as any).name}（{(overviewQuery.data as any).code}）</h1>
          <pre className="text-xs">{JSON.stringify(analysisQuery.data, null, 2)}</pre>
        </div>
      )}
    </Layout>
  );
}
