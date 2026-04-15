import { useRouter } from 'next/router';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import Layout from '@/components/Layout';

interface FundOverview {
  code: string;
  name: string;
  type: string;
  manager: string;
  assets_under_management: number;
  inception_date: string;
  returns: Record<string, number>;
}

interface FundAnalysis {
  nav_curve: number[];
  max_drawdown: number;
  volatility: number;
  rolling_returns: { window: string; rank: number }[];
  industry_exposure: Record<string, number>;
  style_drift: Record<string, number>;
  major_holdings: { ticker: string; name: string; weight: number }[];
  correlation_with_portfolio: number;
  conclusion: {
    suitable_scenarios: string;
    advantages: string;
    risks: string;
  };
}

export default function FundDetailPage() {
  const router = useRouter();
  const { code } = router.query as { code: string };
  const overviewQuery = useQuery(
    ['fund-overview', code],
    async () => {
      const res = await axios.get(`/api/v1/fund/${code}/overview`);
      return res.data.data as FundOverview;
    },
    { enabled: !!code }
  );
  const analysisQuery = useQuery(
    ['fund-analysis', code],
    async () => {
      const res = await axios.get(`/api/v1/fund/${code}/analysis`);
      return res.data.data as FundAnalysis;
    },
    { enabled: !!code }
  );
  return (
    <Layout>
      {(!code || overviewQuery.isLoading || analysisQuery.isLoading) && <p>加载中…</p>}
      {(overviewQuery.error || analysisQuery.error) && <p>加载失败，请刷新重试</p>}
      {overviewQuery.data && analysisQuery.data && (
        <div className="space-y-8">
          <h1 className="text-2xl font-bold mb-2">{overviewQuery.data.name}（{overviewQuery.data.code}）</h1>
          {/* Overview section */}
          <section>
            <h2 className="text-xl font-semibold mb-2">基金概览</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="p-3 border rounded-md bg-white dark:bg-gray-800 shadow-sm">
                <p className="text-sm text-gray-500 dark:text-gray-400">基金类型</p>
                <p className="text-lg font-semibold">{overviewQuery.data.type}</p>
              </div>
              <div className="p-3 border rounded-md bg-white dark:bg-gray-800 shadow-sm">
                <p className="text-sm text-gray-500 dark:text-gray-400">基金经理</p>
                <p className="text-lg font-semibold">{overviewQuery.data.manager}</p>
              </div>
              <div className="p-3 border rounded-md bg-white dark:bg-gray-800 shadow-sm">
                <p className="text-sm text-gray-500 dark:text-gray-400">管理规模</p>
                <p className="text-lg font-semibold">{(overviewQuery.data.assets_under_management / 1e9).toFixed(2)} 亿</p>
              </div>
              <div className="p-3 border rounded-md bg-white dark:bg-gray-800 shadow-sm">
                <p className="text-sm text-gray-500 dark:text-gray-400">成立日期</p>
                <p className="text-lg font-semibold">{overviewQuery.data.inception_date}</p>
              </div>
              <div className="p-3 border rounded-md bg-white dark:bg-gray-800 shadow-sm col-span-2 md:col-span-1">
                <p className="text-sm text-gray-500 dark:text-gray-400">近阶段收益</p>
                <ul className="text-sm space-y-1">
                  {Object.entries(overviewQuery.data.returns).map(([k, v]) => (
                    <li key={k}>{k}: {(v * 100).toFixed(2)}%</li>
                  ))}
                </ul>
              </div>
            </div>
          </section>
          {/* Risk/Return section */}
          <section>
            <h2 className="text-xl font-semibold mb-2">风险收益画像</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="p-3 border rounded-md bg-white dark:bg-gray-800 shadow-sm">
                <p className="text-sm text-gray-500 dark:text-gray-400">波动率</p>
                <p className="text-lg font-semibold">{(analysisQuery.data.volatility * 100).toFixed(2)}%</p>
              </div>
              <div className="p-3 border rounded-md bg-white dark:bg-gray-800 shadow-sm">
                <p className="text-sm text-gray-500 dark:text-gray-400">最大回撤</p>
                <p className="text-lg font-semibold">{(analysisQuery.data.max_drawdown * 100).toFixed(2)}%</p>
              </div>
              <div className="p-3 border rounded-md bg-white dark:bg-gray-800 shadow-sm col-span-2 md:col-span-1">
                <p className="text-sm text-gray-500 dark:text-gray-400">滚动收益排名</p>
                <ul className="text-sm space-y-1">
                  {analysisQuery.data.rolling_returns.map((item) => (
                    <li key={item.window}>{item.window}: {(item.rank * 100).toFixed(1)}%</li>
                  ))}
                </ul>
              </div>
            </div>
          </section>
          {/* Exposures section */}
          <section>
            <h2 className="text-xl font-semibold mb-2">持仓与风格画像</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-3 border rounded-md bg-white dark:bg-gray-800 shadow-sm">
                <h3 className="font-medium mb-1">行业配置</h3>
                <ul className="text-sm space-y-1">
                  {Object.entries(analysisQuery.data.industry_exposure).map(([k, v]) => (
                    <li key={k}>{k}: {(v * 100).toFixed(1)}%</li>
                  ))}
                </ul>
              </div>
              <div className="p-3 border rounded-md bg-white dark:bg-gray-800 shadow-sm">
                <h3 className="font-medium mb-1">风格漂移</h3>
                <ul className="text-sm space-y-1">
                  {Object.entries(analysisQuery.data.style_drift).map(([k, v]) => (
                    <li key={k}>{k}: {(v * 100).toFixed(1)}%</li>
                  ))}
                </ul>
              </div>
            </div>
            <div className="p-3 border rounded-md bg-white dark:bg-gray-800 shadow-sm mt-4">
              <h3 className="font-medium mb-1">重仓股（模拟）</h3>
              <ul className="text-sm space-y-1">
                {analysisQuery.data.major_holdings.map((h) => (
                  <li key={h.ticker}>
                    {h.name} ({h.ticker}): {(h.weight * 100).toFixed(1)}%
                  </li>
                ))}
              </ul>
            </div>
          </section>
          {/* Correlation and conclusion */}
          <section>
            <h2 className="text-xl font-semibold mb-2">组合关系与结论</h2>
            <div className="p-3 border rounded-md bg-white dark:bg-gray-800 shadow-sm">
              <p className="text-sm">与当前组合相关性: {analysisQuery.data.correlation_with_portfolio.toFixed(2)}</p>
              <p className="text-sm mt-2 font-medium">适合的持有场景</p>
              <p className="text-sm mb-2">{analysisQuery.data.conclusion.suitable_scenarios}</p>
              <p className="text-sm font-medium">当前主要优势</p>
              <p className="text-sm mb-2">{analysisQuery.data.conclusion.advantages}</p>
              <p className="text-sm font-medium">当前最大风险</p>
              <p className="text-sm">{analysisQuery.data.conclusion.risks}</p>
            </div>
          </section>
        </div>
      )}
    </Layout>
  );
}