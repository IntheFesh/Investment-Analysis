import { Card, CardHeader } from '@/components/ui/Card';
import { Sparkline } from '@/components/charts/Sparkline';
import { DataTable, type Column } from '@/components/ui/Table';
import { EmptyState } from '@/components/ui/EmptyState';
import { formatNumber, formatPercent, formatSignedNumber, formatCompact, directionClass } from '@/utils/format';
import type { IndexRow } from '@/services/types';

interface IndicesPanelProps {
  indices: IndexRow[];
}

export function IndicesPanel({ indices }: IndicesPanelProps) {
  const columns: Column<IndexRow>[] = [
    {
      key: 'name',
      header: '指数',
      render: (r) => (
        <div className="flex flex-col">
          <span className="text-body-sm font-medium text-text-primary">{r.name}</span>
          <span className="text-caption text-text-tertiary">{r.symbol}</span>
        </div>
      ),
    },
    {
      key: 'last',
      header: '最新',
      align: 'right',
      render: (r) => <span className="tabular">{formatNumber(r.last)}</span>,
    },
    {
      key: 'change',
      header: '日涨跌',
      align: 'right',
      render: (r) => (
        <span className={`tabular ${directionClass(r.change)}`}>
          {formatSignedNumber(r.change)}
        </span>
      ),
    },
    {
      key: 'pct',
      header: '涨跌幅',
      align: 'right',
      render: (r) => (
        <span className={`tabular ${directionClass(r.change_percent)}`}>
          {formatPercent(r.change_percent)}
        </span>
      ),
    },
    {
      key: 'trend',
      header: '近 5 日',
      align: 'right',
      width: '96px',
      render: (r) => (
        <div className="flex justify-end">
          <Sparkline data={r.trend ?? []} width={96} height={28} />
        </div>
      ),
    },
    {
      key: 'turnover',
      header: '成交量',
      align: 'right',
      render: (r) => <span className="tabular text-text-secondary">{formatCompact(r.turnover)}</span>,
    },
    {
      key: 'asof',
      header: '截止',
      align: 'right',
      render: (r) => <span className="text-caption text-text-tertiary">{r.as_of}</span>,
    },
  ];

  return (
    <Card>
      <CardHeader
        title="核心指数快照"
        subtitle="日收盘、日涨跌幅、近 5 日走势与成交量。所有数值由后端 /market/overview 计算。"
      />
      <div className="mt-3">
        {indices.length > 0 ? (
          <DataTable
            columns={columns}
            rows={indices}
            getRowKey={(r) => r.symbol}
            dense
          />
        ) : (
          <EmptyState
            compact
            title="无指数数据"
            description="当前适配器返回为空或筛选条件过窄，请检查数据源或调整观察窗口。"
          />
        )}
      </div>
    </Card>
  );
}
