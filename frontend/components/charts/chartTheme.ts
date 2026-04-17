/**
 * ECharts theme tokens. All charts ultimately read from these helpers so a
 * single dark/light flip updates every chart at once. Values come from the
 * CSS variables set in globals.css — we read them once per render so the
 * theme sticks even when the user toggles dark/light.
 */

export interface ChartTokens {
  grid: string;
  axis: string;
  axisLabel: string;
  textPrimary: string;
  textSecondary: string;
  textTertiary: string;
  up: string;
  down: string;
  neutral: string;
  brand: string;
  brandSoft: string;
  warn: string;
  tooltipBg: string;
  tooltipBorder: string;
  surface: string;
  border: string;
}

const getVar = (name: string, fallback: string): string => {
  if (typeof window === 'undefined') return fallback;
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return value || fallback;
};

export const resolveChartTokens = (): ChartTokens => ({
  grid: getVar('--chart-grid', '#19243b'),
  axis: getVar('--chart-axis', '#3b4a6b'),
  axisLabel: getVar('--text-tertiary', '#6b7a95'),
  textPrimary: getVar('--text-primary', '#e6edf9'),
  textSecondary: getVar('--text-secondary', '#a6b3c8'),
  textTertiary: getVar('--text-tertiary', '#6b7a95'),
  up: getVar('--up', '#21c88a'),
  down: getVar('--down', '#ff4d6d'),
  neutral: getVar('--neutral', '#a6b3c8'),
  brand: getVar('--brand', '#3278ff'),
  brandSoft: getVar('--brand-muted', '#1b2b55'),
  warn: getVar('--warn', '#f5b94a'),
  tooltipBg: getVar('--chart-tooltip-bg', '#0f1626'),
  tooltipBorder: getVar('--chart-tooltip-border', '#2c3b58'),
  surface: getVar('--surface-raised', '#121a2b'),
  border: getVar('--border-default', '#1e2a42'),
});

export const tooltipStyle = (tokens: ChartTokens) => ({
  backgroundColor: tokens.tooltipBg,
  borderColor: tokens.tooltipBorder,
  borderWidth: 1,
  padding: [8, 10],
  textStyle: {
    color: tokens.textPrimary,
    fontSize: 12,
    fontFamily: 'Inter, system-ui, sans-serif',
  },
  extraCssText: 'box-shadow: 0 12px 28px rgba(0,0,0,0.25); border-radius: 6px;',
});

export const axisStyle = (tokens: ChartTokens) => ({
  axisLine: { lineStyle: { color: tokens.grid } },
  axisTick: { lineStyle: { color: tokens.grid } },
  axisLabel: {
    color: tokens.axisLabel,
    fontSize: 11,
    fontFamily: 'Inter, system-ui, sans-serif',
  },
  splitLine: { lineStyle: { color: tokens.grid, type: 'dashed' } },
});
