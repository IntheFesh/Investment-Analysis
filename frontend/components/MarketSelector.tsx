import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

/**
 * MarketSelector component
 *
 * Renders a drop-down for selecting the market view.  It retrieves the
 * available options from the bootstrap endpoint and falls back to a
 * predefined list if the request fails.  The selected value is stored
 * in local component state; in a full implementation this could be
 * lifted into a global context.
 */
export default function MarketSelector() {
  const { data } = useQuery(['bootstrap'], async () => {
    const res = await axios.get('/api/v1/system/bootstrap');
    return res.data.data;
  });
  const options: string[] = data?.market_views ?? ['A股主视角', '港股补充视角', '全球联动视角'];
  const defaultValue = data?.default_settings.market_view ?? options[0];
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