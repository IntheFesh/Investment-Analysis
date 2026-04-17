import { ReactNode, HTMLAttributes } from 'react';
import clsx from 'clsx';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  variant?: 'raised' | 'sunken' | 'outline';
  interactive?: boolean;
  padding?: 'none' | 'compact' | 'default' | 'relaxed';
}

const PADDING: Record<NonNullable<CardProps['padding']>, string> = {
  none: '',
  compact: 'p-3',
  default: 'p-4',
  relaxed: 'p-6',
};

export function Card({
  children,
  variant = 'raised',
  interactive = false,
  padding = 'default',
  className,
  ...rest
}: CardProps) {
  return (
    <div
      {...rest}
      className={clsx(
        'card rounded-card',
        variant === 'sunken' && 'bg-surface-sunken',
        variant === 'outline' && 'bg-transparent shadow-none',
        interactive && 'card-interactive cursor-pointer transition-transform hover:-translate-y-[1px]',
        PADDING[padding],
        className
      )}
    >
      {children}
    </div>
  );
}

interface CardHeaderProps {
  title: ReactNode;
  subtitle?: ReactNode;
  action?: ReactNode;
  icon?: ReactNode;
  className?: string;
}

export function CardHeader({ title, subtitle, action, icon, className }: CardHeaderProps) {
  return (
    <div className={clsx('flex items-start justify-between gap-3', className)}>
      <div className="flex items-start gap-2.5">
        {icon ? <div className="text-brand mt-0.5">{icon}</div> : null}
        <div>
          <div className="text-heading-sm text-text-primary">{title}</div>
          {subtitle ? (
            <div className="text-caption text-text-tertiary mt-0.5">{subtitle}</div>
          ) : null}
        </div>
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}

interface MetricProps {
  label: string;
  value: ReactNode;
  tone?: 'primary' | 'up' | 'down' | 'neutral' | 'warn';
  delta?: ReactNode;
  hint?: string;
  className?: string;
  size?: 'md' | 'lg' | 'xl';
}

const TONE: Record<NonNullable<MetricProps['tone']>, string> = {
  primary: 'text-text-primary',
  up: 'text-up',
  down: 'text-down',
  neutral: 'text-text-secondary',
  warn: 'text-warn',
};

const SIZE: Record<NonNullable<MetricProps['size']>, string> = {
  md: 'text-metric-md',
  lg: 'text-metric-lg',
  xl: 'text-metric-xl',
};

export function Metric({ label, value, tone = 'primary', delta, hint, className, size = 'lg' }: MetricProps) {
  return (
    <div className={clsx('flex flex-col gap-1', className)}>
      <div className="text-micro uppercase tracking-wider text-text-tertiary">{label}</div>
      <div className={clsx('tabular font-semibold', SIZE[size], TONE[tone])}>{value}</div>
      {delta ? <div className="text-caption tabular text-text-secondary">{delta}</div> : null}
      {hint ? <div className="text-caption text-text-tertiary">{hint}</div> : null}
    </div>
  );
}
