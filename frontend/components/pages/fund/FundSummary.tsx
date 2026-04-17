import { Card, CardHeader, Metric } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { formatCompact, formatPercent } from '@/utils/format';
import type { FundOverview } from '@/services/types';

interface Props {
  data: FundOverview;
}

export function FundSummary({ data }: Props) {
  return (
    <Card>
      <CardHeader
        title={data.name}
        subtitle={
          <div className="flex items-center gap-2 text-caption text-text-tertiary">
            <span className="font-mono">{data.code}</span>
            <span>·</span>
            <Badge tone="brand" size="xs">{data.type}</Badge>
            <span>·</span>
            <span>{data.manager}</span>
            <span>·</span>
            <span>成立 {data.inception_date}</span>
          </div>
        }
      />
      <div className="grid grid-cols-2 md:grid-cols-4 gap-5 mt-4">
        <Metric
          label="规模"
          value={formatCompact(data.aum)}
          size="md"
        />
        {['20D', '60D', '120D'].map((w) => (
          <Metric
            key={w}
            label={`${w} 累计`}
            value={formatPercent(data.returns[w] ?? 0, { signed: true })}
            tone={(data.returns[w] ?? 0) >= 0 ? 'up' : 'down'}
            size="md"
          />
        ))}
      </div>
      <div className="mt-4 text-caption text-text-tertiary">
        代理指数：<span className="font-mono text-text-secondary">{data.proxy_index}</span>
      </div>
    </Card>
  );
}
