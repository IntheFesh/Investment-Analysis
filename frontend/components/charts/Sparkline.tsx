import { useCallback, useMemo } from 'react';
import { BaseChart } from './BaseChart';
import type { ChartTokens } from './chartTheme';

interface SparklineProps {
  data: number[];
  height?: number;
  width?: number | string;
  tone?: 'auto' | 'up' | 'down' | 'neutral' | 'brand';
  filled?: boolean;
  className?: string;
}

export function Sparkline({
  data,
  height = 28,
  width = 96,
  tone = 'auto',
  filled = true,
  className,
}: SparklineProps) {
  const resolvedTone = useMemo<SparklineProps['tone']>(() => {
    if (tone !== 'auto') return tone;
    if (!data || data.length < 2) return 'neutral';
    return data[data.length - 1] >= data[0] ? 'up' : 'down';
  }, [data, tone]);

  const option = useCallback(
    (tokens: ChartTokens) => {
      const color =
        resolvedTone === 'up'
          ? tokens.up
          : resolvedTone === 'down'
            ? tokens.down
            : resolvedTone === 'brand'
              ? tokens.brand
              : tokens.neutral;
      return {
        animation: false,
        grid: { left: 0, right: 0, top: 2, bottom: 2 },
        xAxis: { type: 'category', show: false, data: data.map((_, i) => i) },
        yAxis: { type: 'value', show: false, scale: true },
        series: [
          {
            type: 'line',
            data,
            showSymbol: false,
            smooth: true,
            lineStyle: { color, width: 1.4 },
            areaStyle: filled ? { color, opacity: 0.12 } : undefined,
          },
        ],
      };
    },
    [data, filled, resolvedTone]
  );

  return (
    <div style={{ width }} className={className}>
      <BaseChart option={option} height={height} />
    </div>
  );
}
