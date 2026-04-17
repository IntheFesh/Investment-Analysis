import { memo, useEffect, useMemo, useRef, useState } from 'react';
import dynamic from 'next/dynamic';
import clsx from 'clsx';
import { useAppContext } from '@/context/AppContext';
import { resolveChartTokens, type ChartTokens } from './chartTheme';

const ReactECharts = dynamic(() => import('echarts-for-react').then((m) => m.default), {
  ssr: false,
});

interface BaseChartProps {
  option: (tokens: ChartTokens) => Record<string, unknown>;
  height?: number | string;
  className?: string;
  notMerge?: boolean;
  lazyUpdate?: boolean;
}

const BaseChartImpl = ({
  option,
  height = 280,
  className,
  notMerge = true,
  lazyUpdate = false,
}: BaseChartProps) => {
  const { resolvedTheme } = useAppContext();
  const [tokens, setTokens] = useState<ChartTokens | null>(null);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setTokens(resolveChartTokens());
  }, [resolvedTheme]);

  const built = useMemo(() => (tokens ? option(tokens) : null), [option, tokens]);

  if (!tokens || !built) {
    return (
      <div
        ref={ref}
        className={clsx('w-full rounded-md bg-surface-sunken/40', className)}
        style={{ height }}
      />
    );
  }

  return (
    <div ref={ref} className={clsx('w-full', className)} style={{ height }}>
      <ReactECharts
        option={built}
        style={{ height: '100%', width: '100%' }}
        notMerge={notMerge}
        lazyUpdate={lazyUpdate}
        opts={{ renderer: 'canvas' }}
      />
    </div>
  );
};

export const BaseChart = memo(BaseChartImpl);
