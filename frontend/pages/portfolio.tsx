import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import Layout from '@/components/Layout';

interface PortfolioOverview {
  summary: {
    total_assets: number;
    total_cost: number;
    profit_loss: number;
    return_percent: number;
    max_drawdown: number;
    volatility: number;
    fund_count: number;
    updated_at: string;
  };
  exposures: {
    industry: Record<string, number>;
    style: Record<string, number>;
    market: Record<string, number>;
  };
  overlap_matrix: number[][];
  target_deviation: {
    risk_profile: string;
    recommended_risk_range: [number, number];
    actual_risk: number;
    deviation: number;
  };
}

interface PortfolioExportPack {
  formats: {
    json: unknown;
    markdown: string;
    csv: string;
  };
  recommendation_prompt: string;
}

interface PortfolioDiagnosis {
  diagnosis: {
    risk_type: string;
    investment_horizon: string;
    risk_warnings: string[];
    environment_fit: string;
    optimization: string[];
    evidence: Record<string, string>;
  };
}

export default function PortfolioPage() {
  const [tab, setTab] = useState<'overview' | 'diagnosis' | 'export'>('overview');
  const portfolioId = 'pf_default';
  // Fetch overview
  const overviewQuery = useQuery(['portfolio-overview', portfolioId], async () => {
    const res = await axios.get(`/api/v1/portfolio/${portfolioId}/overview`);
    return res.data.data as PortfolioOverview;
  });
  // Fetch diagnosis
  const diagnosisQuery = useQuery(['portfolio-diagnosis', portfolioId], async () => {
    const res = await axios.get(`/api/v1/portfolio/${portfolioId}/diagnosis`);
    return res.data.data as PortfolioDiagnosis;
  });

  const exportQuery = useQuery(['portfolio-export-pack', portfolioId], async () => {
    const res = await axios.get(`/api/v1/portfolio/${portfolioId}/export-pack`);
    return res.data.data as PortfolioExportPack;
  });
  const markdownPreview = useMemo(
    () => exportQuery.data?.formats.markdown.split('\n').slice(0, 8).join('\n') ?? '',
    [exportQuery.data]
  );
  return (
    <Layout>
      <h1 className="text-2xl font-bold mb-4">基金组合</h1>
      <div className="flex space-x-4 mb-4 border-b border-gray-200 dark:border-gray-700">
          <button
            className={`px-3 py-2 text-sm font-medium ${tab === 'overview' ? 'border-b-2 border-indigo-600 text-indigo-600' : 'text-gray-600 dark:text-gray-400'}`}
            onClick={() => setTab('overview')}
          >
            组合看穿
          </button>
          <button
            className={`px-3 py-2 text-sm font-medium ${tab === 'diagnosis' ? 'border-b-2 border-indigo-600 text-indigo-600' : 'text-gray-600 dark:text-gray-400'}`}
            onClick={() => setTab('diagnosis')}
          >
            组合诊断
          </button>
          <button
            className={`px-3 py-2 text-sm font-medium ${tab === 'export' ? 'border-b-2 border-indigo-600 text-indigo-600' : 'text-gray-600 dark:text-gray-400'}`}
            onClick={() => setTab('export')}
          >
            AI 导出
          </button>
      </div>
      {tab === 'overview' && (
        <div>
          {overviewQuery.isLoading && <p>加载中…</p>}
          {overviewQuery.error && <p>加载失败，请刷新重试</p>}
          {overviewQuery.data && (
            <div className="space-y-8">
              {/* Summary */}
              <section>
                <h2 className="text-xl font-semibold mb-2">组合摘要</h2>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div className="p-3 border rounded-md bg-white dark:bg-gray-800 shadow-sm">
                    <p className="text-sm text-gray-500 dark:text-gray-400">总资产</p>
                    <p className="text-lg font-semibold">{overviewQuery.data.summary.total_assets.toLocaleString()}</p>
                  </div>
                  <div className="p-3 border rounded-md bg-white dark:bg-gray-800 shadow-sm">
                    <p className="text-sm text-gray-500 dark:text-gray-400">总成本</p>
                    <p className="text-lg font-semibold">{overviewQuery.data.summary.total_cost.toLocaleString()}</p>
                  </div>
                  <div className="p-3 border rounded-md bg-white dark:bg-gray-800 shadow-sm">
                    <p className="text-sm text-gray-500 dark:text-gray-400">浮盈浮亏</p>
                    <p className="text-lg font-semibold">{overviewQuery.data.summary.profit_loss.toLocaleString()}</p>
                  </div>
                  <div className="p-3 border rounded-md bg-white dark:bg-gray-800 shadow-sm">
                    <p className="text-sm text-gray-500 dark:text-gray-400">收益率</p>
                    <p className="text-lg font-semibold">{(overviewQuery.data.summary.return_percent * 100).toFixed(2)}%</p>
                  </div>
                  <div className="p-3 border rounded-md bg-white dark:bg-gray-800 shadow-sm">
                    <p className="text-sm text-gray-500 dark:text-gray-400">最大回撤</p>
                    <p className="text-lg font-semibold">{(overviewQuery.data.summary.max_drawdown * 100).toFixed(2)}%</p>
                  </div>
                  <div className="p-3 border rounded-md bg-white dark:bg-gray-800 shadow-sm">
                    <p className="text-sm text-gray-500 dark:text-gray-400">波动率</p>
                    <p className="text-lg font-semibold">{(overviewQuery.data.summary.volatility * 100).toFixed(2)}%</p>
                  </div>
                </div>
              </section>
              {/* Exposures */}
              <section>
                <h2 className="text-xl font-semibold mb-2">底层暴露</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Industry exposures */}
                  <div className="p-3 border rounded-md bg-white dark:bg-gray-800 shadow-sm">
                    <h3 className="font-medium mb-1">行业暴露</h3>
                    <ul className="text-sm space-y-1">
                      {Object.entries(overviewQuery.data.exposures.industry).map(([k, v]) => (
                        <li key={k}>
                          {k}: {(v * 100).toFixed(1)}%
                        </li>
                      ))}
                    </ul>
                  </div>
                  {/* Style exposures */}
                  <div className="p-3 border rounded-md bg-white dark:bg-gray-800 shadow-sm">
                    <h3 className="font-medium mb-1">风格暴露</h3>
                    <ul className="text-sm space-y-1">
                      {Object.entries(overviewQuery.data.exposures.style).map(([k, v]) => (
                        <li key={k}>
                          {k}: {(v * 100).toFixed(1)}%
                        </li>
                      ))}
                    </ul>
                  </div>
                  {/* Market exposures */}
                  <div className="p-3 border rounded-md bg-white dark:bg-gray-800 shadow-sm">
                    <h3 className="font-medium mb-1">市场暴露</h3>
                    <ul className="text-sm space-y-1">
                      {Object.entries(overviewQuery.data.exposures.market).map(([k, v]) => (
                        <li key={k}>
                          {k}: {(v * 100).toFixed(1)}%
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </section>
              {/* Overlap matrix */}
              <section>
                <h2 className="text-xl font-semibold mb-2">基金重叠热力图</h2>
                <div className="overflow-x-auto">
                  <table className="min-w-max text-sm">
                    <tbody>
                      {overviewQuery.data.overlap_matrix.map((row, i) => (
                        <tr key={i} className="border-b border-gray-100 dark:border-gray-700">
                          {row.map((val, j) => (
                            <td
                              key={j}
                              className="px-2 py-1 text-center"
                              style={{ backgroundColor: `rgba(99, 102, 241, ${Math.abs(val)})` }}
                            >
                              {val.toFixed(2)}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
              {/* Target deviation */}
              <section>
                <h2 className="text-xl font-semibold mb-2">目标画像偏差</h2>
                <div className="p-3 border rounded-md bg-white dark:bg-gray-800 shadow-sm">
                  <p className="text-sm">风险画像: {overviewQuery.data.target_deviation.risk_profile}</p>
                  <p className="text-sm">
                    建议风险区间: {overviewQuery.data.target_deviation.recommended_risk_range[0].toFixed(2)}–{overviewQuery.data.target_deviation.recommended_risk_range[1].toFixed(2)}
                  </p>
                  <p className="text-sm">实际风险: {overviewQuery.data.target_deviation.actual_risk.toFixed(2)}</p>
                  <p className="text-sm">偏离度: {overviewQuery.data.target_deviation.deviation.toFixed(2)}</p>
                </div>
              </section>
            </div>
          )}
        </div>
      )}
      {tab === 'diagnosis' && (
        <div>
          {diagnosisQuery.isLoading && <p>加载中…</p>}
          {diagnosisQuery.error && <p>加载失败，请刷新重试</p>}
          {diagnosisQuery.data && (
            <div className="space-y-8">
              <section>
                <h2 className="text-xl font-semibold mb-2">风险提示</h2>
                <ul className="list-disc pl-5 space-y-1 text-sm">
                  {diagnosisQuery.data.diagnosis.risk_warnings.map((msg, idx) => (
                    <li key={idx}>{msg}</li>
                  ))}
                </ul>
              </section>
              <section>
                <h2 className="text-xl font-semibold mb-2">环境适配度</h2>
                <p className="text-sm">{diagnosisQuery.data.diagnosis.environment_fit}</p>
              </section>
              <section>
                <h2 className="text-xl font-semibold mb-2">优化方向</h2>
                <ul className="list-disc pl-5 space-y-1 text-sm">
                  {diagnosisQuery.data.diagnosis.optimization.map((msg, idx) => (
                    <li key={idx}>{msg}</li>
                  ))}
                </ul>
              </section>
              <section>
                <h2 className="text-xl font-semibold mb-2">支持证据</h2>
                <ul className="list-disc pl-5 space-y-1 text-sm">
                  {Object.entries(diagnosisQuery.data.diagnosis.evidence).map(([k, v]) => (
                    <li key={k}>{k}: {v}</li>
                  ))}
                </ul>
              </section>
            </div>
          )}
        </div>
      )}
      {tab === 'export' && (
        <div>
          {exportQuery.isLoading && <p>加载中…</p>}
          {exportQuery.error && <p>加载失败，请刷新重试</p>}
          {exportQuery.data && (
            <div className="space-y-6">
              <section className="p-4 border rounded-md bg-white dark:bg-gray-800 shadow-sm">
                <h2 className="text-xl font-semibold mb-2">导出格式预览</h2>
                <p className="text-sm mb-2">JSON / Markdown / CSV 已在后端生成预览；PNG 将通过异步导出任务提供。</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <pre className="text-xs overflow-auto p-2 rounded bg-gray-100 dark:bg-gray-900">{JSON.stringify(exportQuery.data.formats.json, null, 2)}</pre>
                  <pre className="text-xs overflow-auto p-2 rounded bg-gray-100 dark:bg-gray-900">{markdownPreview}</pre>
                </div>
                <details className="mt-3">
                  <summary className="cursor-pointer text-sm font-medium">查看 CSV 预览</summary>
                  <pre className="text-xs overflow-auto p-2 rounded bg-gray-100 dark:bg-gray-900 mt-2">{exportQuery.data.formats.csv}</pre>
                </details>
              </section>

              <section className="p-4 border rounded-md bg-white dark:bg-gray-800 shadow-sm">
                <h2 className="text-xl font-semibold mb-2">推荐提示词</h2>
                <textarea
                  className="w-full h-28 border rounded-md p-2 dark:bg-gray-700 dark:border-gray-600"
                  value={exportQuery.data.recommendation_prompt}
                  readOnly
                />
              </section>
            </div>
          )}
        </div>
      )}
    </Layout>
  );
}