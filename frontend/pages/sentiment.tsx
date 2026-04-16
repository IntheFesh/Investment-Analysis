import { useQuery } from '@tanstack/react-query';
import Layout from '@/components/Layout';
import QueryErrorState from '@/components/QueryErrorState';
import { useAppContext } from '@/context/AppContext';
import { sentimentService } from '@/services/sentimentService';

interface SentimentData {
  short_term_score: number;
  mid_term_score: number;
  short_term_label: string;
  mid_term_label: string;
}

export default function SentimentPage() {
  const { marketView, timeWindow } = useAppContext();
  const { data, isLoading, error } = useQuery(
    ['sentiment-overview', marketView, timeWindow],
    () => sentimentService.getOverview({ market_view: marketView, time_window: timeWindow }) as Promise<SentimentData>,
    { staleTime: 60 * 1000 }
  );

  return (
    <Layout>
      <h1 className="text-2xl font-bold mb-4">风险情绪</h1>
      {isLoading && <p>加载中…</p>}
      {error && <QueryErrorState error={error} />}
      {data && (
        <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 border rounded-md bg-white dark:bg-gray-800 shadow-sm flex flex-col items-center">
            <h2 className="font-medium mb-2">短期情绪</h2>
            <div className="text-4xl font-bold mb-1">{data.short_term_score}</div>
            <div className="text-sm">{data.short_term_label}</div>
          </div>
          <div className="p-4 border rounded-md bg-white dark:bg-gray-800 shadow-sm flex flex-col items-center">
            <h2 className="font-medium mb-2">中长期情绪</h2>
            <div className="text-4xl font-bold mb-1">{data.mid_term_score}</div>
            <div className="text-sm">{data.mid_term_label}</div>
          </div>
        </section>
      )}
    </Layout>
  );
}
