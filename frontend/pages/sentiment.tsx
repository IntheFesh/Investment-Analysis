import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import Layout from '@/components/Layout';

interface SentimentData {
  short_term_score: number;
  mid_term_score: number;
  short_term_label: string;
  mid_term_label: string;
  factors: {
    name: string;
    score: number;
    direction: string;
    driver: string;
  }[];
  time_series: {
    date: string;
    short: number;
    mid: number;
  }[];
  contributions: Record<string, number>;
}

export default function SentimentPage() {
  const { data, isLoading, error } = useQuery(['sentiment-overview'], async () => {
    const res = await axios.get('/api/v1/sentiment/overview', {
      params: { market_view: 'A股主视角', time_window: '20D' },
    });
    return res.data.data as SentimentData;
  });
  return (
    <Layout>
      <h1 className="text-2xl font-bold mb-4">风险情绪</h1>
      {isLoading && <p>加载中…</p>}
      {error && <p>加载失败，请刷新重试</p>}
      {data && (
        <div className="space-y-8">
          {/* Gauges */}
          <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 border rounded-md bg-white dark:bg-gray-800 shadow-sm flex flex-col items-center">
              <h2 className="font-medium mb-2">短期情绪</h2>
              <div className="text-4xl font-bold mb-1">{data.short_term_score}</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">{data.short_term_label}</div>
            </div>
            <div className="p-4 border rounded-md bg-white dark:bg-gray-800 shadow-sm flex flex-col items-center">
              <h2 className="font-medium mb-2">中长期情绪</h2>
              <div className="text-4xl font-bold mb-1">{data.mid_term_score}</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">{data.mid_term_label}</div>
            </div>
          </section>
          {/* Factor breakdown */}
          <section>
            <h2 className="text-xl font-semibold mb-2">因子拆解</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {data.factors.map((factor) => (
                <div
                  key={factor.name}
                  className="p-3 border rounded-md bg-white dark:bg-gray-800 shadow-sm"
                >
                  <p className="font-medium">{factor.name}</p>
                  <p className="text-sm">得分: {factor.score}</p>
                  <p className="text-sm">
                    方向: {factor.direction === 'up' ? '上升' : '下降'}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">驱动: {factor.driver}</p>
                </div>
              ))}
            </div>
          </section>
          {/* Time series */}
          <section>
            <h2 className="text-xl font-semibold mb-2">情绪时间序列</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700 text-sm">
                <thead>
                  <tr>
                    <th className="px-2 py-1">日期</th>
                    <th className="px-2 py-1">短期</th>
                    <th className="px-2 py-1">中长期</th>
                  </tr>
                </thead>
                <tbody>
                  {data.time_series.map((row) => (
                    <tr key={row.date} className="border-b border-gray-100 dark:border-gray-700">
                      <td className="px-2 py-1 whitespace-nowrap">{row.date}</td>
                      <td className="px-2 py-1">{row.short}</td>
                      <td className="px-2 py-1">{row.mid}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
          {/* Contributions */}
          <section>
            <h2 className="text-xl font-semibold mb-2">因子贡献权重</h2>
            <ul className="list-disc pl-5 space-y-1">
              {Object.entries(data.contributions).map(([name, weight]) => (
                <li key={name} className="text-sm">
                  {name}: {Math.round(weight * 100)}%
                </li>
              ))}
            </ul>
          </section>
        </div>
      )}
    </Layout>
  );
}