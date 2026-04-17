import clsx from 'clsx';

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  className?: string;
  rounded?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
}

const ROUNDED = {
  sm: 'rounded-sm',
  md: 'rounded-md',
  lg: 'rounded-lg',
  xl: 'rounded-xl',
  full: 'rounded-full',
};

export function Skeleton({ width, height = '1em', className, rounded = 'md' }: SkeletonProps) {
  return (
    <div
      aria-hidden="true"
      className={clsx('skeleton', ROUNDED[rounded], className)}
      style={{ width, height }}
    />
  );
}

export function SkeletonText({
  lines = 3,
  widths,
  className,
}: {
  lines?: number;
  widths?: string[];
  className?: string;
}) {
  return (
    <div className={clsx('flex flex-col gap-2', className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          height="0.75rem"
          width={widths?.[i] ?? (i === lines - 1 ? '60%' : '100%')}
        />
      ))}
    </div>
  );
}

export function SkeletonChart({ height = 240, className }: { height?: number; className?: string }) {
  return (
    <div className={clsx('card-skeleton flex flex-col gap-2', className)}>
      <Skeleton width="40%" height="0.875rem" />
      <Skeleton width="100%" height={height} rounded="lg" />
    </div>
  );
}
