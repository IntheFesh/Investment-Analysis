import { useAppContext } from '@/context/AppContext';

export default function TimeWindowSelector() {
  const { bootstrapData, timeWindow, setTimeWindow } = useAppContext();
  const options = bootstrapData?.time_windows ?? ['20D', '60D', '120D', 'YTD', '1Y'];

  return (
    <select
      value={timeWindow}
      onChange={(e) => setTimeWindow(e.target.value)}
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
