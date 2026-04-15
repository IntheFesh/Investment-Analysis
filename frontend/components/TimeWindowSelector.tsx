import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

/**
 * TimeWindowSelector component
 *
 * Allows the user to choose a time window for calculations.  Options
 * are fetched from the bootstrap API.  Selected value is stored
 * locally; you may lift state into a context for global usage.
 */
export default function TimeWindowSelector() {
  const { data } = useQuery(['bootstrap'], async () => {
    const res = await axios.get('/api/v1/system/bootstrap');
    return res.data.data;
  });
  const options: string[] = data?.time_windows ?? ['20D', '60D', '120D', 'YTD', '1Y'];
  const defaultValue = data?.default_settings.time_window ?? options[0];
  const [value, setValue] = useState<string>(defaultValue);
  return (
    <select
      value={value}
      onChange={(e) => setValue(e.target.value)}
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