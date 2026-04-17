import { useAppContext } from '@/context/AppContext';
import clsx from 'clsx';

const ICONS = {
  dark: (
    <svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M15 11.5A6 6 0 018.5 5a6 6 0 109.5 6.5 6 6 0 01-3 0z" strokeLinejoin="round" />
    </svg>
  ),
  light: (
    <svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <circle cx="10" cy="10" r="3.4" />
      <path d="M10 3v1.5M10 15.5V17M3 10h1.5M15.5 10H17M5 5l1.1 1.1M13.9 13.9L15 15M5 15l1.1-1.1M13.9 6.1L15 5" strokeLinecap="round" />
    </svg>
  ),
  system: (
    <svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <rect x="3" y="4" width="14" height="9" rx="1.5" />
      <path d="M7 17h6M10 13v4" strokeLinecap="round" />
    </svg>
  ),
};

const LABELS = { dark: '深色', light: '浅色', system: '跟随' };

export function ThemeToggle() {
  const { theme, setTheme } = useAppContext();
  const options: Array<'dark' | 'light' | 'system'> = ['dark', 'light', 'system'];
  return (
    <div className="inline-flex items-center rounded-md border border-border bg-surface-sunken p-0.5">
      {options.map((opt) => (
        <button
          key={opt}
          aria-pressed={theme === opt}
          onClick={() => setTheme(opt)}
          title={`${LABELS[opt]}模式`}
          className={clsx(
            'inline-flex items-center gap-1 px-2 h-7 rounded-[5px] text-caption transition-colors duration-standard',
            theme === opt
              ? 'bg-surface-raised text-text-primary shadow-card'
              : 'text-text-tertiary hover:text-text-primary'
          )}
        >
          {ICONS[opt]}
          <span>{LABELS[opt]}</span>
        </button>
      ))}
    </div>
  );
}
