import { useCallback } from 'react';
import { BaseChart } from './BaseChart';
import type { ChartTokens } from './chartTheme';

interface GaugeChartProps {
  value: number;
  min?: number;
  max?: number;
  label?: string;
  tone?: 'auto' | 'brand' | 'up' | 'down' | 'warn';
  subtitle?: string;
  height?: number;
  className?: string;
}

const autoTone = (value: number): 'up' | 'brand' | 'warn' | 'down' => {
  if (value >= 75) return 'warn'; // over-heated territory
  if (value >= 55) return 'up';
  if (value >= 35) return 'brand';
  return 'down';
};

export function GaugeChart({
  value,
  min = 0,
  max = 100,
  label,
  tone = 'auto',
  subtitle,
  height = 220,
  className,
}: GaugeChartProps) {
  const option = useCallback(
    (tokens: ChartTokens) => {
      const toneKey = tone === 'auto' ? autoTone(value) : tone;
      const colorMap: Record<string, string> = {
        up: tokens.up,
        down: tokens.down,
        warn: tokens.warn,
        brand: tokens.brand,
      };
      const color = colorMap[toneKey] ?? tokens.brand;

      return {
        series: [
          {
            type: 'gauge',
            startAngle: 200,
            endAngle: -20,
            min,
            max,
            radius: '95%',
            progress: {
              show: true,
              width: 14,
              roundCap: true,
              itemStyle: { color },
            },
            axisLine: {
              lineStyle: {
                width: 14,
                color: [[1, tokens.grid]],
              },
            },
            splitLine: { show: false },
            axisTick: { show: false },
            axisLabel: {
              show: true,
              distance: -40,
              color: tokens.textTertiary,
              fontSize: 10,
              formatter: (v: number) => (v === min || v === max ? String(v) : ''),
            },
            pointer: { show: false },
            anchor: { show: false },
            title: {
              offsetCenter: [0, '28%'],
              color: tokens.textTertiary,
              fontSize: 12,
              fontFamily: 'Inter, system-ui, sans-serif',
            },
            detail: {
              offsetCenter: [0, '0%'],
              valueAnimation: true,
              formatter: (v: number) => v.toFixed(0),
              color: tokens.textPrimary,
              fontSize: 34,
              fontWeight: 600,
              fontFamily: 'Inter, system-ui, sans-serif',
            },
            data: [
              {
                value,
                name: label ?? '',
              },
            ],
          },
        ],
        graphic: subtitle
          ? [
              {
                type: 'text',
                left: 'center',
                bottom: 6,
                style: {
                  text: subtitle,
                  fill: tokens.textSecondary,
                  font: '12px Inter, system-ui, sans-serif',
                },
              },
            ]
          : undefined,
      };
    },
    [value, min, max, label, tone, subtitle]
  );

  return <BaseChart option={option} height={height} className={className} />;
}
