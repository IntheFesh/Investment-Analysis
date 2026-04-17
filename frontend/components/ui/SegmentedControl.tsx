import clsx from 'clsx';

interface SegmentedControlProps<T extends string> {
  value: T;
  onChange: (value: T) => void;
  options: Array<{ value: T; label: string; hint?: string }>;
  size?: 'xs' | 'sm' | 'md';
  className?: string;
}

const SIZE = {
  xs: 'h-7 text-caption px-2',
  sm: 'h-8 text-body-sm px-3',
  md: 'h-9 text-body-md px-3.5',
};

export function SegmentedControl<T extends string>({
  value,
  onChange,
  options,
  size = 'sm',
  className,
}: SegmentedControlProps<T>) {
  return (
    <div
      role="radiogroup"
      className={clsx(
        'inline-flex items-center rounded-md border border-border bg-surface-sunken p-0.5',
        className
      )}
    >
      {options.map((opt) => {
        const active = opt.value === value;
        return (
          <button
            key={opt.value}
            role="radio"
            aria-checked={active}
            onClick={() => onChange(opt.value)}
            title={opt.hint}
            className={clsx(
              'flex items-center justify-center rounded-[5px] font-medium transition-colors duration-standard',
              SIZE[size],
              active
                ? 'bg-surface-raised text-text-primary shadow-card'
                : 'text-text-secondary hover:text-text-primary'
            )}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
