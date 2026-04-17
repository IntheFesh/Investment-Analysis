import clsx from 'clsx';

interface ToggleProps {
  checked: boolean;
  onChange: (value: boolean) => void;
  label?: string;
  description?: string;
  disabled?: boolean;
  className?: string;
}

export function Toggle({ checked, onChange, label, description, disabled, className }: ToggleProps) {
  return (
    <label
      className={clsx(
        'flex items-start gap-3 cursor-pointer',
        disabled && 'opacity-60 cursor-not-allowed',
        className
      )}
    >
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => !disabled && onChange(!checked)}
        className={clsx(
          'relative inline-flex h-5 w-9 shrink-0 items-center rounded-full transition-colors duration-standard',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/60 focus-visible:ring-offset-2 focus-visible:ring-offset-surface-base',
          checked ? 'bg-brand' : 'bg-border'
        )}
      >
        <span
          className={clsx(
            'absolute left-0.5 h-4 w-4 rounded-full bg-white transition-transform duration-standard',
            checked ? 'translate-x-4' : 'translate-x-0'
          )}
        />
      </button>
      {(label || description) && (
        <div className="flex flex-col">
          {label ? <span className="text-body-sm text-text-primary">{label}</span> : null}
          {description ? <span className="text-caption text-text-tertiary">{description}</span> : null}
        </div>
      )}
    </label>
  );
}
