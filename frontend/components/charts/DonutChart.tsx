import { useCallback } from 'react';
import { BaseChart } from './BaseChart';
import { tooltipStyle, type ChartTokens } from './chartTheme';

interface DonutChartProps {
  data: Array<{ name: string; value: number }>;
  height?: number;
  label?: string;
  valueFormatter?: (v: number) => string;
  className?: string;
}

export function DonutChart({
  data,
  height = 220,
  label,
  valueFormatter,
  className,
}: DonutChartProps) {
  const option = useCallback(
    (tokens: ChartTokens) => {
      const total = data.reduce((s, d) => s + (Number.isFinite(d.value) ? d.value : 0), 0);
      const palette = [
        tokens.brand,
        tokens.up,
        tokens.warn,
        tokens.down,
        tokens.neutral,
        '#7b61ff',
        '#00d1ff',
        '#ff9f43',
      ];
      return {
        tooltip: {
          ...tooltipStyle(tokens),
          trigger: 'item',
          formatter: (p: { name: string; value: number; percent: number }) =>
            `${p.name}<br/><b>${valueFormatter ? valueFormatter(p.value) : p.value}</b> · ${p.percent.toFixed(1)}%`,
        },
        series: [
          {
            type: 'pie',
            radius: ['58%', '85%'],
            avoidLabelOverlap: true,
            itemStyle: {
              borderColor: tokens.surface,
              borderWidth: 2,
              borderRadius: 4,
            },
            label: { show: false },
            data: data.map((d, i) => ({
              ...d,
              itemStyle: { color: palette[i % palette.length] },
            })),
          },
        ],
        graphic: [
          {
            type: 'text',
            left: 'center',
            top: 'center',
            style: {
              text: label ?? `${total.toFixed(1)}`,
              fill: tokens.textPrimary,
              font: '600 18px Inter, system-ui, sans-serif',
              textAlign: 'center',
            },
          },
        ],
      };
    },
    [data, label, valueFormatter]
  );

  return <BaseChart option={option} height={height} className={className} />;
}
