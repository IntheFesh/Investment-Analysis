import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import Layout from '@/components/Layout';

interface ScreenshotPreview {
  preview: { code: string; name: string; shares: number; market_value: number }[];
}
interface CsvPreview {
  preview: {
    columns: string[];
    rows: { [key: string]: any }[];
  };
}

export default function ImportPage() {
  const [tab, setTab] = useState<'code' | 'screenshot' | 'csv'>('code');
  // For code import
  const [codes, setCodes] = useState('FUND001\nFUND002');
  const [totalCost, setTotalCost] = useState('100000');
  const [importResult, setImportResult] = useState<string | null>(null);
  const confirmMutation = useMutation(async (funds: any[]) => {
    const res = await axios.post('/api/v1/import/confirm', {
      funds,
      total_cost: parseFloat(totalCost) || 0,
    });
    return res.data.data.portfolio_id as string;
  });
  // For screenshot import
  const [screenshotText, setScreenshotText] = useState('');
  const [screenshotPreview, setScreenshotPreview] = useState<ScreenshotPreview | null>(null);
  const screenshotMutation = useMutation(async () => {
    const res = await axios.post('/api/v1/import/screenshot', {
      images: [screenshotText],
    });
    return res.data.data as ScreenshotPreview;
  }, {
    onSuccess: (data) => setScreenshotPreview(data),
  });
  // For csv import
  const [csvText, setCsvText] = useState('code,shares,cost\nFUND003,100,8000');
  const [csvPreview, setCsvPreview] = useState<CsvPreview | null>(null);
  const csvMutation = useMutation(async () => {
    const res = await axios.post('/api/v1/import/csv', {
      csv_data: csvText,
    });
    return res.data.data as CsvPreview;
  }, {
    onSuccess: (data) => setCsvPreview(data),
  });
  const handleCodeConfirm = () => {
    const funds = codes
      .split(/\n|,|\s+/)
      .filter((c) => c)
      .map((code) => ({ code, name: '', shares: 0, market_value: 0 }));
    confirmMutation.mutate(funds, {
      onSuccess: (portfolioId) => {
        setImportResult(`创建成功，组合ID: ${portfolioId}`);
      },
    });
  };
  const handleScreenshotConfirm = () => {
    if (!screenshotPreview) return;
    confirmMutation.mutate(screenshotPreview.preview as any, {
      onSuccess: (portfolioId) => {
        setImportResult(`创建成功，组合ID: ${portfolioId}`);
      },
    });
  };
  const handleCsvConfirm = () => {
    if (!csvPreview) return;
    // Convert rows to funds
    const funds = csvPreview.preview.rows.map((row) => ({
      code: row.code,
      name: '',
      shares: row.shares || 0,
      market_value: row.cost || 0,
    }));
    confirmMutation.mutate(funds, {
      onSuccess: (portfolioId) => {
        setImportResult(`创建成功，组合ID: ${portfolioId}`);
      },
    });
  };
  return (
    <Layout>
      <h1 className="text-2xl font-bold mb-4">导入持仓</h1>
      <div className="flex space-x-4 mb-4 border-b border-gray-200 dark:border-gray-700">
        <button
          className={`px-3 py-2 text-sm font-medium ${tab === 'code' ? 'border-b-2 border-indigo-600 text-indigo-600' : 'text-gray-600 dark:text-gray-400'}`}
          onClick={() => setTab('code')}
        >
          代码导入
        </button>
        <button
          className={`px-3 py-2 text-sm font-medium ${tab === 'screenshot' ? 'border-b-2 border-indigo-600 text-indigo-600' : 'text-gray-600 dark:text-gray-400'}`}
          onClick={() => setTab('screenshot')}
        >
          截图导入
        </button>
        <button
          className={`px-3 py-2 text-sm font-medium ${tab === 'csv' ? 'border-b-2 border-indigo-600 text-indigo-600' : 'text-gray-600 dark:text-gray-400'}`}
          onClick={() => setTab('csv')}
        >
          CSV 导入
        </button>
      </div>
      {tab === 'code' && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm mb-1">基金代码列表（换行或逗号分隔）</label>
            <textarea
              className="w-full h-24 border rounded-md p-2 dark:bg-gray-700 dark:border-gray-600"
              value={codes}
              onChange={(e) => setCodes(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm mb-1">总成本 (可选)</label>
            <input
              type="text"
              className="border rounded-md px-2 py-1 dark:bg-gray-700 dark:border-gray-600"
              value={totalCost}
              onChange={(e) => setTotalCost(e.target.value)}
            />
          </div>
          <button
            onClick={handleCodeConfirm}
            disabled={confirmMutation.isLoading}
            className="px-4 py-2 text-sm font-medium rounded-md bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {confirmMutation.isLoading ? '创建中…' : '确认创建组合'}
          </button>
        </div>
      )}
      {tab === 'screenshot' && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm mb-1">截图内容（模拟）</label>
            <textarea
              className="w-full h-24 border rounded-md p-2 dark:bg-gray-700 dark:border-gray-600"
              value={screenshotText}
              onChange={(e) => setScreenshotText(e.target.value)}
            />
          </div>
          <button
            onClick={() => screenshotMutation.mutate()}
            disabled={screenshotMutation.isLoading}
            className="px-4 py-2 text-sm font-medium rounded-md bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {screenshotMutation.isLoading ? '识别中…' : '预览'}
          </button>
          {screenshotPreview && (
            <div className="border rounded-md p-3 mt-2 bg-white dark:bg-gray-800">
              <h3 className="font-medium mb-2">识别结果预览</h3>
              <ul className="text-sm space-y-1">
                {screenshotPreview.preview.map((item, idx) => (
                  <li key={idx}>
                    {item.code} - {item.name}：份额 {item.shares}, 市值 {item.market_value}
                  </li>
                ))}
              </ul>
              <div className="mt-2">
                <label className="block text-sm mb-1">总成本 (可选)</label>
                <input
                  type="text"
                  className="border rounded-md px-2 py-1 dark:bg-gray-700 dark:border-gray-600"
                  value={totalCost}
                  onChange={(e) => setTotalCost(e.target.value)}
                />
              </div>
              <button
                onClick={handleScreenshotConfirm}
                disabled={confirmMutation.isLoading}
                className="px-4 py-2 text-sm font-medium rounded-md bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 mt-2"
              >
                {confirmMutation.isLoading ? '创建中…' : '确认创建组合'}
              </button>
            </div>
          )}
        </div>
      )}
      {tab === 'csv' && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm mb-1">CSV 数据</label>
            <textarea
              className="w-full h-24 border rounded-md p-2 dark:bg-gray-700 dark:border-gray-600"
              value={csvText}
              onChange={(e) => setCsvText(e.target.value)}
            />
          </div>
          <button
            onClick={() => csvMutation.mutate()}
            disabled={csvMutation.isLoading}
            className="px-4 py-2 text-sm font-medium rounded-md bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {csvMutation.isLoading ? '解析中…' : '预览'}
          </button>
          {csvPreview && (
            <div className="border rounded-md p-3 mt-2 bg-white dark:bg-gray-800">
              <h3 className="font-medium mb-2">CSV 预览</h3>
              <table className="min-w-max text-sm">
                <thead>
                  <tr>
                    {csvPreview.preview.columns.map((col) => (
                      <th key={col} className="px-2 py-1 border-b border-gray-200 dark:border-gray-700">
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {csvPreview.preview.rows.map((row, idx) => (
                    <tr key={idx} className="border-b border-gray-100 dark:border-gray-700">
                      {csvPreview.preview.columns.map((col) => (
                        <td key={col} className="px-2 py-1 text-center">
                          {row[col]}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="mt-2">
                <label className="block text-sm mb-1">总成本 (可选)</label>
                <input
                  type="text"
                  className="border rounded-md px-2 py-1 dark:bg-gray-700 dark:border-gray-600"
                  value={totalCost}
                  onChange={(e) => setTotalCost(e.target.value)}
                />
              </div>
              <button
                onClick={handleCsvConfirm}
                disabled={confirmMutation.isLoading}
                className="px-4 py-2 text-sm font-medium rounded-md bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 mt-2"
              >
                {confirmMutation.isLoading ? '创建中…' : '确认创建组合'}
              </button>
            </div>
          )}
        </div>
      )}
      {importResult && (
        <div className="mt-6 p-3 border rounded-md bg-green-50 border-green-200 text-green-700 dark:bg-green-900 dark:border-green-700 dark:text-green-200">
          {importResult}
        </div>
      )}
    </Layout>
  );
}