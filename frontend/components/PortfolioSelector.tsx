import { useAppContext } from '@/context/AppContext';

export default function PortfolioSelector() {
  const { bootstrapData, portfolioId, setPortfolioId } = useAppContext();
  const portfolios = bootstrapData?.portfolios ?? ['pf_default'];

  return (
    <select
      value={portfolioId}
      onChange={(e) => setPortfolioId(e.target.value)}
      className="border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-100 text-sm rounded-md px-2 py-1"
    >
      {portfolios.map((id) => (
        <option key={id} value={id}>
          {id}
        </option>
      ))}
    </select>
  );
}
