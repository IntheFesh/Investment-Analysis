import { InputHTMLAttributes, TextareaHTMLAttributes, forwardRef } from 'react';
import clsx from 'clsx';

interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'size'> {
  label?: string;
  error?: string;
  size?: 'sm' | 'md';
  leftIcon?: React.ReactNode;
  rightSlot?: React.ReactNode;
}

const INPUT_SIZE = {
  sm: 'h-8 text-body-sm px-3',
  md: 'h-9 text-body-md px-3',
};

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, error, size = 'md', leftIcon, rightSlot, className, id, ...rest },
  ref
) {
  return (
    <div className="flex flex-col gap-1">
      {label ? (
        <label htmlFor={id} className="text-caption text-text-tertiary uppercase tracking-wide">
          {label}
        </label>
      ) : null}
      <div
        className={clsx(
          'group flex items-center gap-2 bg-surface-raised border rounded-md transition-colors duration-standard',
          'hover:border-border-strong focus-within:border-brand focus-within:ring-2 focus-within:ring-brand/40',
          error ? 'border-danger' : 'border-border'
        )}
      >
        {leftIcon ? <span className="pl-3 text-text-tertiary">{leftIcon}</span> : null}
        <input
          id={id}
          ref={ref}
          {...rest}
          className={clsx(
            'flex-1 bg-transparent outline-none text-text-primary placeholder:text-text-tertiary',
            'disabled:cursor-not-allowed disabled:opacity-60 tabular',
            leftIcon ? 'pl-0' : '',
            INPUT_SIZE[size],
            className
          )}
        />
        {rightSlot ? <span className="pr-2 text-text-tertiary">{rightSlot}</span> : null}
      </div>
      {error ? <div className="text-caption text-danger">{error}</div> : null}
    </div>
  );
});

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(function Textarea(
  { label, error, className, id, rows = 6, ...rest },
  ref
) {
  return (
    <div className="flex flex-col gap-1">
      {label ? (
        <label htmlFor={id} className="text-caption text-text-tertiary uppercase tracking-wide">
          {label}
        </label>
      ) : null}
      <textarea
        id={id}
        ref={ref}
        rows={rows}
        {...rest}
        className={clsx(
          'w-full bg-surface-raised text-text-primary border rounded-md p-3 text-body-sm',
          'placeholder:text-text-tertiary resize-y font-mono tabular',
          'hover:border-border-strong focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/40',
          error ? 'border-danger' : 'border-border',
          className
        )}
      />
      {error ? <div className="text-caption text-danger">{error}</div> : null}
    </div>
  );
});
