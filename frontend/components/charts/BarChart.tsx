import { useCallback } from 'react';
import { BaseChart } from './BaseChart';
import { axisStyle, tooltipStyle, type ChartTokens } from './chartTheme';

interface BarChartProps {
  categories: string[];
  values: number[];
  valueFormatter?: (v: number) => string;
  height?: number;
  horizontal?: boolean;
  tone?: 'brand' | 'up' | 'down' | 'neutral';
  signedColors?: boolean;
  className?: string;
}

export function BarChart({
  categories,
  values,
  valueFormatter,
  height = 260,
  horizontal = false,
  tone = 'brand',
  signedColors = false,
  className,
}: BarChartProps) {
  const option = useCallback(
    (tokens: ChartTokens) => {
      const palette = {
        brand: tokens.brand,
        up: tokens.up,
        down: tokens.down,
        neutral: tokens.neutral,
      };
      const defaultColor = palette[tone];
      const colorFor = (v: number) => {
        if (!signedColors) return defaultColor;
        if (v > 0) return tokens.up;
        if (v < 0) return tokens.down;
        return tokens.neutral;
      };
      const categoryAxis = { type: 'category' as const, data: categories, ...axisStyle(tokens), splitLine: { show: false } };
      const valueAxis = {
        type: 'value' as const,
        ...axisStyle(tokens),
        axisLabel: { ...axisStyle(tokens).axisLabel, formatter: valueFormatter },
        scale: true,
      };
      return {
        grid: { left: horizontal ? 80 : 48, right: 24, top: 24, bottom: 28, containLabel: false },
        tooltip: {
          ...tooltipStyle(tokens),
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
          valueFormatter: valueFormatter ? (v: number) => valueFormatter(v) : undefined,
        },
        xAxis: horizontal ? valueAxis : categoryAxis,
        yAxis: horizontal ? categoryAxis : valueAxis,
        series: [
          {
            type: 'bar',
            data: values.map((v) => ({ value: v, itemStyle: { color: colorFor(v) } })),
            barMaxWidth: 24,
            itemStyle: { borderRadius: horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0] },
            emphasis: { itemStyle: { opacity: 0.85 } },
            label: {
              show: false,
            },
          },
        ],
      };
    },
    [categories, values, valueFormatter, horizontal, tone, signedColors]
  );

  return <BaseChart option={option} height={height} className={className} />;
}
