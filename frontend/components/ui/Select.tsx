import { SelectHTMLAttributes, forwardRef } from 'react';
import clsx from 'clsx';

interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'size'> {
  options: SelectOption[];
  size?: 'sm' | 'md';
  label?: string;
  error?: string;
}

const SIZE = {
  sm: 'h-8 text-body-sm pl-3 pr-8 rounded-md',
  md: 'h-9 text-body-md pl-3 pr-9 rounded-md',
};

export const Select = forwardRef<HTMLSelectElement, SelectProps>(function Select(
  { options, size = 'md', label, error, className, id, ...rest },
  ref
) {
  return (
    <div className="flex flex-col gap-1">
      {label ? (
        <label htmlFor={id} className="text-caption text-text-tertiary uppercase tracking-wide">
          {label}
        </label>
      ) : null}
      <div className="relative">
        <select
          ref={ref}
          id={id}
          {...rest}
          className={clsx(
            'block w-full appearance-none bg-surface-raised text-text-primary border transition-colors duration-standard',
            'hover:border-border-strong focus:border-brand focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/40',
            'disabled:cursor-not-allowed disabled:opacity-60',
            error ? 'border-danger' : 'border-border',
            SIZE[size],
            className
          )}
        >
          {options.map((opt) => (
            <option key={opt.value} value={opt.value} disabled={opt.disabled}>
              {opt.label}
            </option>
          ))}
        </select>
        <svg
          aria-hidden
          viewBox="0 0 20 20"
          className="pointer-events-none absolute right-2 top-1/2 h-4 w-4 -translate-y-1/2 text-text-tertiary"
          fill="none"
          stroke="currentColor"
        >
          <path d="M6 8l4 4 4-4" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
      {error ? <div className="text-caption text-danger">{error}</div> : null}
    </div>
  );
});
