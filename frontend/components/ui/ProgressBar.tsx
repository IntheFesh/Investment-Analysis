import clsx from 'clsx';

interface ProgressBarProps {
  value: number;
  tone?: 'brand' | 'up' | 'down' | 'warn';
  size?: 'xs' | 'sm' | 'md';
  showLabel?: boolean;
  className?: string;
}

const TONE = {
  brand: 'bg-brand',
  up: 'bg-up',
  down: 'bg-down',
  warn: 'bg-warn',
};

const SIZE = {
  xs: 'h-1',
  sm: 'h-1.5',
  md: 'h-2',
};

export function ProgressBar({
  value,
  tone = 'brand',
  size = 'sm',
  showLabel = false,
  className,
}: ProgressBarProps) {
  const clamped = Math.max(0, Math.min(1, value));
  return (
    <div className={clsx('flex items-center gap-2 w-full', className)}>
      <div
        role="progressbar"
        aria-valuenow={Math.round(clamped * 100)}
        aria-valuemin={0}
        aria-valuemax={100}
        className={clsx('w-full rounded-pill bg-border-subtle overflow-hidden', SIZE[size])}
      >
        <div
          className={clsx('h-full rounded-pill transition-all duration-500 ease-out', TONE[tone])}
          style={{ width: `${clamped * 100}%` }}
        />
      </div>
      {showLabel ? (
        <div className="text-caption text-text-tertiary tabular shrink-0">
          {Math.round(clamped * 100)}%
        </div>
      ) : null}
    </div>
  );
}
