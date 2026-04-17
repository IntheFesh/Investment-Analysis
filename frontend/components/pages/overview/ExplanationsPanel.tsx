import { useState } from 'react';
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
  const firstId = explanations[0]?.id ?? null;
  const [openId, setOpenId] = useState<string | null>(firstId);
  const open = explanations.find((e) => e.id === openId) ?? explanations[0];

  return (
    <Card>
      <CardHeader
        title="今日解读"
        subtitle="事实 → 推断 → 证据 → 风险，四段式展开；点击切换条目。"
      />
      <div className="text-body-sm text-text-secondary mt-2">{summary}</div>
      {explanations.length === 0 ? (
        <EmptyState compact title="暂无解读" description="当前窗口数据不足以生成解读。" />
      ) : (
        <div className="mt-4 grid grid-cols-1 md:grid-cols-[1fr_1.4fr] gap-4">
          <ul className="flex flex-col gap-1">
            {explanations.map((e) => {
              const active = e.id === (open?.id ?? null);
              return (
                <li key={e.id}>
                  <button
                    onClick={() => setOpenId(e.id)}
                    aria-pressed={active}
                    className={`w-full text-left rounded-md border transition-colors duration-standard p-3 ${
                      active
                        ? 'border-brand bg-brand/10'
                        : 'border-border bg-surface-sunken/40 hover:border-border-strong'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-body-sm font-medium text-text-primary line-clamp-1">
                        {e.fact}
                      </span>
                      <Badge tone={TAG_TONE[e.tag] ?? 'neutral'} size="xs">
                        {e.tag}
                      </Badge>
                    </div>
                    <div className="text-caption text-text-tertiary mt-1 line-clamp-2">
                      {e.inference}
                    </div>
                  </button>
                </li>
              );
            })}
          </ul>
          <aside className="rounded-md border border-border bg-surface-sunken/40 p-4">
            {open ? (
              <div className="flex flex-col gap-3">
                <div>
                  <div className="text-caption text-text-tertiary uppercase tracking-wider">事实</div>
                  <div className="text-body-md text-text-primary mt-0.5">{open.fact}</div>
                </div>
                <div>
                  <div className="text-caption text-text-tertiary uppercase tracking-wider">推断</div>
                  <div className="text-body-md text-text-primary mt-0.5">{open.inference}</div>
                </div>
                {open.evidence ? (
                  <div>
                    <div className="text-caption text-text-tertiary uppercase tracking-wider">
                      证据
                    </div>
                    <div className="text-body-sm text-text-secondary mt-0.5">
                      {open.evidence.conclusion}
                      <span className="text-text-tertiary">
                        {' '}
                        · 方法 {open.evidence.method}（{open.evidence.method_version}）· 源{' '}
                        {open.evidence.source_name} · 置信度{' '}
                        {Math.round((open.evidence.confidence ?? 0) * 100)}%
                      </span>
                    </div>
                  </div>
                ) : null}
                <div>
                  <div className="text-caption text-text-tertiary uppercase tracking-wider">风险</div>
                  <div className="text-body-sm text-warn mt-0.5">{open.risk}</div>
                </div>
              </div>
            ) : null}
          </aside>
        </div>
      )}
    </Card>
  );
}
