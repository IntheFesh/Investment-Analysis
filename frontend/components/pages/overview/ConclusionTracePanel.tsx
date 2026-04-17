import { useState } from 'react';
import { Card, CardHeader } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import type { Explanation } from '@/services/types';

interface Props {
  explanations: Explanation[];
}

export function ConclusionTracePanel({ explanations }: Props) {
  const [open, setOpen] = useState<string | null>(explanations[0]?.id ?? null);

  return (
    <Card>
      <CardHeader title="今日结论追溯" subtitle="摘要默认展示，展开可查看驱动指标与适用视角。" />
      <div className="mt-3 space-y-2">
        {explanations.map((e) => {
          const active = open === e.id;
          return (
            <div key={e.id} className="rounded-lg border border-border bg-surface-sunken/30">
              <button className="w-full text-left p-3.5" onClick={() => setOpen(active ? null : e.id)}>
                <div className="flex items-center justify-between gap-2">
                  <div>
                    <div className="text-body-md font-medium text-text-primary">{e.title ?? e.fact}</div>
                    <div className="text-caption text-text-tertiary mt-0.5 line-clamp-2">{e.inference}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    {e.horizon ? <Badge tone="neutral" size="xs">{e.horizon}</Badge> : null}
                    {e.timestamp ? <span className="text-micro text-text-tertiary">{e.timestamp}</span> : null}
                  </div>
                </div>
              </button>
              {active ? (
                <div className="px-3.5 pb-3.5 grid grid-cols-1 lg:grid-cols-[1.5fr_1fr] gap-3">
                  <div>
                    <div className="text-caption text-text-tertiary mb-1">关键驱动指标</div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {(e.drivers ?? []).map((d) => (
                        <div key={d.label} className="rounded-md border border-border/70 bg-surface-raised/40 p-2.5">
                          <div className="text-micro text-text-tertiary">{d.label}</div>
                          <div className="text-body-sm tabular text-text-primary mt-0.5">{d.value}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="rounded-md border border-border/70 bg-surface-raised/40 p-3">
                    <div className="text-caption text-text-tertiary">风险提示</div>
                    <div className="text-body-sm text-warn mt-1">{e.risk}</div>
                    <div className="text-caption text-text-tertiary mt-3">适用视角</div>
                    <div className="text-body-sm text-text-primary mt-1">{e.tag === 'cross-market' ? '跨市场与隔夜交易' : 'A股日内/短线配置'}</div>
                  </div>
                </div>
              ) : null}
            </div>
          );
        })}
      </div>
    </Card>
  );
}
