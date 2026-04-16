import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import Layout from '@/components/Layout';
import QueryErrorState from '@/components/QueryErrorState';
import { simulationService } from '@/services/simulationService';

export default function SimulationPage() {
  const [horizon, setHorizon] = useState(60);
  const [paths, setPaths] = useState(500);

  const mutation = useMutation(() =>
    simulationService.run({
      mode: 'statistical',
      horizon_days: horizon,
      num_paths: paths,
      confidence_interval: 0.95,
      bootstrap: false,
    })
  );

  return (
    <Layout>
      <h1 className="text-2xl font-bold mb-4">情景模拟</h1>
      <div className="space-y-3 mb-4">
        <input type="number" value={horizon} onChange={(e) => setHorizon(Number(e.target.value))} className="border rounded px-2 py-1" />
        <input type="number" value={paths} onChange={(e) => setPaths(Number(e.target.value))} className="border rounded px-2 py-1 ml-2" />
        <button onClick={() => mutation.mutate()} className="px-3 py-2 text-sm rounded bg-indigo-600 text-white">
          {mutation.isLoading ? '模拟中…' : '开始模拟'}
        </button>
      </div>
      {mutation.error && <QueryErrorState error={mutation.error} />}
      {mutation.data && <pre className="text-xs">{JSON.stringify(mutation.data, null, 2)}</pre>}
    </Layout>
  );
}
