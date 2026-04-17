import { ReactNode } from 'react';
import clsx from 'clsx';

interface Tab {
  id: string;
  label: ReactNode;
  badge?: ReactNode;
  disabled?: boolean;
}

interface TabsProps {
  value: string;
  onChange: (id: string) => void;
  items: Tab[];
  size?: 'sm' | 'md';
  variant?: 'underline' | 'segment';
  className?: string;
}

export function Tabs({
  value,
  onChange,
  items,
  size = 'md',
  variant = 'underline',
  className,
}: TabsProps) {
  if (variant === 'segment') {
    return (
      <div
        role="tablist"
        className={clsx(
          'inline-flex items-center gap-1 rounded-md border border-border bg-surface-sunken p-1',
          className
        )}
      >
        {items.map((tab) => {
          const active = value === tab.id;
          return (
            <button
              key={tab.id}
              role="tab"
              disabled={tab.disabled}
              aria-selected={active}
              onClick={() => onChange(tab.id)}
              className={clsx(
                'flex items-center gap-1.5 rounded-md px-3 font-medium transition-colors duration-standard',
                size === 'sm' ? 'h-7 text-body-sm' : 'h-8 text-body-md',
                active
                  ? 'bg-surface-raised text-text-primary shadow-card'
                  : 'text-text-secondary hover:text-text-primary'
              )}
            >
              <span>{tab.label}</span>
              {tab.badge}
            </button>
          );
        })}
      </div>
    );
  }

  return (
    <div
      role="tablist"
      className={clsx('flex items-end gap-4 border-b border-border', className)}
    >
      {items.map((tab) => {
        const active = value === tab.id;
        return (
          <button
            key={tab.id}
            role="tab"
            disabled={tab.disabled}
            aria-selected={active}
            onClick={() => onChange(tab.id)}
            className={clsx(
              'relative inline-flex items-center gap-1.5 py-2 font-medium transition-colors duration-standard',
              size === 'sm' ? 'text-body-sm' : 'text-body-md',
              active
                ? 'text-text-primary after:absolute after:inset-x-0 after:-bottom-px after:h-0.5 after:bg-brand'
                : 'text-text-secondary hover:text-text-primary'
            )}
          >
            <span>{tab.label}</span>
            {tab.badge}
          </button>
        );
      })}
    </div>
  );
}
