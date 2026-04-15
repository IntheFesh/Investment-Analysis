import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import Layout from '@/components/Layout';

interface MarketData {
  indices: {
    symbol: string;
    name: string;
    last: number;
    change: number;
    change_percent: number;
    turnover: number;
    trend: number[];
  }[];
  signals: {
    sector_rotation: {
      strongest_sectors: string[];
      candidate_sectors: string[];
      high_crowding_sectors: string[];
    };
    fund_flows: {
      top_inflows: { sector: string; value: number }[];
      top_outflows: { sector: string; value: number }[];
    };
    breadth: {
      advancers_ratio: number;
      limit_up: number;
      limit_down: number;
      turnover_change: number;
      market_heat: number;
    };
  };
  explanations: {
    event: string;
    impact: string;
    evidence: string;
  }[];
  summary: string;
}

export default function OverviewPage() {
  // Fetch market overview using react-query.  We ignore the selected
  // market and time window for simplicity and use defaults (A股主视角, 20D).
  const { data, isLoading, error } = useQuery(['market-overview'], async () => {
    const res = await axios.get('/api/v1/market/overview', {
      params: { market_view: 'A股主视角', time_window: '20D' },
    });
    return res.data.data as MarketData;
  });

  return (
    <Layout>
      <h1 className="text-2xl font-bold mb-4">市场总览</h1>
      {isLoading && <p>加载中…</p>}
      {error && <p>加载失败，请刷新重试</p>}
      {data && (
        <div className="space-y-8">
          {/* Indices section */}
          <section>
            <h2 className="text-xl font-semibold mb-2">主要指数</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {data.indices.map((idx) => (
                <div
                  key={idx.symbol}
                  className="p-3 border rounded-md bg-white dark:bg-gray-800 shadow-sm"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">{idx.name}</span>
                    <span
                      className={
                        idx.change > 0
                          ? 'text-green-600'
                          : idx.change < 0
                          ? 'text-red-600'
                          : 'text-gray-600'
                      }
                    >
                      {idx.change_percent}%
                    </span>
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">最新: {idx.last}</div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">成交额: {idx.turnover}</div>
                </div>
              ))}
            </div>
          </section>
          {/* Signals section */}
          <section>
            <h2 className="text-xl font-semibold mb-2">市场信号</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Sector rotation */}
              <div className="p-3 border rounded-md bg-white dark:bg-gray-800 shadow-sm">
                <h3 className="font-medium mb-1">板块轮动</h3>
                <p className="text-sm">最强板块: {data.signals.sector_rotation.strongest_sectors.join(', ') || '—'}</p>
                <p className="text-sm">候选板块: {data.signals.sector_rotation.candidate_sectors.join(', ') || '—'}</p>
                <p className="text-sm">高拥挤风险: {data.signals.sector_rotation.high_crowding_sectors.join(', ') || '—'}</p>
              </div>
              {/* Fund flows */}
              <div className="p-3 border rounded-md bg-white dark:bg-gray-800 shadow-sm">
                <h3 className="font-medium mb-1">主力资金流</h3>
                <p className="text-sm">净流入: {data.signals.fund_flows.top_inflows.map((f) => `${f.sector}(${f.value.toLocaleString()})`).join(', ') || '—'}</p>
                <p className="text-sm">净流出: {data.signals.fund_flows.top_outflows.map((f) => `${f.sector}(${f.value.toLocaleString()})`).join(', ') || '—'}</p>
              </div>
              {/* Breadth */}
              <div className="p-3 border rounded-md bg-white dark:bg-gray-800 shadow-sm">
                <h3 className="font-medium mb-1">市场广度</h3>
                <p className="text-sm">上涨家数占比: {Math.round(data.signals.breadth.advancers_ratio * 100)}%</p>
                <p className="text-sm">涨停: {data.signals.breadth.limit_up}</p>
                <p className="text-sm">跌停: {data.signals.breadth.limit_down}</p>
                <p className="text-sm">成交变化: {data.signals.breadth.turnover_change}</p>
                <p className="text-sm">市场热度: {data.signals.breadth.market_heat}</p>
              </div>
            </div>
          </section>
          {/* Explanation section */}
          <section>
            <h2 className="text-xl font-semibold mb-2">市场解释</h2>
            <div className="space-y-2">
              {data.explanations.map((exp, idx) => (
                <div
                  key={idx}
                  className="p-3 border rounded-md bg-white dark:bg-gray-800 shadow-sm"
                >
                  <p className="font-medium text-sm">{exp.event}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">影响: {exp.impact}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">证据: {exp.evidence}</p>
                </div>
              ))}
            </div>
          </section>
          {/* Summary section */}
          <section>
            <h2 className="text-xl font-semibold mb-2">今日摘要</h2>
            <p className="text-sm text-gray-700 dark:text-gray-300">{data.summary}</p>
          </section>
        </div>
      )}
    </Layout>
  );
}