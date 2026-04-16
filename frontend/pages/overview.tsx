import { useQuery } from '@tanstack/react-query';
import Layout from '@/components/Layout';
import QueryErrorState from '@/components/QueryErrorState';
import { useAppContext } from '@/context/AppContext';
import { marketService } from '@/services/marketService';

interface MarketData {
  indices: { symbol: string; name: string; last: number; change_percent: number; turnover: number }[];
  summary: string;
}

export default function OverviewPage() {
  const { marketView, timeWindow } = useAppContext();
  const { data, isLoading, error } = useQuery(
    ['market-overview', marketView, timeWindow],
    () => marketService.getOverview({ market_view: marketView, time_window: timeWindow }) as Promise<MarketData>,
    { staleTime: 60 * 1000 }
  );

  return (
    <Layout>
      <h1 className="text-2xl font-bold mb-4">市场总览</h1>
      {isLoading && <p>加载中…</p>}
      {error && <QueryErrorState error={error} />}
      {data && (
        <div className="space-y-8">
          <section>
            <h2 className="text-xl font-semibold mb-2">主要指数</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {data.indices.map((idx) => (
                <div key={idx.symbol} className="p-3 border rounded-md bg-white dark:bg-gray-800 shadow-sm">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">{idx.name}</span>
                    <span>{idx.change_percent}%</span>
                  </div>
                  <div className="text-sm">最新: {idx.last}</div>
                  <div className="text-sm">成交额: {idx.turnover}</div>
                </div>
              ))}
            </div>
          </section>
          <section>
            <h2 className="text-xl font-semibold mb-2">今日摘要</h2>
            <p className="text-sm">{data.summary}</p>
          </section>
        </div>
      )}
    </Layout>
  );
}
