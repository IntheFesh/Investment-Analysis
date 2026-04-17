import { Card, CardHeader } from '@/components/ui/Card';
import { EmptyState } from '@/components/ui/EmptyState';
import type { NewsItem } from '@/services/types';

interface Props {
  domestic: NewsItem[];
  international: NewsItem[];
}

function Block({ title, items }: { title: string; items: NewsItem[] }) {
  return (
    <section className="rounded-lg border border-border bg-surface-sunken/30 p-3">
      <div className="text-body-sm font-semibold text-text-primary mb-2">{title}</div>
      {items.length === 0 ? (
        <EmptyState compact title="暂无资讯" description="数据源暂不可用，稍后自动刷新。" />
      ) : (
        <ul className="space-y-2.5">
          {items.slice(0, 5).map((n) => (
            <li key={`${n.url}-${n.published_at}`} className="border-b border-border/60 pb-2 last:border-b-0 last:pb-0">
              <a href={n.url} target="_blank" rel="noreferrer" className="text-body-sm text-text-primary hover:text-brand line-clamp-2">
                {n.title}
              </a>
              <div className="text-micro text-text-tertiary mt-1">{n.source} · {n.published_at || '最近更新'}</div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function NewsPanel({ domestic, international }: Props) {
  return (
    <Card>
      <CardHeader title="重大新闻热点" subtitle="实时更新的市场相关资讯，按国内 / 国际拆分。" />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 mt-3">
        <Block title="国内" items={domestic} />
        <Block title="国际" items={international} />
      </div>
    </Card>
  );
}
