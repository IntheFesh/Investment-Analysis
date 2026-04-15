import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import Layout from '@/components/Layout';

interface SimulationResult {
  heatmap: Record<string, Record<string, number>>;
  extreme_curve: { day: number; best_return: number; worst_return: number }[];
  sensitivity: {
    factor: string;
    expected_change: number;
    loss_risk: number;
    affected_exposure: string;
  }[];
  max_drawdown: number;
}

export default function SimulationPage() {
  const [horizon, setHorizon] = useState(60);
  const [paths, setPaths] = useState(500);
  const mutation = useMutation(async () => {
    const res = await axios.post('/api/v1/simulation/run', {
      mode: 'statistical',
      horizon_days: horizon,
      num_paths: paths,
      confidence_interval: 0.95,
      bootstrap: false,
    });
    return res.data.data as SimulationResult;
  });
  const handleRun = () => {
    mutation.mutate();
  };
  return (
    <Layout>
      <h1 className="text-2xl font-bold mb-4">情景模拟</h1>
      <div className="space-y-4 mb-8 p-4 border rounded-md bg-white dark:bg-gray-800 shadow-sm">
        <h2 className="text-xl font-semibold mb-2">参数设置</h2>
        <div className="flex flex-col md:flex-row space-y-3 md:space-y-0 md:space-x-4 items-center">
          <div>
            <label className="block text-sm mb-1">模拟期限 (天)</label>
            <input
              type="number"
              className="border rounded-md px-2 py-1 w-32 dark:bg-gray-700 dark:border-gray-600"
              value={horizon}
              min={10}
              max={120}
              step={10}
              onChange={(e) => setHorizon(parseInt(e.target.value, 10))}
            />
          </div>
          <div>
            <label className="block text-sm mb-1">模拟路径数</label>
            <input
              type="number"
              className="border rounded-md px-2 py-1 w-32 dark:bg-gray-700 dark:border-gray-600"
              value={paths}
              min={100}
              max={2000}
              step={100}
              onChange={(e) => setPaths(parseInt(e.target.value, 10))}
            />
          </div>
          <button
            onClick={handleRun}
            disabled={mutation.isLoading}
            className="px-4 py-2 text-sm font-medium rounded-md bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {mutation.isLoading ? '模拟中…' : '开始模拟'}
          </button>
        </div>
      </div>
      {mutation.data && (
        <div className="space-y-8">
          {/* Heatmap */}
          <section>
            <h2 className="text-xl font-semibold mb-2">收益分布热力图</h2>
            {Object.entries(mutation.data.heatmap).map(([horizonKey, buckets]) => (
              <div key={horizonKey} className="mb-4">
                <h3 className="font-medium mb-1">{horizonKey}</h3>
                <table className="min-w-max text-sm">
                  <thead>
                    <tr>
                      {Object.keys(buckets).map((label) => (
                        <th key={label} className="px-2 py-1 border-b border-gray-200 dark:border-gray-700">
                          {label}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      {Object.values(buckets).map((prob, idx) => (
                        <td
                          key={idx}
                          className="px-2 py-1 text-center"
                          style={{ backgroundColor: `rgba(99, 102, 241, ${prob})` }}
                        >
                          {(prob * 100).toFixed(1)}%
                        </td>
                      ))}
                    </tr>
                  </tbody>
                </table>
              </div>
            ))}
          </section>
          {/* Extreme curve */}
          <section>
            <h2 className="text-xl font-semibold mb-2">最优/最差回报曲线</h2>
            <table className="min-w-max text-sm">
              <thead>
                <tr>
                  <th className="px-2 py-1 border-b border-gray-200 dark:border-gray-700">天数</th>
                  <th className="px-2 py-1 border-b border-gray-200 dark:border-gray-700">最佳回报</th>
                  <th className="px-2 py-1 border-b border-gray-200 dark:border-gray-700">最差回报</th>
                </tr>
              </thead>
              <tbody>
                {mutation.data.extreme_curve.map((row) => (
                  <tr key={row.day} className="border-b border-gray-100 dark:border-gray-700">
                    <td className="px-2 py-1 text-center">{row.day}</td>
                    <td className="px-2 py-1 text-center">{(row.best_return * 100).toFixed(1)}%</td>
                    <td className="px-2 py-1 text-center">{(row.worst_return * 100).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
          {/* Sensitivity */}
          <section>
            <h2 className="text-xl font-semibold mb-2">情景敏感度表</h2>
            <table className="min-w-max text-sm">
              <thead>
                <tr>
                  <th className="px-2 py-1 border-b border-gray-200 dark:border-gray-700">因素</th>
                  <th className="px-2 py-1 border-b border-gray-200 dark:border-gray-700">预期变动</th>
                  <th className="px-2 py-1 border-b border-gray-200 dark:border-gray-700">损失风险</th>
                  <th className="px-2 py-1 border-b border-gray-200 dark:border-gray-700">受影响暴露</th>
                </tr>
              </thead>
              <tbody>
                {mutation.data.sensitivity.map((item, idx) => (
                  <tr key={idx} className="border-b border-gray-100 dark:border-gray-700">
                    <td className="px-2 py-1 text-center">{item.factor}</td>
                    <td className="px-2 py-1 text-center">{(item.expected_change * 100).toFixed(1)}%</td>
                    <td className="px-2 py-1 text-center">{(item.loss_risk * 100).toFixed(1)}%</td>
                    <td className="px-2 py-1 text-center">{item.affected_exposure}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
          {/* Max drawdown */}
          <section>
            <h2 className="text-xl font-semibold mb-2">最大回撤</h2>
            <p className="text-sm">{(mutation.data.max_drawdown * 100).toFixed(2)}%</p>
          </section>
        </div>
      )}
    </Layout>
  );
}