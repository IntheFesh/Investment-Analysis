import { Card, CardHeader } from '@/components/ui/Card';
import { EmptyState } from '@/components/ui/EmptyState';
import type { NewsItem, NewsStatus } from '@/services/types';

interface Props {
  domestic: NewsItem[];
  international: NewsItem[];
  status?: NewsStatus;
  ageSeconds?: number | null;
}

function Block({ title, items, status }: { title: string; items: NewsItem[]; status?: NewsStatus }) {
  const empty = items.length === 0;
  const emptyDescription =
    status === 'refreshing'
      ? '正在拉取最新资讯，请稍候。'
      : status === 'stale'
        ? '数据源响应较慢，正在后台刷新，稍后自动更新。'
        : status === 'unavailable'
          ? '当前所有资讯源均不可达，已停止轮询。'
          : '数据源暂不可用，稍后自动刷新。';
  return (
    <section className="rounded-lg border border-border bg-surface-sunken/30 p-3">
      <div className="text-body-sm font-semibold text-text-primary mb-2">{title}</div>
      {empty ? (
        <EmptyState compact title="暂无资讯" description={emptyDescription} />
      ) : (
        <ul className="space-y-2.5">
          {items.slice(0, 5).map((n) => (
            <li key={`${n.url}-${n.published_at}`} className="border-b border-border/60 pb-2 last:border-b-0 last:pb-0">
              <a href={n.url} target="_blank" rel="noreferrer" className="text-body-sm text-text-primary hover:text-brand line-clamp-2">
                {n.title}
              </a>
              <div className="text-micro text-text-tertiary mt-1">
                {n.source} · {n.published_at || '最近更新'}
                {n.lang === 'zh' ? ' · 中文' : n.lang === 'en' ? ' · 英文' : ''}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function statusBadge(status?: NewsStatus, ageSeconds?: number | null): { label: string; tone: string } | null {
  if (!status || status === 'fresh') {
    if (typeof ageSeconds === 'number' && ageSeconds >= 0) {
      return { label: `更新 ${Math.round(ageSeconds)} 秒前`, tone: 'text-text-tertiary' };
    }
    return null;
  }
  if (status === 'stale') return { label: '缓存（后台刷新中）', tone: 'text-amber-600' };
  if (status === 'refreshing') return { label: '正在获取…', tone: 'text-text-tertiary' };
  return { label: '数据源不可达', tone: 'text-red-600' };
}

export function NewsPanel({ domestic, international, status, ageSeconds }: Props) {
  const badge = statusBadge(status, ageSeconds);
  return (
    <Card>
      <CardHeader
        title="重大新闻热点"
        subtitle="国内外资讯均取自东方财富、新浪财经等国内平台（中文标题），按重要度（关键词 + 时效）排序。"
      />
      {badge ? (
        <div className={`text-micro mt-1 ${badge.tone}`}>{badge.label}</div>
      ) : null}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 mt-3">
        <Block title="国内" items={domestic} status={status} />
        <Block title="国际" items={international} status={status} />
      </div>
    </Card>
  );
}
