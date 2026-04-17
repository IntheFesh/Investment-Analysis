import { Card, CardHeader } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { EmptyState } from '@/components/ui/EmptyState';
import { formatPercent } from '@/utils/format';
import type { SectorRotation, SectorItem } from '@/services/types';

interface Props {
  data: SectorRotation;
}

function SectorBlock({
  title,
  tone,
  items,
  hint,
}: {
  title: string;
  tone: 'up' | 'warn' | 'down';
  items: SectorItem[];
  hint: string;
}) {
  const extremum = Math.max(1, ...items.map((it) => Math.abs(it.score)));
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <Badge tone={tone} size="sm">
          {title}
        </Badge>
        <span className="text-caption text-text-tertiary">{hint}</span>
      </div>
      <div className="flex flex-col gap-2">
        {items.length === 0 ? (
          <div className="text-caption text-text-tertiary">—</div>
        ) : (
          items.map((it) => (
            <div key={it.sector} className="flex flex-col gap-1">
              <div className="flex items-center justify-between text-body-sm">
                <span className="text-text-primary">{it.sector}</span>
                <span className={`tabular ${it.score >= 0 ? 'text-up' : 'text-down'}`}>
                  {formatPercent(it.score)}
                </span>
              </div>
              <ProgressBar
                value={Math.min(1, Math.abs(it.score) / extremum)}
                tone={it.score >= 0 ? 'up' : 'down'}
                size="xs"
              />
              {it.note ? <div className="text-micro text-text-tertiary">{it.note}</div> : null}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export function SectorRotationPanel({ data }: Props) {
  const total = data.strongest.length + data.candidate.length + data.high_crowding.length;
  return (
    <Card>
      <CardHeader
        title="板块轮动"
        subtitle="窗口累计收益代理行业强弱，按代理指数计算（见注释）。"
      />
      {total === 0 ? (
        <EmptyState compact title="无轮动数据" description="当前窗口内行业代理指数样本不足。" />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mt-4">
          <SectorBlock title="最强" tone="up" items={data.strongest} hint="相对超涨" />
          <SectorBlock title="候选" tone="warn" items={data.candidate} hint="轮动临界" />
          <SectorBlock title="拥挤/承压" tone="down" items={data.high_crowding} hint="相对偏弱" />
        </div>
      )}
    </Card>
  );
}
