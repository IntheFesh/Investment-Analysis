import { useMemo, useState } from 'react';
import { Card, CardHeader } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import type { Explanation } from '@/services/types';

interface Props {
  explanations: Explanation[];
  summary: string;
}

const TAG_TONE: Record<string, 'brand' | 'up' | 'down' | 'warn' | 'info' | 'neutral'> = {
  'sector-rotation': 'brand',
  breadth: 'info',
  'cross-market': 'warn',
};

export function ExplanationsPanel({ explanations, summary }: Props) {
  const [openId, setOpenId] = useState<string | null>(explanations[0]?.id ?? null);
  const open = useMemo(() => explanations.find((e) => e.id === openId) ?? explanations[0], [explanations, openId]);

  return (
    <Card>
      <CardHeader title="今日解读" subtitle="一句核心判断 + 关键推断，按主题查看结论。" />
      <div className="text-body-sm text-text-secondary mt-2">{summary}</div>
      {explanations.length === 0 ? (
        <EmptyState compact title="暂无解读" description="当前窗口数据不足以生成解读。" />
      ) : (
        <div className="mt-4 grid grid-cols-1 md:grid-cols-[1fr_1.5fr] gap-4">
          <ul className="flex flex-col gap-1.5">
            {explanations.map((e) => {
              const active = e.id === (open?.id ?? null);
              return (
                <li key={e.id}>
                  <button
                    onClick={() => setOpenId(e.id)}
                    aria-pressed={active}
                    className={`w-full text-left rounded-lg border transition-colors duration-standard p-3 ${
                      active
                        ? 'border-brand bg-brand/10'
                        : 'border-border bg-surface-sunken/40 hover:border-border-strong'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-body-sm font-medium text-text-primary line-clamp-1">{e.title ?? e.fact}</span>
                      <Badge tone={TAG_TONE[e.tag] ?? 'neutral'} size="xs">
                        {e.tag === 'sector-rotation' ? '轮动' : e.tag === 'cross-market' ? '联动' : '广度'}
                      </Badge>
                    </div>
                    <div className="text-caption text-text-tertiary mt-1 line-clamp-2">{e.fact}</div>
                  </button>
                </li>
              );
            })}
          </ul>

          <aside className="rounded-lg border border-border bg-surface-sunken/40 p-4">
            {open ? (
              <div className="space-y-4">
                <div>
                  <div className="text-caption text-text-tertiary uppercase tracking-wider">核心判断</div>
                  <div className="text-body-md text-text-primary mt-1">{open.fact}</div>
                </div>
                <div>
                  <div className="text-caption text-text-tertiary uppercase tracking-wider">推断</div>
                  <div className="text-body-md text-text-primary mt-1 leading-relaxed">{open.inference}</div>
                </div>
                {open.drivers && open.drivers.length > 0 ? (
                  <div>
                    <div className="text-caption text-text-tertiary uppercase tracking-wider">关键驱动</div>
                    <div className="mt-1.5 grid grid-cols-1 sm:grid-cols-3 gap-2">
                      {open.drivers.map((d) => (
                        <div key={d.label} className="rounded-md border border-border/70 bg-surface-raised/40 p-2">
                          <div className="text-micro text-text-tertiary">{d.label}</div>
                          <div className="text-body-sm text-text-primary tabular mt-0.5">{d.value}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null}
                <div>
                  <div className="text-caption text-text-tertiary uppercase tracking-wider">风险提示</div>
                  <div className="text-body-sm text-warn mt-1">{open.risk}</div>
                </div>
              </div>
            ) : null}
          </aside>
        </div>
      )}
    </Card>
  );
}
