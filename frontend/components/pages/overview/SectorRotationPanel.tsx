import { Card, CardHeader } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { EmptyState } from '@/components/ui/EmptyState';
import { formatPercent } from '@/utils/format';
import type { SectorRotation, SectorItem } from '@/services/types';

interface Props {
  data: SectorRotation;
}

function ItemRow({ it }: { it: SectorItem }) {
  const rs = it.metrics?.relative_strength ?? 0;
  const vol = it.metrics?.turnover_surge ?? 0;
  return (
    <div className="rounded-lg border border-border/70 bg-surface-sunken/40 p-2.5">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-body-sm font-medium text-text-primary">{it.sector}</span>
          {it.tag ? <Badge tone={it.tag === '强势' ? 'up' : it.tag === '弱势' ? 'down' : 'neutral'} size="xs">{it.tag}</Badge> : null}
        </div>
        <span className={`tabular text-body-sm ${it.score >= 55 ? 'text-up' : it.score <= 40 ? 'text-down' : 'text-text-secondary'}`}>
          {it.score.toFixed(1)}
        </span>
      </div>
      <ProgressBar value={Math.min(1, it.score / 100)} tone={it.score >= 55 ? 'up' : it.score <= 40 ? 'down' : 'warn'} size="xs" />
      <div className="mt-1.5 grid grid-cols-2 gap-x-3 text-micro text-text-tertiary">
        <span>相对强弱 {formatPercent(rs * 100)}</span>
        <span>成交脉冲 {vol >= 0 ? '+' : ''}{vol.toFixed(2)}σ</span>
      </div>
    </div>
  );
}

function Block({ title, items }: { title: string; items: SectorItem[] }) {
  return (
    <div className="space-y-2">
      <div className="text-caption uppercase tracking-wider text-text-tertiary">{title}</div>
      {items.length === 0 ? <div className="text-caption text-text-tertiary">—</div> : items.map((it) => <ItemRow key={`${title}-${it.sector}`} it={it} />)}
    </div>
  );
}

export function SectorRotationPanel({ data }: Props) {
  const total = data.strongest.length + data.candidate.length + data.high_crowding.length;
  return (
    <Card>
      <CardHeader title="板块轮动" subtitle="综合相对强弱、滚动动量、成交脉冲、广度与拥挤度生成。" />
      {total === 0 ? (
        <EmptyState compact title="无轮动数据" description="当前窗口有效样本不足。" />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
          <Block title="领先" items={data.strongest} />
          <Block title="关注" items={data.candidate} />
          <Block title="拥挤/承压" items={data.high_crowding} />
        </div>
      )}
    </Card>
  );
}
