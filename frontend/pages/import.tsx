import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import Layout from '@/components/Layout';
import QueryErrorState from '@/components/QueryErrorState';
import { importService } from '@/services/importService';

export default function ImportPage() {
  const [codes, setCodes] = useState('FUND001\nFUND002');
  const [totalCost, setTotalCost] = useState('100000');
  const [importResult, setImportResult] = useState<string | null>(null);

  const confirmMutation = useMutation((funds: any[]) =>
    importService.confirm({ funds, total_cost: parseFloat(totalCost) || 0 })
  );

  const handleCodeConfirm = () => {
    const funds = codes
      .split(/\n|,|\s+/)
      .filter(Boolean)
      .map((code) => ({ code, name: '', shares: 0, market_value: 0 }));
    confirmMutation.mutate(funds, { onSuccess: (data) => setImportResult(`创建成功，组合ID: ${data.portfolio_id}`) });
  };

  return (
    <Layout>
      <h1 className="text-2xl font-bold mb-4">导入持仓</h1>
      <textarea className="w-full h-24 border rounded-md p-2" value={codes} onChange={(e) => setCodes(e.target.value)} />
      <input className="border rounded-md px-2 py-1 mt-2" value={totalCost} onChange={(e) => setTotalCost(e.target.value)} />
      <button onClick={handleCodeConfirm} className="ml-2 px-4 py-2 text-sm rounded-md bg-indigo-600 text-white">确认创建组合</button>
      {confirmMutation.error && <QueryErrorState error={confirmMutation.error} />}
      {importResult && <p className="mt-2 text-green-600">{importResult}</p>}
    </Layout>
  );
}
