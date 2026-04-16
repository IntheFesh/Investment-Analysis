import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import Layout from '@/components/Layout';
import QueryErrorState from '@/components/QueryErrorState';
import { useAppContext } from '@/context/AppContext';
import { portfolioService } from '@/services/portfolioService';

export default function PortfolioPage() {
  const [tab, setTab] = useState<'overview' | 'diagnosis' | 'export'>('overview');
  const { portfolioId } = useAppContext();

  const overviewQuery = useQuery(['portfolio-overview', portfolioId], () => portfolioService.getOverview(portfolioId), { staleTime: 60 * 1000 });
  const diagnosisQuery = useQuery(['portfolio-diagnosis', portfolioId], () => portfolioService.getDiagnosis(portfolioId), { staleTime: 60 * 1000 });
  const exportQuery = useQuery(['portfolio-export-pack', portfolioId], () => portfolioService.getExportPack(portfolioId), { staleTime: 2 * 60 * 1000 });

  const markdownPreview = useMemo(
    () => (exportQuery.data as any)?.formats?.markdown?.split('\n').slice(0, 8).join('\n') ?? '',
    [exportQuery.data]
  );

  return (
    <Layout>
      <h1 className="text-2xl font-bold mb-4">基金组合</h1>
      <div className="flex space-x-4 mb-4 border-b border-gray-200 dark:border-gray-700">
        {['overview', 'diagnosis', 'export'].map((name) => (
          <button
            key={name}
            className={`px-3 py-2 text-sm font-medium ${tab === name ? 'border-b-2 border-indigo-600 text-indigo-600' : 'text-gray-600 dark:text-gray-400'}`}
            onClick={() => setTab(name as any)}
          >
            {name === 'overview' ? '组合看穿' : name === 'diagnosis' ? '组合诊断' : 'AI 导出'}
          </button>
        ))}
      </div>
      {tab === 'overview' && (overviewQuery.isLoading ? <p>加载中…</p> : overviewQuery.error ? <QueryErrorState error={overviewQuery.error} /> : <pre className="text-xs">{JSON.stringify(overviewQuery.data, null, 2)}</pre>)}
      {tab === 'diagnosis' && (diagnosisQuery.isLoading ? <p>加载中…</p> : diagnosisQuery.error ? <QueryErrorState error={diagnosisQuery.error} /> : <pre className="text-xs">{JSON.stringify(diagnosisQuery.data, null, 2)}</pre>)}
      {tab === 'export' && (exportQuery.isLoading ? <p>加载中…</p> : exportQuery.error ? <QueryErrorState error={exportQuery.error} /> : <pre className="text-xs">{markdownPreview}</pre>)}
    </Layout>
  );
}
