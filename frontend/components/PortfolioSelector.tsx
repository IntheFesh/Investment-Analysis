import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

/**
 * PortfolioSelector component
 *
 * Provides a drop‑down for selecting one of the user's portfolios.
 * Currently the bootstrap endpoint returns an empty list by default, so
 * the component falls back to a placeholder entry.  In a complete
 * application this selection would drive subsequent API calls.
 */
export default function PortfolioSelector() {
  const { data } = useQuery(['bootstrap'], async () => {
    const res = await axios.get('/api/v1/system/bootstrap');
    return res.data.data;
  });
  const portfolios: string[] = data?.portfolios ?? ['pf_default'];
  const [value, setValue] = useState<string>(portfolios[0]);
  return (
    <select
      value={value}
      onChange={(e) => setValue(e.target.value)}
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