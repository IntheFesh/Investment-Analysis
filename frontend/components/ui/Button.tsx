import { ButtonHTMLAttributes, forwardRef, ReactNode } from 'react';
import clsx from 'clsx';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'link';
export type ButtonSize = 'xs' | 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  fullWidth?: boolean;
}

const VARIANT: Record<ButtonVariant, string> = {
  primary:
    'bg-brand text-text-inverse border border-brand hover:brightness-110 active:brightness-95 disabled:bg-border disabled:text-text-tertiary disabled:border-border',
  secondary:
    'bg-surface-raised text-text-primary border border-border hover:border-border-strong hover:bg-surface-sunken active:bg-surface-sunken disabled:text-text-tertiary',
  ghost:
    'bg-transparent text-text-secondary border border-transparent hover:bg-surface-sunken hover:text-text-primary active:bg-border-subtle disabled:text-text-tertiary',
  danger:
    'bg-danger text-text-inverse border border-danger hover:brightness-110 active:brightness-95 disabled:bg-border disabled:text-text-tertiary',
  link:
    'bg-transparent text-brand border border-transparent hover:underline disabled:text-text-tertiary',
};

const SIZE: Record<ButtonSize, string> = {
  xs: 'h-7 px-2 text-caption gap-1 rounded-md',
  sm: 'h-8 px-3 text-body-sm gap-1.5 rounded-md',
  md: 'h-9 px-4 text-body-md gap-2 rounded-md',
  lg: 'h-10 px-5 text-body-lg gap-2 rounded-lg',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  {
    variant = 'secondary',
    size = 'md',
    loading = false,
    leftIcon,
    rightIcon,
    className,
    children,
    disabled,
    fullWidth,
    ...rest
  },
  ref
) {
  return (
    <button
      {...rest}
      ref={ref}
      disabled={disabled || loading}
      className={clsx(
        'inline-flex items-center justify-center font-medium transition-colors duration-standard',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/60 focus-visible:ring-offset-2 focus-visible:ring-offset-surface-base',
        'disabled:cursor-not-allowed',
        VARIANT[variant],
        SIZE[size],
        fullWidth && 'w-full',
        className
      )}
    >
      {loading ? (
        <svg
          className="h-3.5 w-3.5 animate-spin"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
          <path
            className="opacity-80"
            fill="currentColor"
            d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z"
          />
        </svg>
      ) : leftIcon}
      <span>{children}</span>
      {rightIcon}
    </button>
  );
});
