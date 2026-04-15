import { useState, useEffect } from 'react';

/**
 * ResearchModeSwitch component
 *
 * Toggles between "轻量模式" and "研究模式".  The current mode is
 * persisted in localStorage so that the setting survives page reloads.
 * In a more complete implementation this state would be stored in
 * global context or synchronised with the server via the settings API.
 */
export default function ResearchModeSwitch() {
  const [mode, setMode] = useState<string>('轻量模式');

  useEffect(() => {
    // Load initial mode from localStorage if available
    const stored = typeof window !== 'undefined' && localStorage.getItem('research_mode');
    if (stored) {
      setMode(stored);
    }
  }, []);

  useEffect(() => {
    // Persist mode changes
    if (typeof window !== 'undefined') {
      localStorage.setItem('research_mode', mode);
    }
  }, [mode]);

  const toggleMode = () => {
    setMode((prev) => (prev === '轻量模式' ? '研究模式' : '轻量模式'));
  };

  return (
    <button
      onClick={toggleMode}
      className="px-3 py-2 text-sm font-medium rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-600"
    >
      {mode}
    </button>
  );
}