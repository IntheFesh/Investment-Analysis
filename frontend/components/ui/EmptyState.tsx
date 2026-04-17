import { ReactNode } from 'react';
import clsx from 'clsx';

interface EmptyStateProps {
  title: string;
  description?: ReactNode;
  icon?: ReactNode;
  action?: ReactNode;
  className?: string;
  compact?: boolean;
}

const DefaultIcon = (
  <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.3">
    <path d="M3 7l9-4 9 4-9 4-9-4z" strokeLinejoin="round" />
    <path d="M3 12l9 4 9-4" strokeLinejoin="round" />
    <path d="M3 17l9 4 9-4" strokeLinejoin="round" />
  </svg>
);

export function EmptyState({
  title,
  description,
  icon,
  action,
  className,
  compact = false,
}: EmptyStateProps) {
  return (
    <div
      className={clsx(
        'flex flex-col items-center justify-center text-center gap-3 text-text-secondary',
        compact ? 'py-6 px-4' : 'py-10 px-6',
        className
      )}
    >
      <div className="text-text-tertiary">{icon ?? DefaultIcon}</div>
      <div className="text-heading-sm text-text-primary">{title}</div>
      {description ? <div className="text-body-sm text-text-tertiary max-w-md">{description}</div> : null}
      {action ? <div className="mt-1">{action}</div> : null}
    </div>
  );
}
