import { useCallback } from 'react';
import { BaseChart } from './BaseChart';
import { axisStyle, tooltipStyle, type ChartTokens } from './chartTheme';

export interface LineSeries {
  name: string;
  data: number[];
  color?: string;
  area?: boolean;
  type?: 'line';
  dashed?: boolean;
}

interface LineChartProps {
  xData: string[];
  series: LineSeries[];
  height?: number;
  valueFormatter?: (value: number) => string;
  yAxisName?: string;
  className?: string;
  smooth?: boolean;
}

export function LineChart({
  xData,
  series,
  height = 280,
  valueFormatter,
  yAxisName,
  className,
  smooth = true,
}: LineChartProps) {
  const optionBuilder = useCallback(
    (tokens: ChartTokens) => {
      const palette = [tokens.brand, tokens.up, tokens.warn, tokens.down, tokens.neutral];
      return {
        grid: { left: 48, right: 24, top: 32, bottom: 28, containLabel: false },
        tooltip: {
          ...tooltipStyle(tokens),
          trigger: 'axis',
          axisPointer: { type: 'line', lineStyle: { color: tokens.brand, width: 1 } },
          valueFormatter: valueFormatter ? (v: number) => valueFormatter(v) : undefined,
        },
        legend: {
          icon: 'roundRect',
          textStyle: { color: tokens.textSecondary, fontSize: 11 },
          right: 0,
          top: 0,
          itemWidth: 8,
          itemHeight: 4,
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
          nameTextStyle: { color: tokens.textTertiary, fontSize: 11, padding: [0, 0, 0, -12] },
          ...axisStyle(tokens),
          scale: true,
          axisLabel: {
            ...axisStyle(tokens).axisLabel,
            formatter: valueFormatter,
          },
        },
        series: series.map((s, i) => ({
          name: s.name,
          type: 'line',
          data: s.data,
          smooth,
          showSymbol: false,
          symbolSize: 6,
          lineStyle: {
            width: 2,
            color: s.color ?? palette[i % palette.length],
            type: s.dashed ? 'dashed' : 'solid',
          },
          itemStyle: { color: s.color ?? palette[i % palette.length] },
          areaStyle: s.area
            ? {
                opacity: 0.15,
                color: s.color ?? palette[i % palette.length],
              }
            : undefined,
          emphasis: { focus: 'series' },
        })),
      };
    },
    [series, xData, yAxisName, valueFormatter, smooth]
  );

  return <BaseChart option={optionBuilder} height={height} className={className} />;
}
