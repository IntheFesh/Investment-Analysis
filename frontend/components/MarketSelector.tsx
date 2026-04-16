import { useAppContext } from '@/context/AppContext';

export default function MarketSelector() {
  const { bootstrapData, marketView, setMarketView } = useAppContext();
  const options = bootstrapData?.market_views ?? ['A股主视角', '港股补充视角', '全球联动视角'];

  return (
    <select
      value={marketView}
      onChange={(e) => setMarketView(e.target.value)}
      className="border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-100 text-sm rounded-md px-2 py-1"
    >
      {options.map((opt) => (
        <option key={opt} value={opt}>
          {opt}
        </option>
      ))}
    </select>
  );
}
