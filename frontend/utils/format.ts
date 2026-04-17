/**
 * Number formatters. All callers go through here so tabular-num alignment,
 * sign rendering, and NaN handling stay consistent.
 */

const NBSP = '\u00A0';

export const isFiniteNumber = (x: unknown): x is number =>
  typeof x === 'number' && Number.isFinite(x);

export const formatNumber = (
  value: unknown,
  options: { digits?: number; placeholder?: string } = {}
): string => {
  const { digits = 2, placeholder = '—' } = options;
  if (!isFiniteNumber(value)) return placeholder;
  return value.toLocaleString('zh-CN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
};

export const formatSignedNumber = (
  value: unknown,
  options: { digits?: number; placeholder?: string } = {}
): string => {
  const { digits = 2, placeholder = '—' } = options;
  if (!isFiniteNumber(value)) return placeholder;
  const formatted = formatNumber(Math.abs(value), { digits });
  if (value > 0) return `+${formatted}`;
  if (value < 0) return `-${formatted}`;
  return formatted;
};

export const formatPercent = (
  value: unknown,
  options: { digits?: number; placeholder?: string; signed?: boolean; scale?: boolean } = {}
): string => {
  const { digits = 2, placeholder = '—', signed = true, scale = false } = options;
  if (!isFiniteNumber(value)) return placeholder;
  const pct = scale ? value * 100 : value;
  const absStr = Math.abs(pct).toFixed(digits);
  if (!signed) return `${pct.toFixed(digits)}%`;
  if (pct > 0) return `+${absStr}%`;
  if (pct < 0) return `-${absStr}%`;
  return `${absStr}%`;
};

export const formatCurrency = (
  value: unknown,
  options: { digits?: number; placeholder?: string; symbol?: string } = {}
): string => {
  const { digits = 2, placeholder = '—', symbol = '¥' } = options;
  if (!isFiniteNumber(value)) return placeholder;
  return `${symbol}${formatNumber(value, { digits })}`;
};

export const formatCompact = (
  value: unknown,
  options: { digits?: number; placeholder?: string } = {}
): string => {
  const { digits = 1, placeholder = '—' } = options;
  if (!isFiniteNumber(value)) return placeholder;
  const abs = Math.abs(value);
  const sign = value < 0 ? '-' : '';
  if (abs >= 1e12) return `${sign}${(abs / 1e12).toFixed(digits)}万亿`;
  if (abs >= 1e8) return `${sign}${(abs / 1e8).toFixed(digits)}亿`;
  if (abs >= 1e4) return `${sign}${(abs / 1e4).toFixed(digits)}万`;
  return `${sign}${abs.toFixed(digits)}`;
};

export const directionClass = (value: unknown): string => {
  if (!isFiniteNumber(value)) return 'text-text-secondary';
  if (value > 0) return 'text-up';
  if (value < 0) return 'text-down';
  return 'text-text-secondary';
};

export const directionArrow = (value: unknown): string => {
  if (!isFiniteNumber(value) || value === 0) return '';
  return value > 0 ? '▲' : '▼';
};

export const formatTimestamp = (
  value: unknown,
  options: { includeSeconds?: boolean } = {}
): string => {
  if (typeof value !== 'string' || !value) return '—';
  try {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    const opts: Intl.DateTimeFormatOptions = {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    };
    if (options.includeSeconds) opts.second = '2-digit';
    return new Intl.DateTimeFormat('zh-CN', opts).format(date).replace(/\//g, '-');
  } catch {
    return value;
  }
};

export const joinWithSep = (parts: Array<string | null | undefined>, sep = NBSP + '·' + NBSP): string =>
  parts.filter((p): p is string => Boolean(p)).join(sep);
