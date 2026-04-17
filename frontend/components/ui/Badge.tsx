import { ReactNode } from 'react';
import clsx from 'clsx';

export type BadgeTone =
  | 'brand'
  | 'up'
  | 'down'
  | 'warn'
  | 'neutral'
  | 'info'
  | 'danger';

interface BadgeProps {
  tone?: BadgeTone;
  variant?: 'soft' | 'solid' | 'outline';
  size?: 'xs' | 'sm' | 'md';
  children: ReactNode;
  icon?: ReactNode;
  className?: string;
}

const TONE_SOFT: Record<BadgeTone, string> = {
  brand: 'text-brand bg-brand-muted/40 border-brand-muted',
  up: 'text-up bg-up-soft border-up-muted',
  down: 'text-down bg-down-soft border-down-muted',
  warn: 'text-warn bg-warn-soft border-warn-muted',
  neutral: 'text-text-secondary bg-neutral-soft border-border',
  info: 'text-info bg-info-soft border-info-muted',
  danger: 'text-danger bg-danger-soft border-danger-muted',
};

const TONE_SOLID: Record<BadgeTone, string> = {
  brand: 'text-text-inverse bg-brand',
  up: 'text-text-inverse bg-up',
  down: 'text-text-inverse bg-down',
  warn: 'text-text-inverse bg-warn',
  neutral: 'text-text-inverse bg-text-secondary',
  info: 'text-text-inverse bg-info',
  danger: 'text-text-inverse bg-danger',
};

const TONE_OUTLINE: Record<BadgeTone, string> = {
  brand: 'text-brand border-brand',
  up: 'text-up border-up',
  down: 'text-down border-down',
  warn: 'text-warn border-warn',
  neutral: 'text-text-secondary border-border',
  info: 'text-info border-info',
  danger: 'text-danger border-danger',
};

const SIZE = {
  xs: 'text-micro px-1.5 py-0 h-4',
  sm: 'text-caption px-2 py-0 h-5',
  md: 'text-body-sm px-2.5 py-0.5 h-6',
};

export function Badge({
  tone = 'neutral',
  variant = 'soft',
  size = 'sm',
  children,
  icon,
  className,
}: BadgeProps) {
  const toneClass =
    variant === 'solid' ? TONE_SOLID[tone] : variant === 'outline' ? TONE_OUTLINE[tone] : TONE_SOFT[tone];
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 rounded-pill border whitespace-nowrap font-medium tabular',
        variant === 'outline' ? 'bg-transparent' : '',
        toneClass,
        SIZE[size],
        className
      )}
    >
      {icon}
      {children}
    </span>
  );
}
