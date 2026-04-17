import { useCallback } from 'react';
import { BaseChart } from './BaseChart';
import { axisStyle, tooltipStyle, type ChartTokens } from './chartTheme';

interface AreaChartProps {
  xData: string[];
  values: number[];
  name: string;
  height?: number;
  valueFormatter?: (v: number) => string;
  tone?: 'up' | 'down' | 'brand' | 'warn';
  yAxisName?: string;
  className?: string;
}

export function AreaChart({
  xData,
  values,
  name,
  height = 260,
  valueFormatter,
  tone = 'brand',
  yAxisName,
  className,
}: AreaChartProps) {
  const option = useCallback(
    (tokens: ChartTokens) => {
      const color = tokens[tone];
      return {
        grid: { left: 48, right: 24, top: 24, bottom: 28 },
        tooltip: {
          ...tooltipStyle(tokens),
          trigger: 'axis',
          valueFormatter: valueFormatter ? (v: number) => valueFormatter(v) : undefined,
        },
        xAxis: {
          type: 'category',
          data: xData,
          boundaryGap: false,
          ...axisStyle(tokens),
          splitLine: { show: false },
        },
        yAxis: {
          type: 'value',
          name: yAxisName,
          nameTextStyle: { color: tokens.textTertiary, fontSize: 11 },
          ...axisStyle(tokens),
          axisLabel: { ...axisStyle(tokens).axisLabel, formatter: valueFormatter },
          scale: true,
        },
        series: [
          {
            name,
            type: 'line',
            data: values,
            smooth: true,
            showSymbol: false,
            lineStyle: { color, width: 1.8 },
            itemStyle: { color },
            areaStyle: {
              opacity: 0.22,
              color: {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [
                  { offset: 0, color: color + 'AA' },
                  { offset: 1, color: color + '11' },
                ],
              },
            },
          },
        ],
      };
    },
    [xData, values, name, valueFormatter, tone, yAxisName]
  );

  return <BaseChart option={option} height={height} className={className} />;
}
