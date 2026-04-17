import { useCallback } from 'react';
import { BaseChart } from './BaseChart';
import { axisStyle, tooltipStyle, type ChartTokens } from './chartTheme';

interface HeatmapProps {
  xLabels: string[];
  yLabels: string[];
  data: Array<[number, number, number]>; // [x, y, value]
  valueFormatter?: (v: number) => string;
  height?: number;
  scheme?: 'diverging' | 'sequential';
  min?: number;
  max?: number;
  className?: string;
}

export function Heatmap({
  xLabels,
  yLabels,
  data,
  valueFormatter,
  height = 260,
  scheme = 'diverging',
  min,
  max,
  className,
}: HeatmapProps) {
  const option = useCallback(
    (tokens: ChartTokens) => {
      const values = data.map((d) => d[2]);
      const finite = values.filter(Number.isFinite);
      const localMin = min ?? (finite.length ? Math.min(...finite) : 0);
      const localMax = max ?? (finite.length ? Math.max(...finite) : 1);

      const visualMap =
        scheme === 'diverging'
          ? {
              type: 'continuous' as const,
              min: -Math.max(Math.abs(localMin), Math.abs(localMax)),
              max: Math.max(Math.abs(localMin), Math.abs(localMax)),
              calculable: true,
              orient: 'horizontal' as const,
              left: 'center',
              bottom: 0,
              itemWidth: 12,
              textStyle: { color: tokens.textTertiary, fontSize: 10 },
              inRange: { color: [tokens.down, tokens.surface, tokens.up] },
            }
          : {
              type: 'continuous' as const,
              min: localMin,
              max: localMax,
              calculable: true,
              orient: 'horizontal' as const,
              left: 'center',
              bottom: 0,
              itemWidth: 12,
              textStyle: { color: tokens.textTertiary, fontSize: 10 },
              inRange: { color: [tokens.surface, tokens.brand] },
            };
      return {
        tooltip: {
          ...tooltipStyle(tokens),
          position: 'top',
          formatter: (params: { data: [number, number, number] }) => {
            const [x, y, v] = params.data;
            return `<div style="font-size:12px;">${xLabels[x]} · ${yLabels[y]}</div><div style="font-weight:600;">${valueFormatter ? valueFormatter(v) : v}</div>`;
          },
        },
        grid: { left: 80, right: 24, top: 24, bottom: 56 },
        xAxis: {
          type: 'category',
          data: xLabels,
          splitArea: { show: false },
          ...axisStyle(tokens),
          axisLabel: { ...axisStyle(tokens).axisLabel, rotate: xLabels.length > 8 ? 30 : 0 },
        },
        yAxis: {
          type: 'category',
          data: yLabels,
          splitArea: { show: false },
          ...axisStyle(tokens),
        },
        visualMap,
        series: [
          {
            type: 'heatmap',
            data,
            label: { show: false },
            emphasis: {
              itemStyle: {
                shadowBlur: 8,
                shadowColor: tokens.brandSoft,
              },
            },
            itemStyle: { borderRadius: 3, borderColor: tokens.surface, borderWidth: 1 },
          },
        ],
      };
    },
    [xLabels, yLabels, data, valueFormatter, scheme, min, max]
  );

  return <BaseChart option={option} height={height} className={className} />;
}
